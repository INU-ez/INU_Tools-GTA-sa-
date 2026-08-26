"""Scene-generation counter for panel ``draw()`` memoisation.

Several panels answer questions that need a walk over the whole blend
file — «does another object claim this model ID?», «how many ZON zones
are in the scene?», «how many IFP actions are loaded?». ``draw()`` runs
on EVERY redraw of the region, and the N-sidebar is redrawn along with
the viewport, so those walks used to run per frame and made viewport
navigation stutter on a big map scene.

The fix is to memoise anything derived from scene contents against
:func:`generation`, a counter bumped from ``depsgraph_update_post``.

Pure transforms don't bump it. Dragging an object fires a depsgraph
update every frame, but moving a mesh cannot change its model type, its
ID conflicts or the zone count — so a transform-only update batch is
skipped and the memo survives the whole drag. Anything else (rename,
retag, material edit, add/remove) bumps the counter and every memo
rebuilds on the next draw.

Data that lives OUTSIDE the depsgraph (``bpy.data.actions`` is the
notable one — an unassigned action isn't evaluated) can't rely on the
counter alone. Fold a cheap discriminator such as ``len(bpy.data.
actions)`` into the memo key for those; that's one C-level call versus
the scan it guards.
"""

_generation = 0

# key → (generation, value). Bounded — see _MAX_ENTRIES.
_store = {}

# Keys are per-panel and usually per-object-name, so the table stays
# small in practice. The cap is a safety net against a pathological
# scene (thousands of objects cycled through the active slot) turning
# the memo into a leak.
_MAX_ENTRIES = 512


def generation() -> int:
    """Current scene generation. Changes when scene CONTENT changes."""
    return _generation


# Datablocks Blender tags on nearly every update as bookkeeping. They
# say only «something in this scene changed», never WHAT, so they can't
# decide anything either way and are skipped when reading a batch.
# Without this the predicate below would answer False for every real
# depsgraph batch, because a Scene entry rides along with all of them.
_BOOKKEEPING_IDS = frozenset(('Scene', 'ViewLayer'))


def is_transform_only(depsgraph) -> bool:
    """True when this batch is nothing but objects being moved.

    Blender's own flags: ``is_updated_transform`` without
    ``is_updated_geometry`` / ``is_updated_shading`` means the object
    moved and nothing else about it changed.

    Everything ambiguous answers False — an empty batch, a depsgraph we
    can't read, or an updated datablock that isn't an Object (a Mesh,
    Material or Collection edit reaches us that way). Bumping needlessly
    only costs one rebuild; skipping needlessly shows the user a stale
    number, so the bias goes one way only.
    """
    if depsgraph is None:
        return False
    try:
        updates = depsgraph.updates
    except AttributeError:
        return False
    saw_object = False
    for upd in updates:
        target = getattr(upd, 'id', None)
        kind = type(target).__name__ if target is not None else ''
        if kind in _BOOKKEEPING_IDS:
            continue
        if kind != 'Object':
            return False
        if (not getattr(upd, 'is_updated_transform', False)
                or getattr(upd, 'is_updated_geometry', False)
                or getattr(upd, 'is_updated_shading', False)):
            return False
        saw_object = True
    return saw_object


def bump(_scene=None, depsgraph=None) -> None:
    """Invalidate every memo (``depsgraph_update_post`` handler).

    Registered persistent in ``INU_tools.register`` — see the note on
    ``invalidate_model_type_cache`` for why the decorator isn't applied
    at module level.
    """
    global _generation
    if is_transform_only(depsgraph):
        return
    _generation += 1
    _store.clear()


def memo(key, build):
    """Return ``build()``, memoised until the scene generation moves.

    ``key`` must be hashable and identify the question being asked —
    include any cheap input the answer depends on (active object name,
    a ``len()`` guard for non-depsgraph data), since only the generation
    is checked for you.
    """
    gen = _generation
    hit = _store.get(key)
    if hit is not None and hit[0] == gen:
        return hit[1]
    value = build()
    if len(_store) >= _MAX_ENTRIES:
        _store.clear()
    _store[key] = (gen, value)
    return value


def clear() -> None:
    """Drop every memo without touching the generation (tests, unregister)."""
    _store.clear()
