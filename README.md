<div align="center">

![INU Tools Logo](docs/logo.jpg)

# INU_Tools (GTA SA)

**Blender addon for GTA San Andreas modding — full pipeline from modeling to IMG archive.**

<p>
  <img src="https://img.shields.io/badge/Blender-2.83%E2%80%935.1-orange?logo=blender" alt="Blender">
  <img src="https://img.shields.io/badge/Version-2.2.0-green" alt="Version">
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

- 💾 **Game Folder Backup** — auto-snapshot `gta3.img` and key `.ide` files before destructive ops (Map Export, IMG rebuild)
- 🔁 **IPL Mass Replace** — swap all INST entries with model X for model Y by coordinates / radius / tag
- 🎬 **IFP Library Viewer** — preview any of the 294 animations on a temporary armature without creating a ped
- 🎆 **Auto-LOD generation** — when no paired `_L0` is found, Map Export auto-generates a decimated copy (EMAPTool-style)

## 🆕 What's New in 2.2.0

- 🔥 **LightMap bake** — bakes full GI straight from your scene's real lamps / sun / world (no internal light-rig) over diffuse. **Apply LightMap** in 3 modes: keep as a stack layer · bake into diffuse as one vanilla SA texture · write to the Day vertex prelight. Plus **Show over base (UV2)**, **denoise** for every noisy map (OIDN on Blender 4.x, numpy bilateral on 5.x), and linear-space compositing so **Save as** matches the game
- 🗺️ **Smarter IDE/IPL** — **"Also to IDE/IPL"** export checkbox; automatic `lod_index`; **Model ID = 0 blocked**; IDE flag translation across games; FLA `realInterior` (12th column); the panel-picked file wins on Add
- 📦 **Rebuild IMG (compact)** — reclaim dead space left by repeated exports; block on IMG entry names over 24 chars
- 🔍 **Model type auto-detection** (DFF / LOD / COL, case-insensitive LOD) — the `_DFF/_LOD/_COL` suffixes are now a manual override only
- ✨ **2DFX** — **"Apply settings to selected"** (one effect's settings onto a whole group of empties), attach several at once, relationship-line toggle, preview auto-rebuild on `Shift+D` / `Ctrl+C+V`; per-effect settings moved to the empty's Object Data
- 🎞️ **UV animation × Night** — found why the animation won't play in retail single-player: **night vertex colors** disable UV anim. Now warned right in DFF Flags and the pre-export check
- 🆔 **ID Manager** — **"Skip occupied IDs"** toggle (strict from the start number vs. skip occupied)
- 🧹 **Cleanup + Blender Extensions ready** — dropped NVTT/nvcompress (pure numpy DXT) and dead code (broken JSON material presets, hidden panels); manifest updated for extensions.blender.org rules

→ [Release notes 2.2.0](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v2.2.0) · [2.1.0](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v2.1.0) · [2.0.0](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v2.0.0) · [Version history](../../releases)

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
- 💡 **Prelight baking** — Day/Night vcols, raycast shadows, scatter, foliage shading, **Light Cutter** (light pools under lamps), Fill, vertex-alpha preview, LightMap UV2, Modulate Color preview
- 🎯 **2DFX** — Light / Particle / Ped Attractor / Sun Glare with presets and attach/detach
- 🎨 **Materials** — Env Map, Bump, Specular, Reflection, UV Animation, Dual Texture, COL Surface
- 🦴 **Skinned DFF + IK Rig** — armature, weights, FK→IK bake for peds, **Frame Hierarchy Editor** with vanilla VEHICLE/PED templates, byte-perfect round-trip
- 🎬 **Animated Map Object** — one-click wizard assembles DFF + IFP + IDE for animated objects (windmills, cranes, doors)
- 🚗 **Vehicle Paintjob** — Pay'n'Spray alt-texture support (`<base>_paintjob1/2`) with pair validation
- ✅ **Validate Scene** — single pre-export pass (quaternions, flags, damage/paintjob pairing)
- 🔍 **File Scanner** — lint DFF/COL/TXD from a folder for crash-prone patterns (limit overruns, broken refs)
- 🗺️ **X Radar Maker** — minimap tile generation (8×8 / menu / full radar) with TXD packing
- 🧩 **Profile System** — custom N-sidebar layouts (panel visibility / order) saved as JSON, switch between tasks
- 🔍 **Model type auto-detection** — DFF / LOD / COL are recognised automatically (LOD by a case-insensitive "lod" token, COL by tag/no-texture); the `_DFF/_LOD/_COL` suffixes work as a manual override
- 📁 **Preset folder** — point all presets/data (profiles, ID presets, pipeline flag defaults) at any folder; existing presets are copied across on switch

## 🧭 UI Panels

| Location | Panel | What's there |
|---|---|---|
| `Properties > Scene` | **INU Tools** | IDE/IPL/IMG paths, textures, IMG files, preset folder |
| `Properties > Object` | **INU Tools: Model** | Type (auto+manual), Model ID, TXD, Draw Dist, IDE Flags, DFF Flags, Pipeline, Breakable, 2DFX |
| `Properties > Material` | **GTA Material** (2 tabs) | SURFACE — collision surface type · EFFECTS — Env Map, Bump, Reflection, Specular, UV Animation + quick presets (Glass/Chrome/Paint/Reset) |
| `View3D > Sidebar (N)` | **GTA Tools** | SETUP → MODEL → DATA → EXPORT pipeline (Export at top, ID Manager, Object IDE/IPL, all other sub-panels) |
| `UV Editor > Sidebar (N)` | **GTA Tools** | UV tools |

## ⌨️ Hotkeys

| Key | Action |
|---|---|
| `Shift+T` | Toggle UV Editor |

## 📹 Video Tutorial

→ [Export & Import IDE / IPL / IMG / Map](https://www.youtube.com/watch?v=Jw_R9QFYxWE)

## 📦 Installation

**Blender Extensions (Blender 4.2+):** install from [extensions.blender.org](https://extensions.blender.org) (Get Extensions → search "INU Tools"), or **Edit → Preferences → Get Extensions → Install from Disk…** with the release `.zip`.

**Manual (Blender 2.83+):**
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
| **Game** | GTA San Andreas (primary), GTA Vice City + GTA III (experimental, see below) |
| **MTA** | MTA:SA compatible (GTA SA fork) |
| **OS** | Windows / Linux / macOS |

### 🎮 Multi-game support

INU Tools targets **GTA San Andreas** by default but can read and write the older RenderWare games. Set the target game from the **GTA Tools** N-sidebar header dropdown (SA / VC / III) — every exporter then routes through the right format dispatch.

| Format | III (RW 3.3) | VC (RW 3.5) | SA (RW 3.6) |
|---|:-:|:-:|:-:|
| **DFF** read | ✅ auto-detect by RW version | ✅ auto-detect | ✅ |
| **DFF** write | ✅ (skips SA-only Night vcols, Pipeline chunk, UV anim) | ✅ (skips Night vcols, Pipeline) | ✅ |
| **COL** read | ✅ `COLL` | ✅ `COL2` | ✅ `COL3` |
| **COL** write | ✅ `COLL` v1 | ✅ `COL2` v2 | ✅ `COL3` v3 |
| **TXD** read | ✅ | ✅ | ✅ |
| **TXD** write | ✅ (RW lib_id per game) | ✅ | ✅ |
| **IDE** read | ✅ | ✅ | ✅ |
| **IDE** write | ✅ (5-field OBJS, no `txdp` / `2dfx`) | ✅ (5-field OBJS, no `2dfx`) | ✅ (multi-mesh, `txdp`, `2dfx`) |
| **IPL** read | ✅ (12 cols, scale, no interior) | ✅ (13 cols, scale + interior) | ✅ (11 cols, lod_index) |
| **IPL** write | ✅ text only | ✅ text only | ✅ text + binary |
| **IMG** read | ✅ VER1 (split `.dir` + `.img`) | ✅ VER1 | ✅ VER2 |
| **IMG** write | ✅ VER1 | ✅ VER1 | ✅ VER2 |
| **IFP** anim | ✅ ANPK (chunked) | ✅ ANPK | ✅ ANPK + ANP3 compressed |
| **2DFX** | Light + Particle | + PedAttractor | + SunGlare |
| **Surface IDs** | 0–84 (clamp on write) | 0–85 | 0–178 |

**Known limitations:**
- **Lossy surface translation** — cross-game COL export collapses ~12 categories from SA's 179 surfaces. SA → VC → SA loses sub-types (e.g. `GRASS_SHORT` ↔ `GRASS_LONG`).
- **Validate Scene cross-game checks** — warn if scene targets III/VC but objects still carry SA-only features (Night vcols, Multi-mesh LOD, UV anim, SunGlare 2DFX).
- **Map editor flow** — main pipeline is SA. III/VC modders can import vanilla assets and export individual DFF/COL/TXD; full map round-trip is currently SA-only.
- **IFP**: ANP3 (compressed int16) is SA-only — exporting to III/VC auto-downgrades to ANPK with a warning.

The scene's active game also affects File Scanner / Map Analyzer thresholds — `model_id_max` (III=6500, VC=8500, SA=19999) and `surface_id_max` are checked against the target game's limits.

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
