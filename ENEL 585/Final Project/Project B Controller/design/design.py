"""
Control design and hardware analysis for Project B.

Run:  python3 design.py
Writes: ../figures/*.png and results_design.json (numbers quoted in docs/).

Method (Lecture 11):
  plant      Gp(s) = vo / v_inv for the LC filter with resistive load
  sensing    H(s)  = interface-board filter (bench: 2 poles + zero; HIL model: 1 pole + zero)
  delay      e^{-s tau}, tau = 1.5 Ts (sample at the valley, load at the next valley)
  controller Gc(s) = Kp + 2 Ki s / (s^2 + w1^2), plus reference feedforward and m = v*/v_dc
  loop       T(s)  = Gc Gp H e^{-s tau}   (feedforward is outside the loop)

The LC resonance (2.95 kHz) is above fs/6 = 1.67 kHz and the sensing filter adds about
-86 deg there, so it cannot be actively damped from these measurements. As in the course's
Cuk example, Kp is limited so that the resonant peak of |T| stays 6 dB under 1 at the worst
corner, and the resonant term supplies the gain at 60 Hz.
"""
import json
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import params as P

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)

W1 = P.w1()
TWO_PI = 2 * math.pi


# ------------------------------------------------------------------ transfer functions
def Gp(s, R, L=P.L):
    """vo / v_inv. R=None means no load (bleeders only, ignored)."""
    if R is None:
        return 1.0 / (s * s * L * P.C + s * P.R_L * P.C + 1.0)
    return R / (s * s * L * P.C * R + s * (L + P.R_L * R * P.C) + R + P.R_L)


def H(s, bench=True):
    h = (1 + s / (TWO_PI * P.F_Z)) / (1 + s / (TWO_PI * P.F_P2))
    if bench:
        h = h / (1 + s / (TWO_PI * P.F_P1))
    return h


def Gd(s):
    return np.exp(-s * P.TAU)


def Gc(s, Kp=P.KP, Ki=P.KI):
    return Kp + 2 * Ki * s / (s * s + W1 * W1)


def loop(s, R, L=P.L, bench=True, Kp=P.KP, Ki=P.KI):
    return Gc(s, Kp, Ki) * Gp(s, R, L) * H(s, bench) * Gd(s)


# ------------------------------------------------------------------ margins
def margins(f, T):
    """All |T| = 1 crossings with their phase margins, plus the high-frequency resonant peak."""
    mag = np.abs(T)
    ph = np.unwrap(np.angle(T))
    out = []
    idx = np.where(np.diff(np.sign(mag - 1.0)) != 0)[0]
    for i in idx:
        # linear interpolation in log f
        a = (1.0 - mag[i]) / (mag[i + 1] - mag[i])
        fc = 10 ** (np.log10(f[i]) + a * (np.log10(f[i + 1]) - np.log10(f[i])))
        phc = ph[i] + a * (ph[i + 1] - ph[i])
        ang = (math.degrees(phc) + 180) % 360 - 180     # angle of T wrapped into (-180, 180]
        pm = 180 - abs(ang)                              # distance from the -1 point
        out.append(dict(fc=float(fc), pm=float(pm)))
    hf = (f > 1000) & (f < 8000)
    pk_i = np.argmax(mag[hf])
    return out, float(f[hf][pk_i]), float(20 * np.log10(mag[hf][pk_i]))


CORNERS = []
for bench in (True, False):
    for Lk in (1 - P.L_TOL, 1.0, 1 + P.L_TOL):
        for R in (12.5, 25.0, 50.0, 250.0, None):
            CORNERS.append((bench, Lk, R))


def corner_name(bench, Lk, R):
    rs = "open" if R is None else f"{R:g}"
    return f"{'bench' if bench else 'HIL'} L={Lk*P.L*1e6:.0f}uH R={rs}"


def analyse(Kp=P.KP, Ki=P.KI, f=None):
    if f is None:
        f = np.logspace(0, np.log10(20e3), 60000)
    s = 1j * TWO_PI * f
    rows = []
    for bench, Lk, R in CORNERS:
        T = loop(s, R, Lk * P.L, bench, Kp, Ki)
        xs, fpk, pkdb = margins(f, T)
        rows.append(dict(corner=corner_name(bench, Lk, R), bench=bench, L=Lk * P.L,
                         R=R, crossings=xs, f_peak=fpk, peak_dB=pkdb))
    return rows


# ------------------------------------------------------------------ hardware analysis
def hardware():
    w = W1
    out = {}
    te = P.DEADTIME_EFFECTIVE
    v_dt = (4 / math.pi) * 2 * te * P.FSW * P.VDC       # fundamental of the dead-time error (two legs)
    v_dev = 2.0                                          # two conducting devices, ~1 V each at a few A
    out["deadtime_fundamental_V"] = v_dt
    out["device_drop_V"] = v_dev
    ops = {}
    for name, op in P.OPERATING_POINTS.items():
        Vpk = op["Vrms"] * math.sqrt(2)
        R = op["R"]
        Io_pk = Vpk / R
        Ic_pk = w * P.C * Vpk
        IL_pk_fund = math.hypot(Io_pk, Ic_pk)
        IL_rms_fund = IL_pk_fund / math.sqrt(2)
        # inverter fundamental needed (resistive load: drops add almost in phase)
        Vinv = abs(Vpk * (1 - w * w * P.L * P.C + 1j * w * P.L / R + P.R_L / R)) + v_dt + v_dev
        m50 = Vinv / 50.0
        m55 = Vinv / P.VDC
        # unipolar ripple: worst instant when |vo| = Vdc/2 if reached, else at the peak
        def ripple_pp(v):
            d = abs(v) / P.VDC
            return (P.VDC - abs(v)) * d / (2 * P.FSW) / P.L
        th = np.linspace(0, math.pi, 2001)
        rip = np.array([ripple_pp(Vpk * math.sin(t)) for t in th])
        dI_pp_max = float(rip.max())
        # rms ripple ~ pp/sqrt(12) averaged over the cycle
        rip_rms = float(np.sqrt(np.mean(rip ** 2) / 12))
        IL_rms = math.hypot(IL_rms_fund, rip_rms)
        IL_peak = IL_pk_fund + dI_pp_max / 2
        P_out = op["Vrms"] ** 2 / R
        ops[name] = dict(
            Vrms=op["Vrms"], Vpk=Vpk, R=R, P=P_out,
            Io_rms=op["Vrms"] / R, Ic_rms=Ic_pk / math.sqrt(2),
            IL_rms=IL_rms, IL_peak=IL_peak, ripple_pp_max=dI_pp_max,
            Vinv_needed=Vinv, m_at_50V=m50, m_at_55V=m55,
            Idc_est=P_out / 0.85 / P.VDC,
            margin_IL_rms=1 - IL_rms / P.I_RATED_L,
            margin_IL_peak_sat=1 - IL_peak / P.I_SAT_L,
            margin_m=1 - m55 / P.M_MAX,
            margin_trip_vo=1 - Vpk / P.TRIP_VO,
            margin_trip_iL=1 - IL_pk_fund / P.TRIP_IL,
            margin_trip_io=1 - Io_pk / P.TRIP_IO,
        )
    out["operating_points"] = ops
    # envelope: the largest output the DC limit allows, and what the bank then allows
    Vinv_max = P.M_MAX * P.V_ITECH_MAX - (4 / math.pi) * 2 * te * P.FSW * P.V_ITECH_MAX - v_dev
    Vo_max_rms = Vinv_max / math.sqrt(2)
    out["envelope"] = dict(
        Vinv_max_pk=Vinv_max, Vo_max_rms=Vo_max_rms,
        Vo_max_rms_ideal=P.V_ITECH_MAX / math.sqrt(2),
        P_max=Vo_max_rms ** 2 / P.R_BANK_MIN,
        IL_rms_at_Pmax=Vo_max_rms / P.R_BANK_MIN,
        Idc_at_Pmax=Vo_max_rms ** 2 / P.R_BANK_MIN / 0.85 / P.V_ITECH_MAX,
    )
    return out


def adc_table():
    """Pin voltage and ADC code for each channel at the operating extremes and trips."""
    def vpin_v(v):
        return P.V_ADC_OFFSET + P.K_VCH * v / P.V_PROBE_ATTEN

    def vpin_i(i):
        return P.V_ADC_OFFSET + P.K_ICH * i * P.I_PROBE_V_PER_A

    def code(vp):
        return int(round(min(max(vp, 0), P.ADC_FULL_SCALE) / P.ADC_FULL_SCALE * (2 ** P.ADC_BITS - 1)))

    lsb_v = P.ADC_FULL_SCALE / 4095 * P.V_SCALE
    lsb_i = P.ADC_FULL_SCALE / 4095 * P.I_SCALE
    op2 = P.OPERATING_POINTS["OP2"]
    vo_pk = op2["Vrms"] * math.sqrt(2)
    io_pk = vo_pk / op2["R"]
    il_pk = math.hypot(io_pk, W1 * P.C * vo_pk)
    rows = [
        ("v_o", "VProbe1, N2791A 10:1", "ADCINB2", vpin_v, [("OP2 peak", vo_pk), ("trip", P.TRIP_VO)], lsb_v, "V"),
        ("v_dc", "VProbe2, N2791A 10:1", "ADCINA6", vpin_v, [("nominal", P.VDC), ("OV trip", P.TRIP_VDC_HI)], lsb_v, "V"),
        ("i_L1", "CProbe1, 1146B 100 mV/A", "ADCINA10", vpin_i, [("OP2 peak (avg)", il_pk), ("trip", P.TRIP_IL), ("probe limit", 10.0)], lsb_i, "A"),
        ("i_o", "CProbe2, 1146B 100 mV/A", "ADCINB0", vpin_i, [("OP2 peak", io_pk), ("trip", P.TRIP_IO)], lsb_i, "A"),
    ]
    out = []
    for sig, probe, pin, fn, pts, lsb, unit in rows:
        for label, x in pts:
            hi, lo = fn(x), fn(-x)
            out.append(dict(signal=sig, probe=probe, pin=pin, point=label, value=x, unit=unit,
                            v_bnc=(x / P.V_PROBE_ATTEN if unit == "V" else x * P.I_PROBE_V_PER_A),
                            vpin_pos=hi, vpin_neg=lo, code_pos=code(hi), code_neg=code(lo),
                            lsb=lsb))
    return out


# ------------------------------------------------------------------ envelope (equivalent PI) view
def envelope_prediction(Ki=P.KI, bench=True, R=25.0):
    """Near 60 Hz the resonant term acts like an integrator on the 60 Hz envelope.
    Loop seen by the envelope: Ki * P0 / s', P0 = Gp H Gd at w1. Crossover |Ki P0|, PM = 90 + angle(P0)."""
    s1 = 1j * W1
    P0 = Gp(s1, R) * H(s1, bench) * Gd(s1)
    fc_env = Ki * abs(P0) / TWO_PI
    pm_env = 90 + math.degrees(np.angle(P0))
    tau_env = 1 / (Ki * abs(P0))
    return dict(P0_mag=float(abs(P0)), P0_deg=float(math.degrees(np.angle(P0))),
                f_env_crossover=fc_env, pm_env=pm_env, tau_env=tau_env,
                settle_2pct=4 * tau_env, vo_gain_error=float(1 / abs(H(s1, bench)) - 1))


# ------------------------------------------------------------------ figures
def fig_bode(rows_f, f):
    s = 1j * TWO_PI * f
    fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    sel = [(True, 1.0, 12.5), (True, 1.0, 25.0), (True, 1.0, 250.0),
           (False, 1.0, 12.5), (False, 1.0, 250.0), (False, 1.2, None)]
    for bench, Lk, R in sel:
        T = loop(s, R, Lk * P.L, bench)
        lab = corner_name(bench, Lk, R)
        ax[0].semilogx(f, 20 * np.log10(np.abs(T)), lw=1.2, label=lab, ls="-" if bench else "--")
        ax[1].semilogx(f, np.degrees(np.unwrap(np.angle(T))), lw=1.2, ls="-" if bench else "--")
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].axhline(-6, color="r", lw=0.8, ls=":")
    ax[0].text(1.2e3, -4.5, "-6 dB limit for the resonant peak", color="r", fontsize=8)
    ax[0].set_ylabel("|T| (dB)")
    ax[0].set_ylim(-80, 60)
    ax[0].legend(fontsize=7, ncol=2)
    ax[0].grid(True, which="both", alpha=0.3)
    ax[1].axhline(-180, color="k", lw=0.8)
    ax[1].set_ylabel("angle T (deg)")
    ax[1].set_xlabel("f (Hz)")
    ax[1].set_ylim(-540, 180)
    ax[1].grid(True, which="both", alpha=0.3)
    fig.suptitle(f"Loop gain T = Gc Gp H e^(-s 1.5Ts),  Kp = {P.KP}, Ki = {P.KI:g} 1/s, fsw = {P.FSW:.0f} Hz")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "bode_loop.png"), dpi=150)
    plt.close(fig)

    # zoom near 60 Hz
    fz = np.linspace(20, 120, 4000)
    sz = 1j * TWO_PI * fz
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for bench, Lk, R in [(True, 1.0, 12.5), (True, 1.0, 25.0), (False, 1.0, 25.0), (False, 1.0, 250.0)]:
        T = loop(sz, R, Lk * P.L, bench)
        lab = corner_name(bench, Lk, R)
        ax[0].plot(fz, 20 * np.log10(np.abs(T)), label=lab)
        ax[1].plot(fz, np.degrees(np.angle(T)))
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].set_ylabel("|T| (dB)")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    ax[1].axhline(-180, color="k", lw=0.8)
    ax[1].axhline(180, color="k", lw=0.8)
    ax[1].set_ylabel("angle T (deg)")
    ax[1].set_xlabel("f (Hz)")
    ax[1].grid(alpha=0.3)
    fig.suptitle("Loop gain near 60 Hz: two crossings, one each side of f1")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "bode_loop_60Hz.png"), dpi=150)
    plt.close(fig)


def fig_plant(f):
    s = 1j * TWO_PI * f
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for R in (12.5, 25.0, 50.0, 250.0, None):
        g = Gp(s, R)
        ax[0].semilogx(f, 20 * np.log10(np.abs(g)), label="Gp, R=" + ("open" if R is None else f"{R:g}"))
        ax[1].semilogx(f, np.degrees(np.angle(g)))
    for bench in (True, False):
        h = H(s, bench)
        ax[0].semilogx(f, 20 * np.log10(np.abs(h)), "k" + ("-" if bench else "--"),
                       lw=1, label=f"H, {'bench' if bench else 'HIL model'}")
        ax[1].semilogx(f, np.degrees(np.angle(h)), "k" + ("-" if bench else "--"), lw=1)
    ax[0].set_ylim(-60, 50)
    ax[0].set_ylabel("dB")
    ax[0].legend(fontsize=8, ncol=2)
    ax[0].grid(True, which="both", alpha=0.3)
    ax[1].set_ylabel("deg")
    ax[1].set_xlabel("f (Hz)")
    ax[1].grid(True, which="both", alpha=0.3)
    fig.suptitle("Plant Gp = vo/v_inv (94 uH, 31 uF) and sensing filter H")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "bode_plant_sensor.png"), dpi=150)
    plt.close(fig)


def fig_kp_limit(f):
    s = 1j * TWO_PI * f
    kps = np.linspace(0, 0.05, 101)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for bench, Lk, R in [(False, 1.2, 250.0), (False, 1.2, None), (False, 1.0, 50.0), (True, 1.2, 250.0), (True, 1.2, None)]:
        pk = []
        for kp in kps:
            T = loop(s, R, Lk * P.L, bench, kp, P.KI)
            pk.append(20 * np.log10(np.abs(T[(f > 1000) & (f < 8000)]).max()))
        ax.plot(kps, pk, label=corner_name(bench, Lk, R))
    ax.axhline(-6, color="r", ls=":")
    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(P.KP, color="g", ls="--", label=f"chosen Kp = {P.KP}")
    ax.set_xlabel("Kp")
    ax.set_ylabel("resonant peak of |T| (dB)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title(f"Gain stabilization of the 2.95 kHz resonance (Ki = {P.KI:g} 1/s)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "kp_limit.png"), dpi=150)
    plt.close(fig)


def main():
    f = np.logspace(0, np.log10(20e3), 60000)
    rows = analyse(f=f)
    hw = hardware()
    adc = adc_table()
    env = {("bench" if b else "HIL") + f" R={R:g}": envelope_prediction(P.KI, b, R)
           for b in (True, False) for R in (12.5, 25.0)}
    fig_plant(f)
    fig_bode(rows, f)
    fig_kp_limit(f)

    # summary of the loop across corners
    print(f"\nKp = {P.KP}, Ki = {P.KI} 1/s, fsw = {P.FSW:.2f} Hz, tau = {P.TAU*1e6:.1f} us")
    print(f"{'corner':38s} {'crossings (f Hz / PM deg)':40s} {'res. peak':>12s}")
    worst_bank = -1e9
    worst_open = -1e9
    min_pm = 1e9
    for r in rows:
        xs = ", ".join(f"{c['fc']:.1f}/{c['pm']:.0f}" for c in r["crossings"])
        print(f"{r['corner']:38s} {xs:40s} {r['peak_dB']:7.1f} dB @ {r['f_peak']:.0f}")
        if r["R"] is None:
            worst_open = max(worst_open, r["peak_dB"])
        else:
            worst_bank = max(worst_bank, r["peak_dB"])
        for c in r["crossings"]:
            if c["fc"] < 500:
                min_pm = min(min_pm, c["pm"])
    print(f"\nworst resonant peak over the bank range: {worst_bank:.1f} dB, open load: {worst_open:.1f} dB")
    print(f"smallest phase margin at the 60 Hz crossings: {min_pm:.1f} deg")
    for k, v in env.items():
        print(f"envelope {k}: crossover {v['f_env_crossover']:.1f} Hz, PM {v['pm_env']:.1f} deg, "
              f"tau {v['tau_env']*1e3:.1f} ms, vo gain error {v['vo_gain_error']*100:+.2f} %")
    print("\nOperating points:")
    for k, v in hw["operating_points"].items():
        print(k, {a: round(b, 3) if isinstance(b, float) else b for a, b in v.items()})
    print("Envelope:", {a: round(b, 2) for a, b in hw["envelope"].items()})
    print(f"Dead-time fundamental error {hw['deadtime_fundamental_V']:.2f} V at {P.VDC} V")

    out = dict(params=dict(KP=P.KP, KI=P.KI, FSW=P.FSW, TS=P.TS, TAU=P.TAU, VDC=P.VDC, L=P.L, C=P.C,
                           f0=1 / (2 * math.pi * math.sqrt(P.L * P.C)), Z0=math.sqrt(P.L / P.C)),
               loop=rows, worst_peak_bank_dB=worst_bank, worst_peak_open_dB=worst_open,
               min_pm_60Hz=min_pm, envelope=env, hardware=hw, adc=adc)
    with open(os.path.join(HERE, "results_design.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
