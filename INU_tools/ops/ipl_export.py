"""Export Blender objects → IPL file (object placements)."""

from __future__ import annotations
from ..core.ipl import IplFile, IplInstance, write_ipl


def export_ipl(filepath: str, objects: list) -> None:
    """
    Generate an IPL file from selected Blender objects.

    Position and rotation are taken from the object's world transform.
    Blender quaternion is (W, X, Y, Z), GTA SA IPL stores (X, Y, Z, W).
    """
    ipl = IplFile()

    for obj in objects:
        if obj.type != 'MESH':
            continue

        inu = getattr(obj, 'inu', None)

        model_name = _clean_model_name(obj.name)
        model_id = getattr(inu, 'model_id', 0) if inu else 0
        interior = getattr(inu, 'interior_id', 0) if inu else 0
        lod_index = getattr(inu, 'lod_index', -1) if inu else -1

        # World position
        loc = obj.matrix_world.translation

        # World rotation as quaternion — Blender: (W,X,Y,Z)
        # GTA SA uses conjugate quaternion (like Kam's scripts)
        rot = obj.matrix_world.to_quaternion().conjugated()

        ipl.instances.append(IplInstance(
            model_id=model_id,
            model_name=model_name,
            interior=interior,
            pos_x=loc.x,
            pos_y=loc.y,
            pos_z=loc.z,
            rot_x=rot.x,
            rot_y=rot.y,
            rot_z=rot.z,
            rot_w=rot.w,
            lod_index=lod_index,
        ))

    write_ipl(filepath, ipl)


def _clean_model_name(name: str) -> str:
    """Remove suffixes/prefixes and Blender duplicate suffixes (.001, .002)."""
    from ..tools.model_utils import get_model_type
    class _Mock:
        def __init__(self, n):
            self.name = n
    _, base = get_model_type(_Mock(name))
    # Strip Blender duplicate suffix (.001, .002, etc.)
    if '.' in base:
        b, s = base.rsplit('.', 1)
        if s.isdigit():
            base = b
    return base
