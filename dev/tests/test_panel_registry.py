from pathlib import Path
import sys


# Lives at dev/tests/ — go up two to reach repo root.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from ui.registry import TABS, ZONES, PANELS, apply_order  # noqa: E402


def test_tabs_are_nonempty_strings():
    """Every tab key must map to a human-readable bl_category."""
    assert TABS, "TABS must not be empty"
    for key, label in TABS.items():
        assert isinstance(key, str) and key, f"bad tab key: {key!r}"
        assert isinstance(label, str) and label, f"bad tab label for {key!r}: {label!r}"


def test_zones_are_nonneg_ints():
    """Zone bases must be non-negative integers — bl_order doesn't accept floats."""
    assert ZONES, "ZONES must not be empty"
    for key, base in ZONES.items():
        assert isinstance(base, int) and base >= 0, f"bad zone base for {key!r}: {base!r}"


def test_zones_are_well_spaced():
    """Zone bases should be spaced by at least 10 to leave room for slots
    inside each zone without colliding with the next zone's base."""
    bases = sorted(ZONES.values())
    for prev, nxt in zip(bases, bases[1:]):
        assert nxt - prev >= 10, (
            f"zones too close: {prev} → {nxt} (need ≥10 slots per zone)")


def test_every_panel_entry_references_known_tab_and_zone():
    """Catches typos like ('GTA_TOLS', ...) or ('MODL', ...) in PANELS."""
    for idname, entry in PANELS.items():
        assert isinstance(entry, tuple) and len(entry) == 3, (
            f"PANELS[{idname!r}] must be a 3-tuple, got {entry!r}")
        tab_key, zone_key, slot = entry
        assert tab_key in TABS, f"PANELS[{idname!r}] uses unknown tab {tab_key!r}"
        assert zone_key in ZONES, f"PANELS[{idname!r}] uses unknown zone {zone_key!r}"
        assert isinstance(slot, int) and slot >= 0, (
            f"PANELS[{idname!r}] slot must be a non-negative int, got {slot!r}")


def test_no_two_panels_collide_on_same_bl_order_in_same_tab():
    """Two panels in the same tab+zone+slot would resolve to identical
    bl_order — Blender would render them in unspecified order."""
    seen = {}
    for idname, (tab, zone, slot) in PANELS.items():
        key = (tab, ZONES[zone] + slot)
        if key in seen:
            other = seen[key]
            raise AssertionError(
                f"{idname!r} and {other!r} both resolve to "
                f"tab={tab!r} bl_order={key[1]} — pick a different slot")
        seen[key] = idname


def test_apply_order_writes_expected_attrs():
    """apply_order must set bl_category and bl_order for known panels,
    and leave unknown panels untouched."""
    class FakePanel:
        bl_idname = "GTATOOLS_PT_check_panel"   # in PANELS
        bl_category = "old"
        bl_order = 999

    apply_order(FakePanel)
    assert FakePanel.bl_category == "GTA Tools"
    # Phase 0: check_panel is at MODEL slot 0 → ZONES['MODEL'] + 0 = 10
    assert FakePanel.bl_order == 10

    class UnknownPanel:
        bl_idname = "GTATOOLS_PT_does_not_exist"
        bl_category = "unchanged"
        bl_order = 7

    apply_order(UnknownPanel)
    assert UnknownPanel.bl_category == "unchanged"
    assert UnknownPanel.bl_order == 7


def test_apply_order_handles_class_without_bl_idname():
    """Some root panels may rely on Blender's auto-generated bl_idname.
    The decorator must not crash on them — just skip."""
    class NoIdname:
        pass

    result = apply_order(NoIdname)
    assert result is NoIdname  # returned unchanged


def test_top_level_bl_order_invariant():
    """Each registered top-level panel must compute to its expected
    bl_order. Update this map intentionally when moving a panel."""
    # Phase 2 (2026-04-26): prelight/prelight_col/vertex_paint/lightmap/
    # itera became subpanels under GTATOOLS_PT_light_master — not in PANELS.
    # light_master takes their old slot (bl_order=12).
    # Phase 5 reverted (2026-04-26): zone_model + zone_data divider panels
    # deleted entirely; not in PANELS anymore.
    expected = {
        'GTATOOLS_PT_export_panel':          0,
        'GTATOOLS_PT_bitmaps_panel':         2,
        'GTATOOLS_PT_check_panel':          10,
        'GTATOOLS_PT_vehicle_panel':        11,
        'GTATOOLS_PT_light_master':         12,
        'GTATOOLS_PT_frame_hierarchy':      13,
        'GTATOOLS_PT_2dfx_panel':           22,
        'GTATOOLS_PT_anim_panel':           24,
        'GTATOOLS_PT_object_ide_ipl_panel': 29,
        'GTATOOLS_PT_ide_ipl_panel':        30,
        'GTATOOLS_PT_id_manager_panel':     31,
        'GTATOOLS_PT_paths_panel':          32,
        'GTATOOLS_PT_water_panel':          34,
        'GTATOOLS_PT_radar_panel':          36,
    }
    for idname, want in expected.items():
        assert idname in PANELS, f'{idname} dropped from PANELS'
        _, zone, slot = PANELS[idname]
        got = ZONES[zone] + slot
        assert got == want, (
            f'{idname}: bl_order={got}, expected {want}')


def test_phase2_light_subpanels_not_in_registry():
    """Phase 2: 5 light panels became subpanels of light_master. They
    must NOT be in PANELS — subpanels inherit category from parent and
    use raw bl_order literals for sibling ordering. Re-adding them here
    would force them back to top-level placement."""
    subpanels = {
        'GTATOOLS_PT_prelight_panel',
        'GTATOOLS_PT_prelight_col_panel',
        'GTATOOLS_PT_vertex_paint_panel',
        'GTATOOLS_PT_lightmap_panel',
        'GTATOOLS_PT_itera_panel',
    }
    leaked = subpanels & set(PANELS.keys())
    assert not leaked, f'subpanels leaked into registry: {leaked}'
