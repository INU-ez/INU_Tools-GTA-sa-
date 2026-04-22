# INU_tools.tools.bitmaps_manager — texture audit, resolve, batch copy
#
# Provides scanning for missing textures, automatic path-resolving from
# user-specified search folders, batch copy of used textures into a
# single folder (for release builds), and a simple duplicate finder
# based on MD5 hash of file contents.

from __future__ import annotations

import os
import shutil
import hashlib
from collections import defaultdict

import bpy

from .. import T


# ──────────────────────────── scanning ────────────────────────────────

def _iter_image_users():
    """Yield (image, material) for every image referenced by any material."""
    for mat in bpy.data.materials:
        if not mat.use_nodes or not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                yield node.image, mat


def scan_missing_textures():
    """Return list of (image, list_of_materials, reason) for textures that
    cannot be loaded. `reason` is one of: 'empty', 'not_found', 'packed_ok'.
    Packed images never count as missing — they are skipped from the result.
    """
    mat_by_image: dict[bpy.types.Image, set[str]] = defaultdict(set)
    for img, mat in _iter_image_users():
        mat_by_image[img].add(mat.name)

    missing: list[tuple[bpy.types.Image, list[str], str]] = []
    for img, mats in mat_by_image.items():
        if img.packed_file:
            continue  # packed textures are always OK
        fp = bpy.path.abspath(img.filepath or '')
        if not fp:
            missing.append((img, sorted(mats), 'empty'))
            continue
        if not os.path.isfile(fp):
            missing.append((img, sorted(mats), 'not_found'))
    return missing


def resolve_missing(search_folders, *, extensions=('.png', '.tga', '.jpg',
                                                    '.jpeg', '.bmp', '.tiff',
                                                    '.dds')):
    """Walk `search_folders` recursively, match by basename (case-insensitive)
    against missing textures, and patch image.filepath when found.

    Returns (resolved_count, still_missing_count).
    """
    missing = scan_missing_textures()
    if not missing:
        return 0, 0

    # Build name → full path index of every candidate file
    index: dict[str, str] = {}
    for folder in search_folders:
        if not folder or not os.path.isdir(folder):
            continue
        for root, _dirs, files in os.walk(folder):
            for fn in files:
                if not fn.lower().endswith(extensions):
                    continue
                key = fn.lower()
                # prefer first hit; keep deterministic
                index.setdefault(key, os.path.join(root, fn))
                # also index bare stem so that .png can resolve a .tga request
                stem = os.path.splitext(fn)[0].lower()
                index.setdefault(stem, os.path.join(root, fn))

    resolved = 0
    for img, _mats, _reason in missing:
        target = img.name.lower()
        hit = index.get(target)
        if not hit:
            stem = os.path.splitext(target)[0]
            hit = index.get(stem)
        if hit:
            img.filepath = bpy.path.relpath(hit) if bpy.data.filepath else hit
            try:
                img.reload()
            except RuntimeError:
                pass
            resolved += 1

    still_missing = len(scan_missing_textures())
    return resolved, still_missing


# ──────────────────────────── batch copy ──────────────────────────────

def _build_material_to_txds() -> dict[str, set[str]]:
    """Return {material_name: {txd_name, ...}} by walking every mesh object
    in the scene. txd_name lives on `obj.inu.txd_name` (not on the material
    itself), so one material slot can map to several TXD buckets when the
    same material is used across objects with different TXDs.
    """
    out: dict[str, set[str]] = defaultdict(set)
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        inu = getattr(obj, 'inu', None)
        txd = (getattr(inu, 'txd_name', '') if inu else '') or ''
        if not txd:
            continue
        for slot in obj.data.materials:
            if slot:
                out[slot.name].add(txd)
    return out


def batch_copy_textures(target_dir: str, *, used_only: bool = True,
                        group_by_txd: bool = False) -> tuple[int, int, list[str]]:
    """Copy textures referenced in the scene into `target_dir`.

    `used_only=True` copies only images that are used by at least one material.
    `group_by_txd=True` places each image in a subfolder per TXD. The TXD
    name is read from `obj.inu.txd_name` on every mesh that uses the
    material — if multiple TXDs share a material, the texture is copied
    into each of their subfolders.

    Returns (copied, skipped, errors).
    """
    os.makedirs(target_dir, exist_ok=True)

    mat_to_txds = _build_material_to_txds() if group_by_txd else {}

    wanted: dict[bpy.types.Image, set[str]] = defaultdict(set)
    if used_only:
        for img, mat in _iter_image_users():
            if group_by_txd:
                for txd in mat_to_txds.get(mat.name, {''}):
                    wanted[img].add(txd)
            else:
                wanted[img].add('')
    else:
        for img in bpy.data.images:
            wanted[img] = {''}

    copied = 0
    skipped = 0
    errors: list[str] = []

    for img, txd_names in wanted.items():
        src = bpy.path.abspath(img.filepath or '')
        if not src or not os.path.isfile(src):
            skipped += 1
            continue
        basename = os.path.basename(src)

        targets: list[str] = []
        if group_by_txd:
            for txd in (txd_names or {''}):
                sub = os.path.join(target_dir, txd) if txd else target_dir
                os.makedirs(sub, exist_ok=True)
                targets.append(os.path.join(sub, basename))
        else:
            targets.append(os.path.join(target_dir, basename))

        for dst in targets:
            if os.path.abspath(src) == os.path.abspath(dst):
                skipped += 1
                continue
            try:
                shutil.copy2(src, dst)
                copied += 1
            except OSError as e:
                errors.append(f"{basename}: {e}")

    return copied, skipped, errors


# ──────────────────────────── duplicate detection ─────────────────────

def find_duplicate_textures() -> dict[str, list[str]]:
    """Hash every reachable texture file on disk and return {hash: [paths...]}
    groups where the group has more than one entry.
    """
    by_hash: dict[str, list[str]] = defaultdict(list)
    seen_paths: set[str] = set()

    for img in bpy.data.images:
        fp = bpy.path.abspath(img.filepath or '')
        if not fp or not os.path.isfile(fp):
            continue
        real = os.path.normcase(os.path.abspath(fp))
        if real in seen_paths:
            continue
        seen_paths.add(real)
        try:
            with open(real, 'rb') as f:
                h = hashlib.md5(f.read()).hexdigest()
        except OSError:
            continue
        by_hash[h].append(real)

    return {h: paths for h, paths in by_hash.items() if len(paths) > 1}


# ──────────────────────────── operators ───────────────────────────────

def _report(op, level: str, msg: str):
    op.report({level}, msg)
    print(f"[Bitmaps Manager] {msg}")


class GTATOOLS_OT_bitmaps_scan(bpy.types.Operator):
    """Проверить все материалы и показать текстуры, файлы которых не найдены"""
    bl_idname = "gtatools.bitmaps_scan"
    bl_label = "Scan Missing Textures"
    bl_options = {'REGISTER'}

    def execute(self, context):
        missing = scan_missing_textures()
        scene = context.scene
        scene['bitmaps_missing_count'] = len(missing)
        if not missing:
            _report(self, 'INFO', "All textures resolved — nothing missing")
            return {'FINISHED'}

        for img, mats, reason in missing:
            print(f"  [{reason:9}] {img.name} → {img.filepath!r}  "
                  f"(used by: {', '.join(mats)})")
        _report(self, 'WARNING',
                f"Missing: {len(missing)} (see System Console for details)")
        return {'FINISHED'}


class GTATOOLS_OT_bitmaps_resolve(bpy.types.Operator):
    """Рекурсивно искать в выбранной папке и подставлять image.filepath для найденных по имени недостающих текстур"""
    bl_idname = "gtatools.bitmaps_resolve"
    bl_label = "Resolve From Folder…"
    bl_options = {'REGISTER'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        folders = [self.directory]
        extra = (context.scene.get('bitmaps_extra_folders') or '').splitlines()
        folders.extend(f for f in extra if f.strip())
        resolved, left = resolve_missing(folders)
        if left == 0:
            _report(self, 'INFO', f"Resolved {resolved}, nothing left missing")
        else:
            _report(self, 'WARNING',
                    f"Resolved {resolved}, still missing {left}")
        return {'FINISHED'}


class GTATOOLS_OT_bitmaps_copy(bpy.types.Operator):
    """Скопировать все используемые материалами текстуры сцены в выбранную папку"""
    bl_idname = "gtatools.bitmaps_copy"
    bl_label = "Copy Used To Folder…"
    bl_options = {'REGISTER'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    group_by_txd: bpy.props.BoolProperty(
        name="Subfolder per TXD",
        description=T("Создать подпапку на каждый txd_name (читается с mesh-объектов)"),
        default=False,
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.directory or not os.path.isdir(self.directory):
            _report(self, 'ERROR', "Target folder not set")
            return {'CANCELLED'}
        copied, skipped, errors = batch_copy_textures(
            self.directory, used_only=True, group_by_txd=self.group_by_txd)
        for e in errors:
            print(f"  [error] {e}")
        _report(self, 'INFO',
                f"Copied {copied}, skipped {skipped}, errors {len(errors)}")
        return {'FINISHED'}


class GTATOOLS_OT_bitmaps_find_dupes(bpy.types.Operator):
    """Хэшировать все файлы текстур и показать группы одинаковых файлов"""
    bl_idname = "gtatools.bitmaps_find_dupes"
    bl_label = "Find Duplicates"
    bl_options = {'REGISTER'}

    def execute(self, context):
        dupes = find_duplicate_textures()
        if not dupes:
            _report(self, 'INFO', "No duplicate textures found")
            return {'FINISHED'}
        total = sum(len(v) for v in dupes.values())
        for h, paths in dupes.items():
            print(f"  [dupe {h[:8]}] {len(paths)} copies:")
            for p in paths:
                print(f"     {p}")
        _report(self, 'WARNING',
                f"{len(dupes)} duplicate groups ({total} files) — see console")
        return {'FINISHED'}


# ──────────────────────────── panel ───────────────────────────────────

class GTATOOLS_PT_bitmaps_panel(bpy.types.Panel):
    bl_label = "Bitmaps Manager"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        from . import icons as _icons
        layout = self.layout
        scene = context.scene

        picture_id = _icons.get_icon("picture")

        row = layout.row(align=True)
        if picture_id:
            row.operator("gtatools.bitmaps_scan",
                         icon_value=picture_id)
        else:
            row.operator("gtatools.bitmaps_scan", icon='VIEWZOOM')
        miss = scene.get('bitmaps_missing_count', None)
        if miss is not None:
            row.label(text=f"Missing: {miss}",
                      icon='ERROR' if miss else 'CHECKMARK')

        col = layout.column(align=True)
        col.operator("gtatools.bitmaps_resolve", icon='FILE_REFRESH')
        col.operator("gtatools.bitmaps_copy", icon='COPY_ID')
        col.operator("gtatools.bitmaps_find_dupes", icon='DUPLICATE')


classes = (
    GTATOOLS_OT_bitmaps_scan,
    GTATOOLS_OT_bitmaps_resolve,
    GTATOOLS_OT_bitmaps_copy,
    GTATOOLS_OT_bitmaps_find_dupes,
    GTATOOLS_PT_bitmaps_panel,
)
