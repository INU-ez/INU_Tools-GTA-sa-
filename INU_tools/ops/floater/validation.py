# INU_tools.ops.floater.validation
#
# ValidationFloater — pre-export sanity check: walks selected objects,
# reports vertex/triangle/material counts against the format hard limits,
# flags geometry that would crash the GTA-SA engine before the user
# wastes time on the actual export.

import bpy

from . import theme as TH
from . import gpu_shaders as GS
from . import text_atlas as TA
from . import widgets as WG
from . import base as B


# ── ValidationFloater: «Проверка перед экспортом» ────────────────────


class ValidationFloater(B.Floater):
    """Replica of GTATOOLS_PT_check_panel: geometry checks + transform
    helpers + DFF/LOD/COL/SHA visibility toggles + link overlay + batch
    type assignment. Buttons invoke the same operators the native panel
    uses — we own layout/rendering only."""

    def __init__(self):
        super().__init__(
            name='val',
            title='Проверка',
            prop_names={
                'visible':   'inu_floater_val_visible',
                'collapsed': 'inu_floater_val_collapsed',
                'locked':    'inu_floater_val_locked',
                'workspace': 'inu_floater_val_workspace',
                'x':         'inu_floater_val_x',
                'y':         'inu_floater_val_y',
            },
            default_pos=(640, 200),
            # Wider than the 220 px default — "Проверка вершин" and
            # "LOD/COL → DFF" labels need the room, otherwise they
            # truncate to "Проверка вер…" inside the buttons.
            width=270,
        )
        self.title_icon = 'checkmark'

    # 6 rows of widgets, stacked as one fused vertical cluster
    # (mirrors `layout.column(align=True)` in the N-panel — adjacent
    # rows share a 1-px edge, no `_BTN_GAP` separators between rows):
    #   1. check_geometry  | check_ngons     (2-col)        — TL+TR
    #   2. reset_transform                   (1-col)        — interior
    #   3. snap_to_dff                       (1-col)        — interior
    #   4. DFF | LOD | COL | SHA toggles     (4-col)        — interior
    #   5. toggle_links                      (1-col)        — interior
    #   6. Тип:  OBJ | COL | SHA | NON       (label + 4 btns) — BL+BR
    _ROWS = 6
    # 1-px vertical overlap between adjacent rows so their outlines
    # fuse into a single shared horizontal divider.
    _FUSED_OVERLAP = 1

    def compute_body_height(self, context):
        # 6 rows tall minus 5 overlaps (one per adjacent pair). The bottom
        # result strip is added by the Floater base class for every window.
        return self._ROWS * TH._BUTTON_H - (self._ROWS - 1) * self._FUSED_OVERLAP

    def _vis_states(self):
        try:
            from .. import object_utils_ops as _u
            return {
                'DFF': bool(_u._hide_dff),
                'LOD': bool(_u._hide_lod),
                'COL': bool(_u._hide_col),
                'SHA': bool(_u._hide_sha),
            }
        except Exception:
            return {'DFF': False, 'LOD': False, 'COL': False, 'SHA': False}

    def _links_state(self):
        try:
            from .. import map_ops as _m
            return bool(_m._links_active)
        except Exception:
            return False

    def extend_body_layout(self, context, L):
        x, w = L['x'], L['w']
        top_y = L['body_top_y']

        def row_y(i):
            # Row i sits `i` row-heights below top, with `i` overlap-px
            # added back (each preceding row "eats" 1 px from the next).
            return (top_y - (i + 1) * TH._BUTTON_H
                    + i * self._FUSED_OVERLAP)

        # Row 0 — Geometry checks: fused pair (both validate geometry).
        r0y = row_y(0)
        L['geo_check_rect'], L['geo_ngon_rect'] = WG._enum_row_rects(
            (x + TH._PAD, r0y, w - 2 * TH._PAD, TH._BUTTON_H), 2)

        # Row 1 — Reset transform (independent full-width)
        L['reset_rect'] = (x + TH._PAD, row_y(1), w - 2 * TH._PAD, TH._BUTTON_H)

        # Row 2 — LOD/COL → DFF (independent full-width)
        L['snap_rect'] = (x + TH._PAD, row_y(2), w - 2 * TH._PAD, TH._BUTTON_H)

        # Row 3 — Visibility toggles: fused 4-button cluster. All four
        # flags (DFF/LOD/COL/SHA) are independent multi-select toggles
        # but share the "what's visible" context → one widget.
        r3y = row_y(3)
        vis_kinds = ('DFF', 'LOD', 'COL', 'SHA')
        vis_rects = WG._enum_row_rects(
            (x + TH._PAD, r3y, w - 2 * TH._PAD, TH._BUTTON_H), 4)
        L['vis_rects'] = list(zip(vis_kinds, vis_rects))

        # Row 4 — Links toggle (independent full-width)
        L['links_rect'] = (x + TH._PAD, row_y(4), w - 2 * TH._PAD, TH._BUTTON_H)

        # Row 5 — Type label + 4 type buttons (exclusive selection →
        # fused enum-row; label sits left of the cluster as standalone).
        r5y = row_y(5)
        label_w = 40
        type_strip_x = x + TH._PAD + label_w + WG._BTN_GAP
        type_strip_w = w - 2 * TH._PAD - label_w - WG._BTN_GAP
        type_kinds = ('OBJ', 'COL', 'SHA', 'NON')
        type_rects_only = WG._enum_row_rects(
            (type_strip_x, r5y, type_strip_w, TH._BUTTON_H), 4)
        L['type_label_rect'] = (x + TH._PAD, r5y, label_w, TH._BUTTON_H)
        L['type_rects'] = list(zip(type_kinds, type_rects_only))

    def draw_body(self, context, L):
        st = self.state
        h = st.hover_button

        # All 6 rows form one fused vertical cluster — corner masks
        # only round the 4 outer corners of the whole panel:
        #   Row 0 (top-row): geo_check=TL, geo_ngon=TR
        #   Row 4 (links, full width): bottom-LEFT is at cluster's
        #     bottom-left (label area below it is text-only, no
        #     button) → CORNER_BL. Right side fuses with NON below.
        #   Row 5 (type 4-cluster): OBJ=BL (bottom-left of cluster),
        #     NON=BR. Note "Тип:" label is text and doesn't widen
        #     the cluster — OBJ's left edge IS the perimeter here.

        # Row 0 — geometry fused pair (top of the whole stack).
        WG._draw_button(L['geo_check_rect'], "Проверка вершин",
                     hovered=(h == 'geo_check'),
                     icon='viewzoom',
                     corner_mask=GS.CORNER_TL)
        WG._draw_button(L['geo_ngon_rect'], "Проверка N-gon",
                     hovered=(h == 'geo_ngon'),
                     icon='mesh_data',
                     corner_mask=GS.CORNER_TR)

        # Rows 1-2 — interior of the vertical fusion.
        WG._draw_button(L['reset_rect'], "Сброс трансформ",
                     hovered=(h == 'reset'),
                     icon='empty_axis',
                     corner_mask=GS.CORNER_NONE)
        WG._draw_button(L['snap_rect'], "LOD/COL → DFF",
                     hovered=(h == 'snap'),
                     icon='snap_on',
                     corner_mask=GS.CORNER_NONE)

        # Row 3 — Visibility 4-cluster, all interior (top fuses snap,
        # bottom fuses links).
        vis = self._vis_states()
        for kind, rect in L['vis_rects']:
            WG._draw_button(rect, kind,
                         hovered=(h == ('vis', kind)),
                         pressed=vis[kind],
                         icon='hide_on' if vis[kind] else 'hide_off',
                         corner_mask=GS.CORNER_NONE)

        # Row 4 — links toggle, full width. Bottom-LEFT meets the
        # label area in row 5 below (text only, no button) → that
        # corner is cluster perimeter and rounds. Bottom-right meets
        # NON button → interior, sharp.
        links_on = self._links_state()
        WG._draw_button(L['links_rect'],
                     "Связи: ON" if links_on else "Связи: OFF",
                     hovered=(h == 'links'),
                     pressed=links_on,
                     icon='linked',
                     corner_mask=GS.CORNER_BL)

        # Row 5 — Тип: label + 4 type buttons.
        tlx, tly, _tlw, tlh = L['type_label_rect']
        _, lh = TA._text_dims("Тип:")
        TA._text(int(tlx), int(tly + (tlh - lh) // 2), "Тип:", TH._C_LABEL)
        n_type = len(L['type_rects'])
        for i, (kind, rect) in enumerate(L['type_rects']):
            if i == 0:
                cm = GS.CORNER_BL                  # bottom-left of cluster
            elif i == n_type - 1:
                cm = GS.CORNER_BR                  # bottom-right of cluster
            else:
                cm = GS.CORNER_NONE
            WG._draw_button(rect, kind,
                         hovered=(h == ('type', kind)),
                         corner_mask=cm)

    def handle_body_mousemove(self, context, L, mx, my):
        st = self.state
        was = st.hover_button
        st.hover_button = None
        for key, rect in (
            ('geo_check', L['geo_check_rect']),
            ('geo_ngon',  L['geo_ngon_rect']),
            ('reset',     L['reset_rect']),
            ('snap',      L['snap_rect']),
            ('links',     L['links_rect']),
        ):
            if B._hit(mx, my, *rect):
                st.hover_button = key
                break
        if st.hover_button is None:
            for kind, rect in L['vis_rects']:
                if B._hit(mx, my, *rect):
                    st.hover_button = ('vis', kind)
                    break
        if st.hover_button is None:
            for kind, rect in L['type_rects']:
                if B._hit(mx, my, *rect):
                    st.hover_button = ('type', kind)
                    break
        return was != st.hover_button

    def handle_body_press(self, context, L, mx, my):
        if B._hit(mx, my, *L['geo_check_rect']):
            B._invoke_operator("gtatools.check_geometry", {})
            return True
        if B._hit(mx, my, *L['geo_ngon_rect']):
            B._invoke_operator("gtatools.check_ngons", {})
            return True
        if B._hit(mx, my, *L['reset_rect']):
            B._invoke_operator("gtatools.reset_transform", {})
            return True
        if B._hit(mx, my, *L['snap_rect']):
            B._invoke_operator("gtatools.snap_to_dff", {})
            return True
        for kind, rect in L['vis_rects']:
            if B._hit(mx, my, *rect):
                B._invoke_operator("gtatools.toggle_visibility",
                                 {"model_type": kind})
                return True
        if B._hit(mx, my, *L['links_rect']):
            B._invoke_operator("gtatools.toggle_links", {})
            return True
        for kind, rect in L['type_rects']:
            if B._hit(mx, my, *rect):
                B._invoke_operator("gtatools.batch_set_type",
                                 {"obj_type": kind})
                return True
        return False
