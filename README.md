![image alt](https://github.com/INU-ez/INU_Tools-GTA-sa-/blob/5e82d62dd40105c557ef9cb6be261bb70b63d3a2/logo.jpg)

# INU_Tools (GTA SA)

![Blender](https://img.shields.io/badge/Blender-5.1+-orange?logo=blender)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)
![Version](https://img.shields.io/badge/Version-1.5.1-green)

> **[English version](README_eng.md)**

INU_Tools — Blender аддон для работы с моделями GTA San Andreas.
Предоставляет инструменты экспорта, прелайтинга и подготовки 3D моделей.
Начиная с v1.5.0 аддон имеет собственный экспорт DFF, COL и TXD (без зависимости от DragonFF).

## Возможности

<details>
<summary><b>IDE / IPL / IMG</b></summary>

> - ✅ IDE экспорт/импорт — определение моделей, upsert/remove в существующие файлы
> - ✅ IPL экспорт/импорт — размещение объектов на карте
> - ✅ IMG Archive — экспорт DFF+TXD+COL прямо в .img архив (VER2)

</details>

<details>
<summary><b>Export/Import</b></summary>

> - ✅ DFF экспорт/импорт (GTA SA v3.6.0.3)
> - ✅ COL экспорт/импорт (формат COL3)
> - ✅ LOD экспорт/импорт
> - ✅ TXD экспорт/импорт (DXT сжатие, параллельная обработка, GPU через NVIDIA Texture Tools)
> - ✅ Export All — массовый экспорт по суффиксам `_DFF` / `_LOD` / `_COL` + автосборка TXD

</details>

<details>
<summary><b>Support Itera Tools 3</b></summary>

> - ✅ Применение Itera материалов (Vertex Lit Linear / Quickstart) из панели аддона
> - ✅ Удаление Itera материалов и восстановление оригинальных
> - ✅ Автопоиск библиотеки Itera Tools 3 в Asset Libraries
>
> </details>

</details>

<details>
<summary><b>Prelight</b></summary>

> - ✅ Запекание Vertex Colors (Fast / With Shadows)
> - ✅ Raycast тени через depsgraph
> - ✅ Fill Colors — покраска полигонов с пипеткой и системой уровней
> - ✅ Scatter Light — рассеивание света с настраиваемыми параметрами
> - ✅ Day/Night — раздельные атрибуты цвета для дня и ночи
> - ✅ Анализ и предпросмотр вертексных цветов
> - ✅ Prelight COL — конвертация vertex colors в COL Day/Night Light (авторазбиение материалов по яркости)
> - ✅ Превью COL Light — визуализация освещения на полигонах с настройками Край/Контраст и числовыми значениями
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Itera_Inu_tools](gif/col_light.gif)
>
> </details>

</details>

<details>
<summary><b>2DFX Effects</b></summary>

> - ✅ Создание 2DFX эффектов (Light, Particle, Ped Attractor, Sun Glare)
> - ✅ Привязка/отвязка 2DFX к мешу (Attach/Detach) — координаты автоматически пересчитываются относительно меша при экспорте
> - ✅ Пресеты: Default, OnAllDay, Lamp Post, Lamp Post Coast, BB Pickup, Flashing варианты, Train Crossing, Traffic
> - ✅ Выпадающие списки для Corona Texture (34 текстуры), Shadow Texture, Show Mode, Flare Type
> - ✅ Show Mode — режимы отображения (Default, Random Flashing, Flash Rain, Only Rain, No Rain, Flash 5)
> - ✅ Экспорт 2DFX в DFF (RW Light chunk + 2DFX PLG) — совместимость с MTA SA / GTA SA
> - ✅ Визуализация всех эффектов и их редактирование в реальном времени
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Itera_Inu_tools](gif/2DFX.gif)
>
> </details>

</details>

<details>
<summary><b>Post-Processing</b></summary>

> - ✅ Smooth — сглаживание vertex colors между соседними вершинами
> - ✅ Contrast — настройка контраста
> - ✅ Brightness — настройка яркости
> - ✅ Gamma — гамма-коррекция

</details>

<details>
<summary><b>UV Editor</b></summary>

> - ✅ UV Grid Randomizer — рандомизация позиций UV в ячейках сетки
> - ✅ Snap to Grid — привязка UV островов к ближайшей ячейке
> - ✅ 9 точек выравнивания — выбор позиции UV в ячейке
> - ✅ Связать полигоны — перемещение полигонов с пересекающимися UV вместе
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![random_windows](gif/random_windows.gif)
>
> </details>

</details>

<details>
<summary><b>Geometry & Materials</b></summary>

> - ✅ Проверка геометрии — висящие вершины, рёбра, N-gons
> - ✅ Очистка геометрии — удаление проблемных элементов
> - ✅ Проверка лимита материалов (50 для GTA SA)
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Check](gif/Check.gif)
>
> </details>

> - ✅ Автозагрузка текстур по именам материалов
> - ✅ Drag & Drop — создание материалов перетаскиванием изображений
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![add_material](gif/add_material.gif)
>
> </details>

> - ✅ Очистка дубликатов материалов (.001, .002)
> - ✅ Сортировка материалов по имени
>
> <details>
> <summary><b>Tutorial</b></summary>
>
> ![material_sorting](gif/material_sorting.jpg)
>
> </details>

</details>

<details>
<summary><b>Lightmap Generator</b></summary>

> - ✅ Генерация кода для MTA-скрипта
> - ✅ Копирование настроек лайтмапа между объектами
> - ✅ Настройка V-offset для выравнивания текстур

Ссылка на файл скрипта для MTA лежит в Issues.

</details>

## Установка

1. Скачайте папку `INU_tools/` (или zip-архив)
2. Поместите папку `INU_tools/` в `Blender/5.1/scripts/addons/`
3. Blender → Edit → Preferences → Add-ons → включите "INU_tools(gta_sa)"

## Использование

Аддон добавляет панели в:
- **Properties > Scene > INU Tools** — текстуры, NVTT настройки
- **Properties > Object > GTA SA Object** — тип объекта (OBJ/COL/SHA/2DFX), DFF Flags, Pipeline, UV Maps
- **Properties > Material > GTA SA Material Effects** — Environment Map, Bump Map, Reflection, Specular, UV Animation
- **Properties > Material > COL Surface Type** — выбор типа поверхности коллизии
- **View3D > Sidebar (N) > GTA Tools** — экспорт/импорт, прелайт, 2DFX, vertex paint
- **UV Editor > Sidebar (N) > GTA Tools** — UV инструменты

<details>
<summary><b>Горячие клавиши</b></summary>

> | Клавиша | Действие |
> |---------|----------|
> | `Shift+T` | Открыть / закрыть UV Editor |
> | `Shift+A` | Gta sa->Army.dff(ped)/Admiral.dff(car)|

</details>

#### Быстрый экспорт

Назовите объекты с суффиксами (`Model_DFF`, `Model_LOD`, `Model_COL`), выделите и нажмите **Export All**.

## Требования

- **Blender 5.1+**
- NVIDIA Texture Tools — опционально, для GPU сжатия текстур
- Itera Tools 3 — опционально, для vertex lighting (https://itera.gumroad.com/l/IteraTools3)

<details>
<summary><b>История изменений</b></summary>

- **v1.5.1** — IDE/IPL экспорт/импорт (upsert/remove в существующие файлы); IMG Archive экспорт (DFF+TXD+COL в .img); Dual Texture и Blend Mode; удалён Vertex Alpha (не поддерживается GTA SA)
- **v1.5.0** — Собственный DFF/COL/TXD импорт и экспорт (без DragonFF); авто-импорт TXD при импорте DFF; numpy DXT декомпрессия; сортировка материалов по имени; аддон переведён в пакетную структуру (`INU_tools/`); исправлены prelight preview при экспорте; совместимость с Blender 5.1
- **v1.4.8** — Shift+T Раскрытие UV редактора
- **v1.4.7** — COL Surface Type с группировкой по 13 категориям; Day/Night Light + Brightness в Material Properties; Prelight COL — конвертация vertex colors в COL Light с авторазбиением материалов по яркости (0-15)
- **v1.4.6** — Post-Processing vertex colors (Smooth, Contrast, Brightness, Gamma); Fast Bake с тенями (raycast); панель DFF Flags
- **v1.4.5** — Export All: массовый экспорт нескольких групп; Lightmap Generator возвращён в интерфейс
- **v1.4.4** — Fill Colors, Scatter Light, Drag-and-Drop текстур, панель перемещена в Properties > Scene
- **v1.4.3** — Исправлена прозрачность DXT3; пропуск текстур не кратных 4
- **v1.4.2** — GPU режим TXD через NVIDIA Texture Tools
- **v1.4.1** — Параллельная обработка TXD (до 8x быстрее)
- **v1.4.0** — UV Editor панель, Snap to Grid, привязка полигонов, лимит 50 материалов
- **v1.3.0** — Очистка дубликатов материалов
- **v1.2.x** — Серия улучшений экспорта (COL3, версия GTA SA, прогресс-бар, авто-Collision Object)
- **v1.1.0** — Экспорт DFF/COL/LOD/TXD, определение по суффиксам
- **v1.0.0** — Начальная версия

</details>

<details>
<summary><b>Таблица функций</b></summary>

| Функция | Статус |
|---------|:------:|
| **Форматы** | |
| DFF Import/Export | ✅ |
| COL Import/Export (COL3) | ✅ |
| TXD Import/Export (DXT, GPU NVTT) | ✅ |
| LOD Import/Export | ✅ |
| Export All (batch по суффиксам) | ✅ |
| Embedded COL в DFF | ✅ |
| Автозагрузка текстур по именам | ✅ |
| IFP (анимации) | ❌ |
| IPL/IDE (размещение на карте) | ✅ |
| IMG Archive | ✅ |
| Skinned Mesh (полный скелет) | ❌ |
| **Материалы** | |
| Environment Map | ✅ |
| Bump Map | ✅ |
| Specular | ✅ |
| UV Animation | ✅ |
| Reflection Material | ✅ |
| Dual Texture | ✅ |
| Blend Mode (Src/Dst) | ✅ |
| **2DFX** | |
| Light (превью + 11 пресетов) | ✅ |
| Particle | ✅ |
| Ped Attractor | ✅ |
| Sun Glare | ✅ |
| Road Sign | ❌ |
| Escalator | ❌ |
| Cover Point / EnterExit | ❌ |
| **Освещение (Prelight)** | |
| Vertex Colors Bake (Fast / Shadows) | ✅ |
| Raycast тени | ✅ |
| Fill Colors (пипетка + уровни) | ✅ |
| Scatter Light | ✅ |
| Day/Night атрибуты | ✅ |
| Post-Processing (Smooth/Contrast/Gamma) | ✅ |
| COL Light Bake | ✅ |
| COL Light Preview (Край/Контраст) | ✅ |
| Day↔Night копирование | ❌ |
| VC Smooth между объектами | ❌ |
| **Инструменты** | |
| UV Grid Randomizer / Snap | ✅ |
| Проверка/очистка геометрии | ✅ |
| Очистка/сортировка материалов | ✅ |
| Drag & Drop текстуры | ✅ |
| Itera Tools 3 интеграция | ✅ |
| Lightmap Generator (MTA) | ✅ |
| COL Surface Type (179 типов) | ✅ |
| Горячие клавиши (Shift+T/A) | ✅ |
| DFF Flags панель | ✅ |
| Pipeline (Building/Reflections) | ✅ |
| Bitmap Manager | ❌ |
| Water IO | ❌ |
| CULL Zones | ❌ |
| Object Explode (разрезка мешей) | ❌ |
| Vehicle Tools | ❌ |

</details>

## Благодарности

Проект вдохновлён и частично совместим с:

- **[DragonFF](https://github.com/Parik27/DragonFF)** (Parik, GPL-3.0) — Blender аддон для RenderWare форматов. INU_tools использует совместимые имена свойств материалов и объектов для удобства перехода между аддонами.
- **[RenderWare](https://en.wikipedia.org/wiki/RenderWare)** — игровой движок GTA SA, документация форматов DFF/COL/TXD.

#### Авторы

- **INU** — автор аддона (Discord: 1.n.u)

#### Лицензия

[GPL-3.0](LICENSE)



