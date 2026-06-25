# INU_tools.tools.bake.bake_composite — Слой 3 подсистемы запекания.
#
# Композитор «N карт → одна текстура». ЧИСТЫЙ numpy, БЕЗ bpy и без
# относительных импортов — поэтому юнит-тестируется headless (и его
# инвариант «нет bpy» не нарушается: на вход подаются простые LayerSpec,
# не PropertyGroup — извлечение делает оператор, слой 4).
#
# Порядок пикселей — нативный Blender (снизу вверх, RGBA float). Композит
# идёт в linear, на выходе RGB кодируется в sRGB (карты GTA SA — sRGB
# 8-bit), alpha берётся из базового слоя без изменений (cutout/листва).

from dataclasses import dataclass

import numpy as np


# ── HSV-хелперы (векторные, для Hue/Saturation/Color/Value) ──────────
# numpy не имеет встроенного RGB↔HSV; повторяем точные формулы Blender
# (rgb_to_hsv / hsv_to_rgb из math_color.c), чтобы HSV-режимы совпадали
# с живым нодовым превью. Вход/выход (… ,3) float в [0,1].

def _rgb_to_hsv(rgb):
    """(… ,3) RGB → (h, s, v), каждый (…) в [0,1]. Серый (d==0) → h=0."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    d = mx - mn
    d_safe = np.where(d == 0.0, 1.0, d)
    # Порядок where обратный (b→g→r): при равенстве максимумов «победитель» —
    # r, как в if/elif Blender (последний where перетирает предыдущие).
    h = np.zeros_like(mx)
    h = np.where(mx == b, 4.0 + (r - g) / d_safe, h)
    h = np.where(mx == g, 2.0 + (b - r) / d_safe, h)
    h = np.where(mx == r, (g - b) / d_safe, h)
    h = (h / 6.0) % 1.0
    h = np.where(d == 0.0, 0.0, h)
    s = np.where(mx == 0.0, 0.0, d / np.where(mx == 0.0, 1.0, mx))
    return h, s, mx


def _hsv_to_rgb(h, s, v):
    """(h, s, v) каждый (…) → (… ,3) RGB float."""
    h6 = (h % 1.0) * 6.0
    i = np.floor(h6).astype(np.int64)
    f = h6 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
                  [v, q, p, p, t, v])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
                  [t, v, v, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
                  [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1)


# ── Blend-функции ────────────────────────────────────────────────────
# Каждая: (acc_rgb=низ, top_rgb=верх) -> blended_rgb, всё (h,w,3).
# Это значение режима при полной непрозрачности (fac=1) — смешивание по
# opacity делает вызывающий (composite_layers), ровно как Blender: outcol =
# facm*col1 + fac*<blend>. Формулы — 1:1 с ramp_blend() ядра Blender, поэтому
# numpy-«сведение» совпадает с живым превью на нодах ShaderNodeMix.

def _b_normal(a, b):   return b
def _b_darken(a, b):   return np.minimum(a, b)
def _b_multiply(a, b): return a * b
def _b_lighten(a, b):  return np.maximum(a, b)
def _b_screen(a, b):   return 1.0 - (1.0 - a) * (1.0 - b)
def _b_add(a, b):      return np.clip(a + b, 0.0, 1.0)
def _b_subtract(a, b): return np.clip(a - b, 0.0, 1.0)
def _b_difference(a, b): return np.abs(a - b)


def _b_burn(a, b):     # Color Burn: 1 − (1−a)/b
    out = 1.0 - (1.0 - a) / np.where(b <= 0.0, 1.0, b)
    return np.clip(np.where(b <= 0.0, 0.0, out), 0.0, 1.0)


def _b_dodge(a, b):    # Color Dodge: a / (1−b)
    denom = 1.0 - b
    out = a / np.where(denom <= 0.0, 1.0, denom)
    out = np.where(denom <= 0.0, 1.0, out)   # 1−b ≤ 0 → белый
    out = np.where(a <= 0.0, 0.0, out)        # a == 0 → чёрный (приоритет)
    return np.clip(out, 0.0, 1.0)


def _b_overlay(a, b):
    return np.where(a < 0.5, 2.0 * a * b,
                    1.0 - 2.0 * (1.0 - a) * (1.0 - b))


def _b_soft_light(a, b):
    scr = 1.0 - (1.0 - b) * (1.0 - a)
    return np.clip((1.0 - a) * b * a + a * scr, 0.0, 1.0)


def _b_linear_light(a, b):
    return np.clip(a + 2.0 * b - 1.0, 0.0, 1.0)


def _b_divide(a, b):   # где b==0 — слой не влияет (остаётся низ), как в Blender
    out = a / np.where(b == 0.0, 1.0, b)
    return np.clip(np.where(b == 0.0, a, out), 0.0, 1.0)


def _b_hue(a, b):          # тон ← верх; насыщ./яркость ← низ
    _ha, sa, va = _rgb_to_hsv(a)
    hb, sb, _vb = _rgb_to_hsv(b)
    out = _hsv_to_rgb(hb, sa, va)
    return np.where((sb == 0.0)[..., None], a, out)


def _b_saturation(a, b):   # насыщенность ← верх; тон/яркость ← низ
    ha, sa, va = _rgb_to_hsv(a)
    _hb, sb, _vb = _rgb_to_hsv(b)
    out = _hsv_to_rgb(ha, sb, va)
    return np.where((sa == 0.0)[..., None], a, out)


def _b_value(a, b):        # яркость ← верх; тон/насыщ. ← низ
    ha, sa, _va = _rgb_to_hsv(a)
    _hb, _sb, vb = _rgb_to_hsv(b)
    return _hsv_to_rgb(ha, sa, vb)


def _b_color(a, b):        # тон+насыщ. ← верх; яркость ← низ
    _ha, _sa, va = _rgb_to_hsv(a)
    hb, sb, _vb = _rgb_to_hsv(b)
    out = _hsv_to_rgb(hb, sb, va)
    return np.where((sb == 0.0)[..., None], a, out)


# ── Реестр режимов — ЕДИНЫЙ источник правды ──────────────────────────
# (id, blend_type ноды ShaderNodeMix, английская метка). Порядок = порядок
# в выпадашке. id NORMAL/MULTIPLY/ADD/SCREEN/OVERLAY сохранены ради старых
# .blend. Набор и порядок — как в Mix-узле Blender (версионно-безопасный
# поднабор без EXCLUSION: его нет в ShaderNodeMixRGB на ≤3.3).
#   bake_composite (этот файл) — формулы (_BLEND);
#   bake_nodes      — blend_type ноды (BLEND_NODE_TYPE);
#   scene_settings  — EnumProperty-метки (BLEND_LABEL).
BLEND_DEFS = (
    ('NORMAL',       'MIX',          'Normal',       _b_normal),
    ('DARKEN',       'DARKEN',       'Darken',       _b_darken),
    ('MULTIPLY',     'MULTIPLY',     'Multiply',     _b_multiply),
    ('BURN',         'BURN',         'Color Burn',   _b_burn),
    ('LIGHTEN',      'LIGHTEN',      'Lighten',      _b_lighten),
    ('SCREEN',       'SCREEN',       'Screen',       _b_screen),
    ('DODGE',        'DODGE',        'Color Dodge',  _b_dodge),
    ('ADD',          'ADD',          'Add',          _b_add),
    ('OVERLAY',      'OVERLAY',      'Overlay',      _b_overlay),
    ('SOFT_LIGHT',   'SOFT_LIGHT',   'Soft Light',   _b_soft_light),
    ('LINEAR_LIGHT', 'LINEAR_LIGHT', 'Linear Light', _b_linear_light),
    ('DIFFERENCE',   'DIFFERENCE',   'Difference',   _b_difference),
    ('SUBTRACT',     'SUBTRACT',     'Subtract',     _b_subtract),
    ('DIVIDE',       'DIVIDE',       'Divide',       _b_divide),
    ('HUE',          'HUE',          'Hue',          _b_hue),
    ('SATURATION',   'SATURATION',   'Saturation',   _b_saturation),
    ('COLOR',        'COLOR',        'Color',        _b_color),
    ('VALUE',        'VALUE',        'Value',        _b_value),
)

BLEND_MODES = tuple(d[0] for d in BLEND_DEFS)
BLEND_NODE_TYPE = {d[0]: d[1] for d in BLEND_DEFS}
BLEND_LABEL = {d[0]: d[2] for d in BLEND_DEFS}
_BLEND = {d[0]: d[3] for d in BLEND_DEFS}


@dataclass
class LayerSpec:
    """Плоское (bpy-free) описание слоя для композитора. Оператор
    извлекает его из INUBakeLayer (PropertyGroup) перед вызовом."""
    map_id: str
    enabled: bool = True
    blend_mode: str = 'NORMAL'
    opacity: float = 1.0
    contrast: float = 1.0          # FUTURE (1.0 = identity)
    gamma: float = 1.0             # FUTURE (1.0 = identity)
    influence_target: str = ''     # FUTURE (masking by another map)
    influence_amount: float = 1.0


def linear_to_srgb(c):
    """scene-linear → sRGB (C1). Вход/выход (… ,3) float в [0,1]."""
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308,
                    c * 12.92,
                    1.055 * np.power(c, 1.0 / 2.4) - 0.055)


def apply_contrast_gamma(rgb, contrast=1.0, gamma=1.0):
    """Per-layer контраст/гамма. При (1.0, 1.0) — тождество (FUTURE-хук:
    движок уже зовёт это каждый прогон, включение = только UI)."""
    if contrast == 1.0 and gamma == 1.0:
        return rgb
    out = rgb
    if contrast != 1.0:
        out = np.clip((out - 0.5) * contrast + 0.5, 0.0, 1.0)
    if gamma != 1.0 and gamma > 0.0:
        out = np.power(np.clip(out, 0.0, 1.0), 1.0 / gamma)
    return out


def _resample_to(arr, w, h):
    """Nearest-resample (h0,w0,C) → (h,w,C). Подстраховка на случай карт
    разного размера (C-mixed-resolution); в норме все слои печём в одно
    разрешение и это no-op."""
    ah, aw = arr.shape[0], arr.shape[1]
    if aw == w and ah == h:
        return arr
    yi = np.linspace(0, ah - 1, h).astype(np.int64)
    xi = np.linspace(0, aw - 1, w).astype(np.int64)
    return arr[yi][:, xi]


def composite_layers(layer_pixels, layers, w, h, *, srgb=True):
    """Сложить включённые слои снизу вверх в одну текстуру.

    layer_pixels : dict {map_id: (h,w,4) float32} — запечённые карты
                   (scene-linear).
    layers       : упорядоченный list[LayerSpec]; index 0 = низ = база.
    w, h         : целевое разрешение.
    srgb         : кодировать ли RGB результата в sRGB (для записи в
                   8-bit текстуру GTA SA — да; для отладки blend-математики
                   удобно False).

    Возвращает (h,w,4) float32. Alpha = alpha базового слоя (cutout SA).
    Выключенные слои и слои без запечённых пикселей пропускаются —
    отсюда «скомбинировать любой поднабор».
    """
    enabled = [L for L in layers if L.enabled and L.map_id in layer_pixels]
    # Список сверху вниз (как в фотошопе): база = НИЖНИЙ слой → разворот.
    enabled = list(reversed(enabled))
    if not enabled:
        return np.zeros((h, w, 4), dtype=np.float32)

    def _desat(rgb):
        # Обесцветить в серое по яркости (Rec.709, scene-linear) — убирает
        # синий оттенок Normal Map при объединении, оставляя только рельеф.
        lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1]
               + 0.0722 * rgb[..., 2])
        return np.repeat(lum[..., None], 3, axis=-1)

    base = _resample_to(layer_pixels[enabled[0].map_id], w, h)
    acc = base[..., :3].astype(np.float32)
    if getattr(enabled[0], 'desaturate', False):
        acc = _desat(acc)
    acc = apply_contrast_gamma(acc, enabled[0].contrast, enabled[0].gamma)
    base_alpha = base[..., 3].astype(np.float32)

    for L in enabled[1:]:
        top = _resample_to(layer_pixels[L.map_id], w, h)[..., :3].astype(np.float32)
        if getattr(L, 'desaturate', False):
            top = _desat(top)
        top = apply_contrast_gamma(top, L.contrast, L.gamma)
        blended = _BLEND.get(L.blend_mode, _BLEND['NORMAL'])(acc, top)
        # FUTURE: mask = mask_lookup[L.influence_target]; сейчас 1.0
        fac = float(L.opacity) * float(L.influence_amount) * 1.0
        acc = acc * (1.0 - fac) + blended * fac

    acc = np.clip(acc, 0.0, 1.0)
    if srgb:
        acc = linear_to_srgb(acc)

    out = np.empty((h, w, 4), dtype=np.float32)
    out[..., :3] = acc
    out[..., 3] = np.clip(base_alpha, 0.0, 1.0)
    return out
