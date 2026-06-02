# INU_tools.ops.cst_export — export Blender objects to CST text format.

import os
import bpy

from ..core.col import ColModel
from ..core.cst import write_cst
from .col_export import (
    _collect_mesh, _collect_shadow_mesh, _collect_empty,
    _is_shadow_mesh, _compute_bounds,
)


def export_cst(filepath: str, objects, version: int = 3,
               model_name: str = "") -> ColModel:
    if not model_name:
        model_name = os.path.splitext(os.path.basename(filepath))[0]
    model = ColModel(version=version, model_name=model_name)
    for obj in objects:
        if obj.type == 'MESH':
            if _is_shadow_mesh(obj):
                _collect_shadow_mesh(obj, model)
            else:
                _collect_mesh(obj, model)
        elif obj.type == 'EMPTY':
            # Same sphere/box dispatcher as col_export — picks by
            # `empty_display_type`. CST is the text-format twin of
            # COL so it serialises the same `model.boxes` structure.
            _collect_empty(obj, model)
    model.bounds = _compute_bounds(model)
    write_cst(filepath, [model])
    return model


class GTATOOLS_OT_export_cst(bpy.types.Operator):
    """Экспорт выделения в текстовый файл Steve's COL Editor (.cst)"""
    bl_idname = "gtatools.export_cst"
    bl_label = "INU: Export CST (.cst)"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(default="*.cst", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "model.cst"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        from .col_export import _draw_col_auto_light
        _draw_col_auto_light(self.layout, context)

    def execute(self, context):
        objs = [o for o in context.selected_objects
                if o.type in ('MESH', 'EMPTY')]
        if not objs:
            self.report({'ERROR'}, "Select COL meshes or empties")
            return {'CANCELLED'}
        try:
            export_cst(self.filepath, objs)
            self.report({'INFO'}, f"Exported CST: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"CST export: {e}")
            return {'CANCELLED'}


classes = (
    GTATOOLS_OT_export_cst,
)
