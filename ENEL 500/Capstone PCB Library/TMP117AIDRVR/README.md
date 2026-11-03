# TMP117AIDRVR: Altium footprint and schematic symbol

Altium library parts for the Texas Instruments TMP117 high-accuracy digital temperature sensor in the 6-pin WSON (2.0 x 2.0 x 0.8 mm max, TI package DRV0006B), order code TMP117AIDRVR. The same footprint and pinout fit every DRV order code (TMP117AIDRVR, TMP117MAIDRVR, TMP117NAIDRVR). The DSBGA (YBG) version has a different footprint and is not covered here. Built from the TMP117 data sheet SNOSD82D (Sept 2022):

- Pin numbers and names: Figure 5-1 (DRV Package Top View) and Table 5-1 (Pin Functions), page 4
- Package: DRV0006B package outline, page 40: body 2.0 ±0.1 x 2.0 ±0.1 mm, 0.8 mm max height, pitch 0.65, terminal width 0.2 to 0.3, length 0.25 to 0.35, exposed thermal pad 1.0 x 1.6 mm
- Land pattern: DRV0006B example board layout, page 41: 6 pads 0.45 x 0.3 mm, 0.65 mm pitch, 1.95 mm row spacing, R0.05 corners, non solder mask defined, 0.07 mm max mask opening around each pad
- Thermal pad: section 9.2 (page 36) says the thermal pad isn't connected to device ground and should be left unsoldered for best accuracy on a rigid PCB

## Files

| File | What it is |
|---|---|
| `TMP117AIDRVR.pas` | Altium DelphiScript. `CreateFootprint` builds the footprint in the open PcbLib, `CreateSymbol` builds the symbol in the open SchLib. |
| `TMP117AIDRVR.PrjScr` | Script project, so the script shows up in File > Run Script. |
| `TMP117AIDRVR_pin_table.csv` | Every pin: designator, pin name, electrical type, symbol side, pad position and size. |
| `TMP117AIDRVR_footprint_preview.png` | Top view of the footprint as the script draws it. |
| `TMP117AIDRVR_symbol_preview.png` | The schematic symbol as the script draws it. |
| `generator/` | The spec JSON and the `gen_altium.py` used to make the script. |

## Using it in Altium Designer

1. File > New > Library > PCB Library (or open the project PcbLib). Click its tab so it is the active document, then File > Run Script > Browse > From file, pick `TMP117AIDRVR.PrjScr`, choose `CreateFootprint` and press OK.
2. File > New > Library > Schematic Library (or open the project SchLib). Click its tab, then File > Run Script and run `CreateSymbol`.
3. Save both libraries. The symbol is already linked to footprint `TI_WSON6_2X2MM_P0.65_DRV0006B`.

Don't use the Run button inside the script editor. The script itself is then the active document, so it can't find the library and stops with a message.

## Footprint

- 6 rectangular SMD pads, 0.45 x 0.3 mm, named 1 to 6. Top view, pin 1 top left: 1 to 3 down the left side, 4 to 6 up the right side, as in Figure 5-1.
- Pad centres at x = ±0.975 mm (TI's 1.95 mm row spacing), y = +0.65, 0, -0.65 mm. Gap between pads in a row 0.35 mm.
- No thermal pad land, following TI's land pattern example and the section 9.2 advice. If you build on a flexible PCB and want the extra solder joint for reliability, add a 1.0 x 1.6 mm pad at the centre and tie it to GND or leave it floating (the data sheet allows both).
- TI draws R0.05 rounded corners. The pads here are plain rectangles; the difference is negligible at this size, but you can switch them to rounded rectangles (corner radius about 33%) in Altium if you want an exact match.
- Solder mask expansion fixed at 0.05 mm per side (TI: 0.07 max, non solder mask defined). Paste: same as the pad, which matches TI's stencil example (page 42) for a 0.125 mm stencil.
- Pin-1 dot outside the body next to pin 1, assembly outline with pin-1 chamfer on Mechanical 13, silkscreen lines along the top and bottom edges (the sides are clipped because the pads come within 0.2 mm), courtyard (body + 0.25 mm) on Mechanical 15. Height 0.8 mm (A max).
- No 3D model.

## Symbol

Single part, 6 pins, 100 mil pitch.

- Left: V+ (pin 5), ADD0 (pin 4, connect to GND, V+, SDA or SCL to pick one of four I2C addresses).
- Right: SCL (pin 1), SDA (pin 6, open drain, needs a pullup), ALERT (pin 3, open drain, needs a pullup).
- Bottom: GND (pin 2).
- Hidden parameters: Manufacturer, Manufacturer Part Number, Package, Datasheet.

Checks done: 6 pins in Table 5-1, 6 signal terminals in the package outline (plus the thermal pad, deliberately not landed), every pin has one pad, and no pads overlap.

## Things to confirm before ordering boards

- Decide whether to solder the thermal pad (see above). For best accuracy on a rigid board, leave it as is.
- Keep a 0.1 µF decoupling cap close to V+ (Figure 10-1) and follow the thermal layout advice in sections 9.2 and 10.1 (keep it away from heat sources, consider a PCB cutout around it).
- Check the 0.25 mm mask web between pads against the board house's limits (it is comfortable).
- Print the footprint 1:1 and lay a part on it.

## Rebuilding

```
python3 generator/gen_altium.py generator/TMP117AIDRVR_spec.json .
```
