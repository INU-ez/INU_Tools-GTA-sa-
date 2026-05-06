# INU_tools.ops.inu_export — combined INU Import / Export operators.
#
# Phase 3 batch 5 (2026-04-26): 3 mega-operators from __init__.py.
#   - INU Import: file-extension-driven dispatch (.dff/.col/.txd/.ide/.ipl)
#   - Export All: bulk DFF+COL+LOD+TXD export to a folder
#   - INU Export: ExportHelper-based unified export with TXD bucketing
#
# Several small helpers (_ide_entry_from_obj, _ipl_entry_from_obj,
# _clean_model_name_ide, _clean_name_typed_ipl, _append_export_report)
# stay in __init__.py — pulled in lazily inside each method since
# loading order makes top-level `from .. import _foo` racy.

import os
import bpy
from bpy.props import (
    BoolProperty, CollectionProperty, EnumProperty, StringProperty,
)
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .. import T
from ..tools.compat import safe_icon


class GTATOOLS_OT_inu_import(bpy.types.Operator, ImportHelper):
    """Импорт GTA SA файлов (.dff/.col/.txd/.ide/.ipl) с авто-определением формата"""
    bl_idname = "gtatools.inu_import"
    bl_label = "INU: INU Import"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = ".dff"
    filter_glob: StringProperty(
        default="*.dff;*.col;*.txd;*.ide;*.ipl",
        options={'HIDDEN'}
    )
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        from .dff_import import import_dff as inu_import_dff
        from .col_import import import_col as inu_import_col
        from .txd_import import import_txd as inu_import_txd
        from .ide_import import import_ide as inu_import_ide
        from .ipl_import import import_ipl as inu_import_ipl

        file_list = [f.name for f in self.files if f.name] or [os.path.basename(self.filepath)]
        directory = self.directory or os.path.dirname(self.filepath)

        # Import order: TXD first (so DFF import can auto-link textures), then DFF, COL, IDE, IPL
        order = {'.txd': 0, '.dff': 1, '.col': 2, '.ide': 3, '.ipl': 4}
        file_list.sort(key=lambda n: order.get(os.path.splitext(n)[1].lower(), 99))

        imported = []
        errors = []
        imported_txd_paths = set()

        for fname in file_list:
            fpath = os.path.join(directory, fname)
            ext = os.path.splitext(fname)[1].lower()
            try:
                if ext == '.dff':
                    inu_import_dff(filepath=fpath, context=context)
                    imported.append(fname)
                    # Auto-import TXD if enabled and not already imported
                    if getattr(context.scene.inu_settings, 'gtatools_txd_auto_import', True):
                        dff_name = os.path.splitext(fname)[0]
                        custom_dir = getattr(context.scene.inu_settings, 'gtatools_txd_import_path', '')
                        if custom_dir:
                            custom_dir = bpy.path.abspath(custom_dir)
                        search_dirs = []
                        if custom_dir and os.path.isdir(custom_dir):
                            search_dirs.append(custom_dir)
                        search_dirs.append(directory)
                        txd_file = None
                        for search_dir in search_dirs:
                            if txd_file:
                                break
                            same_name = os.path.join(search_dir, dff_name + ".txd")
                            if os.path.isfile(same_name) and same_name not in imported_txd_paths:
                                txd_file = same_name
                                break
                        if txd_file:
                            try:
                                images = inu_import_txd(filepath=txd_file)
                                imported_txd_paths.add(txd_file)
                                imported.append(f"{os.path.basename(txd_file)} ({len(images)} tex)")
                            except Exception as e:
                                errors.append(f"{os.path.basename(txd_file)}: {e}")
                elif ext == '.col':
                    inu_import_col(filepath=fpath, context=context)
                    imported.append(fname)
                elif ext == '.txd':
                    if fpath in imported_txd_paths:
                        continue
                    images = inu_import_txd(filepath=fpath)
                    imported_txd_paths.add(fpath)
                    imported.append(f"{fname} ({len(images)} tex)")
                elif ext == '.ide':
                    matched = inu_import_ide(filepath=fpath, context=context)
                    imported.append(f"{fname} ({len(matched)} matched)")
                elif ext == '.ipl':
                    placed = inu_import_ipl(filepath=fpath, context=context)
                    imported.append(f"{fname} ({len(placed)} placed)")
                else:
                    errors.append(f"{fname}: unsupported extension")
            except Exception as e:
                errors.append(f"{fname}: {e}")

        if imported:
            self.report({'INFO'}, f"INU Import: {len(imported)} — {', '.join(imported)}")
        if errors:
            self.report({'ERROR'}, f"Errors: {'; '.join(errors)}")
            return {'CANCELLED'} if not imported else {'FINISHED'}
        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(GTATOOLS_OT_inu_import.bl_idname,
                         text="INU Import (.dff/.col/.txd/.ide/.ipl)")


class GTATOOLS_OT_export_all(bpy.types.Operator):
    """Экспорт всех выделенных моделей (DFF + COL + LOD + TXD)"""
    bl_idname = "gtatools.export_all"
    bl_label = "INU: Export All (DFF+COL+LOD+TXD)"
    bl_options = {'REGISTER'}

    directory: StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        # File browser sidebar — the 4 format toggles + conditional
        # library/shared rows used to live on the main panel; moved
        # here so the panel collapses to just two target buttons and
        # the format pick happens at the moment of export.
        layout = self.layout
        scn = context.scene
        layout.label(text=T("Что экспортировать:"))
        row = layout.row(align=True)
        row.prop(scn.inu_settings, "gtatools_export_all_dff", text="DFF")
        row.prop(scn.inu_settings, "gtatools_export_all_col", text="COL")
        row.prop(scn.inu_settings, "gtatools_export_all_lod", text="LOD")
        row.prop(scn.inu_settings, "gtatools_export_all_txd", text="TXD")
        if scn.inu_settings.gtatools_export_all_col:
            row = layout.row(align=True)
            row.prop(scn.inu_settings, "gtatools_export_all_col_library",
                     text="", icon=safe_icon('PACKAGE'))
            row.prop(scn.inu_settings, "gtatools_export_all_col_library_name",
                     text="", placeholder="collision")
        if scn.inu_settings.gtatools_export_all_txd:
            row = layout.row(align=True)
            row.prop(scn.inu_settings, "gtatools_export_all_txd_shared",
                     text="", icon=safe_icon('PACKAGE'))
            row.prop(scn.inu_settings, "gtatools_export_all_txd_shared_name",
                     text="", placeholder="textures")

    def export_model_group(self, context, base_name, models, skip_dff, skip_col, skip_lod, skip_txd, use_gpu):
        """Export a single model group (DFF + LOD + COL + TXD)"""
        exported = []
        errors = []

        # Экспорт DFF (версия GTA SA)
        if models['DFF'] and not skip_dff:
            dff_path = os.path.join(self.directory, f"{base_name}.dff")
            try:
                from .dff_export import export_dff as inu_export_dff
                # Collect mesh + attached 2DFX objects
                dff_objects = [models['DFF']]
                for child in models['DFF'].children:
                    if child.type == 'EMPTY' and getattr(child, 'inu', None) and child.inu.type == '2DFX':
                        dff_objects.append(child)
                inu_export_dff(filepath=dff_path, objects=dff_objects)
                exported.append(f"{base_name}.dff")
            except Exception as e:
                errors.append(f"{base_name}.dff: {str(e)}")

        # Экспорт LOD (с префиксом LOD, версия GTA SA)
        if models['LOD'] and not skip_lod:
            lod_path = os.path.join(self.directory, f"LOD{base_name}.dff")
            try:
                from .dff_export import export_dff as inu_export_dff
                inu_export_dff(filepath=lod_path, objects=[models['LOD']])
                exported.append(f"LOD{base_name}.dff")
            except Exception as e:
                errors.append(f"LOD{base_name}.dff: {str(e)}")

        # Экспорт COL (версия GTA SA COL3)
        if models['COL'] and not skip_col:
            col_path = os.path.join(self.directory, f"{base_name}.col")
            original_col_loc = models['COL'].location.copy()
            try:
                from .col_export import export_col as inu_export_col

                # COL всегда экспортируется в центре (0,0,0)
                models['COL'].location = (0, 0, 0)

                inu_export_col(
                    filepath=col_path,
                    objects=[models['COL']],
                    version=3,
                    model_name=base_name,
                )

                # Возвращаем позицию
                models['COL'].location = original_col_loc

                exported.append(f"{base_name}.col")
            except Exception as e:
                errors.append(f"{base_name}.col: {str(e)}")
            finally:
                # Always restore object transform even when export fails.
                models['COL'].location = original_col_loc

        # Экспорт TXD (текстуры из DFF + LOD в один архив)
        if (models['DFF'] or models['LOD']) and not skip_txd:
            txd_path = os.path.join(self.directory, f"{base_name}.txd")
            prev_active = context.view_layer.objects.active
            prev_selected = [o for o in context.selected_objects]
            try:
                bpy.ops.object.select_all(action='DESELECT')
                # Выделяем DFF и LOD для сбора текстур
                if models['DFF']:
                    models['DFF'].select_set(True)
                    context.view_layer.objects.active = models['DFF']
                if models['LOD']:
                    models['LOD'].select_set(True)
                    if not models['DFF']:
                        context.view_layer.objects.active = models['LOD']
                from ..tools.txd_export import export_txd
                result, message, _ = export_txd(txd_path, context, selected_only=True, use_gpu=use_gpu)
                if result == {'FINISHED'}:
                    exported.append(f"{base_name}.txd")
                else:
                    errors.append(f"{base_name}.txd: {message}")
            except Exception as e:
                errors.append(f"{base_name}.txd: {str(e)}")
            finally:
                # Restore previous user selection/active object after temporary hijack.
                bpy.ops.object.select_all(action='DESELECT')
                for o in prev_selected:
                    o.select_set(True)
                if prev_active is not None:
                    context.view_layer.objects.active = prev_active

        return exported, errors

    def execute(self, context):
        # Ищем все группы моделей среди выделенных
        from ..tools.model_utils import find_all_selected_model_groups
        model_groups = find_all_selected_model_groups()

        if not model_groups:
            self.report({'ERROR'}, T("Выделите модели для экспорта!"))
            return {'CANCELLED'}

        # Запоминаем объекты с активным prelight и отключаем
        prelight_was_on = set()
        for base_name, models in model_groups.items():
            for model_type in ['DFF', 'LOD', 'COL']:
                obj = models[model_type]
                if obj and obj.type == 'MESH':
                    has_prelight = False
                    for mat_slot in obj.material_slots:
                        mat = mat_slot.material
                        if mat and mat.use_nodes and mat.node_tree.nodes.get("Prelight_Mix"):
                            has_prelight = True
                            break
                    if has_prelight:
                        prelight_was_on.add(obj)
                        from ..tools.prelight import setup_prelight_preview
                        setup_prelight_preview(obj, enable=False)

        all_exported = []
        all_errors = []
        wm = context.window_manager

        # Настройки экспорта
        skip_dff = not context.scene.inu_settings.gtatools_export_all_dff
        skip_col = not context.scene.inu_settings.gtatools_export_all_col
        skip_lod = not context.scene.inu_settings.gtatools_export_all_lod
        skip_txd = not context.scene.inu_settings.gtatools_export_all_txd
        col_library = bool(getattr(context.scene.inu_settings, 'gtatools_export_all_col_library', False))
        col_library_name = getattr(context.scene.inu_settings, 'gtatools_export_all_col_library_name', '') or 'collision'
        txd_shared = bool(getattr(context.scene.inu_settings, 'gtatools_export_all_txd_shared', False))
        txd_shared_name = getattr(context.scene.inu_settings, 'gtatools_export_all_txd_shared_name', '') or 'textures'
        from ..tools.txd_export import check_nvtt_available
        use_gpu = check_nvtt_available(getattr(context.scene.inu_settings, 'gtatools_nvtt_path', ''))[0]

        # Library mode: skip the per-group COL write path and collect all
        # COL objects instead. A single combined .col file is written after
        # the group loop. DFF/LOD/TXD still go per-group.
        library_col_objects = []
        if col_library and not skip_col:
            skip_col = True
            for _base, _models in model_groups.items():
                if _models['COL']:
                    library_col_objects.append(_models['COL'])

        # Shared TXD mode: same pattern — skip per-group TXD, collect every
        # DFF/LOD mesh, write one combined archive after the loop.
        shared_txd_objects = []
        if txd_shared and not skip_txd:
            skip_txd = True
            for _base, _models in model_groups.items():
                if _models['DFF']:
                    shared_txd_objects.append(_models['DFF'])
                if _models['LOD']:
                    shared_txd_objects.append(_models['LOD'])

        # Считаем общее количество шагов для прогресс-бара
        total_steps = 0
        for base_name, models in model_groups.items():
            total_steps += sum([
                1 if models['DFF'] and not skip_dff else 0,
                1 if models['LOD'] and not skip_lod else 0,
                1 if models['COL'] and not skip_col else 0,
                1 if (models['DFF'] or models['LOD']) and not skip_txd else 0
            ])

        current_step = 0
        wm.progress_begin(0, total_steps)
        context.workspace.status_text_set(T("Экспорт..."))
        try:
            # Экспортируем каждую группу моделей
            for group_idx, (base_name, models) in enumerate(model_groups.items()):
                wm.progress_update(current_step)
                context.workspace.status_text_set(
                    f"{T('Экспорт:')} {group_idx + 1}/{len(model_groups)} {base_name}")
                exported, errors = self.export_model_group(context, base_name, models, skip_dff, skip_col, skip_lod, skip_txd, use_gpu)
                all_exported.extend(exported)
                all_errors.extend(errors)

                # Обновляем прогресс
                current_step += sum([
                    1 if models['DFF'] and not skip_dff else 0,
                    1 if models['LOD'] and not skip_lod else 0,
                    1 if models['COL'] and not skip_col else 0,
                    1 if (models['DFF'] or models['LOD']) and not skip_txd else 0
                ])

            # Library COL — one multi-entry .col file from every group's COL mesh
            if col_library and library_col_objects:
                from .col_export import export_col_library
                lib_path = os.path.join(self.directory, f"{col_library_name}.col")
                # COL exports expect objects at origin — temporarily centre them
                original_locations = {}
                try:
                    for obj in library_col_objects:
                        original_locations[obj.name] = obj.location.copy()
                        obj.location = (0, 0, 0)
                    count = export_col_library(lib_path, library_col_objects, version=3)
                    all_exported.append(f"{col_library_name}.col ({count} records)")
                except Exception as e:
                    all_errors.append(f"{col_library_name}.col: {e}")
                finally:
                    for obj in library_col_objects:
                        if obj.name in original_locations:
                            obj.location = original_locations[obj.name]

            # Shared TXD — every texture from every exported mesh packed into
            # one archive. Selection is hijacked because export_txd reads
            # selection; we restore it on the way out.
            if txd_shared and shared_txd_objects:
                shared_path = os.path.join(self.directory, f"{txd_shared_name}.txd")
                prev_active = context.view_layer.objects.active
                prev_selected = [o for o in context.selected_objects]
                try:
                    bpy.ops.object.select_all(action='DESELECT')
                    for src in shared_txd_objects:
                        src.select_set(True)
                    context.view_layer.objects.active = shared_txd_objects[0]
                    from ..tools.txd_export import export_txd
                    result, message, _ = export_txd(
                        shared_path, context, selected_only=True, use_gpu=use_gpu)
                    if result == {'FINISHED'}:
                        all_exported.append(
                            f"{txd_shared_name}.txd ({len(shared_txd_objects)} models)")
                    else:
                        all_errors.append(f"{txd_shared_name}.txd: {message}")
                except Exception as e:
                    all_errors.append(f"{txd_shared_name}.txd: {e}")
                finally:
                    bpy.ops.object.select_all(action='DESELECT')
                    for o in prev_selected:
                        o.select_set(True)
                    if prev_active is not None:
                        context.view_layer.objects.active = prev_active
        finally:
            wm.progress_end()
            context.workspace.status_text_set(None)
            # Восстанавливаем prelight только где он был включён
            for obj in prelight_was_on:
                setup_prelight_preview(obj, enable=True)

        # Result
        num_groups = len(model_groups)
        if all_exported:
            self.report({'INFO'}, f"{T('Экспортировано:')} {len(all_exported)} файлов ({num_groups} моделей)")
        if all_errors:
            preview = '; '.join(all_errors[:5])
            more = f" (+{len(all_errors) - 5})" if len(all_errors) > 5 else ""
            self.report({'WARNING'}, f"{T('Ошибки:')} {preview}{more}")

        # Persist full per-run report into export directory.
        try:
            report_path = os.path.join(self.directory, "_export_report.txt")
            rows = [f"Directory: {self.directory}"]
            rows.extend(f"[OK] {row}" for row in all_exported)
            rows.extend(f"[ERR] {row}" for row in all_errors)
            from .. import _append_export_report
            _append_export_report(report_path, "Export All", rows)
        except Exception as e:
            self.report({'WARNING'}, f"{T('Не удалось записать отчёт:')} {e}")

        return {'FINISHED'}


class GTATOOLS_OT_inu_export(bpy.types.Operator, ExportHelper):
    """Единый экспорт INU — DFF, COL, TXD, IDE, IPL в одну папку"""
    bl_idname = "gtatools.inu_export"
    bl_label = "INU: INU Export"
    bl_options = {'REGISTER', 'PRESET'}

    filename_ext = ""
    use_filter_folder = True

    # ── Format checkboxes ──
    export_dff: BoolProperty(name="DFF", default=True, description="Export DFF models")
    export_col: BoolProperty(name="COL", default=True, description="Export COL collision")
    from ..tools.txd_export import export_txd
    export_txd: BoolProperty(name="TXD", default=True, description="Export TXD textures")
    export_ide: BoolProperty(name="IDE", default=False, description="Export IDE definitions")
    export_ipl: BoolProperty(name="IPL", default=False, description="Export IPL placements")

    # ── Source ──
    source: EnumProperty(
        name="Source",
        items=[
            ('SELECTED', "Selected", "Export selected objects"),
            ('COLLECTION', "Active Collection", "Export objects from active collection"),
            ('SCENE', "Entire Scene", "Export all mesh objects in scene"),
        ],
        default='SELECTED',
    )

    # ── DFF settings ──
    dff_include_2dfx: BoolProperty(name="Include 2DFX", default=True)
    dff_auto_lod: BoolProperty(name="Auto-LOD", default=True,
        description="Automatically export LOD models (LOD*.dff)")

    # ── COL settings ──
    col_library: BoolProperty(
        name=T("COL Library"),
        description=T("Писать все коллизии в один .col файл (multi-entry library). Каждая запись в файле — отдельная коллизия со своим model_id, сопоставляется с DFF по ID"),
        default=False,
    )
    col_library_name: StringProperty(
        name=T("Имя library .col"),
        description=T("Имя общего .col файла без расширения (например 'district' → district.col)"),
        default="collision",
    )

    # ── TXD settings ──
    txd_selected_only: BoolProperty(name="Selected Only", default=True,
        description="Export only textures used by exported models")

    # ── IDE/IPL settings ──
    ide_ipl_upsert: BoolProperty(name="Upsert (add/update)", default=False,
        description="Add or update entries in existing IDE/IPL files instead of creating new ones")
    ide_upsert_path: StringProperty(name="IDE File", subtype='FILE_PATH',
        description="Path to existing IDE file for upsert")
    ipl_upsert_path: StringProperty(name="IPL File", subtype='FILE_PATH',
        description="Path to existing IPL file for upsert")

    def draw(self, context):
        layout = self.layout

        # Format
        box = layout.box()
        box.label(text=T("Формат:"), icon=safe_icon('EXPORT'))
        col = box.column(align=True)
        col.prop(self, "export_dff")
        col.prop(self, "export_col")
        col.prop(self, "export_txd")
        col.prop(self, "export_ide")
        col.prop(self, "export_ipl")

        # Source
        box = layout.box()
        box.label(text=T("Источник:"), icon=safe_icon('OBJECT_DATA'))
        box.prop(self, "source", text="")

        # DFF settings
        if self.export_dff:
            box = layout.box()
            box.label(text="DFF:", icon=safe_icon('MESH_DATA'))
            box.prop(self, "dff_include_2dfx")
            box.prop(self, "dff_auto_lod")
            # Pipeline
            box.prop(context.scene.inu_settings, "gtatools_export_pipeline", text="Pipeline")

        # COL settings
        if self.export_col:
            box = layout.box()
            box.label(text="COL:", icon=safe_icon('MESH_ICOSPHERE'))
            box.prop(self, "col_library")
            if self.col_library:
                box.prop(self, "col_library_name")

        # TXD settings
        if self.export_txd:
            box = layout.box()
            box.label(text="TXD:", icon=safe_icon('IMAGE_DATA'))
            box.prop(self, "txd_selected_only")

        # IDE/IPL settings
        if self.export_ide or self.export_ipl:
            box = layout.box()
            box.label(text="IDE / IPL:", icon=safe_icon('TEXT'))
            box.prop(self, "ide_ipl_upsert")
            if self.ide_ipl_upsert:
                if self.export_ide:
                    box.prop(self, "ide_upsert_path")
                if self.export_ipl:
                    box.prop(self, "ipl_upsert_path")

    def _get_source_objects(self, context):
        """Get objects based on source setting."""
        if self.source == 'SELECTED':
            return [o for o in context.selected_objects if o.type in ('MESH', 'EMPTY')]
        elif self.source == 'COLLECTION':
            col = context.view_layer.active_layer_collection.collection
            return [o for o in col.objects if o.type in ('MESH', 'EMPTY')]
        else:  # SCENE
            return [o for o in context.scene.objects if o.type in ('MESH', 'EMPTY')]

    def execute(self, context):
        directory = os.path.dirname(self.filepath) if self.filepath else self.filepath
        if not directory or not os.path.isdir(directory):
            self.report({'ERROR'}, T("Выберите папку для экспорта"))
            return {'CANCELLED'}

        source_objects = self._get_source_objects(context)
        mesh_objects = [o for o in source_objects if o.type == 'MESH']

        if not mesh_objects:
            self.report({'ERROR'}, T("Нет меш объектов для экспорта"))
            return {'CANCELLED'}

        # Build model groups from source objects
        groups = {}
        for obj in mesh_objects:
            from ..tools.model_utils import get_model_type
            model_type, base_name = get_model_type(obj)
            if not base_name:
                continue
            base_name_clean = base_name.rstrip('_')
            if base_name_clean not in groups:
                groups[base_name_clean] = {'DFF': None, 'LOD': None, 'COL': None}
            if model_type and groups[base_name_clean][model_type] is None:
                groups[base_name_clean][model_type] = obj

        if not groups:
            self.report({'ERROR'}, T("Не найдено моделей для экспорта"))
            return {'CANCELLED'}

        # Disable prelight preview
        prelight_was_on = set()
        for base_name, models in groups.items():
            for mt in ('DFF', 'LOD', 'COL'):
                obj = models[mt]
                if obj and obj.type == 'MESH':
                    for mat_slot in obj.material_slots:
                        mat = mat_slot.material
                        if mat and mat.use_nodes and mat.node_tree.nodes.get("Prelight_Mix"):
                            prelight_was_on.add(obj)
                            from ..tools.prelight import setup_prelight_preview
                            setup_prelight_preview(obj, enable=False)
                            break

        all_exported = []
        all_errors = []
        from ..tools.txd_export import check_nvtt_available
        use_gpu = check_nvtt_available(getattr(context.scene.inu_settings, 'gtatools_nvtt_path', ''))[0]

        # Library COL bypasses the per-group loop — collect once and emit
        # a single multi-entry .col after all groups finish.
        library_col_objects = []
        write_col_per_group = self.export_col
        if self.export_col and self.col_library:
            write_col_per_group = False
            for _base, _models in groups.items():
                if _models['COL']:
                    library_col_objects.append(_models['COL'])

        wm = context.window_manager
        total_groups = len(groups)
        wm.progress_begin(0, total_groups)
        context.workspace.status_text_set(T("INU Export..."))

        for idx, (base_name, models) in enumerate(groups.items()):
            wm.progress_update(idx)
            context.workspace.status_text_set(
                f"{T('INU Export:')} {idx + 1}/{total_groups} {base_name}")

            # ── DFF ──
            if self.export_dff and models['DFF']:
                dff_path = os.path.join(directory, f"{base_name}.dff")
                try:
                    from .dff_export import export_dff as inu_export_dff
                    dff_objects = [models['DFF']]
                    if self.dff_include_2dfx:
                        for child in models['DFF'].children:
                            if child.type == 'EMPTY' and getattr(child, 'inu', None) and child.inu.type == '2DFX':
                                dff_objects.append(child)
                    inu_export_dff(filepath=dff_path, objects=dff_objects)
                    all_exported.append(f"{base_name}.dff")
                except Exception as e:
                    all_errors.append(f"{base_name}.dff: {e}")

            # ── LOD ──
            if self.export_dff and self.dff_auto_lod and models['LOD']:
                lod_path = os.path.join(directory, f"LOD{base_name}.dff")
                try:
                    from .dff_export import export_dff as inu_export_dff
                    inu_export_dff(filepath=lod_path, objects=[models['LOD']])
                    all_exported.append(f"LOD{base_name}.dff")
                except Exception as e:
                    all_errors.append(f"LOD{base_name}.dff: {e}")

            # ── COL ── (per-group, skipped when library mode is on)
            if write_col_per_group and models['COL']:
                col_path = os.path.join(directory, f"{base_name}.col")
                try:
                    from .col_export import export_col as inu_export_col
                    original_loc = models['COL'].location.copy()
                    models['COL'].location = (0, 0, 0)
                    inu_export_col(filepath=col_path, objects=[models['COL']], version=3, model_name=base_name)
                    models['COL'].location = original_loc
                    all_exported.append(f"{base_name}.col")
                except Exception as e:
                    all_errors.append(f"{base_name}.col: {e}")

            # ── TXD ──
            from ..tools.txd_export import export_txd
            if self.export_txd and (models['DFF'] or models['LOD']):
                txd_path = os.path.join(directory, f"{base_name}.txd")
                try:
                    bpy.ops.object.select_all(action='DESELECT')
                    if models['DFF']:
                        models['DFF'].select_set(True)
                        context.view_layer.objects.active = models['DFF']
                    if models['LOD']:
                        models['LOD'].select_set(True)
                        if not models['DFF']:
                            context.view_layer.objects.active = models['LOD']
                    result, msg, _ = export_txd(txd_path, context, self.txd_selected_only, use_gpu)
                    if result == {'FINISHED'}:
                        all_exported.append(f"{base_name}.txd")
                    else:
                        all_errors.append(f"{base_name}.txd: {msg}")
                except Exception as e:
                    all_errors.append(f"{base_name}.txd: {e}")

        # ── IDE ──
        if self.export_ide:
            if self.ide_ipl_upsert and self.ide_upsert_path:
                try:
                    from ..core.ide import upsert_ide
                    entries = []
                    for base_name, models in groups.items():
                        if models['DFF']:
                            from .. import _ide_entry_from_obj
                            entries.append(_ide_entry_from_obj(models['DFF']))
                        if models['LOD']:
                            lod_entry = _ide_entry_from_obj(models['LOD'])
                            lod_entry.model_name = "LOD" + base_name
                            from .. import _clean_model_name_ide
                            lod_entry.txd_name = _clean_model_name_ide(base_name)
                            entries.append(lod_entry)
                    ide_path = bpy.path.abspath(self.ide_upsert_path)
                    updated, added = upsert_ide(ide_path, entries)
                    all_exported.append(f"IDE: +{added} ~{updated}")
                except Exception as e:
                    all_errors.append(f"IDE upsert: {e}")
            else:
                ide_path = os.path.join(directory, "objects.ide")
                try:
                    from .ide_export import export_ide as inu_export_ide
                    inu_export_ide(filepath=ide_path, objects=mesh_objects)
                    all_exported.append("objects.ide")
                except Exception as e:
                    all_errors.append(f"IDE: {e}")

        # ── IPL ──
        if self.export_ipl:
            if self.ide_ipl_upsert and self.ipl_upsert_path:
                try:
                    from ..core.ipl import upsert_ipl
                    entries = []
                    for base_name, models in groups.items():
                        if models['DFF']:
                            from .. import _ipl_entry_from_obj
                            entries.append(_ipl_entry_from_obj(models['DFF']))
                        if models['LOD']:
                            lod_entry = _ipl_entry_from_obj(models['LOD'])
                            lod_entry.model_name = "LOD" + base_name
                            entries.append(lod_entry)
                    ipl_path = bpy.path.abspath(self.ipl_upsert_path)
                    updated, added = upsert_ipl(ipl_path, entries)
                    all_exported.append(f"IPL: +{added} ~{updated}")
                except Exception as e:
                    all_errors.append(f"IPL upsert: {e}")
            else:
                ipl_path = os.path.join(directory, "objects.ipl")
                try:
                    from .ipl_export import export_ipl as inu_export_ipl
                    inu_export_ipl(filepath=ipl_path, objects=mesh_objects)
                    all_exported.append("objects.ipl")
                except Exception as e:
                    all_errors.append(f"IPL: {e}")

        # Library COL — one multi-entry .col after per-group loop
        if self.col_library and library_col_objects:
            context.workspace.status_text_set(
                f"{T('INU Export:')} library COL ({len(library_col_objects)} models)")
            try:
                from .col_export import export_col_library
                lib_name = self.col_library_name or 'collision'
                lib_path = os.path.join(directory, f"{lib_name}.col")
                original_locations = {}
                for obj in library_col_objects:
                    original_locations[obj.name] = obj.location.copy()
                    obj.location = (0, 0, 0)
                count = export_col_library(lib_path, library_col_objects, version=3)
                for obj in library_col_objects:
                    if obj.name in original_locations:
                        obj.location = original_locations[obj.name]
                all_exported.append(f"{lib_name}.col ({count} records)")
            except Exception as e:
                all_errors.append(f"col library: {e}")

        wm.progress_end()
        context.workspace.status_text_set(None)

        # Restore prelight
        for obj in prelight_was_on:
            setup_prelight_preview(obj, enable=True)

        # Report
        if all_exported:
            self.report({'INFO'}, f"INU Export: {len(all_exported)} — {', '.join(all_exported)}")
        if all_errors:
            self.report({'WARNING'}, f"{T('Ошибки:')} {'; '.join(all_errors)}")
        if not all_exported and not all_errors:
            self.report({'WARNING'}, T("Нечего экспортировать"))

        return {'FINISHED'} if all_exported else {'CANCELLED'}


classes = (
    GTATOOLS_OT_inu_import,
    GTATOOLS_OT_export_all,
    GTATOOLS_OT_inu_export,
)
