/* Interface-board sensing chain (Inverter Box Setup Guide), simulation only.
 * Probe -> divider -> active low-pass -> ADC pin, modelled as
 *   H(s) = (1 + s/wz) / ((1 + s/wp1)(1 + s/wp2)),  fz = 1.5 kHz, fp = 700/900 Hz
 * (0.5 % low and -6 deg at 60 Hz, -21 dB at 5 kHz), then
 *   V_pin = 1.667 V + k*signal, 12-bit quantisation over 0..3.3 V.
 * Input  (probe order): [iL, iR1, iR2, vo, vdc]
 * Output 1: pins [B2 B0 B1] = [vo iL io]   2: pin [A6] = vdc
 */
#include <math.h>
enum { S_FZ, S_FP1, S_FP2, S_OFS, S_KV, S_KI, S_VREF, S_BITS, S_VDC0, S_NUM };
static double s_wz, s_wp1, s_wp2, s_q;

static double s_pin(double y, double k)
{
    double v = ParamRealData(0, S_OFS) + k*y;
    v = s_q*floor(v/s_q + 0.5);
    if (v < 0.0) v = 0.0;
    if (v > ParamRealData(0, S_VREF)) v = ParamRealData(0, S_VREF);
    return v;
}
