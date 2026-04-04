# build_web.ps1 — Build Cyber Survivor as a static HTML5 / WebAssembly bundle
# Output: build/web/  (contains index.html + assets)
# Requires:  Python 3.11+, pip install pygbag>=0.9.0

param(
    [string]$AppName = "CyberSurvivor",
    [string]$OutDir  = "build/web"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── 1. Ensure pygbag is installed ───────────────────────────────────────────
Write-Host "Checking pygbag..." -ForegroundColor Cyan
$pygbagVersion = python -m pygbag --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pygbag..." -ForegroundColor Yellow
    pip install "pygbag>=0.9.0"
    if ($LASTEXITCODE -ne 0) { throw "pygbag install failed." }
}
else {
    Write-Host "  Found: $pygbagVersion" -ForegroundColor Green
}

# ── 2. Clean previous web build ─────────────────────────────────────────────
if (Test-Path $OutDir) {
    Write-Host "Removing old $OutDir ..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $OutDir
}

# ── 3. Run pygbag build ───────────────────────────────────────────────────────
# --build   → static output (no dev server)
# --archive → packages everything into build/<AppName>.zip too
Write-Host ""
Write-Host "Building web bundle (this may take a minute)..." -ForegroundColor Cyan
python -m pygbag --build --app_name $AppName main.py

if ($LASTEXITCODE -ne 0) { throw "pygbag build failed." }

# pygbag outputs to build/<AppName>/ — rename to build/web/ for clarity
$pygbagOut = Join-Path "build" $AppName
if (Test-Path $pygbagOut) {
    Move-Item $pygbagOut $OutDir
}

# ── 4. Sanity check ──────────────────────────────────────────────────────────
$indexFile = Join-Path $OutDir "index.html"
if (-not (Test-Path $indexFile)) {
    Write-Warning "index.html not found in $OutDir — check pygbag output."
}
else {
    Write-Host ""
    Write-Host "Web build ready:" -ForegroundColor Green
    Write-Host "  $((Resolve-Path $OutDir).Path)" -ForegroundColor White
    Write-Host ""
    Write-Host "Test locally (optional):" -ForegroundColor Cyan
    Write-Host "  python -m http.server 8000 --directory $OutDir" -ForegroundColor White
    Write-Host "  then open http://localhost:8000"
}
