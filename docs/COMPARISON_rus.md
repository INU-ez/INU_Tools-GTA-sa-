# INU Tools vs Kams Script vs DragonFF

Фокусное сравнение трёх актуальных тулчейнов для моддинга GTA San Andreas. Актуально для **INU Tools 2.3.0** (2026).

> **[🇬🇧 English version](COMPARISON.md)**

---

## Участники

| Инструмент | Хост | Авторы | Лицензия | Версия |
|---|---|---|---|---|
| **INU Tools** | Blender 4.2 – 5.1 | INU | GPL-3.0 | 2.3.0 (2026) |
| **Kams Script (GTA_Tools GF)** | 3ds Max | Kam, Goldfish, community | freeware (closed) | 2014–2018 |
| **DragonFF** | Blender 2.8 – 4.x | Parik | GPL-3.0 | active |

**Кратко.** Kams исторически покрывает больше форматов, но привязан к платному 3ds Max и не получает обновлений несколько лет. DragonFF — лёгкий вариант для DFF/COL/TXD round-trip в Blender, плюс самое широкое покрытие 2DFX и native console форматы. INU Tools закрывает полный пайплайн в бесплатном Blender'е — карты, IMG-архивы, педы с IK, частицы, лайтбейк — и единственный со стороны Blender умеет писать полный IDE, писать IFP и работать с IMG-архивом.

---

## По задачам

### 🗺️ Постройка карт

| Возможность | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| IDE чтение / запись | ✅ все секции | ✅ | — |
| IPL чтение (текст) | ✅ все секции | ✅ | partial (experimental) |
| IPL запись (текст) | ✅ все секции | ✅ | partial |
| IPL binary чтение / запись | ✅ | ✅ | — |
| IMG-архив чтение / запись | ✅ VER2 | — | — |
| Импорт карты IMG → сцена | ✅ | ✅ | ✅ |
| **Экспорт сцена → IDE+IPL+COL+TXD** | ✅ одной кнопкой | ✅ EMAPTool | — |
| Адаптивный grid auto-split (quadtree) | ✅ | — | — |
| BBox для дальних объектов | ✅ | — | — |
| Round-trip с CRLF / IPL dedup / `.NNN` ID | ✅ | partial | — |
| Трекинг связей IDE/IPL (повторное добавление обновляет строку, без дублей) | ✅ sidecar `.inu_cache/` | — | — |
| Детекция внешних правок + Sync / Unlink / Verify | ✅ | — | — |
| Выбор конкретных IPL при импорте (бинарные **и** текстовые) | ✅ | — | — |
| Cull зоны | ✅ | ✅ | ✅ |
| Garage / Enex / Pickup / Cars / Auzo / Jump / Occl / Zone | ✅ все 8 | ✅ все 8 | — |
| Парсинг `gta.dat` для регионов | ✅ | — | — |
| Model ID Manager + расширение FLA | ✅ | — | — |
| X-Radar minimap maker | ✅ | — | — |

### 🚗 Машины — workflow-помощники

> Базовый импорт/экспорт vehicle DFF / COL / TXD работает во всех трёх (это тот же формат DFF). Строки ниже — специализированные помощники сверх этого.

| Возможность | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| Vehicle DFF + COL + TXD round-trip (базовый) | ✅ | ✅ | ✅ |
| Dummies импортируются как Empty (колёса / двери / фары) | ✅ | ✅ | ✅ |
| Валидация Frame Hierarchy по vanilla SA-шаблону | ✅ 37 dummies | partial | — |
| `_ok` / `_dam` damage-pair операторы (Add / Show / Check) | ✅ | вручную | — |
| Paintjob (`_paintjob1/2`) Pay'n'Spray слоты | ✅ | вручную | — |
| Vehicle Scale Helper (масштаб иерархии / dummies) | ✅ | ✅ | — |

### 🦴 Педы и анимации

| Возможность | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| Skinned DFF чтение / запись (byte-perfect) | ✅ | ✅ | ✅ |
| IFP чтение (ANP3 / ANPK / ANP2) | ✅ всё 3 | ✅ всё 3 | — |
| **IFP запись (экспорт анимации)** | ✅ всё 3 | ✅ | — |
| Применение `ped.ifp` (294+ анимаций) | ✅ поиск + apply | ✅ | — |
| **Bone-based IK rig** (FK→IK bake, pole калибровка) | ✅ | — | — |
| Floor limiter (FLOOR constraint на стопы) | ✅ | — | — |
| Animated Map Object (мельница / кран wizard) | ✅ DFF+IFP+IDE одной кнопкой | вручную | — |
| Управление frame / parent bone | ✅ Hierarchy Editor + Mirror L↔R | partial | partial (3 bone-prop ops) |
| Валидация vehicle / ped по шаблонам SA | ✅ vanilla SA-шаблоны | partial | — |

### 🎆 Эффекты и свет

| Возможность | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| 2DFX Light (сырой тип) | ✅ | ✅ | ✅ |
| 2DFX Light convenience-пресеты (Lamp Post, Flashing, Traffic, Train Crossing…) | ✅ 7 пресетов | ✅ | — |
| 2DFX Particle | ✅ | stub | ✅ |
| 2DFX Ped Attractor / Sun Glare | ✅ | — | ✅ |
| 2DFX Enex / Road Sign / Trigger Point / Cover Point / Escalator | — | partial | ✅ всё 5 |
| **`effects.fxp` парсер + симуляция в viewport** | ✅ 82 системы, 30 FPS | — | — |
| Vertex-color бейк света (raycast тени) | ✅ | — | — |
| Day / Night vertex colors | ✅ | ✅ | ✅ |
| Vertex Alpha инструменты | — | ✅ | — |
| Lightmap UV2 + Multiply blend | ✅ | — | — |
| COL light бейк + превью | ✅ | — | — |
| Post-processing (Smooth / Contrast / Bright / Gamma) | ✅ | — | — |
| Интеграция Itera Tools 3 | ✅ | — | — |

### 🎨 Материалы и текстуры

| Возможность | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| TXD чтение | ✅ | ✅ | ✅ |
| TXD запись (DXT1/3/5) | ✅ | — | ✅ experimental |
| Векторизованный DXT-энкодер (без внешних бинарников) | ✅ pure numpy, ~×7 быстрее | — | — |
| Environment / Bump / Specular / Reflection | ✅ | ✅ | ✅ |
| UV Animation в DFF (чтение + запись) | ✅ | ✅ | ✅ |
| Dual Texture / Blend Mode | ✅ | ✅ | — |
| 179 COL surface types | ✅ | ✅ | ✅ |
| Drag-drop DFF / COL / TXD во viewport | ✅ | — | — |
| Bitmaps Manager (поиск / очистка unused) | ✅ | ✅ | — |
| Smart auto-TXD picker (coverage scoring) | ✅ | — | — |
| Material dedup / sort / cleanup | ✅ | — | — |

### 🛣️ Прочие форматы

| Возможность | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| `water.dat` чтение / запись | ✅ | ✅ | — |
| `paths.ipl` (vehicle / ped) | ✅ | partial | — |
| `tracks.dat` (поезда) | ✅ | ✅ | — |
| `NODES.dat` compiled paths + 8×8 split | ✅ | ✅ ZZPuma | — |
| FLA4 extended path format | — | ✅ | — |
| Roadblocks / traffic-light enums | partial | ✅ | — |
| Breakable objects chunk | ✅ | ✅ | ✅ |
| CST (Steve's COL Editor) чтение / запись | ✅ | ✅ | — |
| Object Explode (разрезка на куски) | ✅ grid + scatter | ✅ | — |
| Native renderware (GameCube / PS2 / PSP / Xbox / WDGL) | — | — | ✅ |
| Delta Morphs | — | — | ✅ |

### ⚙️ Пайплайн и UX

| Возможность | INU Tools | Kams | DragonFF |
|---|:---:|:---:|:---:|
| Бесплатно + open source | ✅ GPL-3.0 | freeware, платный хост | ✅ GPL-3.0 |
| Активная разработка | ✅ 2026 | dormant с ~2018 | ✅ |
| Нативный Blender (без лицензии Max) | ✅ | — | ✅ |
| Batch-экспорт по суффиксам (`_DFF` / `_LOD` / `_COL`) | ✅ | ✅ | ✅ mass |
| Profile system (кастомный N-sidebar) | ✅ | — | — |
| Отрывные GPU floater-окна | ✅ | — | — |
| Память DFF-флагов по пайплайнам + флаги в каждом диалоге экспорта | ✅ | — | — |
| Настраиваемая папка пресетов / данных | ✅ | — | — |
| Понятные ошибки лимитов формата (имя модели + счётчик, без сырого struct overflow) | ✅ | — | — |
| Локализация | RU / EN / ES | EN | EN |
| Real-time progress bar + отмена | ✅ | partial | — |
| Встроенные тесты (~300 pytest) | ✅ | — | — |

---

## Что выбирать

**Бери INU Tools**, если строишь карты, педов, машины или эффекты в Blender-пайплайне. Это единственный вариант с round-trip полного IDE / IPL / IMG внутри Blender, и единственный со встроенным `effects.fxp` редактором, bone-based IK ригом, линтером бинарных файлов и векторизованным pure-numpy DXT-энкодером (без внешних бинарников).

**Бери Kams Script**, если у тебя уже есть 3ds Max, продолжаешь существующий проект на Max, или нужны точечные ниши, которые ещё не закрыты в Blender-стороне (FLA4 paths, Object Explode, Vertex Alpha инструменты). Учти: скрипт давно не обновляется — баги, в которые упрёшься, останутся с тобой.

**Бери DragonFF**, если нужен лёгкий round-trip DFF/COL/TXD в Blender с самым широким покрытием 2DFX (Cover Point, Trigger Point, Road Sign, Escalator, Enex), или если работаешь с native console сборками (PS2 / PSP / Xbox / GameCube / WDGL). Для полного SA-пайплайна (map export, IDE/IFP write, частицы, IK) — INU шире.

---

## Заметки и методология

- «✅» = поддерживается в текущем публичном релизе; «partial» = есть, но неполно или ограниченный workflow; «—» = не реализовано.
- Строка Kams отражает GTA_Tools (GF) от Goldfish плюс community-аддоны (DeniskaMax, ZZPuma, EMAPTool). Точечные standalone-инструменты под Max (Water IO и т.п.) свёрнуты в колонку Kams где применимо.
- Покрытие сверено с исходниками INU Tools 2.3.0 (`core/`, `ops/`).
- Поправки приветствуются — открой issue или пиши `1.n.u` в Discord.
