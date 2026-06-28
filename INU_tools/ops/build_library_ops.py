# INU_tools.ops.build_library_ops — Asset Library Builder operator.
#
# Drives the `build_library_iter` generator IN-PROCESS via a modal timer
# pump: each TIMER tick advances the generator for a short time-slice,
# repaints the progress bar / status text, then yields control back to
# Blender so the UI stays responsive. There is NO background Blender
# subprocess and NO reader thread — extensions.blender.org does not
# accept addons that spawn looping OS threads or force-enable the addon
# in / manipulate the python path of another Blender process.
#
# The build is DESTRUCTIVE to the current session: `build_library_iter`
# wipes scene data (`reset_blend_state`) and `save_as_mainfile`s each
# category .blend out. So this operator:
#   • requires the asset-builder opt-in toggle (off by default),
#   • requires the scene already saved AND with no unsaved changes,
#   • reloads the user's original .blend when the build finishes (or is
#     cancelled / errors) so they get their scene back.
#
# Pre-requisites checked at invoke():
#   • Scene saved + clean (cache_dir lives next to the .blend).
#   • Game Root set in INU settings.
#   • Output Path set in INU settings.
#   • At least one .dff exists in the cache (Extract Resources must have
#     run first, otherwise there's nothing to classify).

import os
import time

import bpy

from .. import T
from ..tools import compat


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
    _gen = None
    _status: dict = {}
    _t_start = 0.0
    _orig_filepath = ""

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

        # Gate: the build rebuilds the current session (imports thousands
        # of models and resets scene data). Off by default — the user
        # must opt in (see gtatools_enable_asset_builder).
        if not getattr(settings, 'gtatools_enable_asset_builder', False):
            self.report({'ERROR'}, T(
                "Сборка Asset Library пересобирает текущую сцену "
                "(импортирует тысячи моделей и очищает данные сцены). "
                "Включи галочку «Разрешить сборку Asset Library» в настройках."))
            return {'CANCELLED'}

        if not bpy.data.filepath:
            self.report({'ERROR'}, T(
                "Сначала сохраните сцену (.blend) — кеш создаётся рядом "
                "с ней, и после сборки файл будет открыт заново"))
            return {'CANCELLED'}

        # The build wipes scene data (reset_blend_state) and save_as_-
        # mainfile's category files over the current session, so any
        # unsaved work would be lost. Refuse rather than risk it; the
        # original file is reopened once the build finishes.
        if bpy.data.is_dirty:
            self.report({'ERROR'}, T(
                "Сохрани изменения — сборка очищает текущую сцену и "
                "потеряет несохранённую работу (после сборки твой файл "
                "будет открыт заново)"))
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
        categories = None
        if region and region != 'ALL':
            cats = {
                f'mapobjects_{region.upper()}',
                'mapobjects_GENERIC',
                'lod',
            }
            if getattr(settings, 'gtatools_library_include_vehicles', False):
                cats.add('vehicles')
            if getattr(settings, 'gtatools_library_include_peds', False):
                cats.add('peds')
            if getattr(settings, 'gtatools_library_include_weapons', False):
                cats.add('weapons')
            if getattr(settings, 'gtatools_library_include_interiors', False):
                cats.add('mapobjects_INTERIORS')
            categories = cats

        # Scene's active game drives which .dat manifest is parsed
        # (gta.dat / gta_vc.dat / gta3.dat). Reader logic is game-agnostic
        # per Phase 5/18/19; this just selects entry points.
        from ..core import game_versions as _gv
        target_game = _gv.game_of_scene(context.scene)

        from ..tools.build_library import build_library_iter

        self._orig_filepath = bpy.data.filepath
        self._status = {}
        try:
            self._gen = build_library_iter(
                cache_dir=cache_dir,
                game_root=game_root,
                output_dir=output_dir,
                status=self._status,
                no_preview=no_preview,
                preview_size=preview_size,
                categories=categories,
                skip_existing=skip_existing,
                delete_cache_after=delete_cache,
                game=target_game,
            )
        except FileNotFoundError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        self._t_start = time.perf_counter()

        wm = context.window_manager
        wm.progress_begin(0, 100)
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Сборка библиотеки…"))
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            self._cleanup(context)
            self._schedule_restore()
            self.report({'WARNING'}, T("Отменено — сцена будет перезагружена"))
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        # Advance the build generator for a short slice so a single tick
        # never blocks the UI for long. StopIteration = build finished.
        deadline = time.monotonic() + 0.1
        while time.monotonic() < deadline:
            try:
                next(self._gen)
            except StopIteration:
                elapsed = time.perf_counter() - self._t_start
                classified = self._status.get('classified', 0)
                cat_done = self._status.get('cat_done', 0)
                self._cleanup(context)
                self._schedule_restore()
                self.report({'INFO'},
                            f"{T('Библиотека собрана за')} {elapsed:.0f}s "
                            f"({classified or cat_done} {T('моделей')})")
                return {'FINISHED'}
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._cleanup(context)
                self._schedule_restore()
                self.report({'ERROR'}, f"Build error: {e}")
                return {'CANCELLED'}

        # Update progress display from status dict.
        wm = context.window_manager
        st = self._status
        phase = st.get('phase', 'init')

        if phase == 'build':
            cat = st.get('category', '?')
            cat_done = st.get('cat_done', 0)
            cat_total = max(st.get('cat_total', 1), 1)
            wm.progress_update(int(100 * cat_done / cat_total))
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

        return {'RUNNING_MODAL'}

    def _schedule_restore(self):
        """Reopen the user's original .blend after the build wiped the
        session. Done from a timer (not inline) so open_mainfile runs
        once this operator has fully exited."""
        orig = self._orig_filepath
        if not orig:
            return

        def _do():
            try:
                bpy.ops.wm.open_mainfile(filepath=orig)
            except Exception as e:
                print(f"[Build Library] could not reload original file: {e}")
            return None

        try:
            bpy.app.timers.register(_do, first_interval=0.1)
        except Exception:
            pass

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

        # Gate: opens library .blend files in this session; off by default.
        if not getattr(settings, 'gtatools_enable_asset_builder', False):
            self.report({'ERROR'}, T(
                "Регенерация превью открывает .blend файлы библиотеки в "
                "этом окне Blender. Включи галочку «Разрешить сборку "
                "Asset Library» в настройках."))
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
