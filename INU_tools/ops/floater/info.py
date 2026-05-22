# INU_tools.ops.floater.info
#
# InfoFloater — active-object readout: mesh vert/face/material counts
# with format-limit thresholds, IDE flag checkboxes, DFF/LOD/COL triplet
# jump buttons. Visibility helpers reveal hidden related models when
# the user clicks a triplet button.

import bpy

from ...ui import layout_rules as LR
from . import theme as TH
from . import gpu_shaders as GS
from . import text_atlas as TA
from . import widgets as WG
from . import base as B


# Format-limit thresholds (mirror file_lint.py).
_LIM_VERT_SOFT = 32000
_LIM_VERT_HARD = 65535
_LIM_TRI_SOFT  = 30000
_LIM_MAT_SOFT  = 100

_SEV_COLOR = {
    'normal': TH._C_TEXT,
    'warn':   TH._C_WARN,
    'error':  TH._C_ERROR,
}

# Button widget visuals — inter-button gap; height/colors/shade in theme.py

# IDE flags exposed in InfoFloater (mirror INUObjectProps.flag_*).
_IDE_FLAGS = [
    ('flag_is_road',      'IS_ROAD'),
    ('flag_draw_last',    'DRAW_LAST'),
    ('flag_additive',     'ADDITIVE'),
    ('flag_no_zbuffer',   'NO_ZBUFFER'),
    ('flag_no_shadows',   'NO_SHADOWS'),
    ('flag_no_backface',  'NO_BACKFACE'),
    ('flag_damagable',    'DAMAGABLE'),
    ('flag_breakable',    'BREAKABLE'),
    ('flag_is_tree',      'IS_TREE'),
    ('flag_is_palm',      'IS_PALM'),
    ('flag_glass_1',      'GLASS_1'),
    ('flag_glass_2',      'GLASS_2'),
    ('flag_garage_door',  'GARAGE_DOOR'),
    ('flag_no_flyer_col', 'NO_FLYER_COL'),
    ('flag_is_tag',       'IS_TAG'),
]
_TRIPLET_LABEL = {'DFF': 'DFF', 'LOD': 'LOD', 'COL': 'COL'}


# ── Visibility helpers (used by InfoFloater triplet jump) ────────────

def _is_visible(obj):
    if obj is None:
        return False
    try:
        return obj.visible_get()
    except Exception:
        return True


def _unhide_layer_collection_recursive(layer_coll, target_coll_name):
    if layer_coll.collection.name == target_coll_name:
        layer_coll.hide_viewport = False
        layer_coll.exclude = False
        return True
    for child in layer_coll.children:
        if _unhide_layer_collection_recursive(child, target_coll_name):
            layer_coll.hide_viewport = False
            layer_coll.exclude = False
            return True
    return False


def _reveal(obj, context):
    if obj is None:
        return
    try:
        obj.hide_set(False)
        obj.hide_viewport = False
    except Exception:
        pass
    root = context.view_layer.layer_collection
    for coll in obj.users_collection:
        try:
            _unhide_layer_collection_recursive(root, coll.name)
        except Exception:
            pass


def _find_related_models(obj):
    empty = {'DFF': None, 'LOD': None, 'COL': None}
    if obj is None:
        return None, empty
    try:
        from ...tools.model_utils import get_model_type, find_related_models
        self_type, base_name = get_model_type(obj)
        if not base_name:
            return self_type, empty
        return self_type, find_related_models(base_name)
    except Exception as e:
        print(f"[INU Floater] related lookup failed: {e}")
        return None, empty


# ── InfoFloater: active object info + IDE flags ──────────────────────

def _gather_object_info(obj):
    if obj is None:
        return [("(no active object)", "", 'normal')]

    rows = [
        ("Name", obj.name, 'normal'),
        ("Blender type", obj.type, 'normal'),
    ]

    inu = getattr(obj, 'inu', None)
    if inu is not None:
        rows.append(("INU type", inu.type, 'normal'))
        if inu.type == '2DFX':
            rows.append(("2DFX effect", inu.effect_2dfx, 'normal'))
        mid = inu.model_id
        rows.append(("Model ID", str(mid), 'warn' if mid == 0 else 'normal'))
        rows.append(("TXD", inu.txd_name or "—",
                     'normal' if inu.txd_name else 'warn'))

        show_triplet = (obj.type == 'MESH' and inu.type in ('OBJ', 'COL', 'SHA'))
        if show_triplet:
            self_type, related = _find_related_models(obj)
            for kind in ('DFF', 'LOD', 'COL'):
                if kind == self_type:
                    continue
                label = _TRIPLET_LABEL[kind]

                target_obj = None
                value = "—"
                if kind == 'LOD' and inu.lod_object is not None:
                    target_obj = inu.lod_object
                    value = inu.lod_object.name
                else:
                    partner = related.get(kind)
                    if partner is not None and partner is not obj:
                        target_obj = partner
                        value = partner.name
                    elif kind == 'COL' and inu.col_name:
                        value = inu.col_name

                rows.append((label, value, 'normal', target_obj))

    if obj.type == 'MESH' and obj.data is not None:
        m = obj.data
        nv = len(m.vertices)
        npoly = len(m.polygons)
        nmat = len(m.materials)
        if nv >= _LIM_VERT_HARD:
            v_sev = 'error'
        elif nv >= _LIM_VERT_SOFT or npoly >= _LIM_TRI_SOFT:
            v_sev = 'warn'
        else:
            v_sev = 'normal'
        rows.append(("Verts / Polys", f"{nv} / {npoly}", v_sev))
        m_sev = 'warn' if nmat >= _LIM_MAT_SOFT else 'normal'
        rows.append(("Materials", str(nmat), m_sev))
    elif obj.type == 'ARMATURE' and obj.data is not None:
        rows.append(("Bones", str(len(obj.data.bones)), 'normal'))

    return rows


def _flags_applicable(obj):
    if obj is None or obj.type != 'MESH':
        return False
    inu = getattr(obj, 'inu', None)
    if inu is None or not hasattr(inu, 'flag_is_road'):
        return False
    return getattr(inu, 'type', 'OBJ') == 'OBJ'


class InfoFloater(B.Floater):
    """Active object info: identity, TXD, triplet jump."""

    def __init__(self):
        super().__init__(
            name='info',
            title='INU Floater',
            prop_names={
                'visible':   'inu_floater_visible',
                'collapsed': 'inu_floater_collapsed',
                'locked':    'inu_floater_locked',
                'workspace': 'inu_floater_workspace',
                'x':         'inu_floater_x',
                'y':         'inu_floater_y',
            },
            default_pos=(40, 200),
            # Wider than the 220 default — info rows can carry long
            # object names like "ugrium_str_40_1DFF" that wrap or
            # clip at the standard width.
            width=230,
        )
        self.title_icon = 'info'

    # Layout — info rows live inside one `layout.box()`-style
    # container, mirroring the selection-summary box in IE floater
    # (panels.py:686 `box = layout.box()`). Row stride uses the
    # native widget_unit so rows line up pixel-for-pixel with the
    # N-panel `col.label(...)` rendering.

    _BOX_PAD = 6  # internal padding inside the info box

    def compute_body_height(self, context):
        rows = _gather_object_info(context.active_object)
        n = len(rows)
        if n <= 0:
            return 0
        return LR.box_height(n, row_h=TH._BUTTON_H,
                             row_gap=LR.inter_row_gap(),
                             pad=self._BOX_PAD)

    def extend_body_layout(self, context, L):
        obj = context.active_object
        info_rows = _gather_object_info(obj)
        L['info_rows'] = info_rows

        # Single boxed container covering the whole body width.
        box_x = L['x'] + TH._PAD
        box_w = L['w'] - 2 * TH._PAD
        box_h = self.compute_body_height(context)
        box_y = L['body_top_y'] - box_h
        L['info_box_rect'] = (box_x, box_y, box_w, box_h)

        # Row stride matches IE diag box: widget_unit + inter-row gap.
        row_h = TH._BUTTON_H
        row_gap = LR.inter_row_gap()
        L['info_row_h'] = row_h
        L['info_row_gap'] = row_gap

        # Top of the FIRST row sits just under the box top-padding.
        first_row_top = box_y + box_h - self._BOX_PAD

        # Clickable triplet rows (LOD / COL "jump-to" targets) —
        # rebuilt against the new row layout so hit-tests stay
        # aligned with what's drawn.
        triplet_rects = []
        for i, row in enumerate(info_rows):
            target = row[3] if len(row) > 3 else None
            if target is None:
                continue
            row_top = first_row_top - i * (row_h + row_gap)
            row_bottom = row_top - row_h
            rect = (box_x + 2, row_bottom, box_w - 4, row_h)
            triplet_rects.append((target, rect))
        L['triplet_rects'] = triplet_rects
        L['info_first_row_top'] = first_row_top

    # Drawing

    def draw_body(self, context, L):
        st = self.state
        rows = L['info_rows']
        if not rows:
            return

        # The container itself — same chrome IE uses for its
        # selection diagnostic box.
        WG._draw_box(L['info_box_rect'])

        box_x, _box_y, box_w, _box_h = L['info_box_rect']
        first_row_top = L['info_first_row_top']
        row_h = L['info_row_h']
        row_gap = L['info_row_gap']

        label_x = box_x + 8
        value_x = box_x + 8 + B._LABEL_COL_W

        for i, row in enumerate(rows):
            label, value = row[0], row[1]
            sev = row[2] if len(row) > 2 else 'normal'
            target = row[3] if len(row) > 3 else None
            row_top = first_row_top - i * (row_h + row_gap)
            row_bottom = row_top - row_h

            # Hover highlight (rounded so it matches the dropdown
            # item style — `TH._C_BUTTON_SEL` lit fill, white text).
            is_hovered = (target is not None
                          and st.hover_triplet is target)
            if is_hovered:
                GS._draw_rect_rounded(
                    box_x + 2, row_bottom, box_w - 4, row_h,
                    TH._C_BUTTON_SEL,
                    max(1, int(round(TH._R_BUTTON)) - 1))

            label_color = TH._C_TEXT_SEL if is_hovered else TH._C_LABEL
            value_color = (TH._C_TEXT_SEL if is_hovered
                           else _SEV_COLOR.get(sev, TH._C_TEXT))

            # Both texts vertically centred inside the row's
            # widget_unit slot.
            _, lh = TA._text_dims(label, 11)
            text_y = row_bottom + (row_h - lh) // 2
            TA._text(label_x, text_y, label, label_color, 11)
            TA._text(value_x, text_y, str(value), value_color, 11)

    # Events

    def handle_body_mousemove(self, context, L, mx, my):
        st = self.state
        was_triplet = st.hover_triplet

        st.hover_triplet = None
        for target, rect in L['triplet_rects']:
            if B._hit(mx, my, *rect):
                st.hover_triplet = target
                break

        return was_triplet is not st.hover_triplet

    def handle_body_press(self, context, L, mx, my):
        # Click on a triplet row jumps the viewport selection to that
        # object (DFF/LOD/COL of the same base name). All other triplet
        # siblings get auto-hidden so the meshes don't overlap visually;
        # their original visibility is captured and restored on the
        # NEXT jump so the user's manual state is preserved between
        # hops.
        for target, rect in L['triplet_rects']:
            if not B._hit(mx, my, *rect):
                continue
            st = self.state

            # Restore visibility changes from the previous jump first.
            prev_changes = getattr(st, 'auto_changes', None)
            if prev_changes:
                for obj, was_hidden in prev_changes.items():
                    try:
                        if obj is not None:
                            obj.hide_set(was_hidden)
                    except Exception:
                        pass
                st.auto_changes = None

            # Collect siblings (DFF / LOD / COL for the target's
            # base_name) — including the target itself.
            try:
                from ...tools.model_utils import (
                    find_related_models, get_model_type,
                )
                _self_type, base_name = get_model_type(target)
                siblings = (find_related_models(base_name)
                            if base_name else {})
            except Exception:
                siblings = {}

            changes = {}
            for kind in ('DFF', 'LOD', 'COL'):
                obj = siblings.get(kind)
                if obj is None:
                    continue
                try:
                    was_hidden = not _is_visible(obj)
                except Exception:
                    was_hidden = False
                if obj is target:
                    if was_hidden:
                        try:
                            _reveal(obj, context)
                        except Exception:
                            pass
                        changes[obj] = True
                else:
                    if not was_hidden:
                        try:
                            obj.hide_set(True)
                        except Exception:
                            pass
                        changes[obj] = False
            st.auto_changes = changes if changes else None

            try:
                for o in context.view_layer.objects:
                    o.select_set(False)
                target.select_set(True)
                context.view_layer.objects.active = target
            except Exception as e:
                print(f"[INU Floater] jump failed: {e}")
            B._tag_redraw_view3d(context)
            return True
        return False
