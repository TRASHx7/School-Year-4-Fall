{ ==========================================================================
  Nordic nRF52840-QIAA-F-R7 (aQFN73 7 x 7 mm): Altium footprint and schematic symbol
  Generated from: nRF52840 Product Specification v1.8, section 7.1.1 (Figure 207, Table 145) and section 7.2.1 (Figure 210, Table 148)
  Generated on:   2026-11-01

  HOW TO USE (Altium Designer)
  1. File > New > Library > PCB Library. With the new PcbLib open and active,
     run File > Run Script, browse to this file and pick CreateFootprint.
  2. File > New > Library > Schematic Library. With the new SchLib open and
     active, run File > Run Script again and pick CreateSymbol.
  3. Save both libraries. The symbol already links to footprint
     'NORDIC_AQFN73_7X7MM_P0.5', so keep the PcbLib in the same project or add it to your
     installed libraries.

  All footprint coordinates are in millimetres, top view, origin at the
  package centre, +Y up. Symbol coordinates are in mils.
  ========================================================================== }

{ ---------------------------------------------------------------- footprint }

Var
    FpLib     : IPCB_Library;
    SymComp   : ISch_Component;
    MaskExpMM : Double;

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
    Pad : IPCB_Pad;
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
    { Fixed solder mask opening; the usual 0.1 mm rule leaves no mask web at this pitch }
    Pad.SolderMaskExpansionMode := eMaskExpansionMode_Manual;
    Pad.SolderMaskExpansion     := MMsToCoord(MaskExpMM);
    If NoPaste = 1 Then
    Begin
        Pad.PasteMaskExpansionMode := eMaskExpansionMode_Manual;
        Pad.PasteMaskExpansion     := -MMsToCoord(W);
    End;
    AddToComp(Comp, Pad);
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
    FpLib := PCBServer.GetCurrentPCBLibrary;
    If FpLib = Nil Then
    Begin
        ShowMessage('Open (or create) a PCB Library and make it the active document first.');
        Exit;
    End;

    MaskExpMM := 0.05;
    Comp := PCBServer.CreatePCBLibComp;
    Comp.Name        := 'NORDIC_AQFN73_7X7MM_P0.5';
    Comp.Description := 'Nordic aQFN73 7.0 x 7.0 mm, 0.5 mm pitch staggered rows, 0.25 mm round pads, 4.85 mm exposed pad (nRF52840 PS v1.8 Fig. 207/210)';
    Comp.Height      := MMsToCoord(0.85);
    FpLib.RegisterComponent(Comp);

    PCBServer.PreProcess;
    AddSmdPad(Comp, 'A8', -1.25, 3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'A10', -0.75, 3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'A12', -0.25, 3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'A14', 0.25, 3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'A16', 0.75, 3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'A18', 1.25, 3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'A20', 1.75, 3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'A22', 2.25, 3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'A23', 2.75, 3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B1', -3.25, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B3', -2.5, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B5', -2, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B7', -1.5, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B9', -1, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B11', -0.5, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B13', 0, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B15', 0.5, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B17', 1, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B19', 1.5, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'B24', 3.25, 2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'C1', -3.25, 2.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'D2', -2.75, 2, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'D23', 2.75, 2, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'E24', 3.25, 1.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'F2', -2.75, 1.5, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'F23', 2.75, 1.5, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'G1', -3.25, 1.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'H2', -2.75, 1, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'H23', 2.75, 1, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'J1', -3.25, 0.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'J24', 3.25, 0.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'K2', -2.75, 0.5, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'L1', -3.25, 0.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'L24', 3.25, 0.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'M2', -2.75, 0, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'N1', -3.25, -0.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'N24', 3.25, -0.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'P2', -2.75, -0.5, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'P23', 2.75, -0.5, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'R1', -3.25, -0.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'R24', 3.25, -0.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'T2', -2.75, -1, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'T23', 2.75, -1, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'U1', -3.25, -1.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'U24', 3.25, -1.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'V23', 2.75, -1.5, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'W1', -3.25, -1.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'W24', 3.25, -1.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'Y2', -2.75, -2, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'Y23', 2.75, -2, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AA24', 3.25, -2.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AB2', -2.75, -2.5, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AC5', -2, -2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AC9', -1, -2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AC11', -0.5, -2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AC13', 0, -2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AC15', 0.5, -2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AC17', 1, -2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AC19', 1.5, -2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AC21', 2, -2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AC24', 3.25, -2.75, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD2', -2.75, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD4', -2.25, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD6', -1.75, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD8', -1.25, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD10', -0.75, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD12', -0.25, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD14', 0.25, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD16', 0.75, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD18', 1.25, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD20', 1.75, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD22', 2.25, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'AD23', 2.75, -3.25, 0.25, 0.25, 1, 0);
    AddSmdPad(Comp, 'EP', 0, 0, 4.85, 4.85, 0, 1);
    AddPasteFill(Comp, -2.05, 0.15, -0.15, 2.05);
    AddPasteFill(Comp, -2.05, -2.05, -0.15, -0.15);
    AddPasteFill(Comp, 0.15, 0.15, 2.05, 2.05);
    AddPasteFill(Comp, 0.15, -2.05, 2.05, -0.15);
    AddLine(Comp, 3.61, 3.61, 3.01, 3.61, 0.12, eTopOverlay);
    AddLine(Comp, 3.61, 3.61, 3.61, 3.01, 0.12, eTopOverlay);
    AddLine(Comp, 3.61, -3.61, 3.01, -3.61, 0.12, eTopOverlay);
    AddLine(Comp, 3.61, -3.61, 3.61, -3.01, 0.12, eTopOverlay);
    AddLine(Comp, -3.61, -3.61, -3.01, -3.61, 0.12, eTopOverlay);
    AddLine(Comp, -3.61, -3.61, -3.61, -3.01, 0.12, eTopOverlay);
    AddLine(Comp, -3.61, 3.01, -3.61, 3.31, 0.12, eTopOverlay);
    AddLine(Comp, -3.31, 3.61, -3.01, 3.61, 0.12, eTopOverlay);
    AddCircle(Comp, -3.95, 3.95, 0.075, 0.15, eTopOverlay);
    AddLine(Comp, -3, 3.5, 3.5, 3.5, 0.1, eMechanical13);
    AddLine(Comp, 3.5, 3.5, 3.5, -3.5, 0.1, eMechanical13);
    AddLine(Comp, 3.5, -3.5, -3.5, -3.5, 0.1, eMechanical13);
    AddLine(Comp, -3.5, -3.5, -3.5, 3, 0.1, eMechanical13);
    AddLine(Comp, -3.5, 3, -3, 3.5, 0.1, eMechanical13);
    AddLine(Comp, -3.8, 3.8, 3.8, 3.8, 0.05, eMechanical15);
    AddLine(Comp, 3.8, 3.8, 3.8, -3.8, 0.05, eMechanical15);
    AddLine(Comp, 3.8, -3.8, -3.8, -3.8, 0.05, eMechanical15);
    AddLine(Comp, -3.8, -3.8, -3.8, 3.8, 0.05, eMechanical15);
    PCBServer.PostProcess;

    FpLib.CurrentComponent := Comp;
    FpLib.Board.ViewManager_FullUpdate;
    ShowMessage('Footprint NORDIC_AQFN73_7X7MM_P0.5 created (74 pads). Check it against the datasheet drawing, then save the library.');
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
    If SchServer = Nil Then Exit;
    SchLib := SchServer.GetCurrentSchDocument;
    If (SchLib = Nil) Or (SchLib.ObjectID <> eSchLib) Then
    Begin
        ShowMessage('Open (or create) a Schematic Library and make it the active document first.');
        Exit;
    End;

    SymComp := SchServer.SchObjectFactory(eSchComponent, eCreate_Default);
    If SymComp = Nil Then Exit;
    SymComp.CurrentPartID        := 1;
    SymComp.DisplayMode          := 0;
    SymComp.LibReference         := 'NRF52840-QIAA-F-R7';
    SymComp.ComponentDescription := 'nRF52840 BLE 5 / 802.15.4 SoC, Cortex-M4F 64 MHz, 1 MB flash, 256 kB RAM, aQFN73 7x7 mm';
    SymComp.Designator.Text      := 'U?';
    SymComp.Comment.Text         := 'NRF52840-QIAA-F-R7';

    AddRect(SymComp, 0, -4600, 2000, 0);
    AddPin(SymComp, 'Y2', 'VDDH', 0, -100, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'A22', 'VDD', 0, -200, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'AD14', 'VDD', 0, -300, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'AD23', 'VDD', 0, -400, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'B1', 'VDD', 0, -500, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'W1', 'VDD', 0, -600, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'C1', 'DEC1', 0, -800, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'A18', 'DEC2', 0, -900, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'D23', 'DEC3', 0, -1000, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'B5', 'DEC4', 0, -1100, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'E24', 'DEC6', 0, -1200, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'B3', 'DCC', 0, -1300, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'AB2', 'DCCH', 0, -1400, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'N24', 'NC', 0, -1500, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'B24', 'XC1', 0, -1700, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'A23', 'XC2', 0, -1800, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'H23', 'ANT', 0, -2000, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'AC24', 'SWDIO', 0, -2200, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'AA24', 'SWDCLK', 0, -2300, eRotate180, eElectricInput, 200);
    AddPin(SymComp, 'AD2', 'VBUS', 0, -2500, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'AC5', 'DECUSB', 0, -2600, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'AD6', 'D+', 0, -2700, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'AD4', 'D-', 0, -2800, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'AD22', 'P1.00/TRACEDATA0', 0, -3000, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'Y23', 'P1.01', 0, -3100, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'W24', 'P1.02', 0, -3200, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'V23', 'P1.03', 0, -3300, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'U24', 'P1.04', 0, -3400, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'T23', 'P1.05', 0, -3500, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'R24', 'P1.06', 0, -3600, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'P23', 'P1.07', 0, -3700, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'P2', 'P1.08', 0, -3800, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'R1', 'P1.09/TRACEDATA3', 0, -3900, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'A20', 'P1.10', 0, -4000, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'B19', 'P1.11', 0, -4100, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'B17', 'P1.12', 0, -4200, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'A16', 'P1.13', 0, -4300, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'B15', 'P1.14', 0, -4400, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'A14', 'P1.15', 0, -4500, eRotate180, eElectricIO, 200);
    AddPin(SymComp, 'D2', 'P0.00/XL1', 2000, -100, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'F2', 'P0.01/XL2', 2000, -200, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'A12', 'P0.02/AIN0', 2000, -300, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'B13', 'P0.03/AIN1', 2000, -400, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'J1', 'P0.04/AIN2', 2000, -500, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'K2', 'P0.05/AIN3', 2000, -600, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'L1', 'P0.06', 2000, -700, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'M2', 'P0.07/TRACECLK', 2000, -800, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'N1', 'P0.08', 2000, -900, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'L24', 'P0.09/NFC1', 2000, -1000, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'J24', 'P0.10/NFC2', 2000, -1100, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'T2', 'P0.11/TRACEDATA2', 2000, -1200, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'U1', 'P0.12/TRACEDATA1', 2000, -1300, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AD8', 'P0.13', 2000, -1400, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AC9', 'P0.14', 2000, -1500, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AD10', 'P0.15', 2000, -1600, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AC11', 'P0.16', 2000, -1700, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AD12', 'P0.17', 2000, -1800, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AC13', 'P0.18/nRESET', 2000, -1900, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AC15', 'P0.19', 2000, -2000, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AD16', 'P0.20', 2000, -2100, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AC17', 'P0.21', 2000, -2200, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AD18', 'P0.22', 2000, -2300, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AC19', 'P0.23', 2000, -2400, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AD20', 'P0.24', 2000, -2500, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'AC21', 'P0.25', 2000, -2600, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'G1', 'P0.26', 2000, -2700, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'H2', 'P0.27', 2000, -2800, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'B11', 'P0.28/AIN4', 2000, -2900, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'A10', 'P0.29/AIN5', 2000, -3000, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'B9', 'P0.30/AIN6', 2000, -3100, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'A8', 'P0.31/AIN7', 2000, -3200, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'B7', 'VSS', 900, -4600, eRotate270, eElectricPower, 200);
    AddPin(SymComp, 'EP', 'VSS', 1000, -4600, eRotate270, eElectricPower, 200);
    AddPin(SymComp, 'F23', 'VSS_PA', 1100, -4600, eRotate270, eElectricPower, 200);

    AddParam(SymComp, 'Manufacturer', 'Nordic Semiconductor');
    AddParam(SymComp, 'Manufacturer Part Number', 'NRF52840-QIAA-F-R7');
    AddParam(SymComp, 'Package', 'aQFN73 7 x 7 mm');
    AddParam(SymComp, 'Datasheet', 'nRF52840 Product Specification v1.8');
    AddParam(SymComp, 'Supplier 1', 'Digi-Key');
    AddParam(SymComp, 'Supplier Part Number 1', 'NRF52840-QIAA-F-R7 (Cut Tape)');

    Impl := SymComp.AddSchImplementation;
    Impl.ClearAllDatafileLinks;
    Impl.Description := 'Footprint';
    Impl.ModelName   := 'NORDIC_AQFN73_7X7MM_P0.5';
    Impl.ModelType   := 'PCBLIB';
    Impl.AddDataFileLink('NORDIC_AQFN73_7X7MM_P0.5', '', 'PCBLIB');
    Impl.IsCurrent   := True;

    SchLib.AddSchComponent(SymComp);
    SchServer.RobotManager.SendMessage(nil, c_BroadCast, SCHM_PrimitiveRegistration, SymComp.I_ObjectAddress);
    SchLib.CurrentSchComponent := SymComp;
    SchLib.GraphicallyInvalidate;
    ShowMessage('Symbol NRF52840-QIAA-F-R7 created (74 pins). Save the library.');
End;
