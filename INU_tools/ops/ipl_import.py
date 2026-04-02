"""Import IPL file → Blender (place objects or create empties)."""

from __future__ import annotations
import bpy
from mathutils import Quaternion, Vector
from ..core.ipl import read_ipl


def import_ipl(filepath: str, context=None) -> list:
    """
    Read IPL file and position matching Blender objects.

    For each ``inst`` entry, searches for a mesh object whose name matches
    model_name. Tries exact match first, then with _DFF/_LOD suffixes.
    If not found, creates an Empty at that position.

    GTA SA IPL quaternion is (X, Y, Z, W) → Blender quaternion is (W, X, Y, Z).

    Returns list of placed objects.
    """
    ipl = read_ipl(filepath)
    placed = []

    # Build multiple lookups for flexible matching
    # exact name (lowercase) → obj
    exact_lookup: dict[str, bpy.types.Object] = {}
    # clean name without suffixes (lowercase) → {suffix_type: obj}
    clean_lookup: dict[str, dict[str, bpy.types.Object]] = {}

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        low = obj.name.lower()
        if low not in exact_lookup:
            exact_lookup[low] = obj

        clean, suffix_type = _clean_name_typed(obj.name)
        clean_low = clean.lower()
        if clean_low not in clean_lookup:
            clean_lookup[clean_low] = {}
        if suffix_type not in clean_lookup[clean_low]:
            clean_lookup[clean_low][suffix_type] = obj

    for inst in ipl.instances:
        key = inst.model_name.lower()
        is_lod = key.startswith('lod')

        # GTA SA quat (X,Y,Z,W) → Blender quat (W,X,Y,Z), conjugate back
        quat = Quaternion((inst.rot_w, inst.rot_x, inst.rot_y, inst.rot_z)).conjugated()
        loc = Vector((inst.pos_x, inst.pos_y, inst.pos_z))

        # Try to find matching object
        obj = None

        # 1. Exact name match
        obj = exact_lookup.get(key)

        # 2. Match by clean name + appropriate suffix
        if not obj:
            # For LOD entries (name starts with "lod"), strip prefix and look for _LOD suffix
            if is_lod:
                base = key[3:]  # remove "lod" prefix
                variants = clean_lookup.get(base, {})
                obj = variants.get('LOD') or variants.get('DFF')
            else:
                variants = clean_lookup.get(key, {})
                obj = variants.get('DFF') or variants.get('OTHER')

        if obj:
            obj.location = loc
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = quat

            # Rename LODmodel → model_LOD
            if is_lod and obj.name.lower().startswith('lod'):
                base = obj.name[3:]  # remove "LOD" prefix
                obj.name = base + '_LOD'

            inu = obj.inu
            inu.model_id = inst.model_id
            inu.interior_id = inst.interior
            inu.lod_index = inst.lod_index

            placed.append(obj)
        else:
            # Create empty as placeholder (model not in scene)
            empty = bpy.data.objects.new(inst.model_name, None)
            empty.empty_display_type = 'CUBE'
            empty.empty_display_size = 1.0
            empty.location = loc
            empty.rotation_mode = 'QUATERNION'
            empty.rotation_quaternion = quat
            empty['ipl_placeholder'] = True
            empty['ipl_model_name'] = inst.model_name

            if context and context.collection:
                context.collection.objects.link(empty)
            else:
                bpy.context.scene.collection.objects.link(empty)

            inu = empty.inu
            inu.model_id = inst.model_id
            inu.interior_id = inst.interior
            inu.lod_index = inst.lod_index

            placed.append(empty)

    return placed


def _clean_name_typed(name: str) -> tuple[str, str]:
    """Remove Blender numeric suffix and known suffixes.
    Returns (clean_name, suffix_type) where suffix_type is 'DFF', 'LOD', 'COL', 'SHA', or 'OTHER'."""
    if '.' in name:
        base, suffix = name.rsplit('.', 1)
        if suffix.isdigit():
            name = base

    for sfx, stype in [('_DFF', 'DFF'), ('_dff', 'DFF'),
                        ('_LOD', 'LOD'), ('_lod', 'LOD'),
                        ('_COL', 'COL'), ('_col', 'COL'),
                        ('_SHA', 'SHA'), ('_sha', 'SHA')]:
        if name.endswith(sfx):
            return name[:-len(sfx)], stype

    return name, 'OTHER'
