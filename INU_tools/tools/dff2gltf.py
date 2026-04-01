"""
DFF → glTF Binary (.glb) converter.

Converts GTA SA DFF models to glTF format for fast import into Blender.
Blender's glTF importer is written in C and is 10-50x faster than Python mesh creation.

Can be used standalone:
    python dff2gltf.py input.dff output.glb
    python dff2gltf.py --batch cache_dir/   (convert all .dff in directory)

Or as a module:
    from INU_tools.tools.dff2gltf import convert_dff_to_glb
    convert_dff_to_glb("model.dff", "model.glb")
"""

from __future__ import annotations
import struct
import json
import os
import sys

# Add parent dirs to path for standalone use
_this_dir = os.path.dirname(os.path.abspath(__file__))
_addon_dir = os.path.dirname(_this_dir)
_root_dir = os.path.dirname(_addon_dir)
if _addon_dir not in sys.path:
    sys.path.insert(0, _addon_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)


def convert_dff_to_glb(dff_path: str, glb_path: str, tex_dir: str = "") -> bool:
    """Convert a DFF file to glTF Binary (.glb).

    Args:
        dff_path: path to input .dff file
        glb_path: path to output .glb file
        tex_dir: optional directory with PNG textures (for texture references)

    Returns True on success.
    """
    from INU_tools.core.dff import read_dff

    try:
        with open(dff_path, 'rb') as f:
            data = f.read()
        clump = read_dff(data)
    except Exception:
        return False

    if not clump or not clump.geometries:
        return False

    # Build glTF structure
    gltf = _GltfBuilder()

    for gi, geom in enumerate(clump.geometries):
        if not geom.vertices or not geom.triangles:
            continue

        # Materials
        mat_indices = []
        for mi, dff_mat in enumerate(geom.materials):
            tex_name = ""
            if dff_mat.texture and dff_mat.texture.name:
                tex_name = dff_mat.texture.name

            mat_idx = gltf.add_material(
                name=tex_name or f"Material_{gi}_{mi}",
                color=(dff_mat.color.r / 255.0, dff_mat.color.g / 255.0,
                       dff_mat.color.b / 255.0, dff_mat.color.a / 255.0),
                tex_name=tex_name,
                tex_dir=tex_dir,
            )
            mat_indices.append(mat_idx)

        # Split triangles by material
        mat_tris: dict[int, list] = {}
        for tri in geom.triangles:
            mid = tri.material
            if mid not in mat_tris:
                mat_tris[mid] = []
            mat_tris[mid].append((tri.a, tri.b, tri.c))

        # Vertices
        positions = geom.vertices
        normals = geom.normals if geom.normals else None
        uvs = geom.uv_layers[0] if geom.uv_layers else None
        colors = geom.prelit_colors if geom.prelit_colors else None

        # Create mesh with primitives per material
        primitives = []
        for mid, tris in sorted(mat_tris.items()):
            # Indices
            indices = []
            for v1, v2, v3 in tris:
                indices.extend([v1, v2, v3])

            idx_accessor = gltf.add_indices(indices)

            # Attributes (shared across primitives)
            attrs = {}
            attrs['POSITION'] = gltf.add_vec3(positions)
            if normals:
                attrs['NORMAL'] = gltf.add_vec3(normals)
            if uvs:
                attrs['TEXCOORD_0'] = gltf.add_vec2([(tc.u, tc.v) for tc in uvs])
            if colors:
                attrs['COLOR_0'] = gltf.add_vec4_ubyte(
                    [(c.r, c.g, c.b, c.a) for c in colors])

            mat_gltf_idx = mat_indices[mid] if mid < len(mat_indices) else 0

            primitives.append({
                'attributes': attrs,
                'indices': idx_accessor,
                'material': mat_gltf_idx,
            })

        # Frame name
        frame_name = ""
        if clump.frames:
            # Find frame linked to this geometry via atomics
            for atom in clump.atomics:
                if atom.geometry_index == gi and atom.frame_index < len(clump.frames):
                    frame_name = clump.frames[atom.frame_index].name or ""
                    break
        mesh_name = frame_name or os.path.splitext(os.path.basename(dff_path))[0]

        mesh_idx = gltf.add_mesh(mesh_name, primitives)
        gltf.add_node(mesh_name, mesh_idx)

    # Write .glb
    try:
        gltf.write_glb(glb_path)
        return True
    except Exception:
        return False


class _GltfBuilder:
    """Minimal glTF 2.0 builder for binary .glb output."""

    def __init__(self):
        self._buffer = bytearray()
        self._accessors = []
        self._buffer_views = []
        self._meshes = []
        self._nodes = []
        self._materials = []
        self._textures = []
        self._images = []
        self._mat_cache: dict[str, int] = {}

    def _pad4(self):
        while len(self._buffer) % 4:
            self._buffer.append(0)

    def add_indices(self, indices: list[int]) -> int:
        """Add index buffer, return accessor index."""
        max_idx = max(indices) if indices else 0
        if max_idx <= 0xFFFF:
            fmt = '<H'
            comp_type = 5123  # UNSIGNED_SHORT
        else:
            fmt = '<I'
            comp_type = 5125  # UNSIGNED_INT

        self._pad4()
        offset = len(self._buffer)
        for i in indices:
            self._buffer.extend(struct.pack(fmt, i))

        bv_idx = len(self._buffer_views)
        self._buffer_views.append({
            'buffer': 0,
            'byteOffset': offset,
            'byteLength': len(self._buffer) - offset,
            'target': 34963,  # ELEMENT_ARRAY_BUFFER
        })

        acc_idx = len(self._accessors)
        self._accessors.append({
            'bufferView': bv_idx,
            'componentType': comp_type,
            'count': len(indices),
            'type': 'SCALAR',
            'max': [max_idx],
            'min': [min(indices) if indices else 0],
        })
        return acc_idx

    def add_vec3(self, data: list[tuple]) -> int:
        """Add vec3 attribute, return accessor index."""
        self._pad4()
        offset = len(self._buffer)
        mins = [float('inf')] * 3
        maxs = [float('-inf')] * 3
        for v in data:
            for i in range(3):
                mins[i] = min(mins[i], v[i])
                maxs[i] = max(maxs[i], v[i])
            self._buffer.extend(struct.pack('<3f', *v))

        bv_idx = len(self._buffer_views)
        self._buffer_views.append({
            'buffer': 0,
            'byteOffset': offset,
            'byteLength': len(self._buffer) - offset,
            'byteStride': 12,
            'target': 34962,  # ARRAY_BUFFER
        })

        acc_idx = len(self._accessors)
        self._accessors.append({
            'bufferView': bv_idx,
            'componentType': 5126,  # FLOAT
            'count': len(data),
            'type': 'VEC3',
            'max': maxs,
            'min': mins,
        })
        return acc_idx

    def add_vec2(self, data: list[tuple]) -> int:
        """Add vec2 attribute (UV), return accessor index."""
        self._pad4()
        offset = len(self._buffer)
        for v in data:
            self._buffer.extend(struct.pack('<2f', *v))

        bv_idx = len(self._buffer_views)
        self._buffer_views.append({
            'buffer': 0,
            'byteOffset': offset,
            'byteLength': len(self._buffer) - offset,
            'byteStride': 8,
            'target': 34962,
        })

        acc_idx = len(self._accessors)
        self._accessors.append({
            'bufferView': bv_idx,
            'componentType': 5126,
            'count': len(data),
            'type': 'VEC2',
        })
        return acc_idx

    def add_vec4_ubyte(self, data: list[tuple]) -> int:
        """Add vec4 unsigned byte attribute (vertex color), return accessor index."""
        self._pad4()
        offset = len(self._buffer)
        for v in data:
            self._buffer.extend(struct.pack('<4B', *v))

        bv_idx = len(self._buffer_views)
        self._buffer_views.append({
            'buffer': 0,
            'byteOffset': offset,
            'byteLength': len(self._buffer) - offset,
            'byteStride': 4,
            'target': 34962,
        })

        acc_idx = len(self._accessors)
        self._accessors.append({
            'bufferView': bv_idx,
            'componentType': 5121,  # UNSIGNED_BYTE
            'normalized': True,
            'count': len(data),
            'type': 'VEC4',
        })
        return acc_idx

    def add_material(self, name: str, color: tuple,
                     tex_name: str = "", tex_dir: str = "",
                     double_sided: bool = False,
                     has_alpha: bool = False) -> int:
        """Add material, return material index. Caches by name."""
        if name in self._mat_cache:
            return self._mat_cache[name]

        mat = {
            'name': name,
            'pbrMetallicRoughness': {
                'baseColorFactor': list(color),
                'metallicFactor': 0.0,
                'roughnessFactor': 1.0,
            },
        }

        # Add texture reference if PNG exists
        tex_has_alpha = False
        if tex_name and tex_dir:
            png_path = os.path.join(tex_dir, tex_name + '.png')
            if os.path.isfile(png_path):
                img_idx = len(self._images)
                self._images.append({'uri': 'textures/' + tex_name + '.png'})
                tex_idx = len(self._textures)
                self._textures.append({'source': img_idx})
                mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': tex_idx}
                tex_has_alpha = True  # PNG always has alpha channel

        mat['doubleSided'] = True

        # Alpha mode based on IDE flags and material properties
        if color[3] < 1.0:
            mat['alphaMode'] = 'BLEND'
        elif has_alpha:
            # IDE flag DRAW_LAST/ADDITIVE → use MASK for cutout (trees, fences)
            mat['alphaMode'] = 'MASK'
            mat['alphaCutoff'] = 0.5

        idx = len(self._materials)
        self._materials.append(mat)
        self._mat_cache[name] = idx
        return idx

    def add_mesh(self, name: str, primitives: list[dict]) -> int:
        idx = len(self._meshes)
        self._meshes.append({'name': name, 'primitives': primitives})
        return idx

    def add_node(self, name: str, mesh_idx: int,
                 translation: tuple = None, rotation: tuple = None) -> int:
        """Add node. rotation is (x,y,z,w) quaternion."""
        idx = len(self._nodes)
        node = {'name': name, 'mesh': mesh_idx}
        if translation:
            node['translation'] = list(translation)
        if rotation:
            # glTF uses (x,y,z,w)
            node['rotation'] = list(rotation)
        self._nodes.append(node)
        return idx

    def write_glb(self, path: str):
        """Write binary glTF (.glb) file."""
        # Build JSON
        gltf_json = {
            'asset': {'version': '2.0', 'generator': 'INU_Tools DFF2glTF'},
            'scene': 0,
            'scenes': [{'nodes': list(range(len(self._nodes)))}],
            'nodes': self._nodes,
            'meshes': self._meshes,
            'accessors': self._accessors,
            'bufferViews': self._buffer_views,
            'buffers': [{'byteLength': len(self._buffer)}],
            'materials': self._materials,
        }
        if self._textures:
            gltf_json['textures'] = self._textures
        if self._images:
            gltf_json['images'] = self._images

        json_bytes = json.dumps(gltf_json, separators=(',', ':')).encode('utf-8')
        # Pad JSON to 4 bytes
        while len(json_bytes) % 4:
            json_bytes += b' '

        # Pad buffer to 4 bytes
        buf = bytes(self._buffer)
        while len(buf) % 4:
            buf += b'\x00'

        # GLB header: magic + version + length
        # Chunk 0: JSON
        # Chunk 1: BIN
        total = 12 + 8 + len(json_bytes) + 8 + len(buf)

        with open(path, 'wb') as f:
            # Header
            f.write(struct.pack('<4sII', b'glTF', 2, total))
            # JSON chunk
            f.write(struct.pack('<II', len(json_bytes), 0x4E4F534A))  # JSON
            f.write(json_bytes)
            # BIN chunk
            f.write(struct.pack('<II', len(buf), 0x004E4942))  # BIN
            f.write(buf)


def batch_convert(cache_dir: str, tex_dir: str = "",
                  callback=None) -> dict[str, int]:
    """Convert all .dff files in cache_dir to .glb.

    Args:
        cache_dir: directory with .dff files
        tex_dir: directory with PNG textures
        callback: optional function(current, total) for progress

    Returns dict with counts.
    """
    dff_files = [f for f in os.listdir(cache_dir) if f.lower().endswith('.dff')]
    total = len(dff_files)
    converted = 0
    skipped = 0

    for i, fname in enumerate(dff_files):
        if callback and i % 20 == 0:
            callback(i, total)

        glb_name = os.path.splitext(fname)[0] + '.glb'
        glb_path = os.path.join(cache_dir, glb_name)

        if os.path.isfile(glb_path):
            skipped += 1
            continue

        dff_path = os.path.join(cache_dir, fname)
        if convert_dff_to_glb(dff_path, glb_path, tex_dir):
            converted += 1
        else:
            skipped += 1

    return {'converted': converted, 'skipped': skipped, 'total': total}


def build_map_glb(cache_dir: str, instances: list, ide_models: dict,
                  output_path: str, tex_dir: str = "",
                  skip_lod: bool = True, callback=None) -> dict:
    """Build a single .glb file containing all map models positioned by IPL.

    Args:
        cache_dir: directory with .dff files
        instances: list of IplInstance objects (from IPL)
        ide_models: dict model_id → IDE object (for txd_name, draw_distance)
        output_path: path to output .glb file
        tex_dir: directory with PNG textures
        skip_lod: skip LOD models
        callback: optional function(current, total, status_text)

    Returns dict with counts.
    """
    import math
    from INU_tools.core.dff import read_dff

    gltf = _GltfBuilder()
    mesh_cache = {}  # model_name → mesh_idx (for instancing)

    placed = 0
    skipped = 0
    total = len(instances)

    for idx, inst in enumerate(instances):
        if callback and idx % 100 == 0:
            callback(idx, total, inst.model_name if hasattr(inst, 'model_name') else '')

        model_name = inst.model_name
        if not model_name:
            skipped += 1
            continue

        is_lod = model_name.upper().startswith('LOD') or '_LOD' in model_name.upper()
        if skip_lod and is_lod:
            skipped += 1
            continue

        # Get or create mesh for this model
        if model_name not in mesh_cache:
            dff_path = os.path.join(cache_dir, model_name + '.dff')
            if not os.path.isfile(dff_path):
                skipped += 1
                continue

            try:
                with open(dff_path, 'rb') as f:
                    data = f.read()
                clump = read_dff(data)
            except Exception:
                skipped += 1
                continue

            if not clump or not clump.geometries:
                skipped += 1
                continue

            # Build mesh from first geometry
            geom = clump.geometries[0]
            if not geom.vertices or not geom.triangles:
                skipped += 1
                continue

            # Check IDE flags
            ide_obj = ide_models.get(inst.model_id)
            ide_flags = ide_obj.flags if ide_obj else 0
            # DRAW_LAST (0x10) or ADDITIVE (0x8) = has alpha transparency
            draw_last = bool(ide_flags & 0x10)
            additive = bool(ide_flags & 0x8)
            model_has_alpha = draw_last or additive

            # Materials
            mat_indices = []
            for mi, dff_mat in enumerate(geom.materials):
                tex_name = ""
                if dff_mat.texture and dff_mat.texture.name:
                    tex_name = dff_mat.texture.name
                # Alpha from material color or IDE flags
                mat_alpha = (dff_mat.color.a < 255) or model_has_alpha
                mat_idx = gltf.add_material(
                    name=tex_name or f"mat_{model_name}_{mi}",
                    color=(dff_mat.color.r / 255.0, dff_mat.color.g / 255.0,
                           dff_mat.color.b / 255.0, dff_mat.color.a / 255.0),
                    tex_name=tex_name, tex_dir=tex_dir,
                    double_sided=True,
                    has_alpha=mat_alpha,
                )
                mat_indices.append(mat_idx)

            # Split triangles by material
            mat_tris = {}
            for tri in geom.triangles:
                mid = tri.material
                if mid not in mat_tris:
                    mat_tris[mid] = []
                mat_tris[mid].append((tri.a, tri.b, tri.c))

            # Build primitives
            primitives = []
            positions = geom.vertices
            normals = geom.normals if geom.normals else None
            uvs = geom.uv_layers[0] if geom.uv_layers else None
            colors = geom.prelit_colors if geom.prelit_colors else None

            # Shared attribute accessors (one set per unique mesh)
            # Z-up → Y-up: (x,y,z) → (x,z,-y)
            pos_acc = gltf.add_vec3([(x, z, -y) for x, y, z in positions])
            # Don't write normals — Blender will calculate smooth shading
            # DFF split normals are already baked into duplicate vertices
            norm_acc = None
            uv_acc = gltf.add_vec2([(tc.u, tc.v) for tc in uvs]) if uvs else None
            col_acc = gltf.add_vec4_ubyte(
                [(c.r, c.g, c.b, c.a) for c in colors]) if colors else None

            for mid, tris in sorted(mat_tris.items()):
                indices = []
                for a, b, c in tris:
                    indices.extend([a, b, c])
                idx_acc = gltf.add_indices(indices)

                attrs = {'POSITION': pos_acc}
                if norm_acc is not None:
                    attrs['NORMAL'] = norm_acc
                if uv_acc is not None:
                    attrs['TEXCOORD_0'] = uv_acc
                if col_acc is not None:
                    attrs['COLOR_0'] = col_acc

                mat_gltf = mat_indices[mid] if mid < len(mat_indices) else 0
                primitives.append({
                    'attributes': attrs,
                    'indices': idx_acc,
                    'material': mat_gltf,
                })

            mesh_idx = gltf.add_mesh(model_name, primitives)
            mesh_cache[model_name] = mesh_idx

        mesh_idx = mesh_cache[model_name]

        # Z-up → Y-up position
        px, py, pz = inst.pos_x, inst.pos_z, -inst.pos_y

        # Conjugate quaternion (GTA stores conjugated) + axis swap
        qx, qy, qz, qw = inst.rot_x, inst.rot_y, inst.rot_z, inst.rot_w
        qx, qy, qz = -qx, -qy, -qz
        qx, qy, qz = qx, qz, -qy

        gltf.add_node(
            name=f"{model_name}.dff",
            mesh_idx=mesh_idx,
            translation=(px, py, pz),
            rotation=(qx, qy, qz, qw),
        )
        placed += 1

    if placed == 0:
        return {'placed': 0, 'skipped': skipped, 'meshes': 0}

    try:
        gltf.write_glb(output_path)
    except Exception:
        return {'placed': 0, 'skipped': skipped, 'meshes': len(mesh_cache)}

    return {'placed': placed, 'skipped': skipped, 'meshes': len(mesh_cache)}


# ── CLI ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='DFF → glTF converter')
    parser.add_argument('input', help='.dff file or directory for --batch')
    parser.add_argument('output', nargs='?', help='.glb output file')
    parser.add_argument('--batch', action='store_true', help='Convert all .dff in directory')
    parser.add_argument('--texdir', default='', help='Directory with PNG textures')
    args = parser.parse_args()

    if args.batch:
        tex_dir = args.texdir or os.path.join(args.input, 'textures')
        result = batch_convert(args.input, tex_dir,
                               lambda c, t: print(f'\r{c}/{t}', end=''))
        print(f"\nConverted: {result['converted']}, Skipped: {result['skipped']}")
    else:
        out = args.output or os.path.splitext(args.input)[0] + '.glb'
        if convert_dff_to_glb(args.input, out, args.texdir):
            print(f"OK: {out}")
        else:
            print("FAILED")
            sys.exit(1)
