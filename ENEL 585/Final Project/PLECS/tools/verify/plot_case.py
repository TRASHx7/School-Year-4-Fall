#!/usr/bin/env python3
"""Plot a sim_station CSV as a standalone SVG (no plotting libraries needed).
Usage: python3 plot_case.py case0.csv out.svg"""
import csv
import sys

rows = [{k: float(v) for k, v in x.items()} for x in csv.DictReader(open(sys.argv[1]))]
W, PH, L, R, TOP = 900, 150, 70, 20, 40
T0, T1 = 0.0, 1.10
panels = [
    ("Output voltage vo [V]", [("vo", "#1f5fa8", 1)], (-50, 50)),
    ("Inductor current iL [A] (at ADC instants, and true peak)", [("iL", "#b5432c", 1),
                                                                   ("iL_max", "#e3a08f", 1)], (-8, 8)),
    ("Output amplitude [V pk]: measured, command", [("vpk_meas", "#1f5fa8", 2),
                                                    ("vc", "#7a7a7a", 1)], (0, 50)),
    ("Modulation index m", [("m", "#2e7d32", 2)], (0, 1)),
]
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{TOP + len(panels)*(PH + 40)}" '
       'font-family="sans-serif" font-size="11"><rect width="100%" height="100%" fill="white"/>',
       f'<text x="{L}" y="20" font-size="13" font-weight="bold">Demonstration sequence, '
       'C model of the station with the firmware controller (Vdc = 50 V, 2 us dead time)</text>']


def X(t):
    return L + (t - T0)/(T1 - T0)*(W - L - R)


for k, (title, series, (lo, hi)) in enumerate(panels):
    y0 = TOP + k*(PH + 40) + 20

    def Y(v):
        return y0 + PH - (min(max(v, lo), hi) - lo)/(hi - lo)*PH
    svg.append(f'<text x="{L}" y="{y0 - 6}">{title}</text>')
    svg.append(f'<rect x="{L}" y="{y0}" width="{W - L - R}" height="{PH}" fill="none" stroke="#999"/>')
    for v in (lo, (lo + hi)/2, hi):
        svg.append(f'<text x="{L - 6}" y="{Y(v) + 4}" text-anchor="end">{v:g}</text>')
    for te, lab in ((0.02, "enable"), (0.30, "12.5 ohm"), (0.50, "30 Vrms"), (0.70, "25 Vrms"),
                    (0.85, "25 ohm")):
        svg.append(f'<line x1="{X(te)}" x2="{X(te)}" y1="{y0}" y2="{y0 + PH}" stroke="#ccc" '
                   'stroke-dasharray="3,3"/>')
        if k == len(panels) - 1:
            svg.append(f'<text x="{X(te)}" y="{y0 + PH + 14}" text-anchor="middle">{te:g} s {lab}</text>')
    for key, color, width in series:
        step = 2 if key in ("vo", "iL", "iL_max") else 8
        pts = " ".join(f"{X(r['t']):.1f},{Y(r[key]):.1f}" for r in rows[::step])
        svg.append(f'<polyline fill="none" stroke="{color}" stroke-width="{width}" points="{pts}"/>')
svg.append("</svg>")
open(sys.argv[2], "w").write("\n".join(svg))
