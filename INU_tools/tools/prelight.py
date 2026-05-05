# INU_tools.tools.prelight — Vertex colors, baking, fill, scatter light

import bpy
import bmesh
import math
import numpy as np
from mathutils import Vector

from . import compat


# =============================================================================
# PRELIGHT
# =============================================================================

class GTASAPrelight:
    def __init__(self, obj, split_angle=90.0, normal_threshold=0.1,
                 top_color=(0.8235, 0.7608, 0.7137), bottom_color=(0.3, 0.3, 0.3),
                 ambient_color=(0.5, 0.5, 0.5)):
        self.obj = obj
        self.split_angle = math.radians(split_angle)
        self.normal_threshold = normal_threshold
        self.top_color = top_color
        self.bottom_color = bottom_color
        self.ambient_color = ambient_color

    def are_faces_coplanar(self, face1, face2, angle_threshold=0.01):
        dot = abs(face1.normal.dot(face2.normal))
        return dot > (1.0 - angle_threshold)

    def split_by_angle(self):
        bpy.context.view_layer.objects.active = self.obj
        self.obj.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT')

        mesh = self.obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # Mark sharp edges (compatible with 4.4+)
        if hasattr(bm.edges[0] if bm.edges else None, 'smooth'):
            # Blender < 4.1 — use edge.smooth
            for edge in bm.edges:
                edge.smooth = True
        else:
            pass  # 4.1+ — sharp via attribute below

        sharp_count = 0
        for edge in bm.edges:
            if len(edge.link_faces) != 2:
                continue
            face1, face2 = edge.link_faces[0], edge.link_faces[1]
            if self.are_faces_coplanar(face1, face2):
                continue
            dot = face1.normal.dot(face2.normal)
            dot = max(-1.0, min(1.0, dot))
            angle = math.acos(dot)
            if angle >= self.split_angle:
                if hasattr(edge, 'smooth'):
                    edge.smooth = False
                sharp_count += 1

        # Blender 4.1+: set sharp_edge attribute
        if bpy.app.version >= (4, 1, 0) and sharp_count > 0:
            bm.to_mesh(mesh)
            # Use sharp_edge attribute
            if 'sharp_edge' not in mesh.attributes:
                mesh.attributes.new('sharp_edge', 'BOOLEAN', 'EDGE')
            sharp_attr = mesh.attributes['sharp_edge']
            bm2 = bmesh.new()
            bm2.from_mesh(mesh)
            bm2.edges.ensure_lookup_table()
            bm2.faces.ensure_lookup_table()
            for edge in bm2.edges:
                if len(edge.link_faces) != 2:
                    continue
                face1, face2 = edge.link_faces[0], edge.link_faces[1]
                dot = face1.normal.dot(face2.normal)
                dot = max(-1.0, min(1.0, dot))
                angle = math.acos(dot)
                if angle >= self.split_angle:
                    sharp_attr.data[edge.index].value = True
            bm2.free()

        if bpy.app.version < (4, 1, 0):
            bm.to_mesh(mesh)
            bm.free()
        else:
            if not hasattr(self, '_bm2_used'):
                bm.to_mesh(mesh)
                bm.free()

        # Split edges by sharp marks (compatible 4.4+)
        if bpy.app.version >= (4, 1, 0):
            # Use Split Edges by sharp attribute
            bpy.context.view_layer.objects.active = self.obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            try:
                bpy.ops.mesh.split_normals()
            except:
                pass
            bpy.ops.object.mode_set(mode='OBJECT')
        else:
            edge_split = self.obj.modifiers.new(name="EdgeSplit_Prelight", type='EDGE_SPLIT')
            edge_split.use_edge_angle = False
            edge_split.use_edge_sharp = True
            bpy.ops.object.modifier_apply(modifier=edge_split.name)

    def group_coplanar_faces(self, bm, normal_threshold=0.01):
        face_groups = []
        processed = set()

        for start_face in bm.faces:
            if start_face.index in processed:
                continue
            group = []
            queue = [start_face]
            while queue:
                face = queue.pop(0)
                if face.index in processed:
                    continue
                processed.add(face.index)
                group.append(face.index)
                for edge in face.edges:
                    for linked_face in edge.link_faces:
                        if linked_face.index in processed:
                            continue
                        dot = abs(face.normal.dot(linked_face.normal))
                        if dot > (1.0 - normal_threshold):
                            queue.append(linked_face)
            if group:
                avg_normal = Vector((0, 0, 0))
                for face_idx in group:
                    avg_normal += bm.faces[face_idx].normal
                avg_normal.normalize()
                face_groups.append((avg_normal, group))
        return face_groups

    def lerp_color(self, color1, color2, factor):
        return tuple(c1 + (c2 - c1) * factor for c1, c2 in zip(color1, color2))

    def apply_vertex_colors(self):
        mesh = self.obj.data

        color_layer = compat.vcol_get(mesh, "Prelight")
        if color_layer is None:
            color_layer = compat.vcol_new(mesh, "Prelight")

        compat.vcol_active(mesh, color_layer)

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()

        face_groups = self.group_coplanar_faces(bm)

        global_z_min = min(v.co.z for v in bm.verts)
        global_z_max = max(v.co.z for v in bm.verts)
        z_range = global_z_max - global_z_min if global_z_max != global_z_min else 1.0

        loop_colors = {}

        for group_normal, face_indices in face_groups:
            normal_z = group_normal.z
            group_colors = []

            for face_idx in face_indices:
                face = bm.faces[face_idx]
                for loop in face.loops:
                    vert = loop.vert
                    z_factor = (vert.co.z - global_z_min) / z_range

                    if normal_z > 0.3:
                        base_color = self.lerp_color(self.bottom_color, self.top_color, z_factor)
                        brightness = 0.1 + 0.2 * normal_z
                        color = tuple(min(1.0, c + brightness) for c in base_color)
                    elif normal_z < -0.3:
                        darkness = 0.3 * abs(normal_z)
                        base_color = self.lerp_color(self.bottom_color, self.ambient_color, z_factor * 0.5)
                        color = tuple(max(0.0, c - darkness) for c in base_color)
                    else:
                        color = self.lerp_color(self.bottom_color, self.ambient_color, z_factor)

                    group_colors.append(color)

            if group_colors:
                avg_color = (
                    sum(c[0] for c in group_colors) / len(group_colors),
                    sum(c[1] for c in group_colors) / len(group_colors),
                    sum(c[2] for c in group_colors) / len(group_colors)
                )
                for face_idx in face_indices:
                    face = bm.faces[face_idx]
                    for loop in face.loops:
                        loop_colors[loop.index] = avg_color

        bm.free()

        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                if loop_idx in loop_colors:
                    color = loop_colors[loop_idx]
                    color_layer.data[loop_idx].color = (color[0], color[1], color[2], 1.0)

    def run(self):
        self.split_by_angle()
        self.apply_vertex_colors()


def average_colors_on_coplanar_faces(obj, normal_threshold=0.01):
    if obj is None or obj.type != 'MESH':
        return False

    mesh = obj.data
    if not compat.vcol_list(mesh):
        return False

    color_layer = compat.vcol_active(mesh)
    if color_layer is None:
        color_layer = compat.vcol_list(mesh)[0]

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    face_groups = []
    processed = set()

    for start_face in bm.faces:
        if start_face.index in processed:
            continue
        group = []
        queue = [start_face]
        while queue:
            face = queue.pop(0)
            if face.index in processed:
                continue
            processed.add(face.index)
            group.append(face.index)
            for edge in face.edges:
                for linked_face in edge.link_faces:
                    if linked_face.index in processed:
                        continue
                    dot = abs(face.normal.dot(linked_face.normal))
                    if dot > (1.0 - normal_threshold):
                        queue.append(linked_face)
        if group:
            face_groups.append(group)

    bm.free()

    for group in face_groups:
        group_loops = []
        for face_idx in group:
            poly = mesh.polygons[face_idx]
            group_loops.extend(poly.loop_indices)

        if not group_loops:
            continue

        colors = []
        for loop_idx in group_loops:
            c = color_layer.data[loop_idx].color
            colors.append((c[0], c[1], c[2]))

        avg_color = (
            sum(c[0] for c in colors) / len(colors),
            sum(c[1] for c in colors) / len(colors),
            sum(c[2] for c in colors) / len(colors)
        )

        for loop_idx in group_loops:
            color_layer.data[loop_idx].color = (avg_color[0], avg_color[1], avg_color[2], 1.0)

    return True


# =============================================================================
# UV2 TO VERTEX COLOR
# =============================================================================

def encode_uv2_to_color_16bit(obj):
    if not obj or obj.type != 'MESH':
        return False, "Select a mesh!"

    mesh = obj.data

    if len(mesh.uv_layers) < 2:
        return False, "Need 2 UV layers!"

    uv_layer = mesh.uv_layers[1]

    color_name = "UV2_Color"
    existing = compat.vcol_get(mesh, color_name)
    if existing is not None:
        compat.vcol_remove(mesh, existing)

    color_attr = compat.vcol_new(mesh, color_name)
    compat.vcol_active(mesh, color_attr)

    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            uv = uv_layer.data[loop_idx].uv
            u = max(0.0, min(1.0, uv[0]))
            v = max(0.0, min(1.0, uv[1]))

            u_16 = int(u * 65535)
            v_16 = int(v * 65535)

            r = (u_16 >> 8) / 255.0
            g = (u_16 & 0xFF) / 255.0
            b = (v_16 >> 8) / 255.0
            a = (v_16 & 0xFF) / 255.0

            color_attr.data[loop_idx].color = (r, g, b, a)

    return True, f"Encoded {len(mesh.polygons)} faces"


# =============================================================================
# PRELIGHT SCENE LIGHTS
# =============================================================================

def create_prelight_scene_lights(center, distance=100.0):
    """Создать 8 источников света для запекания prelight вокруг объекта"""

    # Color #BCBCBC = RGB(188, 188, 188) = (0.737, 0.737, 0.737)
    light_color = (0.737, 0.737, 0.737)

    cx, cy, cz = center

    # Light positions and intensities
    # Format: (name, offset (x, y, z), intensity)
    # Right = +X, Left = -X, Front = +Y, Back = -Y, Up = +Z, Down = -Z
    lights_config = [
        ("Prelight_TopRightBack",    ( distance,  -distance,  distance), 11),
        ("Prelight_BottomRightBack", ( distance,  -distance, -distance), 8),
        ("Prelight_TopLeftBack",     (-distance,  -distance,  distance), 10),
        ("Prelight_BottomLeftBack",  (-distance,  -distance, -distance), 7),
        ("Prelight_TopRightFront",   ( distance,   distance,  distance), 11),
        ("Prelight_BottomRightFront",( distance,   distance, -distance), 11),
        ("Prelight_TopLeftFront",    (-distance,   distance,  distance), 9),
        ("Prelight_BottomLeftFront", (-distance,   distance, -distance), 7),
    ]

    created_lights = []

    # Create collection for lights
    collection_name = "Prelight_Lights"
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        # Remove existing lights in collection
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)

    for name, offset, intensity in lights_config:
        # Create light data
        light_data = bpy.data.lights.new(name=name, type='POINT')
        light_data.color = light_color
        light_data.energy = intensity

        # Create light object with position relative to object center
        light_obj = bpy.data.objects.new(name=name, object_data=light_data)
        light_obj.location = (cx + offset[0], cy + offset[1], cz + offset[2])

        # Link to collection
        collection.objects.link(light_obj)
        created_lights.append(name)

    return created_lights


def remove_prelight_scene_lights():
    """Удалить все источники света prelight"""
    collection_name = "Prelight_Lights"
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
        return True
    return False


def bake_vertex_colors_from_lights(obj, use_shadows=True):
    """Запечь освещение от Point источников в vertex colors.

    Lambert per-corner (loop.normal сохраняет smooth shading), но
    теневой raycast выполняется один раз на вершину — corner'ы одной
    вершины делят результат. Запись цвета — пакетная через
    foreach_set, без поэлементного RNA-доступа.
    """
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    lights = []
    for light_obj in bpy.data.objects:
        if light_obj.type == 'LIGHT' and light_obj.data.type == 'POINT':
            if not light_obj.visible_get():
                continue
            if light_obj.hide_render:
                continue
            lights.append(light_obj)

    if not lights:
        return False, "No visible Point lights in scene!"

    mesh = obj.data
    n_verts = len(mesh.vertices)
    n_loops = len(mesh.loops)
    if n_loops == 0:
        return False, "Mesh has no loops"

    color_name = "BakedLight"
    existing = compat.vcol_get(mesh, color_name)
    if existing is not None:
        compat.vcol_remove(mesh, existing)
    color_attr = compat.vcol_new(mesh, color_name)
    compat.vcol_active(mesh, color_attr)

    world_matrix = obj.matrix_world
    normal_matrix = world_matrix.to_3x3().inverted().transposed()

    try:
        mesh.calc_normals_split()
    except Exception:
        pass

    depsgraph = bpy.context.evaluated_depsgraph_get() if use_shadows else None

    # ── Vectorized geometry pull ─────────────────────────────────
    vert_co = np.empty(n_verts * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', vert_co)
    vert_co = vert_co.reshape(n_verts, 3)
    M = np.array(world_matrix, dtype=np.float32)
    homo = np.concatenate(
        [vert_co, np.ones((n_verts, 1), dtype=np.float32)], axis=1)
    world_pos = (homo @ M.T)[:, :3]

    NM = np.array(normal_matrix, dtype=np.float32)

    vert_no = np.empty(n_verts * 3, dtype=np.float32)
    mesh.vertices.foreach_get('normal', vert_no)
    vert_no = vert_no.reshape(n_verts, 3)
    vert_world_no = vert_no @ NM.T
    norms = np.linalg.norm(vert_world_no, axis=1, keepdims=True)
    norms[norms < 1e-6] = 1.0
    vert_world_no /= norms

    loop_no = np.empty(n_loops * 3, dtype=np.float32)
    mesh.loops.foreach_get('normal', loop_no)
    loop_no = loop_no.reshape(n_loops, 3)
    loop_world_no = loop_no @ NM.T
    norms = np.linalg.norm(loop_world_no, axis=1, keepdims=True)
    norms[norms < 1e-6] = 1.0
    loop_world_no /= norms

    loop_vidx = np.empty(n_loops, dtype=np.int32)
    mesh.loops.foreach_get('vertex_index', loop_vidx)
    loop_world_pos = world_pos[loop_vidx]

    total = np.zeros((n_loops, 3), dtype=np.float32)

    for light_obj in lights:
        light = light_obj.data
        light_pos = np.array(light_obj.location, dtype=np.float32)
        light_color = np.array(light.color, dtype=np.float32) * light.energy

        # ── Per-vertex shadow raycast (cached, reused by all corners)
        shadow_per_vert = np.ones(n_verts, dtype=np.float32)
        if use_shadows and depsgraph is not None:
            for i in range(n_verts):
                wp = world_pos[i]
                ld = light_pos - wp
                dist = float(np.linalg.norm(ld))
                if dist < 1e-3:
                    continue
                ld_n = ld / dist
                ray_start = wp + vert_world_no[i] * 0.02
                result = bpy.context.scene.ray_cast(
                    depsgraph,
                    Vector((float(ray_start[0]), float(ray_start[1]), float(ray_start[2]))),
                    Vector((float(ld_n[0]), float(ld_n[1]), float(ld_n[2]))),
                    distance=dist - 0.04,
                )[0]
                if result:
                    shadow_per_vert[i] = 0.0

        # ── Per-loop Lambert (vectorized) ────────────────────────
        ld = light_pos[None, :] - loop_world_pos
        dist = np.linalg.norm(ld, axis=1)
        valid = dist >= 1e-3
        dist_safe = np.where(valid, dist, 1.0)
        ld_n = ld / dist_safe[:, None]
        n_dot_l = np.maximum(np.sum(loop_world_no * ld_n, axis=1), 0.0)
        n_dot_l = np.where(valid, n_dot_l, 0.0)
        atten = 1.0 / (1.0 + dist * 0.01 + dist * dist * 0.0001)
        shadow_for_loop = shadow_per_vert[loop_vidx]
        intensity = atten * n_dot_l * shadow_for_loop
        total += intensity[:, None] * light_color[None, :]

    np.clip(total, 0.0, 1.0, out=total)
    flat = np.empty(n_loops * 4, dtype=np.float32)
    flat[0::4] = total[:, 0]
    flat[1::4] = total[:, 1]
    flat[2::4] = total[:, 2]
    flat[3::4] = 1.0
    color_attr.data.foreach_set('color', flat)

    return True, f"Baked lighting from {len(lights)} lights"


def bake_vertex_colors_simple(obj, ambient=0.05, intensity_mult=0.008, gamma=1.8, use_shadows=True):
    """Быстрое запекание vertex colors от Point источников.

    Та же оптимизация что и в bake_vertex_colors_from_lights — Lambert
    per-corner, теневой raycast per-vertex, batch foreach_set."""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    lights = []
    for light_obj in bpy.data.objects:
        if light_obj.type == 'LIGHT' and light_obj.data.type == 'POINT':
            if not light_obj.visible_get():
                continue
            if light_obj.hide_render:
                continue
            lights.append(light_obj)

    if not lights:
        return False, "No visible Point lights in scene!"

    mesh = obj.data
    n_verts = len(mesh.vertices)
    n_loops = len(mesh.loops)
    if n_loops == 0:
        return False, "Mesh has no loops"

    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        existing = compat.vcol_list(mesh)
        if existing:
            color_attr = existing[0]
        else:
            color_attr = compat.vcol_new(mesh, "Col")
        compat.vcol_active(mesh, color_attr)
    color_name = color_attr.name

    world_matrix = obj.matrix_world
    normal_matrix = world_matrix.to_3x3().inverted().transposed()

    try:
        mesh.calc_normals_split()
    except Exception:
        pass

    depsgraph = bpy.context.evaluated_depsgraph_get() if use_shadows else None

    vert_co = np.empty(n_verts * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', vert_co)
    vert_co = vert_co.reshape(n_verts, 3)
    M = np.array(world_matrix, dtype=np.float32)
    homo = np.concatenate(
        [vert_co, np.ones((n_verts, 1), dtype=np.float32)], axis=1)
    world_pos = (homo @ M.T)[:, :3]

    NM = np.array(normal_matrix, dtype=np.float32)

    vert_no = np.empty(n_verts * 3, dtype=np.float32)
    mesh.vertices.foreach_get('normal', vert_no)
    vert_no = vert_no.reshape(n_verts, 3)
    vert_world_no = vert_no @ NM.T
    norms = np.linalg.norm(vert_world_no, axis=1, keepdims=True)
    norms[norms < 1e-6] = 1.0
    vert_world_no /= norms

    loop_no = np.empty(n_loops * 3, dtype=np.float32)
    mesh.loops.foreach_get('normal', loop_no)
    loop_no = loop_no.reshape(n_loops, 3)
    loop_world_no = loop_no @ NM.T
    norms = np.linalg.norm(loop_world_no, axis=1, keepdims=True)
    norms[norms < 1e-6] = 1.0
    loop_world_no /= norms

    loop_vidx = np.empty(n_loops, dtype=np.int32)
    mesh.loops.foreach_get('vertex_index', loop_vidx)
    loop_world_pos = world_pos[loop_vidx]

    total = np.full((n_loops, 3), ambient, dtype=np.float32)

    for light_obj in lights:
        light = light_obj.data
        light_pos = np.array(light_obj.location, dtype=np.float32)
        light_color = np.array(light.color, dtype=np.float32) * (
            light.energy * intensity_mult)

        shadow_per_vert = np.ones(n_verts, dtype=np.float32)
        if use_shadows and depsgraph is not None:
            for i in range(n_verts):
                wp = world_pos[i]
                ld = light_pos - wp
                dist = float(np.linalg.norm(ld))
                if dist < 1e-3:
                    continue
                ld_n = ld / dist
                ray_start = wp + vert_world_no[i] * 0.02
                result = bpy.context.scene.ray_cast(
                    depsgraph,
                    Vector((float(ray_start[0]), float(ray_start[1]), float(ray_start[2]))),
                    Vector((float(ld_n[0]), float(ld_n[1]), float(ld_n[2]))),
                    distance=dist - 0.04,
                )[0]
                if result:
                    shadow_per_vert[i] = 0.0

        ld = light_pos[None, :] - loop_world_pos
        dist = np.linalg.norm(ld, axis=1)
        valid = dist >= 1e-3
        dist_safe = np.where(valid, dist, 1.0)
        ld_n = ld / dist_safe[:, None]
        n_dot_l = np.maximum(np.sum(loop_world_no * ld_n, axis=1), 0.0)
        n_dot_l = np.where(valid, n_dot_l, 0.0)
        atten = 1.0 / (1.0 + dist * dist * 0.0001)
        shadow_for_loop = shadow_per_vert[loop_vidx]
        intensity = atten * n_dot_l * shadow_for_loop
        total += intensity[:, None] * light_color[None, :]

    # Gamma + clamp (negatives clipped first so pow is well-defined)
    np.clip(total, 0.0, None, out=total)
    total = np.power(total, 1.0 / gamma, dtype=np.float32)
    np.clip(total, 0.0, 1.0, out=total)

    flat = np.empty(n_loops * 4, dtype=np.float32)
    flat[0::4] = total[:, 0]
    flat[1::4] = total[:, 1]
    flat[2::4] = total[:, 2]
    flat[3::4] = 1.0
    color_attr.data.foreach_set('color', flat)

    return True, f"Baked to '{color_name}' from {len(lights)} lights"


def apply_brightness_offset(obj, v_offset):
    """Apply V (brightness) offset to vertex colors like 3Ds Max Adjust Color

    In 3Ds Max, V offset works as percentage:
    - V = -80 means keep 20% of brightness (multiply by 0.2)
    - V = +50 means increase brightness by 50% (multiply by 1.5)

    Tracks current V offset to allow adjusting in any direction.
    """
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    if not compat.vcol_list(mesh):
        return False, "No vertex colors found!"

    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        return False, "No active color layer!"

    # Get current V offset stored on the layer (default 0 = no offset applied yet)
    prop_name = f"v_offset_{color_attr.name}"
    current_v = obj.get(prop_name, 0.0)

    # Calculate multipliers
    # V=-80 -> multiplier 0.2, V=0 -> multiplier 1.0, V=+50 -> multiplier 1.5
    current_mult = 1.0 + (current_v / 100.0)
    target_mult = 1.0 + (v_offset / 100.0)

    current_mult = max(0.001, current_mult)  # Avoid division by zero
    target_mult = max(0.0, target_mult)

    # Calculate conversion multiplier (from current state to target state)
    conversion = target_mult / current_mult

    # Apply conversion to all vertex colors
    for i, data in enumerate(color_attr.data):
        c = data.color
        r = min(1.0, max(0.0, c[0] * conversion))
        g = min(1.0, max(0.0, c[1] * conversion))
        b = min(1.0, max(0.0, c[2] * conversion))
        color_attr.data[i].color = (r, g, b, c[3])

    # Store the new V offset
    obj[prop_name] = v_offset

    return True, f"V: {current_v:.0f} → {v_offset:.0f} (x{conversion:.2f})"


def analyze_vertex_colors(obj):
    """Анализировать vertex colors выделенного объекта"""
    if obj is None or obj.type != 'MESH':
        return None

    mesh = obj.data
    if not compat.vcol_list(mesh):
        return None

    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        existing = compat.vcol_list(mesh)
        if existing:
            color_attr = existing[0]

    if color_attr is None:
        return None

    # Collect all colors
    colors = []
    for data in color_attr.data:
        c = data.color
        brightness = (c[0] + c[1] + c[2]) / 3.0
        colors.append({
            'r': c[0], 'g': c[1], 'b': c[2],
            'brightness': brightness
        })

    if not colors:
        return None

    # Calculate statistics
    brightnesses = [c['brightness'] for c in colors]
    min_bright = min(brightnesses)
    max_bright = max(brightnesses)
    avg_bright = sum(brightnesses) / len(brightnesses)

    return {
        'count': len(colors),
        'min_brightness': min_bright,
        'max_brightness': max_bright,
        'avg_brightness': avg_bright,
        'layer_name': color_attr.name
    }


# =============================================================================
# POST-PROCESSING VERTEX COLORS
# =============================================================================

def smooth_vertex_colors(obj, iterations=1, factor=0.5):
    """Сгладить vertex colors между соседними вершинами"""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    if not compat.vcol_list(mesh):
        return False, "No vertex colors found!"

    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        return False, "No active color layer!"

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Build vertex -> loop indices mapping and vertex -> color mapping
    # color_attr.data is per-loop (face corner)
    loop_idx = 0
    vert_loops = {}  # vert_index -> [loop_indices]
    for face in bm.faces:
        for vert in face.verts:
            if vert.index not in vert_loops:
                vert_loops[vert.index] = []
            vert_loops[vert.index].append(loop_idx)
            loop_idx += 1

    for iteration in range(iterations):
        # Collect current per-vertex average colors
        vert_colors = {}
        for vi, loops in vert_loops.items():
            r, g, b = 0.0, 0.0, 0.0
            for li in loops:
                c = color_attr.data[li].color
                r += c[0]
                g += c[1]
                b += c[2]
            n = len(loops)
            vert_colors[vi] = (r / n, g / n, b / n)

        # For each vertex, compute smoothed color from neighbors
        smoothed = {}
        for vert in bm.verts:
            vi = vert.index
            if vi not in vert_colors:
                continue
            neighbors = []
            for edge in vert.link_edges:
                other = edge.other_vert(vert)
                if other.index in vert_colors:
                    neighbors.append(vert_colors[other.index])

            if not neighbors:
                smoothed[vi] = vert_colors[vi]
                continue

            # Average of neighbors
            avg_r = sum(c[0] for c in neighbors) / len(neighbors)
            avg_g = sum(c[1] for c in neighbors) / len(neighbors)
            avg_b = sum(c[2] for c in neighbors) / len(neighbors)

            # Blend: original * (1 - factor) + avg * factor
            orig = vert_colors[vi]
            smoothed[vi] = (
                orig[0] * (1.0 - factor) + avg_r * factor,
                orig[1] * (1.0 - factor) + avg_g * factor,
                orig[2] * (1.0 - factor) + avg_b * factor,
            )

        # Write smoothed colors back to all loops
        for vi, color in smoothed.items():
            for li in vert_loops[vi]:
                c = color_attr.data[li].color
                color_attr.data[li].color = (color[0], color[1], color[2], c[3])

    bm.free()
    return True, f"Smoothed {iterations}x (factor {factor:.2f})"


def adjust_vertex_colors_contrast(obj, contrast=1.0):
    """Применить контраст к vertex colors.
    contrast=1 — без изменений, <1 — меньше контраста, >1 — больше.
    """
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        return False, "No active color layer!"

    # Compute average brightness
    total_r, total_g, total_b = 0.0, 0.0, 0.0
    count = len(color_attr.data)
    if count == 0:
        return True, "No vertex data"
    for data in color_attr.data:
        c = data.color
        total_r += c[0]
        total_g += c[1]
        total_b += c[2]

    avg_r = total_r / count
    avg_g = total_g / count
    avg_b = total_b / count

    # Apply contrast: new = avg + (old - avg) * contrast
    for i, data in enumerate(color_attr.data):
        c = data.color
        r = max(0.0, min(1.0, avg_r + (c[0] - avg_r) * contrast))
        g = max(0.0, min(1.0, avg_g + (c[1] - avg_g) * contrast))
        b = max(0.0, min(1.0, avg_b + (c[2] - avg_b) * contrast))
        color_attr.data[i].color = (r, g, b, c[3])

    return True, f"Contrast: {contrast:.2f}"


def adjust_vertex_colors_brightness(obj, brightness=0.0):
    """Применить яркость к vertex colors. brightness — смещение (-1..+1)."""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        return False, "No active color layer!"

    for i, data in enumerate(color_attr.data):
        c = data.color
        r = max(0.0, min(1.0, c[0] + brightness))
        g = max(0.0, min(1.0, c[1] + brightness))
        b = max(0.0, min(1.0, c[2] + brightness))
        color_attr.data[i].color = (r, g, b, c[3])

    return True, f"Brightness: {brightness:+.2f}"


def adjust_vertex_colors_gamma(obj, gamma=1.0):
    """Применить гамма-коррекцию к vertex colors.
    gamma=1 — без изменений, <1 — светлее, >1 — темнее.
    """
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        return False, "No active color layer!"

    if gamma <= 0:
        return False, "Gamma must be > 0"

    for i, data in enumerate(color_attr.data):
        c = data.color
        r = pow(max(0.0, c[0]), gamma)
        g = pow(max(0.0, c[1]), gamma)
        b = pow(max(0.0, c[2]), gamma)
        color_attr.data[i].color = (min(1.0, r), min(1.0, g), min(1.0, b), c[3])

    return True, f"Gamma: {gamma:.2f}"


# ── Modulate Color presets ──────────────────────────────────────
# Хардкод значений из ванильного timecyc.dat (EXTRASUNNY_LA),
# чтобы пользователю не нужно было ничего настраивать.
# Источник: pcBuildingVS.hlsl + CPostEffects::ColourFilter
# (gta-reversed-modern).
_MODULATE_PRESETS = {
    'DAY': {
        # Midday — цвет ambient_obj. Сила (mix) задаётся слайдером
        # пользователем. Post-fx тинты пока отключены (pf1a/pf2a=0):
        # аддитивные фуллскрин-overlay из движка после AgX-тонмапа
        # Blender'а уходят в whiteout, поэтому в preview не годятся.
        'ambient': (210/255, 194/255, 182/255),
        'pf1':  (66/255, 66/255, 48/255), 'pf1a': 0.0,
        'pf2':  (166/255, 129/255, 60/255), 'pf2a': 0.0,
    },
    'NIGHT': {
        # Midnight — то же без post-fx.
        'ambient': (220/255, 212/255, 130/255),
        'pf1':  (87/255, 87/255, 87/255), 'pf1a': 0.0,
        'pf2':  (60/255, 121/255, 122/255), 'pf2a': 0.0,
    },
}


def _modulate_preset_values(mode, mix=0.15, contrast=0.0, gamma=1.0):
    """Return shader values for the given preset mode (OFF/DAY/NIGHT).

    Returns: (amb_b, amb_factor, pf1_b, pf1_f, pf2_b, pf2_f, contrast, gamma).
    OFF мод обнуляет ambient/post-fx и сбрасывает contrast/gamma в нейтраль."""
    p = _MODULATE_PRESETS.get(mode)
    if p is None:
        return ((0.0, 0.0, 0.0, 0.0), 0.0,
                (0.0, 0.0, 0.0, 0.0), 0.0,
                (0.0, 0.0, 0.0, 0.0), 0.0,
                0.0, 1.0)
    return ((p['ambient'][0], p['ambient'][1], p['ambient'][2], 0.0), mix,
            (p['pf1'][0],     p['pf1'][1],     p['pf1'][2],     0.0), p['pf1a'],
            (p['pf2'][0],     p['pf2'][1],     p['pf2'][2],     0.0), p['pf2a'],
            contrast, gamma)


def setup_prelight_preview(obj, enable=True):
    """Setup materials to show vertex colors multiplied with textures in Material Preview

    Adds a Vertex Color node and MixRGB (Multiply) between texture and shader.
    """
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    if not compat.vcol_list(mesh):
        return False, "No vertex colors on object!"

    # Get active color attribute name
    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        color_attr = compat.vcol_list(mesh)[0]
    color_name = color_attr.name

    # Read «Modulate Color» preview state from scene (если scene доступна)
    # — ambient_obj × surfAmbient добавляется к vertex color, имитируя
    # формулу из ванильного шейдера зданий SA (см. euryopa
    # pcBuildingVS.hlsl: OUT.Color.rgb += ambient * surfAmb).
    scene = getattr(bpy.context, 'scene', None)
    mode = getattr(scene, 'gtatools_modulate_mode', 'OFF') if scene else 'OFF'
    mix = float(getattr(scene, 'gtatools_modulate_mix', 0.15)) if scene else 0.15
    contrast = float(getattr(scene, 'gtatools_modulate_contrast', 0.0)) if scene else 0.0
    gamma = float(getattr(scene, 'gtatools_modulate_gamma', 1.0)) if scene else 1.0
    (amb_b, amb_factor, pf1_b, pf1_f, pf2_b, pf2_f,
     bc_contrast, gm_gamma) = _modulate_preset_values(mode, mix, contrast, gamma)

    modified_count = 0

    for mat_slot in obj.material_slots:
        mat = mat_slot.material
        if not mat or not mat.use_nodes:
            continue

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Find existing prelight nodes
        vc_node = nodes.get("Prelight_VertexColor")
        mix_node = nodes.get("Prelight_Mix")
        bright_node = nodes.get("Prelight_Bright")
        amb_node = nodes.get("Prelight_Ambient")
        pf1_node = nodes.get("Prelight_PostFx1")
        pf2_node = nodes.get("Prelight_PostFx2")
        bc_node = nodes.get("Prelight_BrightContrast")
        gm_node = nodes.get("Prelight_Gamma")

        if enable:
            # Find the Principled BSDF and texture connected to Base Color
            principled = None
            tex_node = None
            original_link = None

            for node in nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled = node
                    break

            if not principled:
                continue

            # Get what's connected to Base Color
            base_color_input = principled.inputs.get('Base Color')
            if base_color_input and base_color_input.is_linked:
                original_link = base_color_input.links[0]
                tex_node = original_link.from_node
                tex_output = original_link.from_socket

            # If already has prelight setup - just update values
            if mix_node and vc_node and bright_node:
                # Set color attribute name (compatible with both node types)
                if hasattr(vc_node, 'layer_name'):
                    vc_node.layer_name = color_name
                elif hasattr(vc_node, 'attribute_name'):
                    vc_node.attribute_name = color_name
                bright_node.inputs[compat.MIX_INPUT_B].default_value = (0.0, 0.0, 0.0, 0.0)
                # Insert Prelight_Ambient if missing (older preview without it)
                if amb_node is None:
                    amb_node = nodes.new(compat.MIX_NODE_TYPE)
                    amb_node.name = "Prelight_Ambient"
                    amb_node.label = "Ambient (Modulate)"
                    compat.setup_mix_rgba_node(amb_node, blend='ADD')
                    amb_node.location = (
                        principled.location.x - 280, principled.location.y - 100)
                    # Splice between bright_node and mix_node B
                    for lnk in list(mix_node.inputs[compat.MIX_INPUT_B].links):
                        links.remove(lnk)
                    links.new(bright_node.outputs[compat.MIX_OUTPUT_RESULT], amb_node.inputs[compat.MIX_INPUT_A])
                    links.new(amb_node.outputs[compat.MIX_OUTPUT_RESULT], mix_node.inputs[compat.MIX_INPUT_B])
                amb_node.inputs[compat.MIX_INPUT_FACTOR].default_value = amb_factor
                amb_node.inputs[compat.MIX_INPUT_B].default_value = amb_b
                # Создать недостающие ноды: PostFx1, PostFx2, BrightContrast, Gamma
                if pf1_node is None:
                    pf1_node = nodes.new(compat.MIX_NODE_TYPE)
                    pf1_node.name = "Prelight_PostFx1"
                    pf1_node.label = "PostFx1 (Add)"
                    compat.setup_mix_rgba_node(pf1_node, blend='ADD')
                    pf1_node.location = (
                        principled.location.x - 200, principled.location.y - 50)
                if pf2_node is None:
                    pf2_node = nodes.new(compat.MIX_NODE_TYPE)
                    pf2_node.name = "Prelight_PostFx2"
                    pf2_node.label = "PostFx2 (Add)"
                    compat.setup_mix_rgba_node(pf2_node, blend='ADD')
                    pf2_node.location = (
                        principled.location.x - 150, principled.location.y - 50)
                if bc_node is None:
                    bc_node = nodes.new('ShaderNodeBrightContrast')
                    bc_node.name = "Prelight_BrightContrast"
                    bc_node.label = "Contrast"
                    bc_node.location = (
                        principled.location.x - 100, principled.location.y - 50)
                    bc_node.inputs['Bright'].default_value = 0.0
                if gm_node is None:
                    gm_node = nodes.new('ShaderNodeGamma')
                    gm_node.name = "Prelight_Gamma"
                    gm_node.label = "Gamma"
                    gm_node.location = (
                        principled.location.x - 50, principled.location.y - 50)
                # Перевязать цепочку: Mix → PostFx1 → PostFx2 → BrightContrast → Gamma → Base Color
                for lnk in list(base_color_input.links):
                    links.remove(lnk)
                for lnk in list(pf1_node.inputs[compat.MIX_INPUT_A].links):
                    links.remove(lnk)
                for lnk in list(pf2_node.inputs[compat.MIX_INPUT_A].links):
                    links.remove(lnk)
                for lnk in list(bc_node.inputs['Color'].links):
                    links.remove(lnk)
                for lnk in list(gm_node.inputs['Color'].links):
                    links.remove(lnk)
                links.new(mix_node.outputs[compat.MIX_OUTPUT_RESULT], pf1_node.inputs[compat.MIX_INPUT_A])
                links.new(pf1_node.outputs[compat.MIX_OUTPUT_RESULT], pf2_node.inputs[compat.MIX_INPUT_A])
                links.new(pf2_node.outputs[compat.MIX_OUTPUT_RESULT], bc_node.inputs['Color'])
                links.new(bc_node.outputs['Color'], gm_node.inputs['Color'])
                links.new(gm_node.outputs['Color'], base_color_input)
                pf1_node.inputs[compat.MIX_INPUT_FACTOR].default_value = pf1_f
                pf1_node.inputs[compat.MIX_INPUT_B].default_value = pf1_b
                pf2_node.inputs[compat.MIX_INPUT_FACTOR].default_value = pf2_f
                pf2_node.inputs[compat.MIX_INPUT_B].default_value = pf2_b
                bc_node.inputs['Contrast'].default_value = bc_contrast
                gm_node.inputs['Gamma'].default_value = gm_gamma
                continue

            # Create Color Attribute node (compatible 4.4+)
            if not vc_node:
                if bpy.app.version >= (4, 0, 0):
                    vc_node = nodes.new('ShaderNodeAttribute')
                    vc_node.attribute_type = 'GEOMETRY'
                    vc_node.attribute_name = color_name
                else:
                    vc_node = nodes.new('ShaderNodeVertexColor')
                    vc_node.layer_name = color_name
                vc_node.name = "Prelight_VertexColor"
                vc_node.label = "Prelight"
                vc_node.location = (principled.location.x - 500, principled.location.y - 200)
            else:
                if hasattr(vc_node, 'layer_name'):
                    vc_node.layer_name = color_name
                elif hasattr(vc_node, 'attribute_name'):
                    vc_node.attribute_name = color_name

            # Create Brightness node (+ brightness offset)
            if not bright_node:
                bright_node = nodes.new(compat.MIX_NODE_TYPE)
                bright_node.name = "Prelight_Bright"
                bright_node.label = "Brightness"
                compat.setup_mix_rgba_node(bright_node, blend='ADD')
                bright_node.location = (principled.location.x - 350, principled.location.y - 200)
                bright_node.inputs[compat.MIX_INPUT_FACTOR].default_value = 1.0
            bright_node.inputs[compat.MIX_INPUT_B].default_value = (0.0, 0.0, 0.0, 0.0)

            # Create Ambient (Modulate) node — adds ambient_obj × surfAmb
            # to vertex color, mirroring ванильный SA-шейдер зданий
            # (см. euryopa pcBuildingVS.hlsl: Color.rgb += ambient*surfAmb).
            # B input управляется глобальной настройкой scene; default 0.
            if not amb_node:
                amb_node = nodes.new(compat.MIX_NODE_TYPE)
                amb_node.name = "Prelight_Ambient"
                amb_node.label = "Ambient (Modulate)"
                compat.setup_mix_rgba_node(amb_node, blend='ADD')
                amb_node.location = (
                    principled.location.x - 280, principled.location.y - 100)
            amb_node.inputs[compat.MIX_INPUT_FACTOR].default_value = amb_factor
            amb_node.inputs[compat.MIX_INPUT_B].default_value = amb_b

            # Create Mix node (Multiply with texture)
            if not mix_node:
                mix_node = nodes.new(compat.MIX_NODE_TYPE)
                mix_node.name = "Prelight_Mix"
                mix_node.label = "Prelight Multiply"
                compat.setup_mix_rgba_node(mix_node, blend='MULTIPLY')
                mix_node.location = (principled.location.x - 200, principled.location.y)
                mix_node.inputs[compat.MIX_INPUT_FACTOR].default_value = 1.0

            # ── PostFx1 + PostFx2 — точная игровая формула из
            # CPostEffects::ColourFilter (gta-reversed-modern):
            #   final += postfx1.rgb*alpha + postfx2.rgb*alpha
            # Два аддитивных тинта с настраиваемой alpha. По дефолту
            # alpha=0 для DAY/NIGHT (Blender'овский AgX-тонмап
            # пересвечивает их), цветовое значение оставлено для
            # будущей точной настройки.
            if not pf1_node:
                pf1_node = nodes.new(compat.MIX_NODE_TYPE)
                pf1_node.name = "Prelight_PostFx1"
                pf1_node.label = "PostFx1 (Add)"
                compat.setup_mix_rgba_node(pf1_node, blend='ADD')
                pf1_node.location = (principled.location.x - 200, principled.location.y - 50)
            pf1_node.inputs[compat.MIX_INPUT_FACTOR].default_value = pf1_f
            pf1_node.inputs[compat.MIX_INPUT_B].default_value = pf1_b

            if not pf2_node:
                pf2_node = nodes.new(compat.MIX_NODE_TYPE)
                pf2_node.name = "Prelight_PostFx2"
                pf2_node.label = "PostFx2 (Add)"
                compat.setup_mix_rgba_node(pf2_node, blend='ADD')
                pf2_node.location = (principled.location.x - 150, principled.location.y - 50)
            pf2_node.inputs[compat.MIX_INPUT_FACTOR].default_value = pf2_f
            pf2_node.inputs[compat.MIX_INPUT_B].default_value = pf2_b

            # ── BrightContrast + Gamma — color-grading на финальный результат
            if not bc_node:
                bc_node = nodes.new('ShaderNodeBrightContrast')
                bc_node.name = "Prelight_BrightContrast"
                bc_node.label = "Contrast"
                bc_node.location = (principled.location.x - 100, principled.location.y - 50)
            bc_node.inputs['Bright'].default_value = 0.0
            bc_node.inputs['Contrast'].default_value = bc_contrast

            if not gm_node:
                gm_node = nodes.new('ShaderNodeGamma')
                gm_node.name = "Prelight_Gamma"
                gm_node.label = "Gamma"
                gm_node.location = (principled.location.x - 50, principled.location.y - 50)
            gm_node.inputs['Gamma'].default_value = gm_gamma

            # Connect nodes
            if tex_node and original_link:
                # Texture -> Mix A
                links.new(tex_output, mix_node.inputs[compat.MIX_INPUT_A])
            else:
                # No texture - use white
                mix_node.inputs[compat.MIX_INPUT_A].default_value = (1, 1, 1, 1)

            # Vertex Color -> Bright A
            links.new(vc_node.outputs['Color'], bright_node.inputs[compat.MIX_INPUT_A])

            # Bright Result -> Ambient A
            links.new(bright_node.outputs[compat.MIX_OUTPUT_RESULT], amb_node.inputs[compat.MIX_INPUT_A])

            # Ambient Result -> Mix B
            links.new(amb_node.outputs[compat.MIX_OUTPUT_RESULT], mix_node.inputs[compat.MIX_INPUT_B])

            # Mix -> PostFx1 -> PostFx2 -> BrightContrast -> Gamma -> Base Color
            links.new(mix_node.outputs[compat.MIX_OUTPUT_RESULT], pf1_node.inputs[compat.MIX_INPUT_A])
            links.new(pf1_node.outputs[compat.MIX_OUTPUT_RESULT], pf2_node.inputs[compat.MIX_INPUT_A])
            links.new(pf2_node.outputs[compat.MIX_OUTPUT_RESULT], bc_node.inputs['Color'])
            links.new(bc_node.outputs['Color'], gm_node.inputs['Color'])
            links.new(gm_node.outputs['Color'], base_color_input)

            # ── Alpha: vertex color alpha → Principled Alpha ──
            # Only if active color attribute actually has any alpha < 1.0 painted
            has_alpha_painted = False
            active_attr = compat.vcol_get(mesh, color_name)
            if active_attr and compat.vcol_data_type(active_attr) in ('BYTE_COLOR', 'FLOAT_COLOR'):
                for d in active_attr.data:
                    if d.color[3] < 0.999:
                        has_alpha_painted = True
                        break

            alpha_input = principled.inputs.get('Alpha')
            if has_alpha_painted and alpha_input and 'Alpha' in vc_node.outputs:
                # Save original blend_method
                if 'prelight_orig_blend' not in mat:
                    mat['prelight_orig_blend'] = getattr(mat, 'blend_method', 'OPAQUE')
                if hasattr(mat, 'blend_method'):
                    mat.blend_method = 'HASHED'

                if alpha_input.is_linked:
                    # Texture alpha already connected — insert Multiply node
                    orig_alpha_socket = alpha_input.links[0].from_socket
                    alpha_mult = nodes.get("Prelight_AlphaMult")
                    if not alpha_mult:
                        alpha_mult = nodes.new('ShaderNodeMath')
                        alpha_mult.name = "Prelight_AlphaMult"
                        alpha_mult.label = "Prelight Alpha Mult"
                        alpha_mult.operation = 'MULTIPLY'
                        alpha_mult.location = (principled.location.x - 200, principled.location.y - 350)
                    # Disconnect old alpha link
                    for lnk in list(alpha_input.links):
                        links.remove(lnk)
                    # texture_alpha × vc_alpha → Principled Alpha
                    links.new(orig_alpha_socket, alpha_mult.inputs[0])
                    links.new(vc_node.outputs['Alpha'], alpha_mult.inputs[1])
                    links.new(alpha_mult.outputs[0], alpha_input)
                    mat['prelight_alpha_mode'] = 'mult'
                else:
                    # No existing alpha — connect vc alpha directly
                    links.new(vc_node.outputs['Alpha'], alpha_input)
                    mat['prelight_alpha_mode'] = 'direct'

            modified_count += 1

        else:
            # Disable - remove prelight nodes and restore original connection
            if mix_node:
                # Find what was connected to Mix A input (original texture or Lightmap_Mix)
                mix_a_input = mix_node.inputs.get('A')
                original_source = None
                original_socket = None

                if mix_a_input and mix_a_input.is_linked:
                    original_source = mix_a_input.links[0].from_node
                    original_socket = mix_a_input.links[0].from_socket

                # Find Principled BSDF
                principled = None
                for node in nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        principled = node
                        break

                if principled:
                    base_color_input = principled.inputs.get('Base Color')
                    # Restore connection - может быть Lightmap_Mix или оригинальная текстура
                    if original_source and original_socket:
                        links.new(original_socket, base_color_input)

                    # ── Alpha cleanup ──
                    alpha_mode = mat.get('prelight_alpha_mode')
                    alpha_input = principled.inputs.get('Alpha')
                    alpha_mult = nodes.get("Prelight_AlphaMult")

                    if alpha_mode == 'mult' and alpha_mult and alpha_input:
                        # Restore original texture alpha → Principled Alpha
                        orig_socket = None
                        if alpha_mult.inputs[0].is_linked:
                            orig_socket = alpha_mult.inputs[0].links[0].from_socket
                        # Disconnect mult output
                        for lnk in list(alpha_input.links):
                            links.remove(lnk)
                        if orig_socket:
                            links.new(orig_socket, alpha_input)
                        nodes.remove(alpha_mult)
                    elif alpha_mode == 'direct' and alpha_input:
                        # Disconnect VC alpha, reset to 1.0
                        for lnk in list(alpha_input.links):
                            if lnk.from_node == vc_node:
                                links.remove(lnk)
                        alpha_input.default_value = 1.0

                    if 'prelight_alpha_mode' in mat:
                        del mat['prelight_alpha_mode']

                    # Restore blend_method
                    if 'prelight_orig_blend' in mat:
                        if hasattr(mat, 'blend_method'):
                            try:
                                mat.blend_method = mat['prelight_orig_blend']
                            except Exception:
                                mat.blend_method = 'OPAQUE'
                        del mat['prelight_orig_blend']

                # Remove prelight nodes
                nodes.remove(mix_node)
                modified_count += 1

            if gm_node:
                nodes.remove(gm_node)

            if bc_node:
                nodes.remove(bc_node)

            if pf2_node:
                nodes.remove(pf2_node)

            if pf1_node:
                nodes.remove(pf1_node)

            if amb_node:
                nodes.remove(amb_node)

            if bright_node:
                nodes.remove(bright_node)

            if vc_node:
                nodes.remove(vc_node)

    if enable:
        return True, f"Prelight preview enabled on {modified_count} materials"
    else:
        return True, f"Prelight preview disabled on {modified_count} materials"


def apply_modulate_preview(scene=None):
    """Push Modulate Color preview values into every material that has a
    Prelight_Ambient node.

    Сценарий: пользователь крутит slider/color-picker → надо
    мгновенно обновить ambient во всех уже настроенных материалах
    без переотрисовки графа. Дешевле чем повторно вызывать
    setup_prelight_preview на каждом меше.

    Returns: (count, color_used) для отчёта в UI/коллбэке.
    """
    if scene is None:
        scene = getattr(bpy.context, 'scene', None)
    if scene is None:
        return 0, (0.0, 0.0, 0.0)

    mode = getattr(scene, 'gtatools_modulate_mode', 'OFF')
    mix = float(getattr(scene, 'gtatools_modulate_mix', 0.15))
    contrast = float(getattr(scene, 'gtatools_modulate_contrast', 0.0))
    gamma = float(getattr(scene, 'gtatools_modulate_gamma', 1.0))
    (amb_b, amb_factor, pf1_b, pf1_f, pf2_b, pf2_f,
     bc_contrast, gm_gamma) = _modulate_preset_values(mode, mix, contrast, gamma)

    count = 0
    for mat in bpy.data.materials:
        if not mat or not getattr(mat, 'use_nodes', False):
            continue
        nt = mat.node_tree
        if nt is None:
            continue
        bright_n = nt.nodes.get("Prelight_Bright")
        mix_n = nt.nodes.get("Prelight_Mix")
        # No prelight setup at all → пропускаем
        if not (bright_n and mix_n):
            continue
        amb_n = nt.nodes.get("Prelight_Ambient")
        pf1_n = nt.nodes.get("Prelight_PostFx1")
        pf2_n = nt.nodes.get("Prelight_PostFx2")
        bc_n = nt.nodes.get("Prelight_BrightContrast")
        gm_n = nt.nodes.get("Prelight_Gamma")
        # Find Principled BSDF for inserting post-fx/contrast/gamma nodes
        principled = None
        for n in nt.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                principled = n
                break

        # Lazy upgrade: вставить Prelight_Ambient если отсутствует.
        if amb_n is None:
            amb_n = nt.nodes.new(compat.MIX_NODE_TYPE)
            amb_n.name = "Prelight_Ambient"
            amb_n.label = "Ambient (Modulate)"
            compat.setup_mix_rgba_node(amb_n, blend='ADD')
            amb_n.location = (mix_n.location.x - 80, mix_n.location.y - 100)
            for lnk in list(mix_n.inputs[compat.MIX_INPUT_B].links):
                nt.links.remove(lnk)
            nt.links.new(bright_n.outputs[compat.MIX_OUTPUT_RESULT], amb_n.inputs[compat.MIX_INPUT_A])
            nt.links.new(amb_n.outputs[compat.MIX_OUTPUT_RESULT], mix_n.inputs[compat.MIX_INPUT_B])

        # Lazy upgrade: вставить PostFx1+PostFx2+BrightContrast+Gamma
        # после mix_n, перед Principled.Base Color если их нет.
        need_chain = principled is not None and (
            pf1_n is None or pf2_n is None or bc_n is None or gm_n is None)
        if need_chain:
            base_input = principled.inputs.get('Base Color')
            if base_input is not None:
                if pf1_n is None:
                    pf1_n = nt.nodes.new(compat.MIX_NODE_TYPE)
                    pf1_n.name = "Prelight_PostFx1"
                    pf1_n.label = "PostFx1 (Add)"
                    compat.setup_mix_rgba_node(pf1_n, blend='ADD')
                    pf1_n.location = (
                        principled.location.x - 200, principled.location.y - 50)
                if pf2_n is None:
                    pf2_n = nt.nodes.new(compat.MIX_NODE_TYPE)
                    pf2_n.name = "Prelight_PostFx2"
                    pf2_n.label = "PostFx2 (Add)"
                    compat.setup_mix_rgba_node(pf2_n, blend='ADD')
                    pf2_n.location = (
                        principled.location.x - 150, principled.location.y - 50)
                if bc_n is None:
                    bc_n = nt.nodes.new('ShaderNodeBrightContrast')
                    bc_n.name = "Prelight_BrightContrast"
                    bc_n.label = "Contrast"
                    bc_n.location = (
                        principled.location.x - 100, principled.location.y - 50)
                    bc_n.inputs['Bright'].default_value = 0.0
                if gm_n is None:
                    gm_n = nt.nodes.new('ShaderNodeGamma')
                    gm_n.name = "Prelight_Gamma"
                    gm_n.label = "Gamma"
                    gm_n.location = (
                        principled.location.x - 50, principled.location.y - 50)
                # Перевязать: mix → pf1 → pf2 → bc → gm → Base Color
                for lnk in list(base_input.links):
                    nt.links.remove(lnk)
                for lnk in list(pf1_n.inputs[compat.MIX_INPUT_A].links):
                    nt.links.remove(lnk)
                for lnk in list(pf2_n.inputs[compat.MIX_INPUT_A].links):
                    nt.links.remove(lnk)
                for lnk in list(bc_n.inputs['Color'].links):
                    nt.links.remove(lnk)
                for lnk in list(gm_n.inputs['Color'].links):
                    nt.links.remove(lnk)
                nt.links.new(mix_n.outputs[compat.MIX_OUTPUT_RESULT], pf1_n.inputs[compat.MIX_INPUT_A])
                nt.links.new(pf1_n.outputs[compat.MIX_OUTPUT_RESULT], pf2_n.inputs[compat.MIX_INPUT_A])
                nt.links.new(pf2_n.outputs[compat.MIX_OUTPUT_RESULT], bc_n.inputs['Color'])
                nt.links.new(bc_n.outputs['Color'], gm_n.inputs['Color'])
                nt.links.new(gm_n.outputs['Color'], base_input)

        try:
            amb_n.inputs[compat.MIX_INPUT_FACTOR].default_value = amb_factor
            amb_n.inputs[compat.MIX_INPUT_B].default_value = amb_b
            if pf1_n is not None:
                pf1_n.inputs[compat.MIX_INPUT_FACTOR].default_value = pf1_f
                pf1_n.inputs[compat.MIX_INPUT_B].default_value = pf1_b
            if pf2_n is not None:
                pf2_n.inputs[compat.MIX_INPUT_FACTOR].default_value = pf2_f
                pf2_n.inputs[compat.MIX_INPUT_B].default_value = pf2_b
            if bc_n is not None:
                bc_n.inputs['Contrast'].default_value = bc_contrast
            if gm_n is not None:
                gm_n.inputs['Gamma'].default_value = gm_gamma
            count += 1
        except (KeyError, AttributeError, RuntimeError):
            continue
    return count, amb_b[:3]


def fill_selected_faces(obj, color):
    """Залить выделенные грани цветом в режиме vertex paint"""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    if not compat.vcol_list(mesh):
        return False, "No vertex colors found!"

    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        return False, "No active color layer!"

    # Get selected faces from bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]

    if not selected_faces:
        bm.free()
        return False, "No faces selected!"

    # Get selected face indices
    selected_indices = set(f.index for f in selected_faces)
    bm.free()

    # Fill selected faces with color
    filled_count = 0
    for poly in mesh.polygons:
        if poly.index in selected_indices:
            for loop_idx in poly.loop_indices:
                color_attr.data[loop_idx].color = (color[0], color[1], color[2], 1.0)
            filled_count += 1

    return True, f"Filled {filled_count} faces"


# =============================================================================
# НОВАЯ АРХИТЕКТУРА СЛОЁВ
# =============================================================================
# Формула: ИТОГ = (База ИЛИ Fill) + Σ Scatter
#
# База — исходный цвет вершин, неизменный
# Fill — заменяет базу локально (не складывается)
# Scatter — дельта, всегда прибавляется
# =============================================================================

# Исходные цвета вершин (сохраняются при первой операции, никогда не меняются)
# Structure: {obj_name: {loop_idx: (r,g,b,a), ...}}
_base_colors = {}

# Fill слои - заменяют базу для своих loops
# Structure: {obj_name: {loop_idx: (r,g,b,a), ...}}
_fill_layers = {}

# Scatter слои - дельты которые прибавляются
# Structure: {obj_name: {color_tuple: {level_num: {loop_idx: (dr,dg,db,da), ...}, ...}, ...}}
_scatter_layers = {}


def ensure_base_colors(obj):
    """Сохранить базовые цвета если ещё не сохранены"""
    if obj is None or obj.type != 'MESH':
        return False

    obj_key = obj.name
    if obj_key in _base_colors:
        return True  # Уже сохранены

    mesh = obj.data
    if not compat.vcol_active(mesh):
        return False

    color_attr = compat.vcol_active(mesh)

    _base_colors[obj_key] = {}
    for loop_idx in range(len(color_attr.data)):
        c = color_attr.data[loop_idx].color
        _base_colors[obj_key][loop_idx] = (c[0], c[1], c[2], c[3])

    return True


def recalculate_loop_color(obj_key, loop_idx):
    """Пересчитать цвет одного loop: ИТОГ = (База ИЛИ Fill) + Σ Scatter"""
    # Получаем базу
    if obj_key not in _base_colors or loop_idx not in _base_colors[obj_key]:
        return None

    base = _base_colors[obj_key][loop_idx]

    # Проверяем есть ли Fill для этого loop
    fill = None
    if obj_key in _fill_layers and loop_idx in _fill_layers[obj_key]:
        fill = _fill_layers[obj_key][loop_idx]

    # Основа = Fill если есть, иначе База
    r, g, b, a = fill if fill else base

    # Добавляем все Scatter дельты
    if obj_key in _scatter_layers:
        for color_tuple, levels in _scatter_layers[obj_key].items():
            for level_num, deltas in levels.items():
                if loop_idx in deltas:
                    dr, dg, db, da = deltas[loop_idx]
                    r += dr
                    g += dg
                    b += db

    # Clamp to [0, 1]
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    a = max(0.0, min(1.0, a))

    return (r, g, b, a)


def recalculate_colors(obj, loop_indices=None):
    """Пересчитать цвета для указанных loops (или всех если не указано)"""
    if obj is None or obj.type != 'MESH':
        return False

    obj_key = obj.name
    mesh = obj.data

    if not compat.vcol_active(mesh):
        return False

    color_attr = compat.vcol_active(mesh)

    # Если loops не указаны - пересчитать все
    if loop_indices is None:
        loop_indices = range(len(color_attr.data))

    for loop_idx in loop_indices:
        new_color = recalculate_loop_color(obj_key, loop_idx)
        if new_color and loop_idx < len(color_attr.data):
            color_attr.data[loop_idx].color = new_color

    return True


def add_fill_layer(obj, color, loop_indices):
    """Добавить Fill слой для указанных loops"""
    if obj is None:
        return False

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    # Сохраняем базу если ещё не сохранена
    ensure_base_colors(obj)

    # Инициализируем хранилище
    if obj_key not in _fill_layers:
        _fill_layers[obj_key] = {}

    # Записываем Fill цвет для каждого loop
    for loop_idx in loop_indices:
        _fill_layers[obj_key][loop_idx] = (color[0], color[1], color[2], 1.0)

    # Добавляем в UI список если новый цвет
    color_exists = False
    for item in obj.gtatools_fill_colors:
        existing = (round(item.color[0], 3), round(item.color[1], 3), round(item.color[2], 3))
        if existing == color_tuple:
            color_exists = True
            break

    if not color_exists:
        new_item = obj.gtatools_fill_colors.add()
        new_item.color = color_tuple

    return True


def add_scatter_layer(obj, color, deltas):
    """Добавить Scatter слой (дельты) для цвета
    deltas = {loop_idx: (dr, dg, db, da), ...}
    """
    if obj is None or not deltas:
        return -1

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    # Сохраняем базу если ещё не сохранена
    ensure_base_colors(obj)

    # Инициализируем хранилище
    if obj_key not in _scatter_layers:
        _scatter_layers[obj_key] = {}
    if color_tuple not in _scatter_layers[obj_key]:
        _scatter_layers[obj_key][color_tuple] = {}

    # Находим следующий номер уровня
    existing_levels = list(_scatter_layers[obj_key][color_tuple].keys())
    next_level = max(existing_levels) + 1 if existing_levels else 1

    # Сохраняем дельты
    _scatter_layers[obj_key][color_tuple][next_level] = deltas

    return next_level


def get_scatter_levels(obj, color):
    """Получить список уровней scatter для цвета"""
    if obj is None:
        return []

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    if obj_key not in _scatter_layers:
        return []
    if color_tuple not in _scatter_layers[obj_key]:
        return []

    return sorted(_scatter_layers[obj_key][color_tuple].keys())


def remove_scatter_layer(obj, color, level):
    """Удалить Scatter слой и пересчитать цвета"""
    if obj is None:
        return False, "No object"

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    if obj_key not in _scatter_layers:
        return False, "No scatter layers"
    if color_tuple not in _scatter_layers[obj_key]:
        return False, "No scatter layers for this color"
    if level not in _scatter_layers[obj_key][color_tuple]:
        return False, f"Level {level} not found"

    # Получаем loops которые были затронуты этим слоем
    affected_loops = list(_scatter_layers[obj_key][color_tuple][level].keys())

    # Удаляем слой
    del _scatter_layers[obj_key][color_tuple][level]

    # Пересчитываем цвета для затронутых loops
    recalculate_colors(obj, affected_loops)

    return True, f"Level {level} removed"


def clear_scatter_layers(obj, color):
    """Удалить все Scatter слои для цвета и пересчитать"""
    if obj is None:
        return False, "No object"

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    if obj_key not in _scatter_layers:
        return False, "No scatter layers"
    if color_tuple not in _scatter_layers[obj_key]:
        return False, "No scatter layers for this color"

    # Собираем все затронутые loops
    affected_loops = set()
    for level_data in _scatter_layers[obj_key][color_tuple].values():
        affected_loops.update(level_data.keys())

    # Удаляем все слои
    _scatter_layers[obj_key][color_tuple] = {}

    # Пересчитываем цвета
    recalculate_colors(obj, affected_loops)

    return True, "All scatter levels removed"


def remove_fill_color(obj, color):
    """Удалить Fill цвет и все его Scatter слои, пересчитать"""
    if obj is None:
        return False, "No object"

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    affected_loops = set()

    # Собираем loops из Fill
    if obj_key in _fill_layers:
        for loop_idx, fill_color in list(_fill_layers[obj_key].items()):
            fill_tuple = (round(fill_color[0], 3), round(fill_color[1], 3), round(fill_color[2], 3))
            if fill_tuple == color_tuple:
                affected_loops.add(loop_idx)
                del _fill_layers[obj_key][loop_idx]

    # Собираем loops из Scatter и удаляем
    if obj_key in _scatter_layers:
        if color_tuple in _scatter_layers[obj_key]:
            for level_data in _scatter_layers[obj_key][color_tuple].values():
                affected_loops.update(level_data.keys())
            del _scatter_layers[obj_key][color_tuple]

    # Пересчитываем цвета
    if affected_loops:
        recalculate_colors(obj, affected_loops)

    return True, "Fill color removed"


def remove_fill_color_by_index(obj, index):
    """Удалить цвет из списка по индексу"""
    if obj is None:
        return False, "No object"

    if not (0 <= index < len(obj.gtatools_fill_colors)):
        return False, "Invalid index"

    # Получаем цвет
    color_item = obj.gtatools_fill_colors[index]
    color_tuple = (color_item.color[0], color_item.color[1], color_item.color[2])

    # Удаляем цвет и пересчитываем
    remove_fill_color(obj, color_tuple)

    # Удаляем из UI списка
    obj.gtatools_fill_colors.remove(index)

    return True, "Color removed"


def get_selected_faces_color(obj):
    """Получить Fill цвет выделенных полигонов"""
    if obj is None or obj.type != 'MESH':
        return None

    mesh = obj.data

    # Получаем выделенные полигоны
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]
    if not selected_faces:
        bm.free()
        return None

    selected_face_indices = set(f.index for f in selected_faces)
    bm.free()

    # Получаем loops выделенных полигонов
    selected_loops = set()
    for poly in mesh.polygons:
        if poly.index in selected_face_indices:
            for loop_idx in poly.loop_indices:
                selected_loops.add(loop_idx)

    if not selected_loops:
        return None

    obj_key = obj.name

    # Проверяем какой Fill цвет есть у этих loops
    if obj_key in _fill_layers:
        for loop_idx in selected_loops:
            if loop_idx in _fill_layers[obj_key]:
                fill_color = _fill_layers[obj_key][loop_idx]
                return (round(fill_color[0], 3), round(fill_color[1], 3), round(fill_color[2], 3))

    # Fallback: по текущему цвету
    color_attr = compat.vcol_active(mesh)
    if color_attr is not None:
        first_loop = next(iter(selected_loops))
        c = color_attr.data[first_loop].color
        color_tuple = (round(c[0], 3), round(c[1], 3), round(c[2], 3))

        # Проверяем есть ли в списке Fill цветов
        for item in obj.gtatools_fill_colors:
            existing = (round(item.color[0], 3), round(item.color[1], 3), round(item.color[2], 3))
            if existing == color_tuple:
                return color_tuple

    return None


def fill_selected_faces_with_backup(obj, color):
    """Залить выделенные грани цветом через систему слоёв"""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    # Запоминаем режим и переключаемся в Object если нужно
    original_mode = obj.mode
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    mesh = obj.data
    if not compat.vcol_list(mesh):
        return False, "No vertex colors found!"

    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        return False, "No active color layer!"

    # Get selected faces from bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]

    if not selected_faces:
        bm.free()
        return False, "No faces selected!"

    selected_indices = set(f.index for f in selected_faces)
    bm.free()

    # Собираем loop indices выделенных полигонов
    loop_indices = []
    for poly in mesh.polygons:
        if poly.index in selected_indices:
            for loop_idx in poly.loop_indices:
                loop_indices.append(loop_idx)

    filled_count = len(selected_indices)

    # Добавляем Fill слой (сохраняет базу автоматически)
    add_fill_layer(obj, color, loop_indices)

    # Применяем цвет напрямую (быстрее чем пересчёт)
    for loop_idx in loop_indices:
        color_attr.data[loop_idx].color = (color[0], color[1], color[2], 1.0)

    # Возвращаемся в исходный режим
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

    return True, f"Filled {filled_count} faces"


def restore_filled_faces(obj):
    """Восстановить все цвета к базовым (удалить fill и scatter слои)"""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    obj_key = obj.name

    # Проверяем есть ли база
    if obj_key not in _base_colors:
        return False, "No base colors saved!"

    # Запоминаем режим и переключаемся в Object если нужно
    original_mode = obj.mode
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    mesh = obj.data
    if not compat.vcol_list(mesh):
        return False, "No vertex colors found!"

    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        return False, "No active color layer!"

    # Очищаем fill слои
    if obj_key in _fill_layers:
        _fill_layers[obj_key] = {}

    # Очищаем scatter слои
    if obj_key in _scatter_layers:
        _scatter_layers[obj_key] = {}

    # Восстанавливаем из базы
    base = _base_colors[obj_key]
    restored_count = 0
    for loop_idx, base_color in base.items():
        if loop_idx < len(color_attr.data):
            color_attr.data[loop_idx].color = base_color
            restored_count += 1

    # Удаляем все цвета из UI
    obj.gtatools_fill_colors.clear()

    # Возвращаемся в исходный режим
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

    return True, f"Restored {restored_count} vertices to base"


def scatter_light_from_selected(obj, intensity=1.0, falloff=2.0, iterations=3, radius=0.0):
    """Scatter light from selected faces to vertices with distance-based falloff

    Paints vertices based on distance from light source faces.
    Creates smooth gradient - closer vertices are brighter.
    """
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!", []

    # Запоминаем режим и переключаемся в Object если нужно
    original_mode = obj.mode
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    mesh = obj.data
    if not compat.vcol_list(mesh):
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return False, "No vertex colors found!", []

    color_attr = compat.vcol_active(mesh)
    if color_attr is None:
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return False, "No active color layer!", []

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]

    if not selected_faces:
        bm.free()
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return False, "No faces selected! Select light source faces!", []

    # Get source face indices
    source_indices = set(f.index for f in selected_faces)

    # Collect light source points (centers of selected faces)
    light_sources = []
    for f in selected_faces:
        light_sources.append(f.calc_center_median())

    # Calculate average color of selected faces (light source color)
    source_colors = []
    for poly in mesh.polygons:
        if poly.index in source_indices:
            for loop_idx in poly.loop_indices:
                c = color_attr.data[loop_idx].color
                source_colors.append((c[0], c[1], c[2]))

    if not source_colors:
        bm.free()
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return False, "Could not read source colors!", []

    # Average light color
    light_color = (
        sum(c[0] for c in source_colors) / len(source_colors),
        sum(c[1] for c in source_colors) / len(source_colors),
        sum(c[2] for c in source_colors) / len(source_colors)
    )
    light_brightness = (light_color[0] + light_color[1] + light_color[2]) / 3.0

    # Calculate auto-radius if not specified
    if radius <= 0:
        total_area = sum(f.calc_area() for f in selected_faces)
        avg_size = math.sqrt(total_area / len(selected_faces)) if selected_faces else 1.0
        radius = avg_size * iterations * 2.0

    # Get vertices from source faces (these won't be modified)
    source_verts = set()
    for f in selected_faces:
        for v in f.verts:
            source_verts.add(v.index)

    # Calculate light factor for each vertex based on distance
    # vertex_light[vert_index] = light_factor
    vertex_light = {}

    for vert in bm.verts:
        if vert.index in source_verts:
            continue  # Skip source vertices

        vert_pos = vert.co

        # Find minimum distance to any light source
        min_dist = float('inf')
        for light_pos in light_sources:
            dist = (vert_pos - light_pos).length
            if dist < min_dist:
                min_dist = dist

        # Only affect vertices within radius
        if min_dist < radius:
            # Calculate falloff based on distance
            # Normalize distance to 0-1 range within radius
            norm_dist = min_dist / radius

            # Apply falloff curve (higher falloff = faster decay)
            # factor goes from intensity (at distance 0) to 0 (at radius)
            factor = intensity * pow(1.0 - norm_dist, falloff)

            vertex_light[vert.index] = factor

    bm.free()

    # Build vertex index to loop indices mapping
    vert_to_loops = {}
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            vert_idx = mesh.loops[loop_idx].vertex_index
            if vert_idx not in vert_to_loops:
                vert_to_loops[vert_idx] = []
            vert_to_loops[vert_idx].append(loop_idx)

    # Apply light to vertices
    modified_count = 0
    affected_loops = []  # Track affected loop indices

    for vert_idx, factor in vertex_light.items():
        if vert_idx not in vert_to_loops:
            continue

        for loop_idx in vert_to_loops[vert_idx]:
            affected_loops.append(loop_idx)

            c = color_attr.data[loop_idx].color

            # Add light but don't exceed source brightness
            add_r = light_color[0] * factor * 0.5
            add_g = light_color[1] * factor * 0.5
            add_b = light_color[2] * factor * 0.5

            new_r = c[0] + add_r
            new_g = c[1] + add_g
            new_b = c[2] + add_b

            # Clamp so we don't exceed light source brightness
            new_brightness = (new_r + new_g + new_b) / 3.0
            if new_brightness > light_brightness:
                scale = light_brightness / new_brightness if new_brightness > 0 else 1.0
                new_r *= scale
                new_g *= scale
                new_b *= scale

            new_r = min(1.0, max(0.0, new_r))
            new_g = min(1.0, max(0.0, new_g))
            new_b = min(1.0, max(0.0, new_b))

            color_attr.data[loop_idx].color = (new_r, new_g, new_b, c[3])

        modified_count += 1

    # Возвращаемся в исходный режим
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

    return True, f"Light scattered to {modified_count} vertices (radius: {radius:.2f})", affected_loops
