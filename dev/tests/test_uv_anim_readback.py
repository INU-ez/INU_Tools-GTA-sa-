"""Bytes-only round-trip tests for DFF UV animation chunks (0x2B, 0x1B, 0x135).

Covers the readers added alongside the writers: builds a UVAnimDict + PLG,
serialises via ``to_bytes`` / ``_uv_anim_plg_bytes``, parses via
``_read_uv_anim_dict`` / ``_read_uv_anim_plg``, asserts the round-trip
preserves all material fields the importer relies on (name, duration,
node_to_uv mapping, keyframe trans/scale).
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.dff import (  # noqa: E402
    UVAnim,
    UVAnimKeyframe,
    UVAnimDict,
    CHUNK_UV_ANIM_PLG,
    _read_uv_anim_dict,
    _read_uv_anim_plg,
    _uv_anim_plg_bytes,
)

import struct as _struct  # noqa: E402


LIB_ID = 0x1803FFFF  # GTA SA RW version id


def _find_chunk_body(data, chunk_id):
    """(offset, size) of the first ``chunk_id`` body in a run of top-level
    RW chunks. Mirrors how read_dff locates 0x135 after the 0x120 prefix
    that ``_uv_anim_plg_bytes`` writes (Kam's UVanim layout)."""
    pos = 0
    while pos + 12 <= len(data):
        ct, cs, _ = _struct.unpack_from('<III', data, pos)
        if ct == chunk_id:
            return pos + 12, cs
        pos += 12 + cs
    return None, 0


def test_uv_anim_dict_single_anim_roundtrip():
    src = UVAnimDict(anims=[
        UVAnim(
            name="scrollX",
            type_id=0x1C0,
            node_to_uv=(1, 0, 0, 0, 0, 0, 0, 0),
            duration=2.0,
            keyframes=[
                UVAnimKeyframe(time=0.0, scale_u=1.0, scale_v=1.0,
                               trans_u=0.0, trans_v=0.0),
                UVAnimKeyframe(time=2.0, scale_u=1.0, scale_v=1.0,
                               trans_u=2.5, trans_v=0.0),
            ],
        ),
    ])

    wrapped = src.to_bytes(LIB_ID)
    parsed = _read_uv_anim_dict(wrapped, 12, len(wrapped) - 12)

    assert len(parsed.anims) == 1
    a = parsed.anims[0]
    assert a.name == "scrollX"
    assert a.type_id == 0x1C0
    assert a.node_to_uv == (1, 0, 0, 0, 0, 0, 0, 0)
    assert abs(a.duration - 2.0) < 1e-6
    assert len(a.keyframes) == 2

    last = a.keyframes[1]
    assert abs(last.time - 2.0) < 1e-6
    assert abs(last.trans_u - 2.5) < 1e-6
    assert abs(last.trans_v - 0.0) < 1e-6


def test_uv_anim_dict_multi_anim_preserves_order():
    src = UVAnimDict(anims=[
        UVAnim(name="a", duration=1.0,
               keyframes=[UVAnimKeyframe(time=0.0), UVAnimKeyframe(time=1.0)]),
        UVAnim(name="b", duration=3.0,
               keyframes=[UVAnimKeyframe(time=0.0), UVAnimKeyframe(time=3.0)]),
        UVAnim(name="c", duration=0.5,
               keyframes=[UVAnimKeyframe(time=0.0), UVAnimKeyframe(time=0.5)]),
    ])

    wrapped = src.to_bytes(LIB_ID)
    parsed = _read_uv_anim_dict(wrapped, 12, len(wrapped) - 12)

    assert [a.name for a in parsed.anims] == ["a", "b", "c"]
    assert [a.duration for a in parsed.anims] == [1.0, 3.0, 0.5]


def test_uv_anim_plg_filters_empty_slots_via_mask():
    # Only first two slots populated — mask should encode that and the
    # reader should drop the 6 padding empties.
    wrapped = _uv_anim_plg_bytes(["scroll_main", "scroll_alt"], LIB_ID)
    off, sz = _find_chunk_body(wrapped, CHUNK_UV_ANIM_PLG)
    names = _read_uv_anim_plg(wrapped, off, sz)

    assert names == ["scroll_main", "scroll_alt"]


def test_uv_anim_plg_empty_input_returns_empty_bytes():
    # Materials without any UV anim must not emit a 0x135 chunk.
    assert _uv_anim_plg_bytes([], LIB_ID) == b''


def test_uv_anim_plg_clamps_to_eight_slots():
    # GTA SA's UV anim PLG layout has exactly 8 name slots; extras
    # must be silently dropped — both writer and reader.
    names_in = [f"a{i}" for i in range(12)]
    wrapped = _uv_anim_plg_bytes(names_in, LIB_ID)
    off, sz = _find_chunk_body(wrapped, CHUNK_UV_ANIM_PLG)
    names_out = _read_uv_anim_plg(wrapped, off, sz)

    assert names_out == names_in[:8]
