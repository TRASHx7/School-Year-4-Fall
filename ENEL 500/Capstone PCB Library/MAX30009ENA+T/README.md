# MAX30009ENA+T: Altium footprint and schematic symbol

Altium library parts for the Analog Devices MAX30009 bioimpedance AFE in the 25-bump WLP (2.03 x 2.03 mm, 0.4 mm pitch), order code MAX30009ENA+T. Built from:

- Ball map and names: MAX30009 data sheet Rev 2 (19-101213, Aug 2023), Pin Configuration (page 20) and Pin Description (pages 20 and 21)
- Package dimensions: package outline 21-100494 Rev A (N252C2+1): e = 0.40, b = 0.27 ±0.03, D = E = 2.028 ±0.025, A = 0.50 max, D1 = E1 = 1.60, SD = SE = 0, no depopulated bumps

## Files

| File | What it is |
|---|---|
| `MAX30009ENA+T.pas` | Altium DelphiScript. `CreateFootprint` builds the footprint in the open PcbLib, `CreateSymbol` builds the symbol in the open SchLib. |
| `MAX30009ENA+T.PrjScr` | Script project, so the script shows up in File > Run Script. |
| `MAX30009ENA+T_pin_table.csv` | Every ball: designator, pin name, electrical type, symbol side, pad position and size. |
| `MAX30009ENA+T_footprint_preview.png` | Top view of the footprint as the script draws it. |
| `MAX30009ENA+T_symbol_preview.png` | The schematic symbol as the script draws it. |
| `generator/` | `build_spec.py` (ball map and package numbers to spec), the spec JSON, and the `gen_altium.py` used to make the script. |

## Using it in Altium Designer

1. File > New > Library > PCB Library (or open the project PcbLib). Click its tab so it is the active document, then File > Run Script > Browse > From file, pick `MAX30009ENA+T.PrjScr`, choose `CreateFootprint` and press OK.
2. File > New > Library > Schematic Library (or open the project SchLib). Click its tab, then File > Run Script and run `CreateSymbol`.
3. Save both libraries. The symbol is already linked to footprint `ADI_WLP25_2.03X2.03MM_P0.4`.

Don't use the Run button inside the script editor. The script itself is then the active document, so it can't find the library and stops with a message.

## Footprint

- 25 round pads, 0.22 mm diameter, non-solder-mask-defined, named with the ball designators A1 to E5.
- 5 x 5 grid at 0.40 mm pitch centred on the origin. Top view: row A at the top, column 1 on the left, so A1 is top-left (the outline's bottom view mirrored, and the same as the data sheet's top-view pin configuration).
- Pad size: the outline gives no land pattern, and the data sheet only says "Refer to Application Note 1891". The pad is 80% of the nominal ball diameter (0.8 x 0.27 = 0.216, rounded to 0.22 mm), the usual NSMD rule. That leaves 0.18 mm copper to copper.
- Solder mask expansion fixed at 0.03 mm per side (0.28 mm openings), which leaves a 0.12 mm mask web between neighbouring pads. The usual 0.1 mm rule would remove the web completely at this pitch.
- Paste: same as the pad (0.22 mm circles).
- Pin-1 dot outside the body next to A1, assembly outline with A1 chamfer on Mechanical 13, silkscreen outline 0.2 mm outside the body (closer would overlap the pad clearance), courtyard (body + 0.3 mm) on Mechanical 15. Height 0.50 mm (A max).
- No 3D model.

## Symbol

Single part, 25 pins, 100 mil pitch.

- Left: supply (AVDD, DVDD, VREF), electrodes (EL1, EL2A, EL2B, EL3B, EL3A, EL4), calibration port (CAL1 to CAL4).
- Right: interface (SCLK/SCL, SDI/SDA, SDO/ADDR, CSB/I2C_SEL, INT), clock (FCLK, TRIG), drive amplifier (DRVSJ, DRVXR, DRVXC).
- Bottom: AGND (C3), DGND (E1).
- Hidden parameters: Manufacturer, Manufacturer Part Number, Package, Datasheet, Supplier 1, Supplier Part Number 1 (Digi-Key 175-MAX30009ENA+TCT-ND).

Checks done: 25 names in the pin configuration, 25 bumps in the outline, every ball has one pad and one pin, and no pads overlap.

## Things to confirm before ordering boards

- Compare the 0.22 mm pad and 0.03 mm mask expansion with ADI Application Note 1891 (WLP land pattern guidance) and with the MAX30009 EV kit sensor board layout, and change them if either says otherwise.
- Check the 0.12 mm mask web and 0.18 mm pad gap against the board house's limits.
- The inner nine balls need via-in-pad (filled and capped) or microvias to escape. Confirm the board house can do it.
- Print the footprint 1:1, or overlay it on the EV kit layout.

## Rebuilding

```
python3 generator/build_spec.py generator/MAX30009ENA+T_spec.json
python3 generator/gen_altium.py generator/MAX30009ENA+T_spec.json .
```
