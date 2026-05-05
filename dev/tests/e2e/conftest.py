"""E2E tests — run *inside Blender* via dev/tests/run_e2e.ps1.

These tests exercise the full operator path (bpy.ops.gtatools.*),
so they need a real Blender process. Pure-Python unit tests live one
level up in dev/tests/ and run on regular CI without Blender.

The ASSETS_DIR fixture points to F:/GitHub/INU Tools TEST — a folder
the user fills with hand-picked vanilla .dff/.col/.txd/.ifp samples
copied (NEVER edited) from the game install. Add files there to grow
coverage; conftest auto-skips a test if the file it needs is missing.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


# ── Blender gate ─────────────────────────────────────────────────
# Skip the entire e2e folder if pytest somehow gets invoked outside
# Blender (e.g. from a regular pytest run on CI). The runner script
# launches Blender with --background, so bpy is always present there.

bpy = pytest.importorskip("bpy", reason="e2e tests require Blender (run via run_e2e.ps1)")


# ── Asset folder ─────────────────────────────────────────────────

ASSETS_DIR = Path(r"F:\GitHub\INU Tools TEST")


@pytest.fixture(scope="session")
def assets_dir() -> Path:
    if not ASSETS_DIR.is_dir():
        pytest.skip(f"Test assets dir not found: {ASSETS_DIR}")
    return ASSETS_DIR


@pytest.fixture
def asset(assets_dir):
    """Return a callable that resolves a filename inside ASSETS_DIR
    and skips the test if it is missing — keeps tests resilient when
    the user adds/removes sample files."""
    def _resolve(name: str) -> str:
        p = assets_dir / name
        if not p.is_file():
            pytest.skip(f"Asset missing: {p.name}")
        return str(p)
    return _resolve


# ── Scene reset between tests ────────────────────────────────────

def _wipe_data_blocks():
    """Manually purge every data-block from `bpy.data`.

    Originally this fixture used `bpy.ops.wm.read_factory_settings(use_empty=True)`,
    which is the obvious "File → New → General" equivalent. But that
    fires `load_post` handlers, and on this machine one of them
    (`bl_ext.user_default.uvpackmaster4`) raises a KeyError that leaves
    custom PropertyGroups on bpy.types.Material in a bad state — every
    subsequent `mat.inu` access then fails with
        AttributeError: 'Material' object has no attribute 'inu'

    Manual cleanup avoids triggering load_post entirely and keeps the
    addon's registration stable across test boundaries.
    """
    # Order matters: remove dependents (objects) before their data
    # (meshes/materials), or removal fails with "still referenced".
    for collection in (
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.textures,
        bpy.data.actions,
        bpy.data.curves,
        bpy.data.lights,
        bpy.data.cameras,
    ):
        for item in list(collection):
            collection.remove(item, do_unlink=True)
    # Collections (other than master) come last — children must already
    # be gone so the unlink chain is short.
    master = bpy.context.scene.collection
    for c in list(bpy.data.collections):
        if c is not master:
            bpy.data.collections.remove(c)

    # The DFF/COL importers fall back to `bpy.context.collection` when
    # no target is given, so we need at least one user-facing collection
    # in the scene — and it has to be the *active* one. Without this,
    # `obj.objects.link()` blows up with "'NoneType' has no attribute
    # 'objects'" on the second test in any session.
    if not master.children:
        default = bpy.data.collections.new("Collection")
        master.children.link(default)
    # Activate the first child so bpy.context.collection resolves.
    layer_root = bpy.context.view_layer.layer_collection
    for lc in layer_root.children:
        if lc.collection is not master:
            bpy.context.view_layer.active_layer_collection = lc
            break


@pytest.fixture(autouse=True)
def fresh_scene():
    """Wipe scene contents between tests so cross-test leaks can't
    mask real bugs. See `_wipe_data_blocks` for why we don't use
    `read_factory_settings` here."""
    _wipe_data_blocks()
    yield


# ── Addon must be registered ─────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def ensure_addon_loaded():
    """Bail out loudly if the user's Blender doesn't have INU Tools
    enabled — every test downstream calls bpy.ops.gtatools.* and would
    otherwise fail with a confusing AttributeError on bpy.ops.gtatools."""
    if not hasattr(bpy.ops, "gtatools"):
        pytest.exit(
            "INU Tools addon is not registered in this Blender. "
            "Enable it in Edit → Preferences → Add-ons before running e2e tests.",
            returncode=2,
        )


# ── Direct access to addon's Python functions ────────────────────

@pytest.fixture(scope="session")
def inu():
    """Return the addon's top-level Python module so tests can call
    underlying functions (import_dff, import_col, import_ifp, …)
    directly instead of going through bpy.ops.

    Why both paths? Operators wrap the function in
        try: import_dff(...)
        except Exception as e: self.report({'ERROR'}, f"…{str(e)}")
    which hides the traceback and turns any NameError into a single
    line. For debugging, calling the function directly gives a real
    stack. For full integration coverage, tests still use bpy.ops.

    The addon may register under either `INU_tools` (legacy add-on
    folder layout) or `bl_ext.*.inu_tools` (Blender 4.2+ extension);
    we discover whichever one is loaded.
    """
    import sys
    candidates = [
        name for name in sys.modules
        if name.split(".")[-1].lower() == "inu_tools"
        and not name.endswith(".__init__")
    ]
    if not candidates:
        pytest.fail("INU Tools module not found in sys.modules")

    # Prefer the shortest name (the package itself, not a submodule).
    pkg_name = min(candidates, key=len)
    return sys.modules[pkg_name]


@pytest.fixture(scope="session")
def inu_ops(inu):
    """Direct access to addon's `ops` submodules, for traceback-friendly
    test calls. Usage: `inu_ops.dff_import.import_dff(filepath=…)`."""
    import importlib
    return importlib.import_module(f"{inu.__name__}.ops")
