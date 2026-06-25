# INU_tools.ops.check — geometry validation operators.
#
# Phase 3 of UI redesign: extracted from __init__.py without behavior
# changes. Operators rely on T() (translation) and check_loose_geometry
# (geometry helper); both are imported from the addon root.

import bpy
from bpy.props import BoolProperty

from .. import T
from ..tools.model_utils import check_loose_geometry, bmesh_from_object_safe


def _flash_status(context, msg, level='INFO'):
    """Surface a check result at the bottom of the screen — Blender's
    status bar AND the floater status strip (shared by all windows).

    Why not rely on ``self.report()``: launched from a floater button these
    ops are dispatched through ``bpy.ops`` (Python), and Blender suppresses
    the report *banner* for Python-invoked operators — the message reaches
    only the Info log / console. ``set_floater_status`` surfaces it both in
    the bottom status bar and in the floater's in-window strip. *level*
    (``INFO`` / ``WARNING`` / ``ERROR``) colours the strip. Works the same
    from the N-panel button.
    """
    try:
        from .floater import base as _B
        _B.set_floater_status(msg, level, context=context)
    except Exception:
        # Floater subsystem unavailable — degrade to the status bar only.
        ws = getattr(context, 'workspace', None)
        if ws is not None:
            try:
                ws.status_text_set(str(msg))
            except Exception:
                pass


class GTATOOLS_OT_check_geometry(bpy.types.Operator):
    """Проверить геометрию на висящие вершины и рёбра"""
    bl_idname = "gtatools.check_geometry"
    bl_label = "INU: Check Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    select_loose: BoolProperty(
        name="Select Loose",
        description=T("Выделить найденные проблемные элементы"),
        default=True
    )

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            msg = T("Выберите меш объект!")
            self.report({'ERROR'}, msg)
            _flash_status(context, msg, 'ERROR')
            return {'CANCELLED'}

        loose_verts, loose_edges, error = check_loose_geometry(obj)

        if error:
            self.report({'ERROR'}, T(error))
            _flash_status(context, T(error), 'ERROR')
            return {'CANCELLED'}

        total_problems = len(loose_verts) + len(loose_edges)

        if total_problems == 0:
            msg = f"✓ {obj.name}: {T('Геометрия в порядке!')}"
            self.report({'INFO'}, msg)
            _flash_status(context, msg)
            return {'FINISHED'}

        if self.select_loose and (loose_verts or loose_edges):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            mesh = obj.data
            for idx in loose_verts:
                mesh.vertices[idx].select = True
            for idx in loose_edges:
                mesh.edges[idx].select = True

            bpy.ops.object.mode_set(mode='EDIT')
            if loose_verts:
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            elif loose_edges:
                bpy.context.tool_settings.mesh_select_mode = (False, True, False)

        message = f"⚠ {obj.name}: "
        if loose_verts:
            message += f"{len(loose_verts)} {T('висящих вершин')} "
        if loose_edges:
            message += f"{len(loose_edges)} {T('висящих рёбер')}"

        self.report({'WARNING'}, message)
        _flash_status(context, message, 'WARNING')
        return {'FINISHED'}


class GTATOOLS_OT_check_ngons(bpy.types.Operator):
    """Проверить геометрию на N-gons (полигоны с 5+ вершинами)"""
    bl_idname = "gtatools.check_ngons"
    bl_label = "INU: Check N-gons"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            msg = T("Выберите меш объект!")
            self.report({'ERROR'}, msg)
            _flash_status(context, msg, 'ERROR')
            return {'CANCELLED'}

        bm, err = bmesh_from_object_safe(obj)
        if err:
            self.report({'ERROR'}, T(err))
            _flash_status(context, T(err), 'ERROR')
            return {'CANCELLED'}

        ngon_indices = [f.index for f in bm.faces if len(f.verts) > 4]

        bm.free()

        if not ngon_indices:
            msg = f"✓ {obj.name}: {T('N-gons не найдены!')}"
            self.report({'INFO'}, msg)
            _flash_status(context, msg)
            return {'FINISHED'}

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        for idx in ngon_indices:
            mesh.polygons[idx].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)

        msg = f"⚠ {obj.name}: {len(ngon_indices)} {T('N-gons (5+ вершин)')}"
        self.report({'WARNING'}, msg)
        _flash_status(context, msg, 'WARNING')
        return {'FINISHED'}


