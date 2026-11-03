# Altium scripting and automation pitfalls (diagnosed on Altium Designer 25.5.2)

Each item: what happened, why, what to do. `scripts/gen_altium.py` already follows all
of these. Keep it that way when editing the template.

## Script API

### 1. Pad mask expansion setters crash Altium (access violation)

What happened: `Pad.SolderMaskExpansion := ...` and `Pad.PasteMaskExpansion := ...`
raise "Access violation at address ... in module 'ScriptingSystem.DLL'. Read of address
0000000000000038". This happens whether the pad has been added to the component or
not, and inside `BeginModify`/`EndModify` too. Setting the `...ExpansionMode` properties
works; only the coordinate-valued setters crash. `SolderMaskExpansionTop`,
`SolderMaskTopExpansion` and similar names give "Undeclared identifier".

Fix (verified: reads back 0.05 mm mask, -0.25 mm paste): add the pad to the component
first, then set the values through the pad cache record:

```pascal
AddToComp(Comp, Pad);
Pad.BeginModify;
Cache := Pad.GetState_Cache;                 { Cache : TPadCache }
Cache.SolderMaskExpansion      := MMsToCoord(0.05);
Cache.SolderMaskExpansionValid := eCacheManual;
Cache.PasteMaskExpansion       := -MMsToCoord(W);   { negative pad width = no paste }
Cache.PasteMaskExpansionValid  := eCacheManual;
Pad.SetState_Cache := Cache;
Pad.EndModify;
```

Never write `Pad.SolderMaskExpansion :=` or `Pad.PasteMaskExpansion :=` in a script.

### 2. Access violations are not caught by Try/Except

The crash in item 1 bypassed the script's `Try ... Except` and showed Altium's own
crash dialog, so the "stopped while <step>" message never appeared. Don't rely on
Try/Except to find where a script fails. Use a log file instead (item 9).

### 3. DelphiScript evaluates both sides of And/Or

`If (SchLib = Nil) Or (SchLib.ObjectID <> eSchLib)` reads `ObjectID` on a nil object and
crashes. Give each nil check its own `If`.

### 4. New schematic components may have a nil Comment

Don't assign `SymComp.Comment.Text` on a component made with `SchObjectFactory`.
Set `LibReference`, `ComponentDescription` and `Designator.Text` only.

### 5. Guard the library objects

`PCBServer.GetCurrentPCBLibrary` is nil unless a PcbLib tab is active, and
`FpLib.Board` can be nil. `SchServer.GetCurrentSchDocument` may be a schematic sheet,
not a library. Check each and show a message, as the template does.

## Running scripts in Altium

### 6. Altium keeps a loaded script in memory

Once a `.PrjScr`/`.pas` has been loaded (it shows in File > Run Script's list), editing
the file on disk has **no effect**. Altium keeps running the old copy. After changing a
script, either close that script project in Altium (Projects panel > right-click >
Close Project) or load a copy under a new file name (e.g. `<base>_v2.pas` plus a
matching `.PrjScr`) and run that.

### 7. File > Run Script > Browse only accepts script projects

Browse > From file filters for project files. Pointing it at a bare `.pas` does nothing.
Always give it a `.PrjScr` whose `[Document1] DocumentPath=` is the `.pas` file.

### 8. A script error leaves the debugger paused

A compile error (e.g. "Undeclared identifier") opens the `.pas` in an editor tab with
the line highlighted and leaves the script paused. Every later run then fails with
"Another script executing now". Fix: click the `.pas` tab, then Run > Stop (Ctrl+F3),
then click the library tab again before the next run.

### 9. Finding the failing line: log to a file

Altium's error dialogs don't say which line failed. Write a small diagnostic script that
appends a line to a log file after each statement, then read the log:

```pascal
Var Log : TStringList;
Procedure L(S : String);
Begin
    Log.Add(S);
    Log.SaveToFile('C:\path\to\diag.log');
End;
{ In the procedure: Log := TStringList.Create; L('start'); ... L('after X'); }
```

The last logged line is the one before the crash.

### 10. Crashed runs leave junk components

A crash after `RegisterComponent` leaves an empty footprint with the same name in the
PcbLib. Rerunning then creates a duplicate. Before rerunning, delete it in the PCB
Library panel, or remove it from a script (iterate with `LibraryIterator_Create`,
collect matches in a `TInterfaceList`, then `Lib.RemoveComponent(...)` after the loop).

### 11. Run from File > Run Script with the library tab active

The template's procedures act on the active document. The File menu layout changes
with the active document: some documents (e.g. a newly created library) add a
"Save As..." row, which pushes "Run Script..." down one row, so a click at the old
position opens the Import Wizard instead (cancel it). Always open the File menu,
screenshot it, then click "Run Script...".

In the Run Script dialog the newest script project is at the bottom of the list and
may be scrolled out of view. Click the `.pas` row of your project and press Down to
select its first procedure, or scroll the list, then screenshot before pressing OK.

## Driving Altium with computer use

### 12. Computer-use screenshots of Altium come back blank

`mcp__computer-use__screenshot` returned a solid dark grey screen while Altium was in
front, even though clicks worked. Capture the screen with Windows instead, using
`scripts/screencap.ps1`, which writes a PNG you can Read:

```
powershell -ExecutionPolicy Bypass -File scripts/screencap.ps1 <out.png>
```

That capture is 1920x1080 (real pixels). The computer-use click tools use their own
coordinate frame (reported in the screenshot result, e.g. 1456x819). Convert:
`tool = real * (tool_width / real_width)`, e.g. x 0.7583 for 1456/1920. Re-capture after
every action that changes the screen.

### 13. Don't launch a second Altium

`open_application("Altium Designer")` started a second Altium instance when one was
already running. Check first with `Get-Process X2`; if it is running, bring its window
forward instead of opening the app again.

### 14. Test in a throwaway library, then remove it cleanly

To try a new or changed script without touching the user's libraries: File > New >
Library > PCB Library (it is added to the focused project as `PcbLibN`), run the
script there, check it, then in the Projects panel right-click it > Remove from
Project > **Exclude from project** (never "Delete file"), then right-click it under
Free Documents > Close.

### 15. Saving a library a script created: "A command is currently active"

Saving a PcbLib the script built (Ctrl+S, File > Save or the Projects panel's Save)
showed "A command is currently active and save cannot be completed at this time" every
time, even after Escape and right-clicks on the canvas. Answering **Yes** ("save copy of
current document") opens a second dialog; type the real file name (not the offered
"Copy of ...") and click Save. That writes the full library. Then swap the in-memory
document for the saved file: Projects panel > right-click the old `PcbLibN` > Remove
from Project > **Exclude from project**, close it with **Don't Save**, then Project > Add
Existing to Project > the saved `.PcbLib`, and save the project. Check the file on disk
afterwards (its size, and that it contains the footprint name).

SchLibs saved normally.

### 16. File dialogs

In the Windows file dialog, typing a path into "File name" sometimes landed before the
box had focus. Click the File name box first, then type the full path and press
Enter. Or double-click the file in the list if the dialog is already in the right
folder (it opens in the folder used last).

### 17. Workspace component won't save: "contains more than one component"

What happened (ADXL367, 2026-11-03): the user built the component in the workspace
Component Editor (Capstone workspace), clicked Add Footprint > New and Add Symbol > New,
ran `CreateFootprint` / `CreateSymbol` in those new documents, and Save to Server failed
validation with two errors in turn:

- `[Fatal Error] Footprint "<fp_name>" contains more than one component`
- after fixing that: `[Error] Number of pads in the footprint <fp_name> (12) exceeds
  number of pins in the symbol <part>-Symbol-1 (0)`

Why: a new workspace footprint or symbol document is not empty. Altium creates it with
one blank default item (e.g. `<part>-Symbol-1`, 0 pins). The script then
`RegisterComponent` / `AddSchComponent`s a *second* item next to it. A workspace
footprint or symbol document must hold exactly one item, and the validator also checks
the blank symbol, not the scripted one.

Fix: delete every item that is not the scripted one and has no primitives (footprint)
or no pins (symbol). The template now does this at the end of `CreateFootprint` and
`CreateSymbol` (`RemoveEmptyFootprintsFrom` / `RemoveEmptySymbolsFrom`), and has
standalone `RemoveEmptyFootprints` / `RemoveEmptySymbols` procedures for documents an
older script already filled. Run those from File > Run Script with the footprint or
symbol tab active, save that document (Ctrl+S), then Save to Server on the component.
Only empty items are removed, so a normal multi-footprint PcbLib is safe.

After the fix the only remaining message was the warning `Offset Component Origin`:
pads are centred on the origin, but the pin-1 dot and courtyard extend further on one
side, so the bounding box isn't. It is harmless; Release past it.

Also seen in this session (AD 25.5.2): `mcp__computer-use__screenshot` showed Altium
normally (item 12 didn't happen), and after the `.pas` was edited on disk, File > Run
Script listed and ran the new procedures without closing the script project (item 6
didn't happen). Still check the Run Script list for the new procedure names before
relying on this.
