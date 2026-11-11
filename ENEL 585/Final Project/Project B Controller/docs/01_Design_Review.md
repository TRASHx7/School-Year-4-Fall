# Design Review Notes: Project B, Group 8 (Station 5 per the Oct 29 list)

The review is 10 minutes at the start of Bench 2 (Fri Nov 20): about 4 minutes walking through the
design, then questions. Every member may be asked anything, and answers must be unaided by AI. Read
this whole document as a group, run `design.py` and `simulate.py` yourselves, and practise
explaining each section without notes.

Rubric (8 points): switching frequency and operating limits 2, sensing and protection 1.5,
bring-up readiness 1.5, control design 3.

Suggested 4-minute walk-through, one person per block:

1. Station and operating points, what limits the power (§1, §2). About 45 s.
2. Switching frequency and modulation (§3). About 30 s.
3. Sensing, ADC scaling and protection (§4, §5). About 45 s.
4. Control design: plant, structure, compensator, predicted crossover and phase margin (§6). About 90 s.
5. Switched simulation compared with the prediction (§7), then bring-up (§8). About 30 s.

Have on screen or paper: `figures/bode_plant_sensor.png`, `figures/bode_loop.png`,
`figures/kp_limit.png`, `figures/sim_ref_step_ff0.png`, `figures/sim_load_step.png`, the
connection diagram, and the tables below.

---

## 1. Station

| Item | Value | Source |
|---|---|---|
| Source | ITECH IT-M3632, ≤ 58 V (OVP 60 V), current limit set to 10 A | Station sheet, App. H |
| Bridge | Two SEMITEACH legs (SKM50GB12T4, 50 A), C_dc = 1.1 mF | Station sheet |
| Filter | Two branches, each 47 µH ±20 % and 62 µF; load between the capacitor taps; star nC floating | Station sheet |
| Loop seen by the controller | L = 2 × 47 = **94 µH**, C = 62/2 = **31 µF** (the two capacitors are in series through nC), R_L = 23.6 mΩ | |
| Resonance | f0 = 1/(2π√(LC)) = **2.95 kHz**, Z0 = √(L/C) = **1.74 Ω** | |
| Load | 20 × 250 Ω branches: 12.5 Ω to 250 Ω | |
| Inductor ratings | 19.3 A rms (50 K rise), 32.3 A typical saturation | Würth 7443783533470 |

## 2. Operating points, envelope and what limits the power

Proposal feedback asked us to "state clearly what limits the output power, covering both the dc
supply limit and the load."

**What limits the output voltage.** The bridge can produce at most m_max · V_dc of peak voltage.
Part of that is lost before it reaches the filter:

- Dead time: the SKHI 22A driver enforces an interlock of about 3.3 µs. Each leg loses
  t_d · f_sw · V_dc of average voltage against the current, so the bridge loses
  2 t_d f_sw V_dc = 3.6 V, a square wave in phase with the current. Its fundamental is
  (4/π)(3.6) = **4.6 V peak** at 55 V.
- Device drops: two devices always conduct, about 1 V each, so **about 2 V**.

With m_max = 0.96 and the ITECH at its 58 V limit, the largest output is
(0.96 × 58 − 4.9 − 2)/√2 = **34.5 V rms**. The ideal value, 58/√2 = 41 V rms, is not reachable.

**What limits the power.** Power is V_o²/R. The voltage limit above combined with the smallest
bank resistance (12.5 Ω, all 20 switches closed) gives **P_max ≈ 95 W**. At that point every
current is far from its rating: inductor 2.8 A rms against 19.3 A, IGBT about 7 A peak against
50 A, ITECH about 1.9 A against its 10 A limit. **So the binding constraint is the DC voltage limit
(through the modulation limit) together with the minimum bank resistance.** The current ratings and
the ITECH current limit are not binding for this station.

**Why the DC link moves from 50 V to 55 V.** At OP2 the inverter must produce
42.4 + 4.6 + 2 ≈ 49.1 V peak. That is m = 0.98 at 50 V, above m_max = 0.96, so the controller
would saturate and the output would distort. At 55 V, **m = 0.89**, leaving 7 % headroom. 55 V is
still under the 58 V station limit.

| | OP1 | OP2 | Source |
|---|---|---|---|
| Output | 25 V rms (35.4 V pk) | 30 V rms (42.4 V pk) | proposal |
| Load | 25 Ω (10 switches) | 12.5 Ω (20 switches) | proposal |
| Output power | 25 W | 72 W | V²/R |
| Load current | 1.00 A rms | 2.40 A rms | V/R |
| Capacitor current | 0.29 A rms | 0.35 A rms | ωCV |
| Inductor current (60 Hz + ripple) | 2.07 A rms | 2.96 A rms | design.py |
| Inductor ripple, worst | 7.30 A pk-pk | 7.30 A pk-pk | V_dc/(8 L f_sw) |
| Inductor peak | 5.1 A | 7.1 A | fundamental + half ripple |
| Modulation index needed | 0.76 | 0.89 | incl. dead time and drops |
| DC current (85 % assumed) | 0.53 A | 1.54 A | |
| Margin, inductor rms | 89 % | 85 % | 1 − I/19.3 A |
| Margin, inductor peak to saturation | 84 % | 78 % | 1 − I/32.3 A |
| Margin, modulation | 20 % | 7 % | 1 − m/0.96 |

Ripple: unipolar SPWM puts the bridge voltage between 0 and ±V_dc at 2 f_sw. The worst instant is
when |v_o| = V_dc/2, giving ΔI_pp = V_dc/(8 L f_sw) = 55/(8 · 94 µH · 9960 Hz) = 7.3 A. The
ripple is large relative to the load current: at OP1 the inductor current crosses zero in most
switching periods. This matters for the dead-time distortion (§7) and is why we measure i_L.

## 3. Switching frequency and modulation

- **f_sw = 9.960 kHz**, chosen as the highest frequency under the 10 kHz lab limit (losses in the
  teaching inverter) that the ePWM up-down counter hits exactly while staying synchronous with
  60 Hz: f_sw = 50 MHz/(2 · round(50 MHz/(2 · 166 · 60))) = 166 × 60.001 Hz. The reference is
  read from a 166-entry sine table, as in Lab 2's LaunchPad programs.
- **Unipolar SPWM**: both legs compare their own duty (d_A = (1 + m)/2, d_B = (1 − m)/2) with the
  same carrier. The bridge voltage switches at 2 f_sw ≈ 19.9 kHz, which halves the ripple compared
  with bipolar at the same f_sw and puts the first ripple harmonics near 20 kHz, 6.8 × the 2.95 kHz
  resonance. An even carrier ratio is the usual choice for unipolar.
- **Why not higher**: lab limit and switching losses. **Why not lower**: at 5 kHz the ripple doubles
  to 14.6 A pk-pk, the peak inductor current at OP2 would approach the current probe's 10 A range,
  and the ripple would sit at 10 kHz, closer to the resonance.
- **Sampling**: one sample per carrier period, at the carrier valley, where both legs are in the
  middle of a zero state, so the sample is close to the period average. The duty is loaded at the
  next valley: total delay τ = 1.5 T_s = **150.6 µs** (Lecture 11, "The Sampling Delay").

## 4. Sensing and ADC scaling

Probes: two N2791A differential probes on 10:1, two 1146B current probes on 100 mV/A. Interface
board (Inverter Box Setup Guide v3): V_pin = 1.62 V + 0.213 V_BNC (voltage channels),
1.62 V + 0.154 V_BNC (current channels). The firmware converts pin voltage to physical units:

| Signal | Probe and setting | BNC | LaunchPad pin | Conversion in firmware |
|---|---|---|---|---|
| v_o (tap 1 + to tap 2 −) | VProbe1, N2791A 10:1 | VProbe 1 | **ADCINB2** | v = 46.95 V_pin − 76.06 |
| v_dc | VProbe2, N2791A 10:1 | VProbe 2 | **ADCINA6** | v = 46.95 V_pin − 76.06 |
| i_L1 (leg A to tap 1) | CProbe1, 1146B 100 mV/A | CProbe 1 | **ADCINA10** | i = 64.94 V_pin − 105.19 |
| i_o (tap 1 to the load) | CProbe2, 1146B 100 mV/A | CProbe 2 | **ADCINB0** | i = 64.94 V_pin − 105.19 |

Where the numbers come from (proposal feedback): for a voltage channel on 10:1,
V_pin = 1.62 + 0.213 · v/10, so v = (V_pin − 1.62) · 10/0.213 = 46.95 V_pin − 76.06. For a current
channel at 100 mV/A, V_pin = 1.62 + 0.154 · 0.1 · i, so i = (V_pin − 1.62)/0.0154. The pin
voltages below use those formulas; the ADC code is V_pin/3.3 × 4095.

| Signal | Point | Value | BNC | Pin (+ / −) | Code (+ / −) | Resolution |
|---|---|---|---|---|---|---|
| v_o | OP2 peak | 42.4 V | 4.24 V | 2.524 / 0.716 V | 3132 / 889 | 0.038 V |
| v_o | trip | 50 V | 5.00 V | 2.685 / 0.555 V | 3332 / 689 | |
| v_dc | nominal | 55 V | 5.50 V | 2.792 V | 3464 | 0.038 V |
| v_dc | OV trip | 58 V | 5.80 V | 2.855 V | 3543 | |
| i_L1 | OP2 peak (average) | 3.43 A | 0.343 V | 1.673 / 1.567 V | 2076 / 1945 | 0.052 A |
| i_L1 | trip | 7 A | 0.70 V | 1.728 / 1.512 V | 2144 / 1877 | |
| i_L1 | probe range | 10 A | 1.00 V | 1.774 / 1.466 V | 2201 / 1819 | |
| **i_o** | OP2 peak | 3.39 A | 0.339 V | 1.672 / 1.568 V | 2075 / 1945 | 0.052 A |
| **i_o** | trip | 6 A | 0.60 V | 1.712 / 1.528 V | 2125 / 1896 | |

Headroom: every trip is inside the ADC range (0 to 3.3 V). The voltage channels saturate at about
+79 V and −76 V, well above the 58 V DC trip. The current channels use only ±0.15 V of the range
because the 1146B never exceeds ±1 V; resolution is 0.052 A per code, fine for protection.

**Why we measure the inductor current** (proposal feedback):

1. It is the switch current. Overcurrent protection must watch the current through the IGBTs and the
   inductor. i_o misses the capacitor current, and a fault such as a shorted filter capacitor would
   raise i_L while i_o stays low.
2. The station sheet requires the inductor current waveform at every operating point and transient.
3. Appendix G asks us to compare simulated and measured peak and rms filter currents, including
   ripple, with the ratings.
4. It is a sanity check on the bench: i_L − i_o is the capacitor current, about 0.3 A rms.

We do **not** use i_L in an inner current loop, and §6.3 explains why.

**Sensing dynamics.** Each channel is a low-pass filter: two poles (723 Hz, 872 Hz) and a zero
(1447 Hz) on the bench board. At 60 Hz the gain is 0.995 (−6.2°). At 2.95 kHz it is about
−16 dB and −86°. **The posted HIL model only implements one pole (872 Hz) and the zero**, so on the
HIL the measurement is less filtered at the resonance (−5 dB instead of −16 dB). We designed for
both versions.

## 5. Protection

All trips are checked every control period, latch, and disable all six gate signals through the
TI Powerstage Protection block. A fault is cleared only by setting `enableswitch` to 0 (operator
acknowledgement); setting it back to 1 restarts with soft start if the condition has gone.

| Bit | Trip | Level | Margin from highest operating value | Why this level |
|---|---|---|---|---|
| 1 | \|v_o\| over | 50 V | 15 % above OP2 peak (42.4 V) | Above any overshoot seen in simulation (43.0 V), well inside ADC range |
| 2 | \|i_L\| over (sampled average) | 7 A | 2 × OP2 peak (3.4 A) | Average + half ripple (3.7 A) = 10.7 A, about the 1146B's 10 A range; inductor saturates at 32 A, IGBT 50 A |
| 4 | \|i_o\| over | 6 A | 77 % above OP2 peak (3.4 A) | Short or wrong bank setting |
| 8 | v_dc over | 58 V | 5.5 % over 55 V | Station sheet limit, under ITECH OVP (60 V) and ADC saturation (79 V) |
| 16 | v_dc under while running | 35 V | | ITECH output off or in current limit: stop switching cleanly |
| 32 | v_o polarity | vo·vref summed over a cycle < 0 during soft start | | Catches a reversed v_o probe before the resonant term winds up |

Other built-in limits: PWM does not start unless v_dc > 40 V; the reference is clamped to 49 V peak
(34.6 V rms); |m| ≤ 0.96; the resonant correction is clamped to 15 V (anti-windup).

For the HIL sign-off, `Trip_vo`, `Trip_iL` and `Trip_io` can be changed live in Watch to **lower**
a trip for a test. The firmware ignores any value above the design level, so they cannot be used to
raise a trip.

Hardware protection that firmware cannot replace: ITECH current limit (10 A) and OVP (60 V), the
inverter's thermal trip loop (gates disabled above 71 °C), and the gate drivers' own protection.

## 6. Control design

### 6.1 Objective and structure

Regulate v_o to a 60 Hz sine of commanded amplitude, with zero steady-state amplitude and phase
error to the measured signal, under load changes from 25 Ω to 12.5 Ω and DC-link changes.

```
 Vref_rms → A (soft start; steps at zero crossings) → vref = A sin θ ─┬──────────────── FF ─────┐
                                                                      │                         ▼
                                                     vo_meas ─(−)→ e ─┴→ Gc(s) = Kp + 2Ki s/(s²+ω1²) → (+) → v* → m = v*/v_dc → PWM
```

- **Reference feedforward**: the plant gain at 60 Hz is almost exactly 1
  (G_p(jω1) = 1/(1 − ω1²LC + jω1L/R) ≈ 1.0004), so v* = vref already gives the right output.
  Feedback only corrects what feedforward misses: dead time, device drops, sensing gain.
- **Normalization m = v*/v_dc** cancels DC-link changes (Lecture 11).
- **PR controller** in the course's form. The resonant term is implemented as demodulate,
  integrate, remodulate with the same sine and cosine table as the reference:
  x_d += 2 Ki T_s e sin θ, x_q += 2 Ki T_s e cos θ, u_r = x_d sin θ + x_q cos θ. Its transfer
  function is exactly 2 Ki s/(s² + ω1²), with the resonance locked to the reference frequency.

### 6.2 Plant and loop

- Plant (inverter voltage to output voltage), with R the load:
  G_p(s) = R / (s² L C R + s (L + R_L R C) + R + R_L)
- Sensing: H(s) = (1 + s/ω_z) / ((1 + s/ω_p1)(1 + s/ω_p2)) on the bench; (1 + s/ω_z)/(1 + s/ω_p2) on the HIL.
- Delay: e^(−s 1.5 T_s), τ = 150.6 µs.
- Loop gain (feedforward is outside the loop): **T(s) = G_c(s) G_p(s) H(s) e^(−sτ)**.

### 6.3 Why not an inner inductor-current loop

An inner i_L loop is the textbook way to damp an LC filter. Here it fails for three reasons:

1. **The resonance is above f_s/6.** With τ = 1.5 T_s, a proportional i_L feedback behaves like a
   resistor K e^(−jωτ) in series with L. Its real part turns negative above ωτ = 90°, that is
   f > 1/(4τ) = 1.66 kHz = f_s/6. At 2.95 kHz it adds **negative** damping.
2. **The sensing filter adds about 86° of extra lag at 2.95 kHz**, which makes point 1 worse.
3. The natural damping is very small: Q = R/Z0 is 7 at 12.5 Ω and 144 at 250 Ω.

So, as in the course's Ćuk example, we use **gain stabilization**: keep |T| at the resonant peak
well under 1 so the resonance cannot be destabilized, and get the 60 Hz performance from the
resonant term and feedforward.

### 6.4 Choosing the gains

Desired targets: **resonant peak of |T| ≤ −6 dB at the worst corner of the operating range**, and
**phase margin ≥ 60°** at the 60 Hz crossings. We checked 30 corners: bench and HIL sensing,
L at −20 %, nominal and +20 %, and R = 12.5, 25, 50, 250 Ω and open circuit.

- **Kp sets the gain at the resonance.** At 2.7 to 3.3 kHz the resonant term is only 2 Ki/ω ≈ 0.006 to 0.007,
  so |T| at the peak ≈ |Kp + 2Ki/(jω)| · Q-peak · |H|. The worst corner is HIL sensing,
  L + 20 %, R = 250 Ω, where |G_p H| peaks at 32.5 (+30 dB). The −6 dB requirement needs
  |G_c| ≤ 0.5/32.5 = 0.0154. With Ki = 60, **Kp = 0.01** gives |G_c| = 0.0123 and a peak of
  **−8.0 dB**. See `figures/kp_limit.png`.
- **Ki sets the 60 Hz loop.** Near ω1 the resonant term is an integrator acting on the 60 Hz
  envelope: T_env(s') ≈ Ki P0/s', where P0 = G_p H e^(−sτ) at 60 Hz = 0.995∠−9.7° (bench, 25 Ω).
  Envelope crossover = Ki |P0|/2π; phase margin = 90° + ∠P0 = 80°; time constant
  τ_env = 1/(Ki |P0|). **Ki = 60 1/s** gives 9.5 Hz and τ_env = **16.8 ms** (2 % settling in
  4τ = 67 ms, about 4 cycles). Faster (Ki = 120) would push the resonant peak to −5 dB at the
  worst corner, breaking the −6 dB rule, so we kept 60.

### 6.5 Predicted margins (`design.py`, `figures/bode_loop.png`)

|T| crosses 1 twice, once on each side of 60 Hz (the resonant term makes |T| infinite at 60 Hz):

| Sensing | Lower crossing | Upper crossing | Worst resonant peak, bank range (12.5 to 250 Ω) | Open circuit |
|---|---|---|---|---|
| Bench | 51.2 Hz, PM 99° | 70.2 Hz, **PM 79°** | −19.7 dB | −15.5 dB |
| HIL model | 51.2 Hz, PM 95° | 70.3 Hz, **PM 85°** | **−8.0 dB** | −3.8 dB |

The crossings do not move with load or inductance (G_p ≈ 1 at 60 Hz). Only the resonant peak
does, and it stays under −6 dB everywhere in the bank range. With the load fully disconnected on
the HIL the peak is −3.8 dB: still stable, but with less margin. The procedures never run without
a load.

Steady state: the resonant term removes the 60 Hz error in the **measured** signal. Because
|H(jω1)| = 0.995, the actual output is about 0.5 % above the reference on the bench (0.15 % on
the HIL).

## 7. Switched simulation compared with the prediction

`simulate.py` runs the station at the switching level (dead time 3.3 µs, device drops, ITECH
behind 0.05 Ω, 1.1 mF link, sensing filter, 12-bit ADC sampled at the valley, duty loaded one
period later). It compiles and calls `firmware/pb_ctrl_core.c`, the same code that is in the
PLECS C-Script. `ProjectB_Sim.plecs` is the PLECS version of the same test.

**Station-sheet transient for the review: reference step 25 → 30 V rms at 25 Ω.**

- With feedforward **off** (`FF = 0`, so the loop alone does the work), the per-cycle output
  amplitude follows the first-order prediction with τ_env = 16.8 ms; the switched, averaged and
  predicted curves lie on top of each other (`figures/sim_ref_step_ff0.png`). Within 2 % after
  4 cycles, as predicted (4τ = 67 ms).
- With feedforward **on** (normal setting), the new amplitude is applied at the next positive zero
  crossing, so the reference has no jump. Within 2 % after 2 cycles, 1 % overshoot, peak 43.0 V.

**Load step 25 → 12.5 Ω at 30 V rms (and back)**, `figures/sim_load_step.png`:

- The averaged model predicts almost nothing: the output impedance at 60 Hz is
  jω1 L + R_L ≈ 0.04 Ω, so 2.4 A changes v_o by under 0.1 V (0.3 %).
- The switched simulation shows a **2.9 % dip** for one to two cycles, recovered in about
  3 cycles. The difference is dead time: at 25 Ω the ripple makes i_L cross zero in most switching
  periods, which partly cancels the dead-time error; at 12.5 Ω the current keeps one sign around
  the peaks and the full error appears. The resonant term then removes it with τ_env ≈ 17 ms.
  This is a known limitation of the averaged model, not a control problem.

Operating points (switched simulation, bench sensing):

| | OP1 | OP2 |
|---|---|---|
| v_o fundamental | 25.18 V rms | 30.39 V rms |
| THD of v_o (to 50th) | 1.2 % | 4.9 % (dead-time notches at the current zero crossings) |
| i_L rms / peak | 2.11 A / 5.12 A | 2.99 A / 7.30 A |
| Ripple pk-pk | 7.5 A | 7.7 A |
| Peak modulation index | 0.66 | 0.86 |
| Resonant correction amplitude | 6.5 V | 9.6 V |
| P_in / P_out | 28.0 W / 25.4 W | 77.0 W / 74.1 W |
| I_dc | 0.51 A | 1.40 A |

The simulated i_L rms, peak and ripple agree with the hand calculations in §2 within 3 %.
The resonant correction of 6.5 V at OP1 agrees with the 6.6 V predicted for dead time and drops.
P_in − P_out includes conduction losses only; switching losses are not modelled.

On the HIL sensing model, the output settles about 1 % lower (24.70 V and 29.92 V rms). The HIL
filter passes part of the capacitor ripple (its direct feedthrough is 0.6), and sampling at the
valley turns that ripple into a small 60 Hz measurement error. Expect this on the HIL.

Robustness: L at ±20 % with R = 250 Ω on the HIL sensing model, the hardest case: stable, no trips.

## 8. Bring-up readiness

- **Connection diagram**: from the station-sheet figure, add VProbe1 across tap 1 (+) and tap 2 (−);
  VProbe2 across DC+ and DC−; CProbe1 on the leg-A inductor wire, arrow from leg A toward tap 1;
  CProbe2 on the load wire from tap 1, arrow toward the bank; gate BNCs Top 1/Bot 1 (ePWM1A/B,
  leg A) and Top 2/Bot 2 (ePWM2A/B, leg B); third leg not connected; nC floating; ITECH across DC+/DC−.
- **Gate mapping**: ePWM1A = Top 1 = Q1, ePWM1B = Bot 1 = Q3 (leg A); ePWM2A = Top 2 = Q2,
  ePWM2B = Bot 2 = Q4 (leg B). Positive m raises d_A and lowers d_B, so v_AB > 0 and v_o > 0
  (tap 1 positive).
- **How we verify the wiring**: two members trace every connection against the diagram, then a
  third member checks it again from the diagram alone (no other group shares our station). Probe polarity is checked at low voltage with an open-loop
  check (§3 of `03_Bench_Procedure_and_Log.md`) and by the firmware's polarity trip.
- **ADC scaling verified on hardware**: with the ITECH at a known voltage and PWM off, compare
  `vdc` in External Mode with the ITECH display; with zero current, check that i_L and i_o read
  under 0.1 A (offset check). Note any offset different from 1.62 V in the bench log.
- **Startup and shutdown**: see `03_Bench_Procedure_and_Log.md` §4. There is no precharge on
  Project B: the ITECH charges the link as we raise its voltage in steps.

## 9. Questions to expect, with answers to understand (not to read out)

**Why is Kp so small? Isn't that a useless controller?** Kp is limited by the resonant peak, not by
the 60 Hz loop. The 60 Hz gain comes from the resonant term (infinite at ω1) and from feedforward.
Kp = 0.01 is the largest value that keeps the peak 6 dB under 1 at the worst corner.

**What is your crossover frequency and phase margin?** Two crossings, 51 Hz and 70 Hz; phase
margin 79° at the upper one on the bench (85° on the HIL model). Equivalent envelope crossover
9.5 Hz with 80° margin.

**What happens if the load is disconnected while running?** The resonant peak rises to −15.5 dB
(bench) and −3.8 dB (HIL model): still stable. The output voltage barely changes (output impedance
0.04 Ω). We do not plan to open-circuit it.

**What happens at a zero crossing of the inductor current?** Dead time: during the 3.3 µs dead
time the diodes set the leg voltage according to the current sign, so the effective voltage error
flips sign with the current. That causes the notches and most of the THD; the resonant term
corrects only the 60 Hz part.

**Why sample at the carrier valley?** In unipolar SPWM both legs are in a zero state at the
valley, at the centre of a symmetric pattern, so the sample is close to the period average and
avoids the ripple.

**Where does the 1.5 T_s delay come from?** One period from sampling to loading the new duty, plus
half a period because the symmetric PWM's effect is centred half a period after loading.

**How does m = v*/v_dc help?** The bridge output is m v_dc. Dividing by the measured v_dc makes the
gain from v* to the bridge voltage equal to 1 whatever the DC-link voltage, so ITECH droop or
ripple does not change the loop gain.

**How do you know the ADC scaling is right?** Formula from the setup guide; checked on HIL against
the SCADA values; on the bench against the ITECH display with PWM off and against the scope.

**What does the firmware do on a trip?** Latches the fault bit, disables every gate through the TI
Powerstage Protection block, resets the controller states. Then we isolate the source (ITECH
output off), confirm v_dc < 5 V before touching anything, and only reset (enableswitch 0) after
finding the cause with the TA.

**What limits the output power?** §2: the DC voltage (58 V) through the modulation limit, with dead
time and drops, caps v_o at 34.5 V rms; with the minimum bank resistance of 12.5 Ω, about 95 W.
The current ratings are far from binding.

**Why not run the PR on the inductor current like Tutorial 5?** Tutorial 5 regulates a current;
here the output voltage is the regulated quantity. A current loop cannot damp this resonance
(§6.3).

**What would you change with more time?** Dead-time compensation (add the expected dead-time voltage
with the sign of the current reference) to cut the THD and the load-step dip; oversample the ADC
to remove the ripple aliasing; a capacitor-current active damping loop if the sampling could be
made fast enough (double update at 2 f_sw puts f_s/6 at 3.3 kHz, above the resonance).
