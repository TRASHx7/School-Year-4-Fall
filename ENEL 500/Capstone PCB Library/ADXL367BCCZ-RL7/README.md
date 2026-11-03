# ADXL367BCCZ-RL7: Altium footprint and schematic symbol

Altium library parts for the Analog Devices ADXL367 ultralow power 3-axis MEMS accelerometer in the 12-terminal LGA (2.2 x 2.3 x 0.87 mm, package option CC-12-4), order code ADXL367BCCZ-RL7. The same footprint and pinout fit every ADXL367 order code (BCCZ, BCCZ-RL, BCCZ-RL7, U8-BCCZ...). Built from the ADXL367 data sheet Rev. B:

- Pin numbers and names: Figure 17 (Pin Configuration, top view) and Table 9 (Pin Function Descriptions), page 13
- Land pattern: Figure 64 (Recommended PCB Land Pattern), page 64: 2.11 mm overall X, 2.21 mm overall Y, pad 0.39 mm long, side-pad width 0.33 mm, side-pad pitch 0.5 mm
- Body: 2.2 x 2.3 x 0.87 mm, page 1

The data sheet's Outline Dimensions section (page 65) has no drawing, only a link to the ADI package index for CC-12-4.

## Files

| File | What it is |
|---|---|
| `ADXL367BCCZ-RL7.pas` | Altium DelphiScript. `CreateFootprint` builds the footprint in the open PcbLib, `CreateSymbol` builds the symbol in the open SchLib. |
| `ADXL367BCCZ-RL7.PrjScr` | Script project, so the script shows up in File > Run Script. |
| `ADXL367BCCZ-RL7_pin_table.csv` | Every pin: designator, pin name, electrical type, symbol side, pad position and size. |
| `ADXL367BCCZ-RL7_footprint_preview.png` | Top view of the footprint as the script draws it. |
| `ADXL367BCCZ-RL7_symbol_preview.png` | The schematic symbol as the script draws it. |
| `generator/` | The spec JSON and the `gen_altium.py` used to make the script. |

## Using it in Altium Designer

1. File > New > Library > PCB Library (or open the project PcbLib). Click its tab so it is the active document, then File > Run Script > Browse > From file, pick `ADXL367BCCZ-RL7.PrjScr`, choose `CreateFootprint` and press OK.
2. File > New > Library > Schematic Library (or open the project SchLib). Click its tab, then File > Run Script and run `CreateSymbol`.
3. Save both libraries. The symbol is already linked to footprint `ADI_LGA12_2.2X2.3MM_P0.5`.

Don't use the Run button inside the script editor. The script itself is then the active document, so it can't find the library and stops with a message.

## Footprint

- 12 rectangular SMD pads, named 1 to 12. Top view, pin 1 top-left, numbered counter-clockwise: 1 to 4 down the left side, 5 and 6 on the bottom, 7 to 10 up the right side, 11 and 12 on the top (11 right, 12 left), as in Figure 17.
- Left and right pads (1 to 4, 7 to 10): 0.39 x 0.33 mm, centres at x = ±0.86 mm, y = ±0.25 and ±0.75 mm (0.5 mm pitch). The outer edges land at ±1.055 mm, giving Figure 64's 2.11 mm.
- Top and bottom pads (5, 6, 11, 12): 0.33 x 0.39 mm, centres at x = ±0.25 mm, y = ±0.91 mm. Outer edges at ±1.105 mm, giving Figure 64's 2.21 mm.
- Pad gap 0.17 mm between neighbours on a side, 0.25 mm between a top/bottom pad and the nearest corner pad.
- Solder mask expansion fixed at 0.05 mm per side, which leaves a 0.07 mm mask web between neighbouring side pads. Paste: same as the pad.
- Pin-1 dot outside the body next to pin 1, assembly outline with pin-1 chamfer on Mechanical 13, silkscreen corner marks (the rest of the outline is clipped because the pads come within 0.2 mm of it), courtyard (body + 0.25 mm) on Mechanical 15. Height 0.87 mm.
- No 3D model.

## Symbol

Single part, 12 pins, 100 mil pitch.

- Left: supplies (VS pin 10, VDDIO pin 12), VREG_OUT (pin 9, needs the external 0.2 µF decoupling cap per Table 9 note 1), ADC_IN (pin 8).
- Right: serial bus (CS/SCL, SCLK, MOSI/SDA, MISO/ASEL), interrupts (INT1, INT2; both can also act as inputs for external clock / synchronized sampling, so they are typed I/O).
- Bottom: GND (pins 7 and 11), both must be grounded.
- Hidden parameters: Manufacturer, Manufacturer Part Number, Package, Datasheet.

Checks done: 12 pins in Table 9, 12 terminals in Figures 17 and 64, every pin has one pad, and no pads overlap.

## Things to confirm before ordering boards

- **Top and bottom pad pitch and width are not dimensioned in Figure 64.** The figure only labels the side pads (0.33 wide, 0.5 pitch) and the 0.39 pad length. The top/bottom pads are drawn the same size as the side pads, so this footprint uses 0.33 mm wide pads at 0.5 mm pitch (x = ±0.25 mm). Check these against the CC-12-4 package drawing from the ADI package index, or the EVAL-ADXL367Z breakout board layout, before ordering.
- Check the 0.07 mm mask web against the board house's minimum. If it's too small, drop the mask expansion to 0.03 mm or use a gang (no web) opening per side.
- Print the footprint 1:1 and lay a part on it, or overlay it on the EVAL-ADXL367Z layout.
- Mount the part near a rigid mounting point (data sheet page 63 to 64) so board resonance doesn't show up in the readings.

## Rebuilding

```
python3 generator/gen_altium.py generator/ADXL367BCCZ-RL7_spec.json .
```
