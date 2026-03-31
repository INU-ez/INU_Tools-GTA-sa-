"""
GTA SA water.dat reader/writer.

Format — text file:
  Line 1: "processed"
  Each subsequent line = one water polygon (3 or 4 vertices):
    For each vertex: X Y Z SpeedX SpeedY SpeedZ WaveHeight
    Last value on line: Flag (0-3)
      0 = Default/Invisible
      1 = Default/Visible
      2 = Shallow/Invisible
      3 = Shallow/Visible

  3 vertices = triangle (21 floats + 1 int = 22 values)
  4 vertices = quad (28 floats + 1 int = 29 values)

No Blender dependency — pure Python.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class WaterVertex:
    """One vertex of a water polygon."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    speed_x: float = 0.0
    speed_y: float = 0.0
    speed_z: float = 0.0
    wave_height: float = 0.0


@dataclass
class WaterPolygon:
    """One water polygon (3 or 4 vertices)."""
    vertices: List[WaterVertex] = field(default_factory=list)
    flag: int = 1  # 0-3, default visible


@dataclass
class WaterFile:
    """Collection of water polygons."""
    polygons: List[WaterPolygon] = field(default_factory=list)


# ── Reading ─────────────────────────────────────────────────────────

def read_water(filepath: str) -> WaterFile:
    """Parse a water.dat file and return structured data."""
    water = WaterFile()

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#') or line == 'processed':
                continue

            parts = line.split()
            try:
                values = [float(p) for p in parts]
            except ValueError:
                continue

            poly = WaterPolygon()

            if len(parts) == 22:
                # Triangle (3 vertices + flag)
                for i in range(3):
                    base = i * 7
                    v = WaterVertex(
                        x=values[base], y=values[base + 1], z=values[base + 2],
                        speed_x=values[base + 3], speed_y=values[base + 4],
                        speed_z=values[base + 5], wave_height=values[base + 6],
                    )
                    poly.vertices.append(v)
                poly.flag = int(values[21])

            elif len(parts) == 29:
                # Quad (4 vertices + flag)
                for i in range(4):
                    base = i * 7
                    v = WaterVertex(
                        x=values[base], y=values[base + 1], z=values[base + 2],
                        speed_x=values[base + 3], speed_y=values[base + 4],
                        speed_z=values[base + 5], wave_height=values[base + 6],
                    )
                    poly.vertices.append(v)
                poly.flag = int(values[28])

            else:
                continue

            water.polygons.append(poly)

    return water


# ── Writing ─────────────────────────────────────────────────────────

def write_water(filepath: str, water: WaterFile) -> int:
    """Write water polygons to a water.dat file. Returns polygon count."""
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write('processed\n')

        for poly in water.polygons:
            parts = []
            for v in poly.vertices:
                parts.extend([
                    f"{v.x:.1f}", f"{v.y:.1f}", f"{v.z:.1f}",
                    f"{v.speed_x:.1f}", f"{v.speed_y:.1f}",
                    f"{v.speed_z:.1f}", f"{v.wave_height:.1f}",
                ])
            # Join with spaces, add flag at end
            line = '    '.join(
                ' '.join(parts[i * 7:(i + 1) * 7]) for i in range(len(poly.vertices))
            )
            f.write(f"{line}  {poly.flag}\n")

    return len(water.polygons)
