# INU_tools.ops.col_export
# Blender mesh objects → COL collision file.
# Uses INU_tools.core.col for binary format writing.

import math
import bmesh
import mathutils

from ..core.col import (
    ColModel, ColFace, ColSphere, ColBox,
    Bounds, Vec3, Surface,
    write_col_file, write_col,
)


def _vec3(v) -> Vec3:
    """Convert any (x,y,z) to Vec3."""
    return Vec3(v[0], v[1], v[2])


def _get_surface_from_material(mat) -> Surface:
    """Read collision surface properties from a Blender material."""
    surface = Surface()

    if mat is None:
        return surface

    inu = getattr(mat, 'inu', None)
    if inu is not None:
        surface.material = getattr(inu, 'col_mat_index', 0)
        surface.flags = getattr(inu, 'col_flags', 0)
        surface.brightness = getattr(inu, 'col_brightness', 0)
        day = getattr(inu, 'col_day_light', 0)
        night = getattr(inu, 'col_night_light', 0)
        surface.light = (day & 0xF) | ((night & 0xF) << 4)

    return surface


def _collect_mesh(obj, model: ColModel):
    """Triangulate a mesh object and add its vertices/faces to the model."""
    mesh = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        mat = obj.matrix_world.copy()
        mat.translation = (0, 0, 0)
        bm.transform(mat)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.verts.index_update()

        vert_offset = len(model.vertices)

        # Vertices
        for vert in bm.verts:
            model.vertices.append(Vec3(vert.co.x, vert.co.y, vert.co.z))

        # Faces
        for face in bm.faces:
            # Get surface from material
            surface = Surface()
            if face.material_index < len(obj.data.materials):
                mat = obj.data.materials[face.material_index]
                surface = _get_surface_from_material(mat)

            # Swap verts[1] and verts[2] for GTA winding order
            verts = list(face.verts)
            a = verts[0].index + vert_offset
            b = verts[2].index + vert_offset
            c = verts[1].index + vert_offset

            model.faces.append(ColFace(a, b, c, surface))
    finally:
        bm.free()


def _collect_shadow_mesh(obj, model: ColModel):
    """Same as _collect_mesh but writes to shadow_vertices/shadow_faces."""
    mesh = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        mat = obj.matrix_world.copy()
        mat.translation = (0, 0, 0)
        bm.transform(mat)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.verts.index_update()

        vert_offset = len(model.shadow_vertices)

        for vert in bm.verts:
            model.shadow_vertices.append(Vec3(vert.co.x, vert.co.y, vert.co.z))

        for face in bm.faces:
            surface = Surface()
            if face.material_index < len(obj.data.materials):
                mat = obj.data.materials[face.material_index]
                surface = _get_surface_from_material(mat)

            # Swap verts[1] and verts[2] for GTA winding order
            verts = list(face.verts)
            a = verts[0].index + vert_offset
            b = verts[2].index + vert_offset
            c = verts[1].index + vert_offset

            model.shadow_faces.append(ColFace(a, b, c, surface))
    finally:
        bm.free()


def _collect_sphere(obj, model: ColModel):
    """Convert an Empty (sphere display) to ColSphere."""
    radius = max(s * obj.empty_display_size for s in obj.scale)
    center = Vec3(obj.location.x, obj.location.y, obj.location.z)

    surface = Surface()
    inu = getattr(obj, 'inu', None)
    if inu is not None:
        surface.material = getattr(inu, 'col_material', 0)
        surface.flags = getattr(inu, 'col_flags', 0)
        surface.brightness = getattr(inu, 'col_brightness', 0)
        surface.light = getattr(inu, 'col_light', 0)

    model.spheres.append(ColSphere(center=center, radius=radius, surface=surface))


def _compute_bounds(model: ColModel) -> Bounds:
    """Calculate bounding sphere and AABB from all geometry."""
    all_verts = model.vertices + model.shadow_vertices

    if not all_verts:
        return Bounds()

    # AABB
    xs = [v.x for v in all_verts]
    ys = [v.y for v in all_verts]
    zs = [v.z for v in all_verts]

    bb_min = Vec3(min(xs), min(ys), min(zs))
    bb_max = Vec3(max(xs), max(ys), max(zs))

    # Also include sphere centers
    for s in model.spheres:
        bb_min.x = min(bb_min.x, s.center.x - s.radius)
        bb_min.y = min(bb_min.y, s.center.y - s.radius)
        bb_min.z = min(bb_min.z, s.center.z - s.radius)
        bb_max.x = max(bb_max.x, s.center.x + s.radius)
        bb_max.y = max(bb_max.y, s.center.y + s.radius)
        bb_max.z = max(bb_max.z, s.center.z + s.radius)

    # Bounding sphere
    center = Vec3(
        (bb_min.x + bb_max.x) / 2,
        (bb_min.y + bb_max.y) / 2,
        (bb_min.z + bb_max.z) / 2,
    )
    radius = math.sqrt(
        (bb_max.x - bb_min.x) ** 2 +
        (bb_max.y - bb_min.y) ** 2 +
        (bb_max.z - bb_min.z) ** 2
    ) / 2

    return Bounds(center=center, radius=radius, bb_min=bb_min, bb_max=bb_max)


def export_col(filepath: str, objects, version: int = 3, model_name: str = ""):
    """
    Export selected Blender objects as a COL file.

    Args:
        filepath: Output .col file path.
        objects: Iterable of Blender objects to export.
        version: COL version (1, 2, 3, or 4). Default 3 for GTA SA.
        model_name: Model name in COL header. If empty, derived from filename.
    """
    import os

    if not model_name:
        model_name = os.path.splitext(os.path.basename(filepath))[0]

    model = ColModel(version=version, model_name=model_name)

    for obj in objects:
        if obj.type == 'MESH':
            # Determine if this is a shadow mesh or collision mesh
            obj_type = 'COL'
            inu = getattr(obj, 'inu', None)
            if inu is not None:
                obj_type = getattr(inu, 'type', 'COL')

            if obj_type == 'SHA':
                _collect_shadow_mesh(obj, model)
            else:
                _collect_mesh(obj, model)

        elif obj.type == 'EMPTY':
            _collect_sphere(obj, model)

    model.bounds = _compute_bounds(model)
    write_col_file(filepath, [model])
    return model


def export_col_bytes(objects, version: int = 3, model_name: str = "") -> bytes:
    """
    Export selected Blender objects as COL bytes (for embedding in DFF, etc.).
    """
    model = ColModel(version=version, model_name=model_name)

    for obj in objects:
        if obj.type == 'MESH':
            obj_type = 'COL'
            inu = getattr(obj, 'inu', None)
            if inu is not None:
                obj_type = getattr(inu, 'type', 'COL')

            if obj_type == 'SHA':
                _collect_shadow_mesh(obj, model)
            else:
                _collect_mesh(obj, model)

        elif obj.type == 'EMPTY':
            _collect_sphere(obj, model)

    model.bounds = _compute_bounds(model)
    return write_col([model])
