#!/usr/bin/env python3
"""Generate an Altium DelphiScript that builds a footprint (PcbLib) and a
schematic symbol (SchLib) from a JSON spec, plus SVG previews and a pin table.

Usage: gen_altium.py spec.json out_dir

Spec format: ../references/spec_format.md
Altium pitfalls this template avoids: ../references/altium_pitfalls.md
"""
import csv
import json
import math
import os
import sys

FP_DEFAULTS = {
    "silk_width": 0.12, "silk_offset": 0.1, "silk_clearance": 0.2,
    "courtyard_expansion": 0.25, "assembly_layer": "eMechanical13",
    "courtyard_layer": "eMechanical15", "paste_windows": [],
}
SYM_DEFAULTS = {"designator": "U?", "pin_pitch_mil": 100, "pin_length_mil": 200, "parameters": {}}
ETYPE = {"io": "eElectricIO", "in": "eElectricInput", "out": "eElectricOutput",
         "power": "eElectricPower", "passive": "eElectricPassive", "oc": "eElectricOpenCollector",
         "hiz": "eElectricHiZ", "emitter": "eElectricOpenEmitter"}
ORIENT = {"left": "eRotate180", "right": "eRotate0", "top": "eRotate90", "bottom": "eRotate270"}


def esc(s):
    return str(s).replace("'", "''")


def f(v):
    v = round(v, 4) + 0.0
    return f"{int(v)}" if v == int(v) else f"{v:.4f}".rstrip("0").rstrip(".")


def fail(msg):
    sys.exit("ERROR: " + msg)


# ---------------------------------------------------------------- geometry
def pad_box(p, grow=0.0):
    """Axis-aligned bounding box (x1, y1, x2, y2) of a pad, grown by `grow`."""
    a = math.radians(p.get("rotation", 0))
    hx = abs(p["dx"] / 2 * math.cos(a)) + abs(p["dy"] / 2 * math.sin(a))
    hy = abs(p["dx"] / 2 * math.sin(a)) + abs(p["dy"] / 2 * math.cos(a))
    return (p["x"] - hx - grow, p["y"] - hy - grow, p["x"] + hx + grow, p["y"] + hy + grow)


def box_gap(a, b):
    """Edge-to-edge distance between two boxes (negative = overlap)."""
    dx = max(a[0] - b[2], b[0] - a[2])
    dy = max(a[1] - b[3], b[1] - a[3])
    return max(dx, dy) if (dx < 0 or dy < 0) else math.hypot(dx, dy)


def clip_segment(fixed, lo, hi, horizontal, boxes, min_len=0.3):
    """Split a horizontal (y = fixed) or vertical (x = fixed) segment around boxes."""
    cuts = []
    for b in boxes:
        if horizontal and b[1] <= fixed <= b[3]:
            cuts.append((b[0], b[2]))
        if not horizontal and b[0] <= fixed <= b[2]:
            cuts.append((b[1], b[3]))
    pieces, start = [], lo
    for c0, c1 in sorted(cuts):
        if c1 <= start or c0 >= hi:
            continue
        if c0 > start:
            pieces.append((start, c0))
        start = max(start, c1)
    if start < hi:
        pieces.append((start, hi))
    return [(a, b) for a, b in pieces if b - a >= min_len]


def pin1_pad(fp):
    names = [p["name"] for p in fp["pads"]]
    want = fp.get("pin1_pad") or ("1" if "1" in names else "A1" if "A1" in names else names[0])
    for p in fp["pads"]:
        if p["name"] == want:
            return p
    fail(f"pin1_pad '{want}' is not a pad name")


def footprint_geometry(fp):
    """Silk segments, pin-1 dot, assembly polygon and courtyard box."""
    D, E = fp["body"]["D"], fp["body"]["E"]
    hx, hy = D / 2 + fp["silk_offset"], E / 2 + fp["silk_offset"]
    w = fp["silk_width"]
    keep_out = [pad_box(p, fp["silk_clearance"] + w / 2) for p in fp["pads"]]
    silk = []
    for y in (hy, -hy):
        silk += [(a, y, b, y) for a, b in clip_segment(y, -hx, hx, True, keep_out)]
    for x in (hx, -hx):
        silk += [(x, a, x, b) for a, b in clip_segment(x, -hy, hy, False, keep_out)]

    p1 = pin1_pad(fp)
    sx = -1 if p1["x"] < 0 else 1 if p1["x"] > 0 else -1
    sy = -1 if p1["y"] < 0 else 1 if p1["y"] > 0 else 1
    if "pin1_dot" in fp:
        dot = fp["pin1_dot"]
    else:
        r = 0.15
        b = pad_box(p1)
        if abs(p1["x"]) / D >= abs(p1["y"]) / E:   # pin 1 on a left/right edge
            edge = max(abs(b[0]), abs(b[2]), hx)
            dot = {"x": sx * (edge + fp["silk_clearance"] + r), "y": p1["y"], "r": r}
        else:                                      # pin 1 on a top/bottom edge
            edge = max(abs(b[1]), abs(b[3]), hy)
            dot = {"x": p1["x"], "y": sy * (edge + fp["silk_clearance"] + r), "r": r}

    c = min(1.0, 0.25 * min(D, E))
    corners = [(-D / 2, E / 2), (D / 2, E / 2), (D / 2, -E / 2), (-D / 2, -E / 2)]
    asm = []
    for x, y in corners:   # chamfer the corner in pin 1's quadrant
        if x * sx > 0 and y * sy > 0:
            asm += [(x, y - sy * c), (x - sx * c, y)] if sx * sy < 0 else [(x - sx * c, y), (x, y - sy * c)]
        else:
            asm.append((x, y))
    asm.append(asm[0])

    boxes = [pad_box(p) for p in fp["pads"]] + [(-D / 2, -E / 2, D / 2, E / 2),
             (dot["x"] - dot["r"], dot["y"] - dot["r"], dot["x"] + dot["r"], dot["y"] + dot["r"])]
    g = fp["courtyard_expansion"]

    def out(v, up):
        return (math.ceil if up else math.floor)(v * 20) / 20   # 0.05 mm grid, outward
    cy = (out(min(b[0] for b in boxes) - g, False), out(min(b[1] for b in boxes) - g, False),
          out(max(b[2] for b in boxes) + g, True), out(max(b[3] for b in boxes) + g, True))
    return silk, dot, asm, cy


def check_pads(fp):
    pads = fp["pads"]
    msgs = []
    for i in range(len(pads)):
        for j in range(i + 1, len(pads)):
            a, b = pads[i], pads[j]
            gap = box_gap(pad_box(a), pad_box(b))
            if gap < 0 and a["name"] != b["name"]:
                fail(f"pads {a['name']} and {b['name']} overlap")
            if 0 <= gap < 0.15 and a["name"] != b["name"]:
                msgs.append(f"WARNING: pads {a['name']} and {b['name']} are only {gap:.3f} mm apart")
    return msgs


# ---------------------------------------------------------------- footprint lines
def footprint_lines(fp):
    L = []
    for p in fp["pads"]:
        shape = 0 if p["shape"] == "rect" else 1
        L.append(f"    AddPad(Comp, '{esc(p['name'])}', {f(p['x'])}, {f(p['y'])}, {f(p['dx'])}, {f(p['dy'])}, "
                 f"{shape}, {f(p.get('hole', 0))}, {f(p.get('rotation', 0))}, {0 if p.get('paste', True) else 1});")
    for w in fp["paste_windows"]:
        L.append(f"    AddPasteFill(Comp, {f(w['x'] - w['dx'] / 2)}, {f(w['y'] - w['dy'] / 2)}, "
                 f"{f(w['x'] + w['dx'] / 2)}, {f(w['y'] + w['dy'] / 2)});")
    silk, dot, asm, cy = footprint_geometry(fp)
    sw = fp["silk_width"]
    for x1, y1, x2, y2 in silk:
        L.append(f"    AddLine(Comp, {f(x1)}, {f(y1)}, {f(x2)}, {f(y2)}, {f(sw)}, eTopOverlay);")
    L.append(f"    AddCircle(Comp, {f(dot['x'])}, {f(dot['y'])}, {f(dot['r'] / 2)}, {f(dot['r'])}, eTopOverlay);")
    for (x1, y1), (x2, y2) in zip(asm, asm[1:]):
        L.append(f"    AddLine(Comp, {f(x1)}, {f(y1)}, {f(x2)}, {f(y2)}, 0.1, {fp['assembly_layer']});")
    x1, y1, x2, y2 = cy
    box = [(x1, y2), (x2, y2), (x2, y1), (x1, y1), (x1, y2)]
    for (a, b), (c, d) in zip(box, box[1:]):
        L.append(f"    AddLine(Comp, {f(a)}, {f(b)}, {f(c)}, {f(d)}, 0.05, {fp['courtyard_layer']});")
    return L


# ---------------------------------------------------------------- symbol
def symbol_layout(sym):
    """Place pins in list order; blank row between groups on left/right.
    Returns [(pin, x, y, orient)] in mils and the body box (x1, y1, x2, y2)."""
    pitch = sym["pin_pitch_mil"]
    sides = {"left": [], "right": [], "top": [], "bottom": []}
    for p in sym["pins"]:
        if p["side"] not in sides:
            fail(f"pin {p['num']}: side must be left/right/top/bottom")
        sides[p["side"]].append(p)

    def rows(lst):
        out, last = [], None
        for p in lst:
            if last is not None and p.get("group") != last:
                out.append(None)
            out.append(p)
            last = p.get("group")
        return out

    left, right = rows(sides["left"]), rows(sides["right"])
    top_n, bot_n = len(sides["top"]), len(sides["bottom"])
    longest = lambda lst: max((len(p["name"]) for p in lst), default=0)
    auto_w = (longest(sides["left"]) + longest(sides["right"])) * 60 + 300
    auto_w = max(auto_w, (max(top_n, bot_n) + 1) * pitch)
    width = sym.get("body_width_mil") or int(math.ceil(auto_w / pitch) * pitch)
    # leave room under top pins' names and above bottom pins' names
    y_off = (longest(sides["top"]) * 60 + pitch) // pitch * pitch if top_n else 0
    n = max(len(left), len(right))
    top = 0
    bottom = -(y_off + (n + 1) * pitch + ((longest(sides["bottom"]) * 60) // pitch * pitch if bot_n else 0))
    placed = []
    for i, p in enumerate(left):
        if p:
            placed.append((p, 0, top - y_off - (i + 1) * pitch, ORIENT["left"]))
    for i, p in enumerate(right):
        if p:
            placed.append((p, width, top - y_off - (i + 1) * pitch, ORIENT["right"]))
    for side, y in (("top", top), ("bottom", bottom)):
        lst = sides[side]
        if lst:
            x0 = round((width - (len(lst) - 1) * pitch) / 2 / pitch) * pitch
            for i, p in enumerate(lst):
                placed.append((p, x0 + i * pitch, y, ORIENT[side]))
    return placed, (0, bottom, width, top)


def symbol_lines(sym):
    placed, (x1, y1, x2, y2) = symbol_layout(sym)
    L = [f"    AddRect(SymComp, {x1}, {y1}, {x2}, {y2});"]
    for p, x, y, o in placed:
        if p["type"] not in ETYPE:
            fail(f"pin {p['num']}: unknown type '{p['type']}' (use {', '.join(ETYPE)})")
        L.append(f"    AddPin(SymComp, '{esc(p['num'])}', '{esc(p['name'])}', {x}, {y}, {o}, "
                 f"{ETYPE[p['type']]}, {sym['pin_length_mil']});")
    return L


# ---------------------------------------------------------------- script template
SCRIPT = r"""{ ==========================================================================
  {title}
  Generated from: {source}
  Generated on:   {date}

  HOW TO USE (Altium Designer)
  1. Open or create a PCB Library (File > New > Library > PCB Library). Click its
     tab so it is the active document, then File > Run Script > Browse > From file,
     pick {basename}.PrjScr and run CreateFootprint.
  2. Open or create a Schematic Library, click its tab, then File > Run Script and
     run CreateSymbol.
  Do not use the Run button in the script editor: the script itself is then the
  active document and the library is not found.
  If you edit this file after Altium has loaded it, Altium keeps running the old
  copy: close the script project in Altium first, or load a renamed copy.
  3. Save both libraries. The symbol links to footprint '{fp_name}', so keep the
     PcbLib in the same project or add it to your installed libraries.

  Footprint coordinates are in millimetres, top view, origin at the package
  centre, +Y up. Symbol coordinates are in mils.
  ========================================================================== }

{ ---------------------------------------------------------------- footprint }

Var
    FpLib     : IPCB_Library;
    SymComp   : ISch_Component;
    MaskExpMM : Double;
    SetMask   : Integer;
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

{ Shape: 1 = round/oval, 0 = rectangular.  HoleMM > 0 makes a plated through-hole
  pad on all layers.  NoPaste: 1 removes the pad's own paste. }
Procedure AddPad(Comp : IPCB_LibComponent; PadName : String; X, Y, W, H : Double; Shape : Integer; HoleMM, RotDeg : Double; NoPaste : Integer);
Var
    Pad   : IPCB_Pad;
    Cache : TPadCache;
Begin
    Pad := PCBServer.PCBObjectFactory(ePadObject, eNoDimension, eCreate_Default);
    Pad.Mode := ePadMode_Simple;
    If HoleMM > 0 Then
    Begin
        Pad.Layer    := eMultiLayer;
        Pad.HoleSize := MMsToCoord(HoleMM);
    End
    Else
    Begin
        Pad.Layer    := eTopLayer;
        Pad.HoleSize := 0;
    End;
    Pad.X        := X0(X);
    Pad.Y        := Y0(Y);
    Pad.TopXSize := MMsToCoord(W);
    Pad.TopYSize := MMsToCoord(H);
    If Shape = 1 Then Pad.TopShape := eRounded Else Pad.TopShape := eRectangular;
    Pad.Rotation := RotDeg;
    Pad.Name     := PadName;
    AddToComp(Comp, Pad);
    If (SetMask = 0) And (NoPaste = 0) Then Exit;
    { AD25: the Pad.SolderMaskExpansion / Pad.PasteMaskExpansion setters crash the
      scripting system with an access violation. Set the values through the pad
      cache instead, after the pad is in the component. }
    Pad.BeginModify;
    Cache := Pad.GetState_Cache;
    If SetMask = 1 Then
    Begin
        Cache.SolderMaskExpansion      := MMsToCoord(MaskExpMM);
        Cache.SolderMaskExpansionValid := eCacheManual;
    End;
    If NoPaste = 1 Then
    Begin
        Cache.PasteMaskExpansion      := -MMsToCoord(W + H);
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

Function FootprintExists(Lib : IPCB_Library; FpName : String) : Boolean;
Var
    It : IPCB_LibraryIterator;
    C  : IPCB_LibComponent;
Begin
    Result := False;
    It := Lib.LibraryIterator_Create;
    It.SetState_FilterAll;
    C := It.FirstPCBObject;
    While C <> Nil Do
    Begin
        If C.Name = FpName Then Result := True;
        C := It.NextPCBObject;
    End;
    Lib.LibraryIterator_Destroy(It);
End;

Function PrimitiveCount(C : IPCB_LibComponent) : Integer;
Var
    GIt  : IPCB_GroupIterator;
    Prim : IPCB_Primitive;
Begin
    Result := 0;
    GIt := C.GroupIterator_Create;
    GIt.AddFilter_ObjectSet(AllObjects);
    Prim := GIt.FirstPCBObject;
    While Prim <> Nil Do
    Begin
        Result := Result + 1;
        Prim := GIt.NextPCBObject;
    End;
    C.GroupIterator_Destroy(GIt);
End;

Function FindEmptyFootprint(Lib : IPCB_Library; KeepName : String) : IPCB_LibComponent;
Var
    It : IPCB_LibraryIterator;
    C  : IPCB_LibComponent;
Begin
    Result := Nil;
    It := Lib.LibraryIterator_Create;
    It.SetState_FilterAll;
    C := It.FirstPCBObject;
    While C <> Nil Do
    Begin
        If C.Name <> KeepName Then
            If PrimitiveCount(C) = 0 Then
                If Result = Nil Then Result := C;
        C := It.NextPCBObject;
    End;
    Lib.LibraryIterator_Destroy(It);
End;

Function RemoveEmptyFootprintsFrom(Lib : IPCB_Library; KeepName : String) : Integer;
Var
    C : IPCB_LibComponent;
Begin
    { A new workspace footprint document starts with an empty default footprint.
      The workspace accepts only one footprint per document, so delete the empty ones
      (see altium_pitfalls.md item 17). Footprints with any primitives are kept. }
    Result := 0;
    C := FindEmptyFootprint(Lib, KeepName);
    While C <> Nil Do
    Begin
        Lib.RemoveComponent(C);
        Result := Result + 1;
        C := FindEmptyFootprint(Lib, KeepName);
    End;
End;

Procedure RemoveEmptyFootprints;
Var
    N : Integer;
Begin
    { Run from File > Run Script with the footprint document as the active tab. }
    If PCBServer = Nil Then Exit;
    FpLib := PCBServer.GetCurrentPCBLibrary;
    If FpLib = Nil Then
    Begin
        ShowMessage('No PCB Library is active. Click on the footprint tab, then run RemoveEmptyFootprints.');
        Exit;
    End;
    If Not FootprintExists(FpLib, '{fp_name}') Then
    Begin
        ShowMessage('{fp_name} is not in this library, so nothing was removed.');
        Exit;
    End;
    N := RemoveEmptyFootprintsFrom(FpLib, '{fp_name}');
    FpLib.Board.ViewManager_FullUpdate;
    ShowMessage('Removed ' + IntToStr(N) + ' empty footprint(s). Save the footprint, then save the component again.');
End;

Procedure CreateFootprint;
Var
    Comp : IPCB_LibComponent;
Begin
    { Run from File > Run Script with the PcbLib as the active tab, not from the script editor.
      DelphiScript evaluates both sides of And/Or, so each nil check is its own If. }
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
    If FootprintExists(FpLib, '{fp_name}') Then
    Begin
        ShowMessage('The library already has a footprint named {fp_name}. Delete or rename it first, then run CreateFootprint again.');
        Exit;
    End;

    Step := 'creating the footprint';
    Try
    MaskExpMM := {mask_exp};
    SetMask   := {set_mask};
    Comp := PCBServer.CreatePCBLibComp;
    Comp.Name        := '{fp_name}';
    Comp.Description := '{fp_desc}';
    Comp.Height      := MMsToCoord({height});
    FpLib.RegisterComponent(Comp);

    Step := 'adding pads and outlines';
    PCBServer.PreProcess;
{fp_body}
    PCBServer.PostProcess;

    Step := 'removing the empty default footprint';
    RemoveEmptyFootprintsFrom(FpLib, '{fp_name}');

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

Function SchPinCount(C : ISch_Component) : Integer;
Var
    It  : ISch_Iterator;
    Obj : ISch_BasicContainer;
Begin
    Result := 0;
    It := C.SchIterator_Create;
    It.AddFilter_ObjectSet(MkSet(ePin));
    Obj := It.FirstSchObject;
    While Obj <> Nil Do
    Begin
        Result := Result + 1;
        Obj := It.NextSchObject;
    End;
    C.SchIterator_Destroy(It);
End;

Function FindEmptySymbol(Lib : ISch_Lib; KeepRef : String) : ISch_Component;
Var
    It : ISch_Iterator;
    C  : ISch_Component;
Begin
    Result := Nil;
    It := Lib.SchLibIterator_Create;
    It.AddFilter_ObjectSet(MkSet(eSchComponent));
    C := It.FirstSchObject;
    While C <> Nil Do
    Begin
        If C.LibReference <> KeepRef Then
            If SchPinCount(C) = 0 Then
                If Result = Nil Then Result := C;
        C := It.NextSchObject;
    End;
    Lib.SchIterator_Destroy(It);
End;

Function RemoveEmptySymbolsFrom(Lib : ISch_Lib; KeepRef : String) : Integer;
Var
    C : ISch_Component;
Begin
    { A new workspace symbol document starts with an empty default symbol.
      The workspace accepts only one symbol per document, so delete the empty ones
      (see altium_pitfalls.md item 17). Symbols with any pins are kept. }
    Result := 0;
    C := FindEmptySymbol(Lib, KeepRef);
    While C <> Nil Do
    Begin
        Lib.RemoveSchComponent(C);
        Result := Result + 1;
        C := FindEmptySymbol(Lib, KeepRef);
    End;
End;

Procedure RemoveEmptySymbols;
Var
    SchLib : ISch_Lib;
    N      : Integer;
Begin
    { Run from File > Run Script with the symbol document as the active tab. }
    If SchServer = Nil Then Exit;
    SchLib := SchServer.GetCurrentSchDocument;
    If SchLib = Nil Then
    Begin
        ShowMessage('No Schematic Library is active. Click on the symbol tab, then run RemoveEmptySymbols.');
        Exit;
    End;
    If SchLib.ObjectID <> eSchLib Then
    Begin
        ShowMessage('The active document is not a Schematic Library. Click on the symbol tab and try again.');
        Exit;
    End;
    N := RemoveEmptySymbolsFrom(SchLib, '{sym_name}');
    SchLib.GraphicallyInvalidate;
    ShowMessage('Removed ' + IntToStr(N) + ' empty symbol(s). Save the symbol, then save the component again.');
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
    { Comment can be nil on a new component, so it is not set here. }
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
    Step := 'removing the empty default symbol';
    RemoveEmptySymbolsFrom(SchLib, '{sym_name}');
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
    mask = fp.get("mask_expansion")
    out = SCRIPT
    for k, v in {
        "{title}": spec["title"], "{source}": spec["source"], "{date}": spec["date"],
        "{basename}": spec["basename"], "{fp_name}": esc(fp["name"]), "{fp_desc}": esc(fp["description"]),
        "{height}": f(fp["body"]["A"]), "{fp_body}": "\n".join(footprint_lines(fp)),
        "{npads}": str(len(fp["pads"])), "{mask_exp}": f(mask or 0), "{set_mask}": "0" if mask is None else "1",
        "{sym_name}": esc(sym["name"]), "{sym_desc}": esc(sym["description"]),
        "{designator}": esc(sym["designator"]), "{sym_body}": "\n".join(symbol_lines(sym)),
        "{params}": params, "{npins}": str(len(sym["pins"])),
    }.items():
        out = out.replace(k, v)
    return out


# ---------------------------------------------------------------- previews
def footprint_svg(fp):
    silk, dot, asm, cy = footprint_geometry(fp)
    m = 0.5
    x1, y1, x2, y2 = cy[0] - m, cy[1] - m, cy[2] + m, cy[3] + m
    scale = 900 / max(x2 - x1, y2 - y1)
    W, H = (x2 - x1) * scale, (y2 - y1) * scale

    def X(x):
        return (x - x1) * scale

    def Y(y):
        return (y2 - y) * scale   # +Y up in Altium

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H + 40:.0f}" '
         f'font-family="Arial" style="background:#101418">',
         f'<rect x="{X(cy[0])}" y="{Y(cy[3])}" width="{(cy[2] - cy[0]) * scale}" height="{(cy[3] - cy[1]) * scale}" '
         f'fill="none" stroke="#c080ff" stroke-width="1" stroke-dasharray="4,3"/>',
         '<polyline points="' + " ".join(f"{X(a)},{Y(b)}" for a, b in asm) +
         '" fill="none" stroke="#777" stroke-width="1"/>']
    fs = max(7, min(14, 0.35 * scale * min(min(p["dx"], p["dy"]) for p in fp["pads"])))
    for p in fp["pads"]:
        rx = min(p["dx"], p["dy"]) / 2 * scale if p["shape"] != "rect" else 0
        o.append(f'<rect x="{X(p["x"]) - p["dx"] / 2 * scale}" y="{Y(p["y"]) - p["dy"] / 2 * scale}" '
                 f'width="{p["dx"] * scale}" height="{p["dy"] * scale}" rx="{rx}" fill="#d04040" '
                 f'transform="rotate({-p.get("rotation", 0)} {X(p["x"])} {Y(p["y"])})"/>')
        if p.get("hole"):
            o.append(f'<circle cx="{X(p["x"])}" cy="{Y(p["y"])}" r="{p["hole"] / 2 * scale}" fill="#101418"/>')
        o.append(f'<text x="{X(p["x"])}" y="{Y(p["y"]) + fs / 3}" font-size="{fs:.1f}" fill="#fff" '
                 f'text-anchor="middle">{p["name"]}</text>')
    for w in fp["paste_windows"]:
        o.append(f'<rect x="{X(w["x"] - w["dx"] / 2)}" y="{Y(w["y"] + w["dy"] / 2)}" '
                 f'width="{w["dx"] * scale}" height="{w["dy"] * scale}" fill="#9a9a9a" opacity="0.6"/>')
    for a, b, c, d in silk:
        o.append(f'<line x1="{X(a)}" y1="{Y(b)}" x2="{X(c)}" y2="{Y(d)}" stroke="#f0e060" '
                 f'stroke-width="{max(1.5, fp["silk_width"] * scale)}"/>')
    o.append(f'<circle cx="{X(dot["x"])}" cy="{Y(dot["y"])}" r="{dot["r"] * scale}" fill="#f0e060"/>')
    o.append(f'<text x="10" y="{H + 25:.0f}" font-size="14" fill="#e8e8e8">{fp["name"]}  (top view; '
             f'body {fp["body"]["D"]} x {fp["body"]["E"]} mm; grey = body/paste, dashed = courtyard)</text>')
    o.append("</svg>")
    return "\n".join(o)


def symbol_svg(sym, s=0.12):
    placed, (x1, y1, x2, y2) = symbol_layout(sym)
    pl = sym["pin_length_mil"]
    pad = pl + 300

    def X(x):
        return (x - x1 + pad) * s

    def Y(y):
        return (y2 - y + pad) * s

    W, H = (x2 - x1 + 2 * pad) * s, (y2 - y1 + 2 * pad) * s
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" font-family="Arial" '
         f'style="background:white">',
         f'<rect x="{X(x1)}" y="{Y(y2)}" width="{(x2 - x1) * s}" height="{(y2 - y1) * s}" '
         f'fill="#ffffb0" stroke="#800000" stroke-width="1.5"/>',
         f'<text x="{X(x1)}" y="{Y(y2) - 30 * s - (pl * s if any(o == ORIENT["top"] for *_, o in placed) else 0)}" '
         f'font-size="12">{sym["designator"]}  {sym["name"]}</text>']
    for p, x, y, orient in placed:
        dx, dy = {"eRotate180": (-pl, 0), "eRotate0": (pl, 0), "eRotate90": (0, pl), "eRotate270": (0, -pl)}[orient]
        o.append(f'<line x1="{X(x)}" y1="{Y(y)}" x2="{X(x + dx)}" y2="{Y(y + dy)}" stroke="#000" stroke-width="1"/>')
        if orient == "eRotate180":
            o.append(f'<text x="{X(x) + 4}" y="{Y(y) + 3.5}" font-size="9.5">{p["name"]}</text>')
        elif orient == "eRotate0":
            o.append(f'<text x="{X(x) - 4}" y="{Y(y) + 3.5}" font-size="9.5" text-anchor="end">{p["name"]}</text>')
        elif orient == "eRotate90":
            o.append(f'<text transform="translate({X(x) + 3.5},{Y(y) + 4}) rotate(-90)" font-size="9.5" '
                     f'text-anchor="end">{p["name"]}</text>')
        else:
            o.append(f'<text transform="translate({X(x) + 3.5},{Y(y) - 4}) rotate(-90)" font-size="9.5">{p["name"]}</text>')
        tx, ty = X(x + dx / 2), Y(y + dy / 2)
        if dy:
            o.append(f'<text transform="translate({tx - 2},{ty}) rotate(-90)" font-size="8" text-anchor="middle" '
                     f'fill="#444">{p["num"]}</text>')
        else:
            o.append(f'<text x="{tx}" y="{ty - 2}" font-size="8" text-anchor="middle" fill="#444">{p["num"]}</text>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- main
def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    fp = spec["footprint"] = {**FP_DEFAULTS, **spec["footprint"]}
    sym = spec["symbol"] = {**SYM_DEFAULTS, **spec["symbol"]}

    nums = [p["num"] for p in sym["pins"]]
    dups = sorted({n for n in nums if nums.count(n) > 1})
    if dups:
        fail(f"duplicate symbol pin numbers: {dups}")
    pad_names = {p["name"] for p in fp["pads"]}
    missing = sorted(set(nums) - pad_names)
    if missing:
        fail(f"symbol pins with no pad: {missing}")
    for p in fp["pads"]:
        if p["shape"] not in ("rect", "round", "oval"):
            fail(f"pad {p['name']}: shape must be rect, round or oval")
    warnings = check_pads(fp)

    os.makedirs(out, exist_ok=True)
    base = spec["basename"]
    with open(os.path.join(out, base + ".pas"), "w", newline="", encoding="utf-8") as fh:
        fh.write(build_script(spec))
    with open(os.path.join(out, base + ".PrjScr"), "w", newline="") as fh:
        fh.write(f"[Design]\r\nVersion=1.0\r\n\r\n[Document1]\r\nDocumentPath={base}.pas\r\n")
    with open(os.path.join(out, base + "_footprint_preview.svg"), "w", encoding="utf-8") as fh:
        fh.write(footprint_svg(fp))
    with open(os.path.join(out, base + "_symbol_preview.svg"), "w", encoding="utf-8") as fh:
        fh.write(symbol_svg(sym))

    first_pad = {}
    for p in fp["pads"]:
        first_pad.setdefault(p["name"], p)
    with open(os.path.join(out, base + "_pin_table.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Pin", "Name", "Electrical type", "Symbol side", "Group", "Pad X (mm)", "Pad Y (mm)",
                    "Pad size (mm)", "Hole (mm)"])
        placed, _ = symbol_layout(sym)
        for p, *_ in placed:
            pd = first_pad[p["num"]]
            w.writerow([p["num"], p["name"], p["type"], p["side"], p.get("group", ""), f(pd["x"]), f(pd["y"]),
                        f"{f(pd['dx'])} x {f(pd['dy'])}", f(pd["hole"]) if pd.get("hole") else ""])

    for m in warnings:
        print(m)
    print(f"pads: {len(fp['pads'])} ({len(pad_names)} names)  pins: {len(nums)}  "
          f"pads without a pin: {sorted(pad_names - set(nums))}")
    print(f"wrote {base}.pas, {base}.PrjScr, previews and pin table to {out}")


if __name__ == "__main__":
    main()
