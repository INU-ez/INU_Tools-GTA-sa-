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

from struct import pack, unpack_from, calcsize
from dataclasses import dataclass, field
from typing import Optional

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
class DffMaterial:
    """Single material with optional plugins."""
    color: RGBA = field(default_factory=RGBA)
    surface: SurfaceProperties = field(default_factory=SurfaceProperties)
    texture: Optional[DffTexture] = None
    bump_map: Optional[BumpMapEffect] = None
    env_map: Optional[EnvMapEffect] = None
    specular: Optional[SpecularMaterial] = None
    reflection: Optional[ReflectionMaterial] = None

    def _matfx_bytes(self, lib_id: int) -> bytes:
        """Build Material Effects PLG content."""
        has_bump = self.bump_map is not None
        has_env = self.env_map is not None

        if has_bump and has_env:
            effect_type = 3
        elif has_bump:
            effect_type = 1
        elif has_env:
            effect_type = 2
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
class ExtraVertColors:
    """Night vertex colors (second color layer)."""
    colors: list = field(default_factory=list)  # list[RGBA]


@dataclass
class SkinData:
    """Bone skinning data for a geometry."""
    num_bones: int = 0
    bone_indices: list = field(default_factory=list)   # per-vertex: list[(b0,b1,b2,b3)]
    bone_weights: list = field(default_factory=list)    # per-vertex: list[(w0,w1,w2,w3)]
    bone_matrices: list = field(default_factory=list)   # per-bone: list[16 floats]

    def to_bytes(self, lib_id: int) -> bytes:
        data = pack('<B3x', self.num_bones)

        for indices in self.bone_indices:
            data += pack('<4B', *indices)

        for weights in self.bone_weights:
            data += pack('<4f', *weights)

        for matrix in self.bone_matrices:
            data += pack('<4x')  # padding
            data += pack('<16f', *matrix)

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

    def header_bytes(self) -> bytes:
        """56 bytes: rotation(36) + position(12) + parent(4) + flags(4)."""
        data = pack('<9f', *self.rotation)
        data += pack('<3f', *self.position)
        data += pack('<iI', self.parent, self.flags)
        return data

    def extension_bytes(self, lib_id: int) -> bytes:
        ext = b''
        if self.name and self.name != "unknown":
            ext += _chunk(CHUNK_FRAME_NAME, _pad_string(self.name), lib_id)
        if self.hanim:
            ext += self.hanim.to_bytes(lib_id)
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

    skin: Optional[SkinData] = None
    extra_colors: Optional[ExtraVertColors] = None

    def _build_flags(self) -> int:
        flags = GEOM_POSITIONS
        if self.uv_layers:
            flags |= GEOM_TEXTURED
        if len(self.uv_layers) > 1:
            flags |= GEOM_TEXTURED2
        if self.prelit_colors:
            flags |= GEOM_PRELIT
        if self.export_normals and self.normals:
            flags |= GEOM_NORMALS
        flags |= GEOM_LIGHT | GEOM_MOD_COLOR

        # UV layer count in bits 16-23
        num_uv = len(self.uv_layers)
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

        if self.pipeline:
            ext_data += _chunk(CHUNK_PIPELINE_SET, pack('<I', self.pipeline), lib_id)

        # MatFX indicator on geometry extension (if any material has effects)
        has_matfx = any(
            m.bump_map or m.env_map
            for m in self.materials
        )
        if has_matfx:
            ext_data += _chunk(CHUNK_MATFX_PLG, pack('<I', 1), lib_id)

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
class DffClump:
    """Root DFF structure containing frames, geometries, and atomics."""
    frames: list = field(default_factory=list)       # list[DffFrame]
    geometries: list = field(default_factory=list)    # list[DffGeometry]
    atomics: list = field(default_factory=list)       # list[DffAtomic]
    version: int = GTA_SA_VERSION
    collision_data: bytes = b''

    def to_bytes(self) -> bytes:
        lib_id = make_library_id(self.version)
        rw_version = self.version

        # Clump struct
        num_atomics = len(self.atomics)
        clump_struct = pack('<III', num_atomics, 0, 0)  # atomics, lights, cameras
        body = _chunk(CHUNK_STRUCT, clump_struct, lib_id)

        # Frame list
        frame_struct = pack('<I', len(self.frames))
        for frame in self.frames:
            frame_struct += frame.header_bytes()
        frame_body = _chunk(CHUNK_STRUCT, frame_struct, lib_id)
        for frame in self.frames:
            frame_body += frame.extension_bytes(lib_id)
        body += _chunk(CHUNK_FRAME_LIST, frame_body, lib_id)

        # Geometry list
        geom_struct = pack('<I', len(self.geometries))
        geom_body = _chunk(CHUNK_STRUCT, geom_struct, lib_id)
        for geom in self.geometries:
            geom_body += geom.to_bytes(lib_id, rw_version)
        body += _chunk(CHUNK_GEOMETRY_LIST, geom_body, lib_id)

        # Atomics
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
            if any(m.bump_map or m.env_map for m in geom.materials):
                atomic_ext += _chunk(CHUNK_MATFX_PLG, pack('<I', 1), lib_id)
            if geom.pipeline:
                atomic_ext += _chunk(CHUNK_PIPELINE_SET, pack('<I', geom.pipeline), lib_id)

            atomic_body += _chunk(CHUNK_EXTENSION, atomic_ext, lib_id)
            body += _chunk(CHUNK_ATOMIC, atomic_body, lib_id)

        # Clump extension
        clump_ext = b''
        if self.collision_data:
            clump_ext += _chunk(CHUNK_COLLISION_MODEL, self.collision_data, lib_id)
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
        # Prelit colors (4 bytes per vertex: RGBA)
        if flags & GEOM_PRELIT:
            for _ in range(num_verts):
                geom.prelit_colors.append(RGBA(*r.read('<4B')))

        # UV layers (8 bytes per vertex per layer: u, v as float)
        for _ in range(num_uv):
            uv_layer = []
            for _ in range(num_verts):
                u, v = r.read('<2f')
                uv_layer.append(TexCoords(u, v))
            geom.uv_layers.append(uv_layer)

        # Triangles (8 bytes each: b, a, material, c as uint16)
        for _ in range(num_tris):
            b_idx, a_idx, mat_idx, c_idx = r.read('<4H')
            geom.triangles.append(Triangle(a=a_idx, b=b_idx, c=c_idx, material=mat_idx))

    # ── Morph targets ──
    for _morph in range(morph_count):
        geom.bounding_sphere = BoundingSphere(*r.read('<4f'))
        has_pos, has_norms = r.read('<II')

        if has_pos:
            for _ in range(num_verts):
                geom.vertices.append(r.read('<3f'))

        if has_norms:
            for _ in range(num_verts):
                geom.normals.append(r.read('<3f'))

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
                    pass  # skip, we have triangles
                elif ect == CHUNK_SKIN_PLG:
                    geom.skin = _read_skin_plugin(r, ecs, len(geom.vertices))
                elif ect == CHUNK_EXTRA_COLORS:
                    _magic = r.read_one('<I')
                    ec = ExtraVertColors()
                    for _ in range(len(geom.vertices)):
                        ec.colors.append(RGBA(*r.read('<4B')))
                    geom.extra_colors = ec
                elif ect == CHUNK_PIPELINE_SET:
                    geom.pipeline = r.read_one('<I')
                else:
                    pass
                r.seek(plugin_end)

    r.seek(end)
    return geom


def _read_skin_plugin(r: BinaryReader, size: int, num_verts: int) -> SkinData:
    """Read Skin PLG."""
    skin = SkinData()
    skin.num_bones = r.read_one('<B')
    r.skip(3)  # padding

    for _ in range(num_verts):
        skin.bone_indices.append(r.read('<4B'))

    for _ in range(num_verts):
        skin.bone_weights.append(r.read('<4f'))

    for _ in range(skin.num_bones):
        r.skip(4)  # padding
        skin.bone_matrices.append(r.read('<16f'))

    return skin


def _read_frame_list(r: BinaryReader, size: int) -> list:
    """Read Frame List chunk. Returns list of DffFrame."""
    end = r.pos + size
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
                elif ect == CHUNK_HANIM_PLG:
                    frames[i].hanim = _read_hanim_plugin(r, ecs)
                else:
                    pass
                r.seek(plugin_end)
            r.seek(ext_end)
        else:
            r.skip(cs)

    r.seek(end)
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
            r.seek(atom_end)

        elif ct == CHUNK_EXTENSION:
            ext_end = r.pos + cs
            while r.pos < ext_end:
                ect, ecs, ecl = _read_chunk_header(r)
                if ect == CHUNK_COLLISION_MODEL:
                    clump.collision_data = r.read_bytes(ecs)
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
