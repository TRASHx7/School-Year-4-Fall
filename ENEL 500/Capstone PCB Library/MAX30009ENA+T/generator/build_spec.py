"""Build the MAX30009ENA+T spec for gen_altium.py.

Sources:
  Ball map and names: MAX30009 data sheet Rev 2 (19-101213, Aug 2023), Pin Configuration p.20
  and Pin Description pp.20-21.
  Package dimensions: ADI/Maxim package outline 21-100494 Rev A (N252C2+1).
"""
import json, sys

E = 0.40            # pitch e (21-100494)
B = 0.27            # ball diameter b nominal (21-100494)
PAD = 0.22          # NSMD land = ~80% of b nominal (0.216), rounded to 0.22
ROWS = "ABCDE"      # top view: row A at the top (+Y), column 1 at the left (-X)

# Data sheet p.20 Pin Configuration (top view, bump side down)
BALLMAP = {
    "A": ["EL1", "EL2A", "EL2B", "CAL1", "CAL2"],
    "B": ["EL4", "EL3A", "EL3B", "CAL4", "CAL3"],
    "C": ["AVDD", "VREF", "AGND", "DRVSJ", "DRVXR"],
    "D": ["DVDD", "CSB/I2C_SEL", "FCLK", "TRIG", "DRVXC"],
    "E": ["DGND", "SDO/ADDR", "SDI/SDA", "SCLK/SCL", "INT"],
}

# Symbol: (ball, type, side, group), in display order
SYMBOL = [
    ("C1", "power", "left", "1 Supply"), ("D1", "power", "left", "1 Supply"),
    ("C2", "passive", "left", "1 Supply"),
    ("A1", "passive", "left", "2 Electrodes"), ("A2", "passive", "left", "2 Electrodes"),
    ("A3", "passive", "left", "2 Electrodes"), ("B3", "passive", "left", "2 Electrodes"),
    ("B2", "passive", "left", "2 Electrodes"), ("B1", "passive", "left", "2 Electrodes"),
    ("A4", "passive", "left", "3 Calibration"), ("A5", "passive", "left", "3 Calibration"),
    ("B5", "passive", "left", "3 Calibration"), ("B4", "passive", "left", "3 Calibration"),
    ("E4", "in", "right", "1 Interface"), ("E3", "io", "right", "1 Interface"),
    ("E2", "io", "right", "1 Interface"), ("D2", "in", "right", "1 Interface"),
    ("E5", "out", "right", "1 Interface"),
    ("D3", "in", "right", "2 Clock"), ("D4", "in", "right", "2 Clock"),
    ("C4", "passive", "right", "3 Drive amp"), ("C5", "passive", "right", "3 Drive amp"),
    ("D5", "passive", "right", "3 Drive amp"),
    ("C3", "power", "bottom", "4 Ground"), ("E1", "power", "bottom", "4 Ground"),
]

def main(out):
    names, pads = {}, []
    for r, row in enumerate(ROWS):
        for c in range(5):
            ball = f"{row}{c + 1}"
            names[ball] = BALLMAP[row][c]
            pads.append({"name": ball, "x": round((c - 2) * E, 3), "y": round((2 - r) * E, 3),
                         "dx": PAD, "dy": PAD, "shape": "round"})
    used = [s[0] for s in SYMBOL]
    assert len(used) == len(set(used)) == 25 and set(used) == set(names), "symbol does not cover all 25 balls"

    spec = {
        "basename": "MAX30009ENA+T",
        "title": "Analog Devices MAX30009ENA+T (25-bump WLP 2.03 x 2.03 mm, 0.4 mm pitch): Altium footprint and schematic symbol",
        "source": "MAX30009 data sheet Rev 2 (Aug 2023) p.20-21 pin configuration and description; package outline 21-100494 Rev A",
        "date": "2026-11-01",
        "footprint": {
            "name": "ADI_WLP25_2.03X2.03MM_P0.4",
            "description": "25-bump WLP (N252C2+1), 2.028 x 2.028 mm, 0.4 mm pitch, 0.22 mm NSMD lands (21-100494 Rev A)",
            "body": {"D": 2.028, "E": 2.028, "A": 0.50},
            "mask_expansion": 0.03,
            "pads": pads,
            "pin1_pad": "A1",
            "courtyard_expansion": 0.25,
        },
        "symbol": {
            "name": "MAX30009ENA+T",
            "description": "Low-power, high-performance bioimpedance (BioZ) AFE, 1.8 V, SPI/I2C",
            "designator": "U?",
            "pins": [{"num": b, "name": names[b], "type": t, "side": s, "group": g} for b, t, s, g in SYMBOL],
            "parameters": {
                "Manufacturer": "Analog Devices",
                "Manufacturer Part Number": "MAX30009ENA+T",
                "Package": "25-WLP 2.03 x 2.03 mm, 0.4 mm pitch (N252C2+1, outline 21-100494)",
                "Datasheet": "https://www.analog.com/media/en/technical-documentation/data-sheets/max30009.pdf",
                "Supplier 1": "Digi-Key",
                "Supplier Part Number 1": "175-MAX30009ENA+TCT-ND",
            },
        },
    }
    json.dump(spec, open(out, "w"), indent=2)
    print(f"wrote {out}: {len(pads)} pads, {len(SYMBOL)} pins, pad {PAD} mm, gap {E - PAD:.2f} mm")

if __name__ == "__main__":
    main(sys.argv[1])
