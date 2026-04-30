# INU_tools.ops.water_geometry_ops — Add water plane + snap to grid + set params + stitch.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import os
import bpy
import bmesh
from bpy.props import (
    StringProperty, BoolProperty, FloatProperty, FloatVectorProperty,
    IntProperty, EnumProperty, CollectionProperty, PointerProperty,
)

from .. import T


class GTATOOLS_OT_add_water(bpy.types.Operator):
    """Создать водный полигон с параметрами GTA SA"""
    bl_idname = "gtatools.add_water"
    bl_label = "INU: Add Water Plane"
    bl_options = {'REGISTER', 'UNDO'}

    size: FloatProperty(name="Size", default=100.0, min=4.0)
    subdivisions: IntProperty(name="Subdivisions", default=0, min=0, max=10)
    water_flag: EnumProperty(
        name="Water Type",
        items=[
            ('0', T("Обычная / Невидимая"), T("Глубокая вода, не отображается (подводные зоны)")),
            ('1', T("Обычная / Видимая"), T("Глубокая вода с волнами (океан, реки)")),
            ('2', T("Мелкая / Невидимая"), T("Мелкая вода, не отображается (анимация хождения по воде)")),
            ('3', T("Мелкая / Видимая"), T("Мелкая вода, отображается (лужи, пруды)")),
        ],
        default='1',
    )
    wave_height: FloatProperty(name="Wave Height", default=0.1, min=0.0, max=10.0)
    speed: FloatProperty(name="Speed", default=0.05, min=0.0, max=5.0)

    def execute(self, context):
        import bmesh

        mesh = bpy.data.meshes.new("Water")
        bm = bmesh.new()

        # Create water parameter layers
        speed_x_layer = bm.verts.layers.float.new('water_speed_x')
        speed_y_layer = bm.verts.layers.float.new('water_speed_y')
        speed_z_layer = bm.verts.layers.float.new('water_speed_z')
        wave_layer = bm.verts.layers.float.new('water_wave_height')

        s = self.size / 2.0
        z = context.scene.cursor.location.z

        # Create base quad
        v1 = bm.verts.new((-s, -s, z))
        v2 = bm.verts.new((s, -s, z))
        v3 = bm.verts.new((s, s, z))
        v4 = bm.verts.new((-s, s, z))

        for v in [v1, v2, v3, v4]:
            v[speed_x_layer] = 0.0
            v[speed_y_layer] = 0.0
            v[speed_z_layer] = self.speed
            v[wave_layer] = self.wave_height

        bm.faces.new([v1, v2, v3, v4])

        # Subdivide if needed
        if self.subdivisions > 0:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=self.subdivisions)
            for v in bm.verts:
                v[speed_x_layer] = 0.0
                v[speed_y_layer] = 0.0
                v[speed_z_layer] = self.speed
                v[wave_layer] = self.wave_height

        # Generate planar UV from XY coordinates
        uv_layer = bm.loops.layers.uv.new('UVMap')
        uv_scale = 1.0 / 100.0
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = (loop.vert.co.x * uv_scale, loop.vert.co.y * uv_scale)

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new("Water", mesh)
        obj['water_flag'] = int(self.water_flag)

        # Water material with texture
        from .water_import import _get_water_material
        mat = _get_water_material()
        mesh.materials.append(mat)

        # Add to Water collection
        water_col = bpy.data.collections.get("Water")
        if not water_col:
            water_col = bpy.data.collections.new("Water")
            context.scene.collection.children.link(water_col)
        water_col.objects.link(obj)

        # Position at cursor XY
        obj.location.x = context.scene.cursor.location.x
        obj.location.y = context.scene.cursor.location.y

        self.report({'INFO'}, f"Water plane created ({self.size}x{self.size})")
        return {'FINISHED'}


class GTATOOLS_OT_water_snap_grid(bpy.types.Operator):
    """Привязать вершины воды к кратным 4 координатам (требование GTA SA)"""
    bl_idname = "gtatools.water_snap_grid"
    bl_label = "INU: Snap to Grid (x4)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            mesh = obj.data
            mat_w = obj.matrix_world
            for vert in mesh.vertices:
                co = mat_w @ vert.co
                new_x = round(co.x / 4.0) * 4.0
                new_y = round(co.y / 4.0) * 4.0
                inv = mat_w.inverted()
                from mathutils import Vector
                new_co = inv @ Vector((new_x, new_y, co.z))
                vert.co = new_co
                count += 1
            mesh.update()
        self.report({'INFO'}, f"{T('Привязано вершин:')} {count}")
        return {'FINISHED'}


class GTATOOLS_OT_water_set_params(bpy.types.Operator):
    """Задать параметры воды для выделенных объектов"""
    bl_idname = "gtatools.water_set_params"
    bl_label = "INU: Set Water Parameters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        flag = int(scene.gtatools_water_flag)
        speed_x = scene.gtatools_water_speed_x
        speed_y = scene.gtatools_water_speed_y
        speed_z = scene.gtatools_water_speed_z
        wave = scene.gtatools_water_wave_height

        import bmesh
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            obj['water_flag'] = flag
            mesh = obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)

            sx = bm.verts.layers.float.get('water_speed_x') or bm.verts.layers.float.new('water_speed_x')
            sy = bm.verts.layers.float.get('water_speed_y') or bm.verts.layers.float.new('water_speed_y')
            sz = bm.verts.layers.float.get('water_speed_z') or bm.verts.layers.float.new('water_speed_z')
            wh = bm.verts.layers.float.get('water_wave_height') or bm.verts.layers.float.new('water_wave_height')

            for v in bm.verts:
                v[sx] = speed_x
                v[sy] = speed_y
                v[sz] = speed_z
                v[wh] = wave

            bm.to_mesh(mesh)
            bm.free()
            count += 1

        self.report({'INFO'}, f"{T('Параметры воды:')} {count} objects")
        return {'FINISHED'}


class GTATOOLS_OT_water_stitch(bpy.types.Operator):
    """Сшить края двух водных плоскостей (выровнять ближайшие вершины)"""
    bl_idname = "gtatools.water_stitch"
    bl_label = "INU: Stitch Water Edges"
    bl_options = {'REGISTER', 'UNDO'}

    threshold: FloatProperty(name="Threshold", default=1.0, min=0.01, max=50.0)

    def execute(self, context):
        from mathutils import kdtree

        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if len(mesh_objects) < 2:
            self.report({'ERROR'}, T("Выделите минимум 2 меш объекта"))
            return {'CANCELLED'}

        # Collect all boundary vertices (edges with only 1 face)
        all_boundary = []  # [(world_co, obj, vert_index)]

        for obj in mesh_objects:
            mesh = obj.data
            mat_w = obj.matrix_world

            # Find boundary vertices
            vert_face_count = [0] * len(mesh.vertices)
            for poly in mesh.polygons:
                for vi in poly.vertices:
                    vert_face_count[vi] += 1

            for edge in mesh.edges:
                edge_faces = 0
                for poly in mesh.polygons:
                    verts = list(poly.vertices)
                    if edge.vertices[0] in verts and edge.vertices[1] in verts:
                        edge_faces += 1
                if edge_faces == 1:  # boundary edge
                    for vi in edge.vertices:
                        co = mat_w @ mesh.vertices[vi].co
                        all_boundary.append((co, obj, vi))

        if not all_boundary:
            self.report({'WARNING'}, T("Нет граничных вершин"))
            return {'CANCELLED'}

        # Match boundary vertices between objects
        stitched = 0
        for i, (co1, obj1, vi1) in enumerate(all_boundary):
            for j, (co2, obj2, vi2) in enumerate(all_boundary):
                if obj1 == obj2 or j <= i:
                    continue
                dist = (co1 - co2).length
                if dist < self.threshold:
                    # Average position
                    avg = (co1 + co2) / 2.0
                    inv1 = obj1.matrix_world.inverted()
                    inv2 = obj2.matrix_world.inverted()
                    obj1.data.vertices[vi1].co = inv1 @ avg
                    obj2.data.vertices[vi2].co = inv2 @ avg
                    stitched += 1

        for obj in mesh_objects:
            obj.data.update()

        self.report({'INFO'}, f"{T('Сшито вершин:')} {stitched}")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_add_water,
    GTATOOLS_OT_water_snap_grid,
    GTATOOLS_OT_water_set_params,
    GTATOOLS_OT_water_stitch,
)
