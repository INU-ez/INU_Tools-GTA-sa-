# INU_tools.ops.floater.base
#
# Foundation of the floater subsystem:
#   * Module singletons — `_floaters` registry, modal/draw bookkeeping,
#     `_ui_state` undoable-prop cache.
#   * Position constants — panel width, viewport margins, chrome buttons.
#   * Helper functions — `_invoke_operator` (deferred bpy.ops dispatch),
#     `_push_undo`, `_hit` (AABB), `_tag_redraw_view3d`.
#   * `FloaterState` — per-instance mutable runtime state.
#   * `Floater` — base class for the 5 concrete floaters; owns chrome
#     drawing, dragging, snap-to-edge, event dispatch, save/load.
#   * Modal operator + draw callback + watchdog + msgbus + undo handler
#     — single instance of each, shared across all floaters via `_floaters`.
#
# Concrete subclasses (InfoFloater, ImportExportFloater, etc.) still
# live in viewport_floater.py and inherit `B.Floater` — they will move
# to their own `floater/<name>.py` files in the next refactor step.

import time
from collections import OrderedDict

import bpy
import gpu

from ... import T
from ...tools import compat
from ...ui import layout_rules as LR
from . import theme as TH
from . import gpu_shaders as GS
from . import text_atlas as TA
from . import widgets as WG


# Offscreen window cache. Each floater renders its full content into a GPU
# offscreen once, then every frame just blits that texture (1 draw call)
# until something invalidates it (hover / content / size / scene change).
# Turns the per-frame ~140-draw-call storm per window into one textured
# quad while a window is static (the viewport-navigation case). Flip to
# False to fall back to direct per-frame drawing if anything looks off.
_OFFSCREEN_CACHE = True
# Shadow + AA fringe extend a few px beyond the panel rect — pad the
# offscreen so they aren't clipped.
_OS_PAD = 8
# ── Gamma / blend knobs for the offscreen blit — TUNE THESE BY EYE ──
# The windows render LINEAR into the offscreen (the floater shaders
# pre-linearise for Blender's linear viewport framebuffer). The blit back
# adds an extra sRGB step → too dark at 1.0. Lower brightens.
#   too DARK  → lower  (try 0.4545, then 0.4, 0.35 …)
#   too LIGHT → raise toward 1.0 (or 2.2 to darken)
_OS_BLIT_GAMMA = 1
# Blend mode for the blit. Content is premultiplied (rendered onto a
# transparent clear) → ALPHA_PREMULT is correct. If edges/shadow look
# wrong, try premult=False (straight ALPHA).
_OS_BLIT_PREMULT = True


def _ortho2d(left, right, bottom, top):
    """Pixel-space → clip-space ortho, so the existing absolute-coordinate
    draw code renders correctly into an offscreen whose viewport is
    [0..W]×[0..H] mapping the panel's screen rect."""
    from mathutils import Matrix
    m = Matrix.Identity(4)
    rl = (right - left) or 1.0
    tb = (top - bottom) or 1.0
    m[0][0] = 2.0 / rl
    m[0][3] = -(right + left) / rl
    m[1][1] = 2.0 / tb
    m[1][3] = -(top + bottom) / tb
    m[2][2] = -1.0
    return m


def _mark_all_floaters_dirty():
    for f in _floaters.values():
        f._dirty = True


# ── Module-level singletons (shared across all floater instances) ────

_floaters = OrderedDict()  # name -> Floater instance
_draw_handler = None       # single SpaceView3D POST_PIXEL handler
_kick_active = False       # guard: one _kick_redraw burst at a time
_modal_running = False     # single modal operator alive flag
_modal_last_tick = 0.0     # time.monotonic() of last modal() callback;
                           # used by the watchdog to detect when
                           # Blender silently kills the modal on
                           # screen swaps (workspace tab clicks).
_theme_fp = None           # last seen theme/UI-scale fingerprint; the
                           # palette + text metrics are recomputed ONLY
                           # when this changes (a real theme switch),
                           # never speculatively per redraw.

# Per-floater UI-state cache, keyed by (floater_name, prop_key) where
# prop_key is one of 'visible' / 'collapsed' / 'x' / 'y' / ...
#
# Blender persists these via scene props (inu_floater_*_visible / _x /
# _y / _collapsed) so they survive `.blend` reload. But scene props
# are undoable — without a Python-side cache, Ctrl+Z right after an
# operator click rolls the scene props back to pre-floater state,
# visually closing / moving / collapsing the floater. Users reported
# this as "окна иногда перемещаются или закрываются при undo".
#
# The cache holds the **live** value, which `_prop()` returns instead
# of reading the scene prop. `_set_prop()` writes both. An undo_post
# handler also re-launches the modal if the user-intended state says
# "should be visible" but the modal died during undo.
_ui_state = {}



_WIDTH = 280
# Minimum gap the floater keeps from each viewport edge so it never
# slides under Blender's own chrome (left toolbar, right N-sidebar gutter,
# or the bottom status bar). The user picked these by eye to match the
# visible widths of the surrounding UI strips on their setup.
_VIEWPORT_MARGIN_LEFT = 50
_VIEWPORT_MARGIN_RIGHT = 24
_VIEWPORT_MARGIN_TOP = 28
_VIEWPORT_MARGIN_BOTTOM = 0
_LABEL_COL_W = 90
_BTN_W = 16  # width of one chrome icon (close / collapse)

def _first_view3d_ctx():
    """Return a ``(window, area, region)`` triple for a VIEW_3D WINDOW
    region (preferring the active window), or ``(None, None, None)``.

    Operators dispatched from ``bpy.app.timers`` carry no UI window in
    ``bpy.context``. Their ``self.report()`` still reaches the Info log /
    system console, but the bottom **status-bar banner never fires** —
    that banner is drawn into ``CTX_wm_window(C)`` and there's no window
    in a timer context. Running the op under a ``temp_override`` with
    this triple gives the report a window to render its banner in,
    matching what a native panel-button click already provides."""
    wm = bpy.context.window_manager
    if wm is None:
        return None, None, None
    active = getattr(bpy.context, 'window', None)
    windows = list(wm.windows)
    if active in windows:
        windows = [active] + [w for w in windows if w != active]
    for window in windows:
        screen = getattr(window, 'screen', None)
        if screen is None:
            continue
        for area in screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for region in area.regions:
                if region.type == 'WINDOW':
                    return window, area, region
    return None, None, None


def _invoke_operator(op_idname, op_kwargs=None):
    """Invoke a Blender operator via `bpy.app.timers`, on the next
    idle tick, with INVOKE_DEFAULT.

    Why defer:
      Several operators we dispatch from floater buttons use
      `bpy.ops.object.mode_set` internally (bake / check / snap
      ops). When invoked inline from our floater_modal's event
      handler, mode_set is blocked because Blender refuses mode
      changes while another modal owns the event loop. Symptom:
      "Запечь" button consumed the click but the bake never ran.
      Deferring through a 0-interval timer hands control back to
      Blender first — by the time the operator actually invokes,
      our modal is idle again and mode_set works normally.

    Why override context:
      A timer-invoked op has no UI window in `bpy.context` — so
      `context.window` / `context.workspace` are unreliable and
      window-dependent calls (mode_set, `status_text_set`) can
      no-op. We run it under a `temp_override` with a real VIEW_3D
      window/area/region so the operator sees a proper UI context.
      (Note: this does NOT restore the colored report *banner* —
      when an op is called through `bpy.ops` from Python, Python
      owns its ReportList and Blender suppresses the banner by
      design; reports reach only the Info log / console. We do NOT
      auto-publish a generic label per button. Instead, operators
      that produce a meaningful notification — Sync/Add/Del/Check —
      call `set_floater_status` themselves with their real report
      text, so the floater strip mirrors the N-panel notifications
      and stays empty for buttons that have nothing to say.)

    Inline-dispatch operators (preset picker, V-offset edit) do
    NOT use this helper any more: they bypass `_invoke_operator`
    and manipulate state directly, so they don't need event
    context."""
    if not op_idname:
        return
    parts = op_idname.split('.')
    if len(parts) < 2:
        return
    kwargs = op_kwargs or {}

    def _run():
        global _floater_dispatch_active
        try:
            op = bpy.ops
            for p in parts:
                op = getattr(op, p)
            win, area, region = _first_view3d_ctx()
            # Mark this op as floater-originated so its report mirrors into
            # the active floater's strip (reset in finally so N-panel ops
            # that run later don't inherit the flag).
            _floater_dispatch_active = True
            try:
                if win is not None and hasattr(bpy.context, 'temp_override'):
                    with bpy.context.temp_override(window=win, area=area, region=region):
                        op('INVOKE_DEFAULT', **kwargs)
                else:
                    op('INVOKE_DEFAULT', **kwargs)
            finally:
                _floater_dispatch_active = False
        except Exception as e:
            print(f"[INU Floater] operator '{op_idname}' failed: {e}")
        return None  # one-shot

    try:
        bpy.app.timers.register(_run, first_interval=0.0)
    except Exception as e:
        print(f"[INU Floater] could not schedule '{op_idname}': {e}")


# ── Floater status strip ─────────────────────────────────────────────
# Every floater draws a one-line result strip at its bottom (added by the
# Floater base class). It mirrors what the just-run action reported —
# necessary because floaters dispatch ops via bpy.ops, where Blender
# suppresses the native report banner. The status is PER-WINDOW: a result
# routes to whichever floater the user is interacting with, so each window
# shows its own info (not a shared global message).

_status_gen = 0

# The floater the user is currently interacting with. `_handle_lmb_press`
# sets it on every press, so an action dispatched from that window (and
# its deferred operator, which runs a frame later) routes its result back
# to that same window's strip.
_active_floater = None

# True only while an operator dispatched FROM a floater button is running.
# `set_floater_status` (called by operators' report-mirror helpers) writes
# to a window's strip only when this is set — so the SAME operators
# triggered from the N-panel keep their native banner and DON'T leak into
# whatever floater happens to be active.
_floater_dispatch_active = False

# Green for an OK/INFO result (theme has _C_WARN / _C_ERROR but no «ok»).
_C_OK_STATUS = (0.45, 0.82, 0.45, 1.0)


def set_floater_status(msg, level='INFO', secs=6.0, context=None):
    """Publish a one-line *msg* to the status strip of the floater being
    interacted with (per-window) AND Blender's bottom status bar. *level*
    ∈ {INFO, WARNING, ERROR} colours the strip.

    No-op unless an operator launched from a floater button is currently
    running (`_floater_dispatch_active`) — that keeps N-panel-triggered
    reports out of the floaters.

    The in-window strip persists until that window's next action; the
    status-bar text auto-clears after *secs*, Blender-style."""
    # Mirror only reports that originate from a floater button. The same
    # operators fired from the N-panel keep their native banner and must
    # not bleed into whatever floater happens to be the active target.
    if not _floater_dispatch_active:
        return
    global _status_gen
    _status_gen += 1
    gen = _status_gen

    target = _active_floater
    if target is not None:
        try:
            target.state.status = (str(msg), level)
            target._dirty = True   # content changed → re-render offscreen
        except Exception:
            pass

    ctx = context if context is not None else bpy.context
    ws = getattr(ctx, 'workspace', None) or getattr(bpy.context, 'workspace', None)
    if ws is not None:
        try:
            ws.status_text_set(str(msg))
        except Exception:
            pass
    try:
        _tag_redraw_view3d(bpy.context)
    except Exception:
        pass

    def _clear():
        # Only the bottom status-bar text auto-clears; each floater's strip
        # keeps its own last result until that window's next action.
        if gen != _status_gen:
            return None
        try:
            w = getattr(bpy.context, 'workspace', None)
            if w is not None:
                w.status_text_set(None)
        except Exception:
            pass
        return None

    try:
        bpy.app.timers.register(_clear, first_interval=secs)
    except Exception:
        pass


# Number of text lines reserved in every floater's bottom status strip.
_STATUS_LINES = 2


def _fit_text(text, max_w):
    """Trim *text* with a trailing ellipsis so it fits within *max_w* px."""
    if TA._text_dims(text)[0] <= max_w:
        return text
    ell = "…"
    while text and TA._text_dims(text + ell)[0] > max_w:
        text = text[:-1]
    return text + ell


def _wrap_text(text, max_w, max_lines):
    """Greedy word-wrap *text* into at most *max_lines* lines that each fit
    *max_w* px. The last line is ellipsised if content still overflows.
    Splits on spaces — our messages put spaces around their « | »
    separators, so segments break cleanly."""
    words = text.split(' ')
    lines = []
    cur = ''
    for wd in words:
        trial = wd if not cur else cur + ' ' + wd
        if not cur or TA._text_dims(trial)[0] <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
            if len(lines) == max_lines:
                break
    if len(lines) < max_lines and cur:
        lines.append(cur)
    if not lines:
        return ['']
    # Anything that didn't fit → fold the remainder into the last line and
    # ellipsise it so nothing is silently dropped without a hint.
    used = ' '.join(lines)
    if used != text:
        rest = text[len(used):].strip()
        lines[-1] = _fit_text((lines[-1] + ' ' + rest).strip(), max_w)
    else:
        lines[-1] = _fit_text(lines[-1], max_w)
    return lines


def _push_undo(message):
    """Register an undo step for floater-driven prop changes that
    don't go through a real operator (toggle / slider / pipeline /
    enum-dropdown). Without this, those `setattr(...)` writes are
    invisible to Blender's undo stack — Ctrl+Z couldn't revert
    them. The companion undo_post handler restores floater UI
    state (visible / position / collapsed) from `_ui_state` so
    those don't visually move when this push triggers an undo."""
    try:
        bpy.ops.ed.undo_push(message=message)
    except Exception as e:
        print(f"[INU Floater] undo_push failed: {e}")


def _hit(mx, my, x, y, w, h):
    return x <= mx <= x + w and y <= my <= y + h


def _tag_redraw_view3d(context):
    """Tag every VIEW_3D WINDOW region across every Blender window for
    redraw. Tags both the area and the specific WINDOW region — on some
    Blender versions area.tag_redraw doesn't propagate the dirty flag
    down to the region level reliably for SpaceView3D's POST_PIXEL
    handler, which is what we register for."""
    wm = bpy.context.window_manager
    if wm is None:
        return
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            area.tag_redraw()
            for region in area.regions:
                if region.type == 'WINDOW':
                    region.tag_redraw()


def _kick_redraw():
    """Принудительно сбросить перерисовку вьюпорта через одноразовый
    таймер (0 с).

    Только `tag_redraw` НЕ перерисовывает, пока Blender не обработает
    какое-нибудь событие — отсюда баг «окно появляется только после
    движения мышью» при ПЕРВОМ открытии после запуска (cursor_warp в ту
    же точку не всегда генерит MOUSEMOVE). Таймер с интервалом 0 надёжно
    будит цикл событий и сбрасывает помеченные перерисовки."""
    global _kick_active
    if _kick_active:
        # Серия уже идёт — не плодим параллельные таймеры (меньше лишних
        # перерисовок главного потока, безопаснее на dev-сборке).
        return
    _kick_active = True
    state = {'n': 0}
    def _cb():
        global _kick_active
        try:
            _tag_redraw_view3d(bpy.context)
        except Exception:
            pass
        state['n'] += 1
        # Серия из ~6 перерисовок за ~0.18 с: один tag_redraw на первом
        # старте мог не «проявить» окно, а при открытии 2-го/3-го окна
        # серия гарантирует, что все окна перерисуются и устаканятся.
        if state['n'] >= 6:
            _kick_active = False
            return None
        return 0.03
    try:
        bpy.app.timers.register(_cb, first_interval=0.0)
    except Exception:
        _kick_active = False

# ── Per-instance runtime state ───────────────────────────────────────

class FloaterState:
    """Mutable runtime state for a single Floater instance.

    Lives on each Floater instance. Scene-persisted state (visible /
    collapsed / x / y / etc.) goes through prop_names → INUSceneSettings;
    this class only holds transient session state.
    """
    def __init__(self):
        self.drag_active = False
        self.drag_offset = (0, 0)
        self.hover_header = False
        self.hover_collapse = False
        self.hover_close = False
        self.hover_lock = False
        # Body-specific hover slots — only relevant subclasses touch them
        # but they live on the base state for simplicity. Add more if a
        # new subclass needs new hover targets.
        self.hover_triplet = None
        self.hover_button = None  # index of hovered button or None
        self.hover_toggle = None  # toggle dict ref or None
        self.hover_slider = None  # slider dict ref or None
        self.hover_enum = None    # (enum_id, item_index) or None
        self.hover_collapsible = None  # id of hovered section-header or None
        self.hover_menu = None    # int index into menus list, or None
        self.open_dropdown = None        # {'menu_id', 'anchor_rect'} or None
        self.hover_dropdown_item = None  # int index into items, or None
        # Slider drag state — captured on PRESS, released on RELEASE
        self.drag_slider = None
        self.drag_slider_start_x = 0
        self.drag_slider_start_value = 0.0
        # Inline text-edit state for numeric fields (V-offsets etc.).
        # Set when the user clicks a field that wants typing input;
        # keystrokes update `edit_buffer`, Enter commits, Esc cancels.
        # `edit_field` carries the same dict shape as a slider —
        # {'rect', 'owner', 'prop', 'min', 'max', 'is_float', 'label'}.
        self.edit_field = None
        self.edit_buffer = ''
        # InfoFloater-only: previous visibility state per affected
        # object so a second jump can restore what was hidden. Lives on
        # the base for convenience; only InfoFloater touches it.
        self.auto_changes = None
        # Last action result shown in THIS floater's bottom strip, as
        # (msg, level) or None. Per-instance so each window shows its own
        # result, not a shared global one. Persists until the next action
        # in this same floater replaces it (not cleared by reset()).
        self.status = None

    def reset(self):
        self.drag_active = False
        self.hover_header = False
        self.hover_collapse = False
        self.hover_close = False
        self.hover_lock = False
        self.hover_triplet = None
        self.hover_button = None
        self.hover_toggle = None
        self.hover_slider = None
        self.hover_enum = None
        self.hover_collapsible = None
        self.hover_menu = None
        self.open_dropdown = None
        self.hover_dropdown_item = None
        self.drag_slider = None
        self.edit_field = None
        self.edit_buffer = ''


# ── Floater base class ───────────────────────────────────────────────

class Floater:
    """Common chrome (header, drag, collapse, close) + dispatch hooks
    for subclass body content.

    Subclasses override:
      compute_body_height(context) -> int
      extend_body_layout(context, L) -> mutates L in place with body keys
      draw_body(context, L)
      handle_body_mousemove(context, L, mx, my) -> bool (any hover changed)
      handle_body_press(context, L, mx, my) -> bool (consumed)
    """

    def __init__(self, name, title, prop_names, default_pos=(40, 200),
                 width=None):
        self.name = name
        self.title = title
        # prop_names keys: 'visible', 'collapsed', 'x', 'y'
        # subclasses may add more (e.g. 'flags_expanded' for InfoFloater)
        self.prop_names = prop_names
        self.default_pos = default_pos
        # Per-instance width override — defaults to the module-level
        # _WIDTH (280 px). Floaters with denser inner widget rows can
        # bump this in their subclass __init__.
        self.width = width if width is not None else _WIDTH
        self.state = FloaterState()

    # Scene-prop accessors. Reads go through `_ui_state` first so an
    # undo that reverts the underlying scene prop doesn't visually
    # change the floater. Writes update both the cache and the scene
    # prop (so .blend save persists the latest state).

    def _prop(self, scene, key, default=None):
        ck = (self.name, key)
        if ck in _ui_state:
            return _ui_state[ck]
        name = self.prop_names.get(key)
        if name is None:
            return default
        val = getattr(scene.inu_settings, name, default)
        _ui_state[ck] = val
        return val

    def _set_prop(self, scene, key, value):
        _ui_state[(self.name, key)] = value
        name = self.prop_names.get(key)
        if name is None:
            return
        try:
            setattr(scene.inu_settings, name, value)
        except Exception as e:
            print(f"[INU Floater] _set_prop({key}) failed: {e}")

    def is_visible(self, scene):
        return bool(self._prop(scene, 'visible', False))

    def is_locked(self):
        """True when the user pinned this floater via the lock icon.
        Locked floaters block other floaters from being dragged
        through their body rect — see `_collision_adjust`.

        State lives in the scene's `inu_floater_*_locked` BoolProperty
        so it survives `.blend` save/load. `_prop` caches via
        `_ui_state` so reads are cheap."""
        try:
            return bool(self._prop(bpy.context.scene, 'locked', False))
        except Exception:
            return False

    def _center_if_at_default(self, context):
        """Reposition the floater to the centre of the active VIEW_3D
        region IF the persisted position is still at the hardcoded
        default. We use that as a sentinel for "user has never moved
        this floater" — any drag writes a non-default value, so this
        check skips itself once the user has positioned the floater
        even once."""
        try:
            cur_x = int(self._prop(context.scene, 'x', self.default_pos[0]))
            cur_y = int(self._prop(context.scene, 'y', self.default_pos[1]))
            if (cur_x != self.default_pos[0]
                    or cur_y != self.default_pos[1]):
                return  # user-positioned, leave it alone

            # Find the active VIEW_3D / WINDOW region. Falls back to
            # the first one in any window if context isn't a 3D view
            # (e.g., toggled via N-panel button while hovering a
            # different editor).
            region = context.region if (context.region
                and getattr(context.region, 'type', None) == 'WINDOW'
                and context.area and context.area.type == 'VIEW_3D'
            ) else None
            if region is None:
                for win in context.window_manager.windows:
                    for a in win.screen.areas:
                        if a.type != 'VIEW_3D':
                            continue
                        for r in a.regions:
                            if r.type == 'WINDOW':
                                region = r
                                break
                        if region is not None:
                            break
                    if region is not None:
                        break
            if region is None:
                return

            # Estimate floater height — uses `_last_h` when available
            # (set after first draw); otherwise a conservative
            # half-region height so we at least don't push it off-screen.
            h_est = getattr(self, '_last_h', None) or min(
                region.height // 2, 400)
            cx = (region.width - self.width) // 2
            cy = (region.height - h_est) // 2
            self._set_prop(context.scene, 'x', max(0, cx))
            self._set_prop(context.scene, 'y', max(0, cy))
        except Exception as e:
            print(f"[INU Floater] center failed: {e}")

    def toggle_locked(self):
        try:
            cur = self.is_locked()
            self._set_prop(bpy.context.scene, 'locked', not cur)
        except Exception as e:
            print(f"[INU Floater] toggle_locked failed: {e}")

    def toggle_visible(self, context):
        new = not self.is_visible(context.scene)
        # Center the floater in the viewport on first show this
        # session IF the saved position is still at the hardcoded
        # default. Persisted positions from a prior save (`.blend`
        # file) survive automatically — we only override when the
        # user has never dragged this floater before.
        if new:
            self._center_if_at_default(context)
        self._set_prop(context.scene, 'visible', new)
        # Workspace pinning disabled — see is_active_here(). Keep prop
        # empty so старые сохранённые .blend файлы тоже автоматически
        # «расpinиваются» при следующем toggle.
        self._set_prop(context.scene, 'workspace', "")
        # Принудительная перерисовка вьюпорта — без неё включённое окно не
        # появлялось, пока пользователь не дёрнет вьюпорт (поворот и т.п.),
        # т.к. сам тоггл не помечает VIEW_3D «грязным».
        _tag_redraw_view3d(context)

    _COLLISION_PAD = 0  # extra px around a locked floater's bbox

    def _collision_adjust(self, context, nx, ny, w, h):
        """Slide the proposed (nx, ny) drag position so this floater's
        rect doesn't overlap any LOCKED neighbour. We pick the smallest
        push along x or y per overlap — the cursor visibly skates
        along the edge of the locked floater instead of clipping
        through. Locked floaters in the same workspace only.

        Locked floaters get a `_COLLISION_PAD` (2 px) buffer on every
        side so dragged floaters maintain a small visible gap around
        them instead of butting flush against the outline."""
        pad = self._COLLISION_PAD
        for other in _floaters.values():
            if other is self or not other.is_locked():
                continue
            if not other.is_active_here(context):
                continue
            try:
                ox = int(other._prop(context.scene, 'x',
                                     other.default_pos[0])) - pad
                oy = int(other._prop(context.scene, 'y',
                                     other.default_pos[1])) - pad
                ow = other.width + 2 * pad
                oh_raw = getattr(other, '_last_h', None)
                if oh_raw is None:
                    ol = other.compute_layout(context)
                    oh_raw = ol['h']
                oh = oh_raw + 2 * pad
            except Exception:
                continue

            # AABB overlap?
            if (nx < ox + ow and nx + w > ox
                    and ny < oy + oh and ny + h > oy):
                push_right = (ox + ow) - nx
                push_left  = (nx + w) - ox
                push_up    = (oy + oh) - ny
                push_down  = (ny + h) - oy
                m = min(push_right, push_left, push_up, push_down)
                if m == push_right:
                    nx = ox + ow
                elif m == push_left:
                    nx = ox - w
                elif m == push_up:
                    ny = oy + oh
                else:
                    ny = oy - h
        return nx, ny

    def is_active_here(self, context):
        """True if the floater is marked visible in scene state.

        Removed guards:
          • Workspace pin — `bpy.context.workspace` в operator-context
            возвращает workspace панели, не active screen → false
            negatives при загрузке сохранённых .blend (state pin'нен на
            один workspace, юзер на другом → floater не рисуется).
          • OBJECT-mode-only — старые .blend часто загружаются с
            активным объектом в Edit/Sculpt/Vertex Paint mode (юзер
            именно так его сохранил). Floater тогда никогда не
            появлялся пока юзер не переключался в OBJECT manually.

        Глобальное правило (visible == True) надёжнее любых
        context-зависимых проверок.
        """
        return self.is_visible(context.scene)

    # Layout

    def _status_line_h(self):
        """Height of one wrapped text line in the status strip."""
        try:
            return int(TA._text_dims("Mg")[1]) + 7
        except Exception:
            return 16

    def _status_strip_h(self):
        """Total height the status strip adds to the body: a gap + N text
        lines (so multi-line reports like «Sync IDE: … | Sync IPL: …» fit
        instead of truncating to one line)."""
        return TH._PAD + _STATUS_LINES * self._status_line_h()

    def _panel_bbox(self, context):
        """Cheap outer rect ``(x, y, w, h)`` of the panel — props +
        ``compute_body_height`` only, WITHOUT the per-widget body layout.
        Used to reject idle mouse-moves before paying for the full
        ``compute_layout`` + hit-tests (the hot cost with many floaters)."""
        s = context.scene
        x = int(self._prop(s, 'x', self.default_pos[0]))
        y = int(self._prop(s, 'y', self.default_pos[1]))
        w = self.width
        if bool(self._prop(s, 'collapsed', False)):
            h = TH._HEADER_H
        else:
            h = TH._HEADER_H + TH._PAD * 2 + self.compute_body_height(context)
            if getattr(self, 'SHOW_STATUS_STRIP', True):
                h += self._status_strip_h()
        return x, y, w, h

    def _clear_hover(self):
        """Reset all hover slots; return True if anything was set (→ caller
        should tag a redraw so the de-hovered widget repaints)."""
        st = self.state
        had = (st.hover_header or st.hover_collapse or st.hover_close
               or st.hover_lock or st.hover_triplet is not None
               or st.hover_button is not None or st.hover_toggle is not None
               or st.hover_slider is not None or st.hover_enum is not None
               or st.hover_collapsible is not None or st.hover_menu is not None
               or st.hover_dropdown_item is not None)
        if had:
            st.hover_header = st.hover_collapse = False
            st.hover_close = st.hover_lock = False
            st.hover_triplet = st.hover_button = st.hover_toggle = None
            st.hover_slider = st.hover_enum = st.hover_collapsible = None
            st.hover_menu = st.hover_dropdown_item = None
        return had

    def compute_layout(self, context):
        # One layout pass = one compute_layout call. compute_body_height
        # and extend_body_layout both run inside it; subclasses memoise any
        # expensive tree-build against this token so it's done once, not
        # twice, per frame.
        self._layout_pass = getattr(self, '_layout_pass', 0) + 1
        s = context.scene
        x = int(self._prop(s, 'x', self.default_pos[0]))
        y = int(self._prop(s, 'y', self.default_pos[1]))
        w = self.width
        collapsed = bool(self._prop(s, 'collapsed', False))

        show_strip = getattr(self, 'SHOW_STATUS_STRIP', True)
        if collapsed:
            h = TH._HEADER_H
            body_h = 0
        else:
            body_h = TH._PAD * 2 + self.compute_body_height(context)
            if show_strip:
                # Permanently reserve a result strip (gap + N text lines) at
                # the bottom — fixed height so the panel never grows/jumps
                # when a message appears (it would shove a bottom-docked
                # floater upward otherwise).
                body_h += self._status_strip_h()
            h = TH._HEADER_H + body_h

        # Keep the panel's TOP edge anchored when content height changes
        # (collapse/expand of the floater itself or of one of its inner
        # sections). Without this, Blender's bottom-left origin means
        # the body would grow/shrink upward, jumping the title bar.
        last_h = getattr(self, '_last_h', None)
        if last_h is not None and last_h != h:
            shift = h - last_h
            y -= shift
            try:
                rh = context.region.height
                y = max(0, min(y, rh - h))
            except Exception:
                pass
            self._set_prop(s, 'y', y)
        self._last_h = h

        header_y = y + h - TH._HEADER_H
        # Chrome layout — Left: collapse arrow + title icon. Right:
        # lock + close, each filling the full header height, flush to
        # the right edge with 1 px between them.
        BTN_W = 22                # 22 px wide chrome buttons
        # Overlap by 1 — both outlines collide at the same column so
        # the visible separator is a single 1-px line (without overlap
        # we'd see 2 px: one outline pixel from each button).
        close_x = x + w - BTN_W
        lock_x  = close_x - BTN_W + 1

        # 19-px left inset so the visible chevron tip sits ~22 px from
        # the panel edge (chevron is drawn centred in a _BTN_W rect, so
        # its visible left edge is collapse_inset + (16-9)/2 = +3 in).
        collapse_inset = 19
        # title-icon nudged 1 px left so the visible gap between chevron
        # and icon tightens by 1 px (chevron rect ends at +16 inside,
        # icon rect starts at +15 → 1 px overlap on the rects but the
        # icon glyph still has space inside its rect).
        collapse_rect = (x + collapse_inset,             header_y, _BTN_W, TH._HEADER_H)
        title_icon_rect = (x + collapse_inset + _BTN_W + 1, header_y, _BTN_W, TH._HEADER_H)
        close_rect    = (close_x, header_y, BTN_W, TH._HEADER_H)
        lock_rect     = (lock_x,  header_y, BTN_W, TH._HEADER_H)
        drag_rect     = (x + collapse_inset + 2 * _BTN_W + 1, header_y,
                         lock_x - (x + collapse_inset + 2 * _BTN_W + 1), TH._HEADER_H)

        L = {
            'x': x, 'y': y, 'w': w, 'h': h,
            'header_y': header_y,
            'collapsed': collapsed,
            'close_rect': close_rect,
            'collapse_rect': collapse_rect,
            'title_icon_rect': title_icon_rect,
            'lock_rect': lock_rect,
            'drag_rect': drag_rect,
            # 8-px breathing room between header strip bottom and body
            # content top — matches the N-panel section-header gap.
            'body_top_y': header_y - 8,
        }
        if not collapsed:
            self.extend_body_layout(context, L)
            if show_strip:
                # Pinned to the panel bottom with a _PAD margin — sits below
                # whatever the subclass body laid out (the reserved extra
                # height above guarantees no overlap).
                L['_status_rect'] = (x + TH._PAD, y + TH._PAD,
                                     w - 2 * TH._PAD,
                                     _STATUS_LINES * self._status_line_h())
        return L

    def compute_body_height(self, context):
        return 0

    def extend_body_layout(self, context, L):
        pass

    def header_text(self, context):
        """Optional right-aligned status text rendered in the header
        strip alongside the × / ▼ icons. Override in subclasses; the
        default is no extra text."""
        return ""

    # Drawing

    def _draw_content(self, context, L):
        """Paint the whole window (chrome + body + status strip) at the
        layout's absolute coords. Used for direct drawing AND for rendering
        into the offscreen cache."""
        self._draw_chrome(context, L)
        if not L['collapsed']:
            self.draw_body(context, L)
            self._draw_status_strip(L)
        # NOTE: the open dropdown is NOT drawn here. It's painted directly in
        # blit_pass, on top of the blitted panel, so it can hang DOWNWARD past
        # the panel without being clipped by the offscreen buffer edge (and
        # without a per-open buffer resize that made the window vanish).

    def draw(self, context):
        """Прямая (без offscreen) однопроходная отрисовка — используется,
        когда _OFFSCREEN_CACHE выключен. При включённом offscreen
        draw_callback гоняет render_pass()+blit_pass() ДВУМЯ отдельными
        проходами по всем окнам (создание буфера нового окна больше не
        сбивает блит уже нарисованных → нет мигания при открытии)."""
        try:
            L = self.compute_layout(context)
        except Exception as e:
            print(f"[INU Floater] layout error in {self.name}: {e}")
            return
        try:
            self._draw_content(context, L)
        except Exception as e:
            print(f"[INU Floater] draw error in {self.name}: {e}")

    def render_pass(self, context):
        """Проход 1: посчитать раскладку и отрендерить в offscreen-буфер
        (БЕЗ блита). L сохраняется для blit_pass."""
        try:
            L = self.compute_layout(context)
        except Exception as e:
            print(f"[INU Floater] layout error in {self.name}: {e}")
            self._last_L = None
            return
        self._last_L = L
        try:
            self._render_offscreen(context, L)
        except Exception as e:
            print(f"[INU Floater] offscreen render ({self.name}): {e}")
            self._os = None        # blit_pass упадёт на прямую отрисовку

    def blit_pass(self, context):
        """Проход 2: блитнуть готовый offscreen-буфер. Все рендеры уже
        сделаны в проходе 1, поэтому блиты идут подряд по дефолтному
        фреймбуферу вьюпорта — без взаимного влияния окон."""
        L = getattr(self, '_last_L', None)
        if L is None:
            return
        blitted = False
        if getattr(self, '_os', None) is not None and getattr(self, '_os_blit', None):
            try:
                px, py, W, H = self._os_blit
                GS._draw_offscreen_texture(self._os.texture_color, px, py, W, H,
                                           _OS_BLIT_GAMMA, _OS_BLIT_PREMULT)
                blitted = True
            except Exception as e:
                print(f"[INU Floater] blit ({self.name}): {e}")
        if not blitted:
            # Фолбэк — прямая отрисовка этого кадра.
            try:
                self._draw_content(context, L)
            except Exception as e:
                print(f"[INU Floater] draw error in {self.name}: {e}")

        # Open dropdown drawn DIRECTLY on top of the panel (region pixel
        # coords, like the fallback path) — NOT into the cached offscreen
        # buffer. This lets a menu hang downward past the panel bottom without
        # being clipped by the buffer edge, and never resizes the buffer.
        if not L.get('collapsed') and self.state.open_dropdown is not None:
            dd = getattr(self, '_draw_open_dropdown', None)
            if dd is not None:
                try:
                    dd(context, L)
                except Exception as e:
                    print(f"[INU Floater] dropdown draw ({self.name}): {e}")

    def _render_offscreen(self, context, L):
        """Создать/переиспользовать GPU-offscreen и отрендерить в него
        содержимое окна (если «грязно» / устарело). Блит — отдельно, в
        blit_pass. Координаты блита сохраняются в self._os_blit."""
        x, y, w, h = int(L['x']), int(L['y']), int(L['w']), int(L['h'])
        M = _OS_PAD
        # Base bounds = panel + pad. An open dropdown that extends past the
        # bottom is handled by making it open UPWARD (see _dropdown_layout),
        # so it stays inside this buffer — no per-open resize (that resize
        # was making the whole window vanish when the menu opened).
        px, py = x - M, y - M
        W, H = w + 2 * M, h + 2 * M
        self._os_blit = None
        if W <= 0 or H <= 0:
            self._os = None
            return

        os = getattr(self, '_os', None)
        if os is None or getattr(self, '_os_size', None) != (W, H):
            if os is not None:
                try:
                    os.free()
                except Exception:
                    pass
            os = gpu.types.GPUOffScreen(W, H)
            self._os = os
            self._os_size = (W, H)
            self._dirty = True

        now = time.monotonic()
        last = getattr(self, '_os_last_render', 0.0)
        # Re-render on explicit invalidation (hover/content/theme/undo) or
        # as a ≤0.5 s catch-all for external changes not routed through a
        # floater event. Viewport navigation fires neither → pure blits.
        if getattr(self, '_dirty', True) or (now - last) > 0.5:
            with os.bind():
                fb = gpu.state.active_framebuffer_get()
                fb.clear(color=(0.0, 0.0, 0.0, 0.0))
                gpu.matrix.push_projection()
                gpu.matrix.push()
                try:
                    gpu.matrix.load_projection_matrix(
                        _ortho2d(px, px + W, py, py + H))
                    gpu.matrix.load_identity()
                    self._draw_content(context, L)
                finally:
                    gpu.matrix.pop()
                    gpu.matrix.pop_projection()
            self._dirty = False
            self._os_last_render = now
            _PROF['renders'] = _PROF.get('renders', 0) + 1
        else:
            _PROF['blits'] = _PROF.get('blits', 0) + 1
        self._os_blit = (px, py, W, H)

    def _draw_status_strip(self, L):
        """Bottom result strip shared by every floater — echoes the last
        action's report (status banner is suppressed for bpy.ops-dispatched
        ops, so we mirror it here). Recessed field: body fill + border,
        text colour by level; dim «—» placeholder until the first message."""
        rect = L.get('_status_rect')
        if not rect:
            return
        mx, my, mw, mh = rect
        GS._draw_widget(mx, my, mw, mh, TH._C_BG, TH._C_BG, TH._C_BORDER,
                     TH._R_BUTTON, outline_width=1.0, corner_mask=GS.CORNER_ALL)
        st = self.state.status
        line_h = self._status_line_h()
        if st is not None:
            msg, level = st
            col = {'WARNING': TH._C_WARN,
                   'ERROR': TH._C_ERROR}.get(level, _C_OK_STATUS)
            # Word-wrap across the reserved lines, top-to-bottom (GPU y is
            # up, so line 0 sits at the top of the box).
            top = my + mh
            for i, ln in enumerate(_wrap_text(msg, mw - 12, _STATUS_LINES)):
                tw, th_ = TA._text_dims(ln)
                ly = int(top - (i + 1) * line_h + (line_h - th_) / 2)
                TA._text(int(mx + 6), ly, ln, col)
        else:
            txt = "—"
            tw0, th0 = TA._text_dims(txt)
            TA._text(int(mx + (mw - tw0) / 2),
                     int(my + (mh - th0) / 2), txt, TH._C_DIM)

    def _draw_chrome(self, context, L):
        x, y, w, h = L['x'], L['y'], L['w'], L['h']
        header_y = L['header_y']
        st = self.state

        # Drop shadow under the panel — drawn first so the panel paints
        # over it, leaving the shadow visible on right/bottom edges.
        GS._draw_drop_shadow(x, y, w, h, TH._R_PANEL)

        # Header strip on top — slightly lighter colour (`_C_HEADER`,
        # taken from Blender's `wcol_regular.inner`) so the title bar
        # reads as a distinct band, matching N-panel chrome.
        # Body below — `_C_BG`. Two widgets with matching outline so
        # the join line reads as one continuous border.
        body_h = h - TH._HEADER_H
        if body_h > 0:
            # One panel-sized widget with a single outline around the
            # whole perimeter, then the header strip painted on top
            # WITHOUT its own outline so there's no internal divider
            # between header and body.
            GS._draw_widget(x, y, w, h,
                         TH._C_BG, TH._C_BG, TH._C_PANEL_BORDER, TH._R_PANEL,
                         outline_width=1.0, corner_mask=GS.CORNER_ALL)
            # Header overlay — inset 1 px on top/left/right to stay
            # inside the panel outline. Bottom touches the body so
            # the colour change reads as a band, not a separator.
            GS._draw_widget(x + 1, header_y, w - 2, TH._HEADER_H - 1,
                         TH._C_HEADER, TH._C_HEADER, TH._C_HEADER, TH._R_PANEL,
                         outline_width=0.0, corner_mask=GS.CORNER_TOP)
        else:
            # Collapsed: only the header is visible — keep it rounded
            # on all four corners.
            GS._draw_widget(x, y, w, h,
                         TH._C_HEADER, TH._C_HEADER, TH._C_PANEL_BORDER, TH._R_PANEL,
                         outline_width=1.0)

        # Collapse arrow (▼/▶) — far LEFT of the header. Inactive
        # grey by default; the chrome control isn't the primary
        # affordance of the title bar so it stays muted.
        glyph_color = TH._C_DIM
        gx, gy, gw, gh = L['collapse_rect']
        direction = 'right' if L['collapsed'] else 'down'
        # Explicit 9×5 chevron, no halo — crisp 1-px strokes with a
        # clean 1-px apex, no AA fringe widening the tip.
        GS._draw_menu_tria((gx, gy, gw, gh), glyph_color,
                           pointing=direction, width=9, height=5,
                           halo=True, apex_size=1,
                           halo_alpha=0.45, halo_clip_bbox=True)

        # Title icon — between collapse arrow and title text. Pulled
        # from `self.title_icon` (each floater subclass picks its own
        # — IE → "import", Info → "info", etc.).
        title_icon = getattr(self, 'title_icon', None)
        if title_icon and title_icon in GS._ICON_TEXTURES:
            tx_, ty_, tw_, th_ = L['title_icon_rect']
            GS._draw_icon_centered((tx_, ty_, tw_, th_), title_icon,
                                size=LR.icon_size(), tint=TH._C_TEXT)

        # Title — left-aligned at the start of the drag area, so it
        # reads next to the title icon rather than centred over an
        # imaginary midpoint. +4 px breathing room between icon and text.
        if self.title:
            dx, dy, dw, dh = L['drag_rect']
            title = WG._tr(self.title)
            tw, th = TA._text_dims(title)
            TA._text(int(dx) + 4,
                  int(dy + (dh - th) / 2),
                  title, TH._C_TEXT)

        # × close button (far RIGHT) — neutral by default, lights up
        # blue only on hover/press to signal action availability.
        cx, cy, cw, ch = L['close_rect']
        if st.hover_close:
            close_bg = TH._C_BUTTON_SEL_H
            close_color = TH._C_TEXT_SEL
        else:
            close_bg = TH._C_BUTTON
            close_color = TH._C_DIM
        GS._draw_widget(cx, cy, cw, ch, close_bg, close_bg, TH._C_BORDER,
                     TH._R_BUTTON, outline_width=1.0,
                     corner_mask=GS.CORNER_TR)
        if 'x' in GS._ICON_TEXTURES:
            GS._draw_icon_centered((cx, cy, cw, ch), 'x',
                                size=LR.icon_size(), tint=close_color)
        else:
            clw, clh = TA._text_dims("×", 11)
            TA._text(int(cx + (cw - clw) / 2),
                  int(cy + (ch - clh) / 2),
                  "×", close_color, 11)

        # Lock button — neutral by default, blue when pinned (active
        # state), brightens on hover in either case.
        is_locked = self.is_locked()
        lx, ly, lw, lh = L['lock_rect']
        if is_locked:
            lock_bg = TH._C_BUTTON_SEL_H if st.hover_lock else TH._C_BUTTON_SEL
            lock_color = TH._C_TEXT_SEL
        elif st.hover_lock:
            lock_bg = TH._C_BUTTON_H
            lock_color = TH._C_TEXT
        else:
            lock_bg = TH._C_BUTTON
            lock_color = TH._C_DIM
        GS._draw_widget(lx, ly, lw, lh, lock_bg, lock_bg, TH._C_BORDER,
                     TH._R_BUTTON, outline_width=1.0,
                     corner_mask=GS.CORNER_LEFT)
        if 'locked' in GS._ICON_TEXTURES:
            GS._draw_icon_centered((lx, ly, lw, lh), 'locked',
                                size=LR.icon_size(), tint=lock_color)
        else:
            glyph = "▶" if L['collapsed'] else "▼"
            glw, glh = TA._text_dims(glyph, 9)
            TA._text(int(gx + (gw - glw) / 2),
                  int(gy + (gh - glh) / 2),
                  glyph, glyph_color, 9)

    def draw_body(self, context, L):
        pass

    # ── Open-dropdown rendering (shared) ─────────────────────────
    #
    # Both IE and Lighting floaters render inline dropdowns anchored
    # under a "menu" button. The geometry (`L['dropdown_rect']` and
    # `L['dropdown_items']`) is built by `extend_body_layout`; this
    # base helper paints the panel + per-item rows. Subclass
    # `_draw_open_dropdown` is responsible only for resolving the
    # items list (static dict vs dynamic enum scan) and delegating
    # to `_draw_dropdown_panel`.

    def _draw_dropdown_panel(self, L, items):
        """Paint the open dropdown panel for the items the subclass
        resolved. Items are 3-tuples `(label, value, icon_name|None)`;
        a row with `label is None` is rendered as a separator line."""
        if not L.get('dropdown_rect') or not items:
            return
        dx, dy, dw, dh = L['dropdown_rect']
        rad = max(2, int(round(TH._R_BUTTON)))
        # Dark menu-back fill, flat TOP corners so the panel fuses
        # with the anchor button above (same trick enum-row uses to
        # join siblings).
        GS._draw_widget(dx, dy, dw, dh,
                     TH._C_DROPDOWN_PANEL_BG, TH._C_DROPDOWN_PANEL_BG,
                     TH._C_BORDER, rad,
                     outline_width=1.0, corner_mask=GS.CORNER_BOTTOM)

        # Optional "currently-selected value" — when set, the matching
        # item is highlighted with the same blue accent used for hover,
        # so the open dropdown shows at a glance which value is active.
        current_value = L.get('dropdown_current_value')
        for kind, idx, row_rect in L['dropdown_items']:
            if kind not in ('item', 'header') or row_rect is None:
                continue
            entry = items[idx]
            label = WG._tr(entry[0])
            icon_name = entry[2] if len(entry) > 2 else None
            rx, ry, rw, rh = row_rect
            if kind == 'header':
                # Title row — dimmed label, 1-px underline below it.
                # Geometry pinned bottom-up:
                #   y = ry + 4         → 4-px gap above row bottom
                #   y = ry + 4..5      → 1-px underline
                #   y = ry + 14        → label baseline (9-px gap above
                #                        underline top)
                # Top padding (above the label) is whatever's left of
                # the extended row height — gives the header room to
                # breathe like Blender's native menu title row.
                tcolor = TH._C_DIM
                GS._draw_rect(rx + 6, ry + 4, rw - 12, 1, TH._C_BORDER)
                TA._text(rx + 10, ry + 14, label, tcolor)
                continue
            hovered = (self.state.hover_dropdown_item == idx)
            is_active = (current_value is not None
                         and len(entry) > 1
                         and entry[1] == current_value)
            if hovered or is_active:
                # Highlight pill — fixed 18 px tall, centred in the row,
                # 3 px inset from the panel's left/right edges so it
                # reads as a button floating inside the panel rather
                # than filling the row corner-to-corner.
                hh = 18
                hi_x = dx + 3
                hi_w = dw - 6
                hi_y = ry + (rh - hh) // 2
                GS._draw_rect_rounded(hi_x, hi_y, hi_w, hh,
                                   TH._C_BUTTON_SEL,
                                   max(1, int(round(TH._R_BUTTON))))
                tcolor = TH._C_TEXT_SEL
            else:
                tcolor = TH._C_TEXT
            text_x = rx + 10
            if icon_name and icon_name in GS._ICON_TEXTURES:
                isz = LR.icon_size()
                iy = ry + (rh - isz) // 2
                GS._draw_icon((rx + 8, iy, isz, isz),
                           icon_name, tint=tcolor)
                text_x = rx + 8 + isz + 6
            _, lh = TA._text_dims(label)
            ty = ry + (rh - lh) // 2
            TA._text(text_x, ty, label, tcolor)

        # Separator lines — placed between adjacent item rects.
        for i, (kind, idx, _r) in enumerate(L['dropdown_items']):
            if kind != 'sep':
                continue
            prev_rect = next_rect = None
            for j in range(i - 1, -1, -1):
                _k, _, r2 = L['dropdown_items'][j]
                if r2 is not None:
                    prev_rect = r2
                    break
            for j in range(i + 1, len(L['dropdown_items'])):
                _k, _, r2 = L['dropdown_items'][j]
                if r2 is not None:
                    next_rect = r2
                    break
            if prev_rect is None or next_rect is None:
                continue
            mid_y = (prev_rect[1] + (next_rect[1] + next_rect[3])) // 2
            GS._draw_rect(dx + 6, mid_y, dw - 12, 1, TH._C_BORDER)

    # Event handling

    def handle_event(self, context, event):
        """Returns 'RUNNING_MODAL' if event consumed, else 'PASS_THROUGH'."""
        if not self.is_active_here(context):
            return 'PASS_THROUGH'

        st = self.state
        # Release drag — even when cursor left the viewport. Covers both
        # the header drag and any active slider drag.
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if st.drag_active or st.drag_slider is not None:
                if st.drag_slider is not None:
                    s = st.drag_slider
                    _push_undo(f"INU: adjust {s.get('label', s['prop'])}")
                st.drag_active = False
                st.drag_slider = None
                return 'RUNNING_MODAL'

        # Inline-edit keyboard capture — intercepts BEFORE the viewport
        # check so the text field can keep receiving keystrokes even
        # if the cursor briefly leaves the floater. Mirrors how
        # Blender's native float field keeps focus until Enter / Esc.
        if st.edit_field is not None:
            consumed = self._handle_edit_event(context, event)
            if consumed is not None:
                return consumed

        area = context.area
        region = context.region

        # Context fallback. When the modal is re-invoked from a
        # timer (which is how the watchdog relaunches after a
        # workspace swap kills the modal), Blender hands us events
        # with `context.area = context.region = None` and
        # `event.mouse_region_x = -1`. The modal IS receiving the
        # event — it just lost its area/region pointers. We rebuild
        # them by finding the VIEW_3D / WINDOW region under the
        # window-absolute cursor.
        if area is None or region is None:
            try:
                mx_abs = event.mouse_x
                my_abs = event.mouse_y
                for win in bpy.context.window_manager.windows:
                    for a in win.screen.areas:
                        if a.type != 'VIEW_3D':
                            continue
                        for r in a.regions:
                            if r.type != 'WINDOW':
                                continue
                            if (r.x <= mx_abs < r.x + r.width
                                    and r.y <= my_abs < r.y + r.height):
                                area = a
                                region = r
                                break
                        if area is not None:
                            break
                    if area is not None:
                        break
            except Exception:
                pass

        in_viewport = (area is not None and area.type == 'VIEW_3D'
                       and region is not None and region.type == 'WINDOW')
        if not in_viewport:
            return 'PASS_THROUGH'

        # Use raw region coords when valid, otherwise reconstruct
        # from absolute coords and our found region.
        if event.mouse_region_x >= 0 and event.mouse_region_y >= 0:
            mx, my = event.mouse_region_x, event.mouse_region_y
        else:
            mx = event.mouse_x - region.x
            my = event.mouse_y - region.y

        # Fast reject for idle mouse-move: if the cursor isn't over this
        # floater and nothing is being dragged / edited / hovered-in-a-
        # dropdown, skip the full compute_layout + per-widget hit-tests.
        # Every mouse move over the viewport otherwise pays
        # N×(temp_override + compute_layout + hover) — the dominant cost
        # when several floaters are open. Cheap bbox test instead.
        if (event.type == 'MOUSEMOVE'
                and not st.drag_active and st.drag_slider is None
                and st.open_dropdown is None and st.edit_field is None):
            try:
                bx, by, bw, bh = self._panel_bbox(context)
                m = 6
                outside = not (bx - m <= mx <= bx + bw + m
                               and by - m <= my <= by + bh + m)
            except Exception:
                outside = False   # fall through to the normal path
            if outside:
                if self._clear_hover():
                    self._dirty = True
                    _tag_redraw_view3d(context)
                return 'PASS_THROUGH'

        # Window-drag fast path: while the panel is being dragged its layout
        # doesn't change (only the origin moves), so skip the per-move
        # compute_layout + body hover-tests — reposition using the size cached
        # at drag start. This removes the dominant per-move CPU cost; the
        # viewport still has to redraw (an overlay can't move without it), but
        # the layout solver no longer re-runs on every mouse-move. Everything
        # else (clicks, hover, release, sliders, open dropdown) falls through
        # to the full path below.
        if (event.type == 'MOUSEMOVE' and st.drag_active
                and st.drag_slider is None and st.open_dropdown is None
                and getattr(st, 'drag_w', None) is not None):
            # NOTE: deliberately do NOT set self._dirty here. A pure move
            # doesn't change the panel's pixels — the cached offscreen texture
            # can just be re-blitted at the new position, skipping a full GPU
            # re-render every mouse-move. render_pass still updates the blit
            # position from the new x/y without redrawing the content.
            try:
                with bpy.context.temp_override(area=area, region=region):
                    w, h = st.drag_w, st.drag_h
                    ox, oy = st.drag_offset
                    nx = max(_VIEWPORT_MARGIN_LEFT,
                             min(mx - ox,
                                 region.width - w - _VIEWPORT_MARGIN_RIGHT))
                    ny = max(_VIEWPORT_MARGIN_BOTTOM,
                             min(my - oy,
                                 region.height - h - _VIEWPORT_MARGIN_TOP))
                    nx, ny = self._collision_adjust(bpy.context, nx, ny, w, h)
                    self._set_prop(bpy.context.scene, 'x', nx)
                    self._set_prop(bpy.context.scene, 'y', ny)
                    _tag_redraw_view3d(bpy.context)
                return 'RUNNING_MODAL'
            except Exception:
                pass   # any hiccup → fall through to the robust full path

        # Past the cheap reject → this event touches the window; its
        # appearance may change (hover highlight, click, drag), so
        # invalidate the offscreen cache to re-render this frame.
        self._dirty = True

        # Wrap downstream dispatch in a `temp_override` so anything
        # the handlers read off the context (`context.region.width`
        # for drag-clamping, `context.area.tag_redraw`, etc.) sees
        # the area/region we just resolved instead of the `None`
        # that Blender hands us after a workspace swap.
        try:
            with bpy.context.temp_override(area=area, region=region):
                L = self.compute_layout(bpy.context)

                if event.type == 'MOUSEMOVE':
                    return self._handle_mousemove(bpy.context, L, mx, my)

                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    return self._handle_lmb_press(bpy.context, L, mx, my)
        except Exception as e:
            print(f"[INU Floater] handle_event override crashed: {e}")

        return 'PASS_THROUGH'

    def _handle_edit_event(self, context, event):
        """Process events while an inline numeric field is active.
        Returns 'RUNNING_MODAL' / 'PASS_THROUGH' if the event is
        relevant to editing, or None to let the normal pipeline
        handle it.

        Numeric input rules (match Blender's native float field):
          • 0-9, period, minus → append to buffer (minus only at
            start, period only once)
          • Backspace → drop last char
          • Enter / Tab → commit + exit
          • Escape / right-mouse → cancel + exit
          • Click outside the field → commit + exit, then let the
            click through so the next widget can react"""
        st = self.state
        ef = st.edit_field
        if ef is None:
            return None
        if event.value != 'PRESS':
            return 'RUNNING_MODAL'
        t = event.type
        if t in ('ESC', 'RIGHTMOUSE'):
            self._cancel_edit(context)
            return 'RUNNING_MODAL'
        if t in ('RET', 'NUMPAD_ENTER', 'TAB'):
            self._commit_edit(context)
            return 'RUNNING_MODAL'
        if t == 'BACK_SPACE':
            if st.edit_buffer:
                st.edit_buffer = st.edit_buffer[:-1]
                _tag_redraw_view3d(context)
            return 'RUNNING_MODAL'
        if t == 'LEFTMOUSE':
            # Click — if inside the edit rect, just consume; outside,
            # commit and let the click fall through to whatever widget
            # is under the cursor (so a single click to another field
            # commits *and* enters that one).
            mx, my = event.mouse_region_x, event.mouse_region_y
            if _hit(mx, my, *ef['rect']):
                return 'RUNNING_MODAL'
            self._commit_edit(context)
            return None  # let the normal handler process the click
        # Character input via event.unicode (handles different
        # keyboard layouts correctly).
        ch = getattr(event, 'unicode', '') or ''
        if ch:
            if ch in '0123456789':
                st.edit_buffer += ch
                _tag_redraw_view3d(context)
                return 'RUNNING_MODAL'
            if ch == '-' and st.edit_buffer == '':
                st.edit_buffer = '-'
                _tag_redraw_view3d(context)
                return 'RUNNING_MODAL'
            if ch in ('.', ',') and '.' not in st.edit_buffer:
                st.edit_buffer += '.'
                _tag_redraw_view3d(context)
                return 'RUNNING_MODAL'
        # Unrecognised key while editing — consume so it doesn't
        # interfere with the modal (e.g. an unfortunate G/R hotkey
        # triggering a transform).
        return 'RUNNING_MODAL'

    def _commit_edit(self, context):
        """Parse the buffer, clamp to range, write to the bound
        property, exit edit mode. No-op if the buffer is empty."""
        st = self.state
        ef = st.edit_field
        if ef is None:
            return
        buf = st.edit_buffer.strip()
        if buf and buf not in ('-', '.', '-.'):
            try:
                val = float(buf)
                lo = ef.get('min', float('-inf'))
                hi = ef.get('max', float('inf'))
                val = max(lo, min(hi, val))
                if not ef.get('is_float', True):
                    val = int(round(val))
                setattr(ef['owner'], ef['prop'], val)
                _push_undo(f"INU: set {ef.get('label', ef['prop'])}")
            except (ValueError, Exception) as e:
                print(f"[INU Floater] edit commit failed: {e}")
        st.edit_field = None
        st.edit_buffer = ''
        _tag_redraw_view3d(context)

    def _cancel_edit(self, context):
        st = self.state
        st.edit_field = None
        st.edit_buffer = ''
        _tag_redraw_view3d(context)

    def _handle_mousemove(self, context, L, mx, my):
        st = self.state

        # Active slider drag takes priority — updates the bound property
        # from cursor delta. Subclasses just expose sliders in L, the
        # base class handles all motion/release semantics here.
        if st.drag_slider is not None:
            s = st.drag_slider
            rect = s['rect']
            slider_w = max(1, rect[2])
            span = s['max'] - s['min']
            delta_v = (mx - st.drag_slider_start_x) / slider_w * span
            new_v = st.drag_slider_start_value + delta_v
            new_v = max(s['min'], min(s['max'], new_v))
            if not s.get('is_float', True):
                new_v = int(round(new_v))
            try:
                setattr(s['owner'], s['prop'], new_v)
            except Exception as e:
                print(f"[INU Floater] slider write failed: {e}")
            _tag_redraw_view3d(context)
            return 'RUNNING_MODAL'

        was_header = st.hover_header
        was_collapse = st.hover_collapse
        was_close = st.hover_close
        was_lock = st.hover_lock

        st.hover_close = _hit(mx, my, *L['close_rect'])
        st.hover_collapse = _hit(mx, my, *L['collapse_rect'])
        st.hover_lock = _hit(mx, my, *L['lock_rect'])
        st.hover_header = _hit(mx, my, *L['drag_rect'])

        body_changed = (not L['collapsed']
                        and self.handle_body_mousemove(context, L, mx, my))

        if st.drag_active:
            ox, oy = st.drag_offset
            nx = mx - ox
            ny = my - oy
            rw = context.region.width
            rh = context.region.height
            nx = max(_VIEWPORT_MARGIN_LEFT,
                     min(nx, rw - L['w'] - _VIEWPORT_MARGIN_RIGHT))
            ny = max(_VIEWPORT_MARGIN_BOTTOM,
                     min(ny, rh - L['h'] - _VIEWPORT_MARGIN_TOP))
            # Block movement into a locked floater's body rect.
            nx, ny = self._collision_adjust(context, nx, ny,
                                            L['w'], L['h'])
            self._set_prop(context.scene, 'x', nx)
            self._set_prop(context.scene, 'y', ny)
            _tag_redraw_view3d(context)
            return 'RUNNING_MODAL'

        if (was_header != st.hover_header
                or was_collapse != st.hover_collapse
                or was_close != st.hover_close
                or was_lock != st.hover_lock
                or body_changed):
            _tag_redraw_view3d(context)
        return 'PASS_THROUGH'

    def _handle_lmb_press(self, context, L, mx, my):
        # Mark this window as the status target: any action dispatched from
        # it (and its deferred operator) routes its result to THIS window's
        # strip, not a shared global one.
        global _active_floater
        _active_floater = self
        st = self.state

        # An open subclass-managed dropdown captures ALL clicks while
        # visible: items fire on click, anything else closes the
        # dropdown. Without this, clicks outside the floater body would
        # leak through to the viewport while a dropdown is still drawn.
        if getattr(st, 'open_dropdown', None) is not None:
            self.handle_body_press(context, L, mx, my)
            _tag_redraw_view3d(context)
            return 'RUNNING_MODAL'

        # Close
        if _hit(mx, my, *L['close_rect']):
            self._set_prop(context.scene, 'visible', False)
            _tag_redraw_view3d(context)
            return 'RUNNING_MODAL'

        # Lock toggle — pins/unpins the floater so other floaters
        # can't be dragged through its body.
        if _hit(mx, my, *L['lock_rect']):
            self.toggle_locked()
            _tag_redraw_view3d(context)
            return 'RUNNING_MODAL'

        # Collapse
        if _hit(mx, my, *L['collapse_rect']):
            self._set_prop(context.scene, 'collapsed',
                           not self._prop(context.scene, 'collapsed', False))
            # Высота тела резко меняется → инвалидируем offscreen-кэш и
            # дёргаем немедленную перерисовку, иначе окно «пропадает» до
            # срабатывания watchdog (~2с).
            self._dirty = True
            _mark_all_floaters_dirty()
            _tag_redraw_view3d(context)
            _kick_redraw()
            return 'RUNNING_MODAL'

        if not L['collapsed']:
            # Generic slider hit-test — if the subclass exposed any
            # sliders in L['sliders'], grab the first one under cursor.
            for s in L.get('sliders', ()):
                if _hit(mx, my, *s['rect']):
                    try:
                        cur = float(getattr(s['owner'], s['prop']))
                    except Exception:
                        cur = float(s.get('min', 0))
                    st.drag_slider = s
                    st.drag_slider_start_x = mx
                    st.drag_slider_start_value = cur
                    return 'RUNNING_MODAL'

            # Generic toggle hit-test — subclass exposed L['toggles'].
            # Each toggle: {'rect', 'owner', 'prop'}
            for t in L.get('toggles', ()):
                if _hit(mx, my, *t['rect']):
                    try:
                        cur = bool(getattr(t['owner'], t['prop']))
                        setattr(t['owner'], t['prop'], not cur)
                        _push_undo(f"INU: toggle {t.get('label', t['prop'])}")
                    except Exception as e:
                        print(f"[INU Floater] toggle write failed: {e}")
                    _tag_redraw_view3d(context)
                    return 'RUNNING_MODAL'

            # Subclass-specific clicks (triplet, flags, action buttons,
            # dropdown menus). Must tag a redraw because the click may
            # have mutated draw-relevant state (e.g. opening an inline
            # dropdown) without touching any of the generic toggle /
            # slider paths above that tag redraw themselves.
            if self.handle_body_press(context, L, mx, my):
                _tag_redraw_view3d(context)
                return 'RUNNING_MODAL'

        # Whole-panel drag — by the time we get here, all interactive
        # widgets (close/lock/collapse, sliders, toggles, subclass
        # buttons) already had their chance to consume the click and
        # return early. So any LMB-press on the remaining panel area
        # (header gaps + label columns + body whitespace) starts a drag.
        if _hit(mx, my, L['x'], L['y'], L['w'], L['h']):
            st.drag_active = True
            st.drag_offset = (mx - L['x'], my - L['y'])
            # Cache the panel size so the drag fast-path in modal() can
            # reposition without a full compute_layout every mouse-move.
            st.drag_w = L['w']
            st.drag_h = L['h']
            return 'RUNNING_MODAL'
        return 'PASS_THROUGH'

    def handle_body_mousemove(self, context, L, mx, my):
        return False

    def handle_body_press(self, context, L, mx, my):
        return False



# ── Draw callback + modal + toggle operator (shared) ─────────────────

def _theme_fingerprint(context):
    """Cheap signature of Blender's theme + UI scale. Compared each frame
    so the (costly) palette/text recompute runs ONLY on a real theme
    switch. A handful of representative colours change together whenever
    the user picks another theme, so this catches switches without
    reading every wcol_* slot every frame."""
    try:
        prefs = context.preferences
        ui = prefs.themes[0].user_interface
        return (
            tuple(ui.wcol_regular.inner),
            tuple(ui.wcol_regular.text),
            tuple(ui.wcol_tool.inner),
            tuple(ui.wcol_box.inner),
            tuple(ui.wcol_menu_back.inner),
            round(prefs.view.ui_scale, 4),
        )
    except Exception:
        return None


_PROF = {'frames': 0, 'draw': 0.0, 'max': 0.0, 'per': {}, 'last': 0.0,
         'renders': 0, 'blits': 0}


def _prof_flush():
    """Print a floater-cost summary once per second, then reset counters."""
    P = _PROF
    now = time.monotonic()
    if now - P['last'] < 1.0:
        return
    n = P['frames']
    if n <= 0:
        P['last'] = now
        return
    from . import gpu_shaders as _GS
    from . import text_atlas as _TA
    bs, gs = _GS._BATCH_STATS, _TA._GLYPH_STATS
    avg_ms = P['draw'] / n * 1000.0
    # Per-window average draw time, slowest first.
    per = sorted(P['per'].items(), key=lambda kv: -kv[1])
    per_str = ", ".join(f"{nm} {t / n * 1000.0:.2f}ms" for nm, t in per)

    def _bk(hit, miss):
        tot = hit + miss
        return f"{tot / n:.0f}/frame (miss {miss / n:.1f})"

    renders = P.get('renders', 0)
    blits = P.get('blits', 0)
    print(f"[FLOATER PROF] {n} fps-frames | draw avg {avg_ms:.2f}ms "
          f"max {P['max'] * 1000.0:.2f}ms | windows: {per_str or '—'}")
    print(f"[FLOATER PROF]   offscreen: {renders / n:.1f} re-renders/frame, "
          f"{blits / n:.1f} blits/frame "
          f"(blits = cached, cheap; re-renders = full draw)")
    print(f"[FLOATER PROF]   batches — widget {_bk(bs['w_hit'], bs['w_miss'])}, "
          f"glyph {_bk(gs['hit'], gs['miss'])}, "
          f"icon {_bk(bs['i_hit'], bs['i_miss'])}, "
          f"fan {_bk(bs['f_hit'], bs['f_miss'])}")

    P['frames'] = 0
    P['draw'] = 0.0
    P['max'] = 0.0
    P['per'] = {}
    P['last'] = now
    P['renders'] = 0
    P['blits'] = 0
    for k in bs:
        bs[k] = 0
    gs['hit'] = 0
    gs['miss'] = 0


def _draw_callback():
    """POST_PIXEL draw hook — runs on EVERY viewport redraw.

    Hot path: keep this O(1) when no floater is visible. The earlier
    version unconditionally refreshed theme colors, reloaded icons,
    and ran the watchdog every tick, plus printed debug lines on a
    1-per-second cadence — combined with Blender's 60+ FPS redraw
    rate that made simple operations (adding a 2DFX empty, etc.) lag
    visibly because the user wasn't using any floater at all."""
    ctx = bpy.context
    scene = ctx.scene
    # Cheap visibility gate — skip ALL per-frame work when no floater
    # is on. `_any_visible` is a 5-attr prop read; if every floater's
    # `_visible` prop is False we bail immediately.
    if scene is None or not _any_visible(scene):
        return

    # Re-sync palette + text metrics with Blender's theme ONLY when the
    # theme actually changed. Recomputing dozens of colours every redraw
    # (60+ fps) was pure waste — the theme almost never changes. We read a
    # cheap fingerprint (a handful of theme colours + ui_scale) each frame
    # and only pay for the full recompute when it differs. Instant on a
    # real theme switch, ~free otherwise.
    global _theme_fp
    _fp = _theme_fingerprint(ctx)
    if _fp is not None and _fp != _theme_fp:
        _theme_fp = _fp
        try:
            TH._apply_theme()
        except Exception:
            pass
        try:
            TA._refresh_ui_text_style()
        except Exception:
            pass
        # Palette / metrics changed → every window must re-render its cache.
        _mark_all_floaters_dirty()
    # Defensive icon load — prewarm timer is supposed to populate this,
    # but in some Blender contexts (background, headless, GPU not ready
    # at +1s after register) it can no-op. GS._load_icons() short-circuits
    # if already populated, so subsequent draws pay only a dict-truthy
    # check.
    if not GS._ICON_TEXTURES:
        try:
            GS._load_icons()
        except Exception as e:
            print(f"[INU Floater] icon load failed in draw: {e}")
    # Watchdog — detect a silently-killed modal (workspace tab
    # click triggers a screen swap which Blender uses to kill modal
    # operators without giving them a chance to clean up). If
    # nothing has called modal() in the last 0.5 s but
    # `_modal_running` is still True, the modal is a ghost; reset
    # the flag and schedule a re-invoke. We can't call bpy.ops from
    # a draw handler directly, hence the 0-interval timer.
    global _modal_running
    try:
        # Порог 2.0 с (было 0.5). Реже ложно считаем простаивавшую модалку
        # «мёртвой» → реже дёргаем перезапуск модал-оператора. Перезапуск
        # bpy.ops во время взаимодействия пользователя с UISlider'ом на
        # dev-сборке Blender может расшатывать UI — поэтому осторожнее.
        # Реальную смерть модалки (смена воркспейса) ловит msgbus сразу.
        if _modal_running and (time.monotonic() - _modal_last_tick) > 2.0:
            _modal_running = False
        if not _modal_running:
            if not bpy.app.timers.is_registered(_relaunch_modal_timer):
                bpy.app.timers.register(
                    _relaunch_modal_timer, first_interval=0.0)
    except Exception as e:
        print(f"[INU Floater] watchdog crashed: {e}")

    # Profiler — gated by the «Профайлер» checkbox. Times each window's
    # draw and, once per second, prints avg/max frame cost, per-window
    # breakdown, and batch hits/misses (a MISS = a freshly built GPU
    # buffer — the expensive case; lots of misses on a still viewport
    # means something is invalidating the geometry caches).
    _prof_on = False
    try:
        _prof_on = bool(getattr(scene.inu_settings, 'gtatools_profile_enabled', False))
    except Exception:
        pass

    # Активные окна в этой области.
    active = [(name, f) for name, f in _floaters.items() if f.is_active_here(ctx)]

    def _draw_active(timed):
        # Два прохода при offscreen: сначала рендер ВСЕХ буферов, затем блит
        # всех. Так создание буфера только что открытого окна не сбивает
        # блит уже нарисованных (это и давало мигание). Без offscreen —
        # обычная однопроходная прямая отрисовка.
        total = 0.0
        if _OFFSCREEN_CACHE:
            for name, f in active:
                try:
                    if timed:
                        _t0 = time.perf_counter()
                    f.render_pass(ctx)
                    if timed:
                        _dt = time.perf_counter() - _t0
                        _PROF['per'][name] = _PROF['per'].get(name, 0.0) + _dt
                        total += _dt
                except Exception:
                    import traceback as _tb
                    print(f"[INU Floater] render('{name}') crashed:")
                    _tb.print_exc()
            for name, f in active:
                try:
                    if timed:
                        _t0 = time.perf_counter()
                    f.blit_pass(ctx)
                    if timed:
                        _dt = time.perf_counter() - _t0
                        _PROF['per'][name] = _PROF['per'].get(name, 0.0) + _dt
                        total += _dt
                except Exception:
                    import traceback as _tb
                    print(f"[INU Floater] blit('{name}') crashed:")
                    _tb.print_exc()
        else:
            for name, f in active:
                try:
                    if timed:
                        _t0 = time.perf_counter()
                    f.draw(ctx)
                    if timed:
                        _dt = time.perf_counter() - _t0
                        _PROF['per'][name] = _PROF['per'].get(name, 0.0) + _dt
                        total += _dt
                except Exception:
                    import traceback as _tb
                    print(f"[INU Floater] draw('{name}') crashed:")
                    _tb.print_exc()
        return total

    if not _prof_on:
        _draw_active(timed=False)
        return

    _frame_total = _draw_active(timed=True)
    _PROF['draw'] += _frame_total
    if _frame_total > _PROF['max']:
        _PROF['max'] = _frame_total
    _PROF['frames'] += 1
    _prof_flush()


def _relaunch_modal_timer():
    """One-shot timer scheduled from `_draw_callback` when the
    watchdog detects a dead modal.

    The relaunch MUST happen with a valid window+area+region in
    `bpy.context` — modal_handler_add attaches the modal to the
    active window's event queue. Without an explicit override the
    timer callback's bpy.context can have window=None and the
    modal returns RUNNING_MODAL but never receives any event.
    Symptom we hit on workspace switch: floater drawn, watchdog
    relaunches, status says RUNNING_MODAL but clicks/mousemove
    don't reach `modal()`."""
    try:
        scene = getattr(bpy.context, 'scene', None)
        if scene is None or not _any_visible(scene) or _modal_running:
            return None

        # Find the first VIEW_3D area in any window and use it as
        # the override target.
        wm = bpy.context.window_manager
        for window in wm.windows:
            for area in window.screen.areas:
                if area.type != 'VIEW_3D':
                    continue
                for region in area.regions:
                    if region.type != 'WINDOW':
                        continue
                    try:
                        with bpy.context.temp_override(
                                window=window, area=area, region=region):
                            bpy.ops.gtatools.floater_modal('INVOKE_DEFAULT')
                    except Exception as e:
                        print(f"[INU Floater] override relaunch failed: {e}")
                    return None
        # No 3D view found anywhere — fall back to plain invoke
        try:
            bpy.ops.gtatools.floater_modal('INVOKE_DEFAULT')
        except Exception as e:
            print(f"[INU Floater] plain relaunch failed: {e}")
    except Exception:
        pass
    return None  # one-shot


def _any_visible(scene):
    """Visibility intent only — used by the modal to decide whether
    to stay alive. Does NOT factor workspace because the modal must
    keep running so it can pick the floater up again when the user
    flips back to its workspace."""
    return any(f.is_visible(scene) for f in _floaters.values())


class GTATOOLS_OT_floater_modal(bpy.types.Operator):
    """Фоновый модал — диспатчит события на все видимые floater'ы"""
    bl_idname = "gtatools.floater_modal"
    bl_label = "INU Floater (modal)"
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        global _modal_last_tick
        import time as _time
        _modal_last_tick = time.monotonic()
        if not _any_visible(context.scene):
            return self._end(context)

        # Kick-burst: пока активен стартовый wm-таймер, на каждый TIMER
        # принудительно перерисовываем вьюпорт. Это надёжно «проявляет»
        # окно сразу при первом открытии после запуска (tag_redraw/таймер
        # приложения/cursor_warp по отдельности VIEW_3D не будили). После
        # нескольких тиков таймер снимаем — постоянной нагрузки нет.
        if event.type == 'TIMER' and getattr(self, '_kick_timer', None) is not None:
            self._kick_ticks += 1
            _tag_redraw_view3d(context)
            if self._kick_ticks >= 8:
                try:
                    context.window_manager.event_timer_remove(self._kick_timer)
                except Exception:
                    pass
                self._kick_timer = None
            return {'PASS_THROUGH'}

        # First-match-wins event dispatch. _floaters insertion order is
        # also the draw order — later entries draw on top of earlier
        # ones — so we iterate REVERSED here, letting the topmost
        # floater consume the click before the ones underneath.
        #
        # On a click that triggers drag (LMB PRESS), we also "raise"
        # the clicked floater to the top of the stack via move_to_end
        # so it stays on top for future interactions, matching native
        # window-manager click-to-front behaviour.
        consuming_name = None
        for name, f in reversed(_floaters.items()):
            result = f.handle_event(context, event)
            if result == 'RUNNING_MODAL':
                consuming_name = name
                break
        if (consuming_name is not None
                and event.type == 'LEFTMOUSE'
                and event.value == 'PRESS'):
            try:
                _floaters.move_to_end(consuming_name)
            except KeyError:
                pass
        return {'RUNNING_MODAL'} if consuming_name else {'PASS_THROUGH'}

    def invoke(self, context, event):
        global _modal_running, _modal_last_tick
        import time as _time
        if _modal_running:
            return {'CANCELLED'}
        _modal_running = True
        _modal_last_tick = time.monotonic()
        context.window_manager.modal_handler_add(self)
        # Короткий wm-таймер: даёт модалке несколько TIMER-тиков сразу
        # после старта → гарантированная перерисовка вьюпорта на первом
        # открытии окна. Снимается после нескольких тиков (см. modal()).
        self._kick_ticks = 0
        self._kick_timer = None
        try:
            self._kick_timer = context.window_manager.event_timer_add(
                0.02, window=context.window)
        except Exception:
            pass
        _tag_redraw_view3d(context)
        _kick_redraw()
        return {'RUNNING_MODAL'}

    def _end(self, context):
        global _modal_running
        _modal_running = False
        kt = getattr(self, '_kick_timer', None)
        if kt is not None:
            try:
                context.window_manager.event_timer_remove(kt)
            except Exception:
                pass
            self._kick_timer = None
        for f in _floaters.values():
            f.state.reset()
        _tag_redraw_view3d(context)
        return {'CANCELLED'}


class GTATOOLS_OT_floater_toggle(bpy.types.Operator):
    """Показать / скрыть плавающее окно INU Floater"""
    bl_idname = "gtatools.floater_toggle"
    bl_label = "INU Floater"
    bl_options = {'REGISTER'}

    floater_name: bpy.props.StringProperty(
        name="Floater",
        description="Floater instance name (e.g. 'info', 'tools'). "
                    "Comma-separated to toggle several at once.",
        default='info',
    )

    # Плавающие окна построены на modal/timer + context.temp_override —
    # требуют Blender 3.2+. На 2.83-3.1 кнопка неактивна с подсказкой.
    @classmethod
    def poll(cls, context):
        return compat.poll_version(cls, (3, 2, 0), "INU Floater")

    def execute(self, context):
        global _modal_last_tick
        if not compat.supports((3, 2, 0)):
            return compat.warn_unsupported(self, "INU Floater", (3, 2, 0))
        # Split on commas so a single button can flip multiple floaters
        # (used to keep production + sandbox lighting windows in sync).
        names = [n.strip() for n in self.floater_name.split(',') if n.strip()]
        any_found = False
        for nm in names:
            f = _floaters.get(nm)
            if f is None:
                continue
            f.toggle_visible(context)
            any_found = True
        if not any_found:
            self.report({'WARNING'},
                        f"Unknown floater '{self.floater_name}'")
            return {'CANCELLED'}
        # Модалка ЖИВА (пользователь только что кликнул) — освежаем метку,
        # иначе перерисовка от этого toggle разбудит watchdog в
        # _draw_callback, тот сочтёт простаивавшую модалку «мёртвой» и
        # перезапустит её → ВСЕ окна ре-рендерятся.
        _modal_last_tick = time.monotonic()
        # Обходной путь от «мигания»: при открытии/закрытии окна метим ВСЕ
        # окна «грязными» → в той же перерисовке все рендерят свои буферы
        # заново и блитятся вместе (свежими). Так ни одно окно не пропадает
        # на кадр из-за устаревшей/невалидной offscreen-текстуры.
        _mark_all_floaters_dirty()
        # Start the shared modal lazily on first visible floater
        if _any_visible(context.scene) and not _modal_running:
            try:
                bpy.ops.gtatools.floater_modal('INVOKE_DEFAULT')
            except Exception as e:
                print(f"[INU Floater] modal invoke failed: {e}")
        _tag_redraw_view3d(context)
        # Таймер-пинок: гарантированно перерисовать на первом открытии
        # после запуска (когда cursor_warp не будит цикл событий).
        _kick_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        result = self.execute(context)
        # Blender doesn't flush our viewport's tag_redraw until SOME
        # event ticks the event loop — without one, a user clicking the
        # sidebar toggle would see the floater appear only on their
        # next mouse move. Warping the cursor to its current position
        # emits a synthetic MOUSEMOVE event that wakes the event loop
        # without visually moving the cursor.
        if context.window is not None:
            try:
                context.window.cursor_warp(event.mouse_x, event.mouse_y)
            except Exception:
                pass
        return result


# ── Public API used by __init__.py ───────────────────────────────────

def _prewarm_gpu_resources():
    """Pre-build the SDF / text shaders and the glyph atlases for the
    pixel sizes we'll actually use (10, 11, 12 pt at the system's UI
    scale). Without this the first floater open triggers all of:
    shader compile, GPUOffScreen creation, and 3× atlas bakes, which
    together stalled the UI for ~1-2 seconds. Doing it from a one-shot
    timer at register time pushes that cost into the Blender-already-
    starting window where the user expects load delay."""
    try:
        TA._refresh_ui_text_style()
        GS._get_widget_shader()
        TA._get_text_shader()
        GS._get_icon_shader()
        for pt in (10, 11, 12):
            TA._get_atlas(TA._text_px_size(pt))
        GS._load_icons()
    except Exception as e:
        print(f"[INU Floater] prewarm failed: {e}")
    return None  # one-shot


_MSGBUS_OWNER = object()


def _on_workspace_change():
    """Fires immediately when `bpy.context.window.workspace` changes
    (any time the user clicks a workspace tab). Drops the
    `_modal_running` guard and force-resets the flag because Blender
    sometimes kills the modal during a screen swap without giving
    our `_end()` a chance to run — `_modal_running` would otherwise
    stay True forever and block re-invoke."""
    global _modal_running
    try:
        scene = getattr(bpy.context, 'scene', None)
        if scene is not None and _any_visible(scene):
            _modal_running = False
            try:
                bpy.ops.gtatools.floater_modal('INVOKE_DEFAULT')
            except Exception as e:
                print(f"[INU Floater] msgbus relaunch failed: {e}")
        _tag_redraw_view3d(bpy.context)
    except Exception as e:
        print(f"[INU Floater] _on_workspace_change crashed: {e}")


def _register_workspace_msgbus():
    """Subscribe to `Window.workspace` changes so we can wake the
    modal up instantly when the user flips back to the floater's
    home workspace, instead of polling every 0.5 s."""
    try:
        bpy.msgbus.subscribe_rna(
            key=(bpy.types.Window, 'workspace'),
            owner=_MSGBUS_OWNER,
            args=(),
            notify=_on_workspace_change,
            options={'PERSISTENT'},
        )
    except Exception as e:
        print(f"[INU Floater] msgbus subscribe failed: {e}")


def _unregister_workspace_msgbus():
    try:
        bpy.msgbus.clear_by_owner(_MSGBUS_OWNER)
    except Exception:
        pass


@bpy.app.handlers.persistent
def _floater_undo_post(scene, depsgraph=None):
    """After any undo/redo:
      1. Re-write floater UI-state scene props from `_ui_state` so
         the floater doesn't appear to move/close/un-collapse.
      2. Force a depsgraph update + viewport redraw so the data
         change the undo reverted (e.g. an object's transform) is
         immediately visible. Without (2) the modal that's still
         running seems to prevent Blender's normal post-undo
         re-evaluation from flushing — symptom was "Ctrl+Z does
         nothing until I move the model".
      3. Restart the modal if undo killed it.
    """
    global _modal_running
    # Undo/redo may have changed anything the windows display → re-render.
    _mark_all_floaters_dirty()
    try:
        wants_visible = False
        for (name, key), val in list(_ui_state.items()):
            f = _floaters.get(name)
            if f is None:
                continue
            prop_name = f.prop_names.get(key)
            if prop_name is None:
                continue
            try:
                cur = getattr(scene.inu_settings, prop_name, None)
                if cur != val:
                    setattr(scene.inu_settings, prop_name, val)
            except Exception:
                pass
            if key == 'visible' and bool(val):
                wants_visible = True

        # Force depsgraph eval + viewport refresh.
        #
        # `view_layer.update()` alone is unreliable while our modal
        # is active — Blender defers the post-undo re-evaluation to
        # the next user event ("Ctrl+Z does nothing until I move
        # the model"). We dirty the transform channels manually on
        # active + selected objects by writing each property back to
        # itself: `obj.location = obj.location` is a no-op on value
        # but bumps the channel version in the depsgraph, forcing
        # re-eval this frame.
        #
        # CRITICAL: only direct RNA properties (location,
        # rotation_euler, rotation_quaternion, scale) — NOT
        # `matrix_world`. `matrix_world` is a lazy cache that
        # hasn't been refreshed yet at this point in the handler;
        # writing its stale value back overwrites the just-restored
        # underlying channels and destroys the undo (this was a real
        # bug we hit earlier).
        try:
            ctx = bpy.context
            touched = set()
            ao = getattr(ctx, 'active_object', None)
            if ao is not None:
                touched.add(ao)
            for o in (getattr(ctx, 'selected_objects', None) or ()):
                touched.add(o)
            for o in touched:
                try:
                    o.location = o.location
                    if o.rotation_mode == 'QUATERNION':
                        o.rotation_quaternion = o.rotation_quaternion
                    elif o.rotation_mode == 'AXIS_ANGLE':
                        o.rotation_axis_angle = o.rotation_axis_angle
                    else:
                        o.rotation_euler = o.rotation_euler
                    o.scale = o.scale
                except Exception:
                    pass
            vl = ctx.view_layer
            if vl is not None:
                vl.update()
        except Exception:
            pass

        if wants_visible and not _modal_running:
            try:
                bpy.ops.gtatools.floater_modal('INVOKE_DEFAULT')
            except Exception as e:
                print(f"[INU Floater] undo-restart failed: {e}")
        _tag_redraw_view3d(bpy.context)
    except Exception as e:
        print(f"[INU Floater] undo_post handler crashed: {e}")
