# INU_tools.ops.frame_hierarchy
# Frame Hierarchy Editor — focused tools for editing the DFF frame tree
# (the chain of dummy/mesh objects that gets serialised as the DFF Frame
# List). Critical for vehicle and ped workflows where the engine looks
# up frames by exact name (chassis_dummy, wheel_lf_dummy, R UpperArm, …).
#
# This module owns:
#   - operators: rename, set/clear parent, validate-against-template,
#     mirror left↔right
#   - vanilla-name templates for vehicles and peds
#
# The actual UI lives in ui/panels.py (panel that draws the descendant
# tree of the active object plus the operator buttons).

import bpy
from bpy.props import StringProperty

from .. import T


# ── Vanilla SA name templates ──────────────────────────────────
# Required = engine reads this exact name; missing = broken behavior.
# Optional = nice to have, no engine error if absent.

VEHICLE_REQUIRED = {
    'chassis_dummy':   "верхний dummy всей машины",
    'wheel_lf_dummy':  "ось переднего левого колеса",
    'wheel_rf_dummy':  "ось переднего правого колеса",
    'wheel_lb_dummy':  "ось заднего левого колеса",
    'wheel_rb_dummy':  "ось заднего правого колеса",
}

VEHICLE_OPTIONAL = {
    'bonnet_dummy', 'boot_dummy',
    'door_lf_dummy', 'door_rf_dummy', 'door_lb_dummy', 'door_rb_dummy',
    'bumper_lf_dummy', 'bumper_rf_dummy',
    'wing_lf_dummy', 'wing_rf_dummy',
    'exhaust_dummy', 'misc_a', 'misc_b', 'misc_c',
}

# Ped skeleton — these 31 names are matched verbatim by ped.ifp.
PED_REQUIRED = {
    'Root', 'Pelvis', 'Spine', 'Spine1', 'Neck', 'Head',
    'Bip01 L Clavicle', 'L UpperArm', 'L Forearm', 'L Hand', 'L Finger',
    'Bip01 R Clavicle', 'R UpperArm', 'R Forearm', 'R Hand', 'R Finger',
    'L Thigh', 'L Calf', 'L Foot', 'L Toe0',
    'R Thigh', 'R Calf', 'R Foot', 'R Toe0',
    'Bip01',
}


# ── Helpers ────────────────────────────────────────────────────

def _all_descendants(root):
    """Depth-first list of root + all children, no ordering guarantees
    beyond depth-first."""
    out = [root]
    stack = list(root.children)
    while stack:
        cur = stack.pop()
        out.append(cur)
        stack.extend(cur.children)
    return out


def _restore_world_after_reparent(obj, parent):
    """Re-parent ``obj`` under ``parent`` while preserving its world
    transform. matrix_parent_inverse is reset to identity so the DFF
    exporter doesn't bake an offset into the frame matrix."""
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse.identity()
    if parent is not None:
        # World = parent_world @ local. Recompute local from world.
        obj.matrix_world = world


# ── Operators ──────────────────────────────────────────────────

class GTATOOLS_OT_frame_select(bpy.types.Operator):
    """Сделать активным указанный фрейм (используется панелью при клике
    на строку дерева)."""
    bl_idname = "gtatools.frame_select"
    bl_label = "INU: Select Frame"
    bl_options = {'REGISTER', 'UNDO'}

    target_name: StringProperty()
    extend: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        target = bpy.data.objects.get(self.target_name)
        if target is None:
            return {'CANCELLED'}
        if not self.extend:
            for o in context.selected_objects:
                o.select_set(False)
        target.select_set(True)
        context.view_layer.objects.active = target
        return {'FINISHED'}


class GTATOOLS_OT_frame_rename(bpy.types.Operator):
    """Переименовать активный фрейм."""
    bl_idname = "gtatools.frame_rename"
    bl_label = "INU: Rename Frame"
    bl_options = {'REGISTER', 'UNDO'}

    new_name: StringProperty(
        name=T("Имя"),
        description=T("Новое имя фрейма (точное соответствие требуется для машин и педов)"),
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        self.new_name = context.active_object.name
        return context.window_manager.invoke_props_dialog(self, width=380)

    def execute(self, context):
        obj = context.active_object
        new = self.new_name.strip()
        if not new or obj is None:
            self.report({'ERROR'}, T("Имя не может быть пустым"))
            return {'CANCELLED'}
        if new == obj.name:
            return {'CANCELLED'}
        old = obj.name
        obj.name = new
        # Update DFF write-name flag so the new name actually survives export.
        if 'dff_frame_write_name' in obj:
            obj['dff_frame_write_name'] = True
        self.report({'INFO'}, f"{old} → {obj.name}")
        return {'FINISHED'}


class GTATOOLS_OT_frame_set_parent(bpy.types.Operator):
    """Назначить parent: активный объект становится родителем для остальных
    выделенных. Мировая позиция каждого ребёнка сохраняется, а
    matrix_parent_inverse сбрасывается в identity (DFF requirement)."""
    bl_idname = "gtatools.frame_set_parent"
    bl_label = "INU: Set Frame Parent"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None
                and len(context.selected_objects) >= 2)

    def execute(self, context):
        parent = context.active_object
        children = [o for o in context.selected_objects if o is not parent]
        for c in children:
            _restore_world_after_reparent(c, parent)
        self.report({'INFO'},
                    f"{T('parent')} {parent.name} → {len(children)}")
        return {'FINISHED'}


class GTATOOLS_OT_frame_unparent(bpy.types.Operator):
    """Снять parent с выделенных объектов (parent → None). Мировая
    позиция сохраняется."""
    bl_idname = "gtatools.frame_unparent"
    bl_label = "INU: Clear Frame Parent"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(o.parent for o in context.selected_objects)

    def execute(self, context):
        count = 0
        for o in context.selected_objects:
            if o.parent:
                _restore_world_after_reparent(o, None)
                count += 1
        self.report({'INFO'}, f"{T('сняли parent с')}: {count}")
        return {'FINISHED'}


class GTATOOLS_OT_frame_validate(bpy.types.Operator):
    """Проверить иерархию активного объекта против vanilla SA шаблона.
    Тип шаблона выбирается атрибутом ``template`` оператора."""
    bl_idname = "gtatools.frame_validate"
    bl_label = "INU: Validate Frame Hierarchy"
    bl_options = {'REGISTER'}

    template: bpy.props.EnumProperty(
        name="Template",
        items=[
            ('VEHICLE', "Vehicle", "GTA SA vehicle dummy hierarchy"),
            ('PED',     "Ped",     "GTA SA ped 31-bone skeleton"),
        ],
        default='VEHICLE',
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        root = context.active_object
        descendants = _all_descendants(root)
        names = {o.name for o in descendants}
        names_lower = {n.lower() for n in names}

        if self.template == 'VEHICLE':
            required = VEHICLE_REQUIRED
            missing = [
                f"{name} — {desc}"
                for name, desc in required.items()
                if name not in names_lower
            ]
            # Suspicious wheel names (probably typos)
            suspicious = []
            for n in names_lower:
                if 'wheel' in n:
                    if not any(s in n for s in
                               ('_lf', '_rf', '_lb', '_rb')):
                        suspicious.append(f"{n} — wheel без _lf/_rf/_lb/_rb")
            label = "Vehicle"
        else:
            required = PED_REQUIRED
            # Peds use exact case-sensitive match
            missing = [
                f"{name}"
                for name in required
                if name not in names
            ]
            suspicious = []
            label = "Ped"

        # Always log — easier to copy-paste from console.
        print(f"[frame_validate {label}] root={root.name}, "
              f"descendants={len(descendants)}")
        if missing:
            print(f"  Missing required ({len(missing)}):")
            for m in missing:
                print(f"    ! {m}")
        if suspicious:
            print(f"  Suspicious ({len(suspicious)}):")
            for s in suspicious:
                print(f"    ? {s}")
        if not missing and not suspicious:
            print("  OK — все обязательные имена на месте")

        if missing or suspicious:
            self.report({'WARNING'},
                        f"{label}: missing={len(missing)}, "
                        f"suspicious={len(suspicious)} "
                        f"({T('см. System Console')})")
        else:
            self.report({'INFO'}, f"{label} {T('иерархия OK')}")
        return {'FINISHED'}


class GTATOOLS_OT_frame_mirror_lr(bpy.types.Operator):
    """Создать зеркальную копию выделенных фреймов: ``_lf`` → ``_rf``,
    ``_lb`` → ``_rb`` (X отражается, остальные оси без изменений). Если
    зеркальный близнец уже существует — оператор его не трогает."""
    bl_idname = "gtatools.frame_mirror_lr"
    bl_label = "INU: Mirror Left↔Right"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(
            any(suf in o.name for suf in ('_lf', '_lb'))
            for o in context.selected_objects
        )

    _MAP = {'_lf': '_rf', '_lb': '_rb'}

    def execute(self, context):
        created = 0
        skipped = 0

        for src in list(context.selected_objects):
            mirror_suffix = None
            target_name = None
            for src_suf, dst_suf in self._MAP.items():
                if src_suf in src.name:
                    target_name = src.name.replace(src_suf, dst_suf, 1)
                    mirror_suffix = (src_suf, dst_suf)
                    break
            if mirror_suffix is None:
                continue
            if target_name in bpy.data.objects:
                skipped += 1
                continue

            # Duplicate: keep parent + flip X position
            if src.data is None:
                copy = bpy.data.objects.new(target_name, None)
                copy.empty_display_type = src.empty_display_type
                copy.empty_display_size = src.empty_display_size
            else:
                copy = bpy.data.objects.new(target_name, src.data.copy())

            copy.parent = src.parent
            copy.matrix_parent_inverse = src.matrix_parent_inverse.copy()
            # Mirror local X
            from mathutils import Matrix
            mirror_x = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))
            copy.matrix_basis = src.matrix_basis @ mirror_x

            # Carry DFF frame metadata if present
            for k in ('dff_frame_flags', 'dff_frame_write_name'):
                if k in src:
                    copy[k] = src[k]

            # Link to same collections
            for col in src.users_collection:
                col.objects.link(copy)

            created += 1

        self.report({'INFO'},
                    f"{T('зеркально создано')}: {created}, "
                    f"{T('пропущено (уже есть)')}: {skipped}")
        return {'FINISHED'}


