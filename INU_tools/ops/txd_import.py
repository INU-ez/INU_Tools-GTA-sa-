# INU_tools.ops.txd_import
# TXD texture dictionary → Blender images + material assignment.

import numpy as np
import bpy

from ..core.txd import read_txd_file, read_txd


def _textures_to_blender_images(textures):
    """Convert a list of TxdTexture objects into bpy.data.images.

    Creates or replaces images in-place. Returns the list of Blender images.
    """
    images = []
    for tex in textures:
        name = tex.name.rstrip('\x00')
        if not name:
            continue

        w, h = tex.width, tex.height
        if w == 0 or h == 0 or not tex.pixels:
            continue

        if name in bpy.data.images:
            img = bpy.data.images[name]
            if img.size[0] != w or img.size[1] != h:
                bpy.data.images.remove(img)
                img = bpy.data.images.new(name, w, h, alpha=True)
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


def import_txd_bytes(data: bytes, assign_to_materials: bool = False):
    """Import a TXD from in-memory bytes (e.g. extracted from an IMG archive)."""
    textures = read_txd(data)
    images = _textures_to_blender_images(textures)
    if assign_to_materials:
        _assign_textures_to_materials(images)
    return images


def import_txd(filepath: str, assign_to_materials: bool = True):
    """
    Import a TXD file into Blender.

    Creates Blender images from each texture in the TXD.
    If assign_to_materials is True, auto-assigns images to materials
    whose names match the texture names.
    """
    textures = read_txd_file(filepath)
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
