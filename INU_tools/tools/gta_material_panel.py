# INU_tools.tools.gta_material_panel
#
# Condensed "GTA Material" panel for the material Properties tab. It
# surfaces the most common GTA SA modding knobs in one place:
#   • preset dropdown (Generic / Vehicle / Ped / Env / Dual / Specular)
#   • vehicle color slot (Primary/Secondary/Headlight/…)
#   • one-click "apply preset" buttons
#
# Underlying state is still stored in `mat.inu.*` custom properties so
# it round-trips through the existing DFF writer — this file only adds
# UI + orchestration.

from __future__ import annotations

import bpy


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


# ──────────────────────────── operator ───────────────────────────────

class GTATOOLS_OT_material_preset(bpy.types.Operator):
    """Записать выбранный GTA Material пресет в свойства mat.inu.*"""
    bl_idname = "gtatools.material_preset"
    bl_label = "Apply Material Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.EnumProperty(items=PRESETS, default='VEHICLE')

    @classmethod
    def poll(cls, context):
        return context.material is not None

    def execute(self, context):
        msg = apply_preset(context.material, self.preset)
        self.report({'INFO'}, msg)
        return {'FINISHED'}


# ──────────────────────────── panel ──────────────────────────────────

class GTATOOLS_PT_gta_material_panel(bpy.types.Panel):
    bl_label = "GTA Material"
    bl_idname = "GTATOOLS_PT_gta_material_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.material is not None

    def draw(self, context):
        layout = self.layout
        mat = context.material
        inu = getattr(mat, 'inu', None)
        if not inu:
            layout.label(text="No inu properties on material", icon='ERROR')
            return

        # Preset
        box = layout.box()
        box.label(text="Preset", icon='PRESET')
        scene = context.scene
        box.prop(scene, 'gtatools_material_preset', text="")
        op = box.operator("gtatools.material_preset", icon='CHECKMARK')
        op.preset = scene.gtatools_material_preset

        # Vehicle color slot (carcols.dat magic)
        box = layout.box()
        box.label(text="Vehicle Color", icon='COLOR')
        box.prop(inu, "vehicle_color_slot", text="")

        # Quick toggles summary
        box = layout.box()
        box.label(text="Active Effects", icon='MODIFIER')
        col = box.column(align=True)
        for attr, label in (
            ('export_env_map',    "Env Map"),
            ('export_bump_map',   "Bump Map"),
            ('export_specular',   "Specular"),
            ('export_reflection', "Reflection"),
            ('export_dual_tex',   "Dual Texture"),
            ('uv_anim_write',     "UV Animation"),
        ):
            if hasattr(inu, attr):
                col.prop(inu, attr, text=label)


classes = (
    GTATOOLS_OT_material_preset,
    GTATOOLS_PT_gta_material_panel,
)
