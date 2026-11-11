# ENEL 585 Project B: Single-Phase Standalone Inverter Controller

Group 8, Lab B01. **Station 5 and HIL computer SSE-6Y8G3H4 per the Oct 29 station list** (the
proposal says Station 6; confirm with the TA). Everything needed from now to the final report: the controller, the
PLECS models, the design analysis, the switched simulation, and the plans for the HIL sign-off,
the bench sessions, the report and the presentation.

## Key dates

| When | What | Where to look |
|---|---|---|
| Before Fri Nov 20 | Build the firmware, run it on the remote HIL, rehearse the review | `docs/02_HIL_Signoff.md`, `docs/01_Design_Review.md` |
| Fri Nov 20 (Bench 2) | Design review (8 %) and HIL sign-off, then first closed-loop tests | `docs/01_Design_Review.md`, `docs/03_Bench_Procedure_and_Log.md` |
| Fri Dec 4 (Bench 3) | All station-sheet measurements | `docs/03_Bench_Procedure_and_Log.md` |
| Tue Dec 8 | Final presentation and individual questions | `docs/05_Presentation_Plan.md` |
| Fri Dec 11 | Final report and ZIP | `docs/04_Report_Draft.md` |

## The design in one paragraph

Unipolar SPWM at 9.96 kHz (166 carrier periods per 60 Hz cycle, synchronous with the reference),
one sample per carrier period at the valley (1.5 Ts delay). The output voltage is regulated by
**reference feedforward plus a proportional-resonant controller**, Gc = Kp + 2 Ki s / (s² + ω1²),
with m = v*/v_dc so DC-link changes are cancelled. The LC filter resonates at 2.95 kHz, above
fs/6, and the sensing filter adds about 86° of lag there, so the resonance cannot be damped
actively from these measurements. Following the course's gain-stabilization method, Kp = 0.01 keeps
the resonant peak of |T| at least 8 dB under 1 over the whole bank range, and Ki = 60 1/s gives
loop crossings at 51 Hz and 70 Hz with 79° or more of phase margin (envelope bandwidth 9.5 Hz,
τ = 17 ms). Latched protection on v_o, i_L, i_o, v_dc (high and low) and probe polarity.

## Folder map

```
design/
  params.py           every number (hardware, operating points, timing, gains, trips)
  design.py           plant, sensing, loop gain, margins at all corners, hardware and ADC tables
  simulate.py         switched simulation of the station running the real controller C code
  results_*.json      numbers quoted in the docs; sim_log.txt is the last simulation printout
firmware/
  pb_ctrl_core.c      THE controller (single source). Pasted into both PLECS models.
  pb_ctrl_test.c      ctypes wrapper used by simulate.py
plecs/
  Controller.plecs    firmware model for PLECS Coder (LAUNCHXL-F28P55X, TI C2000 TSP)
  ProjectB_Sim.plecs  switched simulation for the design review (plant + sensing + controller)
  gen_plecs.py        generates both .plecs files from the course's own PLECS files
  controller_cscript_sections.txt   the C-Script code as plain text (for the report ZIP)
figures/              Bode plots, Kp limit, simulated operating points, transients, trip
docs/
  01_Design_Review.md         what to say at the review, every number, likely questions
  02_HIL_Signoff.md           build, flash, Watch variables, checklist with expected values
  03_Bench_Procedure_and_Log.md  wiring, startup, shutdown, fault response, measurements, log
  04_Report_Draft.md          report skeleton mapped to the rubric, predictions filled in
  05_Presentation_Plan.md     slide plan and individual-question preparation
  bench_log_template.csv
```

## What changed from the proposal (all justified in `docs/01_Design_Review.md` §2)

| Item | Proposal | Now | Why |
|---|---|---|---|
| DC-link voltage | 50 V | **55 V** | Dead time and device drops cost about 6.6 V of peak inverter voltage. At 50 V, OP2 needs m = 0.98, over the 0.96 limit |
| Switching frequency | 10 kHz | **9.960 kHz** | Exactly reachable by the ePWM counter, synchronous with 60 Hz (166 periods) and inside the 10 kHz limit |
| Inductor OC trip | ±9 A | **7 A** (sampled average) | Average plus half-ripple (3.7 A) must stay under the 1146B's 10 A range |
| Load OC trip | none | **6 A** | Second current channel used for protection |
| DC OV trip | 55 V | **58 V**, plus **35 V** undervoltage while running | Run at 55 V; 58 V is below ITECH OVP (60 V) and ADC saturation (79 V) |
| Current probe numbering | CP1 = i_o, CP2 = i_L | **CProbe1 = i_L1, CProbe2 = i_o** | Matches the posted HIL model, so the same firmware runs on HIL and bench |

Operating points are unchanged: **OP1 25 V rms at 25 Ω (25 W)** and **OP2 30 V rms at 12.5 Ω (72 W)**.

## How to regenerate everything

```bash
cd design && python3 design.py && python3 simulate.py && cd ../plecs && python3 gen_plecs.py
```

Needs Python 3 with numpy, scipy and matplotlib, plus gcc (the simulation compiles the controller).

## What has been verified, and what has not

| Item | Status |
|---|---|
| Control design, margins at 30 corners (bench and HIL sensing, L ±20 %, 12.5 Ω to open) | Verified (design.py) |
| Controller C code: operating points, both transients, all six trips, polarity check | Verified in the switched simulation, which compiles and runs the exact file |
| The C-Script code inside both .plecs files | Extracted back out of the files and compiled and run here |
| The .plecs files open in PLECS, simulate, and build with PLECS Coder | **Not verified: no PLECS licence in this environment.** Every block was copied from course files that work, but open both files first and read `docs/02_HIL_Signoff.md` §1 if anything fails to load |
| Firmware on the HIL and bench | Your job at the HIL sign-off; expected values are in `docs/02_HIL_Signoff.md` |

## AI disclosure (required in every submission)

Claude (Anthropic) designed the controller, wrote the C code, the Python analysis and simulation,
generated the PLECS models, and drafted these documents. The group must check, run and
understand all of it: the design review and the individual questions are answered without AI.
Suggested wording is in `docs/04_Report_Draft.md`.
