const double t = CurrentTime;
OutputSignal(0, 0) = (t >= ParamRealData(0, T_REF_UP) && t < ParamRealData(0, T_REF_DN))
                     ? ParamRealData(0, V_OP2) : ParamRealData(0, V_OP1);
OutputSignal(1, 0) = t >= ParamRealData(0, T_EN) ? 1.0 : 0.0;
OutputSignal(2, 0) = (t >= ParamRealData(0, T_LOAD_ON) && t < ParamRealData(0, T_LOAD_OFF))
                     ? 1.0 : 0.0;
