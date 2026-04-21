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


# ──────────────────────────── batch import ────────────────────────────

def enumerate_animations(folder: str, name_filter: str = "") -> list[tuple[str, str]]:
    """Walk `folder` (non-recursive) for *.ifp files and return a flat list
    of (filepath, animation_name) tuples, optionally filtered by prefix
    (case-insensitive, empty = no filter).
    """
    import os
    from ..core.ifp import read_ifp as _read_ifp

    out: list[tuple[str, str]] = []
    if not folder or not os.path.isdir(folder):
        return out
    flt = (name_filter or "").strip().lower()
    for entry in sorted(os.listdir(folder)):
        if not entry.lower().endswith('.ifp'):
            continue
        path = os.path.join(folder, entry)
        try:
            ifp = _read_ifp(path)
        except Exception as e:
            print(f"[IFP Batch] failed to read {entry}: {e}")
            continue
        for anim in ifp.animations:
            if flt and not anim.name.lower().startswith(flt):
                continue
            out.append((path, anim.name))
    return out


def _action_frame_range(action) -> tuple[float, float]:
    """Return (start, end) in frames for an action regardless of Blender 4/5."""
    try:
        rng = action.frame_range
        return (float(rng[0]), float(rng[1]))
    except Exception:
        pass
    # Layered actions (Blender 5) — scan fcurves inside channelbags
    start, end = 0.0, 0.0
    if hasattr(action, 'layers'):
        for layer in action.layers:
            for strip in layer.strips:
                for cb in getattr(strip, 'channelbags', []):
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            start = min(start, kp.co.x)
                            end = max(end, kp.co.x)
    return start, end


def batch_apply_sequential(armature, anims: list[tuple[str, str]],
                           *, mode: str = 'NLA',
                           offset_frames: float = 10.0) -> tuple[int, str]:
    """Apply a list of (file, anim_name) pairs to `armature`.

    mode:
      'ACTIONS' — just create Actions, no NLA arrangement
      'NLA'     — stack sequentially on one NLA track with `offset_frames`
                  between clips (lets you scrub through the whole batch)

    Returns (applied_count, message).
    """
    import bpy

    if not armature or armature.type != 'ARMATURE':
        return 0, "Select an armature"

    applied = 0
    nla_track = None
    cursor = float(bpy.context.scene.frame_start or 0)

    if mode == 'NLA':
        if not armature.animation_data:
            armature.animation_data_create()
        nla_track = armature.animation_data.nla_tracks.new()
        nla_track.name = "IFP Batch"

    for path, anim_name in anims:
        # Ensure the action exists (import_ifp creates empty stubs per anim)
        action = bpy.data.actions.get(anim_name)
        if not action:
            created = import_ifp(path)
            action = bpy.data.actions.get(anim_name)
            if not action:
                continue

        ok, _msg = apply_ifp_action(anim_name, armature)
        if not ok:
            continue
        applied += 1

        if mode == 'NLA' and nla_track is not None:
            start_f, end_f = _action_frame_range(action)
            length = max(1.0, end_f - start_f)
            try:
                strip = nla_track.strips.new(anim_name, int(cursor), action)
                strip.frame_end = cursor + length
            except Exception as e:
                print(f"[IFP Batch] NLA strip failed for {anim_name}: {e}")
            cursor += length + offset_frames

    if mode == 'NLA' and applied > 0:
        # Clear the direct action so the NLA takes over
        armature.animation_data.action = None
        bpy.context.scene.frame_end = int(cursor)

    return applied, f"Applied {applied} animation(s)"


class GTATOOLS_OT_ifp_batch_import(bpy.types.Operator):
    """Импортировать все *.ifp из папки и уложить анимации на NLA-трек активного armature"""
    bl_idname = "gtatools.ifp_batch_import"
    bl_label = "Batch Import IFP Folder"
    bl_options = {'REGISTER', 'UNDO'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    name_filter: bpy.props.StringProperty(
        name="Name Prefix",
        description="Применять только анимации, имя которых начинается с этого префикса (регистронезависимо)",
        default="",
    )
    mode: bpy.props.EnumProperty(
        name="Mode",
        items=[
            ('NLA', "NLA Sequential", "Уложить клипы на один NLA-трек с зазором"),
            ('ACTIONS', "Actions Only", "Создать Actions, без NLA"),
        ],
        default='NLA',
    )
    offset_frames: bpy.props.FloatProperty(
        name="Gap Between Clips",
        default=10.0, min=0.0, soft_max=100.0,
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature as the active object")
            return {'CANCELLED'}

        anims = enumerate_animations(self.directory, self.name_filter)
        if not anims:
            self.report({'WARNING'}, "No animations matched in folder")
            return {'CANCELLED'}

        applied, msg = batch_apply_sequential(
            armature, anims, mode=self.mode, offset_frames=self.offset_frames)
        if applied == 0:
            self.report({'WARNING'}, "No animations applied")
            return {'CANCELLED'}
        self.report({'INFO'}, f"{msg} from {len(anims)} candidate(s)")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_ifp_batch_import,
)


# ──────────────────────────── train station markers ───────────────────
# (Lives in this module only for lack of a dedicated path_ui module.)

def _refresh_station_markers(track_obj):
    """Rebuild visible Empty markers for every station point on a track
    curve. The markers are parented to the curve so they follow any
    object-space moves.
    """
    import bpy as _bpy
    from mathutils import Vector
    if track_obj is None or track_obj.type != 'CURVE':
        return 0
    if track_obj.get('path_type') != 'track':
        return 0

    # Wipe old markers under this track
    for child in list(track_obj.children):
        if child.get('station_marker_of') == track_obj.name:
            try:
                _bpy.data.objects.remove(child, do_unlink=True)
            except Exception:
                pass

    try:
        stations = set(eval(track_obj.get('station_indices', '[]')))
    except Exception:
        return 0

    target_collection = (track_obj.users_collection[0]
                         if track_obj.users_collection
                         else _bpy.context.scene.collection)

    idx = 0
    placed = 0
    for spline in track_obj.data.splines:
        for pt in spline.points:
            if idx in stations:
                empty = _bpy.data.objects.new(
                    f"{track_obj.name}_station_{idx}", None)
                empty.empty_display_type = 'SPHERE'
                empty.empty_display_size = 3.0
                empty['station_marker_of'] = track_obj.name
                empty['station_index'] = idx
                target_collection.objects.link(empty)
                # Parent first, clear parent-inverse, THEN write position.
                # pt.co is in the curve's local space, which is exactly what
                # `location` on a child (with identity parent-inverse) wants.
                empty.parent = track_obj
                empty.matrix_parent_inverse.identity()
                empty.location = Vector((pt.co.x, pt.co.y, pt.co.z))
                placed += 1
            idx += 1
    return placed


class GTATOOLS_OT_refresh_station_markers(bpy.types.Operator):
    """Пересоздать видимые Empty-маркеры для каждой станции на активном ж/д пути"""
    bl_idname = "gtatools.refresh_station_markers"
    bl_label = "Refresh Station Markers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'CURVE' and obj.get('path_type') == 'track'

    def execute(self, context):
        placed = _refresh_station_markers(context.active_object)
        self.report({'INFO'}, f"{placed} station marker(s)")
        return {'FINISHED'}


classes = classes + (GTATOOLS_OT_refresh_station_markers,)


# ──────────────────────────── path-node flags ─────────────────────────

class GTATOOLS_OT_path_node_flag(bpy.types.Operator):
    """Переключить roadblock или задать тип светофора на выделенных точках кривой пути"""
    bl_idname = "gtatools.path_node_flag"
    bl_label = "Set Path Node Flag"
    bl_options = {'REGISTER', 'UNDO'}

    action: bpy.props.EnumProperty(
        items=[
            ('TOGGLE_ROADBLOCK', "Toggle Roadblock",
             "Переключить бит 12 (барьер копов) на каждой выделенной точке"),
            ('TRAFFIC_NONE',   "Clear Traffic Light",
             "Поставить traffic_light=0 на каждой выделенной точке"),
            ('TRAFFIC_NORMAL', "Normal Traffic Light",
             "Поставить traffic_light=1 на каждой выделенной точке"),
            ('TRAFFIC_RAIL',   "Rail Traffic Light",
             "Поставить traffic_light=2 на каждой выделенной точке"),
            ('TRAFFIC_BUS',    "Bus Traffic Light",
             "Поставить traffic_light=3 на каждой выделенной точке"),
        ],
        default='TOGGLE_ROADBLOCK',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'CURVE'
                and obj.get('path_type') == 'path_ipl'
                and context.mode == 'EDIT_CURVE')

    def execute(self, context):
        from ..core.paths import (
            PATH_FLAG_ROADBLOCK, PATH_FLAG_TRAFFIC_MASK,
            PATH_FLAG_TRAFFIC_SHIFT,
        )
        obj = context.active_object
        # The spline contains only nodes with node_type > 0, but IDProps
        # `pn_{j}_*` are stored for every node including empty padding.
        # Build a mapping from spline-point index → full IDProp index so
        # we write flags into the right slot.
        pn_count = int(obj.get('pn_count', 0) or 0)
        real_to_full: list[int] = []
        for j in range(pn_count):
            if int(obj.get(f'pn_{j}_type', 0) or 0) > 0:
                real_to_full.append(j)

        touched = 0
        spline_idx = 0
        for spline in obj.data.splines:
            for pt in spline.points:
                if pt.select:
                    if spline_idx >= len(real_to_full):
                        spline_idx += 1
                        continue
                    full_idx = real_to_full[spline_idx]
                    key = f'pn_{full_idx}_flags'
                    cur = int(obj.get(key, 0) or 0)
                    if self.action == 'TOGGLE_ROADBLOCK':
                        cur ^= PATH_FLAG_ROADBLOCK
                    else:
                        tl_map = {'TRAFFIC_NONE': 0, 'TRAFFIC_NORMAL': 1,
                                  'TRAFFIC_RAIL': 2, 'TRAFFIC_BUS': 3}
                        tl = tl_map[self.action]
                        cur = (cur & ~PATH_FLAG_TRAFFIC_MASK) | \
                              ((tl << PATH_FLAG_TRAFFIC_SHIFT) & PATH_FLAG_TRAFFIC_MASK)
                    obj[key] = cur
                    touched += 1
                spline_idx += 1
        self.report({'INFO'}, f"{touched} point(s) updated — {self.action}")
        return {'FINISHED'}


classes = classes + (GTATOOLS_OT_path_node_flag,)
