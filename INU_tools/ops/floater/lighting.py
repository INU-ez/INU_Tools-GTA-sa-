# INU_tools.ops.floater.lighting
#
# LightingFloater — replica of GTATOOLS_PT_prelight_panel: prelight
# preset picker (with dynamic dropdown), 8-lamps toggle, Day/Night
# vertex-colour controls, bake + copy + LightMap shortcuts. Talks to
# the existing prelight operators rather than reimplementing logic.

import bpy

from . import theme as TH
from . import gpu_shaders as GS
from . import text_atlas as TA
from . import widgets as WG
from . import base as B
from . import layout_solver as LS
from ...ui import layout_rules as LR


def _panel_margin_x():
    # `UI_PANEL_MARGIN_X = U.widget_unit * 0.4` — ≈ 8 px @ scale 1.0.
    return max(2, int(round(LR.widget_unit() * 0.4)))


# ── Prelight-preset dropdown ──────────────────────────────────────────
#
# Preset names are dynamic: they come from .json files in the
# addon's presets folder and are exposed via the
# `gtatools_prelight_preset` EnumProperty's `items=` callback. We
# can't hardcode them like the IE-side dropdown items, so this
# helper rebuilds the list on every open. The result follows the
# same shape the IE-side menu expects — list of (label, value) —
# so we can pipe it through the existing `WG._dropdown_layout` helper.
_PRELIGHT_PRESET_MENU_ID = '__prelight_preset__'


_HEADER_SENTINEL = '__HEADER__'


def _get_prelight_preset_dropdown_items(context):
    """Return [(label, preset_id), ...] for the prelight preset
    dropdown. Calls the addon's own `_get_preset_items` helper —
    the same one the EnumProperty's dynamic `items=` callback uses —
    so we always see the live list of `.json` presets on disk.

    `prop.enum_items` on a callback-driven Enum returns an empty /
    stale collection in many Blender builds (the callback is only
    invoked when the UI renders the prop, not on direct RNA access).
    Going through `_get_preset_items` directly avoids that quirk.

    The first entry is a non-clickable header «Prelight Preset» —
    matches the title row Blender's native enum dropdown shows at
    the top of `prop(..., 'prop_enum')` popups. Detected by the
    `_HEADER_SENTINEL` value so click / hover handlers can skip it."""
    try:
        from ... import _get_preset_items
        raw = _get_preset_items(context.scene.inu_settings, context)
        items = [("Prelight Preset", _HEADER_SENTINEL, None)]
        items.extend((name or ident, ident, None)
                      for (ident, name, *_rest) in raw)
        return items
    except Exception as e:
        print(f"[INU Floater] preset items fetch failed: {e}")
        return []


class LightingFloater(B.Floater):
    """Replica of GTATOOLS_PT_prelight_panel: preset row + 8-lamps
    toggle + Day/Night vertex-colour controls + bake row + Copy row +
    LightMap row. All actions invoke their existing operators."""

    def __init__(self):
        super().__init__(
            name='light',
            title='Освещение',
            prop_names={
                'visible':   'inu_floater_light_visible',
                'collapsed': 'inu_floater_light_collapsed',
                'locked':    'inu_floater_light_locked',
                'workspace': 'inu_floater_light_workspace',
                'x':         'inu_floater_light_x',
                'y':         'inu_floater_light_y',
            },
            default_pos=(340, 400),
            # User's N-panel measures ~312 px wide (Apply 116 + dropdown
            # 115 + 4×18 icons = 303 + paddings = 312). UI_SIDEBAR_PANEL
            # _WIDTH default is 280 but he's resized his N-panel.
            # Match his measurement so widget widths line up.
            # Чуть шире N-панели по просьбе — длинным подписям («Запечь
            # поверх с тенями») просторнее.
            width=360,
        )
        # Header icon — matches the COLOR icon Blender's N-panel uses
        # for the Prelight sub-panel header (panels.py:2556).
        self.title_icon = 'color'

    # Fixed-width icon button (rename / +/- / export) in the preset row.
    _ICON_BTN_W = 22

    # ── State probes ───────────────────────────────────────────────

    def _lights_on(self):
        coll = bpy.data.collections.get("Prelight_Lights")
        return bool(coll and len(coll.objects) > 0)

    def _preview_on(self, obj):
        # Reads the explicit `prelight_preview_active` flag instead
        # of detecting `Prelight_Mix` node existence — the node now
        # survives toggles (we keep it to avoid pop-in lag) so it's
        # not a reliable on/off signal.
        if obj is None or obj.type != 'MESH':
            return False
        for ms in obj.material_slots:
            m = ms.material
            if m and m.get('prelight_preview_active', False):
                return True
        return False

    def _vcol_active_name(self, obj):
        if obj is None or obj.type != 'MESH':
            return None
        try:
            from ...tools import compat as _c
            a = _c.vcol_active(obj.data)
            return a.name if a is not None else None
        except Exception:
            return None

    def _has_vcol(self, obj, name):
        if obj is None or obj.type != 'MESH':
            return False
        try:
            from ...tools import compat as _c
            return _c.vcol_get(obj.data, name) is not None
        except Exception:
            return False

    @staticmethod
    def _is_nonstd_mesh(obj):
        """Активный объект — MESH, но его data НЕ обычный bpy.types.Mesh
        (например 'FastMesh' от Plumber / Source-импорта). Почти весь
        прилайт читает геометрию через bmesh / polygons и на таком меше не
        работает — пользователю нужно сделать Object → Convert → Mesh."""
        if obj is None or getattr(obj, 'type', None) != 'MESH':
            return False
        if obj.data is None:
            return False
        try:
            return not isinstance(obj.data, bpy.types.Mesh)
        except Exception:
            return False

    def _lm_state(self, obj):
        if obj is None or obj.type != 'MESH':
            return (False, False)   # (exists, on)
        exists = False
        on = False
        for ms in obj.material_slots:
            m = ms.material
            if m and m.use_nodes:
                node = m.node_tree.nodes.get("LM_Mix")
                if node is not None:
                    exists = True
                    if not node.mute:
                        on = True
                    break
        return (exists, on)

    def _preset_label(self, context):
        try:
            return str(context.scene.inu_settings.gtatools_prelight_preset)
        except Exception:
            return "—"

    # ── Layout ─────────────────────────────────────────────────────

    def _build_layout(self, context):
        """Declarative layout tree — mirrors what `bpy.types.UILayout`
        receives in `panels.py:GTATOOLS_PT_prelight_panel.draw()` so
        the layout traversal lands on the exact same widget positions
        as the native N-panel.

        Top-level `root` corresponds to the panel's implicit `layout`
        (Blender default `column(align=False)` — children get
        UI_DEFAULT_SPACING_Y gap between them). All the prelight rows
        live in the nested `preset_col` (align=True) so they fuse into
        one cluster."""
        root = LS.Column(align=False)
        preset_col = root.column(align=True)

        # 1. Preset row — Apply | Name | ✏ | + | − | ↑
        preset_row = preset_col.row(align=True)
        preset_row.operator('preset_apply', text='Применить',
                            icon='checkmark')
        preset_row.prop('preset_name',
                        text=self._preset_label(context))
        for op_id, icon in (('preset_rename', 'greasepencil'),
                            ('preset_save',   'add'),
                            ('preset_delete', 'remove'),
                            ('preset_export', 'export')):
            preset_row.operator(op_id, icon=icon,
                                width=self._ICON_BTN_W)

        # 2. Lights toggle + Солнце — две full-width кнопки.
        preset_col.operator('lights', text='Свет (8 ламп)', icon='light')
        preset_col.operator('sun', text='Солнце', icon='light_sun')

        # `if obj and obj.type == 'MESH':` from panels.py:2613.
        # Without an active mesh the N-panel skips the box, Day/Night,
        # bake, copy and lm rows entirely (operators have nothing to
        # work on); only preset row + lights are visible.
        obj = context.active_object
        if obj is not None and obj.type == 'MESH':
            self._build_mesh_rows(preset_col)
        # Предупреждение внизу: активный объект — не обычный меш Blender
        # (FastMesh от Plumber / Source-импорт). Функции прилайта читают
        # геометрию через bmesh / polygons и на нём не работают.
        if self._is_nonstd_mesh(obj):
            warn_col = preset_col.column(align=True)
            warn_col.label('fastmesh_warn1', scale_y=0.9)
            warn_col.label('fastmesh_warn2', scale_y=0.9)
        return root

    def _build_mesh_rows(self, preset_col):
        """Mesh-only widgets — Day/Night box, bake, copy, LightMap row.
        Mirrors the body of the `if obj.type == 'MESH'` block in
        panels.py:2613-2751."""
        # 3. Day/Night box — preview tall column + 2×3 Day/Night grid.
        # Mirrors panels.py:2636-2694 exactly:
        #   box = preset_col.box()
        #   body = box.row(align=True)
        #   preview_col = body.column(align=True); ui_units_x=1.4 (=28 px); scale_y=2
        #   box_col = body.column(align=True)
        #     for Day, Night:
        #       row = box_col.split(factor=0.6, align=True)
        #       left = row.row(align=True)              # 60 % — name+radiobut
        #       right_part = row.split(factor=0.85, align=True)
        #         v_cell = right_part.row(align=True)   # 85 % of 40 % = 34 %
        #         btn_cell = right_part.row(align=True) # 15 % of 40 % =  6 %
        UI_UNIT_X = LR.widget_unit_x()       # = 20 @ scale 1.0
        # Box + кнопка альфы в одном align-столбце → они вплотную (1px),
        # при этом кнопка остаётся обычным элементом (получает rect и
        # рисуется — внутрь самого box её класть нельзя).
        dn_col = preset_col.column(align=True)
        box = dn_col.box(box_id='daynight_box')
        body = box.row(align=True)
        preview = body.column(align=True)
        preview.scale_y = 2.0
        preview.width = int(round(1.4 * UI_UNIT_X))   # ui_units_x = 1.4 → 28 px
        preview.operator('preview', icon='hide_off')
        grid = body.column(align=True)
        for kind in ('day', 'night'):
            # `split(factor=0.6, align=True)` — outer split, left 60 %, right 40 %
            split_row = grid.row(align=True)
            left = split_row.row(align=True)
            left.scale_x = 0.6
            left.operator(f'{kind}_name', text=kind.capitalize())
            # `right_part.split(factor=0.85, align=True)` — inner split
            right_part = split_row.row(align=True)
            right_part.scale_x = 0.4
            v_cell = right_part.row(align=True)
            v_cell.scale_x = 0.85
            v_cell.prop(f'{kind}_v', text='V  0.00')
            # Fixed-width +/- icon cell at 20 px rect (user-tuned —
            # earlier 18 looked 2 px too narrow in the rendered floater).
            btn_cell = right_part.row(align=True)
            btn_cell.width = 20
            btn_cell.operator(f'{kind}_remove', icon='remove')

        # Альфа вершины (сцена) — в том же align-столбце, в упор под
        # боксом Day/Night (1px).
        dn_col.operator('alpha_scene', text='Альфа вершины (сцена)',
                        icon='hide_on')

        # 4. Запечь поверх / с тенями (additive, over=True) — СВЕРХУ: свет
        # кладётся ПОВЕРХ текущего прилайта, не перезаписывая.
        bake_over_row = preset_col.row(align=True)
        bake_over_row.operator('bake_over', text='Запечь поверх', icon='add')
        bake_over_row.operator('bake_over_shadow',
                               text='Запечь поверх с тенями', icon='add')

        # 4b. Запечь / с тенями (перезапись) — СНИЗУ и ВЫШЕ по высоте
        # (как в N-панели, scale_y=1.6 — основные кнопки крупнее).
        bake_row = preset_col.row(align=True)
        bake_row.scale_y = 1.6
        bake_row.operator('bake', text='Запечь', icon='render_still')
        bake_row.operator('bake_shadow', text='Запечь с тенями',
                          icon='render_result')

        # 5. Copy Day↔Night — fused pair
        copy_row = preset_col.row(align=True)
        copy_row.operator('copy_dn', text='Day → Night')
        copy_row.operator('copy_nd', text='Night → Day')

        # 6. LightMap row — eye toggle + main button + remove. Fused
        # via `align=True` to match the N-panel: panels.py builds this
        # as `row = preset_col.row(align=True)` with the eye / add /
        # remove operators butting up against each other. The eye is
        # an operator when LM exists, a label-icon when it doesn't —
        # draw_body picks between the two visual modes.
        lm_row = preset_col.row(align=True)
        lm_row.operator('lm_toggle', icon='hide_off',
                        width=self._ICON_BTN_W)
        lm_row.operator('lm_add', text='Добавить LightMap')
        lm_row.operator('lm_remove', icon='remove',
                        width=self._ICON_BTN_W)

    def _layout_for_pass(self, context, body_w):
        """Build the layout tree + total height ONCE per compute_layout
        pass. Both compute_body_height and extend_body_layout need them;
        without this the tree-build (and its per-material-slot state
        probes) ran twice every frame — the bulk of this window's
        per-frame cost. Cache is keyed by the base's `_layout_pass` token
        (bumped once per compute_layout) + body width."""
        tok = getattr(self, '_layout_pass', 0)
        cache = getattr(self, '_lt_cache', None)
        if cache is not None and cache[0] == tok and cache[1] == body_w:
            return cache[2], cache[3]
        root = self._build_layout(context)
        total_h = LS.total_height(root, body_w)
        self._lt_cache = (tok, body_w, root, total_h)
        return root, total_h

    def compute_body_height(self, context):
        # Body width = panel width (`self.width`) minus 2 × UI_PANEL_MARGIN_X.
        body_w = max(1, self.width - 2 * _panel_margin_x())
        _root, total_h = self._layout_for_pass(context, body_w)
        return total_h

    def extend_body_layout(self, context, L):
        x, w = L['x'], L['w']
        top_y = L['body_top_y']
        side_pad = _panel_margin_x()

        # Build the declarative layout tree once, then ask the solver
        # to resolve every widget's rect — same `(x, y, w, h)` tuples
        # we used to hand-compute. Layout traversal walks the tree
        # using Blender-native metrics from `layout_rules.py` so the
        # output should line up with the N-panel pixel-for-pixel.
        body_w = w - 2 * side_pad
        root, body_h = self._layout_for_pass(context, body_w)
        body_rect = (x + side_pad, top_y - body_h, body_w, body_h)
        solved = LS.solve(root, body_rect)

        # Bridge solver IDs → existing `*_rect` keys so draw_body and
        # event handlers don't need rewriting. The keys are exactly
        # the operator/prop IDs from `_build_layout`.
        for widget_id, (rect, _leaf) in solved.items():
            L[f'{widget_id}_rect'] = rect
        # The Day/Night box widget is the Box wrapper, not a Leaf —
        # its outer rect lives under its `box_id` directly (no
        # `_rect` suffix on the legacy key).
        if 'daynight_box' in solved:
            L['daynight_box'] = solved['daynight_box'][0]

        # If a dropdown is currently open under `preset_name_rect`,
        # compute its panel + per-item rects so the click handler and
        # the draw pass see the same geometry. Mirrors IE pattern at
        # `extend_body_layout` (line ~3490).
        dropdown_rect = None
        dropdown_items = []
        if (self.state.open_dropdown is not None
                and self.state.open_dropdown.get('menu_id')
                == _PRELIGHT_PRESET_MENU_ID):
            ditems = _get_prelight_preset_dropdown_items(context)
            if ditems:
                dropdown_rect, dropdown_items = WG._dropdown_layout(
                    self.state.open_dropdown['anchor_rect'], ditems)
        L['dropdown_rect'] = dropdown_rect
        L['dropdown_items'] = dropdown_items
        # Tell `_draw_dropdown_panel` which item is currently selected
        # so it can paint that row with the blue accent (matching the
        # N-panel's `prop_enum(..., expand=True)` "active" highlight).
        try:
            L['dropdown_current_value'] = str(
                context.scene.inu_settings.gtatools_prelight_preset)
        except Exception:
            L['dropdown_current_value'] = None

    # ── Draw ───────────────────────────────────────────────────────

    def draw_body(self, context, L):
        st = self.state
        h = st.hover_button
        obj = context.active_object
        active_vcol = self._vcol_active_name(obj)

        # Preset row — fused 6-button cluster. Only the outermost
        # corners (apply's left, export's right) get rounded; everything
        # in between is CORNER_NONE so outlines fuse into shared 1-px
        # divider lines. The name dropdown's auto CORNER_TOP / CORNER_ALL
        # behaviour is overridden via the explicit `corner_mask=` param.
        WG._draw_button(L['preset_apply_rect'], "Применить",
                     hovered=(h == 'preset_apply'),
                     icon='checkmark',
                     corner_mask=GS.CORNER_TL)
        dd_open = (self.state.open_dropdown or {}).get('menu_id')
        WG._draw_value_dropdown(L['preset_name_rect'],
                             self._preset_label(context),
                             hovered=(h == 'preset_name'),
                             active=(dd_open == _PRELIGHT_PRESET_MENU_ID),
                             corner_mask=GS.CORNER_NONE)
        WG._draw_button(L['preset_rename_rect'], "",
                     hovered=(h == 'preset_rename'),
                     icon='greasepencil',
                     corner_mask=GS.CORNER_NONE)
        WG._draw_button(L['preset_save_rect'], "",
                     hovered=(h == 'preset_save'),
                     icon='add',
                     corner_mask=GS.CORNER_NONE)
        WG._draw_button(L['preset_delete_rect'], "",
                     hovered=(h == 'preset_delete'),
                     icon='remove',
                     corner_mask=GS.CORNER_NONE)
        WG._draw_button(L['preset_export_rect'], "",
                     hovered=(h == 'preset_export'),
                     icon='export',
                     corner_mask=GS.CORNER_TR)

        # Lights toggle — both edges touch siblings in the fused stack
        # (preset row above, daynight box below), so all corners sharp.
        lights_on = self._lights_on()
        WG._draw_button(L['lights_rect'], "Свет (8 ламп)",
                     hovered=(h == 'lights'), pressed=lights_on,
                     icon='light',
                     corner_mask=GS.CORNER_NONE)
        if 'sun_rect' in L:
            sun_on = bpy.data.objects.get("Prelight_Sun") is not None
            WG._draw_button(L['sun_rect'], "Солнце",
                         hovered=(h == 'sun'), pressed=sun_on,
                         icon='light_sun',
                         corner_mask=GS.CORNER_NONE)

        # Day/Night cluster sits inside a `layout.box()`-style frame —
        # matches the N-panel's Prelight section (panels.py:2628 `box =
        # preset_col.box()`). Box drawn first so the buttons paint over
        # the inner edge of the frame. All corners sharp — the box is
        # fused into the surrounding stack (lights above, bake below).
        if 'daynight_box' in L:
            WG._draw_box(L['daynight_box'], corner_mask=GS.CORNER_NONE)
        if 'preview_rect' in L:
            preview_on = self._preview_on(obj)
            WG._draw_button(L['preview_rect'], "",
                         hovered=(h == 'preview'), pressed=preview_on,
                         icon='hide_off' if preview_on else 'hide_on',
                         corner_mask=GS.CORNER_LEFT)

        for kind in ('day', 'night'):
            if f'{kind}_name_rect' not in L:
                continue
            name_rect = L[f'{kind}_name_rect']
            v_rect    = L[f'{kind}_v_rect']
            rm_rect   = L[f'{kind}_remove_rect']
            label_name = "Day" if kind == 'day' else "Night"
            has = self._has_vcol(obj, label_name)
            active = (active_vcol == label_name)

            # Radiobutton-style icon left of the label — matches N-panel
            # (panels.py:2666 `safe_icon('RADIOBUT_ON' if is_active else
            # 'RADIOBUT_OFF')`). `RADIOBUT_ON` = active vcol selected,
            # `RADIOBUT_OFF` = exists but inactive. When the attr does
            # NOT exist on the mesh, the button + V slot render greyed
            # out (mirrors N-panel `left.enabled = False` + `v_sub.
            # enabled = False`); the + button on the right stays
            # enabled so the user can create the attr.
            radio_icon = 'radiobut_on' if (has and active) else 'radiobut_off'
            WG._draw_button(name_rect, label_name,
                         hovered=(h == f'{kind}_name'),
                         pressed=(has and active),
                         icon=radio_icon,
                         disabled=not has,
                         corner_mask=GS.CORNER_NONE)

            # V offset — always show. Drawn dimmed when the vcol layer
            # doesn't exist yet (matches the native panel's
            # `v_sub.enabled = False` placeholder). When the field is
            # being edited inline, render the buffer + caret instead
            # of the live value and switch the bg to the selected
            # accent so it reads like a focused text input.
            v_val = 0.0
            try:
                v_val = float(getattr(
                    obj, f'gtatools_v_offset_{kind}', 0.0))
            except Exception:
                pass
            vx, vy, vw, vh = v_rect
            ef = self.state.edit_field
            is_editing = (ef is not None and ef.get('rect') == v_rect)
            if is_editing:
                # Inline text-edit state — accent-coloured fill + caret.
                # Keep manual rendering here because `_draw_button`
                # doesn't expose a "focused input" style.
                GS._draw_rect_rounded(vx, vy, vw, vh,
                                   TH._C_BUTTON_SEL,
                                   max(2, int(round(TH._R_BUTTON))))
                vtxt = self.state.edit_buffer + '|'
                tw, th = TA._text_dims(vtxt)
                TA._text(int(vx + (vw - tw) / 2),
                      int(vy + (vh - th) / 2), vtxt, TH._C_TEXT_SEL)
            else:
                # Regular button look — matches the N-panel's `V` slot.
                # All inner cluster cells use CORNER_NONE so adjacent
                # buttons share sharp edges. Greyed out when no attr
                # exists (matches `v_sub.enabled = False` in N-panel).
                # `prop(obj, _v_prop, text="V")` from panels.py:2670 —
                # Blender renders the prop with `precision=2` (the
                # FloatProperty default, since the property doesn't
                # set `precision=N`). Layout writes `V` label then the
                # value with that precision.
                WG._draw_button(v_rect, f"V {v_val:.2f}",
                             hovered=(h == f'{kind}_v'),
                             translate=False,
                             disabled=not has,
                             corner_mask=GS.CORNER_NONE)

            # Right-edge button — Remove (−) when layer exists, Add (+)
            # otherwise. day_remove gets CORNER_TR (top-right of cluster),
            # night_remove gets CORNER_BR (bottom-right of cluster).
            rm_corner = GS.CORNER_TR if kind == 'day' else GS.CORNER_BR
            WG._draw_button(rm_rect, "",
                         hovered=(h == f'{kind}_remove'),
                         icon='remove' if has else 'add',
                         corner_mask=rm_corner)

        # Bake / Bake with shadows — fused pair in the vertical stack
        # (daynight box above, copy row below) so all corners sharp.
        if 'bake_rect' in L:
            WG._draw_button(L['bake_rect'], "Запечь",
                         hovered=(h == 'bake'),
                         icon='render_still',
                         corner_mask=GS.CORNER_NONE)
        if 'bake_shadow_rect' in L:
            WG._draw_button(L['bake_shadow_rect'], "Запечь с тенями",
                         hovered=(h == 'bake_shadow'),
                         icon='render_result',
                         corner_mask=GS.CORNER_NONE)

        # Альфа вершины (сцена) — pressed когда превью включено.
        if 'alpha_scene_rect' in L:
            alpha_on = bool(context.scene.get('inu_alpha_preview_on', False))
            WG._draw_button(L['alpha_scene_rect'], "Альфа вершины (сцена)",
                         hovered=(h == 'alpha_scene'), pressed=alpha_on,
                         icon='hide_off' if alpha_on else 'hide_on',
                         corner_mask=GS.CORNER_NONE)

        # Запечь поверх / с тенями (additive).
        if 'bake_over_rect' in L:
            WG._draw_button(L['bake_over_rect'], "Запечь поверх",
                         hovered=(h == 'bake_over'),
                         icon='add',
                         corner_mask=GS.CORNER_NONE)
        if 'bake_over_shadow_rect' in L:
            WG._draw_button(L['bake_over_shadow_rect'], "Запечь поверх с тенями",
                         hovered=(h == 'bake_over_shadow'),
                         icon='add',
                         corner_mask=GS.CORNER_NONE)

        # Copy Day↔Night — fused pair (bake row above, lm row below).
        if 'copy_dn_rect' in L:
            WG._draw_button(L['copy_dn_rect'], "Day → Night",
                         hovered=(h == 'copy_dn'),
                         corner_mask=GS.CORNER_NONE)
        if 'copy_nd_rect' in L:
            WG._draw_button(L['copy_nd_rect'], "Night → Day",
                         hovered=(h == 'copy_nd'),
                         corner_mask=GS.CORNER_NONE)

        # LightMap row — bottom of the fused preset_col cluster, so
        # each button rounds ONLY its perimeter corners:
        #   lm_toggle (leftmost): BL — top touches copy, right touches
        #     lm_add, bottom-left is cluster's outer corner
        #   lm_add (middle): NONE — all four sides touch siblings or
        #     the cluster boundary
        #   lm_remove (rightmost): BR — symmetric to lm_toggle on the
        #     right edge of the cluster
        #
        # When LM_Mix node exists → operator button with eye icon +
        # depress for the current toggle state. When it doesn't exist
        # → label (no button bg, just centred icon) so the row reads as
        # «LM не создан, ничего тогглить» — matches panels.py:2745-2749.
        if 'lm_toggle_rect' in L:
            lm_exists, lm_on = self._lm_state(obj)
            lm_toggle_rect = L['lm_toggle_rect']
            if lm_exists:
                WG._draw_button(lm_toggle_rect, "",
                             hovered=(h == 'lm_toggle'), pressed=lm_on,
                             icon='hide_off' if lm_on else 'hide_on',
                             corner_mask=GS.CORNER_BL)
            else:
                GS._draw_icon_centered(lm_toggle_rect, 'hide_on',
                                    size=int(round(16 * LR.effective_scale())),
                                    tint=TH._C_TEXT)
            WG._draw_button(L['lm_add_rect'], "Добавить LightMap",
                         hovered=(h == 'lm_add'),
                         corner_mask=GS.CORNER_NONE)
            WG._draw_button(L['lm_remove_rect'], "",
                         hovered=(h == 'lm_remove'),
                         icon='remove',
                         corner_mask=GS.CORNER_BR)

        # Предупреждение о не-обычном меше (FastMesh) — оранжевым внизу.
        for key, txt in (
                ('fastmesh_warn1_rect', "Объект — не обычный меш (FastMesh)"),
                ('fastmesh_warn2_rect', "Конвертируй: Object → Convert → Mesh")):
            r = L.get(key)
            if r:
                rx, ry, rw, rh = r
                _, th = TA._text_dims(txt)
                TA._text(int(rx), int(ry + (rh - th) / 2), txt, TH._C_WARN)

        # NOTE: the open dropdown is drawn by the base _draw_content AFTER
        # the status strip, so the strip can't paint over its lower rows.

    def _draw_open_dropdown(self, context, L):
        """Resolve the dynamic preset items list and delegate the
        actual panel rendering to `Floater._draw_dropdown_panel`."""
        dd = self.state.open_dropdown
        if dd is None or dd.get('menu_id') != _PRELIGHT_PRESET_MENU_ID:
            return
        items = _get_prelight_preset_dropdown_items(context)
        if items:
            self._draw_dropdown_panel(L, items)

    # ── Events ─────────────────────────────────────────────────────

    _HOVER_TARGETS = [
        ('preset_apply',   'preset_apply_rect'),
        ('preset_name',    'preset_name_rect'),
        ('preset_rename',  'preset_rename_rect'),
        ('preset_save',    'preset_save_rect'),
        ('preset_delete',  'preset_delete_rect'),
        ('preset_export',  'preset_export_rect'),
        ('lights',         'lights_rect'),
        ('sun',            'sun_rect'),
        ('alpha_scene',    'alpha_scene_rect'),
        ('bake_over',      'bake_over_rect'),
        ('bake_over_shadow', 'bake_over_shadow_rect'),
        ('preview',        'preview_rect'),
        ('day_name',       'day_name_rect'),
        ('day_v',          'day_v_rect'),
        ('day_remove',     'day_remove_rect'),
        ('night_name',     'night_name_rect'),
        ('night_v',        'night_v_rect'),
        ('night_remove',   'night_remove_rect'),
        ('bake',           'bake_rect'),
        ('bake_shadow',    'bake_shadow_rect'),
        ('copy_dn',        'copy_dn_rect'),
        ('copy_nd',        'copy_nd_rect'),
        ('lm_toggle',      'lm_toggle_rect'),
        ('lm_add',         'lm_add_rect'),
        ('lm_remove',      'lm_remove_rect'),
    ]

    def handle_body_mousemove(self, context, L, mx, my):
        st = self.state
        was = st.hover_button
        was_dd = st.hover_dropdown_item

        # If a dropdown is open, ONLY its items receive hover —
        # everything underneath is visually behind it.
        if (st.open_dropdown is not None
                and st.open_dropdown.get('menu_id')
                == _PRELIGHT_PRESET_MENU_ID):
            st.hover_dropdown_item = None
            items = _get_prelight_preset_dropdown_items(context)
            for kind, idx, r in L.get('dropdown_items', []):
                if kind != 'item' or r is None:
                    continue
                # Skip non-clickable header row.
                if 0 <= idx < len(items) and items[idx][1] == _HEADER_SENTINEL:
                    continue
                if B._hit(mx, my, *r):
                    st.hover_dropdown_item = idx
                    break
            return was_dd != st.hover_dropdown_item

        st.hover_button = None
        for key, rect_name in self._HOVER_TARGETS:
            r = L.get(rect_name)
            if r and B._hit(mx, my, *r):
                st.hover_button = key
                break
        return was != st.hover_button

    def handle_body_press(self, context, L, mx, my):
        st = self.state
        obj = context.active_object

        # If our preset dropdown is open, clicks inside fire the
        # item action, clicks elsewhere close it. Either way the
        # click is consumed so it can't hit the widgets behind.
        if (st.open_dropdown is not None
                and st.open_dropdown.get('menu_id')
                == _PRELIGHT_PRESET_MENU_ID):
            items = _get_prelight_preset_dropdown_items(context)
            for kind, idx, r in L.get('dropdown_items', []):
                if kind != 'item' or r is None:
                    continue
                if not B._hit(mx, my, *r):
                    continue
                entry = items[idx]
                val = entry[1]
                # Skip clicks on the non-interactive header row.
                if val == _HEADER_SENTINEL:
                    return True
                try:
                    context.scene.inu_settings.gtatools_prelight_preset = val
                except Exception as e:
                    print(f"[INU Floater] preset set failed: {e}")
                break
            st.open_dropdown = None
            st.hover_dropdown_item = None
            return True

        # Preset row
        if B._hit(mx, my, *L['preset_apply_rect']):
            B._invoke_operator("gtatools.prelight_preset_load", {})
            return True
        if B._hit(mx, my, *L['preset_name_rect']):
            # Open an inline dropdown anchored under the preset
            # name field — same pattern the IE floater uses for the
            # DXT backend dropdown. Items come from
            # `_get_prelight_preset_dropdown_items` (dynamic, reads
            # the live enum).
            st.open_dropdown = {
                'menu_id': _PRELIGHT_PRESET_MENU_ID,
                'anchor_rect': L['preset_name_rect'],
            }
            st.hover_dropdown_item = None
            return True
        if B._hit(mx, my, *L['preset_rename_rect']):
            B._invoke_operator("gtatools.prelight_preset_rename", {})
            return True
        if B._hit(mx, my, *L['preset_save_rect']):
            B._invoke_operator("gtatools.prelight_preset_save", {})
            return True
        if B._hit(mx, my, *L['preset_delete_rect']):
            B._invoke_operator("gtatools.prelight_preset_delete", {})
            return True
        if B._hit(mx, my, *L['preset_export_rect']):
            B._invoke_operator("gtatools.prelight_preset_apply", {})
            return True
        # Lights
        if B._hit(mx, my, *L['lights_rect']):
            B._invoke_operator("gtatools.toggle_prelight_lights", {})
            return True
        # Солнце — как и Свет, доступно без активного меша.
        if 'sun_rect' in L and B._hit(mx, my, *L['sun_rect']):
            B._invoke_operator("gtatools.toggle_prelight_sun", {})
            return True
        # Mesh-only widgets — absent when no active mesh.
        if 'preview_rect' not in L:
            return False
        # Preview toggle (enable kwarg flips the current state)
        if B._hit(mx, my, *L['preview_rect']):
            B._invoke_operator("gtatools.prelight_preview",
                             {"enable": not self._preview_on(obj)})
            return True
        # Day/Night rows
        for kind in ('day', 'night'):
            label_name = "Day" if kind == 'day' else "Night"
            if B._hit(mx, my, *L[f'{kind}_name_rect']):
                B._invoke_operator("gtatools.select_color_attribute",
                                 {"attribute_name": label_name})
                return True
            if B._hit(mx, my, *L[f'{kind}_v_rect']):
                # Start inline numeric edit — same pattern as N-panel
                # `layout.prop(...)`: click the value, type a number,
                # press Enter. Keyboard handler in the base class
                # captures keystrokes until commit/cancel.
                if obj is not None:
                    prop_name = f'gtatools_v_offset_{kind}'
                    try:
                        cur = float(getattr(obj, prop_name, 0.0))
                    except Exception:
                        cur = 0.0
                    st.edit_field = {
                        'rect': L[f'{kind}_v_rect'],
                        'owner': obj,
                        'prop': prop_name,
                        'min': -100.0,
                        'max': 100.0,
                        'is_float': True,
                        'label': f'V {kind}',
                    }
                    # Pre-fill with current value formatted to 2 dp.
                    st.edit_buffer = f"{cur:.2f}".rstrip('0').rstrip('.')
                    if not st.edit_buffer or st.edit_buffer == '-':
                        st.edit_buffer = '0'
                return True
            if B._hit(mx, my, *L[f'{kind}_remove_rect']):
                if self._has_vcol(obj, label_name):
                    B._invoke_operator("gtatools.remove_color_attr",
                                     {"attr_name": label_name})
                else:
                    B._invoke_operator("gtatools.create_color_attr",
                                     {"attr_name": label_name})
                return True
        # Bake
        if B._hit(mx, my, *L['bake_rect']):
            B._invoke_operator("gtatools.bake_vertex_colors_simple", {})
            return True
        if B._hit(mx, my, *L['bake_shadow_rect']):
            B._invoke_operator("gtatools.bake_vertex_colors",
                             {"use_shadows": True})
            return True
        # Альфа вершины (сцена) — превью альфы (enable флипает текущее)
        if 'alpha_scene_rect' in L and B._hit(mx, my, *L['alpha_scene_rect']):
            alpha_on = bool(context.scene.get('inu_alpha_preview_on', False))
            B._invoke_operator("gtatools.alpha_preview",
                             {"enable": not alpha_on})
            return True
        # Запечь поверх / с тенями (additive, over=True)
        if 'bake_over_rect' in L and B._hit(mx, my, *L['bake_over_rect']):
            B._invoke_operator("gtatools.bake_vertex_colors_simple",
                             {"over": True})
            return True
        if 'bake_over_shadow_rect' in L and B._hit(mx, my, *L['bake_over_shadow_rect']):
            B._invoke_operator("gtatools.bake_vertex_colors",
                             {"over": True, "use_shadows": True})
            return True
        # Copy
        if B._hit(mx, my, *L['copy_dn_rect']):
            B._invoke_operator("gtatools.copy_color_attr",
                             {"source": "Day", "target": "Night"})
            return True
        if B._hit(mx, my, *L['copy_nd_rect']):
            B._invoke_operator("gtatools.copy_color_attr",
                             {"source": "Night", "target": "Day"})
            return True
        # LightMap
        if B._hit(mx, my, *L['lm_toggle_rect']):
            exists, on = self._lm_state(obj)
            if exists:
                B._invoke_operator("gtatools.toggle_lightmap_uv2",
                                 {"enable": not on})
            return True
        if B._hit(mx, my, *L['lm_add_rect']):
            B._invoke_operator("gtatools.apply_lightmap_uv2", {})
            return True
        if B._hit(mx, my, *L['lm_remove_rect']):
            B._invoke_operator("gtatools.remove_lightmap_uv2", {})
            return True
        return False
