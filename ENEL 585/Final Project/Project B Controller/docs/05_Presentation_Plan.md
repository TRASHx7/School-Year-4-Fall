# Final Presentation Plan (Tue Dec 8, ENA13, 15-minute slot)

Group mark (10 points): experimental evidence 4, comparison and explanation 4, communication 2.
No hardware is operated. Every member presents. Then each student answers individual questions
unaided (8 points): **one design decision and one measured result**, with follow-ups.

## Slides (about 10 minutes, 9 slides)

| # | Slide | Content | Presenter |
|---|---|---|---|
| 1 | Station and targets | Circuit with probes, OP1 and OP2, the change to 55 V | |
| 2 | Limits | What limits power (DC voltage and bank), margins table | |
| 3 | Design choices | 9.96 kHz unipolar, sampling, sensing and protection | |
| 4 | Control design | Structure, why gain stabilization, Kp and Ki, margins | |
| 5 | Validation path | Averaged vs switched vs HIL, loop-only reference step | |
| 6 | Steady state | Measured v_o and i_L at OP1 and OP2 next to simulation; comparison table | |
| 7 | Load step | Measured vs simulated, dead-time explanation | |
| 8 | Reference step | Measured vs simulated | |
| 9 | Conclusions | What matched, what did not and why, losses, improvements | |

Leave about 5 minutes for questions. Rehearse with a timer.

## Individual questions: be ready to explain without notes

Design decisions:
- Why 55 V and not 50 V; what limits the output power.
- Why 9.96 kHz and unipolar; how the ripple formula works; why sample at the valley.
- Why Kp is 0.01: the resonant peak, gain stabilization, f_s/6.
- How the resonant term works and why it gives zero 60 Hz error; what Ki sets.
- Why the reference changes at a zero crossing; what feedforward does.
- How each trip level was chosen; what happens on a trip.
- ADC scaling formula for one channel, from the setup guide to the code.

Measured results:
- The output amplitude and its error: where the error comes from.
- The inductor ripple and peak: compare with V_dc/(8 L f_sw).
- The load-step dip: why the averaged model misses it.
- The reference step: why it settles in 2 cycles, and in 4 with feedforward off.
- THD and the notches at the current zero crossings.
- Input vs output power: where the losses go.

Each member should be able to derive, on a whiteboard: G_p(s) for the LC filter with a resistive
load, f0 and Z0, the 1.5 T_s delay, the ripple formula, and one ADC conversion.
