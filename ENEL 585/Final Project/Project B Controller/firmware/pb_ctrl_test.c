/* Test harness: exposes the controller in pb_ctrl_core.c to Python (ctypes).
 * Build: gcc -O2 -shared -fPIC -o libpbctrl.so pb_ctrl_test.c -lm   (simulate.py does this)
 */
#include "pb_ctrl_core.c"

static pb_param_t P;
static pb_state_t S;

/* p: N, Ts, v_scale, v_offset, i_scale, i_offset, trip_vo, trip_il, trip_io,
 *    trip_vdc_hi, trip_vdc_lo, vdc_start_min, m_max, x_max, ramp_rate */
void t_init(const double *p)
{
    P.N = (int)(p[0] + 0.5);
    P.Ts = (float)p[1];
    P.v_scale = (float)p[2];
    P.v_offset = (float)p[3];
    P.i_scale = (float)p[4];
    P.i_offset = (float)p[5];
    P.trip_vo = (float)p[6];
    P.trip_il = (float)p[7];
    P.trip_io = (float)p[8];
    P.trip_vdc_hi = (float)p[9];
    P.trip_vdc_lo = (float)p[10];
    P.vdc_start_min = (float)p[11];
    P.m_max = (float)p[12];
    P.x_max = (float)p[13];
    P.ramp_rate = (float)p[14];
    pb_init(&S, &P);
}

/* in: vpin_vdc, vpin_il, vpin_vo, vpin_io, enable, vref_rms, kp, ki, ff,
 *     trip_vo_set, trip_il_set, trip_io_set
 * out: dA, dB, pwm_en, fault, amp, m, x_amp, vref, vdc, il, vo, io */
void t_step(const double *in, double *out)
{
    pb_in_t u;
    pb_out_t o;
    pb_state_t ns;
    u.vpin_vdc = (float)in[0];
    u.vpin_il = (float)in[1];
    u.vpin_vo = (float)in[2];
    u.vpin_io = (float)in[3];
    u.enable = (float)in[4];
    u.vref_rms = (float)in[5];
    u.kp = (float)in[6];
    u.ki = (float)in[7];
    u.ff = (float)in[8];
    u.trip_vo_set = (float)in[9];
    u.trip_il_set = (float)in[10];
    u.trip_io_set = (float)in[11];
    pb_step(&u, &S, &P, &o, &ns);
    S = ns;
    out[0] = o.dA; out[1] = o.dB; out[2] = o.pwm_en; out[3] = o.fault;
    out[4] = o.amp; out[5] = o.m; out[6] = o.x_amp; out[7] = o.vref;
    out[8] = o.vdc; out[9] = o.il; out[10] = o.vo; out[11] = o.io;
}
