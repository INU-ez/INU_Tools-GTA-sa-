"""Tests for core/cst.py — Collision File Editor II text formats.

Covers the modern CST2 section format, the old 1.x ``=>`` format, the
legacy INU flat MODEL format, and a write→read round-trip. Pure Python,
no Blender. Run with `pytest dev/tests/test_cst.py`."""

from pathlib import Path
import sys
import tempfile
import os


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.cst import read_cst, write_cst  # noqa: E402
from core.col import ColModel, ColFace, ColSphere, ColBox, Surface, Vec3  # noqa: E402


def _write_tmp(text: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".cst")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


CST2_SAMPLE = """\
# Exported with Collision File Editor II 0.4 BETA

CST2

5, Vertex
-1.0, -1.0, 2.0
1.0, -1.0, 2.0
-1.0, 1.0, 2.0
1.0, 1.0, 2.0
0.0, 0.0, 3.0

4, Face
0, 4, 1, 0, 0, 0, 255
1, 4, 3, 0, 0, 0, 255
3, 4, 2, 0, 0, 0, 255
2, 4, 0, 0, 0, 0, 255

1, Sphere
0.0, 0.0, 3.0, 0.5, 0, 0, 0, 64

1, Box
-1.0, -1.0, 0.0, 1.0, 1.0, 2.0, 0, 0, 0, 64

3, ShadVert
0.0, 0.0, 0.0
1.0, 0.0, 0.0
0.0, 1.0, 0.0

1, ShadFace
0, 1, 2, 0, 0, 0, 0
"""

OLD_SAMPLE = """\
# GTA Collision Script Exporter version 1.5 by Steve M.

=> Spheres:
S 0: 0.5  |  0.0; 0.0; 3.0  |  [7]

=> Boxes:
B 0: -1.0; -1.0; 0.0  |  1.0; 1.0; 2.0  |  [4]

=> Vertex Count: 3
V 0: -1.0; -1.0; 2.0
V 1: 1.0; -1.0; 2.0
V 2: -1.0; 1.0; 2.0

=> Face Count: 1
F 0: 0; 1; 2  |  [16]
"""

LEGACY_SAMPLE = """\
MODEL legacy
ID 5
VERSION 3
VERTEX 0 0 0
VERTEX 1 0 0
VERTEX 0 1 0
FACE 0 1 2 16 0 0 0
END
"""


def test_read_cst2_sections():
    path = _write_tmp(CST2_SAMPLE)
    try:
        models = read_cst(path)
    finally:
        os.remove(path)
    assert len(models) == 1
    m = models[0]
    assert len(m.vertices) == 5
    assert len(m.faces) == 4
    assert len(m.spheres) == 1
    assert len(m.boxes) == 1
    assert len(m.shadow_vertices) == 3
    assert len(m.shadow_faces) == 1
    # SA-format default
    assert m.version == 3
    # face surface columns map to (material, flags, brightness, light)
    f0 = m.faces[0]
    assert (f0.a, f0.b, f0.c) == (0, 4, 1)
    assert f0.surface.light == 255
    # sphere/box surface
    assert m.spheres[0].surface.light == 64
    assert m.spheres[0].radius == 0.5


def test_read_old_format():
    path = _write_tmp(OLD_SAMPLE)
    try:
        models = read_cst(path)
    finally:
        os.remove(path)
    m = models[0]
    assert len(m.vertices) == 3
    assert len(m.faces) == 1
    assert len(m.spheres) == 1
    assert len(m.boxes) == 1
    assert m.faces[0].surface.material == 16
    assert m.boxes[0].surface.material == 4


def test_read_legacy_model_format():
    path = _write_tmp(LEGACY_SAMPLE)
    try:
        models = read_cst(path)
    finally:
        os.remove(path)
    m = models[0]
    assert m.model_name == "legacy"
    assert m.model_id == 5
    assert len(m.vertices) == 3
    assert len(m.faces) == 1


def test_roundtrip_cst2():
    m = ColModel(version=3, model_name="rt")
    m.vertices = [Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0), Vec3(0, 0, 1)]
    m.faces = [
        ColFace(0, 1, 2, Surface(16, 0, 0, 200)),
        ColFace(0, 2, 3, Surface(16, 0, 0, 200)),
    ]
    m.spheres = [ColSphere(center=Vec3(0, 0, 0), radius=2.0, surface=Surface(4, 0, 0, 0))]
    m.boxes = [ColBox(bb_min=Vec3(-1, -1, -1), bb_max=Vec3(1, 1, 1), surface=Surface(7, 0, 0, 0))]
    m.shadow_vertices = [Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0)]
    m.shadow_faces = [ColFace(0, 1, 2, Surface(0, 0, 0, 0))]

    path = _write_tmp("")
    try:
        write_cst(path, [m])
        # Output must be the real CST2 dialect, not the legacy MODEL one.
        head = open(path, encoding="utf-8").read()
        assert "CST2" in head
        assert "MODEL" not in head

        back = read_cst(path)[0]
    finally:
        os.remove(path)

    assert len(back.vertices) == 4
    assert len(back.faces) == 2
    assert len(back.spheres) == 1
    assert len(back.boxes) == 1
    assert len(back.shadow_vertices) == 3
    assert len(back.shadow_faces) == 1
    assert back.faces[0].surface.light == 200
    assert back.boxes[0].surface.material == 7
