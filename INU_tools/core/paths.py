"""
GTA SA path file readers/writers.

Supported formats:
  - paths.ipl   — path definitions for gta.dat (text, groups of 12 nodes)
  - tracks.dat  — train rail paths (text)
  - nodes*.dat  — compiled ped/vehicle navigation nodes (binary)

No Blender dependency — pure Python.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import struct


# ═══════════════════════════════════════════════════════════════════════
# FLIGHT PATHS (flight.dat)
# ═══════════════════════════════════════════════════════════════════════
#
# Text file format:
#   Each line: X, Y, Z  (comma-separated floats)
#   Empty line = end of current path, start of next
#   Planes follow waypoints sequentially, then loop.

@dataclass
class FlightPoint:
    """One waypoint in a flight path."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class FlightPath:
    """One complete flight route."""
    points: List[FlightPoint] = field(default_factory=list)


@dataclass
class FlightFile:
    """Collection of flight paths."""
    paths: List[FlightPath] = field(default_factory=list)


def read_flight(filepath: str) -> FlightFile:
    """Parse flight.dat and return structured data."""
    result = FlightFile()
    current = FlightPath()

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                # Empty line = end of current path
                if current.points:
                    result.paths.append(current)
                    current = FlightPath()
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                try:
                    pt = FlightPoint(
                        x=float(parts[0]),
                        y=float(parts[1]),
                        z=float(parts[2]),
                    )
                    current.points.append(pt)
                except ValueError:
                    continue

    # Last path if file doesn't end with empty line
    if current.points:
        result.paths.append(current)

    return result


def write_flight(filepath: str, data: FlightFile) -> int:
    """Write flight paths to flight.dat. Returns path count."""
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        for i, path in enumerate(data.paths):
            for pt in path.points:
                f.write(f"{pt.x:.4f}, {pt.y:.4f}, {pt.z:.4f}\n")
            # Empty line between paths
            if i < len(data.paths) - 1:
                f.write('\n')

    return len(data.paths)


# ═══════════════════════════════════════════════════════════════════════
# PATHS.IPL (path definitions for gta.dat)
# ═══════════════════════════════════════════════════════════════════════
#
# Text file format (IPL with 'path' section):
#   path
#   GroupType, ExternalIndex     ← 0=ped, 1=vehicle
#   <tab>NodeType, LinkID, AreaID, X, Y, Z, Unknown, Width, LeftLanes, RightLanes, MedianWidth, Flags, SpawnRate
#   ...exactly 12 nodes per group...
#   end
#
# NodeType: 0=empty/unused, 1=external link, 2=internal node
# Groups always have 12 nodes; unused slots filled with NodeType=0

NODES_PER_GROUP = 12


@dataclass
class PathIPLNode:
    """One node in a paths.ipl group."""
    node_type: int = 0       # 0=empty, 1=external, 2=internal
    link_id: int = -1        # Next node index (-1 = none)
    area_id: int = 0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    unknown: float = 0.0
    width: int = 1
    left_lanes: int = 1
    right_lanes: int = 1
    median_width: int = 0
    flags: int = 1
    spawn_rate: int = 0


@dataclass
class PathIPLGroup:
    """One group of 12 nodes (vehicle or ped path)."""
    group_type: int = 1      # 0=ped, 1=vehicle
    external_index: int = -1
    nodes: List[PathIPLNode] = field(default_factory=list)


@dataclass
class PathIPLFile:
    """Collection of path groups from a paths.ipl file."""
    groups: List[PathIPLGroup] = field(default_factory=list)


# ── PathIPLNode.flags bit constants ─────────────────────────────────
#
# Based on SA path-node reverse-engineering (GTAMods wiki, Fastman92):
#   bits 0-3   : speed limit           (0 = slow, higher = faster)
#   bits 4-7   : special behaviour     (traffic lights encoded here)
#   bits 8-11  : traffic light kind    (0 none, 1 normal, 2 rail, 3 bus)
#   bit 12     : roadblock             (cops spawn barriers here)
#   bits 13-15 : reserved

PATH_FLAG_ROADBLOCK       = 1 << 12
PATH_FLAG_TRAFFIC_MASK    = 0xF << 8
PATH_FLAG_TRAFFIC_SHIFT   = 8
PATH_FLAG_SPEED_MASK      = 0xF
PATH_FLAG_BEHAVIOUR_MASK  = 0xF << 4
PATH_FLAG_BEHAVIOUR_SHIFT = 4

TRAFFIC_LIGHT_NONE   = 0
TRAFFIC_LIGHT_NORMAL = 1
TRAFFIC_LIGHT_RAIL   = 2
TRAFFIC_LIGHT_BUS    = 3


def decode_node_flags(flags: int) -> dict:
    """Expand the packed flags int into a readable dict."""
    return {
        'speed_limit': flags & PATH_FLAG_SPEED_MASK,
        'behaviour': (flags & PATH_FLAG_BEHAVIOUR_MASK) >> PATH_FLAG_BEHAVIOUR_SHIFT,
        'traffic_light': (flags & PATH_FLAG_TRAFFIC_MASK) >> PATH_FLAG_TRAFFIC_SHIFT,
        'roadblock': bool(flags & PATH_FLAG_ROADBLOCK),
    }


def encode_node_flags(*, speed_limit: int = 0, behaviour: int = 0,
                      traffic_light: int = 0, roadblock: bool = False,
                      keep_bits: int = 0) -> int:
    """Pack individual fields back into the flags int. `keep_bits` lets
    callers preserve unknown bits read from an existing file."""
    v = keep_bits & ~(PATH_FLAG_SPEED_MASK | PATH_FLAG_BEHAVIOUR_MASK
                      | PATH_FLAG_TRAFFIC_MASK | PATH_FLAG_ROADBLOCK)
    v |= speed_limit & PATH_FLAG_SPEED_MASK
    v |= (behaviour << PATH_FLAG_BEHAVIOUR_SHIFT) & PATH_FLAG_BEHAVIOUR_MASK
    v |= (traffic_light << PATH_FLAG_TRAFFIC_SHIFT) & PATH_FLAG_TRAFFIC_MASK
    if roadblock:
        v |= PATH_FLAG_ROADBLOCK
    return v


def read_paths_ipl(filepath: str) -> PathIPLFile:
    """Parse a paths.ipl file (path section only)."""
    result = PathIPLFile()

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    in_path = False
    current_group = None

    for raw_line in lines:
        line = raw_line.strip()

        if line == 'path':
            in_path = True
            continue
        if line == 'end' and in_path:
            if current_group and current_group.nodes:
                result.groups.append(current_group)
                current_group = None
            in_path = False
            continue
        if not in_path:
            continue

        # Tab-indented = node line, otherwise = group header
        if raw_line.startswith('\t') or raw_line.startswith('  '):
            # Node line
            if current_group is None:
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 13:
                try:
                    node = PathIPLNode(
                        node_type=int(parts[0]),
                        link_id=int(parts[1]),
                        area_id=int(parts[2]),
                        x=float(parts[3]),
                        y=float(parts[4]),
                        z=float(parts[5]),
                        unknown=float(parts[6]),
                        width=int(parts[7]),
                        left_lanes=int(parts[8]),
                        right_lanes=int(parts[9]),
                        median_width=int(parts[10]),
                        flags=int(parts[11]),
                        spawn_rate=int(parts[12]),
                    )
                    current_group.nodes.append(node)
                except ValueError:
                    continue
        else:
            # Group header: GroupType, ExternalIndex
            if current_group and current_group.nodes:
                result.groups.append(current_group)
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 2:
                try:
                    current_group = PathIPLGroup(
                        group_type=int(parts[0]),
                        external_index=int(parts[1]),
                    )
                except ValueError:
                    current_group = None

    if current_group and current_group.nodes:
        result.groups.append(current_group)

    return result


def write_paths_ipl(filepath: str, data: PathIPLFile) -> int:
    """Write path groups to a paths.ipl file. Returns group count."""
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# IPL generated by INU Tools\n')
        f.write('inst\nend\ncull\nend\npath\n')

        for group in data.groups:
            f.write(f"{group.group_type}, {group.external_index}\n")

            # Write nodes, pad to 12
            for i in range(NODES_PER_GROUP):
                if i < len(group.nodes):
                    n = group.nodes[i]
                    f.write(f"\t{n.node_type}, {n.link_id}, {n.area_id}, "
                            f"{n.x:.4g}, {n.y:.4g}, {n.z:.6g}, {n.unknown:.4g}, "
                            f"{n.width}, {n.left_lanes}, {n.right_lanes}, "
                            f"{n.median_width}, {n.flags}, {n.spawn_rate}\n")
                else:
                    # Empty node
                    f.write("\t0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0\n")

        f.write('end\n')

    return len(data.groups)


# ═══════════════════════════════════════════════════════════════════════
# TRAIN TRACKS (tracks.dat, tracks2.dat, tracks3.dat, tracks4.dat)
# ═══════════════════════════════════════════════════════════════════════
#
# Text file format:
#   Line 1: node count (integer)
#   Each subsequent line: X Y Z Flag
#     X, Y, Z = position (floats)
#     Flag = 0 or 1 (0 = normal, 1 = station/stop)
#
# tracks.dat  = track 1 (main LS-SF-LV loop)
# tracks2.dat = track 2 (secondary)
# tracks3.dat = track 3
# tracks4.dat = track 4


@dataclass
class TrackNode:
    """One node on a train track."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    flag: int = 0  # 0 = normal, 1 = station stop


@dataclass
class TrackFile:
    """One train track (one file)."""
    nodes: List[TrackNode] = field(default_factory=list)


def read_track(filepath: str) -> TrackFile:
    """Parse a tracks*.dat text file."""
    result = TrackFile()

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    if not lines:
        return result

    # First line is node count
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 3:
            try:
                node = TrackNode(
                    x=float(parts[0]),
                    y=float(parts[1]),
                    z=float(parts[2]),
                    flag=int(float(parts[3])) if len(parts) >= 4 else 0,
                )
                result.nodes.append(node)
            except ValueError:
                continue

    return result


def write_track(filepath: str, track: TrackFile) -> int:
    """Write train track to text file. Returns node count."""
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f"{len(track.nodes)}\n")
        for node in track.nodes:
            f.write(f"{node.x:.2f} {node.y:.2f} {node.z:.5f} {node.flag}\n")

    return len(track.nodes)


# ═══════════════════════════════════════════════════════════════════════
# VEHICLE/PED NODES (nodes0.dat — nodes63.dat)
# ═══════════════════════════════════════════════════════════════════════
#
# Binary format — header + path nodes + navi nodes + links
#
# Header (20 bytes):
#   uint32 numNodes
#   uint32 numVehicleNodes
#   uint32 numPedNodes
#   uint32 numNaviNodes
#   uint32 numLinks
#
# Each PathNode (28 bytes):
#   int16  memAddress (unused, 0)
#   int16  unknown1 (0)
#   int16  posX      (compressed: real = value / 8.0)
#   int16  posY
#   int16  posZ
#   int16  heuristic (path distance, usually 0x7FFE)
#   uint16 linkID    (index of first link)
#   uint16 areaID    (zone area ID, 0-63)
#   uint16 nodeID    (node index within area)
#   uint8  pathWidth
#   uint8  nodeType  (flags: ped/vehicle, etc.)
#   uint32 flags
#
# Each NaviNode (14 bytes):
#   int16  posX (compressed / 8.0)
#   int16  posY
#   uint16 areaID
#   uint16 nodeID
#   int8   dirX  (direction vector, -100..100)
#   int8   dirY
#   uint32 flags
#
# Each Link (4 bytes):
#   uint16 areaID
#   uint16 nodeID

PATH_NODE_SIZE = 28
NAVI_NODE_SIZE = 14
LINK_SIZE = 4

# FLA4 (Fastman Limit Adjuster 4) extension — unofficial format that
# inflates each PathNode by 12 bytes to store per-node speed limit,
# spawn probability and a lane override. File is tagged with the
# magic "FLA4" at offset 0 and the original 5-uint32 count header
# shifts to offset 4.
FLA4_MAGIC = b'FLA4'
FLA4_NODE_EXTRA = 12   # bytes appended after a normal PathNode
FLA4_PATH_NODE_SIZE = PATH_NODE_SIZE + FLA4_NODE_EXTRA  # 40


@dataclass
class PathNode:
    """Vehicle or pedestrian path node."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    link_id: int = 0
    area_id: int = 0
    node_id: int = 0
    path_width: int = 0
    node_type: int = 0
    flags: int = 0
    is_vehicle: bool = True  # True = vehicle, False = ped
    # FLA4 extension fields (unused in vanilla SA format)
    spawn_probability: int = 0
    speed_limit_kmh: int = 0
    lane_count_override: int = 0


@dataclass
class NaviNode:
    """Navigation node (intermediate point between path nodes)."""
    x: float = 0.0
    y: float = 0.0
    area_id: int = 0
    node_id: int = 0
    dir_x: int = 0
    dir_y: int = 0
    flags: int = 0


@dataclass
class PathLink:
    """Link between two path nodes."""
    area_id: int = 0
    node_id: int = 0


@dataclass
class NodesFile:
    """One nodes*.dat file (one zone area)."""
    vehicle_nodes: List[PathNode] = field(default_factory=list)
    ped_nodes: List[PathNode] = field(default_factory=list)
    navi_nodes: List[NaviNode] = field(default_factory=list)
    links: List[PathLink] = field(default_factory=list)
    extra_data: bytes = b''  # Raw bytes after links (naviLinks, linkLengths, etc.)
    fla4: bool = False       # True when loaded from / meant to write a FLA4 file


def read_nodes(filepath: str) -> NodesFile:
    """Parse a nodes*.dat binary file. Detects FLA4 extended format."""
    result = NodesFile()

    with open(filepath, 'rb') as f:
        data = f.read()

    if len(data) < 20:
        return result

    # FLA4 marker — skip the 4-byte magic and read the normal header after
    header_offset = 0
    if data[:4] == FLA4_MAGIC:
        result.fla4 = True
        header_offset = 4
        if len(data) < 24:
            return result

    num_nodes, num_vehicle, num_ped, num_navi, num_links = struct.unpack_from(
        '<5I', data, header_offset)
    offset = header_offset + 20

    node_size = FLA4_PATH_NODE_SIZE if result.fla4 else PATH_NODE_SIZE

    # Read all path nodes
    for i in range(num_nodes):
        if offset + node_size > len(data):
            break
        # PathNode: uint32 mem, uint32 unk, int16 x/y/z, int16 heuristic,
        #           uint16 linkID/areaID/nodeID, uint8 width/type, uint32 flags
        (mem, unk1, px, py, pz, heuristic,
         link_id, area_id, node_id,
         path_width, node_type, flags) = struct.unpack_from(
             '<II4h3HBBi', data, offset)

        extra_spawn = extra_speed = extra_lanes = 0
        if result.fla4:
            (extra_spawn, extra_speed, extra_lanes) = struct.unpack_from(
                '<III', data, offset + PATH_NODE_SIZE)

        offset += node_size

        node = PathNode(
            x=px / 8.0,
            y=py / 8.0,
            z=pz / 8.0,
            link_id=link_id,
            area_id=area_id,
            node_id=node_id,
            path_width=path_width,
            node_type=node_type,
            flags=flags,
            is_vehicle=(i < num_vehicle),
            spawn_probability=extra_spawn,
            speed_limit_kmh=extra_speed,
            lane_count_override=extra_lanes,
        )
        if i < num_vehicle:
            result.vehicle_nodes.append(node)
        else:
            result.ped_nodes.append(node)

    # Read navi nodes
    for i in range(num_navi):
        if offset + NAVI_NODE_SIZE > len(data):
            break
        (nx, ny, area_id, node_id, dir_x, dir_y, nflags) = struct.unpack_from('<2h2H2bi', data, offset)
        offset += NAVI_NODE_SIZE

        result.navi_nodes.append(NaviNode(
            x=nx / 8.0,
            y=ny / 8.0,
            area_id=area_id,
            node_id=node_id,
            dir_x=dir_x,
            dir_y=dir_y,
            flags=nflags,
        ))

    # Read links
    for i in range(num_links):
        if offset + LINK_SIZE > len(data):
            break
        area_id, node_id = struct.unpack_from('<2H', data, offset)
        offset += LINK_SIZE

        result.links.append(PathLink(area_id=area_id, node_id=node_id))

    # Preserve remaining data (naviLinks, linkLengths, pathIntersections, etc.)
    if offset < len(data):
        result.extra_data = data[offset:]

    return result


def write_nodes(filepath: str, nodes_file: NodesFile) -> int:
    """Write nodes*.dat binary file. Returns total node count.

    If ``nodes_file.fla4`` is set, the output is written in FLA4 extended
    format (FLA4 magic + 40-byte path nodes with spawn/speed/lane fields).
    """
    num_vehicle = len(nodes_file.vehicle_nodes)
    num_ped = len(nodes_file.ped_nodes)
    num_nodes = num_vehicle + num_ped
    num_navi = len(nodes_file.navi_nodes)
    num_links = len(nodes_file.links)

    with open(filepath, 'wb') as f:
        if nodes_file.fla4:
            f.write(FLA4_MAGIC)

        # Header
        f.write(struct.pack('<5I', num_nodes, num_vehicle, num_ped, num_navi, num_links))

        # Path nodes (vehicle first, then ped)
        for node in (nodes_file.vehicle_nodes + nodes_file.ped_nodes):
            px = int(node.x * 8.0)
            py = int(node.y * 8.0)
            pz = int(node.z * 8.0)
            f.write(struct.pack('<II4h3HBBi',
                                0, 0,  # memAddress, unknown
                                px, py, pz,
                                0x7FFE,  # heuristic
                                node.link_id, node.area_id, node.node_id,
                                node.path_width, node.node_type, node.flags))
            if nodes_file.fla4:
                f.write(struct.pack('<III',
                                    node.spawn_probability,
                                    node.speed_limit_kmh,
                                    node.lane_count_override))

        # Navi nodes
        for navi in nodes_file.navi_nodes:
            nx = int(navi.x * 8.0)
            ny = int(navi.y * 8.0)
            f.write(struct.pack('<2h2H2bi',
                                nx, ny,
                                navi.area_id, navi.node_id,
                                navi.dir_x, navi.dir_y,
                                navi.flags))

        # Links
        for link in nodes_file.links:
            f.write(struct.pack('<2H', link.area_id, link.node_id))

        # Extra data (naviLinks, linkLengths, etc.)
        if nodes_file.extra_data:
            f.write(nodes_file.extra_data)

    return num_nodes
