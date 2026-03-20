# INU_tools.core.rwbinary
# Low-level binary read/write helpers for GTA RenderWare formats.
# Pure Python, no Blender dependency.
#
# Based on public RenderWare format specifications.

from struct import pack, unpack_from, calcsize


class BinaryReader:
    """Sequential binary reader with position tracking."""

    __slots__ = ('data', 'pos')

    def __init__(self, data: bytes, pos: int = 0):
        self.data = data
        self.pos = pos

    @classmethod
    def from_file(cls, filepath: str):
        with open(filepath, 'rb') as f:
            return cls(f.read())

    # -- primitives --

    def read(self, fmt: str):
        """Unpack struct format at current position and advance."""
        result = unpack_from(fmt, self.data, self.pos)
        self.pos += calcsize(fmt)
        return result

    def read_one(self, fmt: str):
        """Unpack a single value."""
        return self.read(fmt)[0]

    def read_bytes(self, count: int) -> bytes:
        result = self.data[self.pos:self.pos + count]
        self.pos += count
        return result

    def read_float(self) -> float:
        return self.read_one('<f')

    def read_u8(self) -> int:
        return self.read_one('<B')

    def read_u16(self) -> int:
        return self.read_one('<H')

    def read_i16(self) -> int:
        return self.read_one('<h')

    def read_u32(self) -> int:
        return self.read_one('<I')

    def read_vec3(self) -> tuple:
        return self.read('<3f')

    def skip(self, count: int):
        self.pos += count

    def seek(self, pos: int):
        self.pos = pos

    def remaining(self) -> int:
        return len(self.data) - self.pos

    # -- strings --

    def read_str(self, max_len: int) -> str:
        """Read a fixed-size null-terminated ASCII string."""
        raw = self.read_bytes(max_len)
        end = raw.find(b'\x00')
        if end == -1:
            end = max_len
        return raw[:end].decode('ascii', errors='replace')


class BinaryWriter:
    """Sequential binary writer that builds a bytes buffer."""

    __slots__ = ('_parts',)

    def __init__(self):
        self._parts = []

    def write(self, fmt: str, *values):
        self._parts.append(pack(fmt, *values))

    def write_bytes(self, data: bytes):
        self._parts.append(data)

    def write_float(self, v: float):
        self.write('<f', v)

    def write_u8(self, v: int):
        self.write('<B', v)

    def write_u16(self, v: int):
        self.write('<H', v)

    def write_i16(self, v: int):
        self.write('<h', v)

    def write_u32(self, v: int):
        self.write('<I', v)

    def write_vec3(self, x: float, y: float, z: float):
        self.write('<3f', x, y, z)

    def write_str(self, s: str, max_len: int):
        """Write a fixed-size null-padded ASCII string."""
        encoded = s.encode('ascii', errors='replace')[:max_len]
        padded = encoded + b'\x00' * (max_len - len(encoded))
        self.write_bytes(padded)

    def to_bytes(self) -> bytes:
        return b''.join(self._parts)

    def __len__(self) -> int:
        return sum(len(p) for p in self._parts)

    def to_file(self, filepath: str):
        with open(filepath, 'wb') as f:
            f.write(self.to_bytes())
