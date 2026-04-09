![image alt](https://github.com/INU-ez/INU_Tools-GTA-sa-/blob/5e82d62dd40105c557ef9cb6be261bb70b63d3a2/logo.jpg)

# INU_Tools (GTA SA)

![Blender](https://img.shields.io/badge/Blender-4.2+-orange?logo=blender)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)
![Version](https://img.shields.io/badge/Version-1.6.1-green)
![Views](https://komarev.com/ghpvc/?username=INU-ez&color=orange&style=flat-square&label=REPO+VIEWS)

> **[English version](README_eng.md)**

> [!NOTE]
> Аддон в активной разработке. Сообщения об ошибках приветствуются в [Issues](../../issues).

INU_Tools — Blender аддон для работы с моделями GTA San Andreas.
Предоставляет инструменты экспорта, прелайтинга и подготовки 3D моделей.
Начиная с v1.5.0 аддон имеет собственный экспорт DFF, COL и TXD (без зависимости от DragonFF).

## Возможности

<details>
<summary><b>Экспорт / Импорт</b></summary>

> - ✅ DFF экспорт/импорт (GTA SA v3.6.0.3)
> - ✅ COL экспорт/импорт (формат COL3)
> - ✅ LOD экспорт/импорт
> - ✅ TXD экспорт/импорт (DXT сжатие, параллельная обработка, GPU через NVIDIA Texture Tools)
> - ✅ Export All — массовый экспорт по суффиксам `_DFF` / `_LOD` / `_COL` + автосборка TXD
> - ✅ Экспорт коллекций — если ничего не выделено, экспортируются все объекты из активной коллекции
> - ✅ Drag & Drop TXD — перетаскивание .txd файлов во viewport с автосозданием материалов
> - ✅ DFF Flags — сворачиваемая панель флагов геометрии (Normals, Light, Modulate Color, UV1/UV2, Day/Night, BinMesh)

</details>

<details>
<summary><b>IDE / IPL / IMG</b></summary>

> - ✅ IDE экспорт/импорт — все секции (objs, tobj, anim, cars, peds, weap, hier, txdp), upsert/remove, авто-LOD
> - ✅ IPL экспорт/импорт — все секции (inst, cull, grge, enex, pick, cars, auzo, jump, occl, tcyc, zone), binary IPL (bnry)
> - ✅ IPL Sections — визуализация секций (cull, garage, enex, pickup, cars, auzo, jump, occl, zone) как объектов в Blender
> - ✅ IMG Archive — экспорт/импорт DFF+LOD+TXD+COL в .img архив (VER2)
> - ✅ Import Map — извлечение ресурсов из IMG, сборка карты в .glb, импорт с авто-сортировкой по коллекциям
> - ✅ BBox Mode — переключение далёких объектов в Bounding Box, рядом с выделением (300м) — полные модели
> - ✅ Регионы карты — автоопределение из gta.dat (LA, SF, VEGAS, COUNTRY и т.д.)
> - ✅ Менеджер ID — создание файла (321-19999), синхронизация сцены, загрузка из игры, очистка выделенных, поиск и прокрутка
> - ✅ Назначить ID с номера — назначение ID начиная с указанного, с пропуском занятых
> - ✅ Расширить ID (FLA) — расширение диапазона ID для Fastman Limit Adjuster
> - ✅ IDE Флаги — 15 чекбоксов с описаниями (IS_ROAD, IS_TREE, DRAW_LAST и др.)
> - ✅ Настраиваемые суффиксы и префиксы моделей (_DFF, _LOD, _COL, LOD и т.д.)
> - ✅ Model Links — визуализация связей DFF↔LOD↔COL пунктирными линиями
> - ✅ Удалить из IMG — удаление DFF/COL/TXD по типу выделенного объекта
> - ✅ Список файлов IMG — UIList с прокруткой и поиском
> - ✅ Заменить Empty — замена IPL плейсхолдеров на модели из сцены
> - ✅ X Radar Maker — генерация тайлов мини-карты (8x8, меню, полный радар) + упаковка в TXD

</details>

<details>
<summary><b>Prelight</b></summary>

> - ✅ Запекание Vertex Colors (Fast / With Shadows)
> - ✅ Raycast тени через depsgraph
> - ✅ Fill Colors — покраска полигонов с пипеткой и системой уровней
> - ✅ Scatter Light — рассеивание света с настраиваемыми параметрами
> - ✅ Day/Night — раздельные атрибуты цвета для дня и ночи
> - ✅ LightMap UV2 — подключение текстуры лайтмапа на второй UV канал (Multiply)
> - ✅ Анализ и предпросмотр вертексных цветов
> - ✅ Prelight COL — конвертация vertex colors в COL Day/Night Light
> - ✅ Превью COL Light — визуализация с настройками Край/Порог/Контраст
> - ✅ Пресеты прелайта — сохранение/загрузка настроек запекания
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
> - ✅ Smooth между объектами — сглаживание vertex colors на стыках разных объектов
> - ✅ Contrast — настройка контраста
> - ✅ Brightness — настройка яркости
> - ✅ Gamma — гамма-коррекция

</details>

<details>
<summary><b>2DFX Effects</b></summary>

> - ✅ Создание 2DFX эффектов (Light, Particle, Ped Attractor, Sun Glare)
> - ✅ Привязка/отвязка 2DFX к мешу — координаты автоматически пересчитываются при экспорте
> - ✅ Пресеты: Default, OnAllDay, Lamp Post, Lamp Post Coast, BB Pickup, Flashing, Train Crossing, Traffic
> - ✅ Выпадающие списки для Corona Texture (34 текстуры), Shadow Texture, Show Mode, Flare Type
> - ✅ Экспорт 2DFX в DFF (RW Light chunk + 2DFX PLG)
> - ✅ Визуализация всех эффектов и редактирование в реальном времени
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Itera_Inu_tools](gif/2DFX.gif)
>
> </details>

</details>

<details>
<summary><b>Материалы</b></summary>

> - ✅ Environment Map
> - ✅ Bump Map
> - ✅ Specular
> - ✅ UV Animation
> - ✅ Reflection Material
> - ✅ Dual Texture / Blend Mode
> - ✅ COL Surface Type (179 типов GTA SA)
> - ✅ Автозагрузка текстур по именам материалов
> - ✅ Drag & Drop — создание материалов перетаскиванием
> - ✅ Очистка дубликатов (.001, .002)
> - ✅ Сортировка материалов по имени

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
<summary><b>Проверка</b></summary>

> - ✅ Проверка геометрии — висящие вершины, рёбра, N-gons
> - ✅ Проверка лимита материалов (50 для GTA SA)
> - ✅ Очистка/сортировка материалов
> - ✅ LOD/COL → DFF snap — подтянуть LOD и COL к позиции DFF
> - ✅ Скрытие DFF/LOD/COL по отдельности
> - ✅ Проверка конфликтов Model ID
> - ✅ Массовое назначение типа (OBJ/COL/SHA/NON) с переименованием
> - ✅ Сброс трансформ — обнуление Location и Rotation для выделенных мешей
>
> <details>
> <summary><b>Tutorial .gif</b></summary>
>
> ![Check](gif/Check.gif)
>
> </details>

</details>

<details>
<summary><b>Water IO</b></summary>

> - ✅ Импорт/экспорт water.dat
> - ✅ Текстура waterclear256 с анимацией течения
> - ✅ Типы воды: Обычная/Мелкая, Видимая/Невидимая
> - ✅ Привязка к сетке (x4), сшивание краёв
> - ✅ Экспорт коллекции Water

</details>

<details>
<summary><b>Path IO</b></summary>

> - ✅ Импорт/экспорт paths.ipl (авто/пешеходные пути для gta.dat)
> - ✅ Импорт/экспорт tracks.dat (ж/д пути, станции)
> - ✅ Импорт/экспорт NODES.dat (скомпилированные пути), мультифайловый импорт
> - ✅ Создание путей, конвертация кривых/рёбер в пути
> - ✅ Автоматическое разбиение на группы по 12 нод
> - ✅ Экспорт NODES с авто-разбиением по зонам 8x8

</details>

<details>
<summary><b>Персонажи (Skinned DFF)</b></summary>

> - ✅ Импорт DFF с скелетом (Armature), vertex weights, bone matrices
> - ✅ Экспорт skinned DFF (round-trip с побайтовой точностью)
> - ✅ IFP анимации: импорт ped.ifp (294+ анимаций), поиск, применение к скелету
> - ✅ Совместимость с Kams Script DFF и оригинальными игровыми моделями

</details>

<details>
<summary><b>Интеграции</b></summary>

> - ✅ Support Itera Tools 3 (Vertex Lit Linear / Quickstart)
> - ✅ LightMap (beta_MTA)
> - ✅ Pipeline (Building / Reflections)
> - ✅ Горячие клавиши (Shift+T, Shift+A)
> - ✅ Локализация (RU / EN)

</details>

## Видео

[![IDE/IPL/IMG/Map Tutorial](https://img.youtube.com/vi/Jw_R9QFYxWE/0.jpg)](https://www.youtube.com/watch?v=Jw_R9QFYxWE)

> Export & Import IDE / IPL / IMG / Map

## Установка

1. Скачайте папку `INU_tools/` (или zip-архив)
2. Поместите папку `INU_tools/` в `Blender/5.1/scripts/addons/`
3. Blender → Edit → Preferences → Add-ons → включите "INU_tools(gta_sa)"

## Использование

Аддон добавляет панели в:
- **Properties > Scene > INU Tools** — пути IDE/IPL/IMG, текстуры, NVTT, суффиксы моделей, менеджер ID, пресеты
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

- **Blender 4.2+**
- NVIDIA Texture Tools — опционально, для GPU сжатия текстур (автодетект)
- Itera Tools 3 — опционально, для vertex lighting (https://itera.gumroad.com/l/IteraTools3)

<details>
<summary><b>История изменений</b></summary>

- **v1.6.1** — IPL Import: перемещение COL вместе с DFF, Empty-плейсхолдеры с _empty суффиксом в коллекции IPL_Empty, кнопка Заменить Empty; Префиксы моделей в настройках с авто-очисткой конфликтов; Model Links — визуализация связей DFF↔LOD↔COL пунктирными линиями; LOD/COL → DFF snap; Скрытие DFF/LOD/COL по отдельности; Удалить из IMG по типу объекта; Список файлов IMG с прокруткой и поиском; Менеджер ID: очистка выделенных, синхронизация сцены, файл 321-19999, проверка конфликтов; Normals toggle; Drag & Drop TXD с созданием материалов
- **v1.6.0** — Import Map: полный workflow импорта карты (Extract → Build .glb → Import), автосортировка по коллекциям (Buildings/Vegetation/Props/Small/LOD), дубликаты в _Instances подколлекциях; BBox Mode: переключение далёких объектов в Bounding Box с радиусом 300м от выделения; IPL ZONE секция: парсинг/запись/визуализация зон карты; динамические регионы карты из gta.dat (вместо захардкоженных); TXD: исправлена декомпрессия RASTER_888 (32-bit BGRX), улучшена детекция DXT по compression_flag; GPU NVTT автодетект (без toggle кнопки); UI: объединены панели Экспорт/Импорт, компактный layout IDE/IPL/IMG, панель Проверка переведена на русский; экспорт коллекций (если ничего не выделено — экспорт активной коллекции); убраны: Fake mode, Bounds mode, LOD view, Auto-discover кнопка
- **v1.5.3** — Импорт/экспорт персонажей (skinned DFF): скелет, vertex weights, bone matrices; IFP анимации: импорт 294+ анимаций из ped.ifp, применение к скелету, выбор через поиск; Water IO: импорт/экспорт water.dat, текстура waterclear256, анимация течения, типы воды; Path IO: импорт/экспорт paths.ipl, tracks.dat, NODES.dat, создание/конвертация путей; Bin Mesh PLG — корректные material indices для skinned моделей; пользовательские настройки в INU_Preset (не удаляются при обновлении); совместимость Blender 5.1 (layered actions API); исправлен SkinPLG reader (bones_used, num_used, max_weights)
- **v1.5.2** — Рефакторинг: модульная структура (tools/, data/); COL Light Preview: активный атрибут Day/Night, порог яркости, цифры только на границах, автообновление при перемещении; Менеджер ID моделей (model_ids.txt); авто-LOD в IDE/IPL/IMG экспорте; Export All с 2DFX; LOD в IMG экспорте; массовый IMG экспорт; VC Smooth между объектами; настраиваемые суффиксы моделей; сортировка материалов в панели; сворачиваемые секции в INU Tools
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

> **[Документация](DOCS.md)** | **[Documentation (English)](DOCS_eng.md)** | **[Сравнение с другими инструментами](COMPARISON.md)**

## Благодарности

Проект вдохновлён и частично совместим с:

- **[DragonFF](https://github.com/Parik27/DragonFF)** (Parik, GPL-3.0) — Blender аддон для RenderWare форматов. INU_tools использует совместимые имена свойств материалов и объектов для удобства перехода между аддонами.
- **[RenderWare](https://en.wikipedia.org/wiki/RenderWare)** — игровой движок GTA SA, документация форматов DFF/COL/TXD.

#### Авторы

- **INU** — автор аддона (Discord: 1.n.u)

#### Лицензия

[GPL-3.0](LICENSE)
