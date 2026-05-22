# INU_tools.ops.floater.gpu_shaders
#
# Custom GPU shader pipelines for the floater:
#   * Widget SDF shader — rounded rect + gradient + outline + AA in one
#     fragment program. Mirrors Blender's interface_draw.c.
#   * Icon raster shader — samples PNGs under INU_tools/data/icons/,
#     tinted by `tint_color`.
# Plus all rect / rounded-rect / drop-shadow drawing helpers built on
# top of the above (fallbacks to UNIFORM_COLOR built-in when the SDF
# shader compile fails on a given platform).
#
# Colour values flow in via the `theme` sibling module — `TH._C_TEXT`
# is referenced here as the default icon tint.

import math
import os
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from . import theme as TH


# ── GPU primitives ───────────────────────────────────────────────────

def _rect_verts(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _draw_rect(x, y, w, h, color):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    batch = batch_for_shader(shader, 'TRI_FAN', {"pos": _rect_verts(x, y, w, h)})
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def _draw_rect_outline(x, y, w, h, color):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    verts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": verts})
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


# ── Native-feel widget shader ────────────────────────────────────────
#
# Single GLSL shader that does rounded corners + vertical gradient +
# outline + anti-aliasing in one draw call. Mirrors what Blender's own
# interface_draw.c → widget_base.glsl does for native widgets, just
# implemented here in our addon since the C-level shader is not exposed
# to Python's gpu API.
#
# Algorithm:
#   1. Quad covers slightly larger area than the rect (1-2 px padding)
#      so anti-aliased fringe pixels aren't clipped.
#   2. Fragment computes signed-distance to rounded rectangle:
#        d < 0   inside
#        d = 0   exactly on boundary
#        d > 0   outside
#   3. total_shape  = smoothstep around d=0 → soft AA edge
#      outline_mask = band of pixels with -outline_width <= d <= 0
#   4. Inner color = mix(bottom, top) by Y position in rect.
#   5. Final = mix(inner, outline_color, outline_mask), alpha *= total_shape

# Vertex source — no `uniform mat4 ModelViewProjectionMatrix` line:
# in Blender 4.x's create_from_info shaders the MVP is declared as a
# push_constant in Python and we manually set it before each draw.
_WIDGET_VERT_SRC = """
void main()
{
    v_local = local_pos;
    gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
}
"""

_WIDGET_FRAG_SRC = """
vec3 srgb_to_linear(vec3 c)
{
    // Blender's theme colours come from the user as sRGB display values.
    // create_from_info shaders write to a linear framebuffer that
    // Blender re-converts to sRGB for display, so without this step
    // our colours render ~2× lighter than the user picked in Theme.
    return pow(max(c, vec3(0.0)), vec3(2.2));
}

void main()
{
    // size_radius_outline (xyzw) = size.x, size.y, base_radius, corner_mask
    // Corner mask encodes which corners are rounded as 4 bits:
    //   bit 0 (1)  = top-left,   bit 1 (2)  = top-right,
    //   bit 2 (4)  = bottom-left, bit 3 (8) = bottom-right.
    // For uniform rounding all 4 bits are set (mask = 15). Enum-row
    // buttons turn off inner-edge bits to fuse adjacent buttons with
    // a sharp shared edge.
    //
    // outline_width is packed into color_outline.a so we keep the
    // 128-byte push-constant budget. We assume opaque outlines (alpha
    // always 1.0 for the colour itself).
    vec2  size         = size_radius_outline.xy;
    float base_radius  = size_radius_outline.z;
    int   corner_mask  = int(round(size_radius_outline.w));
    float outline_width = color_outline.a;

    vec2 half_size = size * 0.5;
    vec2 p = v_local - half_size;

    // Pick this fragment's corner radius from the mask.
    bool right = p.x > 0.0;
    bool top   = p.y > 0.0;
    int bit;
    if      (top  && !right) bit = 1;   // TL
    else if (top  &&  right) bit = 2;   // TR
    else if (!top && !right) bit = 4;   // BL
    else                     bit = 8;   // BR
    float radius = ((corner_mask & bit) != 0) ? base_radius : 0.0;

    vec2 q = abs(p) - half_size + vec2(radius);
    float d = min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - radius;

    float total_shape = 1.0 - smoothstep(-0.5, 0.5, d);
    // `inside_inner` is 1.0 deep inside the shape and 0.0 at/past the
    // outline band — we use it to pick between inner and outline rgb.
    // Outer AA happens on `total_shape` instead, which controls alpha
    // only; that way fragments on the outer fringe are pure outline
    // colour fading to transparent, with no inner-colour bleed.
    float inside_inner = 1.0 - smoothstep(-outline_width - 0.5,
                                          -outline_width + 0.5, d);

    float t = clamp(v_local.y / max(size.y, 1.0), 0.0, 1.0);
    vec4 inner_color = mix(color_bottom, color_top, t);

    vec3 col_rgb = mix(color_outline.rgb, inner_color.rgb, inside_inner);

    fragColor = vec4(srgb_to_linear(col_rgb), inner_color.a * total_shape);
}
"""

_widget_shader = None
_widget_first_draw_logged = False


def _get_widget_shader():
    """Lazy-build the widget shader. Returns None if compile fails — in
    that case callers fall back to the older flat-rendering path.

    Built via gpu.shader.create_from_info — direct `GPUShader(vert, frag)`
    construction is locked down in Blender 4.x ("cannot create
    'GPUShader' instances"), the create_from_info pipeline is the
    sanctioned way to load custom shaders going forward.
    """
    global _widget_shader
    if _widget_shader is None:
        try:
            info = gpu.types.GPUShaderCreateInfo()
            info.push_constant('MAT4', 'ModelViewProjectionMatrix')
            # Pack size + radius + outline_width into one vec4 — separate
            # FLOAT / VEC2 push constants each pad to 16 bytes due to
            # std140 alignment rules and quickly blow past the 128-byte
            # minimum guarantee.
            info.push_constant('VEC4', 'size_radius_outline')
            info.push_constant('VEC4', 'color_bottom')
            info.push_constant('VEC4', 'color_top')
            info.push_constant('VEC4', 'color_outline')

            info.vertex_in(0, 'VEC2', 'pos')
            info.vertex_in(1, 'VEC2', 'local_pos')

            iface = gpu.types.GPUStageInterfaceInfo("inu_widget_iface")
            iface.smooth('VEC2', 'v_local')
            info.vertex_out(iface)

            info.fragment_out(0, 'VEC4', 'fragColor')
            info.vertex_source(_WIDGET_VERT_SRC)
            info.fragment_source(_WIDGET_FRAG_SRC)

            _widget_shader = gpu.shader.create_from_info(info)
            print("[INU Floater] widget shader compile: OK")
        except Exception as e:
            print(f"[INU Floater] widget shader compile failed: {e}")
            _widget_shader = False  # sentinel — don't retry
    return _widget_shader if _widget_shader else None


CORNER_TL = 1
CORNER_TR = 2
CORNER_BL = 4
CORNER_BR = 8
CORNER_ALL = CORNER_TL | CORNER_TR | CORNER_BL | CORNER_BR    # 15
CORNER_LEFT = CORNER_TL | CORNER_BL                            # 5
CORNER_RIGHT = CORNER_TR | CORNER_BR                           # 10
CORNER_TOP = CORNER_TL | CORNER_TR                             # 3 — dropdown anchor btn
CORNER_BOTTOM = CORNER_BL | CORNER_BR                          # 12 — dropdown panel
CORNER_NONE = 0


def _draw_widget(x, y, w, h, color_bottom, color_top, color_outline,
                 radius, outline_width=1.0, corner_mask=CORNER_ALL):
    """Draw a native-feel widget: rounded rect + gradient + AA + outline.

    `corner_mask` selects which corners get the `radius`; the rest are
    drawn sharp. Use CORNER_LEFT / CORNER_RIGHT / CORNER_NONE for the
    middle and end buttons of an attached enum-row so neighbours share
    a flat edge.

    Single GPU draw call. Falls back to flat rounded rect if the SDF
    shader failed to compile on this platform.
    """
    shader = _get_widget_shader()
    if shader is None:
        _draw_rect_rounded_gradient(x, y, w, h, color_bottom, color_top, radius)
        if outline_width > 0:
            _draw_rect_outline_rounded(x, y, w, h, color_outline, radius)
        return

    # Expand the quad by 1.5 px on each side so the AA fringe at d≈0
    # has somewhere to live — without padding the corner pixels would
    # be clipped by the quad geometry and edges look chunky.
    pad = 1.5
    verts = [
        (x - pad,     y - pad),
        (x + w + pad, y - pad),
        (x + w + pad, y + h + pad),
        (x - pad,     y + h + pad),
    ]
    locals_ = [
        (-pad,    -pad),
        (w + pad, -pad),
        (w + pad, h + pad),
        (-pad,    h + pad),
    ]

    # outline_width is packed into color_outline.a — see fragment shader
    # for the unpack — so we have room for corner_mask in the push
    # constants without exceeding the 128-byte budget.
    outline_packed = (float(color_outline[0]),
                      float(color_outline[1]),
                      float(color_outline[2]),
                      float(outline_width))

    try:
        gpu.state.blend_set('ALPHA')
        batch = batch_for_shader(
            shader, 'TRI_FAN',
            {"pos": verts, "local_pos": locals_},
        )
        shader.bind()
        # create_from_info shaders don't auto-bind ModelViewProjectionMatrix;
        # we must compute & upload it from the current gpu.matrix stacks.
        mvp = (gpu.matrix.get_projection_matrix()
               @ gpu.matrix.get_model_view_matrix())
        shader.uniform_float("ModelViewProjectionMatrix", mvp)
        shader.uniform_float("size_radius_outline",
                             (float(w), float(h),
                              float(radius), float(corner_mask)))
        shader.uniform_float("color_bottom", color_bottom)
        shader.uniform_float("color_top", color_top)
        shader.uniform_float("color_outline", outline_packed)
        batch.draw(shader)
        gpu.state.blend_set('NONE')
        global _widget_first_draw_logged
        if not _widget_first_draw_logged:
            print(f"[INU Floater] widget shader first draw: OK "
                  f"(rect={w}x{h}, radius={radius})")
            _widget_first_draw_logged = True
    except Exception as e:
        print(f"[INU Floater] widget render failed: {e}")
        # Fall back to tessellated path so the panel/buttons stay visible.
        _draw_rect_rounded_gradient(x, y, w, h, color_bottom, color_top, radius)
        if outline_width > 0:
            _draw_rect_outline_rounded(x, y, w, h, color_outline, radius)


def _rounded_rect_fan(x, y, w, h, radius, segments=6):
    """Triangle-fan vertices for a filled rounded rectangle: center
    first, then perimeter counterclockwise from bottom-right corner."""
    r = max(0.0, min(radius, w / 2.0, h / 2.0))
    if r <= 0.5:
        return [(x + w / 2.0, y + h / 2.0),
                (x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    cx, cy = x + w / 2.0, y + h / 2.0
    verts = [(cx, cy)]
    corners = (
        (x + w - r, y + r,         -math.pi / 2.0),  # bottom-right
        (x + w - r, y + h - r,      0.0),            # top-right
        (x + r,     y + h - r,      math.pi / 2.0),  # top-left
        (x + r,     y + r,          math.pi),        # bottom-left
    )
    for ccx, ccy, start in corners:
        for i in range(segments + 1):
            a = start + (math.pi / 2.0) * (i / segments)
            verts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    verts.append(verts[1])  # close fan
    return verts


def _rounded_rect_perimeter(x, y, w, h, radius, segments=6):
    """Perimeter-only verts for the outline LINE_STRIP."""
    r = max(0.0, min(radius, w / 2.0, h / 2.0))
    if r <= 0.5:
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    verts = []
    corners = (
        (x + w - r, y + r,         -math.pi / 2.0),
        (x + w - r, y + h - r,      0.0),
        (x + r,     y + h - r,      math.pi / 2.0),
        (x + r,     y + r,          math.pi),
    )
    for ccx, ccy, start in corners:
        for i in range(segments + 1):
            a = start + (math.pi / 2.0) * (i / segments)
            verts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    verts.append(verts[0])  # close
    return verts


def _draw_rect_rounded(x, y, w, h, color, radius):
    """Filled rounded rect using triangle-fan tessellation. No anti-
    aliasing — for crisper edges we'd need a custom SDF fragment shader."""
    if radius <= 0.5:
        _draw_rect(x, y, w, h, color)
        return
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    batch = batch_for_shader(
        shader, 'TRI_FAN',
        {"pos": _rounded_rect_fan(x, y, w, h, radius)}
    )
    shader.uniform_float("color", color)
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def _lerp(a, b, t):
    return a + (b - a) * t


def _draw_drop_shadow(x, y, w, h, radius, spread=4, alpha_base=0.03):
    """Soft directional drop shadow — bottom + left + right (no top).

    Simulates a panel lifted above the viewport with light from
    directly above: shadow drops straight down and spreads outward
    to both sides, but the top edge stays flush so no shadow is
    cast above the panel. Each layer is a slightly-wider rounded
    rect offset down by `i` px.
    """
    for i in range(spread, 0, -1):
        a = alpha_base * (spread - i + 1) / spread
        _draw_rect_rounded(x - i, y - i, w + 2 * i, h,
                           (0.0, 0.0, 0.0, a), radius + i)


def _draw_rect_gradient(x, y, w, h, color_bottom, color_top):
    """Sharp-cornered vertical gradient — used for the flat header strip
    inside the rounded panel (panel border hides the sharp corners)."""
    verts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    colors = [color_bottom, color_bottom, color_top, color_top]
    shader = gpu.shader.from_builtin('SMOOTH_COLOR')
    gpu.state.blend_set('ALPHA')
    batch = batch_for_shader(shader, 'TRI_FAN', {"pos": verts, "color": colors})
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def _draw_rect_rounded_gradient(x, y, w, h, color_bottom, color_top, radius):
    """Same shape as _draw_rect_rounded but with a vertical color gradient.

    Used to give buttons the subtle 'raised' look Blender's native widgets
    have — bottom slightly darker, top slightly lighter. Per-vertex color
    interpolation via the SMOOTH_COLOR built-in shader.
    """
    verts = _rounded_rect_fan(x, y, w, h, radius)
    h_safe = max(1.0, float(h))
    colors = []
    for vx, vy in verts:
        t = max(0.0, min(1.0, (vy - y) / h_safe))
        colors.append((
            _lerp(color_bottom[0], color_top[0], t),
            _lerp(color_bottom[1], color_top[1], t),
            _lerp(color_bottom[2], color_top[2], t),
            _lerp(color_bottom[3] if len(color_bottom) > 3 else 1.0,
                  color_top[3] if len(color_top) > 3 else 1.0, t),
        ))
    shader = gpu.shader.from_builtin('SMOOTH_COLOR')
    gpu.state.blend_set('ALPHA')
    batch = batch_for_shader(shader, 'TRI_FAN',
                             {"pos": verts, "color": colors})
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def _draw_rect_outline_rounded(x, y, w, h, color, radius):
    if radius <= 0.5:
        _draw_rect_outline(x, y, w, h, color)
        return
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    try:
        gpu.state.line_smooth_set(True)
    except Exception:
        pass
    batch = batch_for_shader(
        shader, 'LINE_STRIP',
        {"pos": _rounded_rect_perimeter(x, y, w, h, radius)}
    )
    shader.uniform_float("color", color)
    batch.draw(shader)
    try:
        gpu.state.line_smooth_set(False)
    except Exception:
        pass
    gpu.state.blend_set('NONE')


# ── Menu chevron (programmatic, no SVG) ──────────────────────────────
#
# Mirrors Blender's `shape_preset_trias_from_rect_menu` in
# interface_widgets.cc:916 — the dropdown indicator in N-panel menu
# buttons is drawn as a programmatic double-arrow (▲ on top + ▼ on
# bottom), not from any SVG icon. Matching that exactly here is the
# only way to have our floater menu buttons look identical to Blender's.
#
# Vertex layout (from g_shape_preset_menu_arrow_vert):
#   0: (-0.33,  0.16)
#   1: ( 0.33,  0.16)
#   2: ( 0.00,  0.82)   ▲ apex
#   3: ( 0.00, -0.82)   ▼ apex
#   4: (-0.33, -0.16)
#   5: ( 0.33, -0.16)
# Faces: {2, 0, 1} (upper ▲) and {3, 5, 4} (lower ▼).
# Size = 0.4 * height (Blender's scaling factor).

_MENU_TRIA_VERTS_NORM = (
    (-0.33,  0.16),
    ( 0.33,  0.16),
    ( 0.00,  0.82),
    ( 0.00, -0.82),
    (-0.33, -0.16),
    ( 0.33, -0.16),
)


def _draw_menu_tria(rect, color, pointing='down', scale=1.0,
                    width=None, height=None, halo=True, apex_size=2,
                    halo_alpha=0.15, halo_clip_bbox=False):
    """Draw a chevron dropdown indicator inside `rect`.

    Two thick parallelogram strokes meeting at a centre apex —
    mathematically a proper chevron, not a pixel-stamp approximation.
    Each stroke is computed by offsetting the start/end points by
    half the stroke thickness along the segment's perpendicular,
    giving a uniform 1-px stroke with 2-px AA halo.

    `pointing='down'` draws `v` (apex below centre — dropdown menus).
    `pointing='right'` draws `>` (apex right of centre — collapsible
    section headers when collapsed).
    `scale` shrinks/expands the whole chevron proportionally.
    `width` / `height` (px) explicitly override the chevron geometry
    — useful when the dropdown chevron and the header collapse chevron
    want different aspect ratios."""
    x, y, w, h = rect
    cx = x + w / 2.0
    cy = y + h / 2.0

    base_w = width  if width  is not None else 6.0 * scale
    base_h = height if height is not None else 3.0 * scale
    arm_w     = base_w / 2.0
    arm_y_top = base_h / 2.0
    apex_y    = -base_h / 2.0
    core_t    = 1.0     # crisp 1-px center stroke (don't scale to keep crispness)
    halo_t    = 2.0     # AA fringe extends 0.5 px each side of core

    def _quad(start, end, t):
        """Return 4 verts (CCW) of a `t`-thick stroke between two points."""
        sx, sy = start
        ex, ey = end
        dx, dy = ex - sx, ey - sy
        length = max(0.001, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        hx, hy = nx * t / 2.0, ny * t / 2.0
        return [
            (sx - hx, sy - hy),
            (sx + hx, sy + hy),
            (ex + hx, ey + hy),
            (ex - hx, ey - hy),
        ]

    if pointing == 'right':
        # Rotate the down-chevron by 90° CCW: (x', y') = (-y, x).
        apex      = (cx - apex_y,     cy)
        arm_left  = (cx - arm_y_top, cy - arm_w)   # top arm
        arm_right = (cx - arm_y_top, cy + arm_w)   # bottom arm
    else:
        apex      = (cx, cy + apex_y)
        arm_left  = (cx - arm_w, cy + arm_y_top)
        arm_right = (cx + arm_w, cy + arm_y_top)

    def _stroke_tris(thickness):
        l = _quad(arm_left, apex, thickness)
        r = _quad(arm_right, apex, thickness)
        return [
            l[0], l[1], l[2], l[0], l[2], l[3],
            r[0], r[1], r[2], r[0], r[2], r[3],
        ]

    # Both paths share a pixel-stamp v-shape — crisp 1-px stair-step
    # core. `halo=True` additionally paints a uniform soft halo around
    # every core pixel (one fringe pixel per neighbour, alpha by number
    # of adjacent cores). `halo=False` keeps just the core for chrome
    # collapse arrows where the smallest possible footprint matters.
    icx = int(round(cx))
    icy = int(round(cy))
    ih  = int(round(base_h))             # vertical extent in px (= rows)
    iw_half = ih - 1                     # arm half-width at top
    base_a = color[3] if len(color) >= 4 else 1.0

    def _coord(i, side):
        """Compute (px, py) of the main pixel for row `i`, given
        `side` (-1 left, +1 right). For pointing='right', x/y are
        swapped semantically."""
        offset = iw_half - i
        if pointing == 'right':
            px = icx + i - (ih // 2)
            py = icy + side * offset
        else:
            px = icx + side * offset
            py = icy + offset - (ih // 2)
        return px, py

    # Collect core pixel positions (set so dedupes overlaps).
    # `apex_size=2` adds a second pixel at the apex and shifts the +1
    # arm by 1 px so the chevron stays symmetric around the widened
    # tip (used by dropdown chevrons which want a chunkier point).
    # `apex_size=1` keeps the apex as a single pixel — used by chrome
    # collapse arrows where the tip should read as a crisp 1-px dot.
    cores = set()
    for i in range(ih):
        offset = iw_half - i
        if offset == 0:
            px, py = _coord(i, 1)
            cores.add((px, py))
            if apex_size >= 2:
                if pointing == 'right':
                    cores.add((px, py + 1))
                else:
                    cores.add((px + 1, py))
        else:
            for side in (-1, +1):
                px, py = _coord(i, side)
                if side == +1 and apex_size >= 2:
                    if pointing == 'right':
                        py += 1
                    else:
                        px += 1
                cores.add((px, py))

    gpu.state.blend_set('ALPHA')
    if halo:
        # 1-px halo — only CARDINAL neighbours (N/S/E/W), never
        # diagonal. Including diagonals would paint the L-corner
        # between two stair-step cores, visually thickening each
        # diagonal arm to 2 px. Skipping them keeps the arm 1 px
        # thick and adds halo only on the outer perimeter sides.
        halo_pixels = set()
        for (cx_, cy_) in cores:
            for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = cx_ + dx, cy_ + dy
                if (nx, ny) in cores:
                    continue
                halo_pixels.add((nx, ny))
        # Optionally clip halo to the bbox of cores — strips halo on
        # the top / bottom / left / right of the whole chevron so the
        # AA reads only along the diagonal arm slopes, not as a frame
        # around the whole shape.
        if halo_clip_bbox:
            xs = [c[0] for c in cores]
            ys = [c[1] for c in cores]
            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            halo_pixels = {(hx, hy) for (hx, hy) in halo_pixels
                           if xmin <= hx <= xmax and ymin <= hy <= ymax}
        halo_color = (color[0], color[1], color[2], base_a * halo_alpha)
        for (hx, hy) in halo_pixels:
            _draw_rect(hx, hy, 1, 1, halo_color)

    # Core pixels at full alpha — drawn last so they sit on top of
    # any halo pixel that overlapped a core position.
    for (cx_, cy_) in cores:
        _draw_rect(cx_, cy_, 1, 1, color)
    gpu.state.blend_set('NONE')


# ── Icon (Blender SVG) raster pipeline ───────────────────────────────
#
# Each PNG in INU_tools/data/icons/ is white-on-transparent. We sample
# the texture with bilinear filtering and modulate by `tint_color`,
# giving the same multi-purpose tinted-icon look Blender uses for its
# UI icons. PNGs are 32×32 RGBA, baked from Blender's official SVG
# icon set via dev/rasterize_icons.py.

_ICON_TEXTURES = {}
_icon_shader = None

_ICON_VERT_SRC = """
void main() {
    v_uv = uv;
    gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
}
"""

_ICON_FRAG_SRC = """
void main() {
    fragColor = texture(atlas, v_uv) * tint_color;
}
"""


def _get_icon_shader():
    global _icon_shader
    if _icon_shader is None:
        try:
            info = gpu.types.GPUShaderCreateInfo()
            info.push_constant('MAT4', 'ModelViewProjectionMatrix')
            info.push_constant('VEC4', 'tint_color')
            info.vertex_in(0, 'VEC2', 'pos')
            info.vertex_in(1, 'VEC2', 'uv')
            iface = gpu.types.GPUStageInterfaceInfo("inu_icon_iface")
            iface.smooth('VEC2', 'v_uv')
            info.vertex_out(iface)
            info.sampler(0, 'FLOAT_2D', 'atlas')
            info.fragment_out(0, 'VEC4', 'fragColor')
            info.vertex_source(_ICON_VERT_SRC)
            info.fragment_source(_ICON_FRAG_SRC)
            _icon_shader = gpu.shader.create_from_info(info)
            print("[INU Floater] icon shader compile: OK")
        except Exception as e:
            print(f"[INU Floater] icon shader compile failed: {e}")
            _icon_shader = False
    return _icon_shader if _icon_shader else None


def _load_icons():
    """Eager-load every PNG under INU_tools/data/icons/ into a
    GPUTexture cache keyed by the file's base name (without .png).
    Already-loaded icons are not re-loaded — safe to call repeatedly.

    Lookup order (first match wins):
      1. ``data/icons/native/<NAME>.png`` — Blender stock icons,
         pre-baked offline and shipped with the addon. Files here use
         UPPERCASE names matching Blender's icon enum, so we lowercase
         them on load to match the existing key convention.
      2. ``data/icons/<name>.png`` — the original Lucide PNG bake
         shipped with the addon.
    """
    if _ICON_TEXTURES:
        return
    addon_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    base_dir = os.path.join(addon_dir, "data", "icons")
    native_dir = os.path.join(base_dir, "native")

    if not os.path.isdir(base_dir):
        print(f"[INU Floater] icons dir missing: {base_dir}")
        return
    print(f"[INU Floater] icon scan: base={base_dir}")
    print(f"[INU Floater] icon scan: native={native_dir} exists={os.path.isdir(native_dir)}")

    # Source #1: native bake (UPPERCASE filenames, BLENDER_ICON.png).
    # These take priority because the user just ran a bake to get them
    # and clearly wants Blender stock visuals.
    sources = []
    if os.path.isdir(native_dir):
        for fn in sorted(os.listdir(native_dir)):
            if fn.lower().endswith(".png"):
                # Native bake stores the enum name verbatim; lower-case
                # it for our cache key so callers (compat.inu_icon)
                # don't have to know which set is active.
                key = os.path.splitext(fn)[0].lower()
                sources.append((key, os.path.join(native_dir, fn)))

    # Source #2: shipped Lucide PNGs in the parent folder (lowercase).
    existing_keys = {k for k, _ in sources}
    for fn in sorted(os.listdir(base_dir)):
        if not fn.lower().endswith(".png"):
            continue
        path = os.path.join(base_dir, fn)
        if os.path.isdir(path):
            continue
        key = os.path.splitext(fn)[0].lower()
        if key in existing_keys:
            continue  # native bake wins
        sources.append((key, path))

    loaded = 0
    for name, path in sources:
        try:
            img_name = f"inu_icon_{name}"
            old = bpy.data.images.get(img_name)
            if old is not None:
                try:
                    bpy.data.images.remove(old)
                except Exception:
                    pass
            img = bpy.data.images.load(path)
            img.name = img_name
            _ICON_TEXTURES[name] = gpu.texture.from_image(img)
            loaded += 1
        except Exception as e:
            print(f"[INU Floater] icon load failed: {name} -> {e}")
    print(f"[INU Floater] loaded {loaded} icons (native: {len(existing_keys)})")


def _free_icons():
    """Drop the icon texture cache on unregister."""
    _ICON_TEXTURES.clear()


def _draw_icon(rect, name, tint=None):
    """Draw a named icon stretched to the supplied rect, tinted by
    `tint` (RGBA tuple, defaults to TH._C_TEXT). Returns True on success.

    Always tries the PNG cache even when ``USE_CUSTOM_ICONS=False``
    in N-panel mode — Blender's stock icon atlas isn't accessible
    from custom GPU draw handlers, so floaters MUST use PNG textures.
    Cleaner to have inconsistent-but-iconographic floater buttons
    than text-only ones."""
    tex = _ICON_TEXTURES.get(name)
    if tex is None:
        return False
    shader = _get_icon_shader()
    if shader is None:
        return False
    if tint is None:
        tint = TH._C_TEXT
    x, y, w, h = rect
    verts = [
        (x,     y),
        (x + w, y),
        (x + w, y + h),
        (x,     y + h),
    ]
    # gpu.texture.from_image already stores Blender-image pixels in
    # bottom-up order (image[0,0] = bottom-left), so screen-bottom-left
    # maps to UV (0,0) without flipping. Earlier we had the V flipped
    # which displayed every icon upside down.
    uvs = [
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
    ]
    try:
        gpu.state.blend_set('ALPHA')
        batch = batch_for_shader(shader, 'TRI_FAN',
                                 {"pos": verts, "uv": uvs})
        shader.bind()
        mvp = (gpu.matrix.get_projection_matrix()
               @ gpu.matrix.get_model_view_matrix())
        shader.uniform_float("ModelViewProjectionMatrix", mvp)
        shader.uniform_sampler("atlas", tex)
        shader.uniform_float("tint_color", tint)
        batch.draw(shader)
        gpu.state.blend_set('NONE')
        return True
    except Exception as e:
        print(f"[INU Floater] draw icon '{name}' failed: {e}")
        return False


def _draw_icon_centered(rect, name, size=None, tint=None):
    """Centre an icon inside `rect`. `size` defaults to the smaller of
    rect's dimensions minus 8 px padding (clamped >= 10)."""
    x, y, w, h = rect
    if size is None:
        size = max(10, min(w, h) - 8)
    cx = x + (w - size) // 2
    cy = y + (h - size) // 2
    return _draw_icon((int(cx), int(cy), int(size), int(size)),
                      name, tint)


