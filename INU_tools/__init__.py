# INU_tools(gta_sa) for Blender 4.2+
# Copyright (C) 2024-2026  INU
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Material/Object property names are compatible with DragonFF by Parik (GPL-3.0)
# https://github.com/Parik27/DragonFF
#
# Объединённая панель инструментов для работы с GTA SA моделями
# Включает: Export (DFF, COL, LOD, TXD), Prelight, Lightmap Generator

bl_info = {
    "name": "INU_tools(gta_sa)",
    "author": "INU",
    "version": (1, 7, 0),
    # Минимум 2.80 — поддержка через tools/compat.py:
    # • bake / preview / DFF I/O работают через legacy mesh.vertex_colors
    # • prelight preview shader использует ShaderNodeMixRGB на ≤3.3
    # • VC Layers System требует 3.2+ (на старых показывает warning)
    # • IK rig работает на pose.bones (без bone collections)
    # blender_manifest.toml для extensions.blender.org остаётся 4.2+ —
    # это второй канал distribution, для современного Blender'а.
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar (N) > GTA Tools",
    "description": "Toolset for GTA SA models",
    "category": "3D View",
    # Dev build marker — все коммиты после тега v1.7.0 идут как нерелизные.
    # Blender показывает это поле красным в Edit → Preferences → Add-ons.
    # Снять при cut-релиза 1.7.1 / 1.8.0.
    "warning": "Dev build (post 1.7.0) — нерелизная сборка, возможны баги",
}

# Changelog:
# v1.7.0 - Большой UX-релиз + рефакторинг.
#        - Adaptive grid auto-split (tools/map_export.py compute_adaptive_cells):
#          quadtree-разбиение по плотности (max_per_cell, min_cell_size floor).
#          Плотные районы получают мелкие ячейки, разреженные остаются одной
#          большой. Имя ячейки <base>_q<path>, где path — путь по квадрантам
#          (0=SW, 1=SE, 2=NW, 3=NE). 13 unit-тестов в test_map_export_split.py.
#        - Prelight panel polish: убраны иконки FORWARD/BACK на кнопках Day↔Night
#          (выглядели как media play/back и спорили со стрелкой → в тексте),
#          лейбл «Скопировать:» как заголовок, удалены 3 layout.separator() и
#          info-кнопки перед лейблами — на 4-5 строк ниже.
#        - IK Rig для SA peds (ops/ik_rig.py): control-bones внутри армати с custom-shape
#          кубиками (chain/pole/rot/root), FK→IK bake при создании, brute-force
#          pole_angle калибровка, Bake & Clear IK перед IFP-экспортом, INU_Ground
#          floor plane 10×10м с FLOOR constraint и offset slider.
#        - Animated Map Object workflow (ops/animobj_ops.py): Setup rig → Validate →
#          Export DFF+IFP+IDE одной кнопкой. Ползунки axis/turns/duration/reverse
#          с auto-rebuild keyframes. Auto vs Manual режим управления Action.
#        - Frame Hierarchy Editor (ops/frame_hierarchy.py): Rename / Set Parent /
#          Unparent / Зеркало L↔R / Validate Vehicle (37 dummies) / Validate Ped
#          (31 кость) против vanilla SA шаблонов.
#        - Vehicle Paintjob (ops/paintjob_ops.py): material props paintjob_alt_1/_2
#          + TXD-хук пишет <base>_paintjob1/2 + Validate Paintjobs.
#        - Profile system (tools/profiles.py): JSON-storage наборов N-sidebar
#          панелей в INU_Preset/profiles/<name>.json со списком order и hidden,
#          dropdown в шапке + операторы save/edit/delete/pick_panel/toggle_panel.
#        - Smart auto-TXD picker (ops/dff_import.py): coverage-based scoring
#          (same-name → ≥50% coverage → solo). Использует core/txd.read_txd_texture_names
#          (header-only TXD parse, ~50× быстрее). Грузит с name_filter — только
#          нужные текстуры (vehicle.txd 150 → ~5 для одной двери).
#        - DFF/COL drag-drop в viewport (FH_dff_drop, FH_col_drop), TXD-drop
#          теперь цепляет материалы на выделенные меши.
#        - 2DFX panel: collapsible-секции (Свойства/Поведение/Тень/Флаги),
#          семантические группы флагов (Видимость/Эффекты короны/Мерцание/Доп.),
#          per-bit tooltips через operator description classmethod.
#        - DFF Flags pipeline-aware: Vehicle прячет Day/Night/Light Beam,
#          Day/Night pipeline прячет mesh-флаги Day/Night.
#        - Texture Manager dropdowns: Текстуры (Найти/Скопировать/Дубли/Найти-Удалить
#          unused) + Материалы (Check/Cleanup/Sort) — 9 кнопок → 3 строки.
#        - Compact mass export: «В папку» / «В IMG» уехали в дропдаун Экспорт ▾
#          как «All → Папка» / «All → IMG». Убран hint «Полный экспорт».
#        - Selection diagnostic: при множественном DFF показывает «name +N» count.
#        - Save-required wrappers (Extract Resources / Import Map / Export Map):
#          alert-box + disabled-кнопки пока .blend не сохранён. Soft cache-empty
#          warning на Import Map (Empty placeholders вместо hard cancel).
#        - Light Master container panel: 5 sub-panels (Prelight/Prelight COL/
#          Vertex Paint/Lightmap/Itera Tools) под одним заголовком.
#        - 4 dropdown menus: Create 2DFX / Radar Maker / Path Traffic / Import-Export.
#        - 2-column IDE/IPL panel layout, niche IPL utilities полной шириной снизу.
#        - Все operator bl_label получили префикс «INU: » для F3-поиска.
#        - Bug fixes: TXD import duplicates (vehiclelights128.001-005),
#          material dedup при DFF import (fingerprint всех effect-блоков),
#          2DFX preview plane size (corona_size * 5.0 → native), BreakableData
#          round-trip (reader не парсил), IFP export round-trip (rest_quat @ bl_quat
#          инверс), IFP custom skin root motion (bone_id fallback для 'Bip01'/'Root'),
#          Blender 5.x compat (layered Action API, default=set() fix).
#        - Refactor: __init__.py 16486 → 4327 строк. 22 новых ops/*.py модуля,
#          ui/panels.py (2820 строк), ui/registry.py с apply_order декоратором.
#        - 7 новых pytest файлов (~110 тестов) в dev/tests/: DFF/COL/IDE/IPL/IMG
#          round-trip + panel registry + profiles.
#        - Repo cleanup: docs/ папка, удалён COMPARISON.md.
#        - DOCS_rus.md +470 строк: новые рецепты IK Rig / Profile system /
#          Animated Map Object / Frame Hierarchy / Paintjob.
# v1.6.7 - Map round-trip preservation (полный цикл импорт→правка→экспорт):
#        - inu.col_name + inu.lod_object свойства для round-trip разметки COL/LOD
#          через scene props (не теряются при reload .blend).
#        - Group-by-IPL импорт: каждый исходный IPL → отдельная коллекция; By-collection
#          экспорт: каждая коллекция → свой IPL (плюс multi-collection picker с чекбоксами).
#        - Парность main ↔ LOD в IDE/IPL output: lod_index пересчитывается на позицию
#          LOD-инстанса в выходном IPL.
#        - TXD bucketing per-txd_name: модели с одинаковым inu.txd_name группируются
#          в один .txd; per-DFF COL по умолчанию (один col на модель, не one-shared).
#        - Modal Map Export с progress bar и ESC cancel; multi-collection чекбоксный
#          picker; NVTT auto + параллельный DXT1.
#        - Format conformance: CRLF line endings в IDE/IPL/IFP, IPL inst dedup,
#          согласованность ID для .NNN дубликатов в outliner.
#        - Vehicles панель вынесена из Check как dedicated.
# v1.6.6 - Map auto-split (XY grid): tools/map_export.py auto_split=True + cell_size
#          (по умолчанию 256м) → каждая клетка свой IPL для эффективной streaming-загрузки.
#        - Vehicle damage variants: ops/vehicle.py операторы Add (создаёт _dam meshcopy
#          скрытый во viewport), Show OK/Dam/Both (toggle hide_viewport на парах),
#          Check pairs (отчёт с одиночными атомиками).
#        - VC Layer System (BETA): tools/vc_layers.py — composite vertex colors из
#          нескольких layers с per-layer opacity/brightness/contrast, multi-select.
#        - IFP write: ANP2 / ANPK форматы (раньше только ANP3), source_format
#          сохраняется при импорте → экспорт по умолчанию пишет в исходном формате.
#        - Bitmaps Manager: Find Unused / Remove Unused (orphan images + materials).
#        - COL parsing ~5× быстрее (numpy bulk decode фасов/вершин).
#        - Train paths verified: запись/чтение track1/track2.dat с прогоном round-trip.
# v1.6.5 - Производительность и round-trip карты — накопленные изменения после 1.6.4-beta
#        - Import Map ~10x быстрее: полный район LA за ~30 с (было 5+ мин)
#          - cache-only поток (никакого обращения к IMG в горячем цикле)
#          - параллельный DFF-парсинг: 4-worker ThreadPoolExecutor, split на
#            read_dff_file (main) + DffClump.to_bytes (worker) — numpy/zlib отпускают GIL
#          - material-cache по (texture_name, RGBA) — одна текстура на 500 моделей = один материал
#          - bulk_mode в import_dff: пропускает per-model view_layer.update/select_all
#            (O(N²) → O(N)), target_collection напрямую — без unlink+relink
#          - убран print("[DFF Parse] ...") на каждом frame (~170 с потерь на stdout)
#          - LOD-детекция теперь только по имени (is_lod_name), lod_refs из IPL отключён
#            из-за шумных данных ванили
#          - bulk_mode пропускает armature для ванильных DFF с HAnim без skin
#          - фикс IPL lod_index remap при мерже нескольких IPL в один список
#        - Import Map — Load COL toggle: коллизии подтягиваются рядом с геометрией
#          в Map_COL коллекцию, с transform'ом на каждый инстанс. Для round-trip
#          (импорт части карты → редактирование → экспорт в IMG другой сборки).
#          Парсинг .col параллелен в том же пуле, ключуется по внутреннему model_name.
#        - Export to IMG ~5-15x быстрее:
#          - ImgWriter context manager (core/img.py): директория читается и пишется
#            по одному разу вместо N раз (~2.6 ГБ лишних записей на большом экспорте)
#          - параллельное кодирование DFF/COL: build_dff_clump/build_col_model на main
#            (bpy reads), clump.to_bytes() в 4-поточном пуле
#        - Shared TXD toggle (симметрично с COL Library): пакует все текстуры в один
#          общий .txd вместо одного на модель — scene props gtatools_export_all_txd_shared[_name]
#        - Фикс «экспортируется только коллизия»: унифицированы тумблеры DFF/COL/LOD/TXD
#          между «В папку», «В IMG», «INU Export». Все операторы теперь читают
#          gtatools_export_all_*, устаревшие gtatools_img_export_* удалены.
#          Добавлен отдельный export_lod_flag (раньше LOD был привязан к DFF).
#        - ID Manager:
#          - новая reserve_id(model_id, name) — помечает ID занятым (append если нет)
#          - новая sync_scene_to_preset(objects) — подтягивает ID сцены в пресет,
#            вызывается в начале Auto Assign / Assign From
#          - новая gc_preset(objects) + кнопка «Освободить фантомы» в ID Manager панели —
#            освобождает слоты без backing-объекта
#          - Assign IDs from... теперь пишет в пресет через reserve_id на каждом назначении
#          - Clear Selected IDs не освобождает слот если другой объект сцены держит тот же ID
#            (защита от Shift+D-дубликатов с наследуемым inu.model_id)
#          - новая кнопка «Очистить ID» в Object Properties → INU Tools: Model, под полем Model ID
#        - UI pipeline reorganization (Этапы 1-6):
#          - все подпанели N-sidebar получили bl_order по категориям SETUP/MODEL/DATA/EXPORT
#          - Export панель наверху (bl_order=0), 3-кнопочный ряд: В папку / В IMG / INU Export
#          - Суффиксы/Префиксы и ID Manager вынесены из Scene Properties в N-sidebar
#          - новая панель «INU Tools: Model» в Object Properties — все per-object props в одном месте
#          - Itera Tools 3 / Vertex Paint / LightMap скрыты через poll() до доработки
#          - убраны dead code: gtatools.prelight (35 строк), custom Twemoji PNG icons
#          - Bitmaps Manager переведён на русский (23 новых entries в locale/eng.py)
#        - Material Presets: формат перенесён из JSON в INU_Preset, добавлено undo для
#          7 операторов (Set Preset, Fill Colors, Scatter Light, Bake, Post-Process, ...)
#        - Progress bars: добавлены в Build Map / Export to IMG / Extract Resources
#        - ID Manager multi-preset: поддержка нескольких файлов пресетов
#          в INU_Preset/id_presets/<name>.txt с UI create/rename/delete
#        - LOD Detection: обработка нерегулярных имён ванили (LODfoo / foo_LOD /
#          foo1LOD / modeLODlaett) — is_lod_name покрывает все 4 паттерна
#        - Profiler: thread-safe Profiler в tools/profiler.py + Scene toggle
#          gtatools_profile_enabled — отчёт в .inu_cache/_profile.log
#        - Skip 2DFX по умолчанию = True для bulk-импорта карты (иначе тысячи
#          Light/Empty объектов роняют viewport)
# v1.6.4 - (pre-release) 11 экспериментальных фич — проверка в игре ещё не проведена
#        - Map Export: единый экспорт сцены → DFF + COL + TXD + IDE + IPL одной кнопкой
#          (tools/map_export.py, авто-паринг LOD/COL, пул ID из настройки для пустых model_id=0)
#        - Binary IPL Write: запись в формате `bnry` (только inst+cars, как у Rockstar)
#          (core/ipl.py _write_binary_ipl + чекбокс Binary в GTATOOLS_OT_export_ipl)
#        - UV-анимация в DFF: простой U/V-скролл через чанки 0x2B + 0x135
#          (core/dff.py UVAnim/UVAnimDict, material props uv_anim_write/speed_u/v/duration)
#          ОГРАНИЧЕНИЕ: только запись, обратное чтение не реализовано
#        - Breakable Objects: чанк 0x253F2FD + сила разрушения per-object
#          (core/dff.py BreakableData, обj.inu.breakable/breakable_force)
#        - IFP Batch Import: папка с .ifp → стек на NLA-треке armature
#          (ops/ifp_import.py batch_apply_sequential, режимы NLA/Actions, зазор между клипами)
#        - GTA Material Panel: вкладка Properties → Material с dropdown пресетов
#          (Generic/Vehicle Body/Vehicle Glass/Ped/Env/Dual/Specular + vehicle color slot)
#        - Bitmaps Manager: scan missing / resolve from folder / batch copy / find duplicates
#          (tools/bitmaps_manager.py, панель в N-Sidebar GTA Tools)
#        - CST IO: текстовая сериализация COL (формат Steve's COL Editor, с shadow mesh)
#          (core/cst.py + ops/cst_import.py + ops/cst_export.py)
#        - Vehicle Scale Helper: пропорциональное масштабирование иерархии машины
#          (tools/vehicle_scale.py, опция Dummies Only)
#        - Train Station Markers: видимые Empty-сферы на станциях train-трека
#          (ops/ifp_import.py _refresh_station_markers)
#        - Roadblocks & Traffic Lights: переключение per-node флагов на выделенных path-IPL точках
#          (core/paths.py PATH_FLAG_* константы, ops/ifp_import.py GTATOOLS_OT_path_node_flag)
#        - FLA4 Path Format: чтение/запись расширенных nodes*.dat (spawn/speed/lanes per-node)
#          (core/paths.py FLA4_MAGIC + ветки в read_nodes/write_nodes, чекбокс в Export Path Nodes)
#        - Фиксы ревью: UV_ANIM_KEYFRAME_SIZE 36→32 (pack был короче на 4 байта),
#          path_node_flag правильный маппинг spline→IDProp через пропуск empty-нод,
#          station markers через matrix_parent_inverse.identity() + local pt.co,
#          map_export переключение в OBJECT mode перед select_all,
#          UVAnim.node_to_uv дефолт (1,0,...) вместо (0,...) — иначе анимация инертна
#        - Bitmaps Manager group_by_txd: читает obj.inu.txd_name (а не mat.get('txd_name'))
#          через обратный индекс материал→TXDs
#        - DOCS.md + DOCS_rus.md: новая секция "Experimental (v1.6.4)" с 12 подразделами
#        - README.md + README_rus.md: секция "Experimental (v1.6.4)" с warning-блоком,
#          Coming Soon сжат до одного пункта (Vehicles Phase 2+)
#        - bl_info warning: "Experimental features — not fully tested in-game"
#          (оранжевая метка в Blender Add-ons panel)
# v1.6.3 - Particle Effects: полноценный редактор GTA SA effects.fxp
#        - Парсер effects.fxp (text-based, 82 эффекта), кэш с auto-reload
#        - Симуляция частиц в viewport (30 FPS, до 64 частиц на эмиттер, billboard к камере)
#        - Dropdown выбора эффекта из 82 систем + multi-emitter switching
#        - Редактирование 40+ параметров: цвет, размер, скорость, направление, физика, ветер, гравитация
#        - Keyframe editor для curves (size/color/alpha over lifetime)
#        - Сохранение в effects.fxp с авто-бэкапом (.fxp.bak)
#        - Operators: New, Delete, Switch Emitter, Reload effects.fxp
#        - IDE/IPL Export: очистка .001 дубликатов перед записью
#        - IPL Upsert: поддержка нескольких instances одной модели (match по позиции)
#        - DFF Export: _read_texture идёт через Prelight_Mix/LM_Mix к реальной текстуре
#        - TXD Export: пропускает LM_Texture/Lightmap_Texture ноды
#        - LightMap UV2: Add/Toggle/Remove кнопки в Prelight панели (Multiply blend на UV2)
#        - Prelight Bake: использует loop.normal (smooth shading), пропускает скрытые лампы
#        - Reset Transform: сброс Location/Rotation в (0,0,0) для выделенных мешей
#        - Batch Set Type: массовое назначение OBJ/COL/SHA/NON с автопереименованием
#        - 2DFX: detach all from mesh, список привязанных в UI меша
#        - 2DFX Billboard: переход с timer на draw handler — фикс tracking при смене сцены
#        - DFF Flags: компактный список чекбоксов вместо больших кнопок
#        - Object Properties: новая панель "GTA SA: IDE / IPL" (перенос из N-панели)
#        - Nodes Export: авто-разбиение по зонам карты 8x8 (64 файла nodes0..63.dat)
#        - Nodes Import: мультифайловый импорт (несколько nodes*.dat за раз)
#        - ID Manager: Assign from ID..., Extend IDs (FLA, Fastman Limit Adjuster)
#        - .gitattributes: нормализация LF/CRLF
#        - Документация: Alpha threshold 57% (145/255) — задокументирован hard cutoff в GTA SA
# v1.6.1 - IPL Import: перемещение COL вместе с DFF, Empty с _empty суффиксом в коллекции IPL_Empty, кнопка Заменить Empty
#        - Префиксы моделей (DFF/LOD/COL) в настройках, авто-очистка конфликтов суффикс/префикс
#        - Все import/export используют пользовательские суффиксы/префиксы
#        - Model Links: визуализация связей DFF↔LOD↔COL пунктирными линиями
#        - LOD/COL → DFF: кнопка подтягивания к позиции DFF
#        - Скрытие DFF/LOD/COL по отдельности в панели Проверка
#        - Удалить из IMG по типу выделенного объекта (DFF+TXD / COL / LOD)
#        - Список файлов IMG (UIList с прокруткой и поиском)
#        - Менеджер ID: очистка ID выделенных, синхронизация сцены, создание файла 321-19999
#        - Проверка конфликтов ID (предупреждение в панели)
#        - Normals toggle в панели Pipeline
#        - Drag & Drop TXD с созданием материалов
# v1.6.0 - Import Map: workflow Extract → Build .glb → Import с автосортировкой по коллекциям
#        - BBox Mode: Bounding Box для далёких объектов (300м от выделения)
#        - IPL ZONE секция: парсинг/запись/визуализация зон карты
#        - Динамические регионы из gta.dat
#        - TXD: исправлена декомпрессия RASTER_888, улучшена детекция DXT
#        - GPU NVTT автодетект
#        - UI: объединены Экспорт/Импорт, компактный layout, панель Проверка на русском
#        - Экспорт коллекций (активная коллекция если ничего не выделено)
#        - Убраны: Fake mode, Bounds mode, LOD view, Auto-discover
# v1.4.7 - Export: COL Surface Type — панель выбора типа поверхности коллизии в Material Properties
#        - 179 материалов GTA SA с поиском по названию, запись через DragonFF col_mat_index
# v1.4.6 - Prelight: Post-Processing — новая подпанель пост-обработки vertex colors (Smooth, Contrast, Brightness, Gamma)
#        - Prelight: Fast Bake теперь поддерживает тени (raycast через depsgraph), переключатель Shadows в панели
#        - Export: новая подпанель DFF Flags — отображает флаги геометрии DragonFF (Light, Normals, Pipeline, UV Maps и др.)
# v1.4.5 - Export All: массовый экспорт нескольких групп моделей (Model1_DFF + Model2_DFF и т.д.)
#        - Lightmap Generator: панель снова доступна в интерфейсе
# v1.4.4 - Prelight: Fill Colors - покраска полигонов с пипеткой и системой уровней
#        - Prelight: Scatter Light - рассеивание света с настройками и уровнями
#        - Prelight: убраны лишние заголовки, оставлены только кнопки
#        - Color Attributes: раздельные кнопки создания/удаления Day и Night
#        - Color Attributes: кнопка Day/Night создаёт оба атрибута
#        - Drag-and-Drop: перетаскивание PNG/JPG/TGA из File Browser создаёт материал
#        - INU Tools панель перемещена в Properties > Scene
#        - Удалена пустая вкладка GTA Textures из N-панели
# v1.4.3 - TXD экспорт: исправлена прозрачность DXT3 текстур в игре
#        - TXD экспорт: текстуры с размером не кратным 4 пропускаются с предупреждением
# v1.4.2 - TXD экспорт: добавлен GPU режим через NVIDIA Texture Tools
# v1.4.1 - TXD экспорт: параллельная обработка текстур (до 8x быстрее)
# v1.4.0 - UV Editor: добавлена панель GTA Tools с UV Grid Randomizer и визуализацией сетки
#        - UV Editor: добавлена привязка UV к ближайшей ячейке сетки (Snap to Grid)
#        - UV Editor: добавлен выбор позиции UV в ячейке (9 вариантов выравнивания)
#        - UV Editor: добавлена функция "Связать полигоны" - полигоны с пересекающимися UV перемещаются вместе
#        - GTA Textures: проверка количества материалов (лимит 50)
#        - GTA Textures: загрузка текстуры только для выбранного материала
#        - GTA Textures: автоустановка Specular=0 и подключение Alpha канала
#        - Переведены все описания кнопок на русский язык
# v1.3.0 - Добавлена очистка материалов: объединение дубликатов (.001, .002, etc.)
# v1.2.9 - Добавлена вкладка GTA Textures: автозагрузка текстур по именам материалов
# v1.2.8 - COL экспорт теперь использует версию COL3 (GTA SA) вместо COL1
# v1.2.7 - DFF экспорт: добавлены only_selected=True и export_coll=False для исправления краша
# v1.2.6 - DFF экспорт теперь использует версию GTA SA (v3.6.0.3) вместо GTA 3
# v1.2.5 - Исправление имени модели внутри COL файла (base_name без суффикса COL)
# v1.2.4 - Добавлен прогресс-бар при Export All
# v1.2.3 - Автоустановка типа Collision Object для COL модели перед экспортом
# v1.2.2 - TXD в Export All берёт текстуры из DFF + LOD в один архив
# v1.2.1 - Поиск моделей только среди выделенных объектов
# v1.2.0 - Улучшено определение моделей по суффиксам DFF/LOD/COL (без разделителей)
# v1.1.0 - Добавлен экспорт DFF/COL/LOD/TXD, определение моделей по суффиксам
# v1.0.0 - Начальная версия

import bpy
import bmesh
import math
import re as _re
import struct
import os
import time
import tempfile
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from mathutils import Vector
from bpy.props import StringProperty, BoolProperty, FloatProperty, FloatVectorProperty, IntProperty, CollectionProperty, EnumProperty, PointerProperty
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper


# =============================================================================
# LOCALIZATION SYSTEM
# =============================================================================

def get_locale():
    """Get current Blender UI language"""
    try:
        locale = bpy.app.translations.locale
        if locale and locale.startswith('ru'):
            return 'ru'
    except:
        pass
    return 'en'

# Translation dictionary: Russian -> English
from .locale import get_translation
from .ui.registry import apply_order


def T(text):
    """Translate text based on Blender UI language.
    Code uses Russian strings as keys. For Russian UI — returns as-is.
    For other languages — looks up translation in locale/<lang>.py files.
    Falls back to English (eng.py) if current language not found.
    """
    locale = get_locale()
    if locale and locale.startswith('ru'):
        return text
    # Try exact locale first, then fall back to English
    tr = get_translation(locale)
    if tr:
        result = tr.get(text)
        if result:
            return result
    # Fallback to English
    eng = get_translation('eng')
    if eng:
        return eng.get(text, text)
    return text


# =============================================================================
# EXTRACTED MODULES
# =============================================================================

from .tools.txd_export import (
    export_txd, check_nvtt_available, write_rw_section_header,
)
from .tools.model_utils import (
    get_model_type, find_related_models, find_selected_models,
    find_all_selected_model_groups, get_base_name_from_selected,
    fix_col_model_name, check_loose_geometry, get_model_textures,
)
from .data.surface_materials import (
    GTA_SA_SURFACE_MATERIALS, COL_SURFACE_ENUM_ITEMS, COL_SURFACE_CATEGORIES,
    _surface_id_to_category, get_col_surface_id, get_surface_name,
    get_base_name_from_selection,
)
from .tools.prelight import (
    average_colors_on_coplanar_faces,
    encode_uv2_to_color_16bit, create_prelight_scene_lights,
    remove_prelight_scene_lights, bake_vertex_colors_from_lights,
    bake_vertex_colors_simple, apply_brightness_offset,
    analyze_vertex_colors, smooth_vertex_colors,
    adjust_vertex_colors_contrast, adjust_vertex_colors_brightness,
    adjust_vertex_colors_gamma, setup_prelight_preview,
    fill_selected_faces, ensure_base_colors, recalculate_colors,
    add_fill_layer, add_scatter_layer, get_scatter_levels,
    remove_scatter_layer, clear_scatter_layers, remove_fill_color,
    remove_fill_color_by_index, get_selected_faces_color,
    fill_selected_faces_with_backup, restore_filled_faces,
    scatter_light_from_selected,
)
# COL Light: import module for mutable globals, classes separately
from .tools import col_light as _col_light_mod
from .tools.col_light import (
    _col_light_invalidate_preview, _col_light_watch_transform,
    GTATOOLS_OT_preview_col_light, GTATOOLS_OT_bake_col_light,
    GTATOOLS_OT_clear_col_light_mats,
)
# UV Tools: import module for mutable globals, classes separately
from .tools import uv_tools as _uv
from .tools.uv_tools import (
    GTATOOLS_OT_toggle_uv_editor, GTATOOLS_OT_toggle_uv_grid,
    GTATOOLS_OT_randomize_uv_grid, GTATOOLS_OT_snap_uv_to_grid,
    GTATOOLS_OT_set_uv_align, GTATOOLS_PT_uv_tools_panel,
    GTATOOLS_OT_add_gtasa_model, VIEW3D_MT_gtasa_add_menu,
    _gtasa_add_menu_draw,
)
from .tools.bitmaps_manager import (
    GTATOOLS_OT_bitmaps_scan, GTATOOLS_OT_bitmaps_resolve,
    GTATOOLS_OT_bitmaps_copy, GTATOOLS_OT_bitmaps_find_dupes,
    GTATOOLS_OT_bitmaps_find_unused, GTATOOLS_OT_bitmaps_remove_unused,
    GTATOOLS_MT_textures_menu, GTATOOLS_MT_materials_menu,
    GTATOOLS_PT_bitmaps_panel,
)
from .tools.vc_layers import (
    GTATOOLS_VCLayerItem,
    GTATOOLS_OT_vcl_add, GTATOOLS_OT_vcl_remove, GTATOOLS_OT_vcl_move,
    GTATOOLS_OT_vcl_promote, GTATOOLS_OT_vcl_demote,
    GTATOOLS_OT_vcl_set_active_attr,
    GTATOOLS_OT_vcl_show_composite, GTATOOLS_OT_vcl_refresh_composite,
    GTATOOLS_OT_vcl_apply_multi, GTATOOLS_OT_vcl_recolor_selected,
    GTATOOLS_UL_vc_layers,
    vc_layers_register_handlers, vc_layers_unregister_handlers,
    _on_active_layer_change as _vc_on_active_layer_change,
    _on_live_preview_toggle as _vc_on_live_preview_toggle,
)
# Phase 4: all panels + UIList classes moved to ui/panels.py.
# Imported AFTER def T because panels.py does `from .. import T` at
# top-level (T is referenced in class bodies for bl_label etc., evaluated
# at class-definition time so it can't be deferred).
from .ui.panels import (  # noqa: E501
    GTATOOLS_PT_material_panel,
    GTATOOLS_UL_txd_export_plan,
    GTATOOLS_UL_img_files,
    GTATOOLS_PT_main_panel,
    GTATOOLS_PT_ide_ipl_panel,
    GTATOOLS_PT_export_panel,
    GTATOOLS_PT_validate_scene,
    GTATOOLS_MT_import_menu,
    GTATOOLS_MT_export_menu,
    GTATOOLS_MT_create_2dfx,
    GTATOOLS_MT_radar_generate,
    GTATOOLS_MT_path_traffic,
    GTATOOLS_PT_check_panel,
    GTATOOLS_PT_vehicle_panel,
    GTATOOLS_PT_frame_hierarchy,
    GTATOOLS_PT_2dfx_panel,
    GTATOOLS_PT_object_ide_ipl_panel,
    GTATOOLS_PT_object_inu_tools,
    GTATOOLS_PT_inu_tools_panel,
    GTATOOLS_PT_id_manager_panel,
    GTATOOLS_PT_light_master,
    GTATOOLS_PT_prelight_panel,
    GTATOOLS_PT_bake_settings_subpanel,
    GTATOOLS_PT_vc_postprocess_panel,
    GTATOOLS_PT_itera_panel,
    GTATOOLS_PT_prelight_col_panel,
    GTATOOLS_PT_vertex_paint_panel,
    GTATOOLS_PT_lightmap_panel,
    GTATOOLS_PT_water_panel,
    GTATOOLS_PT_anim_panel,
    GTATOOLS_PT_radar_panel,
    GTATOOLS_PT_paths_panel,
)
# Material context-menu hook — register/unregister append/remove it.
from .ui.panels import _draw_sort_materials_menu
from .ops.ifp_import import (
    GTATOOLS_OT_ifp_batch_import,
    GTATOOLS_OT_refresh_station_markers,
    GTATOOLS_OT_path_node_flag,
)
from .ops.cst_import import GTATOOLS_OT_import_cst
from .ops.cst_export import GTATOOLS_OT_export_cst
from .ops.paintjob_ops import GTATOOLS_OT_validate_paintjobs
from .ops.onboarding_ops import (
    GTATOOLS_OT_open_docs,
    GTATOOLS_OT_open_issues,
    GTATOOLS_OT_open_release,
    GTATOOLS_OT_whats_new,
)
from .ops.validate_scene import (
    INUValidateIssue,
    GTATOOLS_OT_validate_run,
    GTATOOLS_OT_validate_clear,
    GTATOOLS_OT_validate_goto,
    GTATOOLS_OT_validate_fix_quaternions,
    GTATOOLS_OT_validate_fix_suffix,
    GTATOOLS_OT_validate_fix_modulate_color,
)
from .ops.frame_hierarchy import (
    GTATOOLS_OT_frame_select,
    GTATOOLS_OT_frame_rename,
    GTATOOLS_OT_frame_set_parent,
    GTATOOLS_OT_frame_unparent,
    GTATOOLS_OT_frame_validate,
    GTATOOLS_OT_frame_mirror_lr,
)
from .ops.animobj_ops import (
    GTATOOLS_OT_animobj_setup,
    GTATOOLS_OT_animobj_validate,
    GTATOOLS_OT_animobj_export,
    INUAnimObjProps,
)
from .tools.profiles import (
    GTATOOLS_OT_profile_save,
    GTATOOLS_OT_profile_delete,
    GTATOOLS_OT_profile_pick_panel,
    GTATOOLS_OT_profile_toggle_panel,
    GTATOOLS_OT_profile_edit,
)
from .tools.vehicle_scale import (
    GTATOOLS_OT_vehicle_scale,
    GTATOOLS_OT_vehicle_add_damage_variant,
    GTATOOLS_OT_vehicle_show_damage,
    GTATOOLS_OT_vehicle_pair_report,
)
from .tools.map_export import (
    GTATOOLS_OT_map_export,
)
from .tools.gta_material_panel import (
    GTATOOLS_OT_material_preset,
    GTATOOLS_OT_material_preset_save,
    GTATOOLS_OT_material_preset_delete,
)

addon_keymaps = []

# =============================================================================
# PROPERTY GROUPS
# =============================================================================

# ── Particle curve keyframe PropertyGroup (used by B1 curve editor) ── #
class INUParticleKeyframe(bpy.types.PropertyGroup):
    """A single FX_KEYFLOAT_DATA entry (time, val) for the curve editor buffer."""
    time: FloatProperty(
        name="Time",
        default=0.0, min=0.0, max=1.0, precision=4,
    )
    val: FloatProperty(
        name="Value",
        default=0.0, precision=4,
    )


# ── Particle effect EnumProperty — dynamic items from effects.fxp ── #
# Module-level cache: EnumProperty items callbacks MUST return the same
# Python objects across calls, otherwise Blender shows garbled strings
# (strings get GC'd). We keep the last returned list alive here.
_particle_enum_items_cache = [('', '<not loaded>', '')]
_particle_enum_cache_key = None  # (path, mtime)


def _particle_effect_enum_items(self, context):
    """Items callback for INUObjectProps.particle_effect_2dfx."""
    global _particle_enum_items_cache, _particle_enum_cache_key
    try:
        game_root = bpy.path.abspath(
            getattr(context.scene, 'gtatools_game_root', '') or ''
        )
        if not game_root or not os.path.isdir(game_root):
            _particle_enum_items_cache = [('', T('<Game Root не задан>'), '')]
            _particle_enum_cache_key = None
            return _particle_enum_items_cache

        path = os.path.join(game_root, 'models', 'effects.fxp')
        if not os.path.isfile(path):
            _particle_enum_items_cache = [('', T('<effects.fxp не найден>'), '')]
            _particle_enum_cache_key = None
            return _particle_enum_items_cache

        mtime = os.path.getmtime(path)
        key = (path, mtime)
        if key == _particle_enum_cache_key:
            return _particle_enum_items_cache

        from .core import fxp as _fxp
        fxf = _fxp.load_cached(path)
        items = [(s.name, s.name, "") for s in fxf.systems]
        if not items:
            items = [('', T('<нет эффектов>'), '')]
        _particle_enum_items_cache = items
        _particle_enum_cache_key = key
        return _particle_enum_items_cache
    except Exception as ex:
        _particle_enum_items_cache = [('', f'<ошибка: {ex}>', '')]
        _particle_enum_cache_key = None
        return _particle_enum_items_cache


def _particle_effect_get(self):
    obj = self.id_data
    name = obj.get('2dfx_effect_name', '') or ''
    for i, item in enumerate(_particle_enum_items_cache):
        if item[0] == name:
            return i
    return 0


def _particle_effect_set(self, value):
    obj = self.id_data
    items = _particle_enum_items_cache
    if 0 <= value < len(items):
        name = items[value][0]
        if name:
            obj['2dfx_effect_name'] = name
            # Reset to the first emitter whenever the effect changes
            obj.inu.particle_emitter_index = 0
            try:
                _populate_particle_props_from_fxp(obj, name, 0)
            except Exception as e:
                print(f"[2DFX Particle] populate failed: {e}")
            try:
                from .ops.fx_preview import update_particle_preview
                update_particle_preview(obj)
            except Exception as e:
                print(f"[2DFX Particle] preview update failed: {e}")


def _sample_particle_from_emitter(em) -> dict:
    """Sample the editable particle parameters from a FXEmitter.

    Returns a dict with exactly the fields that our editor exposes, in the
    same shape/units as obj.inu.particle_*. Used both to populate from FXP
    and to detect user edits on save (so we only write changed fields).
    """
    tex_raw = (em.base_get('TEXTURE') or '').strip()
    tex = "" if tex_raw == 'NULL' else tex_raw
    try:
        src_blend = int(em.base_get('SRCBLENDID') or 4)
    except (TypeError, ValueError):
        src_blend = 4
    try:
        dst_blend = int(em.base_get('DSTBLENDID') or 5)
    except (TypeError, ValueError):
        dst_blend = 5

    def _curve(info_type, field, default=0.0, t=0.0):
        info = em.info(info_type)
        if not info:
            return default
        c = info.curves.get(field)
        if not c:
            return default
        return c.sample(t)

    def _rgba(t):
        return (
            max(min(_curve('COLOUR', 'RED', 255.0, t) / 255.0, 1.0), 0.0),
            max(min(_curve('COLOUR', 'GREEN', 255.0, t) / 255.0, 1.0), 0.0),
            max(min(_curve('COLOUR', 'BLUE', 255.0, t) / 255.0, 1.0), 0.0),
            max(min(_curve('COLOUR', 'ALPHA', 255.0, t) / 255.0, 1.0), 0.0),
        )

    # Detect a middle COLOUR keyframe: any COLOUR curve with > 2 keys.
    # Use the ALPHA curve's middle keyframe time as the canonical mid_time
    # (alpha is usually where fade-in/fade-out lives).
    colour = em.info('COLOUR')
    mid_enabled = False
    mid_time = 0.5
    if colour is not None:
        for name in ('ALPHA', 'RED', 'GREEN', 'BLUE'):
            c = colour.curves.get(name)
            if c is not None and len(c.keys) >= 3:
                mid_enabled = True
                if name == 'ALPHA':
                    mid_idx = len(c.keys) // 2
                    mid_time = max(0.01, min(c.keys[mid_idx].time, 0.99))
                    break

    return {
        'texture': tex,
        'src_blend': src_blend,
        'dst_blend': dst_blend,
        'color_start': _rgba(0.0),
        'color_end': _rgba(1.0),
        'color_mid_enabled': mid_enabled,
        'color_mid': _rgba(mid_time),
        'color_mid_time': mid_time,
        'size_start': max(_curve('SIZE', 'SIZEX', 0.3, 0.0), 0.0),
        'size_end': max(_curve('SIZE', 'SIZEX', 0.5, 1.0), 0.0),
        'life': max(_curve('EMLIFE', 'LIFE', 1.0, 0.0), 0.0),
        'life_bias': max(_curve('EMLIFE', 'BIAS', 0.0, 0.0), 0.0),
        'rate': max(_curve('EMRATE', 'RATE', 10.0, 0.0), 0.0),
        'speed': max(_curve('EMSPEED', 'SPEED', 1.0, 0.0), 0.0),
        'speed_bias': max(_curve('EMSPEED', 'BIAS', 0.0, 0.0), 0.0),
        'direction': (
            _curve('EMDIR', 'DIRX', 0.0, 0.0),
            _curve('EMDIR', 'DIRY', 0.0, 0.0),
            _curve('EMDIR', 'DIRZ', 1.0, 0.0),
        ),
        # Extended emission
        'angle_min': _curve('EMANGLE', 'MIN', 0.0, 0.0),
        'angle_max': _curve('EMANGLE', 'MAX', 0.0, 0.0),
        # EMSIZE as half-extent: half the min→max range per axis.
        # This loses any offset from origin but keeps the box size,
        # which is all that Box UI needs. Save always writes symmetric.
        'volume': (
            max(
                abs(_curve('EMSIZE', 'SIZEMAXX', 0.0, 0.0)),
                abs(_curve('EMSIZE', 'SIZEMINX', 0.0, 0.0)),
            ),
            max(
                abs(_curve('EMSIZE', 'SIZEMAXY', 0.0, 0.0)),
                abs(_curve('EMSIZE', 'SIZEMINY', 0.0, 0.0)),
            ),
            max(
                abs(_curve('EMSIZE', 'SIZEMAXZ', 0.0, 0.0)),
                abs(_curve('EMSIZE', 'SIZEMINZ', 0.0, 0.0)),
            ),
        ),
        'offset': (
            _curve('EMPOS', 'X', 0.0, 0.0),
            _curve('EMPOS', 'Y', 0.0, 0.0),
            _curve('EMPOS', 'Z', 0.0, 0.0),
        ),
        'rotation_min': _curve('EMROTATION', 'ANGLEMIN', 0.0, 0.0),
        'rotation_max': _curve('EMROTATION', 'ANGLEMAX', 0.0, 0.0),
        # Physics
        'force': (
            _curve('FORCE', 'FORCEX', 0.0, 0.0),
            _curve('FORCE', 'FORCEY', 0.0, 0.0),
            _curve('FORCE', 'FORCEZ', 0.0, 0.0),
        ),
        'friction': _curve('FRICTION', 'FRICTION', 0.0, 0.0),
        'wind': _curve('WIND', 'WINDFACTOR', 0.0, 0.0),
        'noise': _curve('NOISE', 'NOISE', 0.0, 0.0),
        'jitter': _curve('JITTER', 'JITTERFACTOR', 0.0, 0.0),
        'rotspeed_min': _curve('ROTSPEED', 'MINCW', 0.0, 0.0),
        'rotspeed_max': _curve('ROTSPEED', 'MAXCW', 0.0, 0.0),
        'ground_bounce': _curve('GROUNDCOLLIDE', 'BOUNCE', 0.0, 0.0),
        'ground_speedmult': _curve('GROUNDCOLLIDE', 'SPEEDMULT', 1.0, 0.0),
    }


def _get_effect_emitter_count(effect_name: str) -> int:
    """Return number of emitters in a named system, or 0 on any failure."""
    try:
        game_root = bpy.path.abspath(
            getattr(bpy.context.scene, 'gtatools_game_root', '') or ''
        )
        if not game_root:
            return 0
        fxp_path = os.path.join(game_root, 'models', 'effects.fxp')
        if not os.path.isfile(fxp_path):
            return 0
        from .core import fxp as _fxp
        fxf = _fxp.load_cached(fxp_path)
        system = fxf.find(effect_name)
        return len(system.emitters) if system else 0
    except Exception:
        return 0


def _populate_particle_props_from_fxp(obj, effect_name: str, emitter_index: int = 0) -> bool:
    """Copy the Nth emitter's parameters from effects.fxp onto obj.inu."""
    game_root = bpy.path.abspath(
        getattr(bpy.context.scene, 'gtatools_game_root', '') or ''
    )
    if not game_root:
        return False
    fxp_path = os.path.join(game_root, 'models', 'effects.fxp')
    if not os.path.isfile(fxp_path):
        return False

    from .core import fxp as _fxp
    fxf = _fxp.load_cached(fxp_path)
    system = fxf.find(effect_name)
    if system is None or not system.emitters:
        return False

    idx = max(0, min(emitter_index, len(system.emitters) - 1))
    vals = _sample_particle_from_emitter(system.emitters[idx])
    inu = obj.inu
    inu.particle_texture = vals['texture']
    inu.particle_src_blend = vals['src_blend']
    inu.particle_dst_blend = vals['dst_blend']
    inu.particle_color_start = vals['color_start']
    inu.particle_color_end = vals['color_end']
    inu.particle_color_mid_enabled = vals['color_mid_enabled']
    inu.particle_color_mid = vals['color_mid']
    inu.particle_color_mid_time = vals['color_mid_time']
    inu.particle_size_start = vals['size_start']
    inu.particle_size_end = vals['size_end']
    inu.particle_life = vals['life']
    inu.particle_life_bias = vals['life_bias']
    inu.particle_rate = vals['rate']
    inu.particle_speed = vals['speed']
    inu.particle_speed_bias = vals['speed_bias']
    inu.particle_direction = vals['direction']

    # Extended emission
    inu.particle_angle_min = vals['angle_min']
    inu.particle_angle_max = vals['angle_max']
    inu.particle_volume = vals['volume']
    inu.particle_offset = vals['offset']
    inu.particle_rotation_min = vals['rotation_min']
    inu.particle_rotation_max = vals['rotation_max']

    # Physics
    inu.particle_force = vals['force']
    inu.particle_friction = vals['friction']
    inu.particle_wind = vals['wind']
    inu.particle_noise = vals['noise']
    inu.particle_jitter = vals['jitter']
    inu.particle_rotspeed_min = vals['rotspeed_min']
    inu.particle_rotspeed_max = vals['rotspeed_max']
    inu.particle_ground_bounce = vals['ground_bounce']
    inu.particle_ground_speedmult = vals['ground_speedmult']

    # System-level settings from FX_SYSTEM_DATA header
    try:
        inu.particle_sys_length = float(system.header_get('LENGTH') or 1.0)
    except ValueError:
        pass
    try:
        inu.particle_sys_playmode = int(system.header_get('PLAYMODE') or 2)
    except ValueError:
        pass
    try:
        inu.particle_sys_culldist = float(system.header_get('CULLDIST') or 50.0)
    except ValueError:
        pass

    return True


_inu_flag_propagating = False


def _make_inu_flag_update(attr_name):
    """Propagate a DFF flag toggle from the active object to all other selected mesh objects.

    Only fires when the user edits the flag on the active object's panel — guards against
    recursion and against runs from import/export where properties are set programmatically
    on non-active objects.
    """
    def _update(self, context):
        global _inu_flag_propagating
        if _inu_flag_propagating:
            return
        active = context.active_object
        if not active or self.id_data != active:
            return
        selected = [o for o in context.selected_objects
                    if o.type == 'MESH' and o != active and hasattr(o, 'inu')]
        if not selected:
            return
        value = getattr(self, attr_name)
        _inu_flag_propagating = True
        try:
            for obj in selected:
                if getattr(obj.inu, attr_name) != value:
                    setattr(obj.inu, attr_name, value)
        finally:
            _inu_flag_propagating = False
    return _update


class INUObjectProps(bpy.types.PropertyGroup):
    """INU_tools object export properties (replaces DragonFF obj.dff)."""

    type : EnumProperty(
        items=[
            ('OBJ', 'Object', 'Object will be exported as a mesh or a dummy'),
            ('COL', 'Collision Object', 'Object is a collision object'),
            ('SHA', 'Shadow Object', 'Object is a shadow object'),
            ('2DFX', '2DFX Effect', 'Object is a 2DFX effect (light, particle, etc.)'),
            ('NON', "Don't export", 'Object will NOT be exported'),
        ],
        name="Type",
        default='OBJ',
    )

    effect_2dfx : EnumProperty(
        items=[
            ('LIGHT', 'Свет', 'Street light / neon / corona effect'),
            ('PARTICLE', 'Частица', 'Particle effect (smoke, fire, etc.)'),
            ('PED_ATTRACTOR', 'Ped Attractor', 'Ped attractor point (ATM, bench, etc.)'),
            ('SUN_GLARE', 'Sun Glare', 'Sun glare reflection on surface'),
        ],
        name="2DFX Effect Type",
        default='LIGHT',
    )

    particle_effect_2dfx : EnumProperty(
        name="Particle Effect",
        description=T("Имя эффекта из effects.fxp"),
        items=_particle_effect_enum_items,
        get=_particle_effect_get,
        set=_particle_effect_set,
    )

    particle_emitter_index : IntProperty(
        name="Emitter Index",
        description=T("Индекс редактируемого эмиттера (для систем с несколькими)"),
        default=0, min=0,
    )

    # ── Curve editor buffer (B1) ── #
    particle_curve_name : StringProperty(
        name="Curve",
        description=T("Редактируемая кривая в формате INFO.FIELD (например SIZE.SIZEX)"),
        default="",
    )
    particle_curve_keys : CollectionProperty(type=INUParticleKeyframe)
    particle_curve_key_index : IntProperty(default=0)

    # ── Particle editable per-instance properties ── #
    # These get populated from effects.fxp when the user picks an effect
    # from the dropdown. All reads for the billboard preview come from
    # these fields (not directly from the FXP file), so edits here are
    # instantly reflected and stored per-object.
    def _update_particle(self, context):
        obj = self.id_data
        if obj and obj.type == 'EMPTY' and self.type == '2DFX' and self.effect_2dfx == 'PARTICLE':
            try:
                from .ops.fx_preview import update_particle_preview
                update_particle_preview(obj)
            except Exception as e:
                print(f"[2DFX Particle] update error: {e}")

    particle_texture : StringProperty(
        name="Texture",
        description=T("Имя спрайта из particle.txd"),
        default="",
        update=_update_particle,
    )
    particle_src_blend : IntProperty(
        name="SRC Blend",
        description="D3D9 source blend factor (4=SRCALPHA, 2=ONE, ...)",
        default=4, min=0, max=17,
        update=_update_particle,
    )
    particle_dst_blend : IntProperty(
        name="DST Blend",
        description="D3D9 dest blend factor (5=INVSRCALPHA, 2=ONE for additive)",
        default=5, min=0, max=17,
        update=_update_particle,
    )
    particle_color_start : FloatVectorProperty(
        name="Color (start)",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
        update=_update_particle,
    )
    particle_color_end : FloatVectorProperty(
        name="Color (end)",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 0.0),
        update=_update_particle,
    )
    particle_color_mid_enabled : BoolProperty(
        name="Use middle colour",
        description=T("Добавить промежуточный ключ для плавного fade-in/fade-out"),
        default=False,
        update=_update_particle,
    )
    particle_color_mid : FloatVectorProperty(
        name="Color (mid)",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0),
        update=_update_particle,
    )
    particle_color_mid_time : FloatProperty(
        name="Mid time",
        description=T("Позиция промежуточного ключа по времени жизни (0..1)"),
        default=0.5, min=0.01, max=0.99, precision=3,
        update=_update_particle,
    )
    particle_size_start : FloatProperty(
        name="Size (start)",
        description=T("Размер частицы в начале жизни"),
        default=0.3, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_size_end : FloatProperty(
        name="Size (end)",
        description=T("Размер частицы в конце жизни"),
        default=0.5, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_life : FloatProperty(
        name="Life",
        description=T("Длительность жизни частицы в секундах"),
        default=1.0, min=0.0, soft_max=30.0, precision=3,
        update=_update_particle,
    )
    particle_rate : FloatProperty(
        name="Rate",
        description=T("Количество частиц в секунду"),
        default=10.0, min=0.0, soft_max=1000.0,
        update=_update_particle,
    )
    particle_speed : FloatProperty(
        name="Speed",
        description=T("Начальная скорость частицы"),
        default=1.0, min=0.0, soft_max=100.0, precision=3,
        update=_update_particle,
    )
    particle_direction : FloatVectorProperty(
        name="Direction",
        description=T("Направление эмиссии"),
        size=3,
        default=(0.0, 0.0, 1.0),
        update=_update_particle,
    )

    # ── System-level settings (FX_SYSTEM_DATA header) ── #
    particle_sys_length : FloatProperty(
        name="System Length",
        description=T("LENGTH — длительность цикла системы в секундах"),
        default=1.0, min=0.0, soft_max=100.0, precision=3,
        update=_update_particle,
    )
    particle_sys_playmode : IntProperty(
        name="Play Mode",
        description=T("PLAYMODE — режим проигрывания (0-3)"),
        default=2, min=0, max=3,
        update=_update_particle,
    )
    particle_sys_culldist : FloatProperty(
        name="Cull Distance",
        description=T("CULLDIST — расстояние отсечения эффекта в игре"),
        default=50.0, min=0.0, soft_max=500.0, precision=1,
        update=_update_particle,
    )

    # ── Extended emission (EMANGLE / EMSIZE / EMPOS / EMROTATION / biases) ── #
    particle_angle_min : FloatProperty(
        name="Angle Min",
        description=T("EMANGLE MIN — минимальный угол конуса эмиссии"),
        default=0.0, min=0.0, soft_max=180.0, precision=2,
        update=_update_particle,
    )
    particle_angle_max : FloatProperty(
        name="Angle Max",
        description=T("EMANGLE MAX — максимальный угол конуса эмиссии"),
        default=0.0, min=0.0, soft_max=180.0, precision=2,
        update=_update_particle,
    )
    # Box as half-extents — symmetric around the emitter. On save this
    # becomes SIZEMIN=-box, SIZEMAX=+box per axis in the FXP EMSIZE block.
    particle_volume : FloatVectorProperty(
        name="Box",
        description=T("EMSIZE половина размера бокса эмиссии (centered)"),
        size=3,
        default=(0.0, 0.0, 0.0),
        min=0.0, precision=3,
        update=_update_particle,
    )
    # Legacy storage — kept for back-compat with older blend files, not in UI
    particle_volume_radius : FloatProperty(
        name="Volume Radius (legacy)",
        default=0.0, min=0.0, precision=3,
    )
    particle_volume_min : FloatVectorProperty(
        name="Volume Min (legacy)",
        size=3, default=(0.0, 0.0, 0.0), precision=3,
    )
    particle_offset : FloatVectorProperty(
        name="Offset",
        description=T("EMPOS X/Y/Z — смещение точки спавна"),
        size=3,
        default=(0.0, 0.0, 0.0),
        precision=3,
        update=_update_particle,
    )
    particle_rotation_min : FloatProperty(
        name="Rotation Min",
        description=T("EMROTATION ANGLEMIN — мин начальный поворот спрайта"),
        default=0.0, soft_min=-360.0, soft_max=360.0,
        update=_update_particle,
    )
    particle_rotation_max : FloatProperty(
        name="Rotation Max",
        description=T("EMROTATION ANGLEMAX — макс начальный поворот спрайта"),
        default=0.0, soft_min=-360.0, soft_max=360.0,
        update=_update_particle,
    )
    particle_life_bias : FloatProperty(
        name="Life Bias",
        description=T("EMLIFE BIAS — случайный разброс длительности жизни"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_speed_bias : FloatProperty(
        name="Speed Bias",
        description=T("EMSPEED BIAS — случайный разброс начальной скорости"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )

    # ── Physics (FORCE / FRICTION / WIND / NOISE / JITTER / ROTSPEED / GROUNDCOLLIDE) ── #
    particle_force : FloatVectorProperty(
        name="Force",
        description=T("FORCE X/Y/Z — постоянное ускорение (например -9.8 по Z = гравитация)"),
        size=3,
        default=(0.0, 0.0, 0.0),
        precision=3,
        update=_update_particle,
    )
    particle_friction : FloatProperty(
        name="Friction",
        description=T("FRICTION — сопротивление воздуха"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_wind : FloatProperty(
        name="Wind",
        description=T("WIND WINDFACTOR — восприимчивость к ветру игры"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_noise : FloatProperty(
        name="Noise",
        description=T("NOISE — сглаженное случайное движение"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_jitter : FloatProperty(
        name="Jitter",
        description=T("JITTER JITTERFACTOR — резкий случайный дёрг"),
        default=0.0, min=0.0, soft_max=10.0, precision=3,
        update=_update_particle,
    )
    particle_rotspeed_min : FloatProperty(
        name="RotSpeed Min",
        description=T("ROTSPEED MINCW — мин скорость вращения спрайта"),
        default=0.0, soft_min=-360.0, soft_max=360.0,
        update=_update_particle,
    )
    particle_rotspeed_max : FloatProperty(
        name="RotSpeed Max",
        description=T("ROTSPEED MAXCW — макс скорость вращения спрайта"),
        default=0.0, soft_min=-360.0, soft_max=360.0,
        update=_update_particle,
    )
    particle_ground_bounce : FloatProperty(
        name="Ground Bounce",
        description=T("GROUNDCOLLIDE BOUNCE — сила отскока при ударе о землю"),
        default=0.0, min=0.0, soft_max=2.0, precision=3,
        update=_update_particle,
    )
    particle_ground_speedmult : FloatProperty(
        name="Ground SpeedMult",
        description=T("GROUNDCOLLIDE SPEEDMULT — потеря скорости при ударе"),
        default=1.0, min=0.0, soft_max=2.0, precision=3,
        update=_update_particle,
    )

    def _update_2dfx_preview(self, context):
        obj = self.id_data  # owner Object
        if obj and obj.type == 'EMPTY' and self.type == '2DFX' and self.effect_2dfx == 'LIGHT':
            try:
                from .ops.fx_preview import sync_preview_from_props
                sync_preview_from_props(obj)
            except Exception as e:
                print(f"[2DFX] Preview update error: {e}")

    color_2dfx : FloatVectorProperty(
        name="2DFX Color",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(1.0, 1.0, 0.784, 1.0),
        description=T("Цвет короны и света"),
        update=_update_2dfx_preview,
    )

    preset_2dfx : EnumProperty(
        items=[
            ('DEFAULT', 'Default', 'Default light settings'),
            ('ONALLDAY', 'OnAllDay', 'Always visible light'),
            ('LAMP_POST', 'Lamp Post', 'Standard lamp post'),
            ('LAMP_POST_COAST', 'Lamp Post Coast', 'Coastal lamp post (warm)'),
            ('BB_PICKUP', 'BB Pickup', 'Red pickup marker'),
            ('FLASHING_MAV1', 'Flashing (Maverick1)', 'Red blinking helicopter light'),
            ('FLASHING_MAV2', 'Flashing (Maverick2)', 'Green blinking helicopter light'),
            ('FLASHING_TUG', 'Flashing (Tug)', 'Orange blinking tug light'),
            ('TRAIN_CROSSING', 'Train Crossing', 'Red blinking train crossing'),
            ('TRAFFIC', 'Traffic', 'Traffic light'),
        ],
        name="2DFX Preset",
        default='DEFAULT',
    )

    def _update_2dfx_texture(self, context):
        """Recreate preview when texture changes."""
        obj = self.id_data
        if obj and obj.type == 'EMPTY' and self.type == '2DFX' and self.effect_2dfx == 'LIGHT':
            try:
                from .ops.fx_preview import remove_preview_children, create_light_preview
                remove_preview_children(obj)
                create_light_preview(obj)
            except Exception as e:
                print(f"[2DFX] Texture update error: {e}")

    corona_tex_2dfx : EnumProperty(
        items=[
            ('coronastar', 'coronastar', ''),
            ('coronamoon', 'coronamoon', ''),
            ('coronaringb', 'coronaringb', ''),
            ('coronareflect', 'coronareflect', ''),
            ('coronaheadlightline', 'coronaheadlightline', ''),
            ('headlight', 'headlight', ''),
            ('headlight1', 'headlight1', ''),
            ('lockon', 'lockon', ''),
            ('lockonFire', 'lockonFire', ''),
            ('lunar', 'lunar', ''),
            ('roadsignfont', 'roadsignfont', ''),
            ('particleskid', 'particleskid', ''),
            ('finishFlag', 'finishFlag', ''),
            ('handman', 'handman', ''),
            ('seabd32', 'seabd32', ''),
            ('shad_exp', 'shad_exp', ''),
            ('shad_car', 'shad_car', ''),
            ('shad_bike', 'shad_bike', ''),
            ('shad_heli', 'shad_heli', ''),
            ('shad_ped', 'shad_ped', ''),
            ('shad_rcbaron', 'shad_rcbaron', ''),
            ('lamp_shad_64', 'lamp_shad_64', ''),
            ('bloodpool_64', 'bloodpool_64', ''),
            ('target256', 'target256', ''),
            ('white', 'white', ''),
            ('cloud1', 'cloud1', ''),
            ('cloudhigh', 'cloudhigh', ''),
            ('cloudmasked', 'cloudmasked', ''),
            ('carfx1', 'carfx1', ''),
            ('wincrack_32', 'wincrack_32', ''),
            ('waterclear256', 'waterclear256', ''),
            ('waterwake', 'waterwake', ''),
            ('txgrassbig0', 'txgrassbig0', ''),
            ('txgrassbig1', 'txgrassbig1', ''),
        ],
        name="Corona Texture",
        default='coronastar',
        update=_update_2dfx_texture,
    )

    shadow_tex_2dfx : EnumProperty(
        items=[
            ('shad_exp', 'shad_exp', ''),
            ('shad_car', 'shad_car', ''),
            ('shad_bike', 'shad_bike', ''),
            ('shad_heli', 'shad_heli', ''),
            ('shad_ped', 'shad_ped', ''),
            ('shad_rcbaron', 'shad_rcbaron', ''),
            ('lamp_shad_64', 'lamp_shad_64', ''),
            ('bloodpool_64', 'bloodpool_64', ''),
            ('coronastar', 'coronastar', ''),
            ('coronamoon', 'coronamoon', ''),
            ('coronaringb', 'coronaringb', ''),
            ('coronareflect', 'coronareflect', ''),
            ('white', 'white', ''),
        ],
        name="Shadow Texture",
        default='shad_exp',
    )

    show_mode_2dfx : EnumProperty(
        items=[
            ('0', '0 DEFAULT', 'Default behavior'),
            ('1', '1 RANDOM_FLASHING', 'Random flashing'),
            ('2', '2 FLASH_RAIN', 'Flashing when raining'),
            ('3', '3 ONLY_RAIN', 'Only visible in rain'),
            ('4', '4 NO_RAIN', 'Not visible in rain'),
            ('5', '5 FLASH_5', 'Flashing variant 2'),
        ],
        name="Show Mode",
        default='0',
    )

    flare_type_2dfx : EnumProperty(
        items=[
            ('0', '0 None', 'No lens flare'),
            ('1', '1 Type 1', 'Lens flare style 1'),
            ('2', '2 Type 2', 'Lens flare style 2'),
            ('3', '3 Type 3', 'Lens flare style 3'),
        ],
        name="Flare Type",
        default='0',
    )

    pipeline : EnumProperty(
        items=[
            ('NONE', 'None',
             T("Без указания pipeline — использовать стандартный рендер RenderWare. Подходит для простых объектов, которым не нужны специальные эффекты движка")),
            ('0x53F2009A', 'Vehicle',
             T("Pipeline кузова машины (RSPIPE_PC_CustomCarEnvMap). Добавляет env-map отражения неба/облаков/улицы. Используется совместно с текстурами vehicleenv128 + vehiclespecdot64 на материале")),
            ('0x53F20098', 'Day/Night',
             T("Pipeline здания с day/night vertex colors (RSPIPE_PC_CustomBuildingDN). Движок плавно смешивает дневной и ночной слои vertex colors по игровому времени. Требует ДВА Color Attribute слоя (Day + Night) на меше. Mesh-флаги Day/Night здесь не нужны — переход делает pipeline через VC")),
            ('0x53F2009C', 'Building',
             T("Простой pipeline здания (RSPIPE_PC_CustomBuilding). Статическое освещение через один слой vertex colors. Работает быстрее чем Day/Night, но нет смены по времени суток")),
            ('CUSTOM', 'Custom Pipeline',
             T("Указать произвольное значение pipeline ID через поле Custom Pipeline")),
        ],
        name="Pipeline",
        description=T("Рендер-пайплайн движка"),
    )
    custom_pipeline : StringProperty(name="Custom Pipeline")

    export_normals : BoolProperty(
        default=True,
        description=T("Экспорт нормалей вершин (отключить для map объектов)"),
        update=_make_inu_flag_update("export_normals"),
    )
    export_binsplit : BoolProperty(
        default=True,
        description=T("Экспорт Bin Mesh PLG (совместимость с просмотрщиками DFF)"),
        update=_make_inu_flag_update("export_binsplit"),
    )

    uv_map1 : BoolProperty(default=True, description=T("Экспорт первой UV карты"), update=_make_inu_flag_update("uv_map1"))
    uv_map2 : BoolProperty(default=True, description=T("Экспорт второй UV карты"), update=_make_inu_flag_update("uv_map2"))
    day_cols : BoolProperty(default=True, description=T("Экспорт дневных vertex colors"), update=_make_inu_flag_update("day_cols"))
    night_cols : BoolProperty(default=True, description=T("Экспорт ночных vertex colors"), update=_make_inu_flag_update("night_cols"))

    light : BoolProperty(default=True, description=T("Флаг rpGEOMETRYLIGHT — динамическое освещение"), update=_make_inu_flag_update("light"))
    modulate_color : BoolProperty(default=True, description=T("Флаг rpGEOMETRYMODULATEMATERIALCOLOR — цвет материала влияет на модель"), update=_make_inu_flag_update("modulate_color"))
    set_material_alpha : BoolProperty(default=True, description=T("Автоматически ставить material alpha = 254 при наличии vertex alpha < 255.\nНужно для стандартных прозрачных мешей (стёкла, дым). Выключи если материал должен остаться opaque"), update=_make_inu_flag_update("set_material_alpha"))
    light_beam_asi : BoolProperty(default=False, description=T("Помечает меш как объёмный луч света для плагина SA_Light.asi.\nУстанавливает material color = (254,254,254,254) — этот маркер плагин ищет во время рендера.\n\nТРЕБУЕТ SA_Light.asi в корне GTA SA. Без плагина меш будет рендериться как обычный полупрозрачный объект с жёстким срезом alpha.\n\nДля использования:\n1. Собери меш-конус/куб формой луча\n2. Покрась vertex colors как хочешь (любые значения alpha)\n3. Включи этот флаг + Set Material Alpha выключи\n4. Экспорт → плагин автоматически включит плавный alpha blend на этом меше"), update=_make_inu_flag_update("light_beam_asi"))

    # ── IDE / IPL properties ──
    model_id : IntProperty(
        name="Model ID",
        default=0,
        min=0,
        description=T("ID модели в GTA SA (IDE/IPL)"),
    )
    txd_name : StringProperty(
        name="TXD Name",
        default="",
        description=T("Имя словаря текстур (IDE). По умолчанию = имя модели"),
    )
    col_name : StringProperty(
        name="COL Library",
        default="",
        description=T("Имя .col-библиотеки в которой хранится коллизия модели. Заполняется автоматически при Map Import (= имя исходного .col файла). При Map Export DFF группируются в одну .col-библиотеку по совпадающему col_name. Пусто → fallback на txd_name, затем на имя модели"),
    )
    lod_object : PointerProperty(
        type=bpy.types.Object,
        name="LOD partner",
        description=T("LOD-модель этой DFF — заполняется автоматически при Map Import из IPL lod_index. При Map Export пересчитывается в lod_index = позицию LOD-инстанса в выходном IPL. Пусто = модель не имеет LOD"),
    )
    real_interior : IntProperty(
        name="Real Interior (FLA)",
        default=0,
        min=0,
        description=T("Fastman92 Limit Adjuster: 12-я колонка `realInterior` в IPL inst. Обычная SA читает только 11 колонок — это поле игнорируется без FLA. Пусто (0) = не использовать. Включить запись 12-й колонки можно в Map Export → FLA Extended IPL"),
    )
    draw_distance : FloatProperty(
        name="Draw Distance",
        default=299.0,
        min=0.0,
        description=T("Дальность прорисовки объекта (IDE)"),
    )
    lod_draw_distance : FloatProperty(
        name="LOD Distance",
        default=999.0,
        min=0.0,
        description=T("Дальность прорисовки LOD модели (IDE)"),
    )
    ide_flags : IntProperty(
        name="IDE Flags",
        default=0,
        min=0,
        description=T("Флаги объекта в IDE"),
    )

    # Breakable object extension (chunk 0x253F2FD)
    breakable : BoolProperty(
        name="Breakable Object",
        description=T("Пометить геометрию как разрушаемую (пишет чанк 0x253F2FD в DFF)"),
        default=False,
    )
    breakable_force : FloatProperty(
        name="Break Force",
        description=T("Сила, нужная чтобы сломать объект (умолчание 1.0)"),
        default=1.0, min=0.0,
    )

    # IDE flag checkboxes with auto-sync to ide_flags
    def _update_ide_flag(self, context):
        _FLAG_BITS = [
            ('flag_is_road', 1), ('flag_draw_last', 4), ('flag_additive', 8),
            ('flag_no_zbuffer', 64), ('flag_no_shadows', 128),
            ('flag_glass_1', 512), ('flag_glass_2', 1024),
            ('flag_garage_door', 2048), ('flag_damagable', 4096),
            ('flag_is_tree', 8192), ('flag_is_palm', 16384),
            ('flag_no_flyer_col', 32768), ('flag_is_tag', 1048576),
            ('flag_no_backface', 2097152), ('flag_breakable', 4194304),
        ]
        val = 0
        for prop, bit in _FLAG_BITS:
            if getattr(self, prop, False):
                val |= bit
        self['ide_flags'] = val

    flag_is_road : BoolProperty(name="IS_ROAD", description=T("Дорога (1)"), default=False, update=_update_ide_flag)
    flag_draw_last : BoolProperty(name="DRAW_LAST", description=T("Прозрачный, рисовать последним (4)"), default=False, update=_update_ide_flag)
    flag_additive : BoolProperty(name="ADDITIVE", description=T("Аддитивный блендинг (8)"), default=False, update=_update_ide_flag)
    flag_no_zbuffer : BoolProperty(name="NO_ZBUFFER_WRITE", description=T("Не писать в Z-буфер (64)"), default=False, update=_update_ide_flag)
    flag_no_shadows : BoolProperty(name="NO_SHADOWS", description=T("Не получать тени (128)"), default=False, update=_update_ide_flag)
    flag_glass_1 : BoolProperty(name="GLASS_TYPE_1", description=T("Стекло разбиваемое (512)"), default=False, update=_update_ide_flag)
    flag_glass_2 : BoolProperty(name="GLASS_TYPE_2", description=T("Стекло с трещинами (1024)"), default=False, update=_update_ide_flag)
    flag_garage_door : BoolProperty(name="GARAGE_DOOR", description=T("Дверь гаража (2048)"), default=False, update=_update_ide_flag)
    flag_damagable : BoolProperty(name="DAMAGABLE", description=T("Разрушаемый (4096)"), default=False, update=_update_ide_flag)
    flag_is_tree : BoolProperty(name="IS_TREE", description=T("Дерево, качается на ветру (8192)"), default=False, update=_update_ide_flag)
    flag_is_palm : BoolProperty(name="IS_PALM", description=T("Пальма, качается на ветру (16384)"), default=False, update=_update_ide_flag)
    flag_no_flyer_col : BoolProperty(name="NO_FLYER_COL", description=T("Нет коллизии с летающим (32768)"), default=False, update=_update_ide_flag)
    flag_is_tag : BoolProperty(name="IS_TAG", description=T("Граффити тег (1048576)"), default=False, update=_update_ide_flag)
    flag_no_backface : BoolProperty(name="NO_BACKFACE_CULL", description=T("Рисовать обе стороны (2097152)"), default=False, update=_update_ide_flag)
    flag_breakable : BoolProperty(name="BREAKABLE_STATUE", description=T("Разрушаемая статуя (4194304)"), default=False, update=_update_ide_flag)
    interior_id : IntProperty(
        name="Interior ID",
        default=0,
        min=0,
        description=T("ID интерьера для IPL (0 = экстерьер)"),
    )
    lod_index : IntProperty(
        name="LOD Index",
        default=-1,
        description=T("Индекс LOD модели в IPL (-1 = нет LOD)"),
    )

    # Collision sphere/cone properties
    col_material : IntProperty(default=12, description=T("Материал для Sphere/Cone"))
    col_flags : IntProperty(default=0, description=T("Флаги для Sphere/Cone"))
    col_brightness : IntProperty(default=0, description=T("Яркость для Sphere/Cone"))
    col_light : IntProperty(default=0, description=T("Свет для Sphere/Cone"))


# GTA SA vehicle color slot → magic RGB marker value.
# Движок SA сканирует material.color.rgb, и если находит одно из магических значений
# — подставляет цвет из carcols.dat для нужного слота кузова/огня.
# Значения взяты из Kam's GTA_Material.ms (colhprIdx).
_VEHICLE_COLOR_SLOTS = {
    'NONE':    None,
    'PRIMARY':    (60,  255, 0),
    'SECONDARY':  (255, 0,   175),
    'THIRD':      (0,   255, 255),
    'FOURTH':     (255, 0,   255),
    'HL_LEFT':    (255, 175, 0),
    'HL_RIGHT':   (0,   255, 200),
    'TL_LEFT':    (185, 255, 0),
    'TL_RIGHT':   (255, 60,  0),
}

def _on_vehicle_color_slot_update(self, context):
    """При выборе слота красим базовый цвет материала в магическое RGB,
    по которому движок SA найдёт соответствующий carcols-цвет."""
    rgb = _VEHICLE_COLOR_SLOTS.get(self.vehicle_color_slot)
    if rgb is None:
        return
    mat = getattr(self, 'id_data', None)
    if mat is None:
        return
    # Устанавливаем diffuse color в Principled BSDF + material.diffuse_color
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    try:
        mat.diffuse_color = (r, g, b, 1.0)
    except Exception:
        pass
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bc = node.inputs.get('Base Color')
                if bc is not None:
                    bc.default_value = (r, g, b, 1.0)
                break


class INUMaterialProps(bpy.types.PropertyGroup):
    """INU_tools material properties (replaces DragonFF mat.dff)."""

    # UI state — which tab is active in the unified Material panel.
    material_tab : EnumProperty(
        name="Material Tab",
        items=[
            ('SURFACE',  "Surface",  T("COL Surface Type — тип физической поверхности и Day/Night Light")),
            ('EFFECTS',  "Effects",  T("RW-эффекты материала: env map, bump, specular, reflection, dual texture, UV anim")),
            ('PIPELINE', "Pipeline", T("Пресеты материала и сводка активных эффектов")),
        ],
        default='SURFACE',
    )

    ambient : FloatProperty(name="Ambient Shading", default=1.0)

    # Vehicle color slot — только для машин (GTA SA)
    vehicle_color_slot : EnumProperty(
        name="Vehicle Color Slot",
        description=T("Слот цвета машины: движок SA подставит цвет из carcols.dat. Меняет базовый RGB материала на магическую метку."),
        items=[
            ('NONE',      "None",           T("Обычный материал, не связан с carcols")),
            ('PRIMARY',   "Primary",        T("Основной цвет (первый в carcols.dat)")),
            ('SECONDARY', "Secondary",      T("Второй цвет")),
            ('THIRD',     "Third color",    T("Третий цвет (некоторые машины)")),
            ('FOURTH',    "Fourth color",   T("Четвёртый цвет")),
            ('HL_LEFT',   "Left Headlight", T("Левая фара")),
            ('HL_RIGHT',  "Right Headlight",T("Правая фара")),
            ('TL_LEFT',   "Left Taillight", T("Левый задний фонарь")),
            ('TL_RIGHT',  "Right Taillight",T("Правый задний фонарь")),
        ],
        default='NONE',
        update=_on_vehicle_color_slot_update,
    )

    # Collision surface
    col_mat_index : IntProperty(name="Surface ID", default=0, description=T("ID типа поверхности COL (0-178)"))
    col_flags : IntProperty(name="Flags", default=0)
    col_brightness : IntProperty(name="Brightness", default=0)
    col_light : IntProperty(name="Light", default=0)
    col_day_light : IntProperty(name="Day Light", default=0, min=0, max=15)
    col_night_light : IntProperty(name="Night Light", default=0, min=0, max=15)

    # Environment Map
    export_env_map : BoolProperty(name="Environment Map")
    env_map_tex : StringProperty()
    env_map_coef : FloatProperty(default=0.5)
    env_map_fb_alpha : BoolProperty()

    # Bump Map
    export_bump_map : BoolProperty(name="Bump Map")
    bump_map_tex : StringProperty()

    # Reflection
    export_reflection : BoolProperty(name="Reflection Material")
    reflection_scale_x : FloatProperty()
    reflection_scale_y : FloatProperty()
    reflection_offset_x : FloatProperty()
    reflection_offset_y : FloatProperty()
    reflection_intensity : FloatProperty()

    # Specular
    export_specular : BoolProperty(name="Specular Material")
    specular_level : FloatProperty()
    specular_texture : StringProperty()

    # Dual Texture / Blend Mode
    export_dual_tex : BoolProperty(name="Dual Texture / Blend Mode")
    dual_tex_src_blend : EnumProperty(
        name="Src Blend",
        items=[
            ('1', "Zero", ""),
            ('2', "One", ""),
            ('3', "Src Color", ""),
            ('4', "Inv Src Color", ""),
            ('5', "Src Alpha", ""),
            ('6', "Inv Src Alpha", ""),
            ('7', "Dest Alpha", ""),
            ('8', "Inv Dest Alpha", ""),
            ('9', "Dest Color", ""),
            ('10', "Inv Dest Color", ""),
            ('11', "Src Alpha Sat", ""),
        ],
        default='5',
    )
    dual_tex_dst_blend : EnumProperty(
        name="Dst Blend",
        items=[
            ('1', "Zero", ""),
            ('2', "One", ""),
            ('3', "Src Color", ""),
            ('4', "Inv Src Color", ""),
            ('5', "Src Alpha", ""),
            ('6', "Inv Src Alpha", ""),
            ('7', "Dest Alpha", ""),
            ('8', "Inv Dest Alpha", ""),
            ('9', "Dest Color", ""),
            ('10', "Inv Dest Color", ""),
            ('11', "Src Alpha Sat", ""),
        ],
        default='6',
    )
    dual_tex_texture : StringProperty(name="Dual Texture")

    # UV Animation
    export_animation : BoolProperty(name="UV Animation")
    animation_name : StringProperty()
    # UV Animation written into DFF binary (chunks 0x2B / 0x135)
    uv_anim_write : BoolProperty(
        name="Write UV Anim to DFF",
        description=T("Вписать простую UV-прокрутку в экспортируемый DFF"),
        default=False,
    )
    uv_anim_speed_u : FloatProperty(
        name="Scroll U",
        description=T("Скорость прокрутки UV по U в секунду"),
        default=0.0, precision=4,
    )
    uv_anim_speed_v : FloatProperty(
        name="Scroll V",
        description=T("Скорость прокрутки UV по V в секунду"),
        default=0.0, precision=4,
    )
    uv_anim_duration : FloatProperty(
        name="Duration (s)",
        description=T("Длительность цикла UV-анимации"),
        default=1.0, min=0.01, soft_max=60.0, precision=3,
    )

    # Vehicle Paintjob — alt textures packed into vehicle's TXD with names
    # '<base>_paintjob1' and '<base>_paintjob2', where <base> is the name
    # of this material's main image. The game swaps the active body
    # texture with one of these when the player buys a paintjob in
    # Pay'n'Spray. None on either field = no paintjob shipped.
    paintjob_alt_1 : PointerProperty(
        type=bpy.types.Image,
        name="Paintjob 1",
        description=T(
            "Альтернативная текстура для Pay'n'Spray paintjob 1.\n"
            "Будет упакована в TXD как <base>_paintjob1, где <base> — "
            "имя основной текстуры этого материала."),
    )
    paintjob_alt_2 : PointerProperty(
        type=bpy.types.Image,
        name="Paintjob 2",
        description=T(
            "Альтернативная текстура для Pay'n'Spray paintjob 2.\n"
            "Будет упакована в TXD как <base>_paintjob2."),
    )


class GTATOOLS_ImgFileEntry(bpy.types.PropertyGroup):
    """One file entry in IMG archive list."""
    name: StringProperty()


class GTATOOLS_BinaryIplEntry(bpy.types.PropertyGroup):
    """One binary IPL file found inside an IMG archive — user-selectable
    for inclusion in Build Map / Import Map."""
    name: StringProperty()
    enabled: BoolProperty(
        name="",
        default=True,
        description=T("Включить этот бинарный IPL в сборку карты"),
    )
    img_source: StringProperty()


class GTATOOLS_TxdExportEntry(bpy.types.PropertyGroup):
    """One row in the Export-to-IMG TXD plan popup.

    ``model_name`` is the DFF base name and acts as a lookup key back into
    the scene's model groups; ``txd_name`` is the destination archive name
    (editable per row); ``include`` lets the user drop a row out of the
    batch without affecting the rest of the selection.
    """
    model_name: StringProperty()
    txd_name: StringProperty(
        description=T("Имя TXD архива для этой модели. Модели с одинаковым именем попадут в один .txd (textures merged)"),
    )
    include: BoolProperty(
        name="",
        default=True,
        description=T("Включить модель в экспорт"),
    )


# IMG operators + _refresh_img_entries helper moved to ops/img_ops.py
# in Phase 3 of UI redesign.
from .ops.img_ops import (
    GTATOOLS_OT_refresh_img_list,
    GTATOOLS_OT_extract_resources,
    GTATOOLS_OT_import_from_img,
    GTATOOLS_OT_remove_from_img,
    GTATOOLS_OT_export_to_img,
)


class GTATOOLS_FillColorItem(bpy.types.PropertyGroup):
    """Элемент списка цветов заливки"""
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0)
    )


# =============================================================================
# OPERATORS
# =============================================================================

# Check operators moved to ops/check.py in Phase 3 of UI redesign.
from .ops.check import (
    GTATOOLS_OT_check_geometry,
    GTATOOLS_OT_check_ngons,
    GTATOOLS_OT_clean_geometry,
    GTATOOLS_OT_clear_raw_dff,
)


# Vehicle operators moved to ops/vehicle.py in Phase 3 of UI redesign.
from .ops.vehicle import (
    GTATOOLS_OT_sa_vehicle_preset,
    GTATOOLS_OT_apply_vehicle_pipeline,
)


# DFF/COL/TXD import-export operators moved to ops/* in Phase 3 of UI
# redesign. Each engine module now also owns its Blender operator wrapper.
from .ops.txd_export import (
    GTATOOLS_OT_export_txd,
    GTATOOLS_OT_export_shared_txd,
)
from .ops.dff_export import GTATOOLS_OT_export_dff
from .ops.col_export import GTATOOLS_OT_export_col
from .ops.dff_import import (
    GTATOOLS_OT_import_dff,
    GTATOOLS_OT_drop_dff,
    GTATOOLS_FH_dff_drop,
)
from .ops.col_import import (
    GTATOOLS_OT_import_col,
    GTATOOLS_OT_drop_col,
    GTATOOLS_FH_col_drop,
)
from .ops.txd_import import GTATOOLS_OT_import_txd


def menu_func_export(self, context):
    self.layout.operator(GTATOOLS_OT_inu_export.bl_idname,
                         text="INU Export (.dff/.col/.txd/.ide/.ipl)")


# ── IDE / IPL panel operators ──

def _ide_entry_from_obj(obj, auto_id=False):
    """Build IdeObject from a Blender mesh object."""
    from .core.ide import IdeObject
    inu = getattr(obj, 'inu', None)
    name = _clean_model_name_ide(obj.name)
    model_id = getattr(inu, 'model_id', 0) if inu else 0

    # Auto-assign ID from manager if 0
    if model_id == 0 and auto_id:
        from .data.id_manager import allocate_id
        model_id = allocate_id(name)
        if inu:
            inu.model_id = model_id

    txd_name = getattr(inu, 'txd_name', '') if inu else ''
    if not txd_name:
        txd_name = name
    draw_dist = getattr(inu, 'draw_distance', 300.0) if inu else 300.0
    flags = getattr(inu, 'ide_flags', 0) if inu else 0
    return IdeObject(model_id=model_id, model_name=name,
                     txd_name=txd_name, draw_distance=draw_dist, flags=flags)


def _ipl_entry_from_obj(obj):
    """Build IplInstance from a Blender mesh object."""
    from .core.ipl import IplInstance
    inu = getattr(obj, 'inu', None)
    name = _clean_model_name_ide(obj.name)
    model_id = getattr(inu, 'model_id', 0) if inu else 0
    interior = getattr(inu, 'interior_id', 0) if inu else 0
    lod_index = getattr(inu, 'lod_index', -1) if inu else -1
    real_interior = getattr(inu, 'real_interior', 0) if inu else 0
    loc = obj.matrix_world.translation
    rot = obj.matrix_world.to_quaternion().conjugated()
    return IplInstance(model_id=model_id, model_name=name,
                       interior=interior,
                       pos_x=loc.x, pos_y=loc.y, pos_z=loc.z,
                       rot_x=rot.x, rot_y=rot.y, rot_z=rot.z, rot_w=rot.w,
                       lod_index=lod_index, real_interior=real_interior)


def _clean_model_name_ide(name):
    # Strip Blender duplicate suffix FIRST (.001, .002, etc.)
    if '.' in name:
        b, s = name.rsplit('.', 1)
        if s.isdigit():
            name = b
    class _Mock:
        def __init__(self, n):
            self.name = n
    _, base = get_model_type(_Mock(name))
    return base


# Map auto-discover + binary IPL ops moved to ops/map_ops.py
# in Phase 3 of UI redesign.
from .ops.map_ops import (
    GTATOOLS_OT_discover_game,
    GTATOOLS_OT_binary_ipl_toggle_all,
    GTATOOLS_OT_scan_binary_ipls,
)


# Map viewport/glTF/import ops moved to ops/map_ops.py in Phase 3
# (batch 3b). _bbox_* / _links_* globals + their draw handlers moved
# with the operators. Heavy import_map + replace-with-DFF too.
from .ops.map_ops import (
    GTATOOLS_OT_toggle_links,
    GTATOOLS_OT_toggle_bbox,
    GTATOOLS_OT_load_map_glb,
    GTATOOLS_OT_build_map_glb,
    GTATOOLS_OT_import_map,
    GTATOOLS_OT_replace_fake_with_dff,
)


# IMG operator moved to ops/img_ops.py in Phase 3 of UI redesign.


def _append_export_report(report_path: str, title: str, rows: list[str], max_chars: int = 200000):
    """Append one export run to text log and cap file size."""
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    block = [f"[{title}] {ts}"]
    block.extend(rows if rows else ["- no results"])
    payload = "\n".join(block) + "\n\n"

    try:
        if os.path.isfile(report_path):
            with open(report_path, 'r', encoding='utf-8', errors='replace') as f:
                prev = f.read()
        else:
            prev = ""
    except Exception:
        prev = ""

    merged = prev + payload
    if len(merged) > max_chars:
        merged = merged[-max_chars:]
        first_nl = merged.find('\n')
        if first_nl != -1:
            merged = merged[first_nl + 1:]

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(merged)


# IMG operator moved to ops/img_ops.py in Phase 3 of UI redesign.


# IDE/IPL operators (11 ops) moved to ops/ide_ipl.py in Phase 3 batch 4.
# Helpers _ide_entry_from_obj / _ipl_entry_from_obj / _clean_model_name_ide
# stay below as the single source of truth for INU Import/Export too.
from .ops.ide_ipl import (
    GTATOOLS_OT_upsert_ide,
    GTATOOLS_OT_upsert_ipl,
    GTATOOLS_OT_remove_ide,
    GTATOOLS_OT_remove_ipl,
    GTATOOLS_OT_export_ide,
    GTATOOLS_OT_export_ipl,
    GTATOOLS_OT_import_ipl_sections,
    GTATOOLS_OT_export_ipl_sections,
    GTATOOLS_OT_import_ide,
    GTATOOLS_OT_import_ipl,
    GTATOOLS_OT_replace_ipl_placeholders,
)


def _clean_name_typed_ipl(name):
    class _Mock:
        def __init__(self, n):
            self.name = n
    mt, base = get_model_type(_Mock(name))
    return base, mt or 'OTHER'


# INU Import/Export operators (3 ops) moved to ops/inu_export.py
# in Phase 3 batch 5. Helper _clean_name_typed_ipl stays above as it's
# also used by ops/ide_ipl.py.
from .ops.inu_export import (
    GTATOOLS_OT_inu_import,
    GTATOOLS_OT_export_all,
    GTATOOLS_OT_inu_export,
    menu_func_import,
)


class GTATOOLS_OT_info_tooltip(bpy.types.Operator):
    """"""
    bl_idname = "gtatools.info_tooltip"
    bl_label = ""
    bl_options = {'INTERNAL'}

    tooltip : StringProperty(default="")

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    def execute(self, context):
        return {'CANCELLED'}


def _draw_label_with_info(layout, text, tooltip, icon='NONE'):
    """Draw info icon before label text."""
    row = layout.row(align=True)
    sub = row.row(align=True)
    sub.ui_units_x = 1.3
    op = sub.operator("gtatools.info_tooltip", text="", icon='INFO')
    op.tooltip = tooltip
    row.label(text=text, icon=icon)


# Light/Lightmap/Itera/VertexPaint/Scatter operators moved to
# ops/light_ops.py in Phase 3 batch 6 (38 ops + helpers).
from .ops.light_ops import (
    GTATOOLS_OT_detect_models,
    GTATOOLS_OT_average_colors,
    GTATOOLS_OT_lightmap_generate,
    GTATOOLS_OT_lightmap_copy,
    GTATOOLS_OT_lightmap_clear,
    GTATOOLS_OT_create_prelight_lights,
    GTATOOLS_OT_remove_prelight_lights,
    GTATOOLS_OT_bake_vertex_colors,
    GTATOOLS_OT_bake_vertex_colors_simple,
    GTATOOLS_OT_reset_bake_settings,
    GTATOOLS_OT_reset_scatter_settings,
    GTATOOLS_OT_analyze_vertex_colors,
    GTATOOLS_OT_apply_v_offset,
    GTATOOLS_OT_vc_smooth,
    GTATOOLS_OT_vc_contrast,
    GTATOOLS_OT_vc_brightness,
    GTATOOLS_OT_vc_gamma,
    GTATOOLS_OT_vc_smooth_between,
    GTATOOLS_OT_load_lightmap,
    GTATOOLS_OT_remove_lightmap,
    GTATOOLS_OT_create_day_night,
    GTATOOLS_OT_copy_color_attr,
    GTATOOLS_OT_prelight_preview,
    GTATOOLS_OT_fix_itera_collection,
    GTATOOLS_OT_apply_itera_material,
    GTATOOLS_OT_apply_itera_quickstart,
    GTATOOLS_OT_remove_itera_material,
    GTATOOLS_OT_save_materials,
    GTATOOLS_OT_restore_materials,
    GTATOOLS_OT_eyedropper_color,
    GTATOOLS_OT_fill_faces,
    GTATOOLS_OT_restore_fill,
    GTATOOLS_OT_remove_fill_color,
    GTATOOLS_OT_select_fill_color,
    GTATOOLS_OT_delete_fill_color_level,
    GTATOOLS_OT_clear_fill_color_levels,
    GTATOOLS_OT_scatter_light,
    GTATOOLS_OT_toggle_face_select,
    GTATOOLS_OT_switch_to_edit,
    GTATOOLS_OT_switch_to_vpaint,
    GTATOOLS_OT_select_color_attribute,
    GTATOOLS_OT_add_color_attribute,
    GTATOOLS_OT_remove_color_attribute,
    GTATOOLS_OT_create_color_attr,
    GTATOOLS_OT_remove_color_attr,
)


# =============================================================================
# TEXTURE LOADER
# =============================================================================

# Operators moved to ops/texture_ops.py in Phase 3.
from .ops.texture_ops import (
    GTATOOLS_OT_load_textures,
    GTATOOLS_OT_set_blend_folder,
    GTATOOLS_OT_drop_texture_as_material,
    GTATOOLS_OT_drop_txd,
    GTATOOLS_OT_check_materials,
    GTATOOLS_OT_cleanup_materials,
    GTATOOLS_OT_sort_materials,
    GTATOOLS_OT_reset_transform,
    GTATOOLS_OT_apply_lightmap_uv2,
    GTATOOLS_OT_remove_lightmap_uv2,
    GTATOOLS_OT_toggle_lightmap_uv2,
    GTATOOLS_FH_texture_drop,
    GTATOOLS_FH_txd_drop,
)
# =============================================================================
# PANELS
# =============================================================================

# Operators moved to ops/world_ops.py in Phase 3.
from .ops.world_ops import (
    GTATOOLS_OT_import_water,
    GTATOOLS_OT_export_water,
    GTATOOLS_OT_import_flight,
    GTATOOLS_OT_export_flight,
    GTATOOLS_OT_import_track,
    GTATOOLS_OT_export_track,
    GTATOOLS_OT_import_nodes,
    GTATOOLS_OT_export_nodes,
    GTATOOLS_OT_import_paths_ipl,
    GTATOOLS_OT_export_paths_ipl,
    GTATOOLS_OT_convert_to_path,
    GTATOOLS_OT_add_path_ipl,
    GTATOOLS_OT_add_track,
    GTATOOLS_OT_add_vehicle_path,
    GTATOOLS_OT_add_ped_path,
    GTATOOLS_OT_mark_station,
)
_hide_dff = False
_hide_lod = False
_hide_col = False


# Operators moved to ops/object_utils_ops.py in Phase 3.
from .ops.object_utils_ops import (
    GTATOOLS_OT_toggle_visibility,
    GTATOOLS_OT_snap_to_dff,
)
# ── 2DFX Light Presets ──
_2DFX_PRESETS = {
    'Default': dict(color=[255,255,255,255], corona_size=1.0, corona_far_clip=100.0,
                    pointlight_range=18.0, corona_tex='coronastar', corona_show_mode=0,
                    corona_flare_type=0, corona_enable_reflection=0, shadow_size=8.0,
                    shadow_z_distance=0, shadow_color_multiplier=40, shadow_tex='shad_exp',
                    flags1=96, flags2=0),
    'OnAllDay': dict(color=[255,255,255,255], corona_size=1.0, corona_far_clip=100.0,
                     pointlight_range=18.0, corona_tex='coronastar', corona_show_mode=0,
                     corona_flare_type=0, corona_enable_reflection=0, shadow_size=8.0,
                     shadow_z_distance=0, shadow_color_multiplier=40, shadow_tex='shad_exp',
                     flags1=96, flags2=0),
    'Lamp Post': dict(color=[255,255,171,255], corona_size=1.5, corona_far_clip=200.0,
                      pointlight_range=16.0, corona_tex='coronastar', corona_show_mode=0,
                      corona_flare_type=0, corona_enable_reflection=1, shadow_size=10.0,
                      shadow_z_distance=0, shadow_color_multiplier=40, shadow_tex='shad_exp',
                      flags1=64, flags2=0),
    'Lamp Post Coast': dict(color=[255,217,163,255], corona_size=1.2, corona_far_clip=200.0,
                            pointlight_range=14.0, corona_tex='coronamoon', corona_show_mode=0,
                            corona_flare_type=0, corona_enable_reflection=1, shadow_size=8.0,
                            shadow_z_distance=0, shadow_color_multiplier=40, shadow_tex='shad_exp',
                            flags1=64, flags2=0),
    'BB Pickup': dict(color=[255,0,0,255], corona_size=0.8, corona_far_clip=80.0,
                      pointlight_range=8.0, corona_tex='coronastar', corona_show_mode=0,
                      corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                      shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                      flags1=96, flags2=0),
    'Flashing (Maverick1)': dict(color=[255,0,0,255], corona_size=0.5, corona_far_clip=200.0,
                                 pointlight_range=0.0, corona_tex='coronastar', corona_show_mode=1,
                                 corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                                 shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                                 flags1=96, flags2=0),
    'Flashing (Maverick2)': dict(color=[0,255,0,255], corona_size=0.5, corona_far_clip=200.0,
                                 pointlight_range=0.0, corona_tex='coronastar', corona_show_mode=1,
                                 corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                                 shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                                 flags1=96, flags2=0),
    'Flashing (Tug)': dict(color=[255,128,0,255], corona_size=0.4, corona_far_clip=150.0,
                           pointlight_range=0.0, corona_tex='coronastar', corona_show_mode=1,
                           corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                           shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                           flags1=96, flags2=0),
    'Train Crossing': dict(color=[255,0,0,255], corona_size=1.0, corona_far_clip=200.0,
                           pointlight_range=12.0, corona_tex='coronastar', corona_show_mode=1,
                           corona_flare_type=0, corona_enable_reflection=1, shadow_size=0.0,
                           shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                           flags1=96, flags2=0),
    'Traffic': dict(color=[255,0,0,255], corona_size=0.7, corona_far_clip=120.0,
                    pointlight_range=6.0, corona_tex='coronastar', corona_show_mode=0,
                    corona_flare_type=0, corona_enable_reflection=0, shadow_size=0.0,
                    shadow_z_distance=0, shadow_color_multiplier=0, shadow_tex='shad_exp',
                    flags1=96, flags2=0),
}

_PRESET_NAMES = list(_2DFX_PRESETS.keys())


# Map EnumProperty identifiers to preset dict keys
_PRESET_MAP = {
    'DEFAULT': 'Default',
    'ONALLDAY': 'OnAllDay',
    'LAMP_POST': 'Lamp Post',
    'LAMP_POST_COAST': 'Lamp Post Coast',
    'BB_PICKUP': 'BB Pickup',
    'FLASHING_MAV1': 'Flashing (Maverick1)',
    'FLASHING_MAV2': 'Flashing (Maverick2)',
    'FLASHING_TUG': 'Flashing (Tug)',
    'TRAIN_CROSSING': 'Train Crossing',
    'TRAFFIC': 'Traffic',
}


# Operators moved to ops/effects_ops.py in Phase 3.
from .ops.effects_ops import (
    GTATOOLS_OT_apply_2dfx_preset,
    GTATOOLS_OT_create_2dfx,
    GTATOOLS_OT_toggle_2dfx_flag_bit,
    GTATOOLS_OT_refresh_2dfx_preview,
    GTATOOLS_OT_remove_2dfx_preview,
    GTATOOLS_OT_select_particle_effect,
    GTATOOLS_OT_particle_effect_new,
    GTATOOLS_OT_particle_effect_delete,
    GTATOOLS_OT_particle_curve_select,
    GTATOOLS_OT_particle_curve_key_add,
    GTATOOLS_OT_particle_curve_key_select_row,
    GTATOOLS_OT_particle_curve_key_remove,
    GTATOOLS_OT_particle_curve_write,
    GTATOOLS_OT_particle_emitter_switch,
    GTATOOLS_OT_reload_effects_fxp,
    GTATOOLS_OT_save_particle_effect,
    GTATOOLS_OT_attach_2dfx,
    GTATOOLS_OT_detach_2dfx,
    GTATOOLS_OT_detach_all_2dfx,
)
# Operators moved to ops/col_surface_ops.py in Phase 3.
from .ops.col_surface_ops import (
    GTATOOLS_OT_set_col_surface,
    GTATOOLS_OT_col_surface_menu,
    GTATOOLS_OT_batch_set_distance,
)
# ============================================================================
# Preferences & ID Manager — N-sidebar subpanels
# ============================================================================

def _draw_suffix_prefix(layout, scene):
    for _label, _pfx, _sfx in [("DFF", "gtatools_prefix_dff", "gtatools_suffix_dff"),
                                ("LOD", "gtatools_prefix_lod", "gtatools_suffix_lod"),
                                ("COL", "gtatools_prefix_col", "gtatools_suffix_col")]:
        row = layout.row(align=True)
        pfx = row.row(align=True)
        pfx.scale_x = 0.7
        pfx.prop(scene, _pfx, text="")
        sub_lbl = row.row(align=True)
        sub_lbl.scale_x = 0.6
        sub_lbl.label(text="Model")
        sfx = row.row(align=True)
        sfx.scale_x = 0.7
        sfx.prop(scene, _sfx, text="")
        pad = row.row(align=True)
        pad.label(text=" ")
        pad.label(text=" ")
        pad.label(text=" ")


def _draw_id_manager(layout, scene, context):
    """ID Manager UI — visually grouped into 4 sections:
      1. Preset row (which ID list file is active)
      2. Stats + search + paginated used-ID list
      3. Free-ID hint
      4. Action buttons grouped by purpose (selection / bulk / service)
    Service ops are collapsed by default to keep the panel compact —
    rarely-used buttons (FLA extend, GC, open-file) only show when
    the user expands that section.
    """
    _id_preset_sync(context)
    from .data.id_manager import get_free_ids, get_used_ids

    # ── 1. Preset row ──────────────────────────────────
    preset_row = layout.row(align=True)
    preset_row.prop(scene, "gtatools_id_preset", text="")
    preset_row.operator("gtatools.id_preset_new", text="", icon='ADD')
    preset_row.operator("gtatools.id_preset_rename", text="", icon='GREASEPENCIL')
    preset_row.operator("gtatools.id_preset_delete", text="", icon='REMOVE')

    free = get_free_ids()
    used = get_used_ids()

    # ── 2. Stats + next free + search + used-list ─────
    stats_box = layout.box()
    stats_row = stats_box.row(align=True)
    stats_row.label(
        text=f"{T('Свободных:')} {len(free)}",
        icon='CHECKMARK')
    stats_row.label(
        text=f"{T('Занятых:')} {len(used)}",
        icon='OBJECT_DATA')
    if free:
        stats_box.label(
            text=f"{T('Следующий свободный:')} {free[0]}",
            icon='FORWARD')

    layout.prop(scene, "gtatools_id_search", text="", icon='VIEWZOOM')
    search = getattr(scene, 'gtatools_id_search', '').strip()
    page = getattr(scene, 'gtatools_id_page', 0)
    per_page = 20

    if used:
        filtered = []
        for id_num in sorted(used.keys()):
            name = used[id_num]
            if search:
                if search.isdigit():
                    if search not in str(id_num):
                        continue
                else:
                    if search.lower() not in name.lower():
                        continue
            filtered.append((id_num, name))

        total = len(filtered)
        max_page = max(0, (total - 1) // per_page)
        page = min(page, max_page)
        start = page * per_page
        page_items = filtered[start:start + per_page]

        if total == 0 and search:
            layout.label(
                text=T("Ничего не найдено"),
                icon='ERROR')
        else:
            # 2 columns, COLUMN-major (top-to-bottom in col 1, then
            # top-to-bottom in col 2). Old layout was row-major
            # zigzag (1 2 / 3 4 / 5 6) — column-major (1 4 / 2 5 /
            # 3 6) reads naturally because IDs are sorted ascending
            # and the eye scans down each column rather than
            # bouncing across rows.
            sub = layout.box()
            sub.label(text=T("Используются:"),
                      icon='OUTLINER_OB_GROUP_INSTANCE')
            n = len(page_items)
            half = (n + 1) // 2  # rows per column (col 1 ≥ col 2)
            col = sub.column(align=True)
            for r in range(half):
                row = col.row(align=True)
                # Column 1 entry — always present
                id_num, name = page_items[r]
                row.label(text=f"{id_num} {name}")
                op = row.operator(
                    "gtatools.id_manager_release",
                    text="", icon='X')
                op.model_id = id_num
                # Column 2 entry — present unless we hit odd-count tail
                idx2 = r + half
                if idx2 < n:
                    id_num2, name2 = page_items[idx2]
                    row.label(text=f"{id_num2} {name2}")
                    op2 = row.operator(
                        "gtatools.id_manager_release",
                        text="", icon='X')
                    op2.model_id = id_num2
                else:
                    # Filler so single tail entry doesn't take the
                    # full row width.
                    row.label(text="")
                    row.label(text="")

            if total > per_page:
                nav = sub.row(align=True)
                nav.prop(
                    scene, "gtatools_id_page",
                    text=f"{start+1}-{min(start+per_page, total)} / {total}")

    if free:
        sub = layout.box()
        sub.label(text=T("Свободные ID:"), icon='LIBRARY_DATA_DIRECT')
        text = ", ".join(str(i) for i in sorted(free)[:20])
        if len(free) > 20:
            text += "..."
        sub.label(text=text)

    # ── 3. All action buttons in one flat block ───────
    # Earlier split into «Selection / Bulk / Service» (3 boxes with
    # headers + collapsible service) ate too much vertical space.
    # Single column with action buttons grouped by visual proximity
    # is enough — the labels themselves communicate purpose.
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator("gtatools.id_manager_auto_assign",
                 text=T("Назначить"), icon='ADD')
    row.operator("gtatools.id_manager_assign_from",
                 text=T("С ID..."), icon='SEQUENCE')
    row = col.row(align=True)
    row.operator("gtatools.id_manager_sync_scene",
                 text=T("Sync"), icon='FILE_REFRESH')
    row.operator("gtatools.id_manager_clear_selected",
                 text=T("Очистить"), icon='REMOVE')
    row = col.row(align=True)
    row.operator("gtatools.id_manager_create",
                 text=T("Создать ID"), icon='FILE_NEW')
    row.operator("gtatools.id_manager_clear",
                 text=T("Очистить всё"), icon='TRASH')
    row = col.row(align=True)
    row.operator("gtatools.id_manager_from_game",
                 text=T("Из игры"), icon='IMPORT')
    row.operator("gtatools.id_manager_extend",
                 text=T("Расширить FLA"), icon='ADD')
    col.operator("gtatools.id_manager_gc",
                 text=T("Освободить фантомы"),
                 icon='ORPHAN_DATA')
    col.operator("gtatools.id_manager_open_file",
                 text=T("Открыть файл ID"), icon='FILE_TEXT')


# Operators moved to ops/id_manager_ops.py in Phase 3.
from .ops.id_manager_ops import (
    GTATOOLS_OT_id_manager_open_file,
    GTATOOLS_OT_id_manager_release,
    GTATOOLS_OT_id_manager_auto_assign,
    GTATOOLS_OT_id_manager_assign_from,
    GTATOOLS_OT_batch_set_type,
    GTATOOLS_OT_id_manager_clear_selected,
    GTATOOLS_OT_id_manager_clear,
    GTATOOLS_OT_id_manager_create,
    GTATOOLS_OT_id_manager_extend,
    GTATOOLS_OT_id_manager_from_game,
    GTATOOLS_OT_id_manager_gc,
    GTATOOLS_OT_id_manager_sync_scene,
    GTATOOLS_OT_id_preset_new,
    GTATOOLS_OT_id_preset_delete,
    GTATOOLS_OT_id_preset_rename,
)
# Subpanel of light_master. bl_parent_id inherits bl_category, so no
# @apply_order — the registry only places top-level panels. Intra-parent
# bl_order literals are local (sibling order under light_master).
def _presets_dir():
    d = os.path.join(_get_user_config_dir(), 'presets')
    os.makedirs(d, exist_ok=True)
    return d


def _load_prelight_presets():
    import json
    presets = []
    d = _presets_dir()
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    for f in sorted(os.listdir(d)):
        if f.endswith('.json'):
            try:
                with open(os.path.join(d, f), 'r', encoding='utf-8') as fh:
                    p = json.load(fh)
                    if 'name' in p:
                        presets.append(p)
            except:
                pass
    return presets if presets else [{"name": "Default", "ambient": 0.10, "intensity": 0.05, "gamma": 0.50, "shadows": True}]


def _save_preset_file(preset):
    import json
    d = _presets_dir()
    os.makedirs(d, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in preset['name'])
    path = os.path.join(d, f"{safe_name}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(preset, f, indent=2, ensure_ascii=False)


def _delete_preset_file(name):
    d = _presets_dir()
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
    path = os.path.join(d, f"{safe_name}.json")
    if os.path.isfile(path):
        os.remove(path)


def _get_preset_items(self, context):
    presets = _load_prelight_presets()
    items = [(p['name'], p['name'], '') for p in presets]
    return items if items else [('NONE', 'No presets', '')]


# Operators moved to ops/prelight_preset_ops.py in Phase 3.
from .ops.prelight_preset_ops import (
    GTATOOLS_OT_prelight_preset_load,
    GTATOOLS_OT_prelight_preset_save,
    GTATOOLS_OT_prelight_preset_delete,
)
# Operators moved to ops/water_geometry_ops.py in Phase 3.
from .ops.water_geometry_ops import (
    GTATOOLS_OT_add_water,
    GTATOOLS_OT_water_snap_grid,
    GTATOOLS_OT_water_set_params,
    GTATOOLS_OT_water_stitch,
)
# =============================================================================
# IFP (ANIMATION) OPERATORS
# =============================================================================

# Operators moved to ops/ifp_ops.py in Phase 3.
from .ops.ifp_ops import (
    GTATOOLS_OT_import_ifp,
    GTATOOLS_OT_export_ifp,
    GTATOOLS_OT_ifp_roundtrip,
    GTATOOLS_OT_merge_ifp,
    GTATOOLS_OT_ifp_preview_toggle,
    GTATOOLS_OT_apply_ifp,
    GTATOOLS_OT_fix_quat_signs,
    GTATOOLS_OT_delete_active_action,
)
from .ops.ik_rig import (
    GTATOOLS_OT_add_ik_rig,
    GTATOOLS_OT_bake_ik_rig,
    GTATOOLS_OT_add_ground_plane,
)
# ── X Radar Maker ────────────────────────────────────────────────────

# Operators moved to ops/radar_ops.py in Phase 3.
from .ops.radar_ops import (
    GTATOOLS_OT_radar_generate,
    GTATOOLS_OT_radar_pack_txd,
)
# =============================================================================
# =============================================================================
# REGISTRATION
# =============================================================================

classes = (
    INUParticleKeyframe,
    INUObjectProps,
    INUMaterialProps,
    GTATOOLS_ImgFileEntry,
    GTATOOLS_BinaryIplEntry,
    GTATOOLS_TxdExportEntry,
    GTATOOLS_UL_txd_export_plan,
    GTATOOLS_UL_img_files,
    GTATOOLS_OT_refresh_img_list,
    GTATOOLS_OT_discover_game,
    GTATOOLS_OT_scan_binary_ipls,
    GTATOOLS_OT_binary_ipl_toggle_all,
    GTATOOLS_FillColorItem,
    GTATOOLS_OT_toggle_visibility,
    GTATOOLS_OT_snap_to_dff,
    GTATOOLS_OT_check_geometry,
    GTATOOLS_OT_check_ngons,
    GTATOOLS_OT_clear_raw_dff,
    GTATOOLS_OT_sa_vehicle_preset,
    GTATOOLS_OT_apply_vehicle_pipeline,
    GTATOOLS_OT_export_txd,
    GTATOOLS_OT_export_shared_txd,
    GTATOOLS_OT_copy_color_attr,
    GTATOOLS_OT_export_dff,
    GTATOOLS_OT_export_col,
    GTATOOLS_OT_export_all,
    GTATOOLS_OT_inu_export,
    GTATOOLS_OT_info_tooltip,
    GTATOOLS_OT_detect_models,
    GTATOOLS_OT_average_colors,
    GTATOOLS_OT_lightmap_generate,
    GTATOOLS_OT_lightmap_copy,
    GTATOOLS_OT_lightmap_clear,
    GTATOOLS_OT_create_prelight_lights,
    GTATOOLS_OT_remove_prelight_lights,
    GTATOOLS_OT_bake_vertex_colors,
    GTATOOLS_OT_bake_vertex_colors_simple,
    GTATOOLS_OT_reset_bake_settings,
    GTATOOLS_OT_prelight_preset_load,
    GTATOOLS_OT_prelight_preset_save,
    GTATOOLS_OT_prelight_preset_delete,
    GTATOOLS_OT_reset_scatter_settings,
    GTATOOLS_OT_analyze_vertex_colors,
    GTATOOLS_OT_apply_v_offset,
    GTATOOLS_OT_vc_smooth,
    GTATOOLS_OT_vc_contrast,
    GTATOOLS_OT_vc_brightness,
    GTATOOLS_OT_vc_gamma,
    GTATOOLS_OT_vc_smooth_between,
    GTATOOLS_OT_load_lightmap,
    GTATOOLS_OT_remove_lightmap,
    GTATOOLS_OT_create_day_night,
    GTATOOLS_OT_prelight_preview,
    GTATOOLS_OT_fix_itera_collection,
    GTATOOLS_OT_apply_itera_material,
    GTATOOLS_OT_apply_itera_quickstart,
    GTATOOLS_OT_remove_itera_material,
    GTATOOLS_OT_save_materials,
    GTATOOLS_OT_restore_materials,
    GTATOOLS_OT_eyedropper_color,
    GTATOOLS_OT_fill_faces,
    GTATOOLS_OT_restore_fill,
    GTATOOLS_OT_remove_fill_color,
    GTATOOLS_OT_select_fill_color,
    GTATOOLS_OT_delete_fill_color_level,
    GTATOOLS_OT_clear_fill_color_levels,
    GTATOOLS_OT_scatter_light,
    GTATOOLS_OT_toggle_face_select,
    GTATOOLS_OT_switch_to_edit,
    GTATOOLS_OT_switch_to_vpaint,
    GTATOOLS_OT_select_color_attribute,
    GTATOOLS_OT_add_color_attribute,
    GTATOOLS_OT_remove_color_attribute,
    GTATOOLS_OT_create_color_attr,
    GTATOOLS_OT_remove_color_attr,
    GTATOOLS_OT_load_textures,
    GTATOOLS_OT_set_blend_folder,
    GTATOOLS_OT_drop_texture_as_material,
    GTATOOLS_FH_texture_drop,
    GTATOOLS_OT_drop_txd,
    GTATOOLS_FH_txd_drop,
    GTATOOLS_OT_check_materials,
    GTATOOLS_OT_cleanup_materials,
    GTATOOLS_OT_sort_materials,
    GTATOOLS_OT_reset_transform,
    GTATOOLS_OT_apply_lightmap_uv2,
    GTATOOLS_OT_remove_lightmap_uv2,
    GTATOOLS_OT_toggle_lightmap_uv2,
    GTATOOLS_OT_id_manager_open_file,
    GTATOOLS_OT_id_manager_release,
    GTATOOLS_OT_id_manager_auto_assign,
    GTATOOLS_OT_id_manager_assign_from,
    GTATOOLS_OT_batch_set_type,
    GTATOOLS_OT_batch_set_distance,
    GTATOOLS_OT_id_manager_clear_selected,
    GTATOOLS_OT_id_manager_clear,
    GTATOOLS_OT_id_manager_create,
    GTATOOLS_OT_id_manager_extend,
    GTATOOLS_OT_id_manager_gc,
    GTATOOLS_OT_id_manager_sync_scene,
    GTATOOLS_OT_id_manager_from_game,
    GTATOOLS_OT_id_preset_new,
    GTATOOLS_OT_id_preset_delete,
    GTATOOLS_OT_id_preset_rename,
    GTATOOLS_OT_toggle_uv_editor,
    GTATOOLS_OT_toggle_uv_grid,
    GTATOOLS_OT_randomize_uv_grid,
    GTATOOLS_OT_snap_uv_to_grid,
    GTATOOLS_OT_set_uv_align,
    GTATOOLS_PT_main_panel,
    GTATOOLS_OT_import_dff,
    GTATOOLS_OT_drop_dff,
    GTATOOLS_FH_dff_drop,
    GTATOOLS_OT_import_col,
    GTATOOLS_OT_drop_col,
    GTATOOLS_FH_col_drop,
    GTATOOLS_OT_import_txd,
    GTATOOLS_OT_inu_import,
    GTATOOLS_OT_toggle_links,
    GTATOOLS_OT_toggle_bbox,
    GTATOOLS_OT_extract_resources,
    GTATOOLS_OT_import_map,
    GTATOOLS_OT_import_ipl_sections,
    GTATOOLS_OT_export_ipl_sections,
    GTATOOLS_OT_import_from_img,
    GTATOOLS_OT_import_water,
    GTATOOLS_OT_export_water,
    GTATOOLS_OT_add_water,
    GTATOOLS_OT_water_snap_grid,
    GTATOOLS_OT_water_set_params,
    GTATOOLS_OT_water_stitch,
    GTATOOLS_OT_import_track,
    GTATOOLS_OT_export_track,
    GTATOOLS_OT_import_nodes,
    GTATOOLS_OT_export_nodes,
    GTATOOLS_OT_import_ifp,
    GTATOOLS_OT_export_ifp,
    GTATOOLS_OT_merge_ifp,
    GTATOOLS_OT_ifp_roundtrip,
    GTATOOLS_OT_ifp_preview_toggle,
    GTATOOLS_OT_apply_ifp,
    GTATOOLS_OT_fix_quat_signs,
    GTATOOLS_OT_delete_active_action,
    GTATOOLS_OT_add_ik_rig,
    GTATOOLS_OT_bake_ik_rig,
    GTATOOLS_OT_add_ground_plane,
    GTATOOLS_OT_import_paths_ipl,
    GTATOOLS_OT_export_paths_ipl,
    GTATOOLS_OT_convert_to_path,
    GTATOOLS_OT_add_path_ipl,
    GTATOOLS_OT_add_track,
    GTATOOLS_OT_add_vehicle_path,
    GTATOOLS_OT_add_ped_path,
    GTATOOLS_OT_mark_station,
    GTATOOLS_OT_export_to_img,
    GTATOOLS_OT_remove_from_img,
    GTATOOLS_OT_upsert_ide,
    GTATOOLS_OT_upsert_ipl,
    GTATOOLS_OT_remove_ide,
    GTATOOLS_OT_remove_ipl,
    GTATOOLS_OT_export_ide,
    GTATOOLS_OT_export_ipl,
    GTATOOLS_OT_import_ide,
    GTATOOLS_OT_import_ipl,
    GTATOOLS_OT_replace_ipl_placeholders,
    GTATOOLS_PT_ide_ipl_panel,
    GTATOOLS_PT_export_panel,
    GTATOOLS_PT_validate_scene,
    GTATOOLS_MT_import_menu,
    GTATOOLS_MT_export_menu,
    GTATOOLS_MT_create_2dfx,
    GTATOOLS_MT_radar_generate,
    GTATOOLS_MT_path_traffic,
    GTATOOLS_PT_check_panel,
    GTATOOLS_PT_vehicle_panel,
    GTATOOLS_PT_frame_hierarchy,
    GTATOOLS_OT_apply_2dfx_preset,
    GTATOOLS_OT_create_2dfx,
    GTATOOLS_OT_toggle_2dfx_flag_bit,
    GTATOOLS_OT_attach_2dfx,
    GTATOOLS_OT_detach_2dfx,
    GTATOOLS_OT_detach_all_2dfx,
    GTATOOLS_OT_refresh_2dfx_preview,
    GTATOOLS_OT_remove_2dfx_preview,
    GTATOOLS_OT_select_particle_effect,
    GTATOOLS_OT_particle_effect_new,
    GTATOOLS_OT_particle_effect_delete,
    GTATOOLS_OT_particle_emitter_switch,
    GTATOOLS_OT_particle_curve_select,
    GTATOOLS_OT_particle_curve_key_add,
    GTATOOLS_OT_particle_curve_key_remove,
    GTATOOLS_OT_particle_curve_key_select_row,
    GTATOOLS_OT_particle_curve_write,
    GTATOOLS_OT_reload_effects_fxp,
    GTATOOLS_OT_save_particle_effect,
    GTATOOLS_OT_set_col_surface,
    GTATOOLS_OT_col_surface_menu,
    GTATOOLS_PT_material_panel,
    GTATOOLS_PT_object_ide_ipl_panel,
    GTATOOLS_PT_object_inu_tools,
    GTATOOLS_PT_inu_tools_panel,
    GTATOOLS_PT_id_manager_panel,
    # Phase 2: light_master must register before its 5 child light panels
    # so Blender can resolve their bl_parent_id at register time.
    GTATOOLS_PT_light_master,
    GTATOOLS_PT_itera_panel,
    GTATOOLS_PT_prelight_panel,
    GTATOOLS_PT_bake_settings_subpanel,
    GTATOOLS_PT_vc_postprocess_panel,
    GTATOOLS_OT_preview_col_light,
    GTATOOLS_OT_bake_col_light,
    GTATOOLS_OT_clear_col_light_mats,
    GTATOOLS_PT_prelight_col_panel,
    GTATOOLS_PT_2dfx_panel,
    GTATOOLS_PT_vertex_paint_panel,
    GTATOOLS_PT_lightmap_panel,
    GTATOOLS_PT_water_panel,
    GTATOOLS_PT_anim_panel,
    GTATOOLS_OT_radar_generate,
    GTATOOLS_OT_radar_pack_txd,
    GTATOOLS_PT_radar_panel,
    GTATOOLS_PT_paths_panel,
    GTATOOLS_PT_uv_tools_panel,
    GTATOOLS_OT_add_gtasa_model,
    VIEW3D_MT_gtasa_add_menu,
    GTATOOLS_OT_bitmaps_scan,
    GTATOOLS_OT_bitmaps_resolve,
    GTATOOLS_OT_bitmaps_copy,
    GTATOOLS_OT_bitmaps_find_unused,
    GTATOOLS_OT_bitmaps_remove_unused,
    GTATOOLS_OT_bitmaps_find_dupes,
    GTATOOLS_MT_textures_menu,
    GTATOOLS_MT_materials_menu,
    GTATOOLS_PT_bitmaps_panel,
    GTATOOLS_VCLayerItem,
    GTATOOLS_OT_vcl_add,
    GTATOOLS_OT_vcl_remove,
    GTATOOLS_OT_vcl_move,
    GTATOOLS_OT_vcl_promote,
    GTATOOLS_OT_vcl_demote,
    GTATOOLS_OT_vcl_set_active_attr,
    GTATOOLS_OT_vcl_show_composite,
    GTATOOLS_OT_vcl_refresh_composite,
    GTATOOLS_OT_vcl_apply_multi,
    GTATOOLS_OT_vcl_recolor_selected,
    GTATOOLS_UL_vc_layers,
    GTATOOLS_OT_ifp_batch_import,
    GTATOOLS_OT_refresh_station_markers,
    GTATOOLS_OT_path_node_flag,
    GTATOOLS_OT_map_export,
    GTATOOLS_OT_material_preset,
    GTATOOLS_OT_material_preset_save,
    GTATOOLS_OT_material_preset_delete,
    GTATOOLS_OT_import_cst,
    GTATOOLS_OT_export_cst,
    GTATOOLS_OT_validate_paintjobs,
    GTATOOLS_OT_open_docs,
    GTATOOLS_OT_open_issues,
    GTATOOLS_OT_open_release,
    GTATOOLS_OT_whats_new,
    INUValidateIssue,
    GTATOOLS_OT_validate_run,
    GTATOOLS_OT_validate_clear,
    GTATOOLS_OT_validate_goto,
    GTATOOLS_OT_validate_fix_quaternions,
    GTATOOLS_OT_validate_fix_suffix,
    GTATOOLS_OT_validate_fix_modulate_color,
    GTATOOLS_OT_frame_select,
    GTATOOLS_OT_frame_rename,
    GTATOOLS_OT_frame_set_parent,
    GTATOOLS_OT_frame_unparent,
    GTATOOLS_OT_frame_validate,
    GTATOOLS_OT_frame_mirror_lr,
    GTATOOLS_OT_animobj_setup,
    GTATOOLS_OT_animobj_validate,
    GTATOOLS_OT_animobj_export,
    INUAnimObjProps,
    GTATOOLS_OT_profile_save,
    GTATOOLS_OT_profile_delete,
    GTATOOLS_OT_profile_pick_panel,
    GTATOOLS_OT_profile_toggle_panel,
    GTATOOLS_OT_profile_edit,
    GTATOOLS_OT_vehicle_scale,
    GTATOOLS_OT_vehicle_add_damage_variant,
    GTATOOLS_OT_vehicle_show_damage,
    GTATOOLS_OT_vehicle_pair_report,
)


# ── Persistent paths (saved in Blender config, survive addon updates) ──

_PATHS_FILE = None

def _write_png(path: str, pixels: bytes, width: int, height: int):
    """Write RGBA pixels to PNG file using numpy for scanline prep + zlib.

    numpy builds the filtered raw buffer (prepend 1 filter byte per row)
    in one C-level operation — ~5-10x faster than the Python for-row loop
    on big textures (e.g. 2048x2048).
    """
    import zlib
    import struct as _st

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = _st.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return _st.pack('>I', len(data)) + c + crc

    # IHDR
    ihdr = _st.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)  # 8bit RGBA

    # IDAT — raw scanlines with filter byte 0 per row (none filter).
    # Build via numpy: column-0 is zero filter byte, columns 1.. hold RGBA.
    stride = width * 4
    pixels_arr = np.frombuffer(pixels, dtype=np.uint8)[:height * stride].reshape(height, stride)
    filtered = np.empty((height, stride + 1), dtype=np.uint8)
    filtered[:, 0] = 0  # filter byte per scanline
    filtered[:, 1:] = pixels_arr

    compressed = zlib.compress(filtered.tobytes(), 1)  # fast compression

    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')  # PNG signature
        f.write(_chunk(b'IHDR', ihdr))
        f.write(_chunk(b'IDAT', compressed))
        f.write(_chunk(b'IEND', b''))


def _write_dds(path: str, tex):
    """Write a TxdTexture as an uncompressed RGBA DDS file for nvdecompress."""
    import struct as _st
    w, h = tex.width, tex.height
    # DDS header (128 bytes)
    header = bytearray(128)
    _st.pack_into('<4s', header, 0, b'DDS ')
    _st.pack_into('<I', header, 4, 124)        # header size
    _st.pack_into('<I', header, 8, 0x1 | 0x2 | 0x4 | 0x1000 | 0x8)  # flags
    _st.pack_into('<I', header, 12, h)          # height
    _st.pack_into('<I', header, 16, w)          # width
    _st.pack_into('<I', header, 20, w * 4)      # pitch
    # Pixel format at offset 76
    _st.pack_into('<I', header, 76, 32)         # pf size
    _st.pack_into('<I', header, 80, 0x41)       # pf flags (RGBA)
    _st.pack_into('<I', header, 88, 32)         # RGB bit count
    _st.pack_into('<I', header, 92, 0x000000FF)  # R mask
    _st.pack_into('<I', header, 96, 0x0000FF00)  # G mask
    _st.pack_into('<I', header, 100, 0x00FF0000) # B mask
    _st.pack_into('<I', header, 104, 0xFF000000) # A mask
    _st.pack_into('<I', header, 108, 0x1000)    # caps (texture)

    with open(path, 'wb') as f:
        f.write(header)
        f.write(tex.pixels)


_VEG_NAME_KEYWORDS = {'tree', 'palm', 'bush', 'grass', 'veg_', 'genveg_',
                       'cactus', 'cacti', 'fern', 'ivy', 'plant', 'flower',
                       'hedge', 'weed', 'leaf', 'leaves'}
_VEG_TXD_KEYWORDS = {'gta_tree_', 'gta_proc_', 'gta_cactus', 'veg_',
                      'gta_potplant', 'kbplantsm'}


def _is_vegetation(model_name: str, txd_name: str = "") -> bool:
    """Check if model is vegetation by name and TXD patterns."""
    low = model_name.lower()
    for kw in _VEG_NAME_KEYWORDS:
        if kw in low:
            return True
    if txd_name:
        txd_low = txd_name.lower()
        for kw in _VEG_TXD_KEYWORDS:
            if kw in txd_low:
                return True
    return False


def _sort_map_objects(context, objects: list, ide_models: dict):
    """Sort imported map objects into collections by category."""
    def _get_col(name):
        c = bpy.data.collections.get(name)
        if not c:
            c = bpy.data.collections.new(name)
            context.scene.collection.children.link(c)
        return c

    col_buildings = _get_col("Map_Buildings")
    col_props = _get_col("Map_Props")
    col_vegetation = _get_col("Map_Vegetation")
    col_small = _get_col("Map_Small")
    col_lod = _get_col("Map_LOD")

    # Build name→IDE lookup from ide_models
    name_to_ide = {}
    for mid, obj in ide_models.items():
        name_to_ide[obj.model_name.lower()] = obj

    for obj in objects:
        if obj.type not in ('MESH', 'EMPTY'):
            continue

        # Extract model name: "modelname.dff" or "modelname.dff.001"
        name = obj.name
        # Remove .dff suffix and Blender .NNN suffix
        model_name = name
        if '.dff' in model_name:
            model_name = model_name.split('.dff')[0]

        low = model_name.lower()

        # Find IDE data and set properties
        ide_obj = name_to_ide.get(low)
        if ide_obj and hasattr(obj, 'inu'):
            obj.inu.model_id = ide_obj.model_id
            obj.inu.txd_name = ide_obj.txd_name
            obj.inu.draw_distance = ide_obj.draw_distance
            obj.inu.ide_flags = ide_obj.flags

        dd = ide_obj.draw_distance if ide_obj else 300.0
        txd = ide_obj.txd_name if ide_obj else ""

        # Check LOD
        from .core.ipl import is_lod_name
        if is_lod_name(model_name):
            target = col_lod
        elif _is_vegetation(model_name, txd):
            target = col_vegetation
        elif dd >= 300:
            target = col_buildings
        elif dd >= 100:
            target = col_props
        else:
            target = col_small

        # Move to target collection
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        target.objects.link(obj)

    # Move duplicates (.001, .002 etc) into _Instances sub-collections
    for obj in objects:
        if obj.type != 'MESH':
            continue
        name = obj.name
        # Check for Blender duplicate suffix (.001, .002, etc)
        if '.' not in name:
            continue
        base, suffix = name.rsplit('.', 1)
        if not suffix.isdigit():
            continue
        # This is a duplicate — move to parent_Instances
        parent = obj.users_collection[0] if obj.users_collection else None
        if parent and parent.name.startswith('Map_') and not parent.name.endswith('_Instances'):
            inst_name = parent.name + "_Instances"
            inst_col = bpy.data.collections.get(inst_name)
            if not inst_col:
                inst_col = bpy.data.collections.new(inst_name)
                parent.children.link(inst_col)
            parent.objects.unlink(obj)
            inst_col.objects.link(obj)



def _load_textures_from_cache(tex_dir: str, objects: list) -> bool:
    """Load PNG textures from cache dir and assign to materials of objects.
    Returns True if at least one texture was loaded."""
    loaded = False
    # Cache: already loaded images by name
    _img_cache = {}

    for obj in objects:
        if obj.type != 'MESH' or not obj.data.materials:
            continue
        for mat in obj.data.materials:
            if not mat or not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image is None:
                    tex_name = node.label or ''
                    if not tex_name:
                        # Fallback: material name without .001 suffix
                        tex_name = mat.name.rsplit('.', 1)[0] if '.' in mat.name and mat.name.rsplit('.', 1)[1].isdigit() else mat.name

                    # Check image cache first
                    if tex_name in _img_cache:
                        node.image = _img_cache[tex_name]
                        loaded = True
                        continue

                    png_path = os.path.join(tex_dir, tex_name + '.png')
                    if os.path.isfile(png_path):
                        img = bpy.data.images.get(tex_name)
                        if not img:
                            img = bpy.data.images.load(png_path)
                            img.name = tex_name
                        node.image = img
                        _img_cache[tex_name] = img
                        loaded = True
    return loaded


_map_region_cache = []
_map_region_cache_root = ""


def _get_map_region_items(self, context):
    """Dynamic enum items for map region selector, based on gta.dat paths."""
    global _map_region_cache, _map_region_cache_root

    items = [('ALL', T("Вся карта"), T("Импорт всей карты"))]

    game_root = bpy.path.abspath(getattr(context.scene, 'gtatools_game_root', ''))
    if not game_root or not os.path.isdir(game_root):
        return items

    # Cache: avoid re-parsing on every UI redraw
    if game_root == _map_region_cache_root and _map_region_cache:
        return _map_region_cache

    dat_path = os.path.join(game_root, 'data', 'gta.dat')
    if not os.path.isfile(dat_path):
        return items

    from .core.gta_dat import parse_gta_dat, extract_regions
    try:
        info = parse_gta_dat(dat_path)
        regions = extract_regions(info)
        for r in regions:
            items.append((r, r, f"Region: {r}"))
    except Exception:
        pass

    _map_region_cache = items
    _map_region_cache_root = game_root
    return items


# ID preset selector ─ dynamic EnumProperty
_id_preset_cache = []


def _get_id_preset_items(self, context):
    """Dynamic enum items for the Model ID preset selector."""
    global _id_preset_cache
    from .data.id_manager import list_presets
    names = list_presets()
    items = [(n, n, "") for n in names]
    if not items:
        items = [('default', 'default', '')]
    _id_preset_cache = items
    return _id_preset_cache


def _id_preset_update(self, context):
    """Sync id_manager's active preset whenever the selector changes."""
    from .data.id_manager import set_active_preset
    set_active_preset(self.gtatools_id_preset)


def _id_preset_sync(context):
    """Push the scene's current preset name into id_manager's module state."""
    try:
        from .data.id_manager import set_active_preset
        name = getattr(context.scene, 'gtatools_id_preset', 'default') or 'default'
        set_active_preset(name)
    except Exception:
        pass


def _get_cache_dir():
    """Get cache folder next to .blend file. Falls back to temp."""
    blend = bpy.data.filepath
    if blend:
        d = os.path.join(os.path.dirname(blend), '.inu_cache')
        os.makedirs(d, exist_ok=True)
        return d
    # Unsaved file — use temp
    return tempfile.mkdtemp(prefix='inu_')


def _get_user_config_dir():
    """Get INU_Preset folder next to the addon folder (not inside it)."""
    addon_dir = os.path.dirname(os.path.abspath(__file__))  # .../addons/INU_tools
    addons_dir = os.path.dirname(addon_dir)                  # .../addons/
    d = os.path.join(addons_dir, 'INU_Preset')
    os.makedirs(d, exist_ok=True)
    return d


def _get_paths_file():
    global _PATHS_FILE
    if _PATHS_FILE is None:
        _PATHS_FILE = os.path.join(_get_user_config_dir(), 'paths.json')
    return _PATHS_FILE

_SAVED_PATH_KEYS = [
    'gtatools_ide_path', 'gtatools_ipl_path', 'gtatools_img_path', 'gtatools_game_root',
    'gtatools_texture_path1', 'gtatools_texture_path2',
    'gtatools_nvtt_path',
]

def _save_paths(self, context):
    """Save paths to config file when any path changes."""
    import json
    scene = context.scene
    data = {}
    for key in _SAVED_PATH_KEYS:
        val = getattr(scene, key, '')
        if val:
            data[key] = val
    try:
        with open(_get_paths_file(), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except:
        pass

def _load_paths(scene):
    """Load saved paths from config file into scene properties."""
    import json
    path = _get_paths_file()
    if not os.path.isfile(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for key, val in data.items():
            if key in _SAVED_PATH_KEYS and hasattr(scene, key):
                setattr(scene, key, val)
    except:
        pass


def _upd_suffix_dff(self, ctx):
    if self.gtatools_suffix_dff and self.gtatools_prefix_dff:
        self.gtatools_prefix_dff = ""

def _upd_suffix_lod(self, ctx):
    if self.gtatools_suffix_lod and self.gtatools_prefix_lod:
        self.gtatools_prefix_lod = ""

def _upd_suffix_col(self, ctx):
    if self.gtatools_suffix_col and self.gtatools_prefix_col:
        self.gtatools_prefix_col = ""

def _upd_prefix_dff(self, ctx):
    if self.gtatools_prefix_dff and self.gtatools_suffix_dff:
        self.gtatools_suffix_dff = ""

def _upd_prefix_lod(self, ctx):
    if self.gtatools_prefix_lod and self.gtatools_suffix_lod:
        self.gtatools_suffix_lod = ""

def _upd_prefix_col(self, ctx):
    if self.gtatools_prefix_col and self.gtatools_suffix_col:
        self.gtatools_suffix_col = ""


def _prewarm_dff_subsystem():
    """One-shot warmup that touches the slow lazily-initialised parts
    of Blender + the DFF import stack so the user's first
    Shift+A → GTA SA Model click doesn't pay the full cold-start cost.

    Cold-start budget on first DFF import:
      • bpy.data.materials/objects RNA init   ~200ms
      • first bpy.ops.object.select_all       ~100ms (undo bootstrap)
      • DFF parser numpy buffer setup         ~100ms
      • bmesh ops first call                  ~100ms

    We force all four here, well before the user clicks anything.
    Returning ``None`` from a timer callback means «don't repeat» —
    this runs exactly once per addon load.
    """
    try:
        # 1) Touch global collections — forces RNA init.
        _ = list(bpy.data.materials)
        _ = list(bpy.data.objects)
        # 2) Pull in the DFF + COL parser modules. They're already
        #    imported eagerly in this __init__.py, but referencing
        #    their hot symbols nudges any lazy submodule binding.
        from .core.dff import read_dff_file  # noqa: F401
        from .core.col import read_col_file  # noqa: F401
        from .ops.dff_import import import_dff  # noqa: F401
        # 3) numpy primitives — touch a small array so numpy's
        #    internal buffer pool gets allocated. The DFF parser
        #    creates large numpy arrays per-mesh; first allocation
        #    is the expensive one.
        try:
            import numpy as _np
            _np.zeros(16, dtype=_np.float32)
        except Exception:
            pass
    except Exception as e:
        print(f"[INU prewarm] skipped: {e}")
    return None  # don't reschedule


def _register_blender_translations():
    """Register the addon's localization with Blender's native i18n
    system so ``bl_label``/``bl_description`` translate dynamically
    when the user switches UI language.

    Background: ``T(...)`` is a regular Python function — when it
    appears as ``bl_label = T("Русский")`` it runs ONCE at class-
    definition time, the result is baked into ``bl_rna``, and never
    updates. Blender's own ``app.translations`` is the only way to
    have static class attributes follow locale changes — Blender
    consults the registered dict via ``pgettext_iface`` at draw time.

    Format: ``{locale: {(context, msg): translation}}``. Blender uses
    different contexts for different UI element types — panels often
    use ``"*"``, operators use ``"Operator"``, property names use
    ``"Property"`` etc. We register the SAME translation under the
    most common contexts so any UI element looking up our message
    finds it regardless of the context Blender picks.
    """
    from .locale import get_translation
    eng_dict = get_translation('eng')
    if not eng_dict:
        return

    # Mirror every entry across the contexts Blender consults for
    # different UI element kinds. Costs a few KiB of dict — negligible.
    contexts = ('*', 'Operator', 'Property', 'WindowManager')
    en_us_entries = {}
    for k, v in eng_dict.items():
        for ctx in contexts:
            en_us_entries[(ctx, k)] = v

    blender_dict = {'en_US': en_us_entries}

    # Idempotent — addon reload may otherwise hit «already registered».
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass
    try:
        bpy.app.translations.register(__name__, blender_dict)
    except Exception as e:
        print(f"[INU translations] register failed: {e}")


def _unregister_blender_translations():
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass


def register():
    # Hook the addon's localization into Blender's i18n FIRST — before
    # we touch class bl_descriptions. Once registered, raw Russian
    # strings on bl_label/bl_description get translated dynamically by
    # Blender at draw time when the user is on a non-Russian UI.
    _register_blender_translations()

    # Auto-fill operator tooltip from the class docstring when one
    # isn't explicitly set. We assign the *raw* Russian text rather
    # than T(...) — Blender's translation system above handles the
    # locale switch dynamically. Using T() here would snapshot the
    # text in whatever locale the addon loaded with and freeze it.
    for cls in classes:
        doc = getattr(cls, '__doc__', None)
        if doc and doc.strip():
            cls.bl_description = doc.strip()
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            # Already registered (addon reload without restart)
            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)

    # INU property groups
    bpy.types.Object.inu = bpy.props.PointerProperty(type=INUObjectProps)
    bpy.types.Material.inu = bpy.props.PointerProperty(type=INUMaterialProps)
    # Per-rig settings for Animated Map Object — exposes the live-edit
    # sliders (turns, duration, axis) on armatures tagged with
    # obj['inu_animobj']. Created/populated by GTATOOLS_OT_animobj_setup.
    bpy.types.Object.inu_animobj_props = bpy.props.PointerProperty(
        type=INUAnimObjProps)

    # Sort materials button in material context menu
    bpy.types.MATERIAL_MT_context_menu.append(_draw_sort_materials_menu)

    bpy.types.Scene.gtatools_lightmap_result = StringProperty(name="Result", default="")
    bpy.types.Scene.gtatools_lightmap_path = StringProperty(name="Lightmap Path", default="lightmaps/lightmap.png")

    # Pre-export validation results — refilled by GTATOOLS_OT_validate_run
    # and consumed by GTATOOLS_PT_validate_scene panel.
    bpy.types.Scene.inu_validate_issues = bpy.props.CollectionProperty(
        type=INUValidateIssue)

    # Collapsible-section state for the PARTICLE 2DFX editor panel
    # All Particle expert sections start collapsed for a clean panel.
    # The create_2dfx operator opens «Спрайт и смешивание» right after
    # creating a Particle effect so the user lands on the texture
    # picker without an extra click.
    bpy.types.Scene.gtatools_pfx_exp_texture = BoolProperty(default=False)
    bpy.types.Scene.gtatools_pfx_exp_color = BoolProperty(default=False)
    bpy.types.Scene.gtatools_pfx_exp_size = BoolProperty(default=False)
    bpy.types.Scene.gtatools_pfx_exp_emission = BoolProperty(default=False)
    bpy.types.Scene.gtatools_pfx_exp_physics = BoolProperty(default=False)
    bpy.types.Scene.gtatools_pfx_exp_system = BoolProperty(default=False)
    bpy.types.Scene.gtatools_pfx_exp_curves = BoolProperty(default=False)

    def _update_particle_sim(self, context):
        from .ops import particle_sim
        if self.gtatools_particle_sim:
            particle_sim.start_simulation()
        else:
            particle_sim.stop_simulation()

    bpy.types.Scene.gtatools_particle_sim = BoolProperty(
        name="Particle Simulation",
        description=T("Анимировать 2DFX частицы в viewport"),
        default=False,
        update=_update_particle_sim,
    )
    bpy.types.Scene.gtatools_model_id = StringProperty(name="Model ID", default="0")
    bpy.types.Scene.gtatools_vc_analysis = StringProperty(name="VC Analysis", default="")

    # Fill colors history on Object
    bpy.types.Object.gtatools_fill_colors = CollectionProperty(type=GTATOOLS_FillColorItem)

    # UV Grid Randomizer settings
    def update_uv_grid(self, context):
        # Force redraw UV editor
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.tag_redraw()

    bpy.types.Scene.gtatools_uv_grid_cols = IntProperty(
        name="Columns",
        description=T("Количество колонок в сетке текстуры"),
        default=3,
        min=1,
        max=16,
        update=update_uv_grid
    )
    bpy.types.Scene.gtatools_uv_grid_rows = IntProperty(
        name="Rows",
        description=T("Количество рядов в сетке текстуры"),
        default=2,
        min=1,
        max=16,
        update=update_uv_grid
    )

    from bpy.props import EnumProperty
    bpy.types.Scene.gtatools_uv_grid_align = EnumProperty(
        name="Alignment",
        description=T("Позиция UV в ячейке"),
        items=[
            ('CENTER', "Center", "Center of cell"),
            ('TOP_LEFT', "Top Left", "Top left corner"),
            ('TOP_CENTER', "Top", "Top center"),
            ('TOP_RIGHT', "Top Right", "Top right corner"),
            ('LEFT_CENTER', "Left", "Left center"),
            ('RIGHT_CENTER', "Right", "Right center"),
            ('BOTTOM_LEFT', "Bottom Left", "Bottom left corner"),
            ('BOTTOM_CENTER', "Bottom", "Bottom center"),
            ('BOTTOM_RIGHT', "Bottom Right", "Bottom right corner"),
        ],
        default='CENTER'
    )

    bpy.types.Scene.gtatools_uv_link_islands = BoolProperty(
        name="Link Polygons",
        description=T("Полигоны с пересекающимися UV перемещаются вместе"),
        default=False
    )

    # COL Light settings
    bpy.types.Scene.gtatools_col_day_min = IntProperty(
        name="Day Min", description=T("Минимальное значение дневного света (тень)"), default=10, min=0, max=15)
    bpy.types.Scene.gtatools_col_day_max = IntProperty(
        name="Day Max", description=T("Максимальное значение дневного света (свет)"), default=15, min=0, max=15)
    bpy.types.Scene.gtatools_col_night_min = IntProperty(
        name="Night Min", description=T("Минимальное значение ночного света (тень)"), default=0, min=0, max=15,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_night_max = IntProperty(
        name="Night Max", description=T("Максимальное значение ночного света (свет)"), default=5, min=0, max=15,
        update=_col_light_invalidate_preview)

    bpy.types.Scene.gtatools_col_light_edge = FloatProperty(
        name="Edge",
        description=T("Сдвиг границы COL освещения: + расширяет зелёную зону, — сужает"),
        default=0.0, min=-5.0, max=5.0, soft_min=-1.0, soft_max=1.0, step=1,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_light_threshold = IntProperty(
        name="Threshold",
        description=T("Порог яркости: 0 = без порога, 100 = максимальная отсечка"),
        default=0, min=0, max=100,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_light_contrast = FloatProperty(
        name="Contrast",
        description=T("Контраст: резкость перехода между тёмными и светлыми зонами"),
        default=0.0, min=0.0, max=5.0, soft_min=0.0, soft_max=1.0, step=1,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_light_font_size = IntProperty(
        name="Font Size",
        description=T("Размер цифр на полигонах"),
        default=13, min=6, max=36,
        update=_col_light_invalidate_preview)
    bpy.types.Scene.gtatools_col_light_show_numbers = BoolProperty(
        name="Show Numbers",
        description=T("Показать цифры на полигонах"),
        default=True)

    # IMG archive path
    bpy.types.Scene.gtatools_img_path = StringProperty(
        name="IMG Archive",
        description=T("Путь к .img архиву GTA SA для экспорта моделей"),
        default="",
        subtype='FILE_PATH',
        update=_save_paths,
    )
    bpy.types.Scene.gtatools_map_region = EnumProperty(
        name="Region",
        description=T("Район карты для импорта"),
        items=_get_map_region_items,
    )
    bpy.types.Scene.gtatools_profile_enabled = BoolProperty(
        name=T("Профайлер"),
        description=T("Замерять время операций и записывать отчёт в .inu_cache/_profile.log. Включай только для отладки — добавляет небольшой overhead на каждый шаг"),
        default=False,
    )
    bpy.types.Scene.gtatools_binary_ipls = CollectionProperty(
        type=GTATOOLS_BinaryIplEntry,
    )
    bpy.types.WindowManager.gtatools_txd_export_plan = CollectionProperty(
        type=GTATOOLS_TxdExportEntry,
    )
    bpy.types.WindowManager.gtatools_txd_export_plan_index = IntProperty(
        default=0,
    )
    bpy.types.Scene.gtatools_show_binary_ipls = BoolProperty(
        name="Show binary IPLs",
        description=T("Развернуть список бинарных IPL для галочек"),
        default=False,
    )
    bpy.types.Scene.gtatools_map_skip_2dfx = BoolProperty(
        name="Skip 2DFX",
        description=T("Не импортировать 2DFX-эффекты (лампы, частицы, ped attractors, sun glare) при импорте карты и DFF"),
        default=True,
    )
    bpy.types.Scene.gtatools_img_use_gta_dat = BoolProperty(
        name="Use gta.dat",
        description=T("Искать все IDE/IPL через gta.dat (нужна корневая папка игры)"),
        default=False,
    )
    bpy.types.Scene.gtatools_img_skip_lod = BoolProperty(
        name="Skip LOD",
        description=T("Пропустить LOD модели при импорте"),
        default=True,
    )
    bpy.types.Scene.gtatools_img_load_txd = BoolProperty(
        name="Load TXD",
        description=T("Загружать TXD текстуры вместе с DFF"),
        default=False,
    )
    bpy.types.Scene.gtatools_map_load_col = BoolProperty(
        name="Load COL",
        description=T("Загружать коллизии из кеша при импорте карты. Нужно для round-trip (импорт части карты → редактирование → экспорт в IMG другой сборки). При выключенном — только DFF геометрия, сцена легче"),
        default=False,
    )
    bpy.types.Scene.gtatools_map_group_by_ipl = BoolProperty(
        name="Group by IPL",
        description=T("Создавать отдельную коллекцию на каждый IPL-файл (Map_LAn, Map_LAs, Map_SF…) вместо одиночных Map_DFF_Far/Mid/Near. Удобно для скрытия районов целиком и для совместного редактирования карты. LOD-меши идут в коллекцию своего IPL вместе с обычными мешами"),
        default=True,
    )

    # Game root path (for gta.dat auto-discovery)
    bpy.types.Scene.gtatools_game_root = StringProperty(
        name="Game Root",
        description=T("Корневая папка GTA SA для автопоиска IDE/IPL/IMG"),
        default="",
        subtype='DIR_PATH',
        update=_save_paths,
    )

    # IDE / IPL paths
    bpy.types.Scene.gtatools_ide_path = StringProperty(
        name="IDE File",
        description=T("Путь к IDE файлу GTA SA для добавления/обновления записей"),
        default="",
        subtype='FILE_PATH',
        update=_save_paths,
    )
    bpy.types.Scene.gtatools_ipl_path = StringProperty(
        name="IPL File",
        description=T("Путь к IPL файлу GTA SA для добавления/обновления записей"),
        default="",
        subtype='FILE_PATH',
        update=_save_paths,
    )

    # NVIDIA Texture Tools settings
    bpy.types.Scene.gtatools_txd_auto_import = BoolProperty(
        name="Import TXD",
        description=T("Автоимпорт TXD текстур при импорте DFF"),
        default=True,
    )

    # Shared TXD — single TXD for multiple DFF models
    bpy.types.Scene.gtatools_shared_txd_name = StringProperty(
        name="Shared TXD Name",
        description=T("Имя общего TXD файла для нескольких DFF моделей"),
        default="",
    )

    bpy.types.Scene.gtatools_txd_import_path = StringProperty(
        name="TXD Import Folder",
        description=T("Папка для поиска TXD при импорте DFF (пусто = автопоиск в папке DFF)"),
        default="",
        subtype='DIR_PATH'
    )

    bpy.types.Scene.gtatools_nvtt_path = StringProperty(
        name="NVTT Path",
        description=T("Путь к папке NVIDIA Texture Tools (для GPU сжатия)"),
        default="",
        subtype='DIR_PATH',
        update=_save_paths,
    )

    bpy.types.Scene.gtatools_txd_use_gpu = BoolProperty(
        name="Use GPU",
        description=T("Использовать GPU (NVTT) для сжатия текстур"),
        default=False
    )

    bpy.types.Scene.gtatools_show_nvtt_settings = BoolProperty(
        name="Show NVTT Settings",
        description=T("Показать настройки NVTT"),
        default=False
    )

    bpy.types.Scene.gtatools_show_texture_settings = BoolProperty(
        name="Show Texture Settings",
        description=T("Показать настройки текстур"),
        default=False
    )

    bpy.types.Scene.gtatools_show_paths_settings = BoolProperty(
        name="Show Paths Settings",
        description=T("Показать пути IDE/IPL/IMG"),
        default=False
    )

    # Suffix settings
    bpy.types.Scene.gtatools_show_suffix_settings = BoolProperty(
        name="Show Suffix Settings",
        description=T("Показать настройки суффиксов"),
        default=False
    )

    bpy.types.Scene.gtatools_show_dff_flags = BoolProperty(
        name="Show DFF Flags",
        default=False
    )
    # 2DFX Light section collapse-state. All sections start closed
    # for a clean panel — the create_2dfx operator opens «Свойства»
    # right after creating a fresh Light effect so the user sees the
    # editable fields immediately without an extra click.
    bpy.types.Scene.gtatools_2dfx_show_props = BoolProperty(
        name="Show 2DFX Light Props", default=False)
    bpy.types.Scene.gtatools_2dfx_show_behavior = BoolProperty(
        name="Show 2DFX Behavior", default=False)
    bpy.types.Scene.gtatools_2dfx_show_shadow = BoolProperty(
        name="Show 2DFX Shadow", default=False)
    bpy.types.Scene.gtatools_2dfx_show_flags = BoolProperty(
        name="Show 2DFX Flags", default=False)
    bpy.types.Scene.gtatools_anim_tab = EnumProperty(
        name="Animation Tab",
        description=T("Раздел панели Анимации"),
        items=[
            ('CHAR', T("Персонажи"),
             T("IFP импорт/экспорт, применение анимации к скелету, IK Rig")),
            ('OBJ',  T("Объекты"),
             T("Animated Map Object — мельницы, краны, флюгеры")),
        ],
        default='CHAR',
    )
    # Active addon profile — controls which top-level panels appear in
    # the N-sidebar AND in what order. ALL = no filter, default zone
    # ordering. User profiles are JSON in INU_Preset/profiles/ with an
    # ordered `panels` list — position drives bl_order on activation.
    from .tools.profiles import (
        profile_enum_items, _on_profile_changed,
    )
    bpy.types.Scene.gtatools_profile = EnumProperty(
        name=T("Профиль"),
        description=T(
            "Какие панели показывать в N-sidebar и в каком порядке.\n"
            "Свои профили — INU_Preset/profiles/<name>.json"),
        items=profile_enum_items,
        update=_on_profile_changed,
    )
    # Click-to-pick / click-to-place state for the profile editor.
    # Empty = nothing picked; non-empty = bl_idname of the panel
    # currently «held» by the user, waiting for a place click.
    bpy.types.Scene.gtatools_profile_picked = StringProperty(
        name="Profile Picked Panel",
        default="",
    )
    bpy.types.Scene.gtatools_show_ide_flags = BoolProperty(
        name="Show IDE Flags",
        description=T("Показать флаги IDE"),
        default=False
    )
    bpy.types.Scene.gtatools_suffix_dff = StringProperty(
        name="DFF Suffix", default="_DFF", update=_upd_suffix_dff,
        description=T("Суффикс для DFF моделей"),
    )
    bpy.types.Scene.gtatools_suffix_lod = StringProperty(
        name="LOD Suffix", default="_LOD", update=_upd_suffix_lod,
        description=T("Суффикс для LOD моделей"),
    )
    bpy.types.Scene.gtatools_suffix_col = StringProperty(
        name="COL Suffix", default="_COL", update=_upd_suffix_col,
        description=T("Суффикс для COL моделей"),
    )
    bpy.types.Scene.gtatools_prefix_dff = StringProperty(
        name="DFF Prefix", default="", update=_upd_prefix_dff,
        description=T("Префикс для DFF моделей"),
    )
    bpy.types.Scene.gtatools_prefix_lod = StringProperty(
        name="LOD Prefix", default="", update=_upd_prefix_lod,
        description=T("Префикс для LOD моделей"),
    )
    bpy.types.Scene.gtatools_prefix_col = StringProperty(
        name="COL Prefix", default="", update=_upd_prefix_col,
        description=T("Префикс для COL моделей"),
    )

    # ID Manager
    # X Radar Maker
    bpy.types.Scene.gtatools_radar_output = StringProperty(
        name="Radar Output",
        subtype='DIR_PATH',
        default="",
        description=T("Папка для сохранения тайлов радара"),
    )
    bpy.types.Scene.gtatools_radar_grid = IntProperty(
        name="Radar Grid",
        default=8,
        min=1, max=16,
        description=T("Размер сетки (8 = 64 тайла)"),
    )
    bpy.types.Scene.gtatools_radar_size = IntProperty(
        name="Radar Tile Size",
        default=256,
        min=64, max=4096,
        description=T("Размер тайла в пикселях"),
    )
    bpy.types.Scene.gtatools_radar_height = FloatProperty(
        name="Radar Height",
        default=3000.0,
        min=100.0,
        description=T("Высота камеры"),
    )
    bpy.types.Scene.gtatools_radar_gamma = FloatProperty(
        name="Radar Gamma",
        default=1.0,
        min=0.1, max=5.0,
    )
    bpy.types.Scene.gtatools_radar_specific = StringProperty(
        name="Radar Specific",
        default="",
        description=T("Индексы тайлов через запятую (0,1,5,63)"),
    )

    bpy.types.Scene.gtatools_show_img_list = BoolProperty(
        name="Show IMG List",
        default=False
    )
    bpy.types.Scene.gtatools_img_entries = CollectionProperty(type=GTATOOLS_ImgFileEntry)
    bpy.types.Scene.gtatools_img_entries_index = IntProperty(default=0)
    bpy.types.Scene.gtatools_show_id_manager = BoolProperty(
        name="Show ID Manager",
        description=T("Показать менеджер ID"),
        default=False
    )
    bpy.types.Scene.gtatools_id_search = StringProperty(
        name="ID Search",
        description=T("Поиск по ID или имени модели"),
        default=""
    )
    bpy.types.Scene.gtatools_id_page = IntProperty(
        name="ID Page",
        default=0,
        min=0,
        soft_max=1000,
    )
    bpy.types.Scene.gtatools_id_preset = EnumProperty(
        name=T("Пресет ID"),
        description=T("Активный файл со списком ID. Каждый пресет — отдельный .txt в папке data/id_presets/"),
        items=_get_id_preset_items,
        update=_id_preset_update,
    )
    bpy.types.Scene.gtatools_id_show_service = BoolProperty(
        name=T("Показать сервисные кнопки"),
        description=T(
            "Развернуть редкие операции: импорт ID из игры, "
            "расширение FLA, очистка фантомов, открыть файл ID"),
        default=False,
    )
    # Texture loader paths
    bpy.types.Scene.gtatools_texture_path1 = StringProperty(
        name="System Textures Path",
        description=T("Путь к папке с системными текстурами GTA"),
        default="",
        subtype='DIR_PATH',
        update=_save_paths,
    )
    bpy.types.Scene.gtatools_texture_path2 = StringProperty(
        name="Blend Folder Path",
        description=T("Путь к папке где находится .blend файл"),
        default="",
        subtype='DIR_PATH',
        update=_save_paths,
    )

    # IFP action selector — update callback re-binds the live preview
    # to the new selection so users don't have to click Preview again
    # for every animation while browsing 294 vanilla anims.
    def _ifp_action_changed(self, context):
        try:
            from .ops.ifp_import import preview_is_active, preview_start
        except Exception:
            return
        if not preview_is_active():
            return
        arm = context.active_object
        if not arm or arm.type != 'ARMATURE':
            return
        name = self.gtatools_ifp_action
        if not name:
            return
        # Restart the handler against the new animation. preview_start
        # keeps the saved_action stash because saved_action is only set
        # on first enable (see preview_start guard).
        preview_start(arm, name)

    # IK rig display preferences — read by ops.ik_rig.add_ik_rig when
    # creating empties. Changing them later doesn't update existing
    # empties; user re-runs Add IK Rig (idempotent for same skeleton).
    from .ops.ik_rig import EMPTY_TYPES as _IK_EMPTY_TYPES
    bpy.types.Scene.gtatools_ik_display = EnumProperty(
        name=T("Форма IK-эмпти"),
        description=T("Какой примитив рисовать на IK-target и pole"),
        items=_IK_EMPTY_TYPES,
        default='SPHERE',
    )
    def _on_ik_color_change(self, context):
        # Repaint every existing IK control bone in every rigged
        # armature. Custom palette must be set for ``custom`` to
        # be writable on the BoneColor object.
        rgb = tuple(self.gtatools_ik_color)[:3]
        for arm in bpy.data.objects:
            if arm.type != 'ARMATURE' or not arm.get('inu_ik_rigged'):
                continue
            for pb in arm.pose.bones:
                db = arm.data.bones.get(pb.name)
                if db is None or not db.get('inu_ik_control'):
                    continue
                try:
                    pb.color.palette = 'CUSTOM'
                    pb.color.custom.normal = rgb
                    pb.color.custom.select = rgb
                    pb.color.custom.active = rgb
                except Exception:
                    pass

    bpy.types.Scene.gtatools_ik_color = FloatVectorProperty(
        name=T("Цвет IK-контроллов"),
        description=T(
            "Цвет всех IK-контрольных костей (запястья, ступни, "
            "локти, колени, голова, корень). Применяется через "
            "Bone Color → CUSTOM. Изменение применяется ко всем "
            "существующим ригам сразу"),
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(0.2, 1.0, 0.2, 1.0),
        update=_on_ik_color_change,
    )

    def _on_floor_offset_change(self, context):
        # Push the new value to every live foot Floor constraint so
        # the slider feels like a global "raise the collision plane"
        # control rather than a "next time" preference.
        for arm in bpy.data.objects:
            if arm.type != 'ARMATURE' or not arm.get('inu_ik_rigged'):
                continue
            for pb in arm.pose.bones:
                for c in pb.constraints:
                    if (c.type == 'FLOOR'
                            and c.name.startswith('INU_IK_')):
                        c.offset = float(self.gtatools_floor_offset)

    bpy.types.Scene.gtatools_floor_offset = FloatProperty(
        name=T("Коллизия"),
        description=T(
            "Высота виртуальной коллизии над плоскостью-полом. "
            "Стопы IK-рига упираются на эту высоту ВЫШЕ плоскости "
            "— компенсирует толщину подошвы. Изменение применяется "
            "к существующим ригам сразу"),
        default=0.05,
        min=0.0,
        max=1.0,
        step=1,        # 0.01 per arrow click
        precision=3,
        subtype='DISTANCE',
        update=_on_floor_offset_change,
    )

    bpy.types.Scene.gtatools_ik_extras_show = BoolProperty(
        name=T("Дополнительно"),
        description=T("Настройки пола, коллизии, цвета IK, плюс "
                      "редкие утилиты (round-trip, batch-импорт)"),
        default=False,
    )

    bpy.types.Scene.gtatools_ik_root_motion = BoolProperty(
        name=T("Root motion"),
        description=T("Включить для анимаций которые двигают "
                      "персонажа по миру (walk/run/jump): IK_root "
                      "цепляется на топ-кость скелета. По умолчанию "
                      "выключено — IK_root сидит на Pelvis, что "
                      "удобнее для idle/crouch/aim/static, где root "
                      "должен оставаться в (0,0,0)"),
        default=False,
    )

    bpy.types.Scene.gtatools_anim_tools_show = BoolProperty(
        name=T("Настройка анимации"),
        description=T("Утилиты для исправления sign-discontinuities, "
                      "коррекций по диапазону кадров и т.п."),
        default=False,
    )
    bpy.types.Scene.gtatools_anim_fix_start = IntProperty(
        name=T("Старт"),
        description=T("Первый кадр диапазона (включительно)"),
        default=0, min=0,
    )
    bpy.types.Scene.gtatools_anim_fix_end = IntProperty(
        name=T("Конец"),
        description=T("Последний кадр диапазона (включительно)"),
        default=10000, min=0,
    )

    def _on_chain_offset_change(self, context):
        # Visual offset for chain (hand/foot) IK control cubes —
        # custom_shape_translation moves the rendered shape only,
        # bone math (IK target position) stays put. Lets the user
        # align the cube with the actual mesh hand/foot when SA
        # skinning offsets the mesh from the bone.
        offset = tuple(self.gtatools_ik_chain_offset)
        for arm in bpy.data.objects:
            if arm.type != 'ARMATURE' or not arm.get('inu_ik_rigged'):
                continue
            for pb in arm.pose.bones:
                db = arm.data.bones.get(pb.name)
                if db is None or not db.get('inu_ik_control'):
                    continue
                ct = db.get('inu_ik_ctrl_type')
                if ct != 'chain':
                    continue
                try:
                    pb.custom_shape_translation = offset
                except Exception:
                    pass

    bpy.types.Scene.gtatools_ik_chain_offset = FloatVectorProperty(
        name=T("Смещение куба руки/ноги"),
        description=T(
            "Визуальный сдвиг кубов IK для рук и ног (X, Y, Z). "
            "Двигает только отображение — позиция самой кости и "
            "цели IK не меняется. Тюнится через Python: "
            "``bpy.context.scene.gtatools_ik_chain_offset = "
            "(x, y, z)``"),
        size=3,
        subtype='TRANSLATION',
        default=(0.0, 0.0, 0.0),
        precision=3,
        update=_on_chain_offset_change,
    )

    # ── IK control size + visibility ────────────────────────────
    _IK_BASE_SIZES = {
        'chain': 0.08, 'head': 0.08, 'rot': 0.08,
        'pole':  0.04, 'root': 0.16,
    }

    def _derive_ik_type(name):
        # Fallback when ``inu_ik_ctrl_type`` custom prop is missing
        # (rigs created before that prop was introduced). Names follow
        # the ``INU_IK_<short>[_pole]`` convention so the type is
        # derivable: hand/foot chains, elbow/knee poles, head/spine1/
        # shoulder rotation controls, single root.
        if not name.startswith('INU_IK_'):
            return None
        if name.endswith('_pole'):
            return 'pole'
        suffix = name[len('INU_IK_'):]
        if suffix in {'R_arm', 'L_arm', 'R_leg', 'L_leg'}:
            return 'chain'
        if suffix == 'root':
            return 'root'
        return 'rot'

    def _ctrl_type_of(db):
        return db.get('inu_ik_ctrl_type') or _derive_ik_type(db.name)

    def _on_ik_size_change(self, context):
        # Live-resize every IK control widget across every rigged
        # armature. ``custom_shape_scale_xyz`` is the only knob —
        # ``use_custom_shape_bone_size`` is already False so the
        # scalar applies directly without bone-length coupling.
        mult = float(self.gtatools_ik_size)
        for arm in bpy.data.objects:
            if arm.type != 'ARMATURE' or not arm.get('inu_ik_rigged'):
                continue
            for pb in arm.pose.bones:
                db = arm.data.bones.get(pb.name)
                if db is None or not db.get('inu_ik_control'):
                    continue
                ct = _ctrl_type_of(db) or 'chain'
                base = _IK_BASE_SIZES.get(ct, 0.08)
                size = base * mult
                try:
                    pb.custom_shape_scale_xyz = (size, size, size)
                except Exception:
                    pass

    bpy.types.Scene.gtatools_ik_size = FloatProperty(
        name=T("Размер"),
        description=T("Множитель размера всех IK-контролов "
                      "(кубов). 1.0 = по умолчанию, 0.5 = вдвое "
                      "меньше. Применяется к существующим ригам "
                      "сразу"),
        default=1.0,
        min=0.1,
        max=5.0,
        step=10,        # 0.1 per arrow click
        precision=2,
        update=_on_ik_size_change,
    )

    # Map type → bone collection name. Stays in sync with
    # ops.ik_rig._IK_COLL_* constants.
    _IK_TYPE_TO_COLL = {
        'chain': 'INU_IK_Chain',
        'pole':  'INU_IK_Pole',
        'rot':   'INU_IK_Rot',
        'head':  'INU_IK_Rot',  # legacy alias
        'root':  'INU_IK_Root',
    }

    def _make_visibility_setter(ctrl_types):
        # Build an update callback that toggles bone-collection
        # visibility for every rigged armature. Falls back to
        # ``Bone.hide`` per-bone if the rig was created before
        # collections were introduced. Both paths force a viewport
        # redraw via tag_redraw / update_tag so the change is
        # immediately visible.
        def _setter(self, context):
            attr = ctrl_types[1]
            visible = bool(getattr(self, attr))
            type_set = ctrl_types[0]
            coll_names = {_IK_TYPE_TO_COLL[t] for t in type_set
                          if t in _IK_TYPE_TO_COLL}

            for arm in bpy.data.objects:
                if (arm.type != 'ARMATURE'
                        or not arm.get('inu_ik_rigged')):
                    continue

                bone_colls = getattr(arm.data, 'collections', None)
                touched_via_collection = set()
                if bone_colls is not None:
                    for cname in coll_names:
                        coll = bone_colls.get(cname)
                        if coll is None:
                            continue
                        coll.is_visible = visible
                        try:
                            for bone in coll.bones:
                                touched_via_collection.add(bone.name)
                        except Exception:
                            pass

                # Fallback for bones not yet in any IK collection
                # (e.g. rig saved with an earlier addon version):
                # toggle Bone.hide directly.
                for db in arm.data.bones:
                    if db.name in touched_via_collection:
                        continue
                    if not db.get('inu_ik_control'):
                        continue
                    if _ctrl_type_of(db) in type_set:
                        db.hide = not visible

                arm.data.update_tag()

            if context.area is not None:
                context.area.tag_redraw()
        return _setter

    bpy.types.Scene.gtatools_ik_show_chain = BoolProperty(
        name=T("Руки/ноги"),
        description=T("Показывать кубы запястий и ступней "
                      "(IK target'ы)"),
        default=True,
        update=_make_visibility_setter(
            (frozenset({'chain'}), 'gtatools_ik_show_chain')),
    )
    bpy.types.Scene.gtatools_ik_show_pole = BoolProperty(
        name=T("Локти/колени"),
        description=T("Показывать кубы-маркеры на локтях и "
                      "коленях (pole_target'ы)"),
        default=True,
        update=_make_visibility_setter(
            (frozenset({'pole'}), 'gtatools_ik_show_pole')),
    )
    bpy.types.Scene.gtatools_ik_show_rot = BoolProperty(
        name=T("Голова/торс/плечи"),
        description=T("Показывать кубы головы, верхнего торса "
                      "(Spine1) и ключиц"),
        default=True,
        update=_make_visibility_setter(
            (frozenset({'rot', 'head'}), 'gtatools_ik_show_rot')),
    )
    bpy.types.Scene.gtatools_ik_show_root = BoolProperty(
        name=T("Корень"),
        description=T("Показывать корневой куб (мастер-контроль "
                      "всего скелета)"),
        default=True,
        update=_make_visibility_setter(
            (frozenset({'root'}), 'gtatools_ik_show_root')),
    )

    bpy.types.Scene.gtatools_ifp_action = StringProperty(
        name="IFP Action",
        description="Select IFP animation to apply",
        update=_ifp_action_changed,
    )


    # Water settings
    bpy.types.Scene.gtatools_water_flag = EnumProperty(
        name="Water Type",
        description="Water polygon visibility and depth type",
        items=[
            ('0', T("Обычная / Невидимая"), T("Глубокая вода, не отображается (подводные зоны)")),
            ('1', T("Обычная / Видимая"), T("Глубокая вода с волнами (океан, реки)")),
            ('2', T("Мелкая / Невидимая"), T("Мелкая вода, не отображается (анимация хождения по воде)")),
            ('3', T("Мелкая / Видимая"), T("Мелкая вода, отображается (лужи, пруды)")),
        ],
        default='1',
    )
    bpy.types.Scene.gtatools_water_speed_x = FloatProperty(
        name="Speed X", default=0.0, min=-5.0, max=5.0
    )
    bpy.types.Scene.gtatools_water_speed_y = FloatProperty(
        name="Speed Y", default=0.0, min=-5.0, max=5.0
    )
    bpy.types.Scene.gtatools_water_speed_z = FloatProperty(
        name="Speed Z", default=0.05, min=-5.0, max=5.0
    )
    bpy.types.Scene.gtatools_water_wave_height = FloatProperty(
        name="Wave Height", default=0.1, min=0.0, max=10.0
    )

    # Bake settings (calibrated for 3Ds Max-like output)
    bpy.types.Scene.gtatools_bake_ambient = FloatProperty(
        name="Ambient",
        description=T("Базовый рассеянный свет (ниже = темнее тени)"),
        default=0.10,
        min=0.0,
        max=0.5
    )
    bpy.types.Scene.gtatools_bake_intensity = FloatProperty(
        name="Intensity",
        description=T("Множитель интенсивности света (ниже = темнее)"),
        default=0.05,
        min=0.0001,
        max=0.5
    )
    bpy.types.Scene.gtatools_bake_gamma = FloatProperty(
        name="Gamma",
        description=T("Гамма-коррекция (ниже = темнее)"),
        default=0.50,
        min=0.1,
        max=3.0
    )

    bpy.types.Scene.gtatools_bake_shadows = BoolProperty(
        name="Shadows",
        description=T("Включить тени при запекании (raycast проверка перекрытий)"),
        default=True
    )

    # ── Modulate Color preview ──────────────────────────────────────
    # Three-state preview: OFF (чистый prelight) / DAY / NIGHT.
    # Каждый режим хардкодит пресет из ванильного timecyc.dat
    # (EXTRASUNNY_LA Midday / Midnight): ambient_obj + два аддитивных
    # post-fx тинта. Имитирует ванильную формулу (см. euryopa
    # pcBuildingVS.hlsl + CPostEffects::ColourFilter из
    # gta-reversed-modern).
    def _on_modulate_preview_update(self, context):
        from .tools.prelight import apply_modulate_preview
        apply_modulate_preview(context.scene)

    bpy.types.Scene.gtatools_modulate_mode = EnumProperty(
        name="Modulate Color",
        description=T("Preview-режим: OFF — чистый prelight, Day/Night — добавить ambient как игра при Modulate Color = ON. Vcols и DFF-флаги не трогаются"),
        items=[
            ('OFF',   "Off",   T("Без ambient — только prelight")),
            ('DAY',   "Day",   T("EXTRASUNNY_LA Midday из timecyc.dat")),
            ('NIGHT', "Night", T("EXTRASUNNY_LA Midnight из timecyc.dat")),
        ],
        default='OFF',
        update=_on_modulate_preview_update,
    )
    bpy.types.Scene.gtatools_modulate_mix = FloatProperty(
        name="Прозрачность",
        description=T("Сколько ambient добавлять к prelight: 0 — без ambient (только prelight), 1 — полный ambient. Аналог surfAmbient материала из ванильного шейдера"),
        default=0.002,
        min=0.0, max=1.0,
        precision=3,
        subtype='FACTOR',
        update=_on_modulate_preview_update,
    )
    bpy.types.Scene.gtatools_modulate_contrast = FloatProperty(
        name="Контраст",
        description=T("Контраст финального изображения. 0 — без изменений, отрицательные — мягче, положительные — резче"),
        default=0.0,
        min=-1.0, max=1.0,
        subtype='FACTOR',
        update=_on_modulate_preview_update,
    )
    bpy.types.Scene.gtatools_modulate_gamma = FloatProperty(
        name="Гамма",
        description=T("Гамма финального изображения. 1.0 — без изменений, <1 — светлее, >1 — темнее"),
        default=0.8,
        min=0.1, max=4.0,
        update=_on_modulate_preview_update,
    )

    bpy.types.Scene.gtatools_prelight_preset = EnumProperty(
        name="Prelight Preset",
        items=_get_preset_items,
        description=T("Выбрать пресет настроек прелайта"),
    )

    # V offset for night prelight
    bpy.types.Scene.gtatools_v_offset = FloatProperty(
        name="V Offset",
        description=T("Смещение яркости как в 3Ds Max Adjust Color V (-80 для ночи)"),
        default=0.0,
        min=-100.0,
        max=100.0
    )

    # Post-processing vertex colors
    bpy.types.Scene.gtatools_vc_smooth_iterations = IntProperty(
        name="Iterations",
        description=T("Количество итераций сглаживания"),
        default=1,
        min=1,
        max=50
    )
    bpy.types.Scene.gtatools_vc_smooth_factor = FloatProperty(
        name="Factor",
        description=T("Сила сглаживания (0 = без изменений, 1 = полное усреднение)"),
        default=0.5,
        min=0.0,
        max=1.0
    )
    bpy.types.Scene.gtatools_vc_contrast = FloatProperty(
        name="Contrast",
        description=T("Контраст (1 = без изменений, <1 = меньше, >1 = больше)"),
        default=1.0,
        min=0.0,
        max=3.0
    )
    bpy.types.Scene.gtatools_vc_brightness = FloatProperty(
        name="Brightness",
        description=T("Яркость смещение (-1..+1)"),
        default=0.0,
        min=-1.0,
        max=1.0
    )
    bpy.types.Scene.gtatools_vc_gamma = FloatProperty(
        name="Gamma",
        description=T("Гамма-коррекция (1 = без изменений, <1 = светлее, >1 = темнее)"),
        default=1.0,
        min=0.1,
        max=3.0
    )

    # Vertex paint - fill color
    bpy.types.Scene.gtatools_fill_color = FloatVectorProperty(
        name="Fill Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0
    )

    # Vertex paint - scatter light settings
    bpy.types.Scene.gtatools_scatter_intensity = FloatProperty(
        name="Intensity",
        description=T("Интенсивность рассеивания света"),
        default=1.0,
        min=0.1,
        max=5.0
    )
    bpy.types.Scene.gtatools_scatter_falloff = FloatProperty(
        name="Falloff",
        description=T("Скорость затухания света (выше = быстрее)"),
        default=1.5,
        min=0.5,
        max=5.0
    )
    bpy.types.Scene.gtatools_scatter_iterations = IntProperty(
        name="Iterations",
        description=T("Количество слоёв соседних граней"),
        default=3,
        min=1,
        max=10
    )
    bpy.types.Scene.gtatools_scatter_radius = FloatProperty(
        name="Radius",
        description=T("Радиус поиска соседних граней (0 = авто по размеру грани)"),
        default=0.0,
    )

    # Pipeline selector for export
    bpy.types.Scene.gtatools_export_pipeline = EnumProperty(
        items=[
            ('NONE', 'None',
             T("Без указания pipeline — использовать стандартный рендер RenderWare. Подходит для простых объектов, которым не нужны специальные эффекты движка")),
            ('0x53F2009A', 'Vehicle',
             T("Pipeline кузова машины (RSPIPE_PC_CustomCarEnvMap). Добавляет env-map отражения неба/облаков/улицы. Используется совместно с текстурами vehicleenv128 + vehiclespecdot64 на материале")),
            ('0x53F20098', 'Day/Night',
             T("Pipeline здания с day/night vertex colors (RSPIPE_PC_CustomBuildingDN). Движок плавно смешивает дневной и ночной слои vertex colors по игровому времени. Требует ДВА Color Attribute слоя (Day + Night) на меше. Mesh-флаги Day/Night здесь не нужны — переход делает pipeline через VC")),
            ('0x53F2009C', 'Building',
             T("Простой pipeline здания (RSPIPE_PC_CustomBuilding). Статическое освещение через один слой vertex colors. Работает быстрее чем Day/Night, но нет смены по времени суток")),
        ],
        name="Pipeline",
        description=T("Рендер-пайплайн для экспорта DFF"),
        default='NONE',
    )

    from .tools.gta_material_panel import preset_items as _mat_preset_items
    bpy.types.Scene.gtatools_material_preset = EnumProperty(
        items=_mat_preset_items,
        name="GTA Material Preset",
    )

    # Export settings
    bpy.types.Scene.gtatools_export_all_dff = BoolProperty(
        name="Export DFF",
        description=T("Экспортировать DFF при Export All"),
        default=True
    )
    bpy.types.Scene.gtatools_export_all_col = BoolProperty(
        name="Export COL",
        description=T("Экспортировать COL при Export All"),
        default=True
    )
    bpy.types.Scene.gtatools_export_all_lod = BoolProperty(
        name="Export LOD",
        description=T("Экспортировать LOD при Export All"),
        default=True
    )
    bpy.types.Scene.gtatools_export_all_txd = BoolProperty(
        name="Export TXD",
        description=T("Экспортировать TXD при Export All"),
        default=True
    )
    bpy.types.Scene.gtatools_export_all_col_library = BoolProperty(
        name=T("COL Library"),
        description=T("Писать все коллизии в один .col файл (multi-entry library). Каждая запись в файле — отдельная коллизия со своим model_id, сопоставляется с DFF по ID"),
        default=False,
    )
    bpy.types.Scene.gtatools_export_all_col_library_name = StringProperty(
        name=T("Имя library .col"),
        description=T("Имя общего .col файла без расширения (например 'district' → district.col)"),
        default="collision",
    )
    bpy.types.Scene.gtatools_export_all_txd_shared = BoolProperty(
        name=T("Shared TXD"),
        description=T("Писать все текстуры в один общий .txd файл вместо отдельного .txd на каждую модель. Полезно для районов и сборок где множество моделей делят одни и те же текстуры"),
        default=False,
    )
    bpy.types.Scene.gtatools_export_all_txd_shared_name = StringProperty(
        name=T("Имя общего .txd"),
        description=T("Имя общего .txd файла без расширения (например 'district' → district.txd)"),
        default="textures",
    )

    # Keymap: Shift+T — toggle UV Editor
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('gtatools.toggle_uv_editor', 'T', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

    # File > Export / Import menus
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    # Add > GTA SA submenu
    bpy.types.VIEW3D_MT_add.append(_gtasa_add_menu_draw)

    # Pre-warm DFF import path so the user's first Shift+A → GTA SA
    # Model click is fast. Without this, the first click takes 1-3s
    # because Blender does cold-start work (RNA init for materials/
    # objects collections, first bpy.ops call setting up undo, numpy
    # JIT, bmesh setup) ON the call. Subsequent clicks are instant.
    # Run after a short delay so the UI doesn't stutter during
    # addon load — by the time the user actually hits Shift+A this
    # has long completed.
    bpy.app.timers.register(_prewarm_dff_subsystem,
                            first_interval=2.0)

    # 2DFX real-time preview handler
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update_2dfx)

    # 2DFX billboard rotation timer — start now and restart on file load
    from .ops.fx_preview import start_billboard_timer
    start_billboard_timer()
    bpy.app.handlers.load_post.append(_on_file_load_restart_timer)
    bpy.app.handlers.load_post.append(_on_file_load_restore_paths)
    bpy.app.handlers.load_post.append(_on_file_load_migrate_modulate)
    # Run migration once at register too — для уже открытой сцены.
    try:
        _on_file_load_migrate_modulate(None)
    except Exception:
        pass

    # Deferred load paths (context.scene not available during register)
    def _deferred_load_paths():
        try:
            _load_paths(bpy.context.scene)
        except:
            pass
        return None
    bpy.app.timers.register(_deferred_load_paths, first_interval=0.5)

    # VC Layer System — per-mesh stack of editing layers that compose
    # into Day / Night at export-flatten time. Stored on Mesh (data)
    # so linked-duplicate objects share the same layer stack.
    # Wrapped in try/except so a VCL bug never takes out the whole
    # addon — better to log loudly and keep the rest of the operators
    # functional than to leave the user with nothing.
    try:
        bpy.types.Mesh.gtatools_vc_layers = CollectionProperty(
            type=GTATOOLS_VCLayerItem)
        bpy.types.Mesh.gtatools_vc_active_layer = IntProperty(
            name="Active VC Layer", default=0, min=0,
            update=_vc_on_active_layer_change)
        bpy.types.Mesh.gtatools_vc_edit_target = EnumProperty(
            name=T("Стек"),
            items=[
                ('DAY',   T("Day"),   T("Редактируем Day-стек")),
                ('NIGHT', T("Night"), T("Редактируем Night-стек")),
            ],
            default='DAY',
        )
        bpy.types.Mesh.gtatools_vc_multi_mode = EnumProperty(
            name=T("Multi-edit"),
            description=T("Как групповые слайдеры применяются к выделенным слоям"),
            items=[
                ('ABSOLUTE', T("Absolute"),
                    T("Все выделенные получают одинаковое значение")),
                ('RELATIVE', T("Relative"),
                    T("Все выделенные сдвигаются на одну дельту от текущего")),
            ],
            default='ABSOLUTE',
        )
        bpy.types.Mesh.gtatools_vc_live_preview = BoolProperty(
            name=T("Live preview"),
            description=T("Авто-композиция стека при изменении любого слайдера или мазке кистью"),
            default=False,
            update=_vc_on_live_preview_toggle,
        )
        # Tracks which scope the VCL_PREVIEW buffer currently holds so
        # the panel can show «Preview: Day» / «Preview: Night» and the
        # update hook on layer sliders knows whether a same-scope edit
        # warrants a refresh.
        bpy.types.Mesh.gtatools_vc_preview_scope = EnumProperty(
            name="Preview Scope",
            items=[
                ('DAY',   "Day",   ""),
                ('NIGHT', "Night", ""),
            ],
            default='DAY',
            options={'HIDDEN'},
        )
        # Multi-edit scratch values — separate from per-layer fields so
        # adjusting them doesn't accidentally fire per-layer update
        # callbacks. User clicks "Apply" to push them to selected layers.
        bpy.types.Mesh.gtatools_vc_multi_opacity = FloatProperty(
            name="Multi Opacity", default=1.0, min=0.0, max=1.0,
            subtype='FACTOR')
        bpy.types.Mesh.gtatools_vc_multi_brightness = FloatProperty(
            name="Multi Brightness", default=0.0, min=-1.0, max=1.0,
            subtype='FACTOR')
        bpy.types.Mesh.gtatools_vc_multi_contrast = FloatProperty(
            name="Multi Contrast", default=1.0, min=0.0, max=3.0)
        # Section-expanded toggle for the inline «Слои Vertex Color»
        # block in the prelight panel. Stored on Scene (not Mesh) so
        # the user's collapsed/expanded preference persists across
        # the active object — switching meshes shouldn't fold the
        # section every time.
        bpy.types.Scene.gtatools_vc_layers_expanded = BoolProperty(
            name="VC Layers Section Expanded",
            default=False,
        )
        vc_layers_register_handlers()
    except Exception as _e:
        import traceback
        print(f"[GTA Tools] VC Layer System register failed: {_e}")
        traceback.print_exc()

    print("[GTA Tools Panel] Addon registered!")


@persistent
def _on_file_load_restore_paths(dummy):
    """Restore saved paths after loading a .blend file."""
    _load_paths(bpy.context.scene)


# ── Migrate stale Modulate Color defaults ────────────────────────
# Property defaults применяются только к новым сценам. Если в .blend
# было сохранено значение со старым дефолтом, оно останется. Этот
# хендлер один раз поднимает старые значения до новых.
_MODULATE_DEFAULT_MIGRATIONS = {
    'gtatools_modulate_gamma': [(0.7, 0.8)],  # old → new
}


@persistent
def _on_file_load_migrate_modulate(dummy):
    """Bump scene's Modulate Color values from stale old defaults to new."""
    for scn in bpy.data.scenes:
        for prop_name, pairs in _MODULATE_DEFAULT_MIGRATIONS.items():
            try:
                cur = float(getattr(scn, prop_name))
            except (AttributeError, TypeError):
                continue
            for old, new in pairs:
                if abs(cur - old) < 1e-6:
                    setattr(scn, prop_name, new)
                    break


@persistent
def _on_file_load_restart_timer(dummy):
    """Restart billboard timer after loading a new .blend file."""
    print("[2DFX] load_post handler fired — scheduling timer restart in 1s...")
    def _delayed_start():
        print("[2DFX] Delayed start — restarting billboard timer now")
        from .ops.fx_preview import start_billboard_timer
        start_billboard_timer()
        return None
    bpy.app.timers.register(_delayed_start, first_interval=1.0)


_2dfx_sync_busy = False

def _on_depsgraph_update_2dfx(scene, depsgraph):
    """Auto-sync 2DFX preview when properties change in UI."""
    global _2dfx_sync_busy

    # Ensure billboard timer is alive (restart after scene switch etc.)
    try:
        from .ops.fx_preview import _update_billboard_rotations, start_billboard_timer
        import bpy as _bpy
        if not _bpy.app.timers.is_registered(_update_billboard_rotations):
            start_billboard_timer()
    except Exception:
        pass

    if _2dfx_sync_busy:
        return
    try:
        obj = bpy.context.active_object
    except Exception:
        return
    if not obj or obj.type != 'EMPTY':
        return
    inu = getattr(obj, 'inu', None)
    if not inu or inu.type != '2DFX' or inu.effect_2dfx != 'LIGHT':
        return
    # Only run if this object has preview children
    has_children = any(
        getattr(c, 'inu', None) and c.inu.type == 'NON'
        for c in obj.children
    )
    if not has_children:
        return
    _2dfx_sync_busy = True
    try:
        from .ops.fx_preview import sync_preview_from_props
        sync_preview_from_props(obj)
    except Exception:
        pass
    finally:
        _2dfx_sync_busy = False


def unregister():
    # Drop our locale dict before any classes go away — keeps Blender's
    # translation table clean across addon reloads.
    _unregister_blender_translations()

    # 2DFX billboard timer
    from .ops.fx_preview import stop_billboard_timer
    stop_billboard_timer()

    # IFP live preview — unregister frame-change handler so reload
    # doesn't leave a stale callable pointing at the old module.
    try:
        from .ops.ifp_import import preview_stop
        preview_stop()
    except Exception:
        pass

    # 2DFX handlers
    if _on_depsgraph_update_2dfx in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update_2dfx)
    if _on_file_load_restart_timer in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_file_load_restart_timer)
    if _on_file_load_restore_paths in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_file_load_restore_paths)
    if _on_file_load_migrate_modulate in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_file_load_migrate_modulate)

    # File > Export / Import menus
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    # Add > GTA SA submenu
    bpy.types.VIEW3D_MT_add.remove(_gtasa_add_menu_draw)

    del bpy.types.Object.inu
    del bpy.types.Material.inu
    if hasattr(bpy.types.Object, 'inu_animobj_props'):
        del bpy.types.Object.inu_animobj_props

    bpy.types.MATERIAL_MT_context_menu.remove(_draw_sort_materials_menu)

    # Remove keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Remove COL Light preview handlers
    for h in _col_light_mod._col_light_preview_handlers:
        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
    _col_light_mod._col_light_preview_handlers.clear()
    _col_light_mod._col_light_preview_active = False

    # Remove model links draw handler
    global _links_draw_handler, _links_active
    if _links_draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_links_draw_handler, 'WINDOW')
        _links_draw_handler = None
    _links_active = False

    # Remove UV grid draw handler
    if _uv._uv_grid_draw_handler is not None:
        bpy.types.SpaceImageEditor.draw_handler_remove(_uv._uv_grid_draw_handler, 'WINDOW')
        _uv._uv_grid_draw_handler = None
    _uv._uv_grid_visible = False

    del bpy.types.Scene.gtatools_uv_grid_cols
    del bpy.types.Scene.gtatools_uv_grid_rows
    del bpy.types.Scene.gtatools_uv_grid_align
    del bpy.types.Scene.gtatools_uv_link_islands
    del bpy.types.Scene.gtatools_col_day_min
    del bpy.types.Scene.gtatools_col_day_max
    del bpy.types.Scene.gtatools_col_night_min
    del bpy.types.Scene.gtatools_col_night_max
    del bpy.types.Scene.gtatools_col_light_edge
    del bpy.types.Scene.gtatools_col_light_threshold
    del bpy.types.Scene.gtatools_col_light_contrast
    del bpy.types.Scene.gtatools_col_light_font_size
    del bpy.types.Scene.gtatools_col_light_show_numbers
    del bpy.types.Scene.gtatools_img_path
    del bpy.types.Scene.gtatools_game_root
    del bpy.types.Scene.gtatools_map_region
    del bpy.types.Scene.gtatools_profile_enabled
    del bpy.types.Scene.gtatools_binary_ipls
    try:
        del bpy.types.WindowManager.gtatools_txd_export_plan
        del bpy.types.WindowManager.gtatools_txd_export_plan_index
    except Exception:
        pass
    del bpy.types.Scene.gtatools_show_binary_ipls
    del bpy.types.Scene.gtatools_map_skip_2dfx
    del bpy.types.Scene.gtatools_img_use_gta_dat
    del bpy.types.Scene.gtatools_img_skip_lod
    del bpy.types.Scene.gtatools_img_load_txd
    del bpy.types.Scene.gtatools_map_load_col
    try:
        del bpy.types.Scene.gtatools_map_group_by_ipl
    except Exception:
        pass
    del bpy.types.Scene.gtatools_ide_path
    del bpy.types.Scene.gtatools_ipl_path
    del bpy.types.Scene.gtatools_txd_auto_import
    del bpy.types.Scene.gtatools_shared_txd_name
    del bpy.types.Scene.gtatools_txd_import_path
    del bpy.types.Scene.gtatools_nvtt_path
    del bpy.types.Scene.gtatools_txd_use_gpu
    del bpy.types.Scene.gtatools_show_nvtt_settings
    del bpy.types.Scene.gtatools_show_texture_settings
    del bpy.types.Scene.gtatools_show_paths_settings
    del bpy.types.Scene.gtatools_show_suffix_settings
    del bpy.types.Scene.gtatools_show_dff_flags
    for _p in ('gtatools_2dfx_show_props', 'gtatools_2dfx_show_behavior',
               'gtatools_2dfx_show_shadow', 'gtatools_2dfx_show_flags'):
        if hasattr(bpy.types.Scene, _p):
            delattr(bpy.types.Scene, _p)
    if hasattr(bpy.types.Scene, 'gtatools_anim_tab'):
        del bpy.types.Scene.gtatools_anim_tab
    if hasattr(bpy.types.Scene, 'gtatools_profile'):
        del bpy.types.Scene.gtatools_profile
    if hasattr(bpy.types.Scene, 'gtatools_profile_picked'):
        del bpy.types.Scene.gtatools_profile_picked
    del bpy.types.Scene.gtatools_show_ide_flags
    del bpy.types.Scene.gtatools_suffix_dff
    del bpy.types.Scene.gtatools_suffix_lod
    del bpy.types.Scene.gtatools_suffix_col
    del bpy.types.Scene.gtatools_prefix_dff
    del bpy.types.Scene.gtatools_prefix_lod
    del bpy.types.Scene.gtatools_prefix_col
    del bpy.types.Scene.gtatools_radar_output
    del bpy.types.Scene.gtatools_radar_grid
    del bpy.types.Scene.gtatools_radar_size
    del bpy.types.Scene.gtatools_radar_height
    del bpy.types.Scene.gtatools_radar_gamma
    del bpy.types.Scene.gtatools_radar_specific
    del bpy.types.Scene.gtatools_show_img_list
    del bpy.types.Scene.gtatools_img_entries
    del bpy.types.Scene.gtatools_img_entries_index
    del bpy.types.Scene.gtatools_show_id_manager
    del bpy.types.Scene.gtatools_id_search
    del bpy.types.Scene.gtatools_id_page
    del bpy.types.Scene.gtatools_id_preset
    if hasattr(bpy.types.Scene, 'gtatools_id_show_service'):
        del bpy.types.Scene.gtatools_id_show_service
    del bpy.types.Scene.gtatools_texture_path2
    del bpy.types.Scene.gtatools_texture_path1
    del bpy.types.Scene.gtatools_export_pipeline
    del bpy.types.Scene.gtatools_material_preset
    del bpy.types.Scene.gtatools_export_all_dff
    del bpy.types.Scene.gtatools_export_all_col
    del bpy.types.Scene.gtatools_export_all_lod
    del bpy.types.Scene.gtatools_export_all_txd
    del bpy.types.Scene.gtatools_export_all_col_library
    del bpy.types.Scene.gtatools_export_all_col_library_name
    del bpy.types.Scene.gtatools_export_all_txd_shared
    del bpy.types.Scene.gtatools_export_all_txd_shared_name
    del bpy.types.Scene.gtatools_scatter_radius
    del bpy.types.Scene.gtatools_scatter_iterations
    del bpy.types.Scene.gtatools_scatter_falloff
    del bpy.types.Scene.gtatools_scatter_intensity
    del bpy.types.Scene.gtatools_fill_color
    del bpy.types.Object.gtatools_fill_colors
    # VC Layer System — guarded delete so cleanup never blocks unregister.
    try:
        vc_layers_unregister_handlers()
    except Exception:
        pass
    for _attr in ('gtatools_vc_layers', 'gtatools_vc_active_layer',
                  'gtatools_vc_edit_target', 'gtatools_vc_multi_mode',
                  'gtatools_vc_live_preview',
                  'gtatools_vc_preview_scope',
                  'gtatools_vc_multi_opacity',
                  'gtatools_vc_multi_brightness',
                  'gtatools_vc_multi_contrast'):
        try:
            delattr(bpy.types.Mesh, _attr)
        except (AttributeError, RuntimeError):
            pass
    try:
        delattr(bpy.types.Scene, 'gtatools_vc_layers_expanded')
    except (AttributeError, RuntimeError):
        pass
    del bpy.types.Scene.gtatools_v_offset
    del bpy.types.Scene.gtatools_vc_smooth_iterations
    del bpy.types.Scene.gtatools_vc_smooth_factor
    del bpy.types.Scene.gtatools_vc_contrast
    del bpy.types.Scene.gtatools_vc_brightness
    del bpy.types.Scene.gtatools_vc_gamma
    del bpy.types.Scene.gtatools_bake_shadows
    for _attr in (
        'gtatools_modulate_mode',
        'gtatools_modulate_mix',
        'gtatools_modulate_contrast',
        'gtatools_modulate_gamma',
        # legacy props (предыдущие версии аддона) — снять чтобы не
        # висели «фантомами» в .blend сохранённых старой версией.
        'gtatools_modulate_preview',
        'gtatools_modulate_color',
        'gtatools_modulate_postfx1_color',
        'gtatools_modulate_postfx1_alpha',
        'gtatools_modulate_postfx2_color',
        'gtatools_modulate_postfx2_alpha',
    ):
        try:
            delattr(bpy.types.Scene, _attr)
        except (AttributeError, RuntimeError):
            pass
    del bpy.types.Scene.gtatools_prelight_preset
    del bpy.types.Scene.gtatools_bake_gamma
    del bpy.types.Scene.gtatools_bake_intensity
    del bpy.types.Scene.gtatools_ifp_action
    del bpy.types.Scene.gtatools_ik_display
    del bpy.types.Scene.gtatools_ik_color
    try:
        del bpy.types.Scene.gtatools_floor_offset
    except (AttributeError, RuntimeError):
        pass
    try:
        del bpy.types.Scene.gtatools_ik_extras_show
    except (AttributeError, RuntimeError):
        pass
    for _attr in (
        'gtatools_ik_size',
        'gtatools_ik_show_chain',
        'gtatools_ik_show_pole',
        'gtatools_ik_show_rot',
        'gtatools_ik_show_root',
        'gtatools_ik_chain_offset',
        'gtatools_ik_root_motion',
        'gtatools_anim_tools_show',
        'gtatools_anim_fix_start',
        'gtatools_anim_fix_end',
    ):
        try:
            delattr(bpy.types.Scene, _attr)
        except (AttributeError, RuntimeError):
            pass
    del bpy.types.Scene.gtatools_water_flag
    del bpy.types.Scene.gtatools_water_speed_x
    del bpy.types.Scene.gtatools_water_speed_y
    del bpy.types.Scene.gtatools_water_speed_z
    del bpy.types.Scene.gtatools_water_wave_height
    del bpy.types.Scene.gtatools_bake_ambient
    del bpy.types.Scene.gtatools_vc_analysis
    del bpy.types.Scene.gtatools_lightmap_result
    del bpy.types.Scene.gtatools_lightmap_path
    if hasattr(bpy.types.Scene, 'inu_validate_issues'):
        del bpy.types.Scene.inu_validate_issues
    del bpy.types.Scene.gtatools_model_id

    # Stop particle sim timer and drop meshes
    try:
        from .ops import particle_sim
        particle_sim.stop_simulation()
    except Exception:
        pass
    try:
        del bpy.types.Scene.gtatools_particle_sim
    except Exception:
        pass
    for k in ('gtatools_pfx_exp_texture', 'gtatools_pfx_exp_color',
              'gtatools_pfx_exp_size', 'gtatools_pfx_exp_emission',
              'gtatools_pfx_exp_physics', 'gtatools_pfx_exp_system',
              'gtatools_pfx_exp_curves'):
        try:
            delattr(bpy.types.Scene, k)
        except Exception:
            pass

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    print("[GTA Tools Panel] Addon unregistered!")


if __name__ == "__main__":
    register()
