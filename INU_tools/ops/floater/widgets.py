# INU_tools.ops.floater.widgets
#
# Widget-level drawing primitives — checkbox, button, toggle, slider,
# menu button, collapsible header, enum row, dropdown layout, box.
# Each function takes a rect + state (hovered/pressed/checked/etc.)
# and renders the widget via the lower-level `gpu_shaders` SDF and
# `text_atlas` text pipeline.
#
# Also hosts `_tr()` — the UI-string translation bridge used both here
# (button labels) and by `Floater.__init__` over in viewport_floater.py
# (titles). Living here means widgets.py is self-contained for label
# rendering, and the future `base.py` can `from .widgets import _tr`
# without a cycle.

import bpy

from ... import T
from ...ui import layout_rules as LR
from . import theme as TH
from . import gpu_shaders as GS
from . import text_atlas as TA


# Inter-button gap in vertical button stacks (button rows are packed at
# `_BUTTON_H + _BTN_GAP` stride). Subclass `extend_body_layout` methods
# use this to position rows.
_BTN_GAP = 3


def _tr(text):
    """Translate a UI string for floater display.

    Native sidebar widgets (`layout.prop(..., text="Normals")`) get
    auto-translated by Blender via `bpy.app.translations`, but our
    floater renders text directly through `TA._text()` which bypasses
    that pipeline. This helper bridges both:

    1. Try `bpy.app.translations.pgettext_iface` — picks up the
       English-keyed translations registered by the addon at startup.
       This is what `layout.prop` calls internally.
    2. Fall back to `T()` for Russian-source strings already keyed in
       our own locale tables.

    Returns the original text if neither path matches.
    """
    if not text:
        return text
    try:
        out = bpy.app.translations.pgettext_iface(text)
        if out != text:
            return out
    except Exception:
        pass
    return T(text)


def _draw_checkbox(x, y, size, checked, hovered, alert=False):
    if alert and checked:
        # `row.alert = True` in N-panel paints the checkbox fill red.
        # Match that here — red fill replaces the accent when alert
        # is set and the box is checked.
        fill = TH._C_ERROR
    elif checked:
        fill = TH._C_CHECK_ON_H if hovered else TH._C_CHECK_ON
    else:
        fill = TH._C_CHECK_OFF_H if hovered else TH._C_CHECK_OFF
    top = TH._lighten(fill, 0.04)
    outline = TH._C_ERROR if alert else TH._C_BORDER
    # 1 px drop shadow under the widget — sits just below the bottom
    # outline so the checkbox reads as a "raised" element instead of a
    # flat coloured square. The line is inset by 1 px on each side so
    # the rounded-corner radius doesn't get a stray dark pixel poking
    # out below the rounded edge.
    GS._draw_rect(x + 1, y - 1, max(1, size - 2), 1,
               (0.0, 0.0, 0.0, 0.45))
    GS._draw_widget(x, y, size, size, fill, top, outline, TH._R_CHECK,
                 outline_width=1.0)
    if checked:
        # Inner mark — ✓ glyph drawn through the text atlas in the mark
        # colour. Matches Blender native, which draws a checkmark
        # character rather than a filled inner square. The glyph
        # advance-box is bigger than the visual stroke (typical font
        # bearings + descender area), so the naive `(size-tw)/2`
        # centring leaves the visual stroke offset slightly. Our Y
        # axis is bottom-up, so +Y nudges the glyph up — we shift +2 px
        # to lift the ✓ off the box's bottom edge.
        glyph = "✓"
        gsz = size - 2
        tw, th = TA._text_dims(glyph, size=gsz)
        tx = x + (size - tw) / 2 + 0.5
        ty = y + (size - th) / 2 + 1
        TA._text(int(tx), int(ty), glyph, TH._C_CHECK_MARK, size=gsz)


def _draw_box(rect, fill=None, outline=None, radius=None,
              corner_mask=None):
    """Inset container — mirrors `layout.box()` in native UI. Slightly
    lighter fill than the floater bg, 1 px outline, modest rounding so
    grouped content reads as a single visual unit.

    `corner_mask=None` means all corners rounded; pass an explicit
    mask (e.g. `GS.CORNER_TOP`) when this box fuses with a stack of
    widgets below — flattens the bottom corners so the shared edge
    reads as one continuous panel."""
    x, y, w, h = rect
    if fill is None:
        fill = TH._C_BOX_BG
    if outline is None:
        outline = TH._C_BORDER
    if radius is None:
        radius = max(2, int(round(TH._R_BUTTON)))
    cm = GS.CORNER_ALL if corner_mask is None else corner_mask
    GS._draw_widget(x, y, w, h, fill, fill, outline, radius,
                    outline_width=1.0, corner_mask=cm)


def _draw_value_dropdown(rect, label, hovered, active=False,
                         corner_mask=None):
    """Dropdown button styled like a property field — current value
    centred over the whole button rect, chevron pinned to the right
    edge.

    `active=True` (used when the dropdown list is expanded under the
    button) paints the fill with the theme's blue accent
    (`wcol_*.inner_sel`) AND flattens the bottom corners so the
    button merges seamlessly with the dropdown panel below it —
    same trick the enum-row uses to fuse adjacent buttons.

    `corner_mask=None` picks the auto behaviour above. Pass an explicit
    mask (e.g. `GS.CORNER_NONE`) to embed the dropdown inside a wider
    fused enum-row cluster — the dropdown panel still aligns because
    `_draw_dropdown_panel` uses `CORNER_BOTTOM` so the panel's top
    edge is always sharp regardless of the anchor's corner choice."""
    x, y, w, h = rect
    if active:
        # Open-popup trigger — Blender's `widget_state()` swaps
        # `wcol->inner = wcol->inner_sel` for the `UI_SELECT` flag
        # (which the popup-open state carries). For our dropdown
        # widget that's `wcol_regular.inner_sel` — the standard blue
        # accent already loaded into `_C_BUTTON_SEL` via _apply_theme.
        # No HSL transform: `widget_active_color()` only runs for the
        # HOVER state, not for UI_SELECT, so the colour is the raw
        # theme slot value.
        base = TH._C_BUTTON_SEL
        text_color = TH._C_TEXT_SEL
        auto_cm = GS.CORNER_TOP
    else:
        base = TH._lighten(TH._C_DROPDOWN_BG, 0.05) if hovered else TH._C_DROPDOWN_BG
        text_color = TH._C_TEXT
        auto_cm = GS.CORNER_ALL
    cm = auto_cm if corner_mask is None else corner_mask
    # When active the dropdown panel hangs below the trigger and (per
    # `_DD_ANCHOR_GAP`) overlaps the trigger's bottom — visually clipping
    # the button. Extend the widget down by 1 px in that state so the
    # ABOVE-panel portion stays the same height as the idle button.
    draw_y, draw_h = (y - 1, h + 1) if active else (y, h)
    GS._draw_widget(x, draw_y, w, draw_h, base, base, TH._C_BORDER, TH._R_BUTTON,
                 outline_width=1.0, corner_mask=cm)

    # Programmatic ▲▼ — matches Blender's shape_preset_trias_from_rect_menu.
    # See gpu_shaders._draw_menu_tria docstring.
    chev_sz = LR.icon_size()
    chev_x = x + w - chev_sz - 2
    GS._draw_menu_tria((chev_x, y + (h - chev_sz) // 2,
                        chev_sz, chev_sz), TH._C_TEXT_SEL)

    # Left-align label flush with the left edge of the button (small
    # 6 px inset). Native `prop()` in a row puts the value at the left
    # next to the property label / chevron — matching that here keeps
    # value-dropdowns (DXT backend, preset name) reading the same as
    # the N-panel equivalents.
    label = _tr(label)
    tw, th = TA._text_dims(label)
    tx = x + 6
    ty = y + (h - th) / 2
    TA._text(int(tx), int(ty), label, text_color)


def _draw_menu_button(rect, label, prefix_glyph, hovered,
                      corner_mask=GS.CORNER_ALL, active=False,
                      show_tria=True):
    """Button styled as a dropdown — prefix icon at left, label centred,
    ▼ dropdown indicator at right. Uses the same #292929 fill as the
    value-dropdown to read as one widget family.

    ``show_tria=False`` hides the ▼ chevron — for direct-action buttons
    (Import / Export now invoke the operator immediately, like the
    N-panel, instead of opening an in-floater dropdown).

    `prefix_glyph` can be either an icon name (Blender SVG bake) or a
    plain unicode character; we try the icon cache first, then fall
    back to a text glyph so old call-sites keep working.

    `corner_mask` lets callers fuse adjacent menu-buttons (Import /
    Export side-by-side) by turning off the inner-edge corners — same
    pattern enum-rows use.
    """
    x, y, w, h = rect
    if active:
        # Blue accent + bottom corners cut off so the button fuses
        # with the dropdown panel hanging below it.
        base = TH._C_BUTTON_SEL
        text_color = TH._C_TEXT_SEL
        # Keep whatever inter-button corner masking the caller asked
        # for (GS.CORNER_LEFT / RIGHT etc.) but also kill the bottom
        # corners — the dropdown rounds those at the panel's bottom
        # instead.
        corner_mask = corner_mask & GS.CORNER_TOP
    else:
        base = TH._lighten(TH._C_DROPDOWN_BG, 0.05) if hovered else TH._C_DROPDOWN_BG
        text_color = TH._C_TEXT
    GS._draw_widget(x, y, w, h, base, base, TH._C_BORDER, TH._R_BUTTON,
                 outline_width=1.0, corner_mask=corner_mask)

    # Left prefix icon — sized relative to the button height like the
    # rest of the floater widgets.
    if prefix_glyph:
        if prefix_glyph in GS._ICON_TEXTURES:
            isz = LR.icon_size()
            ix = x + 6
            iy = y + (h - isz) // 2
            GS._draw_icon((ix, iy, isz, isz), prefix_glyph, tint=TH._C_TEXT)
            prefix_pad = 6 + isz + 4
        else:
            pw, ph = TA._text_dims(prefix_glyph)
            TA._text(x + 6, y + (h - ph) // 2, prefix_glyph, TH._C_TEXT)
            prefix_pad = 6 + int(pw) + 4
    else:
        prefix_pad = 6

    # Right dropdown chevron. Pinned to 16 px so the 32 px source PNG
    # downsamples at integer 2:1 — matches every other floater icon
    # and keeps the chevron readable at native UI scale. Skipped for
    # direct-action buttons (show_tria=False).
    if show_tria:
        chev_sz = LR.icon_size()
        chev_x = x + w - chev_sz - 6
        GS._draw_menu_tria((chev_x, y + (h - chev_sz) // 2,
                            chev_sz, chev_sz), TH._C_TEXT_SEL)
        avail_r = chev_x - 4
    else:
        avail_r = x + w - 6

    # Left-align label right after the prefix icon. Native menu/operator
    # rows with `text="..."` after an icon put the text immediately to
    # the right of the icon — matching that here makes Import/Export
    # buttons read identically to the N-panel ones.
    label = _tr(label)
    tw, th = TA._text_dims(label)
    tx = x + prefix_pad
    ty = y + (h - th) / 2
    TA._text(int(tx), int(ty), label, text_color)


def _draw_collapsible_header(rect, label, expanded, hovered):
    """Section-collapse header. Triangle icon at left + centred label,
    no fill. Title goes full-bright (`TH._C_TEXT`) when the section is
    expanded so an open section reads as the active one; collapsed
    sections stay dim (`TH._C_LABEL`)."""
    x, y, w, h = rect
    label = _tr(label)
    icon_name = 'tria_down' if expanded else 'tria_right'
    # Both glyph and title go full-bright when the section is open
    # (or hovered) and stay dim when collapsed — keeps the chevron
    # in sync with its label, so the expanded section reads as one
    # active unit.
    # Always bright — N-panel keeps section headers at full text colour
    # whether expanded or collapsed.
    glyph_color = TH._C_TEXT
    title_color = TH._C_TEXT
    # Triangle — use the baked PNG icon when available so the chevron
    # matches the rest of the floater family (dropdowns / menu buttons
    # use the same source). Falls back to a unicode arrow if the cache
    # hasn't loaded yet (e.g. very first frame after addon enable).
    if icon_name in GS._ICON_TEXTURES:
        isz = LR.icon_size()
        iy = y + (h - isz) // 2
        GS._draw_icon((x + 4, iy, isz, isz), icon_name, tint=glyph_color)
    else:
        glyph = "▼" if expanded else "▶"
        _, gh = TA._text_dims(glyph)
        TA._text(x + 4, y + (h - gh) // 2, glyph, glyph_color)
    lw, lh = TA._text_dims(label)
    lx = x + (w - lw) / 2
    ly = y + (h - lh) // 2
    TA._text(int(lx), int(ly), label, title_color)


def _enum_row_rects(rect, n_items):
    """Thin wrapper over `layout_rules.enum_row_rects` kept so existing
    callers don't have to change. See `LR.enum_row_rects` for the
    geometry (1-px overlap so adjacent outlines fuse into one divider)."""
    return LR.enum_row_rects(rect, n_items)


def _draw_enum_row(rect, items, current_value, hover_index,
                   outer_corner_mask=GS.CORNER_ALL):
    """Horizontal row of attached buttons for selecting one enum value.

    Mirrors `row.prop_enum(prop, 'VALUE')` from native Blender: items
    touch with sharp inner edges (only the row's outer corners stay
    rounded) so the buttons read as one connected widget. Returns the
    list of per-item rects so the caller can hit-test in mouse handlers.

    `outer_corner_mask` is AND-ed with each item's auto mask — pass
    `GS.CORNER_BOTTOM` for the bottom-most row of a vertical fused
    stack so only BL/BR corners stay rounded (TL/TR flatten to merge
    with the row above)."""
    n = len(items)
    rects = _enum_row_rects(rect, n)
    if not rects:
        return []
    for i, (value, label, _tt) in enumerate(items):
        bx, by, bw, bh = rects[i]
        pressed = (value == current_value)
        hovered = (i == hover_index)
        # First button keeps left corners rounded; last keeps right
        # corners. Middle buttons get sharp corners on every edge so
        # adjacent buttons fuse into a continuous strip.
        if n == 1:
            cm = GS.CORNER_ALL
        elif i == 0:
            cm = GS.CORNER_LEFT
        elif i == n - 1:
            cm = GS.CORNER_RIGHT
        else:
            cm = GS.CORNER_NONE
        cm &= outer_corner_mask
        _draw_button((bx, by, bw, bh), label, hovered=hovered,
                     pressed=pressed, corner_mask=cm)
    return rects


def _draw_button(rect, label, hovered, pressed=False,
                 corner_mask=GS.CORNER_ALL, icon=None, translate=True,
                 disabled=False):
    """Native-feel rounded button rendered by the SDF widget shader.

    Gradient endpoints are driven by theme.wcol_regular.shadetop and
    shadedown — same values native uses, so when both are 0 we paint
    a perfectly flat button matching the theme's source `inner` colour.

    pressed=True renders in the accent/depressed state (matches
    Blender's `op = layout.operator(...); op.depress = True`).

    `disabled=True` renders the button greyed-out — text + icon at
    `TH._C_DIM`, hover ignored. Mirrors Blender's `layout.enabled =
    False` styling used by inactive widgets (e.g. the Day/Night name
    + V slot when no vcol attribute exists — the + button creating
    the attr stays enabled while everything around it is dimmed).

    `corner_mask` lets callers (e.g. enum-row) fuse adjacent buttons
    by turning off the inner-edge corners.

    `icon` — optional Blender-style icon name (matching a PNG in
    data/icons/). If given, the icon is rendered to the left of the
    label, or centred when label is empty.

    `translate=False` skips the i18n lookup and renders `label`
    verbatim. Mirrors `layout.operator(..., text="Add", translate=False)`
    — useful for short English action labels that would otherwise
    expand into longer Russian forms ("Add" → "Добавить") and overflow
    a narrow column.
    """
    x, y, w, h = rect
    if pressed:
        base = TH._C_BUTTON_SEL
        bottom = top = base
    elif disabled:
        # Disabled rendering — direct port of Blender's
        # `widget_color_disabled` (interface_widgets.cc:~2340):
        #
        #     wcol_theme_s.inner[3] *= factor      # factor = 0.5f
        #     wcol_theme_s.outline[3] *= factor
        #     wcol_theme_s.text[3] *= factor
        #     ...
        #
        # Blender multiplies the ALPHA channel of every theme colour
        # by 0.5 and lets the framebuffer's ALPHA blend mode composite
        # the half-transparent widget over the panel bg behind it.
        # We do the same — pass the inner colour with alpha 0.5 to the
        # SDF shader instead of pre-blending. Result depends on whatever
        # `_C_BG` is locally, so the disabled shade auto-tracks
        # both the theme's `wcol_regular.inner` AND our floater's
        # background colour without hardcoding either.
        base_rgb = TH._C_BUTTON
        base = (base_rgb[0], base_rgb[1], base_rgb[2], 0.5)
        bottom = TH._shade_rgb(base, TH._BTN_SHADE_DOWN)
        top    = TH._shade_rgb(base, TH._BTN_SHADE_TOP)
    else:
        base = TH._C_BUTTON_H if hovered else TH._C_BUTTON
        bottom = TH._shade_rgb(base, TH._BTN_SHADE_DOWN)
        top    = TH._shade_rgb(base, TH._BTN_SHADE_TOP)
    # Outline alpha follows the same 0.5 factor when disabled —
    # mirrors `wcol_theme_s.outline[3] *= factor` in Blender.
    outline_color = TH._C_BORDER
    if disabled:
        outline_color = (outline_color[0], outline_color[1],
                         outline_color[2], outline_color[3] * 0.5
                         if len(outline_color) > 3 else 0.5)
    GS._draw_widget(x, y, w, h, bottom, top, outline_color, TH._R_BUTTON,
                 outline_width=1.0, corner_mask=corner_mask)
    if disabled:
        # Text/icon alpha = 0.5 — direct port of
        # `wcol_theme_s.text[3] *= factor`. Use the regular `_C_TEXT`
        # colour with reduced alpha instead of swapping to `_C_DIM`;
        # this composites with the now-also-half-alpha button bg behind
        # it and matches Blender's pipeline exactly.
        tc = TH._C_TEXT
        label_color = (tc[0], tc[1], tc[2],
                       (tc[3] if len(tc) > 3 else 1.0) * 0.5)
    elif pressed:
        label_color = TH._C_TEXT_SEL
    else:
        label_color = TH._C_TEXT

    # Icon-only button: centre the icon, no label. Fixed at 16 px so
    # the 32 px source PNG downsamples at an integer 2:1 ratio —
    # every destination pixel covers exactly four source texels,
    # which keeps stroke widths uniform across the icon (1 px wide
    # everywhere, no 1/3-px flicker from sub-texel bilinear taps).
    if icon and not label:
        GS._draw_icon_centered((x, y, w, h), icon, size=LR.icon_size(),
                            tint=label_color)
        return

    # Translate the visible label so widget text picks up the same
    # locale dictionary native panels use. `translate=False` skips this
    # — see docstring for the rationale.
    label_text = _tr(label) if translate else label

    # Icon + label: icon at left edge, label centred in the REMAINING
    # space (between the icon's right edge and the button's right edge)
    # — matches Blender's native operator-button rendering where the
    # icon is left-aligned and the text balances inside the leftover
    # space, not across the whole button width.
    if icon:
        icon_size = LR.icon_size()
        icon_x = x + 6
        icon_y = y + (h - icon_size) // 2
        GS._draw_icon((icon_x, icon_y, icon_size, icon_size),
                   icon, tint=label_color)
        icon_right = icon_x + icon_size + 4
        right_edge = x + w - 6
        tw, th = TA._text_dims(label_text)
        tx = icon_right + (right_edge - icon_right - tw) / 2
        if tx < icon_right:
            tx = icon_right
        ty = y + (h - th) / 2
        TA._text(int(tx), int(ty), label_text, label_color)
        return

    # Plain text button — original path.
    tw, th = TA._text_dims(label_text)
    tx = x + (w - tw) / 2
    ty = y + (h - th) / 2
    TA._text(int(tx), int(ty), label_text, label_color)


def _draw_toggle(rect, label, on, hovered, alert=False):
    """Native-style boolean: small checkbox on the left, label to its right.

    Mirrors how `layout.prop(obj, 'bool_prop')` renders in a Blender N-panel
    when toggle=False (the default). Whole row is the click target so the
    user doesn't have to hit the 14×14 checkbox precisely.

    `alert=True` mirrors `row.alert = True` in the N-panel — paints the
    checkbox fill/outline + label red so the user spots an incompatible
    flag for the currently selected pipeline at a glance.
    """
    x, y, w, h = rect
    if hovered:
        # Subtle row-highlight on hover, matching native list-item feel
        GS._draw_rect_rounded(x, y, w, h, TH._C_HEADER, TH._R_BUTTON)
    # Fixed 14 px checkbox regardless of row height — earlier formula
    # `max(14, h-6)` made DFF Flags rows (h=22) render a 16 px box
    # while Auto-TXD (h=20) got 14, creating an inconsistent look
    # between sections. Native Blender draws all property checkboxes
    # at the same size; we match that here.
    box_size = 14
    box_x = x
    box_y = y + (h - box_size + 1) // 2
    _draw_checkbox(box_x, box_y, box_size, on, hovered, alert=alert)
    # `+3` lands a visible ~5 px gap between checkbox and label
    # (the font's left-side bearing already shifts rendered text
    # ~2 px right of `text_x`).
    text_x = box_x + box_size + 3
    _, th = TA._text_dims(label, 11)
    text_y = y + (h - th + 1) // 2
    label_color = TH._C_ERROR if alert else TH._C_TEXT
    TA._text(text_x, text_y, _tr(label), label_color, 11)


def _format_slider_value(value, is_float):
    if is_float:
        if abs(value) >= 1000:
            return f"{value:.1f}"
        return f"{value:.2f}".rstrip('0').rstrip('.')
    return str(int(round(value)))


def _draw_slider(rect, label, value, vmin, vmax, hovered, is_float=True):
    """Horizontal value slider: background fill + accent fill bar to
    the current value + 'label: value' centered text."""
    x, y, w, h = rect
    bg = TH._C_SLIDER_BG_H if hovered else TH._C_SLIDER_BG
    GS._draw_rect_rounded(x, y, w, h, bg, TH._R_SLIDER)

    # Fill bar to current value
    span = max(1e-6, vmax - vmin)
    t = max(0.0, min(1.0, (value - vmin) / span))
    fill_w = max(2, int(w * t))
    if fill_w > 2:
        GS._draw_rect_rounded(x, y, fill_w, h, TH._C_SLIDER_FILL, TH._R_SLIDER)

    GS._draw_rect_outline_rounded(x, y, w, h, TH._C_BORDER, TH._R_SLIDER)

    # Centered "label: value"
    val_str = _format_slider_value(value, is_float)
    full = f"{label}: {val_str}" if label else val_str
    tw, th = TA._text_dims(full)
    tx = x + (w - tw) / 2
    ty = y + (h - th) / 2
    TA._text(int(tx), int(ty), full, TH._C_TEXT)


# Row stride is bigger than the visible text so adjacent preset names
# read with the desired ~16 px visible gap (user-tuned).
_DD_ITEM_H = 22
_DD_SEP_H = 3
_DD_INNER_PAD_TOP = 4             # 4 px gap above the header label
_DD_INNER_PAD_BOTTOM = 4          # ~7 px visible gap below the last item
# Extra height on a "header" entry so the title row places the label
# ~11 px below the trigger button (accounting for the negative anchor
# gap below) with the 1-px underline and 4-px gap above first item.
_DD_HEADER_EXTRA_H = 6
# Negative gap — panel renders 1 px UP from the anchor bottom (i.e.
# overlaps the anchor by 1 px) so trigger and panel read as one fused
# widget without a visible seam, 1 px LOWER than the previous -2.
_DD_ANCHOR_GAP = -1


def _is_header_entry(entry):
    return (len(entry) > 1 and entry[1] == '__HEADER__')


# When a header row is present, items below it are pulled UP by this
# many px (overlapping the header's bottom edge), tightening the gap
# between the underline and the first item without moving the
# header text or its underline.
_DD_HEADER_PULL_UP = 2


def _dropdown_height(items):
    """Total pixel height for a dropdown panel containing `items`.
    `items` are 3-tuples (label, op_or_value, icon_name); we only
    need the label to recognise separator rows."""
    h = _DD_INNER_PAD_TOP + _DD_INNER_PAD_BOTTOM
    has_header = False
    for entry in items:
        label = entry[0]
        if label is None:
            h += _DD_SEP_H
        elif _is_header_entry(entry):
            h += _DD_ITEM_H + _DD_HEADER_EXTRA_H
            has_header = True
        else:
            h += _DD_ITEM_H
    if has_header:
        h -= _DD_HEADER_PULL_UP
    return h


def _dropdown_layout(anchor_rect, items, min_y=None):
    """Return (panel_rect, item_rects) for a dropdown anchored under
    `anchor_rect`. Panel normally hangs DOWN from the anchor's bottom edge
    with a 1-px gap so the two read as a continuous widget.

    When `min_y` is given (the panel's usable bottom) and the downward panel
    would drop below it, the menu FLIPS to open UPWARD above the anchor —
    that keeps it inside the floater's offscreen buffer, so it's not clipped
    and the window doesn't have to resize its buffer (which made it vanish).

    Shared by extend_body_layout (so click hit-test sees the rects)
    and _draw_open_dropdown (so we don't recompute during drawing)."""
    ax, ay, aw, ah = anchor_rect
    total_h = _dropdown_height(items)
    # Default: hang down; `ay` is the anchor's bottom edge.
    down_bottom = ay - _DD_ANCHOR_GAP - total_h
    if min_y is not None and down_bottom < min_y:
        # Not enough room below → open upward above the anchor's top edge.
        panel_rect = (ax, ay + ah + _DD_ANCHOR_GAP, aw, total_h)
    else:
        panel_rect = (ax, down_bottom, aw, total_h)
    dx, dy, dw, dh = panel_rect
    item_rects = []   # list of (kind, index, rect) where kind='item'|'sep'|'header'
    cur_top_y = dy + dh - _DD_INNER_PAD_TOP
    for i, entry in enumerate(items):
        label = entry[0]
        if label is None:
            item_rects.append(('sep', i, None))
            cur_top_y -= _DD_SEP_H
            continue
        if _is_header_entry(entry):
            row_h = _DD_ITEM_H + _DD_HEADER_EXTRA_H
            row_rect = (dx + 1, cur_top_y - row_h, dw - 2, row_h)
            item_rects.append(('header', i, row_rect))
            # Pull items below up by _DD_HEADER_PULL_UP — overlap the
            # header's bottom edge so the visible gap between underline
            # and first item shrinks without moving the underline.
            cur_top_y -= (row_h - _DD_HEADER_PULL_UP)
            continue
        row_rect = (dx + 1, cur_top_y - _DD_ITEM_H, dw - 2, _DD_ITEM_H)
        item_rects.append(('item', i, row_rect))
        cur_top_y -= _DD_ITEM_H
    return panel_rect, item_rects
