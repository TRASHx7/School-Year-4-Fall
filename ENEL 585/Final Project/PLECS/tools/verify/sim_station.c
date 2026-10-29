/* Switched-circuit check of the Group 8 controller, independent of PLECS.
 *
 * Compiles the controller CScript sections verbatim and runs them against a
 * time-stepped model of the Project B station: ITECH (ideal source + Rs),
 * Cdc, H-bridge with dead time and diode conduction, 2 x 47 uH and
 * 2 x 62 uF filter (seen as 94 uH and 31 uF between the taps), resistor bank,
 * interface-board sensing filter and 12-bit ADC.
 *
 * Usage: sim_station <case> [csv]
 *   case 0: demonstration sequence (OP1, load step, reference step, OP2)
 *   case 1: same, worst case: L -20 %, 5 us dead time, 2 V device drop
 *   case 2: protection test, inductor trip lowered to 2.5 A
 *   case 3: Vdc low (45 V) to exercise modulator limit and anti-windup
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

/* CScript macro emulation */
static double g_in[6][4], g_out[4][8], g_par[64];
#define InputSignal(i, j)   g_in[i][j]
#define OutputSignal(i, j)  g_out[i][j]
#define ParamRealData(i, j) g_par[j]
static double g_ds[1];
#define DiscState(i)        g_ds[i]

#include "../cscript/ctrl_declarations.c"
static void ctl_start(void)
{
#include "../cscript/ctrl_start.c"
}
static void ctl_output(void)
{
#include "../cscript/ctrl_output.c"
}
static void ctl_update(void)
{
#include "../cscript/ctrl_update.c"
}

/* Station and test parameters */
static double Lf = 94e-6, Cf = 31e-6, RLf = 0.04, Ron = 0.02, Rb = 200e3;
static double Vs = 50.0, Rs = 0.02, Cdc = 1.1e-3;
static double td = 2e-6, Vdrop = 0.0;
static double t_en = 0.02, t_load_on = 0.30, t_ref_up = 0.50, t_ref_dn = 0.70,
              t_load_off = 0.85, t_end = 1.10, V_op1 = 25.0, V_op2 = 30.0;
static double R_base = 25.0, R_step = 25.0;   /* 25 ohm, 25||25 = 12.5 ohm */

/* Interface-board sensing (Inverter Box Setup Guide) */
#define K_V   0.0213    /* V at pin per V, 10:1 probe */
#define K_I   0.0154    /* V at pin per A, 100 mV/A */
#define OFS   1.667
typedef struct { double x1, x2; } filt;
static double wp1 = 2*M_PI*700, wp2 = 2*M_PI*900, wz = 2*M_PI*1500;
static void filt_step(filt *f, double u, double dt)
{
    double d1 = wp1*(u - f->x1);
    double w = f->x1 + d1/wz;
    f->x1 += dt*d1;
    f->x2 += dt*wp2*(w - f->x2);
}
static double adc(double v)
{
    double q = 3.3/4096;
    v = q*floor(v/q + 0.5);
    return v < 0 ? 0 : (v > 3.3 ? 3.3 : v);
}

static void set_params(double il_trip)
{
    double fclk = 150e6, f1 = 60, N = 166;
    double fcar = fclk/(2*round(fclk/(2*N*f1)));
    double p[P_NUM] = {0};
    p[P_N] = N;            p[P_TS] = 1/fcar;
    p[P_KVO] = 1/K_V;      p[P_OVO] = OFS;
    p[P_KIL] = 1/K_I;      p[P_OIL] = OFS;
    p[P_KIO] = 1/K_I;      p[P_OIO] = OFS;
    p[P_KDC] = 1/K_V;      p[P_ODC] = OFS;
    p[P_SRC_VO] = 1; p[P_SRC_IL] = 2; p[P_SRC_IO] = 3; p[P_SRC_DC] = 4;
    p[P_VDC_NOM] = 50;     p[P_H60] = 0.9949;
    p[P_VO_TRIP] = 50;     p[P_IL_TRIP] = il_trip;
    p[P_IO_TRIP] = 6;      p[P_DC_TRIP] = 55;
    p[P_DC_MIN] = 20;      p[P_VREF_MAX] = 32;
    p[P_SLEW] = 5;         p[P_M_MAX] = 0.98;   p[P_X_MAX] = 10;
    p[P_I_LIM] = 6;        p[P_K_FOLD] = 2;     p[P_FOLD_DEC] = 0.5;
    p[P_TAU_DC] = 0.02;
    for (int k = 0; k < P_NUM; k++) g_par[k] = p[k];
}

int main(int argc, char **argv)
{
    int scase = argc > 1 ? atoi(argv[1]) : 0;
    FILE *csv = argc > 2 ? fopen(argv[2], "w") : NULL;
    double il_trip = 9;
    if (scase == 1) { Lf *= 0.8; td = 5e-6; Vdrop = 2.0; }
    if (scase == 2) il_trip = 2.5;
    if (scase == 3) Vs = 45;
    set_params(il_trip);
    ctl_start();

    const double Tc = g_par[P_TS], dt = 10e-9;
    double t = 0, iL = 0, vo = 0, vdc = Vs;
    filt fv = {0, 0}, fi = {0, 0}, fo = {0, 0}, fd = {Vs, Vs};
    double dA = 0.5, dB = 0.5, dA_next = 0.5, dB_next = 0.5;
    int en = 0, en_next = 0;
    long k_samp = 0;
    double t_on_A = -1, t_on_B = -1; int sA = 0, sB = 0;   /* commanded top-on */

    /* metrics */
    double win_v2 = 0, win_i2 = 0, win_io2 = 0, win_p = 0, win_n = 0, ilpk = 0, vopk = 0;
    double m_max = 0, il_abs_max = 0;
    int fault_seen = 0; double t_fault = -1;

    if (csv) fprintf(csv, "t,vo,iL,io,vpk_meas,vc,m,fault,run,iL_max\n");
    while (t < t_end) {
        /* Controller at the carrier valley; new duties load at the next one. */
        if (t >= k_samp*Tc) {
            dA = dA_next; dB = dB_next; en = en_next;
            double Rl = (t >= t_load_on && t < t_load_off) ? 1/(1/R_base + 1/R_step) : R_base;
            double io_true = vo/Rl;
            (void)io_true;
            g_in[0][0] = adc(OFS + K_V*fv.x2);
            g_in[0][1] = adc(OFS + K_I*fi.x2);
            g_in[0][2] = adc(OFS + K_I*fo.x2);
            g_in[1][0] = adc(OFS + K_V*fd.x2);
            g_in[2][0] = (t >= t_ref_up && t < t_ref_dn) ? V_op2 : V_op1;
            g_in[3][0] = t >= t_en;
            g_in[4][0] = 0.0;     /* Kp_amp */
            g_in[5][0] = 0.4;     /* Ki_amp */
            ctl_output();
            ctl_update();
            dA_next = g_out[0][0]; dB_next = g_out[0][1]; en_next = g_out[1][0] > 0.5;
            if (g_out[3][2] > m_max) m_max = g_out[3][2];
            if (!fault_seen && g_out[3][3] != 0) { fault_seen = (int)g_out[3][3]; t_fault = t; }
            if (csv)
                fprintf(csv, "%.6f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%d,%d,%.4f\n", t, vo, iL,
                        vo/((t >= t_load_on && t < t_load_off) ? 12.5 : 25.0),
                        g_out[3][0], g_out[3][1], g_out[3][2], (int)g_out[3][3], (int)g_out[1][0],
                        il_abs_max);
            il_abs_max = 0;
            k_samp++;
        }

        /* Carrier 0..1..0 over one period, valley at the sample instant. */
        double ph = fmod(t, Tc)/Tc;
        double car = 1 - fabs(2*ph - 1);
        int wantA = car < dA, wantB = car < dB;    /* top device on */
        if (wantA != sA) { sA = wantA; t_on_A = t + td; }
        if (wantB != sB) { sB = wantB; t_on_B = t + td; }
        int deadA = t < t_on_A, deadB = t < t_on_B;

        /* Leg voltages: gated device, or the diode set by the current sign. */
        double vA, vB, vinv, Rpath = RLf;
        int conducting = 1;
        if (!en) {
            /* All gates off: the bridge rectifies; current flows only while
             * |vo| exceeds the dc link. */
            if (fabs(iL) < 1e-6 && fabs(vo) < vdc) { conducting = 0; vinv = vo; }
            else vinv = iL > 0 ? -vdc : vdc;
        } else {
            if (deadA) vA = iL > 0 ? 0 : vdc; else vA = sA ? vdc : 0;
            if (deadB) vB = iL > 0 ? vdc : 0; else vB = sB ? vdc : 0;
            vinv = vA - vB;
            Rpath += 2*Ron;
            vinv -= (iL > 0 ? 1 : -1)*Vdrop*(fabs(iL) > 1e-3);
        }

        double Rl = (t >= t_load_on && t < t_load_off) ? 1/(1/R_base + 1/R_step) : R_base;
        double iLold = iL;
        if (conducting) {
            iL += dt*(vinv - vo - Rpath*iL)/Lf;
            if (!en && iLold*iL < 0) iL = 0;       /* diodes block reversal */
        }
        vo += dt*(iL - vo/Rl - vo/Rb)/Cf;
        /* dc link: source through Rs, bridge input current = iL*(sA - sB) */
        double ibr = en ? iL*((deadA ? (iL < 0) : sA) - (deadB ? (iL > 0) : sB))
                        : (conducting ? fabs(iL) * -1 : 0);
        vdc += dt*((Vs - vdc)/Rs - ibr)/Cdc;

        if (fabs(iL) > il_abs_max) il_abs_max = fabs(iL);
        filt_step(&fv, vo, dt);
        filt_step(&fi, iL, dt);
        filt_step(&fo, vo/Rl, dt);
        filt_step(&fd, vdc, dt);

        /* Steady-state windows: last 5 cycles before each event */
        double w0[4] = {t_load_on - 5/60.0, t_ref_up - 5/60.0, t_ref_dn - 5/60.0, t_load_off - 5/60.0};
        for (int w = 0; w < 4; w++) {
            double ws = w0[w], we = w0[w] + 5/60.0;
            if (t >= ws && t < we) {
                win_v2 += vo*vo; win_i2 += iL*iL; win_io2 += (vo/Rl)*(vo/Rl);
                win_p += vo*vo/Rl; win_n += 1;
                if (fabs(iL) > ilpk) ilpk = fabs(iL);
                if (fabs(vo) > vopk) vopk = fabs(vo);
            }
            if (t < we && t + dt >= we && win_n > 0) {
                printf("window %d (%.3f-%.3f s, R=%.1f): Vrms=%.3f ILrms=%.3f Iorms=%.3f P=%.2f W "
                       "iL_pk=%.2f vo_pk=%.2f  meas: Vpk=%.2f Vrms=%.2f m=%.3f\n",
                       w, ws, we, Rl, sqrt(win_v2/win_n), sqrt(win_i2/win_n), sqrt(win_io2/win_n),
                       win_p/win_n, ilpk, vopk, g_out[3][0], g_out[3][4], g_out[3][2]);
                win_v2 = win_i2 = win_io2 = win_p = win_n = ilpk = vopk = 0;
            }
        }
        t += dt;
    }
    printf("max m = %.3f, first fault bits = %d at t = %.4f s\n", m_max, fault_seen, t_fault);
    if (csv) fclose(csv);
    return 0;
}
