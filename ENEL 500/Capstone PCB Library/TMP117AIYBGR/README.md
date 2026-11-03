# TMP117AIYBGR: Altium footprint and schematic symbol

Altium library parts for the Texas Instruments TMP117 high-accuracy digital temperature sensor in the 6-ball DSBGA (TI package YBG0006-C01), order code TMP117AIYBGR. The same footprint and pinout fit TMP117MAIYBGR and TMP117NAIYBGR. The WSON (DRV) version has a different footprint and is not included. Built from the TMP117 data sheet SNOSD82D (Sept 2022):

- Ball map: Figure 5-2 (YBG Package Top View) and Table 5-1 (Pin Functions), page 4
- Package: YBG0006-C01 package outline, page 43: 2 x 3 balls, 0.4 mm pitch both ways, ball diameter 0.23 to 0.27 mm, body 0.92 to 0.98 mm (TI's E, across the 2 columns) by 1.458 to 1.518 mm (TI's D, along the 3 rows), 0.531 mm max height
- Land pattern: YBG0006-C01 example board layout, page 44: 6 round pads 0.23 mm, 0.4 mm pitch, non solder mask defined (preferred), mask opening 0.05 mm max around each pad
- Paste: YBG0006-C01 example stencil design, page 45: 0.25 mm square apertures with R0.05 corners, 0.1 mm thick stencil

## Files

| File | What it is |
|---|---|
| `TMP117AIYBGR.pas` | Altium DelphiScript. `CreateFootprint` builds the footprint in the open PcbLib, `CreateSymbol` builds the symbol in the open SchLib. |
| `TMP117AIYBGR.PrjScr` | Script project, so the script shows up in File > Run Script. |
| `TMP117AIYBGR_pin_table.csv` | Every ball: designator, pin name, electrical type, symbol side, pad position and size. |
| `TMP117AIYBGR_footprint_preview.png` | Top view of the footprint as the script draws it. |
| `TMP117AIYBGR_symbol_preview.png` | The schematic symbol as the script draws it. |
| `generator/` | The spec JSON and the `gen_altium.py` used to make the script. |

## Using it in Altium Designer

1. File > New > Library > PCB Library (or open the project PcbLib). Click its tab so it is the active document, then File > Run Script > Browse > From file, pick `TMP117AIYBGR.PrjScr`, choose `CreateFootprint` and press OK.
2. File > New > Library > Schematic Library (or open the project SchLib). Click its tab, then File > Run Script and run `CreateSymbol`.
3. Save both libraries. The symbol is already linked to footprint `TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006`.

For a workspace component (Component Editor > Add Footprint/Add Symbol > New), run the same procedures in the new footprint and symbol tabs. The scripts delete the blank default item those documents start with, so Save to Server accepts them. `RemoveEmptyFootprints` / `RemoveEmptySymbols` clean up a document an older script already filled.

Don't use the Run button inside the script editor. The script itself is then the active document, so it can't find the library and stops with a message.

## Footprint

- 6 round SMD pads, 0.23 mm diameter, named with the ball designators A1 to C2.
- Top view, matching Figure 5-2 and the page 44 land pattern: row A at the top, column 1 on the left, so A1 (SDA) is top left. Pad centres at x = -0.2 (column 1) and +0.2 mm (column 2), y = +0.4 (row A), 0 (row B), -0.4 mm (row C). The page 43 outline draws the balls from the other side (row A at the bottom); that is the bottom view, not a different pinout.
- Copper to copper gap 0.17 mm.
- Solder mask expansion fixed at 0.03 mm per side (0.29 mm openings, non solder mask defined). TI allows up to 0.05 mm, but that would leave only a 0.07 mm mask web between balls; 0.03 leaves 0.11 mm.
- Paste: the pads have no paste of their own; instead each ball gets TI's 0.25 x 0.25 mm square aperture (plain square here, TI rounds the corners R0.05).
- Pin-1 dot outside the body next to A1, assembly outline with A1 chamfer on Mechanical 13, silkscreen lines across the top and bottom (the sides are clipped because the pads come within 0.2 mm), courtyard (body + 0.25 mm) on Mechanical 15. Body 0.95 x 1.488 mm nominal, height 0.531 mm (max).
- No 3D model.

## Symbol

Single part, 6 pins, 100 mil pitch, pin numbers are the ball designators.

- Left: V+ (B1), ADD0 (C1, connect to GND, V+, SDA or SCL to pick one of four I2C addresses).
- Right: SCL (A2), SDA (A1, open drain, needs a pullup), ALERT (C2, open drain, needs a pullup).
- Bottom: GND (B2).
- Hidden parameters: Manufacturer, Manufacturer Part Number, Package, Datasheet.

Checks done: 6 balls in Table 5-1, 6 balls in the outline (no depopulated positions), every ball has one pad and one pin, and no pads overlap.

## Things to confirm before ordering boards

- Check the 0.11 mm mask web and the 0.29 mm mask openings against the board house's limits. If they can't hold a web that thin, switch to a gang (no web) opening or ask about their DSBGA rules. TI's SNVA009 app note covers DSBGA board design.
- 0.4 mm pitch with 0.23 mm pads leaves room for a 0.1 mm trace between pads only if the board house can do 0.1/0.1 mm track/space; otherwise route the outer balls out the sides and the middle row (B1 V+, B2 GND) out through vias or straight out the sides, which works here because there are only two columns.
- Keep a 0.1 µF decoupling cap close to V+ (B1) and follow the thermal layout advice in sections 9.2 and 10.1 (the YBG layout example is Figure 10-2).
- Print the footprint 1:1, or overlay it on the TMP117 EVM layout if you have it.

## Rebuilding

```
python3 generator/gen_altium.py generator/TMP117AIYBGR_spec.json .
```
