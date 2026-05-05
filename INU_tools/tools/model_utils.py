# INU_tools.tools.model_utils — Model detection utilities and geometry checks

import bpy
import bmesh



def _get_suffixes():
    """Get custom suffixes from scene settings or use defaults."""
    scene = bpy.context.scene
    return {
        'DFF': getattr(scene.inu_settings, 'gtatools_suffix_dff', '_DFF'),
        'LOD': getattr(scene.inu_settings, 'gtatools_suffix_lod', '_LOD'),
        'COL': getattr(scene.inu_settings, 'gtatools_suffix_col', '_COL'),
    }


def _get_prefixes():
    """Get custom prefixes from scene settings or use defaults."""
    scene = bpy.context.scene
    return {
        'DFF': getattr(scene.inu_settings, 'gtatools_prefix_dff', ''),
        'LOD': getattr(scene.inu_settings, 'gtatools_prefix_lod', 'LOD'),
        'COL': getattr(scene.inu_settings, 'gtatools_prefix_col', ''),
    }


def get_model_type(obj):
    """Определить тип модели по суффиксу или префиксу"""
    if obj is None:
        return None, None

    name = obj.name
    name_upper = name.upper()
    suffixes = _get_suffixes()
    prefixes = _get_prefixes()

    # Shadow mesh suffix (_SHA) — Rockstar/Kam's convention.
    # Treated as COL so IMG export packs it into the .col file; the COL
    # exporter's _is_shadow_mesh() then writes it into shadow mesh section
    # (non-blocking collision, used for bounds and bullet tests only).
    if name_upper.endswith('_SHA'):
        return 'COL', name[:-4]

    # Check suffixes first (higher priority)
    for model_type in ('LOD', 'COL', 'DFF'):
        sfx = suffixes[model_type]
        sfx_upper = sfx.upper()
        if sfx_upper and name_upper.endswith(sfx_upper):
            return model_type, name[:-len(sfx)]
        # Also check without separator (e.g. "modelLOD" if suffix is "_LOD")
        bare = sfx_upper.lstrip('_. ')
        if bare and sfx_upper != bare and name_upper.endswith(bare):
            return model_type, name[:-len(bare)]

    # Check prefixes
    for model_type in ('LOD', 'COL', 'DFF'):
        pfx = prefixes[model_type]
        pfx_upper = pfx.upper()
        if pfx_upper and name_upper.startswith(pfx_upper):
            return model_type, name[len(pfx):]

    # Модель без суффикса/префикса - считается DFF
    return 'DFF', name


def find_related_models(base_name):
    """Найти связанные модели (DFF, LOD, COL) по базовому имени"""
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
    """Найти модели DFF, LOD, COL только среди выделенных объектов"""
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


def _get_active_collection_objects():
    """Get mesh objects from active collection (including child collections)."""
    col = bpy.context.collection
    if col is None or col == bpy.context.scene.collection:
        return []
    objects = []
    def _collect(c):
        for obj in c.objects:
            if obj.type == 'MESH':
                objects.append(obj)
        for child in c.children:
            _collect(child)
    _collect(col)
    return objects


def find_all_selected_model_groups():
    """Find all DFF/LOD/COL model groups among selected objects, grouped by base_name.
    Falls back to active collection if nothing is selected."""
    groups = {}  # {base_name: {'DFF': obj, 'LOD': obj, 'COL': obj}}

    source = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    if not source:
        source = _get_active_collection_objects()

    for obj in source:
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
    """Получить базовое имя из выделенных моделей"""
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


# =============================================================================
# GEOMETRY CHECK FUNCTIONS
# =============================================================================

def check_loose_geometry(obj):
    """Проверить объект на висящие вершины и рёбра (не присоединённые к полигонам)"""
    if obj is None or obj.type != 'MESH':
        return None, None, "Не меш объект"

    bm = bmesh.new()
    bm.from_mesh(obj.data)

    # Находим висящие вершины (не принадлежат ни одному face)
    loose_verts = [v.index for v in bm.verts if not v.link_faces]

    # Находим висящие рёбра (не принадлежат ни одному face)
    loose_edges = [e.index for e in bm.edges if not e.link_faces]

    bm.free()

    return loose_verts, loose_edges, None


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
