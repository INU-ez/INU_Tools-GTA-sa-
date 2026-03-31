# INU_tools.ops.path_import — Import GTA SA path files into Blender

import bpy
from ..core.paths import read_flight, read_track, read_nodes, read_paths_ipl


def import_flight(filepath: str, context=None):
    """Import flight.dat as curve objects in Blender."""
    data = read_flight(filepath)
    if not data.paths:
        return []

    col = _get_or_create_collection("Flight Paths")
    created = []

    for i, path in enumerate(data.paths):
        if not path.points:
            continue

        curve = bpy.data.curves.new(f"FlightPath_{i}", type='CURVE')
        curve.dimensions = '3D'
        spline = curve.splines.new('POLY')
        spline.points.add(len(path.points) - 1)

        for j, pt in enumerate(path.points):
            spline.points[j].co = (pt.x, pt.y, pt.z, 1.0)

        obj = bpy.data.objects.new(f"FlightPath_{i}", curve)
        obj['path_type'] = 'flight'
        obj['path_index'] = i
        col.objects.link(obj)

        # Style
        _setup_path_curve(curve)
        _assign_path_material(obj, 'FlightPath_Mat', (1.0, 1.0, 0.0, 0.8))  # Yellow

        created.append(obj)

    return created


def import_track(filepath: str, context=None):
    """Import tracks*.dat as a curve object in Blender."""
    import os
    data = read_track(filepath)
    if not data.nodes:
        return []

    col = _get_or_create_collection("Train Tracks")
    name = os.path.splitext(os.path.basename(filepath))[0]

    curve = bpy.data.curves.new(name, type='CURVE')
    curve.dimensions = '3D'
    spline = curve.splines.new('POLY')
    spline.points.add(len(data.nodes) - 1)
    spline.use_cyclic_u = True  # Train tracks loop

    station_indices = []
    for j, node in enumerate(data.nodes):
        spline.points[j].co = (node.x, node.y, node.z, 1.0)
        if node.flag == 1:
            station_indices.append(j)

    obj = bpy.data.objects.new(name, curve)
    obj['path_type'] = 'track'
    obj['station_indices'] = str(station_indices)  # Store station stops
    col.objects.link(obj)

    # Style
    _setup_path_curve(curve)
    _assign_path_material(obj, 'TrainTrack_Mat', (0.6, 0.3, 0.0, 0.8))  # Brown

    return [obj]


def import_nodes(filepath: str, context=None):
    """Import nodes*.dat as mesh points + edge connections in Blender."""
    import os
    data = read_nodes(filepath)

    col = _get_or_create_collection("Path Nodes")
    name = os.path.splitext(os.path.basename(filepath))[0]
    created = []

    # Vehicle nodes as mesh with vertices
    if data.vehicle_nodes:
        obj = _create_nodes_mesh(f"{name}_vehicle", data.vehicle_nodes, col)
        obj['path_type'] = 'nodes_vehicle'
        _assign_path_material(obj, 'VehicleNode_Mat', (0.0, 0.5, 1.0, 0.8))  # Blue
        created.append(obj)

    # Ped nodes as mesh with vertices
    if data.ped_nodes:
        obj = _create_nodes_mesh(f"{name}_ped", data.ped_nodes, col)
        obj['path_type'] = 'nodes_ped'
        _assign_path_material(obj, 'PedNode_Mat', (0.0, 1.0, 0.3, 0.8))  # Green
        created.append(obj)

    # Navi nodes
    if data.navi_nodes:
        mesh = bpy.data.meshes.new(f"{name}_navi")
        verts = [(n.x, n.y, 0.0) for n in data.navi_nodes]  # NaviNodes are 2D (X,Y)
        mesh.from_pydata(verts, [], [])
        mesh.update()
        obj = bpy.data.objects.new(f"{name}_navi", mesh)
        obj['path_type'] = 'nodes_navi'

        # Store navi data as custom props
        for i, n in enumerate(data.navi_nodes):
            obj[f'navi_{i}_area'] = n.area_id
            obj[f'navi_{i}_node'] = n.node_id
            obj[f'navi_{i}_dx'] = n.dir_x
            obj[f'navi_{i}_dy'] = n.dir_y
            obj[f'navi_{i}_flags'] = n.flags

        _assign_path_material(obj, 'NaviNode_Mat', (1.0, 0.5, 0.0, 0.8))  # Orange
        col.objects.link(obj)
        created.append(obj)

    # Store links data on vehicle object for export
    if created and data.links:
        obj = created[0]
        for i, link in enumerate(data.links):
            obj[f'link_{i}_area'] = link.area_id
            obj[f'link_{i}_node'] = link.node_id
        obj['num_links'] = len(data.links)

    return created


def import_paths_ipl(filepath: str, context=None):
    """Import paths.ipl as curve objects in Blender.

    Each path group becomes a curve. Vehicle = blue, Ped = green.
    Only non-empty nodes (node_type > 0) are imported as curve points.
    """
    data = read_paths_ipl(filepath)
    if not data.groups:
        return []

    col = _get_or_create_collection("Path IPL")
    created = []

    for i, group in enumerate(data.groups):
        # Filter out empty nodes
        real_nodes = [n for n in group.nodes if n.node_type > 0]
        if not real_nodes:
            continue

        is_vehicle = (group.group_type == 1)
        prefix = "VehPath" if is_vehicle else "PedPath"

        curve = bpy.data.curves.new(f"{prefix}_{i}", type='CURVE')
        curve.dimensions = '3D'
        spline = curve.splines.new('POLY')
        spline.points.add(len(real_nodes) - 1)

        for j, node in enumerate(real_nodes):
            spline.points[j].co = (node.x, node.y, node.z, 1.0)

        obj = bpy.data.objects.new(f"{prefix}_{i}", curve)
        obj['path_type'] = 'path_ipl'
        obj['group_type'] = group.group_type
        obj['group_index'] = i
        obj['external_index'] = group.external_index

        # Store full node data for round-trip export
        for j, node in enumerate(group.nodes):
            obj[f'pn_{j}_type'] = node.node_type
            obj[f'pn_{j}_link'] = node.link_id
            obj[f'pn_{j}_area'] = node.area_id
            obj[f'pn_{j}_unk'] = node.unknown
            obj[f'pn_{j}_width'] = node.width
            obj[f'pn_{j}_ll'] = node.left_lanes
            obj[f'pn_{j}_rl'] = node.right_lanes
            obj[f'pn_{j}_mw'] = node.median_width
            obj[f'pn_{j}_flags'] = node.flags
            obj[f'pn_{j}_spawn'] = node.spawn_rate
        obj['pn_count'] = len(group.nodes)

        # Style
        _setup_path_curve(curve)
        if is_vehicle:
            _assign_path_material(obj, 'VehiclePath_IPL_Mat', (0.0, 0.5, 1.0, 0.8))
        else:
            _assign_path_material(obj, 'PedPath_IPL_Mat', (0.0, 1.0, 0.3, 0.8))

        col.objects.link(obj)
        created.append(obj)

    return created


# ── Helpers ────────────────────────────────────────────────────────

def _setup_path_curve(curve):
    """Apply standard path curve display settings."""
    curve.dimensions = '3D'
    curve.bevel_depth = 0.1
    curve.bevel_resolution = 0
    curve.use_fill_caps = True
    curve.extrude = 0.5
    curve.offset = 0.0


def _get_or_create_collection(name: str):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _create_nodes_mesh(name, nodes, collection):
    """Create a mesh object with a vertex per node, storing node data."""
    mesh = bpy.data.meshes.new(name)
    verts = [(n.x, n.y, n.z) for n in nodes]
    mesh.from_pydata(verts, [], [])
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)

    # Store node properties
    for i, n in enumerate(nodes):
        obj[f'node_{i}_link'] = n.link_id
        obj[f'node_{i}_area'] = n.area_id
        obj[f'node_{i}_id'] = n.node_id
        obj[f'node_{i}_width'] = n.path_width
        obj[f'node_{i}_type'] = n.node_type
        obj[f'node_{i}_flags'] = n.flags

    collection.objects.link(obj)
    return obj


def _assign_path_material(obj, mat_name, color):
    """Assign a colored material to a path object."""
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        for n in mat.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs['Base Color'].default_value = color
                n.inputs['Alpha'].default_value = color[3]
                break
        mat.diffuse_color = color
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'
    obj.data.materials.append(mat)
