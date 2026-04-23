# INU_Tools (GTA SA) — Documentation

> **[Русская версия / Russian version](DOCS_rus.md)**

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Export / Import](#export--import)
  - [DFF (Models)](#dff-models)
  - [COL (Collision)](#col-collision)
  - [TXD (Textures)](#txd-textures)
  - [Export All (Batch)](#export-all-batch)
  - [Collection Export](#collection-export)
- [IDE / IPL / IMG](#ide--ipl--img)
  - [Import Map Workflow](#import-map-workflow)
  - [IDE (Definitions)](#ide-definitions)
  - [IPL (Placement)](#ipl-placement)
  - [IPL Sections](#ipl-sections)
  - [IMG Archive](#img-archive)
  - [BBox Mode](#bbox-mode)
  - [Suffixes / Prefixes](#suffixes--prefixes)
  - [LOD Detection](#lod-detection)
  - [Model ID Manager](#model-id-manager)
- [Materials](#materials)
  - [GTA SA Material Effects](#gta-sa-material-effects)
  - [COL Surface Types](#col-surface-types)
  - [Textures](#textures)
- [Prelight (Vertex Colors)](#prelight-vertex-colors)
  - [Baking](#baking)
  - [Fill Colors](#fill-colors)
  - [Scatter Light](#scatter-light)
  - [Post-Processing](#post-processing)
  - [COL Light](#col-light)
  - [Presets](#presets)
- [2DFX Effects](#2dfx-effects)
- [Particle Effects (effects.fxp)](#particle-effects-effectsfxp-new-in-163)
- [UV Tools](#uv-tools)
- [Check](#check)
- [Characters (Skinned DFF)](#characters-skinned-dff)
- [Water IO](#water-io)
- [Path IO](#path-io)
- [LightMap (beta_MTA)](#lightmap-beta_mta)
- [Integrations](#integrations)
- [Experimental (v1.6.4)](#experimental-v164)
  - [Map Export](#map-export)
  - [Binary IPL Write](#binary-ipl-write)
  - [UV Animation in DFF](#uv-animation-in-dff)
  - [Breakable Objects](#breakable-objects)
  - [IFP Batch Import](#ifp-batch-import)
  - [GTA Material Panel](#gta-material-panel)
  - [Bitmaps Manager](#bitmaps-manager)
  - [CST IO](#cst-io)
  - [Vehicle Scale Helper](#vehicle-scale-helper)
  - [Train Station Markers](#train-station-markers)
  - [Roadblocks & Traffic Lights](#roadblocks--traffic-lights)
  - [FLA4 Path Format](#fla4-path-format)
- [Technical Reference](#technical-reference)
  - [Project Structure](#project-structure)
  - [Core Modules](#core-modules)
  - [File Formats](#file-formats)
  - [Object Properties (INUObjectProps)](#object-properties-inuobjectprops)
  - [Material Properties (INUMaterialProps)](#material-properties-inumaterialprops)
  - [Scene Properties](#scene-properties)

---

## Installation

1. Download the `INU_tools/` folder (or zip archive)
2. Place `INU_tools/` into Blender addons folder:
   - **Windows:** `%APPDATA%/Blender Foundation/Blender/<version>/scripts/addons/`
   - **Linux:** `~/.config/blender/<version>/scripts/addons/`
   - **macOS:** `/Users/<name>/Library/Application Support/Blender/<version>/scripts/addons/`
3. Blender → Edit → Preferences → Add-ons → enable **"INU_tools(gta_sa)"**

**Requirements:**
- Blender 4.2+
- NVIDIA Texture Tools — optional, for GPU texture compression (auto-detected)
- Itera Tools 3 — optional, for vertex lighting

**Settings persistence:** all paths (Game Root, IDE, IPL, IMG, textures, NVTT) are saved in `INU_Preset/paths.json` next to the addons folder. Settings survive addon updates and are restored automatically when Blender starts.

---

## Quick Start

### Export a model to GTA SA

1. Name objects with suffixes: `mybuilding_DFF`, `mybuilding_COL`, `mybuilding_LOD`
2. Set **Model ID**, **TXD Name**, **Draw Distance** in object properties (`obj.inu`)
3. Select all, click **Export All** → choose folder
4. Output: `mybuilding.dff`, `mybuilding.col`, `LODmybuilding.dff`, `mybuilding.txd`

### Import the entire GTA SA map

1. Set **Game Root** to GTA SA folder (e.g. `D:\GTA San Andreas\`)
2. Click **Extract Resources** — extracts DFF/COL/textures from IMG (one-time)
3. Click **Build Map .glb** — converts to glTF (one-time per region)
4. Click **Import Map .glb** — loads into Blender with auto-sorted collections

### Hotkeys

| Key | Action |
|-----|--------|
| `Shift+T` | Toggle UV Editor |
| `Shift+A` | Add GTA SA model (Army.dff / Admiral.dff) |

---

## Export / Import

**Panel:** View3D → Sidebar (N) → GTA Tools → Export / Import

### DFF (Models)

| Button | Operator | Description |
|--------|----------|-------------|
| Import DFF | `gtatools.import_dff` | Import .dff file with mesh, materials, UV maps |
| Export DFF | `gtatools.export_dff` | Export selected mesh to .dff (GTA SA v3.6.0.3) |

**Export includes:** geometry, materials, vertex colors (Day/Night), UV maps, normals, 2DFX effects, BinMesh PLG.

**Auto TXD:** when importing DFF, automatically imports .txd from the same directory if found.

> 💡 **Example — import a single model:** File → Import → GTA SA DFF → pick `admiral.dff`. The addon parses geometry, materials, UV. If `admiral.txd` sits next to it, textures are applied automatically.

> 💡 **Example — export a single mesh:** select mesh → N → Export / Import → **Export DFF** → choose path → saves with current materials and vertex colors.

### COL (Collision)

| Button | Operator | Description |
|--------|----------|-------------|
| Import COL | `gtatools.import_col` | Import .col with surface materials |
| Export COL | `gtatools.export_col` | Export as COL3 format |

COL export automatically sets object type to Collision, centers at origin, and writes surface material IDs.

> 💡 **Example:** create a cube, name it `mybuilding_COL`, assign a material with `col_mat_index = 0` (default asphalt) in Properties → Material → **COL Surface Type**. Select → **Export COL** → you get `mybuilding.col` with the correct surface material.

### TXD (Textures)

| Button | Operator | Description |
|--------|----------|-------------|
| Import TXD | `gtatools.import_txd` | Extract textures and assign to materials |
| Export TXD | `gtatools.export_txd` | Compile textures into .txd archive |

**GPU mode:** if NVIDIA Texture Tools (NVTT) is installed and path is configured in Settings → NVTT, compression uses GPU automatically. Otherwise falls back to CPU.

**Supported formats:** DXT1 (opaque), DXT3 (sharp alpha), DXT5 (smooth alpha). Auto-detected based on alpha channel.

> 💡 **Example — quick TXD build:** a mesh with 3 textures (brick, window with alpha, logo) → select → **Export TXD** → you get a `.txd` where brick is DXT1, window is DXT5, logo is DXT3 — format auto-picked based on each image's alpha channel.

### Export All (Batch)

| Button | Operator | Description |
|--------|----------|-------------|
| Export All (To Folder) | `gtatools.export_all` | Batch export DFF+COL+LOD+TXD |

Select objects with suffixes (`_DFF`, `_LOD`, `_COL`), click Export All, choose output folder.

**Toggles:** DFF / COL / LOD / TXD — enable/disable each format.

**Pipeline:** None / Building (Day/Night vertex colors) / Reflections (window reflections).

> 💡 **Example — export a building with LOD and collision:** you have three meshes `hospital_DFF`, `hospital_LOD`, `hospital_COL`. Select all three → **To Folder** → you get 4 files at once: `hospital.dff` + `hospitalLOD.dff` + `hospital.col` + `hospital.txd`. Ready to drop into the game.

### Collection Export

If **no objects are selected**, Export All takes all mesh objects from the **active collection** (including child collections). This allows exporting an entire collection without selecting everything.

> 💡 **Example:** `MyCity/Buildings` collection holds 20 buildings (40 meshes — HD + LOD). Deselect everything → activate the collection → **To Folder** → 40 dff + 20 txd + ... all appear on disk at once.

### File Menu

All formats are also accessible via **File > Import** and **File > Export**:
- GTA SA DFF (.dff)
- GTA SA COL (.col)
- GTA SA TXD (.txd)
- GTA SA IDE (.ide)
- GTA SA IPL (.ipl)

### Drag & Drop

Drag PNG/JPG/TGA images from File Browser into the 3D viewport to automatically create a material with that texture assigned.

---

## IDE / IPL / IMG

**Panel:** View3D → Sidebar (N) → GTA Tools → IDE / IPL / IMG
**Settings:** Properties → Scene → INU Tools → Import Map

### Import Map Workflow

**Step 1: Setup**
- Set **Game Root** to GTA SA installation folder
- Select **Region** (auto-detected from gta.dat: LA, SF, VEGAS, COUNTRY, etc.)

**Step 2: Extract Resources**
- Click **Extract Resources** — extracts all DFF, COL, and textures from IMG archives into `.inu_cache/` folder next to your .blend file (so save the .blend first)
- This is slow but only needed once — already extracted files are skipped on re-run

**Step 3: Build .glb**
- Click **Build Map .glb** — converts DFF models with IPL positions into a single .glb file
- One file per region, cached in `.inu_cache/`

**Step 4: Import**
- Click **Import Map .glb** — opens file browser, select one or more .glb files
- Objects auto-sorted into collections:
  - **Map_Buildings** — draw distance 300+
  - **Map_Props** — draw distance 100-299
  - **Map_Small** — draw distance <100
  - **Map_Vegetation** — trees, grass, plants
  - **Map_LOD** — LOD models
- Duplicates (`.001`, `.002`) moved to `_Instances` sub-collections

### IDE (Definitions)

> **Per-object properties** *(new in 1.6.3):* Model ID, Draw Distance, LOD Distance, IDE Flags, Interior, LOD index now live in **Properties → Object → "GTA SA: IDE / IPL"** (previously in N-panel). The same panel shows **ID conflict detection** — if multiple objects share the same Model ID, the addon highlights the error with names of conflicting objects.


IDE files define model properties: ID, texture dictionary, draw distance, flags.

| Button | Operator | Description |
|--------|----------|-------------|
| Add | `gtatools.upsert_ide` | Insert/update entry in IDE file (auto-LOD) |
| Remove | `gtatools.remove_ide` | Remove entry by Model ID |
| Import | `gtatools.import_ide` | Load definitions → apply to matching objects |
| Export | `gtatools.export_ide` | Write selected objects as IDE file |

**All sections supported:** objs, tobj, anim, cars, peds, weap, hier, txdp.

**Auto-LOD:** when adding DFF+LOD pair, the following are assigned automatically:
- **Model ID:** LOD = DFF ID + 1 (e.g. DFF ID 3500 → LOD ID 3501)
- **Draw Distance:** LOD = 999 (maximum visibility). The HD model is visible up to its draw distance (e.g. 299m), then LOD appears and stays visible up to 999m
- **TXD:** LOD uses the same texture dictionary as DFF

> 💡 **Example — add a building to mymap.ide:** select `building01_DFF` and `building01_LOD` → Object Properties → **INU Tools: Model** → set `Model ID = 3500` on DFF → N → IDE / IPL / IMG → IDE section → set path to `mymap.ide` → **Add**. Two lines get written: `3500, building01, building01, 299` and `3501, LODbuilding01, building01, 999`.

**IDE Flags** (15 checkboxes in object properties):

| Flag | Bit | Description |
|------|-----|-------------|
| IS_ROAD | 1 | Road surface |
| DRAW_LAST | 4 | Transparent, draw last |
| ADDITIVE | 8 | Additive blending |
| NO_ZBUFFER_WRITE | 64 | Don't write to Z-buffer |
| NO_SHADOWS | 128 | Don't receive shadows |
| GLASS_TYPE_1 | 512 | Breakable glass |
| GLASS_TYPE_2 | 1024 | Cracked glass |
| GARAGE_DOOR | 2048 | Garage door |
| DAMAGABLE | 4096 | Destructible |
| IS_TREE | 8192 | Tree, sways in wind |
| IS_PALM | 16384 | Palm tree, sways in wind |
| NO_FLYER_COL | 32768 | No collision with aircraft |
| IS_TAG | 1048576 | Graffiti tag |
| NO_BACKFACE_CULL | 2097152 | Render both sides |
| BREAKABLE_STATUE | 4194304 | Breakable statue |

### IPL (Placement)

IPL files define object positions, rotations, and LOD links on the map.

| Button | Operator | Description |
|--------|----------|-------------|
| Add | `gtatools.upsert_ipl` | Insert/update placement (auto-LOD linking) |
| Remove | `gtatools.remove_ipl` | Remove by Model ID. When an entry is deleted from the middle of the file, all LOD indices of remaining objects are automatically recalculated — otherwise the game would reference wrong lines and may crash |
| Import | `gtatools.import_ipl` | Place objects or create Empties at positions |
| Export | `gtatools.export_ipl` | Write selected objects with world transforms |

**Quaternion conversion:** GTA SA stores (X,Y,Z,W) conjugated, Blender uses (W,X,Y,Z). Conversion is automatic.

**Binary IPL:** files with `bnry` header (inside IMG archives) are read automatically.

> 💡 **Example — place a model on the map:** imported `building01.dff`, set Model ID 3500. Move/rotate it freely in the scene → IPL → **Export** → pick `mymap.ipl` → the line `3500, building01, 0, X, Y, Z, QX, QY, QZ, QW, lod` is written with the real world coordinates.

### IPL Sections

All IPL sections are supported for import/export as Blender objects:

| Section | Collection | Visualization |
|---------|-----------|---------------|
| cull | IPL_Cull | Wireframe cube |
| grge | IPL_Garage | Empty (cube) |
| enex | IPL_Enex | Empty (axes) — enter + exit points |
| pick | IPL_Pickup | Empty (sphere) |
| cars | IPL_Cars | Empty (arrow) |
| auzo | IPL_Auzo | Cube mesh or Empty (sphere) |
| jump | IPL_Jump | Cube mesh — start + target + camera |
| occl | IPL_Occl | Wireframe cube with rotation |
| zone | IPL_Zone | Wireframe cube |

| Button | Operator | Description |
|--------|----------|-------------|
| Sections IPL ↓ | `gtatools.import_ipl_sections` | Import all sections from IPL file |
| Sections IPL ↑ | `gtatools.export_ipl_sections` | Export all section collections to IPL file |
| Replace Empty | `gtatools.replace_ipl_placeholders` | When IPL import can't find a model, it creates an Empty with `_empty` suffix in IPL_Empty collection. After adding the model to the scene, click this button — the model moves to the Empty's position and the Empty is removed |

### IMG Archive

| Button | Operator | Description |
|--------|----------|-------------|
| Import from IMG | `gtatools.import_from_img` | Extract and import models by IDE/IPL listing |
| Export to IMG | `gtatools.export_to_img` | Pack DFF+COL+TXD directly into .img archive |

**Export toggles:** DFF / COL / TXD — choose what to pack.

**Import options:** Skip LOD / Load TXD.

> 💡 **Example — batch upload to gta3.img:** you have 10 buildings ready to export. Set `gta3.img` path in Import Map settings → select the buildings → **Export to IMG** → a UIList dialog opens showing all model + TXD names (editable). Click OK — all DFF+COL+TXD get written to the archive. After that make sure to **Rebuild Archive** in your IMG tool (otherwise the game keeps the old versions).

### BBox Mode

| Button | Operator | Description |
|--------|----------|-------------|
| BBox: ON/OFF | `gtatools.toggle_bbox` | Toggle Bounding Box display for map objects |

When enabled, all Map_ collection objects switch to `BOUNDS` display. Objects within 300m of the selected object stay as `TEXTURED`. Updates automatically when selection changes.

> 💡 **Example:** imported the LA map (5000+ objects), Blender struggles with viewport rendering. Toggle **BBox: ON** → distant buildings become wireframe boxes, objects within 300m of your selected one stay fully textured. Viewport flies.

### Suffixes / Prefixes

**Panel:** N-sidebar (`N`) → GTA Tools → **Export / Import** → ▸ Suffixes / Prefixes *(collapsible section, same style as DFF Flags)*

Determine how the addon recognizes model type by object name in Blender.

**Suffixes** (end of name):
- DFF: `_DFF` → `mybuilding_DFF` recognized as DFF model
- LOD: `_LOD` → `mybuilding_LOD` recognized as LOD model
- COL: `_COL` → `mybuilding_COL` recognized as collision

**Prefixes** (start of name):
- LOD: `LOD` → `LODmybuilding` recognized as LOD model

You can use **either suffix or prefix** for each type — not both. When entering one, the other is automatically cleared. If neither is set — the model is treated as DFF.

When exporting IDE/IPL, LOD models are always written with `LOD` prefix (GTA SA format).

> 💡 **Example — switch project convention:** your old project uses suffixes `_DFF`/`_LOD`/`_COL`, but a new teammate works with `LOD` prefix and no DFF suffix. Open Suffixes/Prefixes in the Export panel → clear `Suffix DFF` and `Suffix LOD` → type `LOD` into **Prefix LOD**. All scene objects are now recognized by the new convention without renaming (verify via Object Properties → INU Tools: Model → "By name: ...").

### LOD Detection

Vanilla GTA SA and Rockstar's own tools ship LOD models with several naming conventions — not only the standard `LOD<name>` prefix. When importing maps, INU Tools detects LODs with a two-layer strategy:

**Layer 1 (authoritative) — IPL cross-reference.** Every IPL `inst` line has a `lod_index` field pointing to the LOD companion's line number in the same file. Any instance another line references is marked as LOD regardless of its filename. This is 100% reliable for properly authored maps.

**Layer 2 (fallback) — name heuristic.** For loose imports, broken IPLs, or scene operations where no IPL context is available, the addon recognises these patterns:

| Name | Treated as LOD? | Stripped to | Why |
|---|---|---|---|
| `LOD_foo` | ✅ | `foo` | prefix + trailing `_` consumed |
| `LODfoo`, `lodfoo` | ✅ | `foo` | prefix without separator |
| `foo_LOD`, `foo_lod` | ✅ | `foo` | suffix `_LOD` consumed whole |
| `tatar_str_1LOD` | ✅ | `tatar_str_1` | bare suffix adjacent to digit |
| **`modeLODlaett`** | ✅ | `modelaett` | embedded uppercase `LOD` with lowercase neighbor (legacy Rockstar splice) |
| **`foo_LOD_bar`** | ❌ | — | `LOD` surrounded by `_` on both sides → treated as a literal token in the middle |
| **`bar_LOD_baz_LOD_qux`** | ❌ | — | same — every occurrence is between separators |
| `CLOD`, `FLOOD` | ❌ | — | all-uppercase, no lowercase neighbour |
| `explode`, `clodmock` | ❌ | — | no uppercase `LOD` (case-sensitive check) |

**Embedded rule in detail.** The detector looks for a case-sensitive uppercase `LOD` substring. It only flags a match if at least one directly-adjacent character is lowercase — so `modeLODlaett` (neighbours `e`/`l` are lowercase) is recognised as LOD, but `foo_LOD_bar` (both neighbours are `_`) is not. This matches Rockstar's legacy pattern where `LOD` was spliced into the middle of a base name (e.g. base `modelaett` → LOD `modeLODlaett`) while avoiding false positives on names that use `_LOD_` as a literal token.

**When it matters.** The strip logic is used during map import renaming, `Replace IPL Placeholders`, collection sorting, and COL/DFF pair matching. Getting the base name right is what lets the importer send the model to `Map_LOD` instead of `Map_DFF_*` collections and lets the paired-object utilities find the HD twin.

> Implementation: `is_lod_name()` and `strip_lod_marker()` in [core/ipl.py](INU_tools/core/ipl.py).

### Model ID Manager

**Panel:** N-sidebar (`N`) → GTA Tools → **ID Manager** *(dedicated subpanel in DATA zone)*

- Shows free/used ID count
- **Next free ID** displayed
- **Auto Assign** — assigns next free ID to selected objects
- **Assign from ID...** — assign IDs starting from a specific number, skipping occupied
- **Release** — marks ID as free
- **Extend IDs (FLA)** — add IDs beyond 19999 for Fastman Limit Adjuster
- IDs stored in `model_ids.txt` in INU_Preset folder

> 💡 **Example — assign IDs to a batch of buildings:** imported 50 new buildings (no IDs). Select all → **Assign** → each object gets the next free ID starting from the first available (e.g. 3500, 3501, 3502 …). Now you can batch-export them into IDE.

> 💡 **Example — separate ID preset per map:** working on map `mycity`. Create preset with **+** → name `mycity`. All IDs you hand out in this scene now go into `INU_Preset/id_presets/mycity.txt` — no conflicts with your main project. Switch preset back to `default` — your previous ID database is back.

---

## Materials

### GTA SA Material Effects

**Panel:** Properties → Material → GTA SA Material Effects

| Property | Description |
|----------|-------------|
| Environment Map | Reflection texture with coefficient (0-1) |
| Bump Map | Normal map texture |
| Reflection | Mirror reflection with scale, offset, intensity |
| Specular | Specular highlight with level and texture |
| Dual Texture | Second texture with blend modes (11 options for Src/Dst) |
| UV Animation | Animated UV scrolling with animation name |

> 💡 **Example — building window with reflections:** create a material `building_window` → enable ☑ Environment Map → set texture `xenvmap`, coefficient `0.6` → in-game the window will reflect the sky/clouds moving over the city. For transparent glass, additionally enable FB Alpha.

### GTA Material Presets

**Panel:** Properties → Material → **GTA Material** → Preset

Quickly apply common material configurations with one click. Instead of hand-tuning 25+ `mat.inu.*` fields (env map, specular, reflection, dual texture, etc.) — pick from dropdown, click ✓ Apply.

#### Built-in presets (shipped with the addon)

| Preset | What it sets |
|---|---|
| **Generic** | Clears all effects — plain textured material |
| **Vehicle Body** | Car body: env map (`xvehicleenv128`, coef 0.2) + specular (`vehiclespecdot64`) + reflection 0.05 |
| **Vehicle Glass** | Car glass: env map with FB alpha, coef 0.4 |
| **Ped / Skinned** | Plain skinned material (for characters) |
| **Env Mapped** | Env map only (`xenvmap`, coef 0.5), no specular/reflection |
| **Dual Texture** | Enables second texture with alpha blend (src/dst = SRCALPHA / INVSRCALPHA) |
| **Specular** | Basic specular with level 1.0 |

These are always in the dropdown, cannot be deleted.

#### User presets

Stored **outside the addon** — in `<blender addons dir>/INU_Preset/material_presets/*.json`. They survive addon updates and reinstalls. Sits next to `INU_Preset/id_presets/` (same root folder as the ID Manager presets).

#### Example — modeling a car

Say you're building a car with 15 materials: body, glass, chrome, headlights, tires, interior. Hand-tuning each = 7 fields × 15 = 105 clicks.

**Step 1.** Select the car-body material in the object's material stack.

**Step 2.** Properties → Material → **GTA Material** → Preset → pick `Vehicle Body` → click ✓ (Apply). All fields get set: env map, specular, reflection.

**Step 3.** Switch to the glass material → `Vehicle Glass` → ✓. Done.

**Step 4.** Suppose you've dialed in your favorite "retro San Andreas body" mix — matter specular. Select that material → Preset → **Save as…** → name: `car_retro_matte`, description: `matte body for older cars`. Save.

Now `<addons>/INU_Preset/material_presets/car_retro_matte.json` appears:
```json
{
  "name": "car_retro_matte",
  "description": "matte body for older cars",
  "mat_inu": {
    "ambient": 1.0,
    "export_env_map": true,
    "env_map_tex": "xvehicleenv128",
    "env_map_coef": 0.15,
    "export_specular": true,
    "specular_level": 0.4,
    "specular_texture": "vehiclespecdot64",
    "export_reflection": true,
    "reflection_intensity": 0.02
  }
}
```

**Step 5.** No reload needed — the preset shows up in the dropdown immediately. Open another material → your `car_retro_matte` is there. Applies in one click.

**Step 6 (bonus).** Copy the JSON file to a teammate → they drop it into their `<addons>/INU_Preset/material_presets/` → same preset instantly available. Easy sharing across a modding team.

#### What a preset stores

25 fields from `INUMaterialProps`:
- **Ambient:** `ambient`
- **Env Map:** `export_env_map`, `env_map_tex`, `env_map_coef`, `env_map_fb_alpha`
- **Bump:** `export_bump_map`, `bump_map_tex`
- **Reflection:** `export_reflection` + 5 fields (scale X/Y, offset X/Y, intensity)
- **Specular:** `export_specular`, `specular_level`, `specular_texture`
- **Dual Texture:** `export_dual_tex`, `dual_tex_src_blend`, `dual_tex_dst_blend`, `dual_tex_texture`
- **UV Animation:** `export_animation`, `animation_name`

**Not stored** (per-instance data, not portable):
- `vehicle_color_slot` — per-instance carcols tag
- `col_*` — collision surface (separate COL Surface Type panel)
- `uv_anim_*` runtime params (speed_u/v, duration)

#### Deleting a preset

Select a user preset in the dropdown → the **Delete** button becomes active → Delete. File removed. Built-in presets (Generic/Vehicle/…) can't be deleted — button disables.

### COL Surface Types

**Panel:** Properties → Material → COL Surface Type

179 GTA SA surface materials organized in 13 categories. Searchable dropdown with category filtering. Each surface has:
- Surface ID (0-178)
- Flags, Brightness, Light
- Day Light (0-15), Night Light (0-15)

> 💡 **Example — wooden bar floor:** bar floor mesh → new material `bar_wood_floor` → COL Surface Type → search for `wood` → pick `WOOD_BENCH` (ID 9). Now character footsteps on this COL will play the wooden sound, and bullets will leave splinters.

### Textures

**Panel:** Properties → Scene → INU Tools → Textures

- **System textures** — path to a shared texture folder (e.g. `System_textures` from MTA/GTA)
- **.blend folder** — automatically points to the current .blend file's directory. Refresh button 🔄 updates the path
- **Load Textures** — searches for PNG/TGA/JPG files matching material names on the object. Searches both folders: system and .blend. If a material is named `brick_wall`, the addon finds `brick_wall.png` in the specified folders and assigns it as texture
- **Drag & Drop** — drag images from File Browser directly into the viewport to create a new material with the texture

> 💡 **Example — auto-assign textures by name:** unzipped 100 PNG textures into `F:/gta_textures/`. Scene has 100 materials named like `brick01`, `brick02`, `roof_tile` (no textures yet). Set `F:/gta_textures/` as System textures → select objects → **Load Textures** → the addon finds `brick01.png`, `brick02.png` etc. and attaches them to the matching materials automatically.

---

## Prelight (Vertex Colors)

> **Important in 1.6.3:** baking now respects **smooth/flat shading** (uses `loop.normal` instead of `poly.normal`). Also **hidden lights** (via 👁 viewport, 📷 render, or hidden collection) **are skipped** during baking — previously all point lights in the scene were used.


**Panel:** View3D → Sidebar (N) → GTA Tools → Prelight

### Baking

1. **Create Day/Night** — creates `Day` and `Night` color attributes
2. **Create 8 Lights** — places 8 point lights around the object
3. **Bake** (Fast) — CPU bake without shadows
4. **Bake with Shadows** — raycast shadow baking via depsgraph

**Settings:**
- Ambient (0-1) — base brightness
- Intensity (0-1) — light strength
- Gamma (0.5-3.0) — gamma correction
- Shadows toggle

> 💡 **Example — prelight a building for your map:** select the building mesh → Prelight → **Create Day/Night** → **Create 8 Lights** (8 point lights auto-placed around the object) → toggle ☑ Shadows → **Bake with Shadows**. The `Day` attribute gets filled with soft-shadowed lighting. Then same for Night (usually drop Intensity to 0.3 and switch light color to blueish) — switch to the Night attribute before Bake.

### Fill Colors

Paint selected faces with a chosen color. Supports levels (layers of fill) and undo/restore.

> 💡 **Example:** want to tint the roof of a building brighter than the walls. Enter Edit Mode → select the roof faces → Prelight → **Fill Color** → color = RGB(1,1,0.9) → Apply. The walls stay as they were, the roof gets a yellow tint. Not happy with it — **Undo fill** brings back the previous level.

### Scatter Light

Distribute light from selected faces outward. Parameters:
- Intensity, Falloff, Radius, Iterations

> 💡 **Example — glowing neon:** select the neon sign faces → Fill Color pink → **Scatter from selected** (Intensity 0.8, Radius 2m, Iterations 3) → neighboring faces around the sign pick up a pinkish hue, mimicking the neon glow spilling onto the building wall.

### Post-Processing

| Tool | Description |
|------|-------------|
| Smooth | Average colors between neighboring vertices |
| Smooth Between Objects | Smooth at seams between different meshes |
| Contrast | Adjust color contrast |
| Brightness | Adjust brightness offset |
| Gamma | Gamma correction |

> 💡 **Example — seam between two buildings:** two adjacent buildings stand flush. You baked prelight on each separately — a visible vertex-color seam at the border. Select both → **Smooth Between Objects** (passes 2, strength 0.5) → the gradient flows smoothly across the meshes, seam gone.

### COL Light

**Panel:** View3D → Sidebar (N) → GTA Tools → Prelight COL

Convert vertex colors to COL Day/Night Light values (0-15). Auto-splits materials by brightness ranges.

- **Preview** — visualize light values on mesh
- **Bake** — write values to COL material properties
- **Day/Night ranges** — adjustable thresholds

> 💡 **Example — tunnel COL lighting:** COL mesh of a tunnel has vertex colors with a dark center and lighter edges. Open Prelight COL → **👁 Preview** — mesh gets painted with numbers 0-15. Adjust Day range (min=0, max=6) so center is 0 (dark) and entrance is 6 (lighter) → **Bake COL Light** → materials get the corresponding Day/Night Light values. In-game, cars entering the tunnel will auto-darken.

### Presets

Save/load prelight settings (Ambient, Intensity, Gamma, Shadows) as named presets. Stored in `INU_Preset/` folder.

> 💡 **Example:** found your signature mix — Ambient 0.4, Intensity 0.7, Gamma 1.8, Shadows on. **Save preset** → name `my_night_scene`. On any future object: pick the preset → Load → all settings restored.

### Vertex Color Management

| Button | Description |
|--------|-------------|
| Create Day/Night | Creates both `Day` and `Night` color attributes |
| Day + / Night + | Create individual color attribute |
| Day - / Night - | Remove individual color attribute |
| Toggle Preview | Enable/disable Day/Night mix visualization in viewport |
| Add LightMap | Load lightmap texture and connect to UV2 (Multiply blend) |
| 👁 LightMap | Toggle lightmap visibility (mute/unmute) |
| ➖ LightMap | Remove lightmap nodes from materials |
| Analyze | Show vertex color histogram (min/max/avg) |
| Reset | Reset bake settings to defaults |

**Edit/Paint modes:** buttons to switch between Object, Edit, and Vertex Paint modes for quick workflow.

> 💡 **Example — quick-start Night from the Day bake:** you've only baked the `Day` attribute → **Day → Night** → `Night` gets created as a copy of `Day`. Now open Post-Processing → **Brightness** = −0.3 → apply to Night → you've got a darkened version of the daytime bake. Then tweak manually (add yellow fill around lamp posts, etc.).

---

## 2DFX Effects

**Panel:** View3D → Sidebar (N) → GTA Tools → 2DFX Effects

Create and configure 2DFX effects that export into DFF files.

**Effect types:**
- **Light** — street lights, neons, coronas
- **Particle** — smoke, fire
- **Ped Attractor** — ATM, bench, bus stop
- **Sun Glare** — sun reflection on surfaces

### Light Properties

| Property | Options |
|----------|---------|
| Presets | Default, OnAllDay, Lamp Post, Lamp Post Coast, BB Pickup, Flashing (3 types), Train Crossing, Traffic |
| Corona Texture | 34 textures (coronastar, coronamoon, headlight, etc.) |
| Shadow Texture | 13 textures (shad_exp, shad_car, lamp_shad_64, etc.) |
| Show Mode | Default, Random Flashing, Flash Rain, Only Rain, No Rain |
| Flare Type | None, Type 1-3 |
| Color | RGBA color picker |
| Corona Size | Float |
| Draw Distance | Float |
| Light Range | Float |
| Shadow Size | Float |
| Flags 1/2 | Integer |

**Attach to Model:** parent 2DFX Empty to mesh object. Coordinates auto-recalculate on export.

**Detach All from Mesh** *(new in 1.6.3):* batch detach all 2DFX from selected mesh. The mesh's UI shows a list of all attached 2DFX with individual detach buttons.

**Preview:** real-time corona/shadow visualization in viewport. Billboard tracking implemented via **draw handler** *(1.6.3)* — works reliably across scene switches.

> 💡 **Example — street lamp:** select the lamp post mesh → 2DFX → **Create Light** → an Empty with default lamp appears. Move the Empty to the top of the post → pick preset **Lamp Post** → ✓ Apply (sets yellow color, coronastar texture, 200m draw distance). Parenting to the mesh is automatic → Empty.parent = post. On DFF export, 2DFX coordinates are written relative to the mesh.

> 💡 **Example — flashing red emergency:** Create Light → preset **Flashing (Maverick1)** → ✓ Apply → Show Mode `1 RANDOM_FLASHING` is set automatically. In-game this corona will flash red randomly — perfect for emergency lights or police beacons.

---

## Particle Effects (effects.fxp) *(new in 1.6.3)*

Full GTA SA `effects.fxp` editor — text file with 82 particle systems (fire, smoke, blood, sparks, water, etc.).

**File location:** `GTA SA/models/effects.fxp` (auto-detected from game root)

### Basic workflow

1. Create a 2DFX Particle via 2DFX panel → **Particle**
2. In particle properties, pick an effect from dropdown (`prt_blood`, `prt_fire`, `prt_water_splash`, ...)
3. Enable **Simulation** — particles start flying in viewport
4. Edit parameters — changes are visible instantly
5. **Save to effects.fxp** — auto-backup `.fxp.bak` is created on first write

### Emitter parameters

**Sprite & blending:**
| Parameter | Description |
|-----------|-------------|
| Texture | Sprite name from `particle.txd` (sphere, smoke, fire, etc.) |
| SrcBlend / DstBlend | D3D9 blend factors (4=SrcAlpha, 5=InvSrcAlpha, 2=One for additive) |

**Color (start → end):**
- Start, middle, end RGBA colors interpolated over particle lifetime
- Middle color toggle for three-point interpolation

**Size:**
- Start and end size with smooth transition

**Emission:**
| Parameter | Description |
|-----------|-------------|
| Life | Particle lifetime in seconds |
| Speed | Initial speed |
| Direction | Emission direction vector |
| Rate | Particles per second |
| Angle | Cone spread angle |
| Volume box | Spawn volume |

**Physics:**
| Parameter | Description |
|-----------|-------------|
| Force | Gravity force (XYZ vector) |
| Friction | Air resistance |
| Wind | Wind influence |
| Noise | Perlin noise turbulence |
| Jitter | Random jitter |
| Ground bounce | Ground collision response |

**System:**
| Parameter | Description |
|-----------|-------------|
| LENGTH | Total system duration (seconds) |
| PLAYMODE | Playback mode (0-3) |
| CULLDIST | Culling distance for LOD |
| Bounding sphere | Radius for culling |

### Curves (keyframes)

Any parameter can be **animated over particle lifetime** via keyframe curves:

1. In "Curves" section, pick a parameter (e.g. `SIZE.SIZEX` or `COLOUR.RED`)
2. A list of keys appears with **+** and **-** buttons
3. Each key is a `(TIME, VAL)` pair where TIME = 0..1 (normalized lifetime)
4. After editing click **"Write curve to effects.fxp"**

Example: for fire — size grows from 0.5 to 2.0, color transitions from yellow to red to black, alpha from 1.0 to 0.0.

### Operators

| Operator | Description |
|----------|-------------|
| New Effect | Create new effect (cloned from current template) |
| Delete Effect | Remove effect from effects.fxp |
| Switch Emitter | Browse emitters within multi-emitter system (e.g. `prt_cardebris` has 4 emitters) |
| Reload effects.fxp | Re-read file from disk (clear cache) |
| Save to effects.fxp | Write edits back to file with auto-backup |

### Simulation

- **30 FPS** particle position updates via frame_change handler
- Up to **64 particles per emitter** (shared mesh pool, memory efficient)
- **Camera-facing billboards** via draw handler — particles always face viewport
- **Vertex color emission** shader — real color/alpha by particle age
- Simulation is **non-destructive** — DFF model is unchanged

### Important notes

> **When switching effects** all unsaved edits are reset — save first via **"Save to effects.fxp"**

> **Backup:** on first write `effects.fxp.bak` is created next to the original — you can revert if something goes wrong

> **Particle textures** are stored in `particle.txd` (next to effects.fxp). Import the TXD into Blender to see sprites in materials browser

---

## UV Tools

**Panel:** UV Editor → Sidebar (N) → GTA Tools

| Tool | Description |
|------|-------------|
| UV Grid Randomizer | Randomize UV positions within grid cells |
| Snap to Grid | Snap UV islands to nearest cell |
| 9 Alignment Points | Choose position within cell (top-left, center, etc.) |
| Link Polygons | Move polygons with overlapping UVs together |
| Show UV Grid | Visualize GTA texture atlas grid |

**Grid settings:** columns × rows (default 4×4).

> 💡 **Example — UV grid for a 4×4 atlas:** ground mesh with 16 grass variants in a 4×4 atlas. In Edit Mode select faces → UV Editor → **UV Grid Randomizer** → each face's UV coords land in a random cell of the 16. In the viewport the ground shows natural variety without manual texture assignment.

---

## Check

**Panel:** View3D → Sidebar (N) → GTA Tools → Check

| Button | Description |
|--------|-------------|
| Check Vertex | Find loose vertex and edges |
| Check N-gon | Find polygons with 5+ vertex |
| Check Materials | Check 50 material limit per object |
| Cleanup Materials | Merge duplicate materials and textures (.001, .002) |
| Sort Materials | Sort materials by name (natural sorting) |
| Reset Transform | Zero out Location and Rotation for selected meshes (Scale untouched) |
| LOD/COL → DFF | Snap LOD and COL to their corresponding DFF position |
| DFF / LOD / COL | Hide/show objects by type |
| Type: OBJ/COL/SHA/NON | Batch assign type to selected objects with auto-rename |

> 💡 **Example — preflight a building before export:** ready to export a house. In the Check panel, in sequence: **Check Vertex** (no loose ones) → **Check N-gon** (all faces 3–4 verts) → **Check Materials** (≤50) → **Cleanup Materials** (merge .001 duplicates) → **LOD/COL → DFF** (snap pair to HD position). Now you can safely export — no known issues.

> **Duplicate cleanup:** on IDE and IPL export, Blender duplicate suffixes (.001, .002, etc.) are automatically stripped from model names.

### Cleanup Materials — details

The button finds datablocks with `.001`, `.002`, etc. suffix and merges them with the original in a single pass — materials and textures (images) are processed separately.

**Materials:**
- All `material_slots` on meshes that reference a duplicate are switched to the original.
- If no original with the base name exists — the first duplicate is renamed to the base name and becomes the original.
- Unused duplicates (`users == 0`) are removed from `bpy.data.materials`.

**Textures (safe mode):**
- The image reference is replaced inside `Image Texture` nodes in all materials **and** node groups (shader/geometry/compositor).
- A duplicate is merged with the original **only if the absolute file path matches** (`bpy.path.abspath` with library awareness). This prevents false merges in GTA SA, where identically-named textures often come from different TXDs.
- For packed/generated images (no filepath), a weak `source + size` key is used.
- Textures with different paths are **not merged** and counted in the "Skipped" stat.

**Status bar report:**
```
Materials: 12/3 | Textures: 8/2 | Skipped (different paths): 1
```
Format — `merged_slots/removed_duplicates`.

---

## Characters (Skinned DFF)

Import/export GTA SA character models with skeleton and animations.

**Import:**
- Armature with bone hierarchy
- Vertex weights (skin data)
- Bone matrices (Skin PLG)
- Compatible with Kams Script and original game models

**Export:**
- Round-trip with byte-level accuracy
- Correct material indices in BinMesh PLG

**Export settings for characters:** in object properties (`obj.inu`) it's recommended to enable **Normals** and disable **Vertex Colors** — GTA SA characters use normals for dynamic engine lighting instead of baked vertex colors like buildings

> 💡 **Example — import CJ and customize:** File → Import → GTA SA DFF → `cj.dff`. Imports armature + skinned mesh. Edit the mesh (add a hat, tweak proportions) → check weights → **Export DFF** → you get `cj_custom.dff` with the same armature skeleton but modified geometry. Animations from `ped.ifp` apply without any reworking — same skeleton.

### IFP Animations

| Button | Operator | Description |
|--------|----------|-------------|
| Import IFP | `gtatools.import_ifp` | Load animation file (294+ animations in ped.ifp) |
| Export IFP | `gtatools.export_ifp` | Save Blender Actions as IFP |
| Apply | `gtatools.apply_ifp` | Assign animation to armature |

Searchable animation list in the panel.

> 💡 **Example — preview a walk cycle:** imported `cj.dff` with armature → **Import IFP** → pick `ped.ifp` → the list loads 294 animations (WALK_civi, RUN_civi, IDLE_stance, etc.). Type `walk` in the search → pick `WALK_civi` → **Apply Animation** → the walk cycle is applied to CJ's armature, hit Play in Timeline — character walks.

> 💡 **Example — batch import an animation folder:** 50 .ifp files in a folder → Animations panel → **Batch folder…** → pick the folder → all IFPs loaded as separate Actions. Each animation accessible via regular Action Editor.

---

## Water IO

**Panel:** View3D → Sidebar (N) → GTA Tools → Water

| Button | Description |
|--------|-------------|
| Import Water | Load water.dat |
| Export Water | Save water.dat (from Water collection) |
| Add Water | Create water quad with current settings |
| Snap to Grid | Align vertices to 4-unit grid |
| Stitch Edges | Merge overlapping water quads |

**Water properties:**
- Flag: 0=Default visible, 1=Invisible, 2=Shallow visible, 3=Shallow invisible
- Speed X/Y/Z — flow velocity
- Wave Height — wave intensity
- Texture: waterclear256 with flow animation

> 💡 **Example — lake for a custom map:** View3D → Water → **Add Water** → params: Flag `0` (default visible), Wave Height 0.3m, Speed 0.02 — a 100×100m quad appears with water properties. Scale it to match the lake size → **Snap to Grid** so vertices align with GTA's regular grid → **Export Water** → you get `water.dat` ready for in-game use.

---

## Path IO

**Panel:** View3D → Sidebar (N) → GTA Tools → Paths

### Paths IPL (Vehicle/Pedestrian)

| Button | Description |
|--------|-------------|
| Import paths.ipl | Load path definitions |
| Export paths.ipl | Save path data for gta.dat |
| Create Path | New path curve |
| Convert to Path | Convert edges/curve to path data |

Auto-splits into groups of 12 nodes (GTA SA limit).

> 💡 **Example — create a vehicle path with a roadblock:** Paths → **Create Path** → a curve appears → Edit Mode → add points along the road. In Edit Curve mode the panel reveals flag buttons: select one point in the middle of the road → **Toggle Roadblock** → that point becomes a roadblock stop. At an intersection select a point → **Traffic → Normal** → cars will wait at the traffic light there. **Export paths.ipl** → the encoded flags are written to the file.

### Train Tracks

| Button | Description |
|--------|-------------|
| Import tracks.dat | Load train track data |
| Export tracks.dat | Save track definitions |
| Create Track | New track curve |
| Mark Station | Toggle station point (edit mode) |

> 💡 **Example — add a new station on an existing track:** imported tracks.dat (curve loaded from points), Edit Mode → select a point at the desired spot → **Mark Station** → the point is flagged as a stop (marker becomes visible via **Refresh Station Markers** — a visible Empty sphere). Export → station flag is written for that point in tracks.dat.

### Compiled Nodes

| Button | Description |
|--------|-------------|
| Import NODES.dat | Load compiled binary path nodes (multi-file selection) |
| Export NODES.dat | Save compiled nodes to selected folder |

**Import:** select multiple files (nodes0.dat, nodes1.dat, ...) at once. Each imported object gets a `nodes_filename` property with the source file name.

**Export** works in two modes:
1. **By filename** — if objects have `nodes_filename` property (set on import), nodes are grouped by source files and saved with the same names
2. **Auto-split by zones** — objects without `nodes_filename` are automatically distributed across the GTA SA map zone grid (8x8, 64 zones, 750 units per zone). Each vertex is assigned to a zone by coordinates: `gx = (X + 3000) / 750`, `gy = (3000 - Y) / 750`. Files are saved as `nodes0.dat` ... `nodes63.dat`

> **Zone grid:** GTA SA map ranges from -3000 to +3000 on X and Y. Zones are numbered left-to-right, top-to-bottom (zone = gy × 8 + gx).

---

## Integrations

### Itera Tools 3

**Panel:** View3D → Sidebar (N) → GTA Tools → Itera Tools 3

| Button | Description |
|--------|-------------|
| Vertex Lit Linear | Applies a special material for previewing Itera lighting on the model |
| Quickstart | Creates a modifier on the model and a collection with light sources |
| Remove Itera | Removes the lighting material and restores the original materials |

**Workflow:**
1. Click **Vertex Lit Linear** — a lighting preview material is applied to the model
2. Click **Quickstart** — a modifier and light collection appear
3. Position and configure the lights as needed
4. In the model's modifier, set **Output Type / Bake → Vertex Colors**
5. In the **Export Vertex Color** field, type your color attribute name — `Day` or `Night`
6. When lighting is finalized — **apply the modifier**
7. A third extra color attribute will appear — you can delete it
8. Click **Remove Itera** — original materials are restored on the model

> **IMPORTANT:** Do not edit the model's geometry or materials while Itera material is active. Modifying the model in this state can corrupt UV coordinates and break texture assignments.

Panel is only visible when Itera Tools 3 is installed in Asset Libraries.

### LightMap (beta_MTA)

**Panel:** View3D → Sidebar (N) → GTA Tools → Lightmap Generator (beta)

Generate Lua code for MTA SA lightmap scripts. The MTA script replaces shaders at runtime, adding a second UV layer with the lightmap over the base textures.

**Full workflow:**

1. **Create UV1** — main UV layout for model textures (bricks, roof, etc.)
2. **Create UV2** — second UV layout specifically for the lightmap. Each polygon must occupy a unique space with no overlaps. In Blender: UV Editor → UV → Smart UV Project or manually
3. **Bake lighting to a texture using UV2** — use any baking method you prefer (Blender Bake, Cycles, third-party addons). The result must be baked to a texture using the UV2 layout
4. **Save lightmap** as a PNG file (e.g. `lightmaps/building01.png`)
5. **Export DFF** — make sure both UV layers are enabled in object properties (`uv_map1` and `uv_map2`). The addon writes both UVs to the DFF file
6. **Generate code:**
   - Select the object
   - Set the **lightmap path** (relative, as in MTA resources)
   - Set the **Model ID**
   - Click **Generate**
7. **Copy** the result into your MTA Lua script

| Button | Operator | Description |
|--------|----------|-------------|
| Load Lightmap | `gtatools.load_lightmap` | Load lightmap image for preview |
| Remove Lightmap | `gtatools.remove_lightmap` | Remove loaded lightmap |
| Generate | `gtatools.lightmap_generate` | Generate Lua code from object textures |
| Copy | `gtatools.lightmap_copy` | Copy result to clipboard |
| Clear | `gtatools.lightmap_clear` | Clear generated code |

**Output:** Lua table with texture names and lightmap references:
```lua
{
    textures = {
        "brick_wall",
        "roof_tile",
    },
    lightmap = "lightmaps/building01.png",
    models = {3500}
},
```

> **IMPORTANT:** UV2 is required — without a second UV layer, the lightmap will use UV1 coordinates and look incorrect.

The MTA lightmap script itself is available in the [Issues](../../issues) section of the repository.

### Pipeline

Render pipeline determines how the GTA SA engine processes the model:
- **None** — no pipeline. Suitable for most objects: furniture, fences, vegetation, characters
- **Building** (0x53F2009A) — Day/Night vertex colors. Required for buildings and map objects that have vertex colors — without this pipeline, day/night color transitions won't work in-game
- **Reflections** (0x53F20098) — window reflections. Only for window models that should reflect the environment. Windows must be a separate model from the building

> 💡 **Example:** a house `house01` needs day/night lighting → Object Properties → INU Tools: Model → Pipeline = **Day/Night**. Split the windows of this house into a separate mesh `house01_windows` → its Pipeline = **Reflections** so they reflect the street. The fence in front of the house `house01_fence` → Pipeline = **None**.

### Normals

The **Normals** toggle controls vertex normal export in DFF:
- **Enabled** — the model receives dynamic lighting from the GTA SA engine. Required for: characters, vehicles, weapons, interactive objects
- **Disabled** — the model is lit only by baked vertex colors. Used for: buildings, roads, map objects

> 💡 **Example:** CJ (character) — ☑ Normals (engine lights him based on sun and lamps). Map building with baked vertex colors — ☐ Normals (otherwise the engine overlays its own lighting and the visual breaks).

---

## Experimental (v1.6.4)

> ⚠️ **Note:** The features in this section were freshly implemented and have not been extensively tested in-game. Expect rough edges, partial behaviour, or the occasional crash. Report issues in [Issues](../../issues).

### Map Export

Unified one-click export of a scene district: DFF + COL + TXD + IDE + IPL into a single folder.

**Location:** View3D → Sidebar (N) → GTA Tools → *Map Export* panel → button **Export Map…**

**Workflow:**
1. Select the objects that form a district (DFF meshes, their LOD and COL siblings — detection by suffix/prefix).
2. Click *Export Map…*, pick a target folder.
3. Toggle what to emit (DFF / COL / TXD / IDE / IPL) and optionally *Binary IPL*.
4. Set *Base Name* (used for the shared TXD/IDE/IPL filenames) and *ID Pool Start* (first auto-assigned Model ID for DFFs with `model_id == 0`).

**What it does:**
- Groups objects by base name via `get_model_type()` — one DFF + optional LOD + zero-or-more COL meshes per group
- Auto-assigns Model IDs from `[id_pool_start, 19999]` to any DFF with `inu.model_id == 0`, writing them back into the object
- Exports per-group `*.dff` and `*.col` with existing exporters
- Builds one shared `{base_name}.txd` from all DFF textures
- Writes one `{base_name}.ide` (objs section) and one `{base_name}.ipl` (inst section) covering the entire selection

Source: [`tools/map_export.py`](INU_tools/tools/map_export.py).

### Binary IPL Write

Adds `bnry`-format output to the IPL exporter (read was already supported).

**Location:** File → Export → *Export IPL* (or the per-object IPL export operator) → checkbox **Binary (bnry)**.

**Format:** 76-byte header (`bnry` magic + 6 uint32 counts + 12 uint32 offsets), then packed `inst` entries (40 bytes each: 7 floats + 3 ints) and `cars` entries (48 bytes: 4 floats + 8 ints). Other sections (`cull`, `grge`, `zone`, …) are **not** written — Rockstar's binary IPLs only contain `inst` and `cars`, matching vanilla SA behaviour.

Source: [`core/ipl.py`](INU_tools/core/ipl.py) → `_write_binary_ipl`, `write_binary_ipl`, `write_ipl(..., binary=True)`.

### UV Animation in DFF

Write a simple linear U/V scroll animation directly into the DFF binary as chunks `0x2B` (UV anim dict) + `0x135` (UV anim PLG on the material).

**Location:** Properties → Material → *GTA SA Material Effects* → block **Write UV Anim to DFF**.

**Fields:**
- **Write UV Anim to DFF** — toggle that enables the chunks on export
- **Scroll U / Scroll V** — per-second translation along each axis
- **Duration** — animation cycle length in seconds

**How it's encoded:** two keyframes (t=0 with identity transform, t=duration with translation = speed × duration), `node_to_uv[0] = 1` to target the material's first texture slot. For cyclic scrolls (conveyors, water) pick a duration so `speed × duration` lands on a whole UV unit.

**Limitation:** read-back is not implemented yet. Importing an existing UV-animated DFF loses the animation and re-exporting drops it. Write-only.

Source: [`core/dff.py`](INU_tools/core/dff.py) → `UVAnim`, `UVAnimDict`, `_uv_anim_plg_bytes`; [`ops/dff_export.py`](INU_tools/ops/dff_export.py) → `_collect_uv_anim_dict`.

### Breakable Objects

Marks a mesh as destructible by the GTA SA physics engine via chunk `0x253F2FD`.

**Location:** Properties → Object → *GTA SA: IDE / IPL* panel → block **Разрушаемый (Breakable)** (checkbox) + **Break Force**.

**What is written:** a 32-byte breakable chunk on the geometry extension with vertex/face/material/UV buffer counts derived from the exported mesh, plus the break force. Defaults mirror what Kams's `brakableobjects.ms` writes.

Source: [`core/dff.py`](INU_tools/core/dff.py) → `BreakableData`, `CHUNK_BREAKABLE`; [`ops/dff_export.py`](INU_tools/ops/dff_export.py) → breakable block inside `_process_mesh`.

### IFP Batch Import

Import a folder of `.ifp` files and stack every animation onto one NLA track of the active armature.

**Location:** View3D → Sidebar (N) → GTA Tools → *Anim* panel → button **Batch папка…**.

**Options:**
- **Name Prefix** — only apply animations whose name starts with this prefix (case-insensitive). Empty = all.
- **Mode: NLA Sequential** — stack clips on one NLA track with a gap between them
- **Mode: Actions Only** — just create the Actions, no NLA arrangement
- **Gap Between Clips** — frames between consecutive strips (NLA mode only)

**Use case:** scrub through 294 animations from `ped.ifp` consecutively without manually importing each one.

Source: [`ops/ifp_import.py`](INU_tools/ops/ifp_import.py) → `enumerate_animations`, `batch_apply_sequential`, `GTATOOLS_OT_ifp_batch_import`.

### GTA Material Panel

A condensed material UI with a preset dropdown that writes GTA-specific properties in one click.

**Location:** Properties → Material → *GTA Material* panel.

**Presets:**
- **Generic** — clears all effect flags (plain textured material)
- **Vehicle Body** — `xvehicleenv128` env map + `vehiclespecdot64` specular + reflection blend 0.05
- **Vehicle Glass** — `xvehicleenv128` env map with framebuffer alpha
- **Ped / Skinned** — plain skinned material
- **Env Mapped** — plain env map only
- **Dual Texture** — src=SRCALPHA, dst=INVSRCALPHA
- **Specular** — plain specular level 1.0

Plus the **Vehicle Color Slot** dropdown (Primary / Secondary / Third / Fourth / Headlights / Taillights) — writes the carcols magic tag into the material's base RGB.

Source: [`tools/gta_material_panel.py`](INU_tools/tools/gta_material_panel.py).

### Bitmaps Manager

Texture-management utilities: scan for missing files, resolve paths from a search folder, batch-copy used textures, find duplicates.

**Location:** View3D → Sidebar (N) → GTA Tools → *Bitmaps Manager* panel.

**Operators:**
- **Scan Missing Textures** — walks every material, lists images whose `filepath` can't be found. Count is stored on the scene and shown in the panel.
- **Resolve From Folder…** — walks the chosen folder recursively, matches by basename (with or without extension), patches `image.filepath` and reloads.
- **Copy Used To Folder…** — copies every texture used by at least one material into the target folder. Optional **Subfolder per TXD** creates `target/{txd_name}/texture.png` by walking mesh objects and reading `obj.inu.txd_name`. If a material is used across multiple TXDs, the texture lands in each one.
- **Find Duplicates** — MD5-hashes every reachable texture file and reports groups of identical files to the System Console.

Source: [`tools/bitmaps_manager.py`](INU_tools/tools/bitmaps_manager.py).

### CST IO

Text serialisation of COL collision data, compatible in spirit with Steve's COL Editor. Alternative to the binary `.col` format for hand-editing or diffing.

**Location:** Operators `gtatools.import_cst` / `gtatools.export_cst`.

**Format:** line-based, one directive per structure. Multiple MODEL blocks per file supported.
```
MODEL my_col
ID 1234
VERSION 3
BOUNDS 0 0 0 5.0 -2 -2 -2 2 2 2
SPHERE 0 0 1 0.5  0 0 0 0
BOX -1 -1 0 1 1 2  0 0 0 0
VERTEX 1.0 2.0 0.0
FACE 0 1 2  0 0 0 0
SHADOW_VERTEX 0 0 0
SHADOW_FACE 0 1 2  0 0 0 0
END
```

Each `SPHERE` / `BOX` / `FACE` ends with 4 surface tokens: `material flags brightness light`. Anything after `#` is a comment.

Source: [`core/cst.py`](INU_tools/core/cst.py), [`ops/cst_import.py`](INU_tools/ops/cst_import.py), [`ops/cst_export.py`](INU_tools/ops/cst_export.py).

### Vehicle Scale Helper

Uniformly rescale a whole vehicle hierarchy (Empty root + mesh + dummy children) preserving the structure for DFF export.

**Location:** Operator `gtatools.vehicle_scale` (dialog).

**Options:**
- **Factor** — uniform scale multiplier
- **Dummies Only** — if enabled, only move the dummy empties; mesh vertices stay the size they were

**What it does:** walks the hierarchy DFS, multiplies every `obj.location` by the factor, clears `matrix_parent_inverse` to identity, applies `Matrix.Scale(factor)` to mesh data (copies shared meshes first) and Armature data, resets `scale` to `(1,1,1)` on every object. Empty display sizes scale too.

Source: [`tools/vehicle_scale.py`](INU_tools/tools/vehicle_scale.py).

### Train Station Markers

Visible Empty spheres on train-track curves at every station point, so stations are readable in Object mode without entering Edit mode.

**Location:** Operator `gtatools.refresh_station_markers` (active track curve with `path_type == 'track'`).

**What it does:** wipes old markers parented to the track, reads `station_indices` (set by the existing `gtatools.mark_station`), places a sphere Empty at every station point with `empty_display_size = 3.0`, parents it to the track with identity parent-inverse so the local position maps 1:1 to the curve point.

Source: [`ops/ifp_import.py`](INU_tools/ops/ifp_import.py) → `_refresh_station_markers`, `GTATOOLS_OT_refresh_station_markers`.

### Roadblocks & Traffic Lights

Per-node flag editor for paths.ipl curves: roadblock bit + traffic-light kind.

**Location:** Edit Curve mode on a `path_type == 'path_ipl'` curve → operator `gtatools.path_node_flag` with these actions:
- **Toggle Roadblock** — flip bit 12 (cops barrier) on every selected point
- **Clear / Normal / Rail / Bus Traffic Light** — set bits 8–11 to 0 / 1 / 2 / 3

Works on filtered spline points, but writes into the original IDProp slots (which include empty-padding nodes from the 12-per-group IPL format).

Source: [`core/paths.py`](INU_tools/core/paths.py) → flag constants + `decode_node_flags` / `encode_node_flags`; [`ops/ifp_import.py`](INU_tools/ops/ifp_import.py) → `GTATOOLS_OT_path_node_flag`.

### FLA4 Path Format

Extended `nodes*.dat` format used by Fastman Limit Adjuster 4. Adds 12 bytes per path node (spawn probability, speed limit in km/h, lane count override) on top of the vanilla 28-byte structure, for a total of 40 bytes per node.

**Detection:** a file is treated as FLA4 when it starts with the ASCII magic `FLA4`. Counts + offsets layout is otherwise identical to vanilla.

**Location:** File → Export → *Export Path Nodes* → checkbox **FLA4 Format**. Import auto-detects.

Source: [`core/paths.py`](INU_tools/core/paths.py) → `FLA4_MAGIC`, `FLA4_PATH_NODE_SIZE`, FLA4 branches in `read_nodes` / `write_nodes`; [`ops/path_export.py`](INU_tools/ops/path_export.py) → `export_nodes(..., fla4=True)`.

---

## Technical Reference

### Project Structure

```
INU_tools/
├── __init__.py          # Main addon: operators, panels, registration (~9700 lines)
├── core/                # Pure Python parsers (no Blender dependency)
│   ├── dff.py           # RenderWare DFF reader/writer
│   ├── col.py           # COL1/2/3/4 collision format
│   ├── txd.py           # TXD texture dictionary (numpy DXT decompression)
│   ├── ide.py           # IDE definition file I/O
│   ├── ipl.py           # IPL instance file I/O (text + binary)
│   ├── ifp.py           # IFP animation format
│   ├── img.py           # IMG v2 archive (read/write/extract/replace)
│   ├── paths.py         # Path data (flight, track, nodes)
│   ├── water.py         # water.dat format
│   ├── gta_dat.py       # gta.dat/gta_int.dat parser
│   └── rwbinary.py      # Low-level RenderWare binary helpers
├── ops/                 # Blender operators (import/export logic)
│   ├── dff_import.py    # DFF → Blender mesh
│   ├── dff_export.py    # Blender mesh → DFF
│   ├── col_import.py    # COL → Blender mesh
│   ├── col_export.py    # Blender mesh → COL
│   ├── txd_import.py    # TXD → Blender images
│   ├── ide_import.py    # IDE → object properties
│   ├── ide_export.py    # Object properties → IDE
│   ├── ipl_import.py    # IPL → object placement
│   ├── ipl_export.py    # Object transforms → IPL
│   ├── ipl_sections.py  # IPL sections ↔ Blender collections
│   ├── ifp_import.py    # IFP → Blender Actions
│   ├── ifp_export.py    # Blender Actions → IFP
│   ├── path_import.py   # Paths → Blender curves
│   ├── path_export.py   # Blender curves → paths
│   ├── water_import.py  # water.dat → mesh
│   ├── water_export.py  # Mesh → water.dat
│   └── fx_preview.py    # 2DFX light preview visualization
├── tools/               # Utility modules
│   ├── txd_export.py    # TXD compilation (CPU/GPU)
│   ├── prelight.py      # Vertex color baking & post-processing
│   ├── col_light.py     # COL lighting preview & bake
│   ├── uv_tools.py      # UV grid tools & panel
│   ├── model_utils.py   # Model detection by suffixes
│   └── dff2gltf.py      # DFF → glTF conversion for map import
├── data/
│   ├── surface_materials.py  # 179 GTA SA surface types
│   └── id_manager.py         # Model ID allocation
└── locale/
    ├── __init__.py       # Translation loader
    └── eng.py            # English translations
```

### Core Modules

#### dff.py — RenderWare DFF Format
Reads/writes RenderWare binary streams. Handles: Clump, Frame List, Geometry List, Geometry (vertices, normals, UV, vertex colors), Material List, Material, Texture, Atomic, Skin PLG, 2DFX PLG, BinMesh PLG.

#### col.py — Collision Format
Supports COL1, COL2, COL3 (GTA SA default), COL4. Reads/writes: mesh faces, vertices, face groups, spheres, boxes, surface properties (material, flags, brightness, light).

#### txd.py — Texture Dictionary
Numpy-accelerated DXT decompression. Handles: DXT1, DXT3, DXT5, RASTER_8888, RASTER_888 (32-bit BGRX), RASTER_565, RASTER_1555, RASTER_4444, PAL8 (paletted). Platform: D3D8/D3D9.

#### ide.py — Item Definition
All sections: objs (static), tobj (timed), anim (animated), cars (vehicles), peds (pedestrians), weap (weapons), hier (hierarchy), txdp (TXD parents).

#### ipl.py — Item Placement
All sections: inst (instances), cull (cull zones), grge (garages), enex (entry/exit), pick (pickups), cars (parked vehicles), auzo (audio zones), jump (stunt jumps), occl (occlusion), tcyc (time cycle), zone (map zones). Supports binary IPL (`bnry` header).

#### img.py — IMG v2 Archive
`ImgReader` context manager for fast sequential reads. Functions: `read_directory`, `extract_file`, `replace_or_add`, `remove_file`, `create_img`. Sector-aligned (2048 bytes).

#### gta_dat.py — Game Data
Parses `gta.dat` and `gta_int.dat`. Extracts IDE/IPL/IMG paths. `extract_regions()` returns folder names from MAPS directory for dynamic region filtering.

### File Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| DFF | .dff | RenderWare model (geometry, materials, UV, vertex colors, 2DFX) |
| COL | .col | Collision mesh with surface properties |
| TXD | .txd | Texture archive (DXT compressed) |
| IDE | .ide | Object definitions (text, comma-separated) |
| IPL | .ipl | Object placement (text or binary with `bnry` header) |
| IFP | .ifp | Skeletal animations |
| IMG | .img | VER2 archive containing DFF/COL/TXD/IPL files |
| water.dat | .dat | Water quad definitions |
| paths.ipl | .ipl | Vehicle/pedestrian path definitions |
| tracks.dat | .dat | Train track definitions |
| NODES*.dat | .dat | Compiled binary path nodes |

### Object Properties (INUObjectProps)

Accessed via `obj.inu` on any Blender object.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| type | Enum | OBJ | OBJ / COL / SHA / 2DFX / NON |
| model_id | Int | 0 | GTA SA model ID |
| txd_name | String | "" | Texture dictionary name |
| draw_distance | Float | 300.0 | Render distance |
| ide_flags | Int | 0 | IDE flags (bitfield) |
| interior_id | Int | 0 | Interior ID (0=exterior) |
| lod_index | Int | -1 | LOD model index (-1=none) |
| pipeline | Enum | NONE | NONE / Building / Reflections / Custom |
| light | Bool | True | rpGEOMETRYLIGHT flag |
| modulate_color | Bool | True | rpGEOMETRYMODULATEMATERIALCOLOR flag |
| export_normals | Bool | True | Export vertex normals |
| export_binsplit | Bool | True | Export BinMesh PLG |
| uv_map1/2 | Bool | True | Export UV maps |
| day_cols / night_cols | Bool | True | Export vertex colors |
| effect_2dfx | Enum | LIGHT | 2DFX effect type |
| color_2dfx | RGBA | (1,1,0.78,1) | 2DFX color |
| preset_2dfx | Enum | DEFAULT | Light preset |
| corona_tex_2dfx | Enum | coronastar | Corona texture (34 options) |
| shadow_tex_2dfx | Enum | shad_exp | Shadow texture |
| show_mode_2dfx | Enum | 0 | Display mode (6 options) |
| flare_type_2dfx | Enum | 0 | Lens flare type (4 options) |

### Material Properties (INUMaterialProps)

Accessed via `mat.inu` on any Blender material.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| ambient | Float | 1.0 | Ambient shading |
| col_mat_index | Int | 0 | COL surface ID (0-178) |
| col_flags | Int | 0 | Collision flags |
| col_brightness | Int | 0 | Surface brightness |
| col_light | Int | 0 | Surface light |
| col_day_light | Int | 0 | Day light (0-15) |
| col_night_light | Int | 0 | Night light (0-15) |
| export_env_map | Bool | False | Enable environment map |
| env_map_tex | String | "" | Env map texture name |
| env_map_coef | Float | 0.5 | Env map coefficient |
| export_bump_map | Bool | False | Enable bump map |
| bump_map_tex | String | "" | Bump map texture name |
| export_reflection | Bool | False | Enable reflection |
| reflection_scale_x/y | Float | 0 | Reflection scale |
| reflection_offset_x/y | Float | 0 | Reflection offset |
| reflection_intensity | Float | 0 | Reflection intensity |
| export_specular | Bool | False | Enable specular |
| specular_level | Float | 0 | Specular level |
| specular_texture | String | "" | Specular texture |
| export_dual_tex | Bool | False | Enable dual texture |
| dual_tex_src_blend | Enum | 5 | Source blend mode (11 options) |
| dual_tex_dst_blend | Enum | 6 | Dest blend mode (11 options) |
| dual_tex_texture | String | "" | Second texture name |
| export_animation | Bool | False | Enable UV animation |
| animation_name | String | "" | Animation name |

### Scene Properties

All scene-level settings stored in `bpy.types.Scene`:

| Property | Description |
|----------|-------------|
| gtatools_game_root | GTA SA installation path |
| gtatools_ide_path | Active IDE file path |
| gtatools_ipl_path | Active IPL file path |
| gtatools_img_path | Active IMG archive path |
| gtatools_map_region | Map region (dynamic from gta.dat) |
| gtatools_img_skip_lod | Skip LOD on import |
| gtatools_img_load_txd | Auto-load TXD on import |
| gtatools_img_export_dff/col/txd | IMG export toggles |
| gtatools_export_all_dff/col/lod/txd | Export All toggles |
| gtatools_export_pipeline | Pipeline selection |
| gtatools_txd_auto_import | Auto TXD on DFF import |
| gtatools_nvtt_path | NVIDIA Texture Tools path |
| gtatools_texture_path1/2 | Texture search paths |
| gtatools_suffix_dff/lod/col | Model suffixes |
| gtatools_bake_ambient/intensity/gamma | Prelight settings |
| gtatools_bake_shadows | Enable shadow baking |
| gtatools_water_flag | Water type (0-3) |
| gtatools_water_speed_x/y/z | Water flow speed |
| gtatools_uv_grid_cols/rows | UV grid dimensions |

---

> **[Feature comparison with other tools](COMPARISON.md)**
