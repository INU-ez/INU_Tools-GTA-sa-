"""Import IDE file → Blender (store definitions as object properties)."""

from __future__ import annotations
import bpy
from ..core.ide import read_ide, IdeFile


def import_ide(filepath: str, context=None) -> list:
    """
    Read IDE file and apply definitions to matching Blender objects.

    For each IDE entry, searches for a Blender object whose name matches
    the model_name (case-insensitive). If found, writes model_id, txd_name,
    draw_distance, and ide_flags to ``obj.inu``.

    Returns list of matched objects.
    """
    ide = read_ide(filepath)
    matched = []

    # Build lookup: lowercase name → list of IDE objects
    ide_lookup: dict[str, list] = {}
    for obj_def in ide.objects:
        key = obj_def.model_name.lower()
        ide_lookup.setdefault(key, []).append(obj_def)

    # Match against scene objects
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        clean = _clean_name(obj.name).lower()
        entries = ide_lookup.get(clean)
        if not entries:
            continue

        entry = entries[0]  # take first match
        inu = obj.inu

        inu.model_id = entry.model_id
        inu.txd_name = entry.txd_name
        inu.draw_distance = entry.draw_distance
        inu.ide_flags = entry.flags

        matched.append(obj)

    return matched


def _clean_name(name: str) -> str:
    """Remove Blender numeric suffix and known suffixes."""
    if '.' in name:
        base, suffix = name.rsplit('.', 1)
        if suffix.isdigit():
            name = base
    for sfx in ('_COL', '_col', '_LOD', '_lod', '_SHA', '_sha'):
        if name.endswith(sfx):
            name = name[:-len(sfx)]
            break
    return name
