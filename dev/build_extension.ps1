# Build INU Tools as a Blender extension package.
#
# Uses Blender's official `extension build` command which:
#   - Validates blender_manifest.toml
#   - Excludes __pycache__/, .pyc, .git/, dev files automatically
#   - Produces a .zip with the correct extension naming (id-version.zip)
#
# Two modes:
#   .\dev\build_extension.ps1           — full build with NVTT (for GitHub release).
#                                          Copies extras/nvtt_compress.py into the
#                                          addon, builds, leaves it for dev testing.
#   .\dev\build_extension.ps1 -Store    — extensions.blender.org build (NO NVTT).
#                                          Removes nvtt_compress.py from addon if
#                                          present, builds the ToS-compliant zip,
#                                          does NOT restore (to keep zip clean).
#
# Run from repo root.

[CmdletBinding()]
param(
    [switch]$Store
)

$ErrorActionPreference = 'Stop'

# ── Configure ──────────────────────────────────────────────────────────
$BlenderExe   = "D:\Program\Blender 5.1\blender.exe"
$SourceDir    = "INU_tools"
$OutputDir    = "."
$NvttSource   = "extras\nvtt_compress.py"
$NvttTarget   = "$SourceDir\tools\nvtt_compress.py"

# ── Pre-build cleanup ──────────────────────────────────────────────────
Write-Host "Cleaning __pycache__ folders..." -ForegroundColor Cyan
Get-ChildItem -Path $SourceDir -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force

# ── Manage NVTT module presence based on build mode ────────────────────
if ($Store) {
    if (Test-Path $NvttTarget) {
        Write-Host "Store build: removing $NvttTarget (no NVTT in extensions.blender.org zip)..." -ForegroundColor Yellow
        Remove-Item -Path $NvttTarget -Force
    } else {
        Write-Host "Store build: $NvttTarget already absent (good)" -ForegroundColor Yellow
    }
} else {
    if (-not (Test-Path $NvttSource)) {
        Write-Host "Error: $NvttSource not found — can't build full release." -ForegroundColor Red
        exit 1
    }
    Write-Host "Full build: copying $NvttSource → $NvttTarget..." -ForegroundColor Green
    Copy-Item -Path $NvttSource -Destination $NvttTarget -Force
}

# ── Build ──────────────────────────────────────────────────────────────
Write-Host "Building extension via Blender CLI..." -ForegroundColor Cyan
& $BlenderExe --command extension build `
    --source-dir $SourceDir `
    --output-dir $OutputDir 2>&1 |
    Where-Object { $_ -match '^(building|complete|created|error|Error)' }

if (Test-Path "inu_tools_gta_sa-*.zip") {
    Write-Host "`nDone." -ForegroundColor Green
    Get-ChildItem "inu_tools_gta_sa-*.zip" | Format-Table Name, Length, LastWriteTime
    if ($Store) {
        Write-Host "Build mode: STORE (NVTT excluded — ToS-compliant for extensions.blender.org)" -ForegroundColor Yellow
    } else {
        Write-Host "Build mode: FULL (NVTT included — for GitHub release)" -ForegroundColor Green
    }
} else {
    Write-Host "Build did not produce a zip — check output above." -ForegroundColor Red
    exit 1
}
