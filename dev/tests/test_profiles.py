"""Unit tests for tools/profiles.py — built-in lookups, name
validation, and JSON save/load round-trip. Stubs bpy so the module
imports without a real Blender runtime."""

from pathlib import Path
import sys
import os
import tempfile
import shutil
import types

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))


# Stub bpy + bpy.props / bpy.types so importing tools.profiles works
# without a live Blender. The Operator subclasses defined inside the
# module just need a base class; they aren't instantiated by the tests.
class _DummyClass:
    pass


def _ensure_bpy_stubs():
    """Idempotent — top up missing attributes even if a previously
    loaded test (e.g. test_map_export_split.py) already installed
    a partial bpy stub. Without this, alphabetical test order
    matters and `bpy.utils` ends up missing whenever another stub
    runs first."""
    bpy_mod = sys.modules.get('bpy')
    if bpy_mod is None:
        bpy_mod = types.ModuleType('bpy')
        sys.modules['bpy'] = bpy_mod

    if not hasattr(bpy_mod, 'types'):
        bpy_mod.types = types.SimpleNamespace(
            Operator=_DummyClass, PropertyGroup=_DummyClass)
        sys.modules['bpy.types'] = bpy_mod.types
    if not hasattr(bpy_mod, 'props'):
        bpy_mod.props = types.SimpleNamespace(
            StringProperty=lambda **kw: None,
            EnumProperty=lambda **kw: None,
            BoolProperty=lambda **kw: None,
        )
        sys.modules['bpy.props'] = bpy_mod.props
    # bpy.utils — needed by tools/user_data.py when resolving the
    # user-profile directory. Tests that monkeypatch _profiles_dir
    # bypass this; tests that exercise the real lookup (e.g. unknown-
    # profile fallback) need it. A real Blender always has bpy.utils,
    # so the stub only matters for pure-Python CI.
    if not hasattr(bpy_mod, 'utils'):
        bpy_mod.utils = types.SimpleNamespace(
            extension_path_user=lambda *args, **kw: tempfile.mkdtemp(prefix="inu_stub_"),
            user_resource=lambda *args, **kw: tempfile.mkdtemp(prefix="inu_stub_"),
        )
        sys.modules['bpy.utils'] = bpy_mod.utils


_ensure_bpy_stubs()
from tools import profiles as p  # noqa: E402


# ── ALL behaviour ────────────────────────────────────────────────

def test_all_profile_shows_everything():
    assert p.is_panel_visible('GTATOOLS_PT_export_panel', 'ALL')
    assert p.is_panel_visible('GTATOOLS_PT_anything_made_up', 'ALL')


def test_empty_profile_id_falls_back_to_show_all():
    assert p.is_panel_visible('GTATOOLS_PT_water_panel', '')
    assert p.is_panel_visible('GTATOOLS_PT_water_panel', None)


def test_unknown_profile_id_fails_open():
    """Bogus profile id should not lock the user out — show everything."""
    assert p.is_panel_visible('GTATOOLS_PT_export_panel', 'NONEXISTENT_PROFILE')


def test_resolve_all_returns_empty_panels():
    """ALL profile resolves but its panel list is empty == «no filter»."""
    prof = p.resolve_profile('ALL')
    assert prof is not None
    # ALL still uses the legacy `panels` key (it predates the
    # order/hidden split — empty panels means «no filter»).
    assert prof.get('panels') == []


# ── Name validation ─────────────────────────────────────────────

def test_valid_names_accepted():
    assert p._is_valid_name("My Profile")
    assert p._is_valid_name("vehicle_modder_42")
    assert p._is_valid_name("Профиль RU")
    assert p._is_valid_name("a-b-c")


def test_invalid_names_rejected():
    assert not p._is_valid_name("")
    assert not p._is_valid_name("   ")
    assert not p._is_valid_name("../../../etc/passwd")
    assert not p._is_valid_name("name/with/slash")
    assert not p._is_valid_name("a" * 100)
    assert not p._is_valid_name("name<script>")


# ── JSON storage round-trip ─────────────────────────────────────

@pytest.fixture
def tmp_profiles_dir(monkeypatch):
    """Redirect _profiles_dir() to a temp directory for isolation."""
    tmpdir = tempfile.mkdtemp(prefix="inu_profile_test_")
    monkeypatch.setattr(p, "_profiles_dir", lambda: tmpdir)
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_save_then_load_round_trip(tmp_profiles_dir):
    order = [idname for idname, _ in p.ALL_TOGGLEABLE_PANELS]
    hidden = ['GTATOOLS_PT_water_panel']
    assert p.save_user_profile("My Vehicle", order, "test desc",
                               hidden=hidden)

    loaded = p.load_user_profile("My Vehicle")
    assert loaded is not None
    assert loaded['name'] == "My Vehicle"
    assert loaded['desc'] == "test desc"
    assert loaded['order'] == order
    assert loaded['hidden'] == hidden


def test_save_dedupes_but_preserves_order(tmp_profiles_dir):
    """save_user_profile should drop dupes but keep first-occurrence
    order — order matters because it drives bl_order on activation."""
    raw = ['GTATOOLS_PT_water_panel', 'GTATOOLS_PT_export_panel',
           'GTATOOLS_PT_water_panel', 'GTATOOLS_PT_vehicle_panel']
    p.save_user_profile("X", raw)
    loaded = p.load_user_profile("X")
    # Dedupe preserves first-occurrence order; load_user_profile then
    # appends the remaining ALL_TOGGLEABLE_PANELS at the end.
    assert loaded['order'][:3] == [
        'GTATOOLS_PT_water_panel',
        'GTATOOLS_PT_export_panel',
        'GTATOOLS_PT_vehicle_panel',
    ]


def test_save_overwrites_existing(tmp_profiles_dir):
    p.save_user_profile("Y", ['GTATOOLS_PT_export_panel'])
    p.save_user_profile("Y", ['GTATOOLS_PT_water_panel',
                              'GTATOOLS_PT_vehicle_panel'])  # overwrite
    loaded = p.load_user_profile("Y")
    assert loaded['order'][:2] == [
        'GTATOOLS_PT_water_panel',
        'GTATOOLS_PT_vehicle_panel',
    ]


def test_list_user_profiles_includes_saved(tmp_profiles_dir):
    p.save_user_profile("Alpha", ['A'])
    p.save_user_profile("Beta",  ['B'])
    names = p.list_user_profiles()
    assert "Alpha" in names
    assert "Beta" in names


def test_delete_user_profile(tmp_profiles_dir):
    p.save_user_profile("Trash", ['A'])
    assert "Trash" in p.list_user_profiles()
    assert p.delete_user_profile("Trash")
    assert "Trash" not in p.list_user_profiles()


def test_delete_nonexistent_returns_false(tmp_profiles_dir):
    assert not p.delete_user_profile("does_not_exist")


def test_invalid_name_save_rejected(tmp_profiles_dir):
    assert not p.save_user_profile("../escape", ['A'])
    assert not p.save_user_profile("", ['A'])


def test_load_nonexistent_returns_none(tmp_profiles_dir):
    assert p.load_user_profile("ghost") is None


def test_load_corrupted_json_returns_none(tmp_profiles_dir):
    """A profile file with garbage content should fall back to None
    rather than crashing on JSON decode."""
    bad_path = os.path.join(tmp_profiles_dir, "broken.json")
    with open(bad_path, 'w', encoding='utf-8') as f:
        f.write("{this is not json")
    assert p.load_user_profile("broken") is None


def test_load_missing_order_field_returns_none(tmp_profiles_dir):
    """JSON without 'order' or legacy 'panels' isn't a valid profile."""
    import json
    bad_path = os.path.join(tmp_profiles_dir, "incomplete.json")
    with open(bad_path, 'w', encoding='utf-8') as f:
        json.dump({"name": "incomplete"}, f)
    assert p.load_user_profile("incomplete") is None


def test_legacy_panels_field_is_migrated_to_order(tmp_profiles_dir):
    """Old JSON with 'panels' (visible-only list) loads as 'order'
    with hidden empty — legacy compat for upgrades from the previous
    profile schema."""
    import json
    legacy_path = os.path.join(tmp_profiles_dir, "Legacy.json")
    with open(legacy_path, 'w', encoding='utf-8') as f:
        json.dump({
            "name": "Legacy",
            "panels": ['GTATOOLS_PT_export_panel',
                       'GTATOOLS_PT_vehicle_panel'],
        }, f)
    loaded = p.load_user_profile("Legacy")
    assert loaded is not None
    # Order starts with the legacy list, then the rest of ALL_TOGGLEABLE
    assert loaded['order'][:2] == [
        'GTATOOLS_PT_export_panel',
        'GTATOOLS_PT_vehicle_panel',
    ]
    assert loaded['hidden'] == []


# ── resolve_profile combines built-ins + user ───────────────────

def test_resolve_user_profile(tmp_profiles_dir):
    p.save_user_profile("Custom1", ['GTATOOLS_PT_export_panel'])
    prof = p.resolve_profile("Custom1")
    assert prof is not None
    # Saved order leads, the rest of ALL_TOGGLEABLE_PANELS appended.
    assert prof['order'][0] == 'GTATOOLS_PT_export_panel'


def test_resolve_unknown_returns_none(tmp_profiles_dir):
    assert p.resolve_profile("NoSuchProfile") is None


# ── Visibility integration with user profiles ──────────────────

def test_hidden_set_filters_visibility(tmp_profiles_dir):
    """is_panel_visible: True unless idname is in `hidden` set."""
    order = [idname for idname, _ in p.ALL_TOGGLEABLE_PANELS]
    p.save_user_profile("MixedVis", order, hidden=['GTATOOLS_PT_water_panel'])
    assert p.is_panel_visible('GTATOOLS_PT_export_panel', "MixedVis")
    assert not p.is_panel_visible('GTATOOLS_PT_water_panel', "MixedVis")
    # Panel not in `hidden` → still visible
    assert p.is_panel_visible('GTATOOLS_PT_vehicle_panel', "MixedVis")


# ── Order preservation ─────────────────────────────────────────

def test_arbitrary_order_preserved_in_json(tmp_profiles_dir):
    """The new contract: order list drives bl_order on activation,
    so save→load must preserve it. The user-supplied prefix is kept
    intact; the loader appends any missing ALL_TOGGLEABLE_PANELS at
    the end."""
    weird_order = [
        'GTATOOLS_PT_radar_panel',
        'GTATOOLS_PT_export_panel',
        'GTATOOLS_PT_anim_panel',
        'GTATOOLS_PT_water_panel',
    ]
    assert p.save_user_profile("Reordered", weird_order)
    loaded = p.load_user_profile("Reordered")
    assert loaded['order'][:len(weird_order)] == weird_order


def test_panel_label_known_id_returns_label():
    assert p.panel_label('GTATOOLS_PT_export_panel') == "Экспорт / Импорт"


def test_panel_label_unknown_falls_back_to_id():
    assert p.panel_label('GTATOOLS_PT_unknown_xyz') == 'GTATOOLS_PT_unknown_xyz'
