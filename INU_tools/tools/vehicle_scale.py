# INU_tools.tools.vehicle_scale — uniform rescale of a vehicle hierarchy.
#
# GTA SA vehicles are stored as a tree of Empties (chassis_dummy,
# wheel_*_dummy, bump_front_dummy, door_*_dummy, …) with meshes as
# children. Applying `obj.scale = (s,s,s)` only to the root does NOT
# rescale the dummies' positions inside the hierarchy — children stay
# at their original local offsets but render at a different world
# scale, which looks right in Blender but ships broken in game.
#
# This operator walks the hierarchy and rescales:
#   • every child's `location` by the factor
#   • every mesh's vertex positions by the factor (via mesh.transform)
#   • every Empty's display size by the factor
# Then resets `scale` to (1,1,1) everywhere so the hierarchy stays
# clean for the DFF exporter.

from __future__ import annotations

import bpy
from mathutils import Matrix, Vector


def _walk(obj, out: list):
    out.append(obj)
    for ch in obj.children:
        _walk(ch, out)


def _rescale_hierarchy(root, factor: float, *, dummies_only: bool):
    """Return (scaled_meshes, scaled_empties) count after walking the tree."""
    if factor <= 0.0:
        return 0, 0

    tree: list[bpy.types.Object] = []
    _walk(root, tree)

    scaled_meshes = 0
    scaled_empties = 0
    scale_mat = Matrix.Scale(factor, 4)

    for obj in tree:
        # Rescale position offset from parent
        obj.location = Vector(obj.location) * factor
        # Reset any parent-inverse that would re-multiply scale
        try:
            obj.matrix_parent_inverse.identity()
        except Exception:
            pass

        if obj.type == 'MESH' and not dummies_only:
            # Transform the mesh data itself so vertex positions shrink/grow
            if obj.data.users == 1:
                obj.data.transform(scale_mat)
            else:
                # Shared mesh — copy so we don't touch other users
                obj.data = obj.data.copy()
                obj.data.transform(scale_mat)
            obj.scale = (1.0, 1.0, 1.0)
            scaled_meshes += 1

        elif obj.type == 'EMPTY':
            obj.empty_display_size *= factor
            obj.scale = (1.0, 1.0, 1.0)
            scaled_empties += 1

        elif obj.type == 'ARMATURE':
            # For skinned vehicles — transform the armature data too
            if obj.data.users == 1:
                obj.data.transform(scale_mat)
            obj.scale = (1.0, 1.0, 1.0)

    return scaled_meshes, scaled_empties


class GTATOOLS_OT_vehicle_scale(bpy.types.Operator):
    bl_idname = "gtatools.vehicle_scale"
    bl_label = "Vehicle Scale"
    bl_description = (
        "Rescale the active vehicle hierarchy (Empty root + meshes + dummies) "
        "preserving structure. Applies scale to mesh data so DFF export stays clean"
    )
    bl_options = {'REGISTER', 'UNDO'}

    factor: bpy.props.FloatProperty(
        name="Factor", default=1.0, min=0.01, max=100.0,
        description="Uniform scale factor applied to positions and vertices",
    )
    dummies_only: bpy.props.BoolProperty(
        name="Dummies Only",
        description="Move only the dummy empties, leave meshes untouched",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        root = context.active_object
        meshes, empties = _rescale_hierarchy(
            root, self.factor, dummies_only=self.dummies_only)
        self.report(
            {'INFO'},
            f"×{self.factor:g}: {meshes} mesh(es), {empties} empty(s)")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_vehicle_scale,
)
