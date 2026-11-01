---
name: altium-footprint-symbol
description: Build an Altium Designer footprint (PcbLib) and schematic symbol (SchLib) for any part from its datasheet, or from a snippet of the datasheet's package drawing and pin table when the full datasheet is too big. Produces a DelphiScript the user runs in Altium (or Claude runs it via computer use), plus previews and a pin table. Use when the user asks for a footprint, land pattern, PCB library part, schematic symbol, or "add this chip to Altium".
---

# Altium footprint and schematic symbol from a datasheet

You turn datasheet package dimensions and the pin list into a JSON spec, generate an
Altium DelphiScript with `scripts/gen_altium.py`, check the previews, and then run the
script in Altium (yourself through computer use if the user asks, otherwise give the
user the steps).

Read `references/altium_pitfalls.md` before writing or editing any Altium script, and
before driving Altium on screen. It lists every failure found so far and how to avoid it.

## Step 1: get the datasheet, or stop

Look for the source in this order:

1. A file or snippet attached to the conversation (PDF, image, pasted text).
2. A PDF in the working directory or repos in this session. Search with Glob for
   `**/*.pdf` and match the part number in the file name or text
   (`pdftotext -layout file.pdf - | grep -i <part>`; `pdftotext` is in Git's mingw64).
3. Nothing found: **stop and ask the user to attach the datasheet**, or a screenshot or
   snippet of the package drawing (the "Package dimensions" or "Mechanical" section)
   and the pin table. Do not take dimensions from memory or a web search and present
   them as the datasheet's.

The datasheet is too big to read whole (more than about 50 pages): read only the table of
contents, then the package or mechanical section and the pin-assignment table. If you
can't find those sections, ask the user for a snippet of the physical dimensions and the
pinout.

**No dimensions in the source** (for example a product brief or a short-form sheet):
say plainly "This datasheet has no package dimensions", name what is missing (body size,
pitch, pad or lead size, exposed pad), and ask for the package drawing or the
manufacturer's package document. Do not guess a package from the part family.

## Step 2: extract the numbers

Write down, with the page, figure or table each value comes from:

- Package name and code (e.g. QFN-32 5x5, SOIC-8, aQFN73, 0603, TO-220).
- Body size D x E and height A (use A max for the 3D height).
- Pitch e, lead/ball/terminal width b, length L, row/column spans (e1, e2 ...).
- Exposed or thermal pad size D2 x E2, if any.
- Any recommended land pattern. If the datasheet gives one, **use it as-is** and
  don't derive pads yourself.
- Pin table: pin/ball number, name, function/electrical type.

When a value has min/nom/max, use nominal for positions, and for pad sizes follow the
land-pattern rules in `references/land_patterns.md` (IPC-7351-style toe/heel/side
fillets). State which you used.

Cross-check before going on, and stop and tell the user if any check fails:
- Pin count in the table equals pad count in the drawing.
- Every pin number in the table has a position in the drawing, and vice versa.
- Pads stay inside the body outline plus the expected toe extension.
- Pad-to-pad gap is at least about 0.15 mm (flag smaller gaps, don't silently shrink pads).

## Step 3: write the spec

Write `<PART>_spec.json` in the format in `references/spec_format.md`, in a folder next to
the user's other library parts (ask if there is no obvious place; in this user's repo
that is `ENEL 500/Capstone PCB Library/<PART>/`). Positions are in mm, top view, origin
at the package centre, +Y up, pin 1 normally top-left or left side.

Choose the symbol layout for readability: power and ground pins together, related
pins in groups (port pins in order, debug, clock, RF, USB), inputs on the left and
outputs on the right where it makes sense, ground at the bottom.

## Step 4: generate and check

```
python scripts/gen_altium.py <spec.json> <out_dir>
powershell -ExecutionPolicy Bypass -File scripts/render_previews.ps1 <out_dir>
```

The generator writes `<base>.pas`, `<base>.PrjScr`, two SVG previews, and
`<base>_pin_table.csv`, and prints a pad/pin consistency line. It exits with an error
if a pin has no pad, there are duplicate pins, or pads overlap. `render_previews.ps1`
turns the SVGs into PNGs with headless Edge so you can Read them.

Read both PNGs and compare them with the datasheet drawing (pin 1 location, row
order, exposed pad, symbol grouping). Fix the spec and regenerate until they match.

## Step 5: put it in Altium

If the user asked you to do it, use computer use (see the pitfalls file for how to see
the screen and click reliably); otherwise give these steps:

1. In the target project, File > New > Library > PCB Library (or open the existing
   PcbLib). Click its tab so it is the active document. File > Run Script > Browse >
   From file > pick `<base>.PrjScr` > choose `CreateFootprint` > OK.
2. File > New > Library > Schematic Library (or open the existing SchLib), click its
   tab, File > Run Script > `CreateSymbol` > OK.
3. Check the footprint visually, then save both libraries. Ask the user where to save
   new libraries; don't pick a location for them.

Never use the Run button in the script editor: the script becomes the active document
and the library isn't found.

## Step 6: report

Tell the user the footprint and symbol names, pad and pin counts, which datasheet
figure and table they came from, any values you had to choose (pad sizes from
nominal, mask expansion, paste reduction), and what to check before ordering boards
(compare with the manufacturer's recommended land pattern, print 1:1, board-house
mask limits).
