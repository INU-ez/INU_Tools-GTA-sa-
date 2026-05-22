# INU_tools.core.ped_mask_translate
# Cross-game translation of PEDS ``cars_can_drive`` bitmasks.
#
# Each game uses a different bit ordering in this column — VC inserted
# "normal" at bit 0 in 2002, shifting III's class indices by 1. SA
# inherited VC's layout and added "bicycle" at bit 11. Writing III's
# mask byte unchanged into a VC peds.ide would assign vehicle classes
# completely wrong (III "executive" bit 0x04 = VC "richfamily").
#
# Source bits verified against gtamods.com/wiki/PEDS (2026-05).
# SA bicycle bit (0x800) is best-guess: gtamods lists "bicycle" as a
# SA vehicle class but doesn't pin its bit position. Vanilla SA peds
# rarely use the bicycle bit so this is unverifiable from in-file
# samples; the writer treats it as opt-in only.

from typing import Dict


# ── Canonical vehicle classes ────────────────────────────────────

CAT_NORMAL       = 'NORMAL'        # generic civilian car (VC+SA only)
CAT_POORFAMILY   = 'POORFAMILY'
CAT_RICHFAMILY   = 'RICHFAMILY'
CAT_EXECUTIVE    = 'EXECUTIVE'
CAT_WORKER       = 'WORKER'
CAT_SPECIAL      = 'SPECIAL'        # III only — VC reused the slot for "normal"
CAT_BIG          = 'BIG'
CAT_TAXI         = 'TAXI'
CAT_MOPED        = 'MOPED'          # VC+SA
CAT_MOTORBIKE    = 'MOTORBIKE'      # VC+SA
CAT_LEISUREBOAT  = 'LEISUREBOAT'    # VC+SA
CAT_WORKERBOAT   = 'WORKERBOAT'     # VC+SA
CAT_BICYCLE      = 'BICYCLE'        # SA only — bit position best-guess


# ── Per-game ``bit → category`` maps ─────────────────────────────

_BIT_TO_CATEGORY: Dict[str, Dict[int, str]] = {
    'III': {
        0x01: CAT_POORFAMILY,
        0x02: CAT_RICHFAMILY,
        0x04: CAT_EXECUTIVE,
        0x08: CAT_WORKER,
        0x10: CAT_SPECIAL,
        0x20: CAT_BIG,
        0x40: CAT_TAXI,
    },
    'VC': {
        0x001: CAT_NORMAL,
        0x002: CAT_POORFAMILY,
        0x004: CAT_RICHFAMILY,
        0x008: CAT_EXECUTIVE,
        0x010: CAT_WORKER,
        0x020: CAT_BIG,
        0x040: CAT_TAXI,
        0x080: CAT_MOPED,
        0x100: CAT_MOTORBIKE,
        0x200: CAT_LEISUREBOAT,
        0x400: CAT_WORKERBOAT,
    },
    # SA mirrors VC (Rockstar kept the carcols/carmods layout
    # forward-compatible). Bicycle assumed at bit 11 (0x800) — vanilla
    # SA peds.ide uses values like 0xC, 0x1F that match the VC ordering.
    'SA': {
        0x001: CAT_NORMAL,
        0x002: CAT_POORFAMILY,
        0x004: CAT_RICHFAMILY,
        0x008: CAT_EXECUTIVE,
        0x010: CAT_WORKER,
        0x020: CAT_BIG,
        0x040: CAT_TAXI,
        0x080: CAT_MOPED,
        0x100: CAT_MOTORBIKE,
        0x200: CAT_LEISUREBOAT,
        0x400: CAT_WORKERBOAT,
        0x800: CAT_BICYCLE,
    },
}


# ── Per-game ``category → bit`` maps (inverse) ───────────────────

_CATEGORY_TO_BIT: Dict[str, Dict[str, int]] = {
    game: {cat: bit for bit, cat in bits.items()}
    for game, bits in _BIT_TO_CATEGORY.items()
}


def mask_to_categories(mask: int, source_game: str) -> set:
    """Decompose a cars_can_drive mask int into the set of canonical
    vehicle-class categories the source game's bits represent. Unknown
    bits are silently dropped."""
    bit_map = _BIT_TO_CATEGORY.get(source_game, {})
    return {cat for bit, cat in bit_map.items() if mask & bit}


def categories_to_mask(categories, target_game: str) -> int:
    """Compose a mask int for ``target_game`` from a set of canonical
    categories. Categories without a representative bit in the target
    game are dropped (e.g. CAT_NORMAL has no bit in III; CAT_BICYCLE
    has no bit in III/VC)."""
    cat_map = _CATEGORY_TO_BIT.get(target_game, {})
    out = 0
    for cat in categories:
        bit = cat_map.get(cat)
        if bit is not None:
            out |= bit
    return out


def translate_mask(mask: int, source_game: str, target_game: str) -> int:
    """Round-trip a cars_can_drive mask through the canonical category
    layer when source and target games differ. Same game → identity
    pass-through (preserves any unknown bits the caller may have
    appended manually for engine extensions)."""
    if source_game == target_game:
        return mask
    cats = mask_to_categories(mask, source_game)
    return categories_to_mask(cats, target_game)


def translate_mask_str(value, source_game: str, target_game: str) -> str:
    """Hex-string convenience wrapper. PEDS lines store the mask as
    a hex token (``"0d"``, ``"1f"``) — accept the string, parse,
    translate, and emit a lowercase hex string the IDE writer can drop
    in directly. Falls back to the original value on parse failure."""
    if source_game == target_game:
        return str(value)
    try:
        n = int(value, 16) if isinstance(value, str) else int(value)
    except (ValueError, TypeError):
        return str(value)
    return format(translate_mask(n, source_game, target_game), 'x')
