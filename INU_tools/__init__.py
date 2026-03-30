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
    "version": (1, 5, 2),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar (N) > GTA Tools",
    "description": "Toolset for GTA SA models",
    "warning": "",
    "category": "3D View",
}

# Changelog:
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

addon_keymaps = []

# =============================================================================
# PROPERTY GROUPS
# =============================================================================

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
            ('NONE', 'None', 'Export without setting a pipeline'),
            ('0x53F2009A', 'Building', 'Day/Night vertex colors for buildings'),
            ('0x53F20098', 'Reflections', 'Window reflections on buildings'),
            ('CUSTOM', 'Custom Pipeline', 'Set a custom pipeline value'),
        ],
        name="Pipeline",
        description=T("Рендер-пайплайн движка"),
    )
    custom_pipeline : StringProperty(name="Custom Pipeline")

    export_normals : BoolProperty(
        default=True,
        description=T("Экспорт нормалей вершин (отключить для map объектов)"),
    )
    export_binsplit : BoolProperty(
        default=True,
        description=T("Экспорт Bin Mesh PLG (совместимость с просмотрщиками DFF)"),
    )

    uv_map1 : BoolProperty(default=True, description=T("Экспорт первой UV карты"))
    uv_map2 : BoolProperty(default=True, description=T("Экспорт второй UV карты"))
    day_cols : BoolProperty(default=True, description=T("Экспорт дневных vertex colors"))
    night_cols : BoolProperty(default=True, description=T("Экспорт ночных vertex colors"))

    light : BoolProperty(default=True, description=T("Флаг rpGEOMETRYLIGHT — динамическое освещение"))
    modulate_color : BoolProperty(default=True, description=T("Флаг rpGEOMETRYMODULATEMATERIALCOLOR — цвет материала влияет на модель"))

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
        default=300.0,
        min=0.0,
        description=T("Дальность прорисовки объекта (IDE)"),
    )
    ide_flags : IntProperty(
        name="IDE Flags",
        default=0,
        min=0,
        description=T("Флаги объекта в IDE"),
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

    flag_is_road : BoolProperty(name="IS_ROAD", description="Дорога (1)", default=False, update=_update_ide_flag)
    flag_draw_last : BoolProperty(name="DRAW_LAST", description="Прозрачный, рисовать последним (4)", default=False, update=_update_ide_flag)
    flag_additive : BoolProperty(name="ADDITIVE", description="Аддитивный блендинг (8)", default=False, update=_update_ide_flag)
    flag_no_zbuffer : BoolProperty(name="NO_ZBUFFER_WRITE", description="Не писать в Z-буфер (64)", default=False, update=_update_ide_flag)
    flag_no_shadows : BoolProperty(name="NO_SHADOWS", description="Не получать тени (128)", default=False, update=_update_ide_flag)
    flag_glass_1 : BoolProperty(name="GLASS_TYPE_1", description="Стекло разбиваемое (512)", default=False, update=_update_ide_flag)
    flag_glass_2 : BoolProperty(name="GLASS_TYPE_2", description="Стекло с трещинами (1024)", default=False, update=_update_ide_flag)
    flag_garage_door : BoolProperty(name="GARAGE_DOOR", description="Дверь гаража (2048)", default=False, update=_update_ide_flag)
    flag_damagable : BoolProperty(name="DAMAGABLE", description="Разрушаемый (4096)", default=False, update=_update_ide_flag)
    flag_is_tree : BoolProperty(name="IS_TREE", description="Дерево, качается на ветру (8192)", default=False, update=_update_ide_flag)
    flag_is_palm : BoolProperty(name="IS_PALM", description="Пальма, качается на ветру (16384)", default=False, update=_update_ide_flag)
    flag_no_flyer_col : BoolProperty(name="NO_FLYER_COL", description="Нет коллизии с летающим (32768)", default=False, update=_update_ide_flag)
    flag_is_tag : BoolProperty(name="IS_TAG", description="Граффити тег (1048576)", default=False, update=_update_ide_flag)
    flag_no_backface : BoolProperty(name="NO_BACKFACE_CULL", description="Рисовать обе стороны (2097152)", default=False, update=_update_ide_flag)
    flag_breakable : BoolProperty(name="BREAKABLE_STATUE", description="Разрушаемая статуя (4194304)", default=False, update=_update_ide_flag)
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


class INUMaterialProps(bpy.types.PropertyGroup):
    """INU_tools material properties (replaces DragonFF mat.dff)."""

    ambient : FloatProperty(name="Ambient Shading", default=1.0)

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
        use_gpu = context.scene.gtatools_txd_use_gpu
        result, message, transparent_list = export_txd(self.filepath, context, self.selected_only, use_gpu)
        self.report({'INFO'} if result == {'FINISHED'} else {'ERROR'}, message)
        return result

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "selected_only")


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

            # Собираем меши и 2DFX для экспорта
            from .ops.dff_export import export_dff as inu_export_dff
            dff_objects = [o for o in context.selected_objects
                           if o.type == 'MESH'
                           or (o.type == 'EMPTY' and getattr(o, 'inu', None) and o.inu.type == '2DFX')]
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


# ── File > Export / Import operators (with ExportHelper/ImportHelper) ──

class GTATOOLS_OT_file_export_dff(bpy.types.Operator, ExportHelper):
    """Экспорт DFF модели GTA SA"""
    bl_idname = "gtatools.file_export_dff"
    bl_label = "GTA SA DFF (.dff)"
    bl_options = {'PRESET'}
    filename_ext = ".dff"
    filter_glob: StringProperty(default="*.dff", options={'HIDDEN'})

    def execute(self, context):
        from .ops.dff_export import export_dff as inu_export_dff
        try:
            dff_objects = [o for o in context.selected_objects
                           if o.type == 'MESH'
                           or (o.type == 'EMPTY' and getattr(o, 'inu', None) and o.inu.type == '2DFX')]
            inu_export_dff(filepath=self.filepath, objects=dff_objects)
            self.report({'INFO'}, f"Exported DFF: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"DFF export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_file_export_col(bpy.types.Operator, ExportHelper):
    """Экспорт COL коллизии GTA SA"""
    bl_idname = "gtatools.file_export_col"
    bl_label = "GTA SA COL (.col)"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    def execute(self, context):
        from .ops.col_export import export_col as inu_export_col
        try:
            col_objects = [o for o in context.selected_objects if o.type in ('MESH', 'EMPTY')]
            inu_export_col(filepath=self.filepath, objects=col_objects, version=3)
            self.report({'INFO'}, f"Exported COL: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"COL export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_file_export_txd(bpy.types.Operator, ExportHelper):
    """Экспорт TXD текстур GTA SA"""
    bl_idname = "gtatools.file_export_txd"
    bl_label = "GTA SA TXD (.txd)"
    bl_options = {'PRESET'}
    filename_ext = ".txd"
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    def execute(self, context):
        use_gpu = getattr(context.scene, 'gtatools_txd_use_gpu', False)
        result, message, transparent_list = export_txd(self.filepath, context, False, use_gpu)
        self.report({'INFO'} if result == {'FINISHED'} else {'ERROR'}, message)
        return result


class GTATOOLS_OT_file_import_dff(bpy.types.Operator, ImportHelper):
    """Импорт DFF модели GTA SA"""
    bl_idname = "gtatools.file_import_dff"
    bl_label = "GTA SA DFF (.dff)"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".dff"
    filter_glob: StringProperty(default="*.dff", options={'HIDDEN'})

    def execute(self, context):
        from .ops.dff_import import import_dff as inu_import_dff
        from .ops.txd_import import import_txd as inu_import_txd
        try:
            inu_import_dff(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"Imported DFF: {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"DFF import error: {str(e)}")
            return {'CANCELLED'}

        # Auto-import TXD: search in custom folder or DFF folder
        txd_file = None
        dff_name = os.path.splitext(os.path.basename(self.filepath))[0]
        custom_dir = getattr(context.scene, 'gtatools_txd_import_path', '')
        if custom_dir:
            custom_dir = bpy.path.abspath(custom_dir)

        # Search directories: custom folder first, then DFF folder
        search_dirs = []
        if custom_dir and os.path.isdir(custom_dir):
            search_dirs.append(custom_dir)
        search_dirs.append(os.path.dirname(self.filepath))

        for search_dir in search_dirs:
            if txd_file:
                break
            # First try same name as DFF
            same_name = os.path.join(search_dir, dff_name + ".txd")
            if os.path.isfile(same_name):
                txd_file = same_name
                break
            # Then any .txd in folder
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
        else:
            self.report({'WARNING'}, "TXD not found in DFF folder")

        return {'FINISHED'}


class GTATOOLS_OT_file_import_col(bpy.types.Operator, ImportHelper):
    """Импорт COL коллизии GTA SA"""
    bl_idname = "gtatools.file_import_col"
    bl_label = "GTA SA COL (.col)"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    def execute(self, context):
        from .ops.col_import import import_col as inu_import_col
        try:
            inu_import_col(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"Imported COL: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"COL import error: {str(e)}")
            return {'CANCELLED'}


def menu_func_export(self, context):
    self.layout.operator(GTATOOLS_OT_file_export_dff.bl_idname)
    self.layout.operator(GTATOOLS_OT_file_export_col.bl_idname)
    self.layout.operator(GTATOOLS_OT_file_export_txd.bl_idname)
    self.layout.operator(GTATOOLS_OT_file_export_ide.bl_idname)
    self.layout.operator(GTATOOLS_OT_file_export_ipl.bl_idname)


class GTATOOLS_OT_file_import_txd(bpy.types.Operator, ImportHelper):
    """Импорт TXD текстур GTA SA"""
    bl_idname = "gtatools.file_import_txd"
    bl_label = "GTA SA TXD (.txd)"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".txd"
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    def execute(self, context):
        from .ops.txd_import import import_txd as inu_import_txd
        try:
            images = inu_import_txd(filepath=self.filepath)
            self.report({'INFO'}, f"Imported TXD: {len(images)} textures")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"TXD import error: {str(e)}")
            return {'CANCELLED'}


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
    if '.' in name:
        base, suffix = name.rsplit('.', 1)
        if suffix.isdigit():
            name = base
    for sfx in ('_DFF', '_dff', '_COL', '_col', '_LOD', '_lod', '_SHA', '_sha'):
        if name.endswith(sfx):
            name = name[:-len(sfx)]
            break
    return name


class GTATOOLS_OT_import_from_img(bpy.types.Operator):
    """Импортировать модели из IMG архива (по списку из IDE/IPL)"""
    bl_idname = "gtatools.import_from_img"
    bl_label = "Import from IMG"
    bl_options = {'REGISTER', 'UNDO'}

    skip_lod: BoolProperty(
        name="Skip LOD",
        description=T("Пропустить LOD модели при импорте"),
        default=False
    )
    load_txd: BoolProperty(
        name="Load TXD",
        description=T("Загружать TXD текстуры вместе с DFF"),
        default=True
    )

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

        if not img_path or not os.path.isfile(img_path):
            self.report({'ERROR'}, T("Укажите путь к IMG архиву в INU Tools"))
            return {'CANCELLED'}

        # Read IDE for model definitions (optional)
        ide_models = {}
        if ide_path and os.path.isfile(ide_path):
            ide = read_ide(ide_path)
            for obj in ide.objects:
                ide_models[obj.model_id] = obj

        # Read IPL for placements
        instances = []
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

        with tempfile.TemporaryDirectory() as tmpdir:
            # Cache: already imported models (name -> list of created objects)
            imported_models = {}

            for idx, inst in enumerate(instances):
                wm.progress_update(idx)
                model_name = inst.model_name
                is_lod = model_name.upper().startswith('LOD')

                # Skip LOD models if option enabled
                if self.skip_lod and is_lod:
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
                        new_obj.data = src_obj.data.copy()
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
                        if self.load_txd:
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
                                    for co in col_objects:
                                        for c in list(co.users_collection):
                                            c.objects.unlink(co)
                                        col_collection.objects.link(co)
                                        co.location = col_pos
                                        co.rotation_mode = 'QUATERNION'
                                        co.rotation_quaternion = col_rot
                                except:
                                    pass

                        imported_models[model_name] = new_objects
                    except Exception as e:
                        errors.append(f"{model_name}: {str(e)}")
                        continue

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
        use_gpu = getattr(context.scene, 'gtatools_txd_use_gpu', False)

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
                # LOD draw distance = DFF draw distance + 50 if not set
                if lod_obj.inu.draw_distance == 300.0 and dff_obj:
                    lod_entry.draw_distance = dff_obj.inu.draw_distance + 50
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

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "model.ipl"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ops.ipl_export import export_ipl as inu_export_ipl
        try:
            objs = [o for o in context.selected_objects if o.type == 'MESH']
            inu_export_ipl(filepath=self.filepath, objects=objs)
            self.report({'INFO'}, f"Exported IPL: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL export error: {str(e)}")
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


# ── File > Export / Import IDE/IPL operators ──

class GTATOOLS_OT_file_export_ide(bpy.types.Operator, ExportHelper):
    """Экспорт IDE определений GTA SA"""
    bl_idname = "gtatools.file_export_ide"
    bl_label = "GTA SA IDE (.ide)"
    bl_options = {'PRESET'}
    filename_ext = ".ide"
    filter_glob: StringProperty(default="*.ide", options={'HIDDEN'})

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


class GTATOOLS_OT_file_export_ipl(bpy.types.Operator, ExportHelper):
    """Экспорт IPL размещения GTA SA"""
    bl_idname = "gtatools.file_export_ipl"
    bl_label = "GTA SA IPL (.ipl)"
    bl_options = {'PRESET'}
    filename_ext = ".ipl"
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def execute(self, context):
        from .ops.ipl_export import export_ipl as inu_export_ipl
        try:
            objs = [o for o in context.selected_objects if o.type == 'MESH']
            inu_export_ipl(filepath=self.filepath, objects=objs)
            self.report({'INFO'}, f"Exported IPL: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_file_import_ide(bpy.types.Operator, ImportHelper):
    """Импорт IDE определений GTA SA"""
    bl_idname = "gtatools.file_import_ide"
    bl_label = "GTA SA IDE (.ide)"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".ide"
    filter_glob: StringProperty(default="*.ide", options={'HIDDEN'})

    def execute(self, context):
        from .ops.ide_import import import_ide as inu_import_ide
        try:
            matched = inu_import_ide(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"IDE: {len(matched)} objects matched")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IDE import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_file_import_ipl(bpy.types.Operator, ImportHelper):
    """Импорт IPL размещения GTA SA"""
    bl_idname = "gtatools.file_import_ipl"
    bl_label = "GTA SA IPL (.ipl)"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".ipl"
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def execute(self, context):
        from .ops.ipl_import import import_ipl as inu_import_ipl
        try:
            placed = inu_import_ipl(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"IPL: {len(placed)} objects placed")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL import error: {str(e)}")
            return {'CANCELLED'}


def menu_func_import(self, context):
    self.layout.operator(GTATOOLS_OT_file_import_dff.bl_idname)
    self.layout.operator(GTATOOLS_OT_file_import_col.bl_idname)
    self.layout.operator(GTATOOLS_OT_file_import_txd.bl_idname)
    self.layout.operator(GTATOOLS_OT_file_import_ide.bl_idname)
    self.layout.operator(GTATOOLS_OT_file_import_ipl.bl_idname)


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
        use_gpu = context.scene.gtatools_txd_use_gpu

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
            self.report({'WARNING'}, f"{T('Ошибки:')} {'; '.join(errors)}")

        return {'FINISHED'}


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
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        prelight = GTASAPrelight(
            obj,
            split_angle=self.split_angle,
            normal_threshold=self.normal_threshold,
            top_color=tuple(self.top_color),
            bottom_color=tuple(self.bottom_color),
            ambient_color=tuple(self.ambient_color)
        )
        prelight.run()

        self.report({'INFO'}, "Prelight applied!")
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
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        success = average_colors_on_coplanar_faces(obj, self.normal_threshold)

        if success:
            self.report({'INFO'}, "Colors averaged!")
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
        obj = context.active_object
        scene = context.scene
        success, message = bake_vertex_colors_from_lights(obj, self.use_shadows)

        if success:
            # Сброс сохранённого v_offset для активного color attribute (UI остаётся)
            if obj.data.color_attributes.active_color:
                prop_name = f"v_offset_{obj.data.color_attributes.active_color.name}"
                obj[prop_name] = 0.0
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_bake_vertex_colors_simple(bpy.types.Operator):
    """Быстрое запекание vertex colors от Point источников (без теней)"""
    bl_idname = "gtatools.bake_vertex_colors_simple"
    bl_label = "Bake Vertex Colors (Fast)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        scene = context.scene

        # Get settings from panel
        ambient = scene.gtatools_bake_ambient
        intensity = scene.gtatools_bake_intensity
        gamma = scene.gtatools_bake_gamma
        use_shadows = scene.gtatools_bake_shadows

        success, message = bake_vertex_colors_simple(obj, ambient, intensity, gamma, use_shadows)

        if success:
            # Сброс сохранённого v_offset для активного color attribute (UI остаётся)
            if obj.data.color_attributes.active_color:
                prop_name = f"v_offset_{obj.data.color_attributes.active_color.name}"
                obj[prop_name] = 0.0
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
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
            self.report({'ERROR'}, "No vertex colors found!")
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
        obj = context.active_object
        scene = context.scene
        v_offset = scene.gtatools_v_offset

        success, message = apply_brightness_offset(obj, v_offset)

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_vc_smooth(bpy.types.Operator):
    """Сгладить vertex colors между соседними вершинами"""
    bl_idname = "gtatools.vc_smooth"
    bl_label = "Smooth Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        scene = context.scene
        iterations = scene.gtatools_vc_smooth_iterations
        factor = scene.gtatools_vc_smooth_factor

        success, message = smooth_vertex_colors(obj, iterations, factor)
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_vc_contrast(bpy.types.Operator):
    """Применить контраст к vertex colors"""
    bl_idname = "gtatools.vc_contrast"
    bl_label = "Apply Contrast"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        contrast = context.scene.gtatools_vc_contrast

        success, message = adjust_vertex_colors_contrast(obj, contrast)
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_vc_brightness(bpy.types.Operator):
    """Применить яркость к vertex colors"""
    bl_idname = "gtatools.vc_brightness"
    bl_label = "Apply Brightness"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        brightness = context.scene.gtatools_vc_brightness

        success, message = adjust_vertex_colors_brightness(obj, brightness)
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_vc_gamma(bpy.types.Operator):
    """Применить гамма-коррекцию к vertex colors"""
    bl_idname = "gtatools.vc_gamma"
    bl_label = "Apply Gamma"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        gamma = context.scene.gtatools_vc_gamma

        success, message = adjust_vertex_colors_gamma(obj, gamma)
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


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
            self.report({'ERROR'}, T("Нет vertex colors"))
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
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        mesh = obj.data
        created = []

        # Create Day attribute if not exists
        if "Day" not in mesh.color_attributes:
            attr = mesh.color_attributes.new(name="Day", type='BYTE_COLOR', domain='CORNER')
            for i in range(len(attr.data)):
                attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
            created.append("Day")

        # Create Night attribute if not exists
        if "Night" not in mesh.color_attributes:
            attr = mesh.color_attributes.new(name="Night", type='BYTE_COLOR', domain='CORNER')
            for i in range(len(attr.data)):
                attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
            created.append("Night")

        # Set Day as active
        if "Day" in mesh.color_attributes:
            mesh.color_attributes.active_color = mesh.color_attributes["Day"]

        if created:
            self.report({'INFO'}, f"Created: {', '.join(created)}")
        else:
            self.report({'INFO'}, "Day and Night already exist")

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

        if itera_mat is None:
            self.report({'ERROR'}, f"{T('Материал не найден:')} {target_name}")
            return {'CANCELLED'}

        # Apply to selected mesh objects
        applied = 0
        for obj in context.selected_objects:
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
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        mesh = obj.data
        if self.attribute_name not in mesh.color_attributes:
            self.report({'ERROR'}, f"Attribute '{self.attribute_name}' not found!")
            return {'CANCELLED'}

        # Set as active color attribute
        color_attr = mesh.color_attributes[self.attribute_name]
        mesh.color_attributes.active_color = color_attr

        # Update prelight preview on materials
        self.update_prelight_preview(obj, self.attribute_name)

        self.report({'INFO'}, f"Active: {self.attribute_name}")
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
    """Удалить color attribute по имени"""
    bl_idname = "gtatools.remove_color_attr"
    bl_label = "Remove Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    attr_name: StringProperty(default="")

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        mesh = obj.data

        if self.attr_name not in mesh.color_attributes:
            self.report({'ERROR'}, f"{self.attr_name} not found")
            return {'CANCELLED'}

        attr = mesh.color_attributes[self.attr_name]
        mesh.color_attributes.remove(attr)

        self.report({'INFO'}, f"Removed: {self.attr_name}")
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
    """Объединить дубликаты материалов (.001, .002, и т.д.) с оригиналами"""
    bl_idname = "gtatools.cleanup_materials"
    bl_label = "Cleanup Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import re

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

        if merged_count > 0 or removed_materials:
            self.report({'INFO'}, f"{T('Объединено:')} {merged_count} {T('слотов, удалено:')} {len(removed_materials)} {T('дубликатов')}")
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


# =============================================================================
# PANELS
# =============================================================================

class GTATOOLS_PT_main_panel(bpy.types.Panel):
    """Главная панель GTA Tools"""
    bl_label = "GTA Tools"
    bl_idname = "GTATOOLS_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'

    def draw(self, context):
        layout = self.layout
        layout.label(text="GTA SA Modding Tools", icon='TOOL_SETTINGS')


class GTATOOLS_PT_ide_ipl_panel(bpy.types.Panel):
    """Панель IDE / IPL для работы с существующими файлами GTA SA"""
    bl_label = "IDE / IPL"
    bl_idname = "GTATOOLS_PT_ide_ipl_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        obj = context.active_object

        # Show active object IDE/IPL props
        if obj and obj.type == 'MESH':
            inu = obj.inu
            box = layout.box()
            box.label(text=f"{obj.name}", icon='OBJECT_DATA')
            col = box.column(align=True)
            col.prop(inu, "model_id", text="Model ID")
            col.prop(inu, "draw_distance", text="Draw Dist")

            # Flags with expandable checkboxes
            row = box.row(align=True)
            row.prop(inu, "ide_flags", text="Flags")
            row.prop(scn, "gtatools_show_ide_flags",
                     icon='TRIA_DOWN' if scn.gtatools_show_ide_flags else 'TRIA_RIGHT',
                     text="", emboss=False)
            if scn.gtatools_show_ide_flags:
                fbox = box.box()
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

            row = box.row(align=True)
            row.prop(inu, "interior_id", text="Interior")
            row.prop(inu, "lod_index", text="LOD")
        else:
            layout.label(text=T("Выделите меш объект"), icon='INFO')

        layout.separator()

        # IDE section
        box = layout.box()
        box.label(text="IDE", icon='TEXT')
        row = box.row(align=True)
        row.operator("gtatools.upsert_ide", text=T("Добавить"), icon='ADD')
        row.operator("gtatools.remove_ide", text=T("Удалить"), icon='REMOVE')
        row = box.row(align=True)
        row.operator("gtatools.import_ide", text=T("Импорт"), icon='IMPORT')
        row.operator("gtatools.export_ide", text=T("Экспорт"), icon='EXPORT')

        layout.separator()

        # IPL section
        box = layout.box()
        box.label(text="IPL", icon='EMPTY_AXIS')
        row = box.row(align=True)
        row.operator("gtatools.upsert_ipl", text=T("Добавить"), icon='ADD')
        row.operator("gtatools.remove_ipl", text=T("Удалить"), icon='REMOVE')
        row = box.row(align=True)
        row.operator("gtatools.import_ipl", text=T("Импорт"), icon='IMPORT')
        row.operator("gtatools.export_ipl", text=T("Экспорт"), icon='EXPORT')

        layout.separator()

        # IMG section
        box = layout.box()
        box.label(text="IMG", icon='PACKAGE')
        row = box.row(align=True)
        row.prop(scn, "gtatools_img_export_dff", text="DFF", toggle=True)
        row.prop(scn, "gtatools_img_export_col", text="COL", toggle=True)
        row.prop(scn, "gtatools_img_export_txd", text="TXD", toggle=True)
        box.operator("gtatools.import_from_img", text=T("Импорт из IMG"), icon='IMPORT')
        box.operator("gtatools.export_to_img", text=T("Экспорт в IMG"), icon='EXPORT')


class GTATOOLS_PT_export_panel(bpy.types.Panel):
    """Панель экспорта GTA моделей"""
    bl_label = "Export"
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

        # Показываем найденные модели
        col = box.column()
        col.label(text=f"DFF: {models['DFF'].name}" if models['DFF'] else "DFF: -",
                 icon='CHECKMARK' if models['DFF'] else 'X')
        col.label(text=f"LOD: {models['LOD'].name}" if models['LOD'] else "LOD: -",
                 icon='CHECKMARK' if models['LOD'] else 'X')
        col.label(text=f"COL: {models['COL'].name}" if models['COL'] else "COL: -",
                 icon='CHECKMARK' if models['COL'] else 'X')

        layout.separator()

        # Export All button
        row = layout.row(align=True)
        row.operator("gtatools.export_all", text=T("Экспорт всего (DFF+COL+LOD+TXD)"), icon='EXPORT')
        row = layout.row(align=True)
        row.prop(context.scene, "gtatools_export_all_dff", text="DFF", toggle=True)
        row.prop(context.scene, "gtatools_export_all_col", text="COL", toggle=True)
        row.prop(context.scene, "gtatools_export_all_lod", text="LOD", toggle=True)
        row.prop(context.scene, "gtatools_export_all_txd", text="TXD", toggle=True)

        # Pipeline selector
        _draw_label_with_info(layout, "Pipeline:",
            T("None — без pipeline\nBuilding — Day/Night vertex colors (смена освещения по времени суток)\nReflections — отражения на окнах (окна должны быть отдельной моделью)"))
        row = layout.row(align=True)
        row.prop_enum(context.scene, "gtatools_export_pipeline", 'NONE')
        row.prop_enum(context.scene, "gtatools_export_pipeline", '0x53F2009A')
        row.prop_enum(context.scene, "gtatools_export_pipeline", '0x53F20098')

        # Individual export buttons
        _draw_label_with_info(layout, T("Экспорт по одному:"),
            T("DFF — модель (меш, материалы, UV)\nCOL — коллизия\nTXD — текстуры\nCheck vertex — висящие вершины и рёбра\nCheck N-gon — полигоны с 5+ вершинами\nCheck Material — лимит 50 материалов\nGPU (NVTT) — сжатие текстур на видеокарте"))
        row = layout.row(align=True)
        row.operator("gtatools.export_dff", text="DFF", icon='MESH_DATA')
        row.operator("gtatools.export_col", text="COL", icon='MESH_CUBE')

        row = layout.row(align=True)
        row.operator("gtatools.export_txd", text="TXD", icon='TEXTURE')

        # GPU/CPU переключатель
        row = layout.row(align=True)
        if hasattr(context.scene, "gtatools_txd_use_gpu"):
            row.prop(context.scene, "gtatools_txd_use_gpu", text="GPU (NVTT)", toggle=True)

        # Проверка NVTT если включен GPU
        if getattr(context.scene, "gtatools_txd_use_gpu", False):
            nvtt_path = context.scene.gtatools_nvtt_path
            available, msg = check_nvtt_available(nvtt_path)
            if not available:
                layout.label(text=T("Статус: Не найден"), icon='ERROR')


class GTATOOLS_PT_check_panel(bpy.types.Panel):
    """Панель проверки геометрии и материалов"""
    bl_label = "Check"
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

        row = layout.row(align=True)
        row.operator("gtatools.check_materials", text=T("Проверка материалов"), icon='MATERIAL')

        layout.separator()

        row = layout.row(align=True)
        row.operator("gtatools.cleanup_materials", text=T("Очистка материалов"), icon='BRUSH_DATA')
        row = layout.row(align=True)
        row.operator("gtatools.sort_materials", text=T("Сортировка материалов"), icon='SORTALPHA')


class GTATOOLS_PT_import_panel(bpy.types.Panel):
    """GTA models import panel"""
    bl_label = "Import"
    bl_idname = "GTATOOLS_PT_import_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        _draw_label_with_info(layout, T("Импорт по одному:"),
            T("DFF — импорт модели с мешем и материалами\nCOL — импорт коллизии\nTXD — импорт текстур\nIDE — определения объектов\nIPL — размещение объектов\nImport TXD — автоимпорт текстур при импорте DFF"))
        row = layout.row(align=True)
        row.operator("gtatools.import_dff", text="DFF", icon='MESH_DATA')
        row.operator("gtatools.import_col", text="COL", icon='MESH_CUBE')
        row.operator("gtatools.import_txd", text="TXD", icon='TEXTURE')

        layout.separator()
        layout.prop(context.scene, "gtatools_txd_auto_import", text=T("Импорт TXD"))


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

        # Визуальный превью для Light
        if self.effect_type == 'LIGHT':
            from .ops.fx_preview import create_light_preview
            create_light_preview(obj)

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
                and obj.inu.effect_2dfx == 'LIGHT')

    def execute(self, context):
        from .ops.fx_preview import update_light_preview
        update_light_preview(context.active_object)
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

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX'
                and obj.parent is not None)

    def execute(self, context):
        fx_obj = context.active_object
        parent_name = fx_obj.parent.name
        # Keep world position when unparenting
        world_matrix = fx_obj.matrix_world.copy()
        fx_obj.parent = None
        fx_obj.matrix_world = world_matrix
        self.report({'INFO'}, f"2DFX detached from '{parent_name}'")
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
        if effect == 'LIGHT':
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
            if '2dfx_effect_name' in obj:
                box.prop(obj, '["2dfx_effect_name"]', text=T("Имя эффекта"))

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


class GTATOOLS_PT_object_props_panel(bpy.types.Panel):
    """Панель свойств объекта GTA SA"""
    bl_label = "GTA SA Object"
    bl_idname = "GTATOOLS_PT_object_props_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        obj = context.object
        inu = obj.inu

        # ── Object Type ──
        layout.prop(inu, "type", text=T("Тип"))
        layout.separator()

        # ── DFF Flags (only for mesh objects) ──
        if obj.type == 'MESH':
            box = layout.box()
            _draw_label_with_info(box, T("Флаги геометрии:"),
                T("Light — динамическое освещение модели\nModulate Material Color — цвет материала влияет на модель\nExport Normals — экспорт нормалей (отключить для map объектов)"),
                icon='PREFERENCES')
            box.prop(inu, "light", text=T("Свет (rpGEOMETRYLIGHT)"))
            box.prop(inu, "modulate_color", text=T("Цвет материала модулирует"))
            box.prop(inu, "export_normals", text=T("Экспорт нормалей"))

            box = layout.box()
            _draw_label_with_info(box, T("Вертексные цвета:"),
                T("Day — дневные вертексные цвета (prelight)\nNight — ночные вертексные цвета (требует Pipeline: Building)"),
                icon='COLOR')
            box.prop(inu, "day_cols", text=T("Дневные верт. цвета"))
            box.prop(inu, "night_cols", text=T("Ночные верт. цвета"))

            box = layout.box()
            _draw_label_with_info(box, T("UV карты:"),
                T("UV Map 1 — основная UV развёртка\nUV Map 2 — вторая UV (для lightmap и т.д.)\nBin Mesh PLG — совместимость с просмотрщиками DFF"),
                icon='UV')
            box.prop(inu, "uv_map1", text=T("UV карта 1"))
            if inu.uv_map1:
                box.prop(inu, "uv_map2", text=T("UV карта 2"))

            box.prop(inu, "export_binsplit", text=T("Bin Mesh PLG"))

            # ── IDE / IPL Properties ──
            box = layout.box()
            _draw_label_with_info(box, "IDE / IPL:",
                T("Model ID — ID модели в GTA SA\nTXD Name — словарь текстур\nDraw Distance — дальность прорисовки\nIDE Flags — флаги объекта\nInterior — ID интерьера (0 = улица)\nLOD Index — индекс LOD модели (-1 = нет)"),
                icon='WORLD_DATA')
            box.prop(inu, "model_id", text="Model ID")
            box.prop(inu, "txd_name", text="TXD Name")
            box.prop(inu, "draw_distance", text="Draw Distance")
            box.prop(inu, "ide_flags", text="Flags")
            box.prop(inu, "interior_id", text="Interior")
            box.prop(inu, "lod_index", text="LOD Index")


def _draw_sort_materials_menu(self, context):
    """Append sort button to material context menu"""
    self.layout.separator()
    self.layout.operator("gtatools.sort_materials", text=T("Сортировка материалов"), icon='SORTALPHA')


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
                 text=T("IDE / IPL / IMG"), emboss=False)
        if scene.gtatools_show_paths_settings:
            box.label(text="IDE", icon='TEXT')
            box.prop(scene, "gtatools_ide_path", text="")
            box.label(text="IPL", icon='EMPTY_AXIS')
            box.prop(scene, "gtatools_ipl_path", text="")
            box.label(text="IMG", icon='PACKAGE')
            box.prop(scene, "gtatools_img_path", text="")

        layout.separator()

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
                 text=T("Суффиксы моделей"), emboss=False)
        if scene.gtatools_show_suffix_settings:
            box.prop(scene, "gtatools_suffix_dff", text="DFF")
            box.prop(scene, "gtatools_suffix_lod", text="LOD")
            box.prop(scene, "gtatools_suffix_col", text="COL")

        # ID Manager (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene, "gtatools_show_id_manager",
                 icon='TRIA_DOWN' if scene.gtatools_show_id_manager else 'TRIA_RIGHT',
                 text=T("Менеджер ID"), emboss=False)
        if scene.gtatools_show_id_manager:
            from .data.id_manager import get_free_ids, get_used_ids, get_file_path

            free = get_free_ids()
            used = get_used_ids()

            box.label(text=f"{T('Свободных:')} {len(free)}  |  {T('Занятых:')} {len(used)}", icon='PRESET')

            if free:
                box.label(text=f"{T('Следующий свободный:')} {free[0]}", icon='FORWARD')

            # Show used IDs
            if used:
                sub = box.box()
                col = sub.column(align=True)
                for id_num in sorted(used.keys()):
                    row = col.row(align=True)
                    row.label(text=f"{id_num} - {used[id_num]}")
                    op = row.operator("gtatools.id_manager_release", text="", icon='X')
                    op.model_id = id_num

            # Show free IDs (compact)
            if free:
                sub = box.box()
                text = ", ".join(str(i) for i in sorted(free)[:20])
                if len(free) > 20:
                    text += "..."
                sub.label(text=f"{T('Свободные:')} {text}", icon='DOT')

            row = box.row(align=True)
            row.operator("gtatools.id_manager_auto_assign", text=T("Назначить ID выделенным"), icon='ADD')
            row.operator("gtatools.id_manager_clear", text="", icon='TRASH')
            box.operator("gtatools.id_manager_open_file", text=T("Открыть файл ID"), icon='FILE_TEXT')


class GTATOOLS_OT_id_manager_open_file(bpy.types.Operator):
    """Открыть файл model_ids.txt в текстовом редакторе"""
    bl_idname = "gtatools.id_manager_open_file"
    bl_label = "Open ID File"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from .data.id_manager import get_file_path
        import subprocess, sys
        filepath = get_file_path()
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
                self.report({'ERROR'}, T("Нет свободных ID в model_ids.txt"))
                return {'CANCELLED'}
            obj.inu.model_id = new_id
            assigned += 1

        self.report({'INFO'}, f"{T('Назначено ID:')} {assigned}")
        return {'FINISHED'}


class GTATOOLS_OT_id_manager_clear(bpy.types.Operator):
    """Очистить все занятые ID"""
    bl_idname = "gtatools.id_manager_clear"
    bl_label = "Clear All IDs"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        from .data.id_manager import clear_all
        clear_all()
        self.report({'INFO'}, T("Все ID очищены"))
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
            op_on = row.operator("gtatools.prelight_preview", text="", icon='HIDE_OFF')
            op_on.enable = True
            op_off = row.operator("gtatools.prelight_preview", text="", icon='HIDE_ON')
            op_off.enable = False
            row.operator("gtatools.create_day_night", text="Day/Night")
            row.operator("gtatools.add_color_attribute", text="", icon='ADD')
            row.operator("gtatools.remove_color_attribute", text="", icon='REMOVE')

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
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'presets')


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
    bl_label = "Lightmap Generator (beta)"
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


# =============================================================================
# =============================================================================
# REGISTRATION
# =============================================================================

classes = (
    INUObjectProps,
    INUMaterialProps,
    GTATOOLS_FillColorItem,
    GTATOOLS_OT_check_geometry,
    GTATOOLS_OT_check_ngons,
    GTATOOLS_OT_export_txd,
    GTATOOLS_OT_export_dff,
    GTATOOLS_OT_export_col,
    GTATOOLS_OT_export_all,
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
    GTATOOLS_OT_check_materials,
    GTATOOLS_OT_cleanup_materials,
    GTATOOLS_OT_sort_materials,
    GTATOOLS_OT_id_manager_open_file,
    GTATOOLS_OT_id_manager_release,
    GTATOOLS_OT_id_manager_auto_assign,
    GTATOOLS_OT_id_manager_clear,
    GTATOOLS_OT_toggle_uv_editor,
    GTATOOLS_OT_toggle_uv_grid,
    GTATOOLS_OT_randomize_uv_grid,
    GTATOOLS_OT_snap_uv_to_grid,
    GTATOOLS_OT_set_uv_align,
    GTATOOLS_PT_main_panel,
    GTATOOLS_OT_import_dff,
    GTATOOLS_OT_import_col,
    GTATOOLS_OT_import_txd,
    GTATOOLS_OT_file_export_dff,
    GTATOOLS_OT_file_export_col,
    GTATOOLS_OT_file_export_txd,
    GTATOOLS_OT_file_import_dff,
    GTATOOLS_OT_file_import_col,
    GTATOOLS_OT_file_import_txd,
    GTATOOLS_OT_import_from_img,
    GTATOOLS_OT_export_to_img,
    GTATOOLS_OT_upsert_ide,
    GTATOOLS_OT_upsert_ipl,
    GTATOOLS_OT_remove_ide,
    GTATOOLS_OT_remove_ipl,
    GTATOOLS_OT_export_ide,
    GTATOOLS_OT_export_ipl,
    GTATOOLS_OT_import_ide,
    GTATOOLS_OT_import_ipl,
    GTATOOLS_OT_file_export_ide,
    GTATOOLS_OT_file_export_ipl,
    GTATOOLS_OT_file_import_ide,
    GTATOOLS_OT_file_import_ipl,
    GTATOOLS_PT_ide_ipl_panel,
    GTATOOLS_PT_export_panel,
    GTATOOLS_PT_check_panel,
    GTATOOLS_PT_import_panel,
    GTATOOLS_OT_apply_2dfx_preset,
    GTATOOLS_OT_create_2dfx,
    GTATOOLS_OT_attach_2dfx,
    GTATOOLS_OT_detach_2dfx,
    GTATOOLS_OT_refresh_2dfx_preview,
    GTATOOLS_OT_remove_2dfx_preview,
    GTATOOLS_OT_set_col_surface,
    GTATOOLS_OT_col_surface_menu,
    GTATOOLS_PT_col_material_panel,
    GTATOOLS_PT_material_effects_panel,
    GTATOOLS_PT_object_props_panel,
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
    GTATOOLS_PT_uv_tools_panel,
    GTATOOLS_OT_add_gtasa_model,
    VIEW3D_MT_gtasa_add_menu,
)


# ── Persistent paths (saved in Blender config, survive addon updates) ──

_PATHS_FILE = None

def _get_paths_file():
    global _PATHS_FILE
    if _PATHS_FILE is None:
        config = bpy.utils.resource_path('USER')
        d = os.path.join(config, 'config')
        os.makedirs(d, exist_ok=True)
        _PATHS_FILE = os.path.join(d, 'inu_tools_paths.json')
    return _PATHS_FILE

_SAVED_PATH_KEYS = [
    'gtatools_ide_path', 'gtatools_ipl_path', 'gtatools_img_path',
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
                cur = getattr(scene, key, '')
                if not cur:  # Only set if current is empty
                    setattr(scene, key, val)
    except:
        pass


def register():
    # Auto-translate tooltips: docstrings are in Russian,
    # bl_description is set via T() so locale/eng.py handles English
    for cls in classes:
        doc = getattr(cls, '__doc__', None)
        if doc and doc.strip():
            cls.bl_description = T(doc.strip())
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

    bpy.types.Scene.gtatools_txd_import_path = StringProperty(
        name="TXD Import Folder",
        description=T("Папка для поиска TXD при импорте DFF (пусто = автопоиск в папке DFF)"),
        default="",
        subtype='DIR_PATH'
    )

    bpy.types.Scene.gtatools_nvtt_path = StringProperty(
        name="NVTT Path",
        description=T("Путь к папке NVIDIA Texture Tools (для GPU сжатия)"),
        default=r"D:\NVIDIA Corporation\NVIDIA Texture Tools",
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

    bpy.types.Scene.gtatools_show_ide_flags = BoolProperty(
        name="Show IDE Flags",
        description=T("Показать флаги IDE"),
        default=False
    )
    bpy.types.Scene.gtatools_suffix_dff = StringProperty(
        name="DFF Suffix",
        description=T("Суффикс для DFF моделей (например _DFF или DFF)"),
        default="_DFF"
    )
    bpy.types.Scene.gtatools_suffix_lod = StringProperty(
        name="LOD Suffix",
        description=T("Суффикс для LOD моделей (например _LOD или LOD)"),
        default="_LOD"
    )
    bpy.types.Scene.gtatools_suffix_col = StringProperty(
        name="COL Suffix",
        description=T("Суффикс для COL моделей (например _COL или COL)"),
        default="_COL"
    )

    # ID Manager
    bpy.types.Scene.gtatools_show_id_manager = BoolProperty(
        name="Show ID Manager",
        description=T("Показать менеджер ID"),
        default=False
    )
    # Texture loader paths
    bpy.types.Scene.gtatools_texture_path1 = StringProperty(
        name="System Textures Path",
        description=T("Путь к папке с системными текстурами GTA"),
        default=r"E:\Project MTA\System_textures",
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
            ('NONE', 'None', 'No pipeline'),
            ('0x53F2009A', 'Building', 'Day/Night vertex colors for buildings'),
            ('0x53F20098', 'Reflections', 'Window reflections on buildings'),
        ],
        name="Pipeline",
        description=T("Рендер-пайплайн для экспорта DFF"),
        default='0x53F2009A',
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

    # Load paths for current scene
    _load_paths(bpy.context.scene)

    print("[GTA Tools Panel] Addon registered!")


@persistent
@persistent
def _on_file_load_restore_paths(dummy):
    """Restore saved paths after loading a .blend file."""
    _load_paths(bpy.context.scene)


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
    if _2dfx_sync_busy:
        return
    obj = bpy.context.active_object
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
    del bpy.types.Scene.gtatools_img_export_dff
    del bpy.types.Scene.gtatools_img_export_col
    del bpy.types.Scene.gtatools_img_export_txd
    del bpy.types.Scene.gtatools_ide_path
    del bpy.types.Scene.gtatools_ipl_path
    del bpy.types.Scene.gtatools_txd_auto_import
    del bpy.types.Scene.gtatools_txd_import_path
    del bpy.types.Scene.gtatools_nvtt_path
    del bpy.types.Scene.gtatools_txd_use_gpu
    del bpy.types.Scene.gtatools_show_nvtt_settings
    del bpy.types.Scene.gtatools_show_texture_settings
    del bpy.types.Scene.gtatools_show_paths_settings
    del bpy.types.Scene.gtatools_show_suffix_settings
    del bpy.types.Scene.gtatools_show_ide_flags
    del bpy.types.Scene.gtatools_suffix_dff
    del bpy.types.Scene.gtatools_suffix_lod
    del bpy.types.Scene.gtatools_suffix_col
    del bpy.types.Scene.gtatools_show_id_manager
    del bpy.types.Scene.gtatools_texture_path2
    del bpy.types.Scene.gtatools_texture_path1
    del bpy.types.Scene.gtatools_export_pipeline
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
    del bpy.types.Scene.gtatools_bake_ambient
    del bpy.types.Scene.gtatools_vc_analysis
    del bpy.types.Scene.gtatools_lightmap_result
    del bpy.types.Scene.gtatools_lightmap_path
    del bpy.types.Scene.gtatools_model_id

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    print("[GTA Tools Panel] Addon unregistered!")


if __name__ == "__main__":
    register()
