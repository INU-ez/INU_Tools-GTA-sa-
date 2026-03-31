# INU_tools.ops.ifp_export — Export Blender actions to GTA SA IFP

import bpy
from ..core.ifp import IFPFile, Animation, AnimBone, KeyFrame, HAS_ROT, HAS_TRANS, write_ifp


def export_ifp(filepath: str, actions=None, armature=None, package_name="ped"):
    """Export Blender Actions as IFP file.

    Each Action becomes one animation in the IFP.
    Reads keyframes from fcurves on pose bones.
    """
    if armature is None:
        if bpy.context.active_object and bpy.context.active_object.type == 'ARMATURE':
            armature = bpy.context.active_object

    if actions is None:
        # Export all actions that have ifp_source or are assigned to armature
        actions = [a for a in bpy.data.actions if a.get('ifp_source') or
                   (armature and armature.animation_data and
                    armature.animation_data.action == a)]

    if not actions:
        return 0

    ifp = IFPFile(name=package_name)
    fps = bpy.context.scene.render.fps

    for action in actions:
        anim = Animation(name=action.name)

        # Group fcurves by bone name
        bone_curves = {}
        for fc in action.fcurves:
            if not fc.data_path.startswith('pose.bones['):
                continue
            # Extract bone name from data_path
            parts = fc.data_path.split('"')
            if len(parts) < 2:
                continue
            bone_name = parts[1]
            prop = fc.data_path.rsplit('.', 1)[-1]
            bone_curves.setdefault(bone_name, {}).setdefault(prop, []).append(fc)

        for bone_name, props in bone_curves.items():
            bone = AnimBone(name=bone_name)

            # Determine key type
            has_rot = 'rotation_quaternion' in props
            has_loc = 'location' in props
            bone.key_type = 0
            if has_rot:
                bone.key_type |= HAS_ROT
            if has_loc:
                bone.key_type |= HAS_TRANS

            if not bone.key_type:
                continue

            # Find bone_id from armature
            if armature:
                pb = armature.pose.bones.get(bone_name)
                if pb:
                    bone.bone_id = list(armature.pose.bones).index(pb)

            # Collect all keyframe times
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

        ifp.animations.append(anim)

    return write_ifp(filepath, ifp)
