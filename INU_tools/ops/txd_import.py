# INU_tools.ops.txd_import
# TXD texture dictionary → Blender images + material assignment.

import time
import numpy as np
import bpy
from bpy.props import StringProperty

from ..core.txd import read_txd_file, read_txd


def _textures_to_blender_images(textures):
    """Convert a list of TxdTexture objects into bpy.data.images.

    Reuses existing image datablocks by name — never creates ``name.001``
    suffixes. When an existing image has a different size, we resize
    in-place via ``Image.scale`` rather than ``remove + new``, because
    ``use_fake_user = True`` makes ``bpy.data.images.remove(img)`` a
    no-op and the immediate ``new(name, ...)`` then auto-suffixes the
    new image — that's the root cause of the user's 6× duplicate
    ``vehiclelights128.001/.002/...`` accumulation across re-imports.
    """
    images = []
    for tex in textures:
        name = tex.name.rstrip('\x00')
        if not name:
            continue

        w, h = tex.width, tex.height
        if w == 0 or h == 0 or not tex.pixels:
            continue

        # Pixel buffer must be exactly h*w*4 bytes (RGBA8888). The TXD
        # decoder occasionally returns a half-sized buffer when it falls
        # into the wrong format branch (e.g. raster flagged 8888 but
        # data is 16-bit RGB565). Skip with an explicit message rather
        # than reshape-crashing — the rest of the textures still load,
        # and the user can see exactly which one needs investigating.
        expected_bytes = h * w * 4
        actual_bytes = len(tex.pixels)
        if actual_bytes != expected_bytes:
            print(f"[INU_tools TXD] Skip {name!r} ({w}x{h}): "
                  f"decoder returned {actual_bytes} bytes, "
                  f"expected {expected_bytes} (raster_format=0x"
                  f"{getattr(tex, 'raster_format', 0):X}, "
                  f"depth={getattr(tex, 'depth', 0)})")
            continue

        img = bpy.data.images.get(name)
        if img is not None:
            # Reuse existing — resize in-place if dimensions changed.
            # scale() preserves the same datablock + its users (mats
            # already pointing at it), so we don't lose bindings.
            if img.size[0] != w or img.size[1] != h:
                img.scale(w, h)
        else:
            img = bpy.data.images.new(name, w, h, alpha=True)

        arr = np.frombuffer(tex.pixels, dtype=np.uint8).reshape(h, w, 4)
        flipped = arr[::-1].astype(np.float32) / 255.0
        img.pixels.foreach_set(flipped.ravel())
        img.pack()
        img.use_fake_user = True  # keep around even when no shader uses it yet
        img.update()
        images.append(img)
        print(f"[INU_tools TXD] Loaded: {name} ({w}x{h})")
    return images


def import_txd_bytes(data: bytes, assign_to_materials: bool = False,
                     name_filter=None):
    """Import a TXD from in-memory bytes (e.g. extracted from an IMG archive).

    ``name_filter`` (set of lowercase names): when supplied, only
    textures whose name is in the set are decoded. Skips DXT decoding
    for everything else — major speedup on big TXDs (vehicle.txd has
    ~150 textures; a single DFF rarely uses more than ~10)."""
    t0 = time.perf_counter()
    textures = read_txd(data)
    if name_filter is not None:
        textures = [t for t in textures
                    if t.name.lower() in name_filter]
    t_decode = time.perf_counter() - t0

    t0 = time.perf_counter()
    images = _textures_to_blender_images(textures)
    t_upload = time.perf_counter() - t0

    t_assign = 0.0
    if assign_to_materials:
        t0 = time.perf_counter()
        _assign_textures_to_materials(images)
        t_assign = time.perf_counter() - t0

    print(f"[TXD IMPORT] {len(images)} textures: decode={t_decode:.3f}s "
          f"upload={t_upload:.3f}s assign={t_assign:.3f}s "
          f"total={t_decode+t_upload+t_assign:.3f}s")
    return images


def import_txd(filepath: str, assign_to_materials: bool = True,
               name_filter=None):
    """
    Import a TXD file into Blender.

    Creates Blender images from each texture in the TXD.
    If assign_to_materials is True, auto-assigns images to materials
    whose names match the texture names.

    ``name_filter`` (set of lowercase names): when supplied, only those
    textures are decoded — used by DFF-import auto-TXD path so loading
    vehicle.txd for a single car door doesn't drag in 150 unrelated
    textures and freeze Blender.
    """
    import os
    fname = os.path.basename(filepath)
    print(f"[TXD IMPORT] === START {fname} (assign={assign_to_materials}) ===")
    # Mobile TXD container detection — short-circuit with a helpful
    # message before we try to parse PVRTC/ETC1 bytes as RW chunks.
    # Pixel decode would need a C-extension codec we don't ship.
    try:
        from ..core.txd_mobile import detect_mobile_txd, container_summary
        _mobile = detect_mobile_txd(filepath)
        if _mobile is not None:
            from ..core.txd_mobile import MobileTxdPixelDecodeUnsupported
            print(f"[TXD IMPORT] {container_summary(_mobile)}")
            raise MobileTxdPixelDecodeUnsupported(_mobile)
    except ImportError:
        pass
    t0 = time.perf_counter()
    textures = read_txd_file(filepath)
    if name_filter is not None:
        before = len(textures)
        textures = [t for t in textures
                    if t.name.lower() in name_filter]
        print(f"[TXD IMPORT] name_filter applied: {before} → {len(textures)} textures")
    t_decode = time.perf_counter() - t0

    print(f"[TXD IMPORT] decoded textures (name | size | fourcc):")
    for t in textures:
        nm = t.name.rstrip('\x00')
        fc = getattr(t, 'fourcc', 0)
        fc_str = ''.join(chr((fc >> (i*8)) & 0xFF) for i in range(4)).strip('\x00') or f'0x{fc:08X}'
        print(f"  • {nm!r:<32} {t.width:>4}x{t.height:<4} {fc_str}")

    t0 = time.perf_counter()
    images = _textures_to_blender_images(textures)
    t_upload = time.perf_counter() - t0

    print(f"[TXD IMPORT] uploaded {len(images)} images to bpy.data.images. "
          f"Materials in scene: {len(bpy.data.materials)}, "
          f"Objects: {len(bpy.data.objects)}")
    if bpy.data.materials:
        print(f"[TXD IMPORT] material list (name | dff_texture_name | use_nodes | library):")
        for m in bpy.data.materials:
            idprop = m.get('dff_texture_name', '<none>')
            lib = m.library.filepath if m.library else '<local>'
            print(f"  • {m.name!r:<32} dff_texture_name={idprop!r:<20} "
                  f"use_nodes={m.use_nodes} library={lib}")

    # Object dump — shows which objects have material slots and what's
    # in them. If `bpy.data.materials` is short of expectations, this
    # reveals whether the scene uses empty slots, shared materials, or
    # linked references that are stored elsewhere.
    mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
    print(f"[TXD IMPORT] mesh objects: {len(mesh_objs)} (showing first 30)")
    for o in mesh_objs[:30]:
        slot_info = []
        for i, s in enumerate(o.material_slots):
            if s.material:
                idp = s.material.get('dff_texture_name', '')
                slot_info.append(f"#{i}={s.material.name!r}"
                                 + (f"[idprop={idp!r}]" if idp else ''))
            else:
                slot_info.append(f"#{i}=<empty>")
        slots_str = ', '.join(slot_info) if slot_info else '<no slots>'
        print(f"  • obj={o.name!r:<28} slots: {slots_str}")
    if len(mesh_objs) > 30:
        print(f"  … and {len(mesh_objs) - 30} more")

    t_assign = 0.0
    if assign_to_materials:
        t0 = time.perf_counter()
        _assign_textures_to_materials(images)
        t_assign = time.perf_counter() - t0

    print(f"[TXD IMPORT] === DONE {fname}: {len(images)} textures, "
          f"decode={t_decode:.3f}s upload={t_upload:.3f}s "
          f"assign={t_assign:.3f}s total={t_decode+t_upload+t_assign:.3f}s ===")
    return images


# Single source of truth for alpha detection + linking lives in
# texture_ops.py. We call link_material_alpha_if_textured() here too,
# instead of duplicating the logic — that way blend_method, shadow_method
# and the actual Alpha link stay in sync regardless of which import path
# (TXD direct, DFF auto-TXD, IMG, etc.) reached the material.
from .texture_ops import image_has_significant_alpha, link_material_alpha_if_textured


def _assign_textures_to_materials(images):
    """Assign imported images to materials and re-evaluate alpha links.

    Two-phase pipeline, both with verbose console diagnostics:

      Phase 1 — name match:
        For each material, look up an image by ``mat['dff_texture_name']``
        IDProp, fallback to lowercased material name. If matched, ensure
        a Principled BSDF + Image Texture node exists, wire Base Color,
        and re-evaluate the Alpha link via ``image_has_significant_alpha``.

      Phase 2 — fallback alpha pass:
        For ALL materials in the scene (including those we couldn't match
        by name), call ``link_material_alpha_if_textured`` so any material
        that already had a TEX_IMAGE node from elsewhere (DFF import,
        manual user wiring) also gets its alpha re-evaluated. Catches the
        case where DFF was imported with an old addon that didn't set
        ``dff_texture_name``, or material names diverged from texture
        names (Blender ``.001`` suffix, manual rename, etc.).

    Every step prints a diagnostic line so failures are visible: which
    material matched how, which image was found, what alpha decision
    was made, and final summary counts.
    """
    image_map = {img.name.lower(): img for img in images}

    n_total = len(bpy.data.materials)
    n_matched_idprop = 0
    n_matched_name = 0
    n_no_match = 0
    n_no_bsdf = 0
    n_alpha_linked = 0
    n_alpha_unlinked = 0

    print(f"[TXD ASSIGN] Phase 1 — name matching: {n_total} materials, {len(images)} images available")

    for mat in bpy.data.materials:
        dff_tex = mat.get('dff_texture_name')
        match_kind = None
        if dff_tex:
            img = image_map.get(dff_tex.lower())
            if img is not None:
                n_matched_idprop += 1
                match_kind = f"IDProp dff_texture_name={dff_tex!r}"
        else:
            img = image_map.get(mat.name.lower())
            if img is not None:
                n_matched_name += 1
                match_kind = f"name={mat.name!r}"

        if img is None:
            n_no_match += 1
            continue

        print(f"[TXD ASSIGN] mat={mat.name!r} matched via {match_kind} → image={img.name!r}")

        if not mat.use_nodes:
            mat.use_nodes = True

        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links

        bsdf = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bsdf = node
                break
        if bsdf is None:
            n_no_bsdf += 1
            print(f"[TXD ASSIGN] mat={mat.name!r}: no Principled BSDF → skipping alpha wire")
            continue

        bc_input = bsdf.inputs.get('Base Color')
        tex_node = None
        if bc_input and bc_input.links:
            from_node = bc_input.links[0].from_node
            if from_node.type == 'TEX_IMAGE':
                tex_node = from_node
                tex_node.image = img
                print(f"[TXD ASSIGN] mat={mat.name!r}: reusing existing TEX_IMAGE node, image set to {img.name!r}")

        if tex_node is None:
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.image = img
            tex_node.location = (bsdf.location.x - 300, bsdf.location.y)
            links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
            print(f"[TXD ASSIGN] mat={mat.name!r}: created new TEX_IMAGE node + Base Color link")

        # Single unified call — checks pixels, links/unlinks Alpha,
        # AND sets material.blend_method correctly. No duplicated logic
        # between Phase 1 and Phase 2 anymore.
        was_linked_before = bool(bsdf.inputs.get('Alpha') and bsdf.inputs['Alpha'].is_linked)
        if link_material_alpha_if_textured(mat):
            is_linked_after = bool(bsdf.inputs.get('Alpha') and bsdf.inputs['Alpha'].is_linked)
            if is_linked_after and not was_linked_before:
                n_alpha_linked += 1
            elif not is_linked_after and was_linked_before:
                n_alpha_unlinked += 1

    print(f"[TXD ASSIGN] Phase 1 done: matched_idprop={n_matched_idprop} "
          f"matched_name={n_matched_name} no_match={n_no_match} no_bsdf={n_no_bsdf} "
          f"alpha_linked={n_alpha_linked} alpha_unlinked={n_alpha_unlinked}")

    # ── Phase 2: blanket alpha pass over ALL reachable materials ──
    # Collects materials from both bpy.data.materials and from every
    # mesh object's material_slots — covers the case where slots
    # reference materials missing from the global list (rare but
    # happens with linked / partially-loaded scenes).
    # NB: link_material_alpha_if_textured is already imported at module
    # level above. A second `from .texture_ops import …` here would make
    # the name a function-local — and Phase 1's earlier reference would
    # then raise UnboundLocalError before this import statement runs.
    seen = set()
    all_mats = []
    for mat in bpy.data.materials:
        if mat.name not in seen:
            seen.add(mat.name)
            all_mats.append(mat)
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            if slot.material and slot.material.name not in seen:
                seen.add(slot.material.name)
                all_mats.append(slot.material)

    n_phase2_changed = 0
    for mat in all_mats:
        if link_material_alpha_if_textured(mat):
            n_phase2_changed += 1
    print(f"[TXD ASSIGN] Phase 2 done: visited={len(all_mats)} (incl. slot-only materials) "
          f"alpha_changed={n_phase2_changed}")


# ──────────────────── Blender operator wrapper ────────────────────────

class GTATOOLS_OT_import_txd(bpy.types.Operator):
    """Импорт TXD текстур GTA SA"""
    bl_idname = "gtatools.import_txd"
    bl_label = "INU: Import TXD (.txd)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    import_game: bpy.props.EnumProperty(
        name="Игра",
        description="Из какой игры импортируем TXD. Auto — по RW-версии в chunk header",
        items=[
            ('AUTO', "Авто-определение", ""),
            ('III',  "GTA III", ""),
            ('VC',   "Vice City", ""),
            ('SA',   "San Andreas", ""),
        ],
        default='AUTO')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        self.layout.prop(self, "import_game")

    def execute(self, context):
        try:
            images = import_txd(filepath=self.filepath)
            from ..core import game_versions as gv
            if self.import_game == 'AUTO':
                detected = gv.detect_game_from_txd(self.filepath)
            else:
                detected = self.import_game
            switched = gv.maybe_set_game_from_import(context.scene, detected)
            tag = f" → game={detected}" if switched else ""
            self.report({'INFO'}, f"Imported TXD: {len(images)} textures{tag}")
            if not switched:
                warn = gv.check_game_mismatch_warning(context.scene, detected)
                if warn:
                    self.report({'WARNING'}, warn)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"TXD import error: {str(e)}")
            return {'CANCELLED'}


classes = (
    GTATOOLS_OT_import_txd,
)
