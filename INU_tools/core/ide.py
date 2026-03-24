"""
GTA SA IDE (Item Definition) file reader/writer.

IDE format — text file with sections:
  objs   — static objects
  tobj   — timed objects (appear/disappear by hour)
  anim   — animated objects
  txdp   — TXD parent references

objs line format (SA):
  ID, ModelName, TxdName, DrawDist, Flags

tobj line format (SA):
  ID, ModelName, TxdName, DrawDist, Flags, TimeOn, TimeOff

No Blender dependency — pure Python.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IdeObject:
    """Single object definition from IDE ``objs`` or ``tobj`` section."""
    model_id: int
    model_name: str
    txd_name: str
    draw_distance: float = 300.0
    flags: int = 0
    # tobj-only
    time_on: Optional[int] = None   # hour 0-23
    time_off: Optional[int] = None  # hour 0-23

    @property
    def is_timed(self) -> bool:
        return self.time_on is not None and self.time_off is not None


@dataclass
class IdeFile:
    """Collection of IDE entries."""
    objects: list[IdeObject] = field(default_factory=list)


# ── Reading ─────────────────────────────────────────────────────────

def read_ide(filepath: str) -> IdeFile:
    """Parse a text IDE file and return structured data."""
    ide = IdeFile()
    section = None

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            low = line.lower()

            if low == 'end':
                section = None
                continue

            if low in ('objs', 'tobj', 'anim', 'txdp', 'weap', 'hier',
                       'cars', 'peds', 'path', '2dfx'):
                section = low
                continue

            if section in ('objs', 'tobj', 'anim'):
                obj = _parse_obj_line(line, timed=(section == 'tobj'))
                if obj:
                    ide.objects.append(obj)

    return ide


def _parse_obj_line(line: str, timed: bool = False) -> Optional[IdeObject]:
    """Parse one comma-separated object line."""
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 4:
            return None
        model_id = int(parts[0])
        model_name = parts[1]
        txd_name = parts[2]

        # Draw distance — might have multiple values (LOD system), take first
        draw_dist = float(parts[3])

        flags = int(parts[4]) if len(parts) > 4 else 0

        time_on = None
        time_off = None
        if timed and len(parts) >= 7:
            time_on = int(parts[5])
            time_off = int(parts[6])

        return IdeObject(
            model_id=model_id,
            model_name=model_name,
            txd_name=txd_name,
            draw_distance=draw_dist,
            flags=flags,
            time_on=time_on,
            time_off=time_off,
        )
    except (ValueError, IndexError):
        return None


def _format_obj_line(o: IdeObject) -> str:
    """Format one IDE object line."""
    dd = int(o.draw_distance) if o.draw_distance == int(o.draw_distance) else o.draw_distance
    return f'{o.model_id}, {o.model_name}, {o.txd_name}, {dd}, {o.flags}'


def _format_tobj_line(o: IdeObject) -> str:
    """Format one IDE tobj line."""
    dd = int(o.draw_distance) if o.draw_distance == int(o.draw_distance) else o.draw_distance
    return f'{o.model_id}, {o.model_name}, {o.txd_name}, {dd}, {o.flags}, {o.time_on}, {o.time_off}'


# ── Writing ─────────────────────────────────────────────────────────

def write_ide(filepath: str, ide: IdeFile) -> None:
    """Write a new IDE file with all standard SA sections (like Kam's scripts)."""
    objs = [o for o in ide.objects if not o.is_timed]
    tobjs = [o for o in ide.objects if o.is_timed]

    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        # objs — always present
        f.write('objs\n')
        for o in objs:
            f.write(_format_obj_line(o) + '\n')
        f.write('end\n')

        # tobj
        f.write('tobj\n')
        for o in tobjs:
            f.write(_format_tobj_line(o) + '\n')
        f.write('end\n')

        # Standard empty sections
        for section in ('path', '2dfx', 'anim', 'txdp'):
            f.write(f'{section}\nend\n')


def upsert_ide(filepath: str, entries: list[IdeObject]) -> tuple[int, int]:
    """
    Insert or update entries in an existing IDE file.

    - If entry with same model_id exists → replace the line.
    - If no match → append to the ``objs`` section (or create it).

    Returns (updated_count, added_count).
    """
    if not os.path.isfile(filepath):
        # File doesn't exist — write fresh
        write_ide(filepath, IdeFile(objects=entries))
        return (0, len(entries))

    # Read original lines
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Build lookup of entries to upsert by model_id
    pending: dict[int, IdeObject] = {e.model_id: e for e in entries}
    updated = 0
    result_lines = []
    section = None
    objs_end_idx = -1  # index of 'end' line for objs section ONLY

    for line in lines:
        stripped = line.strip()
        low = stripped.lower()

        if low == 'end' and section is not None:
            if section == 'objs':
                objs_end_idx = len(result_lines)
            section = None
            result_lines.append(line)
            continue

        if low in ('objs', 'tobj', 'anim', 'txdp', 'weap', 'hier',
                   'cars', 'peds', 'path', '2dfx'):
            section = low
            result_lines.append(line)
            continue

        if section in ('objs', 'tobj') and stripped and not stripped.startswith('#'):
            parsed = _parse_obj_line(stripped, timed=(section == 'tobj'))
            if parsed and parsed.model_id in pending:
                # Replace this line with updated entry
                entry = pending.pop(parsed.model_id)
                if entry.is_timed:
                    result_lines.append(_format_tobj_line(entry) + '\n')
                else:
                    result_lines.append(_format_obj_line(entry) + '\n')
                updated += 1
                continue

        result_lines.append(line)

    # Remaining entries need to be appended
    added = len(pending)
    if added > 0:
        remaining = list(pending.values())
        if objs_end_idx >= 0:
            # Insert before the last 'end' of objs section
            insert_lines = [_format_obj_line(e) + '\n' for e in remaining]
            result_lines = (result_lines[:objs_end_idx]
                          + insert_lines
                          + result_lines[objs_end_idx:])
        else:
            # No objs section found — append one at the end
            result_lines.append('objs\n')
            for e in remaining:
                result_lines.append(_format_obj_line(e) + '\n')
            result_lines.append('end\n')

    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(result_lines)

    return (updated, added)


def remove_ide(filepath: str, model_ids: set[int]) -> int:
    """Remove entries with given model_ids from IDE file. Returns count removed."""
    if not os.path.isfile(filepath):
        return 0

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    result_lines = []
    section = None
    removed = 0

    for line in lines:
        stripped = line.strip()
        low = stripped.lower()

        if low == 'end':
            section = None
            result_lines.append(line)
            continue

        if low in ('objs', 'tobj', 'anim', 'txdp', 'weap', 'hier',
                   'cars', 'peds', 'path', '2dfx'):
            section = low
            result_lines.append(line)
            continue

        if section in ('objs', 'tobj') and stripped and not stripped.startswith('#'):
            parsed = _parse_obj_line(stripped, timed=(section == 'tobj'))
            if parsed and parsed.model_id in model_ids:
                removed += 1
                continue

        result_lines.append(line)

    if removed > 0:
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.writelines(result_lines)

    return removed
