"""Tests for the pure check functions in core/validate.py.

The bpy-side adapters in ops/validate_scene.py and the panel that
draws the results aren't covered here — they need a Blender session.
The rules themselves (which input combinations produce which issues)
live in core/validate.py and are exercised directly.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.validate import (  # noqa: E402
    check_paintjobs,
    check_quaternions,
    check_uv_anim_night_vcols,
    check_damage_pairs,
    check_orphan_models,
    check_orphan_2dfx,
    check_duplicate_model_ids,
    check_empty_meshes,
    check_large_meshes,
    check_materials_without_texture,
    check_suffix_consistency,
    check_object_scale,
    check_light_beam_asi,
)


# ── Paintjobs ───────────────────────────────────────────────────────


def test_paintjob_clean_scene_yields_no_issues():
    issues = check_paintjobs([])
    assert issues == []


def test_paintjob_material_without_slots_is_ignored():
    """A material with no paintjob slots at all isn't part of the
    paintjob feature and shouldn't get scolded for missing a base."""
    materials = [dict(name='body', alt1=False, alt2=False, has_base=False)]
    assert check_paintjobs(materials) == []


def test_paintjob_only_alt1_filled_warns():
    materials = [dict(name='body', alt1=True, alt2=False, has_base=True)]
    issues = check_paintjobs(materials)
    assert len(issues) == 1
    assert issues[0]['severity'] == 'WARNING'
    assert issues[0]['target_name'] == 'body'
    assert 'Paintjob 1' in issues[0]['message']


def test_paintjob_only_alt2_filled_warns():
    materials = [dict(name='body', alt1=False, alt2=True, has_base=True)]
    issues = check_paintjobs(materials)
    assert len(issues) == 1
    assert 'Paintjob 2' in issues[0]['message']


def test_paintjob_both_slots_no_base_warns():
    materials = [dict(name='body', alt1=True, alt2=True, has_base=False)]
    issues = check_paintjobs(materials)
    assert len(issues) == 1
    assert 'нет основной текстуры' in issues[0]['message']


def test_paintjob_complete_setup_clean():
    materials = [dict(name='body', alt1=True, alt2=True, has_base=True)]
    assert check_paintjobs(materials) == []


# ── Quaternions ─────────────────────────────────────────────────────


def test_quat_unit_quaternions_clean():
    actions = [dict(name='walk',
                    quat_groups=[[1.0, 0.0, 0.0, 0.0],
                                 [0.7071, 0.7071, 0.0, 0.0]])]
    assert check_quaternions(actions) == []


def test_quat_non_unit_reports_info():
    """Non-unit quats are INFO, not WARNING — the IFP exporter
    normalises on the fly, so dirty Action data doesn't break the
    actual export. The check is for viewport preview correctness."""
    actions = [dict(name='walk',
                    quat_groups=[[2.0, 0.0, 0.0, 0.0]])]  # |q|=2
    issues = check_quaternions(actions)
    assert len(issues) == 1
    assert issues[0]['severity'] == 'INFO'
    assert issues[0]['target_name'] == 'walk'
    assert issues[0]['target_kind'] == 'ACTION'
    assert issues[0]['fix_op_id'] == 'gtatools.validate_fix_quaternions'
    assert issues[0]['fix_arg'] == 'walk'


def test_quat_wrong_arity_skipped():
    """A 'group' that doesn't have 4 components shouldn't crash the
    check — we just skip it."""
    actions = [dict(name='broken', quat_groups=[[1.0, 0.0]])]
    assert check_quaternions(actions) == []


def test_quat_eps_tolerates_tiny_drift():
    """Floats from fcurves aren't bit-exact; values inside ±1e-3 of
    unit length should be accepted as 'normalised'."""
    actions = [dict(name='clean',
                    quat_groups=[[1.0001, 0.0, 0.0, 0.0]])]
    assert check_quaternions(actions) == []


def test_quat_counts_bad_keys_in_message():
    actions = [dict(name='walk',
                    quat_groups=[[1.0, 0.0, 0.0, 0.0],
                                 [2.0, 0.0, 0.0, 0.0],
                                 [3.0, 0.0, 0.0, 0.0]])]
    issues = check_quaternions(actions)
    assert len(issues) == 1
    assert issues[0]['message'].startswith('2 ')  # 2 bad out of 3


# ── UV-anim × night vcols ───────────────────────────────────────────


def test_uv_anim_no_night_clean():
    """UV-anim material with day-only prelight → animation plays fine."""
    meshes = [dict(name='sign', has_uv_anim=True,
                   night_flag=False, has_night_vcol=False)]
    assert check_uv_anim_night_vcols(meshes) == []


def test_night_without_uv_anim_clean():
    """Night vcols are fine on their own — only the combo breaks."""
    meshes = [dict(name='wall', has_uv_anim=False,
                   night_flag=True, has_night_vcol=True)]
    assert check_uv_anim_night_vcols(meshes) == []


def test_uv_anim_with_night_flag_warns():
    meshes = [dict(name='sign', has_uv_anim=True,
                   night_flag=True, has_night_vcol=False)]
    issues = check_uv_anim_night_vcols(meshes)
    assert len(issues) == 1
    assert issues[0]['severity'] == 'WARNING'
    assert issues[0]['target_kind'] == 'OBJECT'
    assert issues[0]['target_name'] == 'sign'


def test_uv_anim_with_night_vcol_attr_warns():
    """Night detected via a colour attribute even if the flag is off."""
    meshes = [dict(name='sign', has_uv_anim=True,
                   night_flag=False, has_night_vcol=True)]
    assert len(check_uv_anim_night_vcols(meshes)) == 1


# ── _ok / _dam pairs ────────────────────────────────────────────────


def test_pairs_clean_when_complete():
    names = ['door1_ok', 'door1_dam', 'wing_ok', 'wing_dam']
    assert check_damage_pairs(names) == []


def test_pairs_orphan_ok_warns():
    names = ['door1_ok']
    issues = check_damage_pairs(names)
    assert len(issues) == 1
    assert issues[0]['target_name'] == 'door1_ok'
    assert '_dam' in issues[0]['message']


def test_pairs_orphan_dam_warns():
    names = ['door1_dam']
    issues = check_damage_pairs(names)
    assert len(issues) == 1
    assert issues[0]['target_name'] == 'door1_dam'
    assert '_ok' in issues[0]['message']


def test_pairs_unrelated_meshes_ignored():
    """Meshes without _ok/_dam suffix shouldn't show up in the report."""
    names = ['chassis', 'wheel_lf', 'door1_ok', 'door1_dam']
    assert check_damage_pairs(names) == []


def test_pairs_mixed_orphans_each_listed():
    names = ['a_ok', 'b_dam', 'c_ok', 'c_dam']  # a missing _dam, b missing _ok
    issues = check_damage_pairs(names)
    assert len(issues) == 2
    targets = sorted(i['target_name'] for i in issues)
    assert targets == ['a_ok', 'b_dam']


# ── Orphan models (LOD / COL without main DFF) ──────────────────────


def test_orphan_models_complete_set_clean():
    """DFF + LOD + COL with matching base names — no orphans."""
    models = [
        dict(name='body',     type='DFF', base='body'),
        dict(name='body_LOD', type='LOD', base='body'),
        dict(name='body_COL', type='COL', base='body'),
    ]
    assert check_orphan_models(models) == []


def test_orphan_lod_without_main_dff_warns():
    models = [dict(name='wheel_LOD', type='LOD', base='wheel')]
    issues = check_orphan_models(models)
    assert len(issues) == 1
    assert issues[0]['target_name'] == 'wheel_LOD'
    assert issues[0]['category'] == 'OrphanModel'
    assert 'LOD' in issues[0]['message']


def test_orphan_col_without_main_dff_warns():
    models = [dict(name='wheel_COL', type='COL', base='wheel')]
    issues = check_orphan_models(models)
    assert len(issues) == 1
    assert issues[0]['target_name'] == 'wheel_COL'
    assert 'COL' in issues[0]['message']


def test_orphan_models_case_insensitive_base_match():
    """`Body_LOD` and `body` should pair regardless of case."""
    models = [
        dict(name='Body',     type='DFF', base='Body'),
        dict(name='body_LOD', type='LOD', base='body'),
    ]
    assert check_orphan_models(models) == []


def test_orphan_models_lod_and_col_both_flagged():
    """When both LOD and COL exist for a base without a DFF, two
    issues are reported (one per orphan kind)."""
    models = [
        dict(name='door_LOD', type='LOD', base='door'),
        dict(name='door_COL', type='COL', base='door'),
    ]
    issues = check_orphan_models(models)
    assert len(issues) == 2
    targets = sorted(i['target_name'] for i in issues)
    assert targets == ['door_COL', 'door_LOD']


# ── Orphan 2DFX (Empty without MESH parent) ─────────────────────────


def test_orphan_2dfx_attached_to_mesh_clean():
    fx = [dict(name='fx_light_01', parent_kind='MESH')]
    assert check_orphan_2dfx(fx) == []


def test_orphan_2dfx_no_parent_warns():
    fx = [dict(name='fx_light_01', parent_kind=None)]
    issues = check_orphan_2dfx(fx)
    assert len(issues) == 1
    assert issues[0]['category'] == 'Orphan2DFX'
    assert issues[0]['target_name'] == 'fx_light_01'


def test_orphan_2dfx_parented_to_empty_warns():
    """Parenting a 2DFX to another Empty (e.g. a dummy hierarchy
    organiser) doesn't make it part of any DFF atomic — the export
    looks only at MESH parents."""
    fx = [dict(name='fx_light_01', parent_kind='EMPTY')]
    issues = check_orphan_2dfx(fx)
    assert len(issues) == 1
    assert 'EMPTY' in issues[0]['message']


def test_orphan_2dfx_parented_to_armature_warns():
    fx = [dict(name='fx_light_01', parent_kind='ARMATURE')]
    issues = check_orphan_2dfx(fx)
    assert len(issues) == 1
    assert 'ARMATURE' in issues[0]['message']


# ── Duplicate model_id (A) ──────────────────────────────────────────


def test_duplicate_id_unique_ids_clean():
    objs = [dict(name='a', model_id=100),
            dict(name='b', model_id=101)]
    assert check_duplicate_model_ids(objs) == []


def test_duplicate_id_zero_is_not_duplicate():
    """Multiple objects with model_id == 0 are auto-assigned at export
    time — they don't collide."""
    objs = [dict(name='a', model_id=0), dict(name='b', model_id=0)]
    assert check_duplicate_model_ids(objs) == []


def test_duplicate_id_collision_reports_error():
    objs = [dict(name='a', model_id=42),
            dict(name='b', model_id=42)]
    issues = check_duplicate_model_ids(objs)
    assert len(issues) == 1
    assert issues[0]['severity'] == 'ERROR'
    assert issues[0]['category'] == 'DuplicateID'
    assert 'a' in issues[0]['message'] and 'b' in issues[0]['message']


def test_duplicate_id_three_way_collision():
    objs = [dict(name='a', model_id=7),
            dict(name='b', model_id=7),
            dict(name='c', model_id=7)]
    issues = check_duplicate_model_ids(objs)
    assert len(issues) == 1
    assert issues[0]['target_name'] == 'a'  # first sorted name


def test_duplicate_id_blender_dups_not_collision():
    """``body`` + ``body.001`` share model_id by design (Shift+D
    copies inherit it for Map Export's repeat-instances flow).
    Stripping the .NNN suffix folds them into one logical model."""
    objs = [dict(name='body', model_id=42),
            dict(name='body.001', model_id=42)]
    assert check_duplicate_model_ids(objs) == []


def test_duplicate_id_dups_plus_real_collision_flagged():
    """If ``body`` and ``body.001`` (dups) collide WITH ``wing``
    (different model), report the real collision and don't add
    noise from the dup pair."""
    objs = [dict(name='body', model_id=42),
            dict(name='body.001', model_id=42),
            dict(name='body.002', model_id=42),
            dict(name='wing', model_id=42)]
    issues = check_duplicate_model_ids(objs)
    assert len(issues) == 1
    # message should list 2 distinct logical objects, not 4 names
    assert 'body' in issues[0]['message']
    assert 'wing' in issues[0]['message']
    assert 'body.001' not in issues[0]['message']
    assert '2' in issues[0]['message']  # "2 разными моделями"


def test_duplicate_id_strip_only_exact_3digit_form():
    """Names like 'foo.something' or 'foo.12' don't match Blender's
    .NNN dup pattern — they're user-typed and should NOT be stripped.
    """
    objs = [dict(name='foo.something', model_id=10),
            dict(name='foo.12',        model_id=10)]
    issues = check_duplicate_model_ids(objs)
    # Both names are distinct logical models → real collision.
    assert len(issues) == 1


# ── Empty mesh (B) ──────────────────────────────────────────────────


def test_empty_mesh_zero_verts_warns():
    meshes = [dict(name='ghost', vert_count=0)]
    issues = check_empty_meshes(meshes)
    assert len(issues) == 1
    assert issues[0]['category'] == 'EmptyMesh'


def test_empty_mesh_normal_clean():
    meshes = [dict(name='cube', vert_count=8)]
    assert check_empty_meshes(meshes) == []


# ── Large mesh (E) ──────────────────────────────────────────────────


def test_large_mesh_under_threshold_clean():
    meshes = [dict(name='small', vert_count=1000)]
    assert check_large_meshes(meshes) == []


def test_large_mesh_over_threshold_reports_info():
    meshes = [dict(name='huge', vert_count=40000)]
    issues = check_large_meshes(meshes)
    assert len(issues) == 1
    assert issues[0]['severity'] == 'INFO'
    assert '40000' in issues[0]['message']


def test_large_mesh_threshold_param_overrides_default():
    """Test sets threshold=100 to verify the threshold knob actually
    governs the cutoff (and isn't hardcoded)."""
    meshes = [dict(name='m', vert_count=200)]
    assert len(check_large_meshes(meshes, threshold=100)) == 1
    assert len(check_large_meshes(meshes, threshold=300)) == 0


# ── Material without texture (F) ────────────────────────────────────


def test_no_texture_unused_material_ignored():
    """Unused materials shouldn't bloat the report — they get cleaned
    up by other tools."""
    materials = [dict(name='orphan', has_base=False, used_on_mesh=False)]
    assert check_materials_without_texture(materials) == []


def test_no_texture_used_without_base_warns():
    materials = [dict(name='body', has_base=False, used_on_mesh=True)]
    issues = check_materials_without_texture(materials)
    assert len(issues) == 1
    assert issues[0]['category'] == 'NoTexture'
    assert issues[0]['target_name'] == 'body'


def test_no_texture_used_with_base_clean():
    materials = [dict(name='body', has_base=True, used_on_mesh=True)]
    assert check_materials_without_texture(materials) == []


def test_no_texture_col_surface_skipped():
    """COL surface materials are flag-only by design — no warning even
    when has_base=False and the material is used on a mesh."""
    materials = [dict(name='COLlight_d9_n8',
                      has_base=False,
                      used_on_mesh=True,
                      is_col_surface=True)]
    assert check_materials_without_texture(materials) == []


def test_no_texture_col_flag_overrides_used_on_mesh():
    """Even if the adapter incorrectly counted the COL material as
    used_on_mesh (e.g. it's also assigned to a regular mesh by
    mistake), the is_col_surface flag still skips the warning — the
    material itself is COL by definition and the user shouldn't be
    bothered about textures on it."""
    materials = [dict(name='COL_42',
                      has_base=False,
                      used_on_mesh=True,
                      is_col_surface=True)]
    assert check_materials_without_texture(materials) == []


# ── Suffix consistency (H) ──────────────────────────────────────────


_DEFAULT_SFX = {'DFF': '_DFF', 'LOD': '_LOD', 'COL': '_COL'}


def test_suffix_correct_separator_clean():
    names = ['body_DFF', 'body_LOD', 'body_COL']
    assert check_suffix_consistency(names, _DEFAULT_SFX) == []


def test_suffix_dot_when_underscore_configured_warns():
    """Settings expect '_DFF' but the user typed 'body.DFF'."""
    names = ['body.DFF']
    issues = check_suffix_consistency(names, _DEFAULT_SFX)
    assert len(issues) == 1
    assert issues[0]['category'] == 'SuffixMismatch'
    assert '.DFF' in issues[0]['message']
    assert '_DFF' in issues[0]['message']


def test_suffix_double_suffix_warns():
    """body_LOD_DFF — two type-suffixes piled on."""
    names = ['body_LOD_DFF']
    issues = check_suffix_consistency(names, _DEFAULT_SFX)
    assert len(issues) == 1
    assert 'лишний суффикс' in issues[0]['message']


def test_suffix_dot_when_underscore_not_configured_for_lod():
    """Mismatch detection works for any of DFF/LOD/COL, not just DFF."""
    names = ['body.LOD']
    issues = check_suffix_consistency(names, _DEFAULT_SFX)
    assert len(issues) == 1
    assert '.LOD' in issues[0]['message']


def test_suffix_custom_config_respected():
    """If user configured '_low' as LOD suffix, the check uses that
    rather than the hardcoded default."""
    custom = {'DFF': '_DFF', 'LOD': '_low', 'COL': '_COL'}
    names = ['body_low']  # matches custom config — clean
    assert check_suffix_consistency(names, custom) == []
    names_bad = ['body.low']
    issues = check_suffix_consistency(names_bad, custom)
    assert len(issues) == 1


# ── Object scale (D) ────────────────────────────────────────────────


def test_scale_unit_clean():
    objs = [dict(name='cube', scale=(1.0, 1.0, 1.0))]
    assert check_object_scale(objs) == []


def test_scale_negative_axis_warns():
    """Mirroring via S X -1 without Apply Scale flips the mesh."""
    objs = [dict(name='mirror', scale=(-1.0, 1.0, 1.0))]
    issues = check_object_scale(objs)
    assert len(issues) == 1
    assert issues[0]['severity'] == 'WARNING'
    assert issues[0]['category'] == 'BadScale'


def test_scale_non_uniform_reports_info():
    objs = [dict(name='stretched', scale=(2.0, 1.0, 1.0))]
    issues = check_object_scale(objs)
    assert len(issues) == 1
    assert issues[0]['severity'] == 'INFO'


def test_scale_uniform_non_one_clean():
    """Uniform scale (e.g. 2,2,2) is intentionally not flagged — too
    common during WIP and Apply Transforms is one keystroke away."""
    objs = [dict(name='big', scale=(2.0, 2.0, 2.0))]
    assert check_object_scale(objs) == []


def test_scale_tolerance_around_one():
    """Tiny float drift (1.0001) shouldn't trigger non-uniform false
    positive."""
    objs = [dict(name='drift', scale=(1.0001, 1.0, 0.9999))]
    assert check_object_scale(objs) == []


# ── Light Beam ASI (I) ──────────────────────────────────────────────


def test_light_beam_with_plugin_present_clean():
    meshes = [dict(name='ray', light_beam_asi=True)]
    assert check_light_beam_asi(meshes, sa_light_asi_present=True) == []


def test_light_beam_without_plugin_reports_info():
    meshes = [dict(name='ray', light_beam_asi=True)]
    issues = check_light_beam_asi(meshes, sa_light_asi_present=False)
    assert len(issues) == 1
    assert issues[0]['severity'] == 'INFO'
    assert issues[0]['category'] == 'LightBeamASI'


def test_light_beam_flag_off_clean_even_without_plugin():
    meshes = [dict(name='regular', light_beam_asi=False)]
    assert check_light_beam_asi(meshes, sa_light_asi_present=False) == []


# ── Issue dict shape ────────────────────────────────────────────────


def test_all_issues_have_required_fields():
    """Issue dicts must carry the full schema even when fields are
    empty — the bpy CollectionProperty mirrors them as StringProperty
    and keys with default '' are fine, but a missing key would
    KeyError when copying into the PropertyGroup."""
    REQUIRED = {'severity', 'category', 'message',
                'message_template', 'message_args',
                'target_kind', 'target_name', 'fix_op_id', 'fix_arg'}

    samples = []
    samples += check_paintjobs([
        dict(name='m1', alt1=True, alt2=False, has_base=True),
        dict(name='m2', alt1=False, alt2=True, has_base=True),
        dict(name='m3', alt1=True, alt2=True, has_base=False),
    ])
    samples += check_quaternions([dict(name='a',
                                       quat_groups=[[2.0, 0.0, 0.0, 0.0]])])
    samples += check_uv_anim_night_vcols([
        dict(name='o', has_uv_anim=True, night_flag=True, has_night_vcol=False)])
    samples += check_damage_pairs(['x_ok', 'y_dam'])
    samples += check_orphan_models([
        dict(name='lone_LOD', type='LOD', base='lone'),
        dict(name='lone_COL', type='COL', base='lone'),
    ])
    samples += check_orphan_2dfx([dict(name='fx_x', parent_kind=None)])
    samples += check_duplicate_model_ids([
        dict(name='a', model_id=1), dict(name='b', model_id=1)])
    samples += check_empty_meshes([dict(name='ghost', vert_count=0)])
    samples += check_large_meshes([dict(name='huge', vert_count=99999)])
    samples += check_materials_without_texture([
        dict(name='m', has_base=False, used_on_mesh=True)])
    samples += check_suffix_consistency(['body.DFF'], _DEFAULT_SFX)
    samples += check_object_scale([dict(name='m', scale=(-1.0, 1.0, 1.0))])
    samples += check_light_beam_asi(
        [dict(name='ray', light_beam_asi=True)], sa_light_asi_present=False)

    assert samples, "fixtures should produce at least one issue per check"
    for issue in samples:
        assert set(issue.keys()) == REQUIRED, (
            f"issue missing fields: {REQUIRED - set(issue.keys())}")
        assert issue['severity'] in ('ERROR', 'WARNING', 'INFO')
