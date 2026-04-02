# INU_tools.data.id_manager — Model ID allocation and tracking
#
# File format (model_ids.txt):
#   One ID per line. Free IDs are just numbers, used IDs have -modelname suffix.
#   Example:
#     3500
#     3501-tatar_str_2817_1
#     3502-LODtatar_str_2817_1
#     3503
#     3600

import os

_ID_FILE = os.path.join(os.path.dirname(__file__), 'model_ids.txt')


def _load():
    """Load ID list from text file. Returns list of (id, model_name_or_None)."""
    entries = []
    if not os.path.isfile(_ID_FILE):
        return entries
    try:
        with open(_ID_FILE, 'r', encoding='utf-8') as f:
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
    except:
        pass
    return entries


def _save(entries):
    """Save ID list to text file, preserving header lines."""
    # Read existing non-ID lines (header)
    header_lines = []
    if os.path.isfile(_ID_FILE):
        with open(_ID_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                # Check if line starts with a digit — it's an ID line, stop
                if stripped[0].isdigit():
                    break
                header_lines.append(line.rstrip('\n'))

    with open(_ID_FILE, 'w', encoding='utf-8') as f:
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
    """Clear all assignments (all IDs become free)."""
    entries = _load()
    entries = [(id_num, None) for id_num, _ in entries]
    _save(entries)


def get_file_path():
    """Return path to the ID file."""
    return _ID_FILE


def create_id_file():
    """Create model_ids.txt with all IDs 321-19999 as free."""
    entries = [(i, None) for i in range(321, 20000)]
    _save(entries)
    return len(entries)


def populate_from_game(game_root):
    """Read all IDE files from gta.dat and mark those IDs as occupied."""
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

    # Update existing entries: mark game IDs as occupied
    entries = _load()
    entry_map = {id_num: name for id_num, name in entries}

    for gid, gname in game_ids.items():
        entry_map[gid] = gname  # mark as occupied with model name

    entries = [(k, v) for k, v in entry_map.items()]
    _save(entries)
    return len(game_ids)
