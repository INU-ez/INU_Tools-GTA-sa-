"""Bake Lucide UI icons into white RGBA PNGs for the floater.

Replaces the older Blender-source SVG bake — Lucide icons are designed
on a pixel grid for UI rendering and translate much cleaner to small
raster sizes than Blender's mesh-style SVGs.

Source SVGs (Lucide, ISC license) live in dev/ next to this script.
Each Lucide name is mapped to one or more "our names" — the floater
code looks icons up by these (e.g. `checkmark.png` not `check.png`)
so the runtime icon-cache keys stay stable when the source set
changes. Naming follows Blender's `safe_icon('NAME')` convention but
lowercased, so adding a new icon usually means: pick the right Lucide
source + add an entry below.

The bake recolours `stroke="currentColor"` to white before rendering
and supersamples 4×: render at `SIZE * SS` with AA on, then downscale
to SIZE with PIL LANCZOS. Result is a smooth white glyph on a
transparent canvas — usable as `icon_value` inside UILayout and as a
GPU texture inside the floater.

Run from anywhere — paths anchored to __file__:
    python dev/rasterize_icons.py
"""
import os
import sys
import re
import tempfile
import fitz   # pymupdf — pure-Python SVG/PDF renderer

# AA on — we render at 4× and downscale with LANCZOS, so anti-aliasing
# at render time gives the LANCZOS filter clean gradients to work with.
fitz.TOOLS.set_aa_level(8)

DEV_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(DEV_DIR),
                       "INU_tools", "data", "icons")

# Lucide source filename → list of our PNG names. Each source can map
# to multiple destinations because several Blender icon names share
# the same visual (e.g. light / light_data / light_hemi all use the
# lightbulb glyph). Names mirror Blender's `safe_icon('NAME')` keys
# lowercased so future floater code can do a 1:1 swap.
ICON_MAP = {
    # ── Basic glyphs ────────────────────────────────
    "check":            ["checkmark", "file_tick"],
    "pencil":           ["greasepencil"],
    "plus":             ["add"],
    "minus":            ["remove"],
    "x":                ["x", "cancel", "panel_close"],

    # ── Import / Export / Upload arrows ─────────────
    "upload":           ["export"],
    "download":         ["import"],
    "arrow-up-from-line": ["empty_single_arrow"],

    # ── Chevrons / Tria ─────────────────────────────
    "chevron-down":     ["tria_down", "disclosure_tri_down"],
    "chevron-right":    ["tria_right"],
    "chevron-up":       ["tria_up"],
    "chevron-left":     ["tria_left"],

    # ── Other arrows ────────────────────────────────
    "arrow-right":      ["forward"],
    "rotate-ccw":       ["loop_back"],
    "arrow-down-a-z":   ["sortalpha"],

    # ── Visibility / Eye ────────────────────────────
    "eye":              ["hide_off", "restrict_view_off"],
    "eye-closed":       ["hide_on", "restrict_view_on"],

    # ── Status ──────────────────────────────────────
    "triangle-alert":   ["error"],
    "info":             ["info"],
    "circle-question-mark": ["question", "help"],
    "users":            ["community"],
    "external-link":    ["url"],
    "lock":             ["locked"],

    # ── Files / Folders ─────────────────────────────
    "file":             ["file", "file_blank"],
    "folder":           ["file_folder", "outliner_collection"],
    "file-plus":        ["file_new"],
    "file-text":        ["file_text", "text"],
    "refresh-ccw":      ["file_refresh"],
    "database":         ["file_cache"],
    "archive":          ["file_volume"],
    "trash-2":          ["trash"],
    "package":          ["package", "asset_manager"],
    "library":          ["library_data_direct"],
    "clipboard-copy":   ["copydown"],

    # ── Edit / Action ───────────────────────────────
    "copy":             ["duplicate", "copy_id"],
    "square-pen":       ["editmode_hlt"],
    "settings-2":       ["preferences", "tool_settings"],
    "wrench":           ["modifier"],
    "play":             ["play"],
    "circle-dot":       ["radiobut_on", "rec"],
    "circle":           ["radiobut_off"],
    "hand":             ["hand"],
    "maximize":         ["fullscreen_enter"],
    "pipette":          ["eyedropper"],
    "zap":              ["auto"],
    "merge":            ["automerge_on"],
    "bookmark":         ["preset"],
    "star":             ["solo_on"],
    "user-check":       ["fake_user_on"],
    "ellipsis":         ["three_dots"],

    # ── Selection / View ────────────────────────────
    "mouse-pointer":    ["restrict_select_off"],
    "mouse-pointer-ban":["restrict_select_on"],
    "mouse-pointer-2":  ["select_extend"],
    "zoom-out":         ["zoom_previous"],
    "search":           ["viewzoom"],
    "grid-3x3":         ["grid", "snap_grid"],
    "list-tree":        ["outliner"],

    # ── Materials / Color / Texture ─────────────────
    "palette":          ["material", "node_material", "color"],
    "grid-2x2":         ["texture"],
    "brush":            ["brush_data"],
    "paint-bucket":     ["vpaint_hlt"],
    "workflow":         ["nodetree"],
    "image":            ["render_still", "image", "image_data"],
    "images-down":      ["render_result"],
    "unlink":           ["orphan_data", "unlinked"],
    "link":             ["linked", "link_blend"],
    "link-2":           ["constraint"],

    # ── Checkbox / Radio ────────────────────────────
    "square-check":     ["checkbox_hlt"],
    "square":           ["checkbox_dehlt"],

    # ── Geometry / Mesh ─────────────────────────────
    "box":              ["mesh_data", "mesh_cube", "object_data"],
    "globe":            ["mesh_icosphere", "orientation_gimbal"],
    "smile":            ["mesh_monkey"],
    "spline":           ["curve_path"],
    "pin":              ["sticky_uvs_loc"],
    "waves-horizontal": ["mod_smooth"],
    "rotate-3d":        ["mod_screw"],
    "droplets":         ["mod_fluidsim"],
    "projector":        ["mod_uvproject"],
    "square-centerline-dashed-horizontal": ["mod_mirror"],
    "move":             ["empty_axis", "empty_arrows", "move"],
    "magnet":           ["snap_on"],
    "lightbulb":        ["light", "light_data", "light_hemi", "light_point"],

    # ── Lights / Camera / Tools ─────────────────────
    "sun":              ["light_sun"],
    "camera":           ["camera_data"],
    "bone":             ["armature_data"],
    "sparkles":         ["particles"],
    "atom":             ["physics"],
    "film":             ["action"],
    "list-ordered":     ["sequence"],
    "crosshair":        ["tracker"],
    "train-track":      ["tracking"],
    "bot":              ["con_kinematic"],
    "route":            ["con_followpath"],
    "diamond":          ["decorate_keyframe"],
    "chart-line":       ["fcurve", "smoothcurve"],
    "trending-up":      ["ipo_linear"],
    "type":             ["outliner_data_font", "outliner_ob_group_instance"],

    # ── Floater chrome ──────────────────────────────
    "square-arrow-out-up-right": ["window"],
}

SIZE = 128       # Final PNG resolution. 128 covers Blender at UI scale 1–4×.
SS = 8           # Supersample factor: render at SIZE*SS, then downscale.
                 # 8× gives the LANCZOS/BICUBIC filter enough source pixels
                 # per output pixel that anti-aliasing comes from the
                 # supersample itself — no extra Gaussian blur needed.
STROKE_COLOR = "#FCFCFC"   # rgb(252,252,252) — matches Blender's native
                           # icon stroke colour, slightly off-pure-white
                           # so glyphs don't burn against panel backgrounds.


def _normalise_stroke_null(svg_text: str) -> str:
    """Rewrite the Photoshop-isms ``stroke="null"`` based on context.

    PS exports invalid ``null`` to mean "stroke disabled". But that's
    only correct for fill-only shapes — for lines and unfilled paths
    "no stroke" means **invisible geometry** (a line needs a stroke
    to render anything at all). So:

      * tag has ``fill="<non-none>"`` (e.g. ``fill="currentColor"``)
        → ``stroke="null"`` is replaced with ``stroke="none"`` so the
        filled body shows without an unwanted dark border;
      * everything else (``fill="none"``, no fill attr — i.e. line /
        unfilled path) → replaced with ``stroke="currentColor"`` so
        the geometry stays visible after the main currentColor →
        colour substitution downstream.
    """
    def fix(m):
        tag = m.group(0)
        if 'stroke="null"' not in tag:
            return tag
        fm = re.search(r'\bfill="([^"]+)"', tag)
        if fm and fm.group(1) != 'none':
            return tag.replace('stroke="null"', 'stroke="none"')
        return tag.replace('stroke="null"', 'stroke="currentColor"')
    return re.sub(r'<\w+\b[^>]*/?>', fix, svg_text)


def _recolour_svg(svg_text: str, colour: str) -> str:
    """Replace Lucide's stroke="currentColor" with the requested
    colour. Also patch any inline fill="currentColor" — a few Lucide
    glyphs (e.g. circle-dot) use fill on inner shapes.

    Two normalisations for editor-emitted SVGs:
      * Context-aware fix for ``stroke="null"`` (see
        ``_normalise_stroke_null``). Editors like the Photoshop-SVG
        pipeline emit ``null`` to mean «no stroke», but it ruins
        ``<line>`` / unfilled paths if blindly mapped to ``none``.
      * If the root ``<svg>`` lacks a ``viewBox``, derive one from its
        ``width``/``height`` attributes. fitz without a viewBox crops
        the rendered pixmap to the bounding box of geometry — for
        circle-dot that shifts the glyph off-centre because the inner
        and outer circles are concentric but the bbox happens to
        ignore the empty stroke margin. Explicit viewBox locks the
        rendered area to the editor's canvas.
    """
    out = _normalise_stroke_null(svg_text)
    out = re.sub(r'stroke="currentColor"',
                 f'stroke="{colour}"', out)
    out = re.sub(r'fill="currentColor"',
                 f'fill="{colour}"', out)

    if 'viewBox' not in out:
        m = re.search(r'<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"',
                      out)
        if m:
            w = float(m.group(1))
            h = float(m.group(2))
            # Read stroke-width from root svg (defaults to 1 per spec,
            # but Lucide/our convention is 2). Pad viewBox by stroke
            # radius + 1px safety buffer so:
            #   * stroke pixels along the edge don't get clipped,
            #   * rotated paths that orbit a pivot near the edge stay
            #     inside the rendered area.
            sw_m = re.search(r'stroke-width="([\d.]+)"', out)
            sw = float(sw_m.group(1)) if sw_m else 2.0
            pad = sw / 2.0 + 1.0
            vb_x = -pad
            vb_y = -pad
            vb_w = w + pad * 2
            vb_h = h + pad * 2
            out = re.sub(
                r'(<svg\b)',
                rf'\1 viewBox="{vb_x} {vb_y} {vb_w} {vb_h}"',
                out, count=1)
    return out


def rasterise(svg_path: str, png_path: str, size: int) -> None:
    """Render an SVG to a `size×size` transparent PNG with the glyph
    recoloured to white. Supersamples by SS× then BICUBIC-downscales
    plus a tiny Gaussian blur so edges read as soft pixel transitions
    rather than the hard pixelated stair-step LANCZOS gives.

    LANCZOS is a sharpening filter (its sinc-window kernel has negative
    lobes that boost high-frequency content), which on small UI icons
    reads as «aliased» — each pixel along an edge is either fully on or
    fully off. BICUBIC's smoother kernel + 0.4px Gaussian gives the
    same edge density but with mid-tone pixels in between, matching
    Blender's native icon rendering.
    """
    from PIL import Image, ImageFilter
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_text = f.read()
    recoloured = _recolour_svg(svg_text, STROKE_COLOR)
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False,
                                     mode="w", encoding="utf-8") as tmp:
        tmp.write(recoloured)
        tmp_path = tmp.name
    try:
        doc = fitz.open(tmp_path)
        page = doc[0]
        rect = page.rect
        if rect.width == 0 or rect.height == 0:
            raise RuntimeError(f"Empty SVG bounds: {svg_path}")
        hi = size * SS
        s = min(hi / rect.width, hi / rect.height)
        pix = page.get_pixmap(matrix=fitz.Matrix(s, s), alpha=True)
        doc.close()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    big = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    # BICUBIC with low reducing_gap delivers softer edges than LANCZOS.
    # LANCZOS sharpens via its sinc kernel's negative lobes, putting
    # mid-tone coverage almost-fully-on or almost-fully-off → reads as
    # "aliased" on stroke icons. BICUBIC's smoother kernel keeps edge
    # density but allows real middle-grey pixels along the boundary.
    # Final 1.0px Gaussian smooths the remaining diagonal stair-step.
    target = (size, size)
    small = big.resize(target, Image.BICUBIC, reducing_gap=2.0)
    small = small.filter(ImageFilter.GaussianBlur(radius=1.0))
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox = (size - small.width) // 2
    oy = (size - small.height) // 2
    canvas.paste(small, (ox, oy), small)
    canvas.save(png_path)


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    ok = 0
    missing = []
    total_outputs = 0
    for lucide_name, our_names in ICON_MAP.items():
        svg = os.path.join(DEV_DIR, lucide_name + ".svg")
        if not os.path.isfile(svg):
            missing.append(lucide_name)
            continue
        for our_name in our_names:
            png = os.path.join(OUT_DIR, our_name + ".png")
            rasterise(svg, png, SIZE)
            total_outputs += 1
        ok += 1
    print(f"baked {ok}/{len(ICON_MAP)} sources -> "
          f"{total_outputs} PNGs in {OUT_DIR}")
    if missing:
        print("missing SVGs:", ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
