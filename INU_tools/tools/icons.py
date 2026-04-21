# INU_tools.tools.icons — custom icon preview collection.
#
# Wraps `bpy.utils.previews` so the addon can ship its own PNG icons
# (Twemoji, CC-BY 4.0 © Twitter Inc.) alongside Blender's built-ins.
# Usage in panel draw():
#     layout.operator("gtatools.map_export",
#                     icon_value=get_icon("map"))
# or as a Label:
#     layout.label(text="Map", icon_value=get_icon("map"))

from __future__ import annotations

import os
import bpy
import bpy.utils.previews


_preview: "bpy.utils.previews.ImagePreviewCollection | None" = None


# Each entry maps an internal key → filename under data/icons/.
# Add new rows here when you drop another PNG into the folder.
_ICON_FILES = {
    "map":        "map.png",          # 🗺️
    "light":      "light.png",        # 💡
    "bone":       "bone.png",         # 🦴
    "water":      "water.png",        # 🌊
    "palette":    "palette.png",      # 🎨
    "disk":       "disk.png",         # 💾
    "explosion":  "explosion.png",    # 💥
    "clapper":    "clapper.png",      # 🎬
    "picture":    "picture.png",      # 🖼️
    "rock":       "rock.png",         # 🪨
    "roadblock":  "roadblock.png",    # 🚧
    "ruler":      "ruler.png",        # 📏
    "firework":   "firework.png",     # 🎆
    "film":       "film.png",         # 🎞️
    "train":      "train.png",        # 🚂
    "road":       "road.png",         # 🛣️
    "testtube":   "testtube.png",     # 🧪
}


def _icons_dir() -> str:
    # tools/icons.py → addon root → data/icons/
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "data", "icons"))


def get_icon(key: str) -> int:
    """Return the integer icon_id for `key`, or 0 if unknown.

    Pass the result as ``icon_value=get_icon("map")`` in layout.operator()
    / layout.label() calls. A return of 0 disables the icon, which is a
    safer fallback than raising when an addon update removes a PNG.
    """
    if _preview is None:
        return 0
    entry = _preview.get(key)
    return entry.icon_id if entry else 0


def register():
    global _preview
    if _preview is not None:
        return
    _preview = bpy.utils.previews.new()
    folder = _icons_dir()
    for key, fname in _ICON_FILES.items():
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            print(f"[INU_tools icons] missing {path}")
            continue
        try:
            _preview.load(key, path, 'IMAGE')
        except Exception as e:
            print(f"[INU_tools icons] failed to load {fname}: {e}")


def unregister():
    global _preview
    if _preview is not None:
        try:
            bpy.utils.previews.remove(_preview)
        except Exception:
            pass
        _preview = None
