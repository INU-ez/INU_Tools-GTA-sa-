# INU_tools.ops.dff_export
# Blender mesh objects → DFF file.
# Uses INU_tools.core.dff for binary format writing.

import os
import bmesh

from ..core.dff import (
    DffClump, DffFrame, DffGeometry, DffAtomic, DffLight,
    DffMaterial, DffTexture, SurfaceProperties,
    Triangle, BoundingSphere, TexCoords, RGBA,
    ExtraVertColors, SkinData, HAnimData, HAnimBone,
    BumpMapEffect, EnvMapEffect, DualTextureEffect, SpecularMaterial, ReflectionMaterial,
    UserData, UserDataSection,
    USERDATA_INT, USERDATA_FLOAT, USERDATA_STRING,
    Extension2dfx, Light2dfx, Particle2dfx, PedAttractor2dfx, SunGlare2dfx,
    GTA_SA_VERSION, write_dff_file,
)


# ── Helpers ──────────────────────────────────────────────────────

def _load_user_data(target) -> UserData:
    """Load UserData from Blender custom property 'inu_user_data'.

    Returns UserData or None if not present.
    """
    raw = target.get('inu_user_data')
    if not raw:
        return None

    type_map = {'int': USERDATA_INT, 'float': USERDATA_FLOAT, 'str': USERDATA_STRING}
    ud = UserData()
    # IDProperty arrays come back as IDPropertyArray or list
    sections = list(raw) if hasattr(raw, '__iter__') else []
    for sec_raw in sections:
        sec = UserDataSection()
        sec.name = sec_raw.get('name', '')
        sec.data_type = type_map.get(sec_raw.get('type', 'na'), 0)
        data_raw = sec_raw.get('data', [])
        sec.data = list(data_raw)
        ud.sections.append(sec)

    return ud if ud.sections else None


def _strip_ext(name: str) -> str:
    """Remove file extension from a name (e.g. 'tex.png' → 'tex')."""
    base, ext = os.path.splitext(name)
    if ext.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.tga', '.dds'):
        return base
    return name


def _color_to_rgba(c, alpha=1.0) -> RGBA:
    """Convert Blender float color (0-1) to RGBA (0-255)."""
    return RGBA(
        max(0, min(255, int(c[0] * 255))),
        max(0, min(255, int(c[1] * 255))),
        max(0, min(255, int(c[2] * 255))),
        max(0, min(255, int(alpha * 255))),
    )


# ── Material reading ─────────────────────────────────────────────

def _get_principled(mat):
    """Find Principled BSDF node in material."""
    if not mat or not mat.use_nodes:
        return None
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            return node
    return None


def _read_base_color(mat) -> RGBA:
    """Read base color from Principled BSDF or fallback."""
    principled = _get_principled(mat)
    if principled:
        bc = principled.inputs.get('Base Color')
        if bc:
            c = bc.default_value
            # Read alpha from Principled BSDF Alpha input
            alpha_input = principled.inputs.get('Alpha')
            alpha = int(alpha_input.default_value * 255) if alpha_input else int(c[3] * 255)
            return RGBA(int(c[0]*255), int(c[1]*255), int(c[2]*255), alpha)
    if hasattr(mat, 'diffuse_color'):
        c = mat.diffuse_color
        return RGBA(int(c[0]*255), int(c[1]*255), int(c[2]*255), 255)
    return RGBA()


def _read_texture(mat) -> DffTexture:
    """Read texture name from Principled BSDF image node.

    Walks through preview nodes (Prelight_Mix, LM_Mix) to find the real texture.
    Falls back to IDProp `dff_texture_name` set at import time — это страхует
    от кейса, когда TXD не был загружен и image=None на Texture-ноде, но имя
    текстуры всё равно известно из DFF.
    """
    # 1. Если импорт DFF сохранил имя текстуры — используем его как авторитетный
    dff_tex_name = mat.get('dff_texture_name')
    if dff_tex_name:
        return DffTexture(name=_strip_ext(dff_tex_name), mask="")

    principled = _get_principled(mat)
    if not principled:
        return None

    bc_input = principled.inputs.get('Base Color')
    if not bc_input or not bc_input.is_linked:
        return None

    source_node = bc_input.links[0].from_node

    # Walk through preview mix nodes (Prelight_Mix, LM_Mix) to find real texture
    # These wrappers have original texture on input 'A' or 'Color1'
    max_depth = 5
    while source_node and source_node.name in ("Prelight_Mix", "LM_Mix", "Lightmap_Mix") and max_depth > 0:
        max_depth -= 1
        a_input = source_node.inputs.get('A') or source_node.inputs.get('Color1')
        if not a_input or not a_input.is_linked:
            return None
        source_node = a_input.links[0].from_node

    # Also skip lightmap texture nodes if they ended up here
    if source_node and source_node.name in ("LM_Texture", "Lightmap_Texture"):
        return None

    if not source_node or source_node.type != 'TEX_IMAGE':
        return None

    # Prefer node label (сохранённое имя из DFF-импорта), иначе имя картинки.
    # Разрешаем источник без прикреплённой картинки — имени label'а достаточно.
    name = source_node.label
    if not name and source_node.image:
        name = source_node.image.name
    if not name:
        return None
    name = _strip_ext(name)

    return DffTexture(name=name, mask="")


def _read_surface(mat) -> SurfaceProperties:
    """Read surface properties (ambient, specular, diffuse)."""
    props = SurfaceProperties()
    principled = _get_principled(mat)

    if principled:
        spec_input = principled.inputs.get('Specular IOR Level')
        if spec_input is None:
            spec_input = principled.inputs.get('Specular')
        if spec_input:
            props.specular = spec_input.default_value

        rough_input = principled.inputs.get('Roughness')
        if rough_input:
            props.diffuse = rough_input.default_value

    # DragonFF ambient property (backward compatible)
    inu = getattr(mat, 'inu', None)
    if inu:
        props.ambient = getattr(inu, 'ambient', 1.0)

    return props


def _read_material_plugins(mat) -> dict:
    """Read material effect plugins from INU properties."""
    plugins = {}
    inu = getattr(mat, 'inu', None)
    if not inu:
        return plugins

    # Bump map
    if getattr(inu, 'export_bump_map', False):
        bump = BumpMapEffect()
        bump_tex_name = getattr(inu, 'bump_map_tex', '')
        if bump_tex_name:
            bump.bump_texture = DffTexture(name=bump_tex_name)
        plugins['bump_map'] = bump

    # Environment map
    if getattr(inu, 'export_env_map', False):
        env = EnvMapEffect()
        env.coefficient = getattr(inu, 'env_map_coef', 0.5)
        env.use_fb_alpha = getattr(inu, 'env_map_fb_alpha', False)
        tex_name = getattr(inu, 'env_map_tex', '')
        if tex_name:
            env.texture = DffTexture(name=tex_name)
        plugins['env_map'] = env

    # Specular
    if getattr(inu, 'export_specular', False):
        spec = SpecularMaterial()
        spec.level = getattr(inu, 'specular_level', 1.0)
        spec.name = getattr(inu, 'specular_texture', '')
        plugins['specular'] = spec

    # Reflection
    if getattr(inu, 'export_reflection', False):
        refl = ReflectionMaterial()
        refl.scale_x = getattr(inu, 'reflection_scale_x', 0.0)
        refl.scale_y = getattr(inu, 'reflection_scale_y', 0.0)
        refl.offset_x = getattr(inu, 'reflection_offset_x', 0.0)
        refl.offset_y = getattr(inu, 'reflection_offset_y', 0.0)
        refl.intensity = getattr(inu, 'reflection_intensity', 0.0)
        plugins['reflection'] = refl

    # Dual Texture / Blend Mode
    if getattr(inu, 'export_dual_tex', False):
        dt = DualTextureEffect()
        dt.src_blend = int(getattr(inu, 'dual_tex_src_blend', '5'))
        dt.dst_blend = int(getattr(inu, 'dual_tex_dst_blend', '6'))
        tex_name = getattr(inu, 'dual_tex_texture', '')
        if tex_name:
            dt.texture = DffTexture(name=tex_name)
        plugins['dual_texture'] = dt

    return plugins


def _build_material(mat) -> DffMaterial:
    """Convert a Blender material to DffMaterial."""
    dff_mat = DffMaterial()
    if mat is None:
        return dff_mat

    dff_mat.color = _read_base_color(mat)
    dff_mat.surface = _read_surface(mat)
    dff_mat.texture = _read_texture(mat)

    plugins = _read_material_plugins(mat)
    dff_mat.bump_map = plugins.get('bump_map')
    dff_mat.env_map = plugins.get('env_map')
    dff_mat.dual_texture = plugins.get('dual_texture')
    dff_mat.specular = plugins.get('specular')
    dff_mat.reflection = plugins.get('reflection')
    dff_mat.user_data = _load_user_data(mat)

    return dff_mat


# ── Export flags from DragonFF properties ────────────────────────

def _get_obj_export_flags(obj) -> dict:
    """Read export settings from obj.inu properties."""
    defaults = {
        'export_normals': True,
        'export_binsplit': True,
        'uv_map1': True,
        'uv_map2': True,
        'day_cols': True,
        'night_cols': True,
        'light': True,
        'modulate_color': True,
        'set_material_alpha': True,
        'light_beam_asi': False,
        'pipeline': 0,
    }
    inu = getattr(obj, 'inu', None)
    if not inu:
        return defaults

    result = {}
    for key, default in defaults.items():
        if key == 'pipeline':
            pipe_val = getattr(inu, 'pipeline', 'NONE')
            # If per-object pipeline is NONE, use scene-level setting
            if pipe_val == 'NONE' or pipe_val == '0':
                import bpy as _bpy
                scene_pipe = getattr(_bpy.context.scene, 'gtatools_export_pipeline', 'NONE')
                if scene_pipe != 'NONE':
                    try:
                        result['pipeline'] = int(scene_pipe, 0)
                    except ValueError:
                        result['pipeline'] = 0
                else:
                    result['pipeline'] = 0
            elif pipe_val == 'CUSTOM':
                custom = getattr(inu, 'custom_pipeline', '0')
                try:
                    result['pipeline'] = int(custom, 0)
                except ValueError:
                    result['pipeline'] = 0
            else:
                try:
                    result['pipeline'] = int(pipe_val, 0)
                except ValueError:
                    result['pipeline'] = 0
        else:
            result[key] = getattr(inu, key, default)

    return result


# ── Mesh processing ──────────────────────────────────────────────

def _needs_split(bm, vert, uv_layers, color_layers):
    """
    Check if a vertex needs to be split because its loops
    have different UV or color values.
    Returns list of loop groups that need separate vertices.
    """
    loops = list(vert.link_loops)
    if len(loops) <= 1:
        return None

    groups = []
    used = [False] * len(loops)

    for i, loop_a in enumerate(loops):
        if used[i]:
            continue
        group = [loop_a]
        used[i] = True

        for j in range(i + 1, len(loops)):
            if used[j]:
                continue
            loop_b = loops[j]
            same = True

            for uv_layer in uv_layers:
                if loop_a[uv_layer].uv != loop_b[uv_layer].uv:
                    same = False
                    break

            if same:
                for cl in color_layers:
                    if loop_a[cl] != loop_b[cl]:
                        same = False
                        break

            if same:
                group.append(loop_b)
                used[j] = True

        groups.append(group)

    if len(groups) <= 1:
        return None
    return groups


def _process_mesh(obj, clump: DffClump, frame_index: int):
    """
    Convert a Blender mesh object into DffGeometry + DffAtomic.
    """
    import mathutils

    flags = _get_obj_export_flags(obj)

    # Convert FLOAT_COLOR attributes to BYTE_COLOR before export (Itera Tools compatibility)
    import bpy
    orig_mesh = obj.data
    for ca in list(orig_mesh.color_attributes):
        ca_type = getattr(ca, 'data_type', None) or getattr(ca, 'type', None)
        if ca_type in ('FLOAT_COLOR', 'COLOR'):
            name = ca.name
            domain = ca.domain
            # Read float data
            float_data = [tuple(d.color) for d in ca.data]
            # Remove float attr, create byte attr
            orig_mesh.color_attributes.remove(ca)
            new_attr = orig_mesh.color_attributes.new(name=name, type='BYTE_COLOR', domain=domain)
            for i, color in enumerate(float_data):
                new_attr.data[i].color = color
            print(f"[DFF Export] Converted '{name}' FLOAT_COLOR → BYTE_COLOR")

    # Get evaluated mesh with modifiers applied (disable ARMATURE first)
    arm_mods = []
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE' and mod.show_viewport:
            mod.show_viewport = False
            arm_mods.append(mod)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

    # Re-enable ARMATURE modifiers
    for mod in arm_mods:
        mod.show_viewport = True

    # Read alpha per vertex directly from ORIGINAL mesh color attributes
    # (workaround: bmesh doesn't read alpha from byte color attrs in Blender 5.x)
    _mesh_alpha = [{}, {}]  # [day_alpha_by_vert, night_alpha_by_vert]
    orig_mesh = obj.data
    for ci, ca in enumerate(orig_mesh.color_attributes[:2]):
        for li, ld in enumerate(ca.data):
            vi = orig_mesh.loops[li].vertex_index
            a = int(ld.color[3] * 255)
            _mesh_alpha[ci][vi] = a
    print(f"[DFF Export] _mesh_alpha day samples: {list(_mesh_alpha[0].items())[:10]}")

    # Triangulate with bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    bm.faces.index_update()

    # Collect UV and color layers
    max_uv = 0
    if flags['uv_map1']:
        max_uv = 1
        if flags['uv_map2'] and len(bm.loops.layers.uv) > 1:
            # Only use 2nd UV if it actually has different data (not auto-generated)
            max_uv = 2
    max_uv = min(max_uv, len(bm.loops.layers.uv))
    # For skinned meshes: respect original UV count stored on object
    orig_uv_count = obj.get('dff_num_uv_layers', 0)
    if orig_uv_count > 0:
        max_uv = min(max_uv, orig_uv_count)

    uv_layers_bm = [bm.loops.layers.uv[i] for i in range(max_uv)]

    color_layers_bm = []
    if bm.loops.layers.color:
        color_layers_bm = list(bm.loops.layers.color)

    has_day = len(color_layers_bm) > 0 and flags['day_cols']
    has_night = len(color_layers_bm) > 1 and flags['night_cols']

    # ── Vertex splitting ──
    # Each vertex may need multiple copies if loops have different UV/color
    # We build a mapping: (vert_index, loop_group) → new_index

    num_original = len(bm.verts)

    # Vertex data lists (will grow as we split)
    positions = []
    normals_list = []
    # Track original bmesh vertex index for each output vertex (for skin data)
    split_origin = []

    for v in bm.verts:
        positions.append((v.co.x, v.co.y, v.co.z))
        normals_list.append((v.normal.x, v.normal.y, v.normal.z))
        split_origin.append(v.index)

    # Maps: BMLoop object → vertex index in output
    # Use loop objects (not loop.index) to avoid stale/duplicate index issues
    # after bmesh.ops.triangulate()
    loop_vert_map = {}

    for vert in bm.verts:
        groups = _needs_split(bm, vert, uv_layers_bm, color_layers_bm)
        if groups is None:
            # No split needed, all loops use original index
            for loop in vert.link_loops:
                loop_vert_map[loop] = vert.index
        else:
            # First group keeps original index
            for loop in groups[0]:
                loop_vert_map[loop] = vert.index

            # Additional groups get new vertices
            for group in groups[1:]:
                new_idx = len(positions)
                positions.append((vert.co.x, vert.co.y, vert.co.z))
                normals_list.append((vert.normal.x, vert.normal.y, vert.normal.z))
                split_origin.append(vert.index)
                for loop in group:
                    loop_vert_map[loop] = new_idx

    num_verts = len(positions)

    # ── UV layers ──
    uv_data = []
    for _ in range(max_uv):
        uv_data.append([TexCoords() for _ in range(num_verts)])

    # ── Vertex colors ──
    day_colors = [RGBA(255, 255, 255, 255)] * num_verts if has_day else []
    night_colors = [RGBA(0, 0, 0, 255)] * num_verts if has_night else []

    # ── Triangles ──
    triangles = []

    for face in bm.faces:
        face_loops = list(face.loops)
        # Get mapped vertex indices
        vi = [loop_vert_map[loop] for loop in face_loops]

        # Triangle (RenderWare winding order)
        triangles.append(Triangle(
            a=vi[0],
            b=vi[1],
            c=vi[2],
            material=face.material_index,
        ))

        # Fill UV and color data from loops
        for loop in face_loops:
            out_idx = loop_vert_map[loop]

            for layer_i, uv_layer in enumerate(uv_layers_bm):
                uv = loop[uv_layer].uv
                uv_data[layer_i][out_idx] = TexCoords(uv.x, 1.0 - uv.y)  # V flipped

            if has_day:
                c = loop[color_layers_bm[0]]
                alpha = _mesh_alpha[0].get(loop.vert.index, int(c[3]*255))
                day_colors[out_idx] = RGBA(
                    int(c[0]*255), int(c[1]*255), int(c[2]*255), alpha)

            if has_night:
                c = loop[color_layers_bm[1]]
                alpha = _mesh_alpha[1].get(loop.vert.index, int(c[3]*255))
                night_colors[out_idx] = RGBA(
                    int(c[0]*255), int(c[1]*255), int(c[2]*255), alpha)

    # ── Bounding sphere (from actual vertex positions, local space) ──
    if positions:
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        zs = [p[2] for p in positions]
        cx = (min(xs) + max(xs)) / 2.0
        cy = (min(ys) + max(ys)) / 2.0
        cz = (min(zs) + max(zs)) / 2.0
        radius = 0.0
        for p in positions:
            d = ((p[0] - cx)**2 + (p[1] - cy)**2 + (p[2] - cz)**2) ** 0.5
            if d > radius:
                radius = d
        center = mathutils.Vector((cx, cy, cz))
    else:
        center = mathutils.Vector((0, 0, 0))
        radius = 0.0

    # ── Materials ──
    materials = []
    if obj.data.materials:
        for mat in obj.data.materials:
            materials.append(_build_material(mat))
    else:
        materials.append(DffMaterial())

    # ── Build geometry ──
    geom = DffGeometry()
    geom.original_flags = obj.get('dff_geom_flags', 0)
    geom.vertices = positions
    geom.normals = normals_list
    geom.triangles = triangles
    geom.uv_layers = uv_data
    geom.prelit_colors = day_colors

    # Auto-detect vertex alpha: if any vertex has alpha < 255,
    # set material color alpha to 254 to enable alpha blending in GTA SA.
    # Can be disabled (Rockstar-style) via "Set Material Alpha" flag —
    # vanilla SA volumetric light beams (e.g. vgsecnstrct11.dff) use
    # material alpha 255 with only vertex alpha to drive transparency.
    if day_colors and flags.get('set_material_alpha', True):
        has_vertex_alpha = any(c.a < 255 for c in day_colors)
        if has_vertex_alpha:
            for m in materials:
                if m.color.a == 255:
                    m.color = RGBA(m.color.r, m.color.g, m.color.b, 254)

    # Light Beam marker for SA_Light.asi plugin.
    # When enabled, overrides the first material's color to the magic
    # marker RGBA(254,254,254,254). The plugin detects this at render
    # time and applies volumetric-beam render states (alpha test off,
    # proper alpha blend). Without the plugin, mesh renders as a plain
    # near-opaque object.
    #
    # Also: expand the bounding sphere to prevent frustum culling when
    # the player turns the camera. SA culls geometry whose bounding
    # sphere doesn't intersect the camera frustum — with a small offset
    # sphere, the mesh can disappear on slight camera rotation.
    # Light beams need to stay visible from any angle within range.
    if flags.get('light_beam_asi', False):
        if materials:
            materials[0].color = RGBA(254, 254, 254, 254)
        # Expand bounding sphere: center at origin + radius x5
        center = mathutils.Vector((0, 0, 0))
        radius = max(radius, 1.0) * 5.0

    geom.materials = materials
    geom.bounding_sphere = BoundingSphere(center.x, center.y, center.z, radius)
    geom.export_normals = flags['export_normals']
    geom.write_bin_mesh = flags['export_binsplit']
    geom.pipeline = flags['pipeline']
    geom.export_light = flags.get('light', True)
    geom.export_mod_color = flags.get('modulate_color', True)

    if has_night:
        geom.extra_colors = ExtraVertColors(colors=night_colors)

    # ── User Data PLG (from mesh custom property) ──
    geom.user_data = _load_user_data(obj.data)

    # ── Skin data (armature) ──
    armature_mod = None
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE' and mod.object:
            armature_mod = mod
            break

    if armature_mod:
        arm_obj = armature_mod.object
        bones = arm_obj.data.bones
        bone_names = [b.name for b in bones]

        skin = SkinData(num_bones=len(bones))

        # Bone matrices — use original if available (round-trip)
        import json
        orig_matrices = None
        raw = obj.get('dff_bone_matrices')
        if raw:
            try:
                orig_matrices = json.loads(raw)
            except Exception:
                pass

        if orig_matrices and len(orig_matrices) == len(bones):
            skin.bone_matrices = orig_matrices
            # Restore original skin header
            skin.num_used = obj.get('dff_skin_num_used', 0)
            skin.max_weights = obj.get('dff_skin_max_weights', 4)
            raw_bu = obj.get('dff_skin_bones_used')
            if raw_bu:
                try:
                    if isinstance(raw_bu, str):
                        skin.bones_used = json.loads(raw_bu)
                    else:
                        skin.bones_used = list(raw_bu)
                except Exception as e:
                    print(f"[DFF Export] bones_used error: {e}, raw_bu type={type(raw_bu)}")
            print(f"[DFF Export] Using original skin: num_used={skin.num_used}, bones_used={skin.bones_used[:5]}...")
        else:
            print(f"[DFF Export] Computing bone_matrices from Blender (orig={len(orig_matrices) if orig_matrices else 'None'}, bones={len(bones)})")
            for bone in bones:
                inv_mat = bone.matrix_local.inverted().transposed()
                mat = []
                for row in range(4):
                    mat.append([inv_mat[row][col] for col in range(4)])
                skin.bone_matrices.append(mat)

        # Vertex weights — build per-original-vertex first, then expand for splits
        bone_name_to_idx = {name: i for i, name in enumerate(bone_names)}
        orig_skin = []  # per original bmesh vertex: (indices, weights)
        for v_idx in range(num_original):
            vert = mesh.vertices[v_idx]
            bone_idx = [0, 0, 0, 0]
            bone_wgt = [0.0, 0.0, 0.0, 0.0]

            entries = []
            for g in vert.groups:
                vg = obj.vertex_groups[g.group]
                bi = bone_name_to_idx.get(vg.name)
                if bi is not None:
                    entries.append((bi, g.weight))

            entries.sort(key=lambda x: -x[1])
            for i, (bi, w) in enumerate(entries[:4]):
                bone_idx[i] = bi
                bone_wgt[i] = w

            # Normalize weights
            total = sum(bone_wgt)
            if total > 0:
                bone_wgt = [w / total for w in bone_wgt]

            # Kams: root bone (index 0) must be last in the 4-slot array
            for i in range(3):  # check slots 0,1,2
                if bone_idx[i] == 0 and bone_wgt[i] > 0:
                    bone_idx[i], bone_idx[3] = bone_idx[3], bone_idx[i]
                    bone_wgt[i], bone_wgt[3] = bone_wgt[3], bone_wgt[i]
                    break

            orig_skin.append((tuple(bone_idx), tuple(bone_wgt)))

        # Map to output vertices using split_origin (O(n))
        for v_idx in range(num_verts):
            orig_idx = split_origin[v_idx]
            if orig_idx < len(orig_skin):
                skin.bone_indices.append(orig_skin[orig_idx][0])
                skin.bone_weights.append(orig_skin[orig_idx][1])
            else:
                skin.bone_indices.append((0, 0, 0, 0))
                skin.bone_weights.append((0.0, 0.0, 0.0, 0.0))

        # Compute bones_used only if not restored from original
        # Kams: bones_used excludes bone 0 (root) and only counts non-zero weight entries
        if not skin.bones_used:
            used_set = set()
            for vi in range(len(skin.bone_indices)):
                indices = skin.bone_indices[vi]
                weights = skin.bone_weights[vi]
                for slot in range(4):
                    if indices[slot] != 0 and weights[slot] > 0:
                        used_set.add(indices[slot])
            skin.bones_used = sorted(used_set)
            skin.num_used = len(skin.bones_used)
            skin.max_weights = 4

        geom.skin = skin

    # ── Add to clump ──
    geom_idx = len(clump.geometries)
    clump.geometries.append(geom)
    clump.atomics.append(DffAtomic(
        frame_index=frame_index,
        geometry_index=geom_idx,
    ))

    # Debug summary
    print(f"[DFF Export] _process_mesh: verts={num_verts} tris={len(triangles)} "
          f"uv_layers={max_uv} has_skin={geom.skin is not None} "
          f"frame_index={frame_index} geom_flags=0x{geom._build_flags():X}")
    if geom.skin:
        skin = geom.skin
        print(f"[DFF Export]   SkinPLG: bones={skin.num_bones} used={skin.num_used} "
              f"max_w={skin.max_weights} bones_used={skin.bones_used[:10]} "
              f"vert_count={len(skin.bone_indices)} matrices={len(skin.bone_matrices)}")

    bm.free()
    eval_obj.to_mesh_clear()


# ── Frame building ───────────────────────────────────────────────

def _build_frame(obj, parent_index: int = -1) -> DffFrame:
    """Create a DffFrame from a Blender object.

    Uses stored original frame data for round-trip fidelity if available.
    """
    frame = DffFrame()
    frame.name = _strip_ext(obj.name)
    frame.parent = parent_index

    # Use original frame data if available (round-trip)
    orig_rot = obj.get('dff_frame_rot')
    orig_pos = obj.get('dff_frame_pos')
    orig_flags = obj.get('dff_frame_flags', 0)
    frame.write_name = obj.get('dff_frame_write_name', False)

    if orig_rot and orig_pos:
        frame.rotation = tuple(orig_rot)
        frame.position = tuple(orig_pos)
        frame.flags = orig_flags
    else:
        # Fallback: compute from Blender transform
        loc = obj.matrix_local.to_translation()
        frame.position = (loc.x, loc.y, loc.z)

        rot = obj.matrix_local.to_3x3().transposed()
        frame.rotation = (
            rot[0][0], rot[0][1], rot[0][2],
            rot[1][0], rot[1][1], rot[1][2],
            rot[2][0], rot[2][1], rot[2][2],
        )

    # User Data PLG (from object custom property)
    frame.user_data = _load_user_data(obj)

    return frame


# ── Armature export ──────────────────────────────────────────────

def _export_armature(arm_obj, clump: DffClump, parent_frame: int):
    """Export armature bones as frames with HAnimPLG.

    Uses stored original frame data from armature['dff_frame_data'] for round-trip fidelity.
    """
    import json
    bones = arm_obj.data.bones

    # Load original frame data if available
    orig_data = {}
    raw_json = arm_obj.get('dff_frame_data')
    if raw_json:
        try:
            orig_data = json.loads(raw_json)
            print(f"[DFF Export] Loaded dff_frame_data: {len(orig_data)} bones")
        except Exception as e:
            print(f"[DFF Export] Failed to load dff_frame_data: {e}")
    else:
        print(f"[DFF Export] No dff_frame_data on armature")

    for i, bone in enumerate(bones):
        frame = DffFrame()
        frame.name = bone.name

        # Use original frame data if available (round-trip)
        bone_id = str(bone.get('bone_id', 0))
        orig = orig_data.get(bone_id)

        if orig:
            frame.rotation = tuple(orig['rot'])
            frame.position = tuple(orig['pos'])
            frame.flags = orig.get('flags', 0)
            frame.write_name = bool(orig.get('write_name', False))
            if i < 3:
                print(f"[DFF Export] Bone '{bone.name}' write_name={frame.write_name} (raw={orig.get('write_name')})")
        else:
            # Fallback: compute from Blender bone (new model, not round-trip)
            frame.write_name = True
            # SA skinned: root bone frame flags = 0x20003, others = 0
            if i == 0:
                frame.flags = 0x20003
            if bone.parent:
                mat = bone.parent.matrix_local.inverted() @ bone.matrix_local
            else:
                mat = bone.matrix_local

            loc = mat.to_translation()
            rot = mat.to_3x3().transposed()

            frame.position = (loc.x, loc.y, loc.z)
            frame.rotation = (
                rot[0][0], rot[0][1], rot[0][2],
                rot[1][0], rot[1][1], rot[1][2],
                rot[2][0], rot[2][1], rot[2][2],
            )
        # Parent frame — use original if available
        if orig and 'parent' in orig:
            frame.parent = orig['parent']
        elif i == 0:
            frame.parent = parent_frame
        else:
            parent_bone = bone.parent
            if parent_bone:
                parent_bone_idx = list(bones).index(parent_bone)
                frame.parent = parent_frame + 1 + parent_bone_idx
            else:
                frame.parent = parent_frame

        # HAnimPLG
        bone_id_int = bone.get('bone_id', 0)
        bone_type = bone.get('bone_type', 0)
        bone_index = orig.get('index', i) if orig else bone.get('bone_index', i)

        if i == 0:
            # Root bone gets full bone list
            hanim = HAnimData(bone_id=bone_id_int)
            for j, b in enumerate(bones):
                b_id = str(b.get('bone_id', 0))
                b_orig = orig_data.get(b_id)
                hanim.bones.append(HAnimBone(
                    bone_id=b.get('bone_id', 0),
                    index=b_orig.get('index', j) if b_orig else b.get('bone_index', j),
                    bone_type=b.get('bone_type', 0),
                ))
            frame.hanim = hanim
        else:
            frame.hanim = HAnimData(bone_id=bone_id_int)

        clump.frames.append(frame)


# ── 2DFX export ──────────────────────────────────────────────────

def _collect_2dfx(objects) -> Extension2dfx:
    """Collect 2DFX effect entries from Empty objects with inu.type == '2DFX'."""
    ext = Extension2dfx()

    # Find mesh origin to make 2DFX coordinates relative to the model
    mesh_origin = None
    for obj in objects:
        if obj.type == 'MESH':
            mesh_origin = obj.location.copy()
            break

    for obj in objects:
        if obj.type != 'EMPTY':
            continue
        inu = getattr(obj, 'inu', None)
        if not inu or getattr(inu, 'type', '') != '2DFX':
            continue

        effect_type = getattr(inu, 'effect_2dfx', '')
        # 2DFX position relative to mesh origin
        if mesh_origin:
            loc = (obj.location.x - mesh_origin.x,
                   obj.location.y - mesh_origin.y,
                   obj.location.z - mesh_origin.z)
        else:
            loc = (obj.location.x, obj.location.y, obj.location.z)

        if effect_type == 'LIGHT':
            light = Light2dfx(loc=loc)
            inu = getattr(obj, 'inu', None)
            if inu and hasattr(inu, 'color_2dfx'):
                c = inu.color_2dfx
                light.color = RGBA(int(c[0] * 255), int(c[1] * 255),
                                   int(c[2] * 255), int(c[3] * 255))
            else:
                color_raw = obj.get('2dfx_color', [255, 255, 255, 255])
                light.color = RGBA(int(color_raw[0]), int(color_raw[1]),
                                   int(color_raw[2]), int(color_raw[3]))
            light.corona_far_clip = obj.get('2dfx_corona_far_clip', 0.0)
            light.pointlight_range = obj.get('2dfx_pointlight_range', 0.0)
            light.corona_size = obj.get('2dfx_corona_size', 0.0)
            light.shadow_size = obj.get('2dfx_shadow_size', 0.0)
            inu = getattr(obj, 'inu', None)
            light.corona_show_mode = int(inu.show_mode_2dfx) if inu else obj.get('2dfx_corona_show_mode', 0)
            light.corona_enable_reflection = obj.get('2dfx_corona_enable_reflection', 0)
            light.corona_flare_type = int(inu.flare_type_2dfx) if inu else obj.get('2dfx_corona_flare_type', 0)
            light.shadow_color_multiplier = obj.get('2dfx_shadow_color_multiplier', 0)
            light.flags1 = obj.get('2dfx_flags1', 0)
            light.corona_tex_name = inu.corona_tex_2dfx if inu else obj.get('2dfx_corona_tex', '')
            light.shadow_tex_name = inu.shadow_tex_2dfx if inu else obj.get('2dfx_shadow_tex', '')
            light.shadow_z_distance = obj.get('2dfx_shadow_z_distance', 0)
            light.flags2 = obj.get('2dfx_flags2', 0)
            look = obj.get('2dfx_look_direction')
            if look is not None:
                light.look_direction = (int(look[0]), int(look[1]), int(look[2]))
            ext.entries.append(light)

        elif effect_type == 'PARTICLE':
            particle = Particle2dfx(loc=loc)
            particle.effect_name = obj.get('2dfx_effect_name', '')
            ext.entries.append(particle)

        elif effect_type == 'PED_ATTRACTOR':
            ped = PedAttractor2dfx(loc=loc)
            ped.attractor_type = obj.get('2dfx_attractor_type', 0)
            rot = obj.get('2dfx_rotation_matrix', [1,0,0, 0,1,0, 0,0,1])
            ped.rotation_matrix = tuple(float(v) for v in rot)
            ped.external_script = obj.get('2dfx_external_script', '')
            ped.ped_existing_probability = obj.get('2dfx_ped_probability', 0)
            ext.entries.append(ped)

        elif effect_type == 'SUN_GLARE':
            ext.entries.append(SunGlare2dfx(loc=loc))

    return ext if ext.entries else None


# ── Hierarchy traversal ──────────────────────────────────────────

def _collect_frame_objects(objects):
    """Return list of (obj, parent_obj) in DFS order for DFF frame list.

    Includes MESH and EMPTY objects; excludes 2DFX Empties, Armatures, and
    NON-type objects. Roots are objects whose Blender parent is not in the set.
    """
    valid = []
    for obj in objects:
        inu = getattr(obj, 'inu', None)
        itype = getattr(inu, 'type', 'OBJ') if inu else 'OBJ'
        if itype == 'NON':
            continue
        if obj.type == 'MESH':
            valid.append(obj)
        elif obj.type == 'EMPTY' and itype != '2DFX':
            valid.append(obj)

    obj_set = set(valid)
    input_order = {o: i for i, o in enumerate(valid)}
    roots = sorted(
        (o for o in valid if o.parent is None or o.parent not in obj_set),
        key=lambda o: input_order[o],
    )

    ordered = []
    visited = set()

    def dfs(obj, parent_obj):
        if obj in visited:
            return
        visited.add(obj)
        ordered.append((obj, parent_obj))
        children = sorted(
            (c for c in obj.children if c in obj_set),
            key=lambda c: input_order[c],
        )
        for child in children:
            dfs(child, obj)

    for root in roots:
        dfs(root, None)

    return ordered


# ── Main export function ─────────────────────────────────────────

def export_dff(filepath: str, objects, version: int = GTA_SA_VERSION):
    """
    Export Blender objects as a DFF file.

    Args:
        filepath: Output .dff file path.
        objects: Iterable of Blender objects (MESH, EMPTY, ARMATURE).
        version: RenderWare version. Default GTA SA (0x36003).
    """
    clump = DffClump(version=version)

    # Separate objects by type
    mesh_objects = []
    armatures = set()

    for obj in objects:
        if obj.type == 'MESH':
            mesh_objects.append(obj)
            # Check for armature modifier
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE' and mod.object:
                    armatures.add(mod.object)

    has_skinned = bool(armatures)

    if has_skinned:
        # Skinned DFF (ped): flat one-mesh-one-frame, armature handles hierarchy
        for obj in mesh_objects:
            frame = _build_frame(obj)
            frame_idx = len(clump.frames)

            clump.frames.append(frame)

            arm_obj = None
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE' and mod.object:
                    arm_obj = mod.object
                    break

            if arm_obj:
                import base64
                raw_fl = arm_obj.get('dff_raw_frame_list')

                if raw_fl:
                    try:
                        clump.raw_frame_list = base64.b64decode(raw_fl)
                        clump.frames.clear()
                        print(f"[DFF Export] Using raw frame list ({len(clump.raw_frame_list)} bytes)")
                    except Exception:
                        _export_armature(arm_obj, clump, frame_idx)
                else:
                    _export_armature(arm_obj, clump, frame_idx)

            if clump.raw_frame_list:
                stored_fi = obj.get('dff_mesh_frame_index', -1)
                if stored_fi >= 0:
                    mesh_frame_idx = stored_fi
                else:
                    from struct import unpack_from
                    if len(clump.raw_frame_list) >= 16:
                        frame_count = unpack_from('<I', clump.raw_frame_list, 12)[0]
                        mesh_frame_idx = frame_count - 1
                        print(f"[DFF Export] Parsed frame_count={frame_count} from raw, mesh frame={mesh_frame_idx}")
                    else:
                        mesh_frame_idx = frame_idx
                print(f"[DFF Export] Skinned mesh: frame_index={mesh_frame_idx}")
            else:
                mesh_frame_idx = frame_idx

            _process_mesh(obj, clump, mesh_frame_idx)
    else:
        # Static DFF: walk Blender hierarchy, write Empty→dummy frames
        ordered = _collect_frame_objects(objects)
        obj_to_frame_idx = {}

        for obj, parent_obj in ordered:
            parent_idx = obj_to_frame_idx[parent_obj] if parent_obj is not None else -1
            frame = _build_frame(obj, parent_index=parent_idx)
            my_idx = len(clump.frames)
            clump.frames.append(frame)
            obj_to_frame_idx[obj] = my_idx

            if obj.type == 'MESH':
                _process_mesh(obj, clump, my_idx)

        print(f"[DFF Export] Static hierarchy: {len(clump.frames)} frames "
              f"({sum(1 for o, _ in ordered if o.type == 'EMPTY')} dummies)")

    # If no frames were created, add a default one
    if not clump.frames:
        clump.frames.append(DffFrame(name="root"))

    # Collect 2DFX effects — from selected objects AND from children of selected meshes
    all_objects = list(objects)
    for obj in objects:
        if obj.type == 'MESH':
            for child in obj.children:
                if child not in all_objects:
                    all_objects.append(child)
    ext_2dfx = _collect_2dfx(all_objects)
    if ext_2dfx and clump.geometries:
        clump.geometries[-1].ext_2dfx = ext_2dfx

        # Create RW Light frames for each Light2dfx entry (like Kam's 3DS Max Omni)
        light_count = 0
        for entry in ext_2dfx.entries:
            if isinstance(entry, Light2dfx):
                light_count += 1
                # Add frame for the light (child of root frame 0)
                light_frame = DffFrame(
                    name=f"Omni{light_count:03d}",
                    position=entry.loc,
                    parent=0,
                    flags=3,
                )
                frame_idx = len(clump.frames)
                clump.frames.append(light_frame)

                # Add RW Light linked to this frame
                color_r = entry.color.r / 255.0
                color_g = entry.color.g / 255.0
                color_b = entry.color.b / 255.0
                rw_light = DffLight(
                    frame_index=frame_idx,
                    radius=entry.pointlight_range * 10.0,
                    color=(color_r, color_g, color_b),
                )
                clump.lights.append(rw_light)

    # Embed collision data in DFF (CHUNK_COLLISION_MODEL)
    col_objects = [obj for obj in objects if obj.type == 'MESH'
                   and getattr(getattr(obj, 'inu', None), 'type', '') in ('COL', 'SHA')]
    if col_objects:
        from .col_export import export_col_bytes
        model_name = os.path.splitext(os.path.basename(filepath))[0]
        clump.collision_data = export_col_bytes(col_objects, version=3, model_name=model_name)

    write_dff_file(filepath, clump)
