<div align="center">

![INU Tools Logo](docs/logo.jpg)

# INU_Tools (GTA SA)

**Blender addon for GTA San Andreas modding — full pipeline from modeling to IMG archive.**

<p>
  <img src="https://img.shields.io/badge/Blender-2.83%E2%80%935.1-orange?logo=blender" alt="Blender">
  <img src="https://img.shields.io/badge/Version-1.9.0-green" alt="Version">
  <img src="https://img.shields.io/badge/License-GPL--3.0-blue" alt="License">
</p>

**[🇷🇺 Русская версия](docs/README_rus.md)** · **[📖 Documentation](docs/DOCS.md)** · **[⚖️ Compare to Kams / DragonFF](docs/COMPARISON.md)**

</div>

> [!IMPORTANT]
> **Two ways to install — pick based on your priority:**
>
> 🟢 **[Latest release](../../releases/latest)** — recommended for most users. Tested before publication, predictable behaviour.
>
> 🟡 **`main` branch** (this page's `Code → Download ZIP`, or `git clone`) — latest fixes and in-progress features that haven't shipped in a release yet. May contain bugs, unfinished work, or breaking changes. All `main` fixes eventually ship in the next release. If you hit a bug here, please mention **"from main"** in the issue so I can tell apart release vs. development reports.

---

## ✨ Highlights

<table>
<tr>
<td width="50%" valign="top">

- ⚡ **Performance** — Import Map ~10×, Export to IMG ~5–15× (parallel DFF parsing + batch IMG writer)
- 🎨 **Native parsers** — DFF / COL / TXD / IDE / IPL / IMG / IFP / FXP, zero external dependencies
- 🗺️ **Full map round-trip** — IMG → Blender → edit DFF + COL + TXD → IMG in another build
- 🎆 **`effects.fxp` editor** — 82 systems, live particle simulation in viewport
- 🦴 **Skinned DFF + IFP** — import peds with 294+ vanilla animations
- 🆔 **ID Manager** — multi-preset, scene sync, FLA range extension, conflict detection

</td>
<td width="50%" valign="top">

![2DFX tutorial](docs/gif/cj-explosion.gif)

</td>
</tr>
</table>

## 🔮 Roadmap

Ideas being considered. Not all of these will ship — some may turn out impractical, deprioritised, or just not worth it on closer inspection.

- 🔍 **Game Validator** — cross-file IDE / IPL / IMG / COL / TXD checks: missing references, duplicate IDs, broken LOD chains, coordinates out of map bounds. Single report grouped Critical / Warning / Info
- 💾 **Game Folder Backup** — auto-snapshot `gta3.img` and key `.ide` files before destructive ops (Map Export, IMG rebuild)
- 🧪 **Lint Profiles** — strict / lenient / FLA toggle for File Scanner and Game Validator (FLA builds have different limits)
- 🔁 **IPL Mass Replace** — swap all INST entries with model X for model Y by coordinates / radius / tag
- 🔍 **Texture Browser** — UIList with all textures from all TXDs in the game folder, with search and cross-ref «used by»
- 🎬 **IFP Library Viewer** — preview any of the 294 animations on a temporary armature without creating a ped

## 🆕 What's New in 1.9.0

- 📦 **Single unified build** — one `.zip` works on GitHub release and on extensions.blender.org. NVTT subprocess path replaced by bundled pure-numpy DXT encoder (`core/dxt.py`, ~7× faster than NVTT, no external binaries)
- 🔍 **Binary File Linter** — sub-panel «File Scanner» inside Check. Walks DFF/COL/TXD on disk, finds crash-prone patterns (shadow-mesh corruption, NPOT textures, GEOM_NATIVE on PC, atomic/triangle indices out of range, etc.) with explanatory description for every issue code
- 📚 **Asset Library builder** — turns any IDE/IPL/IMG set (vanilla SA, custom map, modded archive) into a Blender Asset Library with thumbnails, ready to drop into the **Asset Browser**
- 🎨 **Day/Night V-offset inline** — per-attribute brightness slider directly in the Day/Night row (auto-applies on Enter), survives bake
- 💡 **Prelight tweaks** — preset selector moved into the Prelight header with a one-click ✓ overwrite button (reports diff of changed fields), Modulate Color values saved per preset, new **Scatter Color** sub-panel paints chosen color around selected polygons with KDTree falloff
- 🔄 **DFF round-trip for special files** — parser now handles DFFs that start with non-Clump RW chunks (e.g. UV Animation Dictionary 0x2B). Vanilla files like `chinafurn1.dff` import/export byte-identical
- 🧹 Cleanup: removed `dff2gltf.py`, `extras/nvtt_compress.py`, dropped FULL/STORE build split

→ [Full release notes](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v1.9.0) · [Version history](../../releases)

## 🧰 Features

### Format Support

| Format | Import | Export | Edit | What it is |
|---|:---:|:---:|:---:|---|
| **DFF** | ✅ | ✅ | ✅ | RenderWare 3D model (geometry, skinning, materials, 2DFX, flags) |
| **COL** | ✅ | ✅ | ✅ | Collision (COL3, 179 surface types) |
| **TXD** | ✅ | ✅ | ✅ | Textures (DXT1/DXT5, parallel, pure numpy, drag&drop) |
| **IDE** | ✅ | ✅ | ✅ | Object definitions (objs/tobj/anim/cars/peds/weap/hier/txdp) |
| **IPL** | ✅ | ✅ | ✅ | Object placement (text + binary, 11 sections, FLA) |
| **IMG** | ✅ | ✅ | ✅ | Resource archive (VER2) — DFF + LOD + COL + TXD |
| **IFP** | ✅ | ✅ | ✅ | Animations (294+ vanilla, batch import, ANP3/ANPK/ANP2) |
| **FXP** (`effects.fxp`) | ✅ | ✅ | ✅ | Particles — 82 systems, viewport simulation, 40+ parameters |
| **CST** | ✅ | ✅ | ✅ | Steve's COL Editor text format |
| **water.dat** | ✅ | ✅ | ✅ | Water: types, snap, waterclear256 texture |
| **paths.ipl** / **tracks.dat** / **nodes\*.dat** / **flight.dat** | ✅ | ✅ | ✅ | Vehicle/ped paths, rail, compiled path nodes, flight routes |

### Also does

- 🗺️ **Full Map round-trip** — import the entire map straight from the game folder (IDE + IPL + IMG → Blender), edit, Map Export back preserving the layout
- 🆔 **ID Manager** — file-backed, multi-preset, scene sync, load from game, FLA range extension, conflict detection
- 💡 **Prelight baking** — Day/Night vcols, raycast shadows, scatter, LightMap UV2, Modulate Color preview
- 🎯 **2DFX** — Light / Particle / Ped Attractor / Sun Glare with presets and attach/detach
- 🎨 **Materials** — Env Map, Bump, Specular, Reflection, UV Animation, Dual Texture, COL Surface
- 🦴 **Skinned DFF + IK Rig** — armature, weights, FK→IK bake for peds, **Frame Hierarchy Editor** with vanilla VEHICLE/PED templates, byte-perfect round-trip
- 🎬 **Animated Map Object** — one-click wizard assembles DFF + IFP + IDE for animated objects (windmills, cranes, doors)
- 🚗 **Vehicle Paintjob** — Pay'n'Spray alt-texture support (`<base>_paintjob1/2`) with pair validation
- ✅ **Validate Scene** — single pre-export pass (quaternions, flags, damage/paintjob pairing)
- 🔍 **File Scanner** — lint DFF/COL/TXD from a folder for crash-prone patterns (limit overruns, broken refs)
- 🗺️ **X Radar Maker** — minimap tile generation (8×8 / menu / full radar) with TXD packing
- 🧩 **Profile System** — custom N-sidebar layouts (panel visibility / order) saved as JSON, switch between tasks
- 🚀 **Pipeline suffixes** — `_DFF` / `_LOD` / `_COL` → Export All / Export to IMG in one click

## 🧭 UI Panels

| Location | Panel | What's there |
|---|---|---|
| `Properties > Scene` | **INU Tools** | IDE/IPL/IMG paths, textures, IMG files |
| `Properties > Object` | **INU Tools: Model** | Type (auto+manual), Model ID, TXD, Draw Dist, IDE Flags, DFF Flags, Pipeline, Breakable, 2DFX |
| `Properties > Material` | **GTA Material** (3 tabs) | SURFACE — collision surface type · EFFECTS — Env Map, Bump, Reflection, Specular, UV Animation · PIPELINE |
| `View3D > Sidebar (N)` | **GTA Tools** | SETUP → MODEL → DATA → EXPORT pipeline (Export at top, ID Manager, Object IDE/IPL, all other sub-panels) |
| `UV Editor > Sidebar (N)` | **GTA Tools** | UV tools |

## ⌨️ Hotkeys

| Key | Action |
|---|---|
| `Shift+T` | Toggle UV Editor |

A **GTA SA** entry is added to Blender's standard `Shift+A` (Add) menu — quick-insert Army.dff (ped) / Admiral.dff (car).

## 📹 Video Tutorial

→ [Export & Import IDE / IPL / IMG / Map](https://www.youtube.com/watch?v=Jw_R9QFYxWE)

## 📦 Installation

1. Download the `INU_tools/` folder (or zip archive)
2. Copy it into your Blender addons directory:
   ```
   Blender/<version>/scripts/addons/INU_tools/
   ```
3. Open Blender → **Edit → Preferences → Add-ons** → enable **INU_tools(gta_sa)**

## 🔧 Compatibility

| | |
|---|---|
| **Blender** | 2.83 – 5.1 ✅ (4.2+ for extensions.blender.org install) |
| **Game** | GTA San Andreas (also compatible with MTA:SA) |
| **OS** | Windows / Linux / macOS |

## 🙏 Credits

Inspired by and partially compatible with:

- **[DragonFF](https://github.com/Parik27/DragonFF)** (Parik, GPL-3.0) — Blender addon for RenderWare formats. INU_tools uses compatible material and object property names for easy transition between addons.
- **[RenderWare](https://en.wikipedia.org/wiki/RenderWare)** — GTA SA game engine, DFF/COL/TXD format documentation.

### 🔧 Recommended companion tools

- **[Itera Tools 3](https://itera.gumroad.com/l/IteraTools3)** — Blender addon for vertex lighting. INU_tools includes a dedicated **Itera Tools 3** sub-panel (under the *Lighting* container): auto-detects Itera in your Asset Libraries and applies its `Vertex Lit Linear` / `Quickstart` material presets to the selection (plus one-click `Remove Itera` to restore original materials).

### Author

**INU** — addon author (Discord: `1.n.u`)
https://discord.gg/sqtGAVTGdy

### License

[GPL-3.0](LICENSE)
