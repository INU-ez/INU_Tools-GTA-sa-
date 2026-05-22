# INU_tools.ops.floater.theme
#
# Palette / radius / size constants for the floater subsystem, plus
# `_apply_theme()` which refreshes them from Blender's current theme
# once per draw.
#
# IMPORTANT: every consumer must access these as module attributes
# (`from ..floater import theme as TH; TH._C_BG`) rather than via
# `from .theme import _C_BG`. The `from ... import name` form binds a
# *new local* to the current value at import time and never tracks the
# mutations `_apply_theme()` makes to this module's globals.

import bpy

from ...ui import layout_rules as LR


# ── Layout dimensions (mutated by _apply_theme on HiDPI / UI scale) ──

# Title-bar height. Drag handle + close/collapse chrome live here.
# Recomputed from `LR.widget_unit()` each draw so it tracks user UI
# scale just like native Blender chrome.
_HEADER_H = 22

# Native Blender row metrics — height calibrated so 11pt text fits with
# ~4-5px vertical breathing room, matching native operator rows.
_BUTTON_H = 20

# Height for "regular" flat buttons (filter / enum rows). Slightly taller
# than dropdown rows so the un-decorated buttons read with a bit more
# weight against neighbouring labels.
_BUTTON_H_REG = 21

# Row stride for label rows inside a boxed column — equals native
# `widget_unit + small gap` (≈ 22 px at scale 1.0). Native `col.label()`
# advances Y by exactly this much, so matching it makes our diagnostic
# box and dropdown menus line up pixel-for-pixel with the N-panel.
_LINE_H = 22

# `_PAD` is both the outer body inset AND the inter-row gap. Native
# N-panel uses ~4 px between rows in `column(align=False)` so we match
# that here. _apply_theme() rescales it on HiDPI.
_PAD = 4


# ── Color defaults (mutated by _apply_theme from theme palette) ──────

_C_BG               = (0.18, 0.18, 0.18, 1.00)  # opaque — see panel draw notes
_C_BORDER           = (0.10, 0.10, 0.10, 1.00)
_C_PANEL_BORDER     = (0x4a / 255.0, 0x4a / 255.0, 0x4a / 255.0, 1.0)
_C_HEADER           = (0.27, 0.27, 0.27, 1.00)
_C_TEXT             = (0.85, 0.85, 0.85, 1.00)
_C_TEXT_SEL         = (1.00, 1.00, 1.00, 1.00)  # text on pressed/selected widgets
_C_LABEL            = (0.60, 0.60, 0.60, 1.00)
_C_DIM              = (0.45, 0.45, 0.45, 1.00)
_C_WARN             = (1.00, 0.70, 0.25, 1.00)
_C_ERROR            = (1.00, 0.35, 0.30, 1.00)

# Inset / dropdown surface defaults. `_apply_theme()` overwrites with
# theme-derived values; these are only used between module-import and
# the first draw call.
_C_BOX_BG            = (0x30 / 255.0, 0x30 / 255.0, 0x30 / 255.0, 1.0)  # layout.box()
_C_DROPDOWN_BG       = (0x29 / 255.0, 0x29 / 255.0, 0x29 / 255.0, 1.0)  # menu button
_C_DROPDOWN_PANEL_BG = (0x18 / 255.0, 0x18 / 255.0, 0x18 / 255.0, 1.0)  # popup menu_back
_C_MENU_SEL          = (0.27, 0.40, 0.65, 1.0)                          # wcol_menu.inner_sel — open-popup trigger

_C_CHECK_OFF      = (0.22, 0.22, 0.22, 1.00)
_C_CHECK_OFF_H    = (0.30, 0.30, 0.30, 1.00)
_C_CHECK_ON       = (0.35, 0.55, 0.85, 1.00)
_C_CHECK_ON_H     = (0.45, 0.65, 0.95, 1.00)
_C_CHECK_MARK     = (1.00, 1.00, 1.00, 1.00)

_C_BUTTON       = (0.28, 0.28, 0.28, 1.00)
_C_BUTTON_H     = (0.38, 0.38, 0.38, 1.00)
_C_BUTTON_SEL   = (0.35, 0.55, 0.85, 1.00)  # pressed/active — blue accent
_C_BUTTON_SEL_H = (0.45, 0.65, 0.95, 1.00)

# Per-widget shade factors from theme (-1.0..+1.0 added to RGB).
# These mirror wcol_*.shadetop / shadedown which natively drive the
# vertical button gradient. Zero on both = perfectly flat button.
_BTN_SHADE_TOP  = 0.0
_BTN_SHADE_DOWN = 0.0

_C_SLIDER_BG    = (0.20, 0.20, 0.20, 1.00)
_C_SLIDER_BG_H  = (0.26, 0.26, 0.26, 1.00)
_C_SLIDER_FILL  = (0.35, 0.55, 0.85, 1.00)  # accent — overridden by theme


# ── Corner radii — overwritten in _apply_theme from wcol_*.roundness ─

_R_PANEL    = 5
_R_BUTTON   = 4
_R_CHECK    = 2
_R_SLIDER   = 3


# ── Color math helpers ──────────────────────────────────────────────

def _rgb4(t, alpha=1.0):
    """Convert a Blender theme color tuple (3 or 4 floats) to RGBA-4."""
    if len(t) >= 4:
        return (t[0], t[1], t[2], t[3] if alpha is None else alpha)
    return (t[0], t[1], t[2], alpha)


def _lighten(c, amt=0.08):
    return (min(1.0, c[0] + amt),
            min(1.0, c[1] + amt),
            min(1.0, c[2] + amt),
            c[3] if len(c) > 3 else 1.0)


def _shade_rgb(c, shade):
    """Add Blender-style shade factor (-1..+1) to RGB, clamped to 0..1.

    Mirrors interface_widgets.cc which adds wcol_*.shadetop/shadedown
    (normalised) directly to the inner colour. shade > 0 lightens,
    shade < 0 darkens. shade == 0 returns the input verbatim — important
    for matching native flat buttons pixel-for-pixel.
    """
    if shade == 0:
        return c
    return (
        max(0.0, min(1.0, c[0] + shade)),
        max(0.0, min(1.0, c[1] + shade)),
        max(0.0, min(1.0, c[2] + shade)),
        c[3] if len(c) > 3 else 1.0,
    )


def _scale_rgb(c, k):
    return (c[0] * k, c[1] * k, c[2] * k, c[3] if len(c) > 3 else 1.0)


def _disabled_inner(button_rgb, panel_rgb, alpha=0.5):
    """Port of Blender's `widget_disabled` rendering — alpha-blends the
    widget's inner colour with the panel background to darken the fill
    so the button reads as "inactive". Blender doesn't reserve a
    dedicated theme slot for this state (none of `wcol_*.inner_*`
    map cleanly to disabled); the C-level implementation overlays a
    50 % transparent fill of `wcol_*.inner` onto the panel surface.

    Single point of disabled-color derivation — changes track theme
    automatically because both `button_rgb` and `panel_rgb` come from
    `_apply_theme()`'s `wcol_regular.inner` / `TH_BACK` reads."""
    return (
        button_rgb[0] * alpha + panel_rgb[0] * (1.0 - alpha),
        button_rgb[1] * alpha + panel_rgb[1] * (1.0 - alpha),
        button_rgb[2] * alpha + panel_rgb[2] * (1.0 - alpha),
        button_rgb[3] if len(button_rgb) > 3 else 1.0,
    )


def _hsl_mul(c, h_mul, s_mul, l_mul):
    """Multiply HSL components of `c` — direct port of Blender's
    `color_mul_hsl_v3` from interface_widgets.cc, used by
    `widget_active_color()` to derive the "popup-open" fill colour
    from a widget's idle inner colour.

    `colorsys.rgb_to_hls` returns (h, l, s) — note the swapped order
    vs Blender's HSL naming. Components clamped to [0, 1]."""
    import colorsys
    r, g, b = c[0], c[1], c[2]
    a = c[3] if len(c) > 3 else 1.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h = max(0.0, min(1.0, h * h_mul))
    l = max(0.0, min(1.0, l * l_mul))
    s = max(0.0, min(1.0, s * s_mul))
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return (r2, g2, b2, a)


def _srgb_grayscale(c):
    """Luminance of a colour, sRGB-weighted. Used by the dark-vs-light
    branch in `widget_active_color()` to pick L-multiplier 1.1 vs 1.2."""
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _widget_active_inner(idle_rgb, text_rgb):
    """Port of Blender's `widget_active_color()` inner-colour branch.

    When a widget enters the "active" / "popup-open" state Blender
    transforms the idle inner colour via HSL multiplication rather
    than swapping to a different theme slot:

        color_mul_hsl_v3(wcol->inner, 1.0, 1.15, dark ? 1.2 : 1.1)

    `dark = grayscale(text) > grayscale(inner)` — true for our dark
    theme where text is bright on a dark fill, so L-multiplier 1.2.
    """
    dark = _srgb_grayscale(text_rgb) > _srgb_grayscale(idle_rgb)
    return _hsl_mul(idle_rgb, 1.0, 1.15, 1.2 if dark else 1.1)


# ── Theme refresh ───────────────────────────────────────────────────

def _apply_theme():
    """Refresh module-level color constants from Blender's current theme.

    Called once per draw cycle so the floater follows live theme
    switches and matches whatever palette the user has on their N-panel
    right now. Wrapped in broad try/except — any missing wcol_* slot
    just keeps the current defaults rather than breaking the draw.
    """
    global _C_BG, _C_BORDER, _C_HEADER
    global _C_TEXT, _C_TEXT_SEL, _C_LABEL, _C_DIM
    global _C_BUTTON, _C_BUTTON_H, _C_BUTTON_SEL, _C_BUTTON_SEL_H
    global _BTN_SHADE_TOP, _BTN_SHADE_DOWN
    global _C_MENU_SEL
    global _C_CHECK_OFF, _C_CHECK_OFF_H, _C_CHECK_ON, _C_CHECK_ON_H, _C_CHECK_MARK
    global _C_SLIDER_BG, _C_SLIDER_BG_H, _C_SLIDER_FILL
    global _R_PANEL, _R_BUTTON, _R_CHECK, _R_SLIDER
    global _C_BOX_BG, _C_DROPDOWN_BG, _C_DROPDOWN_PANEL_BG
    global _HEADER_H, _BUTTON_H, _BUTTON_H_REG, _LINE_H, _PAD
    try:
        ui = bpy.context.preferences.themes[0].user_interface
    except Exception:
        return

    # ── Layout dimensions ── pulled from `ui.layout_rules` which
    # mirrors Blender's interface_layout.c constants. Centralising the
    # source means a fix to e.g. `inter_row_gap()` propagates here
    # automatically. Floater-specific overrides:
    #   • _HEADER_H — drag-handle bar, +1 widget unit of breathing room
    #   • _PAD — uses inter_row_gap() because it doubles as the
    #     between-row spacing in our body layout
    # Fixed 18-px heights, matching native Blender N-panels at default
    # UI scale. Earlier the floater used `widget_unit() + 3` to give
    # bigger click targets, but the user wants every panel and floater
    # row to read as the same height — so we override the DPI-adaptive
    # math here and pin the three dimensions to native row size.
    # +1 px on top of Blender's native 20 px widget_unit — our SDF
    # shader's outline_width=1 + AA fringe shaves the visible height
    # by 1 px vs how Blender's native widget renderer draws its 20-px
    # buttons, so we compensate to match the N-panel pixel-for-pixel.
    _BUTTON_H = 21
    _BUTTON_H_REG = 21
    _HEADER_H = 26
    _LINE_H   = 21
    _PAD      = LR.inter_row_gap() * 2 + 4  # ≈ 10 px — wider side padding (+4 over previous 6)

    # ── Corner radii ── derived from each widget slot's `roundness`
    # (0..1) multiplied by a sensible base. Native panels read this same
    # value so our rounding visually tracks the user's theme.
    def _radius_for(wcol_name, base):
        try:
            r = float(getattr(ui, wcol_name).roundness)
            return max(0.0, r * base)
        except Exception:
            return base
    # Bases mirror Blender's interface_widgets.cc which uses
    # U.widget_unit (≈ 20 px at default DPI) as the multiplier on
    # wcol.roundness. wcol_regular is the right slot for operator-style
    # buttons (roundness 0.18 in default theme → 3.6 px corners);
    # wcol_tool would pull from the pill-shaped toolbar slot which is
    # intentionally rounder (roundness 0.5) and not what we want here.
    _R_PANEL  = _radius_for('wcol_box', 8.0) + 1
    _R_BUTTON = _radius_for('wcol_regular', 10.0)
    _R_CHECK  = _radius_for('wcol_option', 8.0)
    _R_SLIDER = _radius_for('wcol_numslider', 10.0)

    # ── Panel background ── hardcoded to #181818, matching the N-panel
    # body colour that ships in the default Blender theme. wcol_box.inner
    # is the wrong slot for this (it's the "metabox" / nested-box slot
    # which renders much darker on top of a sub-panel header) and reading
    # it directly produced a near-black background that contrasted oddly
    # with the actual N-panel sitting next to the floater.
    # Panel / inset / dropdown backgrounds — fully theme-driven.
    # Two distinct colour-space rules apply (verified empirically
    # against the measured #363636 / #292929 / #292929 reference):
    #
    #   • Panel background is computed as the **linear-space average**
    #     of `space.gradients.gradient` and `space.gradients.high_gradient`.
    #     Blender resolves the viewport sidebar fill at theme-load
    #     time, in linear-light, then stores the sRGB result for
    #     rendering. (linear avg of 0.1882 and 0.2392 → sRGB 0.213
    #     = #363636.)
    #
    #   • Box / dropdown surfaces are alpha-composited at draw time
    #     in the UI sRGB framebuffer — naive sRGB lerp, *not* linear.
    #     Trying linear here gives results ~5/255 too bright.
    #
    #   • `wcol_menu.inner` has alpha=1.0 → no composite, direct.

    def _linear_avg_srgb(a, b):
        """Average two sRGB colours via linear-light space."""
        out = []
        for i in range(3):
            la = max(0.0, a[i]) ** 2.2
            lb = max(0.0, b[i]) ** 2.2
            out.append(((la + lb) * 0.5) ** (1.0 / 2.2))
        return (out[0], out[1], out[2], 1.0)

    def _composite_over_bg_srgb(fg_rgba, bg_rgba):
        """Alpha-composite `fg` over `bg` in straight sRGB (no
        gamma round-trip). Mirrors how Blender's UI draws transparent
        widgets into its sRGB framebuffer."""
        a = fg_rgba[3] if len(fg_rgba) >= 4 else 1.0
        if a >= 0.999:
            return (fg_rgba[0], fg_rgba[1], fg_rgba[2], 1.0)
        if a <= 0.001:
            return (bg_rgba[0], bg_rgba[1], bg_rgba[2], 1.0)
        return (
            bg_rgba[0] * (1.0 - a) + fg_rgba[0] * a,
            bg_rgba[1] * (1.0 - a) + fg_rgba[1] * a,
            bg_rgba[2] * (1.0 - a) + fg_rgba[2] * a,
            1.0,
        )

    # Panel bg — linear-space average of the viewport gradient stops.
    try:
        v3d = bpy.context.preferences.themes[0].view_3d
        grad = v3d.space.gradients
        _C_BG = _linear_avg_srgb(grad.gradient, grad.high_gradient)
    except Exception:
        _C_BG = (0x36 / 255.0, 0x36 / 255.0, 0x36 / 255.0, 1.0)

    # Box bg — sRGB-space alpha-composite of wcol_box.inner over panel.
    try:
        _C_BOX_BG = _composite_over_bg_srgb(ui.wcol_box.inner, _C_BG)
    except Exception:
        _C_BOX_BG = (0x30 / 255.0, 0x30 / 255.0, 0x30 / 255.0, 1.0)

    # Dropdown bg — wcol_menu.inner direct (alpha=1) or sRGB composite
    # if a non-default theme sets transparent menu surfaces.
    try:
        m = ui.wcol_menu.inner
        if len(m) >= 4 and m[3] < 0.999:
            _C_DROPDOWN_BG = _composite_over_bg_srgb(m, _C_BG)
        else:
            _C_DROPDOWN_BG = (m[0], m[1], m[2], 1.0)
    except Exception:
        _C_DROPDOWN_BG = (0x29 / 255.0, 0x29 / 255.0, 0x29 / 255.0, 1.0)

    # `wcol_menu.inner_sel` — exact colour Blender's N-panel paints on
    # a dropdown / menu trigger button when its popup is open. This is
    # SEPARATE from `wcol_regular.inner_sel` (the operator-button blue
    # accent we stored in `_C_BUTTON_SEL`) — `wcol_menu` is a darker
    # shade in the default theme, which is what makes the open-popup
    # state read as "pressed in" rather than "actively selected".
    try:
        ms = ui.wcol_menu.inner_sel
        _C_MENU_SEL = _rgb4(ms, 1.0)
    except Exception:
        _C_MENU_SEL = (0.27, 0.40, 0.65, 1.0)

    # Expanded-dropdown panel background — `wcol_menu_back.inner` is
    # the dark surface Blender uses when a popup menu is open
    # (#181818 in the default dark theme — measurably darker than
    # the regular menu button fill).
    try:
        mb = ui.wcol_menu_back.inner
        _C_DROPDOWN_PANEL_BG = (mb[0], mb[1], mb[2], 1.0)
    except Exception:
        _C_DROPDOWN_PANEL_BG = (0x18 / 255.0, 0x18 / 255.0, 0x18 / 255.0, 1.0)

    # Outline for INNER widgets (buttons, diag box, etc.) — uses the
    # theme's `wcol_box.outline` (darker, near-black in default theme)
    # so buttons keep their original visible-but-subtle border.
    try:
        ol = ui.wcol_box.outline
        _C_BORDER = _rgb4(ol, 1.0)
    except Exception:
        pass

    # Outline for the PANEL chrome itself (body + header strip) —
    # hardcoded mid-grey (#4a4a4a). Picked by the user from N-panel
    # via colour picker for default-theme parity. Separate from
    # `_C_BORDER` so widget borders don't get washed out.
    global _C_PANEL_BORDER
    _C_PANEL_BORDER = (0x4a / 255.0, 0x4a / 255.0, 0x4a / 255.0, 1.0)

    # ── Header strip ── source from N-panel's own back colour. The
    # N-panel lives inside the View 3D editor's UI region, so the
    # right slot is `theme.view_3d.space.panelcolors.back`. It's an
    # RGBA with low-ish alpha so we composite over the viewport bg
    # to get the actual on-screen colour.
    try:
        npb = bpy.context.preferences.themes[0].view_3d.space.panelcolors.back
        _C_HEADER = _composite_over_bg_srgb(npb, _C_BG)
    except Exception:
        # Fallback: hardcoded #3d3d3d matching the default-theme reading.
        _C_HEADER = (0x3d / 255.0, 0x3d / 255.0, 0x3d / 255.0, 1.0)

    # ── Text colors ── from box.text for general labels; derive
    # label/dim by scaling. text_sel (white in default theme) is used
    # for text on pressed/selected widgets — same convention as native.
    try:
        t = ui.wcol_box.text
        _C_TEXT = _rgb4(t, 1.0)
        _C_LABEL = _scale_rgb(_C_TEXT, 0.72)
        _C_DIM   = _scale_rgb(_C_TEXT, 0.55)
    except Exception:
        pass
    try:
        ts = ui.wcol_regular.text_sel
        _C_TEXT_SEL = _rgb4(ts, 1.0)
    except Exception:
        _C_TEXT_SEL = (1.0, 1.0, 1.0, 1.0)

    # ── Button widget ── wcol_regular is the standard operator button
    # slot (grey in default theme).
    try:
        bt = ui.wcol_regular.inner
        _C_BUTTON = _rgb4(bt, 1.0)
    except Exception:
        pass
    # Hover is a SUBTLE lighten of the idle colour — NOT inner_sel,
    # which is the depressed/selected state (blue accent) and is
    # reserved for actual on/pressed widgets via _C_BUTTON_SEL below.
    _C_BUTTON_H = _lighten(_C_BUTTON, 0.08)
    # Pressed / depressed / active state — matches native's
    # `depress=True` button rendering (the blue accent in default theme).
    try:
        bts = ui.wcol_regular.inner_sel
        _C_BUTTON_SEL = _rgb4(bts, 1.0)
    except Exception:
        _C_BUTTON_SEL = (0.35, 0.55, 0.85, 1.0)
    _C_BUTTON_SEL_H = _lighten(_C_BUTTON_SEL, 0.06)

    # Shade factors driving the vertical button gradient — native uses
    # these directly added to RGB at top/bottom of the inner area. With
    # both = 0 the button is flat (no gradient).
    try:
        _BTN_SHADE_TOP  = float(getattr(ui.wcol_regular, 'shadetop', 0)) / 100.0
        _BTN_SHADE_DOWN = float(getattr(ui.wcol_regular, 'shadedown', 0)) / 100.0
    except Exception:
        _BTN_SHADE_TOP = 0.0
        _BTN_SHADE_DOWN = 0.0

    # ── Checkbox ── use wcol_option (the radio/option slot)
    try:
        co = ui.wcol_option.inner
        _C_CHECK_OFF = _rgb4(co, 1.0)
        _C_CHECK_OFF_H = _lighten(_C_CHECK_OFF, 0.08)
    except Exception:
        pass
    try:
        cs = ui.wcol_option.inner_sel
        _C_CHECK_ON = _rgb4(cs, 1.0)
        _C_CHECK_ON_H = _lighten(_C_CHECK_ON, 0.10)
    except Exception:
        pass
    try:
        cm = ui.wcol_option.text_sel
        _C_CHECK_MARK = _rgb4(cm, 1.0)
    except Exception:
        pass

    # ── Slider ── wcol_numslider for the value-drag widget
    try:
        sb = ui.wcol_numslider.inner
        _C_SLIDER_BG = _rgb4(sb, 1.0)
        _C_SLIDER_BG_H = _lighten(_C_SLIDER_BG, 0.06)
    except Exception:
        pass
    try:
        sf = ui.wcol_numslider.item
        _C_SLIDER_FILL = _rgb4(sf, 1.0)
    except Exception:
        pass
