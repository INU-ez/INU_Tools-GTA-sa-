<div align="center">

![INU Tools Logo](https://github.com/INU-ez/INU_Tools-GTA-sa-/blob/5e82d62dd40105c557ef9cb6be261bb70b63d3a2/logo.jpg)

# INU_Tools (GTA SA)

**Blender addon for GTA San Andreas modding — full pipeline from modeling to IMG archive.**

<p>
  <img src="https://img.shields.io/badge/Blender-4.2%E2%80%935.1-orange?logo=blender" alt="Blender">
  <img src="https://img.shields.io/badge/Version-1.6.3-green" alt="Version">
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

- 🎨 **Native DFF / COL / TXD** — built-in RenderWare parser and writer, zero external dependencies
- 🗺️ **Full map pipeline** — IMG → Blender → IPL / IDE round-trip
- 💡 **Prelight & 2DFX** — vertex colors, corona lights, day/night
- 🎆 **effects.fxp editor** — live particle simulation in viewport
- 🦴 **Skinned DFF + IFP** — import peds with animations
- 🌊 **Water & Paths** — water.dat, tracks.dat, NODES.dat

</td>
<td width="50%" valign="top">

![2DFX tutorial](gif/cj-explosion.gif)

</td>
</tr>
</table>

## 🔮 Coming Soon

Planned for upcoming releases:

- 🚗 **Vehicles** — full import/export of cars (hierarchy: wheels, doors, damage dummies, color slots)
- 🎨 **Custom GTA Material** — dedicated material plugin with vehicle colors and blend modes
- 💥 **Breakable Objects** — breakable mesh extension (0x253F2FD in DFF)
- 📦 **COL inside DFF** — pack collision directly inside DFF (for vehicles and world objects)
- 🎬 **IFP ANPK** — support for older animation format (GTA3 / Vice City)
- 🖼️ **Bitmaps Manager** — missing texture report, batch copy, duplicate search

> [!NOTE]
> The addon is under active development. Bug reports are welcome in [Issues](../../issues).

## 🆕 What's new in 1.6.3

- 🎆 **Particle Effects** — full `effects.fxp` editor (82 effects, 30 FPS simulation, 40+ parameters)
- 🧩 **Object Properties** — new *GTA SA: IDE / IPL* panel (Model ID, Draw Dist, Flags, Interior)
- 💡 **LightMap UV2** — Add / Toggle / Remove buttons (Multiply blend on second UV channel)
- 🎯 **2DFX UI** — Detach All from Mesh, attached effects list in mesh UI
- 🆔 **ID Manager** — Assign from ID…, Extend IDs (FLA)
- 🛣️ **Nodes** — multi-file import, export with 8×8 zone splitting

<details>
<summary>Older releases</summary>

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

### License

[GPL-3.0](LICENSE)
