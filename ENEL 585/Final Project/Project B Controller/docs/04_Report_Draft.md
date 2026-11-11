# Final Report Draft (due Fri Dec 11, 23:59)

About 10 pages excluding appendices, for a reader who knows power electronics but has not seen
the station. Rubric (10 points): hardware analysis 2, control and model validation 3, experimental
evidence and comparison 3, interpretation and losses 2. Predictions are filled in below; replace
every `[MEASURED]` after Bench 3. Fix the four proposal-feedback items (marked ✱).

Every plot needs axes, units, operating conditions and probe scaling, and the model and firmware
version used.

---

## 1. Station, operating points and targets (about 1.5 pages)

- Station-sheet circuit with our additions (probes, ADC pins, gate mapping, instruments): the
  connection diagram. Use the HIL pin mapping (CProbe1 = i_L1, CProbe2 = i_o).
- Operating points and the change from the proposal: OP1 25 V rms at 25 Ω (25 W), OP2 30 V rms at
  12.5 Ω (72 W); V_dc raised from 50 V to 55 V. Give both values and the reason
  (`01_Design_Review.md` §2).
- Steady-state targets table (from the proposal, corrected): v_o, i_o, P_out, i_L rms and ripple,
  capacitor current, input current.
- ✱ What limits the output power: DC voltage through the modulation limit (34.5 V rms at 58 V,
  after dead time and drops) together with the minimum bank resistance (12.5 Ω): about 95 W.
  Show that the inductor, IGBT and ITECH current limits are far away.

## 2. Hardware analysis and switching frequency (about 1.5 pages)

- Filter: L = 94 µH, C = 31 µF seen by the loop, f0 = 2.95 kHz, Z0 = 1.74 Ω, Q from 7 (12.5 Ω) to
  144 (250 Ω). Role of the filter (removes the 19.9 kHz unipolar ripple voltage from the load);
  effect of the ±20 % inductance (f0 from 2.69 to 3.30 kHz).
- Ripple: ΔI_pp = V_dc/(8 L f_sw) = 7.3 A worst case; rms and peak inductor currents against the
  ratings (table in `01_Design_Review.md` §2). Compare predicted, simulated and measured.
- Switching frequency 9.960 kHz, unipolar, synchronous carrier (166 per cycle), sampling at the
  valley, τ = 1.5 T_s.
- ✱ Sensing: probe settings, ADC conversion formulas, the full ADC table including **i_o**, where
  every number comes from, headroom to the trips.
- ✱ Why the inductor current is measured (four reasons, `01_Design_Review.md` §4).
- Protection thresholds and firmware action.

## 3. Control design (about 2 pages)

- Objectives and structure: reference feedforward, m = v*/v_dc, PR controller implemented as
  demodulate, integrate and remodulate (exact 2 Ki s/(s² + ω1²)), soft start, zero-crossing
  reference steps, anti-windup.
- Plant G_p(s), sensing H(s) (bench and HIL versions), delay; the loop gain.
- Why an inner current loop cannot damp this filter (f0 > f_s/6, sensing lag), and the
  gain-stabilization choice of Kp (figure: `kp_limit.png`).
- Ki from the envelope model: crossover 9.5 Hz, PM 80°, τ_env = 16.8 ms.
- Predicted margins at all corners (table from `01_Design_Review.md` §6.5), Bode plot
  (`bode_loop.png`, `bode_loop_60Hz.png`).

## 4. Simulation and remote HIL validation (about 1.5 pages)

- Linearised (averaged) model vs switched simulation vs prediction, reference step with
  feedforward off (`sim_ref_step_ff0.png`): agreement with τ_env.
- Load step: averaged predicts 0.3 %, switched shows 2.9 %. Explain with the dead-time error
  depending on whether the ripple makes i_L cross zero in each switching period.
- HIL results: the checklist table from `02_HIL_Signoff.md` §6 with what was observed `[MEASURED]`.
- **Model limitations**: the HIL sensing model has one pole instead of two; ITECH modelled as an
  ideal CV source behind 0.05 Ω; device model (constant drop plus resistance); switching losses
  absent; the valley sample aliases capacitor ripple into a 60 Hz error (about −1 % on the HIL, +0.5 to
  1.3 % on the bench model); dead time assumed 3.3 µs (driver interlock).

## 5. Experimental results (about 2 pages)

Comparison table (the core of the experimental-evidence mark):

| Quantity | Target | Prediction (bench sim) | HIL | Measured | Difference and reason |
|---|---|---|---|---|---|
| OP1 v_o (V rms) | 25.0 | 25.2 | `[HIL]` | `[MEASURED]` | |
| OP1 i_L rms / pk / ripple (A) | 2.07 / 5.1 / 7.3 | 2.11 / 5.12 / 7.5 | | | |
| OP1 ITECH V, I | 55 V, 0.53 A | 55.0 V, 0.51 A | | | |
| OP1 P_out (W) | 25 | 25.4 | | | |
| OP1 v_o THD (%) | | 1.2 | | | |
| OP2 v_o (V rms) | 30.0 | 30.4 | | | |
| OP2 i_L rms / pk / ripple (A) | 2.96 / 7.1 / 7.3 | 2.99 / 7.30 / 7.7 | | | |
| OP2 ITECH V, I | 55 V, 1.54 A | 54.9 V, 1.40 A | | | |
| OP2 P_out (W) | 72 | 74.1 | | | |
| OP2 v_o THD (%) | | 4.9 | | | |
| Load step: v_o dip, recovery | | 2.9 %, about 3 cycles | | | |
| Reference step: cycles to 2 %, overshoot | | 2 cycles, 1 % | | | |
| Efficiency P_out/P_in | | 91 % / 96 % (conduction only) | | | |

Figures: steady state at each operating point (v_o, i_L), load step, reference step, each overlaid
or side by side with the simulation at the same conditions.

## 6. Interpretation, losses and improvements (about 1.5 pages)

- Discrepancies with evidence: output amplitude offsets (sensing gain 0.995 at 60 Hz, ripple
  aliasing, probe accuracy), THD from dead time, load-step dip from the load-dependent dead-time error.
- Loss estimate: conduction (about 2.6 W at OP1 and 2.9 W at OP2 from the simulation: 2 × 0.8 V
  plus 2 × 25 mΩ plus the inductor DCR), switching (use E_on, E_off, E_rr from the SKM50GB12T4
  datasheet at its test condition, scaled linearly to 55 V and the average switched current;
  expect about 1 W), inductor core and AC copper losses from the 7 A ripple at 20 kHz (largest
  unknown). Compare with measured P_in − P_out.
- Thermal: all currents far below ratings; the box stayed below its 71 °C trip.
- Improvements: dead-time compensation; ADC oversampling to remove ripple aliasing; double-update
  PWM (f_s = 2 f_sw) so capacitor-current active damping becomes possible (f_s/6 = 3.3 kHz is above
  f0); a DC integrator to null any output DC offset.
- Unresolved questions and useful further tests.

## Appendices and ZIP

Appendices: calculations (`design.py` printout), full ADC table, connection diagram, protection
table, HIL checklist results, bench log.

ZIP contents: `plecs/Controller.plecs` and `plecs/ProjectB_Sim.plecs`; the Coder settings
(screenshot of target, parameter-inlining exceptions); `plecs/controller_cscript_sections.txt`;
`firmware/`; `design/` (scripts and JSON); HIL model changes (`R_load_A = 25`, `R_load_B = 25`,
panel settings); raw scope data; bench log.

## AI disclosure (suggested wording; edit to match what you actually did)

> Claude (Anthropic) was used to design the controller structure and gains, write the controller
> C code, the Python design and switched-simulation scripts and the script that generates the PLECS
> models, and to draft the design-review notes, test procedures and the structure of this report.
> The group reviewed, ran and verified all of it on the remote HIL and the bench, and wrote the
> final text and conclusions. All measured data are our own.
