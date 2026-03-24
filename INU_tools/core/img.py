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
