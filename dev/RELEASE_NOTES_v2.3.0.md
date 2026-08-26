# Release Notes — v2.3.0

Готовые тексты для GitHub release page. Скопируй нужный язык в поле описания релиза при создании тега `v2.3.0`.

---

## 🇷🇺 Русский

```markdown
## INU Tools v2.3.0 — Живой мост с Ariane, растительность/зоны/камеры и корректный round-trip шейдинга

Самый крупный релиз аддона. Главное — **двусторонний live-мост с редактором карт Ariane**: модели ходят между Blender и Ariane в реальном времени, без ручного импорта. Плюс новые инструменты (трава, зоны, камеры, фрагменты, handsign, alpha-материалы), полностью переработанный конвейер **IDE / IPL / IMG** и **запекания**, 4 новых типа 2DFX и полная локализация EN + ES. Совместимость с .blend/.dff/.ifp/.col из 2.2.x сохранена.

### 🌉 Живой мост с Ariane (round-trip редактор карт)

Двусторонний мост между Blender (INU Tools) и картовым редактором **Ariane** через общую папку (`<игра>\ariane\bridge` или `%LOCALAPPDATA%\INU_ariane_bridge`) — без запуска и ручного импорта.

- **Ariane → Blender**: жмёшь «Export to Blender» в Ariane → уже открытый Blender сам импортирует выбранные модели (DFF + LOD), расставляет по позициям (IPL) и проставляет теги (IDE). Авто-TXD, флаги vanilla / ide / ipl.
- **Blender → Ariane**:
  - **Отправить обратно** — экспорт выделенного (DFF + TXD, опц. COL) с live-reload в Ariane.
  - **Обновить позицию** — только координаты инстансов, без переэкспорта DFF/TXD.
  - **Создать модель** — регистрирует НОВУЮ модель в Ariane из выделенной геометрии (DFF + TXD + COL), получает guid.
  - **Привязать** — связать объекты Blender с УЖЕ существующими инстансами Ariane, без дублей.
- **Живая синхронизация** (watcher с настраиваемым интервалом): плавная синхронизация позиций в обе стороны, синхронизация выделения (кто последним изменил — тот и прав), определение активного окна (двигаем только когда Blender в фокусе), **двусторонняя синхронизация удалений** (удалил в Ariane → объект скрывается в Blender, обратимо; и наоборот) — по умолчанию выключена.
- Прикреплённые к мешу **2DFX** тоже уходят в экспорт.
- Иконка-планета в шапке ведёт на **наш форк Ariane** (временно, до официального релиза Ariane).

### 🆕 Новые инструменты

- **🌿 Растительность (трава)** — импорт/экспорт травы, генерация геометрии, превью во вьюпорте, применение к выделенным полигонам; встроенный редактор **plants.dat**.
- **🗺️ Зоны (map.zon)** — редактор зон (типы/уровни): импорт и экспорт `map.zon`.
- **📷 Камеры** — импорт/экспорт camera `.dat` (позиции + FOV как keyframes).
- **🧩 Фрагменты** — разбивка меша на фрагменты (breakable-геометрия) одной кнопкой.
- **✋ Handsign (ghands.ifp)** — жесты рук: прицепить/отцепить кисти к скелету, экспорт жеста.
- **🎨 Alpha-материалы** — сканирование, выделение объектов и массовое применение прозрачных материалов. **Единый стандарт прозрачности**: на Blender 4.2+ (EEVEE Next) `blend_method`/`show_transparent_back` стали мёртвыми — теперь прозрачность включается корректно во всех путях аддона (метод рендеринга + тени).

### 🗂️ IDE / IPL / IMG — переработка

- **Три вкладки**: Импорт / Экспорт / **Карта** (импорт/экспорт карты переехал из Properties → Scene).
- Бокс **«Выделенная модель»** — по каждой модели статус и действия в IDE/IPL/IMG: **Check** (проверить привязку), **Add** (добавить/обновить строку), **Export** (в IMG), 🗑 (убрать), 🔄 (вернуть координаты из IPL / проверить, в каком IMG лежит модель).
- Тумблеры импорта **LOD / 2DFX / TXD / COL** инвертированы: **ВКЛ = грузить** (убраны «Skip / Без»).
- Удаление инстанса IPL сносит и **парный LOD** + пересчитывает индексы.
- «Папка игры» (переименовано), выбор целевого IMG-архива + определение, в каком архиве лежит модель; обнаружение устаревшей привязки IDE при копировании модели со сменой ID.

### 📦 Экспорт в IMG (диалог)

- **Иерархия по модели**: DFF → (с отступом) **LOD** и **COL** с галочками (по умолчанию включены).
- Нет LOD в сцене → пишется копия основной модели как LOD; нет COL → **пустая габаритная COL-заглушка** (чтобы игра не отсекала модель).
- **Выбор IMG-архива** сверху (по умолчанию — родной IMG модели).
- Галочка **«Пересобрать после экспорта»** — сразу компактирует архив (убирает мёртвое место от старых версий).

### 🔥 Запекание текстур

- **Стек слоёв теперь у каждой модели свой** (per-model), а не общий на сцене.
- **«Изолировать объект»** (по умолчанию ВКЛ) — прячет прочие меши на время бейка: чинит **чёрный AO** среди объектов карты и заметно **ускоряет** бейк.
- **Карта Alpha** — снимает прозрачность материала в маску; при сохранении текстура выходит **RGBA** (вырез сохраняется).
- **Декаль** — галочка на любом слое (обычно Shadow): уводит яркость карты в прозрачность → **тень-декаль** (Порог/Мягкость; Мягкость = 0 — жёсткая граница; Инверсия цвета).
- **«Свет от сцены»** для Shadow / Diffuse-Lit — печёт от твоих ламп/солнца/world.
- Прилайт печётся от **всех типов света (Point/Sun/Spot/Area) + HDRI + world**.
- Предупреждение при экспорте модели **без текстуры**.

### 🗺️ Импорт: ваниль vs кастом

- Новая галочка **«Стандартная модель GTA SA (vanilla)»** — в File ▸ Import, в отдельном Import DFF и в чузере при перетаскивании .dff во вьюпорт.
  - **ВКЛ** — стандартная обработка GTA SA (ваниль не тронута).
  - **ВЫКЛ** — кастом: **связать** рассыпанную геометрию и **сохранить двусторонние заборы**.

### 🚗 Машины / DFF — корректный round-trip

- **Editable-импорт**: сваренный редактируемый меш с сохранением авторских нормалей.
- Реэкспорт не портит шейдинг: **сплит по нормали** (жёсткие кромки целы), **нет чёрных нормалей**, двусторонние заборы и reflection-слой сохраняются.
- **Замена текстуры теперь экспортируется** (имя из ноды/картинки, а не «залипшее» из импорта).
- Быстрый экспорт одной машины в DFF со встроенной коллизией.

### 💡 2DFX — 4 новых типа с превью

**Дорожный знак** (текст), **Вход/Выход** (маркер интерьера), **Эскалатор**, **Raw** (сохранение неизвестного эффекта как есть).

### 🎬 Анимации (IFP)

- **Зеркало L/R** с учётом rest-позы кости + авто-доворот Root и инверсия локации.
- Байт-точный round-trip и фиксы дёрганья (условная нормализация кватернионов, непрерывность полушарий, жёсткие 30 fps).
- **«Иерархия фреймов»** подпанелью в **Машины** (+ копия для персонажей в **Анимациях**); смена родителя прямо в дереве (⤴ назначить, ⛓ отвязать).

### 🌊 Вода

- Оверлей **«Лимиты воды»** — подсветка квадов за пределами 500-блока + привязка к сетке.
- **«Порезать по блокам (500)»** теперь и режет, и **раскидывает куски по объектам** (`Water_-3_2`, со всеми слоями/UV/материалами/флагами). Галка «Разделить на объекты» (по умолчанию ВКЛ).

### 🧱 Коллизии

- Импорт коллизий в отдельную коллекцию **«Collision»**.
- Избранные поверхности коллизии + **цвета поверхностей во вьюпорте** (как в COL-редакторе).
- Дамми-фреймы машин теперь **кубики** (видно и удобно кликать).

### 🌐 Локализация — полная EN + ES

- Переведены **все** строки интерфейса: `T(…)`-строки, сырые `description`/`name`/`label`, **тултипы-докстринги 355 операторов**, метки/описания выпадающих списков и подсказки. Русского в английском/испанском интерфейсе больше не остаётся.
- `get_locale` учитывает «Translate Interface» (аддон больше не показывает русский в English Blender).

### ⚡ Производительность

- **Кэш отрисовки N-панели** (`draw_cache`) — панели больше не сканируют сцену на каждый кадр: результат `draw()` мемоизируется по счётчику генераций depsgraph, transform-only изменения пропускаются. На больших сценах вьюпорт перестаёт «дёргаться».

### 🧹 Интерфейс и стор

- Плавающие окна: кнопки открытия убраны, оставлено окно **«Проверка»**.
- Манифест: добавлена лицензия шрифта **`SPDX:OFL-1.1`**, поле `maintainer` приведено к формату.
- Документация (DOCS / README / чеклист / сравнение) синхронизирована с аддоном.

### 🐛 Исправления

- Ревью-фиксы: краш зеркала на Blender 4.2/4.3, оверлей воды не реагировал на правку вершин, skin-header при смене числа костей, лишние вершины на нулевой нормали, безопасное превью дорожного знака, чёрный AO/Diffuse при превью+изоляции, дамми машин ломали игру при реэкспорте, мелкая чистка.
- Skin/скелет, LOD, `.ifp`; ускорен «Add to IDE».
```

---

## 🇬🇧 English

```markdown
## INU Tools v2.3.0 — Live Ariane bridge, plants/zones/cameras & correct shading round-trip

The addon's biggest release. The headline: a **two-way live bridge with the Ariane map editor** — models move between Blender and Ariane in real time, no manual import. Plus new tools (grass, zones, cameras, fragments, handsign, alpha materials), a fully reworked **IDE / IPL / IMG** and **baking** pipeline, 4 new 2DFX types, and full EN + ES localization. Compatible with .blend/.dff/.ifp/.col from 2.2.x.

### 🌉 Live Ariane bridge (round-trip map editing)

A two-way bridge between Blender (INU Tools) and the **Ariane** map editor over a shared folder (`<game>\ariane\bridge` or `%LOCALAPPDATA%\INU_ariane_bridge`) — no relaunching, no manual import.

- **Ariane → Blender**: click "Export to Blender" in Ariane → your already-open Blender imports the selected models (DFF + LOD), places them (IPL) and tags them (IDE). Auto-TXD, vanilla / ide / ipl flags.
- **Blender → Ariane**:
  - **Send back** — export the selection (DFF + TXD, optional COL) with a live-reload in Ariane.
  - **Update position** — coordinates only, without re-exporting DFF/TXD.
  - **Create model** — registers a NEW model in Ariane from the selected geometry (DFF + TXD + COL), gets a guid.
  - **Bind** — link Blender objects to EXISTING Ariane instances, no duplicates.
- **Live sync** (watcher, configurable interval): smooth two-way position sync, selection sync (last edit wins), foreground detection (only drive while Blender is focused), **two-way deletion sync** (delete in Ariane → object hidden in Blender, reversible; and back) — off by default.
- Attached **2DFX** empties are exported too.
- The globe icon in the header opens **our Ariane fork** (temporary, until Ariane's official release).

### 🆕 New tools

- **🌿 Plants / grass** — import/export grass, generate geometry, viewport preview, apply to selected polygons; built-in **plants.dat** editor.
- **🗺️ Zones (map.zon)** — zone editor (types/levels): import and export `map.zon`.
- **📷 Cameras** — import/export camera `.dat` (positions + FOV as keyframes).
- **🧩 Fragments** — split a mesh into breakable fragments in one click.
- **✋ Handsign (ghands.ifp)** — hand gestures: attach/detach hands to the skeleton, export a gesture.
- **🎨 Alpha materials** — scan, select objects and bulk-apply transparent materials. **Unified transparency standard**: on Blender 4.2+ (EEVEE Next) `blend_method`/`show_transparent_back` became dead — transparency now turns on correctly across every path (render method + shadows).

### 🗂️ IDE / IPL / IMG — reworked

- **Three tabs**: Import / Export / **Map** (full map import/export moved here from Properties → Scene).
- A **"Selected model"** box — per-model status and actions in IDE/IPL/IMG: **Check** (verify the link), **Add** (add/update the line), **Export** (to IMG), 🗑 (unlink), 🔄 (restore coordinates from IPL / find which IMG holds the model).
- Import toggles **LOD / 2DFX / TXD / COL** inverted: **ON = load** ("Skip/Без" prefixes removed).
- Deleting an IPL instance also removes its **paired LOD** and re-indexes.
- "Game folder" (renamed), target-IMG-archive picker + which-archive detection; stale-IDE-link detection when a model is copied with a changed ID.

### 📦 Export to IMG (dialog)

- **Per-model hierarchy**: DFF → (indented) **LOD** and **COL** with checkboxes (on by default).
- No LOD in the scene → the main model is written as the LOD; no COL → an **empty bounding-box COL stub** (so the game doesn't cull the model).
- **IMG-archive dropdown** at the top (defaults to the model's own IMG).
- A **"Rebuild after export"** checkbox — compacts the archive immediately (removes dead space from old versions).

### 🔥 Texture baking

- **Layer stacks are now per-model**, not a single scene-wide stack.
- **"Isolate object"** (on by default) — hides other meshes during baking: fixes **black AO** among map objects and noticeably **speeds up** baking.
- **Alpha map** — bakes material opacity into a mask; saving outputs **RGBA** (cutout preserved).
- **Decal** — a toggle on any layer (usually Shadow): routes brightness into transparency → a **shadow decal** (Threshold/Softness; Softness = 0 is a hard edge; Invert color).
- **"Scene lights"** for Shadow / Diffuse-Lit — bakes from your lamps/sun/world.
- Prelight bakes from **all light types (Point/Sun/Spot/Area) + HDRI + world**.
- Warning when exporting a model **without a texture**.

### 🗺️ Import: vanilla vs custom

- New **"Standard GTA SA model (vanilla)"** checkbox — in File ▸ Import, standalone Import DFF, and the drag-drop chooser.
  - **ON** — standard GTA SA processing (vanilla untouched).
  - **OFF** — custom: **connect** loose geometry and **keep double-sided fences**.

### 🚗 Vehicles / DFF — correct round-trip

- **Editable import**: a welded, editable mesh that keeps the authored normals.
- Re-export no longer breaks shading: **split by normal**, **no black normals**, double-sided fences and the reflection layer survive.
- **Swapping a texture now exports** (name from the image node, not a stale import stamp).
- Quick single-vehicle DFF export with embedded collision.

### 💡 2DFX — 4 new types with previews

**Road sign** (text), **Enter/Exit** (interior marker), **Escalator**, **Raw** (round-trips an unknown effect verbatim).

### 🎬 Animation (IFP)

- **L/R mirror** respecting each bone's rest pose + auto Root turn and location invert.
- Byte-exact round-trip and jitter fixes (conditional quaternion normalization, hemisphere continuity, fixed 30 fps).
- **Frame Hierarchy** as a sub-panel under **Vehicles** (+ a Ped copy under **Animations**); reparent in the tree (⤴ set, ⛓ unparent).

### 🌊 Water

- **Water Limits** overlay — highlights quads past the 500-block + snap-to-grid.
- **"Cut by blocks (500)"** now also **splits the pieces into objects** (`Water_-3_2`, with all layers/UVs/materials/flags). "Split into objects" checkbox (on by default).

### 🧱 Collision

- Collision imports into a dedicated **"Collision"** collection.
- Favourite collision surfaces + **per-surface viewport colors** (COL-editor style).
- Vehicle dummy frames are now **cubes** (visible, clickable).

### 🌐 Localization — full EN + ES

- **Every** UI string is translated: `T(…)` strings, raw `description`/`name`/`label`, **the docstring tooltips of 355 operators**, dropdown item labels/descriptions and hints. No Russian remains in the English/Spanish interface.
- `get_locale` honours "Translate Interface" (no more Russian in an English Blender).

### ⚡ Performance

- **N-panel draw cache** (`draw_cache`) — panels no longer scan the scene every frame: the `draw()` result is memoised against the depsgraph generation counter and transform-only changes are skipped. On large scenes the viewport stops stuttering.

### 🧹 Interface & store

- Floating windows: launch buttons removed, the **"Validation"** window kept.
- Manifest: added the **`SPDX:OFL-1.1`** font license, fixed the `maintainer` field.
- Docs (DOCS / README / checklist / comparison) synced to the addon.

### 🐛 Fixes

- Review fixes: mirror crash on Blender 4.2/4.3, water overlay ignoring vertex edits, skin header on bone-count change, redundant verts on zero normals, safe road-sign preview, black AO/Diffuse with preview+isolation, vehicle dummies crashing the game on re-export, minor cleanup.
- Skin/skeleton, LOD, `.ifp`; faster "Add to IDE".
```

---

## 🇪🇸 Español (resumen)

```markdown
## INU Tools v2.3.0 — Puente en vivo con Ariane, plantas/zonas/cámaras y round-trip de sombreado correcto

La versión más grande del addon. Lo principal: un **puente bidireccional en vivo con el editor de mapas Ariane** — los modelos viajan entre Blender y Ariane en tiempo real, sin importación manual. Además: herramientas nuevas, un flujo **IDE / IPL / IMG** y de **horneado** rehecho, 4 tipos de 2DFX y localización completa EN + ES.

- 🌉 **Puente en vivo con Ariane**: Ariane → Blender (importa e coloca solo al pulsar «Export to Blender»); Blender → Ariane (**enviar de vuelta**, **actualizar posición**, **crear modelo**, **vincular** a instancias existentes); sincronización en vivo de posición/selección/**borrados** en ambos sentidos; los 2DFX adjuntos también se exportan. El icono del globo abre **nuestro fork de Ariane** (temporal, hasta el lanzamiento de Ariane).
- 🆕 **Herramientas nuevas**: 🌿 plantas/plants.dat, 🗺️ zonas/map.zon, 📷 cámaras (.dat), 🧩 fragmentos, ✋ handsign/ghands.ifp, 🎨 materiales alpha (estándar de transparencia unificado, arregla EEVEE Next 4.2+).
- 🗂️ **IDE/IPL/IMG rehecho**: pestaña **Mapa**; caja «Modelo seleccionado» (Check/Add/Export/🗑/🔄); casillas LOD/2DFX/TXD/COL invertidas (ON = cargar); acciones por archivo; destino IMG + detección de archivo; borrar instancia IPL borra su LOD + reindexa.
- 📦 **Exportar a IMG (diálogo)**: jerarquía DFF → LOD/COL con casillas; sin LOD → modelo principal como LOD; sin COL → COL sustituto vacío; selector de archivo IMG; casilla «Reconstruir tras exportar».
- 🔥 **Horneado**: pila de capas **por modelo**; **«Aislar objeto»** (corrige el AO negro entre objetos del mapa y acelera); decal de sombra (Alpha/Decal), RGBA, «Luz de la escena»; prelight desde todos los tipos de luz + HDRI. Aviso al exportar un modelo sin textura.
- 🗺️ Casilla **vanilla / custom** al importar. 🚗 DFF: importación editable con normales, re-exportación sin romper sombreado, exportación del cambio de textura. 💡 2DFX: señal, entrada/salida, escalera, raw.
- 🎬 IFP: espejo L/R + round-trip exacto; jerarquía de frames como sub-panel. 🌊 Agua: límites + cortar por bloques en objetos. 🧱 Colisiones en colección "Collision" (colores por superficie), dummies como cubos.
- 🌐 **Localización completa EN + ES**: todas las cadenas, incluidos los tooltips-docstring de 355 operadores y las listas desplegables.
- ⚡ **Rendimiento**: caché de dibujo del panel N (los paneles ya no escanean la escena en cada fotograma; el viewport deja de tironear en escenas grandes).
- 🧹 Ventanas flotantes reducidas a «Validación»; manifiesto: +`SPDX:OFL-1.1`, `maintainer`; documentación sincronizada.
- 🐛 Correcciones de revisión (crash del espejo en 4.2/4.3, overlay de agua, skin-header, AO negro con vista previa+aislamiento, dummies de vehículos, etc.).
```
