# Сравнение инструментов GTA SA

## Инструменты

| Инструмент | Платформа | Автор | Функций |
|------------|-----------|-------|--------:|
| **INU_Tools** | Blender 5.1+ | INU | ~145 |
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
| Map Import (IMG) | ✅ | ✅ | ✅ | — | — | — | — |
| Cull Zone Import | ✅ | ✅ | ✅ | ✅ | — | — | — |
| Occlusion Import | ✅ | — | — | ✅ | — | — | — |
| ZON Import | ✅ | — | ✅ | — | — | — | — |
| BSP Import (Manhunt) | ❌ | — | ✅ | — | — | — | — |
| **EXPORT** | | | | | | | |
| DFF Export | ✅ | ✅ | ✅ | ✅ | — | — | — |
| COL Export | ✅ | ✅ | ✅ | ✅ | — | — | — |
| TXD Export | ✅ (GPU) | ✅ | — | — | — | — | — |
| IDE Export | ✅ | — | ✅ | ✅ | — | ✅ | — |
| IPL Export | ✅ | ✅ (cull) | ✅ | — | — | ✅ | — |
| IMG Archive Export/Import | ✅ | — | — | — | — | — | — |
| Export All (batch) | ✅ | ✅ (mass) | ✅ (mass) | ✅ (multi) | — | — | — |
| IFP Export (анимации) | ✅ | — | ✅ | ✅ | — | — | — |
| Water Export | ✅ | — | ✅ | — | ✅ | — | — |
| Path Export | ✅ | — | — | ✅ | — | — | ✅ |
| ZON Export | ✅ | — | ✅ | — | — | — | — |
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
| VC Smooth между объектами | ✅ | — | ✅ | — | — | — | — |
| Vertex Alpha | ❌ | — | ✅ | — | — | — | — |
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
| Skinned Mesh | ❌ | ✅ | ✅ | — | — | — | — |
| IFP Animation IO | ❌ | — | ✅ | ✅ | — | — | — |
| Bone Management | ❌ | ✅ | ✅ | — | — | — | — |
| **MAP** | | | | | | | |
| Map Import (IMG→scene) | ✅ | ✅ | ✅ | — | — | — | — |
| Cull Zones IO | ✅ | ✅ | ✅ | ✅ | — | — | — |
| Occlusion IO | ✅ | — | ✅ | ✅ | — | — | — |
| Water IO | ✅ | — | ✅ | — | ✅ | — | — |
| Path IO | ✅ | — | — | ✅ | — | — | ✅ |
| ZON IO | ✅ | — | ✅ | — | — | — | — |
| Map Objects (Garage/Cars/...) | ✅ | — | ✅ | — | — | — | — |
| **ИНТЕГРАЦИЯ** | | | | | | | |
| Itera Tools 3 | ✅ | — | — | — | — | — | — |
| Lightmap Generator (MTA) | ✅ | — | — | — | — | — | — |
| Менеджер ID моделей | ✅ | — | — | — | — | — | — |
| Настраиваемые суффиксы | ✅ | — | — | — | — | — | — |
| IDE Флаги (чекбоксы) | ✅ | — | — | — | — | — | — |
| Пресеты прелайта | ✅ | — | — | — | — | — | — |
| COL Light Preview + Порог | ✅ | — | — | — | — | — | — |
| Панель Check (отдельная) | ✅ | — | — | — | — | — | — |

---

## Функции которых нет в INU_Tools

| Функция | Где есть | Сложность |
|---------|----------|-----------|
| Skinned Mesh | DragonFF, GTA_Tools | Высокая |
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
