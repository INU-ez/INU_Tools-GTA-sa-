"""
GTA III / VC / SA IMG archive reader/writer.

Two on-disk formats:

* **VER1** (GTA III + Vice City) — split:
    - ``gta3.dir`` (directory only): num_entries × 32-byte records, no header
    - ``gta3.img`` (raw data): files at sector-aligned offsets, no header
  Reader auto-pairs by basename: a ``.img`` next to a same-named ``.dir``
  is treated as VER1.

* **VER2** (San Andreas) — single file:
    - Header: ``"VER2"`` (4 bytes) + num_entries (uint32 LE)
    - Directory: num_entries × 32 bytes (offset, size, name)
    - Data: files at sector-aligned offsets.

Directory record layout is identical between versions — only the
location of the directory differs (inline vs sibling file).

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

# Img-archive version IDs (also used in core.game_versions.GameProfile.img_version).
IMG_VERSION_1 = 1   # III / VC: split .dir + .img
IMG_VERSION_2 = 2   # SA: single .img with embedded header + directory


def _sibling_dir_path(img_path: str) -> str:
    """Return the ``.dir`` path that pairs with the given ``.img``.
    Strips the trailing extension and replaces with ``.dir`` — case is
    preserved on the suffix so vanilla ``gta3.img`` ↔ ``gta3.dir``
    round-trips on case-sensitive filesystems."""
    base, _ext = os.path.splitext(img_path)
    return base + '.dir'


def detect_img_version(filepath: str) -> int:
    """Return ``IMG_VERSION_1`` or ``IMG_VERSION_2`` for the given path.

    Probe order:
      1. First 4 bytes == ``b'VER2'`` → VER2
      2. Sibling ``.dir`` file exists → VER1
      3. Otherwise → fall back to VER2 (most common; the caller's
         downstream ``read_directory`` will raise a clear error if the
         header turns out to be malformed)
    """
    try:
        with open(filepath, 'rb') as f:
            head = f.read(4)
    except OSError:
        return IMG_VERSION_2
    if head == MAGIC:
        return IMG_VERSION_2
    if os.path.isfile(_sibling_dir_path(filepath)):
        return IMG_VERSION_1
    return IMG_VERSION_2


# Filename sanitization for entry/texture names extracted from corrupt
# archives. Non-ASCII bytes get replaced with `?` during ascii-decode,
# and `?` is invalid on Windows; the rest of this set covers POSIX/NTFS
# reserved characters. Real GTA SA archives never need this — it only
# fires when a TXD/IMG was hand-edited with garbage bytes.
_FILENAME_INVALID = '<>:"/\\|?*\x00'


def safe_filename(name: str) -> str:
    """Replace filesystem-invalid characters with underscore."""
    return ''.join('_' if c in _FILENAME_INVALID else c for c in name).strip()


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

def _parse_dir_records(raw: bytes) -> list[ImgEntry]:
    """Decode N × 32-byte directory records into ``ImgEntry`` objects.
    Used for both formats — VER2 reads from inside the .img after the
    8-byte header, VER1 reads from the entire .dir file."""
    entries = []
    n = len(raw) // DIR_ENTRY_SIZE
    for i in range(n):
        rec = raw[i * DIR_ENTRY_SIZE : (i + 1) * DIR_ENTRY_SIZE]
        off, sz = struct.unpack_from('<II', rec, 0)
        name_bytes = rec[8:8 + NAME_SIZE]
        name = name_bytes.split(b'\x00', 1)[0].decode('ascii', errors='replace')
        entries.append(ImgEntry(name=name, offset=off, size=sz))
    return entries


def read_directory(filepath: str) -> list[ImgEntry]:
    """Read the directory of an IMG archive — version auto-detected.

    For VER2, the directory is embedded at the top of the ``.img`` file.
    For VER1, it lives in a sibling ``.dir`` (same basename).
    """
    version = detect_img_version(filepath)
    if version == IMG_VERSION_1:
        dir_path = _sibling_dir_path(filepath)
        with open(dir_path, 'rb') as f:
            return _parse_dir_records(f.read())

    # VER2 — magic header + count + inline directory.
    entries = []
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        if magic != MAGIC:
            raise ValueError(f"Not a VER2 IMG archive (got {magic!r}). "
                             "No sibling .dir found either — file is "
                             "neither VER1 nor VER2.")
        num = struct.unpack('<I', f.read(4))[0]
        raw = f.read(num * DIR_ENTRY_SIZE)
        entries.extend(_parse_dir_records(raw))
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
        self.version = IMG_VERSION_2
        self._f = None
        self._entries: list[ImgEntry] = []
        self._lookup: dict[str, ImgEntry] = {}

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def open(self):
        # Detect version BEFORE opening — for VER1 the directory lives
        # in a sibling .dir file, not inside the .img we'll be reading
        # data from.
        self.version = detect_img_version(self.filepath)
        self._entries = []
        self._lookup = {}

        if self.version == IMG_VERSION_1:
            # VER1: parse the sibling .dir first; keep the .img open
            # for random-access data reads.
            dir_path = _sibling_dir_path(self.filepath)
            with open(dir_path, 'rb') as df:
                raw = df.read()
            self._entries = _parse_dir_records(raw)
            self._f = open(self.filepath, 'rb')
        else:
            # VER2: magic + count + inline directory in one file.
            self._f = open(self.filepath, 'rb')
            magic = self._f.read(4)
            if magic != MAGIC:
                self._f.close()
                raise ValueError(f"Not a VER2 IMG archive (got {magic!r})")
            num = struct.unpack('<I', self._f.read(4))[0]
            raw = self._f.read(num * DIR_ENTRY_SIZE)
            self._entries = _parse_dir_records(raw)

        for entry in self._entries:
            self._lookup[entry.name.lower()] = entry

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
                       skip_existing: bool = True,
                       name_filter=None) -> dict[str, int]:
        """Batch extract files to output_dir in one sequential pass.

        Args:
            output_dir: directory to write files to
            extensions: set of extensions to extract (e.g. {'.dff', '.col'}),
                       None = extract all
            skip_existing: skip files that already exist on disk
            name_filter: optional callable ``(lower_name: str) -> bool`` —
                       only entries where the filter returns True are
                       extracted. Lets callers narrow down by base name
                       (e.g. region-filtered TXD subsets) while still
                       benefiting from the sorted-by-offset pass.

        Returns dict with counts: {'dff': N, 'col': N, 'txd': N, 'other': N, 'skipped': N}
        """
        os.makedirs(output_dir, exist_ok=True)

        # Sort entries by offset for sequential disk read
        sorted_entries = sorted(self._entries, key=lambda e: e.offset)

        counts = {'dff': 0, 'col': 0, 'txd': 0, 'other': 0, 'skipped': 0}

        for entry in sorted_entries:
            low = entry.name.lower()
            ext = '.' + low.rsplit('.', 1)[-1] if '.' in low else ''

            if extensions and ext not in extensions:
                continue
            if name_filter is not None and not name_filter(low):
                continue

            out_path = os.path.join(output_dir, safe_filename(entry.name))
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


def _encode_directory_records(entries: list[ImgEntry]) -> bytes:
    """Serialise entries to the 32-bytes-per-record on-disk form. Used
    for both VER1 (full .dir contents) and VER2 (in-place at top of .img)."""
    out = bytearray()
    for e in entries:
        name_bytes = e.name.encode('ascii', errors='replace')[:NAME_SIZE]
        name_bytes = name_bytes.ljust(NAME_SIZE, b'\x00')
        out += struct.pack('<II', e.offset, e.size)
        out += name_bytes
    return bytes(out)


def _write_directory(f, entries: list[ImgEntry]) -> None:
    """Rewrite the VER2 header and directory in-place at the top of
    the IMG file. VER1 doesn't use this — its .dir is a separate file
    written by ImgWriter on close."""
    f.seek(0)
    f.write(MAGIC)
    f.write(struct.pack('<I', len(entries)))
    f.write(_encode_directory_records(entries))


def _write_dir_file(dir_path: str, entries: list[ImgEntry]) -> None:
    """Write VER1's sibling .dir file (just concatenated 32-byte
    records, no header)."""
    with open(dir_path, 'wb') as f:
        f.write(_encode_directory_records(entries))


class ImgWriter:
    """Batch-mode IMG archive writer — context manager.

    Opens the IMG once, loads the directory once, appends/replaces many
    files, then rewrites the directory ONCE at close. Cuts the cost of
    big exports from O(N × directory-size) writes to O(N + directory-size).

    Typical use:

        with ImgWriter("gta3.img") as w:
            for group in groups:
                w.add("house1.dff", dff_bytes)
                w.add("house1.col", col_bytes)
                w.add("house1.txd", txd_bytes)
        # Directory was rewritten exactly once on exit.

    Compatible semantics with ``replace_or_add``:
    - If the file exists and new data fits in the old slot → overwrite
      in place
    - If it doesn't fit or the file is new → append at the end
    - Directory entry is updated accordingly and flushed at close.
    """

    def __init__(self, filepath: str, *, version: int | None = None):
        """Open or create an IMG archive for batch writes.

        ``version`` — 1 (VER1, III/VC: split .dir + .img) or 2 (VER2,
        SA: single .img). Default ``None`` means auto-detect from the
        existing file (or fall back to VER2 for new archives).
        """
        self.filepath = filepath
        self.version = version
        self._f = None
        self._entries: list[ImgEntry] = []
        self._lookup: dict[str, int] = {}
        self._end_pos: int = 0

    def __enter__(self):
        # Auto-detect version when not pinned by caller. We do this BEFORE
        # opening so the right read path (embedded vs sibling .dir) is
        # taken.
        if self.version is None:
            if os.path.isfile(self.filepath):
                self.version = detect_img_version(self.filepath)
            else:
                self.version = IMG_VERSION_2

        if self.version == IMG_VERSION_1:
            # VER1: directory lives in sibling .dir. Data file (.img)
            # is plain raw — no header to consume. Append-pointer (
            # ``_end_pos``) starts at the file's current EOF, which is
            # 0 for a freshly created archive.
            dir_path = _sibling_dir_path(self.filepath)
            # Create the .img if missing, then open r+b.
            if not os.path.isfile(self.filepath):
                open(self.filepath, 'wb').close()
            self._f = open(self.filepath, 'r+b')
            if os.path.isfile(dir_path):
                with open(dir_path, 'rb') as df:
                    raw = df.read()
                for i, e in enumerate(_parse_dir_records(raw)):
                    self._entries.append(e)
                    self._lookup[e.name.lower()] = i
            self._f.seek(0, 2)
            self._end_pos = self._f.tell()
            return self

        # VER2 — single-file with embedded header + directory at top.
        # If the file doesn't exist we initialise an empty VER2 header
        # so the append path below has a valid file to work with.
        if not os.path.isfile(self.filepath):
            create_img(self.filepath)
        self._f = open(self.filepath, 'r+b')
        magic = self._f.read(4)
        if magic != MAGIC:
            self._f.close()
            self._f = None
            raise ValueError(f"Not a VER2 IMG archive (got {magic!r})")
        num = struct.unpack('<I', self._f.read(4))[0]
        for _ in range(num):
            raw = self._f.read(DIR_ENTRY_SIZE)
            if len(raw) < DIR_ENTRY_SIZE:
                break
            off, sz = struct.unpack_from('<II', raw, 0)
            name_bytes = raw[8:8 + NAME_SIZE]
            name = name_bytes.split(b'\x00', 1)[0].decode(
                'ascii', errors='replace')
            self._entries.append(ImgEntry(name=name, offset=off, size=sz))
            self._lookup[name.lower()] = len(self._entries) - 1
        # Remember current EOF so append operations don't have to
        # seek-to-end every time (which costs a syscall).
        self._f.seek(0, 2)
        self._end_pos = self._f.tell()
        return self

    def add(self, filename: str, data: bytes) -> str:
        """Add or replace one file. Returns ``'added'`` or ``'replaced'``."""
        if self._f is None:
            raise RuntimeError("ImgWriter used outside its 'with' block")

        new_sectors = sectors_needed(len(data))
        padded = data + b'\x00' * (new_sectors * SECTOR - len(data))

        idx = self._lookup.get(filename.lower())
        if idx is not None and new_sectors <= self._entries[idx].size:
            # In-place — cheapest path.
            e = self._entries[idx]
            self._f.seek(e.offset * SECTOR)
            self._f.write(padded)
            e.size = new_sectors
            return 'replaced'

        # Append path — align end to sector boundary.
        end_sector = sectors_needed(self._end_pos)
        aligned = end_sector * SECTOR
        if self._end_pos < aligned:
            self._f.seek(self._end_pos)
            self._f.write(b'\x00' * (aligned - self._end_pos))
            self._end_pos = aligned
        self._f.seek(self._end_pos)
        self._f.write(padded)
        new_offset = self._end_pos // SECTOR
        self._end_pos += new_sectors * SECTOR

        if idx is not None:
            self._entries[idx].offset = new_offset
            self._entries[idx].size = new_sectors
            return 'replaced'
        self._entries.append(ImgEntry(
            name=filename, offset=new_offset, size=new_sectors))
        self._lookup[filename.lower()] = len(self._entries) - 1
        return 'added'

    def __exit__(self, *args):
        if self._f is not None:
            try:
                if self.version == IMG_VERSION_1:
                    # VER1: directory in sibling .dir, .img holds only data.
                    _write_dir_file(_sibling_dir_path(self.filepath),
                                    self._entries)
                else:
                    _write_directory(self._f, self._entries)
            finally:
                self._f.close()
                self._f = None


def create_img(filepath: str, *, version: int = IMG_VERSION_2) -> None:
    """Create an empty IMG archive.

    VER2 (SA): single ``.img`` with ``VER2`` magic + zero count.
    VER1 (III/VC): empty ``.img`` data file plus empty ``.dir`` next
    to it — the data file has no header, the directory file is also
    initially empty.
    """
    if version == IMG_VERSION_1:
        # Empty .img (raw data, no header) + empty .dir (no records).
        open(filepath, 'wb').close()
        open(_sibling_dir_path(filepath), 'wb').close()
        return
    with open(filepath, 'wb') as f:
        f.write(MAGIC)
        f.write(struct.pack('<I', 0))


def list_files(img_path: str) -> list[str]:
    """Return list of filenames in the archive."""
    return [e.name for e in read_directory(img_path)]


