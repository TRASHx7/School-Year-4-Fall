# ENEL 585 Project B: PLECS models (Group 8, Station 6, B01)

Single-phase standalone inverter: ITECH dc supply, two SEMITEACH legs, LC filter
(2 x 47 uH, 2 x 62 uF, floating star), resistor bank, regulated 60 Hz output.

| File | What it is |
|---|---|
| `ENEL585_F26_ProjectB_G8_Firmware.plecs` | Controller for the LAUNCHXL-F28P55X (bench and remote HIL). Build this with PLECS Coder. |
| `ENEL585_F26_ProjectB_G8_Station.plecs` | Switched model of the station running the same controller code: full bridge with dead time, LC filter, switched bank, interface-board sensing, demonstration sequence. |
| `verification_demo_sequence.svg` | Waveforms of the demonstration sequence from the independent C check (below). |
| `tools/cscript/` | Controller, sensing and test-sequence C code embedded in the CScript blocks. |
| `tools/generate_plecs.py` | Regenerates both models from `tools/cscript/` and the course example files. |
| `tools/verify/` | C model of the station that runs the controller code, plus analysis and plot scripts. |

The controller sits in one C-Script block whose code is identical in both
files, so what you simulate is what you flash. The PLECS Setup guide suggests
a single file with a code-generation subsystem instead; two files were used
here so that every block could be copied from a course model PLECS had already
saved. If you prefer one file, copy the firmware blocks into a subsystem of the
station model and enable code generation on it.

## Using the models

**Simulation.** Open the station model and run it (1.1 s). The sequence is:
enable at 20 ms with a soft start to 25 Vrms on 25 ohm (OP1), load step to
12.5 ohm at 0.30 s, reference step to 30 Vrms at 0.50 s (OP2), back to 25 Vrms
at 0.70 s, load step back to 25 ohm at 0.85 s. Times and levels are in
`scen_par`. Set `protection_test = 1` in the init commands to lower the
inductor trip to 2.5 A; the bridge then trips at the load step and stays off.

**Bench.** Open the firmware model. In Coder options > Target select
TI28P55x, the LaunchPad board, "Build and program", "Run from Flash", and
check External Mode is Serial on GPIO 28/29. Then build.

1. Leave `enableswitch` at 0 (PWM inhibited) while the ITECH ramps to 50 V.
2. Set `enableswitch` to 1. Switching starts at a zero crossing and ramps to
   `Vref_rms` (default 25 Vrms) in about 60 ms.
3. Reference step: change `Vref_rms` between 25 and 30. Load step: switch the
   bank between 10 and 20 closed switches.
4. A trip removes the gates and latches. Set `enableswitch` to 0 to clear it.

The `status` display and scope show
`[Vpk_meas Vpk_cmd m fault Vrms ILrms Pout]`. Fault bits: 1 = output
overvoltage, 2 = inductor overcurrent, 4 = output overcurrent, 8 = dc overvoltage.

**Remote HIL.** First fill in the `target == 2` block of the init commands from
the provided Project B HIL model. In its `.tse`, the `analog_outputs` entry
lists `AOn;signal;scale;offset;...` for each channel. Then set `target = 2`,
choose "Build only" and follow the Remote HIL Quick Start. Tunable fields
(prefix `ENEL585_F26_ProjectB_G8_Firmware_P.`): `enableswitch_SwitchState`,
`Vref_rms_Value`, `Kp_amp_Value`, `Ki_amp_Value`. Check `<model>.h` for the
exact names.

## Design summary

### Plant

| Quantity | Value |
|---|---|
| Loop inductance L | 2 x 47 uH = 94 uH (+-20 %) |
| Filter capacitance C (load taps) | 62 uF in series with 62 uF = 31 uF |
| Resonance f0, impedance Z0 | 2.95 kHz, 1.74 ohm |
| Q = R/Z0 | 14.4 at 25 ohm, 7.2 at 12.5 ohm |
| Filter gain at 60 Hz | 1.0004, phase under 1 deg: vo is about m Vdc sin(wt) |

### Switching frequency and modulation

fsw = 9960 Hz: 166 carrier periods per 60 Hz cycle. This is even, as unipolar
modulation needs, and it is a period the ePWM counter hits exactly at
150 MHz, so the reference stays synchronous (f1 = 60.001 Hz). It is below the
10 kHz ceiling. With unipolar SPWM the ripple is at 19.9 kHz, 6.8 x f0, with
a worst-case 6.7 A peak to peak (at |vo| = Vdc/2). Halving fsw would double
that, which is why the frequency stays near the ceiling. The interface-board
filter is 27.5 dB down at fsw, so the ADC samples are effectively ripple-free.

### Why an amplitude loop and not an instantaneous loop

The interface-board conditioning is modelled as
H(s) = (1 + s/wz)/((1 + s/wp1)(1 + s/wp2)) with fz = 1.5 kHz and
fp = 700 and 900 Hz. This reproduces every figure in the Inverter Box Setup
Guide: 0.5 % low at 60 Hz, 5 % low and 21 deg lag at 200 Hz, 25 % low at
500 Hz, and 21 and 27 dB down at 5 and 10 kHz.

At f0 the sensed signal is 0.15 of the true value with 87 deg lag, so active
damping of the LC resonance through these probes is not possible. A loop
that tracks the 60 Hz waveform directly would need bandwidth well above
60 Hz, where the sensor lag is already large. The controller therefore uses:

* **Feedforward.** m = (V\*pk + x)/Vdc_f with Vdc measured (VProbe 2) and
  filtered (20 ms). Leg duties are dA = (1 + m sin wt)/2 and dB = 1 - dA.
* **Amplitude measurement.** Synchronous demodulation (sums of vo sin and
  vo cos) over the last full 60 Hz cycle, updated every half cycle. A full
  cycle rejects dc offset and all harmonics. The result is divided by the
  sensor's 60 Hz gain (0.9949).
* **Integral trim x.** This corrects the losses: dead time, device drops, the
  inductor drop and sensor gain error. The error is taken against the command
  applied over the same measurement window, so the trim does not wind up
  during ramps.
* m changes only at reference zero crossings, which keeps steps from
  exciting the LC resonance.

### Small-signal model and compensator

At the half-cycle update rate (T = 8.33 ms) the measured amplitude is
y[k] = g (u[k-1] + u[k-2])/2, where g is about 1 because the feedforward
normalises Vdc. The integrator is x[k] = x[k-1] + Ki e[k], so

L(z) = Ki g (z + 1) / (2 z (z - 1)), stable for Ki g < 2.

| Ki (g = 1) | Crossover | Phase margin | Gain margin | Closed-loop poles |
|---|---|---|---|---|
| **0.4 (default)** | 7.5 Hz | 67 deg | 14 dB | 0.40 +- 0.20j (2 % in about 40 ms) |
| 0.4, g = 0.8 to 1.2 | 6.1 to 9.0 Hz | 72 to 63 deg | 16 to 12 dB | |

`Kp_amp` (default 0) adds a proportional term if wanted. `Kp_amp` and
`Ki_amp` are tunable on the target.

### Limiters

* Amplitude slew of 5 V pk per half cycle. This is also the soft start
  (OP1 in about 60 ms).
* m at most 0.98, with conditional-integration anti-windup.
* Trim limited to +-10 V pk, and `Vref_rms` capped at 32 Vrms.
* Current-limit foldback: while the half-cycle peak of the sensed iL exceeds
  6 A, the amplitude is reduced by 2 V per A per half cycle. It recovers at
  0.5 V per half cycle once below.
* Switching starts only once the filtered Vdc exceeds 20 V.

## Sensing and protection

The Inverter Box Setup Guide gives V_pin = 1.667 V + 0.213 x V_BNC for voltage
channels and 1.667 V + 0.154 x V_BNC for current channels. With 10:1 voltage
probes this is 21.3 mV per volt. With 100 mV/A current probes it is 15.4 mV
per amp.

| Signal | Probe, setting | Input, ADC pin | Largest operating value, pin | Trip, pin |
|---|---|---|---|---|
| Output voltage vo (tap A - tap B) | VP1, 10:1 | VProbe 1, ADCINB2 | 42.4 V pk (OP2): 0.763 / 2.571 V | +-50 V: 0.602 / 2.732 V |
| Inductor current iL (leg A) | CP2, 100 mV/A | CProbe 2, ADCINB0 | 3.43 A pk sensed (OP2): 1.614 / 1.720 V | +-9 A: 1.528 / 1.806 V |
| Output current io | CP1, 100 mV/A | CProbe 1, ADCINB1 | 3.39 A pk (OP2): 1.615 / 1.719 V | +-6 A: 1.575 / 1.759 V |
| DC input voltage | VP2, 10:1 | VProbe 2, ADCINA6 | 50 V: 2.732 V | 55 V: 2.839 V |

Gates: EPWM1A/B drive Top 1/Bot 1 (leg A, Q1/Q2) and EPWM2A/B drive Top 2/Bot 2
(leg B, Q3/Q4), complementary with 2 us dead time. Leg 3 stays inhibited.

**Why measure the inductor current.** The station sheet asks for it in every
demonstration. It is also the current in the IGBTs and the inductor (load plus
capacitor current plus ripple), so it is the right signal for overcurrent
protection and the current limit. The output current misses the capacitor
current and any filter ringing.

**On a trip** the controller sets the Powerstage Protection enable to 0, so all
gates go low. The trip latches until `enableswitch` is set to 0. Trips act on
the sensed (filtered) signals every 100 us. A hard short faster than that is
covered by the gate drivers' own protection and the thermal interlock (Inverter
Box Setup Guide) and by the ITECH current limit.

## Verification

I could not open the models in PLECS. They were built in an environment without
it, so the controller was checked another way. `tools/verify/sim_station.c`
compiles the CScript sections verbatim and runs them once per carrier period
against a 10 ns time-step model of the station. That model includes Rs, Cdc,
dead time with diode conduction, the LC filter with bleeders, the bank step,
the sensing filter and a 12-bit ADC, with duties applied one period later as
the ePWM shadow load does. The embedded code in both `.plecs` files was checked
to be byte-identical to these sources.

**Steady state** (Vdc = 50 V, 2 us dead time):

| Point | Load | vo | io | P | iL rms | iL peak | m |
|---|---|---|---|---|---|---|---|
| OP1 | 25 ohm | 25.01 Vrms | 1.00 A | 25.0 W | 1.94 A | 4.78 A | 0.71 |
| Load step state | 12.5 ohm | 25.01 Vrms | 2.00 A | 50.0 W | 2.61 A | 5.89 A | 0.72 |
| OP2 | 12.5 ohm | 30.01 Vrms | 2.40 A | 72.1 W | 2.85 A | 6.06 A | 0.885 |

**Transients** (half-cycle peaks of vo; iL peak includes ripple):

| Event | Deviation | Overshoot | 2 % settling | iL peak |
|---|---|---|---|---|
| Load step 25 to 12.5 ohm | 0.7 % | 0.7 % | within one half cycle | 6.1 A |
| Reference step 25 to 30 Vrms | slew-limited ramp | 0 % | 16.7 ms | 6.1 A |
| Reference step 30 to 25 Vrms | slew-limited ramp | 0 % | 16.7 ms | 6.0 A |
| Load step 12.5 to 25 ohm | 3.7 % | 3.7 % | 8.3 ms | 5.4 A |

**Worst case** (L -20 %, 5 us dead time as in Lab 2, 2 V device drop): all
targets are still met, the deviation is at most 4.1 %, and the iL peak is at
most 6.8 A. That leaves 24 % margin to the 9 A trip and 65 % to the 19.3 A
inductor rating. **At Vdc = 45 V** OP2 reaches the modulation limit and
gives 29.85 Vrms. The anti-windup holds and the loop stays stable.
**Protection test:** an inductor trip of 2.5 A trips 6 ms after the load step
and the bridge stays off.

To reproduce:

```bash
cd tools/verify && gcc -std=c99 -D_DEFAULT_SOURCE -O2 -o sim sim_station.c -lm
```

```bash
./sim 0 case0.csv && python3 analyze.py case0.csv && python3 plot_case.py case0.csv demo.svg
```

Cases: 0 nominal, 1 worst case, 2 protection test, 3 Vdc = 45 V.

## Points that change the proposal

* **Inductor current targets.** The steady-state table gives 1.04 and
  2.43 A rms. Those are the 60 Hz components only. With about 1.5 to 1.6 A rms
  of switching ripple, the predicted totals are **1.94 A rms (OP1)** and
  **2.85 A rms (OP2)**, in line with the envelope table's ranges. The
  capacitor current targets (0.29 and 0.35 A rms) are also 60 Hz only, since
  the ripple flows mostly in Cf. Compare with the scope RMS; the Fluke 39 may
  not capture 20 kHz content fully.
* **fsw** is 9.96 kHz rather than 10 kHz, so the carrier stays synchronous.
* **Dead time** is 2 us (the orientation model uses 1 us and Lab 2 used 5 us).
  With 5 us, OP2 needs m = 0.975 in the worst case, which leaves no headroom
  below about 50 V. If the TA wants 5 us, keep Vdc at 50 V or more for OP2.
* **Output current channel** is now fully mapped (CProbe 1 to ADCINB1, table
  above), with a 6 A trip.

## Check before relying on the models

* **Load errors.** Every block except the filter capacitors was copied from a
  course model that PLECS 5.0 saved. The capacitor block (`Type Capacitor`,
  parameters `C` and `v_init`) is the one written from the standard format. If
  PLECS reports a problem, it is most likely there or in a probe signal name
  (`Resistor current`).
* **Wire routing.** Wires may draw diagonally; drag them to tidy up.
* **HIL I/O.** The HIL scaling and pin mapping must come from the provided
  HIL model (see "Remote HIL").
* **Enable output.** The Powerstage Protection drives `PWR_GPIO` = 21 as an
  enable output, as the orientation model does. Change it if your HIL model
  uses another pin.
* **No VProbe 2.** If VProbe 2 is not wired, set `src(4) = 0`. The feedforward
  then uses `Vdc_nom`, and the dc trip is skipped.
* **Placeholders.** Inductor winding resistance (20 mOhm) and switch on
  resistance (20 mOhm) are estimates. Device voltage drops are not in the
  PLECS model, so expect slightly more trim on the bench.

## Regenerating

After editing `tools/cscript/*.c` or the init commands in
`tools/generate_plecs.py`, run:

```bash
python3 tools/generate_plecs.py
```

This rewrites both models. Re-run the C check afterwards.

## AI disclosure (for the report)

Claude (Anthropic) generated these PLECS models, the controller and test code,
and the verification scripts, and proposed the control structure and limiter
settings. The group is responsible for checking them in PLECS, on the HIL and
on the bench.
