# Capture the primary screen to a PNG. Use this when computer-use screenshots of
# Altium come back blank (see references/altium_pitfalls.md, item 12).
# Usage: powershell -ExecutionPolicy Bypass -File screencap.ps1 <out.png>
param([Parameter(Mandatory = $true)][string]$Out)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object Drawing.Bitmap $b.Width, $b.Height
$g = [Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Location, [Drawing.Point]::Empty, $b.Size)
$bmp.Save($Out)
$g.Dispose(); $bmp.Dispose()
"$Out ($($b.Width)x$($b.Height))"
