# Сравнение инструментов GTA SA

## Инструменты

| Инструмент | Платформа | Автор | Функций |
|------------|-----------|-------|--------:|
| **INU_Tools** | Blender 4.2+ | INU | ~178 |
| **DragonFF** | Blender 4.x | Parik | ~132 |
| **GTA_Tools(GF)** | 3ds Max | Kam / Goldfish | ~150 |
| **DeniskaMax** | 3ds Max | Deniska | ~54 |
| **GTA Water IO** | 3ds Max | Goldfish | ~12 |
| **EMAPTool** | 3ds Max | Goldfish | ~22 |
| **ZZPuma Paths IO** | 3ds Max | ZZPuma | ~51 |

---

## Сводная таблица функций

| Функция | INU_Tools | DragonFF | GTA_Tools(GF) | DeniskaMax | WaterIO | EMAPTool | ZZPuma |
|---------|:---------:|:--------:|:--------------:|:----------:|:-------:|:--------:|:------:|
| **IMPORT** | | | | | | | |
| DFF Import | ✅ | ✅ | ✅ | — | — | — | — |
| COL Import | ✅ | ✅ | ✅ | — | — | — | — |
| TXD Import | ✅ | ✅ | — | — | — | — | — |
| IDE Import | ✅ | — | ✅ | — | — | — | — |
| IPL Import | ✅ | ✅ (map) | ✅ | — | — | — | — |
| IFP Import (анимации) | ✅ | — | ✅ | — | — | — | — |
| Water Import | ✅ | — | ✅ | — | ✅ | — | — |
| Path Import | ✅ | — | — | ✅ | — | — | ✅ |
| Map Import (.glb) | ✅ | ✅ | ✅ | — | — | — | — |
| Cull Zone Import | ✅ | ✅ | ✅ | ✅ | — | — | — |
| Occlusion Import | ✅ | — | — | ✅ | — | — | — |
| Zone Import | ✅ | — | ✅ | — | — | — | — |
| **EXPORT** | | | | | | | |
| DFF Export | ✅ | ✅ | ✅ | ✅ | — | — | — |
| COL Export | ✅ | ✅ | ✅ | ✅ | — | — | — |
| TXD Export (CPU/GPU) | ✅ | ✅ | — | — | — | — | — |
| IDE Export | ✅ | — | ✅ | ✅ | — | ✅ | — |
| IPL Export | ✅ | ✅ (cull) | ✅ | — | — | ✅ | — |
| IMG Archive Export/Import | ✅ | — | — | — | — | — | — |
| Export All (batch) | ✅ | ✅ (mass) | ✅ (mass) | ✅ (multi) | — | — | — |
| Export Collection | ✅ | — | — | — | — | — | — |
| IFP Export (анимации) | ✅ | — | ✅ | ✅ | — | — | — |
| Water Export | ✅ | — | ✅ | — | ✅ | — | — |
| Path Export | ✅ | — | — | ✅ | — | — | ✅ |
| Zone Export | ✅ | — | ✅ | — | — | — | — |
| Cull Zone Export | ✅ | ✅ | ✅ | ✅ | — | — | — |
| Occlusion Export | ✅ | — | — | ✅ | — | — | — |
| **МАТЕРИАЛЫ** | | | | | | | |
| Environment Map | ✅ | ✅ | ✅ | — | — | — | — |
| Bump Map | ✅ | ✅ | ✅ | — | — | — | — |
| Reflection | ✅ | ✅ | ✅ | — | — | — | — |
| Specular | ✅ | ✅ | ✅ | — | — | — | — |
| UV Animation | ✅ | ✅ | — | ✅ | — | — | — |
| Dual Texture / Blend | ✅ | ✅ | ✅ | — | — | — | — |
| COL Surface Types (179) | ✅ | ✅ | ✅ | ✅ | — | — | — |
| Cleanup дубликатов | ✅ | — | — | — | — | — | — |
| Сортировка материалов | ✅ | — | — | — | — | — | — |
| Drag & Drop текстур | ✅ | — | — | — | — | — | — |
| Автозагрузка текстур | ✅ | ✅ | — | — | — | — | — |
| Vehicle Color Presets | ❌ | ✅ | ✅ | — | — | — | — |
| Bitmap Manager | ❌ | — | ✅ | — | — | — | — |
| **PRELIGHT** | | | | | | | |
| Vertex Color Bake | ✅ | — | — | — | — | — | — |
| Bake с тенями (raycast) | ✅ | — | — | — | — | — | — |
| Fill Colors (пипетка) | ✅ | — | — | — | — | — | — |
| Scatter Light | ✅ | — | — | — | — | — | — |
| Day/Night атрибуты | ✅ | ✅ | ✅ | ✅ | — | — | — |
| Post-Processing (S/C/B/G) | ✅ | — | — | — | — | — | — |
| COL Light Bake | ✅ | — | — | — | — | — | — |
| COL Light Preview | ✅ | — | — | — | — | — | — |
| Prelight Preview | ✅ | — | — | — | — | — | — |
| Day↔Night копирование | ❌ | — | ✅ | ✅ | — | — | — |
| Vertex Alpha (редактор) | ❌ | — | ✅ | — | — | — | — |
| VC Smooth между объектами | ✅ | — | ✅ | — | — | — | — |
| Пресеты прелайта | ✅ | — | — | — | — | — | — |
| **2DFX** | | | | | | | |
| Light (превью + пресеты) | ✅ | ✅ | ✅ | — | — | — | — |
| Particle | ✅ | ✅ | ⚠️ stub | — | — | — | — |
| Ped Attractor | ✅ | ✅ | — | — | — | — | — |
| Sun Glare | ✅ | ✅ | — | — | — | — | — |
| Road Sign | ❌ | ✅ | ⚠️ stub | — | — | — | — |
| Escalator | ❌ | ✅ | ⚠️ stub | — | — | — | — |
| Cover Point | ❌ | ✅ | — | — | — | — | — |
| Trigger Point | ❌ | ✅ | — | — | — | — | — |
| Enter/Exit | ❌ | ✅ | ✅ | — | — | — | — |
| **UV** | | | | | | | |
| UV Grid Randomizer | ✅ | — | — | — | — | — | — |
| Snap to Grid | ✅ | — | — | — | — | — | — |
| Sprite Sheet Animator | ❌ | ✅ | — | ✅ | — | — | — |
| **ГЕОМЕТРИЯ** | | | | | | | |
| Проверка/очистка | ✅ | — | ✅ | — | — | — | — |
| Лимит 50 материалов | ✅ | — | — | — | — | — | — |
| Breakable Objects | ❌ | ✅ | ✅ | ✅ | — | — | — |
| Object Explode (разрезка) | ❌ | — | ✅ | — | — | — | — |
| Face Groups (COL) | ❌ | ✅ | — | — | — | — | — |
| **СКЕЛЕТ / АНИМАЦИИ** | | | | | | | |
| Skinned Mesh Import/Export | ✅ | ✅ | ✅ | — | — | — | — |
| IFP Animation IO | ✅ | — | ✅ | ✅ | — | — | — |
| Bone Management | ❌ | ✅ | ✅ | — | — | — | — |
| **MAP** | | | | | | | |
| Map Import (.glb workflow) | ✅ | ✅ | ✅ | — | — | — | — |
| Map Build (DFF→glTF) | ✅ | — | — | — | — | — | — |
| BBox Mode | ✅ | — | — | — | — | — | — |
| Auto-sort Collections | ✅ | — | — | — | — | — | — |
| Dynamic Regions (gta.dat) | ✅ | — | — | — | — | — | — |
| Replace IPL Placeholders | ✅ | — | — | — | — | — | — |
| Cull Zones IO | ✅ | ✅ | ✅ | ✅ | — | — | — |
| Occlusion IO | ✅ | — | ✅ | ✅ | — | — | — |
| Water IO | ✅ | — | ✅ | — | ✅ | — | — |
| Path IO | ✅ | — | — | ✅ | — | — | ✅ |
| Zone IO | ✅ | — | ✅ | — | — | — | — |
| Map Objects (Garage/Cars/...) | ✅ | — | ✅ | — | — | — | — |
| **ИНТЕГРАЦИЯ** | | | | | | | |
| Itera Tools 3 | ✅ | — | — | — | — | — | — |
| Lightmap Generator (MTA) | ✅ | — | — | — | — | — | — |
| Менеджер ID (321-19999) | ✅ | — | — | — | — | — | — |
| Загрузка ID из игры | ✅ | — | — | — | — | — | — |
| Настраиваемые суффиксы | ✅ | — | — | — | — | — | — |
| IDE Флаги (чекбоксы) | ✅ | — | — | — | — | — | — |
| LOD Distance (отдельное поле) | ✅ | — | — | — | — | — | — |
| Normals toggle (Pipeline) | ✅ | — | — | — | — | — | — |
| Пресеты прелайта | ✅ | — | — | — | — | — | — |
| COL Light Preview + Порог | ✅ | — | — | — | — | — | — |
| GPU NVTT автодетект | ✅ | — | — | — | — | — | — |
| Локализация (RU/EN) | ✅ | — | — | — | — | — | — |
| Сохранение путей (paths.json) | ✅ | — | — | — | — | — | — |
| X Radar Maker (тайлы мини-карты) | ✅ | — | ✅ | — | — | — | — |
| Model Links визуализация | ✅ | — | — | — | — | — | — |
| Скрытие DFF/LOD/COL | ✅ | — | — | — | — | — | — |
| LOD/COL → DFF snap | ✅ | — | — | — | — | — | — |
| Удалить из IMG | ✅ | — | — | — | — | — | — |
| Список файлов IMG | ✅ | — | — | — | — | — | — |
| Заменить Empty (IPL) | ✅ | — | — | — | — | — | — |
| Drag & Drop TXD | ✅ | — | — | — | — | — | — |
| DFF Flags панель | ✅ | — | — | — | — | — | — |
| ID Manager (синхр./создание) | ✅ | — | — | — | — | — | — |
| Проверка конфликтов ID | ✅ | — | — | — | — | — | — |
| Суффиксы + Префиксы | ✅ | — | — | — | — | — | — |
| Batch Set Type (OBJ/COL/SHA/NON) | ✅ | — | — | — | — | — | — |
| Назначить ID с номера | ✅ | — | — | — | — | — | — |
| Расширить ID (FLA) | ✅ | — | — | — | — | — | — |
| Сброс трансформ | ✅ | — | — | — | — | — | — |
| LightMap UV2 превью | ✅ | — | — | — | — | — | — |
| NODES мультифайловый импорт | ✅ | — | — | — | — | — | ✅ |
| NODES экспорт (зоны 8x8) | ✅ | — | — | — | — | — | ✅ |
| Очистка .001 при экспорте IDE/IPL | ✅ | — | — | — | — | — | — |

---

## Функции которых нет в INU_Tools

| Функция | Где есть | Сложность |
|---------|----------|-----------|
| Road Sign 2DFX | DragonFF | Средняя |
| Escalator 2DFX | DragonFF | Средняя |
| Cover/Trigger Point 2DFX | DragonFF | Низкая |
| Enter/Exit 2DFX | DragonFF, GTA_Tools | Средняя |
| Breakable Objects | DragonFF, GTA_Tools, DeniskaMax | Средняя |
| Vehicle Color Presets | DragonFF, GTA_Tools | Низкая |
| Bitmap Manager | GTA_Tools | Низкая |
| Sprite Sheet UV Animator | DragonFF, DeniskaMax | Низкая |
| Day↔Night копирование | GTA_Tools, DeniskaMax | Низкая |
| Face Groups (COL) | DragonFF | Средняя |
| Object Explode | GTA_Tools | Средняя |
| Bone Management | DragonFF, GTA_Tools | Средняя |
| Vertex Alpha (редактор) | GTA_Tools | Низкая |
