# INU_tools.core.surface_translate
# Cross-game COL surface-ID translation.
#
# Each game has its own surface enum:
#   GTA III: 0..83  (~84 entries)
#   GTA VC:  0..84  (~85 entries)
#   GTA SA:  0..178 (~179 entries)
#
# IDs do not align across games — surface 5 in SA (PAVEMENT) is not
# the same material as surface 5 in III. When porting collision
# between games, the writer routes IDs through a category-keyed
# canonical layer here:
#
#     game_id → CATEGORY → other_game_id
#
# Unmapped IDs fall through to CATEGORY_DEFAULT which every game has
# at index 0 — safe but loses the original material distinction.
# Better than writing an arbitrary byte that the target game reads
# as garbage offset into a too-short table.

from typing import Dict, Optional


# ── Canonical categories ─────────────────────────────────────────
# Twelve broad material families covering ~95% of vanilla COL faces.
# More specific subtypes (TARMAC_FUCKED, MUD_DRY etc.) collapse to
# their parent here — we trade detail for cross-game portability.

CATEGORY_DEFAULT = 0
CATEGORY_TARMAC  = 1   # paved road
CATEGORY_GRASS   = 2
CATEGORY_DIRT    = 3   # unpaved earth
CATEGORY_GRAVEL  = 4
CATEGORY_MUD     = 5
CATEGORY_SAND    = 6
CATEGORY_WOOD    = 7
CATEGORY_METAL   = 8
CATEGORY_STONE   = 9   # concrete, brick, paving stones
CATEGORY_GLASS   = 10
CATEGORY_WATER   = 11


# ── Per-game ID → category maps ──────────────────────────────────
# Entries are best-effort; the goal is "won't crash and looks
# reasonable", not "byte-perfect cross-game fidelity".

_SA_ID_TO_CATEGORY: Dict[int, int] = {
    0:  CATEGORY_DEFAULT,
    1:  CATEGORY_TARMAC,
    2:  CATEGORY_TARMAC,    # TARMAC_FUCKED
    3:  CATEGORY_TARMAC,
    4:  CATEGORY_TARMAC,    # TARMAC_REALLY_FUCKED
    5:  CATEGORY_STONE,     # PAVEMENT
    6:  CATEGORY_STONE,
    7:  CATEGORY_GRAVEL,
    8:  CATEGORY_STONE,
    9:  CATEGORY_MUD,
    10: CATEGORY_STONE,     # PEBBLES
    11: CATEGORY_SAND,
    12: CATEGORY_SAND,      # SAND_BEACH
    19: CATEGORY_GRASS,     # GRASS_SHORT
    20: CATEGORY_GRASS,     # GRASS_MEDIUM
    21: CATEGORY_GRASS,     # GRASS_LONG
    22: CATEGORY_GRASS,
    26: CATEGORY_WOOD,      # WOOD_CRATES
    27: CATEGORY_WOOD,      # WOOD_SOLID
    35: CATEGORY_GLASS,
    36: CATEGORY_METAL,     # SCAFFOLD_POLE
    37: CATEGORY_METAL,     # METAL_GATE
    51: CATEGORY_METAL,     # METAL_HOLLOW
    56: CATEGORY_METAL,     # METAL_CHAIN_FENCE
    81: CATEGORY_METAL,     # BARREL
    82: CATEGORY_GRASS,     # PILE_OF_LEAVES
}

_VC_ID_TO_CATEGORY: Dict[int, int] = {
    0:  CATEGORY_DEFAULT,
    1:  CATEGORY_TARMAC,
    2:  CATEGORY_GRASS,
    3:  CATEGORY_DIRT,
    4:  CATEGORY_GRAVEL,
    5:  CATEGORY_MUD,
    6:  CATEGORY_WOOD,
    7:  CATEGORY_GLASS,
    8:  CATEGORY_METAL,
    9:  CATEGORY_STONE,
    10: CATEGORY_SAND,
    11: CATEGORY_WATER,
}

_III_ID_TO_CATEGORY: Dict[int, int] = {
    0:  CATEGORY_DEFAULT,
    1:  CATEGORY_TARMAC,
    2:  CATEGORY_GRASS,
    3:  CATEGORY_DIRT,
    4:  CATEGORY_GRAVEL,
    5:  CATEGORY_MUD,
    6:  CATEGORY_WOOD,
    7:  CATEGORY_GLASS,
    8:  CATEGORY_METAL,
    9:  CATEGORY_STONE,
    10: CATEGORY_SAND,
    11: CATEGORY_WATER,
}


# ── Per-game category → preferred ID ─────────────────────────────
# Multiple game IDs can map to the same category (e.g. GRASS_SHORT
# and GRASS_LONG both → CATEGORY_GRASS). For the reverse pass we
# pick one canonical ID per category.

_SA_CATEGORY_TO_ID: Dict[int, int] = {
    CATEGORY_DEFAULT: 0,
    CATEGORY_TARMAC:  1,
    CATEGORY_GRASS:   19,
    CATEGORY_DIRT:    9,   # MUD_DRY (closest SA equivalent)
    CATEGORY_GRAVEL:  7,
    CATEGORY_MUD:     9,
    CATEGORY_SAND:    11,
    CATEGORY_WOOD:    27,  # WOOD_SOLID
    CATEGORY_METAL:   36,  # SCAFFOLD_POLE (generic metal)
    CATEGORY_STONE:   5,   # PAVEMENT
    CATEGORY_GLASS:   35,
    CATEGORY_WATER:   0,   # SA handles water separately, fall to default
}

_VC_CATEGORY_TO_ID: Dict[int, int] = {
    CATEGORY_DEFAULT: 0,
    CATEGORY_TARMAC:  1,
    CATEGORY_GRASS:   2,
    CATEGORY_DIRT:    3,
    CATEGORY_GRAVEL:  4,
    CATEGORY_MUD:     5,
    CATEGORY_WOOD:    6,
    CATEGORY_GLASS:   7,
    CATEGORY_METAL:   8,
    CATEGORY_STONE:   9,
    CATEGORY_SAND:    10,
    CATEGORY_WATER:   11,
}

_III_CATEGORY_TO_ID: Dict[int, int] = dict(_VC_CATEGORY_TO_ID)


_ID_TO_CATEGORY = {
    'III': _III_ID_TO_CATEGORY,
    'VC':  _VC_ID_TO_CATEGORY,
    'SA':  _SA_ID_TO_CATEGORY,
}

_CATEGORY_TO_ID = {
    'III': _III_CATEGORY_TO_ID,
    'VC':  _VC_CATEGORY_TO_ID,
    'SA':  _SA_CATEGORY_TO_ID,
}


def translate_surface(surface_id: int, from_game: str, to_game: str
                      ) -> int:
    """Map ``surface_id`` from ``from_game``'s surface table into
    ``to_game``'s. Same game in/out → no-op. Unknown source IDs and
    categories without a target ID fall to 0 (DEFAULT).

    The translation is lossy by design — SA's 179 surfaces collapse
    to ~12 categories before re-expansion, so SA→III→SA round-trip
    will lose the GRASS_SHORT-vs-GRASS_LONG distinction.
    """
    if from_game == to_game:
        return surface_id
    category = _ID_TO_CATEGORY.get(from_game, {}).get(surface_id,
                                                     CATEGORY_DEFAULT)
    return _CATEGORY_TO_ID.get(to_game, {}).get(category, 0)


def clamp_surface_for_game(surface_id: int, target_game: str) -> int:
    """Clamp an arbitrary surface_id to the target game's range. Used
    by the writer when the source's category translation can't be
    determined (e.g. user authored a custom non-vanilla surface ID).
    Returns the original ID if it's within range; otherwise 0."""
    from . import game_versions as _gv
    max_id = _gv.profile_for(target_game).surface_id_max
    if 0 <= surface_id <= max_id:
        return surface_id
    return 0
