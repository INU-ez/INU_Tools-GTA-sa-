# INU_tools.ops.light_ops — Prelight, Vertex Color, Itera, Lightmap,
# Vertex Paint, Scatter Light, Color Attribute operators.
#
# Phase 3 batch 6 (2026-04-26): 38 operators + 1 helper moved from
# __init__.py. Big-picture: anything that touches vertex colors, light
# baking, lightmap textures, itera materials, or vertex-paint mode
# tooling lives here. Material save/restore lives here too because
# they're paired with itera workflow.

import os
import bpy
from bpy.props import (
    StringProperty, BoolProperty, FloatProperty, EnumProperty,
)
from mathutils import Vector

from .. import T
from ..tools import compat
from ..tools.model_utils import find_selected_models
from ..tools.prelight import (
    average_colors_on_coplanar_faces,
    create_prelight_scene_lights, remove_prelight_scene_lights,
    bake_vertex_colors_from_lights, bake_vertex_colors_simple,
    apply_brightness_offset, analyze_vertex_colors,
    smooth_vertex_colors, adjust_vertex_colors_contrast,
    adjust_vertex_colors_brightness, adjust_vertex_colors_gamma,
    setup_prelight_preview,
    add_scatter_layer, remove_scatter_layer, clear_scatter_layers,
    remove_fill_color_by_index, get_selected_faces_color,
    fill_selected_faces_with_backup, restore_filled_faces,
    scatter_light_from_selected,
)


class GTATOOLS_OT_detect_models(bpy.types.Operator):
    """Определить модели DFF, LOD, COL среди выделенных"""
    bl_idname = "gtatools.detect_models"
    bl_label = "INU: Detect Models"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        models = find_selected_models()

        found = []
        if models['DFF']:
            found.append(f"DFF: {models['DFF'].name}")
        if models['LOD']:
            found.append(f"LOD: {models['LOD'].name}")
        if models['COL']:
            found.append(f"COL: {models['COL'].name}")

        if found:
            self.report({'INFO'}, f"{T('Найдено:')} {', '.join(found)}")
        else:
            self.report({'WARNING'}, T("Среди выделенных не найдено DFF/LOD/COL моделей"))

        return {'FINISHED'}


class GTATOOLS_OT_average_colors(bpy.types.Operator):
    """Усреднить vertex colors для компланарных граней"""
    bl_idname = "gtatools.average_colors"
    bl_label = "INU: Average Colors"
    bl_options = {'REGISTER', 'UNDO'}

    normal_threshold: FloatProperty(
        name="Normal Threshold",
        default=0.01,
        min=0.001,
        max=0.5
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        if not mesh_objects:
            self.report({'ERROR'}, "Select mesh object(s)!")
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        count = 0
        for obj in mesh_objects:
            success = average_colors_on_coplanar_faces(obj, self.normal_threshold)
            if success:
                count += 1

        if count:
            self.report({'INFO'}, f"Colors averaged: {count} objects")
        else:
            self.report({'ERROR'}, "Failed to average colors!")
            return {'CANCELLED'}

        return {'FINISHED'}


class GTATOOLS_OT_lightmap_generate(bpy.types.Operator):
    """Сгенерировать код lightmap для выделенного объекта"""
    bl_idname = "gtatools.lightmap_generate"
    bl_label = "INU: Generate Lightmap Code"

    def execute(self, context):
        scene = context.scene
        obj = context.active_object

        if not obj:
            self.report({'WARNING'}, "No object selected")
            scene.inu_settings.gtatools_lightmap_result = "Error: no object selected"
            return {'CANCELLED'}

        textures = self.get_textures_from_object(obj)

        if not textures:
            self.report({'WARNING'}, "No textures found")
            scene.inu_settings.gtatools_lightmap_result = "Error: no textures found"
            return {'CANCELLED'}

        lightmap_path = scene.inu_settings.gtatools_lightmap_path if scene.inu_settings.gtatools_lightmap_path else "lightmaps/lightmap.png"
        model_id = scene.inu_settings.gtatools_model_id if scene.inu_settings.gtatools_model_id else "0"

        code = self.generate_code(textures, lightmap_path, model_id)
        scene.inu_settings.gtatools_lightmap_result = code

        self.report({'INFO'}, f"Found {len(textures)} textures")
        return {'FINISHED'}

    def get_textures_from_object(self, obj):
        textures = []
        if not obj.data or not hasattr(obj.data, 'materials'):
            return textures

        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue

            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    tex_name = os.path.splitext(node.image.name)[0]
                    if tex_name not in textures:
                        textures.append(tex_name)

        return textures

    def generate_code(self, textures, lightmap_path, model_id):
        lines = []
        lines.append("    {")
        lines.append("        textures = {")
        for tex in textures:
            lines.append(f'            "{tex}",')
        lines.append("        },")
        lines.append(f'        lightmap = "{lightmap_path}",')
        lines.append(f"        models = {{{model_id}}}")
        lines.append("    },")
        return '\n'.join(lines)


class GTATOOLS_OT_lightmap_copy(bpy.types.Operator):
    """Копировать результат в буфер обмена"""
    bl_idname = "gtatools.lightmap_copy"
    bl_label = "INU: Copy to Clipboard"

    def execute(self, context):
        scene = context.scene
        if scene.inu_settings.gtatools_lightmap_result:
            context.window_manager.clipboard = scene.inu_settings.gtatools_lightmap_result
            self.report({'INFO'}, "Copied to clipboard")
        return {'FINISHED'}


class GTATOOLS_OT_lightmap_clear(bpy.types.Operator):
    """Очистить сгенерированный код"""
    bl_idname = "gtatools.lightmap_clear"
    bl_label = "INU: Clear"

    def execute(self, context):
        context.scene.inu_settings.gtatools_lightmap_result = ""
        self.report({'INFO'}, T("Код очищен"))
        return {'FINISHED'}


class GTATOOLS_OT_create_prelight_lights(bpy.types.Operator):
    """Создать 8 источников света для запекания prelight вокруг объекта"""
    bl_idname = "gtatools.create_prelight_lights"
    bl_label = "INU: Create Prelight Lights"
    bl_options = {'REGISTER', 'UNDO'}

    distance: FloatProperty(
        name="Distance",
        description=T("Расстояние ламп от центра"),
        default=100.0,
        min=1.0,
        max=1000.0
    )

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'ERROR'}, "Select an object!")
            return {'CANCELLED'}

        # Get object center (bounding box center in world space)
        bbox_center = sum((Vector(b) for b in obj.bound_box), Vector()) / 8
        world_center = obj.matrix_world @ bbox_center

        lights = create_prelight_scene_lights(world_center, self.distance)
        self.report({'INFO'}, f"Created {len(lights)} lights around {obj.name}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_prelight_lights(bpy.types.Operator):
    """Удалить все источники света prelight"""
    bl_idname = "gtatools.remove_prelight_lights"
    bl_label = "INU: Remove Prelight Lights"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if remove_prelight_scene_lights():
            self.report({'INFO'}, "Prelight lights removed")
        else:
            self.report({'WARNING'}, "No prelight lights found")
        return {'FINISHED'}


class GTATOOLS_OT_bake_vertex_colors(bpy.types.Operator):
    """Запечь освещение от Point источников в vertex colors"""
    bl_idname = "gtatools.bake_vertex_colors"
    bl_label = "INU: Bake Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    use_shadows: BoolProperty(
        name="Use Shadows",
        description=T("Рассчитать тени (медленнее, но точнее)"),
        default=True
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        baked = 0
        for obj in mesh_objects:
            success, message = bake_vertex_colors_from_lights(obj, self.use_shadows)
            if success:
                if compat.vcol_active(obj.data):
                    prop_name = f"v_offset_{compat.vcol_active(obj.data).name}"
                    obj[prop_name] = 0.0
                baked += 1

        if baked:
            self.report({'INFO'}, f"Baked from lights: {baked} objects")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, T("Нет vertex colors"))
            return {'CANCELLED'}


class GTATOOLS_OT_bake_vertex_colors_simple(bpy.types.Operator):
    """Быстрое запекание vertex colors от Point источников (без теней)"""
    bl_idname = "gtatools.bake_vertex_colors_simple"
    bl_label = "INU: Bake Vertex Colors (Fast)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        # Get settings from panel. "Запечь" — быстрый режим без теней;
        # для теней нужно жать кнопку «С тенями» рядом.
        ambient = scene.inu_settings.gtatools_bake_ambient
        intensity = scene.inu_settings.gtatools_bake_intensity
        gamma = scene.inu_settings.gtatools_bake_gamma
        use_shadows = False

        baked = 0
        for obj in mesh_objects:
            success, message = bake_vertex_colors_simple(obj, ambient, intensity, gamma, use_shadows)
            if success:
                if compat.vcol_active(obj.data):
                    prop_name = f"v_offset_{compat.vcol_active(obj.data).name}"
                    obj[prop_name] = 0.0
                baked += 1

        if baked:
            _act = compat.vcol_active(mesh_objects[0].data)
            attr_name = _act.name if _act else "?"
            self.report({'INFO'}, f"Baked to '{attr_name}' from {baked} objects")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, T("Нет vertex colors"))
            return {'CANCELLED'}


class GTATOOLS_OT_reset_bake_settings(bpy.types.Operator):
    """Сбросить настройки запекания по умолчанию"""
    bl_idname = "gtatools.reset_bake_settings"
    bl_label = "INU: Reset to Default"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.inu_settings.gtatools_bake_ambient = 0.10
        scene.inu_settings.gtatools_bake_intensity = 0.05
        scene.inu_settings.gtatools_bake_gamma = 0.50
        self.report({'INFO'}, T("Настройки сброшены по умолчанию"))
        return {'FINISHED'}


class GTATOOLS_OT_reset_scatter_settings(bpy.types.Operator):
    """Сбросить настройки Scatter Light по умолчанию"""
    bl_idname = "gtatools.reset_scatter_settings"
    bl_label = "INU: Reset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.inu_settings.gtatools_scatter_intensity = 1.0
        scene.inu_settings.gtatools_scatter_falloff = 1.5
        scene.inu_settings.gtatools_scatter_iterations = 3
        scene.inu_settings.gtatools_scatter_radius = 0.0
        self.report({'INFO'}, "Scatter settings reset")
        return {'FINISHED'}


class GTATOOLS_OT_analyze_vertex_colors(bpy.types.Operator):
    """Анализировать vertex colors выделенного объекта"""
    bl_idname = "gtatools.analyze_vertex_colors"
    bl_label = "INU: Analyze Colors"

    def execute(self, context):
        obj = context.active_object
        result = analyze_vertex_colors(obj)

        if result is None:
            self.report({'WARNING'}, "No vertex colors found!")
            return {'CANCELLED'}

        # Store result in scene for display
        scene = context.scene
        scene.inu_settings.gtatools_vc_analysis = (
            f"Layer: {result['layer_name']}\n"
            f"Vertices: {result['count']}\n"
            f"Min: {result['min_brightness']:.3f}\n"
            f"Max: {result['max_brightness']:.3f}\n"
            f"Avg: {result['avg_brightness']:.3f}"
        )

        self.report({'INFO'}, f"Avg brightness: {result['avg_brightness']:.3f}")
        return {'FINISHED'}


class GTATOOLS_OT_apply_v_offset(bpy.types.Operator):
    """Применить смещение яркости (V) к vertex colors"""
    bl_idname = "gtatools.apply_v_offset"
    bl_label = "INU: Apply V Offset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        v_offset = context.scene.inu_settings.gtatools_v_offset
        count = 0
        for obj in mesh_objects:
            success, _ = apply_brightness_offset(obj, v_offset)
            if success:
                count += 1
        self.report({'INFO'}, f"V Offset: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_smooth(bpy.types.Operator):
    """Сгладить vertex colors между соседними вершинами"""
    bl_idname = "gtatools.vc_smooth"
    bl_label = "INU: Smooth Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        iterations = context.scene.inu_settings.gtatools_vc_smooth_iterations
        factor = context.scene.inu_settings.gtatools_vc_smooth_factor
        count = 0
        for obj in mesh_objects:
            success, _ = smooth_vertex_colors(obj, iterations, factor)
            if success:
                count += 1
        self.report({'INFO'}, f"Smooth: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_contrast(bpy.types.Operator):
    """Применить контраст к vertex colors"""
    bl_idname = "gtatools.vc_contrast"
    bl_label = "INU: Apply Contrast"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        contrast = context.scene.inu_settings.gtatools_vc_contrast
        count = 0
        for obj in mesh_objects:
            success, _ = adjust_vertex_colors_contrast(obj, contrast)
            if success:
                count += 1
        self.report({'INFO'}, f"Contrast: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_brightness(bpy.types.Operator):
    """Применить яркость к vertex colors"""
    bl_idname = "gtatools.vc_brightness"
    bl_label = "INU: Apply Brightness"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        brightness = context.scene.inu_settings.gtatools_vc_brightness
        count = 0
        for obj in mesh_objects:
            success, _ = adjust_vertex_colors_brightness(obj, brightness)
            if success:
                count += 1
        self.report({'INFO'}, f"Brightness: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_gamma(bpy.types.Operator):
    """Применить гамма-коррекцию к vertex colors"""
    bl_idname = "gtatools.vc_gamma"
    bl_label = "INU: Apply Gamma"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            mesh_objects = [context.active_object] if context.active_object and context.active_object.type == 'MESH' else []
        gamma = context.scene.inu_settings.gtatools_vc_gamma

        count = 0
        for obj in mesh_objects:
            success, _ = adjust_vertex_colors_gamma(obj, gamma)
            if success:
                count += 1
        self.report({'INFO'}, f"Gamma: {count} objects")
        return {'FINISHED'} if count else {'CANCELLED'}


class GTATOOLS_OT_vc_smooth_between(bpy.types.Operator):
    """Сгладить vertex colors на стыках между выделенными объектами"""
    bl_idname = "gtatools.vc_smooth_between"
    bl_label = "INU: Smooth Between Objects"
    bl_options = {'REGISTER', 'UNDO'}

    tolerance: FloatProperty(
        name="Tolerance",
        description=T("Максимальное расстояние между вершинами для сопоставления"),
        default=0.001,
        min=0.0001,
        max=1.0
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if len(mesh_objects) < 2:
            self.report({'ERROR'}, T("Выделите минимум 2 меш объекта"))
            return {'CANCELLED'}

        # Collect all boundary vertex data: (world_pos, obj, loop_indices, color_attr)
        from mathutils import kdtree

        all_points = []  # [(world_co, obj_index, vert_index)]
        obj_data = []    # [(obj, color_attr, {vert_idx: [loop_indices]})]

        for oi, obj in enumerate(mesh_objects):
            mesh = obj.data
            color_attr = compat.vcol_active(mesh)
            if color_attr is None:
                continue

            # Build vert -> loop indices map
            vert_loops = {}
            for poly in mesh.polygons:
                for vi, li in zip(poly.vertices, poly.loop_indices):
                    vert_loops.setdefault(vi, []).append(li)

            obj_data.append((obj, color_attr, vert_loops))

            mat_w = obj.matrix_world
            for vi, vert in enumerate(mesh.vertices):
                world_co = mat_w @ vert.co
                all_points.append((world_co, len(obj_data) - 1, vi))

        if not obj_data:
            self.report({'WARNING'}, T("Нет vertex colors"))
            return {'CANCELLED'}

        # Build KD-tree from all vertices
        kd = kdtree.KDTree(len(all_points))
        for i, (co, _, _) in enumerate(all_points):
            kd.insert(co, i)
        kd.balance()

        # Find matching vertices and average their colors
        processed = set()
        smoothed_count = 0
        tol = self.tolerance

        for i, (co, oi, vi) in enumerate(all_points):
            if i in processed:
                continue

            # Find all vertices at this position
            matches = kd.find_range(co, tol)
            if len(matches) < 2:
                continue

            # Check if matches span multiple objects
            match_indices = [idx for _, idx, _ in matches]
            obj_indices = set(all_points[idx][1] for idx in match_indices)
            if len(obj_indices) < 2:
                continue

            # Collect all colors from matching vertices
            colors = []
            match_data = []  # [(obj_data_index, loop_indices)]
            for idx in match_indices:
                _, m_oi, m_vi = all_points[idx]
                obj, color_attr, vert_loops = obj_data[m_oi]
                loops = vert_loops.get(m_vi, [])
                for li in loops:
                    c = color_attr.data[li].color
                    colors.append((c[0], c[1], c[2], c[3]))
                match_data.append((m_oi, loops))
                processed.add(idx)

            if not colors:
                continue

            # Average
            avg = [sum(c[ch] for c in colors) / len(colors) for ch in range(4)]

            # Apply averaged color back
            for m_oi, loops in match_data:
                _, color_attr, _ = obj_data[m_oi]
                for li in loops:
                    color_attr.data[li].color = avg

            smoothed_count += 1

        # Update meshes
        for obj, _, _ in obj_data:
            obj.data.update()

        self.report({'INFO'}, f"{T('Сглажено стыков:')} {smoothed_count}")
        return {'FINISHED'}


class GTATOOLS_OT_load_lightmap(bpy.types.Operator):
    """Загрузить Lightmap из папки с .blend файлом (текстуры с приставкой LP_)"""
    bl_idname = "gtatools.load_lightmap"
    bl_label = "INU: Load Lightmap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        # Get path to .blend file
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({'ERROR'}, T("Сохраните .blend файл сначала!"))
            return {'CANCELLED'}

        blend_dir = os.path.dirname(blend_path)

        # Ищем текстуры с приставкой LP_
        lightmap_files = []
        supported_ext = ('.png', '.jpg', '.jpeg', '.tga', '.bmp', '.tif', '.tiff')

        for filename in os.listdir(blend_dir):
            if filename.upper().startswith('LP_') and filename.lower().endswith(supported_ext):
                lightmap_files.append(filename)

        if not lightmap_files:
            self.report({'ERROR'}, f"{T('Текстуры с приставкой LP_ не найдены в папке:')} {blend_dir}")
            return {'CANCELLED'}

        # Берём первую найденную текстуру
        lightmap_filename = lightmap_files[0]
        lightmap_path = os.path.join(blend_dir, lightmap_filename)

        # Загружаем текстуру
        lightmap_image = bpy.data.images.load(lightmap_path, check_existing=True)

        # Применяем лайтмап ко всем материалам объекта
        applied_count = 0
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Находим Principled BSDF
            principled = None
            for node in nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled = node
                    break

            if not principled:
                continue

            # Проверяем есть ли уже лайтмап нода
            existing_lm = nodes.get("Lightmap_Texture")
            if existing_lm:
                # Обновляем текстуру
                existing_lm.image = lightmap_image
                applied_count += 1
                continue

            # Находим что подключено к Base Color
            base_color_input = principled.inputs['Base Color']
            original_link = None
            original_node = None
            prelight_mix = nodes.get("Prelight_Mix")

            if base_color_input.links:
                original_link = base_color_input.links[0]
                original_node = original_link.from_node
                original_socket = original_link.from_socket

                # Если подключен Prelight_Mix - ищем оригинальную текстуру в его входе A
                if original_node and original_node.name == "Prelight_Mix":
                    prelight_mix = original_node
                    prelight_a_input = prelight_mix.inputs.get('A')
                    if prelight_a_input and prelight_a_input.is_linked:
                        original_node = prelight_a_input.links[0].from_node
                        original_socket = prelight_a_input.links[0].from_socket
                    else:
                        original_node = None
                        original_socket = None

            # Создаём ноду UV Map для UV2
            uv_node = nodes.new('ShaderNodeUVMap')
            uv_node.name = "Lightmap_UV"
            uv_node.label = "UV2"
            # Ищем второй UV слой
            if len(obj.data.uv_layers) >= 2:
                uv_node.uv_map = obj.data.uv_layers[1].name
            elif len(obj.data.uv_layers) == 1:
                # Если только один UV - используем его
                uv_node.uv_map = obj.data.uv_layers[0].name

            # Создаём ноду текстуры для лайтмапа
            lm_tex = nodes.new('ShaderNodeTexImage')
            lm_tex.name = "Lightmap_Texture"
            lm_tex.label = "Lightmap"
            lm_tex.image = lightmap_image

            # Создаём ноду Mix (Multiply) через compat — на 3.4+ это
            # ShaderNodeMix(RGBA), на 2.80-3.3 — ShaderNodeMixRGB.
            mix_node = nodes.new(compat.MIX_NODE_TYPE)
            compat.setup_mix_rgba_node(mix_node, blend='MULTIPLY')
            mix_node.inputs[compat.MIX_INPUT_FACTOR].default_value = 1.0
            _mix_in1, _mix_in2, _mix_out = (
                compat.MIX_INPUT_A, compat.MIX_INPUT_B, compat.MIX_OUTPUT_RESULT)
            mix_node.name = "Lightmap_Mix"
            mix_node.label = "Lightmap Mix"

            # Позиционируем ноды
            if original_node:
                uv_node.location = (original_node.location.x - 200, original_node.location.y - 300)
                lm_tex.location = (original_node.location.x, original_node.location.y - 300)
                mix_node.location = (original_node.location.x + 300, original_node.location.y - 150)
            else:
                uv_node.location = (principled.location.x - 700, principled.location.y - 200)
                lm_tex.location = (principled.location.x - 500, principled.location.y - 200)
                mix_node.location = (principled.location.x - 200, principled.location.y)

            # Подключаем UV2 к текстуре лайтмапа
            links.new(uv_node.outputs['UV'], lm_tex.inputs['Vector'])

            # Подключаем ноды
            if original_node:
                links.new(original_socket, mix_node.inputs[_mix_in1])
            else:
                mix_node.inputs[_mix_in1].default_value = (1, 1, 1, 1)

            links.new(lm_tex.outputs['Color'], mix_node.inputs[_mix_in2])

            if prelight_mix:
                links.new(mix_node.outputs[_mix_out], prelight_mix.inputs['A'])
            else:
                links.new(mix_node.outputs[_mix_out], base_color_input)

            applied_count += 1

        if applied_count > 0:
            self.report({'INFO'}, f"Lightmap '{lightmap_filename}' applied to {applied_count} material(s)")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, T("Не удалось применить лайтмап - нет подходящих материалов"))
            return {'CANCELLED'}


class GTATOOLS_OT_remove_lightmap(bpy.types.Operator):
    """Удалить Lightmap из материалов объекта"""
    bl_idname = "gtatools.remove_lightmap"
    bl_label = "INU: Remove Lightmap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        removed_count = 0
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Find lightmap nodes
            lm_tex = nodes.get("Lightmap_Texture")
            lm_mix = nodes.get("Lightmap_Mix")
            lm_uv = nodes.get("Lightmap_UV")

            if not lm_mix:
                continue

            # Находим Principled BSDF
            principled = None
            for node in nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled = node
                    break

            if principled:
                # Восстанавливаем оригинальное подключение
                base_color_input = principled.inputs['Base Color']
                prelight_mix = nodes.get("Prelight_Mix")

                # Находим что было подключено к входу (оригинальная текстура)
                _in1 = 'A' if 'A' in lm_mix.inputs else 'Color1'
                original_socket = None
                if lm_mix.inputs[_in1].links:
                    original_link = lm_mix.inputs[_in1].links[0]
                    original_socket = original_link.from_socket

                # Удаляем связи с Mix нодой
                for link in list(links):
                    if link.to_node == lm_mix or link.from_node == lm_mix:
                        links.remove(link)

                # Восстанавливаем оригинальное подключение
                if original_socket:
                    if prelight_mix:
                        # Если есть Prelight_Mix - подключаем к его входу A
                        links.new(original_socket, prelight_mix.inputs['A'])
                    else:
                        # Иначе напрямую к Base Color
                        links.new(original_socket, base_color_input)

            # Удаляем ноды лайтмапа
            if lm_tex:
                nodes.remove(lm_tex)
            if lm_mix:
                nodes.remove(lm_mix)
            if lm_uv:
                nodes.remove(lm_uv)

            removed_count += 1

        if removed_count > 0:
            self.report({'INFO'}, f"Lightmap удалён из {removed_count} материал(ов)")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Lightmap не найден в материалах")
            return {'CANCELLED'}


class GTATOOLS_OT_create_day_night(bpy.types.Operator):
    """Создать Day и Night color attributes"""
    bl_idname = "gtatools.create_day_night"
    bl_label = "INU: Create Day/Night"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "Select mesh object(s)!")
            return {'CANCELLED'}

        total_created = 0
        for obj in mesh_objects:
            mesh = obj.data

            # Create Day attribute if not exists
            if compat.vcol_get(mesh, "Day") is None:
                attr = compat.vcol_new(mesh, "Day")
                for i in range(len(attr.data)):
                    attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
                total_created += 1

            # Create Night attribute if not exists
            if compat.vcol_get(mesh, "Night") is None:
                attr = compat.vcol_new(mesh, "Night")
                for i in range(len(attr.data)):
                    attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
                total_created += 1

            # Set Day as active
            day_attr = compat.vcol_get(mesh, "Day")
            if day_attr is not None:
                compat.vcol_active(mesh, day_attr)

        self.report({'INFO'}, f"Day/Night: {len(mesh_objects)} objects, {total_created} attributes created")
        return {'FINISHED'}


class GTATOOLS_OT_copy_color_attr(bpy.types.Operator):
    """Копировать vertex colors из одного атрибута в другой (Day ↔ Night)"""
    bl_idname = "gtatools.copy_color_attr"
    bl_label = "INU: Copy Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    source: StringProperty(name="Source", default="Day")
    target: StringProperty(name="Target", default="Night")

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                mesh_objects = [obj]
        if not mesh_objects:
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        copied = 0
        for obj in mesh_objects:
            mesh = obj.data
            src_attr = compat.vcol_get(mesh, self.source)
            if not src_attr:
                continue

            tgt_attr = compat.vcol_get(mesh, self.target)
            if not tgt_attr:
                tgt_attr = compat.vcol_new(mesh, self.target)

            # Copy all colors
            n = min(len(src_attr.data), len(tgt_attr.data))
            for i in range(n):
                c = src_attr.data[i].color
                tgt_attr.data[i].color = (c[0], c[1], c[2], c[3])
            copied += 1

        self.report({'INFO'}, f"{self.source} → {self.target}: {copied} {T('объектов')}")
        return {'FINISHED'}


class GTATOOLS_OT_prelight_preview(bpy.types.Operator):
    """Переключить превью prelight - показать vertex colors с текстурами"""
    bl_idname = "gtatools.prelight_preview"
    bl_label = "INU: Toggle Prelight Preview"
    bl_options = {'REGISTER', 'UNDO'}

    enable: BoolProperty(
        name="Enable",
        description=T("Включить или выключить превью prelight"),
        default=True
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            # Fallback to active object
            obj = context.active_object
            if obj and obj.type == 'MESH':
                mesh_objects = [obj]

        count = 0
        for obj in mesh_objects:
            success, message = setup_prelight_preview(obj, self.enable)
            if success:
                count += 1

        if count:
            state = "enabled" if self.enable else "disabled"
            self.report({'INFO'}, f"Prelight preview {state} on {count} materials")
            return {'FINISHED'}

        # Single object error
        obj = context.active_object
        success, message = setup_prelight_preview(obj, self.enable)
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_fix_itera_collection(bpy.types.Operator):
    """Исправить коллекцию освещения Itera Tools — сделать локальной и привязать к сцене"""
    bl_idname = "gtatools.fix_itera_collection"
    bl_label = "INU: Fix Itera Light Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import bpy
        # Find all Itera collections (including .001, .002, etc.)
        itera_cols = [c for c in bpy.data.collections if c.name.startswith("Template Scene - Vertex Lights")]
        if not itera_cols:
            self.report({'WARNING'}, T("Коллекция 'Template Scene - Vertex Lights' не найдена"))
            return {'CANCELLED'}

        fixed = 0
        for col in itera_cols:
            if col.library:
                try:
                    col.make_local()
                    for obj in col.objects:
                        obj.make_local()
                except Exception:
                    bpy.ops.object.make_local(type='ALL')
                    col = bpy.data.collections.get(col.name)
                    if col is None:
                        continue

            if col.name not in context.scene.collection.children:
                context.scene.collection.children.link(col)
                fixed += 1

        self.report({'INFO'}, T("Коллекции Itera привязаны к сцене") + f": {fixed}")
        return {'FINISHED'}


def _find_itera_blend_path():
    """Find the Itera Tools 3 blend file from Blender asset libraries."""
    for lib in bpy.context.preferences.filepaths.asset_libraries:
        if "itera" in lib.name.lower() or "itera" in lib.path.lower():
            blend_path = os.path.join(lib.path, "Vertex Light 3.0.89.blend")
            if os.path.isfile(blend_path):
                return blend_path
            # Try to find any blend file with "Vertex Light" in name
            for f in os.listdir(lib.path):
                if f.startswith("Vertex Light") and f.endswith(".blend"):
                    return os.path.join(lib.path, f)
    return None


class GTATOOLS_OT_apply_itera_material(bpy.types.Operator):
    """Применить Itera материал из библиотеки к выделенным объектам"""
    bl_idname = "gtatools.apply_itera_material"
    bl_label = "INU: Apply Itera Material"
    bl_options = {'REGISTER', 'UNDO'}

    preset: EnumProperty(
        name="Preset",
        items=[
            ('VERTEX_LIT_LINEAR', "Vertex Lit Linear UV",
             T("Линейное освещение вершин с UV текстурой")),
        ],
        default='VERTEX_LIT_LINEAR'
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        blend_path = _find_itera_blend_path()
        if not blend_path:
            self.report({'ERROR'}, T("Itera Tools 3 не найден в библиотеках ассетов"))
            return {'CANCELLED'}

        # Remember selection before append (append can change selection)
        saved_selected = [obj for obj in context.selected_objects]
        saved_active = context.active_object

        mat_names = {
            'VERTEX_LIT_LINEAR': "Vertex Lit Linear UV Texture",
        }
        target_name = mat_names[self.preset]

        # Check if already loaded
        itera_mat = bpy.data.materials.get(target_name)

        if itera_mat is None:
            # Append from blend file (more reliable than libraries.load for assets)
            try:
                bpy.ops.wm.append(
                    filepath=os.path.join(blend_path, "Material", target_name),
                    directory=os.path.join(blend_path, "Material") + os.sep,
                    filename=target_name,
                    link=False,
                    do_reuse_local_id=True,
                )
                itera_mat = bpy.data.materials.get(target_name)
            except Exception as e:
                self.report({'ERROR'}, f"{T('Ошибка загрузки:')} {e}")
                return {'CANCELLED'}

            # Restore selection after append
            bpy.ops.object.select_all(action='DESELECT')
            for obj in saved_selected:
                obj.select_set(True)
            if saved_active:
                context.view_layer.objects.active = saved_active

        if itera_mat is None:
            self.report({'ERROR'}, f"{T('Материал не найден:')} {target_name}")
            return {'CANCELLED'}

        # Apply to selected mesh objects
        applied = 0
        for obj in saved_selected:
            if obj.type != 'MESH':
                continue

            # Save original materials + face assignments before replacing
            import json
            if not obj.get("gtatools_saved_materials"):
                orig = {
                    "materials": [slot.material.name if slot.material else "" for slot in obj.material_slots],
                    "face_indices": [p.material_index for p in obj.data.polygons]
                }
                obj["gtatools_saved_materials"] = json.dumps(orig)

            # Clear existing slots and add Itera material
            obj.data.materials.clear()
            obj.data.materials.append(itera_mat)
            applied += 1

        self.report({'INFO'}, f"Itera '{self.preset}': {applied} {T('объектов')}")
        return {'FINISHED'}


class GTATOOLS_OT_apply_itera_quickstart(bpy.types.Operator):
    """Применить Quickstart Vertex Lightable Surface — модификатор + коллекция со светом"""
    bl_idname = "gtatools.apply_itera_quickstart"
    bl_label = "INU: Apply Itera Quickstart"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        blend_path = _find_itera_blend_path()
        if not blend_path:
            self.report({'ERROR'}, T("Itera Tools 3 не найден в библиотеках ассетов"))
            return {'CANCELLED'}

        ng_name = "Quickstart Vertex Lightable Surface"
        col_name = "Template Scene - Vertex Lights"

        # Remember selection before append (append can change selection)
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        # 1. Load node group if not already in blend
        node_group = bpy.data.node_groups.get(ng_name)
        if node_group is None:
            try:
                with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                    if ng_name in data_from.node_groups:
                        data_to.node_groups = [ng_name]
                node_group = bpy.data.node_groups.get(ng_name)
            except Exception as e:
                self.report({'ERROR'}, f"{T('Ошибка загрузки node group:')} {e}")
                return {'CANCELLED'}

        if node_group is None:
            self.report({'ERROR'}, f"{T('Node group не найден:')} {ng_name}")
            return {'CANCELLED'}

        # 2. Load light collection if not already present
        light_col = None
        for c in bpy.data.collections:
            if c.name.startswith(col_name):
                light_col = c
                break

        if light_col is None:
            try:
                with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                    if col_name in data_from.collections:
                        data_to.collections = [col_name]
                light_col = bpy.data.collections.get(col_name)
            except Exception:
                pass

        # 3. Link collection to scene if needed
        if light_col and light_col.name not in context.scene.collection.children:
            context.scene.collection.children.link(light_col)

        # 4. Add modifier only to MESH objects (not lights)
        applied = 0
        for obj in mesh_objects:
            # Check if modifier already exists
            has_mod = any(m.type == 'NODES' and m.node_group and
                         m.node_group.name == ng_name for m in obj.modifiers)
            if has_mod:
                continue

            mod = obj.modifiers.new(name=ng_name, type='NODES')
            mod.node_group = node_group

            # Set Light Collection input if available
            if light_col:
                for item in mod.node_group.interface.items_tree:
                    if hasattr(item, 'socket_type') and item.socket_type == 'NodeSocketCollection':
                        mod[item.identifier] = light_col
                        break

            applied += 1

        self.report({'INFO'}, f"Quickstart: {applied} {T('объектов')}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_itera_material(bpy.types.Operator):
    """Убрать Itera материал и восстановить оригинальные"""
    bl_idname = "gtatools.remove_itera_material"
    bl_label = "INU: Remove Itera Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        import json
        restored = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Remove Quickstart modifier
            quickstart_mods = [m for m in obj.modifiers
                               if m.type == 'NODES' and m.node_group
                               and "Quickstart" in m.node_group.name]
            for mod in quickstart_mods:
                obj.modifiers.remove(mod)

            # Restore saved materials + face assignments
            saved = obj.get("gtatools_saved_materials")
            if saved:
                data = json.loads(saved)
                names = data["materials"] if isinstance(data, dict) else data
                face_indices = data.get("face_indices", []) if isinstance(data, dict) else []

                obj.data.materials.clear()
                for name in names:
                    mat = bpy.data.materials.get(name)
                    obj.data.materials.append(mat)

                # Restore face material assignments
                if face_indices:
                    for i, idx in enumerate(face_indices):
                        if i < len(obj.data.polygons):
                            obj.data.polygons[i].material_index = idx

                del obj["gtatools_saved_materials"]
                restored += 1
            else:
                # No saved data — just clear Itera materials
                itera_names = {"Vertex Lit Linear UV Texture"}
                to_remove = []
                for i, slot in enumerate(obj.material_slots):
                    if slot.material and slot.material.name in itera_names:
                        to_remove.append(i)
                for i in reversed(to_remove):
                    obj.active_material_index = i
                    bpy.ops.object.material_slot_remove()

            if quickstart_mods:
                restored += 1

        self.report({'INFO'}, f"{T('Восстановлено:')} {restored} {T('объектов')}")
        return {'FINISHED'}


class GTATOOLS_OT_save_materials(bpy.types.Operator):
    """Сохранить материалы объекта в буфер"""
    bl_idname = "gtatools.save_materials"
    bl_label = "INU: Save Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        import json
        mesh = obj.data

        # Сохраняем имена материалов в слотах
        mat_names = []
        for slot in obj.material_slots:
            mat_names.append(slot.material.name if slot.material else "")

        # Сохраняем material_index каждого полигона
        face_indices = [p.material_index for p in mesh.polygons]

        obj["gtatools_saved_materials"] = json.dumps({
            "materials": mat_names,
            "face_indices": face_indices
        })
        self.report({'INFO'}, T("Материалы сохранены") + f" ({len(mat_names)})")
        return {'FINISHED'}


class GTATOOLS_OT_restore_materials(bpy.types.Operator):
    """Восстановить сохранённые материалы на объект"""
    bl_idname = "gtatools.restore_materials"
    bl_label = "INU: Restore Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        raw = obj.get("gtatools_saved_materials")
        if not raw:
            self.report({'ERROR'}, T("Нет сохранённых материалов!"))
            return {'CANCELLED'}

        import json
        data = json.loads(raw)

        # Поддержка старого формата (список имён) и нового (dict)
        if isinstance(data, list):
            mat_names = data
            face_indices = None
        else:
            mat_names = data["materials"]
            face_indices = data.get("face_indices")

        mesh = obj.data

        # Очищаем все слоты
        mesh.materials.clear()

        # Создаём слоты и назначаем материалы
        not_found = []
        for mat_name in mat_names:
            if mat_name == "":
                mesh.materials.append(None)
            elif mat_name in bpy.data.materials:
                mesh.materials.append(bpy.data.materials[mat_name])
            else:
                not_found.append(mat_name)
                mesh.materials.append(None)

        # Восстанавливаем назначения полигонов
        if face_indices and len(face_indices) == len(mesh.polygons):
            for poly, idx in zip(mesh.polygons, face_indices):
                poly.material_index = idx

        if not_found:
            self.report({'WARNING'}, T("Материал не найден:") + " " + ", ".join(not_found))
        else:
            self.report({'INFO'}, T("Материалы восстановлены") + f" ({len(mat_names)})")
        return {'FINISHED'}


class GTATOOLS_OT_eyedropper_color(bpy.types.Operator):
    """Кликните на полигон чтобы взять его цвет"""
    bl_idname = "gtatools.eyedropper_color"
    bl_label = "INU: Pick Color from Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            # Показываем курсор пипетки
            context.window.cursor_set('EYEDROPPER')

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # Делаем raycast под курсором
            result = self.pick_color_at_cursor(context, event)
            if result:
                context.window.cursor_set('DEFAULT')
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "No mesh under cursor")
                return {'RUNNING_MODAL'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            # Отмена
            context.window.cursor_set('DEFAULT')
            self.report({'INFO'}, "Color pick cancelled")
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type != 'VIEW_3D':
            self.report({'ERROR'}, "Use in 3D View!")
            return {'CANCELLED'}

        context.window.cursor_set('EYEDROPPER')
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Click on polygon to pick color (ESC to cancel)")
        return {'RUNNING_MODAL'}

    def pick_color_at_cursor(self, context, event):
        """Raycast и получение цвета полигона под курсором"""
        from bpy_extras import view3d_utils

        region = context.region
        rv3d = context.region_data

        # Координаты мыши в 3D
        coord = event.mouse_region_x, event.mouse_region_y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

        # Raycast по всем объектам
        depsgraph = context.evaluated_depsgraph_get()
        result, location, normal, face_index, obj, matrix = context.scene.ray_cast(
            depsgraph, ray_origin, view_vector
        )

        if not result or obj is None or obj.type != 'MESH':
            return False

        mesh = obj.data
        if not compat.vcol_list(mesh):
            self.report({'ERROR'}, "Object has no vertex colors!")
            return False

        color_attr = compat.vcol_active(mesh)
        if color_attr is None:
            self.report({'ERROR'}, "No active color layer!")
            return False

        if face_index < 0 or face_index >= len(mesh.polygons):
            return False

        # Считываем цвета вершин этой грани
        colors = []
        poly = mesh.polygons[face_index]
        for loop_idx in poly.loop_indices:
            c = color_attr.data[loop_idx].color
            colors.append((c[0], c[1], c[2]))

        # Усредняем цвет
        if colors:
            avg_r = sum(c[0] for c in colors) / len(colors)
            avg_g = sum(c[1] for c in colors) / len(colors)
            avg_b = sum(c[2] for c in colors) / len(colors)

            context.scene.inu_settings.gtatools_fill_color = (avg_r, avg_g, avg_b)
            self.report({'INFO'}, f"Color picked: RGB({int(avg_r*255)}, {int(avg_g*255)}, {int(avg_b*255)})")
            return True

        return False


class GTATOOLS_OT_fill_faces(bpy.types.Operator):
    """Залить выделенные грани цветом"""
    bl_idname = "gtatools.fill_faces"
    bl_label = "INU: Fill Selected Faces"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        scene = context.scene
        color = scene.inu_settings.gtatools_fill_color

        success, message = fill_selected_faces_with_backup(obj, color)

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_restore_fill(bpy.types.Operator):
    """Восстановить цвета, изменённые заливкой"""
    bl_idname = "gtatools.restore_fill"
    bl_label = "INU: Restore Fill"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        success, message = restore_filled_faces(obj)

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_remove_fill_color(bpy.types.Operator):
    """Удалить цвет из списка и восстановить оригинальные цвета"""
    bl_idname = "gtatools.remove_fill_color"
    bl_label = "INU: Remove Fill Color"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        # Switch to Object Mode for data writing
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        success, message = remove_fill_color_by_index(obj, self.index)

        # Возвращаемся в исходный режим
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_select_fill_color(bpy.types.Operator):
    """Выделить полигоны с этим цветом"""
    bl_idname = "gtatools.select_fill_color"
    bl_label = "INU: Select Faces by Color"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        if not (0 <= self.index < len(obj.gtatools_fill_colors)):
            return {'CANCELLED'}

        target_color = obj.gtatools_fill_colors[self.index].color
        tolerance = 0.01

        # Switch to Object Mode for data reading
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        if not compat.vcol_active(mesh):
            self.report({'ERROR'}, T("Нет vertex colors!"))
            if original_mode == 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}

        color_attr = compat.vcol_active(mesh)

        # Find polygons with this color
        selected_count = 0
        for poly in mesh.polygons:
            has_color = False
            for loop_idx in poly.loop_indices:
                c = color_attr.data[loop_idx].color
                if (abs(c[0] - target_color[0]) < tolerance and
                    abs(c[1] - target_color[1]) < tolerance and
                    abs(c[2] - target_color[2]) < tolerance):
                    has_color = True
                    break

            if has_color:
                poly.select = True
                selected_count += 1
            else:
                poly.select = False

        # Switch to Edit Mode to show selection
        bpy.ops.object.mode_set(mode='EDIT')

        self.report({'INFO'}, f"{T('Выделено')} {selected_count} {T('полигонов')}")
        return {'FINISHED'}


class GTATOOLS_OT_delete_fill_color_level(bpy.types.Operator):
    """Удалить scatter уровень (пересчитать цвета)"""
    bl_idname = "gtatools.delete_fill_color_level"
    bl_label = "INU: Delete Scatter Level"
    bl_options = {'REGISTER', 'UNDO'}

    color_index: bpy.props.IntProperty()
    level: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        if not (0 <= self.color_index < len(obj.gtatools_fill_colors)):
            return {'CANCELLED'}

        color = obj.gtatools_fill_colors[self.color_index].color

        # Switch to Object Mode
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        success, message = remove_scatter_layer(obj, color, self.level)

        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_clear_fill_color_levels(bpy.types.Operator):
    """Очистить все scatter уровни цвета"""
    bl_idname = "gtatools.clear_fill_color_levels"
    bl_label = "INU: Clear Scatter Levels"
    bl_options = {'REGISTER', 'UNDO'}

    color_index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        if not (0 <= self.color_index < len(obj.gtatools_fill_colors)):
            return {'CANCELLED'}

        color = obj.gtatools_fill_colors[self.color_index].color

        # Switch to Object Mode
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        success, message = clear_scatter_layers(obj, color)

        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_scatter_light(bpy.types.Operator):
    """Рассеять свет от выделенных граней к соседним"""
    bl_idname = "gtatools.scatter_light"
    bl_label = "INU: Scatter Light"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        scene = context.scene

        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш!"))
            return {'CANCELLED'}

        # Switch to Object Mode for data reading
        original_mode = obj.mode
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Определяем цвет выделенных полигонов
        selected_color = get_selected_faces_color(obj)

        # Сохраняем цвета ДО scatter для вычисления дельты
        pre_scatter_colors = {}
        mesh = obj.data
        if compat.vcol_active(mesh):
            color_attr = compat.vcol_active(mesh)
            for loop_idx in range(len(color_attr.data)):
                c = color_attr.data[loop_idx].color
                pre_scatter_colors[loop_idx] = (c[0], c[1], c[2], c[3])

        intensity = scene.inu_settings.gtatools_scatter_intensity
        falloff = scene.inu_settings.gtatools_scatter_falloff
        iterations = scene.inu_settings.gtatools_scatter_iterations
        radius = scene.inu_settings.gtatools_scatter_radius

        success, message, affected_loops = scatter_light_from_selected(obj, intensity, falloff, iterations, radius)

        level_info = ""

        # Вычисляем дельты ДО переключения режима (пока данные mesh актуальны)
        if success and selected_color and affected_loops:
            deltas = {}
            color_attr = compat.vcol_active(mesh)
            for loop_idx in affected_loops:
                if loop_idx in pre_scatter_colors and loop_idx < len(color_attr.data):
                    old = pre_scatter_colors[loop_idx]
                    new = color_attr.data[loop_idx].color
                    delta = (new[0] - old[0], new[1] - old[1], new[2] - old[2], 0.0)
                    # Сохраняем только если дельта не нулевая
                    if abs(delta[0]) > 0.001 or abs(delta[1]) > 0.001 or abs(delta[2]) > 0.001:
                        deltas[loop_idx] = delta

            # Сохраняем дельты как scatter слой
            if deltas:
                scatter_level = add_scatter_layer(obj, selected_color, deltas)
                if scatter_level > 0:
                    level_info = f" | Level {scatter_level}"

        # Возвращаемся в исходный режим
        if original_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if success:
            self.report({'INFO'}, f"{message}{level_info}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class GTATOOLS_OT_toggle_face_select(bpy.types.Operator):
    """Переключить режим выделения граней в Vertex Paint"""
    bl_idname = "gtatools.toggle_face_select"
    bl_label = "INU: Toggle Face Selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        # Toggle face selection masking in paint mode
        obj.data.use_paint_mask = not obj.data.use_paint_mask

        if obj.data.use_paint_mask:
            self.report({'INFO'}, "Face selection ON - Click faces to select")
        else:
            self.report({'INFO'}, "Face selection OFF")

        return {'FINISHED'}


class GTATOOLS_OT_switch_to_edit(bpy.types.Operator):
    """Переключить в Edit Mode для выделения граней"""
    bl_idname = "gtatools.switch_to_edit"
    bl_label = "INU: Edit Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
        return {'FINISHED'}


class GTATOOLS_OT_switch_to_vpaint(bpy.types.Operator):
    """Переключить в Vertex Paint Mode"""
    bl_idname = "gtatools.switch_to_vpaint"
    bl_label = "INU: Vertex Paint Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.active_object:
            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        return {'FINISHED'}


class GTATOOLS_OT_select_color_attribute(bpy.types.Operator):
    """Выбрать color attribute и обновить превью prelight"""
    bl_idname = "gtatools.select_color_attribute"
    bl_label = "INU: Select Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    attribute_name: StringProperty(name="Attribute Name")

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                mesh_objects = [obj]

        if not mesh_objects:
            self.report({'ERROR'}, "Select mesh object(s)!")
            return {'CANCELLED'}

        switched = 0
        for obj in mesh_objects:
            mesh = obj.data
            color_attr = compat.vcol_get(mesh, self.attribute_name)
            if color_attr is not None:
                compat.vcol_active(mesh, color_attr)
                self.update_prelight_preview(obj, self.attribute_name)
                switched += 1

        self.report({'INFO'}, f"Active: {self.attribute_name} ({switched} objects)")
        return {'FINISHED'}

    def update_prelight_preview(self, obj, color_name):
        """Update vertex color node in materials to use new color attribute"""
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue

            nodes = mat.node_tree.nodes
            vc_node = nodes.get("Prelight_VertexColor")

            if vc_node:
                if hasattr(vc_node, 'layer_name'):
                    vc_node.layer_name = color_name
                elif hasattr(vc_node, 'attribute_name'):
                    vc_node.attribute_name = color_name


class GTATOOLS_OT_add_color_attribute(bpy.types.Operator):
    """Добавить новый color attribute"""
    bl_idname = "gtatools.add_color_attribute"
    bl_label = "INU: Add Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        mesh = obj.data

        # Generate unique name
        base_name = "Color"
        name = base_name
        counter = 1
        while compat.vcol_get(mesh, name) is not None:
            name = f"{base_name}.{counter:03d}"
            counter += 1

        color_attr = compat.vcol_new(mesh, name)
        compat.vcol_active(mesh, color_attr)

        self.report({'INFO'}, f"Created: {name}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_color_attribute(bpy.types.Operator):
    """Удалить активный color attribute"""
    bl_idname = "gtatools.remove_color_attribute"
    bl_label = "INU: Remove Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        mesh = obj.data
        if not compat.vcol_list(mesh):
            self.report({'ERROR'}, "No color attributes!")
            return {'CANCELLED'}

        active = compat.vcol_active(mesh)
        if active:
            name = active.name
            compat.vcol_remove(mesh, active)
            self.report({'INFO'}, f"Removed: {name}")
        else:
            self.report({'ERROR'}, "No active color attribute!")
            return {'CANCELLED'}

        return {'FINISHED'}


class GTATOOLS_OT_create_color_attr(bpy.types.Operator):
    """Создать color attribute"""
    bl_idname = "gtatools.create_color_attr"
    bl_label = "INU: Create Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    attr_name: StringProperty(default="Day")

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object!")
            return {'CANCELLED'}

        mesh = obj.data

        if compat.vcol_get(mesh, self.attr_name) is not None:
            self.report({'INFO'}, f"{self.attr_name} already exists")
            return {'CANCELLED'}

        # Create attribute
        attr = compat.vcol_new(mesh, self.attr_name)
        # Fill with white
        for i in range(len(attr.data)):
            attr.data[i].color = (1.0, 1.0, 1.0, 1.0)

        # Set as active
        compat.vcol_active(mesh, attr)

        self.report({'INFO'}, f"Created: {self.attr_name}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_color_attr(bpy.types.Operator):
    """Удалить color attribute по имени на всех выделенных объектах"""
    bl_idname = "gtatools.remove_color_attr"
    bl_label = "INU: Remove Color Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    attr_name: StringProperty(default="")

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                mesh_objects = [obj]

        if not mesh_objects:
            self.report({'ERROR'}, "Select mesh object(s)!")
            return {'CANCELLED'}

        removed = 0
        for obj in mesh_objects:
            mesh = obj.data
            attr = compat.vcol_get(mesh, self.attr_name)
            if attr is not None:
                compat.vcol_remove(mesh, attr)
                removed += 1

        if removed:
            self.report({'INFO'}, f"Removed '{self.attr_name}' from {removed} objects")
        else:
            self.report({'ERROR'}, f"{self.attr_name} not found")
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_detect_models,
    GTATOOLS_OT_average_colors,
    GTATOOLS_OT_lightmap_generate,
    GTATOOLS_OT_lightmap_copy,
    GTATOOLS_OT_lightmap_clear,
    GTATOOLS_OT_create_prelight_lights,
    GTATOOLS_OT_remove_prelight_lights,
    GTATOOLS_OT_bake_vertex_colors,
    GTATOOLS_OT_bake_vertex_colors_simple,
    GTATOOLS_OT_reset_bake_settings,
    GTATOOLS_OT_reset_scatter_settings,
    GTATOOLS_OT_analyze_vertex_colors,
    GTATOOLS_OT_apply_v_offset,
    GTATOOLS_OT_vc_smooth,
    GTATOOLS_OT_vc_contrast,
    GTATOOLS_OT_vc_brightness,
    GTATOOLS_OT_vc_gamma,
    GTATOOLS_OT_vc_smooth_between,
    GTATOOLS_OT_load_lightmap,
    GTATOOLS_OT_remove_lightmap,
    GTATOOLS_OT_create_day_night,
    GTATOOLS_OT_copy_color_attr,
    GTATOOLS_OT_prelight_preview,
    GTATOOLS_OT_fix_itera_collection,
    GTATOOLS_OT_apply_itera_material,
    GTATOOLS_OT_apply_itera_quickstart,
    GTATOOLS_OT_remove_itera_material,
    GTATOOLS_OT_save_materials,
    GTATOOLS_OT_restore_materials,
    GTATOOLS_OT_eyedropper_color,
    GTATOOLS_OT_fill_faces,
    GTATOOLS_OT_restore_fill,
    GTATOOLS_OT_remove_fill_color,
    GTATOOLS_OT_select_fill_color,
    GTATOOLS_OT_delete_fill_color_level,
    GTATOOLS_OT_clear_fill_color_levels,
    GTATOOLS_OT_scatter_light,
    GTATOOLS_OT_toggle_face_select,
    GTATOOLS_OT_switch_to_edit,
    GTATOOLS_OT_switch_to_vpaint,
    GTATOOLS_OT_select_color_attribute,
    GTATOOLS_OT_add_color_attribute,
    GTATOOLS_OT_remove_color_attribute,
    GTATOOLS_OT_create_color_attr,
    GTATOOLS_OT_remove_color_attr,
)
