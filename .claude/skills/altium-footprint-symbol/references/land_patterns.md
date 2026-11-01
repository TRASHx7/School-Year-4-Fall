# Land pattern rules of thumb

Use the manufacturer's recommended land pattern whenever the datasheet has one. These
rules are for when it only gives package dimensions. They follow IPC-7351B nominal
(density level B) and are meant to be checked against the datasheet drawing.

All values in mm. `Lmin/Lmax` = terminal length, `bmax` = terminal width, `D/E` = body,
`e` = pitch.

## Gull-wing leads (SOIC, SOP, TSSOP, QFP)

- Lead span (toe to toe) S: use the datasheet's E (or HE) nominal.
- Pad length = (Lmax - Lmin)/2 + Lnom + toe 0.35 + heel 0.35, rounded to 0.05.
  Simple form: pad length ≈ L + 0.8.
- Pad width = bmax + 0.1 (side 0.05 each), but keep the gap between pads ≥ 0.15:
  pad width ≤ e - 0.15.
- Pad centre distance from package centre = (S/2) - L/2 + (toe - heel)/2 ≈ S/2 - L/2.

## No-lead (QFN, DFN, SON)

- Pad length = L + toe 0.3 (outward) + heel 0.05 (inward). Pad extends ~0.3 beyond the
  body edge.
- Pad width = b + 0.05, capped at e - 0.18 so the solder mask web survives.
- Exposed pad = D2 x E2 nominal (not larger). Paste: split into a grid of windows
  covering 50-70 % of the pad (`paste_windows` in the spec), and set the pad itself to
  `"paste": false`.

## BGA / ball grids (including Nordic aQFN-style land grids)

- Non-solder-mask-defined round pad ≈ 80 % of the nominal ball diameter for BGAs; for
  land-grid packages with a given land size b, use b nominal.
- Solder mask: per-pad manual expansion of 0.05 is typical at 0.5 mm pitch, since the
  default 0.1 rule leaves no mask web.

## Chip passives (0402, 0603, 0805 ...)

| Size | Pad (L x W) | Centre-to-centre |
|---|---|---|
| 0402 (1005) | 0.6 x 0.5 | 1.0 |
| 0603 (1608) | 0.9 x 0.95 | 1.6 |
| 0805 (2012) | 1.15 x 1.45 | 1.9 |
| 1206 (3216) | 1.15 x 1.8 | 3.0 |

(Pad "L" here is the dimension along the part's long axis.)

## Through-hole

- Drill = max lead diameter (or diagonal for square leads) + 0.2 to 0.25.
- Annular ring ≥ 0.15 per side: pad diameter = drill + 0.5 typical, pin 1 square.

## Silkscreen, courtyard, assembly

- Silk line 0.12-0.15, kept 0.2 from copper (the generator clips it automatically).
- Courtyard = outline of body and pads + 0.25 (0.5 for connectors/large parts).
- Assembly outline = body nominal, with a pin-1 chamfer.
