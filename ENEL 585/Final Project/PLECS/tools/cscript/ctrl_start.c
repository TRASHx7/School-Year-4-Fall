/* Copy the parameters and build the sine/cosine tables once, before the PWM
 * starts, so the per-step task does lookups instead of sin() calls. */
int k;
g8_state zero = {0};
for (k = 0; k < P_NUM; k++)
    g8_p[k] = (float)ParamRealData(0, k);
g8_N = (int)(g8_p[P_N] + 0.5f);
if (g8_N > G8_NMAX) g8_N = G8_NMAX;
g8_N -= g8_N % 2;                   /* even, so a half cycle is whole samples */
g8_NH = g8_N/2;
for (k = 0; k < g8_N; k++) {
    g8_sin[k] = (float)sin(6.283185307179586*k/g8_N);
    g8_cos[k] = (float)cos(6.283185307179586*k/g8_N);
}
g8 = zero;
g8.vdcf = g8_p[P_VDC_NOM];
g8_next = g8;
