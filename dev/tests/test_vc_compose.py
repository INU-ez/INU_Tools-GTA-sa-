"""Tests for the VC Layer System composite math (Phase 2).

Pure-Python (``composite_stack_pixels``) and numpy
(``composite_stack_np``) compositors must produce the same results
modulo float tolerance — that's the invariant the live-preview path
relies on. Numpy is the production code path; the pure variant is a
reference implementation for testing and a fallback if numpy is gone.
"""

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.vc_layers import (  # noqa: E402
    apply_pre_adjust_pixel,
    blend_pixel,
    composite_stack_pixels,
    composite_stack_np,
    _HAS_NUMPY,
)


# ─────────────────────────── apply_pre_adjust_pixel ───────────────────

def test_pre_adjust_neutral_is_identity():
    pixel = (0.4, 0.6, 0.8, 1.0)
    out = apply_pre_adjust_pixel(pixel, brightness=0.0, contrast=1.0)
    assert out == pytest.approx(pixel)


def test_pre_adjust_brightness_offsets_rgb_only():
    out = apply_pre_adjust_pixel((0.5, 0.5, 0.5, 0.7),
                                  brightness=0.2, contrast=1.0)
    assert out == pytest.approx((0.7, 0.7, 0.7, 0.7))


def test_pre_adjust_contrast_pivots_around_half():
    # Contrast=2 doubles the spread around 0.5 → 0.4 → 0.3 (less),
    # 0.6 → 0.7 (more), 0.5 stays.
    out = apply_pre_adjust_pixel((0.4, 0.5, 0.6, 1.0),
                                  brightness=0.0, contrast=2.0)
    assert out == pytest.approx((0.3, 0.5, 0.7, 1.0))


def test_pre_adjust_clamps_overflow():
    # Brightness 0.5 on a 0.8 input → 1.3 → clamped to 1.0.
    out = apply_pre_adjust_pixel((0.8, 0.0, 0.0, 1.0),
                                  brightness=0.5, contrast=1.0)
    assert out == pytest.approx((1.0, 0.5, 0.5, 1.0))


def test_pre_adjust_clamps_negative():
    out = apply_pre_adjust_pixel((0.1, 0.5, 0.5, 1.0),
                                  brightness=-0.5, contrast=1.0)
    assert out == pytest.approx((0.0, 0.0, 0.0, 1.0))


# ─────────────────────────── blend_pixel ──────────────────────────────

def test_blend_normal_full_opacity_replaces_base():
    base = (0.0, 0.0, 0.0, 1.0)
    layer = (1.0, 0.0, 0.0, 1.0)
    out = blend_pixel(base, layer, opacity=1.0, mode='NORMAL')
    assert out == pytest.approx((1.0, 0.0, 0.0, 1.0))


def test_blend_normal_half_opacity_lerps():
    base = (0.0, 0.0, 0.0, 1.0)
    layer = (1.0, 0.0, 0.0, 1.0)
    out = blend_pixel(base, layer, opacity=0.5, mode='NORMAL')
    assert out == pytest.approx((0.5, 0.0, 0.0, 1.0))


def test_blend_zero_opacity_passthrough():
    base = (0.3, 0.4, 0.5, 1.0)
    layer = (0.9, 0.9, 0.9, 1.0)
    out = blend_pixel(base, layer, opacity=0.0, mode='NORMAL')
    assert out == pytest.approx(base)


def test_blend_zero_layer_alpha_passthrough():
    """Transparent layer pixel must contribute nothing regardless of mode."""
    base = (0.5, 0.5, 0.5, 1.0)
    layer = (1.0, 1.0, 1.0, 0.0)
    for mode in ('NORMAL', 'MULTIPLY', 'ADD', 'SUBTRACT'):
        out = blend_pixel(base, layer, opacity=1.0, mode=mode)
        assert out == pytest.approx(base), \
            f"mode {mode} broke alpha=0 invariant"


def test_blend_multiply_darkens():
    base = (0.5, 0.5, 0.5, 1.0)
    layer = (0.5, 1.0, 0.0, 1.0)
    out = blend_pixel(base, layer, opacity=1.0, mode='MULTIPLY')
    assert out == pytest.approx((0.25, 0.5, 0.0, 1.0))


def test_blend_add_clamped_at_one():
    base = (0.7, 0.0, 0.0, 1.0)
    layer = (0.5, 0.5, 0.5, 1.0)
    out = blend_pixel(base, layer, opacity=1.0, mode='ADD')
    # 0.7 + 0.5 = 1.2 → clamp 1.0
    assert out == pytest.approx((1.0, 0.5, 0.5, 1.0))


def test_blend_subtract_clamped_at_zero():
    base = (0.3, 0.5, 0.7, 1.0)
    layer = (0.5, 0.5, 0.5, 1.0)
    out = blend_pixel(base, layer, opacity=1.0, mode='SUBTRACT')
    # 0.3 - 0.5 = -0.2 → clamp 0
    assert out == pytest.approx((0.0, 0.0, 0.2, 1.0))


def test_blend_unknown_mode_raises():
    with pytest.raises(ValueError):
        blend_pixel((0,0,0,1), (1,1,1,1), 1.0, 'OVERLAY')


# ───────────────────────── composite_stack_pixels ─────────────────────

def test_compose_empty_stack_returns_base_unchanged():
    base = [(0.5, 0.0, 0.0, 1.0)] * 3
    out = composite_stack_pixels(base, [])
    assert out == base


def test_compose_invisible_layer_skipped():
    base = [(0.0, 0.0, 0.0, 1.0)]
    layer = [(1.0, 1.0, 1.0, 1.0)]
    out = composite_stack_pixels(base, [
        (layer, {'opacity': 1.0, 'blend_mode': 'NORMAL', 'visible': False,
                 'pre_brightness': 0.0, 'pre_contrast': 1.0}),
    ])
    assert out == [pytest.approx((0.0, 0.0, 0.0, 1.0))]


def test_compose_two_layers_normal():
    """Stack: black base, red 50% normal, then green 50% normal.
    Result should be red*0.5 then green*0.5 over that mid result."""
    base = [(0.0, 0.0, 0.0, 1.0)]
    red = [(1.0, 0.0, 0.0, 1.0)]
    green = [(0.0, 1.0, 0.0, 1.0)]

    out = composite_stack_pixels(base, [
        (red, {'opacity': 0.5, 'blend_mode': 'NORMAL', 'visible': True,
               'pre_brightness': 0.0, 'pre_contrast': 1.0}),
        (green, {'opacity': 0.5, 'blend_mode': 'NORMAL', 'visible': True,
                 'pre_brightness': 0.0, 'pre_contrast': 1.0}),
    ])

    # After red: (0.5, 0.0, 0.0). After green over that:
    # r = 0.5*0.5 + 0*0.5 = 0.25
    # g = 0.0*0.5 + 1.0*0.5 = 0.5
    # b = 0.0
    assert out[0] == pytest.approx((0.25, 0.5, 0.0, 1.0))


def test_compose_pre_brightness_then_blend():
    """pre_brightness should affect ONLY this layer's pixels, not the
    stack below. Verify by composing a layer with brightness=0.2 over
    a black base — result should reflect brightness'd colour, not
    blended-then-brightened."""
    base = [(0.0, 0.0, 0.0, 1.0)]
    layer = [(0.5, 0.5, 0.5, 1.0)]

    out = composite_stack_pixels(base, [
        (layer, {'opacity': 1.0, 'blend_mode': 'NORMAL', 'visible': True,
                 'pre_brightness': 0.2, 'pre_contrast': 1.0}),
    ])
    # Layer pixel after pre-adjust: (0.7, 0.7, 0.7, 1.0).
    # Normal blend full opacity over black: (0.7, 0.7, 0.7, 1.0).
    assert out[0] == pytest.approx((0.7, 0.7, 0.7, 1.0))


# ─────────────────────────── numpy parity ─────────────────────────────

@pytest.mark.skipif(not _HAS_NUMPY, reason="numpy not available")
def test_pure_and_numpy_compositors_agree():
    import numpy as np

    base_pixels = [
        (0.0, 0.0, 0.0, 1.0),
        (0.2, 0.4, 0.6, 1.0),
        (0.5, 0.5, 0.5, 1.0),
    ]
    layer_pixels = [
        (1.0, 0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0, 0.5),  # half-alpha
        (0.0, 0.0, 1.0, 1.0),
    ]

    metas = [
        {'opacity': 0.7, 'blend_mode': 'NORMAL', 'visible': True,
         'pre_brightness': 0.0, 'pre_contrast': 1.0},
        {'opacity': 1.0, 'blend_mode': 'MULTIPLY', 'visible': True,
         'pre_brightness': 0.1, 'pre_contrast': 1.5},
        {'opacity': 0.5, 'blend_mode': 'ADD', 'visible': True,
         'pre_brightness': 0.0, 'pre_contrast': 1.0},
        {'opacity': 1.0, 'blend_mode': 'SUBTRACT', 'visible': True,
         'pre_brightness': 0.0, 'pre_contrast': 1.0},
    ]
    layer_stacks = [(layer_pixels, m) for m in metas]

    pure_result = composite_stack_pixels(base_pixels, layer_stacks)

    # Numpy form
    base_np = np.array(base_pixels, dtype=np.float32)
    np_stacks = [(np.array(layer_pixels, dtype=np.float32), m) for m in metas]
    np_result = composite_stack_np(base_np, np_stacks)

    for i, (pure, npx) in enumerate(zip(pure_result, np_result)):
        for c in range(4):
            assert abs(pure[c] - float(npx[c])) < 1e-5, \
                f"pixel {i} channel {c}: pure={pure[c]} np={npx[c]}"


@pytest.mark.skipif(not _HAS_NUMPY, reason="numpy not available")
def test_numpy_compositor_handles_thousand_pixels():
    """Smoke-test a non-trivial size — make sure foreach-style numpy
    operations don't degrade on real-mesh-sized inputs."""
    import numpy as np
    n = 1000
    base = np.random.rand(n, 4).astype(np.float32)
    base[:, 3] = 1.0
    layer = np.random.rand(n, 4).astype(np.float32)

    meta = {'opacity': 0.5, 'blend_mode': 'NORMAL', 'visible': True,
            'pre_brightness': 0.05, 'pre_contrast': 1.2}

    out = composite_stack_np(base, [(layer, meta)])
    assert out.shape == (n, 4)
    assert (out >= 0.0).all()
    assert (out <= 1.0).all()


# ─────────────────────────── edge cases ──────────────────────────────

def test_compose_single_layer_full_opacity_normal_replaces_base():
    base = [(0.5, 0.5, 0.5, 1.0)] * 4
    layer = [(0.1, 0.2, 0.3, 1.0)] * 4
    out = composite_stack_pixels(base, [
        (layer, {'opacity': 1.0, 'blend_mode': 'NORMAL', 'visible': True,
                 'pre_brightness': 0.0, 'pre_contrast': 1.0}),
    ])
    for px in out:
        assert px == pytest.approx((0.1, 0.2, 0.3, 1.0))


def test_compose_zero_opacity_layer_skipped_fast_path():
    """opacity=0 should short-circuit BEFORE pre-adjust, so even an
    expensive contrast/brightness setting won't waste cycles."""
    base = [(0.5, 0.5, 0.5, 1.0)]
    layer = [(0.9, 0.9, 0.9, 1.0)]
    out = composite_stack_pixels(base, [
        (layer, {'opacity': 0.0, 'blend_mode': 'MULTIPLY', 'visible': True,
                 'pre_brightness': 0.5, 'pre_contrast': 2.5}),
    ])
    assert out[0] == pytest.approx((0.5, 0.5, 0.5, 1.0))
