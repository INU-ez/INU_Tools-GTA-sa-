# INU_Tools (GTA SA) — Documentation

> **[Русская версия](DOCS.md)** | **[English](DOCS_eng.md)**

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
- [UV Tools](#uv-tools)
- [Characters (Skinned DFF)](#characters-skinned-dff)
- [Water IO](#water-io)
- [Path IO](#path-io)
- [Integrations](#integrations)
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

### COL (Collision)

| Button | Operator | Description |
|--------|----------|-------------|
| Import COL | `gtatools.import_col` | Import .col with surface materials |
| Export COL | `gtatools.export_col` | Export as COL3 format |

COL export automatically sets object type to Collision, centers at origin, and writes surface material IDs.

### TXD (Textures)

| Button | Operator | Description |
|--------|----------|-------------|
| Import TXD | `gtatools.import_txd` | Extract textures and assign to materials |
| Export TXD | `gtatools.export_txd` | Compile textures into .txd archive |

**GPU mode:** if NVIDIA Texture Tools (NVTT) is installed and path is configured in Settings → NVTT, compression uses GPU automatically. Otherwise falls back to CPU.

**Supported formats:** DXT1 (opaque), DXT3 (sharp alpha), DXT5 (smooth alpha). Auto-detected based on alpha channel.

### Export All (Batch)

| Button | Operator | Description |
|--------|----------|-------------|
| Export All | `gtatools.export_all` | Batch export DFF+COL+LOD+TXD |

Select objects with suffixes (`_DFF`, `_LOD`, `_COL`), click Export All, choose output folder.

**Toggles:** DFF / COL / LOD / TXD — enable/disable each format.

**Pipeline:** None / Building (Day/Night vertex colors) / Reflections (window reflections).

### Collection Export

If **no objects are selected**, Export All takes all mesh objects from the **active collection** (including child collections). This allows exporting an entire collection without selecting everything.

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

### IMG Archive

| Button | Operator | Description |
|--------|----------|-------------|
| Import from IMG | `gtatools.import_from_img` | Extract and import models by IDE/IPL listing |
| Export to IMG | `gtatools.export_to_img` | Pack DFF+COL+TXD directly into .img archive |

**Export toggles:** DFF / COL / TXD — choose what to pack.

**Import options:** Skip LOD / Load TXD.

### BBox Mode

| Button | Operator | Description |
|--------|----------|-------------|
| BBox: ON/OFF | `gtatools.toggle_bbox` | Toggle Bounding Box display for map objects |

When enabled, all Map_ collection objects switch to `BOUNDS` display. Objects within 300m of the selected object stay as `TEXTURED`. Updates automatically when selection changes.

### Model ID Manager

**Panel:** Properties → Scene → INU Tools → ID Manager

- Shows free/used ID count
- **Next free ID** displayed
- **Auto Assign** — assigns next free ID to selected objects
- **Release** — marks ID as free
- IDs stored in `model_ids.txt` in INU_Preset folder

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

### COL Surface Types

**Panel:** Properties → Material → COL Surface Type

179 GTA SA surface materials organized in 13 categories. Searchable dropdown with category filtering. Each surface has:
- Surface ID (0-178)
- Flags, Brightness, Light
- Day Light (0-15), Night Light (0-15)

### Textures

**Panel:** Properties → Scene → INU Tools → Textures

- **System textures** — path to a shared texture folder (e.g. `System_textures` from MTA/GTA)
- **.blend folder** — automatically points to the current .blend file's directory. Refresh button 🔄 updates the path
- **Load Textures** — searches for PNG/TGA/JPG files matching material names on the object. Searches both folders: system and .blend. If a material is named `brick_wall`, the addon finds `brick_wall.png` in the specified folders and assigns it as texture
- **Drag & Drop** — drag images from File Browser directly into the viewport to create a new material with the texture

---

## Prelight (Vertex Colors)

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

### Fill Colors

Paint selected faces with a chosen color. Supports levels (layers of fill) and undo/restore.

### Scatter Light

Distribute light from selected faces outward. Parameters:
- Intensity, Falloff, Radius, Iterations

### Post-Processing

| Tool | Description |
|------|-------------|
| Smooth | Average colors between neighboring vertices |
| Smooth Between Objects | Smooth at seams between different meshes |
| Contrast | Adjust color contrast |
| Brightness | Adjust brightness offset |
| Gamma | Gamma correction |

### COL Light

**Panel:** View3D → Sidebar (N) → GTA Tools → Prelight COL

Convert vertex colors to COL Day/Night Light values (0-15). Auto-splits materials by brightness ranges.

- **Preview** — visualize light values on mesh
- **Bake** — write values to COL material properties
- **Day/Night ranges** — adjustable thresholds

### Presets

Save/load prelight settings (Ambient, Intensity, Gamma, Shadows) as named presets. Stored in `INU_Preset/` folder.

### Vertex Color Management

| Button | Description |
|--------|-------------|
| Create Day/Night | Creates both `Day` and `Night` color attributes |
| Day + / Night + | Create individual color attribute |
| Day - / Night - | Remove individual color attribute |
| Toggle Preview | Enable/disable Day/Night mix visualization in viewport |
| Analyze | Show vertex color histogram (min/max/avg) |
| Reset | Reset bake settings to defaults |

**Edit/Paint modes:** buttons to switch between Object, Edit, and Vertex Paint modes for quick workflow.

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

**Preview:** real-time corona/shadow visualization in viewport.

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

### IFP Animations

| Button | Operator | Description |
|--------|----------|-------------|
| Import IFP | `gtatools.import_ifp` | Load animation file (294+ animations in ped.ifp) |
| Export IFP | `gtatools.export_ifp` | Save Blender Actions as IFP |
| Apply | `gtatools.apply_ifp` | Assign animation to armature |

Searchable animation list in the panel.

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

### Train Tracks

| Button | Description |
|--------|-------------|
| Import tracks.dat | Load train track data |
| Export tracks.dat | Save track definitions |
| Create Track | New track curve |
| Mark Station | Toggle station point (edit mode) |

### Compiled Nodes

| Button | Description |
|--------|-------------|
| Import NODES.dat | Load compiled binary path nodes |
| Export NODES.dat | Save compiled nodes |

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

### Lightmap Generator (MTA)

**Panel:** View3D → Sidebar (N) → GTA Tools → Lightmap Generator (beta)

Generate Lua code for MTA SA lightmap scripts.

| Button | Operator | Description |
|--------|----------|-------------|
| Load Lightmap | `gtatools.load_lightmap` | Load lightmap image for preview |
| Remove Lightmap | `gtatools.remove_lightmap` | Remove loaded lightmap |
| Generate | `gtatools.lightmap_generate` | Generate Lua code from object textures |
| Copy | `gtatools.lightmap_copy` | Copy result to clipboard |
| Clear | `gtatools.lightmap_clear` | Clear generated code |

**Fields:** lightmap path, model ID. Output: Lua table with texture names and lightmap references.

The MTA lightmap script itself is available in the [Issues](../../issues) section of the repository.

### Pipeline

Render pipeline determines how the GTA SA engine processes the model:
- **None** — no pipeline. Suitable for most objects: furniture, fences, vegetation, characters
- **Building** (0x53F2009A) — Day/Night vertex colors. Required for buildings and map objects that have vertex colors — without this pipeline, day/night color transitions won't work in-game
- **Reflections** (0x53F20098) — window reflections. Only for window models that should reflect the environment. Windows must be a separate model from the building

### Normals

The **Normals** toggle controls vertex normal export in DFF:
- **Enabled** — the model receives dynamic lighting from the GTA SA engine. Required for: characters, vehicles, weapons, interactive objects
- **Disabled** — the model is lit only by baked vertex colors. Used for: buildings, roads, map objects

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
