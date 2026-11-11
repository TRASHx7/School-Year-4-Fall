"""
Generate the two PLECS models for Project B from the course's own PLECS files.

  Controller.plecs     firmware for the LAUNCHXL-F28P55X (PLECS Coder, TI C2000 TSP).
                       Named "Controller" so the build produces Controller.out / Controller.h and
                       the CCS Watch prefix is Controller_P / Controller_B (Remote HIL Quick Start).
  ProjectB_Sim.plecs   switched simulation of the station (plant + sensing + the same controller
                       code + a test sequencer) for the design review and the report.

Block syntax is copied from files that are known to work:
  - header, Coder target settings, both PWM blocks, C-Script, enableswitch:
        spwm_unipolar_ti_launchpad.plecs (Lab 2, run on the bench with both legs)
  - ADC blocks, Control Task Trigger, Powerstage Protection, CPU load, scope:
        tut5_PLECS_20261103.plecs (Tutorial 5, run on the remote HIL)
  - power circuit, Symmetrical PWM, Turn-on Delay, probe:  SPWM_bipolar.plecs (Lab 2 simulation)
The controller C code is read from ../firmware/pb_ctrl_core.c, so it is identical in both models.

Run:  python3 gen_plecs.py
"""
import base64
import math
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "design"))
import params as P  # noqa: E402

COURSE = os.path.join(HERE, "..", "..", "..",
                      "ENEL 585 L01 - (Fall 2026) - Introduction to Power Electronics - 10152026 - 853 PM")
SRC_LAB2 = os.path.join(COURSE, "spwm_unipolar_ti_launchpad.plecs")
SRC_TUT5 = os.path.join(COURSE, "ENEL585_Fall2026_Tutorial5Files_20261103", "tut5_PLECS_20261103.plecs")
SRC_SIM = os.path.join(COURSE, "SPWM_bipolar.plecs")
CORE = os.path.join(HERE, "..", "firmware", "pb_ctrl_core.c")


# ------------------------------------------------------------------ helpers for the file format
def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def header_of(text):
    """Everything before the first top-level Terminal/Schematic line."""
    m = re.search(r"\n  (Terminal \{|Schematic \{)", text)
    return text[:m.start() + 1]


def component(text, name):
    """Return the text of the top-level component with this Name (4-space indented)."""
    for blk in re.findall(r"\n(    Component \{\n.*?\n    \})(?=\n)", text, flags=re.S):
        m = re.search(r'\n      Name +"(.*?)"\n', blk, flags=re.S)
        if m and m.group(1) == name:
            return blk
    raise KeyError(name)


def set_param(comp, var, value):
    pat = re.compile(r'(Variable +"%s"\n +Value +)"(?:[^"\\]|\\.)*"((?:\n *"(?:[^"\\]|\\.)*")*)' % re.escape(var))
    new, n = pat.subn(lambda m: m.group(1) + qstr(value, indent=len(m.group(1)) - len(m.group(1).lstrip())), comp)
    if n != 1:
        raise KeyError(f"{var} not found exactly once")
    return new


def set_field(comp, field, value):
    pat = re.compile(r'(\n      %s +)(.*)' % re.escape(field))
    new, n = pat.subn(lambda m: m.group(1) + value, comp, count=1)
    if n != 1:
        raise KeyError(field)
    return new


def rename(comp, name):
    return re.sub(r'(\n      Name +)"(?:[^"\\]|\\.)*"', lambda m: m.group(1) + qstr(name), comp, count=1)


def place(comp, x, y):
    return re.sub(r'(\n      Position +)\[.*?\]', lambda m: m.group(1) + f"[{x}, {y}]", comp, count=1)


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def qstr(s, indent=0, width=74):
    """PLECS quoted string; long strings continue as further quoted lines."""
    e = esc(s)
    if len(e) <= width:
        return f'"{e}"'
    parts = []
    i = 0
    while i < len(e):
        j = min(i + width, len(e))
        # never split an escape sequence
        while j < len(e) and e[j - 1] == "\\" and (j - i) > 1:
            k = j - 1
            nb = 0
            while k >= i and e[k] == "\\":
                nb += 1
                k -= 1
            if nb % 2 == 1:
                j -= 1
            else:
                break
        parts.append(e[i:j])
        i = j
    return ("\n").join(f'"{p}"' for p in parts)


def qstringlist_b64(items):
    """Encode a QStringList the way PLECS stores CodeGenInliningExceptions."""
    b = struct.pack(">I", 11) + b"\x00" + struct.pack(">I", len(items))
    for s in items:
        u = s.encode("utf-16-be")
        b += struct.pack(">I", len(u)) + u
    return base64.b64encode(b).decode()


def blob_field(name, b64):
    lines = [b64[i:i + 54] for i in range(0, len(b64), 54)]
    return f'  {name} "' + '"\n"'.join(lines) + '"\n'


def hdr_set(header, field, value_q):
    """Replace a header field (possibly spanning several quoted lines)."""
    pat = re.compile(r'(\n  %s +)"(?:[^"\\]|\\.)*"((?:\n"(?:[^"\\]|\\.)*")*)' % re.escape(field))
    new, n = pat.subn(lambda m: m.group(1) + value_q, header)
    if n != 1:
        raise KeyError(field)
    return new


def P_(var, value, show="off"):
    return (f"      Parameter {{\n        Variable      \"{var}\"\n        Value         {qstr(str(value))}\n"
            f"        Show          {show}\n      }}\n")


def simple(typ, name, x, y, params=(), direction="right", show="on", flipped="off", label="south", extra=""):
    s = (f"    Component {{\n      Type          {typ}\n      Name          {qstr(name)}\n"
         f"      Show          {show}\n      Position      [{x}, {y}]\n      Direction     {direction}\n"
         f"      Flipped       {flipped}\n      LabelPosition {label}\n{extra}")
    for v, val in params:
        s += P_(v, val)
    return s + "    }"


def sig(src, st, dst, dt):
    return (f"    Connection {{\n      Type          Signal\n      SrcComponent  {qstr(src)}\n"
            f"      SrcTerminal   {st}\n      DstComponent  {qstr(dst)}\n      DstTerminal   {dt}\n    }}")


def merge_signals(conns, positions):
    """Join signal connections that leave the same output into one connection with branches."""
    groups, order, other = {}, [], []
    for c in conns:
        m = re.match(r'    Connection \{\n      Type          Signal\n      SrcComponent  (".*?")\n'
                     r'      SrcTerminal   (\d+)\n      DstComponent  (".*?")\n      DstTerminal   (\d+)\n    \}$', c)
        if not m:
            other.append(c)
            continue
        key = (m.group(1), m.group(2))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append((m.group(3), m.group(4)))
    out = []
    for key in order:
        dsts = groups[key]
        if len(dsts) == 1:
            out.append(f"    Connection {{\n      Type          Signal\n      SrcComponent  {key[0]}\n"
                       f"      SrcTerminal   {key[1]}\n      DstComponent  {dsts[0][0]}\n"
                       f"      DstTerminal   {dsts[0][1]}\n    }}")
        else:
            x, y = positions.get(key[0][1:-1], (0, 0))
            s = (f"    Connection {{\n      Type          Signal\n      SrcComponent  {key[0]}\n"
                 f"      SrcTerminal   {key[1]}\n      Points        [{x + 30}, {y}]\n")
            for d, tt in dsts:
                s += f"      Branch {{\n        DstComponent  {d}\n        DstTerminal   {tt}\n      }}\n"
            out.append(s + "    }")
    return out + other


def positions_of(comps):
    pos = {}
    for c in comps:
        n = re.search(r'\n      Name +"((?:[^"\\]|\\.)*)"', c)
        p = re.search(r'\n      Position +\[(-?\d+), (-?\d+)\]', c)
        if n and p:
            pos[n.group(1)] = (int(p.group(1)), int(p.group(2)))
    return pos


def event(src, st, dsts):
    s = (f"    Connection {{\n      Type          Event\n      SrcComponent  {qstr(src)}\n      SrcTerminal   {st}\n"
         f"      Points        [20, 20]\n")
    for d, t in dsts:
        s += f"      Branch {{\n        DstComponent  {qstr(d)}\n        DstTerminal   {t}\n      }}\n"
    return s + "    }"


def wire(net, point):
    """net: list of (component, terminal); first is the source, the rest branch from one point."""
    (c0, t0), rest = net[0], net[1:]
    s = (f"    Connection {{\n      Type          Wire\n      SrcComponent  {qstr(c0)}\n      SrcTerminal   {t0}\n"
         f"      Points        [{point[0]}, {point[1]}]\n")
    for c, t in rest:
        s += f"      Branch {{\n        DstComponent  {qstr(c)}\n        DstTerminal   {t}\n      }}\n"
    return s + "    }"


# ------------------------------------------------------------------ C-Script sections
CORE_C = read(CORE)

PARAM_NAMES = ["Nper", "Tctrl", "Vscale", "Voffset", "Iscale", "Ioffset", "TRIP_VO", "TRIP_IL", "TRIP_IO",
               "TRIP_VDC_HI", "TRIP_VDC_LO", "VDC_START_MIN", "M_MAX", "X_MAX", "RAMP_RATE"]

GLUE_DECL = """
/* ---- C-Script glue (generated by gen_plecs.py) ---- */
static pb_param_t pbP;
static pb_state_t pbS, pbNext;
static pb_in_t pbIn;
static pb_out_t pbOut;
#define PRM(i) ((float)ParamRealData(i, 0))
"""

START_FCN = """pbP.N = (int)(ParamRealData(0, 0) + 0.5);
pbP.Ts = PRM(1);
pbP.v_scale = PRM(2);
pbP.v_offset = PRM(3);
pbP.i_scale = PRM(4);
pbP.i_offset = PRM(5);
pbP.trip_vo = PRM(6);
pbP.trip_il = PRM(7);
pbP.trip_io = PRM(8);
pbP.trip_vdc_hi = PRM(9);
pbP.trip_vdc_lo = PRM(10);
pbP.vdc_start_min = PRM(11);
pbP.m_max = PRM(12);
pbP.x_max = PRM(13);
pbP.ramp_rate = PRM(14);
pb_init(&pbS, &pbP);
pbNext = pbS;"""

READ_INPUTS = """pbIn.vpin_vdc = (float)Input(0);
pbIn.vpin_il = (float)Input(1);
pbIn.vpin_vo = (float)Input(2);
pbIn.vpin_io = (float)Input(3);
pbIn.enable = (float)Input(4);
pbIn.vref_rms = (float)Input(5);
pbIn.kp = (float)Input(6);
pbIn.ki = (float)Input(7);
pbIn.ff = (float)Input(8);
pbIn.trip_vo_set = (float)Input(9);
pbIn.trip_il_set = (float)Input(10);
pbIn.trip_io_set = (float)Input(11);
pb_step(&pbIn, &pbS, &pbP, &pbOut, &pbNext);
"""

WRITE_OUTPUTS = """Output(0) = pbOut.dA;
Output(1) = pbOut.dB;
Output(2) = pbOut.pwm_en;
Output(3) = pbOut.fault;
Output(4) = pbOut.amp;
Output(5) = pbOut.m;
Output(6) = pbOut.x_amp;
Output(7) = pbOut.vref;
Output(8) = pbOut.vdc;
Output(9) = pbOut.il;
Output(10) = pbOut.vo;
Output(11) = pbOut.io;"""

# Firmware: on the TI target the duty written now is loaded at the next valley by the ePWM shadow
# register, which gives the 1.5 Ts delay by itself.
FW_OUTPUT = READ_INPUTS + WRITE_OUTPUTS
FW_UPDATE = "pbS = pbNext;"

# Simulation: the ideal modulator applies a new duty at once, so hold the duties for one period
# to reproduce the target's timing (computed from sample k, applied from valley k+1).
SIM_DECL_EXTRA = "static float simDA = 0.5f, simDB = 0.5f, simEN = 0.0f;\n"
SIM_OUTPUT = READ_INPUTS + """Output(0) = simDA;
Output(1) = simDB;
Output(2) = simEN;
Output(3) = pbOut.fault;
Output(4) = pbOut.amp;
Output(5) = pbOut.m;
Output(6) = pbOut.x_amp;
Output(7) = pbOut.vref;
Output(8) = pbOut.vdc;
Output(9) = pbOut.il;
Output(10) = pbOut.vo;
Output(11) = pbOut.io;"""
SIM_UPDATE = """pbS = pbNext;
simDA = pbOut.dA;
simDB = pbOut.dB;
simEN = pbOut.pwm_en;"""


def cscript(template, name, x, y, decl, start, output, update, n_in, n_out, ts, params):
    c = rename(template, name)
    c = place(c, x, y)
    c = set_field(c, "Direction", "right")
    for var, val in [("NumInputs", str(n_in)), ("NumOutputs", str(n_out)), ("NumContStates", "0"),
                     ("NumDiscStates", "0"), ("NumZCSignals", "0"), ("DirectFeedthrough", "1"),
                     ("Ts", ts), ("Parameters", params), ("Declarations", decl), ("StartFcn", start),
                     ("OutputFcn", output), ("UpdateFcn", update)]:
        c = set_param(c, var, val)
    c = re.sub(r'(Variable +"DialogGeometry"\n +Value +)"[^"]*"', r'\1""', c)
    return c


# ------------------------------------------------------------------ shared init commands
def fmt(x):
    return repr(float(x)) if not float(x).is_integer() else f"{x:.1f}"


TRIP_INIT = f"""% Protection (fixed in the firmware; Trip_vo/Trip_iL/Trip_io can only lower them)
TRIP_VO = {P.TRIP_VO};        % V peak, output overvoltage
TRIP_IL = {P.TRIP_IL};         % A, inductor overcurrent (sampled average)
TRIP_IO = {P.TRIP_IO};         % A, load overcurrent
TRIP_VDC_HI = {P.TRIP_VDC_HI};    % V, DC-link overvoltage
TRIP_VDC_LO = {P.TRIP_VDC_LO};    % V, DC-link undervoltage while running
VDC_START_MIN = {P.VDC_START_MIN};  % V, PWM does not start below this
M_MAX = {P.M_MAX};          % modulation limit
X_MAX = {P.X_MAX};          % V, anti-windup limit on the resonant correction
RAMP_RATE = {P.RAMP_RATE};     % V/s of peak amplitude during soft start
"""

TIMING_INIT = f"""% PWM timing: carrier synchronous with 60 Hz, as in Lab 2
f1 = 60;
Nper = {P.MF};          % carrier periods per 60 Hz period (even, unipolar)
fclk = 50e6;          % ePWM time-base clock of the TI28P55x target
fsw = fclk/(2*round(fclk/(2*Nper*f1)));   % {P.FSW:.2f} Hz
fcar = fsw;
Tctrl = 1/fsw;        % control period (one sample per carrier period)
deadtime = {P.DEADTIME};    % s (Lab 2 used 5e-6; the SKHI 22A driver adds its own interlock)
% Controller defaults (tunable blocks Kp, Ki, FF, Vref_rms)
Kp0 = {P.KP};
Ki0 = {P.KI};
"""

FW_INIT = f"""%% ENEL 585 Project B, Group 8: firmware model (generated by gen_plecs.py)
{TIMING_INIT}
% ADC scaling, Inverter Box Setup Guide v3: V_pin = 1.62 + K * V_BNC
V_adc_offset = {P.V_ADC_OFFSET};
Vprobe_atten = {P.V_PROBE_ATTEN};      % N2791A setting (10:1)
Iprobe_VperA = {P.I_PROBE_V_PER_A};     % 1146B setting (100 mV/A)
Vscale = Vprobe_atten/{P.K_VCH};          % V per V at the pin
Voffset = -V_adc_offset*Vscale;
Iscale = 1/(Iprobe_VperA*{P.K_ICH});      % A per V at the pin
Ioffset = -V_adc_offset*Iscale;

% Pins (HIL model and Setup Guide v3, Table 2)
ADC_A_CH = [6 10];    % ADCINA6 = VProbe2 = v_dc,  ADCINA10 = CProbe1 = i_L1
ADC_B_CH = [2 0];     % ADCINB2 = VProbe1 = v_o,   ADCINB0  = CProbe2 = i_o
PWR_DSP_GPIO = 21;    % power-stage enable GPIO, as in the Tutorial 5 model

{TRIP_INIT}"""

SIM_INIT = f"""%% ENEL 585 Project B, Group 8: switched simulation (generated by gen_plecs.py)
{TIMING_INIT}
% Station
Vdc = {P.VDC};          % ITECH set point
R_itech = 0.05;
Cdc = {P.C_DC};
Lf = {P.L_BRANCH};       % each branch; scale for the +/-20 % tolerance cases
R_Lf = {P.R_L_BRANCH};
Cf = {P.C_BRANCH};
R_bleed = 100e3;
Ron = 0.03;           % switch on-resistance (stand-in for the IGBT/diode drop)
R_load_A = 25;        % always connected
R_load_B = 25;        % switched in by the sequencer: 25 ohm -> 12.5 ohm

% Sensing filter H(s): bench = two poles + zero; HIL model = one pole + zero
sensing_bench = 1;
wz = 2*pi*{P.F_Z}; wp1 = 2*pi*{P.F_P1}; wp2 = 2*pi*{P.F_P2};
if sensing_bench
  Hnum = [1/wz 1];
  Hden = [1/(wp1*wp2) 1/wp1+1/wp2 1];
else
  Hnum = [1/wz 1];
  Hden = [1/wp2 1];
end

% The simulation feeds physical values to the controller, so its ADC scaling is unity
Vscale = 1; Voffset = 0; Iscale = 1; Ioffset = 0;

% Test sequence (s): enable, reference step, load step
t_enable = 0.001;
V1 = {P.REF_STEP['V_from']};   V2 = {P.REF_STEP['V_to']};   % V rms
t_ref_up = 0.60;   t_ref_down = 0.80;
t_load_on = 1.00;  t_load_off = 1.20;   % load step at V2: 25 ohm -> 12.5 ohm -> 25 ohm

{TRIP_INIT}"""

SEQ_DECL = """/* Test sequence for the simulation: enable, Vref steps, load B gate */
#define T_EN  ParamRealData(0, 0)
#define V_1   ParamRealData(1, 0)
#define V_2   ParamRealData(2, 0)
#define T_UP  ParamRealData(3, 0)
#define T_DN  ParamRealData(4, 0)
#define T_LON ParamRealData(5, 0)
#define T_LOF ParamRealData(6, 0)
"""
SEQ_OUTPUT = """double t = CurrentTime;
Output(0) = (t >= T_EN) ? 1.0 : 0.0;
Output(1) = (t >= T_UP && t < T_DN) ? V_2 : ((t >= T_LON) ? V_2 : V_1);
Output(2) = (t >= T_LON && t < T_LOF) ? 1.0 : 0.0;"""


# ------------------------------------------------------------------ firmware model
def build_firmware():
    lab2 = read(SRC_LAB2)
    tut5 = read(SRC_TUT5)
    hdr = header_of(lab2)
    hdr = hdr_set(hdr, "Name", '"Controller"')
    hdr = hdr_set(hdr, "InitializationCommands", qstr(FW_INIT))
    tunables = ["enableswitch", "Vref_rms", "Kp", "Ki", "FF", "Trip_vo", "Trip_iL", "Trip_io"]
    b64 = qstringlist_b64(tunables)
    hdr = re.sub(r'  CodeGenInliningExceptions "(?:[^"]*)"(?:\n"[^"]*")*\n', blob_field("CodeGenInliningExceptions", b64), hdr)

    comps = []
    conns = []
    # ---- ADCs (Tutorial 5 blocks), pin voltages out (scaling done in the controller)
    adcA = component(tut5, "ADC1")
    adcA = rename(place(adcA, 80, 120), "ADC_A")
    adcA = set_param(adcA, "Input", "ADC_A_CH")
    adcA = set_param(adcA, "Scale", "1")
    adcA = set_param(adcA, "Offset", "0")
    adcB = component(tut5, "ADC2")
    adcB = rename(place(adcB, 80, 220), "ADC_B")
    adcB = set_param(adcB, "Input", "ADC_B_CH")
    adcB = set_param(adcB, "Scale", "1")
    adcB = set_param(adcB, "Offset", "0")
    comps += [adcA, adcB]
    comps.append(place(component(tut5, "Control Task Trigger"), 150, 300))
    comps.append(simple("SignalDemux", "DemuxA", 150, 120, [("Width", "2")], show="off"))
    comps.append(simple("SignalDemux", "DemuxB", 150, 220, [("Width", "2")], show="off"))
    conns += [sig("ADC_A", 1, "DemuxA", 1), sig("ADC_B", 1, "DemuxB", 1)]

    # ---- operator inputs (tunable)
    lab2_en = component(lab2, "enable")
    lab2_dis = component(lab2, "disable")
    lab2_sw = component(lab2, "enableswitch")
    comps += [place(lab2_en, 190, 330), place(lab2_dis, 190, 360), place(lab2_sw, 240, 345)]
    conns += [sig("enable", 1, "enableswitch", 2), sig("disable", 1, "enableswitch", 3)]
    consts = [("Vref_rms", P.OPERATING_POINTS["OP1"]["Vrms"]), ("Kp", "Kp0"), ("Ki", "Ki0"),
              ("FF", P.FF_GAIN), ("Trip_vo", 0), ("Trip_iL", 0), ("Trip_io", 0)]
    y = 390
    for nm, val in consts:
        comps.append(simple("Constant", nm, 230, y, [("Value", val), ("DataType", "10")],
                            extra="      Frame         [-15, -10; 15, 10]\n"))
        y += 30

    # ---- mux -> controller -> demux
    n_in, n_out = 12, 12
    comps.append(simple("SignalMux", "Mux", 330, 300, [("Width", str(n_in))], show="off"))
    mux_inputs = [("DemuxA", 2), ("DemuxA", 3), ("DemuxB", 2), ("DemuxB", 3), ("enableswitch", 1)] + \
                 [(nm, 1) for nm, _ in consts]
    for i, (src, st) in enumerate(mux_inputs):
        conns.append(sig(src, st, "Mux", i + 2))
    cs_t = component(lab2, "Unipolar SPWM\\nduty")
    decl = CORE_C + GLUE_DECL
    cs = cscript(cs_t, "PB_controller", 430, 300, decl, START_FCN, FW_OUTPUT, FW_UPDATE, n_in, n_out,
                 "Tctrl", ", ".join(PARAM_NAMES))
    comps.append(cs)
    conns.append(sig("Mux", 1, "PB_controller", 1))
    comps.append(simple("SignalDemux", "Demux", 520, 300, [("Width", str(n_out))], show="off"))
    conns.append(sig("PB_controller", 2, "Demux", 1))

    # ---- PWM leg A (ePWM1: ADC trigger, as in Tutorial 5) and leg B (ePWM2, as Lab 2's PWM1)
    pwmA = component(tut5, "PWM")
    pwmA = place(pwmA, 680, 180)
    pwmA = set_param(pwmA, "PwmUnit", "[1]")
    pwmA = set_param(pwmA, "CarrierFreq", "fsw")
    pwmA = set_param(pwmA, "FixedDeadTime", "deadtime")
    pwmA = set_param(pwmA, "Phase", "0")
    pwmB = component(lab2, "PWM1")
    pwmB = place(pwmB, 680, 320)
    pwmB = set_param(pwmB, "CarrierFreq", "fsw")
    pwmB = set_param(pwmB, "FixedDeadTime", "deadtime")
    comps += [pwmA, pwmB]
    conns += [sig("Demux", 2, "PWM", 1), sig("Demux", 3, "PWM1", 1)]
    # ADC trigger from leg A, task from ADC_B end of conversion (Tutorial 5 wiring)
    conns.append(event("PWM", 3, [("ADC_A", 3), ("ADC_B", 3)]))
    conns.append(event("ADC_B", 2, [("Control Task Trigger", 1)]))

    # ---- power-stage enable from the controller (trips disable all gates)
    prot = component(tut5, "Protection")
    prot = place(prot, 680, 440)
    comps.append(prot)
    conns.append(sig("Demux", 4, "Protection", 1))

    # ---- diagnostics: scope (External Mode on the bench) and CPU load
    scope_t = component(tut5, "Scope")
    sc1 = rename(place(scope_t, 640, 560), "Scope meas")
    sc1 = sc1.replace('Name          "Input DC Voltage"', 'Name          "v_o and v_ref (V)"')
    sc1 = sc1.replace('Name          "Inductor Current"', 'Name          "i_L (A)"')
    sc1 = sc1.replace('Name          "Output AC voltage"', 'Name          "fault bits, m"')
    comps.append(sc1)
    comps.append(simple("SignalMux", "MuxS1", 600, 540, [("Width", "2")], show="off"))
    comps.append(simple("SignalMux", "MuxS3", 600, 580, [("Width", "2")], show="off"))
    conns += [sig("Demux", 12, "MuxS1", 2), sig("Demux", 9, "MuxS1", 3), sig("MuxS1", 1, "Scope meas", 1),
              sig("Demux", 11, "Scope meas", 2),
              sig("Demux", 5, "MuxS3", 2), sig("Demux", 7, "MuxS3", 3), sig("MuxS3", 1, "Scope meas", 3)]
    load = place(component(tut5, "Load"), 800, 560)
    disp = place(component(tut5, "%"), 860, 560)
    comps += [load, disp]
    conns.append(sig("Load", 1, "%", 1))
    # display the remaining controller outputs so they are not left open
    for i, (nm, port) in enumerate([("amp (V pk)", 6), ("x_amp (V)", 8), ("v_dc (V)", 10), ("i_o (A)", 13)]):
        comps.append(simple("Display", nm, 600, 640 + 30 * i, [("Notation", "1"), ("Precision", "2")],
                            extra="      Frame         [-31, -11; 31, 11]\n"))
        conns.append(sig("Demux", port, nm, 1))

    # top-level target ports: Input 1/2 = ADCs, Output 1 = PWM, 2 = Protection, 3 = PWM1
    terms = ""
    for typ, idx in [("Output", 1), ("Input", 1), ("Input", 2), ("Output", 2), ("Output", 3)]:
        terms += f"  Terminal {{\n    Type          {typ}\n    Index         \"{idx}\"\n  }}\n"
    body = ("  Schematic {\n    Location      [0, 50; 1400, 900]\n    ZoomFactor    1\n"
            "    SliderPosition [0, 0]\n    ShowBrowser   off\n    BrowserWidth  100\n")
    conns = merge_signals(conns, positions_of(comps))
    body += "\n".join(comps) + "\n" + "\n".join(conns) + "\n"
    body += annotation("Project B controller (Group 8): ADC -> controller C-Script -> ePWM1/ePWM2. "
                       "Generated by gen_plecs.py from pb_ctrl_core.c. Do not edit the C-Script here.", 420, 60)
    body += "  }\n}\n"
    return hdr + terms + body


def annotation(text, x, y):
    return (f"    Annotation {{\n      Name          {qstr('<html><body><p>' + text + '</p></body></html>')}\n"
            f"      Position      [{x}, {y}]\n    }} \n")


# ------------------------------------------------------------------ simulation model
def build_sim():
    simsrc = read(SRC_SIM)
    lab2 = read(SRC_LAB2)
    tut5 = read(SRC_TUT5)
    hdr = header_of(simsrc)
    hdr = hdr_set(hdr, "Name", '"ProjectB_Sim"')
    hdr = hdr_set(hdr, "TimeSpan", '"1.4"')
    hdr = hdr_set(hdr, "MaxStep", '"1e-5"')
    hdr = hdr_set(hdr, "InitializationCommands", qstr(SIM_INIT))
    comps, conns = [], []

    fet = component(simsrc, "FETD")
    def fetd(name, x, y):
        c = rename(place(fet, x, y), name)
        return set_param(c, "Ron", "Ron")
    # ---- DC side
    comps.append(simple("DCVoltageSource", "V_ITECH", 60, 200, [("V", "Vdc")], direction="down", flipped="on", label="east"))
    comps.append(simple("Resistor", "R_itech", 110, 120, [("R", "R_itech")], direction="left", label="north"))
    comps.append(simple("Capacitor", "C_dc", 170, 200, [("C", "Cdc"), ("v_init", "Vdc")], direction="down", label="east"))
    comps.append(simple("Voltmeter", "Vm_dc", 210, 200, direction="up", label="west"))
    # ---- bridge
    comps += [fetd("Q1", 280, 150), fetd("Q3", 280, 250), fetd("Q2", 380, 150), fetd("Q4", 380, 250)]
    # ---- filter
    comps.append(simple("Inductor", "L1", 460, 200, [("L", "Lf"), ("i_init", "0")], direction="left", label="north"))
    comps.append(simple("Resistor", "R_L1", 510, 200, [("R", "R_Lf")], direction="left", label="north"))
    comps.append(simple("Inductor", "L2", 460, 300, [("L", "Lf"), ("i_init", "0")], direction="left", label="north"))
    comps.append(simple("Resistor", "R_L2", 510, 300, [("R", "R_Lf")], direction="left", label="north"))
    comps.append(simple("Capacitor", "C1", 560, 240, [("C", "Cf"), ("v_init", "0")], direction="down", label="west"))
    comps.append(simple("Capacitor", "C2", 560, 330, [("C", "Cf"), ("v_init", "0")], direction="up", label="west"))
    comps.append(simple("Resistor", "R_b1", 590, 240, [("R", "R_bleed")], direction="down", label="east"))
    comps.append(simple("Resistor", "R_b2", 590, 330, [("R", "R_bleed")], direction="up", label="east"))
    # ---- load between the taps
    comps.append(simple("Resistor", "R_load_A", 660, 250, [("R", "R_load_A")], direction="down", label="east"))
    comps.append(simple("Resistor", "R_load_B", 740, 220, [("R", "R_load_B")], direction="down", label="east"))
    comps += [fetd("S_B1", 740, 270), fetd("S_B2", 740, 330)]
    comps.append(simple("Voltmeter", "Vm_o", 700, 250, direction="up", label="west"))

    # ---- nets (component, terminal); MosfetWithDiode: 1 drain, 2 source, 3 gate
    nets = [
        ([("V_ITECH", 1), ("R_itech", 2)], (60, 120)),
        ([("R_itech", 1), ("C_dc", 1), ("Vm_dc", 1), ("Q1", 1), ("Q2", 1)], (230, 100)),
        ([("V_ITECH", 2), ("C_dc", 2), ("Vm_dc", 2), ("Q3", 2), ("Q4", 2)], (230, 300)),
        ([("Q1", 2), ("Q3", 1), ("L1", 1)], (280, 200)),
        ([("Q2", 2), ("Q4", 1), ("L2", 1)], (380, 300)),
        ([("L1", 2), ("R_L1", 1)], (485, 200)),
        ([("L2", 2), ("R_L2", 1)], (485, 300)),
        ([("R_L1", 2), ("C1", 1), ("R_b1", 1), ("R_load_A", 1), ("R_load_B", 1), ("Vm_o", 1)], (620, 200)),
        ([("R_L2", 2), ("C2", 1), ("R_b2", 1), ("R_load_A", 2), ("S_B2", 1), ("Vm_o", 2)], (620, 300)),
        ([("C1", 2), ("C2", 2), ("R_b1", 2), ("R_b2", 2)], (575, 285)),            # nC, floating
        ([("R_load_B", 2), ("S_B1", 1)], (740, 245)),
        ([("S_B1", 2), ("S_B2", 2)], (740, 300)),                                   # anti-series switch
    ]
    for net, pt in nets:
        conns.append(wire(net, pt))

    # ---- measurements
    comps.append("""    Component {
      Type          PlecsProbe
      Name          "Probe"
      Show          on
      Position      [80, 420]
      Direction     right
      Flipped       off
      LabelPosition south
      Probe {
        Component     "Vm_dc"
        Path          ""
        Signals       {"Measured voltage"}
      }
      Probe {
        Component     "L1"
        Path          ""
        Signals       {"Inductor current"}
      }
      Probe {
        Component     "Vm_o"
        Path          ""
        Signals       {"Measured voltage"}
      }
      Probe {
        Component     "R_load_A"
        Path          ""
        Signals       {"Resistor current"}
      }
      Probe {
        Component     "R_load_B"
        Path          ""
        Signals       {"Resistor current"}
      }
    }""")
    comps.append(simple("SignalDemux", "DemuxP", 130, 420, [("Width", "5")], show="off"))
    conns.append(sig("Probe", 1, "DemuxP", 1))
    comps.append(simple("Sum", "io", 190, 500, [("IconShape", "1"), ("Inputs", "++"), ("DataType", "11"),
                                                 ("DataTypeOverflowMode", "1")]))
    conns += [sig("DemuxP", 5, "io", 2), sig("DemuxP", 6, "io", 3)]
    # sensing filter on each channel
    for i, (nm, src, st) in enumerate([("H_vdc", "DemuxP", 2), ("H_iL", "DemuxP", 3), ("H_vo", "DemuxP", 4),
                                       ("H_io", "io", 1)]):
        comps.append(simple("TransferFunction", nm, 260, 400 + 40 * i,
                            [("Numerator", "Hnum"), ("Denominator", "Hden"), ("X0", "0")],
                            extra="      Frame         [-30, -15; 30, 15]\n"))
        conns.append(sig(src, st, nm, 1))

    # ---- sequencer and tunables
    cs_t = component(lab2, "Unipolar SPWM\\nduty")
    seq = cscript(cs_t, "Test_sequence", 260, 600, SEQ_DECL, "", SEQ_OUTPUT, "", 1, 3, "Tctrl",
                  "t_enable, V1, V2, t_ref_up, t_ref_down, t_load_on, t_load_off")
    comps.append(seq)
    comps.append(simple("Constant", "dummy", 200, 600, [("Value", "0"), ("DataType", "10")],
                        extra="      Frame         [-10, -10; 10, 10]\n"))
    conns.append(sig("dummy", 1, "Test_sequence", 1))
    comps.append(simple("SignalDemux", "DemuxS", 320, 600, [("Width", "3")], show="off"))
    conns.append(sig("Test_sequence", 2, "DemuxS", 1))
    consts = [("Kp", "Kp0"), ("Ki", "Ki0"), ("FF", P.FF_GAIN), ("Trip_vo", 0), ("Trip_iL", 0), ("Trip_io", 0)]
    y = 660
    for nm, val in consts:
        comps.append(simple("Constant", nm, 330, y, [("Value", val), ("DataType", "10")],
                            extra="      Frame         [-15, -10; 15, 10]\n"))
        y += 30

    # ---- controller (same C as the firmware; one-period duty hold for the target's timing)
    comps.append(simple("SignalMux", "Mux", 420, 500, [("Width", "12")], show="off"))
    mux_inputs = [("H_vdc", 2), ("H_iL", 2), ("H_vo", 2), ("H_io", 2), ("DemuxS", 2), ("DemuxS", 3)] + \
                 [(nm, 1) for nm, _ in consts]
    for i, (src, st) in enumerate(mux_inputs):
        conns.append(sig(src, st, "Mux", i + 2))
    cs = cscript(cs_t, "PB_controller", 500, 500, CORE_C + GLUE_DECL + SIM_DECL_EXTRA, START_FCN,
                 SIM_OUTPUT, SIM_UPDATE, 12, 12, "Tctrl", ", ".join(PARAM_NAMES))
    comps.append(cs)
    conns.append(sig("Mux", 1, "PB_controller", 1))
    comps.append(simple("SignalDemux", "Demux", 570, 500, [("Width", "12")], show="off"))
    conns.append(sig("PB_controller", 2, "Demux", 1))

    # ---- modulator: d in 0..1 -> u = 2d - 1 against a [-1 1] carrier, dead time, enable
    spwm = component(simsrc, "Symmetrical PWM")
    tod = component(simsrc, "Turn-on Delay")
    notop = component(simsrc, "Logical\\nOperator")
    for leg, port, y0, top, bot in [("A", 2, 420, "Q1", "Q3"), ("B", 3, 540, "Q2", "Q4")]:
        comps.append(simple("Gain", f"x2_{leg}", 640, y0, [("K", "2"), ("Multiplication", "1"),
                                                           ("OutputDataType", "11"), ("DataTypeOverflowMode", "1"),
                                                           ("GainDataType", "11")]))
        comps.append(simple("Constant", f"one_{leg}", 640, y0 + 30, [("Value", "1"), ("DataType", "10")],
                            extra="      Frame         [-10, -10; 10, 10]\n"))
        comps.append(simple("Sum", f"u_{leg}", 690, y0, [("IconShape", "1"), ("Inputs", "+-"),
                                                         ("DataType", "11"), ("DataTypeOverflowMode", "1")]))
        conns += [sig("Demux", port, f"x2_{leg}", 1), sig(f"x2_{leg}", 2, f"u_{leg}", 2),
                  sig(f"one_{leg}", 1, f"u_{leg}", 3)]
        p = rename(place(spwm, 750, y0), f"PWM_{leg}")
        p = set_param(p, "fc", "fsw")
        comps.append(p)
        conns.append(sig(f"u_{leg}", 1, f"PWM_{leg}", 2))
        n = rename(place(notop, 800, y0 + 40), f"NOT_{leg}")
        comps.append(n)
        conns.append(sig(f"PWM_{leg}", 1, f"NOT_{leg}", 2))
        for sw, srcb, yy in [(top, f"PWM_{leg}", y0), (bot, f"NOT_{leg}", y0 + 40)]:
            d = rename(place(tod, 850, yy), f"DT_{sw}")
            d = set_param(d, "T_d", "deadtime")
            comps.append(d)
            conns.append(sig(srcb, 1, f"DT_{sw}", 1))
            comps.append(simple("LogicalOperator", f"EN_{sw}", 910, yy, [("Operator", "1"), ("Inputs", "2")]))
            conns += [sig(f"DT_{sw}", 2, f"EN_{sw}", 2), sig("Demux", 4, f"EN_{sw}", 3)]
            conns.append(sig(f"EN_{sw}", 1, sw, 3))
    # load-step switch gates
    conns += [sig("DemuxS", 4, "S_B1", 3), sig("DemuxS", 4, "S_B2", 3)]

    # ---- scopes
    scope_t = component(tut5, "Scope")
    s1 = rename(place(scope_t, 980, 300), "Scope power")
    s1 = s1.replace('"Input DC Voltage"', '"v_o (V)"').replace('"Inductor Current"', '"i_L1 (A)"') \
           .replace('"Output AC voltage"', '"v_dc (V)"')
    s1 = s1.replace("Open          \"0\"", "Open          \"1\"")
    s2 = rename(place(scope_t, 980, 500), "Scope control")
    s2 = s2.replace('"Input DC Voltage"', '"v_ref, amplitude (V)"').replace('"Inductor Current"', '"m"') \
           .replace('"Output AC voltage"', '"fault bits, PWM enable"')
    comps += [s1, s2]
    conns += [sig("DemuxP", 4, "Scope power", 1), sig("DemuxP", 3, "Scope power", 2),
              sig("DemuxP", 2, "Scope power", 3)]
    comps.append(simple("SignalMux", "MuxC1", 940, 480, [("Width", "2")], show="off"))
    comps.append(simple("SignalMux", "MuxC3", 940, 520, [("Width", "2")], show="off"))
    conns += [sig("Demux", 9, "MuxC1", 2), sig("Demux", 6, "MuxC1", 3), sig("MuxC1", 1, "Scope control", 1),
              sig("Demux", 7, "Scope control", 2),
              sig("Demux", 5, "MuxC3", 2), sig("Demux", 4, "MuxC3", 3), sig("MuxC3", 1, "Scope control", 3)]
    # the rest of the controller outputs to displays
    for i, (nm, port) in enumerate([("x_amp (V)", 8), ("vdc meas", 10), ("iL meas", 11), ("vo meas", 12),
                                    ("io meas", 13)]):
        comps.append(simple("Display", nm, 640, 640 + 30 * i, [("Notation", "1"), ("Precision", "3")],
                            extra="      Frame         [-31, -11; 31, 11]\n"))
        conns.append(sig("Demux", port, nm, 1))

    body = ("  Schematic {\n    Location      [0, 50; 1400, 900]\n    ZoomFactor    1\n"
            "    SliderPosition [0, 0]\n    ShowBrowser   off\n    BrowserWidth  100\n")
    conns = merge_signals(conns, positions_of(comps))
    body += "\n".join(comps) + "\n" + "\n".join(conns) + "\n"
    body += annotation("Project B switched simulation (Group 8). Test sequence: soft start to V1, "
                       "Vref step V1 -> V2 at 0.6 s and back at 0.8 s, load step 25 -> 12.5 ohm at 1.0 s and back "
                       "at 1.2 s. Set sensing_bench = 0 in the init commands for the HIL filter.", 500, 60)
    body += "  }\n}\n"
    return hdr + body


# ------------------------------------------------------------------ checks
def check(text, name):
    # braces balance (outside strings)
    depth = 0
    for line in text.split("\n"):
        s = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)
        depth += s.count("{") - s.count("}")
        assert depth >= 0, (name, line)
    assert depth == 0, (name, depth)
    comps = re.findall(r'\n    Component \{\n      Type +(\S+)\n(?:      SrcComponent +".*?"\n)?      Name +((?:"(?:[^"\\]|\\.)*"\n?)+)', text)
    names = set()
    for typ, nm in comps:
        n = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', nm)).replace("\\n", "\n")
        assert n not in names, ("duplicate", n)
        names.add(n)
    conn_text = "\n".join(re.findall(r"\n    Connection \{\n.*?\n    \}", text, flags=re.S))
    refs = re.findall(r'(?:Src|Dst)Component +((?:"(?:[^"\\]|\\.)*"))', conn_text)
    for r in refs:
        n = r[1:-1].replace("\\n", "\n")
        assert n in names, (name, "unknown component", n)
    print(f"{name}: {len(names)} components, {len(refs)} connection ends, braces balanced")


def main():
    fw = build_firmware()
    check(fw, "Controller.plecs")
    with open(os.path.join(HERE, "Controller.plecs"), "w", encoding="utf-8") as fh:
        fh.write(fw)
    sim = build_sim()
    check(sim, "ProjectB_Sim.plecs")
    with open(os.path.join(HERE, "ProjectB_Sim.plecs"), "w", encoding="utf-8") as fh:
        fh.write(sim)
    # a plain copy of the controller code for the report ZIP
    with open(os.path.join(HERE, "controller_cscript_sections.txt"), "w", encoding="utf-8") as fh:
        fh.write("==== Declarations ====\n" + CORE_C + GLUE_DECL + "\n==== Start function ====\n" + START_FCN +
                 "\n\n==== Output function ====\n" + FW_OUTPUT + "\n\n==== Update function ====\n" + FW_UPDATE +
                 "\n\n==== Parameters ====\n" + ", ".join(PARAM_NAMES) + "\n")


if __name__ == "__main__":
    main()
