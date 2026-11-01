# Spec format for scripts/gen_altium.py

One JSON file per part. Footprint units are mm (top view, origin at package centre,
+Y up). Symbol units are mils. Fields marked (opt) have defaults.

```json
{
  "basename": "TPS62840DLC",
  "title": "TI TPS62840 (VSON-8 1.5 x 2 mm): Altium footprint and schematic symbol",
  "source": "TPS62840 datasheet SLVSEC9B, section 11 (Mechanical), pin table 7.1",
  "date": "2026-11-01",

  "footprint": {
    "name": "TI_VSON8_1P5X2MM_P0.5",
    "description": "VSON-8 1.5 x 2.0 mm, 0.5 mm pitch (TPS62840 datasheet Fig. 11-1)",
    "body": {"D": 1.5, "E": 2.0, "A": 0.6},
    "mask_expansion": 0.05,
    "pads": [
      {"name": "1", "x": -0.7, "y": 0.75, "dx": 0.5, "dy": 0.25, "shape": "rect"},
      {"name": "9", "x": 0, "y": 0, "dx": 0.6, "dy": 1.6, "shape": "rect", "paste": false},
      {"name": "P1", "x": 2.54, "y": 0, "dx": 1.7, "dy": 1.7, "shape": "round", "hole": 1.0}
    ],
    "paste_windows": [{"x": 0, "y": 0.45, "dx": 0.5, "dy": 0.6}],
    "pin1_pad": "1",
    "silk_width": 0.12,
    "silk_offset": 0.1,
    "silk_clearance": 0.2,
    "courtyard_expansion": 0.25,
    "assembly_layer": "eMechanical13",
    "courtyard_layer": "eMechanical15"
  },

  "symbol": {
    "name": "TPS62840DLC",
    "description": "1.8-6.5 V, 750 mA step-down converter",
    "designator": "U?",
    "pin_pitch_mil": 100,
    "pin_length_mil": 200,
    "body_width_mil": 1200,
    "pins": [
      {"num": "1", "name": "VIN", "type": "power", "side": "left", "group": "supply"},
      {"num": "3", "name": "SW", "type": "out", "side": "right", "group": "out"},
      {"num": "9", "name": "GND", "type": "power", "side": "bottom", "group": "gnd"}
    ],
    "parameters": {
      "Manufacturer": "Texas Instruments",
      "Manufacturer Part Number": "TPS62840DLCR",
      "Package": "VSON-8",
      "Datasheet": "https://www.ti.com/lit/ds/symlink/tps62840.pdf"
    }
  }
}
```

## Footprint fields

| Field | Meaning |
|---|---|
| `body.D`, `body.E` | Body size in X and Y (nominal). `body.A` = height (max), used as component height. |
| `mask_expansion` (opt) | Manual solder mask expansion per side for every pad, in mm. `null` or absent = leave pads on the board's mask rule. Use 0.05 at 0.5 mm pitch or finer. |
| `pads[].name` | Pad designator. Must match the symbol pin `num`. Several pads may share a name (e.g. multiple GND or exposed-pad pieces). |
| `pads[].x`, `y`, `dx`, `dy` | Centre and size. Size is before rotation. |
| `pads[].shape` | `"rect"`, `"round"` (dx = dy) or `"oval"` (rounded ends, dx ≠ dy). |
| `pads[].hole` (opt) | Drill diameter. Present = plated through-hole pad on all layers; absent = top-layer SMD pad. |
| `pads[].rotation` (opt) | Degrees, counter-clockwise. |
| `pads[].paste` (opt) | `false` removes the pad's own paste (use with `paste_windows` for exposed pads). |
| `paste_windows` (opt) | Extra top-paste rectangles (centre + size). |
| `pin1_pad` (opt) | Pad that gets the silkscreen dot and assembly chamfer. Default: pad "1", else "A1", else the first pad. |
| `pin1_dot` (opt) | `{"x","y","r"}` to place the dot yourself; otherwise it goes outside the body next to pin 1. |
| `silk_*`, `courtyard_*`, `*_layer` (opt) | Defaults shown above. Silk is the body outline offset by `silk_offset`, with every part that comes within `silk_clearance` of copper removed. |

## Symbol fields

| Field | Meaning |
|---|---|
| `pins[].side` | `left`, `right`, `top` or `bottom`. Pins are placed in list order. |
| `pins[].group` | A blank row is left between consecutive pins of different groups on the left/right sides. |
| `pins[].type` | `io`, `in`, `out`, `power`, `passive`, `oc` (open collector), `hiz`, `emitter`. |
| `body_width_mil` (opt) | Default: wide enough for the longest left + right names and the top/bottom pins. |
| `parameters` | Hidden component parameters (any name/value). |

Pin numbers must be unique in the symbol. Every pin number must have at least one pad
with that name; pads without a pin are reported (fine for mounting pads, an error
otherwise).
