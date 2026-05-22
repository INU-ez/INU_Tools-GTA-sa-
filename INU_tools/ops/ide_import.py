"""Import IDE file → Blender (store definitions as object properties)."""

from __future__ import annotations
import bpy
from ..core.ide import read_ide


def _detect_source_game(filepath: str) -> str:
    """Best-effort guess at which game an IDE file came from. IDE is
    pure text without a game magic — we infer from the presence of
    SA-only sections (``2dfx``) or VC-introduced ones (``txdp``).
    Falls back to the scene's active game when the file has no
    distinguishing markers; if even that can't be read, default SA.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(8192).lower()
        if '\n2dfx' in content or content.startswith('2dfx'):
            return 'SA'
        if '\ntxdp' in content or content.startswith('txdp'):
            return 'VC'   # txdp is VC+SA; defaults to VC, user overrides if SA
    except OSError:
        pass
    try:
        import bpy as _bpy
        from ..core import game_versions as gv
        return gv.game_of_scene(_bpy.context.scene)
    except Exception:
        return 'SA'


def import_ide(filepath: str, context=None) -> list:
    """
    Read IDE file and apply definitions to matching Blender objects.

    Matching logic:
    - admiral_DFF  → matches IDE entry "admiral"
    - admiral_LOD  → matches IDE entry "LODadmiral"
    - admiral      → matches IDE entry "admiral"

    Returns list of matched objects.
    """
    ide = read_ide(filepath)
    matched = []

    # Record source game on each imported object so a future export
    # to a different target game can translate the flags through
    # core.ide_flag_translate rather than writing the bytes verbatim.
    source_game = _detect_source_game(filepath)

    # Build lookup: lowercase name → IDE entry
    ide_lookup: dict[str, dict] = {}
    for obj_def in ide.objects:
        key = obj_def.model_name.lower()
        if key not in ide_lookup:
            ide_lookup[key] = {
                'model_id': obj_def.model_id,
                'txd_name': obj_def.txd_name,
                'draw_distance': obj_def.draw_distance,
                'flags': obj_def.flags,
            }

    for anim_def in ide.anims:
        key = anim_def.model_name.lower()
        if key not in ide_lookup:
            ide_lookup[key] = {
                'model_id': anim_def.model_id,
                'txd_name': anim_def.txd_name,
                'draw_distance': anim_def.draw_distance,
                'flags': anim_def.flags,
            }

    # Match against scene objects
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        clean, stype = _clean_name_typed(obj.name)
        clean_low = clean.lower()

        # Skip COL and SHA objects — IDE definitions are for DFF/LOD only
        if stype in ('COL', 'SHA'):
            continue

        entry = None
        if stype == 'LOD':
            # admiral_LOD → look for "LODadmiral" in IDE
            entry = ide_lookup.get('lod' + clean_low)
        else:
            # admiral_DFF or admiral → look for "admiral" in IDE
            entry = ide_lookup.get(clean_low)

        if not entry:
            continue

        inu = obj.inu
        inu.model_id = entry['model_id']
        inu.txd_name = entry['txd_name']
        inu.draw_distance = entry['draw_distance']
        inu.ide_flags = entry['flags']
        # Tag the source game so the writer knows when to translate.
        try:
            inu.ide_flags_source_game = source_game
        except AttributeError:
            pass


        matched.append(obj)

    # 2DFX section: vanilla III/VC store effects here (in IDE), not
    # in DFF chunks. Materialise each entry as a child Empty under
    # the matching mesh object so the user can see + edit them in
    # the viewport. Position-only round-trip for the first pass —
    # type-specific params live in ``obj['ide_2dfx_params']`` as a
    # raw string list so the writer can emit them back verbatim
    # without per-type Blender prop mapping.
    if ide.fx_2dfx and source_game in ('III', 'VC'):
        _materialise_2dfx_from_ide(ide.fx_2dfx, matched)

    return matched


def _materialise_2dfx_from_ide(fx_entries, scene_objects):
    """Create one Empty per ``IdeFx2dfx`` entry, parented to the mesh
    object whose ``inu.model_id`` matches the entry's ``model_id``.

    Stores ``type_id``, ``r/g/b``, ``unknown`` and the raw
    ``type_params`` list on the Empty as custom props so the IDE
    writer can re-emit them byte-for-byte on export. Full per-type
    Blender-prop mapping (corona_tex, particle_name, etc.) is left
    for Phase 22.5b — for now the Empty is a placeholder marker.
    """
    import bpy
    by_mid: dict[int, object] = {}
    for obj in scene_objects:
        inu = getattr(obj, 'inu', None)
        if inu is None:
            continue
        mid = getattr(inu, 'model_id', 0) or 0
        if mid:
            by_mid.setdefault(mid, obj)

    _FX_TYPE_NAME = {0: 'LIGHT', 1: 'PARTICLE', 2: 'PED_ATTRACTOR',
                     3: 'PED_BEHAVIOR', 4: 'SUN_GLARE'}

    for fx in fx_entries:
        parent = by_mid.get(fx.model_id)
        if parent is None:
            # No matching mesh in scene — skip silently. User can
            # re-import the DFF later and the IDE re-import will
            # match then.
            continue
        empty = bpy.data.objects.new(
            f"{parent.name}_2dfx_{fx.type_id}", None)
        empty.empty_display_type = 'SPHERE'
        empty.empty_display_size = 0.5
        empty.location = (fx.pos_x, fx.pos_y, fx.pos_z)
        empty.parent = parent
        # Link to the parent's collection so the Empty shows in the
        # same outliner group.
        for coll in parent.users_collection:
            try:
                coll.objects.link(empty)
            except RuntimeError:
                pass

        # Mark as 2DFX so other tools (validate scene, export) pick
        # it up; effect_2dfx maps numeric type → string enum.
        try:
            empty.inu.type = '2DFX'
            empty.inu.effect_2dfx = _FX_TYPE_NAME.get(fx.type_id, 'LIGHT')
            empty.inu.color_2dfx = (fx.r / 255.0, fx.g / 255.0,
                                     fx.b / 255.0, fx.unknown / 255.0)
        except Exception:
            pass

        # Stash the raw type_params for re-emission on export — keeps
        # the IDE round-trip byte-identical even when our reverse
        # type-prop mapping is incomplete.
        empty['ide_2dfx_type_id'] = fx.type_id
        empty['ide_2dfx_unknown'] = fx.unknown
        empty['ide_2dfx_params'] = list(fx.type_params)


def _clean_name_typed(name: str) -> tuple[str, str]:
    """Remove Blender numeric suffix and detect type using scene settings."""
    from ..tools.model_utils import get_model_type
    # Create a minimal mock object for get_model_type
    class _Mock:
        def __init__(self, n):
            self.name = n
    mt, base = get_model_type(_Mock(name))
    return base, mt or 'OTHER'
