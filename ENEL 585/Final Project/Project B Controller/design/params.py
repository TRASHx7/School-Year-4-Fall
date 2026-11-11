"""
ENEL 585 Fall 2026, Project B (single-phase standalone inverter), Group 8 (Station 5 per the Oct 29 list).

One place for every number the design, the simulation and the PLECS files use.
Sources are given next to each value. If you change a value here, re-run
design.py, simulate.py and ../plecs/gen_plecs.py so everything stays consistent.
"""
import math

# ---------------------------------------------------------------- station hardware
# Project B station sheet (Rev 12) and HIL model init (ENEL585_F26_ProjectB_sch_20261029.tse)
L_BRANCH = 47e-6          # H, Wurth 7443783533470, +/-20 %
R_L_BRANCH = 11.8e-3      # ohm, inductor DCR (HIL model value)
C_BRANCH = 62e-6          # F, one LCL-board capacitor
L_TOL = 0.20              # inductance tolerance

# The load sits between the two capacitor taps, so the loop sees both branches in series:
L = 2 * L_BRANCH          # 94 uH total in the current path
R_L = 2 * R_L_BRANCH      # 23.6 mOhm
C = C_BRANCH / 2          # 31 uF: the two capacitors in series through the floating star nC

C_DC = 1.1e-3             # F, SEMITEACH DC link
I_RATED_L = 19.3          # A rms, inductor (50 K rise)
I_SAT_L = 32.3            # A, inductor typical saturation (-30 % L)
I_IGBT = 50.0             # A, SKM50GB12T4
V_ITECH_MAX = 58.0        # V, station sheet limit (OVP 60 V)
I_ITECH_LIM = 10.0        # A, ITECH current limit used in all procedures
R_BANK_MIN = 12.5         # ohm, 20 x 250 ohm branches all closed
R_BANK_MAX = 250.0        # ohm, one branch closed

# ---------------------------------------------------------------- operating points
# Proposal values for vo and R are kept. Vdc is raised from 50 V to 55 V (see docs/01):
# dead time and device drops need about 6.6 V of the inverter's peak voltage at OP2.
VDC = 55.0
OPERATING_POINTS = {
    "OP1": dict(Vrms=25.0, R=25.0),
    "OP2": dict(Vrms=30.0, R=12.5),
}
# Station-sheet transients (what we will do on HIL and the bench)
LOAD_STEP = dict(Vrms=30.0, R_from=25.0, R_to=12.5)     # 36 W -> 72 W, ends at OP2
REF_STEP = dict(R=25.0, V_from=25.0, V_to=30.0)         # starts at OP1

# ---------------------------------------------------------------- PWM and timing
F1 = 60.0
MF = 166                                  # carrier periods per 60 Hz period (even: unipolar SPWM; fsw <= 10 kHz)
FCLK = 50e6                               # ePWM time-base clock used by Lab 2's model
FSW = FCLK / (2 * round(FCLK / (2 * MF * F1)))   # 9960.16 Hz, exactly reachable by the up-down counter
F1_EXACT = FSW / MF                        # 60.0002 Hz: reference and resonator use this
TS = 1 / FSW                               # control period (one sample per carrier period)
TAU = 1.5 * TS                             # sample-to-PWM delay, Lecture 11 "The Sampling Delay"
DEADTIME = 2e-6                            # s, firmware dead time (Lab 2 used 5 us; see docs/01)
DEADTIME_EFFECTIVE = 3.3e-6                # s, SKHI 22A driver interlock is assumed to dominate
M_MAX = 0.96                               # modulation limit (keeps duty inside 2 % ... 98 %)

# ---------------------------------------------------------------- sensing
# Inverter Box Setup Guide v3: V_ADC = 1.62 V + K * H(s) * V_BNC
V_ADC_OFFSET = 1.62
K_VCH = 0.213             # voltage channels, V per V at the BNC
K_ICH = 0.154             # current channels, V per V at the BNC
V_PROBE_ATTEN = 10.0      # N2791A on 10:1
I_PROBE_V_PER_A = 0.1     # 1146B on 100 mV/A
ADC_FULL_SCALE = 3.3
ADC_BITS = 12
# Measured channel dynamics (HIL model init): two poles and a zero on the bench board.
F_P1, F_P2, F_Z = 723.4, 871.9, 1446.9    # Hz
# NOTE: the posted HIL model implements only (1 + s/wz)/(1 + s/wp2); the 723 Hz pole is
# defined but not used. Both versions are analysed; the HIL one is the harder case.

# Physical value from ADC pin voltage: x = K_ADC * V_pin + O_ADC  (PLECS TI ADC block Scale/Offset)
V_SCALE = V_PROBE_ATTEN / K_VCH                      # 46.95 V per V
V_OFFSET = -V_ADC_OFFSET * V_SCALE                   # -76.06 V
I_SCALE = 1.0 / (I_PROBE_V_PER_A * K_ICH)            # 64.94 A per V
I_OFFSET = -V_ADC_OFFSET * I_SCALE                   # -105.19 A

# LaunchPad pins (HIL model comments, Inverter Box Setup Guide v3 Table 2)
ADC_MAP = {
    "v_dc": ("VProbe2", "ADCINA6", "A", 6),
    "i_L1": ("CProbe1", "ADCINA10", "A", 10),
    "v_o":  ("VProbe1", "ADCINB2", "B", 2),
    "i_o":  ("CProbe2", "ADCINB0", "B", 0),
}

# ---------------------------------------------------------------- controller (chosen in design.py)
# Gc(s) = Kp + 2 Ki s / (s^2 + w1^2)   (Lecture 11, "Why a Proportional-Resonant Controller?")
KP = 0.01
KI = 60.0                 # 1/s: envelope crossover about 9.5 Hz either side of 60 Hz
FF_GAIN = 1.0             # reference feedforward on (set 0 to show the feedback loop alone)
X_MAX = 15.0              # V, anti-windup clamp on the resonant correction amplitude
RAMP_RATE = 100.0         # V/s of peak amplitude during soft start (42 V in 0.42 s)

# ---------------------------------------------------------------- protection (firmware, sampled values)
TRIP_VO = 50.0            # V peak, output overvoltage   (OP2 peak 42.4 V)
TRIP_IL = 7.0             # A, inductor overcurrent      (OP2 avg peak 3.4 A; +3.7 A ripple -> 10.7 A max)
TRIP_IO = 6.0             # A, load overcurrent          (OP2 peak 3.4 A)
TRIP_VDC_HI = 58.0        # V, DC link overvoltage       (setpoint 55 V, ITECH OVP 60 V, ADC sat 79 V)
TRIP_VDC_LO = 35.0        # V, DC link undervoltage while running (ITECH off or in current limit)
VDC_START_MIN = 40.0      # V, PWM will not start below this


def w1():
    return 2 * math.pi * F1_EXACT


if __name__ == "__main__":
    print(f"fsw = {FSW:.3f} Hz, f1 = {F1_EXACT:.5f} Hz, Ts = {TS*1e6:.2f} us, tau = {TAU*1e6:.1f} us")
    f0 = 1 / (2 * math.pi * math.sqrt(L * C))
    print(f"L = {L*1e6:.0f} uH, C = {C*1e6:.0f} uF, f0 = {f0:.0f} Hz, Z0 = {math.sqrt(L/C):.3f} ohm")
    print(f"ADC: V = {V_SCALE:.3f}*Vpin {V_OFFSET:+.3f};  I = {I_SCALE:.3f}*Vpin {I_OFFSET:+.3f}")
