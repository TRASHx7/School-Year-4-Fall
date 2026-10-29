#!/usr/bin/env python3
"""Generate the Group 8 Project B PLECS models.

Writes, next to this folder:
  ENEL585_F26_ProjectB_G8_Firmware.plecs  controller for the LAUNCHXL-F28P55X
  ENEL585_F26_ProjectB_G8_Station.plecs   switched station model, same controller

Block definitions are copied from the course's own PLECS files (orientation
model, LaunchPad SPWM labs, bipolar SPWM simulation) and only renamed,
moved and re-parameterised, so every block is in a form PLECS 5.0 wrote
itself. The controller C code comes from cscript/ and is embedded verbatim
in both models.

Usage: python3 generate_plecs.py
"""
import base64
import re
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
COURSE = HERE.parents[2] / ("ENEL 585 L01 - (Fall 2026) - Introduction to Power "
                            "Electronics - 10152026 - 853 PM")
SRC = HERE / "cscript"

ORIENT = (COURSE / "ENEL585_F26_ProjectOrientation_PLECS_20260909.plecs").read_text()
UNIPOLAR = (COURSE / "spwm_unipolar_ti_launchpad.plecs").read_text()
BIPOLAR = (COURSE / "SPWM_bipolar.plecs").read_text()


# --------------------------------------------------------------------------
# PLECS text helpers
# --------------------------------------------------------------------------
def q(s):
    """PLECS string literal, split over lines the way PLECS writes long ones."""
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    chunks, cur = [], ""
    for ch in s:
        cur += ch
        if len(cur) >= 76 and not cur.endswith("\\"):
            chunks.append(cur)
            cur = ""
    chunks.append(cur)
    return '"' + '"\n"'.join(chunks) + '"'


def block_at(text, start):
    """Return the brace-balanced block that opens at or after index start."""
    i = text.index("{", start)
    depth, j = 0, i
    in_str = False
    while True:
        c = text[j]
        if in_str:
            if c == "\\":
                j += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:j + 1]
        j += 1


def component(text, name):
    """Component block with the given Name, from a model file."""
    m = re.search(r'\n(    Component \{\n      Type +\S+\n(?:      SrcComponent +"[^"]*"\n)?'
                  r'      Name +"' + re.escape(name) + r'"\n)', text)
    if not m:
        raise KeyError(name)
    return block_at(text, m.start(1))


def set_field(blk, field, value):
    new, n = re.subn(r'(\n      ' + field + r' +)[^\n]*', lambda m: m.group(1) + value, blk, count=1)
    if n != 1:
        raise KeyError(field)
    return new


def set_param(blk, var, value):
    """Replace a Parameter's Value (value given as a plain string)."""
    pat = re.compile(r'(Variable +"' + re.escape(var) + r'"\n +Value +)("(?:[^"\\]|\\.)*"'
                     r'(?:\n"(?:[^"\\]|\\.)*")*)')
    new, n = pat.subn(lambda m: m.group(1) + q(value), blk, count=1)
    if n != 1:
        raise KeyError(var)
    return new


def place(blk, name, pos, direction=None, flipped=None, show=None):
    blk = set_field(blk, "Name", q(name))
    blk = set_field(blk, "Position", "[%d, %d]" % pos)
    if direction:
        blk = set_field(blk, "Direction", direction)
    if flipped:
        blk = set_field(blk, "Flipped", flipped)
    if show:
        blk = set_field(blk, "Show", show)
    return blk


def header_field(text, key):
    """Raw (possibly multi-line) value of a top-level model setting."""
    m = re.search(r'\n  ' + key + r' +("(?:[^"\\]|\\.)*"(?:\n"(?:[^"\\]|\\.)*")*)', text)
    return m.group(1)


def string_list_blob(names):
    """QDataStream QVariant(QStringList), as used for CodeGenInliningExceptions."""
    b = struct.pack(">IBI", 11, 0, len(names))
    for n in names:
        u = n.encode("utf-16-be")
        b += struct.pack(">I", len(u)) + u
    return base64.b64encode(b).decode()


def split_blob(s):
    return '"' + '"\n"'.join(s[i:i + 78] for i in range(0, len(s), 78)) + '"'


class Net:
    """Collects components and connections for one schematic."""

    def __init__(self):
        self.parts, self.conns = [], []

    def add(self, blk):
        self.parts.append(blk)

    def sig(self, src, st, dsts, points=None):
        """Signal from (src, terminal) to one or more (dst, terminal)."""
        self.conns.append(conn("Signal", src, st, dsts, points))

    def wire(self, src, st, dsts, points=None):
        self.conns.append(conn("Wire", src, st, dsts, points))

    def event(self, src, st, dsts, points=None):
        self.conns.append(conn("Event", src, st, dsts, points))

    def text(self):
        return "".join(p + "\n" for p in self.parts) + "".join(self.conns)


def _pts(points, ind):
    if not points:
        return ""
    return ind + "Points        [" + "; ".join("%d, %d" % p for p in points) + "]\n"


def conn(kind, src, st, dsts, points=None):
    s = ("    Connection {\n      Type          %s\n      SrcComponent  %s\n"
         "      SrcTerminal   %d\n" % (kind, q(src), st))
    s += _pts(points, "      ")
    if len(dsts) == 1:
        d = dsts[0]
        s += _pts(d[2] if len(d) > 2 else None, "      ")
        s += "      DstComponent  %s\n      DstTerminal   %d\n" % (q(d[0]), d[1])
    else:
        for d in dsts:
            s += "      Branch {\n"
            s += _pts(d[2] if len(d) > 2 else None, "        ")
            s += "        DstComponent  %s\n        DstTerminal   %d\n      }\n" % (q(d[0]), d[1])
    return s + "    }\n"


def annotation(html_text, pos):
    return ('    Annotation {\n      Name          %s\n      Position      [%d, %d]\n    } \n'
            % (q("<html><body>\n<p><span style=\" font-weight:700;\">" + html_text
                 + "</span></p></body></html>"), pos[0], pos[1]))


def note(text, pos):
    return ('    Annotation {\n      Name          %s\n      Position      [%d, %d]\n    } \n'
            % (q(text), pos[0], pos[1]))


# --------------------------------------------------------------------------
# Block templates (from the course files)
# --------------------------------------------------------------------------
T_PWM_ADCTRIG = component(ORIENT, "PWM")          # AdcTriggerMode 2 (triggers ADCs)
T_PWM = component(UNIPOLAR, "PWM1")               # second leg, no ADC trigger
T_ADC = component(ORIENT, "ADC1")
T_TASK = component(ORIENT, "Control Task Trigger")
T_PROT = component(ORIENT, "Protection")
T_LOAD = component(ORIENT, "Load")
T_DISP = component(ORIENT, "%")
T_SW = component(ORIENT, "enableswitch")
T_CONST = component(ORIENT, "enable")
T_CSCRIPT = component(UNIPOLAR, "Unipolar SPWM\\nduty")
T_DEMUX = component(UNIPOLAR, "Demux")
T_SCOPE = component(BIPOLAR, "Scope4")
T_FET = component(BIPOLAR, "FETD")
T_RES = component(BIPOLAR, "R1")
T_IND = component(BIPOLAR, "L2")
T_VDC = component(BIPOLAR, "Vd")
T_VM = component(BIPOLAR, "Vm1")
T_PROBE = component(BIPOLAR, "Probe3")
T_GOTO = component(BIPOLAR, "Goto")
T_FROM = component(BIPOLAR, "From")
T_DELAY = component(BIPOLAR, "Turn-on Delay")
T_LOGIC = component(BIPOLAR, "Logical\\nOperator")
T_SPWM = component(BIPOLAR, "Symmetrical PWM")


def const(name, value, pos):
    b = place(T_CONST, name, pos)
    return set_param(b, "Value", value)


def goto(tag, pos, name=None):
    b = place(T_GOTO, name or ("Goto " + tag), pos, show="off")
    return set_param(b, "Tag", tag)


def frm(tag, pos, name=None, direction=None):
    b = place(T_FROM, name or ("From " + tag), pos, direction=direction, show="off")
    return set_param(b, "Tag", tag)


def resistor(name, value, pos, direction="up"):
    b = place(T_RES, name, pos, direction=direction)
    return set_param(b, "R", value)


def inductor(name, value, pos, direction="left"):
    b = place(T_IND, name, pos, direction=direction)
    return set_param(b, "L", value)


def capacitor(name, value, pos, v_init="0", direction="up"):
    return ("    Component {\n      Type          Capacitor\n      Name          %s\n"
            "      Show          on\n      Position      [%d, %d]\n      Direction     %s\n"
            "      Flipped       off\n      LabelPosition east\n"
            "      Parameter {\n        Variable      \"C\"\n        Value         %s\n"
            "        Show          off\n      }\n"
            "      Parameter {\n        Variable      \"v_init\"\n        Value         %s\n"
            "        Show          off\n      }\n    }"
            % (q(name), pos[0], pos[1], direction, q(value), q(v_init)))


def fet(name, pos, ron="Ron", direction="up"):
    b = place(T_FET, name, pos, direction=direction)
    return set_param(b, "Ron", ron)


def logic(name, op, n_in, pos):
    b = place(T_LOGIC, name, pos)
    b = set_param(b, "Operator", op)
    return set_param(b, "Inputs", n_in)


def delay(name, pos):
    return place(T_DELAY, name, pos)    # T_d = dead_time in the template


def scope(name, pos, axes, loc):
    b = place(T_SCOPE, name, pos)
    b = set_field(b, "Location", loc)
    b = set_field(b, "Axes", q(str(len(axes))))
    b = set_field(b, "Open", q("0"))
    one = re.search(r"      Axis \{\n.*?\n      \}\n", b, re.S).group(0)
    four = re.search(r"        Axis \{\n.*?\n        \}\n", b, re.S).group(0)
    b = re.sub(r"(      Axis \{\n.*?\n      \}\n)+", lambda m: "".join(
        one.replace('Name          ""', "Name          " + q(a)) for a in axes), b, count=1, flags=re.S)
    b = re.sub(r"(        Axis \{\n.*?\n        \}\n)+", lambda m: four * len(axes), b,
               count=1, flags=re.S)
    return b


def cscript(name, pos, n_in, n_out, ts, params, sections, n_cont="0", n_disc="0",
            feedthrough="1"):
    b = place(T_CSCRIPT, name, pos)
    b = set_param(b, "NumInputs", n_in)
    b = set_param(b, "NumOutputs", n_out)
    b = set_param(b, "NumContStates", n_cont)
    b = set_param(b, "NumDiscStates", n_disc)
    b = set_param(b, "DirectFeedthrough", feedthrough)
    b = set_param(b, "Ts", ts)
    b = set_param(b, "Parameters", params)
    for var in ("Declarations", "StartFcn", "OutputFcn", "UpdateFcn", "DerivativeFcn",
                "TerminateFcn"):
        b = set_param(b, var, sections.get(var, ""))
    return b


def section(fname):
    return (SRC / fname).read_text().rstrip("\n")


CTRL = {
    "Declarations": section("ctrl_declarations.c"),
    "StartFcn": section("ctrl_start.c"),
    "OutputFcn": section("ctrl_output.c"),
    "UpdateFcn": section("ctrl_update.c"),
}
SENS = {
    "Declarations": section("sens_declarations.c"),
    "StartFcn": section("sens_start.c"),
    "OutputFcn": section("sens_output.c"),
    "DerivativeFcn": section("sens_derivative.c"),
}
SCEN = {
    "Declarations": section("scen_declarations.c"),
    "OutputFcn": section("scen_output.c"),
}

# Controller parameter vector, in the order of the enum in ctrl_declarations.c
CTL_PAR = ["N_per", "Ts", "K_vo", "O_vo", "K_il", "O_il", "K_io", "O_io", "K_dc", "O_dc",
           "src(1)", "src(2)", "src(3)", "src(4)", "Vdc_nom", "H60",
           "Vo_trip", "IL_trip", "Io_trip", "Vdc_trip", "Vdc_min", "Vref_max",
           "slew", "m_max", "x_max", "I_lim", "K_fold", "fold_dec", "tau_dc"]
enum = re.search(r"enum \{(.*?)P_NUM", CTRL["Declarations"], re.S).group(1)
enum = re.findall(r"\bP_\w+", re.sub(r"/\*.*?\*/", "", enum, flags=re.S))
assert len(enum) == len(CTL_PAR), (len(enum), len(CTL_PAR))

INIT_COMMON = """\
%% ENEL 585 Fall 2026, Project B: single-phase standalone inverter
%% Group 8, Station 6, Lab B01

%% Timing: N_per samples per 60 Hz period. The carrier is the nearest value the
%% ePWM up-down counter hits exactly, so the reference stays synchronous.
f1    = 60;
N_per = 166;                               % even; carrier periods per 60 Hz period
fclk  = 150e6;                             % SYSCLK in the TI28P55x target settings [Hz]
fsw   = fclk/(2*round(fclk/(2*N_per*f1))); % 9960.16 Hz, below the 10 kHz ceiling
Ts    = 1/fsw;                             % control and ADC sample period [s]
dead_time = 2e-6;                          % per-leg dead time [s] (Lab 2 used 5e-6)

%% Sensing: V_pin = O + signal/K at the ADC pin (Inverter Box Setup Guide:
%% 1.667 V centre, 0.213 V/V after the probe for voltage, 0.154 V/V for current)
K_vo = 10/0.213;  O_vo = 1.667;   % VProbe 1, 10:1: output voltage, tap A - tap B
K_il = 1/0.0154;  O_il = 1.667;   % CProbe 2, 100 mV/A: leg-A inductor current
K_io = 1/0.0154;  O_io = 1.667;   % CProbe 1, 100 mV/A: load current
K_dc = 10/0.213;  O_dc = 1.667;   % VProbe 2, 10:1: dc input voltage
src  = [1 2 3 4];                 % pin carrying [vo iL io vdc]: 1=B2 2=B0 3=B1 4=A6, 0=none
H60  = 0.9949;                    % interface-board filter gain at 60 Hz (amplitude calibration)
Vdc_nom = 50;                     % used if src(4) = 0
"""

INIT_PROTECT = """
%% Protection (latched; clear by setting enableswitch to 0). Pin voltages:
Vo_trip  = 50;    % |vo| [V]   -> 0.602 V / 2.732 V
IL_trip  = 9;     % |iL| [A]   -> 1.528 V / 1.806 V
Io_trip  = 6;     % |io| [A]   -> 1.575 V / 1.759 V
Vdc_trip = 55;    % vdc [V]    -> 2.839 V
Vdc_min  = 20;    % switching starts only once the filtered vdc exceeds this [V]
"""

INIT_CONTROL = """
%% Amplitude control (see README for the loop design)
Vref_max = 32;    % largest accepted Vref_rms [V]
slew     = 5;     % amplitude slew [V pk per half cycle] = 600 V/s, also the soft start
m_max    = 0.98;  % modulation limit; anti-windup holds the trim here
x_max    = 10;    % integral trim limit [V pk]
I_lim    = 6;     % current limit on the half-cycle peak of the sensed iL [A]
K_fold   = 2;     % foldback gain [V pk per A per half cycle]
fold_dec = 0.5;   % foldback recovery [V pk per half cycle]
tau_dc   = 0.02;  % dc-link voltage filter for the feedforward [s]

ctl_par = [N_per Ts K_vo O_vo K_il O_il K_io O_io K_dc O_dc src Vdc_nom H60 Vo_trip IL_trip Io_trip Vdc_trip Vdc_min Vref_max slew m_max x_max I_lim K_fold fold_dec tau_dc];
"""

INIT_FW = INIT_COMMON + """
%% Target: 1 = bench (interface board), 2 = remote Typhoon HIL
target = 1;
if target == 2
  % Replace with the provided Project B HIL model's I/O before flashing:
  % in its .tse, analog_outputs lists 'AOn;signal;scale;offset;...' per channel.
  % The orientation model used AO1 -> ADCINA6 and AO2 -> ADCINB2, scale 10.
  K_vo = 10/0.213;  O_vo = 1.667;
  K_il = 1/0.0154;  O_il = 1.667;
  src  = [1 2 0 0];               % no io or vdc channel: feedforward uses Vdc_nom
end

%% Pins (Inverter Box Setup Guide, Table 1 and 2)
ADCB_CH   = [2 0 1];   % ADCINB2 = VProbe 1, ADCINB0 = CProbe 2, ADCINB1 = CProbe 1
ADCA_CH   = [6];       % ADCINA6 = VProbe 2
PWM_LEG_A = 1;         % EPWM1A/B = Top 1 / Bot 1 (leg A, Q1/Q2)
PWM_LEG_B = 2;         % EPWM2A/B = Top 2 / Bot 2 (leg B, Q3/Q4)
PWR_GPIO  = 21;        % powerstage enable output, as in the orientation model
""" + INIT_PROTECT + INIT_CONTROL

INIT_SIM = INIT_COMMON + INIT_PROTECT + """
protection_test = 0;  % 1: lower IL_trip to 2.5 A so the load step trips the bridge
if protection_test
  IL_trip = 2.5;
end
""" + INIT_CONTROL + """
%% Station (Project B sheet)
Vdc   = 50;       % ITECH setting [V]
Rs    = 0.02;     % supply leads [ohm]
Cdc   = 1.1e-3;   % SEMITEACH dc link [F]
Lf    = 47e-6;    % per branch, Wurth 7443783533470, +-20 %
RLf   = 0.02;     % per branch winding + wiring [ohm] (estimate)
Cf    = 62e-6;    % per branch; star point floating
Rbl   = 100e3;    % capacitor bleeders [ohm]
Ron   = 0.02;     % switch on-resistance [ohm] (no IGBT/diode drop modelled)
R_bank = 250/10;  % 10 bank switches closed: 25 ohm (OP1)
R_step = 250/10;  % 10 more switches: 25 || 25 = 12.5 ohm (OP2, load step)

%% Interface-board sensing model
sens_par = [1500 700 900 1.667 0.213/10 0.0154 3.3 12 Vdc];

%% Test sequence [t_en t_load_on t_ref_up t_ref_dn t_load_off V_op1 V_op2]
scen_par = [0.02 0.30 0.50 0.70 0.85 25 30];
"""


# --------------------------------------------------------------------------
# Model header
# --------------------------------------------------------------------------
def header(name, init, timespan, maxstep, reltol, fixedstep, exceptions):
    h = UNIPOLAR[:UNIPOLAR.index("\n  Terminal {")]
    h = re.sub(r'(\n  Name +)"[^"]*"', lambda m: m.group(1) + q(name), h, count=1)
    for key, val in (("TimeSpan", timespan), ("MaxStep", maxstep), ("RelTol", reltol),
                     ("FixedStep", fixedstep)):
        h = re.sub(r'(\n  ' + key + r' +)"[^"]*"', lambda m, v=val: m.group(1) + q(v), h, count=1)
    old = header_field(h, "InitializationCommands")
    h = h.replace(old, q(init), 1)
    old = header_field(h, "CodeGenInliningExceptions")
    h = h.replace(old, split_blob(string_list_blob(exceptions)), 1)
    # TI28P55x target settings from the orientation model (150 MHz SYSCLK,
    # External Mode on GPIO 28/29, analog trips off)
    old = header_field(h, "CodeGenTargetSettings")
    h = h.replace(old, header_field(ORIENT, "CodeGenTargetSettings"), 1)
    return h


def schematic(body, loc="[0, 26; 1536, 864]"):
    return ("  Schematic {\n    Location      %s\n    ZoomFactor    1.2\n"
            "    SliderPosition [0, 0]\n    ShowBrowser   off\n    BrowserWidth  100\n"
            "%s  }\n}\n" % (loc, body))


# --------------------------------------------------------------------------
# Firmware model
# --------------------------------------------------------------------------
def firmware():
    n = Net()
    # ADCs: one block per unit, pin voltage out (scaling is done in the controller)
    for nm, unit, ch, idx, pos in (("ADC_B", "2", "ADCB_CH", "1", (90, 130)),
                                   ("ADC_A", "1", "ADCA_CH", "2", (90, 210))):
        b = place(T_ADC, nm, pos)
        b = set_param(b, "AdcUnit", unit)
        b = set_param(b, "Input", ch)
        b = set_param(b, "Scale", "1")
        b = set_param(b, "Offset", "0")
        b = set_param(b, "TargetPortIndices", idx)
        n.add(b)
    n.add(place(T_TASK, "Control Task Trigger", (180, 235)))

    n.add(const("Vref_rms", "25", (90, 290)))
    n.add(const("enable", "1", (40, 330)))
    n.add(const("disable", "0", (40, 360)))
    n.add(place(T_SW, "enableswitch", (90, 345)))
    n.add(const("Kp_amp", "0", (90, 400)))
    n.add(const("Ki_amp", "0.4", (90, 440)))

    n.add(cscript("Controller", (300, 290), "[3, 1, 1, 1, 1, 1]", "[2, 1, 3, 7]", "Ts",
                  "ctl_par", CTRL, n_disc="1"))
    n.add(place(T_DEMUX, "Demux", (420, 230)))

    for nm, tpl, unit, idx, pos in (("PWM_A", T_PWM_ADCTRIG, "[PWM_LEG_A]", "1", (560, 160)),
                                    ("PWM_B", T_PWM, "[PWM_LEG_B]", "3", (560, 310))):
        b = place(tpl, nm, pos)
        b = set_param(b, "PwmUnit", unit)
        b = set_param(b, "CarrierFreq", "fsw")
        b = set_param(b, "Phase", "0")
        b = set_param(b, "FixedDeadTime", "dead_time")
        b = set_param(b, "TargetPortIndices", idx)
        n.add(b)

    b = place(T_PROT, "Powerstage Protection", (560, 430))
    b = set_param(b, "EnableSignalGpio", "PWR_GPIO")
    n.add(b)

    sd = set_param(place(T_DEMUX, "Demux status", (420, 400)), "Width", "7")
    n.add(sd)
    n.add(scope("Scope", (520, 520), ["vo, iL, io (sensed)", "Vpk measured", "m"],
                "[100, 100; 700, 600]"))
    n.add(place(T_DISP, "status", (560, 590)))
    n.add(place(T_LOAD, "Load", (700, 60)))
    n.add(place(T_DISP, "%", (765, 60)))

    # ADC trigger from leg A's PWM, task trigger from the last ADC (as in the
    # orientation model)
    n.event("PWM_A", 3, [("ADC_B", 3), ("ADC_A", 3, [(30, 170)])], [(610, 140), (610, 40), (30, 40)])
    n.event("ADC_B", 2, [("Control Task Trigger", 1)], [(140, 145), (140, 235)])
    n.sig("ADC_B", 1, [("Controller", 1)])
    n.sig("ADC_A", 1, [("Controller", 2)])
    n.sig("Vref_rms", 1, [("Controller", 3)])
    n.sig("enable", 1, [("enableswitch", 2)])
    n.sig("disable", 1, [("enableswitch", 3)])
    n.sig("enableswitch", 1, [("Controller", 4)])
    n.sig("Kp_amp", 1, [("Controller", 5)])
    n.sig("Ki_amp", 1, [("Controller", 6)])
    n.sig("Controller", 7, [("Demux", 1)])
    n.sig("Demux", 2, [("PWM_A", 1)], [(480, 160)])
    n.sig("Demux", 3, [("PWM_B", 1)], [(480, 310)])
    n.sig("Controller", 8, [("Powerstage Protection", 1)], [(380, 430)])
    n.sig("Controller", 9, [("Scope", 1)])
    n.sig("Controller", 10, [("Demux status", 1), ("status", 1)])
    n.sig("Demux status", 2, [("Scope", 2)])
    n.sig("Demux status", 4, [("Scope", 3)])
    n.sig("Load", 1, [("%", 1)])

    body = n.text()
    body += annotation("ENEL 585 Project B, Group 8: standalone inverter firmware "
                       "(LAUNCHXL-F28P55X)", (330, 15))
    body += note("Pins: VProbe 1 (vo) ADCINB2, CProbe 2 (iL) ADCINB0, CProbe 1 (io) ADCINB1, "
                 "VProbe 2 (vdc) ADCINA6.\nGates: EPWM1A/B = Top 1/Bot 1 (leg A), "
                 "EPWM2A/B = Top 2/Bot 2 (leg B). Leave leg 3 inhibited.", (330, 650))
    body += note("Start: set enableswitch to 1 (or <model>_P.enableswitch_SwitchState = 1 "
                 "in CCS).\nA trip latches; set it to 0 to clear. status = [Vpk_meas "
                 "Vpk_cmd m fault Vrms ILrms Pout],\nfault bits: 1 vo, 2 iL, 4 io, 8 vdc.",
                 (330, 700))

    terms = ("  Terminal {\n    Type          Input\n    Index         \"1\"\n  }\n"
             "  Terminal {\n    Type          Input\n    Index         \"2\"\n  }\n"
             "  Terminal {\n    Type          Output\n    Index         \"1\"\n  }\n"
             "  Terminal {\n    Type          Output\n    Index         \"2\"\n  }\n"
             "  Terminal {\n    Type          Output\n    Index         \"3\"\n  }\n")
    h = header("ENEL585_F26_ProjectB_G8_Firmware", INIT_FW, "1.0", "1e-3", "1e-3", "Ts",
               ["enableswitch", "Vref_rms", "Kp_amp", "Ki_amp"])
    return h + "\n" + terms + schematic(body)


# --------------------------------------------------------------------------
# Switched station model
# --------------------------------------------------------------------------
def station():
    n = Net()
    # ---- power stage (x grows to the right, y down; DC+ rail y=60, DC- y=300)
    b = place(T_VDC, "ITECH", (60, 180))
    n.add(set_param(b, "V", "Vdc"))
    n.add(resistor("Rs", "Rs", (110, 60), direction="right"))
    n.add(capacitor("Cdc", "Cdc", (170, 180), v_init="Vdc"))
    n.add(place(T_VM, "Vm_dc", (220, 180)))
    n.add(fet("Q1", (300, 120)))
    n.add(fet("Q2", (300, 240)))
    n.add(fet("Q3", (420, 120)))
    n.add(fet("Q4", (420, 240)))
    n.add(resistor("RL1", "RLf", (520, 180), direction="right"))
    n.add(inductor("Lf1", "Lf", (580, 180), direction="left"))
    n.add(inductor("Lf2", "Lf", (580, 330), direction="right"))
    n.add(resistor("RL2", "RLf", (520, 330), direction="left"))
    n.add(capacitor("Cf1", "Cf", (650, 225)))
    n.add(capacitor("Cf2", "Cf", (650, 285)))
    n.add(resistor("Rbl1", "Rbl", (690, 225)))
    n.add(resistor("Rbl2", "Rbl", (690, 285)))
    n.add(resistor("R_bank", "R_bank", (760, 255)))
    n.add(resistor("R_step", "R_step", (840, 210)))
    n.add(fet("S1", (840, 270)))
    n.add(fet("S2", (840, 320), direction="down"))
    n.add(place(T_VM, "Vm_o", (910, 255)))

    # Rail and node wiring
    n.wire("ITECH", 1, [("Rs", 1)], [(60, 60)])
    n.wire("Rs", 2, [("Cdc", 1, [(170, 60)]), ("Vm_dc", 1, [(220, 60)]),
                     ("Q1", 1, [(300, 60)]), ("Q3", 1, [(420, 60)])], [(140, 60)])
    n.wire("ITECH", 2, [("Cdc", 2, [(170, 300)]), ("Vm_dc", 2, [(220, 300)]),
                        ("Q2", 2, [(300, 300)]), ("Q4", 2, [(420, 300)])], [(60, 300)])
    n.wire("Q1", 2, [("Q2", 1), ("RL1", 1, [(300, 180)])])           # node A
    n.wire("Q3", 2, [("Q4", 1), ("RL2", 2, [(440, 180), (440, 330)])])  # node B
    n.wire("RL1", 2, [("Lf1", 1)])
    n.wire("RL2", 1, [("Lf2", 2)])
    n.wire("Lf1", 2, [("Cf1", 1, [(650, 180)]), ("Rbl1", 1, [(690, 180)]),
                      ("R_bank", 1, [(760, 180)]), ("R_step", 1, [(840, 180)]),
                      ("Vm_o", 1, [(910, 180)])])                       # tap A
    n.wire("Cf1", 2, [("Cf2", 1), ("Rbl1", 2, [(670, 255), (690, 255)]),
                      ("Rbl2", 1, [(670, 255), (690, 255)])])          # star nC
    n.wire("Lf2", 1, [("Cf2", 2, [(650, 330)]), ("Rbl2", 2, [(690, 330)]),
                      ("R_bank", 2, [(760, 330)]), ("S2", 1, [(840, 345)]),
                      ("Vm_o", 2, [(910, 330)])])                       # tap B
    n.wire("R_step", 2, [("S1", 1)])
    n.wire("S1", 2, [("S2", 2)])                                     # anti-series pair

    # ---- probes, sensing and controller
    pr = place(T_PROBE, "Probe", (120, 430))
    probes = ('      Probe {\n        Component     %s\n        Path          ""\n'
              '        Signals       {%s}\n      }\n')
    plist = "".join(probes % (q(c), q(s)) for c, s in (
        ("Lf1", "Inductor current"), ("R_bank", "Resistor current"),
        ("R_step", "Resistor current"), ("Vm_o", "Measured voltage"),
        ("Vm_dc", "Measured voltage")))
    pr = re.sub(r"(      Probe \{\n.*?\n      \}\n)+", lambda m: plist, pr, count=1, flags=re.S)
    n.add(pr)
    n.add(cscript("Interface board\nsensing", (250, 430), "5", "[3, 1]", "0", "sens_par",
                  SENS, n_cont="8", feedthrough="0"))
    n.add(cscript("Test sequence", (250, 530), "0", "[1, 1, 1]", "Ts", "scen_par", SCEN,
                  feedthrough="0"))
    n.add(const("Kp_amp", "0", (250, 590)))
    n.add(const("Ki_amp", "0.4", (250, 630)))
    n.add(cscript("Controller", (420, 500), "[3, 1, 1, 1, 1, 1]", "[2, 1, 3, 7]", "Ts",
                  "ctl_par", CTRL, n_disc="1"))
    n.add(place(T_DEMUX, "Demux", (520, 450)))

    # ---- modulator (TI up-down carrier stand-in) and gate logic
    for nm, pos in (("PWM leg A", (580, 430)), ("PWM leg B", (580, 520))):
        b = place(T_SPWM, nm, pos)
        b = set_param(b, "fc", "fsw")
        b = set_param(b, "carrier_limits", "[0 1]")
        n.add(set_param(b, "output_values", "[0 1]"))
    n.add(logic("NOT A", "6", "2", (640, 460)))
    n.add(logic("NOT B", "6", "2", (640, 550)))
    for i, y in enumerate((420, 460, 510, 550), start=1):
        n.add(logic("AND%d" % i, "1", "2", (700, y)))
        b = delay("Dead time %d" % i, (760, y))
        n.add(set_param(b, "T_d", "dead_time"))
        n.add(goto("G%d" % i, (810, y)))
    for i, (q_, y) in enumerate((("Q1", 120), ("Q2", 240), ("Q3", 120), ("Q4", 240)), start=1):
        x = 300 if q_ in ("Q1", "Q2") else 420
        n.add(frm("G%d" % i, (x - 50, y)))
    n.add(goto("LS", (340, 560)))
    n.add(frm("LS", (790, 270), name="From LS1"))
    n.add(frm("LS", (790, 320), name="From LS2"))

    sd = set_param(place(T_DEMUX, "Demux probe", (180, 380)), "Width", "5")
    n.add(sd)
    sd = set_param(place(T_DEMUX, "Demux status", (520, 600)), "Width", "7")
    n.add(sd)
    n.add(scope("Scope", (680, 650), ["Output voltage vo [V]", "Inductor current iL [A]",
                                      "Amplitude measured [V pk]", "Modulation index m"],
                "[100, 100; 900, 800]"))
    n.add(place(T_DISP, "status", (680, 720)))

    n.sig("Probe", 1, [("Interface board\nsensing", 1), ("Demux probe", 1)])
    n.sig("Interface board\nsensing", 2, [("Controller", 1)])
    n.sig("Interface board\nsensing", 3, [("Controller", 2)])
    n.sig("Test sequence", 1, [("Controller", 3)])
    n.sig("Test sequence", 2, [("Controller", 4)])
    n.sig("Test sequence", 3, [("Goto LS", 1)])
    n.sig("Kp_amp", 1, [("Controller", 5)])
    n.sig("Ki_amp", 1, [("Controller", 6)])
    n.sig("Controller", 7, [("Demux", 1)])
    n.sig("Demux", 2, [("PWM leg A", 2)])
    n.sig("Demux", 3, [("PWM leg B", 2)])
    n.sig("PWM leg A", 1, [("AND1", 2), ("NOT A", 2)])
    n.sig("PWM leg B", 1, [("AND3", 2), ("NOT B", 2)])
    n.sig("NOT A", 1, [("AND2", 2)])
    n.sig("NOT B", 1, [("AND4", 2)])
    n.sig("Controller", 8, [("AND%d" % i, 3) for i in range(1, 5)])
    for i in range(1, 5):
        n.sig("AND%d" % i, 1, [("Dead time %d" % i, 1)])
        n.sig("Dead time %d" % i, 2, [("Goto G%d" % i, 1)])
    for i, q_ in enumerate(("Q1", "Q2", "Q3", "Q4"), start=1):
        n.sig("From G%d" % i, 1, [(q_, 3)])
    n.sig("From LS1", 1, [("S1", 3)])
    n.sig("From LS2", 1, [("S2", 3)])
    n.sig("Demux probe", 5, [("Scope", 1)])
    n.sig("Demux probe", 2, [("Scope", 2)])
    n.sig("Controller", 10, [("Demux status", 1), ("status", 1)])
    n.sig("Demux status", 2, [("Scope", 3)])
    n.sig("Demux status", 4, [("Scope", 4)])

    body = n.text()
    body += annotation("ENEL 585 Project B, Group 8: switched station model "
                       "(same controller code as the firmware)", (480, 15))
    body += note("Sequence: enable at 20 ms (soft start to 25 Vrms, 25 ohm = OP1); load step to "
                 "12.5 ohm at 0.30 s;\nreference step 25 -> 30 Vrms at 0.50 s (OP2) and back at "
                 "0.70 s; load step back to 25 ohm at 0.85 s.\nSet protection_test = 1 in the "
                 "init commands to see the inductor-current trip at the load step.", (480, 780))
    h = header("ENEL585_F26_ProjectB_G8_Station", INIT_SIM, "1.1", "1e-5", "1e-4", "Ts",
               ["Kp_amp", "Ki_amp"])
    return h + "\n" + schematic(body)


def main():
    for fname, text in (("ENEL585_F26_ProjectB_G8_Firmware.plecs", firmware()),
                        ("ENEL585_F26_ProjectB_G8_Station.plecs", station())):
        (OUT / fname).write_text(text)
        print("wrote", OUT / fname, len(text), "bytes")


if __name__ == "__main__":
    main()
