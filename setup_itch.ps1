# setup_itch.ps1 — One-time itch.io / butler setup
# Run this once before using itch_push.ps1
#
# What it does:
#   1. Downloads butler.exe for Windows to D:\_git\butler\windows-amd64\
#   2. Launches butler login (browser OAuth — you click Approve once)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ButlerDir = "D:\_git\butler\windows-amd64"
$ButlerExe = Join-Path $ButlerDir "butler.exe"

# ── Step 1: Download butler ───────────────────────────────────────────────────
if (Test-Path $ButlerExe) {
    Write-Host "butler.exe already present at $ButlerExe" -ForegroundColor Green
} else {
    Write-Host "Downloading butler for Windows..." -ForegroundColor Cyan
    $null = New-Item -ItemType Directory -Force $ButlerDir
    $ZipDest = Join-Path $ButlerDir "butler-windows.zip"

    Invoke-WebRequest `
        -Uri "https://broth.itch.zone/butler/windows-amd64/LATEST/archive/default" `
        -OutFile $ZipDest

    Write-Host "Extracting..." -ForegroundColor Cyan
    Expand-Archive -Path $ZipDest -DestinationPath $ButlerDir -Force
    Remove-Item $ZipDest

    if (-not (Test-Path $ButlerExe)) {
        throw "butler.exe not found after extraction. Check $ButlerDir"
    }
    Write-Host "butler.exe downloaded successfully." -ForegroundColor Green
}

# Show version to confirm it works
$ver = & $ButlerExe version 2>&1
Write-Host "  butler $ver" -ForegroundColor DarkGray

# ── Step 2: Authenticate ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "Launching butler login — your browser will open." -ForegroundColor Cyan
Write-Host "Click 'Grant access' on the itch.io page, then return here." -ForegroundColor Yellow
Write-Host ""

& $ButlerExe login

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All set! You can now run:" -ForegroundColor Green
    Write-Host "  .\itch_push.ps1            # push both Windows + HTML5" -ForegroundColor White
    Write-Host "  .\itch_push.ps1 -Channel html5     # HTML5 only" -ForegroundColor White
    Write-Host "  .\itch_push.ps1 -Channel windows   # Windows only" -ForegroundColor White
} else {
    Write-Host "butler login returned exit code $LASTEXITCODE." -ForegroundColor Red
    Write-Host "Try running manually: & `"$ButlerExe`" login" -ForegroundColor Yellow
}
