# INU_tools.data.material_presets
#
# JSON-based preset storage for GTA Material panel. Presets live in
# <addons dir>/INU_Preset/material_presets/*.json — same INU_Preset root
# folder as id_presets/, so they survive addon updates and re-installs.
#
# Each preset file is a dict:
#     {
#       "name": "Vehicle Body",
#       "description": "Кузов машины с env map отражениями",
#       "mat_inu": {
#           "pipeline": "0x53F2009A",
#           "export_env_map": true,
#           "env_map_tex": "xvehicleenv128",
#           ...
#       }
#     }

from __future__ import annotations

import os
import re
import json


_DATA_DIR = os.path.dirname(__file__)
_ADDON_DIR = os.path.dirname(_DATA_DIR)
_ADDONS_DIR = os.path.dirname(_ADDON_DIR)
_INU_PRESET_DIR = os.path.join(_ADDONS_DIR, 'INU_Preset')
_PRESETS_DIR = os.path.join(_INU_PRESET_DIR, 'material_presets')


# Fields from INUMaterialProps that a preset may capture. Collision-surface
# and UV-animation per-material settings are skipped — a "material style"
# preset is about rendering/shading, not per-instance data.
PRESET_FIELDS = (
    'ambient',
    'export_env_map', 'env_map_tex', 'env_map_coef', 'env_map_fb_alpha',
    'export_bump_map', 'bump_map_tex',
    'export_reflection', 'reflection_scale_x', 'reflection_scale_y',
    'reflection_offset_x', 'reflection_offset_y', 'reflection_intensity',
    'export_specular', 'specular_level', 'specular_texture',
    'export_dual_tex', 'dual_tex_src_blend', 'dual_tex_dst_blend',
    'dual_tex_texture',
    'export_animation', 'animation_name',
)


def _sanitize(name: str) -> str:
    """Return a filename-safe preset name."""
    name = (name or '').strip()
    name = re.sub(r'[^\w.\- ]+', '_', name)
    return name


def _ensure_dir():
    try:
        os.makedirs(_PRESETS_DIR, exist_ok=True)
    except Exception:
        pass


def presets_dir() -> str:
    """Return the INU_Preset/material_presets/ path (may not exist yet)."""
    return _PRESETS_DIR


def list_presets() -> list:
    """Return sorted list of user preset names (without .json)."""
    _ensure_dir()
    names = []
    if os.path.isdir(_PRESETS_DIR):
        for fn in sorted(os.listdir(_PRESETS_DIR)):
            if fn.lower().endswith('.json'):
                names.append(fn[:-5])
    return names


def load_preset(name: str) -> dict:
    """Read a preset by name, return its mat_inu dict (empty if not found)."""
    path = os.path.join(_PRESETS_DIR, _sanitize(name) + '.json')
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('mat_inu', {})
    except Exception:
        return {}


def save_preset(name: str, mat_inu: dict, description: str = '') -> bool:
    """Write preset to disk as JSON. Returns True on success."""
    _ensure_dir()
    name = _sanitize(name)
    if not name:
        return False
    path = os.path.join(_PRESETS_DIR, name + '.json')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'name': name,
                'description': description,
                'mat_inu': mat_inu,
            }, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def delete_preset(name: str) -> bool:
    """Remove preset file. Returns True if it existed and was removed."""
    path = os.path.join(_PRESETS_DIR, _sanitize(name) + '.json')
    if not os.path.isfile(path):
        return False
    try:
        os.remove(path)
        return True
    except Exception:
        return False


def capture_from_inu(inu) -> dict:
    """Snapshot a mat.inu PropertyGroup into a plain dict (JSON-safe)."""
    out = {}
    for field in PRESET_FIELDS:
        if hasattr(inu, field):
            value = getattr(inu, field)
            # Convert bpy types (Color, Vector) to plain Python
            if hasattr(value, '__iter__') and not isinstance(value, str):
                try:
                    value = list(value)
                except Exception:
                    pass
            out[field] = value
    return out


def apply_to_inu(inu, data: dict) -> int:
    """Write dict values into mat.inu. Returns count of applied fields."""
    count = 0
    for field, value in data.items():
        if hasattr(inu, field):
            try:
                setattr(inu, field, value)
                count += 1
            except Exception:
                pass
    return count
