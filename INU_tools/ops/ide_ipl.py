# INU_tools.ops.ide_ipl — IDE / IPL panel operators.
#
# Phase 3 batch 4 (2026-04-26): 11 operators moved from __init__.py.
# Three small helpers (_ide_entry_from_obj, _ipl_entry_from_obj,
# _clean_model_name_ide) stay in __init__.py because INU Import/Export
# and other ops still use them; this module pulls them in lazily.

import os
import bpy
from bpy.props import (
    BoolProperty, StringProperty,
)
from .. import T


class GTATOOLS_OT_upsert_ide(bpy.types.Operator):
    """Добавить / обновить запись в существующем IDE файле (авто-LOD)"""
    bl_idname = "gtatools.upsert_ide"
    bl_label = "INU: Add to IDE"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ide import upsert_ide
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ide_path)
        if not filepath:
            self.report({'ERROR'}, T("Укажите путь к IDE файлу"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        entries = []
        processed_names = set()
        for obj in objs:
            from ..tools.model_utils import get_model_type
            model_type, base_name = get_model_type(obj)
            if base_name in processed_names:
                continue
            processed_names.add(base_name)

            # Add DFF entry
            dff_obj = obj if model_type == 'DFF' else None
            lod_obj = obj if model_type == 'LOD' else None

            # Auto-find paired LOD/DFF among selected
            for o2 in objs:
                mt2, bn2 = get_model_type(o2)
                if bn2 == base_name and o2 != obj:
                    if mt2 == 'LOD':
                        lod_obj = o2
                    elif mt2 == 'DFF':
                        dff_obj = o2

            if dff_obj:
                from .. import _ide_entry_from_obj
                entries.append(_ide_entry_from_obj(dff_obj))
            if lod_obj:
                lod_entry = _ide_entry_from_obj(lod_obj)
                # LOD model name: LOD + base_name
                lod_entry.model_name = "LOD" + base_name
                # LOD TXD = same as DFF TXD (base_name without suffixes)
                from .. import _clean_model_name_ide
                lod_entry.txd_name = _clean_model_name_ide(base_name)
                # LOD model_id = DFF model_id + 1 if LOD has no ID
                if lod_entry.model_id == 0 and dff_obj:
                    dff_id = getattr(dff_obj.inu, 'model_id', 0)
                    if dff_id > 0:
                        lod_entry.model_id = dff_id + 1
                # LOD draw distance from DFF's lod_draw_distance property
                if dff_obj:
                    lod_entry.draw_distance = dff_obj.inu.lod_draw_distance
                elif lod_obj.inu.draw_distance in (299.0, 300.0):
                    lod_entry.draw_distance = 999.0
                entries.append(lod_entry)

        # Validate model IDs
        zero_ids = [e for e in entries if e.model_id == 0]
        if zero_ids:
            self.report({'WARNING'}, f"{len(zero_ids)} {T('объектов с Model ID = 0, задайте ID в свойствах')}")

        updated, added = upsert_ide(filepath, entries)

        # ── Record last-exported state for drift detection ──
        # After a successful upsert, stamp every selected obj with the
        # fields it just sent to IDE.  The N-panel uses these to show
        # a "В IDE / координаты разошлись / Не в IDE" status, and the
        # Sync operator uses them to pull file→Blender.
        for obj in objs:
            inu = getattr(obj, 'inu', None)
            if inu is None or inu.model_id <= 0:
                continue
            inu.ide_target_file = filepath
            inu.ide_last_draw_distance = inu.draw_distance
            inu.ide_last_txd_name = inu.txd_name
            inu.ide_last_flags = inu.ide_flags
            inu.ide_linked = True

        self.report({'INFO'}, f"IDE: {T('обновлено')} {updated}, {T('добавлено')} {added}")
        return {'FINISHED'}


class GTATOOLS_OT_upsert_ipl(bpy.types.Operator):
    """Добавить / обновить запись в существующем IPL файле (авто-LOD привязка + tracking перемещений)"""
    bl_idname = "gtatools.upsert_ipl"
    bl_label = "INU: Add to IPL"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ipl import upsert_ipl, read_ipl, write_ipl
        from ..core import ipl_links as iplinks
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ipl_path)
        if not filepath:
            self.report({'ERROR'}, T("Укажите путь к IPL файлу"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        # ── IPL link tracking: sidecar lookup ──
        # The sidecar (one JSON next to .blend in .inu_cache/) maps
        # per-object UUIDs to ``(line_idx, model_id, last_pos)`` so
        # repeated ``Add to IPL`` of a moved object overwrites its
        # existing row instead of appending a duplicate.  When the
        # IPL was edited externally the hash mismatches and we
        # fall back to content-match (model_id + last_pos within 0.5 m).
        blend_path = bpy.data.filepath
        sidecar = iplinks.load_sidecar(blend_path)
        file_links = sidecar.file_links(filepath, create=True)

        # Read existing IPL once — needed both for upsert math and for
        # the reconcile pass below.
        try:
            existing_ipl = read_ipl(filepath) if os.path.isfile(filepath) else None
        except Exception:
            existing_ipl = None

        if existing_ipl is not None:
            current_hash = iplinks.hash_ipl_file(filepath)
            if file_links.ipl_hash and file_links.ipl_hash != current_hash:
                # External edit detected — re-validate every link.
                repaired, removed = iplinks.reconcile_file_links(
                    file_links, existing_ipl, current_hash)
                if repaired or removed:
                    self.report({'INFO'},
                                T("IPL правили извне: {0} ссылок исправлено, {1} удалено").format(
                                    repaired, len(removed)))
            elif not file_links.ipl_hash:
                file_links.ipl_hash = current_hash

        # De-dupe selection by Blender object identity — Ctrl+D'd
        # duplicates may inherit a parent's uuid; we mint a new one for
        # any object that shares a uuid already claimed in this batch.
        seen_uuids = set()
        for o in objs:
            u = o.inu.ipl_uuid
            if u and u in seen_uuids:
                o.inu.ipl_uuid = iplinks.new_uuid()
            elif u:
                seen_uuids.add(u)

        # ── UUID-aware upsert ──
        # Three branches per object:
        #   1. No uuid yet → mint one, APPEND to IPL, record link
        #   2. uuid in sidecar + line_idx still valid → UPDATE that row
        #      (regardless of whether the object's transform changed —
        #      `Add to IPL` always pushes Blender state to the file)
        #   3. uuid present but link lost → content-match
        #      (model_id + ipl_last_pos within 0.5 m); on hit UPDATE,
        #      on miss APPEND as new placement
        from ..tools.model_utils import get_model_type
        from .. import _ipl_entry_from_obj

        if existing_ipl is None:
            from ..core.ipl import IplFile
            existing_ipl = IplFile()

        # Pre-pass: separate DFFs from LODs and group LODs by base
        # name so a single LOD entry can be referenced by many DFF
        # placements (vanilla R* pattern).
        lod_per_base = {}     # base_name → LOD obj
        dff_objs = []
        for obj in objs:
            mt, base = get_model_type(obj)
            if mt == 'LOD':
                lod_per_base[base] = obj
            else:
                dff_objs.append((obj, base))

        # ── LOD entries: upsert each base's LOD first, remember idx ──
        # The LOD entry needs to be findable to fill ``lod_index`` on
        # its DFF siblings.  We upsert LODs with the same uuid-track
        # logic.
        lod_idx_per_base = {}
        updated = 0
        added = 0

        def _upsert_entry(obj, build_fn):
            """Returns (final_line_idx, was_update_or_append)."""
            nonlocal updated, added
            entry = build_fn(obj)
            uuid = obj.inu.ipl_uuid
            link_rec = file_links.links.get(uuid) if uuid else None

            # Branch 2: known link, still valid?
            if (link_rec
                    and 0 <= link_rec.line_idx < len(existing_ipl.instances)):
                existing_ipl.instances[link_rec.line_idx] = entry
                link_rec.line_idx = link_rec.line_idx  # unchanged
                link_rec.model_id = entry.model_id
                link_rec.model_name = entry.model_name
                link_rec.last_pos = (entry.pos_x, entry.pos_y, entry.pos_z)
                _record_last_state(obj, entry)
                updated += 1
                return link_rec.line_idx

            # Branch 3: uuid known, line lost → content-match
            if uuid and any(obj.inu.ipl_last_pos):
                idx = iplinks.find_inst_by_content(
                    existing_ipl,
                    obj.inu.ipl_last_model_id or entry.model_id,
                    tuple(obj.inu.ipl_last_pos))
                if idx >= 0:
                    existing_ipl.instances[idx] = entry
                    file_links.links[uuid] = iplinks.IplLinkRecord(
                        idx, entry.model_id, entry.model_name,
                        (entry.pos_x, entry.pos_y, entry.pos_z))
                    _record_last_state(obj, entry)
                    updated += 1
                    return idx

            # Branch 1: APPEND
            if not uuid:
                uuid = iplinks.new_uuid()
                obj.inu.ipl_uuid = uuid
            existing_ipl.instances.append(entry)
            idx = len(existing_ipl.instances) - 1
            file_links.links[uuid] = iplinks.IplLinkRecord(
                idx, entry.model_id, entry.model_name,
                (entry.pos_x, entry.pos_y, entry.pos_z))
            _record_last_state(obj, entry)
            added += 1
            return idx

        def _record_last_state(obj, entry):
            obj.inu.ipl_last_pos = (entry.pos_x, entry.pos_y, entry.pos_z)
            obj.inu.ipl_last_rot = (entry.rot_x, entry.rot_y,
                                    entry.rot_z, entry.rot_w)
            obj.inu.ipl_last_model_id = entry.model_id
            obj.inu.ipl_target_file = filepath

        # Build LOD entries first.
        def _lod_builder(lod_obj):
            mt, base = get_model_type(lod_obj)
            e = _ipl_entry_from_obj(lod_obj)
            e.model_name = "LOD" + base
            e.lod_index = -1
            # Auto-assign LOD model_id from first DFF sibling + 1.
            if e.model_id == 0:
                for dff_obj, dff_base in dff_objs:
                    if dff_base == base:
                        dff_id = getattr(dff_obj.inu, 'model_id', 0)
                        if dff_id > 0:
                            e.model_id = dff_id + 1
                            break
            return e

        for base, lod_obj in lod_per_base.items():
            lod_idx = _upsert_entry(lod_obj, _lod_builder)
            lod_idx_per_base[base] = lod_idx

        # DFF entries — assign lod_index after both rows exist.
        def _dff_builder(o):
            e = _ipl_entry_from_obj(o)
            _, base = get_model_type(o)
            li = lod_idx_per_base.get(base, -1)
            e.lod_index = li
            return e

        for dff_obj, base in dff_objs:
            dff_idx = _upsert_entry(dff_obj, _dff_builder)
            # Mirror lod_index onto the object's inu prop so subsequent
            # IPL exports (text-only path) stay in sync.
            dff_obj.inu.lod_index = lod_idx_per_base.get(base, -1)

        # Write IPL + sidecar.
        try:
            write_ipl(filepath, existing_ipl, game=_get_scene_game(context))
        except TypeError:
            # write_ipl signature without ``game`` kwarg — fall back.
            write_ipl(filepath, existing_ipl)
        file_links.ipl_hash = iplinks.hash_ipl_file(filepath)
        iplinks.save_sidecar(blend_path, sidecar)

        zero_ids = [o for o, _ in dff_objs if o.inu.model_id == 0]
        if zero_ids:
            self.report({'WARNING'},
                        f"{len(zero_ids)} {T('объектов с Model ID = 0, задайте ID в свойствах')}")
        self.report({'INFO'},
                    f"IPL: {T('обновлено')} {updated}, {T('добавлено')} {added}")
        return {'FINISHED'}


def _get_scene_game(context):
    try:
        from ..core import game_versions as gv
        return gv.game_of_scene(context.scene)
    except Exception:
        return 'SA'


# ── IPL link tracking operators ────────────────────────────────────


class GTATOOLS_OT_ipl_sync_from_file(bpy.types.Operator):
    """Синхронизация Blender ↔ IPL.

    Bi-directional:
      • Если у объекта НЕТ uuid и его (model_id + позиция) совпадает с
        какой-то строкой IPL — линкует: генерирует uuid, регистрирует в
        sidecar. Это автолинковка после Map Import.
      • Если у объекта uuid есть — подтягивает позицию ИЗ IPL в Blender
        (после внешней правки файла).

    Работает по выделению (или по всем mesh-объектам если selection пуст).
    """
    bl_idname = "gtatools.ipl_sync_from_file"
    bl_label = "INU: Sync from IPL"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..core.ipl import read_ipl
        from ..core import ipl_links as iplinks
        from mathutils import Quaternion
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ipl_path)
        if not filepath or not os.path.isfile(filepath):
            self.report({'ERROR'}, T("IPL файл не найден"))
            return {'CANCELLED'}

        blend_path = bpy.data.filepath
        sidecar = iplinks.load_sidecar(blend_path)
        file_links = sidecar.file_links(filepath, create=True)

        ipl = read_ipl(filepath)
        # Reconcile in case the IPL has been edited externally.
        current_hash = iplinks.hash_ipl_file(filepath)
        if file_links.ipl_hash and current_hash != file_links.ipl_hash:
            iplinks.reconcile_file_links(file_links, ipl, current_hash)
        elif not file_links.ipl_hash:
            file_links.ipl_hash = current_hash

        # Selection scope — if user has objects selected, work on those;
        # otherwise sweep every mesh in the scene.  Importing a 383-obj
        # map then clicking Sync with nothing selected should still
        # link everything.
        sel = [o for o in context.selected_objects if o.type == 'MESH']
        if not sel:
            sel = [o for o in bpy.data.objects if o.type == 'MESH']

        # ── Garbage-collect orphan sidecar entries ──
        # A previous Sync / Add might have left uuid→line records that
        # no longer correspond to any Blender object (file reopened,
        # objects deleted, undo).  Keeping them blocks fresh
        # content-match: an unused line shows as "occupied" by a ghost
        # uuid, so a new attempt to link a matching object skips it.
        # Drop these before computing the occupied set so only LIVE
        # links count as occupied territory.
        live_uuids = set()
        for o in bpy.data.objects:
            if o.type != 'MESH':
                continue
            u = getattr(o.inu, 'ipl_uuid', '')
            if u:
                live_uuids.add(u)
        orphans_dropped = 0
        for u in list(file_links.links.keys()):
            if u not in live_uuids:
                del file_links.links[u]
                orphans_dropped += 1
        if orphans_dropped:
            print(f"[IPL Sync] dropped {orphans_dropped} orphan sidecar links")

        # Index occupied IPL line indices — only LIVE uuids count.
        occupied = {rec.line_idx for rec in file_links.links.values()}

        linked = 0   # objects without uuid that just got linked
        synced = 0   # objects with uuid whose pos was pulled from IPL
        skipped = 0  # objects we couldn't find any matching row for
        # Per-reason skip counters so the user can see *why* the match
        # failed.  Printed to the system console at the end and also
        # surfaced in the operator report when non-trivial.
        skip_reasons = {'no_model_id': 0, 'no_match': 0,
                        'occupied': 0, 'line_lost': 0}
        debug_samples = []

        for obj in sel:
            uuid = getattr(obj.inu, 'ipl_uuid', '')

            # Branch B: already linked → pull position from IPL.
            if uuid and uuid in file_links.links:
                rec = file_links.links[uuid]
                if not (0 <= rec.line_idx < len(ipl.instances)):
                    skip_reasons['line_lost'] += 1
                    continue
                inst = ipl.instances[rec.line_idx]
                obj.location = (inst.pos_x, inst.pos_y, inst.pos_z)
                q = Quaternion((inst.rot_w, -inst.rot_x, -inst.rot_y, -inst.rot_z))
                obj.rotation_mode = 'QUATERNION'
                obj.rotation_quaternion = q
                obj.inu.ipl_last_pos = (inst.pos_x, inst.pos_y, inst.pos_z)
                obj.inu.ipl_last_rot = (inst.rot_x, inst.rot_y, inst.rot_z, inst.rot_w)
                obj.inu.ipl_last_model_id = inst.model_id
                obj.inu.ipl_target_file = filepath
                rec.last_pos = (inst.pos_x, inst.pos_y, inst.pos_z)
                synced += 1
                continue

            # Branch A: no uuid → content-match by (model_id, world pos).
            model_id = getattr(obj.inu, 'model_id', 0)
            if model_id <= 0:
                skipped += 1
                skip_reasons['no_model_id'] += 1
                if len(debug_samples) < 5:
                    debug_samples.append(
                        f"  {obj.name!r}: model_id=0 (Map Import не выставил ID — "
                        f"проверь Object Properties → INU Tools → Model ID)")
                continue
            world_pos = obj.matrix_world.translation
            idx = iplinks.find_inst_by_content(
                ipl, model_id,
                (world_pos.x, world_pos.y, world_pos.z))
            if idx < 0:
                skipped += 1
                skip_reasons['no_match'] += 1
                if len(debug_samples) < 5:
                    # Show closest same-id row in the IPL for diagnosis.
                    nearest = None
                    nearest_d = float('inf')
                    for i, inst in enumerate(ipl.instances):
                        if int(getattr(inst, 'model_id', -1)) != int(model_id):
                            continue
                        d2 = ((inst.pos_x - world_pos.x) ** 2
                              + (inst.pos_y - world_pos.y) ** 2
                              + (inst.pos_z - world_pos.z) ** 2)
                        if d2 < nearest_d:
                            nearest_d = d2
                            nearest = inst
                    if nearest is not None:
                        debug_samples.append(
                            f"  {obj.name!r}: model_id={model_id}, "
                            f"pos=({world_pos.x:.3f},{world_pos.y:.3f},{world_pos.z:.3f}); "
                            f"ближайшая IPL-строка с тем же ID на расстоянии "
                            f"{nearest_d ** 0.5:.3f} m: "
                            f"({nearest.pos_x:.3f},{nearest.pos_y:.3f},{nearest.pos_z:.3f})")
                    else:
                        debug_samples.append(
                            f"  {obj.name!r}: model_id={model_id} ОТСУТСТВУЕТ в IPL "
                            f"(в файле нет ни одной строки с этим ID)")
                continue
            if idx in occupied:
                skipped += 1
                skip_reasons['occupied'] += 1
                continue
            inst = ipl.instances[idx]
            new_uuid = iplinks.new_uuid()
            obj.inu.ipl_uuid = new_uuid
            obj.inu.ipl_last_pos = (inst.pos_x, inst.pos_y, inst.pos_z)
            obj.inu.ipl_last_rot = (inst.rot_x, inst.rot_y, inst.rot_z, inst.rot_w)
            obj.inu.ipl_last_model_id = inst.model_id
            obj.inu.ipl_target_file = filepath
            file_links.links[new_uuid] = iplinks.IplLinkRecord(
                idx, inst.model_id, inst.model_name,
                (inst.pos_x, inst.pos_y, inst.pos_z))
            occupied.add(idx)
            linked += 1

        iplinks.save_sidecar(blend_path, sidecar)

        # Console diagnostics — surfaced when skipped > 0 so the user
        # can see why content-match failed without opening a debugger.
        if skipped > 0:
            print("[IPL Sync] skipped breakdown:")
            print(f"  no_model_id : {skip_reasons['no_model_id']}")
            print(f"  no_match    : {skip_reasons['no_match']}")
            print(f"  occupied    : {skip_reasons['occupied']}")
            print(f"  line_lost   : {skip_reasons['line_lost']}")
            print(f"  IPL: {filepath}  (instances: {len(ipl.instances)})")
            if debug_samples:
                print("[IPL Sync] sample skips:")
                for s in debug_samples:
                    print(s)

        # Build user-facing report; lead with the dominant skip reason
        # so the fix path is obvious from one line.
        msg = T("Sync: linked {0}, обновлено {1}, пропущено {2}").format(
            linked, synced, skipped)
        if skipped and skip_reasons['no_model_id'] == skipped:
            msg += " — " + T("все без Model ID")
        elif skipped and skip_reasons['no_match'] == skipped:
            msg += " — " + T("ни одного совпадения по (model_id+pos) в этом IPL")
        elif skipped and skip_reasons['occupied'] == skipped:
            msg += " — " + T("все целевые строки уже заняты другими объектами")
        GTATOOLS_OT_ipl_sync_from_file.last_message = msg
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_ipl_remove_link(bpy.types.Operator):
    """Удалить выделенные объекты из IPL и очистить ссылки.
    Объекты остаются в Blender, но их inst-строки удаляются из IPL,
    line_idx остальных пересчитываются."""
    bl_idname = "gtatools.ipl_remove_link"
    bl_label = "INU: Remove from IPL"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ipl import read_ipl, write_ipl
        from ..core import ipl_links as iplinks
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ipl_path)
        if not filepath or not os.path.isfile(filepath):
            self.report({'ERROR'}, T("IPL файл не найден"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects
                if o.type == 'MESH' and o.inu.ipl_uuid]
        if not objs:
            self.report({'ERROR'}, T("Выделите объекты с привязкой к IPL"))
            return {'CANCELLED'}

        blend_path = bpy.data.filepath
        sidecar = iplinks.load_sidecar(blend_path)
        file_links = sidecar.file_links(filepath, create=False)
        if file_links is None:
            self.report({'INFO'}, T("Нет связанных объектов для этого IPL"))
            return {'CANCELLED'}

        ipl = read_ipl(filepath)
        current_hash = iplinks.hash_ipl_file(filepath)
        if current_hash != file_links.ipl_hash:
            iplinks.reconcile_file_links(file_links, ipl, current_hash)

        # Collect indices to drop (descending so deletion preserves
        # remaining indices of links we keep).
        drop_idx = set()
        cleared_uuids = []
        for o in objs:
            u = o.inu.ipl_uuid
            rec = file_links.links.get(u)
            if rec is None:
                continue
            if 0 <= rec.line_idx < len(ipl.instances):
                drop_idx.add(rec.line_idx)
            cleared_uuids.append(u)

        if not drop_idx:
            self.report({'INFO'}, T("Не найдено записей для удаления"))
            return {'CANCELLED'}

        # Build remap old_idx → new_idx for survivors.
        survivors = [i for i in range(len(ipl.instances)) if i not in drop_idx]
        remap = {old: new for new, old in enumerate(survivors)}
        ipl.instances = [ipl.instances[i] for i in survivors]
        # Patch lod_index pointers — they reference inst positions in
        # the same IPL; surviving rows pointing at a dropped index lose
        # their LOD link.
        for inst in ipl.instances:
            if inst.lod_index >= 0:
                inst.lod_index = remap.get(inst.lod_index, -1)
        # Update sidecar link records for survivors.
        for u, rec in list(file_links.links.items()):
            if u in cleared_uuids:
                del file_links.links[u]
                continue
            rec.line_idx = remap.get(rec.line_idx, -1)
            if rec.line_idx < 0:
                del file_links.links[u]

        try:
            write_ipl(filepath, ipl, game=_get_scene_game(context))
        except TypeError:
            write_ipl(filepath, ipl)
        file_links.ipl_hash = iplinks.hash_ipl_file(filepath)
        iplinks.save_sidecar(blend_path, sidecar)

        # Clear per-object link state.
        for o in objs:
            o.inu.ipl_uuid = ""
            o.inu.ipl_target_file = ""
            o.inu.ipl_last_pos = (0.0, 0.0, 0.0)
            o.inu.ipl_last_rot = (0.0, 0.0, 0.0, 1.0)
            o.inu.ipl_last_model_id = 0

        msg = T("Удалено из IPL: {0}, осталось записей: {1}").format(
            len(drop_idx), len(ipl.instances))
        GTATOOLS_OT_ipl_remove_link.last_message = msg
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_ipl_verify_links(bpy.types.Operator):
    """Проверить все ссылки sidecar'а на валидность. Сообщает orphan'ы
    (uuid в sidecar, объект удалён из Blender) и broken links
    (line_idx за пределами IPL или content не совпадает)."""
    bl_idname = "gtatools.ipl_verify_links"
    bl_label = "INU: Verify IPL Links"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ipl import read_ipl
        from ..core import ipl_links as iplinks
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ipl_path)
        if not filepath or not os.path.isfile(filepath):
            self.report({'ERROR'}, T("IPL файл не найден"))
            return {'CANCELLED'}

        blend_path = bpy.data.filepath
        sidecar = iplinks.load_sidecar(blend_path)
        file_links = sidecar.file_links(filepath, create=False)
        if file_links is None or not file_links.links:
            self.report({'INFO'}, T("Нет связанных объектов для этого IPL"))
            return {'CANCELLED'}

        ipl = read_ipl(filepath)
        current_hash = iplinks.hash_ipl_file(filepath)
        repaired, removed = iplinks.reconcile_file_links(
            file_links, ipl, current_hash)

        # Find orphans: uuids in sidecar with no matching Blender object.
        uuid_to_obj = {o.inu.ipl_uuid for o in bpy.data.objects
                       if o.type == 'MESH' and getattr(o.inu, 'ipl_uuid', '')}
        orphans = [u for u in file_links.links if u not in uuid_to_obj]

        iplinks.save_sidecar(blend_path, sidecar)
        msg = T("Проверка: {0} ссылок ОК, {1} исправлено, {2} удалено, {3} orphan").format(
            len(file_links.links) - len(orphans),
            repaired, len(removed), len(orphans))
        GTATOOLS_OT_ipl_verify_links.last_message = msg
        self.report({'INFO'}, msg)
        return {'FINISHED'}


# Wrapper-friendly message stash.  When an inner operator (ide_sync,
# ipl_sync, …) runs inside ``link_sync`` via ``bpy.ops`` + temp_override,
# Blender's status bar shows only the OUTER operator's last report —
# the inner ``self.report({'INFO'}, ...)`` becomes invisible.  The
# inner ops mirror their final message onto ``last_message`` so the
# wrapper can read it post-call and re-emit it as its own report.
# Naming: ``<OperatorClassName>.last_message`` — accessed directly,
# no helper.  ClassVar in spirit; not annotated to keep PropertyGroup
# scanners from picking it up.

class GTATOOLS_OT_ide_sync_from_file(bpy.types.Operator):
    """Синхронизация Blender ↔ IDE.

    Bi-directional, аналогично Sync для IPL:
      • Если model_id объекта найден в IDE → подтягивает draw_distance,
        txd_name, flags из IDE в obj.inu props.  Это автолинковка после
        Map Import и кейс пост-внешней-правки IDE.
      • Если model_id не найден → пропускает (записи нет, нечего тянуть).

    Работает по выделению; пустое выделение = всё meshes сцены.
    """
    bl_idname = "gtatools.ide_sync_from_file"
    bl_label = "INU: Sync from IDE"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..core.ide import read_ide
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ide_path)
        if not filepath or not os.path.isfile(filepath):
            self.report({'ERROR'}, T("IDE файл не найден"))
            return {'CANCELLED'}

        ide = read_ide(filepath)
        # Build a single (model_id → entry) lookup over both objs and
        # anims sections — IDE.anims share the same id-space as
        # IDE.objects.
        by_id = {}
        for e in ide.objects:
            by_id[int(e.model_id)] = e
        for e in ide.anims:
            by_id.setdefault(int(e.model_id), e)

        sel = [o for o in context.selected_objects if o.type == 'MESH']
        if not sel:
            sel = [o for o in bpy.data.objects if o.type == 'MESH']

        linked = 0
        skipped = 0
        skip_reasons = {'no_model_id': 0, 'not_in_ide': 0}
        for obj in sel:
            inu = getattr(obj, 'inu', None)
            if inu is None:
                skipped += 1
                continue
            mid = int(inu.model_id) if inu.model_id else 0
            if mid <= 0:
                skipped += 1
                skip_reasons['no_model_id'] += 1
                continue
            entry = by_id.get(mid)
            if entry is None:
                skipped += 1
                skip_reasons['not_in_ide'] += 1
                continue
            # Pull file → Blender.
            inu.draw_distance = float(getattr(entry, 'draw_distance', 0.0))
            inu.txd_name = str(getattr(entry, 'txd_name', '') or '')
            inu.ide_flags = int(getattr(entry, 'flags', 0))
            inu.ide_target_file = filepath
            inu.ide_last_draw_distance = inu.draw_distance
            inu.ide_last_txd_name = inu.txd_name
            inu.ide_last_flags = inu.ide_flags
            inu.ide_linked = True
            linked += 1

        if skipped:
            print(f"[IDE Sync] skipped: no_model_id={skip_reasons['no_model_id']}, "
                  f"not_in_ide={skip_reasons['not_in_ide']}")
        msg = T("Sync IDE: linked {0}, пропущено {1}").format(linked, skipped)
        GTATOOLS_OT_ide_sync_from_file.last_message = msg
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_ide_remove_link(bpy.types.Operator):
    """Удалить выделенные объекты из IDE и очистить tracking-поля.
    Объекты остаются в Blender, но их записи в IDE удаляются по model_id."""
    bl_idname = "gtatools.ide_remove_link"
    bl_label = "INU: Unlink from IDE"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ide import remove_ide
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ide_path)
        if not filepath or not os.path.isfile(filepath):
            self.report({'ERROR'}, T("IDE файл не найден"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects
                if o.type == 'MESH' and getattr(o.inu, 'model_id', 0) > 0]
        if not objs:
            self.report({'ERROR'}, T("Выделите объекты с Model ID > 0"))
            return {'CANCELLED'}

        model_ids = set()
        for o in objs:
            model_ids.add(int(o.inu.model_id))
            # Also drop the auto-paired LOD id (DFF+1) if user linked
            # via Add to IDE; this mirrors the LOD-pair behaviour there.
            if o.inu.ide_linked:
                model_ids.add(int(o.inu.model_id) + 1)

        removed = remove_ide(filepath, list(model_ids))

        # Clear per-object IDE link state.
        for o in objs:
            o.inu.ide_target_file = ""
            o.inu.ide_last_draw_distance = 0.0
            o.inu.ide_last_txd_name = ""
            o.inu.ide_last_flags = 0
            o.inu.ide_linked = False

        msg = T("IDE: удалено {0} записей").format(removed)
        GTATOOLS_OT_ide_remove_link.last_message = msg
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_ide_verify_links(bpy.types.Operator):
    """Проверить, что model_id всех выделенных объектов есть в IDE.
    Сообщает: present (есть), missing (нет), zero_id (Model ID не задан)."""
    bl_idname = "gtatools.ide_verify_links"
    bl_label = "INU: Verify IDE Links"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ide import read_ide
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ide_path)
        if not filepath or not os.path.isfile(filepath):
            self.report({'ERROR'}, T("IDE файл не найден"))
            return {'CANCELLED'}

        ide = read_ide(filepath)
        ide_ids = set()
        for e in ide.objects:
            ide_ids.add(int(e.model_id))
        for e in ide.anims:
            ide_ids.add(int(e.model_id))

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            objs = [o for o in bpy.data.objects if o.type == 'MESH']

        present = 0
        missing = 0
        zero_id = 0
        missing_samples = []
        for o in objs:
            mid = int(getattr(o.inu, 'model_id', 0) or 0)
            if mid <= 0:
                zero_id += 1
                continue
            if mid in ide_ids:
                present += 1
            else:
                missing += 1
                if len(missing_samples) < 5:
                    missing_samples.append(f"{o.name!r} (id={mid})")

        if missing_samples:
            print("[IDE Verify] missing sample:")
            for s in missing_samples:
                print(f"  {s}")
        msg = T("IDE Verify: present {0}, missing {1}, zero_id {2}").format(
            present, missing, zero_id)
        GTATOOLS_OT_ide_verify_links.last_message = msg
        self.report({'INFO'}, msg)
        return {'FINISHED'}


def _run_with_override(context, op_callable):
    """Invoke ``op_callable`` via ``bpy.ops`` with the wrapper's live
    context explicitly forwarded.

    Wrappers (link_sync / link_unlink / link_verify) are invoked from
    the floater through ``bpy.app.timers``.  The timer callback runs
    on an idle tick — by then Blender's ``context`` for ``bpy.ops``
    has been reset to a stripped-down "background" form that no
    longer exposes ``selected_objects`` / ``active_object``.  Nested
    ``bpy.ops.x.y('EXEC_DEFAULT')`` from inside our wrapper's
    ``execute()`` inherits THAT stripped context and silently does
    nothing.

    ``context.temp_override(**state)`` (Blender 3.2+) tells the
    bpy.ops dispatcher to use the supplied attributes for the
    duration of the nested call.  We forward the scene-level prop
    bag, the selection, and the active object — enough for any
    operator that reads ``context.selected_objects`` or
    ``context.scene``.
    """
    override = {
        'scene': context.scene,
        'window': context.window,
        'screen': context.screen,
        'area': context.area,
        'region': context.region,
        'view_layer': context.view_layer,
        'selected_objects': list(getattr(context, 'selected_objects', [])),
        'active_object': getattr(context, 'active_object', None),
        'object': getattr(context, 'object', None),
    }
    # Drop None entries — temp_override rejects them silently but a
    # cleaner dict makes debugging easier.
    override = {k: v for k, v in override.items() if v is not None}
    with context.temp_override(**override):
        op_callable('EXEC_DEFAULT')


def _show_status_text(context, text: str, hold_seconds: float = 6.0):
    """Push *text* to Blender's bottom status bar via
    ``window_manager.status_text_set`` and auto-clear after a few
    seconds.

    Why: operator ``self.report({'INFO'}, ...)`` from inside a
    wrapper invoked from ``bpy.app.timers`` lands in the Info log
    but DOES NOT update the status bar shown at the bottom of the
    Blender window — that bar is driven by the user-invoked
    operator's last report only.  Setting ``status_text_set``
    explicitly bypasses the dispatch chain and writes the text
    directly onto the visible bar so the user sees the same line
    they'd see when clicking the N-panel button.
    """
    try:
        wm = context.window_manager
        if wm is None:
            return
        wm.status_text_set(text)
    except Exception as ex:
        print(f"[INU] status_text_set failed: {ex}")
        return

    def _clear():
        try:
            wm.status_text_set(None)
        except Exception:
            pass
        return None

    try:
        bpy.app.timers.register(_clear, first_interval=hold_seconds)
    except Exception:
        pass


class GTATOOLS_OT_link_sync(bpy.types.Operator):
    """Sync для обоих файлов: IDE + IPL.

    Не добавляет свой собственный финальный report — это бы перетёрло
    детальный отчёт inner-операторов в status-bar Blender'а
    («Sync: linked 0, обновлено 0, пропущено 2 — все без Model ID»).
    Сохраняем info-сообщение последнего inner-вызова видимым.
    """
    bl_idname = "gtatools.link_sync"
    bl_label = "INU: Sync IDE+IPL"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        GTATOOLS_OT_ide_sync_from_file.last_message = ""
        GTATOOLS_OT_ipl_sync_from_file.last_message = ""
        try:
            _run_with_override(context, bpy.ops.gtatools.ide_sync_from_file)
        except Exception as ex:
            GTATOOLS_OT_ide_sync_from_file.last_message = str(ex)
        try:
            _run_with_override(context, bpy.ops.gtatools.ipl_sync_from_file)
        except Exception as ex:
            GTATOOLS_OT_ipl_sync_from_file.last_message = str(ex)
        parts = [m for m in (
            GTATOOLS_OT_ide_sync_from_file.last_message,
            GTATOOLS_OT_ipl_sync_from_file.last_message,
        ) if m]
        if parts:
            msg = "  |  ".join(parts)
            self.report({'INFO'}, msg)
            _show_status_text(context, msg)
        return {'FINISHED'}


class GTATOOLS_OT_link_unlink(bpy.types.Operator):
    """Unlink из обоих файлов: IDE + IPL для выделенных объектов."""
    bl_idname = "gtatools.link_unlink"
    bl_label = "INU: Unlink IDE+IPL"
    bl_options = {'REGISTER'}

    def execute(self, context):
        GTATOOLS_OT_ide_remove_link.last_message = ""
        GTATOOLS_OT_ipl_remove_link.last_message = ""
        try:
            _run_with_override(context, bpy.ops.gtatools.ide_remove_link)
        except Exception as ex:
            GTATOOLS_OT_ide_remove_link.last_message = str(ex)
        try:
            _run_with_override(context, bpy.ops.gtatools.ipl_remove_link)
        except Exception as ex:
            GTATOOLS_OT_ipl_remove_link.last_message = str(ex)
        parts = [m for m in (
            GTATOOLS_OT_ide_remove_link.last_message,
            GTATOOLS_OT_ipl_remove_link.last_message,
        ) if m]
        if parts:
            msg = "  |  ".join(parts)
            self.report({'INFO'}, msg)
            _show_status_text(context, msg)
        return {'FINISHED'}


class GTATOOLS_OT_link_verify(bpy.types.Operator):
    """Verify обоих: IDE-ссылок (по model_id) + IPL-ссылок (по uuid+sidecar)."""
    bl_idname = "gtatools.link_verify"
    bl_label = "INU: Verify IDE+IPL Links"
    bl_options = {'REGISTER'}

    def execute(self, context):
        GTATOOLS_OT_ide_verify_links.last_message = ""
        GTATOOLS_OT_ipl_verify_links.last_message = ""
        try:
            _run_with_override(context, bpy.ops.gtatools.ide_verify_links)
        except Exception as ex:
            GTATOOLS_OT_ide_verify_links.last_message = str(ex)
        try:
            _run_with_override(context, bpy.ops.gtatools.ipl_verify_links)
        except Exception as ex:
            GTATOOLS_OT_ipl_verify_links.last_message = str(ex)
        parts = [m for m in (
            GTATOOLS_OT_ide_verify_links.last_message,
            GTATOOLS_OT_ipl_verify_links.last_message,
        ) if m]
        if parts:
            msg = "  |  ".join(parts)
            self.report({'INFO'}, msg)
            _show_status_text(context, msg)
        return {'FINISHED'}


class GTATOOLS_OT_remove_ide(bpy.types.Operator):
    """Удалить запись из IDE файла по Model ID"""
    bl_idname = "gtatools.remove_ide"
    bl_label = "INU: Remove from IDE"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ide import remove_ide
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ide_path)
        if not filepath:
            self.report({'ERROR'}, T("Укажите путь к IDE файлу"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        model_ids = set()
        for o in objs:
            inu = getattr(o, 'inu', None)
            mid = getattr(inu, 'model_id', 0) if inu else 0
            if mid > 0:
                model_ids.add(mid)

        if not model_ids:
            self.report({'ERROR'}, T("Нет объектов с Model ID > 0"))
            return {'CANCELLED'}

        removed = remove_ide(filepath, model_ids)
        self.report({'INFO'}, f"IDE: {T('удалено')} {removed}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_ipl(bpy.types.Operator):
    """Удалить запись из IPL файла по Model ID"""
    bl_idname = "gtatools.remove_ipl"
    bl_label = "INU: Remove from IPL"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.ipl import remove_ipl
        filepath = bpy.path.abspath(context.scene.inu_settings.gtatools_ipl_path)
        if not filepath:
            self.report({'ERROR'}, T("Укажите путь к IPL файлу"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        model_ids = set()
        for o in objs:
            inu = getattr(o, 'inu', None)
            mid = getattr(inu, 'model_id', 0) if inu else 0
            if mid > 0:
                model_ids.add(mid)

        if not model_ids:
            self.report({'ERROR'}, T("Нет объектов с Model ID > 0"))
            return {'CANCELLED'}

        removed = remove_ipl(filepath, model_ids)

        # Reset lod_index to -1 on removed objects
        for o in objs:
            if hasattr(o, 'inu'):
                o.inu.lod_index = -1

        self.report({'INFO'}, f"IPL: {T('удалено')} {removed}")
        return {'FINISHED'}


def _ensure_extension(filepath: str, ext: str) -> str:
    """Append ``ext`` (e.g. '.ide') to ``filepath`` if it isn't already
    there (case-insensitive). Operators here don't use ExportHelper so
    Blender's file dialog happily accepts ``hospital_1a`` without the
    extension and we'd silently write an extensionless file — which the
    user has to rename by hand before the game / IMG editor will load
    it.

    Edge cases:
      * Empty / None input → returned as-is (caller already handles
        empty paths elsewhere).
      * Path already ends with ``ext`` (any casing) → unchanged.
      * Path ends with a different extension (e.g. user typed
        ``foo.txt``) → still appended so we get ``foo.txt.ide``. The
        ``filter_glob='*.ide'`` makes that unlikely in practice but
        keeping the rule simple beats "smart" replacement that could
        mangle filenames with dots in them.
    """
    if not filepath:
        return filepath
    if filepath.lower().endswith(ext.lower()):
        return filepath
    return filepath + ext


class GTATOOLS_OT_export_ide(bpy.types.Operator):
    """Экспорт IDE (определение объектов GTA SA)"""
    bl_idname = "gtatools.export_ide"
    bl_label = "INU: Export IDE (.ide)"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ide", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "model.ide"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ide_export import export_ide as inu_export_ide
        self.filepath = _ensure_extension(self.filepath, ".ide")
        try:
            objs = [o for o in context.selected_objects if o.type == 'MESH']
            inu_export_ide(filepath=self.filepath, objects=objs)
            self.report({'INFO'}, f"Exported IDE: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IDE export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_ipl(bpy.types.Operator):
    """Экспорт IPL (размещение объектов GTA SA)"""
    bl_idname = "gtatools.export_ipl"
    bl_label = "INU: Export IPL (.ipl)"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})
    binary: BoolProperty(
        name="Binary (bnry)",
        description=T("Писать IPL в бинарном формате (только inst+cars)"),
        default=False,
    )

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "model.ipl"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "binary")

    def execute(self, context):
        from .ipl_export import export_ipl as inu_export_ipl
        self.filepath = _ensure_extension(self.filepath, ".ipl")
        try:
            objs = [o for o in context.selected_objects if o.type == 'MESH']
            inu_export_ipl(filepath=self.filepath, objects=objs, binary=self.binary)
            self.report({'INFO'}, f"Exported IPL: {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL export error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_ipl_sections(bpy.types.Operator):
    """Импорт секций IPL (cull, grge, enex, pick, cars, auzo, jump, occl)"""
    bl_idname = "gtatools.import_ipl_sections"
    bl_label = "INU: Import IPL Sections"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from ..core.ipl import read_ipl
        from .ipl_sections import import_ipl_sections
        try:
            ipl = read_ipl(self.filepath)
            result = import_ipl_sections(ipl)
            total = sum(len(v) for v in result.values())
            sections = ", ".join(f"{k}: {len(v)}" for k, v in result.items() if v)
            self.report({'INFO'}, f"{T('Импортировано:')} {total} ({sections})")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL sections import: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_export_ipl_sections(bpy.types.Operator):
    """Экспорт секций IPL из коллекций IPL_* в файл"""
    bl_idname = "gtatools.export_ipl_sections"
    bl_label = "INU: Export IPL Sections"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = "sections.ipl"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from ..core.ipl import IplFile, write_ipl
        from .ipl_sections import export_ipl_sections
        self.filepath = _ensure_extension(self.filepath, ".ipl")
        try:
            sections = export_ipl_sections()
            ipl = IplFile(
                culls=sections.get('cull', []),
                garages=sections.get('grge', []),
                enexs=sections.get('enex', []),
                pickups=sections.get('pick', []),
                cars=sections.get('cars', []),
                auzos=sections.get('auzo', []),
                jumps=sections.get('jump', []),
                occls=sections.get('occl', []),
                zones=sections.get('zone', []),
            )
            from ..core import game_versions as gv
            write_ipl(self.filepath, ipl,
                      game=gv.game_of_scene(context.scene))
            total = sum(len(v) for v in sections.values())
            self.report({'INFO'}, f"Exported {total} IPL section entries")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL sections export: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_ide(bpy.types.Operator):
    """Импорт IDE (определения объектов GTA SA)"""
    bl_idname = "gtatools.import_ide"
    bl_label = "INU: Import IDE (.ide)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ide", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .ide_import import import_ide as inu_import_ide
        try:
            matched = inu_import_ide(filepath=self.filepath, context=context)
            self.report({'INFO'}, f"IDE: {len(matched)} objects matched")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IDE import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_import_ipl(bpy.types.Operator):
    """Импорт IPL (размещение объектов GTA SA)"""
    bl_idname = "gtatools.import_ipl"
    bl_label = "INU: Import IPL (.ipl)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.ipl", options={'HIDDEN'})

    import_game: bpy.props.EnumProperty(
        name=T("Игра"),
        description=T("Из какой игры импортируем IPL. Auto — по числу колонок в inst-секции"),
        items=[
            ('AUTO', T("Авто-определение"), ""),
            ('III',  "GTA III",  ""),
            ('VC',   "Vice City", ""),
            ('SA',   "San Andreas", ""),
        ],
        default='AUTO')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        self.layout.prop(self, "import_game")

    def execute(self, context):
        from .ipl_import import import_ipl as inu_import_ipl
        try:
            placed = inu_import_ipl(filepath=self.filepath, context=context)
            from ..core import game_versions as gv
            if self.import_game == 'AUTO':
                detected = gv.detect_game_from_ipl(self.filepath)
            else:
                detected = self.import_game
            switched = gv.maybe_set_game_from_import(context.scene, detected)
            tag = f" → game={detected}" if switched else ""
            self.report({'INFO'}, f"IPL: {len(placed)} objects placed{tag}")
            if not switched:
                warn = gv.check_game_mismatch_warning(context.scene, detected)
                if warn:
                    self.report({'WARNING'}, warn)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"IPL import error: {str(e)}")
            return {'CANCELLED'}


class GTATOOLS_OT_replace_ipl_placeholders(bpy.types.Operator):
    """Заменить IPL Empty-плейсхолдеры на модели из сцены"""
    bl_idname = "gtatools.replace_ipl_placeholders"
    bl_label = "INU: Replace IPL Placeholders"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        replaced = 0
        # Build lookup from scene meshes
        mesh_lookup = {}
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                from .. import _clean_name_typed_ipl
                clean, stype = _clean_name_typed_ipl(obj.name)
                low = clean.lower()
                if low not in mesh_lookup:
                    mesh_lookup[low] = {}
                if stype not in mesh_lookup[low]:
                    mesh_lookup[low][stype] = obj

        for obj in list(bpy.data.objects):
            if obj.type != 'EMPTY' or not obj.get('ipl_placeholder'):
                continue

            model_name = obj.get('ipl_model_name', obj.name.replace('_empty', ''))
            key = model_name.lower()
            from ..core.ipl import is_lod_name, strip_lod_marker
            is_lod = is_lod_name(model_name)

            # Find matching mesh
            mesh_obj = None
            if is_lod:
                base = strip_lod_marker(model_name).lower()
                variants = mesh_lookup.get(base, {})
                mesh_obj = variants.get('LOD') or variants.get('DFF')
            else:
                variants = mesh_lookup.get(key, {})
                mesh_obj = variants.get('DFF') or variants.get('OTHER')

            if not mesh_obj:
                continue

            # Move existing model to placeholder position
            mesh_obj.location = obj.location.copy()
            mesh_obj.rotation_mode = 'QUATERNION'
            mesh_obj.rotation_quaternion = obj.rotation_quaternion.copy()

            # Copy IPL properties
            mesh_obj.inu.model_id = obj.inu.model_id
            mesh_obj.inu.interior_id = obj.inu.interior_id
            mesh_obj.inu.lod_index = obj.inu.lod_index

            # Remove placeholder
            bpy.data.objects.remove(obj, do_unlink=True)
            replaced += 1

        self.report({'INFO'}, f"{T('Заменено:')} {replaced}")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_upsert_ide,
    GTATOOLS_OT_upsert_ipl,
    GTATOOLS_OT_ide_sync_from_file,
    GTATOOLS_OT_ide_remove_link,
    GTATOOLS_OT_ide_verify_links,
    GTATOOLS_OT_ipl_sync_from_file,
    GTATOOLS_OT_ipl_remove_link,
    GTATOOLS_OT_ipl_verify_links,
    GTATOOLS_OT_link_sync,
    GTATOOLS_OT_link_unlink,
    GTATOOLS_OT_link_verify,
    GTATOOLS_OT_remove_ide,
    GTATOOLS_OT_remove_ipl,
    GTATOOLS_OT_export_ide,
    GTATOOLS_OT_export_ipl,
    GTATOOLS_OT_import_ipl_sections,
    GTATOOLS_OT_export_ipl_sections,
    GTATOOLS_OT_import_ide,
    GTATOOLS_OT_import_ipl,
    GTATOOLS_OT_replace_ipl_placeholders,
)
