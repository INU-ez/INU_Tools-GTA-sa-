# INU_tools.data.id_manager — Model ID allocation and tracking
#
# Presets: IDs are stored as individual .txt files under `data/id_presets/`.
# The caller picks the active preset via `set_active_preset(name)`; all
# subsequent allocate/release/load/save operations run against that file.
# A legacy `data/model_ids.txt` (single-file layout from earlier versions)
# is auto-migrated into `id_presets/default.txt` on first access.
#
# File format (one ID per line):
#   Free IDs are plain numbers; used IDs carry a `-modelname` suffix.
#     3500
#     3501-tatar_str_2817_1
#     3502-LODtatar_str_2817_1
#     3503

import os
import re
import shutil

# Presets now live alongside paths.json in the user config folder:
#     <blender addons dir>/INU_Preset/id_presets/<name>.txt
# The old `INU_tools/data/id_presets/` and `INU_tools/data/model_ids.txt`
# locations are still honoured for auto-migration on first access.
_DATA_DIR = os.path.dirname(__file__)              # .../INU_tools/data/
_ADDON_DIR = os.path.dirname(_DATA_DIR)            # .../INU_tools/
_ADDONS_DIR = os.path.dirname(_ADDON_DIR)          # .../addons/
_INU_PRESET_DIR = os.path.join(_ADDONS_DIR, 'INU_Preset')
_PRESETS_DIR = os.path.join(_INU_PRESET_DIR, 'id_presets')

_LEGACY_FILE = os.path.join(_DATA_DIR, 'model_ids.txt')
_LEGACY_PRESETS_DIR = os.path.join(_DATA_DIR, 'id_presets')

_DEFAULT_PRESET = 'default'
_active_preset = _DEFAULT_PRESET


# ── Presets ──────────────────────────────────────────────────────────

def _sanitize(name: str) -> str:
    """Return a filename-safe preset name (letters/digits/dash/underscore/dot/space)."""
    name = (name or '').strip()
    name = re.sub(r'[^\w.\- ]+', '_', name)
    return name or _DEFAULT_PRESET


def _ensure_presets_dir():
    """Create the presets directory and migrate any legacy locations.

    Legacy layouts that get auto-imported on first access:

    * ``INU_tools/data/model_ids.txt`` → ``INU_Preset/id_presets/default.txt``
      (single-file store from the very first preset release)
    * ``INU_tools/data/id_presets/*.txt`` → ``INU_Preset/id_presets/*.txt``
      (intermediate layout that lived inside the addon folder — moved out
      so presets survive addon reinstalls and updates)
    """
    try:
        os.makedirs(_INU_PRESET_DIR, exist_ok=True)
        os.makedirs(_PRESETS_DIR, exist_ok=True)
    except Exception:
        return

    # Migration 1: bring presets from the intermediate data/id_presets/
    if os.path.isdir(_LEGACY_PRESETS_DIR):
        try:
            for fn in os.listdir(_LEGACY_PRESETS_DIR):
                if not fn.lower().endswith('.txt'):
                    continue
                src = os.path.join(_LEGACY_PRESETS_DIR, fn)
                dst = os.path.join(_PRESETS_DIR, fn)
                if os.path.isfile(src) and not os.path.isfile(dst):
                    try:
                        shutil.copy2(src, dst)
                    except Exception:
                        pass
        except Exception:
            pass

    # Migration 2: original single-file model_ids.txt → default.txt
    default_path = os.path.join(_PRESETS_DIR, _DEFAULT_PRESET + '.txt')
    if os.path.isfile(_LEGACY_FILE) and not os.path.isfile(default_path):
        try:
            shutil.copy2(_LEGACY_FILE, default_path)
        except Exception:
            pass


def set_active_preset(name: str) -> None:
    """Select the preset used by subsequent load/save calls."""
    global _active_preset
    _active_preset = _sanitize(name) if name else _DEFAULT_PRESET


def get_active_preset() -> str:
    return _active_preset


def list_presets() -> list:
    """Return the sorted list of preset names (without .txt extension)."""
    _ensure_presets_dir()
    try:
        files = os.listdir(_PRESETS_DIR)
    except Exception:
        return []
    names = []
    for fn in files:
        low = fn.lower()
        if not low.endswith('.txt') or fn.startswith('_'):
            continue
        names.append(os.path.splitext(fn)[0])
    names.sort(key=lambda s: s.lower())
    if _DEFAULT_PRESET not in names:
        # Ensure a default preset always shows up so the dropdown isn't empty.
        names.insert(0, _DEFAULT_PRESET)
    return names


def _preset_path(name: str = None) -> str:
    _ensure_presets_dir()
    safe = _sanitize(name if name is not None else _active_preset)
    return os.path.join(_PRESETS_DIR, safe + '.txt')


def create_preset(name: str, copy_from: str = None) -> bool:
    """Create a new empty preset, optionally duplicating another preset's IDs."""
    _ensure_presets_dir()
    safe = _sanitize(name)
    if not safe:
        return False
    dst = os.path.join(_PRESETS_DIR, safe + '.txt')
    if os.path.isfile(dst):
        return False
    try:
        if copy_from:
            src = os.path.join(_PRESETS_DIR, _sanitize(copy_from) + '.txt')
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                return True
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(f'# GTA SA model ID preset: {safe}\n')
        return True
    except Exception:
        return False


def delete_preset(name: str) -> bool:
    """Delete a preset file. The `default` preset cannot be removed."""
    safe = _sanitize(name)
    if safe == _DEFAULT_PRESET:
        return False
    path = os.path.join(_PRESETS_DIR, safe + '.txt')
    if not os.path.isfile(path):
        return False
    try:
        os.remove(path)
        return True
    except Exception:
        return False


def rename_preset(old: str, new: str) -> bool:
    old_safe = _sanitize(old)
    new_safe = _sanitize(new)
    if old_safe == new_safe:
        return False
    src = os.path.join(_PRESETS_DIR, old_safe + '.txt')
    dst = os.path.join(_PRESETS_DIR, new_safe + '.txt')
    if not os.path.isfile(src) or os.path.isfile(dst):
        return False
    try:
        os.rename(src, dst)
        return True
    except Exception:
        return False


# ── Storage (current active preset) ──────────────────────────────────

def _load():
    """Load ID list from the active preset. Returns list of (id, model_name_or_None)."""
    entries = []
    path = _preset_path()
    if not os.path.isfile(path):
        return entries
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '-' in line:
                    parts = line.split('-', 1)
                    try:
                        id_num = int(parts[0].strip())
                        name = parts[1].strip()
                        entries.append((id_num, name if name else None))
                    except ValueError:
                        continue
                else:
                    try:
                        id_num = int(line)
                        entries.append((id_num, None))
                    except ValueError:
                        continue
    except Exception:
        pass
    return entries


def _save(entries):
    """Save ID list to the active preset, preserving any header comment lines."""
    path = _preset_path()
    header_lines = []
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped[0].isdigit():
                    break
                header_lines.append(line.rstrip('\n'))

    with open(path, 'w', encoding='utf-8') as f:
        for h in header_lines:
            f.write(h + '\n')
        for id_num, name in sorted(entries, key=lambda x: x[0]):
            if name:
                f.write(f"{id_num}-{name}\n")
            else:
                f.write(f"{id_num}\n")


def get_free_ids():
    """Return list of free (unassigned) IDs."""
    return [id_num for id_num, name in _load() if name is None]


def get_used_ids():
    """Return dict of used IDs: {id_num: model_name}."""
    return {id_num: name for id_num, name in _load() if name is not None}


def get_all():
    """Return all entries as list of (id, name_or_None)."""
    return _load()


def allocate_id(model_name):
    """Take first free ID, assign model_name, save. Returns ID or None."""
    entries = _load()
    for i, (id_num, name) in enumerate(entries):
        if name is None:
            entries[i] = (id_num, model_name)
            _save(entries)
            return id_num
    return None


def release_id(model_id):
    """Release an ID (remove model name, keep ID as free)."""
    entries = _load()
    for i, (id_num, name) in enumerate(entries):
        if id_num == model_id and name is not None:
            entries[i] = (id_num, None)
            _save(entries)
            return True
    return False


def clear_all():
    """Clear all assignments in the active preset (all IDs become free)."""
    entries = _load()
    entries = [(id_num, None) for id_num, _ in entries]
    _save(entries)


def get_file_path():
    """Return path to the current active preset file."""
    return _preset_path()


def create_id_file(max_id=19999):
    """Fill the active preset with free IDs 321..max_id."""
    entries = [(i, None) for i in range(321, max_id + 1)]
    _save(entries)
    return len(entries)


def extend_ids(count=1000):
    """Add more free IDs after the current maximum. Returns (new_start, new_end)."""
    entries = _load()
    if entries:
        max_id = max(id_num for id_num, _ in entries)
    else:
        max_id = 320
    new_start = max_id + 1
    new_end = new_start + count - 1
    for i in range(new_start, new_end + 1):
        entries.append((i, None))
    _save(entries)
    return new_start, new_end


def populate_from_game(game_root):
    """Read all IDE files from gta.dat and mark those IDs as occupied in the active preset."""
    from ..core.gta_dat import find_all_resources
    from ..core.ide import read_ide
    import os

    info = find_all_resources(game_root)
    game_ids = {}  # id -> model_name

    for p in info.ide_paths:
        if os.path.isfile(p):
            try:
                ide = read_ide(p)
                for obj in ide.objects:
                    game_ids[obj.model_id] = obj.model_name
                for anim in ide.anims:
                    game_ids[anim.model_id] = anim.model_name
                for car in ide.cars:
                    game_ids[car.model_id] = car.model_name
                for ped in ide.peds:
                    game_ids[ped.model_id] = ped.model_name
                for weap in ide.weaps:
                    game_ids[weap.model_id] = weap.model_name
                for hier in ide.hiers:
                    game_ids[hier.model_id] = hier.model_name
            except Exception:
                pass

    entries = _load()
    entry_map = {id_num: name for id_num, name in entries}

    for gid, gname in game_ids.items():
        entry_map[gid] = gname

    entries = [(k, v) for k, v in entry_map.items()]
    _save(entries)
    return len(game_ids)
