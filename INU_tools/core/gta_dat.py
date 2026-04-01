"""
GTA SA gta.dat / gta_int.dat parser.

These files list all IDE, IPL, IMG and other resources the game loads.
Lines starting with IDE, IPL, IMG, SPLASH, COLFILE, TEXDICTION, MODELFILE
specify resource paths relative to the game root.

Usage:
    info = parse_gta_dat("C:/Games/GTA SA/data/gta.dat")
    # info.ide_paths  → ["DATA\\MAPS\\generic\\vegepart.ide", ...]
    # info.ipl_paths  → ["DATA\\MAPS\\LA\\LAn.ipl", ...]
    # info.img_paths  → ["MODELS\\gta3.img", ...]

No Blender dependency — pure Python.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field


@dataclass
class GtaDatInfo:
    """Parsed gta.dat / gta_int.dat contents."""
    ide_paths: list[str] = field(default_factory=list)
    ipl_paths: list[str] = field(default_factory=list)
    img_paths: list[str] = field(default_factory=list)
    colfile_paths: list[str] = field(default_factory=list)
    texdiction_paths: list[str] = field(default_factory=list)
    modelfile_paths: list[str] = field(default_factory=list)
    splash_paths: list[str] = field(default_factory=list)


def parse_gta_dat(filepath: str) -> GtaDatInfo:
    """Parse a gta.dat or gta_int.dat file."""
    info = GtaDatInfo()

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(None, 1)
            if len(parts) < 2:
                continue

            keyword = parts[0].upper()
            path = parts[1].strip()

            if keyword == 'IDE':
                info.ide_paths.append(path)
            elif keyword == 'IPL':
                info.ipl_paths.append(path)
            elif keyword == 'IMG':
                info.img_paths.append(path)
            elif keyword == 'COLFILE':
                # Format: COLFILE <level> <path>
                col_parts = path.split(None, 1)
                if len(col_parts) >= 2:
                    info.colfile_paths.append(col_parts[1].strip())
                else:
                    info.colfile_paths.append(path)
            elif keyword == 'TEXDICTION':
                info.texdiction_paths.append(path)
            elif keyword == 'MODELFILE':
                info.modelfile_paths.append(path)
            elif keyword == 'SPLASH':
                info.splash_paths.append(path)

    return info


def resolve_paths(game_root: str, dat_info: GtaDatInfo) -> GtaDatInfo:
    """Convert relative paths to absolute using game root directory.
    Backslashes are normalized to forward slashes."""
    def _resolve(p: str) -> str:
        # Normalize separators
        p = p.replace('\\', '/')
        full = os.path.join(game_root, p)
        return os.path.normpath(full)

    return GtaDatInfo(
        ide_paths=[_resolve(p) for p in dat_info.ide_paths],
        ipl_paths=[_resolve(p) for p in dat_info.ipl_paths],
        img_paths=[_resolve(p) for p in dat_info.img_paths],
        colfile_paths=[_resolve(p) for p in dat_info.colfile_paths],
        texdiction_paths=[_resolve(p) for p in dat_info.texdiction_paths],
        modelfile_paths=[_resolve(p) for p in dat_info.modelfile_paths],
        splash_paths=[_resolve(p) for p in dat_info.splash_paths],
    )


def find_all_resources(game_root: str) -> GtaDatInfo:
    """Parse both gta.dat and gta_int.dat, merge and resolve all paths."""
    merged = GtaDatInfo()

    for dat_name in ('gta.dat', 'gta_int.dat'):
        dat_path = os.path.join(game_root, 'data', dat_name)
        if not os.path.isfile(dat_path):
            continue
        info = parse_gta_dat(dat_path)
        merged.ide_paths.extend(info.ide_paths)
        merged.ipl_paths.extend(info.ipl_paths)
        merged.img_paths.extend(info.img_paths)
        merged.colfile_paths.extend(info.colfile_paths)
        merged.texdiction_paths.extend(info.texdiction_paths)
        merged.modelfile_paths.extend(info.modelfile_paths)
        merged.splash_paths.extend(info.splash_paths)

    return resolve_paths(game_root, merged)


def extract_regions(info: GtaDatInfo) -> list[str]:
    """Extract unique region folder names from IPL paths.
    E.g. 'DATA\\MAPS\\LA\\LAe.IPL' → 'LA'
    Returns sorted list of region names."""
    regions = set()
    for p in info.ipl_paths:
        # Normalize and split path
        parts = p.replace('\\', '/').upper().split('/')
        # Look for MAPS/<region>/<file> pattern
        for i, part in enumerate(parts):
            if part == 'MAPS' and i + 2 < len(parts):
                region = parts[i + 1]
                if region not in ('GENERIC',):  # skip generic
                    regions.add(region)
                break
    return sorted(regions)
