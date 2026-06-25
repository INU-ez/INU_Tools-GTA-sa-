# INU_tools.ui.library_panel — GTA Library N-sidebar tab.
#
# Standalone N-panel category, separate from the main GTA Tools tab.
# Asset Library construction is a one-shot per modpack/install — having
# it next to the constantly-used Import/Export Map clutters the main
# panel without value. A dedicated tab also signals the workflow:
# Extract Resources (in GTA Tools) → switch to GTA Library → Build →
# point Blender at the result. After that the user can hide the tab
# until next time.

import os

import bpy

from .. import T
from ..tools.compat import safe_icon, inu_icon
class GTATOOLS_PT_library_panel(bpy.types.Panel):
    """Asset Library Builder — turns extracted .inu_cache contents into a
    portable Blender asset library (one .blend per category, with
    thumbnails and embedded IDE metadata)."""
    bl_label = "GTA Library"
    bl_idname = "GTATOOLS_PT_library_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Library'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.inu_settings

        saved = bool(bpy.data.filepath)
        cache_dir = ''
        cache_exists = False
        if saved:
            blend_dir = os.path.dirname(bpy.data.filepath)
            cache_dir = os.path.join(blend_dir, '.inu_cache')
            cache_exists = os.path.isdir(cache_dir)

        game_root_path = bpy.path.abspath(
            getattr(settings, 'gtatools_game_root', '') or '')
        game_root_set = bool(game_root_path) and os.path.isdir(game_root_path)

        # ── Game Root ──────────────────────────────────────────
        # Surfaced here so the whole workflow lives in one panel — no
        # tab-switching to GTA Tools just to set the install path.
        # The property is shared with the main GTA Tools panel, so
        # editing it here updates there and vice versa.
        gr_box = layout.box()
        gr_box.label(text=T("Корневая папка GTA SA"),
                     **inu_icon(safe_icon('FILE_FOLDER')))
        gr_box.prop(settings, "gtatools_game_root", text="")

        # ── Step 1: Extract Resources ──────────────────────────
        # Same operator as the GTA Tools tab; clicking either one runs
        # the same modal extract. Region picker also exposed inline so
        # the user can build a region-specific library without tab
        # hopping (ALL = full game).
        step1 = layout.box()
        step1.label(text=T("1. Извлечь ресурсы"),
                    **inu_icon(safe_icon('PACKAGE')))
        step1.prop(settings, "gtatools_map_region",
                   text=T("Регион"))
        if saved and game_root_set:
            step1.operator("gtatools.extract_textures",
                           text=T("Извлечь ресурсы"),
                           **inu_icon(safe_icon('PACKAGE')))
        else:
            warn = step1.row(align=True)
            warn.enabled = False
            warn.operator("gtatools.extract_textures",
                          text=T("Извлечь ресурсы"),
                          **inu_icon(safe_icon('PACKAGE')))

        # ── Status header ──
        # Four chips reflecting the prerequisites for the build step.
        # Green = ready, red = missing — clearer than relying on the
        # disabled-button gray-out alone.
        status = layout.box()
        status.label(text=T("Готовность"), **inu_icon(safe_icon('INFO')))

        def _chip(ok: bool, ok_text: str, fail_text: str):
            row = status.row(align=True)
            if ok:
                row.label(text=ok_text, **inu_icon(safe_icon('CHECKMARK')))
            else:
                sub = row.row(align=True)
                sub.alert = True
                sub.label(text=fail_text, **inu_icon(safe_icon('ERROR')))

        _chip(saved, T(".blend сохранён"), T("Сцена не сохранена"))
        _chip(game_root_set, T("Game Root указан"),
              T("Game Root не указан"))
        _chip(cache_exists, T("Кеш найден"),
              T("Кеш пуст — Extract Resources"))

        output_set = bool(getattr(settings, 'gtatools_library_output_path', ''))
        _chip(output_set, T("Output задан"), T("Output не задан"))

        layout.separator()

        # ── Step 2: Build options ──────────────────────────────
        step2 = layout.box()
        step2.label(text=T("2. Папка библиотеки"),
                    **inu_icon(safe_icon('FILE_FOLDER')))
        step2.prop(settings, "gtatools_library_output_path", text="")

        opt_box = layout.box()
        opt_box.label(text=T("Параметры"), **inu_icon(safe_icon('PREFERENCES')))
        col = opt_box.column(align=True)
        col.prop(settings, "gtatools_library_skip_existing",
                 text=T("Пропускать готовые .blend"))
        col.prop(settings, "gtatools_library_no_preview",
                 text=T("Без превьюшек (быстрее, но без миниатюр)"))
        col.prop(settings, "gtatools_library_preview_size",
                 text=T("Размер превью (px)"))
        col.prop(settings, "gtatools_library_delete_cache",
                 text=T("Удалить кеш после сборки"))

        # Доп. категории — релевантны только при region != ALL. Регион
        # читается из общей Map-Region настройки (та же что в Import
        # Map / Extract Resources). При ALL строится вся библиотека и
        # эти тогглы не нужны.
        region = getattr(settings, 'gtatools_map_region', 'ALL')
        if region and region != 'ALL':
            opt_box.separator()
            opt_box.label(text=T(f"Региональная сборка: {region}. Доп. категории:"))
            grid = opt_box.grid_flow(columns=2, align=True)
            grid.prop(settings, "gtatools_library_include_vehicles",
                      toggle=True)
            grid.prop(settings, "gtatools_library_include_peds",
                      toggle=True)
            grid.prop(settings, "gtatools_library_include_weapons",
                      toggle=True)
            grid.prop(settings, "gtatools_library_include_interiors",
                      toggle=True)

        layout.separator()

        # ── Enable gate (this feature spawns a background Blender process) ──
        layout.prop(settings, "gtatools_enable_asset_builder",
                    text=T("Разрешить сборку (фоновый процесс Blender)"))

        # ── Build button ──
        btn_row = layout.row(align=True)
        btn_row.scale_y = 1.5
        ready = (saved and game_root_set and cache_exists and output_set
                 and settings.gtatools_enable_asset_builder)
        if not ready:
            btn_row.enabled = False
        btn_row.operator(
            "gtatools.build_asset_library",
            text=T("Собрать Asset Library"),
            **inu_icon(safe_icon('ASSET_MANAGER')))

        # ── Regenerate previews ──
        # Secondary action — only relevant when the library already
        # exists. Detected by presence of any .blend in the output dir.
        regen_available = False
        if output_set:
            output_path = bpy.path.abspath(
                settings.gtatools_library_output_path)
            if os.path.isdir(output_path):
                try:
                    regen_available = any(
                        f.lower().endswith('.blend')
                        for f in os.listdir(output_path))
                except OSError:
                    pass

        regen_row = layout.row(align=True)
        if not (regen_available and settings.gtatools_enable_asset_builder):
            regen_row.enabled = False
        regen_row.operator(
            "gtatools.regenerate_previews",
            text=T("Перегенерировать превью"),
            **inu_icon(safe_icon('RENDER_STILL')))

        # ── Info / hints ──
        layout.separator()
        info = layout.box()
        info.label(text=T("Как пользоваться"), **inu_icon(safe_icon('QUESTION')))
        col = info.column(align=True)
        col.scale_y = 0.85
        col.label(text=T("1. Сохрани .blend"))
        col.label(text=T("2. Укажи Game Root и регион"))
        col.label(text=T("3. Извлеки ресурсы"))
        col.label(text=T("4. Укажи папку Output"))
        col.label(text=T("5. Жми «Собрать»"))
        col.label(text=T("6. Edit > Preferences > File Paths >"))
        col.label(text=T("   Asset Libraries > Add → твой Output"))


# ── Registration ───────────────────────────────────────────────────

CLASSES = (
    GTATOOLS_PT_library_panel,
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
