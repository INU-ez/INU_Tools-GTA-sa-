"""Round-trip tests for core/img.py — IMG v2 archive create/add/replace/
remove/extract via batch ImgWriter and one-shot replace_or_add.

Pure Python."""

from pathlib import Path
import sys
import os


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.img import (  # noqa: E402
    SECTOR,
    create_img,
    list_files,
    read_directory,
    extract_file,
    replace_or_add,
    remove_file,
    sectors_needed,
    ImgReader,
    ImgWriter,
)


def _make_payload(size: int, fill: bytes = b'X') -> bytes:
    return (fill * size)[:size]


# ── sectors_needed math ──────────────────────────────────────────

def test_sectors_needed_round_up():
    assert sectors_needed(0) == 0
    assert sectors_needed(1) == 1
    assert sectors_needed(SECTOR) == 1
    assert sectors_needed(SECTOR + 1) == 2
    assert sectors_needed(2 * SECTOR) == 2


# ── Empty archive ────────────────────────────────────────────────

def test_create_empty(tmp_path):
    p = tmp_path / "empty.img"
    create_img(str(p))
    assert p.exists()
    assert read_directory(str(p)) == []
    assert list_files(str(p)) == []


# ── Single-file add via replace_or_add ───────────────────────────

def test_add_single_file(tmp_path):
    p = tmp_path / "one.img"
    create_img(str(p))
    payload = _make_payload(500, fill=b'A')
    status = replace_or_add(str(p), "test.dff", payload)
    assert status == 'added'

    files = list_files(str(p))
    assert len(files) == 1
    assert files[0].lower() == "test.dff"

    # Extract back, strip padding, compare
    extracted = extract_file(str(p), "test.dff")
    assert extracted is not None
    assert extracted[:500] == payload  # padding may follow


# ── Replace in place (fits in old slot) ──────────────────────────

def test_replace_in_place(tmp_path):
    p = tmp_path / "rep.img"
    create_img(str(p))
    replace_or_add(str(p), "data.col", _make_payload(SECTOR * 3, fill=b'A'))

    # New data fits — should reuse existing sectors
    new_data = _make_payload(SECTOR * 2, fill=b'B')
    status = replace_or_add(str(p), "data.col", new_data)
    assert status == 'replaced'

    extracted = extract_file(str(p), "data.col")
    assert extracted is not None
    assert extracted[:len(new_data)] == new_data


# ── Replace overflow (forces append) ─────────────────────────────

def test_replace_overflow_appends(tmp_path):
    p = tmp_path / "over.img"
    create_img(str(p))
    replace_or_add(str(p), "small.dff", _make_payload(100, fill=b'A'))

    # New data doesn't fit — must append
    bigger = _make_payload(SECTOR * 4, fill=b'B')
    status = replace_or_add(str(p), "small.dff", bigger)
    assert status == 'replaced'

    extracted = extract_file(str(p), "small.dff")
    assert extracted is not None
    assert extracted[:len(bigger)] == bigger


# ── Remove file ──────────────────────────────────────────────────

def test_remove_file(tmp_path):
    p = tmp_path / "rm.img"
    create_img(str(p))
    replace_or_add(str(p), "a.dff", _make_payload(100, fill=b'A'))
    replace_or_add(str(p), "b.dff", _make_payload(200, fill=b'B'))
    replace_or_add(str(p), "c.dff", _make_payload(300, fill=b'C'))

    assert remove_file(str(p), "b.dff") is True
    files = {n.lower() for n in list_files(str(p))}
    assert "a.dff" in files
    assert "b.dff" not in files
    assert "c.dff" in files


def test_remove_nonexistent_returns_false(tmp_path):
    p = tmp_path / "miss.img"
    create_img(str(p))
    assert remove_file(str(p), "nothing.dff") is False


# ── Case-insensitive lookup ──────────────────────────────────────

def test_case_insensitive_lookup(tmp_path):
    p = tmp_path / "case.img"
    create_img(str(p))
    replace_or_add(str(p), "House01.DFF", _make_payload(100, fill=b'X'))

    assert extract_file(str(p), "house01.dff") is not None
    assert extract_file(str(p), "HOUSE01.DFF") is not None


# ── ImgReader context manager ────────────────────────────────────

def test_reader_keeps_archive_open(tmp_path):
    p = tmp_path / "reader.img"
    create_img(str(p))
    replace_or_add(str(p), "a.dff", _make_payload(100, fill=b'A'))
    replace_or_add(str(p), "b.dff", _make_payload(200, fill=b'B'))

    with ImgReader(str(p)) as r:
        assert len(r.entries) == 2
        a = r.read("a.dff")
        b = r.read("b.dff")
        assert a is not None and a[:100] == b'A' * 100
        assert b is not None and b[:200] == b'B' * 200
        # Missing returns None, not exception
        assert r.read("ghost.dff") is None


def test_reader_extract_all_to_dir(tmp_path):
    p = tmp_path / "batch.img"
    create_img(str(p))
    replace_or_add(str(p), "a.dff", _make_payload(100, fill=b'A'))
    replace_or_add(str(p), "b.col", _make_payload(200, fill=b'B'))
    replace_or_add(str(p), "c.txd", _make_payload(300, fill=b'C'))
    replace_or_add(str(p), "d.bin", _make_payload(50, fill=b'D'))

    out = tmp_path / "extracted"
    with ImgReader(str(p)) as r:
        counts = r.extract_all_to(str(out))

    assert counts['dff'] == 1
    assert counts['col'] == 1
    assert counts['txd'] == 1
    assert counts['other'] == 1
    assert (out / "a.dff").exists()
    assert (out / "b.col").exists()


def test_reader_extract_filtered_by_extension(tmp_path):
    p = tmp_path / "filt.img"
    create_img(str(p))
    replace_or_add(str(p), "a.dff", _make_payload(100, fill=b'A'))
    replace_or_add(str(p), "b.col", _make_payload(200, fill=b'B'))
    replace_or_add(str(p), "c.txd", _make_payload(300, fill=b'C'))

    out = tmp_path / "dffonly"
    with ImgReader(str(p)) as r:
        counts = r.extract_all_to(str(out), extensions={'.dff'})

    assert counts['dff'] == 1
    assert counts['col'] == 0
    assert counts['txd'] == 0
    assert (out / "a.dff").exists()
    assert not (out / "b.col").exists()


# ── ImgWriter batch mode ─────────────────────────────────────────

def test_writer_batch_add(tmp_path):
    """Writer should write directory exactly once at __exit__, not per-add."""
    p = tmp_path / "batch.img"
    create_img(str(p))

    with ImgWriter(str(p)) as w:
        for i in range(20):
            w.add(f"file{i:02d}.dff", _make_payload(100 + i, fill=bytes([0x40 + i])))

    files = list_files(str(p))
    assert len(files) == 20
    # Verify a few survived intact
    assert extract_file(str(p), "file00.dff")[:100] == b'@' * 100
    assert extract_file(str(p), "file19.dff")[:119] == bytes([0x40 + 19]) * 119


def test_writer_replace_and_add_mixed(tmp_path):
    """First populate, then re-open with writer to replace some + add new."""
    p = tmp_path / "mixed.img"
    create_img(str(p))
    replace_or_add(str(p), "old1.dff", _make_payload(SECTOR * 3, fill=b'A'))
    replace_or_add(str(p), "old2.dff", _make_payload(SECTOR * 3, fill=b'B'))

    with ImgWriter(str(p)) as w:
        # Replace fits in slot
        w.add("old1.dff", _make_payload(SECTOR, fill=b'X'))
        # Replace overflows
        w.add("old2.dff", _make_payload(SECTOR * 5, fill=b'Y'))
        # Net new
        w.add("new1.dff", _make_payload(100, fill=b'Z'))

    files = {n.lower() for n in list_files(str(p))}
    assert files == {"old1.dff", "old2.dff", "new1.dff"}

    assert extract_file(str(p), "old1.dff")[:SECTOR] == b'X' * SECTOR
    assert extract_file(str(p), "old2.dff")[:SECTOR * 5] == b'Y' * (SECTOR * 5)
    assert extract_file(str(p), "new1.dff")[:100] == b'Z' * 100


# ── Directory layout invariants ──────────────────────────────────

def test_directory_offsets_are_sector_aligned(tmp_path):
    p = tmp_path / "align.img"
    create_img(str(p))
    for i in range(5):
        replace_or_add(str(p), f"f{i}.dff", _make_payload(SECTOR + 17 + i,
                                                          fill=bytes([0x60 + i])))

    entries = read_directory(str(p))
    assert len(entries) == 5
    # No entry overlaps the next entry's start
    sorted_e = sorted(entries, key=lambda e: e.offset)
    for prev, nxt in zip(sorted_e, sorted_e[1:]):
        assert prev.offset + prev.size <= nxt.offset, (
            f"{prev.name} overlaps {nxt.name}: "
            f"{prev.offset}+{prev.size} > {nxt.offset}")
