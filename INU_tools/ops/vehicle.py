# INU_tools.ops.vehicle — vehicle-specific operators.
#
# Phase 3 of UI redesign: extracted from __init__.py without behavior
# changes. Both operators only touch material/object .inu properties,
# so they need no helpers from the parent module.

import bpy


class GTATOOLS_OT_sa_vehicle_preset(bpy.types.Operator):
    """Применить стандартные SA-настройки для материала кузова машины:
    env map = xvehicleenv128, specular = vehiclespecdot64, blend = 0.05, + Vehicle pipeline.
    Эквивалент кнопки "SA Vehicle default" из Kam's GTA_Material.ms."""
    bl_idname = "gtatools.sa_vehicle_preset"
    bl_label = "INU: SA Vehicle Preset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.material is not None

    def execute(self, context):
        mat = context.material
        inu = mat.inu

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
        inu.reflection_offset_x = 0.0
        inu.reflection_offset_y = 0.0
        inu.reflection_intensity = 0.05  # Kam's default blend=0.05

        self.report({'INFO'}, "SA Vehicle defaults applied (env + specular + reflection)")
        return {'FINISHED'}


class GTATOOLS_OT_apply_vehicle_pipeline(bpy.types.Operator):
    """Выставить Vehicle pipeline (0x53F2009A) на выделенных MESH-объектах.
    Нужен чтобы кузов получил env-map отражения в игре."""
    bl_idname = "gtatools.apply_vehicle_pipeline"
    bl_label = "INU: Set Vehicle Pipeline on selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            if hasattr(obj, 'inu'):
                obj.inu.pipeline = '0x53F2009A'
                count += 1
        self.report({'INFO'}, f"Vehicle pipeline set on {count} object(s)")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_sa_vehicle_preset,
    GTATOOLS_OT_apply_vehicle_pipeline,
)
