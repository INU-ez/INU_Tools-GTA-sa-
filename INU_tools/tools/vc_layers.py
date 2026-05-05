"""Vertex Color Layer System — Phase 1 (data model + UI scaffold).

**Минимальная версия Blender: 3.2.** Система требует
``mesh.color_attributes`` API + FLOAT_COLOR + POINT/CORNER domain'ы,
которых нет в 2.80-3.1. На старых версиях UI секция показывает
warning-label, handler'ы не регистрируются, операторы не вызываются.

Each VCL layer is backed by a ``BYTE_COLOR``/``CORNER`` color attribute
on the mesh whose name encodes the scope:

    VCL_D_<label> — composed into Day during export-flatten
    VCL_N_<label> — composed into Night during export-flatten

The bottom of each stack is the canonical "Day" / "Night" attribute
the game reads. Phase 2 will add the live composite preview and the
export-time flatten-then-restore. Phase 1 is just add / remove /
reorder / promote-demote and the panel that classifies every color
attribute on the mesh by its name prefix.

User-visible label is editable in the panel — renaming an item there
renames the underlying attribute (preserving the prefix).
"""

from __future__ import annotations

import bpy
from bpy.props import (
    StringProperty, FloatProperty, FloatVectorProperty, BoolProperty,
    EnumProperty, IntProperty, CollectionProperty,
)

from .. import T
from . import compat
from ..core.vc_layers import (
    VCL_PREFIX_DAY, VCL_PREFIX_NIGHT,
    BASE_DAY_NAME, BASE_NIGHT_NAME,
    MAX_LAYERS_PER_STACK,
    parse_vcl_attr_name, make_vcl_attr_name, classify_attribute,
    auto_label, count_layers_per_scope, BLEND_MODES,
    composite_stack_np,
)


# ─────────────────────── live preview compositor ───────────────────────

# «Hijack» mode: when Live Preview is ON, the composite of all visible
# Day-scope layers is written DIRECTLY into the canonical "Day" color
# attribute (and same for Night). The originals are backed up to a
# base64-encoded float32 blob in a Mesh custom property. On Live
# Preview OFF, we restore from the backup.
#
# This means there's no separate VCL_PREVIEW attribute polluting the
# Color Attributes list — Day "just shows" the composite seamlessly,
# matching how Photoshop's flatten preview works inside the canvas.
#
# Trade-off: if the user paints on Day while Live Preview is ON,
# they're painting on the composite, not the base. On Live Preview
# OFF, that paint is lost (we restore the backup). The remedy is to
# always paint on a layer (VCL_D_…) when in hijack mode — Day/Night
# are read-only in that state by convention.

# Custom property names where the base attribute backups live. Stored
# on Mesh (not Object) so linked-duplicate objects share the backup.
_BACKUP_PROP_DAY = "_vcl_backup_day"
_BACKUP_PROP_NIGHT = "_vcl_backup_night"


def _backup_prop_for_scope(scope: str) -> str:
    return _BACKUP_PROP_DAY if scope == 'DAY' else _BACKUP_PROP_NIGHT


def _backup_base_attr(mesh, attr_name: str, prop_name: str) -> bool:
    """Snapshot a color attribute's pixel buffer to a custom property.

    Stored as base64-encoded float32 bytes — compact (~16 bytes/loop
    on disk after Blender's compression) and survives .blend save/load.
    Idempotent: overwrites any prior backup, so re-enabling Live
    Preview re-snapshots the current Day/Night state.
    """
    try:
        import numpy as np
        import base64
    except ImportError:
        return False
    attr = mesh.color_attributes.get(attr_name)
    if attr is None:
        return False
    n_loops = len(attr.data)
    arr = _read_color_attr_as_array(attr, n_loops)
    encoded = base64.b64encode(arr.astype(np.float32).tobytes()).decode('ascii')
    mesh[prop_name] = encoded
    return True


def _read_backup_array(mesh, prop_name: str):
    """Decode a backup custom property back into an (N, 4) float32 array.

    Returns None if no backup exists or decoding fails (e.g. geometry
    changed and the buffer is the wrong size — caller should fall back
    to whatever sensible default).
    """
    try:
        import numpy as np
        import base64
    except ImportError:
        return None
    encoded = mesh.get(prop_name)
    if not encoded:
        return None
    try:
        raw = base64.b64decode(encoded)
        arr = np.frombuffer(raw, dtype=np.float32)
        if len(arr) % 4 != 0:
            return None
        return arr.reshape(-1, 4).copy()
    except Exception:
        return None


def _restore_base_attr(mesh, attr_name: str, prop_name: str) -> bool:
    """Inverse of ``_backup_base_attr`` — write the backup buffer back
    into ``attr_name`` and delete the custom property. No-op when the
    backup is missing or the loop count doesn't match the current
    attribute (geometry changed under us)."""
    arr = _read_backup_array(mesh, prop_name)
    if arr is None:
        return False
    attr = mesh.color_attributes.get(attr_name)
    if attr is None:
        return False
    if len(attr.data) != arr.shape[0]:
        # Loop count mismatch — geometry changed since backup. Drop
        # the stale backup rather than corrupting the attribute.
        try:
            del mesh[prop_name]
        except KeyError:
            pass
        return False
    _write_array_to_color_attr(attr, arr)
    try:
        del mesh[prop_name]
    except KeyError:
        pass
    return True


def _read_color_attr_as_array(attr, n_loops: int):
    """Pull a CORNER-domain color attribute into an (N, 4) float32 array.

    Uses ``foreach_get`` — the fast path. Falls back to a Python loop
    for the rare attribute types that don't support it.
    """
    import numpy as np
    flat = np.empty(n_loops * 4, dtype=np.float32)
    try:
        attr.data.foreach_get('color', flat)
    except (TypeError, RuntimeError):
        for i, entry in enumerate(attr.data):
            c = entry.color
            flat[i * 4:i * 4 + 4] = (c[0], c[1], c[2], c[3])
    return flat.reshape((n_loops, 4))


def _write_array_to_color_attr(attr, arr):
    """Inverse of ``_read_color_attr_as_array``."""
    flat = arr.astype('float32', copy=False).ravel()
    try:
        attr.data.foreach_set('color', flat)
    except (TypeError, RuntimeError):
        for i, entry in enumerate(attr.data):
            entry.color = (flat[i * 4], flat[i * 4 + 1],
                           flat[i * 4 + 2], flat[i * 4 + 3])


def recompose_stack(mesh, scope: str) -> bool:
    """Read the base buffer + every visible VCL layer of ``scope``,
    blend them via ``core.vc_layers.composite_stack_np``, and write
    the result back into the canonical ``Day`` / ``Night`` attribute.

    The base buffer comes from ``mesh[_vcl_backup_<scope>]`` (the
    backup snapshot captured when Live Preview turned ON) — NOT from
    the live Day/Night attribute, because that one already holds the
    last composite and reading from it would double-blend.

    Returns True on success, False if numpy is unavailable, the base
    attribute doesn't exist, or there's no backup to read from. Caller
    is expected to check ``_is_live_preview_on(mesh)`` before invoking
    — there's no separate "preview off" path; when LP is off, we just
    don't recompose and Day/Night show whatever they already hold.
    """
    try:
        import numpy as np
    except ImportError:
        return False

    base_name = BASE_DAY_NAME if scope == 'DAY' else BASE_NIGHT_NAME
    backup_prop = _backup_prop_for_scope(scope)

    base_attr = mesh.color_attributes.get(base_name)
    if base_attr is None:
        return False
    n_loops = len(base_attr.data)

    # Read the original base from the backup. If no backup exists yet
    # (e.g. first Live Preview tick after toggling on), fall back to
    # capturing one now from the current Day/Night content. This is a
    # safety net — the LP-toggle handler should have already done it.
    base_arr = _read_backup_array(mesh, backup_prop)
    if base_arr is None or base_arr.shape[0] != n_loops:
        if not _backup_base_attr(mesh, base_name, backup_prop):
            return False
        base_arr = _read_backup_array(mesh, backup_prop)
        if base_arr is None:
            return False

    layer_stacks = []
    for item in mesh.gtatools_vc_layers:
        if item.scope != scope:
            continue
        attr = mesh.color_attributes.get(item.attr_name)
        if attr is None:
            continue
        if len(attr.data) != n_loops:
            # POINT-vs-CORNER mismatch — skip rather than corrupt.
            continue
        layer_arr = _read_color_attr_as_array(attr, n_loops)
        meta = {
            'opacity': item.opacity,
            'blend_mode': item.blend_mode,
            'visible': item.visible,
            'pre_brightness': item.pre_brightness,
            'pre_contrast': item.pre_contrast,
        }
        layer_stacks.append((layer_arr, meta))

    if not layer_stacks:
        # Empty stack — composite is just the original. Restore from
        # backup so Day/Night reflects what the user originally had.
        result = base_arr
    else:
        result = composite_stack_np(base_arr, layer_stacks)

    _write_array_to_color_attr(base_attr, result)

    # Stamp the scope marker — used by the panel's depress state on
    # the «Day» / «Night» buttons in the section header.
    try:
        mesh.gtatools_vc_preview_scope = scope
    except (AttributeError, TypeError):
        pass

    mesh.update()
    return True


def recompose_current(mesh):
    """Recompose whichever scope the preview is currently on. Used by
    the «Refresh Composite» button — keeps view stable while forcing
    a re-blend (e.g. after a manual color attribute edit)."""
    scope = getattr(mesh, 'gtatools_vc_preview_scope', 'DAY')
    recompose_stack(mesh, scope)


# ────────────────────── transient flatten for export ──────────────────────
#
# DFF exporter reads mesh.color_attributes["Day" / "Night"] directly.
# For Phase 3 — auto-flatten on export — we composite the VCL stacks
# into Day/Night BEFORE the export reads them, then restore the
# originals AFTER. Implementation goes through a context manager so
# the restoration runs even if export raises an exception mid-way.
#
# Distinct from the Live Preview hijack: that one persists state into
# a custom property and stays "until the user toggles off". This one
# is purely transient — snapshot lives in memory, restored at the
# end of the with-block, no side effects on the .blend.

def _flatten_into_base(mesh, scope: str):
    """One-shot composite Day/Night for export.

    Snapshots the current Day/Night attribute, composites the layer
    stack over it, writes the composite back. Returns the snapshot
    (numpy array) for the caller to restore later, or ``None`` when
    nothing was done (no base, no layers, no numpy, etc.).

    Live-Preview-on case is handled gracefully: Day/Night already hold
    the composite, so we snapshot the composite as the "snapshot to
    restore" — net effect at the end is "Day/Night = composite", which
    is exactly what the user wants in hijack mode anyway.
    """
    try:
        import numpy as np
    except ImportError:
        return None

    base_name = BASE_DAY_NAME if scope == 'DAY' else BASE_NIGHT_NAME
    base_attr = mesh.color_attributes.get(base_name)
    if base_attr is None:
        return None

    n_loops = len(base_attr.data)
    snapshot = _read_color_attr_as_array(base_attr, n_loops)

    # Pick the source we composite ON TOP of. In hijack mode the
    # backup custom-prop holds the original; in non-hijack mode the
    # current attribute IS the original and we use the snapshot.
    if _is_live_preview_on(mesh):
        backup_arr = _read_backup_array(mesh, _backup_prop_for_scope(scope))
        # Defensive fallback — backup could be missing if user toggled
        # LP on but recompose hasn't run yet. The snapshot IS the
        # composite in that case, blending layers over it produces a
        # weird «composite of composite» result. Better to skip.
        if backup_arr is None or backup_arr.shape[0] != n_loops:
            return snapshot
        base_arr = backup_arr
    else:
        base_arr = snapshot

    layer_stacks = []
    for item in mesh.gtatools_vc_layers:
        if item.scope != scope:
            continue
        attr = mesh.color_attributes.get(item.attr_name)
        if attr is None or len(attr.data) != n_loops:
            continue
        layer_arr = _read_color_attr_as_array(attr, n_loops)
        meta = {
            'opacity': item.opacity,
            'blend_mode': item.blend_mode,
            'visible': item.visible,
            'pre_brightness': item.pre_brightness,
            'pre_contrast': item.pre_contrast,
        }
        layer_stacks.append((layer_arr, meta))

    if not layer_stacks:
        # Empty stack — nothing to flatten. Return snapshot anyway so
        # restoration is a clean no-op (write same data back).
        return snapshot

    result = composite_stack_np(base_arr, layer_stacks)
    _write_array_to_color_attr(base_attr, result)
    return snapshot


def _restore_base_from_snapshot(mesh, scope: str, snapshot):
    """Inverse of ``_flatten_into_base`` — write a captured snapshot
    back into Day/Night. No-op when the snapshot is None."""
    if snapshot is None:
        return
    base_name = BASE_DAY_NAME if scope == 'DAY' else BASE_NIGHT_NAME
    attr = mesh.color_attributes.get(base_name)
    if attr is None:
        return
    if len(attr.data) != snapshot.shape[0]:
        # Geometry changed mid-export (shouldn't happen but be safe).
        return
    _write_array_to_color_attr(attr, snapshot)


from contextlib import contextmanager


@contextmanager
def flatten_for_export(meshes):
    """Composite VCL stacks into Day/Night for the duration of the
    with-block, then restore originals on exit.

    Usage:
        with flatten_for_export(mesh_objects):
            build_dff_clump(...)   # exporter reads Day/Night = composite

    Snapshots live in memory only (no custom-property side effects).
    Iterates each mesh's Day and Night stacks. No-op for meshes
    without VCL layers — they pass through unchanged. Safe to nest
    (rare, but possible if export wraps export).
    """
    backups = []  # (mesh, scope, snapshot)
    try:
        seen = set()
        for mesh in meshes:
            if mesh is None or mesh.name in seen:
                continue
            seen.add(mesh.name)
            if not getattr(mesh, 'gtatools_vc_layers', None):
                continue
            if len(mesh.gtatools_vc_layers) == 0:
                continue
            for scope in ('DAY', 'NIGHT'):
                snap = _flatten_into_base(mesh, scope)
                if snap is not None:
                    backups.append((mesh, scope, snap))
            mesh.update()
        yield
    finally:
        for mesh, scope, snap in backups:
            try:
                _restore_base_from_snapshot(mesh, scope, snap)
                mesh.update()
            except Exception as e:
                print(f"[VCL] flatten restore failed for "
                      f"{mesh.name if mesh else '?'}/{scope}: {e}")


# ─────────────────────── trigger / debounce ───────────────────────

# Tracks meshes that need a recompose after the next idle tick.
# Keyed by mesh.name → set of scopes ('DAY', 'NIGHT').
_pending_recompose: dict = {}
_recompose_timer_registered = False


def _flush_pending_recompose():
    """Drain ``_pending_recompose`` and run the queued recomposes.

    Called by a one-shot ``bpy.app.timers`` after at least one trigger
    fires — debouncing rapid slider drags / paint strokes into a single
    composite update.
    """
    global _recompose_timer_registered
    _recompose_timer_registered = False

    if not _pending_recompose:
        return None
    pending = dict(_pending_recompose)
    _pending_recompose.clear()
    for mesh_name, scopes in pending.items():
        mesh = bpy.data.meshes.get(mesh_name)
        if mesh is None:
            continue
        for scope in scopes:
            try:
                recompose_stack(mesh, scope)
            except Exception as e:
                print(f"[VCL] recompose failed for {mesh.name}/{scope}: {e}")
    return None


def schedule_recompose(mesh, scope: str):
    """Mark a mesh+scope dirty and schedule a debounced recompose."""
    global _recompose_timer_registered
    _pending_recompose.setdefault(mesh.name, set()).add(scope)
    if not _recompose_timer_registered:
        _recompose_timer_registered = True
        bpy.app.timers.register(_flush_pending_recompose,
                                first_interval=0.1)


def _is_live_preview_on(mesh) -> bool:
    return bool(getattr(mesh, 'gtatools_vc_live_preview', False))


def _on_layer_prop_change(self, context):
    """Update hook for opacity/blend_mode/visible/pre_brightness/contrast.

    Fires whenever the user moves a slider in the panel. Schedules a
    debounced recompose only when the currently-shown preview is for
    this layer's scope — touching a Night slider while Day is on
    screen has no visible effect until the user switches view.
    """
    if _LABEL_SYNC_SUPPRESSED:
        return
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return
    mesh = obj.data
    if not _is_live_preview_on(mesh):
        return
    current_scope = getattr(mesh, 'gtatools_vc_preview_scope', 'DAY')
    if self.scope != current_scope:
        return
    schedule_recompose(mesh, self.scope)


def _on_live_preview_toggle(self, context):
    """Update hook on ``mesh.gtatools_vc_live_preview``.

    ON  → backup current Day + Night to custom properties, then
          recompose both stacks into the actual Day/Night attributes.
          User now sees composite when looking at Day/Night.
    OFF → restore Day + Night from their backups, drop the custom
          properties. Day/Night go back to their original content.

    Either direction is debounced via ``schedule_recompose`` for ON,
    but restoration on OFF runs synchronously — there's no benefit to
    delaying a one-shot copy.
    """
    mesh = self
    if _is_live_preview_on(mesh):
        # Capture original Day/Night BEFORE the first composite is
        # written (otherwise we'd back up a composite as the original).
        if BASE_DAY_NAME in mesh.color_attributes:
            _backup_base_attr(mesh, BASE_DAY_NAME, _BACKUP_PROP_DAY)
        if BASE_NIGHT_NAME in mesh.color_attributes:
            _backup_base_attr(mesh, BASE_NIGHT_NAME, _BACKUP_PROP_NIGHT)
        # Recompose whichever scope is currently being viewed first
        # (snappy feedback), then the other so both stay in sync.
        scope = getattr(mesh, 'gtatools_vc_preview_scope', 'DAY')
        schedule_recompose(mesh, scope)
        other = 'NIGHT' if scope == 'DAY' else 'DAY'
        schedule_recompose(mesh, other)
    else:
        # Disable path — restore originals from backup. If the backup
        # is missing (e.g. user manually deleted the custom prop), we
        # leave Day/Night holding whatever's there. Better than
        # silently zeroing it.
        if _BACKUP_PROP_DAY in mesh:
            _restore_base_attr(mesh, BASE_DAY_NAME, _BACKUP_PROP_DAY)
        if _BACKUP_PROP_NIGHT in mesh:
            _restore_base_attr(mesh, BASE_NIGHT_NAME, _BACKUP_PROP_NIGHT)
        mesh.update()


def _layers_need_sync(mesh) -> bool:
    """Cheap check: are the layer collection's tracked names still in
    sync with the actual VCL_* color attributes on the mesh?

    Returns True if the panel would have to add/remove items to match
    reality. Used by the depsgraph hook so a full sync only runs when
    something changed (not on every viewport tick).
    """
    try:
        layers = mesh.gtatools_vc_layers
    except AttributeError:
        return False
    tracked = {item.attr_name for item in layers}
    actual = {a.name for a in mesh.color_attributes
              if parse_vcl_attr_name(a.name) is not None}
    return tracked != actual


def _on_depsgraph_paint(scene, depsgraph):
    """Combined depsgraph hook for two jobs:

    1. **Layer-list sync** — picks up VCL_* color attributes the user
       added/removed via Mesh Data Properties (outside our operators).
       Cheap-checked first so the full sync only runs on actual change.
    2. **Paint-stroke recompose** — when in vertex paint mode on a VCL
       layer with live preview on, mark the active scope dirty.

    Both bodies are cheap on the no-op path: we early-out as soon as
    nothing of interest is happening.
    """
    try:
        obj = bpy.context.active_object
    except (AttributeError, RuntimeError):
        return
    if obj is None or obj.type != 'MESH' or obj.data is None:
        return
    mesh = obj.data

    # Sync first — runs only when needed.
    if _layers_need_sync(mesh):
        try:
            _sync_layers_from_mesh(mesh)
        except (RuntimeError, AttributeError):
            # Can fail mid-undo or during scene save — safe to skip,
            # next tick will retry.
            pass

    # Paint-stroke recompose path.
    if not _is_live_preview_on(mesh):
        return
    if bpy.context.mode != 'PAINT_VERTEX':
        return
    active = mesh.color_attributes.active_color
    if active is None:
        return
    parsed = parse_vcl_attr_name(active.name)
    if parsed is None:
        return
    schedule_recompose(mesh, parsed[0])


# ────────────────────────── PropertyGroup ──────────────────────────

_BLEND_MODE_ITEMS = [
    ('NORMAL',   "Normal",   "out = base*(1-α) + layer*α"),
    ('MULTIPLY', "Multiply", "out = base*(1-α) + (base*layer)*α"),
    ('ADD',      "Add",      "out = base*(1-α) + clamp(base+layer)*α"),
    ('SUBTRACT', "Subtract", "out = base*(1-α) + clamp(base-layer)*α"),
]

_SCOPE_ITEMS = [
    ('DAY',   "Day",   "Day-time prelight target"),
    ('NIGHT', "Night", "Night-time prelight target"),
]


# Module-level flag to suppress _on_label_change recursion while our
# own operators populate / rename items. Blender PropertyGroup instances
# don't reliably preserve arbitrary attributes (no per-instance __dict__),
# so a per-item flag would be flaky — module-level is safe because
# Blender's property update callbacks are single-threaded.
_LABEL_SYNC_SUPPRESSED = False


class _suppressed_label_sync:
    """Context manager to disable the label→attribute rename hook
    while our operators tweak ``label`` / ``scope`` programmatically.
    """
    def __enter__(self):
        global _LABEL_SYNC_SUPPRESSED
        self._prev = _LABEL_SYNC_SUPPRESSED
        _LABEL_SYNC_SUPPRESSED = True

    def __exit__(self, *exc):
        global _LABEL_SYNC_SUPPRESSED
        _LABEL_SYNC_SUPPRESSED = self._prev


def _on_label_change(self, context):
    """Rename the underlying color attribute when the user edits the
    layer's label in the UI. Keeps the VCL_<scope>_ prefix intact.

    Skipped entirely when an operator is in the middle of populating
    or renaming an item — see ``_suppressed_label_sync``.
    """
    if _LABEL_SYNC_SUPPRESSED:
        return
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return
    mesh = obj.data
    old_attr = self.attr_name
    new_attr = make_vcl_attr_name(self.scope, self.label)
    if old_attr == new_attr or not old_attr:
        self['attr_name'] = new_attr
        return

    attr = mesh.color_attributes.get(old_attr)
    if attr is None:
        # Attribute was deleted out from under us — re-sync the item's
        # cached name to whatever the user typed and bail. The panel's
        # validation pass will spot the orphan on next redraw.
        self['attr_name'] = new_attr
        return

    # Avoid name collision: Blender will silently rename to "<name>.001"
    # which would silently break the user's intent. Roll back instead.
    if mesh.color_attributes.get(new_attr) is not None and new_attr != old_attr:
        with _suppressed_label_sync():
            self.label = parse_vcl_attr_name(old_attr)[1]
        return

    attr.name = new_attr
    self['attr_name'] = new_attr


class GTATOOLS_VCLayerItem(bpy.types.PropertyGroup):
    """One entry in the per-mesh VCL stack.

    The layer's vertex color data lives in a ``BYTE_COLOR`` attribute
    on the mesh; this PropertyGroup is just the metadata around it
    (display label, opacity, blend mode, lock/visibility flags).
    """

    # User-visible label (without the VCL_<scope>_ prefix). Editing it
    # in the UI renames the underlying attribute via the update hook.
    label: StringProperty(
        name=T("Имя слоя"),
        description=T("Видимое имя слоя. Изменение переименует атрибут на меше"),
        default="Layer",
        update=_on_label_change,
    )

    # Cached attribute name — kept in sync with label + scope. Stored
    # so the UI can look up the attribute on every redraw without
    # re-composing the name (and so promote/demote can find the orig).
    attr_name: StringProperty(
        name="Attribute Name",
        default="",
        options={'HIDDEN'},
    )

    scope: EnumProperty(
        name=T("Куда композится"),
        description=T("Day / Night — в какой стек этот слой вкладывается при flatten"),
        items=_SCOPE_ITEMS,
        default='DAY',
    )

    opacity: FloatProperty(
        name=T("Прозрачность"),
        description=T("Какая часть слоя смешивается с тем что под ним"),
        default=1.0, min=0.0, max=1.0, subtype='FACTOR',
        update=_on_layer_prop_change,
    )

    blend_mode: EnumProperty(
        name=T("Режим"),
        description=T("Как этот слой смешивается со стеком ниже"),
        items=_BLEND_MODE_ITEMS,
        default='NORMAL',
        update=_on_layer_prop_change,
    )

    visible: BoolProperty(
        name=T("Виден"),
        description=T("Выключенный слой исключается из flatten (alpha → 0)"),
        default=True,
        update=_on_layer_prop_change,
    )

    locked: BoolProperty(
        name=T("Заблокирован"),
        description=T("Запрещает рисование на слое. Слайдеры остаются доступны"),
        default=False,
    )

    selected: BoolProperty(
        name=T("Выделен"),
        description=T("Включить в групповое редактирование (multi-edit slider'ы)"),
        default=False,
    )

    # Pre-blend brightness/contrast — applied to this layer's pixels
    # before they enter the composite. Phase 2 wires these into the
    # flattener; Phase 1 just stores the values.
    pre_brightness: FloatProperty(
        name=T("Яркость до"),
        description=T("Сдвиг яркости пикселей этого слоя ДО блендинга"),
        default=0.0, min=-1.0, max=1.0, subtype='FACTOR',
        update=_on_layer_prop_change,
    )
    pre_contrast: FloatProperty(
        name=T("Контраст до"),
        description=T("Контраст пикселей этого слоя ДО блендинга"),
        default=1.0, min=0.0, max=3.0,
        update=_on_layer_prop_change,
    )


# ────────────────────────── helpers ──────────────────────────

def _mesh_or_none(context):
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return None
    return obj.data


def _layers(mesh):
    return getattr(mesh, 'gtatools_vc_layers', None) or ()


def _existing_labels_in_scope(mesh, scope):
    return {item.label for item in _layers(mesh) if item.scope == scope}


def _sync_layers_from_mesh(mesh):
    """Make ``mesh.gtatools_vc_layers`` reflect the actual VCL_*
    color attributes present on the mesh.

    Adds entries for VCL attrs the collection doesn't know about,
    drops entries whose backing attribute has been removed manually
    (e.g. via Blender's Object Data Properties → Color Attributes UI).
    Composite attributes (VCL_COMPOSITE_*) are NOT user-editable layers
    — they're recomputed output, so they're excluded from the stack.
    Idempotent — safe to call from panel draw().
    """
    layers = mesh.gtatools_vc_layers
    known_attrs = {item.attr_name for item in layers}
    actual_attrs = {a.name for a in mesh.color_attributes
                    if parse_vcl_attr_name(a.name) is not None}

    # Drop stale entries (attribute was deleted outside our operator).
    for i in range(len(layers) - 1, -1, -1):
        if layers[i].attr_name not in actual_attrs:
            layers.remove(i)

    # Add entries for VCL_* attributes we don't track yet.
    for attr_name in actual_attrs - known_attrs:
        scope, label = parse_vcl_attr_name(attr_name)
        item = layers.add()
        # Bypass the rename hook — we're populating from existing state.
        with _suppressed_label_sync():
            item.scope = scope
            item.label = label
            item.attr_name = attr_name


def _find_layer_index(mesh, attr_name):
    for i, item in enumerate(mesh.gtatools_vc_layers):
        if item.attr_name == attr_name:
            return i
    return -1


# ────────────────────────── operators ──────────────────────────

class GTATOOLS_OT_vcl_add(bpy.types.Operator):
    """Добавить новый слой в текущий стек (Day или Night).

    Создаёт ``BYTE_COLOR``/``CORNER`` атрибут с префиксом ``VCL_D_`` или
    ``VCL_N_`` и инициализирует его прозрачным (alpha=0). Стек ограничен
    10 слоями — операция отказывает с предупреждением при переполнении"""
    bl_idname = "gtatools.vcl_add"
    bl_label = "INU: Add VC Layer"
    bl_options = {'REGISTER', 'UNDO'}

    label: StringProperty(name="Label", default="")
    scope: EnumProperty(items=_SCOPE_ITEMS, default='DAY')

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}

        _sync_layers_from_mesh(mesh)
        day_count, night_count = count_layers_per_scope(
            a.name for a in mesh.color_attributes)
        current_count = day_count if self.scope == 'DAY' else night_count
        if current_count >= MAX_LAYERS_PER_STACK:
            self.report({'WARNING'},
                T("Лимит {n} слоёв для стека {scope} достигнут").format(
                    n=MAX_LAYERS_PER_STACK,
                    scope=T("Day") if self.scope == 'DAY' else T("Night")))
            return {'CANCELLED'}

        label = self.label.strip() or auto_label(
            _existing_labels_in_scope(mesh, self.scope))
        attr_name = make_vcl_attr_name(self.scope, label)

        if mesh.color_attributes.get(attr_name) is not None:
            self.report({'WARNING'}, T("Слой с именем {} уже есть").format(label))
            return {'CANCELLED'}

        attr = mesh.color_attributes.new(
            name=attr_name, type='BYTE_COLOR', domain='CORNER')

        # Initialise to fully transparent so a fresh layer contributes
        # nothing until the user paints on it. The composite skips
        # zero-alpha pixels — which means add/remove of an empty
        # layer is a true no-op visually.
        for entry in attr.data:
            entry.color = (0.0, 0.0, 0.0, 0.0)

        item = mesh.gtatools_vc_layers.add()
        with _suppressed_label_sync():
            item.scope = self.scope
            item.label = label
            item.attr_name = attr_name

        mesh.gtatools_vc_active_layer = len(mesh.gtatools_vc_layers) - 1

        # Make the new layer the active color attribute so the user
        # is painting into it the moment they enter Vertex Paint mode.
        # In hijack mode the auto-switch is suppressed (Day/Night stay
        # active so the composite view doesn't break) — user can click
        # «Рисовать» on the row to switch when they want to paint.
        current_active = mesh.color_attributes.active_color
        on_base = current_active is not None and current_active.name in (
            BASE_DAY_NAME, BASE_NIGHT_NAME)
        if not on_base:
            try:
                mesh.color_attributes.active_color_index = list(
                    mesh.color_attributes).index(attr)
            except (ValueError, AttributeError):
                pass

        # Empty layer doesn't change the composite (alpha=0), but
        # still trigger a refresh for consistency — the layer count
        # stamp on the panel header and the metadata sync are nicer
        # when always up to date.
        if _is_live_preview_on(mesh):
            schedule_recompose(mesh, self.scope)

        self.report({'INFO'},
            f"VCL: +{attr_name} ({current_count + 1}/{MAX_LAYERS_PER_STACK})")
        return {'FINISHED'}


class GTATOOLS_OT_vcl_remove(bpy.types.Operator):
    """Удалить активный слой и его color attribute. Действие undo-able"""
    bl_idname = "gtatools.vcl_remove"
    bl_label = "INU: Remove VC Layer"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mesh = _mesh_or_none(context)
        return mesh is not None and len(mesh.gtatools_vc_layers) > 0

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}

        idx = mesh.gtatools_vc_active_layer
        if idx < 0 or idx >= len(mesh.gtatools_vc_layers):
            return {'CANCELLED'}

        item = mesh.gtatools_vc_layers[idx]
        scope = item.scope
        attr = mesh.color_attributes.get(item.attr_name)
        if attr is not None:
            mesh.color_attributes.remove(attr)
        mesh.gtatools_vc_layers.remove(idx)

        # Move active index up one so the next layer (or the bottom)
        # becomes active without leaving the index dangling past the end.
        new_idx = max(0, min(idx, len(mesh.gtatools_vc_layers) - 1))
        mesh.gtatools_vc_active_layer = new_idx
        # Composite must refresh — one layer fewer in the stack.
        if _is_live_preview_on(mesh):
            schedule_recompose(mesh, scope)
        return {'FINISHED'}


class GTATOOLS_OT_vcl_move(bpy.types.Operator):
    """Переместить активный слой вверх/вниз в стеке (меняет порядок блендинга)"""
    bl_idname = "gtatools.vcl_move"
    bl_label = "INU: Move VC Layer"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(items=[
        ('UP', "Up", ""), ('DOWN', "Down", "")])

    @classmethod
    def poll(cls, context):
        mesh = _mesh_or_none(context)
        return mesh is not None and len(mesh.gtatools_vc_layers) > 1

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}

        idx = mesh.gtatools_vc_active_layer
        if idx < 0 or idx >= len(mesh.gtatools_vc_layers):
            return {'CANCELLED'}

        new_idx = idx - 1 if self.direction == 'UP' else idx + 1
        if new_idx < 0 or new_idx >= len(mesh.gtatools_vc_layers):
            return {'CANCELLED'}

        # Capture scope BEFORE the move — after .move() the index points
        # at our item under its new position, scope is the same but
        # reading via the post-move active_layer feels less fragile.
        scope = mesh.gtatools_vc_layers[idx].scope
        mesh.gtatools_vc_layers.move(idx, new_idx)
        mesh.gtatools_vc_active_layer = new_idx
        # Reorder changes the blend stack — composite must refresh
        # immediately, otherwise the user has to wiggle a slider to
        # see the new order take effect.
        if _is_live_preview_on(mesh):
            schedule_recompose(mesh, scope)
        return {'FINISHED'}


class GTATOOLS_OT_vcl_promote(bpy.types.Operator):
    """Сделать слой полноценным прилайт-атрибутом (убрать VCL_<scope>_ префикс).

    Атрибут останется на меше под коротким именем — но из стека VCL
    исчезнет. Полезно когда заведомо «временный» слой пора зафиксировать
    как новый базовый прилайт"""
    bl_idname = "gtatools.vcl_promote"
    bl_label = "INU: Promote to Base"
    bl_options = {'REGISTER', 'UNDO'}

    attr_name: StringProperty()

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}

        attr = mesh.color_attributes.get(self.attr_name)
        if attr is None:
            self.report({'WARNING'}, T("Атрибут не найден"))
            return {'CANCELLED'}
        parsed = parse_vcl_attr_name(self.attr_name)
        if parsed is None:
            self.report({'WARNING'}, T("Не VCL-атрибут"))
            return {'CANCELLED'}

        new_name = parsed[1]
        if mesh.color_attributes.get(new_name) is not None:
            self.report({'WARNING'},
                T("Атрибут «{}» уже есть — переименуйте слой перед promote")
                    .format(new_name))
            return {'CANCELLED'}

        # Capture scope before we drop the layer entry — we need it
        # for the recompose below.
        idx = _find_layer_index(mesh, self.attr_name)
        scope = parsed[0]
        attr.name = new_name
        if idx >= 0:
            mesh.gtatools_vc_layers.remove(idx)
        # Promoted layer is no longer in the stack — composite needs
        # to refresh without it.
        if _is_live_preview_on(mesh):
            schedule_recompose(mesh, scope)
        return {'FINISHED'}


class GTATOOLS_OT_vcl_demote(bpy.types.Operator):
    """Превратить произвольный color attribute в VCL-слой (добавить префикс).

    Scope (Day или Night) определяется параметром оператора — на UI
    кнопки «→ Day» / «→ Night» рядом с не-VCL атрибутами в секции «База»"""
    bl_idname = "gtatools.vcl_demote"
    bl_label = "INU: Demote to Layer"
    bl_options = {'REGISTER', 'UNDO'}

    attr_name: StringProperty()
    scope: EnumProperty(items=_SCOPE_ITEMS, default='DAY')

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}

        attr = mesh.color_attributes.get(self.attr_name)
        if attr is None:
            self.report({'WARNING'}, T("Атрибут не найден"))
            return {'CANCELLED'}
        if parse_vcl_attr_name(self.attr_name) is not None:
            self.report({'WARNING'}, T("Это уже VCL-слой"))
            return {'CANCELLED'}

        # Cap check — refuse if target stack is already full.
        day_count, night_count = count_layers_per_scope(
            a.name for a in mesh.color_attributes)
        current_count = day_count if self.scope == 'DAY' else night_count
        if current_count >= MAX_LAYERS_PER_STACK:
            self.report({'WARNING'},
                T("Лимит {n} слоёв для стека {scope} достигнут").format(
                    n=MAX_LAYERS_PER_STACK,
                    scope=T("Day") if self.scope == 'DAY' else T("Night")))
            return {'CANCELLED'}

        new_name = make_vcl_attr_name(self.scope, self.attr_name)
        if mesh.color_attributes.get(new_name) is not None:
            self.report({'WARNING'},
                T("Атрибут «{}» уже есть").format(new_name))
            return {'CANCELLED'}

        attr.name = new_name

        item = mesh.gtatools_vc_layers.add()
        with _suppressed_label_sync():
            item.scope = self.scope
            item.label = self.attr_name  # original name → label
            item.attr_name = new_name
        # New layer joined the stack — refresh composite if Live
        # Preview is on so the demoted attribute starts contributing
        # to Day/Night immediately.
        if _is_live_preview_on(mesh):
            schedule_recompose(mesh, self.scope)
        return {'FINISHED'}


class GTATOOLS_OT_vcl_show_composite(bpy.types.Operator):
    """Сделать атрибут Day или Night активным в Color Attributes.

    В hijack-режиме (Live Preview ON) Day и Night содержат итоговую
    композицию своего стека — клик на эту кнопку просто переключает
    активный color attribute на нужный, чтобы viewport показал нужный
    стек. Если Live Preview OFF — Day/Night содержат оригиналы, кнопки
    работают как обычный «выбрать атрибут»"""
    bl_idname = "gtatools.vcl_show_composite"
    bl_label = "INU: Show Composite"
    bl_options = {'REGISTER', 'UNDO'}

    scope: EnumProperty(items=_SCOPE_ITEMS, default='DAY')

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}
        # If LP is on, ensure the composite for *this* scope is fresh
        # before we activate the attribute (the user might have edited
        # the other scope's layers, leaving this scope stale).
        if _is_live_preview_on(mesh):
            recompose_stack(mesh, self.scope)
        target_name = (BASE_DAY_NAME if self.scope == 'DAY'
                       else BASE_NIGHT_NAME)
        target_attr = mesh.color_attributes.get(target_name)
        if target_attr is None:
            self.report({'WARNING'},
                T("Атрибут «{}» не существует").format(target_name))
            return {'CANCELLED'}
        try:
            mesh.color_attributes.active_color_index = list(
                mesh.color_attributes).index(target_attr)
        except (ValueError, AttributeError):
            pass
        # Track which scope the user is currently viewing — used by the
        # button depress state and by edit-time recompose triggers
        # (only same-scope edits cause a recompute).
        try:
            mesh.gtatools_vc_preview_scope = self.scope
        except (AttributeError, TypeError):
            pass
        return {'FINISHED'}


class GTATOOLS_OT_vcl_refresh_composite(bpy.types.Operator):
    """Пересобрать composite в Day/Night вручную.

    Используется когда нужно форсировать пересчёт без триггера через
    слайдер — например после ручного редактирования атрибутов через
    Mesh Data Properties"""
    bl_idname = "gtatools.vcl_refresh_composite"
    bl_label = "INU: Refresh Composite"
    bl_options = {'REGISTER'}

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}
        if not _is_live_preview_on(mesh):
            self.report({'INFO'},
                T("Live Preview выключен — нечего обновлять"))
            return {'CANCELLED'}
        recompose_current(mesh)
        return {'FINISHED'}


class GTATOOLS_OT_vcl_apply_multi(bpy.types.Operator):
    """Применить значение слайдера к выделенным слоям.

    Режим 'ABSOLUTE' — всем выделенным присваивается одно и то же
    значение. 'RELATIVE' — каждое значение сдвигается на дельту
    относительно своего текущего"""
    bl_idname = "gtatools.vcl_apply_multi"
    bl_label = "INU: Apply to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    target: EnumProperty(items=[
        ('opacity', "Opacity", ""),
        ('pre_brightness', "Brightness", ""),
        ('pre_contrast', "Contrast", ""),
    ])
    value: FloatProperty()

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}
        selected = [it for it in mesh.gtatools_vc_layers if it.selected]
        if not selected:
            self.report({'WARNING'}, T("Нет выделенных слоёв"))
            return {'CANCELLED'}
        mode = mesh.gtatools_vc_multi_mode
        # Resolve property meta to clamp to its range — sliders don't
        # auto-clamp in RELATIVE mode if we just add a delta blindly.
        clamps = {
            'opacity':         (0.0, 1.0),
            'pre_brightness':  (-1.0, 1.0),
            'pre_contrast':    (0.0, 3.0),
        }
        lo, hi = clamps[self.target]
        scopes_changed = set()
        for item in selected:
            current = getattr(item, self.target)
            new_val = self.value if mode == 'ABSOLUTE' else current + self.value
            new_val = max(lo, min(hi, new_val))
            setattr(item, self.target, new_val)
            scopes_changed.add(item.scope)
        if _is_live_preview_on(mesh):
            for scope in scopes_changed:
                schedule_recompose(mesh, scope)
        return {'FINISHED'}


class GTATOOLS_OT_vcl_recolor_selected(bpy.types.Operator):
    """Перекрасить выделенные слои — заменить RGB всех окрашенных
    пикселей на выбранный цвет (alpha сохраняется).

    Полезно когда хочешь поменять оттенок группы слоёв, не трогая то
    что под ними и не перерисовывая руками"""
    bl_idname = "gtatools.vcl_recolor_selected"
    bl_label = "INU: Recolor Selected"
    bl_options = {'REGISTER', 'UNDO'}

    color: FloatVectorProperty(
        name=T("Цвет"),
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0),
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=240)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "color")
        mesh = _mesh_or_none(context)
        if mesh:
            n = sum(1 for it in mesh.gtatools_vc_layers if it.selected)
            layout.label(text=f"{T('Будут перекрашены')}: {n}",
                         icon='COLOR')

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}
        selected = [it for it in mesh.gtatools_vc_layers if it.selected]
        if not selected:
            self.report({'WARNING'}, T("Нет выделенных слоёв"))
            return {'CANCELLED'}

        try:
            import numpy as np
        except ImportError:
            self.report({'ERROR'}, "numpy required")
            return {'CANCELLED'}

        new_r, new_g, new_b = self.color[0], self.color[1], self.color[2]
        scopes_changed = set()
        for item in selected:
            attr = mesh.color_attributes.get(item.attr_name)
            if attr is None:
                continue
            n = len(attr.data)
            arr = _read_color_attr_as_array(attr, n)
            # Replace RGB only on pixels that have non-zero alpha — fully
            # transparent pixels stay transparent (no point painting
            # invisible canvas).
            mask = arr[:, 3] > 0.0
            arr[mask, 0] = new_r
            arr[mask, 1] = new_g
            arr[mask, 2] = new_b
            _write_array_to_color_attr(attr, arr)
            scopes_changed.add(item.scope)
        mesh.update()
        if _is_live_preview_on(mesh):
            for scope in scopes_changed:
                schedule_recompose(mesh, scope)
        return {'FINISHED'}


class GTATOOLS_OT_vcl_set_active_attr(bpy.types.Operator):
    """Сделать color attribute этого слоя активным на меше + (опционально) переключиться в Vertex Paint.

    Используется UIList'ом — клик по строке слоя сразу даёт пользователю
    рисовать в нужный атрибут без ручного переключения в Mesh Data
    Properties → Color Attributes"""
    bl_idname = "gtatools.vcl_set_active_attr"
    bl_label = "INU: Activate Layer"
    bl_options = {'REGISTER', 'UNDO'}

    attr_name: StringProperty()
    enter_paint: BoolProperty(default=False)

    def execute(self, context):
        mesh = _mesh_or_none(context)
        if mesh is None:
            return {'CANCELLED'}
        attr = mesh.color_attributes.get(self.attr_name)
        if attr is None:
            return {'CANCELLED'}
        try:
            mesh.color_attributes.active_color_index = list(
                mesh.color_attributes).index(attr)
        except (ValueError, AttributeError):
            pass
        if self.enter_paint and context.mode != 'PAINT_VERTEX':
            try:
                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
            except RuntimeError:
                pass
        return {'FINISHED'}


# ────────────────────────── UIList ──────────────────────────

# Set by the panel right before each ``template_list`` call so the
# UIList knows which scope to filter for. Module-level (rather than a
# Blender property) because we can't safely write to ID data from
# inside draw() — and this is read-only after the panel sets it.
_UILIST_FILTER_SCOPE = 'DAY'


class GTATOOLS_UL_vc_layers(bpy.types.UIList):
    """Per-scope filtered layer list.

    Same UIList class drives both the Day and the Night sections —
    we set ``_UILIST_FILTER_SCOPE`` to the scope being rendered before
    each ``template_list`` call, then read it back in ``filter_items``.
    """

    def draw_item(self, context, layout, data, item, icon, active_data,
                   active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "selected", text="", emboss=False,
                     icon='CHECKBOX_HLT' if item.selected else 'CHECKBOX_DEHLT')
            row.prop(item, "visible", text="", emboss=False,
                     icon='HIDE_OFF' if item.visible else 'HIDE_ON')
            row.prop(item, "locked", text="", emboss=False,
                     icon='LOCKED' if item.locked else 'UNLOCKED')
            # Click-to-rename label takes the bulk of the row width.
            row.prop(item, "label", text="", emboss=False)
            sub = row.row(align=True)
            sub.scale_x = 0.5
            sub.prop(item, "opacity", text="", slider=True)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=item.label)

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        target_scope = _UILIST_FILTER_SCOPE
        flt_flags = []
        flt_neworder = []
        for item in items:
            visible = (item.scope == target_scope)
            flt_flags.append(self.bitflag_filter_item if visible else 0)
        return flt_flags, flt_neworder


# ────────────────────────── inline draw section ──────────────────────────

def _looks_like_color_attr(attr):
    """Whether *attr* is a ``BYTE_COLOR`` / ``FLOAT_COLOR`` (vs UV map etc.)."""
    return getattr(attr, 'data_type', '') in {'BYTE_COLOR', 'FLOAT_COLOR'}


def _draw_other_attrs_flat_list(layout, mesh):
    """Flat list of every color attribute except the canonical Day/Night.

    Originally lived inside the prelight panel's main color-attribute
    selector — moved here because the user wants the top selector to
    only show Day/Night. This list shows everything else — VCL layers,
    VCL_PREVIEW, custom prelight names — with a radio (Activate) and
    Remove (X) button per row, matching the visual style of the top
    Day/Night list one-for-one.
    """
    active_attr = mesh.color_attributes.active_color if mesh.color_attributes else None

    others = [a for a in mesh.color_attributes
              if a.name not in (BASE_DAY_NAME, BASE_NIGHT_NAME)
              and _looks_like_color_attr(a)]
    if not others:
        return

    box = layout.box()
    box.label(text=T("Дополнительные атрибуты:"), icon='COLOR')
    for attr in others:
        row = box.row(align=True)
        is_active = bool(active_attr and active_attr.name == attr.name)
        icon = 'RADIOBUT_ON' if is_active else 'RADIOBUT_OFF'
        # Click activates the attribute (same operator the top list uses).
        op = row.operator("gtatools.select_color_attribute",
                          text=attr.name, icon=icon, depress=is_active)
        op.attribute_name = attr.name
        # Remove (X) — Blender's standard attribute remove operator.
        op_rm = row.operator("gtatools.remove_color_attr",
                             text="", icon='X')
        op_rm.attr_name = attr.name


def _draw_stack(layout, mesh, scope, header_text, icon):
    """One per-scope layer stack box (the 'Слои Day' / 'Слои Night' UIList)."""
    global _UILIST_FILTER_SCOPE
    _UILIST_FILTER_SCOPE = scope

    box = layout.box()
    head = box.row(align=True)
    head.label(text=header_text, icon=icon)

    attr_names = [a.name for a in mesh.color_attributes]
    day_count, night_count = count_layers_per_scope(attr_names)
    count = day_count if scope == 'DAY' else night_count
    head.label(text=f"{count}/{MAX_LAYERS_PER_STACK}")

    ctrl = box.row(align=True)
    op_add = ctrl.operator("gtatools.vcl_add", text="", icon='ADD')
    op_add.scope = scope
    op_add.label = ""
    ctrl.operator("gtatools.vcl_remove", text="", icon='REMOVE')
    ctrl.separator()
    op_up = ctrl.operator("gtatools.vcl_move", text="", icon='TRIA_UP')
    op_up.direction = 'UP'
    op_dn = ctrl.operator("gtatools.vcl_move", text="", icon='TRIA_DOWN')
    op_dn.direction = 'DOWN'

    if count == 0:
        box.label(text=T("Стек пуст — жми +"), icon='INFO')
        return

    box.template_list(
        "GTATOOLS_UL_vc_layers", f"vcl_{scope.lower()}",
        mesh, "gtatools_vc_layers",
        mesh, "gtatools_vc_active_layer",
        rows=min(count + 1, 6),
    )

    idx = mesh.gtatools_vc_active_layer
    if 0 <= idx < len(mesh.gtatools_vc_layers):
        active = mesh.gtatools_vc_layers[idx]
        if active.scope == scope:
            col = box.column(align=True)
            col.prop(active, "blend_mode", text=T("Режим"))
            col.prop(active, "pre_brightness", text=T("Яркость до"),
                     slider=True)
            col.prop(active, "pre_contrast", text=T("Контраст до"),
                     slider=True)
            row = col.row(align=True)
            op_act = row.operator("gtatools.vcl_set_active_attr",
                                  text=T("Рисовать"), icon='BRUSH_DATA')
            op_act.attr_name = active.attr_name
            op_act.enter_paint = True
            op_prom = row.operator("gtatools.vcl_promote",
                                   text=T("→ База"), icon='COLOR')
            op_prom.attr_name = active.attr_name


def draw_vc_layers_section(layout, context, mesh):
    """Draw the «Слои Vertex Color» collapsible section.

    На Blender 2.80-3.1 показывает warning-label вместо контролов:
    система требует mesh.color_attributes API (3.2+) + FLOAT_COLOR.
    Полная реализация — только на 3.2+.

    Called inline from the prelight panel's draw, sandwiched between
    the LightMap row and the Запекание section. Lives outside the
    Panel-class machinery because Blender doesn't let sub-panels
    insert into the middle of their parent's layout — they always
    render after the parent's body.

    Renders:
      ▾ Слои Vertex Color  [Live preview] [↻] [Day] [Night] [×]
        ┌─ Дополнительные атрибуты ──────────┐
        │ ⚪ VCL_PREVIEW       [×]          │
        │ ⚪ VCL_D_Layer_1    [×]          │
        │ …                                  │
        ├─ Слои Day ─────────────── 2/10 ──┤
        │ [+] [−] | [▲] [▼]                  │
        │ <UIList>                           │
        ├─ Слои Night ────────────── 0/10 ──┤
        │ [+] [−] | [▲] [▼]                  │
        │ Стек пуст — жми +                  │
        ├─ Выделенные слои (N) ──────────────┤
        │ [Absolute|Relative] sliders + apply│
        └────────────────────────────────────┘
    """
    # Version gate: на 2.80-3.1 секция отключена целиком.
    if not compat.HAS_COLOR_ATTRIBUTES:
        box = layout.box()
        col = box.column(align=True)
        col.label(text=T("VC Layers System"), icon='COLOR')
        col.label(
            text=compat.require_version_message(
                "VC Layers", (3, 2, 0)),
            icon='ERROR')
        return

    scene = context.scene
    expanded = bool(getattr(scene, 'gtatools_vc_layers_expanded', False))

    # Header row — TRIA toggle + section label with inline BETA tag.
    # «BETA» is part of the bl_label-style text (not a separate stamp
    # icon), so it survives across Blender versions that may lack the
    # EXPERIMENTAL icon and reads natively in localised UIs.
    head_row = layout.row(align=True)
    head_row.prop(scene, "gtatools_vc_layers_expanded",
                  icon='TRIA_DOWN' if expanded else 'TRIA_RIGHT',
                  text=T("Слои Vertex Color (BETA)"),
                  emboss=False)

    if not expanded:
        return

    # Sub-header: live preview toggle + refresh + show day/night
    sub_head = layout.row(align=True)
    sub_head.prop(mesh, "gtatools_vc_live_preview",
                  text=T("Live preview"),
                  icon='HIDE_OFF' if _is_live_preview_on(mesh)
                        else 'HIDE_ON',
                  toggle=True)
    sub_head.operator("gtatools.vcl_refresh_composite",
                      text="", icon='FILE_REFRESH')
    cur = getattr(mesh, 'gtatools_vc_preview_scope', 'DAY')
    sub = sub_head.row(align=True)
    sub.scale_x = 0.6
    op_sd = sub.operator("gtatools.vcl_show_composite",
                          text=T("Day"), icon='LIGHT_SUN',
                          depress=(cur == 'DAY'))
    op_sd.scope = 'DAY'
    op_sn = sub.operator("gtatools.vcl_show_composite",
                          text=T("Night"), icon='LIGHT_HEMI',
                          depress=(cur == 'NIGHT'))
    op_sn.scope = 'NIGHT'

    # Hint when in hijack mode: warn the user that Day/Night now
    # show the composite, so painting on them directly is a footgun.
    if _is_live_preview_on(mesh):
        info_row = layout.row()
        info_row.label(
            text=T("Day/Night показывают композит — рисуй на слое"),
            icon='INFO')
    # ──────── flat list of all non-Day/Night color attributes ────────
    _draw_other_attrs_flat_list(layout, mesh)

    # ──────── per-scope structured stacks ────────
    _draw_stack(layout, mesh, 'DAY', T("Слои Day"), 'LIGHT_SUN')
    _draw_stack(layout, mesh, 'NIGHT', T("Слои Night"), 'LIGHT_HEMI')

    # ──────── multi-edit footer (only when something is selected) ────
    selected = [it for it in mesh.gtatools_vc_layers if it.selected]
    if selected:
        box = layout.box()
        box.label(text=T("Выделенные слои ({}):").format(len(selected)),
                  icon='SELECT_EXTEND')
        row = box.row(align=True)
        row.prop(mesh, "gtatools_vc_multi_mode", expand=True)

        for prop_name, target, label_key, _lo, _hi in (
            ('gtatools_vc_multi_opacity', 'opacity',
             "Прозрачность", 0.0, 1.0),
            ('gtatools_vc_multi_brightness', 'pre_brightness',
             "Яркость до", -1.0, 1.0),
            ('gtatools_vc_multi_contrast', 'pre_contrast',
             "Контраст до", 0.0, 3.0),
        ):
            grow = box.row(align=True)
            grow.prop(mesh, prop_name, text=T(label_key), slider=True)
            op_apply = grow.operator("gtatools.vcl_apply_multi",
                                      text="", icon='CHECKMARK')
            op_apply.target = target
            op_apply.value = getattr(mesh, prop_name, 0.0)

        box.operator("gtatools.vcl_recolor_selected",
                     text=T("Перекрасить выделенные…"), icon='COLOR')


classes = (
    GTATOOLS_VCLayerItem,
    GTATOOLS_OT_vcl_add,
    GTATOOLS_OT_vcl_remove,
    GTATOOLS_OT_vcl_move,
    GTATOOLS_OT_vcl_promote,
    GTATOOLS_OT_vcl_demote,
    GTATOOLS_OT_vcl_set_active_attr,
    GTATOOLS_OT_vcl_show_composite,
    GTATOOLS_OT_vcl_refresh_composite,
    GTATOOLS_OT_vcl_apply_multi,
    GTATOOLS_OT_vcl_recolor_selected,
    GTATOOLS_UL_vc_layers,
)


# ─────────────────────── module-level register hooks ────────────────

def _on_active_layer_change(self, context):
    """When the user clicks a different row in the layer UIList, switch
    the active color attribute to that layer so they can immediately
    paint or visually inspect the raw pixels.

    Exception: when the user is currently watching ``Day`` or
    ``Night`` (the composite output in hijack mode, or the canonical
    base when Live Preview is off), DO NOT swap them off it. Moving /
    selecting layers in the list is metadata — they want to keep
    looking at the end result, not the raw layer that happens to be
    highlighted now.

    Also a no-op when the index points outside the collection (race
    after remove). Doesn't toggle paint mode — that's an explicit
    "Рисовать" button click.
    """
    layers = self.gtatools_vc_layers
    idx = self.gtatools_vc_active_layer
    if idx < 0 or idx >= len(layers):
        return
    current_active = self.color_attributes.active_color
    if current_active is not None and current_active.name in (
            BASE_DAY_NAME, BASE_NIGHT_NAME):
        return
    item = layers[idx]
    attr = self.color_attributes.get(item.attr_name)
    if attr is None:
        return
    try:
        self.color_attributes.active_color_index = list(
            self.color_attributes).index(attr)
    except (ValueError, AttributeError):
        pass


@bpy.app.handlers.persistent
def _on_file_load_vcl(_dummy):
    """Reconcile any inconsistent VCL hijack state after .blend load.

    A consistent state is:
        Live Preview ON  → backup custom prop EXISTS, Day/Night holds
                            composite
        Live Preview OFF → backup custom prop is GONE, Day/Night holds
                            original

    If we find Live Preview OFF but a backup is still present (e.g. the
    user toggled LP off in another mesh's draw context, or .blend was
    saved mid-state), we restore from the backup so Day/Night reflects
    the intended «no preview» content.
    """
    for mesh in bpy.data.meshes:
        # No layer collection? Skip — fresh mesh, nothing to reconcile.
        if not getattr(mesh, 'gtatools_vc_layers', None):
            if _BACKUP_PROP_DAY not in mesh and _BACKUP_PROP_NIGHT not in mesh:
                continue
        if _is_live_preview_on(mesh):
            # Consistent state expected — leave as is. If for some
            # reason backup is missing, ``recompose_stack`` will
            # snapshot the current Day/Night content as the new base
            # on its next run.
            continue
        # LP off — restore any leftover backups so we end up with a
        # clean Day/Night = original state.
        for prop_name, attr_name in (
            (_BACKUP_PROP_DAY, BASE_DAY_NAME),
            (_BACKUP_PROP_NIGHT, BASE_NIGHT_NAME),
        ):
            if prop_name in mesh:
                _restore_base_attr(mesh, attr_name, prop_name)


def vc_layers_register_handlers():
    """Attach the depsgraph hook for paint-stroke recomposition + the
    load_post reconciler.

    Called by the addon's ``register()`` after the timer-driven
    flush function exists. Idempotent — the addon does
    register/unregister cycles on reload and re-adding a duplicate
    handler would fire it twice per stroke.

    На Blender 2.80-3.1 — no-op, потому что вся система требует
    mesh.color_attributes (3.2+) и при срабатывании handler'ы упадут.
    """
    if not compat.HAS_COLOR_ATTRIBUTES:
        return
    handlers = bpy.app.handlers.depsgraph_update_post
    if _on_depsgraph_paint not in handlers:
        handlers.append(_on_depsgraph_paint)
    load_handlers = bpy.app.handlers.load_post
    if _on_file_load_vcl not in load_handlers:
        load_handlers.append(_on_file_load_vcl)


def vc_layers_unregister_handlers():
    handlers = bpy.app.handlers.depsgraph_update_post
    if _on_depsgraph_paint in handlers:
        handlers.remove(_on_depsgraph_paint)
    load_handlers = bpy.app.handlers.load_post
    if _on_file_load_vcl in load_handlers:
        load_handlers.remove(_on_file_load_vcl)
