# INU_tools.data.surface_materials — GTA SA COL surface material definitions

import bpy



# GTA SA surface material IDs (0-178)
# Format: (id, name, description)
GTA_SA_SURFACE_MATERIALS = [
    (0, "DEFAULT", "Стандартная поверхность (по умолчанию)"),
    (1, "TARMAC", "Асфальт — дорожное покрытие, хорошее сцепление"),
    (2, "TARMAC_FUCKED", "Потрескавшийся асфальт"),
    (3, "TARMAC_REALLYFUCKED", "Сильно разбитый асфальт"),
    (4, "PAVEMENT", "Тротуар — пешеходная плитка"),
    (5, "PAVEMENT_FUCKED", "Повреждённый тротуар"),
    (6, "GRAVEL", "Гравий — сыпучий камень, поднимает пыль"),
    (7, "FUCKED_CONCRETE", "Разрушенный бетон"),
    (8, "PAINTED_GROUND", "Крашеный бетон / дорожная разметка"),
    (9, "GRASS_SHORT_LUSH", "Трава короткая сочная (зелёная)"),
    (10, "GRASS_MEDIUM_LUSH", "Трава средняя сочная"),
    (11, "GRASS_LONG_LUSH", "Трава высокая сочная"),
    (12, "GRASS_SHORT_DRY", "Трава короткая сухая (жёлтая)"),
    (13, "GRASS_MEDIUM_DRY", "Трава средняя сухая"),
    (14, "GRASS_LONG_DRY", "Трава высокая сухая"),
    (15, "GOLFGRASS_ROUGH", "Газон гольф-поля — грубый (рафф)"),
    (16, "GOLFGRASS_SMOOTH", "Газон гольф-поля — гладкий (грин)"),
    (17, "STEEP_SLIDYGRASS", "Крутая скользкая трава — машина скатывается"),
    (18, "STEEP_CLIFF", "Крутой утёс — непроходимый склон"),
    (19, "FLOWERBED", "Клумба — цветочная грядка"),
    (20, "MEADOW", "Луг"),
    (21, "WASTEGROUND", "Пустырь — заброшенная земля"),
    (22, "WOODLANDGROUND", "Лесная почва"),
    (23, "VEGETATION", "Растительность — кусты и листва"),
    (24, "MUD_WET", "Мокрая грязь — вязкая, брызги"),
    (25, "MUD_DRY", "Сухая грязь"),
    (26, "DIRT", "Земля / грунт, поднимает пыль"),
    (27, "DIRTTRACK", "Грунтовая дорога"),
    (28, "SAND_DEEP", "Глубокий песок — вязкий, тормозит машину"),
    (29, "SAND_MEDIUM", "Песок средней плотности"),
    (30, "SAND_COMPACT", "Плотный утрамбованный песок"),
    (31, "SAND_ARID", "Пустынный песок"),
    (32, "SAND_MORE", "Песок (дополнительный вариант)"),
    (33, "SAND_BEACH", "Пляжный песок"),
    (34, "CONCRETE_BEACH", "Бетон у пляжа / набережная"),
    (35, "ROCK_DRY", "Сухой камень (скала)"),
    (36, "ROCK_WET", "Мокрый камень"),
    (37, "ROCK_CLIFF", "Скалистый утёс"),
    (38, "WATER_RIVERBED", "Дно реки под водой"),
    (39, "WATER_SHALLOW", "Мелководье — брызги воды"),
    (40, "CORNFIELD", "Кукурузное поле"),
    (41, "HEDGE", "Живая изгородь — плотные кусты"),
    (42, "WOOD_CRATES", "Деревянные ящики"),
    (43, "WOOD_SOLID", "Прочное дерево — доски, брус"),
    (44, "WOOD_THIN", "Тонкое дерево — фанера, ломается"),
    (45, "GLASS", "Стекло — бьётся при ударе"),
    (46, "GLASS_WINDOWS_LARGE", "Большое оконное стекло"),
    (47, "GLASS_WINDOWS_SMALL", "Малое оконное стекло"),
    (48, "EMPTY1", "Пусто — не используется"),
    (49, "EMPTY2", "Пусто — не используется"),
    (50, "GARAGE_DOOR", "Гаражная дверь (металл)"),
    (51, "THICK_METAL_PLATE", "Толстая металлическая плита"),
    (52, "SCAFFOLD_POLE", "Труба строительных лесов (металл)"),
    (53, "LAMP_POST", "Фонарный столб"),
    (54, "METAL_GATE", "Металлические ворота"),
    (55, "METAL_CHAIN_FENCE", "Забор сетка-рабица — пули пролетают насквозь"),
    (56, "GIRDER", "Металлическая балка / ферма"),
    (57, "FIRE_HYDRANT", "Пожарный гидрант — при сбитии бьёт вода"),
    (58, "CONTAINER", "Грузовой контейнер (металл)"),
    (59, "NEWS_VENDOR", "Газетный автомат / стойка"),
    (60, "WHEELBASE", "Колёсный отбойник / основание"),
    (61, "CARDBOARDBOX", "Картонная коробка — лёгкая"),
    (62, "PED", "Тело персонажа (пешехода)"),
    (63, "CAR", "Кузов машины (металл)"),
    (64, "CAR_PANEL", "Панель кузова машины"),
    (65, "CAR_MOVINGCOMPONENT", "Подвижная деталь машины (дверь, капот)"),
    (66, "TRANSPARENT_CLOTH", "Прозрачная ткань / тент"),
    (67, "RUBBER", "Резина — шины, покрышки"),
    (68, "PLASTIC", "Пластик"),
    (69, "TRANSPARENT_STONE", "Прозрачный камень (спец.)"),
    (70, "WOOD_BENCH", "Деревянная скамейка"),
    (71, "CARPET", "Ковёр — приглушённые шаги"),
    (72, "FLOORBOARD", "Дощатый пол"),
    (73, "STAIRSWOOD", "Деревянная лестница"),
    (74, "P_SAND", "Песок — зона генерации растительности"),
    (75, "P_SAND_DENSE", "Плотный песок — зона растительности"),
    (76, "P_SAND_ARID", "Пустынный песок — зона растительности"),
    (77, "P_SAND_COMPACT", "Утрамбованный песок — зона растительности"),
    (78, "P_SAND_ROCKY", "Каменистый песок — зона растительности"),
    (79, "P_SAND_BEACH", "Пляжный песок — зона растительности"),
    (80, "P_GRASS_SHORT", "Короткая трава — процедурная генерация"),
    (81, "P_GRASS_MEADOW", "Луговая трава — процедурная генерация"),
    (82, "P_GRASS_DRY", "Сухая трава — процедурная генерация"),
    (83, "P_WOODLAND", "Лесная земля — генерация растительности"),
    (84, "P_WOODDENSE", "Густой лес — генерация растительности"),
    (85, "P_ROADSIDE", "Обочина — генерация травы"),
    (86, "P_ROADSIDEDES", "Обочина в пустыне — генерация растительности"),
    (87, "P_FLOWERBED", "Клумба — генерация цветов"),
    (88, "P_WASTEGROUND", "Пустырь — генерация растительности"),
    (89, "P_CONCRETE", "Бетон — без растительности"),
    (90, "P_OFFICEDESK", "Офисный стол"),
    (91, "P_711SHELF1", "Полка магазина 24/7 (1)"),
    (92, "P_711SHELF2", "Полка магазина 24/7 (2)"),
    (93, "P_711SHELF3", "Полка магазина 24/7 (3)"),
    (94, "P_RESTURANTTABLE", "Стол в ресторане"),
    (95, "P_BARTABLE", "Барная стойка"),
    (96, "P_UNDERWATERLUSH", "Подводное дно с растительностью"),
    (97, "P_UNDERWATERBARREN", "Голое подводное дно"),
    (98, "P_UNDERWATERCORAL", "Коралловое дно"),
    (99, "P_UNDERWATERDEEP", "Глубокое подводное дно"),
    (100, "P_RIVERBED", "Дно реки — генерация водорослей"),
    (101, "P_RUBBLE", "Строительный мусор / щебень"),
    (102, "P_BEDROOMFLOOR", "Пол спальни"),
    (103, "P_KITCHENFLOOR", "Пол кухни"),
    (104, "P_LIVINGROOMFLOOR", "Пол гостиной"),
    (105, "P_CORRIDORFLOOR", "Пол коридора"),
    (106, "P_711FLOOR", "Пол магазина 24/7"),
    (107, "P_ABORETUMFLOOR", "Пол кафе / фастфуда"),
    (108, "P_SKANKYFLOOR", "Грязный пол (притон, трущобы)"),
    (109, "P_MOUNTAIN", "Горная поверхность — генерация растительности"),
    (110, "P_MARSH", "Болото — генерация растительности"),
    (111, "P_BUSHY", "Кустарник — процедурная генерация"),
    (112, "P_BUSHYMIX", "Смешанный кустарник — генерация"),
    (113, "P_BUSHYDRY", "Сухой кустарник — генерация"),
    (114, "P_BUSHYMID", "Средний кустарник — генерация"),
    (115, "P_GRASSWEEFLOWERS", "Трава с мелкими цветами — генерация"),
    (116, "P_GRASSDRYTALL", "Высокая сухая трава — генерация"),
    (117, "P_GRASSLUSHTALL", "Высокая сочная трава — генерация"),
    (118, "P_GRASSGREENMIX", "Смесь зелёной травы — генерация"),
    (119, "P_GRASSBROWNMIX", "Смесь бурой травы — генерация"),
    (120, "P_GRASSLOW", "Низкая трава — генерация"),
    (121, "P_GRASSROCKY", "Трава на камнях — генерация"),
    (122, "P_GRASSSMALLTREES", "Трава с деревцами — генерация"),
    (123, "P_DIRTROCKY", "Каменистая земля — генерация"),
    (124, "P_DIRTWEEDS", "Земля с сорняками — генерация"),
    (125, "P_GRASSWEEDS", "Трава с сорняками — генерация"),
    (126, "P_RIVEREDGE", "Берег реки — генерация растительности"),
    (127, "P_POOLSIDE", "Край бассейна"),
    (128, "P_FORESTSTUMPS", "Лес с пнями — генерация"),
    (129, "P_FORESTSTICKS", "Лес с ветками — генерация"),
    (130, "P_FORESTLEAVES", "Лесная подстилка (листва) — генерация"),
    (131, "P_DESERTROCKS", "Пустынные камни — генерация"),
    (132, "P_FORRESTDRY", "Сухой лес — генерация"),
    (133, "P_SPARSEFLOWERS", "Редкие цветы — генерация"),
    (134, "P_BUILDINGSITE", "Стройплощадка"),
    (135, "P_DOCKLANDS", "Доки / причал"),
    (136, "P_INDUSTRIAL", "Промзона"),
    (137, "P_INDUSTJETTY", "Промышленный причал"),
    (138, "P_CONCRETELITTER", "Бетон с мусором"),
    (139, "P_ALLEYRUBISH", "Мусор в переулке"),
    (140, "P_JUNKYARDPILES", "Кучи на свалке"),
    (141, "P_JUNKYARDGRND", "Земля на свалке"),
    (142, "P_DUMP", "Мусорная свалка"),
    (143, "P_CACTUSDENSE", "Заросли кактусов — генерация"),
    (144, "P_AIRPORTGND", "Земля аэропорта"),
    (145, "P_CORNFIELD", "Кукурузное поле — генерация"),
    (146, "P_YOURGRASS1", "Пользовательская трава 1 (светлая)"),
    (147, "P_YOURGRASS2", "Пользовательская трава 2"),
    (148, "P_YOURGRASS3", "Пользовательская трава 3"),
    (149, "P_GRASSMID1", "Средняя трава 1 — генерация"),
    (150, "P_GRASSMID2", "Средняя трава 2 — генерация"),
    (151, "P_GRASSDARK", "Тёмная трава — генерация"),
    (152, "P_GRASSDARK2", "Тёмная трава 2 — генерация"),
    (153, "P_GRASSDIRTMIX", "Трава с проплешинами земли — генерация"),
    (154, "P_RIVERBEDSTONE", "Каменистое дно реки"),
    (155, "P_RIVERBEDSHALLOW", "Мелкое дно реки"),
    (156, "P_RIVERBEDWEEDS", "Дно реки с водорослями"),
    (157, "P_SEAWEED", "Морские водоросли"),
    (158, "DOOR", "Дверь"),
    (159, "PLASTICBARRIER", "Пластиковый барьер / отбойник"),
    (160, "PARKGRASS", "Парковый газон"),
    (161, "STAIRSSTONE", "Каменная лестница"),
    (162, "STAIRSMETAL", "Металлическая лестница"),
    (163, "STAIRSCARPET", "Лестница с ковровым покрытием"),
    (164, "FLOORMETAL", "Металлический пол"),
    (165, "FLOORCONCRETE", "Бетонный пол"),
    (166, "BIN_BAG", "Мусорный пакет"),
    (167, "THIN_METAL_SHEET", "Тонкий металлический лист"),
    (168, "METAL_BARREL", "Металлическая бочка"),
    (169, "PLASTIC_CONE", "Дорожный конус (пластик)"),
    (170, "PLASTIC_DUMPSTER", "Пластиковый мусорный бак"),
    (171, "METAL_DUMPSTER", "Металлический мусорный бак"),
    (172, "WOOD_PICKET_FENCE", "Деревянный штакетник"),
    (173, "WOOD_SLATTED_FENCE", "Дощатый забор"),
    (174, "WOOD_RANCH_FENCE", "Забор ранчо (жерди)"),
    (175, "UNBREAKABLE_GLASS", "Небьющееся стекло"),
    (176, "HAY_BALE", "Тюк сена"),
    (177, "GORE", "Кровь / останки (gore)"),
    (178, "RAILTRACK", "Железнодорожные рельсы"),
]

# Build enum items for Blender UI: (identifier, name, description)
COL_SURFACE_ENUM_ITEMS = [
    (str(sid), f"{sid}: {name}", desc)
    for sid, name, desc in GTA_SA_SURFACE_MATERIALS
]

# Surface material categories for grouped display.
#
# Grouping mirrors *Collision File Editor II* (by Steve M) exactly — the
# de-facto reference tool — so IDs land in the same category modders
# expect (e.g. P_FLOWERBED 87 under Dirt, not Grass). Verified against
# the MTA wiki (same source): covers every ID 0-178 once, no gaps.
COL_SURFACE_CATEGORIES = [
    ("Default", [0, 1, 2, 3]),
    ("Concrete", [4, 5, 7, 8, 34, 89, 127, 135, 136, 137, 138, 139, 144, 165]),
    ("Gravel", [6, 85, 101, 134, 140]),
    ("Grass", [9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 80, 81, 82, 115, 116, 117, 118, 119, 120,
               121, 122, 125, 146, 147, 148, 149, 150, 151, 152, 153, 160]),
    ("Dirt", [19, 21, 22, 24, 25, 26, 27, 40, 83, 84, 87, 88, 100, 110, 123, 124, 126, 128, 129,
              130, 132, 133, 141, 142, 145, 155, 156]),
    ("Sand", [28, 29, 30, 31, 32, 33, 74, 75, 76, 77, 78, 79, 86, 96, 97, 98, 99, 131, 143, 157]),
    ("Glass", [45, 46, 47, 175]),
    ("Wood", [42, 43, 44, 70, 72, 73, 172, 173, 174]),
    ("Metal", [50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 63, 64, 65, 162, 164, 167, 168, 171]),
    ("Stone", [18, 35, 36, 37, 69, 109, 154, 161]),
    ("Vegetation", [23, 41, 111, 112, 113, 114]),
    ("Water", [38, 39]),
    ("Misc", [48, 49, 60, 61, 62, 66, 67, 68, 71, 90, 91, 92, 93, 94, 95, 102, 103, 104, 105, 106,
              107, 108, 158, 159, 163, 166, 169, 170, 176, 177, 178]),
]

# Build lookup: surface_id -> category name
_surface_id_to_category = {}
for _cat_name, _cat_ids in COL_SURFACE_CATEGORIES:
    for _sid in _cat_ids:
        _surface_id_to_category[_sid] = _cat_name


def get_col_surface_id(mat):
    """Get COL surface ID from material property or fallback."""
    if mat is None:
        return 0
    if hasattr(mat, 'inu'):
        return mat.inu.col_mat_index
    return 0


def get_surface_name(surface_id):
    """Get surface name by ID."""
    for sid, name, _ in GTA_SA_SURFACE_MATERIALS:
        if sid == surface_id:
            return name
    return "DEFAULT"


# Fast id -> description lookup (built once at import).
_surface_id_to_desc = {sid: desc for sid, name, desc in GTA_SA_SURFACE_MATERIALS}

# ── Surfaces on which vanilla plants.dat spawns procedural grass/plants ──
# Источник — data/plants.dat игры: перечислены surface-имена, на которых
# движок генерирует растительность (CPlantMgr). Многие «базовые» травы
# (9-14), песок (28-32), лес/поле (22, 40) и P_SAND (74-77) её ТОЖЕ
# генерируют, а не только P_*-поверхности — но в описаниях это раньше было
# помечено непоследовательно. Набор даёт единый источник истины; пометку
# «— генерация» дописывает get_surface_desc, если её ещё нет в тексте.
PLANTS_GENERATING_IDS = frozenset({
    3,                                    # TARMAC_REALLYFUCKED
    9, 10, 11, 12, 13, 14,                # базовая трава GRASS_*_LUSH/DRY
    22, 40,                               # WOODLANDGROUND, CORNFIELD
    28, 29, 30, 31, 32,                   # SAND_DEEP/MEDIUM/COMPACT/ARID/MORE
    74, 75, 76, 77,                       # P_SAND / P_SAND_DENSE/ARID/COMPACT
    80, 81, 82, 83, 84, 86,               # P_GRASS_SHORT/MEADOW/DRY, P_WOODLAND/DENSE, …
    113, 115, 116, 117,                   # P_BUSHYDRY, P_GRASSWEEFLOWERS/DRYTALL/LUSHTALL
    118, 119, 120, 121, 122,              # P_GRASSGREENMIX/BROWNMIX/LOW/ROCKY/SMALLTREES
    128,                                  # P_FORESTSTUMPS
    146, 147, 148,                        # P_YOURGRASS1/2/3 (plants: P_GRASSLIGHT/LIGHTER/2)
    149, 150, 151, 152, 153,              # P_GRASSMID1/2, P_GRASSDARK/2, P_GRASSDIRTMIX
})


def generates_plants(surface_id):
    """True, если на этой поверхности vanilla plants.dat спавнит траву."""
    try:
        return int(surface_id) in PLANTS_GENERATING_IDS
    except (TypeError, ValueError):
        return False


def get_surface_desc(surface_id):
    """Human-readable description for a surface ID (empty if unknown).

    Для поверхностей из plants.dat дописываем «— генерация», если пометки
    ещё нет в тексте — чтобы базовая трава (9-14), песок и т.п. были помечены
    так же, как P_*-поверхности."""
    try:
        sid = int(surface_id)
    except (TypeError, ValueError):
        return ""
    desc = _surface_id_to_desc.get(sid, "")
    if sid in PLANTS_GENERATING_IDS and "генерац" not in desc.lower():
        desc = (desc + " — генерация") if desc else "генерация"
    return desc


# ── Per-surface viewport colors ──────────────────────────────────────
# Colour COL materials by surface type so they're readable in the
# viewport (Solid shading → Color: Material), like a COL editor. Each
# category has a base hue; within a category every ID gets its own
# shade (brightness / slight hue shift) so no two surfaces look alike.

# Base RGB per category (0..1). Chosen to be intuitive and mutually
# distinct: grass green, water blue, sand tan, metal steel, etc.
_CATEGORY_BASE_RGB = {
    "Default":    (0.55, 0.55, 0.55),
    "Concrete":   (0.66, 0.66, 0.70),
    "Gravel":     (0.52, 0.47, 0.40),
    "Grass":      (0.24, 0.62, 0.18),
    "Dirt":       (0.46, 0.31, 0.16),
    "Sand":       (0.86, 0.74, 0.42),
    "Glass":      (0.55, 0.82, 0.90),
    "Wood":       (0.60, 0.40, 0.20),
    "Metal":      (0.52, 0.58, 0.68),
    "Stone":      (0.50, 0.46, 0.42),
    "Vegetation": (0.16, 0.50, 0.34),
    "Water":      (0.15, 0.40, 0.82),
    "Misc":       (0.62, 0.36, 0.62),
}

# category name -> ordered list of IDs (for per-ID shade offset).
_category_ids = {cat: list(ids) for cat, ids in COL_SURFACE_CATEGORIES}


def get_surface_color(surface_id):
    """RGBA viewport colour for a surface ID: category hue + per-ID
    variation so every material gets a distinct shade."""
    import colorsys
    try:
        sid = int(surface_id)
    except (TypeError, ValueError):
        sid = 0
    cat = _surface_id_to_category.get(sid, "Misc")
    base = _CATEGORY_BASE_RGB.get(cat, (0.55, 0.55, 0.55))
    ids = _category_ids.get(cat, [sid])
    idx = ids.index(sid) if sid in ids else 0
    n = max(1, len(ids))
    frac = idx / n  # 0..1 position within the category

    h, s, v = colorsys.rgb_to_hsv(*base)
    # Slight hue drift (±0.03) and brightness spread across the category
    # so neighbouring IDs read as clearly different shades of one hue.
    h = (h + (frac - 0.5) * 0.06) % 1.0
    v = min(1.0, max(0.22, v * (0.72 + 0.55 * frac)))
    s = min(1.0, max(0.12, s * (0.85 + 0.30 * ((idx % 3) / 2.0))))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def get_surface_material_name(surface_id):
    """Canonical material name for a surface: ``<id>_<NAME>`` — e.g.
    ``9_GRASS_SHORT_LUSH``."""
    return f"{int(surface_id)}_{get_surface_name(surface_id)}"


# ── Favorites ────────────────────────────────────────────────────────
# The user can star "important" surface materials so they float to the
# top of the picker. Persisted as a small JSON file in the user data
# directory (survives .blend files and Blender restarts — no need to
# save_userpref). Cached in-process so draw() doesn't hit disk each frame.

_FAV_FILE = 'col_surface_favorites.json'
_fav_cache = None  # None = not loaded yet; set of ints once loaded


def _fav_path():
    import os
    from ..tools import user_data
    return os.path.join(user_data.get_user_data_dir(), _FAV_FILE)


def get_favorites():
    """Set of favorited surface IDs (loaded from disk once, then cached)."""
    global _fav_cache
    if _fav_cache is None:
        _fav_cache = set()
        try:
            import json
            with open(_fav_path(), encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                _fav_cache = {int(x) for x in data}
        except Exception:
            _fav_cache = set()
    return _fav_cache


def is_favorite(surface_id):
    try:
        return int(surface_id) in get_favorites()
    except (TypeError, ValueError):
        return False


def toggle_favorite(surface_id):
    """Add/remove a surface ID from favorites. Returns the new state
    (True = now favorited). Writes the JSON file immediately."""
    global _fav_cache
    sid = int(surface_id)
    favs = set(get_favorites())
    if sid in favs:
        favs.discard(sid)
        now = False
    else:
        favs.add(sid)
        now = True
    _fav_cache = favs
    try:
        import json
        with open(_fav_path(), 'w', encoding='utf-8') as f:
            json.dump(sorted(favs), f)
    except Exception as e:
        print(f"[INU] save col surface favorites failed: {e}")
    return now


# ── COLPOINT names for plants.dat ────────────────────────────────────
# Vanilla plants.dat uses COLPOINT_SURFACETYPE_* names. Ours match for
# all but a handful the game abbreviates — these overrides map surface ID
# to the exact name the engine expects (so exported grass actually
# generates), plus the reverse for resolving imported entries.
_COLPOINT_NAME_OVERRIDE = {
    118: "P_GRASSGRNMIX",   # our P_GRASSGREENMIX
    119: "P_GRASSBRNMIX",   # our P_GRASSBROWNMIX
    146: "P_GRASSLIGHT",    # our P_YOURGRASS1
    147: "P_GRASSLIGHTER",  # our P_YOURGRASS2
    148: "P_GRASSLIGHTER2",  # our P_YOURGRASS3
}
_COLPOINT_NAME_TO_ID = {name: sid for sid, name in _COLPOINT_NAME_OVERRIDE.items()}
_OUR_NAME_TO_ID = {name: sid for sid, name, _ in GTA_SA_SURFACE_MATERIALS}


def get_colpoint_name(surface_id):
    """Exact COLPOINT surface name for plants.dat (game-matchable)."""
    try:
        sid = int(surface_id)
    except (TypeError, ValueError):
        return "DEFAULT"
    return _COLPOINT_NAME_OVERRIDE.get(sid, get_surface_name(sid))


def resolve_surface_id(name):
    """Surface ID for a name — accepts both our names and the COLPOINT
    abbreviations found in plants.dat. Returns None if unknown."""
    if name in _OUR_NAME_TO_ID:
        return _OUR_NAME_TO_ID[name]
    return _COLPOINT_NAME_TO_ID.get(name)


def get_base_name_from_selection():
    """Get base model name from selected object"""
    from ..tools.model_utils import get_model_type
    obj = bpy.context.active_object
    if obj is None:
        return None

    model_type, base_name = get_model_type(obj)
    return base_name
