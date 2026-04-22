# INU_tools(gta_sa) for Blender 4.4+
# Copyright (C) 2024-2026  INU
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Material/Object property names are compatible with DragonFF by Parik (GPL-3.0)
# https://github.com/Parik27/DragonFF
#
# Объединённая панель инструментов для работы с GTA SA моделями
# Включает: Export (DFF, COL, LOD, TXD), Prelight, Lightmap Generator

bl_info = {
    "name": "INU_tools(gta_sa)",
    "author": "INU",
    "version": (1, 6, 4),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar (N) > GTA Tools",
    "description": "Toolset for GTA SA models",
    "warning": "Experimental features — not fully tested in-game",
    "category": "3D View",
}

# Changelog:
# v1.6.4 - (pre-release) 11 экспериментальных фич — проверка в игре ещё не проведена
#        - Map Export: единый экспорт сцены → DFF + COL + TXD + IDE + IPL одной кнопкой
#          (tools/map_export.py, авто-паринг LOD/COL, пул ID из настройки для пустых model_id=0)
#        - Binary IPL Write: запись в формате `bnry` (только inst+cars, как у Rockstar)
#          (core/ipl.py _write_binary_ipl + чекбокс Binary в GTATOOLS_OT_export_ipl)
#        - UV-анимация в DFF: простой U/V-скролл через чанки 0x2B + 0x135
#          (core/dff.py UVAnim/UVAnimDict, material props uv_anim_write/speed_u/v/duration)
#          ОГРАНИЧЕНИЕ: только запись, обратное чтение не реализовано
#        - Breakable Objects: чанк 0x253F2FD + сила разрушения per-object
#          (core/dff.py BreakableData, обj.inu.breakable/breakable_force)
#        - IFP Batch Import: папка с .ifp → стек на NLA-треке armature
#          (ops/ifp_import.py batch_apply_sequential, режимы NLA/Actions, зазор между клипами)
#        - GTA Material Panel: вкладка Properties → Material с dropdown пресетов
#          (Generic/Vehicle Body/Vehicle Glass/Ped/Env/Dual/Specular + vehicle color slot)
#        - Bitmaps Manager: scan missing / resolve from folder / batch copy / find duplicates
#          (tools/bitmaps_manager.py, панель в N-Sidebar GTA Tools)
#        - CST IO: текстовая сериализация COL (формат Steve's COL Editor, с shadow mesh)
#          (core/cst.py + ops/cst_import.py + ops/cst_export.py)
#        - Vehicle Scale Helper: пропорциональное масштабирование иерархии машины
#          (tools/vehicle_scale.py, опция Dummies Only)
#        - Train Station Markers: видимые Empty-сферы на станциях train-трека
#          (ops/ifp_import.py _refresh_station_markers)
#        - Roadblocks & Traffic Lights: переключение per-node флагов на выделенных path-IPL точках
#          (core/paths.py PATH_FLAG_* константы, ops/ifp_import.py GTATOOLS_OT_path_node_flag)
#        - FLA4 Path Format: чтение/запись расширенных nodes*.dat (spawn/speed/lanes per-node)
#          (core/paths.py FLA4_MAGIC + ветки в read_nodes/write_nodes, чекбокс в Export Path Nodes)
#        - Фиксы ревью: UV_ANIM_KEYFRAME_SIZE 36→32 (pack был короче на 4 байта),
#          path_node_flag правильный маппинг spline→IDProp через пропуск empty-нод,
#          station markers через matrix_parent_inverse.identity() + local pt.co,
#          map_export переключение в OBJECT mode перед select_all,
#          UVAnim.node_to_uv дефолт (1,0,...) вместо (0,...) — иначе анимация инертна
#        - Bitmaps Manager group_by_txd: читает obj.inu.txd_name (а не mat.get('txd_name'))
#          через обратный индекс материал→TXDs
#        - DOCS.md + DOCS_rus.md: новая секция "Experimental (v1.6.4)" с 12 подразделами
#        - README.md + README_rus.md: секция "Experimental (v1.6.4)" с warning-блоком,
#          Coming Soon сжат до одного пункта (Vehicles Phase 2+)
#        - bl_info warning: "Experimental features — not fully tested in-game"
#          (оранжевая метка в Blender Add-ons panel)
# v1.6.3 - Particle Effects: полноценный редактор GTA SA effects.fxp
#        - Парсер effects.fxp (text-based, 82 эффекта), кэш с auto-reload
#        - Симуляция частиц в viewport (30 FPS, до 64 частиц на эмиттер, billboard к камере)
#        - Dropdown выбора эффекта из 82 систем + multi-emitter switching
#        - Редактирование 40+ параметров: цвет, размер, скорость, направление, физика, ветер, гравитация
#        - Keyframe editor для curves (size/color/alpha over lifetime)
#        - Сохранение в effects.fxp с авто-бэкапом (.fxp.bak)
#        - Operators: New, Delete, Switch Emitter, Reload effects.fxp
#        - IDE/IPL Export: очистка .001 дубликатов перед записью
#        - IPL Upsert: поддержка нескольких instances одной модели (match по позиции)
#        - DFF Export: _read_texture идёт через Prelight_Mix/LM_Mix к реальной текстуре
#        - TXD Export: пропускает LM_Texture/Lightmap_Texture ноды
#        - LightMap UV2: Add/Toggle/Remove кнопки в Prelight панели (Multiply blend на UV2)
#        - Prelight Bake: использует loop.normal (smooth shading), пропускает скрытые лампы
#        - Reset Transform: сброс Location/Rotation в (0,0,0) для выделенных мешей
#        - Batch Set Type: массовое назначение OBJ/COL/SHA/NON с автопереименованием
#        - 2DFX: detach all from mesh, список привязанных в UI меша
#        - 2DFX Billboard: переход с timer на draw handler — фикс tracking при смене сцены
#        - DFF Flags: компактный список чекбоксов вместо больших кнопок
#        - Object Properties: новая панель "GTA SA: IDE / IPL" (перенос из N-панели)
#        - Nodes Export: авто-разбиение по зонам карты 8x8 (64 файла nodes0..63.dat)
#        - Nodes Import: мультифайловый импорт (несколько nodes*.dat за раз)
#        - ID Manager: Assign from ID..., Extend IDs (FLA, Fastman Limit Adjuster)
#        - .gitattributes: нормализация LF/CRLF
#        - Документация: Alpha threshold 57% (145/255) — задокументирован hard cutoff в GTA SA
# v1.6.1 - IPL Import: перемещение COL вместе с DFF, Empty с _empty суффиксом в коллекции IPL_Empty, кнопка Заменить Empty
#        - Префиксы моделей (DFF/LOD/COL) в настройках, авто-очистка конфликтов суффикс/префикс
#        - Все import/export используют пользовательские суффиксы/префиксы
#        - Model Links: визуализация связей DFF↔LOD↔COL пунктирными линиями
#        - LOD/COL → DFF: кнопка подтягивания к позиции DFF
#        - Скрытие DFF/LOD/COL по отдельности в панели Проверка
#        - Удалить из IMG по типу выделенного объекта (DFF+TXD / COL / LOD)
#        - Список файлов IMG (UIList с прокруткой и поиском)
#        - Менеджер ID: очистка ID выделенных, синхронизация сцены, создание файла 321-19999
#        - Проверка конфликтов ID (предупреждение в панели)
#        - Normals toggle в панели Pipeline
#        - Drag & Drop TXD с созданием материалов
# v1.6.0 - Import Map: workflow Extract → Build .glb → Import с автосортировкой по коллекциям
#        - BBox Mode: Bounding Box для далёких объектов (300м от выделения)
#        - IPL ZONE секция: парсинг/запись/визуализация зон карты
#        - Динамические регионы из gta.dat
#        - TXD: исправлена декомпрессия RASTER_888, улучшена детекция DXT
#        - GPU NVTT автодетект
#        - UI: объединены Экспорт/Импорт, компактный layout, панель Проверка на русском
#        - Экспорт коллекций (активная коллекция если ничего не выделено)
#        - Убраны: Fake mode, Bounds mode, LOD view, Auto-discover
# v1.4.7 - Export: COL Surface Type — панель выбора типа поверхности коллизии в Material Properties
#        - 179 материалов GTA SA с поиском по названию, запись через DragonFF col_mat_index
# v1.4.6 - Prelight: Post-Processing — новая подпанель пост-обработки vertex colors (Smooth, Contrast, Brightness, Gamma)
#        - Prelight: Fast Bake теперь поддерживает тени (raycast через depsgraph), переключатель Shadows в панели
#        - Export: новая подпанель DFF Flags — отображает флаги геометрии DragonFF (Light, Normals, Pipeline, UV Maps и др.)
# v1.4.5 - Export All: массовый экспорт нескольких групп моделей (Model1_DFF + Model2_DFF и т.д.)
#        - Lightmap Generator: панель снова доступна в интерфейсе
# v1.4.4 - Prelight: Fill Colors - покраска полигонов с пипеткой и системой уровней
#        - Prelight: Scatter Light - рассеивание света с настройками и уровнями
#        - Prelight: убраны лишние заголовки, оставлены только кнопки
#        - Color Attributes: раздельные кнопки создания/удаления Day и Night
#        - Color Attributes: кнопка Day/Night создаёт оба атрибута
#        - Drag-and-Drop: перетаскивание PNG/JPG/TGA из File Browser создаёт материал
#        - INU Tools панель перемещена в Properties > Scene
#        - Удалена пустая вкладка GTA Textures из N-панели
# v1.4.3 - TXD экспорт: исправлена прозрачность DXT3 текстур в игре
#        - TXD экспорт: текстуры с размером не кратным 4 пропускаются с предупреждением
# v1.4.2 - TXD экспорт: добавлен GPU режим через NVIDIA Texture Tools
# v1.4.1 - TXD экспорт: параллельная обработка текстур (до 8x быстрее)
# v1.4.0 - UV Editor: добавлена панель GTA Tools с UV Grid Randomizer и визуализацией сетки
#        - UV Editor: добавлена привязка UV к ближайшей ячейке сетки (Snap to Grid)
#        - UV Editor: добавлен выбор позиции UV в ячейке (9 вариантов выравнивания)
#        - UV Editor: добавлена функция "Связать полигоны" - полигоны с пересекающимися UV перемещаются вместе
#        - GTA Textures: проверка количества материалов (лимит 50)
#        - GTA Textures: загрузка текстуры только для выбранного материала
#        - GTA Textures: автоустановка Specular=0 и подключение Alpha канала
#        - Переведены все описания кнопок на русский язык
# v1.3.0 - Добавлена очистка материалов: объединение дубликатов (.001, .002, etc.)
# v1.2.9 - Добавлена вкладка GTA Textures: автозагрузка текстур по именам материалов
# v1.2.8 - COL экспорт теперь использует версию COL3 (GTA SA) вместо COL1
# v1.2.7 - DFF экспорт: добавлены only_selected=True и export_coll=False для исправления краша
# v1.2.6 - DFF экспорт теперь использует версию GTA SA (v3.6.0.3) вместо GTA 3
# v1.2.5 - Исправление имени модели внутри COL файла (base_name без суффикса COL)
# v1.2.4 - Добавлен прогресс-бар при Export All
# v1.2.3 - Автоустановка типа Collision Object для COL модели перед экспортом
# v1.2.2 - TXD в Export All берёт текстуры из DFF + LOD в один архив
# v1.2.1 - Поиск моделей только среди выделенных объектов
# v1.2.0 - Улучшено определение моделей по суффиксам DFF/LOD/COL (без разделителей)
# v1.1.0 - Добавлен экспорт DFF/COL/LOD/TXD, определение моделей по суффиксам
# v1.0.0 - Начальная версия

import bpy
import bmesh
import math
import re as _re
import struct
import os
import tempfile
import subprocess
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from mathutils import Vector
from bpy.props import StringProperty, BoolProperty, FloatProperty, FloatVectorProperty, IntProperty, CollectionProperty, EnumProperty
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper


# =============================================================================
# LOCALIZATION SYSTEM
# =============================================================================

def get_locale():
    """Get current Blender UI language"""
    try:
        locale = bpy.app.translations.locale
        if locale and locale.startswith('ru'):
            return 'ru'
    except:
        pass
    return 'en'

# Translation dictionary: Russian -> English
from .locale import get_translation

def T(text):
    """Translate text based on Blender UI language.
    Code uses Russian strings as keys. For Russian UI — returns as-is.
    For other languages — looks up translation in locale/<lang>.py files.
    Falls back to English (eng.py) if current language not found.
    """
    locale = get_locale()
    if locale and locale.startswith('ru'):
        return text
    # Try exact locale first, then fall back to English
    tr = get_translation(locale)
    if tr:
        result = tr.get(text)
        if result:
            return result
    # Fallback to English
    eng = get_translation('eng')
    if eng:
        return eng.get(text, text)
    return text


# =============================================================================
# EXTRACTED MODULES
# =============================================================================

from .tools.txd_export import (
    export_txd, check_nvtt_available, write_rw_section_header,
)
from .tools.model_utils import (
    get_model_type, find_related_models, find_selected_models,
    find_all_selected_model_groups, get_base_name_from_selected,
    fix_col_model_name, check_loose_geometry, get_model_textures,
)
from .data.surface_materials import (
    GTA_SA_SURFACE_MATERIALS, COL_SURFACE_ENUM_ITEMS, COL_SURFACE_CATEGORIES,
    _surface_id_to_category, get_col_surface_id, get_surface_name,
    get_base_name_from_selection,
)
from .tools.prelight import (
    GTASAPrelight, average_colors_on_coplanar_faces,
    encode_uv2_to_color_16bit, create_prelight_scene_lights,
    remove_prelight_scene_lights, bake_vertex_colors_from_lights,
    bake_vertex_colors_simple, apply_brightness_offset,
    analyze_vertex_colors, smooth_vertex_colors,
    adjust_vertex_colors_contrast, adjust_vertex_colors_brightness,
    adjust_vertex_colors_gamma, setup_prelight_preview,
    fill_selected_faces, ensure_base_colors, recalculate_colors,
    add_fill_layer, add_scatter_layer, get_scatter_levels,
    remove_scatter_layer, clear_scatter_layers, remove_fill_color,
    remove_fill_color_by_index, get_selected_faces_color,
    fill_selected_faces_with_backup, restore_filled_faces,
    scatter_light_from_selected,
)
# COL Light: import module for mutable globals, classes separately
from .tools import col_light as _col_light_mod
from .tools.col_light import (
    _col_light_invalidate_preview, _col_light_watch_transform,
    GTATOOLS_OT_preview_col_light, GTATOOLS_OT_bake_col_light,
    GTATOOLS_OT_clear_col_light_mats,
)
# UV Tools: import module for mutable globals, classes separately
from .tools import uv_tools as _uv
from .tools.uv_tools import (
    GTATOOLS_OT_toggle_uv_editor, GTATOOLS_OT_toggle_uv_grid,
    GTATOOLS_OT_randomize_uv_grid, GTATOOLS_OT_snap_uv_to_grid,
    GTATOOLS_OT_set_uv_align, GTATOOLS_PT_uv_tools_panel,
    GTATOOLS_OT_add_gtasa_model, VIEW3D_MT_gtasa_add_menu,
    _gtasa_add_menu_draw,
)
from .tools.bitmaps_manager import (
    GTATOOLS_OT_bitmaps_scan, GTATOOLS_OT_bitmaps_resolve,
    GTATOOLS_OT_bitmaps_copy, GTATOOLS_OT_bitmaps_find_dupes,
    GTATOOLS_PT_bitmaps_panel,
)
from .ops.ifp_import import (
    GTATOOLS_OT_ifp_batch_import,
    GTATOOLS_OT_refresh_station_markers,
    GTATOOLS_OT_path_node_flag,
)
from .ops.cst_import import GTATOOLS_OT_import_cst
from .ops.cst_export import GTATOOLS_OT_export_cst
from .tools.vehicle_scale import GTATOOLS_OT_vehicle_scale
from .tools.map_export import (
    GTATOOLS_OT_map_export,
    GTATOOLS_PT_map_export_panel,
)
from .tools.gta_material_panel import (
    GTATOOLS_OT_material_preset,
    GTATOOLS_PT_gta_material_panel,
)
from .tools import icons as _icons

addon_keymaps = []

# =============================================================================
# PROPERTY GROUPS
# =============================================================================

# ── Particle curve keyframe PropertyGroup (used by B1 curve editor) ── #
class INUParticleKeyframe(bpy.types.PropertyGroup):
    """A single FX_KEYFLOAT_DATA entry (time, val) for the curve editor buffer."""
    time: FloatProperty(
        name="Time",
        default=0.0, min=0.0, max=1.0, precision=4,
    )
    val: FloatProperty(
        name="Value",
        default=0.0, precision=4,
    )


# ── Particle effect EnumProperty — dynamic items from effects.fxp ── #
# Module-level cache: EnumProperty items callbacks MUST return the same
# Python objects across calls, otherwise Blender shows garbled strings
# (strings get GC'd). We keep the last returned list alive here.
_particle_enum_items_cache = [('', '<not loaded>', '')]
_particle_enum_cache_key = None  # (path, mtime)


def _particle_effect_enum_items(self, context):
    """Items callback for INUObjectProps.particle_effect_2dfx."""
    global _particle_enum_items_cache, _particle_enum_cache_key
    try:
        game_root = bpy.path.abspath(
            getattr(context.scene, 'gtatools_game_root', '') or ''
        )
        if not game_root or not os.path.isdir(game_root):
            _particle_enum_items_cache = [('', T('<Game Root не задан>'), '')]
            _particle_enum_cache_key = None
            return _particle_enum_items_cache

        path = os.path.join(game_root, 'models', 'effects.fxp')
        if not os.path.isfile(path):
            _particle_enum_items_cache = [('', T('<effects.fxp не найден>'), '')]
            _particle_enum_cache_key = None
            return _particle_enum_items_cache

        mtime = os.path.getmtime(path)
        key = (path, mtime)
        if key == _particle_enum_cache_key:
            return _particle_enum_items_cache

        from .core import fxp as _fxp
        fxf = _fxp.load_cached(path)
        items = [(s.name, s.name, "") for s in fxf.systems]
        if not items:
            items = [('', T('<нет эффектов>'), '')]
        _particle_enum_items_cache = items
        _particle_enum_cache_key = key
        return _particle_enum_items_cache
    except Exception as ex:
        _particle_enum_items_cache = [('', f'<ошибка: {ex}>', '')]
        _particle_enum_cache_key = None
        return _particle_enum_items_cache


def _particle_effect_get(self):
    obj = self.id_data
    name = obj.get('2dfx_effect_name', '') or ''
    for i, item in enumerate(_particle_enum_items_cache):
        if item[0] == name:
            return i
    return 0


def _particle_effect_set(self, value):
    obj = self.id_data
    items = _particle_enum_items_cache
    if 0 <= value < len(items):
        name = items[value][0]
        if name:
            obj['2dfx_effect_name'] = name
            # Reset to the first emitter whenever the effect changes
            obj.inu.particle_emitter_index = 0
            try:
                _populate_particle_props_from_fxp(obj, name, 0)
            except Exception as e:
                print(f"[2DFX Particle] populate failed: {e}")
            try:
                from .ops.fx_preview import update_particle_preview
                update_particle_preview(obj)
            except Exception as e:
                print(f"[2DFX Particle] preview update failed: {e}")


def _sample_particle_from_emitter(em) -> dict:
    """Sample the editable particle parameters from a FXEmitter.

    Returns a dict with exactly the fields that our editor exposes, in the
    same shape/units as obj.inu.particle_*. Used both to populate from FXP
    and to detect user edits on save (so we only write changed fields).
    """
    tex_raw = (em.base_get('TEXTURE') or '').strip()
    tex = "" if tex_raw == 'NULL' else tex_raw
    try:
        src_blend = int(em.base_get('SRCBLENDID') or 4)
    except (TypeError, ValueError):
        src_blend = 4
    try:
        dst_blend = int(em.base_get('DSTBLENDID') or 5)
    except (TypeError, ValueError):
        dst_blend = 5

    def _curve(info_type, field, default=0.0, t=0.0):
        info = em.info(info_type)
        if not info:
            return default
        c = info.curves.get(field)
        if not c:
            return default
        return c.sample(t)

    def _rgba(t):
        return (
            max(min(_curve('COLOUR', 'RED', 255.0, t) / 255.0, 1.0), 0.0),
            max(min(_curve('COLOUR', 'GREEN', 255.0, t) / 255.0, 1.0), 0.0),
            max(min(_curve('COLOUR', 'BLUE', 255.0, t) / 255.0, 1.0), 0.0),
            max(min(_curve('COLOUR', 'ALPHA', 255.0, t) / 255.0, 1.0), 0.0),
        )

    # Detect a middle COLOUR keyframe: any COLOUR curve with > 2 keys.
    # Use the ALPHA curve's middle keyframe time as the canonical mid_time
    # (alpha is usually where fade-in/fade-out lives).
    colour = em.info('COLOUR')
    mid_enabled = False
    mid_time = 0.5
    if colour is not None:
        for name in ('ALPHA', 'RED', 'GREEN', 'BLUE'):
            c = colour.curves.get(name)
            if c is not None and len(c.keys) >= 3:
                mid_enabled = True
                if name == 'ALPHA':
                    mid_idx = len(c.keys) // 2
                    mid_time = max(0.01, min(c.keys[mid_idx].time, 0.99))
                    break

    return {
        'texture': tex,
        'src_blend': src_blend,
        'dst_blend': dst_blend,
        'color_start': _rgba(0.0),
        'color_end': _rgba(1.0),
        'color_mid_enabled': mid_enabled,
        'color_mid': _rgba(mid_time),
        'color_mid_time': mid_time,
        'size_start': max(_curve('SIZE', 'SIZEX', 0.3, 0.0), 0.0),
        'size_end': max(_curve('SIZE', 'SIZEX', 0.5, 1.0), 0.0),
        'life': max(_curve('EMLIFE', 'LIFE', 1.0, 0.0), 0.0),
        'life_bias': max(_curve('EMLIFE', 'BIAS', 0.0, 0.0), 0.0),
        'rate': max(_curve('EMRATE', 'RATE', 10.0, 0.0), 0.0),
        'speed': max(_curve('EMSPEED', 'SPEED', 1.0, 0.0), 0.0),
        'speed_bias': max(_curve('EMSPEED', 'BIAS', 0.0, 0.0), 0.0),
        'direction': (
            _curve('EMDIR', 'DIRX', 0.0, 0.0),
            _curve('EMDIR', 'DIRY', 0.0, 0.0),
            _curve('EMDIR', 'DIRZ', 1.0, 0.0),
        ),
        # Extended emission
        'angle_min': _curve('EMANGLE', 'MIN', 0.0, 0.0),
        'angle_max': _curve('EMANGLE', 'MAX', 0.0, 0.0),
        # EMSIZE as half-extent: half the min→max range per axis.
        # This loses any offset from origin but keeps the box size,
        # which is all that Box UI needs. Save always writes symmetric.
        'volume': (
            max(
                abs(_curve('EMSIZE', 'SIZEMAXX', 0.0, 0.0)),
                abs(_curve('EMSIZE', 'SIZEMINX', 0.0, 0.0)),
            ),
            max(
                abs(_curve('EMSIZE', 'SIZEMAXY', 0.0, 0.0)),
                abs(_curve('EMSIZE', 'SIZEMINY', 0.0, 0.0)),
            ),
            max(
                abs(_curve('EMSIZE', 'SIZEMAXZ', 0.0, 0.0)),
                abs(_curve('EMSIZE', 'SIZEMINZ', 0.0, 0.0)),
            ),
        ),
        'offset': (
            _curve('EMPOS', 'X', 0.0, 0.0),
            _curve('EMPOS', 'Y', 0.0, 0.0),
            _curve('EMPOS', 'Z', 0.0, 0.0),
        ),
        'rotation_min': _curve('EMROTATION', 'ANGLEMIN', 0.0, 0.0),
        'rotation_max': _curve('EMROTATION', 'ANGLEMAX', 0.0, 0.0),
        # Physics
        'force': (
            _curve('FORCE', 'FORCEX', 0.0, 0.0),
            _curve('FORCE', 'FORCEY', 0.0, 0.0),
            _curve('FORCE', 'FORCEZ', 0.0, 0.0),
        ),
        'friction': _curve('FRICTION', 'FRICTION', 0.0, 0.0),
        'wind': _curve('WIND', 'WINDFACTOR', 0.0, 0.0),
        'noise': _curve('NOISE', 'NOISE', 0.0, 0.0),
        'jitter': _curve('JITTER', 'JITTERFACTOR', 0.0, 0.0),
        'rotspeed_min': _curve('ROTSPEED', 'MINCW', 0.0, 0.0),
        'rotspeed_max': _curve('ROTSPEED', 'MAXCW', 0.0, 0.0),
        'ground_bounce': _curve('GROUNDCOLLIDE', 'BOUNCE', 0.0, 0.0),
        'ground_speedmult': _curve('GROUNDCOLLIDE', 'SPEEDMULT', 1.0, 0.0),
    }


def _get_effect_emitter_count(effect_name: str) -> int:
    """Return number of emitters in a named system, or 0 on any failure."""
    try:
        game_root = bpy.path.abspath(
            getattr(bpy.context.scene, 'gtatools_game_root', '') or ''
        )
        if not game_root:
            return 0
        fxp_path = os.path.join(game_root, 'models', 'effects.fxp')
        if not os.path.isfile(fxp_path):
            return 0
        from .core import fxp as _fxp
        fxf = _fxp.load_cached(fxp_path)
        system = fxf.find(effect_name)
        return len(system.emitters) if system else 0
    except Exception:
        return 0


def _populate_particle_props_from_fxp(obj, effect_name: str, emitter_index: int = 0) -> bool:
    """Copy the Nth emitter's parameters from effects.fxp onto obj.inu."""
    game_root = bpy.path.abspath(
        getattr(bpy.context.scene, 'gtatools_game_root', '') or ''
    )
    if not game_root:
        return False
    fxp_path = os.path.join(game_root, 'models', 'effects.fxp')
    if not os.path.isfile(fxp_path):
        return False

    from .core import fxp as _fxp
    fxf = _fxp.load_cached(fxp_path)
    system = fxf.find(effect_name)
    if system is None or not system.emitters:
        return False

    idx = max(0, min(emitter_index, len(system.emitters) - 1))
    vals = _sample_particle_from_emitter(system.emitters[idx])
    inu = obj.inu
    inu.particle_texture = vals['texture']
    inu.particle_src_blend = vals['src_blend']
    inu.particle_dst_blend = vals['dst_blend']
    inu.particle_color_start = vals['color_start']
    inu.particle_color_end = vals['color_end']
    inu.particle_color_mid_enabled = vals['color_mid_enabled']
    inu.particle_color_mid = vals['color_mid']
    inu.particle_color_mid_time = vals['color_mid_time']
    inu.particle_size_start = vals['size_start']
    inu.particle_size_end = vals['size_end']
    inu.particle_life = vals['life']
    inu.particle_life_bias = vals['life_bias']
    inu.particle_rate = vals['rate']
    inu.particle_speed = vals['speed']
    inu.particle_speed_bias = vals['speed_bias']
    inu.particle_direction = vals['direction']

    # Extended emission
    inu.particle_angle_min = vals['angle_min']
    inu.particle_angle_max = vals['angle_max']
    inu.particle_volume = vals['volume']
    inu.particle_offset = vals['offset']
    inu.particle_rotation_min = vals['rotation_min']
    inu.particle_rotation_max = vals['rotation_max']

    # Physics
    inu.particle_force = vals['force']
    inu.particle_friction = vals['friction']
    inu.particle_wind = vals['wind']
    inu.particle_noise = vals['noise']
    inu.particle_jitter = vals['jitter']
    inu.particle_rotspeed_min = vals['rotspeed_min']
    inu.particle_rotspeed_max = vals['rotspeed_max']
    inu.particle_ground_bounce = vals['ground_bounce']
    inu.particle_ground_speedmult = vals['ground_speedmult']

    # System-level settings from FX_SYSTEM_DATA header
    try:
        inu.particle_sys_length = float(system.header_get('LENGTH') or 1.0)
    except ValueError:
        pass
    try:
        inu.particle_sys_playmode = int(system.header_get('PLAYMODE') or 2)
    except ValueError:
        pass
    try:
        inu.particle_sys_culldist = float(system.header_get('CULLDIST') or 50.0)
    except ValueError:
        pass

    return True


_inu_flag_propagating = False


def _make_inu_flag_update(attr_name):
    """Propagate a DFF flag toggle from the active object to all other selected mesh objects.

    Only fires when the user edits the flag on the active object's panel — guards against
    recursion and against runs from import/export where properties are set programmatically
    on non-active objects.
    """
    def _update(self, context):
        global _inu_flag_propagating
        if _inu_flag_propagating:
            return
        active = context.active_object
        if not active or self.id_data != active:
            return
        selected = [o for o in context.selected_objects
                    if o.type == 'MESH' and o != active and hasattr(o, 'inu')]
        if not selected:
            return
        value = getattr(self, attr_name)
        _inu_flag_propagating = True
        try:
            for obj in selected:
                if getattr(obj.inu, attr_name) != value:
                    setattr(obj.inu, attr_name, value)
        finally:
            _inu_flag_propagating = False
    return _update


class INUObjectProps(bpy.types.PropertyGroup):
    """INU_tools object export properties (replaces DragonFF obj.dff)."""

    type : EnumProperty(
        items=[
            ('OBJ', 'Object', 'Object will be exported as a mesh or a dummy'),
            ('COL', 'Collision Object', 'Object is a collision object'),
            ('SHA', 'Shadow Object', 'Object is a shadow object'),
            ('2DFX', '2DFX Effect', 'Object is a 2DFX effect (light, particle, etc.)'),
            ('NON', "Don't export", 'Object will NOT be exported'),
        ],
        name="Type",
        default='OBJ',
    )

    effect_2dfx : EnumProperty(
        items=[
            ('LIGHT', 'Свет', 'Street light / neon / corona effect'),
            ('PARTICLE', 'Частица', 'Particle effect (smoke, fire, etc.)'),
            ('PED_ATTRACTOR', 'Ped Attractor', 'Ped attractor point (ATM, bench, etc.)'),
            ('SUN_GLARE', 'Sun Glare', 'Sun glare reflection on surface'),
        ],
        name="2DFX Effect Type",
        default='LIGHT',
    )

    particle_effect_2dfx : EnumProperty(
        name="Particle Effect",
        description=T("Имя эффекта из effects.fxp"),
        items=_particle_effect_enum_items,
        get=_particle_effect_get,
        set=_particle_effect_set,
    )

    particle_emitter_index : IntProperty(
        name="Emitter Index",
        description=T("Индекс редактируемого эмиттера (для систем с несколькими)"),
        default=0, min=0,
    )

    # ── Curve editor buffer (B1) ── #
    particle_curve_name : StringProperty(
        name="Curve",
        description=T("Редактируемая кривая в формате INFO.FIELD (например SIZE.SIZEX)"),
        default="",
    )
    particle_curve_keys : CollectionProperty(type=INUParticleKeyframe)
    particle_curve_key_index : IntProperty(default=0)

    # ── Particle editable per-instance properties ── #
    # These get populated from effects.fxp when the user picks an effect
    # from the dropdown. All reads for the billboard preview come from
    # these fields (not directly from the FXP file), so edits here are
    # instantly reflected and stored per-object.
    def _update_particle(self, context):
        obj = self.id_data
        if obj and obj.type == 'EMPTY' and self.type == '2DFX' and self.effect_2dfx == 'PARTICLE':
            try:
                from .ops.fx_preview import update_particle_preview
                update_particle_preview(obj)
            except Exception as e:
                print(f"[2DFX Particle] update error: {e}")

    particle_texture : StringProperty(
        name="Texture",
        description=T("Имя спрайта из particle.txd"),
        default="",
        update=_update_particle,
    )
    particle_src_blend : IntProperty(
        name="SRC Blend",
        description="D3D9 source blend factor (4=SRCALPHA, 2=ONE, ...)",
        default=4, min=0, max=17,
        update=_update_particle,
    )
    particle_dst_blend : IntProperty(
        name="DST Blend",
        description="D3D9 dest blend factor (5=INVSRCALPHA, 2=ONE for additive)",
        default=5, min=0, max=17,
        update=_update_particle,
    )
    particle_color_start : FloatVectorProperty(
        name="Color (start)",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
        update=_update_particle,
    )
    particle_color_end : FloatVectorProperty(
        name="Color (end)",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 0.0),
        update=_update_particle,
    )
    particle_color_mid_enabled : BoolProperty(
        name="Use middle colour",
        description=T("Добавить промежуточный ключ для плавного fade-in/fade-out"),
        default=False,
        update=_update_particle,
    )
    particle_color_mid : FloatVectorProperty(
        name="Color (mid)",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
        update=_update_particle,
    )
    particle_color_mid_time : FloatProperty(
        name="Mid time",
        description=T("Позиция промежуточного ключа по времени жизни (0..1)"),
        default=0.5, min=0.01, max=0.99, precision=3,
        update=_update_particle,
    )
    particle_size_start : FloatProperty(
        name="Size (start)",
        description=T("Размер частицы в начале жизни"),
        default=0.3, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_size_end : FloatProperty(
        name="Size (end)",
        description=T("Размер частицы в конце жизни"),
        default=0.5, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_life : FloatProperty(
        name="Life",
        description=T("Длительность жизни частицы в секундах"),
        default=1.0, min=0.0, soft_max=30.0, precision=3,
        update=_update_particle,
    )
    particle_rate : FloatProperty(
        name="Rate",
        description=T("Количество частиц в секунду"),
        default=10.0, min=0.0, soft_max=1000.0,
        update=_update_particle,
    )
    particle_speed : FloatProperty(
        name="Speed",
        description=T("Начальная скорость частицы"),
        default=1.0, min=0.0, soft_max=100.0, precision=3,
        update=_update_particle,
    )
    particle_direction : FloatVectorProperty(
        name="Direction",
        description=T("Направление эмиссии"),
        size=3,
        default=(0.0, 0.0, 1.0),
        update=_update_particle,
    )

    # ── System-level settings (FX_SYSTEM_DATA header) ── #
    particle_sys_length : FloatProperty(
        name="System Length",
        description=T("LENGTH — длительность цикла системы в секундах"),
        default=1.0, min=0.0, soft_max=100.0, precision=3,
        update=_update_particle,
    )
    particle_sys_playmode : IntProperty(
        name="Play Mode",
        description=T("PLAYMODE — режим проигрывания (0-3)"),
        default=2, min=0, max=3,
        update=_update_particle,
    )
    particle_sys_culldist : FloatProperty(
        name="Cull Distance",
        description=T("CULLDIST — расстояние отсечения эффекта в игре"),
        default=50.0, min=0.0, soft_max=500.0, precision=1,
        update=_update_particle,
    )

    # ── Extended emission (EMANGLE / EMSIZE / EMPOS / EMROTATION / biases) ── #
    particle_angle_min : FloatProperty(
        name="Angle Min",
        description=T("EMANGLE MIN — минимальный угол конуса эмиссии"),
        default=0.0, min=0.0, soft_max=180.0, precision=2,
        update=_update_particle,
    )
    particle_angle_max : FloatProperty(
        name="Angle Max",
        description=T("EMANGLE MAX — максимальный угол конуса эмиссии"),
        default=0.0, min=0.0, soft_max=180.0, precision=2,
        update=_update_particle,
    )
    # Box as half-extents — symmetric around the emitter. On save this
    # becomes SIZEMIN=-box, SIZEMAX=+box per axis in the FXP EMSIZE block.
    particle_volume : FloatVectorProperty(
        name="Box",
        description=T("EMSIZE половина размера бокса эмиссии (centered)"),
        size=3,
        default=(0.0, 0.0, 0.0),
        min=0.0, precision=3,
        update=_update_particle,
    )
    # Legacy storage — kept for back-compat with older blend files, not in UI
    particle_volume_radius : FloatProperty(
        name="Volume Radius (legacy)",
        default=0.0, min=0.0, precision=3,
    )
    particle_volume_min : FloatVectorProperty(
        name="Volume Min (legacy)",
        size=3, default=(0.0, 0.0, 0.0), precision=3,
    )
    particle_offset : FloatVectorProperty(
        name="Offset",
        description=T("EMPOS X/Y/Z — смещение точки спавна"),
        size=3,
        default=(0.0, 0.0, 0.0),
        precision=3,
        update=_update_particle,
    )
    particle_rotation_min : FloatProperty(
        name="Rotation Min",
        description=T("EMROTATION ANGLEMIN — мин начальный поворот спрайта"),
        default=0.0, soft_min=-360.0, soft_max=360.0,
        update=_update_particle,
    )
    particle_rotation_max : FloatProperty(
        name="Rotation Max",
        description=T("EMROTATION ANGLEMAX — макс начальный поворот спрайта"),
        default=0.0, soft_min=-360.0, soft_max=360.0,
        update=_update_particle,
    )
    particle_life_bias : FloatProperty(
        name="Life Bias",
        description=T("EMLIFE BIAS — случайный разброс длительности жизни"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_speed_bias : FloatProperty(
        name="Speed Bias",
        description=T("EMSPEED BIAS — случайный разброс начальной скорости"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )

    # ── Physics (FORCE / FRICTION / WIND / NOISE / JITTER / ROTSPEED / GROUNDCOLLIDE) ── #
    particle_force : FloatVectorProperty(
        name="Force",
        description=T("FORCE X/Y/Z — постоянное ускорение (например -9.8 по Z = гравитация)"),
        size=3,
        default=(0.0, 0.0, 0.0),
        precision=3,
        update=_update_particle,
    )
    particle_friction : FloatProperty(
        name="Friction",
        description=T("FRICTION — сопротивление воздуха"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_wind : FloatProperty(
        name="Wind",
        description=T("WIND WINDFACTOR — восприимчивость к ветру игры"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_noise : FloatProperty(
        name="Noise",
        description=T("NOISE — сглаженное случайное движение"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_jitter : FloatProperty(
        name="Jitter",
        description=T("JITTER JITTERFACTOR — резкий случайный дёрг"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_rotspeed_min : FloatProperty(
        name="RotSpeed Min",
        description=T("ROTSPEED MINCW — мин скорость вращения спрайта"),
        default=0.0, soft_min=-360.0, soft_max=360.0,
        update=_update_particle,
    )
    particle_rotspeed_max : FloatProperty(
        name="RotSpeed Max",
        description=T("ROTSPEED MAXCW — макс скорость вращения спрайта"),
        default=0.0, soft_min=-360.0, soft_max=360.0,
        update=_update_particle,
    )
    particle_ground_bounce : FloatProperty(
        name="Ground Bounce",
        description=T("GROUNDCOLLIDE BOUNCE — сила отскока при ударе о землю"),
        default=0.0, min=0.0, soft_max=2.0, precision=3,
        update=_update_particle,
    )
    particle_ground_speedmult : FloatProperty(
        name="Ground SpeedMult",
        description=T("GROUNDCOLLIDE SPEEDMULT — потеря скорости при ударе"),
        default=1.0, min=0.0, soft_max=2.0, precision=3,
        update=_update_particle,
    )

    def _update_2dfx_preview(self, context):
        obj = self.id_data  # owner Object
        if obj and obj.type == 'EMPTY' and self.type == '2DFX' and self.effect_2dfx == 'LIGHT':
            try:
                from .ops.fx_preview import sync_preview_from_props
                sync_preview_from_props(obj)
            except Exception as e:
                print(f"[2DFX] Preview update error: {e}")

    color_2dfx : FloatVectorProperty(
        name="2DFX Color",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 0.784, 1.0),
        description=T("Цвет короны и света"),
        update=_update_2dfx_preview,
    )

    preset_2dfx : EnumProperty(
        items=[
            ('DEFAULT', 'Default', 'Default light settings'),
            ('ONALLDAY', 'OnAllDay', 'Always visible light'),
            ('LAMP_POST', 'Lamp Post', 'Standard lamp post'),
            ('LAMP_POST_COAST', 'Lamp Post Coast', 'Coastal lamp post (warm)'),
            ('BB_PICKUP', 'BB Pickup', 'Red pickup marker'),
            ('FLASHING_MAV1', 'Flashing (Maverick1)', 'Red blinking helicopter light'),
            ('FLASHING_MAV2', 'Flashing (Maverick2)', 'Green blinking helicopter light'),
            ('FLASHING_TUG', 'Flashing (Tug)', 'Orange blinking tug light'),
            ('TRAIN_CROSSING', 'Train Crossing', 'Red blinking train crossing'),
            ('TRAFFIC', 'Traffic', 'Traffic light'),
        ],
        name="2DFX Preset",
        default='DEFAULT',
    )

    def _update_2dfx_texture(self, context):
        """Recreate preview when texture changes."""
        obj = self.id_data
        if obj and obj.type == 'EMPTY' and self.type == '2DFX' and self.effect_2dfx == 'LIGHT':
            try:
                from .ops.fx_preview import remove_preview_children, create_light_preview
                remove_preview_children(obj)
                create_light_preview(obj)
            except Exception as e:
                print(f"[2DFX] Texture update error: {e}")

    corona_tex_2dfx : EnumProperty(
        items=[
            ('coronastar', 'coronastar', ''),
            ('coronamoon', 'coronamoon', ''),
            ('coronaringb', 'coronaringb', ''),
            ('coronareflect', 'coronareflect', ''),
            ('coronaheadlightline', 'coronaheadlightline', ''),
            ('headlight', 'headlight', ''),
            ('headlight1', 'headlight1', ''),
            ('lockon', 'lockon', ''),
            ('lockonFire', 'lockonFire', ''),
            ('lunar', 'lunar', ''),
            ('roadsignfont', 'roadsignfont', ''),
            ('particleskid', 'particleskid', ''),
            ('finishFlag', 'finishFlag', ''),
            ('handman', 'handman', ''),
            ('seabd32', 'seabd32', ''),
            ('shad_exp', 'shad_exp', ''),
            ('shad_car', 'shad_car', ''),
            ('shad_bike', 'shad_bike', ''),
            ('shad_heli', 'shad_heli', ''),
            ('shad_ped', 'shad_ped', ''),
            ('shad_rcbaron', 'shad_rcbaron', ''),
            ('lamp_shad_64', 'lamp_shad_64', ''),
            ('bloodpool_64', 'bloodpool_64', ''),
            ('target256', 'target256', ''),
            ('white', 'white', ''),
            ('cloud1', 'cloud1', ''),
            ('cloudhigh', 'cloudhigh', ''),
            ('cloudmasked', 'cloudmasked', ''),
            ('carfx1', 'carfx1', ''),
            ('wincrack_32', 'wincrack_32', ''),
            ('waterclear256', 'waterclear256', ''),
            ('waterwake', 'waterwake', ''),
            ('txgrassbig0', 'txgrassbig0', ''),
            ('txgrassbig1', 'txgrassbig1', ''),
        ],
        name="Corona Texture",
        default='coronastar',
        update=_update_2dfx_texture,
    )

    shadow_tex_2dfx : EnumProperty(
        items=[
            ('shad_exp', 'shad_exp', ''),
            ('shad_car', 'shad_car', ''),
            ('shad_bike', 'shad_bike', ''),
            ('shad_heli', 'shad_heli', ''),
            ('shad_ped', 'shad_ped', ''),
            ('shad_rcbaron', 'shad_rcbaron', ''),
            ('lamp_shad_64', 'lamp_shad_64', ''),
            ('bloodpool_64', 'bloodpool_64', ''),
            ('coronastar', 'coronastar', ''),
            ('coronamoon', 'coronamoon', ''),
            ('coronaringb', 'coronaringb', ''),
            ('coronareflect', 'coronareflect', ''),
            ('white', 'white', ''),
        ],
        name="Shadow Texture",
        default='shad_exp',
    )

    show_mode_2dfx : EnumProperty(
        items=[
            ('0', '0 DEFAULT', 'Default behavior'),
            ('1', '1 RANDOM_FLASHING', 'Random flashing'),
            ('2', '2 FLASH_RAIN', 'Flashing when raining'),
            ('3', '3 ONLY_RAIN', 'Only visible in rain'),
            ('4', '4 NO_RAIN', 'Not visible in rain'),
            ('5', '5 FLASH_5', 'Flashing variant 2'),
        ],
        name="Show Mode",
        default='0',
    )

    flare_type_2dfx : EnumProperty(
        items=[
            ('0', '0 None', 'No lens flare'),
            ('1', '1 Type 1', 'Lens flare style 1'),
            ('2', '2 Type 2', 'Lens flare style 2'),
            ('3', '3 Type 3', 'Lens flare style 3'),
        ],
        name="Flare Type",
        default='0',
    )

    pipeline : EnumProperty(
        items=[
            ('NONE', 'None',
             T("Без указания pipeline — использовать стандартный рендер RenderWare. Подходит для простых объектов, которым не нужны специальные эффекты движка")),
            ('0x53F2009A', 'Vehicle',
             T("Pipeline кузова машины (RSPIPE_PC_CustomCarEnvMap). Добавляет env-map отражения неба/облаков/улицы. Используется совместно с текстурами vehicleenv128 + vehiclespecdot64 на материале")),
            ('0x53F20098', 'Day/Night',
             T("Pipeline здания с day/night vertex colors (RSPIPE_PC_CustomBuildingDN). Движок плавно смешивает дневной и ночной слои vertex colors по игровому времени. Требует ДВА Color Attribute слоя (Day + Night) на меше")),
            ('0x53F2009C', 'Building',
             T("Простой pipeline здания (RSPIPE_PC_CustomBuilding). Статическое освещение через один слой vertex colors. Работает быстрее чем Day/Night, но нет смены по времени суток")),
            ('CUSTOM', 'Custom Pipeline',
             T("Указать произвольное значение pipeline ID через поле Custom Pipeline")),
        ],
        name="Pipeline",
        description=T("Рендер-пайплайн движка"),
    )
    custom_pipeline : StringProperty(name="Custom Pipeline")

    export_normals : BoolProperty(
        default=True,
        description=T("Экспорт нормалей вершин (отключить для map объектов)"),
        update=_make_inu_flag_update("export_normals"),
    )
    export_binsplit : BoolProperty(
        default=True,
        description=T("Экспорт Bin Mesh PLG (совместимость с просмотрщиками DFF)"),
        update=_make_inu_flag_update("export_binsplit"),
    )

    uv_map1 : BoolProperty(default=True, description=T("Экспорт первой UV карты"), update=_make_inu_flag_update("uv_map1"))
    uv_map2 : BoolProperty(default=True, description=T("Экспорт второй UV карты"), update=_make_inu_flag_update("uv_map2"))
    day_cols : BoolProperty(default=True, description=T("Экспорт дневных vertex colors"), update=_make_inu_flag_update("day_cols"))
    night_cols : BoolProperty(default=True, description=T("Экспорт ночных vertex colors"), update=_make_inu_flag_update("night_cols"))

    light : BoolProperty(default=True, description=T("Флаг rpGEOMETRYLIGHT — динамическое освещение"), update=_make_inu_flag_update("light"))
    modulate_color : BoolProperty(default=True, description=T("Флаг rpGEOMETRYMODULATEMATERIALCOLOR — цвет материала влияет на модель"), update=_make_inu_flag_update("modulate_color"))
    set_material_alpha : BoolProperty(default=True, description=T("Автоматически ставить material alpha = 254 при наличии vertex alpha < 255.\nНужно для стандартных прозрачных мешей (стёкла, дым). Выключи если материал должен остаться opaque"), update=_make_inu_flag_update("set_material_alpha"))
    light_beam_asi : BoolProperty(default=False, description=T("Помечает меш как объёмный луч света для плагина SA_Light.asi.\nУстанавливает material color = (254,254,254,254) — этот маркер плагин ищет во время рендера.\n\nТРЕБУЕТ SA_Light.asi в корне GTA SA. Без плагина меш будет рендериться как обычный полупрозрачный объект с жёстким срезом alpha.\n\nДля использования:\n1. Собери меш-конус/куб формой луча\n2. Покрась vertex colors как хочешь (любые значения alpha)\n3. Включи этот флаг + Set Material Alpha выключи\n4. Экспорт → плагин автоматически включит плавный alpha blend на этом меше"), update=_make_inu_flag_update("light_beam_asi"))

    # ── IDE / IPL properties ──
    model_id : IntProperty(
        name="Model ID",
        default=0,
        min=0,
        description=T("ID модели в GTA SA (IDE/IPL)"),
    )
    txd_name : StringProperty(
        name="TXD Name",
        default="",
        description=T("Имя словаря текстур (IDE). По умолчанию = имя модели"),
    )
    draw_distance : FloatProperty(
        name="Draw Distance",
        default=299.0,
        min=0.0,
        description=T("Дальность прорисовки объекта (IDE)"),
    )
    lod_draw_distance : FloatProperty(
        name="LOD Distance",
        default=999.0,
        min=0.0,
        description=T("Дальность прорисовки LOD модели (IDE)"),
    )
    ide_flags : IntProperty(
        name="IDE Flags",
        default=0,
        min=0,
        description=T("Флаги объекта в IDE"),
    )

    # Breakable object extension (chunk 0x253F2FD)
    breakable : BoolProperty(
        name="Breakable Object",
        description=T("Пометить геометрию как разрушаемую (пишет чанк 0x253F2FD в DFF)"),
        default=False,
    )
    breakable_force : FloatProperty(
        name="Break Force",
        description=T("Сила, нужная чтобы сломать объект (умолчание 1.0)"),
        default=1.0, min=0.0,
    )

    # IDE flag checkboxes with auto-sync to ide_flags
    def _update_ide_flag(self, context):
        _FLAG_BITS = [
            ('flag_is_road', 1), ('flag_draw_last', 4), ('flag_additive', 8),
            ('flag_no_zbuffer', 64), ('flag_no_shadows', 128),
            ('flag_glass_1', 512), ('flag_glass_2', 1024),
            ('flag_garage_door', 2048), ('flag_damagable', 4096),
            ('flag_is_tree', 8192), ('flag_is_palm', 16384),
            ('flag_no_flyer_col', 32768), ('flag_is_tag', 1048576),
            ('flag_no_backface', 2097152), ('flag_breakable', 4194304),
        ]
        val = 0
        for prop, bit in _FLAG_BITS:
            if getattr(self, prop, False):
                val |= bit
        self['ide_flags'] = val

    flag_is_road : BoolProperty(name="IS_ROAD", description=T("Дорога (1)"), default=False, update=_update_ide_flag)
    flag_draw_last : BoolProperty(name="DRAW_LAST", description=T("Прозрачный, рисовать последним (4)"), default=False, update=_update_ide_flag)
    flag_additive : BoolProperty(name="ADDITIVE", description=T("Аддитивный блендинг (8)"), default=False, update=_update_ide_flag)
    flag_no_zbuffer : BoolProperty(name="NO_ZBUFFER_WRITE", description=T("Не писать в Z-буфер (64)"), default=False, update=_update_ide_flag)
    flag_no_shadows : BoolProperty(name="NO_SHADOWS", description=T("Не получать тени (128)"), default=False, update=_update_ide_flag)
    flag_glass_1 : BoolProperty(name="GLASS_TYPE_1", description=T("Стекло разбиваемое (512)"), default=False, update=_update_ide_flag)
    flag_glass_2 : BoolProperty(name="GLASS_TYPE_2", description=T("Стекло с трещинами (1024)"), default=False, update=_update_ide_flag)
    flag_garage_door : BoolProperty(name="GARAGE_DOOR", description=T("Дверь гаража (2048)"), default=False, update=_update_ide_flag)
    flag_damagable : BoolProperty(name="DAMAGABLE", description=T("Разрушаемый (4096)"), default=False, update=_update_ide_flag)
    flag_is_tree : BoolProperty(name="IS_TREE", description=T("Дерево, качается на ветру (8192)"), default=False, update=_update_ide_flag)
    flag_is_palm : BoolProperty(name="IS_PALM", description=T("Пальма, качается на ветру (16384)"), default=False, update=_update_ide_flag)
    flag_no_flyer_col : BoolProperty(name="NO_FLYER_COL", description=T("Нет коллизии с летающим (32768)"), default=False, update=_update_ide_flag)
    flag_is_tag : BoolProperty(name="IS_TAG", description=T("Граффити тег (1048576)"), default=False, update=_update_ide_flag)
    flag_no_backface : BoolProperty(name="NO_BACKFACE_CULL", description=T("Рисовать обе стороны (2097152)"), default=False, update=_update_ide_flag)
    flag_breakable : BoolProperty(name="BREAKABLE_STATUE", description=T("Разрушаемая статуя (4194304)"), default=False, update=_update_ide_flag)
    interior_id : IntProperty(
        name="Interior ID",
        default=0,
        min=0,
        description=T("ID интерьера для IPL (0 = экстерьер)"),
    )
    lod_index : IntProperty(
        name="LOD Index",
        default=-1,
        description=T("Индекс LOD модели в IPL (-1 = нет LOD)"),
    )

    # Collision sphere/cone properties
    col_material : IntProperty(default=12, description=T("Материал для Sphere/Cone"))
    col_flags : IntProperty(default=0, description=T("Флаги для Sphere/Cone"))
    col_brightness : IntProperty(default=0, description=T("Яркость для Sphere/Cone"))
    col_light : IntProperty(default=0, description=T("Свет для Sphere/Cone"))


# GTA SA vehicle color slot → magic RGB marker value.
# Движок SA сканирует material.color.rgb, и если находит одно из магических значений
# — подставляет цвет из carcols.dat для нужного слота кузова/огня.
# Значения взяты из Kam's GTA_Material.ms (colhprIdx).
_VEHICLE_COLOR_SLOTS = {
    'NONE':    None,
    'PRIMARY':    (60,  255, 0),
    'SECONDARY':  (255, 0,   175),
    'THIRD':      (0,   255, 255),
    'FOURTH':     (255, 0,   255),
    'HL_LEFT':    (255, 175, 0),
    'HL_RIGHT':   (0,   255, 200),
    'TL_LEFT':    (185, 255, 0),
    'TL_RIGHT':   (255, 60,  0),
}

def _on_vehicle_color_slot_update(self, context):
    """При выборе слота красим базовый цвет материала в магическое RGB,
    по которому движок SA найдёт соответствующий carcols-цвет."""
    rgb = _VEHICLE_COLOR_SLOTS.get(self.vehicle_color_slot)
    if rgb is None:
        return
    mat = getattr(self, 'id_data', None)
    if mat is None:
        return
    # Устанавливаем diffuse color в Principled BSDF + material.diffuse_color
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    try:
        mat.diffuse_color = (r, g, b, 1.0)
    except Exception:
        pass
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bc = node.inputs.get('Base Color')
                if bc is not None:
                    bc.default_value = (r, g, b, 1.0)
                break


class INUMaterialProps(bpy.types.PropertyGroup):
    """INU_tools material properties (replaces DragonFF mat.dff)."""

    ambient : FloatProperty(name="Ambient Shading", default=1.0)

    # Vehicle color slot — только для машин (GTA SA)
    vehicle_color_slot : EnumProperty(
        name="Vehicle Color Slot",
        description=T("Слот цвета машины: движок SA подставит цвет из carcols.dat. Меняет базовый RGB материала на магическую метку."),
        items=[
            ('NONE',      "None",           T("Обычный материал, не связан с carcols")),
            ('PRIMARY',   "Primary",        T("Основной цвет (первый в carcols.dat)")),
            ('SECONDARY', "Secondary",      T("Второй цвет")),
            ('THIRD',     "Third color",    T("Третий цвет (некоторые машины)")),
            ('FOURTH',    "Fourth color",   T("Четвёртый цвет")),
            ('HL_LEFT',   "Left Headlight", T("Левая фара")),
            ('HL_RIGHT',  "Right Headlight",T("Правая фара")),
            ('TL_LEFT',   "Left Taillight", T("Левый задний фонарь")),
            ('TL_RIGHT',  "Right Taillight",T("Правый задний фонарь")),
        ],
        default='NONE',
        update=_on_vehicle_color_slot_update,
    )

    # Collision surface
    col_mat_index : IntProperty(name="Surface ID", default=0, description=T("ID типа поверхности COL (0-178)"))
    col_flags : IntProperty(name="Flags", default=0)
    col_brightness : IntProperty(name="Brightness", default=0)
    col_light : IntProperty(name="Light", default=0)
    col_day_light : IntProperty(name="Day Light", default=0, min=0, max=15)
    col_night_light : IntProperty(name="Night Light", default=0, min=0, max=15)

    # Environment Map
    export_env_map : BoolProperty(name="Environment Map")
    env_map_tex : StringProperty()
    env_map_coef : FloatProperty(default=0.5)
    env_map_fb_alpha : BoolProperty()

    # Bump Map
    export_bump_map : BoolProperty(name="Bump Map")
    bump_map_tex : StringProperty()

    # Reflection
    export_reflection : BoolProperty(name="Reflection Material")
    reflection_scale_x : FloatProperty()
    reflection_scale_y : FloatProperty()
    reflection_offset_x : FloatProperty()
    reflection_offset_y : FloatProperty()
    reflection_intensity : FloatProperty()

    # Specular
    export_specular : BoolProperty(name="Specular Material")
    specular_level : FloatProperty()
    specular_texture : StringProperty()

    # Dual Texture / Blend Mode
    export_dual_tex : BoolProperty(name="Dual Texture / Blend Mode")
    dual_tex_src_blend : EnumProperty(
        name="Src Blend",
        items=[
            ('1', "Zero", ""),
            ('2', "One", ""),
            ('3', "Src Color", ""),
            ('4', "Inv Src Color", ""),
            ('5', "Src Alpha", ""),
            ('6', "Inv Src Alpha", ""),
            ('7', "Dest Alpha", ""),
            ('8', "Inv Dest Alpha", ""),
            ('9', "Dest Color", ""),
            ('10', "Inv Dest Color", ""),
            ('11', "Src Alpha Sat", ""),
        ],
        default='5',
    )
    dual_tex_dst_blend : EnumProperty(
        name="Dst Blend",
        items=[
            ('1', "Zero", ""),
            ('2', "One", ""),
            ('3', "Src Color", ""),
            ('4', "Inv Src Color", ""),
            ('5', "Src Alpha", ""),
            ('6', "Inv Src Alpha", ""),
            ('7', "Dest Alpha", ""),
            ('8', "Inv Dest Alpha", ""),
            ('9', "Dest Color", ""),
            ('10', "Inv Dest Color", ""),
            ('11', "Src Alpha Sat", ""),
        ],
        default='6',
    )
    dual_tex_texture : StringProperty(name="Dual Texture")

    # UV Animation
    export_animation : BoolProperty(name="UV Animation")
    animation_name : StringProperty()
    # UV Animation written into DFF binary (chunks 0x2B / 0x135)
    uv_anim_write : BoolProperty(
        name="Write UV Anim to DFF",
        description=T("Вписать простую UV-прокрутку в экспортируемый DFF"),
        default=False,
    )
    uv_anim_speed_u : FloatProperty(
        name="Scroll U",
        description=T("Скорость прокрутки UV по U в секунду"),
        default=0.0, precision=4,
    )
    uv_anim_speed_v : FloatProperty(
        name="Scroll V",
        description=T("Скорость прокрутки UV по V в секунду"),
        default=0.0, precision=4,
    )
    uv_anim_duration : FloatProperty(
        name="Duration (s)",
        description=T("Длительность цикла UV-анимации"),
        default=1.0, min=0.01, soft_max=60.0, precision=3,
    )


class GTATOOLS_ImgFileEntry(bpy.types.PropertyGroup):
    """One file entry in IMG archive list."""
    name: StringProperty()


class GTATOOLS_BinaryIplEntry(bpy.types.PropertyGroup):
    """One binary IPL file found inside an IMG archive — user-selectable
    for inclusion in Build Map / Import Map."""
    name: StringProperty()
    enabled: BoolProperty(
        name="",
        default=True,
        description=T("Включить этот бинарный IPL в сборку карты"),
    )
    img_source: StringProperty()


class GTATOOLS_UL_img_files(bpy.types.UIList):
    """Scrollable list of files in IMG archive."""
    bl_idname = "GTATOOLS_UL_img_files"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        ext = item.name.rsplit('.', 1)[-1].lower() if '.' in item.name else ''
        icons = {'dff': 'MESH_DATA', 'col': 'MESH_CUBE', 'txd': 'TEXTURE', 'ipl': 'EMPTY_AXIS'}
        layout.label(text=item.name, icon=icons.get(ext, 'FILE'))

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt_flags = [self.bitflag_filter_item] * len(items)
        # Keep original order — no sorting
        flt_neworder = []

        if self.filter_name:
            search = self.filter_name.lower()
            for i, item in enumerate(items):
                if search not in item.name.lower():
                    flt_flags[i] = 0

        return flt_flags, flt_neworder



def _refresh_img_entries(scn, img_path):
    """Directly refresh IMG entries list."""
    scn.gtatools_img_entries.clear()
    try:
        from .core.img import read_directory
        entries = read_directory(img_path)
        for entry in entries:
            item = scn.gtatools_img_entries.add()
            item.name = entry.name
        scn.gtatools_img_entries_index = max(0, len(entries) - 1)
    except Exception:
        pass


class GTATOOLS_OT_refresh_img_list(bpy.types.Operator):
    """Обновить список файлов IMG архива"""
    bl_idname = "gtatools.refresh_img_list"
    bl_label = "Refresh IMG List"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .core.img import read_directory
        scn = context.scene
        img_path = bpy.path.abspath(scn.gtatools_img_path)
        if not img_path or not os.path.isfile(img_path):
            self.report({'WARNING'}, T("Укажите путь к IMG"))
            return {'CANCELLED'}

        scn.gtatools_img_entries.clear()
        try:
            entries = read_directory(img_path)
            for entry in entries:
                item = scn.gtatools_img_entries.add()
                item.name = entry.name
            # Set index to end so list shows from bottom
            scn.gtatools_img_entries_index = max(0, len(entries) - 1)
            self.report({'INFO'}, f"{T('Файлов:')} {len(scn.gtatools_img_entries)}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}


class GTATOOLS_FillColorItem(bpy.types.PropertyGroup):
    """Элемент списка цветов заливки"""
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0)
    )


# =============================================================================
# OPERATORS
# =============================================================================

class GTATOOLS_OT_check_geometry(bpy.types.Operator):
    """Проверить геометрию на висящие вершины и рёбра"""
    bl_idname = "gtatools.check_geometry"
    bl_label = "Check Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    select_loose: BoolProperty(
        name="Select Loose",
        description=T("Выделить найденные проблемные элементы"),
        default=True
    )

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        loose_verts, loose_edges, error = check_loose_geometry(obj)

        if error:
            self.report({'ERROR'}, T(error))
            return {'CANCELLED'}

        total_problems = len(loose_verts) + len(loose_edges)

        if total_problems == 0:
            self.report({'INFO'}, f"✓ {obj.name}: {T('Геометрия в порядке!')}")
            return {'FINISHED'}

        # Select problem elements
        if self.select_loose and (loose_verts or loose_edges):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            mesh = obj.data
            for idx in loose_verts:
                mesh.vertices[idx].select = True
            for idx in loose_edges:
                mesh.edges[idx].select = True

            bpy.ops.object.mode_set(mode='EDIT')
            # Switch selection mode to see vertices/edges
            if loose_verts:
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            elif loose_edges:
                bpy.context.tool_settings.mesh_select_mode = (False, True, False)

        message = f"⚠ {obj.name}: "
        if loose_verts:
            message += f"{len(loose_verts)} {T('висящих вершин')} "
        if loose_edges:
            message += f"{len(loose_edges)} {T('висящих рёбер')}"

        self.report({'WARNING'}, message)
        return {'FINISHED'}


class GTATOOLS_OT_check_ngons(bpy.types.Operator):
    """Проверить геометрию на N-gons (полигоны с 5+ вершинами)"""
    bl_idname = "gtatools.check_ngons"
    bl_label = "Check N-gons"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        import bmesh
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        # Find N-gons (polygons with 5+ vertices)
        ngon_indices = [f.index for f in bm.faces if len(f.verts) > 4]

        bm.free()

        if not ngon_indices:
            self.report({'INFO'}, f"✓ {obj.name}: {T('N-gons не найдены!')}")
            return {'FINISHED'}

        # Select N-gons
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        for idx in ngon_indices:
            mesh.polygons[idx].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)

        self.report({'WARNING'}, f"⚠ {obj.name}: {len(ngon_indices)} {T('N-gons (5+ вершин)')}")
        return {'FINISHED'}


class GTATOOLS_OT_clean_geometry(bpy.types.Operator):
    """Удалить висящие вершины и рёбра"""
    bl_idname = "gtatools.clean_geometry"
    bl_label = "Clean Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        loose_verts, loose_edges, error = check_loose_geometry(obj)

        if error:
            self.report({'ERROR'}, T(error))
            return {'CANCELLED'}

        if not loose_verts and not loose_edges:
            self.report({'INFO'}, T("Нечего удалять - геометрия чистая!"))
            return {'FINISHED'}

        # Delete via bmesh
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        # Delete loose vertices
        verts_to_remove = [v for v in bm.verts if not v.link_faces]
        for v in verts_to_remove:
            bm.verts.remove(v)

        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()

        message = f"{T('Удалено:')} {len(loose_verts)} {T('вершин,')}{len(loose_edges)} {T('рёбер')}"
        self.report({'INFO'}, message)
        return {'FINISHED'}


class GTATOOLS_OT_clear_raw_dff(bpy.types.Operator):
    """Очистить сохранённые raw DFF данные для экспорта отредактированной геометрии"""
    bl_idname = "gtatools.clear_raw_dff"
    bl_label = "Clear Raw DFF Data"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'ERROR'}, T("Нет активного объекта!"))
            return {'CANCELLED'}

        # Find armature (from mesh or directly)
        arm_obj = None
        if obj.type == 'MESH':
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE' and mod.object:
                    arm_obj = mod.object
                    break
        elif obj.type == 'ARMATURE':
            arm_obj = obj

        if arm_obj is None:
            self.report({'ERROR'}, T("Не найден Armature!"))
            return {'CANCELLED'}

        cleared = []
        for key in ('dff_raw_geometry_list', 'dff_raw_atomics'):
            if key in arm_obj:
                del arm_obj[key]
                cleared.append(key)

        if cleared:
            self.report({'INFO'}, f"Cleared: {', '.join(cleared)}")
        else:
            self.report({'INFO'}, "No raw DFF data to clear")
        return {'FINISHED'}


class GTATOOLS_OT_sa_vehicle_preset(bpy.types.Operator):
    """Применить стандартные SA-настройки для материала кузова машины:
    env map = xvehicleenv128, specular = vehiclespecdot64, blend = 0.05, + Vehicle pipeline.
    Эквивалент кнопки "SA Vehicle default" из Kam's GTA_Material.ms."""
    bl_idname = "gtatools.sa_vehicle_preset"
    bl_label = "SA Vehicle Preset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.material is not None

    def execute(self, context):
        mat = context.material
        inu = mat.inu

        # Environment map — отражения кузова через xvehicleenv128
        inu.export_env_map = True
        inu.env_map_tex = 'xvehicleenv128'
        inu.env_map_coef = 0.2
        inu.env_map_fb_alpha = False

        # Specular material (RW SpecularMaterial chunk)
        inu.export_specular = True
        inu.specular_level = 1.0
        inu.specular_texture = 'vehiclespecdot64'

        # Reflection material (SA custom specular — отвечает за блеск покраски)
        inu.export_reflection = True
        inu.reflection_scale_x = 1.0
        inu.reflection_scale_y = 1.0
        inu.reflection_offset_x = 0.0
        inu.reflection_offset_y = 0.0
        inu.reflection_intensity = 0.05  # Kam's default blend=0.05

        self.report({'INFO'}, "SA Vehicle defaults applied (env + specular + reflection)")
        return {'FINISHED'}


class GTATOOLS_OT_apply_vehicle_pipeline(bpy.types.Operator):
    """Выставить Vehicle pipeline (0x53F2009A) на выделенных MESH-объектах.
    Нужен чтобы кузов получил env-map отражения в игре."""
    bl_idname = "gtatools.apply_vehicle_pipeline"
    bl_label = "Set Vehicle Pipeline on selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            if hasattr(obj, 'inu'):
                obj.inu.pipeline = '0x53F2009A'
                count += 1
        self.report({'INFO'}, f"Vehicle pipeline set on {count} object(s)")
        return {'FINISHED'}


class GTATOOLS_OT_export_txd(bpy.types.Operator, ExportHelper):
    """Экспортировать текстуры в TXD архив"""
    bl_idname = "gtatools.export_txd"
    bl_label = "Export TXD"
    bl_options = {'PRESET'}
    filename_ext = ".txd"
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    selected_only: BoolProperty(
        name="Selected Only",
        description=T("Экспортировать текстуры только из выделенных объектов"),
        default=False,
    )

    def execute(self, context):
        # Берём настройку GPU из панели
        use_gpu = check_nvtt_available(getattr(context.scene, 'gtatools_nvtt_path', ''))[0]
        result, message, transparent_list = export_txd(self.filepath, context, self.selected_only, use_gpu)
        self.report({'INFO'} if result == {'FINISHED'} else {'ERROR'}, message)
        return result

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "selected_only")


class GTATOOLS_OT_export_shared_txd(bpy.types.Operator, ExportHelper):
    """Экспортировать один общий TXD для нескольких DFF моделей"""
    bl_idname = "gtatools.export_shared_txd"
    bl_label = "Export Shared TXD"
    bl_options = {'PRESET'}
    filename_ext = ".txd"
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    def invoke(self, context, event):
        # Pre-fill filename from scene property
        txd_name = getattr(context.scene, 'gtatools_shared_txd_name', '').strip()
        if txd_name:
            if not txd_name.lower().endswith('.txd'):
                txd_name += '.txd'
            self.filepath = txd_name
        return super().invoke(context, event)

    def execute(self, context):
        # Validate selection
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if not selected_meshes:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        use_gpu = check_nvtt_available(getattr(context.scene, 'gtatools_nvtt_path', ''))[0]
        # Force selected_only=True for shared TXD (collects from all selected DFFs)
        result, message, transparent_list = export_txd(self.filepath, context, True, use_gpu)
        self.report({'INFO'} if result == {'FINISHED'} else {'ERROR'}, message)
        return result


class GTATOOLS_OT_export_dff(bpy.types.Operator, ExportHelper):
    """Экспортировать DFF модель"""
    bl_idname = "gtatools.export_dff"
    bl_label = "Export DFF"
    bl_options = {'PRESET'}
    filename_ext = ".dff"
    filter_glob: StringProperty(default="*.dff", options={'HIDDEN'})

    def execute(self, context):
        try:
            # Запоминаем у каких объектов prelight preview был включён
            prelight_was_on = []
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    # Проверяем наличие Prelight_Mix ноды — признак включённого превью
                    has_prelight = False
                    for mat_slot in obj.material_slots:
                        mat = mat_slot.material
                        if mat and mat.use_nodes and mat.node_tree.nodes.get("Prelight_Mix"):
                            has_prelight = True
                            break
                    if has_prelight:
                        prelight_was_on.append(obj)
                        setup_prelight_preview(obj, enable=False)

            # Собираем меши, 2DFX и dummy-пустышки для экспорта.
            # Auto-include: если выбран меш/пустышка, подтягиваем всех его
            # предков и потомков-пустышек, чтобы иерархия DFF была целой.
            from .ops.dff_export import export_dff as inu_export_dff

            def _inu_type(o):
                return getattr(getattr(o, 'inu', None), 'type', 'OBJ')

            def _is_exportable(o):
                if o.type == 'MESH':
                    return _inu_type(o) != 'NON'
                if o.type == 'EMPTY':
                    return _inu_type(o) in ('OBJ', '2DFX')
                return False

            selected = [o for o in context.selected_objects if _is_exportable(o)]
            dff_objects = list(selected)
            seen = set(dff_objects)

            # Тянем родителей-Empty (dummy-иерархия вверх)
            for o in list(selected):
                p = o.parent
                while p is not None and p not in seen:
                    if p.type == 'EMPTY' and _inu_type(p) == 'OBJ':
                        dff_objects.append(p)
                        seen.add(p)
                    p = p.parent

            # Тянем потомков-Empty + MESH (dummy-иерархия вниз)
            def _walk_children(o):
                for c in o.children:
                    if c in seen or not _is_exportable(c):
                        continue
                    dff_objects.append(c)
                    seen.add(c)
                    _walk_children(c)
            for o in list(selected):
                _walk_children(o)

            print(f"[DFF Export] selector: selected={len(selected)}, total={len(dff_objects)} objects → {self.filepath}")
            for o in dff_objects[:20]:
                print(f"  - {o.name} ({o.type})")
            inu_export_dff(filepath=self.filepath, objects=dff_objects)

            # Восстанавливаем prelight только для тех объектов, где он был
            for obj in prelight_was_on:
                setup_prelight_preview(obj, enable=True)

            self.report({'INFO'}, f"Exported DFF: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            # При ошибке тоже восстанавливаем prelight
            for obj in prelight_was_on:
                try:
                    setup_prelight_preview(obj, enable=True)
                except:
                    pass
            self.report({'ERROR'}, f"DFF export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_col(bpy.types.Operator, ExportHelper):
    """Экспортировать COL модель коллизии"""
    bl_idname = "gtatools.export_col"
    bl_label = "Export COL"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    def execute(self, context):
        from .ops.col_export import export_col as inu_export_col
        prelight_was_on = []
        try:
            # Запоминаем и отключаем prelight только где он был
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    has_prelight = False
                    for mat_slot in obj.material_slots:
                        mat = mat_slot.material
                        if mat and mat.use_nodes and mat.node_tree.nodes.get("Prelight_Mix"):
                            has_prelight = True
                            break
                    if has_prelight:
                        prelight_was_on.append(obj)
                        setup_prelight_preview(obj, enable=False)

            # COL всегда экспортируется в центре (0,0,0)
            original_locations = {}
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    original_locations[obj.name] = obj.location.copy()
                    obj.location = (0, 0, 0)

            # Собираем объекты для экспорта
            col_objects = [o for o in context.selected_objects
                           if o.type in ('MESH', 'EMPTY')]

            # Экспорт через INU_tools COL exporter
            inu_export_col(
                filepath=self.filepath,
                objects=col_objects,
                version=3,
            )

            # Возвращаем оригинальные позиции
            for obj in context.selected_objects:
                if obj.name in original_locations:
                    obj.location = original_locations[obj.name]

            # Восстанавливаем prelight только где он был
            for obj in prelight_was_on:
                setup_prelight_preview(obj, enable=True)

            self.report({'INFO'}, f"Exported COL: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            for obj in prelight_was_on:
                try:
                    setup_prelight_preview(obj, enable=True)
                except:
                    pass
            self.report({'ERROR'}, f"COL export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_dff(bpy.types.Operator):
    """Импорт DFF модели GTA SA"""
    bl_idname = "gtatools.import_dff"
    bl_label = "Import DFF (.dff)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.dff", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.dff_import import import_dff as inu_import_dff
        from .ops.txd_import import import_txd as inu_import_txd
        try:
            inu_import_dff(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"Imported DFF: {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"DFF import error: {str(e)}")
            return {'CANCELLED'}

        # Auto-import TXD (if enabled)
        if not getattr(context.scene, 'gtatools_txd_auto_import', True):
            return {'FINISHED'}
        txd_file = None
        dff_name = os.path.splitext(os.path.basename(self.filepath))[0]
        custom_dir = getattr(context.scene, 'gtatools_txd_import_path', '')
        if custom_dir:
            custom_dir = bpy.path.abspath(custom_dir)

        search_dirs = []
        if custom_dir and os.path.isdir(custom_dir):
            search_dirs.append(custom_dir)
        search_dirs.append(os.path.dirname(self.filepath))

        for search_dir in search_dirs:
            if txd_file:
                break
            same_name = os.path.join(search_dir, dff_name + ".txd")
            if os.path.isfile(same_name):
                txd_file = same_name
                break
            for f in os.listdir(search_dir):
                if f.lower().endswith('.txd'):
                    txd_file = os.path.join(search_dir, f)
                    break

        if txd_file:
            try:
                images = inu_import_txd(filepath=txd_file)
                self.report({'INFO'}, f"TXD: {len(images)} textures ({os.path.basename(txd_file)})")
            except Exception as e:
                self.report({'WARNING'}, f"TXD import error: {str(e)}")

        return {'FINISHED'}


class GTATOOLS_OT_import_col(bpy.types.Operator):
    """Импорт COL коллизии GTA SA"""
    bl_idname = "gtatools.import_col"
    bl_label = "Import COL (.col)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.col_import import import_col as inu_import_col
        try:
            inu_import_col(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"Imported COL: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"COL import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_txd(bpy.types.Operator):
    """Импорт TXD текстур GTA SA"""
    bl_idname = "gtatools.import_txd"
    bl_label = "Import TXD (.txd)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.txd_import import import_txd as inu_import_txd
        try:
            images = inu_import_txd(filepath=self.filepath)
            self.report({'INFO'}, f"Imported TXD: {len(images)} textures")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"TXD import error: {str(e)}")
            return {'CANCELLED'}


def menu_func_export(self, context):
    self.layout.operator(GTATOOLS_OT_inu_export.bl_idname,
                         text="INU Export (.dff/.col/.txd/.ide/.ipl)")


# ── IDE / IPL panel operators ──

def _ide_entry_from_obj(obj, auto_id=False):
    """Build IdeObject from a Blender mesh object."""
    from .core.ide import IdeObject
    inu = getattr(obj, 'inu', None)
    name = _clean_model_name_ide(obj.name)
    model_id = getattr(inu, 'model_id', 0) if inu else 0

    # Auto-assign ID from manager if 0
    if model_id == 0 and auto_id:
        from .data.id_manager import allocate_id
        model_id = allocate_id(name)
        if inu:
            inu.model_id = model_id

    txd_name = getattr(inu, 'txd_name', '') if inu else ''
    if not txd_name:
        txd_name = name
    draw_dist = getattr(inu, 'draw_distance', 300.0) if inu else 300.0
    flags = getattr(inu, 'ide_flags', 0) if inu else 0
    return IdeObject(model_id=model_id, model_name=name,
                     txd_name=txd_name, draw_distance=draw_dist, flags=flags)


def _ipl_entry_from_obj(obj):
    """Build IplInstance from a Blender mesh object."""
    from .core.ipl import IplInstance
    inu = getattr(obj, 'inu', None)
    name = _clean_model_name_ide(obj.name)
    model_id = getattr(inu, 'model_id', 0) if inu else 0
    interior = getattr(inu, 'interior_id', 0) if inu else 0
    lod_index = getattr(inu, 'lod_index', -1) if inu else -1
    loc = obj.matrix_world.translation
    rot = obj.matrix_world.to_quaternion().conjugated()
    return IplInstance(model_id=model_id, model_name=name,
                       interior=interior,
                       pos_x=loc.x, pos_y=loc.y, pos_z=loc.z,
                       rot_x=rot.x, rot_y=rot.y, rot_z=rot.z, rot_w=rot.w,
                       lod_index=lod_index)


def _clean_model_name_ide(name):
    from .tools.model_utils import get_model_type
    # Strip Blender duplicate suffix FIRST (.001, .002, etc.)
    if '.' in name:
        b, s = name.rsplit('.', 1)
        if s.isdigit():
            name = b
    class _Mock:
        def __init__(self, n):
            self.name = n
    _, base = get_model_type(_Mock(name))
    return base


class GTATOOLS_OT_discover_game(bpy.types.Operator):
    """Найти все IDE/IPL/IMG по gta.dat из корневой папки игры"""
    bl_idname = "gtatools.discover_game"
    bl_label = "Auto-discover"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .core.gta_dat import find_all_resources
        scene = context.scene
        game_root = bpy.path.abspath(scene.gtatools_game_root)
        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}

        dat_path = os.path.join(game_root, 'data', 'gta.dat')
        if not os.path.isfile(dat_path):
            self.report({'ERROR'}, T("Не найден data/gta.dat в указанной папке"))
            return {'CANCELLED'}

        info = find_all_resources(game_root)

        ide_count = len([p for p in info.ide_paths if os.path.isfile(p)])
        ipl_count = len([p for p in info.ipl_paths if os.path.isfile(p)])
        img_count = len([p for p in info.img_paths if os.path.isfile(p)])

        # Auto-set main IMG path if not set
        if not scene.gtatools_img_path:
            for p in info.img_paths:
                if os.path.isfile(p) and 'gta3.img' in p.lower():
                    scene.gtatools_img_path = p
                    break

        self.report({'INFO'},
                    f"IDE: {ide_count}, IPL: {ipl_count}, IMG: {img_count}")
        return {'FINISHED'}


class GTATOOLS_OT_binary_ipl_toggle_all(bpy.types.Operator):
    """Включить или выключить все бинарные IPL в списке одной кнопкой"""
    bl_idname = "gtatools.binary_ipl_toggle_all"
    bl_label = "Toggle All Binary IPLs"
    bl_options = {'REGISTER'}

    enable: BoolProperty(default=True)

    def execute(self, context):
        for item in context.scene.gtatools_binary_ipls:
            item.enabled = self.enable
        return {'FINISHED'}


class GTATOOLS_OT_scan_binary_ipls(bpy.types.Operator):
    """Сканировать IMG архивы и собрать список бинарных IPL для выбранного района. После скана можно галочками включать/выключать конкретные файлы"""
    bl_idname = "gtatools.scan_binary_ipls"
    bl_label = "Scan Binary IPLs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .core.gta_dat import find_all_resources
        from .core.img import read_directory
        scene = context.scene

        game_root = bpy.path.abspath(getattr(scene, 'gtatools_game_root', ''))
        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}

        region = getattr(scene, 'gtatools_map_region', 'ALL')
        region_u = region.upper() if region != 'ALL' else 'ALL'

        info = find_all_resources(game_root)
        img_paths = []
        std = os.path.join(game_root, 'models', 'gta3.img')
        if os.path.isfile(std):
            img_paths.append(std)
        for p in info.img_paths:
            if os.path.isfile(p) and p not in img_paths:
                img_paths.append(p)

        # Remember previously enabled entries so rescans don't lose user picks
        prev_state = {i.name.lower(): i.enabled
                      for i in scene.gtatools_binary_ipls}

        scene.gtatools_binary_ipls.clear()
        total_checked = 0
        for ip in img_paths:
            try:
                for e in read_directory(ip):
                    nm = e.name.lower()
                    if not nm.endswith('.ipl'):
                        continue
                    total_checked += 1
                    # Peek at the first 4 bytes to confirm it's binary — skip text .ipl
                    try:
                        from .core.img import extract_file
                        head = extract_file(ip, e.name)
                        if not head or head[:4] != b'bnry':
                            continue
                    except Exception:
                        continue
                    # Region match
                    if region_u != 'ALL' and not e.name.upper().startswith(region_u):
                        continue
                    item = scene.gtatools_binary_ipls.add()
                    item.name = e.name
                    item.img_source = ip
                    item.enabled = prev_state.get(nm, True)
            except Exception as ex:
                self.report({'WARNING'}, f"{os.path.basename(ip)}: {ex}")

        scene['gtatools_binary_ipls_region'] = region
        self.report({'INFO'},
                    f"{len(scene.gtatools_binary_ipls)} binary IPL(s) for region '{region}' "
                    f"(scanned {total_checked} .ipl entries)")
        return {'FINISHED'}


class GTATOOLS_OT_extract_resources(bpy.types.Operator):
    """Извлечь все DFF, COL и текстуры из IMG в .inu_cache/"""
    bl_idname = "gtatools.extract_textures"
    bl_label = "Extract Resources"
    bl_options = {'REGISTER'}

    _timer = None
    _gen = None

    def invoke(self, context, event):
        scene = context.scene
        game_root = bpy.path.abspath(scene.gtatools_game_root)

        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}

        from .core.gta_dat import find_all_resources
        from .core.img import read_directory

        info = find_all_resources(game_root)

        # Collect all IMG archives
        img_paths = []
        std = os.path.join(game_root, 'models', 'gta3.img')
        if os.path.isfile(std):
            img_paths.append(std)
        for p in info.img_paths:
            if os.path.isfile(p) and p not in img_paths:
                img_paths.append(p)
        fallback = bpy.path.abspath(scene.gtatools_img_path)
        if fallback and os.path.isfile(fallback) and fallback not in img_paths:
            img_paths.append(fallback)

        if not img_paths:
            self.report({'ERROR'}, T("Не найден IMG архив"))
            return {'CANCELLED'}

        # Create output dirs
        cache_dir = _get_cache_dir()
        tex_dir = os.path.join(cache_dir, 'textures')
        os.makedirs(tex_dir, exist_ok=True)

        # GPU mode
        use_gpu = check_nvtt_available(getattr(scene, 'gtatools_nvtt_path', ''))[0]
        nvdecompress = None
        dds_dir = None
        if use_gpu:
            nvtt_path = getattr(scene, 'gtatools_nvtt_path', '')
            if nvtt_path:
                nv = os.path.join(nvtt_path, 'nvdecompress.exe')
                if os.path.isfile(nv):
                    nvdecompress = nv
                    dds_dir = os.path.join(cache_dir, '_dds_tmp')
                    os.makedirs(dds_dir, exist_ok=True)

        # Pre-count TXDs for progress
        txd_total = 0
        for ip in img_paths:
            try:
                for e in read_directory(ip):
                    if e.name.lower().endswith('.txd'):
                        txd_total += 1
            except Exception:
                pass

        # Store state
        self._img_paths = img_paths
        self._cache_dir = cache_dir
        self._tex_dir = tex_dir
        self._use_gpu = use_gpu
        self._nvdecompress = nvdecompress
        self._dds_dir = dds_dir
        self._txd_total = txd_total
        self._dff_count = 0
        self._col_count = 0
        self._tex_count = 0
        self._skipped = 0
        self._txd_progress = 0
        self._phase = 'TXD'
        self._gpu_done = 0
        self._gpu_total = 0
        self._dds_queue = []

        self._gen = self._work(context)
        wm = context.window_manager
        wm.progress_begin(0, max(txd_total, 1))
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Извлечение ресурсов..."))
        return {'RUNNING_MODAL'}

    def _work(self, context):
        from .core.img import ImgReader
        from .core.txd import read_txd_file

        cache_dir = self._cache_dir
        tex_dir = self._tex_dir
        use_gpu = self._use_gpu
        nvdecompress = self._nvdecompress
        dds_dir = self._dds_dir
        dds_queue = self._dds_queue

        for ip in self._img_paths:
            try:
                with ImgReader(ip) as img:
                    # DFF + COL batch extraction (fast)
                    counts = img.extract_all_to(
                        cache_dir,
                        extensions={'.dff', '.col'},
                        skip_existing=True)
                    self._dff_count += counts['dff']
                    self._col_count += counts['col']
                    self._skipped += counts['skipped']

                    # TXD processing (slow — yield per entry)
                    for entry in img.entries:
                        if not entry.name.lower().endswith('.txd'):
                            continue
                        self._txd_progress += 1
                        yield

                        txd_data = img.read(entry.name)
                        if not txd_data:
                            continue

                        tmp_path = os.path.join(cache_dir, entry.name)
                        with open(tmp_path, 'wb') as f:
                            f.write(txd_data)

                        try:
                            textures = read_txd_file(tmp_path)
                            for tex in textures:
                                name = tex.name.rstrip('\x00')
                                if not name or tex.width == 0 or tex.height == 0 or not tex.pixels:
                                    continue
                                png_path = os.path.join(tex_dir, name + '.png')
                                if os.path.isfile(png_path):
                                    existing_size = os.path.getsize(png_path)
                                    new_size = tex.width * tex.height * 4
                                    if new_size <= existing_size:
                                        self._skipped += 1
                                        continue

                                if use_gpu and nvdecompress:
                                    dds_path = os.path.join(dds_dir, name + '.dds')
                                    _write_dds(dds_path, tex)
                                    dds_queue.append((dds_path, png_path))
                                    self._tex_count += 1
                                else:
                                    _write_png(png_path, tex.pixels, tex.width, tex.height)
                                    self._tex_count += 1
                        except Exception as _e:
                            _log = os.path.join(cache_dir, '_txd_errors.log')
                            with open(_log, 'a', encoding='utf-8') as _lf:
                                _lf.write(f"{entry.name}: {_e}\n")

                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
            except Exception:
                pass

        # GPU batch conversion
        if dds_queue and nvdecompress:
            self._phase = 'GPU'
            self._gpu_total = len(dds_queue)

            workers = min(os.cpu_count() or 4, 8)

            def _convert(args):
                dds_p, png_p = args
                try:
                    subprocess.run(
                        [nvdecompress, '-format', 'png', dds_p, png_p],
                        capture_output=True, timeout=10)
                except Exception:
                    pass

            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_convert, args) for args in dds_queue]
                while True:
                    done = sum(1 for f in futures if f.done())
                    self._gpu_done = done
                    if done >= len(futures):
                        break
                    yield

            if dds_dir:
                try:
                    import shutil
                    shutil.rmtree(dds_dir, ignore_errors=True)
                except Exception:
                    pass

    def modal(self, context, event):
        if event.type == 'ESC':
            self._cleanup(context)
            self.report({'WARNING'}, T("Отменено"))
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        import time
        wm = context.window_manager
        deadline = time.monotonic() + 0.1

        while time.monotonic() < deadline:
            try:
                next(self._gen)
            except StopIteration:
                self._cleanup(context)
                gpu_str = " (GPU)" if (self._use_gpu and self._nvdecompress) else ""
                self.report({'INFO'},
                    f"DFF: {self._dff_count}, COL: {self._col_count}, "
                    f"{T('Извлечено текстур:')} {self._tex_count}{gpu_str}, "
                    f"{T('пропущено:')} {self._skipped}")
                return {'FINISHED'}

        # Update UI
        if self._phase == 'GPU':
            wm.progress_begin(0, max(self._gpu_total, 1))
            wm.progress_update(self._gpu_done)
            context.workspace.status_text_set(
                f"GPU DDS→PNG: {self._gpu_done}/{self._gpu_total}")
        else:
            wm.progress_update(self._txd_progress)
            context.workspace.status_text_set(
                f"TXD: {self._txd_progress}/{self._txd_total} | "
                f"DFF: {self._dff_count} COL: {self._col_count}")

        return {'RUNNING_MODAL'}

    def _cleanup(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        context.workspace.status_text_set(None)


_bbox_mode_active = False
_bbox_last_selection = set()


_bbox_near_set = set()


def _bbox_selection_handler(scene, depsgraph):
    """Keep selected + nearby (300m) objects as TEXTURED, rest as BOUNDS."""
    global _bbox_last_selection, _bbox_near_set
    if not _bbox_mode_active:
        return

    try:
        selected = {o.name for o in bpy.context.selected_objects if o.type == 'MESH'}
    except Exception:
        return
    if selected == _bbox_last_selection:
        return
    _bbox_last_selection = selected

    sel_positions = []
    for name in selected:
        obj = bpy.data.objects.get(name)
        if obj:
            sel_positions.append(obj.location)

    new_near = set()
    radius = 300.0

    for col in bpy.data.collections:
        if not col.name.startswith('Map_'):
            continue
        for obj in col.objects:
            if obj.type != 'MESH':
                continue
            if obj.name in selected:
                new_near.add(obj.name)
            elif sel_positions and any((obj.location - sp).length <= radius for sp in sel_positions):
                new_near.add(obj.name)

    # Objects that left the near zone → BOUNDS
    for name in _bbox_near_set - new_near:
        obj = bpy.data.objects.get(name)
        if obj and obj.type == 'MESH':
            obj.display_type = 'BOUNDS'

    # Objects that entered the near zone → TEXTURED
    for name in new_near - _bbox_near_set:
        obj = bpy.data.objects.get(name)
        if obj and obj.type == 'MESH':
            obj.display_type = 'TEXTURED'

    _bbox_near_set = new_near


# ── Model Links Visualization ────────────────────────────────────────

_links_draw_handler = None
_links_active = False


def _draw_model_links():
    """Draw lines between DFF↔LOD↔COL related models."""
    import gpu
    from gpu_extras.batch import batch_for_shader

    if not _links_active:
        return

    from .tools.model_utils import get_model_type

    # Group objects by base name
    groups = {}  # base_name → {'DFF': obj, 'LOD': obj, 'COL': obj}
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        mt, base = get_model_type(obj)
        if not base:
            continue
        base_clean = base.rstrip('_').lower()
        if base_clean not in groups:
            groups[base_clean] = {'DFF': None, 'LOD': None, 'COL': None}
        if mt and groups[base_clean][mt] is None:
            groups[base_clean][mt] = obj

    # Build dashed lines
    verts = []
    colors = []
    dash_len = 0.5
    gap_len = 0.3

    def _add_dashed(p1, p2, color):
        from mathutils import Vector
        a = Vector(p1)
        b = Vector(p2)
        d = b - a
        total = d.length
        if total < 0.01:
            return
        step = dash_len + gap_len
        n = d.normalized()
        t = 0.0
        while t < total:
            seg_start = a + n * t
            seg_end = a + n * min(t + dash_len, total)
            verts.extend([seg_start, seg_end])
            colors.extend([color, color])
            t += step

    for base, g in groups.items():
        dff = g['DFF']
        lod = g['LOD']
        col = g['COL']

        if dff and lod:
            _add_dashed(dff.location, lod.location, (0.2, 0.6, 1.0, 0.8))  # blue
        if dff and col:
            _add_dashed(dff.location, col.location, (1.0, 0.3, 0.1, 0.8))  # red
        if lod and col and not dff:
            _add_dashed(lod.location, col.location, (1.0, 0.6, 0.0, 0.8))  # orange

    if not verts:
        return

    shader = gpu.shader.from_builtin('FLAT_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": verts, "color": colors})
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(3.0)
    shader.bind()
    batch.draw(shader)
    gpu.state.blend_set('NONE')
    gpu.state.line_width_set(1.0)


class GTATOOLS_OT_toggle_links(bpy.types.Operator):
    """Показать/скрыть линии связей DFF↔LOD↔COL"""
    bl_idname = "gtatools.toggle_links"
    bl_label = "Toggle Model Links"
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _links_active, _links_draw_handler

        _links_active = not _links_active

        if _links_active:
            if _links_draw_handler is None:
                _links_draw_handler = bpy.types.SpaceView3D.draw_handler_add(
                    _draw_model_links, (), 'WINDOW', 'POST_VIEW')
            self.report({'INFO'}, "Model Links: ON")
        else:
            if _links_draw_handler is not None:
                bpy.types.SpaceView3D.draw_handler_remove(_links_draw_handler, 'WINDOW')
                _links_draw_handler = None
            self.report({'INFO'}, "Model Links: OFF")

        # Force viewport redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


class GTATOOLS_OT_toggle_bbox(bpy.types.Operator):
    """Переключить все Map_ объекты между Bounding Box и Textured"""
    bl_idname = "gtatools.toggle_bbox"
    bl_label = "Toggle Bounding Box"
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _bbox_mode_active, _bbox_last_selection, _bbox_near_set

        _bbox_mode_active = not _bbox_mode_active

        selected = {o.name for o in context.selected_objects if o.type == 'MESH'}

        if _bbox_mode_active:
            sel_positions = []
            for name in selected:
                obj = bpy.data.objects.get(name)
                if obj:
                    sel_positions.append(obj.location)

            radius = 300.0
            count = 0
            near = set()
            for col in bpy.data.collections:
                if not col.name.startswith('Map_'):
                    continue
                for obj in col.objects:
                    if obj.type == 'MESH':
                        is_near = (obj.name in selected or
                                   (sel_positions and any((obj.location - sp).length <= radius for sp in sel_positions)))
                        obj.display_type = 'TEXTURED' if is_near else 'BOUNDS'
                        if is_near:
                            near.add(obj.name)
                        count += 1

            _bbox_last_selection = selected
            _bbox_near_set = near
            if _bbox_selection_handler not in bpy.app.handlers.depsgraph_update_post:
                bpy.app.handlers.depsgraph_update_post.append(_bbox_selection_handler)
        else:
            count = 0
            for col in bpy.data.collections:
                if not col.name.startswith('Map_'):
                    continue
                for obj in col.objects:
                    if obj.type == 'MESH':
                        obj.display_type = 'TEXTURED'
                        count += 1

            _bbox_last_selection = set()
            _bbox_near_set = set()
            if _bbox_selection_handler in bpy.app.handlers.depsgraph_update_post:
                bpy.app.handlers.depsgraph_update_post.remove(_bbox_selection_handler)

        self.report({'INFO'}, f"BBox: {'ON' if _bbox_mode_active else 'OFF'} ({count})")
        return {'FINISHED'}


class GTATOOLS_OT_load_map_glb(bpy.types.Operator, ImportHelper):
    """Импортировать .glb карты с сортировкой по коллекциям"""
    bl_idname = "gtatools.load_map_glb"
    bl_label = "Import Map glTF"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".glb"
    filter_glob: StringProperty(default="*.glb;*.gltf", options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    _timer = None
    _gen = None

    def execute(self, context):
        from .core.gta_dat import find_all_resources
        from .core.ide import read_ide

        scene = context.scene

        # Read IDE for properties
        game_root = bpy.path.abspath(scene.gtatools_game_root)
        ide_models = {}
        if game_root and os.path.isdir(game_root):
            info = find_all_resources(game_root)
            for p in info.ide_paths:
                if os.path.isfile(p):
                    try:
                        ide = read_ide(p)
                        for obj in ide.objects:
                            ide_models[obj.model_id] = obj
                        for anim in ide.anims:
                            if anim.model_id not in ide_models:
                                ide_models[anim.model_id] = anim
                    except Exception:
                        pass

        # Collect valid files
        glb_files = []
        for f in self.files:
            glb_path = os.path.join(self.directory, f.name)
            if os.path.isfile(glb_path):
                glb_files.append(glb_path)

        if not glb_files:
            self.report({'WARNING'}, T("Нет файлов для импорта"))
            return {'CANCELLED'}

        self._ide_models = ide_models
        self._glb_files = glb_files
        self._total_imported = 0
        self._file_idx = 0

        self._gen = self._work(context)
        wm = context.window_manager
        wm.progress_begin(0, len(glb_files))
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Импорт .glb..."))
        return {'RUNNING_MODAL'}

    def _work(self, context):
        for idx, glb_path in enumerate(self._glb_files):
            self._file_idx = idx
            fname = os.path.basename(glb_path)
            yield  # let UI update before blocking import

            before = set(context.scene.objects)
            bpy.ops.import_scene.gltf(filepath=glb_path)
            after = set(context.scene.objects)
            new_objs = list(after - before)

            _sort_map_objects(context, new_objs, self._ide_models)
            self._total_imported += len(new_objs)

    def modal(self, context, event):
        if event.type == 'ESC':
            self._cleanup(context)
            self.report({'WARNING'}, T("Отменено"))
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        wm = context.window_manager

        try:
            next(self._gen)
        except StopIteration:
            self._cleanup(context)
            self.report({'INFO'}, f"{T('Импортировано:')} {self._total_imported}")
            return {'FINISHED'}

        wm.progress_update(self._file_idx)
        fname = os.path.basename(self._glb_files[self._file_idx]) if self._file_idx < len(self._glb_files) else ""
        context.workspace.status_text_set(
            f"{T('Импорт .glb:')} {self._file_idx + 1}/{len(self._glb_files)} {fname}")
        return {'RUNNING_MODAL'}

    def _cleanup(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        context.workspace.status_text_set(None)


class GTATOOLS_OT_build_map_glb(bpy.types.Operator):
    """Собрать один .glb файл карты (все модели с позициями из IPL)"""
    bl_idname = "gtatools.build_map_glb"
    bl_label = "Build Map glTF"
    bl_options = {'REGISTER'}

    _timer = None
    _thread = None

    def invoke(self, context, event):
        from .core.gta_dat import find_all_resources
        from .core.ide import read_ide
        from .core.ipl import read_ipl, _read_binary_ipl
        from .core.img import extract_file, read_directory
        from .tools.dff2gltf import build_map_glb

        scene = context.scene
        game_root = bpy.path.abspath(scene.gtatools_game_root)
        cache_dir = _get_cache_dir()
        tex_dir = os.path.join(cache_dir, 'textures')
        skip_lod = getattr(scene, 'gtatools_img_skip_lod', False)
        region = getattr(scene, 'gtatools_map_region', 'ALL')

        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}

        dff_count = len([f for f in os.listdir(cache_dir) if f.lower().endswith('.dff')])
        if dff_count == 0:
            self.report({'WARNING'}, T("Нет DFF файлов в кэше. Сначала извлеките ресурсы."))
            return {'CANCELLED'}

        info = find_all_resources(game_root)

        # Read IDE
        ide_models = {}
        for p in info.ide_paths:
            if os.path.isfile(p):
                try:
                    ide = read_ide(p)
                    for obj in ide.objects:
                        ide_models[obj.model_id] = obj
                    for anim in ide.anims:
                        if anim.model_id not in ide_models:
                            ide_models[anim.model_id] = anim
                except Exception:
                    pass

        def _match(path):
            if region == 'ALL':
                return True
            parts = path.replace('\\', '/').upper().split('/')
            for i, part in enumerate(parts):
                if part == 'MAPS' and i + 1 < len(parts):
                    return parts[i + 1] == region
            name = path.replace('\\', '/').rsplit('/', 1)[-1].upper()
            return name.startswith(region)

        # Read IPL instances
        instances = []
        for p in info.ipl_paths:
            if os.path.isfile(p) and _match(p):
                try:
                    ipl = read_ipl(p)
                    instances.extend(ipl.instances)
                except Exception:
                    pass

        # Binary IPL from IMG
        img_paths = []
        std = os.path.join(game_root, 'models', 'gta3.img')
        if os.path.isfile(std):
            img_paths.append(std)
        for p in info.img_paths:
            if os.path.isfile(p) and p not in img_paths:
                img_paths.append(p)

        # Binary IPL selection — if the scene collection has entries, honour
        # the user's explicit enabled/disabled picks; otherwise fall back to
        # the region-based auto-match.
        bi_entries = scene.gtatools_binary_ipls
        bi_enabled = {i.name.lower() for i in bi_entries if i.enabled}
        bi_use_selection = len(bi_entries) > 0

        for ip in img_paths:
            try:
                for e in read_directory(ip):
                    key = e.name.lower()
                    if not key.endswith('.ipl'):
                        continue
                    if bi_use_selection:
                        if key not in bi_enabled:
                            continue
                    elif not _match(key):
                        continue
                    ipl_data = extract_file(ip, e.name)
                    if ipl_data and ipl_data[:4] == b'bnry':
                        ipl_parsed = _read_binary_ipl(ipl_data)
                        instances.extend(ipl_parsed.instances)
            except Exception:
                pass

        for inst in instances:
            if not inst.model_name and inst.model_id in ide_models:
                inst.model_name = ide_models[inst.model_id].model_name

        if not instances:
            self.report({'WARNING'}, T("IPL файл пуст или не указан"))
            return {'CANCELLED'}

        out_name = f"map_{region.lower()}.glb"
        out_path = os.path.join(cache_dir, out_name)
        if os.path.isfile(out_path):
            try:
                os.remove(out_path)
            except Exception:
                pass

        # Store state
        self._out_path = out_path
        self._ide_models = ide_models
        self._instance_count = len(instances)
        self._pg_current = 0
        self._pg_name = ''
        self._result = None
        self._error = None

        # Progress callback (called from thread — GIL-safe)
        def _progress_cb(current, total, name):
            self._pg_current = current
            self._pg_name = name

        # Start build in background thread
        import threading

        def _thread_fn():
            try:
                self._result = build_map_glb(
                    cache_dir=cache_dir,
                    instances=instances,
                    ide_models=ide_models,
                    output_path=out_path,
                    tex_dir=tex_dir,
                    skip_lod=skip_lod,
                    callback=_progress_cb,
                )
            except Exception as e:
                self._error = str(e)

        self._thread = threading.Thread(target=_thread_fn, daemon=True)
        self._thread.start()

        wm = context.window_manager
        wm.progress_begin(0, len(instances))
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Сборка карты..."))
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            self._cleanup(context)
            self.report({'WARNING'}, T("Отменено"))
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        wm = context.window_manager
        wm.progress_update(self._pg_current)
        context.workspace.status_text_set(
            f"{T('Сборка карты:')} {self._pg_current}/{self._instance_count} {self._pg_name}")

        if self._thread.is_alive():
            return {'RUNNING_MODAL'}

        # Thread finished
        self._thread.join()
        self._thread = None

        if self._error:
            self._cleanup(context)
            self.report({'ERROR'}, f"Build error: {self._error}")
            return {'CANCELLED'}

        result = self._result
        if result and result['placed'] > 0:
            context.workspace.status_text_set(T("Импорт .glb..."))

            before = set(context.scene.objects)
            bpy.ops.import_scene.gltf(filepath=self._out_path)
            after = set(context.scene.objects)
            new_objs = list(after - before)

            _sort_map_objects(context, new_objs, self._ide_models)

            self._cleanup(context)
            self.report({'INFO'},
                        f"{T('Импортировано:')} {len(new_objs)} obj, "
                        f"{result['meshes']} {T('уникальных моделей')}, "
                        f"{result['skipped']} {T('пропущено')}")
        else:
            self._cleanup(context)
            self.report({'WARNING'}, T("Нет моделей для импорта"))

        return {'FINISHED'}

    def _cleanup(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        context.workspace.status_text_set(None)


class GTATOOLS_OT_import_map(bpy.types.Operator):
    """Импорт карты GTA SA: автопоиск IDE/IPL/IMG по папке игры"""
    bl_idname = "gtatools.import_map"
    bl_label = "Import Map"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _gen = None

    def invoke(self, context, event):
        from .core.gta_dat import find_all_resources
        from .core.img import extract_file, read_directory
        from .core.ide import read_ide
        from .core.ipl import read_ipl, _read_binary_ipl
        from .ops.ipl_sections import import_ipl_sections

        scene = context.scene
        game_root = bpy.path.abspath(scene.gtatools_game_root)
        skip_lod = getattr(scene, 'gtatools_img_skip_lod', False)
        fake_mode = getattr(scene, 'gtatools_map_fake_mode', True)

        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}

        dat_path = os.path.join(game_root, 'data', 'gta.dat')
        if not os.path.isfile(dat_path):
            self.report({'ERROR'}, T("Не найден data/gta.dat в указанной папке"))
            return {'CANCELLED'}

        info = find_all_resources(game_root)

        # Collect ALL available IMG archives
        img_paths = []
        for p in info.img_paths:
            if os.path.isfile(p) and p not in img_paths:
                img_paths.append(p)
        std = os.path.join(game_root, 'models', 'gta3.img')
        if os.path.isfile(std) and std not in img_paths:
            img_paths.insert(0, std)
        fallback = bpy.path.abspath(scene.gtatools_img_path)
        if fallback and os.path.isfile(fallback) and fallback not in img_paths:
            img_paths.append(fallback)
        if not img_paths:
            self.report({'ERROR'}, T("Не найден IMG архив"))
            return {'CANCELLED'}

        # Read all IDE files
        ide_models = {}
        for p in info.ide_paths:
            if os.path.isfile(p):
                try:
                    ide = read_ide(p)
                    for obj in ide.objects:
                        ide_models[obj.model_id] = obj
                    for anim in ide.anims:
                        if anim.model_id not in ide_models:
                            ide_models[anim.model_id] = anim
                except Exception:
                    pass

        # Region filter
        region = getattr(scene, 'gtatools_map_region', 'ALL')
        def _ipl_matches_region(path: str) -> bool:
            if region == 'ALL':
                return True
            parts = path.replace('\\', '/').upper().split('/')
            for i, part in enumerate(parts):
                if part == 'MAPS' and i + 1 < len(parts):
                    return parts[i + 1] == region
            name = path.replace('\\', '/').rsplit('/', 1)[-1].upper()
            return name.startswith(region)

        # Read text IPL files
        instances = []
        for p in info.ipl_paths:
            if os.path.isfile(p) and _ipl_matches_region(p):
                try:
                    ipl = read_ipl(p)
                    instances.extend(ipl.instances)
                    if any([ipl.culls, ipl.garages, ipl.enexs, ipl.pickups,
                            ipl.cars, ipl.jumps, ipl.auzos, ipl.occls]):
                        import_ipl_sections(ipl)
                except Exception:
                    pass

        # Binary IPL selection (see build_map_glb for details)
        bi_entries = scene.gtatools_binary_ipls
        bi_enabled = {i.name.lower() for i in bi_entries if i.enabled}
        bi_use_selection = len(bi_entries) > 0

        # Build unified file index
        img_files = {}
        for ip in img_paths:
            try:
                for e in read_directory(ip):
                    key = e.name.lower()
                    if key not in img_files:
                        img_files[key] = (e.name, ip)
                    if not key.endswith('.ipl'):
                        continue
                    if bi_use_selection:
                        if key not in bi_enabled:
                            continue
                    elif not _ipl_matches_region(key):
                        continue
                    try:
                        ipl_data = extract_file(ip, e.name)
                        if ipl_data and ipl_data[:4] == b'bnry':
                            ipl_parsed = _read_binary_ipl(ipl_data)
                            instances.extend(ipl_parsed.instances)
                    except Exception:
                        pass
            except Exception:
                pass

        if not instances:
            self.report({'WARNING'}, T("IPL файл пуст или не указан"))
            return {'CANCELLED'}

        for inst in instances:
            if not inst.model_name and inst.model_id in ide_models:
                inst.model_name = ide_models[inst.model_id].model_name

        # Create collections
        def _get_col(name):
            c = bpy.data.collections.get(name)
            if not c:
                c = bpy.data.collections.new(name)
                context.scene.collection.children.link(c)
            return c

        dff_far = _get_col("Map_DFF_Far")
        dff_mid = _get_col("Map_DFF_Mid")
        dff_near = _get_col("Map_DFF_Near")
        lod_col = _get_col("Map_LOD")

        # Hide collections during import
        dff_far.hide_viewport = True
        dff_mid.hide_viewport = True
        dff_near.hide_viewport = True
        lod_col.hide_viewport = True

        # Store state
        self._instances = instances
        self._ide_models = ide_models
        self._img_files = img_files
        self._skip_lod = skip_lod
        self._fake_mode = fake_mode
        self._dff_far = dff_far
        self._dff_mid = dff_mid
        self._dff_near = dff_near
        self._lod_col = lod_col
        self._imported = 0
        self._skipped = 0
        self._progress = 0
        self._total = len(instances)
        self._scene = scene

        self._gen = self._work(context)
        wm = context.window_manager
        wm.progress_begin(0, len(instances))
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Импорт карты..."))
        return {'RUNNING_MODAL'}

    def _pick_dff_col(self, model_id):
        ide_models = self._ide_models
        if model_id in ide_models:
            dd = ide_models[model_id].draw_distance
            if dd >= 300:
                return self._dff_far
            elif dd >= 100:
                return self._dff_mid
            else:
                return self._dff_near
        return self._dff_far

    def _work(self, context):
        from .core.img import extract_file
        from .core.ipl import is_lod_name, lod_instance_indices
        from mathutils import Quaternion
        import bmesh

        instances = self._instances
        ide_models = self._ide_models
        img_files = self._img_files
        skip_lod = self._skip_lod
        scene = self._scene
        lod_col = self._lod_col
        # Authoritative LOD detection: any instance referenced by
        # another via its lod_index IS a LOD, regardless of name.
        lod_refs = lod_instance_indices(instances)

        if self._fake_mode:
            # ── FAKE MODE ──
            plane_mesh = bpy.data.meshes.new("_fake_plane")
            bm = bmesh.new()
            bm.verts.new((-25, -25, 0))
            bm.verts.new((25, -25, 0))
            bm.verts.new((25, 25, 0))
            bm.verts.new((-25, 25, 0))
            bm.faces.new(bm.verts)
            bm.to_mesh(plane_mesh)
            bm.free()

            for idx, inst in enumerate(instances):
                self._progress = idx + 1

                model_name = inst.model_name
                if not model_name:
                    self._skipped += 1
                    if idx % 32 == 0:
                        yield
                    continue

                is_lod = idx in lod_refs or is_lod_name(model_name)
                if skip_lod and is_lod:
                    self._skipped += 1
                    if idx % 32 == 0:
                        yield
                    continue

                target = lod_col if is_lod else self._pick_dff_col(inst.model_id)

                obj = bpy.data.objects.new(model_name, plane_mesh)
                obj.location = (inst.pos_x, inst.pos_y, inst.pos_z)
                rot = Quaternion((inst.rot_w, inst.rot_x, inst.rot_y, inst.rot_z)).conjugated()
                obj.rotation_mode = 'QUATERNION'
                obj.rotation_quaternion = rot
                obj.display_type = 'WIRE'

                obj['map_fake'] = True
                obj['map_model_name'] = model_name
                obj['map_model_id'] = inst.model_id
                obj['map_interior'] = inst.interior
                obj['map_lod_index'] = inst.lod_index

                if inst.model_id in ide_models:
                    ide_obj = ide_models[inst.model_id]
                    obj['map_txd_name'] = ide_obj.txd_name
                    obj['map_draw_distance'] = ide_obj.draw_distance
                    obj['map_flags'] = ide_obj.flags

                target.objects.link(obj)
                self._imported += 1
                yield

        else:
            # ── FULL MODE ──
            imported_models = {}
            tmpdir = _get_cache_dir()

            for idx, inst in enumerate(instances):
                self._progress = idx + 1
                model_name = inst.model_name
                if not model_name:
                    self._skipped += 1
                    if idx % 32 == 0:
                        yield
                    continue

                is_lod = idx in lod_refs or is_lod_name(model_name)
                if skip_lod and is_lod:
                    self._skipped += 1
                    if idx % 32 == 0:
                        yield
                    continue

                target = lod_col if is_lod else self._pick_dff_col(inst.model_id)
                dff_fn = model_name + '.dff'

                if dff_fn.lower() not in img_files:
                    self._skipped += 1
                    if idx % 32 == 0:
                        yield
                    continue

                if model_name in imported_models:
                    new_objs = []
                    for src in imported_models[model_name]:
                        o = src.copy()
                        o.data = src.data
                        target.objects.link(o)
                        new_objs.append(o)
                else:
                    dff_path = os.path.join(tmpdir, dff_fn)
                    if not os.path.isfile(dff_path):
                        dff_entry = img_files[dff_fn.lower()]
                        dff_data = extract_file(dff_entry[1], dff_entry[0])
                        if not dff_data:
                            continue
                        with open(dff_path, 'wb') as f:
                            f.write(dff_data)

                    try:
                        before = set(context.scene.objects)
                        glb_path = os.path.splitext(dff_path)[0] + '.glb'
                        if os.path.isfile(glb_path):
                            bpy.ops.import_scene.gltf(filepath=glb_path)
                        else:
                            from .ops.dff_import import import_dff as inu_import_dff
                            inu_import_dff(filepath=dff_path, context=context)
                        after = set(context.scene.objects)
                        new_objs = list(after - before)

                        load_txd = getattr(scene, 'gtatools_img_load_txd', True)
                        if load_txd:
                            tex_cache = os.path.join(tmpdir, 'textures')
                            _loaded_from_cache = False
                            if os.path.isdir(tex_cache):
                                _loaded_from_cache = _load_textures_from_cache(
                                    tex_cache, new_objs)

                            if not _loaded_from_cache:
                                from .ops.txd_import import import_txd as inu_import_txd
                                txd_name = model_name
                                if inst.model_id in ide_models:
                                    txd_name = ide_models[inst.model_id].txd_name
                                txd_fn = txd_name + '.txd'
                                if txd_fn.lower() in img_files:
                                    txd_path = os.path.join(tmpdir, txd_fn)
                                    if not os.path.isfile(txd_path):
                                        txd_entry = img_files[txd_fn.lower()]
                                        txd_data = extract_file(txd_entry[1], txd_entry[0])
                                        if txd_data:
                                            with open(txd_path, 'wb') as f:
                                                f.write(txd_data)
                                    if os.path.isfile(txd_path):
                                        try:
                                            inu_import_txd(filepath=txd_path)
                                        except Exception:
                                            pass

                        for o in new_objs:
                            for c in list(o.users_collection):
                                c.objects.unlink(o)
                            target.objects.link(o)

                        imported_models[model_name] = new_objs
                    except Exception:
                        continue

                pos = (inst.pos_x, inst.pos_y, inst.pos_z)
                rot = Quaternion((inst.rot_w, inst.rot_x, inst.rot_y, inst.rot_z)).conjugated()
                for o in new_objs:
                    if o.type == 'MESH':
                        o.location = pos
                        o.rotation_mode = 'QUATERNION'
                        o.rotation_quaternion = rot
                        if hasattr(o, 'inu'):
                            o.inu.model_id = inst.model_id
                            if inst.model_id in ide_models:
                                ide_obj = ide_models[inst.model_id]
                                o.inu.draw_distance = ide_obj.draw_distance
                                o.inu.ide_flags = ide_obj.flags
                                o.inu.txd_name = ide_obj.txd_name
                self._imported += 1
                yield

    def modal(self, context, event):
        if event.type == 'ESC':
            self._finish(context)
            self.report({'WARNING'}, T("Отменено"))
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        import time
        wm = context.window_manager
        deadline = time.monotonic() + 0.1

        while time.monotonic() < deadline:
            try:
                next(self._gen)
            except StopIteration:
                self._progress = self._total
                wm.progress_update(self._total)
                self._finish(context)
                msg = f"{T('Импортировано:')} {self._imported}"
                if self._skipped:
                    msg += f", {T('пропущено:')} {self._skipped}"
                self.report({'INFO'}, msg)
                return {'FINISHED'}

        wm.progress_update(self._progress)
        context.workspace.status_text_set(
            f"{T('Импорт карты:')} {self._progress}/{self._total}")
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        context.workspace.status_text_set(None)

        # Re-enable viewport
        for col in (self._dff_far, self._dff_mid, self._dff_near, self._lod_col):
            if col:
                col.hide_viewport = False

        context.view_layer.update()


class GTATOOLS_OT_replace_fake_with_dff(bpy.types.Operator):
    """Заменить выделенные fake-объекты на DFF модели из IMG"""
    bl_idname = "gtatools.replace_fake_dff"
    bl_label = "Replace with DFF"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .ops.dff_import import import_dff as inu_import_dff
        from .ops.txd_import import import_txd as inu_import_txd

        scene = context.scene
        game_root = bpy.path.abspath(scene.gtatools_game_root)
        cache_dir = _get_cache_dir()
        tex_dir = os.path.join(cache_dir, 'textures')

        # Find selected fake objects
        fakes = [o for o in context.selected_objects
                 if o.get('map_fake') and o.get('map_model_name')]
        if not fakes:
            self.report({'WARNING'}, T("Выделите fake объекты карты"))
            return {'CANCELLED'}

        # Build IMG reader only if needed (lazy)
        img_reader = None
        load_txd = getattr(scene, 'gtatools_img_load_txd', True)

        wm = context.window_manager
        wm.progress_begin(0, len(fakes))

        # Hide all target collections during replacement
        affected_cols = set()
        for fake in fakes:
            if fake.users_collection:
                affected_cols.add(fake.users_collection[0])
        col_visibility = {}
        for col in affected_cols:
            col_visibility[col] = col.hide_viewport
            col.hide_viewport = True

        replaced = 0
        imported_models = {}

        for idx, fake in enumerate(fakes):
            if idx % 5 == 0:
                wm.progress_update(idx)
            model_name = fake['map_model_name']
            dff_fn = model_name + '.dff'

            # Get collection of the fake object
            target = fake.users_collection[0] if fake.users_collection else context.scene.collection

            # Import or reuse model
            if model_name in imported_models:
                new_objs = []
                for src in imported_models[model_name]:
                    o = src.copy()
                    o.data = src.data  # linked duplicate
                    target.objects.link(o)
                    new_objs.append(o)
            else:
                # Try cache first, then IMG
                dff_path = os.path.join(cache_dir, dff_fn)
                if not os.path.isfile(dff_path):
                    # Lazy init IMG reader
                    if img_reader is None:
                        img_reader = self._open_img(scene, game_root)
                    if img_reader is None:
                        continue
                    dff_data = img_reader.read(dff_fn)
                    if not dff_data:
                        continue
                    with open(dff_path, 'wb') as f:
                        f.write(dff_data)

                try:
                    before = set(context.scene.objects)
                    glb_path = os.path.splitext(dff_path)[0] + '.glb'
                    if os.path.isfile(glb_path):
                        bpy.ops.import_scene.gltf(filepath=glb_path)
                    else:
                        inu_import_dff(filepath=dff_path, context=context)
                    after = set(context.scene.objects)
                    new_objs = list(after - before)

                    if load_txd and os.path.isdir(tex_dir):
                        _load_textures_from_cache(tex_dir, new_objs)

                    for o in new_objs:
                        for c in list(o.users_collection):
                            c.objects.unlink(o)
                        target.objects.link(o)

                    imported_models[model_name] = new_objs
                except Exception:
                    continue

            # Position new objects at fake's transform
            for o in new_objs:
                if o.type == 'MESH':
                    o.location = fake.location.copy()
                    o.rotation_mode = 'QUATERNION'
                    o.rotation_quaternion = fake.rotation_quaternion.copy()
                    if hasattr(o, 'inu'):
                        o.inu.model_id = fake.get('map_model_id', 0)
                        o.inu.txd_name = fake.get('map_txd_name', '')
                        o.inu.draw_distance = fake.get('map_draw_distance', 300.0)
                        o.inu.ide_flags = fake.get('map_flags', 0)

            # Delete fake object
            bpy.data.objects.remove(fake, do_unlink=True)
            replaced += 1

        # Restore collection visibility
        for col, vis in col_visibility.items():
            col.hide_viewport = vis
        context.view_layer.update()

        # Close IMG reader if opened
        if img_reader:
            img_reader.close()

        wm.progress_end()
        self.report({'INFO'}, f"{T('Заменено:')} {replaced}")
        return {'FINISHED'}

    @staticmethod
    def _open_img(scene, game_root):
        """Open ImgReader from settings or game root."""
        from .core.img import ImgReader
        img_path = bpy.path.abspath(scene.gtatools_img_path)
        if not img_path or not os.path.isfile(img_path):
            if game_root:
                std = os.path.join(game_root, 'models', 'gta3.img')
                if os.path.isfile(std):
                    img_path = std
        if not img_path or not os.path.isfile(img_path):
            return None
        reader = ImgReader(img_path)
        reader.open()
        return reader


class GTATOOLS_OT_import_from_img(bpy.types.Operator):
    """Импортировать модели из IMG архива (по списку из IDE/IPL)"""
    bl_idname = "gtatools.import_from_img"
    bl_label = "Import from IMG"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import tempfile
        from .core.img import extract_file, read_directory
        from .core.ide import read_ide
        from .core.ipl import read_ipl
        from .ops.dff_import import import_dff as inu_import_dff
        from .ops.txd_import import import_txd as inu_import_txd
        from mathutils import Quaternion

        scene = context.scene
        img_path = bpy.path.abspath(scene.gtatools_img_path)
        ide_path = bpy.path.abspath(scene.gtatools_ide_path)
        ipl_path = bpy.path.abspath(scene.gtatools_ipl_path)
        game_root = bpy.path.abspath(scene.gtatools_game_root)

        if not img_path or not os.path.isfile(img_path):
            self.report({'ERROR'}, T("Укажите путь к IMG архиву в INU Tools"))
            return {'CANCELLED'}

        # Collect IDE models and IPL instances
        ide_models = {}
        instances = []

        use_gta_dat = getattr(scene, 'gtatools_img_use_gta_dat', False)
        skip_lod = getattr(scene, 'gtatools_img_skip_lod', False)
        load_txd = getattr(scene, 'gtatools_img_load_txd', True)

        if use_gta_dat and game_root and os.path.isdir(game_root):
            # Auto-discover all IDE/IPL from gta.dat
            from .core.gta_dat import find_all_resources
            info = find_all_resources(game_root)

            for p in info.ide_paths:
                if os.path.isfile(p):
                    try:
                        ide = read_ide(p)
                        for obj in ide.objects:
                            ide_models[obj.model_id] = obj
                        for anim in ide.anims:
                            if anim.model_id not in ide_models:
                                ide_models[anim.model_id] = anim
                    except Exception:
                        pass

            for p in info.ipl_paths:
                if os.path.isfile(p):
                    try:
                        ipl = read_ipl(p)
                        instances.extend(ipl.instances)
                    except Exception:
                        pass

            # Also read binary IPL from IMG (stream files)
            img_dir = read_directory(img_path)
            for e in img_dir:
                if e.name.lower().endswith('.ipl'):
                    try:
                        ipl_data = extract_file(img_path, e.name)
                        if ipl_data and ipl_data[:4] == b'bnry':
                            ipl = read_ipl.__wrapped__(ipl_data) if hasattr(read_ipl, '__wrapped__') else None
                            if ipl is None:
                                from .core.ipl import _read_binary_ipl
                                ipl_parsed = _read_binary_ipl(ipl_data)
                                instances.extend(ipl_parsed.instances)
                    except Exception:
                        pass
        else:
            # Single IDE / IPL mode
            if ide_path and os.path.isfile(ide_path):
                ide = read_ide(ide_path)
                for obj in ide.objects:
                    ide_models[obj.model_id] = obj
                for anim in ide.anims:
                    if anim.model_id not in ide_models:
                        ide_models[anim.model_id] = anim

            if ipl_path and os.path.isfile(ipl_path):
                ipl = read_ipl(ipl_path)
                instances = ipl.instances

        if not instances:
            self.report({'ERROR'}, T("IPL файл пуст или не указан"))
            return {'CANCELLED'}

        # Build set of model names to import
        img_files = {e.name.lower(): e.name for e in read_directory(img_path)}

        # Create collections for DFF, LOD and COL
        def _get_or_create_collection(name):
            col = bpy.data.collections.get(name)
            if not col:
                col = bpy.data.collections.new(name)
                context.scene.collection.children.link(col)
            return col

        dff_collection = _get_or_create_collection("Map_DFF")
        lod_collection = _get_or_create_collection("Map_LOD")
        col_collection = _get_or_create_collection("Map_COL")

        wm = context.window_manager
        wm.progress_begin(0, len(instances))

        imported_count = 0
        skipped_count = 0
        errors = []

        from .core.ipl import is_lod_name, lod_instance_indices
        lod_refs = lod_instance_indices(instances)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Cache: already imported models (name -> list of created objects)
            imported_models = {}

            for idx, inst in enumerate(instances):
                wm.progress_update(idx)
                model_name = inst.model_name
                is_lod = idx in lod_refs or is_lod_name(model_name)

                # Skip LOD models if option enabled
                if skip_lod and is_lod:
                    skipped_count += 1
                    continue

                # Choose target collection
                target_collection = lod_collection if is_lod else dff_collection

                dff_filename = model_name + '.dff'

                # Check if DFF exists in IMG
                if dff_filename.lower() not in img_files:
                    skipped_count += 1
                    continue

                # Import DFF (or duplicate if already imported)
                if model_name in imported_models:
                    # Duplicate existing objects
                    new_objects = []
                    for src_obj in imported_models[model_name]:
                        new_obj = src_obj.copy()
                        new_obj.data = src_obj.data  # linked duplicate
                        target_collection.objects.link(new_obj)
                        new_objects.append(new_obj)
                else:
                    # Extract and import DFF
                    dff_data = extract_file(img_path, img_files[dff_filename.lower()])
                    if not dff_data:
                        errors.append(f"{model_name}: DFF extract failed")
                        continue

                    dff_path = os.path.join(tmpdir, dff_filename)
                    with open(dff_path, 'wb') as f:
                        f.write(dff_data)

                    try:
                        # Remember objects before import
                        before = set(context.scene.objects)
                        inu_import_dff(filepath=dff_path, context=context)
                        after = set(context.scene.objects)
                        new_objects = list(after - before)

                        # Load TXD if available
                        if load_txd:
                            # Get TXD name from IDE or use model name
                            txd_name = model_name
                            if inst.model_id in ide_models:
                                txd_name = ide_models[inst.model_id].txd_name

                            txd_filename = txd_name + '.txd'
                            if txd_filename.lower() in img_files:
                                txd_data = extract_file(img_path, img_files[txd_filename.lower()])
                                if txd_data:
                                    txd_path = os.path.join(tmpdir, txd_filename)
                                    with open(txd_path, 'wb') as f:
                                        f.write(txd_data)
                                    try:
                                        inu_import_txd(filepath=txd_path)
                                    except:
                                        pass

                        # Move imported objects to target collection
                        for obj in new_objects:
                            # Remove from all current collections
                            for c in list(obj.users_collection):
                                c.objects.unlink(obj)
                            target_collection.objects.link(obj)

                        # Import COL if available
                        col_filename = model_name + '.col'
                        if col_filename.lower() in img_files:
                            col_data = extract_file(img_path, img_files[col_filename.lower()])
                            if col_data:
                                col_path = os.path.join(tmpdir, col_filename)
                                with open(col_path, 'wb') as f:
                                    f.write(col_data)
                                try:
                                    from .ops.col_import import import_col as inu_import_col
                                    before_col = set(context.scene.objects)
                                    inu_import_col(filepath=col_path, context=context)
                                    after_col = set(context.scene.objects)
                                    col_objects = list(after_col - before_col)
                                    col_pos = (inst.pos_x, inst.pos_y, inst.pos_z)
                                    col_rot = Quaternion((inst.rot_w, inst.rot_x, inst.rot_y, inst.rot_z)).conjugated()
                                    _sfx_col = getattr(scene, 'gtatools_suffix_col', '_COL')
                                    _pfx_col = getattr(scene, 'gtatools_prefix_col', '')
                                    for co in col_objects:
                                        for c in list(co.users_collection):
                                            c.objects.unlink(co)
                                        col_collection.objects.link(co)
                                        co.location = col_pos
                                        co.rotation_mode = 'QUATERNION'
                                        co.rotation_quaternion = col_rot
                                        # Rename COL
                                        from .core.ipl import strip_lod_marker
                                        base_col = strip_lod_marker(model_name)
                                        if _sfx_col:
                                            co.name = base_col + _sfx_col
                                        elif _pfx_col:
                                            co.name = _pfx_col + base_col
                                except:
                                    pass

                        imported_models[model_name] = new_objects
                    except Exception as e:
                        errors.append(f"{model_name}: {str(e)}")
                        continue

                # Rename objects: add suffixes, convert LOD prefix
                _sfx_dff = getattr(scene, 'gtatools_suffix_dff', '_DFF')
                _sfx_lod = getattr(scene, 'gtatools_suffix_lod', '_LOD')
                _pfx_dff = getattr(scene, 'gtatools_prefix_dff', '')
                _pfx_lod = getattr(scene, 'gtatools_prefix_lod', '')
                for obj in new_objects:
                    if obj.type == 'MESH':
                        base = obj.name
                        # Remove .dff extension if present
                        if '.dff' in base.lower():
                            base = base.split('.dff')[0]
                        # Remove Blender numeric suffix (.001, .002)
                        if '.' in base:
                            b, s = base.rsplit('.', 1)
                            if s.isdigit():
                                base = b
                        # Remove _0, _1 etc (multiple atomics in DFF)
                        if '_' in base:
                            b, s = base.rsplit('_', 1)
                            if s.isdigit():
                                base = b

                        if is_lod:
                            # Strip any LOD marker (prefix/suffix/no-sep) and
                            # rebuild the name using the user-configured
                            # LOD suffix or prefix.
                            from .core.ipl import strip_lod_marker
                            base = strip_lod_marker(base)
                            if _sfx_lod:
                                obj.name = base + _sfx_lod
                            elif _pfx_lod:
                                obj.name = _pfx_lod + base
                        else:
                            if _sfx_dff:
                                obj.name = base + _sfx_dff
                            elif _pfx_dff:
                                obj.name = _pfx_dff + base

                # Position and rotate according to IPL
                pos = (inst.pos_x, inst.pos_y, inst.pos_z)
                # GTA SA quaternion is stored conjugated
                rot = Quaternion((inst.rot_w, inst.rot_x, inst.rot_y, inst.rot_z)).conjugated()

                for obj in new_objects:
                    if obj.type == 'MESH':
                        obj.location = pos
                        obj.rotation_mode = 'QUATERNION'
                        obj.rotation_quaternion = rot
                        # Set IDE properties
                        if hasattr(obj, 'inu'):
                            obj.inu.model_id = inst.model_id
                            if inst.model_id in ide_models:
                                ide_obj = ide_models[inst.model_id]
                                obj.inu.draw_distance = ide_obj.draw_distance
                                obj.inu.ide_flags = ide_obj.flags
                                obj.inu.txd_name = ide_obj.txd_name

                imported_count += 1

        wm.progress_end()

        msg = f"{T('Импортировано:')} {imported_count}"
        if skipped_count:
            msg += f", {T('пропущено:')} {skipped_count}"
        if errors:
            msg += f", {T('ошибок:')} {len(errors)}"
            for e in errors[:5]:
                print(f"[Map Import] {e}")
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_remove_from_img(bpy.types.Operator):
    """Удалить DFF/TXD/COL выделенных моделей из IMG архива"""
    bl_idname = "gtatools.remove_from_img"
    bl_label = "Remove from IMG"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .core.img import remove_file
        from .tools.model_utils import get_model_type

        img_path = bpy.path.abspath(context.scene.gtatools_img_path)
        if not img_path or not os.path.isfile(img_path):
            self.report({'ERROR'}, T("Укажите путь к .img архиву"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        removed = []
        for obj in objs:
            mt, base = get_model_type(obj)
            if not base:
                continue

            if mt == 'DFF':
                if remove_file(img_path, base + '.dff'):
                    removed.append(base + '.dff')
                if remove_file(img_path, base + '.txd'):
                    removed.append(base + '.txd')
            elif mt == 'LOD':
                fname = 'LOD' + base + '.dff'
                if remove_file(img_path, fname):
                    removed.append(fname)
            elif mt == 'COL':
                if remove_file(img_path, base + '.col'):
                    removed.append(base + '.col')

        if removed:
            # Refresh IMG file list
            _refresh_img_entries(context.scene, img_path)
            self.report({'INFO'}, f"IMG: {T('удалено')} {', '.join(removed)}")
        else:
            self.report({'WARNING'}, T("Файлы не найдены в IMG"))
        return {'FINISHED'}


class GTATOOLS_OT_export_to_img(bpy.types.Operator):
    """Экспортировать DFF + TXD + COL прямо в .img архив"""
    bl_idname = "gtatools.export_to_img"
    bl_label = "Export to IMG"
    bl_options = {'REGISTER'}

    def execute(self, context):
        import tempfile
        from .core.img import replace_or_add
        from .ops.dff_export import export_dff as inu_export_dff
        from .ops.col_export import export_col as inu_export_col

        img_path = bpy.path.abspath(context.scene.gtatools_img_path)
        if not img_path or not os.path.isfile(img_path):
            self.report({'ERROR'}, T("Укажите путь к .img архиву"))
            return {'CANCELLED'}

        # Find all model groups among selected
        model_groups = find_all_selected_model_groups()
        if not model_groups:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        export_dff_flag = getattr(context.scene, 'gtatools_img_export_dff', True)
        export_col_flag = getattr(context.scene, 'gtatools_img_export_col', True)
        export_txd_flag = getattr(context.scene, 'gtatools_img_export_txd', True)
        use_gpu = check_nvtt_available(getattr(context.scene, 'gtatools_nvtt_path', ''))[0]

        results = []

        with tempfile.TemporaryDirectory() as tmpdir:
            for base_name, models in model_groups.items():
                # Export LOD first
                if export_dff_flag and models['LOD']:
                    lod_name = 'LOD' + base_name
                    lod_path = os.path.join(tmpdir, lod_name + '.dff')
                    try:
                        inu_export_dff(filepath=lod_path, objects=[models['LOD']])
                        with open(lod_path, 'rb') as f:
                            status = replace_or_add(img_path, lod_name + '.dff', f.read())
                        results.append(f"{lod_name}.dff {status}")
                    except Exception as e:
                        results.append(f"{lod_name}.dff error: {e}")

                # Export DFF + attached 2DFX
                if export_dff_flag and models['DFF']:
                    dff_path = os.path.join(tmpdir, base_name + '.dff')
                    try:
                        dff_objs = [models['DFF']]
                        for child in models['DFF'].children:
                            if child.type == 'EMPTY' and getattr(child, 'inu', None) and child.inu.type == '2DFX':
                                dff_objs.append(child)
                        inu_export_dff(filepath=dff_path, objects=dff_objs)
                        with open(dff_path, 'rb') as f:
                            status = replace_or_add(img_path, base_name + '.dff', f.read())
                        results.append(f"{base_name}.dff {status}")
                    except Exception as e:
                        results.append(f"{base_name}.dff error: {e}")

                # Export COL
                if export_col_flag and models['COL']:
                    col_path = os.path.join(tmpdir, base_name + '.col')
                    try:
                        inu_export_col(filepath=col_path, objects=[models['COL']], version=3)
                        with open(col_path, 'rb') as f:
                            status = replace_or_add(img_path, base_name + '.col', f.read())
                        results.append(f"{base_name}.col {status}")
                    except Exception as e:
                        results.append(f"{base_name}.col error: {e}")

                # Export TXD (textures from DFF + LOD)
                if export_txd_flag and (models['DFF'] or models['LOD']):
                    txd_path = os.path.join(tmpdir, base_name + '.txd')
                    try:
                        # Select only this group's objects for texture collection
                        bpy.ops.object.select_all(action='DESELECT')
                        if models['DFF']:
                            models['DFF'].select_set(True)
                            context.view_layer.objects.active = models['DFF']
                        if models['LOD']:
                            models['LOD'].select_set(True)
                        result, msg, _ = export_txd(txd_path, context, True, use_gpu)
                        if result == {'FINISHED'}:
                            with open(txd_path, 'rb') as f:
                                status = replace_or_add(img_path, base_name + '.txd', f.read())
                            results.append(f"{base_name}.txd {status}")
                        else:
                            results.append(f"{base_name}.txd: {msg}")
                    except Exception as e:
                        results.append(f"{base_name}.txd error: {e}")

        # Refresh IMG file list
        _refresh_img_entries(context.scene, img_path)
        self.report({'INFO'}, f"IMG: {', '.join(results)}")
        return {'FINISHED'}


class GTATOOLS_OT_upsert_ide(bpy.types.Operator):
    """Добавить / обновить запись в существующем IDE файле (авто-LOD)"""
    bl_idname = "gtatools.upsert_ide"
    bl_label = "Add to IDE"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .core.ide import upsert_ide
        filepath = bpy.path.abspath(context.scene.gtatools_ide_path)
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
                entries.append(_ide_entry_from_obj(dff_obj))
            if lod_obj:
                lod_entry = _ide_entry_from_obj(lod_obj)
                # LOD model name: LOD + base_name
                lod_entry.model_name = "LOD" + base_name
                # LOD TXD = same as DFF TXD (base_name without suffixes)
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
    bl_label = "Add to IPL"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .core.ipl import upsert_ipl, read_ipl
        filepath = bpy.path.abspath(context.scene.gtatools_ipl_path)
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
                dff_entry = _ipl_entry_from_obj(pair['DFF'])
                dff_idx = entry_index
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
    bl_label = "Remove from IDE"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .core.ide import remove_ide
        filepath = bpy.path.abspath(context.scene.gtatools_ide_path)
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
    bl_label = "Remove from IPL"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .core.ipl import remove_ipl
        filepath = bpy.path.abspath(context.scene.gtatools_ipl_path)
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


class GTATOOLS_OT_export_ide(bpy.types.Operator):
    """Экспорт IDE (определение объектов GTA SA)"""
    bl_idname = "gtatools.export_ide"
    bl_label = "Export IDE (.ide)"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ide", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "model.ide"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.ide_export import export_ide as inu_export_ide
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
    bl_label = "Export IPL (.ipl)"
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
        icon_id = _icons.get_icon("disk")
        if icon_id:
            row.prop(self, "binary", icon_value=icon_id)
        else:
            row.prop(self, "binary")

    def execute(self, context):
        from .ops.ipl_export import export_ipl as inu_export_ipl
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
    bl_label = "Import IPL Sections"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .core.ipl import read_ipl
        from .ops.ipl_sections import import_ipl_sections
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
    bl_label = "Export IPL Sections"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "sections.ipl"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .core.ipl import IplFile, write_ipl
        from .ops.ipl_sections import export_ipl_sections
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
            write_ipl(self.filepath, ipl)
            total = sum(len(v) for v in sections.values())
            self.report({'INFO'}, f"Exported {total} IPL section entries")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL sections export: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_ide(bpy.types.Operator):
    """Импорт IDE (определения объектов GTA SA)"""
    bl_idname = "gtatools.import_ide"
    bl_label = "Import IDE (.ide)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ide", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.ide_import import import_ide as inu_import_ide
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
    bl_label = "Import IPL (.ipl)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.ipl_import import import_ipl as inu_import_ipl
        try:
            placed = inu_import_ipl(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"IPL: {len(placed)} objects placed")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_replace_ipl_placeholders(bpy.types.Operator):
    """Заменить IPL Empty-плейсхолдеры на модели из сцены"""
    bl_idname = "gtatools.replace_ipl_placeholders"
    bl_label = "Replace IPL Placeholders"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        replaced = 0
        # Build lookup from scene meshes
        mesh_lookup = {}
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
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
            from .core.ipl import is_lod_name, strip_lod_marker
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


def _clean_name_typed_ipl(name):
    from .tools.model_utils import get_model_type
    class _Mock:
        def __init__(self, n):
            self.name = n
    mt, base = get_model_type(_Mock(name))
    return base, mt or 'OTHER'


class GTATOOLS_OT_inu_import(bpy.types.Operator, ImportHelper):
    """Импорт GTA SA файлов (.dff/.col/.txd/.ide/.ipl) с авто-определением формата"""
    bl_idname = "gtatools.inu_import"
    bl_label = "INU Import"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    filename_ext = ".dff"
    filter_glob: StringProperty(
        default="*.dff;*.col;*.txd;*.ide;*.ipl",
        options={'HIDDEN'}
    )
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        from .ops.dff_import import import_dff as inu_import_dff
        from .ops.col_import import import_col as inu_import_col
        from .ops.txd_import import import_txd as inu_import_txd
        from .ops.ide_import import import_ide as inu_import_ide
        from .ops.ipl_import import import_ipl as inu_import_ipl

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
                    if getattr(context.scene, 'gtatools_txd_auto_import', True):
                        dff_name = os.path.splitext(fname)[0]
                        custom_dir = getattr(context.scene, 'gtatools_txd_import_path', '')
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
    bl_label = "Export All (DFF+COL+LOD+TXD)"
    bl_options = {'REGISTER'}

    directory: StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def export_model_group(self, context, base_name, models, skip_dff, skip_col, skip_lod, skip_txd, use_gpu):
        """Export a single model group (DFF + LOD + COL + TXD)"""
        exported = []
        errors = []

        # Экспорт DFF (версия GTA SA)
        if models['DFF'] and not skip_dff:
            dff_path = os.path.join(self.directory, f"{base_name}.dff")
            try:
                from .ops.dff_export import export_dff as inu_export_dff
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
                from .ops.dff_export import export_dff as inu_export_dff
                inu_export_dff(filepath=lod_path, objects=[models['LOD']])
                exported.append(f"LOD{base_name}.dff")
            except Exception as e:
                errors.append(f"LOD{base_name}.dff: {str(e)}")

        # Экспорт COL (версия GTA SA COL3)
        if models['COL'] and not skip_col:
            col_path = os.path.join(self.directory, f"{base_name}.col")
            try:
                from .ops.col_export import export_col as inu_export_col

                # COL всегда экспортируется в центре (0,0,0)
                original_col_loc = models['COL'].location.copy()
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

        # Экспорт TXD (текстуры из DFF + LOD в один архив)
        if (models['DFF'] or models['LOD']) and not skip_txd:
            txd_path = os.path.join(self.directory, f"{base_name}.txd")
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
                result, message, _ = export_txd(txd_path, context, selected_only=True, use_gpu=use_gpu)
                if result == {'FINISHED'}:
                    exported.append(f"{base_name}.txd")
                else:
                    errors.append(f"{base_name}.txd: {message}")
            except Exception as e:
                errors.append(f"{base_name}.txd: {str(e)}")

        return exported, errors

    def execute(self, context):
        # Ищем все группы моделей среди выделенных
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
                        setup_prelight_preview(obj, enable=False)

        all_exported = []
        all_errors = []
        wm = context.window_manager

        # Настройки экспорта
        skip_dff = not context.scene.gtatools_export_all_dff
        skip_col = not context.scene.gtatools_export_all_col
        skip_lod = not context.scene.gtatools_export_all_lod
        skip_txd = not context.scene.gtatools_export_all_txd
        use_gpu = check_nvtt_available(getattr(context.scene, 'gtatools_nvtt_path', ''))[0]

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

        # Экспортируем каждую группу моделей
        for base_name, models in model_groups.items():
            wm.progress_update(current_step)
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

        wm.progress_end()

        # Восстанавливаем prelight только где он был включён
        for obj in prelight_was_on:
            setup_prelight_preview(obj, enable=True)

        # Result
        num_groups = len(model_groups)
        if all_exported:
            self.report({'INFO'}, f"{T('Экспортировано:')} {len(all_exported)} файлов ({num_groups} моделей)")
        if all_errors:
            self.report({'WARNING'}, f"{T('Ошибки:')} {'; '.join(all_errors)}")

        return {'FINISHED'}


class GTATOOLS_OT_inu_export(bpy.types.Operator, ExportHelper):
    """Единый экспорт INU — DFF, COL, TXD, IDE, IPL в одну папку"""
    bl_idname = "gtatools.inu_export"
    bl_label = "INU Export"
    bl_options = {'REGISTER', 'PRESET'}

    filename_ext = ""
    use_filter_folder = True

    # ── Format checkboxes ──
    export_dff: BoolProperty(name="DFF", default=True, description="Export DFF models")
    export_col: BoolProperty(name="COL", default=True, description="Export COL collision")
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
        box.label(text=T("Формат:"), icon='EXPORT')
        col = box.column(align=True)
        col.prop(self, "export_dff")
        col.prop(self, "export_col")
        col.prop(self, "export_txd")
        col.prop(self, "export_ide")
        col.prop(self, "export_ipl")

        # Source
        box = layout.box()
        box.label(text=T("Источник:"), icon='OBJECT_DATA')
        box.prop(self, "source", text="")

        # DFF settings
        if self.export_dff:
            box = layout.box()
            box.label(text="DFF:", icon='MESH_DATA')
            box.prop(self, "dff_include_2dfx")
            box.prop(self, "dff_auto_lod")
            # Pipeline
            box.prop(context.scene, "gtatools_export_pipeline", text="Pipeline")

        # TXD settings
        if self.export_txd:
            box = layout.box()
            box.label(text="TXD:", icon='IMAGE_DATA')
            box.prop(self, "txd_selected_only")
            nvtt_path = getattr(context.scene, 'gtatools_nvtt_path', '')
            available, _ = check_nvtt_available(nvtt_path)
            if available:
                box.label(text="GPU (NVTT)", icon='CHECKMARK')
            else:
                box.label(text="CPU", icon='INFO')

        # IDE/IPL settings
        if self.export_ide or self.export_ipl:
            box = layout.box()
            box.label(text="IDE / IPL:", icon='TEXT')
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
                            setup_prelight_preview(obj, enable=False)
                            break

        all_exported = []
        all_errors = []
        use_gpu = check_nvtt_available(getattr(context.scene, 'gtatools_nvtt_path', ''))[0]

        wm = context.window_manager
        wm.progress_begin(0, len(groups))

        for idx, (base_name, models) in enumerate(groups.items()):
            wm.progress_update(idx)

            # ── DFF ──
            if self.export_dff and models['DFF']:
                dff_path = os.path.join(directory, f"{base_name}.dff")
                try:
                    from .ops.dff_export import export_dff as inu_export_dff
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
                    from .ops.dff_export import export_dff as inu_export_dff
                    inu_export_dff(filepath=lod_path, objects=[models['LOD']])
                    all_exported.append(f"LOD{base_name}.dff")
                except Exception as e:
                    all_errors.append(f"LOD{base_name}.dff: {e}")

            # ── COL ──
            if self.export_col and models['COL']:
                col_path = os.path.join(directory, f"{base_name}.col")
                try:
                    from .ops.col_export import export_col as inu_export_col
                    original_loc = models['COL'].location.copy()
                    models['COL'].location = (0, 0, 0)
                    inu_export_col(filepath=col_path, objects=[models['COL']], version=3, model_name=base_name)
                    models['COL'].location = original_loc
                    all_exported.append(f"{base_name}.col")
                except Exception as e:
                    all_errors.append(f"{base_name}.col: {e}")

            # ── TXD ──
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
                    from .core.ide import upsert_ide
                    entries = []
                    for base_name, models in groups.items():
                        if models['DFF']:
                            entries.append(_ide_entry_from_obj(models['DFF']))
                        if models['LOD']:
                            lod_entry = _ide_entry_from_obj(models['LOD'])
                            lod_entry.model_name = "LOD" + base_name
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
                    from .ops.ide_export import export_ide as inu_export_ide
                    inu_export_ide(filepath=ide_path, objects=mesh_objects)
                    all_exported.append("objects.ide")
                except Exception as e:
                    all_errors.append(f"IDE: {e}")

        # ── IPL ──
        if self.export_ipl:
            if self.ide_ipl_upsert and self.ipl_upsert_path:
                try:
                    from .core.ipl import upsert_ipl
                    entries = []
                    for base_name, models in groups.items():
                        if models['DFF']:
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
                    from .ops.ipl_export import export_ipl as inu_export_ipl
                    inu_export_ipl(filepath=ipl_path, objects=mesh_objects)
                    all_exported.append("objects.ipl")
                except Exception as e:
                    all_errors.append(f"IPL: {e}")

        wm.progress_end()

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


class GTATOOLS_OT_info_tooltip(bpy.types.Operator):
    """"""
    bl_idname = "gtatools.info_tooltip"
    bl_label = ""
    bl_options = {'INTERNAL'}

    tooltip : StringProperty(default="")

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        return {'CANCELLED'}


def _draw_label_with_info(layout, text, tooltip, icon='NONE'):
    """Draw info icon before label text."""
    row = layout.row(align=True)
    sub = row.row(align=True)
    sub.ui_units_x = 1.3
    op = sub.operator("gtatools.info_tooltip", text="", icon='INFO')
    op.tooltip = tooltip
    row.label(text=text, icon=icon)


class GTATOOLS_OT_detect_models(bpy.types.Operator):
    """Определить модели DFF, LOD, COL среди выделенных"""
    bl_idname = "gtatools.detect_models"
    bl_label = "Detect Models"
    bl_options = {'REGISTER'}

    def execute(self, context):
        models = find_selected_models()

        found = []
        if models['DFF']:
            found.append(f"DFF: {models['DFF'].name}")
        if models['LOD']:
            found.append(f"LOD: {models['LOD'].name}")
        if models['COL']:
            found.append(f"COL: {models['COL'].name}")

        if found:
            self.report({'INFO'}, f"{T('Найдено:')} {', '.join(found)}")
        else:
            self.report({'WARNING'}, T("Среди выделенных не найдено DFF/LOD/COL моделей"))

        return {'FINISHED'}


class GTATOOLS_OT_prelight(bpy.types.Operator):
    """Применить GTA SA Prelight к выделенному объекту"""
    bl_idname = "gtatools.prelight"
    bl_label = "Apply Prelight"
    bl_options = {'REGISTER', 'UNDO'}

    split_angle: FloatProperty(name="Split Angle", default=90.0, min=0.0, max=180.0)
    normal_threshold: FloatProperty(name="Normal Threshold", default=0.15, min=0.001, max=0.5)
    top_color: FloatVectorProperty(name="Top Color", subtype='COLOR', default=(1.0, 1.0, 1.0), min=0.0, max=1.0)
    bottom_color: FloatVectorProperty(name="Bottom Color", subtype='COLOR', default=(0.25, 0.25, 0.25), min=0.0, max=1.0)
    ambient_color: FloatVectorProperty(name="Ambient Color", subtype='COLOR', default=(0.5, 0.5, 0.5), min=0.0, max=1.0)

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        if not mesh_objects:
            self.report({'ERROR'}, "Select mesh object(s)!")
            return {'CANCELLED'}

        count = 0
        for obj in mesh_objects:
            prelight = GTASAPrelight(
                obj,
                split_angle=self.split_angle,
                normal_threshold=self.normal_threshold,
                top_color=tuple(self.top_color),
                bottom_color=tuple(self.bottom_color),
                ambient_color=tuple(self.ambient_color)
            )
            prelight.run()
            count += 1

        self.report({'INFO'}, f"Prelight applied: {count} objects")
        return {'FINISHED'}


class GTATOOLS_OT_average_colors(bpy.types.Operator):
    """Усреднить vertex colors для компланарных граней"""
    bl_idname = "gtatools.average_colors"
    bl_label = "Average Colors"
    bl_options = {'REGISTER', 'UNDO'}

    normal_threshold: FloatProperty(
        name="Normal Threshold",
        default=0.01,
        min=0.001,
        max=0.5
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        if not mesh_objects:
            self.report({'ERROR'}, "Select mesh object(s)!")
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        count = 0
        for obj in mesh_objects:
            success = average_colors_on_coplanar_faces(obj, self.normal_threshold)
            if success:
                count += 1

        if count:
            self.report({'INFO'}, f"Colors averaged: {count} objects")
        else:
            self.report({'ERROR'}, "Failed to average colors!")
            return {'CANCELLED'}

        return {'FINISHED'}


class GTATOOLS_OT_lightmap_generate(bpy.types.Operator):
    """Сгенерировать код lightmap для выделенного объекта"""
    bl_idname = "gtatools.lightmap_generate"
    bl_label = "Generate Lightmap Code"

    def execute(self, context):
        scene = context.scene
        obj = context.active_object

        if not obj:
            self.report({'WARNING'}, "No object selected")
            scene.gtatools_lightmap_result = "Error: no object selected"
            return {'CANCELLED'}

        textures = self.get_textures_from_object(obj)

        if not textures:
            self.report({'WARNING'}, "No textures found")
            scene.gtatools_lightmap_result = "Error: no textures found"
            return {'CANCELLED'}

        lightmap_path = scene.gtatools_lightmap_path if scene.gtatools_lightmap_path else "lightmaps/lightmap.png"
        model_id = scene.gtatools_model_id if scene.gtatools_model_id else "0"

        code = self.generate_code(textures, lightmap_path, model_id)
        scene.gtatools_lightmap_result = code

        self.report({'INFO'}, f"Found {len(textures)} textures")
        return {'FINISHED'}

    def get_textures_from_object(self, obj):
        textures = []
        if not obj.data or not hasattr(obj.data, 'materials'):
            return textures

        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue

            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    tex_name = os.path.splitext(node.image.name)[0]
                    if tex_name not in textures:
                        textures.append(tex_name)

        return textures

    def generate_code(self, textures, lightmap_path, model_id):
        lines = []
        lines.append("    {")
        lines.append("        textures = {")
        for tex in textures:
            lines.append(f'            "{tex}",')
        lines.append("        },")
        lines.append(f'        lightmap = "{lightmap_path}",')
        lines.append(f"        models = {{{model_id}}}")
        lines.append("    },")
        return '\n'.join(lines)


class GTATOOLS_OT_lightmap_copy(bpy.types.Operator):
    """Копировать результат в буфер обмена"""
    bl_idname = "gtatools.lightmap_copy"
    bl_label = "Copy to Clipboard"

    def execute(self, context):
        scene = context.scene
        if scene.gtatools_lightmap_result:
            context.window_manager.clipboard = scene.gtatools_lightmap_result
            self.report({'INFO'}, "Copied to clipboard")
        return {'FINISHED'}


class GTATOOLS_OT_lightmap_clear(bpy.types.Operator):
    """Очистить сгенерированный код"""
    bl_idname = "gtatools.lightmap_clear"
    bl_label = "Clear"

    def execute(self, context):
        context.scene.gtatools_lightmap_result = ""
        self.report({'INFO'}, T("Код очищен"))
        return {'FINISHED'}


class GTATOOLS_OT_create_prelight_lights(bpy.types.Operator):
    """Создать 8 источников света для запекания prelight вокруг объекта"""
    bl_idname = "gtatools.create_prelight_lights"
    bl_label = "Create Prelight Lights"
    bl_options = {'REGISTER', 'UNDO'}

    distance: FloatProperty(
        name="Distance",
        description=T("Расстояние ламп от центра"),
        default=100.0,
        min=1.0,
        max=1000.0
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'ERROR'}, "Select an object!")
            return {'CANCELLED'}

        # Get object center (bounding box center in world space)
        bbox_center = sum((Vector(b) for b in obj.bound_box), Vector()) / 8
        world_center = obj.matrix_world @ bbox_center

        lights = create_prelight_scene_lights(world_center, self.distance)
        self.report({'INFO'}, f"Created {len(lights)} lights around {obj.name}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_prelight_lights(bpy.types.Operator):
    """Удалить все источники света prelight"""
    bl_idname = "gtatools.remove_prelight_lights"
    bl_label = "Remove Prelight Lights"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if remove_prelight_scene_lights():
            self.report({'INFO'}, "Prelight lights removed")
        else:
            self.report({'WARNING'}, "No prelight lights found")
        return {'FINISHED'}


class GTATOOLS_OT_bake_vertex_colors(bpy.types.Operator):
    """Запечь освещение от Point источников в vertex colors"""
    bl_idname = "gtatools.bake_vertex_colors"
    bl_label = "Bake Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    use_shadows: BoolProperty(
        name="Use Shadows",
        description=T("Рассчитать тени (медленнее, но точнее)"),
        default=False
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        baked = 0
        for obj in mesh_objects:
            success, message = bake_vertex_colors_from_lights(obj, self.use_shadows)
            if success:
                if obj.data.color_attributes.active_color:
                    prop_name = f"v_offset_{obj.data.color_attributes.active_color.name}"
                    obj[prop_name] = 0.0
                baked += 1

        if baked:
            self.report({'INFO'}, f"Baked from lights: {baked} objects")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, T("Нет vertex colors"))
            return {'CANCELLED'}


class GTATOOLS_OT_bake_vertex_colors_simple(bpy.types.Operator):
    """Быстрое запекание vertex colors от Point источников (без теней)"""
    bl_idname = "gtatools.bake_vertex_colors_simple"
    bl_label = "Bake Vertex Colors (Fast)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        # Get settings from panel
        ambient = scene.gtatools_bake_ambient
        intensity = scene.gtatools_bake_intensity
        gamma = scene.gtatools_bake_gamma
        use_shadows = scene.gtatools_bake_shadows

        baked = 0
        for obj in mesh_objects:
            success, message = bake_vertex_colors_simple(obj, ambient, intensity, gamma, use_shadows)
            if success:
                if obj.data.color_attributes.active_color:
                    prop_name = f"v_offset_{obj.data.color_attributes.active_color.name}"
                    obj[prop_name] = 0.0
                baked += 1

        if baked:
            attr_name = mesh_objects[0].data.color_attributes.active_color.name if mesh_objects[0].data.color_attributes.active_color else "?"
            self.report({'INFO'}, f"Baked to '{attr_name}' from {baked} objects")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, T("Нет vertex colors"))
            return {'CANCELLED'}


class GTATOOLS_OT_reset_bake_settings(bpy.types.Operator):
    """Сбросить настройки запекания по умолчанию"""
    bl_idname = "gtatools.reset_bake_settings"
    bl_label = "Reset to Default"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.gtatools_bake_ambient = 0.10
        scene.gtatools_bake_intensity = 0.05
        scene.gtatools_bake_gamma = 0.50
        self.report({'INFO'}, T("Настройки сброшены по умолчанию"))
        return {'FINISHED'}


class GTATOOLS_OT_reset_scatter_settings(bpy.types.Operator):
    """Сбросить настройки Scatter Light по умолчанию"""
    bl_idname = "gtatools.reset_scatter_settings"
    bl_label = "Reset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.gtatools_scatter_intensity = 1.0
        scene.gtatools_scatter_falloff = 1.5
        scene.gtatools_scatter_iterations = 3
        scene.gtatools_scatter_radius = 0.0
        self.report({'INFO'}, "Scatter settings reset")
        return {'FINISHED'}


class GTATOOLS_OT_analyze_vertex_colors(bpy.types.Operator):
    """Анализировать vertex colors выделенного объекта"""
    bl_idname = "gtatools.analyze_vertex_colors"
    bl_label = "Analyze Colors"

    def execute(self, context):
        obj = context.active_object
        result = analyze_vertex_colors(obj)

        if result is None:
            self.report({'WARNING'}, "No vertex colors found!")
            return {'CANCELLED'}

        # Store result in scene for display
        scene = context.scene
        scene.gtatools_vc_analysis = (
            f"Layer: {result['layer_name']}\n"
            f"Vertices: {result['count']}\n"
            f"Min: {result['min_brightness']:.3f}\n"
            f"Max: {result['max_brightness']:.3f}\n"
            f"Avg: {result['avg_brightness']:.3f}"
        )

        self.report({'INFO'}, f"Avg brightness: {result['avg_brightness']:.3f}")
        return {'FINISHED'}


class GTATOOLS_OT_apply_v_offset(bpy.types.Operator):
    """Применить смещение яркости (V) к vertex colors"""
    bl_idname = "gtatools.apply_v_offset"
    bl_label = "Apply V Offset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        v_offset = context.scene.gtatools_v_offset
        count = 0
        for obj in mesh_objects:
            success, _ = apply_brightness_offset(obj, v_offset)
            if success:
                count += 1
        self.report({'INFO'}, f"V Offset: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_smooth(bpy.types.Operator):
    """Сгладить vertex colors между соседними вершинами"""
    bl_idname = "gtatools.vc_smooth"
    bl_label = "Smooth Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        iterations = context.scene.gtatools_vc_smooth_iterations
        factor = context.scene.gtatools_vc_smooth_factor
        count = 0
        for obj in mesh_objects:
            success, _ = smooth_vertex_colors(obj, iterations, factor)
            if success:
                count += 1
        self.report({'INFO'}, f"Smooth: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_contrast(bpy.types.Operator):
    """Применить контраст к vertex colors"""
    bl_idname = "gtatools.vc_contrast"
    bl_label = "Apply Contrast"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        contrast = context.scene.gtatools_vc_contrast
        count = 0
        for obj in mesh_objects:
            success, _ = adjust_vertex_colors_contrast(obj, contrast)
            if success:
                count += 1
        self.report({'INFO'}, f"Contrast: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_brightness(bpy.types.Operator):
    """Применить яркость к vertex colors"""
    bl_idname = "gtatools.vc_brightness"
    bl_label = "Apply Brightness"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        brightness = context.scene.gtatools_vc_brightness
        count = 0
        for obj in mesh_objects:
            success, _ = adjust_vertex_colors_brightness(obj, brightness)
            if success:
                count += 1
        self.report({'INFO'}, f"Brightness: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_gamma(bpy.types.Operator):
    """Применить гамма-коррекцию к vertex colors"""
    bl_idname = "gtatools.vc_gamma"
    bl_label = "Apply Gamma"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        gamma = context.scene.gtatools_vc_gamma

        count = 0
        for obj in mesh_objects:
            success, _ = adjust_vertex_colors_gamma(obj, gamma)
            if success:
                count += 1
        self.report({'INFO'}, f"Gamma: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_smooth_between(bpy.types.Operator):
    """Сгладить vertex colors на стыках между выделенными объектами"""
    bl_idname = "gtatools.vc_smooth_between"
    bl_label = "Smooth Between Objects"
    bl_options = {'REGISTER', 'UNDO'}

    tolerance: FloatProperty(
        name="Tolerance",
        description=T("Максимальное расстояние между вершинами для сопоставления"),
        default=0.001,
        min=0.0001,
        max=1.0
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if len(mesh_objects) < 2:
            self.report({'ERROR'}, T("Выделите минимум 2 меш объекта"))
            return {'CANCELLED'}

        # Collect all boundary vertex data: (world_pos, obj, loop_indices, color_attr)
        from mathutils import kdtree

        all_points = []  # [(world_co, obj_index, vert_index)]
        obj_data = []    # [(obj, color_attr, {vert_idx: [loop_indices]})]

        for oi, obj in enumerate(mesh_objects):
            mesh = obj.data
            color_attr = mesh.color_attributes.active_color
            if color_attr is None:
                continue

            # Build vert -> loop indices map
            vert_loops = {}
            for poly in mesh.polygons:
                for vi, li in zip(poly.vertices, poly.loop_indices):
                    vert_loops.setdefault(vi, []).append(li)

            obj_data.append((obj, color_attr, vert_loops))

            mat_w = obj.matrix_world
            for vi, vert in enumerate(mesh.vertices):
                world_co = mat_w @ vert.co
                all_points.append((world_co, len(obj_data) - 1, vi))

        if not obj_data:
            self.report({'WARNING'}, T("Нет vertex colors"))
            return {'CANCELLED'}

        # Build KD-tree from all vertices
        kd = kdtree.KDTree(len(all_points))
        for i, (co, _, _) in enumerate(all_points):
            kd.insert(co, i)
        kd.balance()

        # Find matching vertices and average their colors
        processed = set()
        smoothed_count = 0
        tol = self.tolerance

        for i, (co, oi, vi) in enumerate(all_points):
            if i in processed:
                continue

            # Find all vertices at this position
            matches = kd.find_range(co, tol)
            if len(matches) < 2:
                continue

            # Check if matches span multiple objects
            match_indices = [idx for _, idx, _ in matches]
            obj_indices = set(all_points[idx][1] for idx in match_indices)
            if len(obj_indices) < 2:
                continue

            # Collect all colors from matching vertices
            colors = []
            match_data = []  # [(obj_data_index, loop_indices)]
            for idx in match_indices:
                _, m_oi, m_vi = all_points[idx]
                obj, color_attr, vert_loops = obj_data[m_oi]
                loops = vert_loops.get(m_vi, [])
                for li in loops:
                    c = color_attr.data[li].color
                    colors.append((c[0], c[1], c[2], c[3]))
                match_data.append((m_oi, loops))
                processed.add(idx)

            if not colors:
                continue

            # Average
            avg = [sum(c[ch] for c in colors) / len(colors) for ch in range(4)]

            # Apply averaged color back
            for m_oi, loops in match_data:
                _, color_attr, _ = obj_data[m_oi]
                for li in loops:
                    color_attr.data[li].color = avg

            smoothed_count += 1

        # Update meshes
        for obj, _, _ in obj_data:
            obj.data.update()

        self.report({'INFO'}, f"{T('Сглажено стыков:')} {smoothed_count}")
        return {'FINISHED'}


class GTATOOLS_OT_load_lightmap(bpy.types.Operator):
    """Загрузить Lightmap из папки с .blend файлом (текстуры с приставкой LP_)"""
    bl_idname = "gtatools.load_lightmap"
    bl_label = "Load Lightmap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        # Get path to .blend file
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({'ERROR'}, T("Сохраните .blend файл сначала!"))
            return {'CANCELLED'}

        blend_dir = os.path.dirname(blend_path)

        # Ищем текстуры с приставкой LP_
        lightmap_files = []
        supported_ext = ('.png', '.jpg', '.jpeg', '.tga', '.bmp', '.tif', '.tiff')

        for filename in os.listdir(blend_dir):
            if filename.upper().startswith('LP_') and filename.lower().endswith(supported_ext):
                lightmap_files.append(filename)

        if not lightmap_files:
            self.report({'ERROR'}, f"{T('Текстуры с приставкой LP_ не найдены в папке:')} {blend_dir}")
            return {'CANCELLED'}

        # Берём первую найденную текстуру
        lightmap_filename = lightmap_files[0]
        lightmap_path = os.path.join(blend_dir, lightmap_filename)

        # Загружаем текстуру
        lightmap_image = bpy.data.images.load(lightmap_path, check_existing=True)

        # Применяем лайтмап ко всем материалам объекта
        applied_count = 0
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Находим Principled BSDF
            principled = None
            for node in nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled = node
                    break

            if not principled:
                continue

            # Проверяем есть ли уже лайтмап нода
            existing_lm = nodes.get("Lightmap_Texture")
            if existing_lm:
                # Обновляем текстуру
                existing_lm.image = lightmap_image
                applied_count += 1
                continue

            # Находим что подключено к Base Color
            base_color_input = principled.inputs['Base Color']
            original_link = None
            original_node = None
            prelight_mix = nodes.get("Prelight_Mix")

            if base_color_input.links:
                original_link = base_color_input.links[0]
                original_node = original_link.from_node
                original_socket = original_link.from_socket

                # Если подключен Prelight_Mix - ищем оригинальную текстуру в его входе A
                if original_node and original_node.name == "Prelight_Mix":
                    prelight_mix = original_node
                    prelight_a_input = prelight_mix.inputs.get('A')
                    if prelight_a_input and prelight_a_input.is_linked:
                        original_node = prelight_a_input.links[0].from_node
                        original_socket = prelight_a_input.links[0].from_socket
                    else:
                        original_node = None
                        original_socket = None

            # Создаём ноду UV Map для UV2
            uv_node = nodes.new('ShaderNodeUVMap')
            uv_node.name = "Lightmap_UV"
            uv_node.label = "UV2"
            # Ищем второй UV слой
            if len(obj.data.uv_layers) >= 2:
                uv_node.uv_map = obj.data.uv_layers[1].name
            elif len(obj.data.uv_layers) == 1:
                # Если только один UV - используем его
                uv_node.uv_map = obj.data.uv_layers[0].name

            # Создаём ноду текстуры для лайтмапа
            lm_tex = nodes.new('ShaderNodeTexImage')
            lm_tex.name = "Lightmap_Texture"
            lm_tex.label = "Lightmap"
            lm_tex.image = lightmap_image

            # Создаём ноду Mix (Multiply) — совместимость 4.4+
            if bpy.app.version >= (4, 0, 0):
                mix_node = nodes.new('ShaderNodeMix')
                mix_node.data_type = 'RGBA'
                mix_node.blend_type = 'MULTIPLY'
                mix_node.inputs['Factor'].default_value = 1.0
                _mix_in1, _mix_in2, _mix_out = 'A', 'B', 'Result'
            else:
                mix_node = nodes.new('ShaderNodeMixRGB')
                mix_node.blend_type = 'MULTIPLY'
                mix_node.inputs['Fac'].default_value = 1.0
                _mix_in1, _mix_in2, _mix_out = 'Color1', 'Color2', 'Color'
            mix_node.name = "Lightmap_Mix"
            mix_node.label = "Lightmap Mix"

            # Позиционируем ноды
            if original_node:
                uv_node.location = (original_node.location.x - 200, original_node.location.y - 300)
                lm_tex.location = (original_node.location.x, original_node.location.y - 300)
                mix_node.location = (original_node.location.x + 300, original_node.location.y - 150)
            else:
                uv_node.location = (principled.location.x - 700, principled.location.y - 200)
                lm_tex.location = (principled.location.x - 500, principled.location.y - 200)
                mix_node.location = (principled.location.x - 200, principled.location.y)

            # Подключаем UV2 к текстуре лайтмапа
            links.new(uv_node.outputs['UV'], lm_tex.inputs['Vector'])

            # Подключаем ноды
            if original_node:
                links.new(original_socket, mix_node.inputs[_mix_in1])
            else:
                mix_node.inputs[_mix_in1].default_value = (1, 1, 1, 1)

            links.new(lm_tex.outputs['Color'], mix_node.inputs[_mix_in2])

            if prelight_mix:
                links.new(mix_node.outputs[_mix_out], prelight_mix.inputs['A'])
            else:
                links.new(mix_node.outputs[_mix_out], base_color_input)

            applied_count += 1

        if applied_count > 0:
            self.report({'INFO'}, f"Lightmap '{lightmap_filename}' applied to {applied_count} material(s)")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, T("Не удалось применить лайтмап - нет подходящих материалов"))
            return {'CANCELLED'}


class GTATOOLS_OT_remove_lightmap(bpy.types.Operator):
    """Удалить Lightmap из материалов объекта"""
    bl_idname = "gtatools.remove_lightmap"
    bl_label = "Remove Lightmap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        removed_count = 0
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Find lightmap nodes
            lm_tex = nodes.get("Lightmap_Texture")
            lm_mix = nodes.get("Lightmap_Mix")
            lm_uv = nodes.get("Lightmap_UV")

            if not lm_mix:
                continue

            # Находим Principled BSDF
            principled = None
            for node in nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled = node
                    break

            if principled:
                # Восстанавливаем оригинальное подключение
                base_color_input = principled.inputs['Base Color']
                prelight_mix = nodes.get("Prelight_Mix")

                # Находим что было подключено к входу (оригинальная текстура)
                _in1 = 'A' if 'A' in lm_mix.inputs else 'Color1'
                original_socket = None
                if lm_mix.inputs[_in1].links:
                    original_link = lm_mix.inputs[_in1].links[0]
                    original_socket = original_link.from_socket

                # Удаляем связи с Mix нодой
                for link in list(links):
                    if link.to_node == lm_mix or link.from_node == lm_mix:
                        links.remove(link)

                # Восстанавливаем оригинальное подключение
                if original_socket:
                    if prelight_mix:
                        # Если есть Prelight_Mix - подключаем к его входу A
                        links.new(original_socket, prelight_mix.inputs['A'])
                    else:
                        # Иначе напрямую к Base Color
                        links.new(original_socket, base_color_input)

            # Удаляем ноды лайтмапа
            if lm_tex:
                nodes.remove(lm_tex)
            if lm_mix:
                nodes.remove(lm_mix)
            if lm_uv:
                nodes.remove(lm_uv)

            removed_count += 1

        if removed_count > 0:
            self.report({'INFO'}, f"Lightmap удалён из {removed_count} материал(ов)")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Lightmap не найден в материалах")
            return {'CANCELLED'}


class GTATOOLS_OT_create_day_night(bpy.types.Operator):
    """Создать Day и Night color attributes"""
    bl_idname = "gtatools.create_day_night"
    bl_label = "Create Day/Night"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "Select mesh object(s)!")
            return {'CANCELLED'}

        total_created = 0
        for obj in mesh_objects:
            mesh = obj.data

            # Create Day attribute if not exists
            if "Day" not in mesh.color_attributes:
                attr = mesh.color_attributes.new(name="Day", type='BYTE_COLOR', domain='CORNER')
                for i in range(len(attr.data)):
                    attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
                total_created += 1

            # Create Night attribute if not exists
            if "Night" not in mesh.color_attributes:
                attr = mesh.color_attributes.new(name="Night", type='BYTE_COLOR', domain='CORNER')
                for i in range(len(attr.data)):
                    attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
                total_created += 1

            # Set Day as active
            if "Day" in mesh.color_attributes:
                mesh.color_attributes.active_color = mesh.color_attributes["Day"]

        self.report({'INFO'}, f"Day/Night: {len(mesh_objects)} objects, {total_created} attributes created")
        return {'FINISHED'}


class GTATOOLS_OT_copy_color_attr(bpy.types.Operator):
    """Копировать vertex colors из одного атрибута в другой (Day ↔ Night)"""
    bl_idname = "gtatools.copy_color_attr"
    bl_label = "Copy Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    source: StringProperty(name="Source", default="Day")
    target: StringProperty(name="Target", default="Night")

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                mesh_objects = [obj]
        if not mesh_objects:
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        copied = 0
        for obj in mesh_objects:
            mesh = obj.data
            src_attr = mesh.color_attributes.get(self.source)
            if not src_attr:
                continue

            tgt_attr = mesh.color_attributes.get(self.target)
            if not tgt_attr:
                tgt_attr = mesh.color_attributes.new(
                    name=self.target, type='BYTE_COLOR', domain='CORNER')

            # Copy all colors
            n = min(len(src_attr.data), len(tgt_attr.data))
            for i in range(n):
                c = src_attr.data[i].color
                tgt_attr.data[i].color = (c[0], c[1], c[2], c[3])
            copied += 1

        self.report({'INFO'}, f"{self.source} → {self.target}: {copied} {T('объектов')}")
        return {'FINISHED'}


class GTATOOLS_OT_prelight_preview(bpy.types.Operator):
    """Переключить превью prelight - показать vertex colors с текстурами"""
    bl_idname = "gtatools.prelight_preview"
    bl_label = "Toggle Prelight Preview"
    bl_options = {'REGISTER', 'UNDO'}

    enable: BoolProperty(
        name="Enable",
        description=T("Включить или выключить превью prelight"),
        default=True
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            # Fallback to active object
            obj = context.active_object
            if obj and obj.type == 'MESH':
                mesh_objects = [obj]

        count = 0
        for obj in mesh_objects:
            success, message = setup_prelight_preview(obj, self.enable)
            if success:
                count += 1

        if count:
            state = "enabled" if self.enable else "disabled"
            self.report({'INFO'}, f"Prelight preview {state} on {count} materials")
            return {'FINISHED'}

        # Single object error
        obj = context.active_object
        success, message = setup_prelight_preview(obj, self.enable)
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_fix_itera_collection(bpy.types.Operator):
    """Исправить коллекцию освещения Itera Tools — сделать локальной и привязать к сцене"""
    bl_idname = "gtatools.fix_itera_collection"
    bl_label = "Fix Itera Light Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import bpy
        # Find all Itera collections (including .001, .002, etc.)
        itera_cols = [c for c in bpy.data.collections if c.name.startswith("Template Scene - Vertex Lights")]
        if not itera_cols:
            self.report({'WARNING'}, T("Коллекция 'Template Scene - Vertex Lights' не найдена"))
            return {'CANCELLED'}

        fixed = 0
        for col in itera_cols:
            if col.library:
                try:
                    col.make_local()
                    for obj in col.objects:
                        obj.make_local()
                except Exception:
                    bpy.ops.object.make_local(type='ALL')
                    col = bpy.data.collections.get(col.name)
                    if col is None:
                        continue

            if col.name not in context.scene.collection.children:
                context.scene.collection.children.link(col)
                fixed += 1

        self.report({'INFO'}, T("Коллекции Itera привязаны к сцене") + f": {fixed}")
        return {'FINISHED'}


def _find_itera_blend_path():
    """Find the Itera Tools 3 blend file from Blender asset libraries."""
    for lib in bpy.context.preferences.filepaths.asset_libraries:
        if "itera" in lib.name.lower() or "itera" in lib.path.lower():
            blend_path = os.path.join(lib.path, "Vertex Light 3.0.89.blend")
            if os.path.isfile(blend_path):
                return blend_path
            # Try to find any blend file with "Vertex Light" in name
            for f in os.listdir(lib.path):
                if f.startswith("Vertex Light") and f.endswith(".blend"):
                    return os.path.join(lib.path, f)
    return None


class GTATOOLS_OT_apply_itera_material(bpy.types.Operator):
    """Применить Itera материал из библиотеки к выделенным объектам"""
    bl_idname = "gtatools.apply_itera_material"
    bl_label = "Apply Itera Material"
    bl_options = {'REGISTER', 'UNDO'}

    preset: EnumProperty(
        name="Preset",
        items=[
            ('VERTEX_LIT_LINEAR', "Vertex Lit Linear UV",
             T("Линейное освещение вершин с UV текстурой")),
        ],
        default='VERTEX_LIT_LINEAR'
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        blend_path = _find_itera_blend_path()
        if not blend_path:
            self.report({'ERROR'}, T("Itera Tools 3 не найден в библиотеках ассетов"))
            return {'CANCELLED'}

        # Remember selection before append (append can change selection)
        saved_selected = [obj for obj in context.selected_objects]
        saved_active = context.active_object

        mat_names = {
            'VERTEX_LIT_LINEAR': "Vertex Lit Linear UV Texture",
        }
        target_name = mat_names[self.preset]

        # Check if already loaded
        itera_mat = bpy.data.materials.get(target_name)

        if itera_mat is None:
            # Append from blend file (more reliable than libraries.load for assets)
            try:
                bpy.ops.wm.append(
                    filepath=os.path.join(blend_path, "Material", target_name),
                    directory=os.path.join(blend_path, "Material") + os.sep,
                    filename=target_name,
                    link=False,
                    do_reuse_local_id=True,
                )
                itera_mat = bpy.data.materials.get(target_name)
            except Exception as e:
                self.report({'ERROR'}, f"{T('Ошибка загрузки:')} {e}")
                return {'CANCELLED'}

            # Restore selection after append
            bpy.ops.object.select_all(action='DESELECT')
            for obj in saved_selected:
                obj.select_set(True)
            if saved_active:
                context.view_layer.objects.active = saved_active

        if itera_mat is None:
            self.report({'ERROR'}, f"{T('Материал не найден:')} {target_name}")
            return {'CANCELLED'}

        # Apply to selected mesh objects
        applied = 0
        for obj in saved_selected:
            if obj.type != 'MESH':
                continue

            # Save original materials + face assignments before replacing
            import json
            if not obj.get("gtatools_saved_materials"):
                orig = {
                    "materials": [slot.material.name if slot.material else "" for slot in obj.material_slots],
                    "face_indices": [p.material_index for p in obj.data.polygons]
                }
                obj["gtatools_saved_materials"] = json.dumps(orig)

            # Clear existing slots and add Itera material
            obj.data.materials.clear()
            obj.data.materials.append(itera_mat)
            applied += 1

        self.report({'INFO'}, f"Itera '{self.preset}': {applied} {T('объектов')}")
        return {'FINISHED'}


class GTATOOLS_OT_apply_itera_quickstart(bpy.types.Operator):
    """Применить Quickstart Vertex Lightable Surface — модификатор + коллекция со светом"""
    bl_idname = "gtatools.apply_itera_quickstart"
    bl_label = "Apply Itera Quickstart"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        blend_path = _find_itera_blend_path()
        if not blend_path:
            self.report({'ERROR'}, T("Itera Tools 3 не найден в библиотеках ассетов"))
            return {'CANCELLED'}

        ng_name = "Quickstart Vertex Lightable Surface"
        col_name = "Template Scene - Vertex Lights"

        # Remember selection before append (append can change selection)
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        # 1. Load node group if not already in blend
        node_group = bpy.data.node_groups.get(ng_name)
        if node_group is None:
            try:
                with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                    if ng_name in data_from.node_groups:
                        data_to.node_groups = [ng_name]
                node_group = bpy.data.node_groups.get(ng_name)
            except Exception as e:
                self.report({'ERROR'}, f"{T('Ошибка загрузки node group:')} {e}")
                return {'CANCELLED'}

        if node_group is None:
            self.report({'ERROR'}, f"{T('Node group не найден:')} {ng_name}")
            return {'CANCELLED'}

        # 2. Load light collection if not already present
        light_col = None
        for c in bpy.data.collections:
            if c.name.startswith(col_name):
                light_col = c
                break

        if light_col is None:
            try:
                with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                    if col_name in data_from.collections:
                        data_to.collections = [col_name]
                light_col = bpy.data.collections.get(col_name)
            except Exception:
                pass

        # 3. Link collection to scene if needed
        if light_col and light_col.name not in context.scene.collection.children:
            context.scene.collection.children.link(light_col)

        # 4. Add modifier only to MESH objects (not lights)
        applied = 0
        for obj in mesh_objects:
            # Check if modifier already exists
            has_mod = any(m.type == 'NODES' and m.node_group and
                         m.node_group.name == ng_name for m in obj.modifiers)
            if has_mod:
                continue

            mod = obj.modifiers.new(name=ng_name, type='NODES')
            mod.node_group = node_group

            # Set Light Collection input if available
            if light_col:
                for item in mod.node_group.interface.items_tree:
                    if hasattr(item, 'socket_type') and item.socket_type == 'NodeSocketCollection':
                        mod[item.identifier] = light_col
                        break

            applied += 1

        self.report({'INFO'}, f"Quickstart: {applied} {T('объектов')}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_itera_material(bpy.types.Operator):
    """Убрать Itera материал и восстановить оригинальные"""
    bl_idname = "gtatools.remove_itera_material"
    bl_label = "Remove Itera Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        import json
        restored = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Remove Quickstart modifier
            quickstart_mods = [m for m in obj.modifiers
                               if m.type == 'NODES' and m.node_group
                               and "Quickstart" in m.node_group.name]
            for mod in quickstart_mods:
                obj.modifiers.remove(mod)

            # Restore saved materials + face assignments
            saved = obj.get("gtatools_saved_materials")
            if saved:
                data = json.loads(saved)
                names = data["materials"] if isinstance(data, dict) else data
                face_indices = data.get("face_indices", []) if isinstance(data, dict) else []

                obj.data.materials.clear()
                for name in names:
                    mat = bpy.data.materials.get(name)
                    obj.data.materials.append(mat)

                # Restore face material assignments
                if face_indices:
                    for i, idx in enumerate(face_indices):
                        if i < len(obj.data.polygons):
                            obj.data.polygons[i].material_index = idx

                del obj["gtatools_saved_materials"]
                restored += 1
            else:
                # No saved data — just clear Itera materials
                itera_names = {"Vertex Lit Linear UV Texture"}
                to_remove = []
                for i, slot in enumerate(obj.material_slots):
                    if slot.material and slot.material.name in itera_names:
                        to_remove.append(i)
                for i in reversed(to_remove):
                    obj.active_material_index = i
                    bpy.ops.object.material_slot_remove()

            if quickstart_mods:
                restored += 1

        self.report({'INFO'}, f"{T('Восстановлено:')} {restored} {T('объектов')}")
        return {'FINISHED'}


class GTATOOLS_OT_save_materials(bpy.types.Operator):
    """Сохранить материалы объекта в буфер"""
    bl_idname = "gtatools.save_materials"
    bl_label = "Save Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        import json
        mesh = obj.data

        # Сохраняем имена материалов в слотах
        mat_names = []
        for slot in obj.material_slots:
            mat_names.append(slot.material.name if slot.material else "")

        # Сохраняем material_index каждого полигона
        face_indices = [p.material_index for p in mesh.polygons]

        obj["gtatools_saved_materials"] = json.dumps({
            "materials": mat_names,
            "face_indices": face_indices
        })
        self.report({'INFO'}, T("Материалы сохранены") + f" ({len(mat_names)})")
        return {'FINISHED'}


class GTATOOLS_OT_restore_materials(bpy.types.Operator):
    """Восстановить сохранённые материалы на объект"""
    bl_idname = "gtatools.restore_materials"
    bl_label = "Restore Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        raw = obj.get("gtatools_saved_materials")
        if not raw:
            self.report({'ERROR'}, T("Нет сохранённых материалов!"))
            return {'CANCELLED'}

        import json
        data = json.loads(raw)

        # Поддержка старого формата (список имён) и нового (dict)
        if isinstance(data, list):
            mat_names = data
            face_indices = None
        else:
            mat_names = data["materials"]
            face_indices = data.get("face_indices")

        mesh = obj.data

        # Очищаем все слоты
        mesh.materials.clear()

        # Создаём слоты и назначаем материалы
        not_found = []
        for mat_name in mat_names:
            if mat_name == "":
                mesh.materials.append(None)
            elif mat_name in bpy.data.materials:
                mesh.materials.append(bpy.data.materials[mat_name])
            else:
                not_found.append(mat_name)
                mesh.materials.append(None)

        # Восстанавливаем назначения полигонов
        if face_indices and len(face_indices) == len(mesh.polygons):
            for poly, idx in zip(mesh.polygons, face_indices):
                poly.material_index = idx

        if not_found:
            self.report({'WARNING'}, T("Материал не найден:") + " " + ", ".join(not_found))
        else:
            self.report({'INFO'}, T("Материалы восстановлены") + f" ({len(mat_names)})")
        return {'FINISHED'}


class GTATOOLS_OT_eyedropper_color(bpy.types.Operator):
    """Кликните на полигон чтобы взять его цвет"""
    bl_idname = "gtatools.eyedropper_color"
    bl_label = "Pick Color from Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            # Показываем курсор пипетки
            context.window.cursor_set('EYEDROPPER')

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # Делаем raycast под курсором
            result = self.pick_color_at_cursor(context, event)
            if result:
                context.window.cursor_set('DEFAULT')
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "No mesh under cursor")
                return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            # Отмена
            context.window.cursor_set('DEFAULT')
            self.report({'INFO'}, "Color pick cancelled")
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type != 'VIEW_3D':
            self.report({'ERROR'}, "Use in 3D View!")
            return {'CANCELLED'}

        context.window.cursor_set('EYEDROPPER')
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Click on polygon to pick color (ESC to cancel)")
        return {'RUNNING_MODAL'}

    def pick_color_at_cursor(self, context, event):
        """Raycast и получение цвета полигона под курсором"""
        from bpy_extras import view3d_utils

        region = context.region
        rv3d = context.region_data

        # Координаты мыши в 3D
        coord = event.mouse_region_x, event.mouse_region_y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

        # Raycast по всем объектам
        depsgraph = context.evaluated_depsgraph_get()
        result, location, normal, face_index, obj, matrix = context.scene.ray_cast(
            depsgraph, ray_origin, view_vector
        )

        if not result or obj is None or obj.type != 'MESH':
            return False

        mesh = obj.data
        if not mesh.color_attributes:
            self.report({'ERROR'}, "Object has no vertex colors!")
            return False

        color_attr = mesh.color_attributes.active_color
        if color_attr is None:
            self.report({'ERROR'}, "No active color layer!")
            return False

        if face_index < 0 or face_index >= len(mesh.polygons):
            return False

        # Считываем цвета вершин этой грани
        colors = []
        poly = mesh.polygons[face_index]
        for loop_idx in poly.loop_indices:
            c = color_attr.data[loop_idx].color
            colors.append((c[0], c[1], c[2]))

        # Усредняем цвет
        if colors:
            avg_r = sum(c[0] for c in colors) / len(colors)
            avg_g = sum(c[1] for c in colors) / len(colors)
            avg_b = sum(c[2] for c in colors) / len(colors)

            context.scene.gtatools_fill_color = (avg_r, avg_g, avg_b)
            self.report({'INFO'}, f"Color picked: RGB({int(avg_r*255)}, {int(avg_g*255)}, {int(avg_b*255)})")
            return True

        return False


class GTATOOLS_OT_fill_faces(bpy.types.Operator):
    """Залить выделенные грани цветом"""
    bl_idname = "gtatools.fill_faces"
    bl_label = "Fill Selected Faces"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        scene = context.scene
        color = scene.gtatools_fill_color

        success, message = fill_selected_faces_with_backup(obj, color)

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_restore_fill(bpy.types.Operator):
    """Восстановить цвета, изменённые заливкой"""
    bl_idname = "gtatools.restore_fill"
    bl_label = "Restore Fill"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        success, message = restore_filled_faces(obj)

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_remove_fill_color(bpy.types.Operator):
    """Удалить цвет из списка и восстановить оригинальные цвета"""
    bl_idname = "gtatools.remove_fill_color"
    bl_label = "Remove Fill Color"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        # Switch to Object Mode for data writing
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        success, message = remove_fill_color_by_index(obj, self.index)

        # Возвращаемся в исходный режим
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_select_fill_color(bpy.types.Operator):
    """Выделить полигоны с этим цветом"""
    bl_idname = "gtatools.select_fill_color"
    bl_label = "Select Faces by Color"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        if not (0 <= self.index < len(obj.gtatools_fill_colors)):
            return {'CANCELLED'}

        target_color = obj.gtatools_fill_colors[self.index].color
        tolerance = 0.01

        # Switch to Object Mode for data reading
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        if not mesh.color_attributes or not mesh.color_attributes.active_color:
            self.report({'ERROR'}, T("Нет vertex colors!"))
            if original_mode == 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}

        color_attr = mesh.color_attributes.active_color

        # Find polygons with this color
        selected_count = 0
        for poly in mesh.polygons:
            has_color = False
            for loop_idx in poly.loop_indices:
                c = color_attr.data[loop_idx].color
                if (abs(c[0] - target_color[0]) < tolerance and
                    abs(c[1] - target_color[1]) < tolerance and
                    abs(c[2] - target_color[2]) < tolerance):
                    has_color = True
                    break

            if has_color:
                poly.select = True
                selected_count += 1
            else:
                poly.select = False

        # Switch to Edit Mode to show selection
        bpy.ops.object.mode_set(mode='EDIT')

        self.report({'INFO'}, f"{T('Выделено')} {selected_count} {T('полигонов')}")
        return {'FINISHED'}


class GTATOOLS_OT_delete_fill_color_level(bpy.types.Operator):
    """Удалить scatter уровень (пересчитать цвета)"""
    bl_idname = "gtatools.delete_fill_color_level"
    bl_label = "Delete Scatter Level"
    bl_options = {'REGISTER', 'UNDO'}

    color_index: bpy.props.IntProperty()
    level: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        if not (0 <= self.color_index < len(obj.gtatools_fill_colors)):
            return {'CANCELLED'}

        color = obj.gtatools_fill_colors[self.color_index].color

        # Switch to Object Mode
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        success, message = remove_scatter_layer(obj, color, self.level)

        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_clear_fill_color_levels(bpy.types.Operator):
    """Очистить все scatter уровни цвета"""
    bl_idname = "gtatools.clear_fill_color_levels"
    bl_label = "Clear Scatter Levels"
    bl_options = {'REGISTER', 'UNDO'}

    color_index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        if not (0 <= self.color_index < len(obj.gtatools_fill_colors)):
            return {'CANCELLED'}

        color = obj.gtatools_fill_colors[self.color_index].color

        # Switch to Object Mode
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        success, message = clear_scatter_layers(obj, color)

        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_scatter_light(bpy.types.Operator):
    """Рассеять свет от выделенных граней к соседним"""
    bl_idname = "gtatools.scatter_light"
    bl_label = "Scatter Light"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        scene = context.scene

        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        # Switch to Object Mode for data reading
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Определяем цвет выделенных полигонов
        selected_color = get_selected_faces_color(obj)

        # Сохраняем цвета ДО scatter для вычисления дельты
        pre_scatter_colors = {}
        mesh = obj.data
        if mesh.color_attributes and mesh.color_attributes.active_color:
            color_attr = mesh.color_attributes.active_color
            for loop_idx in range(len(color_attr.data)):
                c = color_attr.data[loop_idx].color
                pre_scatter_colors[loop_idx] = (c[0], c[1], c[2], c[3])

        intensity = scene.gtatools_scatter_intensity
        falloff = scene.gtatools_scatter_falloff
        iterations = scene.gtatools_scatter_iterations
        radius = scene.gtatools_scatter_radius

        success, message, affected_loops = scatter_light_from_selected(obj, intensity, falloff, iterations, radius)

        level_info = ""

        # Вычисляем дельты ДО переключения режима (пока данные mesh актуальны)
        if success and selected_color and affected_loops:
            deltas = {}
            color_attr = mesh.color_attributes.active_color
            for loop_idx in affected_loops:
                if loop_idx in pre_scatter_colors and loop_idx < len(color_attr.data):
                    old = pre_scatter_colors[loop_idx]
                    new = color_attr.data[loop_idx].color
                    delta = (new[0] - old[0], new[1] - old[1], new[2] - old[2], 0.0)
                    # Сохраняем только если дельта не нулевая
                    if abs(delta[0]) > 0.001 or abs(delta[1]) > 0.001 or abs(delta[2]) > 0.001:
                        deltas[loop_idx] = delta

            # Сохраняем дельты как scatter слой
            if deltas:
                scatter_level = add_scatter_layer(obj, selected_color, deltas)
                if scatter_level > 0:
                    level_info = f" | Level {scatter_level}"

        # Возвращаемся в исходный режим
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if success:
            self.report({'INFO'}, f"{message}{level_info}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_toggle_face_select(bpy.types.Operator):
    """Переключить режим выделения граней в Vertex Paint"""
    bl_idname = "gtatools.toggle_face_select"
    bl_label = "Toggle Face Selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        # Toggle face selection masking in paint mode
        obj.data.use_paint_mask = not obj.data.use_paint_mask

        if obj.data.use_paint_mask:
            self.report({'INFO'}, "Face selection ON - Click faces to select")
        else:
            self.report({'INFO'}, "Face selection OFF")

        return {'FINISHED'}


class GTATOOLS_OT_switch_to_edit(bpy.types.Operator):
    """Переключить в Edit Mode для выделения граней"""
    bl_idname = "gtatools.switch_to_edit"
    bl_label = "Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
        return {'FINISHED'}


class GTATOOLS_OT_switch_to_vpaint(bpy.types.Operator):
    """Переключить в Vertex Paint Mode"""
    bl_idname = "gtatools.switch_to_vpaint"
    bl_label = "Vertex Paint Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object:
            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        return {'FINISHED'}


class GTATOOLS_OT_select_color_attribute(bpy.types.Operator):
    """Выбрать color attribute и обновить превью prelight"""
    bl_idname = "gtatools.select_color_attribute"
    bl_label = "Select Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    attribute_name: StringProperty(name="Attribute Name")

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                mesh_objects = [obj]

        if not mesh_objects:
            self.report({'ERROR'}, "Select mesh object(s)!")
            return {'CANCELLED'}

        switched = 0
        for obj in mesh_objects:
            mesh = obj.data
            if self.attribute_name in mesh.color_attributes:
                color_attr = mesh.color_attributes[self.attribute_name]
                mesh.color_attributes.active_color = color_attr
                self.update_prelight_preview(obj, self.attribute_name)
                switched += 1

        self.report({'INFO'}, f"Active: {self.attribute_name} ({switched} objects)")
        return {'FINISHED'}

    def update_prelight_preview(self, obj, color_name):
        """Update vertex color node in materials to use new color attribute"""
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue

            nodes = mat.node_tree.nodes
            vc_node = nodes.get("Prelight_VertexColor")

            if vc_node:
                if hasattr(vc_node, 'layer_name'):
                    vc_node.layer_name = color_name
                elif hasattr(vc_node, 'attribute_name'):
                    vc_node.attribute_name = color_name


class GTATOOLS_OT_add_color_attribute(bpy.types.Operator):
    """Добавить новый color attribute"""
    bl_idname = "gtatools.add_color_attribute"
    bl_label = "Add Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        mesh = obj.data

        # Generate unique name
        base_name = "Color"
        name = base_name
        counter = 1
        while name in mesh.color_attributes:
            name = f"{base_name}.{counter:03d}"
            counter += 1

        color_attr = mesh.color_attributes.new(name=name, type='BYTE_COLOR', domain='CORNER')
        mesh.color_attributes.active_color = color_attr

        self.report({'INFO'}, f"Created: {name}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_color_attribute(bpy.types.Operator):
    """Удалить активный color attribute"""
    bl_idname = "gtatools.remove_color_attribute"
    bl_label = "Remove Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        mesh = obj.data
        if not mesh.color_attributes:
            self.report({'ERROR'}, "No color attributes!")
            return {'CANCELLED'}

        active = mesh.color_attributes.active_color
        if active:
            name = active.name
            mesh.color_attributes.remove(active)
            self.report({'INFO'}, f"Removed: {name}")
        else:
            self.report({'ERROR'}, "No active color attribute!")
            return {'CANCELLED'}

        return {'FINISHED'}


class GTATOOLS_OT_create_color_attr(bpy.types.Operator):
    """Создать color attribute"""
    bl_idname = "gtatools.create_color_attr"
    bl_label = "Create Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    attr_name: StringProperty(default="Day")

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        mesh = obj.data

        if self.attr_name in mesh.color_attributes:
            self.report({'INFO'}, f"{self.attr_name} already exists")
            return {'CANCELLED'}

        # Create attribute
        attr = mesh.color_attributes.new(name=self.attr_name, type='BYTE_COLOR', domain='CORNER')
        # Fill with white
        for i in range(len(attr.data)):
            attr.data[i].color = (1.0, 1.0, 1.0, 1.0)

        # Set as active
        mesh.color_attributes.active_color = attr

        self.report({'INFO'}, f"Created: {self.attr_name}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_color_attr(bpy.types.Operator):
    """Удалить color attribute по имени на всех выделенных объектах"""
    bl_idname = "gtatools.remove_color_attr"
    bl_label = "Remove Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    attr_name: StringProperty(default="")

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                mesh_objects = [obj]

        if not mesh_objects:
            self.report({'ERROR'}, "Select mesh object(s)!")
            return {'CANCELLED'}

        removed = 0
        for obj in mesh_objects:
            mesh = obj.data
            if self.attr_name in mesh.color_attributes:
                attr = mesh.color_attributes[self.attr_name]
                mesh.color_attributes.remove(attr)
                removed += 1

        if removed:
            self.report({'INFO'}, f"Removed '{self.attr_name}' from {removed} objects")
        else:
            self.report({'ERROR'}, f"{self.attr_name} not found")
            return {'CANCELLED'}
        return {'FINISHED'}


# =============================================================================
# TEXTURE LOADER
# =============================================================================

class GTATOOLS_OT_load_textures(bpy.types.Operator):
    """Загрузить текстуры по именам материалов из указанных папок"""
    bl_idname = "gtatools.load_textures"
    bl_label = "Load Textures"
    bl_options = {'REGISTER', 'UNDO'}

    def find_texture_file(self, material_name, search_paths):
        """Search for texture file with given material name in specified paths"""
        extensions = ['.png', '.jpg', '.jpeg', '.tga', '.bmp', '.dds']

        for search_path in search_paths:
            if not search_path or not os.path.isdir(search_path):
                continue

            for ext in extensions:
                # Try exact name
                texture_path = os.path.join(search_path, material_name + ext)
                if os.path.isfile(texture_path):
                    return texture_path

                # Try lowercase
                texture_path = os.path.join(search_path, material_name.lower() + ext)
                if os.path.isfile(texture_path):
                    return texture_path

                # Try uppercase
                texture_path = os.path.join(search_path, material_name.upper() + ext)
                if os.path.isfile(texture_path):
                    return texture_path

        return None

    def setup_material_texture(self, material, image):
        """Setup material nodes to use the loaded texture"""
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Find or create Principled BSDF
        principled = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break

        if not principled:
            principled = nodes.new('ShaderNodeBsdfPrincipled')
            principled.location = (0, 0)

        # Set Specular to 0 (works for Blender 3.x and 4.x)
        for inp in principled.inputs:
            if 'specular' in inp.name.lower() or 'ior level' in inp.name.lower():
                if inp.type == 'VALUE':
                    inp.default_value = 0.0

        # Check if texture already connected
        for node in nodes:
            if node.type == 'TEX_IMAGE' and node.image == image:
                return False  # Already setup, use "Fix Materials" button instead

        # Find existing empty image texture node or create new
        tex_node = None
        for node in nodes:
            if node.type == 'TEX_IMAGE' and node.image is None:
                tex_node = node
                break

        if not tex_node:
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.location = (-300, 0)

        tex_node.image = image

        # Connect to Principled BSDF Base Color
        base_color_input = principled.inputs.get('Base Color')
        if base_color_input and not base_color_input.is_linked:
            links.new(tex_node.outputs['Color'], base_color_input)

        # Connect Alpha only if image has significant transparent pixels (>100)
        has_significant_alpha = False
        try:
            # Принудительно загрузить пиксели в память
            if not image.has_data:
                image.reload()

            if image.channels >= 4 and len(image.pixels) > 0:
                pixels = np.array(image.pixels[:])
                alpha = pixels[3::4]
                transparent_count = int(np.sum(alpha < 0.95))
                print(f"[Texture] {image.name}: прозрачных = {transparent_count}")
                if transparent_count > 5000:
                    has_significant_alpha = True
        except Exception as e:
            print(f"[Texture] {image.name}: ошибка - {e}")

        if has_significant_alpha:
            alpha_input = principled.inputs.get('Alpha')
            if alpha_input and not alpha_input.is_linked:
                links.new(tex_node.outputs['Alpha'], alpha_input)
                if hasattr(material, 'blend_method'):
                    material.blend_method = 'HASHED'
                if hasattr(material, 'shadow_method'):
                    material.shadow_method = 'HASHED'
                if hasattr(material, 'show_transparent_back'):
                    material.show_transparent_back = False

        return True

    def execute(self, context):
        scene = context.scene

        # Get search paths
        path1 = scene.gtatools_texture_path1
        path2 = scene.gtatools_texture_path2

        # If path2 is empty, try to get blend file directory
        if not path2 and bpy.data.filepath:
            path2 = os.path.dirname(bpy.data.filepath)

        search_paths = [p for p in [path1, path2] if p]

        if not search_paths:
            self.report({'ERROR'}, T("Укажите хотя бы один путь к папке с текстурами!"))
            return {'CANCELLED'}

        # Get active material from active object
        obj = context.active_object
        if not obj or not obj.active_material:
            self.report({'ERROR'}, T("Выберите материал в списке!"))
            return {'CANCELLED'}

        material = obj.active_material
        material_name = material.name

        # Skip default/system material names
        if material_name.lower() in ('none', 'material', 'dots stroke'):
            self.report({'ERROR'}, T("Выберите корректный материал!"))
            return {'CANCELLED'}

        # Find texture file
        texture_path = self.find_texture_file(material_name, search_paths)

        if texture_path:
            # Check if image already loaded
            existing_image = None
            for img in bpy.data.images:
                if img.filepath and os.path.normpath(img.filepath) == os.path.normpath(texture_path):
                    existing_image = img
                    break

            if existing_image:
                image = existing_image
            else:
                # Load new image
                try:
                    image = bpy.data.images.load(texture_path)
                except Exception as e:
                    self.report({'ERROR'}, f"{T('Не удалось загрузить')} {texture_path}: {e}")
                    return {'CANCELLED'}

            # Setup material
            if self.setup_material_texture(material, image):
                self.report({'INFO'}, f"{T('Загружена текстура:')} {material_name}")
            else:
                self.report({'INFO'}, f"{T('Текстура уже подключена:')} {material_name}")
        else:
            self.report({'WARNING'}, f"{T('Текстура не найдена:')} {material_name}")

        return {'FINISHED'}


class GTATOOLS_OT_set_blend_folder(bpy.types.Operator):
    """Установить путь к папке .blend файла"""
    bl_idname = "gtatools.set_blend_folder"
    bl_label = "Set Blend Folder"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if bpy.data.filepath:
            context.scene.gtatools_texture_path2 = os.path.dirname(bpy.data.filepath)
            self.report({'INFO'}, T("Путь установлен"))
        else:
            self.report({'WARNING'}, T("Сначала сохраните .blend файл!"))
        return {'FINISHED'}


class GTATOOLS_OT_drop_texture_as_material(bpy.types.Operator):
    """Создать материал из перетаскиваемой текстуры"""
    bl_idname = "gtatools.drop_texture_as_material"
    bl_label = "Drop Texture as Material"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        subtype='FILE_PATH',
    )

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, T("Файл не указан!"))
            return {'CANCELLED'}

        # Check extension
        ext = os.path.splitext(self.filepath)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.tga', '.bmp', '.dds'):
            self.report({'ERROR'}, f"{T('Неподдерживаемый формат:')} {ext}")
            return {'CANCELLED'}

        # Get active object
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        # Имя материала из имени файла
        mat_name = os.path.splitext(os.path.basename(self.filepath))[0]

        # Load image
        try:
            image = bpy.data.images.load(self.filepath)
        except Exception as e:
            self.report({'ERROR'}, f"{T('Ошибка загрузки:')} {e}")
            return {'CANCELLED'}

        # Создаём материал
        material = bpy.data.materials.new(name=mat_name)
        material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Получаем Principled BSDF (ищем по типу, не по имени)
        principled = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break

        # Specular = 0 (GTA стиль)
        for inp in principled.inputs:
            if 'specular' in inp.name.lower() or 'ior level' in inp.name.lower():
                if inp.type == 'VALUE':
                    inp.default_value = 0.0

        # Создаём Image Texture ноду
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = image
        tex_node.location = (-300, 300)

        # Подключаем Color к Base Color
        links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])

        # Проверяем альфа канал
        if image.channels >= 4:
            try:
                pixels = np.array(image.pixels[:])
                alpha = pixels[3::4]
                transparent_count = int(np.sum(alpha < 0.95))
                if transparent_count > 5000:
                    links.new(tex_node.outputs['Alpha'], principled.inputs['Alpha'])
                    if hasattr(material, 'blend_method'):
                        material.blend_method = 'HASHED'
                    if hasattr(material, 'shadow_method'):
                        material.shadow_method = 'HASHED'
                    if hasattr(material, 'show_transparent_back'):
                        material.show_transparent_back = False
            except:
                pass

        # Применяем материал к объекту
        if obj.data.materials:
            obj.data.materials.append(material)
        else:
            obj.data.materials.append(material)

        # Делаем новый материал активным
        obj.active_material_index = len(obj.data.materials) - 1

        self.report({'INFO'}, f"{T('Создан материал:')} {mat_name}")
        return {'FINISHED'}


class GTATOOLS_FH_texture_drop(bpy.types.FileHandler):
    """File Handler для перетаскивания текстур"""
    bl_idname = "GTATOOLS_FH_texture_drop"
    bl_label = "GTA Texture Drop"
    bl_import_operator = "gtatools.drop_texture_as_material"
    bl_file_extensions = ".png;.jpg;.jpeg;.tga;.bmp;.dds"

    @classmethod
    def poll_drop(cls, context):
        return context.area and context.area.type == 'VIEW_3D'


class GTATOOLS_OT_drop_txd(bpy.types.Operator):
    """Импорт TXD при перетаскивании во viewport"""
    bl_idname = "gtatools.drop_txd"
    bl_label = "Import TXD (Drop)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        from .ops.txd_import import import_txd as inu_import_txd
        count = 0
        for f in self.files:
            path = os.path.join(self.directory, f.name)
            if os.path.isfile(path) and path.lower().endswith('.txd'):
                try:
                    images = inu_import_txd(filepath=path)
                    # Create materials for each imported texture
                    for img in images:
                        mat_name = os.path.splitext(img.name)[0]
                        mat = bpy.data.materials.get(mat_name)
                        if not mat:
                            mat = bpy.data.materials.new(name=mat_name)
                            mat.use_nodes = True
                            nodes = mat.node_tree.nodes
                            bsdf = None
                            for n in nodes:
                                if n.type == 'BSDF_PRINCIPLED':
                                    bsdf = n
                                    break
                            if bsdf:
                                tex_node = nodes.new('ShaderNodeTexImage')
                                tex_node.image = img
                                tex_node.location = (bsdf.location.x - 300, bsdf.location.y)
                                mat.node_tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
                                if 'Specular IOR Level' in bsdf.inputs:
                                    bsdf.inputs['Specular IOR Level'].default_value = 0.0
                                elif 'Specular' in bsdf.inputs:
                                    bsdf.inputs['Specular'].default_value = 0.0
                    count += len(images)
                except Exception as e:
                    self.report({'WARNING'}, f"TXD: {e}")
        self.report({'INFO'}, f"TXD: {count} {T('текстур импортировано')}")
        return {'FINISHED'}


class GTATOOLS_FH_txd_drop(bpy.types.FileHandler):
    """File Handler для перетаскивания TXD"""
    bl_idname = "GTATOOLS_FH_txd_drop"
    bl_label = "GTA TXD Drop"
    bl_import_operator = "gtatools.drop_txd"
    bl_file_extensions = ".txd"

    @classmethod
    def poll_drop(cls, context):
        return context.area and context.area.type == 'VIEW_3D'


class GTATOOLS_OT_check_materials(bpy.types.Operator):
    """Проверить количество материалов на выделенных объектах"""
    bl_idname = "gtatools.check_materials"
    bl_label = "Check Materials"

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected:
            self.report({'ERROR'}, T("Выделите меш объекты!"))
            return {'CANCELLED'}

        total_materials = 0
        report_lines = []

        for obj in selected:
            mat_count = len([slot for slot in obj.material_slots if slot.material])
            total_materials += mat_count

            # GTA SA limit is 50 materials per object
            status = "⚠️" if mat_count > 50 else "✓"
            report_lines.append(f"{status} {obj.name}: {mat_count} mat.")

        # Show detailed report
        if len(selected) == 1:
            obj = selected[0]
            mat_count = len([slot for slot in obj.material_slots if slot.material])
            if mat_count > 50:
                self.report({'WARNING'}, f"{obj.name}: {mat_count} materials (GTA limit: 50)")
            else:
                self.report({'INFO'}, f"{obj.name}: {mat_count} materials")
        else:
            over_limit = sum(1 for obj in selected if len([s for s in obj.material_slots if s.material]) > 50)
            if over_limit > 0:
                self.report({'WARNING'}, f"{T('Объектов:')} {len(selected)}, {T('всего материалов:')} {total_materials}, {T('превышен лимит:')} {over_limit}")
            else:
                self.report({'INFO'}, f"{T('Объектов:')} {len(selected)}, {T('всего материалов:')} {total_materials}")

        return {'FINISHED'}


class GTATOOLS_OT_cleanup_materials(bpy.types.Operator):
    """Объединить дубликаты материалов и текстур (.001, .002, и т.д.) с оригиналами"""
    bl_idname = "gtatools.cleanup_materials"
    bl_label = "Cleanup Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import re
        import os

        # Pattern to match .001, .002, etc. suffix
        pattern = re.compile(r'^(.+)\.(\d{3})$')

        merged_count = 0
        removed_materials = []

        # Find all duplicate materials
        duplicates = {}  # {base_name: [list of duplicate materials]}

        for mat in bpy.data.materials:
            match = pattern.match(mat.name)
            if match:
                base_name = match.group(1)
                if base_name not in duplicates:
                    duplicates[base_name] = []
                duplicates[base_name].append(mat)

        # Process each group of duplicates
        for base_name, dup_list in duplicates.items():
            # Find original material
            original = bpy.data.materials.get(base_name)

            if not original:
                # No original found, rename first duplicate to base name
                first_dup = dup_list[0]
                first_dup.name = base_name
                original = first_dup
                dup_list = dup_list[1:]

            # Replace duplicates with original in all objects
            for dup_mat in dup_list:
                for obj in bpy.data.objects:
                    if obj.type != 'MESH':
                        continue
                    for slot in obj.material_slots:
                        if slot.material == dup_mat:
                            slot.material = original
                            merged_count += 1

                removed_materials.append(dup_mat.name)

        # Remove unused duplicate materials
        for mat_name in removed_materials:
            mat = bpy.data.materials.get(mat_name)
            if mat and mat.users == 0:
                bpy.data.materials.remove(mat)

        # --- Textures (images) cleanup: safe mode (filepath must match) ---
        img_merged_count = 0
        removed_images = []
        skipped_images = 0

        def _img_key(img):
            # Compare by absolute filepath when possible; fall back to basename
            try:
                fp = bpy.path.abspath(img.filepath, library=img.library) if img.filepath else ""
            except Exception:
                fp = img.filepath or ""
            if fp:
                return os.path.normcase(os.path.normpath(fp))
            # No filepath (packed/generated) — use source+size as a weak key
            return f"<nofile>:{img.source}:{tuple(img.size)}"

        img_duplicates = {}  # {base_name: [list of duplicate images]}
        for img in bpy.data.images:
            match = pattern.match(img.name)
            if match:
                base_name = match.group(1)
                img_duplicates.setdefault(base_name, []).append(img)

        for base_name, dup_list in img_duplicates.items():
            original = bpy.data.images.get(base_name)

            if not original:
                # No original — promote first duplicate whose key matches the rest
                first_dup = dup_list[0]
                first_dup.name = base_name
                original = first_dup
                dup_list = dup_list[1:]

            orig_key = _img_key(original)

            for dup_img in dup_list:
                # Safe check: only merge if filepath matches the original
                if _img_key(dup_img) != orig_key:
                    skipped_images += 1
                    continue

                # Replace in all material node trees
                for mat in bpy.data.materials:
                    if not mat.use_nodes or not mat.node_tree:
                        continue
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image == dup_img:
                            node.image = original
                            img_merged_count += 1

                # Replace in node groups (shader/geometry/compositor)
                for ng in bpy.data.node_groups:
                    for node in ng.nodes:
                        if node.type == 'TEX_IMAGE' and getattr(node, 'image', None) == dup_img:
                            node.image = original
                            img_merged_count += 1

                removed_images.append(dup_img.name)

        for img_name in removed_images:
            img = bpy.data.images.get(img_name)
            if img and img.users == 0:
                bpy.data.images.remove(img)

        # --- Report ---
        parts = []
        if merged_count or removed_materials:
            parts.append(f"{T('Материалов:')} {merged_count}/{len(removed_materials)}")
        if img_merged_count or removed_images:
            parts.append(f"{T('Текстур:')} {img_merged_count}/{len(removed_images)}")
        if skipped_images:
            parts.append(f"{T('Пропущено (разные пути):')} {skipped_images}")

        if parts:
            self.report({'INFO'}, " | ".join(parts))
        else:
            self.report({'INFO'}, T("Дубликаты материалов не найдены"))

        return {'FINISHED'}


class GTATOOLS_OT_sort_materials(bpy.types.Operator):
    """Сортировка материалов"""
    bl_idname = "gtatools.sort_materials"
    bl_label = "Sort Materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and len(obj.material_slots) > 1

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # Собираем текущие материалы и индексы полигонов
        mat_names = []
        for slot in obj.material_slots:
            mat_names.append(slot.material.name if slot.material else "")

        # Натуральная сортировка: 1, 2, 3, 10 вместо 1, 10, 2, 3
        def natural_key(i):
            return [int(p) if p.isdigit() else p for p in _re.split(r'(\d+)', mat_names[i].lower())]

        sorted_indices = sorted(range(len(mat_names)), key=natural_key)

        # Если уже отсортировано — ничего не делаем
        if sorted_indices == list(range(len(mat_names))):
            self.report({'INFO'}, T("Материалы уже отсортированы"))
            return {'FINISHED'}

        # Маппинг старый индекс -> новый индекс
        index_map = {old: new for new, old in enumerate(sorted_indices)}

        # Сохраняем новые индексы полигонов
        new_indices = [index_map[poly.material_index] for poly in mesh.polygons]

        # Сохраняем отсортированные материалы
        sorted_mats = [obj.material_slots[i].material for i in sorted_indices]

        # Очищаем все слоты и добавляем в отсортированном порядке
        mesh.materials.clear()
        for mat in sorted_mats:
            mesh.materials.append(mat)

        # Восстанавливаем индексы полигонов
        for poly, idx in zip(mesh.polygons, new_indices):
            poly.material_index = idx

        sorted_count = len(sorted_mats)
        self.report({'INFO'}, f"{T('Отсортировано материалов:')} {sorted_count}")
        return {'FINISHED'}


class GTATOOLS_OT_reset_transform(bpy.types.Operator):
    """Сброс Location и Rotation в (0,0,0) для выделенных мешей"""
    bl_idname = "gtatools.reset_transform"
    bl_label = "Reset Transform"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = context.selected_objects
        if not objects:
            objects = [o for o in context.scene.objects if o.type == 'MESH']
        count = 0
        for obj in objects:
            if obj.type == 'MESH':
                obj.location = (0.0, 0.0, 0.0)
                obj.rotation_euler = (0.0, 0.0, 0.0)
                count += 1
        self.report({'INFO'}, f"{T('Сброшено объектов:')} {count}")
        return {'FINISHED'}


class GTATOOLS_OT_apply_lightmap_uv2(bpy.types.Operator):
    """Применить текстуру LightMap на UV2 (Multiply) для выделенных объектов"""
    bl_idname = "gtatools.apply_lightmap_uv2"
    bl_label = "Apply LightMap UV2"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.png;*.jpg;*.jpeg;*.tga;*.bmp;*.tif;*.tiff", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath or not os.path.isfile(self.filepath):
            self.report({'ERROR'}, T("Файл не найден"))
            return {'CANCELLED'}

        lm_image = bpy.data.images.load(self.filepath, check_existing=True)

        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                objects = [obj]
        if not objects:
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        applied = 0
        for obj in objects:
            mesh = obj.data
            # Ensure UV2 exists
            if len(mesh.uv_layers) < 2:
                mesh.uv_layers.new(name="UVMap.001")
            uv2_name = mesh.uv_layers[1].name

            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not mat or not mat.use_nodes:
                    continue

                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                # Find Principled BSDF
                principled = None
                for n in nodes:
                    if n.type == 'BSDF_PRINCIPLED':
                        principled = n
                        break
                if not principled:
                    continue

                # Skip if already has lightmap
                if nodes.get("LM_Texture"):
                    nodes.get("LM_Texture").image = lm_image
                    applied += 1
                    continue

                # Find what's connected to Base Color
                base_input = principled.inputs['Base Color']
                orig_socket = None
                if base_input.links:
                    orig_socket = base_input.links[0].from_socket

                # UV Map node for UV2
                uv_node = nodes.new('ShaderNodeUVMap')
                uv_node.name = "LM_UV"
                uv_node.uv_map = uv2_name

                # Lightmap texture node
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.name = "LM_Texture"
                tex_node.label = "LightMap"
                tex_node.image = lm_image

                # Mix node (Multiply)
                if bpy.app.version >= (4, 0, 0):
                    mix = nodes.new('ShaderNodeMix')
                    mix.data_type = 'RGBA'
                    mix.blend_type = 'MULTIPLY'
                    mix.inputs['Factor'].default_value = 1.0
                    in_a, in_b, out_r = 'A', 'B', 'Result'
                else:
                    mix = nodes.new('ShaderNodeMixRGB')
                    mix.blend_type = 'MULTIPLY'
                    mix.inputs['Fac'].default_value = 1.0
                    in_a, in_b, out_r = 'Color1', 'Color2', 'Color'
                mix.name = "LM_Mix"
                mix.label = "LightMap Mix"

                # Position nodes
                px = principled.location.x
                py = principled.location.y
                uv_node.location = (px - 700, py - 300)
                tex_node.location = (px - 500, py - 300)
                mix.location = (px - 200, py)

                # Connect
                links.new(uv_node.outputs['UV'], tex_node.inputs['Vector'])
                if orig_socket:
                    links.new(orig_socket, mix.inputs[in_a])
                else:
                    mix.inputs[in_a].default_value = (1, 1, 1, 1)
                links.new(tex_node.outputs['Color'], mix.inputs[in_b])
                links.new(mix.outputs[out_r], base_input)

                applied += 1

        self.report({'INFO'}, f"LightMap UV2: {applied} {T('материалов')}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_lightmap_uv2(bpy.types.Operator):
    """Убрать LightMap UV2 из материалов выделенных объектов"""
    bl_idname = "gtatools.remove_lightmap_uv2"
    bl_label = "Remove LightMap UV2"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                objects = [obj]

        removed = 0
        for obj in objects:
            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not mat or not mat.use_nodes:
                    continue

                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                lm_mix = nodes.get("LM_Mix")
                lm_tex = nodes.get("LM_Texture")
                lm_uv = nodes.get("LM_UV")

                if not lm_mix:
                    continue

                # Restore original connection: A input -> Base Color target
                orig_socket = None
                a_input = lm_mix.inputs.get('A') or lm_mix.inputs.get('Color1')
                if a_input and a_input.links:
                    orig_socket = a_input.links[0].from_socket

                # Find where mix output goes
                for link in lm_mix.outputs[0].links:
                    target_socket = link.to_socket
                    if orig_socket:
                        links.new(orig_socket, target_socket)

                if lm_mix:
                    nodes.remove(lm_mix)
                if lm_tex:
                    nodes.remove(lm_tex)
                if lm_uv:
                    nodes.remove(lm_uv)
                removed += 1

        self.report({'INFO'}, f"LightMap UV2: {removed} {T('удалено')}")
        return {'FINISHED'}


class GTATOOLS_OT_toggle_lightmap_uv2(bpy.types.Operator):
    """Включить/выключить отображение LightMap UV2"""
    bl_idname = "gtatools.toggle_lightmap_uv2"
    bl_label = "Toggle LightMap UV2"
    bl_options = {'REGISTER', 'UNDO'}

    enable: BoolProperty(name="Enable", default=True)

    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                objects = [obj]

        count = 0
        for obj in objects:
            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not mat or not mat.use_nodes:
                    continue

                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                lm_mix = nodes.get("LM_Mix")
                if not lm_mix:
                    continue

                principled = None
                for n in nodes:
                    if n.type == 'BSDF_PRINCIPLED':
                        principled = n
                        break
                if not principled:
                    continue

                base_input = principled.inputs['Base Color']
                # Get A input of mix (original texture)
                a_input = lm_mix.inputs.get('A') or lm_mix.inputs.get('Color1')
                out_socket = lm_mix.outputs.get('Result') or lm_mix.outputs.get('Color') or lm_mix.outputs[0]
                orig_socket = a_input.links[0].from_socket if a_input and a_input.links else None

                if self.enable:
                    # ON: connect LM_Mix output → Base Color
                    lm_mix.mute = False
                    links.new(out_socket, base_input)
                else:
                    # OFF: bypass LM_Mix, connect original texture → Base Color directly
                    lm_mix.mute = True
                    if orig_socket:
                        links.new(orig_socket, base_input)
                count += 1

        state = "ON" if self.enable else "OFF"
        self.report({'INFO'}, f"LightMap UV2: {state} ({count})")
        return {'FINISHED'}


# =============================================================================
# PANELS
# =============================================================================

# Twemoji icons applied to subpanel headers at register() time. Edit the
# value to change the emoji, or comment out a line to fall back to the
# plain panel title.
_PANEL_ICON_KEYS = {
    "GTATOOLS_PT_ide_ipl_panel":       "disk",       # 💾
    "GTATOOLS_PT_export_panel":        "disk",       # 💾
    "GTATOOLS_PT_check_panel":         "testtube",   # 🧪
    "GTATOOLS_PT_itera_panel":         "palette",    # 🎨
    "GTATOOLS_PT_prelight_panel":      "light",      # 💡
    "GTATOOLS_PT_prelight_col_panel":  "rock",       # 🪨
    "GTATOOLS_PT_2dfx_panel":          "firework",   # 🎆
    "GTATOOLS_PT_lightmap_panel":      "light",      # 💡
    "GTATOOLS_PT_water_panel":         "water",      # 🌊
    "GTATOOLS_PT_anim_panel":          "clapper",    # 🎬
    "GTATOOLS_PT_radar_panel":         "map",        # 🗺️
    "GTATOOLS_PT_paths_panel":         "road",       # 🛣️
    "GTATOOLS_PT_bitmaps_panel":       "picture",    # 🖼️
    "GTATOOLS_PT_map_export_panel":    "map",        # 🗺️
    "GTATOOLS_PT_gta_material_panel":  "palette",    # 🎨
}


def _make_twemoji_header(original_draw_header, icon_key: str):
    """Return a draw_header that prepends a Twemoji PNG before the title.
    Wraps any existing draw_header so we don't clobber panels that use it."""
    def draw_header(self, context):
        icon_id = _icons.get_icon(icon_key)
        if icon_id:
            self.layout.label(text="", icon_value=icon_id)
        if original_draw_header is not None:
            original_draw_header(self, context)
    return draw_header


class GTATOOLS_PT_main_panel(bpy.types.Panel):
    """Главная панель GTA Tools"""
    bl_label = "GTA Tools"
    bl_idname = "GTATOOLS_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'

    def draw(self, context):
        layout = self.layout
        layout.label(text="GTA SA Modding Tools",
                     icon_value=_icons.get_icon("palette"))


class GTATOOLS_PT_ide_ipl_panel(bpy.types.Panel):
    """Панель IDE / IPL / IMG для работы с существующими файлами GTA SA"""
    bl_label = "IDE / IPL / IMG"
    bl_idname = "GTATOOLS_PT_ide_ipl_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        # IDE section
        box = layout.box()
        row = box.row(align=True)
        row.label(text="IDE", icon='TEXT')
        # Show entry count inline with tooltip
        ide_path = bpy.path.abspath(scn.gtatools_ide_path)
        if ide_path and os.path.isfile(ide_path):
            try:
                from .core.ide import read_ide
                _ide = read_ide(ide_path)
                counts = []
                if _ide.objects: counts.append(f"objs: {len(_ide.objects)}")
                if _ide.anims: counts.append(f"anim: {len(_ide.anims)}")
                if _ide.cars: counts.append(f"cars: {len(_ide.cars)}")
                if _ide.peds: counts.append(f"peds: {len(_ide.peds)}")
                if _ide.txdps: counts.append(f"txdp: {len(_ide.txdps)}")
                if counts:
                    info_text = ", ".join(counts)
                    op = row.operator("gtatools.info_tooltip", text=info_text, icon='INFO', emboss=False)
                    op.tooltip = T("Количество записей в IDE файле")
            except Exception:
                pass
        row = box.row(align=True)
        row.operator("gtatools.upsert_ide", text=T("Добавить"), icon='ADD')
        row.operator("gtatools.remove_ide", text=T("Удалить"), icon='REMOVE')
        row = box.row(align=True)
        row.operator("gtatools.import_ide", text=T("Импорт"), icon='IMPORT')
        row.operator("gtatools.export_ide", text=T("Экспорт"), icon='EXPORT')

        # IPL section
        box = layout.box()
        row = box.row(align=True)
        row.label(text="IPL", icon='EMPTY_AXIS')
        # Show entry count inline with tooltip
        ipl_path = bpy.path.abspath(scn.gtatools_ipl_path)
        if ipl_path and os.path.isfile(ipl_path):
            try:
                from .core.ipl import read_ipl
                _ipl = read_ipl(ipl_path)
                counts = []
                if _ipl.instances: counts.append(f"inst: {len(_ipl.instances)}")
                if _ipl.culls: counts.append(f"cull: {len(_ipl.culls)}")
                if _ipl.garages: counts.append(f"grge: {len(_ipl.garages)}")
                if _ipl.enexs: counts.append(f"enex: {len(_ipl.enexs)}")
                if _ipl.pickups: counts.append(f"pick: {len(_ipl.pickups)}")
                if _ipl.cars: counts.append(f"cars: {len(_ipl.cars)}")
                if _ipl.jumps: counts.append(f"jump: {len(_ipl.jumps)}")
                if _ipl.auzos: counts.append(f"auzo: {len(_ipl.auzos)}")
                if _ipl.occls: counts.append(f"occl: {len(_ipl.occls)}")
                if _ipl.zones: counts.append(f"zone: {len(_ipl.zones)}")
                if counts:
                    info_text = ", ".join(counts)
                    op = row.operator("gtatools.info_tooltip", text=info_text, icon='INFO', emboss=False)
                    op.tooltip = T("Количество записей в IPL файле")
            except Exception:
                pass
        row = box.row(align=True)
        row.operator("gtatools.upsert_ipl", text=T("Добавить"), icon='ADD')
        row.operator("gtatools.remove_ipl", text=T("Удалить"), icon='REMOVE')
        row = box.row(align=True)
        row.operator("gtatools.import_ipl", text=T("Импорт"), icon='IMPORT')
        row.operator("gtatools.export_ipl", text=T("Экспорт"), icon='EXPORT')
        row = box.row(align=True)
        row.operator("gtatools.import_ipl_sections", text=T("Секции IPL"), icon='IMPORT')
        row.operator("gtatools.export_ipl_sections", text=T("Секции IPL"), icon='EXPORT')
        box.operator("gtatools.replace_ipl_placeholders", text=T("Заменить Empty"), icon='MESH_DATA')

        # IMG section
        box = layout.box()
        row = box.row(align=True)
        row.label(text="IMG", icon='PACKAGE')
        row = box.row(align=True)
        row.prop(scn, "gtatools_img_export_dff", text="DFF", toggle=True)
        row.prop(scn, "gtatools_img_export_col", text="COL", toggle=True)
        row.prop(scn, "gtatools_img_export_txd", text="TXD", toggle=True)
        row = box.row(align=True)
        row.prop(scn, "gtatools_img_skip_lod", text="Skip LOD", toggle=True)
        row.prop(scn, "gtatools_img_load_txd", text="TXD", toggle=True)
        box.operator("gtatools.import_from_img", text=T("Импорт из IMG"), icon='IMPORT')
        box.operator("gtatools.export_to_img", text=T("Экспорт в IMG"), icon='EXPORT')
        box.operator("gtatools.remove_from_img", text=T("Удалить из IMG"), icon='REMOVE')

        # Shared TXD — one TXD for multiple DFFs
        box.separator()
        row = box.row(align=True)
        row.prop(scn, "gtatools_shared_txd_name", text="")
        row.operator("gtatools.export_shared_txd", text=T("Общий TXD"), icon='PACKAGE')




class GTATOOLS_OT_import_water(bpy.types.Operator):
    """Импорт water.dat"""
    bl_idname = "gtatools.import_water"
    bl_label = "Import Water"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.water_import import import_water
        try:
            objects = import_water(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"Water: {len(objects)} objects imported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Water import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_water(bpy.types.Operator):
    """Экспорт water.dat"""
    bl_idname = "gtatools.export_water"
    bl_label = "Export Water"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "water.dat"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.water_export import export_water
        try:
            objects = [o for o in context.selected_objects if o.type == 'MESH']
            if not objects:
                col = bpy.data.collections.get("Water")
                if col:
                    objects = [o for o in col.objects if o.type == 'MESH']
            count = export_water(filepath=self.filepath, objects=objects)
            self.report({'INFO'}, f"Water: {count} polygons exported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Water export error: {str(e)}")
            return {'CANCELLED'}


# =============================================================================
# PATH IO OPERATORS
# =============================================================================

class GTATOOLS_OT_import_flight(bpy.types.Operator):
    """Импорт flight.dat — маршруты полётов"""
    bl_idname = "gtatools.import_flight"
    bl_label = "Import Flight Paths"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.path_import import import_flight
        try:
            objects = import_flight(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"Flight: {len(objects)} paths imported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Flight import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_flight(bpy.types.Operator):
    """Экспорт flight.dat — маршруты полётов"""
    bl_idname = "gtatools.export_flight"
    bl_label = "Export Flight Paths"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "flight.dat"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.path_export import export_flight
        try:
            objects = [o for o in context.selected_objects
                       if o.type == 'CURVE' and o.get('path_type') == 'flight']
            count = export_flight(filepath=self.filepath, objects=objects)
            self.report({'INFO'}, f"Flight: {count} paths exported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Flight export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_track(bpy.types.Operator):
    """Импорт tracks.dat — железнодорожные пути"""
    bl_idname = "gtatools.import_track"
    bl_label = "Import Train Track"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.path_import import import_track
        try:
            objects = import_track(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"Track: {len(objects[0].data.splines[0].points) if objects else 0} nodes imported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Track import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_track(bpy.types.Operator):
    """Экспорт tracks.dat — железнодорожные пути"""
    bl_idname = "gtatools.export_track"
    bl_label = "Export Train Track"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "tracks.dat"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.path_export import export_track
        try:
            obj = None
            for o in context.selected_objects:
                if o.type == 'CURVE' and o.get('path_type') == 'track':
                    obj = o
                    break
            if not obj:
                col = bpy.data.collections.get("Train Tracks")
                if col:
                    for o in col.objects:
                        if o.type == 'CURVE' and o.get('path_type') == 'track':
                            obj = o
                            break
            count = export_track(filepath=self.filepath, obj=obj)
            self.report({'INFO'}, f"Track: {count} nodes exported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Track export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_nodes(bpy.types.Operator):
    """Импорт nodes.dat — пешеходные/авто пути (мультивыбор)"""
    bl_idname = "gtatools.import_nodes"
    bl_label = "Import Path Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.path_import import import_nodes
        total_nodes = 0
        total_files = 0
        for f in self.files:
            path = os.path.join(self.directory, f.name)
            if not os.path.isfile(path):
                continue
            try:
                objects = import_nodes(filepath=path, context=context)
                total_nodes += sum(len(o.data.vertices) for o in objects if o.type == 'MESH')
                total_files += 1
            except Exception as e:
                self.report({'WARNING'}, f"{f.name}: {str(e)}")
        self.report({'INFO'}, f"Nodes: {total_nodes} nodes from {total_files} files")
        return {'FINISHED'}


class GTATOOLS_OT_export_nodes(bpy.types.Operator):
    """Экспорт nodes.dat — группировка по имени файла или авто-разбиение по зонам"""
    bl_idname = "gtatools.export_nodes"
    bl_label = "Export Path Nodes"
    bl_options = {'REGISTER'}

    directory: StringProperty(subtype='DIR_PATH')
    fla4: BoolProperty(
        name="FLA4 Format",
        description=T("Писать nodes*.dat в расширенном FLA4 формате (spawn/speed/lanes per-node)"),
        default=False,
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        icon_id = _icons.get_icon("road")
        if icon_id:
            row.prop(self, "fla4", icon_value=icon_id)
        else:
            row.prop(self, "fla4")

    def execute(self, context):
        from .ops.path_export import export_nodes

        objects = [o for o in context.selected_objects
                   if o.type == 'MESH' and o.get('path_type', '').startswith('nodes_')]
        if not objects:
            self.report({'ERROR'}, T("Выделите объекты с нодами"))
            return {'CANCELLED'}

        # Group by nodes_filename
        groups = {}  # filename → [objects]
        auto_split = []  # objects without filename
        for obj in objects:
            fname = obj.get('nodes_filename', '')
            if fname:
                groups.setdefault(fname, []).append(obj)
            else:
                auto_split.append(obj)

        exported = 0

        # Export objects with known filename
        for fname, objs in groups.items():
            filepath = os.path.join(self.directory, fname)
            try:
                count = export_nodes(filepath=filepath, objects=objs, fla4=self.fla4)
                exported += count
            except Exception as e:
                self.report({'WARNING'}, f"{fname}: {e}")

        # Auto-split objects by zone (8x8 grid)
        if auto_split:
            from .core.paths import NodesFile, PathNode, write_nodes
            zones = {}  # zone_idx → NodesFile
            for obj in auto_split:
                path_type = obj.get('path_type', '')
                mat_w = obj.matrix_world
                for vert in obj.data.vertices:
                    co = mat_w @ vert.co
                    gx = max(0, min(7, int((co.x + 3000) / 750)))
                    gy = max(0, min(7, int((3000 - co.y) / 750)))
                    zone = gy * 8 + gx
                    if zone not in zones:
                        zones[zone] = NodesFile()
                        zones[zone].fla4 = self.fla4
                    node = PathNode(x=co.x, y=co.y, z=co.z)
                    if path_type == 'nodes_vehicle':
                        zones[zone].vehicle_nodes.append(node)
                    elif path_type == 'nodes_ped':
                        zones[zone].ped_nodes.append(node)

            for zone_idx, nf in zones.items():
                fname = f"nodes{zone_idx}.dat"
                filepath = os.path.join(self.directory, fname)
                try:
                    write_nodes(filepath, nf)
                    exported += len(nf.vehicle_nodes) + len(nf.ped_nodes)
                except Exception as e:
                    self.report({'WARNING'}, f"{fname}: {e}")

        self.report({'INFO'}, f"Nodes: {exported} nodes exported")
        return {'FINISHED'}


class GTATOOLS_OT_import_paths_ipl(bpy.types.Operator):
    """Импорт paths.ipl — пути для gta.dat"""
    bl_idname = "gtatools.import_paths_ipl"
    bl_label = "Import Paths IPL"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.path_import import import_paths_ipl
        try:
            objects = import_paths_ipl(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"Paths IPL: {len(objects)} groups imported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Paths IPL import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_paths_ipl(bpy.types.Operator):
    """Экспорт paths.ipl — пути для gta.dat"""
    bl_idname = "gtatools.export_paths_ipl"
    bl_label = "Export Paths IPL"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "paths_custom.ipl"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.path_export import export_paths_ipl
        try:
            # Selected objects first, then fall back to "Path IPL" collection
            objects = [o for o in context.selected_objects
                       if o.type == 'CURVE' and o.get('path_type') == 'path_ipl']
            if not objects:
                col = bpy.data.collections.get("Path IPL")
                if col:
                    objects = [o for o in col.objects
                               if o.type == 'CURVE' and o.get('path_type') == 'path_ipl']
            count = export_paths_ipl(filepath=self.filepath, objects=objects)
            self.report({'INFO'}, f"Paths IPL: {count} groups exported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Paths IPL export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_convert_to_path(bpy.types.Operator):
    """Конвертировать кривую или рёбра меша в путь paths.ipl"""
    bl_idname = "gtatools.convert_to_path"
    bl_label = "Convert to Path"
    bl_options = {'REGISTER', 'UNDO'}

    group_type: EnumProperty(
        name="Type",
        items=[
            ('1', T("Авто"), ""),
            ('0', T("Пешеходный"), ""),
        ],
        default='1',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        if obj.type == 'CURVE':
            return True
        if obj.type == 'MESH':
            # Allow only if no faces (edges/verts only)
            return len(obj.data.polygons) == 0
        return False

    def execute(self, context):
        obj = context.active_object
        is_veh = self.group_type == '1'

        if obj.type == 'MESH':
            # Convert edges-only mesh to curve first
            if len(obj.data.polygons) > 0:
                self.report({'ERROR'}, T("Нельзя конвертировать меш с полигонами"))
                return {'CANCELLED'}

            # Convert to curve
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.convert(target='CURVE')
            obj = context.active_object  # Now it's a curve

        if obj.type != 'CURVE':
            self.report({'ERROR'}, "Not a curve")
            return {'CANCELLED'}

        # Set path properties
        obj['path_type'] = 'path_ipl'
        obj['group_type'] = int(self.group_type)
        obj['group_index'] = 0
        obj['external_index'] = -1

        # Count real points
        total_pts = sum(len(s.points) if s.type == 'POLY' else len(s.bezier_points)
                        for s in obj.data.splines)
        for i in range(total_pts):
            obj[f'pn_{i}_type'] = 2
            obj[f'pn_{i}_link'] = (i + 1) if i < total_pts - 1 else -1
            obj[f'pn_{i}_area'] = 0
            obj[f'pn_{i}_unk'] = 0.0
            obj[f'pn_{i}_width'] = 1
            obj[f'pn_{i}_ll'] = 1
            obj[f'pn_{i}_rl'] = 1
            obj[f'pn_{i}_mw'] = 0
            obj[f'pn_{i}_flags'] = 1
            obj[f'pn_{i}_spawn'] = 0
        obj['pn_count'] = total_pts

        # Apply curve style
        from .ops.path_import import _setup_path_curve
        _setup_path_curve(obj.data)

        # Material
        mat_name = 'VehiclePath_IPL_Mat' if is_veh else 'PedPath_IPL_Mat'
        color = (0.0, 0.5, 1.0, 0.8) if is_veh else (0.0, 1.0, 0.3, 0.8)
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = bpy.data.materials.new(mat_name)
            mat.use_nodes = True
            for n in mat.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Base Color'].default_value = color
                    break
            mat.diffuse_color = color
        if not obj.data.materials:
            obj.data.materials.append(mat)

        # Move to Path IPL collection
        col = bpy.data.collections.get("Path IPL")
        if not col:
            col = bpy.data.collections.new("Path IPL")
            context.scene.collection.children.link(col)
        # Unlink from current collections
        for c in obj.users_collection:
            c.objects.unlink(obj)
        col.objects.link(obj)

        label = T("Авто") if is_veh else T("Пешеходный")
        self.report({'INFO'}, f"{obj.name} → {label} path ({total_pts} pts)")
        return {'FINISHED'}


class GTATOOLS_OT_add_path_ipl(bpy.types.Operator):
    """Создать новый путь для paths.ipl"""
    bl_idname = "gtatools.add_path_ipl"
    bl_label = "Add Path (IPL)"
    bl_options = {'REGISTER', 'UNDO'}

    group_type: EnumProperty(
        name="Type",
        items=[
            ('1', T("Авто"), T("Автомобильный путь")),
            ('0', T("Пешеходный"), T("Пешеходный путь")),
        ],
        default='1',
    )

    def execute(self, context):
        is_veh = self.group_type == '1'
        prefix = "VehPath" if is_veh else "PedPath"

        curve = bpy.data.curves.new(f"{prefix}_new", type='CURVE')
        curve.dimensions = '3D'
        spline = curve.splines.new('POLY')
        spline.points.add(1)
        loc = context.scene.cursor.location
        spline.points[0].co = (loc.x, loc.y, loc.z, 1.0)
        spline.points[1].co = (loc.x + 30, loc.y, loc.z, 1.0)

        obj = bpy.data.objects.new(f"{prefix}_new", curve)
        obj['path_type'] = 'path_ipl'
        obj['group_type'] = int(self.group_type)
        obj['group_index'] = 0
        obj['external_index'] = -1

        # Default node props for 2 internal nodes
        for i in range(2):
            obj[f'pn_{i}_type'] = 2  # internal
            obj[f'pn_{i}_link'] = (i + 1) if i < 1 else -1
            obj[f'pn_{i}_area'] = 0
            obj[f'pn_{i}_unk'] = 0.0
            obj[f'pn_{i}_width'] = 1
            obj[f'pn_{i}_ll'] = 1
            obj[f'pn_{i}_rl'] = 1
            obj[f'pn_{i}_mw'] = 0
            obj[f'pn_{i}_flags'] = 1
            obj[f'pn_{i}_spawn'] = 0
        obj['pn_count'] = 2

        from .ops.path_import import _setup_path_curve
        _setup_path_curve(curve)
        mat_name = 'VehiclePath_IPL_Mat' if is_veh else 'PedPath_IPL_Mat'
        color = (0.0, 0.5, 1.0, 0.8) if is_veh else (0.0, 1.0, 0.3, 0.8)
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = bpy.data.materials.new(mat_name)
            mat.use_nodes = True
            for n in mat.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Base Color'].default_value = color
                    break
            mat.diffuse_color = color
        curve.materials.append(mat)

        col = bpy.data.collections.get("Path IPL")
        if not col:
            col = bpy.data.collections.new("Path IPL")
            context.scene.collection.children.link(col)
        col.objects.link(obj)

        context.view_layer.objects.active = obj
        obj.select_set(True)

        label = T("Авто") if is_veh else T("Пешеходный")
        self.report({'INFO'}, f"{label} path created. Edit in Edit Mode, max 12 points")
        return {'FINISHED'}


class GTATOOLS_OT_add_track(bpy.types.Operator):
    """Создать новый ж/д путь (кривая)"""
    bl_idname = "gtatools.add_track"
    bl_label = "Add Train Track"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        curve = bpy.data.curves.new("Track_New", type='CURVE')
        curve.dimensions = '3D'
        spline = curve.splines.new('POLY')
        # Start with 2 points at cursor
        spline.points.add(1)
        loc = context.scene.cursor.location
        spline.points[0].co = (loc.x, loc.y, loc.z, 1.0)
        spline.points[1].co = (loc.x + 50, loc.y, loc.z, 1.0)
        spline.use_cyclic_u = True

        obj = bpy.data.objects.new("Track_New", curve)
        obj['path_type'] = 'track'
        obj['station_indices'] = '[]'

        from .ops.path_import import _setup_path_curve
        _setup_path_curve(curve)

        # Material
        mat = bpy.data.materials.get('TrainTrack_Mat')
        if not mat:
            mat = bpy.data.materials.new('TrainTrack_Mat')
            mat.use_nodes = True
            for n in mat.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Base Color'].default_value = (0.6, 0.3, 0.0, 0.8)
                    break
            mat.diffuse_color = (0.6, 0.3, 0.0, 0.8)
        curve.materials.append(mat)

        col = bpy.data.collections.get("Train Tracks")
        if not col:
            col = bpy.data.collections.new("Train Tracks")
            context.scene.collection.children.link(col)
        col.objects.link(obj)

        context.view_layer.objects.active = obj
        obj.select_set(True)

        self.report({'INFO'}, T("Ж/д путь создан. Редактируйте в Edit Mode"))
        return {'FINISHED'}


class GTATOOLS_OT_add_vehicle_path(bpy.types.Operator):
    """Создать новый автомобильный путь (меш с вершинами)"""
    bl_idname = "gtatools.add_vehicle_path"
    bl_label = "Add Vehicle Path"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh = bpy.data.meshes.new("VehiclePath_New")
        loc = context.scene.cursor.location
        verts = [(loc.x, loc.y, loc.z), (loc.x + 20, loc.y, loc.z)]
        edges = [(0, 1)]
        mesh.from_pydata(verts, edges, [])
        mesh.update()

        obj = bpy.data.objects.new("VehiclePath_New", mesh)
        obj['path_type'] = 'nodes_vehicle'

        # Store default node props
        for i in range(2):
            obj[f'node_{i}_link'] = 0
            obj[f'node_{i}_area'] = 0
            obj[f'node_{i}_id'] = i
            obj[f'node_{i}_width'] = 4
            obj[f'node_{i}_type'] = 0
            obj[f'node_{i}_flags'] = 0

        mat = bpy.data.materials.get('VehicleNode_Mat')
        if not mat:
            mat = bpy.data.materials.new('VehicleNode_Mat')
            mat.use_nodes = True
            for n in mat.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Base Color'].default_value = (0.0, 0.5, 1.0, 0.8)
                    break
            mat.diffuse_color = (0.0, 0.5, 1.0, 0.8)
        mesh.materials.append(mat)

        col = bpy.data.collections.get("Path Nodes")
        if not col:
            col = bpy.data.collections.new("Path Nodes")
            context.scene.collection.children.link(col)
        col.objects.link(obj)

        context.view_layer.objects.active = obj
        obj.select_set(True)

        self.report({'INFO'}, T("Авто путь создан. Добавляйте вершины в Edit Mode"))
        return {'FINISHED'}


class GTATOOLS_OT_add_ped_path(bpy.types.Operator):
    """Создать новый пешеходный путь (меш с вершинами)"""
    bl_idname = "gtatools.add_ped_path"
    bl_label = "Add Ped Path"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh = bpy.data.meshes.new("PedPath_New")
        loc = context.scene.cursor.location
        verts = [(loc.x, loc.y, loc.z), (loc.x + 10, loc.y, loc.z)]
        edges = [(0, 1)]
        mesh.from_pydata(verts, edges, [])
        mesh.update()

        obj = bpy.data.objects.new("PedPath_New", mesh)
        obj['path_type'] = 'nodes_ped'

        for i in range(2):
            obj[f'node_{i}_link'] = 0
            obj[f'node_{i}_area'] = 0
            obj[f'node_{i}_id'] = i
            obj[f'node_{i}_width'] = 2
            obj[f'node_{i}_type'] = 0
            obj[f'node_{i}_flags'] = 0

        mat = bpy.data.materials.get('PedNode_Mat')
        if not mat:
            mat = bpy.data.materials.new('PedNode_Mat')
            mat.use_nodes = True
            for n in mat.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Base Color'].default_value = (0.0, 1.0, 0.3, 0.8)
                    break
            mat.diffuse_color = (0.0, 1.0, 0.3, 0.8)
        mesh.materials.append(mat)

        col = bpy.data.collections.get("Path Nodes")
        if not col:
            col = bpy.data.collections.new("Path Nodes")
            context.scene.collection.children.link(col)
        col.objects.link(obj)

        context.view_layer.objects.active = obj
        obj.select_set(True)

        self.report({'INFO'}, T("Пешеходный путь создан. Добавляйте вершины в Edit Mode"))
        return {'FINISHED'}


class GTATOOLS_OT_mark_station(bpy.types.Operator):
    """Отметить/снять выбранные точки кривой как станции (flag=1)"""
    bl_idname = "gtatools.mark_station"
    bl_label = "Toggle Station"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'CURVE' and obj.get('path_type') == 'track'
                and context.mode == 'EDIT_CURVE')

    def execute(self, context):
        obj = context.active_object
        raw = obj.get('station_indices', '[]')
        try:
            stations = set(eval(raw))
        except Exception:
            stations = set()

        # Toggle selected points
        idx = 0
        toggled = 0
        for spline in obj.data.splines:
            for point in spline.points:
                if point.select:
                    if idx in stations:
                        stations.discard(idx)
                    else:
                        stations.add(idx)
                    toggled += 1
                idx += 1

        obj['station_indices'] = str(sorted(stations))
        self.report({'INFO'}, f"{toggled} points toggled, {len(stations)} stations total")
        return {'FINISHED'}


class GTATOOLS_PT_export_panel(bpy.types.Panel):
    """Панель экспорта/импорта GTA моделей"""
    bl_label = T("Экспорт / Импорт")
    bl_idname = "GTATOOLS_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        # Ищем модели среди выделенных объектов
        models = find_selected_models()
        selected_count = len([o for o in context.selected_objects if o.type == 'MESH'])

        box = layout.box()
        box.label(text=f"{T('Выделено')}: {selected_count} {T('меш(ей)')}", icon='OBJECT_DATA')

        col = box.column()
        col.label(text=f"DFF: {models['DFF'].name}" if models['DFF'] else "DFF: -",
                 icon='CHECKMARK' if models['DFF'] else 'X')
        col.label(text=f"LOD: {models['LOD'].name}" if models['LOD'] else "LOD: -",
                 icon='CHECKMARK' if models['LOD'] else 'X')
        col.label(text=f"COL: {models['COL'].name}" if models['COL'] else "COL: -",
                 icon='CHECKMARK' if models['COL'] else 'X')

        # DFF
        row = layout.row(align=True)
        row.operator("gtatools.import_dff", text=T("Импорт DFF"), icon='IMPORT')
        row.operator("gtatools.export_dff", text=T("Экспорт DFF"), icon='EXPORT')

        # COL
        row = layout.row(align=True)
        row.operator("gtatools.import_col", text=T("Импорт COL"), icon='IMPORT')
        row.operator("gtatools.export_col", text=T("Экспорт COL"), icon='EXPORT')

        # CST (Steve's COL Editor text format)
        row = layout.row(align=True)
        _rock_id = _icons.get_icon("rock")
        if _rock_id:
            row.operator("gtatools.import_cst", text=T("Импорт CST"),
                         icon_value=_rock_id)
            row.operator("gtatools.export_cst", text=T("Экспорт CST"),
                         icon_value=_rock_id)
        else:
            row.operator("gtatools.import_cst", text=T("Импорт CST"), icon='IMPORT')
            row.operator("gtatools.export_cst", text=T("Экспорт CST"), icon='EXPORT')

        # TXD
        row = layout.row(align=True)
        row.operator("gtatools.import_txd", text=T("Импорт TXD"), icon='IMPORT')
        row.operator("gtatools.export_txd", text=T("Экспорт TXD"), icon='EXPORT')

        # Shared TXD — single TXD for multiple DFFs
        row = layout.row(align=True)
        row.prop(context.scene, "gtatools_shared_txd_name", text="")
        row.operator("gtatools.export_shared_txd", text=T("Общий TXD"), icon='PACKAGE')

        # Auto TXD + GPU status
        row = layout.row(align=True)
        row.prop(context.scene, "gtatools_txd_auto_import", text=T("Авто TXD"))
        nvtt_path = getattr(context.scene, 'gtatools_nvtt_path', '')
        available, _ = check_nvtt_available(nvtt_path)
        if available:
            row.label(text="GPU (NVTT)", icon='CHECKMARK')
        else:
            row.label(text="CPU", icon='INFO')

        layout.separator()

        # Vehicle tools
        _ruler_id = _icons.get_icon("ruler")
        if _ruler_id:
            layout.operator("gtatools.vehicle_scale",
                            text=T("Масштаб машины…"),
                            icon_value=_ruler_id)
        else:
            layout.operator("gtatools.vehicle_scale",
                            text=T("Масштаб машины…"),
                            icon='FULLSCREEN_ENTER')

        layout.separator()

        # Export All
        layout.operator("gtatools.export_all", text=T("Экспорт всего (DFF+COL+LOD+TXD)"), icon='EXPORT')
        row = layout.row(align=True)
        row.prop(context.scene, "gtatools_export_all_dff", text="DFF", toggle=True)
        row.prop(context.scene, "gtatools_export_all_col", text="COL", toggle=True)
        row.prop(context.scene, "gtatools_export_all_lod", text="LOD", toggle=True)
        row.prop(context.scene, "gtatools_export_all_txd", text="TXD", toggle=True)

        # Pipeline + Normals
        _draw_label_with_info(layout, "Pipeline:",
            T("None — без pipeline\nVehicle — машины (отражения кузова, env map)\nBuilding DN — здания с day/night vertex colors\nBuilding — обычные здания\n\nNormals — динамическое освещение движком (персонажи, транспорт, оружие)\nОтключить для зданий и объектов карты (используют vertex colors)"))
        row = layout.row(align=True)
        row.prop_enum(context.scene, "gtatools_export_pipeline", 'NONE')
        row.prop_enum(context.scene, "gtatools_export_pipeline", '0x53F2009A')
        row.prop_enum(context.scene, "gtatools_export_pipeline", '0x53F20098')
        row.prop_enum(context.scene, "gtatools_export_pipeline", '0x53F2009C')
        obj = context.active_object
        if obj and obj.type == 'MESH' and hasattr(obj, 'inu'):
            inu = obj.inu
            row = layout.row(align=True)
            row.prop(context.scene, "gtatools_show_dff_flags",
                     icon='TRIA_DOWN' if context.scene.gtatools_show_dff_flags else 'TRIA_RIGHT',
                     text="DFF Flags", emboss=False)
            if context.scene.gtatools_show_dff_flags:
                fbox = layout.box()
                fc = fbox.column(align=True)
                fc.prop(inu, "export_normals", text="Normals")
                fc.prop(inu, "light", text="Light")
                fc.prop(inu, "modulate_color", text="Modulate Color")
                fc.prop(inu, "set_material_alpha", text="Set Material Alpha")
                fc.prop(inu, "light_beam_asi", text="Light Beam (SA_Light.asi)")
                fc.prop(inu, "export_binsplit", text="Bin Mesh PLG")
                fc.prop(inu, "uv_map1", text="UV1")
                fc.prop(inu, "uv_map2", text="UV2")
                fc.prop(inu, "day_cols", text="Day")
                fc.prop(inu, "night_cols", text="Night")





_hide_dff = False
_hide_lod = False
_hide_col = False


class GTATOOLS_OT_toggle_visibility(bpy.types.Operator):
    """Скрыть/показать DFF, LOD или COL объекты во всей сцене"""
    bl_idname = "gtatools.toggle_visibility"
    bl_label = "Toggle Visibility"
    bl_options = {'REGISTER'}

    model_type: StringProperty()

    def execute(self, context):
        global _hide_dff, _hide_lod, _hide_col
        from .tools.model_utils import get_model_type

        if self.model_type == 'DFF':
            _hide_dff = not _hide_dff
            hide = _hide_dff
        elif self.model_type == 'LOD':
            _hide_lod = not _hide_lod
            hide = _hide_lod
        elif self.model_type == 'COL':
            _hide_col = not _hide_col
            hide = _hide_col
        else:
            return {'CANCELLED'}

        count = 0
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            mt, _ = get_model_type(obj)
            if mt == self.model_type:
                obj.hide_viewport = hide
                count += 1

        self.report({'INFO'}, f"{self.model_type}: {'Hidden' if hide else 'Visible'} ({count})")
        return {'FINISHED'}


class GTATOOLS_OT_snap_to_dff(bpy.types.Operator):
    """Подтянуть LOD и COL к позиции DFF модели"""
    bl_idname = "gtatools.snap_to_dff"
    bl_label = "Snap LOD/COL to DFF"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .tools.model_utils import get_model_type

        # Group all scene meshes by base name
        groups = {}
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            mt, base = get_model_type(obj)
            if not base:
                continue
            base_clean = base.rstrip('_').lower()
            if base_clean not in groups:
                groups[base_clean] = {'DFF': None, 'LOD': None, 'COL': None}
            if mt and groups[base_clean][mt] is None:
                groups[base_clean][mt] = obj

        snapped = 0
        for base, g in groups.items():
            dff = g['DFF']
            if not dff:
                continue
            for mt in ('LOD', 'COL'):
                other = g[mt]
                if other and other.location != dff.location:
                    other.location = dff.location.copy()
                    other.rotation_mode = dff.rotation_mode
                    if dff.rotation_mode == 'QUATERNION':
                        other.rotation_quaternion = dff.rotation_quaternion.copy()
                    else:
                        other.rotation_euler = dff.rotation_euler.copy()
                    snapped += 1

        self.report({'INFO'}, f"{T('Перемещено:')} {snapped}")
        return {'FINISHED'}


class GTATOOLS_PT_check_panel(bpy.types.Panel):
    """Панель проверки геометрии и материалов"""
    bl_label = T("Проверка")
    bl_idname = "GTATOOLS_PT_check_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.operator("gtatools.check_geometry", text=T("Проверка вершин"), icon='VIEWZOOM')
        row.operator("gtatools.check_ngons", text=T("Проверка N-gon"), icon='MESH_DATA')
        layout.operator("gtatools.check_materials", text=T("Проверка материалов"), icon='MATERIAL')
        layout.operator("gtatools.cleanup_materials", text=T("Очистка материалов"), icon='BRUSH_DATA')
        layout.operator("gtatools.sort_materials", text=T("Сортировка материалов"), icon='SORTALPHA')
        layout.operator("gtatools.reset_transform", text=T("Сброс трансформ"), icon='EMPTY_AXIS')
        layout.separator()
        layout.operator("gtatools.snap_to_dff", text=T("LOD/COL → DFF"), icon='SNAP_ON')
        row = layout.row(align=True)
        op = row.operator("gtatools.toggle_visibility", text="DFF",
                          icon='HIDE_ON' if _hide_dff else 'HIDE_OFF', depress=_hide_dff)
        op.model_type = 'DFF'
        op = row.operator("gtatools.toggle_visibility", text="LOD",
                          icon='HIDE_ON' if _hide_lod else 'HIDE_OFF', depress=_hide_lod)
        op.model_type = 'LOD'
        op = row.operator("gtatools.toggle_visibility", text="COL",
                          icon='HIDE_ON' if _hide_col else 'HIDE_OFF', depress=_hide_col)
        op.model_type = 'COL'
        # Batch set type
        row = layout.row(align=True)
        row.label(text=T("Тип:"))
        for _t in ('OBJ', 'COL', 'SHA', 'NON'):
            op = row.operator("gtatools.batch_set_type", text=_t)
            op.obj_type = _t


# ── 2DFX Light Presets ──
_2DFX_PRESETS = {
    'Default': dict(color=[255,255,255,255], corona_size=1.0, corona_far_clip=100.0,
                    pointlight_range=18.0, corona_tex='coronastar', corona_show_mode=0,
                    corona_flare_type=0, corona_enable_reflection=0, shadow_size=8.0,
                    shadow_z_distance=0, shadow_color_multiplier=40, shadow_tex='shad_exp',
                    flags1=96, flags2=0),
    'OnAllDay': dict(color=[255,255,255,255], corona_size=1.0, corona_far_clip=100.0,
                     pointlight_range=18.0, corona_tex='coronastar', corona_show_mode=0,
                     corona_flare_type=0, corona_enable_reflection=0, shadow_size=8.0,
                     shadow_z_distance=0, shadow_color_multiplier=40, shadow_tex='shad_exp',
                     flags1=96, flags2=0),
    'Lamp Post': dict(color=[255,255,171,255], corona_size=1.5, corona_far_clip=200.0,
                      pointlight_range=16.0, corona_tex='coronastar', corona_show_mode=0,
                      corona_flare_type=0, corona_enable_reflection=1, shadow_size=10.0,
                      shadow_z_distance=0, shadow_color_multiplier=40, shadow_tex='shad_exp',
                      flags1=64, flags2=0),
    'Lamp Post Coast': dict(color=[255,217,163,255], corona_size=1.2, corona_far_clip=200.0,
                            pointlight_range=14.0, corona_tex='coronamoon', corona_show_mode=0,
                            corona_flare_type=0, corona_enable_reflection=1, shadow_size=8.0,
                            shadow_z_distance=0, shadow_color_multiplier=40, shadow_tex='shad_exp',
                            flags1=64, flags2=0),
    'BB Pickup': dict(color=[255,0,0,255], corona_size=0.8, corona_far_clip=80.0,
                      pointlight_range=8.0, corona_tex='coronastar', corona_show_mode=0,
                      corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                      shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                      flags1=96, flags2=0),
    'Flashing (Maverick1)': dict(color=[255,0,0,255], corona_size=0.5, corona_far_clip=200.0,
                                 pointlight_range=0.0, corona_tex='coronastar', corona_show_mode=1,
                                 corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                                 shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                                 flags1=96, flags2=0),
    'Flashing (Maverick2)': dict(color=[0,255,0,255], corona_size=0.5, corona_far_clip=200.0,
                                 pointlight_range=0.0, corona_tex='coronastar', corona_show_mode=1,
                                 corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                                 shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                                 flags1=96, flags2=0),
    'Flashing (Tug)': dict(color=[255,128,0,255], corona_size=0.4, corona_far_clip=150.0,
                           pointlight_range=0.0, corona_tex='coronastar', corona_show_mode=1,
                           corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                           shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                           flags1=96, flags2=0),
    'Train Crossing': dict(color=[255,0,0,255], corona_size=1.0, corona_far_clip=200.0,
                           pointlight_range=12.0, corona_tex='coronastar', corona_show_mode=1,
                           corona_flare_type=0, corona_enable_reflection=1, shadow_size=0.0,
                           shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                           flags1=96, flags2=0),
    'Traffic': dict(color=[255,0,0,255], corona_size=0.7, corona_far_clip=120.0,
                    pointlight_range=6.0, corona_tex='coronastar', corona_show_mode=0,
                    corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                    shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                    flags1=96, flags2=0),
}

_PRESET_NAMES = list(_2DFX_PRESETS.keys())


# Map EnumProperty identifiers to preset dict keys
_PRESET_MAP = {
    'DEFAULT': 'Default',
    'ONALLDAY': 'OnAllDay',
    'LAMP_POST': 'Lamp Post',
    'LAMP_POST_COAST': 'Lamp Post Coast',
    'BB_PICKUP': 'BB Pickup',
    'FLASHING_MAV1': 'Flashing (Maverick1)',
    'FLASHING_MAV2': 'Flashing (Maverick2)',
    'FLASHING_TUG': 'Flashing (Tug)',
    'TRAIN_CROSSING': 'Train Crossing',
    'TRAFFIC': 'Traffic',
}


class GTATOOLS_OT_apply_2dfx_preset(bpy.types.Operator):
    """Применить пресет 2DFX к активному объекту"""
    bl_idname = "gtatools.apply_2dfx_preset"
    bl_label = "Apply 2DFX Preset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'EMPTY':
            self.report({'WARNING'}, "No 2DFX object selected")
            return {'CANCELLED'}
        inu = obj.inu
        preset_key = _PRESET_MAP.get(inu.preset_2dfx, 'Default')
        p = _2DFX_PRESETS[preset_key]

        inu.color_2dfx = (p['color'][0] / 255.0, p['color'][1] / 255.0,
                          p['color'][2] / 255.0, p['color'][3] / 255.0)
        obj['2dfx_corona_size'] = p['corona_size']
        obj['2dfx_corona_far_clip'] = p['corona_far_clip']
        obj['2dfx_pointlight_range'] = p['pointlight_range']
        obj['2dfx_corona_enable_reflection'] = p['corona_enable_reflection']
        obj['2dfx_shadow_size'] = p['shadow_size']
        obj['2dfx_shadow_z_distance'] = p['shadow_z_distance']
        obj['2dfx_shadow_color_multiplier'] = p['shadow_color_multiplier']
        obj['2dfx_flags1'] = p['flags1']
        obj['2dfx_flags2'] = p['flags2']
        # Set EnumProperty values
        inu.corona_tex_2dfx = p['corona_tex']
        inu.shadow_tex_2dfx = p['shadow_tex']
        inu.show_mode_2dfx = str(p['corona_show_mode'])
        inu.flare_type_2dfx = str(p['corona_flare_type'])

        self.report({'INFO'}, f"Preset '{preset_key}' applied")
        return {'FINISHED'}


class GTATOOLS_OT_create_2dfx(bpy.types.Operator):
    """Создать 2DFX эффект с настройками по умолчанию"""
    bl_idname = "gtatools.create_2dfx"
    bl_label = "Create 2DFX Effect"
    bl_options = {'REGISTER', 'UNDO'}

    effect_type: EnumProperty(
        items=[
            ('LIGHT', 'Light', 'Street light / corona'),
            ('PARTICLE', 'Particle', 'Particle effect'),
            ('PED_ATTRACTOR', 'Ped Attractor', 'Ped attractor point'),
            ('SUN_GLARE', 'Sun Glare', 'Sun glare on surface'),
        ],
        default='LIGHT',
    )

    def execute(self, context):
        cursor_loc = context.scene.cursor.location

        display_map = {
            'LIGHT': ('PLAIN_AXES', 0.3),
            'PARTICLE': ('CIRCLE', 0.2),
            'PED_ATTRACTOR': ('CUBE', 0.15),
            'SUN_GLARE': ('SPHERE', 0.1),
        }
        display_type, display_size = display_map[self.effect_type]

        name = f"2dfx_{self.effect_type.lower()}"
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = display_type
        obj.empty_display_size = display_size
        obj.location = cursor_loc

        obj.inu.type = '2DFX'
        obj.inu.effect_2dfx = self.effect_type

        # Создаём дефолтные custom properties
        if self.effect_type == 'LIGHT':
            obj.inu.color_2dfx = (1.0, 1.0, 1.0, 1.0)  # white
            obj['2dfx_corona_far_clip'] = 100.0
            obj['2dfx_pointlight_range'] = 18.0
            obj['2dfx_corona_size'] = 1.0
            obj['2dfx_shadow_size'] = 8.0
            obj['2dfx_corona_enable_reflection'] = 0
            obj['2dfx_shadow_color_multiplier'] = 40
            obj['2dfx_flags1'] = 96  # AT_DAY + AT_NIGHT
            obj['2dfx_shadow_z_distance'] = 0
            obj['2dfx_flags2'] = 0
            # Set display precision for float properties
            for key in ('2dfx_corona_far_clip', '2dfx_pointlight_range',
                        '2dfx_corona_size', '2dfx_shadow_size'):
                ui = obj.id_properties_ui(key)
                ui.update(precision=1)
        elif self.effect_type == 'PARTICLE':
            obj['2dfx_effect_name'] = ""
        elif self.effect_type == 'PED_ATTRACTOR':
            obj['2dfx_attractor_type'] = 0
            obj['2dfx_rotation_matrix'] = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
            obj['2dfx_external_script'] = ""
            obj['2dfx_ped_probability'] = 0

        # Link to dedicated 2DFX collection (auto-create if missing)
        col_name = "2DFX"
        if col_name in bpy.data.collections:
            fx_col = bpy.data.collections[col_name]
        else:
            fx_col = bpy.data.collections.new(col_name)
            context.scene.collection.children.link(fx_col)
        fx_col.objects.link(obj)

        # Визуальный превью
        if self.effect_type == 'LIGHT':
            from .ops.fx_preview import create_light_preview
            create_light_preview(obj)
        elif self.effect_type == 'PARTICLE':
            from .ops.fx_preview import create_particle_preview
            create_particle_preview(obj)

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        self.report({'INFO'}, f"2DFX {self.effect_type} created")
        return {'FINISHED'}


class GTATOOLS_OT_refresh_2dfx_preview(bpy.types.Operator):
    """Обновить визуальный превью (свет + корона + тень) для выбранного 2DFX"""
    bl_idname = "gtatools.refresh_2dfx_preview"
    bl_label = "Refresh Preview"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX'
                and obj.inu.effect_2dfx in ('LIGHT', 'PARTICLE'))

    def execute(self, context):
        obj = context.active_object
        if obj.inu.effect_2dfx == 'LIGHT':
            from .ops.fx_preview import update_light_preview
            update_light_preview(obj)
        else:
            from .ops.fx_preview import update_particle_preview
            update_particle_preview(obj)
        self.report({'INFO'}, "2DFX preview updated")
        return {'FINISHED'}


class GTATOOLS_OT_remove_2dfx_preview(bpy.types.Operator):
    """Удалить визуальный превью из выбранного 2DFX"""
    bl_idname = "gtatools.remove_2dfx_preview"
    bl_label = "Remove Preview"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX')

    def execute(self, context):
        from .ops.fx_preview import remove_preview_children
        remove_preview_children(context.active_object)
        self.report({'INFO'}, "2DFX preview removed")
        return {'FINISHED'}


def _particle_effect_items(self, context):
    """Enum items callback — lazily loads effects.fxp from the game root."""
    from .core import fxp as _fxp
    game_root = bpy.path.abspath(getattr(context.scene, 'gtatools_game_root', '') or '')
    if not game_root or not os.path.isdir(game_root):
        return [('', T("<Game Root не задан>"), "")]
    path = os.path.join(game_root, 'models', 'effects.fxp')
    if not os.path.isfile(path):
        return [('', T("<effects.fxp не найден>"), "")]
    try:
        fxf = _fxp.load_cached(path)
    except Exception as ex:
        return [('', f"<ошибка: {ex}>", "")]
    return [(s.name, s.name, "") for s in fxf.systems]


class GTATOOLS_OT_select_particle_effect(bpy.types.Operator):
    """Выбрать имя эффекта из effects.fxp"""
    bl_idname = "gtatools.select_particle_effect"
    bl_label = "Select Particle Effect"
    bl_property = "effect_name"
    bl_options = {'REGISTER', 'UNDO'}

    effect_name: EnumProperty(
        name="Effect",
        items=_particle_effect_items,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX'
                and obj.inu.effect_2dfx == 'PARTICLE')

    def execute(self, context):
        obj = context.active_object
        if obj is not None and self.effect_name:
            obj['2dfx_effect_name'] = self.effect_name
            from .ops.fx_preview import update_particle_preview
            update_particle_preview(obj)
            self.report({'INFO'}, f"2DFX effect: {self.effect_name}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}


def _get_current_emitter(obj):
    """Return (fxf, system, emitter) for the obj's current effect+emitter, or None."""
    effect_name = obj.get('2dfx_effect_name', '') or ''
    if not effect_name:
        return None
    game_root = bpy.path.abspath(
        getattr(bpy.context.scene, 'gtatools_game_root', '') or ''
    )
    if not game_root:
        return None
    fxp_path = os.path.join(game_root, 'models', 'effects.fxp')
    if not os.path.isfile(fxp_path):
        return None
    from .core import fxp as _fxp
    fxf = _fxp.load_cached(fxp_path)
    system = fxf.find(effect_name)
    if not system or not system.emitters:
        return None
    idx = max(0, min(int(obj.inu.particle_emitter_index), len(system.emitters) - 1))
    return fxf, system, system.emitters[idx]


def _load_curve_into_buffer(obj, curve_key: str) -> bool:
    """Parse 'INFO.FIELD' and populate obj.inu.particle_curve_keys."""
    if '.' not in curve_key:
        return False
    info_type, field_name = curve_key.split('.', 1)

    result = _get_current_emitter(obj)
    if not result:
        return False
    _fxf, _system, em = result

    info = em.info(info_type)
    if not info:
        return False
    curve = info.curves.get(field_name)
    if not curve:
        return False

    obj.inu.particle_curve_keys.clear()
    for kf in curve.keys:
        item = obj.inu.particle_curve_keys.add()
        item.time = float(kf.time)
        item.val = float(kf.val)
    obj.inu.particle_curve_key_index = 0
    return True


# Curve picker — search popup of all curves in current emitter.
_particle_curve_items_cache = [('', '<none>', '')]


def _particle_curve_items(self, context):
    global _particle_curve_items_cache
    obj = context.active_object
    if not obj:
        _particle_curve_items_cache = [('', '<no object>', '')]
        return _particle_curve_items_cache
    result = _get_current_emitter(obj)
    if not result:
        _particle_curve_items_cache = [('', '<no emitter>', '')]
        return _particle_curve_items_cache
    _fxf, _system, em = result
    items = []
    for info in em.infos:
        for field_name in info.curves.keys():
            key = f"{info.type}.{field_name}"
            items.append((key, key, ""))
    if not items:
        items = [('', '<no curves>', '')]
    _particle_curve_items_cache = items
    return _particle_curve_items_cache


def _create_blank_particle_system(name: str):
    """Return a brand-new FXSystem with sensible defaults — single emitter,
    a 'sphere' texture, basic emission/colour/size info blocks set to neutral
    values. Everything is plain Python objects from core.fxp; no Blender state.
    """
    from .core.fxp import (
        FXSystem, FXEmitter, FXInfoBlock, FXCurve, FXKeyframe,
    )

    system = FXSystem()
    system.version = "109"
    system.header = [
        ('FILENAME', f'X:\\INU\\effects\\particles/{name}.fxs'),
        ('NAME', name),
        ('LENGTH', '1.000'),
        ('LOOPINTERVALMIN', '0.000'),
        ('LENGTH', '0.000'),
        ('PLAYMODE', '2'),
        ('CULLDIST', '50.000'),
        ('BOUNDINGSPHERE', '0.0 0.0 0.0 0.0'),
    ]
    system.footer = [
        ('OMITTEXTURES', '0'),
        ('TXDNAME', 'NOTXDSET'),
    ]

    em = FXEmitter()
    em.base = [
        ('NAME', 'ParticleEmitter'),
        ('MATRIX', '1.000 0.000 0.000 0.000 1.000 0.000 0.000 0.000 1.000 0.000 0.000 0.000 '),
        ('TEXTURE', 'sphere'),
        ('TEXTURE2', 'NULL'),
        ('TEXTURE3', 'NULL'),
        ('TEXTURE4', 'NULL'),
        ('ALPHAON', '1'),
        ('SRCBLENDID', '4'),
        ('DSTBLENDID', '5'),
    ]
    em.footer = [
        ('LODSTART', '30.000'),
        ('LODEND', '50.000'),
    ]

    def _single(val):
        return FXCurve(looped=0, keys=[FXKeyframe(time=0.0, val=float(val))])

    def _start_end(a, b):
        return FXCurve(looped=0, keys=[
            FXKeyframe(time=0.0, val=float(a)),
            FXKeyframe(time=1.0, val=float(b)),
        ])

    # Emission: EMLIFE, EMRATE, EMSPEED, EMDIR
    em.infos.append(FXInfoBlock(
        type='EMLIFE',
        curves={'LIFE': _single(1.0), 'BIAS': _single(0.0)},
    ))
    em.infos.append(FXInfoBlock(
        type='EMRATE',
        curves={'RATE': _single(10.0)},
    ))
    em.infos.append(FXInfoBlock(
        type='EMSPEED',
        curves={'SPEED': _single(1.0), 'BIAS': _single(0.0)},
    ))
    em.infos.append(FXInfoBlock(
        type='EMDIR',
        curves={'DIRX': _single(0.0), 'DIRY': _single(0.0), 'DIRZ': _single(1.0)},
    ))

    # Rendering: SIZE, COLOUR (white, full alpha → white, zero alpha for fade-out)
    em.infos.append(FXInfoBlock(
        type='SIZE',
        scalars=[('TIMEMODEPRT', '1')],
        curves={
            'SIZEX': _start_end(0.3, 0.5),
            'SIZEY': _start_end(0.3, 0.5),
            'SIZEXBIAS': _single(0.0),
            'SIZEYBIAS': _single(0.0),
        },
    ))
    em.infos.append(FXInfoBlock(
        type='COLOUR',
        scalars=[('TIMEMODEPRT', '1')],
        curves={
            'RED': _start_end(255.0, 255.0),
            'GREEN': _start_end(255.0, 255.0),
            'BLUE': _start_end(255.0, 255.0),
            'ALPHA': _start_end(255.0, 0.0),
        },
    ))

    system.emitters.append(em)
    return system


class GTATOOLS_OT_particle_effect_new(bpy.types.Operator):
    """Создать новый пустой эффект в effects.fxp"""
    bl_idname = "gtatools.particle_effect_new"
    bl_label = "New Particle Effect"
    bl_options = {'REGISTER'}

    effect_name: StringProperty(
        name="Name",
        description=T("Имя нового эффекта (должно быть уникальным)"),
        default="prt_custom",
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX'
                and obj.inu.effect_2dfx == 'PARTICLE')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=340)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'effect_name')
        layout.label(text=T("Создастся пустая система с одним эмиттером"), icon='INFO')
        layout.label(text=T("Текстура: sphere. Жизнь 1с, rate 10/с, цвет белый"))

    def execute(self, context):
        obj = context.active_object
        name = self.effect_name.strip()
        if not name:
            self.report({'ERROR'}, T("Имя пустое"))
            return {'CANCELLED'}

        game_root = bpy.path.abspath(context.scene.gtatools_game_root or '')
        if not game_root:
            self.report({'ERROR'}, "Game Root не задан")
            return {'CANCELLED'}
        fxp_path = os.path.join(game_root, 'models', 'effects.fxp')
        if not os.path.isfile(fxp_path):
            self.report({'ERROR'}, f"effects.fxp не найден: {fxp_path}")
            return {'CANCELLED'}

        # Auto-backup on first write
        backup_path = fxp_path + '.bak'
        if not os.path.isfile(backup_path):
            import shutil
            try:
                shutil.copy2(fxp_path, backup_path)
                print(f"[FXP] backed up to {backup_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Не удалось создать бэкап: {e}")
                return {'CANCELLED'}

        from .core import fxp as _fxp
        try:
            fxf = _fxp.read_fxp(fxp_path)
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка парсинга: {e}")
            return {'CANCELLED'}

        if fxf.find(name) is not None:
            self.report({'ERROR'}, f"Эффект '{name}' уже существует")
            return {'CANCELLED'}

        new_system = _create_blank_particle_system(name)
        fxf.systems.append(new_system)

        try:
            _fxp.write_fxp(fxp_path, fxf)
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка записи: {e}")
            return {'CANCELLED'}

        _fxp.clear_cache()
        # Force the enum to rebuild its cached item list on next draw
        global _particle_enum_cache_key
        _particle_enum_cache_key = None

        # Switch the object to the newly created effect
        obj['2dfx_effect_name'] = name
        obj.inu.particle_emitter_index = 0
        try:
            _populate_particle_props_from_fxp(obj, name, 0)
        except Exception as e:
            print(f"[2DFX Particle] populate failed: {e}")
        try:
            from .ops.fx_preview import update_particle_preview
            update_particle_preview(obj)
        except Exception:
            pass

        self.report({'INFO'}, f"Создан эффект: {name}")
        return {'FINISHED'}


class GTATOOLS_OT_particle_effect_delete(bpy.types.Operator):
    """Удалить текущий эффект из effects.fxp (с автобэкапом)"""
    bl_idname = "gtatools.particle_effect_delete"
    bl_label = "Delete Particle Effect"
    bl_options = {'REGISTER'}

    confirm: BoolProperty(
        name=T("Я понимаю что это перезапишет effects.fxp"),
        default=False,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX'
                and obj.inu.effect_2dfx == 'PARTICLE'
                and (obj.get('2dfx_effect_name', '') or ''))

    def invoke(self, context, event):
        self.confirm = False
        return context.window_manager.invoke_props_dialog(self, width=380)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        name = obj.get('2dfx_effect_name', '') or ''
        layout.label(text=T(f"Удалить '{name}' из effects.fxp?"), icon='ERROR')
        layout.label(text=T("Действие необратимо (хотя есть .bak)"), icon='INFO')

        # Warn if other scene objects reference the same effect
        count = 0
        for o in bpy.data.objects:
            if o.type != 'EMPTY':
                continue
            inu = getattr(o, 'inu', None)
            if not inu or inu.type != '2DFX' or inu.effect_2dfx != 'PARTICLE':
                continue
            if (o.get('2dfx_effect_name', '') or '') == name:
                count += 1
        if count > 1:
            layout.label(
                text=T(f"⚠ {count} объектов в сцене используют этот эффект"),
                icon='ERROR',
            )

        layout.prop(self, 'confirm')

    def execute(self, context):
        if not self.confirm:
            self.report({'WARNING'}, T("Подтверждение не получено"))
            return {'CANCELLED'}

        obj = context.active_object
        name = (obj.get('2dfx_effect_name', '') or '').strip()
        if not name:
            self.report({'ERROR'}, T("Имя эффекта пустое"))
            return {'CANCELLED'}

        game_root = bpy.path.abspath(context.scene.gtatools_game_root or '')
        if not game_root:
            self.report({'ERROR'}, "Game Root не задан")
            return {'CANCELLED'}
        fxp_path = os.path.join(game_root, 'models', 'effects.fxp')
        if not os.path.isfile(fxp_path):
            self.report({'ERROR'}, f"effects.fxp не найден: {fxp_path}")
            return {'CANCELLED'}

        backup_path = fxp_path + '.bak'
        if not os.path.isfile(backup_path):
            import shutil
            try:
                shutil.copy2(fxp_path, backup_path)
                print(f"[FXP] backed up to {backup_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Не удалось создать бэкап: {e}")
                return {'CANCELLED'}

        from .core import fxp as _fxp
        try:
            fxf = _fxp.read_fxp(fxp_path)
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка парсинга: {e}")
            return {'CANCELLED'}

        before = len(fxf.systems)
        fxf.systems = [s for s in fxf.systems if s.name != name]
        removed = before - len(fxf.systems)
        if removed == 0:
            self.report({'WARNING'}, f"Эффект '{name}' не найден в effects.fxp")
            return {'CANCELLED'}

        try:
            _fxp.write_fxp(fxp_path, fxf)
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка записи: {e}")
            return {'CANCELLED'}

        _fxp.clear_cache()
        global _particle_enum_cache_key
        _particle_enum_cache_key = None

        # Clear the object's effect name so it doesn't point at a missing entry
        obj['2dfx_effect_name'] = ""
        obj.inu.particle_emitter_index = 0

        try:
            from .ops.fx_preview import update_particle_preview
            update_particle_preview(obj)
        except Exception:
            pass

        self.report({'INFO'}, f"Удалено: {name}")
        return {'FINISHED'}


class GTATOOLS_OT_particle_curve_select(bpy.types.Operator):
    """Выбрать кривую для редактирования"""
    bl_idname = "gtatools.particle_curve_select"
    bl_label = "Select Curve"
    bl_property = "curve_name"
    bl_options = {'REGISTER'}

    curve_name: EnumProperty(name="Curve", items=_particle_curve_items)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX'
                and obj.inu.effect_2dfx == 'PARTICLE')

    def execute(self, context):
        obj = context.active_object
        if obj is None or not self.curve_name:
            return {'CANCELLED'}
        obj.inu.particle_curve_name = self.curve_name
        if _load_curve_into_buffer(obj, self.curve_name):
            n = len(obj.inu.particle_curve_keys)
            self.report({'INFO'}, f"{self.curve_name}: {n} ключей")
        else:
            self.report({'WARNING'}, f"Не удалось загрузить {self.curve_name}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}


class GTATOOLS_OT_particle_curve_key_add(bpy.types.Operator):
    """Добавить ключевой кадр в конец кривой"""
    bl_idname = "gtatools.particle_curve_key_add"
    bl_label = "Add Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and getattr(obj, 'inu', None) and obj.inu.particle_curve_name

    def execute(self, context):
        obj = context.active_object
        keys = obj.inu.particle_curve_keys
        item = keys.add()
        # Default new key to t=1 and the last val, or fallback
        if len(keys) >= 2:
            prev = keys[-2]
            item.time = min(prev.time + 0.1, 1.0)
            item.val = prev.val
        else:
            item.time = 0.0
            item.val = 0.0
        obj.inu.particle_curve_key_index = len(keys) - 1
        return {'FINISHED'}


class GTATOOLS_OT_particle_curve_key_select_row(bpy.types.Operator):
    """Выбрать активный ключ для удаления"""
    bl_idname = "gtatools.particle_curve_key_select_row"
    bl_label = "Select Keyframe Row"
    bl_options = {'REGISTER'}

    index: IntProperty(default=0)

    def execute(self, context):
        obj = context.active_object
        if obj and getattr(obj, 'inu', None):
            obj.inu.particle_curve_key_index = self.index
        return {'FINISHED'}


class GTATOOLS_OT_particle_curve_key_remove(bpy.types.Operator):
    """Удалить активный ключевой кадр"""
    bl_idname = "gtatools.particle_curve_key_remove"
    bl_label = "Remove Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and getattr(obj, 'inu', None)
                and len(obj.inu.particle_curve_keys) > 0)

    def execute(self, context):
        obj = context.active_object
        keys = obj.inu.particle_curve_keys
        idx = max(0, min(obj.inu.particle_curve_key_index, len(keys) - 1))
        keys.remove(idx)
        if obj.inu.particle_curve_key_index >= len(keys):
            obj.inu.particle_curve_key_index = max(0, len(keys) - 1)
        return {'FINISHED'}


class GTATOOLS_OT_particle_curve_write(bpy.types.Operator):
    """Записать буфер ключей обратно в effects.fxp для выбранной кривой"""
    bl_idname = "gtatools.particle_curve_write"
    bl_label = "Write Curve to FXP"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and getattr(obj, 'inu', None)
                and obj.inu.particle_curve_name
                and len(obj.inu.particle_curve_keys) > 0)

    def execute(self, context):
        obj = context.active_object
        curve_key = obj.inu.particle_curve_name
        if '.' not in curve_key:
            self.report({'ERROR'}, f"Неверный ключ кривой: {curve_key}")
            return {'CANCELLED'}
        info_type, field_name = curve_key.split('.', 1)

        game_root = bpy.path.abspath(context.scene.gtatools_game_root or '')
        if not game_root:
            self.report({'ERROR'}, "Game Root не задан")
            return {'CANCELLED'}
        fxp_path = os.path.join(game_root, 'models', 'effects.fxp')
        if not os.path.isfile(fxp_path):
            self.report({'ERROR'}, f"effects.fxp не найден: {fxp_path}")
            return {'CANCELLED'}

        effect_name = obj.get('2dfx_effect_name', '') or ''
        if not effect_name:
            self.report({'ERROR'}, T("Эффект не выбран"))
            return {'CANCELLED'}

        # Auto-backup on first write
        backup_path = fxp_path + '.bak'
        if not os.path.isfile(backup_path):
            import shutil
            try:
                shutil.copy2(fxp_path, backup_path)
                print(f"[FXP] backed up to {backup_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Не удалось создать бэкап: {e}")
                return {'CANCELLED'}

        from .core import fxp as _fxp
        from .core.fxp import FXCurve, FXKeyframe, FXInfoBlock
        try:
            fxf = _fxp.read_fxp(fxp_path)
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка парсинга: {e}")
            return {'CANCELLED'}

        system = fxf.find(effect_name)
        if not system or not system.emitters:
            self.report({'ERROR'}, f"Система '{effect_name}' не найдена")
            return {'CANCELLED'}

        em_idx = max(0, min(int(obj.inu.particle_emitter_index), len(system.emitters) - 1))
        em = system.emitters[em_idx]

        info = em.info(info_type)
        if info is None:
            info = FXInfoBlock(type=info_type, scalars=[('TIMEMODEPRT', '1')])
            em.infos.append(info)

        # Build the new curve from the buffer, sorted by time
        keys_sorted = sorted(
            ((float(k.time), float(k.val)) for k in obj.inu.particle_curve_keys),
            key=lambda kv: kv[0],
        )
        info.curves[field_name] = FXCurve(
            looped=0,
            keys=[FXKeyframe(time=t, val=v) for t, v in keys_sorted],
        )

        try:
            _fxp.write_fxp(fxp_path, fxf)
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка записи: {e}")
            return {'CANCELLED'}

        _fxp.clear_cache()

        # Refresh the scalar fields from the updated FXP and rebuild preview
        try:
            _populate_particle_props_from_fxp(obj, effect_name, em_idx)
        except Exception:
            pass
        try:
            from .ops.fx_preview import update_particle_preview
            update_particle_preview(obj)
        except Exception:
            pass

        self.report({'INFO'}, f"{curve_key}: {len(keys_sorted)} ключей записано")
        return {'FINISHED'}


class GTATOOLS_OT_particle_emitter_switch(bpy.types.Operator):
    """Переключить редактируемый эмиттер в системе с несколькими"""
    bl_idname = "gtatools.particle_emitter_switch"
    bl_label = "Switch Particle Emitter"
    bl_options = {'REGISTER', 'UNDO'}

    direction: IntProperty(default=1)  # +1 = next, -1 = prev

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX'
                and obj.inu.effect_2dfx == 'PARTICLE')

    def execute(self, context):
        obj = context.active_object
        name = obj.get('2dfx_effect_name', '') or ''
        if not name:
            self.report({'WARNING'}, T("Эффект не выбран"))
            return {'CANCELLED'}
        total = _get_effect_emitter_count(name)
        if total <= 1:
            self.report({'INFO'}, T("У эффекта один эмиттер"))
            return {'CANCELLED'}

        cur = int(obj.inu.particle_emitter_index)
        new_idx = (cur + self.direction) % total
        obj.inu.particle_emitter_index = new_idx
        try:
            _populate_particle_props_from_fxp(obj, name, new_idx)
        except Exception as e:
            self.report({'ERROR'}, f"populate error: {e}")
            return {'CANCELLED'}
        try:
            from .ops.fx_preview import update_particle_preview
            update_particle_preview(obj)
        except Exception as e:
            print(f"[2DFX Particle] preview update failed: {e}")

        self.report({'INFO'}, f"Emitter {new_idx + 1}/{total}")
        return {'FINISHED'}


class GTATOOLS_OT_reload_effects_fxp(bpy.types.Operator):
    """Перечитать effects.fxp с диска (сбросить кэш)"""
    bl_idname = "gtatools.reload_effects_fxp"
    bl_label = "Reload effects.fxp"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .core import fxp as _fxp
        _fxp.clear_cache()
        self.report({'INFO'}, "effects.fxp cache cleared")
        return {'FINISHED'}


# Zone assignment per FX_INFO block type, matching GTA SA / FX Editor order.
# The native parser reads blocks sequentially and expects them grouped by
# zone: Emission(1) → Physics(2) → Rendering(3). Out-of-order blocks
# (e.g. EMANGLE after COLOUR) are silently ignored by the game engine.
_INFO_ZONES = {
    # Zone 1 — Emission / birth
    'EMLIFE': 1, 'EMRATE': 1, 'EMSPEED': 1, 'EMANGLE': 1, 'EMDIR': 1,
    'EMSIZE': 1, 'EMROTATION': 1, 'EMPOS': 1, 'EMWEATHER': 1,
    # Zone 2 — Physics / movement
    'FORCE': 2, 'FRICTION': 2, 'WIND': 2, 'ROTSPEED': 2, 'NOISE': 2,
    'JITTER': 2, 'GROUNDCOLLIDE': 2, 'ATTRACTPT': 2, 'FLOAT': 2,
    'UNDERWATER': 2,
    # Zone 3 — Rendering / visuals
    'SIZE': 3, 'COLOUR': 3, 'COLOURBRIGHT': 3, 'SPRITERECT': 3, 'DIR': 3,
    'ANIMTEX': 3, 'TRAIL': 3, 'FLAT': 3, 'HEATHAZE': 3, 'SELFLIT': 3,
}


def _info_zone(type_name: str) -> int:
    return _INFO_ZONES.get(type_name, 3)


def _sort_infos_by_zone(em) -> None:
    """Stable-sort an emitter's info blocks into canonical zone order."""
    em.infos.sort(key=lambda i: _info_zone(i.type))


# Mandatory curve fields per FX_INFO block type, with sensible defaults.
# When we create a new info block from scratch during save, the game crashes
# if any of these fields are missing — the native parser allocates a fixed
# struct per block and reads garbage for absent fields. These defaults come
# from analysing the pristine effects.fxp across all 161 emitters.
_INFO_TEMPLATES = {
    'COLOUR': (
        [('TIMEMODEPRT', '1')],
        {'RED': 255.0, 'GREEN': 255.0, 'BLUE': 255.0, 'ALPHA': 255.0},
    ),
    'COLOURBRIGHT': (
        [('TIMEMODEPRT', '1')],
        {'RED': 255.0, 'GREEN': 255.0, 'BLUE': 255.0, 'ALPHA': 255.0, 'BIAS': 0.0},
    ),
    'SIZE': (
        [('TIMEMODEPRT', '1')],
        {'SIZEX': 1.0, 'SIZEY': 1.0, 'SIZEXBIAS': 0.0, 'SIZEYBIAS': 0.0},
    ),
    'EMLIFE':     ([], {'LIFE': 1.0, 'BIAS': 0.0}),
    'EMRATE':     ([], {'RATE': 10.0}),
    'EMSPEED':    ([], {'SPEED': 1.0, 'BIAS': 0.0}),
    'EMDIR':      ([], {'DIRX': 0.0, 'DIRY': 0.0, 'DIRZ': 1.0}),
    'EMANGLE':    ([], {'MIN': 0.0, 'MAX': 0.0}),
    'EMSIZE': (
        # Zone 1 blocks never carry TIMEMODEPRT in original GTA SA data;
        # adding one here desynchronises the native field-order parser.
        [],
        # Interleaved axis order — GTA SA's native parser reads these
        # sequentially by position, not by name. Wrong order => particles
        # emit along a degenerate line/point instead of the intended volume.
        {
            'RADIUS': 0.0,
            'SIZEMINX': 0.0, 'SIZEMAXX': 0.0,
            'SIZEMINY': 0.0, 'SIZEMAXY': 0.0,
            'SIZEMINZ': 0.0, 'SIZEMAXZ': 0.0,
        },
    ),
    'EMPOS':      ([], {'X': 0.0, 'Y': 0.0, 'Z': 0.0}),
    'EMROTATION': ([], {'ANGLEMIN': 0.0, 'ANGLEMAX': 0.0}),
    'FORCE': (
        [('TIMEMODEPRT', '1')],
        {'FORCEX': 0.0, 'FORCEY': 0.0, 'FORCEZ': 0.0},
    ),
    'FRICTION':   ([('TIMEMODEPRT', '1')], {'FRICTION': 0.0}),
    'WIND':       ([('TIMEMODEPRT', '1')], {'WINDFACTOR': 0.0}),
    'NOISE':      ([('TIMEMODEPRT', '1')], {'NOISE': 0.0}),
    'JITTER':     ([('TIMEMODEPRT', '1')], {'JITTERFACTOR': 0.0}),
    'ROTSPEED': (
        [('TIMEMODEPRT', '1')],
        {'MINCW': 0.0, 'MAXCW': 0.0, 'MINCCW': 0.0, 'MAXCCW': 0.0},
    ),
    'GROUNDCOLLIDE': (
        [('TIMEMODEPRT', '1')],
        {'BOUNCE': 0.0, 'SPEEDMULT': 1.0, 'BOUNCEERROR': 0.0},
    ),
}


def _apply_particle_props_to_emitter(obj, em) -> int:
    """Write obj.inu.particle_* back into an FXEmitter, but ONLY for fields
    that differ from what a fresh sample of `em` would produce.

    This preserves multi-keyframe curves the user hasn't touched: if the
    user only edited `particle_size_start`, we rewrite just SIZE.SIZEX/SIZEY
    with a 2-keyframe curve and leave every other curve alone.

    Returns the number of fields actually applied.
    """
    from .core.fxp import FXCurve, FXKeyframe, FXInfoBlock
    inu = obj.inu
    fresh = _sample_particle_from_emitter(em)

    applied = 0
    eps = 1e-4

    def _close_scalar(a, b):
        return abs(float(a) - float(b)) < eps

    def _close_vec(a, b):
        if len(a) != len(b):
            return False
        return all(abs(float(x) - float(y)) < eps for x, y in zip(a, b))

    def _set_base(key, value):
        sv = str(value)
        for i, (k, _) in enumerate(em.base):
            if k == key:
                em.base[i] = (k, sv)
                return
        em.base.append((key, sv))

    def _get_or_create_info(type_name):
        info = em.info(type_name)
        if info is not None:
            return info
        # Build fresh block populated with ALL mandatory fields at sensible
        # defaults. The subsequent per-field writes below will overwrite the
        # specific fields the user actually changed, while non-touched fields
        # remain as defaults — so the game sees a complete struct.
        tmpl = _INFO_TEMPLATES.get(type_name, ([], {}))
        scalars, default_curves = tmpl
        info = FXInfoBlock(type=type_name, scalars=list(scalars))
        for field, default_val in default_curves.items():
            info.curves[field] = FXCurve(
                looped=0,
                keys=[FXKeyframe(time=0.0, val=float(default_val))],
            )
        em.infos.append(info)
        return info

    def _set_start_end(info, field, start_val, end_val):
        info.curves[field] = FXCurve(looped=0, keys=[
            FXKeyframe(time=0.0, val=float(start_val)),
            FXKeyframe(time=1.0, val=float(end_val)),
        ])

    def _set_single(info, field, value):
        info.curves[field] = FXCurve(looped=0, keys=[
            FXKeyframe(time=0.0, val=float(value)),
        ])

    # ── Base scalars ── #
    cur_tex = inu.particle_texture.strip()
    cur_tex_to_write = cur_tex if cur_tex else 'NULL'
    if cur_tex != fresh['texture']:
        _set_base('TEXTURE', cur_tex_to_write)
        applied += 1

    if int(inu.particle_src_blend) != fresh['src_blend']:
        _set_base('SRCBLENDID', int(inu.particle_src_blend))
        applied += 1
    if int(inu.particle_dst_blend) != fresh['dst_blend']:
        _set_base('DSTBLENDID', int(inu.particle_dst_blend))
        applied += 1

    # ── COLOUR curves ── #
    c0 = tuple(inu.particle_color_start)
    c1 = tuple(inu.particle_color_end)
    cm = tuple(inu.particle_color_mid)
    mid_enabled = bool(inu.particle_color_mid_enabled)
    mid_time = float(inu.particle_color_mid_time)
    fresh_mid_enabled = bool(fresh.get('color_mid_enabled', False))
    fresh_mid = tuple(fresh.get('color_mid', (1.0, 1.0, 1.0, 1.0)))
    fresh_mid_time = float(fresh.get('color_mid_time', 0.5))

    colour_changed_start = not _close_vec(c0, fresh['color_start'])
    colour_changed_end = not _close_vec(c1, fresh['color_end'])
    mid_mode_changed = mid_enabled != fresh_mid_enabled
    mid_value_changed = mid_enabled and (
        not _close_vec(cm, fresh_mid)
        or abs(mid_time - fresh_mid_time) >= eps
    )

    def _set_3key(info, field, v0, vm, v1, tm):
        info.curves[field] = FXCurve(looped=0, keys=[
            FXKeyframe(time=0.0, val=float(v0)),
            FXKeyframe(time=float(tm), val=float(vm)),
            FXKeyframe(time=1.0, val=float(v1)),
        ])

    if colour_changed_start or colour_changed_end or mid_mode_changed or mid_value_changed:
        colour = _get_or_create_info('COLOUR')
        # Rewrite channels that changed; if middle is enabled, always use
        # 3-key curves for those channels to preserve the middle keyframe.
        for idx, name in enumerate(('RED', 'GREEN', 'BLUE', 'ALPHA')):
            ch_a_changed = abs(c0[idx] - fresh['color_start'][idx]) >= eps
            ch_b_changed = abs(c1[idx] - fresh['color_end'][idx]) >= eps
            ch_m_changed = mid_enabled and abs(cm[idx] - fresh_mid[idx]) >= eps
            if ch_a_changed or ch_b_changed or ch_m_changed or mid_mode_changed:
                if mid_enabled:
                    _set_3key(colour, name,
                              c0[idx] * 255.0, cm[idx] * 255.0, c1[idx] * 255.0,
                              mid_time)
                else:
                    _set_start_end(colour, name, c0[idx] * 255.0, c1[idx] * 255.0)
                applied += 1

    # ── SIZE curves (SIZEX/SIZEY) ── #
    sz_start_changed = not _close_scalar(inu.particle_size_start, fresh['size_start'])
    sz_end_changed = not _close_scalar(inu.particle_size_end, fresh['size_end'])
    if sz_start_changed or sz_end_changed:
        size_info = _get_or_create_info('SIZE')
        _set_start_end(size_info, 'SIZEX', inu.particle_size_start, inu.particle_size_end)
        _set_start_end(size_info, 'SIZEY', inu.particle_size_start, inu.particle_size_end)
        applied += 1

    # ── Scalar emission curves ── #
    if not _close_scalar(inu.particle_life, fresh['life']):
        _set_single(_get_or_create_info('EMLIFE'), 'LIFE', inu.particle_life)
        applied += 1
    if not _close_scalar(inu.particle_rate, fresh['rate']):
        _set_single(_get_or_create_info('EMRATE'), 'RATE', inu.particle_rate)
        applied += 1
    if not _close_scalar(inu.particle_speed, fresh['speed']):
        _set_single(_get_or_create_info('EMSPEED'), 'SPEED', inu.particle_speed)
        applied += 1

    # ── EMDIR ── #
    dir_cur = tuple(inu.particle_direction)
    if not _close_vec(dir_cur, fresh['direction']):
        emdir = _get_or_create_info('EMDIR')
        if abs(dir_cur[0] - fresh['direction'][0]) >= eps:
            _set_single(emdir, 'DIRX', dir_cur[0])
            applied += 1
        if abs(dir_cur[1] - fresh['direction'][1]) >= eps:
            _set_single(emdir, 'DIRY', dir_cur[1])
            applied += 1
        if abs(dir_cur[2] - fresh['direction'][2]) >= eps:
            _set_single(emdir, 'DIRZ', dir_cur[2])
            applied += 1

    # ── Biases (EMLIFE BIAS, EMSPEED BIAS) ── #
    if not _close_scalar(inu.particle_life_bias, fresh['life_bias']):
        _set_single(_get_or_create_info('EMLIFE'), 'BIAS', inu.particle_life_bias)
        applied += 1
    if not _close_scalar(inu.particle_speed_bias, fresh['speed_bias']):
        _set_single(_get_or_create_info('EMSPEED'), 'BIAS', inu.particle_speed_bias)
        applied += 1

    # ── EMANGLE ── #
    if not _close_scalar(inu.particle_angle_min, fresh['angle_min']):
        _set_single(_get_or_create_info('EMANGLE'), 'MIN', inu.particle_angle_min)
        applied += 1
    if not _close_scalar(inu.particle_angle_max, fresh['angle_max']):
        _set_single(_get_or_create_info('EMANGLE'), 'MAX', inu.particle_angle_max)
        applied += 1

    # ── EMSIZE (Box as symmetric half-extent around emitter) ── #
    # UI stores `particle_volume` as half-extent; FXP needs pairs of
    # SIZEMIN=-v SIZEMAX=+v. Writing both sides keeps the parser happy.
    vol_cur = tuple(inu.particle_volume)
    if not _close_vec(vol_cur, fresh['volume']):
        emsize = _get_or_create_info('EMSIZE')
        for idx, (fld_min, fld_max) in enumerate(
            (('SIZEMINX', 'SIZEMAXX'),
             ('SIZEMINY', 'SIZEMAXY'),
             ('SIZEMINZ', 'SIZEMAXZ'))
        ):
            half = float(vol_cur[idx])
            _set_single(emsize, fld_min, -half)
            _set_single(emsize, fld_max, half)
            applied += 2

    # ── EMPOS ── #
    off_cur = tuple(inu.particle_offset)
    if not _close_vec(off_cur, fresh['offset']):
        empos = _get_or_create_info('EMPOS')
        for idx, fld in enumerate(('X', 'Y', 'Z')):
            if abs(off_cur[idx] - fresh['offset'][idx]) >= eps:
                _set_single(empos, fld, off_cur[idx])
                applied += 1

    # ── EMROTATION ── #
    if not _close_scalar(inu.particle_rotation_min, fresh['rotation_min']):
        _set_single(_get_or_create_info('EMROTATION'), 'ANGLEMIN', inu.particle_rotation_min)
        applied += 1
    if not _close_scalar(inu.particle_rotation_max, fresh['rotation_max']):
        _set_single(_get_or_create_info('EMROTATION'), 'ANGLEMAX', inu.particle_rotation_max)
        applied += 1

    # ── FORCE ── #
    force_cur = tuple(inu.particle_force)
    if not _close_vec(force_cur, fresh['force']):
        finfo = _get_or_create_info('FORCE')
        for idx, fld in enumerate(('FORCEX', 'FORCEY', 'FORCEZ')):
            if abs(force_cur[idx] - fresh['force'][idx]) >= eps:
                _set_single(finfo, fld, force_cur[idx])
                applied += 1

    # ── FRICTION / WIND / NOISE / JITTER ── #
    if not _close_scalar(inu.particle_friction, fresh['friction']):
        _set_single(_get_or_create_info('FRICTION'), 'FRICTION', inu.particle_friction)
        applied += 1
    if not _close_scalar(inu.particle_wind, fresh['wind']):
        _set_single(_get_or_create_info('WIND'), 'WINDFACTOR', inu.particle_wind)
        applied += 1
    if not _close_scalar(inu.particle_noise, fresh['noise']):
        _set_single(_get_or_create_info('NOISE'), 'NOISE', inu.particle_noise)
        applied += 1
    if not _close_scalar(inu.particle_jitter, fresh['jitter']):
        _set_single(_get_or_create_info('JITTER'), 'JITTERFACTOR', inu.particle_jitter)
        applied += 1

    # ── ROTSPEED ── #
    if not _close_scalar(inu.particle_rotspeed_min, fresh['rotspeed_min']):
        _set_single(_get_or_create_info('ROTSPEED'), 'MINCW', inu.particle_rotspeed_min)
        applied += 1
    if not _close_scalar(inu.particle_rotspeed_max, fresh['rotspeed_max']):
        _set_single(_get_or_create_info('ROTSPEED'), 'MAXCW', inu.particle_rotspeed_max)
        applied += 1

    # ── GROUNDCOLLIDE ── #
    if not _close_scalar(inu.particle_ground_bounce, fresh['ground_bounce']):
        _set_single(_get_or_create_info('GROUNDCOLLIDE'), 'BOUNCE', inu.particle_ground_bounce)
        applied += 1
    if not _close_scalar(inu.particle_ground_speedmult, fresh['ground_speedmult']):
        _set_single(_get_or_create_info('GROUNDCOLLIDE'), 'SPEEDMULT', inu.particle_ground_speedmult)
        applied += 1

    # Enforce canonical zone order — the native GTA SA parser ignores
    # info blocks that appear out of Emission→Physics→Rendering sequence.
    if applied > 0:
        _sort_infos_by_zone(em)

    # Strip stray TIMEMODEPRT from Zone 1 blocks (the native parser never
    # expects it there; its presence desyncs the field-order reader and
    # crashes the game). Zone 2/3 blocks always keep TIMEMODEPRT: 1.
    for info in em.infos:
        if _info_zone(info.type) == 1:
            if any(k == 'TIMEMODEPRT' for k, _ in info.scalars):
                info.scalars = [(k, v) for k, v in info.scalars if k != 'TIMEMODEPRT']
                applied += 1

    return applied


class GTATOOLS_OT_save_particle_effect(bpy.types.Operator):
    """Сохранить правки эффекта обратно в effects.fxp (с автобэкапом)"""
    bl_idname = "gtatools.save_particle_effect"
    bl_label = "Save Particle Effect"
    bl_options = {'REGISTER'}

    effect_name: StringProperty(
        name="Effect Name",
        description=T("Имя системы в effects.fxp (можно новое — тогда клонируется из текущей)"),
        default="",
    )
    overwrite: BoolProperty(
        name="Overwrite existing",
        description=T("Перезаписать существующую систему с таким именем"),
        default=True,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX'
                and obj.inu.effect_2dfx == 'PARTICLE')

    def invoke(self, context, event):
        obj = context.active_object
        self.effect_name = obj.get('2dfx_effect_name', '') or ''
        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'effect_name')
        layout.prop(self, 'overwrite')
        layout.label(text=T("При первой записи создастся effects.fxp.bak"), icon='INFO')

    def execute(self, context):
        obj = context.active_object
        game_root = bpy.path.abspath(context.scene.gtatools_game_root or '')
        if not game_root:
            self.report({'ERROR'}, "Game Root не задан")
            return {'CANCELLED'}

        fxp_path = os.path.join(game_root, 'models', 'effects.fxp')
        if not os.path.isfile(fxp_path):
            self.report({'ERROR'}, f"effects.fxp не найден: {fxp_path}")
            return {'CANCELLED'}

        target_name = self.effect_name.strip()
        if not target_name:
            self.report({'ERROR'}, T("Имя эффекта пустое"))
            return {'CANCELLED'}

        # Read fresh (don't mutate cached object)
        from .core import fxp as _fxp
        try:
            fxf = _fxp.read_fxp(fxp_path)
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка парсинга effects.fxp: {e}")
            return {'CANCELLED'}

        existing = fxf.find(target_name)

        if existing is None:
            # Clone current system under new name
            source_name = obj.get('2dfx_effect_name', '') or ''
            source = fxf.find(source_name)
            if source is None:
                self.report({'ERROR'}, f"Исходная система '{source_name}' не найдена — нечего клонировать")
                return {'CANCELLED'}
            import copy
            new_system = copy.deepcopy(source)
            renamed = False
            for i, (k, v) in enumerate(new_system.header):
                if k == 'NAME':
                    new_system.header[i] = (k, target_name)
                    renamed = True
                    break
            if not renamed:
                new_system.header.append(('NAME', target_name))
            fxf.systems.append(new_system)
            target_system = new_system
        else:
            if not self.overwrite:
                self.report({'ERROR'}, f"Система '{target_name}' уже существует (снимите галку 'Overwrite' нельзя, включите её)")
                return {'CANCELLED'}
            target_system = existing

        if not target_system.emitters:
            self.report({'ERROR'}, f"У системы '{target_name}' нет эмиттеров")
            return {'CANCELLED'}

        em_idx = max(0, min(int(obj.inu.particle_emitter_index), len(target_system.emitters) - 1))
        try:
            applied = _apply_particle_props_to_emitter(obj, target_system.emitters[em_idx])
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка применения правок: {e}")
            return {'CANCELLED'}

        # System-level header fields (LENGTH/PLAYMODE/CULLDIST) — dirty check
        def _set_header(key, value):
            sv = str(value)
            for i, (k, _) in enumerate(target_system.header):
                if k == key:
                    target_system.header[i] = (k, sv)
                    return
            target_system.header.append((key, sv))

        def _header_float(key, default):
            try:
                return float(target_system.header_get(key) or default)
            except ValueError:
                return default

        def _header_int(key, default):
            try:
                return int(target_system.header_get(key) or default)
            except ValueError:
                return default

        inu = obj.inu
        if abs(float(inu.particle_sys_length) - _header_float('LENGTH', 1.0)) > 1e-4:
            _set_header('LENGTH', f"{float(inu.particle_sys_length):.3f}")
            applied += 1
        if int(inu.particle_sys_playmode) != _header_int('PLAYMODE', 2):
            _set_header('PLAYMODE', int(inu.particle_sys_playmode))
            applied += 1
        if abs(float(inu.particle_sys_culldist) - _header_float('CULLDIST', 50.0)) > 1e-4:
            _set_header('CULLDIST', f"{float(inu.particle_sys_culldist):.3f}")
            applied += 1

        # No-op early exit: if we didn't clone a new system and no fields
        # changed, don't touch the file (and don't create a pointless backup).
        is_clone = existing is None
        if not is_clone and applied == 0:
            self.report({'INFO'}, T("Нет изменений — файл не тронут"))
            return {'FINISHED'}

        # Auto-backup on first actual write
        backup_path = fxp_path + '.bak'
        if not os.path.isfile(backup_path):
            import shutil
            try:
                shutil.copy2(fxp_path, backup_path)
                print(f"[FXP] backed up to {backup_path}")
            except Exception as e:
                self.report({'ERROR'}, f"Не удалось создать бэкап: {e}")
                return {'CANCELLED'}

        try:
            _fxp.write_fxp(fxp_path, fxf)
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка записи: {e}")
            return {'CANCELLED'}

        _fxp.clear_cache()

        if obj.get('2dfx_effect_name') != target_name:
            obj['2dfx_effect_name'] = target_name

        msg = f"Клон '{target_name}' сохранён" if is_clone else f"'{target_name}': применено полей — {applied}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_attach_2dfx(bpy.types.Operator):
    """Привязать 2DFX к модели (сделать дочерним)"""
    bl_idname = "gtatools.attach_2dfx"
    bl_label = "Attach to Model"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX')

    def execute(self, context):
        fx_obj = context.active_object
        # Find a selected mesh to attach to
        mesh_obj = None
        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj != fx_obj:
                mesh_obj = obj
                break
        if not mesh_obj:
            self.report({'WARNING'}, "Select a mesh object together with the 2DFX")
            return {'CANCELLED'}
        # Keep world position when parenting
        fx_obj.parent = mesh_obj
        fx_obj.matrix_parent_inverse = mesh_obj.matrix_world.inverted()
        self.report({'INFO'}, f"2DFX attached to '{mesh_obj.name}'")
        return {'FINISHED'}


class GTATOOLS_OT_detach_2dfx(bpy.types.Operator):
    """Отвязать 2DFX от родительской модели"""
    bl_idname = "gtatools.detach_2dfx"
    bl_label = "Detach from Model"
    bl_options = {'REGISTER', 'UNDO'}

    fx_name: StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # Если указано имя — отвязываем конкретный объект
        if self.fx_name:
            fx_obj = bpy.data.objects.get(self.fx_name)
        else:
            fx_obj = context.active_object

        if not fx_obj or not fx_obj.parent:
            self.report({'WARNING'}, "Nothing to detach")
            return {'CANCELLED'}

        parent_name = fx_obj.parent.name
        world_matrix = fx_obj.matrix_world.copy()
        fx_obj.parent = None
        fx_obj.matrix_world = world_matrix
        self.report({'INFO'}, f"'{fx_obj.name}' detached from '{parent_name}'")
        return {'FINISHED'}


class GTATOOLS_OT_detach_all_2dfx(bpy.types.Operator):
    """Отвязать все 2DFX/частицы от выделенного меша"""
    bl_idname = "gtatools.detach_all_2dfx"
    bl_label = "Detach All from Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        mesh_obj = context.active_object
        # Собрать всех дочерних 2DFX
        children = [c for c in bpy.data.objects
                    if c.parent == mesh_obj and c.type == 'EMPTY'
                    and getattr(c, 'inu', None) and c.inu.type == '2DFX']

        if not children:
            self.report({'WARNING'}, "No attached 2DFX found")
            return {'CANCELLED'}

        for fx in children:
            world_matrix = fx.matrix_world.copy()
            fx.parent = None
            fx.matrix_world = world_matrix

        self.report({'INFO'}, f"{len(children)} 2DFX detached from '{mesh_obj.name}'")
        return {'FINISHED'}


class GTATOOLS_PT_2dfx_panel(bpy.types.Panel):
    """2DFX Effects Properties"""
    bl_label = "2DFX Effects"
    bl_idname = "GTATOOLS_PT_2dfx_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def _is_2dfx(self, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX')

    def draw_header(self, context):
        if self._is_2dfx(context):
            self.layout.label(text="", icon='CHECKMARK')

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        is_active = self._is_2dfx(context)

        # ── Кнопки создания (видны всегда) ──
        box = layout.box()
        _draw_label_with_info(box, "Create Effect:",
            T("Light — уличные фонари, неон, corona\nParticle — дым, огонь, частицы\nPed Attractor — точки притяжения NPC (банкомат, скамейка)\nSun Glare — блик солнца на поверхности"),
            icon='ADD')
        row = box.row(align=True)
        op = row.operator("gtatools.create_2dfx", text=T("Свет"), icon='LIGHT_POINT')
        op.effect_type = 'LIGHT'
        op = row.operator("gtatools.create_2dfx", text=T("Частица"), icon='PARTICLES')
        op.effect_type = 'PARTICLE'
        row = box.row(align=True)
        op = row.operator("gtatools.create_2dfx", text=T("Ped Attractor"), icon='COMMUNITY')
        op.effect_type = 'PED_ATTRACTOR'
        op = row.operator("gtatools.create_2dfx", text=T("Блик солнца"), icon='LIGHT_SUN')
        op.effect_type = 'SUN_GLARE'

        # ── Статус: счётчик 2DFX в сцене ──
        fx_count = sum(1 for o in context.scene.objects
                       if o.type == 'EMPTY' and getattr(o, 'inu', None)
                       and o.inu.type == '2DFX')
        layout.label(text=f"2DFX objects in scene: {fx_count}", icon='INFO')

        # ── Если выделен меш — показываем привязанные 2DFX ──
        if not is_active and obj and obj.type == 'MESH':
            attached = [c for c in bpy.data.objects
                        if c.parent == obj and c.type == 'EMPTY'
                        and getattr(c, 'inu', None) and c.inu.type == '2DFX']
            if attached:
                box = layout.box()
                box.label(text=f"{T('Привязанные 2DFX:')} {len(attached)}", icon='LINKED')
                for fx in attached:
                    row = box.row(align=True)
                    row.label(text=fx.name, icon='LIGHT' if fx.inu.effect_2dfx == 'LIGHT' else 'PARTICLES')
                    op = row.operator("gtatools.detach_2dfx", text="", icon='X')
                    op.fx_name = fx.name
                layout.operator("gtatools.detach_all_2dfx", text=T("Отвязать все"), icon='UNLINKED')
                layout.separator()
            layout.label(text=T("Выберите 2DFX Empty для редактирования"), icon='RESTRICT_SELECT_ON')
            return

        # ── Если не выбран 2DFX — показываем подсказку ──
        if not is_active:
            layout.label(text=T("Выберите 2DFX Empty для редактирования"), icon='RESTRICT_SELECT_ON')
            return

        # ── Активный 2DFX — зелёная галка в заголовке, свойства ниже ──
        layout.separator()

        # Обводка-box для активного эффекта
        main_box = layout.box()
        header_row = main_box.row()
        header_row.label(text=f"Active: {obj.name}", icon='CHECKMARK')

        settings = obj.inu
        main_box.prop(settings, "effect_2dfx", text=T("Тип эффекта"))

        # Attach/Detach buttons
        attach_box = main_box.box()
        if obj.parent and obj.parent.type == 'MESH':
            row_a = attach_box.row(align=True)
            row_a.label(text=f"Model: {obj.parent.name}", icon='LINKED')
            row_a.operator("gtatools.detach_2dfx", text="", icon='X')
        else:
            attach_box.operator("gtatools.attach_2dfx", text=T("Привязать к модели"), icon='LINK_BLEND')
            attach_box.label(text=T("Выделите меш + 2DFX, затем нажмите"), icon='INFO')

        effect = settings.effect_2dfx

        # Preview buttons
        if effect in ('LIGHT', 'PARTICLE'):
            row = main_box.row(align=True)
            row.operator("gtatools.refresh_2dfx_preview", text=T("Обновить превью"), icon='FILE_REFRESH')
            row.operator("gtatools.remove_2dfx_preview", text=T("Удалить превью"), icon='X')

        if effect == 'LIGHT':
            # Presets
            box_p = main_box.box()
            box_p.label(text=T("Пресеты:"), icon='PRESET')
            row_p = box_p.row(align=True)
            row_p.prop(settings, "preset_2dfx", text="")
            row_p.operator("gtatools.apply_2dfx_preset", text=T("Применить"), icon='CHECKMARK')

            # Color
            box = main_box.box()
            _draw_label_with_info(box, T("Свойства света:"),
                T("Color — цвет короны и света\nCorona Size — размер короны\nDraw Distance — дальность отрисовки\nLight Range — радиус точечного света"),
                icon='LIGHT_POINT')
            box.prop(settings, "color_2dfx", text=T("Цвет:"))

            # Corona
            col = box.column(align=True)
            col.prop(obj, '["2dfx_corona_size"]', text=T("Размер короны"))
            col.prop(obj, '["2dfx_corona_far_clip"]', text=T("Дальность отрисовки"))
            col.prop(obj, '["2dfx_pointlight_range"]', text=T("Радиус света"))
            _draw_label_with_info(col, T("Имя короны:"),
                T("Текстура короны (светящийся спрайт)"))
            col.prop(settings, "corona_tex_2dfx", text="")

            # Show Mode / Flare / Reflection
            box2 = main_box.box()
            col2 = box2.column(align=True)
            _draw_label_with_info(col2, T("Режим показа:"),
                T("DEFAULT — всегда видим\nRANDOM_FLASHING — случайное мерцание\nFLASH_RAIN — мерцает в дождь\nONLY_RAIN — видим только в дождь\nNO_RAIN — не видим в дождь\nFLASH_5 — вариант мерцания 2"))
            col2.prop(settings, "show_mode_2dfx", text="")
            _draw_label_with_info(col2, T("Тип бликов:"),
                T("None — без бликов линзы\nType 1/2/3 — разные стили бликов линзы"))
            col2.prop(settings, "flare_type_2dfx", text="")
            col2.prop(obj, '["2dfx_corona_enable_reflection"]', text=T("Отражение короны"))

            # Shadow
            box3 = main_box.box()
            col3 = box3.column(align=True)
            col3.prop(obj, '["2dfx_shadow_size"]', text=T("Размер тени"))
            col3.prop(obj, '["2dfx_shadow_z_distance"]', text=T("Дистанция тени"))
            col3.prop(obj, '["2dfx_shadow_color_multiplier"]', text=T("Множитель тени"))
            _draw_label_with_info(col3, T("Имя тени:"),
                T("Текстура тени на земле под источником света"))
            col3.prop(settings, "shadow_tex_2dfx", text="")

            # Flags
            box4 = main_box.box()
            row4 = box4.row(align=True)
            row4.prop(obj, '["2dfx_flags1"]', text=T("Флаги 1"))
            row4.prop(obj, '["2dfx_flags2"]', text=T("Флаги 2"))

            # View Vector
            if '2dfx_look_direction' in obj:
                box5 = main_box.box()
                box5.label(text=T("Вектор направления:"), icon='EMPTY_ARROWS')
                box5.prop(obj, '["2dfx_look_direction"]', text="")


        elif effect == 'PARTICLE':
            box = main_box.box()
            box.label(text=T("Свойства частицы:"), icon='PARTICLES')
            row = box.row(align=True)
            row.prop(obj.inu, 'particle_effect_2dfx', text=T("Эффект"))
            row.operator("gtatools.particle_effect_new", text="", icon='ADD')
            row.operator("gtatools.particle_effect_delete", text="", icon='REMOVE')
            row.operator("gtatools.reload_effects_fxp", text="", icon='FILE_REFRESH')

            # Emitter switcher (only if system has > 1 emitter)
            eff_name = obj.get('2dfx_effect_name', '') or ''
            if eff_name:
                em_total = _get_effect_emitter_count(eff_name)
                if em_total > 1:
                    em_row = box.row(align=True)
                    op = em_row.operator("gtatools.particle_emitter_switch", text="", icon='TRIA_LEFT')
                    op.direction = -1
                    em_row.label(text=f"Emitter {obj.inu.particle_emitter_index + 1} / {em_total}")
                    op = em_row.operator("gtatools.particle_emitter_switch", text="", icon='TRIA_RIGHT')
                    op.direction = 1
                    box.label(text=T("Переключение сбросит правки — сохраняйте первыми"), icon='INFO')

            # Live simulation toggle (scene-global)
            sim_row = box.row(align=True)
            sim_row.prop(
                context.scene, 'gtatools_particle_sim',
                text=T("Симуляция"),
                icon='PLAY' if context.scene.gtatools_particle_sim else 'PAUSE',
                toggle=True,
            )

            inu = obj.inu
            scene = context.scene

            def _section(parent, prop_name: str, label: str, icon: str):
                """Collapsible section helper. Returns the content box or None."""
                expanded = getattr(scene, prop_name)
                header = parent.row(align=True)
                header.prop(
                    scene, prop_name,
                    icon='TRIA_DOWN' if expanded else 'TRIA_RIGHT',
                    text="", emboss=False,
                )
                header.label(text=label, icon=icon)
                if expanded:
                    return parent.box()
                return None

            # ── Texture / blend ── #
            tex_box = _section(box, 'gtatools_pfx_exp_texture', T("Спрайт и смешивание"), 'TEXTURE')
            if tex_box:
                tex_box.prop(inu, 'particle_texture', text=T("Текстура"))
                row = tex_box.row(align=True)
                row.prop(inu, 'particle_src_blend', text="SRC")
                row.prop(inu, 'particle_dst_blend', text="DST")

            # ── Colour ── #
            col_box = _section(box, 'gtatools_pfx_exp_color', T("Цвет (start → end)"), 'COLOR')
            if col_box:
                col_box.prop(inu, 'particle_color_start', text=T("Начало"))
                col_box.prop(inu, 'particle_color_mid_enabled', text=T("Средний"), toggle=True)
                if inu.particle_color_mid_enabled:
                    col_box.prop(inu, 'particle_color_mid', text=T("Middle"))
                    col_box.prop(inu, 'particle_color_mid_time', text=T("Mid time"), slider=True)
                col_box.prop(inu, 'particle_color_end', text=T("Конец"))

            # ── Size ── #
            size_box = _section(box, 'gtatools_pfx_exp_size', T("Размер"), 'FULLSCREEN_ENTER')
            if size_box:
                row = size_box.row(align=True)
                row.prop(inu, 'particle_size_start', text=T("Начало"))
                row.prop(inu, 'particle_size_end', text=T("Конец"))

            # ── Emission ── #
            em_box = _section(box, 'gtatools_pfx_exp_emission', T("Эмиссия"), 'OUTLINER_OB_FORCE_FIELD')
            if em_box:
                em_box.prop(inu, 'particle_life', text=T("Жизнь"))
                em_box.prop(inu, 'particle_life_bias', text=T("Life bias"))
                em_box.prop(inu, 'particle_rate', text=T("Rate"))
                em_box.prop(inu, 'particle_speed', text=T("Скорость"))
                em_box.prop(inu, 'particle_speed_bias', text=T("Speed bias"))
                em_box.prop(inu, 'particle_direction', text=T("Направление"))
                row = em_box.row(align=True)
                row.prop(inu, 'particle_angle_min', text=T("Angle min"))
                row.prop(inu, 'particle_angle_max', text=T("Angle max"))
                em_box.prop(inu, 'particle_volume', text=T("Box"))
                em_box.prop(inu, 'particle_offset', text=T("Offset"))
                row = em_box.row(align=True)
                row.prop(inu, 'particle_rotation_min', text=T("Rot min"))
                row.prop(inu, 'particle_rotation_max', text=T("Rot max"))

            # ── Physics ── #
            ph_box = _section(box, 'gtatools_pfx_exp_physics', T("Физика"), 'PHYSICS')
            if ph_box:
                ph_box.prop(inu, 'particle_force', text=T("Force"))
                row = ph_box.row(align=True)
                row.prop(inu, 'particle_friction', text=T("Friction"))
                row.prop(inu, 'particle_wind', text=T("Wind"))
                row = ph_box.row(align=True)
                row.prop(inu, 'particle_noise', text=T("Noise"))
                row.prop(inu, 'particle_jitter', text=T("Jitter"))
                row = ph_box.row(align=True)
                row.prop(inu, 'particle_rotspeed_min', text=T("RotSpd min"))
                row.prop(inu, 'particle_rotspeed_max', text=T("RotSpd max"))
                row = ph_box.row(align=True)
                row.prop(inu, 'particle_ground_bounce', text=T("Bounce"))
                row.prop(inu, 'particle_ground_speedmult', text=T("SpeedMult"))

            # ── System-level (FX_SYSTEM_DATA header) ── #
            sys_box = _section(box, 'gtatools_pfx_exp_system', T("Система"), 'WORLD')
            if sys_box:
                sys_box.prop(inu, 'particle_sys_length', text=T("Length"))
                sys_box.prop(inu, 'particle_sys_playmode', text=T("Play mode"))
                sys_box.prop(inu, 'particle_sys_culldist', text=T("Cull dist"))

            # ── Curve editor (B1) ── #
            cv_box = _section(box, 'gtatools_pfx_exp_curves', T("Кривые (keyframes)"), 'FCURVE')
            if cv_box:
                # Curve picker row
                pick_row = cv_box.row(align=True)
                pick_row.operator(
                    "gtatools.particle_curve_select",
                    text=inu.particle_curve_name or T("Выбрать кривую..."),
                    icon='VIEWZOOM',
                )

                if inu.particle_curve_name:
                    keys = inu.particle_curve_keys
                    # Header
                    hdr = cv_box.row(align=True)
                    hdr.label(text=T(f"Ключи ({len(keys)}):"))
                    hdr.operator("gtatools.particle_curve_key_add", text="", icon='ADD')
                    hdr.operator("gtatools.particle_curve_key_remove", text="", icon='REMOVE')

                    # Keyframe rows (time, val)
                    if len(keys) == 0:
                        cv_box.label(text=T("Нет ключей"), icon='INFO')
                    else:
                        for i, kf in enumerate(keys):
                            r = cv_box.row(align=True)
                            # Active-row indicator (click selects for deletion)
                            is_active = (i == inu.particle_curve_key_index)
                            op = r.operator(
                                "gtatools.particle_curve_key_select_row",
                                text="", depress=is_active,
                                icon='RADIOBUT_ON' if is_active else 'RADIOBUT_OFF',
                            )
                            op.index = i
                            r.prop(kf, 'time', text="t")
                            r.prop(kf, 'val', text="v")

                    # Write to FXP button
                    write_row = cv_box.row(align=True)
                    write_row.scale_y = 1.2
                    write_row.operator(
                        "gtatools.particle_curve_write",
                        text=T("Записать кривую в effects.fxp"),
                        icon='FILE_TICK',
                    )

            # Save to effects.fxp
            save_row = box.row(align=True)
            save_row.scale_y = 1.3
            save_row.operator(
                "gtatools.save_particle_effect",
                text=T("Сохранить в effects.fxp"),
                icon='FILE_TICK',
            )

        elif effect == 'PED_ATTRACTOR':
            box = main_box.box()
            box.label(text=T("Точка притяжения:"), icon='COMMUNITY')
            if '2dfx_attractor_type' in obj:
                box.prop(obj, '["2dfx_attractor_type"]', text=T("Тип аттрактора"))
            if '2dfx_rotation_matrix' in obj:
                box.prop(obj, '["2dfx_rotation_matrix"]', text=T("Матрица поворота"))
            if '2dfx_external_script' in obj:
                box.prop(obj, '["2dfx_external_script"]', text=T("Внешний скрипт"))
            if '2dfx_ped_probability' in obj:
                box.prop(obj, '["2dfx_ped_probability"]', text=T("Вероятность NPC"))

        elif effect == 'SUN_GLARE':
            box = main_box.box()
            box.label(text=T("Солнечный блик"), icon='LIGHT_SUN')
            box.label(text=T("Только позиция (без доп. данных)"))


class GTATOOLS_OT_set_col_surface(bpy.types.Operator):
    """Назначить тип поверхности GTA SA для COL коллизии"""
    bl_idname = "gtatools.set_col_surface"
    bl_label = "Set COL Surface"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: StringProperty()
    surface_id: IntProperty(default=0, min=0, max=178)

    def execute(self, context):
        mat = bpy.data.materials.get(self.material_name)
        if mat is None:
            self.report({'ERROR'}, f"Material not found: {self.material_name}")
            return {'CANCELLED'}
        mat.inu.col_mat_index = self.surface_id
        name = get_surface_name(self.surface_id)
        self.report({'INFO'}, f"{T('Surface ID назначен:')} {self.material_name} = {self.surface_id} ({name})")
        return {'FINISHED'}


class GTATOOLS_OT_col_surface_menu(bpy.types.Operator):
    """Выбрать тип поверхности для COL материала"""
    bl_idname = "gtatools.col_surface_menu"
    bl_label = "Surface Type"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: StringProperty()

    # Search filter
    search: StringProperty(
        name="Search",
        description=T("Фильтр типов поверхности"),
        default="",
        options={'TEXTEDIT_UPDATE'},
    )

    # Category expand toggles (collapsed by default)
    cat_default: BoolProperty(default=False)
    cat_concrete: BoolProperty(default=False)
    cat_gravel: BoolProperty(default=False)
    cat_grass: BoolProperty(default=False)
    cat_dirt: BoolProperty(default=False)
    cat_sand: BoolProperty(default=False)
    cat_glass: BoolProperty(default=False)
    cat_wood: BoolProperty(default=False)
    cat_metal: BoolProperty(default=False)
    cat_stone: BoolProperty(default=False)
    cat_vegetation: BoolProperty(default=False)
    cat_water: BoolProperty(default=False)
    cat_misc: BoolProperty(default=False)

    _cat_props = {
        "Default": "cat_default", "Concrete": "cat_concrete", "Gravel": "cat_gravel",
        "Grass": "cat_grass", "Dirt": "cat_dirt", "Sand": "cat_sand",
        "Glass": "cat_glass", "Wood": "cat_wood", "Metal": "cat_metal",
        "Stone": "cat_stone", "Vegetation": "cat_vegetation", "Water": "cat_water",
        "Misc": "cat_misc",
    }

    def execute(self, context):
        return {'CANCELLED'}

    def invoke(self, context, event):
        self.search = ""
        return context.window_manager.invoke_popup(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "search", text="", icon='VIEWZOOM')

        search_lower = self.search.lower()
        name_lookup = {sid: name for sid, name, desc in GTA_SA_SURFACE_MATERIALS}

        if search_lower:
            col = layout.column(align=True)
            for sid, name, desc in GTA_SA_SURFACE_MATERIALS:
                if search_lower not in name.lower() and search_lower not in str(sid):
                    continue
                op = col.operator("gtatools.set_col_surface", text=f"{sid}: {name}")
                op.material_name = self.material_name
                op.surface_id = sid
        else:
            for cat_name, cat_ids in COL_SURFACE_CATEGORIES:
                prop_name = self._cat_props.get(cat_name, "")
                is_open = getattr(self, prop_name, False)

                box = layout.box()
                row = box.row()
                icon = 'DISCLOSURE_TRI_DOWN' if is_open else 'DISCLOSURE_TRI_RIGHT'
                row.prop(self, prop_name, text=f"{cat_name} ({len(cat_ids)})", icon=icon, emboss=False)

                if is_open:
                    col = box.column(align=True)
                    for sid in cat_ids:
                        name = name_lookup.get(sid, f"UNKNOWN_{sid}")
                        op = col.operator("gtatools.set_col_surface", text=f"{sid}: {name}")
                        op.material_name = self.material_name
                        op.surface_id = sid


# =============================================================================

class GTATOOLS_PT_col_material_panel(bpy.types.Panel):
    """Выбор типа поверхности COL в свойствах материала"""
    bl_label = "COL Surface Type"
    bl_idname = "GTATOOLS_PT_col_material_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.material is not None

    def draw(self, context):
        layout = self.layout
        mat = context.material

        current_id = mat.inu.col_mat_index
        current_name = get_surface_name(current_id)

        # Current value display
        row = layout.row(align=True)
        row.prop(mat.inu, "col_mat_index", text="ID")
        # Search button
        op = row.operator("gtatools.col_surface_menu", text="", icon='VIEWZOOM')
        op.material_name = mat.name

        # Show surface name
        layout.label(text=f"{current_name}", icon='PHYSICS')

        layout.separator()

        # Day/Night Light
        row = layout.row(align=True)
        row.prop(mat.inu, "col_day_light", text=T("Дневной свет"))
        row.prop(mat.inu, "col_night_light", text=T("Ночной свет"))

        # Brightness
        layout.prop(mat.inu, "col_brightness", text=T("Яркость"))


class GTATOOLS_PT_material_effects_panel(bpy.types.Panel):
    """Панель эффектов материала в свойствах материала"""
    bl_label = "GTA SA Material Effects"
    bl_idname = "GTATOOLS_PT_material_effects_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.material is not None

    def draw(self, context):
        layout = self.layout
        mat = context.material
        inu = mat.inu

        # Ambient
        layout.prop(inu, "ambient", text=T("Фоновое затенение"))

        # ── Vehicle Color Slot ──
        box = layout.box()
        row = box.row()
        row.label(text=T("Слот цвета машины:"), icon='AUTO')
        box.prop(inu, "vehicle_color_slot", text="")
        if inu.vehicle_color_slot != 'NONE':
            box.operator("gtatools.sa_vehicle_preset", text=T("Применить SA Vehicle defaults"), icon='SHADING_RENDERED')

        layout.separator()

        # ── Environment Map ──
        box = layout.box()
        row = box.row()
        row.prop(inu, "export_env_map", text=T("Карта окружения"))
        if inu.export_env_map:
            box.prop(inu, "env_map_tex", text=T("Текстура"))
            box.prop(inu, "env_map_coef", text=T("Коэффициент"))
            box.prop(inu, "env_map_fb_alpha", text=T("Использовать FB Alpha"))

        # ── Bump Map ──
        box = layout.box()
        row = box.row()
        row.prop(inu, "export_bump_map", text=T("Карта высот"))
        if inu.export_bump_map:
            box.prop(inu, "bump_map_tex", text=T("Текстура карты высот"))

        # ── Reflection ──
        box = layout.box()
        row = box.row()
        row.prop(inu, "export_reflection", text=T("Отражение материала"))
        if inu.export_reflection:
            row = box.row(align=True)
            row.prop(inu, "reflection_scale_x", text=T("Масштаб X"))
            row.prop(inu, "reflection_scale_y", text="Y")
            row = box.row(align=True)
            row.prop(inu, "reflection_offset_x", text=T("Смещение X"))
            row.prop(inu, "reflection_offset_y", text="Y")
            box.prop(inu, "reflection_intensity", text=T("Интенсивность"))

        # ── Specular ──
        box = layout.box()
        row = box.row()
        row.prop(inu, "export_specular", text=T("Зеркальный материал"))
        if inu.export_specular:
            box.prop(inu, "specular_level", text=T("Уровень зеркальности"))
            box.prop(inu, "specular_texture", text=T("Текстура"))

        # ── Dual Texture / Blend Mode ──
        box = layout.box()
        row = box.row()
        row.prop(inu, "export_dual_tex", text="Blend Mode (Src/Dst)")
        if inu.export_dual_tex:
            box.prop(inu, "dual_tex_src_blend", text="Src")
            box.prop(inu, "dual_tex_dst_blend", text="Dst")
            box.prop(inu, "dual_tex_texture", text=T("Текстура"))

        # ── UV Animation ──
        box = layout.box()
        row = box.row()
        row.prop(inu, "export_animation", text=T("UV Анимация"))
        if inu.export_animation:
            box.prop(inu, "animation_name", text=T("Имя анимации"))

        # ── UV Animation write into DFF ──
        box = layout.box()
        row = box.row(align=True)
        _fid = _icons.get_icon("film")
        if _fid:
            row.label(text="", icon_value=_fid)
        row.prop(inu, "uv_anim_write", text=T("Писать UV Anim в DFF"))
        if inu.uv_anim_write:
            row = box.row(align=True)
            row.prop(inu, "uv_anim_speed_u", text="Speed U")
            row.prop(inu, "uv_anim_speed_v", text="Speed V")
            box.prop(inu, "uv_anim_duration", text=T("Длительность"))




def _draw_sort_materials_menu(self, context):
    """Append sort button to material context menu"""
    self.layout.separator()
    self.layout.operator("gtatools.sort_materials", text=T("Сортировка материалов"), icon='SORTALPHA')


class GTATOOLS_PT_object_ide_ipl_panel(bpy.types.Panel):
    """IDE/IPL свойства в Object Properties"""
    bl_label = "GTA SA: IDE / IPL"
    bl_idname = "GTATOOLS_PT_object_ide_ipl_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        obj = context.active_object
        inu = obj.inu

        col = layout.column(align=True)
        col.prop(inu, "model_id", text="Model ID")
        col.prop(inu, "draw_distance", text="Draw Dist")
        col.prop(inu, "lod_draw_distance", text="LOD Dist")

        # Flags with expandable checkboxes
        row = layout.row(align=True)
        row.prop(inu, "ide_flags", text="Flags")
        row.prop(scn, "gtatools_show_ide_flags",
                 icon='TRIA_DOWN' if scn.gtatools_show_ide_flags else 'TRIA_RIGHT',
                 text="", emboss=False)
        if scn.gtatools_show_ide_flags:
            fbox = layout.box()
            fc = fbox.column(align=True)
            fc.prop(inu, "flag_is_road")
            fc.prop(inu, "flag_draw_last")
            fc.prop(inu, "flag_additive")
            fc.prop(inu, "flag_no_zbuffer")
            fc.prop(inu, "flag_no_shadows")
            fc.prop(inu, "flag_glass_1")
            fc.prop(inu, "flag_glass_2")
            fc.prop(inu, "flag_garage_door")
            fc.prop(inu, "flag_damagable")
            fc.prop(inu, "flag_is_tree")
            fc.prop(inu, "flag_is_palm")
            fc.prop(inu, "flag_no_flyer_col")
            fc.prop(inu, "flag_is_tag")
            fc.prop(inu, "flag_no_backface")
            fc.prop(inu, "flag_breakable")

        row = layout.row(align=True)
        row.prop(inu, "interior_id", text="Interior")
        row.prop(inu, "lod_index", text="LOD")

        # Breakable object (DFF chunk 0x253F2FD)
        box = layout.box()
        row = box.row(align=True)
        _eid = _icons.get_icon("explosion")
        if _eid:
            row.label(text="", icon_value=_eid)
        row.prop(inu, "breakable", text=T("Разрушаемый (Breakable)"))
        if inu.breakable:
            box.prop(inu, "breakable_force", text=T("Break Force"))

        # Check for ID conflicts
        if inu.model_id > 0:
            conflicts = [o.name for o in bpy.data.objects
                         if o.type == 'MESH' and o != obj
                         and hasattr(o, 'inu') and o.inu.model_id == inu.model_id]
            if conflicts:
                layout.label(text=f"ID {inu.model_id}: {T('конфликт с')} {', '.join(conflicts[:3])}", icon='ERROR')


class GTATOOLS_PT_inu_tools_panel(bpy.types.Panel):
    """Панель INU Tools в Properties > Scene"""
    bl_label = "INU Tools"
    bl_idname = "GTATOOLS_PT_inu_tools_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # IDE / IPL / IMG paths (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene, "gtatools_show_paths_settings",
                 icon='TRIA_DOWN' if scene.gtatools_show_paths_settings else 'TRIA_RIGHT',
                 text=T("Import Map"), emboss=False)
        if scene.gtatools_show_paths_settings:
            box.label(text="Game Root", icon='FILE_FOLDER')
            box.prop(scene, "gtatools_game_root", text="")
            row = box.row(align=True)
            row.prop(scene, "gtatools_img_skip_lod", text="Skip LOD", toggle=True)
            row.prop(scene, "gtatools_map_skip_2dfx", text=T("Без 2DFX"), toggle=True)
            box.prop(scene, "gtatools_map_region", text="")

            # Binary IPL selector (collapsible)
            bi_box = box.box()
            bi_row = bi_box.row(align=True)
            bi_row.prop(
                scene, "gtatools_show_binary_ipls",
                icon='TRIA_DOWN' if scene.gtatools_show_binary_ipls else 'TRIA_RIGHT',
                emboss=False,
                text=T("Бинарные IPL") + f": {len(scene.gtatools_binary_ipls)}",
            )
            bi_row.operator(
                "gtatools.scan_binary_ipls", text="", icon='FILE_REFRESH',
            )
            if scene.gtatools_show_binary_ipls:
                cached_region = scene.get('gtatools_binary_ipls_region', '')
                if cached_region and cached_region != scene.gtatools_map_region:
                    bi_box.label(
                        text=T("Район изменился — пересканируйте"),
                        icon='ERROR',
                    )
                if not scene.gtatools_binary_ipls:
                    bi_box.label(
                        text=T("Список пуст — нажмите Scan"),
                        icon='INFO',
                    )
                else:
                    bi_row2 = bi_box.row(align=True)
                    op_all = bi_row2.operator(
                        "gtatools.binary_ipl_toggle_all",
                        text=T("Все"), icon='CHECKBOX_HLT',
                    )
                    op_all.enable = True
                    op_none = bi_row2.operator(
                        "gtatools.binary_ipl_toggle_all",
                        text=T("Никакие"), icon='CHECKBOX_DEHLT',
                    )
                    op_none.enable = False
                    bi_col = bi_box.column(align=True)
                    for item in scene.gtatools_binary_ipls:
                        bi_col.prop(item, "enabled", text=item.name)

            box.operator("gtatools.extract_textures", text=T("Извлечь ресурсы"), icon='PACKAGE')
            box.operator("gtatools.build_map_glb", text=T("Собрать карту в .glb"), icon='WORLD')
            box.operator("gtatools.load_map_glb", text=T("Импорт карты .glb"), icon='IMPORT')
            row = box.row(align=True)
            row.operator("gtatools.toggle_bbox",
                         text=T("BBox: ON") if _bbox_mode_active else T("BBox: OFF"),
                         icon='MESH_CUBE',
                         depress=_bbox_mode_active)
            row.operator("gtatools.toggle_links",
                         text=T("Links: ON") if _links_active else T("Links: OFF"),
                         icon='LINKED',
                         depress=_links_active)
            box.separator()
            box.label(text="IDE", icon='TEXT')
            box.prop(scene, "gtatools_ide_path", text="")
            box.label(text="IPL", icon='EMPTY_AXIS')
            box.prop(scene, "gtatools_ipl_path", text="")
            box.label(text="IMG", icon='PACKAGE')
            box.prop(scene, "gtatools_img_path", text="")

        # Textures (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene, "gtatools_show_texture_settings",
                 icon='TRIA_DOWN' if scene.gtatools_show_texture_settings else 'TRIA_RIGHT',
                 text=T("Текстуры"), emboss=False)
        if scene.gtatools_show_texture_settings:
            box.label(text=T("Системные текстуры:"), icon='TEXTURE')
            box.prop(scene, "gtatools_texture_path1", text="")
            row = box.row()
            row.label(text=T("Папка .blend:"), icon='FILE_FOLDER')
            row.operator("gtatools.set_blend_folder", text="", icon='FILE_REFRESH')
            box.prop(scene, "gtatools_texture_path2", text="")
            box.operator("gtatools.load_textures", text=T("Загрузить текстуры"), icon='IMPORT')

        # NVTT Settings (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene, "gtatools_show_nvtt_settings",
                 icon='TRIA_DOWN' if scene.gtatools_show_nvtt_settings else 'TRIA_RIGHT',
                 text=T("Настройки NVTT"), emboss=False)
        if scene.gtatools_show_nvtt_settings:
            box.prop(scene, "gtatools_nvtt_path", text="")
            nvtt_path = scene.gtatools_nvtt_path
            available, msg = check_nvtt_available(nvtt_path)
            if available:
                box.label(text=T("Статус: Готов"), icon='CHECKMARK')
            else:
                box.label(text=T("Статус: Не найден"), icon='ERROR')

        # Suffix settings (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene, "gtatools_show_suffix_settings",
                 icon='TRIA_DOWN' if scene.gtatools_show_suffix_settings else 'TRIA_RIGHT',
                 text=T("Суффиксы / Префиксы"), emboss=False)
        if scene.gtatools_show_suffix_settings:
            for _label, _pfx, _sfx in [("DFF", "gtatools_prefix_dff", "gtatools_suffix_dff"),
                                        ("LOD", "gtatools_prefix_lod", "gtatools_suffix_lod"),
                                        ("COL", "gtatools_prefix_col", "gtatools_suffix_col")]:
                row = box.row(align=True)
                pfx = row.row(align=True)
                pfx.scale_x = 0.7
                pfx.prop(scene, _pfx, text="")
                sub_lbl = row.row(align=True)
                sub_lbl.scale_x = 0.6
                sub_lbl.label(text="Model")
                sfx = row.row(align=True)
                sfx.scale_x = 0.7
                sfx.prop(scene, _sfx, text="")
                pad = row.row(align=True)
                pad.label(text=" ")
                pad.label(text=" ")
                pad.label(text=" ")

        # ID Manager (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene, "gtatools_show_id_manager",
                 icon='TRIA_DOWN' if scene.gtatools_show_id_manager else 'TRIA_RIGHT',
                 text=T("Менеджер ID"), emboss=False)
        if scene.gtatools_show_id_manager:
            _id_preset_sync(context)
            from .data.id_manager import get_free_ids, get_used_ids, get_file_path

            # Preset selector
            preset_row = box.row(align=True)
            preset_row.prop(scene, "gtatools_id_preset", text=T("Пресет"))
            preset_row.operator("gtatools.id_preset_new", text="", icon='ADD')
            preset_row.operator("gtatools.id_preset_rename", text="", icon='GREASEPENCIL')
            preset_row.operator("gtatools.id_preset_delete", text="", icon='REMOVE')

            free = get_free_ids()
            used = get_used_ids()

            box.label(text=f"{T('Свободных:')} {len(free)}  |  {T('Занятых:')} {len(used)}", icon='PRESET')

            if free:
                box.label(text=f"{T('Следующий свободный:')} {free[0]}", icon='FORWARD')

            # Search field
            box.prop(scene, "gtatools_id_search", text="", icon='VIEWZOOM')
            search = getattr(scene, 'gtatools_id_search', '').strip()
            page = getattr(scene, 'gtatools_id_page', 0)
            per_page = 20

            # Filter IDs
            if used:
                filtered = []
                for id_num in sorted(used.keys()):
                    name = used[id_num]
                    if search:
                        if search.isdigit():
                            if search not in str(id_num):
                                continue
                        else:
                            if search.lower() not in name.lower():
                                continue
                    filtered.append((id_num, name))

                total = len(filtered)
                max_page = max(0, (total - 1) // per_page)
                page = min(page, max_page)
                start = page * per_page
                page_items = filtered[start:start + per_page]

                sub = box.box()
                col = sub.column(align=True)
                # 2 columns
                for i in range(0, len(page_items), 2):
                    row = col.row(align=True)
                    for j in range(2):
                        if i + j < len(page_items):
                            id_num, name = page_items[i + j]
                            row.label(text=f"{id_num}-{name}")
                            op = row.operator("gtatools.id_manager_release", text="", icon='X')
                            op.model_id = id_num

                # Page navigation
                if total > per_page:
                    nav = sub.row(align=True)
                    nav.prop(scene, "gtatools_id_page", text=f"{start+1}-{min(start+per_page, total)} / {total}")

            # Show free IDs (compact)
            if free:
                sub = box.box()
                text = ", ".join(str(i) for i in sorted(free)[:20])
                if len(free) > 20:
                    text += "..."
                sub.label(text=f"{T('Свободные:')} {text}", icon='DOT')

            row = box.row(align=True)
            row.operator("gtatools.id_manager_auto_assign", text=T("Назначить ID выделенным"), icon='ADD')
            box.operator("gtatools.id_manager_assign_from", text=T("Назначить с ID..."), icon='SEQUENCE')
            row.operator("gtatools.id_manager_clear_selected", text="", icon='REMOVE')
            row.operator("gtatools.id_manager_clear", text="", icon='TRASH')
            box.operator("gtatools.id_manager_create", text=T("Создать файл ID"), icon='FILE_NEW')
            box.operator("gtatools.id_manager_extend", text=T("Расширить ID (FLA)"), icon='ADD')
            box.operator("gtatools.id_manager_sync_scene", text=T("Синхронизировать сцену"), icon='SCENE_DATA')
            box.operator("gtatools.id_manager_from_game", text=T("Загрузить из игры"), icon='IMPORT')
            box.operator("gtatools.id_manager_open_file", text=T("Открыть файл ID"), icon='FILE_TEXT')

        # IMG file list (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene, "gtatools_show_img_list",
                 icon='TRIA_DOWN' if scene.gtatools_show_img_list else 'TRIA_RIGHT',
                 text=T("Файлы IMG"), emboss=False)
        if scene.gtatools_show_img_list:
            if len(scene.gtatools_img_entries) > 0:
                box.template_list("GTATOOLS_UL_img_files", "", scene, "gtatools_img_entries",
                                  scene, "gtatools_img_entries_index", rows=8)
                entries = scene.gtatools_img_entries
                dff_c = sum(1 for e in entries if e.name.lower().endswith('.dff'))
                col_c = sum(1 for e in entries if e.name.lower().endswith('.col'))
                txd_c = sum(1 for e in entries if e.name.lower().endswith('.txd'))
                box.label(text=f"DFF: {dff_c}  COL: {col_c}  TXD: {txd_c}  Total: {len(entries)}", icon='INFO')
            box.operator("gtatools.refresh_img_list", text=T("Обновить список"), icon='FILE_REFRESH')


class GTATOOLS_OT_id_manager_open_file(bpy.types.Operator):
    """Открыть файл активного ID пресета в текстовом редакторе"""
    bl_idname = "gtatools.id_manager_open_file"
    bl_label = "Open ID File"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _id_preset_sync(context)
        from .data.id_manager import get_file_path
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
    bl_label = "Release ID"
    bl_options = {'REGISTER'}

    model_id: IntProperty()

    def execute(self, context):
        _id_preset_sync(context)
        from .data.id_manager import release_id
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
    bl_label = "Auto Assign IDs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _id_preset_sync(context)
        from .data.id_manager import allocate_id

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        # Group by base_name, order: DFF then LOD per group (skip COL)
        pairs = {}  # base_name -> {'DFF': obj, 'LOD': obj}
        for obj in objs:
            inu = getattr(obj, 'inu', None)
            if not inu or inu.model_id != 0:
                continue
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
    bl_label = "Assign IDs from..."
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
        _id_preset_sync(context)
        from .data.id_manager import get_used_ids

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        used = set(get_used_ids().keys())
        # Also collect IDs already on scene objects
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
                used.add(current_id)
                current_id += 1
                assigned += 1

        self.report({'INFO'}, f"{T('Назначено ID:')} {assigned} ({self.start_id}+)")
        return {'FINISHED'}


class GTATOOLS_OT_batch_set_type(bpy.types.Operator):
    """Массовое переключение типа объектов (OBJ/COL/SHA/2DFX/NON)"""
    bl_idname = "gtatools.batch_set_type"
    bl_label = "Batch Set Type"
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
        from .tools.model_utils import get_model_type, _get_suffixes, _get_prefixes

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
    bl_label = "Clear Selected IDs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _id_preset_sync(context)
        from .data.id_manager import release_id
        count = 0
        for obj in context.selected_objects:
            if obj.type == 'MESH' and hasattr(obj, 'inu'):
                mid = obj.inu.model_id
                if mid > 0:
                    release_id(mid)
                    obj.inu.model_id = 0
                    count += 1
        self.report({'INFO'}, f"{T('Очищено ID:')} {count}")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_clear(bpy.types.Operator):
    """Очистить все занятые ID"""
    bl_idname = "gtatools.id_manager_clear"
    bl_label = "Clear All IDs"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        _id_preset_sync(context)
        from .data.id_manager import clear_all
        clear_all()
        self.report({'INFO'}, T("Все ID очищены"))
        return {'FINISHED'}



class GTATOOLS_OT_id_manager_create(bpy.types.Operator):
    """Заполнить активный пресет ID (321-19999, все свободные)"""
    bl_idname = "gtatools.id_manager_create"
    bl_label = "Create ID File"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _id_preset_sync(context)
        from .data.id_manager import create_id_file
        count = create_id_file()
        self.report({'INFO'}, f"ID: 321-19999 ({count})")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_extend(bpy.types.Operator):
    """Добавить ID (Fastman Limit Adjuster)"""
    bl_idname = "gtatools.id_manager_extend"
    bl_label = "Extend IDs"
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
        _id_preset_sync(context)
        from .data.id_manager import extend_ids
        new_start, new_end = extend_ids(self.count)
        self.report({'INFO'}, f"ID: +{self.count} ({new_start}-{new_end})")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_from_game(bpy.types.Operator):
    """Загрузить занятые ID из IDE файлов GTA SA"""
    bl_idname = "gtatools.id_manager_from_game"
    bl_label = "Load IDs from Game"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _id_preset_sync(context)
        from .data.id_manager import populate_from_game
        game_root = bpy.path.abspath(context.scene.gtatools_game_root)
        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}
        count = populate_from_game(game_root)
        self.report({'INFO'}, f"{T('Занято ID:')} {count}")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_sync_scene(bpy.types.Operator):
    """Добавить ID из объектов сцены в менеджер"""
    bl_idname = "gtatools.id_manager_sync_scene"
    bl_label = "Sync Scene IDs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        _id_preset_sync(context)
        from .data.id_manager import _load, _save
        from .tools.model_utils import get_model_type

        entries = _load()
        existing = {id_num for id_num, _ in entries}

        added = 0
        for obj in bpy.data.objects:
            if obj.type != 'MESH' or not hasattr(obj, 'inu'):
                continue
            mid = obj.inu.model_id
            if mid > 0 and mid not in existing:
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
    bl_label = "New ID Preset"
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
        from .data.id_manager import create_preset, get_active_preset
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
    bl_label = "Delete ID Preset"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        from .data.id_manager import delete_preset, list_presets
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
    bl_label = "Rename ID Preset"
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
        from .data.id_manager import rename_preset
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


class GTATOOLS_PT_prelight_panel(bpy.types.Panel):
    """Панель Prelight"""
    bl_label = "Prelight"
    bl_idname = "GTATOOLS_PT_prelight_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene

        # Setup Lights
        row = layout.row(align=True)
        row.operator("gtatools.create_prelight_lights", text=T("Создать 8 ламп"), icon='LIGHT')
        row.operator("gtatools.remove_prelight_lights", text=T("Удалить"), icon='X')

        layout.separator()

        # Color Attributes selector
        _draw_label_with_info(layout, T("Цветовые атрибуты:"),
            T("Day — дневные вертексные цвета\nNight — ночные вертексные цвета\nDay/Night — создать оба атрибута\n+/- — добавить или удалить атрибут\nSave Materials — сохранить материалы (для Itera Tools)\nRestore — восстановить сохранённые материалы"))

        if obj and obj.type == 'MESH':
            mesh = obj.data
            active_attr = mesh.color_attributes.active_color if mesh.color_attributes else None

            box = layout.box()

            # Day row
            row = box.row(align=True)
            if "Day" in mesh.color_attributes:
                is_active = bool(active_attr and active_attr.name == "Day")
                icon = 'RADIOBUT_ON' if is_active else 'RADIOBUT_OFF'
                op = row.operator("gtatools.select_color_attribute", text="Day", icon=icon, depress=is_active)
                op.attribute_name = "Day"
                op = row.operator("gtatools.remove_color_attr", text="", icon='REMOVE')
                op.attr_name = "Day"
            else:
                row.label(text="Day", icon='RADIOBUT_OFF')
                op = row.operator("gtatools.create_color_attr", text="", icon='ADD')
                op.attr_name = "Day"

            # Night row
            row = box.row(align=True)
            if "Night" in mesh.color_attributes:
                is_active = bool(active_attr and active_attr.name == "Night")
                icon = 'RADIOBUT_ON' if is_active else 'RADIOBUT_OFF'
                op = row.operator("gtatools.select_color_attribute", text="Night", icon=icon, depress=is_active)
                op.attribute_name = "Night"
                op = row.operator("gtatools.remove_color_attr", text="", icon='REMOVE')
                op.attr_name = "Night"
            else:
                row.label(text="Night", icon='RADIOBUT_OFF')
                op = row.operator("gtatools.create_color_attr", text="", icon='ADD')
                op.attr_name = "Night"

            # Other attributes (not Day/Night)
            for attr in mesh.color_attributes:
                if attr.name not in ("Day", "Night"):
                    row = box.row(align=True)
                    is_active = bool(active_attr and active_attr.name == attr.name)
                    icon = 'RADIOBUT_ON' if is_active else 'RADIOBUT_OFF'
                    op = row.operator("gtatools.select_color_attribute", text=attr.name, icon=icon, depress=is_active)
                    op.attribute_name = attr.name
                    op = row.operator("gtatools.remove_color_attr", text="", icon='REMOVE')
                    op.attr_name = attr.name

            # Day/Night label and buttons
            row = layout.row(align=True)
            # Check if preview is active on active object
            _preview_on = False
            if obj and obj.type == 'MESH':
                for _ms in obj.material_slots:
                    _m = _ms.material
                    if _m and _m.use_nodes and _m.node_tree.nodes.get("Prelight_Mix"):
                        _preview_on = True
                        break
            _pv_icon = 'HIDE_OFF' if _preview_on else 'HIDE_ON'
            op_pv = row.operator("gtatools.prelight_preview", text="", icon=_pv_icon, depress=_preview_on)
            op_pv.enable = not _preview_on
            row.operator("gtatools.create_day_night", text="Day/Night")
            row.operator("gtatools.add_color_attribute", text="", icon='ADD')
            row.operator("gtatools.remove_color_attribute", text="", icon='REMOVE')

            # Copy Day ↔ Night
            row = layout.row(align=True)
            op = row.operator("gtatools.copy_color_attr", text=T("Day → Night"), icon='FORWARD')
            op.source = "Day"
            op.target = "Night"
            op = row.operator("gtatools.copy_color_attr", text=T("Night → Day"), icon='BACK')
            op.source = "Night"
            op.target = "Day"

            # LightMap UV2 row
            row = layout.row(align=True)
            _lm_on = False
            _lm_exists = False
            for _ms in obj.material_slots:
                _m = _ms.material
                if _m and _m.use_nodes:
                    _lm_mix = _m.node_tree.nodes.get("LM_Mix")
                    if _lm_mix:
                        _lm_exists = True
                        if not _lm_mix.mute:
                            _lm_on = True
                        break
            _lm_icon = 'HIDE_OFF' if _lm_on else 'HIDE_ON'
            if _lm_exists:
                op_lm = row.operator("gtatools.toggle_lightmap_uv2", text="", icon=_lm_icon, depress=_lm_on)
                op_lm.enable = not _lm_on
            else:
                row.label(text="", icon='HIDE_ON')
            row.operator("gtatools.apply_lightmap_uv2", text=T("Добавить LightMap"))
            row.operator("gtatools.remove_lightmap_uv2", text="", icon='REMOVE')

        layout.separator()

        # Bake Vertex Colors
        _draw_label_with_info(layout, T("Запекание:"),
            T("Тени — включить расчёт теней при запекании\nЗапечь — быстрое запекание без теней\nС тенями — запекание с raycast тенями (медленнее, но точнее)"))
        row = layout.row(align=True)
        row.prop(scene, "gtatools_bake_shadows", text=T("Тени"), icon='SHADING_RENDERED', toggle=True)
        row = layout.row(align=True)
        row.operator("gtatools.bake_vertex_colors_simple", text=T("Запечь"), icon='RENDER_STILL')
        row.operator("gtatools.bake_vertex_colors", text=T("С тенями"), icon='RENDER_RESULT')

        layout.separator()

        # Adjust Color (V offset)
        _draw_label_with_info(layout, T("Настройка цвета:"),
            T("V — смещение яркости vertex colors\nПоложительное значение — светлее\nОтрицательное — темнее"))
        row = layout.row(align=True)
        row.prop(scene, "gtatools_v_offset", text="V")
        row.operator("gtatools.apply_v_offset", text=T("Применить"), icon='CHECKMARK')



class GTATOOLS_PT_bake_settings_subpanel(bpy.types.Panel):
    """Расширенные настройки запекания"""
    bl_label = "Advanced Settings"
    bl_idname = "GTATOOLS_PT_bake_settings_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_prelight_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "gtatools_bake_ambient", text=T("Окружающий"), slider=True)
        layout.prop(scene, "gtatools_bake_intensity", text=T("Интенсивность"), slider=True)
        layout.prop(scene, "gtatools_bake_gamma", text=T("Гамма"), slider=True)

        layout.separator()
        layout.operator("gtatools.reset_bake_settings", icon='LOOP_BACK')

        # Presets
        layout.separator()
        box = layout.box()
        box.label(text=T("Пресеты:"), icon='PRESET')
        row = box.row(align=True)
        row.prop(scene, "gtatools_prelight_preset", text="")
        row.operator("gtatools.prelight_preset_load", text="", icon='IMPORT')
        row.operator("gtatools.prelight_preset_save", text="", icon='ADD')
        row.operator("gtatools.prelight_preset_delete", text="", icon='REMOVE')


def _presets_dir():
    d = os.path.join(_get_user_config_dir(), 'presets')
    os.makedirs(d, exist_ok=True)
    return d


def _load_prelight_presets():
    import json
    presets = []
    d = _presets_dir()
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    for f in sorted(os.listdir(d)):
        if f.endswith('.json'):
            try:
                with open(os.path.join(d, f), 'r', encoding='utf-8') as fh:
                    p = json.load(fh)
                    if 'name' in p:
                        presets.append(p)
            except:
                pass
    return presets if presets else [{"name": "Default", "ambient": 0.10, "intensity": 0.05, "gamma": 0.50, "shadows": True}]


def _save_preset_file(preset):
    import json
    d = _presets_dir()
    os.makedirs(d, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in preset['name'])
    path = os.path.join(d, f"{safe_name}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(preset, f, indent=2, ensure_ascii=False)


def _delete_preset_file(name):
    d = _presets_dir()
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
    path = os.path.join(d, f"{safe_name}.json")
    if os.path.isfile(path):
        os.remove(path)


def _get_preset_items(self, context):
    presets = _load_prelight_presets()
    items = [(p['name'], p['name'], '') for p in presets]
    return items if items else [('NONE', 'No presets', '')]


class GTATOOLS_OT_prelight_preset_load(bpy.types.Operator):
    """Загрузить выбранный пресет"""
    bl_idname = "gtatools.prelight_preset_load"
    bl_label = "Load Preset"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        name = scene.gtatools_prelight_preset
        presets = _load_prelight_presets()
        for p in presets:
            if p['name'] == name:
                scene.gtatools_bake_ambient = p.get('ambient', 0.10)
                scene.gtatools_bake_intensity = p.get('intensity', 0.05)
                scene.gtatools_bake_gamma = p.get('gamma', 0.50)
                scene.gtatools_bake_shadows = p.get('shadows', True)
                self.report({'INFO'}, f"{T('Пресет загружен:')} {name}")
                return {'FINISHED'}
        self.report({'ERROR'}, T("Пресет не найден"))
        return {'CANCELLED'}


class GTATOOLS_OT_prelight_preset_save(bpy.types.Operator):
    """Сохранить текущие настройки как пресет"""
    bl_idname = "gtatools.prelight_preset_save"
    bl_label = "Save Preset"
    bl_options = {'REGISTER'}

    preset_name: StringProperty(name="Name", default="My Preset")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        scene = context.scene

        new_preset = {
            "name": self.preset_name,
            "ambient": scene.gtatools_bake_ambient,
            "intensity": scene.gtatools_bake_intensity,
            "gamma": scene.gtatools_bake_gamma,
            "shadows": scene.gtatools_bake_shadows,
        }

        _save_preset_file(new_preset)
        self.report({'INFO'}, f"{T('Пресет сохранён:')} {self.preset_name}")
        return {'FINISHED'}


class GTATOOLS_OT_prelight_preset_delete(bpy.types.Operator):
    """Удалить выбранный пресет"""
    bl_idname = "gtatools.prelight_preset_delete"
    bl_label = "Delete Preset"
    bl_options = {'REGISTER'}

    def execute(self, context):
        name = context.scene.gtatools_prelight_preset
        _delete_preset_file(name)
        self.report({'INFO'}, f"{T('Пресет удалён:')} {name}")
        return {'FINISHED'}


class GTATOOLS_PT_vc_postprocess_panel(bpy.types.Panel):
    """Панель пост-обработки vertex colors"""
    bl_label = "Post-Processing"
    bl_idname = "GTATOOLS_PT_vc_postprocess_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_prelight_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Smooth
        box = layout.box()
        _draw_label_with_info(box, T("Сглаживание:"),
            T("Сглаживание vertex colors между соседними вершинами\nIterations — количество проходов\nFactor — сила сглаживания (0-1)"),
            icon='MOD_SMOOTH')
        row = box.row(align=True)
        row.prop(scene, "gtatools_vc_smooth_iterations", text=T("Проходы"))
        row.prop(scene, "gtatools_vc_smooth_factor", text=T("Сила"))
        box.operator("gtatools.vc_smooth", text=T("Сгладить"), icon='SMOOTHCURVE')

        # Contrast
        box = layout.box()
        _draw_label_with_info(box, T("Контраст:"),
            T("Контраст vertex colors\n1.0 — без изменений\n< 1.0 — меньше контраст\n> 1.0 — больше контраст"),
            icon='CAMERA_DATA')
        row = box.row(align=True)
        row.prop(scene, "gtatools_vc_contrast", text=T("Контраст"))
        row.operator("gtatools.vc_contrast", text=T("Применить"), icon='CHECKMARK')

        # Brightness
        box = layout.box()
        _draw_label_with_info(box, T("Яркость:"),
            T("Яркость vertex colors\n0.0 — без изменений\n> 0 — светлее\n< 0 — темнее"),
            icon='LIGHT_SUN')
        row = box.row(align=True)
        row.prop(scene, "gtatools_vc_brightness", text=T("Яркость"))
        row.operator("gtatools.vc_brightness", text=T("Применить"), icon='CHECKMARK')

        # Gamma
        box = layout.box()
        _draw_label_with_info(box, T("Гамма:"),
            T("Гамма-коррекция vertex colors\n1.0 — без изменений\n< 1.0 — светлее (тени)\n> 1.0 — темнее (тени)"),
            icon='FCURVE')
        row = box.row(align=True)
        row.prop(scene, "gtatools_vc_gamma", text=T("Гамма"))
        row.operator("gtatools.vc_gamma", text=T("Применить"), icon='CHECKMARK')

        # Smooth between objects
        layout.separator()
        layout.operator("gtatools.vc_smooth_between", text=T("Сгладить между объектами"), icon='MOD_SMOOTH')


class GTATOOLS_PT_itera_panel(bpy.types.Panel):
    """Интеграция с Itera Tools 3 — материалы освещения"""
    bl_label = "Itera Tools 3"
    bl_idname = "GTATOOLS_PT_itera_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        itera_path = _find_itera_blend_path()
        if not itera_path:
            layout.label(text=T("Itera не найден в библиотеках ассетов"), icon='ERROR')
            return

        # Apply presets
        row = layout.row(align=True)
        row.operator("gtatools.apply_itera_material", text="Vertex Lit Linear", icon='MATERIAL')
        row.operator("gtatools.apply_itera_quickstart", text="Quickstart", icon='NODE_MATERIAL')

        layout.operator("gtatools.remove_itera_material", text=T("Убрать Itera"), icon='LOOP_BACK')

        layout.separator()

        # Fix Itera Collection
        itera_cols = [c for c in bpy.data.collections if c.name.startswith("Template Scene - Vertex Lights")]
        if itera_cols:
            needs_fix = any(c.library or c.name not in context.scene.collection.children for c in itera_cols)
            if needs_fix:
                layout.operator("gtatools.fix_itera_collection", text=T("Исправить коллекцию Itera"), icon='LIGHT')
            else:
                row = layout.row()
                row.enabled = False
                row.operator("gtatools.fix_itera_collection", text=T("Коллекция Itera исправлена"), icon='CHECKMARK')


class GTATOOLS_PT_prelight_col_panel(bpy.types.Panel):
    """Конвертировать vertex colors в COL Day/Night Light"""
    bl_label = "Prelight COL"
    bl_idname = "GTATOOLS_PT_prelight_col_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene

        # Show source layers
        if obj and obj.type == 'MESH' and obj.data.color_attributes:
            mesh = obj.data
            day_src = "Day" if "Day" in mesh.color_attributes else (mesh.color_attributes.active_color.name if mesh.color_attributes.active_color else "—")
            night_src = "Night" if "Night" in mesh.color_attributes else day_src
            layout.label(text=f"Day: {day_src} | Night: {night_src}", icon='COLOR')
        else:
            layout.label(text=T("Нет vertex colors"), icon='INFO')

        layout.separator()

        # Day range
        box = layout.box()
        _draw_label_with_info(box, T("Дневной свет:"),
            T("Диапазон дневного освещения для COL материалов\nMin/Max — значения от 0 до 15\nЯркость vertex colors конвертируется в этот диапазон"),
            icon='LIGHT_SUN')
        row = box.row(align=True)
        row.prop(scene, "gtatools_col_day_min", text=T("Мин."))
        row.prop(scene, "gtatools_col_day_max", text=T("Макс."))

        # Night range
        box = layout.box()
        _draw_label_with_info(box, T("Ночной свет:"),
            T("Диапазон ночного освещения для COL материалов\nMin/Max — значения от 0 до 15\nИспользует Night color attribute если есть"),
            icon='SHADING_RENDERED')
        row = box.row(align=True)
        row.prop(scene, "gtatools_col_night_min", text=T("Мин."))
        row.prop(scene, "gtatools_col_night_max", text=T("Макс."))

        layout.separator()

        # Preview button
        preview_icon = 'HIDE_OFF' if _col_light_mod._col_light_preview_active else 'HIDE_ON'
        preview_text = T("Скрыть превью") if _col_light_mod._col_light_preview_active else T("Превью COL Light")
        layout.operator("gtatools.preview_col_light", text=preview_text,
                         icon=preview_icon, depress=_col_light_mod._col_light_preview_active)

        if _col_light_mod._col_light_preview_active:
            box = layout.box()
            box.prop(scene, "gtatools_col_light_edge", text=T("Край"), slider=True)
            box.prop(scene, "gtatools_col_light_threshold", text=T("Порог"), slider=True)
            box.prop(scene, "gtatools_col_light_contrast", text=T("Контраст"), slider=True)
            row = box.row(align=True)
            row.prop(scene, "gtatools_col_light_show_numbers", text=T("Цифры"), toggle=True)
            row.prop(scene, "gtatools_col_light_font_size", text=T("Размер"))

        row = layout.row(align=True)
        row.operator("gtatools.bake_col_light", text=T("Запечь COL Light"), icon='RENDER_STILL')
        row.operator("gtatools.clear_col_light_mats", text="", icon='X')

        # Show info about created COL materials
        if obj and obj.type == 'MESH':
            import json
            stored = json.loads(obj.get("gtatools_col_light_mats", "[]"))
            if stored:
                layout.label(text=f"{T('COL light материалов:')} {len(stored)}", icon='CHECKMARK')


class GTATOOLS_PT_vertex_paint_panel(bpy.types.Panel):
    """Панель инструментов Vertex Paint"""
    bl_label = "Vertex Paint"
    bl_idname = "GTATOOLS_PT_vertex_paint_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return False  # Hidden — code kept for future use

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        # Mode switching
        layout.label(text=T("Режим:"))
        row = layout.row(align=True)
        row.operator("gtatools.switch_to_edit", text=T("Редактор"), icon='EDITMODE_HLT')
        row.operator("gtatools.switch_to_vpaint", text=T("Рисование"), icon='VPAINT_HLT')

        # Face selection toggle (only in Vertex Paint mode)
        if obj and obj.mode == 'VERTEX_PAINT':
            row = layout.row()
            icon = 'RESTRICT_SELECT_OFF' if obj.data.use_paint_mask else 'RESTRICT_SELECT_ON'
            row.operator("gtatools.toggle_face_select", text=T("Выделение граней"), icon=icon, depress=obj.data.use_paint_mask)

        layout.separator()

        # Fill selected faces
        layout.label(text=T("Заливка граней:"))
        row = layout.row(align=True)
        row.prop(scene, "gtatools_fill_color", text="")
        row.operator("gtatools.eyedropper_color", text="", icon='EYEDROPPER')
        row = layout.row(align=True)
        row.operator("gtatools.fill_faces", text=T("Залить"), icon='BRUSH_DATA')
        row.operator("gtatools.restore_fill", text=T("Восстановить"), icon='LOOP_BACK')

        # Список использованных цветов с уровнями
        if obj and hasattr(obj, 'gtatools_fill_colors') and len(obj.gtatools_fill_colors) > 0:
            for i, item in enumerate(obj.gtatools_fill_colors):
                color_box = layout.box()

                # Заголовок цвета
                row = color_box.row(align=True)
                row.prop(item, "color", text="")
                # Кнопка выделения полигонов с этим цветом
                op = row.operator("gtatools.select_fill_color", text="", icon='RESTRICT_SELECT_OFF')
                op.index = i
                # Кнопка удаления цвета (и всех его уровней)
                op = row.operator("gtatools.remove_fill_color", text="", icon='X')
                op.index = i

                # Scatter уровни для этого цвета
                color = item.color
                levels = get_scatter_levels(obj, color)
                if levels:
                    row = color_box.row()
                    row.label(text=f"Levels ({len(levels)}):")
                    op = row.operator("gtatools.clear_fill_color_levels", text=T("Очистить всё"), icon='X')
                    op.color_index = i

                    levels_box = color_box.box()
                    last_level = max(levels)

                    # Показываем только последний уровень
                    max_visible = 1
                    if len(levels) > max_visible:
                        hidden_count = len(levels) - max_visible
                        row = levels_box.row()
                        row.label(text=f"... +{hidden_count} hidden", icon='THREE_DOTS')
                        visible_levels = levels[-max_visible:]
                    else:
                        visible_levels = levels

                    for lvl in visible_levels:
                        row = levels_box.row(align=True)
                        row.label(text=f"Level {lvl}")
                        # Кнопка отмены только для последнего уровня
                        if lvl == last_level:
                            op = row.operator("gtatools.delete_fill_color_level", text=T("Отменить"), icon='LOOP_BACK')
                            op.color_index = i
                            op.level = lvl

        layout.separator()

        # Scatter light
        row = layout.row()
        row.label(text=T("Рассеянный свет:"))
        row.operator("gtatools.reset_scatter_settings", text="", icon='LOOP_BACK')
        layout.prop(scene, "gtatools_scatter_intensity", text=T("Интенсивность"), slider=True)
        layout.prop(scene, "gtatools_scatter_falloff", text=T("Затухание"), slider=True)
        layout.prop(scene, "gtatools_scatter_iterations", text=T("Итерации"))
        layout.prop(scene, "gtatools_scatter_radius", text=T("Радиус (0=авто)"), slider=True)
        layout.operator("gtatools.scatter_light", text=T("Рассеять от выделенных"), icon='LIGHT_POINT')


class GTATOOLS_PT_lightmap_panel(bpy.types.Panel):
    """Панель генератора Lightmap"""
    bl_label = "LightMap (beta_MTA)"
    bl_idname = "GTATOOLS_PT_lightmap_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Load Lightmap texture
        layout.label(text=T("Текстура Lightmap:"))
        row = layout.row(align=True)
        row.operator("gtatools.load_lightmap", text=T("Загрузить (LP_)"), icon='IMAGE_DATA')
        row.operator("gtatools.remove_lightmap", text=T("Удалить"), icon='X')

        layout.separator()

        # Generate code
        layout.label(text=T("Генерация кода:"))
        layout.operator("gtatools.lightmap_generate", text=T("Генерировать"), icon='FILE_TEXT')
        layout.prop(scene, "gtatools_lightmap_path", text=T("Путь"))
        layout.prop(scene, "gtatools_model_id", text=T("ID модели"))

        layout.separator()
        layout.label(text=T("Результат:"))

        box = layout.box()
        if scene.gtatools_lightmap_result:
            lines = scene.gtatools_lightmap_result.split('\n')
            for line in lines:
                box.label(text=line)
            row = layout.row(align=True)
            row.operator("gtatools.lightmap_copy", text=T("Копировать"), icon='COPYDOWN')
            row.operator("gtatools.lightmap_clear", text=T("Очистить"), icon='X')
        else:
            box.label(text=T("Нажмите кнопку для генерации"))


class GTATOOLS_OT_add_water(bpy.types.Operator):
    """Создать водный полигон с параметрами GTA SA"""
    bl_idname = "gtatools.add_water"
    bl_label = "Add Water Plane"
    bl_options = {'REGISTER', 'UNDO'}

    size: FloatProperty(name="Size", default=100.0, min=4.0)
    subdivisions: IntProperty(name="Subdivisions", default=0, min=0, max=10)
    water_flag: EnumProperty(
        name="Water Type",
        items=[
            ('0', T("Обычная / Невидимая"), T("Глубокая вода, не отображается (подводные зоны)")),
            ('1', T("Обычная / Видимая"), T("Глубокая вода с волнами (океан, реки)")),
            ('2', T("Мелкая / Невидимая"), T("Мелкая вода, не отображается (анимация хождения по воде)")),
            ('3', T("Мелкая / Видимая"), T("Мелкая вода, отображается (лужи, пруды)")),
        ],
        default='1',
    )
    wave_height: FloatProperty(name="Wave Height", default=0.1, min=0.0, max=10.0)
    speed: FloatProperty(name="Speed", default=0.05, min=0.0, max=5.0)

    def execute(self, context):
        import bmesh

        mesh = bpy.data.meshes.new("Water")
        bm = bmesh.new()

        # Create water parameter layers
        speed_x_layer = bm.verts.layers.float.new('water_speed_x')
        speed_y_layer = bm.verts.layers.float.new('water_speed_y')
        speed_z_layer = bm.verts.layers.float.new('water_speed_z')
        wave_layer = bm.verts.layers.float.new('water_wave_height')

        s = self.size / 2.0
        z = context.scene.cursor.location.z

        # Create base quad
        v1 = bm.verts.new((-s, -s, z))
        v2 = bm.verts.new((s, -s, z))
        v3 = bm.verts.new((s, s, z))
        v4 = bm.verts.new((-s, s, z))

        for v in [v1, v2, v3, v4]:
            v[speed_x_layer] = 0.0
            v[speed_y_layer] = 0.0
            v[speed_z_layer] = self.speed
            v[wave_layer] = self.wave_height

        bm.faces.new([v1, v2, v3, v4])

        # Subdivide if needed
        if self.subdivisions > 0:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=self.subdivisions)
            for v in bm.verts:
                v[speed_x_layer] = 0.0
                v[speed_y_layer] = 0.0
                v[speed_z_layer] = self.speed
                v[wave_layer] = self.wave_height

        # Generate planar UV from XY coordinates
        uv_layer = bm.loops.layers.uv.new('UVMap')
        uv_scale = 1.0 / 100.0
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = (loop.vert.co.x * uv_scale, loop.vert.co.y * uv_scale)

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new("Water", mesh)
        obj['water_flag'] = int(self.water_flag)

        # Water material with texture
        from .ops.water_import import _get_water_material
        mat = _get_water_material()
        mesh.materials.append(mat)

        # Add to Water collection
        water_col = bpy.data.collections.get("Water")
        if not water_col:
            water_col = bpy.data.collections.new("Water")
            context.scene.collection.children.link(water_col)
        water_col.objects.link(obj)

        # Position at cursor XY
        obj.location.x = context.scene.cursor.location.x
        obj.location.y = context.scene.cursor.location.y

        self.report({'INFO'}, f"Water plane created ({self.size}x{self.size})")
        return {'FINISHED'}


class GTATOOLS_OT_water_snap_grid(bpy.types.Operator):
    """Привязать вершины воды к кратным 4 координатам (требование GTA SA)"""
    bl_idname = "gtatools.water_snap_grid"
    bl_label = "Snap to Grid (x4)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            mesh = obj.data
            mat_w = obj.matrix_world
            for vert in mesh.vertices:
                co = mat_w @ vert.co
                new_x = round(co.x / 4.0) * 4.0
                new_y = round(co.y / 4.0) * 4.0
                inv = mat_w.inverted()
                from mathutils import Vector
                new_co = inv @ Vector((new_x, new_y, co.z))
                vert.co = new_co
                count += 1
            mesh.update()
        self.report({'INFO'}, f"{T('Привязано вершин:')} {count}")
        return {'FINISHED'}


class GTATOOLS_OT_water_set_params(bpy.types.Operator):
    """Задать параметры воды для выделенных объектов"""
    bl_idname = "gtatools.water_set_params"
    bl_label = "Set Water Parameters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        flag = int(scene.gtatools_water_flag)
        speed_x = scene.gtatools_water_speed_x
        speed_y = scene.gtatools_water_speed_y
        speed_z = scene.gtatools_water_speed_z
        wave = scene.gtatools_water_wave_height

        import bmesh
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            obj['water_flag'] = flag
            mesh = obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)

            sx = bm.verts.layers.float.get('water_speed_x') or bm.verts.layers.float.new('water_speed_x')
            sy = bm.verts.layers.float.get('water_speed_y') or bm.verts.layers.float.new('water_speed_y')
            sz = bm.verts.layers.float.get('water_speed_z') or bm.verts.layers.float.new('water_speed_z')
            wh = bm.verts.layers.float.get('water_wave_height') or bm.verts.layers.float.new('water_wave_height')

            for v in bm.verts:
                v[sx] = speed_x
                v[sy] = speed_y
                v[sz] = speed_z
                v[wh] = wave

            bm.to_mesh(mesh)
            bm.free()
            count += 1

        self.report({'INFO'}, f"{T('Параметры воды:')} {count} objects")
        return {'FINISHED'}


class GTATOOLS_OT_water_stitch(bpy.types.Operator):
    """Сшить края двух водных плоскостей (выровнять ближайшие вершины)"""
    bl_idname = "gtatools.water_stitch"
    bl_label = "Stitch Water Edges"
    bl_options = {'REGISTER', 'UNDO'}

    threshold: FloatProperty(name="Threshold", default=1.0, min=0.01, max=50.0)

    def execute(self, context):
        from mathutils import kdtree

        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if len(mesh_objects) < 2:
            self.report({'ERROR'}, T("Выделите минимум 2 меш объекта"))
            return {'CANCELLED'}

        # Collect all boundary vertices (edges with only 1 face)
        all_boundary = []  # [(world_co, obj, vert_index)]

        for obj in mesh_objects:
            mesh = obj.data
            mat_w = obj.matrix_world

            # Find boundary vertices
            vert_face_count = [0] * len(mesh.vertices)
            for poly in mesh.polygons:
                for vi in poly.vertices:
                    vert_face_count[vi] += 1

            for edge in mesh.edges:
                edge_faces = 0
                for poly in mesh.polygons:
                    verts = list(poly.vertices)
                    if edge.vertices[0] in verts and edge.vertices[1] in verts:
                        edge_faces += 1
                if edge_faces == 1:  # boundary edge
                    for vi in edge.vertices:
                        co = mat_w @ mesh.vertices[vi].co
                        all_boundary.append((co, obj, vi))

        if not all_boundary:
            self.report({'WARNING'}, T("Нет граничных вершин"))
            return {'CANCELLED'}

        # Match boundary vertices between objects
        stitched = 0
        for i, (co1, obj1, vi1) in enumerate(all_boundary):
            for j, (co2, obj2, vi2) in enumerate(all_boundary):
                if obj1 == obj2 or j <= i:
                    continue
                dist = (co1 - co2).length
                if dist < self.threshold:
                    # Average position
                    avg = (co1 + co2) / 2.0
                    inv1 = obj1.matrix_world.inverted()
                    inv2 = obj2.matrix_world.inverted()
                    obj1.data.vertices[vi1].co = inv1 @ avg
                    obj2.data.vertices[vi2].co = inv2 @ avg
                    stitched += 1

        for obj in mesh_objects:
            obj.data.update()

        self.report({'INFO'}, f"{T('Сшито вершин:')} {stitched}")
        return {'FINISHED'}


class GTATOOLS_PT_water_panel(bpy.types.Panel):
    """Панель Water IO"""
    bl_label = "Water"
    bl_idname = "GTATOOLS_PT_water_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Import / Export
        row = layout.row(align=True)
        row.operator("gtatools.import_water", text=T("Импорт"), icon='IMPORT')
        row.operator("gtatools.export_water", text=T("Экспорт"), icon='EXPORT')

        layout.separator()

        # Add water
        layout.operator("gtatools.add_water", text=T("Добавить воду"), icon='SHADING_RENDERED')

        layout.separator()

        # Water parameters
        box = layout.box()
        box.label(text=T("Параметры воды:"), icon='PREFERENCES')
        flag_labels = {
            '0': T("Обычная / Невидимая"),
            '1': T("Обычная / Видимая"),
            '2': T("Мелкая / Невидимая"),
            '3': T("Мелкая / Видимая"),
        }
        box.prop_menu_enum(scene, "gtatools_water_flag", text=flag_labels.get(scene.gtatools_water_flag, "?"))
        box.label(text=T("Скорость течения:"))
        row = box.row(align=True)
        row.prop(scene, "gtatools_water_speed_x", text="X")
        row.prop(scene, "gtatools_water_speed_y", text="Y")
        row.prop(scene, "gtatools_water_speed_z", text="Z")
        box.prop(scene, "gtatools_water_wave_height", text=T("Волны"))
        box.operator("gtatools.water_set_params", text=T("Применить"), icon='CHECKMARK')

        layout.separator()

        # Tools
        box = layout.box()
        box.label(text=T("Инструменты:"), icon='TOOL_SETTINGS')
        box.operator("gtatools.water_snap_grid", text=T("Привязка к сетке (x4)"), icon='SNAP_GRID')
        box.operator("gtatools.water_stitch", text=T("Сшить края"), icon='AUTOMERGE_ON')

        # Show active object water info
        obj = context.active_object
        if obj and obj.type == 'MESH' and 'water_flag' in obj:
            layout.separator()
            box = layout.box()
            flag = obj.get('water_flag', -1)
            flag_names = {
                0: "Default / Invisible",
                1: "Default / Visible",
                2: "Shallow / Invisible",
                3: "Shallow / Visible",
            }
            box.label(text=f"{obj.name}: {flag_names.get(flag, '?')} (flag={flag})", icon='INFO')


# =============================================================================
# IFP (ANIMATION) OPERATORS
# =============================================================================

class GTATOOLS_OT_import_ifp(bpy.types.Operator):
    """Импорт IFP — анимации GTA SA"""
    bl_idname = "gtatools.import_ifp"
    bl_label = "Import IFP"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ifp", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.ifp_import import import_ifp
        try:
            actions = import_ifp(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"IFP: {len(actions)} animations imported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IFP import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_ifp(bpy.types.Operator):
    """Экспорт IFP — анимации GTA SA"""
    bl_idname = "gtatools.export_ifp"
    bl_label = "Export IFP"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ifp", options={'HIDDEN'})
    package_name: StringProperty(name="Package", default="custom")

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "custom.ifp"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.ifp_export import export_ifp
        try:
            count = export_ifp(filepath=self.filepath, package_name=self.package_name)
            self.report({'INFO'}, f"IFP: {count} animations exported")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IFP export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_apply_ifp(bpy.types.Operator):
    """Применить IFP анимацию к выделенному скелету"""
    bl_idname = "gtatools.apply_ifp"
    bl_label = "Apply IFP Animation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and
                context.scene.gtatools_ifp_action != '')

    def execute(self, context):
        from .ops.ifp_import import apply_ifp_action
        name = context.scene.gtatools_ifp_action
        armature = context.active_object

        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, T("Выделите скелет (Armature)"))
            return {'CANCELLED'}

        ok, msg = apply_ifp_action(name, armature, context)
        if ok:
            self.report({'INFO'}, msg)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}


class GTATOOLS_PT_anim_panel(bpy.types.Panel):
    """Панель анимаций IFP"""
    bl_label = T("Анимации")
    bl_idname = "GTATOOLS_PT_anim_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        _bone_id = _icons.get_icon("bone")
        if _bone_id:
            box.label(text=T("Анимации IFP (GTA SA):"), icon_value=_bone_id)
        else:
            box.label(text=T("Анимации IFP (GTA SA):"), icon='ACTION')
        row = box.row(align=True)
        row.operator("gtatools.import_ifp", text=T("Импорт"), icon='IMPORT')
        row.operator("gtatools.export_ifp", text=T("Экспорт"), icon='EXPORT')
        _clap_id = _icons.get_icon("clapper")
        if _clap_id:
            box.operator("gtatools.ifp_batch_import",
                         text=T("Batch папка…"), icon_value=_clap_id)
        else:
            box.operator("gtatools.ifp_batch_import",
                         text=T("Batch папка…"), icon='FILE_FOLDER')

        # IFP actions list
        ifp_actions = [a for a in bpy.data.actions if a.get('ifp_source')]
        if ifp_actions:
            box.label(text=f"{len(ifp_actions)} {T('анимаций загружено')}")

            obj = context.active_object
            if obj and obj.type == 'ARMATURE':
                # Dropdown with search
                box.prop_search(context.scene, "gtatools_ifp_action", bpy.data, "actions",
                                text=T("Анимация"), icon='ACTION')
                box.operator("gtatools.apply_ifp", text=T("Применить анимацию"), icon='PLAY')

                if obj.animation_data and obj.animation_data.action:
                    action = obj.animation_data.action
                    box.label(text=f"{T('Текущая')}: {action.name}", icon='ARMATURE_DATA')

            else:
                box.label(text=T("Выделите скелет для применения"), icon='INFO')


# ── X Radar Maker ────────────────────────────────────────────────────

class GTATOOLS_OT_radar_generate(bpy.types.Operator):
    """Генерировать тайлы радара GTA SA"""
    bl_idname = "gtatools.radar_generate"
    bl_label = "Generate Radars"
    bl_options = {'REGISTER'}

    mode: StringProperty(default='ALL')  # ALL, MENU, FULL, FULL_MENU, SPECIFIC

    def execute(self, context):
        scn = context.scene
        output_dir = bpy.path.abspath(scn.gtatools_radar_output)
        if not output_dir:
            self.report({'ERROR'}, T("Укажите папку для сохранения"))
            return {'CANCELLED'}
        os.makedirs(output_dir, exist_ok=True)

        height = scn.gtatools_radar_height
        size = scn.gtatools_radar_size
        gamma = scn.gtatools_radar_gamma

        # GTA SA map: -3000 to 3000
        map_half = 3000.0

        # Create temp camera
        cam_data = bpy.data.cameras.new("_RadarCam")
        cam_data.type = 'ORTHO'
        cam_data.clip_start = 1.0
        cam_data.clip_end = height + 5000.0
        cam_obj = bpy.data.objects.new("_RadarCam", cam_data)
        context.scene.collection.objects.link(cam_obj)
        cam_obj.location.z = height
        cam_obj.rotation_euler = (0, 0, 0)

        old_cam = scn.camera
        scn.camera = cam_obj

        # Save render settings
        old_x = scn.render.resolution_x
        old_y = scn.render.resolution_y
        old_path = scn.render.filepath
        old_format = scn.render.image_settings.file_format

        scn.render.image_settings.file_format = 'PNG'
        scn.render.resolution_x = size
        scn.render.resolution_y = size

        wm = context.window_manager
        count = 0

        if self.mode == 'FULL':
            # One full radar image
            cam_data.ortho_scale = map_half * 2
            cam_obj.location.x = 0
            cam_obj.location.y = 0
            filepath = os.path.join(output_dir, "FullRadar.png")
            scn.render.filepath = filepath
            bpy.ops.render.render(write_still=True)
            count = 1

        elif self.mode == 'FULL_MENU':
            cam_data.ortho_scale = map_half * 2
            cam_obj.location.x = 0
            cam_obj.location.y = 0
            filepath = os.path.join(output_dir, "FullMenuRadar.png")
            scn.render.filepath = filepath
            bpy.ops.render.render(write_still=True)
            count = 1

        elif self.mode == 'MENU':
            # 3x3 menu radar
            grid = 3
            sect_size = map_half * 2 / grid
            cam_data.ortho_scale = sect_size
            wm.progress_begin(0, grid * grid)
            names = [
                "MapTop01", "MapTop02", "MapTop03",
                "MapMid01", "MapMid02", "MapMid03",
                "MapBot01", "MapBot02", "MapBot03",
            ]
            idx = 0
            for y in range(grid):
                for x in range(grid):
                    cam_obj.location.x = -map_half + sect_size * (x + 0.5)
                    cam_obj.location.y = map_half - sect_size * (y + 0.5)
                    filepath = os.path.join(output_dir, names[idx] + ".png")
                    scn.render.filepath = filepath
                    bpy.ops.render.render(write_still=True)
                    idx += 1
                    wm.progress_update(idx)
            wm.progress_end()
            count = grid * grid

        elif self.mode == 'SPECIFIC':
            # Specific tiles by index
            grid = scn.gtatools_radar_grid
            sect_size = map_half * 2 / grid
            cam_data.ortho_scale = sect_size
            indices_str = scn.gtatools_radar_specific.strip()
            if not indices_str:
                self.report({'WARNING'}, T("Укажите индексы тайлов (например 0,1,8,9)"))
                bpy.data.objects.remove(cam_obj, do_unlink=True)
                bpy.data.cameras.remove(cam_data)
                scn.camera = old_cam
                scn.render.resolution_x = old_x
                scn.render.resolution_y = old_y
                scn.render.filepath = old_path
                scn.render.image_settings.file_format = old_format
                return {'CANCELLED'}
            indices = []
            for part in indices_str.split(','):
                part = part.strip()
                if part.isdigit():
                    idx = int(part)
                    if 0 <= idx < grid * grid:
                        indices.append(idx)

            wm.progress_begin(0, len(indices))
            for i, radar_idx in enumerate(indices):
                x = radar_idx % grid
                y = radar_idx // grid
                cam_obj.location.x = -map_half + sect_size * (x + 0.5)
                cam_obj.location.y = map_half - sect_size * (y + 0.5)
                name = f"radar{radar_idx:02d}"
                filepath = os.path.join(output_dir, name + ".png")
                scn.render.filepath = filepath
                bpy.ops.render.render(write_still=True)
                wm.progress_update(i + 1)
                count += 1
            wm.progress_end()

        else:
            # ALL: full grid
            grid = scn.gtatools_radar_grid
            sect_size = map_half * 2 / grid
            cam_data.ortho_scale = sect_size
            total = grid * grid
            wm.progress_begin(0, total)
            for y in range(grid):
                for x in range(grid):
                    radar_idx = y * grid + x
                    cam_obj.location.x = -map_half + sect_size * (x + 0.5)
                    cam_obj.location.y = map_half - sect_size * (y + 0.5)
                    name = f"radar{radar_idx:02d}"
                    filepath = os.path.join(output_dir, name + ".png")
                    scn.render.filepath = filepath
                    bpy.ops.render.render(write_still=True)
                    wm.progress_update(radar_idx + 1)
                    count += 1
            wm.progress_end()

        # Cleanup
        scn.camera = old_cam
        scn.render.resolution_x = old_x
        scn.render.resolution_y = old_y
        scn.render.filepath = old_path
        scn.render.image_settings.file_format = old_format
        bpy.data.objects.remove(cam_obj, do_unlink=True)
        bpy.data.cameras.remove(cam_data)

        self.report({'INFO'}, f"Radar: {count} {T('тайлов сохранено')}")
        return {'FINISHED'}


class GTATOOLS_OT_radar_pack_txd(bpy.types.Operator):
    """Упаковать тайлы радара в TXD архивы (1 тайл = 1 TXD)"""
    bl_idname = "gtatools.radar_pack_txd"
    bl_label = "Pack Radar to TXD"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scn = context.scene
        output_dir = bpy.path.abspath(scn.gtatools_radar_output)
        if not output_dir:
            self.report({'ERROR'}, T("Укажите папку для сохранения"))
            return {'CANCELLED'}

        grid = scn.gtatools_radar_grid
        use_gpu = check_nvtt_available(getattr(scn, 'gtatools_nvtt_path', ''))[0]

        txd_dir = os.path.join(output_dir, "txd")
        os.makedirs(txd_dir, exist_ok=True)

        wm = context.window_manager
        total = grid * grid
        wm.progress_begin(0, total)
        packed = 0

        # Create temp object with temp material for TXD export
        temp_mesh = bpy.data.meshes.new("_radar_tmp")
        temp_obj = bpy.data.objects.new("_radar_tmp", temp_mesh)
        context.scene.collection.objects.link(temp_obj)

        for radar_idx in range(total):
            name = f"radar{radar_idx:02d}"
            png_path = os.path.join(output_dir, name + ".png")

            if not os.path.isfile(png_path):
                wm.progress_update(radar_idx + 1)
                continue

            # Load image
            img = bpy.data.images.load(png_path, check_existing=False)
            img.name = name

            # Create temp material
            mat = bpy.data.materials.new(name=name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            bsdf = None
            for n in nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    bsdf = n
                    break
            if bsdf:
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.image = img
                mat.node_tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

            # Assign to temp object
            temp_obj.data.materials.clear()
            temp_obj.data.materials.append(mat)

            # Select only temp object
            bpy.ops.object.select_all(action='DESELECT')
            temp_obj.select_set(True)
            context.view_layer.objects.active = temp_obj

            # Export TXD
            txd_path = os.path.join(txd_dir, name + ".txd")
            try:
                result, msg, _ = export_txd(txd_path, context, selected_only=True, use_gpu=use_gpu)
                if result == {'FINISHED'}:
                    packed += 1
            except Exception as e:
                print(f"[Radar TXD] {name}: {e}")

            # Cleanup temp material and image
            bpy.data.materials.remove(mat)
            bpy.data.images.remove(img)
            wm.progress_update(radar_idx + 1)

        # Remove temp object
        bpy.data.objects.remove(temp_obj, do_unlink=True)
        bpy.data.meshes.remove(temp_mesh)

        wm.progress_end()
        self.report({'INFO'}, f"TXD: {packed} {T('архивов создано')}")
        return {'FINISHED'}


class GTATOOLS_PT_radar_panel(bpy.types.Panel):
    """X Radar Maker — генерация тайлов мини-карты GTA SA"""
    bl_label = "X Radar Maker"
    bl_idname = "GTATOOLS_PT_radar_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        layout.prop(scn, "gtatools_radar_output", text=T("Папка"))
        col = layout.column(align=True)
        col.prop(scn, "gtatools_radar_grid", text=T("Сетка"))
        col.prop(scn, "gtatools_radar_size", text=T("Размер"))
        col.prop(scn, "gtatools_radar_height", text=T("Высота"))

        layout.separator()

        op = layout.operator("gtatools.radar_generate", text=T("Генерировать радар"), icon='RENDER_RESULT')
        op.mode = 'ALL'
        op = layout.operator("gtatools.radar_generate", text=T("Меню радар (3x3)"), icon='RENDER_RESULT')
        op.mode = 'MENU'

        row = layout.row(align=True)
        op = row.operator("gtatools.radar_generate", text=T("Полный радар"), icon='IMAGE')
        op.mode = 'FULL'
        op = row.operator("gtatools.radar_generate", text=T("Полный меню"), icon='IMAGE')
        op.mode = 'FULL_MENU'

        layout.separator()
        layout.prop(scn, "gtatools_radar_specific", text=T("Индексы"))
        op = layout.operator("gtatools.radar_generate", text=T("Указанные тайлы"), icon='RENDER_RESULT')
        op.mode = 'SPECIFIC'
        layout.separator()
        layout.operator("gtatools.radar_pack_txd", text=T("Упаковать в TXD"), icon='PACKAGE')


class GTATOOLS_PT_paths_panel(bpy.types.Panel):
    """Панель Path IO"""
    bl_label = T("Пути")
    bl_idname = "GTATOOLS_PT_paths_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        # Convert to path button (top)
        obj = context.active_object
        if obj and (obj.type == 'CURVE' or (obj.type == 'MESH' and len(obj.data.polygons) == 0)):
            if obj.get('path_type') != 'path_ipl':
                layout.operator("gtatools.convert_to_path", text=T("Конвертировать в путь"), icon='CURVE_PATH')

        # Paths IPL (main — for gta.dat)
        box = layout.box()
        box.label(text=T("Пути (paths.ipl):"), icon='TRACKING')
        row = box.row(align=True)
        row.operator("gtatools.import_paths_ipl", text=T("Импорт"), icon='IMPORT')
        row.operator("gtatools.export_paths_ipl", text=T("Экспорт"), icon='EXPORT')
        box.operator("gtatools.add_path_ipl", text=T("Создать путь"), icon='ADD')
        # Roadblocks / Traffic Lights — visible only in Edit Curve on path_ipl
        if (obj and obj.type == 'CURVE' and obj.get('path_type') == 'path_ipl'
                and context.mode == 'EDIT_CURVE'):
            _rb_id = _icons.get_icon("roadblock")
            sub = box.column(align=True)
            if _rb_id:
                sub.label(text=T("Флаги выделенных точек:"),
                          icon_value=_rb_id)
            else:
                sub.label(text=T("Флаги выделенных точек:"), icon='CONSTRAINT')
            op = sub.operator("gtatools.path_node_flag",
                              text=T("Переключить Roadblock"))
            op.action = 'TOGGLE_ROADBLOCK'
            row = sub.row(align=True)
            op = row.operator("gtatools.path_node_flag", text=T("Светофор —"))
            op.action = 'TRAFFIC_NONE'
            op = row.operator("gtatools.path_node_flag", text=T("Обычн."))
            op.action = 'TRAFFIC_NORMAL'
            op = row.operator("gtatools.path_node_flag", text=T("Ж/д"))
            op.action = 'TRAFFIC_RAIL'
            op = row.operator("gtatools.path_node_flag", text=T("Авт."))
            op.action = 'TRAFFIC_BUS'

        layout.separator()

        # Train tracks
        box = layout.box()
        box.label(text=T("Ж/д пути:"), icon='CON_FOLLOWPATH')
        row = box.row(align=True)
        row.operator("gtatools.import_track", text=T("Импорт"), icon='IMPORT')
        row.operator("gtatools.export_track", text=T("Экспорт"), icon='EXPORT')
        box.operator("gtatools.add_track", text=T("Создать ж/д путь"), icon='ADD')
        obj = context.active_object
        if (obj and obj.type == 'CURVE' and obj.get('path_type') == 'track'
                and context.mode == 'EDIT_CURVE'):
            box.operator("gtatools.mark_station", text=T("Станция (вкл/выкл)"), icon='DECORATE_KEYFRAME')
        # Station markers refresh — works in object mode too
        if obj and obj.type == 'CURVE' and obj.get('path_type') == 'track':
            _train_id = _icons.get_icon("train")
            if _train_id:
                box.operator("gtatools.refresh_station_markers",
                             text=T("Обновить маркеры станций"),
                             icon_value=_train_id)
            else:
                box.operator("gtatools.refresh_station_markers",
                             text=T("Обновить маркеры станций"),
                             icon='EMPTY_SINGLE_ARROW')

        layout.separator()

        # Compiled nodes (NODES*.DAT)
        box = layout.box()
        box.label(text=T("Скомпилированные (NODES):"), icon='FILE_CACHE')
        row = box.row(align=True)
        row.operator("gtatools.import_nodes", text=T("Импорт"), icon='IMPORT')
        row.operator("gtatools.export_nodes", text=T("Экспорт"), icon='EXPORT')

        # Info about selected path object
        obj = context.active_object
        if obj and 'path_type' in obj:
            layout.separator()
            box = layout.box()
            pt = obj.get('path_type', '')
            type_names = {
                'track': T("Ж/д путь"),
                'path_ipl': T("Путь IPL"),
                'nodes_vehicle': T("Авто пути"),
                'nodes_ped': T("Пешеходные пути"),
                'nodes_navi': T("Навигационные точки"),
            }
            label = type_names.get(pt, pt)
            if pt == 'path_ipl':
                gt = obj.get('group_type', 1)
                gt_label = T("Авто") if gt == 1 else T("Пешеходный")
                count = sum(len(s.points) for s in obj.data.splines)
                box.label(text=f"{obj.name}: {gt_label} ({count}/12 pts)", icon='INFO')
            elif obj.type == 'CURVE':
                count = sum(len(s.points) for s in obj.data.splines)
                stations = obj.get('station_indices', '[]')
                try:
                    num_st = len(eval(stations))
                except Exception:
                    num_st = 0
                box.label(text=f"{obj.name}: {label} ({count} pts, {num_st} stations)", icon='INFO')
            elif obj.type == 'MESH':
                box.label(text=f"{obj.name}: {label} ({len(obj.data.vertices)} nodes)", icon='INFO')


# =============================================================================
# =============================================================================
# REGISTRATION
# =============================================================================

classes = (
    INUParticleKeyframe,
    INUObjectProps,
    INUMaterialProps,
    GTATOOLS_ImgFileEntry,
    GTATOOLS_BinaryIplEntry,
    GTATOOLS_UL_img_files,
    GTATOOLS_OT_refresh_img_list,
    GTATOOLS_OT_scan_binary_ipls,
    GTATOOLS_OT_binary_ipl_toggle_all,
    GTATOOLS_FillColorItem,
    GTATOOLS_OT_toggle_visibility,
    GTATOOLS_OT_snap_to_dff,
    GTATOOLS_OT_check_geometry,
    GTATOOLS_OT_check_ngons,
    GTATOOLS_OT_clear_raw_dff,
    GTATOOLS_OT_sa_vehicle_preset,
    GTATOOLS_OT_apply_vehicle_pipeline,
    GTATOOLS_OT_export_txd,
    GTATOOLS_OT_export_shared_txd,
    GTATOOLS_OT_copy_color_attr,
    GTATOOLS_OT_export_dff,
    GTATOOLS_OT_export_col,
    GTATOOLS_OT_export_all,
    GTATOOLS_OT_inu_export,
    GTATOOLS_OT_info_tooltip,
    GTATOOLS_OT_detect_models,
    GTATOOLS_OT_prelight,
    GTATOOLS_OT_average_colors,
    GTATOOLS_OT_lightmap_generate,
    GTATOOLS_OT_lightmap_copy,
    GTATOOLS_OT_lightmap_clear,
    GTATOOLS_OT_create_prelight_lights,
    GTATOOLS_OT_remove_prelight_lights,
    GTATOOLS_OT_bake_vertex_colors,
    GTATOOLS_OT_bake_vertex_colors_simple,
    GTATOOLS_OT_reset_bake_settings,
    GTATOOLS_OT_prelight_preset_load,
    GTATOOLS_OT_prelight_preset_save,
    GTATOOLS_OT_prelight_preset_delete,
    GTATOOLS_OT_reset_scatter_settings,
    GTATOOLS_OT_analyze_vertex_colors,
    GTATOOLS_OT_apply_v_offset,
    GTATOOLS_OT_vc_smooth,
    GTATOOLS_OT_vc_contrast,
    GTATOOLS_OT_vc_brightness,
    GTATOOLS_OT_vc_gamma,
    GTATOOLS_OT_vc_smooth_between,
    GTATOOLS_OT_load_lightmap,
    GTATOOLS_OT_remove_lightmap,
    GTATOOLS_OT_create_day_night,
    GTATOOLS_OT_prelight_preview,
    GTATOOLS_OT_fix_itera_collection,
    GTATOOLS_OT_apply_itera_material,
    GTATOOLS_OT_apply_itera_quickstart,
    GTATOOLS_OT_remove_itera_material,
    GTATOOLS_OT_save_materials,
    GTATOOLS_OT_restore_materials,
    GTATOOLS_OT_eyedropper_color,
    GTATOOLS_OT_fill_faces,
    GTATOOLS_OT_restore_fill,
    GTATOOLS_OT_remove_fill_color,
    GTATOOLS_OT_select_fill_color,
    GTATOOLS_OT_delete_fill_color_level,
    GTATOOLS_OT_clear_fill_color_levels,
    GTATOOLS_OT_scatter_light,
    GTATOOLS_OT_toggle_face_select,
    GTATOOLS_OT_switch_to_edit,
    GTATOOLS_OT_switch_to_vpaint,
    GTATOOLS_OT_select_color_attribute,
    GTATOOLS_OT_add_color_attribute,
    GTATOOLS_OT_remove_color_attribute,
    GTATOOLS_OT_create_color_attr,
    GTATOOLS_OT_remove_color_attr,
    GTATOOLS_OT_load_textures,
    GTATOOLS_OT_set_blend_folder,
    GTATOOLS_OT_drop_texture_as_material,
    GTATOOLS_FH_texture_drop,
    GTATOOLS_OT_drop_txd,
    GTATOOLS_FH_txd_drop,
    GTATOOLS_OT_check_materials,
    GTATOOLS_OT_cleanup_materials,
    GTATOOLS_OT_sort_materials,
    GTATOOLS_OT_reset_transform,
    GTATOOLS_OT_apply_lightmap_uv2,
    GTATOOLS_OT_remove_lightmap_uv2,
    GTATOOLS_OT_toggle_lightmap_uv2,
    GTATOOLS_OT_id_manager_open_file,
    GTATOOLS_OT_id_manager_release,
    GTATOOLS_OT_id_manager_auto_assign,
    GTATOOLS_OT_id_manager_assign_from,
    GTATOOLS_OT_batch_set_type,
    GTATOOLS_OT_id_manager_clear_selected,
    GTATOOLS_OT_id_manager_clear,
    GTATOOLS_OT_id_manager_create,
    GTATOOLS_OT_id_manager_extend,
    GTATOOLS_OT_id_manager_sync_scene,
    GTATOOLS_OT_id_manager_from_game,
    GTATOOLS_OT_id_preset_new,
    GTATOOLS_OT_id_preset_delete,
    GTATOOLS_OT_id_preset_rename,
    GTATOOLS_OT_toggle_uv_editor,
    GTATOOLS_OT_toggle_uv_grid,
    GTATOOLS_OT_randomize_uv_grid,
    GTATOOLS_OT_snap_uv_to_grid,
    GTATOOLS_OT_set_uv_align,
    GTATOOLS_PT_main_panel,
    GTATOOLS_OT_import_dff,
    GTATOOLS_OT_import_col,
    GTATOOLS_OT_import_txd,
    GTATOOLS_OT_inu_import,
    GTATOOLS_OT_toggle_links,
    GTATOOLS_OT_toggle_bbox,
    GTATOOLS_OT_extract_resources,
    GTATOOLS_OT_load_map_glb,
    GTATOOLS_OT_build_map_glb,
    GTATOOLS_OT_import_map,
    GTATOOLS_OT_replace_fake_with_dff,
    GTATOOLS_OT_import_ipl_sections,
    GTATOOLS_OT_export_ipl_sections,
    GTATOOLS_OT_import_from_img,
    GTATOOLS_OT_import_water,
    GTATOOLS_OT_export_water,
    GTATOOLS_OT_add_water,
    GTATOOLS_OT_water_snap_grid,
    GTATOOLS_OT_water_set_params,
    GTATOOLS_OT_water_stitch,
    GTATOOLS_OT_import_track,
    GTATOOLS_OT_export_track,
    GTATOOLS_OT_import_nodes,
    GTATOOLS_OT_export_nodes,
    GTATOOLS_OT_import_ifp,
    GTATOOLS_OT_export_ifp,
    GTATOOLS_OT_apply_ifp,
    GTATOOLS_OT_import_paths_ipl,
    GTATOOLS_OT_export_paths_ipl,
    GTATOOLS_OT_convert_to_path,
    GTATOOLS_OT_add_path_ipl,
    GTATOOLS_OT_add_track,
    GTATOOLS_OT_add_vehicle_path,
    GTATOOLS_OT_add_ped_path,
    GTATOOLS_OT_mark_station,
    GTATOOLS_OT_export_to_img,
    GTATOOLS_OT_remove_from_img,
    GTATOOLS_OT_upsert_ide,
    GTATOOLS_OT_upsert_ipl,
    GTATOOLS_OT_remove_ide,
    GTATOOLS_OT_remove_ipl,
    GTATOOLS_OT_export_ide,
    GTATOOLS_OT_export_ipl,
    GTATOOLS_OT_import_ide,
    GTATOOLS_OT_import_ipl,
    GTATOOLS_OT_replace_ipl_placeholders,
    GTATOOLS_PT_ide_ipl_panel,
    GTATOOLS_PT_export_panel,
    GTATOOLS_PT_check_panel,
    GTATOOLS_OT_apply_2dfx_preset,
    GTATOOLS_OT_create_2dfx,
    GTATOOLS_OT_attach_2dfx,
    GTATOOLS_OT_detach_2dfx,
    GTATOOLS_OT_detach_all_2dfx,
    GTATOOLS_OT_refresh_2dfx_preview,
    GTATOOLS_OT_remove_2dfx_preview,
    GTATOOLS_OT_select_particle_effect,
    GTATOOLS_OT_particle_effect_new,
    GTATOOLS_OT_particle_effect_delete,
    GTATOOLS_OT_particle_emitter_switch,
    GTATOOLS_OT_particle_curve_select,
    GTATOOLS_OT_particle_curve_key_add,
    GTATOOLS_OT_particle_curve_key_remove,
    GTATOOLS_OT_particle_curve_key_select_row,
    GTATOOLS_OT_particle_curve_write,
    GTATOOLS_OT_reload_effects_fxp,
    GTATOOLS_OT_save_particle_effect,
    GTATOOLS_OT_set_col_surface,
    GTATOOLS_OT_col_surface_menu,
    GTATOOLS_PT_col_material_panel,
    GTATOOLS_PT_material_effects_panel,
    GTATOOLS_PT_object_ide_ipl_panel,
    GTATOOLS_PT_inu_tools_panel,
    GTATOOLS_PT_itera_panel,
    GTATOOLS_PT_prelight_panel,
    GTATOOLS_PT_bake_settings_subpanel,
    GTATOOLS_PT_vc_postprocess_panel,
    GTATOOLS_OT_preview_col_light,
    GTATOOLS_OT_bake_col_light,
    GTATOOLS_OT_clear_col_light_mats,
    GTATOOLS_PT_prelight_col_panel,
    GTATOOLS_PT_2dfx_panel,
    GTATOOLS_PT_vertex_paint_panel,
    GTATOOLS_PT_lightmap_panel,
    GTATOOLS_PT_water_panel,
    GTATOOLS_PT_anim_panel,
    GTATOOLS_OT_radar_generate,
    GTATOOLS_OT_radar_pack_txd,
    GTATOOLS_PT_radar_panel,
    GTATOOLS_PT_paths_panel,
    GTATOOLS_PT_uv_tools_panel,
    GTATOOLS_OT_add_gtasa_model,
    VIEW3D_MT_gtasa_add_menu,
    GTATOOLS_OT_bitmaps_scan,
    GTATOOLS_OT_bitmaps_resolve,
    GTATOOLS_OT_bitmaps_copy,
    GTATOOLS_OT_bitmaps_find_dupes,
    GTATOOLS_PT_bitmaps_panel,
    GTATOOLS_OT_ifp_batch_import,
    GTATOOLS_OT_refresh_station_markers,
    GTATOOLS_OT_path_node_flag,
    GTATOOLS_OT_map_export,
    GTATOOLS_PT_map_export_panel,
    GTATOOLS_OT_material_preset,
    GTATOOLS_PT_gta_material_panel,
    GTATOOLS_OT_import_cst,
    GTATOOLS_OT_export_cst,
    GTATOOLS_OT_vehicle_scale,
)


# ── Persistent paths (saved in Blender config, survive addon updates) ──

_PATHS_FILE = None

def _write_png(path: str, pixels: bytes, width: int, height: int):
    """Write RGBA pixels to PNG file using pure Python (zlib + struct)."""
    import zlib
    import struct as _st

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = _st.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return _st.pack('>I', len(data)) + c + crc

    # IHDR
    ihdr = _st.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)  # 8bit RGBA

    # IDAT — raw scanlines with filter byte 0 per row
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)  # filter: None
        row_start = y * stride
        raw.extend(pixels[row_start:row_start + stride])

    compressed = zlib.compress(bytes(raw), 1)  # fast compression

    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')  # PNG signature
        f.write(_chunk(b'IHDR', ihdr))
        f.write(_chunk(b'IDAT', compressed))
        f.write(_chunk(b'IEND', b''))


def _write_dds(path: str, tex):
    """Write a TxdTexture as an uncompressed RGBA DDS file for nvdecompress."""
    import struct as _st
    w, h = tex.width, tex.height
    # DDS header (128 bytes)
    header = bytearray(128)
    _st.pack_into('<4s', header, 0, b'DDS ')
    _st.pack_into('<I', header, 4, 124)        # header size
    _st.pack_into('<I', header, 8, 0x1 | 0x2 | 0x4 | 0x1000 | 0x8)  # flags
    _st.pack_into('<I', header, 12, h)          # height
    _st.pack_into('<I', header, 16, w)          # width
    _st.pack_into('<I', header, 20, w * 4)      # pitch
    # Pixel format at offset 76
    _st.pack_into('<I', header, 76, 32)         # pf size
    _st.pack_into('<I', header, 80, 0x41)       # pf flags (RGBA)
    _st.pack_into('<I', header, 88, 32)         # RGB bit count
    _st.pack_into('<I', header, 92, 0x000000FF)  # R mask
    _st.pack_into('<I', header, 96, 0x0000FF00)  # G mask
    _st.pack_into('<I', header, 100, 0x00FF0000) # B mask
    _st.pack_into('<I', header, 104, 0xFF000000) # A mask
    _st.pack_into('<I', header, 108, 0x1000)    # caps (texture)

    with open(path, 'wb') as f:
        f.write(header)
        f.write(tex.pixels)


_VEG_NAME_KEYWORDS = {'tree', 'palm', 'bush', 'grass', 'veg_', 'genveg_',
                       'cactus', 'cacti', 'fern', 'ivy', 'plant', 'flower',
                       'hedge', 'weed', 'leaf', 'leaves'}
_VEG_TXD_KEYWORDS = {'gta_tree_', 'gta_proc_', 'gta_cactus', 'veg_',
                      'gta_potplant', 'kbplantsm'}


def _is_vegetation(model_name: str, txd_name: str = "") -> bool:
    """Check if model is vegetation by name and TXD patterns."""
    low = model_name.lower()
    for kw in _VEG_NAME_KEYWORDS:
        if kw in low:
            return True
    if txd_name:
        txd_low = txd_name.lower()
        for kw in _VEG_TXD_KEYWORDS:
            if kw in txd_low:
                return True
    return False


def _sort_map_objects(context, objects: list, ide_models: dict):
    """Sort imported map objects into collections by category."""
    def _get_col(name):
        c = bpy.data.collections.get(name)
        if not c:
            c = bpy.data.collections.new(name)
            context.scene.collection.children.link(c)
        return c

    col_buildings = _get_col("Map_Buildings")
    col_props = _get_col("Map_Props")
    col_vegetation = _get_col("Map_Vegetation")
    col_small = _get_col("Map_Small")
    col_lod = _get_col("Map_LOD")

    # Build name→IDE lookup from ide_models
    name_to_ide = {}
    for mid, obj in ide_models.items():
        name_to_ide[obj.model_name.lower()] = obj

    for obj in objects:
        if obj.type not in ('MESH', 'EMPTY'):
            continue

        # Extract model name: "modelname.dff" or "modelname.dff.001"
        name = obj.name
        # Remove .dff suffix and Blender .NNN suffix
        model_name = name
        if '.dff' in model_name:
            model_name = model_name.split('.dff')[0]

        low = model_name.lower()

        # Find IDE data and set properties
        ide_obj = name_to_ide.get(low)
        if ide_obj and hasattr(obj, 'inu'):
            obj.inu.model_id = ide_obj.model_id
            obj.inu.txd_name = ide_obj.txd_name
            obj.inu.draw_distance = ide_obj.draw_distance
            obj.inu.ide_flags = ide_obj.flags

        dd = ide_obj.draw_distance if ide_obj else 300.0
        txd = ide_obj.txd_name if ide_obj else ""

        # Check LOD
        from .core.ipl import is_lod_name
        if is_lod_name(model_name):
            target = col_lod
        elif _is_vegetation(model_name, txd):
            target = col_vegetation
        elif dd >= 300:
            target = col_buildings
        elif dd >= 100:
            target = col_props
        else:
            target = col_small

        # Move to target collection
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        target.objects.link(obj)

    # Move duplicates (.001, .002 etc) into _Instances sub-collections
    for obj in objects:
        if obj.type != 'MESH':
            continue
        name = obj.name
        # Check for Blender duplicate suffix (.001, .002, etc)
        if '.' not in name:
            continue
        base, suffix = name.rsplit('.', 1)
        if not suffix.isdigit():
            continue
        # This is a duplicate — move to parent_Instances
        parent = obj.users_collection[0] if obj.users_collection else None
        if parent and parent.name.startswith('Map_') and not parent.name.endswith('_Instances'):
            inst_name = parent.name + "_Instances"
            inst_col = bpy.data.collections.get(inst_name)
            if not inst_col:
                inst_col = bpy.data.collections.new(inst_name)
                parent.children.link(inst_col)
            parent.objects.unlink(obj)
            inst_col.objects.link(obj)



def _load_textures_from_cache(tex_dir: str, objects: list) -> bool:
    """Load PNG textures from cache dir and assign to materials of objects.
    Returns True if at least one texture was loaded."""
    loaded = False
    # Cache: already loaded images by name
    _img_cache = {}

    for obj in objects:
        if obj.type != 'MESH' or not obj.data.materials:
            continue
        for mat in obj.data.materials:
            if not mat or not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image is None:
                    tex_name = node.label or ''
                    if not tex_name:
                        # Fallback: material name without .001 suffix
                        tex_name = mat.name.rsplit('.', 1)[0] if '.' in mat.name and mat.name.rsplit('.', 1)[1].isdigit() else mat.name

                    # Check image cache first
                    if tex_name in _img_cache:
                        node.image = _img_cache[tex_name]
                        loaded = True
                        continue

                    png_path = os.path.join(tex_dir, tex_name + '.png')
                    if os.path.isfile(png_path):
                        img = bpy.data.images.get(tex_name)
                        if not img:
                            img = bpy.data.images.load(png_path)
                            img.name = tex_name
                        node.image = img
                        _img_cache[tex_name] = img
                        loaded = True
    return loaded


_map_region_cache = []
_map_region_cache_root = ""


def _get_map_region_items(self, context):
    """Dynamic enum items for map region selector, based on gta.dat paths."""
    global _map_region_cache, _map_region_cache_root

    items = [('ALL', T("Вся карта"), T("Импорт всей карты"))]

    game_root = bpy.path.abspath(getattr(context.scene, 'gtatools_game_root', ''))
    if not game_root or not os.path.isdir(game_root):
        return items

    # Cache: avoid re-parsing on every UI redraw
    if game_root == _map_region_cache_root and _map_region_cache:
        return _map_region_cache

    dat_path = os.path.join(game_root, 'data', 'gta.dat')
    if not os.path.isfile(dat_path):
        return items

    from .core.gta_dat import parse_gta_dat, extract_regions
    try:
        info = parse_gta_dat(dat_path)
        regions = extract_regions(info)
        for r in regions:
            items.append((r, r, f"Region: {r}"))
    except Exception:
        pass

    _map_region_cache = items
    _map_region_cache_root = game_root
    return items


# ID preset selector ─ dynamic EnumProperty
_id_preset_cache = []


def _get_id_preset_items(self, context):
    """Dynamic enum items for the Model ID preset selector."""
    global _id_preset_cache
    from .data.id_manager import list_presets
    names = list_presets()
    items = [(n, n, "") for n in names]
    if not items:
        items = [('default', 'default', '')]
    _id_preset_cache = items
    return _id_preset_cache


def _id_preset_update(self, context):
    """Sync id_manager's active preset whenever the selector changes."""
    from .data.id_manager import set_active_preset
    set_active_preset(self.gtatools_id_preset)


def _id_preset_sync(context):
    """Push the scene's current preset name into id_manager's module state."""
    try:
        from .data.id_manager import set_active_preset
        name = getattr(context.scene, 'gtatools_id_preset', 'default') or 'default'
        set_active_preset(name)
    except Exception:
        pass


def _get_cache_dir():
    """Get cache folder next to .blend file. Falls back to temp."""
    blend = bpy.data.filepath
    if blend:
        d = os.path.join(os.path.dirname(blend), '.inu_cache')
        os.makedirs(d, exist_ok=True)
        return d
    # Unsaved file — use temp
    import tempfile
    return tempfile.mkdtemp(prefix='inu_')


def _get_user_config_dir():
    """Get INU_Preset folder next to the addon folder (not inside it)."""
    addon_dir = os.path.dirname(os.path.abspath(__file__))  # .../addons/INU_tools
    addons_dir = os.path.dirname(addon_dir)                  # .../addons/
    d = os.path.join(addons_dir, 'INU_Preset')
    os.makedirs(d, exist_ok=True)
    return d


def _get_paths_file():
    global _PATHS_FILE
    if _PATHS_FILE is None:
        _PATHS_FILE = os.path.join(_get_user_config_dir(), 'paths.json')
    return _PATHS_FILE

_SAVED_PATH_KEYS = [
    'gtatools_ide_path', 'gtatools_ipl_path', 'gtatools_img_path', 'gtatools_game_root',
    'gtatools_texture_path1', 'gtatools_texture_path2',
    'gtatools_nvtt_path',
]

def _save_paths(self, context):
    """Save paths to config file when any path changes."""
    import json
    scene = context.scene
    data = {}
    for key in _SAVED_PATH_KEYS:
        val = getattr(scene, key, '')
        if val:
            data[key] = val
    try:
        with open(_get_paths_file(), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except:
        pass

def _load_paths(scene):
    """Load saved paths from config file into scene properties."""
    import json
    path = _get_paths_file()
    if not os.path.isfile(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for key, val in data.items():
            if key in _SAVED_PATH_KEYS and hasattr(scene, key):
                setattr(scene, key, val)
    except:
        pass


def _upd_suffix_dff(self, ctx):
    if self.gtatools_suffix_dff and self.gtatools_prefix_dff:
        self.gtatools_prefix_dff = ""

def _upd_suffix_lod(self, ctx):
    if self.gtatools_suffix_lod and self.gtatools_prefix_lod:
        self.gtatools_prefix_lod = ""

def _upd_suffix_col(self, ctx):
    if self.gtatools_suffix_col and self.gtatools_prefix_col:
        self.gtatools_prefix_col = ""

def _upd_prefix_dff(self, ctx):
    if self.gtatools_prefix_dff and self.gtatools_suffix_dff:
        self.gtatools_suffix_dff = ""

def _upd_prefix_lod(self, ctx):
    if self.gtatools_prefix_lod and self.gtatools_suffix_lod:
        self.gtatools_suffix_lod = ""

def _upd_prefix_col(self, ctx):
    if self.gtatools_prefix_col and self.gtatools_suffix_col:
        self.gtatools_suffix_col = ""


def register():
    # Custom Twemoji icons — load BEFORE panel classes draw
    _icons.register()

    # Inject Twemoji icon into each subpanel header (wraps any existing
    # draw_header so we don't clobber panels that already define one).
    for _pid, _ikey in _PANEL_ICON_KEYS.items():
        _cls = globals().get(_pid)
        if _cls is not None:
            _orig = _cls.__dict__.get('draw_header', None)
            _cls.draw_header = _make_twemoji_header(_orig, _ikey)

    # Auto-translate tooltips: docstrings are in Russian,
    # bl_description is set via T() so locale/eng.py handles English
    for cls in classes:
        doc = getattr(cls, '__doc__', None)
        if doc and doc.strip():
            cls.bl_description = T(doc.strip())
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            # Already registered (addon reload without restart)
            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)

    # INU property groups
    bpy.types.Object.inu = bpy.props.PointerProperty(type=INUObjectProps)
    bpy.types.Material.inu = bpy.props.PointerProperty(type=INUMaterialProps)

    # Sort materials button in material context menu (clean old entries on reload)
    if hasattr(bpy.types.MATERIAL_MT_context_menu.draw, '_draw_funcs'):
        draw_funcs = bpy.types.MATERIAL_MT_context_menu.draw._draw_funcs
        bpy.types.MATERIAL_MT_context_menu.draw._draw_funcs = [
            f for f in draw_funcs if getattr(f, '__name__', '') != '_draw_sort_materials_menu'
        ]
    bpy.types.MATERIAL_MT_context_menu.append(_draw_sort_materials_menu)

    bpy.types.Scene.gtatools_lightmap_result = StringProperty(name="Result", default="")
    bpy.types.Scene.gtatools_lightmap_path = StringProperty(name="Lightmap Path", default="lightmaps/lightmap.png")

    # Collapsible-section state for the PARTICLE 2DFX editor panel
    bpy.types.Scene.gtatools_pfx_exp_texture = BoolProperty(default=True)
    bpy.types.Scene.gtatools_pfx_exp_color = BoolProperty(default=True)
    bpy.types.Scene.gtatools_pfx_exp_size = BoolProperty(default=True)
    bpy.types.Scene.gtatools_pfx_exp_emission = BoolProperty(default=False)
    bpy.types.Scene.gtatools_pfx_exp_physics = BoolProperty(default=False)
    bpy.types.Scene.gtatools_pfx_exp_system = BoolProperty(default=False)
    bpy.types.Scene.gtatools_pfx_exp_curves = BoolProperty(default=False)

    def _update_particle_sim(self, context):
        from .ops import particle_sim
        if self.gtatools_particle_sim:
            particle_sim.start_simulation()
        else:
            particle_sim.stop_simulation()

    bpy.types.Scene.gtatools_particle_sim = BoolProperty(
        name="Particle Simulation",
        description=T("Анимировать 2DFX частицы в viewport"),
        default=False,
        update=_update_particle_sim,
    )
    bpy.types.Scene.gtatools_model_id = StringProperty(name="Model ID", default="0")
    bpy.types.Scene.gtatools_vc_analysis = StringProperty(name="VC Analysis", default="")

    # Fill colors history on Object
    bpy.types.Object.gtatools_fill_colors = CollectionProperty(type=GTATOOLS_FillColorItem)

    # UV Grid Randomizer settings
    def update_uv_grid(self, context):
        # Force redraw UV editor
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.tag_redraw()

    bpy.types.Scene.gtatools_uv_grid_cols = IntProperty(
        name="Columns",
        description=T("Количество колонок в сетке текстуры"),
        default=3,
        min=1,
        max=16,
        update=update_uv_grid
    )
    bpy.types.Scene.gtatools_uv_grid_rows = IntProperty(
        name="Rows",
        description=T("Количество рядов в сетке текстуры"),
        default=2,
        min=1,
        max=16,
        update=update_uv_grid
    )

    from bpy.props import EnumProperty
    bpy.types.Scene.gtatools_uv_grid_align = EnumProperty(
        name="Alignment",
        description=T("Позиция UV в ячейке"),
        items=[
            ('CENTER', "Center", "Center of cell"),
            ('TOP_LEFT', "Top Left", "Top left corner"),
            ('TOP_CENTER', "Top", "Top center"),
            ('TOP_RIGHT', "Top Right", "Top right corner"),
            ('LEFT_CENTER', "Left", "Left center"),
            ('RIGHT_CENTER', "Right", "Right center"),
            ('BOTTOM_LEFT', "Bottom Left", "Bottom left corner"),
            ('BOTTOM_CENTER', "Bottom", "Bottom center"),
            ('BOTTOM_RIGHT', "Bottom Right", "Bottom right corner"),
        ],
        default='CENTER'
    )

    bpy.types.Scene.gtatools_uv_link_islands = BoolProperty(
        name="Link Polygons",
        description=T("Полигоны с пересекающимися UV перемещаются вместе"),
        default=False
    )

    # COL Light settings
    bpy.types.Scene.gtatools_col_day_min = IntProperty(
        name="Day Min", description=T("Минимальное значение дневного света (тень)"), default=10, min=0, max=15)
    bpy.types.Scene.gtatools_col_day_max = IntProperty(
        name="Day Max", description=T("Максимальное значение дневного света (свет)"), default=15, min=0, max=15)
    bpy.types.Scene.gtatools_col_night_min = IntProperty(
        name="Night Min", description=T("Минимальное значение ночного света (тень)"), default=0, min=0, max=15,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_night_max = IntProperty(
        name="Night Max", description=T("Максимальное значение ночного света (свет)"), default=5, min=0, max=15,
        update=_col_light_invalidate_preview)

    bpy.types.Scene.gtatools_col_light_edge = FloatProperty(
        name="Edge",
        description=T("Сдвиг границы COL освещения: + расширяет зелёную зону, — сужает"),
        default=0.0, min=-5.0, max=5.0, soft_min=-1.0, soft_max=1.0, step=1,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_light_threshold = IntProperty(
        name="Threshold",
        description=T("Порог яркости: 0 = без порога, 100 = максимальная отсечка"),
        default=0, min=0, max=100,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_light_contrast = FloatProperty(
        name="Contrast",
        description=T("Контраст: резкость перехода между тёмными и светлыми зонами"),
        default=0.0, min=0.0, max=5.0, soft_min=0.0, soft_max=1.0, step=1,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_light_font_size = IntProperty(
        name="Font Size",
        description=T("Размер цифр на полигонах"),
        default=13, min=6, max=36,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_light_show_numbers = BoolProperty(
        name="Show Numbers",
        description=T("Показать цифры на полигонах"),
        default=True)

    # IMG archive path
    bpy.types.Scene.gtatools_img_path = StringProperty(
        name="IMG Archive",
        description=T("Путь к .img архиву GTA SA для экспорта моделей"),
        default="",
        subtype='FILE_PATH',
        update=_save_paths,
    )
    bpy.types.Scene.gtatools_img_export_dff = BoolProperty(
        name="DFF", default=True,
        description=T("Экспорт DFF в IMG"),
    )
    bpy.types.Scene.gtatools_img_export_col = BoolProperty(
        name="COL", default=True,
        description=T("Экспорт COL в IMG"),
    )
    bpy.types.Scene.gtatools_img_export_txd = BoolProperty(
        name="TXD", default=True,
        description=T("Экспорт TXD в IMG"),
    )

    bpy.types.Scene.gtatools_map_fake_mode = BoolProperty(
        name="Fake Mode",
        description=T("Импорт плоскостей вместо моделей (быстрый превью карты)"),
        default=True,
    )
    bpy.types.Scene.gtatools_map_region = EnumProperty(
        name="Region",
        description=T("Район карты для импорта"),
        items=_get_map_region_items,
    )
    bpy.types.Scene.gtatools_binary_ipls = CollectionProperty(
        type=GTATOOLS_BinaryIplEntry,
    )
    bpy.types.Scene.gtatools_show_binary_ipls = BoolProperty(
        name="Show binary IPLs",
        description=T("Развернуть список бинарных IPL для галочек"),
        default=False,
    )
    bpy.types.Scene.gtatools_map_skip_2dfx = BoolProperty(
        name="Skip 2DFX",
        description=T("Не импортировать 2DFX-эффекты (лампы, частицы, ped attractors, sun glare) при импорте карты и DFF"),
        default=False,
    )
    bpy.types.Scene.gtatools_img_use_gta_dat = BoolProperty(
        name="Use gta.dat",
        description=T("Искать все IDE/IPL через gta.dat (нужна корневая папка игры)"),
        default=False,
    )
    bpy.types.Scene.gtatools_img_skip_lod = BoolProperty(
        name="Skip LOD",
        description=T("Пропустить LOD модели при импорте"),
        default=False,
    )
    bpy.types.Scene.gtatools_img_load_txd = BoolProperty(
        name="Load TXD",
        description=T("Загружать TXD текстуры вместе с DFF"),
        default=True,
    )

    # Game root path (for gta.dat auto-discovery)
    bpy.types.Scene.gtatools_game_root = StringProperty(
        name="Game Root",
        description=T("Корневая папка GTA SA для автопоиска IDE/IPL/IMG"),
        default="",
        subtype='DIR_PATH',
        update=_save_paths,
    )

    # IDE / IPL paths
    bpy.types.Scene.gtatools_ide_path = StringProperty(
        name="IDE File",
        description=T("Путь к IDE файлу GTA SA для добавления/обновления записей"),
        default="",
        subtype='FILE_PATH',
        update=_save_paths,
    )
    bpy.types.Scene.gtatools_ipl_path = StringProperty(
        name="IPL File",
        description=T("Путь к IPL файлу GTA SA для добавления/обновления записей"),
        default="",
        subtype='FILE_PATH',
        update=_save_paths,
    )

    # NVIDIA Texture Tools settings
    bpy.types.Scene.gtatools_txd_auto_import = BoolProperty(
        name="Import TXD",
        description=T("Автоимпорт TXD текстур при импорте DFF"),
        default=True,
    )

    # Shared TXD — single TXD for multiple DFF models
    bpy.types.Scene.gtatools_shared_txd_name = StringProperty(
        name="Shared TXD Name",
        description=T("Имя общего TXD файла для нескольких DFF моделей"),
        default="",
    )

    bpy.types.Scene.gtatools_txd_import_path = StringProperty(
        name="TXD Import Folder",
        description=T("Папка для поиска TXD при импорте DFF (пусто = автопоиск в папке DFF)"),
        default="",
        subtype='DIR_PATH'
    )

    bpy.types.Scene.gtatools_nvtt_path = StringProperty(
        name="NVTT Path",
        description=T("Путь к папке NVIDIA Texture Tools (для GPU сжатия)"),
        default="",
        subtype='DIR_PATH',
        update=_save_paths,
    )

    bpy.types.Scene.gtatools_txd_use_gpu = BoolProperty(
        name="Use GPU",
        description=T("Использовать GPU (NVTT) для сжатия текстур"),
        default=False
    )

    bpy.types.Scene.gtatools_show_nvtt_settings = BoolProperty(
        name="Show NVTT Settings",
        description=T("Показать настройки NVTT"),
        default=False
    )

    bpy.types.Scene.gtatools_show_texture_settings = BoolProperty(
        name="Show Texture Settings",
        description=T("Показать настройки текстур"),
        default=False
    )

    bpy.types.Scene.gtatools_show_paths_settings = BoolProperty(
        name="Show Paths Settings",
        description=T("Показать пути IDE/IPL/IMG"),
        default=False
    )

    # Suffix settings
    bpy.types.Scene.gtatools_show_suffix_settings = BoolProperty(
        name="Show Suffix Settings",
        description=T("Показать настройки суффиксов"),
        default=False
    )

    bpy.types.Scene.gtatools_show_dff_flags = BoolProperty(
        name="Show DFF Flags",
        default=False
    )
    bpy.types.Scene.gtatools_show_ide_flags = BoolProperty(
        name="Show IDE Flags",
        description=T("Показать флаги IDE"),
        default=False
    )
    bpy.types.Scene.gtatools_suffix_dff = StringProperty(
        name="DFF Suffix", default="_DFF", update=_upd_suffix_dff,
        description=T("Суффикс для DFF моделей"),
    )
    bpy.types.Scene.gtatools_suffix_lod = StringProperty(
        name="LOD Suffix", default="_LOD", update=_upd_suffix_lod,
        description=T("Суффикс для LOD моделей"),
    )
    bpy.types.Scene.gtatools_suffix_col = StringProperty(
        name="COL Suffix", default="_COL", update=_upd_suffix_col,
        description=T("Суффикс для COL моделей"),
    )
    bpy.types.Scene.gtatools_prefix_dff = StringProperty(
        name="DFF Prefix", default="", update=_upd_prefix_dff,
        description=T("Префикс для DFF моделей"),
    )
    bpy.types.Scene.gtatools_prefix_lod = StringProperty(
        name="LOD Prefix", default="", update=_upd_prefix_lod,
        description=T("Префикс для LOD моделей"),
    )
    bpy.types.Scene.gtatools_prefix_col = StringProperty(
        name="COL Prefix", default="", update=_upd_prefix_col,
        description=T("Префикс для COL моделей"),
    )

    # ID Manager
    # X Radar Maker
    bpy.types.Scene.gtatools_radar_output = StringProperty(
        name="Radar Output",
        subtype='DIR_PATH',
        default="",
        description=T("Папка для сохранения тайлов радара"),
    )
    bpy.types.Scene.gtatools_radar_grid = IntProperty(
        name="Radar Grid",
        default=8,
        min=1, max=16,
        description=T("Размер сетки (8 = 64 тайла)"),
    )
    bpy.types.Scene.gtatools_radar_size = IntProperty(
        name="Radar Tile Size",
        default=256,
        min=64, max=4096,
        description=T("Размер тайла в пикселях"),
    )
    bpy.types.Scene.gtatools_radar_height = FloatProperty(
        name="Radar Height",
        default=3000.0,
        min=100.0,
        description=T("Высота камеры"),
    )
    bpy.types.Scene.gtatools_radar_gamma = FloatProperty(
        name="Radar Gamma",
        default=1.0,
        min=0.1, max=5.0,
    )
    bpy.types.Scene.gtatools_radar_specific = StringProperty(
        name="Radar Specific",
        default="",
        description=T("Индексы тайлов через запятую (0,1,5,63)"),
    )

    bpy.types.Scene.gtatools_show_img_list = BoolProperty(
        name="Show IMG List",
        default=False
    )
    bpy.types.Scene.gtatools_img_entries = CollectionProperty(type=GTATOOLS_ImgFileEntry)
    bpy.types.Scene.gtatools_img_entries_index = IntProperty(default=0)
    bpy.types.Scene.gtatools_show_id_manager = BoolProperty(
        name="Show ID Manager",
        description=T("Показать менеджер ID"),
        default=False
    )
    bpy.types.Scene.gtatools_id_search = StringProperty(
        name="ID Search",
        description=T("Поиск по ID или имени модели"),
        default=""
    )
    bpy.types.Scene.gtatools_id_page = IntProperty(
        name="ID Page",
        default=0,
        min=0,
        soft_max=1000,
    )
    bpy.types.Scene.gtatools_id_preset = EnumProperty(
        name=T("Пресет ID"),
        description=T("Активный файл со списком ID. Каждый пресет — отдельный .txt в папке data/id_presets/"),
        items=_get_id_preset_items,
        update=_id_preset_update,
    )
    # Texture loader paths
    bpy.types.Scene.gtatools_texture_path1 = StringProperty(
        name="System Textures Path",
        description=T("Путь к папке с системными текстурами GTA"),
        default="",
        subtype='DIR_PATH',
        update=_save_paths,
    )
    bpy.types.Scene.gtatools_texture_path2 = StringProperty(
        name="Blend Folder Path",
        description=T("Путь к папке где находится .blend файл"),
        default="",
        subtype='DIR_PATH',
        update=_save_paths,
    )

    # IFP action selector
    bpy.types.Scene.gtatools_ifp_action = StringProperty(
        name="IFP Action",
        description="Select IFP animation to apply",
    )

    # Water settings
    bpy.types.Scene.gtatools_water_flag = EnumProperty(
        name="Water Type",
        description="Water polygon visibility and depth type",
        items=[
            ('0', T("Обычная / Невидимая"), T("Глубокая вода, не отображается (подводные зоны)")),
            ('1', T("Обычная / Видимая"), T("Глубокая вода с волнами (океан, реки)")),
            ('2', T("Мелкая / Невидимая"), T("Мелкая вода, не отображается (анимация хождения по воде)")),
            ('3', T("Мелкая / Видимая"), T("Мелкая вода, отображается (лужи, пруды)")),
        ],
        default='1',
    )
    bpy.types.Scene.gtatools_water_speed_x = FloatProperty(
        name="Speed X", default=0.0, min=-5.0, max=5.0
    )
    bpy.types.Scene.gtatools_water_speed_y = FloatProperty(
        name="Speed Y", default=0.0, min=-5.0, max=5.0
    )
    bpy.types.Scene.gtatools_water_speed_z = FloatProperty(
        name="Speed Z", default=0.05, min=-5.0, max=5.0
    )
    bpy.types.Scene.gtatools_water_wave_height = FloatProperty(
        name="Wave Height", default=0.1, min=0.0, max=10.0
    )

    # Bake settings (calibrated for 3Ds Max-like output)
    bpy.types.Scene.gtatools_bake_ambient = FloatProperty(
        name="Ambient",
        description=T("Базовый рассеянный свет (ниже = темнее тени)"),
        default=0.10,
        min=0.0,
        max=0.5
    )
    bpy.types.Scene.gtatools_bake_intensity = FloatProperty(
        name="Intensity",
        description=T("Множитель интенсивности света (ниже = темнее)"),
        default=0.05,
        min=0.0001,
        max=0.5
    )
    bpy.types.Scene.gtatools_bake_gamma = FloatProperty(
        name="Gamma",
        description=T("Гамма-коррекция (ниже = темнее)"),
        default=0.50,
        min=0.1,
        max=3.0
    )

    bpy.types.Scene.gtatools_bake_shadows = BoolProperty(
        name="Shadows",
        description=T("Включить тени при запекании (raycast проверка перекрытий)"),
        default=True
    )

    bpy.types.Scene.gtatools_prelight_preset = EnumProperty(
        name="Prelight Preset",
        items=_get_preset_items,
        description=T("Выбрать пресет настроек прелайта"),
    )

    # V offset for night prelight
    bpy.types.Scene.gtatools_v_offset = FloatProperty(
        name="V Offset",
        description=T("Смещение яркости как в 3Ds Max Adjust Color V (-80 для ночи)"),
        default=0.0,
        min=-100.0,
        max=100.0
    )

    # Post-processing vertex colors
    bpy.types.Scene.gtatools_vc_smooth_iterations = IntProperty(
        name="Iterations",
        description=T("Количество итераций сглаживания"),
        default=1,
        min=1,
        max=50
    )
    bpy.types.Scene.gtatools_vc_smooth_factor = FloatProperty(
        name="Factor",
        description=T("Сила сглаживания (0 = без изменений, 1 = полное усреднение)"),
        default=0.5,
        min=0.0,
        max=1.0
    )
    bpy.types.Scene.gtatools_vc_contrast = FloatProperty(
        name="Contrast",
        description=T("Контраст (1 = без изменений, <1 = меньше, >1 = больше)"),
        default=1.0,
        min=0.0,
        max=3.0
    )
    bpy.types.Scene.gtatools_vc_brightness = FloatProperty(
        name="Brightness",
        description=T("Яркость смещение (-1..+1)"),
        default=0.0,
        min=-1.0,
        max=1.0
    )
    bpy.types.Scene.gtatools_vc_gamma = FloatProperty(
        name="Gamma",
        description=T("Гамма-коррекция (1 = без изменений, <1 = светлее, >1 = темнее)"),
        default=1.0,
        min=0.1,
        max=3.0
    )

    # Vertex paint - fill color
    bpy.types.Scene.gtatools_fill_color = FloatVectorProperty(
        name="Fill Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0
    )

    # Vertex paint - scatter light settings
    bpy.types.Scene.gtatools_scatter_intensity = FloatProperty(
        name="Intensity",
        description=T("Интенсивность рассеивания света"),
        default=1.0,
        min=0.1,
        max=5.0
    )
    bpy.types.Scene.gtatools_scatter_falloff = FloatProperty(
        name="Falloff",
        description=T("Скорость затухания света (выше = быстрее)"),
        default=1.5,
        min=0.5,
        max=5.0
    )
    bpy.types.Scene.gtatools_scatter_iterations = IntProperty(
        name="Iterations",
        description=T("Количество слоёв соседних граней"),
        default=3,
        min=1,
        max=10
    )
    bpy.types.Scene.gtatools_scatter_radius = FloatProperty(
        name="Radius",
        description=T("Радиус поиска соседних граней (0 = авто по размеру грани)"),
        default=0.0,
    )

    # Pipeline selector for export
    bpy.types.Scene.gtatools_export_pipeline = EnumProperty(
        items=[
            ('NONE', 'None',
             T("Без указания pipeline — использовать стандартный рендер RenderWare. Подходит для простых объектов, которым не нужны специальные эффекты движка")),
            ('0x53F2009A', 'Vehicle',
             T("Pipeline кузова машины (RSPIPE_PC_CustomCarEnvMap). Добавляет env-map отражения неба/облаков/улицы. Используется совместно с текстурами vehicleenv128 + vehiclespecdot64 на материале")),
            ('0x53F20098', 'Day/Night',
             T("Pipeline здания с day/night vertex colors (RSPIPE_PC_CustomBuildingDN). Движок плавно смешивает дневной и ночной слои vertex colors по игровому времени. Требует ДВА Color Attribute слоя (Day + Night) на меше")),
            ('0x53F2009C', 'Building',
             T("Простой pipeline здания (RSPIPE_PC_CustomBuilding). Статическое освещение через один слой vertex colors. Работает быстрее чем Day/Night, но нет смены по времени суток")),
        ],
        name="Pipeline",
        description=T("Рендер-пайплайн для экспорта DFF"),
        default='NONE',
    )

    from .tools.gta_material_panel import PRESETS as _MAT_PRESETS
    bpy.types.Scene.gtatools_material_preset = EnumProperty(
        items=_MAT_PRESETS,
        name="GTA Material Preset",
        default='VEHICLE',
    )

    # Export settings
    bpy.types.Scene.gtatools_export_all_dff = BoolProperty(
        name="Export DFF",
        description=T("Экспортировать DFF при Export All"),
        default=True
    )
    bpy.types.Scene.gtatools_export_all_col = BoolProperty(
        name="Export COL",
        description=T("Экспортировать COL при Export All"),
        default=True
    )
    bpy.types.Scene.gtatools_export_all_lod = BoolProperty(
        name="Export LOD",
        description=T("Экспортировать LOD при Export All"),
        default=True
    )
    bpy.types.Scene.gtatools_export_all_txd = BoolProperty(
        name="Export TXD",
        description=T("Экспортировать TXD при Export All"),
        default=True
    )

    # Keymap: Shift+T — toggle UV Editor
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('gtatools.toggle_uv_editor', 'T', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

    # File > Export / Import menus
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    # Add > GTA SA submenu
    bpy.types.VIEW3D_MT_add.append(_gtasa_add_menu_draw)

    # 2DFX real-time preview handler
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update_2dfx)

    # 2DFX billboard rotation timer — start now and restart on file load
    from .ops.fx_preview import start_billboard_timer
    start_billboard_timer()
    bpy.app.handlers.load_post.append(_on_file_load_restart_timer)
    bpy.app.handlers.load_post.append(_on_file_load_restore_paths)

    # Deferred load paths (context.scene not available during register)
    def _deferred_load_paths():
        try:
            _load_paths(bpy.context.scene)
        except:
            pass
        return None
    bpy.app.timers.register(_deferred_load_paths, first_interval=0.5)

    print("[GTA Tools Panel] Addon registered!")


@persistent
def _on_file_load_restore_paths(dummy):
    """Restore saved paths after loading a .blend file."""
    _load_paths(bpy.context.scene)


@persistent
def _on_file_load_restart_timer(dummy):
    """Restart billboard timer after loading a new .blend file."""
    print("[2DFX] load_post handler fired — scheduling timer restart in 1s...")
    def _delayed_start():
        print("[2DFX] Delayed start — restarting billboard timer now")
        from .ops.fx_preview import start_billboard_timer
        start_billboard_timer()
        return None
    bpy.app.timers.register(_delayed_start, first_interval=1.0)


_2dfx_sync_busy = False

def _on_depsgraph_update_2dfx(scene, depsgraph):
    """Auto-sync 2DFX preview when properties change in UI."""
    global _2dfx_sync_busy

    # Ensure billboard timer is alive (restart after scene switch etc.)
    try:
        from .ops.fx_preview import _update_billboard_rotations, start_billboard_timer
        import bpy as _bpy
        if not _bpy.app.timers.is_registered(_update_billboard_rotations):
            start_billboard_timer()
    except Exception:
        pass

    if _2dfx_sync_busy:
        return
    try:
        obj = bpy.context.active_object
    except Exception:
        return
    if not obj or obj.type != 'EMPTY':
        return
    inu = getattr(obj, 'inu', None)
    if not inu or inu.type != '2DFX' or inu.effect_2dfx != 'LIGHT':
        return
    # Only run if this object has preview children
    has_children = any(
        getattr(c, 'inu', None) and c.inu.type == 'NON'
        for c in obj.children
    )
    if not has_children:
        return
    _2dfx_sync_busy = True
    try:
        from .ops.fx_preview import sync_preview_from_props
        sync_preview_from_props(obj)
    except Exception:
        pass
    finally:
        _2dfx_sync_busy = False


def unregister():
    # 2DFX billboard timer
    from .ops.fx_preview import stop_billboard_timer
    stop_billboard_timer()

    # 2DFX handlers
    if _on_depsgraph_update_2dfx in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update_2dfx)
    if _on_file_load_restart_timer in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_file_load_restart_timer)
    if _on_file_load_restore_paths in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_file_load_restore_paths)

    # File > Export / Import menus
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    # Add > GTA SA submenu
    bpy.types.VIEW3D_MT_add.remove(_gtasa_add_menu_draw)

    del bpy.types.Object.inu
    del bpy.types.Material.inu

    bpy.types.MATERIAL_MT_context_menu.remove(_draw_sort_materials_menu)

    # Remove keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Remove COL Light preview handlers
    for h in _col_light_mod._col_light_preview_handlers:
        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
    _col_light_mod._col_light_preview_handlers.clear()
    _col_light_mod._col_light_preview_active = False

    # Remove model links draw handler
    global _links_draw_handler, _links_active
    if _links_draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_links_draw_handler, 'WINDOW')
        _links_draw_handler = None
    _links_active = False

    # Remove UV grid draw handler
    if _uv._uv_grid_draw_handler is not None:
        bpy.types.SpaceImageEditor.draw_handler_remove(_uv._uv_grid_draw_handler, 'WINDOW')
        _uv._uv_grid_draw_handler = None
    _uv._uv_grid_visible = False

    del bpy.types.Scene.gtatools_uv_grid_cols
    del bpy.types.Scene.gtatools_uv_grid_rows
    del bpy.types.Scene.gtatools_uv_grid_align
    del bpy.types.Scene.gtatools_uv_link_islands
    del bpy.types.Scene.gtatools_col_day_min
    del bpy.types.Scene.gtatools_col_day_max
    del bpy.types.Scene.gtatools_col_night_min
    del bpy.types.Scene.gtatools_col_night_max
    del bpy.types.Scene.gtatools_col_light_edge
    del bpy.types.Scene.gtatools_col_light_threshold
    del bpy.types.Scene.gtatools_col_light_contrast
    del bpy.types.Scene.gtatools_col_light_font_size
    del bpy.types.Scene.gtatools_col_light_show_numbers
    del bpy.types.Scene.gtatools_img_path
    del bpy.types.Scene.gtatools_game_root
    del bpy.types.Scene.gtatools_map_fake_mode
    del bpy.types.Scene.gtatools_map_region
    del bpy.types.Scene.gtatools_binary_ipls
    del bpy.types.Scene.gtatools_show_binary_ipls
    del bpy.types.Scene.gtatools_map_skip_2dfx
    del bpy.types.Scene.gtatools_img_use_gta_dat
    del bpy.types.Scene.gtatools_img_skip_lod
    del bpy.types.Scene.gtatools_img_load_txd
    del bpy.types.Scene.gtatools_img_export_dff
    del bpy.types.Scene.gtatools_img_export_col
    del bpy.types.Scene.gtatools_img_export_txd
    del bpy.types.Scene.gtatools_ide_path
    del bpy.types.Scene.gtatools_ipl_path
    del bpy.types.Scene.gtatools_txd_auto_import
    del bpy.types.Scene.gtatools_shared_txd_name
    del bpy.types.Scene.gtatools_txd_import_path
    del bpy.types.Scene.gtatools_nvtt_path
    del bpy.types.Scene.gtatools_txd_use_gpu
    del bpy.types.Scene.gtatools_show_nvtt_settings
    del bpy.types.Scene.gtatools_show_texture_settings
    del bpy.types.Scene.gtatools_show_paths_settings
    del bpy.types.Scene.gtatools_show_suffix_settings
    del bpy.types.Scene.gtatools_show_dff_flags
    del bpy.types.Scene.gtatools_show_ide_flags
    del bpy.types.Scene.gtatools_suffix_dff
    del bpy.types.Scene.gtatools_suffix_lod
    del bpy.types.Scene.gtatools_suffix_col
    del bpy.types.Scene.gtatools_prefix_dff
    del bpy.types.Scene.gtatools_prefix_lod
    del bpy.types.Scene.gtatools_prefix_col
    del bpy.types.Scene.gtatools_radar_output
    del bpy.types.Scene.gtatools_radar_grid
    del bpy.types.Scene.gtatools_radar_size
    del bpy.types.Scene.gtatools_radar_height
    del bpy.types.Scene.gtatools_radar_gamma
    del bpy.types.Scene.gtatools_radar_specific
    del bpy.types.Scene.gtatools_show_img_list
    del bpy.types.Scene.gtatools_img_entries
    del bpy.types.Scene.gtatools_img_entries_index
    del bpy.types.Scene.gtatools_show_id_manager
    del bpy.types.Scene.gtatools_id_search
    del bpy.types.Scene.gtatools_id_page
    del bpy.types.Scene.gtatools_id_preset
    del bpy.types.Scene.gtatools_texture_path2
    del bpy.types.Scene.gtatools_texture_path1
    del bpy.types.Scene.gtatools_export_pipeline
    del bpy.types.Scene.gtatools_material_preset
    del bpy.types.Scene.gtatools_export_all_dff
    del bpy.types.Scene.gtatools_export_all_col
    del bpy.types.Scene.gtatools_export_all_lod
    del bpy.types.Scene.gtatools_export_all_txd
    del bpy.types.Scene.gtatools_scatter_radius
    del bpy.types.Scene.gtatools_scatter_iterations
    del bpy.types.Scene.gtatools_scatter_falloff
    del bpy.types.Scene.gtatools_scatter_intensity
    del bpy.types.Scene.gtatools_fill_color
    del bpy.types.Object.gtatools_fill_colors
    del bpy.types.Scene.gtatools_v_offset
    del bpy.types.Scene.gtatools_vc_smooth_iterations
    del bpy.types.Scene.gtatools_vc_smooth_factor
    del bpy.types.Scene.gtatools_vc_contrast
    del bpy.types.Scene.gtatools_vc_brightness
    del bpy.types.Scene.gtatools_vc_gamma
    del bpy.types.Scene.gtatools_bake_shadows
    del bpy.types.Scene.gtatools_prelight_preset
    del bpy.types.Scene.gtatools_bake_gamma
    del bpy.types.Scene.gtatools_bake_intensity
    del bpy.types.Scene.gtatools_ifp_action
    del bpy.types.Scene.gtatools_water_flag
    del bpy.types.Scene.gtatools_water_speed_x
    del bpy.types.Scene.gtatools_water_speed_y
    del bpy.types.Scene.gtatools_water_speed_z
    del bpy.types.Scene.gtatools_water_wave_height
    del bpy.types.Scene.gtatools_bake_ambient
    del bpy.types.Scene.gtatools_vc_analysis
    del bpy.types.Scene.gtatools_lightmap_result
    del bpy.types.Scene.gtatools_lightmap_path
    del bpy.types.Scene.gtatools_model_id

    # Stop particle sim timer and drop meshes
    try:
        from .ops import particle_sim
        particle_sim.stop_simulation()
    except Exception:
        pass
    try:
        del bpy.types.Scene.gtatools_particle_sim
    except Exception:
        pass
    for k in ('gtatools_pfx_exp_texture', 'gtatools_pfx_exp_color',
              'gtatools_pfx_exp_size', 'gtatools_pfx_exp_emission',
              'gtatools_pfx_exp_physics', 'gtatools_pfx_exp_system',
              'gtatools_pfx_exp_curves'):
        try:
            delattr(bpy.types.Scene, k)
        except Exception:
            pass

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    _icons.unregister()

    print("[GTA Tools Panel] Addon unregistered!")


if __name__ == "__main__":
    register()
