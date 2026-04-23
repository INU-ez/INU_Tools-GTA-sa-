# INU_tools.tools.map_export — unified scene → IPL + IDE + (optional) DFF / COL / TXD
#
# Orchestrates the individual format exporters so a user can publish a
# whole city district with one click. Per-object IDs, draw distance and
# TXD names are taken from `obj.inu` custom properties (same props that
# back the separate IDE/IPL exports).

from __future__ import annotations

import os
from dataclasses import dataclass

import bpy

from ..tools.model_utils import get_model_type
from .. import T


# ──────────────────────────── grouping ────────────────────────────────

@dataclass
class MapGroup:
    """One DFF → (LOD, COL) group inferred from object naming."""
    base: str
    dff: bpy.types.Object
    lod: bpy.types.Object | None = None
    col_objects: list = None   # list of COL/SHA meshes

    def __post_init__(self):
        if self.col_objects is None:
            self.col_objects = []


def collect_map_groups(objects) -> list[MapGroup]:
    """Walk `objects` and build MapGroup records keyed by base name.

    A group is created for every DFF mesh; any LOD / COL / SHA objects
    sharing that base name are attached to the group.
    """
    dffs: dict[str, bpy.types.Object] = {}
    lods: dict[str, bpy.types.Object] = {}
    cols: dict[str, list] = {}

    for obj in objects:
        if obj.type != 'MESH':
            continue
        mtype, base = get_model_type(obj)
        if not mtype:
            continue
        if mtype == 'DFF':
            dffs.setdefault(base, obj)
        elif mtype == 'LOD':
            lods.setdefault(base, obj)
        elif mtype == 'COL':
            cols.setdefault(base, []).append(obj)

    groups: list[MapGroup] = []
    for base, dff in dffs.items():
        groups.append(MapGroup(
            base=base,
            dff=dff,
            lod=lods.get(base),
            col_objects=cols.get(base, []),
        ))
    return groups


# ──────────────────────────── ID helpers ──────────────────────────────

def _get_or_assign_id(obj, id_pool_start: int, used_ids: set[int]) -> int:
    """Return the object's inu.model_id, allocating a free ID from the
    [`id_pool_start`, 19999] range when the current value is 0.
    """
    inu = getattr(obj, 'inu', None)
    current = int(getattr(inu, 'model_id', 0) or 0) if inu else 0
    if current > 0:
        used_ids.add(current)
        return current
    next_id = id_pool_start
    while next_id in used_ids:
        next_id += 1
    used_ids.add(next_id)
    if inu:
        try:
            inu.model_id = next_id
        except Exception:
            pass
    return next_id


# ──────────────────────────── main export ─────────────────────────────

def export_map(target_dir: str, *, objects=None,
               export_dff: bool = True,
               export_col: bool = True,
               col_library: bool = False,
               export_txd: bool = True,
               export_ipl: bool = True,
               export_ide: bool = True,
               binary_ipl: bool = False,
               id_pool_start: int = 20000,
               base_name: str = "district") -> dict:
    """Emit every format for the given scene objects into `target_dir`.

    Returns a dict with per-format counts: {'dff', 'col', 'txd', 'ide', 'ipl'}.
    """
    os.makedirs(target_dir, exist_ok=True)

    if objects is None:
        objects = list(bpy.context.selected_objects)
        if not objects:
            objects = list(bpy.context.scene.objects)

    groups = collect_map_groups(objects)
    if not groups:
        return {'error': 'no DFF meshes found in selection'}

    used_ids: set[int] = set()
    for g in groups:
        _get_or_assign_id(g.dff, id_pool_start, used_ids)

    stats = {'dff': 0, 'col': 0, 'txd': 0, 'ide': 0, 'ipl': 0}

    # Per-group DFF + COL
    if export_dff:
        from ..ops.dff_export import export_dff as _export_dff
        for g in groups:
            dff_path = os.path.join(target_dir, f"{g.base}.dff")
            group_objs = [g.dff]
            if g.lod:
                group_objs.append(g.lod)
            group_objs.extend(g.col_objects)
            try:
                _export_dff(dff_path, group_objs)
                stats['dff'] += 1
            except Exception as e:
                print(f"[map_export] DFF {g.base} failed: {e}")

    if export_col and any(g.col_objects for g in groups):
        if col_library:
            # One multi-entry .col named after the district (base_name).
            from ..ops.col_export import export_col_library
            lib_path = os.path.join(target_dir, f"{base_name}.col")
            all_col_objs = []
            for g in groups:
                all_col_objs.extend(g.col_objects)
            try:
                count = export_col_library(lib_path, all_col_objs)
                stats['col'] = count
            except Exception as e:
                print(f"[map_export] COL library failed: {e}")
        else:
            from ..ops.col_export import export_col
            for g in groups:
                if not g.col_objects:
                    continue
                col_path = os.path.join(target_dir, f"{g.base}.col")
                try:
                    export_col(col_path, g.col_objects)
                    stats['col'] += 1
                except Exception as e:
                    print(f"[map_export] COL {g.base} failed: {e}")

    # Shared TXD per district (all textures from all DFFs merged)
    if export_txd:
        from ..tools.txd_export import export_txd as _export_txd
        txd_path = os.path.join(target_dir, f"{base_name}.txd")
        # Ensure Object mode — select_all and select_set need it.
        if bpy.context.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass
        prev_selection = [o for o in bpy.context.selected_objects]
        prev_active = bpy.context.view_layer.objects.active
        try:
            for o in prev_selection:
                try:
                    o.select_set(False)
                except Exception:
                    pass
            for g in groups:
                if g.dff:
                    g.dff.select_set(True)
            if groups and groups[0].dff:
                bpy.context.view_layer.objects.active = groups[0].dff
            _export_txd(txd_path, bpy.context, selected_only=True)
            stats['txd'] += 1
        except Exception as e:
            print(f"[map_export] TXD failed: {e}")
        finally:
            for g in groups:
                if g.dff:
                    try:
                        g.dff.select_set(False)
                    except Exception:
                        pass
            for o in prev_selection:
                try:
                    o.select_set(True)
                except Exception:
                    pass
            if prev_active:
                try:
                    bpy.context.view_layer.objects.active = prev_active
                except Exception:
                    pass

    # IDE
    if export_ide:
        from ..ops.ide_export import export_ide as _export_ide
        ide_path = os.path.join(target_dir, f"{base_name}.ide")
        ide_objs = [g.dff for g in groups]
        try:
            _export_ide(ide_path, ide_objs)
            stats['ide'] += 1
        except Exception as e:
            print(f"[map_export] IDE failed: {e}")

    # IPL
    if export_ipl:
        from ..ops.ipl_export import export_ipl as _export_ipl
        ipl_path = os.path.join(target_dir, f"{base_name}.ipl")
        ipl_objs = [g.dff for g in groups]
        try:
            _export_ipl(ipl_path, ipl_objs, binary=binary_ipl)
            stats['ipl'] += 1
        except Exception as e:
            print(f"[map_export] IPL failed: {e}")

    stats['groups'] = len(groups)
    return stats


# ──────────────────────────── operator + panel ───────────────────────

class GTATOOLS_OT_map_export(bpy.types.Operator):
    """Экспортировать выделение как готовый район GTA SA (DFF + COL + TXD + IDE + IPL в одну папку)"""
    bl_idname = "gtatools.map_export"
    bl_label = "Export Map…"
    bl_options = {'REGISTER'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    base_name: bpy.props.StringProperty(name="Base Name", default="district")
    include_dff: bpy.props.BoolProperty(name="DFF", default=True)
    include_col: bpy.props.BoolProperty(name="COL", default=True)
    col_library: bpy.props.BoolProperty(
        name=T("COL Library"),
        description=T("Писать все коллизии в один <district>.col файл (multi-entry library). Каждая запись в файле — отдельная коллизия со своим model_id, сопоставляется с DFF по ID"),
        default=True,
    )
    include_txd: bpy.props.BoolProperty(name="TXD", default=True)
    include_ide: bpy.props.BoolProperty(name="IDE", default=True)
    include_ipl: bpy.props.BoolProperty(name="IPL", default=True)
    binary_ipl: bpy.props.BoolProperty(name="Binary IPL", default=False)
    id_pool_start: bpy.props.IntProperty(
        name="ID Pool Start", default=20000, min=1, max=32000,
        description=T("Первый ID для DFF у которых inu.model_id == 0"),
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.directory or not os.path.isdir(self.directory):
            self.report({'ERROR'}, "Pick a target folder")
            return {'CANCELLED'}

        selected = [o for o in context.selected_objects if o.type == 'MESH']
        if not selected:
            selected = [o for o in context.scene.objects if o.type == 'MESH']

        stats = export_map(
            self.directory,
            objects=selected,
            export_dff=self.include_dff,
            export_col=self.include_col,
            col_library=self.col_library,
            export_txd=self.include_txd,
            export_ide=self.include_ide,
            export_ipl=self.include_ipl,
            binary_ipl=self.binary_ipl,
            id_pool_start=self.id_pool_start,
            base_name=self.base_name,
        )
        if 'error' in stats:
            self.report({'ERROR'}, stats['error'])
            return {'CANCELLED'}
        msg = (f"{stats['groups']} group(s) → "
               f"{stats['dff']} DFF, {stats['col']} COL, "
               f"{stats['txd']} TXD, {stats['ide']} IDE, {stats['ipl']} IPL")
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_PT_map_export_panel(bpy.types.Panel):
    bl_label = "Map Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.operator("gtatools.map_export", icon='WORLD')


classes = (
    GTATOOLS_OT_map_export,
    GTATOOLS_PT_map_export_panel,
)
