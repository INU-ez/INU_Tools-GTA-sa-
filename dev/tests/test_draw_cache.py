"""Unit tests for tools/draw_cache.py — the panel draw() memo.

The module is deliberately bpy-free (it only ever reads flags off the
depsgraph object it's handed), so these run without any stubbing.

What matters here is the invalidation contract: a memo must survive a
drag (transform-only depsgraph batch) and must NOT survive anything that
can change what a panel would print.
"""

from pathlib import Path
import sys
import types

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from tools import draw_cache  # noqa: E402


def _fake_id(kind):
    """Stand-in for a Blender ID — only its class NAME is inspected."""
    return type(kind, (), {})()


def _update(transform=False, geometry=False, shading=False, kind='Object'):
    return types.SimpleNamespace(
        id=_fake_id(kind),
        is_updated_transform=transform,
        is_updated_geometry=geometry,
        is_updated_shading=shading,
    )


def _depsgraph(*updates):
    return types.SimpleNamespace(updates=list(updates))


@pytest.fixture(autouse=True)
def clean_cache():
    draw_cache.clear()
    yield
    draw_cache.clear()


# ── memo basics ──────────────────────────────────────────────────

def test_memo_builds_once_until_invalidated():
    calls = []

    def build():
        calls.append(1)
        return len(calls)

    assert draw_cache.memo('k', build) == 1
    assert draw_cache.memo('k', build) == 1
    assert len(calls) == 1


def test_memo_rebuilds_after_bump():
    calls = []
    build = lambda: calls.append(1) or len(calls)

    draw_cache.memo('k', build)
    draw_cache.bump(None, _depsgraph(_update(geometry=True)))
    draw_cache.memo('k', build)
    assert len(calls) == 2


def test_distinct_keys_are_independent():
    draw_cache.memo('a', lambda: 'A')
    draw_cache.memo('b', lambda: 'B')
    assert draw_cache.memo('a', lambda: 'changed') == 'A'
    assert draw_cache.memo('b', lambda: 'changed') == 'B'


def test_memo_caches_falsy_values():
    """0 / [] / None are legitimate answers («no conflicts») — they must
    not look like a cache miss and rebuild every draw."""
    calls = []
    build = lambda: calls.append(1) or 0

    assert draw_cache.memo('k', build) == 0
    assert draw_cache.memo('k', build) == 0
    assert len(calls) == 1


def test_store_is_bounded():
    for i in range(draw_cache._MAX_ENTRIES + 50):
        draw_cache.memo(('k', i), lambda: i)
    assert len(draw_cache._store) <= draw_cache._MAX_ENTRIES


# ── invalidation rules ───────────────────────────────────────────

def test_transform_only_batch_does_not_invalidate():
    """The whole point: dragging an object fires one of these per frame."""
    calls = []
    build = lambda: calls.append(1) or len(calls)

    draw_cache.memo('k', build)
    for _ in range(10):
        draw_cache.bump(None, _depsgraph(_update(transform=True)))
        draw_cache.memo('k', build)
    assert len(calls) == 1


def test_scene_bookkeeping_entry_does_not_block_the_skip():
    """Blender rides a Scene entry along with real updates. If that alone
    counted as «something changed», the transform skip would never fire
    and the whole optimisation would be dead code."""
    calls = []
    build = lambda: calls.append(1) or len(calls)

    draw_cache.memo('k', build)
    draw_cache.bump(None, _depsgraph(_update(kind='Scene'),
                                     _update(transform=True)))
    draw_cache.memo('k', build)
    assert len(calls) == 1


def test_scene_entry_alone_still_invalidates():
    """No object moved → we have no evidence this was a drag."""
    draw_cache.memo('k', lambda: 'old')
    draw_cache.bump(None, _depsgraph(_update(kind='Scene')))
    assert draw_cache.memo('k', lambda: 'new') == 'new'


@pytest.mark.parametrize('kind', ['Mesh', 'Material', 'Collection', 'Action'])
def test_non_object_datablock_invalidates(kind):
    """A material or collection edit can change what a panel prints."""
    draw_cache.memo('k', lambda: 'old')
    draw_cache.bump(None, _depsgraph(_update(transform=True, kind=kind)))
    assert draw_cache.memo('k', lambda: 'new') == 'new'


def test_geometry_change_invalidates():
    draw_cache.memo('k', lambda: 'old')
    draw_cache.bump(None, _depsgraph(_update(transform=True, geometry=True)))
    assert draw_cache.memo('k', lambda: 'new') == 'new'


def test_shading_change_invalidates():
    draw_cache.memo('k', lambda: 'old')
    draw_cache.bump(None, _depsgraph(_update(shading=True)))
    assert draw_cache.memo('k', lambda: 'new') == 'new'


def test_flagless_update_invalidates():
    """Renames / retags arrive with no flags set — must not be mistaken
    for a transform and skipped."""
    draw_cache.memo('k', lambda: 'old')
    draw_cache.bump(None, _depsgraph(_update()))
    assert draw_cache.memo('k', lambda: 'new') == 'new'


def test_mixed_batch_invalidates():
    draw_cache.memo('k', lambda: 'old')
    draw_cache.bump(None, _depsgraph(_update(transform=True),
                                     _update(geometry=True)))
    assert draw_cache.memo('k', lambda: 'new') == 'new'


def test_empty_batch_invalidates():
    """Nothing to prove it was a transform → fail safe and rebuild."""
    draw_cache.memo('k', lambda: 'old')
    draw_cache.bump(None, _depsgraph())
    assert draw_cache.memo('k', lambda: 'new') == 'new'


def test_missing_depsgraph_invalidates():
    draw_cache.memo('k', lambda: 'old')
    draw_cache.bump()
    assert draw_cache.memo('k', lambda: 'new') == 'new'


def test_unreadable_depsgraph_invalidates():
    draw_cache.memo('k', lambda: 'old')
    draw_cache.bump(None, object())
    assert draw_cache.memo('k', lambda: 'new') == 'new'


def test_generation_moves_only_on_real_change():
    start = draw_cache.generation()
    draw_cache.bump(None, _depsgraph(_update(transform=True)))
    assert draw_cache.generation() == start
    draw_cache.bump(None, _depsgraph(_update(geometry=True)))
    assert draw_cache.generation() == start + 1


def test_clear_keeps_generation():
    """clear() drops values without pretending the scene changed."""
    gen = draw_cache.generation()
    draw_cache.memo('k', lambda: 'v')
    draw_cache.clear()
    assert draw_cache.generation() == gen
    assert draw_cache.memo('k', lambda: 'rebuilt') == 'rebuilt'
