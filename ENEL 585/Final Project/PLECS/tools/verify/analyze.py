#!/usr/bin/env python3
"""Transient metrics from a sim_station CSV: half-cycle output peaks around each
event of the demonstration sequence. Usage: python3 analyze.py case0.csv [...]"""
import csv
import sys

EVENTS = [(0.30, "load step 25 -> 12.5 ohm", 0.50), (0.50, "ref step 25 -> 30 Vrms", 0.70),
          (0.70, "ref step 30 -> 25 Vrms", 0.85), (0.85, "load step 12.5 -> 25 ohm", 1.10)]


def half_cycle_peaks(fname):
    hp = {}
    for x in csv.DictReader(open(fname)):
        t = float(x["t"])
        h = hp.setdefault(int(t*120), [0.0, 0.0])
        h[0] = max(h[0], abs(float(x["vo"])))
        h[1] = max(h[1], float(x["iL_max"]))
    return [(h/120, v, i) for h, (v, i) in sorted(hp.items())]


def report(fname):
    hp = half_cycle_peaks(fname)
    print("==", fname)
    for t, v, _ in hp:
        if t >= 0.02 and v >= 0.98*25*2**0.5:
            print(f"  startup: 98 % of 35.36 V pk {1000*(t + 1/120 - 0.02):.0f} ms after enable")
            break
    for t0, name, t1 in EVENTS:
        pre = [v for t, v, _ in hp if t0 - 0.05 <= t < t0]
        fin = [v for t, v, _ in hp if t1 - 0.05 <= t < t1]
        vb, vf = sum(pre)/len(pre), sum(fin)/len(fin)
        seg = [(t, v, i) for t, v, i in hp if t0 <= t < t1]
        sgn = 1 if vf >= vb else -1
        over = max(sgn*(v - vf) for _, v, _ in seg)
        dev = max(abs(v - vf) for _, v, _ in seg)
        ts = max([t + 1/120 - t0 for t, v, _ in seg if abs(v - vf) > 0.02*vf] or [0])
        ipk = max(i for _, _, i in seg)
        print(f"  {name:25s} {vb:5.2f} -> {vf:5.2f} V pk | overshoot {100*over/vf:4.1f} % | "
              f"max deviation {100*dev/vf:4.1f} % | 2 % settling {1000*ts:5.1f} ms | "
              f"iL peak {ipk:4.2f} A")


for f in sys.argv[1:]:
    report(f)
