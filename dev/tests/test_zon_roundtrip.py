"""Round-trip tests for core/zon.py — GTA SA zone files (data/map.zon,
data/info.zon).

Pure Python."""

import struct
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.zon import (  # noqa: E402
    Zone,
    ZonFile,
    format_zon,
    format_zone_line,
    parse_zon,
    parse_zone_line,
    read_zon,
    write_zon,
    zone_line,
)


VANILLA = (
    "zone\r\n"
    "Vegas, 3, 685.0, 476.093, -500.0, 3000.0, 3000.0, 500.0, 3, UNUSED\r\n"
    "SF01, 3, -3000.0, -742.306, -500.0, -1270.53, 1530.24, 500.0, 2, UNUSED\r\n"
    "end\r\n"
)


def _f32(v):
    """Value as it comes back from a Blender object transform."""
    return struct.unpack('f', struct.pack('f', v))[0]


# ── Parsing ──────────────────────────────────────────────────────

def test_parse_line_columns():
    z = parse_zone_line(
        "LA01, 3, 480.0, -3000.0, -500.0, 3000.0, -850.0, 500.0, 1, UNUSED")
    assert z.name == "LA01"
    assert z.zone_type == 3
    assert z.level == 1
    assert z.gxt == "UNUSED"
    assert abs(z.x1 - 480.0) < 1e-4
    assert abs(z.y2 + 850.0) < 1e-4


def test_parse_line_without_gxt_key():
    z = parse_zone_line("A, 0, 1, 2, 3, 4, 5, 6, 1")
    assert z.gxt == "UNUSED"


def test_parse_line_rejects_short_and_garbage():
    assert parse_zone_line("A, 0, 1, 2, 3") is None
    assert parse_zone_line("# just a comment") is None


def test_stray_space_shifts_columns_like_the_engine():
    """CFileLoader::LoadLine turns ',' into ' ' and splits on whitespace,
    so a stray space inside a field shifts every column after it. We must
    read what the game reads, not what the author meant."""
    z = parse_zone_line("CC04, 3, 11569.564, 7830.247, 0 -500.0, "
                        "11937.008, 8248.85, 500.0, 8, UNUSED")
    assert abs(z.z1 - 0.0) < 1e-4        # "0" became z1
    assert abs(z.x2 + 500.0) < 1e-4      # everything after slid one over
    assert z.level == 500                # "500.0" read as %d → 500
    assert z.gxt == "8"


def test_sections_and_comments_are_captured():
    zf = parse_zon("# head\nzone\n# grp\n\nA, 3, 1, 2, 3, 4, 5, 6, 1, UNUSED\n"
                   "# tail\nend\n# after\n")
    assert zf.header == ["# head"]
    assert zf.zones[0].comment == ["# grp", ""]
    assert zf.section_tail == ["# tail"]
    assert zf.footer == ["# after"]


def test_missing_zone_section_warns_and_keeps_lines():
    zf = parse_zon("nothing here\n")
    assert not zf.zones
    assert zf.warnings
    assert zf.header == ["nothing here"]


def test_unparsable_data_line_is_kept_verbatim():
    text = "zone\nA, 3, 1, 2, 3, 4, 5, 6, 1, UNUSED\nbroken line\nend\n"
    zf = parse_zon(text)
    assert len(zf.zones) == 1
    assert zf.warnings
    assert format_zon(zf) == text        # nothing lost


# ── Round-trip ───────────────────────────────────────────────────

def test_text_round_trip_is_byte_exact():
    assert format_zon(parse_zon(VANILLA)) == VANILLA


def test_crlf_and_lf_are_preserved():
    lf = VANILLA.replace("\r\n", "\n")
    assert format_zon(parse_zon(lf)) == lf
    assert parse_zon(VANILLA).eol == "\r\n"


def test_utf8_comment_survives_latin1_read():
    """Cyrillic comments contain byte 0x85, which str.splitlines() treats
    as a line break — the parser must not split there."""
    text = ("zone\n# зона храма\nA, 3, 1, 2, 3, 4, 5, 6, 1, UNUSED\nend\n")
    raw = text.encode('utf-8').decode('latin-1')
    assert format_zon(parse_zon(raw)) == raw


def test_untouched_zone_keeps_its_original_line_after_float32():
    """A zone that made a Blender round-trip drifts in the last decimals;
    it must still be written as the original line."""
    z = parse_zone_line(
        "LC01, 3, 12634.818, 6381.449, -500.0, 16390.244, 8864.271, 500.0, 5, UNUSED")
    for axis in ('x1', 'y1', 'z1', 'x2', 'y2', 'z2'):
        setattr(z, axis, _f32(getattr(z, axis)))
    assert zone_line(z) == z.raw


def test_moved_zone_is_reformatted():
    z = parse_zone_line("A, 3, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 1, UNUSED")
    z.x1 = -10.5
    assert zone_line(z) == "A, 3, -10.5, 2.0, 3.0, 4.0, 5.0, 6.0, 1, UNUSED"


def test_reversed_bbox_is_flagged_but_not_silently_fixed():
    """The engine tests `x >= x1 && x <= x2`, so a swapped pair is dead
    data — report it, but never rewrite the file behind the user's back."""
    z = parse_zone_line(
        "WTH_LC, 4, 12500.0, 10500.0, -2000.0, 16500.0, 6000.0, 2000.0, 5, UNUSED")
    assert z.is_reversed
    assert z.bounds[0][1] == 6000.0 and z.bounds[1][1] == 10500.0
    assert zone_line(z) == z.raw


def test_file_round_trip(tmp_path):
    p = tmp_path / "map.zon"
    write_zon(str(p), ZonFile(zones=[
        Zone(name="LA01", zone_type=3, x1=480.0, y1=-3000.0, z1=-500.0,
             x2=3000.0, y2=-850.0, z2=500.0, level=1),
        Zone(name="SFSE", zone_type=0, x1=-1.5, y1=-2.25, z1=0.0,
             x2=1.5, y2=2.25, z2=200.0, level=2, gxt="SFSE"),
    ], eol="\n"))
    zf = read_zon(str(p))
    assert [z.name for z in zf.zones] == ["LA01", "SFSE"]
    assert zf.zones[1].gxt == "SFSE"
    assert abs(zf.zones[1].y1 + 2.25) < 1e-4
    assert format_zon(zf) == p.read_text(encoding='latin-1')


def test_format_keeps_three_decimals():
    assert format_zone_line(
        Zone(name="A", zone_type=3, x1=11569.5635, y2=-0.0004, level=9)
    ) == "A, 3, 11569.564, 0.0, 0.0, 0.0, 0.0, 0.0, 9, UNUSED"
