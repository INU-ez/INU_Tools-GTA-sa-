"""Export Blender objects → IDE file (object definitions)."""

from __future__ import annotations
import os
from ..core.ide import IdeFile, IdeObject, write_ide


def export_ide(filepath: str, objects: list) -> None:
    """
    Generate an IDE file from selected Blender objects.

    Each mesh object produces one ``objs`` entry.
    Properties are read from ``obj.inu`` (model_id, txd_name, draw_distance, ide_flags).
    Model name defaults to the object name (without _COL/_LOD suffixes).
    """
    ide = IdeFile()

    for obj in objects:
        if obj.type != 'MESH':
            continue

        inu = getattr(obj, 'inu', None)

        # Model name: strip suffixes, use clean name
        model_name = _clean_model_name(obj.name)

        model_id = getattr(inu, 'model_id', 0) if inu else 0
        txd_name = getattr(inu, 'txd_name', '') if inu else ''
        if not txd_name:
            txd_name = model_name  # default: same as model name

        draw_distance = getattr(inu, 'draw_distance', 300.0) if inu else 300.0
        flags = getattr(inu, 'ide_flags', 0) if inu else 0

        ide.objects.append(IdeObject(
            model_id=model_id,
            model_name=model_name,
            txd_name=txd_name,
            draw_distance=draw_distance,
            flags=flags,
        ))

    write_ide(filepath, ide)


def _clean_model_name(name: str) -> str:
    """Remove common suffixes like .001, _COL, _LOD from object name."""
    # Remove Blender numeric suffix
    if '.' in name:
        base, suffix = name.rsplit('.', 1)
        if suffix.isdigit():
            name = base

    # Remove known suffixes
    for sfx in ('_COL', '_col', '_LOD', '_lod', '_SHA', '_sha'):
        if name.endswith(sfx):
            name = name[:-len(sfx)]
            break

    return name
