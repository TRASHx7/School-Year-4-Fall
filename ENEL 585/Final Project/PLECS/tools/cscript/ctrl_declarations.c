/* ENEL 585 Project B, Group 8: single-phase standalone inverter controller.
 * The same code runs in the switched station model and on the LAUNCHXL-F28P55X.
 *
 * Inputs  1: ADC unit B pins [B2 B0 B1] (V)    2: ADC unit A pin [A6] (V)
 *         3: Vref_rms (V)   4: enable (0/1)   5: Kp_amp   6: Ki_amp
 * Outputs 1: [dA dB] leg duties   2: PWM enable to Powerstage Protection
 *         3: [vo iL io] (V, A)    4: [Vpk_meas Vpk_cmd m fault Vrms ILrms Pout]
 *
 * Runs once per carrier period. The 60 Hz reference is sampled at n/N of a
 * period (n counts carrier periods), so it stays synchronous with the carrier.
 * The output amplitude is measured by synchronous demodulation over the last
 * full cycle and trimmed by an integrator; the modulation index changes only
 * at the reference zero crossings (n = 0 and n = N/2).
 */
#include <math.h>

#define G8_NMAX 256                 /* sine-table capacity */

/* Parameter vector ctl_par (see the model's init commands) */
enum {
    P_N, P_TS,                      /* samples per 60 Hz period, sample time */
    P_KVO, P_OVO, P_KIL, P_OIL,     /* pin-to-physical gain and pin offset */
    P_KIO, P_OIO, P_KDC, P_ODC,
    P_SRC_VO, P_SRC_IL, P_SRC_IO, P_SRC_DC, /* pin index 1..4, 0 = not wired */
    P_VDC_NOM, P_H60,               /* dc voltage if unmeasured, sensor gain at 60 Hz */
    P_VO_TRIP, P_IL_TRIP, P_IO_TRIP, P_DC_TRIP, /* protection thresholds */
    P_DC_MIN,                       /* dc voltage needed before switching starts */
    P_VREF_MAX,                     /* largest accepted Vref_rms */
    P_SLEW,                         /* amplitude slew, V pk per half cycle */
    P_M_MAX, P_X_MAX,               /* modulation and integrator limits */
    P_I_LIM, P_K_FOLD, P_FOLD_DEC,  /* inductor-current limit foldback */
    P_TAU_DC,                       /* dc voltage filter time constant */
    P_NUM
};

/* Latched fault bits */
#define F_VO 1                      /* output overvoltage */
#define F_IL 2                      /* inductor overcurrent */
#define F_IO 4                      /* output overcurrent */
#define F_DC 8                      /* dc-link overvoltage */

typedef struct {
    int   n;                        /* index in the 60 Hz period, 0..N-1 */
    int   cnt;                      /* samples summed in this half cycle */
    int   halves;                   /* half cycles completed since start */
    int   run;                      /* 1 while the bridge switches */
    int   fault;                    /* latched fault bits */
    float sI, sQ;                   /* half-cycle sums of vo*sin, vo*cos */
    float AIh, AQh;                 /* previous half-cycle amplitudes */
    float s_v2, s_il2, s_io2, s_p;  /* full-cycle sums for RMS and power */
    float ilpk;                     /* half-cycle peak |iL| */
    float vc, vc1;                  /* amplitude command, this and last half */
    float x;                        /* integral trim, V pk */
    float fold;                     /* current-limit foldback, V pk */
    float m;                        /* modulation index for this half cycle */
    float vdcf;                     /* filtered dc-link voltage */
    float vpk;                      /* measured output amplitude, V pk */
    float vrms, ilrms, pout;        /* last full-cycle results */
} g8_state;

static g8_state g8, g8_next;        /* committed state, state after this step */
static float g8_sin[G8_NMAX], g8_cos[G8_NMAX];
static float g8_p[P_NUM];
static int   g8_N, g8_NH;

static float g8_clamp(float v, float lo, float hi)
{
    return v < lo ? lo : (v > hi ? hi : v);
}

/* Physical value of signal 'src' (pin index 1..4), or dflt if not wired. */
static float g8_meas(const float *pin, int k_src, int k_gain, int k_ofs, float dflt)
{
    int src = (int)(g8_p[k_src] + 0.5f);
    if (src < 1 || src > 4)
        return dflt;
    return g8_p[k_gain]*(pin[src - 1] - g8_p[k_ofs]);
}
