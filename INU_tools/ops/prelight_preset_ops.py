# INU_tools.ops.prelight_preset_ops — Prelight bake preset load/save/delete.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import bpy
from bpy.props import (
    StringProperty,
)

from .. import T


class GTATOOLS_OT_prelight_preset_load(bpy.types.Operator):
    """Загрузить выбранный пресет"""
    bl_idname = "gtatools.prelight_preset_load"
    bl_label = "INU: Load Preset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        name = scene.gtatools_prelight_preset
        from .. import _load_prelight_presets
        presets = _load_prelight_presets()
        for p in presets:
            if p['name'] == name:
                scene.gtatools_bake_ambient = p.get('ambient', 0.10)
                scene.gtatools_bake_intensity = p.get('intensity', 0.05)
                scene.gtatools_bake_gamma = p.get('gamma', 0.50)
                scene.gtatools_bake_shadows = p.get('shadows', True)
                self.report({'INFO'}, f"{T('Пресет загружен:')} {name}")
                return {'FINISHED'}
        self.report({'ERROR'}, T("Пресет не найден"))
        return {'CANCELLED'}


class GTATOOLS_OT_prelight_preset_save(bpy.types.Operator):
    """Сохранить текущие настройки как пресет"""
    bl_idname = "gtatools.prelight_preset_save"
    bl_label = "INU: Save Preset"
    bl_options = {'REGISTER'}

    preset_name: StringProperty(name="Name", default="My Preset")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        scene = context.scene

        new_preset = {
            "name": self.preset_name,
            "ambient": scene.gtatools_bake_ambient,
            "intensity": scene.gtatools_bake_intensity,
            "gamma": scene.gtatools_bake_gamma,
            "shadows": scene.gtatools_bake_shadows,
        }

        from .. import _save_preset_file
        _save_preset_file(new_preset)
        self.report({'INFO'}, f"{T('Пресет сохранён:')} {self.preset_name}")
        return {'FINISHED'}


class GTATOOLS_OT_prelight_preset_delete(bpy.types.Operator):
    """Удалить выбранный пресет"""
    bl_idname = "gtatools.prelight_preset_delete"
    bl_label = "INU: Delete Preset"
    bl_options = {'REGISTER'}

    def execute(self, context):
        name = context.scene.gtatools_prelight_preset
        from .. import _delete_preset_file
        _delete_preset_file(name)
        self.report({'INFO'}, f"{T('Пресет удалён:')} {name}")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_prelight_preset_load,
    GTATOOLS_OT_prelight_preset_save,
    GTATOOLS_OT_prelight_preset_delete,
)
