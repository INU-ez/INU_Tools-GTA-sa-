# INU_tools.ops.viewport_floater
#
# Shim module — the floater framework's actual code lives in the
# `floater` package (`base`, `theme`, `gpu_shaders`, `text_atlas`,
# `widgets`, and one file per concrete floater: `info`, `ie`,
# `validation`, `lighting`, `iii`).
#
# This file's job:
#   * Re-export `GTATOOLS_OT_floater_modal/_toggle` so `__init__.py`'s
#     `from .ops.viewport_floater import ...` keeps resolving.
#   * Host the lifecycle functions (`register_floaters`,
#     `floater_cleanup`, `restore_floater_if_visible`) that need to
#     import every subclass to instantiate them; keeping these here
#     avoids a circular import (base → subclasses → base).
#
# Adding a new floater type:
#   1. Create `floater/<name>.py` with `class FooFloater(B.Floater):`.
#   2. Import it below and add a `B._floaters[...] = FooFloater()` line
#      in `register_floaters()`.

import bpy

from .floater import gpu_shaders as GS
from .floater import text_atlas as TA
from .floater import base as B
from .floater.info import InfoFloater
from .floater.ie import ImportExportFloater
from .floater.validation import ValidationFloater
from .floater.lighting import LightingFloater
from .floater.iii import IdeIplImgFloater


# ── Re-exports for __init__.py (operators registered by name there) ─
GTATOOLS_OT_floater_modal = B.GTATOOLS_OT_floater_modal
GTATOOLS_OT_floater_toggle = B.GTATOOLS_OT_floater_toggle


def register_floaters():
    """Populate B._floaters with concrete instances. Call from register()
    after the scene PropertyGroup is registered so prop names resolve."""
    B._floaters.clear()
    B._floaters['info'] = InfoFloater()
    B._floaters['ie'] = ImportExportFloater()
    B._floaters['val'] = ValidationFloater()
    B._floaters['light'] = LightingFloater()
    B._floaters['iii'] = IdeIplImgFloater()
    # Hook into Blender's undo/redo notifications so the floater
    # modal can come back if undo killed it.
    if B._floater_undo_post not in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.append(B._floater_undo_post)
    if B._floater_undo_post not in bpy.app.handlers.redo_post:
        bpy.app.handlers.redo_post.append(B._floater_undo_post)
    # Install the POST_PIXEL draw handler ONCE at register time so it
    # is permanently live for VIEW_3D draws. Without this, opening a
    # floater for the first time required Blender to first install the
    # handler (in modal.invoke) AND then flush a redraw — the two-step
    # sequence raced with Blender's own redraw flush and produced the
    # symptom where the floater only appeared on the next mouse event.
    if B._draw_handler is None:
        try:
            B._draw_handler = bpy.types.SpaceView3D.draw_handler_add(
                B._draw_callback, (), 'WINDOW', 'POST_PIXEL'
            )
        except Exception as e:
            print(f"[INU Floater] draw_handler install failed: {e}")
    # Defer GPU prewarm to after the addon finishes registering — at
    # register() time the GPU context isn't guaranteed to be ready.
    try:
        bpy.app.timers.register(B._prewarm_gpu_resources, first_interval=1.0)
    except Exception as e:
        print(f"[INU Floater] could not schedule prewarm: {e}")
    # Subscribe to workspace-change msgbus so the modal wakes up
    # the moment the user flips back to the floater's home tab
    # (Blender kills modal operators when the active screen
    # changes). Replaces the previous 0.5 s polling timer.
    B._register_workspace_msgbus()


def floater_cleanup():
    """Hard-reset all runtime state — called from unregister()."""
    if B._draw_handler is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(B._draw_handler, 'WINDOW')
        except Exception:
            pass
        B._draw_handler = None
    B._modal_running = False
    # Drop the workspace-change msgbus subscription so an addon
    # reload doesn't leave a stale notifier pointing at a
    # no-longer-registered operator.
    B._unregister_workspace_msgbus()
    # Drop the undo/redo handlers — otherwise an addon reload leaves
    # stale references that crash on next undo.
    for ho in (bpy.app.handlers.undo_post, bpy.app.handlers.redo_post):
        try:
            while B._floater_undo_post in ho:
                ho.remove(B._floater_undo_post)
        except Exception:
            pass
    B._ui_state.clear()
    for f in B._floaters.values():
        f.state.reset()
    TA._free_font_atlases()
    GS._free_icons()


def restore_floater_if_visible():
    """load_post timer: re-invoke modal if any floater was on in the
    saved scene. Searches all windows for a VIEW_3D area to invoke from.

    Clears the `B._ui_state` cache first — without that, values from
    a previous file would silently override the scene props of the
    file we just opened (floater position / visibility would all
    revert to whatever the previous session had).
    """
    try:
        # Drop the cache so `_prop()` reads fresh values from the
        # newly-loaded scene's properties. Otherwise visibility,
        # position, locked-state etc. all carry over from whatever
        # was last open in this Blender session.
        B._ui_state.clear()

        scene = bpy.context.scene
        if scene is None or not B._any_visible(scene):
            return None
        if B._modal_running:
            return None
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type != 'WINDOW':
                            continue
                        with bpy.context.temp_override(
                                window=window, area=area, region=region):
                            bpy.ops.gtatools.floater_modal('INVOKE_DEFAULT')
                        return None
    except Exception as e:
        print(f"[INU Floater] restore failed: {e}")
    return None
