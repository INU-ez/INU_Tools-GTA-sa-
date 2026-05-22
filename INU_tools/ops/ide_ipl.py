# INU_tools.ops.ide_ipl — IDE / IPL panel operators.
#
# Phase 3 batch 4 (2026-04-26): 11 operators moved from __init__.py.
# Three small helpers (_ide_entry_from_obj, _ipl_entry_from_obj,
# _clean_model_name_ide) stay in __init__.py because INU Import/Export
# and other ops still use them; this module pulls them in lazily.

import os
import bpy
from bpy.props import (
    BoolProperty, StringProperty,
)
from .. import T


class GTATOOLS_OT_upsert_ide(bpy.types.Operator):
    """Добавить / обновить запись в существующем IDE файле (авто-LOD)"""
    bl_idname = "gtatools.upsert_ide"
    bl_label = "INU: Add to IDE"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ide import upsert_ide
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ide_path)
        if not filepath:
            self.report({'ERROR'}, T("Укажите путь к IDE файлу"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        entries = []
        processed_names = set()
        for obj in objs:
            from ..tools.model_utils import get_model_type
            model_type, base_name = get_model_type(obj)
            if base_name in processed_names:
                continue
            processed_names.add(base_name)

            # Add DFF entry
            dff_obj = obj if model_type == 'DFF' else None
            lod_obj = obj if model_type == 'LOD' else None

            # Auto-find paired LOD/DFF among selected
            for o2 in objs:
                mt2, bn2 = get_model_type(o2)
                if bn2 == base_name and o2 != obj:
                    if mt2 == 'LOD':
                        lod_obj = o2
                    elif mt2 == 'DFF':
                        dff_obj = o2

            if dff_obj:
                from .. import _ide_entry_from_obj
                entries.append(_ide_entry_from_obj(dff_obj))
            if lod_obj:
                lod_entry = _ide_entry_from_obj(lod_obj)
                # LOD model name: LOD + base_name
                lod_entry.model_name = "LOD" + base_name
                # LOD TXD = same as DFF TXD (base_name without suffixes)
                from .. import _clean_model_name_ide
                lod_entry.txd_name = _clean_model_name_ide(base_name)
                # LOD model_id = DFF model_id + 1 if LOD has no ID
                if lod_entry.model_id == 0 and dff_obj:
                    dff_id = getattr(dff_obj.inu, 'model_id', 0)
                    if dff_id > 0:
                        lod_entry.model_id = dff_id + 1
                # LOD draw distance from DFF's lod_draw_distance property
                if dff_obj:
                    lod_entry.draw_distance = dff_obj.inu.lod_draw_distance
                elif lod_obj.inu.draw_distance in (299.0, 300.0):
                    lod_entry.draw_distance = 999.0
                entries.append(lod_entry)

        # Validate model IDs
        zero_ids = [e for e in entries if e.model_id == 0]
        if zero_ids:
            self.report({'WARNING'}, f"{len(zero_ids)} {T('объектов с Model ID = 0, задайте ID в свойствах')}")

        updated, added = upsert_ide(filepath, entries)
        self.report({'INFO'}, f"IDE: {T('обновлено')} {updated}, {T('добавлено')} {added}")
        return {'FINISHED'}


class GTATOOLS_OT_upsert_ipl(bpy.types.Operator):
    """Добавить / обновить запись в существующем IPL файле (авто-LOD привязка)"""
    bl_idname = "gtatools.upsert_ipl"
    bl_label = "INU: Add to IPL"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ipl import upsert_ipl, read_ipl
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ipl_path)
        if not filepath:
            self.report({'ERROR'}, T("Укажите путь к IPL файлу"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        # Group objects by base name, find DFF+LOD pairs
        pairs = {}  # base_name -> {'DFF': obj, 'LOD': obj}
        for obj in objs:
            from ..tools.model_utils import get_model_type
            model_type, base_name = get_model_type(obj)
            if not base_name:
                continue
            if base_name not in pairs:
                pairs[base_name] = {'DFF': None, 'LOD': None}
            if model_type in ('DFF', 'LOD'):
                pairs[base_name][model_type] = obj

        # Read existing IPL to count entries that will remain (excluding ones we'll replace)
        existing_count = 0
        if os.path.isfile(filepath):
            try:
                existing_ipl = read_ipl(filepath)
                # Collect model IDs we're about to upsert
                our_ids = set()
                for pair in pairs.values():
                    if pair['DFF'] and hasattr(pair['DFF'], 'inu'):
                        our_ids.add(pair['DFF'].inu.model_id)
                    if pair['LOD'] and hasattr(pair['LOD'], 'inu'):
                        our_ids.add(pair['LOD'].inu.model_id)
                # Count entries that won't be replaced
                existing_count = sum(1 for inst in existing_ipl.instances if inst.model_id not in our_ids)
            except:
                pass

        # Build entries in pairs: DFF, LOD, DFF, LOD...
        entries = []
        entry_index = existing_count

        for base_name, pair in pairs.items():
            dff_entry = None
            lod_entry = None

            if pair['DFF']:
                from .. import _ipl_entry_from_obj
                dff_entry = _ipl_entry_from_obj(pair['DFF'])
                entry_index += 1

            if pair['LOD']:
                lod_entry = _ipl_entry_from_obj(pair['LOD'])
                lod_entry.model_name = "LOD" + base_name
                lod_entry.lod_index = -1
                # Auto-assign LOD model_id = DFF model_id + 1
                if lod_entry.model_id == 0 and pair['DFF']:
                    dff_id = getattr(pair['DFF'].inu, 'model_id', 0)
                    if dff_id > 0:
                        lod_entry.model_id = dff_id + 1
                lod_idx = entry_index
                entry_index += 1

            # Set DFF lod_index pointing to LOD
            if dff_entry and lod_entry:
                dff_entry.lod_index = lod_idx
                # Update object property too
                if pair['DFF']:
                    pair['DFF'].inu.lod_index = lod_idx
            elif dff_entry:
                dff_entry.lod_index = -1
                if pair['DFF']:
                    pair['DFF'].inu.lod_index = -1

            if dff_entry:
                entries.append(dff_entry)
            if lod_entry:
                entries.append(lod_entry)

            if not pair['DFF'] and not pair['LOD']:
                for obj in objs:
                    mt, bn = get_model_type(obj)
                    if bn == base_name:
                        entries.append(_ipl_entry_from_obj(obj))
                        entry_index += 1
                        break

        zero_ids = [e for e in entries if e.model_id == 0]
        if zero_ids:
            self.report({'WARNING'}, f"{len(zero_ids)} {T('объектов с Model ID = 0, задайте ID в свойствах')}")

        updated, added = upsert_ipl(filepath, entries)
        msg = f"IPL: {T('обновлено')} {updated}, {T('добавлено')} {added}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_remove_ide(bpy.types.Operator):
    """Удалить запись из IDE файла по Model ID"""
    bl_idname = "gtatools.remove_ide"
    bl_label = "INU: Remove from IDE"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ide import remove_ide
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ide_path)
        if not filepath:
            self.report({'ERROR'}, T("Укажите путь к IDE файлу"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        model_ids = set()
        for o in objs:
            inu = getattr(o, 'inu', None)
            mid = getattr(inu, 'model_id', 0) if inu else 0
            if mid > 0:
                model_ids.add(mid)

        if not model_ids:
            self.report({'ERROR'}, T("Нет объектов с Model ID > 0"))
            return {'CANCELLED'}

        removed = remove_ide(filepath, model_ids)
        self.report({'INFO'}, f"IDE: {T('удалено')} {removed}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_ipl(bpy.types.Operator):
    """Удалить запись из IPL файла по Model ID"""
    bl_idname = "gtatools.remove_ipl"
    bl_label = "INU: Remove from IPL"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ipl import remove_ipl
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ipl_path)
        if not filepath:
            self.report({'ERROR'}, T("Укажите путь к IPL файлу"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        model_ids = set()
        for o in objs:
            inu = getattr(o, 'inu', None)
            mid = getattr(inu, 'model_id', 0) if inu else 0
            if mid > 0:
                model_ids.add(mid)

        if not model_ids:
            self.report({'ERROR'}, T("Нет объектов с Model ID > 0"))
            return {'CANCELLED'}

        removed = remove_ipl(filepath, model_ids)

        # Reset lod_index to -1 on removed objects
        for o in objs:
            if hasattr(o, 'inu'):
                o.inu.lod_index = -1

        self.report({'INFO'}, f"IPL: {T('удалено')} {removed}")
        return {'FINISHED'}


def _ensure_extension(filepath: str, ext: str) -> str:
    """Append ``ext`` (e.g. '.ide') to ``filepath`` if it isn't already
    there (case-insensitive). Operators here don't use ExportHelper so
    Blender's file dialog happily accepts ``hospital_1a`` without the
    extension and we'd silently write an extensionless file — which the
    user has to rename by hand before the game / IMG editor will load
    it.

    Edge cases:
      * Empty / None input → returned as-is (caller already handles
        empty paths elsewhere).
      * Path already ends with ``ext`` (any casing) → unchanged.
      * Path ends with a different extension (e.g. user typed
        ``foo.txt``) → still appended so we get ``foo.txt.ide``. The
        ``filter_glob='*.ide'`` makes that unlikely in practice but
        keeping the rule simple beats "smart" replacement that could
        mangle filenames with dots in them.
    """
    if not filepath:
        return filepath
    if filepath.lower().endswith(ext.lower()):
        return filepath
    return filepath + ext


class GTATOOLS_OT_export_ide(bpy.types.Operator):
    """Экспорт IDE (определение объектов GTA SA)"""
    bl_idname = "gtatools.export_ide"
    bl_label = "INU: Export IDE (.ide)"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ide", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "model.ide"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ide_export import export_ide as inu_export_ide
        self.filepath = _ensure_extension(self.filepath, ".ide")
        try:
            objs = [o for o in context.selected_objects if o.type == 'MESH']
            inu_export_ide(filepath=self.filepath, objects=objs)
            self.report({'INFO'}, f"Exported IDE: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IDE export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_ipl(bpy.types.Operator):
    """Экспорт IPL (размещение объектов GTA SA)"""
    bl_idname = "gtatools.export_ipl"
    bl_label = "INU: Export IPL (.ipl)"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})
    binary: BoolProperty(
        name="Binary (bnry)",
        description=T("Писать IPL в бинарном формате (только inst+cars)"),
        default=False,
    )

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "model.ipl"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "binary")

    def execute(self, context):
        from .ipl_export import export_ipl as inu_export_ipl
        self.filepath = _ensure_extension(self.filepath, ".ipl")
        try:
            objs = [o for o in context.selected_objects if o.type == 'MESH']
            inu_export_ipl(filepath=self.filepath, objects=objs, binary=self.binary)
            self.report({'INFO'}, f"Exported IPL: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_ipl_sections(bpy.types.Operator):
    """Импорт секций IPL (cull, grge, enex, pick, cars, auzo, jump, occl)"""
    bl_idname = "gtatools.import_ipl_sections"
    bl_label = "INU: Import IPL Sections"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from ..core.ipl import read_ipl
        from .ipl_sections import import_ipl_sections
        try:
            ipl = read_ipl(self.filepath)
            result = import_ipl_sections(ipl)
            total = sum(len(v) for v in result.values())
            sections = ", ".join(f"{k}: {len(v)}" for k, v in result.items() if v)
            self.report({'INFO'}, f"{T('Импортировано:')} {total} ({sections})")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL sections import: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_ipl_sections(bpy.types.Operator):
    """Экспорт секций IPL из коллекций IPL_* в файл"""
    bl_idname = "gtatools.export_ipl_sections"
    bl_label = "INU: Export IPL Sections"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "sections.ipl"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from ..core.ipl import IplFile, write_ipl
        from .ipl_sections import export_ipl_sections
        self.filepath = _ensure_extension(self.filepath, ".ipl")
        try:
            sections = export_ipl_sections()
            ipl = IplFile(
                culls=sections.get('cull', []),
                garages=sections.get('grge', []),
                enexs=sections.get('enex', []),
                pickups=sections.get('pick', []),
                cars=sections.get('cars', []),
                auzos=sections.get('auzo', []),
                jumps=sections.get('jump', []),
                occls=sections.get('occl', []),
                zones=sections.get('zone', []),
            )
            from ..core import game_versions as gv
            write_ipl(self.filepath, ipl,
                      game=gv.game_of_scene(context.scene))
            total = sum(len(v) for v in sections.values())
            self.report({'INFO'}, f"Exported {total} IPL section entries")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL sections export: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_ide(bpy.types.Operator):
    """Импорт IDE (определения объектов GTA SA)"""
    bl_idname = "gtatools.import_ide"
    bl_label = "INU: Import IDE (.ide)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ide", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ide_import import import_ide as inu_import_ide
        try:
            matched = inu_import_ide(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"IDE: {len(matched)} objects matched")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IDE import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_ipl(bpy.types.Operator):
    """Импорт IPL (размещение объектов GTA SA)"""
    bl_idname = "gtatools.import_ipl"
    bl_label = "INU: Import IPL (.ipl)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    import_game: bpy.props.EnumProperty(
        name=T("Игра"),
        description=T("Из какой игры импортируем IPL. Auto — по числу колонок в inst-секции"),
        items=[
            ('AUTO', T("Авто-определение"), ""),
            ('III',  "GTA III",  ""),
            ('VC',   "Vice City", ""),
            ('SA',   "San Andreas", ""),
        ],
        default='AUTO')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        self.layout.prop(self, "import_game")

    def execute(self, context):
        from .ipl_import import import_ipl as inu_import_ipl
        try:
            placed = inu_import_ipl(filepath=self.filepath, context=context)
            from ..core import game_versions as gv
            if self.import_game == 'AUTO':
                detected = gv.detect_game_from_ipl(self.filepath)
            else:
                detected = self.import_game
            switched = gv.maybe_set_game_from_import(context.scene, detected)
            tag = f" → game={detected}" if switched else ""
            self.report({'INFO'}, f"IPL: {len(placed)} objects placed{tag}")
            if not switched:
                warn = gv.check_game_mismatch_warning(context.scene, detected)
                if warn:
                    self.report({'WARNING'}, warn)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_replace_ipl_placeholders(bpy.types.Operator):
    """Заменить IPL Empty-плейсхолдеры на модели из сцены"""
    bl_idname = "gtatools.replace_ipl_placeholders"
    bl_label = "INU: Replace IPL Placeholders"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        replaced = 0
        # Build lookup from scene meshes
        mesh_lookup = {}
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                from .. import _clean_name_typed_ipl
                clean, stype = _clean_name_typed_ipl(obj.name)
                low = clean.lower()
                if low not in mesh_lookup:
                    mesh_lookup[low] = {}
                if stype not in mesh_lookup[low]:
                    mesh_lookup[low][stype] = obj

        for obj in list(bpy.data.objects):
            if obj.type != 'EMPTY' or not obj.get('ipl_placeholder'):
                continue

            model_name = obj.get('ipl_model_name', obj.name.replace('_empty', ''))
            key = model_name.lower()
            from ..core.ipl import is_lod_name, strip_lod_marker
            is_lod = is_lod_name(model_name)

            # Find matching mesh
            mesh_obj = None
            if is_lod:
                base = strip_lod_marker(model_name).lower()
                variants = mesh_lookup.get(base, {})
                mesh_obj = variants.get('LOD') or variants.get('DFF')
            else:
                variants = mesh_lookup.get(key, {})
                mesh_obj = variants.get('DFF') or variants.get('OTHER')

            if not mesh_obj:
                continue

            # Move existing model to placeholder position
            mesh_obj.location = obj.location.copy()
            mesh_obj.rotation_mode = 'QUATERNION'
            mesh_obj.rotation_quaternion = obj.rotation_quaternion.copy()

            # Copy IPL properties
            mesh_obj.inu.model_id = obj.inu.model_id
            mesh_obj.inu.interior_id = obj.inu.interior_id
            mesh_obj.inu.lod_index = obj.inu.lod_index

            # Remove placeholder
            bpy.data.objects.remove(obj, do_unlink=True)
            replaced += 1

        self.report({'INFO'}, f"{T('Заменено:')} {replaced}")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_upsert_ide,
    GTATOOLS_OT_upsert_ipl,
    GTATOOLS_OT_remove_ide,
    GTATOOLS_OT_remove_ipl,
    GTATOOLS_OT_export_ide,
    GTATOOLS_OT_export_ipl,
    GTATOOLS_OT_import_ipl_sections,
    GTATOOLS_OT_export_ipl_sections,
    GTATOOLS_OT_import_ide,
    GTATOOLS_OT_import_ipl,
    GTATOOLS_OT_replace_ipl_placeholders,
)
