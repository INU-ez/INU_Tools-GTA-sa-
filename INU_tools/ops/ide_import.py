"""Import IDE file → Blender (store definitions as object properties)."""

from __future__ import annotations
import bpy
from ..core.ide import read_ide


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


        matched.append(obj)

    return matched


def _clean_name_typed(name: str) -> tuple[str, str]:
    """Remove Blender numeric suffix and detect type using scene settings."""
    from ..tools.model_utils import get_model_type
    # Create a minimal mock object for get_model_type
    class _Mock:
        def __init__(self, n):
            self.name = n
    mt, base = get_model_type(_Mock(name))
    return base, mt or 'OTHER'
