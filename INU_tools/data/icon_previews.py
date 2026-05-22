"""Custom icon previews — exposes the Lucide-derived PNG bake under
``INU_tools/data/icons/`` as ``icon_value=N`` values usable inside any
``layout.operator(...)`` / ``layout.label(...)`` call.

Blender's UILayout has no public access to its compiled icon atlas
(see investigation in viewport_floater.py), but
``bpy.utils.previews.new()`` plus ``pcoll.load(path, 'IMAGE')`` returns
a ``ImagePreview`` whose ``icon_id`` is a valid UILayout icon_value.
This module wraps that pattern: ``register()`` populates a single
preview collection at addon load, ``get(name)`` resolves a base name
(without extension) to its icon_id, ``unregister()`` releases.

Usage from a panel::

    from .data import icon_previews
    layout.operator("foo.bar", text="X",
                    icon_value=icon_previews.get("export"))
"""
import os
import bpy
import bpy.utils.previews

_PCOLL_KEY = "inu_tools_icons"
_pcoll = None


def _icons_dir():
    """Native bake folder (UPPERCASE PNGs, resvg-based 1-px pipeline).
    The parent ``data/icons/`` Lucide bake is not loaded into the
    preview collection — N-panel uses the same native bake the floater
    uses, so visuals match across both."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "icons", "native")


def register():
    """Create the preview collection and load every PNG in
    data/icons/native/. Idempotent — safe to call multiple times.

    PNGs are stored under UPPERCASE filenames (BLENDER_ICON.png); we
    lowercase the key so callers can lookup either case without caring."""
    global _pcoll
    if _pcoll is not None:
        return
    _pcoll = bpy.utils.previews.new()
    icons_dir = _icons_dir()
    if not os.path.isdir(icons_dir):
        print(f"[INU Icons] dir missing: {icons_dir}")
        return
    loaded = 0
    for fn in sorted(os.listdir(icons_dir)):
        if not fn.lower().endswith(".png"):
            continue
        name = os.path.splitext(fn)[0].lower()
        path = os.path.join(icons_dir, fn)
        try:
            _pcoll.load(name, path, 'IMAGE')
            loaded += 1
        except Exception as e:
            print(f"[INU Icons] failed {name}: {e}")
    print(f"[INU Icons] loaded {loaded} preview icons from {icons_dir}")


def unregister():
    """Release the preview collection. Safe if already released."""
    global _pcoll
    if _pcoll is None:
        return
    try:
        bpy.utils.previews.remove(_pcoll)
    except Exception:
        pass
    _pcoll = None


def get(name):
    """Return the Blender icon_value for the named PNG, or 0 if not
    loaded. 0 is the standard "no icon" sentinel that UILayout accepts
    without erroring, so callers don't need to guard the result.

    Lookup is case-insensitive — callers can pass Blender's UPPERCASE
    enum names directly."""
    if _pcoll is None or not name:
        return 0
    p = _pcoll.get(name.lower())
    return p.icon_id if p is not None else 0
