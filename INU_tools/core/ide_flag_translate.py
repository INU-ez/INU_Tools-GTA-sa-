# INU_tools.core.ide_flag_translate
# Cross-game translation of IDE ``objs.flags`` bit masks.
#
# Each game uses the same 32-bit flags column with DIFFERENT meanings
# per bit. Source: gtamods.com/wiki/Item_Definition (cross-checked
# 2026-05). Same bit position = different feature across games — a
# III .ide with bit 0x40 (NO_ZBUFFER_WRITE) is portable since SA uses
# the same meaning, but bit 0x10 (IS_SUBWAY in III, unused in SA)
# loses meaning entirely.
#
# Translation strategy: bits → canonical category → bits-in-target-game.
# Unmapped bits (unknown source bit, or category without target ID)
# are silently dropped, since writing a stale bit in the wrong column
# could trigger unintended engine behaviour (e.g. III bit 0x10 set on
# an SA model is unused, but if SA later defines that bit, the file
# would suddenly behave unexpectedly).

from typing import Dict


# ── Canonical category names ─────────────────────────────────────
# Each name represents a high-level feature; bits in different games
# may carry it. Stable across SDK versions — public API for users
# building their own translation tooling.

CAT_ROAD           = 'ROAD'
CAT_DO_NOT_FADE    = 'DO_NOT_FADE'
CAT_DRAW_LAST      = 'DRAW_LAST'
CAT_ADDITIVE       = 'ADDITIVE'
CAT_IS_SUBWAY      = 'IS_SUBWAY'
CAT_IGNORE_LIGHT   = 'IGNORE_LIGHTING'
CAT_NO_ZBUFFER     = 'NO_ZBUFFER_WRITE'
CAT_NO_SHADOWS     = 'DONT_RECEIVE_SHADOWS'
CAT_IGNORE_DRAW    = 'IGNORE_DRAW_DISTANCE'
CAT_GLASS_1        = 'IS_GLASS_TYPE_1'
CAT_GLASS_2        = 'IS_GLASS_TYPE_2'
CAT_GARAGE_DOOR    = 'IS_GARAGE_DOOR'
CAT_DAMAGABLE      = 'IS_DAMAGABLE'
CAT_IS_TREE        = 'IS_TREE'
CAT_IS_PALM        = 'IS_PALM'
CAT_NO_FLYER       = 'DOES_NOT_COLLIDE_WITH_FLYER'
CAT_IS_TAG         = 'IS_TAG'
CAT_NO_BACKFACE    = 'DISABLE_BACKFACE_CULLING'
CAT_BREAKABLE      = 'IS_BREAKABLE_STATUE'


# ── Per-game ``bit → category`` maps ─────────────────────────────
# A bit absent from the dict for a given game means "unused / not
# recognised by that game's engine".

_BIT_TO_CATEGORY: Dict[str, Dict[int, str]] = {
    'III': {
        # 0x1 is "ignored" in III — no category mapped.
        0x2:    CAT_DO_NOT_FADE,
        0x4:    CAT_DRAW_LAST,
        0x8:    CAT_ADDITIVE,
        0x10:   CAT_IS_SUBWAY,
        0x20:   CAT_IGNORE_LIGHT,
        0x40:   CAT_NO_ZBUFFER,
    },
    'VC': {
        0x1:    CAT_ROAD,
        0x2:    CAT_DO_NOT_FADE,
        0x4:    CAT_DRAW_LAST,
        0x8:    CAT_ADDITIVE,
        # 0x10 in VC is "read but unused" — no category.
        0x20:   CAT_IGNORE_LIGHT,
        0x40:   CAT_NO_ZBUFFER,
        0x80:   CAT_NO_SHADOWS,
        0x100:  CAT_IGNORE_DRAW,
        0x200:  CAT_GLASS_1,
        0x400:  CAT_GLASS_2,
    },
    'SA': {
        0x1:      CAT_ROAD,
        # 0x2 — not read by SA engine, no category.
        0x4:      CAT_DRAW_LAST,
        0x8:      CAT_ADDITIVE,
        # 0x10, 0x20 — not read in SA (0x20 is anim-only).
        0x40:     CAT_NO_ZBUFFER,
        0x80:     CAT_NO_SHADOWS,
        # 0x100 — not read in SA.
        0x200:    CAT_GLASS_1,
        0x400:    CAT_GLASS_2,
        0x800:    CAT_GARAGE_DOOR,
        0x1000:   CAT_DAMAGABLE,
        0x2000:   CAT_IS_TREE,
        0x4000:   CAT_IS_PALM,
        0x8000:   CAT_NO_FLYER,
        0x100000: CAT_IS_TAG,
        0x200000: CAT_NO_BACKFACE,
        0x400000: CAT_BREAKABLE,
    },
}


# ── Per-game ``category → bit`` maps (inverse) ───────────────────
# Built automatically — a category mapped via multiple bits in the
# same game would be ambiguous, but currently every category lives at
# a single bit per game.

_CATEGORY_TO_BIT: Dict[str, Dict[str, int]] = {
    game: {cat: bit for bit, cat in bits.items()}
    for game, bits in _BIT_TO_CATEGORY.items()
}


def flags_to_categories(flags: int, source_game: str) -> set:
    """Decompose a flags int into the set of canonical categories
    that the source game's bits represent. Unknown bits are silently
    dropped — they mean nothing in the source engine."""
    bit_map = _BIT_TO_CATEGORY.get(source_game, {})
    return {cat for bit, cat in bit_map.items() if flags & bit}


def categories_to_flags(categories, target_game: str) -> int:
    """Compose a flags int for ``target_game`` from a set of canonical
    categories. Categories without a representative bit in the target
    game are dropped (e.g. CAT_GARAGE_DOOR has no III bit, so a III
    export omits it)."""
    cat_map = _CATEGORY_TO_BIT.get(target_game, {})
    out = 0
    for cat in categories:
        bit = cat_map.get(cat)
        if bit is not None:
            out |= bit
    return out


def translate_flags(flags: int, source_game: str, target_game: str
                    ) -> int:
    """Round-trip a flags int through the canonical-category layer
    when source and target games differ. Same game in/out → no-op
    pass-through, preserving any "unknown" bits the caller may have
    appended manually (e.g. FLA-specific extensions)."""
    if source_game == target_game:
        return flags
    cats = flags_to_categories(flags, source_game)
    return categories_to_flags(cats, target_game)


# ── Which flag-properties (in INUObjectProps) are valid per game ─
# Used by the UI panel to hide checkboxes that have no meaning in the
# current scene's target game. Keys are the prop names defined in
# __init__.py:INUObjectProps; values are the games the property is
# valid for.

FLAG_PROP_GAMES: Dict[str, frozenset] = {
    'flag_draw_last':         frozenset({'III', 'VC', 'SA'}),
    'flag_additive':          frozenset({'III', 'VC', 'SA'}),
    'flag_no_zbuffer':        frozenset({'III', 'VC', 'SA'}),
    'flag_do_not_fade':       frozenset({'III', 'VC'}),
    'flag_ignore_lighting':   frozenset({'III', 'VC'}),
    'flag_is_subway':         frozenset({'III'}),
    'flag_is_road':           frozenset({'VC', 'SA'}),
    'flag_no_shadows':        frozenset({'VC', 'SA'}),
    'flag_glass_1':           frozenset({'VC', 'SA'}),
    'flag_glass_2':           frozenset({'VC', 'SA'}),
    'flag_ignore_draw_dist':  frozenset({'VC'}),
    'flag_garage_door':       frozenset({'SA'}),
    'flag_damagable':         frozenset({'SA'}),
    'flag_is_tree':           frozenset({'SA'}),
    'flag_is_palm':           frozenset({'SA'}),
    'flag_no_flyer_col':      frozenset({'SA'}),
    'flag_is_tag':            frozenset({'SA'}),
    'flag_no_backface':       frozenset({'SA'}),
    'flag_breakable':         frozenset({'SA'}),
}


def flag_props_for_game(game: str) -> list:
    """Return the ordered list of INUObjectProps flag property names
    that should be shown in the UI for the given target game. Order
    matches a logical grouping (universal → VC-only → SA-only)."""
    _ORDER = (
        'flag_draw_last', 'flag_additive', 'flag_no_zbuffer',
        'flag_do_not_fade', 'flag_ignore_lighting',
        'flag_is_subway',
        'flag_is_road', 'flag_no_shadows',
        'flag_glass_1', 'flag_glass_2',
        'flag_ignore_draw_dist',
        'flag_garage_door', 'flag_damagable',
        'flag_is_tree', 'flag_is_palm',
        'flag_no_flyer_col', 'flag_is_tag',
        'flag_no_backface', 'flag_breakable',
    )
    return [p for p in _ORDER if game in FLAG_PROP_GAMES.get(p, frozenset())]
