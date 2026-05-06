# Build INU Tools as a Blender extension package — FULL edition.
#
# This branch (full-build) is the GitHub-release variant: NVTT GPU
# compression is included, parallelism is on, no extensions.blender.org
# restrictions. Output zip is renamed with a `-full` suffix so users
# can tell the FULL build apart from the STORE build by filename.
#
# Uses Blender's official `extension build` command which:
#   - Validates blender_manifest.toml
#   - Excludes __pycache__/, .pyc, .git/, dev files automatically
#   - Produces a .zip with the correct extension naming (id-version.zip)
#
# Run from repo root.

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# --- Configure ---------------------------------------------------------
$BlenderExe = "D:\Program\Blender 5.1\blender.exe"
$SourceDir  = "INU_tools"
$OutputDir  = "."

# --- Pre-build cleanup -------------------------------------------------
Write-Host "Cleaning __pycache__ folders..." -ForegroundColor Cyan
Get-ChildItem -Path $SourceDir -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force

# --- Build -------------------------------------------------------------
# NVTT lives directly inside INU_tools/tools/txd_export.py on the
# full-build branch (subprocess.run on nvcompress.exe), no extras/
# copy step needed.
Write-Host "Building extension via Blender CLI..." -ForegroundColor Cyan
& $BlenderExe --command extension build `
    --source-dir $SourceDir `
    --output-dir $OutputDir 2>&1 |
    Where-Object { $_ -match '^(building|complete|created|error|Error)' }

# --- Rename output zip with -full suffix -------------------------------
$builtZip = Get-ChildItem "inu_tools_gta_sa-*.zip" |
    Where-Object { $_.Name -notmatch '-full\.zip$' } |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $builtZip) {
    Write-Host "Build did not produce a zip -- check output above." -ForegroundColor Red
    exit 1
}

$fullZipName = $builtZip.Name -replace '\.zip$', '-full.zip'
Move-Item -Path $builtZip.FullName -Destination $fullZipName -Force

Write-Host "`nDone." -ForegroundColor Green
Get-ChildItem "inu_tools_gta_sa-*-full.zip" | Format-Table Name, Length, LastWriteTime
Write-Host "Build mode: FULL (NVTT included, parallelism enabled -- GitHub release)" -ForegroundColor Green
