"""Pure-logic helpers for the Vertex Color Layer System.

Layer attributes on a mesh are named with a prefix that encodes the
scope (Day / Night) so the panel can classify everything by name alone:

    Day base      → "Day"      (canonical prelight, game reads this)
    Night base    → "Night"    (canonical prelight, game reads this)
    Day layer     → "VCL_D_<label>"
    Night layer   → "VCL_N_<label>"

This file is bpy-free so the parsing / counting logic is testable
outside Blender. The actual operators live in
``INU_tools.tools.vc_layers``.
"""

from __future__ import annotations
from typing import Iterable, Optional, Tuple


VCL_PREFIX_DAY = "VCL_D_"
VCL_PREFIX_NIGHT = "VCL_N_"
BASE_DAY_NAME = "Day"
BASE_NIGHT_NAME = "Night"

# Hard cap per scope. Stacks compose into Day / Night during export
# flatten; more than 10 visible at once becomes both expensive (live
# preview composes every depsgraph tick) and unmanageable in the panel.
MAX_LAYERS_PER_STACK = 10


def parse_vcl_attr_name(name: str) -> Optional[Tuple[str, str]]:
    """Return ``(scope, label)`` for VCL attribute names, or ``None``.

    ``scope`` is the string ``'DAY'`` or ``'NIGHT'``. ``label`` is the
    user-visible portion after the prefix (may contain anything Blender
    accepts in attribute names — including spaces, Cyrillic etc.).
    """
    if name.startswith(VCL_PREFIX_DAY):
        return ('DAY', name[len(VCL_PREFIX_DAY):])
    if name.startswith(VCL_PREFIX_NIGHT):
        return ('NIGHT', name[len(VCL_PREFIX_NIGHT):])
    return None


def make_vcl_attr_name(scope: str, label: str) -> str:
    """Compose a VCL attribute name from ``scope`` and ``label``."""
    if scope == 'DAY':
        return VCL_PREFIX_DAY + label
    if scope == 'NIGHT':
        return VCL_PREFIX_NIGHT + label
    raise ValueError(f"Unknown VCL scope: {scope!r}")


def classify_attribute(name: str) -> str:
    """Bucket a color attribute name into a UI section.

    Returns one of:
        'BASE_DAY'   — the literal "Day" prelight attribute
        'BASE_NIGHT' — the literal "Night" prelight attribute
        'LAYER_DAY'  — VCL_D_… edit layer
        'LAYER_NIGHT'— VCL_N_… edit layer
        'OTHER'      — UV map, generic user attr, or non-VCL prelight
                       (treated as a "custom base")
    """
    if name == BASE_DAY_NAME:
        return 'BASE_DAY'
    if name == BASE_NIGHT_NAME:
        return 'BASE_NIGHT'
    parsed = parse_vcl_attr_name(name)
    if parsed is not None:
        return 'LAYER_' + parsed[0]
    return 'OTHER'


def auto_label(existing_labels: Iterable[str], base: str = "Layer") -> str:
    """Pick the first ``Layer_1`` / ``Layer_2`` / … not already taken.

    ``existing_labels`` is checked as a set — pass user-visible labels
    (without the VCL_ prefix). Falls back to ``Layer_overflow`` after
    9999 attempts; in practice we cap stacks at 10 so this never trips.
    """
    taken = set(existing_labels)
    for i in range(1, 10000):
        candidate = f"{base}_{i}"
        if candidate not in taken:
            return candidate
    return f"{base}_overflow"


def count_layers_per_scope(attr_names: Iterable[str]) -> Tuple[int, int]:
    """Walk an iterable of attribute names → ``(day_count, night_count)``."""
    day = 0
    night = 0
    for name in attr_names:
        parsed = parse_vcl_attr_name(name)
        if parsed is None:
            continue
        if parsed[0] == 'DAY':
            day += 1
        else:
            night += 1
    return day, night


def promote_to_base(name: str) -> str:
    """Strip a VCL prefix so the attribute becomes a "full prelight".

    A no-op for non-VCL names. The caller is responsible for ensuring
    the resulting name doesn't already exist on the mesh — Blender
    rejects duplicate color attribute names with a numeric suffix
    fallback (e.g. ``окна.001``) which would silently break the
    user's promote intent.
    """
    parsed = parse_vcl_attr_name(name)
    if parsed is None:
        return name
    return parsed[1]


def demote_to_layer(name: str, scope: str) -> str:
    """Add the VCL prefix matching *scope*, turning a base-prelight
    attribute into a layer. Already-VCL names pass through unchanged."""
    if parse_vcl_attr_name(name) is not None:
        return name
    return make_vcl_attr_name(scope, name)


# Blend modes for layer composition.
BLEND_MODES = ('NORMAL', 'MULTIPLY', 'ADD', 'SUBTRACT')


# ─────────────────────────── compose math ────────────────────────────
#
# All composite functions accept either pure-Python tuples (one pixel
# at a time, slow but easy to test) or numpy arrays (fast, used by the
# bpy wrapper for thousands of pixels at once). The ``_np`` variants are
# numpy-native and skipped when numpy isn't available — pytest CI can
# import the module either way.

try:
    import numpy as _np
    _HAS_NUMPY = True
except ImportError:
    _np = None
    _HAS_NUMPY = False


def apply_pre_adjust_pixel(rgba, brightness: float, contrast: float):
    """Apply pre-blend brightness/contrast to a single (r,g,b,a) tuple.

    Brightness is an additive offset on RGB (alpha unchanged).
    Contrast is a multiplicative scale around 0.5 mid-grey:
        out = (in - 0.5) * contrast + 0.5
    Output clamped to [0, 1].
    """
    r, g, b, a = rgba
    r = (r - 0.5) * contrast + 0.5 + brightness
    g = (g - 0.5) * contrast + 0.5 + brightness
    b = (b - 0.5) * contrast + 0.5 + brightness
    return (
        max(0.0, min(1.0, r)),
        max(0.0, min(1.0, g)),
        max(0.0, min(1.0, b)),
        a,
    )


def blend_pixel(base, layer_rgba, opacity: float, mode: str):
    """Composite one ``layer_rgba`` pixel onto ``base`` per the formula:

        Normal:    out = base*(1-α) + layer*α
        Multiply:  out = base*(1-α) + (base*layer)*α
        Add:       out = base*(1-α) + clamp(base+layer)*α
        Subtract:  out = base*(1-α) + clamp(base-layer)*α

    where ``α = layer_alpha * opacity``. The output alpha is the union
    of base alpha and effective α (so a fully-opaque base stays opaque
    even if every layer above it has α=0).
    """
    br, bg, bb, ba = base
    lr, lg, lb, la = layer_rgba

    alpha = la * opacity
    if alpha <= 0.0:
        return base

    if mode == 'NORMAL':
        nr, ng, nb = lr, lg, lb
    elif mode == 'MULTIPLY':
        nr, ng, nb = br * lr, bg * lg, bb * lb
    elif mode == 'ADD':
        nr = min(1.0, br + lr)
        ng = min(1.0, bg + lg)
        nb = min(1.0, bb + lb)
    elif mode == 'SUBTRACT':
        nr = max(0.0, br - lr)
        ng = max(0.0, bg - lg)
        nb = max(0.0, bb - lb)
    else:
        raise ValueError(f"Unknown blend mode: {mode!r}")

    one_minus = 1.0 - alpha
    return (
        br * one_minus + nr * alpha,
        bg * one_minus + ng * alpha,
        bb * one_minus + nb * alpha,
        max(ba, alpha),
    )


def composite_stack_pixels(base_pixels, layer_stacks):
    """Pure-Python compositor. Slow — for tests / fallback only.

    ``base_pixels`` — iterable of (r,g,b,a) tuples for the base buffer.
    ``layer_stacks`` — list of (pixels, meta) tuples, applied bottom→top.
        meta is a dict with ``opacity``, ``blend_mode``, ``visible``,
        ``pre_brightness``, ``pre_contrast``.
    Returns a list of (r,g,b,a) tuples — same length as ``base_pixels``.
    """
    out = list(base_pixels)
    for layer_pixels, meta in layer_stacks:
        if not meta.get('visible', True):
            continue
        opacity = meta.get('opacity', 1.0)
        if opacity <= 0.0:
            continue
        mode = meta.get('blend_mode', 'NORMAL')
        bright = meta.get('pre_brightness', 0.0)
        contrast = meta.get('pre_contrast', 1.0)
        # Apply pre-adjust + blend in a single per-pixel sweep — keeps
        # the inner loop tight even though we do two transformations.
        for i, layer_pixel in enumerate(layer_pixels):
            adjusted = apply_pre_adjust_pixel(layer_pixel, bright, contrast)
            out[i] = blend_pixel(out[i], adjusted, opacity, mode)
    return out


def composite_stack_np(base, layer_stacks):
    """Numpy compositor. ``base`` is an (N, 4) float array.

    ``layer_stacks`` — list of ``(layer_array, meta)`` where layer_array
    is an (N, 4) float array and meta is the same dict as in the pure
    variant. Returns an (N, 4) float array — same shape as ``base``.

    Roughly 100× faster than the pure-Python compositor on a 50k-loop
    mesh — that's the difference between a 50ms live-preview tick and
    a 5-second one. Required for the depsgraph-driven live preview.
    """
    if not _HAS_NUMPY:
        raise RuntimeError("numpy not available — use composite_stack_pixels")

    out = base.astype(_np.float32, copy=True)

    for layer, meta in layer_stacks:
        if not meta.get('visible', True):
            continue
        opacity = float(meta.get('opacity', 1.0))
        if opacity <= 0.0:
            continue
        mode = meta.get('blend_mode', 'NORMAL')
        bright = float(meta.get('pre_brightness', 0.0))
        contrast = float(meta.get('pre_contrast', 1.0))

        adjusted = layer.astype(_np.float32, copy=True)
        # Pre-adjust RGB only, alpha untouched.
        rgb = adjusted[:, :3]
        rgb -= 0.5
        rgb *= contrast
        rgb += 0.5 + bright
        _np.clip(rgb, 0.0, 1.0, out=rgb)

        # Effective per-pixel alpha = layer.a * opacity, broadcast over RGB.
        alpha = (adjusted[:, 3:4] * opacity).clip(0.0, 1.0)

        if mode == 'NORMAL':
            blended_rgb = adjusted[:, :3]
        elif mode == 'MULTIPLY':
            blended_rgb = out[:, :3] * adjusted[:, :3]
        elif mode == 'ADD':
            blended_rgb = _np.minimum(1.0, out[:, :3] + adjusted[:, :3])
        elif mode == 'SUBTRACT':
            blended_rgb = _np.maximum(0.0, out[:, :3] - adjusted[:, :3])
        else:
            raise ValueError(f"Unknown blend mode: {mode!r}")

        one_minus = 1.0 - alpha
        out[:, :3] = out[:, :3] * one_minus + blended_rgb * alpha
        # Alpha union — base keeps its alpha unless layer α exceeds it.
        out[:, 3:4] = _np.maximum(out[:, 3:4], alpha)

    return out
