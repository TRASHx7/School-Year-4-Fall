/* Work on a copy of the state; UpdateFcn commits it, so a repeated call at the
 * same sample time cannot advance the controller twice. */
g8_state s = g8;
float pin[4];
pin[0] = (float)InputSignal(0, 0);  /* B2: VProbe 1 */
pin[1] = (float)InputSignal(0, 1);  /* B0: CProbe 2 */
pin[2] = (float)InputSignal(0, 2);  /* B1: CProbe 1 */
pin[3] = (float)InputSignal(1, 0);  /* A6: VProbe 2 */
const float vref_rms = (float)InputSignal(2, 0);
const int   enable   = InputSignal(3, 0) > 0.5;
const float kp       = (float)InputSignal(4, 0);
const float ki       = (float)InputSignal(5, 0);

const float vo  = g8_meas(pin, P_SRC_VO, P_KVO, P_OVO, 0.0f);
const float il  = g8_meas(pin, P_SRC_IL, P_KIL, P_OIL, 0.0f);
const float io  = g8_meas(pin, P_SRC_IO, P_KIO, P_OIO, 0.0f);
const float vdc = g8_meas(pin, P_SRC_DC, P_KDC, P_ODC, g8_p[P_VDC_NOM]);

s.vdcf += g8_p[P_TS]/g8_p[P_TAU_DC]*(vdc - s.vdcf);

/* Protection, every sample. A trip latches until the enable switch is set
 * to 0; while disabled the bits show any condition that is still present. */
if (!enable)
    s.fault = 0;
if (fabsf(vo) > g8_p[P_VO_TRIP]) s.fault |= F_VO;
if (fabsf(il) > g8_p[P_IL_TRIP]) s.fault |= F_IL;
if (g8_p[P_SRC_IO] > 0.5f && fabsf(io) > g8_p[P_IO_TRIP]) s.fault |= F_IO;
if (g8_p[P_SRC_DC] > 0.5f && vdc > g8_p[P_DC_TRIP]) s.fault |= F_DC;

if (!enable || s.fault) {
    s.run = 0;
} else if (!s.run && s.vdcf >= g8_p[P_DC_MIN]) {
    /* Start at a zero crossing with zero amplitude; the slew limit ramps it. */
    g8_state zero = {0};
    zero.vdcf = s.vdcf;
    s = zero;
    s.run = 1;
}

/* Half-cycle boundary: the sums now hold one complete half cycle. */
if (s.run && (s.n == 0 || s.n == g8_NH) && s.cnt == g8_NH) {
    const float AI = 2.0f*s.sI/(float)g8_NH;
    const float AQ = 2.0f*s.sQ/(float)g8_NH;
    /* Average with the previous half: a full-cycle window rejects dc offset
     * and even harmonics as well as the odd ones. */
    const float AIf = s.halves > 0 ? 0.5f*(AI + s.AIh) : AI;
    const float AQf = s.halves > 0 ? 0.5f*(AQ + s.AQh) : AQ;
    s.AIh = AI;
    s.AQh = AQ;
    s.vpk = sqrtf(AIf*AIf + AQf*AQf)/g8_p[P_H60];
    s.halves++;

    /* Compare with the command applied over the same window, so the trim
     * corrects losses rather than the measurement delay during a ramp. */
    const float r_win = s.halves > 1 ? 0.5f*(s.vc + s.vc1) : s.vc;
    const float e = r_win - s.vpk;
    if (s.halves > 1) {
        /* Conditional integration: hold the trim while the modulator is at
         * its limit and the error would push it further. */
        if (!(s.m >= g8_p[P_M_MAX] - 1e-4f && e > 0.0f))
            s.x += ki*e;
        s.x = g8_clamp(s.x, -g8_p[P_X_MAX], g8_p[P_X_MAX]);
    }

    /* Current limit: reduce the amplitude while the half-cycle peak of the
     * sensed inductor current is above I_LIM, recover slowly once below. */
    if (s.ilpk > g8_p[P_I_LIM])
        s.fold += g8_p[P_K_FOLD]*(s.ilpk - g8_p[P_I_LIM]);
    else
        s.fold -= g8_p[P_FOLD_DEC];
    s.fold = g8_clamp(s.fold, 0.0f, 1.41421356f*g8_p[P_VREF_MAX]);

    /* Slew-limited amplitude command for the next half cycle. */
    float target = 1.41421356f*g8_clamp(vref_rms, 0.0f, g8_p[P_VREF_MAX]) - s.fold;
    if (target < 0.0f) target = 0.0f;
    s.vc1 = s.vc;
    s.vc += g8_clamp(target - s.vc, -g8_p[P_SLEW], g8_p[P_SLEW]);

    /* Feedforward over the measured dc link plus the trim. */
    float a = s.vc + s.x + (s.halves > 1 ? kp*e : 0.0f);
    if (a < 0.0f) a = 0.0f;
    s.m = g8_clamp(a/(s.vdcf > 1.0f ? s.vdcf : 1.0f), 0.0f, g8_p[P_M_MAX]);

    s.sI = 0.0f;
    s.sQ = 0.0f;
    s.ilpk = 0.0f;
    s.cnt = 0;

    if (s.n == 0) {
        s.vrms  = sqrtf(s.s_v2/(float)g8_N)/g8_p[P_H60];
        s.ilrms = sqrtf(s.s_il2/(float)g8_N);
        s.pout  = s.s_p/(float)g8_N;
        s.s_v2 = s.s_il2 = s.s_io2 = s.s_p = 0.0f;
    }
}

float dA = 0.5f;
if (s.run) {
    const float sn = g8_sin[s.n];
    dA = 0.5f + 0.5f*s.m*sn;
    s.sI += vo*sn;
    s.sQ += vo*g8_cos[s.n];
    s.cnt++;
    s.s_v2  += vo*vo;
    s.s_il2 += il*il;
    s.s_io2 += io*io;
    s.s_p   += vo*io;
    if (fabsf(il) > s.ilpk) s.ilpk = fabsf(il);
    s.n = s.n + 1 >= g8_N ? 0 : s.n + 1;
}

/* Unipolar SPWM: leg B compares -m*sin with the same carrier. */
OutputSignal(0, 0) = dA;
OutputSignal(0, 1) = 1.0f - dA;
OutputSignal(1, 0) = s.run ? 1.0 : 0.0;
OutputSignal(2, 0) = vo;
OutputSignal(2, 1) = il;
OutputSignal(2, 2) = io;
OutputSignal(3, 0) = s.vpk;
OutputSignal(3, 1) = s.vc;
OutputSignal(3, 2) = s.m;
OutputSignal(3, 3) = s.fault;
OutputSignal(3, 4) = s.vrms;
OutputSignal(3, 5) = s.ilrms;
OutputSignal(3, 6) = s.pout;
g8_next = s;
