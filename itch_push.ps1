# itch_push.ps1 — Push Cyber Survivor builds to itch.io via butler
#
# First-time setup:
#   1. Run this script with -Setup to download butler for Windows
#   2. Run "D:\_git\butler\windows-amd64\butler.exe login"   (once, browser OAuth)
#   3. Create the itch.io project at https://itch.io/game/new
#
# Normal publish:
#   .\itch_push.ps1 -User YOUR_ITCH_USERNAME
#
# Push only one channel:
#   .\itch_push.ps1 -User YOUR_ITCH_USERNAME -Channel html5
#   .\itch_push.ps1 -User YOUR_ITCH_USERNAME -Channel windows

param(
    [string]$User    = "YOUR_ITCH_USERNAME",   # your itch.io username
    [string]$Game    = "cyber-survivor",        # itch.io project URL slug
    [string]$Version = "v0.9.1",

    # Which channels to push: "windows", "html5", or "all"
    [ValidateSet("all","windows","html5")]
    [string]$Channel = "all",

    # File paths
    [string]$WinZip  = "dist/CyberSurvivor-Windows-$Version.zip",
    [string]$WebDir  = "build/web",
    [string]$ButlerDir = "D:\_git\butler\windows-amd64",

    # Pass -Setup to download / update butler
    [switch]$Setup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ButlerExe = Join-Path $ButlerDir "butler.exe"

# ── Helper ───────────────────────────────────────────────────────────────────
function Invoke-Butler {
    param([string[]]$Args)
    & $ButlerExe @Args
    if ($LASTEXITCODE -ne 0) { throw "butler exited with code $LASTEXITCODE" }
}

# ── Optional: download butler for Windows ───────────────────────────────────
if ($Setup) {
    Write-Host "Downloading butler for Windows..." -ForegroundColor Cyan
    $null = New-Item -ItemType Directory -Force $ButlerDir

    $ZipDest = Join-Path $ButlerDir "butler-windows.zip"
    Invoke-WebRequest `
        -Uri "https://broth.itch.ovh/butler/windows-amd64/LATEST/archive/default" `
        -OutFile $ZipDest

    Expand-Archive -Path $ZipDest -DestinationPath $ButlerDir -Force
    Remove-Item $ZipDest

    if (-not (Test-Path $ButlerExe)) {
        throw "butler.exe not found after extraction — check $ButlerDir"
    }

    Write-Host "butler installed at $ButlerExe" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: authenticate once with itch.io" -ForegroundColor Yellow
    Write-Host "  & `"$ButlerExe`" login" -ForegroundColor White
    exit 0
}

# ── Pre-flight checks ────────────────────────────────────────────────────────
if (-not (Test-Path $ButlerExe)) {
    Write-Host "butler.exe not found." -ForegroundColor Red
    Write-Host "Run this script with -Setup to download it:" -ForegroundColor Yellow
    Write-Host "  .\itch_push.ps1 -Setup" -ForegroundColor White
    exit 1
}

if ($User -eq "YOUR_ITCH_USERNAME") {
    Write-Host "Set your itch.io username with -User flag:" -ForegroundColor Red
    Write-Host "  .\itch_push.ps1 -User your_username" -ForegroundColor White
    exit 1
}

$GameTarget = "${User}/${Game}"
Write-Host "Publishing $GameTarget @ $Version" -ForegroundColor Cyan
Write-Host "  butler: $ButlerExe" -ForegroundColor DarkGray
Write-Host ""

# ── Push Windows build ───────────────────────────────────────────────────────
if ($Channel -in "all","windows") {
    if (-not (Test-Path $WinZip)) {
        Write-Warning "Windows zip not found: $WinZip  — build first with .\build_release.ps1"
        if ($Channel -eq "windows") { exit 1 }
    }
    else {
        Write-Host "Pushing Windows build..." -ForegroundColor Cyan
        Invoke-Butler push $WinZip "${GameTarget}:windows-stable" --userversion $Version
        Write-Host "  Windows channel updated." -ForegroundColor Green
    }
}

# ── Push HTML5 build ─────────────────────────────────────────────────────────
if ($Channel -in "all","html5") {
    if (-not (Test-Path $WebDir)) {
        Write-Warning "Web build not found: $WebDir  — build first with .\build_web.ps1"
        if ($Channel -eq "html5") { exit 1 }
    }
    else {
        Write-Host "Pushing HTML5 build..." -ForegroundColor Cyan
        Invoke-Butler push $WebDir "${GameTarget}:html5" --userversion $Version
        Write-Host "  HTML5 channel updated." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Done! View your page at https://${User}.itch.io/${Game}" -ForegroundColor Green
