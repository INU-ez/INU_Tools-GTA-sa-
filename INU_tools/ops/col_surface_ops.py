# INU_tools.ops.col_surface_ops — COL Surface picker (material assignment) + batch set draw distance.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import bpy
from bpy.props import (
    StringProperty, BoolProperty, FloatProperty, IntProperty,
)

from .. import T
from ..tools.compat import safe_icon, inu_icon
from ..data.surface_materials import (
    GTA_SA_SURFACE_MATERIALS,
    COL_SURFACE_CATEGORIES,
    get_surface_name,
)
class GTATOOLS_OT_set_col_surface(bpy.types.Operator):
    """Назначить тип поверхности GTA SA для COL коллизии"""
    bl_idname = "gtatools.set_col_surface"
    bl_label = "INU: Set COL Surface"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: StringProperty()
    surface_id: IntProperty(default=0, min=0, max=178)

    def execute(self, context):
        mat = bpy.data.materials.get(self.material_name)
        if mat is None:
            self.report({'ERROR'}, f"Material not found: {self.material_name}")
            return {'CANCELLED'}
        mat.inu.col_mat_index = self.surface_id
        name = get_surface_name(self.surface_id)
        self.report({'INFO'}, f"{T('Surface ID назначен:')} {self.material_name} = {self.surface_id} ({name})")
        return {'FINISHED'}


class GTATOOLS_OT_col_surface_menu(bpy.types.Operator):
    """Выбрать тип поверхности для COL материала"""
    bl_idname = "gtatools.col_surface_menu"
    bl_label = "INU: Surface Type"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: StringProperty()

    # Search filter
    search: StringProperty(
        name="Search",
        description=T("Фильтр типов поверхности"),
        default="",
        options={'TEXTEDIT_UPDATE'},
    )

    # Category expand toggles (collapsed by default)
    cat_default: BoolProperty(default=False)
    cat_concrete: BoolProperty(default=False)
    cat_gravel: BoolProperty(default=False)
    cat_grass: BoolProperty(default=False)
    cat_dirt: BoolProperty(default=False)
    cat_sand: BoolProperty(default=False)
    cat_glass: BoolProperty(default=False)
    cat_wood: BoolProperty(default=False)
    cat_metal: BoolProperty(default=False)
    cat_stone: BoolProperty(default=False)
    cat_vegetation: BoolProperty(default=False)
    cat_water: BoolProperty(default=False)
    cat_misc: BoolProperty(default=False)

    _cat_props = {
        "Default": "cat_default", "Concrete": "cat_concrete", "Gravel": "cat_gravel",
        "Grass": "cat_grass", "Dirt": "cat_dirt", "Sand": "cat_sand",
        "Glass": "cat_glass", "Wood": "cat_wood", "Metal": "cat_metal",
        "Stone": "cat_stone", "Vegetation": "cat_vegetation", "Water": "cat_water",
        "Misc": "cat_misc",
    }

    def execute(self, context):
        return {'CANCELLED'}

    def invoke(self, context, event):
        self.search = ""
        return context.window_manager.invoke_popup(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "search", text="", **inu_icon(safe_icon('VIEWZOOM')))

        search_lower = self.search.lower()
        name_lookup = {sid: name for sid, name, desc in GTA_SA_SURFACE_MATERIALS}

        if search_lower:
            col = layout.column(align=True)
            for sid, name, desc in GTA_SA_SURFACE_MATERIALS:
                if search_lower not in name.lower() and search_lower not in str(sid):
                    continue
                op = col.operator("gtatools.set_col_surface", text=f"{sid}: {name}")
                op.material_name = self.material_name
                op.surface_id = sid
        else:
            for cat_name, cat_ids in COL_SURFACE_CATEGORIES:
                prop_name = self._cat_props.get(cat_name, "")
                is_open = getattr(self, prop_name, False)

                box = layout.box()
                row = box.row()
                icon = safe_icon('DISCLOSURE_TRI_DOWN') if is_open else 'DISCLOSURE_TRI_RIGHT'
                row.prop(self, prop_name, text=f"{cat_name} ({len(cat_ids)})", **inu_icon(icon), emboss=False)

                if is_open:
                    col = box.column(align=True)
                    for sid in cat_ids:
                        name = name_lookup.get(sid, f"UNKNOWN_{sid}")
                        op = col.operator("gtatools.set_col_surface", text=f"{sid}: {name}")
                        op.material_name = self.material_name
                        op.surface_id = sid


# =============================================================================

# ── Unified Material panel (Phase 1 of UI redesign) ──────────────────
#
# Replaces 3 separate Properties→Material panels (col_material_panel,
# material_effects_panel, gta_material_panel) with a single panel that
# shows one of three tab views — SURFACE / EFFECTS / PIPELINE.
#
# Tab state lives on the material itself (mat.inu.material_tab) so it
# survives switching between materials and reload. Default = SURFACE.
#
# Helpers below contain the original draw bodies verbatim — only the
# enclosing class/method wrapper is gone. Each takes (layout, mat) so
# they're testable and reusable from elsewhere.

class GTATOOLS_OT_batch_set_distance(bpy.types.Operator):
    """Задать Draw Distance и/или LOD Distance всем выделенным MESH-объектам.

    По умолчанию поля заполняются значениями активного объекта — можно
    изменить и применить к выделению одним действием. Галочки слева
    выбирают какие именно поля переписывать (удобно менять только одно)"""
    bl_idname = "gtatools.batch_set_distance"
    bl_label = "INU: Apply distances to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    apply_draw: BoolProperty(
        name=T("Применить Draw Dist"),
        default=True,
    )
    draw_distance: FloatProperty(
        name="Draw Dist",
        default=299.0, min=0.0, max=10000.0,
    )
    apply_lod: BoolProperty(
        name=T("Применить LOD Dist"),
        default=False,
    )
    lod_draw_distance: FloatProperty(
        name="LOD Dist",
        default=999.0, min=0.0, max=10000.0,
    )

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    def invoke(self, context, event):
        # Prefill from the active object so user can tweak from a known state.
        obj = context.active_object
        if obj and obj.type == 'MESH' and hasattr(obj, 'inu'):
            self.draw_distance = obj.inu.draw_distance
            self.lod_draw_distance = obj.inu.lod_draw_distance
        return context.window_manager.invoke_props_dialog(self, width=280)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "apply_draw", text="")
        sub = row.row(align=True)
        sub.active = self.apply_draw
        sub.prop(self, "draw_distance")

        row = layout.row(align=True)
        row.prop(self, "apply_lod", text="")
        sub = row.row(align=True)
        sub.active = self.apply_lod
        sub.prop(self, "lod_draw_distance")

        n = sum(1 for o in context.selected_objects if o.type == 'MESH')
        layout.label(text=f"{n} {T('объектов будет изменено')}", **inu_icon(safe_icon('INFO')))

    def execute(self, context):
        if not self.apply_draw and not self.apply_lod:
            self.report({'WARNING'}, T("Включите хотя бы одну галочку"))
            return {'CANCELLED'}
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH' or not hasattr(obj, 'inu'):
                continue
            if self.apply_draw:
                obj.inu.draw_distance = self.draw_distance
            if self.apply_lod:
                obj.inu.lod_draw_distance = self.lod_draw_distance
            count += 1
        self.report({'INFO'}, f"{T('Изменено:')} {count}")
        return {'FINISHED'}

