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
        import os
        # Shared TXD implies selected-only collection
        sel_only = self.selected_only or self.shared_txd
        backend = getattr(context.scene.inu_settings, 'gtatools_dxt_backend', 'numpy')
        is_mobile = getattr(context.scene.inu_settings, 'gtatools_platform', 'PC') == 'MOBILE'

        # ── Per-mesh split: «selected only» + multiple selected meshes
        # without «shared TXD» → one .txd per mesh, named after the
        # mesh (suffix-stripped), all written to the chosen directory.
        # Mirrors the per-model TXD layout the full Export pipeline
        # produces, instead of bundling everything into one file.
        if self.selected_only and not self.shared_txd:
            selected_meshes = [o for o in context.selected_objects
                               if o.type == 'MESH']
            if len(selected_meshes) > 1:
                return self._export_per_mesh(
                    context, selected_meshes, backend, is_mobile)

        # ── Single-file paths (legacy behaviour) ─────────────────────
        target = self.filepath
        if self.shared_txd and self.shared_name.strip():
            name = self.shared_name.strip()
            if not name.lower().endswith('.txd'):
                name += '.txd'
            target = os.path.join(os.path.dirname(target), name)

        result, message, _ = export_txd(target, context, sel_only, backend=backend)
        # Mobile target: we still write a PC-format TXD (PVRTC/ETC1
        # codecs aren't shipped). Surface a WARNING so the user knows
        # to run TxdGen for PC → mobile conversion.
        if result == {'FINISHED'} and is_mobile:
            self.report({'WARNING'},
                        T("TXD сохранён в PC формате. Для mobile конвертируй через TxdGen (PVRTC/ETC1)."))
        else:
            self.report({'INFO'} if result == {'FINISHED'} else {'ERROR'}, message)
        return result

    def _export_per_mesh(self, context, selected_meshes, backend, is_mobile):
        """Write one .txd per selected mesh, named after the mesh with
        common suffixes stripped (``_dff``, ``.dff``, ``_LOD``, ``_dam``,
        ``_ok``). Output directory comes from the file dialog. Restores
        the original selection on exit even if encoding fails."""
        import os
        out_dir = os.path.dirname(self.filepath) or '.'
        prev_active = context.view_layer.objects.active
        prev_selected = list(context.selected_objects)

        # Suffixes lowercased once — keep order long-first so `_LOD_dff`
        # gets the longer strip before the shorter token is considered.
        SUFFIXES = ('_lod_dff', '_dam_dff', '_ok_dff',
                    '_dff', '.dff', '_lod', '_dam', '_ok')

        def _basename_for(obj):
            n = obj.name
            ln = n.lower()
            for s in SUFFIXES:
                if ln.endswith(s):
                    return n[:-len(s)]
            return n

        written = []
        errors = []
        try:
            for obj in selected_meshes:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                base = _basename_for(obj)
                txd_path = os.path.join(out_dir, f"{base}.txd")
                try:
                    result, msg, _ = export_txd(
                        txd_path, context, True, backend=backend)
                    if result == {'FINISHED'}:
                        written.append(f"{base}.txd")
                    else:
                        errors.append(f"{base}.txd: {msg}")
                except Exception as e:
                    errors.append(f"{base}.txd: {e}")
        finally:
            bpy.ops.object.select_all(action='DESELECT')
            for o in prev_selected:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if prev_active is not None:
                try:
                    context.view_layer.objects.active = prev_active
                except Exception:
                    pass

        if not written:
            self.report({'ERROR'},
                        f"{T('Не удалось экспортировать ни одного TXD')}: "
                        + "; ".join(errors[:3]))
            return {'CANCELLED'}

        summary = (f"{len(written)} {T('TXD записано в')} {out_dir}"
                   + (f" ({len(errors)} {T('с ошибками')})" if errors else ""))
        self.report({'WARNING'} if (errors or is_mobile) else {'INFO'},
                    summary)
        if is_mobile:
            self.report({'WARNING'},
                        T("TXD сохранён в PC формате. Для mobile конвертируй через TxdGen (PVRTC/ETC1)."))
        return {'FINISHED'}

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
        if result == {'FINISHED'} and getattr(
                context.scene.inu_settings, 'gtatools_platform', 'PC') == 'MOBILE':
            self.report({'WARNING'},
                        T("TXD сохранён в PC формате. Для mobile конвертируй через TxdGen (PVRTC/ETC1)."))
        else:
            self.report({'INFO'} if result == {'FINISHED'} else {'ERROR'}, message)
        return result


classes = (
    GTATOOLS_OT_export_txd,
    GTATOOLS_OT_export_shared_txd,
)
