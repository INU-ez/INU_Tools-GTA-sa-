# INU_tools.ops.fx_preview
# Visual preview for 2DFX effects in Blender viewport.
# Creates child objects (light + billboard) for Light2dfx empties.

import os
import bpy
import math
import random
import time


def _get_fx_textures_dir() -> str:
    """Return path to data/fx_textures/ inside the addon."""
    addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(addon_dir, "data", "fx_textures")


def _load_fx_image(tex_name: str):
    """Load a corona/shadow texture from fx_textures folder."""
    if not tex_name:
        return None

    if tex_name in bpy.data.images:
        return bpy.data.images[tex_name]

    tex_dir = _get_fx_textures_dir()
    filepath = os.path.join(tex_dir, tex_name + ".png")
    if not os.path.isfile(filepath):
        filepath = os.path.join(tex_dir, tex_name)
        if not os.path.isfile(filepath):
            return None

    img = bpy.data.images.load(filepath)
    img.name = tex_name
    return img


def _create_plane_mesh(name: str, size: float = 1.0) -> bpy.types.Mesh:
    """Create a simple quad mesh without bpy.ops."""
    import bmesh
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    s = size / 2.0
    v1 = bm.verts.new((-s, -s, 0))
    v2 = bm.verts.new(( s, -s, 0))
    v3 = bm.verts.new(( s,  s, 0))
    v4 = bm.verts.new((-s,  s, 0))
    bm.faces.new((v1, v2, v3, v4))

    # UV layer
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co
            loop[uv_layer].uv = ((co.x / size) + 0.5, (co.y / size) + 0.5)

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh


def _lock_child(obj, lock_rotation=True):
    """Make child object non-selectable and non-exportable."""
    # Non-exportable
    if hasattr(obj, 'inu'):
        obj.inu.type = 'NON'

    # Non-selectable in viewport
    obj.hide_select = True

    # Lock transforms
    obj.lock_location = (True, True, True)
    obj.lock_rotation = (lock_rotation, lock_rotation, lock_rotation)
    obj.lock_scale = (True, True, True)


def _create_corona_material(tex_name: str, color_rgb, edge_power=2.0, emission_strength=0.7) -> bpy.types.Material:
    """Create corona material: Transparent + Emission mixed by texture brightness.

    Black pixels = fully transparent, white pixels = glowing with effect color.
    color_rgb: tuple of (r, g, b) floats in 0.0-1.0 range.
    """
    r, g, b = color_rgb[0], color_rgb[1], color_rgb[2]

    mat_name = f"2dfx_corona_{tex_name}"

    # Always recreate material to apply debug tuning params
    if mat_name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[mat_name])

    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    if hasattr(mat, 'blend_method'):
        mat.blend_method = 'BLEND'
    mat.use_backface_culling = False
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    # Transparent BSDF (for black parts)
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (200, 100)

    # Emission shader (for bright parts, colored)
    emission = nodes.new('ShaderNodeEmission')
    emission.location = (200, -100)
    emission.inputs['Color'].default_value = (r, g, b, 1.0)
    emission.inputs['Strength'].default_value = emission_strength

    # Mix Shader: factor = brightness → 0=transparent, 1=emission
    mix_shader = nodes.new('ShaderNodeMixShader')
    mix_shader.location = (400, 0)
    links.new(transparent.outputs['BSDF'], mix_shader.inputs[1])
    links.new(emission.outputs['Emission'], mix_shader.inputs[2])
    links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])

    # Texture → brightness as mix factor (with contrast boost for additive look)
    img = _load_fx_image(tex_name)
    if img:
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = img
        tex_node.location = (-400, 0)

        rgb_to_bw = nodes.new('ShaderNodeRGBToBW')
        rgb_to_bw.location = (-200, 0)
        links.new(tex_node.outputs['Color'], rgb_to_bw.inputs['Color'])

        # Power node: raises brightness to power 0.5 (sqrt) to boost mid-tones
        # and make dark areas more transparent (mimics additive blending)
        power = nodes.new('ShaderNodeMath')
        power.operation = 'POWER'
        power.location = (0, 0)
        power.inputs[1].default_value = edge_power
        links.new(rgb_to_bw.outputs['Val'], power.inputs[0])
        links.new(power.outputs['Value'], mix_shader.inputs[0])  # Fac
    else:
        mix_shader.inputs[0].default_value = 1.0

    return mat


def _update_corona_color(mat, color_rgb):
    """Update existing corona material color. color_rgb: (r,g,b) floats 0-1."""
    if not mat or not mat.use_nodes:
        return
    r, g, b = color_rgb[0], color_rgb[1], color_rgb[2]
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            node.inputs['Color'].default_value = (r, g, b, 1.0)
            break


def _create_shadow_material(shadow_tex: str) -> bpy.types.Material:
    """Create shadow plane material: Transparent + dark Diffuse mixed by texture brightness.

    Black pixels = fully transparent, white pixels = dark shadow.
    Same approach as corona material but with dark color instead of emission.
    """
    mat_name = f"2dfx_shadow_{shadow_tex}"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    if hasattr(mat, 'blend_method'):
        mat.blend_method = 'BLEND'
    mat.use_backface_culling = False

    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    # Transparent BSDF (for black parts)
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (200, 100)

    # Diffuse BSDF (dark shadow, semi-transparent look)
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.location = (200, -100)
    diffuse.inputs['Color'].default_value = (0, 0, 0, 1.0)

    # Mix Shader: factor = brightness → 0=transparent, 1=dark shadow
    mix_shader = nodes.new('ShaderNodeMixShader')
    mix_shader.location = (400, 0)
    links.new(transparent.outputs['BSDF'], mix_shader.inputs[1])
    links.new(diffuse.outputs['BSDF'], mix_shader.inputs[2])
    links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])

    # Texture → brightness as mix factor
    img = _load_fx_image(shadow_tex)
    if img:
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = img
        tex_node.location = (-200, 0)

        rgb_to_bw = nodes.new('ShaderNodeRGBToBW')
        rgb_to_bw.location = (0, 0)
        links.new(tex_node.outputs['Color'], rgb_to_bw.inputs['Color'])
        links.new(rgb_to_bw.outputs['Val'], mix_shader.inputs[0])  # Fac
    else:
        mix_shader.inputs[0].default_value = 0.3

    return mat


def create_light_preview(parent_obj):
    """Create visual preview children for a Light2dfx Empty.

    Creates:
    - A Point Light (color, range)
    - A billboard plane with corona texture (vertical, facing Y)
    """
    inu = getattr(parent_obj, 'inu', None)
    if inu and hasattr(inu, 'color_2dfx'):
        c = inu.color_2dfx
        r, g, b = c[0], c[1], c[2]
    else:
        color = parent_obj.get('2dfx_color', [255, 255, 255, 255])
        r = min(color[0], 255) / 255.0
        g = min(color[1], 255) / 255.0
        b = min(color[2], 255) / 255.0
    corona_tex = inu.corona_tex_2dfx if inu else parent_obj.get('2dfx_corona_tex', 'coronastar')
    corona_size = parent_obj.get('2dfx_corona_size', 1.0)
    shadow_size = parent_obj.get('2dfx_shadow_size', 8.0)

    collection = parent_obj.users_collection[0] if parent_obj.users_collection else bpy.context.collection

    # ── Point Light (radius driven by shadow_size like in GTA SA) ──
    light_name = f"{parent_obj.name}_light"
    light_data = bpy.data.lights.new(light_name, 'POINT')
    light_data.color = (r, g, b)
    light_data.energy = shadow_size * 5.0
    light_data.shadow_soft_size = shadow_size

    if hasattr(light_data, 'use_custom_distance'):
        light_data.use_custom_distance = True
        light_data.cutoff_distance = shadow_size

    light_obj = bpy.data.objects.new(light_name, light_data)
    light_obj.parent = parent_obj
    light_obj.location = (0, 0, 0)
    collection.objects.link(light_obj)
    _lock_child(light_obj)

    # ── Billboard plane (corona sprite) ──
    billboard_name = f"{parent_obj.name}_corona"
    plane_mesh = _create_plane_mesh(billboard_name, size=1.0)

    billboard = bpy.data.objects.new(billboard_name, plane_mesh)
    billboard.parent = parent_obj
    billboard.location = (0, 0, 0)
    # corona_size is the world-space corona radius in metres — use it
    # directly as the plane scale so the preview matches the real sprite
    # footprint. Earlier we multiplied by 5×, which made every preview
    # plane appear 5× the actual GTA corona.
    billboard.scale = (corona_size, corona_size, corona_size)

    collection.objects.link(billboard)

    # Assign corona material
    mat = _create_corona_material(corona_tex, (r, g, b))
    billboard.data.materials.append(mat)

    _lock_child(billboard, lock_rotation=False)

    return light_obj, billboard


_particle_txd_loaded_for: str = ""  # game_root we've already auto-loaded from


def _ensure_particle_txd_loaded() -> int:
    """One-shot auto-load of particle textures for the current game_root.

    Looks first for standalone `models/particle.txd` (and siblings), then
    falls back to extracting them from `models/gta3.img`. Loaded textures
    land in `bpy.data.images` with fake_user=True. Re-runs if the key
    texture `sphere` disappears.

    Returns the number of images added on this call.
    """
    global _particle_txd_loaded_for
    try:
        game_root = bpy.path.abspath(
            getattr(bpy.context.scene, 'gtatools_game_root', '') or ''
        )
        if not game_root or not os.path.isdir(game_root):
            print(f"[2DFX Particle] auto-load: game_root invalid ({game_root!r})")
            return 0

        # Skip if already auto-loaded and sphere is available.
        if _particle_txd_loaded_for == game_root and 'sphere' in bpy.data.images:
            return 0

        from .txd_import import import_txd, import_txd_bytes

        candidate_txds = (
            'particle.txd', 'particle2.txd',
            'effectsPC.txd', 'misc.txd',
        )

        total = 0

        # 1) Standalone files in models/
        models_dir = os.path.join(game_root, 'models')
        for txd_name in candidate_txds:
            path = os.path.join(models_dir, txd_name)
            if os.path.isfile(path):
                try:
                    imgs = import_txd(path, assign_to_materials=False)
                    total += len(imgs)
                    print(f"[2DFX Particle] auto-loaded {len(imgs)} textures from standalone {txd_name}")
                except Exception as e:
                    print(f"[2DFX Particle] failed to parse standalone {txd_name}: {e}")

        # 2) Fallback: inside gta3.img
        if 'sphere' not in bpy.data.images:
            img_path = os.path.join(models_dir, 'gta3.img')
            if os.path.isfile(img_path):
                from ..core import img as _img
                for txd_name in candidate_txds:
                    data = _img.extract_file(img_path, txd_name)
                    if data is None:
                        continue
                    try:
                        imgs = import_txd_bytes(data, assign_to_materials=False)
                        total += len(imgs)
                        print(f"[2DFX Particle] auto-loaded {len(imgs)} textures from gta3.img/{txd_name}")
                    except Exception as e:
                        print(f"[2DFX Particle] failed to parse gta3.img/{txd_name}: {e}")

        if total == 0:
            print(f"[2DFX Particle] auto-load found no particle TXDs in {models_dir}")

        _particle_txd_loaded_for = game_root
        return total
    except Exception as e:
        import traceback
        print(f"[2DFX Particle] auto-load error: {e}")
        traceback.print_exc()
        return 0


def _find_particle_image(tex_name: str):
    """Find a loaded image for a particle texture name.

    Matches (case-insensitive):
      - exact name
      - name with common extension
      - image name stem (filename without extension)
      - filepath basename stem
      - image name or stem CONTAINING the target as a substring (last resort)
    """
    if not tex_name:
        return None

    # Exact match first (fast path)
    img = bpy.data.images.get(tex_name)
    if img is not None:
        print(f"[2DFX Particle] texture '{tex_name}' -> exact match '{img.name}'")
        return img

    target = tex_name.lower()
    target_exts = (target, target + ".png", target + ".tga", target + ".dds", target + ".bmp")

    # Strict passes
    for image in bpy.data.images:
        name_lower = image.name.lower()
        if name_lower in target_exts:
            print(f"[2DFX Particle] texture '{tex_name}' -> ext match '{image.name}'")
            return image
        stem = os.path.splitext(name_lower)[0]
        if stem == target:
            print(f"[2DFX Particle] texture '{tex_name}' -> stem match '{image.name}'")
            return image
        fp = getattr(image, 'filepath', '') or ''
        if fp:
            fp_stem = os.path.splitext(os.path.basename(fp).lower())[0]
            if fp_stem == target:
                print(f"[2DFX Particle] texture '{tex_name}' -> filepath match '{image.name}'")
                return image

    # Fuzzy substring pass (last resort, helps with prefixed/suffixed names)
    for image in bpy.data.images:
        name_lower = image.name.lower()
        stem = os.path.splitext(name_lower)[0]
        if target in stem or target in name_lower:
            print(f"[2DFX Particle] texture '{tex_name}' -> fuzzy match '{image.name}'")
            return image

    all_names = [i.name for i in bpy.data.images]
    print(f"[2DFX Particle] texture '{tex_name}' NOT FOUND among {len(all_names)} images: {all_names[:20]}{'...' if len(all_names) > 20 else ''}")
    return None


def _create_particle_material(effect_name: str, color_rgb, tex_name) -> bpy.types.Material:
    """Emission material for a particle billboard, optionally textured.

    color_rgb — (r,g,b) floats 0..1 (sampled from the COLOUR curve at t=0).
    tex_name  — name of an already-loaded bpy.data.image, or None for flat plane.
    """
    mat_name = f"2dfx_particle_{effect_name}"
    if mat_name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[mat_name], do_unlink=True)

    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    if hasattr(mat, 'blend_method'):
        mat.blend_method = 'BLEND'
    mat.use_backface_culling = False

    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    r, g, b = color_rgb[0], color_rgb[1], color_rgb[2]

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)

    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (200, 100)

    emission = nodes.new('ShaderNodeEmission')
    emission.location = (200, -100)
    emission.inputs['Color'].default_value = (r, g, b, 1.0)
    emission.inputs['Strength'].default_value = 1.0

    mix_shader = nodes.new('ShaderNodeMixShader')
    mix_shader.location = (400, 0)
    links.new(transparent.outputs['BSDF'], mix_shader.inputs[1])
    links.new(emission.outputs['Emission'], mix_shader.inputs[2])
    links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])

    img = _find_particle_image(tex_name) if tex_name else None
    if img is None:
        # Diagnostic: bright magenta so "missing texture" is visually distinct
        # from a genuinely-white particle effect.
        emission.inputs['Color'].default_value = (1.0, 0.0, 1.0, 1.0)
        mix_shader.inputs[0].default_value = 0.9
        print(f"[2DFX Particle] material '{mat_name}' created WITHOUT texture (tex_name={tex_name!r})")
        return mat

    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = img
    tex_node.location = (-400, 0)

    # Texture colour tinted by the particle colour
    mix_rgb = nodes.new('ShaderNodeMixRGB')
    mix_rgb.blend_type = 'MULTIPLY'
    mix_rgb.inputs['Fac'].default_value = 1.0
    mix_rgb.inputs['Color2'].default_value = (r, g, b, 1.0)
    mix_rgb.location = (-100, -100)
    links.new(tex_node.outputs['Color'], mix_rgb.inputs['Color1'])
    links.new(mix_rgb.outputs['Color'], emission.inputs['Color'])

    # Texture alpha → mix factor (0 transparent, 1 emission)
    links.new(tex_node.outputs['Alpha'], mix_shader.inputs[0])
    print(f"[2DFX Particle] material '{mat_name}' using image '{img.name}'")

    return mat


def _particle_appearance_from_obj(obj):
    """Return (tint_rgb, scale, tex_name) for the billboard preview.

    Reads from `obj.inu.particle_*` which is populated when the user picks
    an effect from the dropdown. Falls back to the largest value between
    size_start and size_end, and the brightest of the two colors.
    """
    inu = getattr(obj, 'inu', None)
    if inu is None:
        return (1.0, 1.0, 1.0), 1.0, None

    tex_name = (inu.particle_texture or '').strip() or None

    # Use start colour for the billboard tint (it's usually the fully-lit
    # moment of the particle, and avoids a faded preview when alpha=0 at t=1).
    c = inu.particle_color_start
    tint = (c[0], c[1], c[2])

    scale = max(inu.particle_size_start, inu.particle_size_end, 0.05)
    scale = min(scale, 20.0)

    return tint, scale, tex_name


def create_particle_preview(parent_obj):
    """Create a billboard preview child for a Particle2dfx Empty.

    Reads effects.fxp for the selected effect name, samples its first emitter's
    COLOUR/SIZE/TEXTURE, and builds a single camera-facing plane. No simulation.
    Also ensures particle textures are auto-loaded from gta3.img on first use.
    """
    _ensure_particle_txd_loaded()

    effect_name = parent_obj.get('2dfx_effect_name', '') or ''
    inu = getattr(parent_obj, 'inu', None)

    # Lazy migration: if an effect is set but our editable fields are still
    # at defaults (blend opened with older addon version, or the user just
    # typed a name), populate them from the FXP now.
    if (effect_name and inu is not None
            and not (inu.particle_texture or '').strip()):
        try:
            from .. import _populate_particle_props_from_fxp
            _populate_particle_props_from_fxp(
                parent_obj, effect_name,
                int(getattr(inu, 'particle_emitter_index', 0)),
            )
        except Exception as e:
            print(f"[2DFX Particle] lazy populate failed: {e}")

    tint, scale, tex_name = _particle_appearance_from_obj(parent_obj)

    collection = parent_obj.users_collection[0] if parent_obj.users_collection else bpy.context.collection

    billboard_name = f"{parent_obj.name}_particle"
    plane_mesh = _create_plane_mesh(billboard_name, size=1.0)
    billboard = bpy.data.objects.new(billboard_name, plane_mesh)
    billboard.parent = parent_obj
    billboard.location = (0, 0, 0)
    billboard.scale = (scale, scale, scale)
    collection.objects.link(billboard)

    mat = _create_particle_material(effect_name or "empty", tint, tex_name)
    billboard.data.materials.append(mat)

    _lock_child(billboard, lock_rotation=False)
    _face_billboard_to_view(billboard)
    return billboard


def update_particle_preview(parent_obj):
    """Recreate particle preview for a Particle2dfx Empty."""
    remove_preview_children(parent_obj)
    create_particle_preview(parent_obj)


def create_shadow_preview(parent_obj):
    """Create shadow projection plane below a Light2dfx Empty."""
    shadow_tex = parent_obj.get('2dfx_shadow_tex', 'shad_exp')
    shadow_size = parent_obj.get('2dfx_shadow_size', 4.0)

    if not shadow_tex or shadow_size <= 0:
        return None

    collection = parent_obj.users_collection[0] if parent_obj.users_collection else bpy.context.collection

    shadow_name = f"{parent_obj.name}_shadow"
    plane_mesh = _create_plane_mesh(shadow_name, size=1.0)

    shadow_plane = bpy.data.objects.new(shadow_name, plane_mesh)
    shadow_plane.parent = parent_obj
    # Shadow projects to ground (Z=0 world), offset from parent
    shadow_plane.location = (0, 0, -parent_obj.location.z)
    shadow_plane.scale = (shadow_size, shadow_size, 1.0)
    collection.objects.link(shadow_plane)

    mat = _create_shadow_material(shadow_tex)
    shadow_plane.data.materials.append(mat)

    _lock_child(shadow_plane)

    return shadow_plane


def remove_preview_children(parent_obj):
    """Remove all preview children (lights, billboards, shadows)."""
    children_to_remove = []
    for child in parent_obj.children:
        inu = getattr(child, 'inu', None)
        if inu and inu.type == 'NON' and parent_obj.name in child.name:
            children_to_remove.append(child)

    for child in children_to_remove:
        mesh_data = child.data if child.type == 'MESH' else None
        light_data = child.data if child.type == 'LIGHT' else None
        bpy.data.objects.remove(child, do_unlink=True)
        if mesh_data and mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)
        if light_data and light_data.users == 0:
            bpy.data.lights.remove(light_data)


def update_light_preview(parent_obj):
    """Recreate visual preview for a Light2dfx Empty."""
    remove_preview_children(parent_obj)
    create_light_preview(parent_obj)


def sync_preview_from_props(parent_obj):
    """Update existing preview children to match current properties (no recreate).

    Updates color, size, light energy/range in real-time.
    """
    inu = getattr(parent_obj, 'inu', None)
    if inu and hasattr(inu, 'color_2dfx'):
        c = inu.color_2dfx
        r, g, b = c[0], c[1], c[2]
    else:
        color = parent_obj.get('2dfx_color', [255, 255, 255, 255])
        r = min(color[0], 255) / 255.0
        g = min(color[1], 255) / 255.0
        b = min(color[2], 255) / 255.0
    corona_size = parent_obj.get('2dfx_corona_size', 1.0)
    shadow_size = parent_obj.get('2dfx_shadow_size', 8.0)

    for child in parent_obj.children:
        inu_c = getattr(child, 'inu', None)
        if not inu_c or inu_c.type != 'NON':
            continue

        if child.type == 'LIGHT':
            child.data.color = (r, g, b)
            child.data.energy = shadow_size * 5.0
            child.data.shadow_soft_size = shadow_size
            if hasattr(child.data, 'use_custom_distance'):
                child.data.cutoff_distance = shadow_size

        elif child.type == 'MESH' and '_corona' in child.name:
            child.scale = (corona_size, corona_size, corona_size)
            # Update emission color in material
            if child.data.materials:
                mat = child.data.materials[0]
                if mat and mat.use_nodes:
                    for node in mat.node_tree.nodes:
                        if node.type == 'EMISSION':
                            node.inputs['Color'].default_value = (r, g, b, 1.0)
                            break


# ── Billboard facing timer ──

_billboard_timer_running = False

# Per-object random flash state: {obj_name: (visible, next_toggle_time)}
_flash_states = {}


def _get_show_mode(parent_obj):
    """Get show_mode value from parent 2DFX object."""
    inu = getattr(parent_obj, 'inu', None)
    if inu and hasattr(inu, 'show_mode_2dfx'):
        return inu.show_mode_2dfx  # '0'..'5'
    return '0'


def _apply_show_mode_visibility(corona_obj, parent_obj):
    """Animate corona visibility based on show_mode.

    Show modes in GTA SA:
      0 - DEFAULT: always on
      1 - RANDOM_FLASHING: random on/off flicker
      2 - FLASH_RAIN: flashes only in rain (preview: slow pulse)
      3 - ONLY_RAIN: visible only in rain (preview: dimmed, blinking)
      4 - NO_RAIN: hidden in rain (preview: normal, steady)
      5 - FLASH_5: fast strobe flashing
    """
    mode = _get_show_mode(parent_obj)
    t = time.time()
    key = parent_obj.name

    if mode == '0' or mode == '4':
        # DEFAULT / NO_RAIN: always visible
        corona_obj.hide_viewport = False
        _set_corona_emission(corona_obj, 0.7)

    elif mode == '1':
        # RANDOM_FLASHING: random toggle every 0.2-1.0 sec
        state = _flash_states.get(key)
        if state is None or t >= state[1]:
            visible = not (state[0] if state else True)
            interval = random.uniform(0.15, 0.8)
            _flash_states[key] = (visible, t + interval)
        else:
            visible = state[0]
        corona_obj.hide_viewport = not visible

    elif mode == '2':
        # FLASH_RAIN: slow pulse (sine wave on emission)
        pulse = (math.sin(t * 3.0) + 1.0) / 2.0  # 0..1
        _set_corona_emission(corona_obj, 0.1 + pulse * 0.7)
        corona_obj.hide_viewport = False

    elif mode == '3':
        # ONLY_RAIN: dimmed with slow blink
        pulse = (math.sin(t * 1.5) + 1.0) / 2.0
        _set_corona_emission(corona_obj, 0.15 + pulse * 0.3)
        corona_obj.hide_viewport = False

    elif mode == '5':
        # FLASH_5: fast strobe (~5 Hz)
        on = (int(t * 5) % 2) == 0
        corona_obj.hide_viewport = not on


def _set_corona_emission(corona_obj, strength):
    """Set emission strength on corona material."""
    if corona_obj.data and corona_obj.data.materials:
        mat = corona_obj.data.materials[0]
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'EMISSION':
                    node.inputs['Strength'].default_value = strength
                    break


def _update_billboard_rotations():
    """Timer: rotate all corona billboards to face the active 3D viewport camera."""
    try:
        # Find active 3D viewport — check all windows (not just context.screen)
        view_quat = None
        wm = bpy.context.window_manager
        if wm is None:
            print("[2DFX Billboard] No window_manager")
            return 0.1
        for window in wm.windows:
            screen = window.screen
            if screen is None:
                continue
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            view_quat = space.region_3d.view_rotation.copy()
                            break
                    if view_quat:
                        break
            if view_quat:
                break

        if view_quat is None:
            return 0.1

        billboard_euler = view_quat.to_euler()

        for obj in bpy.data.objects:
            if (obj.type == 'MESH'
                    and '_corona' in obj.name
                    and getattr(obj, 'inu', None)
                    and obj.inu.type == 'NON'):
                obj.rotation_euler = billboard_euler

                # Apply show mode animation if parent is a 2DFX object
                parent = obj.parent
                if parent and getattr(parent, 'inu', None) and parent.inu.type == '2DFX':
                    _apply_show_mode_visibility(obj, parent)

    except Exception as e:
        print(f"[2DFX Billboard] Timer error: {e}")

    return 0.1  # Repeat every 0.1 sec


_billboard_draw_handler = None
_last_view_quat = None


def _current_view_rotation():
    """Return the active 3D viewport's view_rotation, or None.

    Safe to call from property-update callbacks where `context.region_data`
    is not available — scans all windows for a VIEW_3D area.
    """
    try:
        wm = bpy.context.window_manager
        if wm is None:
            return None
        for window in wm.windows:
            screen = window.screen
            if screen is None:
                continue
            for area in screen.areas:
                if area.type != 'VIEW_3D':
                    continue
                for space in area.spaces:
                    if space.type == 'VIEW_3D' and space.region_3d is not None:
                        return space.region_3d.view_rotation.copy()
    except Exception:
        pass
    return None


def _face_billboard_to_view(obj):
    """Snap a freshly-created billboard so it faces the current viewport."""
    quat = _current_view_rotation()
    if quat is not None:
        obj.rotation_euler = quat.to_euler()
    # Invalidate the draw-handler cache so the next redraw won't short-circuit.
    global _last_view_quat
    _last_view_quat = None


def _billboard_draw_callback():
    """Draw handler: runs on every VIEW_3D redraw, updates billboards to face camera."""
    global _last_view_quat
    try:
        region_3d = bpy.context.region_data
        if region_3d is None:
            return
        view_quat = region_3d.view_rotation.copy()

        # Skip if view hasn't changed (optimization)
        if _last_view_quat is not None:
            diff = (view_quat - _last_view_quat).magnitude
            if diff < 0.0001:
                return
        _last_view_quat = view_quat

        billboard_euler = view_quat.to_euler()

        for obj in bpy.data.objects:
            if (obj.type == 'MESH'
                    and ('_corona' in obj.name or '_particle' in obj.name)
                    and getattr(obj, 'inu', None)
                    and obj.inu.type == 'NON'):
                obj.rotation_euler = billboard_euler

                parent = obj.parent
                if parent and getattr(parent, 'inu', None) and parent.inu.type == '2DFX':
                    if '_corona' in obj.name:
                        _apply_show_mode_visibility(obj, parent)
    except Exception as e:
        print(f"[2DFX Billboard] Draw handler error: {e}")


def start_billboard_timer():
    """Register draw handler for billboard rotation updates."""
    global _billboard_draw_handler
    # Keep timer fallback too
    if bpy.app.timers.is_registered(_update_billboard_rotations):
        bpy.app.timers.unregister(_update_billboard_rotations)
    bpy.app.timers.register(_update_billboard_rotations, first_interval=0.1)

    # Register draw handler on VIEW_3D space
    if _billboard_draw_handler is None:
        try:
            _billboard_draw_handler = bpy.types.SpaceView3D.draw_handler_add(
                _billboard_draw_callback, (), 'WINDOW', 'POST_VIEW')
            print("[2DFX Billboard] Draw handler registered")
        except Exception as e:
            print(f"[2DFX Billboard] Failed to register draw handler: {e}")


def stop_billboard_timer():
    """Unregister draw handler and timer."""
    global _billboard_draw_handler
    if _billboard_draw_handler is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_billboard_draw_handler, 'WINDOW')
        except Exception:
            pass
        _billboard_draw_handler = None
