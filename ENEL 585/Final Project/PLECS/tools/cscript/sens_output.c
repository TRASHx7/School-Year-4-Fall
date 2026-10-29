/* Each channel: state 2c is the first pole, state 2c+1 the output. */
OutputSignal(0, 0) = s_pin(ContState(1), ParamRealData(0, S_KV));   /* B2: vo  */
OutputSignal(0, 1) = s_pin(ContState(3), ParamRealData(0, S_KI));   /* B0: iL  */
OutputSignal(0, 2) = s_pin(ContState(5), ParamRealData(0, S_KI));   /* B1: io  */
OutputSignal(1, 0) = s_pin(ContState(7), ParamRealData(0, S_KV));   /* A6: vdc */
