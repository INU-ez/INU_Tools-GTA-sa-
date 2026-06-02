# INU_tools.core.cst
#
# Text serialisation of COL collision data in the format used by
# Steve M.'s "Collision File Editor II" (.cst). Two real-world dialects
# are read:
#
#   * New format (header line ``CST1``..``CST4``): comma-separated
#     sections ``<count>, <Name>`` — Vertex / Face / Sphere / Box /
#     ShadVert / ShadFace. One model per file (the model name comes
#     from the file name; the format has no MODEL/ID directive).
#
#   * Old 1.x format (``=> Spheres:`` / ``V 0: x; y; z`` …): semicolon-
#     separated, surface in ``[..]`` brackets.
#
# A third, INU-only flat dialect (``MODEL`` / ``VERTEX x y z`` …) that
# earlier INU builds emitted is still read for backward compatibility.
#
# Writing always emits the modern ``CST2`` format so the output opens
# directly in Collision File Editor II. Pure Python, no Blender import.

from __future__ import annotations

import os
import re
from typing import List

from .col import ColModel, ColSphere, ColBox, ColFace, Surface, Bounds, Vec3


def _num(s: str, cast=float):
    try:
        return cast(s)
    except (ValueError, TypeError):
        try:
            return cast(float(s))  # "1.0" -> int via float
        except (ValueError, TypeError):
            return cast(0)


def _surface_from_tokens(tokens):
    """Build Surface from up to 4 trailing tokens (material, flags,
    brightness, light)."""
    vals = [0, 0, 0, 0]
    for i, tok in enumerate(tokens[:4]):
        vals[i] = _num(tok, int)
    return Surface(material=vals[0], flags=vals[1],
                   brightness=vals[2], light=vals[3])


# ── Format sniffing ──────────────────────────────────────────────

_NEW_SECTION = re.compile(r'^\s*(\d+)\s*,\s*([A-Za-z]+)')


def _first_meaningful(lines) -> str:
    for raw in lines:
        s = raw.strip()
        if s and not s.startswith('#'):
            return s
    return ''


def read_cst(filepath: str) -> List[ColModel]:
    """Parse a CST file and return one ColModel per model block.

    Auto-detects the Collision File Editor II new/old dialects and the
    legacy INU flat dialect.
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    head = _first_meaningful(lines)
    name = os.path.splitext(os.path.basename(filepath))[0]

    if head[:3].upper() == 'CST':
        return _read_new(lines, name)
    if head.startswith('=>') or re.match(r'^[VFSB]\s+\d+\s*:', head):
        return _read_old(lines, name)
    return _read_legacy(lines)


# ── New format (CST1..CST4) ──────────────────────────────────────

def _split_csv(line: str):
    return [t.strip() for t in line.split(',') if t.strip() != '']


def _read_new(lines, name: str) -> List[ColModel]:
    model = ColModel(model_name=name)
    section = None  # current section name (lowercased)

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line[:3].upper() == 'CST':
            continue  # magic line — version derived from content below

        m = _NEW_SECTION.match(line)
        if m:
            section = m.group(2).lower()
            continue

        if section is None:
            continue
        tok = _split_csv(line)
        if not tok:
            continue

        if section.startswith('vertex') or section == 'vert':
            if len(tok) >= 3:
                model.vertices.append(Vec3(_num(tok[0]), _num(tok[1]), _num(tok[2])))
        elif section.startswith('shadvert') or section.startswith('shadowvert'):
            if len(tok) >= 3:
                model.shadow_vertices.append(
                    Vec3(_num(tok[0]), _num(tok[1]), _num(tok[2])))
        elif section.startswith('shadface') or section.startswith('shadowface'):
            if len(tok) >= 3:
                model.shadow_faces.append(ColFace(
                    a=_num(tok[0], int), b=_num(tok[1], int), c=_num(tok[2], int),
                    surface=_surface_from_tokens(tok[3:])))
        elif section.startswith('face'):
            if len(tok) >= 3:
                model.faces.append(ColFace(
                    a=_num(tok[0], int), b=_num(tok[1], int), c=_num(tok[2], int),
                    surface=_surface_from_tokens(tok[3:])))
        elif section.startswith('sphere'):
            if len(tok) >= 4:
                model.spheres.append(ColSphere(
                    center=Vec3(_num(tok[0]), _num(tok[1]), _num(tok[2])),
                    radius=_num(tok[3]),
                    surface=_surface_from_tokens(tok[4:])))
        elif section.startswith('box'):
            if len(tok) >= 6:
                model.boxes.append(ColBox(
                    bb_min=Vec3(_num(tok[0]), _num(tok[1]), _num(tok[2])),
                    bb_max=Vec3(_num(tok[3]), _num(tok[4]), _num(tok[5])),
                    surface=_surface_from_tokens(tok[6:])))

    # Collision File Editor II's "CST2" is a text-format generation
    # marker, not a COL version — both VC (COL2) and SA (COL3) export
    # as CST2. INU targets SA, so default to COL3 (version 3); this also
    # keeps surface IDs from being translated as if they were VC on a
    # later .col re-export. The presence of a shadow mesh confirms COL3.
    model.version = 3
    model.bounds = _bounds_from_verts(model.vertices or model.shadow_vertices)
    return [model]


# ── Old format (=> Spheres / V n: x; y; z …) ─────────────────────

def _semi_nums(s: str):
    return [t.strip() for t in s.replace('|', ';').split(';') if t.strip() != '']


def _bracket_surface(line: str) -> Surface:
    m = re.search(r'\[([^\]]*)\]', line)
    if not m:
        return Surface()
    return _surface_from_tokens([t.strip() for t in m.group(1).split(',') if t.strip()])


def _read_old(lines, name: str) -> List[ColModel]:
    model = ColModel(model_name=name)
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#') or line.startswith('=>'):
            continue
        kind = line[0].upper()
        body = line.split(':', 1)[1] if ':' in line else ''
        if kind == 'V':
            n = _semi_nums(body)
            if len(n) >= 3:
                model.vertices.append(Vec3(_num(n[0]), _num(n[1]), _num(n[2])))
        elif kind == 'F':
            seg = body.split('|', 1)[0]
            n = _semi_nums(seg)
            if len(n) >= 3:
                model.faces.append(ColFace(
                    a=_num(n[0], int), b=_num(n[1], int), c=_num(n[2], int),
                    surface=_bracket_surface(line)))
        elif kind == 'S':
            # "S 0: <radius>  |  x; y; z  |  [surf]"
            segs = body.split('|')
            radius = _num(_semi_nums(segs[0])[0]) if _semi_nums(segs[0]) else 0.0
            c = _semi_nums(segs[1]) if len(segs) > 1 else []
            if len(c) >= 3:
                model.spheres.append(ColSphere(
                    center=Vec3(_num(c[0]), _num(c[1]), _num(c[2])),
                    radius=radius, surface=_bracket_surface(line)))
        elif kind == 'B':
            segs = body.split('|')
            lo = _semi_nums(segs[0]) if segs else []
            hi = _semi_nums(segs[1]) if len(segs) > 1 else []
            if len(lo) >= 3 and len(hi) >= 3:
                model.boxes.append(ColBox(
                    bb_min=Vec3(_num(lo[0]), _num(lo[1]), _num(lo[2])),
                    bb_max=Vec3(_num(hi[0]), _num(hi[1]), _num(hi[2])),
                    surface=_bracket_surface(line)))
    model.version = 1
    model.bounds = _bounds_from_verts(model.vertices)
    return [model]


# ── Legacy INU flat format (MODEL / VERTEX x y z …) ──────────────

def _read_legacy(lines) -> List[ColModel]:
    models: List[ColModel] = []
    cur: ColModel | None = None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        tag = parts[0].upper()
        args = parts[1:]

        if tag == 'MODEL':
            if cur is not None:
                models.append(cur)
            cur = ColModel(model_name=' '.join(args) if args else '')
            continue
        if cur is None:
            cur = ColModel()

        if tag == 'ID' and args:
            cur.model_id = _num(args[0], int)
        elif tag == 'VERSION' and args:
            cur.version = _num(args[0], int)
        elif tag == 'BOUNDS' and len(args) >= 10:
            cur.bounds = Bounds(
                center=Vec3(_num(args[0]), _num(args[1]), _num(args[2])),
                radius=_num(args[3]),
                bb_min=Vec3(_num(args[4]), _num(args[5]), _num(args[6])),
                bb_max=Vec3(_num(args[7]), _num(args[8]), _num(args[9])))
        elif tag == 'SPHERE' and len(args) >= 4:
            cur.spheres.append(ColSphere(
                center=Vec3(_num(args[0]), _num(args[1]), _num(args[2])),
                radius=_num(args[3]), surface=_surface_from_tokens(args[4:])))
        elif tag == 'BOX' and len(args) >= 6:
            cur.boxes.append(ColBox(
                bb_min=Vec3(_num(args[0]), _num(args[1]), _num(args[2])),
                bb_max=Vec3(_num(args[3]), _num(args[4]), _num(args[5])),
                surface=_surface_from_tokens(args[6:])))
        elif tag == 'VERTEX' and len(args) >= 3:
            cur.vertices.append(Vec3(_num(args[0]), _num(args[1]), _num(args[2])))
        elif tag == 'FACE' and len(args) >= 3:
            cur.faces.append(ColFace(
                a=_num(args[0], int), b=_num(args[1], int), c=_num(args[2], int),
                surface=_surface_from_tokens(args[3:])))
        elif tag == 'SHADOW_VERTEX' and len(args) >= 3:
            cur.shadow_vertices.append(Vec3(_num(args[0]), _num(args[1]), _num(args[2])))
        elif tag == 'SHADOW_FACE' and len(args) >= 3:
            cur.shadow_faces.append(ColFace(
                a=_num(args[0], int), b=_num(args[1], int), c=_num(args[2], int),
                surface=_surface_from_tokens(args[3:])))
        elif tag == 'END':
            if cur is not None:
                models.append(cur)
                cur = None
    if cur is not None:
        models.append(cur)
    return models


# ── Helpers ──────────────────────────────────────────────────────

def _has_geometry(m: ColModel) -> bool:
    return bool(m.vertices or m.faces or m.spheres or m.boxes
                or m.shadow_vertices or m.shadow_faces)


def _bounds_from_verts(verts) -> Bounds:
    if not verts:
        return Bounds()
    xs = [v.x for v in verts]; ys = [v.y for v in verts]; zs = [v.z for v in verts]
    lo = Vec3(min(xs), min(ys), min(zs))
    hi = Vec3(max(xs), max(ys), max(zs))
    cx, cy, cz = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2
    r = max(((v.x - cx) ** 2 + (v.y - cy) ** 2 + (v.z - cz) ** 2) ** 0.5
            for v in verts)
    return Bounds(center=Vec3(cx, cy, cz), radius=r, bb_min=lo, bb_max=hi)


# ── Writing (modern CST2) ────────────────────────────────────────

def _fmt_num(v: float) -> str:
    s = f"{v:.6f}".rstrip('0')
    return s + '0' if s.endswith('.') else s


def _fmt_vec(v: Vec3) -> str:
    return f"{_fmt_num(v.x)}, {_fmt_num(v.y)}, {_fmt_num(v.z)}"


def _fmt_surface(s: Surface) -> str:
    return f"{s.material}, {s.flags}, {s.brightness}, {s.light}"


def _write_section(f, header: str, items, line_fn):
    if not items:
        return
    f.write(f"{len(items)}, {header}\n")
    for it in items:
        f.write(line_fn(it) + "\n")
    f.write("\n")


def write_cst(filepath: str, models: List[ColModel]) -> None:
    """Write a ColModel in Collision File Editor II ``CST2`` format.

    The format is one model per file, so only the first model is
    written (INU's CST export merges a selection into a single model).
    """
    if not models:
        models = [ColModel()]
    m = models[0]
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write("# Exported with INU Tools\n\n")
        f.write("CST2\n\n")
        _write_section(f, "Vertex", m.vertices, _fmt_vec)
        _write_section(f, "Face", m.faces,
                       lambda fc: f"{fc.a}, {fc.b}, {fc.c}, {_fmt_surface(fc.surface)}")
        _write_section(f, "Sphere", m.spheres,
                       lambda sp: f"{_fmt_vec(sp.center)}, {_fmt_num(sp.radius)}, {_fmt_surface(sp.surface)}")
        _write_section(f, "Box", m.boxes,
                       lambda bx: f"{_fmt_vec(bx.bb_min)}, {_fmt_vec(bx.bb_max)}, {_fmt_surface(bx.surface)}")
        _write_section(f, "ShadVert", m.shadow_vertices, _fmt_vec)
        _write_section(f, "ShadFace", m.shadow_faces,
                       lambda fc: f"{fc.a}, {fc.b}, {fc.c}, {_fmt_surface(fc.surface)}")
