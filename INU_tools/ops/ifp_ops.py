# INU_tools.ops.ifp_ops — IFP animation import/export/roundtrip/merge + preview toggle + apply.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import re

import bpy
from bpy.props import (
    StringProperty, BoolProperty, FloatProperty, EnumProperty,
)
from mathutils import Vector, Matrix

from .. import T


class GTATOOLS_OT_import_ifp(bpy.types.Operator):
    """Импорт IFP — анимации GTA SA"""
    bl_idname = "gtatools.import_ifp"
    bl_label = "INU: Import IFP"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ifp", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ifp_import import import_ifp
        try:
            actions = import_ifp(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"IFP: {len(actions)} animations imported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IFP import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_ifp(bpy.types.Operator):
    """Экспорт IFP — анимации GTA SA"""
    bl_idname = "gtatools.export_ifp"
    bl_label = "INU: Export IFP"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ifp", options={'HIDDEN'})
    package_name: StringProperty(name="Package", default="custom")
    ifp_format: EnumProperty(
        name=T("Формат"),
        description=T("Кодировка IFP-файла на диске. ANP3 — компактный формат GTA SA (int16). ANPK / ANP2 — chunked float32 (GTA III, VC, плюс совместим с SA)"),
        items=[
            ('ANPK', "ANPK / ANP2 (III, VC, SA)",
             T("Chunked float32 — III, VC, читается и в SA")),
            ('ANP3', "ANP3 (SA compressed)",
             T("Flat int16-compressed — родной формат GTA SA, минимальный размер файла")),
        ],
        default='ANPK',
    )
    decimate: BoolProperty(
        name=T("Прорежать ключи"),
        description=T("Удалять keyframe'ы которые лежат на линейной интерполяции между соседями. Уменьшает размер .ifp без потери качества — первый и последний ключ каждой кости сохраняются всегда"),
        default=False,
    )
    decimate_tol_rot: FloatProperty(
        name=T("Допуск поворота"),
        description=T("Max-norm tolerance по XYZW quaternion. 1e-3 безопасно — ANP3 квантует rotation c точностью 1/4096 ≈ 2.4e-4, поэтому ниже не имеет смысла"),
        default=1e-3, min=0.0, soft_min=1e-4, soft_max=1e-1,
        precision=5,
    )
    decimate_tol_trans: FloatProperty(
        name=T("Допуск позиции"),
        description=T("Max-norm tolerance по XYZ translation в DFF-единицах (обычно метры). 1e-3 = около 1 мм — незаметно при обычных масштабах сцены"),
        default=1e-3, min=0.0, soft_min=1e-4, soft_max=1e-1,
        precision=5,
    )
    active_only: BoolProperty(
        name=T("Только активную анимацию"),
        description=T(
            "Экспортировать ТОЛЬКО активную Action арматуры — одну анимацию, а "
            "не весь пак. По умолчанию экспорт собирает все импортированные "
            "(ifp_source) Actions + активную; с этой галкой — ровно одну "
            "активную, будь она своя новая ИЛИ существующая из импортнутого "
            "ped.ifp."),
        default=False,
    )

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "custom.ifp"
        # Default the IFP format from the scene's active game. ANP3 is
        # SA-native (compact int16); III/VC engines don't read it, so
        # they get the universal ANPK. User can still override in the
        # export dialog before confirming.
        from ..core import game_versions as gv
        game = gv.game_of_scene(context.scene)
        self.ifp_format = 'ANP3' if game == 'SA' else 'ANPK'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "package_name")
        layout.prop(self, "active_only")
        layout.prop(self, "ifp_format")
        layout.prop(self, "decimate")
        if self.decimate:
            box = layout.box()
            box.prop(self, "decimate_tol_rot")
            box.prop(self, "decimate_tol_trans")

    def execute(self, context):
        from .ifp_export import validate_action_bones

        # Bone-name validator — warn (not block) when Action fcurves
        # reference bones the target armature doesn't have. Those rows
        # would get bone_id=-1 and the game would silently skip them.
        armature = context.active_object if (
            context.active_object and context.active_object.type == 'ARMATURE'
        ) else None
        if armature and armature.animation_data and armature.animation_data.action:
            unknown, _known = validate_action_bones(
                armature.animation_data.action, armature)
            if unknown:
                preview = ', '.join(unknown[:5])
                more = f" (+{len(unknown) - 5})" if len(unknown) > 5 else ""
                self.report({'WARNING'},
                    f"{T('Неизвестные кости в Action:')} {preview}{more}")

        # Build → optionally decimate → write. Three separate calls so
        # we can measure decimation savings (removed/total) for the
        # report line. export_ifp() would do all three internally but
        # would hide the count behind a single return.
        from .ifp_export import build_ifp_from_actions
        from ..core.ifp import write_ifp, decimate_ifp

        try:
            # active_only → export exactly the armature's active Action (one
            # animation), bypassing the ifp_source pack collection. Works for a
            # freshly-made Action or one of the imported ped.ifp Actions alike.
            actions = None
            if self.active_only:
                if not (armature and armature.animation_data
                        and armature.animation_data.action):
                    self.report({'WARNING'},
                                T("Нет активной анимации на арматуре"))
                    return {'CANCELLED'}
                actions = [armature.animation_data.action]

            ifp = build_ifp_from_actions(
                actions=actions, armature=armature,
                package_name=self.package_name)
            if not ifp.animations:
                self.report({'WARNING'}, T("Нет анимаций для экспорта"))
                return {'CANCELLED'}

            removed = 0
            total_before = sum(
                len(b.keyframes) for a in ifp.animations for b in a.bones)
            if self.decimate and total_before:
                removed, _ = decimate_ifp(
                    ifp, self.decimate_tol_rot, self.decimate_tol_trans)

            # Defensive: ANP3 is SA-only. If the user kept ANP3 selected
            # but the scene's game is III/VC, downgrade to ANPK and warn
            # — otherwise the file would be unreadable in the target
            # game's engine.
            from ..core import game_versions as gv
            _scene_game = gv.game_of_scene(context.scene)
            _fmt = self.ifp_format
            if _fmt == 'ANP3' and _scene_game != 'SA':
                self.report({'WARNING'},
                    T("ANP3 не поддерживается в {0} — переключаюсь на ANPK").format(_scene_game))
                _fmt = 'ANPK'

            count = write_ifp(self.filepath, ifp, format=_fmt)

            if self.decimate and total_before:
                pct = (removed / total_before * 100.0)
                self.report({'INFO'},
                    f"IFP {self.ifp_format}: {count} {T('анимаций')}, "
                    f"{T('прорежено')} {removed}/{total_before} "
                    f"({T('ключей')}, −{pct:.1f}%)")
            else:
                self.report({'INFO'},
                    f"IFP {self.ifp_format}: {count} animations exported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IFP export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_ifp_roundtrip(bpy.types.Operator):
    """Диагностика round-trip для IFP — проверяет что read → write → read
    не теряет анимации, не путает кости и не ломает квартернионы.

    Выбранный файл не меняется: экспорт идёт во временный файл рядом,
    результат сравнивается с оригиналом и удаляется. Отчёт показывает
    счётчики и максимальные численные отклонения (dRot, dTrans, dTime)"""
    bl_idname = "gtatools.ifp_roundtrip"
    bl_label = "INU: Validate IFP Round-trip"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ifp", options={'HIDDEN'})

    # Stashed on the operator between execute and the follow-up dialog
    # so draw() can format the multi-line report without re-running the
    # round-trip (it's not cheap on ped.ifp with 294 anims).
    _last_report: str = ""

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from ..core.ifp import roundtrip_test
        if not self.filepath:
            self.report({'ERROR'}, T("Укажите .ifp файл"))
            return {'CANCELLED'}

        r = roundtrip_test(self.filepath)

        if r['error']:
            self.report({'ERROR'}, f"IFP round-trip: {r['error']}")
            return {'CANCELLED'}

        # Build human-readable report
        lines = []
        lines.append(f"{T('Анимации:')} {r['anims_in']} → {r['anims_out']}")
        lines.append(f"{T('Кости:')} {r['bones_in']} → {r['bones_out']}")
        lines.append(f"{T('Ключи:')} {r['keyframes_in']} → {r['keyframes_out']}")
        lines.append(f"{T('Макс. отклонение поворота:')} {r['max_rot_delta']:.6f}")
        lines.append(f"{T('Макс. отклонение позиции:')} {r['max_trans_delta']:.6f}")
        lines.append(f"{T('Макс. отклонение времени:')} {r['max_time_delta']:.6f}")

        if r['missing_anims']:
            mi = r['missing_anims'][:5]
            more = f" (+{len(r['missing_anims']) - 5})" if len(r['missing_anims']) > 5 else ""
            lines.append(f"{T('Потеряны анимации:')} {', '.join(mi)}{more}")

        if r['missing_bones']:
            lines.append(
                f"{T('Анимаций с потерянными костями:')} {len(r['missing_bones'])}")

        if r['kf_mismatches']:
            lines.append(
                f"{T('Несовпадений по числу ключей:')} {len(r['kf_mismatches'])}")

        # Status banner: OK if everything matches and deltas are tiny.
        ok = (
            r['anims_in'] == r['anims_out'] and
            r['bones_in'] == r['bones_out'] and
            r['keyframes_in'] == r['keyframes_out'] and
            not r['missing_anims'] and not r['missing_bones'] and
            not r['kf_mismatches']
        )
        verdict = T("Round-trip: OK ✓") if ok else T("Round-trip: расхождения ⚠")
        header = f"{verdict}\n" + "\n".join(lines)

        # Print full report to console for the copy-paste workflow
        print(f"\n[IFP Round-trip] {self.filepath}")
        print(header)

        # Status bar for the short reminder
        self.report(
            {'INFO' if ok else 'WARNING'},
            f"{verdict} — "
            f"anims {r['anims_in']}→{r['anims_out']}, "
            f"Δrot {r['max_rot_delta']:.4f}, "
            f"Δtrans {r['max_trans_delta']:.4f}"
        )
        return {'FINISHED'}


class GTATOOLS_OT_merge_ifp(bpy.types.Operator):
    """Добавить или заменить анимации в существующем IFP-паке.

    Открывает ped.ifp / anim.ifp (или любой другой .ifp), подменяет
    анимации по имени (case-insensitive) или дописывает в конец, и
    сохраняет файл обратно. Остальные анимации пака сохраняются.
    Позволяет обойтись без внешних IFP-редакторов при правке одной
    анимации в ванильном паке"""
    bl_idname = "gtatools.merge_ifp"
    bl_label = "INU: Merge Into IFP"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ifp", options={'HIDDEN'})
    package_name: StringProperty(
        name="Package",
        description=T("Имя пакета (оставьте пустым чтобы сохранить имя существующего файла)"),
        default="",
    )
    use_current_action: BoolProperty(
        name=T("Только текущая анимация"),
        description=T("Экспортировать только активную Action арматуры (Action Editor). Иначе — все Actions с меткой ifp_source плюс активная"),
        default=True,
    )
    decimate: BoolProperty(
        name=T("Прорежать ключи"),
        description=T("Удалять keyframe'ы которые лежат на линейной интерполяции между соседями. Уменьшает размер .ifp без потери качества — первый и последний ключ каждой кости сохраняются всегда"),
        default=False,
    )
    decimate_tol_rot: FloatProperty(
        name=T("Допуск поворота"),
        default=1e-3, min=0.0, soft_min=1e-4, soft_max=1e-1,
        precision=5,
    )
    decimate_tol_trans: FloatProperty(
        name=T("Допуск позиции"),
        default=1e-3, min=0.0, soft_min=1e-4, soft_max=1e-1,
        precision=5,
    )

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "ped.ifp"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ifp_export import validate_action_bones

        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, T("Выделите скелет (Armature)"))
            return {'CANCELLED'}

        # Narrow actions to only the one currently bound if the user
        # wants the focused flow (editing ONE anim and pushing it back).
        actions = None
        if self.use_current_action:
            if armature.animation_data and armature.animation_data.action:
                actions = [armature.animation_data.action]
            else:
                self.report({'ERROR'},
                    T("У арматуры нет активной Action — включите опцию «Только текущая» выкл. или присвойте Action"))
                return {'CANCELLED'}

        # Bone-name validation — merge into ped.ifp with a mismatched
        # skeleton is the classic silent-fail path (bone_id=-1 rows get
        # skipped in-game, animation plays empty). Warn per-Action so
        # the user can rename bones before committing.
        actions_to_check = actions if actions is not None else (
            [a for a in bpy.data.actions
             if a.get('ifp_source') or (
                 armature.animation_data
                 and armature.animation_data.action == a)]
        )
        for act in actions_to_check:
            unknown, _known = validate_action_bones(act, armature)
            if unknown:
                preview = ', '.join(unknown[:5])
                more = f" (+{len(unknown) - 5})" if len(unknown) > 5 else ""
                self.report({'WARNING'},
                    f"{act.name}: {T('неизвестные кости:')} {preview}{more}")

        # Same three-step flow as Export IFP — gives us the decimation
        # savings counter (removed/total) for the report.
        from .ifp_export import build_ifp_from_actions
        from ..core.ifp import merge_ifp, decimate_ifp

        try:
            ifp = build_ifp_from_actions(
                actions=actions, armature=armature,
                package_name=self.package_name or 'ped')
            if not ifp.animations:
                self.report({'WARNING'}, T("Нет анимаций для merge"))
                return {'CANCELLED'}

            removed = 0
            total_before = sum(
                len(b.keyframes) for a in ifp.animations for b in a.bones)
            if self.decimate and total_before:
                removed, _ = decimate_ifp(
                    ifp, self.decimate_tol_rot, self.decimate_tol_trans)

            replaced, added = merge_ifp(
                self.filepath, ifp.animations,
                package_name=self.package_name or None)

            if self.decimate and total_before:
                pct = (removed / total_before * 100.0)
                self.report({'INFO'},
                    f"IFP: {T('заменено')} {replaced}, {T('добавлено')} {added}, "
                    f"{T('прорежено')} {removed}/{total_before} (−{pct:.1f}%)")
            else:
                self.report({'INFO'},
                    f"IFP: {T('заменено')} {replaced}, {T('добавлено')} {added}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IFP merge error: {e}")
            return {'CANCELLED'}


class GTATOOLS_OT_ifp_preview_toggle(bpy.types.Operator):
    """Переключить живой preview IFP-анимации без коммита в Action.

    Позволяет быстро пробежаться по 294 ванильным анимациям `ped.ifp`
    простым переключением Action-dropdown'а без захламления Action
    Editor'а. Handler frame_change_post напрямую пишет в pose bones
    при скрабе Timeline. Повторный клик — выключает preview и
    восстанавливает предыдущий Action арматуры"""
    bl_idname = "gtatools.ifp_preview_toggle"
    bl_label = "INU: Preview"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        from .ifp_import import preview_start, preview_stop, preview_is_active

        armature = context.active_object

        if preview_is_active():
            ok, msg = preview_stop()
            self.report({'INFO'}, msg)
            return {'FINISHED'} if ok else {'CANCELLED'}

        name = context.scene.inu_settings.gtatools_ifp_action
        if not name:
            self.report({'ERROR'}, T("Выберите анимацию в списке"))
            return {'CANCELLED'}

        ok, msg = preview_start(armature, name)
        if ok:
            self.report({'INFO'}, msg)
            return {'FINISHED'}
        self.report({'ERROR'}, msg)
        return {'CANCELLED'}


class GTATOOLS_OT_apply_ifp(bpy.types.Operator):
    """Применить IFP анимацию к выделенному скелету"""
    bl_idname = "gtatools.apply_ifp"
    bl_label = "INU: Apply IFP Animation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and
                context.scene.inu_settings.gtatools_ifp_action != '')

    def execute(self, context):
        from .ifp_import import apply_ifp_action
        name = context.scene.inu_settings.gtatools_ifp_action
        armature = context.active_object

        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, T("Выделите скелет (Armature)"))
            return {'CANCELLED'}

        ok, msg = apply_ifp_action(name, armature, context)
        if ok:
            self.report({'INFO'}, msg)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}


class GTATOOLS_OT_fix_quat_signs(bpy.types.Operator):
    """Исправить sign-discontinuities кватернионов на диапазоне кадров.
    Между двумя соседними ключами с dot < 0 кость крутится длинной
    дорогой через 360°. Скрипт находит такие пары и инвертирует знак
    кватерниона на втором ключе — q и -q описывают одинаковую ротацию,
    но интерполяция между ними после флипа идёт коротким путём.

    Идемпотентный — повторный прогон не ухудшит, иногда нужен 2-й
    проход чтобы вылезли ранее скрытые разрывы."""
    bl_idname = "gtatools.fix_quat_signs"
    bl_label = "INU: Fix Quaternion Sign Discontinuities"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE'
                and obj.animation_data
                and obj.animation_data.action is not None)

    def execute(self, context):
        from collections import defaultdict
        arm = context.active_object
        action = arm.animation_data.action
        slot = arm.animation_data.action_slot
        scene = context.scene
        start = scene.inu_settings.gtatools_anim_fix_start
        end = scene.inu_settings.gtatools_anim_fix_end

        fcurves = []
        for layer in action.layers:
            for strip in layer.strips:
                cb = strip.channelbag(slot) if slot else None
                if cb:
                    fcurves.extend(cb.fcurves)

        quat_by_bone = defaultdict(dict)
        for fc in fcurves:
            if fc.data_path.endswith('rotation_quaternion'):
                s = fc.data_path.find('"') + 1
                e = fc.data_path.rfind('"')
                bone_name = fc.data_path[s:e]
                quat_by_bone[bone_name][fc.array_index] = fc

        total_flipped = 0
        for bone_name, axis_fcs in quat_by_bone.items():
            if len(axis_fcs) != 4:
                continue
            frame_to_kp_idx = [
                {int(kp.co.x): i for i, kp in enumerate(axis_fcs[j].keyframe_points)}
                for j in range(4)
            ]
            all_frames = sorted(set().union(*frame_to_kp_idx))

            prev_q = None
            for f in all_frames:
                if f < start or f > end:
                    prev_q = None  # сбрасываем цепочку вне диапазона
                    continue
                q = [axis_fcs[j].evaluate(f) for j in range(4)]
                if prev_q is not None:
                    dot = sum(prev_q[j] * q[j] for j in range(4))
                    if dot < 0:
                        for j in range(4):
                            if f in frame_to_kp_idx[j]:
                                kp = axis_fcs[j].keyframe_points[frame_to_kp_idx[j][f]]
                                kp.co.y = -kp.co.y
                                kp.handle_left.y  = -kp.handle_left.y
                                kp.handle_right.y = -kp.handle_right.y
                                q[j] = -q[j]
                        for j in range(4):
                            axis_fcs[j].update()
                        total_flipped += 1
                prev_q = q

        self.report(
            {'INFO'},
            f"{T('Перевёрнуто ключей')}: {total_flipped} "
            f"({T('диапазон')} {start}–{end})")
        return {'FINISHED'}


def _mirror_lr_partner(name, valid_names):
    """GTA SA left/right bone partner by name, or self for centre bones.

    Handles 'L UpperArm'↔'R UpperArm', 'L Thigh'↔'R Thigh', 'L breast'↔…
    and the 'Bip01 L Clavicle'↔'Bip01 R Clavicle' embedded form. Falls
    back to self when no partner exists in the armature."""
    p = None
    if name[:2] == 'L ':
        p = 'R ' + name[2:]
    elif name[:2] == 'R ':
        p = 'L ' + name[2:]
    elif ' L ' in name:
        p = name.replace(' L ', ' R ', 1)
    elif ' R ' in name:
        p = name.replace(' R ', ' L ', 1)
    return p if (p and p in valid_names) else name


def _bones_parent_first(arm):
    """Pose bones ordered parents-before-children (needed so setting a
    child's armature-space matrix resolves against its already-posed
    parent)."""
    ordered, seen = [], set()

    def visit(pb):
        if pb.name in seen:
            return
        if pb.parent is not None:
            visit(pb.parent)
        seen.add(pb.name)
        ordered.append(pb)

    for pb in arm.pose.bones:
        visit(pb)
    return ordered


class GTATOOLS_OT_mirror_anim(bpy.types.Operator):
    """Отзеркалить активную анимацию по оси X/Y/Z (in-place).

    Blender-овские встроенные зеркала ломают GTA-анимацию, потому что
    GTA-риг не именует кости .L/.R и имеет свой roll/rest. Здесь зеркало
    делается в armature-space через FK: для каждого кадра читаем мировую
    матрицу каждой кости, отражаем её конъюгацией `flip @ W @ flip`
    (позиция и поворот отражаются, det остаётся +1 — без негатив-скейла),
    и назначаем результат ПАРНОЙ L/R кости (при включённом обмене).
    Так «повернуть налево» превращается в «повернуть направо», а не в
    вывернутую наизнанку позу."""
    bl_idname = "gtatools.mirror_anim"
    bl_label = "INU: Mirror Animation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE'
                and obj.animation_data
                and obj.animation_data.action is not None)

    def execute(self, context):
        arm = context.active_object
        action = arm.animation_data.action
        slot = arm.animation_data.action_slot

        # Gather the action's fcurves (layered 5.x + legacy fallback).
        fcurves = []
        for layer in getattr(action, 'layers', []):
            for strip in layer.strips:
                cbs = []
                if slot is not None:
                    try:
                        cb = strip.channelbag(slot)
                        if cb:
                            cbs.append(cb)
                    except Exception:
                        pass
                for cb in getattr(strip, 'channelbags', []):
                    if cb not in cbs:
                        cbs.append(cb)
                for cb in cbs:
                    fcurves.extend(cb.fcurves)
        if not fcurves:
            fcurves = list(getattr(action, 'fcurves', []))

        # Index every pose-bone fcurve by (bone, property, array_index).
        fmap = {}
        for fc in fcurves:
            dp = fc.data_path
            if not dp.startswith('pose.bones['):
                continue
            bname = dp[dp.find('"') + 1:dp.rfind('"')]
            prop = dp.rsplit('.', 1)[-1]
            fmap[(bname, prop, fc.array_index)] = fc

        valid = {pb.name for pb in arm.pose.bones}

        # Plain L/R key swap: for every 'L …'↔'R …' bone pair, swap the
        # keyframe VALUES of their matching channels (rotation + location).
        # Nothing else — no reflection, no axis math.
        swapped = 0
        done = set()
        for (bname, prop, idx), fc in list(fmap.items()):
            partner = _mirror_lr_partner(bname, valid)
            if partner == bname:
                continue
            pair_key = (min(bname, partner), max(bname, partner), prop, idx)
            if pair_key in done:
                continue
            done.add(pair_key)
            pfc = fmap.get((partner, prop, idx))
            if pfc is None:
                continue
            a = {round(kp.co.x): kp for kp in fc.keyframe_points}
            b = {round(kp.co.x): kp for kp in pfc.keyframe_points}
            for f in set(a) & set(b):
                ka, kb = a[f], b[f]
                va, vb = ka.co.y, kb.co.y
                ka.co = (ka.co.x, vb)
                kb.co = (kb.co.x, va)
                swapped += 1
            fc.update()
            pfc.update()

        if not swapped:
            self.report({'WARNING'}, T("Не найдено парных L/R костей"))
            return {'CANCELLED'}
        self.report({'INFO'}, f"{T('Переставлено ключей L/R')}: {swapped}")
        return {'FINISHED'}


class GTATOOLS_OT_smooth_between_anchors(bpy.types.Operator):
    """Сгладить ключи между выделенными опорными.

    Use-case: запечённая анимация с ключом на каждом кадре (например 700
    ключей). Хочешь опустить кость на кадре 70 — двигаешь её там, потом
    в Dope Sheet/Graph Editor выделяешь 3 ключа (50, 70, 90: первый,
    редактированный, последний) и нажимаешь эту кнопку. Промежуточные
    ключи (51-69 и 71-89) перезаписываются smooth-step интерполяцией
    между соседними опорными — будто там никаких ключей и не было.

    Режимы оси:
    - ALL — обрабатывает ВСЕ F-curve (включая rotation, scale) в bone-
      local координатах. Быстро.
    - WORLD_X/Y/Z — обрабатывает только .location и считает в МИРОВЫХ
      координатах. Учитывает поворот родительских костей и armature.
      Медленнее (per-frame depsgraph eval), но даёт правильный «по Z
      вниз» эффект независимо от ориентации кости.

    Анкоры берутся из выделенных ключей, минимум 2.
    Структура «ключ на каждом кадре» сохраняется (важно для round-trip
    в IFP)."""
    bl_idname = "gtatools.smooth_between_anchors"
    bl_label = "INU: Smooth Between Anchors"
    bl_options = {'REGISTER', 'UNDO'}

    use_cubic: BoolProperty(
        name="Smooth (cubic)",
        description=("True — кубический ease-in/out (без углов на анкорах). "
                     "False — линейная интерполяция"),
        default=True,
    )

    axis_mode: EnumProperty(
        name="Axis",
        description="Ось вдоль которой сглаживать",
        items=[
            ('ALL', "Все каналы (local)",
             "Обработать все F-curve в bone-local координатах "
             "(rotation, location, любые свойства)"),
            ('WORLD_X', "World X",
             "Только translation, по мировой оси X "
             "(per-frame depsgraph eval, медленнее)"),
            ('WORLD_Y', "World Y",
             "Только translation, по мировой оси Y"),
            ('WORLD_Z', "World Z",
             "Только translation, по мировой оси Z"),
        ],
        default='ALL',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.animation_data
                and obj.animation_data.action is not None)

    @staticmethod
    def _ease(t, cubic):
        return t * t * (3.0 - 2.0 * t) if cubic else t

    def _collect_fcurves(self, action, slot):
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                cb = strip.channelbag(slot) if slot else None
                if cb:
                    out.extend(cb.fcurves)
        return out

    def _smooth_all_local(self, context):
        """Original behavior: process every F-curve in bone-local space."""
        obj = context.active_object
        action = obj.animation_data.action
        slot = obj.animation_data.action_slot
        fcurves = self._collect_fcurves(action, slot)

        total_modified = 0
        curves_processed = 0

        for fc in fcurves:
            anchors = sorted(
                ((int(round(kp.co.x)), kp.co.y)
                 for kp in fc.keyframe_points
                 if kp.select_control_point),
                key=lambda p: p[0],
            )
            if len(anchors) < 2:
                continue

            for (a, va), (b, vb) in zip(anchors, anchors[1:]):
                if a == b:
                    continue
                span = float(b - a)
                for kp in fc.keyframe_points:
                    f = int(round(kp.co.x))
                    if a < f < b:
                        t = self._ease((f - a) / span, self.use_cubic)
                        new_val = va + t * (vb - va)
                        kp.co.y = new_val
                        kp.handle_left.y = new_val
                        kp.handle_right.y = new_val
                        total_modified += 1

            fc.update()
            curves_processed += 1

        if curves_processed == 0:
            self.report({'WARNING'},
                T("Выдели минимум 2 ключа в Dope Sheet как опорные"))
            return {'CANCELLED'}

        self.report({'INFO'},
            f"{T('Сглажено ключей')}: {total_modified} "
            f"({curves_processed} F-curves)")
        return {'FINISHED'}

    def _smooth_world_axis(self, context, axis_idx):
        """World-space smoothing: target a single world axis, write the
        corresponding local-translation deltas back to the F-curves.

        Heavy operation — sets scene.frame at every anchor and every
        in-between frame so depsgraph gives us accurate parent matrices
        per frame. For ~700 frames typically completes in a few seconds.
        """
        obj = context.active_object
        action = obj.animation_data.action
        slot = obj.animation_data.action_slot
        scene = context.scene

        # Group .location F-curves by bone name.
        loc_by_bone = {}
        for fc in self._collect_fcurves(action, slot):
            if not fc.data_path.endswith('.location'):
                continue
            m = re.match(r'pose\.bones\["([^"]+)"\]\.location', fc.data_path)
            if not m:
                continue
            loc_by_bone.setdefault(m.group(1), {})[fc.array_index] = fc

        if not loc_by_bone:
            self.report({'WARNING'},
                T("Не найдено translation-каналов для смещения в мировом пространстве"))
            return {'CANCELLED'}

        saved_frame = scene.frame_current
        total_modified = 0
        bones_processed = 0

        try:
            for bone_name, axis_fcs in loc_by_bone.items():
                pose_bone = obj.pose.bones.get(bone_name)
                if pose_bone is None:
                    continue

                # Anchor frames = union of selected keys across X/Y/Z curves
                anchor_frames = set()
                for fc in axis_fcs.values():
                    for kp in fc.keyframe_points:
                        if kp.select_control_point:
                            anchor_frames.add(int(round(kp.co.x)))
                if len(anchor_frames) < 2:
                    continue
                anchor_frames = sorted(anchor_frames)

                # Sample world head position component at each anchor.
                anchor_world_val = {}
                for f in anchor_frames:
                    scene.frame_set(f)
                    anchor_world_val[f] = (obj.matrix_world @ pose_bone.head)[axis_idx]

                # In-between frames: any frame that has a key on any axis
                # and falls strictly between two anchors.
                all_keyed_frames = set()
                for fc in axis_fcs.values():
                    for kp in fc.keyframe_points:
                        all_keyed_frames.add(int(round(kp.co.x)))

                for a, b in zip(anchor_frames, anchor_frames[1:]):
                    if a == b:
                        continue
                    span = float(b - a)
                    va, vb = anchor_world_val[a], anchor_world_val[b]

                    for f in sorted(all_keyed_frames):
                        if not (a < f < b):
                            continue
                        t = self._ease((f - a) / span, self.use_cubic)
                        target_world_val = va + t * (vb - va)

                        scene.frame_set(f)
                        current_world = obj.matrix_world @ pose_bone.head
                        delta_world_axis = target_world_val - current_world[axis_idx]
                        if abs(delta_world_axis) < 1e-9:
                            continue

                        # Map world delta vector → bone-local delta vector.
                        # world_delta = (armature_world × parent_armature × bone_rest_local).to_3x3() @ local_delta
                        parent_arm = (pose_bone.parent.matrix.to_3x3()
                                      if pose_bone.parent
                                      else Matrix.Identity(3))
                        bone_rest = pose_bone.bone.matrix_local.to_3x3()
                        M = obj.matrix_world.to_3x3() @ parent_arm @ bone_rest

                        world_delta_vec = Vector((0.0, 0.0, 0.0))
                        world_delta_vec[axis_idx] = delta_world_axis
                        local_delta_vec = M.inverted() @ world_delta_vec

                        # Apply the delta to every axis keyframe at this frame.
                        for ax_i, fc in axis_fcs.items():
                            for kp in fc.keyframe_points:
                                if int(round(kp.co.x)) == f:
                                    kp.co.y += local_delta_vec[ax_i]
                                    kp.handle_left.y += local_delta_vec[ax_i]
                                    kp.handle_right.y += local_delta_vec[ax_i]
                                    total_modified += 1
                                    break

                for fc in axis_fcs.values():
                    fc.update()
                bones_processed += 1
        finally:
            scene.frame_set(saved_frame)

        if bones_processed == 0:
            self.report({'WARNING'},
                T("Выдели минимум 2 ключа .location в Dope Sheet как опорные"))
            return {'CANCELLED'}

        axis_letter = ('X', 'Y', 'Z')[axis_idx]
        self.report({'INFO'},
            f"World-{axis_letter}: {T('сглажено ключей')} "
            f"{total_modified} ({bones_processed} bones)")
        return {'FINISHED'}

    def execute(self, context):
        if self.axis_mode == 'ALL':
            return self._smooth_all_local(context)
        axis_idx = {'WORLD_X': 0, 'WORLD_Y': 1, 'WORLD_Z': 2}[self.axis_mode]
        return self._smooth_world_axis(context, axis_idx)


class GTATOOLS_OT_delete_active_action(bpy.types.Operator):
    """Удалить активную Action арматуры из файла полностью.
    В отличие от кнопки X в Action Editor (которая только отвязывает),
    этот оператор стирает Action из bpy.data.actions — полезно чтобы
    в IFP-экспорт не попадали забытые анимации."""
    bl_idname = "gtatools.delete_active_action"
    bl_label = "INU: Delete Active Action"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE'
                and obj.animation_data
                and obj.animation_data.action is not None)

    def execute(self, context):
        armature = context.active_object
        action = armature.animation_data.action
        name = action.name
        try:
            bpy.data.actions.remove(action, do_unlink=True)
        except Exception as e:
            self.report({'ERROR'}, f"{T('Не удалось удалить')}: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"{T('Удалена Action')}: {name}")
        return {'FINISHED'}


