# INU_tools.ops.txd_export — Blender wrappers for TXD export.
#
# The actual encoder lives in tools.txd_export (`export_txd`); this
# module just holds the operator classes that own filepath dialogs
# and report results to Blender's UI.

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper

from .. import T
from ..tools.txd_export import export_txd


class GTATOOLS_OT_export_txd(bpy.types.Operator, ExportHelper):
    """Экспортировать текстуры в TXD архив"""
    bl_idname = "gtatools.export_txd"
    bl_label = "INU: Export TXD"
    bl_options = {'PRESET'}
    filename_ext = ".txd"
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    selected_only: BoolProperty(
        name=T("Только выделенное"),
        description=T("Экспортировать текстуры только из выделенных объектов"),
        default=False,
    )
    shared_txd: BoolProperty(
        name=T("Общий TXD"),
        description=T(
            "Собрать все текстуры из выделенных DFF в один общий TXD.\n"
            "Авто-включает «Только выделенное» и подставляет имя ниже."),
        default=False,
    )
    shared_name: StringProperty(
        name=T("Имя"),
        description=T("Базовое имя для общего TXD (без .txd)"),
        default="",
    )

    def invoke(self, context, event):
        # Pre-fill shared name from scene preset so the user only types it once
        preset = getattr(context.scene.inu_settings, 'gtatools_shared_txd_name', '').strip()
        if preset and not self.shared_name:
            self.shared_name = preset
        return super().invoke(context, event)

    def execute(self, context):
        # Shared TXD implies selected-only collection
        sel_only = self.selected_only or self.shared_txd

        target = self.filepath
        if self.shared_txd and self.shared_name.strip():
            import os
            name = self.shared_name.strip()
            if not name.lower().endswith('.txd'):
                name += '.txd'
            target = os.path.join(os.path.dirname(target), name)

        backend = getattr(context.scene.inu_settings, 'gtatools_dxt_backend', 'numpy')
        result, message, transparent_list = export_txd(target, context, sel_only, backend=backend)
        self.report({'INFO'} if result == {'FINISHED'} else {'ERROR'}, message)
        return result

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        sub = col.row()
        sub.enabled = not self.shared_txd
        sub.prop(self, "selected_only")
        col.prop(self, "shared_txd")
        if self.shared_txd:
            col.prop(self, "shared_name")


class GTATOOLS_OT_export_shared_txd(bpy.types.Operator, ExportHelper):
    """Экспортировать один общий TXD для нескольких DFF моделей"""
    bl_idname = "gtatools.export_shared_txd"
    bl_label = "INU: Export Shared TXD"
    bl_options = {'PRESET'}
    filename_ext = ".txd"
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    def invoke(self, context, event):
        # Pre-fill filename from scene property
        txd_name = getattr(context.scene.inu_settings, 'gtatools_shared_txd_name', '').strip()
        if txd_name:
            if not txd_name.lower().endswith('.txd'):
                txd_name += '.txd'
            self.filepath = txd_name
        return super().invoke(context, event)

    def execute(self, context):
        selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        if not selected_meshes:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        backend = getattr(context.scene.inu_settings, 'gtatools_dxt_backend', 'numpy')
        # Force selected_only=True for shared TXD (collects from all selected DFFs)
        result, message, transparent_list = export_txd(self.filepath, context, True, backend=backend)
        self.report({'INFO'} if result == {'FINISHED'} else {'ERROR'}, message)
        return result


classes = (
    GTATOOLS_OT_export_txd,
    GTATOOLS_OT_export_shared_txd,
)
