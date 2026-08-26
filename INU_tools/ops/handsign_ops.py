# INU_tools.ops.handsign_ops
# «Handsign Tools» — авторинг жестов банды (ghands.ifp).
#
# В GTA SA знак банды = ТРИ отдельных скелета / анимации в одном ghands.ifp:
#   • gsignN / gsignNlh — поза РУК на скелете игрока (lh-вариант = только левая
#                         рука, когда в правой руке оружие),
#   • lhgsignN          — пальцы левой кисти shandl.dff,
#   • rhgsignN          — пальцы правой кисти shandr.dff.
# Всего 20 блоков: gsign1..5 + gsign1lh..5lh + lhgsign1..5 + rhgsign1..5.
# ВАЖНО: пальцы экспортятся в ИСХОДНОЙ rest-позиции сами — Child Of висит на
# ОБЪЕКТЕ кисти, а IFP-экспорт читает локальные позы костей, не мировые.
# Поэтому «запекать назад в origin» перед экспортом НЕ надо.
# Кисти shandl/shandr — ОТДЕЛЬНЫЕ модели со своим скелетом ( L ForeArm01 →
#  L Hand01 → пальцы), которые игра в рантайме цепляет к запястьям игрока
# ( L Hand /  R Hand). Сливать кости НЕ надо — экспорт идёт по каждой
# armature отдельно (штатным IFP-экспортом).
#
# Единственное новое здесь — «Прицепить кисти»: Child Of на кости запястий,
# чтобы кисти ездили за рукой во вьюпорте при анимации. Кости не меняются.

import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty, FloatProperty

from .. import T


_CON_PREFIX = 'INU Handsign'

# Пары «кость кисти → кость скелета игрока» (совет ligabesar): предплечье и
# запястье кисти следуют за предплечьем/запястьем игрока; кисть остаётся
# отдельной armature. _find_bone регистро-/пробел-устойчив, поэтому 'ForeArm'
# совпадёт и с ' L ForeArm', и с 'L Forearm'.
_PAIRS_L = (('L ForeArm01', 'L ForeArm'), ('L Hand01', 'L Hand'))
_PAIRS_R = (('R ForeArm01', 'R ForeArm'), ('R Hand01', 'R Hand'))

# Каноничные SA bone_id из ванильного ghands.ifp (ключи — имя кости в нижнем
# регистре без ведущих/хвостовых пробелов). Экспорт бэкфиллит id по имени,
# иначе в ANP3 без верного bone_id игра не приложит анимацию (наш экспорт
# писал -1). Ped и кисти — РАЗНЫЕ пространства id (совпадают имена 'l finger01'
# с разными id), поэтому таблицы раздельные и применяются по скелету.
_PED_BONE_IDS = {
    'spine': 2, 'spine1': 3, 'neck': 4, 'head': 5,
    'bip01 l clavicle': 31, 'l upperarm': 32, 'l forearm': 33,
    'l hand': 34, 'l finger': 35, 'l finger01': 36,
    'bip01 r clavicle': 21, 'r upperarm': 22, 'r forearm': 23,
    'r hand': 24, 'r finger': 25, 'r finger01': 26,
}
_HAND_BONE_IDS = {}
for _side in ('l', 'r'):
    _HAND_BONE_IDS[f'{_side} forearm01'] = 1
    _HAND_BONE_IDS[f'{_side} hand01'] = 2
    _HAND_BONE_IDS[f'{_side} finger01'] = 3
    _HAND_BONE_IDS[f'{_side} finger02'] = 4
    for _i, _fid in enumerate(
            (5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19), start=5):
        _HAND_BONE_IDS[f'root {_side} finger{_fid:02d}'] = _i


def _find_bone(arm_obj, *names):
    """Регистро-/пробел-устойчивый поиск кости (в SA имена бывают с ведущим
    пробелом: ' L Hand'). Возвращает Bone или None."""
    if arm_obj is None or arm_obj.type != 'ARMATURE':
        return None
    wanted = {n.strip().lower() for n in names}
    for b in arm_obj.data.bones:
        if b.name.strip().lower() in wanted:
            return b
    return None


def classify_handsign_armatures(context):
    """Определить в сцене (ped, left_hand, right_hand) armature по сигнатурным
    костям: кисти несут ' L Hand01'/' R Hand01', скелет игрока — ' L Hand' и
    ' R Hand' (без 01). Любой из трёх может быть None."""
    ped = lhand = rhand = None
    for o in context.scene.objects:
        if o.type != 'ARMATURE':
            continue
        if _find_bone(o, 'L Hand01'):
            lhand = o
        elif _find_bone(o, 'R Hand01'):
            rhand = o
        elif _find_bone(o, 'L Hand') and _find_bone(o, 'R Hand'):
            ped = o
    return ped, lhand, rhand


class GTATOOLS_OT_handsign_attach(bpy.types.Operator):
    """Прицепить кисти (shandl/shandr) к скелету игрока НА УРОВНЕ КОСТЕЙ
    (совет ligabesar): кость предплечья кисти ' L ForeArm01' следует за
    ' L ForeArm' игрока, а ' L Hand01' — за ' L Hand' (и то же для R), через
    Copy Transforms. Кисть остаётся ОТДЕЛЬНОЙ armature; связываются только
    соответствующие кости → авто-позиция и ориентация без ручного
    выравнивания. Пальцы (дети ' L Hand01') не связаны — их анимируешь сам."""
    bl_idname = "gtatools.handsign_attach"
    bl_label = "INU: Прицепить кисти к скелету"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ped, lhand, rhand = classify_handsign_armatures(context)
        if ped is None:
            self.report({'ERROR'},
                        T("Не найден скелет игрока (кости ' L Hand'/' R Hand')"))
            return {'CANCELLED'}
        if lhand is None and rhand is None:
            self.report({'ERROR'},
                        T("Не найдены кисти (shandl/shandr с ' L Hand01'/' R Hand01')"))
            return {'CANCELLED'}
        n = 0
        for hand_obj, pairs in ((lhand, _PAIRS_L), (rhand, _PAIRS_R)):
            if hand_obj is not None and self._attach(hand_obj, ped, pairs):
                n += 1
        self.report({'INFO'}, T("Прицеплено кистей: {0}").format(n))
        return {'FINISHED'} if n else {'CANCELLED'}

    def _attach(self, hand_obj, ped, pairs):
        # На каждую пару (кость кисти → кость игрока) вешаем Copy Transforms:
        # кость кисти точно повторяет кость игрока (позиция + ориентация),
        # без ручного выравнивания и пивот-сдвига. Пальцы не трогаем.
        linked = 0
        for hand_bn, ped_bn in pairs:
            hb = _find_bone(hand_obj, hand_bn)
            pb = _find_bone(ped, ped_bn)
            if hb is None or pb is None:
                continue
            pose_bone = hand_obj.pose.bones.get(hb.name)
            if pose_bone is None:
                continue
            for c in list(pose_bone.constraints):
                if c.name.startswith(_CON_PREFIX):
                    pose_bone.constraints.remove(c)
            con = pose_bone.constraints.new('COPY_TRANSFORMS')
            con.name = _CON_PREFIX
            con.target = ped
            con.subtarget = pb.name
            linked += 1
        return linked > 0


class GTATOOLS_OT_handsign_detach(bpy.types.Operator):
    """Отцепить кисти — снять все привязки Handsign (Child Of), кисти снова
    свободны. Ничего не удаляет, только констрейнты."""
    bl_idname = "gtatools.handsign_detach"
    bl_label = "INU: Отцепить кисти"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        n = 0
        for o in context.scene.objects:
            if o.type != 'ARMATURE':
                continue
            # объектные констрейнты (старый подход) — на всякий случай чистим
            for c in list(o.constraints):
                if c.name.startswith(_CON_PREFIX):
                    o.constraints.remove(c)
                    n += 1
            # костные констрейнты (текущий подход)
            for pb in o.pose.bones:
                for c in list(pb.constraints):
                    if c.name.startswith(_CON_PREFIX):
                        pb.constraints.remove(c)
                        n += 1
        self.report({'INFO'}, T("Снято привязок: {0}").format(n))
        return {'FINISHED'}


class GTATOOLS_OT_handsign_export(bpy.types.Operator):
    """Экспорт жеста в ОДИН заход: берёт активную Action каждого из трёх
    скелетов (рука→gsignN, левые пальцы→lhgsignN, правые→rhgsignN), строит
    блоки и вливает их в ghands.ifp одним merge — совпавшие по имени блоки
    заменяются, остальные (вся ваниль) остаются байт-в-байт. Имя Action =
    имя блока в IFP, поэтому назови Actions правильно (gsign6/lhgsign6/…)."""
    bl_idname = "gtatools.handsign_export"
    bl_label = "INU: Экспорт жеста в ghands.ifp"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ifp", options={'HIDDEN'})
    ifp_format: EnumProperty(
        name=T("Формат"),
        description=T(
            "ANP3 — родной формат GTA SA (int16, как ванильный ghands.ifp; "
            "читается игрой И сторонними тулзами вроде GTA Anim Manager). "
            "ANPK / ANP2 — chunked float32 (III/VC, тоже читается SA)"),
        items=[
            ('ANP3', "ANP3 (SA compressed)",
             T("Родной SA — как ванильный ghands.ifp")),
            ('ANPK', "ANPK / ANP2 (III, VC, SA)",
             T("Chunked float32 — III, VC, читается и в SA")),
        ],
        default='ANP3',
    )
    decimate: BoolProperty(
        name=T("Прорежать ключи"),
        description=T(
            "Удалять keyframe'ы на линейной интерполяции между соседями. "
            "Уменьшает размер без потери качества — первый и последний ключ "
            "каждой кости сохраняются всегда"),
        default=False,
    )
    decimate_tol_rot: FloatProperty(
        name=T("Допуск поворота"), default=1e-3,
        min=0.0, soft_min=1e-4, soft_max=1e-1, precision=5)
    decimate_tol_trans: FloatProperty(
        name=T("Допуск позиции"), default=1e-3,
        min=0.0, soft_min=1e-4, soft_max=1e-1, precision=5)

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "ghands.ifp"
        # ANP3 по умолчанию для SA (родной формат ghands, читается GTA Anim
        # Manager); для III/VC — универсальный ANPK.
        from ..core import game_versions as gv
        self.ifp_format = ('ANP3' if gv.game_of_scene(context.scene) == 'SA'
                           else 'ANPK')
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "ifp_format")
        layout.prop(self, "decimate")
        if self.decimate:
            box = layout.box()
            box.prop(self, "decimate_tol_rot")
            box.prop(self, "decimate_tol_trans")

    def execute(self, context):
        from .ifp_export import build_ifp_from_actions
        from ..core.ifp import merge_ifp

        ped, lhand, rhand = classify_handsign_armatures(context)
        blocks, names, warns = [], [], []
        seen = set()
        for arm in (ped, lhand, rhand):
            if arm is None:
                continue
            act = (arm.animation_data.action
                   if arm.animation_data else None)
            if act is None:
                continue
            ifp = build_ifp_from_actions(
                actions=[act], armature=arm, package_name='ghands',
                decimate=self.decimate,
                decimate_tol_rot=self.decimate_tol_rot,
                decimate_tol_trans=self.decimate_tol_trans)
            for a in ifp.animations:
                if a.name in seen:
                    continue  # тот же блок активен на нескольких скелетах — дубль
                seen.add(a.name)
                # Таблицу bone_id выбираем по ИМЕНИ анимации, а НЕ по скелету:
                # lhgsign/rhgsign → кисти, остальное (gsign…) → скелет игрока.
                # Иначе gsign-экшен, активный на кисти, брал бы hand-id и почти
                # все кости уходили в -1 (а Finger01 случайно совпадал в =3).
                tbl = (_HAND_BONE_IDS
                       if a.name.lower().startswith(('lhg', 'rhg'))
                       else _PED_BONE_IDS)
                # Бэкфилл каноничных bone_id по имени кости — иначе в ANP3
                # остаётся -1 и игра не приложит анимацию к костям.
                for b in a.bones:
                    _bid = tbl.get(b.name.strip().lower())
                    if _bid is not None:
                        b.bone_id = _bid
                # Предупреждаем ТОЛЬКО о реально нераспознанных костях (нет в
                # стандарте ghands → id не проставился), а не о «нет в скелете».
                unresolved = [b.name for b in a.bones if b.bone_id < 0]
                if unresolved:
                    warns.append(f"{a.name}: {', '.join(unresolved[:3])}")
                blocks.append(a)
                names.append(a.name)
        if not blocks:
            self.report(
                {'ERROR'},
                T("Нет активных анимаций (назначь Action на ped/shandl/shandr)"))
            return {'CANCELLED'}
        # ANP3 читается только в SA — вне SA молча уходим на ANPK.
        from ..core import game_versions as gv
        fmt = self.ifp_format
        if fmt == 'ANP3' and gv.game_of_scene(context.scene) != 'SA':
            fmt = 'ANPK'
        try:
            replaced, added = merge_ifp(self.filepath, blocks,
                                        package_name=None, format=fmt)
        except Exception as e:
            self.report({'ERROR'}, f"IFP merge: {e}")
            return {'CANCELLED'}
        if warns:
            self.report({'WARNING'},
                        T("Неизвестные кости — {0}").format('; '.join(warns)))
        self.report(
            {'INFO'},
            T("ghands.ifp: заменено {0}, добавлено {1} · {2} ({3})").format(
                replaced, added, ', '.join(names), fmt))
        return {'FINISHED'}
