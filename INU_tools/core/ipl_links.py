"""IPL link sidecar — UUID → (ipl_file, line_idx) persistence.

The map workflow benefits from a stable identity between a Blender
object and the IPL inst row it represents: when an object is moved
in Blender and ``Add to IPL`` is invoked again, we want to overwrite
the existing line (single source of truth) instead of appending a
duplicate placement.

We store the mapping in a JSON sidecar next to the .blend file:

    <blend_dir>/.inu_cache/ipl_links.json

Keyed first by absolute IPL path → ``ipl_hash`` (sha1 of file content
on last export) + ``links`` dict ``{uuid: link_record}``.  The link
record carries everything needed to verify / repair the mapping if
the IPL file was edited externally:

    {
        "line_idx":    42,
        "model_id":    7981,
        "model_name":  "ali_pillar",
        "last_pos":    [120.5, -80.3, 14.2]
    }

When ``ipl_hash`` mismatches the live file the link records are
re-validated via content-match (model_id + last_pos within 0.5 m).
This means external edits are tolerated as long as the user's
placement is still recognisable in the file.

No Blender dependency — pure ``os`` / ``hashlib`` / ``json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid as _uuid_mod
from typing import Dict, List, Optional, Tuple

SIDECAR_DIRNAME = ".inu_cache"
SIDECAR_FILENAME = "ipl_links.json"
SIDECAR_VERSION = 1

# Position tolerance (metres) for the content-match fallback.  Vanilla
# SA map placements are usually metres apart; 0.5 m is enough to
# survive light external nudges without false-positive collisions
# between adjacent placements of the same model.
POS_MATCH_TOLERANCE = 0.5


# ── Sidecar path resolution ────────────────────────────────────────

def sidecar_dir_for_blend(blend_path: str) -> str:
    """Return the ``.inu_cache`` directory next to *blend_path*.

    When *blend_path* is empty (file never saved) we fall back to the
    system temp folder under ``inu_cache/<process-id>``.  The user is
    expected to save the .blend before the cache becomes meaningful;
    until then this acts as a scratch area so the operator stays
    functional.
    """
    if blend_path and os.path.isfile(blend_path):
        d = os.path.dirname(blend_path)
        return os.path.join(d, SIDECAR_DIRNAME)
    return os.path.join(tempfile.gettempdir(), 'inu_cache', str(os.getpid()))


def sidecar_path_for_blend(blend_path: str) -> str:
    return os.path.join(sidecar_dir_for_blend(blend_path), SIDECAR_FILENAME)


# ── File hashing ───────────────────────────────────────────────────

def hash_ipl_file(ipl_path: str) -> str:
    """Return sha1 hex of the IPL file content; empty string if missing.

    sha1 is cheap (~250 MB/s on commodity hardware) and IPLs are tiny
    by comparison — typical map IPL is < 200 KB, full vanilla SA IPL
    set sums to ~3 MB.  Hashing on every export is unnoticeable.
    """
    if not ipl_path or not os.path.isfile(ipl_path):
        return ""
    h = hashlib.sha1()
    with open(ipl_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


# ── In-memory model ────────────────────────────────────────────────

class IplLinkRecord:
    __slots__ = ('line_idx', 'model_id', 'model_name', 'last_pos')

    def __init__(self, line_idx: int, model_id: int, model_name: str,
                 last_pos: Tuple[float, float, float]):
        self.line_idx = int(line_idx)
        self.model_id = int(model_id)
        self.model_name = str(model_name)
        self.last_pos = (float(last_pos[0]), float(last_pos[1]), float(last_pos[2]))

    def to_dict(self) -> dict:
        return {
            'line_idx': self.line_idx,
            'model_id': self.model_id,
            'model_name': self.model_name,
            'last_pos': list(self.last_pos),
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'IplLinkRecord':
        return cls(
            line_idx=d.get('line_idx', -1),
            model_id=d.get('model_id', 0),
            model_name=d.get('model_name', ''),
            last_pos=d.get('last_pos', (0.0, 0.0, 0.0)),
        )


class IplFileLinks:
    __slots__ = ('ipl_hash', 'links')

    def __init__(self, ipl_hash: str = "",
                 links: Optional[Dict[str, IplLinkRecord]] = None):
        self.ipl_hash = ipl_hash
        self.links = links if links is not None else {}

    def to_dict(self) -> dict:
        return {
            'ipl_hash': self.ipl_hash,
            'links': {u: r.to_dict() for u, r in self.links.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'IplFileLinks':
        links = {u: IplLinkRecord.from_dict(r)
                 for u, r in (d.get('links') or {}).items()}
        return cls(ipl_hash=d.get('ipl_hash', ''), links=links)


class IplLinksSidecar:
    """Top-level sidecar — one per .blend, holds all IPL files used."""

    __slots__ = ('version', 'ipl_files')

    def __init__(self):
        self.version = SIDECAR_VERSION
        # absolute, normalised IPL path → IplFileLinks
        self.ipl_files: Dict[str, IplFileLinks] = {}

    def file_links(self, ipl_path: str, create: bool = True) -> Optional[IplFileLinks]:
        key = _normkey(ipl_path)
        if key in self.ipl_files:
            return self.ipl_files[key]
        if create:
            f = IplFileLinks()
            self.ipl_files[key] = f
            return f
        return None

    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'ipl_files': {p: f.to_dict() for p, f in self.ipl_files.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'IplLinksSidecar':
        s = cls()
        s.version = int(d.get('version', SIDECAR_VERSION))
        for p, f in (d.get('ipl_files') or {}).items():
            s.ipl_files[p] = IplFileLinks.from_dict(f)
        return s


def _normkey(path: str) -> str:
    """Path normalisation for sidecar dict keys: absolute + normcase."""
    return os.path.normcase(os.path.abspath(os.path.normpath(path)))


# ── Load / save ────────────────────────────────────────────────────

def load_sidecar(blend_path: str) -> IplLinksSidecar:
    """Load sidecar JSON; return empty one if missing or malformed."""
    p = sidecar_path_for_blend(blend_path)
    if not os.path.isfile(p):
        return IplLinksSidecar()
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return IplLinksSidecar.from_dict(data)
    except (OSError, json.JSONDecodeError) as ex:
        print(f"[IPL Links] sidecar load failed: {ex}")
        return IplLinksSidecar()


def save_sidecar(blend_path: str, sidecar: IplLinksSidecar) -> bool:
    """Write sidecar JSON, creating .inu_cache/ if needed.

    Atomic via write-to-tmp + rename so a partial write can't corrupt
    the cache.  Returns True on success.
    """
    p = sidecar_path_for_blend(blend_path)
    d = os.path.dirname(p)
    try:
        os.makedirs(d, exist_ok=True)
    except OSError as ex:
        print(f"[IPL Links] mkdir failed: {ex}")
        return False
    tmp = p + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(sidecar.to_dict(), f, indent=2, ensure_ascii=False)
        os.replace(tmp, p)
        return True
    except OSError as ex:
        print(f"[IPL Links] save failed: {ex}")
        try:
            os.unlink(tmp)
        except OSError:
            pass
        return False


# ── UUID utilities ─────────────────────────────────────────────────

def new_uuid() -> str:
    return _uuid_mod.uuid4().hex


# ── Content-match (fallback) ───────────────────────────────────────

def find_inst_by_content(ipl, model_id: int,
                         pos: Tuple[float, float, float],
                         tolerance: float = POS_MATCH_TOLERANCE) -> int:
    """Find inst index in ``ipl.instances`` matching model_id and pos.

    Returns -1 if no match within ``tolerance`` metres.  Used when the
    sidecar hash doesn't match (external edit) — we can still relocate
    most placements by their last known position.
    """
    if model_id <= 0:
        return -1
    best_idx = -1
    best_d2 = tolerance * tolerance
    for i, inst in enumerate(ipl.instances):
        if int(getattr(inst, 'model_id', -1)) != int(model_id):
            continue
        dx = float(inst.pos_x) - float(pos[0])
        dy = float(inst.pos_y) - float(pos[1])
        dz = float(inst.pos_z) - float(pos[2])
        d2 = dx * dx + dy * dy + dz * dz
        if d2 <= best_d2:
            best_d2 = d2
            best_idx = i
    return best_idx


# ── External-edit detection & repair ───────────────────────────────

def reconcile_file_links(file_links: IplFileLinks, ipl,
                          current_hash: str) -> Tuple[int, List[str]]:
    """Re-validate link line_idx values against a fresh IPL.

    Called when ``current_hash`` differs from ``file_links.ipl_hash``
    (or when caller wants paranoia).  For each link:
      * if its ``line_idx`` still points at a row with the recorded
        model_id and last_pos (within tolerance), keep it as-is
      * else search the file by content-match; on hit, fix line_idx
      * else mark the uuid for removal (placement gone from IPL)

    Returns ``(repaired, removed_uuids)`` so the operator can surface
    a report to the user.
    """
    repaired = 0
    removed: List[str] = []
    n = len(ipl.instances)
    for u, rec in list(file_links.links.items()):
        idx = rec.line_idx
        valid_here = False
        if 0 <= idx < n:
            inst = ipl.instances[idx]
            if int(getattr(inst, 'model_id', -1)) == rec.model_id:
                dx = inst.pos_x - rec.last_pos[0]
                dy = inst.pos_y - rec.last_pos[1]
                dz = inst.pos_z - rec.last_pos[2]
                if dx * dx + dy * dy + dz * dz <= POS_MATCH_TOLERANCE ** 2:
                    valid_here = True
        if valid_here:
            continue
        new_idx = find_inst_by_content(ipl, rec.model_id, rec.last_pos)
        if new_idx >= 0:
            rec.line_idx = new_idx
            repaired += 1
        else:
            removed.append(u)
            del file_links.links[u]
    file_links.ipl_hash = current_hash
    return repaired, removed
