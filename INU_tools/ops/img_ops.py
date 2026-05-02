# INU_tools.ops.img_ops — IMG archive operators.
#
# Phase 3 of UI redesign: extracted from __init__.py without behavior
# changes. Five operators + two helpers (_refresh_img_entries,
# _append_export_report) live here. The Extract Resources modal is the
# heaviest — keeps its modal/timer/threadpool flow intact.

import os
import time
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import bpy
from bpy.props import BoolProperty, StringProperty

# T must be top-level — operator class bodies use T("...") in property
# descriptions which evaluate at class-definition time.
# _get_cache_dir / _write_png / _append_export_report live further down
# in the parent __init__.py than this import — pull them lazily inside
# each method so registration order doesn't matter.
from .. import T


# ──────────────────────────── helpers ─────────────────────────────────

def _refresh_img_entries(scn, img_path):
    """Directly refresh IMG entries list."""
    scn.gtatools_img_entries.clear()
    try:
        from ..core.img import read_directory
        entries = read_directory(img_path)
        for entry in entries:
            item = scn.gtatools_img_entries.add()
            item.name = entry.name
        scn.gtatools_img_entries_index = max(0, len(entries) - 1)
    except Exception:
        pass


# ──────────────────────────── operators ───────────────────────────────

class GTATOOLS_OT_refresh_img_list(bpy.types.Operator):
    """Обновить список файлов IMG архива"""
    bl_idname = "gtatools.refresh_img_list"
    bl_label = "INU: Refresh IMG List"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.img import read_directory
        scn = context.scene
        img_path = bpy.path.abspath(scn.gtatools_img_path)
        if not img_path or not os.path.isfile(img_path):
            self.report({'WARNING'}, T("Укажите путь к IMG"))
            return {'CANCELLED'}

        scn.gtatools_img_entries.clear()
        try:
            entries = read_directory(img_path)
            for entry in entries:
                item = scn.gtatools_img_entries.add()
                item.name = entry.name
            scn.gtatools_img_entries_index = max(0, len(entries) - 1)
            self.report({'INFO'}, f"{T('Файлов:')} {len(scn.gtatools_img_entries)}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}


class GTATOOLS_OT_extract_resources(bpy.types.Operator):
    """Извлечь все DFF, COL и текстуры из IMG в .inu_cache/"""
    bl_idname = "gtatools.extract_textures"
    bl_label = "INU: Extract Resources"
    bl_options = {'REGISTER'}

    _timer = None
    _gen = None

    def invoke(self, context, event):
        scene = context.scene

        # Cache lives next to the .blend file (see _get_cache_dir).
        # Without a saved .blend the cache lands in a temp folder
        # that vanishes on Blender restart — extraction would burn
        # minutes for nothing. Block until the user saves.
        if not bpy.data.filepath:
            self.report({'ERROR'}, T(
                "Сначала сохраните сцену (.blend) — кеш создаётся "
                "рядом с ней. Без сохранения извлечение уйдёт "
                "во временную папку и пропадёт"))
            return {'CANCELLED'}

        game_root = bpy.path.abspath(scene.gtatools_game_root)

        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}

        from ..core.gta_dat import find_all_resources
        from ..core.img import read_directory
        from ..core.ide import read_ide
        from ..core.ipl import read_ipl

        info = find_all_resources(game_root)

        # Collect all IMG archives — standard gta3.img + gta.dat-listed
        # archives + the user's manually-set fallback.
        img_paths = []
        std = os.path.join(game_root, 'models', 'gta3.img')
        if os.path.isfile(std):
            img_paths.append(std)
        for p in info.img_paths:
            if os.path.isfile(p) and p not in img_paths:
                img_paths.append(p)
        fallback = bpy.path.abspath(scene.gtatools_img_path)
        if fallback and os.path.isfile(fallback) and fallback not in img_paths:
            img_paths.append(fallback)

        if not img_paths:
            self.report({'ERROR'}, T("Не найден IMG архив"))
            return {'CANCELLED'}

        # Region filter — when picked, walk matching IPLs to gather used
        # model_ids, look those up in IDE files to get TXD names, then
        # only extract those TXDs. Saves minutes on large extracts.
        region = getattr(scene, 'gtatools_map_region', 'ALL')
        needed_txds = None  # None = "extract everything"
        if region != 'ALL':
            def _ipl_matches_region(path: str) -> bool:
                parts = path.replace('\\', '/').upper().split('/')
                for i, part in enumerate(parts):
                    if part == 'MAPS' and i + 1 < len(parts):
                        return parts[i + 1] == region
                name = path.replace('\\', '/').rsplit('/', 1)[-1].upper()
                return name.startswith(region)

            ide_txd_by_id = {}
            for p in info.ide_paths:
                if os.path.isfile(p):
                    try:
                        ide = read_ide(p)
                        for obj in ide.objects:
                            ide_txd_by_id[obj.model_id] = obj.txd_name
                        for anim in ide.anims:
                            ide_txd_by_id.setdefault(anim.model_id, anim.txd_name)
                    except Exception:
                        pass

            used_ids = set()
            for p in info.ipl_paths:
                if os.path.isfile(p) and _ipl_matches_region(p):
                    try:
                        ipl = read_ipl(p)
                        for inst in ipl.instances:
                            used_ids.add(inst.model_id)
                    except Exception:
                        pass

            needed_txds = {
                ide_txd_by_id[mid].lower()
                for mid in used_ids
                if mid in ide_txd_by_id and ide_txd_by_id[mid]
            }

        from .. import _get_cache_dir
        cache_dir = _get_cache_dir()
        tex_dir = os.path.join(cache_dir, 'textures')
        os.makedirs(tex_dir, exist_ok=True)

        # Pre-count TXDs for accurate progress (after region filter if any)
        txd_total = 0
        for ip in img_paths:
            try:
                for e in read_directory(ip):
                    low = e.name.lower()
                    if not low.endswith('.txd'):
                        continue
                    if needed_txds is not None:
                        if low[:-4] not in needed_txds:
                            continue
                    txd_total += 1
            except Exception:
                pass

        self._img_paths = img_paths
        self._cache_dir = cache_dir
        self._tex_dir = tex_dir
        self._txd_total = txd_total
        self._needed_txds = needed_txds  # None = no filter
        self._region = region
        self._dff_count = 0
        self._col_count = 0
        self._tex_count = 0
        self._skipped = 0
        self._txd_progress = 0

        from ..tools.profiler import Profiler
        self._profiler = Profiler(
            f"Extract Resources ({region})",
            enabled=bool(getattr(scene, 'gtatools_profile_enabled', False)),
        )

        self._gen = self._work(context)
        wm = context.window_manager
        wm.progress_begin(0, max(txd_total, 1))
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Извлечение ресурсов..."))
        return {'RUNNING_MODAL'}

    def _work(self, context):
        from ..core.img import ImgReader
        from ..core.txd import read_txd
        from .. import _write_png
        import threading

        cache_dir = self._cache_dir
        tex_dir = self._tex_dir
        needed_txds = self._needed_txds
        prof = self._profiler

        # Counters lock protects self._tex_count / self._skipped updates
        # from worker threads.
        counters_lock = threading.Lock()

        def _process_txd(entry_name: str, txd_data: bytes):
            """Worker: parse TXD bytes and write PNG for each texture.

            numpy DXT decompress (in read_txd) and zlib.compress (in
            _write_png) both release the GIL — so N workers do real
            parallel work on multi-core CPUs.
            """
            try:
                with prof.stage('read_txd (numpy DXT)', note=entry_name):
                    textures = read_txd(txd_data)
            except Exception as e:
                try:
                    with open(os.path.join(cache_dir, '_txd_errors.log'),
                              'a', encoding='utf-8') as lf:
                        lf.write(f"{entry_name}: {e}\n")
                except Exception:
                    pass
                return

            for tex in textures:
                name = tex.name.rstrip('\x00')
                if not name or tex.width == 0 or tex.height == 0 or not tex.pixels:
                    continue
                png_path = os.path.join(tex_dir, name + '.png')
                if os.path.isfile(png_path):
                    existing_size = os.path.getsize(png_path)
                    new_size = tex.width * tex.height * 4
                    if new_size <= existing_size:
                        with counters_lock:
                            self._skipped += 1
                        continue

                try:
                    with prof.stage('_write_png'):
                        _write_png(png_path, tex.pixels, tex.width, tex.height)
                    with counters_lock:
                        self._tex_count += 1
                except Exception as e:
                    try:
                        with open(os.path.join(cache_dir, '_txd_errors.log'),
                                  'a', encoding='utf-8') as lf:
                            lf.write(f"{entry_name}/{name}: {e}\n")
                    except Exception:
                        pass

        # Worker count — start conservative (4). Bumping to 8 is safe too
        # but diminishing returns above that since IMG reads are serial.
        workers = min(os.cpu_count() or 4, 4)

        for ip in self._img_paths:
            try:
                with ImgReader(ip) as img:
                    with prof.stage('extract_all_to (DFF+COL)', note=os.path.basename(ip)):
                        counts = img.extract_all_to(
                            cache_dir,
                            extensions={'.dff', '.col'},
                            skip_existing=True)
                    self._dff_count += counts['dff']
                    self._col_count += counts['col']
                    self._skipped += counts['skipped']

                    # TXD processing — main thread reads bytes, pool crunches.
                    # ThreadPoolExecutor's __exit__ would block the generator
                    # until every worker finishes which freezes the UI; manage
                    # the pool manually and yield during drain so modal ticks
                    # fire and the progress bar keeps updating.
                    done_count = [0]
                    done_lock = threading.Lock()

                    def _on_done(_fut, _d=done_count, _l=done_lock,
                                 _self=self):
                        with _l:
                            _d[0] += 1
                            _self._txd_progress += 1

                    pool = ThreadPoolExecutor(max_workers=workers)
                    submitted = 0
                    try:
                        for entry in img.entries:
                            low = entry.name.lower()
                            if not low.endswith('.txd'):
                                continue
                            if needed_txds is not None and low[:-4] not in needed_txds:
                                continue

                            with prof.stage('img.read (TXD bytes)'):
                                txd_data = img.read(entry.name)
                            if not txd_data:
                                continue

                            fut = pool.submit(_process_txd, entry.name, txd_data)
                            fut.add_done_callback(_on_done)
                            submitted += 1
                            yield  # let modal tick between submits

                        # Drain — wait for every submitted future while
                        # yielding so UI keeps updating every ~50 ms.
                        import time as _t
                        while True:
                            with done_lock:
                                done = done_count[0]
                            if done >= submitted:
                                break
                            _t.sleep(0.01)
                            yield
                    finally:
                        pool.shutdown(wait=False)
            except Exception:
                pass

        if prof.enabled:
            prof.print_report()
            prof.save_log(os.path.join(cache_dir, '_profile.log'))

    def modal(self, context, event):
        if event.type == 'ESC':
            self._cleanup(context)
            self.report({'WARNING'}, T("Отменено"))
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        wm = context.window_manager
        deadline = time.monotonic() + 0.1

        while time.monotonic() < deadline:
            try:
                next(self._gen)
            except StopIteration:
                self._cleanup(context)
                self.report({'INFO'},
                    f"DFF: {self._dff_count}, COL: {self._col_count}, "
                    f"{T('Извлечено текстур:')} {self._tex_count}, "
                    f"{T('пропущено:')} {self._skipped}")
                return {'FINISHED'}

        wm.progress_update(self._txd_progress)
        context.workspace.status_text_set(
            f"TXD: {self._txd_progress}/{self._txd_total} | "
            f"DFF: {self._dff_count} COL: {self._col_count}")

        return {'RUNNING_MODAL'}

    def _cleanup(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.window_manager.progress_end()
        context.workspace.status_text_set(None)


class GTATOOLS_OT_import_from_img(bpy.types.Operator):
    """Импортировать модели из IMG архива (по списку из IDE/IPL)"""
    bl_idname = "gtatools.import_from_img"
    bl_label = "INU: Import from IMG"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..core.img import extract_file, read_directory
        from ..core.ide import read_ide
        from ..core.ipl import read_ipl
        from .dff_import import import_dff as inu_import_dff
        from .txd_import import import_txd as inu_import_txd
        from mathutils import Quaternion

        scene = context.scene
        img_path = bpy.path.abspath(scene.gtatools_img_path)
        ide_path = bpy.path.abspath(scene.gtatools_ide_path)
        ipl_path = bpy.path.abspath(scene.gtatools_ipl_path)
        game_root = bpy.path.abspath(scene.gtatools_game_root)

        if not img_path or not os.path.isfile(img_path):
            self.report({'ERROR'}, T("Укажите путь к IMG архиву в INU Tools"))
            return {'CANCELLED'}

        ide_models = {}
        instances = []

        use_gta_dat = getattr(scene, 'gtatools_img_use_gta_dat', False)
        skip_lod = getattr(scene, 'gtatools_img_skip_lod', False)
        load_txd = getattr(scene, 'gtatools_img_load_txd', True)

        if use_gta_dat and game_root and os.path.isdir(game_root):
            from ..core.gta_dat import find_all_resources
            info = find_all_resources(game_root)

            for p in info.ide_paths:
                if os.path.isfile(p):
                    try:
                        ide = read_ide(p)
                        for obj in ide.objects:
                            ide_models[obj.model_id] = obj
                        for anim in ide.anims:
                            if anim.model_id not in ide_models:
                                ide_models[anim.model_id] = anim
                    except Exception:
                        pass

            for p in info.ipl_paths:
                if os.path.isfile(p):
                    try:
                        ipl = read_ipl(p)
                        instances.extend(ipl.instances)
                    except Exception:
                        pass

            # Also read binary IPL from IMG (stream files)
            img_dir = read_directory(img_path)
            for e in img_dir:
                if e.name.lower().endswith('.ipl'):
                    try:
                        ipl_data = extract_file(img_path, e.name)
                        if ipl_data and ipl_data[:4] == b'bnry':
                            ipl = read_ipl.__wrapped__(ipl_data) if hasattr(read_ipl, '__wrapped__') else None
                            if ipl is None:
                                from ..core.ipl import _read_binary_ipl
                                ipl_parsed = _read_binary_ipl(ipl_data)
                                instances.extend(ipl_parsed.instances)
                    except Exception:
                        pass
        else:
            if ide_path and os.path.isfile(ide_path):
                ide = read_ide(ide_path)
                for obj in ide.objects:
                    ide_models[obj.model_id] = obj
                for anim in ide.anims:
                    if anim.model_id not in ide_models:
                        ide_models[anim.model_id] = anim

            if ipl_path and os.path.isfile(ipl_path):
                ipl = read_ipl(ipl_path)
                instances = ipl.instances

        if not instances:
            self.report({'ERROR'}, T("IPL файл пуст или не указан"))
            return {'CANCELLED'}

        img_files = {e.name.lower(): e.name for e in read_directory(img_path)}

        def _get_or_create_collection(name):
            col = bpy.data.collections.get(name)
            if not col:
                col = bpy.data.collections.new(name)
                context.scene.collection.children.link(col)
            return col

        dff_collection = _get_or_create_collection("Map_DFF")
        lod_collection = _get_or_create_collection("Map_LOD")
        col_collection = _get_or_create_collection("Map_COL")

        wm = context.window_manager
        wm.progress_begin(0, len(instances))

        imported_count = 0
        skipped_count = 0
        errors = []

        from ..core.ipl import is_lod_name, lod_instance_indices
        lod_refs = lod_instance_indices(instances)

        with tempfile.TemporaryDirectory() as tmpdir:
            imported_models = {}

            for idx, inst in enumerate(instances):
                wm.progress_update(idx)
                model_name = inst.model_name
                is_lod = idx in lod_refs or is_lod_name(model_name)

                if skip_lod and is_lod:
                    skipped_count += 1
                    continue

                target_collection = lod_collection if is_lod else dff_collection

                dff_filename = model_name + '.dff'

                if dff_filename.lower() not in img_files:
                    skipped_count += 1
                    continue

                if model_name in imported_models:
                    new_objects = []
                    for src_obj in imported_models[model_name]:
                        new_obj = src_obj.copy()
                        new_obj.data = src_obj.data  # linked duplicate
                        target_collection.objects.link(new_obj)
                        new_objects.append(new_obj)
                else:
                    dff_data = extract_file(img_path, img_files[dff_filename.lower()])
                    if not dff_data:
                        errors.append(f"{model_name}: DFF extract failed")
                        continue

                    dff_path = os.path.join(tmpdir, dff_filename)
                    with open(dff_path, 'wb') as f:
                        f.write(dff_data)

                    try:
                        before = set(context.scene.objects)
                        inu_import_dff(filepath=dff_path, context=context)
                        after = set(context.scene.objects)
                        new_objects = list(after - before)

                        if load_txd:
                            txd_name = model_name
                            if inst.model_id in ide_models:
                                txd_name = ide_models[inst.model_id].txd_name

                            txd_filename = txd_name + '.txd'
                            if txd_filename.lower() in img_files:
                                txd_data = extract_file(img_path, img_files[txd_filename.lower()])
                                if txd_data:
                                    txd_path = os.path.join(tmpdir, txd_filename)
                                    with open(txd_path, 'wb') as f:
                                        f.write(txd_data)
                                    try:
                                        inu_import_txd(filepath=txd_path)
                                    except:
                                        pass

                        for obj in new_objects:
                            for c in list(obj.users_collection):
                                c.objects.unlink(obj)
                            target_collection.objects.link(obj)

                        col_filename = model_name + '.col'
                        if col_filename.lower() in img_files:
                            col_data = extract_file(img_path, img_files[col_filename.lower()])
                            if col_data:
                                col_path = os.path.join(tmpdir, col_filename)
                                with open(col_path, 'wb') as f:
                                    f.write(col_data)
                                try:
                                    from .col_import import import_col as inu_import_col
                                    before_col = set(context.scene.objects)
                                    inu_import_col(filepath=col_path, context=context)
                                    after_col = set(context.scene.objects)
                                    col_objects = list(after_col - before_col)
                                    col_pos = (inst.pos_x, inst.pos_y, inst.pos_z)
                                    col_rot = Quaternion((inst.rot_w, inst.rot_x, inst.rot_y, inst.rot_z)).conjugated()
                                    _sfx_col = getattr(scene, 'gtatools_suffix_col', '_COL')
                                    _pfx_col = getattr(scene, 'gtatools_prefix_col', '')
                                    for co in col_objects:
                                        for c in list(co.users_collection):
                                            c.objects.unlink(co)
                                        col_collection.objects.link(co)
                                        co.location = col_pos
                                        co.rotation_mode = 'QUATERNION'
                                        co.rotation_quaternion = col_rot
                                        from ..core.ipl import strip_lod_marker
                                        base_col = strip_lod_marker(model_name)
                                        if _sfx_col:
                                            co.name = base_col + _sfx_col
                                        elif _pfx_col:
                                            co.name = _pfx_col + base_col
                                except:
                                    pass

                        imported_models[model_name] = new_objects
                    except Exception as e:
                        errors.append(f"{model_name}: {str(e)}")
                        continue

                _sfx_dff = getattr(scene, 'gtatools_suffix_dff', '_DFF')
                _sfx_lod = getattr(scene, 'gtatools_suffix_lod', '_LOD')
                _pfx_dff = getattr(scene, 'gtatools_prefix_dff', '')
                _pfx_lod = getattr(scene, 'gtatools_prefix_lod', '')
                for obj in new_objects:
                    if obj.type == 'MESH':
                        base = obj.name
                        if '.dff' in base.lower():
                            base = base.split('.dff')[0]
                        if '.' in base:
                            b, s = base.rsplit('.', 1)
                            if s.isdigit():
                                base = b
                        # Strip _0/_1/etc suffix added when DFF has multiple atomics
                        if '_' in base:
                            b, s = base.rsplit('_', 1)
                            if s.isdigit():
                                base = b

                        if is_lod:
                            from ..core.ipl import strip_lod_marker
                            base = strip_lod_marker(base)
                            if _sfx_lod:
                                obj.name = base + _sfx_lod
                            elif _pfx_lod:
                                obj.name = _pfx_lod + base
                        else:
                            if _sfx_dff:
                                obj.name = base + _sfx_dff
                            elif _pfx_dff:
                                obj.name = _pfx_dff + base

                pos = (inst.pos_x, inst.pos_y, inst.pos_z)
                # GTA SA quaternion is stored conjugated
                rot = Quaternion((inst.rot_w, inst.rot_x, inst.rot_y, inst.rot_z)).conjugated()

                for obj in new_objects:
                    if obj.type == 'MESH':
                        obj.location = pos
                        obj.rotation_mode = 'QUATERNION'
                        obj.rotation_quaternion = rot
                        if hasattr(obj, 'inu'):
                            obj.inu.model_id = inst.model_id
                            if inst.model_id in ide_models:
                                ide_obj = ide_models[inst.model_id]
                                obj.inu.draw_distance = ide_obj.draw_distance
                                obj.inu.ide_flags = ide_obj.flags
                                obj.inu.txd_name = ide_obj.txd_name

                imported_count += 1

        wm.progress_end()

        msg = f"{T('Импортировано:')} {imported_count}"
        if skipped_count:
            msg += f", {T('пропущено:')} {skipped_count}"
        if errors:
            msg += f", {T('ошибок:')} {len(errors)}"
            for e in errors[:5]:
                print(f"[Map Import] {e}")
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_remove_from_img(bpy.types.Operator):
    """Удалить DFF/TXD/COL выделенных моделей из IMG архива"""
    bl_idname = "gtatools.remove_from_img"
    bl_label = "INU: Remove from IMG"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.img import remove_file
        from ..tools.model_utils import get_model_type

        img_path = bpy.path.abspath(context.scene.gtatools_img_path)
        if not img_path or not os.path.isfile(img_path):
            self.report({'ERROR'}, T("Укажите путь к .img архиву"))
            return {'CANCELLED'}

        objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not objs:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        removed = []
        for obj in objs:
            mt, base = get_model_type(obj)
            if not base:
                continue

            if mt == 'DFF':
                if remove_file(img_path, base + '.dff'):
                    removed.append(base + '.dff')
                if remove_file(img_path, base + '.txd'):
                    removed.append(base + '.txd')
            elif mt == 'LOD':
                fname = 'LOD' + base + '.dff'
                if remove_file(img_path, fname):
                    removed.append(fname)
            elif mt == 'COL':
                if remove_file(img_path, base + '.col'):
                    removed.append(base + '.col')

        if removed:
            _refresh_img_entries(context.scene, img_path)
            self.report({'INFO'}, f"IMG: {T('удалено')} {', '.join(removed)}")
            # Status-bar reminder shows the *latest* report — make sure
            # the rebuild hint is the one users see. The list of removed
            # files stays in the report log for click-through.
            self.report(
                {'INFO'},
                T("Rebuild Archive в IMG-туле — иначе игра подтянет старую запись"))
        else:
            self.report({'WARNING'}, T("Файлы не найдены в IMG"))
        return {'FINISHED'}


class GTATOOLS_OT_export_to_img(bpy.types.Operator):
    """Экспортировать DFF + TXD + COL прямо в .img архив"""
    bl_idname = "gtatools.export_to_img"
    bl_label = "INU: Export to IMG"
    bl_options = {'REGISTER'}

    shared_txd: BoolProperty(
        name=T("Общий TXD"),
        description=T("Пакует все текстуры в один .txd. Выключено — один .txd на каждую уникальную строку txd_name из списка ниже"),
        default=False,
    )
    shared_txd_name: StringProperty(
        name=T("Имя общего TXD"),
        description=T("Имя .txd файла без расширения"),
        default="textures",
    )

    def invoke(self, context, event):
        from ..tools.model_utils import find_all_selected_model_groups

        img_path = bpy.path.abspath(context.scene.gtatools_img_path)
        if not img_path or not os.path.isfile(img_path):
            self.report({'ERROR'}, T("Укажите путь к .img архиву"))
            return {'CANCELLED'}
        groups = find_all_selected_model_groups()
        if not groups:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        # Pre-fill the dialog's shared-TXD widgets from the scene-level
        # unified toggle. Users configure once in the Unified Export
        # panel ("Общий TXD" + name); the dialog remembers that state
        # without them having to tick it again here.
        self.shared_txd = bool(getattr(
            context.scene, 'gtatools_export_all_txd_shared', False))
        self.shared_txd_name = getattr(
            context.scene, 'gtatools_export_all_txd_shared_name', 'textures') or 'textures'

        # Populate the WindowManager TXD plan collection. Pre-fill each row
        # with obj.inu.txd_name if set, otherwise fall back to base_name —
        # that matches the game's default "model and its TXD share a name".
        wm = context.window_manager
        wm.gtatools_txd_export_plan.clear()
        for base_name, models in groups.items():
            entry = wm.gtatools_txd_export_plan.add()
            entry.model_name = base_name
            entry.include = True
            src = models['DFF'] or models['LOD']
            prefilled = ''
            if src is not None and hasattr(src, 'inu'):
                prefilled = getattr(src.inu, 'txd_name', '') or ''
            entry.txd_name = prefilled or base_name
        wm.gtatools_txd_export_plan_index = 0

        return wm.invoke_props_dialog(self, width=460)

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        scn = context.scene

        info = layout.box()
        info.label(text=f"{T('IMG:')} {os.path.basename(bpy.path.abspath(scn.gtatools_img_path))}",
                   icon='PACKAGE')
        info.label(text=f"{T('Моделей:')} {len(wm.gtatools_txd_export_plan)}", icon='INFO')

        # Format pick moved here from the main panel — same scene
        # props the «To folder» path uses, so toggling here also
        # affects the next folder export and vice-versa.
        layout.label(text=T("Что экспортировать:"))
        row = layout.row(align=True)
        row.prop(scn, "gtatools_export_all_dff", text="DFF")
        row.prop(scn, "gtatools_export_all_col", text="COL")
        row.prop(scn, "gtatools_export_all_lod", text="LOD")
        row.prop(scn, "gtatools_export_all_txd", text="TXD")
        if scn.gtatools_export_all_col:
            row = layout.row(align=True)
            row.prop(scn, "gtatools_export_all_col_library",
                     text="", icon='PACKAGE')
            row.prop(scn, "gtatools_export_all_col_library_name",
                     text="", placeholder="collision")

        row = layout.row(align=True)
        row.prop(self, "shared_txd")
        sub = row.row(align=True)
        sub.active = self.shared_txd
        sub.prop(self, "shared_txd_name", text="")

        box = layout.box()
        box.active = not self.shared_txd
        box.label(text=T("TXD имя на модель:") if not self.shared_txd
                       else T("Общий TXD включён — список игнорируется"),
                  icon='TEXTURE')
        box.template_list(
            "GTATOOLS_UL_txd_export_plan", "",
            wm, "gtatools_txd_export_plan",
            wm, "gtatools_txd_export_plan_index",
            rows=min(10, max(4, len(wm.gtatools_txd_export_plan))),
        )

    def execute(self, context):
        from ..core.img import ImgWriter
        from ..core.dff import write_dff, GTA_SA_VERSION
        from ..core.col import write_col
        from ..tools.model_utils import find_all_selected_model_groups
        from ..tools.txd_export import export_txd, check_nvtt_available
        from .dff_export import build_dff_clump
        from .col_export import build_col_model, export_col_library

        img_path = bpy.path.abspath(context.scene.gtatools_img_path)
        if not img_path or not os.path.isfile(img_path):
            self.report({'ERROR'}, T("Укажите путь к .img архиву"))
            return {'CANCELLED'}

        model_groups = find_all_selected_model_groups()
        if not model_groups:
            self.report({'ERROR'}, T("Выделите меш объекты"))
            return {'CANCELLED'}

        # Unified toggles — same scene props that the «To folder» button
        # uses, so the DFF/COL/LOD/TXD row next to the export buttons
        # applies to «To IMG» as well. Previously this operator read a
        # separate ``gtatools_img_export_*`` set, which led to the
        # «only COL exports» surprise when users had DFF/TXD toggled off
        # somewhere out of sight.
        export_dff_flag = getattr(context.scene, 'gtatools_export_all_dff', True)
        export_col_flag = getattr(context.scene, 'gtatools_export_all_col', True)
        export_lod_flag = getattr(context.scene, 'gtatools_export_all_lod', True)
        export_txd_flag = getattr(context.scene, 'gtatools_export_all_txd', True)
        col_library = bool(getattr(context.scene, 'gtatools_export_all_col_library', False))
        col_library_name = getattr(context.scene, 'gtatools_export_all_col_library_name', '') or 'collision'
        use_gpu = check_nvtt_available(getattr(context.scene, 'gtatools_nvtt_path', ''))[0]

        wm = context.window_manager
        plan_by_name = {}
        for entry in wm.gtatools_txd_export_plan:
            plan_by_name[entry.model_name] = entry

        def _plan_entry(base):
            return plan_by_name.get(base)

        def _is_included(base):
            e = _plan_entry(base)
            return e.include if e is not None else True

        def _txd_for(base):
            e = _plan_entry(base)
            if self.shared_txd:
                return (self.shared_txd_name or 'textures').strip() or 'textures'
            if e is not None and e.txd_name.strip():
                return e.txd_name.strip()
            return base

        # Propagate the edited TXD name back to obj.inu.txd_name so later
        # IDE/IPL writes pick up the same value.
        for base_name, models in model_groups.items():
            if not _is_included(base_name):
                continue
            new_txd = _txd_for(base_name)
            for mt in ('DFF', 'LOD'):
                obj = models[mt]
                if obj is not None and hasattr(obj, 'inu'):
                    obj.inu.txd_name = new_txd

        results = []

        # Library COL bypasses the per-group COL loop: one multi-entry .col
        # is written once and stuffed into the archive under a shared name.
        library_col_objects = []
        write_col_per_group = export_col_flag
        if export_col_flag and col_library:
            write_col_per_group = False
            for _base, _models in model_groups.items():
                if _models['COL']:
                    library_col_objects.append(_models['COL'])

        # Progress estimate. Exact TXD-bucket count is only known after
        # the per-group pass, but counting each write op (LOD/DFF/COL per
        # group, one tick per bucket, plus the optional library COL)
        # gives a meaningful live progress.
        included_groups = [(b, m) for b, m in model_groups.items() if _is_included(b)]
        total_steps = 0
        for _base, _m in included_groups:
            if export_lod_flag and _m['LOD']: total_steps += 1
            if export_dff_flag and _m['DFF']: total_steps += 1
            if write_col_per_group and _m['COL']: total_steps += 1
        if export_txd_flag:
            total_steps += len({_txd_for(b) for b, m in included_groups
                                if m['DFF'] or m['LOD']})
        if col_library and library_col_objects:
            total_steps += 1
        total_steps = max(1, total_steps)

        wm.progress_begin(0, total_steps)
        step = 0

        def _tick(label=""):
            nonlocal step
            step += 1
            wm.progress_update(step)
            if label:
                context.workspace.status_text_set(
                    f"{T('Экспорт в IMG:')} {step}/{total_steps} {label}")

        context.workspace.status_text_set(T("Экспорт в IMG..."))

        try:
            with tempfile.TemporaryDirectory() as tmpdir, ImgWriter(img_path) as writer:
                # Bucket DFF/LOD objects by their resolved TXD name so every
                # bucket produces exactly one .txd containing merged textures.
                txd_buckets = defaultdict(list)
                encode_jobs: list = []  # (filename, callable_returning_bytes, label)

                for base_name, models in model_groups.items():
                    if not _is_included(base_name):
                        continue

                    if export_lod_flag and models['LOD']:
                        lod_name = 'LOD' + base_name
                        try:
                            clump = build_dff_clump([models['LOD']], version=GTA_SA_VERSION, col_model_name=lod_name)
                            encode_jobs.append((lod_name + '.dff', clump.to_bytes, f"{lod_name}.dff"))
                        except Exception as e:
                            results.append(f"{lod_name}.dff error: {e}")
                            _tick(f"{lod_name}.dff")

                    if export_dff_flag and models['DFF']:
                        try:
                            dff_objs = [models['DFF']]
                            for child in models['DFF'].children:
                                if child.type == 'EMPTY' and getattr(child, 'inu', None) and child.inu.type == '2DFX':
                                    dff_objs.append(child)
                            clump = build_dff_clump(dff_objs, version=GTA_SA_VERSION, col_model_name=base_name)
                            encode_jobs.append((base_name + '.dff', clump.to_bytes, f"{base_name}.dff"))
                        except Exception as e:
                            results.append(f"{base_name}.dff error: {e}")
                            _tick(f"{base_name}.dff")

                    if write_col_per_group and models['COL']:
                        try:
                            col_model = build_col_model([models['COL']], version=3, model_name=base_name)
                            encode_jobs.append((base_name + '.col', (lambda m=col_model: write_col([m])), f"{base_name}.col"))
                        except Exception as e:
                            results.append(f"{base_name}.col error: {e}")
                            _tick(f"{base_name}.col")

                    if export_txd_flag and (models['DFF'] or models['LOD']):
                        bucket_name = _txd_for(base_name)
                        for mt in ('DFF', 'LOD'):
                            if models[mt] is not None:
                                txd_buckets[bucket_name].append(models[mt])

                if encode_jobs:
                    enc_workers = min(os.cpu_count() or 4, 4)
                    with ThreadPoolExecutor(max_workers=enc_workers) as enc_pool:
                        futures = [(filename, label, enc_pool.submit(encoder)) for filename, encoder, label in encode_jobs]
                        for filename, label, fut in futures:
                            try:
                                data = fut.result()
                                status = writer.add(filename, data)
                                results.append(f"{filename} {status}")
                            except Exception as e:
                                results.append(f"{filename} error: {e}")
                            _tick(label)

                if export_txd_flag:
                    for txd_name, sources in txd_buckets.items():
                        if not sources:
                            continue
                        txd_path = os.path.join(tmpdir, txd_name + '.txd')
                        prev_active = context.view_layer.objects.active
                        prev_selected = [o for o in context.selected_objects]
                        try:
                            bpy.ops.object.select_all(action='DESELECT')
                            for src in sources:
                                src.select_set(True)
                            context.view_layer.objects.active = sources[0]
                            result, msg, _ = export_txd(txd_path, context, True, use_gpu)
                            if result == {'FINISHED'}:
                                with open(txd_path, 'rb') as f:
                                    status = writer.add(txd_name + '.txd', f.read())
                                results.append(f"{txd_name}.txd {status} ({len(sources)} models)")
                            else:
                                results.append(f"{txd_name}.txd: {msg}")
                        except Exception as e:
                            results.append(f"{txd_name}.txd error: {e}")
                        finally:
                            bpy.ops.object.select_all(action='DESELECT')
                            for o in prev_selected:
                                o.select_set(True)
                            if prev_active is not None:
                                context.view_layer.objects.active = prev_active
                        _tick(f"{txd_name}.txd")

                if col_library and library_col_objects:
                    lib_filename = f"{col_library_name}.col"
                    original_locations = {}
                    try:
                        lib_path = os.path.join(tmpdir, lib_filename)
                        for obj in library_col_objects:
                            original_locations[obj.name] = obj.location.copy()
                            obj.location = (0, 0, 0)
                        count = export_col_library(lib_path, library_col_objects, version=3)
                        with open(lib_path, 'rb') as f:
                            status = writer.add(lib_filename, f.read())
                        results.append(f"{lib_filename} {status} ({count} records)")
                    except Exception as e:
                        results.append(f"{col_library_name}.col error: {e}")
                    finally:
                        for obj in library_col_objects:
                            if obj.name in original_locations:
                                obj.location = original_locations[obj.name]
                    _tick(lib_filename)
        finally:
            # Always reset UI progress/status, even on unexpected error.
            wm.progress_end()
            context.workspace.status_text_set(None)

        from .. import _append_export_report
        _refresh_img_entries(context.scene, img_path)
        try:
            report_path = os.path.join(os.path.dirname(img_path), "_export_report.txt")
            rows = [f"IMG: {img_path}"]
            rows.extend(f"- {row}" for row in results)
            _append_export_report(report_path, "Export to IMG", rows)
        except Exception as e:
            self.report({'WARNING'}, f"{T('Не удалось записать отчёт:')} {e}")
        if results:
            preview = ', '.join(results[:6])
            more = f" (+{len(results) - 6})" if len(results) > 6 else ""
            self.report({'INFO'}, f"IMG: {preview}{more}")
            # Common pitfall ("новый DFF не появляется в игре"): the
            # archive directory updates but external IMG editors / game
            # caches may keep showing the old entry until a Rebuild
            # Archive pass. Status-bar shows the *latest* report — make
            # this the visible one; the file list above stays accessible
            # via the report-log click-through.
            self.report(
                {'INFO'},
                T("Rebuild Archive в IMG-туле — иначе игра подтянет старую запись"))
        else:
            self.report({'WARNING'}, T("IMG: нет результатов экспорта"))
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_refresh_img_list,
    GTATOOLS_OT_extract_resources,
    GTATOOLS_OT_import_from_img,
    GTATOOLS_OT_remove_from_img,
    GTATOOLS_OT_export_to_img,
)
