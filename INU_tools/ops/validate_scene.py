# INU_tools.ops.validate_scene
# Pre-export sanity sweep — one button that runs all scope-wide checks
# the user would otherwise hit one-by-one across 4 different panels,
# plus new checks for known-but-uncovered foot-guns:
#
#   • Quaternion normalisation in armature Actions  (sometimes drifts
#     after manual fcurve edits; in-game playback gets stepping)
#   • Modulate Color on prelit meshes  (causes flicker — common pitfall
#     from importing Kam's-style DFFs into the new Day/Night pipeline)
#   • _ok / _dam pair completeness  (engine silently skips orphans)
#   • Paintjob slot completeness  (Pay'n'Spray fallback if half-filled)
#
# Per-domain validators (frame_validate, animobj_validate, ifp_roundtrip)
# stay where they are — they're tied to context.active_object or to a
# specific .ifp file picker and don't fit a sweep model.
#
# All check rules live in core/validate.py (bpy-free, unit-testable).
# This module only owns the bpy.data adapters and the operator/panel
# plumbing.

from __future__ import annotations

import bpy
from bpy.props import StringProperty

from .. import T
from ..tools import compat
from ..core.validate import (
    check_paintjobs,
    check_quaternions,
    check_modulate_color,
    check_damage_pairs,
    check_orphan_models,
    check_orphan_2dfx,
    check_duplicate_model_ids,
    check_empty_meshes,
    check_large_meshes,
    check_materials_without_texture,
    check_suffix_consistency,
    check_object_scale,
    check_light_beam_asi,
)


# ── bpy-side adapters ───────────────────────────────────────────────


def _scene_objects(types=None):
    """Iterate objects linked to the active scene's collection tree.

    ``bpy.data.objects`` also exposes orphan datablocks — objects
    loaded into the .blend but not linked to any scene (typical after
    interrupted imports). Reporting on those produces phantom rows the
    user can't even ``select_set`` because they aren't in any view
    layer. Walk the scene instead so the validator only sees real
    members.
    """
    scene = bpy.context.scene
    if scene is None:
        return iter([])
    if types is None:
        return iter(scene.objects)
    types_set = types if isinstance(types, (set, frozenset)) else set(types)
    return (o for o in scene.objects if o.type in types_set)


def _gather_paintjob_materials():
    out = []
    for mat in bpy.data.materials:
        inu = getattr(mat, 'inu', None)
        if inu is None:
            continue
        alt1 = getattr(inu, 'paintjob_alt_1', None)
        alt2 = getattr(inu, 'paintjob_alt_2', None)
        if not (alt1 or alt2):
            continue
        # Has a base image texture? Walk the material's nodes for an
        # IMAGE_TEXTURE — same approach as paintjob_ops uses.
        has_base = False
        if mat.use_nodes and mat.node_tree is not None:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image is not None:
                    has_base = True
                    break
        out.append(dict(
            name=mat.name,
            alt1=bool(alt1), alt2=bool(alt2),
            has_base=has_base))
    return out


def _gather_action_quat_groups():
    """Walk every Action and assemble (w,x,y,z) keyframe tuples for
    every rotation_quaternion fcurve group it contains."""
    # Lazy import keeps this module importable by tests' static
    # analysers; ops.animobj_ops itself imports bpy at module level.
    from .animobj_ops import _iter_action_fcurves

    out = []
    for action in bpy.data.actions:
        # path → {array_index: [keyframe_y_values]}
        per_path = {}
        for fc in _iter_action_fcurves(action):
            dp = fc.data_path or ''
            if not dp.endswith('rotation_quaternion'):
                continue
            slot = per_path.setdefault(dp, {})
            slot[fc.array_index] = [kp.co[1] for kp in fc.keyframe_points]

        groups = []
        for dp, comps in per_path.items():
            if set(comps.keys()) != {0, 1, 2, 3}:
                continue
            n = min(len(comps[i]) for i in range(4))
            for i in range(n):
                groups.append([comps[0][i], comps[1][i],
                               comps[2][i], comps[3][i]])
        if groups:
            out.append(dict(name=action.name, quat_groups=groups))
    return out


def _gather_modulate_color_meshes():
    out = []
    for obj in _scene_objects({'MESH'}):
        inu = getattr(obj, 'inu', None)
        if inu is None:
            continue
        mod_col = bool(getattr(inu, 'modulate_color', True))
        me = obj.data
        has_vcol = bool(compat.vcol_list(me))
        out.append(dict(name=obj.name,
                        modulate_color=mod_col,
                        has_vcol=has_vcol))
    return out


def _gather_mesh_names():
    return [obj.name for obj in _scene_objects({'MESH'})]


def _gather_classified_models():
    """Build (name, type, base) tuples for every MESH in the scene
    using the same suffix/prefix recogniser the export pipeline uses.
    Anything without a recognised suffix/prefix falls through to 'DFF'."""
    from ..tools.model_utils import get_model_type

    out = []
    for obj in _scene_objects({'MESH'}):
        model_type, base = get_model_type(obj)
        if not base:
            continue
        # base may carry a trailing separator from the strip — keep
        # the same lowercase-with-rstrip normalisation used by the
        # export grouping.
        base_clean = base.rstrip('_')
        out.append(dict(name=obj.name, type=model_type, base=base_clean))
    return out


def _gather_2dfx_empties():
    """Find Empty objects flagged as 2DFX containers and report what
    kind of object their parent is (or None)."""
    out = []
    for obj in _scene_objects({'EMPTY'}):
        inu = getattr(obj, 'inu', None)
        if inu is None:
            continue
        # The 2DFX flag lives on `inu.type` enum (string match — see
        # GTATOOLS_OT_attach_2dfx.poll). Older blends may not have
        # the prop; we treat absence as "not a 2DFX".
        kind = getattr(inu, 'type', None)
        if kind != '2DFX':
            continue
        parent = obj.parent
        out.append(dict(
            name=obj.name,
            parent_kind=(parent.type if parent is not None else None)))
    return out


def _gather_objects_with_model_id():
    out = []
    for obj in _scene_objects({'MESH'}):
        inu = getattr(obj, 'inu', None)
        mid = getattr(inu, 'model_id', 0) if inu else 0
        out.append(dict(name=obj.name, model_id=int(mid)))
    return out


def _gather_mesh_vert_counts():
    """Vertex counts for every MESH — used by both empty-mesh and
    large-mesh checks. We pull from the underlying Mesh datablock so
    modifiers don't inflate the count (the export goes through
    .data.vertices too)."""
    out = []
    for obj in _scene_objects({'MESH'}):
        me = obj.data
        n = len(me.vertices) if me is not None else 0
        out.append(dict(name=obj.name, vert_count=n))
    return out


def _gather_materials_with_texture_status():
    """For every material, record whether it's used on at least one
    MESH, whether its node tree contains any TEX_IMAGE node with an
    image bound, AND whether the material itself is a COL surface
    descriptor (flag-only, never textured by design).

    Mesh-side filter:
      • `inu.type == 'COL'`/'SHA'/'NON' meshes are excluded outright
        from the used_on_mesh tally, so a material that happens to be
        on only-collision meshes won't count as "used".

    Material-side filter (more reliable — catches Kam's-style imports
    where the COL mesh has inu.type='OBJ' by default):
      • inu.col_mat_index / col_flags / col_brightness / col_day_light
        / col_night_light non-zero — user has touched COL props
      • OR name starts with 'COL' — addon imports (`COL_<id>`,
        `COLlight_d<N>_n<N>`) and Kam's-style names use this prefix
    """
    from ..tools.model_utils import get_model_type

    used_on_mesh = set()
    for obj in _scene_objects({'MESH'}):
        inu = getattr(obj, 'inu', None)
        if inu is not None:
            kind = getattr(inu, 'type', 'OBJ')
            if kind in {'COL', 'SHA', 'NON'}:
                continue
        try:
            model_type, _ = get_model_type(obj)
        except Exception:
            model_type = None
        if model_type == 'COL':
            continue
        for slot in obj.material_slots:
            if slot.material is not None:
                used_on_mesh.add(slot.material.name)

    out = []
    for mat in bpy.data.materials:
        has_base = False
        if mat.use_nodes and mat.node_tree is not None:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image is not None:
                    has_base = True
                    break

        is_col = False
        inu = getattr(mat, 'inu', None)
        if inu is not None:
            if (getattr(inu, 'col_mat_index', 0)
                    or getattr(inu, 'col_flags', 0)
                    or getattr(inu, 'col_brightness', 0)
                    or getattr(inu, 'col_day_light', 0)
                    or getattr(inu, 'col_night_light', 0)):
                is_col = True
        if not is_col and mat.name.startswith('COL'):
            is_col = True

        out.append(dict(
            name=mat.name,
            has_base=has_base,
            used_on_mesh=mat.name in used_on_mesh,
            is_col_surface=is_col))
    return out


def _gather_configured_suffixes():
    scene = bpy.context.scene
    return {
        'DFF': getattr(scene, 'gtatools_suffix_dff', '_DFF'),
        'LOD': getattr(scene, 'gtatools_suffix_lod', '_LOD'),
        'COL': getattr(scene, 'gtatools_suffix_col', '_COL'),
    }


def _gather_object_scales():
    """Object-level transforms only — modifiers don't change obj.scale,
    and the DFF exporter applies obj.matrix_world.to_scale() so we
    care about that exact tuple."""
    out = []
    for obj in _scene_objects({'MESH', 'EMPTY'}):
        sx, sy, sz = obj.scale
        out.append(dict(name=obj.name, scale=(float(sx), float(sy), float(sz))))
    return out


def _gather_light_beam_meshes():
    out = []
    for obj in _scene_objects({'MESH'}):
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                continue
            inu = getattr(mat, 'inu', None)
            if inu is None:
                continue
            if getattr(inu, 'light_beam_asi', False):
                out.append(dict(name=obj.name, light_beam_asi=True))
                break
    return out


def _sa_light_asi_present():
    """Check if SA_Light.asi is present in the configured GTA root.
    Empty/missing root → False (so the check stays silent rather than
    raising spurious INFO entries when the user hasn't set the path)."""
    import os
    root = getattr(bpy.context.scene, 'gtatools_game_root', '') or ''
    if not root:
        # If user hasn't set game root, we can't tell — assume it's
        # there to avoid false-positive INFO noise. Power users who
        # haven't set the root probably know what they're doing.
        return True
    abs_root = bpy.path.abspath(root)
    if not os.path.isdir(abs_root):
        return True
    return os.path.isfile(os.path.join(abs_root, 'SA_Light.asi'))


def collect_all_issues():
    """Run every scope-wide check and return a flat list of issue dicts."""
    issues = []
    issues.extend(check_paintjobs(_gather_paintjob_materials()))
    issues.extend(check_quaternions(_gather_action_quat_groups()))
    issues.extend(check_modulate_color(_gather_modulate_color_meshes()))
    issues.extend(check_damage_pairs(_gather_mesh_names()))
    issues.extend(check_orphan_models(_gather_classified_models()))
    issues.extend(check_orphan_2dfx(_gather_2dfx_empties()))
    # 7 new checks added with the second batch (А, B, D, E, F, H, I)
    issues.extend(check_duplicate_model_ids(_gather_objects_with_model_id()))
    mesh_verts = _gather_mesh_vert_counts()
    issues.extend(check_empty_meshes(mesh_verts))
    issues.extend(check_large_meshes(mesh_verts))
    issues.extend(check_materials_without_texture(
        _gather_materials_with_texture_status()))
    mesh_names = [m['name'] for m in mesh_verts]
    issues.extend(check_suffix_consistency(
        mesh_names, _gather_configured_suffixes()))
    issues.extend(check_object_scale(_gather_object_scales()))
    issues.extend(check_light_beam_asi(
        _gather_light_beam_meshes(), _sa_light_asi_present()))
    return issues


# ── Scene-stored result rows ────────────────────────────────────────


class INUValidateIssue(bpy.types.PropertyGroup):
    """One line in the Validate Scene panel. Backed by Scene
    CollectionProperty so it survives between draws and across the
    Run → Goto/Fix interaction."""
    severity: StringProperty(default='WARNING')
    category: StringProperty(default='')
    message: StringProperty(default='')
    # Translation template + JSON-encoded args for interpolated
    # messages. When non-empty the panel does
    # ``T(template).format(**json.loads(args))`` so the user-facing
    # text follows the active locale. Empty when the message is
    # static and ``message`` itself is the displayed string.
    message_template: StringProperty(default='')
    message_args: StringProperty(default='')
    target_kind: StringProperty(default='')
    target_name: StringProperty(default='')
    fix_op_id: StringProperty(default='')
    fix_arg: StringProperty(default='')


# ── Operators ───────────────────────────────────────────────────────


class GTATOOLS_OT_validate_run(bpy.types.Operator):
    """Запустить полную проверку сцены: paintjob слоты, нормировку
    кватернионов в Action'ах, Modulate Color на прилайтах и парность
    _ok/_dam. Результаты пишутся в панель — кликом можно перейти к
    проблемному объекту или починить автоматически."""
    bl_idname = "gtatools.validate_run"
    bl_label = "INU: Validate Scene"
    bl_options = {'REGISTER'}

    def execute(self, context):
        issues = collect_all_issues()

        coll = context.scene.inu_validate_issues
        coll.clear()
        for d in issues:
            row = coll.add()
            row.severity = d['severity']
            row.category = d['category']
            row.message = d['message']
            row.message_template = d.get('message_template', '')
            row.message_args = d.get('message_args', '')
            row.target_kind = d['target_kind']
            row.target_name = d['target_name']
            row.fix_op_id = d['fix_op_id']
            row.fix_arg = d['fix_arg']

        errors = sum(1 for d in issues if d['severity'] == 'ERROR')
        warns = sum(1 for d in issues if d['severity'] == 'WARNING')
        infos = sum(1 for d in issues if d['severity'] == 'INFO')
        if errors:
            self.report({'ERROR'},
                        f"{T('Ошибок')}: {errors}, {T('предупреждений')}: {warns}")
        elif warns:
            self.report({'WARNING'},
                        f"{T('Предупреждений')}: {warns}")
        elif infos:
            # INFO-only sweep means everything is exportable; the items
            # are cosmetic notes (e.g. wonky viewport preview).
            self.report({'INFO'},
                        f"{T('Экспорт пройдёт OK, замечаний')}: {infos}")
        else:
            self.report({'INFO'}, T("Сцена готова к экспорту — проблем не найдено"))
        return {'FINISHED'}


class GTATOOLS_OT_validate_clear(bpy.types.Operator):
    """Очистить список результатов."""
    bl_idname = "gtatools.validate_clear"
    bl_label = "INU: Clear validation results"
    bl_options = {'REGISTER'}

    def execute(self, context):
        context.scene.inu_validate_issues.clear()
        return {'FINISHED'}


class GTATOOLS_OT_validate_goto(bpy.types.Operator):
    """Сделать активным объект/материал из строки результата."""
    bl_idname = "gtatools.validate_goto"
    bl_label = "INU: Go to validation target"
    bl_options = {'REGISTER'}

    target_kind: StringProperty()
    target_name: StringProperty()

    def execute(self, context):
        if self.target_kind == 'OBJECT':
            obj = bpy.data.objects.get(self.target_name)
            if obj is None:
                self.report({'WARNING'},
                            f"{T('Объект не найден')}: {self.target_name}")
                return {'CANCELLED'}
            for o in context.selected_objects:
                o.select_set(False)
            # Object may live in bpy.data but be excluded from the
            # active view layer (collection unchecked, hidden, or
            # orphan datablock from interrupted import). select_set
            # raises RuntimeError in that case — surface a friendly
            # message instead of crashing the operator.
            try:
                obj.select_set(True)
                context.view_layer.objects.active = obj
            except RuntimeError:
                self.report(
                    {'WARNING'},
                    f"{T('Объект вне View Layer')}: {obj.name} — "
                    f"{T('включи коллекцию в outliner')}")
                return {'CANCELLED'}
            self.report({'INFO'}, f"→ {obj.name}")
        elif self.target_kind == 'MATERIAL':
            mat = bpy.data.materials.get(self.target_name)
            if mat is None:
                self.report({'WARNING'},
                            f"{T('Материал не найден')}: {self.target_name}")
                return {'CANCELLED'}
            # Find any object that uses this material so the property
            # editor can land on it. Walk scene members only — orphan
            # datablocks aren't selectable.
            for obj in _scene_objects({'MESH'}):
                if any(s.material is mat for s in obj.material_slots):
                    for o in context.selected_objects:
                        o.select_set(False)
                    try:
                        obj.select_set(True)
                        context.view_layer.objects.active = obj
                    except RuntimeError:
                        self.report(
                            {'WARNING'},
                            f"{T('Объект вне View Layer')}: {obj.name}")
                        return {'CANCELLED'}
                    for i, slot in enumerate(obj.material_slots):
                        if slot.material is mat:
                            obj.active_material_index = i
                            break
                    self.report({'INFO'}, f"→ {mat.name} @ {obj.name}")
                    return {'FINISHED'}
            self.report({'INFO'},
                        f"{T('Материал без носителя')}: {mat.name}")
        elif self.target_kind == 'ACTION':
            act = bpy.data.actions.get(self.target_name)
            if act is None:
                self.report({'WARNING'},
                            f"{T('Action не найден')}: {self.target_name}")
                return {'CANCELLED'}
            obj = context.active_object
            if obj is not None and obj.animation_data is not None:
                obj.animation_data.action = act
                self.report({'INFO'},
                            f"→ Action {act.name} @ {obj.name}")
            else:
                self.report({'INFO'},
                            f"Action: {act.name} ({T('выбери armature и повтори')})")
        return {'FINISHED'}


class GTATOOLS_OT_validate_fix_quaternions(bpy.types.Operator):
    """Нормализовать все кватернионные ключи в указанном Action.
    Идентично тому что делает IFP-экспортёр на лету, но пишет правку
    обратно в Action — на след. экспорт уже нечего нормировать."""
    bl_idname = "gtatools.validate_fix_quaternions"
    bl_label = "INU: Fix quaternions in Action"
    bl_options = {'REGISTER', 'UNDO'}

    action_name: StringProperty()

    def execute(self, context):
        from .animobj_ops import _iter_action_fcurves
        from mathutils import Quaternion

        act = bpy.data.actions.get(self.action_name)
        if act is None:
            self.report({'ERROR'},
                        f"{T('Action не найден')}: {self.action_name}")
            return {'CANCELLED'}

        # Bucket fcurves by data_path so we can reassemble (w,x,y,z) at
        # each keyframe and write back the normalised component values.
        groups: dict[str, dict[int, bpy.types.FCurve]] = {}
        for fc in _iter_action_fcurves(act):
            dp = fc.data_path or ''
            if not dp.endswith('rotation_quaternion'):
                continue
            groups.setdefault(dp, {})[fc.array_index] = fc

        fixed = 0
        for dp, comps in groups.items():
            if set(comps.keys()) != {0, 1, 2, 3}:
                continue
            n = min(len(comps[i].keyframe_points) for i in range(4))
            for i in range(n):
                w = comps[0].keyframe_points[i].co[1]
                x = comps[1].keyframe_points[i].co[1]
                y = comps[2].keyframe_points[i].co[1]
                z = comps[3].keyframe_points[i].co[1]
                q = Quaternion((w, x, y, z))
                if q.magnitude == 0.0:
                    continue
                if abs(q.magnitude - 1.0) <= 1e-6:
                    continue
                q.normalize()
                comps[0].keyframe_points[i].co[1] = q.w
                comps[1].keyframe_points[i].co[1] = q.x
                comps[2].keyframe_points[i].co[1] = q.y
                comps[3].keyframe_points[i].co[1] = q.z
                fixed += 1
            for i in range(4):
                comps[i].update()

        self.report({'INFO'},
                    f"{T('Нормализовано ключей')}: {fixed} ({act.name})")
        return {'FINISHED'}


class GTATOOLS_OT_validate_fix_suffix(bpy.types.Operator):
    """Переименовать объект, заменив неправильный разделитель в
    суффиксе на тот, что задан в настройках суффиксов сцены.

    Применимо только к мисматчу типа «.DFF при настройке _DFF» —
    т.е. имя оканчивается на конфигурированный bare-token, но через
    другой разделитель. Двойной суффикс (body_LOD_DFF) не трогаем —
    там нет однозначного автоматического fix'а."""
    bl_idname = "gtatools.validate_fix_suffix"
    bl_label = "INU: Fix object suffix"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        if obj is None:
            self.report({'ERROR'},
                        f"{T('Объект не найден')}: {self.object_name}")
            return {'CANCELLED'}

        scene = context.scene
        configured = {
            'DFF': getattr(scene, 'gtatools_suffix_dff', '_DFF'),
            'LOD': getattr(scene, 'gtatools_suffix_lod', '_LOD'),
            'COL': getattr(scene, 'gtatools_suffix_col', '_COL'),
        }
        upper = obj.name.upper()
        for kind, sfx in configured.items():
            if not sfx or len(sfx) < 2:
                continue
            sep = sfx[0]
            rest = sfx[1:]
            if sep not in '_.':
                continue
            alt_sep = '.' if sep == '_' else '_'
            alt = (alt_sep + rest).upper()
            sfx_upper = sfx.upper()
            # Already correct → nothing to do for this kind.
            if upper.endswith(sfx_upper):
                continue
            if not upper.endswith(alt):
                continue
            # Replace the trailing alt-separator suffix with the
            # configured one. Preserve case of the rest by slicing
            # from the original (case-aware) name.
            new_name = obj.name[:-len(alt)] + sfx
            if new_name == obj.name:
                continue
            obj.name = new_name
            self.report(
                {'INFO'},
                f"{self.object_name} → {new_name}")
            return {'FINISHED'}

        self.report({'WARNING'},
                    T("Не нашёл несоответствия суффикса для этого объекта"))
        return {'CANCELLED'}


class GTATOOLS_OT_validate_fix_modulate_color(bpy.types.Operator):
    """Снять флаг Modulate Color у указанного объекта — устраняет
    flicker на прилайтных мешах."""
    bl_idname = "gtatools.validate_fix_modulate_color"
    bl_label = "INU: Disable Modulate Color"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        if obj is None:
            self.report({'ERROR'},
                        f"{T('Объект не найден')}: {self.object_name}")
            return {'CANCELLED'}
        inu = getattr(obj, 'inu', None)
        if inu is None:
            return {'CANCELLED'}
        inu.modulate_color = False
        self.report({'INFO'},
                    f"{T('Modulate Color снят')}: {obj.name}")
        return {'FINISHED'}


classes = (
    INUValidateIssue,
    GTATOOLS_OT_validate_run,
    GTATOOLS_OT_validate_clear,
    GTATOOLS_OT_validate_goto,
    GTATOOLS_OT_validate_fix_quaternions,
    GTATOOLS_OT_validate_fix_suffix,
    GTATOOLS_OT_validate_fix_modulate_color,
)
