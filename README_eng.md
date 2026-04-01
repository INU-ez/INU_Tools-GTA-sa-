![image alt](https://github.com/INU-ez/INU_Tools-GTA-sa-/blob/5e82d62dd40105c557ef9cb6be261bb70b63d3a2/logo.jpg)

# INU_Tools (GTA SA)

![Blender](https://img.shields.io/badge/Blender-4.2+-orange?logo=blender)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)
![Version](https://img.shields.io/badge/Version-1.6.0-green)
![Views](https://komarev.com/ghpvc/?username=INU-ez&color=orange&style=flat-square&label=REPO+VIEWS)

> **[Русская версия / Russian version](README.md)**

> [!NOTE]
> The addon is under active development. Bug reports are welcome in [Issues](../../issues).

INU_Tools is a Blender addon for working with GTA San Andreas models.
It provides tools for export, prelighting, and 3D model preparation.
Starting from v1.5.0, the addon has its own DFF, COL, and TXD export (no DragonFF dependency).

## Features

<details>
<summary><b>Export / Import</b></summary>

> - ✅ DFF export/import (GTA SA v3.6.0.3)
> - ✅ COL export/import (COL3 format)
> - ✅ LOD export/import
> - ✅ TXD export/import (DXT compression, parallel processing, GPU via NVIDIA Texture Tools)
> - ✅ Export All — batch export by suffixes `_DFF` / `_LOD` / `_COL` + automatic TXD assembly
> - ✅ Collection export — if nothing selected, exports all objects from active collection

</details>

<details>
<summary><b>IDE / IPL / IMG</b></summary>

> - ✅ IDE export/import — all sections (objs, tobj, anim, cars, peds, weap, hier, txdp), upsert/remove, auto-LOD
> - ✅ IPL export/import — all sections (inst, cull, grge, enex, pick, cars, auzo, jump, occl, tcyc, zone), binary IPL (bnry)
> - ✅ IPL Sections — visualization of sections (cull, garage, enex, pickup, cars, auzo, jump, occl, zone) as Blender objects
> - ✅ IMG Archive — export/import DFF+LOD+TXD+COL into .img archives (VER2)
> - ✅ Import Map — extract resources from IMG, build map as .glb, import with auto-sorting into collections
> - ✅ BBox Mode — toggle distant objects to Bounding Box, near selection (300m) — full models
> - ✅ Map regions — auto-detected from gta.dat (LA, SF, VEGAS, COUNTRY, etc.)
> - ✅ Model ID Manager — free ID list, auto-assign to selected objects
> - ✅ IDE Flags — 15 checkboxes with descriptions (IS_ROAD, IS_TREE, DRAW_LAST, etc.)
> - ✅ Customizable model suffixes (_DFF, _LOD, _COL)

</details>

<details>
<summary><b>Prelight</b></summary>

> - ✅ Vertex Colors baking (Fast / With Shadows)
> - ✅ Raycast shadows via depsgraph
> - ✅ Fill Colors — polygon painting with eyedropper and level system
> - ✅ Scatter Light — light scattering with configurable parameters
> - ✅ Day/Night — separate color attributes for day and night
> - ✅ Vertex color analysis and preview
> - ✅ Prelight COL — convert vertex colors to COL Day/Night Light
> - ✅ COL Light Preview — visualization with Edge/Threshold/Contrast settings
> - ✅ Prelight Presets — save/load bake settings
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Itera_Inu_tools](gif/col_light.gif)
>
> </details>

</details>

<details>
<summary><b>Post-Processing</b></summary>

> - ✅ Smooth — smooth vertex colors between neighboring vertices
> - ✅ Smooth Between Objects — smooth vertex colors at seams between different objects
> - ✅ Contrast — contrast adjustment
> - ✅ Brightness — brightness adjustment
> - ✅ Gamma — gamma correction

</details>

<details>
<summary><b>2DFX Effects</b></summary>

> - ✅ Create 2DFX effects (Light, Particle, Ped Attractor, Sun Glare)
> - ✅ Attach/Detach 2DFX to mesh — coordinates auto-recalculated on export
> - ✅ Presets: Default, OnAllDay, Lamp Post, Lamp Post Coast, BB Pickup, Flashing, Train Crossing, Traffic
> - ✅ Dropdowns for Corona Texture (34 textures), Shadow Texture, Show Mode, Flare Type
> - ✅ 2DFX export to DFF (RW Light chunk + 2DFX PLG)
> - ✅ Real-time visualization and editing of all effects
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Itera_Inu_tools](gif/2DFX.gif)
>
> </details>

</details>

<details>
<summary><b>Materials</b></summary>

> - ✅ Environment Map
> - ✅ Bump Map
> - ✅ Specular
> - ✅ UV Animation
> - ✅ Reflection Material
> - ✅ Dual Texture / Blend Mode
> - ✅ COL Surface Type (179 GTA SA types)
> - ✅ Auto-load textures by material names
> - ✅ Drag & Drop — create materials by dragging images
> - ✅ Duplicate cleanup (.001, .002)
> - ✅ Sort materials by name

</details>

<details>
<summary><b>UV Editor</b></summary>

> - ✅ UV Grid Randomizer — randomize UV positions within grid cells
> - ✅ Snap to Grid — snap UV islands to the nearest cell
> - ✅ 9 alignment points — choose UV position within a cell
> - ✅ Link Polygons — move polygons with overlapping UVs together
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![random_windows](gif/random_windows.gif)
>
> </details>

</details>

<details>
<summary><b>Check</b></summary>

> - ✅ Geometry check — loose vertices, edges, N-gons
> - ✅ Material limit check (50 for GTA SA)
> - ✅ Material cleanup/sorting
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Check](gif/Check.gif)
>
> </details>

</details>

<details>
<summary><b>Water IO</b></summary>

> - ✅ Import/export water.dat
> - ✅ waterclear256 texture with flow animation
> - ✅ Water types: Default/Shallow, Visible/Invisible
> - ✅ Snap to grid (x4), stitch edges
> - ✅ Export Water collection

</details>

<details>
<summary><b>Path IO</b></summary>

> - ✅ Import/export paths.ipl (vehicle/ped paths for gta.dat)
> - ✅ Import/export tracks.dat (train tracks, stations)
> - ✅ Import NODES.dat (compiled path nodes)
> - ✅ Create paths, convert curves/edges to paths
> - ✅ Auto-split into 12-node groups

</details>

<details>
<summary><b>Characters (Skinned DFF)</b></summary>

> - ✅ Import DFF with skeleton (Armature), vertex weights, bone matrices
> - ✅ Export skinned DFF (byte-perfect round-trip)
> - ✅ IFP animations: import ped.ifp (294+ animations), search, apply to skeleton
> - ✅ Compatible with Kams Script DFF and original game models

</details>

<details>
<summary><b>Integrations</b></summary>

> - ✅ Support Itera Tools 3 (Vertex Lit Linear / Quickstart)
> - ✅ Lightmap Generator (MTA)
> - ✅ Pipeline (Building / Reflections)
> - ✅ Hotkeys (Shift+T, Shift+A)
> - ✅ Localization (RU / EN)

</details>

## Installation

1. Download the `INU_tools/` folder (or zip archive)
2. Place `INU_tools/` into `Blender/<version>/scripts/addons/`
3. Blender → Edit → Preferences → Add-ons → enable "INU_tools(gta_sa)"

## Usage

The addon adds panels to:
- **Properties > Scene > INU Tools** — IDE/IPL/IMG paths, textures, NVTT, model suffixes, ID manager, presets
- **Properties > Object > GTA SA Object** — object type (OBJ/COL/SHA/2DFX), DFF Flags, Pipeline, UV Maps
- **Properties > Material > GTA SA Material Effects** — Environment Map, Bump Map, Reflection, Specular, UV Animation
- **Properties > Material > COL Surface Type** — collision surface type selection
- **View3D > Sidebar (N) > GTA Tools** — export/import, prelight, 2DFX, vertex paint
- **UV Editor > Sidebar (N) > GTA Tools** — UV tools

<details>
<summary><b>Hotkeys</b></summary>

> | Key | Action |
> |-----|--------|
> | `Shift+T` | Open / close UV Editor |
> | `Shift+A` | GTA SA → Army.dff (ped) / Admiral.dff (car) |

</details>

#### Quick Export

Name objects with suffixes (`Model_DFF`, `Model_LOD`, `Model_COL`), select them, and click **Export All**.

## Requirements

- **Blender 4.2+**
- NVIDIA Texture Tools — optional, for GPU texture compression (auto-detected)
- Itera Tools 3 — optional, for vertex lighting (https://itera.gumroad.com/l/IteraTools3)

<details>
<summary><b>Changelog</b></summary>

- **v1.6.0** — Import Map: full workflow (Extract → Build .glb → Import), auto-sort into collections (Buildings/Vegetation/Props/Small/LOD), duplicates in _Instances sub-collections; BBox Mode: toggle distant objects to Bounding Box with 300m radius from selection; IPL ZONE section: parse/write/visualize map zones; dynamic map regions from gta.dat (replaces hardcoded); TXD: fixed RASTER_888 decompression (32-bit BGRX), improved DXT detection via compression_flag; GPU NVTT auto-detect (no toggle button); UI: merged Export/Import panels, compact IDE/IPL/IMG layout, Check panel translated to Russian; collection export (active collection if nothing selected); removed: Fake mode, Bounds mode, LOD view, Auto-discover button; Blender 4.2+ compatibility
- **v1.5.3** — Skinned DFF import/export: skeleton, vertex weights, bone matrices; IFP animations: import 294+ anims from ped.ifp, apply to skeleton, search selector; Water IO: import/export water.dat, waterclear256 texture, flow animation, water types; Path IO: import/export paths.ipl, tracks.dat, NODES.dat, create/convert paths; Bin Mesh PLG — correct material indices for skinned models; user config in INU_Preset folder (preserved on updates); Blender 5.1 compatibility (layered actions API); fixed SkinPLG reader (bones_used, num_used, max_weights)
- **v1.5.2** — Refactoring: modular structure (tools/, data/); COL Light Preview: active Day/Night attribute, brightness threshold, border-only numbers, auto-update on transform; Model ID Manager (model_ids.txt); auto-LOD in IDE/IPL/IMG export; Export All with 2DFX; LOD in IMG export; batch IMG export; VC Smooth between objects; customizable model suffixes; material sorting in panel; collapsible sections in INU Tools
- **v1.5.1** — IDE/IPL export/import (upsert/remove into existing files); IMG Archive export (DFF+TXD+COL into .img); Dual Texture and Blend Mode; removed Vertex Alpha (not supported by GTA SA)
- **v1.5.0** — Native DFF/COL/TXD import and export (no DragonFF); auto-import TXD when importing DFF; numpy DXT decompression; material sorting by name; addon converted to package structure (`INU_tools/`); fixed prelight preview on export; Blender 5.1 compatibility
- **v1.4.8** — Shift+T to toggle UV Editor
- **v1.4.7** — COL Surface Type with 13 category groups; Day/Night Light + Brightness in Material Properties; Prelight COL — convert vertex colors to COL Light with auto-split materials by brightness (0-15)
- **v1.4.6** — Post-Processing vertex colors (Smooth, Contrast, Brightness, Gamma); Fast Bake with shadows (raycast); DFF Flags panel
- **v1.4.5** — Export All: batch export of multiple groups; Lightmap Generator returned to UI
- **v1.4.4** — Fill Colors, Scatter Light, Drag-and-Drop textures, panel moved to Properties > Scene
- **v1.4.3** — Fixed DXT3 transparency; skip textures not divisible by 4
- **v1.4.2** — GPU TXD mode via NVIDIA Texture Tools
- **v1.4.1** — Parallel TXD processing (up to 8x faster)
- **v1.4.0** — UV Editor panel, Snap to Grid, polygon linking, 50 material limit
- **v1.3.0** — Duplicate material cleanup
- **v1.2.x** — Export improvements series (COL3, GTA SA version, progress bar, auto-Collision Object)
- **v1.1.0** — DFF/COL/LOD/TXD export, suffix-based detection
- **v1.0.0** — Initial release

</details>

> **[Comparison with other tools (DragonFF, GTA_Tools, DeniskaMax, etc.)](COMPARISON.md)**

## Credits

Inspired by and partially compatible with:

- **[DragonFF](https://github.com/Parik27/DragonFF)** (Parik, GPL-3.0) — Blender addon for RenderWare formats. INU_tools uses compatible material and object property names for easy transition between addons.
- **[RenderWare](https://en.wikipedia.org/wiki/RenderWare)** — GTA SA game engine, DFF/COL/TXD format documentation.

#### Author

- **INU** — addon author (Discord: 1.n.u)

#### License

[GPL-3.0](LICENSE)
