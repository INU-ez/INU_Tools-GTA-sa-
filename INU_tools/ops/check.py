# INU_tools.ops.check — geometry validation operators.
#
# Phase 3 of UI redesign: extracted from __init__.py without behavior
# changes. Operators rely on T() (translation) and check_loose_geometry
# (geometry helper); both are imported from the addon root.

import bpy
from bpy.props import BoolProperty

from .. import T
from ..tools.model_utils import check_loose_geometry


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
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        loose_verts, loose_edges, error = check_loose_geometry(obj)

        if error:
            self.report({'ERROR'}, T(error))
            return {'CANCELLED'}

        total_problems = len(loose_verts) + len(loose_edges)

        if total_problems == 0:
            self.report({'INFO'}, f"✓ {obj.name}: {T('Геометрия в порядке!')}")
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
        return {'FINISHED'}


class GTATOOLS_OT_check_ngons(bpy.types.Operator):
    """Проверить геометрию на N-gons (полигоны с 5+ вершинами)"""
    bl_idname = "gtatools.check_ngons"
    bl_label = "INU: Check N-gons"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        import bmesh
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        ngon_indices = [f.index for f in bm.faces if len(f.verts) > 4]

        bm.free()

        if not ngon_indices:
            self.report({'INFO'}, f"✓ {obj.name}: {T('N-gons не найдены!')}")
            return {'FINISHED'}

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        for idx in ngon_indices:
            mesh.polygons[idx].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)

        self.report({'WARNING'}, f"⚠ {obj.name}: {len(ngon_indices)} {T('N-gons (5+ вершин)')}")
        return {'FINISHED'}


class GTATOOLS_OT_clean_geometry(bpy.types.Operator):
    """Удалить висящие вершины и рёбра"""
    bl_idname = "gtatools.clean_geometry"
    bl_label = "INU: Clean Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        loose_verts, loose_edges, error = check_loose_geometry(obj)

        if error:
            self.report({'ERROR'}, T(error))
            return {'CANCELLED'}

        if not loose_verts and not loose_edges:
            self.report({'INFO'}, T("Нечего удалять - геометрия чистая!"))
            return {'FINISHED'}

        import bmesh
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        verts_to_remove = [v for v in bm.verts if not v.link_faces]
        for v in verts_to_remove:
            bm.verts.remove(v)

        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()

        message = f"{T('Удалено:')} {len(loose_verts)} {T('вершин,')}{len(loose_edges)} {T('рёбер')}"
        self.report({'INFO'}, message)
        return {'FINISHED'}


class GTATOOLS_OT_clear_raw_dff(bpy.types.Operator):
    """Очистить сохранённые raw DFF данные для экспорта отредактированной геометрии"""
    bl_idname = "gtatools.clear_raw_dff"
    bl_label = "INU: Clear Raw DFF Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'ERROR'}, T("Нет активного объекта!"))
            return {'CANCELLED'}

        arm_obj = None
        if obj.type == 'MESH':
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE' and mod.object:
                    arm_obj = mod.object
                    break
        elif obj.type == 'ARMATURE':
            arm_obj = obj

        if arm_obj is None:
            self.report({'ERROR'}, T("Не найден Armature!"))
            return {'CANCELLED'}

        cleared = []
        for key in ('dff_raw_geometry_list', 'dff_raw_atomics'):
            if key in arm_obj:
                del arm_obj[key]
                cleared.append(key)

        if cleared:
            self.report({'INFO'}, f"Cleared: {', '.join(cleared)}")
        else:
            self.report({'INFO'}, "No raw DFF data to clear")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_check_geometry,
    GTATOOLS_OT_check_ngons,
    GTATOOLS_OT_clean_geometry,
    GTATOOLS_OT_clear_raw_dff,
)
