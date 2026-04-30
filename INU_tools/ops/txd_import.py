# INU_tools.ops.txd_import
# TXD texture dictionary → Blender images + material assignment.

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
    textures = read_txd(data)
    if name_filter is not None:
        textures = [t for t in textures
                    if t.name.lower() in name_filter]
    images = _textures_to_blender_images(textures)
    if assign_to_materials:
        _assign_textures_to_materials(images)
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
    textures = read_txd_file(filepath)
    if name_filter is not None:
        textures = [t for t in textures
                    if t.name.lower() in name_filter]
    images = _textures_to_blender_images(textures)
    if assign_to_materials:
        _assign_textures_to_materials(images)
    return images


def _assign_textures_to_materials(images):
    """Assign imported images to materials whose names match texture names.

    Матчинг идёт в таком порядке:
    1. IDProp `dff_texture_name` на материале (выставляется при импорте DFF) —
       самый надёжный способ, не ломается при Blender-suffix'ах `.001` и т.п.
    2. Имя материала в нижнем регистре (fallback для старых/ручных сцен).
    """
    image_map = {img.name.lower(): img for img in images}

    for mat in bpy.data.materials:
        dff_tex = mat.get('dff_texture_name')
        if dff_tex:
            img = image_map.get(dff_tex.lower())
        else:
            img = image_map.get(mat.name.lower())

        if img is None:
            continue

        if not mat.use_nodes:
            mat.use_nodes = True

        tree = mat.node_tree
        nodes = tree.nodes
        links = tree.links

        # Find Principled BSDF
        bsdf = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bsdf = node
                break
        if bsdf is None:
            continue

        # Check if there's already an image texture connected
        bc_input = bsdf.inputs.get('Base Color')
        if bc_input and bc_input.links:
            tex_node = bc_input.links[0].from_node
            if tex_node.type == 'TEX_IMAGE':
                tex_node.image = img
                continue

        # Create Image Texture node
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = img
        tex_node.location = (bsdf.location.x - 300, bsdf.location.y)

        links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

        if img.channels == 4:
            links.new(tex_node.outputs['Alpha'], bsdf.inputs['Alpha'])


# ──────────────────── Blender operator wrapper ────────────────────────

class GTATOOLS_OT_import_txd(bpy.types.Operator):
    """Импорт TXD текстур GTA SA"""
    bl_idname = "gtatools.import_txd"
    bl_label = "INU: Import TXD (.txd)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.txd", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        try:
            images = import_txd(filepath=self.filepath)
            self.report({'INFO'}, f"Imported TXD: {len(images)} textures")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"TXD import error: {str(e)}")
            return {'CANCELLED'}


classes = (
    GTATOOLS_OT_import_txd,
)
