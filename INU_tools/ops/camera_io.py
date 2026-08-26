# INU_tools.ops.camera_io — GTA cutscene camera (.dat) import/export.
#
# Реализует то же, что MaxScript `SetCamera.ms` (by yelmi): текстовый
# `.dat` с траекторией катсцен-камеры. Файл состоит из 4 блоков, каждый
# закрывается строкой «;», в самом конце ещё одна «;»:
#
#   <N>,                              ← кол-во ключей FOV
#   <t>,<fov>,<fov>,<fov>,            ← t в секундах; fov трижды (in/val/out)
#   …
#   ;
#   <N>,                              ← Roll angle (крен) — обычно 2 нуля
#   <t>,<roll>,<roll>,<roll>,
#   ;
#   <N>,                             ← позиция камеры
#   <t>,<x>,<y>,<z>,<x>,<y>,<z>,<x>,<y>,<z>,   ← xyz трижды (тангенсы)
#   …
#   ;
#   <N>,                             ← позиция цели (target)
#   <t>,<x>,<y>,<z>, … (×3)
#   ;
#   ;
#
# После текста файл добивается нулями до кратности 2048 (движок читает
# блоками). Координаты — метры, ось Z вверх, как в Blender → 1:1, без
# осевых перестановок. Единственная поправка: Z-offset −1.0 при импорте
# и +1.0 при экспорте (обход Z-бага движка, как в оригинальном скрипте).
#
# В Blender камера-с-целью моделируется как Camera + Empty («…​.Target»)
# со связью Track To. FOV пишется в data.angle при sensor_fit='VERTICAL'
# (fovType=2 у оригинала — вертикальный FOV).

import math
import os

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty

from .. import T

PAD_BLOCK = 2048
Z_OFFSET = -1.0          # прибавляется к Z при импорте; при экспорте −Z_OFFSET
TARGET_SUFFIX = ".Target"


# ── .dat parsing ────────────────────────────────────────────────

def _clean_tokens(line: str):
    """Строка `.dat` → список float-токенов.

    Отсекает всё от «;» (разделитель блоков / комментарий), режет по
    запятым, снимает хвостовой `f` у литералов вида «0.0f», выкидывает
    пустые. Возвращает список float или None, если строка пустая/только
    разделитель.
    """
    cut = line.split(';', 1)[0].strip()
    if not cut:
        return None
    out = []
    for tok in cut.split(','):
        tok = tok.strip()
        if not tok:
            continue
        if tok.endswith(('f', 'F')):
            tok = tok[:-1]
        try:
            out.append(float(tok))
        except ValueError:
            return None
    return out or None


def _read_block(records, idx):
    """Читает один блок начиная с records[idx].

    records — список уже отфильтрованных списков-токенов (без пустых).
    Первый элемент блока — счётчик (1 токен), далее ровно `count` строк
    данных. Возвращает (rows, next_idx).
    """
    if idx >= len(records):
        return [], idx
    count = int(round(records[idx][0]))
    idx += 1
    rows = []
    for _ in range(count):
        if idx >= len(records):
            break
        rows.append(records[idx])
        idx += 1
    return rows, idx


def parse_cam_dat(filepath: str):
    """Парсит `.dat` → dict с ключами fov/roll/pos/target.

    Каждый элемент — список кортежей: FOV/roll → (t, value);
    pos/target → (t, x, y, z) (берётся только первая тройка из трёх).
    Время t в секундах.
    """
    with open(filepath, 'r', errors='ignore') as fh:
        raw = fh.readlines()

    records = []
    for line in raw:
        toks = _clean_tokens(line)
        if toks is not None:
            records.append(toks)

    idx = 0
    fov_rows, idx = _read_block(records, idx)
    roll_rows, idx = _read_block(records, idx)
    pos_rows, idx = _read_block(records, idx)
    tgt_rows, idx = _read_block(records, idx)

    def _scalar(rows):
        return [(r[0], r[1]) for r in rows if len(r) >= 2]

    def _vec(rows):
        return [(r[0], r[1], r[2], r[3]) for r in rows if len(r) >= 4]

    return {
        'fov': _scalar(fov_rows),
        'roll': _scalar(roll_rows),
        'pos': _vec(pos_rows),
        'target': _vec(tgt_rows),
    }


# ── .dat writing ────────────────────────────────────────────────

def _fmt(v):
    return f"{v:.6f}"


def write_cam_dat(filepath: str, fov_keys, pos_keys, target_keys,
                  z_offset: float = Z_OFFSET):
    """Пишет `.dat`. Значения дублируются трижды (in/val/out тангенсы),
    как в оригинальном экспортёре. Z смещается на −z_offset (обратно
    импортному +z_offset). Roll-блок — заглушка из 2 нулевых ключей.
    Хвост добивается нулями до кратности 2048.
    """
    zc = -z_offset
    last_t = 0.0
    for seq in (fov_keys, pos_keys, target_keys):
        if seq:
            last_t = max(last_t, seq[-1][0])

    lines = []

    # BLOCK 1 — FOV
    if fov_keys:
        lines.append(f"{len(fov_keys)},")
        for t, fov in fov_keys:
            fov = min(max(fov, 0.1), 179.0)
            lines.append(f"{_fmt(t)},{_fmt(fov)},{_fmt(fov)},{_fmt(fov)},")
    else:
        lines.append("2,")
        lines.append("0.0f,45.0,45.0,45.0,")
        lines.append(f"{_fmt(last_t)},45.0,45.0,45.0,")
    lines.append(";")

    # BLOCK 2 — Roll angle (заглушка, как в оригинале)
    lines.append("2,")
    lines.append("0.0f,0.0,0.0,0.0,")
    lines.append(f"{_fmt(last_t)},0.0,0.0,0.0,")
    lines.append(";")

    # BLOCK 3 — Camera position
    lines.append(f"{len(pos_keys)},")
    for t, x, y, z in pos_keys:
        z = z + zc
        trip = f"{_fmt(x)},{_fmt(y)},{_fmt(z)},"
        lines.append(f"{_fmt(t)},{trip}{trip}{trip}")
    lines.append(";")

    # BLOCK 4 — Target position
    lines.append(f"{len(target_keys)},")
    for t, x, y, z in target_keys:
        z = z + zc
        trip = f"{_fmt(x)},{_fmt(y)},{_fmt(z)},"
        lines.append(f"{_fmt(t)},{trip}{trip}{trip}")
    lines.append(";")
    lines.append(";")

    text = "\n".join(lines) + "\n"
    data = text.encode('ascii', errors='replace')
    pad = (PAD_BLOCK - (len(data) % PAD_BLOCK)) % PAD_BLOCK
    data += b"\x00" * pad

    with open(filepath, 'wb') as fh:
        fh.write(data)


# ── Blender import ──────────────────────────────────────────────

def import_camera_dat(filepath: str, context=None, z_offset: float = Z_OFFSET):
    """Строит Camera + Empty(target) со связью Track To и анимацией."""
    context = context or bpy.context
    scene = context.scene
    fps = scene.render.fps or 30
    data = parse_cam_dat(filepath)

    base = os.path.splitext(os.path.basename(filepath))[0]

    cam_data = bpy.data.cameras.new(base)
    cam_data.sensor_fit = 'VERTICAL'          # fovType=2 — вертикальный FOV
    cam_obj = bpy.data.objects.new(base, cam_data)
    scene.collection.objects.link(cam_obj)

    tgt = bpy.data.objects.new(base + TARGET_SUFFIX, None)
    tgt.empty_display_size = 0.5
    scene.collection.objects.link(tgt)

    con = cam_obj.constraints.new('TRACK_TO')
    con.target = tgt
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'

    def _frame(t):
        return round(t * fps)

    # Позиция камеры
    for t, x, y, z in data['pos']:
        f = _frame(t)
        cam_obj.location = (x, y, z + z_offset)
        cam_obj.keyframe_insert('location', frame=f)

    # Позиция цели
    for t, x, y, z in data['target']:
        f = _frame(t)
        tgt.location = (x, y, z + z_offset)
        tgt.keyframe_insert('location', frame=f)

    # FOV → data.angle (вертикальный). Кейфреймим 'lens' (angle его
    # пересчитывает). fov в градусах.
    for t, fov in data['fov']:
        f = _frame(t)
        cam_data.angle = math.radians(min(max(fov, 0.1), 179.0))
        cam_data.keyframe_insert('lens', frame=f)

    # Диапазон сцены под анимацию
    frames = [_frame(t) for t, *_ in data['pos']] + \
             [_frame(t) for t, *_ in data['target']]
    if frames:
        scene.frame_start = min(scene.frame_start, min(frames))
        scene.frame_end = max(scene.frame_end, max(frames))

    if context.view_layer:
        for o in context.selected_objects:
            o.select_set(False)
        cam_obj.select_set(True)
        context.view_layer.objects.active = cam_obj

    return cam_obj


# ── Blender export ──────────────────────────────────────────────

def _fcurve_frames(obj, data_path):
    """Множество кадров, на которых у obj есть ключи по data_path."""
    frames = set()
    ad = obj.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path == data_path:
                for kp in fc.keyframe_points:
                    frames.add(round(kp.co[0]))
    return frames


def _find_target(cam_obj):
    """Возвращает объект-цель камеры: цель Track To либо Empty с суффиксом."""
    for con in cam_obj.constraints:
        if con.type == 'TRACK_TO' and con.target is not None:
            return con.target
    want = cam_obj.name + TARGET_SUFFIX
    return bpy.data.objects.get(want)


def export_camera_dat(filepath: str, cam_obj, context=None,
                      z_offset: float = Z_OFFSET):
    """Экспортирует камеру Blender в `.dat`. Требует цель (Track To /
    Empty «…​.Target»), fps==30 и ≥2 ключей позиции у камеры и цели."""
    context = context or bpy.context
    scene = context.scene
    fps = scene.render.fps or 30

    tgt = _find_target(cam_obj)
    if tgt is None:
        raise ValueError(T("У камеры нет цели (Track To / Empty «.Target»)"))

    cam_frames = sorted(_fcurve_frames(cam_obj, 'location'))
    tgt_frames = sorted(_fcurve_frames(tgt, 'location'))
    fov_frames = sorted(_fcurve_frames(cam_obj.data, 'lens'))

    if len(cam_frames) < 2 or len(tgt_frames) < 2:
        raise ValueError(
            T("Нужно ≥2 ключей позиции у камеры и у цели"))

    frame_backup = scene.frame_current

    def _sample(obj, frames, kind):
        rows = []
        for f in frames:
            scene.frame_set(f)
            if kind == 'loc':
                co = obj.matrix_world.to_translation()
                rows.append((f / fps, co.x, co.y, co.z))
            else:  # fov
                rows.append((f / fps, math.degrees(obj.data.angle)))
        return rows

    pos_keys = _sample(cam_obj, cam_frames, 'loc')
    target_keys = _sample(tgt, tgt_frames, 'loc')
    fov_keys = _sample(cam_obj, fov_frames, 'fov') if fov_frames else []

    scene.frame_set(frame_backup)

    write_cam_dat(filepath, fov_keys, pos_keys, target_keys, z_offset=z_offset)


# ── Operators ───────────────────────────────────────────────────

class GTATOOLS_OT_import_camera_dat(bpy.types.Operator):
    """Импорт катсцен-камеры GTA (.dat) — FOV, позиция, цель"""
    bl_idname = "gtatools.import_camera_dat"
    bl_label = "INU: Import Camera .dat"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})
    apply_z_offset: BoolProperty(
        name=T("Z-offset −1.0"),
        description=T("Обход Z-бага движка: вычесть 1.0 из Z при импорте "
                      "(и вернуть при экспорте). Как в оригинальном SetCamera"),
        default=True,
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        zoff = Z_OFFSET if self.apply_z_offset else 0.0
        try:
            cam = import_camera_dat(self.filepath, context=context,
                                    z_offset=zoff)
            self.report({'INFO'},
                        T("Камера импортирована: ") + cam.name)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Camera .dat import: {e}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_camera_dat(bpy.types.Operator):
    """Экспорт активной камеры в катсцен-.dat GTA"""
    bl_idname = "gtatools.export_camera_dat"
    bl_label = "INU: Export Camera .dat"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filename_ext = ".dat"
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})
    apply_z_offset: BoolProperty(
        name=T("Z-offset +1.0"),
        description=T("Вернуть 1.0 к Z при экспорте (парно к импорту)"),
        default=True,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'CAMERA'

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = (context.active_object.name or "camera") + ".dat"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        cam = context.active_object
        if context.scene.render.fps != 30:
            self.report({'ERROR'},
                        T("FPS сцены должен быть 30 для катсцен-камеры"))
            return {'CANCELLED'}
        zoff = Z_OFFSET if self.apply_z_offset else 0.0
        try:
            export_camera_dat(self.filepath, cam, context=context,
                              z_offset=zoff)
            self.report({'INFO'}, T("Камера экспортирована: ") + self.filepath)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Camera .dat export: {e}")
            return {'CANCELLED'}


classes = (
    GTATOOLS_OT_import_camera_dat,
    GTATOOLS_OT_export_camera_dat,
)
