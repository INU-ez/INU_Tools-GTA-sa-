"""Mini UILayout port for the floater rendering pipeline.

Mirrors Blender's `interface_layout.cc` layout solver — pixel positions
of every widget come from the same formulas Blender uses in its native
N-panel, instead of being computed by hand in each floater's
`extend_body_layout`. Once a floater declares its content via this API,
moving a row by 1 px means changing one constant in `layout_rules.py`,
not rewriting per-floater pixel math.

Supported primitives (cover ~95 % of N-panel patterns we render):

    Column(align=False/True)  — vertical stack
    Row(align=False/True)     — horizontal split
    Box()                     — wrapper with auto `UI_LAYOUT_BOX_MARGIN`
    Leaf(id, kind, ...)       — widget terminal (operator / prop / label)

API mirrors `bpy.types.UILayout` so call sites read like native panels:

    col = Column(align=True)
    row = col.row(align=True)
    row.operator('apply', text='Apply', icon='checkmark', scale_x=2)
    row.prop('preset')
    box = col.box()
    box.column().operator('action')

Caller invokes `solve(root, (x, y, w, h))` to get a flat
`{widget_id: (rect, leaf_metadata)}` mapping ready for hit-test and
draw passes — same `(x, y, w, h)` tuples we previously hand-computed
in `extend_body_layout`.
"""

from ...ui import layout_rules as LR


def _overlap():
    """1-px fused-border overlap when `align=True` — equivalent to
    `U.pixelsize` (1 @ scale 1.0, 2 on Retina). Adjacent widgets in a
    fused row/column overlap by this much so their outlines collapse
    into a single shared divider."""
    return 1


# ── Leaf widgets ────────────────────────────────────────────────────

class Leaf:
    """Terminal node — represents one operator / prop / label / box.
    Stores presentation metadata; the solver fills in `rect` after
    geometry traversal.

    `width` (px) pins the leaf to an exact width inside a Row — useful
    for icon-only buttons that shouldn't stretch. `scale_x` only applies
    when `width is None`: flexible leaves share the row's leftover width
    in proportion to their `scale_x`."""

    def __init__(self, id, kind='operator', text='', icon=None,
                 scale_x=1.0, scale_y=1.0, width=None,
                 corner_mask=None, **payload):
        self.id = id
        self.kind = kind
        self.text = text
        self.icon = icon
        self.scale_x = float(scale_x)
        self.scale_y = float(scale_y)
        self.width = width  # explicit px width (overrides scale_x)
        self.corner_mask = corner_mask
        # Free-form pass-through for floater-specific draw flags
        # (hovered / pressed / dropdown_open / etc.). Keys aren't
        # interpreted by the solver — only by the floater's draw pass.
        self.payload = payload

    def request_height(self, available_width):
        """Min height this leaf wants given `available_width`.

        Per-kind SDF compensation: Blender's native widgets render
        operator buttons 1 px taller than prop-fields (prop_enum,
        value-dropdown). Our SDF shader shaves an extra px off both
        equally on the visible fringe, so the relative gap is preserved
        once we add `+1` to operator and `+0` to prop:

            operator + scale 1.0 → rect 21 → visible 19 px
            prop     + scale 1.0 → rect 20 → visible 18 px
        """
        base = LR.widget_unit() * self.scale_y
        if self.kind != 'prop':
            base += 1  # SDF AA compensation for operator/label leaves
        return int(round(base))

    def solve(self, rect, out):
        out[self.id] = (rect, self)


# ── Container nodes ─────────────────────────────────────────────────

class _Container:
    """Common children + factory API for Column / Row / Box."""

    def __init__(self, align=False):
        self.align = bool(align)
        self.children = []
        self.scale_x = 1.0
        self.scale_y = 1.0
        # Optional explicit px width — mirrors `UILayout.ui_units_x`
        # (× widget_unit) from Blender, used to pin a column or row
        # to an exact px width inside its parent Row instead of
        # competing for leftover space with `scale_x`.
        self.width = None

    def operator(self, id, **kwargs):
        leaf = Leaf(id, kind='operator', **kwargs)
        self.children.append(leaf)
        return leaf

    def prop(self, id, **kwargs):
        leaf = Leaf(id, kind='prop', **kwargs)
        self.children.append(leaf)
        return leaf

    def label(self, id, **kwargs):
        leaf = Leaf(id, kind='label', **kwargs)
        self.children.append(leaf)
        return leaf

    def column(self, align=False):
        col = Column(align=align)
        self.children.append(col)
        return col

    def row(self, align=False):
        row = Row(align=align)
        self.children.append(row)
        return row

    def box(self, box_id='__box__'):
        b = Box(box_id=box_id)
        self.children.append(b)
        return b


class Column(_Container):
    """Vertical stack. `align=True` collapses the inter-row gap into a
    1-px overlap so adjacent borders fuse into a shared divider.
    `align=False` inserts `UI_DEFAULT_SPACING_Y` between children."""

    def _natural_total(self, available_width):
        """Sum of children natural request heights + gaps (no scale_y).
        Used both for `request_height` (multiplied by scale_y) and as
        the denominator in the `solve` proportional distribution."""
        if not self.children:
            return 0
        gap = -_overlap() if self.align else LR.inter_row_gap()
        total = sum(c.request_height(available_width)
                    for c in self.children)
        total += (len(self.children) - 1) * gap
        return total

    def request_height(self, available_width):
        natural = self._natural_total(available_width)
        return max(0, int(round(natural * self.scale_y)))

    def solve(self, rect, out):
        if not self.children:
            return
        x, y, w, h = rect
        gap = -_overlap() if self.align else LR.inter_row_gap()
        # Distribute the allocated height `h` proportionally to each
        # child's natural request. This lets a column with `scale_y=2`
        # (e.g. prelight Preview) coexist in a Row(align=True) whose
        # height was clamped by a smaller sibling — the row chose MIN,
        # the column accepts whatever fits, and the single child fills
        # the column with `h / natural_sum` scaling instead of bursting
        # outside the column bounds.
        natural = self._natural_total(w)
        if natural <= 0:
            return
        ratio = h / natural
        cur_top_y = y + h
        # Pre-compute heights so the last child absorbs rounding
        # remainder — total summed heights match `h` exactly.
        natural_heights = [c.request_height(w) for c in self.children]
        allocated = []
        for nat in natural_heights[:-1]:
            allocated.append(max(1, int(round(nat * ratio))))
        gaps_total = (len(self.children) - 1) * gap
        allocated.append(max(1, h - sum(allocated) - gaps_total))
        for i, (child, ch) in enumerate(zip(self.children, allocated)):
            child_rect = (x, cur_top_y - ch, w, ch)
            child.solve(child_rect, out)
            cur_top_y -= ch
            if i < len(self.children) - 1:
                cur_top_y -= gap


class Row(_Container):
    """Horizontal split. Each child takes width proportional to its
    `scale_x` (default 1). `align=True` fuses adjacent buttons with
    1-px overlap."""

    def _x_gap(self):
        # Horizontal gap — Blender uses the same UI_DEFAULT_SPACING for
        # X and Y in default layouts. Override if/when we observe a
        # divergence in a specific row kind.
        return -_overlap() if self.align else LR.inter_row_gap()

    def _split_widths(self, total_w):
        """Resolve per-child widths inside the row.

        Two-pass:
          1. Reserve px for children with an explicit `width` attr
             (icon-only buttons, fixed-size widgets).
          2. Distribute the remainder among `width=None` children by
             their `scale_x` ratio. Last flexible child absorbs the
             rounding remainder so total widths sum to `total_w`.
        """
        gap = self._x_gap()
        gap_total = (len(self.children) - 1) * gap
        avail_w = max(1, total_w - gap_total)

        fixed_total = sum(getattr(c, 'width', None) or 0
                          for c in self.children
                          if getattr(c, 'width', None) is not None)
        flex = [c for c in self.children if getattr(c, 'width', None) is None]
        flex_w = max(0, avail_w - fixed_total)
        flex_scale_total = sum(c.scale_x for c in flex) or 1.0

        widths = []
        flex_idx = 0
        flex_assigned = 0
        for c in self.children:
            fixed = getattr(c, 'width', None)
            if fixed is not None:
                widths.append(max(1, int(fixed)))
            else:
                if flex_idx == len(flex) - 1:
                    cw = flex_w - flex_assigned
                else:
                    cw = max(1, int(round(
                        flex_w * (c.scale_x / flex_scale_total))))
                widths.append(max(1, cw))
                flex_assigned += widths[-1]
                flex_idx += 1
        return widths

    def request_height(self, available_width):
        if not self.children:
            return 0
        widths = self._split_widths(available_width)
        heights = [c.request_height(cw)
                   for c, cw in zip(self.children, widths)]
        # `align=True` rows fuse — Blender pulls every child to the
        # SHORTEST sibling's height so adjacent borders share clean
        # 1-px dividers regardless of whether the children are leaves
        # or nested containers. This is also why a column with
        # `scale_y=2` (e.g. prelight Preview spanning Day+Night) gets
        # clipped to its sibling column's smaller height — the row's
        # uniform height wins, and the leaf inside fills whatever its
        # column was allocated.
        #
        # Non-aligned rows use MAX so the row's bounding box can
        # accommodate the tallest widget; each child still keeps its
        # own height (top-aligned inside the row, see `solve`).
        chosen = min(heights) if self.align else max(heights)
        return int(round(chosen * self.scale_y))

    def solve(self, rect, out):
        if not self.children:
            return
        x, y, w, h = rect
        gap = self._x_gap()
        widths = self._split_widths(w)
        cur_x = x
        for i, c in enumerate(self.children):
            if self.align:
                # Aligned — every widget at the row's uniform height.
                child_rect = (cur_x, y, widths[i], h)
            else:
                # Non-aligned — each child at its own natural height,
                # top-aligned inside the row's bounding box.
                ch = min(h, c.request_height(widths[i]))
                child_rect = (cur_x, y + h - ch, widths[i], ch)
            c.solve(child_rect, out)
            cur_x += widths[i]
            if i < len(self.children) - 1:
                cur_x += gap


class Box(_Container):
    """Native `layout.box()` — wrapper that reserves
    `UI_LAYOUT_BOX_MARGIN` of inner padding on all sides and records
    its own outer rect under `box_id` so callers can paint the frame.

    Vertical padding is asymmetric (5 top + 6 bottom = 11 total),
    matching Blender's actual N-panel measurement. Symmetric `2 * pad`
    over-allocates by 1 px against native rendering. Horizontal pad
    stays symmetric (`box_pad()` each side).

    Single child only — wrap a column inside if you need to stack
    multiple rows."""

    # Vertical pad totals 12 px — empirically tuned to match the user's
    # observed box outer height in Blender at his current UI scale.
    # Symmetric 6 top / 6 bottom.
    _PAD_TOP = 6
    _PAD_BOT = 6

    def __init__(self, box_id='__box__'):
        super().__init__()
        self.box_id = box_id

    def request_height(self, available_width):
        if not self.children:
            return self._PAD_TOP + self._PAD_BOT
        pad_h = LR.box_pad()
        inner_w = max(1, available_width - 2 * pad_h)
        child = self.children[0]
        return child.request_height(inner_w) + self._PAD_TOP + self._PAD_BOT

    def solve(self, rect, out):
        x, y, w, h = rect
        out[self.box_id] = (rect, self)
        if not self.children:
            return
        pad_h = LR.box_pad()
        inner_rect = (x + pad_h,
                      y + self._PAD_BOT,
                      w - 2 * pad_h,
                      h - self._PAD_TOP - self._PAD_BOT)
        self.children[0].solve(inner_rect, out)


# ── Public entrypoint ────────────────────────────────────────────────

def solve(root, panel_rect):
    """Run layout traversal. `root` is a Column / Row / Box.
    `panel_rect = (x, y, w, h)` is the body region in floater screen
    coords (Y-up). Returns `{widget_id: (rect, leaf)}` ready for
    hit-test and draw passes — same `(x, y, w, h)` tuples we previously
    hand-computed in each floater's `extend_body_layout`."""
    out = {}
    root.solve(panel_rect, out)
    return out


def total_height(root, available_width):
    """Convenience wrapper around `root.request_height` for callers
    that need to allocate panel height before calling `solve()`."""
    return root.request_height(available_width)
