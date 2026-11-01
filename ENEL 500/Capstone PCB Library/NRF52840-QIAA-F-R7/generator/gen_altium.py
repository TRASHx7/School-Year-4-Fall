#!/usr/bin/env python3
"""Generate an Altium DelphiScript that builds a footprint (PcbLib) and a
schematic symbol (SchLib) from a JSON spec, plus SVG previews and a pin table.

Usage: gen_altium.py spec.json out_dir
"""
import csv
import json
import os
import sys

MIL_PER_MM = 1 / 0.0254


def esc(s):
    return s.replace("'", "''")


def f(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") if v != int(v) else f"{int(v)}"


# ---------------------------------------------------------------- footprint
def footprint_lines(fp):
    L = []
    for p in fp["pads"]:
        L.append(f"    AddSmdPad(Comp, '{esc(p['name'])}', {f(p['x'])}, {f(p['y'])}, "
                 f"{f(p['dx'])}, {f(p['dy'])}, {1 if p['shape'] == 'round' else 0}, 0);")
    ep = fp.get("ep")
    if ep:
        # paste_off=1: the exposed pad gets no paste of its own; windows below supply it
        L.append(f"    AddSmdPad(Comp, '{esc(ep['name'])}', {f(ep['x'])}, {f(ep['y'])}, "
                 f"{f(ep['dx'])}, {f(ep['dy'])}, 0, {1 if fp.get('paste_windows') else 0});")
    for w in fp.get("paste_windows", []):
        L.append(f"    AddPasteFill(Comp, {f(w['x'] - w['dx'] / 2)}, {f(w['y'] - w['dy'] / 2)}, "
                 f"{f(w['x'] + w['dx'] / 2)}, {f(w['y'] + w['dy'] / 2)});")
    # silkscreen corner marks outside the body, chamfer at pin-1 corner
    hb = fp["body"]["D"] / 2
    s = hb + fp["silk_offset"]
    k = fp["silk_corner_len"]
    w = fp["silk_width"]
    for sx, sy in ((1, 1), (1, -1), (-1, -1)):
        L.append(f"    AddLine(Comp, {f(sx * s)}, {f(sy * s)}, {f(sx * (s - k))}, {f(sy * s)}, {f(w)}, eTopOverlay);")
        L.append(f"    AddLine(Comp, {f(sx * s)}, {f(sy * s)}, {f(sx * s)}, {f(sy * (s - k))}, {f(w)}, eTopOverlay);")
    # pin-1 corner (top left): short lines plus a dot
    L.append(f"    AddLine(Comp, {f(-s)}, {f(s - k)}, {f(-s)}, {f(s - k / 2)}, {f(w)}, eTopOverlay);")
    L.append(f"    AddLine(Comp, {f(-s + k / 2)}, {f(s)}, {f(-s + k)}, {f(s)}, {f(w)}, eTopOverlay);")
    d = fp["pin1_dot"]
    L.append(f"    AddCircle(Comp, {f(d['x'])}, {f(d['y'])}, {f(d['r'] / 2)}, {f(d['r'])}, eTopOverlay);")
    # assembly outline (body with pin-1 chamfer) and courtyard
    c = fp["assembly_chamfer"]
    asm = [(-hb + c, hb), (hb, hb), (hb, -hb), (-hb, -hb), (-hb, hb - c), (-hb + c, hb)]
    for (x1, y1), (x2, y2) in zip(asm, asm[1:]):
        L.append(f"    AddLine(Comp, {f(x1)}, {f(y1)}, {f(x2)}, {f(y2)}, 0.1, {fp['assembly_layer']});")
    cy = hb + fp["courtyard_expansion"]
    box = [(-cy, cy), (cy, cy), (cy, -cy), (-cy, -cy), (-cy, cy)]
    for (x1, y1), (x2, y2) in zip(box, box[1:]):
        L.append(f"    AddLine(Comp, {f(x1)}, {f(y1)}, {f(x2)}, {f(y2)}, 0.05, {fp['courtyard_layer']});")
    return L


# ---------------------------------------------------------------- symbol
ETYPE = {"io": "eElectricIO", "in": "eElectricInput", "out": "eElectricOutput",
         "power": "eElectricPower", "passive": "eElectricPassive"}


def symbol_layout(sym):
    """Place pins on left/right/bottom in the order given, with a blank row
    between groups. Returns pins with (x, y, orient) in mils and the body box."""
    pitch = sym["pin_pitch_mil"]
    sides = {"left": [], "right": [], "bottom": []}
    for p in sym["pins"]:
        sides[p["side"]].append(p)

    def rows(lst):
        out, last = [], None
        for p in lst:
            if last is not None and p["group"] != last:
                out.append(None)
            out.append(p)
            last = p["group"]
        return out

    left, right = rows(sides["left"]), rows(sides["right"])
    n = max(len(left), len(right))
    width = sym["body_width_mil"]
    top = 0
    bottom = -(n + 1) * pitch
    placed = []
    for i, p in enumerate(left):
        if p:
            placed.append((p, 0, top - (i + 1) * pitch, "eRotate180"))
    for i, p in enumerate(right):
        if p:
            placed.append((p, width, top - (i + 1) * pitch, "eRotate0"))
    bot = sides["bottom"]
    if bot:
        span = (len(bot) - 1) * pitch
        x0 = round((width - span) / 2 / pitch) * pitch
        for i, p in enumerate(bot):
            placed.append((p, x0 + i * pitch, bottom, "eRotate270"))
    return placed, (0, bottom, width, top)


def symbol_lines(sym):
    placed, (x1, y1, x2, y2) = symbol_layout(sym)
    L = [f"    AddRect(SymComp, {x1}, {y1}, {x2}, {y2});"]
    for p, x, y, o in placed:
        L.append(f"    AddPin(SymComp, '{esc(p['num'])}', '{esc(p['name'])}', {x}, {y}, {o}, "
                 f"{ETYPE[p['type']]}, {sym['pin_length_mil']});")
    return L


# ---------------------------------------------------------------- script
SCRIPT = r"""{ ==========================================================================
  {title}
  Generated from: {source}
  Generated on:   {date}

  HOW TO USE (Altium Designer)
  1. File > New > Library > PCB Library. Click on the new PcbLib tab so it is
     the active document, then File > Run Script, browse to this file and
     pick CreateFootprint.
  2. File > New > Library > Schematic Library. Click on the new SchLib tab,
     then File > Run Script again and pick CreateSymbol.
  Do not run it with the Run button in the script editor: then the script
  itself is the active document and the library is not found.
  3. Save both libraries. The symbol already links to footprint
     '{fp_name}', so keep the PcbLib in the same project or add it to your
     installed libraries.

  All footprint coordinates are in millimetres, top view, origin at the
  package centre, +Y up. Symbol coordinates are in mils.
  ========================================================================== }

{ ---------------------------------------------------------------- footprint }

Var
    FpLib     : IPCB_Library;
    SymComp   : ISch_Component;
    MaskExpMM : Double;
    Step      : String;

Function X0(V : Double) : Integer;
Begin
    Result := FpLib.Board.XOrigin + MMsToCoord(V);
End;

Function Y0(V : Double) : Integer;
Begin
    Result := FpLib.Board.YOrigin + MMsToCoord(V);
End;

Procedure AddToComp(Comp : IPCB_LibComponent; Obj : IPCB_Primitive);
Begin
    Comp.AddPCBObject(Obj);
    PCBServer.SendMessageToRobots(Comp.I_ObjectAddress, c_Broadcast,
        PCBM_BoardRegisteration, Obj.I_ObjectAddress);
End;

{ Shape: 1 = round, 0 = rectangular.  NoPaste: 1 removes the pad's own paste. }
Procedure AddSmdPad(Comp : IPCB_LibComponent; PadName : String; X, Y, W, H : Double; Shape, NoPaste : Integer);
Var
    Pad   : IPCB_Pad;
    Cache : TPadCache;
Begin
    Pad := PCBServer.PCBObjectFactory(ePadObject, eNoDimension, eCreate_Default);
    Pad.Mode     := ePadMode_Simple;
    Pad.Layer    := eTopLayer;
    Pad.HoleSize := 0;
    Pad.X        := X0(X);
    Pad.Y        := Y0(Y);
    Pad.TopXSize := MMsToCoord(W);
    Pad.TopYSize := MMsToCoord(H);
    If Shape = 1 Then Pad.TopShape := eRounded Else Pad.TopShape := eRectangular;
    Pad.Name     := PadName;
    AddToComp(Comp, Pad);
    { Fixed solder mask opening; the usual 0.1 mm rule leaves no mask web at this pitch.
      Set through the pad cache: in AD25 the SolderMaskExpansion and PasteMaskExpansion
      property setters crash the scripting system with an access violation. }
    Pad.BeginModify;
    Cache := Pad.GetState_Cache;
    Cache.SolderMaskExpansion      := MMsToCoord(MaskExpMM);
    Cache.SolderMaskExpansionValid := eCacheManual;
    If NoPaste = 1 Then
    Begin
        Cache.PasteMaskExpansion      := -MMsToCoord(W);
        Cache.PasteMaskExpansionValid := eCacheManual;
    End;
    Pad.SetState_Cache := Cache;
    Pad.EndModify;
End;

Procedure AddPasteFill(Comp : IPCB_LibComponent; Xa, Ya, Xb, Yb : Double);
Var
    Fill : IPCB_Fill;
Begin
    Fill := PCBServer.PCBObjectFactory(eFillObject, eNoDimension, eCreate_Default);
    Fill.X1Location := X0(Xa);
    Fill.Y1Location := Y0(Ya);
    Fill.X2Location := X0(Xb);
    Fill.Y2Location := Y0(Yb);
    Fill.Rotation   := 0;
    Fill.Layer      := eTopPaste;
    AddToComp(Comp, Fill);
End;

Procedure AddLine(Comp : IPCB_LibComponent; Xa, Ya, Xb, Yb, W : Double; Lyr : TLayer);
Var
    Track : IPCB_Track;
Begin
    Track := PCBServer.PCBObjectFactory(eTrackObject, eNoDimension, eCreate_Default);
    Track.X1    := X0(Xa);
    Track.Y1    := Y0(Ya);
    Track.X2    := X0(Xb);
    Track.Y2    := Y0(Yb);
    Track.Width := MMsToCoord(W);
    Track.Layer := Lyr;
    AddToComp(Comp, Track);
End;

{ A filled dot is an arc whose line width equals twice its radius. }
Procedure AddCircle(Comp : IPCB_LibComponent; Xc, Yc, Radius, W : Double; Lyr : TLayer);
Var
    Arc : IPCB_Arc;
Begin
    Arc := PCBServer.PCBObjectFactory(eArcObject, eNoDimension, eCreate_Default);
    Arc.XCenter    := X0(Xc);
    Arc.YCenter    := Y0(Yc);
    Arc.Radius     := MMsToCoord(Radius);
    Arc.LineWidth  := MMsToCoord(W);
    Arc.StartAngle := 0;
    Arc.EndAngle   := 360;
    Arc.Layer      := Lyr;
    AddToComp(Comp, Arc);
End;

Procedure CreateFootprint;
Var
    Comp : IPCB_LibComponent;
Begin
    { Run from File > Run Script with the PcbLib as the active tab, not from the script editor. }
    If PCBServer = Nil Then Exit;
    FpLib := PCBServer.GetCurrentPCBLibrary;
    If FpLib = Nil Then
    Begin
        ShowMessage('No PCB Library is active. Click on the PcbLib tab, then run CreateFootprint from File > Run Script.');
        Exit;
    End;
    If FpLib.Board = Nil Then
    Begin
        ShowMessage('The active PCB Library has no board object. Close and reopen the PcbLib, then try again.');
        Exit;
    End;

    Step := 'creating the footprint';
    Try
    MaskExpMM := {mask_exp};
    Comp := PCBServer.CreatePCBLibComp;
    Comp.Name        := '{fp_name}';
    Comp.Description := '{fp_desc}';
    Comp.Height      := MMsToCoord({height});
    FpLib.RegisterComponent(Comp);

    Step := 'adding pads and outlines';
    PCBServer.PreProcess;
{fp_body}
    PCBServer.PostProcess;

    Step := 'refreshing the view';
    FpLib.CurrentComponent := Comp;
    FpLib.Board.ViewManager_FullUpdate;
    Except
        ShowMessage('CreateFootprint stopped while ' + Step + '. Please report this step and the error text.');
        Exit;
    End;
    ShowMessage('Footprint {fp_name} created ({npads} pads). Check it against the datasheet drawing, then save the library.');
End;

{ ---------------------------------------------------------------- symbol }

Procedure AddRect(Comp : ISch_Component; Xa, Ya, Xb, Yb : Integer);
Var
    R : ISch_Rectangle;
Begin
    R := SchServer.SchObjectFactory(eRectangle, eCreate_Default);
    R.Location  := Point(MilsToCoord(Xa), MilsToCoord(Ya));
    R.Corner    := Point(MilsToCoord(Xb), MilsToCoord(Yb));
    R.LineWidth := eSmall;
    R.IsSolid   := True;
    R.AreaColor := $00B0FFFF;
    R.Color     := $00000080;
    R.OwnerPartId          := Comp.CurrentPartID;
    R.OwnerPartDisplayMode := Comp.DisplayMode;
    Comp.AddSchObject(R);
End;

Procedure AddPin(Comp : ISch_Component; Num, PinName : String; X, Y : Integer; Orient : TRotationBy90; EType : TPinElectrical; LenMil : Integer);
Var
    P : ISch_Pin;
Begin
    P := SchServer.SchObjectFactory(ePin, eCreate_Default);
    P.Location    := Point(MilsToCoord(X), MilsToCoord(Y));
    P.Orientation := Orient;
    P.Designator  := Num;
    P.Name        := PinName;
    P.Electrical  := EType;
    P.PinLength   := MilsToCoord(LenMil);
    P.OwnerPartId          := Comp.CurrentPartID;
    P.OwnerPartDisplayMode := Comp.DisplayMode;
    Comp.AddSchObject(P);
End;

Procedure AddParam(Comp : ISch_Component; PName, PText : String);
Var
    P : ISch_Parameter;
Begin
    P := SchServer.SchObjectFactory(eParameter, eCreate_Default);
    P.Name     := PName;
    P.Text     := PText;
    P.IsHidden := True;
    P.OwnerPartId          := Comp.CurrentPartID;
    P.OwnerPartDisplayMode := Comp.DisplayMode;
    Comp.AddSchObject(P);
End;

Procedure CreateSymbol;
Var
    SchLib : ISch_Lib;
    Impl   : ISch_Implementation;
Begin
    { Run from File > Run Script with the SchLib as the active tab, not from the script editor.
      DelphiScript evaluates both sides of And/Or, so each nil check is its own If. }
    If SchServer = Nil Then Exit;
    SchLib := SchServer.GetCurrentSchDocument;
    If SchLib = Nil Then
    Begin
        ShowMessage('No Schematic Library is active. Click on the SchLib tab, then run CreateSymbol from File > Run Script.');
        Exit;
    End;
    If SchLib.ObjectID <> eSchLib Then
    Begin
        ShowMessage('The active document is a schematic sheet, not a Schematic Library. Click on the SchLib tab and try again.');
        Exit;
    End;

    Step := 'creating the component';
    Try
    SymComp := SchServer.SchObjectFactory(eSchComponent, eCreate_Default);
    If SymComp = Nil Then Exit;
    SymComp.CurrentPartID        := 1;
    SymComp.DisplayMode          := 0;
    SymComp.LibReference         := '{sym_name}';
    SymComp.ComponentDescription := '{sym_desc}';
    SymComp.Designator.Text      := '{designator}';

    Step := 'adding the body and pins';
{sym_body}

    Step := 'adding parameters';
{params}

    Step := 'linking the footprint';

    Impl := SymComp.AddSchImplementation;
    Impl.ClearAllDatafileLinks;
    Impl.Description := 'Footprint';
    Impl.ModelName   := '{fp_name}';
    Impl.ModelType   := 'PCBLIB';
    Impl.AddDataFileLink('{fp_name}', '', 'PCBLIB');
    Impl.IsCurrent   := True;

    Step := 'adding the component to the library';
    SchLib.AddSchComponent(SymComp);
    SchServer.RobotManager.SendMessage(nil, c_BroadCast, SCHM_PrimitiveRegistration, SymComp.I_ObjectAddress);
    SchLib.CurrentSchComponent := SymComp;
    SchLib.GraphicallyInvalidate;
    Except
        ShowMessage('CreateSymbol stopped while ' + Step + '. Please report this step and the error text.');
        Exit;
    End;
    ShowMessage('Symbol {sym_name} created ({npins} pins). Save the library.');
End;
"""


def build_script(spec):
    fp, sym = spec["footprint"], spec["symbol"]
    params = "\n".join(f"    AddParam(SymComp, '{esc(k)}', '{esc(v)}');" for k, v in sym["parameters"].items())
    npads = len(fp["pads"]) + (1 if fp.get("ep") else 0)
    out = SCRIPT
    for k, v in {
        "{title}": spec["title"], "{source}": spec["source"], "{date}": spec["date"],
        "{fp_name}": esc(fp["name"]), "{fp_desc}": esc(fp["description"]),
        "{height}": f(fp["body"]["A"]), "{fp_body}": "\n".join(footprint_lines(fp)),
        "{npads}": str(npads), "{mask_exp}": f(fp["mask_expansion"]), "{sym_name}": esc(sym["name"]), "{sym_desc}": esc(sym["description"]),
        "{designator}": sym["designator"], "{sym_body}": "\n".join(symbol_lines(sym)),
        "{params}": params, "{npins}": str(len(sym["pins"])),
    }.items():
        out = out.replace(k, v)
    return out


# ---------------------------------------------------------------- previews
def footprint_svg(fp, scale=90):
    hb = fp["body"]["D"] / 2
    m = hb + 1.0
    W = 2 * m * scale

    def X(x):
        return (x + m) * scale

    def Y(y):
        return (m - y) * scale  # +Y up in Altium

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{W + 40:.0f}" '
         f'font-family="Arial" style="background:#101418">']
    cy = hb + fp["courtyard_expansion"]
    o.append(f'<rect x="{X(-cy)}" y="{Y(cy)}" width="{2 * cy * scale}" height="{2 * cy * scale}" '
             f'fill="none" stroke="#c080ff" stroke-width="1" stroke-dasharray="4,3"/>')
    o.append(f'<rect x="{X(-hb)}" y="{Y(hb)}" width="{2 * hb * scale}" height="{2 * hb * scale}" '
             f'fill="none" stroke="#666" stroke-width="1"/>')
    ep = fp.get("ep")
    if ep:
        o.append(f'<rect x="{X(ep["x"] - ep["dx"] / 2)}" y="{Y(ep["y"] + ep["dy"] / 2)}" '
                 f'width="{ep["dx"] * scale}" height="{ep["dy"] * scale}" fill="#b03030"/>')
    for w in fp.get("paste_windows", []):
        o.append(f'<rect x="{X(w["x"] - w["dx"] / 2)}" y="{Y(w["y"] + w["dy"] / 2)}" '
                 f'width="{w["dx"] * scale}" height="{w["dy"] * scale}" fill="#9a9a9a" opacity="0.7"/>')
    for p in fp["pads"]:
        if p["shape"] == "round":
            o.append(f'<circle cx="{X(p["x"])}" cy="{Y(p["y"])}" r="{p["dx"] / 2 * scale}" fill="#d04040"/>')
        else:
            o.append(f'<rect x="{X(p["x"] - p["dx"] / 2)}" y="{Y(p["y"] + p["dy"] / 2)}" '
                     f'width="{p["dx"] * scale}" height="{p["dy"] * scale}" fill="#d04040"/>')
        o.append(f'<text x="{X(p["x"])}" y="{Y(p["y"]) - p["dx"] / 2 * scale - 2}" font-size="9" '
                 f'fill="#e8e8e8" text-anchor="middle">{p["name"]}</text>')
    s = hb + fp["silk_offset"]
    d = fp["pin1_dot"]
    o.append(f'<circle cx="{X(d["x"])}" cy="{Y(d["y"])}" r="{d["r"] * scale}" fill="#f0e060"/>')
    for sx, sy in ((1, 1), (1, -1), (-1, -1)):
        k = fp["silk_corner_len"]
        o.append(f'<polyline points="{X(sx * (s - k))},{Y(sy * s)} {X(sx * s)},{Y(sy * s)} '
                 f'{X(sx * s)},{Y(sy * (s - k))}" fill="none" stroke="#f0e060" stroke-width="2"/>')
    k = fp["silk_corner_len"]
    o.append(f'<line x1="{X(-s)}" y1="{Y(s - k)}" x2="{X(-s)}" y2="{Y(s - k / 2)}" stroke="#f0e060" stroke-width="2"/>')
    o.append(f'<line x1="{X(-s + k / 2)}" y1="{Y(s)}" x2="{X(-s + k)}" y2="{Y(s)}" stroke="#f0e060" stroke-width="2"/>')
    o.append(f'<text x="10" y="{W + 25:.0f}" font-size="14" fill="#e8e8e8">{fp["name"]}  (top view, '
             f'+Y up; grid of body {fp["body"]["D"]} x {fp["body"]["E"]} mm; dashed = courtyard)</text>')
    o.append("</svg>")
    return "\n".join(o)


def symbol_svg(sym, s=0.11):
    placed, (x1, y1, x2, y2) = symbol_layout(sym)
    pl = sym["pin_length_mil"]
    pad = pl + 1400
    W = (x2 - x1 + 2 * pad) * s
    H = (y2 - y1 + 2 * pl + 400) * s

    def X(x):
        return (x - x1 + pad) * s

    def Y(y):
        return (y2 - y + 200) * s

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" font-family="Arial" '
         f'style="background:white">',
         f'<rect x="{X(x1)}" y="{Y(y2)}" width="{(x2 - x1) * s}" height="{(y2 - y1) * s}" '
         f'fill="#ffffb0" stroke="#800000" stroke-width="1.5"/>',
         f'<text x="{X(x1)}" y="{Y(y2) - 6}" font-size="12">{sym["designator"]}  {sym["name"]}</text>']
    for p, x, y, orient in placed:
        dx, dy = {"eRotate180": (-pl, 0), "eRotate0": (pl, 0), "eRotate270": (0, -pl)}[orient]
        o.append(f'<line x1="{X(x)}" y1="{Y(y)}" x2="{X(x + dx)}" y2="{Y(y + dy)}" stroke="#000" stroke-width="1"/>')
        if orient == "eRotate180":
            o.append(f'<text x="{X(x) + 4}" y="{Y(y) + 3.5}" font-size="9.5">{p["name"]}</text>')
            o.append(f'<text x="{X(x + dx / 2)}" y="{Y(y) - 2}" font-size="8" text-anchor="middle" fill="#444">{p["num"]}</text>')
        elif orient == "eRotate0":
            o.append(f'<text x="{X(x) - 4}" y="{Y(y) + 3.5}" font-size="9.5" text-anchor="end">{p["name"]}</text>')
            o.append(f'<text x="{X(x + dx / 2)}" y="{Y(y) - 2}" font-size="8" text-anchor="middle" fill="#444">{p["num"]}</text>')
        else:
            o.append(f'<text transform="translate({X(x) + 3.5},{Y(y) - 4}) rotate(-90)" font-size="9.5">{p["name"]}</text>')
            o.append(f'<text transform="translate({X(x) - 2},{Y(y + dy / 2)}) rotate(-90)" font-size="8" '
                     f'text-anchor="middle" fill="#444">{p["num"]}</text>')
    o.append("</svg>")
    return "\n".join(o)


def main():
    spec = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    base = spec["basename"]
    with open(os.path.join(out, base + ".pas"), "w", newline="") as fh:
        fh.write(build_script(spec))
    with open(os.path.join(out, base + ".PrjScr"), "w", newline="") as fh:
        fh.write(f"[Design]\nVersion=1.0\n\n[Document1]\nDocumentPath={base}.pas\n")
    open(os.path.join(out, base + "_footprint_preview.svg"), "w").write(footprint_svg(spec["footprint"]))
    open(os.path.join(out, base + "_symbol_preview.svg"), "w").write(symbol_svg(spec["symbol"]))
    fp = spec["footprint"]
    pads = {p["name"]: p for p in fp["pads"]}
    if fp.get("ep"):
        pads[fp["ep"]["name"]] = fp["ep"]
    with open(os.path.join(out, base + "_pin_table.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator (ball)", "Pin name", "Electrical type", "Symbol side", "Group",
                    "Pad X (mm)", "Pad Y (mm)", "Pad size (mm)"])
        placed, _ = symbol_layout(spec["symbol"])
        for p, _x, _y, _o in placed:
            pd = pads[p["num"]]
            w.writerow([p["num"], p["name"], p["type"], p["side"], p["group"], f(pd["x"]), f(pd["y"]),
                        f"{f(pd['dx'])} x {f(pd['dy'])}"])
    # consistency checks
    sym_nums = [p["num"] for p in spec["symbol"]["pins"]]
    assert len(sym_nums) == len(set(sym_nums)), "duplicate symbol pin designators"
    missing = set(sym_nums) - set(pads)
    unused = set(pads) - set(sym_nums)
    print("pads:", len(pads), "pins:", len(sym_nums), "missing pads:", sorted(missing), "pads without pin:", sorted(unused))


if __name__ == "__main__":
    main()
