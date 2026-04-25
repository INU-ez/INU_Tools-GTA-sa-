from pathlib import Path
import sys


# Lives at dev/tests/ — go up two to reach repo root.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.dff import (  # noqa: E402
    DffClump,
    DffFrame,
    DffGeometry,
    DffAtomic,
    Triangle,
    BoundingSphere,
    write_dff_file,
    read_dff_file,
)
from core.col import (  # noqa: E402
    ColModel,
    ColFace,
    Vec3,
    Bounds,
    Surface,
    write_col_file,
    read_col_file,
)


def test_dff_minimal_read_write_smoke(tmp_path):
    dff_path = tmp_path / "smoke.dff"

    geom = DffGeometry(
        vertices=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        normals=[(0.0, 0.0, 1.0)] * 3,
        triangles=[Triangle(a=0, b=1, c=2, material=0)],
        materials=[],
        bounding_sphere=BoundingSphere(x=0.0, y=0.0, z=0.0, radius=2.0),
    )
    clump = DffClump(
        frames=[DffFrame(name="root", parent=-1)],
        geometries=[geom],
        atomics=[DffAtomic(frame_index=0, geometry_index=0)],
    )

    write_dff_file(str(dff_path), clump)
    parsed = read_dff_file(str(dff_path))

    assert len(parsed.frames) == 1
    assert len(parsed.geometries) == 1
    assert len(parsed.atomics) == 1
    assert len(parsed.geometries[0].vertices) == 3
    assert len(parsed.geometries[0].triangles) == 1


def test_col_minimal_read_write_smoke(tmp_path):
    col_path = tmp_path / "smoke.col"
    model = ColModel(
        version=3,
        model_name="smoke",
        model_id=1337,
        bounds=Bounds(center=Vec3(0.0, 0.0, 0.0), radius=2.0, bb_min=Vec3(0.0, 0.0, 0.0), bb_max=Vec3(1.0, 1.0, 0.0)),
        vertices=[Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0)],
        faces=[ColFace(a=0, b=1, c=2, surface=Surface(material=1, light=2))],
    )

    write_col_file(str(col_path), [model])
    parsed_models = read_col_file(str(col_path))

    assert len(parsed_models) == 1
    parsed = parsed_models[0]
    assert parsed.model_name.lower().startswith("smoke")
    assert parsed.version == 3
    assert len(parsed.vertices) == 3
    assert len(parsed.faces) == 1
