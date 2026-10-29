int c;
s_wz  = 6.283185307179586*ParamRealData(0, S_FZ);
s_wp1 = 6.283185307179586*ParamRealData(0, S_FP1);
s_wp2 = 6.283185307179586*ParamRealData(0, S_FP2);
s_q   = ParamRealData(0, S_VREF)/pow(2.0, ParamRealData(0, S_BITS));
for (c = 0; c < 8; c++)
    ContState(c) = 0.0;
/* dc-link channel starts settled at the supply voltage */
ContState(6) = ParamRealData(0, S_VDC0);
ContState(7) = ParamRealData(0, S_VDC0);
