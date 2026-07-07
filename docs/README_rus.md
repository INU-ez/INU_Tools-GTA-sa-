<div align="center">

![INU Tools Logo](logo.jpg)

# INU_Tools (GTA SA)

**Blender-аддон для моддинга GTA San Andreas — полный пайплайн от моделинга до IMG-архива.**

<p>
  <img src="https://img.shields.io/badge/Blender-2.83%E2%80%935.1-orange?logo=blender" alt="Blender">
  <img src="https://img.shields.io/badge/Version-2.2.0-green" alt="Version">
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

## 🆕 Что нового в 2.2.0

- 🔥 **LightMap-бейк** — запекает полный GI прямо со сцены (реальные лампы/солнце/world, без внутреннего свето-рига) поверх diffuse. **«Применить LightMap»** в 3 режима: оставить слоем в стеке / запечь в diffuse одной ванильной SA-текстурой / записать в вершинный прелайт Day. Плюс **«Показать поверх базы (UV2)»**, **денойз** всех шумных карт (OIDN на Blender 4.x / numpy-fallback на 5.x) и линейный композит — «Сохранить как» теперь совпадает с игрой
- 🗺️ **IDE/IPL умнее** — чекбокс **«Также в IDE/IPL»** при экспорте; авто-запись `lod_index`; блок при `Model ID = 0`; трансляция флагов между играми; FLA `realInterior` (12-я колонка); при добавлении побеждает файл, выбранный в панели
- 📦 **Rebuild IMG (компакт)** — освобождает «мёртвое» место в архиве после повторных экспортов; блок при имени записи > 24 символов
- 🔍 **Авто-детект типа модели** (DFF / LOD / COL, LOD без учёта регистра) — суффиксы `_DFF/_LOD/_COL` теперь только ручной override
- ✨ **2DFX** — **«Применить к выделенным»** (настройки одного эффекта на всю группу пустышек), привязка нескольких сразу, тумблер линий связи, авто-ребилд превью при `Shift+D` / `Ctrl+C+V`; настройки эффекта переехали в свойства пустышки
- 🎞️ **UV-анимация × Night** — найдена причина, почему анимация не играет в retail-сингле: **ночные вершинные цвета** глушат UV-аним. Предупреждение прямо в DFF Flags + в проверке перед экспортом
- 🆔 **ID Manager** — тумблер **«Пропускать занятые ID»** (строго с указанного номера или с пропуском занятых)
- 🧹 **Чистка + готовность к Blender Extensions** — убраны NVTT/nvcompress (чистый numpy-DXT) и мёртвый код (нерабочие JSON-пресеты материала, скрытые панели); манифест обновлён под правила extensions.blender.org

→ [Release notes 2.2.0](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v2.2.0) · [2.1.0](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v2.1.0) · [2.0.0](https://github.com/INU-ez/INU_Tools-GTA-sa-/releases/tag/v2.0.0) · [История версий](../../../releases)

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
- 💡 **Запекание Prelight** — Day/Night vcols, raycast-тени, scatter, листва, **Резак света** (лужи света под фонарями), заливка, превью вертекс-альфы, LightMap UV2, Modulate Color preview
- 🎯 **2DFX** — Light / Particle / Ped Attractor / Sun Glare с пресетами и attach/detach
- 🎨 **Материалы** — Env Map, Bump, Specular, Reflection, UV Animation, Dual Texture, COL Surface
- 🦴 **Skinned DFF + IK Rig** — арматура, веса, FK→IK bake для педов, **Frame Hierarchy Editor** с vanilla VEHICLE/PED шаблонами, byte-perfect round-trip
- 🎬 **Animated Map Object** — мастер одной кнопкой собирает DFF + IFP + IDE для анимированных объектов (мельницы, краны, двери)
- 🚗 **Vehicle Paintjob** — поддержка альт-текстур Pay'n'Spray (`<base>_paintjob1/2`) с валидацией парности
- ✅ **Validate Scene** — единый pre-export проход (кватернионы, флаги, парность damage/paintjob)
- 🔍 **File Scanner** — линт DFF/COL/TXD из папки на crash-prone паттерны (превышение лимитов, битые refs)
- 🗺️ **X Radar Maker** — генерация тайлов миникарты (8×8 / меню / полный радар) с упаковкой в TXD
- 🧩 **Profile System** — кастомные раскладки N-sidebar (видимость / порядок панелей) в JSON, переключение между задачами
- 🔍 **Авто-детект типа модели** — DFF / LOD / COL определяются автоматически (LOD по токену «lod» без учёта регистра, COL по тегу/отсутствию текстур); суффиксы `_DFF/_LOD/_COL` работают как ручной override
- 📁 **Папка пресетов** — направить все пресеты/данные (профили, пресеты ID, дефолты флагов пайплайна) в любую папку; при смене существующие пресеты копируются

## 🧭 Панели UI

| Расположение | Панель | Что там |
|---|---|---|
| `Properties > Scene` | **INU Tools** | IDE/IPL/IMG пути, текстуры, файлы IMG, папка пресетов |
| `Properties > Object` | **INU Tools: Model** | Тип (auto+manual), Model ID, TXD, Draw Dist, IDE Flags, DFF Flags, Pipeline, Breakable, 2DFX |
| `Properties > Material` | **GTA Material** (2 вкладки) | SURFACE — тип поверхности коллизии · EFFECTS — Env Map, Bump, Reflection, Specular, UV Animation + быстрые пресеты (Стекло/Хром/Краска/Сброс) |
| `View3D > Sidebar (N)` | **GTA Tools** | пайплайн SETUP → MODEL → DATA → EXPORT (Export сверху, ID Manager, Object IDE/IPL, все остальные подпанели) |
| `UV Editor > Sidebar (N)` | **GTA Tools** | UV-инструменты |

## ⌨️ Горячие клавиши

| Клавиша | Действие |
|---|---|
| `Shift+T` | Открыть / закрыть UV Editor |

## 📹 Видеоурок

→ [Экспорт и импорт IDE / IPL / IMG / Map](https://www.youtube.com/watch?v=Jw_R9QFYxWE)

## 📦 Установка

**Blender Extensions (Blender 4.2+):** ставь с [extensions.blender.org](https://extensions.blender.org) (Get Extensions → найди "INU Tools"), либо **Edit → Preferences → Get Extensions → Install from Disk…** с релизным `.zip`.

**Вручную (Blender 2.83+):**
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
