# INU_tools.ops.col_import
# COL collision file → Blender mesh objects.
# Uses INU_tools.core.col for binary format reading.

import bpy
import bmesh

from ..core.col import read_col_file, ColModel, Vec3


def _create_mesh_from_col(model: ColModel, collection, obj_type: str):
    """Create a Blender mesh object from COL vertices + faces via bmesh."""
    if obj_type == 'COL':
        vertices = model.vertices
        faces = model.faces
        suffix = '_col'
    else:
        vertices = model.shadow_vertices
        faces = model.shadow_faces
        suffix = '_sha'

    if not vertices or not faces:
        return None

    name = (model.model_name or "col_model") + suffix

    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    # Вершины
    for v in vertices:
        bm.verts.new((v.x, v.y, v.z))

    bm.verts.ensure_lookup_table()

    # Материалы: группируем по surface
    surface_map = {}  # (material, flags, brightness, light) -> mat_index

    for face in faces:
        s = face.surface
        key = (s.material, s.flags, s.brightness, s.light)
        if key not in surface_map:
            mat_idx = len(surface_map)
            surface_map[key] = mat_idx

            mat_name = f"COL_{s.material}"
            mat = bpy.data.materials.new(mat_name)
            mat.inu.col_mat_index = s.material
            mat.inu.col_flags = s.flags
            mat.inu.col_brightness = s.brightness
            mat.inu.col_light = s.light
            mesh.materials.append(mat)

        try:
            # Reverse winding (COL → Blender)
            bm_face = bm.faces.new([
                bm.verts[face.c],
                bm.verts[face.b],
                bm.verts[face.a],
            ])
            bm_face.material_index = surface_map[key]
        except Exception as e:
            print(f"[INU_tools] COL face error: {e}")

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    obj.inu.type = obj_type

    collection.objects.link(obj)
    return obj


def _create_sphere(sphere, collection, model_name: str, index: int):
    """Create an Empty with sphere display from ColSphere."""
    name = f"{model_name}_sphere_{index}"
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'SPHERE'
    empty.empty_display_size = sphere.radius
    empty.location = (sphere.center.x, sphere.center.y, sphere.center.z)

    empty.inu.col_material = sphere.surface.material
    empty.inu.col_flags = sphere.surface.flags
    empty.inu.col_brightness = sphere.surface.brightness
    empty.inu.col_light = sphere.surface.light

    collection.objects.link(empty)
    return empty


def import_col(filepath: str, context=None):
    """
    Import a COL file into Blender.

    Args:
        filepath: Path to .col file.
        context: Blender context (optional).
    """
    models = read_col_file(filepath)

    if not models:
        raise ValueError("No collision models found in file")

    imported_objects = []
    collection = bpy.context.collection

    for model in models:
        # Collision mesh
        obj = _create_mesh_from_col(model, collection, 'COL')
        if obj:
            imported_objects.append(obj)

        # Shadow mesh
        sha_obj = _create_mesh_from_col(model, collection, 'SHA')
        if sha_obj:
            imported_objects.append(sha_obj)

        # Spheres
        for i, sphere in enumerate(model.spheres):
            emp = _create_sphere(sphere, collection, model.model_name or "col", i)
            imported_objects.append(emp)

    # Match position to DFF object with same base name
    for obj in imported_objects:
        if obj.type != 'MESH':
            continue
        base = obj.name
        for suffix in ('_col', '_sha', '_COL', '_SHA'):
            if base.endswith(suffix):
                base = base[:-len(suffix)]
                break
        # Search for matching DFF object
        for candidate in bpy.data.objects:
            if candidate == obj or candidate.type != 'MESH':
                continue
            cname = candidate.name
            cname_low = cname.lower()
            base_low = base.lower()
            if cname_low == base_low or cname_low == base_low + '_dff':
                obj.location = candidate.location.copy()
                break

    # Select imported objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported_objects:
        obj.select_set(True)
    if imported_objects:
        bpy.context.view_layer.objects.active = imported_objects[0]

    return imported_objects
