"""
GTA SA IMG v2 archive reader/writer.

Format:
  Header:  "VER2" (4 bytes) + num_entries (uint32 LE)
  Directory: num_entries × 32 bytes:
      offset  (uint32 LE)  — sector offset (sector = 2048 bytes)
      size    (uint32 LE)  — file size in sectors
      name    (24 bytes)   — null-padded ASCII filename
  Data: files stored at sector-aligned offsets.

No Blender dependency — pure Python.
"""

from __future__ import annotations
import os
import struct
from dataclasses import dataclass

SECTOR = 2048
MAGIC = b'VER2'
DIR_ENTRY_SIZE = 32
NAME_SIZE = 24


@dataclass
class ImgEntry:
    """One file entry in an IMG archive."""
    name: str
    offset: int   # sector offset
    size: int     # size in sectors


def sectors_needed(byte_size: int) -> int:
    """Number of 2048-byte sectors needed to store *byte_size* bytes."""
    return (byte_size + SECTOR - 1) // SECTOR


# ── Reading ─────────────────────────────────────────────────────────

def read_directory(filepath: str) -> list[ImgEntry]:
    """Read the directory of an IMG v2 archive."""
    entries = []
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        if magic != MAGIC:
            raise ValueError(f"Not a VER2 IMG archive (got {magic!r})")
        num = struct.unpack('<I', f.read(4))[0]
        for _ in range(num):
            raw = f.read(DIR_ENTRY_SIZE)
            if len(raw) < DIR_ENTRY_SIZE:
                break
            off, sz = struct.unpack_from('<II', raw, 0)
            name_bytes = raw[8:8 + NAME_SIZE]
            name = name_bytes.split(b'\x00', 1)[0].decode('ascii', errors='replace')
            entries.append(ImgEntry(name=name, offset=off, size=sz))
    return entries


def extract_file(img_path: str, entry_name: str) -> bytes | None:
    """Extract a single file from an IMG archive by name."""
    entries = read_directory(img_path)
    for e in entries:
        if e.name.lower() == entry_name.lower():
            with open(img_path, 'rb') as f:
                f.seek(e.offset * SECTOR)
                return f.read(e.size * SECTOR)
    return None


class ImgReader:
    """Keeps IMG file open for fast sequential/random reads.
    Use as context manager for automatic cleanup.

    Usage:
        with ImgReader("gta3.img") as img:
            data = img.read("building01.dff")
            img.extract_all_to(output_dir)  # batch extract
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._f = None
        self._entries: list[ImgEntry] = []
        self._lookup: dict[str, ImgEntry] = {}

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def open(self):
        self._f = open(self.filepath, 'rb')
        magic = self._f.read(4)
        if magic != MAGIC:
            self._f.close()
            raise ValueError(f"Not a VER2 IMG archive (got {magic!r})")
        num = struct.unpack('<I', self._f.read(4))[0]
        self._entries = []
        self._lookup = {}
        for _ in range(num):
            raw = self._f.read(DIR_ENTRY_SIZE)
            if len(raw) < DIR_ENTRY_SIZE:
                break
            off, sz = struct.unpack_from('<II', raw, 0)
            name_bytes = raw[8:8 + NAME_SIZE]
            name = name_bytes.split(b'\x00', 1)[0].decode('ascii', errors='replace')
            entry = ImgEntry(name=name, offset=off, size=sz)
            self._entries.append(entry)
            self._lookup[name.lower()] = entry

    def close(self):
        if self._f:
            self._f.close()
            self._f = None

    @property
    def entries(self) -> list[ImgEntry]:
        return self._entries

    def read(self, entry_name: str) -> bytes | None:
        """Read a single file by name (fast — no directory re-read)."""
        e = self._lookup.get(entry_name.lower())
        if not e:
            return None
        self._f.seek(e.offset * SECTOR)
        return self._f.read(e.size * SECTOR)

    def extract_all_to(self, output_dir: str,
                       extensions: set[str] | None = None,
                       skip_existing: bool = True) -> dict[str, int]:
        """Batch extract files to output_dir in one sequential pass.

        Args:
            output_dir: directory to write files to
            extensions: set of extensions to extract (e.g. {'.dff', '.col'}),
                       None = extract all
            skip_existing: skip files that already exist on disk

        Returns dict with counts: {'dff': N, 'col': N, 'txd': N, 'other': N, 'skipped': N}
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        # Sort entries by offset for sequential disk read
        sorted_entries = sorted(self._entries, key=lambda e: e.offset)

        counts = {'dff': 0, 'col': 0, 'txd': 0, 'other': 0, 'skipped': 0}

        for entry in sorted_entries:
            low = entry.name.lower()
            ext = '.' + low.rsplit('.', 1)[-1] if '.' in low else ''

            if extensions and ext not in extensions:
                continue

            out_path = os.path.join(output_dir, entry.name)
            if skip_existing and os.path.isfile(out_path):
                counts['skipped'] += 1
                continue

            self._f.seek(entry.offset * SECTOR)
            data = self._f.read(entry.size * SECTOR)

            # Trim padding (sector-aligned, may have trailing zeros)
            with open(out_path, 'wb') as out:
                out.write(data)

            if ext == '.dff':
                counts['dff'] += 1
            elif ext == '.col':
                counts['col'] += 1
            elif ext == '.txd':
                counts['txd'] += 1
            else:
                counts['other'] += 1

        return counts


# ── Writing / Replacing ────────────────────────────────────────────

def replace_or_add(img_path: str, filename: str, data: bytes) -> str:
    """
    Replace or add a file in an IMG v2 archive.

    - If *filename* already exists and the new data fits in the old slot,
      overwrite in place.
    - If new data is larger or file doesn't exist, append at the end.
    - Directory is always rewritten.

    Returns status string: 'replaced' or 'added'.
    """
    entries = read_directory(img_path)
    new_sectors = sectors_needed(len(data))
    # Pad data to sector boundary
    padded = data + b'\x00' * (new_sectors * SECTOR - len(data))

    status = 'added'
    target_entry = None

    # Check if file exists
    for e in entries:
        if e.name.lower() == filename.lower():
            target_entry = e
            break

    with open(img_path, 'r+b') as f:
        if target_entry and new_sectors <= target_entry.size:
            # Fits in existing slot — overwrite in place
            f.seek(target_entry.offset * SECTOR)
            f.write(padded)
            target_entry.size = new_sectors
            status = 'replaced'
        else:
            # Append at end of file
            f.seek(0, 2)  # seek to end
            end_pos = f.tell()
            # Align to sector boundary
            end_sector = sectors_needed(end_pos)
            if end_pos < end_sector * SECTOR:
                f.write(b'\x00' * (end_sector * SECTOR - end_pos))
                end_pos = end_sector * SECTOR

            f.seek(end_pos)
            f.write(padded)

            new_offset = end_pos // SECTOR

            if target_entry:
                # Update existing entry to point to new location
                target_entry.offset = new_offset
                target_entry.size = new_sectors
                status = 'replaced'
            else:
                # Add new entry
                entries.append(ImgEntry(
                    name=filename,
                    offset=new_offset,
                    size=new_sectors,
                ))
                status = 'added'

        # Rewrite header + directory
        _write_directory(f, entries)

    return status


def remove_file(img_path: str, filename: str) -> bool:
    """
    Remove a file entry from the directory (data stays, space is wasted).
    Returns True if removed.
    """
    entries = read_directory(img_path)
    new_entries = [e for e in entries if e.name.lower() != filename.lower()]
    if len(new_entries) == len(entries):
        return False

    with open(img_path, 'r+b') as f:
        _write_directory(f, new_entries)
    return True


def _write_directory(f, entries: list[ImgEntry]) -> None:
    """Rewrite the VER2 header and directory in-place."""
    f.seek(0)
    f.write(MAGIC)
    f.write(struct.pack('<I', len(entries)))
    for e in entries:
        name_bytes = e.name.encode('ascii', errors='replace')[:NAME_SIZE]
        name_bytes = name_bytes.ljust(NAME_SIZE, b'\x00')
        f.write(struct.pack('<II', e.offset, e.size))
        f.write(name_bytes)


def create_img(filepath: str) -> None:
    """Create an empty VER2 IMG archive."""
    with open(filepath, 'wb') as f:
        f.write(MAGIC)
        f.write(struct.pack('<I', 0))


def list_files(img_path: str) -> list[str]:
    """Return list of filenames in the archive."""
    return [e.name for e in read_directory(img_path)]


