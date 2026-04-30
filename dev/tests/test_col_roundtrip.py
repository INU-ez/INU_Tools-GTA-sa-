"""Round-trip tests for core/col.py — COL1/COL2/COL3 versions, spheres,
boxes, vertices+faces, shadow mesh, surface properties, multi-model
archives.

Runs with `pytest dev/tests/test_col_roundtrip.py`. Pure Python."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.col import (  # noqa: E402
    ColModel,
    ColFace,
    ColSphere,
    ColBox,
    Vec3,
    Bounds,
    Surface,
    write_col,
    read_col,
)


def _bounds(rad=2.0):
    return Bounds(
        center=Vec3(0.0, 0.0, 0.0), radius=rad,
        bb_min=Vec3(-1.0, -1.0, 0.0), bb_max=Vec3(1.0, 1.0, 1.0),
    )


def _model(version=3, name="m", **kw):
    m = ColModel(version=version, model_name=name, model_id=1234,
                 bounds=_bounds(), **kw)
    return m


# ── Versions ─────────────────────────────────────────────────────

def test_col1_basic_round_trip():
    m = _model(version=1,
               vertices=[Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0)],
               faces=[ColFace(a=0, b=1, c=2,
                              surface=Surface(material=4, light=1))])
    parsed = read_col(write_col([m]))[0]
    assert parsed.version == 1
    assert len(parsed.vertices) == 3
    assert len(parsed.faces) == 1
    # COL1 face surface stores material; light bytes vary by version
    assert parsed.faces[0].surface.material == 4


def test_col2_basic_round_trip():
    m = _model(version=2,
               vertices=[Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0)],
               faces=[ColFace(a=0, b=1, c=2,
                              surface=Surface(material=7, light=2))])
    parsed = read_col(write_col([m]))[0]
    assert parsed.version == 2
    assert len(parsed.vertices) == 3
    assert parsed.faces[0].surface.material == 7
    assert parsed.faces[0].surface.light == 2


def test_col3_basic_round_trip():
    m = _model(version=3,
               vertices=[Vec3(0, 0, 0), Vec3(2, 0, 0), Vec3(0, 2, 0)],
               faces=[ColFace(a=0, b=1, c=2,
                              surface=Surface(material=12, light=8))])
    parsed = read_col(write_col([m]))[0]
    assert parsed.version == 3
    assert len(parsed.faces) == 1
    assert parsed.faces[0].surface.material == 12
    assert parsed.faces[0].surface.light == 8


# ── Primitives ───────────────────────────────────────────────────

def test_spheres_round_trip():
    m = _model(version=3, spheres=[
        ColSphere(center=Vec3(0, 0, 0), radius=1.0,
                  surface=Surface(material=5)),
        ColSphere(center=Vec3(2, 2, 2), radius=0.5,
                  surface=Surface(material=10)),
    ])
    parsed = read_col(write_col([m]))[0]
    assert len(parsed.spheres) == 2
    assert abs(parsed.spheres[0].radius - 1.0) < 1e-5
    assert abs(parsed.spheres[1].radius - 0.5) < 1e-5
    assert parsed.spheres[0].surface.material == 5
    assert parsed.spheres[1].surface.material == 10


def test_boxes_round_trip():
    m = _model(version=3, boxes=[
        ColBox(bb_min=Vec3(-1, -1, 0), bb_max=Vec3(1, 1, 2),
               surface=Surface(material=3)),
    ])
    parsed = read_col(write_col([m]))[0]
    assert len(parsed.boxes) == 1
    b = parsed.boxes[0]
    assert abs(b.bb_min.x - (-1.0)) < 1e-3
    assert abs(b.bb_max.z - 2.0) < 1e-3
    assert b.surface.material == 3


def test_combined_primitives_and_mesh():
    """Same model with spheres + boxes + face mesh — typical for
    vehicles (chassis sphere set + wheel boxes + shadow mesh)."""
    m = _model(version=3,
               spheres=[ColSphere(center=Vec3(0, 0, 1), radius=1.5,
                                  surface=Surface(material=2))],
               boxes=[ColBox(bb_min=Vec3(-1, -1, 0), bb_max=Vec3(1, 1, 1),
                             surface=Surface(material=3))],
               vertices=[Vec3(0, 0, 0), Vec3(1, 0, 0),
                         Vec3(0, 1, 0), Vec3(1, 1, 0)],
               faces=[ColFace(a=0, b=1, c=2, surface=Surface(material=4)),
                      ColFace(a=1, b=3, c=2, surface=Surface(material=5))])
    parsed = read_col(write_col([m]))[0]
    assert len(parsed.spheres) == 1
    assert len(parsed.boxes) == 1
    assert len(parsed.vertices) == 4
    assert len(parsed.faces) == 2
    # Surface IDs preserved per face
    mats = {f.surface.material for f in parsed.faces}
    assert mats == {4, 5}


# ── Shadow mesh (COL3 only) ──────────────────────────────────────

def test_col3_shadow_mesh():
    m = _model(version=3,
               vertices=[Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0)],
               faces=[ColFace(a=0, b=1, c=2, surface=Surface(material=4))],
               shadow_vertices=[Vec3(0, 0, 0), Vec3(2, 0, 0), Vec3(0, 2, 0),
                                Vec3(2, 2, 0)],
               shadow_faces=[
                   ColFace(a=0, b=1, c=2, surface=Surface(material=0)),
                   ColFace(a=1, b=3, c=2, surface=Surface(material=0)),
               ])
    parsed = read_col(write_col([m]))[0]
    assert len(parsed.shadow_vertices) == 4
    assert len(parsed.shadow_faces) == 2


# ── Surface flags / brightness / light ───────────────────────────

def test_face_surface_material_and_light_preserved():
    """COL2/COL3 face surfaces only encode material(u8) + light(u8) —
    flags and brightness are stored on sphere/box primitives only.
    See [INU_tools/core/col.py _write_face_v2]."""
    m = _model(version=3,
               vertices=[Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0)],
               faces=[ColFace(a=0, b=1, c=2,
                              surface=Surface(material=42, light=7))])
    parsed = read_col(write_col([m]))[0]
    s = parsed.faces[0].surface
    assert s.material == 42
    assert s.light == 7


def test_sphere_surface_preserves_all_four_bytes():
    """Spheres write the full Surface struct (4 bytes — material/flags/
    brightness/light), so all fields round-trip."""
    m = _model(version=3, spheres=[
        ColSphere(center=Vec3(0, 0, 0), radius=1.0,
                  surface=Surface(material=42, flags=0x80,
                                  brightness=15, light=7)),
    ])
    parsed = read_col(write_col([m]))[0]
    s = parsed.spheres[0].surface
    assert s.material == 42
    assert s.flags == 0x80
    assert s.brightness == 15
    assert s.light == 7


def test_extreme_surface_ids():
    """GTA SA goes up to material id 178. Make sure the byte field doesn't
    silently truncate around the high end."""
    m = _model(version=3,
               vertices=[Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0)],
               faces=[ColFace(a=0, b=1, c=2,
                              surface=Surface(material=178))])
    parsed = read_col(write_col([m]))[0]
    assert parsed.faces[0].surface.material == 178


# ── Bounds round-trip ────────────────────────────────────────────

def test_bounds_round_trip():
    m = _model(version=3,
               vertices=[Vec3(0, 0, 0), Vec3(10, 0, 0), Vec3(0, 10, 5)])
    m.bounds = Bounds(center=Vec3(5.0, 5.0, 2.5), radius=12.5,
                      bb_min=Vec3(0, 0, 0), bb_max=Vec3(10, 10, 5))
    m.faces = [ColFace(a=0, b=1, c=2, surface=Surface(material=1))]
    parsed = read_col(write_col([m]))[0]
    b = parsed.bounds
    assert abs(b.center.x - 5.0) < 1e-3
    assert abs(b.center.y - 5.0) < 1e-3
    assert abs(b.radius - 12.5) < 1e-3
    assert abs(b.bb_max.x - 10.0) < 1e-3
    assert abs(b.bb_max.z - 5.0) < 1e-3


# ── Multi-model archive ──────────────────────────────────────────

def test_multi_model_archive():
    """vehicle.col stores many models in a single .col — order and
    names must round-trip exactly."""
    models = [
        _model(version=3, name="landstal",
               vertices=[Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0)],
               faces=[ColFace(a=0, b=1, c=2, surface=Surface(material=1))]),
        _model(version=3, name="bravura",
               vertices=[Vec3(0, 0, 0), Vec3(2, 0, 0), Vec3(0, 2, 0)],
               faces=[ColFace(a=0, b=1, c=2, surface=Surface(material=2))]),
        _model(version=3, name="buffalo",
               spheres=[ColSphere(center=Vec3(0, 0, 0), radius=1.0,
                                  surface=Surface(material=3))]),
    ]
    # Set distinct model_ids
    for i, m in enumerate(models):
        m.model_id = 400 + i

    parsed = read_col(write_col(models))
    assert len(parsed) == 3
    # Names preserved
    names = [m.model_name.lower().rstrip("\x00 ") for m in parsed]
    assert "landstal" in names[0]
    assert "bravura" in names[1]
    assert "buffalo" in names[2]
    # Order preserved
    assert parsed[0].model_id == 400
    assert parsed[1].model_id == 401
    assert parsed[2].model_id == 402


def test_mixed_versions_in_archive():
    """COL files can mix v1, v2, v3 models in the same archive."""
    models = [
        _model(version=1, name="v1model",
               vertices=[Vec3(0, 0, 0), Vec3(1, 0, 0), Vec3(0, 1, 0)],
               faces=[ColFace(a=0, b=1, c=2, surface=Surface(material=1))]),
        _model(version=3, name="v3model",
               vertices=[Vec3(0, 0, 0), Vec3(2, 0, 0), Vec3(0, 2, 0)],
               faces=[ColFace(a=0, b=1, c=2, surface=Surface(material=2))]),
    ]
    parsed = read_col(write_col(models))
    assert len(parsed) == 2
    assert parsed[0].version == 1
    assert parsed[1].version == 3


# ── Empty model edge cases ───────────────────────────────────────

def test_empty_model_no_geometry():
    """A model can have only bounds + no primitives at all (rare, but
    legal — used as placeholder)."""
    m = _model(version=3, name="empty_placeholder")
    parsed = read_col(write_col([m]))[0]
    assert parsed.model_name.lower().startswith("empty_placeholder")
    assert len(parsed.vertices) == 0
    assert len(parsed.faces) == 0
    assert len(parsed.spheres) == 0
    assert len(parsed.boxes) == 0


def test_only_spheres_no_mesh():
    """Pure-sphere collision (e.g. simple props)."""
    m = _model(version=3, name="ballonly", spheres=[
        ColSphere(center=Vec3(0, 0, 0), radius=2.0,
                  surface=Surface(material=5)),
    ])
    parsed = read_col(write_col([m]))[0]
    assert len(parsed.spheres) == 1
    assert len(parsed.faces) == 0
