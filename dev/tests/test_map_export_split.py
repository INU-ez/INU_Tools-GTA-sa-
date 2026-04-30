"""Unit tests for the map-export split planners — the pure-Python
binning helpers that decide how many sub-districts a scene splits into
and what each one is named.

These tests stub bpy so the module imports cleanly without a real
Blender. We only exercise the geometry-driven helpers:

* ``compute_grid_cells`` — uniform XY grid (legacy 1.6.6 mode)
* ``compute_adaptive_cells`` — quadtree subdivision (new 1.7.0 mode)
* ``format_cell_name`` / ``format_adaptive_cell_name`` — naming

The Blender-coupled paths (operator, file IO) need a live Blender and
are out of scope for unit tests.
"""

from pathlib import Path
import math
import sys
import types
from dataclasses import dataclass, field

import pytest


ROOT = Path(__file__).resolve().parents[2]
# Add the addon dir so `tools.map_export` resolves; also stub a fake
# top-level package named `INU_tools` so that ``from .. import T`` in
# map_export.py (which would otherwise reach above top level when the
# module is imported as ``tools.map_export``) finds a usable T helper.
sys.path.insert(0, str(ROOT / "INU_tools"))


def _ensure_bpy_stubs():
    if 'bpy' in sys.modules:
        return
    bpy_mod = types.ModuleType('bpy')

    class _DummyClass:
        pass

    bpy_mod.types = types.SimpleNamespace(
        Operator=_DummyClass, Panel=_DummyClass,
        PropertyGroup=_DummyClass)
    bpy_mod.props = types.SimpleNamespace(
        StringProperty=lambda **kw: None,
        IntProperty=lambda **kw: None,
        FloatProperty=lambda **kw: None,
        BoolProperty=lambda **kw: None,
        EnumProperty=lambda **kw: None,
    )
    bpy_mod.context = types.SimpleNamespace(scene=None)
    sys.modules['bpy'] = bpy_mod
    sys.modules['bpy.types'] = bpy_mod.types
    sys.modules['bpy.props'] = bpy_mod.props
    # `tools.model_utils` imports bmesh at top — module-load-time only
    # uses the symbol indirectly via geometry checks we don't exercise.
    sys.modules.setdefault('bmesh', types.ModuleType('bmesh'))


_ensure_bpy_stubs()


# Re-route `tools.map_export` through a parent package so its
# ``from .. import T`` resolves. We do this by importing the addon as
# `INU_tools.tools.map_export` from the repo root rather than as a
# bare `tools.map_export`. The addon's __init__.py is heavy (defines
# every operator), so we install a *minimal* stub package that only
# exports T — enough for map_export's import-time resolution.
_pkg_root = sys.modules.setdefault('INU_tools', types.ModuleType('INU_tools'))
_pkg_root.__path__ = [str(ROOT / "INU_tools")]
_pkg_root.T = lambda s, *_a, **_kw: s

from INU_tools.tools.map_export import (  # noqa: E402
    MapGroup,
    compute_grid_cells,
    compute_adaptive_cells,
    format_cell_name,
    format_adaptive_cell_name,
)


# ── Mock objects ─────────────────────────────────────────────────

@dataclass
class _Loc:
    x: float
    y: float
    z: float = 0.0


@dataclass
class _Matrix:
    translation: _Loc


@dataclass
class _MockObj:
    name: str
    matrix_world: _Matrix


def _g(name: str, x: float, y: float) -> MapGroup:
    """Build a MapGroup with just enough state for the binning planners."""
    return MapGroup(
        base=name,
        dff=_MockObj(name=name, matrix_world=_Matrix(_Loc(x, y))),
    )


# ── Uniform GRID — legacy regression coverage ──────────────────────

def test_grid_cells_empty_groups_are_one_empty_bucket():
    cells = compute_grid_cells([], 256.0)
    assert cells == {}


def test_grid_cells_zero_cell_size_collapses_to_origin():
    """cell_size <= 0 disables binning — all groups land in (0, 0)."""
    groups = [_g("a", 100, 100), _g("b", -500, 0)]
    cells = compute_grid_cells(groups, 0.0)
    assert cells == {(0, 0): groups}


def test_grid_cells_bin_by_origin():
    groups = [
        _g("a", 50, 50),       # cell (0, 0)
        _g("b", 300, 50),      # cell (1, 0)
        _g("c", 50, 300),      # cell (0, 1)
        _g("d", -10, -10),     # cell (-1, -1)
    ]
    cells = compute_grid_cells(groups, 256.0)
    assert (0, 0) in cells
    assert (1, 0) in cells
    assert (0, 1) in cells
    assert (-1, -1) in cells
    assert sum(len(v) for v in cells.values()) == 4


def test_format_cell_name_negative_uses_m_prefix():
    assert format_cell_name("vegas", 0, 0) == "vegas_x0_y0"
    assert format_cell_name("vegas", -1, 2) == "vegas_xm1_y2"
    assert format_cell_name("vegas", 5, -3) == "vegas_x5_ym3"


# ── Adaptive (quadtree) — new in 1.7.0 ─────────────────────────────

def test_adaptive_empty_returns_empty_dict():
    assert compute_adaptive_cells([]) == {}


def test_adaptive_below_threshold_stays_one_cell():
    """A small population fits in the root cell — empty path key,
    single cell holds everything."""
    groups = [_g(f"m{i}", i * 10, 0) for i in range(10)]
    cells = compute_adaptive_cells(groups, max_per_cell=200)
    assert cells == {(): groups}


def test_adaptive_dense_scene_splits():
    """50 DFFs spread across a big bbox with cap=10 → must split into
    multiple leaf cells (>1) and every leaf is at most cap large."""
    groups = []
    for i in range(50):
        # 5×10 grid spanning 1000×2000 m
        groups.append(_g(f"m{i}",
                         (i % 5) * 200.0,
                         (i // 5) * 200.0))
    cells = compute_adaptive_cells(groups, max_per_cell=10)
    assert len(cells) > 1
    for path, leaf in cells.items():
        # cap is best-effort — min_cell_size floor can leave a cell
        # over budget. With 200 m grid and 16 m floor we shouldn't
        # hit that here.
        assert len(leaf) <= 10, (
            f"leaf {path} holds {len(leaf)} > cap 10")


def test_adaptive_partition_is_complete():
    """Sum of leaves equals input population (no losses, no doubles)."""
    groups = [_g(f"m{i}", i * 30.0, (i * 17) % 800) for i in range(80)]
    cells = compute_adaptive_cells(groups, max_per_cell=15)
    total = sum(len(v) for v in cells.values())
    assert total == len(groups)
    seen = set()
    for leaf in cells.values():
        for g in leaf:
            assert id(g) not in seen, "group counted twice"
            seen.add(id(g))


def test_adaptive_min_cell_size_floor_stops_recursion():
    """Many DFFs at the SAME XY origin would loop infinitely without
    the min_cell_size floor. The floor must terminate even when the
    cap is exceeded."""
    groups = [_g(f"stack{i}", 0.0, 0.0) for i in range(50)]
    cells = compute_adaptive_cells(
        groups, max_per_cell=5, min_cell_size=4.0)
    # Floor reached → one leaf with all 50, over budget but bounded.
    assert len(cells) == 1
    only_leaf = next(iter(cells.values()))
    assert len(only_leaf) == 50


def test_adaptive_path_keys_describe_quadrants():
    """Path tuple uses 0=SW, 1=SE, 2=NW, 3=NE — one DFF per quadrant
    of the bbox should produce four distinct length-1 paths."""
    groups = [
        _g("sw", -100, -100),  # SW
        _g("se",  100, -100),  # SE
        _g("nw", -100,  100),  # NW
        _g("ne",  100,  100),  # NE
    ]
    cells = compute_adaptive_cells(groups, max_per_cell=1)
    assert set(cells.keys()) == {(0,), (1,), (2,), (3,)}


def test_adaptive_naming_omits_suffix_for_single_cell():
    """When the scene fits in one cell the path is empty — name stays
    the bare base_name (no _q suffix), so flipping ADAPTIVE on a small
    scene doesn't sprout a noise directory."""
    assert format_adaptive_cell_name("dist", ()) == "dist"


def test_adaptive_naming_encodes_path():
    assert format_adaptive_cell_name("dist", (0,)) == "dist_q0"
    assert format_adaptive_cell_name("dist", (1, 3)) == "dist_q13"
    assert (format_adaptive_cell_name("dist", (0, 1, 2, 3))
            == "dist_q0123")


def test_adaptive_dense_cluster_subdivides_more_than_sparse():
    """Real motivation for adaptive split: a scene with one packed
    cluster + a few outliers should produce small cells inside the
    cluster while the outliers each get their own coarse cell, NOT
    the other way around."""
    groups = []
    # Cluster: 40 DFFs in a 20×20 m box around origin
    for i in range(40):
        groups.append(_g(f"c{i}",
                         (i % 8) * 2.5, (i // 8) * 2.5))
    # Outliers: 2 single DFFs far away
    groups.append(_g("far_a", 5000.0, 0.0))
    groups.append(_g("far_b", 0.0, 5000.0))

    cells = compute_adaptive_cells(groups, max_per_cell=15,
                                   min_cell_size=1.0)
    # Cluster forces multiple subdivisions; outliers occupy their
    # own (or shared) coarse cell. Total leaves should comfortably
    # exceed 2.
    assert len(cells) >= 3
    # Every leaf still respects the cap (min_cell_size=1m gives
    # plenty of room to subdivide the 20m cluster).
    for leaf in cells.values():
        assert len(leaf) <= 15
