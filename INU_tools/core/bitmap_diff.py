"""Pure-logic helpers for the Bitmaps Manager unused-cleanup feature.

Lives in ``core`` so it stays bpy-free and is testable outside Blender.
The actual operators in ``tools/bitmaps_manager.py`` are thin wrappers
that pass ``bpy.data.objects`` / ``bpy.data.images`` / ``bpy.data.materials``
into these functions.
"""

from __future__ import annotations


# Blender creates these images internally (viewer node, render result,
# compositor previews) and they always look "unused" by the material
# graph. Excluded by name from cleanup so a "Remove Unused" click never
# touches them — they don't actually live in `bpy.data.images.remove()`
# anyway, but excluding upfront keeps the report counters honest.
_INTERNAL_IMAGE_NAME_PREFIXES = ('Render Result', 'Viewer Node')


def is_internal_image(img) -> bool:
    """True if *img* is a Blender-internal datablock (viewer/render result)."""
    if getattr(img, 'source', '') == 'VIEWER':
        return True
    name = getattr(img, 'name', '') or ''
    return any(name.startswith(p) for p in _INTERNAL_IMAGE_NAME_PREFIXES)


def collect_used(objects):
    """Walk an iterable of objects and return ``(used_images, used_materials)``.

    A material is "used" iff at least one MESH object's ``data.materials``
    slot points at it. An image is "used" iff at least one *used* material
    has a TEX_IMAGE node referencing it.

    Inputs are duck-typed: each object needs ``.type``, ``.data.materials``;
    each material ``.use_nodes`` and ``.node_tree.nodes`` (with each node
    having ``.type`` and ``.image``). This matches the bpy API surface
    without requiring Blender to be importable.
    """
    used_materials: set = set()
    for obj in objects:
        if getattr(obj, 'type', None) != 'MESH':
            continue
        data = getattr(obj, 'data', None)
        if data is None:
            continue
        for slot in getattr(data, 'materials', ()) or ():
            if slot is not None:
                used_materials.add(slot)

    used_images: set = set()
    for mat in used_materials:
        if not getattr(mat, 'use_nodes', False):
            continue
        node_tree = getattr(mat, 'node_tree', None)
        if not node_tree:
            continue
        for node in getattr(node_tree, 'nodes', ()) or ():
            if getattr(node, 'type', None) == 'TEX_IMAGE' \
                    and getattr(node, 'image', None) is not None:
                used_images.add(node.image)

    return used_images, used_materials


def diff_unused_images(all_images, used_images, *,
                       respect_fake_user: bool = True,
                       internal_predicate=is_internal_image):
    """Return items in *all_images* not in *used_images*, excluding
    Blender-internal images and (optionally) ``use_fake_user``-flagged ones.
    """
    out = []
    for img in all_images:
        if img in used_images:
            continue
        if internal_predicate is not None and internal_predicate(img):
            continue
        if respect_fake_user and getattr(img, 'use_fake_user', False):
            continue
        out.append(img)
    return out


def diff_unused_materials(all_materials, used_materials, *,
                          respect_fake_user: bool = True):
    """Return items in *all_materials* not in *used_materials*, excluding
    (optionally) ``use_fake_user``-flagged ones.

    No internal-name filter — Blender doesn't generate materials
    internally the way it does Render Result / Viewer Node.
    """
    out = []
    for mat in all_materials:
        if mat in used_materials:
            continue
        if respect_fake_user and getattr(mat, 'use_fake_user', False):
            continue
        out.append(mat)
    return out
