# INU_tools.ops.col_export
# Blender mesh objects → COL collision file.
# Uses INU_tools.core.col for binary format writing.

import math
import bpy
import bmesh
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper

from .. import T
from ..core.col import (
    ColModel, ColFace, ColSphere, ColBox, Bounds, Vec3, Surface,
    write_col_file, write_col,
)
from ..core import game_versions


def _resolve_col_version(context=None) -> int:
    """Pick the COL file version for export from the scene's active
    game (gtatools_game). Falls back to 3 (SA COL3) when context is
    unavailable. Centralised so every caller — operator, IMG bulk
    export, INU Export, map export — uses the same dispatch.
    """
    if context is None:
        try:
            import bpy as _bpy
            context = _bpy.context
        except Exception:
            return 3
    scene = getattr(context, 'scene', None)
    if scene is None:
        return 3
    game = game_versions.game_of_scene(scene)
    return game_versions.profile_for(game).col_version


def _vec3(v) -> Vec3:
    """Convert any (x,y,z) to Vec3."""
    return Vec3(v[0], v[1], v[2])


def _get_surface_from_material(mat, target_game: str = '') -> Surface:
    """Read collision surface properties from a Blender material.

    When ``target_game`` is set and the material was imported from a
    different game (``inu.col_source_game`` recorded the source),
    route the surface ID through ``core.surface_translate`` so the
    written byte points at the right material in the target game's
    surface table. Without translation a III asphalt (id=1) and an SA
    asphalt (id=1) happen to align but a III glass (id=7) would land
    as PEBBLES in SA — translation maps it to SA's glass (id=35).
    """
    surface = Surface()

    if mat is None:
        return surface

    inu = getattr(mat, 'inu', None)
    if inu is not None:
        sid = getattr(inu, 'col_mat_index', 0)
        source = getattr(inu, 'col_source_game', '') or ''
        if target_game and source and source != target_game:
            from ..core.surface_translate import translate_surface
            sid = translate_surface(sid, source, target_game)
        surface.material = sid
        surface.flags = getattr(inu, 'col_flags', 0)
        surface.brightness = getattr(inu, 'col_brightness', 0)
        day = getattr(inu, 'col_day_light', 0)
        night = getattr(inu, 'col_night_light', 0)
        surface.light = (day & 0xF) | ((night & 0xF) << 4)

    return surface


_COL_VERSION_TO_GAME = {1: 'III', 2: 'VC', 3: 'SA'}


def _collect_mesh(obj, model: ColModel):
    """Triangulate a mesh object and add its vertices/faces to the model."""
    mesh = obj.data
    target_game = _COL_VERSION_TO_GAME.get(model.version, 'SA')
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
                surface = _get_surface_from_material(mat, target_game)

            # Swap verts[1] and verts[2] for GTA winding order
            verts = list(face.verts)
            a = verts[0].index + vert_offset
            b = verts[2].index + vert_offset
            c = verts[1].index + vert_offset

            model.faces.append(ColFace(a, b, c, surface))
    finally:
        bm.free()


def _is_shadow_mesh(obj) -> bool:
    """Detect if a Blender object should be treated as shadow mesh.

    Two ways to mark a mesh as shadow-only (Kam's/Rockstar convention):
      1. obj.inu.type == 'SHA'  (INU_Tools dropdown)
      2. Object name ends with '_SHA' / '_sha'  (Kam's suffix convention)
    """
    # Explicit type on inu property
    inu = getattr(obj, 'inu', None)
    if inu is not None and getattr(inu, 'type', '') == 'SHA':
        return True
    # Name suffix
    name = obj.name.lower()
    if name.endswith('_sha') or '_sha.' in name:  # .001 suffix variants
        return True
    return False


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


def _collect_box(obj, model: ColModel):
    """Convert an Empty (cube display) to ColBox primitive.

    Inverse of `_create_box` in col_import: Blender's location is the
    box center, scale carries the half-extents per axis. AABB min/max
    fall out as `loc ± scale`. `abs()` on scale defends against the
    user mirroring an empty to a negative scale — the game stores an
    unordered AABB and a min > max box is silently dropped at load.
    """
    cx, cy, cz = obj.location
    sx, sy, sz = abs(obj.scale.x), abs(obj.scale.y), abs(obj.scale.z)

    surface = Surface()
    inu = getattr(obj, 'inu', None)
    if inu is not None:
        surface.material   = getattr(inu, 'col_material', 0)
        surface.flags      = getattr(inu, 'col_flags', 0)
        surface.brightness = getattr(inu, 'col_brightness', 0)
        surface.light      = getattr(inu, 'col_light', 0)

    model.boxes.append(ColBox(
        bb_min=Vec3(cx - sx, cy - sy, cz - sz),
        bb_max=Vec3(cx + sx, cy + sy, cz + sz),
        surface=surface,
    ))


def _collect_empty(obj, model: ColModel):
    """Dispatch an Empty to the right collector based on its display
    type. `'SPHERE'` → sphere primitive; `'CUBE'` → box primitive.
    Any other display type (`ARROWS`, `PLAIN_AXES`, …) is treated as
    sphere for backward compat with files imported by older versions
    that only knew about sphere empties."""
    if obj.empty_display_type == 'CUBE':
        _collect_box(obj, model)
    else:
        _collect_sphere(obj, model)


def _compute_bounds(model: ColModel) -> Bounds:
    """Calculate bounding sphere and AABB from all geometry.

    Accounts for vertices (mesh + shadow mesh), spheres AND boxes.
    Missing boxes was a bug that broke bounds for COL files that
    only have box collision (e.g. light beams with dummy box bounds).
    """
    all_verts = model.vertices + model.shadow_vertices
    has_any = bool(all_verts) or bool(model.spheres) or bool(model.boxes)

    if not has_any:
        return Bounds()

    # Seed AABB from first available source
    INF = float('inf')
    bb_min = Vec3(INF, INF, INF)
    bb_max = Vec3(-INF, -INF, -INF)

    for v in all_verts:
        if v.x < bb_min.x: bb_min.x = v.x
        if v.y < bb_min.y: bb_min.y = v.y
        if v.z < bb_min.z: bb_min.z = v.z
        if v.x > bb_max.x: bb_max.x = v.x
        if v.y > bb_max.y: bb_max.y = v.y
        if v.z > bb_max.z: bb_max.z = v.z

    for s in model.spheres:
        if s.center.x - s.radius < bb_min.x: bb_min.x = s.center.x - s.radius
        if s.center.y - s.radius < bb_min.y: bb_min.y = s.center.y - s.radius
        if s.center.z - s.radius < bb_min.z: bb_min.z = s.center.z - s.radius
        if s.center.x + s.radius > bb_max.x: bb_max.x = s.center.x + s.radius
        if s.center.y + s.radius > bb_max.y: bb_max.y = s.center.y + s.radius
        if s.center.z + s.radius > bb_max.z: bb_max.z = s.center.z + s.radius

    for b in model.boxes:
        if b.bb_min.x < bb_min.x: bb_min.x = b.bb_min.x
        if b.bb_min.y < bb_min.y: bb_min.y = b.bb_min.y
        if b.bb_min.z < bb_min.z: bb_min.z = b.bb_min.z
        if b.bb_max.x > bb_max.x: bb_max.x = b.bb_max.x
        if b.bb_max.y > bb_max.y: bb_max.y = b.bb_max.y
        if b.bb_max.z > bb_max.z: bb_max.z = b.bb_max.z

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
            if _is_shadow_mesh(obj):
                _collect_shadow_mesh(obj, model)
            else:
                _collect_mesh(obj, model)

        elif obj.type == 'EMPTY':
            _collect_empty(obj, model)

    model.bounds = _compute_bounds(model)
    write_col_file(filepath, [model])
    return model


def build_col_model(objects, version: int = 3, model_name: str = "") -> ColModel:
    """Build a ``ColModel`` from Blender objects (main thread).

    Split out so batch exporters can build models on the main thread
    (bpy reads) and then hand them off to a worker pool for the CPU-
    bound ``write_col`` serialisation.
    """
    model = ColModel(version=version, model_name=model_name)

    for obj in objects:
        if obj.type == 'MESH':
            if _is_shadow_mesh(obj):
                _collect_shadow_mesh(obj, model)
            else:
                _collect_mesh(obj, model)

        elif obj.type == 'EMPTY':
            _collect_empty(obj, model)

    model.bounds = _compute_bounds(model)
    return model


def export_col_bytes(objects, version: int = 3, model_name: str = "") -> bytes:
    """
    Export selected Blender objects as COL bytes (for embedding in DFF, etc.).
    """
    model = build_col_model(objects, version=version, model_name=model_name)
    return write_col([model])


def _group_objects_by_base(objects) -> dict:
    """Group collidable objects by their model base name for library export.

    Grouping rules:
      - MESH objects use :func:`get_model_type` to extract ``base_name``
        (honours suffix/prefix settings — ``_COL``, ``_SHA``, etc.).
      - EMPTY objects (collision spheres/boxes) inherit the base name from
        their parent mesh when possible, otherwise use their own name with
        any Blender ``.001`` duplicate suffix stripped.
      - If an object exposes a non-empty ``inu.model_name``, that wins over
        the derived base so re-exported COLs keep their original library
        key even if the Blender object was renamed.

    Returns ``{base_name: [obj, ...]}`` preserving insertion order.
    """
    from ..tools.model_utils import get_model_type

    groups: dict = {}

    def _clean(name: str) -> str:
        if '.' in name:
            head, tail = name.rsplit('.', 1)
            if tail.isdigit():
                return head
        return name

    def _base_for(obj) -> str:
        inu = getattr(obj, 'inu', None)
        if inu is not None:
            mn = getattr(inu, 'model_name', '') or ''
            if mn:
                return mn
        if obj.type == 'MESH':
            _, base = get_model_type(obj)
            return base or _clean(obj.name)
        if obj.type == 'EMPTY' and obj.parent is not None:
            return _base_for(obj.parent)
        return _clean(obj.name)

    for obj in objects:
        if obj.type not in ('MESH', 'EMPTY'):
            continue
        base = _base_for(obj)
        if not base:
            continue
        groups.setdefault(base, []).append(obj)

    return groups


def export_col_library(filepath: str, objects, version: int = 3) -> int:
    """Export a multi-entry COL "library" file.

    Selected objects are grouped by base name (via :func:`_group_objects_by_base`)
    and each group becomes its own COL record inside the single ``filepath``.
    This is how vanilla GTA SA ships ``<district>.col``, ``vehicles.col``,
    etc. — one ``.col`` file with many entries concatenated back-to-back.

    Returns the number of records written.
    """
    groups = _group_objects_by_base(objects)
    models = []
    for base_name, objs in groups.items():
        model = ColModel(version=version, model_name=base_name)
        for obj in objs:
            if obj.type == 'MESH':
                if _is_shadow_mesh(obj):
                    _collect_shadow_mesh(obj, model)
                else:
                    _collect_mesh(obj, model)
            elif obj.type == 'EMPTY':
                _collect_empty(obj, model)
        model.bounds = _compute_bounds(model)
        models.append(model)

    if models:
        from ..core.col import write_col_file
        write_col_file(filepath, models)
    return len(models)


# ──────────────────── Blender operator wrapper ────────────────────────

class GTATOOLS_OT_export_col(bpy.types.Operator, ExportHelper):
    """Экспортировать COL модель коллизии"""
    bl_idname = "gtatools.export_col"
    bl_label = "INU: Export COL"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    library_mode: BoolProperty(
        name=T("Library (несколько коллизий)"),
        description=T("Сгруппировать выделение по базовому имени (house1_COL + house1_SHA → одна запись 'house1') и записать все группы в один .col файл подряд. Так vanilla SA хранит <district>.col и vehicles.col"),
        default=False,
    )

    def execute(self, context):
        from ..tools.prelight import setup_prelight_preview
        import os

        # Common COL-name suffixes the importer / Map Import may attach.
        # Stripped from object names to derive a per-mesh filename in
        # the multi-select branch.
        SUFFIXES = ('_col', '.col', '_dff', '.dff', '_lod', '_dam', '_ok')

        def _basename_for(obj):
            n = obj.name
            ln = n.lower()
            for s in SUFFIXES:
                if ln.endswith(s):
                    return n[:-len(s)]
            return n

        prelight_was_on = []
        try:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    has_prelight = False
                    for mat_slot in obj.material_slots:
                        mat = mat_slot.material
                        if mat and mat.use_nodes and mat.node_tree.nodes.get("Prelight_Mix"):
                            has_prelight = True
                            break
                    if has_prelight:
                        prelight_was_on.append(obj)
                        setup_prelight_preview(obj, enable=False)

            # COL is always exported around (0,0,0) — temporarily move
            original_locations = {}
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    original_locations[obj.name] = obj.location.copy()
                    obj.location = (0, 0, 0)

            col_objects = [o for o in context.selected_objects
                           if o.type in ('MESH', 'EMPTY')]
            mesh_objects = [o for o in col_objects if o.type == 'MESH']

            col_ver = _resolve_col_version(context)

            # ── Per-mesh split ────────────────────────────────────────
            # `library_mode=False` + multiple selected meshes → one .col
            # per mesh, named after each mesh (suffix-stripped). Default
            # behaviour previously bundled them all into one file which
            # mismatched user expectation and the rest of the toolset
            # (TXD now does per-mesh too).
            if not self.library_mode and len(mesh_objects) > 1:
                out_dir = os.path.dirname(self.filepath) or '.'
                written = []
                errors = []
                for obj in mesh_objects:
                    base = _basename_for(obj)
                    col_path = os.path.join(out_dir, f"{base}.col")
                    try:
                        export_col(
                            filepath=col_path,
                            objects=[obj],
                            version=col_ver,
                            model_name=base,
                        )
                        written.append(f"{base}.col")
                    except Exception as e:
                        errors.append(f"{base}.col: {e}")

                # Restore positions before reporting so user can re-export
                # without picking up zeroed transforms on failure paths.
                for obj in context.selected_objects:
                    if obj.name in original_locations:
                        obj.location = original_locations[obj.name]
                for obj in prelight_was_on:
                    setup_prelight_preview(obj, enable=True)

                if not written:
                    self.report({'ERROR'},
                                "COL export failed for every mesh: "
                                + "; ".join(errors[:3]))
                    return {'CANCELLED'}
                summary = (f"{len(written)} COL written to {out_dir}"
                           + (f" ({len(errors)} failed)" if errors else ""))
                self.report({'WARNING'} if errors else {'INFO'}, summary)
                return {'FINISHED'}

            # ── Single-file paths (legacy behaviour) ──────────────────
            if self.library_mode:
                count = export_col_library(
                    filepath=self.filepath,
                    objects=col_objects,
                    version=col_ver,
                )
                msg = f"Exported COL{col_ver} library: {self.filepath} ({count} records)"
            else:
                export_col(
                    filepath=self.filepath,
                    objects=col_objects,
                    version=col_ver,
                )
                msg = f"Exported COL{col_ver}: {self.filepath}"

            # Restore original positions
            for obj in context.selected_objects:
                if obj.name in original_locations:
                    obj.location = original_locations[obj.name]

            for obj in prelight_was_on:
                setup_prelight_preview(obj, enable=True)

            self.report({'INFO'}, msg)
            return {'FINISHED'}
        except Exception as e:
            for obj in prelight_was_on:
                try:
                    setup_prelight_preview(obj, enable=True)
                except:
                    pass
            self.report({'ERROR'}, f"COL export error: {str(e)}")
            return {'CANCELLED'}


classes = (
    GTATOOLS_OT_export_col,
)
