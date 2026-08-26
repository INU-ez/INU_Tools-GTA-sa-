# INU_tools.ops.alpha_tools — bulk blend-mode editing for alpha materials.
#
# GTA maps have hundreds of alpha-cutout materials (fences, foliage,
# windows). Fixing their transparency mode one material at a time in the
# native Material panel is tedious. This module scans the scene (or the
# selection) for alpha materials, lists them in a scrollable UIList with
# a per-row blend-mode dropdown, and offers one-click "set blend mode on
# all" + "select the objects that use them".
#
# Detection modes (user-selectable — some alpha textures aren't meant to
# be transparent, so the filter is a choice, not a guess):
#   • NODE        — the Principled BSDF's Alpha input is actually wired
#                   (the material genuinely uses texture alpha). Default.
#   • CHANNEL     — the base texture has a *significant* alpha channel
#                   (reuses texture_ops.image_has_significant_alpha).
#   • TRANSPARENT — blend_method is already non-opaque.
#   • ALL         — any of the above.
#
# Placement of the panel is intentionally standalone (a collapsible
# sub-panel under GTA Tools) — can be relocated later.

import bpy

from .. import T
from ..tools import compat
from ..tools.compat import safe_icon, inu_icon
from .texture_ops import image_has_significant_alpha


# ── detection helpers (read-only) ───────────────────────────────────

def _principled(mat):
    if not mat or not mat.use_nodes or mat.node_tree is None:
        return None
    return next((n for n in mat.node_tree.nodes
                 if n.type == 'BSDF_PRINCIPLED'), None)


def _base_image(mat):
    """First Image-Texture datablock in the material's node tree."""
    if not mat or not mat.use_nodes or mat.node_tree is None:
        return None
    for n in mat.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image is not None:
            return n.image
    return None


def _alpha_is_wired(mat):
    """True if the shader's Alpha input is linked (material actually uses
    texture alpha). Read-only — does NOT modify the node tree."""
    bsdf = _principled(mat)
    if bsdf is None:
        return False
    ai = bsdf.inputs.get('Alpha')
    return bool(ai is not None and ai.is_linked)


def _is_transparent(mat):
    """Any non-opaque draw mode — 4.2+ 'BLENDED' render method included
    (compat.blend_method_of normalises both generations)."""
    if mat is None:
        return False
    return compat.blend_method_of(mat) != 'OPAQUE'


def material_matches(mat, mode):
    """Does `mat` count as an alpha material under the given filter mode?"""
    if mat is None:
        return False
    if mode == 'NODE':
        return _alpha_is_wired(mat)
    if mode == 'CHANNEL':
        return image_has_significant_alpha(_base_image(mat))
    if mode == 'TRANSPARENT':
        return _is_transparent(mat)
    # ALL
    return (_alpha_is_wired(mat)
            or image_has_significant_alpha(_base_image(mat))
            or _is_transparent(mat))


def _objects_in_scope(context, scope):
    if scope == 'SELECTED':
        return [o for o in context.selected_objects if o.type == 'MESH']
    scene = context.scene
    return [o for o in scene.objects if o.type == 'MESH'] if scene else []


def _materials_in_scope(context, scope):
    """Unique materials used by mesh objects in the chosen scope."""
    out = {}
    for o in _objects_in_scope(context, scope):
        for slot in o.material_slots:
            m = slot.material
            if m is not None and m.name not in out:
                out[m.name] = m
    return list(out.values())


# Set True by the scan operator while populating the list so the per-row
# `blend` update callbacks don't fire (and mutate materials) during scan.
_SUPPRESS_ITEM_UPDATE = False


def _apply_blend(mat, mode):
    """Set a material's transparency mode across Blender versions
    (compat.set_blend_method writes both ``blend_method`` and the 4.2+
    ``surface_render_method`` — on EEVEE Next the legacy property alone
    looks like "nothing applies").

    Any transparent mode also switches «Перекрытие прозрачности» OFF —
    that's the project standard for alpha materials. ``mode`` ∈
    OPAQUE / CLIP / HASHED / BLEND. Returns True if anything was set."""
    applied = compat.set_blend_method(mat, mode)
    if mode != 'OPAQUE':
        compat.set_transparency_overlap(mat, False)
    if applied:
        mat.update_tag()
    return applied


def _current_mode(mat):
    """Map a material's current transparency to OPAQUE/CLIP/HASHED/BLEND
    for the initial per-row dropdown value."""
    return compat.blend_method_of(mat)


# ── operators ───────────────────────────────────────────────────────

class GTATOOLS_OT_alpha_scan(bpy.types.Operator):
    """Собрать альфа-материалы сцены (или выделения) в список по
    выбранному режиму фильтра."""
    bl_idname = "gtatools.alpha_scan"
    bl_label = "INU: Scan alpha materials"
    bl_options = {'REGISTER'}

    def execute(self, context):
        s = context.scene.inu_settings
        mode = s.gtatools_alpha_filter_mode
        scope = s.gtatools_alpha_scope

        found = [m for m in _materials_in_scope(context, scope)
                 if material_matches(m, mode)]
        found.sort(key=lambda m: m.name.lower())

        coll = s.inu_alpha_mats
        coll.clear()
        global _SUPPRESS_ITEM_UPDATE
        _SUPPRESS_ITEM_UPDATE = True
        try:
            for m in found:
                it = coll.add()
                it.name = m.name
                it.blend = _current_mode(m)
        finally:
            _SUPPRESS_ITEM_UPDATE = False
        s.inu_alpha_mat_idx = 0

        self.report({'INFO'}, f"{T('Найдено альфа-материалов')}: {len(found)}")
        return {'FINISHED'}


class GTATOOLS_OT_alpha_apply_all(bpy.types.Operator):
    """Применить выбранный режим прозрачности ко всем материалам из
    списка."""
    bl_idname = "gtatools.alpha_apply_all"
    bl_label = "INU: Apply blend mode to all"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.inu_settings
        target = s.gtatools_alpha_bulk_blend
        n = 0
        global _SUPPRESS_ITEM_UPDATE
        _SUPPRESS_ITEM_UPDATE = True   # sync row display below without re-applying
        try:
            for item in s.inu_alpha_mats:
                mat = bpy.data.materials.get(item.name)
                if mat is None:
                    continue
                if _apply_blend(mat, target):
                    item.blend = target   # reflect the applied mode in the row
                    n += 1
        finally:
            _SUPPRESS_ITEM_UPDATE = False
        if n == 0:
            self.report({'WARNING'},
                        T("Нет альфа-материалов — нажми «Обновить»"))
            return {'CANCELLED'}
        self.report({'INFO'},
                    f"{T('Режим прозрачности изменён у')} {n} {T('материал(ов)')}")
        return {'FINISHED'}


class GTATOOLS_OT_alpha_select_objects(bpy.types.Operator):
    """Выделить объекты, использующие материалы из списка."""
    bl_idname = "gtatools.alpha_select_objects"
    bl_label = "INU: Select objects with alpha materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.inu_settings
        wanted = {item.name for item in s.inu_alpha_mats}
        if not wanted:
            self.report({'WARNING'},
                        T("Нет альфа-материалов — нажми «Обновить»"))
            return {'CANCELLED'}

        for o in context.selected_objects:
            o.select_set(False)

        n = 0
        active = None
        for o in _objects_in_scope(context, s.gtatools_alpha_scope):
            if any(sl.material is not None and sl.material.name in wanted
                   for sl in o.material_slots):
                try:
                    o.select_set(True)
                    active = o
                    n += 1
                except RuntimeError:
                    # Object not in the active view layer — can't select.
                    pass
        if active is not None:
            context.view_layer.objects.active = active
        self.report({'INFO'}, f"{T('Выделено объектов')}: {n}")
        return {'FINISHED'}


# ── UIList + panel ──────────────────────────────────────────────────

class GTATOOLS_UL_alpha_mats(bpy.types.UIList):
    """Scanned alpha materials — icon (texture preview if available) +
    name + the material's native blend-mode dropdown per row."""

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_property, index):
        # Keep draw O(1): NO node-tree walk and NO image.preview access
        # here — both run on every panel redraw (incl. when any dropdown
        # opens) and image.preview can trigger on-the-fly preview
        # generation, which makes the whole panel feel laggy. Plain icon.
        mat = bpy.data.materials.get(item.name)
        row = layout.row(align=True)
        if mat is None:
            row.label(text=f"{item.name} (?)", **inu_icon(safe_icon('ERROR')))
            return
        row.label(text=mat.name, **inu_icon(safe_icon('MATERIAL')))
        # 4-way mode (Opaque/Clip/Hashed/Blend) on the item. Its update
        # callback applies to the real material via _apply_blend, which
        # sets BOTH blend_method and surface_render_method — so it takes
        # effect on EEVEE Legacy and EEVEE Next alike.
        row.prop(item, "blend", text="")


def draw_alpha_tools(layout, context):
    """Draw the alpha-materials bulk blend-mode tool into ``layout``.

    Not a Panel of its own — hosted as the 'Альфа' tab of the GTA
    Material panel (Properties → Material). Scene-wide: scans all (or
    selected) materials, lists them with a per-row blend-mode dropdown,
    and offers bulk set + select-objects."""
    s = context.scene.inu_settings

    col = layout.column(align=True)
    col.prop(s, "gtatools_alpha_scope", expand=True)
    col.prop(s, "gtatools_alpha_filter_mode", text=T("Режим"))

    row = layout.row(align=True)
    row.operator("gtatools.alpha_scan", text=T("Обновить"),
                 **inu_icon(safe_icon('FILE_REFRESH')))
    layout.label(text=f"{T('Найдено')}: {len(s.inu_alpha_mats)}")

    layout.template_list("GTATOOLS_UL_alpha_mats", "",
                         s, "inu_alpha_mats",
                         s, "inu_alpha_mat_idx", rows=5)

    box = layout.box().column(align=True)
    box.prop(s, "gtatools_alpha_bulk_blend", text=T("Режим для всех"))
    box.operator("gtatools.alpha_apply_all",
                 text=T("Применить ко всем"),
                 **inu_icon(safe_icon('CHECKMARK')))
    layout.operator("gtatools.alpha_select_objects",
                    text=T("Выделить объекты"),
                    **inu_icon(safe_icon('RESTRICT_SELECT_OFF')))
