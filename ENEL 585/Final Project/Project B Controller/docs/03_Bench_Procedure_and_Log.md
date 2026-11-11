# Bench Procedure, Measurement Plan and Log

**Station 5**, computer SSE-6Y8G3H4, per the Oct 29 station list (no B02 group shares it). The
proposal and its feedback say Station 6: confirm with the TA and use the right number in the report.
Bench 2: Fri Nov 20 (design review and HIL sign-off first). Bench 3: Fri Dec 4 (all measurements).
Closed-loop hardware operation is allowed only after the HIL sign-off.

## 1. Wiring (connection diagram)

Power circuit (station sheet): ITECH + and − to the SEMITEACH DC-link terminals; legs A and B
(the third leg inhibited and unconnected); leg A midpoint to inductor branch 1, leg B midpoint to
inductor branch 2; each inductor to its capacitor tap; **load bank between tap 1 and tap 2 only**;
capacitor star nC floating (no earth, no DC−, no neutral); third filter branch and unused inductor
ends open; station transformer disconnected.

Control and sensing (same pins as the HIL model, so the firmware needs no change):

| Signal | Instrument and setting | Connection points | Interface-board input | LaunchPad |
|---|---|---|---|---|
| v_o | N2791A, **10:1** | + on tap 1, − on tap 2 | VProbe 1 | ADCINB2 |
| v_dc | N2791A, **10:1** | + on DC+, − on DC− | VProbe 2 | ADCINA6 |
| i_L1 | 1146B, **100 mV/A** | leg-A inductor wire, arrow from leg A toward tap 1 | CProbe 1 | ADCINA10 |
| i_o | 1146B, **100 mV/A** | load wire leaving tap 1, arrow toward the bank | CProbe 2 | ADCINB0 |
| Gates leg A | BNC | Top 1 / Bot 1 | ePWM1A / ePWM1B | GPIO0 / GPIO1 |
| Gates leg B | BNC | Top 2 / Bot 2 | ePWM2A / ePWM2B | GPIO2 / GPIO3 |

Note that this **swaps the current-probe numbering in our proposal** (we had CP1 = i_o, CP2 = i_L).
Update the connection diagram.

Scope: use BNC splitters so each probe feeds both the interface board and the oscilloscope (as in
Lab 2). Suggested channels: CH1 v_o, CH2 i_L1, CH3 i_o, CH4 v_dc. Set the scope probe factors
to match (10:1 and 100 mV/A).

Auxiliary: E3631A +25 V output set to +15 V, about 1 A limit, to the interface board; thermal trip
leads to Thermal Trip 1; error BNCs connected; LaunchPad switch S4 up, JP1 open; LEDs D5, D9, D4,
D8 on before energizing.

Load bank (20 × 250 Ω): **25 Ω = 10 switches closed** (OP1, load-step start, reference step);
**12.5 Ω = 20 switches** (OP2). Ask the TA how to make the 25 → 12.5 Ω step in one action
(for example a second bank section or a group switch). Flipping 10 switches one by one is not a
step. If only single switches are possible, agree a reproducible alternative with the TA and record it.

## 2. Before energizing (TA sign-off, not graded)

Show the TA: wiring traced by two members against the diagram (no partner group shares Station 5);
probe settings and arrows; gate mapping; protection settings (§5 of the design review); this
startup procedure. Verify the DC link and filter capacitors read below 5 V before any rewiring.

## 3. First power-up and bring-up checks (Bench 2, after the HIL sign-off)

Firmware on the bench: same `Controller.plecs`, but Coder build type **Build, flash and run** from
your laptop over USB, then connect **External Mode** to change the tunables and watch the scope in
the model. Never press Pause in CCS while the LaunchPad drives the real converter.

1. **ADC check, no switching.** enableswitch 0. Raise the ITECH to 20 V, then 55 V (§4 steps 1 and
   2). In External Mode, v_dc should match the ITECH display within 0.5 V; i_L and i_o should read
   under 0.1 A. If the zero readings are offset, the board offset is not 1.62 V: record it. If the
   error matters, change `V_adc_offset` in the init commands and rebuild.
2. **Feedforward only, low voltage.** Set Kp = 0, Ki = 0, Vref_rms = 5. enableswitch 1. Check on the
   scope: v_o ≈ 4 to 5 V rms (dead time costs about 0.7 V rms here), clean 60 Hz, i_L ripple
   about 3 A pk-pk at this low level. In External Mode, v_o should be in phase with v_ref (if it is
   inverted, the polarity trip stops the converter: fix the probe and recheck).
3. **Close the loop.** Ki = 60, then Kp = 0.01. v_o should settle to 5 V rms within about 4 cycles.
4. **Raise power in steps**: Vref 10, 15, 20, 25 V rms at 25 Ω (OP1). Watch i_L peak, the ITECH
   current and the IGBT box temperature at each step.
5. OP2: Vref 30 V rms, then 12.5 Ω.

## 4. Startup, shutdown and fault response (numbered for the log)

**Startup**
1. ITECH output off. Set **source mode, 0 V, current limit 10 A, OVP 60 V**. Load connected (25 Ω).
   PWM inhibited: enableswitch 0. Station transformer disconnected.
2. +15 V auxiliary on; check LEDs D5, D9, D4, D8. Flash the firmware; connect External Mode;
   confirm enableswitch = 0, Vref_rms = 5 V, Trip_* = 0.
3. After TA approval: ITECH output on; raise in steps (10, 20, 30, 40, 50, 55 V) while watching the
   voltage and the charging current. Wait for the charging current to fall to near zero.
4. enableswitch 1. The firmware waits for the next zero crossing and ramps the amplitude at
   100 V/s. Then raise Vref_rms in steps to the operating point.

**Normal shutdown**
1. Reduce Vref_rms to 5 V rms (reduce demand).
2. enableswitch 0 (PWM inhibited).
3. Ramp the ITECH to 0 V, reading the display: confirm **below 5 V** before switching its output off.
   The filter capacitors discharge through their 100 kΩ bleeders.
4. Measure the DC link and the filter capacitors with a multimeter before touching any wiring.

**Fault response** (trip, alarm, smell, noise or unexpected waveform)
1. ITECH output off immediately (this removes power). If the firmware tripped, the gates are already
   off.
2. Record the fault bits, the Watch values and the last scope capture.
3. Confirm the DC link is **below 5 V** on the ITECH display and with a multimeter on the DC link
   and capacitor taps before handling.
4. Investigate with the TA before resetting. Do not reset a trip repeatedly. Recheck any changed
   wiring or setting before energizing again; reset with enableswitch 0, then restart from step 3.

## 5. Measurements for the station sheet (Bench 3)

For **each operating point** (steady state, after at least 1 s):

| Quantity | Instrument | OP1 prediction (bench sim) | OP2 prediction (bench sim) |
|---|---|---|---|
| v_o, rms and waveform | Scope CH1 (measure rms, use 5+ cycles) | 25.2 V rms | 30.4 V rms |
| v_o THD | Scope FFT or Fluke 39 | 1.2 % | 4.9 % |
| i_L, rms, peak and ripple | Scope CH2 | 2.1 A rms, 5.1 A pk, 7.5 A pk-pk | 3.0 A rms, 7.3 A pk, 7.7 A pk-pk |
| i_o | Scope CH3 | 1.0 A rms | 2.4 A rms |
| ITECH V and I | ITECH display | 55.0 V, 0.51 A | 54.9 V, 1.40 A |
| Input power | V × I from the display | 28.0 W (conduction losses only) | 77.0 W |
| Output power | v_o²/R or Fluke 39 | 25.4 W | 74.1 W |
| Firmware view | External Mode: m, x_amp, fault | m pk 0.66, x_amp 6.5 V | m pk 0.86, x_amp 9.6 V |

**Load step** (station sheet 2): 30 V rms, 25 Ω → 12.5 Ω, then back. Capture v_o and i_L through
each transition. Scope: 10 ms/div, Single, trigger on CH3 (i_o) rising above 2.0 A for the step up,
falling for the step down. Prediction: v_o fundamental dips about 3 % for 1 to 2 cycles and is back
within about 3 cycles (`figures/sim_load_step.png`).

**Reference step** (station sheet 3): 25 Ω, Vref 25 → 30 V rms, then back. Capture the same
signals. Trigger on CH1 rising above 38 V. Prediction: new amplitude from the next zero crossing,
within 2 % in 2 cycles, about 1 % overshoot (`figures/sim_ref_step_ff1.png`). Optional extra:
repeat with FF = 0 and compare with the τ = 17 ms envelope prediction (`sim_ref_step_ff0.png`).

For every capture: save the scope image and the CSV data (USB stick), note probe settings, time,
firmware build, Vref, R, V_dc.

Compare each measured value with the prediction in the report's comparison table and give the
reason for any difference larger than 5 %.

## 6. Bench log

Use `bench_log_template.csv` (one row per capture or setting change). The report ZIP must include
the log. Minimum columns: date, time, session, firmware build (time or commit), model file,
Vref_rms, Kp, Ki, FF, ITECH V and I, load setting, probe settings, scope file, observation.
