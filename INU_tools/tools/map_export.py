# INU_tools.tools.map_export — unified scene → IPL + IDE + (optional) DFF / COL / TXD
#
# Orchestrates the individual format exporters so a user can publish a
# whole city district with one click. Per-object IDs, draw distance and
# TXD names are taken from `obj.inu` custom properties (same props that
# back the separate IDE/IPL exports).
#
# Auto-split: for very large scenes (50k+ DFF objects) a single district
# is impractical (long IPL files, monolithic TXD). Auto-split mode bins
# DFFs by their XY origin into a grid of `cell_size`-meter cells; each
# non-empty cell becomes its own subdirectory with its own IDE/IPL/COL/TXD.
# Game-side this just means loading several IPLs instead of one — engine
# behavior is identical.

import math
import os
from dataclasses import dataclass

import bpy

from .model_utils import get_model_type
from .compat import safe_icon, inu_icon
from .. import T
from typing import Dict, List, Optional, Set, Tuple


# ──────────────────────────── grouping ────────────────────────────────

@dataclass
class MapGroup:
    """One DFF → (LOD, COL) group inferred from object naming."""
    base: str
    # Forward-string refs — без future-import dataclass eager-eval'нул бы
    # bpy.types.Object на class-creation, что роняет unit-тесты со
    # стабленным bpy. Аннотации кокласса всё равно не используются как
    # runtime-типы (dataclass только читает имена полей).
    dff: "bpy.types.Object"
    lod: 'Optional["bpy.types.Object"]' = None
    col_objects: list = None   # list of COL/SHA meshes

    def __post_init__(self):
        if self.col_objects is None:
            self.col_objects = []


def collect_map_groups(objects) -> List[MapGroup]:
    """Walk `objects` and build MapGroup records keyed by base name.

    A group is created for every DFF mesh; any LOD / COL / SHA objects
    sharing that base name are attached to the group.
    """
    dffs: Dict[str, bpy.types.Object] = {}
    lods: Dict[str, bpy.types.Object] = {}
    cols: Dict[str, list] = {}

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

    groups: List[MapGroup] = []
    for base, dff in dffs.items():
        groups.append(MapGroup(
            base=base,
            dff=dff,
            lod=lods.get(base),
            col_objects=cols.get(base, []),
        ))
    return groups


# ──────────────────────────── auto-split grid ─────────────────────────

def compute_grid_cells(groups: List[MapGroup], cell_size: float
                       ) -> Dict[Tuple[int, int], List[MapGroup]]:
    """Bin map groups by XY cell index (grid origin = world (0,0)).

    Cell index for a group is taken from the DFF object's world origin.
    LOD/COL members travel with their DFF — they are not assigned
    independently. Returns a dict keyed by (cx, cy).
    """
    if cell_size <= 0:
        return {(0, 0): list(groups)}
    cells: Dict[Tuple[int, int], List[MapGroup]] = {}
    for g in groups:
        loc = g.dff.matrix_world.translation
        cx = int(math.floor(loc.x / cell_size))
        cy = int(math.floor(loc.y / cell_size))
        cells.setdefault((cx, cy), []).append(g)
    return cells


def format_cell_name(base_name: str, cx: int, cy: int) -> str:
    """Return a filesystem-safe sub-district name for a grid cell.

    Negative indices use 'm' (minus) prefix so the name does not start
    with a dash, which some tools/IPL parsers dislike.
    """
    def _fmt(n: int) -> str:
        return f"m{abs(n)}" if n < 0 else f"{n}"
    return f"{base_name}_x{_fmt(cx)}_y{_fmt(cy)}"


# ──────────────────────────── adaptive grid (quadtree) ────────────────

def compute_adaptive_cells(groups: List[MapGroup], *,
                           max_per_cell: int = 200,
                           min_cell_size: float = 16.0
                           ) -> Dict[tuple, List[MapGroup]]:
    """Density-aware quadtree subdivision: dense regions get small cells,
    sparse regions stay one big cell, every leaf cell holds at most
    ``max_per_cell`` DFFs (best-effort — see floor below).

    Starts with one cell covering the world-XY bbox of all groups and
    recursively splits 2×2 any cell exceeding ``max_per_cell``. Uses
    the DFF object's world-origin XY for binning; LOD/COL members
    travel with their DFF (same contract as :func:`compute_grid_cells`).

    Two safety floors prevent runaway recursion:

    * ``min_cell_size`` — cell side length below which we stop splitting
      even if the cell is over budget. Protects against pathological
      cases where many DFFs share an XY origin (e.g. stacked vertical
      buildings).
    * Implicit depth — cells are keyed by a tuple of quadrant indices
      ``(0=SW, 1=SE, 2=NW, 3=NE)`` so the path encodes the recursion
      history. The ``min_cell_size`` floor caps depth around
      ``log2(world_extent / min_cell_size)``.

    Returns a dict keyed by quadrant-path tuples (e.g. ``(0, 1, 3)`` for
    «SW → SE → NE» three subdivisions deep). The empty tuple ``()``
    means a single, unsplit cell holding everything — happens when the
    population fits in ``max_per_cell`` from the start.
    """
    if not groups:
        return {}

    locs = [g.dff.matrix_world.translation for g in groups]
    xs = [loc.x for loc in locs]
    ys = [loc.y for loc in locs]
    # Pad the bbox slightly so points exactly on the max edge stay
    # strictly inside the cell after midpoint splits (otherwise they
    # could escape into a non-existent neighbour cell on the boundary).
    pad = max(0.5, (max(xs) - min(xs) + max(ys) - min(ys)) * 1e-6)
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad

    cells: Dict[tuple, List[MapGroup]] = {}

    def _split(g_list, x0, x1, y0, y1, path):
        cell_size = min(x1 - x0, y1 - y0)
        if (len(g_list) <= max_per_cell
                or cell_size <= min_cell_size):
            cells[path] = g_list
            return
        xm = (x0 + x1) * 0.5
        ym = (y0 + y1) * 0.5
        buckets = [[], [], [], []]
        for g in g_list:
            loc = g.dff.matrix_world.translation
            qx = 1 if loc.x >= xm else 0
            qy = 1 if loc.y >= ym else 0
            buckets[qy * 2 + qx].append(g)
        for q, sub in enumerate(buckets):
            if not sub:
                continue
            qx = q & 1
            qy = (q >> 1) & 1
            sub_x0 = xm if qx else x0
            sub_x1 = x1 if qx else xm
            sub_y0 = ym if qy else y0
            sub_y1 = y1 if qy else ym
            _split(sub, sub_x0, sub_x1, sub_y0, sub_y1, path + (q,))

    _split(list(groups), x0, x1, y0, y1, ())
    return cells


def format_adaptive_cell_name(base_name: str, path: tuple) -> str:
    """Encode a quadtree path as a filesystem-safe district suffix.

    The empty path (single root cell) returns the bare ``base_name`` so
    a small scene that doesn't need subdivision doesn't sprout a noisy
    ``_q0`` directory. Otherwise the suffix is ``_q`` followed by the
    quadrant indices joined: ``_q0123`` means «SW → SE → NW → NE».
    """
    if not path:
        return base_name
    return f"{base_name}_q{''.join(str(q) for q in path)}"


def _build_top_collection_lookup(scene) -> dict:
    """Map every collection name in the scene to its topmost user
    collection (the one directly under ``scene.collection``).

    Blender's data API does not expose a parent pointer on
    :class:`bpy.types.Collection`, so we walk down once from the scene
    root and remember which top-level branch each descendant belongs
    to. The result is keyed by collection *name* — collection refs
    are tracked separately by Blender so identity-keying is unsafe
    across operator invocations.
    """
    top_map: dict = {}

    def _walk(top, current):
        top_map[current.name] = top
        for child in current.children:
            _walk(top, child)

    for top in scene.collection.children:
        _walk(top, top)
    return top_map


def compute_collection_cells(groups: List[MapGroup], scene
                             ) -> Dict[str, List[MapGroup]]:
    """Bin map groups by the name of their topmost user collection.

    Picks each DFF object's first :attr:`bpy.types.Object.users_collection`
    membership (Blender's «main collection» order); then maps that
    collection to its top-level ancestor via
    :func:`_build_top_collection_lookup`. Groups whose DFF lives only
    in the scene root collection (or in no collection at all) land
    under the bin name ``"unsorted"``.

    Prints a one-line summary to the system console — handy for
    diagnosing «everything fell into one bucket» issues without
    sprinkling debug calls in the operator.
    """
    top_map = _build_top_collection_lookup(scene)
    cells: Dict[str, List[MapGroup]] = {}
    for g in groups:
        bucket: Optional[str] = None
        for coll in getattr(g.dff, 'users_collection', ()) or ():
            top = top_map.get(coll.name)
            if top is not None:
                bucket = top.name
                break
        if bucket is None:
            bucket = "unsorted"
        cells.setdefault(bucket, []).append(g)
    return cells


# ──────────────────────────── selection resolver ──────────────────────

def _gather_outliner_selected_collections(context) -> list:
    """Return all Collections currently selected in any outliner area.

    ``context.selected_ids`` only reports the outliner's selection when
    *that outliner* is the active region — so calling it from a sidebar
    panel button (or after a file dialog stole focus) often returns just
    the active collection, missing the other Ctrl-clicked ones. We work
    around that by scanning every screen area, locating outliners, and
    re-reading ``selected_ids`` under each one's :func:`temp_override`.

    Filters outliners to ``display_mode == 'VIEW_LAYER'`` so a Properties
    Editor's tiny outliner pane doesn't steal the selection.

    Returns a deduplicated list preserving outliner order.
    """
    found: list = []
    seen: set = set()

    def _push(coll):
        key = coll.name
        if key not in seen:
            seen.add(key)
            found.append(coll)

    # Direct read first — costs nothing and works when the operator
    # was triggered with the outliner as active region.
    try:
        for did in context.selected_ids or ():
            if isinstance(did, bpy.types.Collection):
                _push(did)
    except AttributeError:
        pass

    # Then sweep every outliner on every open window so Ctrl-click
    # selections survive the «click sidebar button» workflow. We pass
    # both ``area`` and ``region`` to ``temp_override`` — without the
    # WINDOW region some Blender builds skip the outliner-specific
    # context callback and ``selected_ids`` ends up empty even though
    # the area is correctly overridden.
    try:
        windows = list(context.window_manager.windows)
    except Exception:
        windows = []

    for win in windows:
        screen = getattr(win, 'screen', None)
        if screen is None:
            continue
        for area in screen.areas:
            if area.type != 'OUTLINER':
                continue
            space = area.spaces.active if area.spaces else None
            display_mode = getattr(space, 'display_mode', None)
            if display_mode and display_mode != 'VIEW_LAYER':
                continue
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            try:
                kwargs = {'window': win, 'area': area}
                if region is not None:
                    kwargs['region'] = region
                with context.temp_override(**kwargs):
                    for did in bpy.context.selected_ids or ():
                        if isinstance(did, bpy.types.Collection):
                            _push(did)
            except (AttributeError, RuntimeError, TypeError):
                pass

    return found


def _resolve_export_objects(context) -> list:
    """Pick the mesh objects to export based on the user's outliner state.

    Resolution order:
      1. **Two or more collections selected in the outliner** — gather
         their nested meshes via ``Collection.all_objects``. This wins
         over viewport selection so «select 2 collections in outliner +
         click Export Map in sidebar» does the obvious thing.
      2. Currently selected mesh objects (``context.selected_objects``).
      3. Single selected collection (or active collection fallback) —
         gather its meshes.
      4. Last resort: every mesh in the scene.
    """
    outliner_colls = _gather_outliner_selected_collections(context)

    def _gather(colls):
        gathered: Dict[int, bpy.types.Object] = {}
        for coll in colls:
            for obj in coll.all_objects:
                if obj.type == 'MESH':
                    gathered[id(obj)] = obj
        return list(gathered.values())

    # ── (1) Multi-collection selection wins ──
    if len(outliner_colls) >= 2:
        gathered = _gather(outliner_colls)
        if gathered:
            return gathered

    # ── (2) Viewport-selected meshes ──
    selected = [o for o in context.selected_objects if o.type == 'MESH']
    if selected:
        return selected

    # ── (3) Single outliner collection or active collection fallback ──
    fallback_colls = list(outliner_colls)
    if not fallback_colls:
        active = getattr(context, 'collection', None)
        scene_root = context.scene.collection if context and context.scene else None
        if active is not None and active is not scene_root:
            fallback_colls.append(active)

    if fallback_colls:
        gathered = _gather(fallback_colls)
        if gathered:
            return gathered

    # ── (4) Final fallback ──
    return [o for o in context.scene.objects if o.type == 'MESH']


# ──────────────────────────── ID helpers ──────────────────────────────

def _get_or_assign_id(obj, id_pool_start: int, used_ids: Set[int]) -> int:
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

def _pair_main_lod_groups(cell_groups: list) -> list:
    """Reorder cell_groups so each main DFF is immediately followed by
    its LOD partner from ``inu.lod_object``.

    Vanilla SA IPL/IDE files interleave main → LOD → main → LOD →…,
    which keeps a model and its low-poly twin physically close in the
    binary stream. We mirror that by walking ``cell_groups`` once,
    emitting each main and (if it points at a LOD that's also being
    exported) the LOD right after. Groups already emitted via this
    pairing are skipped on their direct visit so a LOD never appears
    twice. Anything without a resolvable LOD partner keeps its
    original position.
    """
    by_obj: dict = {id(g.dff): g for g in cell_groups}
    out: list = []
    consumed: set = set()

    for g in cell_groups:
        if id(g.dff) in consumed:
            continue
        out.append(g)
        consumed.add(id(g.dff))
        inu = getattr(g.dff, 'inu', None)
        lod_obj = getattr(inu, 'lod_object', None) if inu is not None else None
        if lod_obj is None:
            continue
        partner = by_obj.get(id(lod_obj))
        if partner is not None and id(partner.dff) not in consumed:
            out.append(partner)
            consumed.add(id(partner.dff))

    return out


def _plan_cells(groups, *, base_name: str, target_dir: str,
                split_mode: str, cell_size: float, scene,
                max_per_cell: int = 200,
                min_cell_size: float = 16.0):
    """Split groups into a flat list of (cell_name, cell_dir, cell_groups).

    ``split_mode`` is one of:

    * ``'NONE'`` — single cell named ``base_name`` covering all groups.
    * ``'GRID'`` — bin DFFs into ``cell_size``-meter XY cells. Multi-cell
      result is emitted in deterministic order. Single-cell result
      degrades to the NONE layout so flipping GRID on a small scene
      doesn't produce a dead subdirectory.
    * ``'ADAPTIVE'`` — quadtree subdivision driven by per-cell DFF count.
      Dense areas get small cells, sparse areas stay big. Each leaf
      cell holds at most ``max_per_cell`` DFFs (best-effort, capped by
      ``min_cell_size`` to avoid infinite recursion on stacked
      buildings). Single-leaf scenes degrade to the NONE layout.
    * ``'COLLECTION'`` — bin DFFs by their topmost user collection.
      Each cell gets the collection's name as its district name and
      its own subdirectory (always, even when only one bucket is
      produced — keeps the round-trip output structure consistent
      with the user's mental model of «my collection name = the IPL
      filename»).
    """
    mode = (split_mode or 'NONE').upper()

    if mode == 'GRID' and cell_size > 0:
        cells = compute_grid_cells(groups, cell_size)
        if len(cells) > 1:
            return [
                (format_cell_name(base_name, cx, cy),
                 os.path.join(target_dir, format_cell_name(base_name, cx, cy)),
                 cell_groups)
                for (cx, cy), cell_groups in sorted(cells.items())
            ]

    if mode == 'ADAPTIVE' and max_per_cell > 0:
        adaptive = compute_adaptive_cells(
            groups,
            max_per_cell=max_per_cell,
            min_cell_size=max(1.0, min_cell_size),
        )
        # Single-leaf scene means «didn't need to split» — fall through
        # to the bare base_name layout instead of emitting a single
        # «<base>` (no suffix) subdirectory; that's identical to NONE.
        if len(adaptive) > 1:
            return [
                (format_adaptive_cell_name(base_name, path),
                 os.path.join(target_dir,
                              format_adaptive_cell_name(base_name, path)),
                 cell_groups)
                for path, cell_groups in sorted(adaptive.items())
            ]

    if mode == 'COLLECTION' and scene is not None:
        cells = compute_collection_cells(groups, scene)
        if cells:
            # Always emit subfolders in COLLECTION mode — even one bucket
            # gets its own ``target_dir/<bucket>/`` directory so the user
            # immediately sees if all groups landed in the same bucket
            # (e.g. an «unsorted» fallback) and can fix the scene layout.
            return [
                (cell_name, os.path.join(target_dir, cell_name), cell_groups)
                for cell_name, cell_groups in sorted(cells.items())
            ]

    return [(base_name, target_dir, groups)]


def iter_export_map(context, target_dir: str, *, objects=None,
                    export_dff: bool = True,
                    export_col: bool = True,
                    col_library: bool = False,
                    export_txd: bool = True,
                    export_ipl: bool = True,
                    export_ide: bool = True,
                    binary_ipl: bool = False,
                    fla_extended_ipl: bool = False,
                    id_pool_start: int = 20000,
                    base_name: str = "district",
                    split_mode: str = 'NONE',
                    cell_size: float = 256.0,
                    max_per_cell: int = 200,
                    min_cell_size: float = 16.0,
                    stats: Optional[dict] = None):
    """Generator-driven map export.

    Yields ``(current, total, status_label)`` after every unit of work
    (one DFF group, one COL library, one TXD/IDE/IPL write). Caller
    drives it from a modal timer to keep the viewport responsive and
    update the workspace status bar between units. Pass an empty
    ``stats`` dict to have it filled with per-format counts in place.

    The synchronous ``export_map(...)`` wrapper exhausts this generator
    in one go for callers that don't need progress.
    """
    os.makedirs(target_dir, exist_ok=True)

    if objects is None:
        objects = list(context.selected_objects)
        if not objects:
            objects = list(context.scene.objects)

    if stats is None:
        stats = {}
    stats.setdefault('dff', 0)
    stats.setdefault('col', 0)
    stats.setdefault('txd', 0)
    stats.setdefault('ide', 0)
    stats.setdefault('ipl', 0)
    stats.setdefault('groups', 0)

    groups = collect_map_groups(objects)
    if not groups:
        stats['error'] = 'no DFF meshes found in selection'
        return

    # ── Assign / unify Model IDs across duplicate-name objects ──
    # Many scenes have several DFFs sharing the same cleaned model
    # name (Blender's .001 / .002 instance suffixes, or hand-placed
    # copies of vegas_palm01). The IDE dedupes by cleaned name and
    # writes ONE entry per model, but the IPL writes every instance
    # with that DFF's own ``inu.model_id`` — if duplicates carry
    # different IDs (e.g. one vanilla 6870, others auto-assigned
    # 20000/20001/…), the IPL ends up with model_ids that have no
    # IDE definition and the game crashes on load.
    #
    # Resolution: bucket DFFs by cleaned model name; for each bucket
    # pick the existing nonzero ID if any, otherwise allocate one
    # via ``_get_or_assign_id``; then propagate the chosen ID to
    # every duplicate in the bucket.
    from .model_utils import get_model_type
    used_ids: Set[int] = set()

    def _bucket_key(obj):
        """Strip Blender's .001 / .002 instance suffix BEFORE running
        the model-type detector — get_model_type leaves digit-suffixes
        intact and would otherwise put each duplicate in its own bucket."""
        n = obj.name
        if '.' in n:
            b, s = n.rsplit('.', 1)
            if s.isdigit():
                n = b
        class _Mock:
            def __init__(self, nn):
                self.name = nn
        _, base = get_model_type(_Mock(n))
        return base

    name_to_groups: Dict[str, list] = {}
    for g in groups:
        name_to_groups.setdefault(_bucket_key(g.dff), []).append(g)

    for base, gs in name_to_groups.items():
        existing_id = 0
        for g in gs:
            inu = getattr(g.dff, 'inu', None)
            mid = int(getattr(inu, 'model_id', 0) or 0) if inu else 0
            if mid > 0:
                existing_id = mid
                break

        if existing_id > 0:
            used_ids.add(existing_id)
            for g in gs:
                inu = getattr(g.dff, 'inu', None)
                if inu is not None:
                    try:
                        inu.model_id = existing_id
                    except Exception:
                        pass
        else:
            shared_id = _get_or_assign_id(gs[0].dff, id_pool_start, used_ids)
            for g in gs[1:]:
                inu = getattr(g.dff, 'inu', None)
                if inu is not None:
                    try:
                        inu.model_id = shared_id
                    except Exception:
                        pass

    cells = _plan_cells(groups, base_name=base_name, target_dir=target_dir,
                        split_mode=split_mode, cell_size=cell_size,
                        scene=getattr(context, 'scene', None),
                        max_per_cell=max_per_cell,
                        min_cell_size=min_cell_size)
    if (split_mode or 'NONE').upper() != 'NONE' and len(cells) > 1:
        stats['cells'] = len(cells)

    # ── Reorder each cell's groups so each main DFF is immediately
    # followed by its LOD partner (matching the vanilla SA layout
    # main→LOD→main→LOD…). Pairing reads ``inu.lod_object`` set during
    # Map Import; LOD partners that aren't part of the same export
    # subset stay in their original spot.
    cells = [
        (cell_name, cell_dir, _pair_main_lod_groups(cell_groups))
        for cell_name, cell_dir, cell_groups in cells
    ]

    # Pre-bucket each cell's groups by their target ``inu.txd_name``.
    # SA's IDE assigns every model to a TXD by name; many models share
    # one TXD (e.g. ``vegas01.txd`` used by 50 buildings), some have
    # their own (``cj.txd``). A monolithic <cell>.txd would silently
    # destroy that mapping at re-export time, so we bucket per
    # txd_name and emit one .txd per bucket. Empty txd_name falls
    # back to the model's own base name (fresh hand-crafted models).
    cell_txd_buckets: List[List[Tuple[str, list]]] = []
    for cell_name, _cell_dir, cell_groups in cells:
        buckets: Dict[str, list] = {}
        if export_txd:
            for g in cell_groups:
                inu = getattr(g.dff, 'inu', None)
                tname = ((getattr(inu, 'txd_name', '') if inu else '') or '').strip()
                if not tname:
                    tname = g.base
                buckets.setdefault(tname, []).append(g)
        cell_txd_buckets.append(sorted(buckets.items()))

    # Pre-compute total work units for the progress bar
    total = 0
    for cell_idx, (cell_name, cell_dir, cell_groups) in enumerate(cells):
        total += len(cell_groups)  # one DFF (+ optional per-group COL) per group
        if export_col and col_library and any(g.col_objects for g in cell_groups):
            total += 1
        if export_txd:
            total += len(cell_txd_buckets[cell_idx])
        if export_ide:
            total += 1
        if export_ipl:
            total += 1
    if total == 0:
        total = 1
    current = 0

    # ── Lazy imports (so the generator doesn't pull bpy heavy modules
    # in until it's actually run) ──
    if export_dff:
        from ..ops.dff_export import export_dff as _export_dff, _resolve_export_version
        # Resolve RW version + platform once for the whole map export —
        # bulk export honours scene's gtatools_game + gtatools_platform.
        _map_export_rw_version = _resolve_export_version()
        try:
            import bpy as _bpy
            _map_export_platform = getattr(
                _bpy.context.scene.inu_settings, 'gtatools_platform', 'PC')
        except Exception:
            _map_export_platform = 'PC'
    if export_col:
        from ..ops.col_export import _resolve_col_version
        _map_export_col_version = _resolve_col_version()
        if col_library:
            from ..ops.col_export import export_col_library as _export_col_lib
        else:
            from ..ops.col_export import export_col as _export_col
    if export_txd:
        from ..tools.txd_export import export_txd as _export_txd
        # DXT compression backend — read once at the top so every bucket
        # uses the same encoder. Default 'numpy' is the vectorized core.dxt
        # path (no external binaries, ToS-clean for extensions.blender.org).
        _txd_backend = getattr(
            getattr(getattr(context, 'scene', None), 'inu_settings', None),
            'gtatools_dxt_backend', 'numpy')
    if export_ide:
        from ..ops.ide_export import export_ide as _export_ide
    if export_ipl:
        from ..ops.ipl_export import export_ipl as _export_ipl

    for cell_idx, (cell_name, cell_dir, cell_groups) in enumerate(cells):
        os.makedirs(cell_dir, exist_ok=True)
        n_local = len(cell_groups)

        # ── Per-group DFF + (per-group COL if not col_library) ────
        for gi, g in enumerate(cell_groups, start=1):
            current += 1
            yield current, total, f"{cell_name}: DFF {gi}/{n_local} ({g.base})"

            if export_dff:
                dff_path = os.path.join(cell_dir, f"{g.base}.dff")
                group_objs = [g.dff]
                if g.lod:
                    group_objs.append(g.lod)
                group_objs.extend(g.col_objects)
                try:
                    _export_dff(dff_path, group_objs,
                                version=_map_export_rw_version,
                                target_platform=_map_export_platform)
                    stats['dff'] += 1
                except Exception as e:
                    print(f"[map_export] DFF {g.base} failed: {e}")

            if export_col and not col_library and g.col_objects:
                col_path = os.path.join(cell_dir, f"{g.base}.col")
                try:
                    _export_col(col_path, g.col_objects,
                                version=_map_export_col_version)
                    stats['col'] += 1
                except Exception as e:
                    print(f"[map_export] COL {g.base} failed: {e}")

        # ── COL library (one .col per cell) ───────────────────────
        if export_col and col_library and any(g.col_objects for g in cell_groups):
            current += 1
            yield current, total, f"{cell_name}: COL library"
            lib_path = os.path.join(cell_dir, f"{cell_name}.col")
            all_col_objs: list = []
            for g in cell_groups:
                all_col_objs.extend(g.col_objects)
            try:
                count = _export_col_lib(lib_path, all_col_objs,
                                        version=_map_export_col_version)
                stats['col'] += count
            except Exception as e:
                print(f"[map_export] COL library failed: {e}")

        # ── Per-txd_name TXD writes ──────────────────────────────
        # IDE-driven grouping: every model belongs to a named TXD;
        # models sharing a name go into one .txd, exclusive ones get
        # their own. Preserves the vanilla SA layout exactly when the
        # scene was imported with IDE-populated inu.txd_name.
        if export_txd and cell_txd_buckets[cell_idx]:
            if context.mode != 'OBJECT':
                try:
                    bpy.ops.object.mode_set(mode='OBJECT')
                except RuntimeError:
                    pass
            prev_selection = list(context.selected_objects)
            prev_active = context.view_layer.objects.active

            def _clear_selection():
                for _o in context.selected_objects:
                    try:
                        _o.select_set(False)
                    except Exception:
                        pass

            try:
                for txd_basename, txd_groups in cell_txd_buckets[cell_idx]:
                    current += 1
                    yield current, total, (
                        f"{cell_name}: TXD {txd_basename} "
                        f"({len(txd_groups)} model{'s' if len(txd_groups) != 1 else ''})"
                    )
                    txd_path = os.path.join(cell_dir, f"{txd_basename}.txd")
                    _clear_selection()
                    for g in txd_groups:
                        if g.dff:
                            try:
                                g.dff.select_set(True)
                            except Exception:
                                pass
                    if txd_groups and txd_groups[0].dff:
                        try:
                            context.view_layer.objects.active = txd_groups[0].dff
                        except Exception:
                            pass
                    try:
                        _export_txd(txd_path, context, selected_only=True,
                                    backend=_txd_backend)
                        stats['txd'] += 1
                    except Exception as e:
                        print(f"[map_export] TXD {txd_basename} failed: {e}")
            finally:
                _clear_selection()
                for o in prev_selection:
                    try:
                        o.select_set(True)
                    except Exception:
                        pass
                if prev_active:
                    try:
                        context.view_layer.objects.active = prev_active
                    except Exception:
                        pass

        # ── IDE ──────────────────────────────────────────────────
        if export_ide:
            current += 1
            yield current, total, f"{cell_name}: IDE"
            ide_path = os.path.join(cell_dir, f"{cell_name}.ide")
            ide_objs = [g.dff for g in cell_groups]
            try:
                _export_ide(ide_path, ide_objs)
                stats['ide'] += 1
            except Exception as e:
                print(f"[map_export] IDE failed: {e}")

        # ── IPL ──────────────────────────────────────────────────
        if export_ipl:
            current += 1
            yield current, total, f"{cell_name}: IPL"
            ipl_path = os.path.join(cell_dir, f"{cell_name}.ipl")
            ipl_objs = [g.dff for g in cell_groups]
            try:
                _export_ipl(ipl_path, ipl_objs, binary=binary_ipl,
                            fla_extended=fla_extended_ipl)
                stats['ipl'] += 1
            except Exception as e:
                print(f"[map_export] IPL failed: {e}")

        stats['groups'] += n_local


def export_map(target_dir: str, *, objects=None,
               export_dff: bool = True,
               export_col: bool = True,
               col_library: bool = False,
               export_txd: bool = True,
               export_ipl: bool = True,
               export_ide: bool = True,
               binary_ipl: bool = False,
               fla_extended_ipl: bool = False,
               id_pool_start: int = 20000,
               base_name: str = "district",
               split_mode: str = 'NONE',
               cell_size: float = 256.0,
               max_per_cell: int = 200,
               min_cell_size: float = 16.0) -> dict:
    """Synchronous wrapper around :func:`iter_export_map` for callers
    that don't need progress reporting (scripts, INU Export, etc.).

    Drives the generator to exhaustion in one go and returns the stats
    dict — including the ``cells`` count when a split mode was applied.
    """
    stats: dict = {}
    for _ in iter_export_map(
            bpy.context, target_dir, objects=objects,
            export_dff=export_dff, export_col=export_col,
            col_library=col_library, export_txd=export_txd,
            export_ipl=export_ipl, export_ide=export_ide,
            binary_ipl=binary_ipl, fla_extended_ipl=fla_extended_ipl,
            id_pool_start=id_pool_start,
            base_name=base_name, split_mode=split_mode,
            cell_size=cell_size,
            max_per_cell=max_per_cell, min_cell_size=min_cell_size,
            stats=stats):
        pass
    return stats


# ──────────────────────────── operator + panel ───────────────────────

class GTATOOLS_OT_map_export(bpy.types.Operator):
    """Экспортировать выделение как готовый район GTA SA (DFF + COL + TXD + IDE + IPL в одну папку)"""
    bl_idname = "gtatools.map_export"
    bl_label = "INU: Export Map…"
    bl_options = {'REGISTER'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    base_name: bpy.props.StringProperty(name="Base Name", default="district")
    include_dff: bpy.props.BoolProperty(name="DFF", default=True)
    include_col: bpy.props.BoolProperty(name="COL", default=True)
    col_library: bpy.props.BoolProperty(
        name=T("COL Library"),
        description=T("OFF (по умолчанию): каждая DFF получает свой отдельный <model>.col файл — соответствует ванильному SA где у большинства моделей коллизии в собственных файлах.\nON: все коллизии группируются в .col-библиотеки по inu.col_name (vegasN.col, LAs.col, …). Полезно когда есть осознанная shared collision на много моделей"),
        default=False,
    )
    include_txd: bpy.props.BoolProperty(name="TXD", default=True)
    include_ide: bpy.props.BoolProperty(name="IDE", default=True)
    include_ipl: bpy.props.BoolProperty(name="IPL", default=True)
    binary_ipl: bpy.props.BoolProperty(name="Binary IPL", default=False)
    fla_extended_ipl: bpy.props.BoolProperty(
        name=T("FLA: real_interior"),
        description=T(
            "Записать 12-ю колонку realInterior в каждой inst-строке IPL. "
            "Fastman92 Limit Adjuster читает её, vanilla SA молча "
            "игнорирует. Значение берётся из obj.inu.real_interior"),
        default=False,
    )
    id_pool_start: bpy.props.IntProperty(
        name="ID Pool Start", default=20000, min=1, max=32000,
        description=T("Первый ID для DFF у которых inu.model_id == 0"),
    )
    split_mode: bpy.props.EnumProperty(
        name=T("Разбиение"),
        description=T("Как разбить выделение на отдельные district'ы при экспорте"),
        items=[
            ('NONE', T("Без разбиения"),
             T("Один общий district, все DFF в корне target_dir. base_name используется для имён IDE/IPL/COL/TXD")),
            ('GRID', T("XY-сетка"),
             T("Биннить DFF по XY-координате origin'а на ячейки cell_size метров. Каждая непустая ячейка получает подпапку <base>_x<cx>_y<cy> со своими IDE/IPL/COL/TXD")),
            ('ADAPTIVE', T("Адаптивная сетка"),
             T("Quadtree-разбиение по плотности: ячейка делится 2×2 пока в ней больше max_per_cell DFF. Плотные районы получают мелкие ячейки, разреженные остаются одной большой. Гарантирует число DFF на ячейку вместо равномерного пространственного разбиения. Имена подпапок: <base>_q<path>, где path — путь по квадрантам (0=SW, 1=SE, 2=NW, 3=NE)")),
            ('COLLECTION', T("По коллекциям"),
             T("Биннить DFF по имени верхней (top-level) коллекции, в которой объект лежит. Имя коллекции становится именем district'а — идеально для round-trip с Group-by-IPL импортом (vegasn_stream0 в Blender → vegasn_stream0.ipl на выходе)")),
        ],
        default='NONE',
    )
    cell_size: bpy.props.FloatProperty(
        name=T("Размер ячейки (м)"),
        description=T("Сторона квадратной ячейки в метрах для разбиения по XY-сетке. 256 м соответствует ванильному радиусу стриминга. Уменьшай для более мелких чанков, увеличивай если районов получается слишком много"),
        default=256.0, min=16.0, soft_max=2048.0, max=8192.0,
    )
    max_per_cell: bpy.props.IntProperty(
        name=T("Макс. DFF на ячейку"),
        description=T("Целевой потолок DFF в одной адаптивной ячейке. Когда число превышено — ячейка делится на 4. Меньше = больше мелких ячеек (тоньше streaming, но больше IPL-файлов). Больше = крупные ячейки. Vanilla SA streaming-радиус хорошо работает с ~150-300 DFF на IPL"),
        default=200, min=10, soft_max=2000, max=10000,
    )
    min_cell_size: bpy.props.FloatProperty(
        name=T("Мин. размер ячейки (м)"),
        description=T("Минимальная сторона ячейки для адаптивной сетки — нижняя граница рекурсии. Защищает от бесконечного деления когда много DFF разделяют одну XY-точку (вертикально стопкой, как небоскрёбы). При достижении этого предела ячейка остаётся, даже если в ней больше max_per_cell"),
        default=16.0, min=1.0, soft_max=256.0, max=2048.0,
    )

    # ENUM_FLAG = multi-checkbox in the operator dialog. Wins over outliner
    # state because the user picks the collections explicitly with a stable
    # UI element instead of relying on Blender's brittle outliner-context
    # selection forwarding (which gets cleared the moment focus shifts to
    # the sidebar button or the file browser).
    target_collections: bpy.props.EnumProperty(
        name=T("Целевые коллекции"),
        description=T("Какие top-level коллекции экспортировать. Авто-инициализация по выделению в outliner; если не угадало — отметь галочками вручную. Имеет смысл вместе с режимом «По коллекциям»"),
        items=lambda self, context: [
            (c.name, c.name, '')
            for c in context.scene.collection.children
        ][:32],  # ENUM_FLAG hard limit at 32 bits
        options={'ENUM_FLAG'},
        # No `default=` — Blender 5.x rejects non-int defaults when
        # `items` is a callable. Empty set is the natural default for
        # an ENUM_FLAG with dynamic items.
    )

    _timer = None
    _gen = None
    _stats: dict = None
    _captured_objects: list = None

    def invoke(self, context, event):
        # Capture the user's outliner / viewport selection BEFORE the
        # file browser steals focus and clears it. Two-pronged: the
        # snapshot serves as a fallback when ``target_collections`` is
        # left empty in the dialog, and is also used to PRE-CHECK the
        # multi-select so the user sees their outliner selection
        # already mirrored.
        self._captured_objects = _resolve_export_objects(context)

        # Try to pre-populate the dialog's multi-checkbox from the
        # outliner state — best-effort, the user can correct it.
        outliner_colls = _gather_outliner_selected_collections(context)
        scene_top = {c.name for c in context.scene.collection.children}
        prefilled = {c.name for c in outliner_colls if c.name in scene_top}
        if prefilled:
            self.target_collections = prefilled

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout

        # Top-level collections multi-checkbox FIRST — most reliable
        # way to express «export these N collections» when the outliner
        # auto-detection fails to capture the user's Ctrl-clicked set
        # (Blender's selected_ids context is brittle from sidebar buttons).
        box = layout.box()
        box.label(text=T("Целевые коллекции:"), **inu_icon(safe_icon('OUTLINER_COLLECTION')))
        col = box.column(align=True)
        col.prop(self, "target_collections", expand=True)
        if not self.target_collections:
            box.label(
                text=T("(пусто = выделение из outliner на момент нажатия)"),
                **inu_icon(safe_icon('INFO')),
            )

        layout.separator()
        layout.prop(self, "base_name")
        row = layout.row(align=True)
        row.prop(self, "include_dff", toggle=True)
        row.prop(self, "include_col", toggle=True)
        row.prop(self, "include_txd", toggle=True)
        row = layout.row(align=True)
        row.prop(self, "include_ide", toggle=True)
        row.prop(self, "include_ipl", toggle=True)
        layout.prop(self, "col_library")
        layout.prop(self, "binary_ipl")
        layout.prop(self, "fla_extended_ipl")
        layout.prop(self, "id_pool_start")
        layout.separator()
        layout.prop(self, "split_mode")
        if self.split_mode == 'GRID':
            layout.prop(self, "cell_size")
        elif self.split_mode == 'ADAPTIVE':
            sub = layout.column(align=True)
            sub.prop(self, "max_per_cell")
            sub.prop(self, "min_cell_size")

    def execute(self, context):
        if not self.directory or not os.path.isdir(self.directory):
            self.report({'ERROR'}, "Pick a target folder")
            return {'CANCELLED'}

        # Source of truth, in priority order:
        #   1. Explicit dialog checkboxes (``target_collections``) — the
        #      user picked these in the operator panel, ignore everything
        #      else. Most reliable path for multi-collection exports.
        #   2. Snapshot captured at invoke() time, before the file dialog
        #      stole focus.
        #   3. Live resolve (only when the operator was triggered via
        #      ``bpy.ops.gtatools.map_export()`` from a script).
        if self.target_collections:
            collections = []
            for name in self.target_collections:
                coll = bpy.data.collections.get(name)
                if coll is None:
                    coll = next((c for c in context.scene.collection.children
                                 if c.name == name), None)
                if coll is not None:
                    collections.append(coll)
            gathered: dict = {}
            for coll in collections:
                for obj in coll.all_objects:
                    if obj.type == 'MESH':
                        gathered[id(obj)] = obj
            selected = list(gathered.values())
        else:
            selected = self._captured_objects
            if not selected:
                selected = _resolve_export_objects(context)

        # Modal generator pattern (same shape as Import Map): yield-driven
        # work loop fed by a window-manager timer keeps the viewport
        # responsive and the workspace status text fresh between writes.
        self._stats = {}
        self._gen = iter_export_map(
            context, self.directory, objects=selected,
            export_dff=self.include_dff,
            export_col=self.include_col,
            col_library=self.col_library,
            export_txd=self.include_txd,
            export_ide=self.include_ide,
            export_ipl=self.include_ipl,
            binary_ipl=self.binary_ipl,
            fla_extended_ipl=self.fla_extended_ipl,
            id_pool_start=self.id_pool_start,
            base_name=self.base_name,
            split_mode=self.split_mode,
            cell_size=self.cell_size,
            max_per_cell=self.max_per_cell,
            min_cell_size=self.min_cell_size,
            stats=self._stats,
        )

        wm = context.window_manager
        wm.progress_begin(0, 100)
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        context.workspace.status_text_set(T("Map Export: подготовка..."))
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            self._finish(context)
            self.report({'WARNING'}, T("Отменено"))
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        import time
        wm = context.window_manager
        deadline = time.monotonic() + 0.05  # ~20 fps frame budget

        while time.monotonic() < deadline:
            try:
                current, total, label = next(self._gen)
            except StopIteration:
                self._finish(context)
                stats = self._stats or {}
                if stats.get('error'):
                    self.report({'ERROR'}, stats['error'])
                    return {'CANCELLED'}
                if 'cells' in stats:
                    msg = (f"{stats['cells']} cells, {stats.get('groups', 0)} group(s) → "
                           f"{stats.get('dff', 0)} DFF, {stats.get('col', 0)} COL, "
                           f"{stats.get('txd', 0)} TXD, {stats.get('ide', 0)} IDE, "
                           f"{stats.get('ipl', 0)} IPL")
                else:
                    msg = (f"{stats.get('groups', 0)} group(s) → "
                           f"{stats.get('dff', 0)} DFF, {stats.get('col', 0)} COL, "
                           f"{stats.get('txd', 0)} TXD, {stats.get('ide', 0)} IDE, "
                           f"{stats.get('ipl', 0)} IPL")
                self.report({'INFO'}, msg)
                return {'FINISHED'}
            except Exception as e:
                self._finish(context)
                self.report({'ERROR'}, f"{T('Ошибка экспорта')}: {e}")
                print(f"[map_export] aborted: {e}")
                import traceback
                traceback.print_exc()
                return {'CANCELLED'}

            pct = int(100 * current / max(total, 1))
            wm.progress_update(pct)
            context.workspace.status_text_set(
                f"Map Export: {current}/{total} — {label}")

        return {'RUNNING_MODAL'}

    def _finish(self, context):
        if self._timer:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except Exception:
                pass
            self._timer = None
        try:
            context.window_manager.progress_end()
        except Exception:
            pass
        try:
            context.workspace.status_text_set(None)
        except Exception:
            pass
        self._gen = None


