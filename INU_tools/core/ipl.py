"""
GTA SA IPL (Item Placement) file reader/writer.

Sections:
  inst  — object instances
  cull  — cull zones
  grge  — garages
  enex  — entrance/exit markers
  pick  — pickups
  cars  — parked vehicles / car generators
  auzo  — audio zones (box or sphere)
  jump  — stunt jumps
  occl  — occlusion zones
  tcyc  — time cycle modifiers

Also supports binary IPL (``bnry`` header) for inst and cars.

No Blender dependency — pure Python.
"""

from __future__ import annotations
import os
import struct
from dataclasses import dataclass, field
from typing import Optional


# ── Data classes ──────────────────────────────────────────────────────

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
class IplCull:
    """Cull zone from IPL ``cull`` section (11 or 14 fields)."""
    center_x: float = 0.0
    center_y: float = 0.0
    center_z: float = 0.0
    unknown1: float = 0.0
    length: float = 0.0      # Y dimension
    bottom: float = 0.0      # absolute Z bottom
    width: float = 0.0       # X dimension
    unknown2: float = 0.0
    top: float = 0.0         # absolute Z top
    flag: int = 0
    unknown3: float = 0.0
    # Mirror parameters (optional, 14-field format)
    mirror_vx: Optional[float] = None
    mirror_vy: Optional[float] = None
    mirror_vz: Optional[float] = None
    mirror_cm: Optional[float] = None

    @property
    def has_mirror(self) -> bool:
        return self.mirror_vx is not None


@dataclass
class IplGarage:
    """Garage from IPL ``grge`` section (11 fields)."""
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    line_x: float = 0.0
    line_y: float = 0.0
    cube_x: float = 0.0
    cube_y: float = 0.0
    cube_z: float = 0.0
    flags: int = 0
    garage_type: int = 0
    name: str = ""


@dataclass
class IplEnex:
    """Entry/exit marker from IPL ``enex`` section (18 fields)."""
    x1: float = 0.0
    y1: float = 0.0
    z1: float = 0.0
    enter_angle: float = 0.0
    size_x: float = 0.0
    size_y: float = 0.0
    size_z: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    z2: float = 0.0
    exit_angle: float = 0.0
    target_interior: int = 0
    flags: int = 0
    name: str = ""
    sky: int = 0
    num_peds: int = 0
    time_on: int = 0
    time_off: int = 0


@dataclass
class IplPickup:
    """Pickup from IPL ``pick`` section (4 fields)."""
    pickup_id: int = 0
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0


@dataclass
class IplCar:
    """Parked vehicle from IPL ``cars`` section (12 fields)."""
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    angle: float = 0.0
    car_id: int = -1
    primary_color: int = -1
    secondary_color: int = -1
    force_spawn: int = 0
    alarm: int = 0
    door_lock: int = 0
    unknown1: int = 0
    unknown2: int = 0


@dataclass
class IplAuzo:
    """Audio zone from IPL ``auzo`` section (box=9 or sphere=7 fields)."""
    name: str = ""
    audio_id: int = 0
    switch: int = 0
    # Box format
    x1: float = 0.0
    y1: float = 0.0
    z1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    z2: float = 0.0
    # Sphere format
    radius: Optional[float] = None

    @property
    def is_sphere(self) -> bool:
        return self.radius is not None


@dataclass
class IplJump:
    """Stunt jump from IPL ``jump`` section (16 fields)."""
    start_lower_x: float = 0.0
    start_lower_y: float = 0.0
    start_lower_z: float = 0.0
    start_upper_x: float = 0.0
    start_upper_y: float = 0.0
    start_upper_z: float = 0.0
    target_lower_x: float = 0.0
    target_lower_y: float = 0.0
    target_lower_z: float = 0.0
    target_upper_x: float = 0.0
    target_upper_y: float = 0.0
    target_upper_z: float = 0.0
    camera_x: float = 0.0
    camera_y: float = 0.0
    camera_z: float = 0.0
    reward: int = 0


@dataclass
class IplOccl:
    """Occlusion zone from IPL ``occl`` section (10 fields)."""
    mid_x: float = 0.0
    mid_y: float = 0.0
    bottom_z: float = 0.0
    width_x: float = 0.0
    width_y: float = 0.0
    height: float = 0.0
    rotation: float = 0.0
    unknown1: float = 0.0
    unknown2: float = 0.0
    unknown3: int = 0


@dataclass
class IplTcyc:
    """Time cycle modifier from IPL ``tcyc`` section (up to 12 fields)."""
    x1: float = 0.0
    y1: float = 0.0
    z1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    z2: float = 0.0
    far_clip: int = 0
    extra_color: int = 0
    extra_color_intensity: float = 0.0
    falloff_dist: float = 100.0
    unused: float = 0.0
    lod_dist_mult: float = 1.0


@dataclass
class IplZone:
    """Map zone from IPL ``zone`` section (9 fields)."""
    name: str = ""
    zone_type: int = 0
    x1: float = 0.0
    y1: float = 0.0
    z1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    z2: float = 0.0
    level: int = 0


@dataclass
class IplFile:
    """Collection of all IPL entries."""
    instances: list[IplInstance] = field(default_factory=list)
    culls: list[IplCull] = field(default_factory=list)
    garages: list[IplGarage] = field(default_factory=list)
    enexs: list[IplEnex] = field(default_factory=list)
    pickups: list[IplPickup] = field(default_factory=list)
    cars: list[IplCar] = field(default_factory=list)
    auzos: list[IplAuzo] = field(default_factory=list)
    jumps: list[IplJump] = field(default_factory=list)
    occls: list[IplOccl] = field(default_factory=list)
    tcycs: list[IplTcyc] = field(default_factory=list)
    zones: list[IplZone] = field(default_factory=list)


# ── Parsing helpers ───────────────────────────────────────────────────

def _p(parts: list, idx: int, conv=float, default=0):
    """Safe field access with conversion."""
    try:
        return conv(parts[idx].strip())
    except (IndexError, ValueError):
        return default


def _ps(parts: list, idx: int, default: str = "") -> str:
    """Safe string field access."""
    try:
        return parts[idx].strip().strip('"')
    except IndexError:
        return default


def _parse_inst_line(line: str) -> Optional[IplInstance]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 11:
            return None
        return IplInstance(
            model_id=int(parts[0]), model_name=parts[1],
            interior=int(parts[2]),
            pos_x=float(parts[3]), pos_y=float(parts[4]), pos_z=float(parts[5]),
            rot_x=float(parts[6]), rot_y=float(parts[7]),
            rot_z=float(parts[8]), rot_w=float(parts[9]),
            lod_index=int(parts[10]),
        )
    except (ValueError, IndexError):
        return None


def _parse_cull_line(line: str) -> Optional[IplCull]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 10:
            return None
        c = IplCull(
            center_x=float(parts[0]), center_y=float(parts[1]), center_z=float(parts[2]),
            unknown1=float(parts[3]),
            length=float(parts[4]), bottom=float(parts[5]),
            width=float(parts[6]), unknown2=float(parts[7]),
            top=float(parts[8]), flag=int(parts[9]),
        )
        if len(parts) >= 14:
            c.mirror_vx = float(parts[10])
            c.mirror_vy = float(parts[11])
            c.mirror_vz = float(parts[12])
            c.mirror_cm = float(parts[13])
        elif len(parts) >= 11:
            c.unknown3 = float(parts[10])
        return c
    except (ValueError, IndexError):
        return None


def _parse_grge_line(line: str) -> Optional[IplGarage]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 11:
            return None
        return IplGarage(
            pos_x=float(parts[0]), pos_y=float(parts[1]), pos_z=float(parts[2]),
            line_x=float(parts[3]), line_y=float(parts[4]),
            cube_x=float(parts[5]), cube_y=float(parts[6]), cube_z=float(parts[7]),
            flags=int(parts[8]), garage_type=int(parts[9]),
            name=parts[10].strip(),
        )
    except (ValueError, IndexError):
        return None


def _parse_enex_line(line: str) -> Optional[IplEnex]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 14:
            return None
        return IplEnex(
            x1=float(parts[0]), y1=float(parts[1]), z1=float(parts[2]),
            enter_angle=float(parts[3]),
            size_x=float(parts[4]), size_y=float(parts[5]), size_z=float(parts[6]),
            x2=float(parts[7]), y2=float(parts[8]), z2=float(parts[9]),
            exit_angle=float(parts[10]),
            target_interior=int(parts[11]), flags=int(parts[12]),
            name=_ps(parts, 13),
            sky=_p(parts, 14, int, 0),
            num_peds=_p(parts, 15, int, 0),
            time_on=_p(parts, 16, int, 0),
            time_off=_p(parts, 17, int, 0),
        )
    except (ValueError, IndexError):
        return None


def _parse_pick_line(line: str) -> Optional[IplPickup]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 4:
            return None
        return IplPickup(
            pickup_id=int(parts[0]),
            pos_x=float(parts[1]), pos_y=float(parts[2]), pos_z=float(parts[3]),
        )
    except (ValueError, IndexError):
        return None


def _parse_cars_line(line: str) -> Optional[IplCar]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 10:
            return None
        return IplCar(
            pos_x=float(parts[0]), pos_y=float(parts[1]), pos_z=float(parts[2]),
            angle=float(parts[3]), car_id=int(parts[4]),
            primary_color=int(parts[5]), secondary_color=int(parts[6]),
            force_spawn=_p(parts, 7, int, 0),
            alarm=_p(parts, 8, int, 0), door_lock=_p(parts, 9, int, 0),
            unknown1=_p(parts, 10, int, 0), unknown2=_p(parts, 11, int, 0),
        )
    except (ValueError, IndexError):
        return None


def _parse_auzo_line(line: str) -> Optional[IplAuzo]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 7:
            return None
        a = IplAuzo(
            name=parts[0].strip().strip('"'),
            audio_id=int(parts[1]), switch=int(parts[2]),
            x1=float(parts[3]), y1=float(parts[4]), z1=float(parts[5]),
        )
        if len(parts) >= 9:
            # Box format
            a.x2 = float(parts[6])
            a.y2 = float(parts[7])
            a.z2 = float(parts[8])
        else:
            # Sphere format
            a.radius = float(parts[6])
        return a
    except (ValueError, IndexError):
        return None


def _parse_jump_line(line: str) -> Optional[IplJump]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 16:
            return None
        return IplJump(
            start_lower_x=float(parts[0]), start_lower_y=float(parts[1]),
            start_lower_z=float(parts[2]),
            start_upper_x=float(parts[3]), start_upper_y=float(parts[4]),
            start_upper_z=float(parts[5]),
            target_lower_x=float(parts[6]), target_lower_y=float(parts[7]),
            target_lower_z=float(parts[8]),
            target_upper_x=float(parts[9]), target_upper_y=float(parts[10]),
            target_upper_z=float(parts[11]),
            camera_x=float(parts[12]), camera_y=float(parts[13]),
            camera_z=float(parts[14]),
            reward=int(parts[15]),
        )
    except (ValueError, IndexError):
        return None


def _parse_occl_line(line: str) -> Optional[IplOccl]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 7:
            return None
        return IplOccl(
            mid_x=float(parts[0]), mid_y=float(parts[1]),
            bottom_z=float(parts[2]),
            width_x=float(parts[3]), width_y=float(parts[4]),
            height=float(parts[5]), rotation=float(parts[6]),
            unknown1=_p(parts, 7, float, 0.0),
            unknown2=_p(parts, 8, float, 0.0),
            unknown3=_p(parts, 9, int, 0),
        )
    except (ValueError, IndexError):
        return None


def _parse_tcyc_line(line: str) -> Optional[IplTcyc]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 8:
            return None
        return IplTcyc(
            x1=float(parts[0]), y1=float(parts[1]), z1=float(parts[2]),
            x2=float(parts[3]), y2=float(parts[4]), z2=float(parts[5]),
            far_clip=int(parts[6]), extra_color=int(parts[7]),
            extra_color_intensity=_p(parts, 8, float, 0.0),
            falloff_dist=_p(parts, 9, float, 100.0),
            unused=_p(parts, 10, float, 0.0),
            lod_dist_mult=_p(parts, 11, float, 1.0),
        )
    except (ValueError, IndexError):
        return None


def _parse_zone_line(line: str) -> Optional[IplZone]:
    parts = [p.strip() for p in line.split(',')]
    try:
        if len(parts) < 9:
            return None
        return IplZone(
            name=parts[0].strip().strip('"'),
            zone_type=int(parts[1]),
            x1=float(parts[2]), y1=float(parts[3]), z1=float(parts[4]),
            x2=float(parts[5]), y2=float(parts[6]), z2=float(parts[7]),
            level=int(parts[8]),
        )
    except (ValueError, IndexError):
        return None


# ── Formatting helpers ────────────────────────────────────────────────

def _ff(v: float) -> str:
    """Format float: 6 decimal places."""
    return f'{v:.6f}'


def _format_inst_line(i: IplInstance) -> str:
    return (f'{i.model_id}, {i.model_name}, {i.interior}, '
            f'{_ff(i.pos_x)}, {_ff(i.pos_y)}, {_ff(i.pos_z)}, '
            f'{_ff(i.rot_x)}, {_ff(i.rot_y)}, {_ff(i.rot_z)}, {_ff(i.rot_w)}, '
            f'{i.lod_index}')


def _format_cull_line(c: IplCull) -> str:
    base = (f'{c.center_x}, {c.center_y}, {c.center_z}, '
            f'{c.unknown1}, {c.length}, {c.bottom}, '
            f'{c.width}, {c.unknown2}, {c.top}, {c.flag}')
    if c.has_mirror:
        return f'{base}, {c.mirror_vx}, {c.mirror_vy}, {c.mirror_vz}, {c.mirror_cm}'
    return f'{base}, {c.unknown3}'


def _format_grge_line(g: IplGarage) -> str:
    return (f'{_ff(g.pos_x)}, {_ff(g.pos_y)}, {_ff(g.pos_z)}, '
            f'{_ff(g.line_x)}, {_ff(g.line_y)}, '
            f'{_ff(g.cube_x)}, {_ff(g.cube_y)}, {_ff(g.cube_z)}, '
            f'{g.flags}, {g.garage_type}, {g.name}')


def _format_enex_line(e: IplEnex) -> str:
    return (f'{_ff(e.x1)}, {_ff(e.y1)}, {_ff(e.z1)}, {_ff(e.enter_angle)}, '
            f'{_ff(e.size_x)}, {_ff(e.size_y)}, {_ff(e.size_z)}, '
            f'{_ff(e.x2)}, {_ff(e.y2)}, {_ff(e.z2)}, {_ff(e.exit_angle)}, '
            f'{e.target_interior}, {e.flags}, {e.name}, '
            f'{e.sky}, {e.num_peds}, {e.time_on}, {e.time_off}')


def _format_pick_line(p: IplPickup) -> str:
    return f'{p.pickup_id}, {_ff(p.pos_x)}, {_ff(p.pos_y)}, {_ff(p.pos_z)}'


def _format_cars_line(c: IplCar) -> str:
    return (f'{_ff(c.pos_x)}, {_ff(c.pos_y)}, {_ff(c.pos_z)}, {_ff(c.angle)}, '
            f'{c.car_id}, {c.primary_color}, {c.secondary_color}, '
            f'{c.force_spawn}, {c.alarm}, {c.door_lock}, '
            f'{c.unknown1}, {c.unknown2}')


def _format_auzo_line(a: IplAuzo) -> str:
    if a.is_sphere:
        return (f'{a.name}, {a.audio_id}, {a.switch}, '
                f'{_ff(a.x1)}, {_ff(a.y1)}, {_ff(a.z1)}, {_ff(a.radius)}')
    return (f'{a.name}, {a.audio_id}, {a.switch}, '
            f'{_ff(a.x1)}, {_ff(a.y1)}, {_ff(a.z1)}, '
            f'{_ff(a.x2)}, {_ff(a.y2)}, {_ff(a.z2)}')


def _format_jump_line(j: IplJump) -> str:
    return (f'{_ff(j.start_lower_x)}, {_ff(j.start_lower_y)}, {_ff(j.start_lower_z)}, '
            f'{_ff(j.start_upper_x)}, {_ff(j.start_upper_y)}, {_ff(j.start_upper_z)}, '
            f'{_ff(j.target_lower_x)}, {_ff(j.target_lower_y)}, {_ff(j.target_lower_z)}, '
            f'{_ff(j.target_upper_x)}, {_ff(j.target_upper_y)}, {_ff(j.target_upper_z)}, '
            f'{_ff(j.camera_x)}, {_ff(j.camera_y)}, {_ff(j.camera_z)}, {j.reward}')


def _format_occl_line(o: IplOccl) -> str:
    return (f'{_ff(o.mid_x)}, {_ff(o.mid_y)}, {_ff(o.bottom_z)}, '
            f'{_ff(o.width_x)}, {_ff(o.width_y)}, {_ff(o.height)}, '
            f'{_ff(o.rotation)}, {o.unknown1}, {o.unknown2}, {o.unknown3}')


def _format_tcyc_line(t: IplTcyc) -> str:
    return (f'{_ff(t.x1)}, {_ff(t.y1)}, {_ff(t.z1)}, '
            f'{_ff(t.x2)}, {_ff(t.y2)}, {_ff(t.z2)}, '
            f'{t.far_clip}, {t.extra_color}, '
            f'{_ff(t.extra_color_intensity)}, {_ff(t.falloff_dist)}, '
            f'{_ff(t.unused)}, {_ff(t.lod_dist_mult)}')


def _format_zone_line(z: IplZone) -> str:
    return (f'{z.name}, {z.zone_type}, '
            f'{_ff(z.x1)}, {_ff(z.y1)}, {_ff(z.z1)}, '
            f'{_ff(z.x2)}, {_ff(z.y2)}, {_ff(z.z2)}, '
            f'{z.level}')


# ── LOD detection ────────────────────────────────────────────────────

def is_lod_name(model_name: str) -> bool:
    """Heuristic LOD detection from a model name.

    Vanilla GTA SA uses ``LOD<name>`` almost everywhere, but Rockstar's
    own tools and community mods ship assets with the ``LOD`` marker in
    less obvious places:

    - ``LOD<name>`` / ``lod<name>`` — prefix (most common)
    - ``<name>_LOD`` / ``<name>_lod`` — suffix with separator
    - ``<name>LOD`` — suffix without separator next to a digit/separator,
      e.g. ``tatar_str_2817_1LOD``
    - ``<prefix>LOD<suffix>`` — uppercase ``LOD`` spliced into the middle
      of an otherwise lowercase name (legacy Rockstar pattern, e.g.
      ``modeLODlaett`` paired with base ``modelaett``)

    For unreliable content prefer :func:`lod_instance_indices`, which
    reads the IPL ``lod_index`` cross-reference — that is authoritative
    no matter how the DFF happens to be named.
    """
    if not model_name:
        return False
    n = model_name.lower()
    if n.startswith('lod'):
        return True
    if n.endswith('_lod'):
        return True
    # Bare 'LOD' suffix — require a digit or separator just before it so
    # we don't classify words like 'clod', 'explod*', 'aerodrom' as LODs.
    if len(n) > 3 and n.endswith('lod'):
        prev = n[-4]
        if prev.isdigit() or prev in '_-':
            return True
    # Embedded uppercase ``LOD`` in an otherwise lowercase name. Matches
    # Rockstar's legacy pattern ``modeLODlaett`` but avoids all-caps
    # tokens like ``CLOD`` / ``FLOODGATE`` — we only flag if at least one
    # lowercase letter is directly adjacent to the uppercase marker.
    if 'LOD' in model_name:
        pos = model_name.find('LOD')
        before = model_name[:pos]
        after = model_name[pos + 3:]
        has_lower_before = bool(before) and before[-1].islower()
        has_lower_after = bool(after) and after[0].islower()
        if has_lower_before or has_lower_after:
            return True
    return False


def strip_lod_marker(name: str) -> str:
    """Strip the ``LOD`` marker from a model name, honouring the same
    naming conventions recognised by :func:`is_lod_name`.

    ::

        LODbush2b       -> bush2b
        lod_tree        -> tree
        tatar_str_1LOD  -> tatar_str_1
        bush1b_LOD      -> bush1b
        modeLODlaett    -> modelaett
        barrier1        -> barrier1   (unchanged — not a LOD)
    """
    if not name or not is_lod_name(name):
        return name
    n = name.lower()
    if n.startswith('lod'):
        stripped = name[3:]
        if stripped and stripped[0] in '_-':
            stripped = stripped[1:]
        return stripped
    if n.endswith('_lod'):
        return name[:-4]
    if len(n) > 3 and n.endswith('lod'):
        prev = n[-4]
        if prev.isdigit() or prev in '_-':
            clean = name[:-3]
            # Trim trailing separator left behind by e.g. 'foo_LOD' after
            # the earlier branch already matched — here only 'foo_1LOD'
            # and similar reach this point, so keep the digit/char intact.
            return clean.rstrip('_-') if clean.endswith(('_', '-')) else clean
    # Embedded uppercase LOD — drop the 3-char marker from its position.
    if 'LOD' in name:
        pos = name.find('LOD')
        before = name[:pos]
        after = name[pos + 3:]
        if (before and before[-1].islower()) or (after and after[0].islower()):
            return before + after
    return name


def lod_instance_indices(instances) -> set:
    """Return the set of IplInstance indices that another instance points to
    via its ``lod_index`` field — these are the authoritative LOD models.

    Usage:
        refs = lod_instance_indices(instances)
        for idx, inst in enumerate(instances):
            is_lod = idx in refs or is_lod_name(inst.model_name)
    """
    refs = set()
    n = len(instances)
    for inst in instances:
        li = getattr(inst, 'lod_index', -1)
        if 0 <= li < n:
            refs.add(li)
    return refs


# ── Reading ─────────────────────────────────────────────────────────

def read_ipl(filepath: str) -> IplFile:
    """Parse a text or binary IPL file and return structured data."""
    # Check for binary IPL
    try:
        with open(filepath, 'rb') as f:
            magic = f.read(4)
            if magic == b'bnry':
                f.seek(0)
                return _read_binary_ipl(f.read())
    except (IOError, OSError):
        pass

    return _read_text_ipl(filepath)


def _read_text_ipl(filepath: str) -> IplFile:
    """Parse a text IPL file."""
    ipl = IplFile()
    section = None

    _SECTIONS = {'inst', 'cull', 'path', 'grge', 'enex', 'pick',
                 'jump', 'tcyc', 'auzo', 'mult', 'cars', 'occl', 'zone'}

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            low = line.lower()

            if low == 'end':
                section = None
                continue

            if low in _SECTIONS:
                section = low
                continue

            if section == 'inst':
                obj = _parse_inst_line(line)
                if obj:
                    ipl.instances.append(obj)
            elif section == 'cull':
                obj = _parse_cull_line(line)
                if obj:
                    ipl.culls.append(obj)
            elif section == 'grge':
                obj = _parse_grge_line(line)
                if obj:
                    ipl.garages.append(obj)
            elif section == 'enex':
                obj = _parse_enex_line(line)
                if obj:
                    ipl.enexs.append(obj)
            elif section == 'pick':
                obj = _parse_pick_line(line)
                if obj:
                    ipl.pickups.append(obj)
            elif section == 'cars':
                obj = _parse_cars_line(line)
                if obj:
                    ipl.cars.append(obj)
            elif section == 'auzo':
                obj = _parse_auzo_line(line)
                if obj:
                    ipl.auzos.append(obj)
            elif section == 'jump':
                obj = _parse_jump_line(line)
                if obj:
                    ipl.jumps.append(obj)
            elif section == 'occl':
                obj = _parse_occl_line(line)
                if obj:
                    ipl.occls.append(obj)
            elif section == 'tcyc':
                obj = _parse_tcyc_line(line)
                if obj:
                    ipl.tcycs.append(obj)
            elif section == 'zone':
                obj = _parse_zone_line(line)
                if obj:
                    ipl.zones.append(obj)

    return ipl


def _read_binary_ipl(data: bytes) -> IplFile:
    """Parse a binary IPL file (bnry header)."""
    ipl = IplFile()

    if len(data) < 76:
        return ipl

    # Header: 76 bytes
    (num_inst, num_unk1, num_unk2, num_unk3, num_cars, num_unk4,
     off_inst, _, off_unk1, _, off_unk2, _, off_unk3, _,
     off_cars, _, off_unk4, _) = struct.unpack_from('<18I', data, 4)

    # Read INST entries (40 bytes each)
    for i in range(num_inst):
        off = off_inst + i * 40
        if off + 40 > len(data):
            break
        (px, py, pz, rx, ry, rz, rw, obj_id, interior,
         lod_idx) = struct.unpack_from('<7f3i', data, off)
        ipl.instances.append(IplInstance(
            model_id=obj_id, model_name='',
            interior=interior,
            pos_x=px, pos_y=py, pos_z=pz,
            rot_x=rx, rot_y=ry, rot_z=rz, rot_w=rw,
            lod_index=lod_idx,
        ))

    # Read CARS entries (48 bytes each)
    for i in range(num_cars):
        off = off_cars + i * 48
        if off + 48 > len(data):
            break
        (px, py, pz, angle, car_id, pc, sc, fs, alarm, dl,
         u1, u2) = struct.unpack_from('<4f8i', data, off)
        ipl.cars.append(IplCar(
            pos_x=px, pos_y=py, pos_z=pz,
            angle=angle, car_id=car_id,
            primary_color=pc, secondary_color=sc,
            force_spawn=fs, alarm=alarm, door_lock=dl,
            unknown1=u1, unknown2=u2,
        ))

    return ipl


# ── Writing ─────────────────────────────────────────────────────────

def _write_binary_ipl(ipl: IplFile) -> bytes:
    """Serialise IplFile to the GTA SA binary IPL (`bnry`) layout.

    Only ``inst`` and ``cars`` sections are stored in the binary body —
    the four ``num_unknown*`` slots mirror the header shape of vanilla
    files but carry no data. The header is exactly 76 bytes.
    """
    num_inst = len(ipl.instances)
    num_cars = len(ipl.cars)

    inst_size = num_inst * 40
    cars_size = num_cars * 48

    off_inst = 76
    off_unk1 = off_inst + inst_size
    off_unk2 = off_unk1
    off_unk3 = off_unk2
    off_cars = off_unk3
    off_unk4 = off_cars + cars_size

    header = b'bnry'
    header += struct.pack('<6I', num_inst, 0, 0, 0, num_cars, 0)
    header += struct.pack('<12I',
                          off_inst, 0,
                          off_unk1, 0,
                          off_unk2, 0,
                          off_unk3, 0,
                          off_cars, 0,
                          off_unk4, 0)
    assert len(header) == 76, f"bnry header is {len(header)} bytes"

    body = b''
    for inst in ipl.instances:
        body += struct.pack('<7f3i',
                            inst.pos_x, inst.pos_y, inst.pos_z,
                            inst.rot_x, inst.rot_y, inst.rot_z, inst.rot_w,
                            inst.model_id,
                            inst.interior,
                            inst.lod_index)
    for car in ipl.cars:
        body += struct.pack('<4f8i',
                            car.pos_x, car.pos_y, car.pos_z,
                            car.angle,
                            car.car_id,
                            car.primary_color, car.secondary_color,
                            car.force_spawn, car.alarm, car.door_lock,
                            car.unknown1, car.unknown2)

    return header + body


def write_binary_ipl(filepath: str, ipl: IplFile) -> None:
    """Write an IplFile as binary (`bnry`) IPL. Only inst+cars are stored."""
    with open(filepath, 'wb') as f:
        f.write(_write_binary_ipl(ipl))


def write_ipl(filepath: str, ipl: IplFile, *, binary: bool = False) -> None:
    """Write a text IPL file with all populated sections.

    If ``binary=True`` the file is emitted in the binary ``bnry`` format
    instead (only inst + cars sections are preserved).
    """
    if binary:
        write_binary_ipl(filepath, ipl)
        return
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        # Standard GTA SA IPL layout — all 12 sections are emitted, even
        # when empty, to match the vanilla file structure expected by
        # most tools (MEd, IPL Editor, etc.).

        f.write('inst\n')
        for i in ipl.instances:
            f.write(_format_inst_line(i) + '\n')
        f.write('end\n')

        f.write('cull\n')
        for c in ipl.culls:
            f.write(_format_cull_line(c) + '\n')
        f.write('end\n')

        # path section — SA reads nodes from nodes*.dat, IPL path block stays empty
        f.write('path\n')
        f.write('end\n')

        f.write('grge\n')
        for g in ipl.garages:
            f.write(_format_grge_line(g) + '\n')
        f.write('end\n')

        f.write('enex\n')
        for e in ipl.enexs:
            f.write(_format_enex_line(e) + '\n')
        f.write('end\n')

        f.write('pick\n')
        for p in ipl.pickups:
            f.write(_format_pick_line(p) + '\n')
        f.write('end\n')

        f.write('cars\n')
        for c in ipl.cars:
            f.write(_format_cars_line(c) + '\n')
        f.write('end\n')

        f.write('jump\n')
        for j in ipl.jumps:
            f.write(_format_jump_line(j) + '\n')
        f.write('end\n')

        f.write('tcyc\n')
        for t in ipl.tcycs:
            f.write(_format_tcyc_line(t) + '\n')
        f.write('end\n')

        f.write('auzo\n')
        for a in ipl.auzos:
            f.write(_format_auzo_line(a) + '\n')
        f.write('end\n')

        # mult section — not currently parsed/generated, always empty
        f.write('mult\n')
        f.write('end\n')

        f.write('occl\n')
        for o in ipl.occls:
            f.write(_format_occl_line(o) + '\n')
        f.write('end\n')

        # zone — only when populated (most IPLs don't carry zone data)
        if ipl.zones:
            f.write('zone\n')
            for z in ipl.zones:
                f.write(_format_zone_line(z) + '\n')
            f.write('end\n')


# ── Upsert / Remove (inst section only) ──────────────────────────────

def upsert_ipl(filepath: str, entries: list[IplInstance]) -> tuple[int, int]:
    """
    Insert or update inst entries in an existing IPL file.

    Matching is by model_id + model_name + position (to allow multiple
    instances of the same model). Returns (updated_count, added_count).
    """
    if not os.path.isfile(filepath):
        write_ipl(filepath, IplFile(instances=entries))
        return (0, len(entries))

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Keep entries as list — allow duplicates (multiple instances of same model)
    pending = list(entries)

    def _pos_match(a: IplInstance, b: IplInstance, eps: float = 0.001) -> bool:
        return (a.model_id == b.model_id
                and a.model_name.lower() == b.model_name.lower()
                and abs(a.pos_x - b.pos_x) < eps
                and abs(a.pos_y - b.pos_y) < eps
                and abs(a.pos_z - b.pos_z) < eps)

    updated = 0
    result_lines = []
    section = None
    inst_end_idx = -1

    _SECTIONS = {'inst', 'cull', 'path', 'grge', 'enex', 'pick',
                 'jump', 'tcyc', 'auzo', 'mult', 'cars', 'occl', 'zone'}

    for line in lines:
        stripped = line.strip()
        low = stripped.lower()

        if low == 'end' and section == 'inst':
            inst_end_idx = len(result_lines)
            section = None
            result_lines.append(line)
            continue

        if low in _SECTIONS:
            section = low
            result_lines.append(line)
            continue

        if section == 'inst' and stripped and not stripped.startswith('#'):
            parsed = _parse_inst_line(stripped)
            if parsed:
                # Find matching entry by position — allows multiple instances
                match_idx = None
                for i, e in enumerate(pending):
                    if _pos_match(parsed, e):
                        match_idx = i
                        break
                if match_idx is not None:
                    entry = pending.pop(match_idx)
                    result_lines.append(_format_inst_line(entry) + '\n')
                    updated += 1
                    continue

        result_lines.append(line)

    added = len(pending)
    if added > 0:
        if inst_end_idx >= 0:
            insert_lines = [_format_inst_line(e) + '\n' for e in pending]
            result_lines = (result_lines[:inst_end_idx]
                          + insert_lines
                          + result_lines[inst_end_idx:])
        else:
            result_lines.append('inst\n')
            for e in pending:
                result_lines.append(_format_inst_line(e) + '\n')
            result_lines.append('end\n')

    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(result_lines)

    return (updated, added)

    return (updated, added)


def remove_ipl(filepath: str, model_ids: set[int]) -> int:
    """Remove inst entries with given model_ids from IPL file.
    Recalculates lod_index for remaining entries.
    Returns count removed."""
    if not os.path.isfile(filepath):
        return 0

    ipl = read_ipl(filepath)
    original_count = len(ipl.instances)

    removed_indices = set()
    for i, inst in enumerate(ipl.instances):
        if inst.model_id in model_ids:
            removed_indices.add(i)

    if not removed_indices:
        return 0

    # Build old->new index map
    index_map = {}
    new_idx = 0
    for old_idx in range(original_count):
        if old_idx not in removed_indices:
            index_map[old_idx] = new_idx
            new_idx += 1

    # Filter and remap lod_index
    new_instances = []
    for i, inst in enumerate(ipl.instances):
        if i in removed_indices:
            continue
        if inst.lod_index >= 0:
            if inst.lod_index in index_map:
                inst.lod_index = index_map[inst.lod_index]
            else:
                inst.lod_index = -1
        new_instances.append(inst)

    # Rewrite preserving non-inst sections
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    result_lines = []
    section = None
    inst_written = False

    for line in lines:
        stripped = line.strip()
        low = stripped.lower()

        if low == 'end' and section == 'inst':
            if not inst_written:
                for inst in new_instances:
                    result_lines.append(_format_inst_line(inst) + '\n')
                inst_written = True
            section = None
            result_lines.append(line)
            continue

        if low == 'inst':
            section = low
            result_lines.append(line)
            continue

        if section == 'inst' and stripped and not stripped.startswith('#'):
            continue  # skip old inst lines

        result_lines.append(line)

    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(result_lines)

    return len(removed_indices)
