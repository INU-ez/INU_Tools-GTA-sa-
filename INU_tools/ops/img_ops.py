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
from ..tools.compat import safe_icon, inu_icon
# ──────────────────────────── helpers ─────────────────────────────────

def _read_png_dimensions(path):
    """Read width × height from a PNG file's IHDR chunk. Returns (0, 0)
    if the file isn't a valid PNG. Used by Extract Resources to dedupe
    by resolution rather than by raw-vs-compressed byte count, which
    was meaningless (raw RGBA is almost always larger than its PNG)."""
    try:
        with open(path, 'rb') as f:
            sig = f.read(8)
            if sig != b'\x89PNG\r\n\x1a\n':
                return 0, 0
            f.read(8)  # IHDR length(4) + chunk-type "IHDR"(4)
            w = int.from_bytes(f.read(4), 'big')
            h = int.from_bytes(f.read(4), 'big')
            return w, h
    except (OSError, ValueError):
        return 0, 0


def _refresh_img_entries(scn, img_path):
    """Directly refresh IMG entries list."""
    scn.inu_settings.gtatools_img_entries.clear()
    try:
        from ..core.img import read_directory
        entries = read_directory(img_path)
        for entry in entries:
            item = scn.inu_settings.gtatools_img_entries.add()
            item.name = entry.name
        scn.inu_settings.gtatools_img_entries_index = max(0, len(entries) - 1)
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
        img_path = bpy.path.abspath(scn.inu_settings.gtatools_img_path)
        if not img_path or not os.path.isfile(img_path):
            self.report({'WARNING'}, T("Укажите путь к IMG"))
            return {'CANCELLED'}

        scn.inu_settings.gtatools_img_entries.clear()
        try:
            entries = read_directory(img_path)
            for entry in entries:
                item = scn.inu_settings.gtatools_img_entries.add()
                item.name = entry.name
            scn.inu_settings.gtatools_img_entries_index = max(0, len(entries) - 1)
            self.report({'INFO'}, f"{T('Файлов:')} {len(scn.inu_settings.gtatools_img_entries)}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}


class GTATOOLS_OT_extract_resources(bpy.types.Operator):
    """Извлечь все DFF, COL и текстуры из IMG-архивов GTA SA.

    Кеш создаётся в папке .inu_cache/ рядом с твоим .blend файлом,
    поэтому сцену нужно сначала сохранить — без сохранённого .blend
    кешу некуда лечь, и оператор откажется работать.

    Региональный фильтр (если выбран) сужает извлечение до TXD/моделей,
    реально используемых в этом регионе по IDE/IPL — экономит минуты
    на больших картах. ALL = извлечь всё"""
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

        game_root = bpy.path.abspath(scene.inu_settings.gtatools_game_root)

        if not game_root or not os.path.isdir(game_root):
            self.report({'ERROR'}, T("Укажите корневую папку GTA SA"))
            return {'CANCELLED'}

        from ..core.gta_dat import find_all_resources
        from ..core.img import read_directory
        from ..core.ide import read_ide
        from ..core.ipl import read_ipl

        info = find_all_resources(game_root)

        # Collect all IMG archives — four sources, dedup by absolute path:
        #   1. Standard vanilla path: <game>/models/gta3.img
        #   2. Paths declared in gta.dat / gta_int.dat (via find_all_resources)
        #   3. User-set fallback (`gtatools_img_path`)
        #   4. Anything else with a `.img` extension anywhere under game_root —
        #      catches custom installs, mod archives, additional `playerN.img`,
        #      `cutscene.img`, district-split mods, etc. that aren't declared
        #      in gta.dat.
        img_paths = []

        def _add(path: str):
            if not path:
                return
            absp = os.path.normcase(os.path.abspath(path))
            if not os.path.isfile(path):
                return
            for existing in img_paths:
                if os.path.normcase(os.path.abspath(existing)) == absp:
                    return
            img_paths.append(path)

        _add(os.path.join(game_root, 'models', 'gta3.img'))
        for p in info.img_paths:
            _add(p)
        _add(bpy.path.abspath(scene.inu_settings.gtatools_img_path))

        # Recursive fallback — walk the whole game_root for `.img` files. Done
        # AFTER the priority sources so anything declared in gta.dat keeps its
        # position; only "extra" archives get appended at the end. Skip common
        # cache / hidden dirs to avoid scanning a 50-GB user backup folder.
        _SKIP_DIRS = {'.git', '.svn', '__pycache__', '.inu_cache', 'node_modules'}
        extra_count = 0
        for dirpath, dirnames, filenames in os.walk(game_root):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            for fn in filenames:
                if fn.lower().endswith('.img'):
                    full = os.path.join(dirpath, fn)
                    before = len(img_paths)
                    _add(full)
                    if len(img_paths) > before:
                        extra_count += 1
        # Always log the final IMG list — helps users diagnose why some
        # archives weren't picked up (path typos / permission errors / etc.).
        print(f"\n[Extract Resources] game_root = {game_root}")
        print(f"[Extract Resources] {extra_count} extra .img file(s) via recursive walk")
        print(f"[Extract Resources] {len(img_paths)} IMG archive(s) to process:")
        for ip in img_paths:
            print(f"  - {ip}")
        print()

        if not img_paths:
            self.report({'ERROR'}, T("Не найден IMG архив"))
            return {'CANCELLED'}

        # Region filter — when picked, walk matching IPLs (BOTH text +
        # binary-from-IMG) to gather used model_ids, look those up in
        # IDE files to get TXD names, then only extract those TXDs.
        # Saves minutes on large extracts.
        #
        # Why scan binary IPLs too: vanilla SA places a lot of district
        # geometry via binary IPLs inside gta3.img (countn1.ipl,
        # countryS.ipl, …), and these aren't declared in gta.dat. The
        # previous version only walked text IPLs from gta.dat — for
        # COUNTRY that misses ~half of placements, which dropped the
        # corresponding TXDs from ``needed_txds`` and left them filtered.
        region = getattr(scene.inu_settings, 'gtatools_map_region', 'ALL')
        needed_txds = None  # None = "extract everything"
        if region != 'ALL':
            from ..core.ipl import _read_binary_ipl

            def _ipl_matches_region(path: str) -> bool:
                parts = path.replace('\\', '/').upper().split('/')
                for i, part in enumerate(parts):
                    if part == 'MAPS' and i + 1 < len(parts):
                        return parts[i + 1] == region
                name = path.replace('\\', '/').rsplit('/', 1)[-1].upper()
                return name.startswith(region)

            # Binary IPLs in gta3.img don't follow the folder-name region
            # picker. Vanilla SA filenames use abbreviated prefixes:
            # COUNTRY → countn*, country*, countxx; LA → la*; SF → sf*;
            # VEGAS → vegas*. Map the user-facing region label to the
            # filename prefixes the IMG actually contains.
            _BIN_IPL_PREFIXES = {
                'COUNTRY': ('COUNT',),    # countn*, country*, countxx, ...
                'LA':      ('LA',),
                'SF':      ('SF',),
                'VEGAS':   ('VEGAS',),
            }
            bin_ipl_prefixes = _BIN_IPL_PREFIXES.get(region, (region,))

            # Honour explicit binary-IPL toggles if the user curated them
            # (gtatools_binary_ipls is a per-scene checklist that the
            # sidebar's «Binary IPLs» panel surfaces).
            bi_entries = scene.inu_settings.gtatools_binary_ipls
            bi_enabled = {i.name.lower() for i in bi_entries if i.enabled}
            bi_use_selection = len(bi_entries) > 0

            def _bin_ipl_matches(name_lower: str) -> bool:
                if bi_use_selection:
                    return name_lower in bi_enabled
                upper = name_lower.upper()
                return any(upper.startswith(p) for p in bin_ipl_prefixes)

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

            # Pass 1: text IPLs from gta.dat
            text_ipl_count = 0
            for p in info.ipl_paths:
                if os.path.isfile(p) and _ipl_matches_region(p):
                    try:
                        ipl = read_ipl(p)
                        for inst in ipl.instances:
                            used_ids.add(inst.model_id)
                        text_ipl_count += 1
                    except Exception:
                        pass

            # Pass 2: binary IPLs inside IMG archives. Read the directory,
            # filter by name prefix or user selection, parse the bnry
            # blob to pull instance model_ids.
            bin_ipl_count = 0
            from ..core.img import extract_file
            for ip in img_paths:
                try:
                    for e in read_directory(ip):
                        low = e.name.lower()
                        if not low.endswith('.ipl'):
                            continue
                        if not _bin_ipl_matches(low):
                            continue
                        try:
                            ipl_data = extract_file(ip, e.name)
                            if ipl_data and ipl_data[:4] == b'bnry':
                                ipl_parsed = _read_binary_ipl(ipl_data)
                                for inst in ipl_parsed.instances:
                                    used_ids.add(inst.model_id)
                                bin_ipl_count += 1
                        except Exception:
                            pass
                except Exception:
                    pass

            print(f"[Extract Resources] region={region}: scanned "
                  f"{text_ipl_count} text IPLs + {bin_ipl_count} binary IPLs, "
                  f"{len(used_ids)} unique model_ids")

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
        # Per-reason skip counters — updated from worker threads, gated
        # by ``counters_lock`` in _work. Final report shows the breakdown
        # so the user can see WHY textures are missing (region filter vs
        # parse error vs degenerate header vs already-extracted-larger).
        self._skip_reasons = {
            'archive_filtered': 0,  # TXD archive didn't match region IPL
            'parse_error': 0,       # read_txd raised on the archive
            'no_name': 0,           # texture name was empty/all-null
            'zero_dims': 0,         # width or height was 0
            'no_pixels': 0,         # pixel data was empty
            'dedup': 0,             # existing PNG already at >= resolution
            'write_error': 0,       # _write_png raised
        }

        from ..tools.profiler import Profiler
        self._profiler = Profiler(
            f"Extract Resources ({region})",
            enabled=bool(getattr(scene.inu_settings, 'gtatools_profile_enabled', False)),
        )

        self._gen = self._work(context)
        wm = context.window_manager
        wm.progress_begin(0, max(txd_total, 1))
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Извлечение ресурсов..."))
        return {'RUNNING_MODAL'}

    def _work(self, context):
        from ..core.img import ImgReader, safe_filename
        from ..core.txd import read_txd
        from .. import _write_png
        import threading

        cache_dir = self._cache_dir
        tex_dir = self._tex_dir
        needed_txds = self._needed_txds
        prof = self._profiler

        # Counters lock protects self._tex_count / self._skipped updates
        # from worker threads. errors_lock serializes appends to the shared
        # error/skip logs so concurrent failures don't interleave mid-line.
        counters_lock = threading.Lock()
        errors_lock = threading.Lock()
        err_log_path = os.path.join(cache_dir, '_txd_errors.log')
        skip_log_path = os.path.join(cache_dir, '_extract_skipped.log')

        # Reset skip log at start of each extraction so the user always
        # sees results from this run, not a growing all-time history.
        try:
            if os.path.isfile(skip_log_path):
                os.remove(skip_log_path)
        except Exception:
            pass

        def _log_err(msg):
            try:
                with errors_lock, open(err_log_path, 'a', encoding='utf-8') as lf:
                    lf.write(msg + '\n')
            except Exception:
                pass

        def _log_skip(reason: str, tex_name: str, source: str, extra: str = ""):
            """Increment counter + record one line per skipped texture."""
            with counters_lock:
                self._skip_reasons[reason] = self._skip_reasons.get(reason, 0) + 1
                self._skipped += 1
            try:
                with errors_lock, open(skip_log_path, 'a', encoding='utf-8') as lf:
                    lf.write(f"{reason:18s} | {tex_name[:40]:40s} | "
                             f"{source[:30]:30s} | {extra}\n")
            except Exception:
                pass

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
                _log_err(f"{entry_name}: {e}")
                _log_skip('parse_error', '*', entry_name, str(e))
                return

            for tex in textures:
                raw_name = (tex.name or '').rstrip('\x00')
                # tex.name comes from a TXD that may carry garbage bytes —
                # `_read_str32` decodes with errors='replace' so non-ASCII
                # turns into '?'. Sanitize before forming a filesystem path
                # so corrupt archives don't crash the writer on Windows.
                name = safe_filename(raw_name)
                if not name:
                    _log_skip('no_name', raw_name or '<empty>', entry_name)
                    continue
                if tex.width == 0 or tex.height == 0:
                    _log_skip('zero_dims', name, entry_name,
                              f"{tex.width}x{tex.height}")
                    continue
                if not tex.pixels:
                    _log_skip('no_pixels', name, entry_name,
                              f"{tex.width}x{tex.height}")
                    continue

                png_path = os.path.join(tex_dir, name + '.png')

                # Dedup: read existing PNG's actual resolution from its
                # IHDR. Skip only when the file on disk is at least as
                # large as the new texture in BOTH dimensions — protects
                # against a downscale variant from another IMG overwriting
                # a higher-res original. The previous comparison of
                # raw-RGBA bytes vs compressed PNG bytes was meaningless.
                if os.path.isfile(png_path):
                    ew, eh = _read_png_dimensions(png_path)
                    if ew >= tex.width and eh >= tex.height:
                        _log_skip('dedup', name, entry_name,
                                  f"existing {ew}x{eh} >= new {tex.width}x{tex.height}")
                        continue

                try:
                    with prof.stage('_write_png'):
                        _write_png(png_path, tex.pixels, tex.width, tex.height)
                    with counters_lock:
                        self._tex_count += 1
                except Exception as e:
                    _log_err(f"{entry_name}/{name}: {e}")
                    _log_skip('write_error', name, entry_name, str(e))

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
                    # Track on self so _cleanup() can tear it down on ESC
                    # — otherwise worker threads would keep churning after
                    # the operator returns CANCELLED.
                    self._pool = pool
                    submitted = 0
                    try:
                        for entry in img.entries:
                            low = entry.name.lower()
                            if not low.endswith('.txd'):
                                continue
                            if needed_txds is not None and low[:-4] not in needed_txds:
                                # Region filter excluded this TXD — log
                                # at archive level so the user can see if
                                # their region pick was too narrow.
                                _log_skip('archive_filtered', '*', entry.name,
                                          f"region={self._region}")
                                continue

                            with prof.stage('img.read (TXD bytes)'):
                                txd_data = img.read(entry.name)
                            if not txd_data:
                                _log_skip('parse_error', '*', entry.name,
                                          "empty read")
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
                        self._pool = None
            except Exception as _ip_err:
                # Don't let one bad archive abort the whole extraction —
                # but DO surface the failure so users can diagnose.
                # Silent swallowing here previously masked a parser bug
                # that made every Silent Hill TC IMG appear to extract
                # zero files for over a year.
                import traceback as _tb
                print(f"\n[Extract Resources] FAILED on {ip}:")
                _tb.print_exc()
                print()

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

                # Build breakdown — surface only the categories that
                # actually fired this run, otherwise the message is noise.
                # Detailed per-texture log lives in _extract_skipped.log.
                reasons = {k: v for k, v in self._skip_reasons.items() if v}
                breakdown = ""
                if reasons:
                    parts = ", ".join(f"{k}={v}" for k, v in
                                      sorted(reasons.items(), key=lambda kv: -kv[1]))
                    breakdown = f" [{parts}]"
                # Print the full breakdown to the system console so it's
                # easy to copy-paste into a bug report; the operator
                # status line keeps a short version for the header bar.
                full_msg = (f"DFF: {self._dff_count}, COL: {self._col_count}, "
                            f"{T('Извлечено текстур:')} {self._tex_count}, "
                            f"{T('пропущено:')} {self._skipped}{breakdown}")
                print(f"[Extract Resources] {full_msg}")
                if reasons:
                    print(f"[Extract Resources] подробности по каждой текстуре: "
                          f"{os.path.join(self._cache_dir, '_extract_skipped.log')}")
                self.report({'INFO'}, full_msg)
                return {'FINISHED'}

        wm.progress_update(self._txd_progress)
        context.workspace.status_text_set(
            f"TXD: {self._txd_progress}/{self._txd_total} | "
            f"DFF: {self._dff_count} COL: {self._col_count}")

        return {'RUNNING_MODAL'}

    def _cleanup(self, context):
        # Order matters on ESC: kill the pool first so its workers stop
        # picking up new tasks, then close the generator (its finally
        # block clears self._pool). cancel_futures requires Python 3.9+
        # which Blender 4.2 satisfies.
        pool = getattr(self, '_pool', None)
        if pool is not None:
            try:
                pool.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass
            self._pool = None

        gen = getattr(self, '_gen', None)
        if gen is not None:
            try:
                gen.close()
            except Exception:
                pass
            self._gen = None

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
        img_path = bpy.path.abspath(scene.inu_settings.gtatools_img_path)
        ide_path = bpy.path.abspath(scene.inu_settings.gtatools_ide_path)
        ipl_path = bpy.path.abspath(scene.inu_settings.gtatools_ipl_path)
        game_root = bpy.path.abspath(scene.inu_settings.gtatools_game_root)

        if not img_path or not os.path.isfile(img_path):
            self.report({'ERROR'}, T("Укажите путь к IMG архиву в INU Tools"))
            return {'CANCELLED'}

        # Auto-detect game from the IMG archive's format (VER2 magic →
        # SA, sibling .dir present → VC fallback). Auto-flips scene
        # game on fresh scenes, otherwise warns about mismatch so the
        # user can manually switch the GTA Tools tab.
        try:
            from ..core import game_versions as gv
            detected = gv.detect_game_from_img(img_path)
            switched = gv.maybe_set_game_from_import(scene, detected)
            if not switched:
                warn = gv.check_game_mismatch_warning(scene, detected)
                if warn:
                    self.report({'WARNING'}, warn)
        except Exception:
            pass

        ide_models = {}
        instances = []

        use_gta_dat = getattr(scene.inu_settings, 'gtatools_img_use_gta_dat', False)
        skip_lod = getattr(scene.inu_settings, 'gtatools_img_skip_lod', False)
        load_txd = getattr(scene.inu_settings, 'gtatools_img_load_txd', True)

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
                                    _sfx_col = getattr(scene.inu_settings, 'gtatools_suffix_col', '_COL')
                                    _pfx_col = getattr(scene.inu_settings, 'gtatools_prefix_col', '')
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

                _sfx_dff = getattr(scene.inu_settings, 'gtatools_suffix_dff', '_DFF')
                _sfx_lod = getattr(scene.inu_settings, 'gtatools_suffix_lod', '_LOD')
                _pfx_dff = getattr(scene.inu_settings, 'gtatools_prefix_dff', '')
                _pfx_lod = getattr(scene.inu_settings, 'gtatools_prefix_lod', '')
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

        img_path = bpy.path.abspath(context.scene.inu_settings.gtatools_img_path)
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

        img_path = bpy.path.abspath(context.scene.inu_settings.gtatools_img_path)
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
        info.label(text=f"{T('IMG:')} {os.path.basename(bpy.path.abspath(scn.inu_settings.gtatools_img_path))}",
                   **inu_icon(safe_icon('PACKAGE')))
        info.label(text=f"{T('Моделей:')} {len(wm.gtatools_txd_export_plan)}", **inu_icon(safe_icon('INFO')))

        # Format pick moved here from the main panel — same scene
        # props the «To folder» path uses, so toggling here also
        # affects the next folder export and vice-versa.
        layout.label(text=T("Что экспортировать:"))
        row = layout.row(align=True)
        row.prop(scn, "gtatools_export_all_dff", text="DFF")
        row.prop(scn, "gtatools_export_all_col", text="COL")
        row.prop(scn, "gtatools_export_all_lod", text="LOD")
        row.prop(scn, "gtatools_export_all_txd", text="TXD")
        if scn.inu_settings.gtatools_export_all_col:
            row = layout.row(align=True)
            row.prop(scn, "gtatools_export_all_col_library",
                     text="", **inu_icon(safe_icon('PACKAGE')))
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
                  **inu_icon(safe_icon('TEXTURE')))
        box.template_list(
            "GTATOOLS_UL_txd_export_plan", "",
            wm, "gtatools_txd_export_plan",
            wm, "gtatools_txd_export_plan_index",
            rows=min(10, max(4, len(wm.gtatools_txd_export_plan))),
        )

    def execute(self, context):
        from ..core.img import ImgWriter
        from ..core.dff import GTA_SA_VERSION
        from ..core.col import write_col
        from ..tools.model_utils import find_all_selected_model_groups
        from ..tools.txd_export import export_txd
        from .dff_export import build_dff_clump
        from .col_export import build_col_model, export_col_library

        img_path = bpy.path.abspath(context.scene.inu_settings.gtatools_img_path)
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
        export_dff_flag = getattr(context.scene.inu_settings, 'gtatools_export_all_dff', True)
        export_col_flag = getattr(context.scene.inu_settings, 'gtatools_export_all_col', True)
        export_lod_flag = getattr(context.scene.inu_settings, 'gtatools_export_all_lod', True)
        export_txd_flag = getattr(context.scene.inu_settings, 'gtatools_export_all_txd', True)
        col_library = bool(getattr(context.scene.inu_settings, 'gtatools_export_all_col_library', False))
        col_library_name = getattr(context.scene.inu_settings, 'gtatools_export_all_col_library_name', '') or 'collision'
        empty_col_flag = bool(getattr(context.scene.inu_settings, 'gtatools_export_all_col_empty', False))
        backend = getattr(context.scene.inu_settings, 'gtatools_dxt_backend', 'numpy')

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

        # Pick the DFF RW version + IMG archive version once for this
        # whole bulk export — scene's gtatools_game drives III/VC/SA
        # dispatch (RW 3.3/3.5/3.6 for DFF, COL v1/v2/v3, IMG VER1/VER2).
        from .dff_export import _resolve_export_version
        from .col_export import _resolve_col_version
        dff_rw_version = _resolve_export_version(context)
        col_version = _resolve_col_version(context)
        dff_target_platform = getattr(context.scene.inu_settings,
                                      'gtatools_platform', 'PC')

        # Progress estimate. Exact TXD-bucket count is only known after
        # the per-group pass, but counting each write op (LOD/DFF/COL per
        # group, one tick per bucket, plus the optional library COL)
        # gives a meaningful live progress.
        included_groups = [(b, m) for b, m in model_groups.items() if _is_included(b)]
        total_steps = 0
        for _base, _m in included_groups:
            if export_lod_flag and _m['LOD']: total_steps += 1
            if export_dff_flag and _m['DFF']: total_steps += 1
            if write_col_per_group and (_m['COL'] or empty_col_flag): total_steps += 1
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

        # IMG archive version: SA writes VER2 (single .img), III/VC
        # write VER1 (split .dir + .img). Read game off the scene via
        # GameProfile.img_version — keeps the existing op signature
        # untouched while still routing III/VC users to the right
        # archive layout.
        from ..core import game_versions as gv
        _img_version = gv.profile_for(
            gv.game_of_scene(context.scene)).img_version

        try:
            with tempfile.TemporaryDirectory() as tmpdir, ImgWriter(img_path, version=_img_version) as writer:
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
                            clump = build_dff_clump([models['LOD']], version=dff_rw_version, col_model_name=lod_name)
                            if dff_target_platform == 'MOBILE':
                                for g in clump.geometries:
                                    if not g.raw_native_data_plg:
                                        g.is_native_ogl = True
                                clump.is_mobile = True
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
                            clump = build_dff_clump(dff_objs, version=dff_rw_version, col_model_name=base_name)
                            if dff_target_platform == 'MOBILE':
                                for g in clump.geometries:
                                    if not g.raw_native_data_plg:
                                        g.is_native_ogl = True
                                clump.is_mobile = True
                            encode_jobs.append((base_name + '.dff', clump.to_bytes, f"{base_name}.dff"))
                        except Exception as e:
                            results.append(f"{base_name}.dff error: {e}")
                            _tick(f"{base_name}.dff")

                    if write_col_per_group and (models['COL'] or empty_col_flag):
                        try:
                            col_src = [models['COL']] if models['COL'] else []
                            col_model = build_col_model(col_src, version=col_version, model_name=base_name, empty=empty_col_flag)
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
                            result, msg, _ = export_txd(txd_path, context, True, backend=backend)
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
                        count = export_col_library(lib_path, library_col_objects, version=col_version, empty=empty_col_flag)
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


