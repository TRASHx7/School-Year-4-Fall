# Render every *_preview.svg in a folder to PNG with headless Microsoft Edge,
# so the previews can be viewed as images.
# Usage: powershell -ExecutionPolicy Bypass -File render_previews.ps1 <folder>
param([Parameter(Mandatory = $true)][string]$Dir)
$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
          "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { Write-Error "Microsoft Edge not found; open the SVG previews in a browser instead."; exit 1 }
$profileDir = Join-Path $env:TEMP "svg-render-profile"
Get-ChildItem -Path $Dir -Filter *_preview.svg | ForEach-Object {
    $svg = Get-Content $_.FullName -Raw
    $w = [int]([regex]::Match($svg, 'width="(\d+)').Groups[1].Value)
    $h = [int]([regex]::Match($svg, 'height="(\d+)').Groups[1].Value)
    $png = [IO.Path]::ChangeExtension($_.FullName, ".png")
    $url = ([Uri]$_.FullName).AbsoluteUri
    & $edge --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$profileDir" `
        --window-size="$w,$h" --screenshot="$png" $url 2>$null | Out-Null
    $tries = 0
    while (-not (Test-Path $png) -and $tries -lt 20) { Start-Sleep -Milliseconds 250; $tries++ }
    if (Test-Path $png) { "rendered $png" } else { Write-Warning "could not render $($_.Name)" }
}
