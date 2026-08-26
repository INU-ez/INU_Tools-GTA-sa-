# INU_tools.core.zon — GTA SA .zon reader / writer (data/map.zon, data/info.zon).
#
# Both files share one plain-text format: a single `zone` section, one line
# per zone, closed by `end`:
#
#     zone
#     # comment
#     LA01, 3, 480.0, -3000.0, -500.0, 3000.0, -850.0, 500.0, 1, UNUSED
#     end
#
# Columns: name, type, x1, y1, z1, x2, y2, z2, level, GXT-key.
#   type  — 0 navigation / info zone (info.zon), 3 map zone (map.zon).
#           Total conversions add their own (Project Eagle: 4 = weather).
#   level — island / region id: 0 generic, 1 LS, 2 SF, 3 LV; mods extend it.
#   GXT   — key of the on-screen zone name, `UNUSED` when there is none.
#
# The engine (CFileLoader::LoadLine) replaces every ',' with a space and then
# splits on whitespace, so a stray space inside a field silently shifts all
# the following columns. This parser reads lines exactly the same way — what
# Blender shows is what the game actually loads, typos included.
#
# Header, comments and blank lines survive the round-trip, and a zone that
# comes back unchanged is written as its original line, so import → export
# without edits leaves the file byte-identical.
#
# This module is pure (no bpy) so it is unit-testable and reusable.

from __future__ import annotations

import os
from dataclasses import dataclass, field


DEFAULT_GXT = "UNUSED"

# Coordinates come back from Blender as float32 (object transforms), so an
# untouched zone drifts by ~1e-3 at San Andreas' coordinate range. Anything
# below a centimetre counts as "not moved" and keeps the original line.
EPS = 0.01


@dataclass
class Zone:
    """One line of the `zone` section."""
    name: str = ""
    zone_type: int = 0
    x1: float = 0.0
    y1: float = 0.0
    z1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    z2: float = 0.0
    level: int = 0
    gxt: str = DEFAULT_GXT
    # Comment / blank lines that sat above this zone in the file.
    comment: list = field(default_factory=list)
    # The original line, verbatim — re-emitted when nothing changed.
    raw: str = ""

    @property
    def bounds(self):
        """((minX, minY, minZ), (maxX, maxY, maxZ)) — files in the wild do
        carry reversed pairs, so never assume 1 < 2."""
        return (
            (min(self.x1, self.x2), min(self.y1, self.y2), min(self.z1, self.z2)),
            (max(self.x1, self.x2), max(self.y1, self.y2), max(self.z1, self.z2)),
        )

    @property
    def is_reversed(self) -> bool:
        """True when a min/max pair is swapped. The engine tests
        `x >= x1 && x <= x2`, so such a zone can never match — it is dead
        data, worth reporting to the user."""
        return self.x1 > self.x2 or self.y1 > self.y2 or self.z1 > self.z2


@dataclass
class ZonFile:
    zones: list = field(default_factory=list)
    header: list = field(default_factory=list)        # lines before `zone`
    section_tail: list = field(default_factory=list)  # comments before `end`
    footer: list = field(default_factory=list)        # lines after `end`
    eol: str = "\r\n"
    warnings: list = field(default_factory=list)


# ── Parsing ───────────────────────────────────────────────────────────

def _int(tok: str) -> int:
    """sscanf("%d") stops at the first non-digit, so `500.0` in an int
    column reads as 500 instead of killing the whole line."""
    return int(float(tok))


def parse_zone_line(line: str):
    """One `zone` line → Zone, or None when it isn't one.

    Splits the way the engine does: commas are just separators, and so is
    whitespace. Fields past the GXT key are ignored (the engine ignores
    them too)."""
    toks = line.replace(',', ' ').split()
    if len(toks) < 9:
        return None
    try:
        z = Zone(
            name=toks[0],
            zone_type=_int(toks[1]),
            x1=float(toks[2]), y1=float(toks[3]), z1=float(toks[4]),
            x2=float(toks[5]), y2=float(toks[6]), z2=float(toks[7]),
            level=_int(toks[8]),
            gxt=toks[9] if len(toks) > 9 else DEFAULT_GXT,
        )
    except ValueError:
        return None
    z.raw = line.rstrip('\r\n')
    return z


def _is_comment(s: str) -> bool:
    return not s or s.startswith('#') or s.startswith(';')


def split_lines(text: str) -> list:
    """Split on real line breaks only.

    `str.splitlines()` would be wrong here: the file is read as latin-1 to
    keep every byte intact, and splitlines() also breaks on 0x85 / 0x0b /
    0x0c — bytes that sit inside perfectly normal UTF-8 Cyrillic letters
    ('х' is D1 85). That silently cut mod comments in half and corrupted
    them on write."""
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()                      # trailing newline, not an empty line
    return [ln[:-1] if ln.endswith('\r') else ln for ln in lines]


def parse_zon(text: str) -> ZonFile:
    """Parse .zon text. Unparsable data lines are kept verbatim (nothing is
    ever dropped) and reported through `warnings`."""
    zf = ZonFile()
    zf.eol = "\r\n" if "\r\n" in text else "\n"

    pending = []      # comment / blank lines waiting for their zone
    state = 'head'    # head → zone → tail

    for no, raw in enumerate(split_lines(text), start=1):
        s = raw.strip()

        if state == 'head':
            if s.lower() == 'zone':
                zf.header = pending
                pending = []
                state = 'zone'
            else:
                pending.append(raw)
            continue

        if state == 'zone':
            if s.lower() == 'end':
                zf.section_tail = pending
                pending = []
                state = 'tail'
                continue
            if _is_comment(s):
                pending.append(raw)
                continue
            z = parse_zone_line(s)
            if z is None:
                # Keep the line as-is so the export can't lose data.
                zf.warnings.append(f"{no}: {s[:60]}")
                pending.append(raw)
                continue
            if len(s.replace(',', ' ').split()) != 10:
                zf.warnings.append(
                    f"{no}: {z.name} — {len(s.replace(',', ' ').split())} "
                    f"tokens instead of 10")
            z.comment = pending
            pending = []
            zf.zones.append(z)
            continue

        # tail — everything after `end` is carried through untouched.
        pending.append(raw)

    if state == 'head':
        zf.header = pending
        zf.warnings.append("no `zone` section found")
    elif state == 'zone':
        # File ends without `end` — keep the trailing comments in place.
        zf.section_tail = pending
        zf.warnings.append("no `end` line — added on export")
    else:
        zf.footer = pending

    return zf


def read_zon(path: str) -> ZonFile:
    with open(path, encoding='latin-1', newline='') as f:
        return parse_zon(f.read())


# ── Writing ───────────────────────────────────────────────────────────

def _fmt_float(v) -> str:
    """3 decimals, trailing zeros stripped, always one decimal left —
    matches how the vanilla files are written (476.093, -500.0)."""
    s = f"{float(v):.3f}".rstrip('0').rstrip('.')
    if s in ('', '-', '-0'):
        s = '0'
    if '.' not in s:
        s += '.0'
    return s


def format_zone_line(z: Zone) -> str:
    return (f"{z.name}, {z.zone_type}, "
            f"{_fmt_float(z.x1)}, {_fmt_float(z.y1)}, {_fmt_float(z.z1)}, "
            f"{_fmt_float(z.x2)}, {_fmt_float(z.y2)}, {_fmt_float(z.z2)}, "
            f"{z.level}, {z.gxt or DEFAULT_GXT}")


def zones_equal(a: Zone, b: Zone, eps: float = EPS) -> bool:
    """Same zone, ignoring float32 round-trip noise. Bounds are compared
    normalised so a reversed-pair zone the user never touched still counts
    as unchanged (and keeps its original — deliberately broken — line)."""
    if (a.name, a.zone_type, a.level, a.gxt or DEFAULT_GXT) != \
       (b.name, b.zone_type, b.level, b.gxt or DEFAULT_GXT):
        return False
    for pa, pb in zip(a.bounds, b.bounds):
        for ca, cb in zip(pa, pb):
            if abs(ca - cb) > eps:
                return False
    return True


def zone_line(z: Zone) -> str:
    """Original line when the zone is unchanged, freshly formatted when it
    isn't — untouched zones stay byte-identical."""
    if z.raw:
        orig = parse_zone_line(z.raw)
        if orig is not None and zones_equal(orig, z):
            return z.raw
    return format_zone_line(z)


def format_zon(zf: ZonFile) -> str:
    # No generated banner: vanilla info.zon starts straight with `zone`,
    # and an injected line would break the byte-exact round-trip.
    out = list(zf.header)
    out.append("zone")
    for z in zf.zones:
        out.extend(z.comment)
        out.append(zone_line(z))
    out.extend(zf.section_tail)
    out.append("end")
    out.extend(zf.footer)
    return zf.eol.join(out) + zf.eol


def write_zon(path: str, zf: ZonFile) -> int:
    """Write the file (creating the folder if needed). Returns zone count."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, 'w', encoding='latin-1', newline='') as f:
        f.write(format_zon(zf))
    return len(zf.zones)
