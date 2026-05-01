# INU_tools.ops.ifp_export — Export Blender actions to GTA SA IFP

import bpy
import mathutils
from ..core.ifp import (
    IFPFile, Animation, AnimBone, KeyFrame,
    HAS_ROT, HAS_TRANS,
    write_ifp, merge_ifp, decimate_ifp, classify_bone_refs,
)


def _bone_rest_local(armature, bone_name):
    """Return ``(rest_quat, rest_mat3)`` — the bone's rest pose in
    parent space (or armature space for the root). Used to invert the
    import-time ``bl_quat = rest_inv @ gta_quat`` transform: on export
    we apply ``gta_quat = rest_quat @ bl_quat`` so the round-trip
    preserves bone-in-parent rotations exactly.
    """
    if not armature or armature.type != 'ARMATURE':
        return mathutils.Quaternion(), mathutils.Matrix.Identity(3)
    rest_bone = armature.data.bones.get(bone_name)
    if not rest_bone:
        return mathutils.Quaternion(), mathutils.Matrix.Identity(3)
    rest_mat = rest_bone.matrix_local
    if rest_bone.parent:
        rest_mat = rest_bone.parent.matrix_local.inverted() @ rest_mat
    rest_quat = rest_mat.to_quaternion()
    return rest_quat, rest_quat.to_matrix()


# Blender 5.x removed the flat ``Action.fcurves`` collection in favour
# of layered Actions (Slot → Layer → Strip → Channelbag → fcurves). This
# helper yields fcurves regardless of version so the export code stays
# linear.
_USE_LAYERED = hasattr(bpy.types, 'ActionSlot')


def _iter_action_fcurves(action):
    """Yield every fcurve attached to ``action`` (legacy or layered)."""
    if not _USE_LAYERED:
        for fc in action.fcurves:
            yield fc
        return
    for layer in getattr(action, 'layers', []):
        for strip in getattr(layer, 'strips', []):
            # Blender 5.x: strip.channelbags is a collection (per-slot).
            # Older alphas exposed ``channelbag()`` as a callable; keep
            # both paths so we don't break anyone who froze a beta.
            cbs = getattr(strip, 'channelbags', None)
            if cbs is None:
                cb_call = getattr(strip, 'channelbag', None)
                if callable(cb_call):
                    try:
                        cb = cb_call(action.slots[0]) if action.slots else None
                    except Exception:
                        cb = None
                    cbs = [cb] if cb else []
                else:
                    cbs = []
            for cb in cbs:
                if cb is None:
                    continue
                for fc in getattr(cb, 'fcurves', []):
                    yield fc


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
        (fc.data_path for fc in _iter_action_fcurves(action)),
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


def _sample_post_ik_pose(armature, frames):
    """Walk ``frames`` and capture every non-control deform bone's
    visual basis (loc + rot quaternion) at each frame.

    Returns ``{bone_name: [(frame, basis_loc, basis_quat), ...]}``.

    Used when the armature has the IK rig active: the user keyframes
    only the IK control bones, so the deform bones have no fcurves
    of their own. Sampling at every IK-keyed frame gives us the
    post-IK pose without ever modifying the source Action — Bake &
    Clear's destructive flow is bypassed entirely.

    The visual-key math here mirrors ``ik_rig._visual_key_deform_bones``
    so the resulting basis values reproduce the IK-driven pose 1:1
    after the (now stripped) IK constraints are gone.
    """
    samples = {}
    if not frames:
        return samples
    scene = bpy.context.scene
    saved_frame = scene.frame_current
    try:
        for f in sorted(frames):
            f_int = int(round(f))
            scene.frame_set(f_int)
            bpy.context.view_layer.update()

            # Capture all visuals upfront so reading a child's matrix
            # isn't contaminated by parent-basis writes — pure read,
            # no writes here, but the same defensive pattern as in
            # ik_rig keeps things consistent if this is ever extended.
            visuals = {pb.name: pb.matrix.copy()
                       for pb in armature.pose.bones}

            for pb in armature.pose.bones:
                db = armature.data.bones.get(pb.name)
                if db is None:
                    continue
                if db.get('inu_ik_control'):
                    continue
                visual = visuals[pb.name]
                if pb.parent:
                    parent_visual = visuals.get(
                        pb.parent.name, pb.parent.matrix)
                    local_rest = (
                        pb.parent.bone.matrix_local.inverted()
                        @ pb.bone.matrix_local)
                    basis = (local_rest.inverted()
                             @ parent_visual.inverted() @ visual)
                else:
                    basis = pb.bone.matrix_local.inverted() @ visual
                loc, rot_q, _scl = basis.decompose()
                samples.setdefault(pb.name, []).append(
                    (f, loc, rot_q))
    finally:
        scene.frame_set(saved_frame)
        bpy.context.view_layer.update()
    return samples


def _build_animation_from_ik_samples(action, armature,
                                      fps, samples):
    """Build an Animation by sampling deform-bone poses (post-IK)
    at every keyed frame, instead of reading deform-bone fcurves.
    Mirrors the fcurve path's bone_id resolution + rest_quat /
    rest_mat math, so the resulting IFP is interchangeable with
    the post-Bake & Clear output."""
    anim = Animation(name=action.name)
    for bone_name, sample_list in samples.items():
        if not sample_list:
            continue
        # Skip bones that never actually move — sampling captures
        # every non-control deform bone, but most ped bones (fingers,
        # jaw, eyelids, etc.) sit at identity basis the whole time.
        # Including them would bloat the IFP with constant rotations
        # the engine could already read from the rest skeleton.
        rot_active = any(
            abs(q.w - 1.0) > 1e-4 or abs(q.x) > 1e-4
            or abs(q.y) > 1e-4 or abs(q.z) > 1e-4
            for _f, _l, q in sample_list
        )
        loc_active = any(
            abs(loc.x) > 1e-5 or abs(loc.y) > 1e-5
            or abs(loc.z) > 1e-5
            for _f, loc, _q in sample_list
        )
        if not (rot_active or loc_active):
            continue

        rest_quat, rest_mat = _bone_rest_local(armature, bone_name)
        bone = AnimBone(name=bone_name)
        bone.key_type = (
            (HAS_ROT if rot_active else 0)
            | (HAS_TRANS if loc_active else 0)
        )

        if armature:
            data_bone = armature.data.bones.get(bone_name)
            if data_bone is not None and 'bone_id' in data_bone:
                bone.bone_id = int(data_bone['bone_id'])
            else:
                pb = armature.pose.bones.get(bone_name)
                if pb:
                    bone.bone_id = list(armature.pose.bones).index(pb)

        for frame, loc, rot_q in sample_list:
            kf = KeyFrame(time=frame / fps)
            if rot_active:
                gta_quat = rest_quat @ rot_q
                kf.rotation = (gta_quat.x, gta_quat.y,
                               gta_quat.z, gta_quat.w)
            if loc_active:
                gta_loc = rest_mat @ loc
                kf.translation = (gta_loc.x, gta_loc.y, gta_loc.z)
            bone.keyframes.append(kf)
        anim.bones.append(bone)
    return anim


def _build_animation(action, armature, fps: float) -> Animation:
    """Build one Animation dataclass from a Blender Action.

    When the armature has an active IK rig (``inu_ik_rigged`` flag),
    we BYPASS the fcurve-based path and sample post-IK pose at every
    keyed frame instead. This lets the user animate purely on IK
    controls without first running Bake & Clear — the export
    captures the IK-driven deform pose on the fly."""
    if armature is not None and armature.get('inu_ik_rigged'):
        # Collect every keyed frame across the action — control
        # bones (where the user's keys live) AND any deform fcurves
        # they may have authored alongside.
        keyed_frames = set()
        for fc in _iter_action_fcurves(action):
            if not fc.data_path.startswith('pose.bones['):
                continue
            for kp in fc.keyframe_points:
                keyed_frames.add(int(round(kp.co[0])))
        if keyed_frames:
            samples = _sample_post_ik_pose(armature, keyed_frames)
            return _build_animation_from_ik_samples(
                action, armature, fps, samples)
        # Fall through to fcurve path if no keys at all (empty action).

    anim = Animation(name=action.name)

    # Group fcurves by bone name
    bone_curves = {}
    for fc in _iter_action_fcurves(action):
        if not fc.data_path.startswith('pose.bones['):
            continue
        parts = fc.data_path.split('"')
        if len(parts) < 2:
            continue
        bone_name = parts[1]
        prop = fc.data_path.rsplit('.', 1)[-1]
        bone_curves.setdefault(bone_name, {}).setdefault(prop, []).append(fc)

    for bone_name, props in bone_curves.items():
        # Skip IK control bones (created by ops.ik_rig). They live
        # inside the armature only for posing, are marked with the
        # ``inu_ik_control`` custom prop, and have no HAnim id —
        # without this guard their fcurves would fall through to
        # the pose-index id fallback and remap real ped rotations.
        if armature is not None:
            db = armature.data.bones.get(bone_name)
            if db is not None and db.get('inu_ik_control'):
                continue

        bone = AnimBone(name=bone_name)

        has_rot = 'rotation_quaternion' in props
        has_loc = 'location' in props

        # Strip the translation channel for bones that never actually
        # move. Blender's "Whole Character" / "Location & Rotation"
        # keying sets insert a location keyframe on EVERY selected pose
        # bone, even if the user only rotated it. SA's ped IFPs only
        # ever store translation on the root (Normal/Bip01) — every
        # other bone takes its rest_head from the skeleton DFF. If we
        # write zero translation on Jaw, finger tips, breasts, etc. the
        # engine reads "put this bone at parent's origin" instead of
        # "leave at rest", and the joints collapse into the parent —
        # character compresses into a small blob. So drop the location
        # channel when every value across the action is ~0.
        if has_loc:
            loc_active = False
            for fc in props['location']:
                for kp in fc.keyframe_points:
                    if abs(kp.co[1]) > 1e-5:
                        loc_active = True
                        break
                if loc_active:
                    break
            if not loc_active:
                has_loc = False

        bone.key_type = 0
        if has_rot:
            bone.key_type |= HAS_ROT
        if has_loc:
            bone.key_type |= HAS_TRANS
        if not bone.key_type:
            continue

        # SA bone_id is the HAnim hash from the DFF (e.g. L UpperArm=32,
        # Bip01 L Clavicle=31) — NOT a sequential pose-bone index. The
        # DFF importer stashes the original id on each edit_bone as the
        # 'bone_id' custom prop; read it back here. Falling back to the
        # pose index produced ids 1..32 for an animation whose vanilla
        # ids spread across 0..302, so the engine remapped rotations to
        # the wrong bones (twisted hands / broken face).
        if armature:
            data_bone = armature.data.bones.get(bone_name)
            if data_bone is not None and 'bone_id' in data_bone:
                bone.bone_id = int(data_bone['bone_id'])
            else:
                pb = armature.pose.bones.get(bone_name)
                if pb:
                    bone.bone_id = list(armature.pose.bones).index(pb)

        # Mirrors the import-time formula: import did
        #   bl_quat = rest_inv @ gta_quat,  bl_loc = rest_inv_mat @ gta_loc
        # so export reverses it with
        #   gta_quat = rest_quat @ bl_quat, gta_loc = rest_mat @ bl_loc
        # to recover the absolute bone-in-parent rotation/translation
        # the IFP format expects. Skipping this step was producing
        # animations that played in MTA but with the character flat on
        # the ground — every bone was rotated by rest^-1.
        rest_quat, rest_mat = _bone_rest_local(armature, bone_name)

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
                bl_quat = mathutils.Quaternion(
                    (quat[0], quat[1], quat[2], quat[3]))
                # Per-channel evaluate on Bezier-sampled (densified)
                # fcurves can produce non-unit quaternions — magnitudes
                # drift to 0.7-1.2. Without this normalize, the off
                # magnitude propagates through ANP3 int16×4096 quant
                # and the engine applies slightly-off rotations every
                # 30Hz tick → visible "stepped" playback in-game.
                if bl_quat.magnitude > 0:
                    bl_quat.normalize()
                gta_quat = rest_quat @ bl_quat
                kf.rotation = (
                    gta_quat.x, gta_quat.y, gta_quat.z, gta_quat.w)

            if has_loc:
                loc_fcs = props['location']
                loc = [0.0, 0.0, 0.0]
                for fc in loc_fcs:
                    loc[fc.array_index] = fc.evaluate(frame)
                gta_loc = rest_mat @ mathutils.Vector(loc)
                kf.translation = (gta_loc.x, gta_loc.y, gta_loc.z)

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
