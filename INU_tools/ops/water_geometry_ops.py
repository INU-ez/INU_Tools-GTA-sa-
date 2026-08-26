# INU_tools.ops.water_geometry_ops — Add water plane + snap to grid + set params + stitch.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import bpy
import bmesh
from bpy.props import (
    FloatProperty, IntProperty, EnumProperty, BoolProperty,
)

from .. import T
from ..core.water import (
    WATER_BLOCK_SIZE, block_bounds, check_quad_fit,
)


class GTATOOLS_OT_add_water(bpy.types.Operator):
    """Создать водный полигон с параметрами GTA SA"""
    bl_idname = "gtatools.add_water"
    bl_label = "INU: Add Water Plane"
    bl_options = {'REGISTER', 'UNDO'}

    size: FloatProperty(name="Size", default=500.0, min=4.0,
                        description=T("Сторона квада в юнитах. 500 — максимум, влезающий в один блок воды GTA SA"))
    snap_to_block: BoolProperty(
        name=T("Привязать к блоку 500"), default=True,
        description=T("Разместить квад так, чтобы он лёг в игровую сетку блоков 500×500 (иначе вода рендерится без текстуры)"))
    subdivisions: IntProperty(name="Subdivisions", default=0, min=0, max=10)
    water_flag: EnumProperty(
        name="Water Type",
        items=[
            ('0', T("Обычная / Невидимая"), T("Глубокая вода, не отображается (подводные зоны)")),
            ('1', T("Обычная / Видимая"), T("Глубокая вода с волнами (океан, реки)")),
            ('2', T("Мелкая / Невидимая"), T("Мелкая вода, не отображается (анимация хождения по воде)")),
            ('3', T("Мелкая / Видимая"), T("Мелкая вода, отображается (лужи, пруды)")),
        ],
        default='1',
    )
    wave_height: FloatProperty(name="Wave Height", default=0.1, min=0.0, max=10.0)
    speed: FloatProperty(name="Speed", default=0.05, min=0.0, max=5.0)

    def execute(self, context):

        mesh = bpy.data.meshes.new("Water")
        bm = bmesh.new()

        # Create water parameter layers
        speed_x_layer = bm.verts.layers.float.new('water_speed_x')
        speed_y_layer = bm.verts.layers.float.new('water_speed_y')
        speed_z_layer = bm.verts.layers.float.new('water_speed_z')
        wave_layer = bm.verts.layers.float.new('water_wave_height')

        s = self.size / 2.0
        z = context.scene.cursor.location.z

        # Create base quad
        v1 = bm.verts.new((-s, -s, z))
        v2 = bm.verts.new((s, -s, z))
        v3 = bm.verts.new((s, s, z))
        v4 = bm.verts.new((-s, s, z))

        for v in [v1, v2, v3, v4]:
            v[speed_x_layer] = 0.0
            v[speed_y_layer] = 0.0
            v[speed_z_layer] = self.speed
            v[wave_layer] = self.wave_height

        bm.faces.new([v1, v2, v3, v4])

        # Subdivide if needed
        if self.subdivisions > 0:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=self.subdivisions)
            for v in bm.verts:
                v[speed_x_layer] = 0.0
                v[speed_y_layer] = 0.0
                v[speed_z_layer] = self.speed
                v[wave_layer] = self.wave_height

        # Generate planar UV from XY coordinates
        uv_layer = bm.loops.layers.uv.new('UVMap')
        uv_scale = 1.0 / 100.0
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = (loop.vert.co.x * uv_scale, loop.vert.co.y * uv_scale)

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new("Water", mesh)
        obj['water_flag'] = int(self.water_flag)

        # Water material with texture
        from .water_import import _get_water_material
        mat = _get_water_material()
        mesh.materials.append(mat)

        # Add to Water collection
        water_col = bpy.data.collections.get("Water")
        if not water_col:
            water_col = bpy.data.collections.new("Water")
            context.scene.collection.children.link(water_col)
        water_col.objects.link(obj)

        # Position at cursor XY. With block snapping, drop the quad's
        # min (SW) corner onto the 500-block boundary containing the
        # cursor, so a 500-size quad exactly fills one water block and
        # renders in-game.
        cx = context.scene.cursor.location.x
        cy = context.scene.cursor.location.y
        if self.snap_to_block:
            bx0, _ = block_bounds(cx)
            by0, _ = block_bounds(cy)
            obj.location.x = bx0 + s
            obj.location.y = by0 + s
        else:
            obj.location.x = cx
            obj.location.y = cy

        self.report({'INFO'}, f"Water plane created ({self.size}x{self.size})")
        return {'FINISHED'}


class GTATOOLS_OT_water_snap_grid(bpy.types.Operator):
    """Привязать вершины воды к кратным 4 координатам (требование GTA SA)"""
    bl_idname = "gtatools.water_snap_grid"
    bl_label = "INU: Snap to Grid (x4)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            mesh = obj.data
            mat_w = obj.matrix_world
            for vert in mesh.vertices:
                co = mat_w @ vert.co
                new_x = round(co.x / 4.0) * 4.0
                new_y = round(co.y / 4.0) * 4.0
                inv = mat_w.inverted()
                from mathutils import Vector
                new_co = inv @ Vector((new_x, new_y, co.z))
                vert.co = new_co
                count += 1
            mesh.update()
        self.report({'INFO'}, f"{T('Привязано вершин:')} {count}")
        return {'FINISHED'}


class GTATOOLS_OT_water_snap_block(bpy.types.Operator):
    """Привязать вершины воды к ближайшему узлу лимитной сетки (кратным 500 — углы блоков воды GTA SA)"""
    bl_idname = "gtatools.water_snap_block"
    bl_label = "INU: Snap to Block Grid (500)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from mathutils import Vector
        step = WATER_BLOCK_SIZE
        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            mesh = obj.data
            mat_w = obj.matrix_world
            inv = mat_w.inverted()
            for vert in mesh.vertices:
                co = mat_w @ vert.co
                new_x = round(co.x / step) * step
                new_y = round(co.y / step) * step
                vert.co = inv @ Vector((new_x, new_y, co.z))
                count += 1
            mesh.update()
        self.report({'INFO'}, f"{T('Привязано к блоку:')} {count}")
        return {'FINISHED'}


def _wl_block_base_name(name):
    """Strip a previously appended ``_<bx>_<by>`` block suffix so
    re-splitting an already-split object doesn't stack suffixes."""
    import re
    m = re.match(r'^(.*)_-?\d+_-?\d+$', name)
    return m.group(1) if m else name


def _wl_split_bm_to_objects(obj, bm):
    """Emit one new object per 500-block from ``bm``'s faces.

    Copies vertex float layers (water speed / wave height), UV layers,
    materials, custom properties (``water_flag``) and the source
    transform. Returns the new objects, or [] when everything already
    sits in a single block (caller then keeps the original object).
    """
    import math
    mat_w = obj.matrix_world

    groups = {}
    for f in bm.faces:
        c = mat_w @ f.calc_center_median()
        key = (math.floor(c.x / WATER_BLOCK_SIZE),
               math.floor(c.y / WATER_BLOCK_SIZE))
        groups.setdefault(key, []).append(f)
    if len(groups) <= 1:
        return []

    float_names = list(bm.verts.layers.float.keys())
    uv_names = list(bm.loops.layers.uv.keys())
    src_float = {n: bm.verts.layers.float[n] for n in float_names}
    src_uv = {n: bm.loops.layers.uv[n] for n in uv_names}
    base = _wl_block_base_name(obj.name)

    new_objects = []
    for key in sorted(groups):
        nbm = bmesh.new()
        dst_float = {n: nbm.verts.layers.float.new(n) for n in float_names}
        dst_uv = {n: nbm.loops.layers.uv.new(n) for n in uv_names}

        vmap = {}
        for f in groups[key]:
            src_loops = list(f.loops)
            nverts = []
            for loop in src_loops:
                v = loop.vert
                nv = vmap.get(v)
                if nv is None:
                    nv = nbm.verts.new(v.co)
                    for n, lay in dst_float.items():
                        nv[lay] = v[src_float[n]]
                    vmap[v] = nv
                nverts.append(nv)
            try:
                nf = nbm.faces.new(nverts)
            except ValueError:
                continue          # duplicate face — skip
            nf.material_index = f.material_index
            nf.smooth = f.smooth
            for src_loop, dst_loop in zip(src_loops, nf.loops):
                for n in uv_names:
                    dst_loop[dst_uv[n]].uv = src_loop[src_uv[n]].uv

        me = bpy.data.meshes.new(f"{base}_{key[0]}_{key[1]}")
        nbm.to_mesh(me)
        nbm.free()
        for mat in obj.data.materials:
            me.materials.append(mat)

        nobj = bpy.data.objects.new(me.name, me)
        nobj.matrix_world = mat_w.copy()
        for prop_key in obj.keys():
            if prop_key == '_RNA_UI':
                continue
            try:
                nobj[prop_key] = obj[prop_key]
            except (TypeError, ValueError):
                pass
        for col in obj.users_collection:
            col.objects.link(nobj)
        new_objects.append(nobj)

    return new_objects


class GTATOOLS_OT_water_split_blocks(bpy.types.Operator):
    """Порезать воду по сетке блоков 500×500 — каждая грань ляжет внутрь одного блока (иначе вода рендерится без текстуры)"""
    bl_idname = "gtatools.water_split_blocks"
    bl_label = "INU: Split Water by Block Grid"
    bl_options = {'REGISTER', 'UNDO'}

    separate: BoolProperty(
        name=T("Разделить на объекты"), default=True,
        description=T("Разнести куски по отдельным объектам — по одному на блок 500×500"))

    def execute(self, context):
        import math
        from mathutils import Vector

        if context.mode != 'OBJECT':
            self.report({'ERROR'}, T("Выйдите из режима редактирования"))
            return {'CANCELLED'}

        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            self.report({'ERROR'}, T("Выделите водные объекты"))
            return {'CANCELLED'}

        step = WATER_BLOCK_SIZE
        eps = 0.001
        LAYER_NAMES = ('water_speed_x', 'water_speed_y', 'water_speed_z',
                       'water_wave_height')
        faces_before = faces_after = 0
        created = []      # new per-block objects
        dead = []         # originals replaced by those objects

        for obj in objects:
            mesh = obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            faces_before += len(bm.faces)

            mat_w = obj.matrix_world
            inv = mat_w.inverted()
            # Normals transform by the inverse-transpose — a scaled or
            # rotated water object still gets cut on the WORLD grid.
            nmat = inv.transposed().to_3x3()

            # Sample the water params of the pre-cut mesh so new verts
            # created by the bisect inherit them (bisect zeroes float
            # layers it cannot interpolate).
            samples = []   # [(world_co, {layer: value})]
            for v in bm.verts:
                vals = {}
                for name in LAYER_NAMES:
                    lay = bm.verts.layers.float.get(name)
                    if lay is not None:
                        vals[name] = v[lay]
                samples.append((mat_w @ v.co, vals))

            world = [s[0] for s in samples]
            if not world:
                bm.free()
                continue

            planes = []
            for axis in (0, 1):
                lo = min(w[axis] for w in world)
                hi = max(w[axis] for w in world)
                k0 = math.floor(lo / step) + 1
                k1 = math.ceil(hi / step) - 1
                # Guard against a stray vert far outside the ±3000 map
                # turning this into thousands of bisects.
                if k1 - k0 > 64:
                    k1 = k0 + 64
                for k in range(k0, k1 + 1):
                    coord = k * step
                    if coord <= lo + eps or coord >= hi - eps:
                        continue
                    planes.append((axis, coord))

            if not planes:
                faces_after += len(bm.faces)
                bm.free()
                continue

            for axis, coord in planes:
                wno = Vector((1.0, 0.0, 0.0)) if axis == 0 else Vector((0.0, 1.0, 0.0))
                wco = Vector((coord, 0.0, 0.0)) if axis == 0 else Vector((0.0, coord, 0.0))
                lno = (nmat @ wno)
                if lno.length < 1e-9:
                    continue
                geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
                bmesh.ops.bisect_plane(
                    bm, geom=geom, dist=0.0001,
                    plane_co=inv @ wco, plane_no=lno.normalized(),
                    use_snap_center=False, clear_inner=False, clear_outer=False)

            # water.dat holds only tris and quads — the export silently
            # drops anything bigger, so cut n-gons the bisect may leave.
            ngons = [f for f in bm.faces if len(f.verts) > 4]
            if ngons:
                bmesh.ops.triangulate(bm, faces=ngons)

            # Re-apply water params: uniform value if the object had one,
            # otherwise nearest original vertex (only for verts the cut
            # actually created — untouched verts keep what they had).
            by_pos = {(round(w.x, 3), round(w.y, 3), round(w.z, 3)): vals
                      for w, vals in samples}
            for name in LAYER_NAMES:
                lay = bm.verts.layers.float.get(name)
                if lay is None:
                    continue
                vals_set = {round(s[1].get(name, 0.0), 5) for s in samples}
                if len(vals_set) == 1:
                    val = next(iter(vals_set))
                    for v in bm.verts:
                        v[lay] = val
                    continue
                for v in bm.verts:
                    wc = mat_w @ v.co
                    key = (round(wc.x, 3), round(wc.y, 3), round(wc.z, 3))
                    old = by_pos.get(key)
                    if old is not None:
                        v[lay] = old.get(name, 0.0)
                    elif len(samples) <= 4096:
                        nearest = min(samples,
                                      key=lambda s: (s[0] - wc).length_squared)
                        v[lay] = nearest[1].get(name, 0.0)

            faces_after += len(bm.faces)

            pieces = _wl_split_bm_to_objects(obj, bm) if self.separate else []
            bm.free()
            if pieces:
                created += pieces
                dead.append(obj)
            else:
                bm.to_mesh(mesh)
                mesh.update()

        # Drop the originals only after every object is processed —
        # removing an object mid-loop would invalidate the list.
        for obj in dead:
            old_mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if old_mesh.users == 0:
                bpy.data.meshes.remove(old_mesh)

        if created:
            for o in context.selected_objects:
                o.select_set(False)
            for o in created:
                o.select_set(True)
            context.view_layer.objects.active = created[0]

        _water_limits_cache['sig'] = None
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        msg = f"{T('Порезано по блокам:')} {faces_before} → {faces_after}"
        if created:
            msg += f", {T('объектов:')} {len(created)}"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_water_set_params(bpy.types.Operator):
    """Задать параметры воды для выделенных объектов"""
    bl_idname = "gtatools.water_set_params"
    bl_label = "INU: Set Water Parameters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        flag = int(scene.inu_settings.gtatools_water_flag)
        speed_x = scene.inu_settings.gtatools_water_speed_x
        speed_y = scene.inu_settings.gtatools_water_speed_y
        speed_z = scene.inu_settings.gtatools_water_speed_z
        wave = scene.inu_settings.gtatools_water_wave_height

        count = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            obj['water_flag'] = flag
            mesh = obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)

            sx = bm.verts.layers.float.get('water_speed_x') or bm.verts.layers.float.new('water_speed_x')
            sy = bm.verts.layers.float.get('water_speed_y') or bm.verts.layers.float.new('water_speed_y')
            sz = bm.verts.layers.float.get('water_speed_z') or bm.verts.layers.float.new('water_speed_z')
            wh = bm.verts.layers.float.get('water_wave_height') or bm.verts.layers.float.new('water_wave_height')

            for v in bm.verts:
                v[sx] = speed_x
                v[sy] = speed_y
                v[sz] = speed_z
                v[wh] = wave

            bm.to_mesh(mesh)
            bm.free()
            count += 1

        self.report({'INFO'}, f"{T('Параметры воды:')} {count} objects")
        return {'FINISHED'}


class GTATOOLS_OT_water_stitch(bpy.types.Operator):
    """Сшить края двух водных плоскостей (выровнять ближайшие вершины)"""
    bl_idname = "gtatools.water_stitch"
    bl_label = "INU: Stitch Water Edges"
    bl_options = {'REGISTER', 'UNDO'}

    threshold: FloatProperty(name="Threshold", default=1.0, min=0.01, max=50.0)

    def execute(self, context):

        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if len(mesh_objects) < 2:
            self.report({'ERROR'}, T("Выделите минимум 2 меш объекта"))
            return {'CANCELLED'}

        # Collect all boundary vertices (edges with only 1 face)
        all_boundary = []  # [(world_co, obj, vert_index)]

        for obj in mesh_objects:
            mesh = obj.data
            mat_w = obj.matrix_world

            # Find boundary vertices
            vert_face_count = [0] * len(mesh.vertices)
            for poly in mesh.polygons:
                for vi in poly.vertices:
                    vert_face_count[vi] += 1

            for edge in mesh.edges:
                edge_faces = 0
                for poly in mesh.polygons:
                    verts = list(poly.vertices)
                    if edge.vertices[0] in verts and edge.vertices[1] in verts:
                        edge_faces += 1
                if edge_faces == 1:  # boundary edge
                    for vi in edge.vertices:
                        co = mat_w @ mesh.vertices[vi].co
                        all_boundary.append((co, obj, vi))

        if not all_boundary:
            self.report({'WARNING'}, T("Нет граничных вершин"))
            return {'CANCELLED'}

        # Match boundary vertices between objects
        stitched = 0
        for i, (co1, obj1, vi1) in enumerate(all_boundary):
            for j, (co2, obj2, vi2) in enumerate(all_boundary):
                if obj1 == obj2 or j <= i:
                    continue
                dist = (co1 - co2).length
                if dist < self.threshold:
                    # Average position
                    avg = (co1 + co2) / 2.0
                    inv1 = obj1.matrix_world.inverted()
                    inv2 = obj2.matrix_world.inverted()
                    obj1.data.vertices[vi1].co = inv1 @ avg
                    obj2.data.vertices[vi2].co = inv2 @ avg
                    stitched += 1

        for obj in mesh_objects:
            obj.data.update()

        self.report({'INFO'}, f"{T('Сшито вершин:')} {stitched}")
        return {'FINISHED'}


# =============================================================================
# WATER LIMITS OVERLAY — 500-block grid + per-face fit highlighting
# =============================================================================
#
# Each mesh FACE is exported as one water.dat polygon (see water_export),
# and the engine renders water per 500-unit block, so every face must be
# ≤500 and sit inside a single block. This toggleable viewport overlay
# draws the block grid and tints each water face:
#   green  = fits a block (renders)
#   orange = ≤500 but straddles a block boundary (Snap to grid to fix)
#   red    = wider than 500 (must be subdivided / split)
# Drawn only while active — no cost when off (mirrors col_light preview).

import gpu
import blf
from gpu_extras.batch import batch_for_shader

_water_limits_handlers = []
_water_limits_active = False
_water_limits_cache = {'sig': None, 'data': None}

# Fill colours per fit status (RGBA)
_WL_COLORS = {
    'ok':       (0.10, 0.80, 0.20, 0.22),
    'cross':    (0.95, 0.60, 0.00, 0.30),
    'oversize': (0.90, 0.12, 0.12, 0.32),
}
_WL_GRID_COLOR = (0.25, 0.65, 0.95, 0.55)


def _wl_iter_water_objects():
    """Yield mesh objects that are water: in the 'Water' collection or
    carrying a 'water_flag' custom property."""
    seen = set()
    col = bpy.data.collections.get("Water")
    if col:
        for o in col.objects:
            if o.type == 'MESH':
                seen.add(o.name)
                yield o
    for o in bpy.context.scene.objects:
        if o.type == 'MESH' and 'water_flag' in o and o.name not in seen:
            seen.add(o.name)
            yield o


def _wl_signature(objects):
    """Cheap change-key: rebuild geometry only when water actually changes.

    Includes a hash of the VERTEX positions — without it, moving verts while
    the object matrix and face count stay put (snap-to-block, edit-mode
    resize) never invalidated the overlay, so it kept drawing stale tint/size.
    Water meshes are tiny (a few quads), so hashing every vert is cheap.
    """
    import numpy as np
    sig = []
    for o in objects:
        me = o.data
        n = len(me.vertices)
        if n:
            co = np.empty(n * 3, dtype=np.float32)
            me.vertices.foreach_get('co', co)
            vh = hash(np.round(co, 3).tobytes())
        else:
            vh = 0
        m = o.matrix_world
        sig.append((o.name, len(me.polygons), vh,
                    round(m[0][3], 3), round(m[1][3], 3), round(m[2][3], 3),
                    round(m[0][0], 4), round(m[1][1], 4)))
    return tuple(sig)


def _wl_build():
    """Compute overlay geometry (cached by signature)."""
    objects = list(_wl_iter_water_objects())
    sig = _wl_signature(objects)
    if _water_limits_cache['sig'] == sig:
        return _water_limits_cache['data']

    faces = []          # (status, tris, center, label)
    all_min = [None, None]
    all_max = [None, None]
    z_sum = 0.0
    z_n = 0

    for obj in objects:
        mesh = obj.data
        mat_w = obj.matrix_world
        for poly in mesh.polygons:
            if len(poly.vertices) not in (3, 4):
                continue
            world = [mat_w @ mesh.vertices[vi].co for vi in poly.vertices]
            xs = [v.x for v in world]
            ys = [v.y for v in world]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            status = check_quad_fit(min_x, min_y, max_x, max_y)

            # Lift slightly along normal so the fill sits above the mesh
            n = (mat_w.to_3x3() @ poly.normal).normalized() * 0.03
            vlift = [v + n for v in world]
            tris = []
            for i in range(1, len(vlift) - 1):
                tris.append(((vlift[0].x, vlift[0].y, vlift[0].z),
                             (vlift[i].x, vlift[i].y, vlift[i].z),
                             (vlift[i + 1].x, vlift[i + 1].y, vlift[i + 1].z)))
            c = mat_w @ poly.center
            label = None
            if status != 'ok':
                label = f"{round(max(max_x - min_x, max_y - min_y))}"
            faces.append((status, tris, (c.x, c.y, c.z), label))

            # accumulate grid extent / z
            for lo, hi, mn, mx in ((0, 0, min_x, max_x), (1, 1, min_y, max_y)):
                if all_min[lo] is None or mn < all_min[lo]:
                    all_min[lo] = mn
                if all_max[hi] is None or mx > all_max[hi]:
                    all_max[hi] = mx
            z_sum += c.z
            z_n += 1

    grid = []
    if z_n and all_min[0] is not None:
        z = z_sum / z_n
        import math
        gx0 = (math.floor(all_min[0] / WATER_BLOCK_SIZE) - 1) * WATER_BLOCK_SIZE
        gx1 = (math.floor(all_max[0] / WATER_BLOCK_SIZE) + 2) * WATER_BLOCK_SIZE
        gy0 = (math.floor(all_min[1] / WATER_BLOCK_SIZE) - 1) * WATER_BLOCK_SIZE
        gy1 = (math.floor(all_max[1] / WATER_BLOCK_SIZE) + 2) * WATER_BLOCK_SIZE
        # Safety clamp: never emit a runaway number of grid lines if a
        # water object sits far outside the ±3000 map.
        MAX_SPAN = WATER_BLOCK_SIZE * 64
        gx1 = min(gx1, gx0 + MAX_SPAN)
        gy1 = min(gy1, gy0 + MAX_SPAN)
        x = gx0
        while x <= gx1 + 0.5:
            grid.append((x, gy0, z))
            grid.append((x, gy1, z))
            x += WATER_BLOCK_SIZE
        y = gy0
        while y <= gy1 + 0.5:
            grid.append((gx0, y, z))
            grid.append((gx1, y, z))
            y += WATER_BLOCK_SIZE

    data = {'faces': faces, 'grid': grid}
    _water_limits_cache['sig'] = sig
    _water_limits_cache['data'] = data
    return data


def _draw_water_limits():
    """POST_VIEW: block grid + per-face fill."""
    if not _water_limits_active:
        return
    data = _wl_build()
    if not data:
        return

    gpu.state.blend_set('ALPHA')

    # Face fills
    positions = []
    colors = []
    for status, tris, _c, _lbl in data['faces']:
        col = _WL_COLORS.get(status, _WL_COLORS['ok'])
        for v0, v1, v2 in tris:
            positions.extend([v0, v1, v2])
            colors.extend([col, col, col])
    if positions:
        sh = gpu.shader.from_builtin('SMOOTH_COLOR')
        batch = batch_for_shader(sh, 'TRIS', {"pos": positions, "color": colors})
        sh.bind()
        batch.draw(sh)

    # Block grid lines
    if data['grid']:
        sh = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(sh, 'LINES', {"pos": data['grid']})
        sh.bind()
        sh.uniform_float("color", _WL_GRID_COLOR)
        batch.draw(sh)

    gpu.state.blend_set('NONE')


def _draw_water_limits_text():
    """POST_PIXEL: size number on problem faces."""
    if not _water_limits_active:
        return
    data = _wl_build()
    if not data:
        return

    from bpy_extras.view3d_utils import location_3d_to_region_2d
    from mathutils import Vector

    context = bpy.context
    region = context.region
    rv3d = context.region_data
    if not region or not rv3d:
        return

    font_id = 0
    blf.size(font_id, 13)
    for status, _tris, center, label in data['faces']:
        if not label:
            continue
        co = location_3d_to_region_2d(region, rv3d, Vector(center))
        if co is None:
            continue
        blf.color(font_id, 0.0, 0.0, 0.0, 0.9)
        blf.position(font_id, co.x + 1, co.y - 1, 0)
        blf.draw(font_id, label)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, co.x, co.y, 0)
        blf.draw(font_id, label)


class GTATOOLS_OT_toggle_water_limits(bpy.types.Operator):
    """Показать сетку блоков воды 500×500 и подсветить грани: зелёный — влезает, оранжевый — на границе, красный — больше 500"""
    bl_idname = "gtatools.toggle_water_limits"
    bl_label = "INU: Water Limits Overlay"
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _water_limits_active, _water_limits_handlers

        _water_limits_active = not _water_limits_active
        _water_limits_cache['sig'] = None

        if _water_limits_active:
            if not _water_limits_handlers:
                h1 = bpy.types.SpaceView3D.draw_handler_add(
                    _draw_water_limits, (), 'WINDOW', 'POST_VIEW')
                h2 = bpy.types.SpaceView3D.draw_handler_add(
                    _draw_water_limits_text, (), 'WINDOW', 'POST_PIXEL')
                _water_limits_handlers.extend([h1, h2])
            self.report({'INFO'}, T("Лимиты воды: показаны"))
        else:
            for h in _water_limits_handlers:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            _water_limits_handlers.clear()
            self.report({'INFO'}, T("Лимиты воды: скрыты"))

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


