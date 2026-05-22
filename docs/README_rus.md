<div align="center">

![INU Tools Logo](logo.jpg)

# INU_Tools (GTA SA)

**Blender-аддон для моддинга GTA San Andreas — полный пайплайн от моделинга до IMG-архива.**

<p>
  <img src="https://img.shields.io/badge/Blender-2.83%E2%80%935.1-orange?logo=blender" alt="Blender">
  <img src="https://img.shields.io/badge/Version-2.0.0-green" alt="Version">
  <img src="https://img.shields.io/badge/License-GPL--3.0-blue" alt="License">
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

## 🔮 В планах

Список идей на будущее. Не всё обязательно дойдёт до релиза — какие-то фичи могут отвалиться при ближайшем рассмотрении (нет смысла / нет приоритета / технически непрактично).

- 💾 **Game Folder Backup** — авто-снапшот `gta3.img` и важных `.ide` перед destructive ops (Map Export, IMG rebuild)
- 🔁 **IPL Mass Replace** — заменить все INST с model X на model Y по координатам / радиусу / тегу
- 🎬 **IFP Library Viewer** — превью любой из 294 анимаций на временном armature без создания ped'а
- 🎆 **Auto-LOD generation** — при отсутствии парного `_L0` Map Export генерит decimate-копию автоматически (по примеру EMAPTool)

## 🆕 Что нового в 2.0.0

- 🪟 **Floater окна** — 5 свободно-плавающих GPU-окон для частых операций без скролла N-панели: **Info / Import-Export / Validation / Lighting / IDE-IPL-IMG**. SDF-шейдеры, своё AA, тема-адаптивная палитра, drag/resize/collapse/dock между workspace'ами. Кликабельная иконка в шапке каждой панели открывает соответствующий floater.
- 🌐 **Поддержка GTA III / VC / SA** — авто-детект игры по содержимому файла, отдельные таблицы IDE flags / surface IDs / ped masks для каждой игры, корректное чтение/запись III/VC форматов IMG / DFF / COL / IPL / IDE
- 🔍 **Game Validator** — кросс-файловые проверки IDE/IPL: пропущенные ссылки, дубликаты ID, конфликты, IMG-cross-check. Sub-panel «Анализ карты» с группировкой Critical / Warning / Info
- 🧪 **Lint Profiles** — переключатель **STANDARD / FLA / STRICT / LENIENT** для File Scanner и Game Validator (FLA-сборки имеют другие лимиты, LENIENT для legacy-проектов)
- 🖼️ **Texture Browser** — UIList со всеми текстурами из выбранного источника (IMG/папка/IDE-список), с превью, поиском и cross-ref «где используется»
- 🎬 **Анимированные объекты на эмпти** — переписан animobj-пайплайн, обходит rest_quat баг бонового флоу. IFP экспорт стабильно работает с custom анимациями
- 🛠️ **Light Master** — 5 lighting-панелей (Prelight, Prelight COL, Vertex Paint, LightMap, Itera) теперь подпанели одной мастер-панели, collapsible одним кликом
- 🎨 **Material панель унифицирована** — 3 материальные панели (SURFACE / EFFECTS / PIPELINE) объединены в одну с внутренним табом
- 🦴 **IK Rig + IFP фиксы** — bone-based controls с фиксами POSE vs REST, brute-force pole_angle, FK bake on Add, visual_key at union, FLOOR constraint
- 🇪🇸 **Локализация ES** — полный испанский перевод UI (819+ строк)
- 🧱 **Архитектура** — `__init__.py` разбит на 22 ops-модуля (~140 операторов вынесены, −64% размера файла), `ui/registry.py` с zone-based порядком панелей
- 💡 **2DFX** — каждый тип эффекта (Свет / Частица / Ped Attractor / Блик солнца) получил развёрнутые описания. Свободные кнопки IDE/IPL/IMG в floater'е читаются как fused-кластер
- 🐛 **Hotfix'ы из main** — все 14 пост-1.9.0 фиксов включены: col empty, light col day/night, anim object rest_quat, path nodes parser, install extension, particle save и др.

→ [Полные release notes](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v2.0.0) · [История версий](../../../releases)

## 🧰 Возможности

### Поддержка форматов

| Формат | Импорт | Экспорт | Правка | Что это |
|---|:---:|:---:|:---:|---|
| **DFF** | ✅ | ✅ | ✅ | 3D-модель RenderWare (геометрия, скиннинг, материалы, 2DFX, флаги) |
| **COL** | ✅ | ✅ | ✅ | Коллизия (COL3, 179 surface types) |
| **TXD** | ✅ | ✅ | ✅ | Текстуры (DXT1/DXT5, параллельно, pure numpy, drag&drop) |
| **IDE** | ✅ | ✅ | ✅ | Определения объектов (objs/tobj/anim/cars/peds/weap/hier/txdp) |
| **IPL** | ✅ | ✅ | ✅ | Размещение объектов (текстовый + binary, 11 секций, FLA) |
| **IMG** | ✅ | ✅ | ✅ | Архив ресурсов (VER2) — DFF + LOD + COL + TXD |
| **IFP** | ✅ | ✅ | ✅ | Анимации (294+ ванильных, batch import, ANP3/ANPK/ANP2) |
| **FXP** (`effects.fxp`) | ✅ | ✅ | ✅ | Частицы — 82 системы, viewport-симуляция, 40+ параметров |
| **CST** | ✅ | ✅ | ✅ | Текстовый формат Steve's COL Editor |
| **water.dat** | ✅ | ✅ | ✅ | Вода: типы, snap, текстура waterclear256 |
| **paths.ipl** / **tracks.dat** / **nodes*.dat** / **flight.dat** | ✅ | ✅ | ✅ | Пути машин/педов, ж/д, скомпилированные path nodes, маршруты полётов |

### Что ещё умеет

- 🗺️ **Полный Map round-trip** — импорт всей карты прямо из игровой папки (IDE + IPL + IMG → Blender), правка, Map Export обратно с сохранением лейаута
- 🆔 **ID Manager** — файл, multi-preset, sync со сценой, загрузка из игры, FLA-расширение, детекция конфликтов
- 💡 **Запекание Prelight** — Day/Night vcols, raycast-тени, scatter, LightMap UV2, Modulate Color preview
- 🎯 **2DFX** — Light / Particle / Ped Attractor / Sun Glare с пресетами и attach/detach
- 🎨 **Материалы** — Env Map, Bump, Specular, Reflection, UV Animation, Dual Texture, COL Surface
- 🦴 **Skinned DFF + IK Rig** — арматура, веса, FK→IK bake для педов, **Frame Hierarchy Editor** с vanilla VEHICLE/PED шаблонами, byte-perfect round-trip
- 🎬 **Animated Map Object** — мастер одной кнопкой собирает DFF + IFP + IDE для анимированных объектов (мельницы, краны, двери)
- 🚗 **Vehicle Paintjob** — поддержка альт-текстур Pay'n'Spray (`<base>_paintjob1/2`) с валидацией парности
- ✅ **Validate Scene** — единый pre-export проход (кватернионы, флаги, парность damage/paintjob)
- 🔍 **File Scanner** — линт DFF/COL/TXD из папки на crash-prone паттерны (превышение лимитов, битые refs)
- 🗺️ **X Radar Maker** — генерация тайлов миникарты (8×8 / меню / полный радар) с упаковкой в TXD
- 🧩 **Profile System** — кастомные раскладки N-sidebar (видимость / порядок панелей) в JSON, переключение между задачами
- 🚀 **Pipeline-суффиксы** — `_DFF` / `_LOD` / `_COL` → Export All / Export to IMG в один клик

## 🧭 Панели UI

| Расположение | Панель | Что там |
|---|---|---|
| `Properties > Scene` | **INU Tools** | IDE/IPL/IMG пути, текстуры, файлы IMG |
| `Properties > Object` | **INU Tools: Model** | Тип (auto+manual), Model ID, TXD, Draw Dist, IDE Flags, DFF Flags, Pipeline, Breakable, 2DFX |
| `Properties > Material` | **GTA Material** (3 вкладки) | SURFACE — тип поверхности коллизии · EFFECTS — Env Map, Bump, Reflection, Specular, UV Animation · PIPELINE |
| `View3D > Sidebar (N)` | **GTA Tools** | пайплайн SETUP → MODEL → DATA → EXPORT (Export сверху, ID Manager, Object IDE/IPL, все остальные подпанели) |
| `UV Editor > Sidebar (N)` | **GTA Tools** | UV-инструменты |

## ⌨️ Горячие клавиши

| Клавиша | Действие |
|---|---|
| `Shift+T` | Открыть / закрыть UV Editor |

В стандартное меню `Shift+A` (Add) добавлен пункт **GTA SA** — быстрая вставка Army.dff (пед) / Admiral.dff (машина).

## 📹 Видеоурок

→ [Экспорт и импорт IDE / IPL / IMG / Map](https://www.youtube.com/watch?v=Jw_R9QFYxWE)

## 📦 Установка

1. Скачай папку `INU_tools/` (или zip-архив)
2. Скопируй её в директорию аддонов Blender:
   ```
   Blender/<version>/scripts/addons/INU_tools/
   ```
3. Открой Blender → **Edit → Preferences → Add-ons** → включи **INU_tools(gta_sa)**

## 🔧 Совместимость

| | |
|---|---|
| **Blender** | 2.83 – 5.1 ✅ (4.2+ для установки через extensions.blender.org) |
| **Игра** | GTA San Andreas (совместим с MTA:SA) |
| **ОС** | Windows / Linux / macOS |

## 🙏 Благодарности

Вдохновлено и частично совместимо с:

- **[DragonFF](https://github.com/Parik27/DragonFF)** (Parik, GPL-3.0) — Blender-аддон для форматов RenderWare. INU_tools использует совместимые имена свойств материалов и объектов для удобного перехода между аддонами.
- **[RenderWare](https://en.wikipedia.org/wiki/RenderWare)** — игровой движок GTA SA, документация форматов DFF/COL/TXD.

### 🔧 Рекомендуемые сопутствующие инструменты

- **[Itera Tools 3](https://itera.gumroad.com/l/IteraTools3)** — Blender-аддон для vertex lighting. В INU_tools есть отдельная подпанель **Itera Tools 3** (внутри контейнера *Освещение*): авто-определяет Itera в Asset Libraries и применяет его пресеты `Vertex Lit Linear` / `Quickstart` к выделению (плюс `Убрать Itera` одной кнопкой — восстанавливает оригинальные материалы).

### Автор

**INU** — автор аддона (Discord: `1.n.u`)
https://discord.gg/sqtGAVTGdy

### Лицензия

[GPL-3.0](LICENSE)
