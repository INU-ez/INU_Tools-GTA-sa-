# INU_tools.ops.cst_import — import a CST (Steve's COL Editor text) file
# by delegating mesh creation to the regular COL importer.

from ..core.cst import read_cst
from .col_import import _create_mesh_from_col
import bpy
import os


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


class GTATOOLS_OT_drop_cst(bpy.types.Operator):
    """Импорт CST при перетаскивании во viewport (принимает несколько файлов)."""
    bl_idname = "gtatools.drop_cst"
    bl_label = "INU: Import CST (Drop)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        paths = []
        if self.files and self.directory:
            for f in self.files:
                p = os.path.join(self.directory, f.name)
                if os.path.isfile(p) and p.lower().endswith('.cst'):
                    paths.append(p)
        elif self.filepath:
            paths.append(self.filepath)
        if not paths:
            self.report({'WARNING'}, "Нет .cst файлов")
            return {'CANCELLED'}
        total = 0
        errors = 0
        for p in paths:
            try:
                total += len(import_cst(p))
            except Exception as e:
                errors += 1
                self.report({'ERROR'}, f"CST {os.path.basename(p)}: {e}")
        self.report({'INFO'},
                    f"CST: импортировано {total} объект(ов) из "
                    f"{len(paths) - errors}/{len(paths)} файлов")
        return {'FINISHED'}


if hasattr(bpy.types, 'FileHandler'):
    class GTATOOLS_FH_cst_drop(bpy.types.FileHandler):
        """File Handler для перетаскивания CST во viewport."""
        bl_idname = "GTATOOLS_FH_cst_drop"
        bl_label = "GTA CST Drop"
        bl_import_operator = "gtatools.drop_cst"
        bl_file_extensions = ".cst"

        @classmethod
        def poll_drop(cls, context):
            return context.area and context.area.type == 'VIEW_3D'


