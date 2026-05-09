# INU_tools.ops.object_utils_ops — Object visibility toggles + snap-to-DFF helpers.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import bpy
from bpy.props import (
    StringProperty,
)

from .. import T


# Module-level visibility state for «скрыть/показать» toggles. Lives here
# (not __init__.py) so the operator's ``global`` declaration resolves —
# Python's ``global`` only sees the function's own module namespace.
_hide_dff = False
_hide_lod = False
_hide_col = False
_hide_sha = False


class GTATOOLS_OT_toggle_visibility(bpy.types.Operator):
    """Скрыть/показать DFF, LOD или COL объекты во всей сцене"""
    bl_idname = "gtatools.toggle_visibility"
    bl_label = "INU: Toggle Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    model_type: StringProperty()

    def execute(self, context):
        global _hide_dff, _hide_lod, _hide_col, _hide_sha
        from ..tools.model_utils import get_model_type
        # Authoritative LOD detector — handles `LOD<name>`, `<name>_LOD`,
        # `<name>LOD` после цифры/separator, и embedded `LOD` в legacy
        # Rockstar именах типа `modeLODlaett`. get_model_type() видит
        # только настроенный prefix/suffix и пропускает большинство
        # вариантов с маппинг-импорта.
        from ..core.ipl import is_lod_name
        # Authoritative SHA detector — same one COL exporter uses, чтобы
        # toggle и экспорт смотрели на shadow-меши одинаково.
        from .col_export import _is_shadow_mesh

        if self.model_type == 'DFF':
            _hide_dff = not _hide_dff
            hide = _hide_dff
        elif self.model_type == 'LOD':
            _hide_lod = not _hide_lod
            hide = _hide_lod
        elif self.model_type == 'COL':
            _hide_col = not _hide_col
            hide = _hide_col
        elif self.model_type == 'SHA':
            _hide_sha = not _hide_sha
            hide = _hide_sha
        else:
            return {'CANCELLED'}

        count = 0
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            mt, _ = get_model_type(obj)
            is_sha = _is_shadow_mesh(obj)
            if self.model_type == 'LOD':
                # LOD: any name matching is_lod_name (broad), regardless
                # of get_model_type's prefix/suffix-only verdict.
                matches = is_lod_name(obj.name)
            elif self.model_type == 'SHA':
                matches = is_sha
            elif self.model_type == 'COL':
                # COL — реальный _COL, не shadow-меш (у тех своя кнопка).
                matches = (mt == 'COL') and not is_sha
            else:  # DFF — everything that is not LOD, not COL, not SHA
                matches = (mt != 'COL') and not is_lod_name(obj.name) and not is_sha
            if matches:
                obj.hide_viewport = hide
                count += 1

        self.report({'INFO'}, f"{self.model_type}: {'Hidden' if hide else 'Visible'} ({count})")
        return {'FINISHED'}


class GTATOOLS_OT_snap_to_dff(bpy.types.Operator):
    """Подтянуть LOD и COL к позиции DFF модели"""
    bl_idname = "gtatools.snap_to_dff"
    bl_label = "INU: Snap LOD/COL to DFF"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..tools.model_utils import get_model_type

        # Group all scene meshes by base name
        groups = {}
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            mt, base = get_model_type(obj)
            if not base:
                continue
            base_clean = base.rstrip('_').lower()
            if base_clean not in groups:
                groups[base_clean] = {'DFF': None, 'LOD': None, 'COL': None}
            if mt and groups[base_clean][mt] is None:
                groups[base_clean][mt] = obj

        snapped = 0
        for base, g in groups.items():
            dff = g['DFF']
            if not dff:
                continue
            for mt in ('LOD', 'COL'):
                other = g[mt]
                if other and other.location != dff.location:
                    other.location = dff.location.copy()
                    other.rotation_mode = dff.rotation_mode
                    if dff.rotation_mode == 'QUATERNION':
                        other.rotation_quaternion = dff.rotation_quaternion.copy()
                    else:
                        other.rotation_euler = dff.rotation_euler.copy()
                    snapped += 1

        self.report({'INFO'}, f"{T('Перемещено:')} {snapped}")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_toggle_visibility,
    GTATOOLS_OT_snap_to_dff,
)
