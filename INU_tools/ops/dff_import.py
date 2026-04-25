# INU_tools.ops.dff_import
# DFF (RenderWare Clump) → Blender mesh objects.
# Uses INU_tools.core.dff for binary format reading.

import os
import bpy
import bmesh
import mathutils
import numpy as np

from ..core.dff import (
    read_dff_file, DffClump, DffGeometry, DffFrame, DffAtomic,
    RGBA, TexCoords, DffMaterial, DffTexture, UserData,
    SkinData, HAnimData, HAnimBone,
    GEOM_NORMALS, GEOM_PRELIT, GEOM_TEXTURED, GEOM_TEXTURED2,
    USERDATA_INT, USERDATA_FLOAT, USERDATA_STRING,
    Extension2dfx, Light2dfx, Particle2dfx, PedAttractor2dfx, SunGlare2dfx,
)


def _store_user_data(target, user_data: UserData):
    """Store UserData PLG into Blender custom properties.

    Saves as 'inu_user_data' — a list of dicts, each with
    'name', 'type' (int/float/str), and 'data' (list of values).
    """
    if not user_data or not user_data.sections:
        return

    type_names = {USERDATA_INT: 'int', USERDATA_FLOAT: 'float', USERDATA_STRING: 'str'}
    sections = []
    for sec in user_data.sections:
        sections.append({
            'name': sec.name,
            'type': type_names.get(sec.data_type, 'na'),
            'data': list(sec.data),
        })
    target['inu_user_data'] = sections


def _apply_uv_anim_to_material(mat, dff_mat: DffMaterial, uv_anim_dict):
    """Propagate clump UV anim (0x2B dict + 0x135 PLG names) into
    ``mat.inu.uv_anim_*`` so the writer's linear scroll can round-trip.

    Writer builds a 2-keyframe anim from ``speed_u/speed_v/duration`` —
    we invert that: first name wins, read ``duration`` from the anim,
    and derive speeds from ``kf1.trans / kf1.time``. More complex
    multi-keyframe anims flatten to the same speed/duration pair (we
    don't preserve intermediate keys yet; round-trip is lossy for
    hand-edited IFP but correct for addon-round-tripped files).
    """
    if not dff_mat.uv_anim_names or uv_anim_dict is None:
        return
    name = dff_mat.uv_anim_names[0]
    target = None
    for anim in uv_anim_dict.anims:
        if anim.name == name:
            target = anim
            break
    if target is None or not target.keyframes:
        return

    inu = getattr(mat, 'inu', None)
    if inu is None:
        return

    inu.uv_anim_write = True
    try:
        inu.animation_name = name
    except Exception:
        # animation_name may not exist on older addon builds —
        # fall back to material name matching implicitly.
        pass
    inu.uv_anim_duration = max(0.01, float(target.duration))

    # Linear-scroll inference: the writer encodes scroll speed as
    # (trans_u, trans_v) on the last keyframe at time = duration.
    last = target.keyframes[-1]
    dt = max(last.time, 1e-6)
    inu.uv_anim_speed_u = float(last.trans_u) / dt
    inu.uv_anim_speed_v = float(last.trans_v) / dt


def _create_blender_material(dff_mat: DffMaterial, index: int,
                             material_cache: dict | None = None,
                             uv_anim_dict=None) -> bpy.types.Material:
    """Создаём Blender материал из DFF материала.

    If ``material_cache`` (shared dict) is provided, materials without
    advanced effects (env_map / bump_map / specular / reflection /
    dual_texture / user_data) are deduplicated by (texture name, RGBA
    color) — massively cuts ``bpy.data.materials.new`` calls for a
    bulk map import where the same texture repeats across thousands
    of DFFs. Materials with advanced effects are always created fresh
    because each can carry per-model parameters.
    """
    tex_name = ""
    if dff_mat.texture and dff_mat.texture.name:
        tex_name = dff_mat.texture.name

    # Advanced effects prevent caching — each model may ship its own
    # env_map/bump_map coefficients even under the same texture name.
    has_effects = bool(
        dff_mat.env_map or dff_mat.bump_map or dff_mat.specular or
        dff_mat.reflection or dff_mat.dual_texture or dff_mat.user_data
    )

    cache_key = None
    if material_cache is not None and tex_name and not has_effects:
        c = dff_mat.color
        cache_key = (tex_name, c.r, c.g, c.b, c.a)
        cached = material_cache.get(cache_key)
        if cached is not None:
            return cached

    mat_name = tex_name if tex_name else f"Material_{index}"
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True

    # Сохраняем исходное имя текстуры в IDProp — Blender мог добавить .001/.002 к имени
    # материала при коллизии, а матчинг TXD→материал по имени в таком случае ломался.
    if tex_name:
        mat['dff_texture_name'] = tex_name

    tree = mat.node_tree
    nodes = tree.nodes

    # Получаем Principled BSDF
    bsdf = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break

    if bsdf is None:
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')

    # Устанавливаем цвет из DFF
    c = dff_mat.color
    bsdf.inputs['Base Color'].default_value = (c.r / 255.0, c.g / 255.0, c.b / 255.0, 1.0)

    # Connect texture if available
    tex_node = None
    if tex_name:
        img = bpy.data.images.get(tex_name)
        if not img:
            # Try with common extensions
            for ext in ('.png', '.bmp', '.tga', '.dds', '.jpg'):
                img = bpy.data.images.get(tex_name + ext)
                if img:
                    break
        # Always create Image Texture node (for later cache loading)
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.label = tex_name
        tex_node.location = (bsdf.location.x - 300, bsdf.location.y)
        tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
        if img:
            tex_node.image = img

    # Specular = 0 для GTA моделей
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = 0.0

    # Альфа — подключать только если материал прозрачный
    if c.a < 255:
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'
        bsdf.inputs['Alpha'].default_value = c.a / 255.0
        # Connect texture alpha to shader alpha
        if tex_node:
            tree.links.new(tex_node.outputs['Alpha'], bsdf.inputs['Alpha'])

    # Ambient в INU свойства
    mat.inu.ambient = dff_mat.surface.ambient if dff_mat.surface else 1.0

    # Material effects → INU свойства
    if dff_mat.env_map:
        mat.inu.export_env_map = True
        mat.inu.env_map_coef = dff_mat.env_map.coefficient
        mat.inu.env_map_fb_alpha = dff_mat.env_map.use_fb_alpha
        if dff_mat.env_map.texture:
            mat.inu.env_map_tex = dff_mat.env_map.texture.name

    if dff_mat.bump_map:
        mat.inu.export_bump_map = True
        if dff_mat.bump_map.bump_texture:
            mat.inu.bump_map_tex = dff_mat.bump_map.bump_texture.name

    if dff_mat.specular:
        mat.inu.export_specular = True
        mat.inu.specular_level = dff_mat.specular.level
        mat.inu.specular_texture = dff_mat.specular.name

    if dff_mat.reflection:
        mat.inu.export_reflection = True
        mat.inu.reflection_scale_x = dff_mat.reflection.scale_x
        mat.inu.reflection_scale_y = dff_mat.reflection.scale_y
        mat.inu.reflection_offset_x = dff_mat.reflection.offset_x
        mat.inu.reflection_offset_y = dff_mat.reflection.offset_y
        mat.inu.reflection_intensity = dff_mat.reflection.intensity

    if dff_mat.dual_texture:
        mat.inu.export_dual_tex = True
        mat.inu.dual_tex_src_blend = str(dff_mat.dual_texture.src_blend)
        mat.inu.dual_tex_dst_blend = str(dff_mat.dual_texture.dst_blend)
        if dff_mat.dual_texture.texture:
            mat.inu.dual_tex_texture = dff_mat.dual_texture.texture.name

    # User Data PLG
    if dff_mat.user_data:
        _store_user_data(mat, dff_mat.user_data)

    # UV animation — look up referenced anim names in the clump's dict
    # and populate mat.inu.uv_anim_* so the export writer round-trips.
    _apply_uv_anim_to_material(mat, dff_mat, uv_anim_dict)

    if cache_key is not None:
        material_cache[cache_key] = mat
    return mat


def _build_mesh_bmesh(mesh: bpy.types.Mesh, geom: DffGeometry):
    """Legacy bmesh-based mesh builder — used only as a fallback when the
    fast foreach_set path fails on malformed DFF geometry."""
    bm = bmesh.new()
    for v in geom.vertices:
        bm.verts.new((v[0], v[1], v[2]))
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()

    uv_layers = []
    for i in range(len(geom.uv_layers)):
        uv_name = "UVMap" if i == 0 else f"UVMap.{i:03d}"
        uv_layers.append(bm.loops.layers.uv.new(uv_name))

    vc_layer = bm.loops.layers.color.new("Day") if geom.prelit_colors else None
    nc_layer = (bm.loops.layers.color.new("Night")
                if geom.extra_colors and geom.extra_colors.colors else None)

    for tri in geom.triangles:
        try:
            face = bm.faces.new([bm.verts[tri.a], bm.verts[tri.b], bm.verts[tri.c]])
            face.material_index = tri.material
            if hasattr(face, 'smooth'):
                face.smooth = True
            for loop in face.loops:
                vi = loop.vert.index
                for uv_idx, uv_bl_layer in enumerate(uv_layers):
                    uv_data = geom.uv_layers[uv_idx]
                    if vi < len(uv_data):
                        tc = uv_data[vi]
                        loop[uv_bl_layer].uv = (tc.u, 1.0 - tc.v)
                if vc_layer and vi < len(geom.prelit_colors):
                    c = geom.prelit_colors[vi]
                    loop[vc_layer] = (c.r / 255.0, c.g / 255.0, c.b / 255.0, c.a / 255.0)
                if nc_layer and vi < len(geom.extra_colors.colors):
                    c = geom.extra_colors.colors[vi]
                    loop[nc_layer] = (c.r / 255.0, c.g / 255.0, c.b / 255.0, c.a / 255.0)
        except Exception as e:
            print(f"[INU_tools] Face error (bmesh fallback): {e}")

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def _build_mesh(geom: DffGeometry, name: str, materials: list,
                material_cache: dict | None = None,
                uv_anim_dict=None) -> bpy.types.Mesh:
    """Build a Blender Mesh from DFF geometry via direct foreach_set.

    Avoids bmesh entirely — all attributes are pushed in bulk through
    ``foreach_set`` which is a C-level batch assignment. For a 10k-vert
    mesh this is ~40x faster than the old bmesh per-face loop.

    Falls back to the legacy bmesh path if a bulk assign fails — some
    malformed vanilla DFFs have duplicate faces / bad winding that
    ``mesh.validate()`` can't fully clean up.

    ``material_cache`` is threaded through to ``_create_blender_material``
    for cross-DFF dedup in bulk map import.

    ``uv_anim_dict`` (from the clump) is looked up by material's
    ``uv_anim_names`` so ``mat.inu.uv_anim_*`` is populated on import
    and the writer can round-trip the animation.
    """
    mesh = bpy.data.meshes.new(name)

    # Materials first — polygon material_index references these by slot.
    for mi, dff_mat in enumerate(materials):
        bl_mat = _create_blender_material(
            dff_mat, mi, material_cache, uv_anim_dict)
        mesh.materials.append(bl_mat)

    n_verts = len(geom.vertices)
    n_tris = len(geom.triangles)

    if n_verts == 0 or n_tris == 0:
        mesh.update()
        if geom.user_data:
            _store_user_data(mesh, geom.user_data)
        return mesh

    try:
        # ── Vertices ────────────────────────────────────────────────────
        verts_np = np.asarray(geom.vertices, dtype=np.float32).reshape(-1, 3)
        mesh.vertices.add(n_verts)
        mesh.vertices.foreach_set('co', verts_np.ravel())

        # ── Triangles → loops + polygons ────────────────────────────────
        # Build flat index buffer [a0,b0,c0, a1,b1,c1, ...] from DFF tris.
        tri_np = np.empty((n_tris, 3), dtype=np.int32)
        mat_np = np.empty(n_tris, dtype=np.int32)
        for i, tri in enumerate(geom.triangles):
            tri_np[i, 0] = tri.a
            tri_np[i, 1] = tri.b
            tri_np[i, 2] = tri.c
            mat_np[i] = tri.material
        tri_flat = tri_np.ravel()

        n_loops = n_tris * 3
        mesh.loops.add(n_loops)
        mesh.polygons.add(n_tris)

        mesh.loops.foreach_set('vertex_index', tri_flat)
        mesh.polygons.foreach_set(
            'loop_start', np.arange(0, n_loops, 3, dtype=np.int32))
        mesh.polygons.foreach_set(
            'loop_total', np.full(n_tris, 3, dtype=np.int32))
        mesh.polygons.foreach_set('material_index', mat_np)

        # Smooth shading flag (compatible 4.1+, affects normal calc)
        if bpy.app.version >= (4, 1, 0):
            mesh.polygons.foreach_set(
                'use_smooth', np.ones(n_tris, dtype=bool))

        # ── UV layers (per-vertex DFF → per-loop Blender) ───────────────
        for i, uv_layer_data in enumerate(geom.uv_layers):
            if not uv_layer_data:
                continue
            uv_name = "UVMap" if i == 0 else f"UVMap.{i:03d}"
            uv_layer = mesh.uv_layers.new(name=uv_name)
            # Build per-vertex UV array — flip V (GTA top-origin → Blender bot).
            uvs_np = np.array([(tc.u, 1.0 - tc.v) for tc in uv_layer_data],
                              dtype=np.float32)
            # Expand to per-loop via fancy indexing: loop[k] ← vertex[tri_flat[k]]
            loop_uvs = uvs_np[tri_flat]
            uv_layer.data.foreach_set('uv', loop_uvs.ravel())

        # ── Vertex color layers (Day / Night) ───────────────────────────
        def _add_color_layer(layer_name: str, dff_colors):
            if not dff_colors:
                return
            attr = mesh.color_attributes.new(
                name=layer_name, type='BYTE_COLOR', domain='CORNER')
            cols_np = np.empty((len(dff_colors), 4), dtype=np.float32)
            for k, c in enumerate(dff_colors):
                cols_np[k, 0] = c.r / 255.0
                cols_np[k, 1] = c.g / 255.0
                cols_np[k, 2] = c.b / 255.0
                cols_np[k, 3] = c.a / 255.0
            loop_cols = cols_np[tri_flat]
            attr.data.foreach_set('color', loop_cols.ravel())

        _add_color_layer('Day', geom.prelit_colors)
        if geom.extra_colors and getattr(geom.extra_colors, 'colors', None):
            _add_color_layer('Night', geom.extra_colors.colors)

        mesh.update(calc_edges=True)
        mesh.validate(verbose=False)  # clean duplicate/degenerate faces

    except Exception as e:
        # Fallback to bmesh path on malformed geometry — rare but a few
        # vanilla DFFs have non-manifold data that foreach_set can't absorb.
        print(f"[INU_tools] foreach_set mesh build failed ({e}), falling back to bmesh")
        _build_mesh_bmesh(mesh, geom)

    # Store geometry user data on mesh
    if geom.user_data:
        _store_user_data(mesh, geom.user_data)

    return mesh


def _set_object_props(obj, geom: DffGeometry):
    """Записываем INU свойства объекта из DFF данных."""
    obj.inu.type = 'OBJ'
    obj.inu.export_normals = geom.export_normals
    obj.inu.export_binsplit = geom.write_bin_mesh

    if geom.pipeline:
        pipeline_hex = f"0x{geom.pipeline:08X}"
        known = {'0x53F20098', '0x53F2009A', '0x53F2009C'}
        if pipeline_hex in known:
            obj.inu.pipeline = pipeline_hex
        else:
            obj.inu.pipeline = 'CUSTOM'
            obj.inu.custom_pipeline = pipeline_hex

    # UV maps
    obj.inu.uv_map1 = len(geom.uv_layers) >= 1
    obj.inu.uv_map2 = len(geom.uv_layers) >= 2

    # Color flags
    obj.inu.day_cols = bool(geom.prelit_colors)
    obj.inu.night_cols = bool(geom.extra_colors and geom.extra_colors.colors)


def _import_2dfx(ext_2dfx: Extension2dfx, collection, base_name: str) -> list:
    """Создаём Empty-объекты для каждого 2DFX эффекта.

    Каждый эффект хранится как Empty с типом '2DFX' и custom properties.
    """
    objects = []
    if not ext_2dfx or not ext_2dfx.entries:
        return objects

    for i, entry in enumerate(ext_2dfx.entries):
        if isinstance(entry, Light2dfx):
            name = f"{base_name}.2dfx_light.{i}"
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = 'PLAIN_AXES'
            obj.empty_display_size = 0.3
            obj.location = entry.loc

            obj.inu.type = '2DFX'
            obj.inu.effect_2dfx = 'LIGHT'

            obj.inu.color_2dfx = (entry.color.r / 255.0, entry.color.g / 255.0,
                                   entry.color.b / 255.0, entry.color.a / 255.0)
            obj['2dfx_corona_far_clip'] = entry.corona_far_clip
            obj['2dfx_pointlight_range'] = entry.pointlight_range
            obj['2dfx_corona_size'] = entry.corona_size
            obj['2dfx_shadow_size'] = entry.shadow_size
            obj['2dfx_corona_enable_reflection'] = entry.corona_enable_reflection
            obj['2dfx_shadow_color_multiplier'] = entry.shadow_color_multiplier
            obj['2dfx_flags1'] = entry.flags1
            # Set EnumProperty values for dropdowns
            try:
                obj.inu.corona_tex_2dfx = entry.corona_tex_name
            except TypeError:
                obj['2dfx_corona_tex'] = entry.corona_tex_name
            try:
                obj.inu.shadow_tex_2dfx = entry.shadow_tex_name
            except TypeError:
                obj['2dfx_shadow_tex'] = entry.shadow_tex_name
            try:
                obj.inu.show_mode_2dfx = str(entry.corona_show_mode)
            except TypeError:
                pass
            try:
                obj.inu.flare_type_2dfx = str(entry.corona_flare_type)
            except TypeError:
                pass
            obj['2dfx_shadow_z_distance'] = entry.shadow_z_distance
            obj['2dfx_flags2'] = entry.flags2
            if entry.look_direction is not None:
                obj['2dfx_look_direction'] = list(entry.look_direction)
            # Display precision
            for key in ('2dfx_corona_far_clip', '2dfx_pointlight_range',
                        '2dfx_corona_size', '2dfx_shadow_size'):
                ui = obj.id_properties_ui(key)
                ui.update(precision=1)

        elif isinstance(entry, Particle2dfx):
            name = f"{base_name}.2dfx_particle.{i}"
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = 'CIRCLE'
            obj.empty_display_size = 0.2
            obj.location = entry.loc

            obj.inu.type = '2DFX'
            obj.inu.effect_2dfx = 'PARTICLE'

            obj['2dfx_effect_name'] = entry.effect_name

        elif isinstance(entry, PedAttractor2dfx):
            name = f"{base_name}.2dfx_ped.{i}"
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = 'CUBE'
            obj.empty_display_size = 0.15
            obj.location = entry.loc

            obj.inu.type = '2DFX'
            obj.inu.effect_2dfx = 'PED_ATTRACTOR'

            obj['2dfx_attractor_type'] = entry.attractor_type
            obj['2dfx_rotation_matrix'] = list(entry.rotation_matrix)
            obj['2dfx_external_script'] = entry.external_script
            obj['2dfx_ped_probability'] = entry.ped_existing_probability

        elif isinstance(entry, SunGlare2dfx):
            name = f"{base_name}.2dfx_sunglare.{i}"
            obj = bpy.data.objects.new(name, None)
            obj.empty_display_type = 'SPHERE'
            obj.empty_display_size = 0.1
            obj.location = entry.loc

            obj.inu.type = '2DFX'
            obj.inu.effect_2dfx = 'SUN_GLARE'

        else:
            continue

        collection.objects.link(obj)
        objects.append(obj)

        # Визуальный превью для Light2dfx
        if isinstance(entry, Light2dfx):
            try:
                from .fx_preview import create_light_preview
                create_light_preview(obj)
            except Exception as e:
                print(f"[INU_tools] 2DFX import preview error: {e}")

    return objects


def _has_skeleton(clump: DffClump) -> bool:
    """Check if DFF has skeleton (HAnimData on any frame)."""
    return any(f.hanim and f.hanim.bones for f in clump.frames)


def _get_skinned_data(clump: DffClump):
    """Find the first geometry with SkinData."""
    for geom in clump.geometries:
        if geom.skin:
            return geom.skin
    return None


def _align_roll(vec, vecz, tarz):
    """Calculate bone roll to align Z axis (from DragonFF)."""
    import math
    sine_roll = vec.normalized().dot(vecz.normalized().cross(tarz.normalized()))
    if 1 < abs(sine_roll):
        sine_roll /= abs(sine_roll)
    if 0 < vecz.dot(tarz):
        return math.asin(sine_roll)
    elif 0 < sine_roll:
        return -math.asin(sine_roll) + math.pi
    else:
        return -math.asin(sine_roll) - math.pi


def _build_armature(clump: DffClump, name: str):
    """Create Blender Armature from DFF frame hierarchy + HAnimData + SkinData.

    Follows DragonFF approach: bone_matrices from SkinData → transposed → inverted → transform.
    Returns (armature_object, bone_names_list).
    """
    arm_data = bpy.data.armatures.new(f"{name}_Armature")
    arm_obj = bpy.data.objects.new(f"{name}_Armature", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)

    # Find root hanim frame (the one with the bone list)
    hanim_root_frame = None
    hanim_root_idx = 0
    for i, frame in enumerate(clump.frames):
        if frame.hanim and frame.hanim.bones:
            hanim_root_frame = frame
            hanim_root_idx = i
            break

    if not hanim_root_frame:
        print(f"[INU] No HAnimData root found in {name}")
        return arm_obj, []

    # Build bone_id → frame_index mapping
    bone_id_to_frame_idx = {}
    for i, frame in enumerate(clump.frames):
        if frame.hanim:
            bone_id_to_frame_idx[frame.hanim.bone_id] = i

    # Get skin data for bone matrices
    skin = _get_skinned_data(clump)

    print(f"[INU] Building armature: {len(hanim_root_frame.hanim.bones)} bones, "
          f"skin={'yes' if skin else 'no'}, "
          f"bone_matrices={len(skin.bone_matrices) if skin else 0}")

    # Enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    bone_names = []
    bone_list = {}  # frame_index → (edit_bone, has_connected_child)

    for bone_idx, hbone in enumerate(hanim_root_frame.hanim.bones):
        frame_idx = bone_id_to_frame_idx.get(hbone.bone_id)
        if frame_idx is None:
            print(f"[INU] Bone id={hbone.bone_id} has no matching frame, skipping")
            bone_names.append(f"Bone_{hbone.bone_id}")
            continue

        frame = clump.frames[frame_idx]
        bone_name = frame.name if frame.name else f"Bone_{hbone.bone_id}"

        e_bone = edit_bones.new(bone_name)
        e_bone.tail = (0, 0.05, 0)  # Prevent auto-deletion
        e_bone['bone_id'] = hbone.bone_id
        e_bone['bone_type'] = hbone.bone_type
        e_bone['bone_index'] = hbone.index
        e_bone['dff_frame_flags'] = frame.flags
        bone_names.append(bone_name)

        print(f"[INU]   Bone[{bone_idx}] '{bone_name}' id={hbone.bone_id} "
              f"index={hbone.index} frame={frame_idx} parent={frame.parent}")

        # Apply bone matrix from SkinData (exactly like DragonFF)
        if skin and hbone.index < len(skin.bone_matrices):
            matrix = mathutils.Matrix(skin.bone_matrices[hbone.index]).transposed()
            if abs(matrix.determinant()) > 1e-8:
                matrix.invert()
            else:
                matrix.identity()

            e_bone.transform(matrix, scale=True, roll=False)
            e_bone.roll = _align_roll(
                e_bone.vector, e_bone.z_axis,
                matrix.to_3x3() @ mathutils.Vector((0, 0, 1))
            )
        else:
            # Fallback: frame rotation/position
            rot = frame.rotation
            pos = frame.position
            matrix = mathutils.Matrix((
                (rot[0], rot[3], rot[6]),
                (rot[1], rot[4], rot[7]),
                (rot[2], rot[5], rot[8]),
            ))
            e_bone.matrix = (
                mathutils.Matrix.Translation(pos) @
                matrix.transposed().to_4x4()
            )

        # Parent relationship (like DragonFF: frame.parent >= root frame_index and in bone_list)
        if frame.parent >= hanim_root_idx and frame.parent in bone_list:
            e_bone.parent = bone_list[frame.parent][0]
            if skin is None:
                e_bone.matrix = bone_list[frame.parent][0].matrix @ e_bone.matrix

        # Key by frame_index (like DragonFF: bone_list[self.bones[bone.id]['index']])
        bone_list[frame_idx] = (e_bone, False)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Store ALL original frame data on armature object as JSON for round-trip export
    import json
    frame_data = {}
    for hbone in hanim_root_frame.hanim.bones:
        fi = bone_id_to_frame_idx.get(hbone.bone_id)
        if fi is None:
            continue
        f = clump.frames[fi]
        frame_data[str(hbone.bone_id)] = {
            'rot': list(f.rotation),
            'pos': list(f.position),
            'flags': f.flags,
            'parent': f.parent,
            'index': hbone.index,
            'write_name': f.write_name,
        }
        print(f"[INU]   save bone_id={hbone.bone_id} frame={fi} name='{f.name}' write_name={f.write_name}")
    arm_obj['dff_frame_data'] = json.dumps(frame_data)

    # Save raw DFF section bytes for perfect round-trip
    import base64
    if hasattr(clump.frames[0], '_raw_frame_list'):
        arm_obj['dff_raw_frame_list'] = base64.b64encode(clump.frames[0]._raw_frame_list).decode('ascii')
    if clump.raw_geometry_list:
        arm_obj['dff_raw_geometry_list'] = base64.b64encode(clump.raw_geometry_list).decode('ascii')
    if clump.raw_atomics:
        arm_obj['dff_raw_atomics'] = base64.b64encode(clump.raw_atomics).decode('ascii')

    print(f"[INU] Armature created: {len(bone_names)} bones")
    return arm_obj, bone_names


def _apply_skin_weights(obj, geom, arm_obj, bone_names):
    """Apply SkinData vertex weights to mesh object and parent to armature.

    DragonFF approach: create numbered vertex groups first, then rename to bone names.
    """
    skin = geom.skin
    if not skin:
        return

    print(f"[INU] Applying skin weights to '{obj.name}': "
          f"{skin.num_bones} bones, {len(skin.bone_indices)} verts")

    # Create vertex groups (one per bone, in order)
    for _ in range(skin.num_bones):
        obj.vertex_groups.new()

    # Assign weights by index (like DragonFF)
    for vi in range(min(len(obj.data.vertices), len(skin.bone_indices))):
        indices = skin.bone_indices[vi]
        weights = skin.bone_weights[vi]

        for bi in range(4):
            bone_idx = indices[bi]
            weight = weights[bi]
            if weight > 0.0 and bone_idx < skin.num_bones:
                obj.vertex_groups[bone_idx].add([vi], weight, 'ADD')

    # Rename vertex groups to bone names
    for i, bname in enumerate(bone_names):
        if i < len(obj.vertex_groups):
            obj.vertex_groups[i].name = bname

    # Store original bone_matrices for round-trip export
    import json
    obj['dff_bone_matrices'] = json.dumps(skin.bone_matrices)
    obj['dff_skin_num_used'] = skin.num_used
    obj['dff_skin_max_weights'] = skin.max_weights
    obj['dff_skin_bones_used'] = json.dumps(skin.bones_used)

    # Parent mesh to armature with Armature modifier
    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    print(f"[INU] Skin weights applied, {len(obj.vertex_groups)} vertex groups")


def import_dff(filepath: str, context=None, *, skip_2dfx=None,
               bulk_mode: bool = False, target_collection=None,
               material_cache: dict | None = None, profiler=None):
    """
    Импорт DFF файла в Blender.

    Args:
        filepath: Путь к .dff файлу.
        context: Blender context (опционально).
        skip_2dfx: пропустить импорт 2DFX-эффектов (лампы, частицы, ped attractors).
                   None → читать scene.gtatools_map_skip_2dfx.
        bulk_mode: при True пропускаются тяжёлые per-model операции —
                   ``view_layer.update()`` и ``select_all(DESELECT)``.
                   Для bulk-импорта карты их достаточно сделать один раз
                   в конце; в одиночном импорте эти вызовы нужны.
        target_collection: если указана — линковать созданные объекты
                   сразу в неё (избегает лишнего unlink+relink при
                   импорте карты).
        material_cache: общий dict для переиспользования материалов
                   между DFF (ключ — имя текстуры + RGBA). Сильно режет
                   время bulk-импорта карты.
        profiler: опциональный ``Profiler`` (см. ``INU_tools.tools.profiler``)
                   для замера под-стадий parse/build/link.
    """
    clump = read_dff_file(filepath)
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    return import_dff_from_clump(
        clump, base_name, skip_2dfx=skip_2dfx, bulk_mode=bulk_mode,
        target_collection=target_collection, material_cache=material_cache,
        profiler=profiler,
    )


def import_dff_from_clump(clump, base_name: str, *, skip_2dfx=None,
                          bulk_mode: bool = False, target_collection=None,
                          material_cache: dict | None = None, profiler=None):
    """Build Blender objects from an already-parsed DffClump.

    Separates the Blender-only work from the binary parse so the
    parse step can run in a worker thread (numpy releases the GIL)
    while the main thread stays busy creating bpy objects for the
    previous model.
    """
    # Resolve 2DFX skip flag from scene when not passed explicitly.
    if skip_2dfx is None:
        try:
            skip_2dfx = bool(getattr(
                bpy.context.scene, 'gtatools_map_skip_2dfx', False))
        except Exception:
            skip_2dfx = False

    # Null-object context manager so `with _stage(...)` works without
    # an `if profiler:` ladder every time. When profiler is None we
    # get effectively zero overhead.
    def _stage(name):
        if profiler is not None:
            return profiler.stage(name)
        class _Null:
            def __enter__(self): return self
            def __exit__(self, *a): return False
        return _Null()

    collection = target_collection if target_collection is not None else bpy.context.collection
    imported_objects = []
    frame_to_obj = {}  # frame_index → Blender object (MESH or EMPTY dummy)

    is_skinned = _has_skeleton(clump)

    # Создаём объекты из Atomic связей (frame → geometry)
    for atomic in clump.atomics:
        gi = atomic.geometry_index
        fi = atomic.frame_index

        if gi >= len(clump.geometries):
            continue

        geom = clump.geometries[gi]
        frame = clump.frames[fi] if fi < len(clump.frames) else None

        # Имя объекта: из фрейма или из имени файла
        obj_name = frame.name if (frame and frame.name) else f"{base_name}_{gi}"

        with _stage('build_mesh'):
            mesh = _build_mesh(geom, obj_name, geom.materials,
                               material_cache, clump.uv_anim_dict)

        # Создаём объект
        obj = bpy.data.objects.new(obj_name, mesh)

        # Трансформация применяется позже в hierarchy-проходе через matrix_world

        # INU свойства
        _set_object_props(obj, geom)
        # Store original UV layer count for round-trip
        obj['dff_num_uv_layers'] = len(geom.uv_layers)
        obj['dff_orig_vert_count'] = len(obj.data.vertices)
        # Store original geometry flags for round-trip
        obj['dff_geom_flags'] = geom._import_flags if hasattr(geom, '_import_flags') else 0
        # Store mesh frame index from atomic (needed for skinned export with edited geometry)
        obj['dff_mesh_frame_index'] = fi

        # Store original frame data for round-trip export
        if frame:
            obj['dff_frame_flags'] = frame.flags
            obj['dff_frame_rot'] = list(frame.rotation)
            obj['dff_frame_pos'] = list(frame.position)
            obj['dff_frame_write_name'] = frame.write_name

        # Frame user data → object custom property
        if frame and frame.user_data:
            _store_user_data(obj, frame.user_data)

        collection.objects.link(obj)
        imported_objects.append(obj)
        if frame is not None:
            frame_to_obj[fi] = obj

    # Если нет Atomic, но есть геометрии — создаём напрямую
    if not clump.atomics and clump.geometries:
        for gi, geom in enumerate(clump.geometries):
            obj_name = f"{base_name}_{gi}"
            with _stage('build_mesh'):
                mesh = _build_mesh(geom, obj_name, geom.materials,
                               material_cache, clump.uv_anim_dict)
            obj = bpy.data.objects.new(obj_name, mesh)
            _set_object_props(obj, geom)
            collection.objects.link(obj)
            imported_objects.append(obj)

    # Создаём Empty для каждого фрейма БЕЗ atomic'а (это dummy вроде wheel_lf_dummy)
    # Пропускаем если в DFF есть скелет — там фреймы представлены костями армутуры
    if not is_skinned:
        for fi, frame in enumerate(clump.frames):
            if fi in frame_to_obj:
                continue
            dummy_name = frame.name if frame.name else f"{base_name}_frame_{fi}"
            dummy = bpy.data.objects.new(dummy_name, None)
            dummy.empty_display_type = 'PLAIN_AXES'
            dummy.empty_display_size = 0.2

            dummy['dff_frame_flags'] = frame.flags
            dummy['dff_frame_rot'] = list(frame.rotation)
            dummy['dff_frame_pos'] = list(frame.position)
            dummy['dff_frame_write_name'] = frame.write_name

            if frame.user_data:
                _store_user_data(dummy, frame.user_data)

            collection.objects.link(dummy)
            imported_objects.append(dummy)
            frame_to_obj[fi] = dummy

        # Выставляем parent БЕЗ сохранения transform (matrix_parent_inverse=identity).
        for fi, frame in enumerate(clump.frames):
            child_obj = frame_to_obj.get(fi)
            if child_obj is None:
                continue
            parent_idx = frame.parent
            if 0 <= parent_idx < len(clump.frames):
                parent_obj = frame_to_obj.get(parent_idx)
                if parent_obj is not None and parent_obj is not child_obj:
                    child_obj.parent = parent_obj
                    child_obj.matrix_parent_inverse.identity()

        # Пишем matrix_basis прямо из DFF frame (rotation + position).
        # matrix_basis — внутреннее хранилище trans/rot/scale объекта, обходит
        # любые «умные» пересчёты Blender'а. При matrix_parent_inverse=identity
        # matrix_local == matrix_basis, а matrix_world = parent.matrix_world @ matrix_basis.
        for fi, frame in enumerate(clump.frames):
            obj = frame_to_obj.get(fi)
            if obj is None:
                continue
            rot = frame.rotation
            pos = frame.position
            obj.matrix_basis = mathutils.Matrix((
                (rot[0], rot[1], rot[2], pos[0]),
                (rot[3], rot[4], rot[5], pos[1]),
                (rot[6], rot[7], rot[8], pos[2]),
                (0, 0, 0, 1),
            ))

        if not bulk_mode:
            bpy.context.view_layer.update()

    # Skeleton: create Armature + apply skin weights if DFF has bones.
    # Two guards:
    #   1. bulk_mode (map import) — skip armatures entirely. Vanilla
    #      map DFFs occasionally carry HAnim chunks with skin=no, and
    #      we don't want a ``<name>_Armature`` object per such model
    #      cluttering the outliner and bloating depsgraph.
    #   2. require an actual skin somewhere — HAnim without skin is
    #      just animation metadata, no armature-bound mesh to pair with.
    has_skin = any(geom.skin for geom in clump.geometries)
    if not bulk_mode and _has_skeleton(clump) and has_skin:
        try:
            arm_obj, bone_names = _build_armature(clump, base_name)
            imported_objects.append(arm_obj)

            # Apply skin weights to skinned mesh objects
            for atomic in clump.atomics:
                gi = atomic.geometry_index
                if gi >= len(clump.geometries):
                    continue
                geom = clump.geometries[gi]
                if geom.skin:
                    fi = atomic.frame_index
                    frame = clump.frames[fi] if fi < len(clump.frames) else None
                    obj_name = frame.name if (frame and frame.name) else f"{base_name}_{gi}"
                    obj = bpy.data.objects.get(obj_name)
                    if obj and obj.type == 'MESH':
                        _apply_skin_weights(obj, geom, arm_obj, bone_names)
        except Exception as e:
            import traceback
            print(f"[INU_tools] Skeleton import error: {e}")
            traceback.print_exc()

    # Импорт 2DFX эффектов (собираем из всех геометрий) → коллекция "2DFX"
    if not skip_2dfx:
        fx_col = None
        for geom in clump.geometries:
            if geom.ext_2dfx and geom.ext_2dfx.entries:
                if fx_col is None:
                    col_name = "2DFX"
                    if col_name in bpy.data.collections:
                        fx_col = bpy.data.collections[col_name]
                    else:
                        fx_col = bpy.data.collections.new(col_name)
                        bpy.context.scene.collection.children.link(fx_col)
                fx_objects = _import_2dfx(geom.ext_2dfx, fx_col, base_name)
                imported_objects.extend(fx_objects)

    # Выделяем импортированные объекты. При bulk_mode пропускаем
    # select_all — это O(scene_size) операция, которая для импорта
    # карты (тысячи моделей) в сумме даёт O(N²). Для bulk достаточно
    # вернуть список и дать вызывающему коду самому решить.
    if not bulk_mode:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in imported_objects:
            obj.select_set(True)
        if imported_objects:
            bpy.context.view_layer.objects.active = imported_objects[0]

    return imported_objects
