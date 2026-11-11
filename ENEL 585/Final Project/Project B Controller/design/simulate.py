"""
Switched simulation of the Project B station running the real controller code.

The controller is ../firmware/pb_ctrl_core.c, compiled and called through ctypes, so the
simulation tests the same C that goes into the PLECS C-Script and onto the LaunchPad.

Plant (exact piecewise-linear integration between switching events):
  ITECH (CV source behind 0.05 ohm) -> 1.1 mF DC link -> two-leg bridge with dead time and
  device drops -> 2 x 47 uH (series) -> 2 x 62 uF (series, 31 uF) -> load R between the taps.
Sensing: probe + interface-board filter H(s) on all four channels, 1.62 V offset,
  12-bit ADC sampled at the carrier valley. Duty computed from sample k is loaded at the next
  valley (1.5 Ts total delay, Lecture 11).
Unipolar SPWM, symmetric carrier at fsw, top switch on while the carrier is below the duty.

Run:  python3 simulate.py            (all scenarios, ~1 min)
Writes ../figures/sim_*.png and results_sim.json.
"""
import ctypes
import json
import math
import os
import subprocess
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import params as P

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.join(HERE, "..", "firmware")
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)

# device model (SKM50GB12T4 order of magnitude): two devices always in the current path
V0_DEV = 0.8       # V per device
R_DEV = 0.025      # ohm per device
R_ITECH = 0.05     # ohm, as in the HIL model


# ------------------------------------------------------------------ controller (C via ctypes)
class Controller:
    def __init__(self):
        so = os.path.join(FW, "libpbctrl.so")
        src = [os.path.join(FW, "pb_ctrl_test.c"), os.path.join(FW, "pb_ctrl_core.c")]
        if not os.path.exists(so) or any(os.path.getmtime(s) > os.path.getmtime(so) for s in src):
            subprocess.check_call(["gcc", "-O2", "-Wall", "-shared", "-fPIC", "-o", so,
                                   src[0], "-lm"])
        self.lib = ctypes.CDLL(so)
        self.lib.t_init.argtypes = [ctypes.POINTER(ctypes.c_double)]
        self.lib.t_step.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
        self.inb = (ctypes.c_double * 12)()
        self.outb = (ctypes.c_double * 12)()

    def init(self, **over):
        p = [P.MF, P.TS, P.V_SCALE, P.V_OFFSET, P.I_SCALE, P.I_OFFSET, P.TRIP_VO, P.TRIP_IL,
             P.TRIP_IO, P.TRIP_VDC_HI, P.TRIP_VDC_LO, P.VDC_START_MIN, P.M_MAX, P.X_MAX, P.RAMP_RATE]
        names = ["N", "Ts", "v_scale", "v_offset", "i_scale", "i_offset", "trip_vo", "trip_il",
                 "trip_io", "trip_vdc_hi", "trip_vdc_lo", "vdc_start_min", "m_max", "x_max", "ramp_rate"]
        for k, v in over.items():
            p[names.index(k)] = v
        arr = (ctypes.c_double * 15)(*p)
        self.lib.t_init(arr)

    def step(self, vpins, enable, vref_rms, kp, ki, ff, trips=(0.0, 0.0, 0.0)):
        for i, v in enumerate(list(vpins) + [enable, vref_rms, kp, ki, ff] + list(trips)):
            self.inb[i] = v
        self.lib.t_step(self.inb, self.outb)
        return list(self.outb)


# ------------------------------------------------------------------ plant model
class Plant:
    """x = [iL, vo, vdc, z_vdc(.), z_il(.), z_vo(.), z_io(.)]; sensor filters per channel."""

    def __init__(self, bench=True, L=P.L, Vset=P.VDC):
        self.bench = bench
        self.L = L
        self.Vset = Vset
        wz, wp1, wp2 = 2 * math.pi * P.F_Z, 2 * math.pi * P.F_P1, 2 * math.pi * P.F_P2
        if bench:
            # (1+s/wz)/((1+s/wp1)(1+s/wp2)) = (b1 s + b0)/(s^2 + a1 s + a0)
            a0, a1 = wp1 * wp2, wp1 + wp2
            b0, b1 = wp1 * wp2, wp1 * wp2 / wz
            self.fA = np.array([[0, 1], [-a0, -a1]])
            self.fB = np.array([0, 1.0])
            self.fC = np.array([b0, b1])
            self.fD = 0.0
        else:
            # (1+s/wz)/(1+s/wp2) = D + C/(s+wp2)
            D = wp2 / wz
            self.fA = np.array([[-wp2]])
            self.fB = np.array([1.0])
            self.fC = np.array([wp2 * (1 - D)])
            self.fD = D
        self.nf = self.fA.shape[0]
        self.itech_on = True
        self.n = 3 + 4 * self.nf
        self.cache = {}

    # sensor input rows: which plant quantity feeds each channel (as a row on x[0:3]),
    # io depends on R
    def _sensor_inputs(self, R):
        rows = np.zeros((4, 3))
        rows[0, 2] = 1.0          # vdc
        rows[1, 0] = 1.0          # iL
        rows[2, 1] = 1.0          # vo
        rows[3, 1] = 1.0 / R      # io = vo / R
        return rows

    def matrices(self, R, sigma, itech_on=True, l_open=False):
        key = (R, round(sigma, 9), itech_on, l_open)
        if key in self.cache:
            return self.cache[key]
        n, nf = self.n, self.nf
        A = np.zeros((n, n))
        B = np.zeros((n, 2))       # inputs: [Vset, vdrop_signed]
        Rl = P.R_L + 2 * R_DEV
        # L diL/dt = sigma vdc - vo - Rl iL - vdrop
        A[0, 0] = -Rl / self.L
        A[0, 1] = -1 / self.L
        A[0, 2] = sigma / self.L
        B[0, 1] = -1 / self.L
        # C dvo/dt = iL - vo/R
        A[1, 0] = 1 / P.C
        A[1, 1] = -1 / (R * P.C)
        # Cdc dvdc/dt = (Vset - vdc)/Rit - sigma iL
        if itech_on:
            A[2, 2] = -1 / (R_ITECH * P.C_DC)
            B[2, 0] = 1 / (R_ITECH * P.C_DC)
        else:
            A[2, 2] = -1 / (44e3 * P.C_DC)     # output contactor open: balancing resistors only
        A[2, 0] = -sigma / P.C_DC
        if l_open:
            # all gates off and the diodes blocking: the inductor current stays at zero
            A[0, :] = 0.0
            B[0, :] = 0.0
        rows = self._sensor_inputs(R)
        for ch in range(4):
            i0 = 3 + ch * nf
            A[i0:i0 + nf, i0:i0 + nf] = self.fA
            A[i0:i0 + nf, 0:3] += np.outer(self.fB, rows[ch])
        w, V = np.linalg.eig(A)
        Vi = np.linalg.inv(V)
        VB = Vi @ B
        self.cache[key] = (A, B, w, V, Vi, VB)
        return self.cache[key]

    def propagate(self, x, R, sigma, u, h, l_open=False):
        A, B, w, V, Vi, VB = self.matrices(R, sigma, self.itech_on, l_open)
        e = np.exp(w * h)
        # (e^{wh}-1)/w with care for tiny w
        g = np.where(np.abs(w * h) > 1e-12, (e - 1) / np.where(w == 0, 1, w), h)
        y = Vi @ x
        xn = V @ (e * y + g * (VB @ u))
        return xn.real

    def sensor_bnc(self, x, R):
        """Filtered BNC-referred physical value for each channel (before the probe scaling)."""
        rows = self._sensor_inputs(R)
        out = np.zeros(4)
        for ch in range(4):
            i0 = 3 + ch * self.nf
            out[ch] = self.fC @ x[i0:i0 + self.nf] + self.fD * (rows[ch] @ x[0:3])
        return out


def pin_voltages(phys):
    """phys = [vdc, iL, vo, io] filtered; returns quantized ADC pin voltages."""
    vdc, il, vo, io = phys
    pins = np.array([
        P.V_ADC_OFFSET + P.K_VCH * vdc / P.V_PROBE_ATTEN,
        P.V_ADC_OFFSET + P.K_ICH * il * P.I_PROBE_V_PER_A,
        P.V_ADC_OFFSET + P.K_VCH * vo / P.V_PROBE_ATTEN,
        P.V_ADC_OFFSET + P.K_ICH * io * P.I_PROBE_V_PER_A,
    ])
    pins = np.clip(pins, 0, P.ADC_FULL_SCALE)
    lsb = P.ADC_FULL_SCALE / 4095
    return np.round(pins / lsb) * lsb


# ------------------------------------------------------------------ PWM events in one period
def leg_events(d, Ts, td):
    """Return list of (t_start, state) for one leg over [0, Ts): state 1 top on, 0 bottom on,
    -1 dead (both off). Pulse centred on the valley (t = 0 and t = Ts)."""
    if d <= 0:
        return [(0.0, 0)]
    if d >= 1:
        return [(0.0, 1)]
    a1 = d * Ts / 2
    a2 = Ts - d * Ts / 2
    ev = [(0.0, 1), (a1, -1)]
    if a1 + td < a2:
        ev.append((a1 + td, 0))
    ev.append((a2, -1))
    if a2 + td < Ts:
        ev.append((a2 + td, 1))
    return ev


def leg_state_at(ev, t):
    s = ev[0][1]
    for t0, st in ev:
        if t0 <= t + 1e-15:
            s = st
        else:
            break
    return s


# ------------------------------------------------------------------ simulation
def simulate(t_end, schedule, bench=True, L=P.L, averaged=False, deadtime=P.DEADTIME_EFFECTIVE,
             kp=P.KP, ki=P.KI, ff=P.FF_GAIN, Vset=P.VDC, record_fine=True, ctrl_over=None,
             vo_sign=1.0):
    """schedule(t) -> dict(R=..., vref_rms=..., enable=..., Vset=...) evaluated each period."""
    plant = Plant(bench=bench, L=L, Vset=Vset)
    ctl = Controller()
    ctl.init(**(ctrl_over or {}))
    Ts = P.TS
    x = np.zeros(plant.n)
    x[2] = Vset
    # pre-charge the vdc sensor filter to steady state
    for ch_i, val in [(0, Vset)]:
        i0 = 3 + ch_i * plant.nf
        # steady state of filter for constant input val: z = -fA^-1 fB val
        x[i0:i0 + plant.nf] = -np.linalg.solve(plant.fA, plant.fB) * val
    d_now = (0.5, 0.5, 0.0)          # duties applied in the current period, pwm_en
    n_per = int(round(t_end / Ts))
    rec = {k: np.zeros(n_per) for k in ["t", "vo_s", "iL_s", "vdc", "dA", "m", "amp", "fault",
                                        "x_amp", "vref", "R", "pwm", "vo_meas", "il_meas", "io_meas",
                                        "vdc_meas", "idc"]}
    fine_t, fine_vo, fine_il = [], [], []
    for k in range(n_per):
        t0 = k * Ts
        sch = schedule(t0)
        R = sch["R"]
        plant.Vset = sch.get("Vset", Vset)
        plant.itech_on = sch.get("itech_on", True)
        # ---- sample at the valley
        bnc = plant.sensor_bnc(x, R)
        pins = pin_voltages(bnc)
        if vo_sign < 0:
            pins[2] = 2 * P.V_ADC_OFFSET - pins[2]
        out = ctl.step(pins, sch.get("enable", 1.0), sch["vref_rms"], kp, ki, ff,
                       sch.get("trips", (0.0, 0.0, 0.0)))
        # ---- integrate this period with the duty computed one period earlier
        dA, dB, en = d_now
        u_vset = plant.Vset
        idc_acc = 0.0
        if averaged:
            m = (dA - dB) if en > 0.5 else 0.0
            sigma = m
            vdrop = 2 * V0_DEV * np.sign(x[0]) if en > 0.5 else 0.0
            xn = plant.propagate(x, R, sigma, np.array([u_vset, vdrop]), Ts)
            idc_acc = sigma * 0.5 * (x[0] + xn[0]) * Ts
            if record_fine:
                fine_t.append(t0)
                fine_vo.append(x[1])
                fine_il.append(x[0])
            x = xn
        else:
            if en > 0.5:
                evA = leg_events(dA, Ts, deadtime)
                evB = leg_events(dB, Ts, deadtime)
                times = sorted(set([e[0] for e in evA] + [e[0] for e in evB] + [Ts]))
            else:
                times = [0.0, Ts]
            for i in range(len(times) - 1):
                ta, tb = times[i], times[i + 1]
                if tb - ta <= 0:
                    continue
                if en > 0.5:
                    sA = leg_state_at(evA, ta)
                    sB = leg_state_at(evB, ta)
                else:
                    sA = sB = -1
                t_cur = ta
                splits = 0
                while tb - t_cur > 1e-12:
                    h = tb - t_cur
                    iL = x[0]
                    sgn = 1.0 if iL > 0 else -1.0
                    if en > 0.5:
                        # dead time: the diode set by the current direction conducts
                        vA = sA if sA >= 0 else (1 if sgn < 0 else 0)
                        # leg B carries -iL out of its midpoint
                        vB = sB if sB >= 0 else (1 if sgn > 0 else 0)
                        sigma = float(vA - vB)
                        vdrop = 2 * V0_DEV * sgn
                    elif abs(iL) > 1e-6:
                        # gates off, current still flowing: freewheeling diodes put -Vdc
                        # (iL > 0) or +Vdc (iL < 0) across the filter until iL reaches zero
                        sigma = -sgn
                        vdrop = 2 * V0_DEV * sgn
                    else:
                        sigma = 0.0
                        vdrop = 0.0
                    l_open = en <= 0.5 and abs(iL) <= 1e-6
                    u = np.array([u_vset, vdrop])
                    xn = plant.propagate(x, R, sigma, u, h, l_open)
                    if l_open:
                        xn[0] = 0.0
                    if not l_open and splits < 6 and np.sign(xn[0]) != sgn and abs(x[0]) > 1e-9:
                        # the current crosses zero inside the segment: stop at the crossing,
                        # so the device drop and the dead-time diode follow the new direction
                        frac = x[0] / (x[0] - xn[0])
                        hz = max(min(frac * h, h), 1e-10)
                        for _ in range(2):    # refine (iL is nearly linear here)
                            xz = plant.propagate(x, R, sigma, u, hz)
                            A, B = plant.matrices(R, sigma, plant.itech_on)[0:2]
                            didt = (A @ xz + B @ u)[0]
                            if didt != 0:
                                hz = min(max(hz - xz[0] / didt, 1e-10), h)
                        xn = plant.propagate(x, R, sigma, u, hz)
                        xn[0] = 0.0 if abs(xn[0]) < 1e-6 else xn[0]
                        h = hz
                        splits += 1
                    idc_acc += sigma * 0.5 * (x[0] + xn[0]) * h
                    if record_fine:
                        fine_t.append(t0 + t_cur)
                        fine_vo.append(x[1])
                        fine_il.append(x[0])
                    x = xn
                    t_cur += h
                    if abs(x[0]) < 1e-6 and en > 0.5:
                        # nudge the sign so the next sub-segment uses the new direction
                        x[0] = -1e-7 * sgn
                    elif abs(x[0]) < 1e-6:
                        x[0] = 0.0
        d_now = (out[0], out[1], out[2])
        rec["t"][k] = t0
        rec["vo_s"][k] = x[1]
        rec["iL_s"][k] = x[0]
        rec["vdc"][k] = x[2]
        rec["dA"][k] = out[0]
        rec["pwm"][k] = out[2]
        rec["fault"][k] = out[3]
        rec["amp"][k] = out[4]
        rec["m"][k] = out[5]
        rec["x_amp"][k] = out[6]
        rec["vref"][k] = out[7]
        rec["vdc_meas"][k] = out[8]
        rec["il_meas"][k] = out[9]
        rec["vo_meas"][k] = out[10]
        rec["io_meas"][k] = out[11]
        rec["R"][k] = R
        rec["idc"][k] = idc_acc / Ts
    rec["fine_t"] = np.array(fine_t)
    rec["fine_vo"] = np.array(fine_vo)
    rec["fine_il"] = np.array(fine_il)
    return rec


# ------------------------------------------------------------------ metrics
def window(rec, t_a, t_b, key_t="fine_t"):
    t = rec[key_t]
    return (t >= t_a) & (t < t_b)


def resample(rec, t_a, n_cycles, key, fs=P.FSW * 20):
    T = n_cycles / P.F1_EXACT
    tt = t_a + np.arange(int(T * fs)) / fs
    y = np.interp(tt, rec["fine_t"], rec[key])
    return tt, y


def fundamental(rec, t_a, n_cycles, key):
    tt, y = resample(rec, t_a, n_cycles, key)
    w = 2 * math.pi * P.F1_EXACT
    a = 2 * np.mean(y * np.sin(w * tt))
    b = 2 * np.mean(y * np.cos(w * tt))
    return math.hypot(a, b), math.degrees(math.atan2(b, a))


def steady_metrics(rec, t_a, n_cycles=6):
    tt, vo = resample(rec, t_a, n_cycles, "fine_vo")
    _, il = resample(rec, t_a, n_cycles, "fine_il")
    w = 2 * math.pi * P.F1_EXACT
    V1, _ = fundamental(rec, t_a, n_cycles, "fine_vo")
    # THD up to 50th harmonic
    N = len(vo)
    spec = np.abs(np.fft.rfft(vo)) * 2 / N
    h1 = n_cycles
    harm = [spec[h1 * h] for h in range(2, 51) if h1 * h < len(spec)]
    thd = math.sqrt(sum(h * h for h in harm)) / spec[h1]
    sel = (rec["t"] >= t_a) & (rec["t"] < t_a + n_cycles / P.F1_EXACT)
    Pin = np.mean(rec["vdc"][sel] * rec["idc"][sel])
    R = rec["R"][sel][0]
    Pout = np.mean(vo ** 2) / R
    # ripple: within each carrier period, max-min of fine samples
    m = window(rec, t_a, t_a + n_cycles / P.F1_EXACT)
    ft, fil = rec["fine_t"][m], rec["fine_il"][m]
    idx = np.floor((ft - ft[0]) / P.TS).astype(int)
    rip = np.array([fil[idx == j].max() - fil[idx == j].min() for j in np.unique(idx) if (idx == j).sum() > 1])
    return dict(Vo_rms=float(np.sqrt(np.mean(vo ** 2))), Vo1_rms=V1 / math.sqrt(2), THD_vo=float(thd),
                IL_rms=float(np.sqrt(np.mean(il ** 2))), IL_peak=float(np.max(np.abs(rec["fine_il"][m]))),
                ripple_pp_max=float(rip.max()), Pin=float(Pin), Pout=float(Pout),
                Idc=float(np.mean(rec["idc"][sel])), m_peak=float(np.max(np.abs(rec["m"][sel]))),
                x_amp=float(np.mean(rec["x_amp"][sel])), Vdc=float(np.mean(rec["vdc"][sel])))


def envelope(rec, t_a, t_b, key="fine_vo"):
    """Per-cycle fundamental amplitude (V peak) between t_a and t_b."""
    T1 = 1 / P.F1_EXACT
    n = int((t_b - t_a) / T1)
    tc, amp = [], []
    for i in range(n):
        a, _ = fundamental(rec, t_a + i * T1, 1, key)
        tc.append(t_a + (i + 0.5) * T1)
        amp.append(a)
    return np.array(tc), np.array(amp)


# ------------------------------------------------------------------ scenarios
def run_all(quick=False):
    T1 = 1 / P.F1_EXACT
    results = {}
    t_ss = 0.60     # soft start to 42 V takes 0.42 s; steady from 0.6 s

    # 1) operating points, bench and HIL sensing
    for name, op in P.OPERATING_POINTS.items():
        for bench in (True, False):
            sched = lambda t, op=op: dict(R=op["R"], vref_rms=op["Vrms"], enable=1.0)
            rec = simulate(t_ss + 8 * T1, sched, bench=bench)
            met = steady_metrics(rec, t_ss + T1, 6)
            met["fault"] = int(rec["fault"].max())
            results[f"{name}_{'bench' if bench else 'HIL'}"] = met
            if bench:
                fig, ax = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
                m = window(rec, t_ss, t_ss + 3 * T1)
                ax[0].plot(rec["fine_t"][m] * 1e3, rec["fine_vo"][m], lw=0.8, label="vo")
                sel = (rec["t"] >= t_ss) & (rec["t"] < t_ss + 3 * T1)
                ax[0].plot(rec["t"][sel] * 1e3, rec["vref"][sel], "--", lw=0.8, label="vref")
                ax[0].set_ylabel("V")
                ax[0].legend(fontsize=8)
                ax[1].plot(rec["fine_t"][m] * 1e3, rec["fine_il"][m], lw=0.5, label="iL (switched)")
                ax[1].plot(rec["t"][sel] * 1e3, rec["il_meas"][sel], lw=1, label="iL as sampled by the ADC")
                ax[1].set_ylabel("A")
                ax[1].legend(fontsize=8)
                ax[2].plot(rec["t"][sel] * 1e3, rec["m"][sel], lw=0.8)
                ax[2].set_ylabel("m")
                ax[2].set_xlabel("t (ms)")
                for a in ax:
                    a.grid(alpha=0.3)
                fig.suptitle(f"{name}: {op['Vrms']} V rms, R = {op['R']} ohm, Vdc = {P.VDC} V "
                             f"(bench sensing)   Vo1 = {met['Vo1_rms']:.2f} V rms, THD {met['THD_vo']*100:.2f} %")
                fig.tight_layout()
                fig.savefig(os.path.join(FIG, f"sim_{name}.png"), dpi=150)
                plt.close(fig)

    # 2) load step 25 -> 12.5 ohm at 30 V rms, then back
    ls = P.LOAD_STEP
    t1, t2 = t_ss + 5.3 * T1, t_ss + 15.7 * T1        # steps at arbitrary phase
    def sched_ls(t):
        R = ls["R_to"] if t1 <= t < t2 else ls["R_from"]
        return dict(R=R, vref_rms=ls["Vrms"], enable=1.0)
    for bench in ((True, False) if not quick else (True,)):
        rec = simulate(t_ss + 26 * T1, sched_ls, bench=bench)
        recav = simulate(t_ss + 26 * T1, sched_ls, bench=bench, averaged=True) if bench else None
        tc, amp = envelope(rec, t_ss, t_ss + 26 * T1)
        key = f"load_step_{'bench' if bench else 'HIL'}"
        # deviation and recovery
        pre = amp[(tc > t_ss) & (tc < t1)].mean()
        after = amp[(tc > t1) & (tc < t2)]
        results[key] = dict(amp_before=float(pre), amp_min_after=float(after.min()),
                            dev_pct=float((after.min() - pre) / pre * 100),
                            amp_end=float(after[-3:].mean()), fault=int(rec["fault"].max()),
                            vo_peak_abs=float(np.abs(rec["fine_vo"][window(rec, t1, t2)]).max()),
                            il_peak_abs=float(np.abs(rec["fine_il"][window(rec, t_ss, t_ss + 26 * T1)]).max()))
        if bench:
            fig, ax = plt.subplots(3, 1, figsize=(10, 8))
            m = window(rec, t1 - 2 * T1, t1 + 4 * T1)
            ax[0].plot(rec["fine_t"][m] * 1e3, rec["fine_vo"][m], lw=0.8, label="vo switched")
            ma = window(recav, t1 - 2 * T1, t1 + 4 * T1)
            ax[0].plot(recav["fine_t"][ma] * 1e3, recav["fine_vo"][ma], lw=0.8, ls="--", label="vo averaged model")
            ax[0].axvline(t1 * 1e3, color="k", lw=0.6)
            ax[0].set_ylabel("vo (V)")
            ax[0].legend(fontsize=8)
            ax[1].plot(rec["fine_t"][m] * 1e3, rec["fine_il"][m], lw=0.5, label="iL switched")
            ax[1].axvline(t1 * 1e3, color="k", lw=0.6)
            ax[1].set_ylabel("iL (A)")
            ax[1].set_xlabel("t (ms)")
            ax[1].legend(fontsize=8)
            tca, ampa = envelope(recav, t_ss, t_ss + 26 * T1)
            ax[2].plot(tc * 1e3, amp, "o-", ms=3, label="switched")
            ax[2].plot(tca * 1e3, ampa, "s--", ms=3, label="averaged")
            ax[2].axvline(t1 * 1e3, color="k", lw=0.6)
            ax[2].axvline(t2 * 1e3, color="k", lw=0.6)
            ax[2].set_ylabel("vo fundamental, V peak (per cycle)")
            ax[2].set_xlabel("t (ms)")
            ax[2].legend(fontsize=8)
            for a in ax:
                a.grid(alpha=0.3)
            fig.suptitle(f"Load step {ls['R_from']} -> {ls['R_to']} ohm at {ls['Vrms']} V rms (and back), bench sensing")
            fig.tight_layout()
            fig.savefig(os.path.join(FIG, "sim_load_step.png"), dpi=150)
            plt.close(fig)

    # 3) reference step 25 -> 30 V rms at 25 ohm, then back; with and without feedforward
    rs = P.REF_STEP
    t1, t2 = t_ss + 4.2 * T1, t_ss + 16.6 * T1
    def sched_rs(t):
        v = rs["V_to"] if t1 <= t < t2 else rs["V_from"]
        return dict(R=rs["R"], vref_rms=v, enable=1.0)
    for ffv in (1.0, 0.0):
        rec = simulate(t_ss + 28 * T1, sched_rs, bench=True, ff=ffv)
        recav = simulate(t_ss + 28 * T1, sched_rs, bench=True, ff=ffv, averaged=True)
        tc, amp = envelope(rec, t_ss, t_ss + 28 * T1)
        tca, ampa = envelope(recav, t_ss, t_ss + 28 * T1)
        target = rs["V_to"] * math.sqrt(2)
        after = (tc > t1) & (tc < t2)
        a_after = amp[after]
        # cycles to within 2 % of the new target
        within = np.where(np.abs(a_after - target) / target < 0.02)[0]
        n_settle = int(within[0]) + 1 if len(within) else -1
        key = f"ref_step_ff{int(ffv)}"
        results[key] = dict(target_pk=target, first_cycle_pk=float(a_after[0]),
                            cycles_to_2pct=n_settle, overshoot_pct=float((a_after.max() - target) / target * 100),
                            vo_peak_abs=float(np.abs(rec["fine_vo"][window(rec, t1, t2)]).max()),
                            fault=int(rec["fault"].max()))
        fig, ax = plt.subplots(2, 1, figsize=(10, 6.5))
        m = window(rec, t1 - 2 * T1, t1 + 6 * T1)
        ax[0].plot(rec["fine_t"][m] * 1e3, rec["fine_vo"][m], lw=0.8, label="vo switched")
        sel = (rec["t"] >= t1 - 2 * T1) & (rec["t"] < t1 + 6 * T1)
        ax[0].plot(rec["t"][sel] * 1e3, rec["vref"][sel], "--", lw=0.8, label="vref")
        ax[0].axvline(t1 * 1e3, color="k", lw=0.6)
        ax[0].set_ylabel("V")
        ax[0].legend(fontsize=8)
        ax[1].plot(tc * 1e3, amp, "o-", ms=3, label="switched")
        ax[1].plot(tca * 1e3, ampa, "s--", ms=3, label="averaged")
        if ffv == 0.0:
            # linear prediction: first-order envelope with tau from design.py (bench, R=25)
            import design as D
            ev = D.envelope_prediction(P.KI, True, rs["R"])
            tp = tc[after]
            a0 = rs["V_from"] * math.sqrt(2)
            tstep = t1 + (T1 - ((t1 - t_ss) % T1))   # applied at the next zero crossing
            pred = target + (a0 - target) * np.exp(-np.clip(tp - tstep, 0, None) / ev["tau_env"])
            ax[1].plot(tp * 1e3, pred, "k:", label=f"prediction, tau = {ev['tau_env']*1e3:.1f} ms")
            results[key]["tau_pred_ms"] = ev["tau_env"] * 1e3
        ax[1].axvline(t1 * 1e3, color="k", lw=0.6)
        ax[1].axvline(t2 * 1e3, color="k", lw=0.6)
        ax[1].set_ylabel("vo fundamental, V peak")
        ax[1].set_xlabel("t (ms)")
        ax[1].legend(fontsize=8)
        for a in ax:
            a.grid(alpha=0.3)
        fig.suptitle(f"Reference step {rs['V_from']} -> {rs['V_to']} V rms at {rs['R']} ohm, "
                     f"feedforward {'on' if ffv else 'off (feedback only)'}")
        fig.tight_layout()
        fig.savefig(os.path.join(FIG, f"sim_ref_step_ff{int(ffv)}.png"), dpi=150)
        plt.close(fig)

    # 4) protection demos for the HIL checklist (HIL sensing)
    def trip_run(name, sched, t_end, **kw):
        rec = simulate(t_end, sched, bench=False, **kw)
        k = int(np.argmax(rec["fault"] > 0)) if rec["fault"].max() > 0 else -1
        r = dict(fault=int(rec["fault"].max()), t_trip=float(rec["t"][k]) if k >= 0 else None,
                 vdc_at_trip=float(rec["vdc"][k]) if k >= 0 else None,
                 pwm_after=float(rec["pwm"][-1]))
        results[name] = r
        return rec, k

    t_ev = t_ss + 3.3 * T1
    # (a) output OV: lower Trip_vo to 40 V while running at 30 V rms (42.4 V peak)
    trip_run("trip_ov_test", lambda t: dict(R=25.0, vref_rms=30.0,
             trips=(40.0, 0, 0) if t >= t_ev else (0, 0, 0)), t_ev + 0.05)
    # (b) inductor OC: lower Trip_iL to 1.2 A at OP1 (iL fundamental peak 1.45 A)
    trip_run("trip_il_test", lambda t: dict(R=25.0, vref_rms=25.0,
             trips=(0, 1.2, 0) if t >= t_ev else (0, 0, 0)), t_ev + 0.05)
    # (c) DC-link OV: ITECH set point raised to 58.5 V
    trip_run("trip_vdc_ov", lambda t: dict(R=25.0, vref_rms=25.0,
             Vset=58.5 if t >= t_ev else P.VDC), t_ev + 0.05)
    # (d) ITECH output switched off while running: DC link collapses -> UV trip
    rec, k = trip_run("trip_uv_itech_off", lambda t: dict(R=25.0, vref_rms=25.0,
                      itech_on=t < t_ev), t_ev + 0.15)
    if k >= 0:
        results["trip_uv_itech_off"]["t_after_off_ms"] = float((rec["t"][k] - t_ev) * 1e3)
    fig, ax = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    sel = rec["t"] > t_ev - 0.03
    ax[0].plot(rec["t"][sel] * 1e3, rec["vdc"][sel], label="vdc")
    ax[0].plot(rec["t"][sel] * 1e3, rec["vo_s"][sel], lw=0.6, label="vo")
    ax[0].axvline(t_ev * 1e3, color="k", lw=0.6)
    ax[0].legend(fontsize=8)
    ax[0].set_ylabel("V")
    ax[1].plot(rec["t"][sel] * 1e3, rec["fault"][sel], label="fault bits")
    ax[1].plot(rec["t"][sel] * 1e3, rec["pwm"][sel], label="pwm_en")
    ax[1].legend(fontsize=8)
    ax[1].set_xlabel("t (ms)")
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle("Protection: ITECH output switched off while running at OP1 (undervoltage trip at 35 V)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "sim_trip_uv.png"), dpi=150)
    plt.close(fig)
    # (e) vo probe polarity reversed at start-up
    rec, k = trip_run("trip_polarity", lambda t: dict(R=25.0, vref_rms=25.0), 0.3, vo_sign=-1.0)
    results["trip_polarity"]["vo_max_before_trip"] = float(np.abs(rec["vo_s"][:max(k, 1)]).max())

    # 5) robustness: L -20 % and +20 %, light load 250 ohm, HIL sensing (hardest case)
    for Lk in (0.8, 1.2):
        sched = lambda t: dict(R=250.0, vref_rms=25.0, enable=1.0)
        rec = simulate(t_ss + 6 * T1, sched, bench=False, L=Lk * P.L)
        met = steady_metrics(rec, t_ss, 5)
        met["fault"] = int(rec["fault"].max())
        results[f"robust_HIL_L{int(Lk*100)}_R250"] = met

    with open(os.path.join(HERE, "results_sim.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    for k, v in results.items():
        print(k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})
    return results


if __name__ == "__main__":
    run_all(quick="--quick" in sys.argv)
