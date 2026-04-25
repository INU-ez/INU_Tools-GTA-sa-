# INU_tools.ops.col_import
# COL collision file → Blender mesh objects.
# Uses INU_tools.core.col for binary format reading.

import bpy

from ..core.col import read_col_file, ColModel, Vec3


def _get_or_make_col_material(surface, material_cache):
    """Return a reusable material datablock for the given COL surface.

    The cache key is the full surface tuple so different (mat,flags,
    brightness,light) combinations get separate datablocks. Without
    a cache, large-map import creates 10k+ duplicate `COL_N` materials
    (one per surface per model) — sharing collapses that to ~64.
    """
    s = surface
    key = (s.material, s.flags, s.brightness, s.light)
    if material_cache is not None:
        cached = material_cache.get(key)
        if cached is not None:
            return cached, key

    mat = bpy.data.materials.new(f"COL_{s.material}")
    mat.inu.col_mat_index = s.material
    mat.inu.col_flags = s.flags
    mat.inu.col_brightness = s.brightness
    mat.inu.col_light = s.light

    if material_cache is not None:
        material_cache[key] = mat
    return mat, key


def _create_mesh_from_col(model: ColModel, collection, obj_type: str,
                          material_cache=None):
    """Create a Blender mesh object from COL vertices + faces.

    Uses ``mesh.from_pydata`` + ``foreach_set('material_index', ...)``
    instead of bmesh — measured ~5× faster on a large-map import where
    `_create_mesh_from_col` accounted for 60% of total wall time.

    A shared ``material_cache`` dict (keyed by full surface tuple) lets
    the caller reuse material datablocks across many models, avoiding
    thousands of duplicate `bpy.data.materials.new("COL_N")` calls.
    """
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

    # Build geometry buffers in pure Python — much cheaper than bmesh.
    # COL → Blender winding flip done by reordering tuple here, not
    # per-face inside bmesh.
    verts = [(v.x, v.y, v.z) for v in vertices]
    tris = [(f.c, f.b, f.a) for f in faces]

    # Per-face material index, computed alongside cache lookups so we
    # can foreach_set in one shot at the end.
    local_slot = {}  # surface key -> local slot index (per-mesh)
    mat_indices = [0] * len(faces)
    materials_in_order = []

    for i, f in enumerate(faces):
        mat, key = _get_or_make_col_material(f.surface, material_cache)
        slot = local_slot.get(key)
        if slot is None:
            slot = len(local_slot)
            local_slot[key] = slot
            materials_in_order.append(mat)
        mat_indices[i] = slot

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], tris)

    for mat in materials_in_order:
        mesh.materials.append(mat)

    if mat_indices:
        mesh.polygons.foreach_set('material_index', mat_indices)

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
                           skip_position_match: bool = False,
                           material_cache=None):
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
        material_cache: optional dict shared across calls so duplicate
                   surfaces reuse a single material datablock. Pass
                   the same dict for the entire map import.
    """
    if not models:
        raise ValueError("No collision models found in file")

    imported_objects = []
    collection = target_collection if target_collection is not None else bpy.context.collection

    for model in models:
        # Collision mesh
        obj = _create_mesh_from_col(model, collection, 'COL',
                                    material_cache=material_cache)
        if obj:
            imported_objects.append(obj)

        # Shadow mesh
        sha_obj = _create_mesh_from_col(model, collection, 'SHA',
                                        material_cache=material_cache)
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
