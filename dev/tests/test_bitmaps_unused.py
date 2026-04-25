"""Tests for the Bitmaps Manager unused-cleanup logic.

The actual operators in ``tools.bitmaps_manager`` need bpy at import
time. The interesting logic — which datablocks count as "used" given
the scene graph — lives in ``core.bitmap_diff`` as pure helpers, so
we can exercise it with duck-typed mock objects.
"""

from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.bitmap_diff import (  # noqa: E402
    is_internal_image,
    collect_used,
    diff_unused_images,
    diff_unused_materials,
)


class _NS(types.SimpleNamespace):
    """SimpleNamespace + identity hash.

    Plain ``types.SimpleNamespace`` defines ``__eq__`` without explicit
    ``__hash__`` — on Python 3.13+ that makes instances unhashable, so
    they can't go into ``set()`` (which is exactly what ``collect_used``
    uses to dedupe used materials/images). Real Blender datablocks
    have identity hash; mirror that in the mocks via this subclass.
    """
    __hash__ = object.__hash__


# ─────────────────────── mock builders (duck typing) ───────────────────

def _img(name="img", *, source="FILE", use_fake_user=False):
    return _NS(name=name, source=source, use_fake_user=use_fake_user)


def _node(image, kind='TEX_IMAGE'):
    return _NS(type=kind, image=image)


def _material(name="mat", *, image_nodes=None, use_nodes=True,
              use_fake_user=False):
    nodes = [_node(img) for img in (image_nodes or [])]
    node_tree = _NS(nodes=nodes) if use_nodes else None
    return _NS(
        name=name, use_nodes=use_nodes, node_tree=node_tree,
        use_fake_user=use_fake_user)


def _mesh_obj(name, materials):
    return _NS(
        name=name, type='MESH',
        data=_NS(materials=list(materials)))


def _empty_obj(name="E"):
    return _NS(name=name, type='EMPTY', data=None)


# ─────────────────────────── is_internal_image ───────────────────────────

def test_is_internal_image_flags_render_result():
    assert is_internal_image(_img("Render Result"))


def test_is_internal_image_flags_viewer_node():
    assert is_internal_image(_img("Viewer Node"))


def test_is_internal_image_flags_viewer_source_regardless_of_name():
    assert is_internal_image(_img("anything", source="VIEWER"))


def test_is_internal_image_passes_normal_textures():
    assert not is_internal_image(_img("brick.dds"))
    assert not is_internal_image(_img("ground.png", source="FILE"))


# ─────────────────────────── collect_used ─────────────────────────────────

def test_collect_used_picks_up_images_only_via_used_materials():
    """Material in bpy.data.materials but not on any mesh slot must NOT
    keep its TEX_IMAGE alive — orphaned-material textures are unused."""
    detached_img = _img("detached.dds")
    used_img = _img("used.dds")

    detached_mat = _material("detached_mat", image_nodes=[detached_img])
    used_mat = _material("used_mat", image_nodes=[used_img])

    mesh = _mesh_obj("Cube", [used_mat])

    used_images, used_materials = collect_used([mesh])

    assert used_materials == {used_mat}
    assert detached_mat not in used_materials
    assert used_img in used_images
    assert detached_img not in used_images


def test_collect_used_skips_non_mesh_objects():
    img = _img("x.dds")
    mat = _material("M", image_nodes=[img])
    armature = _NS(
        type='ARMATURE',
        data=_NS(materials=[mat]))

    used_images, used_materials = collect_used([armature])

    # Materials on non-MESH objects do not count as used.
    assert used_materials == set()
    assert used_images == set()


def test_collect_used_handles_empty_data():
    obj = _empty_obj()
    used_images, used_materials = collect_used([obj])
    assert used_images == set()
    assert used_materials == set()


def test_collect_used_handles_none_slot():
    """A mesh with an empty material slot (None) must not crash."""
    img = _img("x.dds")
    mat = _material("M", image_nodes=[img])
    mesh = _mesh_obj("Cube", [None, mat, None])

    used_images, used_materials = collect_used([mesh])
    assert used_materials == {mat}
    assert used_images == {img}


def test_collect_used_skips_material_without_nodes():
    """A material with use_nodes=False has no TEX_IMAGE graph — its
    legacy texture slots aren't followed. Material is still "used" if
    a mesh references it; it just contributes no images."""
    mat = _material("classic", image_nodes=[], use_nodes=False)
    mesh = _mesh_obj("Cube", [mat])

    used_images, used_materials = collect_used([mesh])
    assert used_materials == {mat}
    assert used_images == set()


def test_collect_used_ignores_non_tex_image_nodes():
    img = _img("x.dds")
    mat = _NS(
        name="m", use_nodes=True, use_fake_user=False,
        node_tree=_NS(nodes=[
            _node(img, kind='OUTPUT_MATERIAL'),
            _node(None, kind='TEX_IMAGE'),  # node exists but no image
        ]),
    )
    mesh = _mesh_obj("Cube", [mat])
    used_images, _ = collect_used([mesh])
    assert used_images == set()


# ─────────────────────────── diff_unused_images ──────────────────────────

def test_diff_unused_images_flags_orphans():
    used = _img("used.dds")
    orphan = _img("orphan.dds")
    out = diff_unused_images([used, orphan], {used})
    assert out == [orphan]


def test_diff_unused_images_skips_internal_by_default():
    used = _img("used.dds")
    rr = _img("Render Result")
    vn = _img("Viewer Node")
    out = diff_unused_images([used, rr, vn], {used})
    # RR and VN are NOT in used_images, but the internal predicate filters them.
    assert out == []


def test_diff_unused_images_respects_fake_user_by_default():
    keep = _img("custom.dds", use_fake_user=True)
    drop = _img("real_orphan.dds")
    out = diff_unused_images([keep, drop], set())
    assert out == [drop]


def test_diff_unused_images_can_ignore_fake_user_flag():
    keep = _img("custom.dds", use_fake_user=True)
    out = diff_unused_images([keep], set(), respect_fake_user=False)
    assert out == [keep]


def test_diff_unused_images_internal_predicate_can_be_disabled():
    rr = _img("Render Result")
    out = diff_unused_images([rr], set(), internal_predicate=None)
    assert out == [rr]


# ─────────────────────────── diff_unused_materials ───────────────────────

def test_diff_unused_materials_flags_orphans():
    used = _material("used")
    orphan = _material("orphan")
    out = diff_unused_materials([used, orphan], {used})
    assert out == [orphan]


def test_diff_unused_materials_respects_fake_user():
    keep = _material("keep", use_fake_user=True)
    drop = _material("drop")
    out = diff_unused_materials([keep, drop], set())
    assert out == [drop]


def test_diff_unused_materials_can_ignore_fake_user():
    keep = _material("keep", use_fake_user=True)
    out = diff_unused_materials([keep], set(), respect_fake_user=False)
    assert out == [keep]


# ─────────────────────────── end-to-end pipeline ─────────────────────────

def test_full_pipeline_orphan_material_keeps_its_image_unused():
    """The integration scenario: import a TXD, never apply it to a mesh,
    then run cleanup — both the orphan material and its image should
    show up as unused."""
    img_used = _img("brick.dds")
    img_orphan = _img("imported_but_never_used.dds")

    mat_used = _material("BrickMat", image_nodes=[img_used])
    mat_orphan = _material("OrphanMat", image_nodes=[img_orphan])

    mesh = _mesh_obj("Wall", [mat_used])

    all_images = [img_used, img_orphan]
    all_materials = [mat_used, mat_orphan]

    used_images, used_materials = collect_used([mesh])
    unused_imgs = diff_unused_images(all_images, used_images)
    unused_mats = diff_unused_materials(all_materials, used_materials)

    assert unused_imgs == [img_orphan]
    assert unused_mats == [mat_orphan]
