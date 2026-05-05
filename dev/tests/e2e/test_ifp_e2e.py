"""End-to-end IFP tests — import ped.ifp and exercise the writer via
the addon's `core.ifp.roundtrip_test()` helper.

ped.ifp is the canonical 294-animation pedestrian package and acts
as a stress test for both parser and writer."""

from __future__ import annotations

import importlib

import bpy


# ── Import ───────────────────────────────────────────────────────

def test_import_ifp_creates_actions(asset):
    n_before = len(bpy.data.actions)

    result = bpy.ops.gtatools.import_ifp(filepath=asset("ped.ifp"))
    assert result == {'FINISHED'}, f"operator returned {result}"

    new_actions = len(bpy.data.actions) - n_before
    assert new_actions > 0, "IFP import created no actions"
    # ped.ifp ships with ~294 anims. If we see fewer than half, the
    # parser likely choked on a chunk header. Loose lower bound so this
    # test still passes on a reduced custom ped.ifp the user might drop in.
    assert new_actions >= 50, f"only {new_actions} actions — IFP parser may have aborted early"


def test_import_ifp_actions_have_source_metadata(asset):
    """Every action created by the IFP importer carries `ifp_source`,
    `ifp_package`, and `ifp_anim_index` custom props — these drive the
    later apply_ifp_action() lookup. If any are missing, Apply will
    silently fail."""
    bpy.ops.gtatools.import_ifp(filepath=asset("ped.ifp"))

    ifp_actions = [a for a in bpy.data.actions if a.get("ifp_source")]
    assert ifp_actions, "no actions tagged with ifp_source"

    for a in ifp_actions[:5]:  # spot-check first five
        assert a.get("ifp_source"), f"{a.name} missing ifp_source"
        assert a.get("ifp_package"), f"{a.name} missing ifp_package"
        assert a.get("ifp_anim_index") is not None, f"{a.name} missing ifp_anim_index"


# ── Export round-trip via core.ifp.roundtrip_test ────────────────
#
# These tests use the addon's own `roundtrip_test(filepath)` helper:
# it reads the .ifp, writes it to a temp file in the SAME format,
# reads that back, and reports counts + numerical deltas.
#
# Why this matters: project memory has TWO past IFP export regressions
# (rest_quat inverse missing, non-unit quaternions causing in-game
# stepping). Both would surface here as max_rot_delta spikes long
# before they ship to users.

def test_ifp_export_round_trip_ped(asset, inu):
    core_ifp = importlib.import_module(f"{inu.__name__}.core.ifp")
    r = core_ifp.roundtrip_test(asset("ped.ifp"))

    assert r['error'] is None, f"roundtrip_test failed: {r['error']}"

    # Counts must match exactly — losing animations or bones means
    # the writer is dropping data.
    assert r['anims_in'] == r['anims_out'], \
        f"anim count drift: {r['anims_in']} → {r['anims_out']}"
    assert r['bones_in'] == r['bones_out'], \
        f"bone count drift: {r['bones_in']} → {r['bones_out']}"
    assert r['keyframes_in'] == r['keyframes_out'], \
        f"keyframe count drift: {r['keyframes_in']} → {r['keyframes_out']}"

    # Numerical deltas. ANP3 is int16-quantised, so rotation precision
    # is ~1/4096 = 2.4e-4. Allow 1e-3 to absorb format conversion if
    # roundtrip_test toggles formats internally.
    assert r['max_rot_delta'] < 1e-3, \
        f"rotation drift too large: {r['max_rot_delta']}"
    assert r['max_trans_delta'] < 1e-3, \
        f"translation drift too large: {r['max_trans_delta']}"
    assert r['max_time_delta'] < 1e-3, \
        f"time drift too large: {r['max_time_delta']}"


def test_ifp_export_no_missing_anims_or_bones(asset, inu):
    """Stricter than the count check: if `roundtrip_test` lists any
    animations or bones as 'missing', the writer is silently dropping
    them even when the count happens to match (duplicate names could
    mask actual loss)."""
    core_ifp = importlib.import_module(f"{inu.__name__}.core.ifp")
    r = core_ifp.roundtrip_test(asset("ped.ifp"))

    assert not r['missing_anims'], \
        f"animations lost in round-trip: {r['missing_anims'][:5]}"
    assert not r['missing_bones'], \
        f"{len(r['missing_bones'])} animation(s) had bones go missing"
    assert not r['kf_mismatches'], \
        f"{len(r['kf_mismatches'])} animation(s) lost keyframes"
