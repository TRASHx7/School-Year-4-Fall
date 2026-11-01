{ ==========================================================================
  Analog Devices MAX30009ENA+T (25-bump WLP 2.03 x 2.03 mm, 0.4 mm pitch): Altium footprint and schematic symbol
  Generated from: MAX30009 data sheet Rev 2 (Aug 2023) p.20-21 pin configuration and description; package outline 21-100494 Rev A
  Generated on:   2026-11-01

  HOW TO USE (Altium Designer)
  1. Open or create a PCB Library (File > New > Library > PCB Library). Click its
     tab so it is the active document, then File > Run Script > Browse > From file,
     pick MAX30009ENA+T.PrjScr and run CreateFootprint.
  2. Open or create a Schematic Library, click its tab, then File > Run Script and
     run CreateSymbol.
  Do not use the Run button in the script editor: the script itself is then the
  active document and the library is not found.
  If you edit this file after Altium has loaded it, Altium keeps running the old
  copy: close the script project in Altium first, or load a renamed copy.
  3. Save both libraries. The symbol links to footprint 'ADI_WLP25_2.03X2.03MM_P0.4', so keep the
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
    If FootprintExists(FpLib, 'ADI_WLP25_2.03X2.03MM_P0.4') Then
    Begin
        ShowMessage('The library already has a footprint named ADI_WLP25_2.03X2.03MM_P0.4. Delete or rename it first, then run CreateFootprint again.');
        Exit;
    End;

    Step := 'creating the footprint';
    Try
    MaskExpMM := 0.03;
    SetMask   := 1;
    Comp := PCBServer.CreatePCBLibComp;
    Comp.Name        := 'ADI_WLP25_2.03X2.03MM_P0.4';
    Comp.Description := '25-bump WLP (N252C2+1), 2.028 x 2.028 mm, 0.4 mm pitch, 0.22 mm NSMD lands (21-100494 Rev A)';
    Comp.Height      := MMsToCoord(0.5);
    FpLib.RegisterComponent(Comp);

    Step := 'adding pads and outlines';
    PCBServer.PreProcess;
    AddPad(Comp, 'A1', -0.8, 0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'A2', -0.4, 0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'A3', 0, 0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'A4', 0.4, 0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'A5', 0.8, 0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'B1', -0.8, 0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'B2', -0.4, 0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'B3', 0, 0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'B4', 0.4, 0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'B5', 0.8, 0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'C1', -0.8, 0, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'C2', -0.4, 0, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'C3', 0, 0, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'C4', 0.4, 0, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'C5', 0.8, 0, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'D1', -0.8, -0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'D2', -0.4, -0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'D3', 0, -0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'D4', 0.4, -0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'D5', 0.8, -0.4, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'E1', -0.8, -0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'E2', -0.4, -0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'E3', 0, -0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'E4', 0.4, -0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddPad(Comp, 'E5', 0.8, -0.8, 0.22, 0.22, 1, 0, 0, 0);
    AddCircle(Comp, -1.464, 0.8, 0.075, 0.15, eTopOverlay);
    AddLine(Comp, -1.014, 0.507, -0.507, 1.014, 0.1, eMechanical13);
    AddLine(Comp, -0.507, 1.014, 1.014, 1.014, 0.1, eMechanical13);
    AddLine(Comp, 1.014, 1.014, 1.014, -1.014, 0.1, eMechanical13);
    AddLine(Comp, 1.014, -1.014, -1.014, -1.014, 0.1, eMechanical13);
    AddLine(Comp, -1.014, -1.014, -1.014, 0.507, 0.1, eMechanical13);
    AddLine(Comp, -1.9, 1.3, 1.3, 1.3, 0.05, eMechanical15);
    AddLine(Comp, 1.3, 1.3, 1.3, -1.3, 0.05, eMechanical15);
    AddLine(Comp, 1.3, -1.3, -1.9, -1.3, 0.05, eMechanical15);
    AddLine(Comp, -1.9, -1.3, -1.9, 1.3, 0.05, eMechanical15);
    PCBServer.PostProcess;

    Step := 'refreshing the view';
    FpLib.CurrentComponent := Comp;
    FpLib.Board.ViewManager_FullUpdate;
    Except
        ShowMessage('CreateFootprint stopped while ' + Step + '. Please report this step and the error text.');
        Exit;
    End;
    ShowMessage('Footprint ADI_WLP25_2.03X2.03MM_P0.4 created (25 pads). Check it against the datasheet drawing, then save the library.');
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
    { Comment can be nil on a new component, so it is not set here. }
    SymComp.CurrentPartID        := 1;
    SymComp.DisplayMode          := 0;
    SymComp.LibReference         := 'MAX30009ENA+T';
    SymComp.ComponentDescription := 'Low-power, high-performance bioimpedance (BioZ) AFE, 1.8 V, SPI/I2C';
    SymComp.Designator.Text      := 'U?';

    Step := 'adding the body and pins';
    AddRect(SymComp, 0, -1800, 1200, 0);
    AddPin(SymComp, 'C1', 'AVDD', 0, -100, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'D1', 'DVDD', 0, -200, eRotate180, eElectricPower, 200);
    AddPin(SymComp, 'C2', 'VREF', 0, -300, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'A1', 'EL1', 0, -500, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'A2', 'EL2A', 0, -600, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'A3', 'EL2B', 0, -700, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'B3', 'EL3B', 0, -800, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'B2', 'EL3A', 0, -900, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'B1', 'EL4', 0, -1000, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'A4', 'CAL1', 0, -1200, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'A5', 'CAL2', 0, -1300, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'B5', 'CAL3', 0, -1400, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'B4', 'CAL4', 0, -1500, eRotate180, eElectricPassive, 200);
    AddPin(SymComp, 'E4', 'SCLK/SCL', 1200, -100, eRotate0, eElectricInput, 200);
    AddPin(SymComp, 'E3', 'SDI/SDA', 1200, -200, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'E2', 'SDO/ADDR', 1200, -300, eRotate0, eElectricIO, 200);
    AddPin(SymComp, 'D2', 'CSB/I2C_SEL', 1200, -400, eRotate0, eElectricInput, 200);
    AddPin(SymComp, 'E5', 'INT', 1200, -500, eRotate0, eElectricOutput, 200);
    AddPin(SymComp, 'D3', 'FCLK', 1200, -700, eRotate0, eElectricInput, 200);
    AddPin(SymComp, 'D4', 'TRIG', 1200, -800, eRotate0, eElectricInput, 200);
    AddPin(SymComp, 'C4', 'DRVSJ', 1200, -1000, eRotate0, eElectricPassive, 200);
    AddPin(SymComp, 'C5', 'DRVXR', 1200, -1100, eRotate0, eElectricPassive, 200);
    AddPin(SymComp, 'D5', 'DRVXC', 1200, -1200, eRotate0, eElectricPassive, 200);
    AddPin(SymComp, 'C3', 'AGND', 600, -1800, eRotate270, eElectricPower, 200);
    AddPin(SymComp, 'E1', 'DGND', 700, -1800, eRotate270, eElectricPower, 200);

    Step := 'adding parameters';
    AddParam(SymComp, 'Manufacturer', 'Analog Devices');
    AddParam(SymComp, 'Manufacturer Part Number', 'MAX30009ENA+T');
    AddParam(SymComp, 'Package', '25-WLP 2.03 x 2.03 mm, 0.4 mm pitch (N252C2+1, outline 21-100494)');
    AddParam(SymComp, 'Datasheet', 'https://www.analog.com/media/en/technical-documentation/data-sheets/max30009.pdf');
    AddParam(SymComp, 'Supplier 1', 'Digi-Key');
    AddParam(SymComp, 'Supplier Part Number 1', '175-MAX30009ENA+TCT-ND');

    Step := 'linking the footprint';
    Impl := SymComp.AddSchImplementation;
    Impl.ClearAllDatafileLinks;
    Impl.Description := 'Footprint';
    Impl.ModelName   := 'ADI_WLP25_2.03X2.03MM_P0.4';
    Impl.ModelType   := 'PCBLIB';
    Impl.AddDataFileLink('ADI_WLP25_2.03X2.03MM_P0.4', '', 'PCBLIB');
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
    ShowMessage('Symbol MAX30009ENA+T created (25 pins). Save the library.');
End;
