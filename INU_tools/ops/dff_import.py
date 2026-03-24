# INU_tools.ops.dff_import
# DFF (RenderWare Clump) → Blender mesh objects.
# Uses INU_tools.core.dff for binary format reading.

import os
import bpy
import bmesh
import mathutils

from ..core.dff import (
    read_dff_file, DffClump, DffGeometry, DffFrame, DffAtomic,
    RGBA, TexCoords, DffMaterial, DffTexture, UserData,
    GEOM_NORMALS, GEOM_PRELIT, GEOM_TEXTURED, GEOM_TEXTURED2,
    USERDATA_INT, USERDATA_FLOAT, USERDATA_STRING,
    Extension2dfx, Light2dfx, Particle2dfx, PedAttractor2dfx, SunGlare2dfx,
)


def _store_user_data(target, user_data: UserData):
    """Store UserData PLG into Blender custom properties.

    Saves as 'inu_user_data' — a list of dicts, each with
    'name', 'type' (int/float/str), and 'data' (list of values).
    """
    if not user_data or not user_data.sections:
        return

    type_names = {USERDATA_INT: 'int', USERDATA_FLOAT: 'float', USERDATA_STRING: 'str'}
    sections = []
    for sec in user_data.sections:
        sections.append({
            'name': sec.name,
            'type': type_names.get(sec.data_type, 'na'),
            'data': list(sec.data),
        })
    target['inu_user_data'] = sections


def _create_blender_material(dff_mat: DffMaterial, index: int) -> bpy.types.Material:
    """Создаём Blender материал из DFF материала."""
    tex_name = ""
    if dff_mat.texture and dff_mat.texture.name:
        tex_name = dff_mat.texture.name

    mat_name = tex_name if tex_name else f"Material_{index}"
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True

    tree = mat.node_tree
    nodes = tree.nodes

    # Получаем Principled BSDF
    bsdf = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break

    if bsdf is None:
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')

    # Устанавливаем цвет из DFF
    c = dff_mat.color
    bsdf.inputs['Base Color'].default_value = (c.r / 255.0, c.g / 255.0, c.b / 255.0, 1.0)

    # Specular = 0 для GTA моделей
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = 0.0

    # Альфа
    if c.a < 255:
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'
        bsdf.inputs['Alpha'].default_value = c.a / 255.0

    # Ambient в INU свойства
    mat.inu.ambient = dff_mat.surface.ambient if dff_mat.surface else 1.0

    # Material effects → INU свойства
    if dff_mat.env_map:
        mat.inu.export_env_map = True
        mat.inu.env_map_coef = dff_mat.env_map.coefficient
        mat.inu.env_map_fb_alpha = dff_mat.env_map.use_fb_alpha
        if dff_mat.env_map.texture:
            mat.inu.env_map_tex = dff_mat.env_map.texture.name

    if dff_mat.bump_map:
        mat.inu.export_bump_map = True
        if dff_mat.bump_map.bump_texture:
            mat.inu.bump_map_tex = dff_mat.bump_map.bump_texture.name

    if dff_mat.specular:
        mat.inu.export_specular = True
        mat.inu.specular_level = dff_mat.specular.level
        mat.inu.specular_texture = dff_mat.specular.name

    if dff_mat.reflection:
        mat.inu.export_reflection = True
        mat.inu.reflection_scale_x = dff_mat.reflection.scale_x
        mat.inu.reflection_scale_y = dff_mat.reflection.scale_y
        mat.inu.reflection_offset_x = dff_mat.reflection.offset_x
        mat.inu.reflection_offset_y = dff_mat.reflection.offset_y
        mat.inu.reflection_intensity = dff_mat.reflection.intensity

    if dff_mat.dual_texture:
        mat.inu.export_dual_tex = True
        mat.inu.dual_tex_src_blend = str(dff_mat.dual_texture.src_blend)
        mat.inu.dual_tex_dst_blend = str(dff_mat.dual_texture.dst_blend)
        if dff_mat.dual_texture.texture:
            mat.inu.dual_tex_texture = dff_mat.dual_texture.texture.name

    # User Data PLG
    if dff_mat.user_data:
        _store_user_data(mat, dff_mat.user_data)

    return mat


def _build_mesh(geom: DffGeometry, name: str, materials: list) -> bpy.types.Mesh:
    """Создаём Blender Mesh из DFF геометрии через bmesh."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    # Создаём материалы заранее
    for mi, dff_mat in enumerate(materials):
        bl_mat = _create_blender_material(dff_mat, mi)
        mesh.materials.append(bl_mat)

    # Вершины
    for v in geom.vertices:
        bm.verts.new((v[0], v[1], v[2]))

    bm.verts.ensure_lookup_table()
    bm.verts.index_update()

    # UV layers в bmesh
    uv_layers = []
    for i in range(len(geom.uv_layers)):
        uv_name = "UVMap" if i == 0 else f"UVMap.{i:03d}"
        uv_layers.append(bm.loops.layers.uv.new(uv_name))

    # Vertex colors layer
    vc_layer = None
    if geom.prelit_colors:
        vc_layer = bm.loops.layers.color.new("Day")

    # Night vertex colors layer
    nc_layer = None
    if geom.extra_colors and geom.extra_colors.colors:
        nc_layer = bm.loops.layers.color.new("Night")

    # Грани
    for tri in geom.triangles:
        try:
            face = bm.faces.new([
                bm.verts[tri.a],
                bm.verts[tri.b],
                bm.verts[tri.c],
            ])
            face.material_index = tri.material
            face.smooth = True

            # UV координаты через loops
            for loop in face.loops:
                vi = loop.vert.index
                for uv_idx, uv_bl_layer in enumerate(uv_layers):
                    uv_data = geom.uv_layers[uv_idx]
                    if vi < len(uv_data):
                        tc = uv_data[vi]
                        loop[uv_bl_layer].uv = (tc.u, 1.0 - tc.v)

                # Vertex colors
                if vc_layer and vi < len(geom.prelit_colors):
                    c = geom.prelit_colors[vi]
                    loop[vc_layer] = (c.r / 255.0, c.g / 255.0, c.b / 255.0, c.a / 255.0)

                # Night colors
                if nc_layer and vi < len(geom.extra_colors.colors):
                    c = geom.extra_colors.colors[vi]
                    loop[nc_layer] = (c.r / 255.0, c.g / 255.0, c.b / 255.0, c.a / 255.0)

        except Exception as e:
            print(f"[INU_tools] Face error: {e}")

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    # Store geometry user data on mesh
    if geom.user_data:
        _store_user_data(mesh, geom.user_data)

    return mesh


def _set_object_props(obj, geom: DffGeometry):
    """Записываем INU свойства объекта из DFF данных."""
    obj.inu.type = 'OBJ'
    obj.inu.export_normals = geom.export_normals
    obj.inu.export_binsplit = geom.write_bin_mesh

    if geom.pipeline:
        pipeline_hex = f"0x{geom.pipeline:08X}"
        known = {'0x53F20098', '0x53F2009A'}
        if pipeline_hex in known:
            obj.inu.pipeline = pipeline_hex
        else:
            obj.inu.pipeline = 'CUSTOM'
            obj.inu.custom_pipeline = pipeline_hex

    # UV maps
    obj.inu.uv_map1 = len(geom.uv_layers) >= 1
    obj.inu.uv_map2 = len(geom.uv_layers) >= 2

    # Color flags
    obj.inu.day_cols = bool(geom.prelit_colors)
    obj.inu.night_cols = bool(geom.extra_colors and geom.extra_colors.colors)


def _import_2dfx(ext_2dfx: Extension2dfx, collection, base_name: str) -> list:
    """Создаём Empty-объекты для каждого 2DFX эффекта.

    Каждый эффект хранится как Empty с типом '2DFX' и custom properties.
    """
    objects = []
    if not ext_2dfx or not ext_2dfx.entries:
        return objects

    for i, entry in enumerate(ext_2dfx.entries):
        if isinstance(entry, Light2dfx):
            name = f"{base_name}.2dfx_light.{i}"
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = 'PLAIN_AXES'
            obj.empty_display_size = 0.3
            obj.location = entry.loc

            obj.inu.type = '2DFX'
            obj.inu.effect_2dfx = 'LIGHT'

            obj.inu.color_2dfx = (entry.color.r / 255.0, entry.color.g / 255.0,
                                   entry.color.b / 255.0, entry.color.a / 255.0)
            obj['2dfx_corona_far_clip'] = entry.corona_far_clip
            obj['2dfx_pointlight_range'] = entry.pointlight_range
            obj['2dfx_corona_size'] = entry.corona_size
            obj['2dfx_shadow_size'] = entry.shadow_size
            obj['2dfx_corona_enable_reflection'] = entry.corona_enable_reflection
            obj['2dfx_shadow_color_multiplier'] = entry.shadow_color_multiplier
            obj['2dfx_flags1'] = entry.flags1
            # Set EnumProperty values for dropdowns
            try:
                obj.inu.corona_tex_2dfx = entry.corona_tex_name
            except TypeError:
                obj['2dfx_corona_tex'] = entry.corona_tex_name
            try:
                obj.inu.shadow_tex_2dfx = entry.shadow_tex_name
            except TypeError:
                obj['2dfx_shadow_tex'] = entry.shadow_tex_name
            try:
                obj.inu.show_mode_2dfx = str(entry.corona_show_mode)
            except TypeError:
                pass
            try:
                obj.inu.flare_type_2dfx = str(entry.corona_flare_type)
            except TypeError:
                pass
            obj['2dfx_shadow_z_distance'] = entry.shadow_z_distance
            obj['2dfx_flags2'] = entry.flags2
            if entry.look_direction is not None:
                obj['2dfx_look_direction'] = list(entry.look_direction)
            # Display precision
            for key in ('2dfx_corona_far_clip', '2dfx_pointlight_range',
                        '2dfx_corona_size', '2dfx_shadow_size'):
                ui = obj.id_properties_ui(key)
                ui.update(precision=1)

        elif isinstance(entry, Particle2dfx):
            name = f"{base_name}.2dfx_particle.{i}"
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = 'CIRCLE'
            obj.empty_display_size = 0.2
            obj.location = entry.loc

            obj.inu.type = '2DFX'
            obj.inu.effect_2dfx = 'PARTICLE'

            obj['2dfx_effect_name'] = entry.effect_name

        elif isinstance(entry, PedAttractor2dfx):
            name = f"{base_name}.2dfx_ped.{i}"
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = 'CUBE'
            obj.empty_display_size = 0.15
            obj.location = entry.loc

            obj.inu.type = '2DFX'
            obj.inu.effect_2dfx = 'PED_ATTRACTOR'

            obj['2dfx_attractor_type'] = entry.attractor_type
            obj['2dfx_rotation_matrix'] = list(entry.rotation_matrix)
            obj['2dfx_external_script'] = entry.external_script
            obj['2dfx_ped_probability'] = entry.ped_existing_probability

        elif isinstance(entry, SunGlare2dfx):
            name = f"{base_name}.2dfx_sunglare.{i}"
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = 'SPHERE'
            obj.empty_display_size = 0.1
            obj.location = entry.loc

            obj.inu.type = '2DFX'
            obj.inu.effect_2dfx = 'SUN_GLARE'

        else:
            continue

        collection.objects.link(obj)
        objects.append(obj)

        # Визуальный превью для Light2dfx
        if isinstance(entry, Light2dfx):
            try:
                from .fx_preview import create_light_preview
                create_light_preview(obj)
            except Exception as e:
                print(f"[INU_tools] 2DFX import preview error: {e}")

    return objects


def import_dff(filepath: str, context=None):
    """
    Импорт DFF файла в Blender.

    Args:
        filepath: Путь к .dff файлу.
        context: Blender context (опционально).
    """
    clump = read_dff_file(filepath)
    base_name = os.path.splitext(os.path.basename(filepath))[0]

    collection = bpy.context.collection
    imported_objects = []

    # Создаём объекты из Atomic связей (frame → geometry)
    for atomic in clump.atomics:
        gi = atomic.geometry_index
        fi = atomic.frame_index

        if gi >= len(clump.geometries):
            continue

        geom = clump.geometries[gi]
        frame = clump.frames[fi] if fi < len(clump.frames) else None

        # Имя объекта: из фрейма или из имени файла
        obj_name = frame.name if (frame and frame.name) else f"{base_name}_{gi}"

        # Создаём меш через bmesh
        mesh = _build_mesh(geom, obj_name, geom.materials)

        # Создаём объект
        obj = bpy.data.objects.new(obj_name, mesh)

        # Трансформация из фрейма
        if frame:
            rot = frame.rotation
            pos = frame.position
            matrix = mathutils.Matrix((
                (rot[0], rot[1], rot[2], pos[0]),
                (rot[3], rot[4], rot[5], pos[1]),
                (rot[6], rot[7], rot[8], pos[2]),
                (0, 0, 0, 1),
            ))
            obj.matrix_world = matrix

        # INU свойства
        _set_object_props(obj, geom)

        # Frame user data → object custom property
        if frame and frame.user_data:
            _store_user_data(obj, frame.user_data)

        collection.objects.link(obj)
        imported_objects.append(obj)

    # Если нет Atomic, но есть геометрии — создаём напрямую
    if not clump.atomics and clump.geometries:
        for gi, geom in enumerate(clump.geometries):
            obj_name = f"{base_name}_{gi}"
            mesh = _build_mesh(geom, obj_name, geom.materials)
            obj = bpy.data.objects.new(obj_name, mesh)
            _set_object_props(obj, geom)
            collection.objects.link(obj)
            imported_objects.append(obj)

    # Импорт 2DFX эффектов (собираем из всех геометрий) → коллекция "2DFX"
    fx_col = None
    for geom in clump.geometries:
        if geom.ext_2dfx and geom.ext_2dfx.entries:
            if fx_col is None:
                col_name = "2DFX"
                if col_name in bpy.data.collections:
                    fx_col = bpy.data.collections[col_name]
                else:
                    fx_col = bpy.data.collections.new(col_name)
                    bpy.context.scene.collection.children.link(fx_col)
            fx_objects = _import_2dfx(geom.ext_2dfx, fx_col, base_name)
            imported_objects.extend(fx_objects)

    # Выделяем импортированные объекты
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported_objects:
        obj.select_set(True)
    if imported_objects:
        bpy.context.view_layer.objects.active = imported_objects[0]

    return imported_objects
