<div align="center">

![INU Tools Logo](https://github.com/INU-ez/INU_Tools-GTA-sa-/blob/5e82d62dd40105c557ef9cb6be261bb70b63d3a2/logo.jpg)

# INU_Tools (GTA SA)

**Blender addon for GTA San Andreas modding — full pipeline from modeling to IMG archive.**

<p>
  <img src="https://img.shields.io/badge/Blender-4.2%E2%80%935.1-orange?logo=blender" alt="Blender">
  <img src="https://img.shields.io/badge/Version-1.6.6-green" alt="Version">
  <img src="https://img.shields.io/badge/License-GPL--3.0-blue" alt="License">
</p>
<p>
  <img src="https://komarev.com/ghpvc/?username=INU-ez&color=orange&style=flat-square&label=REPO+VIEWS" alt="Views">
  <a href="../../issues"><img src="https://img.shields.io/github/issues/INU-ez/INU_Tools-GTA-sa-?color=red" alt="Issues"></a>
  <a href="../../stargazers"><img src="https://img.shields.io/github/stars/INU-ez/INU_Tools-GTA-sa-?style=social" alt="Stars"></a>
</p>

**[🇷🇺 Русская версия](README_rus.md)** · **[📖 Documentation](DOCS.md)** · **[⚖️ Comparison with other tools](COMPARISON.md)**

</div>

---

## ✨ Highlights

<table>
<tr>
<td width="50%" valign="top">

- ⚡ **Performance** — Import Map ~10×, Export to IMG ~5–15× (parallel DFF parsing + batch IMG writer)
- 🎨 **Native parsers** — DFF / COL / TXD / IDE / IPL / IMG / IFP / FXP, zero external dependencies
- 🗺️ **Full map round-trip** — IMG → Blender → edit DFF + COL + TXD → IMG in another build
- 🎆 **effects.fxp editor** — 82 systems, live particle simulation in viewport
- 🦴 **Skinned DFF + IFP** — import peds with 294+ vanilla animations
- 🆔 **ID Manager** — multi-preset, scene sync, FLA range extension, conflict detection

</td>
<td width="50%" valign="top">

![2DFX tutorial](gif/cj-explosion.gif)

</td>
</tr>
</table>

## 🔮 Planned / In Progress

**Vehicles**
- 🛡️ **Damage variants UI extension** — visual link between matching `_ok` / `_dam` atomics, custom pivot for door swings, batch tools for headlight `dummy` placement

**Map workflow**
- 📐 **Adaptive grid auto-split** — variable cell size driven by local density (currently fixed XY grid only); guarantee per-cell DFF count instead of uniform spatial sub-division

**Animations**
- 🎬 **IFP merge / round-trip preview** — ANPK ↔ ANP3 conversion validator, per-clip preview without re-import

> [!NOTE]
> The addon is under active development. Bug reports are welcome in [Issues](../../issues).

## 🆕 What's new in 1.6.6

Closes the four 1.6.5-tracked Planned items (Pipeline chunk relocation, Map Export auto-split, Train paths verification, Vehicle damage variants) plus a batch of features that didn't make the v1.6.5-beta cut.

**Map workflow**
- 🗺️ **Map Export auto-split** — new `Auto-split into districts` toggle inside Map Export. DFFs are binned by XY origin into a configurable `cell_size` grid (default 256 m, vanilla streaming radius); each non-empty cell becomes its own subdirectory `<base>_x<cx>_y<cy>` with its own IDE / IPL / COL / TXD. Game-side it's identical to loading several IPLs sequentially. Falls back to a single district when only one cell is populated, so flipping the toggle on a small scene is harmless
- 📂 **Map Import: Group by IPL** — new toggle next to *Без LOD* / *Без TXD* / *Без коллизии*. When ON, each source IPL gets a parent collection `Map_<ipl_basename>` (e.g. `Map_LAn`, `Map_LAs`, `Map_SF`, `Map_LV`) with three nested sub-collections `Map_<ipl>_DFF` / `Map_<ipl>_LOD` / `Map_<ipl>_COL`. LODs and collisions stay separated by kind but tied to their district — toggle one parent's eye icon and the entire district disappears from the viewport
- ⚡ **COL import ~5× faster** — replaced bmesh with `mesh.from_pydata + foreach_set('material_index', …)`. Shared material cache across COL models (was creating ~10k duplicate `COL_N` materials on a large map). Profiler-driven fix: build COL was 60% of total wall time

**Vehicles**
- 🛡️ **Vehicle damage variants** — three new operators in *Check → Damage variants*: `Add _dam` duplicates the active mesh as a `_dam` variant (auto-renames source to `_ok` if needed, hides the new `_dam` from viewport but keeps it in the DFF export), `Show OK / Dam / Both` toggles viewport visibility for previewing damaged state, `Check pairs` reports paired and orphan `_ok` / `_dam` meshes via the system console
- 🔩 **Pipeline chunk → atomic extension** — DFF writer now emits `0x253F2F3` only inside the atomic extension (matches Seggaeman / RW vanilla layout). Reader still accepts both atomic and geometry extensions for back-compat with older Kam-era DFFs. Vehicle env-map (`0x53F2009A`) and Day/Night building pipelines (`0x53F20098`) keep working in vanilla SA after a clean export round-trip

**Vertex colors / lighting**
- 🎨 **VC Layer System (BETA)** — Photoshop-style non-destructive vertex color editing. Stack of named layers per scope (Day / Night), each with opacity / blend mode / pre-blend brightness / contrast. Live composite written into Day / Night attributes (originals safely backed up). Auto-flatten on DFF export, restore after — .blend keeps layers, .dff gets composite. Multi-select group sliders, recolor, promote / demote operators. Cap 10 layers per stack. See [DOCS § VC Layer System](DOCS.md#vc-layer-system-beta)

**Animations**
- 📜 **IFP format dispatch — ANP2 / ANPK write** — III/VC modding now supported. `write_ifp(path, ifp, format='ANPK' | 'ANP3')`. Default preserves source format from `ifp.source_format`. Standardised `KeyFrame.time` to seconds (was raw frames for ANP3, seconds for ANPK — now both seconds). Fixed previously-broken writer that emitted invalid hybrid output

**Paths**
- 🚂 **Train paths as splines (verified)** — `tracks*.dat` import/export already uses Blender curves (POLY spline, cyclic) with station flags stored on the curve as `station_indices`. Round-trip preserves station stops; documented under [DOCS § Train Paths](DOCS.md#train-paths)

**ID Manager / detection**
- 📏 **LOD Detection for vanilla** — irregular naming handled: `LODfoo`, `foo_LOD`, `foo1LOD`, `modeLODlaett` — all four patterns covered by `is_lod_name`

**UI / UX**
- 🆕 **UI Stage 7** — zone separator strips «── MODEL ──» / «── DATA ──» between bl_order ranges in N-sidebar (Stages 1-6 shipped in v1.6.5-beta)
- 🚿 **Export progress** — added to INU Export / Export All — workspace `status_text` shows current group / total during long batches (Build Map / Export to IMG / Extract Resources progress was already in v1.6.5-beta)
- 🧹 **Bitmaps Manager — unused cleanup** — `Find Unused` / `Remove Unused` operators scan `bpy.data.images` and `bpy.data.materials` for orphans. Uses `core.bitmap_diff` (bpy-free pure helpers, fully tested) — orphan-material textures correctly count as unused

<details>
<summary>Older releases</summary>

- **v1.6.5-beta** — map-workflow perf release: Import Map ~10× / Export to IMG ~5–15× faster, Load COL + Shared TXD toggles, Skip 2DFX default, ID Manager gaps & phantoms + multi-preset, UI pipeline reorganization (Stages 1-6) + Object Properties *INU Tools: Model* panel, Material Presets in `INU_Preset/`, progress bars (Build Map / Export to IMG / Extract Resources), opt-in Profiler — see [release page](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v1.6.5-beta)
- **v1.6.4** — Experimental: Map Export (scene→IPL+IDE+COL+TXD one-op), Binary IPL Write, CST IO, UV Animation in DFF, Breakable Objects, IFP Batch Import, GTA Material Panel, Bitmaps Manager, Station Markers, Roadblocks & Traffic Lights, FLA4 Path Format, Vehicle Scale Helper
- **v1.6.3** — Particle Effects (effects.fxp editor), Object Properties *GTA SA: IDE / IPL* panel, LightMap UV2, 2DFX UI (Detach All, attached effects list), ID Manager (Assign from ID…, Extend IDs FLA), Nodes multi-file I/O with 8×8 zone splitting
- **v1.6.1** — IPL Import: COL moves with DFF, Empty placeholders; Model Links dashed lines; LOD/COL → DFF snap; Drag & Drop TXD
- **v1.6.0** — Import Map full workflow, BBox Mode, IPL ZONE section, GPU NVTT auto-detect, Blender 4.2+
- **v1.5.3** — Skinned DFF + IFP animations, Water IO, Path IO, Blender 5.1 compatibility
- **v1.5.2** — Modular refactor (tools/ data/), COL Light Preview, Model ID Manager
- **v1.5.1** — IDE/IPL export/import, IMG Archive export, Dual Texture / Blend Mode
- **v1.5.0** — Native DFF/COL/TXD (no DragonFF), auto-import TXD, numpy DXT, package structure
- **v1.4.x** — UV Editor, Post-Processing VC, Fast Bake, DFF Flags, GPU TXD via NVTT, 50 material limit
- **v1.3.0** — Duplicate material cleanup
- **v1.2.x** — Export improvements (COL3, GTA SA version, progress bar)
- **v1.1.0** — DFF/COL/LOD/TXD export, suffix-based detection
- **v1.0.0** — Initial release

</details>

<details>
<summary><b>🔧 Compatibility</b></summary>

| | |
|---|---|
| **Blender** | 4.2 – 5.1 ✅ |
| **Game** | GTA San Andreas (also compatible with MTA:SA) |
| **OS** | Windows / Linux / macOS |
| **Optional** | NVIDIA GPU (for NVTT texture compression) |

</details>

<details>
<summary><b>📦 Installation</b></summary>

1. Download the `INU_tools/` folder (or zip archive)
2. Copy it into your Blender addons directory:
   ```
   Blender/<version>/scripts/addons/INU_tools/
   ```
3. Open Blender → **Edit → Preferences → Add-ons** → enable **INU_tools(gta_sa)**

</details>

<details>
<summary><b>🚀 Quick Start</b></summary>

Name your objects with suffixes, select them, and click **Export All**:

```
Building01_DFF   ← main mesh
Building01_LOD   ← low-poly LOD
Building01_COL   ← collision
```

The addon auto-assembles DFF + LOD + COL + TXD into one group and exports in a single click.

</details>

<details>
<summary><b>🧰 Features</b></summary>

Legend: 🆕 new in 1.6.3 · ⚡ performance · 🎨 UI · 📦 format support

<details>
<summary><b>📤 Export / Import</b></summary>

| Feature | Detail |
|---|---|
| 📦 DFF export/import | GTA SA v3.6.0.3 |
| 📦 COL export/import | COL3 format |
| 📦 LOD export/import | automatic pairing with DFF |
| 📦 TXD export/import | DXT compression, parallel, GPU via NVTT |
| 🚀 Export All | batch by suffixes `_DFF` / `_LOD` / `_COL` + auto TXD |
| 🗂️ Collection export | exports active collection if nothing selected |
| 🎨 Drag & Drop TXD | drop `.txd` into viewport with auto material creation |
| 🎨 DFF Flags panel | Normals, Light, Modulate Color, UV1/UV2, Day/Night, BinMesh |

</details>

<details>
<summary><b>🗺️ IDE / IPL / IMG</b></summary>

| Feature | Detail |
|---|---|
| 📦 IDE export/import | all sections (objs, tobj, anim, cars, peds, weap, hier, txdp), upsert/remove, auto-LOD |
| 📦 IPL export/import | all sections (inst, cull, grge, enex, pick, cars, auzo, jump, occl, tcyc, zone) + binary IPL (bnry) |
| 🎨 IPL Sections visualization | cull, garage, enex, pickup, cars, auzo, jump, occl, zone as Blender objects |
| 📦 IMG Archive | export/import DFF + LOD + TXD + COL into `.img` (VER2) |
| 🗺️ Import Map | extract from IMG, build `.glb`, auto-sort into collections |
| ⚡ BBox Mode | distant objects → Bounding Box, full models within 300m of selection |
| 🗺️ Map regions | auto-detected from `gta.dat` (LA, SF, VEGAS, COUNTRY…) |
| 🆔 Model ID Manager | file (321–19999), sync scene, load from game, search + pagination |
| 🆔 Assign IDs from number | 🆕 skip occupied IDs, start from any number |
| 🆔 Extend IDs (FLA) | 🆕 extend range for Fastman Limit Adjuster |
| 🎨 IDE Flags | 15 checkboxes (IS_ROAD, IS_TREE, DRAW_LAST…) |
| ⚙️ Custom suffixes/prefixes | `_DFF`, `_LOD`, `_COL`, `LOD`, etc. |
| 🔗 Model Links | dashed-line visualization DFF↔LOD↔COL |
| 🗑️ Remove from IMG | delete DFF/COL/TXD by selected object type |
| 🔍 IMG File List | scrollable UIList with search |
| 🔄 Replace Empty | replace IPL placeholders with scene models |
| 🗺️ X Radar Maker | minimap tiles (8×8, menu, full radar) + pack to TXD |

</details>

<details>
<summary><b>💡 Prelight</b></summary>

| Feature | Detail |
|---|---|
| 💡 Vertex Colors baking | Fast / With Shadows |
| 💡 Raycast shadows | via depsgraph |
| 🎨 Fill Colors | polygon painting with eyedropper + level system |
| 💡 Scatter Light | configurable light scattering |
| 🌓 Day/Night | separate color attributes |
| 💡 LightMap UV2 | 🆕 Add/Toggle/Remove buttons, Multiply blend |
| 🔍 Vertex color analysis | and preview |
| 💡 Prelight COL | vertex colors → COL Day/Night Light |
| 🎨 COL Light Preview | Edge / Threshold / Contrast settings |
| ⚙️ Prelight Presets | save/load bake settings |

<details>
<summary>📹 Tutorial .gif</summary>

![COL Light](gif/col_light.gif)

</details>

</details>

<details>
<summary><b>🎨 Post-Processing</b></summary>

| Feature | Detail |
|---|---|
| 🎨 Smooth | smooth vertex colors between neighboring vertices |
| 🎨 Smooth Between Objects | smooth VC at seams between different objects |
| 🎨 Contrast | contrast adjustment |
| 🎨 Brightness | brightness adjustment |
| 🎨 Gamma | gamma correction |

</details>

<details>
<summary><b>🎯 2DFX Effects</b></summary>

| Feature | Detail |
|---|---|
| 🎆 Create effects | Light, Particle, Ped Attractor, Sun Glare |
| 🔗 Attach/Detach to mesh | coordinates auto-recalculated on export |
| 🔗 Detach All from Mesh | 🆕 batch detach all 2DFX from selected mesh |
| 🎨 Attached 2DFX list | 🆕 in mesh UI with per-item detach buttons |
| ⚙️ Presets | Default, OnAllDay, Lamp Post, BB Pickup, Flashing, Train Crossing, Traffic |
| 🎨 Texture dropdowns | 34 Corona textures, Shadow, Show Mode, Flare Type |
| 📦 2DFX export | RW Light chunk + 2DFX PLG |
| 🎨 Real-time visualization | and editing of all effects |

<details>
<summary>📹 Tutorial .gif</summary>

![2DFX](gif/2DFX.gif)

</details>

</details>

<details>
<summary><b>🎆 Particle Effects (<code>effects.fxp</code>)</b></summary>

> 🆕 **Fully new in 1.6.3** — edit GTA SA particles directly in Blender.

| Feature | Detail |
|---|---|
| 📦 Full parser | text-based `effects.fxp`, 82 effects |
| ⚡ Viewport simulation | 30 FPS, up to 64 particles per emitter |
| 🎨 Effect dropdown | pick from all systems in `effects.fxp` |
| 🎨 Multi-emitter switching | browse emitters within a single system |
| ⚙️ 40+ parameters | color (start/mid/end), size, speed, direction, physics |
| 💨 Emission | rate, life, speed, direction, angle, volume box, offset |
| 🌍 Physics | gravity, friction, wind, noise, jitter, ground bounce |
| 📈 Keyframe editor | curves for size/color/alpha over lifetime |
| 💾 Save back | to `effects.fxp` with auto-backup (`.fxp.bak`) |
| ⚙️ Operators | New / Delete / Switch Emitter / Reload |
| 🎨 Camera-facing billboards | same as Light corona |

</details>

<details>
<summary><b>🎨 Materials</b></summary>

| Feature | Detail |
|---|---|
| 🎨 Environment Map | |
| 🎨 Bump Map | |
| 🎨 Specular | |
| 🎨 UV Animation | |
| 🎨 Reflection Material | |
| 🎨 Dual Texture / Blend Mode | |
| 📦 COL Surface Type | 179 GTA SA types |
| ⚡ Auto-load textures | by material names |
| 🎨 Drag & Drop | create materials from images |
| 🧹 Duplicate cleanup | removes `.001`, `.002` |
| 🔤 Sort materials | by name |

</details>

<details>
<summary><b>🧮 UV Editor</b></summary>

| Feature | Detail |
|---|---|
| 🎲 UV Grid Randomizer | randomize UV positions within grid cells |
| 🎯 Snap to Grid | snap UV islands to nearest cell |
| 📐 9 alignment points | choose UV position within a cell |
| 🔗 Link Polygons | move polygons with overlapping UVs together |

<details>
<summary>📹 Tutorial .gif</summary>

![Random windows](gif/random_windows.gif)

</details>

</details>

<details>
<summary><b>🔍 Check</b></summary>

| Feature | Detail |
|---|---|
| 🔍 Geometry check | loose vertices, edges, N-gons |
| ⚠️ Material limit check | 50 materials for GTA SA |
| 🧹 Material cleanup/sorting | |
| 🎯 LOD/COL → DFF snap | move LOD and COL to DFF position |
| 👁️ Hide DFF/LOD/COL | separately |
| ⚠️ Model ID conflict detection | |
| 🔄 Batch Set Type | 🆕 OBJ / COL / SHA / NON with auto-rename |
| 🔄 Reset Transform | 🆕 zero out Location and Rotation |

<details>
<summary>📹 Tutorial .gif</summary>

![Check](gif/Check.gif)

</details>

</details>

<details>
<summary><b>🌊 Water IO</b></summary>

| Feature | Detail |
|---|---|
| 📦 Import/export | `water.dat` |
| 🌊 waterclear256 texture | with flow animation |
| 🌊 Water types | Default / Shallow, Visible / Invisible |
| 🎯 Snap to grid (×4) | stitch edges |
| 📦 Export Water collection | |

</details>

<details>
<summary><b>🛣️ Path IO</b></summary>

| Feature | Detail |
|---|---|
| 📦 paths.ipl | vehicle/ped paths for `gta.dat` |
| 📦 tracks.dat | train tracks and stations |
| 📦 NODES.dat | compiled path nodes, multi-file import 🆕 |
| 🛣️ Create paths | convert curves/edges to paths |
| ⚙️ Auto-split | 12-node groups |
| 🗺️ NODES export | auto-split by 8×8 map zones 🆕 |

</details>

<details>
<summary><b>🦴 Characters (Skinned DFF)</b></summary>

| Feature | Detail |
|---|---|
| 🦴 Import skeleton | Armature + vertex weights + bone matrices |
| 📦 Export skinned DFF | byte-perfect round-trip |
| 🎬 IFP animations | import `ped.ifp` (294+ anims), search, apply |
| ✅ Compatible | Kams Script DFF and original game models |

</details>

<details>
<summary><b>🔌 Integrations</b></summary>

| Integration | Purpose |
|---|---|
| Itera Tools 3 | Vertex Lit Linear / Quickstart |
| LightMap (beta_MTA) | apply pre-baked lightmap via MTA script |
| Pipeline | Building / Reflections |
| Hotkeys | `Shift+T`, `Shift+A` |
| Localization | RU / EN |

</details>

</details>

<details>
<summary><b>🧭 UI Panels</b></summary>

| Location | Panel | What's there |
|---|---|---|
| `Properties > Scene` | **INU Tools** | IDE/IPL/IMG paths, textures, NVTT, suffixes, ID manager, presets |
| `Properties > Object` | **GTA SA Object** | object type (OBJ/COL/SHA/2DFX), DFF Flags, Pipeline, UV Maps |
| `Properties > Object` | **GTA SA: IDE / IPL** 🆕 | Model ID, Draw Dist, LOD Dist, IDE Flags, Interior, conflicts |
| `Properties > Material` | **GTA SA Material Effects** | Environment Map, Bump Map, Reflection, Specular, UV Animation |
| `Properties > Material` | **COL Surface Type** | collision surface type selection |
| `View3D > Sidebar (N)` | **GTA Tools** | export/import, prelight, 2DFX, particles, vertex paint |
| `UV Editor > Sidebar (N)` | **GTA Tools** | UV tools |

</details>

<details>
<summary><b>⌨️ Hotkeys</b></summary>

| Key | Action |
|---|---|
| `Shift+T` | Open / close UV Editor |
| `Shift+A` | GTA SA → Army.dff (ped) / Admiral.dff (car) |

</details>

<details>
<summary><b>📹 Video Tutorial</b></summary>

[![IDE/IPL/IMG/Map Tutorial](https://img.youtube.com/vi/Jw_R9QFYxWE/0.jpg)](https://www.youtube.com/watch?v=Jw_R9QFYxWE)

> Export & Import IDE / IPL / IMG / Map

</details>

## 🙏 Credits

Inspired by and partially compatible with:

- **[DragonFF](https://github.com/Parik27/DragonFF)** (Parik, GPL-3.0) — Blender addon for RenderWare formats. INU_tools uses compatible material and object property names for easy transition between addons.
- **[RenderWare](https://en.wikipedia.org/wiki/RenderWare)** — GTA SA game engine, DFF/COL/TXD format documentation.

### Author

**INU** — addon author (Discord: `1.n.u`)
https://discord.gg/sqtGAVTGdy

### License

[GPL-3.0](LICENSE)
