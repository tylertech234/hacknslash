# build_release.ps1
# Builds Cyber Survivor into a standalone Windows executable for itch.io distribution.
# Run from the repo root:  .\build_release.ps1

$ErrorActionPreference = "Stop"
$GameName  = "CyberSurvivor"
$DistDir   = "dist\$GameName"

# Read version from settings.py so it stays in sync automatically
$Version   = python -c "from src.settings import VERSION; print(VERSION)"
if (-not $Version) { $Version = "dev" }

Write-Host ""
Write-Host "=== Cyber Survivor — itch.io Release Build ===" -ForegroundColor Cyan
Write-Host ""

# 1. Ensure PyInstaller is installed
Write-Host "[1/4] Checking PyInstaller..." -ForegroundColor Yellow
pip show pyinstaller > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "     Installing PyInstaller..." -ForegroundColor Gray
    pip install pyinstaller
}
Write-Host "     OK" -ForegroundColor Green

# 2. Run PyInstaller
Write-Host "[2/4] Building executable (this takes a minute)..." -ForegroundColor Yellow
pyinstaller cyber_survivor.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller build failed." -ForegroundColor Red
    exit 1
}
Write-Host "     OK — output in $DistDir" -ForegroundColor Green

# 3. Strip development files from the distribution directory
#    (save files and cache are generated fresh on first run — don't ship them)
Write-Host "[3/4] Cleaning dist directory..." -ForegroundColor Yellow
$filesToRemove = @(
    "$DistDir\legacy_save.json",
    "$DistDir\settings_save.json",
    "$DistDir\compendium_save.json",
    "$DistDir\game.log",
    "$DistDir\_patch_features.py"
)
foreach ($f in $filesToRemove) {
    if (Test-Path $f) { Remove-Item $f -Force; Write-Host "     Removed: $f" }
}
Write-Host "     OK" -ForegroundColor Green

# 4. Zip the output folder
Write-Host "[4/4] Creating release zip..." -ForegroundColor Yellow
$ZipPath = "$GameName-Windows-v$Version.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path "$DistDir\*" -DestinationPath $ZipPath
Write-Host "     Created: $ZipPath" -ForegroundColor Green

Write-Host ""
Write-Host "=== BUILD COMPLETE ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Upload '$ZipPath' to itch.io:" -ForegroundColor White
Write-Host "  Kind  ->  Executable"          -ForegroundColor Gray
Write-Host "  OS    ->  Windows"              -ForegroundColor Gray
Write-Host "  Exe   ->  CyberSurvivor.exe"   -ForegroundColor Gray
Write-Host ""
