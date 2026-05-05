# INU_tools.data.surface_materials — GTA SA COL surface material definitions

import bpy



# GTA SA surface material IDs (0-178)
# Format: (id, name, description)
GTA_SA_SURFACE_MATERIALS = [
    (0, "DEFAULT", "Default surface"),
    (1, "TARMAC", "Tarmac (asphalt)"),
    (2, "TARMAC_FUCKED", "Damaged tarmac"),
    (3, "TARMAC_REALLYFUCKED", "Heavily damaged tarmac"),
    (4, "PAVEMENT", "Pavement (sidewalk)"),
    (5, "PAVEMENT_FUCKED", "Damaged pavement"),
    (6, "GRAVEL", "Gravel"),
    (7, "FUCKED_CONCRETE", "Damaged concrete"),
    (8, "PAINTED_GROUND", "Painted ground"),
    (9, "GRASS_SHORT_LUSH", "Grass short lush"),
    (10, "GRASS_MEDIUM_LUSH", "Grass medium lush"),
    (11, "GRASS_LONG_LUSH", "Grass long lush"),
    (12, "GRASS_SHORT_DRY", "Grass short dry"),
    (13, "GRASS_MEDIUM_DRY", "Grass medium dry"),
    (14, "GRASS_LONG_DRY", "Grass long dry"),
    (15, "GOLFGRASS_ROUGH", "Golf grass rough"),
    (16, "GOLFGRASS_SMOOTH", "Golf grass smooth"),
    (17, "STEEP_SLIDYGRASS", "Steep slidy grass"),
    (18, "STEEP_CLIFF", "Steep cliff"),
    (19, "FLOWERBED", "Flower bed"),
    (20, "MEADOW", "Meadow"),
    (21, "WASTEGROUND", "Waste ground"),
    (22, "WOODLANDGROUND", "Woodland ground"),
    (23, "VEGETATION", "Vegetation"),
    (24, "MUD_WET", "Mud wet"),
    (25, "MUD_DRY", "Mud dry"),
    (26, "DIRT", "Dirt"),
    (27, "DIRTTRACK", "Dirt track"),
    (28, "SAND_DEEP", "Sand deep"),
    (29, "SAND_MEDIUM", "Sand medium"),
    (30, "SAND_COMPACT", "Sand compact"),
    (31, "SAND_ARID", "Sand arid"),
    (32, "SAND_MORE", "Sand more"),
    (33, "SAND_BEACH", "Sand beach"),
    (34, "CONCRETE_BEACH", "Concrete beach"),
    (35, "ROCK_DRY", "Rock dry"),
    (36, "ROCK_WET", "Rock wet"),
    (37, "ROCK_CLIFF", "Rock cliff"),
    (38, "WATER_RIVERBED", "Water riverbed"),
    (39, "WATER_SHALLOW", "Water shallow"),
    (40, "CORNFIELD", "Corn field"),
    (41, "HEDGE", "Hedge"),
    (42, "WOOD_CRATES", "Wood crates"),
    (43, "WOOD_SOLID", "Wood solid"),
    (44, "WOOD_THIN", "Wood thin"),
    (45, "GLASS", "Glass"),
    (46, "GLASS_WINDOWS_LARGE", "Glass windows large"),
    (47, "GLASS_WINDOWS_SMALL", "Glass windows small"),
    (48, "EMPTY1", "Empty 1"),
    (49, "EMPTY2", "Empty 2"),
    (50, "GARAGE_DOOR", "Garage door"),
    (51, "THICK_METAL_PLATE", "Thick metal plate"),
    (52, "SCAFFOLD_POLE", "Scaffold pole"),
    (53, "LAMP_POST", "Lamp post"),
    (54, "METAL_GATE", "Metal gate"),
    (55, "METAL_CHAIN_FENCE", "Metal chain fence"),
    (56, "GIRDER", "Girder"),
    (57, "FIRE_HYDRANT", "Fire hydrant"),
    (58, "CONTAINER", "Container"),
    (59, "NEWS_VENDOR", "News vendor"),
    (60, "WHEELBASE", "Wheelbase"),
    (61, "CARDBOARDBOX", "Cardboard box"),
    (62, "PED", "Ped (body)"),
    (63, "CAR", "Car"),
    (64, "CAR_PANEL", "Car panel"),
    (65, "CAR_MOVINGCOMPONENT", "Car moving component"),
    (66, "TRANSPARENT_CLOTH", "Transparent cloth"),
    (67, "RUBBER", "Rubber"),
    (68, "PLASTIC", "Plastic"),
    (69, "TRANSPARENT_STONE", "Transparent stone"),
    (70, "WOOD_BENCH", "Wood bench"),
    (71, "CARPET", "Carpet"),
    (72, "FLOORBOARD", "Floorboard"),
    (73, "STAIRSWOOD", "Stairs wood"),
    (74, "P_SAND", "Sand (phys)"),
    (75, "P_SAND_DENSE", "Sand dense (phys)"),
    (76, "P_SAND_ARID", "Sand arid (phys)"),
    (77, "P_SAND_COMPACT", "Sand compact (phys)"),
    (78, "P_SAND_ROCKY", "Sand rocky (phys)"),
    (79, "P_SAND_BEACH", "Sand beach (phys)"),
    (80, "P_GRASS_SHORT", "Grass short (phys)"),
    (81, "P_GRASS_MEADOW", "Grass meadow (phys)"),
    (82, "P_GRASS_DRY", "Grass dry (phys)"),
    (83, "P_WOODLAND", "Woodland (phys)"),
    (84, "P_WOODDENSE", "Wood dense (phys)"),
    (85, "P_ROADSIDE", "Roadside (phys)"),
    (86, "P_ROADSIDEDES", "Roadside desert (phys)"),
    (87, "P_FLOWERBED", "Flowerbed (phys)"),
    (88, "P_WASTEGROUND", "Waste ground (phys)"),
    (89, "P_CONCRETE", "Concrete (phys)"),
    (90, "P_OFFICEDESK", "Office desk"),
    (91, "P_711SHELF1", "711 Shelf 1"),
    (92, "P_711SHELF2", "711 Shelf 2"),
    (93, "P_711SHELF3", "711 Shelf 3"),
    (94, "P_RESTURANTTABLE", "Restaurant table"),
    (95, "P_BARTABLE", "Bar table"),
    (96, "P_UNDERWATERLUSH", "Underwater lush"),
    (97, "P_UNDERWATERBARREN", "Underwater barren"),
    (98, "P_UNDERWATERCORAL", "Underwater coral"),
    (99, "P_UNDERWATERDEEP", "Underwater deep"),
    (100, "P_RIVERBED", "Riverbed"),
    (101, "P_RUBBLE", "Rubble"),
    (102, "P_BEDROOMFLOOR", "Bedroom floor"),
    (103, "P_KITCHENFLOOR", "Kitchen floor"),
    (104, "P_LIVINGROOMFLOOR", "Livingroom floor"),
    (105, "P_CORRIDORFLOOR", "Corridor floor"),
    (106, "P_711FLOOR", "711 floor"),
    (107, "P_ABORETUMFLOOR", "Fast food floor"),
    (108, "P_SKANKYFLOOR", "Skanky floor"),
    (109, "P_MOUNTAIN", "Mountain"),
    (110, "P_MARSH", "Marsh"),
    (111, "P_BUSHY", "Bushy"),
    (112, "P_BUSHYMIX", "Bushy mix"),
    (113, "P_BUSHYDRY", "Bushy dry"),
    (114, "P_BUSHYMID", "Bushy mid"),
    (115, "P_GRASSWEEFLOWERS", "Grass wee flowers"),
    (116, "P_GRASSDRYTALL", "Grass dry tall"),
    (117, "P_GRASSLUSHTALL", "Grass lush tall"),
    (118, "P_GRASSGREENMIX", "Grass green mix"),
    (119, "P_GRASSBROWNMIX", "Grass brown mix"),
    (120, "P_GRASSLOW", "Grass low"),
    (121, "P_GRASSROCKY", "Grass rocky"),
    (122, "P_GRASSSMALLTREES", "Grass small trees"),
    (123, "P_DIRTROCKY", "Dirt rocky"),
    (124, "P_DIRTWEEDS", "Dirt weeds"),
    (125, "P_GRASSWEEDS", "Grass weeds"),
    (126, "P_RIVEREDGE", "River edge"),
    (127, "P_POOLSIDE", "Poolside"),
    (128, "P_FORESTSTUMPS", "Forest stumps"),
    (129, "P_FORESTSTICKS", "Forest sticks"),
    (130, "P_FORESTLEAVES", "Forest leaves"),
    (131, "P_DESERTROCKS", "Desert rocks"),
    (132, "P_FORRESTDRY", "Forest dry"),
    (133, "P_SPARSEFLOWERS", "Sparse flowers"),
    (134, "P_BUILDINGSITE", "Building site"),
    (135, "P_DOCKLANDS", "Docklands"),
    (136, "P_INDUSTRIAL", "Industrial"),
    (137, "P_INDUSTJETTY", "Industrial jetty"),
    (138, "P_CONCRETELITTER", "Concrete litter"),
    (139, "P_ALLEYRUBISH", "Alley rubbish"),
    (140, "P_JUNKYARDPILES", "Junkyard piles"),
    (141, "P_JUNKYARDGRND", "Junkyard ground"),
    (142, "P_DUMP", "Dump"),
    (143, "P_CACTUSDENSE", "Cactus dense"),
    (144, "P_AIRPORTGND", "Airport ground"),
    (145, "P_CORNFIELD", "Cornfield (phys)"),
    (146, "P_YOURGRASS1", "Grass light"),
    (147, "P_YOURGRASS2", "Grass lighter"),
    (148, "P_YOURGRASS3", "Grass lighter 2"),
    (149, "P_GRASSMID1", "Grass mid 1"),
    (150, "P_GRASSMID2", "Grass mid 2"),
    (151, "P_GRASSDARK", "Grass dark"),
    (152, "P_GRASSDARK2", "Grass dark 2"),
    (153, "P_GRASSDIRTMIX", "Grass dirt mix"),
    (154, "P_RIVERBEDSTONE", "Riverbed stone"),
    (155, "P_RIVERBEDSHALLOW", "Riverbed shallow"),
    (156, "P_RIVERBEDWEEDS", "Riverbed weeds"),
    (157, "P_SEAWEED", "Seaweed"),
    (158, "DOOR", "Door"),
    (159, "PLASTICBARRIER", "Plastic barrier"),
    (160, "PARKGRASS", "Park grass"),
    (161, "STAIRSSTONE", "Stairs stone"),
    (162, "STAIRSMETAL", "Stairs metal"),
    (163, "STAIRSCARPET", "Stairs carpet"),
    (164, "FLOORMETAL", "Floor metal"),
    (165, "FLOORCONCRETE", "Floor concrete"),
    (166, "BIN_BAG", "Bin bag"),
    (167, "THIN_METAL_SHEET", "Thin metal sheet"),
    (168, "METAL_BARREL", "Metal barrel"),
    (169, "PLASTIC_CONE", "Plastic cone"),
    (170, "PLASTIC_DUMPSTER", "Plastic dumpster"),
    (171, "METAL_DUMPSTER", "Metal dumpster"),
    (172, "WOOD_PICKET_FENCE", "Wood picket fence"),
    (173, "WOOD_SLATTED_FENCE", "Wood slatted fence"),
    (174, "WOOD_RANCH_FENCE", "Wood ranch fence"),
    (175, "UNBREAKABLE_GLASS", "Unbreakable glass"),
    (176, "HAY_BALE", "Hay bale"),
    (177, "GORE", "Gore"),
    (178, "RAILTRACK", "Rail track"),
]

# Build enum items for Blender UI: (identifier, name, description)
COL_SURFACE_ENUM_ITEMS = [
    (str(sid), f"{sid}: {name}", desc)
    for sid, name, desc in GTA_SA_SURFACE_MATERIALS
]

# Surface material categories for grouped display
COL_SURFACE_CATEGORIES = [
    ("Default", [0]),
    ("Concrete", [1, 2, 3, 4, 5, 7, 8, 34, 89, 134, 135, 136, 137, 138, 139, 144, 165]),
    ("Gravel", [6, 101]),
    ("Grass", [9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 80, 81, 82, 83, 84, 85, 86, 87, 88,
               111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 125, 128, 129, 130, 132,
               133, 146, 147, 148, 149, 150, 151, 152, 153, 160]),
    ("Dirt", [22, 24, 25, 26, 27, 109, 110, 123, 124, 140, 141, 142]),
    ("Sand", [28, 29, 30, 31, 32, 33, 74, 75, 76, 77, 78, 79]),
    ("Glass", [45, 46, 47, 69, 175]),
    ("Wood", [42, 43, 44, 70, 72, 73, 172, 173, 174, 176]),
    ("Metal", [50, 51, 52, 53, 54, 55, 56, 57, 58, 162, 164, 167, 168, 171, 178]),
    ("Stone", [18, 35, 36, 37, 61, 154, 155, 161]),
    ("Vegetation", [23, 40, 41, 96, 97, 98, 99, 100, 126, 127, 131, 143, 145, 156, 157]),
    ("Water", [38, 39]),
    ("Misc", [48, 49, 59, 60, 62, 63, 64, 65, 66, 67, 68, 71, 90, 91, 92, 93, 94, 95,
              102, 103, 104, 105, 106, 107, 108, 158, 159, 163, 166, 169, 170, 177]),
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


def get_base_name_from_selection():
    """Get base model name from selected object"""
    from ..tools.model_utils import get_model_type
    obj = bpy.context.active_object
    if obj is None:
        return None

    model_type, base_name = get_model_type(obj)
    return base_name
