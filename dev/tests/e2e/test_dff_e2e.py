"""End-to-end DFF tests — drive the actual operator
``bpy.ops.gtatools.import_dff`` and inspect what landed in the scene.

These tests catch regressions that pure-Python `core/dff.py` round-trip
tests can't see: operator wiring, scene-graph construction, material/
node-tree population, collection layout, and the full export → re-
import path through Blender's data API.
"""

from __future__ import annotations

import os
from pathlib import Path

import bpy
import pytest


# ── Helpers ──────────────────────────────────────────────────────

def _mesh_objects():
    return [o for o in bpy.data.objects if o.type == 'MESH']


def _all_materials():
    return list(bpy.data.materials)


# ── Plain import ─────────────────────────────────────────────────

def test_import_dff_creates_mesh(asset, inu_ops):
    """Smoke-test: importing a vanilla DFF puts at least one mesh in
    the scene. If this breaks, the import operator is wired wrong —
    nothing else downstream can pass.

    Calls the underlying `import_dff` function (not bpy.ops.gtatools)
    so a NameError surfaces with a real stack instead of the bare
    string the operator's `try/except → self.report()` produces."""
    inu_ops.dff_import.import_dff(filepath=asset("1.dff"), context=bpy.context)
    assert len(_mesh_objects()) >= 1, "no mesh objects after DFF import"


def test_import_dff_creates_materials(asset):
    bpy.ops.gtatools.import_dff('EXEC_DEFAULT', filepath=asset("1.dff"))
    mats = _all_materials()
    assert mats, "DFF import should create at least one material"
    # Every imported material must carry a node tree — otherwise the
    # Eevee/Cycles preview will be black and the user can't see textures
    # they imported.
    for m in mats:
        assert m.use_nodes, f"material {m.name!r} has no node tree"


def test_import_dff_object_has_geometry(asset):
    bpy.ops.gtatools.import_dff('EXEC_DEFAULT', filepath=asset("1.dff"))
    meshes = _mesh_objects()
    assert meshes
    # Pick any mesh — they all should have non-empty vertex data.
    obj = meshes[0]
    assert len(obj.data.vertices) > 0
    assert len(obj.data.polygons) > 0


# ── Round-trip via Blender (operator → operator) ────────────────

def test_dff_blender_round_trip_preserves_mesh_count(asset, tmp_path):
    """Import a DFF, immediately export it, re-import the export, and
    check vertex/triangle counts survived. Catches regressions in the
    Blender-side mesh assembly that the pure-Python writer test can't
    see (e.g. someone breaks normal recalc and we lose verts on merge)."""
    src = asset("1.dff")
    bpy.ops.gtatools.import_dff('EXEC_DEFAULT', filepath=src)

    first = _mesh_objects()[0]
    v0, p0 = len(first.data.vertices), len(first.data.polygons)

    # Select the imported root for export. The export op uses
    # selection / active to find the clump root.
    bpy.ops.object.select_all(action='DESELECT')
    first.select_set(True)
    bpy.context.view_layer.objects.active = first

    out = tmp_path / "roundtrip.dff"
    res = bpy.ops.gtatools.export_dff('EXEC_DEFAULT', filepath=str(out))
    assert res == {'FINISHED'}, f"export returned {res}"
    assert out.is_file() and out.stat().st_size > 0, "export produced no file"

    # Wipe and re-import. We can't use read_factory_settings() — see
    # conftest._wipe_data_blocks for the addon-registration corruption
    # it would cause on this machine.
    from conftest import _wipe_data_blocks
    _wipe_data_blocks()
    bpy.ops.gtatools.import_dff('EXEC_DEFAULT', filepath=str(out))

    second = _mesh_objects()[0]
    v1, p1 = len(second.data.vertices), len(second.data.polygons)

    # Vertex/poly count is allowed to drop slightly (split verts at UV
    # seams collapse on import); strict equality is too brittle.
    # What we DON'T tolerate is a >5 % loss — that's a real bug.
    assert abs(v0 - v1) / max(v0, 1) < 0.05, f"vertex loss: {v0} → {v1}"
    assert abs(p0 - p1) / max(p0, 1) < 0.05, f"polygon loss: {p0} → {p1}"
