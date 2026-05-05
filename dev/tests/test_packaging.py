"""Build the addon two ways (store and full) and assert each ships
the right contents.

These tests need a Blender executable. They auto-skip when one isn't
findable so the rest of the pure-Python test suite stays runnable on
machines without Blender.

Why both builds:
  * STORE  — uploaded to extensions.blender.org. NVTT must be absent
             (third-party binary, ToS violation).
  * FULL   — attached to the GitHub release. NVTT included for users
             who want hardware DXT compression.
A single missing/extra file on either side breaks the dual-release
plan, so we build both and verify each.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest


# ── Paths ────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
ADDON_DIR = REPO_ROOT / "INU_tools"
NVTT_SOURCE = REPO_ROOT / "extras" / "nvtt_compress.py"
NVTT_TARGET = ADDON_DIR / "tools" / "nvtt_compress.py"


# ── Blender discovery ────────────────────────────────────────────

def _find_blender() -> str | None:
    """Locate a blender executable. Mirrors `dev/tests/run_e2e.ps1`
    candidates, plus the `BLENDER` env var, plus PATH lookup."""
    if env := os.environ.get("BLENDER"):
        if Path(env).is_file():
            return env

    candidates = [
        r"D:\Program\Blender 5.1\blender.exe",
        r"D:\Program\blender-4.2.20-windows-x64\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        "/usr/bin/blender",
        "/usr/local/bin/blender",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c

    if path_blender := shutil.which("blender"):
        return path_blender
    return None


@pytest.fixture(scope="module")
def blender() -> str:
    exe = _find_blender()
    if not exe:
        pytest.skip("Blender executable not found; set BLENDER env var to run packaging tests")
    return exe


# ── Build runner ─────────────────────────────────────────────────

def _run(argv: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(argv, capture_output=True, text=True, check=False)
    return p.returncode, p.stdout, p.stderr


def _build_zip(blender: str, source_dir: Path, output_dir: Path) -> Path:
    """Invoke Blender's `extension build` command. Returns the produced
    zip path. Asserts on non-zero exit and on missing artefact."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rc, out, err = _run([
        blender, "--command", "extension", "build",
        "--source-dir", str(source_dir),
        "--output-dir", str(output_dir),
    ])
    assert rc == 0, (
        f"`extension build` failed (rc={rc})\n"
        f"stdout:\n{out}\nstderr:\n{err}"
    )
    zips = sorted(output_dir.glob("*.zip"))
    assert zips, f"no zip produced in {output_dir}; build output:\n{out}"
    # extension build emits exactly one zip per invocation; if more,
    # something stale is in the dir and our assertion needs updating.
    assert len(zips) == 1, f"expected exactly one zip, got: {[z.name for z in zips]}"
    return zips[0]


def _validate_zip(blender: str, zip_path: Path) -> None:
    """Run Blender's official extension validator on the produced zip.
    A non-zero exit here is what extensions.blender.org would also
    reject — fix locally before submission."""
    rc, out, err = _run([
        blender, "--command", "extension", "validate", str(zip_path),
    ])
    assert rc == 0, (
        f"`extension validate` rejected {zip_path.name} (rc={rc})\n"
        f"stdout:\n{out}\nstderr:\n{err}"
    )


# ── Build mode setup ─────────────────────────────────────────────

@pytest.fixture
def store_layout():
    """Ensure NVTT module is ABSENT during the test, then restore
    whatever was there before. Matches `dev/build_extension.ps1 -Store`.

    Both this fixture and `full_layout` save+restore so tests never
    leak NVTT state across each other or to a subsequent CI artifact
    build step. Earlier versions left NVTT in place after `full_layout`,
    which made the order-of-execution part of the contract — fragile."""
    pre_existing = NVTT_TARGET.read_bytes() if NVTT_TARGET.is_file() else None
    if pre_existing is not None:
        NVTT_TARGET.unlink()
    try:
        yield
    finally:
        if pre_existing is not None:
            NVTT_TARGET.write_bytes(pre_existing)
        elif NVTT_TARGET.is_file():
            # Some interrupted run could have left NVTT behind; clean.
            NVTT_TARGET.unlink()


@pytest.fixture
def full_layout():
    """Ensure NVTT module is PRESENT during the test, then restore
    whatever was there before."""
    if not NVTT_SOURCE.is_file():
        pytest.skip(f"{NVTT_SOURCE.name} missing — can't build full release")
    pre_existing = NVTT_TARGET.read_bytes() if NVTT_TARGET.is_file() else None
    if pre_existing is None:
        shutil.copy2(NVTT_SOURCE, NVTT_TARGET)
    try:
        yield
    finally:
        if pre_existing is None:
            # We added the file — remove it.
            if NVTT_TARGET.is_file():
                NVTT_TARGET.unlink()
        else:
            NVTT_TARGET.write_bytes(pre_existing)


# ── Tests: store build ───────────────────────────────────────────

def test_store_build_succeeds(tmp_path, blender, store_layout):
    """The store zip builds and `extension validate` accepts it."""
    zip_path = _build_zip(blender, ADDON_DIR, tmp_path)
    _validate_zip(blender, zip_path)


def test_store_build_excludes_nvtt(tmp_path, blender, store_layout):
    """Walk the produced store zip; nothing matching NVTT may be
    inside. This is the ToS-critical check — NVTT bundled in a store
    upload triggers immediate rejection."""
    zip_path = _build_zip(blender, ADDON_DIR, tmp_path)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()

    nvtt_files = [n for n in names if "nvtt" in n.lower()]
    assert not nvtt_files, (
        f"NVTT files leaked into store zip {zip_path.name}: {nvtt_files}"
    )


def test_store_build_no_pycache(tmp_path, blender, store_layout):
    """`__pycache__/` is excluded by manifest, but verify — a stale
    .pyc snuck in once before."""
    zip_path = _build_zip(blender, ADDON_DIR, tmp_path)
    with zipfile.ZipFile(zip_path) as zf:
        offenders = [
            n for n in zf.namelist()
            if "__pycache__" in n or n.endswith(".pyc")
        ]
    assert not offenders, f"bytecode leaked into store zip: {offenders}"


# ── Tests: full build ────────────────────────────────────────────

def test_full_build_succeeds(tmp_path, blender, full_layout):
    """The full (NVTT-included) zip builds and validates."""
    zip_path = _build_zip(blender, ADDON_DIR, tmp_path)
    _validate_zip(blender, zip_path)


def test_full_build_includes_nvtt(tmp_path, blender, full_layout):
    """The full zip is for users who want NVTT — confirm it actually
    ships the module."""
    zip_path = _build_zip(blender, ADDON_DIR, tmp_path)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    has_nvtt = any(n.endswith("nvtt_compress.py") for n in names)
    assert has_nvtt, f"full zip is missing nvtt_compress.py:\n  {names}"


# ── Sanity: zip is a real addon ──────────────────────────────────

def test_store_zip_contains_manifest(tmp_path, blender, store_layout):
    """Every produced zip must have blender_manifest.toml at its
    addon-root path. If it's missing, the addon won't register.
    Pinned to the store build so CI matrix filtering by `-k store`
    picks it up exactly once (full and store would both pass identically,
    so checking once is enough)."""
    zip_path = _build_zip(blender, ADDON_DIR, tmp_path)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    manifests = [n for n in names if n.endswith("blender_manifest.toml")]
    assert manifests, f"zip missing blender_manifest.toml: {names[:20]}"
