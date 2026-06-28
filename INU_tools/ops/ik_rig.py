# INU_tools.ops.ik_rig — Bone-based IK rigging for SA ped armatures.
#
# Adds non-deform "control bones" inside the armature plus IK / Copy
# Rotation / Copy Location constraints on the deform bones, so the
# user can pose feet/hands/head/root by grabbing the control bones
# directly in pose mode. Everything stays inside the armature — no
# empty objects in the scene, single Action holds all keys. Bake
# operator visual-keys the IK result onto the deform bones, strips
# constraints AND removes the control bones, leaving an Action that
# exports cleanly via Export IFP.

import bpy
import math
import os
import mathutils

from .. import T


def _calibrate_pole_angle(context, ik_constraint, deform_pb,
                            target_tip, mid_pb, target_mid):
    """Brute-force search for the ``pole_angle`` that makes Blender's
    IK solver reproduce the FK pose. SA bones have arbitrary roll,
    so Cessen's analytic formula doesn't work; sweeping the full
    [-π, π] range is slower but reliable.

    The drift metric sums tail- and mid-bone position errors —
    measuring only the tail is ambiguous for near-straight chains
    where pole_angle=0 and pole_angle=±π give the same end point
    but flip the bend direction. Including the mid bone (elbow /
    knee) breaks the tie."""
    deps = context.view_layer

    def _drift_at(angle_rad):
        ik_constraint.pole_angle = angle_rad
        deps.update()
        tail_err = (deform_pb.tail - target_tip).length
        mid_err = (mid_pb.head - target_mid).length
        return tail_err + mid_err

    coarse_step = math.radians(30.0)
    best_angle = 0.0
    best_err = float('inf')
    for i in range(12):
        a = -math.pi + i * coarse_step
        err = _drift_at(a)
        if err < best_err:
            best_err = err
            best_angle = a

    fine_step = math.radians(2.0)
    fine_start = best_angle - coarse_step
    for i in range(31):
        a = fine_start + i * fine_step
        if a < -math.pi or a > math.pi:
            continue
        err = _drift_at(a)
        if err < best_err:
            best_err = err
            best_angle = a

    ik_constraint.pole_angle = best_angle
    deps.update()
    return best_angle


_SA_CHAINS = [
    ("R_arm", [" R UpperArm", " R ForeArm", " R Hand"]),
    ("L_arm", [" L UpperArm", " L ForeArm", " L Hand"]),
    ("R_leg", [" R Thigh", " R Calf", " R Foot"]),
    ("L_leg", [" L Thigh", " L Calf", " L Foot"]),
]

# Single-bone Copy-Rotation controls (head, upper torso). Each is
# NOT part of any IK chain so Copy Rotation can drive its world
# rotation without fighting an IK solver. Order matters — earlier
# entries are processed first; spine1 wires before head so the
# torso rotation is applied first when the user keys both.
_SA_ROT_BONES = [
    ("spine1", [" Spine1", "Spine1", "Bip01 Spine1"]),
    ("R_shoulder", ["Bip01 R Clavicle", " Bip01 R Clavicle"]),
    ("L_shoulder", ["Bip01 L Clavicle", " Bip01 L Clavicle"]),
    ("head", [" Head", "Head", "Bip01 Head"]),
]

# Root controller — Copy Location + Copy Rotation on Pelvis by
# default (idle / crouch / aim / on-spot animations: SA root bone is
# expected to stay at world origin, the actual body movement comes
# from Pelvis). Switch to the topmost bone with the Scene flag
# ``gtatools_ik_root_motion`` for walk/run/jump where root carries
# world translation.
_SA_PELVIS_BONES = [
    ("root", [" Pelvis", "Pelvis", "Bip01 Pelvis"]),
]
_SA_ROOT_BONES = [
    ("root", [" Normal", "Normal", " Bip01", "Bip01", " Root", "Root"]),
]

_IK_FLAG = "inu_ik_rigged"
_CTRL_FLAG = "inu_ik_control"
# Type tag stored on every control bone — read by the size slider
# and the per-group visibility checkboxes so they can scope their
# action to the matching subset (chain / pole / rot / root).
_CTRL_TYPE = "inu_ik_ctrl_type"

# Bone collection names per control type — modern Blender 4+ uses
# bone collections for visibility toggling, more reliable than the
# legacy ``Bone.hide`` flag. Names are exposed in the armature data
# panel (Properties → Object Data Properties → Bone Collections).
_IK_COLL_CHAIN = "INU_IK_Chain"
_IK_COLL_POLE = "INU_IK_Pole"
_IK_COLL_ROT = "INU_IK_Rot"
_IK_COLL_ROOT = "INU_IK_Root"
_WIDGET_MESH_NAME = "INU_IK_Widget_Cube"
_WIDGET_COLLECTION = "INU_IK_Widgets"


def _ensure_widget_mesh():
    """Wireframe-only cube used as custom_shape for every IK control
    bone. Edges-only mesh draws as a transparent box outline — clean
    silhouette that the user can grab in the viewport without the
    stock octahedron getting in the way of the character mesh.

    Lives in a hidden collection ``INU_IK_Widgets`` so it doesn't
    clutter the outliner; reused across multiple Add IK Rig runs."""
    obj = bpy.data.objects.get(_WIDGET_MESH_NAME)
    if obj is not None:
        return obj

    verts = [
        (-0.5, -0.5, -0.5), (+0.5, -0.5, -0.5),
        (+0.5, +0.5, -0.5), (-0.5, +0.5, -0.5),
        (-0.5, -0.5, +0.5), (+0.5, -0.5, +0.5),
        (+0.5, +0.5, +0.5), (-0.5, +0.5, +0.5),
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # bottom
        (4, 5), (5, 6), (6, 7), (7, 4),  # top
        (0, 4), (1, 5), (2, 6), (3, 7),  # verticals
    ]
    mesh = bpy.data.meshes.new(_WIDGET_MESH_NAME + "_mesh")
    mesh.from_pydata(verts, edges, [])
    mesh.update()

    obj = bpy.data.objects.new(_WIDGET_MESH_NAME, mesh)

    coll = bpy.data.collections.get(_WIDGET_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(_WIDGET_COLLECTION)
        bpy.context.scene.collection.children.link(coll)
        # Hide the whole collection from viewport / render so the
        # widget cube never appears as a selectable scene object.
        layer_coll = bpy.context.view_layer.layer_collection.children.get(
            _WIDGET_COLLECTION)
        if layer_coll is not None:
            layer_coll.hide_viewport = True
        coll.hide_render = True
    coll.objects.link(obj)
    obj.hide_render = True

    return obj

# Legacy support: the previous (empty-based) version of this file
# created Empty objects flagged ``inu_ik_widget`` inside a scene
# collection ``INU_IK_Rig``. We still scrub those on Bake & Clear
# so saves written under the old version aren't left orphaned.
_LEGACY_WIDGET_FLAG = "inu_ik_widget"
_LEGACY_COLLECTION = "INU_IK_Rig"

# Kept so __init__.py's display-preference enum still registers; the
# bone-based rig doesn't honour these values, the prop is now
# essentially decorative until/if we re-introduce a visual style
# selector.
EMPTY_TYPES = [
    ('SPHERE', 'Sphere', "Сфера"),
    ('CUBE', 'Cube', "Куб"),
    ('PLAIN_AXES', 'Plain Axes', "Тройка осей"),
    ('CONE', 'Cone', "Конус"),
    ('SINGLE_ARROW', 'Arrow', "Стрелка"),
    ('CIRCLE', 'Circle', "Круг"),
]


def _resolve_bone(armature, name):
    pb = armature.pose.bones.get(name)
    if pb is None:
        pb = armature.pose.bones.get(name.lstrip())
    return pb


def _chain_direction(start_head, tip_head):
    """Unit vector from chain root toward chain tip (used to
    visually orient the elbow / knee marker bone)."""
    v = tip_head - start_head
    if v.length < 1e-6:
        return mathutils.Vector((0.0, 0.0, 1.0))
    return v.normalized()


# Canonical rest pose applied to deform bones BEFORE the IK pipeline
# runs, but only when the armature has zero animation keys. The
# rotations break the IK-plane degeneracy that an unposed straight
# rest chain would otherwise have — pole_angle calibration converges
# on the correct bend side because the chain isn't a flat line at
# calibration time. Captured by INU via the dev-side pose-dump
# script. Bone names use SA's leading-space convention; _resolve_bone
# strips leading whitespace as a fallback so either form works.
_REST_POSE = {
    'Root': {'rot': (1.0, -0.0, 0.0, -0.0),
             'loc': (-0.020707, -0.003663, -0.0)},
    ' Pelvis': (0.0, -0.99844, 0.0, 0.05583),
    ' Spine': (0.999639, 0.002941, 0.020998, -0.016513),
    ' Spine1': (0.997566, 0.010012, 0.052992, 0.044201),
    ' Neck': (0.999011, -0.031481, -0.014937, 0.027637),
    ' Head': (0.9959, 0.054052, 0.07132, 0.013226),
    'Jaw': (0.999985, -0.0, 1e-06, 0.005395),
    'L Brow': (0.99999, 0.002968, -0.000428, 0.003353),
    'R Brow': (0.999852, 0.015993, 0.00163, 0.006155),
    'Bip01 L Clavicle': (0.994921, -0.034688, 0.047642, 0.081598),
    ' L UpperArm': (0.966937, 0.228035, 0.095553, -0.062474),
    ' L ForeArm': (0.993836, -0.0, 1e-06, -0.11086),
    ' L Hand': (0.992712, 0.083451, -0.079519, -0.035149),
    ' L Finger': (0.962828, 0.000131, -0.000125, 0.270116),
    'L Finger01': (0.920734, -0.0, -0.0, 0.39019),
    'Bip01 R Clavicle': (0.994677, 0.02799, -0.095563, 0.026479),
    ' R UpperArm': (0.982845, -0.168682, -0.06244, -0.04078),
    ' R ForeArm': (0.998923, -0.0, 1e-06, -0.046393),
    ' R Hand': (0.993859, 0.063271, 0.077838, 0.046712),
    ' R Finger': (0.825937, 0.013055, -0.012764, 0.563467),
    'R Finger01': (0.918711, 0.0, -0.0, 0.39493),
    'L breast': (1.0, -0.000183, -0.000103, -9.6e-05),
    'R breast': (1.0, 0.000119, 4.1e-05, 5.2e-05),
    'Belly': (1.0, -0.0, 1e-06, -2.8e-05),
    ' L Thigh': (0.981469, -0.125843, 0.042563, 0.138094),
    ' L Calf': (0.971695, -0.0, -0.0, -0.236239),
    ' L Foot': (0.993511, -0.074613, -0.003255, 0.085776),
    ' L Toe0': (0.999789, 0.000345, 0.000345, 0.020545),
    ' R Thigh': (0.988712, 0.082174, 0.098286, 0.077688),
    ' R Calf': (0.98751, 0.0, -0.0, -0.157559),
    ' R Foot': (0.993469, 0.061039, -0.060722, 0.074878),
    ' R Toe0': (1.0, 0.0, -0.0, 0.000345),
}


def _flip_armature_facing(armature):
    """Compose an extra 180° rotation around the (1, 0, 1) axis onto
    the armature object's existing rotation. Only called from Phase 0
    of Add IK Rig, alongside _apply_rest_pose, so it never fires on
    armatures that already carry FK animation.

    Why object-level (not bone-level): SA peds come out of DFF
    import lying on their X-up rest, and the canonical _REST_POSE
    stands them up via Pelvis basis. After standing, the body still
    faces an axis Blender treats as «back» rather than «front» —
    rotating the OBJECT lets us correct that without untangling
    Pelvis bone-rest conventions. Tweak the angle / axis below if
    a future ped variant needs different alignment."""
    flip = mathutils.Quaternion(
        (1.0, 0.0, 1.0), math.radians(180.0))

    if armature.rotation_mode == 'QUATERNION':
        cur = mathutils.Quaternion(armature.rotation_quaternion)
        new = flip @ cur
        armature.rotation_quaternion = new
    elif armature.rotation_mode == 'AXIS_ANGLE':
        aa = armature.rotation_axis_angle
        cur = mathutils.Quaternion((aa[1], aa[2], aa[3]), aa[0])
        new = flip @ cur
        axis, angle = new.to_axis_angle()
        armature.rotation_axis_angle = (
            angle, axis.x, axis.y, axis.z)
    else:
        cur_q = armature.rotation_euler.to_quaternion()
        new_q = flip @ cur_q
        armature.rotation_euler = new_q.to_euler(
            armature.rotation_mode)


def _armature_has_any_keys(armature):
    """True if the armature carries an Action with at least one
    pose-bone keyframe. Used to gate the rest-pose pre-step in Add
    IK Rig — overlaying a 32-bone canonical pose on top of an
    existing FK animation would silently retarget / clobber it,
    so we only stamp keys on a clean rig."""
    ad = armature.animation_data
    if ad is None or ad.action is None:
        return False
    for fc in _iter_action_fcurves(ad.action):
        if fc.data_path.startswith('pose.bones['):
            if len(fc.keyframe_points) > 0:
                return True
    return False


def _apply_rest_pose(armature, frame=0):
    """Write _REST_POSE values to deform bones that are still at
    near-identity rotation, then keyframe them at ``frame`` so the
    pose persists across action evaluation / save+reload / timeline
    scrub. Bones already rotated (|q.w| < 0.999, ~5°+) are skipped —
    the caller still gates this whole function on
    _armature_has_any_keys so existing FK actions never reach here.

    Returns the list of bone names that were updated."""
    applied = []
    for bone_name, data in _REST_POSE.items():
        pb = _resolve_bone(armature, bone_name)
        if pb is None:
            continue

        if pb.rotation_mode == 'QUATERNION':
            q_now = pb.rotation_quaternion
        else:
            q_now = pb.matrix_basis.to_quaternion()
        if abs(q_now.w) < 0.999:
            continue

        if isinstance(data, dict):
            rot = data.get('rot')
            loc = data.get('loc')
        else:
            rot = data
            loc = None

        if rot is not None:
            q = mathutils.Quaternion(rot)
            if pb.rotation_mode == 'QUATERNION':
                pb.rotation_quaternion = q
            elif pb.rotation_mode == 'AXIS_ANGLE':
                axis, angle = q.to_axis_angle()
                pb.rotation_axis_angle = (
                    angle, axis.x, axis.y, axis.z)
            else:
                pb.rotation_euler = q.to_euler(pb.rotation_mode)

        if loc is not None:
            pb.location = loc

        try:
            if pb.rotation_mode == 'QUATERNION':
                pb.keyframe_insert(
                    'rotation_quaternion', frame=frame)
            elif pb.rotation_mode == 'AXIS_ANGLE':
                pb.keyframe_insert(
                    'rotation_axis_angle', frame=frame)
            else:
                pb.keyframe_insert('rotation_euler', frame=frame)
        except Exception:
            pass
        if loc is not None:
            try:
                pb.keyframe_insert('location', frame=frame)
            except Exception:
                pass

        applied.append(pb.name)
    return applied


def _resolve_bone_alt(armature, candidates):
    for n in candidates:
        pb = armature.pose.bones.get(n)
        if pb is not None:
            return pb
        pb = armature.pose.bones.get(n.lstrip())
        if pb is not None:
            return pb
    return None


def _iter_action_fcurves(action):
    if hasattr(action, 'fcurves') and action.fcurves:
        for fc in action.fcurves:
            yield fc
    for layer in getattr(action, 'layers', []):
        for strip in getattr(layer, 'strips', []):
            cbs = getattr(strip, 'channelbags', None)
            if cbs is None:
                continue
            for cb in cbs:
                if cb is None:
                    continue
                for fc in getattr(cb, 'fcurves', []):
                    yield fc


def _simplify_action(action, threshold=0.0001):
    total = 0
    for fc in _iter_action_fcurves(action):
        pts = fc.keyframe_points
        n = len(pts)
        if n < 2:
            continue

        # Constant-curve case: nla.bake with step=1 keys EVERY frame,
        # so a single-keyframe Action becomes ~60 redundant keys after
        # bake. If the whole fcurve fits inside `threshold` we keep
        # just the first key.
        ys = [kp.co[1] for kp in pts]
        if (max(ys) - min(ys)) <= threshold:
            for kp in list(pts)[1:]:
                try:
                    pts.remove(kp, fast=True)
                    total += 1
                except Exception:
                    pass
            try:
                fc.update()
            except Exception:
                pass
            continue

        if n < 3:
            continue
        to_remove = []
        for i in range(1, n - 1):
            prev = pts[i - 1].co
            curr = pts[i].co
            nxt = pts[i + 1].co
            span = nxt.x - prev.x
            if span <= 0.0:
                continue
            t = (curr.x - prev.x) / span
            interp = prev.y + t * (nxt.y - prev.y)
            if abs(curr.y - interp) <= threshold:
                to_remove.append(pts[i])
        for kp in to_remove:
            try:
                pts.remove(kp, fast=True)
                total += 1
            except Exception:
                pass
        try:
            fc.update()
        except Exception:
            pass
    return total


def _visual_key_deform_bones(armature, frame):
    """Snap each deform pose-bone's matrix_basis to its current
    visual pose (after IK / Copy Rotation evaluation) and keyframe.
    Capture all visuals first so editing one bone's basis doesn't
    contaminate the matrices we're about to read for its children.
    Skips bones flagged ``inu_ik_control`` — those are the rig
    helpers, not part of the exported animation.

    The basis is decomposed explicitly into location / rotation /
    scale and written to the matching pose-bone properties before
    keyframe_insert. Earlier code relied on ``matrix_basis`` setter
    propagating to ``rotation_quaternion`` etc. — in practice this
    silently dropped the IK rotation on some Blender versions, so
    keyframe_insert captured the pre-write basis and the bake came
    out as the original FK pose minus the IK overlay."""
    visuals = {pb.name: pb.matrix.copy() for pb in armature.pose.bones}
    for pb in armature.pose.bones:
        db = armature.data.bones.get(pb.name)
        if db is not None and db.get(_CTRL_FLAG):
            continue
        visual = visuals[pb.name]
        bone = pb.bone
        if pb.parent:
            parent_visual = visuals.get(pb.parent.name, pb.parent.matrix)
            local_rest = (pb.parent.bone.matrix_local.inverted()
                          @ bone.matrix_local)
            basis = (local_rest.inverted()
                     @ parent_visual.inverted() @ visual)
        else:
            basis = bone.matrix_local.inverted() @ visual

        loc, rot_q, scl = basis.decompose()
        pb.location = loc
        if pb.rotation_mode == 'QUATERNION':
            pb.rotation_quaternion = rot_q
        elif pb.rotation_mode == 'AXIS_ANGLE':
            axis, angle = rot_q.to_axis_angle()
            pb.rotation_axis_angle = (angle, axis.x, axis.y, axis.z)
        else:
            pb.rotation_euler = rot_q.to_euler(pb.rotation_mode)
        pb.scale = scl

        try:
            if pb.rotation_mode == 'QUATERNION':
                pb.keyframe_insert('rotation_quaternion', frame=frame)
            elif pb.rotation_mode == 'AXIS_ANGLE':
                pb.keyframe_insert('rotation_axis_angle', frame=frame)
            else:
                pb.keyframe_insert('rotation_euler', frame=frame)
        except Exception:
            pass
        try:
            pb.keyframe_insert('location', frame=frame)
        except Exception:
            pass


def _sample_basis_for_bake(context, armature, frames):
    """Walk ``frames`` and capture every non-control deform bone's
    visual basis as ``(loc, rot_quaternion)`` pairs.

    Returns ``{bone_name: [(frame, loc, rot_q), ...]}``.

    The sampling runs with IK constraints still active so the
    captured visual matrices reflect the IK-driven pose. The caller
    is expected to remove the constraints AFTER sampling and BEFORE
    writing the basis values back via ``_write_basis_keyframes``.

    Mirrors ``ifp_export._sample_post_ik_pose`` so Bake & Clear and
    IFP-export-with-active-rig produce identical bone trajectories.
    """
    samples = {}
    if not frames:
        return samples
    scene = context.scene
    saved_frame = scene.frame_current
    try:
        for f in frames:
            f_int = int(round(f))
            scene.frame_set(f_int)
            context.view_layer.update()
            visuals = {pb.name: pb.matrix.copy()
                       for pb in armature.pose.bones}
            for pb in armature.pose.bones:
                db = armature.data.bones.get(pb.name)
                if db is None or db.get(_CTRL_FLAG):
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
                    basis = (pb.bone.matrix_local.inverted()
                             @ visual)
                loc, rot_q, _scl = basis.decompose()
                samples.setdefault(pb.name, []).append(
                    (f_int, loc, rot_q))
    finally:
        scene.frame_set(saved_frame)
        context.view_layer.update()
    return samples


def _write_basis_keyframes(armature, samples):
    """Write the captured basis samples back to the deform bones as
    location + rotation keyframes. Run AFTER IK / Copy constraints
    have been stripped so nothing overrides the values we write.

    Property assignment is explicit (`pb.location = loc`,
    `pb.rotation_quaternion = rot_q`) instead of going through the
    ``matrix_basis`` setter — earlier visual-key code relied on the
    setter propagating values to the rotation/location properties,
    which silently failed on some Blender versions and made the
    keyframes capture stale FK rotations.

    Per-bone hemisphere continuity: ``matrix.decompose()`` returns a
    valid quaternion but doesn't pick a hemisphere consistent with
    the previous frame's sample. Without the dot-flip below, two
    consecutive samples can land on opposite hemispheres (q vs -q,
    same rotation) and the engine / Blender interpolates the long
    way through 360°. Flipping `rot_q` sign when `dot(prev, cur) < 0`
    keeps the chain on a single hemisphere — same fix as the
    quaternion-sign-discontinuity script users had to run manually
    after Bake & Clear."""
    for bone_name, sample_list in samples.items():
        pb = armature.pose.bones.get(bone_name)
        if pb is None:
            continue
        prev_rot_q = None
        for f, loc, rot_q in sample_list:
            if prev_rot_q is not None and rot_q.dot(prev_rot_q) < 0:
                rot_q = mathutils.Quaternion(
                    (-rot_q.w, -rot_q.x, -rot_q.y, -rot_q.z))
            prev_rot_q = rot_q

            pb.location = loc
            if pb.rotation_mode == 'QUATERNION':
                pb.rotation_quaternion = rot_q
            elif pb.rotation_mode == 'AXIS_ANGLE':
                axis, angle = rot_q.to_axis_angle()
                pb.rotation_axis_angle = (
                    angle, axis.x, axis.y, axis.z)
            else:
                pb.rotation_euler = rot_q.to_euler(pb.rotation_mode)
            try:
                pb.keyframe_insert('location', frame=f)
            except Exception:
                pass
            try:
                if pb.rotation_mode == 'QUATERNION':
                    pb.keyframe_insert(
                        'rotation_quaternion', frame=f)
                elif pb.rotation_mode == 'AXIS_ANGLE':
                    pb.keyframe_insert(
                        'rotation_axis_angle', frame=f)
                else:
                    pb.keyframe_insert(
                        'rotation_euler', frame=f)
            except Exception:
                pass


def _strip_fcurves_for_bones(action, bone_names):
    """Drop every fcurve in `action` referencing one of `bone_names`.
    Walks both legacy ``action.fcurves`` and Blender 5.x layered
    ``channelbag.fcurves``. Used after Bake & Clear removes the IK
    control bones — without this step their stale rotation/location
    fcurves linger in the Action and would clutter Graph Editor /
    fail validation in IFP export."""
    bone_names = set(bone_names)

    def _bone_of(fc):
        if not fc.data_path.startswith('pose.bones['):
            return None
        parts = fc.data_path.split('"')
        if len(parts) < 2:
            return None
        return parts[1]

    if hasattr(action, 'fcurves'):
        for fc in list(action.fcurves):
            if _bone_of(fc) in bone_names:
                try:
                    action.fcurves.remove(fc)
                except Exception:
                    pass

    for layer in getattr(action, 'layers', []) or []:
        for strip in getattr(layer, 'strips', []) or []:
            cbs = getattr(strip, 'channelbags', None) or []
            for cb in cbs:
                if cb is None:
                    continue
                for fc in list(cb.fcurves):
                    if _bone_of(fc) in bone_names:
                        try:
                            cb.fcurves.remove(fc)
                        except Exception:
                            pass


class GTATOOLS_OT_add_ik_rig(bpy.types.Operator):
    """Накинуть bone-based IK на стандартные цепочки SA-педа.
    Создаёт non-deform контрольные кости внутри армча: запястья,
    ступни, голову и корень. На deform-кости — IK-constraint и
    Copy Rotation/Location, target — соответствующая control-кость.
    Контроллы окрашены зелёным (THEME09). Перед Export IFP — Bake
    & Clear IK, которая всё снимет и удалит control-кости."""
    bl_idname = "gtatools.add_ik_rig"
    bl_label = "INU: Add IK Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'ARMATURE'
                and not obj.get(_IK_FLAG))

    def execute(self, context):
        armature = context.active_object
        scene = context.scene

        context.view_layer.update()

        # ── Phase 0 ──────────────────────────────────────────────
        # On a freshly imported ped (zero animation keys), apply the
        # canonical rest pose to the deform bones, keyframe it at
        # frame 0, and reorient the armature object so the character
        # ends up facing Blender's front. Without this step the IK
        # chain calibration in Phase 3 would run on a perfectly
        # straight chain — the IK plane is degenerate there,
        # brute-force pole_angle converges on an arbitrary angle,
        # and the limb bends the wrong way the moment the user
        # drags an IK target. Armatures that already carry FK keys
        # are LEFT ALONE — the existing animation provides a non-
        # degenerate reference pose, so calibration converges
        # naturally and we must not overwrite the user's keys.
        if not _armature_has_any_keys(armature):
            if _apply_rest_pose(armature, frame=0):
                context.view_layer.update()
                _flip_armature_facing(armature)
                context.view_layer.update()

        # ── Phase 1 ──────────────────────────────────────────────
        # Capture current-pose target positions in armature-local
        # space. Reading pose_bone.tail/head returns pose-evaluated
        # values, so this gives the place we want each control bone
        # to spawn at. Done BEFORE switching to Edit Mode, where
        # pose evaluation isn't available.
        chain_targets = {}
        for chain_name, names in _SA_CHAINS:
            start_pb = _resolve_bone(armature, names[0])
            mid_pb = _resolve_bone(armature, names[1])
            tip_pb = _resolve_bone(armature, names[-1])
            if start_pb is None or mid_pb is None or tip_pb is None:
                continue
            # Use POSE positions (pose_bone.head/.tail) — for SA peds
            # the rest data is laid out with X=up convention, but the
            # visible character is upright because the user's FK
            # action rotates the whole skeleton via Root. data.bones
            # head_local would put the pole at the rest "lying-flat"
            # position rather than where the joint currently appears
            # in the viewport.
            chain_targets[chain_name] = {
                'tip_tail_local':   tip_pb.tail.copy(),
                'tip_bone_name':    tip_pb.name,
                'mid_bone_name':    mid_pb.name,
                'start_head_rest':  start_pb.head.copy(),
                'mid_head_rest':    mid_pb.head.copy(),
                'tip_head_rest':    tip_pb.head.copy(),
                'chain_len':        len(names),
            }

        # All Copy-Rotation single-bone controls (head + torso).
        # We collect a LIST so each rest-pose target gets its own
        # control bone — the panel previously hardcoded just the
        # head, but spine1 needs the same treatment for upper-body
        # twisting.
        rot_targets = []
        for ctrl_name, candidates in _SA_ROT_BONES:
            pb = _resolve_bone_alt(armature, candidates)
            if pb is not None:
                rot_targets.append({
                    'tail_local': pb.tail.copy(),
                    'bone_name':  pb.name,
                    'ctrl_name':  ctrl_name,
                })

        root_target = None
        ik_root_lookup = (_SA_ROOT_BONES
                          if getattr(scene.inu_settings, 'gtatools_ik_root_motion', False)
                          else _SA_PELVIS_BONES)
        for ctrl_name, candidates in ik_root_lookup:
            pb = _resolve_bone_alt(armature, candidates)
            if pb is not None:
                root_target = {
                    'head_local': pb.head.copy(),
                    'bone_name':  pb.name,
                    'ctrl_name':  ctrl_name,
                }
                break

        # ── Phase 1b ─────────────────────────────────────────────
        # If the user already has a keyed Action on this armature,
        # sample the deform bones' FK pose at every keyed frame
        # BEFORE we add any IK constraints. Stash one armature-space
        # matrix per (control bone, frame). Phase 5 below will write
        # those matrices back as control-bone keyframes so the IK
        # rig reproduces the original animation 1:1 on play. Without
        # this step, Copy Rotation / Copy Location override the
        # FK keys and the character freezes in the rest pose.
        action = (armature.animation_data.action
                  if armature.animation_data else None)
        deform_keyed_frames = set()
        if action is not None:
            armature_bone_names = {b.name for b in armature.data.bones}
            for fc in _iter_action_fcurves(action):
                if not fc.data_path.startswith('pose.bones['):
                    continue
                parts = fc.data_path.split('"')
                if len(parts) < 2:
                    continue
                if parts[1] in armature_bone_names:
                    for kp in fc.keyframe_points:
                        deform_keyed_frames.add(int(round(kp.co[0])))

        fk_samples = {}  # ctrl_name -> list of (frame, armature-space matrix)
        # Pole bones (elbow/knee) need location-only keyframes —
        # pole_angle is calibrated once at rest, so as long as the
        # pole tracks the mid bone's head every keyed frame, the IK
        # plane stays consistent with the FK pose. Without this the
        # pole sits at REST elbow position while the body animates,
        # IK reconstructs a wrong chain plane and the limb twists.
        pole_loc_samples = {}  # ctrl_name -> [(frame, armature head pos)]
        if deform_keyed_frames:
            saved_frame = scene.frame_current
            try:
                for f in sorted(deform_keyed_frames):
                    scene.frame_set(f)
                    for chain_name, names in _SA_CHAINS:
                        start_pb = _resolve_bone(armature, names[0])
                        mid_pb = _resolve_bone(armature, names[1])
                        tip_pb = _resolve_bone(armature, names[-1])
                        if (start_pb is None or mid_pb is None
                                or tip_pb is None):
                            continue
                        # Control bone's rest HEAD sits at tip.tail —
                        # so the matrix we want for the control
                        # is Translation(tip.tail) × Rotation(tip).
                        tail_arm = tip_pb.tail.copy()
                        rot_arm = tip_pb.matrix.to_3x3().to_4x4()
                        target = (mathutils.Matrix.Translation(tail_arm)
                                  @ rot_arm)
                        fk_samples.setdefault(
                            f"INU_IK_{chain_name}", []
                        ).append((f, target))
                        # Pole tracks the elbow/knee head — sampled
                        # in armature space, baked as location-only.
                        pole_loc_samples.setdefault(
                            f"INU_IK_{chain_name}_pole", []
                        ).append((f, mid_pb.head.copy()))

                    for rt in rot_targets:
                        pb = armature.pose.bones.get(rt['bone_name'])
                        if pb is not None:
                            tail_arm = pb.tail.copy()
                            rot_arm = pb.matrix.to_3x3().to_4x4()
                            target = (mathutils.Matrix.Translation(tail_arm)
                                      @ rot_arm)
                            fk_samples.setdefault(
                                f"INU_IK_{rt['ctrl_name']}", []
                            ).append((f, target))

                    if root_target is not None:
                        pb = armature.pose.bones.get(root_target['bone_name'])
                        if pb is not None:
                            head_arm = pb.head.copy()
                            rot_arm = pb.matrix.to_3x3().to_4x4()
                            target = (mathutils.Matrix.Translation(head_arm)
                                      @ rot_arm)
                            fk_samples.setdefault(
                                f"INU_IK_{root_target['ctrl_name']}", []
                            ).append((f, target))
            finally:
                scene.frame_set(saved_frame)

        # ── Phase 2 ──────────────────────────────────────────────
        # Create the control bones in Edit Mode. Each is non-deform,
        # parentless, marked with ``inu_ik_control`` so Bake & Clear
        # and IFP-export can identify and skip them.
        prev_mode = armature.mode
        if prev_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        eb = armature.data.edit_bones

        offset = mathutils.Vector((0.0, 0.0, 0.1))   # 10 cm up
        big_offset = mathutils.Vector((0.0, 0.0, 0.2))  # 20 cm up
        created = []

        for chain_name, t in chain_targets.items():
            ctrl_name = f"INU_IK_{chain_name}"
            if ctrl_name not in eb:
                b = eb.new(ctrl_name)
                b.head = t['tip_tail_local']
                b.tail = t['tip_tail_local'] + offset
                b.use_deform = False
                b.use_connect = False
                b.parent = None
                b[_CTRL_FLAG] = 1
                b[_CTRL_TYPE] = 'chain'
                created.append(
                    (ctrl_name, 'chain', t['tip_bone_name'],
                     t['chain_len']))

            # Elbow / knee VISUAL marker — placed AT the joint
            # (mid bone's rest head), tail extended along the chain
            # direction so the bone visually points down the
            # forearm / shin. Sits exactly on the joint regardless
            # of armature world rotation. Not wired to the IK
            # constraint's pole_target — that requires pole_angle
            # calibration which collapsed the rig last time. This
            # is purely a green selectable indicator.
            pole_name = f"INU_IK_{chain_name}_pole"
            if pole_name not in eb:
                chain_dir = _chain_direction(
                    t['start_head_rest'], t['tip_head_rest'])
                head_pos = t['mid_head_rest']
                pb_eb = eb.new(pole_name)
                pb_eb.head = head_pos
                pb_eb.tail = head_pos + chain_dir * 0.10
                pb_eb.use_deform = False
                pb_eb.use_connect = False
                pb_eb.parent = None
                pb_eb[_CTRL_FLAG] = 1
                pb_eb[_CTRL_TYPE] = 'pole'
                created.append(
                    (pole_name, 'pole', t['mid_bone_name'], 0))

        # Single-bone Copy-Rotation controls (head, spine1, R/L
        # shoulder). Parentless.
        #
        # CRITICAL: copy deform's head, tail, AND roll **exactly**
        # so ``matrix_local`` is bit-identical between control and
        # deform. Earlier "near-match" approaches (dir_vec + roll
        # vs matrix-set + tail-fix) produced subtle rotation
        # offsets — Phase 5 had to compensate via a non-identity
        # basis, and Copy Rotation (WORLD/WORLD) inherited the
        # offset, yanking the deform 90°+ on add.
        #
        # Visual positioning is moved to ``custom_shape_translation``
        # in Phase 4 — the bone math sits at deform's rest, the
        # cube renders wherever we want without affecting the
        # constraint result.
        for rt in rot_targets:
            ctrl_name = f"INU_IK_{rt['ctrl_name']}"
            if ctrl_name not in eb:
                deform_eb = eb.get(rt['bone_name'])
                b = eb.new(ctrl_name)
                if deform_eb is not None:
                    b.head = deform_eb.head.copy()
                    b.tail = deform_eb.tail.copy()
                    b.roll = deform_eb.roll
                else:
                    b.head = rt['tail_local']
                    b.tail = rt['tail_local'] + offset
                b.use_deform = False
                b.use_connect = False
                b.parent = None
                b[_CTRL_FLAG] = 1
                b[_CTRL_TYPE] = 'rot'
                created.append(
                    (ctrl_name, 'rot', rt['bone_name'], 0))

        if root_target is not None:
            ctrl_name = f"INU_IK_{root_target['ctrl_name']}"
            if ctrl_name not in eb:
                b = eb.new(ctrl_name)
                b.head = root_target['head_local']
                b.tail = root_target['head_local'] + big_offset
                b.use_deform = False
                b.use_connect = False
                b.parent = None
                b[_CTRL_FLAG] = 1
                b[_CTRL_TYPE] = 'root'
                created.append(
                    (ctrl_name, 'root', root_target['bone_name'], 0))

        # ── Phase 3 ──────────────────────────────────────────────
        # Pose Mode: hook constraints between deform bones and our
        # newly created control bones (target=armature, subtarget=
        # bone-name). World-space copy keeps math simple — we don't
        # have to rotate-match the rest of the chain.
        bpy.ops.object.mode_set(mode='POSE')

        added_chains = 0
        added_rot = 0
        added_root = 0
        added_poles = 0
        skipped = []

        for ctrl_name, ctrl_type, deform_bone, chain_len in created:
            if ctrl_type == 'pole':
                # Visual-only marker: no constraints. Counted just
                # for the report message.
                added_poles += 1
                continue

            deform_pb = armature.pose.bones.get(deform_bone)
            if deform_pb is None:
                skipped.append(deform_bone)
                continue

            if ctrl_type == 'chain':
                if any(c.type == 'IK' for c in deform_pb.constraints):
                    continue
                ik = deform_pb.constraints.new('IK')
                ik.name = f"INU_IK_{ctrl_name}_ik"
                ik.target = armature
                ik.subtarget = ctrl_name
                ik.chain_count = chain_len
                ik.use_rotation = False

                # Wire elbow / knee pole and calibrate pole_angle.
                # Without calibration the chain twists by an
                # arbitrary amount (SA bone roll != Blender's
                # default pole convention) and the rig collapses
                # on add. We sweep the angle to find the one that
                # makes the IK chain reproduce the FK tip + mid
                # positions captured in Phase 1.
                chain_short = ctrl_name[len("INU_IK_"):]
                pole_name = f"INU_IK_{chain_short}_pole"
                chain_data = chain_targets.get(chain_short, {})
                target_tip = chain_data.get('tip_tail_local')
                target_mid = chain_data.get('mid_head_rest')
                mid_name = chain_data.get('mid_bone_name')
                mid_pb = (armature.pose.bones.get(mid_name)
                          if mid_name else None)
                if (pole_name in armature.pose.bones
                        and target_tip is not None
                        and target_mid is not None
                        and mid_pb is not None):
                    ik.pole_target = armature
                    ik.pole_subtarget = pole_name
                    _calibrate_pole_angle(
                        context, ik, deform_pb,
                        target_tip, mid_pb, target_mid)

                cr = deform_pb.constraints.new('COPY_ROTATION')
                cr.name = f"INU_IK_{ctrl_name}_rot"
                cr.target = armature
                cr.subtarget = ctrl_name
                cr.target_space = 'WORLD'
                cr.owner_space = 'WORLD'
                added_chains += 1

                # Floor for legs: foot IK target can't sink below
                # the ground plane. Blender's FLOOR constraint
                # references an object — if INU_Ground (the
                # texture plane the user can spawn via "Add
                # Ground Plane") already exists, we wire it as
                # the target. Otherwise the constraint stays
                # in place with target=None (inactive); when the
                # user later runs Add Ground Plane, that operator
                # patches every existing INU_IK_*_floor to point
                # at the new plane.
                if chain_short.endswith('_leg'):
                    ctrl_pb_for_floor = armature.pose.bones.get(ctrl_name)
                    if ctrl_pb_for_floor is not None:
                        floor = ctrl_pb_for_floor.constraints.new(
                            'FLOOR')
                        floor.name = f"INU_IK_{ctrl_name}_floor"
                        floor.floor_location = 'FLOOR_Z'
                        # Offset reads from the scene-level
                        # ``gtatools_floor_offset`` slider so the
                        # user can tune it from the panel — the
                        # update callback there propagates new
                        # values to every existing foot Floor.
                        floor.offset = float(getattr(
                            scene, 'gtatools_floor_offset', 0.05))
                        floor.target = bpy.data.objects.get(
                            _GROUND_OBJ_NAME)

            elif ctrl_type == 'rot' or ctrl_type == 'head':
                # Cube position follows deform via the
                # frame-change/depsgraph HANDLER (not via Copy
                # Location constraint). Constraint-based linking
                # would create a depsgraph cycle: Copy Loc on the
                # cube reads deform.pos, Copy Rot on the deform
                # reads cube.rot, → Blender uses cached/previous-
                # frame values and right-click cancel during a
                # rotate transform leaves the deform stuck at the
                # last value. Handler-based position update
                # writes cube.location AFTER pose eval, breaking
                # the cycle cleanly.
                #
                # Deform rotation IS driven by the cube via Copy
                # Rotation (REPLACE / WORLD/WORLD).
                tag = f"INU_IK_{ctrl_name}_rot"
                if not any(c.name == tag for c in deform_pb.constraints):
                    cr = deform_pb.constraints.new('COPY_ROTATION')
                    cr.name = tag
                    cr.target = armature
                    cr.subtarget = ctrl_name
                    cr.target_space = 'WORLD'
                    cr.owner_space = 'WORLD'
                    added_rot += 1

                # Tell the handler to peg this cube's location to
                # the deform bone's pose head every depsgraph
                # update. Offset = (0,0,0) in deform-local means
                # "head of deform" → cube head sits exactly where
                # deform's head sits.
                db_ctrl = armature.data.bones.get(ctrl_name)
                if db_ctrl is not None:
                    db_ctrl['inu_ik_follow_parent'] = deform_bone
                    db_ctrl['inu_ik_follow_offset'] = [0.0, 0.0, 0.0]

            elif ctrl_type == 'root':
                if any(c.name.startswith('INU_IK_root')
                       for c in deform_pb.constraints):
                    continue
                cl = deform_pb.constraints.new('COPY_LOCATION')
                cl.name = f"INU_IK_{ctrl_name}_loc"
                cl.target = armature
                cl.subtarget = ctrl_name
                cl.target_space = 'WORLD'
                cl.owner_space = 'WORLD'

                cr = deform_pb.constraints.new('COPY_ROTATION')
                cr.name = f"INU_IK_{ctrl_name}_rot"
                cr.target = armature
                cr.subtarget = ctrl_name
                cr.target_space = 'WORLD'
                cr.owner_space = 'WORLD'
                added_root += 1

        # ── Phase 4 ──────────────────────────────────────────────
        # Visual setup: tint control bones green, replace their stock
        # octahedron display with a wireframe-cube custom shape so
        # they read as "transparent boxes" in the viewport instead
        # of the chunky default. ``use_custom_shape_bone_size=False``
        # decouples shape size from bone length — without it the cube
        # scales with the rest-bone length (5–20cm here) and gets
        # weirdly thin. Per-control sizes chosen for readability:
        #   * chain / head — 8 cm cube
        #   * pole         — 4 cm cube (smaller, sub-control)
        #   * root         — 16 cm cube (master, biggest)
        widget_mesh = _ensure_widget_mesh()
        size_mult = float(getattr(scene.inu_settings, 'gtatools_ik_size', 1.0))
        size_by_type = {
            'chain': 0.08 * size_mult,
            'head':  0.08 * size_mult,
            'rot':   0.08 * size_mult,
            'pole':  0.04 * size_mult,
            'root':  0.16 * size_mult,
        }
        ik_color = tuple(getattr(
            scene, 'gtatools_ik_color',
            (0.0, 1.0, 0.0, 1.0)))[:3]
        for ctrl_name, ctrl_type, _, _ in created:
            pb = armature.pose.bones.get(ctrl_name)
            if pb is None:
                continue
            pb.rotation_mode = 'QUATERNION'
            # Per-bone CUSTOM color — pulls from the scene's
            # gtatools_ik_color slider so the user can repaint all
            # IK controls live (the property's update callback
            # patches every existing rig). Wrapped in try/except in
            # case the BoneColor API isn't present (pre-4.0 builds).
            try:
                pb.color.palette = 'CUSTOM'
                pb.color.custom.normal = ik_color
                pb.color.custom.select = ik_color
                pb.color.custom.active = ik_color
            except Exception:
                pass
            try:
                pb.custom_shape = widget_mesh
                pb.use_custom_shape_bone_size = False
                size = size_by_type.get(ctrl_type, 0.08)
                pb.custom_shape_scale_xyz = (size, size, size)
                # Rot controls overlap the deform bone exactly
                # (matrix_local is bit-identical so Copy Rotation
                # is a no-op at rest). To keep the cube visually
                # selectable we offset just the SHAPE — bone math
                # stays at deform's rest. Offset = bone length in
                # the bone's local +Y direction = at the tail.
                if ctrl_type == 'rot':
                    bone_length = pb.bone.length
                    pb.custom_shape_translation = (
                        0.0, bone_length, 0.0)
                # Chain controls (hand/foot) read the scene-level
                # offset so the user can nudge cube position to
                # align with the SA mesh hand/foot via the slider.
                elif ctrl_type == 'chain':
                    pb.custom_shape_translation = tuple(getattr(
                        scene, 'gtatools_ik_chain_offset',
                        (0.0, 0.0, 0.0)))
            except Exception:
                pass

        # ── Phase 4b: bone collections per control type ──────────
        # Bone collections are Blender 4+'s modern way to toggle
        # bone visibility (``Bone.hide`` is unreliable now). We
        # create one collection per IK type and assign control
        # bones; the panel's visibility checkboxes then flip
        # ``coll.is_visible`` instead of fighting with bone.hide.
        bone_colls = getattr(armature.data, 'collections', None)
        if bone_colls is not None:
            type_to_coll_name = {
                'chain': _IK_COLL_CHAIN,
                'pole':  _IK_COLL_POLE,
                'rot':   _IK_COLL_ROT,
                'root':  _IK_COLL_ROOT,
            }
            for ctrl_name, ctrl_type, _, _ in created:
                coll_name = type_to_coll_name.get(ctrl_type)
                if coll_name is None:
                    continue
                coll = bone_colls.get(coll_name)
                if coll is None:
                    coll = bone_colls.new(coll_name)
                bone = armature.data.bones.get(ctrl_name)
                if bone is not None:
                    try:
                        coll.assign(bone)
                    except Exception:
                        pass

        # ── Phase 5 ──────────────────────────────────────────────
        # Bake the FK samples we captured in Phase 1b onto the
        # control bones. We set ``ctrl_pb.matrix`` (armature-space)
        # which Blender turns into the corresponding matrix_basis,
        # then keyframe location + rotation_quaternion at the
        # original FK frame. End result: scrubbing the timeline
        # plays the original animation again — but now each pose
        # is editable via the control bones.
        baked_frames = 0
        if fk_samples:
            saved_frame = scene.frame_current
            try:
                for ctrl_name, samples in fk_samples.items():
                    ctrl_pb = armature.pose.bones.get(ctrl_name)
                    if ctrl_pb is None:
                        continue
                    for f, target_mat in samples:
                        scene.frame_set(f)
                        ctrl_pb.matrix = target_mat
                        ctrl_pb.keyframe_insert('location', frame=f)
                        ctrl_pb.keyframe_insert(
                            'rotation_quaternion', frame=f)
                        baked_frames += 1
            finally:
                scene.frame_set(saved_frame)

        # Pole bones — location-only keyframes. We compute the basis
        # location so rest rotation stays untouched (pole orientation
        # in the viewport matches its initial chain-direction tail
        # at every frame). Formula matches _ik_follow_handler's
        # location math elsewhere in this file.
        if pole_loc_samples:
            saved_frame = scene.frame_current
            try:
                for ctrl_name, samples in pole_loc_samples.items():
                    pole_pb = armature.pose.bones.get(ctrl_name)
                    if pole_pb is None:
                        continue
                    rest_head = pole_pb.bone.head_local
                    rest_rot_inv = (pole_pb.bone.matrix_local
                                    .to_3x3().inverted())
                    for f, target_arm_pos in samples:
                        scene.frame_set(f)
                        pole_pb.location = rest_rot_inv @ (
                            target_arm_pos - rest_head)
                        pole_pb.keyframe_insert('location', frame=f)
                        baked_frames += 1
            finally:
                scene.frame_set(saved_frame)

        if (added_chains == 0 and added_rot == 0 and added_root == 0
                and skipped):
            self.report({'ERROR'},
                T("Не найдены кости: ") + ", ".join(skipped[:4]))
            return {'CANCELLED'}

        armature[_IK_FLAG] = 1
        # Lazily attach the depsgraph follow-handler now that we have an
        # IK-rigged armature in the scene. Idempotent — safe if another
        # rig already triggered registration earlier this session.
        _register_follow_handler()
        msg = (f"IK rig: {added_chains} цепочек + {added_poles} pole "
               f"+ {added_rot} rot + {added_root} root")
        if baked_frames:
            msg += f", запечено {baked_frames} FK-семплов"
        if skipped:
            msg += f", пропущено: {len(skipped)}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_bake_ik_rig(bpy.types.Operator):
    """Запечь визуальную позу с IK на deform-кости, удалить
    IK-constraints и control-кости. Делать ПЕРЕД Export IFP —
    иначе ифп получит сырые ротации без учёта IK."""
    bl_idname = "gtatools.bake_ik_rig"
    bl_label = "INU: Bake & Clear IK"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'ARMATURE'
                and obj.get(_IK_FLAG))

    def execute(self, context):
        armature = context.active_object
        scene = context.scene

        prev_mode = armature.mode
        if prev_mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')

        # Sort armature bones into deform vs control sets — we need
        # both to (a) skip the bake when only deform bones already
        # carry user-authored keys and (b) wipe stale fcurves for
        # control bones at the end.
        deform_names = set()
        ctrl_names = set()
        for db in armature.data.bones:
            if db.get(_CTRL_FLAG):
                ctrl_names.add(db.name)
            else:
                deform_names.add(db.name)

        action = (armature.animation_data.action
                  if armature.animation_data else None)

        # Collect every frame on which any pose-bone fcurve has a
        # keyframe (deform OR control). These are the frames the
        # user authored and the only frames the baked action needs
        # values at.
        keyed_frames = set()
        if action is not None:
            for fc in _iter_action_fcurves(action):
                if not fc.data_path.startswith('pose.bones['):
                    continue
                for kp in fc.keyframe_points:
                    keyed_frames.add(int(round(kp.co[0])))

        # Two-pass bake: capture every post-IK pose first (with
        # constraints active so IK evaluates), THEN strip the
        # constraints, THEN write the captured basis values back as
        # keyframes. Earlier single-pass approach (`pb.matrix_basis
        # = basis` + `keyframe_insert` while IK was still active)
        # silently dropped IK contributions on some Blender versions
        # — the keyframed quaternion looked like the bone's pre-IK
        # FK rotation, so playback after Bake & Clear collapsed to
        # the original FK. Sampling first / writing second avoids
        # any depsgraph race entirely.
        sample_frames = (sorted(keyed_frames) if keyed_frames
                         else [scene.frame_current])
        samples = _sample_basis_for_bake(
            context, armature, sample_frames)

        # Drop every IK / Copy / Floor constraint we ever added.
        # Done BEFORE writing keyframes so the just-written basis
        # values aren't overridden during evaluation — and so the
        # keyframe_insert below captures the values we set, not what
        # IK would still resolve to.
        for pb in armature.pose.bones:
            for c in list(pb.constraints):
                if c.name.startswith('INU_IK_') and c.type in {
                        'IK', 'COPY_ROTATION', 'COPY_LOCATION',
                        'LIMIT_LOCATION', 'FLOOR', 'CHILD_OF'}:
                    pb.constraints.remove(c)

        _write_basis_keyframes(armature, samples)

        # ── Edit Mode: remove control bones from the armature ──
        bpy.ops.object.mode_set(mode='EDIT')
        eb = armature.data.edit_bones
        ctrl_to_remove = [b for b in eb if b.get(_CTRL_FLAG)]
        for b in ctrl_to_remove:
            try:
                eb.remove(b)
            except Exception:
                pass

        # Strip any stale fcurves left behind for the now-deleted
        # control bones — Blender doesn't auto-clean these.
        if action is not None and ctrl_names:
            _strip_fcurves_for_bones(action, ctrl_names)

        # Sweep up any leftover empty-widgets from the previous
        # (object-based) version of this addon. Harmless if there
        # are none — keeps the scene tidy after upgrading.
        legacy_targets = [
            o for o in bpy.data.objects
            if o.get(_LEGACY_WIDGET_FLAG)
        ]
        for o in legacy_targets:
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except Exception:
                pass
        legacy_coll = bpy.data.collections.get(_LEGACY_COLLECTION)
        if legacy_coll is not None and len(legacy_coll.objects) == 0:
            try:
                bpy.data.collections.remove(legacy_coll)
            except Exception:
                pass

        # Restore the user's prior mode.
        if prev_mode == 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
        elif prev_mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Final clean-up: collapse runs of constant keys produced by
        # the bake. Threshold matches Blender's IK solver tolerance
        # so static poses do collapse to a single key per fcurve.
        removed_keys = 0
        if action is not None:
            removed_keys = _simplify_action(action, threshold=0.001)

        try:
            del armature[_IK_FLAG]
        except KeyError:
            pass

        msg = f"IK baked, {len(ctrl_to_remove)} control bone(s) removed"
        if legacy_targets:
            msg += f", {len(legacy_targets)} legacy empties cleaned"
        if removed_keys:
            msg += f", {removed_keys} избыточных ключей очищено"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


_GROUND_OBJ_NAME = "INU_Ground"
_GROUND_MAT_NAME = "INU_Ground_Mat"
_GROUND_FLAG = "inu_ik_ground"


class GTATOOLS_OT_add_ground_plane(bpy.types.Operator):
    """Создать "пол" — плоскость 10×10м с процедурной сеткой,
    которая работает как ограничитель для ног IK-рига. После
    Add IK Rig стопы автоматически получают Floor constraint
    с этой плоскостью как target — двигаешь плоскость по Z,
    стопы клемпятся выше неё. Зазор (offset над плоскостью)
    настраивается слайдером "Зазор" """
    bl_idname = "gtatools.add_ground_plane"
    bl_label = "INU: Floor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Reuse existing ground if present, otherwise build a fresh
        # 10x10 m quad at world origin. UV mapped 0..3 so the
        # texture repeats 3 times across each axis — visually
        # finer grid without making the plane smaller.
        obj = bpy.data.objects.get(_GROUND_OBJ_NAME)
        if obj is None:
            half = 5.0
            verts = [
                (-half, -half, 0.0),
                (+half, -half, 0.0),
                (+half, +half, 0.0),
                (-half, +half, 0.0),
            ]
            faces = [(0, 1, 2, 3)]
            mesh = bpy.data.meshes.new(_GROUND_OBJ_NAME)
            mesh.from_pydata(verts, [], faces)
            mesh.update()

            uv_layer = mesh.uv_layers.new()
            uv_repeat = 3.0
            uv_coords = [
                (0.0, 0.0),
                (uv_repeat, 0.0),
                (uv_repeat, uv_repeat),
                (0.0, uv_repeat),
            ]
            for poly in mesh.polygons:
                for i, loop_index in enumerate(poly.loop_indices):
                    uv_layer.data[loop_index].uv = uv_coords[i]

            obj = bpy.data.objects.new(_GROUND_OBJ_NAME, mesh)
            obj[_GROUND_FLAG] = 1
            context.collection.objects.link(obj)

        # Material: reuse if already created, otherwise build a
        # minimal PROCEDURAL grid graph (Checker → Emission → Output;
        # no bundled image, no Principled BSDF — that would add specular
        # highlights which look ugly on a flat dev grid). Color goes
        # straight to surface, scene lighting can't produce a hot spot.
        mat = bpy.data.materials.get(_GROUND_MAT_NAME)
        if mat is None:
            mat = bpy.data.materials.new(_GROUND_MAT_NAME)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            for n in list(nodes):
                nodes.remove(n)
            output = nodes.new('ShaderNodeOutputMaterial')
            emission = nodes.new('ShaderNodeEmission')
            checker = nodes.new('ShaderNodeTexChecker')
            # Subtle grey checkerboard as a floor reference grid.
            checker.inputs['Scale'].default_value = 12.0
            checker.inputs['Color1'].default_value = (0.16, 0.16, 0.16, 1.0)
            checker.inputs['Color2'].default_value = (0.26, 0.26, 0.26, 1.0)
            output.location = (400, 0)
            emission.location = (200, 0)
            checker.location = (-200, 0)
            emission.inputs['Strength'].default_value = 1.0
            links.new(checker.outputs['Color'],
                      emission.inputs['Color'])
            links.new(emission.outputs['Emission'],
                      output.inputs['Surface'])

        if not obj.data.materials:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        # Wire this plane as the floor target for every existing
        # IK rig — when the user spawns the ground after Add IK
        # Rig, foot Floor constraints were created with target=None
        # and need to be patched. Re-running this operator with the
        # ground already present just reuses the same target.
        patched = 0
        for arm in bpy.data.objects:
            if arm.type != 'ARMATURE' or not arm.get(_IK_FLAG):
                continue
            for pb in arm.pose.bones:
                for c in pb.constraints:
                    if (c.type == 'FLOOR'
                            and c.name.startswith('INU_IK_')
                            and c.target is not obj):
                        c.target = obj
                        patched += 1

        msg = T("Ground plane создан")
        if patched:
            msg += f", обновлено {patched} foot-floor"
        self.report({'INFO'}, msg)
        return {'FINISHED'}




# Stale handler cleanup: previous addon versions installed an
# auto-sync depsgraph_update_post hook called `_ik_sync_handler`.
# Strip any leftover reference so it doesn't keep firing after
# update without a reload of Blender.
def _purge_legacy_handler():
    handlers = bpy.app.handlers.depsgraph_update_post
    for h in list(handlers):
        if getattr(h, '__name__', '') == '_ik_sync_handler':
            try:
                handlers.remove(h)
            except Exception:
                pass


_purge_legacy_handler()


# ── Position-following handler ───────────────────────────────────
# Called on every depsgraph update (interactive drag in Pose Mode,
# frame change, anything that changes pose). For each rot-control
# bone that has ``inu_ik_follow_parent`` + ``inu_ik_follow_offset``
# props, recompute its world position as
# ``parent.matrix @ offset`` so the control rides along with body
# movement. Rotation is left alone — user keeps full control.
#
# Re-entry guard: setting pose_bone.matrix triggers another
# depsgraph update, which would re-fire this handler infinitely
# without the flag.
_ik_follow_busy = False


@bpy.app.handlers.persistent
def _ik_follow_handler(scene, depsgraph=None):
    global _ik_follow_busy
    if _ik_follow_busy:
        return

    # Quick early-out: skip the iteration unless at least one
    # rigged armature exists. Saves cycles when user works on
    # unrelated scenes.
    rigged = [o for o in bpy.data.objects
              if o.type == 'ARMATURE' and o.get(_IK_FLAG)]
    if not rigged:
        return

    _ik_follow_busy = True
    try:
        for arm in rigged:
            mw = arm.matrix_world
            for pb in arm.pose.bones:
                db = arm.data.bones.get(pb.name)
                if db is None or not db.get(_CTRL_FLAG):
                    continue
                target_name = db.get('inu_ik_follow_parent')
                if not target_name:
                    continue
                offset = db.get('inu_ik_follow_offset')
                if offset is None or len(offset) != 3:
                    continue
                parent_pb = arm.pose.bones.get(target_name)
                if parent_pb is None:
                    continue

                # Compute desired armature-space head position:
                # parent_world × offset_in_parent_local.
                offset_vec = mathutils.Vector(
                    (offset[0], offset[1], offset[2]))
                parent_world = mw @ parent_pb.matrix
                target_world_loc = parent_world @ offset_vec
                # Convert to armature-local — for armatures with
                # non-identity matrix_world we need to undo it,
                # else the value goes straight into pose_bone.
                target_arm_loc = (mw.inverted_safe()
                                  @ target_world_loc)

                # Convert armature-space target into the bone's
                # ``pose_bone.location`` representation: bone-
                # local offset from the rest head, expressed in
                # the bone's local axes. This way we touch ONLY
                # location, never rotation_quaternion — the user's
                # keyed rotation stays bit-exact.
                rest_head = pb.bone.head_local
                rest_rot_inv = pb.bone.matrix_local.to_3x3().inverted()
                pb.location = rest_rot_inv @ (
                    target_arm_loc - rest_head)
    finally:
        _ik_follow_busy = False


def _register_follow_handler():
    # Drop any stale registration first (so reload-during-dev
    # doesn't accumulate handlers), then attach to BOTH lists:
    # depsgraph_update_post for interactive Pose Mode dragging,
    # frame_change_post for animation playback (depsgraph update
    # alone doesn't always fire mid-playback in older Blenders).
    for handlers in (bpy.app.handlers.depsgraph_update_post,
                     bpy.app.handlers.frame_change_post):
        for h in list(handlers):
            if getattr(h, '__name__', '') == '_ik_follow_handler':
                try:
                    handlers.remove(h)
                except Exception:
                    pass
    bpy.app.handlers.depsgraph_update_post.append(_ik_follow_handler)
    bpy.app.handlers.frame_change_post.append(_ik_follow_handler)


def _unregister_follow_handler():
    """Detach the IK follow handler from both event lists.

    Called from the addon's ``unregister()`` so disabling the addon
    leaves no orphan handlers.
    """
    for handlers in (bpy.app.handlers.depsgraph_update_post,
                     bpy.app.handlers.frame_change_post):
        for h in list(handlers):
            if getattr(h, '__name__', '') == '_ik_follow_handler':
                try:
                    handlers.remove(h)
                except Exception:
                    pass


@bpy.app.handlers.persistent
def _on_file_load_ik(_dummy):
    """Re-attach the IK follow handler when a saved .blend with IK-rigged
    armatures is opened. Without this, the rig would stop following the
    pose-bone targets after a fresh file load until the user added a new
    rig (the depsgraph hook isn't itself persisted across files)."""
    if any(o.type == 'ARMATURE' and o.get(_IK_FLAG) for o in bpy.data.objects):
        _register_follow_handler()


# NOTE: handlers must only be touched from the addon's register()/
# unregister() — never at module import. ``_on_file_load_ik`` is wired
# into the consolidated ``_on_file_load`` load_post handler in the
# package ``__init__.py``. The heavy depsgraph + frame_change follow-
# handler stays lazy — attached by ``GTATOOLS_OT_add_ik_rig`` on first
# rig setup this session, or by ``_on_file_load_ik`` when opening a
# .blend that already has rigs.
