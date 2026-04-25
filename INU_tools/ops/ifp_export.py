# INU_tools.ops.ifp_export — Export Blender actions to GTA SA IFP

import bpy
from ..core.ifp import (
    IFPFile, Animation, AnimBone, KeyFrame,
    HAS_ROT, HAS_TRANS,
    write_ifp, merge_ifp, decimate_ifp, classify_bone_refs,
)


def validate_action_bones(action, armature):
    """Check which bone-name references in an Action's fcurves exist
    on the given armature.

    Silent in-game fails come from this exact mismatch: IFP stores
    ``bone_id`` as the armature index of the bone, so fcurve data on
    bones the target skeleton doesn't have produces ``bone_id = -1``
    entries the game silently skips. Calling this before export and
    surfacing the mismatch lets the user rename / retarget before the
    .ifp goes into an IMG.

    Args:
        action: bpy.types.Action whose fcurves we inspect.
        armature: bpy.types.Object (type='ARMATURE') — target skeleton.

    Returns:
        (unknown, known) — both sorted lists of bone names. ``unknown``
        are referenced by Action fcurves but absent from the armature;
        ``known`` are the ones that will map correctly.
    """
    if armature is None or armature.type != 'ARMATURE':
        return [], []

    return classify_bone_refs(
        (fc.data_path for fc in action.fcurves),
        (pb.name for pb in armature.pose.bones),
    )


def _resolve_actions(actions, armature):
    """Fallback source when ``actions=None``: everything tagged with
    ifp_source plus whatever is currently assigned to ``armature``."""
    return [
        a for a in bpy.data.actions
        if a.get('ifp_source') or (
            armature and armature.animation_data
            and armature.animation_data.action == a
        )
    ]


def _build_animation(action, armature, fps: float) -> Animation:
    """Build one Animation dataclass from a Blender Action."""
    anim = Animation(name=action.name)

    # Group fcurves by bone name
    bone_curves = {}
    for fc in action.fcurves:
        if not fc.data_path.startswith('pose.bones['):
            continue
        parts = fc.data_path.split('"')
        if len(parts) < 2:
            continue
        bone_name = parts[1]
        prop = fc.data_path.rsplit('.', 1)[-1]
        bone_curves.setdefault(bone_name, {}).setdefault(prop, []).append(fc)

    for bone_name, props in bone_curves.items():
        bone = AnimBone(name=bone_name)

        has_rot = 'rotation_quaternion' in props
        has_loc = 'location' in props
        bone.key_type = 0
        if has_rot:
            bone.key_type |= HAS_ROT
        if has_loc:
            bone.key_type |= HAS_TRANS
        if not bone.key_type:
            continue

        if armature:
            pb = armature.pose.bones.get(bone_name)
            if pb:
                bone.bone_id = list(armature.pose.bones).index(pb)

        times = set()
        for prop_curves in props.values():
            for fc in prop_curves:
                for kp in fc.keyframe_points:
                    times.add(kp.co[0])

        for frame in sorted(times):
            kf = KeyFrame(time=frame / fps)

            if has_rot:
                rot_fcs = props['rotation_quaternion']
                quat = [0.0, 0.0, 0.0, 1.0]  # W, X, Y, Z
                for fc in rot_fcs:
                    quat[fc.array_index] = fc.evaluate(frame)
                kf.rotation = (quat[1], quat[2], quat[3], quat[0])  # XYZW

            if has_loc:
                loc_fcs = props['location']
                loc = [0.0, 0.0, 0.0]
                for fc in loc_fcs:
                    loc[fc.array_index] = fc.evaluate(frame)
                kf.translation = tuple(loc)

            bone.keyframes.append(kf)

        anim.bones.append(bone)

    return anim


def build_ifp_from_actions(actions=None, armature=None,
                            package_name: str = "ped",
                            decimate: bool = False,
                            decimate_tol_rot: float = 1e-3,
                            decimate_tol_trans: float = 1e-3) -> IFPFile:
    """Convert Blender Actions into an IFPFile ready for write_ifp /
    merge_ifp. Separated from the file-writing wrapper so the same
    build step can feed both single-file export and merge-into-pack.

    When ``decimate=True`` is passed, keyframes that lie on a linear
    interpolation between their neighbours within the given tolerance
    are dropped from each bone (see ``core.ifp.decimate_ifp``). First
    and last keyframe of every bone are always preserved.
    """
    if armature is None:
        if bpy.context.active_object and bpy.context.active_object.type == 'ARMATURE':
            armature = bpy.context.active_object

    if actions is None:
        actions = _resolve_actions(actions, armature)

    ifp = IFPFile(name=package_name)
    fps = bpy.context.scene.render.fps

    for action in actions:
        ifp.animations.append(_build_animation(action, armature, fps))

    if decimate and ifp.animations:
        decimate_ifp(ifp, decimate_tol_rot, decimate_tol_trans)

    return ifp


def export_ifp(filepath: str, actions=None, armature=None,
               package_name="ped",
               decimate: bool = False,
               decimate_tol_rot: float = 1e-3,
               decimate_tol_trans: float = 1e-3,
               format: str = "ANPK"):
    """Export Blender Actions as a brand-new IFP file.

    Each Action becomes one animation in the IFP. Reads keyframes
    from fcurves on pose bones. Overwrites ``filepath`` completely —
    use ``merge_actions_into_ifp`` to edit a pack in-place.

    ``format`` selects the on-disk encoding (``ANPK`` / ``ANP2`` for
    III/VC/SA chunked float32, ``ANP3`` for SA flat int16-compressed).
    """
    ifp = build_ifp_from_actions(
        actions, armature, package_name,
        decimate=decimate,
        decimate_tol_rot=decimate_tol_rot,
        decimate_tol_trans=decimate_tol_trans,
    )
    if not ifp.animations:
        return 0
    return write_ifp(filepath, ifp, format=format)


def merge_actions_into_ifp(filepath: str, actions=None, armature=None,
                            package_name: str = None,
                            decimate: bool = False,
                            decimate_tol_rot: float = 1e-3,
                            decimate_tol_trans: float = 1e-3,
                            format: str = ""):
    """Merge the given Blender Actions into an existing IFP pack.

    Animations whose name matches an existing entry (case-insensitive)
    overwrite that entry; unknown names are appended. The rest of the
    pack stays intact — this is the flow for patching
    ``ped.ifp`` / ``anim.ifp`` with a single edited animation without
    rewriting all 294 vanilla entries.

    ``format`` is forwarded to the underlying writer; pass empty string
    (default) to preserve the existing pack's on-disk format detected
    by the reader.

    Returns ``(replaced, added)``. When ``filepath`` doesn't exist
    yet, acts like ``export_ifp`` but with the merge-count semantics.
    """
    ifp = build_ifp_from_actions(
        actions, armature, package_name or 'ped',
        decimate=decimate,
        decimate_tol_rot=decimate_tol_rot,
        decimate_tol_trans=decimate_tol_trans,
    )
    if not ifp.animations:
        return 0, 0
    return merge_ifp(filepath, ifp.animations,
                     package_name=package_name, format=format)
