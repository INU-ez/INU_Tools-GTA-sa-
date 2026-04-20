# INU_tools.core.cst
#
# Text ("CST") serialisation of COL collision data, compatible in spirit
# with Steve's COL Editor. The format is line-based; each directive
# names one structure of a ColModel. Multiple MODEL blocks per file are
# supported (COL archives). Pure Python, no Blender dependency.

from __future__ import annotations

from typing import List

from .col import ColModel, ColSphere, ColBox, ColFace, Surface, Bounds, Vec3


def _num(s: str, cast=float):
    try:
        return cast(s)
    except ValueError:
        return cast(0)


def _surface_from_tokens(tokens):
    """Build Surface from 0-4 trailing tokens (material, flags, brightness, light)."""
    defaults = [0, 0, 0, 0]
    for i, tok in enumerate(tokens[:4]):
        defaults[i] = _num(tok, int)
    return Surface(material=defaults[0], flags=defaults[1],
                   brightness=defaults[2], light=defaults[3])


def read_cst(filepath: str) -> List[ColModel]:
    """Parse a CST file and return one ColModel per MODEL block."""
    models: List[ColModel] = []
    cur: ColModel | None = None

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for raw in f:
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
                    bb_max=Vec3(_num(args[7]), _num(args[8]), _num(args[9])),
                )
            elif tag == 'SPHERE' and len(args) >= 4:
                cur.spheres.append(ColSphere(
                    center=Vec3(_num(args[0]), _num(args[1]), _num(args[2])),
                    radius=_num(args[3]),
                    surface=_surface_from_tokens(args[4:]),
                ))
            elif tag == 'BOX' and len(args) >= 6:
                cur.boxes.append(ColBox(
                    bb_min=Vec3(_num(args[0]), _num(args[1]), _num(args[2])),
                    bb_max=Vec3(_num(args[3]), _num(args[4]), _num(args[5])),
                    surface=_surface_from_tokens(args[6:]),
                ))
            elif tag == 'VERTEX' and len(args) >= 3:
                cur.vertices.append(Vec3(
                    _num(args[0]), _num(args[1]), _num(args[2])))
            elif tag == 'FACE' and len(args) >= 3:
                cur.faces.append(ColFace(
                    a=_num(args[0], int), b=_num(args[1], int), c=_num(args[2], int),
                    surface=_surface_from_tokens(args[3:]),
                ))
            elif tag == 'SHADOW_VERTEX' and len(args) >= 3:
                cur.shadow_vertices.append(Vec3(
                    _num(args[0]), _num(args[1]), _num(args[2])))
            elif tag == 'SHADOW_FACE' and len(args) >= 3:
                cur.shadow_faces.append(ColFace(
                    a=_num(args[0], int), b=_num(args[1], int), c=_num(args[2], int),
                    surface=_surface_from_tokens(args[3:]),
                ))
            elif tag == 'END':
                if cur is not None:
                    models.append(cur)
                    cur = None
    if cur is not None:
        models.append(cur)
    return models


def _fmt_vec(v: Vec3) -> str:
    return f"{v.x:.6f} {v.y:.6f} {v.z:.6f}"


def _fmt_surface(s: Surface) -> str:
    return f"{s.material} {s.flags} {s.brightness} {s.light}"


def write_cst(filepath: str, models: List[ColModel]) -> None:
    """Write a list of ColModel objects in CST text format."""
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        for m in models:
            f.write(f"MODEL {m.model_name}\n")
            f.write(f"ID {m.model_id}\n")
            f.write(f"VERSION {m.version}\n")
            b = m.bounds
            f.write(f"BOUNDS {_fmt_vec(b.center)} {b.radius:.6f} "
                    f"{_fmt_vec(b.bb_min)} {_fmt_vec(b.bb_max)}\n")
            for sp in m.spheres:
                f.write(f"SPHERE {_fmt_vec(sp.center)} {sp.radius:.6f} "
                        f"{_fmt_surface(sp.surface)}\n")
            for bx in m.boxes:
                f.write(f"BOX {_fmt_vec(bx.bb_min)} {_fmt_vec(bx.bb_max)} "
                        f"{_fmt_surface(bx.surface)}\n")
            for v in m.vertices:
                f.write(f"VERTEX {_fmt_vec(v)}\n")
            for fc in m.faces:
                f.write(f"FACE {fc.a} {fc.b} {fc.c} "
                        f"{_fmt_surface(fc.surface)}\n")
            for v in m.shadow_vertices:
                f.write(f"SHADOW_VERTEX {_fmt_vec(v)}\n")
            for fc in m.shadow_faces:
                f.write(f"SHADOW_FACE {fc.a} {fc.b} {fc.c} "
                        f"{_fmt_surface(fc.surface)}\n")
            f.write("END\n\n")
