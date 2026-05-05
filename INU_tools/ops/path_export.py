# INU_tools.ops.path_export — Export Blender objects to GTA SA path files

import ast
import bpy
from ..core.paths import (
    FlightFile, FlightPath, FlightPoint, write_flight,
    TrackFile, TrackNode, write_track,
    NodesFile, PathNode, NaviNode, PathLink, write_nodes,
    PathIPLFile, PathIPLGroup, PathIPLNode, write_paths_ipl,
)


def export_flight(filepath: str, objects=None):
    """Export curve objects as flight.dat."""
    if objects is None:
        objects = [o for o in bpy.context.selected_objects
                   if o.type == 'CURVE' and o.get('path_type') == 'flight']

    data = FlightFile()

    for obj in sorted(objects, key=lambda o: o.get('path_index', 0)):
        curve = obj.data
        mat_w = obj.matrix_world

        for spline in curve.splines:
            path = FlightPath()
            for point in spline.points:
                co = mat_w @ point.co.to_3d()
                path.points.append(FlightPoint(x=co.x, y=co.y, z=co.z))
            if path.points:
                data.paths.append(path)

    return write_flight(filepath, data)


def export_track(filepath: str, obj=None):
    """Export a curve object as tracks*.dat."""
    if obj is None:
        for o in bpy.context.selected_objects:
            if o.type == 'CURVE' and o.get('path_type') == 'track':
                obj = o
                break

    if not obj or obj.type != 'CURVE':
        return 0

    track = TrackFile()
    mat_w = obj.matrix_world

    # Restore station flags
    station_indices = set()
    raw = obj.get('station_indices', '[]')
    try:
        station_indices = set(ast.literal_eval(raw))
    except Exception:
        pass

    idx = 0
    for spline in obj.data.splines:
        for point in spline.points:
            co = mat_w @ point.co.to_3d()
            flag = 1 if idx in station_indices else 0
            track.nodes.append(TrackNode(x=co.x, y=co.y, z=co.z, flag=flag))
            idx += 1

    return write_track(filepath, track)


def export_nodes(filepath: str, objects=None, *, fla4: bool = False):
    """Export mesh objects as nodes*.dat. Set ``fla4=True`` to emit the
    extended Fastman Limit Adjuster 4 format."""
    if objects is None:
        objects = [o for o in bpy.context.selected_objects
                   if o.type == 'MESH' and o.get('path_type', '').startswith('nodes_')]

    nodes_file = NodesFile()
    nodes_file.fla4 = fla4

    for obj in objects:
        path_type = obj.get('path_type', '')
        mat_w = obj.matrix_world
        mesh = obj.data

        for i, vert in enumerate(mesh.vertices):
            co = mat_w @ vert.co
            node = PathNode(
                x=co.x, y=co.y, z=co.z,
                link_id=obj.get(f'node_{i}_link', 0),
                area_id=obj.get(f'node_{i}_area', 0),
                node_id=obj.get(f'node_{i}_id', i),
                path_width=obj.get(f'node_{i}_width', 0),
                node_type=obj.get(f'node_{i}_type', 0),
                flags=obj.get(f'node_{i}_flags', 0),
                spawn_probability=obj.get(f'node_{i}_spawn', 0),
                speed_limit_kmh=obj.get(f'node_{i}_speed', 0),
                lane_count_override=obj.get(f'node_{i}_lanes', 0),
            )

            if path_type == 'nodes_vehicle':
                nodes_file.vehicle_nodes.append(node)
            elif path_type == 'nodes_ped':
                nodes_file.ped_nodes.append(node)

        if path_type == 'nodes_navi':
            for i, vert in enumerate(mesh.vertices):
                co = mat_w @ vert.co
                nodes_file.navi_nodes.append(NaviNode(
                    x=co.x, y=co.y,
                    area_id=obj.get(f'navi_{i}_area', 0),
                    node_id=obj.get(f'navi_{i}_node', 0),
                    dir_x=obj.get(f'navi_{i}_dx', 0),
                    dir_y=obj.get(f'navi_{i}_dy', 0),
                    flags=obj.get(f'navi_{i}_flags', 0),
                ))

        # Restore links
        num_links = obj.get('num_links', 0)
        for i in range(num_links):
            nodes_file.links.append(PathLink(
                area_id=obj.get(f'link_{i}_area', 0),
                node_id=obj.get(f'link_{i}_node', 0),
            ))

    return write_nodes(filepath, nodes_file)


def export_paths_ipl(filepath: str, objects=None):
    """Export curve objects as paths.ipl.

    Auto-splits long curves into groups of 12 nodes.
    Links between groups are set automatically.
    """
    if objects is None:
        objects = [o for o in bpy.context.selected_objects
                   if o.type == 'CURVE' and o.get('path_type') == 'path_ipl']

    data = PathIPLFile()

    for obj in sorted(objects, key=lambda o: o.get('group_index', 0)):
        group_type = obj.get('group_type', 1)
        mat_w = obj.matrix_world

        # Collect all curve points
        all_points = []
        for spline in obj.data.splines:
            for point in spline.points:
                co = mat_w @ point.co.to_3d()
                all_points.append(co)

        if not all_points:
            continue

        # Get default node properties from object
        def_width = obj.get('pn_0_width', 1)
        def_ll = obj.get('pn_0_ll', 1)
        def_rl = obj.get('pn_0_rl', 1)
        def_mw = obj.get('pn_0_mw', 0)
        def_flags = obj.get('pn_0_flags', 1)
        def_spawn = obj.get('pn_0_spawn', 0)

        # Max internal nodes per group = 10 (slot 0-9 internal, 10-11 for external links)
        MAX_INTERNAL = 10
        chunks = []
        for i in range(0, len(all_points), MAX_INTERNAL):
            chunks.append(all_points[i:i + MAX_INTERNAL])

        for ci, chunk in enumerate(chunks):
            group = PathIPLGroup(group_type=group_type, external_index=-1)

            # Internal nodes (type=2)
            for pi, co in enumerate(chunk):
                next_link = pi + 1 if pi < len(chunk) - 1 else -1
                node = PathIPLNode(
                    node_type=2,
                    link_id=next_link,
                    area_id=0,
                    x=co.x, y=co.y, z=co.z,
                    width=def_width,
                    left_lanes=def_ll,
                    right_lanes=def_rl,
                    median_width=def_mw,
                    flags=def_flags,
                    spawn_rate=def_spawn,
                )
                group.nodes.append(node)

            # External link to next group (type=1)
            if ci < len(chunks) - 1:
                next_co = chunks[ci + 1][0]
                group.nodes.append(PathIPLNode(
                    node_type=1, link_id=0, area_id=0,
                    x=next_co.x, y=next_co.y, z=next_co.z,
                    width=def_width, left_lanes=def_ll, right_lanes=def_rl,
                    flags=def_flags,
                ))

            # External link to previous group (type=1)
            if ci > 0:
                prev_co = chunks[ci - 1][-1]
                group.nodes.append(PathIPLNode(
                    node_type=1, link_id=len(chunk) - 1, area_id=0,
                    x=prev_co.x, y=prev_co.y, z=prev_co.z,
                    width=def_width, left_lanes=def_ll, right_lanes=def_rl,
                    flags=def_flags,
                ))

            data.groups.append(group)

    return write_paths_ipl(filepath, data)
