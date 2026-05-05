# INU_tools.ops.id_manager_ops — ID manager (auto-assign / clear / extend / GC / sync) + ID preset CRUD.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import os
import bpy
from bpy.props import (
    StringProperty, BoolProperty, IntProperty, EnumProperty,
)

from .. import T


class GTATOOLS_OT_id_manager_open_file(bpy.types.Operator):
    """Открыть файл активного ID пресета в текстовом редакторе"""
    bl_idname = "gtatools.id_manager_open_file"
    bl_label = "INU: Open ID File"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import get_file_path
        import subprocess, sys
        filepath = get_file_path()
        if not os.path.isfile(filepath):
            self.report({'ERROR'}, T("Файл ID не найден. Нажмите 'Создать файл ID'"))
            return {'CANCELLED'}
        if sys.platform == 'win32':
            os.startfile(filepath)
        else:
            subprocess.Popen(['xdg-open', filepath])
        self.report({'INFO'}, f"{T('Открыт:')} {filepath}")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_release(bpy.types.Operator):
    """Освободить ID"""
    bl_idname = "gtatools.id_manager_release"
    bl_label = "INU: Release ID"
    bl_options = {'REGISTER'}

    model_id: IntProperty()

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import release_id
        # Reset model_id on scene objects that use this ID
        for obj in bpy.data.objects:
            inu = getattr(obj, 'inu', None)
            if inu and inu.model_id == self.model_id:
                inu.model_id = 0
        release_id(self.model_id)
        self.report({'INFO'}, f"ID {self.model_id} {T('освобождён')}")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_auto_assign(bpy.types.Operator):
    """Назначить ID всем выделенным объектам с Model ID = 0"""
    bl_idname = "gtatools.id_manager_auto_assign"
    bl_label = "INU: Auto Assign IDs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import allocate_id, sync_scene_to_preset

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        # Bring the preset in line with the scene before allocating.
        # Map-imported objects (or anything hand-edited) may carry IDs
        # that the preset has never heard of; without this sync those
        # IDs stay flagged as free in the preset but get silently
        # skipped during allocation — a classic source of gaps.
        sync_scene_to_preset(bpy.data.objects)

        # Group by base_name, order: DFF then LOD per group (skip COL)
        pairs = {}  # base_name -> {'DFF': obj, 'LOD': obj}
        for obj in objs:
            inu = getattr(obj, 'inu', None)
            if not inu or inu.model_id != 0:
                continue
            from ..tools.model_utils import get_model_type
            model_type, base_name = get_model_type(obj)
            if model_type == 'COL':
                continue
            if base_name not in pairs:
                pairs[base_name] = {'DFF': None, 'LOD': None}
            if model_type in ('DFF', 'LOD'):
                pairs[base_name][model_type] = obj

        # Build ordered list: DFF, LOD, DFF, LOD...
        ordered = []
        for base_name in pairs:
            if pairs[base_name]['DFF']:
                ordered.append(pairs[base_name]['DFF'])
            if pairs[base_name]['LOD']:
                ordered.append(pairs[base_name]['LOD'])

        assigned = 0
        for obj in ordered:
            model_type, base_name = get_model_type(obj)
            from .. import _clean_model_name_ide
            clean_name = _clean_model_name_ide(obj.name)

            if model_type == 'LOD':
                display_name = "LOD" + clean_name
            else:
                display_name = clean_name

            new_id = allocate_id(display_name)
            if new_id is None:
                self.report({'ERROR'}, T("Нет свободных ID в активном пресете"))
                return {'CANCELLED'}
            obj.inu.model_id = new_id
            assigned += 1

        self.report({'INFO'}, f"{T('Назначено ID:')} {assigned}")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_assign_from(bpy.types.Operator):
    """Назначить последовательные ID выделенным объектам начиная с указанного"""
    bl_idname = "gtatools.id_manager_assign_from"
    bl_label = "INU: Assign IDs from..."
    bl_options = {'REGISTER', 'UNDO'}

    start_id: IntProperty(
        name="Start ID",
        default=321,
        min=1,
        description=T("Начальный ID для назначения"),
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import get_used_ids, reserve_id, sync_scene_to_preset

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        # Sync first so the preset reflects every ID that's already
        # placed in the scene. Otherwise we'd skip around those IDs
        # (because they're taken by some scene object) while leaving
        # them visibly "free" in the preset — that's the mysterious
        # gap users see after running this operator.
        sync_scene_to_preset(bpy.data.objects)

        used = set(get_used_ids().keys())
        # Also collect IDs already on scene objects (belt and braces:
        # the sync above should have covered these, but a preset that
        # has been cleared after the sync would miss them).
        for o in bpy.data.objects:
            if o.type == 'MESH' and hasattr(o, 'inu') and o.inu.model_id > 0:
                used.add(o.inu.model_id)

        current_id = self.start_id
        assigned = 0
        for obj in objs:
            if hasattr(obj, 'inu'):
                # Skip occupied IDs
                while current_id in used:
                    current_id += 1
                obj.inu.model_id = current_id
                # Reserve in preset too — otherwise the preset would
                # keep showing these IDs as free and the next Auto
                # Assign run would clash.
                reserve_id(current_id, obj.name)
                used.add(current_id)
                current_id += 1
                assigned += 1

        self.report({'INFO'}, f"{T('Назначено ID:')} {assigned} ({self.start_id}+)")
        return {'FINISHED'}


class GTATOOLS_OT_batch_set_type(bpy.types.Operator):
    """Массовое переключение типа объектов (OBJ/COL/SHA/2DFX/NON)"""
    bl_idname = "gtatools.batch_set_type"
    bl_label = "INU: Batch Set Type"
    bl_options = {'REGISTER', 'UNDO'}

    obj_type: EnumProperty(
        items=[
            ('OBJ', 'Object', ''),
            ('COL', 'Collision', ''),
            ('SHA', 'Shadow', ''),
            ('NON', "Don't export", ''),
        ],
        name="Type",
    )

    def execute(self, context):
        from ..tools.model_utils import get_model_type, _get_suffixes, _get_prefixes

        suffixes = _get_suffixes()
        prefixes = _get_prefixes()

        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH' or not hasattr(obj, 'inu'):
                continue

            # Get current base name
            _, base = get_model_type(obj)
            if not base:
                base = obj.name

            # Set internal type
            obj.inu.type = self.obj_type

            # Rename: base + new suffix/prefix
            new_sfx = suffixes.get(self.obj_type, '')
            new_pfx = prefixes.get(self.obj_type, '')
            if new_sfx:
                obj.name = base + new_sfx
            elif new_pfx:
                obj.name = new_pfx + base
            else:
                obj.name = base

            count += 1
        self.report({'INFO'}, f"{self.obj_type}: {count}")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_clear_selected(bpy.types.Operator):
    """Очистить Model ID у выделенных объектов"""
    bl_idname = "gtatools.id_manager_clear_selected"
    bl_label = "INU: Clear Selected IDs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import release_id

        # Snapshot which (obj, id) pairs we're clearing — then wipe
        # their scene IDs and finally release from the preset only
        # those IDs no other scene object still claims. Without this
        # check, clearing a duplicate (Shift+D gives copies the same
        # inu.model_id as the original) would free the preset slot
        # while the original is still visually using it.
        to_clear = []
        for obj in context.selected_objects:
            if obj.type == 'MESH' and hasattr(obj, 'inu'):
                mid = obj.inu.model_id
                if mid > 0:
                    to_clear.append((obj, mid))

        for obj, _mid in to_clear:
            obj.inu.model_id = 0

        remaining = {
            o.inu.model_id for o in bpy.data.objects
            if o.type == 'MESH' and hasattr(o, 'inu') and o.inu.model_id > 0
        }

        released = 0
        for _obj, mid in to_clear:
            if mid not in remaining:
                release_id(mid)
                released += 1

        count = len(to_clear)
        self.report(
            {'INFO'},
            f"{T('Очищено ID:')} {count} "
            f"({T('освобождено в пресете:')} {released})",
        )
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_clear(bpy.types.Operator):
    """Очистить все занятые ID"""
    bl_idname = "gtatools.id_manager_clear"
    bl_label = "INU: Clear All IDs"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import clear_all
        clear_all()
        self.report({'INFO'}, T("Все ID очищены"))
        return {'FINISHED'}



class GTATOOLS_OT_id_manager_create(bpy.types.Operator):
    """Заполнить активный пресет ID (321-19999, все свободные)"""
    bl_idname = "gtatools.id_manager_create"
    bl_label = "INU: Create ID File"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import create_id_file
        count = create_id_file()
        self.report({'INFO'}, f"ID: 321-19999 ({count})")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_extend(bpy.types.Operator):
    """Добавить ID (Fastman Limit Adjuster)"""
    bl_idname = "gtatools.id_manager_extend"
    bl_label = "INU: Extend IDs"
    bl_options = {'REGISTER'}

    count: IntProperty(
        name="Count",
        default=1000,
        min=100, max=50000,
        description=T("Количество ID для добавления"),
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import extend_ids
        new_start, new_end = extend_ids(self.count)
        self.report({'INFO'}, f"ID: +{self.count} ({new_start}-{new_end})")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_from_game(bpy.types.Operator):
    """Загрузить занятые ID из IDE файлов GTA SA"""
    bl_idname = "gtatools.id_manager_from_game"
    bl_label = "INU: Load IDs from Game"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import populate_from_game
        game_root = bpy.path.abspath(context.scene.gtatools_game_root)
        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}
        count = populate_from_game(game_root)
        self.report({'INFO'}, f"{T('Занято ID:')} {count}")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_gc(bpy.types.Operator):
    """Освободить записи пресета, у которых нет соответствующего объекта в сцене"""
    bl_idname = "gtatools.id_manager_gc"
    bl_label = "INU: Free phantom IDs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import gc_preset
        released = gc_preset(bpy.data.objects)
        self.report(
            {'INFO'},
            f"{T('Освобождено фантомных ID:')} {released}",
        )
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_sync_scene(bpy.types.Operator):
    """Добавить ID из объектов сцены в менеджер"""
    bl_idname = "gtatools.id_manager_sync_scene"
    bl_label = "INU: Sync Scene IDs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .. import _id_preset_sync
        _id_preset_sync(context)
        from ..data.id_manager import _load, _save
        from ..tools.model_utils import get_model_type

        entries = _load()
        existing = {id_num for id_num, _ in entries}

        added = 0
        for obj in bpy.data.objects:
            if obj.type != 'MESH' or not hasattr(obj, 'inu'):
                continue
            mid = obj.inu.model_id
            if mid > 0 and mid not in existing:
                from ..tools.model_utils import get_model_type
                _, base = get_model_type(obj)
                entries.append((mid, base or obj.name))
                existing.add(mid)
                added += 1
            elif mid > 0 and mid in existing:
                # Update name if it was free (None)
                for i, (eid, ename) in enumerate(entries):
                    if eid == mid and ename is None:
                        _, base = get_model_type(obj)
                        entries[i] = (mid, base or obj.name)
                        added += 1
                        break

        if added > 0:
            _save(entries)
        self.report({'INFO'}, f"{T('Добавлено ID:')} {added}")
        return {'FINISHED'}


class GTATOOLS_OT_id_preset_new(bpy.types.Operator):
    """Создать новый пресет ID.

    Пустой пресет создаётся готовым к `Создать файл ID` (Заполнить 321-19999).
    Опция «Скопировать с активного» дублирует текущий файл ID, чтобы не
    начинать с нуля, если часть ID уже назначена.
    """
    bl_idname = "gtatools.id_preset_new"
    bl_label = "INU: New ID Preset"
    bl_options = {'REGISTER'}

    name: StringProperty(
        name=T("Название"),
        description=T("Имя нового пресета. Будет сохранён как data/id_presets/<имя>.txt"),
        default="",
    )
    copy_from_active: BoolProperty(
        name=T("Скопировать с активного"),
        description=T("Создать пресет как копию текущего активного"),
        default=False,
    )

    def invoke(self, context, event):
        self.name = ""
        return context.window_manager.invoke_props_dialog(self, width=320)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'name')
        layout.prop(self, 'copy_from_active')

    def execute(self, context):
        from ..data.id_manager import create_preset, get_active_preset
        name = (self.name or '').strip()
        if not name:
            self.report({'ERROR'}, T("Введите название пресета"))
            return {'CANCELLED'}
        src = get_active_preset() if self.copy_from_active else None
        if not create_preset(name, copy_from=src):
            self.report({'ERROR'}, T("Пресет уже существует или не удалось создать"))
            return {'CANCELLED'}
        # Switch to the newly created preset
        try:
            context.scene.gtatools_id_preset = name
        except Exception:
            pass
        self.report({'INFO'}, f"{T('Создан пресет:')} {name}")
        return {'FINISHED'}


class GTATOOLS_OT_id_preset_delete(bpy.types.Operator):
    """Удалить активный пресет ID. Пресет «default» удалить нельзя"""
    bl_idname = "gtatools.id_preset_delete"
    bl_label = "INU: Delete ID Preset"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        from ..data.id_manager import delete_preset, list_presets
        current = getattr(context.scene, 'gtatools_id_preset', 'default')
        if current == 'default':
            self.report({'ERROR'}, T("Пресет 'default' удалить нельзя"))
            return {'CANCELLED'}
        if not delete_preset(current):
            self.report({'ERROR'}, T("Не удалось удалить пресет"))
            return {'CANCELLED'}
        # Fall back to the first remaining preset
        remaining = list_presets()
        try:
            context.scene.gtatools_id_preset = remaining[0] if remaining else 'default'
        except Exception:
            pass
        self.report({'INFO'}, f"{T('Удалён пресет:')} {current}")
        return {'FINISHED'}


class GTATOOLS_OT_id_preset_rename(bpy.types.Operator):
    """Переименовать активный пресет ID"""
    bl_idname = "gtatools.id_preset_rename"
    bl_label = "INU: Rename ID Preset"
    bl_options = {'REGISTER'}

    new_name: StringProperty(
        name=T("Новое название"),
        default="",
    )

    def invoke(self, context, event):
        self.new_name = getattr(context.scene, 'gtatools_id_preset', '') or ''
        return context.window_manager.invoke_props_dialog(self, width=320)

    def draw(self, context):
        self.layout.prop(self, 'new_name')

    def execute(self, context):
        from ..data.id_manager import rename_preset
        current = getattr(context.scene, 'gtatools_id_preset', 'default')
        new = (self.new_name or '').strip()
        if not new or new == current:
            self.report({'ERROR'}, T("Введите новое название"))
            return {'CANCELLED'}
        if not rename_preset(current, new):
            self.report({'ERROR'}, T("Не удалось переименовать (имя занято или ошибка)"))
            return {'CANCELLED'}
        try:
            context.scene.gtatools_id_preset = new
        except Exception:
            pass
        self.report({'INFO'}, f"{T('Переименован:')} {current} → {new}")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_id_manager_open_file,
    GTATOOLS_OT_id_manager_release,
    GTATOOLS_OT_id_manager_auto_assign,
    GTATOOLS_OT_id_manager_assign_from,
    GTATOOLS_OT_batch_set_type,
    GTATOOLS_OT_id_manager_clear_selected,
    GTATOOLS_OT_id_manager_clear,
    GTATOOLS_OT_id_manager_create,
    GTATOOLS_OT_id_manager_extend,
    GTATOOLS_OT_id_manager_from_game,
    GTATOOLS_OT_id_manager_gc,
    GTATOOLS_OT_id_manager_sync_scene,
    GTATOOLS_OT_id_preset_new,
    GTATOOLS_OT_id_preset_delete,
    GTATOOLS_OT_id_preset_rename,
)
