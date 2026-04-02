"""Import IDE file → Blender (store definitions as object properties)."""

from __future__ import annotations
import bpy
from ..core.ide import read_ide, IdeFile


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
    """Remove Blender numeric suffix and known suffixes.
    Returns (clean_name, suffix_type)."""
    if '.' in name:
        base, suffix = name.rsplit('.', 1)
        if suffix.isdigit():
            name = base

    for sfx, stype in [('_DFF', 'DFF'), ('_dff', 'DFF'),
                        ('_LOD', 'LOD'), ('_lod', 'LOD'),
                        ('_COL', 'COL'), ('_col', 'COL'),
                        ('_SHA', 'SHA'), ('_sha', 'SHA')]:
        if name.endswith(sfx):
            return name[:-len(sfx)], stype

    return name, 'OTHER'
