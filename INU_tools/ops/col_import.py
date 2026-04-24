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
    return import_col_from_models(models, bulk_mode=False)


def import_col_from_models(models, *, bulk_mode: bool = False,
                           target_collection=None,
                           skip_position_match: bool = False):
    """Build Blender objects from already-parsed ColModel list.

    Mirrors ``import_dff_from_clump``: the binary parse (``read_col``)
    can run in a worker thread, then the main thread calls this to
    materialise the objects. Used by Import Map for bulk-loading map
    collisions without going through the one-file-at-a-time flow.

    Args:
        models: list of parsed ``ColModel`` instances.
        bulk_mode: when True, skip ``bpy.ops.object.select_all`` and
                   position-match to DFF — caller handles placement
                   itself (this is the map-import case where we copy
                   the object per IPL instance).
        target_collection: destination collection; falls back to the
                   active one.
        skip_position_match: force-skip the «find DFF with same name
                   and copy its location» pass even without bulk_mode.
    """
    if not models:
        raise ValueError("No collision models found in file")

    imported_objects = []
    collection = target_collection if target_collection is not None else bpy.context.collection

    for model in models:
        # Collision mesh
        obj = _create_mesh_from_col(model, collection, 'COL')
        if obj:
            imported_objects.append(obj)

        # Shadow mesh
        sha_obj = _create_mesh_from_col(model, collection, 'SHA')
        if sha_obj:
            imported_objects.append(sha_obj)

        # Spheres — only for single-file import; map import uses the
        # mesh collision geometry and skipping sphere primitives keeps
        # the outliner manageable at 3000+ models.
        if not bulk_mode:
            for i, sphere in enumerate(model.spheres):
                emp = _create_sphere(sphere, collection,
                                     model.model_name or "col", i)
                imported_objects.append(emp)

    # Single-file-import UX: place COL at the matching DFF's origin
    # so the user sees them aligned. Map import skips this — it sets
    # position directly from the IPL instance.
    if not bulk_mode and not skip_position_match:
        for obj in imported_objects:
            if obj.type != 'MESH':
                continue
            base = obj.name
            for suffix in ('_col', '_sha', '_COL', '_SHA'):
                if base.endswith(suffix):
                    base = base[:-len(suffix)]
                    break
            for candidate in bpy.data.objects:
                if candidate == obj or candidate.type != 'MESH':
                    continue
                cname = candidate.name
                cname_low = cname.lower()
                base_low = base.lower()
                if cname_low == base_low or cname_low == base_low + '_dff':
                    obj.location = candidate.location.copy()
                    break

    # Select only on single-file import. Bulk map import needs no
    # selection side-effects.
    if not bulk_mode:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in imported_objects:
            obj.select_set(True)
        if imported_objects:
            bpy.context.view_layer.objects.active = imported_objects[0]

    return imported_objects
