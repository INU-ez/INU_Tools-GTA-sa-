"""Tests for the VC Layer System name-parsing helpers (Phase 1).

The actual operators in ``tools.vc_layers`` need bpy. The naming
convention — ``Day`` / ``Night`` for canonical prelight, ``VCL_D_…`` /
``VCL_N_…`` for editing layers — is decoded by pure helpers in
``core.vc_layers`` so the panel can classify any color attribute
without parsing in the bpy context.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.vc_layers import (  # noqa: E402
    VCL_PREFIX_DAY, VCL_PREFIX_NIGHT,
    BASE_DAY_NAME, BASE_NIGHT_NAME,
    MAX_LAYERS_PER_STACK,
    parse_vcl_attr_name, make_vcl_attr_name, classify_attribute,
    auto_label, count_layers_per_scope,
    promote_to_base, demote_to_layer,
)


# ─────────────────────────── parse_vcl_attr_name ──────────────────────

def test_parse_day_layer_returns_scope_and_label():
    assert parse_vcl_attr_name("VCL_D_окна") == ('DAY', "окна")


def test_parse_night_layer_returns_scope_and_label():
    assert parse_vcl_attr_name("VCL_N_тени_под_крышей") == \
           ('NIGHT', "тени_под_крышей")


def test_parse_returns_none_for_base_attributes():
    assert parse_vcl_attr_name("Day") is None
    assert parse_vcl_attr_name("Night") is None


def test_parse_returns_none_for_uv_or_unrelated_names():
    assert parse_vcl_attr_name("UVMap") is None
    assert parse_vcl_attr_name("Col") is None
    assert parse_vcl_attr_name("CustomPrelight") is None


def test_parse_distinguishes_VCL_prefix_from_other_VCs():
    # Edge case: name happens to start with VCL but not VCL_D_ / VCL_N_.
    assert parse_vcl_attr_name("VCLayer_thing") is None
    assert parse_vcl_attr_name("VCL_") is None


# ─────────────────────────── make_vcl_attr_name ──────────────────────

def test_make_day_label_compound():
    assert make_vcl_attr_name('DAY', "окна") == "VCL_D_окна"


def test_make_night_label_compound():
    assert make_vcl_attr_name('NIGHT', "shadow") == "VCL_N_shadow"


def test_make_rejects_unknown_scope():
    import pytest
    with pytest.raises(ValueError):
        make_vcl_attr_name('SUNSET', "x")


def test_make_round_trip_through_parse():
    for scope in ('DAY', 'NIGHT'):
        for label in ("a", "Layer_1", "тени", "Window glow"):
            name = make_vcl_attr_name(scope, label)
            assert parse_vcl_attr_name(name) == (scope, label)


# ─────────────────────────── classify_attribute ──────────────────────

def test_classify_canonical_bases():
    assert classify_attribute("Day") == 'BASE_DAY'
    assert classify_attribute("Night") == 'BASE_NIGHT'


def test_classify_layer_attributes():
    assert classify_attribute("VCL_D_x") == 'LAYER_DAY'
    assert classify_attribute("VCL_N_y") == 'LAYER_NIGHT'


def test_classify_other_includes_custom_prelight():
    """A user-renamed attribute («Custom_pre», «UVMap») falls in OTHER —
    panel shows it in the «base» section so they can demote if wanted."""
    assert classify_attribute("CustomPrelight") == 'OTHER'
    assert classify_attribute("UVMap") == 'OTHER'
    assert classify_attribute("") == 'OTHER'


# ─────────────────────────── auto_label ──────────────────────────────

def test_auto_label_picks_first_free_index():
    assert auto_label([]) == "Layer_1"
    assert auto_label({"Layer_1"}) == "Layer_2"
    assert auto_label({"Layer_1", "Layer_2", "Layer_4"}) == "Layer_3"


def test_auto_label_respects_custom_base():
    assert auto_label([], base="Окна") == "Окна_1"
    assert auto_label({"X_1"}, base="X") == "X_2"


def test_auto_label_handles_dense_existing():
    used = {f"Layer_{i}" for i in range(1, 10)}
    assert auto_label(used) == "Layer_10"


# ─────────────────────────── count_layers_per_scope ──────────────────

def test_count_empty_input():
    assert count_layers_per_scope([]) == (0, 0)


def test_count_only_bases_returns_zero():
    # Day/Night themselves are NOT VCL layers — they're the base.
    assert count_layers_per_scope(["Day", "Night", "UVMap"]) == (0, 0)


def test_count_mixed_stacks():
    names = [
        "Day", "Night",
        "VCL_D_a", "VCL_D_b", "VCL_D_c",
        "VCL_N_x", "VCL_N_y",
        "UVMap",
    ]
    assert count_layers_per_scope(names) == (3, 2)


def test_max_layers_per_stack_constant_is_ten():
    """If this constant changes, sync the panel header text + warning
    operators that reference it. Test guards the lock-in value."""
    assert MAX_LAYERS_PER_STACK == 10


# ─────────────────────────── promote / demote ────────────────────────

def test_promote_strips_day_prefix():
    assert promote_to_base("VCL_D_окна") == "окна"


def test_promote_strips_night_prefix():
    assert promote_to_base("VCL_N_тени") == "тени"


def test_promote_passes_through_non_vcl():
    assert promote_to_base("Day") == "Day"
    assert promote_to_base("UVMap") == "UVMap"


def test_demote_adds_correct_prefix():
    assert demote_to_layer("окна", 'DAY') == "VCL_D_окна"
    assert demote_to_layer("тени", 'NIGHT') == "VCL_N_тени"


def test_demote_passes_through_already_layer():
    """Demoting a layer is a no-op — caller probably wanted promote."""
    assert demote_to_layer("VCL_D_x", 'DAY') == "VCL_D_x"
    assert demote_to_layer("VCL_N_y", 'DAY') == "VCL_N_y"


# ─────────────────────────── full classification scenario ────────────

def test_realistic_mesh_attribute_classification():
    """Walk a plausible mesh's color attributes and bucket each one
    the way the panel will when it draws."""
    attrs = [
        "Day", "Night",
        "VCL_D_окна", "VCL_D_тени_крыши",
        "VCL_N_свет_фонарей",
        "UVMap",
        "Col",
        "MyExperiment",
    ]

    buckets = {'BASE_DAY': [], 'BASE_NIGHT': [],
               'LAYER_DAY': [], 'LAYER_NIGHT': [], 'OTHER': []}
    for a in attrs:
        buckets[classify_attribute(a)].append(a)

    assert buckets['BASE_DAY'] == ["Day"]
    assert buckets['BASE_NIGHT'] == ["Night"]
    assert buckets['LAYER_DAY'] == ["VCL_D_окна", "VCL_D_тени_крыши"]
    assert buckets['LAYER_NIGHT'] == ["VCL_N_свет_фонарей"]
    assert buckets['OTHER'] == ["UVMap", "Col", "MyExperiment"]
