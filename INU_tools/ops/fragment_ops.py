# INU_tools.ops.fragment_ops — раскол меша на отдельные объекты-осколки.
#
# Порт `object_explode.ms` (режим GRID — нарезка по сетке шага X/Y) плюс
# режим SCATTER — кластеризация граней по N случайным семенам (грубая
# voronoi-разбивка БЕЗ добавления новых резов: существующие грани просто
# группируются по ближайшему семени). Для настоящего геометрического
# фрактурinга (с добавлением плоскостей разлома) используйте встроенный
# Blender «Cell Fracture».
#
# Осколки — полные копии объекта с удалёнными «чужими» гранями, поэтому
# UV, vertex-color, материалы и прочие слои сохраняются как есть.

import random

import bpy
import bmesh
from bpy.props import (
    EnumProperty, FloatProperty, IntProperty, StringProperty, BoolProperty,
)

from .. import T


def _face_groups_grid(mesh, x_step, y_step):
    """dict[cell] -> set(face_index) по сетке шага X/Y (в локальных коорд.)."""
    verts = mesh.vertices
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    gab_x = max(max_x - min_x, 1e-6)
    gab_y = max(max_y - min_y, 1e-6)

    x_count = max(int(gab_x / x_step), 1)
    y_count = max(int(gab_y / y_step), 1)
    x_step2 = gab_x / x_count
    y_step2 = gab_y / y_count
    x_cells = x_count + 1

    groups = {}
    for poly in mesh.polygons:
        c = poly.center
        a = int((c.x - min_x) / x_step2)
        b = int((c.y - min_y) / y_step2)
        cell = a + b * x_cells
        groups.setdefault(cell, set()).add(poly.index)
    return groups


def _face_groups_scatter(mesh, count, seed):
    """dict[seed_idx] -> set(face_index): грань → ближайшее из N семян."""
    verts = mesh.vertices
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    zs = [v.co.z for v in verts]
    lo = (min(xs), min(ys), min(zs))
    hi = (max(xs), max(ys), max(zs))

    rng = random.Random(seed)
    seeds = [(
        rng.uniform(lo[0], hi[0]),
        rng.uniform(lo[1], hi[1]),
        rng.uniform(lo[2], hi[2]),
    ) for _ in range(max(count, 1))]

    groups = {}
    for poly in mesh.polygons:
        c = poly.center
        best_i, best_d = 0, None
        for i, s in enumerate(seeds):
            d = (c.x - s[0]) ** 2 + (c.y - s[1]) ** 2 + (c.z - s[2]) ** 2
            if best_d is None or d < best_d:
                best_d, best_i = d, i
        groups.setdefault(best_i, set()).add(poly.index)
    return groups


def _make_fragment(src_obj, keep_faces, name):
    """Копия объекта, где оставлены только грани keep_faces (индексы исходника)."""
    new_obj = src_obj.copy()
    new_obj.data = src_obj.data.copy()
    new_obj.name = name
    new_obj.data.name = name
    for coll in src_obj.users_collection:
        coll.objects.link(new_obj)

    bm = bmesh.new()
    bm.from_mesh(new_obj.data)
    bm.faces.ensure_lookup_table()
    # bm.faces[i] следует порядку полигонов исходного меша (copy сохраняет
    # порядок), поэтому позиционный индекс == исходный polygon.index.
    drop = [bm.faces[i] for i in range(len(bm.faces)) if i not in keep_faces]
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    # убрать оставшиеся висящие вершины
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(new_obj.data)
    bm.free()
    return new_obj


class GTATOOLS_OT_fragment_mesh(bpy.types.Operator):
    """Расколоть меш на отдельные объекты-осколки (сетка / кластеры)"""
    bl_idname = "gtatools.fragment_mesh"
    bl_label = "INU: Fragment Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(
        name=T("Режим"),
        items=[
            ('GRID', T("Сетка (шаг X/Y)"),
             T("Нарезать по прямоугольной сетке — как object_explode")),
            ('SCATTER', T("Кластеры (N семян)"),
             T("Сгруппировать грани по ближайшему из N случайных семян")),
        ],
        default='GRID',
    )
    x_step: FloatProperty(name=T("Шаг X"), default=2.0, min=0.01, soft_max=100.0)
    y_step: FloatProperty(name=T("Шаг Y"), default=2.0, min=0.01, soft_max=100.0)
    seed_count: IntProperty(name=T("Число осколков"), default=10, min=2, soft_max=200)
    seed: IntProperty(name=T("Seed"), default=0)
    base_name: StringProperty(name=T("Имя осколков"), default="")
    delete_original: BoolProperty(name=T("Удалить оригинал"), default=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'MESH'
                and len(obj.data.polygons) > 0)

    def invoke(self, context, event):
        if not self.base_name:
            self.base_name = context.active_object.name + "_frag"
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "mode")
        if self.mode == 'GRID':
            row = layout.row(align=True)
            row.prop(self, "x_step")
            row.prop(self, "y_step")
        else:
            layout.prop(self, "seed_count")
            layout.prop(self, "seed")
        layout.prop(self, "base_name")
        layout.prop(self, "delete_original")

    def execute(self, context):
        src = context.active_object
        mesh = src.data

        if self.mode == 'GRID':
            groups = _face_groups_grid(mesh, self.x_step, self.y_step)
        else:
            groups = _face_groups_scatter(mesh, self.seed_count, self.seed)

        groups = {k: v for k, v in groups.items() if v}
        if len(groups) < 2:
            self.report({'WARNING'},
                        T("Получился 1 осколок — уменьши шаг / добавь семян"))
            return {'CANCELLED'}

        created = []
        for i, keep in enumerate(sorted(groups.values(),
                                        key=lambda s: -len(s)), start=1):
            frag = _make_fragment(src, keep, f"{self.base_name}{i}")
            created.append(frag)

        if self.delete_original:
            bpy.data.objects.remove(src, do_unlink=True)

        for o in context.selected_objects:
            o.select_set(False)
        for o in created:
            o.select_set(True)
        if created:
            context.view_layer.objects.active = created[0]

        self.report({'INFO'},
                    f"{T('Осколков создано')}: {len(created)}")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_fragment_mesh,
)
