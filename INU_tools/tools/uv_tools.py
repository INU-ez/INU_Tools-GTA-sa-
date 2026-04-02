# INU_tools.tools.uv_tools — UV Editor tools (grid, randomizer, snap)

import bpy
import bmesh
import random
import gpu
import math
import os
from gpu_extras.batch import batch_for_shader
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
from .. import T


# Global variable for draw handler
_uv_grid_draw_handler = None
_uv_grid_visible = False


def draw_uv_grid_callback():
    """Draw grid overlay in UV Editor"""
    global _uv_grid_visible

    if not _uv_grid_visible:
        return

    context = bpy.context
    scene = context.scene

    cols = scene.gtatools_uv_grid_cols
    rows = scene.gtatools_uv_grid_rows

    if cols < 1 or rows < 1:
        return

    # Get current space and region
    area = context.area
    if not area or area.type != 'IMAGE_EDITOR':
        return

    region = None
    for r in area.regions:
        if r.type == 'WINDOW':
            region = r
            break

    if not region:
        return

    # Get view transformation
    space = area.spaces.active
    if not space:
        return

    # Calculate view to region transformation
    view2d = region.view2d

    # Build grid lines
    vertices = []
    cell_width = 1.0 / cols
    cell_height = 1.0 / rows

    # Vertical lines
    for i in range(cols + 1):
        x = i * cell_width
        # Convert UV to region coordinates
        start = view2d.view_to_region(x, 0, clip=False)
        end = view2d.view_to_region(x, 1, clip=False)
        vertices.append(start)
        vertices.append(end)

    # Horizontal lines
    for i in range(rows + 1):
        y = i * cell_height
        start = view2d.view_to_region(0, y, clip=False)
        end = view2d.view_to_region(1, y, clip=False)
        vertices.append(start)
        vertices.append(end)

    if not vertices:
        return

    # Draw with GPU
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": vertices})

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2.0)

    shader.bind()
    shader.uniform_float("color", (1.0, 0.5, 0.0, 0.8))  # Orange color
    batch.draw(shader)

    gpu.state.blend_set('NONE')
    gpu.state.line_width_set(1.0)


class GTATOOLS_OT_toggle_uv_editor(bpy.types.Operator):
    """Toggle UV Editor panel (split/join area)"""
    bl_idname = "gtatools.toggle_uv_editor"
    bl_label = T("Открыть/Закрыть UV Editor")
    bl_options = {'REGISTER'}

    def execute(self, context):
        screen = context.screen

        # Ищем уже открытый IMAGE_EDITOR
        uv_area = None
        for area in screen.areas:
            if area.type == 'IMAGE_EDITOR':
                uv_area = area
                break

        if uv_area is not None:
            # Закрываем UV Editor — объединяем с соседней областью
            # Находим 3D Viewport рядом для объединения
            view3d_area = None
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    view3d_area = area
                    break

            if view3d_area:
                # Закрываем UV area через area_close
                with context.temp_override(area=uv_area):
                    bpy.ops.screen.area_close()
                pass
            return {'FINISHED'}
        else:
            # Открываем UV Editor — разделяем текущий 3D Viewport
            target_area = None
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    target_area = area
                    break

            if target_area is None:
                self.report({'ERROR'}, T("Не найден 3D Viewport"))
                return {'CANCELLED'}

            # Разделяем область вертикально (UV слева)
            with context.temp_override(area=target_area):
                bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)

            # Находим новую область (самая маленькая VIEW_3D) и меняем тип на IMAGE_EDITOR
            # После split появляется новая область VIEW_3D
            all_view3d = [a for a in screen.areas if a.type == 'VIEW_3D']
            if len(all_view3d) >= 2:
                # Новая область — та что с меньшей шириной (левая часть, factor=0.4)
                new_area = min(all_view3d, key=lambda a: a.width)
                new_area.type = 'IMAGE_EDITOR'
                # Переключаем на UV Editor mode
                for space in new_area.spaces:
                    if space.type == 'IMAGE_EDITOR':
                        space.mode = 'UV'
                        break

            pass
            return {'FINISHED'}


class GTATOOLS_OT_toggle_uv_grid(bpy.types.Operator):
    """Показать/скрыть сетку на UV"""
    bl_idname = "gtatools.toggle_uv_grid"
    bl_label = "Toggle UV Grid"

    def execute(self, context):
        global _uv_grid_draw_handler, _uv_grid_visible

        _uv_grid_visible = not _uv_grid_visible

        if _uv_grid_visible:
            if _uv_grid_draw_handler is None:
                _uv_grid_draw_handler = bpy.types.SpaceImageEditor.draw_handler_add(
                    draw_uv_grid_callback, (), 'WINDOW', 'POST_PIXEL'
                )
            self.report({'INFO'}, T("Сетка UV включена"))
        else:
            self.report({'INFO'}, T("Сетка UV выключена"))

        # Force redraw
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.tag_redraw()

        return {'FINISHED'}


def calculate_uv_offset(face_width, face_height, cell_width, cell_height, alignment):
    """Calculate UV offset based on alignment"""
    if alignment == 'CENTER':
        offset_u = (cell_width - face_width) / 2
        offset_v = (cell_height - face_height) / 2
    elif alignment == 'TOP_LEFT':
        offset_u = 0
        offset_v = cell_height - face_height
    elif alignment == 'TOP_RIGHT':
        offset_u = cell_width - face_width
        offset_v = cell_height - face_height
    elif alignment == 'BOTTOM_LEFT':
        offset_u = 0
        offset_v = 0
    elif alignment == 'BOTTOM_RIGHT':
        offset_u = cell_width - face_width
        offset_v = 0
    elif alignment == 'TOP_CENTER':
        offset_u = (cell_width - face_width) / 2
        offset_v = cell_height - face_height
    elif alignment == 'BOTTOM_CENTER':
        offset_u = (cell_width - face_width) / 2
        offset_v = 0
    elif alignment == 'LEFT_CENTER':
        offset_u = 0
        offset_v = (cell_height - face_height) / 2
    elif alignment == 'RIGHT_CENTER':
        offset_u = cell_width - face_width
        offset_v = (cell_height - face_height) / 2
    else:
        offset_u = (cell_width - face_width) / 2
        offset_v = (cell_height - face_height) / 2
    return offset_u, offset_v


def find_connected_face_groups(faces, uv_layer):
    """Find groups of faces that overlap in UV space or are connected by mesh edges"""
    if not faces:
        return []

    face_set = set(faces)
    visited = set()
    groups = []

    def get_face_uv_bounds(face):
        us = [loop[uv_layer].uv.x for loop in face.loops]
        vs = [loop[uv_layer].uv.y for loop in face.loops]
        return min(us), max(us), min(vs), max(vs)

    def bounds_overlap(b1, b2, margin=0.01):
        """Check if two bounding boxes overlap (with small margin)"""
        min_u1, max_u1, min_v1, max_v1 = b1
        min_u2, max_u2, min_v2, max_v2 = b2
        return not (max_u1 + margin < min_u2 or max_u2 + margin < min_u1 or
                    max_v1 + margin < min_v2 or max_v2 + margin < min_v1)

    # Pre-calculate UV bounds for all faces
    face_bounds = {face: get_face_uv_bounds(face) for face in faces}

    for face in faces:
        if face in visited:
            continue

        # BFS to find all connected faces (by mesh edges OR UV overlap)
        group = []
        queue = [face]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue

            visited.add(current)
            group.append(current)
            current_bounds = face_bounds[current]

            # Method 1: Find adjacent faces through shared mesh edges
            for edge in current.edges:
                for linked_face in edge.link_faces:
                    if linked_face not in visited and linked_face in face_set:
                        queue.append(linked_face)

            # Method 2: Find faces with overlapping UV bounds
            for other_face in faces:
                if other_face not in visited and other_face in face_set:
                    if bounds_overlap(current_bounds, face_bounds[other_face]):
                        queue.append(other_face)

        if group:
            groups.append(group)

    return groups


def get_island_uv_bounds(island, uv_layer):
    """Get UV bounding box for an island of faces"""
    all_us = []
    all_vs = []

    for face in island:
        for loop in face.loops:
            all_us.append(loop[uv_layer].uv.x)
            all_vs.append(loop[uv_layer].uv.y)

    return min(all_us), max(all_us), min(all_vs), max(all_vs)


def move_island_uv(island, uv_layer, offset_u, offset_v):
    """Move all UV vertices of an island by offset"""
    # Track moved UV vertices to avoid moving shared vertices twice
    moved = set()

    for face in island:
        for loop in face.loops:
            uv = loop[uv_layer].uv
            uv_key = (id(loop), round(uv.x, 6), round(uv.y, 6))
            if uv_key not in moved:
                uv.x += offset_u
                uv.y += offset_v
                moved.add(uv_key)


class GTATOOLS_OT_randomize_uv_grid(bpy.types.Operator):
    """Рандомно распределить UV выделенных полигонов по сетке (для окон, вариаций)"""
    bl_idname = "gtatools.randomize_uv_grid"
    bl_label = "Randomize UV Grid"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        import bmesh
        import random

        obj = context.active_object
        scene = context.scene

        # Get grid settings
        cols = scene.gtatools_uv_grid_cols
        rows = scene.gtatools_uv_grid_rows
        alignment = scene.gtatools_uv_grid_align
        link_islands = scene.gtatools_uv_link_islands

        if cols < 1 or rows < 1:
            self.report({'ERROR'}, T("Укажите количество колонок и рядов!"))
            return {'CANCELLED'}

        # Get bmesh
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()

        # Get selected faces
        selected_faces = [f for f in bm.faces if f.select]

        if not selected_faces:
            self.report({'ERROR'}, T("Выделите полигоны!"))
            return {'CANCELLED'}

        # Cell size
        cell_width = 1.0 / cols
        cell_height = 1.0 / rows

        randomized_count = 0

        if link_islands:
            # Group faces by UV islands and move each island together
            islands = find_connected_face_groups(selected_faces, uv_layer)

            for island in islands:
                # Get island UV bounds
                min_u, max_u, min_v, max_v = get_island_uv_bounds(island, uv_layer)

                island_width = max_u - min_u
                island_height = max_v - min_v

                # Random cell
                random_col = random.randint(0, cols - 1)
                random_row = random.randint(0, rows - 1)

                # Target cell position
                target_u = random_col * cell_width
                target_v = random_row * cell_height

                # Calculate alignment offset
                align_offset_u, align_offset_v = calculate_uv_offset(
                    island_width, island_height, cell_width, cell_height, alignment
                )

                offset_u = target_u + align_offset_u - min_u
                offset_v = target_v + align_offset_v - min_v

                # Move entire island
                move_island_uv(island, uv_layer, offset_u, offset_v)
                randomized_count += 1

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"{T('Рандомизировано:')} {randomized_count} {T('групп')}")
        else:
            # Original behavior - each face moves independently
            for face in selected_faces:
                us = [loop[uv_layer].uv.x for loop in face.loops]
                vs = [loop[uv_layer].uv.y for loop in face.loops]

                min_u, max_u = min(us), max(us)
                min_v, max_v = min(vs), max(vs)

                face_width = max_u - min_u
                face_height = max_v - min_v

                random_col = random.randint(0, cols - 1)
                random_row = random.randint(0, rows - 1)

                target_u = random_col * cell_width
                target_v = random_row * cell_height

                align_offset_u, align_offset_v = calculate_uv_offset(
                    face_width, face_height, cell_width, cell_height, alignment
                )

                offset_u = target_u + align_offset_u - min_u
                offset_v = target_v + align_offset_v - min_v

                for loop in face.loops:
                    loop[uv_layer].uv.x += offset_u
                    loop[uv_layer].uv.y += offset_v

                randomized_count += 1

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"{T('Рандомизировано:')} {randomized_count} {T('полигонов')}")

        return {'FINISHED'}


class GTATOOLS_OT_snap_uv_to_grid(bpy.types.Operator):
    """Привязать UV выделенных полигонов к ближайшей ячейке сетки"""
    bl_idname = "gtatools.snap_uv_to_grid"
    bl_label = "Snap UV to Grid"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        import bmesh

        obj = context.active_object
        scene = context.scene

        cols = scene.gtatools_uv_grid_cols
        rows = scene.gtatools_uv_grid_rows
        alignment = scene.gtatools_uv_grid_align
        link_islands = scene.gtatools_uv_link_islands

        if cols < 1 or rows < 1:
            self.report({'ERROR'}, T("Укажите количество колонок и рядов!"))
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()

        selected_faces = [f for f in bm.faces if f.select]

        if not selected_faces:
            self.report({'ERROR'}, T("Выделите полигоны!"))
            return {'CANCELLED'}

        cell_width = 1.0 / cols
        cell_height = 1.0 / rows

        snapped_count = 0

        if link_islands:
            # Group faces by UV islands and snap each island together
            islands = find_connected_face_groups(selected_faces, uv_layer)

            for island in islands:
                # Get island UV bounds
                min_u, max_u, min_v, max_v = get_island_uv_bounds(island, uv_layer)

                island_width = max_u - min_u
                island_height = max_v - min_v

                # Find center of island UV
                center_u = (min_u + max_u) / 2
                center_v = (min_v + max_v) / 2

                # Find nearest cell
                nearest_col = int(center_u / cell_width)
                nearest_row = int(center_v / cell_height)

                # Clamp to valid range
                nearest_col = max(0, min(cols - 1, nearest_col))
                nearest_row = max(0, min(rows - 1, nearest_row))

                # Target cell position
                target_u = nearest_col * cell_width
                target_v = nearest_row * cell_height

                # Calculate alignment offset
                align_offset_u, align_offset_v = calculate_uv_offset(
                    island_width, island_height, cell_width, cell_height, alignment
                )

                offset_u = target_u + align_offset_u - min_u
                offset_v = target_v + align_offset_v - min_v

                # Move entire island
                move_island_uv(island, uv_layer, offset_u, offset_v)
                snapped_count += 1

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"{T('Привязано:')} {snapped_count} {T('групп')}")
        else:
            # Original behavior - each face snaps independently
            for face in selected_faces:
                us = [loop[uv_layer].uv.x for loop in face.loops]
                vs = [loop[uv_layer].uv.y for loop in face.loops]

                min_u, max_u = min(us), max(us)
                min_v, max_v = min(vs), max(vs)

                face_width = max_u - min_u
                face_height = max_v - min_v

                center_u = (min_u + max_u) / 2
                center_v = (min_v + max_v) / 2

                nearest_col = int(center_u / cell_width)
                nearest_row = int(center_v / cell_height)

                nearest_col = max(0, min(cols - 1, nearest_col))
                nearest_row = max(0, min(rows - 1, nearest_row))

                target_u = nearest_col * cell_width
                target_v = nearest_row * cell_height

                align_offset_u, align_offset_v = calculate_uv_offset(
                    face_width, face_height, cell_width, cell_height, alignment
                )

                offset_u = target_u + align_offset_u - min_u
                offset_v = target_v + align_offset_v - min_v

                for loop in face.loops:
                    loop[uv_layer].uv.x += offset_u
                    loop[uv_layer].uv.y += offset_v

                snapped_count += 1

            bmesh.update_edit_mesh(obj.data)
            self.report({'INFO'}, f"{T('Привязано:')} {snapped_count} {T('полигонов')}")

        return {'FINISHED'}


class GTATOOLS_OT_set_uv_align(bpy.types.Operator):
    """Выбрать позицию привязки UV в ячейке"""
    bl_idname = "gtatools.set_uv_align"
    bl_label = "Set UV Align"
    bl_options = {'INTERNAL'}

    alignment: bpy.props.StringProperty()

    def execute(self, context):
        context.scene.gtatools_uv_grid_align = self.alignment
        return {'FINISHED'}


class GTATOOLS_PT_uv_tools_panel(bpy.types.Panel):
    """Панель UV инструментов GTA Tools"""
    bl_label = "GTA Tools"
    bl_idname = "GTATOOLS_PT_uv_tools_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # UV Grid Randomizer
        box = layout.box()
        box.label(text=T("Рандомизатор UV сетки"), icon='GRID')

        # Toggle grid visibility button
        global _uv_grid_visible
        icon = 'HIDE_OFF' if _uv_grid_visible else 'HIDE_ON'
        text = T("Скрыть сетку") if _uv_grid_visible else T("Показать сетку")
        box.operator("gtatools.toggle_uv_grid", text=text, icon=icon)

        # Cols/Rows + Alignment visual grid side by side
        current = scene.gtatools_uv_grid_align
        grid = [
            ['TOP_LEFT', 'TOP_CENTER', 'TOP_RIGHT'],
            ['LEFT_CENTER', 'CENTER', 'RIGHT_CENTER'],
            ['BOTTOM_LEFT', 'BOTTOM_CENTER', 'BOTTOM_RIGHT'],
        ]
        split = box.split(factor=0.35)
        # Left: 3x3 grid
        left = split.column(align=True)
        for grid_row in grid:
            row = left.row(align=True)
            for pos in grid_row:
                ic = 'RADIOBUT_ON' if current == pos else 'RADIOBUT_OFF'
                op = row.operator("gtatools.set_uv_align", text="", icon=ic)
                op.alignment = pos
        # Right: Cols and Rows stacked
        right = split.column(align=True)
        right.prop(scene, "gtatools_uv_grid_cols", text=T("Колонки"))
        right.prop(scene, "gtatools_uv_grid_rows", text=T("Ряды"))

        # Link islands toggle
        row = box.row(align=True)
        row.prop(scene, "gtatools_uv_link_islands", text=T("Связать полигоны"), icon='LINKED', toggle=True)

        row = box.row(align=True)
        row.operator("gtatools.randomize_uv_grid", text=T("Рандом"), icon='MOD_UVPROJECT')
        row.operator("gtatools.snap_uv_to_grid", text=T("Привязать"), icon='SNAP_GRID')


# =============================================================================
# ADD MENU > GTA SA (Shift+A)
# =============================================================================

# Bundled DFF models available in Add > GTA SA menu
_GTASA_MODELS = {
    'ADMIRAL': ("Admiral", "admiral.dff"),
    'ARMY': ("Army", "army.dff"),
}


class GTATOOLS_OT_add_gtasa_model(bpy.types.Operator):
    """Add a GTA SA model to the scene"""
    bl_idname = "gtatools.add_gtasa_model"
    bl_label = "Add GTA SA Model"
    bl_options = {'REGISTER', 'UNDO'}

    model: EnumProperty(
        name="Model",
        items=[(k, v[0], f"Add {v[0]}") for k, v in _GTASA_MODELS.items()],
    )

    def execute(self, context):
        from ..ops.dff_import import import_dff as inu_import_dff

        info = _GTASA_MODELS.get(self.model)
        if not info:
            self.report({'ERROR'}, f"Unknown model: {self.model}")
            return {'CANCELLED'}

        models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "models")
        filepath = os.path.join(models_dir, info[1])

        if not os.path.isfile(filepath):
            self.report({'ERROR'}, f"Model file not found: {filepath}")
            return {'CANCELLED'}

        try:
            inu_import_dff(filepath=filepath, context=context)
            # Move imported objects to 3D cursor position
            cursor_loc = context.scene.cursor.location.copy()
            for obj in context.selected_objects:
                if not obj.parent:
                    obj.location += cursor_loc
            self.report({'INFO'}, f"Added {info[0]}")
        except Exception as e:
            self.report({'ERROR'}, f"Import error: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}


class VIEW3D_MT_gtasa_add_menu(bpy.types.Menu):
    """GTA SA models submenu in Add menu"""
    bl_idname = "VIEW3D_MT_gtasa_add_menu"
    bl_label = "GTA SA"

    def draw(self, context):
        layout = self.layout
        for key, (label, _filename) in _GTASA_MODELS.items():
            op = layout.operator("gtatools.add_gtasa_model", text=label, icon='MESH_MONKEY')
            op.model = key


def _gtasa_add_menu_draw(self, context):
    self.layout.menu("VIEW3D_MT_gtasa_add_menu", icon='AUTO')
