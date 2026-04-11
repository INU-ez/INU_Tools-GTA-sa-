"""
GTA SA effects.fxp reader/writer.

Text format despite the .fxp extension. Hierarchy:
  FX_PROJECT_DATA
    FX_SYSTEM_DATA (one per particle effect, e.g. prt_blood)
      version, header scalars, NUM_PRIMS
      FX_PRIM_EMITTER_DATA * N
        FX_PRIM_BASE_DATA (NAME, MATRIX, TEXTURE..., blend IDs)
        NUM_INFOS, then M info blocks
        FX_INFO_<TYPE>_DATA — bag of scalars and named curves
          each curve: FX_INTERP_DATA -> LOOPED, NUM_KEYS, FX_KEYFLOAT_DATA keys
        emitter footer: LODSTART, LODEND
      system footer: OMITTEXTURES, TXDNAME

Scalars are kept as raw strings to preserve formatting (e.g. "1.000" vs "1").
Curves are parsed to floats for later interpolation/simulation.

No Blender dependency — pure Python.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable


@dataclass
class FXKeyframe:
    time: float = 0.0
    val: float = 0.0


@dataclass
class FXCurve:
    looped: int = 0
    keys: List[FXKeyframe] = field(default_factory=list)

    def sample(self, t: float) -> float:
        """Linear interpolation at t (normalized 0..1 along the effect)."""
        ks = self.keys
        if not ks:
            return 0.0
        if len(ks) == 1 or t <= ks[0].time:
            return ks[0].val
        if t >= ks[-1].time:
            return ks[-1].val
        for a, b in zip(ks, ks[1:]):
            if a.time <= t <= b.time:
                span = b.time - a.time
                if span <= 0.0:
                    return a.val
                f = (t - a.time) / span
                return a.val + (b.val - a.val) * f
        return ks[-1].val


@dataclass
class FXInfoBlock:
    """One FX_INFO_<TYPE>_DATA block.

    `type` is the short name: "EMSPEED", "COLOUR", "SIZE", etc.
    Scalars are insertion-ordered (key, raw_value_string) pairs.
    Curves are keyed by field name ("SPEED", "RED", "DIRX", ...).
    """
    type: str = ""
    scalars: List[Tuple[str, str]] = field(default_factory=list)
    curves: Dict[str, FXCurve] = field(default_factory=dict)

    def scalar(self, key: str, default: Optional[str] = None) -> Optional[str]:
        for k, v in self.scalars:
            if k == key:
                return v
        return default


@dataclass
class FXEmitter:
    base: List[Tuple[str, str]] = field(default_factory=list)
    infos: List[FXInfoBlock] = field(default_factory=list)
    footer: List[Tuple[str, str]] = field(default_factory=list)

    def base_get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        for k, v in self.base:
            if k == key:
                return v
        return default

    @property
    def name(self) -> str:
        return self.base_get("NAME", "ParticleEmitter") or "ParticleEmitter"

    @property
    def textures(self) -> List[str]:
        return [
            self.base_get("TEXTURE", "NULL") or "NULL",
            self.base_get("TEXTURE2", "NULL") or "NULL",
            self.base_get("TEXTURE3", "NULL") or "NULL",
            self.base_get("TEXTURE4", "NULL") or "NULL",
        ]

    @property
    def matrix(self) -> List[float]:
        raw = self.base_get("MATRIX", "") or ""
        return [float(x) for x in raw.split()]

    @property
    def alpha_on(self) -> int:
        return int(self.base_get("ALPHAON", "1") or 1)

    @property
    def src_blend(self) -> int:
        return int(self.base_get("SRCBLENDID", "4") or 4)

    @property
    def dst_blend(self) -> int:
        return int(self.base_get("DSTBLENDID", "5") or 5)

    def info(self, type_name: str) -> Optional[FXInfoBlock]:
        for i in self.infos:
            if i.type == type_name:
                return i
        return None


@dataclass
class FXSystem:
    version: str = "109"
    header: List[Tuple[str, str]] = field(default_factory=list)
    emitters: List[FXEmitter] = field(default_factory=list)
    footer: List[Tuple[str, str]] = field(default_factory=list)

    def header_get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        for k, v in self.header:
            if k == key:
                return v
        return default

    @property
    def name(self) -> str:
        return self.header_get("NAME", "") or ""

    @property
    def length(self) -> float:
        return float(self.header_get("LENGTH", "0") or 0)

    @property
    def play_mode(self) -> int:
        return int(self.header_get("PLAYMODE", "0") or 0)

    @property
    def cull_dist(self) -> float:
        return float(self.header_get("CULLDIST", "0") or 0)


@dataclass
class FXFile:
    systems: List[FXSystem] = field(default_factory=list)

    def find(self, name: str) -> Optional[FXSystem]:
        for s in self.systems:
            if s.name == name:
                return s
        return None


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #

_INFO_TERMINATORS = (
    "LODSTART:", "LODEND:", "OMITTEXTURES:", "TXDNAME:",
    "FX_PRIM_EMITTER_DATA:", "FX_SYSTEM_DATA:",
)


def read_fxp(path: str) -> FXFile:
    with open(path, "r", encoding="ascii", errors="replace") as f:
        return parse_fxp(f.read())


def parse_fxp(text: str) -> FXFile:
    lines = text.splitlines()
    i = 0
    n = len(lines)

    def peek() -> Optional[str]:
        nonlocal i
        while i < n and lines[i].strip() == "":
            i += 1
        return lines[i].strip() if i < n else None

    def consume() -> Optional[str]:
        nonlocal i
        line = peek()
        if line is not None:
            i += 1
        return line

    def expect(expected: str) -> str:
        line = consume()
        if line != expected:
            raise ValueError(f"Expected {expected!r}, got {line!r} (line {i})")
        return line

    def split_kv(line: str) -> Tuple[str, str]:
        if ":" not in line:
            raise ValueError(f"Malformed key:value line: {line!r}")
        k, v = line.split(":", 1)
        return k.strip(), v.strip()

    expect("FX_PROJECT_DATA:")
    fxf = FXFile()

    while True:
        head = peek()
        if head is None or head == "FX_PROJECT_DATA_END:":
            break
        if head != "FX_SYSTEM_DATA:":
            raise ValueError(f"Unexpected line at system level: {head!r}")
        consume()

        system = FXSystem()
        version = consume()
        if version is None:
            raise ValueError("Unexpected EOF after FX_SYSTEM_DATA:")
        system.version = version

        # system header until NUM_PRIMS
        num_prims = 0
        while True:
            line = peek()
            if line is None:
                raise ValueError("Unexpected EOF in system header")
            if line.startswith("NUM_PRIMS:"):
                consume()
                num_prims = int(split_kv(line)[1])
                break
            consume()
            system.header.append(split_kv(line))

        for _ in range(num_prims):
            expect("FX_PRIM_EMITTER_DATA:")
            emitter = FXEmitter()
            expect("FX_PRIM_BASE_DATA:")

            # base scalars until NUM_INFOS
            num_infos = 0
            while True:
                line = peek()
                if line is None:
                    raise ValueError("Unexpected EOF in FX_PRIM_BASE_DATA")
                if line.startswith("NUM_INFOS:"):
                    consume()
                    num_infos = int(split_kv(line)[1])
                    break
                consume()
                emitter.base.append(split_kv(line))

            for _ in range(num_infos):
                info_head = consume()
                if not (info_head and info_head.startswith("FX_INFO_") and info_head.endswith("_DATA:")):
                    raise ValueError(f"Expected FX_INFO_*_DATA:, got {info_head!r}")
                info_type = info_head[len("FX_INFO_"):-len("_DATA:")]
                info = FXInfoBlock(type=info_type)

                while True:
                    nxt = peek()
                    if nxt is None:
                        break
                    if nxt.startswith("FX_INFO_") and nxt.endswith("_DATA:"):
                        break
                    if any(nxt.startswith(t) for t in _INFO_TERMINATORS):
                        break
                    consume()
                    k, v = split_kv(nxt)
                    if v == "":
                        info.curves[k] = _parse_curve(peek, consume)
                    else:
                        info.scalars.append((k, v))

                emitter.infos.append(info)

            # emitter footer: LODSTART / LODEND
            while True:
                nxt = peek()
                if nxt is None:
                    break
                if nxt.startswith("LODSTART:") or nxt.startswith("LODEND:"):
                    consume()
                    emitter.footer.append(split_kv(nxt))
                    continue
                break

            system.emitters.append(emitter)

        # system footer: OMITTEXTURES / TXDNAME
        while True:
            nxt = peek()
            if nxt is None or nxt == "FX_SYSTEM_DATA:":
                break
            if nxt.startswith("OMITTEXTURES:") or nxt.startswith("TXDNAME:"):
                consume()
                system.footer.append(split_kv(nxt))
                continue
            break

        fxf.systems.append(system)

    return fxf


def _parse_curve(peek: Callable[[], Optional[str]], consume: Callable[[], Optional[str]]) -> FXCurve:
    head = consume()
    if head != "FX_INTERP_DATA:":
        raise ValueError(f"Expected FX_INTERP_DATA:, got {head!r}")
    curve = FXCurve()

    line = consume() or ""
    if not line.startswith("LOOPED:"):
        raise ValueError(f"Expected LOOPED:, got {line!r}")
    curve.looped = int(line.split(":", 1)[1].strip())

    line = consume() or ""
    if not line.startswith("NUM_KEYS:"):
        raise ValueError(f"Expected NUM_KEYS:, got {line!r}")
    num_keys = int(line.split(":", 1)[1].strip())

    for _ in range(num_keys):
        kf_head = consume()
        if kf_head != "FX_KEYFLOAT_DATA:":
            raise ValueError(f"Expected FX_KEYFLOAT_DATA:, got {kf_head!r}")
        tline = consume() or ""
        if not tline.startswith("TIME:"):
            raise ValueError(f"Expected TIME:, got {tline!r}")
        vline = consume() or ""
        if not vline.startswith("VAL:"):
            raise ValueError(f"Expected VAL:, got {vline!r}")
        curve.keys.append(FXKeyframe(
            time=float(tline.split(":", 1)[1].strip()),
            val=float(vline.split(":", 1)[1].strip()),
        ))
    return curve


# --------------------------------------------------------------------------- #
# Writer
# --------------------------------------------------------------------------- #

def write_fxp(path: str, fxf: FXFile) -> None:
    with open(path, "w", encoding="ascii", newline="") as f:
        f.write(format_fxp(fxf))


def format_fxp(fxf: FXFile) -> str:
    out: List[str] = []

    def emit(line: str = "") -> None:
        out.append(line)

    emit("FX_PROJECT_DATA:")
    emit()

    for system in fxf.systems:
        emit("FX_SYSTEM_DATA:")
        emit(system.version)
        emit()

        for k, v in system.header:
            emit(f"{k}: {v}")
        emit(f"NUM_PRIMS: {len(system.emitters)}")

        for emitter in system.emitters:
            emit("FX_PRIM_EMITTER_DATA:")
            emit()
            emit("FX_PRIM_BASE_DATA:")
            for k, v in emitter.base:
                # GTA SA's parser appears to require a trailing space after
                # the 12 floats of MATRIX (sscanf pattern with a final " ").
                # Preserving it prevents crashes on level load.
                if k == 'MATRIX':
                    emit(f"{k}: {v} ")
                else:
                    emit(f"{k}: {v}")
            emit()
            emit(f"NUM_INFOS: {len(emitter.infos)}")

            for info in emitter.infos:
                emit(f"FX_INFO_{info.type}_DATA:")
                for k, v in info.scalars:
                    emit(f"{k}: {v}")
                for k, curve in info.curves.items():
                    emit(f"{k}:")
                    emit("FX_INTERP_DATA:")
                    emit(f"LOOPED: {curve.looped}")
                    emit(f"NUM_KEYS: {len(curve.keys)}")
                    for kf in curve.keys:
                        emit("FX_KEYFLOAT_DATA:")
                        emit(f"TIME: {kf.time:.3f}")
                        emit(f"VAL: {kf.val:.3f}")
                emit()

            for k, v in emitter.footer:
                emit(f"{k}: {v}")

        for k, v in system.footer:
            emit(f"{k}: {v}")
        emit()

    emit("FX_PROJECT_DATA_END:")
    return "\r\n".join(out) + "\r\n"


# --------------------------------------------------------------------------- #
# Cache — keyed by absolute path, invalidated on mtime change
# --------------------------------------------------------------------------- #

_cache: Dict[str, Tuple[float, FXFile]] = {}


def load_cached(path: str) -> FXFile:
    """Return parsed FXFile for `path`, reusing a cached copy if unchanged."""
    key = os.path.normcase(os.path.abspath(path))
    mtime = os.path.getmtime(path)
    entry = _cache.get(key)
    if entry is not None and entry[0] == mtime:
        return entry[1]
    fxf = read_fxp(path)
    _cache[key] = (mtime, fxf)
    return fxf


def clear_cache() -> None:
    _cache.clear()
