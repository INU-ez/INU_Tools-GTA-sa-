# INU_tools.ops.floater.iii
#
# IdeIplImgFloater — mirror of GTATOOLS_PT_ide_ipl_panel (panels.py).
# Three boxed sections stacked vertically:
#   * IDE box  — Add / Del / Import / Export
#   * IPL box  — Add / Del / Import / Export
#                + full-width "Секции IPL" Import/Export row
#                + full-width "Заменить Empty" row
#   * IMG box  — three independent toggles (Skip LOD / TXD / COL)
#                bound to scene.inu_settings props, then full-width
#                Import / Export / Remove from IMG ops.

import bpy

from ...ui import layout_rules as LR
from . import theme as TH
from . import gpu_shaders as GS
from . import text_atlas as TA
from . import widgets as WG
from . import base as B


# Padding between the section box's outline and its inner content.
# Asymmetric: top is tight (header читается ближе к верхней рамке),
# bottom + sides шире — даёт «дышать» нижнему ряду кнопок и не
# даёт текстам прилипать к боковым граням.
_BOX_PAD_TOP = 1
_BOX_PAD_BOT = 5
_BOX_PAD_X   = 5

# Adjacent buttons inside a fused cluster overlap by 1 px so their
# outlines merge into a single shared 1-px divider line — same trick
# native `row.prop_enum` uses, encapsulated in `WG._enum_row_rects`.
_FUSED_OVERLAP = 1


class IdeIplImgFloater(B.Floater):
    """N-panel IDE/IPL/IMG mirror — full action surface for working
    with existing GTA-SA files."""

    def __init__(self):
        super().__init__(
            name='iii',
            title='IDE / IPL / IMG',
            prop_names={
                'visible':   'inu_floater_iii_visible',
                'collapsed': 'inu_floater_iii_collapsed',
                'locked':    'inu_floater_iii_locked',
                'workspace': 'inu_floater_iii_workspace',
                'x':         'inu_floater_iii_x',
                'y':         'inu_floater_iii_y',
            },
            default_pos=(640, 400),
            # Wider than the 220 default — IDE+IPL columns need ~140-150 px
            # each so the icon+label buttons don't crowd the box edges,
            # and the IMG box's "Импорт из IMG" / "Экспорт в IMG" /
            # "Удалить из IMG" labels have room to breathe.
            width=310,
        )
        self.title_icon = 'file_folder'

    # ── Heights ─────────────────────────────────────────────────────

    def _ide_ipl_box_h(self):
        # 3 inner rows: header + Add/Del + Import/Export. Header is
        # separated by `_BTN_GAP` from the action cluster; the 2-row
        # action cluster itself uses 1-px vertical overlap.
        return (3 * TH._BUTTON_H
                + WG._BTN_GAP                        # header → row1
                + (-_FUSED_OVERLAP)                  # row1 ↔ row2 overlap
                + _BOX_PAD_TOP + _BOX_PAD_BOT)

    def _img_box_h(self):
        # 4 inner rows: header, 3-toggle row, Import+Export pair, Remove.
        # Internal rows fused via overlap (4 rows = 3 overlaps of 1 px).
        return (4 * TH._BUTTON_H - 3 * _FUSED_OVERLAP
                + _BOX_PAD_TOP + _BOX_PAD_BOT)

    def compute_body_height(self, context):
        # Outer blocks (IDE/IPL pair, Секции IPL, Заменить Empty, IMG)
        # фузятся overlap'ом тоже — единый вертикальный кластер без
        # 18-px gap'ов.
        return (
            self._ide_ipl_box_h()
            - _FUSED_OVERLAP + TH._BUTTON_H   # "Секции IPL" row
            - _FUSED_OVERLAP + TH._BUTTON_H   # "Заменить Empty" row
            - _FUSED_OVERLAP + self._img_box_h()
        )

    # ── Layout ──────────────────────────────────────────────────────

    def extend_body_layout(self, context, L):
        x, w = L['x'], L['w']
        top_y = L['body_top_y']
        inner_x = x + TH._PAD
        inner_w = w - 2 * TH._PAD

        # ── Side-by-side IDE | IPL boxes ──
        # Боксы прижаты друг к другу через 1-px overlap, как fused
        # button pair: правый край IDE и левый край IPL рисуют одну и ту же
        # пиксельную линию → визуально это единый бокс с 1-px разделителем
        # посередине, без двойной обводки.
        ide_ipl_h = self._ide_ipl_box_h()
        ide_ipl_y = top_y - ide_ipl_h
        col_gap = -_FUSED_OVERLAP
        col_w = (inner_w - col_gap) // 2
        L['ide_box_rect'] = (inner_x, ide_ipl_y, col_w, ide_ipl_h)
        L['ipl_box_rect'] = (inner_x + col_w + col_gap, ide_ipl_y, col_w, ide_ipl_h)

        # Each box: header row at top (separate), then a 2×2 fused
        # action cluster (Add/Del on top, Import/Export below).
        # Inside the cluster every adjacent pair overlaps by 1 px so
        # outlines fuse into single dividers. Corner masks (set in
        # draw_body) round only the cluster's 4 outer corners.
        def _layout_box_rows(box_rect):
            bx, by, bw, bh = box_rect
            ix = bx + _BOX_PAD_X
            iw = bw - 2 * _BOX_PAD_X
            header_y = by + bh - _BOX_PAD_TOP - TH._BUTTON_H
            # Header → row1: regular gap (independent groups visually).
            row1_y = header_y - WG._BTN_GAP - TH._BUTTON_H
            # row1 ↔ row2: 1-px vertical overlap so the two action rows
            # read as one fused 2×2 cluster.
            row2_y = row1_y - TH._BUTTON_H + _FUSED_OVERLAP
            r1_l, r1_r = WG._enum_row_rects((ix, row1_y, iw, TH._BUTTON_H), 2)
            r2_l, r2_r = WG._enum_row_rects((ix, row2_y, iw, TH._BUTTON_H), 2)
            return {
                'header': (ix, header_y, iw, TH._BUTTON_H),
                'r1_l': r1_l, 'r1_r': r1_r,
                'r2_l': r2_l, 'r2_r': r2_r,
            }

        ide_r = _layout_box_rows(L['ide_box_rect'])
        L['ide_header_rect'] = ide_r['header']
        L['ide_add_rect']    = ide_r['r1_l']
        L['ide_del_rect']    = ide_r['r1_r']
        L['ide_import_rect'] = ide_r['r2_l']
        L['ide_export_rect'] = ide_r['r2_r']

        ipl_r = _layout_box_rows(L['ipl_box_rect'])
        L['ipl_header_rect'] = ipl_r['header']
        L['ipl_add_rect']    = ipl_r['r1_l']
        L['ipl_del_rect']    = ipl_r['r1_r']
        L['ipl_import_rect'] = ipl_r['r2_l']
        L['ipl_export_rect'] = ipl_r['r2_r']

        # ── Full-width "Секции IPL" Import / Export — fused pair ──
        # Прилегает к IDE/IPL коробкам через 1-px overlap (вместо
        # 18-px gap), формируя единый кластер до самого низа панели.
        sec_y = ide_ipl_y + _FUSED_OVERLAP - TH._BUTTON_H
        L['sec_import_rect'], L['sec_export_rect'] = WG._enum_row_rects(
            (inner_x, sec_y, inner_w, TH._BUTTON_H), 2)

        # ── Full-width "Заменить Empty" row ──
        rep_y = sec_y + _FUSED_OVERLAP - TH._BUTTON_H
        L['replace_empty_rect'] = (inner_x, rep_y, inner_w, TH._BUTTON_H)

        # ── IMG box ── также fused с предыдущими.
        img_h = self._img_box_h()
        img_y = rep_y + _FUSED_OVERLAP - img_h
        L['img_box_rect'] = (inner_x, img_y, inner_w, img_h)
        ix = inner_x + _BOX_PAD_X
        iw = inner_w - 2 * _BOX_PAD_X

        img_header_y = img_y + img_h - _BOX_PAD_TOP - TH._BUTTON_H
        # Header → toggle row, toggle → Import, Import → Export,
        # Export → Remove — все через 1-px overlap, без 18-px gap.
        toggle_y = img_header_y + _FUSED_OVERLAP - TH._BUTTON_H
        L['img_header_rect'] = (ix, img_header_y, iw, TH._BUTTON_H)

        # 3-toggle row — fused via `_enum_row_rects`.
        (L['skip_lod_rect'],
         L['txd_rect'],
         L['col_rect']) = WG._enum_row_rects(
            (ix, toggle_y, iw, TH._BUTTON_H), 3)

        # Import + Export — fused pair в одной строке (раньше шли
        # столбиком), затем Remove — full-width под ними.
        imp_exp_y = toggle_y + _FUSED_OVERLAP - TH._BUTTON_H
        L['img_import_rect'], L['img_export_rect'] = WG._enum_row_rects(
            (ix, imp_exp_y, iw, TH._BUTTON_H), 2)
        rem_y = imp_exp_y + _FUSED_OVERLAP - TH._BUTTON_H
        L['img_remove_rect'] = (ix, rem_y, iw, TH._BUTTON_H)

    # ── Draw ────────────────────────────────────────────────────────

    def _draw_section_header(self, rect, label, icon_name):
        """Section header inside a `_draw_box`: icon at left edge, label
        next to it. Same `_C_TEXT` colour as the action buttons below —
        раньше использовался dim `_C_LABEL`, из-за чего текст читался
        как «неактивный»."""
        x, y, w, h = rect
        icon_size = LR.icon_size()
        icon_x = x + 4
        icon_y = y + (h - icon_size) // 2
        GS._draw_icon((icon_x, icon_y, icon_size, icon_size),
                      icon_name, tint=TH._C_TEXT)
        tw, th = TA._text_dims(label)
        tx = icon_x + icon_size + 4
        ty = y + (h - th) // 2
        TA._text(int(tx), int(ty), label, TH._C_TEXT)

    def draw_body(self, context, L):
        st = self.state
        h = st.hover_button

        # ── IDE box ──
        # Force-English labels mirror the N-panel (panels.py uses
        # `translate=False` for these): "Add"/"Del"/"Import"/"Export"
        # are universally readable, and the localised forms
        # ("Добавить"/"Импорт"/"Экспорт") expand wide enough to overflow
        # the narrow side-by-side columns.
        #
        # The 4 action buttons form a fused 2×2 cluster — only the
        # outer 4 corners (TL on add, TR on del, BL on import, BR on
        # export) are rounded; the rest = CORNER_NONE so the inner
        # cross divider is a single 1-px line.
        # IDE box — слева вверху общего fused-блока: TL свободен,
        # TR прилегает к IPL через 1-px overlap, BL/BR прилегают к
        # Секции IPL ниже.
        WG._draw_box(L['ide_box_rect'], corner_mask=GS.CORNER_TL)
        self._draw_section_header(L['ide_header_rect'], "IDE", 'text')
        WG._draw_button(L['ide_add_rect'], "Add",
                        hovered=(h == 'ide_add'), icon='add',
                        translate=False, corner_mask=GS.CORNER_TL)
        WG._draw_button(L['ide_del_rect'], "Del",
                        hovered=(h == 'ide_del'), icon='remove',
                        translate=False, corner_mask=GS.CORNER_TR)
        WG._draw_button(L['ide_import_rect'], "Import",
                        hovered=(h == 'ide_import'), icon='import',
                        translate=False, corner_mask=GS.CORNER_BL)
        WG._draw_button(L['ide_export_rect'], "Export",
                        hovered=(h == 'ide_export'), icon='export',
                        translate=False, corner_mask=GS.CORNER_BR)

        # IPL box — справа вверху: TR свободен, TL прилегает к IDE,
        # BL/BR прилегают к Секции IPL ниже.
        WG._draw_box(L['ipl_box_rect'], corner_mask=GS.CORNER_TR)
        self._draw_section_header(L['ipl_header_rect'], "IPL", 'empty_axis')
        WG._draw_button(L['ipl_add_rect'], "Add",
                        hovered=(h == 'ipl_add'), icon='add',
                        translate=False, corner_mask=GS.CORNER_TL)
        WG._draw_button(L['ipl_del_rect'], "Del",
                        hovered=(h == 'ipl_del'), icon='remove',
                        translate=False, corner_mask=GS.CORNER_TR)
        WG._draw_button(L['ipl_import_rect'], "Import",
                        hovered=(h == 'ipl_import'), icon='import',
                        translate=False, corner_mask=GS.CORNER_BL)
        WG._draw_button(L['ipl_export_rect'], "Export",
                        hovered=(h == 'ipl_export'), icon='export',
                        translate=False, corner_mask=GS.CORNER_BR)

        # Секции IPL pair и Заменить Empty — все сидят в едином fused
        # столбце между IDE/IPL коробками сверху и IMG коробкой снизу.
        # Никакая сторона свободной не остаётся, поэтому CORNER_NONE
        # на всех — никаких лишних скруглений рядом с соседями.
        WG._draw_button(L['sec_import_rect'], "Секции IPL",
                        hovered=(h == 'sec_import'), icon='import',
                        corner_mask=GS.CORNER_NONE)
        WG._draw_button(L['sec_export_rect'], "Секции IPL",
                        hovered=(h == 'sec_export'), icon='export',
                        corner_mask=GS.CORNER_NONE)
        WG._draw_button(L['replace_empty_rect'], "Заменить Empty",
                        hovered=(h == 'replace_empty'), icon='mesh_data',
                        corner_mask=GS.CORNER_NONE)

        # ── IMG box ── TL/TR прилегают к "Заменить Empty" через overlap,
        # поэтому скругляем только BL/BR.
        WG._draw_box(L['img_box_rect'], corner_mask=GS.CORNER_BOTTOM)
        self._draw_section_header(L['img_header_rect'], "IMG", 'package')

        settings = context.scene.inu_settings
        skip_lod = bool(getattr(settings, 'gtatools_img_skip_lod', False))
        load_txd = bool(getattr(settings, 'gtatools_img_load_txd', False))
        load_col = bool(getattr(settings, 'gtatools_map_load_col', False))
        # 3-toggle row: TL/TR свободны у крайних (под ними нет кнопок,
        # сверху только header-label без рамки), BL/BR прилегают к
        # Import/Export ряду ниже.
        WG._draw_button(L['skip_lod_rect'], "Skip LOD",
                        hovered=(h == 'skip_lod'), pressed=skip_lod,
                        corner_mask=GS.CORNER_TL)
        WG._draw_button(L['txd_rect'], "TXD",
                        hovered=(h == 'txd'), pressed=load_txd,
                        corner_mask=GS.CORNER_NONE)
        WG._draw_button(L['col_rect'], "COL",
                        hovered=(h == 'col'), pressed=load_col,
                        corner_mask=GS.CORNER_TR)

        # Import/Export — зажаты между toggle row сверху и Remove снизу,
        # все 4 угла прилегают к соседям → CORNER_NONE.
        WG._draw_button(L['img_import_rect'], "Импорт из IMG",
                        hovered=(h == 'img_import'), icon='import',
                        corner_mask=GS.CORNER_NONE)
        WG._draw_button(L['img_export_rect'], "Экспорт в IMG",
                        hovered=(h == 'img_export'), icon='export',
                        corner_mask=GS.CORNER_NONE)
        # Remove — нижняя кнопка кластера: TL/TR прилегают к Import/Export,
        # BL/BR оставляем скруглёнными (внутренний нижний край IMG-бокса).
        WG._draw_button(L['img_remove_rect'], "Удалить из IMG",
                        hovered=(h == 'img_remove'), icon='remove',
                        corner_mask=GS.CORNER_BOTTOM)

    # ── Events ──────────────────────────────────────────────────────

    _HOVER_TARGETS = [
        ('ide_add',       'ide_add_rect'),
        ('ide_del',       'ide_del_rect'),
        ('ide_import',    'ide_import_rect'),
        ('ide_export',    'ide_export_rect'),
        ('ipl_add',       'ipl_add_rect'),
        ('ipl_del',       'ipl_del_rect'),
        ('ipl_import',    'ipl_import_rect'),
        ('ipl_export',    'ipl_export_rect'),
        ('sec_import',    'sec_import_rect'),
        ('sec_export',    'sec_export_rect'),
        ('replace_empty', 'replace_empty_rect'),
        ('skip_lod',      'skip_lod_rect'),
        ('txd',           'txd_rect'),
        ('col',           'col_rect'),
        ('img_import',    'img_import_rect'),
        ('img_export',    'img_export_rect'),
        ('img_remove',    'img_remove_rect'),
    ]

    def handle_body_mousemove(self, context, L, mx, my):
        st = self.state
        was = st.hover_button
        st.hover_button = None
        for key, rect_name in self._HOVER_TARGETS:
            r = L.get(rect_name)
            if r and B._hit(mx, my, *r):
                st.hover_button = key
                break
        return was != st.hover_button

    # Click targets that just fire an operator with no kwargs. Keys
    # match `_HOVER_TARGETS` so the same key drives hover + press, and
    # the toggle targets below override the three IMG-filter keys.
    _BUTTON_OPS = {
        'ide_add':       "gtatools.upsert_ide",
        'ide_del':       "gtatools.remove_ide",
        'ide_import':    "gtatools.import_ide",
        'ide_export':    "gtatools.export_ide",
        'ipl_add':       "gtatools.upsert_ipl",
        'ipl_del':       "gtatools.remove_ipl",
        'ipl_import':    "gtatools.import_ipl",
        'ipl_export':    "gtatools.export_ipl",
        'sec_import':    "gtatools.import_ipl_sections",
        'sec_export':    "gtatools.export_ipl_sections",
        'replace_empty': "gtatools.replace_ipl_placeholders",
        'img_import':    "gtatools.import_from_img",
        'img_export':    "gtatools.export_to_img",
        'img_remove':    "gtatools.remove_from_img",
    }

    _TOGGLE_PROPS = {
        'skip_lod': 'gtatools_img_skip_lod',
        'txd':      'gtatools_img_load_txd',
        'col':      'gtatools_map_load_col',
    }

    def handle_body_press(self, context, L, mx, my):
        # Toggle props first — they share the rect-name pattern with
        # operator buttons but need a different action.
        for key, prop_name in self._TOGGLE_PROPS.items():
            r = L.get(f'{key}_rect')
            if r and B._hit(mx, my, *r):
                try:
                    settings = context.scene.inu_settings
                    cur = bool(getattr(settings, prop_name, False))
                    setattr(settings, prop_name, not cur)
                    B._push_undo(f"INU: {prop_name} → {not cur}")
                except Exception as e:
                    print(f"[INU Floater] toggle {prop_name} failed: {e}")
                return True

        # Operator buttons.
        for key, op_id in self._BUTTON_OPS.items():
            r = L.get(f'{key}_rect')
            if r and B._hit(mx, my, *r):
                B._invoke_operator(op_id, {})
                return True

        return False
