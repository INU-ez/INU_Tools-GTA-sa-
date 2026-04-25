"""Tests for the pure ``classify_bone_refs`` helper used during IFP export.

The full ``ops.ifp_export.validate_action_bones`` wrapper imports bpy at
module-load time and isn't reachable in CI. The actual logic — parsing
fcurve ``data_path`` strings and splitting bone names by armature
membership — lives in ``core.ifp.classify_bone_refs`` and is bpy-free,
so we test that directly. Wrapper behaviour (None / non-armature object
guards) is exercised in test_ifp_preview.py when bpy is available.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.ifp import classify_bone_refs  # noqa: E402


def test_splits_referenced_bones_by_membership():
    paths = [
        'pose.bones["Bip01 Pelvis"].rotation_quaternion',
        'pose.bones["Bip01 Pelvis"].location',
        'pose.bones["Bip01 Spine"].rotation_quaternion',
        'pose.bones["TypoBone"].location',
    ]
    arm_bones = ["Bip01 Pelvis", "Bip01 Spine", "Bip01 Head"]

    unknown, known = classify_bone_refs(paths, arm_bones)

    assert unknown == ["TypoBone"]
    assert known == ["Bip01 Pelvis", "Bip01 Spine"]


def test_ignores_object_level_fcurve_paths():
    # location / rotation_euler on an Object (not a bone) must not
    # produce a bogus reference — they're routine for armature root
    # animation and shouldn't show up in the validation report.
    paths = [
        'location',
        'rotation_euler',
        'pose.bones["Real"].location',
    ]
    unknown, known = classify_bone_refs(paths, ["Real"])
    assert unknown == []
    assert known == ["Real"]


def test_handles_empty_inputs():
    assert classify_bone_refs([], []) == ([], [])
    assert classify_bone_refs([], ["Bone"]) == ([], [])
    assert classify_bone_refs(['pose.bones["X"].location'], []) == (["X"], [])


def test_dedupes_repeated_references():
    # location.x/y/z + rotation_quaternion = 4 fcurves all referencing
    # the same bone. Output must list it once.
    paths = [
        'pose.bones["A"].location',
        'pose.bones["A"].location',
        'pose.bones["A"].location',
        'pose.bones["A"].rotation_quaternion',
    ]
    unknown, known = classify_bone_refs(paths, ["A"])
    assert unknown == []
    assert known == ["A"]


def test_handles_bone_names_with_spaces_and_punctuation():
    # GTA bone names use spaces ("Bip01 L Forearm") and digits;
    # parser must not break on either.
    paths = [
        'pose.bones["Bip01 L Forearm"].rotation_quaternion',
        'pose.bones["Bip01 L Hand1"].location',
        'pose.bones["weird-name_123"].location',
    ]
    arm_bones = ["Bip01 L Forearm", "Bip01 L Hand1"]
    unknown, known = classify_bone_refs(paths, arm_bones)
    assert unknown == ["weird-name_123"]
    assert known == ["Bip01 L Forearm", "Bip01 L Hand1"]


def test_unknown_bones_returned_sorted():
    paths = [
        'pose.bones["zebra"].location',
        'pose.bones["alpha"].location',
        'pose.bones["mango"].location',
    ]
    unknown, _ = classify_bone_refs(paths, [])
    assert unknown == sorted(unknown)
