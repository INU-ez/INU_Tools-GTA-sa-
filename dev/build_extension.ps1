# Build INU Tools as a Blender extension package.
#
# Uses Blender's official `extension build` command which:
#   - Validates blender_manifest.toml
#   - Excludes __pycache__/, .pyc, .git/, dev files automatically
#   - Produces a .zip with the correct extension naming (id-version.zip)
#
# Run from repo root:  .\dev\build_extension.ps1

$ErrorActionPreference = 'Stop'

# ── Configure ──────────────────────────────────────────────────────────
$BlenderExe = "D:\Program\Blender 5.1\blender.exe"
$SourceDir  = "INU_tools"
$OutputDir  = "."

# ── Pre-build cleanup ──────────────────────────────────────────────────
Write-Host "Cleaning __pycache__ folders..." -ForegroundColor Cyan
Get-ChildItem -Path $SourceDir -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force

# ── Build ──────────────────────────────────────────────────────────────
Write-Host "Building extension via Blender CLI..." -ForegroundColor Cyan
& $BlenderExe --command extension build `
    --source-dir $SourceDir `
    --output-dir $OutputDir 2>&1 |
    Where-Object { $_ -match '^(building|complete|created|error|Error)' }

if (Test-Path "inu_tools_gta_sa-*.zip") {
    Write-Host "`nDone." -ForegroundColor Green
    Get-ChildItem "inu_tools_gta_sa-*.zip" | Format-Table Name, Length, LastWriteTime
} else {
    Write-Host "Build did not produce a zip — check output above." -ForegroundColor Red
    exit 1
}
