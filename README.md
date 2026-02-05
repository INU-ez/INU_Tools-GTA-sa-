![image alt](https://github.com/INU-ez/INU_Tools-GTA-sa-/blob/5e82d62dd40105c557ef9cb6be261bb70b63d3a2/logo.jpg)

# INU_Tools (GTA SA)

Аддон для Blender — набор инструментов для экспорта, прелайтинга и подготовки моделей GTA San Andreas.

![Blender](https://img.shields.io/badge/Blender-4.4+-orange?logo=blender)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)
![Version](https://img.shields.io/badge/Version-1.4.6-green)

## Возможности

| Раздел | Инструменты |
|--------|-------------|
| **Export** | DFF (v3.6.0.3), COL (COL3), LOD, TXD (DXT сжатие, параллельная обработка, GPU через NVIDIA Texture Tools) |
| **Export All** | Массовый экспорт по суффиксам `_DFF` / `_LOD` / `_COL` + автосборка TXD |
| **DFF Flags** | Панель настроек геометрии DragonFF (Light, Normals, Pipeline, Vertex Colors, UV Maps) |
| **Prelight** | Запекание Vertex Colors (Fast / With Shadows), Day/Night атрибуты, анализ и предпросмотр |
| **Post-Processing** | Smooth, Contrast, Brightness, Gamma — пост-обработка vertex colors |
| **Fill & Scatter** | Покраска полигонов с пипеткой и уровнями, рассеивание света |
| **UV Editor** | Grid Randomizer, Snap to Grid, 9 точек выравнивания, связывание полигонов |
| **Geometry** | Проверка висящих вершин/рёбер, N-gons, очистка геометрии |
| **Materials** | Автозагрузка текстур, очистка дубликатов, Drag & Drop из File Browser |
| **Lightmap** | Генерация кода для MTA-скрипта, копирование настроек, V-offset *(временно не работает)* |

## Требования

- **Blender 4.4+**
- **[DragonFF](https://github.com/Parik27/DragonFF)** (обязателен для DFF/COL экспорта)
- NVIDIA Texture Tools (опционально, GPU сжатие)

## Установка

1. Скачайте `INU_tools(gta_sa).py`
2. Blender → Edit → Preferences → Add-ons → Install → выберите файл
3. Включите "INU_tools(gta_sa)" в списке

## Использование

| Расположение | Что находится |
|---|---|
| **Properties > Scene > INU Tools** | Экспорт, текстуры, материалы |
| **View3D > Sidebar (N) > GTA Tools** | Геометрия, прелайт, DFF Flags |
| **UV Editor > Sidebar (N) > GTA Tools** | UV инструменты |

### Быстрый экспорт
Назовите объекты с суффиксами (`Model_DFF`, `Model_LOD`, `Model_COL`), выделите и нажмите **Export All**.

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

## Авторы

- **INU** — автор аддона
- **[DragonFF](https://github.com/Parik27/DragonFF)** — Parik27 (зависимость для экспорта)

## Лицензия

[GPL-3.0](LICENSE)
