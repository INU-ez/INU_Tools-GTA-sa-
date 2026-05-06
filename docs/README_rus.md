<div align="center">

![INU Tools Logo](logo.jpg)

# INU_Tools (GTA SA)

**Blender-аддон для моддинга GTA San Andreas — полный пайплайн от моделинга до IMG-архива.**

<p>
  <img src="https://img.shields.io/badge/Blender-2.83%E2%80%935.1-orange?logo=blender" alt="Blender">
  <img src="https://img.shields.io/badge/Version-1.8.0-green" alt="Version">
  <img src="https://img.shields.io/badge/License-GPL--3.0-blue" alt="License">
</p>
<p>
  <img src="https://komarev.com/ghpvc/?username=INU-ez&color=orange&style=flat-square&label=REPO+VIEWS" alt="Views">
  <a href="../../../issues"><img src="https://img.shields.io/github/issues/INU-ez/INU_Tools-GTA-sa-?color=red" alt="Issues"></a>
  <a href="../../../stargazers"><img src="https://img.shields.io/github/stars/INU-ez/INU_Tools-GTA-sa-?style=social" alt="Stars"></a>
</p>

**[🇬🇧 English version](../README.md)** · **[📖 Документация](DOCS_rus.md)** · **[⚖️ Сравнение с Kams / DragonFF](COMPARISON_rus.md)**

</div>

> [!IMPORTANT]
> **Два способа установки — выбирай по своим задачам:**
>
> 🟢 **[Последний релиз](../../../releases/latest)** — рекомендую большинству. Проверено перед публикацией, поведение предсказуемое.
>
> 🟡 **Ветка `main`** (на этой странице `Code → Download ZIP` или `git clone`) — свежие фиксы и фичи в разработке, ещё не попавшие в релиз. Могут быть баги, недопиленный функционал, breaking changes. Все правки с `main` рано или поздно попадают в следующий релиз. Если поймал баг здесь — пожалуйста укажи **«from main»** в issue, чтобы я понимал релизный это репорт или с разработки.

---

## ✨ Главное

<table>
<tr>
<td width="50%" valign="top">

- ⚡ **Производительность** — Import Map ~10×, Export to IMG ~5–15× (параллельный парсинг DFF + batch IMG writer)
- 🎨 **Нативные парсеры** — DFF / COL / TXD / IDE / IPL / IMG / IFP / FXP, без внешних зависимостей
- 🗺️ **Полный round-trip карты** — IMG → Blender → правка DFF + COL + TXD → IMG другой сборки
- 🎆 **Редактор `effects.fxp`** — 82 системы, живая симуляция частиц во viewport
- 🦴 **Skinned DFF + IFP** — импорт педов с 294+ ванильными анимациями
- 🆔 **ID Manager** — multi-preset, sync со сценой, FLA-расширение, детекция конфликтов

</td>
<td width="50%" valign="top">

![2DFX tutorial](gif/cj-explosion.gif)

</td>
</tr>
</table>

## 🆕 Что нового в 1.8.0

Релиз с **двумя параллельными сборками**, новой системой Validate Scene, превью Modulate Color по `timecyc.dat` и пачкой багфиксов после глубокого Blender API audit'а. Поддержка Blender'а расширена до **2.83 → 5.1** через `tools/compat.py`. Полная backward-совместимость с .blend / .dff / .ipl / .ide из 1.7.x.

**Две сборки, один исходник:**

- 🟢 **`inu_tools_gta_sa-1.8.0-full.zip`** — полная версия, без ограничений. GPU NVTT compression (10–100× быстрее на больших атласах), полный multi-threading импорта/экспорта, все фичи доступны. **Рекомендуется большинству пользователей.** Установка через `Edit → Preferences → Add-ons → Install from Disk`.
- 🟡 **`inu_tools_gta_sa-1.8.0.zip`** — store-версия, она же публикуется на extensions.blender.org. Без NVTT (CPU DXT), без `subprocess` вне small allowlist, ToS-compliant запись данных (per-user config dir). Медленнее, но удобно если хочется именно через официальный сайт расширений Blender. **Требует Blender 4.2+** (extension API floor).

**Главное** — Validate Scene (единый pre-export sweep) · Modulate Color preview (Day / Night `ambient_obj` из `timecyc.dat`) · авто-линковка alpha после TXD-импорта · поддержка DXT2 / DXT4 fourcc (vanilla SA fence-текстуры теперь декодируются корректно) · FLA IPL (Fastman92 Limit Adjuster) · DFF auto-naming с суффиксом `_DFF` · DFF export ~×2 быстрее на тяжёлых мешах · multi-mesh OBJS в IDE парсере · IplOccl канонические имена полей · Blender 2.83 → 5.1 через `tools/compat.py`.

**Багфиксы** — DFF import NameError (восстановлен `start = r.pos`) · unregister NameError (`_links_draw_handler`) · console spam от workspace_cycle · enum cache flicker · jerky playback IFP-экспорта (`bl_quat.normalize()`) · IK rig на rest-pose peds · понятные лимиты DFF / COL с именем модели и счётчиком · `_save_paths` / `_load_paths` (миграция PropertyGroup — пути теперь сохраняются между сессиями) · 35+ leftover-ов `scene.gtatools_*` мигрированы на `scene.inu_settings.gtatools_*`.

**Внутри** — PropertyGroup consolidation (`scene_settings.py`) · `bpy.utils.extension_path_user` для пользовательских данных · 10 end-to-end тестов внутри headless Blender · static compliance guards (AST scan, manifest hygiene) · CI matrix билдит и валидирует обе сборки на каждый push.

→ **[Полные release notes на GitHub](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v1.8.0)**

<details>
<summary>Более старые релизы</summary>

- **v1.7.0** — IK Rig для SA-педов (FK→IK bake, brute-force pole-калибровка, INU_Ground floor limiter), Animated Map Object workflow (одной кнопкой DFF+IFP+IDE для мельниц/кранов), Frame Hierarchy Editor с vanilla VEHICLE/PED шаблонами, Vehicle Paintjob (Pay'n'Spray альт-текстуры), Profile system (кастомные наборы N-sidebar панелей), большой рефакторинг: монолитный `__init__.py` (16k строк) разбит на 22 модуля `ops/*.py` — [страница релиза](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v1.7.0)

- **v1.6.7** — полный round-trip Map Import → правка → Map Export с сохранением IDE / IPL / COL / TXD-лейаута (CRLF, IPL inst dedup, согласованность ID для `.NNN` дубликатов), модальный экспорт с progress-bar'ом, свойства `inu.col_name` + `inu.lod_object`, Group-by-IPL импорт + By-collection split-режим, парность main ↔ LOD, TXD-bucketing по `txd_name`, per-DFF COL по умолчанию, модальный ESC cancel, multi-collection picker, NVTT auto + параллельный DXT1, отдельная Vehicles панель — [страница релиза](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v1.6.7)
- **v1.6.6-beta** — частичный pre-release с первым набором 1.6.6: Map auto-split (XY-сетка), damage variants, train paths verified, COL ~5×, VC Layer System (BETA), IFP ANP2 / ANPK write, Bitmaps Manager unused cleanup. Заменён на v1.6.7 (round-trip preservation, modal export, format-conformance фиксы) — [страница релиза](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v1.6.6-beta)
- **v1.6.5-beta** — релиз о производительности map-workflow: Import Map ~10× / Export to IMG ~5–15× быстрее, тумблеры Load COL + Shared TXD, Skip 2DFX по умолчанию, ID Manager дыры/фантомы + multi-preset, UI pipeline реорганизация (Этапы 1-6) + панель *INU Tools: Model* в Object Properties, Material Presets в `INU_Preset/`, прогресс-бары (Build Map / Export to IMG / Extract Resources), опциональный Профайлер — см. [страницу релиза](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v1.6.5-beta)
- **v1.6.4** — Experimental: Map Export (сцена→IPL+IDE+COL+TXD одной кнопкой), Binary IPL Write, CST IO, UV-анимация в DFF, Breakable Objects, IFP Batch Import, GTA Material Panel, Bitmaps Manager, Station Markers, Roadblocks & Traffic Lights, FLA4 Path Format, Vehicle Scale Helper
- **v1.6.3** — Particle Effects (редактор effects.fxp), Object Properties *GTA SA: IDE / IPL* панель, LightMap UV2, 2DFX UI (Detach All, список эффектов), ID Manager (Assign from ID…, Extend IDs FLA), Nodes multi-file I/O с разбивкой на 8×8 зон
- **v1.6.1** — IPL Import: COL движется с DFF, Empty-плейсхолдеры; Model Links пунктирные линии; LOD/COL → DFF snap; Drag & Drop TXD
- **v1.6.0** — Import Map полный workflow, BBox Mode, секция IPL ZONE, GPU NVTT авто-определение, Blender 4.2+
- **v1.5.3** — Skinned DFF + IFP анимации, Water IO, Path IO, совместимость с Blender 5.1
- **v1.5.2** — Модульный рефакторинг (tools/ data/), COL Light Preview, Model ID Manager
- **v1.5.1** — IDE/IPL экспорт/импорт, IMG Archive экспорт, Dual Texture / Blend Mode
- **v1.5.0** — Нативные DFF/COL/TXD (без DragonFF), авто-импорт TXD, numpy DXT, package-структура
- **v1.4.x** — UV Editor, Post-Processing VC, Fast Bake, DFF Flags, GPU TXD через NVTT, лимит 50 материалов
- **v1.3.0** — Очистка дубликатов материалов
- **v1.2.x** — Улучшения экспорта (COL3, версия GTA SA, прогресс-бар)
- **v1.1.0** — DFF/COL/LOD/TXD экспорт, суффиксы
- **v1.0.0** — Первый релиз

</details>

<details>
<summary><b>🔧 Совместимость</b></summary>

| | FULL-сборка | STORE-сборка |
|---|---|---|
| **Blender** | 2.83 – 5.1 (рекомендуется 4.2+) | **только 4.2+** (нижняя граница extension API) |
| **GPU TXD-сжатие** | NVIDIA Texture Tools (NVTT) | только CPU-кодек |
| **Дистрибуция** | прямой .zip из GitHub Release | extensions.blender.org / .zip из GitHub |

| | |
|---|---|
| **Игра** | GTA San Andreas (совместим с MTA:SA) |
| **ОС** | Windows / Linux / macOS |
| **Опционально** | NVIDIA GPU + NVIDIA Texture Tools (только в FULL-сборке) |

</details>

<details>
<summary><b>📦 Установка</b></summary>

**Выбери одну из двух сборок** в последнем [GitHub Release](../../../releases/latest):

**🟢 FULL — `inu_tools_gta_sa-X.Y.Z-full.zip`** (рекомендуется)

1. Скачай FULL-zip со страницы релиза
2. Открой Blender → **Edit → Preferences → Add-ons** → ⌄ → **Install from Disk** → выбери zip
3. Включи **INU Tools (GTA SA)**

**🟡 STORE — `inu_tools_gta_sa-X.Y.Z.zip`** (только Blender 4.2+)

Та же версия что публикуется на extensions.blender.org. Два пути установки:

- Прямо с сайта расширений: **Edit → Preferences → Get Extensions** → найди "INU Tools" → Install
- Или скачай STORE-zip из релиза: **Edit → Preferences → Get Extensions** → ⌄ → **Install from Disk**

</details>

<details>
<summary><b>🚀 Быстрый старт</b></summary>

Назови объекты с суффиксами, выдели их и нажми **Export All**:

```
Building01_DFF   ← основной меш
Building01_LOD   ← low-poly LOD
Building01_COL   ← коллизия
```

Аддон автоматически соберёт DFF + LOD + COL + TXD в одну группу и экспортирует в один клик.

</details>

<details>
<summary><b>🧰 Возможности</b></summary>


<details>
<summary><b>&emsp;📤 Экспорт / Импорт</b></summary>

| Фича | Детали |
|---|---|
| 📦 DFF экспорт/импорт | GTA SA v3.6.0.3 |
| 📦 COL экспорт/импорт | формат COL3 |
| 📦 LOD экспорт/импорт | автоматическая привязка к DFF |
| 📦 TXD экспорт/импорт | DXT-сжатие, параллельно, GPU через NVTT |
| 🚀 Export All | массовый экспорт по суффиксам `_DFF` / `_LOD` / `_COL` + авто TXD |
| 🗂️ Экспорт коллекций | активная коллекция, если ничего не выделено |
| 🎨 Drag & Drop TXD | перетащить `.txd` во viewport — материалы создаются сами |
| 🎨 DFF Flags | панель флагов: Normals, Light, Modulate Color, UV1/UV2, Day/Night, BinMesh |

</details>

<details>
<summary><b>&emsp;🗺️ IDE / IPL / IMG</b></summary>

| Фича | Детали |
|---|---|
| 📦 IDE экспорт/импорт | все секции (objs, tobj, anim, cars, peds, weap, hier, txdp), upsert/remove, авто-LOD |
| 📦 IPL экспорт/импорт | все секции (inst, cull, grge, enex, pick, cars, auzo, jump, occl, tcyc, zone) + бинарный IPL (bnry) |
| 🎨 IPL Sections визуализация | cull, garage, enex, pickup, cars, auzo, jump, occl, zone как объекты в Blender |
| 📦 IMG Archive | экспорт/импорт DFF + LOD + TXD + COL в `.img` (VER2) |
| 🗺️ Import Map | извлечение из IMG, сборка `.glb`, авто-сортировка по коллекциям |
| ⚡ BBox Mode | далёкие объекты → Bounding Box, полные модели в радиусе 300м от выделения |
| 🗺️ Регионы карты | автоопределение из `gta.dat` (LA, SF, VEGAS, COUNTRY…) |
| 🆔 Менеджер ID | файл (321–19999), синхронизация сцены, загрузка из игры, поиск + прокрутка |
| 🆔 Назначить ID с номера | 🆕 пропуск занятых ID, старт с любого номера |
| 🆔 Расширить ID (FLA) | 🆕 расширение диапазона для Fastman Limit Adjuster |
| 🎨 IDE Флаги | 15 чекбоксов (IS_ROAD, IS_TREE, DRAW_LAST…) |
| ⚙️ Суффиксы/префиксы | `_DFF`, `_LOD`, `_COL`, `LOD` и т.д. |
| 🔗 Model Links | визуализация связей DFF↔LOD↔COL пунктиром |
| 🗑️ Remove from IMG | удаление DFF/COL/TXD по типу выделенного объекта |
| 🔍 IMG File List | прокручиваемый UIList с поиском |
| 🔄 Replace Empty | замена IPL-плейсхолдеров моделями сцены |
| 🗺️ X Radar Maker | тайлы миникарты (8×8, меню, полный радар) + упаковка в TXD |

</details>

<details>
<summary><b>&emsp;💡 Prelight</b></summary>

| Фича | Детали |
|---|---|
| 💡 Vertex Colors бейк | Fast / With Shadows |
| 💡 Raycast-тени | через depsgraph |
| 🎨 Fill Colors | покраска полигонов с пипеткой + уровневая система |
| 💡 Scatter Light | рассеивание света с настройками |
| 🌓 День/Ночь | раздельные color-атрибуты |
| 💡 LightMap UV2 | 🆕 кнопки Add/Toggle/Remove, Multiply blend |
| 🔍 Анализ vertex colors | и превью |
| 💡 Prelight COL | vertex colors → COL Day/Night Light |
| 🎨 COL Light Preview | настройки Edge / Threshold / Contrast |
| ⚙️ Prelight Presets | сохранение/загрузка настроек |

<details>
<summary>📹 .gif-туториал</summary>

![COL Light](gif/col_light.gif)

</details>

</details>

<details>
<summary><b>&emsp;🎨 Post-Processing</b></summary>

| Фича | Детали |
|---|---|
| 🎨 Smooth | сглаживание vertex colors между соседними вершинами |
| 🎨 Smooth Between Objects | сглаживание VC на стыках между разными объектами |
| 🎨 Contrast | настройка контраста |
| 🎨 Brightness | настройка яркости |
| 🎨 Gamma | гамма-коррекция |

</details>

<details>
<summary><b>&emsp;🎯 2DFX эффекты</b></summary>

| Фича | Детали |
|---|---|
| 🎆 Создание эффектов | Light, Particle, Ped Attractor, Sun Glare |
| 🔗 Attach/Detach к мешу | координаты пересчитываются на экспорте |
| 🔗 Detach All from Mesh | 🆕 массовое открепление всех 2DFX от выделенного меша |
| 🎨 Список прикреплённых 2DFX | 🆕 в UI меша с кнопками detach |
| ⚙️ Пресеты | Default, OnAllDay, Lamp Post, BB Pickup, Flashing, Train Crossing, Traffic |
| 🎨 Дропдауны текстур | 34 Corona-текстуры, Shadow, Show Mode, Flare Type |
| 📦 2DFX экспорт | RW Light chunk + 2DFX PLG |
| 🎨 Real-time визуализация | и редактирование всех эффектов |

<details>
<summary>📹 .gif-туториал</summary>

![2DFX](gif/2DFX.gif)

</details>

</details>

<details>
<summary><b>&emsp;🎆 Particle Effects (<code>effects.fxp</code>)</b></summary>

> 🆕 **Полностью новая фича в 1.6.3** — редактирование частиц GTA SA прямо в Blender.

| Фича | Детали |
|---|---|
| 📦 Полный парсер | текстовый `effects.fxp`, 82 эффекта |
| ⚡ Симуляция во viewport | 30 FPS, до 64 частиц на эмиттер |
| 🎨 Дропдаун эффектов | выбор из всех систем в `effects.fxp` |
| 🎨 Multi-emitter | переключение эмиттеров внутри одной системы |
| ⚙️ 40+ параметров | цвет (start/mid/end), размер, скорость, направление, физика |
| 💨 Эмиссия | rate, life, speed, direction, angle, volume box, offset |
| 🌍 Физика | гравитация, трение, ветер, шум, джиттер, отскок от земли |
| 📈 Редактор ключей | кривые size/color/alpha по времени жизни |
| 💾 Сохранение | обратно в `effects.fxp` с авто-бэкапом (`.fxp.bak`) |
| ⚙️ Операторы | New / Delete / Switch Emitter / Reload |
| 🎨 Camera-facing billboards | как у Light corona |

</details>

<details>
<summary><b>&emsp;🎨 Материалы</b></summary>

| Фича | Детали |
|---|---|
| 🎨 Environment Map | |
| 🎨 Bump Map | |
| 🎨 Specular | |
| 🎨 UV Animation | |
| 🎨 Reflection Material | |
| 🎨 Dual Texture / Blend Mode | |
| 📦 COL Surface Type | 179 типов GTA SA |
| ⚡ Авто-загрузка текстур | по именам материалов |
| 🎨 Drag & Drop | создание материалов перетаскиванием картинок |
| 🧹 Очистка дубликатов | удаляет `.001`, `.002` |
| 🔤 Сортировка материалов | по имени |

</details>

<details>
<summary><b>&emsp;🧮 UV Editor</b></summary>

| Фича | Детали |
|---|---|
| 🎲 UV Grid Randomizer | рандомизация UV-позиций в ячейках сетки |
| 🎯 Snap to Grid | привязка UV-островов к ближайшей ячейке |
| 📐 9 точек выравнивания | выбор позиции UV внутри ячейки |
| 🔗 Link Polygons | совместное перемещение полигонов с перекрывающимися UV |

<details>
<summary>📹 .gif-туториал</summary>

![Random windows](gif/random_windows.gif)

</details>

</details>

<details>
<summary><b>&emsp;🔍 Check</b></summary>

| Фича | Детали |
|---|---|
| 🔍 Проверка геометрии | свободные вершины, рёбра, N-гоны |
| ⚠️ Лимит материалов | 50 для GTA SA |
| 🧹 Очистка/сортировка материалов | |
| 🎯 LOD/COL → DFF snap | переместить LOD и COL к позиции DFF |
| 👁️ Скрыть DFF/LOD/COL | раздельно |
| ⚠️ Обнаружение конфликтов Model ID | |
| 🔄 Batch Set Type | 🆕 OBJ / COL / SHA / NON с авто-переименованием |
| 🔄 Reset Transform | 🆕 обнулить Location и Rotation |

<details>
<summary>📹 .gif-туториал</summary>

![Check](gif/Check.gif)

</details>

</details>

<details>
<summary><b>&emsp;🌊 Water IO</b></summary>

| Фича | Детали |
|---|---|
| 📦 Импорт/экспорт | `water.dat` |
| 🌊 Текстура waterclear256 | с анимацией течения |
| 🌊 Типы воды | Default / Shallow, Visible / Invisible |
| 🎯 Snap to grid (×4) | сшивка краёв |
| 📦 Экспорт коллекции Water | |

</details>

<details>
<summary><b>&emsp;🛣️ Path IO</b></summary>

| Фича | Детали |
|---|---|
| 📦 paths.ipl | пути машин/педов для `gta.dat` |
| 📦 tracks.dat | железнодорожные пути и станции |
| 📦 NODES.dat | компилированные path nodes, multi-file импорт 🆕 |
| 🛣️ Создание путей | конвертация кривых/рёбер в пути |
| ⚙️ Авто-разбиение | группы по 12 нод |
| 🗺️ NODES экспорт | авто-разбиение по 8×8 зонам карты 🆕 |

</details>

<details>
<summary><b>&emsp;🦴 Персонажи (Skinned DFF)</b></summary>

| Фича | Детали |
|---|---|
| 🦴 Импорт скелета | Armature + веса вершин + матрицы костей |
| 📦 Экспорт skinned DFF | byte-perfect round-trip |
| 🎬 IFP анимации | импорт `ped.ifp` (294+ анимаций), поиск, применение |
| ✅ Совместимость | Kams Script DFF и оригинальные игровые модели |

</details>

<details>
<summary><b>&emsp;🔌 Интеграции</b></summary>

| Интеграция | Назначение |
|---|---|
| [Itera Tools 3](https://itera.gumroad.com/l/IteraTools3) | Vertex Lit Linear / Quickstart |
| LightMap (beta_MTA) | подключение готовой lightmap через MTA-скрипт |
| Pipeline | Building / Reflections |
| Hotkeys | `Shift+T`, `Shift+A` |
| Локализация | RU / EN |

</details>

</details>

<details>
<summary><b>🧭 Панели UI</b></summary>

| Расположение | Панель | Что там |
|---|---|---|
| `Properties > Scene` | **INU Tools** | IDE/IPL/IMG пути, текстуры, NVTT, файлы IMG |
| `Properties > Object` | **INU Tools: Model** 🆕 | Тип (auto+manual), Model ID, TXD, Draw Dist, IDE Flags, DFF Flags, Pipeline, Breakable, 2DFX |
| `Properties > Material` | **GTA SA Material Effects** | Environment Map, Bump Map, Reflection, Specular, UV Animation |
| `Properties > Material` | **COL Surface Type** | выбор типа поверхности коллизии |
| `View3D > Sidebar (N)` | **GTA Tools** | пайплайн SETUP → MODEL → DATA → EXPORT (Export сверху, ID Manager, Object IDE/IPL, все остальные подпанели) |
| `UV Editor > Sidebar (N)` | **GTA Tools** | UV-инструменты |

</details>

<details>
<summary><b>⌨️ Горячие клавиши</b></summary>

| Клавиша | Действие |
|---|---|
| `Shift+T` | Открыть / закрыть UV Editor |
| `Shift+A` | GTA SA → Army.dff (пед) / Admiral.dff (машина) |

</details>

<details>
<summary><b>📹 Видеоурок</b></summary>

[![IDE/IPL/IMG/Map Tutorial](https://img.youtube.com/vi/Jw_R9QFYxWE/0.jpg)](https://www.youtube.com/watch?v=Jw_R9QFYxWE)

> Экспорт и импорт IDE / IPL / IMG / Map

</details>

## 🙏 Благодарности

Вдохновлено и частично совместимо с:

- **[DragonFF](https://github.com/Parik27/DragonFF)** (Parik, GPL-3.0) — Blender-аддон для форматов RenderWare. INU_tools использует совместимые имена свойств материалов и объектов для удобного перехода между аддонами.
- **[RenderWare](https://en.wikipedia.org/wiki/RenderWare)** — игровой движок GTA SA, документация форматов DFF/COL/TXD.

### 🔧 Рекомендуемые сопутствующие инструменты

- **[Itera Tools 3](https://itera.gumroad.com/l/IteraTools3)** — Blender-аддон для vertex lighting. В INU_tools есть отдельная подпанель **Itera Tools 3** (внутри контейнера *Освещение*): авто-определяет Itera в Asset Libraries и применяет его пресеты `Vertex Lit Linear` / `Quickstart` к выделению (плюс `Убрать Itera` одной кнопкой — восстанавливает оригинальные материалы).
- **[NVIDIA Texture Tools](https://developer.nvidia.com/texture-tools-exporter)** — отдельный CLI/GUI для GPU-сжатия DXT. Опционально, но рекомендуется: установи и пропиши путь в `Scene → INU Tools → NVTT Path` — экспорт TXD будет использовать GPU-кодирование (параллельный DXT1, заметно быстрее встроенного CPU-кодера).

### Автор

**INU** — автор аддона (Discord: `1.n.u`)
https://discord.gg/sqtGAVTGdy

### Лицензия

[GPL-3.0](LICENSE)
