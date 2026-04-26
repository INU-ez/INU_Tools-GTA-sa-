"""Export Blender objects → IPL file (object placements)."""

from __future__ import annotations
from ..core.ipl import IplFile, IplInstance, write_ipl


def export_ipl(filepath: str, objects: list, *, binary: bool = False) -> None:
    """
    Generate an IPL file from selected Blender objects.

    Position and rotation are taken from the object's world transform.
    Blender quaternion is (W, X, Y, Z), GTA SA IPL stores (X, Y, Z, W).
    If ``binary=True`` the file is written in `bnry` format.

    LOD pairing: each ``inst`` line ends with ``lod_index`` — a position
    pointer into the same IPL's instance list. We resolve it by reading
    ``obj.inu.lod_object`` (PointerProperty set by Map Import) and
    finding that pointee's index in the current export. Without an LOD
    pointer the value defaults to -1 (no LOD).
    """
    ipl = IplFile()
    obj_per_inst: list = []

    for obj in objects:
        if obj.type != 'MESH':
            continue

        inu = getattr(obj, 'inu', None)

        model_name = _clean_model_name(obj.name)
        model_id = getattr(inu, 'model_id', 0) if inu else 0
        interior = getattr(inu, 'interior_id', 0) if inu else 0

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
            lod_index=-1,  # provisionally; resolved below
        ))
        obj_per_inst.append(obj)

    # ── Dedupe identical placements ──
    # SA crashes (0x534134 access violation in CClumpModelInfo::SetClump)
    # when two ``inst`` lines have the same ``(model_id, x, y, z)`` —
    # the streaming slot allocator gets confused trying to materialise
    # the same model twice at the exact same spot. Real-world cause:
    # a Blender duplicate (``.001``) inherited the same cleaned name
    # plus position from its source object, and after ID unification
    # both end up with the same model_id too. Drop duplicates by
    # rounded position (mm precision is enough to consider two
    # placements «the same», robust against float jitter from
    # successive imports).
    seen_keys: set = set()
    keep_idx: list = []
    for i, inst in enumerate(ipl.instances):
        key = (
            inst.model_id,
            round(inst.pos_x, 3),
            round(inst.pos_y, 3),
            round(inst.pos_z, 3),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        keep_idx.append(i)
    if len(keep_idx) != len(ipl.instances):
        ipl.instances = [ipl.instances[i] for i in keep_idx]
        obj_per_inst = [obj_per_inst[i] for i in keep_idx]

    # ── Resolve lod_index from PointerProperty ──
    # Build object → index map once, then walk instances and write
    # the LOD partner's index where the pointer is set and the
    # pointee is also being exported. Pointer to an object that's
    # outside the export selection silently degrades to -1.
    obj_to_idx = {id(obj): i for i, obj in enumerate(obj_per_inst)}
    for i, obj in enumerate(obj_per_inst):
        inu = getattr(obj, 'inu', None)
        if inu is None:
            continue
        lod_obj = getattr(inu, 'lod_object', None)
        if lod_obj is None:
            continue
        lod_idx = obj_to_idx.get(id(lod_obj), -1)
        if lod_idx >= 0:
            ipl.instances[i].lod_index = lod_idx

    write_ipl(filepath, ipl, binary=binary)


def _clean_model_name(name: str) -> str:
    """Remove Blender duplicate suffixes (.001) and model suffixes/prefixes."""
    from ..tools.model_utils import get_model_type
    # Strip Blender duplicate suffix FIRST (before suffix matching)
    if '.' in name:
        b, s = name.rsplit('.', 1)
        if s.isdigit():
            name = b
    class _Mock:
        def __init__(self, n):
            self.name = n
    _, base = get_model_type(_Mock(name))
    return base
