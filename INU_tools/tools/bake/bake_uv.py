# INU_tools.tools.bake.bake_uv — вспомогательный слой подсистемы запекания.
#
# Две независимые утилиты для LightMap-режимов:
#   * ensure_lightmap_uv — создать/переиспользовать непересекающийся
#     lightmap-UV-канал (для режимов «отдельная текстура + 2 UV» и как
#     чистая цель запекания без наложений исходной развёртки);
#   * sample_image_uv / sample_image_uv_batch — билинейный сэмпл картинки
#     по UV (для режима «в vertex prelight»: цвет каждого лупа берётся из
#     запечённого lightmap).
#
# Зависит только от numpy/bpy — верхних слоёв не знает.
#
# ВАЖНО: НЕ добавлять `from __future__ import annotations`.

import math

import numpy as np
import bpy


LIGHTMAP_UV_NAME = 'LightMap'

# Blender ограничивает меш 8 UV-слоями (MAX_MTFACE) — uv_layers.new()
# на лимите возвращает None, это надо обрабатывать, а не ронять оператор.
_UV_LAYER_CAP = 8


def ensure_lightmap_uv(obj, name=LIGHTMAP_UV_NAME, margin=0.02,
                       angle_limit=66.0):
    """Получить-или-создать UV-канал `name` объекта с НЕПЕРЕСЕКАЮЩЕЙСЯ
    развёрткой. Если канал уже существует — переиспользуем как есть (не
    пере-разворачиваем: повторный lightmap_pack сдвинул бы острова и
    рассинхронизировал ранее запечённый lightmap с развёрткой).

    Новый канал разворачиваем `bpy.ops.uv.lightmap_pack` (раскладывает все
    грани без наложений), при провале — `smart_project`. КРИТИЧНО: перед
    входом в EDIT изолируем выделение до одного `obj` — mode_set в 2.8+
    входит в мульти-объектный едит, и unwrap-операторы перепаковали бы
    активные UV ВСЕХ выделенных мешей (тихая порча чужих развёрток).
    Выделение/активный объект/режим восстанавливаются.

    Возвращает имя канала или None при неудаче (без исключений).
    """
    me = getattr(obj, 'data', None)
    uvs = getattr(me, 'uv_layers', None)
    if me is None or uvs is None:
        return None

    existing = uvs.get(name)
    if existing is not None:
        return name                      # уже развёрнут — переиспользуем

    view = bpy.context.view_layer
    prev_obj = view.objects.active
    prev_mode = getattr(obj, 'mode', 'OBJECT')
    prev_sel = [(o, o.select_get()) for o in view.objects]
    prev_active_name = uvs.active.name if uvs.active else None
    ok = False
    try:
        uv = uvs.new(name=name)
        if uv is None:                   # лимит 8 UV-слоёв — new() даёт None
            return None
        # Операторы разворачивают АКТИВНЫЙ UV — временно целевой активный.
        uvs.active = uv

        # Изоляция: только obj выделен и активен (см. докстринг).
        for o in view.objects:
            try:
                o.select_set(o is obj)
            except Exception:
                pass
        view.objects.active = obj
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # Первый сработавший unwrap побеждает.
        for op, kwargs in (
                (bpy.ops.uv.lightmap_pack,
                 dict(PREF_CONTEXT='ALL_FACES',
                      PREF_MARGIN_DIV=max(margin, 1e-4) * 1000.0)),
                (bpy.ops.uv.smart_project,
                 dict(angle_limit=math.radians(angle_limit),
                      island_margin=margin)),
        ):
            try:
                op(**kwargs)
                ok = True
                break
            except Exception:
                continue
    except Exception:
        ok = False
    finally:
        try:
            if obj.mode != prev_mode:
                bpy.ops.object.mode_set(mode=prev_mode)
        except Exception:
            pass
        # Вернуть исходный активный UV (рендер-UV пользователя не трогаем).
        try:
            if prev_active_name and uvs.get(prev_active_name):
                uvs.active = uvs.get(prev_active_name)
        except Exception:
            pass
        # Вернуть исходное выделение и активный объект.
        for o, sel in prev_sel:
            try:
                o.select_set(sel)
            except Exception:
                pass
        try:
            if prev_obj is not None:
                view.objects.active = prev_obj
        except Exception:
            pass
        # Неудачный unwrap — убрать пустой канал, чтобы повторный вызов
        # не «переиспользовал» неразвёрнутый слой.
        if not ok:
            try:
                lay = uvs.get(name)
                if lay is not None:
                    uvs.remove(lay)
            except Exception:
                pass
    return name if ok else None


def sample_image_uv(arr, u, v):
    """Билинейный сэмпл `arr` (H,W,C float32 из read_image_to_numpy) в точке
    UV (u,v). Порядок пикселей Blender — снизу-вверх, поэтому v отображается
    в строку напрямую (row = v*(H-1), без flip). UV зажимается в [0,1]
    (clamp/extend по краям — как GL_CLAMP). Возвращает вектор из C float.

    Тонкая обёртка над sample_image_uv_batch (одна реализация математики)."""
    return sample_image_uv_batch(arr, np.array([[u, v]], np.float32))[0]


def sample_image_uv_batch(arr, uvs):
    """Векторный билинейный сэмпл: `uvs` — (N,2) float массив UV-координат,
    результат — (N,C) float. Семантика как у sample_image_uv, один
    numpy-проход (для записи в per-loop vertex colors)."""
    h, w, c = arr.shape
    uvs = np.asarray(uvs, dtype=np.float32)
    x = np.clip(uvs[:, 0], 0.0, 1.0) * (w - 1)
    y = np.clip(uvs[:, 1], 0.0, 1.0) * (h - 1)
    x0 = np.floor(x).astype(np.intp)
    y0 = np.floor(y).astype(np.intp)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    fx = (x - x0)[:, None]
    fy = (y - y0)[:, None]
    c00 = arr[y0, x0]
    c10 = arr[y0, x1]
    c01 = arr[y1, x0]
    c11 = arr[y1, x1]
    top = c00 * (1.0 - fx) + c10 * fx
    bot = c01 * (1.0 - fx) + c11 * fx
    return top * (1.0 - fy) + bot * fy
