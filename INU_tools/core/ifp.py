"""
GTA SA IFP (animation) reader/writer.

ANP3 format (SA):
  Header: "ANP3" + size + package_name(24) + padding
  Per animation:
    NAME chunk: animation name
    DGAN chunk: contains INFO + CPAN nodes
    Per bone (CPAN):
      ANIM chunk: bone name(24), type, numKeyFrames, nodeId
      Key data chunk (KR00/KRT0/KRTS):
        KR00 = rotation only (16+4 bytes per key)
        KRT0 = rotation + translation (16+12+4 bytes per key)
        KRTS = rotation + translation + scale (16+12+12+4 bytes per key)
        Rotation: 4 floats (quaternion XYZW)
        Translation: 3 floats (XYZ)
        Scale: 3 floats (XYZ)
        Time: 1 float (seconds)

No Blender dependency — pure Python.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
import struct

HAS_ROT = 1
HAS_TRANS = 2
HAS_SCALE = 4


@dataclass
class KeyFrame:
    """One keyframe for a bone."""
    rotation: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)  # XYZW quat
    translation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    time: float = 0.0


@dataclass
class AnimBone:
    """Animation data for one bone."""
    name: str = ""
    bone_id: int = -1
    key_type: int = HAS_ROT  # HAS_ROT, HAS_TRANS, HAS_SCALE flags
    keyframes: List[KeyFrame] = field(default_factory=list)


@dataclass
class Animation:
    """One animation clip."""
    name: str = ""
    bones: List[AnimBone] = field(default_factory=list)


@dataclass
class IFPFile:
    """Collection of animations from an IFP file."""
    name: str = ""  # Package name
    animations: List[Animation] = field(default_factory=list)


def _roundsize(n: int) -> int:
    """Round up to 4-byte boundary."""
    if n & 3:
        n += 4 - (n & 3)
    return n


def _read_header(data: bytes, offset: int) -> Tuple[str, int, int]:
    """Read IFP chunk header (4-char ident + uint32 size). Returns (ident, size, new_offset)."""
    ident = data[offset:offset + 4].decode('ascii', errors='replace')
    size = struct.unpack_from('<I', data, offset + 4)[0]
    return ident, size, offset + 8


def _read_string(data: bytes, offset: int, length: int) -> str:
    """Read null-terminated string from buffer."""
    raw = data[offset:offset + length]
    null_pos = raw.find(b'\x00')
    if null_pos >= 0:
        raw = raw[:null_pos]
    return raw.decode('ascii', errors='replace')


def _read_anp3_animations(data: bytes, offset: int, num_anims: int) -> List[Animation]:
    """Parse ANP3 flat format — compressed int16 keyframes.

    Per animation:
      name(24) + numBones(4) + dataSize(4) + flag(4) = 36 bytes header
    Per bone:
      name(24) + type(4) + numKeyFrames(4) + boneId(4) = 36 bytes header
      Then keyframe data based on type:
        type 3 (rot only):    4*int16 rot + 1*uint16 time = 10 bytes per key
        type 4 (rot+trans):   4*int16 rot + 1*uint16 time + 3*int16 pos = 16 bytes per key
    Rotation: quaternion XYZW compressed as int16 / 4096.0
    Translation: XYZ compressed as int16 / 1024.0
    Time: uint16 (frame number, convert with /30 for seconds)
    """
    animations = []

    for _a in range(num_anims):
        if offset + 36 > len(data):
            break

        try:
            anim = Animation()
            anim.name = _read_string(data, offset, 24)
            num_bones = struct.unpack_from('<I', data, offset + 24)[0]
            data_size = struct.unpack_from('<I', data, offset + 28)[0]
            anim_flag = struct.unpack_from('<I', data, offset + 32)[0]
            offset += 36

            for _b in range(num_bones):
                if offset + 36 > len(data):
                    break

                bone = AnimBone()
                bone.name = _read_string(data, offset, 24)
                bone_type = struct.unpack_from('<I', data, offset + 24)[0]
                num_kf = struct.unpack_from('<I', data, offset + 28)[0]
                bone.bone_id = struct.unpack_from('<i', data, offset + 32)[0]
                offset += 36

                has_trans = (bone_type == 4)
                bone.key_type = (HAS_ROT | HAS_TRANS) if has_trans else HAS_ROT

                for _k in range(num_kf):
                    kf = KeyFrame()

                    # Rotation: 4 * int16, divide by 4096
                    rx, ry, rz, rw = struct.unpack_from('<4h', data, offset)
                    kf.rotation = (rx / 4096.0, ry / 4096.0, rz / 4096.0, rw / 4096.0)
                    offset += 8

                    # Time: uint16
                    t = struct.unpack_from('<H', data, offset)[0]
                    kf.time = float(t)  # Raw frame number at 30fps
                    offset += 2

                    if has_trans:
                        # Translation: 3 * int16, divide by 1024
                        tx, ty, tz = struct.unpack_from('<3h', data, offset)
                        kf.translation = (tx / 1024.0, ty / 1024.0, tz / 1024.0)
                        offset += 6

                    bone.keyframes.append(kf)

                anim.bones.append(bone)

            animations.append(anim)

        except Exception as e:
            print(f"[IFP] Error at anim #{_a}: {e}")
            break

    return animations


def read_ifp(filepath: str) -> IFPFile:
    """Parse an IFP file and return structured animation data."""
    with open(filepath, 'rb') as f:
        data = f.read()

    result = IFPFile()
    offset = 0

    # Main header: ANP3 or ANLF/ANPK
    ident, size, offset = _read_header(data, offset)

    if ident == 'ANP3':
        # ANP3 format (SA) — flat compressed format (int16 keyframes)
        result.name = _read_string(data, offset, 24)
        num_anims = struct.unpack_from('<I', data, offset + 24)[0]
        offset += 28
        print(f"[IFP] ANP3 package='{result.name}', anims={num_anims}")
        result.animations = _read_anp3_animations(data, offset, num_anims)
        print(f"[IFP] Parsed {len(result.animations)} animations")
        return result

    elif ident == 'ANLF':
        # ANLF container — skip to ANPK
        rounded = _roundsize(size)
        num_packages = struct.unpack_from('<I', data, offset)[0]
        offset += rounded

        # Read first ANPK
        ident, size, offset = _read_header(data, offset)
        if ident != 'ANPK':
            return result

        # INFO inside ANPK
        info_ident, info_size, offset = _read_header(data, offset)
        info_rounded = _roundsize(info_size)
        num_anims = struct.unpack_from('<I', data, offset)[0]
        result.name = _read_string(data, offset + 4, 24)
        offset += info_rounded

    elif ident == 'ANPK':
        # Direct ANPK
        info_ident, info_size, offset = _read_header(data, offset)
        info_rounded = _roundsize(info_size)
        num_anims = struct.unpack_from('<I', data, offset)[0]
        result.name = _read_string(data, offset + 4, 24)
        offset += info_rounded

    else:
        return result

    # Read animations
    for _a in range(num_anims):
        if offset + 8 >= len(data):
            break

        try:
            anim = Animation()

            # NAME chunk
            ch_ident, ch_size, offset = _read_header(data, offset)
            if ch_ident != 'NAME':
                print(f"[IFP] Expected NAME at {offset-8}, got '{ch_ident}', skipping rest")
                break
            ch_rounded = _roundsize(ch_size)
            anim.name = _read_string(data, offset, min(ch_size, 24))
            offset += ch_rounded

            # DGAN chunk
            ch_ident, ch_size, offset = _read_header(data, offset)
            if ch_ident != 'DGAN':
                print(f"[IFP] Expected DGAN for '{anim.name}', got '{ch_ident}', skipping")
                offset += _roundsize(ch_size)
                continue
            dgan_end = offset + _roundsize(ch_size)

            # INFO inside DGAN
            ch_ident, ch_size, offset = _read_header(data, offset)
            info_rounded = _roundsize(ch_size)
            num_bones = struct.unpack_from('<I', data, offset)[0]
            offset += info_rounded

            # Read bones (CPAN chunks)
            for _b in range(num_bones):
                if offset + 8 >= dgan_end:
                    break

                bone = AnimBone()

                # CPAN
                ch_ident, ch_size, offset = _read_header(data, offset)
                cpan_end = offset + _roundsize(ch_size)

                # ANIM inside CPAN
                ch_ident, ch_size, offset = _read_header(data, offset)
                anim_rounded = _roundsize(ch_size)
                anim_data = data[offset:offset + anim_rounded]
                offset += anim_rounded

                bone.name = _read_string(anim_data, 0, 24)
                num_kf = struct.unpack_from('<I', anim_data, 28)[0] if len(anim_data) > 28 else 0
                bone.bone_id = struct.unpack_from('<i', anim_data, 40)[0] if len(anim_data) > 40 else -1

                if num_kf == 0:
                    anim.bones.append(bone)
                    offset = cpan_end
                    continue

                # Key data chunk (KR00 / KRT0 / KRTS)
                ch_ident, ch_size, offset = _read_header(data, offset)

                if ch_ident == 'KR00':
                    bone.key_type = HAS_ROT
                elif ch_ident == 'KRT0':
                    bone.key_type = HAS_ROT | HAS_TRANS
                elif ch_ident == 'KRTS':
                    bone.key_type = HAS_ROT | HAS_TRANS | HAS_SCALE
                else:
                    # Unknown key type, skip this bone
                    anim.bones.append(bone)
                    offset = cpan_end
                    continue

                for _k in range(num_kf):
                    kf = KeyFrame()

                    if bone.key_type & HAS_ROT:
                        qx, qy, qz, qw = struct.unpack_from('<4f', data, offset)
                        kf.rotation = (-qx, -qy, -qz, qw)
                        offset += 16

                    if bone.key_type & HAS_TRANS:
                        tx, ty, tz = struct.unpack_from('<3f', data, offset)
                        kf.translation = (tx, ty, tz)
                        offset += 12

                    if bone.key_type & HAS_SCALE:
                        sx, sy, sz = struct.unpack_from('<3f', data, offset)
                        kf.scale = (sx, sy, sz)
                        offset += 12

                    t = struct.unpack_from('<f', data, offset)[0]
                    kf.time = t
                    offset += 4

                    bone.keyframes.append(kf)

                anim.bones.append(bone)
                offset = cpan_end  # Align after each bone

            offset = dgan_end  # Align after DGAN
            result.animations.append(anim)

        except Exception as e:
            print(f"[IFP] Error reading anim #{_a} '{anim.name if anim else '?'}': {e}")
            break

    print(f"[IFP] Parsed {len(result.animations)} animations")
    return result


def write_ifp(filepath: str, ifp: IFPFile) -> int:
    """Write IFP file. Returns animation count."""
    buf = bytearray()

    def write_header(ident: str, size: int):
        buf.extend(ident.encode('ascii'))
        buf.extend(struct.pack('<I', size))

    def write_padded_string(s: str, length: int):
        encoded = s.encode('ascii', errors='replace')[:length - 1]
        buf.extend(encoded)
        buf.extend(b'\x00' * (length - len(encoded)))

    # Calculate total size for ANP3 header
    # We'll write everything to buffer first, then prepend header

    # Build animation data
    anim_buf = bytearray()

    for anim in ifp.animations:
        # NAME chunk
        name_data = bytearray(28)
        name_bytes = anim.name.encode('ascii', errors='replace')[:23]
        name_data[:len(name_bytes)] = name_bytes
        name_chunk = bytearray()
        name_chunk.extend(b'NAME')
        name_chunk.extend(struct.pack('<I', 28))
        name_chunk.extend(name_data)

        # Build DGAN content
        dgan_content = bytearray()

        # INFO inside DGAN
        info_data = struct.pack('<II', len(anim.bones), 0)
        dgan_content.extend(b'INFO')
        dgan_content.extend(struct.pack('<I', len(info_data)))
        dgan_content.extend(info_data)

        for bone in anim.bones:
            # ANIM data (inside CPAN)
            anim_data = bytearray(48)
            bone_name = bone.name.encode('ascii', errors='replace')[:23]
            anim_data[:len(bone_name)] = bone_name
            struct.pack_into('<I', anim_data, 28, len(bone.keyframes))
            struct.pack_into('<i', anim_data, 40, bone.bone_id)
            struct.pack_into('<i', anim_data, 44, -1)

            cpan_content = bytearray()
            cpan_content.extend(b'ANIM')
            cpan_content.extend(struct.pack('<I', len(anim_data)))
            cpan_content.extend(anim_data)

            if bone.keyframes:
                # Key data
                key_data = bytearray()
                for kf in bone.keyframes:
                    if bone.key_type & HAS_ROT:
                        key_data.extend(struct.pack('<4f',
                                                     -kf.rotation[0], -kf.rotation[1],
                                                     -kf.rotation[2], kf.rotation[3]))
                    if bone.key_type & HAS_TRANS:
                        key_data.extend(struct.pack('<3f', *kf.translation))
                    if bone.key_type & HAS_SCALE:
                        key_data.extend(struct.pack('<3f', *kf.scale))
                    key_data.extend(struct.pack('<f', kf.time))

                if bone.key_type == HAS_ROT:
                    key_ident = b'KR00'
                elif bone.key_type == (HAS_ROT | HAS_TRANS):
                    key_ident = b'KRT0'
                else:
                    key_ident = b'KRTS'

                cpan_content.extend(key_ident)
                cpan_content.extend(struct.pack('<I', len(key_data)))
                cpan_content.extend(key_data)

            dgan_content.extend(b'CPAN')
            dgan_content.extend(struct.pack('<I', len(cpan_content)))
            dgan_content.extend(cpan_content)

        anim_buf.extend(name_chunk)
        anim_buf.extend(b'DGAN')
        anim_buf.extend(struct.pack('<I', len(dgan_content)))
        anim_buf.extend(dgan_content)

    # ANP3 header
    header_data = bytearray(28)
    pkg_name = ifp.name.encode('ascii', errors='replace')[:23]
    header_data[:len(pkg_name)] = pkg_name
    struct.pack_into('<I', header_data, 24, len(ifp.animations))

    write_header('ANP3', len(header_data) + len(anim_buf))
    buf.extend(header_data)
    buf.extend(anim_buf)

    with open(filepath, 'wb') as f:
        f.write(buf)

    return len(ifp.animations)
