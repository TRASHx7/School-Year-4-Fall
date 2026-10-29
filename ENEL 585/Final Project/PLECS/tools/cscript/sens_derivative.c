double u[4];
int c;
u[0] = InputSignal(0, 3);                       /* vo */
u[1] = InputSignal(0, 0);                       /* iL */
u[2] = InputSignal(0, 1) + InputSignal(0, 2);   /* io = iR1 + iR2 */
u[3] = InputSignal(0, 4);                       /* vdc */
for (c = 0; c < 4; c++) {
    double d1 = s_wp1*(u[c] - ContState(2*c));
    double w  = ContState(2*c) + d1/s_wz;       /* zero */
    ContDeriv(2*c)     = d1;
    ContDeriv(2*c + 1) = s_wp2*(w - ContState(2*c + 1));
}
