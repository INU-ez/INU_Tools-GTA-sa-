# INU_tools.ops.cst_import — import a CST (Steve's COL Editor text) file
# by delegating mesh creation to the regular COL importer.

from __future__ import annotations

from ..core.cst import read_cst
from .col_import import _create_mesh_from_col
import bpy


def import_cst(filepath: str):
    """Parse the CST file and create Blender objects for every MODEL block."""
    models = read_cst(filepath)
    collection = bpy.context.scene.collection
    created = []
    for m in models:
        o1 = _create_mesh_from_col(m, collection, 'COL')
        if o1:
            created.append(o1)
        o2 = _create_mesh_from_col(m, collection, 'SHA')
        if o2:
            created.append(o2)
    return created


class GTATOOLS_OT_import_cst(bpy.types.Operator):
    """Импорт текстового файла Steve's COL Editor (.cst)"""
    bl_idname = "gtatools.import_cst"
    bl_label = "Import CST (.cst)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(default="*.cst", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        try:
            created = import_cst(self.filepath)
            self.report({'INFO'}, f"Imported {len(created)} object(s)")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"CST import: {e}")
            return {'CANCELLED'}


classes = (
    GTATOOLS_OT_import_cst,
)
