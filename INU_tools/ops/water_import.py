# INU_tools.ops.water_import — Import water.dat into Blender

import os
import bpy
import bmesh
from ..core.water import read_water


def _add_water_drivers(mat, map_node):
    """Add animated drivers to Mapping node Location, linked to scene speed properties.
    Uses time (seconds) for smooth, FPS-independent animation."""
    loc_input = map_node.inputs['Location']
    prop_names = ['gtatools_water_speed_x', 'gtatools_water_speed_y']
    for axis in (0, 1):
        loc_input.driver_remove('default_value', axis)
        drv_data = loc_input.driver_add('default_value', axis)
        drv = drv_data.driver
        drv.type = 'SCRIPTED'
        # Speed from scene property
        var_speed = drv.variables.new()
        var_speed.name = 'speed'
        var_speed.type = 'SINGLE_PROP'
        tar = var_speed.targets[0]
        tar.id_type = 'SCENE'
        tar.id = bpy.context.scene
        tar.data_path = prop_names[axis]
        # Time in seconds (frame_float / fps) for sub-frame smoothness
        var_time = drv.variables.new()
        var_time.name = 'time'
        var_time.type = 'SINGLE_PROP'
        tar2 = var_time.targets[0]
        tar2.id_type = 'SCENE'
        tar2.id = bpy.context.scene
        tar2.data_path = 'frame_float'
        var_fps = drv.variables.new()
        var_fps.name = 'fps'
        var_fps.type = 'SINGLE_PROP'
        tar3 = var_fps.targets[0]
        tar3.id_type = 'SCENE'
        tar3.id = bpy.context.scene
        tar3.data_path = 'render.fps'
        # Smooth time-based offset, looped
        drv.expression = '((time / fps) * speed) % 1000'


def _get_water_material():
    """Get or create water material with waterclear256 texture."""
    mat = bpy.data.materials.get("waterclear256")
    # Check if material exists but has no texture node — rebuild it
    if mat:
        has_tex = False
        has_driver = False
        if mat.use_nodes:
            for n in mat.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image:
                    has_tex = True
                if n.type == 'MAPPING':
                    # Check if driver exists on Location
                    if mat.node_tree.animation_data and mat.node_tree.animation_data.drivers:
                        has_driver = True
            # Add driver to existing Mapping node if missing
            if has_tex and not has_driver:
                for n in mat.node_tree.nodes:
                    if n.type == 'MAPPING':
                        _add_water_drivers(mat, n)
                        break
        if not has_tex:
            bpy.data.materials.remove(mat)
            mat = None

    if not mat:
        mat = bpy.data.materials.new("waterclear256")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = None
        for n in nodes:
            if n.type == 'BSDF_PRINCIPLED':
                bsdf = n
                break

        tex_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'data', 'fx_textures', 'waterclear256.png')
        img = bpy.data.images.get("waterclear256.png")
        if not img and os.path.isfile(tex_path):
            img = bpy.data.images.load(tex_path)

        if img and bsdf:
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.image = img
            tex_node.projection = 'BOX'
            tex_node.projection_blend = 1.0
            tex_node.location = (bsdf.location.x - 300, bsdf.location.y)
            tc_node = nodes.new('ShaderNodeTexCoord')
            tc_node.location = (bsdf.location.x - 800, bsdf.location.y)
            map_node = nodes.new('ShaderNodeMapping')
            map_node.location = (bsdf.location.x - 550, bsdf.location.y)
            map_node.inputs['Scale'].default_value = (0.1, 0.1, 0.1)
            links.new(tc_node.outputs['Object'], map_node.inputs['Vector'])
            links.new(map_node.outputs['Vector'], tex_node.inputs['Vector'])
            links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
            # Animate texture offset — drivers linked to scene speed properties
            _add_water_drivers(mat, map_node)
            bsdf.inputs['Alpha'].default_value = 0.6
            if hasattr(mat, 'blend_method'):
                mat.blend_method = 'BLEND'
        elif bsdf:
            bsdf.inputs['Base Color'].default_value = (0.0, 0.3, 0.8, 1.0)
            bsdf.inputs['Alpha'].default_value = 0.5
            if hasattr(mat, 'blend_method'):
                mat.blend_method = 'BLEND'

        mat.diffuse_color = (0.0, 0.3, 0.8, 0.5)

    return mat


def import_water(filepath: str, context=None):
    """Import water.dat as mesh objects in Blender.

    Creates one mesh per water flag type (0-3), grouped into a 'Water' collection.
    Water parameters stored as custom properties on vertices.
    """
    water = read_water(filepath)
    if not water.polygons:
        return []

    # Create or get Water collection
    col_name = "Water"
    water_col = bpy.data.collections.get(col_name)
    if not water_col:
        water_col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(water_col)

    flag_names = {
        0: "Water_Default_Invis",
        1: "Water_Default_Vis",
        2: "Water_Shallow_Invis",
        3: "Water_Shallow_Vis",
    }

    # Group polygons by flag
    by_flag = {}
    for poly in water.polygons:
        by_flag.setdefault(poly.flag, []).append(poly)

    created_objects = []

    for flag, polys in by_flag.items():
        obj_name = flag_names.get(flag, f"Water_Flag{flag}")

        mesh = bpy.data.meshes.new(obj_name)
        bm = bmesh.new()

        # Water parameter layers (custom float layers on loops)
        speed_x_layer = bm.verts.layers.float.new('water_speed_x')
        speed_y_layer = bm.verts.layers.float.new('water_speed_y')
        speed_z_layer = bm.verts.layers.float.new('water_speed_z')
        wave_layer = bm.verts.layers.float.new('water_wave_height')

        for poly in polys:
            verts = []
            for wv in poly.vertices:
                v = bm.verts.new((wv.x, wv.y, wv.z))
                v[speed_x_layer] = wv.speed_x
                v[speed_y_layer] = wv.speed_y
                v[speed_z_layer] = wv.speed_z
                v[wave_layer] = wv.wave_height
                verts.append(v)

            bm.verts.ensure_lookup_table()

            try:
                if len(verts) == 4:
                    # Quad: vertex order 1,2,4,3 (as in original water.dat)
                    bm.faces.new([verts[0], verts[1], verts[3], verts[2]])
                elif len(verts) == 3:
                    bm.faces.new([verts[0], verts[2], verts[1]])
            except ValueError:
                pass  # Duplicate face

        # Generate planar UV from XY coordinates (scale factor matches texture tiling)
        uv_layer = bm.loops.layers.uv.new('UVMap')
        uv_scale = 1.0 / 100.0  # 100 units = 1 UV tile
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = (loop.vert.co.x * uv_scale, loop.vert.co.y * uv_scale)

        bm.to_mesh(mesh)
        bm.free()
        mesh.update()

        obj = bpy.data.objects.new(obj_name, mesh)
        obj['water_flag'] = flag
        # Assign water material with texture
        water_mat = _get_water_material()
        mesh.materials.append(water_mat)
        water_col.objects.link(obj)
        created_objects.append(obj)

    return created_objects
