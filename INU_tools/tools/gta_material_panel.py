# INU_tools.tools.gta_material_panel
#
# Condensed "GTA Material" panel for the material Properties tab. It
# surfaces the most common GTA SA modding knobs in one place:
#   • preset dropdown (built-ins + user-saved presets from INU_Preset)
#   • vehicle color slot (Primary/Secondary/Headlight/…)
#   • one-click "apply preset" + Save / Delete
#
# Underlying state is still stored in `mat.inu.*` custom properties so
# it round-trips through the existing DFF writer — this file only adds
# UI + orchestration.

import bpy

from .. import T
from ..data import material_presets as _mp
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

    return f"unknown preset {preset}"


# ── Dynamic preset dropdown ─────────────────────────────────────────

# Cache invalidated by Save/Delete operators. Items must be kept alive
# (returning a fresh list every call triggers Blender's Python GC on
# the strings and breaks the dropdown — see bpy.props docs).
_items_cache: list = []


def invalidate_cache():
    global _items_cache
    _items_cache = []


def preset_items(self, context):
    """Enum items callback: built-ins + user presets from INU_Preset."""
    items = [(p_id, p_name, p_desc) for p_id, p_name, p_desc in PRESETS]
    user = _mp.list_presets()
    for name in user:
        # 'USER:<name>' encoded id, actual name shown in the label
        items.append((f'USER:{name}', name, f'Пользовательский пресет: {name}'))

    global _items_cache
    _items_cache = items
    return _items_cache


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

        if self.preset.startswith('USER:'):
            user_name = self.preset[5:]
            _reset_effects(inu)
            data = _mp.load_preset(user_name)
            if not data:
                self.report({'ERROR'}, f"preset not found: {user_name}")
                return {'CANCELLED'}
            count = _mp.apply_to_inu(inu, data)
            self.report({'INFO'}, f"{user_name}: applied {count} fields")
        else:
            msg = apply_preset(mat, self.preset)
            self.report({'INFO'}, msg)

        return {'FINISHED'}


# NOTE: вкладка «Pipeline» удалена из unified Material panel. Блок пресетов
# материала переехал наверх вкладки «Эффекты» (см. _draw_material_effects в
# ui/panels.py), а дублирующая сводка «Active Effects» убрана как избыточная.


