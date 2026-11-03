{ ==========================================================================
  TI TMP117 (DSBGA-6 0.95 x 1.49 mm, YBG0006): Altium footprint and schematic symbol
  Generated from: TMP117 data sheet SNOSD82D: Fig. 5-2 and Table 5-1 (page 4, ball map), YBG0006-C01 package outline, example board layout and stencil (pages 43 to 45)
  Generated on:   2026-11-03

  HOW TO USE (Altium Designer)
  1. Open or create a PCB Library (File > New > Library > PCB Library). Click its
     tab so it is the active document, then File > Run Script > Browse > From file,
     pick TMP117AIYBGR.PrjScr and run CreateFootprint.
  2. Open or create a Schematic Library, click its tab, then File > Run Script and
     run CreateSymbol.
  Do not use the Run button in the script editor: the script itself is then the
  active document and the library is not found.
  If you edit this file after Altium has loaded it, Altium keeps running the old
  copy: close the script project in Altium first, or load a renamed copy.
  3. Save both libraries. The symbol links to footprint 'TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006', so keep the
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
    If Not FootprintExists(FpLib, 'TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006') Then
    Begin
        ShowMessage('TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006 is not in this library, so nothing was removed.');
        Exit;
    End;
    N := RemoveEmptyFootprintsFrom(FpLib, 'TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006');
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
    If FootprintExists(FpLib, 'TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006') Then
    Begin
        ShowMessage('The library already has a footprint named TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006. Delete or rename it first, then run CreateFootprint again.');
        Exit;
    End;

    Step := 'creating the footprint';
    Try
    MaskExpMM := 0.03;
    SetMask   := 1;
    Comp := PCBServer.CreatePCBLibComp;
    Comp.Name        := 'TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006';
    Comp.Description := 'DSBGA-6 (2 x 3) 0.95 x 1.49 mm, 0.4 mm pitch, TI YBG0006-C01, 0.23 mm NSMD pads (TMP117 data sheet land pattern example)';
    Comp.Height      := MMsToCoord(0.531);
    FpLib.RegisterComponent(Comp);

    Step := 'adding pads and outlines';
    PCBServer.PreProcess;
    AddPad(Comp, 'A1', -0.2, 0.4, 0.23, 0.23, 1, 0, 0, 1);
    AddPad(Comp, 'A2', 0.2, 0.4, 0.23, 0.23, 1, 0, 0, 1);
    AddPad(Comp, 'B1', -0.2, 0, 0.23, 0.23, 1, 0, 0, 1);
    AddPad(Comp, 'B2', 0.2, 0, 0.23, 0.23, 1, 0, 0, 1);
    AddPad(Comp, 'C1', -0.2, -0.4, 0.23, 0.23, 1, 0, 0, 1);
    AddPad(Comp, 'C2', 0.2, -0.4, 0.23, 0.23, 1, 0, 0, 1);
    AddPasteFill(Comp, -0.325, 0.275, -0.075, 0.525);
    AddPasteFill(Comp, 0.075, 0.275, 0.325, 0.525);
    AddPasteFill(Comp, -0.325, -0.125, -0.075, 0.125);
    AddPasteFill(Comp, 0.075, -0.125, 0.325, 0.125);
    AddPasteFill(Comp, -0.325, -0.525, -0.075, -0.275);
    AddPasteFill(Comp, 0.075, -0.525, 0.325, -0.275);
    AddLine(Comp, -0.575, 0.844, 0.575, 0.844, 0.12, eTopOverlay);
    AddLine(Comp, -0.575, -0.844, 0.575, -0.844, 0.12, eTopOverlay);
    AddCircle(Comp, -0.2, 1.194, 0.075, 0.15, eTopOverlay);
    AddLine(Comp, -0.475, 0.5065, -0.2375, 0.744, 0.1, eMechanical13);
    AddLine(Comp, -0.2375, 0.744, 0.475, 0.744, 0.1, eMechanical13);
    AddLine(Comp, 0.475, 0.744, 0.475, -0.744, 0.1, eMechanical13);
    AddLine(Comp, 0.475, -0.744, -0.475, -0.744, 0.1, eMechanical13);
    AddLine(Comp, -0.475, -0.744, -0.475, 0.5065, 0.1, eMechanical13);
    AddLine(Comp, -0.75, 1.6, 0.75, 1.6, 0.05, eMechanical15);
    AddLine(Comp, 0.75, 1.6, 0.75, -1, 0.05, eMechanical15);
    AddLine(Comp, 0.75, -1, -0.75, -1, 0.05, eMechanical15);
    AddLine(Comp, -0.75, -1, -0.75, 1.6, 0.05, eMechanical15);
    PCBServer.PostProcess;

    Step := 'removing the empty default footprint';
    RemoveEmptyFootprintsFrom(FpLib, 'TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006');

    Step := 'refreshing the view';
    FpLib.CurrentComponent := Comp;
    FpLib.Board.ViewManager_FullUpdate;
    Except
        ShowMessage('CreateFootprint stopped while ' + Step + '. Please report this step and the error text.');
        Exit;
    End;
    ShowMessage('Footprint TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006 created (6 pads). Check it against the datasheet drawing, then save the library.');
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
    N := RemoveEmptySymbolsFrom(SchLib, 'TMP117AIYBGR');
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
    SymComp.LibReference         := 'TMP117AIYBGR';
    SymComp.ComponentDescription := 'High-accuracy (0.1 C) digital temperature sensor, I2C/SMBus, DSBGA-6';
    SymComp.Designator.Text      := 'U?';

    Step := 'adding the body and pins';
    AddRect(SymComp, 0, -600, 900, 0);
    AddPin(SymComp, 'B1', 'V+', 0, -100, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'C1', 'ADD0', 0, -300, eRotate180, eElectricInput, 200);
    AddPin(SymComp, 'A2', 'SCL', 900, -100, eRotate0, eElectricInput, 200);
    AddPin(SymComp, 'A1', 'SDA', 900, -200, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'C2', 'ALERT', 900, -400, eRotate0, eElectricOpenCollector, 200);
    AddPin(SymComp, 'B2', 'GND', 400, -600, eRotate270, eElectricPower, 200);

    Step := 'adding parameters';
    AddParam(SymComp, 'Manufacturer', 'Texas Instruments');
    AddParam(SymComp, 'Manufacturer Part Number', 'TMP117AIYBGR');
    AddParam(SymComp, 'Package', 'DSBGA-6 (YBG0006)');
    AddParam(SymComp, 'Datasheet', 'https://www.ti.com/lit/ds/symlink/tmp117.pdf');

    Step := 'linking the footprint';
    Impl := SymComp.AddSchImplementation;
    Impl.ClearAllDatafileLinks;
    Impl.Description := 'Footprint';
    Impl.ModelName   := 'TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006';
    Impl.ModelType   := 'PCBLIB';
    Impl.AddDataFileLink('TI_DSBGA6_0.95X1.49MM_P0.4_YBG0006', '', 'PCBLIB');
    Impl.IsCurrent   := True;

    Step := 'adding the component to the library';
    SchLib.AddSchComponent(SymComp);
    SchServer.RobotManager.SendMessage(nil, c_BroadCast, SCHM_PrimitiveRegistration, SymComp.I_ObjectAddress);
    Step := 'removing the empty default symbol';
    RemoveEmptySymbolsFrom(SchLib, 'TMP117AIYBGR');
    SchLib.CurrentSchComponent := SymComp;
    SchLib.GraphicallyInvalidate;
    Except
        ShowMessage('CreateSymbol stopped while ' + Step + '. Please report this step and the error text.');
        Exit;
    End;
    ShowMessage('Symbol TMP117AIYBGR created (6 pins). Save the library.');
End;
