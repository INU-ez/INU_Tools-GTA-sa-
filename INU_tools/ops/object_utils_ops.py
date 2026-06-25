# INU_tools.ops.object_utils_ops — Object visibility toggles + snap-to-DFF helpers.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import bpy
from bpy.props import (
    StringProperty,
)

from .. import T


# Module-level mirrors of the scene-property toggle state. Kept ONLY
# for backward compat with any external code that still reads them
# directly; the authoritative source is ``scene.inu_settings.gtatools_
# hide_*`` so state persists with the .blend across Blender restarts.
# Module globals reset on every addon (re)load and previously caused
# the panel's depress= buttons to "unpress themselves" after restart
# even when objects in the scene were still hidden.
_hide_dff = False
_hide_lod = False
_hide_col = False
_hide_sha = False


_TOGGLE_PROP = {
    'DFF': 'gtatools_hide_dff',
    'LOD': 'gtatools_hide_lod',
    'COL': 'gtatools_hide_col',
    'SHA': 'gtatools_hide_sha',
}


def _sync_module_globals(scene):
    """Mirror scene-prop values into module globals so legacy readers
    still see the right state. Called after every toggle flip."""
    global _hide_dff, _hide_lod, _hide_col, _hide_sha
    s = scene.inu_settings
    _hide_dff = bool(s.gtatools_hide_dff)
    _hide_lod = bool(s.gtatools_hide_lod)
    _hide_col = bool(s.gtatools_hide_col)
    _hide_sha = bool(s.gtatools_hide_sha)


class GTATOOLS_OT_toggle_visibility(bpy.types.Operator):
    """Скрыть/показать DFF, LOD или COL объекты во всей сцене"""
    bl_idname = "gtatools.toggle_visibility"
    bl_label = "INU: Toggle Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    model_type: StringProperty()

    def execute(self, context):
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

        prop_name = _TOGGLE_PROP.get(self.model_type)
        if prop_name is None:
            return {'CANCELLED'}
        settings = context.scene.inu_settings
        new_hide = not getattr(settings, prop_name)
        setattr(settings, prop_name, new_hide)
        _sync_module_globals(context.scene)
        hide = new_hide

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


