# INU_tools.ops.weight_paint_ops — Weight Paint helpers для split-mesh'ей.
#
# GTA SA скин-меши после импорта DFF имеют split-вершины на швах (UV,
# нормали, материалы). При покраске весов один штрих ложится только на
# одну из 4 co-located вершин — получается видимый шов в игре, где
# разные углы меша на одной точке имеют разные веса.
#
# Решение: временно слить co-located вершины через bmesh remove_doubles,
# юзер красит как на цельном меше (одна вершина = один штрих), потом
# обратный swap mesh datablock'а возвращает оригинальные split-вершины
# с одинаковыми весами для всех cluster-mates.
#
# Backup живёт как orphan Mesh datablock (не Object) — в Outliner'е
# юзер видит ОДИН объект всё время, без дубликатов.

import bpy
import bmesh
from collections import defaultdict
from mathutils import Vector

from .. import T


# Tolerance для определения co-located вершин. Split-вершины после
# импорта DFF имеют ТОЧНО идентичные координаты (Blender хранит их как
# float32, копии из одного и того же значения совпадают побайтно), так
# что 1e-6 более чем достаточно. Поднимать выше — рискуем слить
# не-split соседей в одну точку.
_MERGE_DIST = 1e-6

# Округление позиций для построения position → vertex_idx словаря.
# Должно соответствовать _MERGE_DIST по точности: если merge merge'ит
# при distance < 1e-6, то 6 знаков после запятой даёт ту же group'ировку.
_POS_PRECISION = 6


def _pos_key(co: Vector) -> tuple:
    """Hashable key для группировки вершин по позиции."""
    return (round(co.x, _POS_PRECISION),
            round(co.y, _POS_PRECISION),
            round(co.z, _POS_PRECISION))


def _average_cluster_weights(obj: bpy.types.Object) -> int:
    """Усреднить веса между co-located вершинами BEFORE merge.

    Без этого bmesh.ops.remove_doubles берёт веса первой попавшейся
    вершины в кластере и теряет данные остальных. Перед merge мы
    приводим все co-located вершины к одинаковому усреднённому весу,
    чтобы merge не терял информацию.

    Returns: количество обработанных кластеров (≥2 вершин в одной точке).
    """
    mesh = obj.data
    if not mesh.vertices:
        return 0

    # Кластеризация по позиции.
    clusters = defaultdict(list)
    for vi, v in enumerate(mesh.vertices):
        clusters[_pos_key(v.co)].append(vi)

    cluster_count = 0
    for key, indices in clusters.items():
        if len(indices) < 2:
            continue
        cluster_count += 1

        # Собираем все (group_index, weight) от всех вершин кластера.
        weight_sum: dict = defaultdict(float)
        weight_count: dict = defaultdict(int)
        for vi in indices:
            for vge in mesh.vertices[vi].groups:
                weight_sum[vge.group] += vge.weight
                weight_count[vge.group] += 1

        # Усреднение: weight_sum[g] / len(indices) — это «доля» группы
        # по всему кластеру. Делим именно на len(indices), а не на
        # weight_count[g], чтобы вершины БЕЗ этой группы тоже шли в
        # знаменатель (иначе одна крайняя вершина с малым весом дала бы
        # завышенное среднее).
        n = len(indices)
        averaged = {g: w / n for g, w in weight_sum.items()}

        # Применяем ко всем cluster-mate'ам.
        for g_idx, w in averaged.items():
            vg = obj.vertex_groups[g_idx]
            vg.add(indices, w, 'REPLACE')

        # Удаляем группы которых среди averaged нет — те что были только
        # у части cluster-mate'ов с почти-нулём, чтобы оставить чистоту.
        # Skip: оставить, ничего страшного что лишний zero-вес лежит.

    return cluster_count


def _read_weight_map(obj: bpy.types.Object) -> dict:
    """Считать карту pos_key → {group_idx: weight} из текущего obj.data.

    Используется на «Apply»: считываем веса с merged-меша, потом swap'аем
    mesh datablock обратно на backup и распространяем эти веса на все
    cluster-mate'ы по совпадению позиций.
    """
    out: dict = {}
    for v in obj.data.vertices:
        key = _pos_key(v.co)
        if key in out:
            # Сошедшаяся со-located вершина (не должно быть после merge,
            # но если есть — берём первую).
            continue
        out[key] = {vge.group: vge.weight for vge in v.groups}
    return out


def _apply_weights_to_backup(obj: bpy.types.Object,
                              weight_map: dict) -> int:
    """Применить считанные веса к backup-mesh (уже swap'нутому в obj.data).

    Каждая вершина backup'а ищется по позиции в weight_map. Все
    cluster-mate'ы получают одинаковые веса (то что юзер покрасил на
    merged-вершине). Returns: количество updated вершин.
    """
    # Сначала чистим ВСЕ существующие веса (иначе старые остатки могут
    # смешаться с новыми из weight_map). Идём по группам, очищаем все
    # вертексы.
    n_verts = len(obj.data.vertices)
    all_indices = list(range(n_verts))
    for vg in obj.vertex_groups:
        vg.remove(all_indices)

    # Применяем веса по позиции.
    updated = 0
    for vi, v in enumerate(obj.data.vertices):
        key = _pos_key(v.co)
        weights = weight_map.get(key)
        if weights is None:
            continue
        for g_idx, w in weights.items():
            if w <= 0.0:
                continue
            obj.vertex_groups[g_idx].add([vi], w, 'REPLACE')
        updated += 1
    return updated


class GTATOOLS_OT_weight_merge_start(bpy.types.Operator):
    """Временно слить co-located вершины для редактирования весов.

    Backup'ит mesh datablock, усредняет веса между cluster-mate'ами,
    делает bmesh remove_doubles. В Outliner'е остаётся один объект.
    """
    bl_idname = "gtatools.weight_merge_start"
    bl_label = "INU: Merge for weight editing"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None
                and obj.type == 'MESH'
                and obj.mode == 'WEIGHT_PAINT'
                and '_inu_weight_edit_backup' not in obj)

    def execute(self, context):
        obj = context.active_object

        # Backup-mesh уходит в bpy.data.meshes но НЕ линкуется в сцену.
        # Outliner показывает его в Data → Meshes → orphan-data только
        # если развернёшь, но не как отдельный объект в Scene Collection.
        backup_mesh = obj.data.copy()
        backup_mesh.name = f"{obj.data.name}__inu_we_backup"
        obj['_inu_weight_edit_backup'] = backup_mesh.name

        # Усредняем веса cluster-mate'ов на ОРИГИНАЛЕ (до merge), чтобы
        # bmesh remove_doubles не выбрасывал данные а сохранял согласие.
        # После merge каждый кластер представлен одной вершиной с
        # consistent весом.
        prev_mode = obj.mode
        if prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        cluster_count = _average_cluster_weights(obj)

        # Merge by distance — bmesh ops.
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=_MERGE_DIST)
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()

        # Возвращаем в Weight Paint автоматически.
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

        removed = len(backup_mesh.vertices) - len(obj.data.vertices)
        cluster_word = T("cluster'ов,")
        msg = "{prefix} {n} {word} -{r} {suffix}".format(
            prefix=T('Merged для weight paint:'),
            n=cluster_count,
            word=cluster_word,
            r=removed,
            suffix=T('вершин. Не меняй геометрию!'),
        )
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_weight_merge_apply(bpy.types.Operator):
    """Применить покрашенные веса обратно на оригинальную split-геометрию.

    Считывает веса с merged-меша, swap'ает mesh datablock обратно на
    backup (со split-вершинами), распределяет веса по cluster-mate'ам
    через position-match.
    """
    bl_idname = "gtatools.weight_merge_apply"
    bl_label = "INU: Apply weight edits"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None
                and obj.type == 'MESH'
                and '_inu_weight_edit_backup' in obj)

    def execute(self, context):
        obj = context.active_object
        backup_name = obj['_inu_weight_edit_backup']
        backup_mesh = bpy.data.meshes.get(backup_name)
        if backup_mesh is None:
            # Backup пропал — типичный сценарий: юзер нажал Undo,
            # Blender откатил создание datablock'а, а IDProperty-тэг
            # уцелел в текущем state'е. obj.data СЕЙЧАС уже restored
            # к pre-merge состоянию (Undo восстановил), нужно только
            # снять stale-тэг.
            del obj['_inu_weight_edit_backup']
            if obj.mode != 'WEIGHT_PAINT':
                try:
                    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
                except RuntimeError:
                    pass
            self.report({'WARNING'},
                        (T("Backup '{n}' исчез (вероятно Undo). ").format(n=backup_name)
                         + T("Тэг очищен, текущая геометрия принята как есть. ")
                         + T("Изменения весов сделанные после Undo сохранены.")))
            return {'FINISHED'}

        # Считываем веса с TEKУЩЕГО (merged) меша.
        prev_mode = obj.mode
        if prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        weight_map = _read_weight_map(obj)
        merged_mesh = obj.data

        # Гард: если merged_mesh и backup_mesh — один и тот же
        # datablock (Undo сошёл их вместе), не пытаемся swap+remove,
        # просто чистим тэг.
        if merged_mesh is backup_mesh:
            del obj['_inu_weight_edit_backup']
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            self.report({'WARNING'},
                        T("Backup идентичен текущему mesh'у (Undo схлопнул). "
                          "Тэг очищен."))
            return {'FINISHED'}

        # Swap datablock на backup.
        obj.data = backup_mesh

        # Распространяем веса по cluster-mate'ам.
        updated = _apply_weights_to_backup(obj, weight_map)

        # Cleanup: удаляем merged-датаблок и тэг.
        bpy.data.meshes.remove(merged_mesh)
        del obj['_inu_weight_edit_backup']

        # Восстанавливаем Weight Paint mode.
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

        msg = "{prefix} {n} {suffix}".format(
            prefix=T('Веса применены к'),
            n=updated,
            suffix=T('вершинам, split-геометрия восстановлена'),
        )
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_weight_merge_cancel(bpy.types.Operator):
    """Откатить merge без сохранения покрашенных весов.

    Swap'ает mesh datablock обратно на backup, удаляет merged-копию.
    Веса покрашенные в merged-режиме теряются.
    """
    bl_idname = "gtatools.weight_merge_cancel"
    bl_label = "INU: Cancel weight merge"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None
                and obj.type == 'MESH'
                and '_inu_weight_edit_backup' in obj)

    def execute(self, context):
        obj = context.active_object
        backup_name = obj['_inu_weight_edit_backup']
        backup_mesh = bpy.data.meshes.get(backup_name)
        if backup_mesh is None:
            # Тот же recovery-path что и в Apply: backup исчез
            # (вероятно Undo), просто чистим stale-тэг.
            del obj['_inu_weight_edit_backup']
            try:
                bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            except RuntimeError:
                pass
            self.report({'WARNING'},
                        (T("Backup '{n}' исчез (вероятно Undo). ").format(n=backup_name)
                         + T("Тэг очищен, текущая геометрия принята как есть.")))
            return {'FINISHED'}

        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        merged_mesh = obj.data
        # Same-datablock guard как в Apply.
        if merged_mesh is backup_mesh:
            del obj['_inu_weight_edit_backup']
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            self.report({'WARNING'},
                        T("Backup идентичен текущему mesh'у. Тэг очищен."))
            return {'FINISHED'}

        obj.data = backup_mesh
        bpy.data.meshes.remove(merged_mesh)
        del obj['_inu_weight_edit_backup']

        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

        self.report({'INFO'}, T("Merge откатан, веса восстановлены"))
        return {'FINISHED'}


CLASSES = (
    GTATOOLS_OT_weight_merge_start,
    GTATOOLS_OT_weight_merge_apply,
    GTATOOLS_OT_weight_merge_cancel,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
