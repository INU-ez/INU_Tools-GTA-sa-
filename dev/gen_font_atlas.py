"""Generate INU Floater font atlas — runs once, ships PNG + JSON.

Reads Inter.ttf, renders every glyph in our visible character set into a
single PNG atlas, and writes a JSON sidecar with per-glyph metrics
(position in atlas, bearing, advance, etc.). The addon loads the PNG as
a GPU texture and uses the JSON to look up where each character lives.

Run:
    python dev/gen_font_atlas.py

Output:
    INU_tools/data/fonts/inter_atlas.png  (RGBA8 atlas)
    INU_tools/data/fonts/inter_atlas.json (metrics)

Atlas is rendered at PX_SIZE (= 22 px) which corresponds to 11 pt at
2× DPI / pixel_size. At default DPI we sample the texture at half size
in the shader (= 11 px effective). Bigger atlas = sharper text on
hi-DPI displays, no atlas regeneration needed.
"""
from PIL import Image, ImageDraw, ImageFont
import json
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────

REPO    = Path(__file__).resolve().parent.parent
FONT    = REPO / "dev" / "Inter.ttf"
OUT_DIR = REPO / "INU_tools" / "data" / "fonts"
OUT_PNG = OUT_DIR / "inter_atlas.png"
OUT_JSON = OUT_DIR / "inter_atlas.json"

PX_SIZE = 12       # rasterise at 12 px — matches default Blender UI font
                   # at pixel_size=1.0 so the shader renders 1:1 without
                   # bilinear scale, giving us native-grade crispness.
                   # Hi-DPI users (pixel_size > 1) get bilinear upscale —
                   # still readable but slightly soft. Can bake additional
                   # sizes later if needed.
PAD     = 1        # 1 px gutter around each glyph to prevent bilinear bleed

# Character set — only what the floater actually shows
GLYPHS = (
    # ASCII printable
    "".join(chr(c) for c in range(0x20, 0x7F))
    # Cyrillic — uppercase, lowercase, Ё/ё
    + "".join(chr(c) for c in range(0x0410, 0x0450))  # А..я
    + "Ёё"
    # Box-drawing arrows we use for collapse/close glyphs
    + "▼▶►◄▲▽▷◁△×"
    # Common typography
    + "—–…«»‹›„"
)


def measure(font, ch):
    """Return per-glyph metrics. PIL exposes bbox + horizontal advance."""
    bbox = font.getbbox(ch)           # (l, t, r, b) — pixel-space mask bbox
    advance = font.getlength(ch)      # horizontal pen advance
    return bbox, advance


def pack_glyphs(font, chars):
    """Compute layout for the atlas. Naive row-packer: walks glyphs
    left-to-right, wraps to next row when current row overflows max_w.
    Returns (atlas_w, atlas_h, per_glyph_info)."""
    max_w = 512  # power-of-two width; height auto-fits glyphs
    rows = [[]]
    row_h = 0
    cur_x = PAD
    cur_y = PAD
    placements = {}
    for ch in chars:
        bbox, advance = measure(font, ch)
        l, t, r, b = bbox
        w = max(1, r - l)
        h = max(1, b - t)
        if cur_x + w + PAD > max_w:
            cur_y += row_h + PAD
            cur_x = PAD
            row_h = 0
        placements[ch] = {
            "x": cur_x,
            "y": cur_y,
            "w": w,
            "h": h,
            "ox": l,           # pen-to-glyph X offset (left bearing)
            "oy": t,           # pen-to-glyph Y offset (top, descender-aware)
            "advance": float(advance),
        }
        cur_x += w + PAD
        if h > row_h:
            row_h = h
    atlas_w = max_w
    atlas_h = cur_y + row_h + PAD
    # Round atlas_h up to next multiple of 8 for tidy texture sizes
    atlas_h = ((atlas_h + 7) // 8) * 8
    return atlas_w, atlas_h, placements


def render_atlas(font, atlas_w, atlas_h, placements):
    """Rasterise each glyph into the atlas image. Glyphs are stored in
    the ALPHA channel of an RGBA8 image — RGB is white everywhere so a
    plain texture-modulated draw in the addon picks up the correct
    shape with whatever colour the shader multiplies in."""
    img = Image.new("RGBA", (atlas_w, atlas_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    for ch, p in placements.items():
        # PIL renders at (x - bbox.left, y - bbox.top) so the glyph
        # mask fills exactly (p["x"], p["y"], p["x"]+w, p["y"]+h).
        draw.text(
            (p["x"] - p["ox"], p["y"] - p["oy"]),
            ch, font=font, fill=(255, 255, 255, 255),
        )
    return img


def main():
    if not FONT.exists():
        raise SystemExit(f"Inter.ttf not found at {FONT}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    font = ImageFont.truetype(str(FONT), PX_SIZE)
    ascent, descent = font.getmetrics()

    atlas_w, atlas_h, placements = pack_glyphs(font, GLYPHS)
    img = render_atlas(font, atlas_w, atlas_h, placements)
    img.save(OUT_PNG, optimize=True)

    metadata = {
        "font": "Inter",
        "px_size": PX_SIZE,         # raster size in pixels
        "atlas_w": atlas_w,
        "atlas_h": atlas_h,
        "ascent": ascent,           # baseline-to-top
        "descent": descent,         # baseline-to-bottom (positive)
        "line_height": ascent + descent,
        "glyphs": placements,
    }
    OUT_JSON.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {OUT_PNG} ({atlas_w}x{atlas_h}, {len(placements)} glyphs)")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
