# INU_tools.ops.build_library_ops — Asset Library Builder operator.
#
# Spawns a headless Blender subprocess (`blender --background --python
# scripts/build_library_worker.py`) that drains the
# `build_library_iter` generator end-to-end without UI yields. This is
# 2-5× faster than the previous in-process modal-pump approach because
# the worker has no viewport, no depsgraph propagation per asset, and
# no per-tick UI redraws. The user's main Blender stays responsive
# during the build (can keep modeling, etc.).
#
# The worker emits `__INU_JSON__{...}` lines on stdout after every
# unit of work; this operator's modal reads them via a background
# reader thread + queue and updates the progress bar / status text.
#
# Pre-requisites checked at invoke():
#   • Scene saved (cache_dir lives next to .blend — see _get_cache_dir).
#   • Game Root set in INU settings.
#   • Output Path set in INU settings.
#   • At least one .dff exists in the cache (Extract Resources must
#     have run first, otherwise the operator has nothing to classify).

import json
import os
import queue
import subprocess
import threading
import time
from typing import List, Optional, Tuple

import bpy
from bpy.props import StringProperty

from .. import T
from ..tools import compat


# Magic prefix the worker uses to emit JSON-progress lines. Anything
# else on stdout is treated as a plain log line (kept in a small ring
# buffer so we can dump it when the subprocess fails, without flooding
# the console on success).
_JSON_PREFIX = '__INU_JSON__'


def _start_worker(args: List[str]) -> Tuple[subprocess.Popen, queue.Queue]:
    """Spawn the headless Blender + worker script and return
    (Popen, stdout_queue). The reader thread pushes lines into the
    queue; main thread polls it from `modal()`. Sentinel `None` is
    pushed when the subprocess closes its stdout (process exited)."""
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # line-buffered
        # CREATE_NO_WINDOW so we don't open a console window on Windows;
        # ignored on Linux/Mac (kwarg unsupported).
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    out_queue: queue.Queue = queue.Queue()

    def _reader():
        try:
            assert proc.stdout is not None
            for raw in proc.stdout:
                out_queue.put(raw.rstrip('\n'))
        except Exception:
            pass
        finally:
            out_queue.put(None)  # sentinel

    t = threading.Thread(target=_reader, daemon=True, name='inu-worker-reader')
    t.start()
    return proc, out_queue


class GTATOOLS_OT_build_asset_library(bpy.types.Operator):
    """Собрать Blender Asset Library из извлечённых ресурсов.

    Walks every IDE in gta.dat / default.dat, classifies every cached DFF
    by category (Cars / Peds / Weapons / Map Objects per region / LOD /
    Interiors), imports each into a Collection, marks as an asset, embeds
    INU metadata (model_id, txd_name, draw_distance, ide_flags), and
    optionally renders a thumbnail. Output is a folder with one .blend
    per category plus blender_assets.cats.txt — point Blender's Asset
    Library preferences at it and you're done."""
    bl_idname = "gtatools.build_asset_library"
    bl_label = "INU: Build Asset Library"
    bl_options = {'REGISTER'}

    _timer = None
    _proc = None  # Optional[subprocess.Popen], типизация в виде комментария
    _queue = None  # Optional[queue.Queue]
    _status: dict = {}
    _log_buffer: List[str] = []
    _t_start = 0.0

    # Asset Library + custom-preview (ed.lib_id_load_custom_preview через
    # temp_override) требуют Blender 3.2+. На 2.83-3.1 кнопка неактивна.
    @classmethod
    def poll(cls, context):
        return compat.poll_version(cls, (3, 2, 0), "Asset Library Builder")

    def invoke(self, context, event):
        if not compat.supports((3, 2, 0)):
            return compat.warn_unsupported(self, "Asset Library Builder", (3, 2, 0))
        scene = context.scene
        settings = scene.inu_settings

        # Gate: this feature spawns a background Blender process. Off by
        # default — the user must opt in (see gtatools_enable_asset_builder).
        if not getattr(settings, 'gtatools_enable_asset_builder', False):
            self.report({'ERROR'}, T(
                "Сборка Asset Library запускает фоновый процесс Blender. "
                "Включи галочку «Разрешить сборку Asset Library» в настройках."))
            return {'CANCELLED'}

        if not bpy.data.filepath:
            self.report({'ERROR'}, T(
                "Сначала сохраните сцену (.blend) — кеш создаётся "
                "рядом с ней"))
            return {'CANCELLED'}

        game_root = bpy.path.abspath(settings.gtatools_game_root)
        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(
            getattr(settings, 'gtatools_library_output_path', '') or '')
        if not output_dir:
            self.report({'ERROR'}, T(
                "Укажите папку для библиотеки в INU настройках "
                "(Library Output Path)"))
            return {'CANCELLED'}

        from .. import _get_cache_dir
        cache_dir = _get_cache_dir()
        if not os.path.isdir(cache_dir):
            self.report({'ERROR'}, T(
                "Кеш пуст — сначала запустите «Извлечь ресурсы»"))
            return {'CANCELLED'}

        # Quick sanity check: at least one DFF should exist or there's
        # nothing to build.
        has_dff = False
        try:
            for fn in os.listdir(cache_dir):
                if fn.lower().endswith('.dff'):
                    has_dff = True
                    break
        except OSError:
            pass
        if not has_dff:
            self.report({'ERROR'}, T(
                "В кеше нет DFF файлов — запустите «Извлечь ресурсы»"))
            return {'CANCELLED'}

        # Collect run options from scene settings.
        no_preview = bool(getattr(
            settings, 'gtatools_library_no_preview', False))
        preview_size = int(getattr(
            settings, 'gtatools_library_preview_size', 128))
        skip_existing = bool(getattr(
            settings, 'gtatools_library_skip_existing', True))
        delete_cache = bool(getattr(
            settings, 'gtatools_library_delete_cache', False))

        # Region filter — Map-Region setting is the same one Extract
        # Resources uses, переиспользуем чтобы юзер не выбирал регион
        # дважды. ALL → no filter (build everything cache contains).
        # Иначе ограничиваем категории: regional map objects + GENERIC
        # (общие пропы) + lod. Cars/Peds/Weapons/Interiors не привязаны
        # к региону — добавляются опциональными чекбоксами в Library
        # панели (gtatools_library_include_*).
        region = getattr(settings, 'gtatools_map_region', 'ALL')
        categories_filter = ''
        if region and region != 'ALL':
            cats = [
                f'mapobjects_{region.upper()}',
                'mapobjects_GENERIC',
                'lod',
            ]
            if getattr(settings, 'gtatools_library_include_vehicles', False):
                cats.append('vehicles')
            if getattr(settings, 'gtatools_library_include_peds', False):
                cats.append('peds')
            if getattr(settings, 'gtatools_library_include_weapons', False):
                cats.append('weapons')
            if getattr(settings, 'gtatools_library_include_interiors', False):
                cats.append('mapobjects_INTERIORS')
            categories_filter = ','.join(cats)

        # Worker script ships inside the addon so it survives whatever
        # location the user installed the addon to (no `dev/` folder in
        # the distributed zip).
        worker = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'scripts', 'build_library_worker.py')
        if not os.path.isfile(worker):
            self.report({'ERROR'},
                        f"Worker script not found: {worker}")
            return {'CANCELLED'}

        # Re-use the SAME Blender executable that's running this operator
        # — guarantees the addon is registered there too (same install).
        blender_exe = bpy.app.binary_path
        if not blender_exe or not os.path.isfile(blender_exe):
            self.report({'ERROR'},
                        T("Не найден исполняемый файл Blender'а"))
            return {'CANCELLED'}

        # Полное имя модуля аддона. Legacy install → 'INU_tools',
        # extension install (4.2+) → 'bl_ext.<repo>.<addon>'. Worker
        # сам не знает — передаём своё __package__ minus '.ops'.
        addon_module = __package__.rsplit('.', 1)[0] if __package__ else 'INU_tools'

        # Scene's active game drives which .dat manifest the worker
        # parses (gta.dat / gta_vc.dat / gta3.dat). Reader logic is
        # game-agnostic per Phase 5/18/19; this just selects entry
        # points.
        from ..core import game_versions as _gv
        target_game = _gv.game_of_scene(context.scene)

        cmd = [
            blender_exe, '--background',
            '--python', worker, '--',
            '--cache', cache_dir,
            '--game-root', game_root,
            '--output', output_dir,
            '--preview-size', str(preview_size),
            '--addon-module', addon_module,
            '--game', target_game,
        ]
        if no_preview:
            cmd.append('--no-preview')
        if skip_existing:
            cmd.append('--skip-existing')
        if delete_cache:
            cmd.append('--delete-cache')
        if categories_filter:
            cmd.extend(['--categories', categories_filter])

        try:
            self._proc, self._queue = _start_worker(cmd)
        except OSError as e:
            self.report({'ERROR'}, f"Failed to spawn subprocess: {e}")
            return {'CANCELLED'}

        self._status = {}
        self._log_buffer = []
        self._t_start = time.perf_counter()

        wm = context.window_manager
        wm.progress_begin(0, 100)
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Сборка библиотеки (headless)…"))
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            self._terminate_proc()
            self._cleanup(context)
            self.report({'WARNING'}, T("Отменено"))
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        # Drain whatever the worker pushed since the last tick. Stop on
        # sentinel (None) which means stdout closed = process exited.
        proc_done = False
        try:
            while True:
                line = self._queue.get_nowait()
                if line is None:
                    proc_done = True
                    break
                if line.startswith(_JSON_PREFIX):
                    try:
                        update = json.loads(line[len(_JSON_PREFIX):])
                    except json.JSONDecodeError:
                        continue
                    if isinstance(update, dict):
                        self._status.update(update)
                else:
                    # Plain log line — keep last ~200 lines for error
                    # diagnostics, but don't echo them to the Blender
                    # console (would spam on a 13K-model build).
                    self._log_buffer.append(line)
                    if len(self._log_buffer) > 200:
                        self._log_buffer = self._log_buffer[-200:]
        except queue.Empty:
            pass

        # Update progress display from status dict.
        wm = context.window_manager
        st = self._status
        phase = st.get('phase', 'init')

        if phase == 'build':
            cat = st.get('category', '?')
            cat_done = st.get('cat_done', 0)
            cat_total = max(st.get('cat_total', 1), 1)
            pct = int(100 * cat_done / cat_total)
            wm.progress_update(pct)
            cur = st.get('current_asset', '')
            context.workspace.status_text_set(
                f"[{cat}] {cat_done}/{cat_total} {cur}")
        elif phase == 'done':
            wm.progress_update(100)
            context.workspace.status_text_set(T("Сборка завершена"))
        else:
            wm.progress_update(0)
            phase_label = {
                'init': T("Инициализация..."),
                'classify': T("Чтение IDE файлов..."),
                'scan': T("Сканирование кеша..."),
                'finalize': T("Финализация..."),
            }.get(phase, phase)
            context.workspace.status_text_set(
                f"{T('Библиотека:')} {phase_label}")

        if proc_done:
            return self._finish(context)

        return {'RUNNING_MODAL'}

    def _finish(self, context):
        rc = self._proc.poll() if self._proc else None
        if rc is None:
            # Reader saw EOF but process still running — wait briefly.
            try:
                rc = self._proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self._terminate_proc()
                rc = -1

        elapsed = time.perf_counter() - self._t_start
        success = (rc == 0)

        self._cleanup(context)

        if success:
            classified = self._status.get('classified', 0)
            cat_done = self._status.get('cat_done', 0)
            self.report({'INFO'},
                        f"{T('Библиотека собрана за')} {elapsed:.0f}s "
                        f"({classified or cat_done} {T('моделей')})")
            return {'FINISHED'}
        else:
            # Dump the last log lines so the user has something useful
            # in the console when the subprocess died.
            print("─── Build Library worker tail ─────────────────────")
            for ln in self._log_buffer[-40:]:
                print(ln)
            print("───────────────────────────────────────────────────")
            self.report({'ERROR'},
                        f"Worker exited with code {rc} — see console for log tail")
            return {'CANCELLED'}

    def _terminate_proc(self):
        proc = self._proc
        if proc is None:
            return
        try:
            proc.terminate()
            try:
                proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3.0)
        except Exception:
            pass

    def _cleanup(self, context):
        self._proc = None
        self._queue = None
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        context.workspace.status_text_set(None)


class GTATOOLS_OT_regenerate_previews(bpy.types.Operator):
    """Перегенерировать превьюшки в существующей Asset Library.

    Iterates every ``<output>/*.blend``, opens it in this Blender
    instance, re-renders thumbnails for every asset-marked collection,
    then saves the .blend back. The asset list / metadata / textures
    are untouched — only the preview pixels are refreshed. Useful for
    bumping ``preview_size`` from 128 to 256 (or vice-versa) without
    waiting through a full DFF re-import.

    Stays in-process (modal generator) — opens .blend files in the
    current session, headless subprocess would lose that scene-state
    integration with the asset browser. Speed-up isn't critical for
    preview-only refresh anyway."""
    bl_idname = "gtatools.regenerate_previews"
    bl_label = "INU: Regenerate Previews"
    bl_options = {'REGISTER'}

    _timer = None
    _gen = None
    _status: dict = {}
    _t_start = 0.0

    # См. GTATOOLS_OT_build_asset_library — те же требования 3.2+.
    @classmethod
    def poll(cls, context):
        return compat.poll_version(cls, (3, 2, 0), "Asset Library Previews")

    def invoke(self, context, event):
        if not compat.supports((3, 2, 0)):
            return compat.warn_unsupported(self, "Asset Library Previews", (3, 2, 0))
        scene = context.scene
        settings = scene.inu_settings

        # Gate: spawns a background Blender process; off by default.
        if not getattr(settings, 'gtatools_enable_asset_builder', False):
            self.report({'ERROR'}, T(
                "Регенерация превью запускает фоновый процесс Blender. "
                "Включи галочку «Разрешить сборку Asset Library» в настройках."))
            return {'CANCELLED'}

        # Opening other .blend files in this Blender session would
        # silently discard any unsaved work. Refuse rather than risk it.
        if bpy.data.is_dirty:
            self.report({'ERROR'}, T(
                "Сохрани текущую сцену — оператор открывает .blend "
                "файлы библиотеки в этом окне Blender и потеряет "
                "несохранённые изменения"))
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(
            getattr(settings, 'gtatools_library_output_path', '') or '')
        if not output_dir or not os.path.isdir(output_dir):
            self.report({'ERROR'}, T(
                "Library Output не указан или не существует"))
            return {'CANCELLED'}

        preview_size = int(getattr(
            settings, 'gtatools_library_preview_size', 128))

        from ..tools.build_library import regenerate_previews_iter

        self._status = {}
        try:
            self._gen = regenerate_previews_iter(
                library_dir=output_dir,
                status=self._status,
                preview_size=preview_size,
            )
        except FileNotFoundError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        self._t_start = time.perf_counter()

        wm = context.window_manager
        wm.progress_begin(0, 100)
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Перегенерация превью..."))
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            self._cleanup(context)
            self.report({'WARNING'}, T("Отменено"))
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        deadline = time.monotonic() + 0.05
        while time.monotonic() < deadline:
            try:
                next(self._gen)
            except StopIteration:
                self._cleanup(context)
                elapsed = time.perf_counter() - self._t_start
                self.report({'INFO'},
                            f"{T('Превью обновлены за')} {elapsed:.0f}s")
                return {'FINISHED'}
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._cleanup(context)
                self.report({'ERROR'}, f"Regenerate error: {e}")
                return {'CANCELLED'}

        wm = context.window_manager
        st = self._status
        if st.get('phase') == 'regen':
            cat = st.get('category', '?')
            cat_done = st.get('cat_done', 0)
            cat_total = max(st.get('cat_total', 1), 1)
            blend_done = st.get('blend_done', 0)
            blend_total = max(st.get('blend_total', 1), 1)
            # Outer progress (which .blend) drives the visible bar; the
            # inner per-asset count goes in the status text.
            wm.progress_update(int(100 * blend_done / blend_total))
            cur = st.get('current_asset', '')
            context.workspace.status_text_set(
                f"[{blend_done + 1}/{blend_total} {cat}] "
                f"{cat_done}/{cat_total} {cur}")
        else:
            wm.progress_update(0)
            context.workspace.status_text_set(T("Превью: готово"))

        return {'RUNNING_MODAL'}

    def _cleanup(self, context):
        gen = getattr(self, '_gen', None)
        if gen is not None:
            try:
                gen.close()
            except Exception:
                pass
            self._gen = None
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        context.workspace.status_text_set(None)


# ── Registration ───────────────────────────────────────────────────

CLASSES = (
    GTATOOLS_OT_build_asset_library,
    GTATOOLS_OT_regenerate_previews,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
