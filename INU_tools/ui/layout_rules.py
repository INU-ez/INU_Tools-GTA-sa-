"""Blender's internal UI layout constants exposed to Python.

The floater (`ops/viewport_floater.py`) does its own GPU-based draw
instead of using Blender's UILayout, so it has to compute pixel
positions itself. Without help that's easy to get wrong — the floater
ends up using 18 where Blender uses 20, or omits a `layout.separator()`
gap, and the result looks ~10 % off from the equivalent N-panel.

This module is the **single source of truth** for those constants.
Every public function below maps to a specific symbol or formula in
Blender's C source (interface_layout.c, interface_widgets.c,
UI_interface.h). Callers — currently just the floater — should prefer
these helpers over hardcoded numbers; if Blender changes a constant
between versions the fix lives in one place.

Constants are **functions** (not module-level ints) because every
value scales with `bpy.context.preferences.system.pixel_size`
(HiDPI / Retina) and `bpy.context.preferences.view.ui_scale`
(user-configured UI zoom). Reading them is cheap (one preferences
access) and the floater calls them once per draw inside `_apply_theme`.

Reference table — Blender symbol → our helper:

    UI_UNIT_Y               → widget_unit()
    UI_DEFAULT_SPACING_Y    → inter_row_gap()
    UI_LAYOUT_BOX_MARGIN    → box_pad()
    layout.separator() span → separator_h()
    UI_UNIT_X               → widget_unit_x()

Helpers built on top of the constants:

    enum_row_rects(rect, n) → row.prop_enum() / row(align=True) rendering
    box_height(n_rows)      → height of layout.box() with N stacked rows
"""
import bpy


# ── Preference readers ───────────────────────────────────────────────
#
# Both default to 1.0 if prefs are unavailable (rare — usually only
# during early addon init before context is fully built). Floater
# constants will then evaluate to Blender's scale-1.0 defaults.

def _pixel_size():
    """Blender's `U.pixelsize` — combines monitor DPI and the internal
    UI scaling Blender applies based on screen size. 1.0 on a standard
    display, 2.0 on a Retina / 4K with auto-doubling, fractional values
    on tweaked setups."""
    try:
        return float(bpy.context.preferences.system.pixel_size)
    except Exception:
        return 1.0


def _ui_scale():
    """User-configured `Resolution Scale` from Edit → Preferences →
    Interface. Multiplies on top of `pixel_size`. Most users keep
    it at 1.0; modders sometimes bump to 1.1 / 1.2 for readability."""
    try:
        return float(bpy.context.preferences.view.ui_scale)
    except Exception:
        return 1.0


def effective_scale():
    """Combined scale that drives every other size below. Mirrors how
    Blender composes `U.pixelsize * U.dpi_fac` for widget metrics."""
    return max(0.5, _pixel_size() * _ui_scale())


# ── Core widget constants ────────────────────────────────────────────

def widget_unit():
    """`UI_UNIT_Y` from `source/blender/editors/include/UI_interface.h`.

    Standard height of a button / toggle / slider / label row.
    Hardcoded 20 in Blender source, multiplied by `U.pixelsize`
    before reaching the renderer. Raw value with no compensation —
    per-widget-kind SDF compensation lives in `layout_solver.py`
    `Leaf.request_height` because Blender renders different widget
    types at slightly different visible heights (operator buttons
    are 1 px taller than prop_enum / dropdown triggers)."""
    return max(14, int(round(20 * effective_scale())))


def widget_unit_x():
    """`UI_UNIT_X` — same 20-base as Y. Used by Blender for column
    sizing inside grids; we mostly use Y but expose X for parity."""
    return max(14, int(round(20 * effective_scale())))


def inter_row_gap():
    """`UI_DEFAULT_SPACING_Y` from `interface_layout.c`.

    Vertical gap inserted between consecutive rows inside a
    `column(align=False)`. ~2 px at scale 1. `align=True` columns
    collapse this to 0 (rows fuse)."""
    return max(2, int(round(2 * effective_scale())))


def box_pad():
    """`UI_LAYOUT_BOX_MARGIN` — internal padding `layout.box()` adds
    around its content. ~6 px at scale 1, all four sides equal."""
    return max(4, int(round(6 * effective_scale())))


def separator_h():
    """Height an empty `layout.separator()` reserves. Blender uses
    `UI_UNIT_Y * 0.5` for separators inside columns — we follow."""
    return widget_unit() // 2


def icon_size():
    """`ICON_DEFAULT_HEIGHT` — pixel size of a button icon slot.

    Blender computes ``size = ICON_DEFAULT_HEIGHT / (aspect * UI_INV_SCALE_FAC)``
    in ``interface_widgets.cc:1278``. For our floater the block aspect
    is always 1.0, so the formula reduces to
    ``16 * effective_scale()`` — i.e. 16 px at scale 1.0, 24 px at
    1.5×, 32 px at 2.0× (HiDPI).

    Earlier this returned a hardcoded 16 because Blender shipped
    pre-baked HiDPI PNG atlases. Modern Blender (>=4.x) rasterises
    SVG at request time through the BLF glyph cache, so size IS now
    scale-aware — and we mirror that here so a HiDPI user sees the
    floater iconography at the same physical size as the N-panel."""
    return max(8, int(round(16 * effective_scale())))


# ── Composed helpers ─────────────────────────────────────────────────
#
# Higher-level utilities built on the constants above. These match the
# geometry Blender's C layout solver produces for specific UILayout
# patterns so floater rects line up with the equivalent N-panel rects
# pixel-for-pixel.

def box_height(n_rows, row_h=None, row_gap=None, pad=None):
    """Height of a `layout.box()` containing N stacked label/button
    rows. Mirrors `4 * widget_unit + 3 * UI_DEFAULT_SPACING_Y +
    2 * UI_LAYOUT_BOX_MARGIN` for the common N=4 case (e.g. selection
    summary box: header + DFF + LOD + COL).

    All three components can be overridden — passing `row_gap=0`
    matches `column(align=True)`, for example."""
    if n_rows <= 0:
        return 0
    rh = row_h if row_h is not None else widget_unit()
    rg = row_gap if row_gap is not None else inter_row_gap()
    p  = pad if pad is not None else box_pad()
    return n_rows * rh + max(0, n_rows - 1) * rg + 2 * p


def enum_row_rects(rect, n_items):
    """Per-item rects for a fused horizontal row of `N` buttons,
    mirroring `row.prop_enum(...)` rendering. Each item overlaps the
    previous by 1 px so adjacent outlines fuse into a single divider
    line — without the overlap you'd see 2 px between items (one
    border from each button).

    Used by both the pipeline strip and the Import/Export menu pair.
    Returns the rect list so callers can also hit-test against them."""
    x, y, w, h = rect
    if n_items <= 0:
        return []
    step = (w + (n_items - 1)) // n_items
    rects = []
    for i in range(n_items):
        bx = x + i * (step - 1)
        if i == n_items - 1:
            bw = (x + w) - bx
        else:
            bw = step
        rects.append((bx, y, bw, h))
    return rects
