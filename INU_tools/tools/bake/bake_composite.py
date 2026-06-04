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


# Доступные режимы смешивания (id == ключ в _BLEND). Используется и для
# EnumProperty в scene_settings — единый источник правды.
BLEND_MODES = ('NORMAL', 'MULTIPLY', 'ADD', 'SCREEN', 'OVERLAY')


# Каждая функция: (acc_rgb, top_rgb) -> blended_rgb, всё (h,w,3) в [0,1].
_BLEND = {
    'NORMAL':   lambda a, b: b,
    'MULTIPLY': lambda a, b: a * b,
    'ADD':      lambda a, b: np.clip(a + b, 0.0, 1.0),
    'SCREEN':   lambda a, b: 1.0 - (1.0 - a) * (1.0 - b),
    'OVERLAY':  lambda a, b: np.where(a < 0.5, 2.0 * a * b,
                                      1.0 - 2.0 * (1.0 - a) * (1.0 - b)),
}


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
    if not enabled:
        return np.zeros((h, w, 4), dtype=np.float32)

    base = _resample_to(layer_pixels[enabled[0].map_id], w, h)
    acc = apply_contrast_gamma(base[..., :3].astype(np.float32),
                               enabled[0].contrast, enabled[0].gamma)
    base_alpha = base[..., 3].astype(np.float32)

    for L in enabled[1:]:
        top = _resample_to(layer_pixels[L.map_id], w, h)[..., :3].astype(np.float32)
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
