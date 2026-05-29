# INU Tools vs Kams Script vs DragonFF

A focused comparison of the three GTA San Andreas modding toolchains in active use. Updated for **INU Tools 2.0.2** (May 2026).

> **[🇷🇺 Русская версия](COMPARISON_rus.md)**

---

## The three contenders

| Tool | Host | Author(s) | License | Latest |
|---|---|---|---|---|
| **INU Tools** | Blender 4.2 – 5.1 | INU | GPL-3.0 | 2.0.2 (2026) |
| **Kams Script (GTA_Tools GF)** | 3ds Max | Kam, Goldfish, community | freeware (closed) | 2014–2018 |
| **DragonFF** | Blender 2.8 – 4.x | Parik | GPL-3.0 | active |

**TL;DR.** Kams covers more *formats* historically, but is locked to paid 3ds Max and has not received feature work in years. DragonFF is the lightweight Blender option for DFF/COL/TXD round-trip and ships the broadest 2DFX coverage plus native console formats. INU Tools targets the full modding pipeline inside free Blender — map building, IMG archive, peds with IK, particles, light baking — and is the only Blender-side option for full IDE write, IFP write, and IMG archive I/O.

---

## By workflow

### 🗺️ Map building

| Capability | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| IDE read / write | ✅ all sections | ✅ | — |
| IPL read (text) | ✅ all sections | ✅ | partial (experimental) |
| IPL write (text) | ✅ all sections | ✅ | partial |
| IPL binary read / write | ✅ | ✅ | — |
| IMG archive read / write | ✅ VER2 | — | — |
| Map import from IMG → scene | ✅ | ✅ | ✅ |
| **Map export scene → IDE+IPL+COL+TXD** | ✅ one-click | ✅ EMAPTool | — |
| Adaptive grid auto-split (quadtree) | ✅ | — | — |
| BBox far-objects mode | ✅ | — | — |
| Round-trip preserving CRLF / IPL dedup / `.NNN` IDs | ✅ | partial | — |
| IDE/IPL link tracking (re-add updates the row, never duplicates) | ✅ sidecar `.inu_cache/` | — | — |
| External-edit detection + Sync / Unlink / Verify | ✅ | — | — |
| Per-IPL import selection (binary **and** text) | ✅ | — | — |
| Cull zones | ✅ | ✅ | ✅ |
| Garage / Enex / Pickup / Cars / Auzo / Jump / Occl / Zone | ✅ all 8 | ✅ all 8 | — |
| `gta.dat` parsing for region detection | ✅ | — | — |
| Model ID Manager + FLA range extension | ✅ | — | — |
| X-Radar minimap maker | ✅ | — | — |

### 🚗 Vehicles — workflow helpers

> Basic vehicle DFF / COL / TXD import & export works in all three (it's the same DFF format). The rows below are the *specialised* helpers that go on top.

| Capability | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| Vehicle DFF + COL + TXD round-trip (basic) | ✅ | ✅ | ✅ |
| Dummies imported as Empties (wheels / doors / lights) | ✅ | ✅ | ✅ |
| Frame Hierarchy validation against vanilla SA template | ✅ 37 dummies | partial | — |
| `_ok` / `_dam` damage-pair operators (Add / Show / Check) | ✅ | manual | — |
| Paintjob (`_paintjob1/2`) Pay'n'Spray slots | ✅ | manual | — |
| Vehicle Scale Helper (rescale hierarchy / dummies) | ✅ | ✅ | — |

### 🦴 Peds & animation

| Capability | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| Skinned DFF read / write (byte-perfect) | ✅ | ✅ | ✅ |
| IFP read (ANP3 / ANPK / ANP2) | ✅ all 3 | ✅ all 3 | — |
| **IFP write (animation export)** | ✅ all 3 | ✅ | — |
| Apply built-in `ped.ifp` (294+ anims) | ✅ search + apply | ✅ | — |
| **Bone-based IK rig** (FK→IK bake, pole calibration) | ✅ | — | — |
| Floor limiter (FLOOR constraint on feet) | ✅ | — | — |
| Animated Map Object (windmill / crane wizard) | ✅ DFF+IFP+IDE one-click | manual | — |
| Frame / bone parent management | ✅ Hierarchy Editor + L↔R mirror | partial | partial (3 bone-prop ops) |
| Vehicle / ped template validation | ✅ vanilla SA templates | partial | — |

### 🎆 Effects & lighting

| Capability | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| 2DFX Light (raw type) | ✅ | ✅ | ✅ |
| 2DFX Light convenience presets (Lamp Post, Flashing, Traffic, Train Crossing…) | ✅ 7 presets | ✅ | — |
| 2DFX Particle | ✅ | stub | ✅ |
| 2DFX Ped Attractor / Sun Glare | ✅ | — | ✅ |
| 2DFX Enex / Road Sign / Trigger Point / Cover Point / Escalator | — | partial | ✅ all 5 |
| **`effects.fxp` parser + viewport simulation** | ✅ 82 systems, 30 FPS | — | — |
| Vertex-color light bake (raycast shadows) | ✅ | — | — |
| Day / Night vertex colors | ✅ | ✅ | ✅ |
| Vertex Alpha tools | — | ✅ | — |
| Lightmap UV2 + Multiply blend | ✅ | — | — |
| COL light bake + preview | ✅ | — | — |
| Post-processing (Smooth / Contrast / Bright / Gamma) | ✅ | — | — |
| Itera Tools 3 integration | ✅ | — | — |

### 🎨 Materials & textures

| Capability | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| TXD read | ✅ | ✅ | ✅ |
| TXD write (DXT1/3/5) | ✅ | — | ✅ experimental |
| Vectorised DXT encoder (no external binaries) | ✅ pure numpy, ~7× NVTT speed | — | — |
| Environment / Bump / Specular / Reflection | ✅ | ✅ | ✅ |
| UV Animation in DFF (read + write) | ✅ | ✅ | ✅ |
| Dual Texture / Blend Mode | ✅ | ✅ | — |
| 179 COL surface types | ✅ | ✅ | ✅ |
| Drag-drop DFF / COL / TXD into viewport | ✅ | — | — |
| Bitmaps Manager (find / cleanup unused) | ✅ | ✅ | — |
| Smart auto-TXD picker (coverage scoring) | ✅ | — | — |
| Material dedup / sort / cleanup | ✅ | — | — |

### 🛣️ Other formats

| Capability | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| `water.dat` read / write | ✅ | ✅ | — |
| `paths.ipl` (vehicle / ped) | ✅ | partial | — |
| `tracks.dat` (train) | ✅ | ✅ | — |
| `NODES.dat` compiled paths + 8×8 split | ✅ | ✅ ZZPuma | — |
| FLA4 extended path format | — | ✅ | — |
| Roadblocks / traffic-light enums | partial | ✅ | — |
| Breakable objects chunk | ✅ | ✅ | ✅ |
| CST (Steve's COL Editor) read / write | ✅ | ✅ | — |
| Object Explode (cut into pieces) | — | ✅ | — |
| Native renderware (GameCube / PS2 / PSP / Xbox / WDGL) | — | — | ✅ |
| Delta Morphs | — | — | ✅ |

### ⚙️ Pipeline & UX

| Capability | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| Free + open source | ✅ GPL-3.0 | freeware, paid host | ✅ GPL-3.0 |
| Active development | ✅ 2026 | dormant since ~2018 | ✅ |
| Native Blender (no Max licence) | ✅ | — | ✅ |
| Suffix-based batch export (`_DFF` / `_LOD` / `_COL`) | ✅ | ✅ | ✅ mass |
| Profile system (custom N-sidebar) | ✅ | — | — |
| Detachable GPU floater tool windows | ✅ | — | — |
| Per-pipeline DFF-flag memory + flags in every export dialog | ✅ | — | — |
| Configurable preset / data folder | ✅ | — | — |
| Friendly format-limit errors (model name + count, not raw struct overflow) | ✅ | — | — |
| Localization | RU / EN / ES | EN | EN |
| Real-time progress bars + cancel | ✅ | partial | — |
| Built-in tests (~300 pytest) | ✅ | — | — |

---

## When to pick what

**Pick INU Tools** if you're building maps, peds, vehicles, or particle effects on a Blender pipeline. It's the only option that round-trips full IDE / IPL / IMG inside Blender, and the only one with an `effects.fxp` editor, a bone-based IK rig, a binary file linter, and a vectorised pure-numpy DXT encoder (no external binaries).

**Pick Kams Script** if you already own 3ds Max, are continuing an existing 3ds Max project, or need a few specific niches that no Blender tool yet covers (FLA4 paths, Object Explode, Vertex Alpha tools). Be aware that the script is no longer maintained — bugs you hit are bugs you keep.

**Pick DragonFF** if you need a lightweight DFF/COL/TXD round-trip in Blender with the broadest 2DFX coverage (Cover Point, Trigger Point, Road Sign, Escalator, Enex), or if you work with native console builds (PS2 / PSP / Xbox / GameCube / WDGL). For full SA modding pipeline (map export, IDE/IFP write, particles, IK), INU is broader.

---

## Notes & methodology

- "✅" = supported in the current public release; "partial" = present but incomplete or workflow-limited; "—" = not implemented.
- Kams Script row reflects the GTA_Tools (GF) bundle by Goldfish plus community add-ons (DeniskaMax, ZZPuma, EMAPTool). Niche standalone Max tools (Water IO, etc.) are folded into the Kams column where applicable.
- Counts and section coverage verified against INU Tools 2.0.2 source (`core/`, `ops/`).
- Corrections welcome — open an issue or ping `1.n.u` on Discord.
