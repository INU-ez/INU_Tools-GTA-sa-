# Release Notes — v1.7.0

Готовые тексты для GitHub release page. Скопируй нужный язык в поле описания релиза при создании тега `v1.7.0`.

---

## 🇷🇺 Русский

```markdown
## INU Tools v1.7.0 — IK Rig, Animated Map Objects, Profile System

Большой UX-релиз с новыми фичами и глубоким рефакторингом. **22 новых модуля** в `ops/`, монолитный `__init__.py` уменьшен с 16486 → 4327 строк. Полная backward-совместимость с .blend/.dff/.ipl/.ide из 1.6.x.

### 🆕 Новые фичи

**Animation**
- 🦴 **IK Rig для SA peds** — `Add IK Rig` создаёт control-bones (chain/pole/rot/root) внутри армати с custom-shape кубиками. FK→IK bake при создании сохраняет существующие анимации. Brute-force калибровка `pole_angle` справляется с произвольным roll кости. `Bake & Clear IK` снимает control-bones перед IFP экспортом.
- 🦶 **Floor limiter** — встроенная плоскость `INU_Ground` 10×10м с `dev_anim.png` + offset-slider. FLOOR constraint автоматически на foot IK target — стопы не проваливаются под пол.
- 🌀 **Animated Map Object** — workflow для мельниц / кранов / флюгеров: `Setup rig` создаёт скелет одной кости + Action с заданным числом оборотов, `Validate` проверяет связи, `Export DFF+IFP+IDE` пишет всё одной кнопкой. Live-edit ползунки axis/turns/duration/reverse с auto-rebuild keyframes.
- 🦴 **Frame Hierarchy Editor** — Rename / Set Parent / Unparent / Зеркало L↔R / Validate Vehicle / Validate Ped. Древо потомков активного объекта прямо в N-sidebar. Validate сравнивает с vanilla SA шаблонами (37 dummies для машин, 31 кость для педов).

**Vehicles**
- 🎨 **Paintjob (Pay'n'Spray)** — на материале два слота `Paintjob 1 / 2`, TXD-экспортёр пишет `<base>_paintjob1/2`. `Validate Paintjobs` проверяет полноту слотов.

**Map workflow**
- 📐 **Adaptive grid auto-split** — quadtree-разбиение по плотности: ячейка делится 2×2 пока в ней больше `max_per_cell` DFF (по умолчанию 200). Плотные районы получают мелкие ячейки, разреженные остаются одной большой. `min_cell_size` floor защищает от бесконечной рекурсии при стопке DFF в одной XY-точке. Имя подпапки `<base>_q<path>` (0=SW, 1=SE, 2=NW, 3=NE).

**Workflow / UI**
- 🗂️ **Profile system** — кастомные наборы видимых панелей N-sidebar с порядком, JSON-storage в `INU_Preset/profiles/<name>.json`. Dropdown в шапке главной панели + кнопки `+ / − / edit`.
- 🖱️ **Drag-drop DFF / COL во viewport** — как раньше с TXD; TXD-drop теперь цепляет созданные материалы на выделенные меши.
- 🎯 **Smart auto-TXD picker** — coverage-based scoring при импорте DFF: сначала `<dff>.txd`, затем .txd с покрытием ≥50% текстур, затем единственный .txd в папке. С `name_filter` грузятся только нужные текстуры (vehicle.txd 150 → ~5 для одной двери).
- 💾 **Save-required wrappers** для Extract Resources / Import Map / Export Map — disabled-кнопки пока `.blend` не сохранён.
- ⚠️ **Soft cache-empty warning** для Import Map — продолжает с Empty placeholders вместо hard cancel.
- 📦 **Compact mass export** — `В папку` / `В IMG` уехали в дропдаун `Экспорт ▾` как `All → Папка` / `All → IMG`.
- 🎨 **Texture Manager dropdowns** — `Текстуры ▾` (Найти / Скопировать / Дубли / Найти-Удалить unused) + `Материалы ▾` (Check / Cleanup / Sort) вместо 9 кнопок.
- 💡 **2DFX panel collapsible** — секции `Свойства света` / `Поведение` / `Тень` / `Флаги` свёрнуты по умолчанию. Light flags сгруппированы семантически (Видимость / Эффекты короны / Мерцание / Доп.). Per-bit tooltips через operator description classmethod.
- 🎛️ **DFF Flags pipeline-aware** — Vehicle pipeline прячет `Day/Night/Light Beam`, Day/Night pipeline прячет mesh-флаги Day/Night (он управляет переходом через VC слои).
- 🔗 **Связи DFF↔LOD↔COL toggle** — переехал из Map в Check панель как `Связи: ON/OFF`.
- 📋 **IDE/IPL panel** — 2-column layout, niche IPL utilities (Sections / Replace Empty) полной шириной снизу.
- 🚗 **Vehicle panel** вынесен из Check как отдельная панель.
- 💡 **Light Master container** — 5 sub-panels (Prelight / Prelight COL / Vertex Paint / Lightmap / Itera Tools) под одним заголовком.

**Format support**
- 📦 **BreakableData round-trip** — reader для `CHUNK_BREAKABLE` (writer был в 1.6.4).
- 🎨 **Paintjob alt textures** в TXD — `<base>_paintjob1/2`.
- 🎮 **`read_txd_texture_names()`** — header-only TXD parse, ~50× быстрее `read_txd_file`.

### 🐛 Bug fixes

- **TXD import duplicates** (`vehiclelights128.001-005`) — устранены за счёт in-place `Image.scale()` + name_filter в импортёре.
- **Material deduplication** при DFF import — fingerprint всех effect-блоков (env/bump/specular/reflection/dual_texture) в ключе кэша; раньше дубли при `has_effects=True`.
- **2DFX preview plane size** — `corona_size * 5.0` визуально показывал короны в 5× → теперь нативный размер.
- **IFP export round-trip** — добавлен `rest_quat @ bl_quat` инверс; раньше custom анимации экспортились flat.
- **IFP custom skin root motion** — bone_id fallback для custom-renamed root ('Bip01'/'Root' вместо vanilla 'Normal').
- **Blender 5.x compat** — layered Action API в IFP exporter, `default=set()` fix в map_export, particle panel callable items.

### 🔧 Refactoring

`__init__.py` уменьшен с 16486 → 4327 строк. **22 новых `ops/*.py`** модуля + новые `ui/panels.py` (2820 строк) и `ui/registry.py` с `apply_order` декоратором. Все `bl_label` operators получили префикс `INU:` для F3-поиска.

### 🧪 Tests

7 новых pytest-файлов, ~110 тестов (DFF / COL / IDE / IPL / IMG round-trip + panel registry + profiles).

### 📚 Docs

- Repo cleanup: `docs/` папка, удалён COMPARISON.md
- DOCS_rus.md +470 строк: новые рецепты IK Rig, Profile system, Animated Map Object, Frame Hierarchy, Paintjob
- README обновлены пути и переписана секция Coming-next под backlog v1.7.1

### Установка

1. Скачай `INU_tools/` из релиза или zip-архив
2. Скопируй в `Blender/<version>/scripts/addons/INU_tools/`
3. `Edit → Preferences → Add-ons` → активируй **INU_tools(gta_sa)**

### Совместимость

- Blender 4.2 – 5.1 ✅
- GTA San Andreas (также совместимо с MTA:SA)
- Windows / Linux / macOS

**Полный diff:** [v1.6.7...v1.7.0](https://github.com/INU-ez/INU_Tools-GTA-sa-/compare/v1.6.7...v1.7.0)
```

---

## 🇬🇧 English

```markdown
## INU Tools v1.7.0 — IK Rig, Animated Map Objects, Profile System

Major UX release with new features and a deep refactor. **22 new modules** in `ops/`, monolithic `__init__.py` shrunk from 16486 → 4327 lines. Full backward compatibility with .blend/.dff/.ipl/.ide from 1.6.x.

### 🆕 New features

**Animation**
- 🦴 **Bone-based IK rig for SA peds** — `Add IK Rig` creates control bones (chain/pole/rot/root) inside the SA armature with custom-shape wireframe cubes. FK→IK bake on creation preserves existing animations. Brute-force `pole_angle` calibration handles arbitrary SA bone roll. `Bake & Clear IK` strips control bones before IFP export.
- 🦶 **Floor limiter** — bundled `INU_Ground` plane (10×10 m, `dev_anim.png` texture) + tunable offset slider. FLOOR constraint auto-pinned to every foot IK target so feet can't sink below ground.
- 🌀 **Animated Map Object** — workflow for windmills / cranes / weather vanes: `Setup rig` builds a single-bone armature + Action with N turns, `Validate` checks links, `Export DFF+IFP+IDE` writes all three in one click. Live-edit sliders (axis / turns / duration / reverse) with auto-rebuild keyframes.
- 🦴 **Frame Hierarchy Editor** — Rename / Set Parent / Unparent / Mirror L↔R / Validate Vehicle / Validate Ped. Descendants tree of the active object directly in the N-sidebar. Validate compares against vanilla SA templates (37 dummies for vehicles, 31 bones for peds).

**Vehicles**
- 🎨 **Paintjob (Pay'n'Spray)** — material gets two `Paintjob 1 / 2` slots; TXD exporter writes `<base>_paintjob1/2`. `Validate Paintjobs` verifies slot completeness.

**Map workflow**
- 📐 **Adaptive grid auto-split** — density-driven quadtree subdivision: a cell splits 2×2 whenever it holds more than `max_per_cell` DFFs (default 200). Dense regions get small cells, sparse regions stay as one big cell. A `min_cell_size` floor protects against infinite recursion when many DFFs share an XY point (stacked vertical buildings). Subdirectory naming: `<base>_q<path>` (0=SW, 1=SE, 2=NW, 3=NE).

**Workflow / UI**
- 🗂️ **Profile system** — custom N-sidebar layouts (visibility + order) saved as JSON in `INU_Preset/profiles/<name>.json`. Dropdown in the main panel header with `+ / − / edit` buttons.
- 🖱️ **Drag-drop DFF / COL into viewport** — like the existing TXD drop; TXD drop now attaches created materials to selected meshes.
- 🎯 **Smart auto-TXD picker** — coverage-based scoring on DFF import: first `<dff>.txd`, then any .txd with ≥50% texture coverage, then the only .txd in the folder. With `name_filter` only the needed textures decompress (vehicle.txd 150 → ~5 for one door).
- 💾 **Save-required wrappers** for Extract Resources / Import Map / Export Map — buttons disabled until `.blend` is saved.
- ⚠️ **Soft cache-empty warning** for Import Map — proceeds with Empty placeholders instead of hard-cancelling.
- 📦 **Compact mass export** — `To Folder` / `To IMG` moved into the `Export ▾` dropdown as `All → Folder` / `All → IMG`.
- 🎨 **Texture Manager dropdowns** — `Textures ▾` (Find / Copy / Dupes / Find-Remove unused) + `Materials ▾` (Check / Cleanup / Sort) instead of 9 buttons.
- 💡 **2DFX panel collapsible** — `Light Properties` / `Behaviour` / `Shadow` / `Flags` sections collapsed by default. Light flags grouped semantically (Visibility / Corona Effects / Blinking / Misc.). Per-bit tooltips via operator `description` classmethod.
- 🎛️ **DFF Flags pipeline-aware** — Vehicle pipeline hides `Day/Night/Light Beam`; Day/Night pipeline hides mesh Day/Night flags (it handles transitions via VC layers).
- 🔗 **Links DFF↔LOD↔COL toggle** — moved from Map to Check panel as `Links: ON/OFF`.
- 📋 **IDE/IPL panel** — 2-column layout; niche IPL utilities (Sections / Replace Empty) full-width below.
- 🚗 **Vehicle panel** split out from Check as a dedicated panel.
- 💡 **Light Master container** — 5 sub-panels (Prelight / Prelight COL / Vertex Paint / Lightmap / Itera Tools) under one header.

**Format support**
- 📦 **BreakableData round-trip** — reader for `CHUNK_BREAKABLE` (writer was added in 1.6.4).
- 🎨 **Paintjob alt textures** in TXD — `<base>_paintjob1/2`.
- 🎮 **`read_txd_texture_names()`** — header-only TXD parse, ~50× faster than `read_txd_file`.

### 🐛 Bug fixes

- **TXD import duplicates** (`vehiclelights128.001-005`) — fixed via in-place `Image.scale()` + name_filter in the importer.
- **Material deduplication** on DFF import — cache key now fingerprints all effect blocks (env / bump / specular / reflection / dual_texture); previously duplicated when `has_effects=True`.
- **2DFX preview plane size** — `corona_size * 5.0` showed coronas 5× their game size; now native size.
- **IFP export round-trip** — added `rest_quat @ bl_quat` inverse; previously custom animations exported flat.
- **IFP custom skin root motion** — bone_id fallback for custom-renamed root ('Bip01' / 'Root' instead of vanilla 'Normal').
- **Blender 5.x compat** — layered Action API in IFP exporter, `default=set()` fix in map_export, particle panel callable items.

### 🔧 Refactoring

`__init__.py` shrunk from 16486 → 4327 lines. **22 new `ops/*.py`** modules + new `ui/panels.py` (2820 lines) and `ui/registry.py` with the `apply_order` decorator. All operator `bl_label`s prefixed with `INU:` for F3 search.

### 🧪 Tests

7 new pytest files, ~110 tests (DFF / COL / IDE / IPL / IMG round-trip + panel registry + profiles).

### 📚 Docs

- Repo cleanup: `docs/` folder, removed COMPARISON.md
- DOCS_rus.md +470 lines: new recipes for IK Rig, Profile system, Animated Map Object, Frame Hierarchy, Paintjob
- READMEs updated paths and rewrote Coming-next section against backlog v1.7.1

### Installation

1. Download `INU_tools/` from release or the zip archive
2. Copy to `Blender/<version>/scripts/addons/INU_tools/`
3. `Edit → Preferences → Add-ons` → enable **INU_tools(gta_sa)**

### Compatibility

- Blender 4.2 – 5.1 ✅
- GTA San Andreas (also compatible with MTA:SA)
- Windows / Linux / macOS

**Full diff:** [v1.6.7...v1.7.0](https://github.com/INU-ez/INU_Tools-GTA-sa-/compare/v1.6.7...v1.7.0)
```
