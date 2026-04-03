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
    """Remove suffixes/prefixes using scene settings."""
    from ..tools.model_utils import get_model_type
    class _Mock:
        def __init__(self, n):
            self.name = n
    _, base = get_model_type(_Mock(name))
    return base
