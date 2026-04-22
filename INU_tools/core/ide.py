"""
GTA SA IDE (Item Definition) file reader/writer.

IDE format — text file with sections:
  objs   — static objects
  tobj   — timed objects (appear/disappear by hour)
  anim   — animated objects
  cars   — vehicle definitions
  peds   — pedestrian definitions
  weap   — weapon model definitions
  hier   — hierarchy/cutscene objects
  txdp   — TXD parent references
  2dfx   — 2D effects (SA uses binary in DFF, IDE section usually empty)

No Blender dependency — pure Python.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional


# ── Data classes ──────────────────────────────────────────────────────

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
class IdeAnim:
    """Animated object from IDE ``anim`` section.
    Format: ID, ModelName, TXDName, AnimFile, DrawDist, Flags
    """
    model_id: int
    model_name: str
    txd_name: str
    anim_file: str = ""
    draw_distance: float = 300.0
    flags: int = 0


@dataclass
class IdeCar:
    """Vehicle definition from IDE ``cars`` section.
    Format: ID, ModelName, TxdName, Type, HandlingID, GameName, Anims,
            Class, Frequency, Flags, Comprules, WheelID,
            WheelScaleFront, WheelScaleRear, WheelUpgradeClass
    """
    model_id: int
    model_name: str
    txd_name: str
    veh_type: str = "car"
    handling_id: str = ""
    game_name: str = ""
    anims: str = "null"
    veh_class: str = "normal"
    frequency: int = 10
    flags: int = 0
    comprules: int = 0
    wheel_id: int = -1
    wheel_scale_front: float = 1.0
    wheel_scale_rear: float = 1.0
    wheel_upgrade_class: int = -1


@dataclass
class IdePed:
    """Pedestrian definition from IDE ``peds`` section.
    Format: ID, ModelName, TxdName, PedType, Behaviour, AnimGroup,
            CarsCanDriveMask, Flags, AnimFile, Radio1, Radio2,
            VoiceArchive, Voice1, Voice2
    """
    model_id: int
    model_name: str
    txd_name: str
    ped_type: str = "CIVMALE"
    behaviour: str = "CIVMALE"
    anim_group: str = "man"
    cars_can_drive: str = "0"
    flags: str = "0"
    anim_file: str = "null"
    radio1: int = 0
    radio2: int = 0
    voice_archive: str = "null"
    voice1: str = "null"
    voice2: str = "null"


@dataclass
class IdeWeap:
    """Weapon model from IDE ``weap`` section.
    Format: ID, ModelName, TxdName, AnimName, MeshCount, DrawDistance
    """
    model_id: int
    model_name: str
    txd_name: str
    anim_name: str = "null"
    mesh_count: int = 1
    draw_distance: float = 100.0


@dataclass
class IdeHier:
    """Hierarchy/cutscene object from IDE ``hier`` section.
    Format: ID, ModelName, TxdName
    """
    model_id: int
    model_name: str
    txd_name: str


@dataclass
class IdeTxdp:
    """TXD parent reference from IDE ``txdp`` section.
    Format: TxdName, ParentTxdName
    """
    txd_name: str
    parent_txd_name: str


@dataclass
class IdeFile:
    """Collection of all IDE entries."""
    objects: list[IdeObject] = field(default_factory=list)
    anims: list[IdeAnim] = field(default_factory=list)
    cars: list[IdeCar] = field(default_factory=list)
    peds: list[IdePed] = field(default_factory=list)
    weaps: list[IdeWeap] = field(default_factory=list)
    hiers: list[IdeHier] = field(default_factory=list)
    txdps: list[IdeTxdp] = field(default_factory=list)


# ── Parsing helpers ───────────────────────────────────────────────────

def _parse_obj_line(line: str, timed: bool = False) -> Optional[IdeObject]:
    """Parse one comma-separated object line."""
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 4:
            return None
        model_id = int(parts[0])
        model_name = parts[1]
        txd_name = parts[2]
        draw_dist = float(parts[3])
        flags = int(parts[4]) if len(parts) > 4 else 0
        time_on = None
        time_off = None
        if timed and len(parts) >= 7:
            time_on = int(parts[5])
            time_off = int(parts[6])
        return IdeObject(
            model_id=model_id, model_name=model_name, txd_name=txd_name,
            draw_distance=draw_dist, flags=flags,
            time_on=time_on, time_off=time_off,
        )
    except (ValueError, IndexError):
        return None


def _parse_anim_line(line: str) -> Optional[IdeAnim]:
    """Parse anim section line: ID, ModelName, TXDName, AnimFile, DrawDist, Flags"""
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 5:
            return None
        return IdeAnim(
            model_id=int(parts[0]),
            model_name=parts[1],
            txd_name=parts[2],
            anim_file=parts[3],
            draw_distance=float(parts[4]),
            flags=int(parts[5]) if len(parts) > 5 else 0,
        )
    except (ValueError, IndexError):
        return None


def _parse_car_line(line: str) -> Optional[IdeCar]:
    """Parse cars section line (15 fields)."""
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 10:
            return None
        car = IdeCar(
            model_id=int(parts[0]),
            model_name=parts[1],
            txd_name=parts[2],
            veh_type=parts[3],
            handling_id=parts[4],
            game_name=parts[5],
            anims=parts[6],
            veh_class=parts[7],
            frequency=int(parts[8]),
            flags=int(parts[9]),
        )
        if len(parts) > 10:
            car.comprules = int(parts[10], 16) if parts[10].strip() else 0
        if len(parts) > 11:
            car.wheel_id = int(parts[11])
        if len(parts) > 12:
            car.wheel_scale_front = float(parts[12])
        if len(parts) > 13:
            car.wheel_scale_rear = float(parts[13])
        if len(parts) > 14:
            car.wheel_upgrade_class = int(parts[14])
        return car
    except (ValueError, IndexError):
        return None


def _parse_ped_line(line: str) -> Optional[IdePed]:
    """Parse peds section line (14 fields)."""
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 9:
            return None
        ped = IdePed(
            model_id=int(parts[0]),
            model_name=parts[1],
            txd_name=parts[2],
            ped_type=parts[3],
            behaviour=parts[4],
            anim_group=parts[5],
            cars_can_drive=parts[6],
            flags=parts[7],
            anim_file=parts[8],
        )
        if len(parts) > 9:
            ped.radio1 = int(parts[9])
        if len(parts) > 10:
            ped.radio2 = int(parts[10])
        if len(parts) > 11:
            ped.voice_archive = parts[11]
        if len(parts) > 12:
            ped.voice1 = parts[12]
        if len(parts) > 13:
            ped.voice2 = parts[13]
        return ped
    except (ValueError, IndexError):
        return None


def _parse_weap_line(line: str) -> Optional[IdeWeap]:
    """Parse weap section line: ID, ModelName, TxdName, AnimName, MeshCount, DrawDist"""
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 5:
            return None
        return IdeWeap(
            model_id=int(parts[0]),
            model_name=parts[1],
            txd_name=parts[2],
            anim_name=parts[3],
            mesh_count=int(parts[4]),
            draw_distance=float(parts[5]) if len(parts) > 5 else 100.0,
        )
    except (ValueError, IndexError):
        return None


def _parse_hier_line(line: str) -> Optional[IdeHier]:
    """Parse hier section line: ID, ModelName, TxdName"""
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 3:
            return None
        return IdeHier(
            model_id=int(parts[0]),
            model_name=parts[1],
            txd_name=parts[2],
        )
    except (ValueError, IndexError):
        return None


def _parse_txdp_line(line: str) -> Optional[IdeTxdp]:
    """Parse txdp section line: TxdName, ParentTxdName"""
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 2:
            return None
        return IdeTxdp(txd_name=parts[0], parent_txd_name=parts[1])
    except (ValueError, IndexError):
        return None


# ── Formatting helpers ────────────────────────────────────────────────

def _fmt_dd(val: float) -> str:
    """Format draw distance: integer if whole, float otherwise."""
    return str(int(val)) if val == int(val) else str(val)


def _format_obj_line(o: IdeObject) -> str:
    return f'{o.model_id}, {o.model_name}, {o.txd_name}, {_fmt_dd(o.draw_distance)}, {o.flags}'


def _format_tobj_line(o: IdeObject) -> str:
    return f'{o.model_id}, {o.model_name}, {o.txd_name}, {_fmt_dd(o.draw_distance)}, {o.flags}, {o.time_on}, {o.time_off}'


def _format_anim_line(a: IdeAnim) -> str:
    return f'{a.model_id}, {a.model_name}, {a.txd_name}, {a.anim_file}, {_fmt_dd(a.draw_distance)}, {a.flags}'


def _format_car_line(c: IdeCar) -> str:
    comprules = format(c.comprules, 'x') if c.comprules else '0'
    return (f'{c.model_id}, {c.model_name}, {c.txd_name}, {c.veh_type}, '
            f'{c.handling_id}, {c.game_name}, {c.anims}, {c.veh_class}, '
            f'{c.frequency}, {c.flags}, {comprules}, {c.wheel_id}, '
            f'{c.wheel_scale_front:.4f}, {c.wheel_scale_rear:.4f}, {c.wheel_upgrade_class}')


def _format_ped_line(p: IdePed) -> str:
    return (f'{p.model_id}, {p.model_name}, {p.txd_name}, {p.ped_type}, '
            f'{p.behaviour}, {p.anim_group}, {p.cars_can_drive}, {p.flags}, '
            f'{p.anim_file}, {p.radio1}, {p.radio2}, '
            f'{p.voice_archive}, {p.voice1}, {p.voice2}')


def _format_weap_line(w: IdeWeap) -> str:
    return f'{w.model_id}, {w.model_name}, {w.txd_name}, {w.anim_name}, {w.mesh_count}, {_fmt_dd(w.draw_distance)}'


def _format_hier_line(h: IdeHier) -> str:
    return f'{h.model_id}, {h.model_name}, {h.txd_name}'


def _format_txdp_line(t: IdeTxdp) -> str:
    return f'{t.txd_name}, {t.parent_txd_name}'


# ── Reading ─────────────────────────────────────────────────────────

def read_ide(filepath: str) -> IdeFile:
    """Parse a text IDE file and return structured data with all sections."""
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

            if section == 'objs':
                obj = _parse_obj_line(line)
                if obj:
                    ide.objects.append(obj)
            elif section == 'tobj':
                obj = _parse_obj_line(line, timed=True)
                if obj:
                    ide.objects.append(obj)
            elif section == 'anim':
                anim = _parse_anim_line(line)
                if anim:
                    ide.anims.append(anim)
            elif section == 'cars':
                car = _parse_car_line(line)
                if car:
                    ide.cars.append(car)
            elif section == 'peds':
                ped = _parse_ped_line(line)
                if ped:
                    ide.peds.append(ped)
            elif section == 'weap':
                weap = _parse_weap_line(line)
                if weap:
                    ide.weaps.append(weap)
            elif section == 'hier':
                hier = _parse_hier_line(line)
                if hier:
                    ide.hiers.append(hier)
            elif section == 'txdp':
                txdp = _parse_txdp_line(line)
                if txdp:
                    ide.txdps.append(txdp)

    return ide


# ── Writing ─────────────────────────────────────────────────────────

def write_ide(filepath: str, ide: IdeFile) -> None:
    """Write a full IDE file.

    Standard map sections (objs, tobj, anim, txdp, 2dfx) are ALWAYS
    emitted with a terminating ``end`` — even when empty — to match the
    vanilla GTA SA file layout that most tools expect. Specialised
    sections (cars, peds, weap, hier) are only written when populated.
    """
    objs = [o for o in ide.objects if not o.is_timed]
    tobjs = [o for o in ide.objects if o.is_timed]

    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        # objs — always emitted
        f.write('objs\n')
        for o in objs:
            f.write(_format_obj_line(o) + '\n')
        f.write('end\n')

        # tobj — always emitted
        f.write('tobj\n')
        for o in tobjs:
            f.write(_format_tobj_line(o) + '\n')
        f.write('end\n')

        # anim — always emitted
        f.write('anim\n')
        for a in ide.anims:
            f.write(_format_anim_line(a) + '\n')
        f.write('end\n')

        # cars — only when populated (veh.ide style)
        if ide.cars:
            f.write('cars\n')
            for c in ide.cars:
                f.write(_format_car_line(c) + '\n')
            f.write('end\n')

        # peds — only when populated (peds.ide style)
        if ide.peds:
            f.write('peds\n')
            for p in ide.peds:
                f.write(_format_ped_line(p) + '\n')
            f.write('end\n')

        # weap — only when populated
        if ide.weaps:
            f.write('weap\n')
            for w in ide.weaps:
                f.write(_format_weap_line(w) + '\n')
            f.write('end\n')

        # hier — only when populated
        if ide.hiers:
            f.write('hier\n')
            for h in ide.hiers:
                f.write(_format_hier_line(h) + '\n')
            f.write('end\n')

        # txdp — always emitted
        f.write('txdp\n')
        for t in ide.txdps:
            f.write(_format_txdp_line(t) + '\n')
        f.write('end\n')

        # 2dfx — always emitted (SA stores effects in DFF, IDE section stays empty)
        f.write('2dfx\n')
        f.write('end\n')


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
            # Previous section ended implicitly (no 'end' before new section)
            if section == 'objs':
                objs_end_idx = len(result_lines)
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

        if section in ('objs', 'tobj', 'anim', 'cars', 'peds', 'weap', 'hier'):
            if stripped and not stripped.startswith('#'):
                # Try to extract model_id (first field)
                try:
                    mid = int(stripped.split(',')[0].strip())
                    if mid in model_ids:
                        removed += 1
                        continue
                except ValueError:
                    pass

        result_lines.append(line)

    if removed > 0:
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.writelines(result_lines)

    return removed
