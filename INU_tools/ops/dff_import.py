# INU_tools.ops.dff_import
# DFF (RenderWare Clump) → Blender mesh objects.
# Uses INU_tools.core.dff for binary format reading.

import os
import bpy
import bmesh
import mathutils

from ..core.dff import (
    read_dff_file, DffClump, DffGeometry, DffFrame, DffAtomic,
    RGBA, TexCoords, DffMaterial, DffTexture,
    GEOM_NORMALS, GEOM_PRELIT, GEOM_TEXTURED, GEOM_TEXTURED2,
)


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

    # Выделяем импортированные объекты
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported_objects:
        obj.select_set(True)
    if imported_objects:
        bpy.context.view_layer.objects.active = imported_objects[0]

    return imported_objects
