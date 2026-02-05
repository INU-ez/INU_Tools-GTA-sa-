![image alt](https://github.com/INU-ez/INU_Tools-GTA-sa-/blob/5e82d62dd40105c557ef9cb6be261bb70b63d3a2/logo.jpg)

# INU_Tools (GTA SA)

![Blender](https://img.shields.io/badge/Blender-4.4+-orange?logo=blender)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)
![Version](https://img.shields.io/badge/Version-1.4.6-green)

INU_Tools — аддон для Blender для работы с моделями GTA San Andreas.
Предоставляет инструменты экспорта, прелайтинга и подготовки 3D моделей.

Для работы экспорта требуется аддон [DragonFF](https://github.com/Parik27/DragonFF).

## Возможности

<details>
<summary><b>Export</b></summary>

- ✅ DFF экспорт (GTA SA v3.6.0.3)
- ✅ COL экспорт (формат COL3)
- ✅ LOD экспорт
- ✅ TXD экспорт (DXT сжатие, параллельная обработка, GPU через NVIDIA Texture Tools)
- ✅ Export All — массовый экспорт по суффиксам `_DFF` / `_LOD` / `_COL` + автосборка TXD
- ✅ DFF Flags — панель настроек геометрии DragonFF (Light, Normals, Pipeline, UV Maps)

</details>

<details>
<summary><b>Prelight</b></summary>

- ✅ Запекание Vertex Colors (Fast / With Shadows)
- ✅ Raycast тени через depsgraph
- ✅ Fill Colors — покраска полигонов с пипеткой и системой уровней
- ✅ Scatter Light — рассеивание света с настраиваемыми параметрами
- ✅ Day/Night — раздельные атрибуты цвета для дня и ночи
- ✅ Анализ и предпросмотр вертексных цветов

</details>

<details>
<summary><b>Post-Processing</b></summary>

- ✅ Smooth — сглаживание vertex colors между соседними вершинами
- ✅ Contrast — настройка контраста
- ✅ Brightness — настройка яркости
- ✅ Gamma — гамма-коррекция

</details>

<details>
<summary><b>UV Editor</b></summary>

- ✅ UV Grid Randomizer — рандомизация позиций UV в ячейках сетки
- ✅ Snap to Grid — привязка UV островов к ближайшей ячейке
- ✅ 9 точек выравнивания — выбор позиции UV в ячейке
- ✅ Связать полигоны — перемещение полигонов с пересекающимися UV вместе

</details>

<details>
<summary><b>Geometry & Materials</b></summary>

- ✅ Проверка геометрии — висящие вершины, рёбра, N-gons
- ✅ Очистка геометрии — удаление проблемных элементов
- ✅ Проверка лимита материалов (50 для GTA SA)
![Image](https://github.com/user-attachments/assets/832d41df-81ae-4af5-8223-59d3f448b771)
- ✅ Автозагрузка текстур по именам материалов
- ✅ Очистка дубликатов материалов (.001, .002)
- ✅ Drag & Drop — создание материалов перетаскиванием изображений

</details>

<details>
<summary><b>Lightmap Generator</b></summary>

- ✅ Генерация кода для MTA-скрипта
- ✅ Копирование настроек лайтмапа между объектами
- ✅ Настройка V-offset для выравнивания текстур

Ссылка на файл скрипта для MTA лежит в Issues.

</details>

## Установка

1. Скачайте `INU_tools(gta_sa).py`
2. Blender → Edit → Preferences → Add-ons → Install → выберите файл
3. Включите "INU_tools(gta_sa)" в списке аддонов

## Использование

Аддон добавляет панели в:
- **Properties > Scene > INU Tools** — экспорт, текстуры, материалы
- **View3D > Sidebar (N) > GTA Tools** — геометрия, прелайт, DFF Flags
- **UV Editor > Sidebar (N) > GTA Tools** — UV инструменты

#### Быстрый экспорт

Назовите объекты с суффиксами (`Model_DFF`, `Model_LOD`, `Model_COL`), выделите и нажмите **Export All**.

## Требования

- **Blender 4.4+**
- **[DragonFF](https://github.com/Parik27/DragonFF)** — обязателен для DFF/COL экспорта
- NVIDIA Texture Tools — опционально, для GPU сжатия текстур

<details>
<summary><b>История изменений</b></summary>

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
- [DragonFF](https://github.com/Parik27/DragonFF) — Parik27

#### Лицензия

[GPL-3.0](LICENSE)
