"""End-to-end COL tests — exercise the import_col / export_col
pipeline on a real game .col and check that the collision shapes
landed as Blender objects.

Unlike DFF, the COL import operator (`gtatools.import_col`) runs as
a *modal* operator with a progress-bar timer. In `--background` mode
the modal loop never gets a chance to step, so the operator stays
in {'RUNNING_MODAL'} forever and the import never completes. We
side-step that by calling the synchronous `import_col(filepath)`
helper directly — same code, just without the timer wrapping."""

from __future__ import annotations

import bpy


def _col_objects():
    """COL geometry comes in as MESH objects (spheres/boxes are also
    realised as meshes by the importer). Some implementations also
    create EMPTY parents — accept both."""
    return [o for o in bpy.data.objects if o.type in {'MESH', 'EMPTY'}]


def test_import_col_creates_objects(asset, inu_ops):
    inu_ops.col_import.import_col(filepath=asset("1.col"), context=bpy.context)
    assert len(_col_objects()) >= 1, "no objects after COL import"


def test_import_col_round_trip_object_count(asset, inu_ops, tmp_path):
    """Import → export → re-import. Object count should match exactly
    — COL has no UV/normal merging on the way back, so every shape
    that went out must come back."""
    inu_ops.col_import.import_col(filepath=asset("1.col"), context=bpy.context)
    n_before = len(_col_objects())
    assert n_before > 0

    # Select everything for export — gtatools.export_col is non-modal,
    # so we can drive it through bpy.ops normally.
    bpy.ops.object.select_all(action='SELECT')
    out = tmp_path / "roundtrip.col"
    res = bpy.ops.gtatools.export_col('EXEC_DEFAULT', filepath=str(out))
    assert res == {'FINISHED'}, f"export returned {res}"
    assert out.is_file() and out.stat().st_size > 0

    from conftest import _wipe_data_blocks
    _wipe_data_blocks()
    inu_ops.col_import.import_col(filepath=str(out), context=bpy.context)
    n_after = len(_col_objects())

    assert n_after == n_before, f"COL object count drift: {n_before} → {n_after}"
