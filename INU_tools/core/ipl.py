"""
GTA SA IPL (Item Placement) file reader/writer.

IPL ``inst`` section line format (SA):
  ID, ModelName, Interior, PosX, PosY, PosZ, RotX, RotY, RotZ, RotW, LOD

Rotation is a quaternion stored as (X, Y, Z, W).

No Blender dependency — pure Python.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IplInstance:
    """One placed object from the IPL ``inst`` section."""
    model_id: int
    model_name: str
    interior: int = 0
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    rot_x: float = 0.0
    rot_y: float = 0.0
    rot_z: float = 0.0
    rot_w: float = 1.0
    lod_index: int = -1


@dataclass
class IplFile:
    """Collection of IPL entries."""
    instances: list[IplInstance] = field(default_factory=list)


# ── Reading ─────────────────────────────────────────────────────────

def read_ipl(filepath: str) -> IplFile:
    """Parse a text IPL file and return structured data."""
    ipl = IplFile()
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

            if low in ('inst', 'cull', 'path', 'grge', 'enex', 'pick',
                       'jump', 'tcyc', 'auzo', 'mult', 'cars', 'occl',
                       'zone'):
                section = low
                continue

            if section == 'inst':
                inst = _parse_inst_line(line)
                if inst:
                    ipl.instances.append(inst)

    return ipl


def _parse_inst_line(line: str) -> Optional[IplInstance]:
    """Parse one comma-separated instance placement line."""
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 11:
            return None
        return IplInstance(
            model_id=int(parts[0]),
            model_name=parts[1],
            interior=int(parts[2]),
            pos_x=float(parts[3]),
            pos_y=float(parts[4]),
            pos_z=float(parts[5]),
            rot_x=float(parts[6]),
            rot_y=float(parts[7]),
            rot_z=float(parts[8]),
            rot_w=float(parts[9]),
            lod_index=int(parts[10]),
        )
    except (ValueError, IndexError):
        return None


def _format_inst_line(i: IplInstance) -> str:
    """Format one IPL inst line."""
    return (f'{i.model_id}, {i.model_name}, {i.interior}, '
            f'{i.pos_x:.6f}, {i.pos_y:.6f}, {i.pos_z:.6f}, '
            f'{i.rot_x:.6f}, {i.rot_y:.6f}, {i.rot_z:.6f}, {i.rot_w:.6f}, '
            f'{i.lod_index}')


# ── Writing ─────────────────────────────────────────────────────────

def write_ipl(filepath: str, ipl: IplFile) -> None:
    """Write a new IPL file with all standard SA sections (like Kam's scripts)."""
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        # inst — always present
        f.write('inst\n')
        for i in ipl.instances:
            f.write(_format_inst_line(i) + '\n')
        f.write('end\n')

        # Standard empty sections
        for section in ('cull', 'path', 'grge', 'enex', 'pick',
                        'cars', 'jump', 'tcyc', 'auzo', 'mult'):
            f.write(f'{section}\nend\n')


def upsert_ipl(filepath: str, entries: list[IplInstance]) -> tuple[int, int]:
    """
    Insert or update entries in an existing IPL file.

    Matching is by model_id + model_name (both must match).
    - If match found → replace the line (update position/rotation).
    - If no match → append to the ``inst`` section.

    Returns (updated_count, added_count).
    """
    if not os.path.isfile(filepath):
        write_ipl(filepath, IplFile(instances=entries))
        return (0, len(entries))

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Build lookup: (model_id, name_lower) → entry
    pending: dict[tuple[int, str], IplInstance] = {}
    for e in entries:
        pending[(e.model_id, e.model_name.lower())] = e

    updated = 0
    result_lines = []
    section = None
    inst_end_idx = -1

    for line in lines:
        stripped = line.strip()
        low = stripped.lower()

        if low == 'end' and section == 'inst':
            inst_end_idx = len(result_lines)
            section = None
            result_lines.append(line)
            continue

        if low in ('inst', 'cull', 'path', 'grge', 'enex', 'pick',
                   'jump', 'tcyc', 'auzo', 'mult', 'cars', 'occl', 'zone'):
            section = low
            result_lines.append(line)
            continue

        if section == 'inst' and stripped and not stripped.startswith('#'):
            parsed = _parse_inst_line(stripped)
            if parsed:
                key = (parsed.model_id, parsed.model_name.lower())
                if key in pending:
                    entry = pending.pop(key)
                    result_lines.append(_format_inst_line(entry) + '\n')
                    updated += 1
                    continue

        result_lines.append(line)

    added = len(pending)
    if added > 0:
        remaining = list(pending.values())
        if inst_end_idx >= 0:
            insert_lines = [_format_inst_line(e) + '\n' for e in remaining]
            result_lines = (result_lines[:inst_end_idx]
                          + insert_lines
                          + result_lines[inst_end_idx:])
        else:
            result_lines.append('inst\n')
            for e in remaining:
                result_lines.append(_format_inst_line(e) + '\n')
            result_lines.append('end\n')

    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(result_lines)

    return (updated, added)


def remove_ipl(filepath: str, model_ids: set[int]) -> int:
    """Remove entries with given model_ids from IPL file. Returns count removed."""
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

        if low in ('inst', 'cull', 'path', 'grge', 'enex', 'pick',
                   'jump', 'tcyc', 'auzo', 'mult', 'cars', 'occl', 'zone'):
            section = low
            result_lines.append(line)
            continue

        if section == 'inst' and stripped and not stripped.startswith('#'):
            parsed = _parse_inst_line(stripped)
            if parsed and parsed.model_id in model_ids:
                removed += 1
                continue

        result_lines.append(line)

    if removed > 0:
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.writelines(result_lines)

    return removed
