"""Import IPL file → Blender (place objects or create empties)."""

from __future__ import annotations
import bpy
from mathutils import Quaternion, Vector
from ..core.ipl import read_ipl


def import_ipl(filepath: str, context=None) -> list:
    """
    Read IPL file and position matching Blender objects.

    For each ``inst`` entry, searches for a mesh object whose name matches
    model_name (case-insensitive). If found, sets its location and rotation.
    If not found, creates an Empty at that position.

    GTA SA IPL quaternion is (X, Y, Z, W) → Blender quaternion is (W, X, Y, Z).

    Returns list of placed objects.
    """
    ipl = read_ipl(filepath)
    placed = []

    # Build lookup: lowercase name → Blender object
    obj_lookup: dict[str, bpy.types.Object] = {}
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            clean = _clean_name(obj.name).lower()
            if clean not in obj_lookup:
                obj_lookup[clean] = obj

    for inst in ipl.instances:
        key = inst.model_name.lower()

        # GTA SA quat (X,Y,Z,W) → Blender quat (W,X,Y,Z), conjugate back
        quat = Quaternion((inst.rot_w, inst.rot_x, inst.rot_y, inst.rot_z)).conjugated()
        loc = Vector((inst.pos_x, inst.pos_y, inst.pos_z))

        obj = obj_lookup.get(key)
        if obj:
            obj.location = loc
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = quat

            # Store IPL properties
            inu = obj.inu
            inu.model_id = inst.model_id
            inu.interior_id = inst.interior
            inu.lod_index = inst.lod_index

            placed.append(obj)
        else:
            # Create empty as placeholder
            empty = bpy.data.objects.new(inst.model_name, None)
            empty.empty_display_type = 'CUBE'
            empty.empty_display_size = 1.0
            empty.location = loc
            empty.rotation_mode = 'QUATERNION'
            empty.rotation_quaternion = quat

            if context and context.collection:
                context.collection.objects.link(empty)
            else:
                bpy.context.scene.collection.objects.link(empty)

            # Store properties on empty too
            inu = empty.inu
            inu.model_id = inst.model_id
            inu.interior_id = inst.interior
            inu.lod_index = inst.lod_index

            placed.append(empty)

    return placed


def _clean_name(name: str) -> str:
    """Remove Blender numeric suffix and known suffixes."""
    if '.' in name:
        base, suffix = name.rsplit('.', 1)
        if suffix.isdigit():
            name = base
    for sfx in ('_COL', '_col', '_LOD', '_lod', '_SHA', '_sha'):
        if name.endswith(sfx):
            name = name[:-len(sfx)]
            break
    return name
