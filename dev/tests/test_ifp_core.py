from pathlib import Path
import sys


# Import core.ifp without importing Blender-dependent INU_tools package root.
# Lives at dev/tests/ — go up two to reach repo root.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.ifp import (  # noqa: E402
    IFPFile,
    Animation,
    AnimBone,
    KeyFrame,
    HAS_ROT,
    HAS_TRANS,
    write_ifp,
    read_ifp,
    decimate_ifp,
    merge_ifp,
    roundtrip_test,
)


def _sample_ifp() -> IFPFile:
    bone = AnimBone(
        name="Bip01 Pelvis",
        bone_id=0,
        key_type=HAS_ROT | HAS_TRANS,
        keyframes=[
            KeyFrame(
                rotation=(0.0, 0.0, 0.0, 1.0),
                translation=(0.0, 0.0, 0.0),
                time=0.0,
            ),
            KeyFrame(
                rotation=(0.0, 0.1, 0.0, 0.995),
                translation=(0.1, 0.0, 0.0),
                time=1.0,
            ),
        ],
    )
    return IFPFile(name="ped", animations=[Animation(name="WALK", bones=[bone])])


def test_write_read_ifp_roundtrip_counts(tmp_path):
    src = _sample_ifp()
    path = tmp_path / "sample.ifp"

    count = write_ifp(str(path), src)
    parsed = read_ifp(str(path))

    assert count == 1
    assert parsed.name == "ped"
    assert len(parsed.animations) == 1
    assert parsed.animations[0].name == "WALK"
    assert len(parsed.animations[0].bones) == 1
    assert len(parsed.animations[0].bones[0].keyframes) == 2


def test_roundtrip_test_reports_no_structural_loss(tmp_path):
    src = _sample_ifp()
    path = tmp_path / "sample.ifp"
    write_ifp(str(path), src)

    report = roundtrip_test(str(path))

    assert report["error"] is None
    assert report["anims_in"] == report["anims_out"] == 1
    assert report["bones_in"] == report["bones_out"] == 1
    assert report["keyframes_in"] == report["keyframes_out"] == 2
    assert report["missing_anims"] == []
    assert report["missing_bones"] == {}
    assert report["kf_mismatches"] == []


def test_decimate_ifp_removes_redundant_middle_key():
    linear_bone = AnimBone(
        name="Bone",
        bone_id=1,
        key_type=HAS_ROT | HAS_TRANS,
        keyframes=[
            KeyFrame(rotation=(0.0, 0.0, 0.0, 1.0), translation=(0.0, 0.0, 0.0), time=0.0),
            KeyFrame(rotation=(0.0, 0.0, 0.0, 1.0), translation=(0.5, 0.0, 0.0), time=0.5),
            KeyFrame(rotation=(0.0, 0.0, 0.0, 1.0), translation=(1.0, 0.0, 0.0), time=1.0),
        ],
    )
    ifp = IFPFile(name="ped", animations=[Animation(name="A", bones=[linear_bone])])

    removed, total_before = decimate_ifp(ifp, tol_rot=1e-6, tol_trans=1e-6)

    assert total_before == 3
    assert removed == 1
    assert len(ifp.animations[0].bones[0].keyframes) == 2


def test_merge_ifp_replaces_and_adds(tmp_path):
    path = tmp_path / "pack.ifp"

    base = IFPFile(
        name="ped",
        animations=[
            Animation(name="WALK", bones=[AnimBone(name="Bone", bone_id=0, key_type=HAS_ROT)]),
        ],
    )
    write_ifp(str(path), base)

    replaced, added = merge_ifp(
        str(path),
        [
            Animation(name="walk", bones=[AnimBone(name="Bone2", bone_id=2, key_type=HAS_ROT)]),
            Animation(name="RUN", bones=[AnimBone(name="Bone3", bone_id=3, key_type=HAS_TRANS)]),
        ],
    )
    merged = read_ifp(str(path))

    assert replaced == 1
    assert added == 1
    assert len(merged.animations) == 2
    assert {a.name.lower() for a in merged.animations} == {"walk", "run"}


def test_merge_ifp_creates_new_pack_when_missing(tmp_path):
    path = tmp_path / "new_pack.ifp"
    replaced, added = merge_ifp(
        str(path),
        [Animation(name="IDLE", bones=[AnimBone(name="B", bone_id=0, key_type=HAS_ROT)])],
        package_name="custom_pack",
    )
    merged = read_ifp(str(path))

    assert replaced == 0
    assert added == 1
    assert merged.name == "custom_pack"
    assert [a.name for a in merged.animations] == ["IDLE"]
