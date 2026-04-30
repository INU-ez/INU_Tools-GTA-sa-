# INU_tools.core.dff
# GTA SA DFF (RenderWare Clump) reader and writer.
# Pure Python, no Blender dependency.
#
# Written from scratch based on public RenderWare format specifications:
#   https://gtamods.com/wiki/RenderWare_binary_stream_file
#   https://gtamods.com/wiki/DFF
#
# RenderWare Binary Stream uses a chunked format:
#   Each chunk = 12-byte header (type:u32, size:u32, version:u32) + data

from __future__ import annotations

from struct import pack, unpack_from, calcsize
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .rwbinary import BinaryReader


# ── RenderWare chunk type IDs (public constants) ─────────────────

CHUNK_STRUCT           = 1
CHUNK_STRING           = 2
CHUNK_EXTENSION        = 3
CHUNK_TEXTURE          = 6
CHUNK_MATERIAL         = 7
CHUNK_MATERIAL_LIST    = 8
CHUNK_FRAME_LIST       = 14
CHUNK_GEOMETRY         = 15
CHUNK_CLUMP            = 16
CHUNK_LIGHT            = 18
CHUNK_ATOMIC           = 20
CHUNK_GEOMETRY_LIST    = 26
CHUNK_ANIM_ANIMATION   = 27
CHUNK_UV_ANIM_DICT     = 43
CHUNK_SKIN_PLG         = 278
CHUNK_HANIM_PLG        = 286
CHUNK_USERDATA_PLG     = 287
CHUNK_MATFX_PLG        = 288
CHUNK_UV_ANIM_PLG      = 309
CHUNK_BIN_MESH_PLG     = 1294
CHUNK_PIPELINE_SET     = 0x0253F2F3
CHUNK_SPECULAR_MAT     = 0x0253F2F6
CHUNK_2DFXPLG          = 0x0253F2F8
CHUNK_EXTRA_COLORS     = 0x0253F2F9
CHUNK_COLLISION_MODEL  = 0x0253F2FA
CHUNK_REFLECTION_MAT   = 0x0253F2FC
CHUNK_BREAKABLE        = 0x0253F2FD
CHUNK_FRAME_NAME       = 0x0253F2FE

# ── Geometry flags (public RenderWare constants) ─────────────────

GEOM_POSITIONS   = 0x02
GEOM_TEXTURED    = 0x04
GEOM_PRELIT      = 0x08
GEOM_NORMALS     = 0x10
GEOM_LIGHT       = 0x20
GEOM_MOD_COLOR   = 0x40
GEOM_TEXTURED2   = 0x80
GEOM_NATIVE      = 0x01000000

# ── GTA SA default version ───────────────────────────────────────

GTA_SA_VERSION = 0x36003
GTA_SA_BUILD   = 0xFFFF


# ── Library ID encoding (RenderWare spec) ────────────────────────

def make_library_id(version: int, build: int = 0xFFFF) -> int:
    """Encode RW version + build into a 32-bit library ID."""
    if version <= 0x31000:
        return version >> 8
    return (
        ((version - 0x30000 & 0x3FF00) << 14) |
        ((version & 0x3F) << 16) |
        (build & 0xFFFF)
    )


# ── Chunk builder ────────────────────────────────────────────────

def _chunk(chunk_type: int, data: bytes, lib_id: int) -> bytes:
    """Wrap data in a RenderWare chunk with 12-byte header."""
    return pack('<III', chunk_type, len(data), lib_id) + data


def _pad_string(s: str) -> bytes:
    """Encode string with null terminator, padded to 4-byte boundary."""
    raw = s.encode('ascii', errors='replace') + b'\x00'
    pad_len = (4 - len(raw) % 4) % 4
    return raw + b'\x00' * pad_len


# ── Data structures ──────────────────────────────────────────────

@dataclass
class RGBA:
    r: int = 255
    g: int = 255
    b: int = 255
    a: int = 255


@dataclass
class TexCoords:
    u: float = 0.0
    v: float = 0.0


@dataclass
class DffTexture:
    """Material texture reference."""
    name: str = ""
    mask: str = ""
    filters: int = 0x1106  # default filter mode

    def to_bytes(self, lib_id: int) -> bytes:
        struct_data = pack('<H2x', self.filters)
        body = _chunk(CHUNK_STRUCT, struct_data, lib_id)
        body += _chunk(CHUNK_STRING, _pad_string(self.name), lib_id)
        body += _chunk(CHUNK_STRING, _pad_string(self.mask), lib_id)
        body += _chunk(CHUNK_EXTENSION, b'', lib_id)
        return _chunk(CHUNK_TEXTURE, body, lib_id)


@dataclass
class SurfaceProperties:
    ambient: float = 1.0
    specular: float = 0.0
    diffuse: float = 1.0


@dataclass
class BumpMapEffect:
    intensity: float = 1.0
    bump_texture: Optional[DffTexture] = None
    height_texture: Optional[DffTexture] = None


@dataclass
class EnvMapEffect:
    coefficient: float = 0.5
    use_fb_alpha: bool = False
    texture: Optional[DffTexture] = None


@dataclass
class SpecularMaterial:
    level: float = 1.0
    name: str = ""


@dataclass
class ReflectionMaterial:
    scale_x: float = 0.0
    scale_y: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    intensity: float = 0.0


@dataclass
class DualTextureEffect:
    """Dual Texture (MatFX type 4) — src/dst blend modes."""
    src_blend: int = 5   # SRCALPHA
    dst_blend: int = 6   # INVSRCALPHA
    texture: Optional[DffTexture] = None


# ── UV Animation ─────────────────────────────────────────────────
#
# RenderWare UV anim format (written as CHUNK_UV_ANIM_DICT 0x2B at clump
# extension, referenced from materials via CHUNK_UV_ANIM_PLG 0x135).
# Keyframes are 36 bytes each: i32 prev_offset, f32 time, 6×f32 uv matrix
# (scale_u, scale_v, shear_u, shear_v, trans_u, trans_v).

UV_ANIM_KEYFRAME_SIZE = 32  # bytes — i32 prev_offset + f32 time + 6×f32 uv matrix


@dataclass
class UVAnimKeyframe:
    time: float = 0.0
    scale_u: float = 1.0
    scale_v: float = 1.0
    shear_u: float = 0.0
    shear_v: float = 0.0
    trans_u: float = 0.0
    trans_v: float = 0.0


@dataclass
class UVAnim:
    """One named UV animation with up to 8-channel node mapping."""
    name: str = ""
    type_id: int = 0x1C0
    # nodeToUv[0]=1 ties the animation to the first material texture slot;
    # all zeros would leave the anim inert in the game engine.
    node_to_uv: tuple = (1, 0, 0, 0, 0, 0, 0, 0)
    duration: float = 1.0
    keyframes: list = field(default_factory=list)   # list[UVAnimKeyframe]

    def to_bytes(self, lib_id: int) -> bytes:
        n = len(self.keyframes)
        # STRUCT payload
        data = pack('<IIIIf',
                    0x100,           # version
                    self.type_id,
                    n,
                    0,               # flags
                    self.duration)
        # name[32]
        raw = self.name.encode('ascii', errors='replace')[:31]
        data += raw + b'\x00' * (32 - len(raw))
        # node_to_uv[8]
        mapping = list(self.node_to_uv) + [0] * (8 - len(self.node_to_uv))
        data += pack('<8i', *mapping[:8])
        # keyframes
        for i, kf in enumerate(self.keyframes):
            prev = (i - 1) * UV_ANIM_KEYFRAME_SIZE if i > 0 else 0
            data += pack('<if6f',
                         prev, kf.time,
                         kf.scale_u, kf.scale_v,
                         kf.shear_u, kf.shear_v,
                         kf.trans_u, kf.trans_v)
        struct_chunk = _chunk(CHUNK_STRUCT, data, lib_id)
        # The UV anim chunk has its own 12-byte wrapper inside the dict
        return _chunk(CHUNK_ANIM_ANIMATION, struct_chunk, lib_id)


@dataclass
class UVAnimDict:
    """Clump-level dictionary of UV animations (chunk 0x2B)."""
    anims: list = field(default_factory=list)  # list[UVAnim]

    def to_bytes(self, lib_id: int) -> bytes:
        body = _chunk(CHUNK_STRUCT, pack('<I', len(self.anims)), lib_id)
        for a in self.anims:
            body += a.to_bytes(lib_id)
        return _chunk(CHUNK_UV_ANIM_DICT, body, lib_id)


def _uv_anim_plg_bytes(anim_names: list, lib_id: int) -> bytes:
    """Build UVAnim PLG chunk (0x135) referencing up to 8 anim names."""
    if not anim_names:
        return b''
    names = list(anim_names)[:8]
    mask = 0
    for i in range(len(names)):
        mask |= 1 << i
    data = pack('<4I', 0x100, mask, 0, 0)   # version, mask, unknown, unknown
    for i in range(8):
        name = names[i] if i < len(names) else ''
        raw = name.encode('ascii', errors='replace')[:31]
        data += raw + b'\x00' * (32 - len(raw))
    return _chunk(CHUNK_UV_ANIM_PLG, data, lib_id)


def _read_uv_anim(data: bytes, offset: int, size: int) -> 'UVAnim':
    """Parse one UVAnim (CHUNK_ANIM_ANIMATION 0x1B) → ``UVAnim``.

    The inverse of ``UVAnim.to_bytes``. Expects the outer 0x1B wrapper
    was already consumed — *offset* points at the inner STRUCT chunk.

    Layout (matches the writer):
        STRUCT:
            u32 version, u32 type_id, u32 num_keyframes, u32 flags,
            f32 duration,
            char name[32],
            i32 node_to_uv[8],
            keyframe[num_keyframes]  — 32 bytes each
    """
    import struct as _s
    end = offset + size
    anim = UVAnim()

    # Inner STRUCT header
    if offset + 12 > end:
        return anim
    struct_ident, struct_size = _s.unpack_from('<II', data, offset)[:2]
    if struct_ident != CHUNK_STRUCT:
        return anim
    offset += 12  # ident + size + libid

    # STRUCT body
    if offset + 20 > end:
        return anim
    _version, type_id, num_kf, _flags, duration = _s.unpack_from(
        '<IIIIf', data, offset)
    anim.type_id = type_id
    anim.duration = duration
    offset += 20

    # Name (32 bytes, null-padded)
    if offset + 32 > end:
        return anim
    raw_name = data[offset:offset + 32]
    anim.name = raw_name.split(b'\x00', 1)[0].decode('ascii', errors='replace')
    offset += 32

    # node_to_uv[8]
    if offset + 32 > end:
        return anim
    anim.node_to_uv = tuple(_s.unpack_from('<8i', data, offset))
    offset += 32

    # Keyframes — 32 bytes each
    for _i in range(num_kf):
        if offset + UV_ANIM_KEYFRAME_SIZE > end:
            break
        _prev, t, su, sv, hu, hv, tu, tv = _s.unpack_from(
            '<if6f', data, offset)
        anim.keyframes.append(UVAnimKeyframe(
            time=t,
            scale_u=su, scale_v=sv,
            shear_u=hu, shear_v=hv,
            trans_u=tu, trans_v=tv,
        ))
        offset += UV_ANIM_KEYFRAME_SIZE

    return anim


def _read_uv_anim_dict(data: bytes, offset: int, size: int) -> 'UVAnimDict':
    """Parse a CHUNK_UV_ANIM_DICT (0x2B) body → ``UVAnimDict``.

    Inverse of ``UVAnimDict.to_bytes``. Expects *offset* points at
    the inner STRUCT (count) chunk, *size* is the 0x2B body length.
    """
    import struct as _s
    end = offset + size
    result = UVAnimDict()

    if offset + 12 > end:
        return result
    struct_ident, struct_size = _s.unpack_from('<II', data, offset)[:2]
    if struct_ident != CHUNK_STRUCT:
        return result
    offset += 12
    if offset + 4 > end:
        return result
    count = _s.unpack_from('<I', data, offset)[0]
    offset += 4

    # Each animation is wrapped in a 0x1B chunk
    for _i in range(count):
        if offset + 12 > end:
            break
        ch_ident, ch_size = _s.unpack_from('<II', data, offset)[:2]
        inner_start = offset + 12
        if ch_ident == CHUNK_ANIM_ANIMATION:
            result.anims.append(
                _read_uv_anim(data, inner_start, ch_size))
        offset = inner_start + ch_size

    return result


def _read_uv_anim_plg(data: bytes, offset: int, size: int) -> list:
    """Parse a CHUNK_UV_ANIM_PLG (0x135) body → list[str] of referenced
    animation names (length ≤ 8, with empty strings filtered out).

    Layout (matches ``_uv_anim_plg_bytes``): u32 version, u32 mask,
    u32 unknown, u32 unknown, then 8 × name[32].
    """
    import struct as _s
    end = offset + size
    if offset + 16 > end:
        return []
    _version, mask = _s.unpack_from('<II', data, offset)[:2]
    offset += 16  # version + mask + 2×unknown

    names = []
    for i in range(8):
        if offset + 32 > end:
            break
        raw = data[offset:offset + 32]
        name = raw.split(b'\x00', 1)[0].decode('ascii', errors='replace')
        offset += 32
        # Only include slots explicitly flagged by the mask AND with
        # a non-empty name — anims.txd uses the mask to signal which
        # slots are active; padded null slots are skipped on read.
        if (mask & (1 << i)) and name:
            names.append(name)
    return names


@dataclass
class DffMaterial:
    """Single material with optional plugins."""
    color: RGBA = field(default_factory=RGBA)
    surface: SurfaceProperties = field(default_factory=SurfaceProperties)
    texture: Optional[DffTexture] = None
    bump_map: Optional[BumpMapEffect] = None
    env_map: Optional[EnvMapEffect] = None
    dual_texture: Optional[DualTextureEffect] = None
    specular: Optional[SpecularMaterial] = None
    reflection: Optional[ReflectionMaterial] = None
    user_data: Optional[UserData] = None
    uv_anim_names: list = field(default_factory=list)  # names in clump UV anim dict

    def _matfx_bytes(self, lib_id: int) -> bytes:
        """Build Material Effects PLG content."""
        has_bump = self.bump_map is not None
        has_env = self.env_map is not None
        has_dual = self.dual_texture is not None

        if has_bump and has_env:
            effect_type = 3
        elif has_bump:
            effect_type = 1
        elif has_env:
            effect_type = 2
        elif has_dual:
            effect_type = 4
        else:
            return b''

        data = pack('<I', effect_type)

        if has_bump:
            bm = self.bump_map
            data += pack('<I', 1)  # bump effect marker
            data += pack('<f', bm.intensity)
            has_bump_tex = bm.bump_texture is not None
            data += pack('<I', 1 if has_bump_tex else 0)
            if has_bump_tex:
                data += bm.bump_texture.to_bytes(lib_id)
            has_height = bm.height_texture is not None
            data += pack('<I', 1 if has_height else 0)
            if has_height:
                data += bm.height_texture.to_bytes(lib_id)

        if has_env:
            em = self.env_map
            data += pack('<I', 2)  # env effect marker
            data += pack('<f', em.coefficient)
            data += pack('<I', 1 if em.use_fb_alpha else 0)
            has_tex = em.texture is not None
            data += pack('<I', 1 if has_tex else 0)
            if has_tex:
                data += em.texture.to_bytes(lib_id)

        if has_dual:
            dt = self.dual_texture
            data += pack('<I', 4)  # dual texture effect marker
            data += pack('<II', dt.src_blend, dt.dst_blend)
            has_tex = dt.texture is not None
            data += pack('<I', 1 if has_tex else 0)
            if has_tex:
                data += dt.texture.to_bytes(lib_id)

        if effect_type not in (3, 6):
            data += pack('<I', 0)  # terminator

        return _chunk(CHUNK_MATFX_PLG, data, lib_id)

    def to_bytes(self, lib_id: int, rw_version: int) -> bytes:
        """Serialize material to RenderWare binary."""
        # Struct header
        has_tex = 1 if self.texture else 0
        struct_data = pack('<4x')  # padding
        struct_data += pack('<4B', self.color.r, self.color.g, self.color.b, self.color.a)
        struct_data += pack('<II', 1, has_tex)  # unused=1, textured flag
        if rw_version > 0x30400:
            struct_data += pack('<3f', self.surface.ambient, self.surface.specular, self.surface.diffuse)

        body = _chunk(CHUNK_STRUCT, struct_data, lib_id)

        # Texture
        if self.texture:
            body += self.texture.to_bytes(lib_id)

        # Extensions
        ext_data = b''
        ext_data += self._matfx_bytes(lib_id)

        if self.specular:
            spec_data = pack('<f', self.specular.level)
            spec_name = self.specular.name.encode('ascii', errors='replace')[:24]
            spec_data += spec_name + b'\x00' * (24 - len(spec_name))
            ext_data += _chunk(CHUNK_SPECULAR_MAT, spec_data, lib_id)

        if self.reflection:
            r = self.reflection
            refl_data = pack('<5f4x', r.scale_x, r.scale_y, r.offset_x, r.offset_y, r.intensity)
            ext_data += _chunk(CHUNK_REFLECTION_MAT, refl_data, lib_id)

        if self.user_data and self.user_data.sections:
            ext_data += self.user_data.to_bytes(lib_id)

        if self.uv_anim_names:
            ext_data += _uv_anim_plg_bytes(self.uv_anim_names, lib_id)

        body += _chunk(CHUNK_EXTENSION, ext_data, lib_id)
        return _chunk(CHUNK_MATERIAL, body, lib_id)


@dataclass
class Triangle:
    """Face triangle with vertex indices and material index."""
    a: int = 0
    b: int = 0
    c: int = 0
    material: int = 0


@dataclass
class BoundingSphere:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    radius: float = 0.0


@dataclass
class UserDataSection:
    """Single named section of user data (int, float, or string array)."""
    name: str = ""
    data_type: int = 0   # 0=NA, 1=int, 2=float, 3=string
    data: list = field(default_factory=list)

USERDATA_NA     = 0
USERDATA_INT    = 1
USERDATA_FLOAT  = 2
USERDATA_STRING = 3


@dataclass
class UserData:
    """User Data PLG — arbitrary named data on geometry/frame/material."""
    sections: list = field(default_factory=list)  # list[UserDataSection]

    def to_bytes(self, lib_id: int) -> bytes:
        """Serialize to RenderWare User Data PLG chunk."""
        data = pack('<I', len(self.sections))
        for sec in self.sections:
            # Name
            name_bytes = sec.name.encode('ascii', errors='replace')
            data += pack('<I', len(name_bytes))
            data += name_bytes

            # Determine type from data if not set
            dtype = sec.data_type
            count = len(sec.data)
            data += pack('<II', dtype, count)

            if dtype == USERDATA_INT:
                for v in sec.data:
                    data += pack('<I', v)
            elif dtype == USERDATA_FLOAT:
                for v in sec.data:
                    data += pack('<f', v)
            elif dtype == USERDATA_STRING:
                for s in sec.data:
                    s_bytes = s.encode('ascii', errors='replace')
                    data += pack('<I', len(s_bytes))
                    data += s_bytes

        return _chunk(CHUNK_USERDATA_PLG, data, lib_id)


@dataclass
class ExtraVertColors:
    """Night vertex colors (second color layer)."""
    colors: list = field(default_factory=list)  # list[RGBA]


@dataclass
class BreakableData:
    """Breakable Objects extension (chunk 0x253F2FD) — marks a mesh as
    destructible by the physics engine. The numbers are pre-allocated
    buffers used by the game to hold the broken copy; the defaults
    mirror what Kam's `brakableobjects.ms` writes.
    """
    vertices_alloc: int = 100
    faces_alloc: int = 200
    materials_alloc: int = 1
    uvs_alloc: int = 100
    offset: tuple = (0.0, 0.0, 0.0)   # break-force offset
    force: float = 1.0                # break-force magnitude

    def to_bytes(self, lib_id: int) -> bytes:
        data = pack('<4I', self.vertices_alloc, self.faces_alloc,
                          self.materials_alloc, self.uvs_alloc)
        data += pack('<3ff',
                     self.offset[0], self.offset[1], self.offset[2],
                     self.force)
        return _chunk(CHUNK_BREAKABLE, data, lib_id)


# ── 2DFX Effect structures ──────────────────────────────────────

@dataclass
class Light2dfx:
    """Light effect (street lights, neon signs, etc.)."""
    effect_id: int = 0
    loc: tuple = (0.0, 0.0, 0.0)
    color: RGBA = field(default_factory=RGBA)
    corona_far_clip: float = 0.0
    pointlight_range: float = 0.0
    corona_size: float = 0.0
    shadow_size: float = 0.0
    corona_show_mode: int = 0
    corona_enable_reflection: int = 0
    corona_flare_type: int = 0
    shadow_color_multiplier: int = 0
    flags1: int = 0
    corona_tex_name: str = ""
    shadow_tex_name: str = ""
    shadow_z_distance: int = 0
    flags2: int = 0
    look_direction: Optional[tuple] = None  # (x, y, z) bytes or None


@dataclass
class Particle2dfx:
    """Particle effect (smoke, fire, etc.)."""
    effect_id: int = 1
    loc: tuple = (0.0, 0.0, 0.0)
    effect_name: str = ""


@dataclass
class PedAttractor2dfx:
    """Ped attractor (ATM, bench, bus stop, etc.)."""
    effect_id: int = 3
    loc: tuple = (0.0, 0.0, 0.0)
    attractor_type: int = 0
    rotation_matrix: tuple = (1,0,0, 0,1,0, 0,0,1)  # 3x3 as 9 floats
    external_script: str = ""
    ped_existing_probability: int = 0


@dataclass
class SunGlare2dfx:
    """Sun glare effect on surfaces."""
    effect_id: int = 4
    loc: tuple = (0.0, 0.0, 0.0)


@dataclass
class Extension2dfx:
    """Container for all 2DFX effect entries."""
    entries: list = field(default_factory=list)  # list of Light2dfx/Particle2dfx/etc.

    def to_bytes(self, lib_id: int) -> bytes:
        """Serialize 2DFX plugin to RenderWare chunk."""
        if not self.entries:
            return b''

        data = pack('<I', len(self.entries))

        for entry in self.entries:
            # Location (3 floats) + entry_type (u32) + entry_size (u32)
            entry_data = _write_2dfx_entry(entry)
            data += pack('<3f', *entry.loc)
            data += pack('<II', entry.effect_id, len(entry_data))
            data += entry_data

        return _chunk(CHUNK_2DFXPLG, data, lib_id)


@dataclass
class SkinData:
    """Bone skinning data for a geometry."""
    num_bones: int = 0
    num_used: int = 0              # Number of used bones
    max_weights: int = 4           # Max weights per vertex
    bones_used: list = field(default_factory=list)  # List of used bone indices
    bone_indices: list = field(default_factory=list)   # per-vertex: list[(b0,b1,b2,b3)]
    bone_weights: list = field(default_factory=list)    # per-vertex: list[(w0,w1,w2,w3)]
    bone_matrices: list = field(default_factory=list)   # per-bone: list[4x4 floats]

    def to_bytes(self, lib_id: int) -> bytes:
        oldver = (self.num_used == 0)
        data = pack('<3Bx', self.num_bones, self.num_used, self.max_weights)

        # bones_used array
        for bu in self.bones_used:
            data += pack('<B', bu)

        for indices in self.bone_indices:
            data += pack('<4B', *indices)

        for weights in self.bone_weights:
            data += pack('<4f', *weights)

        for matrix in self.bone_matrices:
            if oldver:
                data += pack('<4x')  # 0xDEADDEAD marker in old format
            flat = matrix[0] + matrix[1] + matrix[2] + matrix[3]
            data += pack('<16f', *flat)

        # SA version: 3 trailing zero floats (skin bounds/padding)
        if not oldver:
            data += pack('<3f', 0.0, 0.0, 0.0)

        return _chunk(CHUNK_SKIN_PLG, data, lib_id)


@dataclass
class HAnimBone:
    bone_id: int = 0
    index: int = 0
    bone_type: int = 0


@dataclass
class HAnimData:
    """Hierarchical animation data for a frame."""
    version: int = 0x100
    bone_id: int = 0
    bones: list = field(default_factory=list)  # list[HAnimBone], only on root

    def to_bytes(self, lib_id: int) -> bytes:
        data = pack('<3i', self.version, self.bone_id, len(self.bones))
        if self.bones:
            data += pack('<II', 0, 36)  # flags, offset
            for bone in self.bones:
                data += pack('<3i', bone.bone_id, bone.index, bone.bone_type)
        return _chunk(CHUNK_HANIM_PLG, data, lib_id)


@dataclass
class DffFrame:
    """Transform frame in the hierarchy."""
    name: str = ""
    rotation: tuple = (1,0,0, 0,1,0, 0,0,1)  # 3x3 matrix as 9 floats (row-major)
    position: tuple = (0.0, 0.0, 0.0)
    parent: int = -1
    flags: int = 0
    hanim: Optional[HAnimData] = None
    user_data: Optional[UserData] = None
    write_name: bool = False  # Only True if original DFF had Frame Name chunk

    def header_bytes(self) -> bytes:
        """56 bytes: rotation(36) + position(12) + parent(4) + flags(4)."""
        data = pack('<9f', *self.rotation)
        data += pack('<3f', *self.position)
        data += pack('<iI', self.parent, self.flags)
        return data

    def extension_bytes(self, lib_id: int) -> bytes:
        ext = b''
        if self.write_name and self.name and self.name != "unknown":
            ext += _chunk(CHUNK_FRAME_NAME, _pad_string(self.name), lib_id)
        if self.hanim:
            ext += self.hanim.to_bytes(lib_id)
        if self.user_data and self.user_data.sections:
            ext += self.user_data.to_bytes(lib_id)
        return _chunk(CHUNK_EXTENSION, ext, lib_id)


@dataclass
class DffGeometry:
    """Mesh geometry with vertices, normals, UVs, colors, materials."""
    vertices: list = field(default_factory=list)        # list[(x,y,z)]
    normals: list = field(default_factory=list)          # list[(x,y,z)]
    triangles: list = field(default_factory=list)        # list[Triangle]
    uv_layers: list = field(default_factory=list)        # list[list[TexCoords]]
    prelit_colors: list = field(default_factory=list)    # list[RGBA]
    materials: list = field(default_factory=list)         # list[DffMaterial]
    bounding_sphere: BoundingSphere = field(default_factory=BoundingSphere)

    export_normals: bool = True
    write_bin_mesh: bool = True
    pipeline: int = 0
    export_light: bool = True
    export_mod_color: bool = True

    original_flags: int = 0  # original geometry flags from import (for round-trip)

    skin: Optional[SkinData] = None
    extra_colors: Optional[ExtraVertColors] = None
    user_data: Optional[UserData] = None
    ext_2dfx: Optional[Extension2dfx] = None
    breakable: Optional[BreakableData] = None

    def _build_flags(self) -> int:
        num_uv = len(self.uv_layers)

        if self.original_flags:
            # Start from original flags, but update data-dependent bits
            flags = self.original_flags & 0xFFFF

            # Update UV flags based on actual data
            flags &= ~(GEOM_TEXTURED | GEOM_TEXTURED2)
            if num_uv == 1:
                flags |= GEOM_TEXTURED
            elif num_uv >= 2:
                flags |= GEOM_TEXTURED2

            # Update prelit based on actual data
            if self.prelit_colors:
                flags |= GEOM_PRELIT
            else:
                flags &= ~GEOM_PRELIT

            # Update normals
            if self.export_normals and self.normals:
                flags |= GEOM_NORMALS
            else:
                flags &= ~GEOM_NORMALS

            flags = (flags & 0xFFFF) | ((num_uv & 0xFF) << 16)
            return flags

        flags = GEOM_POSITIONS
        if num_uv == 1:
            flags |= GEOM_TEXTURED
        elif num_uv >= 2:
            # Kams: UV2 sets TEXTURED2 only, clears TEXTURED
            flags |= GEOM_TEXTURED2
        if self.prelit_colors:
            flags |= GEOM_PRELIT
        if self.export_normals and self.normals:
            flags |= GEOM_NORMALS
        if self.export_light:
            flags |= GEOM_LIGHT
        if self.export_mod_color:
            flags |= GEOM_MOD_COLOR

        # UV layer count in bits 16-23
        flags |= (num_uv & 0xFF) << 16

        return flags

    def _write_bin_mesh_plg(self, lib_id: int) -> bytes:
        """Group triangles by material index for Binary Mesh PLG."""
        # Group triangles by material
        mat_groups = {}
        for tri in self.triangles:
            mat_groups.setdefault(tri.material, []).append(tri)

        total_indices = len(self.triangles) * 3

        data = pack('<III', 0, len(mat_groups), total_indices)

        for mat_idx in sorted(mat_groups.keys()):
            tris = mat_groups[mat_idx]
            indices_count = len(tris) * 3
            data += pack('<II', indices_count, mat_idx)
            for tri in tris:
                data += pack('<III', tri.a, tri.b, tri.c)

        return _chunk(CHUNK_BIN_MESH_PLG, data, lib_id)

    def to_bytes(self, lib_id: int, rw_version: int) -> bytes:
        flags = self._build_flags()
        num_verts = len(self.vertices)
        num_tris = len(self.triangles)

        # Struct: header
        struct_data = pack('<IIII', flags, num_tris, num_verts, 1)

        # Surface properties (for older versions)
        if rw_version < 0x34000:
            struct_data += pack('<3f', 1.0, 1.0, 1.0)

        # Prelit colors
        if flags & GEOM_PRELIT:
            for c in self.prelit_colors:
                struct_data += pack('<4B', c.r, c.g, c.b, c.a)

        # UV layers
        for uv_layer in self.uv_layers:
            for tc in uv_layer:
                struct_data += pack('<2f', tc.u, tc.v)

        # Triangles (RenderWare format: b, a, material, c)
        for tri in self.triangles:
            struct_data += pack('<4H', tri.b, tri.a, tri.material, tri.c)

        # Bounding sphere
        bs = self.bounding_sphere
        struct_data += pack('<4f', bs.x, bs.y, bs.z, bs.radius)

        # Has vertices / has normals flags
        struct_data += pack('<II', 1 if self.vertices else 0,
                                   1 if (self.export_normals and self.normals) else 0)

        # Vertices
        if self.vertices:
            for v in self.vertices:
                struct_data += pack('<3f', v[0], v[1], v[2])

        # Normals
        if self.export_normals and self.normals:
            for n in self.normals:
                struct_data += pack('<3f', n[0], n[1], n[2])

        body = _chunk(CHUNK_STRUCT, struct_data, lib_id)

        # Material list
        mat_struct = pack('<I', len(self.materials))
        for _ in self.materials:
            mat_struct += pack('<i', -1)
        mat_body = _chunk(CHUNK_STRUCT, mat_struct, lib_id)
        for mat in self.materials:
            mat_body += mat.to_bytes(lib_id, rw_version)
        body += _chunk(CHUNK_MATERIAL_LIST, mat_body, lib_id)

        # Extensions
        ext_data = b''
        if self.write_bin_mesh:
            ext_data += self._write_bin_mesh_plg(lib_id)

        if self.skin:
            ext_data += self.skin.to_bytes(lib_id)

        if self.extra_colors and self.extra_colors.colors:
            ec_data = pack('<I', 1)  # magic
            for c in self.extra_colors.colors:
                ec_data += pack('<4B', c.r, c.g, c.b, c.a)
            ext_data += _chunk(CHUNK_EXTRA_COLORS, ec_data, lib_id)

        # Pipeline chunk пишем на уровне atomic extension (см. DffClump.to_bytes).
        # Раньше писался здесь, в geometry extension, но librwgta/Seggaeman/Kam
        # хранят его в atomic — для полной совместимости делаем как они.

        if self.user_data and self.user_data.sections:
            ext_data += self.user_data.to_bytes(lib_id)

        # MatFX indicator on geometry extension (if any material has effects)
        has_matfx = any(
            m.bump_map or m.env_map or m.dual_texture
            for m in self.materials
        )
        if has_matfx:
            ext_data += _chunk(CHUNK_MATFX_PLG, pack('<I', 1), lib_id)

        # 2DFX effects (usually on last geometry only)
        if self.ext_2dfx and self.ext_2dfx.entries:
            ext_data += self.ext_2dfx.to_bytes(lib_id)

        # Breakable Objects extension (0x253F2FD)
        if self.breakable:
            ext_data += self.breakable.to_bytes(lib_id)

        body += _chunk(CHUNK_EXTENSION, ext_data, lib_id)
        return _chunk(CHUNK_GEOMETRY, body, lib_id)


@dataclass
class DffAtomic:
    """Links a frame to a geometry."""
    frame_index: int = 0
    geometry_index: int = 0
    flags: int = 0x04
    unused: int = 0


@dataclass
class DffLight:
    """RenderWare light in the clump (Omni/Point light for 2DFX)."""
    frame_index: int = 0
    radius: float = 200.0
    color: tuple = (1.0, 1.0, 1.0)
    direction: float = 0.0
    light_type: int = 0x80  # rpLIGHTPOINT (128)
    flags: int = 3          # rpLIGHTLIGHTATOMICS | rpLIGHTLIGHTWORLD


@dataclass
class DffClump:
    """Root DFF structure containing frames, geometries, and atomics."""
    frames: list = field(default_factory=list)       # list[DffFrame]
    geometries: list = field(default_factory=list)    # list[DffGeometry]
    atomics: list = field(default_factory=list)       # list[DffAtomic]
    lights: list = field(default_factory=list)        # list[DffLight]
    version: int = GTA_SA_VERSION
    collision_data: bytes = b''
    raw_frame_list: bytes = b''  # Raw frame list bytes for round-trip
    raw_geometry_list: bytes = b''  # Raw geometry list bytes for round-trip
    raw_atomics: bytes = b''  # Raw atomic bytes for round-trip
    uv_anim_dict: Optional['UVAnimDict'] = None  # Clump-level UV anim dictionary

    def to_bytes(self) -> bytes:
        lib_id = make_library_id(self.version)
        rw_version = self.version

        # Clump struct
        num_atomics = len(self.atomics)
        if num_atomics == 0 and self.raw_atomics:
            num_atomics = 1  # At least 1 atomic in raw data
        num_lights = len(self.lights)
        clump_struct = pack('<III', num_atomics, num_lights, 0)
        body = _chunk(CHUNK_STRUCT, clump_struct, lib_id)

        # Frame list — use raw bytes for perfect round-trip if available
        if self.raw_frame_list:
            body += _chunk(CHUNK_FRAME_LIST, self.raw_frame_list, lib_id)
        else:
            frame_struct = pack('<I', len(self.frames))
            for frame in self.frames:
                frame_struct += frame.header_bytes()
            frame_body = _chunk(CHUNK_STRUCT, frame_struct, lib_id)
            for frame in self.frames:
                frame_body += frame.extension_bytes(lib_id)
            body += _chunk(CHUNK_FRAME_LIST, frame_body, lib_id)

        # Geometry list — use raw bytes for round-trip if available
        if self.raw_geometry_list:
            body += self.raw_geometry_list
        else:
            geom_struct = pack('<I', len(self.geometries))
            geom_body = _chunk(CHUNK_STRUCT, geom_struct, lib_id)
            for geom in self.geometries:
                geom_body += geom.to_bytes(lib_id, rw_version)
            body += _chunk(CHUNK_GEOMETRY_LIST, geom_body, lib_id)

        # Atomics — use raw for round-trip if available
        if self.raw_atomics:
            body += self.raw_atomics
        else:
            for atomic in self.atomics:
                atomic_struct = pack('<IIII',
                    atomic.frame_index, atomic.geometry_index,
                    atomic.flags, atomic.unused)
                atomic_body = _chunk(CHUNK_STRUCT, atomic_struct, lib_id)

                # Atomic extensions
                atomic_ext = b''
                geom = self.geometries[atomic.geometry_index]
                if geom.skin:
                    atomic_ext += _chunk(0x001F, pack('<II', 0x0116, 1), lib_id)  # Right to Render
                    atomic_ext += _chunk(0x0120, pack('<I', 0), lib_id)  # Node Name PLG (required for SA skinned)
                if any(m.bump_map or m.env_map or m.dual_texture for m in geom.materials):
                    atomic_ext += _chunk(CHUNK_MATFX_PLG, pack('<I', 1), lib_id)
                # Pipeline chunk (0x253F2F3) — тут его ожидает RenderWare/librwgta/Kam's scripts.
                # Для Vehicle pipeline (0x53F2009A) кузов машины получает env-map отражения в игре.
                if geom.pipeline:
                    atomic_ext += _chunk(CHUNK_PIPELINE_SET, pack('<I', geom.pipeline), lib_id)

                atomic_body += _chunk(CHUNK_EXTENSION, atomic_ext, lib_id)
                body += _chunk(CHUNK_ATOMIC, atomic_body, lib_id)

        # Lights (RW Light objects for 2DFX)
        for light in self.lights:
            # Frame link struct (precedes the Light chunk in clump)
            body += _chunk(CHUNK_STRUCT, pack('<I', light.frame_index), lib_id)

            # Light struct: radius(f), color_rgb(3f), direction(f), flags_type(u32)
            flags_type = (light.light_type << 16) | light.flags
            light_struct = pack('<f3ffI',
                                light.radius,
                                *light.color,
                                light.direction,
                                flags_type)
            light_body = _chunk(CHUNK_STRUCT, light_struct, lib_id)
            # Light extension (empty)
            light_body += _chunk(CHUNK_EXTENSION, b'', lib_id)

            body += _chunk(CHUNK_LIGHT, light_body, lib_id)

        # Clump extension
        clump_ext = b''
        if self.collision_data:
            clump_ext += _chunk(CHUNK_COLLISION_MODEL, self.collision_data, lib_id)
        if self.uv_anim_dict and self.uv_anim_dict.anims:
            clump_ext += self.uv_anim_dict.to_bytes(lib_id)
        body += _chunk(CHUNK_EXTENSION, clump_ext, lib_id)

        return _chunk(CHUNK_CLUMP, body, lib_id)


def write_dff(clump: DffClump) -> bytes:
    """Serialize a DffClump to DFF binary format."""
    return clump.to_bytes()


def write_dff_file(filepath: str, clump: DffClump):
    """Write a DffClump to a .dff file."""
    with open(filepath, 'wb') as f:
        f.write(clump.to_bytes())


# ── Reader ──────────────────────────────────────────────────────

def _decode_library_id(lib_id: int):
    """Decode 32-bit library ID into (version, build)."""
    if lib_id & 0xFFFF0000 == 0:
        return (lib_id << 8, 0)
    version = (((lib_id >> 14) & 0x3FF00) + 0x30000) | ((lib_id >> 16) & 0x3F)
    build = lib_id & 0xFFFF
    return (version, build)


def _read_chunk_header(r: BinaryReader):
    """Read a 12-byte RW chunk header. Returns (type, size, lib_id)."""
    chunk_type, size, lib_id = r.read('<III')
    return chunk_type, size, lib_id


def _read_string_chunk(r: BinaryReader, size: int) -> str:
    """Read a RW String chunk payload."""
    raw = r.read_bytes(size)
    end = raw.find(b'\x00')
    if end == -1:
        end = len(raw)
    return raw[:end].decode('ascii', errors='replace')


def _read_texture_chunk(r: BinaryReader, size: int) -> DffTexture:
    """Read a Texture chunk (struct + name string + mask string + ext)."""
    end = r.pos + size
    tex = DffTexture()

    # Struct
    ct, cs, cl = _read_chunk_header(r)
    if ct == CHUNK_STRUCT:
        tex.filters = r.read_one('<H')
        r.skip(cs - 2)  # skip remaining struct bytes

    # Name string
    ct, cs, cl = _read_chunk_header(r)
    if ct == CHUNK_STRING:
        tex.name = _read_string_chunk(r, cs)

    # Mask string
    if r.pos < end:
        ct, cs, cl = _read_chunk_header(r)
        if ct == CHUNK_STRING:
            tex.mask = _read_string_chunk(r, cs)
        else:
            r.skip(cs)

    # Skip extension
    r.seek(end)
    return tex


def _read_material_chunk(r: BinaryReader, size: int, rw_version: int) -> DffMaterial:
    """Read a Material chunk."""
    end = r.pos + size
    mat = DffMaterial()

    # Struct
    ct, cs, cl = _read_chunk_header(r)
    struct_end = r.pos + cs
    r.skip(4)  # padding
    mat.color = RGBA(*r.read('<4B'))
    _unused, has_tex = r.read('<II')
    if rw_version > 0x30400:
        mat.surface = SurfaceProperties(*r.read('<3f'))
    r.seek(struct_end)

    # Texture
    if has_tex:
        ct, cs, cl = _read_chunk_header(r)
        if ct == CHUNK_TEXTURE:
            mat.texture = _read_texture_chunk(r, cs)
        else:
            r.skip(cs)

    # Extension
    if r.pos < end:
        ct, cs, cl = _read_chunk_header(r)
        if ct == CHUNK_EXTENSION:
            ext_end = r.pos + cs
            while r.pos < ext_end:
                ect, ecs, ecl = _read_chunk_header(r)
                plugin_end = r.pos + ecs
                if ect == CHUNK_MATFX_PLG:
                    _read_matfx_plugin(r, ecs, mat)
                elif ect == CHUNK_SPECULAR_MAT:
                    level = r.read_one('<f')
                    name_raw = r.read_bytes(min(24, ecs - 4))
                    nm_end = name_raw.find(b'\x00')
                    spec_name = name_raw[:nm_end].decode('ascii', errors='replace') if nm_end >= 0 else name_raw.decode('ascii', errors='replace')
                    mat.specular = SpecularMaterial(level=level, name=spec_name)
                elif ect == CHUNK_REFLECTION_MAT:
                    vals = r.read('<5f')
                    mat.reflection = ReflectionMaterial(*vals)
                elif ect == CHUNK_USERDATA_PLG:
                    mat.user_data = _read_userdata_plugin(r, ecs)
                elif ect == CHUNK_UV_ANIM_PLG:
                    # Material-level UV anim reference — list of names
                    # pointing into the clump-level UV anim dict.
                    mat.uv_anim_names = _read_uv_anim_plg(
                        r.data, r.pos, ecs)
                else:
                    pass
                r.seek(plugin_end)
        else:
            r.skip(cs)

    r.seek(end)
    return mat


def _read_matfx_plugin(r: BinaryReader, size: int, mat: DffMaterial):
    """Read Material Effects PLG content."""
    start = r.pos
    end = start + size
    effect_type = r.read_one('<I')

    if effect_type in (1, 3):
        # Bump map
        marker = r.read_one('<I')
        if marker == 1:
            intensity = r.read_one('<f')
            has_bump_tex = r.read_one('<I')
            bump_tex = None
            if has_bump_tex and r.pos < end:
                ct, cs, cl = _read_chunk_header(r)
                if ct == CHUNK_TEXTURE:
                    bump_tex = _read_texture_chunk(r, cs)
                else:
                    r.skip(cs)
            has_height = r.read_one('<I') if r.pos < end else 0
            height_tex = None
            if has_height and r.pos < end:
                ct, cs, cl = _read_chunk_header(r)
                if ct == CHUNK_TEXTURE:
                    height_tex = _read_texture_chunk(r, cs)
                else:
                    r.skip(cs)
            mat.bump_map = BumpMapEffect(intensity=intensity, bump_texture=bump_tex, height_texture=height_tex)

    if effect_type in (2, 3):
        # Env map
        if r.pos < end:
            marker = r.read_one('<I')
            if marker == 2:
                coeff = r.read_one('<f')
                use_fb = bool(r.read_one('<I'))
                has_tex = r.read_one('<I') if r.pos < end else 0
                env_tex = None
                if has_tex and r.pos < end:
                    ct, cs, cl = _read_chunk_header(r)
                    if ct == CHUNK_TEXTURE:
                        env_tex = _read_texture_chunk(r, cs)
                    else:
                        r.skip(cs)
                mat.env_map = EnvMapEffect(coefficient=coeff, use_fb_alpha=use_fb, texture=env_tex)

    if effect_type == 4:
        # Dual Texture
        if r.pos < end:
            marker = r.read_one('<I')
            if marker == 4:
                src_blend = r.read_one('<I')
                dst_blend = r.read_one('<I')
                has_tex = r.read_one('<I') if r.pos < end else 0
                dual_tex = None
                if has_tex and r.pos < end:
                    ct, cs, cl = _read_chunk_header(r)
                    if ct == CHUNK_TEXTURE:
                        dual_tex = _read_texture_chunk(r, cs)
                    else:
                        r.skip(cs)
                mat.dual_texture = DualTextureEffect(
                    src_blend=src_blend, dst_blend=dst_blend, texture=dual_tex)

    r.seek(end)


def _read_geometry_chunk(r: BinaryReader, size: int, rw_version: int) -> DffGeometry:
    """Read a Geometry chunk.  *rw_version* comes from the parent Geometry List."""
    end = r.pos + size
    geom = DffGeometry()

    # ── Struct ──
    ct, cs, cl = _read_chunk_header(r)
    struct_start = r.pos
    struct_end = r.pos + cs

    flags, num_tris, num_verts, morph_count = r.read('<IIII')
    geom._import_flags = flags  # store original flags for round-trip
    geom.export_normals = bool(flags & GEOM_NORMALS)

    # Old RW versions store surface properties inline
    if rw_version < 0x34000:
        r.skip(12)  # ambient, specular, diffuse

    # Native geometry — data is in platform-specific extension, not here
    is_native = bool(flags & GEOM_NATIVE)

    # UV layer count from upper byte of flags
    num_uv = (flags >> 16) & 0xFF
    if num_uv == 0:
        if flags & GEOM_TEXTURED2:
            num_uv = 2
        elif flags & GEOM_TEXTURED:
            num_uv = 1

    if not is_native:
        # Prelit colors (4 bytes per vertex: RGBA) — numpy bulk read
        if flags & GEOM_PRELIT and num_verts > 0:
            arr = np.frombuffer(r.data, dtype=np.uint8,
                                count=num_verts * 4, offset=r.pos).reshape(num_verts, 4)
            r.skip(num_verts * 4)
            geom.prelit_colors = [RGBA(r_, g_, b_, a_) for r_, g_, b_, a_ in arr.tolist()]

        # UV layers (8 bytes per vertex per layer: u, v as float32)
        for _ in range(num_uv):
            if num_verts > 0:
                arr = np.frombuffer(r.data, dtype='<f4',
                                    count=num_verts * 2, offset=r.pos).reshape(num_verts, 2)
                r.skip(num_verts * 8)
                geom.uv_layers.append([TexCoords(u, v) for u, v in arr.tolist()])
            else:
                geom.uv_layers.append([])

        # Triangles (8 bytes each: b, a, material, c as uint16)
        if num_tris > 0:
            arr = np.frombuffer(r.data, dtype='<u2',
                                count=num_tris * 4, offset=r.pos).reshape(num_tris, 4)
            r.skip(num_tris * 8)
            # File order is (b, a, material, c) — remap into Triangle's ABC layout.
            geom.triangles = [Triangle(a=a, b=b, c=c, material=m)
                              for b, a, m, c in arr.tolist()]

    # ── Morph targets ──
    for _morph in range(morph_count):
        geom.bounding_sphere = BoundingSphere(*r.read('<4f'))
        has_pos, has_norms = r.read('<II')

        if has_pos and num_verts > 0:
            arr = np.frombuffer(r.data, dtype='<f4',
                                count=num_verts * 3, offset=r.pos).reshape(num_verts, 3)
            r.skip(num_verts * 12)
            # extend, not assign — DFFs with morph_count > 1 append per morph.
            # .tolist() yields list of [x, y, z] lists — indexable like the
            # old tuples so downstream `v[0], v[1], v[2]` access is unchanged.
            geom.vertices.extend(arr.tolist())

        if has_norms and num_verts > 0:
            arr = np.frombuffer(r.data, dtype='<f4',
                                count=num_verts * 3, offset=r.pos).reshape(num_verts, 3)
            r.skip(num_verts * 12)
            geom.normals.extend(arr.tolist())

    r.seek(struct_end)

    # ── Material list ──
    ct, cs, cl = _read_chunk_header(r)
    if ct == CHUNK_MATERIAL_LIST:
        matlist_end = r.pos + cs
        mct, mcs, mcl = _read_chunk_header(r)
        mat_count = r.read_one('<I')
        r.skip(mat_count * 4)  # parent indices (-1 each)

        for _ in range(mat_count):
            mct2, mcs2, mcl2 = _read_chunk_header(r)
            if mct2 == CHUNK_MATERIAL:
                geom.materials.append(_read_material_chunk(r, mcs2, rw_version))
            else:
                r.skip(mcs2)

        r.seek(matlist_end)

    # ── Extension ──
    if r.pos < end:
        ct, cs, cl = _read_chunk_header(r)
        if ct == CHUNK_EXTENSION:
            ext_end = r.pos + cs
            while r.pos < ext_end:
                ect, ecs, ecl = _read_chunk_header(r)
                plugin_end = r.pos + ecs
                if ect == CHUNK_BIN_MESH_PLG:
                    _read_bin_mesh_plg(r, ecs, geom)
                elif ect == CHUNK_SKIN_PLG:
                    geom.skin = _read_skin_plugin(r, ecs, len(geom.vertices))
                elif ect == CHUNK_EXTRA_COLORS:
                    # Night Vertex Colors PLG:
                    #   magic u32 — 0 means "no night colors, chunk is only
                    #     the magic word". Non-zero → nv × RGBA follow.
                    # Some vanilla DFFs also trim the chunk short (fewer
                    # colors than verts) or the chunk size doesn't match
                    # `len(geom.vertices)*4` — we clamp to what's actually
                    # in the chunk instead of reading past the buffer.
                    _magic = r.read_one('<I')
                    ec = ExtraVertColors()
                    _nv = len(geom.vertices)
                    available = ecs - 4  # bytes left in this chunk after magic
                    # Cap nv to what the chunk can actually carry (4 B per colour).
                    safe_nv = min(_nv, available // 4) if _nv > 0 else 0
                    if _magic != 0 and safe_nv > 0:
                        _arr = np.frombuffer(r.data, dtype=np.uint8,
                                             count=safe_nv * 4, offset=r.pos).reshape(safe_nv, 4)
                        r.skip(safe_nv * 4)
                        ec.colors = [RGBA(r_, g_, b_, a_) for r_, g_, b_, a_ in _arr.tolist()]
                    geom.extra_colors = ec
                elif ect == CHUNK_PIPELINE_SET:
                    geom.pipeline = r.read_one('<I')
                elif ect == CHUNK_USERDATA_PLG:
                    geom.user_data = _read_userdata_plugin(r, ecs)
                elif ect == CHUNK_2DFXPLG:
                    geom.ext_2dfx = _read_2dfx_plugin(r, ecs)
                elif ect == CHUNK_BREAKABLE:
                    # Breakable Objects extension (Kams brakableobjects.ms):
                    # 4×u32 buffer-allocs + 3×float offset + float force.
                    # 28 bytes total — short enough that we just read the
                    # whole struct here without a dedicated helper.
                    if ecs >= 28:
                        va, fa, ma, ua = r.read('<4I')
                        ox, oy, oz = r.read('<3f')
                        force = r.read_one('<f')
                        geom.breakable = BreakableData(
                            vertices_alloc=va, faces_alloc=fa,
                            materials_alloc=ma, uvs_alloc=ua,
                            offset=(ox, oy, oz), force=force,
                        )
                else:
                    pass
                r.seek(plugin_end)

    r.seek(end)
    return geom


def _read_userdata_plugin(r: BinaryReader, size: int) -> UserData:
    """Read User Data PLG."""
    start = r.pos
    ud = UserData()
    num_sections = r.read_one('<I')

    for _ in range(num_sections):
        sec = UserDataSection()
        # Name
        name_len = r.read_one('<I')
        if name_len > 0:
            sec.name = r.read_bytes(name_len).decode('ascii', errors='replace')
        # Type and count
        sec.data_type, num_elements = r.read('<II')
        sec.data = []

        if sec.data_type == USERDATA_INT:
            for _ in range(num_elements):
                sec.data.append(r.read_one('<I'))
        elif sec.data_type == USERDATA_FLOAT:
            for _ in range(num_elements):
                sec.data.append(r.read_one('<f'))
        elif sec.data_type == USERDATA_STRING:
            for _ in range(num_elements):
                str_len = r.read_one('<I')
                sec.data.append(r.read_bytes(str_len).decode('ascii', errors='replace'))

        ud.sections.append(sec)

    r.seek(start + size)
    return ud


def _read_bin_mesh_plg(r: BinaryReader, size: int, geom: 'DffGeometry'):
    """Read Binary Mesh PLG and update triangle material indices."""
    start = r.pos
    flags = r.read_one('<I')       # 0 = trilist, 1 = tristrip
    num_splits = r.read_one('<I')
    total_indices = r.read_one('<I')

    # Build vertex→triangle lookup for material assignment
    # Map (v0,v1,v2) → triangle index for fast lookup
    tri_lookup = {}
    for ti, tri in enumerate(geom.triangles):
        key = tuple(sorted((tri.a, tri.b, tri.c)))
        tri_lookup[key] = ti

    for _ in range(num_splits):
        num_indices = r.read_one('<I')
        mat_idx = r.read_one('<I')

        if flags == 0:
            # Triangle list: every 3 indices = one triangle — bulk read via numpy
            n_tris = num_indices // 3
            if n_tris > 0:
                tri_arr = np.frombuffer(r.data, dtype='<u4',
                                        count=n_tris * 3, offset=r.pos).reshape(n_tris, 3)
                r.skip(n_tris * 12)
                for i0, i1, i2 in tri_arr.tolist():
                    key = tuple(sorted((i0, i1, i2)))
                    ti = tri_lookup.get(key)
                    if ti is not None:
                        geom.triangles[ti].material = mat_idx
        else:
            # Triangle strip: read all indices at once, then walk in Python.
            if num_indices > 0:
                indices = np.frombuffer(r.data, dtype='<u4',
                                        count=num_indices, offset=r.pos).tolist()
                r.skip(num_indices * 4)
            else:
                indices = []
            for j in range(len(indices) - 2):
                if j % 2 == 0:
                    i0, i1, i2 = indices[j], indices[j+1], indices[j+2]
                else:
                    i0, i1, i2 = indices[j], indices[j+2], indices[j+1]
                if i0 == i1 or i1 == i2 or i0 == i2:
                    continue  # degenerate
                key = tuple(sorted((i0, i1, i2)))
                ti = tri_lookup.get(key)
                if ti is not None:
                    geom.triangles[ti].material = mat_idx

    r.seek(start + size)


def _read_skin_plugin(r: BinaryReader, size: int, num_verts: int) -> SkinData:
    """Read Skin PLG (matching DragonFF format)."""
    skin = SkinData()
    start = r.pos

    # Header: num_bones, num_used_bones, max_weights_per_vertex, padding
    skin.num_bones, skin.num_used, skin.max_weights = r.read('<3B')
    r.skip(1)  # padding byte

    # Read bones_used array
    oldver = (skin.num_used == 0)
    if skin.num_used > 0:
        for _ in range(skin.num_used):
            skin.bones_used.append(r.read_one('<B'))

    # Vertex bone indices (4 bytes per vertex) — bulk read via numpy
    if num_verts > 0:
        _bi = np.frombuffer(r.data, dtype=np.uint8,
                            count=num_verts * 4, offset=r.pos).reshape(num_verts, 4)
        r.skip(num_verts * 4)
        skin.bone_indices = [tuple(row) for row in _bi.tolist()]

    # Vertex bone weights (4 floats per vertex)
    if num_verts > 0:
        _bw = np.frombuffer(r.data, dtype='<f4',
                            count=num_verts * 4, offset=r.pos).reshape(num_verts, 4)
        r.skip(num_verts * 16)
        skin.bone_weights = [tuple(row) for row in _bw.tolist()]

    # Bone matrices (inverse bind pose)
    for _ in range(skin.num_bones):
        if oldver:
            r.skip(4)  # 0xDEADDEAD marker in old format
        raw = list(r.read('<16f'))
        # Clear last column, set [15]=1 (proper affine matrix)
        raw[3] = 0.0
        raw[7] = 0.0
        raw[11] = 0.0
        raw[15] = 1.0
        skin.bone_matrices.append([raw[0:4], raw[4:8], raw[8:12], raw[12:16]])

    return skin


def _write_2dfx_entry(entry) -> bytes:
    """Serialize a single 2DFX effect entry payload (without header)."""
    if isinstance(entry, Light2dfx):
        data = pack('<4B', entry.color.r, entry.color.g, entry.color.b, entry.color.a)
        data += pack('<ffffBBBBB',
                     entry.corona_far_clip, entry.pointlight_range,
                     entry.corona_size, entry.shadow_size,
                     entry.corona_show_mode, entry.corona_enable_reflection,
                     entry.corona_flare_type, entry.shadow_color_multiplier,
                     entry.flags1)
        # Corona and shadow texture names — 24 bytes each
        corona = entry.corona_tex_name.encode('ascii', errors='replace')[:24]
        shadow = entry.shadow_tex_name.encode('ascii', errors='replace')[:24]
        data += corona + b'\x00' * (24 - len(corona))
        data += shadow + b'\x00' * (24 - len(shadow))
        data += pack('<BB', entry.shadow_z_distance, entry.flags2)
        # Always write 80-byte variant (Kam's / GTA SA standard)
        if entry.look_direction is not None:
            data += pack('<BBB2x', *entry.look_direction)
        else:
            data += b'\x00' * 5  # 3 bytes look_dir + 2 padding = 80 bytes total
        return data

    elif isinstance(entry, Particle2dfx):
        name = entry.effect_name.encode('ascii', errors='replace')[:24]
        return name + b'\x00' * (24 - len(name))

    elif isinstance(entry, PedAttractor2dfx):
        data = pack('<I', entry.attractor_type)
        data += pack('<9f', *entry.rotation_matrix)
        script = entry.external_script.encode('ascii', errors='replace')[:8]
        data += script + b'\x00' * (8 - len(script))
        data += pack('<I', entry.ped_existing_probability)
        return data

    elif isinstance(entry, SunGlare2dfx):
        return b''

    return b''


def _read_2dfx_plugin(r: BinaryReader, size: int) -> Extension2dfx:
    """Read 2DFX Plugin (lights, particles, ped attractors, sun glare)."""
    start = r.pos
    ext = Extension2dfx()
    entries_count = r.read_one('<I')

    for _ in range(entries_count):
        loc = r.read('<3f')
        entry_type, entry_size = r.read('<II')
        entry_start = r.pos

        if entry_type == 0:  # Light
            light = Light2dfx(loc=loc)
            light.color = RGBA(*r.read('<4B'))
            (light.corona_far_clip, light.pointlight_range,
             light.corona_size, light.shadow_size,
             light.corona_show_mode, light.corona_enable_reflection,
             light.corona_flare_type, light.shadow_color_multiplier,
             light.flags1) = r.read('<ffffBBBBB')

            corona_raw = r.read_bytes(24)
            shadow_raw = r.read_bytes(24)
            end_c = corona_raw.find(b'\x00')
            end_s = shadow_raw.find(b'\x00')
            light.corona_tex_name = corona_raw[:end_c if end_c >= 0 else 24].decode('ascii', errors='replace')
            light.shadow_tex_name = shadow_raw[:end_s if end_s >= 0 else 24].decode('ascii', errors='replace')

            light.shadow_z_distance, light.flags2 = r.read('<BB')

            # 80-byte variant has look_direction
            if entry_size > 76:
                light.look_direction = r.read('<3B')

            ext.entries.append(light)

        elif entry_type == 1:  # Particle
            particle = Particle2dfx(loc=loc)
            raw = r.read_bytes(min(24, entry_size))
            end_p = raw.find(b'\x00')
            particle.effect_name = raw[:end_p if end_p >= 0 else len(raw)].decode('ascii', errors='replace')
            ext.entries.append(particle)

        elif entry_type == 3:  # Ped Attractor
            ped = PedAttractor2dfx(loc=loc)
            ped.attractor_type = r.read_one('<I')
            ped.rotation_matrix = r.read('<9f')
            script_raw = r.read_bytes(8)
            end_e = script_raw.find(b'\x00')
            ped.external_script = script_raw[:end_e if end_e >= 0 else 8].decode('ascii', errors='replace')
            ped.ped_existing_probability = r.read_one('<I')
            ext.entries.append(ped)

        elif entry_type == 4:  # Sun Glare
            ext.entries.append(SunGlare2dfx(loc=loc))

        r.seek(entry_start + entry_size)

    r.seek(start + size)
    return ext


def _read_frame_list(r: BinaryReader, size: int) -> list:
    """Read Frame List chunk. Returns list of DffFrame."""
    end = r.pos + size
    # Save raw bytes for round-trip export
    start_pos = r.pos
    r.seek(end)
    raw_bytes = r.data[start_pos:end]
    r.seek(start_pos)

    frames = []

    # Struct
    ct, cs, cl = _read_chunk_header(r)
    struct_end = r.pos + cs
    frame_count = r.read_one('<I')

    for _ in range(frame_count):
        rotation = r.read('<9f')
        position = r.read('<3f')
        parent, flags = r.read('<iI')
        frames.append(DffFrame(
            rotation=rotation,
            position=position,
            parent=parent,
            flags=flags,
        ))

    r.seek(struct_end)

    # Frame extensions (one per frame)
    for i in range(frame_count):
        if r.pos >= end:
            break
        ct, cs, cl = _read_chunk_header(r)
        if ct == CHUNK_EXTENSION:
            ext_end = r.pos + cs
            while r.pos < ext_end:
                ect, ecs, ecl = _read_chunk_header(r)
                plugin_end = r.pos + ecs
                if ect == CHUNK_FRAME_NAME:
                    raw = r.read_bytes(ecs)
                    nm_end = raw.find(b'\x00')
                    if nm_end == -1:
                        nm_end = len(raw)
                    frames[i].name = raw[:nm_end].decode('ascii', errors='replace')
                    frames[i].write_name = True
                elif ect == CHUNK_HANIM_PLG:
                    frames[i].hanim = _read_hanim_plugin(r, ecs)
                elif ect == CHUNK_USERDATA_PLG:
                    frames[i].user_data = _read_userdata_plugin(r, ecs)
                else:
                    pass
                r.seek(plugin_end)
            r.seek(ext_end)
        else:
            r.skip(cs)

    r.seek(end)
    # Attach raw bytes for round-trip
    for f in frames:
        f._raw_frame_list = raw_bytes
    return frames


def _read_hanim_plugin(r: BinaryReader, size: int) -> HAnimData:
    """Read HAnim PLG."""
    start = r.pos
    hanim = HAnimData()
    hanim.version, hanim.bone_id, bone_count = r.read('<3i')
    if bone_count > 0:
        r.skip(8)  # flags + offset
        for _ in range(bone_count):
            bid, idx, btype = r.read('<3i')
            hanim.bones.append(HAnimBone(bone_id=bid, index=idx, bone_type=btype))
    r.seek(start + size)
    return hanim


def read_dff(data: bytes) -> DffClump:
    """
    Parse DFF binary data into a DffClump.
    Returns a DffClump with frames, geometries, and atomics.
    """
    r = BinaryReader(data)
    clump = DffClump()

    # Root chunk must be Clump
    ct, cs, cl = _read_chunk_header(r)
    if ct != CHUNK_CLUMP:
        raise ValueError(f"Expected Clump chunk (0x10), got 0x{ct:X}")

    clump.version = _decode_library_id(cl)[0]
    clump_end = r.pos + cs

    # Clump struct
    ct, cs, cl = _read_chunk_header(r)
    if ct == CHUNK_STRUCT:
        num_atomics = r.read_one('<I')
        r.skip(cs - 4)  # lights, cameras
    else:
        r.skip(cs)

    # Read child chunks
    while r.pos < clump_end:
        ct, cs, cl = _read_chunk_header(r)
        chunk_end = r.pos + cs

        if ct == CHUNK_FRAME_LIST:
            clump.frames = _read_frame_list(r, cs)

        elif ct == CHUNK_GEOMETRY_LIST:
            # Save raw geometry list for round-trip
            clump.raw_geometry_list = r.data[r.pos - 12:chunk_end]  # include chunk header

            # Struct: geometry count
            gct, gcs, gcl = _read_chunk_header(r)
            geom_list_ver = _decode_library_id(gcl)[0]
            geom_count = r.read_one('<I')
            r.seek(r.pos + gcs - 4)  # skip rest of struct if any extra

            for _ in range(geom_count):
                gct2, gcs2, gcl2 = _read_chunk_header(r)
                if gct2 == CHUNK_GEOMETRY:
                    # Use Geometry List version (like DragonFF's parent_chunk.version)
                    ver = geom_list_ver or clump.version
                    clump.geometries.append(_read_geometry_chunk(r, gcs2, ver))
                else:
                    r.skip(gcs2)

        elif ct == CHUNK_ATOMIC:
            # Save raw atomic for round-trip
            clump.raw_atomics += r.data[r.pos - 12:chunk_end]

            atom_end = r.pos + cs
            act, acs, acl = _read_chunk_header(r)
            if act == CHUNK_STRUCT:
                fi, gi, af, au = r.read('<IIII')
                clump.atomics.append(DffAtomic(
                    frame_index=fi,
                    geometry_index=gi,
                    flags=af,
                    unused=au,
                ))
                # Parse atomic extension — ищем Pipeline chunk (он может лежать
                # на уровне атомика, как у Kam's/Seggaeman/librwgta).
                if r.pos < atom_end:
                    ect, ecs, ecl = _read_chunk_header(r)
                    if ect == CHUNK_EXTENSION:
                        ext_end = r.pos + ecs
                        while r.pos < ext_end:
                            pct, pcs, pcl = _read_chunk_header(r)
                            plugin_end = r.pos + pcs
                            if pct == CHUNK_PIPELINE_SET and 0 <= gi < len(clump.geometries):
                                # Пишем на геометрию — у нас geom.pipeline единое поле
                                clump.geometries[gi].pipeline = r.read_one('<I')
                            r.seek(plugin_end)
            r.seek(atom_end)

        elif ct == CHUNK_EXTENSION:
            ext_end = r.pos + cs
            while r.pos < ext_end:
                ect, ecs, ecl = _read_chunk_header(r)
                if ect == CHUNK_COLLISION_MODEL:
                    clump.collision_data = r.read_bytes(ecs)
                elif ect == CHUNK_UV_ANIM_DICT:
                    # Parse the dict body off the BinaryReader's buffer
                    # without advancing the cursor mid-parse — seek back
                    # when done. _read_uv_anim_dict wants absolute
                    # offsets into the whole file.
                    body_start = r.pos
                    clump.uv_anim_dict = _read_uv_anim_dict(
                        r.data, body_start, ecs)
                    r.seek(body_start + ecs)
                else:
                    r.skip(ecs)
        else:
            r.skip(cs)

        r.seek(chunk_end)

    return clump


def read_dff_file(filepath: str) -> DffClump:
    """Read a DFF file and return a DffClump."""
    with open(filepath, 'rb') as f:
        return read_dff(f.read())
