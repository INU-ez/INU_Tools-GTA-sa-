# INU_tools.ui.registry — single source of truth for N-sidebar panel placement.
#
# Each top-level Panel that lives in the N-sidebar (View3D > N) declares its
# tab + zone + slot here. The `apply_order` decorator reads this dict and
# writes `bl_category` and `bl_order` onto the class at import time.
#
# Adding a new panel = one entry in PANELS. Moving a panel between tabs =
# change one tuple. No more hunting for free `bl_order` numbers across files.
#
# Subpanels (those with bl_parent_id) inherit their category from the parent
# and don't need a registry entry. Properties-window panels (bl_space_type =
# 'PROPERTIES') aren't placed by category and also don't need entries.

# Tab keys → human-readable bl_category strings shown in N-sidebar tabs.
TABS = {
    'GTA_TOOLS': 'GTA Tools',
    'GTA_MAP':   'GTA Map',
    'GTA_LIGHT': 'GTA Light',
    'GTA_SETUP': 'GTA Setup',
}

# Zone keys → base bl_order. Slots inside a zone are added to the base.
# Bases are spaced (10, 28, 50, 70) so a zone has room to grow without
# colliding with the next one. Phase 0: EXPORT/MODEL/DATA bases chosen
# so existing bl_order literals (0, 10–24, 28–36) map 1:1 to zone+slot.
ZONES = {
    'EXPORT':  0,
    'MODEL':  10,
    'DATA':   28,
    'LIGHT':  50,
    'SETUP':  70,
}

# {bl_idname: (tab_key, zone_key, slot)}
#
# Phase 5 reverted 2026-04-26: user preferred a single tab over 4-tab
# split. All panels back in 'GTA Tools' organised by zones (EXPORT/
# MODEL/DATA/LIGHT). Material consolidation (Phase 1) and Light Master
# (Phase 2) stay — they reduce panel count without separating them
# across tabs.
#
# main_panel is the root of GTA Tools tab and NOT in this registry —
# roots have no bl_order.
PANELS = {
    'GTATOOLS_PT_export_panel':         ('GTA_TOOLS', 'EXPORT',   0),
    'GTATOOLS_PT_bitmaps_panel':        ('GTA_TOOLS', 'EXPORT',   2),
    'GTATOOLS_PT_check_panel':          ('GTA_TOOLS', 'MODEL',    0),
    'GTATOOLS_PT_vehicle_panel':        ('GTA_TOOLS', 'MODEL',    1),
    'GTATOOLS_PT_light_master':         ('GTA_TOOLS', 'MODEL',    2),
    'GTATOOLS_PT_frame_hierarchy':      ('GTA_TOOLS', 'MODEL',    3),
    'GTATOOLS_PT_2dfx_panel':           ('GTA_TOOLS', 'MODEL',   12),
    'GTATOOLS_PT_anim_panel':           ('GTA_TOOLS', 'MODEL',   14),
    'GTATOOLS_PT_object_ide_ipl_panel': ('GTA_TOOLS', 'DATA',     1),
    'GTATOOLS_PT_ide_ipl_panel':        ('GTA_TOOLS', 'DATA',     2),
    'GTATOOLS_PT_id_manager_panel':     ('GTA_TOOLS', 'DATA',     3),
    'GTATOOLS_PT_paths_panel':          ('GTA_TOOLS', 'DATA',     4),
    'GTATOOLS_PT_water_panel':          ('GTA_TOOLS', 'DATA',     6),
    'GTATOOLS_PT_radar_panel':          ('GTA_TOOLS', 'DATA',     8),
}


def apply_order(cls):
    """Decorator: set bl_category + bl_order on a Panel from PANELS registry,
    AND wrap its poll() with a profile-visibility gate.

    The visibility gate consults ``tools.profiles.is_panel_visible`` against
    the active scene's ``gtatools_profile`` enum. Panels that aren't in the
    chosen profile's whitelist short-circuit poll() to False — Blender then
    skips draw entirely, so hidden panels cost nothing to render.

    Usage:
        @apply_order
        class GTATOOLS_PT_check_panel(bpy.types.Panel):
            bl_idname = "GTATOOLS_PT_check_panel"
            ...

    Classes whose bl_idname is not in PANELS are returned unchanged — that
    covers subpanels (which inherit from parent), properties-window panels,
    and anything else not pinned to an N-sidebar tab.
    """
    entry = PANELS.get(getattr(cls, 'bl_idname', None))
    if entry is None:
        return cls
    tab_key, zone_key, slot = entry
    cls.bl_category = TABS[tab_key]
    cls.bl_order = ZONES[zone_key] + slot

    # Wrap poll() so the active profile's whitelist hides off-profile
    # panels. We import lazily inside the wrapper because this module
    # is imported at addon-init time, well before tools.profiles' bpy
    # state is available; plus poll() runs per-redraw anyway.
    original_poll = getattr(cls, 'poll', None)
    idname = cls.bl_idname

    def _profile_aware_poll(_cls, context):
        try:
            from ..tools.profiles import is_panel_visible
            profile = getattr(context.scene.inu_settings, 'gtatools_profile', 'ALL')
            if not is_panel_visible(idname, profile):
                return False
        except Exception:
            # Fail open — broken profile module shouldn't kill the UI
            pass
        if original_poll is not None:
            return original_poll(context)
        return True

    cls.poll = classmethod(_profile_aware_poll)
    return cls
