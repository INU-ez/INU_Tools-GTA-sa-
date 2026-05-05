# INU_tools.tools.bitmaps_manager — texture audit, resolve, batch copy
#
# Provides scanning for missing textures, automatic path-resolving from
# user-specified search folders, batch copy of used textures into a
# single folder (for release builds), and a simple duplicate finder
# based on MD5 hash of file contents.

import os
import shutil
import hashlib
from collections import defaultdict

import bpy

from typing import Dict, List, Set, Tuple

from .. import T
from .compat import safe_icon
from ..core.bitmap_diff import (
    collect_used as _collect_used_from,
    diff_unused_images as _diff_unused_images,
    diff_unused_materials as _diff_unused_materials,
)


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
    mat_by_image: Dict[bpy.types.Image, Set[str]] = defaultdict(set)
    for img, mat in _iter_image_users():
        mat_by_image[img].add(mat.name)

    missing: List[Tuple[bpy.types.Image, List[str], str]] = []
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
    index: Dict[str, str] = {}
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

def _build_material_to_txds() -> Dict[str, Set[str]]:
    """Return {material_name: {txd_name, ...}} by walking every mesh object
    in the scene. txd_name lives on `obj.inu.txd_name` (not on the material
    itself), so one material slot can map to several TXD buckets when the
    same material is used across objects with different TXDs.
    """
    out: Dict[str, Set[str]] = defaultdict(set)
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
                        group_by_txd: bool = False) -> Tuple[int, int, List[str]]:
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

    wanted: Dict[bpy.types.Image, Set[str]] = defaultdict(set)
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
    errors: List[str] = []

    for img, txd_names in wanted.items():
        src = bpy.path.abspath(img.filepath or '')
        if not src or not os.path.isfile(src):
            skipped += 1
            continue
        basename = os.path.basename(src)

        targets: List[str] = []
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


# ──────────────────────────── unused cleanup ─────────────────────────

def collect_used_images_and_materials():
    """Return (used_images, used_materials) sets — datablocks that are
    actually referenced by mesh-bound material slots → TEX_IMAGE nodes.

    A material counts as used iff at least one MESH object's
    ``data.materials`` slot points at it. An image counts as used iff
    at least one *used* material has a TEX_IMAGE node pointing at it
    (so a TEX_IMAGE node inside an orphaned material doesn't keep its
    image alive).
    """
    return _collect_used_from(bpy.data.objects)


def find_unused_images(*, respect_fake_user: bool = True):
    """List images present in ``bpy.data.images`` but not reachable
    via any mesh-bound material's TEX_IMAGE node.

    Skips Blender-internal images (Render Result, Viewer Node) and,
    by default, images flagged ``use_fake_user`` — those are the
    explicit "keep this even when nothing references it" signal.
    """
    used_images, _ = collect_used_images_and_materials()
    return _diff_unused_images(
        bpy.data.images, used_images,
        respect_fake_user=respect_fake_user)


def find_unused_materials(*, respect_fake_user: bool = True):
    """List materials not assigned to any MESH object's slot.

    Same fake-user etiquette as :func:`find_unused_images`. Materials
    living only inside a node group, library override, or other graph
    edge cases get flagged — they're still detached from any mesh and
    won't make it into a TXD/DFF export.
    """
    _, used_materials = collect_used_images_and_materials()
    return _diff_unused_materials(
        bpy.data.materials, used_materials,
        respect_fake_user=respect_fake_user)


def remove_unused_textures(*, remove_materials: bool = False,
                            respect_fake_user: bool = True):
    """Delete unused images (and optionally unused materials) in place.

    Returns ``(images_removed, materials_removed)`` counts.
    """
    images = find_unused_images(respect_fake_user=respect_fake_user)
    img_count = 0
    for img in images:
        try:
            bpy.data.images.remove(img)
            img_count += 1
        except (RuntimeError, ReferenceError):
            # Image was already gone (cascade-removed by a parent), or
            # is locked by another datablock — skip rather than raise.
            continue

    mat_count = 0
    if remove_materials:
        materials = find_unused_materials(respect_fake_user=respect_fake_user)
        for mat in materials:
            try:
                bpy.data.materials.remove(mat)
                mat_count += 1
            except (RuntimeError, ReferenceError):
                continue

    return img_count, mat_count


# ──────────────────────────── duplicate detection ─────────────────────

def find_duplicate_textures() -> Dict[str, List[str]]:
    """Hash every reachable texture file on disk and return {hash: [paths...]}
    groups where the group has more than one entry.
    """
    by_hash: Dict[str, List[str]] = defaultdict(list)
    seen_paths: Set[str] = set()

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
    bl_label = "INU: Scan Missing Textures"
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
    bl_label = "INU: Resolve From Folder…"
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
    bl_label = "INU: Copy Used To Folder…"
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


class GTATOOLS_OT_bitmaps_find_unused(bpy.types.Operator):
    """Найти неиспользуемые текстуры и материалы — те, на которые не ссылается ни один меш-слот в сцене"""
    bl_idname = "gtatools.bitmaps_find_unused"
    bl_label = "INU: Find Unused"
    bl_options = {'REGISTER'}

    def execute(self, context):
        images = find_unused_images()
        materials = find_unused_materials()
        scene = context.scene
        scene['bitmaps_unused_image_count'] = len(images)
        scene['bitmaps_unused_material_count'] = len(materials)

        if not images and not materials:
            _report(self, 'INFO', "No unused textures or materials")
            return {'FINISHED'}

        if images:
            print(f"[Bitmaps Manager] Unused images ({len(images)}):")
            for img in images:
                print(f"     {img.name}  ({img.filepath or 'no path'})")
        if materials:
            print(f"[Bitmaps Manager] Unused materials ({len(materials)}):")
            for mat in materials:
                print(f"     {mat.name}")

        _report(self, 'WARNING',
                f"Unused: {len(images)} images, {len(materials)} materials "
                f"— see System Console")
        return {'FINISHED'}


class GTATOOLS_OT_bitmaps_remove_unused(bpy.types.Operator):
    """Удалить неиспользуемые текстуры и (опционально) материалы из сцены.

    use_fake_user-помеченные datablocks пропускаются — это явный знак
    «оставить даже без ссылок». Действие необратимо без Ctrl+Z, поэтому
    показывает подтверждение со счётчиками перед удалением"""
    bl_idname = "gtatools.bitmaps_remove_unused"
    bl_label = "INU: Remove Unused"
    bl_options = {'REGISTER', 'UNDO'}

    remove_materials: bpy.props.BoolProperty(
        name=T("Также удалить неиспользуемые материалы"),
        description=T("Удалить также материалы, не назначенные ни на один меш-слот"),
        default=False,
    )

    def invoke(self, context, event):
        # Compute counts so the dialog shows what will be removed
        # before the user clicks OK. Stored on self so draw() can read.
        self._img_count = len(find_unused_images())
        self._mat_count = len(find_unused_materials())
        if not self._img_count and not self._mat_count:
            _report(self, 'INFO', "No unused textures or materials")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text=T("Будет удалено:"), icon=safe_icon('TRASH'))
        box.label(text=f"{T('Текстуры')}: {self._img_count}", icon=safe_icon('IMAGE_DATA'))
        if self.remove_materials:
            box.label(text=f"{T('Материалы')}: {self._mat_count}",
                      icon=safe_icon('MATERIAL'))
        else:
            box.label(text=f"{T('Материалы')}: {self._mat_count} "
                           f"({T('пропущены')})",
                      icon=safe_icon('MATERIAL'))
        layout.prop(self, "remove_materials")
        layout.label(text=T("use_fake_user-помеченные пропускаются"),
                     icon=safe_icon('FAKE_USER_ON'))

    def execute(self, context):
        img_removed, mat_removed = remove_unused_textures(
            remove_materials=self.remove_materials)
        scene = context.scene
        # Recompute remaining (could be non-zero if locked by other refs).
        scene['bitmaps_unused_image_count'] = len(find_unused_images())
        scene['bitmaps_unused_material_count'] = len(find_unused_materials())
        if self.remove_materials:
            _report(self, 'INFO',
                    f"Removed {img_removed} images, {mat_removed} materials")
        else:
            _report(self, 'INFO',
                    f"Removed {img_removed} images")
        return {'FINISHED'}


class GTATOOLS_OT_bitmaps_find_dupes(bpy.types.Operator):
    """Хэшировать все файлы текстур и показать группы одинаковых файлов"""
    bl_idname = "gtatools.bitmaps_find_dupes"
    bl_label = "INU: Find Duplicates"
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

from ..ui.registry import apply_order


@apply_order
class GTATOOLS_MT_textures_menu(bpy.types.Menu):
    bl_label = "INU: Текстуры"
    bl_idname = "GTATOOLS_MT_textures_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("gtatools.bitmaps_resolve",
                        text=T("Найти в папке…"), icon=safe_icon('FILE_REFRESH'))
        layout.operator("gtatools.bitmaps_copy",
                        text=T("Скопировать в папку…"), icon=safe_icon('COPY_ID'))
        layout.operator("gtatools.bitmaps_find_dupes",
                        text=T("Найти дубликаты"), icon=safe_icon('DUPLICATE'))
        layout.separator()
        layout.operator("gtatools.bitmaps_find_unused",
                        text=T("Найти неиспользуемые"), icon=safe_icon('ZOOM_PREVIOUS'))
        layout.operator("gtatools.bitmaps_remove_unused",
                        text=T("Удалить неиспользуемые…"), icon=safe_icon('TRASH'))


class GTATOOLS_MT_materials_menu(bpy.types.Menu):
    bl_label = "INU: Материалы"
    bl_idname = "GTATOOLS_MT_materials_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("gtatools.check_materials",
                        text=T("Проверка материалов"), icon=safe_icon('MATERIAL'))
        layout.operator("gtatools.cleanup_materials",
                        text=T("Очистка материалов"), icon=safe_icon('BRUSH_DATA'))
        layout.operator("gtatools.sort_materials",
                        text=T("Сортировка материалов"), icon=safe_icon('SORTALPHA'))


class GTATOOLS_PT_bitmaps_panel(bpy.types.Panel):
    bl_label = T("Менеджер текстур")
    bl_idname = "GTATOOLS_PT_bitmaps_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('IMAGE_DATA'))

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row(align=True)
        row.operator("gtatools.bitmaps_scan",
                     text=T("Сканировать"), icon=safe_icon('VIEWZOOM'))
        from .compat import ICON_CHECK
        miss = scene.get('bitmaps_missing_count', None)
        if miss is not None:
            row.label(text=f"{T('Пропущено')}: {miss}",
                      icon=safe_icon('ERROR') if miss else ICON_CHECK)

        # Текстуры dropdown — file ops + unused cleanup all live here.
        # Unused-count badge sits next to the menu since «Найти/Удалить
        # неиспользуемые» are the ops that produce/consume that count.
        row = layout.row(align=True)
        row.menu("GTATOOLS_MT_textures_menu",
                 text=T("Текстуры"), icon=safe_icon('IMAGE_DATA'))
        unused_imgs = scene.get('bitmaps_unused_image_count')
        unused_mats = scene.get('bitmaps_unused_material_count')
        if unused_imgs is not None:
            total = unused_imgs + (unused_mats or 0)
            row.label(
                text=f"{T('Неисп.')}: {unused_imgs}/{unused_mats or 0}",
                icon=safe_icon('INFO') if total else ICON_CHECK)

        # Материалы dropdown — Check / Cleanup / Sort consolidated here
        # for the same scene-wide asset-management scope as bitmaps.
        layout.menu("GTATOOLS_MT_materials_menu",
                    text=T("Материалы"), icon=safe_icon('MATERIAL'))


classes = (
    GTATOOLS_MT_textures_menu,
    GTATOOLS_MT_materials_menu,
    GTATOOLS_OT_bitmaps_scan,
    GTATOOLS_OT_bitmaps_resolve,
    GTATOOLS_OT_bitmaps_copy,
    GTATOOLS_OT_bitmaps_find_unused,
    GTATOOLS_OT_bitmaps_remove_unused,
    GTATOOLS_OT_bitmaps_find_dupes,
    GTATOOLS_PT_bitmaps_panel,
)
