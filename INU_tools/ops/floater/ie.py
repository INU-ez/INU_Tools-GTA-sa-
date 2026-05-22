# INU_tools.ops.floater.ie
#
# ImportExportFloater — action shelf with Import / Export buttons,
# native-style dropdowns (TXD method, DXT backend, pipeline picker),
# DFF flags checkboxes, selection summary with throttled cache, and a
# diagnostic box showing the active mesh's vert/tri/material counts.

import bpy

from ...ui import layout_rules as LR
from . import theme as TH
from . import gpu_shaders as GS
from . import text_atlas as TA
from . import widgets as WG
from . import base as B


# ── ImportExportFloater: action buttons + native-panel popup ─────────

# Single row of dropdown menus mirroring panels.py:GTATOOLS_PT_export_panel
# which calls `row.menu(GTATOOLS_MT_import_menu/export_menu)`. Each tuple
# is (label, prefix-glyph, menu-idname). The menu itself owns the per-
# format entries (DFF / COL / CST / TXD / All).
_IE_MENUS = [
    ("Импорт",  "import", "GTATOOLS_MT_import_menu"),
    ("Экспорт", "export", "GTATOOLS_MT_export_menu"),
]

# Dropdown item lists — hardcoded to mirror GTATOOLS_MT_import_menu /
# export_menu's draw method. Each entry is (label, op_idname) where
# op_idname=None means "separator" (renders a thin divider, not
# selectable). We draw these ourselves instead of going through
# wm.call_menu / popup_menu so the dropdown is anchored directly below
# the button (Blender's Python API can't position native popups at a
# specific UI rect).
# Items are 3-tuples: (label, op_or_value, icon_name). Icon names
# match our PNG bake keys (lowercased Blender names) — see
# panels.py:521-549 for the N-panel originals.
_IE_DROPDOWN_ITEMS = {
    "GTATOOLS_MT_import_menu": [
        ("DFF",          "gtatools.import_dff", "mesh_data"),
        ("COL",          "gtatools.import_col", "mesh_icosphere"),
        ("CST",          "gtatools.import_cst", "text"),
        ("TXD",          "gtatools.import_txd", "image_data"),
        (None,           None,                  None),     # separator
        ("All",          "gtatools.inu_import", "file"),
    ],
    "GTATOOLS_MT_export_menu": [
        ("DFF",          "gtatools.export_dff", "mesh_data"),
        ("COL",          "gtatools.export_col", "mesh_icosphere"),
        ("CST",          "gtatools.export_cst", "text"),
        ("TXD",          "gtatools.export_txd", "image_data"),
        (None,           None,                  None),     # separator
        ("All → Папка",  "gtatools.export_all",     "file_folder"),
        ("All → IMG",    "gtatools.export_to_img",  "package"),
    ],
    # Prop-set dropdown: items are (label, enum-value, icon) and a click
    # writes the matching value to context.scene.inu_settings.<prop>.
    "__dxt_backend__": [
        ("Numpy",       "numpy",      None),
        ("Numpy fast",  "numpy_fast", None),
        ("GPU",         "gpu",        None),
    ],
}

# Dropdowns whose second-element-of-each-item is an enum value to set
# on context.scene.inu_settings rather than an operator idname.
_IE_PROP_DROPDOWN_BINDINGS = {
    "__dxt_backend__": "gtatools_dxt_backend",
}


def _dxt_backend_label(value):
    """Return the display label for a DXT-backend enum value, falling
    back to the raw value when unrecognised."""
    for entry in _IE_DROPDOWN_ITEMS["__dxt_backend__"]:
        lbl, val = entry[0], entry[1]
        if val == value:
            return lbl
    return str(value)


_IE_PIPELINE = [
    ('NONE',       'Нет',      "Без pipeline"),
    ('0x53F2009A', 'Vehicle',  "Pipeline кузова машины"),
    ('0x53F20098', 'D/N',      "Day/Night vertex colors"),
    ('0x53F2009C', 'Building', "Простой pipeline здания"),
    ('PED',        'Ped',
     "Preset для персонажа: skin=True, day/night vcols + MatFX off"),
]

# DFF Flags rows duplicated from panels.py:GTATOOLS_PT_export_panel.
# Each tuple is (mesh.inu attribute, displayed label, game-filter).
# game-filter='sa_only' means the row is only shown when the scene's
# game version is GTA SA (mirrors `if _is_sa:` checks in panels.py:
# 763, 769). All flags are always shown regardless of pipeline —
# pipeline only changes which flags get the red `alert` highlight,
# matching the N-panel's `row.alert = True` behaviour.
_DFF_FLAGS = [
    ('export_normals',     "Normals",                   None),
    ('light',              "Light",                     None),
    ('modulate_color',     "Modulate Color",            None),
    ('set_material_alpha', "Set Material Alpha",        None),
    ('light_beam_asi',     "Light Beam (SA_Light.asi)", 'sa_only'),
    ('export_binsplit',    "Bin Mesh PLG",              None),
    ('uv_map1',            "UV1",                       None),
    ('uv_map2',            "UV2",                       None),
    ('day_cols',           "Day",                       None),
    ('night_cols',         "Night",                     'sa_only'),
]


# Pipeline → flags that DON'T belong on it. Mirrors panels.py:729-751
# (`_PIPE_FORBIDDEN` in GTATOOLS_PT_export_panel). Flags listed here
# get `row.alert = True` styling in the N-panel; the floater renders
# them with a red checkbox/label so the user spots an incompatible
# combination at a glance. Keep in sync with the N-panel dict.
_PIPE_FORBIDDEN = {
    '0x53F2009A': {  # Vehicle
        'day_cols', 'night_cols',
        'light_beam_asi',
    },
    '0x53F20098': {  # D/N Building
        'uv_map2',
    },
    '0x53F2009C': {  # Building (без D/N)
        'night_cols',
        'uv_map2',
        'light_beam_asi',
    },
    'PED': {
        'day_cols', 'night_cols',
        'modulate_color',
        'set_material_alpha',
        'light_beam_asi',
        'uv_map2',
    },
}


def _dff_flags_visible(context):
    """Return [(attr, label), ...] for DFF Flags applicable to the
    current scene's game version. Mirrors panels.py: SA-only flags
    (Light Beam, Night) are hidden on III/VC. Pipeline does NOT filter
    here — all flags stay visible, with `alert=True` painting forbidden
    combinations red. See `_PIPE_FORBIDDEN` for the alert ruleset."""
    try:
        from ...core import game_versions as _gv
        is_sa = (_gv.game_of_scene(context.scene) == 'SA')
    except Exception:
        is_sa = True
    out = []
    for attr, label, filt in _DFF_FLAGS:
        if filt == 'sa_only' and not is_sa:
            continue
        out.append((attr, label))
    return out


def _ie_mesh_inu(context):
    """Active mesh's .inu PropertyGroup, or None if no eligible object."""
    obj = context.active_object
    if obj and obj.type == 'MESH' and hasattr(obj, 'inu'):
        return obj.inu
    return None


# Selection summary cache.
#
# `find_all_selected_model_groups` falls back to iterating the entire
# active collection when nothing is selected, which on large maps is
# slow enough to freeze redraws. The summary doesn't need to be
# pixel-fresh — throttling to ~6 Hz makes hover redraws cheap while
# still reacting to a real selection change within ~150 ms.
import time as _time
_SELECTION_CACHE = {'t': -1.0, 'data': None}
_SELECTION_TTL = 0.15


def _ie_selection_summary(context):
    """Mirror panels.py's selection-diagnostic block — returns dict
    {selected_count, lines: [(kind, exists, label), ...]} where label is
    a "TYPE: name" / "TYPE: -" string with " +N" suffix when the
    selection covers multiple groups of the same kind.
    """
    now = _time.monotonic()
    if (_SELECTION_CACHE['data'] is not None
            and (now - _SELECTION_CACHE['t']) < _SELECTION_TTL):
        return _SELECTION_CACHE['data']

    try:
        from ...tools.model_utils import (
            find_selected_models, find_all_selected_model_groups,
        )
        models = find_selected_models()
        groups = find_all_selected_model_groups()
    except Exception:
        models = {'DFF': None, 'LOD': None, 'COL': None}
        groups = {}
    selected_count = len(
        [o for o in context.selected_objects if o.type == 'MESH'])
    counts = {'DFF': 0, 'LOD': 0, 'COL': 0}
    for g in groups.values():
        for k in counts:
            if g[k] is not None:
                counts[k] += 1
    lines = []
    for kind in ('DFF', 'LOD', 'COL'):
        obj = models[kind]
        if obj is None:
            label = f"{kind}: -"
        else:
            n = counts[kind]
            label = (f"{kind}: {obj.name}" if n <= 1
                     else f"{kind}: {obj.name} +{n - 1}")
        lines.append((kind, obj is not None, label))

    data = {'selected_count': selected_count, 'lines': lines}
    _SELECTION_CACHE['t'] = now
    _SELECTION_CACHE['data'] = data
    return data


# Diagnostic box: header row ("Выделено: N меш(ей)") + 3 detail lines
# (DFF/LOD/COL). Sits at the top of body, below the floater chrome.
_DIAG_INNER_PAD = 6
_DIAG_BODY_LINES = 4


def _diag_box_h():
    """Height of the selection diagnostic box (4 rows: header + DFF +
    LOD + COL).

    Geometry must mirror `_draw_diagnostic_box`: row_h = `_BUTTON_H`,
    row_gap = 3 px (more breathing room between label rows, matches
    N-panel's spacing), pad = `_DIAG_INNER_PAD`. With the current
    constants this yields ~105 px tall for 4 rows.
    """
    return LR.box_height(_DIAG_BODY_LINES,
                         row_h=TH._BUTTON_H,
                         row_gap=3,
                         pad=_DIAG_INNER_PAD)


class ImportExportFloater(B.Floater):
    """Quick-access import/export buttons + a popup-trigger for the
    full Экспорт / Импорт panel (rendered via wm.call_panel so all
    native Blender widgets — file pickers, toggles, etc. — work)."""

    def __init__(self):
        super().__init__(
            name='ie',
            title='Экспорт / Импорт',
            prop_names={
                'visible':   'inu_floater_ie_visible',
                'collapsed': 'inu_floater_ie_collapsed',
                'locked':    'inu_floater_ie_locked',
                'workspace': 'inu_floater_ie_workspace',
                'x':         'inu_floater_ie_x',
                'y':         'inu_floater_ie_y',
            },
            default_pos=(340, 200),
        )
        # Title icon — matches the same icon Blender's N-panel shows
        # next to the "Экспорт / Импорт" section header.
        self.title_icon = 'export'

    def _draw_open_dropdown(self, context, L):
        """Resolve the items list for the currently-open IE dropdown
        and delegate the actual rendering to the base class. Items
        come from the static `_IE_DROPDOWN_ITEMS` dict, keyed by the
        anchor button's menu_id."""
        dd = self.state.open_dropdown
        if not dd:
            return
        items = _IE_DROPDOWN_ITEMS.get(dd['menu_id'])
        if items:
            self._draw_dropdown_panel(L, items)

    def _draw_diagnostic_box(self, context, rect):
        """Render the selection summary box, pixel-aligned with the
        equivalent `layout.box()` in the N-panel at panels.py:686-691.

        Native layout the box mirrors:
            box = layout.box()                                    # 1 px border + ~6 px pad
            box.label(text=T("Выделено: ..."), icon='OBJECT_DATA')   # row 0
            col = box.column()                                    # 3 px inter-row gap
            for kind in ('DFF', 'LOD', 'COL'):
                col.label(...)                                    # rows 1-3

        Layout rules mirrored from Blender's interface_layout.c:
          • Row height                    = `widget_unit` (=TH._BUTTON_H, 20 px @ scale 1)
          • Inter-row gap (align=False)   = UI_DEFAULT_SPACING_Y ≈ 2 px
          • Box internal padding          = ~6 px on every side
          • Icon X offset inside row      = small left pad (4 px)
          • Icon size                     = 16 px, vertically centred in row
          • Text                          = immediately after icon + 4 px gap,
                                            vertically centred in row
        """
        bx, by, bw, bh = rect
        # Top of the fused IO stack — only TL/TR rounded so the
        # bottom edge merges flat with the Import/Export row below.
        WG._draw_box(rect, corner_mask=GS.CORNER_TOP)
        summary = _ie_selection_summary(context)

        row_h    = TH._BUTTON_H               # 20 at scale 1.0 — Blender widget_unit
        row_gap  = 3                          # vertical gap between rows — matches N-panel's label-row spacing
        pad      = _DIAG_INNER_PAD         # 6 — UI_LAYOUT_BOX_MARGIN-ish
        icon_pad = 4                       # icon left-inset inside a label row
        icon_sz  = LR.icon_size()
        gap_it   = 4                       # icon→text gap

        # Build the row list: (icon_name, label_text, color).
        # Use Blender's i18n at draw time so the string follows the
        # active locale (e.g. "Selected" / "Seleccionado").
        from ... import T
        rows = [(
            'object_data',
            f"{T('Выделено')}: {summary['selected_count']} {T('меш(ей)')}",
            TH._C_TEXT,
        )]
        for _kind, exists, label in summary['lines']:
            # Always bright — N-panel keeps DFF/LOD/COL labels at full
            # text colour regardless of whether the model is present.
            rows.append(('checkmark' if exists else 'x', label, TH._C_TEXT))

        # Rows stack from the TOP of the box downwards, separated by
        # `row_h + row_gap` strides.
        top_y = by + bh - pad
        for i, (icon_name, label, color) in enumerate(rows):
            row_top    = top_y - i * (row_h + row_gap)
            row_bottom = row_top - row_h

            # Icon vertically centred inside the row's widget_unit slot.
            # Icon sits 3 px to the left of the original `pad + icon_pad`
            # column — text stays anchored where it was, only the icon
            # shifts.
            icon_x_shift = 3
            if icon_name in GS._ICON_TEXTURES:
                icon_y = row_bottom + (row_h - icon_sz) // 2
                GS._draw_icon((bx + pad + icon_pad - icon_x_shift,
                               icon_y, icon_sz, icon_sz),
                           icon_name, tint=color)
                text_x = bx + pad + icon_pad + icon_sz + gap_it
            else:
                glyph = "✓" if icon_name == 'checkmark' else "×"
                _, gh = TA._text_dims(glyph)
                gy = row_bottom + (row_h - gh) // 2
                TA._text(bx + pad + icon_pad - icon_x_shift,
                         int(gy), glyph, color)
                gw, _ = TA._text_dims(glyph)
                text_x = bx + pad + icon_pad + int(gw) + gap_it

            # Text vertically centred inside the same row slot.
            _, th = TA._text_dims(label)
            text_y = row_bottom + (row_h - th) // 2
            TA._text(int(text_x), int(text_y), label, color)

    def _layout_sections(self, context):
        """Compute vertical layout for collapsible sections only.

        Returns a list [(section_id, header_h, body_h_when_expanded,
        expanded, body_extras)] where body_extras carries per-section
        data (flag rows for DFF Flags). Called from both compute_body_height
        and extend_body_layout to keep the height + the rects in sync.
        """
        ss = context.scene.inu_settings
        sections = []

        inu = _ie_mesh_inu(context)
        if inu is not None:
            flag_rows = _dff_flags_visible(context)
            flags_expanded = bool(ss.gtatools_show_dff_flags)
            # Flag-row geometry. Each row is a 14-px checkbox with a
            # 6-px gap to the next, padded 7 px top/bottom and 4 px
            # left-inset from the body's left edge.
            _FLAG_ROW_H   = 14
            _FLAG_ROW_GAP = 6
            _FLAG_TOP_PAD = 7
            _FLAG_BOT_PAD = 7
            _FLAG_LEFT_PAD = 5
            _flag_body_h = (
                _FLAG_TOP_PAD
                + len(flag_rows) * _FLAG_ROW_H
                + max(0, len(flag_rows) - 1) * _FLAG_ROW_GAP
                + _FLAG_BOT_PAD
            ) if flag_rows else 0
            sections.append((
                'dff_flags',
                TH._BUTTON_H,
                _flag_body_h if flags_expanded else 0,
                flags_expanded,
                {
                    'rows': flag_rows,
                    'inu': inu,
                    'row_h':   _FLAG_ROW_H,
                    'row_gap': _FLAG_ROW_GAP,
                    'top_pad': _FLAG_TOP_PAD,
                    'left_pad': _FLAG_LEFT_PAD,
                },
            ))
        return sections

    def compute_body_height(self, context):
        # Mirrors `extend_body_layout` — must use the same inter-row
        # gaps or the body clips / leaves trailing whitespace.
        gap_row       = 0
        gap_after_box = 0
        gap_separator = 0
        base = (_diag_box_h()                              # selection box
                + gap_after_box + TH._BUTTON_H                # Import/Export
                + gap_row + TH._BUTTON_H                      # toggle + DXT
                + gap_row + gap_separator + TH._BUTTON_H_REG) # pipeline (after separator)
        sections_h = 0
        for _id, hdr, body, _exp, _ex in self._layout_sections(context):
            sections_h += TH._PAD + hdr + body
        return base + sections_h

    def extend_body_layout(self, context, L):
        x, w = L['x'], L['w']

        buttons = []   # list of (rect, label, op_idname, op_kwargs)
        toggles = []   # list of {rect, label, owner, prop}
        menus = []     # list of (rect, label, prefix, menu_idname)

        # Selection diagnostic box at the very top of body.
        dbh = _diag_box_h()
        diag_y = L['body_top_y'] - dbh
        diag_rect = (x + TH._PAD, diag_y, w - 2 * TH._PAD, dbh)

        # Fully-fused layout — adjacent rows OVERLAP by 1 px so their
        # 1-px outlines collapse into a single shared border. Same
        # pattern as `_enum_row_rects` uses horizontally — without
        # overlap, outlines sit 1 px apart and leave a visible gap.
        gap_row       = -1
        gap_after_box = -1
        gap_separator = -1

        # Import / Export menus — fused 2-item row, equal-width with
        # the shared divider at the center (1-px overlap so outlines
        # merge into one line). Same horizontal split is reused for
        # Auto TXD / Numpy below so column edges align.
        menu_top_y = diag_y - gap_after_box
        menu_row_rect = (x + TH._PAD, menu_top_y - TH._BUTTON_H,
                         w - 2 * TH._PAD, TH._BUTTON_H)
        menu_rects = WG._enum_row_rects(menu_row_rect, len(_IE_MENUS))
        for i, (label, prefix, menu_id) in enumerate(_IE_MENUS):
            menus.append((menu_rects[i], label, prefix, menu_id))

        # Auto-TXD toggle + DXT backend dropdown — same 50/50 split as
        # Import/Export above so the divider lines stack vertically.
        toggle_y = menu_top_y - TH._BUTTON_H - gap_row - TH._BUTTON_H
        toggle_row_rect = (x + TH._PAD, toggle_y,
                           w - 2 * TH._PAD, TH._BUTTON_H)
        txd_rect, dxt_rect = WG._enum_row_rects(toggle_row_rect, 2)
        toggles.append({
            'rect': txd_rect,
            'label': "Авто TXD",
            'owner': context.scene.inu_settings,
            'prop': 'gtatools_txd_auto_import',
        })

        # Pipeline enum-row sits below an explicit `layout.separator()`
        # in the N-panel (panels.py:703), so we add the extra
        # half-widget gap on top of the regular row gap. Uses
        # `_BUTTON_H_REG` (regular/flat buttons sit slightly taller than
        # dropdown rows).
        pipeline_y = toggle_y - gap_row - gap_separator - TH._BUTTON_H_REG
        pipeline_rect = (x + TH._PAD, pipeline_y, w - 2 * TH._PAD, TH._BUTTON_H_REG)

        # Collapsible sections stack below the pipeline row.
        sections = []   # list of {id, header_rect, body_rect, expanded, ...}
        section_specs = self._layout_sections(context)
        cur_y = pipeline_y
        for sid, hdr_h, body_h, expanded, extras in section_specs:
            cur_y -= TH._PAD + hdr_h
            header_rect = (x + TH._PAD, cur_y, w - 2 * TH._PAD, hdr_h)
            body_rect = None
            if expanded and body_h > 0:
                cur_y -= body_h
                body_rect = (x + TH._PAD, cur_y, w - 2 * TH._PAD, body_h)
            sec = {
                'id': sid,
                'header_rect': header_rect,
                'body_rect': body_rect,
                'expanded': expanded,
                'extras': extras,
            }
            # Per-section: precompute flag-toggle rects for DFF Flags so
            # mousemove/press don't have to redo the math.
            if sid == 'dff_flags' and expanded and extras:
                fxs = []
                row_h    = extras['row_h']
                row_gap  = extras['row_gap']
                top_pad  = extras['top_pad']
                left_pad = extras['left_pad']
                body_top_y = body_rect[1] + body_rect[3]
                try:
                    pipeline = context.scene.inu_settings.gtatools_export_pipeline
                except Exception:
                    pipeline = 'NONE'
                forbidden = _PIPE_FORBIDDEN.get(pipeline, set())
                for i, (attr, label) in enumerate(extras['rows']):
                    fy = body_top_y - top_pad - i * (row_h + row_gap) - row_h
                    fxs.append({
                        'rect': (body_rect[0] + left_pad, fy,
                                 body_rect[2] - left_pad, row_h),
                        'label': label,
                        'owner': extras['inu'],
                        'prop': attr,
                        'alert': attr in forbidden,
                    })
                sec['flag_toggles'] = fxs
            sections.append(sec)

        # Pipeline per-item rects: precomputed here so the click handler
        # (which builds its own L from compute_layout without running
        # draw_body) can still hit-test individual enum buttons.
        pipeline_item_rects = WG._enum_row_rects(pipeline_rect, len(_IE_PIPELINE))

        # Same for the open dropdown — anchor rect is stored on state when
        # a menu button is clicked, so we can compute the per-item hit
        # rects without waiting for the next draw.
        dropdown_rect = None
        dropdown_items = []
        if self.state.open_dropdown is not None:
            mid = self.state.open_dropdown['menu_id']
            ditems = _IE_DROPDOWN_ITEMS.get(mid)
            if ditems:
                dropdown_rect, dropdown_items = WG._dropdown_layout(
                    self.state.open_dropdown['anchor_rect'], ditems)

        L['buttons'] = buttons
        L['toggles'] = toggles
        L['menus'] = menus
        L['dxt_rect'] = dxt_rect
        L['diag_rect'] = diag_rect
        L['pipeline_rect'] = pipeline_rect
        L['pipeline_item_rects'] = pipeline_item_rects
        L['dropdown_rect'] = dropdown_rect
        L['dropdown_items'] = dropdown_items
        L['sections'] = sections

    def draw_body(self, context, L):
        st = self.state

        # Selection diagnostic box (read-only display, top of body)
        self._draw_diagnostic_box(context, L['diag_rect'])

        # Import/Export are drawn as a fused 2-item row — first item
        # keeps only its left corners rounded, last item only its right
        # corners, so the inner edges merge into a 1-px divider line.
        # Import/Export — middle row of the fused IO stack (diag box
        # above, Auto TXD below). Import is the first item and keeps
        # its BL corner rounded; everything else flat so the inner
        # edges merge cleanly.
        n_menus = len(L['menus'])
        open_mid = (st.open_dropdown or {}).get('menu_id')
        for i, (rect, label, prefix, mid) in enumerate(L['menus']):
            cm = GS.CORNER_BL if i == 0 else GS.CORNER_NONE
            WG._draw_menu_button(rect, label, prefix,
                              hovered=(st.hover_menu == i),
                              corner_mask=cm,
                              active=(open_mid == mid))
        for i, (rect, label, op_id, _) in enumerate(L['buttons']):
            WG._draw_button(rect, label,
                         hovered=(st.hover_button == i))
        for i, t in enumerate(L['toggles']):
            try:
                on = bool(getattr(t['owner'], t['prop']))
            except Exception:
                on = False
            hovered = (st.hover_toggle == i)
            WG._draw_toggle(t['rect'], t['label'], on, hovered)

        # DXT backend dropdown — shows the current enum label and opens
        # a value-list dropdown on click.
        try:
            dxt_val = context.scene.inu_settings.gtatools_dxt_backend
        except Exception:
            dxt_val = 'numpy'
        dxt_label = _dxt_backend_label(dxt_val)
        WG._draw_value_dropdown(L['dxt_rect'], dxt_label,
                             hovered=(st.hover_menu == 'dxt'),
                             active=(open_mid == '__dxt_backend__'),
                             corner_mask=GS.CORNER_NONE)

        # Pipeline row — geometry already computed in extend_body_layout.
        try:
            pipeline_val = context.scene.inu_settings.gtatools_export_pipeline
        except Exception:
            pipeline_val = 'NONE'
        hov = st.hover_enum
        hi = hov[1] if (hov and hov[0] == 'pipeline') else None
        # Pipeline row — "Нет" keeps TL+BL rounded, "Ped" keeps only
        # BR (top-right flat). Middle items stay flat throughout.
        WG._draw_enum_row(L['pipeline_rect'], _IE_PIPELINE, pipeline_val, hi,
                          outer_corner_mask=GS.CORNER_LEFT | GS.CORNER_BR)

        # Collapsible sections.
        for sec in L['sections']:
            sid = sec['id']
            hdr_rect = sec['header_rect']
            label = ("Суффиксы / Префиксы" if sid == 'suffix'
                     else "DFF Flags")
            WG._draw_collapsible_header(
                hdr_rect, label, sec['expanded'],
                hovered=(st.hover_collapsible == sid))
            if sec['expanded'] and sec['body_rect']:
                bx, by, bw, bh = sec['body_rect']
                if sid == 'suffix':
                    # Placeholder until text-input widget exists.
                    note = "Редактирование через N-панель"
                    nw, nh = TA._text_dims(note)
                    TA._text(int(bx + (bw - nw) / 2),
                          int(by + (bh - nh) / 2),
                          note, TH._C_DIM)
                elif sid == 'dff_flags':
                    # Render flag toggles inside a `layout.box()`-style
                    # surround so the section matches the equivalent
                    # N-panel rendering (panels.py wraps DFF Flags in
                    # `box = layout.box()` then adds the toggles
                    # inside).
                    WG._draw_box(sec['body_rect'])
                    for j, ft in enumerate(sec.get('flag_toggles', [])):
                        try:
                            on = bool(getattr(ft['owner'], ft['prop']))
                        except Exception:
                            on = False
                        hovered = (st.hover_toggle == ('dff_flag', j))
                        WG._draw_toggle(ft['rect'], ft['label'], on, hovered,
                                        alert=ft.get('alert', False))

        # Dropdown panel (drawn LAST so it overlays everything else)
        self._draw_open_dropdown(context, L)

    def handle_body_mousemove(self, context, L, mx, my):
        st = self.state
        was_btn = st.hover_button
        was_tog = st.hover_toggle
        was_enum = st.hover_enum
        was_col = st.hover_collapsible
        was_menu = st.hover_menu
        was_dd_item = st.hover_dropdown_item

        # If a dropdown is open, only the dropdown gets hover updates —
        # the rest of the body sits underneath it and shouldn't react.
        if st.open_dropdown is not None:
            st.hover_dropdown_item = None
            for kind, idx, r in L.get('dropdown_items', []):
                if kind == 'item' and r is not None and B._hit(mx, my, *r):
                    st.hover_dropdown_item = idx
                    break
            return was_dd_item != st.hover_dropdown_item

        st.hover_menu = None
        for i, (rect, _, _, _) in enumerate(L['menus']):
            if B._hit(mx, my, *rect):
                st.hover_menu = i
                break
        # DXT backend dropdown uses the same hover_menu slot but tags
        # itself with a string sentinel so the dispatch can tell it
        # apart from numeric menu indices.
        if st.hover_menu is None and B._hit(mx, my, *L['dxt_rect']):
            st.hover_menu = 'dxt'

        st.hover_button = None
        for i, (rect, _, _, _) in enumerate(L['buttons']):
            if B._hit(mx, my, *rect):
                st.hover_button = i
                break

        st.hover_toggle = None
        for i, t in enumerate(L['toggles']):
            if B._hit(mx, my, *t['rect']):
                st.hover_toggle = i
                break

        st.hover_enum = None
        for i, r in enumerate(L.get('pipeline_item_rects', [])):
            if B._hit(mx, my, *r):
                st.hover_enum = ('pipeline', i)
                break

        st.hover_collapsible = None
        for sec in L['sections']:
            if B._hit(mx, my, *sec['header_rect']):
                st.hover_collapsible = sec['id']
                break
            if sec['expanded'] and sec['id'] == 'dff_flags':
                for j, ft in enumerate(sec.get('flag_toggles', [])):
                    if B._hit(mx, my, *ft['rect']):
                        st.hover_toggle = ('dff_flag', j)
                        break

        return (was_btn != st.hover_button
                or was_tog != st.hover_toggle
                or was_enum != st.hover_enum
                or was_col != st.hover_collapsible
                or was_menu != st.hover_menu
                or was_dd_item != st.hover_dropdown_item)

    def handle_body_press(self, context, L, mx, my):
        st = self.state

        # If a dropdown is open: clicks inside fire the item action,
        # clicks anywhere else just close it. Either way the click is
        # consumed by us so it doesn't trigger anything underneath.
        if st.open_dropdown is not None:
            menu_id = st.open_dropdown['menu_id']
            items = _IE_DROPDOWN_ITEMS.get(menu_id, [])
            prop_name = _IE_PROP_DROPDOWN_BINDINGS.get(menu_id)
            for kind, idx, r in L.get('dropdown_items', []):
                if kind != 'item' or r is None:
                    continue
                if B._hit(mx, my, *r):
                    entry = items[idx]
                    label = entry[0]
                    data = entry[1]
                    if prop_name:
                        # Enum-style dropdown: write the chosen value
                        # onto the bound scene_settings property.
                        try:
                            setattr(context.scene.inu_settings,
                                    prop_name, data)
                            B._push_undo(f"INU: set {prop_name} = {data}")
                        except Exception as e:
                            print(f"[INU Floater] prop set failed: {e}")
                    elif data:
                        B._invoke_operator(data, {})
                    break
            st.open_dropdown = None
            st.hover_dropdown_item = None
            return True

        # Open our in-floater dropdown directly below the clicked menu
        # button. No native popup — items rendered by _draw_open_dropdown,
        # clicks routed back through this same handler on the next press.
        for rect, label, _prefix, menu_id in L['menus']:
            if not B._hit(mx, my, *rect):
                continue
            st.open_dropdown = {'menu_id': menu_id, 'anchor_rect': rect}
            st.hover_dropdown_item = None
            return True

        # DXT backend dropdown — same anchor-rect machinery, but the
        # items will be interpreted as enum values via
        # _IE_PROP_DROPDOWN_BINDINGS instead of as operator idnames.
        if B._hit(mx, my, *L['dxt_rect']):
            st.open_dropdown = {
                'menu_id': '__dxt_backend__',
                'anchor_rect': L['dxt_rect'],
            }
            st.hover_dropdown_item = None
            return True

        # Pipeline enum-row first (specific hit-target above the generic
        # action buttons so we don't double-handle clicks).
        for i, r in enumerate(L.get('pipeline_item_rects', [])):
            if B._hit(mx, my, *r):
                try:
                    context.scene.inu_settings.gtatools_export_pipeline = \
                        _IE_PIPELINE[i][0]
                    B._push_undo(f"INU: pipeline → {_IE_PIPELINE[i][1]}")
                except Exception as e:
                    print(f"[INU Floater] pipeline set failed: {e}")
                return True

        # Collapsible section headers — clicking toggles the
        # corresponding scene prop.
        for sec in L['sections']:
            if not B._hit(mx, my, *sec['header_rect']):
                continue
            ss = context.scene.inu_settings
            try:
                if sec['id'] == 'suffix':
                    ss.gtatools_show_suffix_settings = \
                        not ss.gtatools_show_suffix_settings
                elif sec['id'] == 'dff_flags':
                    ss.gtatools_show_dff_flags = \
                        not ss.gtatools_show_dff_flags
            except Exception as e:
                print(f"[INU Floater] collapsible toggle failed: {e}")
            return True

        # DFF Flag toggles (when expanded).
        for sec in L['sections']:
            if sec['id'] != 'dff_flags' or not sec['expanded']:
                continue
            for ft in sec.get('flag_toggles', []):
                if B._hit(mx, my, *ft['rect']):
                    try:
                        setattr(ft['owner'], ft['prop'],
                                not bool(getattr(ft['owner'], ft['prop'])))
                        B._push_undo(f"INU: toggle {ft['label']}")
                    except Exception as e:
                        print(f"[INU Floater] flag toggle failed: {e}")
                    return True

        # Action buttons (e.g. "Проверить сцену" at the bottom).
        for rect, label, op_id, op_kw in L['buttons']:
            if not B._hit(mx, my, *rect):
                continue
            B._invoke_operator(op_id, op_kw)
            return True
        return False
