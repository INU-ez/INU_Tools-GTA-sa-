# INU_tools.ops.ifp_ops — IFP animation import/export/roundtrip/merge + preview toggle + apply.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import os
import bpy
import bmesh
from bpy.props import (
    StringProperty, BoolProperty, FloatProperty, FloatVectorProperty,
    IntProperty, EnumProperty, CollectionProperty, PointerProperty,
)

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

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "custom.ifp"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "package_name")
        layout.prop(self, "ifp_format")
        layout.prop(self, "decimate")
        if self.decimate:
            box = layout.box()
            box.prop(self, "decimate_tol_rot")
            box.prop(self, "decimate_tol_trans")

    def execute(self, context):
        from .ifp_export import export_ifp, validate_action_bones

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
            ifp = build_ifp_from_actions(
                armature=armature, package_name=self.package_name)
            if not ifp.animations:
                self.report({'WARNING'}, T("Нет анимаций для экспорта"))
                return {'CANCELLED'}

            removed = 0
            total_before = sum(
                len(b.keyframes) for a in ifp.animations for b in a.bones)
            if self.decimate and total_before:
                removed, _ = decimate_ifp(
                    ifp, self.decimate_tol_rot, self.decimate_tol_trans)

            count = write_ifp(self.filepath, ifp, format=self.ifp_format)

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
        from .ifp_export import merge_actions_into_ifp, validate_action_bones

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

        name = context.scene.gtatools_ifp_action
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
                context.scene.gtatools_ifp_action != '')

    def execute(self, context):
        from .ifp_import import apply_ifp_action
        name = context.scene.gtatools_ifp_action
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


classes = (
    GTATOOLS_OT_import_ifp,
    GTATOOLS_OT_export_ifp,
    GTATOOLS_OT_ifp_roundtrip,
    GTATOOLS_OT_merge_ifp,
    GTATOOLS_OT_ifp_preview_toggle,
    GTATOOLS_OT_apply_ifp,
)
