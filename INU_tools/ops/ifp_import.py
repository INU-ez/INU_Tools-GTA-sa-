# INU_tools.ops.ifp_import — Import GTA SA IFP animations into Blender

import bpy
import mathutils
from ..core.ifp import read_ifp, HAS_ROT, HAS_TRANS

# Blender 5.x uses layered actions; 4.x uses action.fcurves directly
_USE_LAYERED = hasattr(bpy.types, 'ActionSlot')

# Cached IFP data (animations stored after import, applied on demand)
_ifp_cache = {}  # name → IFPFile


def _create_action_fcurves(action, armature):
    """Create action and return fcurves container."""
    if not _USE_LAYERED:
        return action.fcurves

    slot = action.slots.new(id_type='OBJECT', name=armature.name)
    layer = action.layers.new(name=action.name)
    strip = layer.strips.new(type='KEYFRAME')
    channelbag = strip.channelbag(slot, ensure=True)
    return channelbag.fcurves


def import_ifp(filepath: str, context=None):
    """Import IFP file — parse and cache animations.

    Does NOT apply to armature. Use apply_ifp_action() to apply.
    """
    ifp = read_ifp(filepath)
    if not ifp.animations:
        return []

    # Cache for later application
    _ifp_cache[filepath] = ifp

    # Store animation names as empty actions (for UI listing)
    created = []
    for anim in ifp.animations:
        action = bpy.data.actions.new(name=anim.name)
        action['ifp_source'] = filepath
        action['ifp_package'] = ifp.name
        action['ifp_anim_index'] = ifp.animations.index(anim)
        created.append(action)

    return created


def apply_ifp_action(action_name: str, armature, context=None):
    """Apply a cached IFP animation to an armature.

    Only works on ARMATURE objects. Finds the animation data from cache
    and creates fcurves on the action.
    """
    if not armature or armature.type != 'ARMATURE':
        return False, "Select an armature"

    # Find the action
    action = bpy.data.actions.get(action_name)
    if not action:
        return False, f"Action '{action_name}' not found"

    filepath = action.get('ifp_source')
    if not filepath:
        return False, "Not an IFP action"

    # Get cached IFP data
    ifp = _ifp_cache.get(filepath)
    if not ifp:
        # Try to reload
        ifp = read_ifp(filepath)
        if ifp:
            _ifp_cache[filepath] = ifp
        else:
            return False, f"Cannot read IFP: {filepath}"

    # Find animation by name
    anim = None
    for a in ifp.animations:
        if a.name == action_name:
            anim = a
            break
    if not anim:
        return False, f"Animation '{action_name}' not found in IFP"

    # Check if action already has fcurves (already applied)
    has_curves = False
    try:
        has_curves = len(action.fcurves) > 0
    except AttributeError:
        if hasattr(action, 'layers') and action.layers:
            for layer in action.layers:
                for strip in layer.strips:
                    if hasattr(strip, 'channelbags'):
                        for cb in strip.channelbags:
                            if len(cb.fcurves) > 0:
                                has_curves = True

    if has_curves:
        # Already applied, just assign
        if not armature.animation_data:
            armature.animation_data_create()
        armature.animation_data.action = action
        if _USE_LAYERED and action.slots:
            try:
                armature.animation_data.action_slot = action.slots[0]
            except Exception:
                pass
        return True, f"Applied '{action_name}'"

    # Create fcurves
    try:
        fc_container = _create_action_fcurves(action, armature)
    except Exception as e:
        return False, f"Error creating fcurves: {e}"

    for abone in anim.bones:
        bone_name = abone.name
        pose_bone = armature.pose.bones.get(bone_name)
        if not pose_bone:
            for pb in armature.pose.bones:
                if pb.name.lower() == bone_name.lower():
                    pose_bone = pb
                    break

        if not pose_bone:
            continue

        data_path_rot = f'pose.bones["{pose_bone.name}"].rotation_quaternion'
        data_path_loc = f'pose.bones["{pose_bone.name}"].location'

        try:
            rest_bone = armature.data.bones.get(pose_bone.name)
            if rest_bone:
                rest_mat = rest_bone.matrix_local
                if rest_bone.parent:
                    rest_mat = rest_bone.parent.matrix_local.inverted() @ rest_mat
                rest_quat = rest_mat.to_quaternion()
                rest_inv = rest_quat.inverted()
            else:
                rest_inv = mathutils.Quaternion()

            if abone.key_type & HAS_ROT:
                fc_rw = fc_container.new(data_path_rot, index=0)
                fc_rx = fc_container.new(data_path_rot, index=1)
                fc_ry = fc_container.new(data_path_rot, index=2)
                fc_rz = fc_container.new(data_path_rot, index=3)

                for kf in abone.keyframes:
                    frame = kf.time
                    qx, qy, qz, qw = kf.rotation
                    gta_quat = mathutils.Quaternion((qw, qx, qy, qz))
                    bl_quat = rest_inv @ gta_quat
                    fc_rw.keyframe_points.insert(frame, bl_quat.w, options={'FAST'})
                    fc_rx.keyframe_points.insert(frame, bl_quat.x, options={'FAST'})
                    fc_ry.keyframe_points.insert(frame, bl_quat.y, options={'FAST'})
                    fc_rz.keyframe_points.insert(frame, bl_quat.z, options={'FAST'})

            if abone.key_type & HAS_TRANS:
                fc_lx = fc_container.new(data_path_loc, index=0)
                fc_ly = fc_container.new(data_path_loc, index=1)
                fc_lz = fc_container.new(data_path_loc, index=2)

                for kf in abone.keyframes:
                    frame = kf.time
                    tx, ty, tz = kf.translation
                    gta_loc = mathutils.Vector((tx, ty, tz))
                    bl_loc = rest_inv.to_matrix() @ gta_loc
                    fc_lx.keyframe_points.insert(frame, bl_loc.x, options={'FAST'})
                    fc_ly.keyframe_points.insert(frame, bl_loc.y, options={'FAST'})
                    fc_lz.keyframe_points.insert(frame, bl_loc.z, options={'FAST'})
        except Exception:
            continue

    # Assign action to armature
    if not armature.animation_data:
        armature.animation_data_create()
    armature.animation_data.action = action
    if _USE_LAYERED and action.slots:
        try:
            armature.animation_data.action_slot = action.slots[0]
        except Exception:
            pass

    return True, f"Applied '{action_name}' ({len(anim.bones)} bones)"
