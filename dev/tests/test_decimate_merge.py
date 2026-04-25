"""Integration test: decimate then merge into an existing IFP pack.

Real export flow does build → decimate → merge_ifp. Each piece is unit-tested
elsewhere (test_ifp_core); this test catches regressions where decimation
produces a state that merge_ifp can't read back correctly (e.g. dropping the
last keyframe, miscounting kf_count in the header, leaving a bone with zero
keys).
"""

from pathlib import Path
import sys


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
)


def _bone_with_redundant_middle(name: str, duration: float) -> AnimBone:
    """Three colinear keys — middle one is redundant under linear interp."""
    return AnimBone(
        name=name,
        bone_id=0,
        key_type=HAS_ROT | HAS_TRANS,
        keyframes=[
            KeyFrame(rotation=(0.0, 0.0, 0.0, 1.0),
                     translation=(0.0, 0.0, 0.0), time=0.0),
            KeyFrame(rotation=(0.0, 0.0, 0.0, 1.0),
                     translation=(duration * 0.5, 0.0, 0.0),
                     time=duration * 0.5),
            KeyFrame(rotation=(0.0, 0.0, 0.0, 1.0),
                     translation=(duration, 0.0, 0.0), time=duration),
        ],
    )


def test_decimate_then_merge_preserves_endpoints(tmp_path):
    path = tmp_path / "pack.ifp"

    # Existing pack on disk — one anim that merge will replace.
    existing = IFPFile(
        name="ped",
        animations=[
            Animation(name="WALK", bones=[
                AnimBone(name="OldBone", bone_id=0, key_type=HAS_ROT)
            ]),
        ],
    )
    write_ifp(str(path), existing)

    # New build with redundant keys → decimate → merge.
    new_anim = Animation(
        name="WALK",
        bones=[_bone_with_redundant_middle("Bip01 Pelvis", duration=1.0)],
    )
    new_pack = IFPFile(name="ped", animations=[new_anim])

    removed, total_before = decimate_ifp(new_pack, tol_rot=1e-6, tol_trans=1e-6)
    assert total_before == 3
    assert removed == 1

    # First and last keys must survive decimation — endpoints carry
    # the loop boundary and the game's interpolation depends on both.
    surviving = new_pack.animations[0].bones[0].keyframes
    assert len(surviving) == 2
    assert abs(surviving[0].time - 0.0) < 1e-6
    assert abs(surviving[-1].time - 1.0) < 1e-6

    replaced, added = merge_ifp(str(path), new_pack.animations)
    assert (replaced, added) == (1, 0)

    merged = read_ifp(str(path))
    assert [a.name for a in merged.animations] == ["WALK"]
    bones = merged.animations[0].bones
    assert len(bones) == 1
    assert bones[0].name == "Bip01 Pelvis"
    # 2 keys after decimation must round-trip through merge → write → read.
    assert len(bones[0].keyframes) == 2


def test_decimate_skips_bones_with_two_or_fewer_keys(tmp_path):
    """Decimate must never empty a bone — only middles are removable."""
    pack = IFPFile(
        name="ped",
        animations=[
            Animation(name="A", bones=[
                AnimBone(
                    name="ShortBone", bone_id=0,
                    key_type=HAS_ROT | HAS_TRANS,
                    keyframes=[
                        KeyFrame(rotation=(0.0, 0.0, 0.0, 1.0),
                                 translation=(0.0, 0.0, 0.0), time=0.0),
                        KeyFrame(rotation=(0.0, 0.0, 0.0, 1.0),
                                 translation=(0.0, 0.0, 0.0), time=1.0),
                    ],
                ),
            ]),
        ],
    )

    removed, total_before = decimate_ifp(pack, tol_rot=1.0, tol_trans=1.0)
    assert total_before == 2
    assert removed == 0
    assert len(pack.animations[0].bones[0].keyframes) == 2


def test_decimate_then_merge_appends_new_anim(tmp_path):
    path = tmp_path / "pack.ifp"
    existing = IFPFile(
        name="ped",
        animations=[
            Animation(name="WALK", bones=[
                AnimBone(name="Bone", bone_id=0, key_type=HAS_ROT)
            ]),
        ],
    )
    write_ifp(str(path), existing)

    new_pack = IFPFile(name="ped", animations=[
        Animation(name="RUN", bones=[
            _bone_with_redundant_middle("Bip01 Pelvis", duration=0.8),
        ]),
    ])
    decimate_ifp(new_pack, tol_rot=1e-6, tol_trans=1e-6)

    replaced, added = merge_ifp(str(path), new_pack.animations)
    assert (replaced, added) == (0, 1)

    merged = read_ifp(str(path))
    names = sorted(a.name.upper() for a in merged.animations)
    assert names == ["RUN", "WALK"]
