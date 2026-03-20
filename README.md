![image alt](https://github.com/INU-ez/INU_Tools-GTA-sa-/blob/5e82d62dd40105c557ef9cb6be261bb70b63d3a2/logo.jpg)

# INU_Tools (GTA SA)

![Blender](https://img.shields.io/badge/Blender-5.1+-orange?logo=blender)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)
![Version](https://img.shields.io/badge/Version-1.5.0-green)

INU_Tools — Blender аддон для работы с моделями GTA San Andreas.
Предоставляет инструменты экспорта, прелайтинга и подготовки 3D моделей.
Начиная с v1.5.0 аддон имеет собственный экспорт DFF, COL и TXD (без зависимости от DragonFF).

## Возможности

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

> - ✅ Функция сохранения материалов на модели для Itera
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Itera_Inu_tools](gif/Itera_Inu_tools.gif)
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
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Itera_Inu_tools](gif/col_light.gif)
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
- **Properties > Scene > INU Tools** — экспорт, текстуры, материалы
- **View3D > Sidebar (N) > GTA Tools** — геометрия, прелайт, DFF Flags
- **Properties > Material > COL Surface Type** — выбор типа поверхности коллизии
- **UV Editor > Sidebar (N) > GTA Tools** — UV инструменты

<details>
<summary><b>Горячие клавиши</b></summary>

> | Клавиша | Действие |
> |---------|----------|
> | `Shift+T` | Открыть / закрыть UV Editor |

</details>

#### Быстрый экспорт

Назовите объекты с суффиксами (`Model_DFF`, `Model_LOD`, `Model_COL`), выделите и нажмите **Export All**.

## Требования

- **Blender 5.1+**
- NVIDIA Texture Tools — опционально, для GPU сжатия текстур
- Itera Tools 3 - (https://itera.gumroad.com/l/IteraTools3)

<details>
<summary><b>История изменений</b></summary>

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

#### Авторы

- **INU** — автор аддона (Discord: 1.n.u)

#### Лицензия

[GPL-3.0](LICENSE)
