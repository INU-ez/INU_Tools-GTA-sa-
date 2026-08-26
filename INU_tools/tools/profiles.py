# INU_tools.tools.profiles
# User-defined panel profiles — saved sets of N-sidebar panels in a
# user-chosen ORDER. Different modder roles need different subsets and
# orderings of the addon: a vehicle author rarely touches Path/Water/
# Radar; a map mapper rarely touches IFP/IK Rig. Without profiles the
# user sees 13 panels every session in the addon's default order —
# profiles let them pick which appear and stack them however they like.
#
# Storage:
#   - 'ALL' — the only built-in: empty list = «show every panel in the
#     addon's natural zone order». Always available, can't be edited
#     or deleted.
#   - User profiles — JSON files under the user data directory's
#     ``profiles/<name>.json`` (see ``tools/user_data.py``).
#     `panels` is an ordered list; the position drives bl_order so the
#     user controls both visibility and order.

import json
import os
import re

import bpy

# `from .. import T` works in production (module loaded as
# `INU_tools.tools.profiles`) but breaks under unit tests that put
# `INU_tools/` on `sys.path` and load `tools` as a top-level package
# (`..` then goes above top-level). Fall back to identity-function so
# error-message strings pass through untranslated — fine for tests.
try:
    from .. import T
except ImportError:
    def T(s):
        return s

from .compat import safe_icon, inu_icon
from .user_data import get_user_data_dir
from typing import Dict, List, Optional


# 'ALL' is the only built-in. Empty `panels` list is special-cased by
# is_panel_visible() and apply_profile_order() to mean «no filter, use
# the addon's default zone-based order».
_ALL_PROFILE = {
    'label':  "Все",
    'desc':   "Показать все панели аддона в порядке по умолчанию",
    'panels': [],
}


# ── On-disk storage helpers ──────────────────────────────────────

def _profiles_dir() -> str:
    """User-isolated ``profiles/`` directory inside the addon's user
    data folder. Created lazily."""
    return get_user_data_dir('profiles')


_NAME_RE = re.compile(r"^[A-Za-zА-Яа-я0-9_\- ]+$")


def _is_valid_name(name: str) -> bool:
    """Letter/digit/underscore/dash/space only — keeps filenames safe
    on every platform without us doing OS-specific escaping."""
    name = name.strip()
    return bool(name) and bool(_NAME_RE.match(name)) and len(name) <= 64


# ── Draw-path caches ─────────────────────────────────────────────
# Profile lookups run on EVERY UI redraw from two places:
#   * ui.registry._profile_aware_poll — once per top-level panel, even
#     for collapsed ones (poll() always runs);
#   * profile_enum_items — the profile dropdown lives in the always-drawn
#     root panel, and Blender re-runs a dynamic enum's items callback
#     every time the widget is drawn.
# Uncached, that meant a listdir + an open()+json.load() PER PANEL PER
# FRAME, which stalled viewport navigation whenever the N-sidebar was
# open. Cache key = absolute path + on-disk stamp (mtime_ns, size):
#   * the path, because the data root is relocatable (preset-root
#     override) and a name-keyed entry would answer for the old root;
#   * the stamp, so a profile edited by hand outside Blender is picked up.
# Cost per lookup drops to one stat().
_dir_listing_cache = None      # None | (dir, stamp, [names])
_profile_file_cache = {}       # path → (stamp, profile dict | None)


def _stamp(path: str):
    """(mtime_ns, size) of *path*, or None when it doesn't exist.

    mtime_ns rather than getmtime() — float seconds can't tell apart two
    writes inside the same tick, which is exactly what a Save-profile
    click followed by a redraw looks like.
    """
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


def _copy_profile(profile):
    """Shallow copy with fresh lists.

    load_user_profile() used to hand out a freshly built dict every call,
    and the profile-editor operators edit `order` / `hidden` in place.
    Now that the parse result is cached, hand out a copy so that in-place
    editing can't poison the cache — the copy is a couple of 16-item
    lists, i.e. free next to the json.load() it replaces.
    """
    if profile is None:
        return None
    out = dict(profile)
    out['order'] = list(profile.get('order') or [])
    out['hidden'] = list(profile.get('hidden') or [])
    return out


def invalidate_profile_cache() -> None:
    """Drop the profile caches. Called after every write/delete so the UI
    never shows a stale list even if the filesystem stamp is coarse."""
    global _dir_listing_cache
    _dir_listing_cache = None
    _profile_file_cache.clear()


def list_user_profiles() -> List[str]:
    """Return the names of profiles saved as JSON files (no extension)."""
    global _dir_listing_cache
    d = _profiles_dir()
    stamp = _stamp(d)
    if (_dir_listing_cache is not None
            and _dir_listing_cache[0] == d
            and _dir_listing_cache[1] == stamp):
        return list(_dir_listing_cache[2])
    out = []
    try:
        for f in os.listdir(d):
            if f.lower().endswith('.json'):
                out.append(os.path.splitext(f)[0])
    except OSError:
        pass
    out.sort()
    _dir_listing_cache = (d, stamp, out)
    return list(out)


def load_user_profile(name: str) -> Optional[dict]:
    """Return the JSON-decoded profile or None on any error.

    Output is normalised to the new schema:
        {
          'name': str,
          'desc': str,
          'order':  List[str]  # ALL known panels in user-chosen order
          'hidden': List[str]  # subset of order that's currently hidden
        }
    Old single-list ``panels`` files (visible-only) are migrated on
    read: their list becomes ``order``, missing panels are appended
    at the end, and ``hidden`` is empty.
    """
    if not _is_valid_name(name):
        return None
    path = os.path.join(_profiles_dir(), f"{name}.json")
    stamp = _stamp(path)
    if stamp is None:
        _profile_file_cache.pop(path, None)
        return None
    hit = _profile_file_cache.get(path)
    if hit is not None and hit[0] == stamp:
        return _copy_profile(hit[1])
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        _profile_file_cache[path] = (stamp, None)
        return None

    raw_order = data.get('order')
    if not isinstance(raw_order, list):
        # Legacy: old files had only 'panels' (visible list). Treat
        # those panels as the user's chosen order, leave the rest at
        # the canonical addon order.
        raw_order = data.get('panels')
        if not isinstance(raw_order, list):
            _profile_file_cache[path] = (stamp, None)
            return None

    raw_hidden = data.get('hidden') or []
    if not isinstance(raw_hidden, list):
        raw_hidden = []

    # Ensure every known panel appears exactly once in `order`. Newly
    # added panels (introduced after the profile was saved) tack onto
    # the end so they're not silently dropped from the layout.
    seen = set()
    order = []
    for pid in raw_order:
        if pid not in seen:
            seen.add(pid)
            order.append(pid)
    for idname, _ in ALL_TOGGLEABLE_PANELS:
        if idname not in seen:
            order.append(idname)
            seen.add(idname)

    profile = {
        'name':   data.get('name', name),
        'desc':   data.get('desc', ''),
        'order':  order,
        'hidden': list(raw_hidden),
    }
    _profile_file_cache[path] = (stamp, profile)
    return _copy_profile(profile)


def save_user_profile(name: str, order: List[str],
                      description: str = "",
                      hidden: Optional[List[str]] = None) -> bool:
    """Write a user profile to disk. Returns True on success.

    ``order`` — full ordered list of panel ids (drives bl_order).
    ``hidden`` — subset that should be invisible (drives poll filter).
    Empty hidden = everything in order is visible.
    """
    if not _is_valid_name(name):
        return False
    d = _profiles_dir()
    # _profiles_dir() memoises its mkdir, so re-create here in case the
    # folder was removed after the first lookup of the session.
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        return False
    path = os.path.join(d, f"{name}.json")

    # Dedupe preserving first-occurrence order.
    deduped = list(dict.fromkeys(order))
    hidden_set = set(hidden or [])
    # Don't carry hidden ids that aren't in order — defensive cleanup.
    hidden_clean = [pid for pid in deduped if pid in hidden_set]

    payload = {
        'name':   name.strip(),
        'desc':   description,
        'order':  deduped,
        'hidden': hidden_clean,
    }
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except OSError:
        return False
    invalidate_profile_cache()
    return True


def delete_user_profile(name: str) -> bool:
    if not _is_valid_name(name):
        return False
    path = os.path.join(_profiles_dir(), f"{name}.json")
    try:
        os.remove(path)
    except OSError:
        return False
    invalidate_profile_cache()
    return True


# ── Public lookup API ──────────────────────────────────────────────

def resolve_profile(profile_id: str) -> Optional[dict]:
    """Return profile dict for either the built-in ALL or a user
    profile name. Returns None when nothing matches — caller falls
    back to ALL behavior (no filter)."""
    if not profile_id:
        return None
    if profile_id == 'ALL':
        return _ALL_PROFILE
    return load_user_profile(profile_id)


def is_panel_visible(panel_idname: str, profile_id: str) -> bool:
    """Return True iff the given panel should be visible under the
    given profile. Behaviour:
      - profile == 'ALL' or unresolved → always visible (no filter)
      - panel id is in profile.hidden → False
      - otherwise → True (visible by default)
    """
    if not profile_id or profile_id == 'ALL':
        return True
    profile = resolve_profile(profile_id)
    if profile is None:
        return True  # unknown profile, fail open
    hidden = profile.get('hidden') or []
    if panel_idname in hidden:
        return False
    # Backward-compat fallback for ALL profile schema:
    # raw _ALL_PROFILE has no `order`, just empty panels list — that
    # was the «show all» sentinel under the old code path.
    visible_set = profile.get('panels') or []
    if not visible_set:
        return True
    return panel_idname in visible_set


# Module-level cache for the items tuples returned by the EnumProperty
# callback below. Blender's dynamic EnumProperty has a well-known gotcha:
# if Python doesn't keep a strong reference to the strings inside each
# item tuple, GC reclaims them and Blender starts logging
#     pyrna_enum_to_py: current value 'N' matches no enum
# at every draw of the dropdown. Caching the list at module scope keeps
# the strings pinned alive across draws, restarts, and items recomputes.
_profile_items_cache: list = []


def profile_enum_items(self, context):
    """EnumProperty items callback — ALL first, then user profiles
    sorted alphabetically. Stable ordering so the dropdown doesn't
    shuffle when the user adds/removes profiles.

    HOT PATH: this dropdown sits in the always-drawn root panel, so
    Blender re-runs the callback on every redraw of the N-sidebar. The
    listing/parse behind it is stat-cached (see _dir_listing_cache), and
    the assembled list is only swapped in when it actually changed —
    keeping the very same string objects pinned across draws, which is
    what the GC note above is about."""
    global _profile_items_cache
    items = [('ALL', _ALL_PROFILE['label'], _ALL_PROFILE['desc'])]
    for name in list_user_profiles():
        prof = load_user_profile(name) or {}
        items.append((name, name, prof.get('desc', '') or
                      "Пользовательский профиль"))
    if items != _profile_items_cache:
        _profile_items_cache = items
    return _profile_items_cache


# ── Discoverable list of toggleable panels ──────────────────────
# Centralised so the Save / Manage operator can render checkboxes for
# every top-level panel without re-discovering them through bpy.types.
# Order roughly matches the N-sidebar zone layout for readability.

# idname → fallback label. The labels here are ONLY a fallback for
# environments where the panel class isn't registered (unit tests);
# at runtime ``panel_label()`` reads each panel's LIVE ``bl_label`` so
# the profile editor always shows the exact same tab name as the
# N-sidebar. Keep both the id list COMPLETE (every top-level panel) and
# these fallbacks equal to the real bl_labels. Order ≈ N-sidebar order.
ALL_TOGGLEABLE_PANELS = [
    ('GTATOOLS_PT_export_panel',         "Экспорт / Импорт"),
    ('GTATOOLS_PT_bitmaps_panel',        "Менеджер текстур"),
    ('GTATOOLS_PT_check_panel',          "Проверка"),
    ('GTATOOLS_PT_vehicle_panel',        "Машины"),
    ('GTATOOLS_PT_light_master',         "Lighting"),
    # «Иерархия фреймов» больше не топ-вкладка — это подпанель «Машины».
    ('GTATOOLS_PT_2dfx_panel',           "Эффекты"),
    ('GTATOOLS_PT_anim_panel',           "Анимации"),
    ('GTATOOLS_PT_bake_panel',           "Texture Bake"),
    ('GTATOOLS_PT_object_ide_ipl_panel', "Object IDE / IPL"),
    ('GTATOOLS_PT_ide_ipl_panel',        "IDE / IPL / IMG"),
    ('GTATOOLS_PT_id_manager_panel',     "ID Manager"),
    ('GTATOOLS_PT_paths_panel',          "Пути"),
    ('GTATOOLS_PT_zon_panel',            "map.zon"),
    ('GTATOOLS_PT_water_panel',          "Water"),
    ('GTATOOLS_PT_grass_panel',          "Трава"),
    ('GTATOOLS_PT_radar_panel',          "X Radar Maker"),
    ('GTATOOLS_PT_footer_panel',         "Поддержка"),
]


def panel_label(idname: str) -> str:
    """Human label for a panel id — its LIVE ``bl_label`` so the profile
    editor matches the N-sidebar tab exactly (same source string → same
    Blender i18n). Falls back to the static table (unregistered classes,
    e.g. unit tests), then the id itself."""
    cls = getattr(bpy.types, idname, None)
    if cls is not None:
        lbl = getattr(cls, 'bl_label', None)
        if lbl:
            return lbl
    for k, v in ALL_TOGGLEABLE_PANELS:
        if k == idname:
            return v
    return idname


# ── bl_order reassignment ───────────────────────────────────────

# Capture each panel's default bl_order at first call so that switching
# back to ALL restores the addon's natural zone-based order. We can't
# read it from PANELS dict directly because slot+zone math happens at
# decorator time and we want the actual final values that ended up on
# the classes.
_default_bl_orders: Dict[str, int] = {}


def _classes_by_idname() -> dict:
    """Return {bl_idname: PanelClass} for the panels we know about,
    fetched via ``bpy.types.<idname>`` so we always get the *live*
    registered class.

    Earlier we used ``Panel.__subclasses__()`` but that also returns
    stale class objects from previous register cycles — calling
    ``unregister_class`` on those raised
    ``missing bl_rna attribute from '_RNAMeta' instance``. Looking up
    via ``bpy.types`` is the canonical way to get the currently-
    registered class for a given idname."""
    out = {}
    for idname, _ in ALL_TOGGLEABLE_PANELS:
        cls = getattr(bpy.types, idname, None)
        if cls is not None:
            out[idname] = cls
    return out


def apply_profile_order(profile_id: str) -> None:
    """Re-assign bl_order on every toggleable panel based on the
    profile's panels list, then unregister + re-register each touched
    class so Blender re-sorts the sidebar.

    Why unregister/register: changing ``cls.bl_order`` at runtime IS
    picked up by Blender on next redraw, but Blender 5.x caches the
    sorted panel list per Space and only invalidates it on register
    events. The cheapest reliable way to force a re-sort is to
    re-register every affected class — that's what this does."""
    classes = _classes_by_idname()

    # First-call snapshot: remember where each panel started so ALL
    # can roll back when user switches away from a custom profile.
    if not _default_bl_orders:
        for idname, _ in ALL_TOGGLEABLE_PANELS:
            cls = classes.get(idname)
            if cls is not None:
                _default_bl_orders[idname] = getattr(cls, 'bl_order', 100)

    # Build {idname: new_bl_order} for everything we want to touch.
    # ALL or empty profile = restore defaults; otherwise the `order`
    # list drives bl_order (position == order index).
    new_orders: Dict[str, int] = {}
    profile = resolve_profile(profile_id)
    order_list = (profile or {}).get('order') or []
    # Old profiles before the schema change still expose `panels`.
    # load_user_profile already migrates, but the built-in ALL_PROFILE
    # uses `panels`=[] — that's the «no filter, default order» case.
    if not order_list:
        order_list = (profile or {}).get('panels') or []

    if not profile_id or profile_id == 'ALL' or not order_list:
        new_orders = dict(_default_bl_orders)
    else:
        for pos, idname in enumerate(order_list):
            new_orders[idname] = pos

    # Apply bl_order then re-register the parent + all its subpanels
    # together. Re-register is what busts Blender's panel-sort cache;
    # without it the new order doesn't show until the user clicks any
    # panel header. The subpanel-aware variant keeps Lighting's
    # children attached (prelight / lightmap / itera / vc_postprocess /
    # bake_settings) when light_master is re-registered.
    changed = []
    for idname, new_order in new_orders.items():
        cls = classes.get(idname)
        if cls is None:
            continue
        if getattr(cls, 'bl_order', None) == new_order:
            continue
        cls.bl_order = new_order
        changed.append(cls)

    for parent_cls in changed:
        _reregister_with_children(parent_cls)


def _reregister_with_children(parent_cls):
    """Unregister parent + its subpanels, then re-register them in
    parent-first order so children re-attach cleanly. Used by
    apply_profile_order to bust the panel-sort cache without
    orphaning the subpanels of compound panels like light_master."""
    import bpy as _bpy

    parent_idname = getattr(parent_cls, 'bl_idname', None)
    if parent_idname is None:
        return

    # Discover registered subpanels by walking Panel.__subclasses__()
    # and filtering by bl_parent_id. Stale (unregistered) classes are
    # skipped via the bl_rna probe — only currently-live classes get
    # touched.
    subpanels = []
    for cls in list(_bpy.types.Panel.__subclasses__()):
        if getattr(cls, 'bl_parent_id', '') != parent_idname:
            continue
        if not hasattr(cls, 'bl_rna'):
            continue
        subpanels.append(cls)

    # Unregister children first, then parent. Children are dependent
    # on parent being registered, so removing them first avoids
    # Blender complaining about orphan children at unregister time.
    for sub in subpanels:
        try:
            _bpy.utils.unregister_class(sub)
        except Exception:
            pass
    try:
        _bpy.utils.unregister_class(parent_cls)
    except Exception:
        pass

    # Register parent first so children have a valid parent to attach
    # to. Any failure here is logged but doesn't stop sibling work.
    try:
        _bpy.utils.register_class(parent_cls)
    except Exception as ex:
        print(f"[INU profiles] re-register parent failed for "
              f"{parent_idname}: {ex}")
    for sub in subpanels:
        try:
            _bpy.utils.register_class(sub)
        except Exception as ex:
            print(f"[INU profiles] re-register subpanel failed for "
                  f"{getattr(sub, 'bl_idname', '?')}: {ex}")


def _force_sidebar_refresh():
    """Tag every VIEW_3D's N-sidebar for redraw after a profile change.

    History: an earlier version cycled the active workspace via
    ``bpy.ops.screen.workspace_cycle(NEXT)/(PREV)`` to bust Blender's
    per-region panel-list cache and force a full re-sort. That worked
    visually but logged C-level ERRORs ("invalid operator call
    SCREEN_OT_workspace_cycle") whenever the operator's poll() failed
    in the call's resolved context — and the error fires BEFORE
    Python's try/except, so it can't be silenced from Python.

    Tradeoff: tag_redraw alone repaints regions but does NOT force
    Blender to re-evaluate the panel sort. After a profile change the
    user may need to collapse/expand any panel once for the new order
    to apply. Acceptable in exchange for a clean console.

    Earlier alternatives that didn't work either:
      - unregister + register panel — Blender 5.x keeps the sort cache
      - show_region_ui off/on — flickers + still doesn't re-sort
    """
    def _redraw():
        wm = bpy.context.window_manager
        if wm is None:
            return None
        for window in wm.windows:
            for area in window.screen.areas:
                if area.type != 'VIEW_3D':
                    continue
                area.tag_redraw()
                for region in area.regions:
                    if region.type == 'UI':
                        region.tag_redraw()
        return None

    # Defer one tick so the redraw runs after the current property
    # update returns and Blender's UI is in a stable state.
    try:
        bpy.app.timers.register(_redraw, first_interval=0.01)
    except Exception:
        _redraw()


def _on_profile_changed(self, context):
    """scene.inu_settings.gtatools_profile update callback — invoked by Blender
    whenever the dropdown switches. Reapplies ordering and forces a
    sidebar redraw so the rearrangement appears immediately."""
    profile_id = getattr(self, 'gtatools_profile', 'ALL')
    apply_profile_order(profile_id)
    _force_sidebar_refresh()


# ── Operators ───────────────────────────────────────────────────

class GTATOOLS_OT_profile_save(bpy.types.Operator):
    """Создать новый профиль. Маленький popup только с именем и
    описанием — все панели включаются по умолчанию, видимость и
    порядок настраиваются после через кнопку ⚙ (Edit Profile)."""
    bl_idname = "gtatools.profile_save"
    bl_label = "INU: Save Panel Profile"
    bl_options = {'REGISTER'}

    profile_name: bpy.props.StringProperty(
        name="Имя",
        description="Имя нового профиля. Заменит существующий с тем же именем",
        default="My Profile",
    )
    description: bpy.props.StringProperty(
        name="Описание",
        description="Короткая подсказка для tooltip в dropdown",
        default="",
    )

    def invoke(self, context, event):
        # confirm_text overrides the default «OK» label so the
        # button reads «Создать» — matches the operator's purpose
        # better than a generic confirm. Blender 4.1+ ignores
        # unknown kwargs gracefully on older versions.
        return context.window_manager.invoke_props_dialog(
            self, width=260, confirm_text="Создать")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "profile_name")
        layout.prop(self, "description")

    def execute(self, context):
        if not _is_valid_name(self.profile_name):
            self.report({'ERROR'},
                        T("Имя содержит недопустимые символы или слишком длинное"))
            return {'CANCELLED'}
        if self.profile_name.upper() == 'ALL':
            self.report({'ERROR'},
                        T("Имя 'ALL' зарезервировано"))
            return {'CANCELLED'}

        # Default: all panels in canonical order, nothing hidden.
        # User refines via the Edit Profile popup (⚙ button).
        order = [idname for idname, _ in ALL_TOGGLEABLE_PANELS]

        if save_user_profile(self.profile_name, order,
                             self.description, hidden=[]):
            try:
                context.scene.inu_settings.gtatools_profile = self.profile_name
            except Exception:
                pass
            self.report({'INFO'},
                        f"{T('Создан: ')}{self.profile_name}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, T("Ошибка записи профиля"))
            return {'CANCELLED'}


class GTATOOLS_OT_profile_delete(bpy.types.Operator):
    """Удалить активный пользовательский профиль (ALL удалить нельзя)."""
    bl_idname = "gtatools.profile_delete"
    bl_label = "INU: Delete Panel Profile"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        active = getattr(context.scene.inu_settings, 'gtatools_profile', 'ALL')
        return active and active != 'ALL'

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        active = context.scene.inu_settings.gtatools_profile
        if active == 'ALL':
            self.report({'ERROR'}, T("ALL удалить нельзя"))
            return {'CANCELLED'}
        if delete_user_profile(active):
            context.scene.inu_settings.gtatools_profile = 'ALL'
            self.report({'INFO'}, f"{T('Удалён: ')}{active}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, T("Ошибка удаления"))
            return {'CANCELLED'}


class GTATOOLS_OT_profile_pick_panel(bpy.types.Operator):
    """Click-to-pick / click-to-place reorder: первый клик «берёт»
    панель (она подсвечивается), второй клик по другой панели
    «кладёт» её на это место. Эмулирует drag-and-drop через два
    клика — Blender Python не отдаёт настоящий drag для custom
    items в popup'е."""
    bl_idname = "gtatools.profile_pick_panel"
    bl_label = "INU: Pick / Place Panel in Profile"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    panel_idname: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        # Empty per-instance description — Blender hover tooltip would
        # otherwise show the verbose docstring on every panel-name
        # button in the editor, drowning out the labels themselves.
        return ""

    @classmethod
    def poll(cls, context):
        active = getattr(context.scene.inu_settings, 'gtatools_profile', 'ALL')
        return active and active != 'ALL'

    def execute(self, context):
        scene = context.scene
        active = scene.inu_settings.gtatools_profile
        if active == 'ALL':
            return {'CANCELLED'}
        prof = load_user_profile(active)
        if prof is None:
            return {'CANCELLED'}

        picked = scene.inu_settings.gtatools_profile_picked
        target = self.panel_idname

        if not picked:
            # First click — pick this panel up.
            scene.inu_settings.gtatools_profile_picked = target
            return {'FINISHED'}

        if picked == target:
            # Click on the picked panel = cancel pick.
            scene.inu_settings.gtatools_profile_picked = ""
            return {'FINISHED'}

        # Insert picked at target's position (drag semantics).
        order = list(prof.get('order') or [])
        try:
            pi = order.index(picked)
            ti = order.index(target)
        except ValueError:
            scene.inu_settings.gtatools_profile_picked = ""
            return {'CANCELLED'}

        order.pop(pi)
        # If the picked item was earlier in the list, target's index
        # shifts down by one after the pop.
        if pi < ti:
            ti -= 1
        order.insert(ti, picked)

        original_hidden = list(prof.get('hidden') or [])
        desc = prof.get('desc', '')

        # User insight: refresh has to fire AFTER the operator
        # completes — synchronous mutations from inside execute() are
        # batched by Blender into one «no net change» event. We do
        # the bare minimum here (persist the order) and schedule the
        # refresh dance entirely from timers, after Blender has had
        # a real frame to settle.
        if not save_user_profile(active, order, desc,
                                 hidden=original_hidden):
            self.report({'ERROR'}, T("Ошибка сохранения"))
            return {'CANCELLED'}

        scene.inu_settings.gtatools_profile_picked = ""

        # Re-uses the eye-toggle path that the user observed works:
        # tick 1 hides `picked` (visibility change → invalidation
        # firing on next frame), tick 2 restores it (visibility
        # back, panels re-sort with the new order we wrote above).
        bumped_hidden = list(original_hidden)
        if picked not in bumped_hidden:
            bumped_hidden.append(picked)

        def _hide_pass():
            sc = bpy.context.scene
            save_user_profile(active, order, desc, hidden=bumped_hidden)
            try:
                sc.inu_settings.gtatools_profile = 'ALL'
                sc.inu_settings.gtatools_profile = active
            except Exception:
                pass
            return None

        def _show_pass():
            sc = bpy.context.scene
            save_user_profile(active, order, desc, hidden=original_hidden)
            try:
                sc.inu_settings.gtatools_profile = 'ALL'
                sc.inu_settings.gtatools_profile = active
            except Exception:
                pass
            return None

        try:
            # Two ticks 50 ms / 200 ms — the empirically proven
            # baseline that reliably triggers Blender's panel-sort
            # cache invalidation via the visibility-toggle path.
            # Tested faster intervals (30/100, 10/30) — Blender starts
            # batching the property changes and the trick stops
            # working. 150 ms gap is the floor we can rely on.
            bpy.app.timers.register(_hide_pass, first_interval=0.05)
            bpy.app.timers.register(_show_pass, first_interval=0.20)
        except Exception:
            _hide_pass()
            _show_pass()

        return {'FINISHED'}


class GTATOOLS_OT_profile_toggle_panel(bpy.types.Operator):
    """Eye-toggle: переключает видимость одной панели в активном
    профиле. Позиция панели в `order` не меняется — только
    membership в `hidden` set."""
    bl_idname = "gtatools.profile_toggle_panel"
    bl_label = "INU: Toggle Panel Visibility"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    panel_idname: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        return ""

    @classmethod
    def poll(cls, context):
        active = getattr(context.scene.inu_settings, 'gtatools_profile', 'ALL')
        return active and active != 'ALL'

    def execute(self, context):
        active = context.scene.inu_settings.gtatools_profile
        if active == 'ALL':
            return {'CANCELLED'}
        prof = load_user_profile(active)
        if prof is None:
            return {'CANCELLED'}
        order = list(prof.get('order') or [])
        hidden = list(prof.get('hidden') or [])
        # Toggle membership in hidden — order stays untouched.
        if self.panel_idname in hidden:
            hidden.remove(self.panel_idname)
        else:
            hidden.append(self.panel_idname)
        if not save_user_profile(active, order, prof.get('desc', ''),
                                 hidden=hidden):
            return {'CANCELLED'}
        # Same trick as pick_panel — toggle the profile EnumProperty
        # to ALL and back to fire Blender's RNA notification, which
        # drives the only UI path that reliably re-evaluates poll().
        # update= callback handles the apply_profile_order + redraw.
        context.scene.inu_settings.gtatools_profile = 'ALL'
        context.scene.inu_settings.gtatools_profile = active
        return {'FINISHED'}


class GTATOOLS_OT_profile_edit(bpy.types.Operator):
    """Открыть редактор активного профиля в отдельном popup-окне.
    Та же UI что и inline-список, но скрытая за одной кнопкой —
    main panel остаётся чистой пока юзер не настраивает layout."""
    bl_idname = "gtatools.profile_edit"
    bl_label = "INU: Edit Panel Profile"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        active = getattr(context.scene.inu_settings, 'gtatools_profile', 'ALL')
        return active and active != 'ALL'

    def invoke(self, context, event):
        # invoke_popup gives us a self-resizing popover that closes on
        # outside-click — feels lighter than a full props_dialog and
        # doesn't have an OK/Cancel footer the user might mistake for
        # «commit changes», since each click is already transactional.
        # 250 is enough width for "Иерархия фреймов" + eye icon
        # without wrapping; wider feels overweight for a settings popup.
        return context.window_manager.invoke_popup(self, width=250)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        active = scene.inu_settings.gtatools_profile
        prof = load_user_profile(active)
        if prof is None:
            layout.label(text=f"Профиль не найден: {active}", **inu_icon(safe_icon('ERROR')))
            return

        layout.label(text=f"{active}", **inu_icon(safe_icon('PRESET')))

        # Single combined list — every panel is shown in one place.
        # Eye-toggle flips visibility without disturbing position;
        # click on the panel name picks it up (or places it at that
        # slot if something is already picked).
        order = list(prof.get('order') or [])
        hidden = set(prof.get('hidden') or [])
        picked = scene.inu_settings.gtatools_profile_picked

        # Hint row — always visible, switches to red (alert) when a
        # panel is picked. Keeps layout height stable so the rest of
        # the list doesn't jump up/down when picking starts/ends.
        # Strings are translated via Blender's i18n (pgettext_iface) so
        # they follow the active UI locale dynamically. The picked f-
        # string is decomposed into translatable fragments around the
        # interpolated panel name — that name comes from a separate
        # localised lookup (panel_label) and shouldn't go through the
        # message catalog twice.
        from bpy.app.translations import pgettext_iface as _t
        hint = layout.row()
        if picked:
            hint.alert = True
            hint.label(
                text=(f"{_t('Взято:')} «{_t(panel_label(picked))}» — "
                      f"{_t('клик на другую = переместить сюда')}"),
                **inu_icon(safe_icon('RESTRICT_SELECT_OFF')))
        else:
            hint.label(
                text=_t("Клик на название = взять, потом клик на "
                        "другую = поставить"),
                **inu_icon(safe_icon('INFO')))

        col = layout.column(align=True)
        for idname in order:
            row = col.row(align=True)
            row.scale_y = 1.1

            is_hidden = idname in hidden
            is_picked = (idname == picked)

            # Click name = pick / place
            name_btn = row.row(align=True)
            # Visually dim hidden rows
            if is_hidden:
                name_btn.active = False
            label_text = _t(panel_label(idname))
            if is_picked:
                label_text = f"▶ {label_text}"
            pick_op = name_btn.operator(
                "gtatools.profile_pick_panel",
                text=label_text,
                emboss=True,
                depress=is_picked,
                translate=False)
            pick_op.panel_idname = idname

            # Eye toggle on the right (HIDE_OFF / HIDE_ON)
            eye_op = row.operator(
                "gtatools.profile_toggle_panel",
                text="",
                **inu_icon(('HIDE_ON' if is_hidden else 'HIDE_OFF')))
            eye_op.panel_idname = idname

    def execute(self, context):
        return {'FINISHED'}


