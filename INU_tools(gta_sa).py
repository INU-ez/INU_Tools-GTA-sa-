# INU_tools(gta_sa) for Blender 4.4
# Объединённая панель инструментов для работы с GTA SA моделями
# Включает: Export (DFF, COL, LOD, TXD), Prelight, Lightmap Generator
#
# This addon depends on DragonFF addon for DFF/COL export.
# DragonFF © its respective authors.

bl_info = {
    "name": "INU_tools(gta_sa)",
    "author": "INU",
    "version": (1, 4, 5),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar (N) > GTA Tools",
    "description": "Toolset for GTA SA models. Requires DragonFF addon",
    "warning": "Requires DragonFF addon installed for DFF/COL export",
    "category": "3D View",
}

# Changelog:
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
import struct
import os
import tempfile
import subprocess
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from mathutils import Vector
from bpy.props import StringProperty, BoolProperty, FloatProperty, FloatVectorProperty, IntProperty, CollectionProperty
from bpy_extras.io_utils import ExportHelper


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
TRANSLATIONS = {
    # bl_info
    "Набор инструментов для работы с GTA SA моделями. Requires DragonFF addon":
        "Toolset for GTA SA models. Requires DragonFF addon",

    # Property descriptions
    "Выделить найденные проблемные элементы": "Select found problem elements",
    "Количество колонок в сетке текстуры": "Number of columns in texture grid",
    "Количество рядов в сетке текстуры": "Number of rows in texture grid",
    "Позиция UV в ячейке": "UV position in cell",
    "Полигоны с пересекающимися UV перемещаются вместе": "Polygons with overlapping UVs move together",
    "Путь к папке NVIDIA Texture Tools (для GPU сжатия)": "Path to NVIDIA Texture Tools folder (for GPU compression)",
    "Использовать GPU (NVTT) для сжатия текстур": "Use GPU (NVTT) for texture compression",
    "Показать настройки NVTT": "Show NVTT settings",
    "Путь к папке с системными текстурами GTA": "Path to GTA system textures folder",
    "Путь к папке где находится .blend файл": "Path to folder where .blend file is located",
    "Не экспортировать TXD при Export All": "Do not export TXD with Export All",
    "Пропустить TXD": "Skip TXD",

    # Enum items (label, description)
    "Центр": "Center",
    "По центру ячейки": "Center of cell",
    "Сверху слева": "Top Left",
    "В верхнем левом углу": "In top left corner",
    "Сверху": "Top",
    "Сверху по центру": "Top center",
    "Сверху справа": "Top Right",
    "В верхнем правом углу": "In top right corner",
    "Слева": "Left",
    "Слева по центру": "Left center",
    "Справа": "Right",
    "Справа по центру": "Right center",
    "Снизу слева": "Bottom Left",
    "В нижнем левом углу": "In bottom left corner",
    "Снизу": "Bottom",
    "Снизу по центру": "Bottom center",
    "Снизу справа": "Bottom Right",
    "В нижнем правом углу": "In bottom right corner",

    # UI text
    "Пропустить TXD": "Skip TXD",
    "Статус: Готов": "Status: Ready",
    "Статус: Не найден": "Status: Not found",
    "Папка .blend:": ".blend Folder:",
    "Загрузить текстуры": "Load Textures",
    "Очистка материалов": "Cleanup Materials",
    "Проверить материалы": "Check Materials",
    "Очистить всё": "Clear All",
    "Отменить": "Undo",
    "Колонки": "Columns",
    "Ряды": "Rows",
    "Скрыть сетку": "Hide Grid",
    "Показать сетку": "Show Grid",
    "Позиция": "Position",
    "Связать полигоны": "Link Polygons",
    "Рандом": "Random",
    "Привязать": "Snap",

    # Report messages
    "Выберите меш объект!": "Select a mesh object!",
    "Не меш объект": "Not a mesh object",
    "Геометрия в порядке!": "Geometry is OK!",
    "висящих вершин": "loose vertices",
    "висящих рёбер": "loose edges",
    "N-gons не найдены!": "No N-gons found!",
    "N-gons (5+ вершин)": "N-gons (5+ vertices)",
    "Нечего удалять - геометрия чистая!": "Nothing to delete - geometry is clean!",
    "Удалено:": "Deleted:",
    "вершин,": "vertices,",
    "рёбер": "edges",
    "Выделите модели для экспорта!": "Select models for export!",
    "Не удалось определить имя модели!": "Could not determine model name!",
    "Экспортировано:": "Exported:",
    "Ошибки:": "Errors:",
    "Найдено:": "Found:",
    "Среди выделенных не найдено DFF/LOD/COL моделей": "No DFF/LOD/COL models found among selected",
    "Укажите хотя бы один путь к папке с текстурами!": "Specify at least one path to textures folder!",
    "Выберите материал в списке!": "Select a material in the list!",
    "Выберите корректный материал!": "Select a valid material!",
    "Не удалось загрузить": "Failed to load",
    "Загружена текстура:": "Texture loaded:",
    "Текстура уже подключена:": "Texture already connected:",
    "Текстура не найдена:": "Texture not found:",
    "Путь установлен": "Path set",
    "Сначала сохраните .blend файл!": "Save .blend file first!",
    "Файл не указан!": "File not specified!",
    "Неподдерживаемый формат:": "Unsupported format:",
    "Ошибка загрузки:": "Loading error:",
    "Создан материал:": "Material created:",
    "Выделите меш объекты!": "Select mesh objects!",
    "Объектов:": "Objects:",
    "всего материалов:": "total materials:",
    "превышен лимит:": "limit exceeded:",
    "Объединено:": "Merged:",
    "слотов, удалено:": "slots, removed:",
    "дубликатов": "duplicates",
    "Дубликаты материалов не найдены": "No duplicate materials found",
    "Сохраните .blend файл сначала!": "Save .blend file first!",
    "Текстуры с приставкой LP_ не найдены в папке:": "Textures with LP_ prefix not found in folder:",
    "Не удалось применить лайтмап - нет подходящих материалов": "Could not apply lightmap - no suitable materials",
    "Настройки сброшены по умолчанию": "Settings reset to default",
    "Код очищен": "Code cleared",
    "Сетка UV включена": "UV grid enabled",
    "Сетка UV выключена": "UV grid disabled",
    "Укажите количество колонок и рядов!": "Specify number of columns and rows!",
    "Выделите полигоны!": "Select polygons!",
    "Рандомизировано:": "Randomized:",
    "групп": "groups",
    "полигонов": "polygons",
    "Привязано:": "Snapped:",
    "Выберите меш!": "Select a mesh!",
    "Нет vertex colors!": "No vertex colors!",
    "Выделено": "Selected",
    "полигонов": "polygons",
    "меш(ей)": "mesh(es)",

    # Function docstrings (for bl_description via __doc__)
    "Проверить геометрию на висящие вершины и рёбра": "Check geometry for loose vertices and edges",
    "Проверить геометрию на N-gons (полигоны с 5+ вершинами)": "Check geometry for N-gons (polygons with 5+ vertices)",
    "Удалить висящие вершины и рёбра": "Delete loose vertices and edges",
    "Экспортировать текстуры в TXD архив": "Export textures to TXD archive",
    "Экспортировать DFF модель": "Export DFF model",
    "Экспортировать COL модель коллизии": "Export COL collision model",
    "Экспорт всех выделенных моделей (DFF + COL + LOD + TXD)": "Export all selected models (DFF + COL + LOD + TXD)",
    "Определить модели DFF, LOD, COL среди выделенных": "Detect DFF, LOD, COL models among selected",
    "Применить GTA SA Prelight к выделенному объекту": "Apply GTA SA Prelight to selected object",
    "Усреднить vertex colors для компланарных граней": "Average vertex colors for coplanar faces",
    "Сгенерировать код lightmap для выделенного объекта": "Generate lightmap code for selected object",
    "Копировать результат в буфер обмена": "Copy result to clipboard",
    "Очистить сгенерированный код": "Clear generated code",
    "Создать 8 источников света для запекания prelight вокруг объекта": "Create 8 lights for prelight baking around object",
    "Удалить все источники света prelight": "Remove all prelight lights",
    "Запечь освещение от Point источников в vertex colors": "Bake lighting from Point sources to vertex colors",
    "Быстрое запекание vertex colors от Point источников (без теней)": "Quick bake vertex colors from Point sources (no shadows)",
    "Сбросить настройки запекания по умолчанию": "Reset bake settings to default",
    "Сбросить настройки Scatter Light по умолчанию": "Reset Scatter Light settings to default",
    "Анализировать vertex colors выделенного объекта": "Analyze vertex colors of selected object",
    "Применить смещение яркости (V) к vertex colors": "Apply brightness offset (V) to vertex colors",
    "Загрузить Lightmap из папки с .blend файлом (текстуры с приставкой LP_)": "Load Lightmap from .blend folder (textures with LP_ prefix)",
    "Удалить Lightmap из материалов объекта": "Remove Lightmap from object materials",
    "Создать Day и Night color attributes": "Create Day and Night color attributes",
    "Переключить превью prelight - показать vertex colors с текстурами": "Toggle prelight preview - show vertex colors with textures",
    "Кликните на полигон чтобы взять его цвет": "Click on polygon to pick its color",
    "Залить выделенные грани цветом": "Fill selected faces with color",
    "Восстановить цвета, изменённые заливкой": "Restore colors changed by fill",
    "Удалить цвет из списка и восстановить оригинальные цвета": "Delete color from list and restore original colors",
    "Выделить полигоны с этим цветом": "Select polygons with this color",
    "Удалить scatter уровень (пересчитать цвета)": "Delete scatter level (recalculate colors)",
    "Очистить все scatter уровни цвета": "Clear all scatter levels of color",
    "Рассеять свет от выделенных граней к соседним": "Scatter light from selected faces to neighbors",
    "Переключить режим выделения граней в Vertex Paint": "Toggle face selection mode in Vertex Paint",
    "Переключить в Edit Mode для выделения граней": "Switch to Edit Mode for face selection",
    "Переключить в Vertex Paint Mode": "Switch to Vertex Paint Mode",
    "Выбрать color attribute и обновить превью prelight": "Select color attribute and update prelight preview",
    "Добавить новый color attribute": "Add new color attribute",
    "Удалить активный color attribute": "Delete active color attribute",
    "Создать color attribute": "Create color attribute",
    "Удалить color attribute по имени": "Delete color attribute by name",
    "Загрузить текстуры по именам материалов из указанных папок": "Load textures by material names from specified folders",
    "Установить путь к папке .blend файла": "Set path to .blend file folder",
    "Создать материал из перетаскиваемой текстуры": "Create material from dropped texture",
    "Проверить количество материалов на выделенных объектах": "Check material count on selected objects",
    "Объединить дубликаты материалов (.001, .002, и т.д.) с оригиналами": "Merge duplicate materials (.001, .002, etc.) with originals",
    "Показать/скрыть сетку на UV": "Show/hide grid on UV",
    "Рандомно распределить UV выделенных полигонов по сетке (для окон, вариаций)": "Randomly distribute UV of selected polygons on grid (for windows, variations)",
    "Привязать UV выделенных полигонов к ближайшей ячейке сетки": "Snap UV of selected polygons to nearest grid cell",

    # Panel docstrings
    "Главная панель GTA Tools": "GTA Tools main panel",
    "Панель экспорта GTA моделей": "GTA models export panel",
    "Панель INU Tools в Properties > Scene": "INU Tools panel in Properties > Scene",
    "Панель Prelight": "Prelight panel",
    "Расширенные настройки запекания": "Advanced bake settings",
    "Панель инструментов Vertex Paint": "Vertex Paint tools panel",
    "Панель генератора Lightmap": "Lightmap generator panel",
    "Панель UV инструментов GTA Tools": "GTA Tools UV panel",

    # Other docstrings
    "Проверить доступность NVIDIA Texture Tools": "Check NVIDIA Texture Tools availability",
    "Папка NVTT не найдена": "NVTT folder not found",
    "Сжать текстуру через NVIDIA Texture Tools (GPU)": "Compress texture via NVIDIA Texture Tools (GPU)",
    "Проверить, подключена ли нода к чему-либо (любой выход)": "Check if node is connected to anything (any output)",
    "Определить тип модели по суффиксу: LOD, COL, DFF в конце названия": "Determine model type by suffix: LOD, COL, DFF at end of name",
    "Найти связанные модели (DFF, LOD, COL) по базовому имени": "Find related models (DFF, LOD, COL) by base name",
    "Найти модели DFF, LOD, COL только среди выделенных объектов": "Find DFF, LOD, COL models only among selected objects",
    "Получить базовое имя из выделенных моделей": "Get base name from selected models",
    "Сохранить базовые цвета если ещё не сохранены": "Save base colors if not saved yet",
    "Пересчитать цвет одного loop: ИТОГ = (База ИЛИ Fill) + Σ Scatter": "Recalculate color of one loop: RESULT = (Base OR Fill) + Σ Scatter",
    "Пересчитать цвета для указанных loops (или всех если не указано)": "Recalculate colors for specified loops (or all if not specified)",
    "Добавить Fill слой для указанных loops": "Add Fill layer for specified loops",
    "Получить список уровней scatter для цвета": "Get list of scatter levels for color",
    "Удалить Scatter слой и пересчитать цвета": "Delete Scatter layer and recalculate colors",
    "Удалить все Scatter слои для цвета и пересчитать": "Delete all Scatter layers for color and recalculate",
    "Удалить Fill цвет и все его Scatter слои, пересчитать": "Delete Fill color and all its Scatter layers, recalculate",
    "Удалить цвет из списка по индексу": "Delete color from list by index",
    "Получить Fill цвет выделенных полигонов": "Get Fill color of selected polygons",
    "Проверить объект на висящие вершины и рёбра (не присоединённые к полигонам)": "Check object for loose vertices and edges (not attached to polygons)",
    "Элемент списка цветов заливки": "Fill color list item",
}

def T(text):
    """Translate text based on Blender UI language"""
    if get_locale() == 'ru':
        return text  # Return Russian as-is
    return TRANSLATIONS.get(text, text)  # Return English translation or original


# =============================================================================
# TXD EXPORTER
# =============================================================================

RW_TEXDICTIONARY = 0x16
RW_TEXTURENATIVE = 0x15
RW_STRUCT = 0x01
RW_EXTENSION = 0x03
RW_VERSION = 0x1803FFFF
PLATFORM_D3D9 = 9
RASTER_565 = 0x0200
RASTER_8888 = 0x0500
RASTER_MIPMAP = 0x8000
FILTER_LINEAR = 0x02
ADDRESS_WRAP = 0x01


def make_filter_flags():
    return FILTER_LINEAR | (ADDRESS_WRAP << 8) | (ADDRESS_WRAP << 12)


def check_nvtt_available(nvtt_path):
    """Check NVIDIA Texture Tools availability"""
    if not nvtt_path or not os.path.isdir(nvtt_path):
        return False, "Папка NVTT не найдена"
    nvcompress = os.path.join(nvtt_path, "nvcompress.exe")
    if not os.path.isfile(nvcompress):
        return False, "nvcompress.exe не найден в указанной папке"
    return True, nvcompress


def compress_with_nvtt(name, image, use_alpha, nvcompress_path):
    """Compress texture via NVIDIA Texture Tools (GPU)"""
    temp_dir = tempfile.gettempdir()
    # Используем безопасное имя файла
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    input_file = os.path.join(temp_dir, f"_nvtt_{safe_name}.png")
    output_file = os.path.join(temp_dir, f"_nvtt_{safe_name}.dds")

    try:
        # Сохраняем изображение через Blender (правильная ориентация)
        old_path = image.filepath_raw
        old_format = image.file_format
        image.filepath_raw = input_file
        image.file_format = 'PNG'
        image.save()
        image.filepath_raw = old_path
        image.file_format = old_format

        width, height = image.size[0], image.size[1]

        # Вызвать nvcompress
        # -alpha говорит nvcompress что PNG имеет alpha канал
        fmt = "-bc2" if use_alpha else "-bc1"  # bc1=DXT1, bc2=DXT3
        alpha_flag = ["-alpha"] if use_alpha else []
        cmd = [nvcompress_path, "-nocuda", fmt, "-mipmap"] + alpha_flag + [input_file, output_file]

        # Попробовать с CUDA, если не получится - без
        cmd_cuda = [nvcompress_path, fmt, "-mipmap"] + alpha_flag + [input_file, output_file]

        result = subprocess.run(cmd_cuda, capture_output=True, timeout=60)
        if result.returncode != 0:
            result = subprocess.run(cmd, capture_output=True, timeout=60)

        if not os.path.exists(output_file):
            return None

        # Прочитать DDS и извлечь данные
        with open(output_file, 'rb') as f:
            dds_data = f.read()

        # Парсим DDS
        if dds_data[:4] != b'DDS ':
            return None

        # DDS Header (124 байта после "DDS ")
        dds_height = struct.unpack('<I', dds_data[12:16])[0]
        dds_width = struct.unpack('<I', dds_data[16:20])[0]
        mip_count = struct.unpack('<I', dds_data[28:32])[0]
        if mip_count == 0:
            mip_count = 1

        # Проверяем на DX10 extended header
        pf_fourcc = dds_data[84:88]
        header_size = 128
        if pf_fourcc == b'DX10':
            header_size = 148  # 128 + 20 bytes DX10 header

        # Данные начинаются после заголовка
        pixel_data = dds_data[header_size:]

        # Создаём TXD структуру
        if use_alpha:
            dxt_type = 3
            raster_format = RASTER_8888 | RASTER_MIPMAP
            depth = 32
            block_size = 16
        else:
            dxt_type = 1
            raster_format = RASTER_565 | RASTER_MIPMAP
            depth = 16
            block_size = 8

        tex_name = name[:31].encode('ascii', errors='replace').ljust(32, b'\x00')
        fourcc = b'DXT1' if dxt_type == 1 else b'DXT3'

        # Собираем мипмапы
        struct_data = bytearray()
        struct_data.extend(struct.pack('<II', PLATFORM_D3D9, make_filter_flags()))
        struct_data.extend(tex_name)
        struct_data.extend(b'\x00' * 32)
        struct_data.extend(struct.pack('<I', raster_format))
        struct_data.extend(fourcc)
        struct_data.extend(struct.pack('<HH', dds_width, dds_height))
        struct_data.extend(struct.pack('<B', depth))
        struct_data.extend(struct.pack('<B', mip_count))
        struct_data.extend(struct.pack('<B', 4))  # raster type
        struct_data.extend(struct.pack('<B', 0x08))  # D3D format flag

        # Извлекаем каждый мип-уровень
        offset = 0
        mip_w, mip_h = dds_width, dds_height
        for _ in range(mip_count):
            blocks_x = max(1, (mip_w + 3) // 4)
            blocks_y = max(1, (mip_h + 3) // 4)
            mip_size = blocks_x * blocks_y * block_size

            if offset + mip_size <= len(pixel_data):
                mip_data = pixel_data[offset:offset + mip_size]
                struct_data.extend(struct.pack('<I', len(mip_data)))
                struct_data.extend(mip_data)
                offset += mip_size

            mip_w = max(1, mip_w // 2)
            mip_h = max(1, mip_h // 2)

        tex_native = bytearray()
        write_rw_section_header(tex_native, RW_STRUCT, len(struct_data))
        tex_native.extend(struct_data)
        write_rw_section_header(tex_native, RW_EXTENSION, 0)

        return bytes(tex_native)

    except Exception as e:
        print(f"NVTT ERROR: {name}: {e}")
        return None

    finally:
        # Очистка временных файлов
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)


def write_rw_section_header(data, section_type, size):
    data.extend(struct.pack('<III', section_type, size, RW_VERSION))


def is_texture_connected_to_alpha(tex_node):
    # Alpha выход - индекс 1 у TEX_IMAGE
    if len(tex_node.outputs) < 2:
        return False
    alpha_output = tex_node.outputs[1]
    if not alpha_output.is_linked:
        return False
    # Проверяем что подключено к Principled BSDF (любой вход с alpha в имени)
    for link in alpha_output.links:
        to_node = link.to_socket.node
        if to_node.type == 'BSDF_PRINCIPLED':
            # Проверяем по индексу или имени (Alpha вход ~индекс 21, но лучше по имени)
            socket_name = link.to_socket.name.lower()
            socket_id = link.to_socket.identifier.lower() if hasattr(link.to_socket, 'identifier') else ''
            if 'alpha' in socket_name or 'alpha' in socket_id or 'альфа' in socket_name:
                return True
    return False


def check_image_has_transparent_pixels(image):
    try:
        pixels = np.array(image.pixels[:])
        if len(pixels) < 4:
            return False
        alpha = pixels[3::4]
        return np.any(alpha < 0.99)
    except:
        return False


def is_node_connected(node):
    """Check if node is connected to anything (any output)"""
    for output in node.outputs:
        if output.is_linked:
            return True
    return False


def collect_textures(selected_only=False):
    textures = {}
    transparent_textures = set()

    if selected_only:
        materials = set()
        for obj in bpy.context.selected_objects:
            if hasattr(obj, 'material_slots'):
                for slot in obj.material_slots:
                    if slot.material:
                        materials.add(slot.material)
        materials = list(materials)
    else:
        materials = bpy.data.materials

    for mat in materials:
        if not mat.use_nodes or not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                # Игнорировать ноды которые ни к чему не подключены
                if not is_node_connected(node):
                    continue

                img = node.image
                name = os.path.splitext(img.name)[0]
                alpha_connected = is_texture_connected_to_alpha(node)
                has_transparent = check_image_has_transparent_pixels(img)
                if has_transparent:
                    transparent_textures.add(img.name)
                # DXT3 только если альфа подключена И есть прозрачные пиксели
                uses_alpha = alpha_connected and has_transparent
                if name in textures:
                    existing_alpha = textures[name][1]
                    textures[name] = (img, existing_alpha or uses_alpha)
                else:
                    textures[name] = (img, uses_alpha)

    return textures, list(transparent_textures)


def downsample_image(pixels, width, height):
    new_w = max(1, width // 2)
    new_h = max(1, height // 2)
    if width == 1 and height == 1:
        return None, 0, 0
    if width > 1 and height > 1:
        reshaped = pixels[:new_h*2, :new_w*2].reshape(new_h, 2, new_w, 2, 4)
        downsampled = reshaped.mean(axis=(1, 3)).astype(np.uint8)
    elif width > 1:
        downsampled = pixels[:1, :new_w*2].reshape(1, new_w, 2, 4).mean(axis=2).astype(np.uint8)
    elif height > 1:
        downsampled = pixels[:new_h*2, :1].reshape(new_h, 2, 1, 4).mean(axis=1).astype(np.uint8)
    else:
        return None, 0, 0
    return downsampled, new_w, new_h


def pad_to_4x4(pixels, width, height):
    if width >= 4 and height >= 4:
        return pixels, width, height
    pad_w = max(4, width)
    pad_h = max(4, height)
    padded = np.zeros((pad_h, pad_w, 4), dtype=np.uint8)
    padded[:height, :width] = pixels
    if width < pad_w:
        padded[:height, width:] = pixels[:, -1:, :]
    if height < pad_h:
        padded[height:, :width] = pixels[-1:, :, :]
    if width < pad_w and height < pad_h:
        padded[height:, width:] = pixels[-1, -1, :]
    return padded, pad_w, pad_h


def compress_dxt1_block(rgb):
    rgb = rgb.astype(np.float32)
    lum = rgb[:, 0] * 0.299 + rgb[:, 1] * 0.587 + rgb[:, 2] * 0.114
    min_idx, max_idx = np.argmin(lum), np.argmax(lum)
    c0, c1 = rgb[max_idx], rgb[min_idx]

    def to_565(c):
        r = int(np.clip(c[0] / 255.0 * 31 + 0.5, 0, 31))
        g = int(np.clip(c[1] / 255.0 * 63 + 0.5, 0, 63))
        b = int(np.clip(c[2] / 255.0 * 31 + 0.5, 0, 31))
        return (r << 11) | (g << 5) | b

    def from_565(c):
        return np.array([
            ((c >> 11) & 0x1F) * 255.0 / 31.0,
            ((c >> 5) & 0x3F) * 255.0 / 63.0,
            (c & 0x1F) * 255.0 / 31.0
        ])

    color0, color1 = to_565(c0), to_565(c1)

    # Для DXT3 нужен режим 4 цветов (color0 > color1)
    if color0 < color1:
        color0, color1 = color1, color0

    # Палитру строим из 565 значений (как будет при декомпрессии)
    c0_565 = from_565(color0)
    c1_565 = from_565(color1)
    palette = np.array([c0_565, c1_565, (2.0*c0_565 + c1_565)/3.0, (c0_565 + 2.0*c1_565)/3.0])
    indices = 0
    for i in range(16):
        dists = np.sum((rgb[i] - palette) ** 2, axis=1)
        indices |= (np.argmin(dists) << (i * 2))
    return struct.pack('<HHI', color0, color1, indices)


def compress_dxt3_block(rgba):
    alpha_data = 0
    for i in range(16):
        a4 = int(np.clip(rgba[i, 3] / 255.0 * 15 + 0.5, 0, 15))
        alpha_data |= (a4 << (i * 4))
    alpha_bytes = struct.pack('<Q', alpha_data)
    color_bytes = compress_dxt1_block(rgba[:, :3])
    return alpha_bytes + color_bytes


def compress_miplevel_dxt1(pixels):
    h, w = pixels.shape[:2]
    compressed = bytearray()
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            block = pixels[y:y+4, x:x+4, :3].reshape(16, 3)
            compressed.extend(compress_dxt1_block(block))
    return bytes(compressed)


def compress_miplevel_dxt3(pixels):
    h, w = pixels.shape[:2]
    compressed = bytearray()
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            block = pixels[y:y+4, x:x+4].reshape(16, 4)
            compressed.extend(compress_dxt3_block(block))
    return bytes(compressed)


def create_texture_native(name, image, use_alpha):
    width, height = image.size[0], image.size[1]
    new_w = (width + 3) // 4 * 4
    new_h = (height + 3) // 4 * 4

    pixels = np.array(image.pixels[:]).reshape(height, width, 4)
    pixels = (pixels * 255).astype(np.uint8)
    pixels = np.flipud(pixels)

    if new_w != width or new_h != height:
        padded = np.zeros((new_h, new_w, 4), dtype=np.uint8)
        padded[:height, :width] = pixels
        if width < new_w:
            padded[:height, width:] = pixels[:, -1:, :]
        if height < new_h:
            padded[height:, :] = padded[height-1:height, :]
        pixels = padded
        width, height = new_w, new_h

    mip_levels = []
    current_pixels = pixels
    current_w, current_h = width, height

    while current_w >= 1 and current_h >= 1:
        compress_pixels, _, _ = pad_to_4x4(current_pixels, current_w, current_h)
        if use_alpha:
            compressed = compress_miplevel_dxt3(compress_pixels)
        else:
            compressed = compress_miplevel_dxt1(compress_pixels)
        mip_levels.append(compressed)
        current_pixels, current_w, current_h = downsample_image(current_pixels, current_w, current_h)
        if current_pixels is None:
            break

    if use_alpha:
        dxt_type = 3
        raster_format = RASTER_8888 | RASTER_MIPMAP
        depth = 32
    else:
        dxt_type = 1
        raster_format = RASTER_565 | RASTER_MIPMAP
        depth = 16

    tex_name = name[:31].encode('ascii', errors='replace').ljust(32, b'\x00')
    mip_count = len(mip_levels)
    fourcc = b'DXT1' if dxt_type == 1 else b'DXT3'

    struct_data = bytearray()
    struct_data.extend(struct.pack('<II', PLATFORM_D3D9, make_filter_flags()))
    struct_data.extend(tex_name)
    struct_data.extend(b'\x00' * 32)
    struct_data.extend(struct.pack('<I', raster_format))
    struct_data.extend(fourcc)
    struct_data.extend(struct.pack('<HH', width, height))
    struct_data.extend(struct.pack('<B', depth))
    struct_data.extend(struct.pack('<B', mip_count))
    struct_data.extend(struct.pack('<B', 4))  # raster type
    # D3D format flag: 0x08 для DXT1, 0x09 для DXT3 (с альфой)
    struct_data.extend(struct.pack('<B', 0x09 if use_alpha else 0x08))

    for mip_data in mip_levels:
        struct_data.extend(struct.pack('<I', len(mip_data)))
        struct_data.extend(mip_data)

    tex_native = bytearray()
    write_rw_section_header(tex_native, RW_STRUCT, len(struct_data))
    tex_native.extend(struct_data)
    write_rw_section_header(tex_native, RW_EXTENSION, 0)

    return bytes(tex_native)


def prepare_texture_data(name, image, use_alpha):
    """Prepare texture data in main thread (Blender data access)"""
    width, height = image.size[0], image.size[1]
    pixels = np.array(image.pixels[:]).reshape(height, width, 4)
    pixels = (pixels * 255).astype(np.uint8)
    pixels = np.flipud(pixels)
    return (name, pixels, width, height, use_alpha)


def process_texture_parallel(texture_data):
    """Process prepared texture data (can run in parallel)"""
    name, pixels, width, height, use_alpha = texture_data

    new_w = (width + 3) // 4 * 4
    new_h = (height + 3) // 4 * 4

    if new_w != width or new_h != height:
        padded = np.zeros((new_h, new_w, 4), dtype=np.uint8)
        padded[:height, :width] = pixels
        if width < new_w:
            padded[:height, width:] = pixels[:, -1:, :]
        if height < new_h:
            padded[height:, :] = padded[height-1:height, :]
        pixels = padded
        width, height = new_w, new_h

    mip_levels = []
    current_pixels = pixels
    current_w, current_h = width, height

    while current_w >= 1 and current_h >= 1:
        compress_pixels, _, _ = pad_to_4x4(current_pixels, current_w, current_h)
        if use_alpha:
            compressed = compress_miplevel_dxt3(compress_pixels)
        else:
            compressed = compress_miplevel_dxt1(compress_pixels)
        mip_levels.append(compressed)
        current_pixels, current_w, current_h = downsample_image(current_pixels, current_w, current_h)
        if current_pixels is None:
            break

    if use_alpha:
        dxt_type = 3
        raster_format = RASTER_8888 | RASTER_MIPMAP
        depth = 32
    else:
        dxt_type = 1
        raster_format = RASTER_565 | RASTER_MIPMAP
        depth = 16

    tex_name = name[:31].encode('ascii', errors='replace').ljust(32, b'\x00')
    mip_count = len(mip_levels)
    fourcc = b'DXT1' if dxt_type == 1 else b'DXT3'

    struct_data = bytearray()
    struct_data.extend(struct.pack('<II', PLATFORM_D3D9, make_filter_flags()))
    struct_data.extend(tex_name)
    struct_data.extend(b'\x00' * 32)
    struct_data.extend(struct.pack('<I', raster_format))
    struct_data.extend(fourcc)
    struct_data.extend(struct.pack('<HH', width, height))
    struct_data.extend(struct.pack('<B', depth))
    struct_data.extend(struct.pack('<B', mip_count))
    struct_data.extend(struct.pack('<B', 4))  # raster type
    # D3D format flag: 0x08 для DXT1, 0x09 для DXT3 (с альфой)
    struct_data.extend(struct.pack('<B', 0x09 if use_alpha else 0x08))

    for mip_data in mip_levels:
        struct_data.extend(struct.pack('<I', len(mip_data)))
        struct_data.extend(mip_data)

    tex_native = bytearray()
    write_rw_section_header(tex_native, RW_STRUCT, len(struct_data))
    tex_native.extend(struct_data)
    write_rw_section_header(tex_native, RW_EXTENSION, 0)

    return bytes(tex_native)


def export_txd(filepath, context, selected_only=False, use_gpu=False):
    textures, transparent_list = collect_textures(selected_only)
    if not textures:
        msg = "No textures found on selected objects" if selected_only else "No textures found in scene"
        return {'CANCELLED'}, msg, []

    scene = context.scene
    nvcompress_path = None
    mode_name = "CPU"

    # Проверка GPU режима
    if use_gpu:
        nvtt_path = getattr(scene, 'gtatools_nvtt_path', '')
        available, result = check_nvtt_available(nvtt_path)
        if not available:
            return {'CANCELLED'}, f"GPU режим недоступен: {result}\nУкажите путь к NVIDIA Texture Tools в настройках", []
        nvcompress_path = result
        mode_name = "GPU (NVTT)"

    wm = context.window_manager
    total = len(textures)
    wm.progress_begin(0, total * 2)

    # Разделяем на DXT1 и DXT3 для правильного порядка (DXT3 в конце)
    dxt1_images = []  # (name, image, use_alpha) для GPU
    dxt3_images = []
    dxt1_data = []    # prepared data для CPU
    dxt3_data = []

    skipped_textures = []
    for i, (name, (image, uses_alpha)) in enumerate(textures.items()):
        wm.progress_update(i)

        # Проверка размера - должен быть кратен 4 для DXT
        w, h = image.size[0], image.size[1]
        if w % 4 != 0 or h % 4 != 0:
            print(f"[TXD] ПРОПУСК {name}: размер {w}x{h} не кратен 4 (DXT требует кратность 4)")
            skipped_textures.append(f"{name} ({w}x{h})")
            continue

        print(f"[TXD] {name}: {w}x{h}, uses_alpha={uses_alpha}")
        try:
            if uses_alpha:
                dxt3_images.append((name, image, True))
                if not use_gpu:
                    dxt3_data.append(prepare_texture_data(name, image, True))
            else:
                dxt1_images.append((name, image, False))
                if not use_gpu:
                    dxt1_data.append(prepare_texture_data(name, image, False))
        except Exception as e:
            print(f"TXD PREPARE ERROR: {name}: {e}")

    dxt1_count = len(dxt1_images)
    dxt3_count = len(dxt3_images)

    # Phase 2: Compression
    tex_natives = []

    if use_gpu and nvcompress_path:
        # GPU режим - NVTT для DXT1, CPU для DXT3 (NVTT DXT3 некорректно работает)
        for i, (name, image, _) in enumerate(dxt1_images):
            wm.progress_update(total + i)
            try:
                result = compress_with_nvtt(name, image, False, nvcompress_path)
                if result:
                    tex_natives.append(result)
                else:
                    data = prepare_texture_data(name, image, False)
                    result = process_texture_parallel(data)
                    tex_natives.append(result)
            except Exception as e:
                print(f"TXD GPU ERROR: {name}: {e}")

        # DXT3 через CPU
        for i, (name, image, _) in enumerate(dxt3_images):
            wm.progress_update(total + dxt1_count + i)
            try:
                data = prepare_texture_data(name, image, True)
                result = process_texture_parallel(data)
                tex_natives.append(result)
            except Exception as e:
                print(f"TXD CPU (DXT3) ERROR: {name}: {e}")
    else:
        # CPU режим - обрабатываем в правильном порядке (DXT1 первыми)
        num_workers = min(8, os.cpu_count() or 4)

        # Сначала DXT1
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(process_texture_parallel, data) for data in dxt1_data]
            for i, future in enumerate(futures):
                wm.progress_update(total + i)
                try:
                    result = future.result()
                    tex_natives.append(result)
                except Exception as e:
                    print(f"TXD CPU ERROR: {e}")

        # Потом DXT3
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(process_texture_parallel, data) for data in dxt3_data]
            for i, future in enumerate(futures):
                wm.progress_update(total + dxt1_count + i)
                try:
                    result = future.result()
                    tex_natives.append(result)
                except Exception as e:
                    print(f"TXD CPU ERROR: {e}")

    wm.progress_end()

    if not tex_natives:
        return {'CANCELLED'}, "No textures could be processed", []

    tex_natives_data = bytearray()
    for tex_native in tex_natives:
        write_rw_section_header(tex_natives_data, RW_TEXTURENATIVE, len(tex_native))
        tex_natives_data.extend(tex_native)

    struct_section = bytearray()
    dict_struct = struct.pack('<HH', len(tex_natives), 0)
    write_rw_section_header(struct_section, RW_STRUCT, len(dict_struct))
    struct_section.extend(dict_struct)

    extension_data = bytearray()
    write_rw_section_header(extension_data, RW_EXTENSION, 0)

    with open(filepath, 'wb') as f:
        content_size = len(struct_section) + len(tex_natives_data) + len(extension_data)
        f.write(struct.pack('<III', RW_TEXDICTIONARY, content_size, RW_VERSION))
        f.write(struct_section)
        f.write(tex_natives_data)
        f.write(extension_data)

    msg = f"Exported {dxt1_count} DXT1 + {dxt3_count} DXT3 ({mode_name})"
    if skipped_textures:
        msg += f"\nПРОПУЩЕНО (размер не кратен 4): {', '.join(skipped_textures)}"
    return {'FINISHED'}, msg, transparent_list


# =============================================================================
# GTA MODEL EXPORT (DFF, COL, LOD, TXD)
# =============================================================================

def get_model_type(obj):
    """Determine model type by suffix: LOD, COL, DFF at end of name"""
    if obj is None:
        return None, None

    name = obj.name
    name_upper = name.upper()

    # Проверяем LOD (поддержка: _lod, .lod, LOD, lod)
    if name_upper.endswith('_LOD') or name_upper.endswith('.LOD'):
        return 'LOD', name[:-4]
    if name_upper.endswith('LOD'):
        return 'LOD', name[:-3]

    # Проверяем COL (поддержка: _col, .col, COL, col)
    if name_upper.endswith('_COL') or name_upper.endswith('.COL'):
        return 'COL', name[:-4]
    if name_upper.endswith('COL'):
        return 'COL', name[:-3]

    # Проверяем DFF (поддержка: _dff, .dff, DFF, dff)
    if name_upper.endswith('_DFF') or name_upper.endswith('.DFF'):
        return 'DFF', name[:-4]
    if name_upper.endswith('DFF'):
        return 'DFF', name[:-3]

    # Модель без суффикса - считается DFF
    return 'DFF', name


def find_related_models(base_name):
    """Find related models (DFF, LOD, COL) by base name"""
    models = {
        'DFF': None,
        'LOD': None,
        'COL': None
    }

    base_upper = base_name.upper()

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        name_upper = obj.name.upper()

        # Проверяем DFF (base, base_dff, baseDFF)
        if name_upper == base_upper:
            models['DFF'] = obj
        elif name_upper == base_upper + '_DFF' or name_upper == base_upper + 'DFF':
            models['DFF'] = obj

        # Проверяем LOD (base_lod, baseLOD)
        if name_upper == base_upper + '_LOD' or name_upper == base_upper + 'LOD':
            models['LOD'] = obj

        # Проверяем COL (base_col, baseCOL)
        if name_upper == base_upper + '_COL' or name_upper == base_upper + 'COL':
            models['COL'] = obj

    return models


def find_selected_models():
    """Find DFF, LOD, COL models only among selected objects"""
    models = {
        'DFF': None,
        'LOD': None,
        'COL': None
    }

    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue

        model_type, base_name = get_model_type(obj)

        if model_type and models[model_type] is None:
            models[model_type] = obj

    return models


def find_all_selected_model_groups():
    """Find all DFF/LOD/COL model groups among selected objects, grouped by base_name"""
    groups = {}  # {base_name: {'DFF': obj, 'LOD': obj, 'COL': obj}}

    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue

        model_type, base_name = get_model_type(obj)
        if not base_name:
            continue

        # Нормализуем base_name (убираем _ в конце если есть)
        base_name_clean = base_name.rstrip('_')

        if base_name_clean not in groups:
            groups[base_name_clean] = {'DFF': None, 'LOD': None, 'COL': None}

        if model_type and groups[base_name_clean][model_type] is None:
            groups[base_name_clean][model_type] = obj

    return groups


def get_base_name_from_selected():
    """Get base name from selected models"""
    models = find_selected_models()

    # Берём имя из первой найденной модели
    if models['DFF']:
        _, base_name = get_model_type(models['DFF'])
        return base_name
    elif models['LOD']:
        _, base_name = get_model_type(models['LOD'])
        return base_name
    elif models['COL']:
        _, base_name = get_model_type(models['COL'])
        return base_name

    return None


def fix_col_model_name(col_path, model_name):
    """
    Исправить имя модели внутри COL файла после экспорта.

    Структура COL заголовка:
    - Offset 0-3: Magic (COLL/COL2/COL3/COL4)
    - Offset 4-7: File size (uint32)
    - Offset 8-29: Model name (22 bytes, null-terminated)
    - Offset 30-31: Model ID (uint16)

    Args:
        col_path: Путь к COL файлу
        model_name: Имя модели для записи (без расширения .col)

    Returns:
        True если успешно, False если ошибка
    """
    try:
        # Читаем файл
        with open(col_path, 'rb') as f:
            data = bytearray(f.read())

        if len(data) < 32:
            return False

        # Проверяем что это COL файл
        magic = data[0:4]
        if magic not in (b'COLL', b'COL2', b'COL3', b'COL4'):
            return False

        # Убираем расширение .col если есть
        if model_name.lower().endswith('.col'):
            model_name = model_name[:-4]

        # Кодируем имя модели (макс 21 символ + null terminator)
        # Пробуем ASCII, если не получается - используем latin-1 с заменой
        try:
            name_bytes = model_name.encode('ascii')
        except UnicodeEncodeError:
            # Для кириллицы и других символов - транслитерация или замена
            name_bytes = model_name.encode('latin-1', errors='replace')

        # Обрезаем до 21 байта (22-й = null terminator)
        name_bytes = name_bytes[:21]

        # Дополняем нулями до 22 байт
        name_bytes = name_bytes.ljust(22, b'\x00')

        # Записываем имя модели в заголовок (offset 8)
        data[8:30] = name_bytes

        # Сохраняем файл
        with open(col_path, 'wb') as f:
            f.write(data)

        return True

    except Exception as e:
        print(f"fix_col_model_name error: {e}")
        return False


def get_base_name_from_selection():
    """Get base model name from selected object"""
    obj = bpy.context.active_object
    if obj is None:
        return None

    model_type, base_name = get_model_type(obj)
    return base_name


def get_model_textures(obj):
    """Get all textures used by object's materials"""
    textures = []

    if obj is None or obj.type != 'MESH':
        return textures

    for mat_slot in obj.material_slots:
        mat = mat_slot.material
        if not mat or not mat.use_nodes:
            continue

        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                if node.image not in textures:
                    textures.append(node.image)

    return textures


# =============================================================================
# PRELIGHT
# =============================================================================

class GTASAPrelight:
    def __init__(self, obj, split_angle=90.0, normal_threshold=0.1,
                 top_color=(1.0, 1.0, 1.0), bottom_color=(0.3, 0.3, 0.3),
                 ambient_color=(0.5, 0.5, 0.5)):
        self.obj = obj
        self.split_angle = math.radians(split_angle)
        self.normal_threshold = normal_threshold
        self.top_color = top_color
        self.bottom_color = bottom_color
        self.ambient_color = ambient_color

    def are_faces_coplanar(self, face1, face2, angle_threshold=0.01):
        dot = abs(face1.normal.dot(face2.normal))
        return dot > (1.0 - angle_threshold)

    def split_by_angle(self):
        bpy.context.view_layer.objects.active = self.obj
        self.obj.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT')

        mesh = self.obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        for edge in bm.edges:
            edge.smooth = True

        sharp_count = 0
        for edge in bm.edges:
            if len(edge.link_faces) != 2:
                continue
            face1, face2 = edge.link_faces[0], edge.link_faces[1]
            if self.are_faces_coplanar(face1, face2):
                continue
            dot = face1.normal.dot(face2.normal)
            dot = max(-1.0, min(1.0, dot))
            angle = math.acos(dot)
            if angle >= self.split_angle:
                edge.smooth = False
                sharp_count += 1

        bm.to_mesh(mesh)
        bm.free()

        edge_split = self.obj.modifiers.new(name="EdgeSplit_Prelight", type='EDGE_SPLIT')
        edge_split.use_edge_angle = False
        edge_split.use_edge_sharp = True
        bpy.ops.object.modifier_apply(modifier=edge_split.name)

    def group_coplanar_faces(self, bm, normal_threshold=0.01):
        face_groups = []
        processed = set()

        for start_face in bm.faces:
            if start_face.index in processed:
                continue
            group = []
            queue = [start_face]
            while queue:
                face = queue.pop(0)
                if face.index in processed:
                    continue
                processed.add(face.index)
                group.append(face.index)
                for edge in face.edges:
                    for linked_face in edge.link_faces:
                        if linked_face.index in processed:
                            continue
                        dot = abs(face.normal.dot(linked_face.normal))
                        if dot > (1.0 - normal_threshold):
                            queue.append(linked_face)
            if group:
                avg_normal = Vector((0, 0, 0))
                for face_idx in group:
                    avg_normal += bm.faces[face_idx].normal
                avg_normal.normalize()
                face_groups.append((avg_normal, group))
        return face_groups

    def lerp_color(self, color1, color2, factor):
        return tuple(c1 + (c2 - c1) * factor for c1, c2 in zip(color1, color2))

    def apply_vertex_colors(self):
        mesh = self.obj.data

        if "Prelight" not in mesh.color_attributes:
            color_layer = mesh.color_attributes.new(name="Prelight", type='BYTE_COLOR', domain='CORNER')
        else:
            color_layer = mesh.color_attributes["Prelight"]

        mesh.color_attributes.active_color = color_layer

        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()

        face_groups = self.group_coplanar_faces(bm)

        global_z_min = min(v.co.z for v in bm.verts)
        global_z_max = max(v.co.z for v in bm.verts)
        z_range = global_z_max - global_z_min if global_z_max != global_z_min else 1.0

        loop_colors = {}

        for group_normal, face_indices in face_groups:
            normal_z = group_normal.z
            group_colors = []

            for face_idx in face_indices:
                face = bm.faces[face_idx]
                for loop in face.loops:
                    vert = loop.vert
                    z_factor = (vert.co.z - global_z_min) / z_range

                    if normal_z > 0.3:
                        base_color = self.lerp_color(self.bottom_color, self.top_color, z_factor)
                        brightness = 0.1 + 0.2 * normal_z
                        color = tuple(min(1.0, c + brightness) for c in base_color)
                    elif normal_z < -0.3:
                        darkness = 0.3 * abs(normal_z)
                        base_color = self.lerp_color(self.bottom_color, self.ambient_color, z_factor * 0.5)
                        color = tuple(max(0.0, c - darkness) for c in base_color)
                    else:
                        color = self.lerp_color(self.bottom_color, self.ambient_color, z_factor)

                    group_colors.append(color)

            if group_colors:
                avg_color = (
                    sum(c[0] for c in group_colors) / len(group_colors),
                    sum(c[1] for c in group_colors) / len(group_colors),
                    sum(c[2] for c in group_colors) / len(group_colors)
                )
                for face_idx in face_indices:
                    face = bm.faces[face_idx]
                    for loop in face.loops:
                        loop_colors[loop.index] = avg_color

        bm.free()

        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                if loop_idx in loop_colors:
                    color = loop_colors[loop_idx]
                    color_layer.data[loop_idx].color = (color[0], color[1], color[2], 1.0)

    def run(self):
        self.split_by_angle()
        self.apply_vertex_colors()


def average_colors_on_coplanar_faces(obj, normal_threshold=0.01):
    if obj is None or obj.type != 'MESH':
        return False

    mesh = obj.data
    if not mesh.color_attributes:
        return False

    color_layer = mesh.color_attributes.active_color
    if color_layer is None:
        color_layer = mesh.color_attributes[0]

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    face_groups = []
    processed = set()

    for start_face in bm.faces:
        if start_face.index in processed:
            continue
        group = []
        queue = [start_face]
        while queue:
            face = queue.pop(0)
            if face.index in processed:
                continue
            processed.add(face.index)
            group.append(face.index)
            for edge in face.edges:
                for linked_face in edge.link_faces:
                    if linked_face.index in processed:
                        continue
                    dot = abs(face.normal.dot(linked_face.normal))
                    if dot > (1.0 - normal_threshold):
                        queue.append(linked_face)
        if group:
            face_groups.append(group)

    bm.free()

    for group in face_groups:
        group_loops = []
        for face_idx in group:
            poly = mesh.polygons[face_idx]
            group_loops.extend(poly.loop_indices)

        if not group_loops:
            continue

        colors = []
        for loop_idx in group_loops:
            c = color_layer.data[loop_idx].color
            colors.append((c[0], c[1], c[2]))

        avg_color = (
            sum(c[0] for c in colors) / len(colors),
            sum(c[1] for c in colors) / len(colors),
            sum(c[2] for c in colors) / len(colors)
        )

        for loop_idx in group_loops:
            color_layer.data[loop_idx].color = (avg_color[0], avg_color[1], avg_color[2], 1.0)

    return True


# =============================================================================
# UV2 TO VERTEX COLOR
# =============================================================================

def encode_uv2_to_color_16bit(obj):
    if not obj or obj.type != 'MESH':
        return False, "Select a mesh!"

    mesh = obj.data

    if len(mesh.uv_layers) < 2:
        return False, "Need 2 UV layers!"

    uv_layer = mesh.uv_layers[1]

    color_name = "UV2_Color"
    if color_name in mesh.color_attributes:
        mesh.color_attributes.remove(mesh.color_attributes[color_name])

    color_attr = mesh.color_attributes.new(name=color_name, type='BYTE_COLOR', domain='CORNER')
    mesh.color_attributes.active_color = color_attr

    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            uv = uv_layer.data[loop_idx].uv
            u = max(0.0, min(1.0, uv[0]))
            v = max(0.0, min(1.0, uv[1]))

            u_16 = int(u * 65535)
            v_16 = int(v * 65535)

            r = (u_16 >> 8) / 255.0
            g = (u_16 & 0xFF) / 255.0
            b = (v_16 >> 8) / 255.0
            a = (v_16 & 0xFF) / 255.0

            color_attr.data[loop_idx].color = (r, g, b, a)

    return True, f"Encoded {len(mesh.polygons)} faces"


# =============================================================================
# PRELIGHT SCENE LIGHTS
# =============================================================================

def create_prelight_scene_lights(center, distance=100.0):
    """Create 8 lights around selected object center for GTA SA prelight baking"""

    # Color #BCBCBC = RGB(188, 188, 188) = (0.737, 0.737, 0.737)
    light_color = (0.737, 0.737, 0.737)

    cx, cy, cz = center

    # Light positions and intensities
    # Format: (name, offset (x, y, z), intensity)
    # Right = +X, Left = -X, Front = +Y, Back = -Y, Up = +Z, Down = -Z
    lights_config = [
        ("Prelight_TopRightBack",    ( distance,  -distance,  distance), 11),
        ("Prelight_BottomRightBack", ( distance,  -distance, -distance), 8),
        ("Prelight_TopLeftBack",     (-distance,  -distance,  distance), 10),
        ("Prelight_BottomLeftBack",  (-distance,  -distance, -distance), 7),
        ("Prelight_TopRightFront",   ( distance,   distance,  distance), 11),
        ("Prelight_BottomRightFront",( distance,   distance, -distance), 11),
        ("Prelight_TopLeftFront",    (-distance,   distance,  distance), 9),
        ("Prelight_BottomLeftFront", (-distance,   distance, -distance), 7),
    ]

    created_lights = []

    # Create collection for lights
    collection_name = "Prelight_Lights"
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        # Remove existing lights in collection
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)

    for name, offset, intensity in lights_config:
        # Create light data
        light_data = bpy.data.lights.new(name=name, type='POINT')
        light_data.color = light_color
        light_data.energy = intensity

        # Create light object with position relative to object center
        light_obj = bpy.data.objects.new(name=name, object_data=light_data)
        light_obj.location = (cx + offset[0], cy + offset[1], cz + offset[2])

        # Link to collection
        collection.objects.link(light_obj)
        created_lights.append(name)

    return created_lights


def remove_prelight_scene_lights():
    """Remove all prelight scene lights"""
    collection_name = "Prelight_Lights"
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
        return True
    return False


def bake_vertex_colors_from_lights(obj, use_shadows=True):
    """Bake lighting from Point lights to vertex colors"""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    # Collect all point lights in scene
    lights = []
    for light_obj in bpy.data.objects:
        if light_obj.type == 'LIGHT' and light_obj.data.type == 'POINT':
            lights.append(light_obj)

    if not lights:
        return False, "No Point lights in scene!"

    mesh = obj.data

    # Create or get vertex color layer
    color_name = "BakedLight"
    if color_name in mesh.color_attributes:
        mesh.color_attributes.remove(mesh.color_attributes[color_name])

    color_attr = mesh.color_attributes.new(name=color_name, type='BYTE_COLOR', domain='CORNER')
    mesh.color_attributes.active_color = color_attr

    # Get world matrix
    world_matrix = obj.matrix_world
    normal_matrix = world_matrix.to_3x3().inverted().transposed()

    # Prepare depsgraph for raycasting
    depsgraph = bpy.context.evaluated_depsgraph_get()

    # Process each polygon
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vert = mesh.vertices[loop.vertex_index]

            # World space position and normal
            world_pos = world_matrix @ vert.co
            world_normal = (normal_matrix @ poly.normal).normalized()

            # Calculate lighting from all lights
            total_light = Vector((0.0, 0.0, 0.0))

            for light_obj in lights:
                light = light_obj.data
                light_pos = light_obj.location

                # Direction from vertex to light
                light_dir = light_pos - world_pos
                distance = light_dir.length

                if distance < 0.001:
                    continue

                light_dir_normalized = light_dir / distance

                # Lambertian diffuse
                n_dot_l = max(0.0, world_normal.dot(light_dir_normalized))

                if n_dot_l <= 0:
                    continue

                # Shadow check with raycast
                shadow = 1.0
                if use_shadows:
                    # Offset start position slightly along normal to avoid self-intersection
                    ray_start = world_pos + world_normal * 0.01
                    result, location, normal, index, hit_obj, matrix = bpy.context.scene.ray_cast(
                        depsgraph, ray_start, light_dir_normalized, distance=distance - 0.02
                    )
                    if result and hit_obj != obj:
                        shadow = 0.0

                # Light attenuation (inverse square with minimum)
                attenuation = 1.0 / (1.0 + distance * 0.01 + distance * distance * 0.0001)

                # Light intensity and color
                intensity = light.energy * attenuation * n_dot_l * shadow
                light_color = Vector(light.color) * intensity

                total_light += light_color

            # Clamp and set color
            r = min(1.0, max(0.0, total_light.x))
            g = min(1.0, max(0.0, total_light.y))
            b = min(1.0, max(0.0, total_light.z))

            color_attr.data[loop_idx].color = (r, g, b, 1.0)

    return True, f"Baked lighting from {len(lights)} lights"


def bake_vertex_colors_simple(obj, ambient=0.05, intensity_mult=0.008, gamma=1.8):
    """Simple vertex color baking from Point lights (no shadows, faster)"""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    # Collect all point lights
    lights = []
    for light_obj in bpy.data.objects:
        if light_obj.type == 'LIGHT' and light_obj.data.type == 'POINT':
            lights.append(light_obj)

    if not lights:
        return False, "No Point lights in scene!"

    mesh = obj.data

    # Use active color attribute or create one if none exists
    color_attr = mesh.color_attributes.active_color
    if color_attr is None:
        if len(mesh.color_attributes) > 0:
            color_attr = mesh.color_attributes[0]
        else:
            color_attr = mesh.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
        mesh.color_attributes.active_color = color_attr

    color_name = color_attr.name

    world_matrix = obj.matrix_world
    normal_matrix = world_matrix.to_3x3().inverted().transposed()

    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            loop = mesh.loops[loop_idx]
            vert = mesh.vertices[loop.vertex_index]

            world_pos = world_matrix @ vert.co
            world_normal = (normal_matrix @ poly.normal).normalized()

            # Start with ambient
            total_light = Vector((ambient, ambient, ambient))

            for light_obj in lights:
                light = light_obj.data
                light_pos = light_obj.location

                light_dir = light_pos - world_pos
                distance = light_dir.length

                if distance < 0.001:
                    continue

                light_dir_normalized = light_dir / distance
                n_dot_l = max(0.0, world_normal.dot(light_dir_normalized))

                if n_dot_l <= 0:
                    continue

                # 3Ds Max style attenuation (inverse square law)
                attenuation = 1.0 / (1.0 + distance * distance * 0.0001)
                intensity = light.energy * attenuation * n_dot_l * intensity_mult
                light_color = Vector(light.color) * intensity

                total_light += light_color

            # Apply gamma correction for 3Ds Max-like result
            r = min(1.0, max(0.0, pow(total_light.x, 1.0 / gamma)))
            g = min(1.0, max(0.0, pow(total_light.y, 1.0 / gamma)))
            b = min(1.0, max(0.0, pow(total_light.z, 1.0 / gamma)))

            color_attr.data[loop_idx].color = (r, g, b, 1.0)

    return True, f"Baked to '{color_name}' from {len(lights)} lights"


def apply_brightness_offset(obj, v_offset):
    """Apply V (brightness) offset to vertex colors like 3Ds Max Adjust Color

    In 3Ds Max, V offset works as percentage:
    - V = -80 means keep 20% of brightness (multiply by 0.2)
    - V = +50 means increase brightness by 50% (multiply by 1.5)

    Tracks current V offset to allow adjusting in any direction.
    """
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    if not mesh.color_attributes:
        return False, "No vertex colors found!"

    color_attr = mesh.color_attributes.active_color
    if color_attr is None:
        return False, "No active color layer!"

    # Get current V offset stored on the layer (default 0 = no offset applied yet)
    prop_name = f"v_offset_{color_attr.name}"
    current_v = obj.get(prop_name, 0.0)

    # Calculate multipliers
    # V=-80 -> multiplier 0.2, V=0 -> multiplier 1.0, V=+50 -> multiplier 1.5
    current_mult = 1.0 + (current_v / 100.0)
    target_mult = 1.0 + (v_offset / 100.0)

    current_mult = max(0.001, current_mult)  # Avoid division by zero
    target_mult = max(0.0, target_mult)

    # Calculate conversion multiplier (from current state to target state)
    conversion = target_mult / current_mult

    # Apply conversion to all vertex colors
    for i, data in enumerate(color_attr.data):
        c = data.color
        r = min(1.0, max(0.0, c[0] * conversion))
        g = min(1.0, max(0.0, c[1] * conversion))
        b = min(1.0, max(0.0, c[2] * conversion))
        color_attr.data[i].color = (r, g, b, c[3])

    # Store the new V offset
    obj[prop_name] = v_offset

    return True, f"V: {current_v:.0f} → {v_offset:.0f} (x{conversion:.2f})"


def analyze_vertex_colors(obj):
    """Analyze vertex colors from object to understand lighting values"""
    if obj is None or obj.type != 'MESH':
        return None

    mesh = obj.data
    if not mesh.color_attributes:
        return None

    color_attr = mesh.color_attributes.active_color
    if color_attr is None and len(mesh.color_attributes) > 0:
        color_attr = mesh.color_attributes[0]

    if color_attr is None:
        return None

    # Collect all colors
    colors = []
    for data in color_attr.data:
        c = data.color
        brightness = (c[0] + c[1] + c[2]) / 3.0
        colors.append({
            'r': c[0], 'g': c[1], 'b': c[2],
            'brightness': brightness
        })

    if not colors:
        return None

    # Calculate statistics
    brightnesses = [c['brightness'] for c in colors]
    min_bright = min(brightnesses)
    max_bright = max(brightnesses)
    avg_bright = sum(brightnesses) / len(brightnesses)

    return {
        'count': len(colors),
        'min_brightness': min_bright,
        'max_brightness': max_bright,
        'avg_brightness': avg_bright,
        'layer_name': color_attr.name
    }


def setup_prelight_preview(obj, enable=True):
    """Setup materials to show vertex colors multiplied with textures in Material Preview

    Adds a Vertex Color node and MixRGB (Multiply) between texture and shader.
    """
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    if not mesh.color_attributes:
        return False, "No vertex colors on object!"

    # Get active color attribute name
    color_attr = mesh.color_attributes.active_color
    if color_attr is None:
        color_attr = mesh.color_attributes[0]
    color_name = color_attr.name

    modified_count = 0

    for mat_slot in obj.material_slots:
        mat = mat_slot.material
        if not mat or not mat.use_nodes:
            continue

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Find existing prelight nodes
        vc_node = nodes.get("Prelight_VertexColor")
        mix_node = nodes.get("Prelight_Mix")
        bright_node = nodes.get("Prelight_Bright")

        if enable:
            # Find the Principled BSDF and texture connected to Base Color
            principled = None
            tex_node = None
            original_link = None

            for node in nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled = node
                    break

            if not principled:
                continue

            # Get what's connected to Base Color
            base_color_input = principled.inputs.get('Base Color')
            if base_color_input and base_color_input.is_linked:
                original_link = base_color_input.links[0]
                tex_node = original_link.from_node
                tex_output = original_link.from_socket

            # If already has prelight setup - just update values
            if mix_node and vc_node and bright_node:
                vc_node.layer_name = color_name
                bright_node.inputs['B'].default_value = (0.0, 0.0, 0.0, 0.0)
                continue

            # Create Vertex Color node
            if not vc_node:
                vc_node = nodes.new('ShaderNodeVertexColor')
                vc_node.name = "Prelight_VertexColor"
                vc_node.label = "Prelight"
                vc_node.location = (principled.location.x - 500, principled.location.y - 200)
            vc_node.layer_name = color_name

            # Create Brightness node (+ brightness offset)
            if not bright_node:
                bright_node = nodes.new('ShaderNodeMix')
                bright_node.name = "Prelight_Bright"
                bright_node.label = "Brightness"
                bright_node.data_type = 'RGBA'
                bright_node.blend_type = 'ADD'
                bright_node.location = (principled.location.x - 350, principled.location.y - 200)
                bright_node.inputs['Factor'].default_value = 1.0
            bright_node.inputs['B'].default_value = (0.0, 0.0, 0.0, 0.0)

            # Create Mix node (Multiply with texture)
            if not mix_node:
                mix_node = nodes.new('ShaderNodeMix')
                mix_node.name = "Prelight_Mix"
                mix_node.label = "Prelight Multiply"
                mix_node.data_type = 'RGBA'
                mix_node.blend_type = 'MULTIPLY'
                mix_node.location = (principled.location.x - 200, principled.location.y)
                mix_node.inputs['Factor'].default_value = 1.0

            # Connect nodes
            if tex_node and original_link:
                # Texture -> Mix A
                links.new(tex_output, mix_node.inputs['A'])
            else:
                # No texture - use white
                mix_node.inputs['A'].default_value = (1, 1, 1, 1)

            # Vertex Color -> Bright A
            links.new(vc_node.outputs['Color'], bright_node.inputs['A'])

            # Bright Result -> Mix B
            links.new(bright_node.outputs['Result'], mix_node.inputs['B'])

            # Mix -> Base Color
            links.new(mix_node.outputs['Result'], base_color_input)

            modified_count += 1

        else:
            # Disable - remove prelight nodes and restore original connection
            if mix_node:
                # Find what was connected to Mix A input (original texture or Lightmap_Mix)
                mix_a_input = mix_node.inputs.get('A')
                original_source = None
                original_socket = None

                if mix_a_input and mix_a_input.is_linked:
                    original_source = mix_a_input.links[0].from_node
                    original_socket = mix_a_input.links[0].from_socket

                # Find Principled BSDF
                principled = None
                for node in nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        principled = node
                        break

                if principled:
                    base_color_input = principled.inputs.get('Base Color')
                    # Restore connection - может быть Lightmap_Mix или оригинальная текстура
                    if original_source and original_socket:
                        links.new(original_socket, base_color_input)

                # Remove prelight nodes
                nodes.remove(mix_node)
                modified_count += 1

            if bright_node:
                nodes.remove(bright_node)

            if vc_node:
                nodes.remove(vc_node)

    if enable:
        return True, f"Prelight preview enabled on {modified_count} materials"
    else:
        return True, f"Prelight preview disabled on {modified_count} materials"


def fill_selected_faces(obj, color):
    """Fill selected faces with a color in vertex paint mode"""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    mesh = obj.data
    if not mesh.color_attributes:
        return False, "No vertex colors found!"

    color_attr = mesh.color_attributes.active_color
    if color_attr is None:
        return False, "No active color layer!"

    # Get selected faces from bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]

    if not selected_faces:
        bm.free()
        return False, "No faces selected!"

    # Get selected face indices
    selected_indices = set(f.index for f in selected_faces)
    bm.free()

    # Fill selected faces with color
    filled_count = 0
    for poly in mesh.polygons:
        if poly.index in selected_indices:
            for loop_idx in poly.loop_indices:
                color_attr.data[loop_idx].color = (color[0], color[1], color[2], 1.0)
            filled_count += 1

    return True, f"Filled {filled_count} faces"


# =============================================================================
# НОВАЯ АРХИТЕКТУРА СЛОЁВ
# =============================================================================
# Формула: ИТОГ = (База ИЛИ Fill) + Σ Scatter
#
# База — исходный цвет вершин, неизменный
# Fill — заменяет базу локально (не складывается)
# Scatter — дельта, всегда прибавляется
# =============================================================================

# Исходные цвета вершин (сохраняются при первой операции, никогда не меняются)
# Structure: {obj_name: {loop_idx: (r,g,b,a), ...}}
_base_colors = {}

# Fill слои - заменяют базу для своих loops
# Structure: {obj_name: {loop_idx: (r,g,b,a), ...}}
_fill_layers = {}

# Scatter слои - дельты которые прибавляются
# Structure: {obj_name: {color_tuple: {level_num: {loop_idx: (dr,dg,db,da), ...}, ...}, ...}}
_scatter_layers = {}


def ensure_base_colors(obj):
    """Save base colors if not saved yet"""
    if obj is None or obj.type != 'MESH':
        return False

    obj_key = obj.name
    if obj_key in _base_colors:
        return True  # Уже сохранены

    mesh = obj.data
    if not mesh.color_attributes or not mesh.color_attributes.active_color:
        return False

    color_attr = mesh.color_attributes.active_color

    _base_colors[obj_key] = {}
    for loop_idx in range(len(color_attr.data)):
        c = color_attr.data[loop_idx].color
        _base_colors[obj_key][loop_idx] = (c[0], c[1], c[2], c[3])

    return True


def recalculate_loop_color(obj_key, loop_idx):
    """Recalculate color of one loop: RESULT = (Base OR Fill) + Σ Scatter"""
    # Получаем базу
    if obj_key not in _base_colors or loop_idx not in _base_colors[obj_key]:
        return None

    base = _base_colors[obj_key][loop_idx]

    # Проверяем есть ли Fill для этого loop
    fill = None
    if obj_key in _fill_layers and loop_idx in _fill_layers[obj_key]:
        fill = _fill_layers[obj_key][loop_idx]

    # Основа = Fill если есть, иначе База
    r, g, b, a = fill if fill else base

    # Добавляем все Scatter дельты
    if obj_key in _scatter_layers:
        for color_tuple, levels in _scatter_layers[obj_key].items():
            for level_num, deltas in levels.items():
                if loop_idx in deltas:
                    dr, dg, db, da = deltas[loop_idx]
                    r += dr
                    g += dg
                    b += db

    # Clamp to [0, 1]
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    a = max(0.0, min(1.0, a))

    return (r, g, b, a)


def recalculate_colors(obj, loop_indices=None):
    """Recalculate colors for specified loops (or all if not specified)"""
    if obj is None or obj.type != 'MESH':
        return False

    obj_key = obj.name
    mesh = obj.data

    if not mesh.color_attributes or not mesh.color_attributes.active_color:
        return False

    color_attr = mesh.color_attributes.active_color

    # Если loops не указаны - пересчитать все
    if loop_indices is None:
        loop_indices = range(len(color_attr.data))

    for loop_idx in loop_indices:
        new_color = recalculate_loop_color(obj_key, loop_idx)
        if new_color and loop_idx < len(color_attr.data):
            color_attr.data[loop_idx].color = new_color

    return True


def add_fill_layer(obj, color, loop_indices):
    """Add Fill layer for specified loops"""
    if obj is None:
        return False

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    # Сохраняем базу если ещё не сохранена
    ensure_base_colors(obj)

    # Инициализируем хранилище
    if obj_key not in _fill_layers:
        _fill_layers[obj_key] = {}

    # Записываем Fill цвет для каждого loop
    for loop_idx in loop_indices:
        _fill_layers[obj_key][loop_idx] = (color[0], color[1], color[2], 1.0)

    # Добавляем в UI список если новый цвет
    color_exists = False
    for item in obj.gtatools_fill_colors:
        existing = (round(item.color[0], 3), round(item.color[1], 3), round(item.color[2], 3))
        if existing == color_tuple:
            color_exists = True
            break

    if not color_exists:
        new_item = obj.gtatools_fill_colors.add()
        new_item.color = color_tuple

    return True


def add_scatter_layer(obj, color, deltas):
    """Добавить Scatter слой (дельты) для цвета
    deltas = {loop_idx: (dr, dg, db, da), ...}
    """
    if obj is None or not deltas:
        return -1

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    # Сохраняем базу если ещё не сохранена
    ensure_base_colors(obj)

    # Инициализируем хранилище
    if obj_key not in _scatter_layers:
        _scatter_layers[obj_key] = {}
    if color_tuple not in _scatter_layers[obj_key]:
        _scatter_layers[obj_key][color_tuple] = {}

    # Находим следующий номер уровня
    existing_levels = list(_scatter_layers[obj_key][color_tuple].keys())
    next_level = max(existing_levels) + 1 if existing_levels else 1

    # Сохраняем дельты
    _scatter_layers[obj_key][color_tuple][next_level] = deltas

    return next_level


def get_scatter_levels(obj, color):
    """Get list of scatter levels for color"""
    if obj is None:
        return []

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    if obj_key not in _scatter_layers:
        return []
    if color_tuple not in _scatter_layers[obj_key]:
        return []

    return sorted(_scatter_layers[obj_key][color_tuple].keys())


def remove_scatter_layer(obj, color, level):
    """Delete Scatter layer and recalculate colors"""
    if obj is None:
        return False, "No object"

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    if obj_key not in _scatter_layers:
        return False, "No scatter layers"
    if color_tuple not in _scatter_layers[obj_key]:
        return False, "No scatter layers for this color"
    if level not in _scatter_layers[obj_key][color_tuple]:
        return False, f"Level {level} not found"

    # Получаем loops которые были затронуты этим слоем
    affected_loops = list(_scatter_layers[obj_key][color_tuple][level].keys())

    # Удаляем слой
    del _scatter_layers[obj_key][color_tuple][level]

    # Пересчитываем цвета для затронутых loops
    recalculate_colors(obj, affected_loops)

    return True, f"Level {level} removed"


def clear_scatter_layers(obj, color):
    """Delete all Scatter layers for color and recalculate"""
    if obj is None:
        return False, "No object"

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    if obj_key not in _scatter_layers:
        return False, "No scatter layers"
    if color_tuple not in _scatter_layers[obj_key]:
        return False, "No scatter layers for this color"

    # Собираем все затронутые loops
    affected_loops = set()
    for level_data in _scatter_layers[obj_key][color_tuple].values():
        affected_loops.update(level_data.keys())

    # Удаляем все слои
    _scatter_layers[obj_key][color_tuple] = {}

    # Пересчитываем цвета
    recalculate_colors(obj, affected_loops)

    return True, "All scatter levels removed"


def remove_fill_color(obj, color):
    """Delete Fill color and all its Scatter layers, recalculate"""
    if obj is None:
        return False, "No object"

    obj_key = obj.name
    color_tuple = (round(color[0], 3), round(color[1], 3), round(color[2], 3))

    affected_loops = set()

    # Собираем loops из Fill
    if obj_key in _fill_layers:
        for loop_idx, fill_color in list(_fill_layers[obj_key].items()):
            fill_tuple = (round(fill_color[0], 3), round(fill_color[1], 3), round(fill_color[2], 3))
            if fill_tuple == color_tuple:
                affected_loops.add(loop_idx)
                del _fill_layers[obj_key][loop_idx]

    # Собираем loops из Scatter и удаляем
    if obj_key in _scatter_layers:
        if color_tuple in _scatter_layers[obj_key]:
            for level_data in _scatter_layers[obj_key][color_tuple].values():
                affected_loops.update(level_data.keys())
            del _scatter_layers[obj_key][color_tuple]

    # Пересчитываем цвета
    if affected_loops:
        recalculate_colors(obj, affected_loops)

    return True, "Fill color removed"


def remove_fill_color_by_index(obj, index):
    """Delete color from list by index"""
    if obj is None:
        return False, "No object"

    if not (0 <= index < len(obj.gtatools_fill_colors)):
        return False, "Invalid index"

    # Получаем цвет
    color_item = obj.gtatools_fill_colors[index]
    color_tuple = (color_item.color[0], color_item.color[1], color_item.color[2])

    # Удаляем цвет и пересчитываем
    remove_fill_color(obj, color_tuple)

    # Удаляем из UI списка
    obj.gtatools_fill_colors.remove(index)

    return True, "Color removed"


def get_selected_faces_color(obj):
    """Get Fill color of selected polygons"""
    if obj is None or obj.type != 'MESH':
        return None

    mesh = obj.data

    # Получаем выделенные полигоны
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]
    if not selected_faces:
        bm.free()
        return None

    selected_face_indices = set(f.index for f in selected_faces)
    bm.free()

    # Получаем loops выделенных полигонов
    selected_loops = set()
    for poly in mesh.polygons:
        if poly.index in selected_face_indices:
            for loop_idx in poly.loop_indices:
                selected_loops.add(loop_idx)

    if not selected_loops:
        return None

    obj_key = obj.name

    # Проверяем какой Fill цвет есть у этих loops
    if obj_key in _fill_layers:
        for loop_idx in selected_loops:
            if loop_idx in _fill_layers[obj_key]:
                fill_color = _fill_layers[obj_key][loop_idx]
                return (round(fill_color[0], 3), round(fill_color[1], 3), round(fill_color[2], 3))

    # Fallback: по текущему цвету
    if mesh.color_attributes and mesh.color_attributes.active_color:
        color_attr = mesh.color_attributes.active_color
        first_loop = next(iter(selected_loops))
        c = color_attr.data[first_loop].color
        color_tuple = (round(c[0], 3), round(c[1], 3), round(c[2], 3))

        # Проверяем есть ли в списке Fill цветов
        for item in obj.gtatools_fill_colors:
            existing = (round(item.color[0], 3), round(item.color[1], 3), round(item.color[2], 3))
            if existing == color_tuple:
                return color_tuple

    return None


def fill_selected_faces_with_backup(obj, color):
    """Fill selected faces with a color using new layer system"""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    # Запоминаем режим и переключаемся в Object если нужно
    original_mode = obj.mode
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    mesh = obj.data
    if not mesh.color_attributes:
        return False, "No vertex colors found!"

    color_attr = mesh.color_attributes.active_color
    if color_attr is None:
        return False, "No active color layer!"

    # Get selected faces from bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]

    if not selected_faces:
        bm.free()
        return False, "No faces selected!"

    selected_indices = set(f.index for f in selected_faces)
    bm.free()

    # Собираем loop indices выделенных полигонов
    loop_indices = []
    for poly in mesh.polygons:
        if poly.index in selected_indices:
            for loop_idx in poly.loop_indices:
                loop_indices.append(loop_idx)

    filled_count = len(selected_indices)

    # Добавляем Fill слой (сохраняет базу автоматически)
    add_fill_layer(obj, color, loop_indices)

    # Применяем цвет напрямую (быстрее чем пересчёт)
    for loop_idx in loop_indices:
        color_attr.data[loop_idx].color = (color[0], color[1], color[2], 1.0)

    # Возвращаемся в исходный режим
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

    return True, f"Filled {filled_count} faces"


def restore_filled_faces(obj):
    """Restore all colors to base (remove fill and scatter layers)"""
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!"

    obj_key = obj.name

    # Проверяем есть ли база
    if obj_key not in _base_colors:
        return False, "No base colors saved!"

    # Запоминаем режим и переключаемся в Object если нужно
    original_mode = obj.mode
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    mesh = obj.data
    if not mesh.color_attributes:
        return False, "No vertex colors found!"

    color_attr = mesh.color_attributes.active_color
    if color_attr is None:
        return False, "No active color layer!"

    # Очищаем fill слои
    if obj_key in _fill_layers:
        _fill_layers[obj_key] = {}

    # Очищаем scatter слои
    if obj_key in _scatter_layers:
        _scatter_layers[obj_key] = {}

    # Восстанавливаем из базы
    base = _base_colors[obj_key]
    restored_count = 0
    for loop_idx, base_color in base.items():
        if loop_idx < len(color_attr.data):
            color_attr.data[loop_idx].color = base_color
            restored_count += 1

    # Удаляем все цвета из UI
    obj.gtatools_fill_colors.clear()

    # Возвращаемся в исходный режим
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

    return True, f"Restored {restored_count} vertices to base"


def scatter_light_from_selected(obj, intensity=1.0, falloff=2.0, iterations=3, radius=0.0):
    """Scatter light from selected faces to vertices with distance-based falloff

    Paints vertices based on distance from light source faces.
    Creates smooth gradient - closer vertices are brighter.
    """
    if obj is None or obj.type != 'MESH':
        return False, "Select a mesh object!", []

    # Запоминаем режим и переключаемся в Object если нужно
    original_mode = obj.mode
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    mesh = obj.data
    if not mesh.color_attributes:
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return False, "No vertex colors found!", []

    color_attr = mesh.color_attributes.active_color
    if color_attr is None:
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return False, "No active color layer!", []

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    selected_faces = [f for f in bm.faces if f.select]

    if not selected_faces:
        bm.free()
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return False, "No faces selected! Select light source faces!", []

    # Get source face indices
    source_indices = set(f.index for f in selected_faces)

    # Collect light source points (centers of selected faces)
    light_sources = []
    for f in selected_faces:
        light_sources.append(f.calc_center_median())

    # Calculate average color of selected faces (light source color)
    source_colors = []
    for poly in mesh.polygons:
        if poly.index in source_indices:
            for loop_idx in poly.loop_indices:
                c = color_attr.data[loop_idx].color
                source_colors.append((c[0], c[1], c[2]))

    if not source_colors:
        bm.free()
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return False, "Could not read source colors!", []

    # Average light color
    light_color = (
        sum(c[0] for c in source_colors) / len(source_colors),
        sum(c[1] for c in source_colors) / len(source_colors),
        sum(c[2] for c in source_colors) / len(source_colors)
    )
    light_brightness = (light_color[0] + light_color[1] + light_color[2]) / 3.0

    # Calculate auto-radius if not specified
    if radius <= 0:
        total_area = sum(f.calc_area() for f in selected_faces)
        avg_size = math.sqrt(total_area / len(selected_faces)) if selected_faces else 1.0
        radius = avg_size * iterations * 2.0

    # Get vertices from source faces (these won't be modified)
    source_verts = set()
    for f in selected_faces:
        for v in f.verts:
            source_verts.add(v.index)

    # Calculate light factor for each vertex based on distance
    # vertex_light[vert_index] = light_factor
    vertex_light = {}

    for vert in bm.verts:
        if vert.index in source_verts:
            continue  # Skip source vertices

        vert_pos = vert.co

        # Find minimum distance to any light source
        min_dist = float('inf')
        for light_pos in light_sources:
            dist = (vert_pos - light_pos).length
            if dist < min_dist:
                min_dist = dist

        # Only affect vertices within radius
        if min_dist < radius:
            # Calculate falloff based on distance
            # Normalize distance to 0-1 range within radius
            norm_dist = min_dist / radius

            # Apply falloff curve (higher falloff = faster decay)
            # factor goes from intensity (at distance 0) to 0 (at radius)
            factor = intensity * pow(1.0 - norm_dist, falloff)

            vertex_light[vert.index] = factor

    bm.free()

    # Build vertex index to loop indices mapping
    vert_to_loops = {}
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            vert_idx = mesh.loops[loop_idx].vertex_index
            if vert_idx not in vert_to_loops:
                vert_to_loops[vert_idx] = []
            vert_to_loops[vert_idx].append(loop_idx)

    # Apply light to vertices
    modified_count = 0
    affected_loops = []  # Track affected loop indices

    for vert_idx, factor in vertex_light.items():
        if vert_idx not in vert_to_loops:
            continue

        for loop_idx in vert_to_loops[vert_idx]:
            affected_loops.append(loop_idx)

            c = color_attr.data[loop_idx].color

            # Add light but don't exceed source brightness
            add_r = light_color[0] * factor * 0.5
            add_g = light_color[1] * factor * 0.5
            add_b = light_color[2] * factor * 0.5

            new_r = c[0] + add_r
            new_g = c[1] + add_g
            new_b = c[2] + add_b

            # Clamp so we don't exceed light source brightness
            new_brightness = (new_r + new_g + new_b) / 3.0
            if new_brightness > light_brightness:
                scale = light_brightness / new_brightness if new_brightness > 0 else 1.0
                new_r *= scale
                new_g *= scale
                new_b *= scale

            new_r = min(1.0, max(0.0, new_r))
            new_g = min(1.0, max(0.0, new_g))
            new_b = min(1.0, max(0.0, new_b))

            color_attr.data[loop_idx].color = (new_r, new_g, new_b, c[3])

        modified_count += 1

    # Возвращаемся в исходный режим
    if original_mode == 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

    return True, f"Light scattered to {modified_count} vertices (radius: {radius:.2f})", affected_loops


# =============================================================================
# GEOMETRY CHECK FUNCTIONS
# =============================================================================

def check_loose_geometry(obj):
    """Check object for loose vertices and edges (not attached to polygons)"""
    if obj is None or obj.type != 'MESH':
        return None, None, "Не меш объект"

    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    # Находим висящие вершины (не принадлежат ни одному face)
    loose_verts = [v.index for v in bm.verts if not v.link_faces]

    # Находим висящие рёбра (не принадлежат ни одному face)
    loose_edges = [e.index for e in bm.edges if not e.link_faces]

    bm.free()

    return loose_verts, loose_edges, None


# =============================================================================
# PROPERTY GROUPS
# =============================================================================

class GTATOOLS_FillColorItem(bpy.types.PropertyGroup):
    """Fill color list item"""
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
    """Check geometry for loose vertices and edges"""
    bl_idname = "gtatools.check_geometry"
    bl_label = "Check Geometry"
    bl_options = {'REGISTER', 'UNDO'}

    select_loose: BoolProperty(
        name="Select Loose",
        description="Select found problem elements",
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
    """Check geometry for N-gons (polygons with 5+ vertices)"""
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
    """Delete loose vertices and edges"""
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
    """Export textures to TXD archive"""
    bl_idname = "gtatools.export_txd"
    bl_label = "Export TXD"
    bl_options = {'PRESET'}
    filename_ext = ".txd"
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    selected_only: BoolProperty(
        name="Selected Only",
        description="Export textures only from selected objects",
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
    """Export DFF model"""
    bl_idname = "gtatools.export_dff"
    bl_label = "Export DFF"
    bl_options = {'PRESET'}
    filename_ext = ".dff"
    filter_glob: StringProperty(default="*.dff", options={'HIDDEN'})

    def execute(self, context):
        # Check if DragonFF is available
        try:
            # Отключаем превью прелайта перед экспортом (иначе экспорт ломается)
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    setup_prelight_preview(obj, enable=False)

            # export_version='0x36003' = GTA SA, only_selected=True, export_coll=False
            bpy.ops.export_dff.scene(
                filepath=self.filepath,
                export_version='0x36003',
                only_selected=True,
                export_coll=False
            )

            # Включаем превью прелайта обратно после экспорта
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    setup_prelight_preview(obj, enable=True)

            self.report({'INFO'}, f"Exported DFF: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"DFF export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_col(bpy.types.Operator, ExportHelper):
    """Export COL collision model"""
    bl_idname = "gtatools.export_col"
    bl_label = "Export COL"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    def execute(self, context):
        # Check if collision exporter is available
        try:
            # Отключаем превью прелайта перед экспортом (иначе экспорт ломается)
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    setup_prelight_preview(obj, enable=False)
                    # Устанавливаем тип объекта как Collision для DragonFF
                    if hasattr(obj, 'dff'):
                        obj.dff.type = 'COL'

            # COL всегда экспортируется в центре (0,0,0)
            original_locations = {}
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    original_locations[obj.name] = obj.location.copy()
                    obj.location = (0, 0, 0)

            # export_version='3' = GTA SA (COL3), only_selected=True
            bpy.ops.export_col.scene(
                filepath=self.filepath,
                export_version='3',
                only_selected=True
            )

            # Возвращаем оригинальные позиции
            for obj in context.selected_objects:
                if obj.name in original_locations:
                    obj.location = original_locations[obj.name]

            # Исправляем имя модели внутри COL файла
            # Берём имя из имени файла (без расширения)
            model_name = os.path.splitext(os.path.basename(self.filepath))[0]
            fix_col_model_name(self.filepath, model_name)

            # Включаем превью прелайта обратно после экспорта
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    setup_prelight_preview(obj, enable=True)

            self.report({'INFO'}, f"Exported COL: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"COL export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_all(bpy.types.Operator):
    """Export all selected models (DFF + COL + LOD + TXD) - supports multiple model groups"""
    bl_idname = "gtatools.export_all"
    bl_label = "Export All (DFF+COL+LOD+TXD)"
    bl_options = {'REGISTER'}

    directory: StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def export_model_group(self, context, base_name, models, skip_txd, use_gpu):
        """Export a single model group (DFF + LOD + COL + TXD)"""
        exported = []
        errors = []

        # Экспорт DFF (версия GTA SA)
        if models['DFF']:
            dff_path = os.path.join(self.directory, f"{base_name}.dff")
            try:
                bpy.ops.object.select_all(action='DESELECT')
                models['DFF'].select_set(True)
                context.view_layer.objects.active = models['DFF']

                bpy.ops.export_dff.scene(
                    filepath=dff_path,
                    export_version='0x36003',
                    only_selected=True,
                    export_coll=False
                )

                exported.append(f"{base_name}.dff")
            except Exception as e:
                errors.append(f"{base_name}.dff: {str(e)}")

        # Экспорт LOD (с префиксом LOD, версия GTA SA)
        if models['LOD']:
            lod_path = os.path.join(self.directory, f"LOD{base_name}.dff")
            try:
                bpy.ops.object.select_all(action='DESELECT')
                models['LOD'].select_set(True)
                context.view_layer.objects.active = models['LOD']

                bpy.ops.export_dff.scene(
                    filepath=lod_path,
                    export_version='0x36003',
                    only_selected=True,
                    export_coll=False
                )

                exported.append(f"LOD{base_name}.dff")
            except Exception as e:
                errors.append(f"LOD{base_name}.dff: {str(e)}")

        # Экспорт COL (версия GTA SA COL3)
        if models['COL']:
            col_path = os.path.join(self.directory, f"{base_name}.col")
            try:
                bpy.ops.object.select_all(action='DESELECT')
                models['COL'].select_set(True)
                context.view_layer.objects.active = models['COL']
                # Устанавливаем тип объекта как Collision для DragonFF
                if hasattr(models['COL'], 'dff'):
                    models['COL'].dff.type = 'COL'

                # COL всегда экспортируется в центре (0,0,0)
                original_col_loc = models['COL'].location.copy()
                models['COL'].location = (0, 0, 0)

                bpy.ops.export_col.scene(
                    filepath=col_path,
                    export_version='3',
                    only_selected=True
                )

                # Возвращаем позицию
                models['COL'].location = original_col_loc

                # Исправляем имя модели внутри COL файла
                fix_col_model_name(col_path, base_name)
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

        # Disable prelight preview before export (otherwise export breaks)
        for base_name, models in model_groups.items():
            for model_type in ['DFF', 'LOD', 'COL']:
                if models[model_type] and models[model_type].type == 'MESH':
                    setup_prelight_preview(models[model_type], enable=False)

        all_exported = []
        all_errors = []
        wm = context.window_manager

        # Настройки экспорта
        skip_txd = context.scene.gtatools_export_all_skip_txd
        use_gpu = context.scene.gtatools_txd_use_gpu

        # Считаем общее количество шагов для прогресс-бара
        total_steps = 0
        for base_name, models in model_groups.items():
            total_steps += sum([
                1 if models['DFF'] else 0,
                1 if models['LOD'] else 0,
                1 if models['COL'] else 0,
                1 if (models['DFF'] or models['LOD']) and not skip_txd else 0
            ])

        current_step = 0
        wm.progress_begin(0, total_steps)

        # Экспортируем каждую группу моделей
        for base_name, models in model_groups.items():
            wm.progress_update(current_step)
            exported, errors = self.export_model_group(context, base_name, models, skip_txd, use_gpu)
            all_exported.extend(exported)
            all_errors.extend(errors)

            # Обновляем прогресс
            current_step += sum([
                1 if models['DFF'] else 0,
                1 if models['LOD'] else 0,
                1 if models['COL'] else 0,
                1 if (models['DFF'] or models['LOD']) and not skip_txd else 0
            ])

        wm.progress_end()

        # Включаем превью прелайта обратно после экспорта
        for base_name, models in model_groups.items():
            for model_type in ['DFF', 'LOD', 'COL']:
                if models[model_type] and models[model_type].type == 'MESH':
                    setup_prelight_preview(models[model_type], enable=True)

        # Result
        num_groups = len(model_groups)
        if all_exported:
            self.report({'INFO'}, f"{T('Экспортировано:')} {len(all_exported)} файлов ({num_groups} моделей)")
        if all_errors:
            self.report({'WARNING'}, f"{T('Ошибки:')} {'; '.join(errors)}")

        return {'FINISHED'}


class GTATOOLS_OT_detect_models(bpy.types.Operator):
    """Detect DFF, LOD, COL models among selected"""
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
    """Apply GTA SA Prelight to selected object"""
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
    """Average vertex colors for coplanar faces"""
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
    """Generate lightmap code for selected object"""
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
    """Copy result to clipboard"""
    bl_idname = "gtatools.lightmap_copy"
    bl_label = "Copy to Clipboard"

    def execute(self, context):
        scene = context.scene
        if scene.gtatools_lightmap_result:
            context.window_manager.clipboard = scene.gtatools_lightmap_result
            self.report({'INFO'}, "Copied to clipboard")
        return {'FINISHED'}


class GTATOOLS_OT_lightmap_clear(bpy.types.Operator):
    """Clear generated code"""
    bl_idname = "gtatools.lightmap_clear"
    bl_label = "Clear"

    def execute(self, context):
        context.scene.gtatools_lightmap_result = ""
        self.report({'INFO'}, T("Код очищен"))
        return {'FINISHED'}


class GTATOOLS_OT_create_prelight_lights(bpy.types.Operator):
    """Create 8 lights for prelight baking around object"""
    bl_idname = "gtatools.create_prelight_lights"
    bl_label = "Create Prelight Lights"
    bl_options = {'REGISTER', 'UNDO'}

    distance: FloatProperty(
        name="Distance",
        description="Distance of lights from center",
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
    """Remove all prelight lights"""
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
    """Bake lighting from Point sources to vertex colors"""
    bl_idname = "gtatools.bake_vertex_colors"
    bl_label = "Bake Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    use_shadows: BoolProperty(
        name="Use Shadows",
        description="Calculate shadows (slower but more accurate)",
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
    """Quick bake vertex colors from Point sources (no shadows)"""
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

        success, message = bake_vertex_colors_simple(obj, ambient, intensity, gamma)

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
    """Reset bake settings to default"""
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
    """Reset Scatter Light settings to default"""
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
    """Analyze vertex colors of selected object"""
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
    """Apply brightness offset (V) to vertex colors"""
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


class GTATOOLS_OT_load_lightmap(bpy.types.Operator):
    """Load Lightmap from .blend folder (textures with LP_ prefix)"""
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

            # Создаём ноду MixRGB (Multiply)
            mix_node = nodes.new('ShaderNodeMixRGB')
            mix_node.name = "Lightmap_Mix"
            mix_node.label = "Lightmap Mix"
            mix_node.blend_type = 'MULTIPLY'
            mix_node.inputs['Fac'].default_value = 1.0

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
            # Оригинальная текстура -> Color1
            if original_node:
                links.new(original_socket, mix_node.inputs['Color1'])
            else:
                mix_node.inputs['Color1'].default_value = (1, 1, 1, 1)

            # Лайтмап -> Color2
            links.new(lm_tex.outputs['Color'], mix_node.inputs['Color2'])

            # Подключаем Lightmap_Mix
            if prelight_mix:
                # Если есть Prelight_Mix - подключаем лайтмап к его входу A
                links.new(mix_node.outputs['Color'], prelight_mix.inputs['A'])
            else:
                # Иначе - напрямую к Base Color
                links.new(mix_node.outputs['Color'], base_color_input)

            applied_count += 1

        if applied_count > 0:
            self.report({'INFO'}, f"Lightmap '{lightmap_filename}' applied to {applied_count} material(s)")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, T("Не удалось применить лайтмап - нет подходящих материалов"))
            return {'CANCELLED'}


class GTATOOLS_OT_remove_lightmap(bpy.types.Operator):
    """Remove Lightmap from object materials"""
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

                # Находим что было подключено к Color1 (оригинальная текстура)
                original_socket = None
                if lm_mix.inputs['Color1'].links:
                    original_link = lm_mix.inputs['Color1'].links[0]
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
    """Create Day and Night color attributes"""
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
    """Toggle prelight preview - show vertex colors with textures"""
    bl_idname = "gtatools.prelight_preview"
    bl_label = "Toggle Prelight Preview"
    bl_options = {'REGISTER', 'UNDO'}

    enable: BoolProperty(
        name="Enable",
        description="Enable or disable prelight preview",
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


class GTATOOLS_OT_eyedropper_color(bpy.types.Operator):
    """Click on polygon to pick its color"""
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
    """Fill selected faces with color"""
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
    """Restore colors changed by fill"""
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
    """Delete color from list and restore original colors"""
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
    """Select polygons with this color"""
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
    """Delete scatter level (recalculate colors)"""
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
    """Clear all scatter levels of color"""
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
    """Scatter light from selected faces to neighbors"""
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
    """Toggle face selection mode in Vertex Paint"""
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
    """Switch to Edit Mode for face selection"""
    bl_idname = "gtatools.switch_to_edit"
    bl_label = "Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
        return {'FINISHED'}


class GTATOOLS_OT_switch_to_vpaint(bpy.types.Operator):
    """Switch to Vertex Paint Mode"""
    bl_idname = "gtatools.switch_to_vpaint"
    bl_label = "Vertex Paint Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object:
            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        return {'FINISHED'}


class GTATOOLS_OT_select_color_attribute(bpy.types.Operator):
    """Select color attribute and update prelight preview"""
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
                vc_node.layer_name = color_name


class GTATOOLS_OT_add_color_attribute(bpy.types.Operator):
    """Add new color attribute"""
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
    """Delete active color attribute"""
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
    """Create color attribute"""
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
    """Delete color attribute by name"""
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
    """Load textures by material names from specified folders"""
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
                material.blend_method = 'BLEND'
                if hasattr(material, 'shadow_method'):
                    material.shadow_method = 'HASHED'

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
    """Set path to .blend file folder"""
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
    """Create material from dropped texture"""
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
                    material.blend_method = 'BLEND'
                    if hasattr(material, 'shadow_method'):
                        material.shadow_method = 'HASHED'
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
    """Check material count on selected objects"""
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
    """Merge duplicate materials (.001, .002, etc.) with originals"""
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


# =============================================================================
# PANELS
# =============================================================================

class GTATOOLS_PT_main_panel(bpy.types.Panel):
    """GTA Tools main panel"""
    bl_label = "GTA Tools"
    bl_idname = "GTATOOLS_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'

    def draw(self, context):
        layout = self.layout
        layout.label(text="GTA SA Modding Tools", icon='TOOL_SETTINGS')


class GTATOOLS_PT_export_panel(bpy.types.Panel):
    """GTA models export panel"""
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
        row.operator("gtatools.export_all", text="Export All (DFF+COL+LOD+TXD)", icon='EXPORT')
        row = layout.row(align=True)
        row.prop(context.scene, "gtatools_export_all_skip_txd", text=T("Пропустить TXD"))

        layout.separator()

        # Individual export buttons
        layout.label(text="Export Individual:")
        row = layout.row(align=True)
        row.operator("gtatools.export_dff", text="DFF", icon='MESH_DATA')
        row.operator("gtatools.export_col", text="COL", icon='MESH_CUBE')

        row = layout.row(align=True)
        row.operator("gtatools.check_geometry", text="Check vertex", icon='VIEWZOOM')
        row.operator("gtatools.check_ngons", text="Check N-gon", icon='MESH_DATA')

        row = layout.row(align=True)
        row.operator("gtatools.export_txd", text="TXD", icon='TEXTURE')

        # GPU/CPU переключатель
        row = layout.row(align=True)
        row.prop(context.scene, "gtatools_txd_use_gpu", text="GPU (NVTT)", toggle=True)

        # Проверка NVTT если включен GPU
        if context.scene.gtatools_txd_use_gpu:
            nvtt_path = context.scene.gtatools_nvtt_path
            available, msg = check_nvtt_available(nvtt_path)
            if not available:
                layout.label(text=T("Статус: Не найден"), icon='ERROR')

        # NVTT Settings (раскрывающийся)
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "gtatools_show_nvtt_settings",
                 icon='TRIA_DOWN' if context.scene.gtatools_show_nvtt_settings else 'TRIA_RIGHT',
                 text="NVTT Settings", emboss=False)

        if context.scene.gtatools_show_nvtt_settings:
            box.prop(context.scene, "gtatools_nvtt_path", text="")
            nvtt_path = context.scene.gtatools_nvtt_path
            available, msg = check_nvtt_available(nvtt_path)
            if available:
                box.label(text=T("Статус: Готов"), icon='CHECKMARK')
            else:
                box.label(text=T("Статус: Не найден"), icon='ERROR')


class GTATOOLS_PT_inu_tools_panel(bpy.types.Panel):
    """INU Tools panel in Properties > Scene"""
    bl_label = "INU Tools"
    bl_idname = "GTATOOLS_PT_inu_tools_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Path 1 - System textures
        box = layout.box()
        box.label(text="System Textures:", icon='TEXTURE')
        box.prop(scene, "gtatools_texture_path1", text="")

        # Path 2 - Blend folder
        box = layout.box()
        row = box.row()
        row.label(text=T("Папка .blend:"), icon='FILE_FOLDER')
        row.operator("gtatools.set_blend_folder", text="", icon='FILE_REFRESH')
        box.prop(scene, "gtatools_texture_path2", text="")

        layout.separator()

        # Buttons
        layout.operator("gtatools.load_textures", text=T("Загрузить текстуры"), icon='IMPORT')
        layout.operator("gtatools.cleanup_materials", text=T("Очистка материалов"), icon='BRUSH_DATA')
        layout.operator("gtatools.check_materials", text=T("Проверить материалы"), icon='MATERIAL')


class GTATOOLS_PT_prelight_panel(bpy.types.Panel):
    """Prelight panel"""
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
        row.operator("gtatools.create_prelight_lights", text="Create 8 Lights", icon='LIGHT')
        row.operator("gtatools.remove_prelight_lights", text="Remove", icon='X')

        layout.separator()

        # Color Attributes selector
        layout.label(text="Color Attributes:")

        if obj and obj.type == 'MESH':
            mesh = obj.data
            active_attr = mesh.color_attributes.active_color if mesh.color_attributes else None

            box = layout.box()

            # Day row
            row = box.row(align=True)
            if "Day" in mesh.color_attributes:
                is_active = (active_attr and active_attr.name == "Day")
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
                is_active = (active_attr and active_attr.name == "Night")
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
                    is_active = (active_attr and active_attr.name == attr.name)
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
        row = layout.row(align=True)
        row.operator("gtatools.bake_vertex_colors_simple", text="Fast", icon='RENDER_STILL')
        row.operator("gtatools.bake_vertex_colors", text="With Shadows", icon='RENDER_RESULT')

        layout.separator()

        # Adjust Color (V offset)
        layout.label(text="Adjust Color:")
        row = layout.row(align=True)
        row.prop(scene, "gtatools_v_offset", text="V")
        row.operator("gtatools.apply_v_offset", text="Apply", icon='CHECKMARK')



class GTATOOLS_PT_bake_settings_subpanel(bpy.types.Panel):
    """Advanced bake settings"""
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

        layout.prop(scene, "gtatools_bake_ambient", text="Ambient", slider=True)
        layout.prop(scene, "gtatools_bake_intensity", text="Intensity", slider=True)
        layout.prop(scene, "gtatools_bake_gamma", text="Gamma", slider=True)

        layout.separator()
        layout.operator("gtatools.reset_bake_settings", icon='LOOP_BACK')


class GTATOOLS_PT_vertex_paint_panel(bpy.types.Panel):
    """Vertex Paint tools panel"""
    bl_label = "Vertex Paint"
    bl_idname = "GTATOOLS_PT_vertex_paint_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        # Mode switching
        layout.label(text="Mode:")
        row = layout.row(align=True)
        row.operator("gtatools.switch_to_edit", text="Edit", icon='EDITMODE_HLT')
        row.operator("gtatools.switch_to_vpaint", text="Paint", icon='VPAINT_HLT')

        # Face selection toggle (only in Vertex Paint mode)
        if obj and obj.mode == 'VERTEX_PAINT':
            row = layout.row()
            icon = 'RESTRICT_SELECT_OFF' if obj.data.use_paint_mask else 'RESTRICT_SELECT_ON'
            row.operator("gtatools.toggle_face_select", text="Face Select", icon=icon, depress=obj.data.use_paint_mask)

        layout.separator()

        # Fill selected faces
        layout.label(text="Fill Faces:")
        row = layout.row(align=True)
        row.prop(scene, "gtatools_fill_color", text="")
        row.operator("gtatools.eyedropper_color", text="", icon='EYEDROPPER')
        row = layout.row(align=True)
        row.operator("gtatools.fill_faces", text="Fill", icon='BRUSH_DATA')
        row.operator("gtatools.restore_fill", text="Restore", icon='LOOP_BACK')

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
        row.label(text="Scatter Light:")
        row.operator("gtatools.reset_scatter_settings", text="", icon='LOOP_BACK')
        layout.prop(scene, "gtatools_scatter_intensity", text="Intensity", slider=True)
        layout.prop(scene, "gtatools_scatter_falloff", text="Falloff", slider=True)
        layout.prop(scene, "gtatools_scatter_iterations", text="Iterations")
        layout.prop(scene, "gtatools_scatter_radius", text="Radius (0=auto)", slider=True)
        layout.operator("gtatools.scatter_light", text="Scatter from Selected", icon='LIGHT_POINT')


class GTATOOLS_PT_lightmap_panel(bpy.types.Panel):
    """Lightmap generator panel"""
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
        layout.label(text="Lightmap Texture:")
        row = layout.row(align=True)
        row.operator("gtatools.load_lightmap", text="Load (LP_)", icon='IMAGE_DATA')
        row.operator("gtatools.remove_lightmap", text="Remove", icon='X')

        layout.separator()

        # Generate code
        layout.label(text="Generate Code:")
        layout.operator("gtatools.lightmap_generate", text="Generate", icon='FILE_TEXT')
        layout.prop(scene, "gtatools_lightmap_path", text="Path")
        layout.prop(scene, "gtatools_model_id", text="Model ID")

        layout.separator()
        layout.label(text="Result:")

        box = layout.box()
        if scene.gtatools_lightmap_result:
            lines = scene.gtatools_lightmap_result.split('\n')
            for line in lines:
                box.label(text=line)
            row = layout.row(align=True)
            row.operator("gtatools.lightmap_copy", text="Copy", icon='COPYDOWN')
            row.operator("gtatools.lightmap_clear", text="Clear", icon='X')
        else:
            box.label(text="Press button to generate")


# =============================================================================
# UV TOOLS
# =============================================================================

import gpu
from gpu_extras.batch import batch_for_shader

# Global variable for draw handler
_uv_grid_draw_handler = None
_uv_grid_visible = False


def draw_uv_grid_callback():
    """Draw grid overlay in UV Editor"""
    global _uv_grid_visible

    if not _uv_grid_visible:
        return

    context = bpy.context
    scene = context.scene

    cols = scene.gtatools_uv_grid_cols
    rows = scene.gtatools_uv_grid_rows

    if cols < 1 or rows < 1:
        return

    # Get current space and region
    area = context.area
    if not area or area.type != 'IMAGE_EDITOR':
        return

    region = None
    for r in area.regions:
        if r.type == 'WINDOW':
            region = r
            break

    if not region:
        return

    # Get view transformation
    space = area.spaces.active
    if not space:
        return

    # Calculate view to region transformation
    view2d = region.view2d

    # Build grid lines
    vertices = []
    cell_width = 1.0 / cols
    cell_height = 1.0 / rows

    # Vertical lines
    for i in range(cols + 1):
        x = i * cell_width
        # Convert UV to region coordinates
        start = view2d.view_to_region(x, 0, clip=False)
        end = view2d.view_to_region(x, 1, clip=False)
        vertices.append(start)
        vertices.append(end)

    # Horizontal lines
    for i in range(rows + 1):
        y = i * cell_height
        start = view2d.view_to_region(0, y, clip=False)
        end = view2d.view_to_region(1, y, clip=False)
        vertices.append(start)
        vertices.append(end)

    if not vertices:
        return

    # Draw with GPU
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": vertices})

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2.0)

    shader.bind()
    shader.uniform_float("color", (1.0, 0.5, 0.0, 0.8))  # Orange color
    batch.draw(shader)

    gpu.state.blend_set('NONE')
    gpu.state.line_width_set(1.0)


class GTATOOLS_OT_toggle_uv_grid(bpy.types.Operator):
    """Show/hide grid on UV"""
    bl_idname = "gtatools.toggle_uv_grid"
    bl_label = "Toggle UV Grid"

    def execute(self, context):
        global _uv_grid_draw_handler, _uv_grid_visible

        _uv_grid_visible = not _uv_grid_visible

        if _uv_grid_visible:
            if _uv_grid_draw_handler is None:
                _uv_grid_draw_handler = bpy.types.SpaceImageEditor.draw_handler_add(
                    draw_uv_grid_callback, (), 'WINDOW', 'POST_PIXEL'
                )
            self.report({'INFO'}, T("Сетка UV включена"))
        else:
            self.report({'INFO'}, T("Сетка UV выключена"))

        # Force redraw
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.tag_redraw()

        return {'FINISHED'}


def calculate_uv_offset(face_width, face_height, cell_width, cell_height, alignment):
    """Calculate UV offset based on alignment"""
    if alignment == 'CENTER':
        offset_u = (cell_width - face_width) / 2
        offset_v = (cell_height - face_height) / 2
    elif alignment == 'TOP_LEFT':
        offset_u = 0
        offset_v = cell_height - face_height
    elif alignment == 'TOP_RIGHT':
        offset_u = cell_width - face_width
        offset_v = cell_height - face_height
    elif alignment == 'BOTTOM_LEFT':
        offset_u = 0
        offset_v = 0
    elif alignment == 'BOTTOM_RIGHT':
        offset_u = cell_width - face_width
        offset_v = 0
    elif alignment == 'TOP_CENTER':
        offset_u = (cell_width - face_width) / 2
        offset_v = cell_height - face_height
    elif alignment == 'BOTTOM_CENTER':
        offset_u = (cell_width - face_width) / 2
        offset_v = 0
    elif alignment == 'LEFT_CENTER':
        offset_u = 0
        offset_v = (cell_height - face_height) / 2
    elif alignment == 'RIGHT_CENTER':
        offset_u = cell_width - face_width
        offset_v = (cell_height - face_height) / 2
    else:
        offset_u = (cell_width - face_width) / 2
        offset_v = (cell_height - face_height) / 2
    return offset_u, offset_v


def find_connected_face_groups(faces, uv_layer):
    """Find groups of faces that overlap in UV space or are connected by mesh edges"""
    if not faces:
        return []

    face_set = set(faces)
    visited = set()
    groups = []

    def get_face_uv_bounds(face):
        us = [loop[uv_layer].uv.x for loop in face.loops]
        vs = [loop[uv_layer].uv.y for loop in face.loops]
        return min(us), max(us), min(vs), max(vs)

    def bounds_overlap(b1, b2, margin=0.01):
        """Check if two bounding boxes overlap (with small margin)"""
        min_u1, max_u1, min_v1, max_v1 = b1
        min_u2, max_u2, min_v2, max_v2 = b2
        return not (max_u1 + margin < min_u2 or max_u2 + margin < min_u1 or
                    max_v1 + margin < min_v2 or max_v2 + margin < min_v1)

    # Pre-calculate UV bounds for all faces
    face_bounds = {face: get_face_uv_bounds(face) for face in faces}

    for face in faces:
        if face in visited:
            continue

        # BFS to find all connected faces (by mesh edges OR UV overlap)
        group = []
        queue = [face]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue

            visited.add(current)
            group.append(current)
            current_bounds = face_bounds[current]

            # Method 1: Find adjacent faces through shared mesh edges
            for edge in current.edges:
                for linked_face in edge.link_faces:
                    if linked_face not in visited and linked_face in face_set:
                        queue.append(linked_face)

            # Method 2: Find faces with overlapping UV bounds
            for other_face in faces:
                if other_face not in visited and other_face in face_set:
                    if bounds_overlap(current_bounds, face_bounds[other_face]):
                        queue.append(other_face)

        if group:
            groups.append(group)

    return groups


def get_island_uv_bounds(island, uv_layer):
    """Get UV bounding box for an island of faces"""
    all_us = []
    all_vs = []

    for face in island:
        for loop in face.loops:
            all_us.append(loop[uv_layer].uv.x)
            all_vs.append(loop[uv_layer].uv.y)

    return min(all_us), max(all_us), min(all_vs), max(all_vs)


def move_island_uv(island, uv_layer, offset_u, offset_v):
    """Move all UV vertices of an island by offset"""
    # Track moved UV vertices to avoid moving shared vertices twice
    moved = set()

    for face in island:
        for loop in face.loops:
            uv = loop[uv_layer].uv
            uv_key = (id(loop), round(uv.x, 6), round(uv.y, 6))
            if uv_key not in moved:
                uv.x += offset_u
                uv.y += offset_v
                moved.add(uv_key)


class GTATOOLS_OT_randomize_uv_grid(bpy.types.Operator):
    """Randomly distribute UV of selected polygons on grid (for windows, variations)"""
    bl_idname = "gtatools.randomize_uv_grid"
    bl_label = "Randomize UV Grid"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        import bmesh
        import random

        obj = context.active_object
        scene = context.scene

        # Get grid settings
        cols = scene.gtatools_uv_grid_cols
        rows = scene.gtatools_uv_grid_rows
        alignment = scene.gtatools_uv_grid_align
        link_islands = scene.gtatools_uv_link_islands

        if cols < 1 or rows < 1:
            self.report({'ERROR'}, T("Укажите количество колонок и рядов!"))
            return {'CANCELLED'}

        # Get bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()

        # Get selected faces
        selected_faces = [f for f in bm.faces if f.select]

        if not selected_faces:
            self.report({'ERROR'}, T("Выделите полигоны!"))
            return {'CANCELLED'}

        # Cell size
        cell_width = 1.0 / cols
        cell_height = 1.0 / rows

        randomized_count = 0

        if link_islands:
            # Group faces by UV islands and move each island together
            islands = find_connected_face_groups(selected_faces, uv_layer)

            for island in islands:
                # Get island UV bounds
                min_u, max_u, min_v, max_v = get_island_uv_bounds(island, uv_layer)

                island_width = max_u - min_u
                island_height = max_v - min_v

                # Random cell
                random_col = random.randint(0, cols - 1)
                random_row = random.randint(0, rows - 1)

                # Target cell position
                target_u = random_col * cell_width
                target_v = random_row * cell_height

                # Calculate alignment offset
                align_offset_u, align_offset_v = calculate_uv_offset(
                    island_width, island_height, cell_width, cell_height, alignment
                )

                offset_u = target_u + align_offset_u - min_u
                offset_v = target_v + align_offset_v - min_v

                # Move entire island
                move_island_uv(island, uv_layer, offset_u, offset_v)
                randomized_count += 1

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"{T('Рандомизировано:')} {randomized_count} {T('групп')}")
        else:
            # Original behavior - each face moves independently
            for face in selected_faces:
                us = [loop[uv_layer].uv.x for loop in face.loops]
                vs = [loop[uv_layer].uv.y for loop in face.loops]

                min_u, max_u = min(us), max(us)
                min_v, max_v = min(vs), max(vs)

                face_width = max_u - min_u
                face_height = max_v - min_v

                random_col = random.randint(0, cols - 1)
                random_row = random.randint(0, rows - 1)

                target_u = random_col * cell_width
                target_v = random_row * cell_height

                align_offset_u, align_offset_v = calculate_uv_offset(
                    face_width, face_height, cell_width, cell_height, alignment
                )

                offset_u = target_u + align_offset_u - min_u
                offset_v = target_v + align_offset_v - min_v

                for loop in face.loops:
                    loop[uv_layer].uv.x += offset_u
                    loop[uv_layer].uv.y += offset_v

                randomized_count += 1

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"{T('Рандомизировано:')} {randomized_count} {T('полигонов')}")

        return {'FINISHED'}


class GTATOOLS_OT_snap_uv_to_grid(bpy.types.Operator):
    """Snap UV of selected polygons to nearest grid cell"""
    bl_idname = "gtatools.snap_uv_to_grid"
    bl_label = "Snap UV to Grid"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        import bmesh

        obj = context.active_object
        scene = context.scene

        cols = scene.gtatools_uv_grid_cols
        rows = scene.gtatools_uv_grid_rows
        alignment = scene.gtatools_uv_grid_align
        link_islands = scene.gtatools_uv_link_islands

        if cols < 1 or rows < 1:
            self.report({'ERROR'}, T("Укажите количество колонок и рядов!"))
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()

        selected_faces = [f for f in bm.faces if f.select]

        if not selected_faces:
            self.report({'ERROR'}, T("Выделите полигоны!"))
            return {'CANCELLED'}

        cell_width = 1.0 / cols
        cell_height = 1.0 / rows

        snapped_count = 0

        if link_islands:
            # Group faces by UV islands and snap each island together
            islands = find_connected_face_groups(selected_faces, uv_layer)

            for island in islands:
                # Get island UV bounds
                min_u, max_u, min_v, max_v = get_island_uv_bounds(island, uv_layer)

                island_width = max_u - min_u
                island_height = max_v - min_v

                # Find center of island UV
                center_u = (min_u + max_u) / 2
                center_v = (min_v + max_v) / 2

                # Find nearest cell
                nearest_col = int(center_u / cell_width)
                nearest_row = int(center_v / cell_height)

                # Clamp to valid range
                nearest_col = max(0, min(cols - 1, nearest_col))
                nearest_row = max(0, min(rows - 1, nearest_row))

                # Target cell position
                target_u = nearest_col * cell_width
                target_v = nearest_row * cell_height

                # Calculate alignment offset
                align_offset_u, align_offset_v = calculate_uv_offset(
                    island_width, island_height, cell_width, cell_height, alignment
                )

                offset_u = target_u + align_offset_u - min_u
                offset_v = target_v + align_offset_v - min_v

                # Move entire island
                move_island_uv(island, uv_layer, offset_u, offset_v)
                snapped_count += 1

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"{T('Привязано:')} {snapped_count} {T('групп')}")
        else:
            # Original behavior - each face snaps independently
            for face in selected_faces:
                us = [loop[uv_layer].uv.x for loop in face.loops]
                vs = [loop[uv_layer].uv.y for loop in face.loops]

                min_u, max_u = min(us), max(us)
                min_v, max_v = min(vs), max(vs)

                face_width = max_u - min_u
                face_height = max_v - min_v

                center_u = (min_u + max_u) / 2
                center_v = (min_v + max_v) / 2

                nearest_col = int(center_u / cell_width)
                nearest_row = int(center_v / cell_height)

                nearest_col = max(0, min(cols - 1, nearest_col))
                nearest_row = max(0, min(rows - 1, nearest_row))

                target_u = nearest_col * cell_width
                target_v = nearest_row * cell_height

                align_offset_u, align_offset_v = calculate_uv_offset(
                    face_width, face_height, cell_width, cell_height, alignment
                )

                offset_u = target_u + align_offset_u - min_u
                offset_v = target_v + align_offset_v - min_v

                for loop in face.loops:
                    loop[uv_layer].uv.x += offset_u
                    loop[uv_layer].uv.y += offset_v

                snapped_count += 1

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"{T('Привязано:')} {snapped_count} {T('полигонов')}")

        return {'FINISHED'}


class GTATOOLS_PT_uv_tools_panel(bpy.types.Panel):
    """GTA Tools UV panel"""
    bl_label = "GTA Tools"
    bl_idname = "GTATOOLS_PT_uv_tools_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # UV Grid Randomizer
        box = layout.box()
        box.label(text="UV Grid Randomizer", icon='GRID')

        row = box.row(align=True)
        row.prop(scene, "gtatools_uv_grid_cols", text=T("Колонки"))
        row.prop(scene, "gtatools_uv_grid_rows", text=T("Ряды"))

        # Toggle grid visibility button
        global _uv_grid_visible
        icon = 'HIDE_OFF' if _uv_grid_visible else 'HIDE_ON'
        text = T("Скрыть сетку") if _uv_grid_visible else T("Показать сетку")
        box.operator("gtatools.toggle_uv_grid", text=text, icon=icon)

        # Alignment selection
        box.prop(scene, "gtatools_uv_grid_align", text=T("Позиция"))

        # Link islands toggle
        row = box.row(align=True)
        row.prop(scene, "gtatools_uv_link_islands", text=T("Связать полигоны"), icon='LINKED', toggle=True)

        row = box.row(align=True)
        row.operator("gtatools.randomize_uv_grid", text=T("Рандом"), icon='MOD_UVPROJECT')
        row.operator("gtatools.snap_uv_to_grid", text=T("Привязать"), icon='SNAP_GRID')


# =============================================================================
# REGISTRATION
# =============================================================================

classes = (
    GTATOOLS_FillColorItem,
    GTATOOLS_OT_check_geometry,
    GTATOOLS_OT_check_ngons,
    GTATOOLS_OT_export_txd,
    GTATOOLS_OT_export_dff,
    GTATOOLS_OT_export_col,
    GTATOOLS_OT_export_all,
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
    GTATOOLS_OT_reset_scatter_settings,
    GTATOOLS_OT_analyze_vertex_colors,
    GTATOOLS_OT_apply_v_offset,
    GTATOOLS_OT_load_lightmap,
    GTATOOLS_OT_remove_lightmap,
    GTATOOLS_OT_create_day_night,
    GTATOOLS_OT_prelight_preview,
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
    GTATOOLS_OT_toggle_uv_grid,
    GTATOOLS_OT_randomize_uv_grid,
    GTATOOLS_OT_snap_uv_to_grid,
    GTATOOLS_PT_main_panel,
    GTATOOLS_PT_export_panel,
    GTATOOLS_PT_inu_tools_panel,
    GTATOOLS_PT_prelight_panel,
    GTATOOLS_PT_bake_settings_subpanel,
    GTATOOLS_PT_vertex_paint_panel,
    GTATOOLS_PT_lightmap_panel,
    GTATOOLS_PT_uv_tools_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

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
        description="Number of columns in texture grid",
        default=3,
        min=1,
        max=16,
        update=update_uv_grid
    )
    bpy.types.Scene.gtatools_uv_grid_rows = IntProperty(
        name="Rows",
        description="Number of rows in texture grid",
        default=2,
        min=1,
        max=16,
        update=update_uv_grid
    )

    from bpy.props import EnumProperty
    bpy.types.Scene.gtatools_uv_grid_align = EnumProperty(
        name="Alignment",
        description="UV position in cell",
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
        description="Polygons with overlapping UVs move together",
        default=False
    )

    # NVIDIA Texture Tools settings
    bpy.types.Scene.gtatools_nvtt_path = StringProperty(
        name="NVTT Path",
        description="Path to NVIDIA Texture Tools folder (for GPU compression)",
        default=r"D:\NVIDIA Corporation\NVIDIA Texture Tools",
        subtype='DIR_PATH'
    )

    bpy.types.Scene.gtatools_txd_use_gpu = BoolProperty(
        name="Use GPU",
        description="Use GPU (NVTT) for texture compression",
        default=False
    )

    bpy.types.Scene.gtatools_show_nvtt_settings = BoolProperty(
        name="Show NVTT Settings",
        description="Show NVTT settings",
        default=False
    )

    # Texture loader paths
    bpy.types.Scene.gtatools_texture_path1 = StringProperty(
        name="System Textures Path",
        description="Path to GTA system textures folder",
        default=r"E:\Project MTA\System_textures",
        subtype='DIR_PATH'
    )
    bpy.types.Scene.gtatools_texture_path2 = StringProperty(
        name="Blend Folder Path",
        description="Path to folder where .blend file is located",
        default="",
        subtype='DIR_PATH'
    )

    # Bake settings (calibrated for 3Ds Max-like output)
    bpy.types.Scene.gtatools_bake_ambient = FloatProperty(
        name="Ambient",
        description="Base ambient light (lower = darker shadows)",
        default=0.10,
        min=0.0,
        max=0.5
    )
    bpy.types.Scene.gtatools_bake_intensity = FloatProperty(
        name="Intensity",
        description="Light intensity multiplier (lower = darker)",
        default=0.05,
        min=0.0001,
        max=0.5
    )
    bpy.types.Scene.gtatools_bake_gamma = FloatProperty(
        name="Gamma",
        description="Gamma correction (lower = darker)",
        default=0.50,
        min=0.1,
        max=3.0
    )

    # V offset for night prelight
    bpy.types.Scene.gtatools_v_offset = FloatProperty(
        name="V Offset",
        description="Brightness offset like 3Ds Max Adjust Color V (-80 for night)",
        default=0.0,
        min=-100.0,
        max=100.0
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
        description="Light scatter intensity",
        default=1.0,
        min=0.1,
        max=5.0
    )
    bpy.types.Scene.gtatools_scatter_falloff = FloatProperty(
        name="Falloff",
        description="How quickly light fades (higher = faster falloff)",
        default=1.5,
        min=0.5,
        max=5.0
    )
    bpy.types.Scene.gtatools_scatter_iterations = IntProperty(
        name="Iterations",
        description="How many neighbor layers to affect",
        default=3,
        min=1,
        max=10
    )
    bpy.types.Scene.gtatools_scatter_radius = FloatProperty(
        name="Radius",
        description="Search radius for nearby faces (0 = auto based on face size)",
        default=0.0,
    )

    # Export settings
    bpy.types.Scene.gtatools_export_all_skip_txd = BoolProperty(
        name="Skip TXD",
        description="Do not export TXD with Export All",
        default=False
    )

    print("[GTA Tools Panel] Addon registered!")


def unregister():
    # Remove UV grid draw handler
    global _uv_grid_draw_handler, _uv_grid_visible
    if _uv_grid_draw_handler is not None:
        bpy.types.SpaceImageEditor.draw_handler_remove(_uv_grid_draw_handler, 'WINDOW')
        _uv_grid_draw_handler = None
    _uv_grid_visible = False

    del bpy.types.Scene.gtatools_uv_grid_cols
    del bpy.types.Scene.gtatools_uv_grid_rows
    del bpy.types.Scene.gtatools_uv_grid_align
    del bpy.types.Scene.gtatools_uv_link_islands
    del bpy.types.Scene.gtatools_nvtt_path
    del bpy.types.Scene.gtatools_txd_use_gpu
    del bpy.types.Scene.gtatools_show_nvtt_settings
    del bpy.types.Scene.gtatools_texture_path2
    del bpy.types.Scene.gtatools_texture_path1
    del bpy.types.Scene.gtatools_export_all_skip_txd
    del bpy.types.Scene.gtatools_scatter_radius
    del bpy.types.Scene.gtatools_scatter_iterations
    del bpy.types.Scene.gtatools_scatter_falloff
    del bpy.types.Scene.gtatools_scatter_intensity
    del bpy.types.Scene.gtatools_fill_color
    del bpy.types.Object.gtatools_fill_colors
    del bpy.types.Scene.gtatools_v_offset
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
