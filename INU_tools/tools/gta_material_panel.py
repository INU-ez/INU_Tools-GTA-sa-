# INU_tools.tools.gta_material_panel
#
# Condensed "GTA Material" panel for the material Properties tab. It
# surfaces the most common GTA SA modding knobs in one place:
#   • one-click quick presets (Glass / Chrome / Paint / Reset)
#   • vehicle color slot (Primary/Secondary/Headlight/…)
#
# Underlying state is still stored in `mat.inu.*` custom properties so
# it round-trips through the existing DFF writer — this file only adds
# UI + orchestration.

import bpy

from .. import T
from . import compat
from .compat import safe_icon, inu_icon
# Built-in presets — shipped with the addon, always available.
PRESETS = (
    ('GENERIC',  "Generic",       "Plain textured material, no effects"),
    ('VEHICLE',  "Vehicle Body",  "xvehicleenv128 + vehiclespecdot64 + reflection blend"),
    ('VEHICLE_GLASS', "Vehicle Glass", "Transparent glass with env map"),
    ('PED',      "Ped / Skinned", "Plain skinned material, alpha from texture"),
    ('ENV',      "Env Mapped",    "Environment map only, no specular/reflection"),
    ('DUAL',     "Dual Texture",  "Blend with a second texture (decal/detail)"),
    ('SPECULAR', "Specular",      "Plain specular highlight from a mask texture"),
    ('CHROME',   "Chrome",        "Strong environment reflection + specular (bumpers/trim)"),
)


def _reset_effects(inu):
    """Clear every optional effect flag so presets apply from a clean base."""
    for flag in ('export_env_map', 'export_bump_map', 'export_reflection',
                 'export_specular', 'export_dual_tex', 'export_animation',
                 'uv_anim_write'):
        if hasattr(inu, flag):
            try:
                setattr(inu, flag, False)
            except Exception:
                pass


def apply_preset(mat, preset: str):
    """Apply one of the `PRESETS` identifiers to `mat.inu.*`.

    Returns a short human-readable description of what was applied.
    """
    inu = getattr(mat, 'inu', None)
    if not inu:
        return "no inu props on material"

    _reset_effects(inu)

    if preset == 'GENERIC':
        return "Generic — effects cleared"

    if preset == 'VEHICLE':
        inu.export_env_map = True
        inu.env_map_tex = 'xvehicleenv128'
        inu.env_map_coef = 0.2
        inu.env_map_fb_alpha = False
        inu.export_specular = True
        inu.specular_level = 1.0
        inu.specular_texture = 'vehiclespecdot64'
        inu.export_reflection = True
        inu.reflection_scale_x = 1.0
        inu.reflection_scale_y = 1.0
        inu.reflection_intensity = 0.05
        return "Vehicle Body — env + specular + reflection"

    if preset == 'VEHICLE_GLASS':
        inu.export_env_map = True
        inu.env_map_tex = 'xvehicleenv128'
        inu.env_map_coef = 0.4
        inu.env_map_fb_alpha = True
        return "Vehicle Glass — env map with FB alpha"

    if preset == 'PED':
        return "Ped — plain skinned material"

    if preset == 'ENV':
        inu.export_env_map = True
        inu.env_map_tex = 'xenvmap'
        inu.env_map_coef = 0.5
        return "Env Mapped"

    if preset == 'DUAL':
        inu.export_dual_tex = True
        inu.dual_tex_src_blend = '5'   # SRCALPHA
        inu.dual_tex_dst_blend = '6'   # INVSRCALPHA
        return "Dual Texture — standard alpha blend"

    if preset == 'SPECULAR':
        inu.export_specular = True
        inu.specular_level = 1.0
        return "Specular — level 1.0"

    if preset == 'CHROME':
        inu.export_env_map = True
        inu.env_map_tex = 'xvehicleenv128'
        inu.env_map_coef = 0.85          # strong, near-mirror reflection
        inu.env_map_fb_alpha = False
        inu.export_specular = True
        inu.specular_level = 1.0
        inu.specular_texture = 'vehiclespecdot64'
        return "Chrome — strong env reflection + specular"

    return f"unknown preset {preset}"


# ──────────────────────────── operators ──────────────────────────────

class GTATOOLS_OT_material_preset(bpy.types.Operator):
    """Записать выбранный GTA Material пресет в свойства mat.inu.*"""
    bl_idname = "gtatools.material_preset"
    bl_label = "INU: Apply Material Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.StringProperty(default='VEHICLE')

    @classmethod
    def poll(cls, context):
        return context.material is not None

    def execute(self, context):
        mat = context.material
        inu = getattr(mat, 'inu', None)
        if not inu:
            self.report({'ERROR'}, "no inu props")
            return {'CANCELLED'}

        msg = apply_preset(mat, self.preset)
        self.report({'INFO'}, msg)
        return {'FINISHED'}


# Material settings copied by GTATOOLS_OT_copy_material_settings. Curated to the
# RW/material knobs — deliberately EXCLUDES collision (col_*), the vehicle colour
# slot (has a side-effecting update), and UI state (material_tab).
_COPY_PROPS = (
    'ambient', 'surf_specular', 'surf_diffuse',
    'tex_filter', 'tex_addr_u', 'tex_addr_v', 'tex_filter_hi', 'mask_texture',
    'export_env_map', 'env_map_tex', 'env_map_coef', 'env_map_fb_alpha',
    'export_bump_map', 'bump_map_tex',
    'export_reflection', 'reflection_scale_x', 'reflection_scale_y',
    'reflection_offset_x', 'reflection_offset_y', 'reflection_intensity',
    'export_specular', 'specular_level', 'specular_texture',
    'export_dual_tex', 'dual_tex_src_blend', 'dual_tex_dst_blend',
    'dual_tex_texture',
    'uv_anim_write', 'animation_name', 'uv_anim_mode',
)


class GTATOOLS_OT_copy_material_settings(bpy.types.Operator):
    """Скопировать GTA-настройки активного материала на материалы всех
    выделенных объектов (эффекты, фильтр текстуры, RW-затенение, цвет)."""
    bl_idname = "gtatools.copy_material_settings"
    bl_label = "INU: Copy Material Settings to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.material is not None
                and len(context.selected_objects) > 0)

    def execute(self, context):
        src = context.material
        src_inu = getattr(src, 'inu', None)
        if not src_inu:
            self.report({'ERROR'}, "no inu props")
            return {'CANCELLED'}
        done = set()
        n = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                mat = slot.material
                if (not mat or mat == src or mat.name in done
                        or not getattr(mat, 'inu', None)):
                    continue
                for pid in _COPY_PROPS:
                    try:
                        setattr(mat.inu, pid, getattr(src_inu, pid))
                    except Exception:
                        pass
                try:
                    mat.diffuse_color = src.diffuse_color
                    # Через compat: копируем и 4.2+ Метод рендеринга с
                    # Перекрытием прозрачности, иначе на EEVEE Next
                    # прозрачность «не копировалась».
                    compat.set_blend_method(mat, compat.blend_method_of(src))
                    compat.set_transparency_overlap(
                        mat, compat.transparency_overlap(src))
                except Exception:
                    pass
                done.add(mat.name)
                n += 1
        self.report({'INFO'}, f"copied to {n} material(s)")
        return {'FINISHED'}


# NOTE: вкладка «Pipeline» удалена из unified Material panel. Блок пресетов
# материала переехал наверх вкладки «Эффекты» (см. _draw_material_effects в
# ui/panels.py), а дублирующая сводка «Active Effects» убрана как избыточная.


