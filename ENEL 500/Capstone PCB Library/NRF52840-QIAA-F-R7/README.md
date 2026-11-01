# NRF52840-QIAA-F-R7: Altium footprint and schematic symbol

Altium library parts for the Nordic nRF52840 in the aQFN73 7 x 7 mm package, built from the nRF52840 Product Specification v1.8, chapter 7:

- Ball names and functions: section 7.1.1, Table 145
- Ball positions: section 7.1.1, Figure 207 (ball map, top view)
- Package dimensions: section 7.2.1, Figure 210 and Table 148 (e = 0.50, e1 = 2.75, e2 = 0.559, b = 0.25, D2 = 4.85 mm)

## Files

| File | What it is |
|---|---|
| `NRF52840-QIAA-F-R7.pas` | Altium DelphiScript. `CreateFootprint` builds the footprint in the open PcbLib, `CreateSymbol` builds the symbol in the open SchLib. |
| `NRF52840-QIAA-F-R7.PrjScr` | Script project, so the script shows up in File > Run Script. |
| `NRF52840-QIAA-F-R7_pin_table.csv` | Every ball: designator, pin name, electrical type, symbol side, pad position and size. |
| `NRF52840-QIAA-F-R7_footprint_preview.png` | Top view of the footprint as the script draws it. |
| `NRF52840-QIAA-F-R7_symbol_preview.png` | The schematic symbol as the script draws it. |
| `generator/` | Python that turns the datasheet pages into the script, so the parts can be rebuilt or edited. |

## Using it in Altium Designer

1. File > New > Library > PCB Library. With the new PcbLib active, File > Run Script, browse to `NRF52840-QIAA-F-R7.pas` (or open `NRF52840-QIAA-F-R7.PrjScr` first) and run `CreateFootprint`.
2. File > New > Library > Schematic Library. With the new SchLib active, run `CreateSymbol`.
3. Save both libraries in the project. The symbol is already linked to footprint `NORDIC_AQFN73_7X7MM_P0.5`.

The script was generated and checked here but has not been run in Altium yet. If Altium reports an error, note the line number and message.

## Footprint

- 73 round pads, 0.25 mm diameter (Table 148 b nominal), named with the ball designators (A8, B1, ... AD23).
- Outer ring at ±3.25 mm (e1 + e), inner ring at ±2.75 mm (e1), 0.5 mm pitch along each row, rings staggered by 0.25 mm (e/2).
- Exposed pad `EP`, 4.85 x 4.85 mm (D2 nominal), ground (VSS). Its own paste is removed and replaced by four 1.9 x 1.9 mm paste windows (about 61% coverage).
- Solder mask expansion fixed at 0.05 mm per side on every pad. The usual 0.1 mm rule would leave almost no mask between pads at this pitch. This leaves a 0.15 mm mask web between neighbouring pads and 0.10 mm between the inner ring and the exposed pad.
- Silkscreen corner marks outside the body (pin-1 corner broken, plus a dot), assembly outline on Mechanical 13, courtyard (body + 0.3 mm) on Mechanical 15. Height 0.85 mm (A max).
- No 3D model or thermal vias. Add vias in the exposed pad in the PCB, and attach a STEP model if you want one.

Checks done: every ball in Table 145 matches a circle in Figure 207 (73 of 73), every position follows the e / e1 / e2 stagger rule, and all 73 positions match KiCad's independently drawn `Nordic_AQFN-73-1EP_7x7mm_P0.5mm` footprint.

## Symbol

Single part, 74 pins (73 balls plus EP), 100 mil pin pitch.

- Left: supply (VDDH, VDD x5), regulator pins (DEC1 to DEC6, DCC, DCCH, NC), clock (XC1, XC2), RF (ANT), debug (SWDIO, SWDCLK), USB (VBUS, DECUSB, D+, D-), then P1.00 to P1.15.
- Right: P0.00 to P0.31.
- Bottom: VSS (B7), VSS (EP), VSS_PA (F23).
- Ball N24 is named `NC`. Table 145 lists it as DEC5 only for build codes Dxx and earlier, and not connected for Fxx parts like this one.
- Hidden parameters: Manufacturer, Manufacturer Part Number, Package, Datasheet, Supplier 1, Supplier Part Number 1.

## Things to confirm before ordering boards

- Check the pad sizes and mask settings against your board house's limits (0.1 mm mask web between the inner ring and the exposed pad).
- Compare with the land pattern in Nordic's nRF52840 reference layout files (Altium format, from the nRF52840 product page) if you can get them.
- Print the footprint 1:1 and lay a chip on it, or compare against the DK board.

## Rebuilding

```
python3 generator/gen_altium.py generator/NRF52840-QIAA-F-R7_spec.json .
```

To rebuild the spec from the datasheet pages: run `pdftotext -layout` on the Table 145 pages into `table145.txt`, run `generator/pdf_circles.py <pdf> <Figure 207 page>` into `p1_paths.txt`, then `generator/build_qiaa_spec.py <dir> <spec.json>`. It stops with an error if the table and the figure disagree.
