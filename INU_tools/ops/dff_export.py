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
    BumpMapEffect, EnvMapEffect, SpecularMaterial, ReflectionMaterial,
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
            return RGBA(int(c[0]*255), int(c[1]*255), int(c[2]*255), int(c[3]*255))
    if hasattr(mat, 'diffuse_color'):
        c = mat.diffuse_color
        return RGBA(int(c[0]*255), int(c[1]*255), int(c[2]*255), 255)
    return RGBA()


def _read_texture(mat) -> DffTexture:
    """Read texture name from Principled BSDF image node."""
    principled = _get_principled(mat)
    if not principled:
        return None

    bc_input = principled.inputs.get('Base Color')
    if not bc_input or not bc_input.is_linked:
        return None

    source_node = bc_input.links[0].from_node
    if source_node.type != 'TEX_IMAGE' or not source_node.image:
        return None

    img = source_node.image
    # Prefer node label if it's a reasonable name
    name = source_node.label if source_node.label else img.name
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
        'pipeline': 0,
    }
    inu = getattr(obj, 'inu', None)
    if not inu:
        return defaults

    result = {}
    for key, default in defaults.items():
        if key == 'pipeline':
            pipe_val = getattr(inu, 'pipeline', 'NONE')
            if pipe_val == 'NONE' or pipe_val == '0':
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

    # Get evaluated mesh with modifiers applied (except ARMATURE)
    import bpy
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)

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
            max_uv = 2
    max_uv = min(max_uv, len(bm.loops.layers.uv))

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

    for v in bm.verts:
        positions.append((v.co.x, v.co.y, v.co.z))
        normals_list.append((v.normal.x, v.normal.y, v.normal.z))

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
                day_colors[out_idx] = RGBA(
                    int(c[0]*255), int(c[1]*255), int(c[2]*255), int(c[3]*255))

            if has_night:
                c = loop[color_layers_bm[1]]
                night_colors[out_idx] = RGBA(
                    int(c[0]*255), int(c[1]*255), int(c[2]*255), int(c[3]*255))

    # ── Bounding sphere ──
    bb = obj.bound_box
    center = mathutils.Vector((0, 0, 0))
    for corner in bb:
        center += mathutils.Vector(corner)
    center /= 8.0
    center = obj.matrix_world @ center
    radius = 1.732 * max(obj.dimensions) / 2.0

    # ── Materials ──
    materials = []
    if obj.data.materials:
        for mat in obj.data.materials:
            materials.append(_build_material(mat))
    else:
        materials.append(DffMaterial())

    # ── Build geometry ──
    geom = DffGeometry()
    geom.vertices = positions
    geom.normals = normals_list
    geom.triangles = triangles
    geom.uv_layers = uv_data
    geom.prelit_colors = day_colors
    geom.materials = materials
    geom.bounding_sphere = BoundingSphere(center.x, center.y, center.z, radius)
    geom.export_normals = flags['export_normals']
    geom.write_bin_mesh = flags['export_binsplit']
    geom.pipeline = flags['pipeline']

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

        # Bone matrices (inverse bind matrices)
        for bone in bones:
            inv_mat = bone.matrix_local.inverted().transposed()
            flat = []
            for row in range(4):
                for col in range(4):
                    flat.append(inv_mat[row][col])
            skin.bone_matrices.append(flat)

        # Vertex weights
        for v_idx in range(num_original):
            vert = mesh.vertices[v_idx]
            bone_idx = [0, 0, 0, 0]
            bone_wgt = [0.0, 0.0, 0.0, 0.0]

            entries = []
            for g in vert.groups:
                vg = obj.vertex_groups[g.group]
                if vg.name in bone_names:
                    bi = bone_names.index(vg.name)
                    entries.append((bi, g.weight))

            entries.sort(key=lambda x: -x[1])
            for i, (bi, w) in enumerate(entries[:4]):
                bone_idx[i] = bi
                bone_wgt[i] = w

            # Normalize weights
            total = sum(bone_wgt)
            if total > 0:
                bone_wgt = [w / total for w in bone_wgt]

            skin.bone_indices.append(tuple(bone_idx))
            skin.bone_weights.append(tuple(bone_wgt))

        # For split vertices, copy from original
        for v_idx in range(num_original, num_verts):
            # Find original vertex this was cloned from
            # The position matches, so find it
            pos = positions[v_idx]
            for orig_idx in range(num_original):
                if positions[orig_idx] == pos:
                    skin.bone_indices.append(skin.bone_indices[orig_idx])
                    skin.bone_weights.append(skin.bone_weights[orig_idx])
                    break
            else:
                skin.bone_indices.append((0, 0, 0, 0))
                skin.bone_weights.append((0.0, 0.0, 0.0, 0.0))

        geom.skin = skin

    # ── Add to clump ──
    geom_idx = len(clump.geometries)
    clump.geometries.append(geom)
    clump.atomics.append(DffAtomic(
        frame_index=frame_index,
        geometry_index=geom_idx,
    ))

    bm.free()
    eval_obj.to_mesh_clear()


# ── Frame building ───────────────────────────────────────────────

def _build_frame(obj, parent_index: int = -1) -> DffFrame:
    """Create a DffFrame from a Blender object."""
    frame = DffFrame()
    frame.name = _strip_ext(obj.name)
    frame.parent = parent_index

    # Local transform
    loc = obj.matrix_local.to_translation()
    frame.position = (loc.x, loc.y, loc.z)

    # 3x3 rotation matrix (transposed for RenderWare)
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
    """Export armature bones as frames with HAnimPLG."""
    bones = arm_obj.data.bones

    for i, bone in enumerate(bones):
        frame = DffFrame()
        frame.name = bone.name

        # Bone transform
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

        # Parent frame
        if i == 0:
            frame.parent = parent_frame
        else:
            parent_bone = bone.parent
            if parent_bone:
                parent_bone_idx = list(bones).index(parent_bone)
                frame.parent = parent_frame + 1 + parent_bone_idx
            else:
                frame.parent = parent_frame

        # HAnimPLG
        bone_id = bone.get('bone_id', 0)
        bone_type = bone.get('type', 0)

        if i == 0:
            # Root bone gets full bone list
            hanim = HAnimData(bone_id=bone_id)
            for j, b in enumerate(bones):
                hanim.bones.append(HAnimBone(
                    bone_id=b.get('bone_id', 0),
                    index=j,
                    bone_type=b.get('type', 0),
                ))
            frame.hanim = hanim
        else:
            frame.hanim = HAnimData(bone_id=bone_id)

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

    # Build frames and geometries
    for obj in mesh_objects:
        # Create frame for this object
        frame = _build_frame(obj)
        frame_idx = len(clump.frames)
        clump.frames.append(frame)

        # Check if object has armature
        arm_obj = None
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object:
                arm_obj = mod.object
                break

        if arm_obj:
            _export_armature(arm_obj, clump, frame_idx)

        # Process mesh
        _process_mesh(obj, clump, frame_idx)

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

    write_dff_file(filepath, clump)
