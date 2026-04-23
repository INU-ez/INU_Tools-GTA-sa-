# English translation for INU_tools
# Keys are Russian strings used in the addon code.
# Values are English translations.

LANG = {
    # bl_info
    "Набор инструментов для работы с GTA SA моделями. Requires DragonFF addon":
        "Toolset for GTA SA models. Requires DragonFF addon",

    # Property descriptions
    "Выделить найденные проблемные элементы": "Select found problem elements",
    "Количество колонок в сетке текстуры": "Number of columns in texture grid",
    "Количество рядов в сетке текстуры": "Number of rows in texture grid",
    "Позиция UV в ячейке": "UV position in cell",
    "Полигоны с пересекающимися UV перемещаются вместе": "Polygons with overlapping UVs move together",
    "Путь к папке NVIDIA Texture Tools (для GPU сжатия)": "Path to NVIDIA Texture Tools folder (for GPU compression)",
    "Использовать GPU (NVTT) для сжатия текстур": "Use GPU (NVTT) for texture compression",
    "Показать настройки NVTT": "Show NVTT settings",
    "Путь к папке с системными текстурами GTA": "Path to GTA system textures folder",
    "Путь к папке где находится .blend файл": "Path to folder where .blend file is located",
    "Не экспортировать TXD при Export All": "Do not export TXD with Export All",
    "Пропустить TXD": "Skip TXD",

    # Enum items
    "Центр": "Center",
    "По центру ячейки": "Center of cell",
    "Сверху слева": "Top Left",
    "В верхнем левом углу": "In top left corner",
    "Сверху": "Top",
    "Сверху по центру": "Top center",
    "Сверху справа": "Top Right",
    "В верхнем правом углу": "In top right corner",
    "Слева": "Left",
    "Слева по центру": "Left center",
    "Справа": "Right",
    "Справа по центру": "Right center",
    "Снизу слева": "Bottom Left",
    "В нижнем левом углу": "In bottom left corner",
    "Снизу": "Bottom",
    "Снизу по центру": "Bottom center",
    "Снизу справа": "Bottom Right",
    "В нижнем правом углу": "In bottom right corner",

    # UI text
    "Статус: Готов": "Status: Ready",
    "Статус: Не найден": "Status: Not found",
    "Папка .blend:": ".blend Folder:",
    "Загрузить текстуры": "Load Textures",
    "Очистка материалов": "Cleanup Materials",
    "Проверить материалы": "Check Materials",
    "Очистить всё": "Clear All",
    "Отменить": "Undo",
    "Колонки": "Columns",
    "Ряды": "Rows",
    "Скрыть сетку": "Hide Grid",
    "Показать сетку": "Show Grid",
    "Позиция": "Position",
    "Связать полигоны": "Link Polygons",
    "Рандом": "Random",
    "Привязать": "Snap",

    # Report messages
    "Выберите меш объект!": "Select a mesh object!",
    "Не меш объект": "Not a mesh object",
    "Геометрия в порядке!": "Geometry is OK!",
    "висящих вершин": "loose vertex",
    "висящих рёбер": "loose edges",
    "N-gons не найдены!": "No N-gons found!",
    "N-gons (5+ вершин)": "N-gons (5+ vertex)",
    "Нечего удалять - геометрия чистая!": "Nothing to delete - geometry is clean!",
    "Удалено:": "Deleted:",
    "вершин,": "vertex,",
    "рёбер": "edges",
    "Выделите модели для экспорта!": "Select models for export!",
    "Не удалось определить имя модели!": "Could not determine model name!",
    "Экспортировано:": "Exported:",
    "Ошибки:": "Errors:",
    "Найдено:": "Found:",
    "Среди выделенных не найдено DFF/LOD/COL моделей": "No DFF/LOD/COL models found among selected",
    "Укажите хотя бы один путь к папке с текстурами!": "Specify at least one path to textures folder!",
    "Выберите материал в списке!": "Select a material in the list!",
    "Выберите корректный материал!": "Select a valid material!",
    "Не удалось загрузить": "Failed to load",
    "Загружена текстура:": "Texture loaded:",
    "Текстура уже подключена:": "Texture already connected:",
    "Текстура не найдена:": "Texture not found:",
    "Путь установлен": "Path set",
    "Сначала сохраните .blend файл!": "Save .blend file first!",
    "Файл не указан!": "File not specified!",
    "Неподдерживаемый формат:": "Unsupported format:",
    "Ошибка загрузки:": "Loading error:",
    "Создан материал:": "Material created:",
    "Выделите меш объекты!": "Select mesh objects!",
    "Объектов:": "Objects:",
    "всего материалов:": "total materials:",
    "превышен лимит:": "limit exceeded:",
    "Объединено:": "Merged:",
    "слотов, удалено:": "slots, removed:",
    "дубликатов": "duplicates",
    "Дубликаты материалов не найдены": "No duplicate materials found",
    "Сортировка материалов": "Sort Materials",
    "Материалы уже отсортированы": "Materials already sorted",
    "Отсортировано материалов:": "Materials sorted:",
    "Сохраните .blend файл сначала!": "Save .blend file first!",
    "Текстуры с приставкой LP_ не найдены в папке:": "Textures with LP_ prefix not found in folder:",
    "Не удалось применить лайтмап - нет подходящих материалов": "Could not apply lightmap - no suitable materials",
    "Настройки сброшены по умолчанию": "Settings reset to default",
    "Код очищен": "Code cleared",
    "Сетка UV включена": "UV grid enabled",
    "Сетка UV выключена": "UV grid disabled",
    "Укажите количество колонок и рядов!": "Specify number of columns and rows!",
    "Выделите полигоны!": "Select polygons!",
    "Рандомизировано:": "Randomized:",
    "групп": "groups",
    "полигонов": "polygons",
    "Привязано:": "Snapped:",
    "Выберите меш!": "Select a mesh!",
    "Нет vertex colors!": "No vertex colors!",
    "Выделено": "Selected",
    "меш(ей)": "mesh(es)",

    # Operator docstrings
    "Проверить геометрию на висящие вершины и рёбра": "Check geometry for loose vertex and edges",
    "Проверить геометрию на N-gons (полигоны с 5+ вершинами)": "Check geometry for N-gons (polygons with 5+ vertex)",
    "Удалить висящие вершины и рёбра": "Delete loose vertex and edges",
    "Экспортировать текстуры в TXD архив": "Export textures to TXD archive",
    "Экспортировать DFF модель": "Export DFF model",
    "Экспортировать COL модель коллизии": "Export COL collision model",
    "Экспорт всех выделенных моделей (DFF + COL + LOD + TXD)": "Export all selected models (DFF + COL + LOD + TXD)",
    "Определить модели DFF, LOD, COL среди выделенных": "Detect DFF, LOD, COL models among selected",
    "Применить GTA SA Prelight к выделенному объекту": "Apply GTA SA Prelight to selected object",
    "Усреднить vertex colors для компланарных граней": "Average vertex colors for coplanar faces",
    "Сгенерировать код lightmap для выделенного объекта": "Generate lightmap code for selected object",
    "Копировать результат в буфер обмена": "Copy result to clipboard",
    "Очистить сгенерированный код": "Clear generated code",
    "Создать 8 источников света для запекания prelight вокруг объекта": "Create 8 lights for prelight baking around object",
    "Удалить все источники света prelight": "Remove all prelight lights",
    "Запечь освещение от Point источников в vertex colors": "Bake lighting from Point sources to vertex colors",
    "Быстрое запекание vertex colors от Point источников (без теней)": "Quick bake vertex colors from Point sources (no shadows)",
    "Сбросить настройки запекания по умолчанию": "Reset bake settings to default",
    "Сбросить настройки Scatter Light по умолчанию": "Reset Scatter Light settings to default",
    "Анализировать vertex colors выделенного объекта": "Analyze vertex colors of selected object",
    "Применить смещение яркости (V) к vertex colors": "Apply brightness offset (V) to vertex colors",
    "Загрузить Lightmap из папки с .blend файлом (текстуры с приставкой LP_)": "Load Lightmap from .blend folder (textures with LP_ prefix)",
    "Удалить Lightmap из материалов объекта": "Remove Lightmap from object materials",
    "Создать Day и Night color attributes": "Create Day and Night color attributes",
    "Переключить превью prelight - показать vertex colors с текстурами": "Toggle prelight preview - show vertex colors with textures",
    "Кликните на полигон чтобы взять его цвет": "Click on polygon to pick its color",
    "Залить выделенные грани цветом": "Fill selected faces with color",
    "Восстановить цвета, изменённые заливкой": "Restore colors changed by fill",
    "Удалить цвет из списка и восстановить оригинальные цвета": "Delete color from list and restore original colors",
    "Выделить полигоны с этим цветом": "Select polygons with this color",
    "Удалить scatter уровень (пересчитать цвета)": "Delete scatter level (recalculate colors)",
    "Очистить все scatter уровни цвета": "Clear all scatter levels of color",
    "Рассеять свет от выделенных граней к соседним": "Scatter light from selected faces to neighbors",
    "Переключить режим выделения граней в Vertex Paint": "Toggle face selection mode in Vertex Paint",
    "Переключить в Edit Mode для выделения граней": "Switch to Edit Mode for face selection",
    "Переключить в Vertex Paint Mode": "Switch to Vertex Paint Mode",
    "Выбрать color attribute и обновить превью prelight": "Select color attribute and update prelight preview",
    "Добавить новый color attribute": "Add new color attribute",
    "Удалить активный color attribute": "Delete active color attribute",
    "Создать color attribute": "Create color attribute",
    "Удалить color attribute по имени": "Delete color attribute by name",
    "Загрузить текстуры по именам материалов из указанных папок": "Load textures by material names from specified folders",
    "Установить путь к папке .blend файла": "Set path to .blend file folder",
    "Создать материал из перетаскиваемой текстуры": "Create material from dropped texture",
    "Проверить количество материалов на выделенных объектах": "Check material count on selected objects",
    "Объединить дубликаты материалов (.001, .002, и т.д.) с оригиналами": "Merge duplicate materials (.001, .002, etc.) with originals",
    "Показать/скрыть сетку на UV": "Show/hide grid on UV",
    "Рандомно распределить UV выделенных полигонов по сетке (для окон, вариаций)": "Randomly distribute UV of selected polygons on grid (for windows, variations)",
    "Привязать UV выделенных полигонов к ближайшей ячейке сетки": "Snap UV of selected polygons to nearest grid cell",

    # Panel docstrings
    "Главная панель GTA Tools": "GTA Tools main panel",
    "Панель экспорта GTA моделей": "GTA models export panel",
    "Панель INU Tools в Properties > Scene": "INU Tools panel in Properties > Scene",
    "Панель Prelight": "Prelight panel",
    "Расширенные настройки запекания": "Advanced bake settings",
    "Панель инструментов Vertex Paint": "Vertex Paint tools panel",
    "Панель генератора Lightmap": "Lightmap generator panel",
    "Панель UV инструментов GTA Tools": "GTA Tools UV panel",

    # Internal docstrings
    "Проверить доступность NVIDIA Texture Tools": "Check NVIDIA Texture Tools availability",
    "Папка NVTT не найдена": "NVTT folder not found",
    "Сжать текстуру через NVIDIA Texture Tools (GPU)": "Compress texture via NVIDIA Texture Tools (GPU)",
    "Проверить, подключена ли нода к чему-либо (любой выход)": "Check if node is connected to anything (any output)",
    "Определить тип модели по суффиксу: LOD, COL, DFF в конце названия": "Determine model type by suffix: LOD, COL, DFF at end of name",
    "Найти связанные модели (DFF, LOD, COL) по базовому имени": "Find related models (DFF, LOD, COL) by base name",
    "Найти модели DFF, LOD, COL только среди выделенных объектов": "Find DFF, LOD, COL models only among selected objects",
    "Получить базовое имя из выделенных моделей": "Get base name from selected models",
    "Сохранить базовые цвета если ещё не сохранены": "Save base colors if not saved yet",
    "Пересчитать цвет одного loop: ИТОГ = (База ИЛИ Fill) + Σ Scatter": "Recalculate color of one loop: RESULT = (Base OR Fill) + Σ Scatter",
    "Пересчитать цвета для указанных loops (или всех если не указано)": "Recalculate colors for specified loops (or all if not specified)",
    "Добавить Fill слой для указанных loops": "Add Fill layer for specified loops",
    "Получить список уровней scatter для цвета": "Get list of scatter levels for color",
    "Удалить Scatter слой и пересчитать цвета": "Delete Scatter layer and recalculate colors",
    "Удалить все Scatter слои для цвета и пересчитать": "Delete all Scatter layers for color and recalculate",
    "Удалить Fill цвет и все его Scatter слои, пересчитать": "Delete Fill color and all its Scatter layers, recalculate",
    "Удалить цвет из списка по индексу": "Delete color from list by index",
    "Получить Fill цвет выделенных полигонов": "Get Fill color of selected polygons",
    "Проверить объект на висящие вершины и рёбра (не присоединённые к полигонам)": "Check object for loose vertex and edges (not attached to polygons)",
    "Элемент списка цветов заливки": "Fill color list item",

    # Material Backup
    "Исправить коллекцию освещения Itera Tools — сделать локальной и привязать к сцене": "Fix Itera Tools light collection — make local and link to scene",
    "Коллекция 'Template Scene - Vertex Lights' не найдена": "Collection 'Template Scene - Vertex Lights' not found",
    "Не удалось сделать коллекцию локальной": "Failed to make collection local",
    "Коллекция освещения Itera привязана к сцене": "Itera light collection linked to scene",
    "Исправить коллекцию Itera": "Fix Itera Collection",
    "Коллекция Itera исправлена": "Itera Collection Fixed",
    "Сохранить материалы объекта в буфер": "Save object materials to buffer",
    "Восстановить сохранённые материалы на объект": "Restore saved materials to object",
    "Материалы сохранены": "Materials saved",
    "Материалы восстановлены": "Materials restored",
    "Нет сохранённых материалов!": "No saved materials!",
    "Материал не найден:": "Material not found:",

    # Post-processing
    "Пост-обработка vertex colors": "Post-process vertex colors",
    "Сгладить vertex colors между соседними вершинами": "Smooth vertex colors between neighboring vertex",
    "Применить контраст к vertex colors": "Apply contrast to vertex colors",
    "Применить яркость к vertex colors": "Apply brightness to vertex colors",
    "Применить гамма-коррекцию к vertex colors": "Apply gamma correction to vertex colors",
    "Количество итераций сглаживания": "Number of smoothing iterations",
    "Сила сглаживания (0 = без изменений, 1 = полное усреднение)": "Smoothing factor (0 = no change, 1 = full average)",
    "Контраст (1 = без изменений, <1 = меньше, >1 = больше)": "Contrast (1 = no change, <1 = less, >1 = more)",
    "Яркость смещение (-1..+1)": "Brightness offset (-1..+1)",
    "Гамма-коррекция (1 = без изменений, <1 = светлее, >1 = темнее)": "Gamma correction (1 = no change, <1 = lighter, >1 = darker)",
    "Панель пост-обработки vertex colors": "Vertex colors post-processing panel",

    # COL Surface
    "Выберите COL меш-объект": "Select a COL mesh object",
    "Нет материалов на объекте": "No materials on object",
    "Тип поверхности GTA SA для коллизии": "GTA SA surface type for collision",
    "Назначить surface ID на выбранный материал": "Assign surface ID to selected material",
    "Surface ID назначен:": "Surface ID assigned:",
    "COL Surface Materials:": "COL Surface Materials:",
    "введите запрос для фильтрации": "type to filter",

    # Info tooltips
    "Текстура короны (светящийся спрайт)": "Corona texture (glowing sprite)",
    "Текстура тени на земле под источником света": "Shadow texture on ground under light source",

    "None — без pipeline\nVehicle — машины (отражения кузова, env map)\nBuilding DN — здания с day/night vertex colors\nBuilding — обычные здания":
        "None — no pipeline\nVehicle — cars (body reflections, env map)\nBuilding DN — buildings with day/night vertex colors\nBuilding — plain buildings",

    "DFF — модель (меш, материалы, UV)\nCOL — коллизия\nTXD — текстуры\nCheck vertex — висящие вершины и рёбра\nCheck N-gon — полигоны с 5+ вершинами\nCheck Material — лимит 50 материалов\nGPU (NVTT) — сжатие текстур на видеокарте":
        "DFF — model (mesh, materials, UV)\nCOL — collision\nTXD — textures\nCheck vertex — loose vertex and edges\nCheck N-gon — polygons with 5+ vertex\nCheck Material — 50 material limit\nGPU (NVTT) — texture compression on GPU",

    "DFF — импорт модели с мешем и материалами\nCOL — импорт коллизии\nTXD — импорт текстур\nImport TXD — автоимпорт текстур при импорте DFF":
        "DFF — import model with mesh and materials\nCOL — import collision\nTXD — import textures\nImport TXD — auto-import textures when importing DFF",

    "Light — уличные фонари, неон, corona\nParticle — дым, огонь, частицы\nPed Attractor — точки притяжения NPC (банкомат, скамейка)\nSun Glare — блик солнца на поверхности":
        "Light — street lights, neon, corona\nParticle — smoke, fire, particles\nPed Attractor — NPC attraction points (ATM, bench)\nSun Glare — sun glare on surface",

    "Color — цвет короны и света\nCorona Size — размер короны\nDraw Distance — дальность отрисовки\nLight Range — радиус точечного света":
        "Color — corona and light color\nCorona Size — corona size\nDraw Distance — draw distance\nLight Range — point light radius",

    "DEFAULT — всегда видим\nRANDOM_FLASHING — случайное мерцание\nFLASH_RAIN — мерцает в дождь\nONLY_RAIN — видим только в дождь\nNO_RAIN — не видим в дождь\nFLASH_5 — вариант мерцания 2":
        "DEFAULT — always visible\nRANDOM_FLASHING — random flashing\nFLASH_RAIN — flashes in rain\nONLY_RAIN — visible only in rain\nNO_RAIN — not visible in rain\nFLASH_5 — flashing variant 2",

    "None — без бликов линзы\nType 1/2/3 — разные стили бликов линзы":
        "None — no lens flare\nType 1/2/3 — different lens flare styles",

    "Light — динамическое освещение модели\nModulate Material Color — цвет материала влияет на модель\nExport Normals — экспорт нормалей (отключить для map объектов)":
        "Light — dynamic lighting on model\nModulate Material Color — material color affects model\nExport Normals — export normals (disable for map objects)",

    "Day — дневные вертексные цвета (prelight)\nNight — ночные вертексные цвета (требует Pipeline: Building)":
        "Day — daytime vertex colors (prelight)\nNight — nighttime vertex colors (requires Pipeline: Building)",

    "UV Map 1 — основная UV развёртка\nUV Map 2 — вторая UV (для lightmap и т.д.)\nBin Mesh PLG — совместимость с просмотрщиками DFF":
        "UV Map 1 — primary UV map\nUV Map 2 — secondary UV (for lightmap etc.)\nBin Mesh PLG — compatibility with DFF viewers",

    "Day — дневные вертексные цвета\nNight — ночные вертексные цвета\nDay/Night — создать оба атрибута\n+/- — добавить или удалить атрибут\nSave Materials — сохранить материалы (для Itera Tools)\nRestore — восстановить сохранённые материалы":
        "Day — daytime vertex colors\nNight — nighttime vertex colors\nDay/Night — create both attributes\n+/- — add or remove attribute\nSave Materials — save materials (for Itera Tools)\nRestore — restore saved materials",

    "V — смещение яркости vertex colors\nПоложительное значение — светлее\nОтрицательное — темнее":
        "V — brightness offset for vertex colors\nPositive value — brighter\nNegative — darker",

    "Сглаживание vertex colors между соседними вершинами\nIterations — количество проходов\nFactor — сила сглаживания (0-1)":
        "Smooth vertex colors between neighboring vertex\nIterations — number of passes\nFactor — smoothing strength (0-1)",

    "Контраст vertex colors\n1.0 — без изменений\n< 1.0 — меньше контраст\n> 1.0 — больше контраст":
        "Vertex colors contrast\n1.0 — no change\n< 1.0 — less contrast\n> 1.0 — more contrast",

    "Яркость vertex colors\n0.0 — без изменений\n> 0 — светлее\n< 0 — темнее":
        "Vertex colors brightness\n0.0 — no change\n> 0 — brighter\n< 0 — darker",

    "Гамма-коррекция vertex colors\n1.0 — без изменений\n< 1.0 — светлее (тени)\n> 1.0 — темнее (тени)":
        "Vertex colors gamma correction\n1.0 — no change\n< 1.0 — lighter (shadows)\n> 1.0 — darker (shadows)",

    "Диапазон дневного освещения для COL материалов\nMin/Max — значения от 0 до 15\nЯркость vertex colors конвертируется в этот диапазон":
        "Day lighting range for COL materials\nMin/Max — values from 0 to 15\nVertex colors brightness is converted to this range",

    "Диапазон ночного освещения для COL материалов\nMin/Max — значения от 0 до 15\nИспользует Night color attribute если есть":
        "Night lighting range for COL materials\nMin/Max — values from 0 to 15\nUses Night color attribute if available",

    "Тени — включить расчёт теней при запекании\nЗапечь — быстрое запекание без теней\nС тенями — запекание с raycast тенями (медленнее, но точнее)":
        "Shadows — enable shadow calculation when baking\nBake — fast baking without shadows\nWith Shadows — baking with raycast shadows (slower but more accurate)",

    # Buttons
    "Запекание:": "Bake:",
    "Тени": "Shadows",
    "Запечь": "Bake",
    "С тенями": "With Shadows",
    "Экспорт всего (DFF+COL+LOD+TXD)": "Export All (DFF+COL+LOD+TXD)",
    "Проверка": "Check",
    "Проверка вершин": "Check Vertex",
    "Проверка N-gon": "Check N-gon",
    "Проверка материалов": "Check Materials",
    "Привязать к модели": "Attach to Model",
    "Выделите меш + 2DFX, затем нажмите": "Select mesh + 2DFX, then click",
    "Обновить превью": "Refresh Preview",
    "Удалить превью": "Remove Preview",
    "Применить": "Apply",
    "Создать 8 ламп": "Create 8 Lights",
    "Удалить": "Remove",
    "Сохранить материалы": "Save Materials",
    "Восстановить": "Restore",
    "Запечь COL Light": "Bake COL Light",
    "Сгладить": "Smooth",
    "Сглаживание:": "Smooth:",
    "Контраст:": "Contrast:",
    "Контраст": "Contrast",
    "Яркость:": "Brightness:",
    "Яркость": "Brightness",
    "Гамма:": "Gamma:",
    "Гамма": "Gamma",
    "Проходы": "Iterations",
    "Сила": "Factor",
    "Мин.": "Min",
    "Макс.": "Max",

    # 2DFX panel
    "Пресеты:": "Presets:",
    "Свойства света:": "Light Properties:",
    "Имя короны:": "Corona Name:",
    "Режим показа:": "Show Mode:",
    "Тип бликов:": "Flare Type:",
    "Имя тени:": "Shadow Name:",
    "Флаги 1": "Flags 1",
    "Флаги 2": "Flags 2",
    "Солнечный блик": "Sun Glare",
    "Только позиция (без доп. данных)": "Position only (no extra data)",
    "Модель:": "Model:",
    "Цвет:": "Color:",
    "Размер короны": "Corona Size",
    "Дальность отрисовки": "Draw Distance",
    "Радиус света": "Light Range",
    "Отражение короны": "Corona Reflection",
    "Размер тени": "Shadow Size",
    "Дистанция тени": "Shadow Distance",
    "Множитель тени": "Shadow Multiplier",
    "Вектор направления:": "Look Direction:",
    "Свойства частицы:": "Particle Properties:",
    "Имя эффекта": "Effect Name",
    "Точка притяжения:": "Ped Attractor:",
    "Тип аттрактора": "Attractor Type",
    "Матрица поворота": "Rotation Matrix",
    "Внешний скрипт": "External Script",
    "Вероятность NPC": "Ped Probability",

    # Prelight panel
    "Цветовые атрибуты:": "Color Attributes:",
    "Настройка цвета:": "Adjust Color:",
    "Сохранено:": "Saved:",
    "мат.": "mat(s)",
    "Окружающий": "Ambient",
    "Интенсивность": "Intensity",

    # Prelight COL panel
    "Дневной свет:": "Day Light:",
    "Ночной свет:": "Night Light:",
    "Нет vertex colors": "No vertex colors",
    "COL light материалов:": "COL light materials:",
    "Дневной свет": "Day Light",
    "Ночной свет": "Night Light",

    # Scatter Light
    "Рассеянный свет:": "Scatter Light:",
    "Затухание": "Falloff",
    "Итерации": "Iterations",
    "Радиус (0=авто)": "Radius (0=auto)",
    "Рассеять от выделенных": "Scatter from Selected",

    # Lightmap panel
    "Текстура Lightmap:": "Lightmap Texture:",
    "Загрузить (LP_)": "Load (LP_)",
    "Генерация кода:": "Generate Code:",
    "Генерировать": "Generate",
    "Путь": "Path",
    "ID модели": "Model ID",
    "Результат:": "Result:",
    "Копировать": "Copy",
    "Очистить": "Clear",
    "Нажмите кнопку для генерации": "Press button to generate",

    # UV panel
    "Рандомизатор UV сетки": "UV Grid Randomizer",

    # Scene panel
    "Системные текстуры:": "System Textures:",
    "Настройки NVTT": "NVTT Settings",

    # Material Effects panel
    "Фоновое затенение": "Ambient Shading",
    "Карта окружения": "Environment Map",
    "Текстура": "Texture",
    "Коэффициент": "Coefficient",
    "Использовать FB Alpha": "Use FB Alpha",
    "Карта высот": "Bump Map",
    "Текстура карты высот": "Height Map Texture",
    "Отражение материала": "Reflection Material",
    "Масштаб X": "Scale X",
    "Смещение X": "Offset X",
    "Зеркальный материал": "Specular Material",
    "Уровень зеркальности": "Specular Level",
    "UV Анимация": "UV Animation",
    "Имя анимации": "Animation Name",

    # Object Props panel
    "Флаги геометрии:": "Geometry Flags:",
    "Вертексные цвета:": "Vertex Colors:",
    "UV карты:": "UV Maps:",
    "Тип": "Type",
    "Свет (rpGEOMETRYLIGHT)": "Light (rpGEOMETRYLIGHT)",
    "Цвет материала модулирует": "Modulate Material Color",
    "Экспорт нормалей": "Export Normals",
    "Дневные верт. цвета": "Day Vertex Colours",
    "Ночные верт. цвета": "Night Vertex Colours",
    "UV карта 1": "UV Map 1",
    "UV карта 2": "UV Map 2",
    "Bin Mesh PLG": "Bin Mesh PLG",

    # Export/Import section headers
    "Экспорт по одному:": "Export Individual:",
    "Импорт по одному:": "Import Individual:",
    "Импорт TXD": "Import TXD",

    # Vertex Paint panel (hidden)
    "Режим:": "Mode:",
    "Редактор": "Edit",
    "Рисование": "Paint",
    "Выделение граней": "Face Select",
    "Заливка граней:": "Fill Faces:",
    "Залить": "Fill",

    # Import/Export File operators
    "Импорт DFF модели GTA SA": "Import GTA SA DFF model",
    "Импорт COL коллизии GTA SA": "Import GTA SA COL collision model",
    "Импорт TXD текстур GTA SA": "Import GTA SA TXD texture dictionary",
    "Экспорт DFF модели GTA SA": "Export GTA SA DFF model",
    "Экспорт COL коллизии GTA SA": "Export GTA SA COL collision model",
    "Экспорт TXD текстур GTA SA": "Export GTA SA TXD texture archive",

    # 2DFX operators
    "Применить пресет 2DFX к активному объекту": "Apply 2DFX preset to active object",
    "Создать 2DFX эффект с настройками по умолчанию": "Create 2DFX effect with default properties",
    "Обновить визуальный превью (свет + корона + тень) для выбранного 2DFX": "Recreate visual preview (light + corona + shadow) for selected 2DFX",
    "Удалить визуальный превью из выбранного 2DFX": "Remove visual preview from selected 2DFX",
    "Привязать 2DFX к модели (сделать дочерним)": "Attach 2DFX to mesh model (make it a child)",
    "Отвязать 2DFX от родительской модели": "Detach 2DFX from parent model",

    # COL operators
    "Назначить тип поверхности GTA SA для COL коллизии": "Assign GTA SA surface type for COL collision",
    "Выбрать тип поверхности для COL материала": "Pick surface type for COL material",
    "Конвертировать vertex colors в COL Day/Night Light (разбиение материалов по яркости)": "Convert vertex colors to COL Day/Night Light (split materials by brightness)",
    "Удалить COL light материалы, созданные Bake COL Light": "Remove COL light materials created by Bake COL Light",
    "Конвертировать vertex colors в COL Day/Night Light": "Convert vertex colors to COL Day/Night Light",

    # Panel docstrings
    "Выбор типа поверхности COL в свойствах материала": "COL Surface Type selector in Material Properties",
    "Панель эффектов материала в свойствах материала": "Material Effects panel in Material Properties",
    "Панель свойств объекта GTA SA": "GTA SA Object Properties panel",
    "Залить выделенные грани цветом в режиме vertex paint": "Fill selected faces with color in vertex paint mode",
    "Залить выделенные грани цветом через систему слоёв": "Fill selected faces with color using layer system",
    "Восстановить все цвета к базовым (удалить fill и scatter слои)": "Restore all colors to base (remove fill and scatter layers)",

    # Property descriptions (tooltips on sliders/checkboxes)
    "Цвет короны и света": "Corona and light color",
    "Рендер-пайплайн движка": "Rendering pipeline for the engine",
    "Экспорт нормалей вершин (отключить для map объектов)": "Export vertex normals (disable for map objects)",
    "Экспорт Bin Mesh PLG (совместимость с просмотрщиками DFF)": "Export Bin Mesh PLG (increases compatibility with DFF viewers)",
    "Экспорт первой UV карты": "Export first UV map",
    "Экспорт второй UV карты": "Export second UV map",
    "Экспорт дневных vertex colors": "Export day vertex prelight colors",
    "Экспорт ночных vertex colors": "Export night vertex colors",
    "Материал для Sphere/Cone": "Material for Sphere/Cone",
    "Флаги для Sphere/Cone": "Flags for Sphere/Cone",
    "Яркость для Sphere/Cone": "Brightness for Sphere/Cone",
    "Свет для Sphere/Cone": "Light for Sphere/Cone",
    "ID типа поверхности COL (0-178)": "COL surface type ID (0-178)",
    "Выделить найденные проблемные элементы": "Select found problem elements",
    "Экспортировать текстуры только из выделенных объектов": "Export textures only from selected objects",
    "Расстояние ламп от центра": "Distance of lights from center",
    "Рассчитать тени (медленнее, но точнее)": "Calculate shadows (slower but more accurate)",
    "Включить или выключить превью prelight": "Enable or disable prelight preview",
    "Фильтр типов поверхности": "Filter surface types",
    "Базовый рассеянный свет (ниже = темнее тени)": "Base ambient light (lower = darker shadows)",
    "Множитель интенсивности света (ниже = темнее)": "Light intensity multiplier (lower = darker)",
    "Гамма-коррекция (ниже = темнее)": "Gamma correction (lower = darker)",
    "Включить тени при запекании (raycast проверка перекрытий)": "Enable shadow casting during bake (rays check for occlusion)",
    "Смещение яркости как в 3Ds Max Adjust Color V (-80 для ночи)": "Brightness offset like 3Ds Max Adjust Color V (-80 for night)",
    "Интенсивность рассеивания света": "Light scatter intensity",
    "Скорость затухания света (выше = быстрее)": "How quickly light fades (higher = faster falloff)",
    "Количество слоёв соседних граней": "How many neighbor layers to affect",
    "Радиус поиска соседних граней (0 = авто по размеру грани)": "Search radius for nearby faces (0 = auto based on face size)",
    "Рендер-пайплайн для экспорта DFF": "Rendering pipeline for DFF export",
    "Экспортировать DFF при Export All": "Export DFF with Export All",
    "Экспортировать COL при Export All": "Export COL with Export All",
    "Экспортировать LOD при Export All": "Export LOD with Export All",
    "Экспортировать TXD при Export All": "Export TXD with Export All",
    "Минимальное значение дневного света (тень)": "Minimum Day Light value (shadow)",
    "Максимальное значение дневного света (свет)": "Maximum Day Light value (lit)",
    "Минимальное значение ночного света (тень)": "Minimum Night Light value (shadow)",
    "Максимальное значение ночного света (свет)": "Maximum Night Light value (lit)",
    "Автоимпорт TXD текстур при импорте DFF": "Auto-import TXD texture dictionary when importing DFF",
    "Папка для поиска TXD при импорте DFF (пусто = автопоиск в папке DFF)": "Custom folder to search for TXD files during DFF import (leave empty for auto-search in DFF folder)",
    "Количество колонок в сетке текстуры": "Number of columns in texture grid",
    "Количество рядов в сетке текстуры": "Number of rows in texture grid",
    "Позиция UV в ячейке": "UV position in cell",
    "Полигоны с пересекающимися UV перемещаются вместе": "Polygons with overlapping UVs move together",
    "Путь к папке NVIDIA Texture Tools (для GPU сжатия)": "Path to NVIDIA Texture Tools folder (for GPU compression)",
    "Использовать GPU (NVTT) для сжатия текстур": "Use GPU (NVTT) for texture compression",
    "Показать настройки NVTT": "Show NVTT settings",
    "Путь к папке с системными текстурами GTA": "Path to GTA system textures folder",
    "Путь к папке где находится .blend файл": "Path to folder where .blend file is located",
    "Флаг rpGEOMETRYLIGHT — динамическое освещение": "rpGEOMETRYLIGHT flag — dynamic lighting",
    "Флаг rpGEOMETRYMODULATEMATERIALCOLOR — цвет материала влияет на модель": "rpGEOMETRYMODULATEMATERIALCOLOR flag — material color affects model",

    # IDE / IPL
    "ID модели в GTA SA (IDE/IPL)": "Model ID in GTA SA (IDE/IPL)",
    "Имя словаря текстур (IDE). По умолчанию = имя модели": "Texture dictionary name (IDE). Default = model name",
    "Дальность прорисовки объекта (IDE)": "Object draw distance (IDE)",
    "Флаги объекта в IDE": "Object flags in IDE",
    "ID интерьера для IPL (0 = экстерьер)": "Interior ID for IPL (0 = exterior)",
    "Индекс LOD модели в IPL (-1 = нет LOD)": "LOD model index in IPL (-1 = no LOD)",
    "Экспорт IDE (определение объектов GTA SA)": "Export IDE (GTA SA object definitions)",
    "Экспорт IPL (размещение объектов GTA SA)": "Export IPL (GTA SA object placements)",
    "Импорт IDE (определения объектов GTA SA)": "Import IDE (GTA SA object definitions)",
    "Импорт IPL (размещение объектов GTA SA)": "Import IPL (GTA SA object placements)",
    "Экспорт IDE определений GTA SA": "Export GTA SA IDE definitions",
    "Экспорт IPL размещения GTA SA": "Export GTA SA IPL placements",
    "Импорт IDE определений GTA SA": "Import GTA SA IDE definitions",
    "Импорт IPL размещения GTA SA": "Import GTA SA IPL placements",
    "Model ID — ID модели в GTA SA\nTXD Name — словарь текстур\nDraw Distance — дальность прорисовки\nIDE Flags — флаги объекта\nInterior — ID интерьера (0 = улица)\nLOD Index — индекс LOD модели (-1 = нет)":
        "Model ID — model ID in GTA SA\nTXD Name — texture dictionary\nDraw Distance — rendering distance\nIDE Flags — object flags\nInterior — interior ID (0 = outdoor)\nLOD Index — LOD model index (-1 = none)",
    "DFF — импорт модели с мешем и материалами\nCOL — импорт коллизии\nTXD — импорт текстур\nIDE — определения объектов\nIPL — размещение объектов\nImport TXD — автоимпорт текстур при импорте DFF":
        "DFF — import model with mesh and materials\nCOL — import collision\nTXD — import textures\nIDE — object definitions\nIPL — object placements\nImport TXD — auto-import textures with DFF import",

    # IMG archive
    "Путь к .img архиву GTA SA для экспорта моделей": "Path to GTA SA .img archive for model export",
    "Экспорт DFF в IMG": "Export DFF to IMG",
    "Экспорт COL в IMG": "Export COL to IMG",
    "Экспорт TXD в IMG": "Export TXD to IMG",
    "Экспортировать DFF + TXD + COL прямо в .img архив": "Export DFF + TXD + COL directly into .img archive",
    "Укажите путь к .img архиву": "Specify path to .img archive",
    "Экспорт в IMG": "Export to IMG",

    # Game root / gta.dat
    "Корневая папка GTA SA для автопоиска IDE/IPL/IMG": "GTA SA root folder for auto-discovering IDE/IPL/IMG",
    "Укажите корневую папку GTA SA": "Specify GTA SA root folder",
    "Не найден data/gta.dat в указанной папке": "data/gta.dat not found in the specified folder",
    "Искать все IDE/IPL через gta.dat (нужна корневая папка игры)": "Find all IDE/IPL via gta.dat (requires game root folder)",

    # IDE / IPL panel
    "Панель IDE / IPL для работы с существующими файлами GTA SA": "IDE / IPL panel for working with existing GTA SA files",
    "Путь к IDE файлу GTA SA для добавления/обновления записей": "Path to GTA SA IDE file for adding/updating entries",
    "Путь к IPL файлу GTA SA для добавления/обновления записей": "Path to GTA SA IPL file for adding/updating entries",
    "Добавить / обновить запись в существующем IDE файле": "Add / update entry in existing IDE file",
    "Добавить / обновить запись в существующем IPL файле": "Add / update entry in existing IPL file",
    "Удалить запись из IDE файла по Model ID": "Remove entry from IDE file by Model ID",
    "Удалить запись из IPL файла по Model ID": "Remove entry from IPL file by Model ID",
    "Укажите путь к IDE файлу": "Specify path to IDE file",
    "Укажите путь к IPL файлу": "Specify path to IPL file",
    "Выделите меш объекты": "Select mesh objects",
    "Выделите меш объект": "Select a mesh object",
    "объектов с Model ID = 0, задайте ID в свойствах": "objects with Model ID = 0, set ID in properties",
    "обновлено": "updated",
    "добавлено": "added",
    "удалено": "removed",
    "Нет объектов с Model ID > 0": "No objects with Model ID > 0",
    "Добавить": "Add",
    "Удалить": "Remove",
    "Импорт": "Import",
    "Экспорт": "Export",

    # v1.5.2 — IDE/IPL/IMG, ID Manager, Suffixes, COL Light, Presets
    "IDE / IPL / IMG": "IDE / IPL / IMG",
    "Текстуры": "Textures",
    "Суффиксы моделей": "Model Suffixes",
    "Менеджер ID": "ID Manager",
    "Свободных:": "Free:",
    "Занятых:": "Used:",
    "Следующий свободный:": "Next free:",
    "Свободные:": "Free:",
    "Назначить ID выделенным": "Assign IDs to selected",
    "Открыть файл ID": "Open ID file",
    "Назначено ID:": "Assigned IDs:",
    "Все ID очищены": "All IDs cleared",
    "освобождён": "released",
    "Нет свободных ID в model_ids.txt": "No free IDs in model_ids.txt",
    "Нет свободных ID в активном пресете": "No free IDs in the active preset",
    "Показать пути IDE/IPL/IMG": "Show IDE/IPL/IMG paths",
    "Показать настройки текстур": "Show texture settings",
    "Показать настройки суффиксов": "Show suffix settings",
    "Показать менеджер ID": "Show ID Manager",
    "Показать флаги IDE": "Show IDE flags",
    "Суффикс для DFF моделей (например _DFF или DFF)": "Suffix for DFF models (e.g. _DFF or DFF)",
    "Суффикс для LOD моделей (например _LOD или LOD)": "Suffix for LOD models (e.g. _LOD or LOD)",
    "Суффикс для COL моделей (например _COL или COL)": "Suffix for COL models (e.g. _COL or COL)",
    "Порог яркости: 0 = без порога, 100 = максимальная отсечка": "Brightness threshold: 0 = max cutoff, 100 = no cutoff",
    "Порог": "Threshold",
    "Край": "Edge",
    "Контраст": "Contrast",
    "Цифры": "Numbers",
    "Размер": "Size",
    "Скрыть превью": "Hide preview",
    "Превью COL Light": "Preview COL Light",
    "Дневной свет:": "Day light:",
    "Ночной свет:": "Night light:",
    "Мин.": "Min.",
    "Макс.": "Max.",
    "Импорт из IMG": "Import from IMG",
    "Извлечь ресурсы": "Extract Resources",
    "Собрать карту": "Build Map",
    "Bounds / Textured": "Bounds / Textured",
    "Bounds: ON": "Bounds: ON",
    "Bounds: OFF": "Bounds: OFF",
    "Загрузить .glb": "Load .glb",
    "уникальных моделей": "unique meshes",
    "Нет моделей для импорта": "No models to import",
    "Нет DFF файлов в кэше. Сначала извлеките ресурсы.": "No DFF files in cache. Extract resources first.",
    "Извлечено текстур:": "Textures extracted:",
    "Импорт карты": "Import Map",
    "Заменить на DFF": "Replace with DFF",
    "Заменено:": "Replaced:",
    "Выделите fake объекты карты": "Select fake map objects",
    "Импорт плоскостей вместо моделей (быстрый превью карты)": "Import planes instead of models (fast map preview)",
    "Район карты для импорта": "Map region to import",
    "Не найден gta3.img": "gta3.img not found",
    "Не найден IMG архив": "IMG archive not found",
    "Секции IPL": "IPL Sections",
    "Пропустить LOD модели при импорте": "Skip LOD models during import",
    "Загружать TXD текстуры вместе с DFF": "Load TXD textures with DFF",
    "Импортировано:": "Imported:",
    "Экспорт в IMG": "Export to IMG",
    "Укажите путь к IMG архиву в INU Tools": "Set IMG archive path in INU Tools",
    "IPL файл пуст или не указан": "IPL file is empty or not specified",
    "Пропустить LOD модели при импорте": "Skip LOD models during import",
    "Загружать TXD текстуры вместе с DFF": "Load TXD textures with DFF",
    "Импортировано:": "Imported:",
    "пропущено:": "skipped:",
    "ошибок:": "errors:",
    "Укажите путь к IDE файлу": "Set IDE file path",
    "Укажите путь к IPL файлу": "Set IPL file path",
    "Нет объектов с Model ID > 0": "No objects with Model ID > 0",
    "объектов с Model ID = 0, задайте ID в свойствах": "objects with Model ID = 0, set ID in properties",
    "обновлено": "updated",
    "добавлено": "added",
    "удалено": "removed",
    "Пресеты:": "Presets:",
    "Пресет загружен:": "Preset loaded:",
    "Пресет не найден": "Preset not found",
    "Пресет сохранён:": "Preset saved:",
    "Пресет удалён:": "Preset deleted:",
    "Выбрать пресет настроек прелайта": "Select prelight settings preset",
    "Сгладить между объектами": "Smooth between objects",
    "Сглажено стыков:": "Smoothed seams:",
    "Выделите минимум 2 меш объекта": "Select at least 2 mesh objects",
    "Нет vertex colors": "No vertex colors",
    "Максимальное расстояние между вершинами для сопоставления": "Maximum distance between vertex for matching",
    "Открыт:": "Opened:",
    "Проверка вершин": "Check Vertex",
    "Проверка N-gon": "Check N-gon",
    "Проверка материалов": "Check materials",
    "Очистка материалов": "Cleanup materials",
    "Сортировка материалов": "Sort materials",
    "Сброс трансформ": "Reset Transform",
    "Сброшено объектов:": "Objects reset:",
    "LightMap UV2": "LightMap UV2",
    "Добавить LightMap": "Add LightMap",
    "Привязанные 2DFX:": "Attached 2DFX:",
    "Отвязать все": "Detach All",
    "материалов": "materials",
    "удалено": "removed",
    "Файл не найден": "File not found",
    "COL light материалов:": "COL light materials:",
    "Запечь COL Light": "Bake COL Light",

    # Water IO
    "Добавить воду": "Add Water",
    "Параметры воды:": "Water Parameters:",
    "Скорость течения:": "Flow Speed:",
    "Волны": "Waves",
    "Применить": "Apply",
    "Инструменты:": "Tools:",
    "Привязка к сетке (x4)": "Snap to Grid (x4)",
    "Сшить края": "Stitch Edges",
    "Обычная / Невидимая": "Default / Invisible",
    "Обычная / Видимая": "Default / Visible",
    "Мелкая / Невидимая": "Shallow / Invisible",
    "Мелкая / Видимая": "Shallow / Visible",
    "Глубокая вода, не отображается (подводные зоны)": "Deep water, not rendered (underwater zones)",
    "Глубокая вода с волнами (океан, реки)": "Deep water with waves (ocean, rivers)",
    "Мелкая вода, не отображается (анимация хождения по воде)": "Shallow water, not rendered (wade animation)",
    "Мелкая вода, отображается (лужи, пруды)": "Shallow water, rendered (puddles, ponds)",

    # Path IO
    "Пути": "Paths",
    "Маршруты полётов:": "Flight Paths:",
    "Ж/д пути:": "Train Tracks:",
    "Пешеходные/Авто пути:": "Ped/Vehicle Paths:",
    "Маршрут полёта": "Flight Path",
    "Ж/д путь": "Train Track",
    "Авто пути": "Vehicle Paths",
    "Пешеходные пути": "Ped Paths",
    "Навигационные точки": "Navigation Nodes",
    "Создать ж/д путь": "Add Train Track",
    "Станция (вкл/выкл)": "Station (toggle)",
    "Авто путь": "Vehicle Path",
    "Пеш. путь": "Ped Path",
    "Ж/д путь создан. Редактируйте в Edit Mode": "Train track created. Edit in Edit Mode",
    "Авто путь создан. Добавляйте вершины в Edit Mode": "Vehicle path created. Add vertex in Edit Mode",
    "Пешеходный путь создан. Добавляйте вершины в Edit Mode": "Ped path created. Add vertex in Edit Mode",
    "Пути (paths.ipl):": "Paths (paths.ipl):",
    "Создать путь": "Add Path",
    "Скомпилированные (NODES):": "Compiled (NODES):",
    "Путь IPL": "Path IPL",
    "Авто": "Vehicle",
    "Пешеходный": "Pedestrian",
    "Автомобильный путь": "Vehicle path",
    "Пешеходный путь": "Pedestrian path",
    "Конвертировать в путь": "Convert to Path",
    "Нельзя конвертировать меш с полигонами": "Cannot convert mesh with polygons",

    # IFP Animations
    "Анимации": "Animations",
    "Анимации IFP (GTA SA):": "IFP Animations (GTA SA):",
    "анимаций загружено": "animations loaded",
    "Анимация": "Animation",
    "Применить анимацию": "Apply Animation",
    "Текущая": "Current",
    "Выделите скелет для применения": "Select armature to apply",
    "Выделите скелет (Armature)": "Select an armature",
    "Разблокировать редактирование": "Unlock Editing",
    "Редактирование разблокировано. Геометрия будет пересчитана при экспорте": "Editing unlocked. Geometry will be rebuilt on export",
    "Экспорт: побайтовая копия": "Export: byte-perfect copy",
    "Редактирование разблокировано": "Editing unlocked",
    "Экспорт: пересчёт геометрии": "Export: geometry rebuild",
    "Скин: побайтовая копия": "Skin: byte-perfect copy",
    "Скин: пересчёт геометрии": "Skin: geometry rebuild",

    # v1.6.0 / v1.6.1
    "Извлечь ресурсы": "Extract Resources",
    "Собрать карту в .glb": "Build Map .glb",
    "Импорт карты .glb": "Import Map .glb",
    "Заменить Empty": "Replace Empty",
    "Удалить из IMG": "Remove from IMG",
    "Файлы IMG": "IMG Files",
    "Обновить список": "Refresh List",
    "Создать файл ID": "Create ID File",
    "Загрузить из игры": "Load from Game",
    "Открыть файл ID": "Open ID File",
    "Назначить ID выделенным": "Assign ID to Selected",
    "Синхронизировать сцену": "Sync Scene",
    "Заполнить ID (321-19999)": "Fill IDs (321-19999)",
    "Занято ID:": "Used IDs:",
    "Загружено ID:": "Loaded IDs:",
    "Добавлено ID:": "Added IDs:",
    "Очищено ID:": "Cleared IDs:",
    "Все ID очищены": "All IDs cleared",
    "Файл ID не найден. Нажмите 'Создать файл ID'": "ID file not found. Click 'Create ID File'",
    "Свободных:": "Free:",
    "Занятых:": "Used:",
    "Следующий свободный:": "Next free:",
    "Свободные:": "Free:",
    "ещё": "more",
    "LOD/COL → DFF": "LOD/COL → DFF",
    "Перемещено:": "Moved:",
    "Сшить вершины": "Snap Border Vertex",
    "вершин усреднено": "vertex averaged",
    "Суффиксы / Префиксы": "Suffixes / Prefixes",
    "Суффиксы:": "Suffixes:",
    "Префиксы:": "Prefixes:",
    "суффикс ИЛИ префикс": "suffix OR prefix",
    "Секции IPL": "IPL Sections",
    "Количество записей в IDE файле": "Number of entries in IDE file",
    "Количество записей в IPL файле": "Number of entries in IPL file",
    "конфликт с": "conflict with",
    "Укажите путь к .img архиву": "Specify path to .img archive",
    "Файлы не найдены в IMG": "Files not found in IMG",
    "Авто TXD": "Auto TXD",
    "текстур импортировано": "textures imported",
    "Поиск по ID или имени модели": "Search by ID or model name",
    "Дистанция LOD": "LOD Distance",
    "Дальность прорисовки LOD модели (IDE)": "LOD model draw distance (IDE)",
    "Префикс для DFF моделей": "Prefix for DFF models",
    "Префикс для LOD моделей": "Prefix for LOD models",
    "Префикс для COL моделей": "Prefix for COL models",
    "Укажите корневую папку GTA SA": "Specify GTA SA root folder",
    "Район карты для импорта": "Map region for import",
    "Нет DFF файлов в кэше. Сначала извлеките ресурсы.": "No DFF files in cache. Extract resources first.",
    "Ошибка чтения IMG": "IMG read error",
    "Укажите путь к IMG": "Specify path to IMG",
    "Файлов:": "Files:",
    "Отсортировано:": "Sorted:",
    "BBox: OFF": "BBox: OFF",
    "BBox: ON": "BBox: ON",
    "Links: OFF": "Links: OFF",
    "Links: ON": "Links: ON",
    "Import Map": "Import Map",
    "Вся карта": "Entire Map",
    "Блик солнца": "Sun Glare",
    "Свет": "Light",
    "Частица": "Particle",
    "Ped Attractor": "Ped Attractor",
    "Тип эффекта": "Effect Type",
    "Убрать Itera": "Remove Itera",
    "Импорт DFF": "Import DFF",
    "Экспорт DFF": "Export DFF",
    "Импорт COL": "Import COL",
    "Экспорт COL": "Export COL",
    "Экспорт TXD": "Export TXD",
    "Экспорт / Импорт": "Export / Import",
    "Импорт всей карты": "Import Entire Map",
    "Выберите 2DFX Empty для редактирования": "Select a 2DFX Empty to edit",
    "Itera Tools 3 не найден в библиотеках ассетов": "Itera Tools 3 not found in Asset Libraries",
    "Itera не найден в библиотеках ассетов": "Itera not found in Asset Libraries",
    "Коллекции Itera привязаны к сцене": "Itera collections linked to scene",
    "Линейное освещение вершин с UV текстурой": "Vertex Lit Linear with UV texture",
    "Не найден Armature!": "Armature not found!",
    "Нет активного объекта!": "No active object!",
    "Нет граничных вершин": "No border vertex",
    "Показать цифры на полигонах": "Show numbers on polygons",
    "Порог яркости: 0 = без порога, 100 = максимальная отсечка": "Brightness threshold: 0 = no threshold, 100 = max cutoff",
    "Размер цифр на полигонах": "Number size on polygons",
    "Контраст: резкость перехода между тёмными и светлыми зонами": "Contrast: sharpness between dark and light zones",
    "Сдвиг границы COL освещения: + расширяет зелёную зону, — сужает": "COL light boundary shift: + expands green zone, — shrinks",
    "Статус: Готов": "Status: Ready",
    "Статус: Не найден": "Status: Not Found",
    "Суффикс для DFF моделей": "Suffix for DFF models",
    "Суффикс для LOD моделей": "Suffix for LOD models",
    "Суффикс для COL моделей": "Suffix for COL models",
    "Day — дневные вертексные цвета (prelight)\nNight — ночные вертексные цвета (требует Pipeline: Building)":
        "Day — daytime vertex colors (prelight)\nNight — nighttime vertex colors (requires Pipeline: Building)",
    "None — без pipeline\nVehicle — машины (отражения кузова, env map)\nBuilding DN — здания с day/night vertex colors\nBuilding — обычные здания\n\nNormals — динамическое освещение движком (персонажи, транспорт, оружие)\nОтключить для зданий и объектов карты (используют vertex colors)":
        "None — no pipeline\nVehicle — cars (body reflections, env map)\nBuilding DN — buildings with day/night vertex colors\nBuilding — plain buildings\n\nNormals — dynamic engine lighting (characters, vehicles, weapons)\nDisable for buildings and map objects (use vertex colors)",
    # FLA / ID Manager
    "Расширить ID (FLA)": "Extend IDs (FLA)",
    "Количество ID для добавления": "Number of IDs to add",

    # ID Presets (v1.6.4+)
    "Пресет ID": "ID Preset",
    "Пресет": "Preset",
    "Активный файл со списком ID. Каждый пресет — отдельный .txt в папке data/id_presets/":
        "Active file with the ID list. Each preset is a separate .txt in data/id_presets/",
    "Название пресета": "Preset name",
    "Имя нового пресета": "Name of the new preset",
    "Название": "Name",
    "Имя нового пресета. Будет сохранён как data/id_presets/<имя>.txt":
        "Name of the new preset. Will be stored as data/id_presets/<name>.txt",
    "Скопировать с активного": "Copy from active",
    "Создать пресет как копию текущего активного":
        "Create the preset as a copy of the current active one",
    "Введите название пресета": "Enter a preset name",
    "Пресет уже существует или не удалось создать":
        "Preset already exists or could not be created",
    "Создан пресет:": "Preset created:",
    "Пресет 'default' удалить нельзя": "The 'default' preset cannot be deleted",
    "Не удалось удалить пресет": "Failed to delete the preset",
    "Удалён пресет:": "Preset deleted:",
    "Новое название": "New name",
    "Введите новое название": "Enter a new name",
    "Не удалось переименовать (имя занято или ошибка)":
        "Failed to rename (name taken or error)",
    "Переименован:": "Renamed:",
    "Заполнить активный пресет ID (321-19999, все свободные)":
        "Fill the active ID preset (321-19999, all free)",
    "Открыть файл активного ID пресета в текстовом редакторе":
        "Open the active ID preset file in a text editor",
    "Создать новый пресет ID.\n\n    Пустой пресет создаётся готовым к `Создать файл ID` (Заполнить 321-19999).\n    Опция «Скопировать с активного» дублирует текущий файл ID, чтобы не\n    начинать с нуля, если часть ID уже назначена.":
        "Create a new ID preset.\n\nAn empty preset is ready for 'Create ID File' (fill 321-19999).\nThe 'Copy from active' option duplicates the current ID file so you\ndon't have to start from scratch when some IDs are already assigned.",
    "Удалить активный пресет ID. Пресет «default» удалить нельзя":
        "Delete the active ID preset. The 'default' preset cannot be removed",
    "Переименовать активный пресет ID": "Rename the active ID preset",

    # Batch operations
    "Назначить с ID...": "Assign from ID...",
    "Начальный ID для назначения": "Starting ID for assignment",
    "Назначено ID:": "Assigned IDs:",
    "Тип:": "Type:",

    # X Radar Maker
    "Папка": "Folder",
    "Сетка": "Grid",
    "Размер": "Size",
    "Высота": "Height",
    "Индексы": "Indices",
    "Генерировать радар": "Generate Radar",
    "Меню радар (3x3)": "Menu Radar (3x3)",
    "Полный радар": "Full Radar",
    "Полный меню": "Full Menu",
    "Указанные тайлы": "Specific Tiles",
    "Упаковать в TXD": "Pack to TXD",
    "тайлов сохранено": "tiles saved",
    "архивов создано": "archives created",
    "Укажите папку для сохранения": "Specify output folder",
    "Укажите индексы тайлов (например 0,1,8,9)": "Specify tile indices (e.g. 0,1,8,9)",
    "Папка для сохранения тайлов радара": "Folder for saving radar tiles",
    "Размер сетки (8 = 64 тайла)": "Grid size (8 = 64 tiles)",
    "Размер тайла в пикселях": "Tile size in pixels",
    "Высота камеры": "Camera height",
    "Индексы тайлов через запятую (0,1,5,63)": "Tile indices comma-separated (0,1,5,63)",

    # v1.6.3 — Particle Effects (effects.fxp)
    "Имя эффекта из effects.fxp": "Effect name from effects.fxp",
    "Индекс редактируемого эмиттера (для систем с несколькими)": "Index of edited emitter (for multi-emitter systems)",
    "Редактируемая кривая в формате INFO.FIELD (например SIZE.SIZEX)": "Edited curve in INFO.FIELD format (e.g. SIZE.SIZEX)",
    "Имя спрайта из particle.txd": "Sprite name from particle.txd",
    "Добавить промежуточный ключ для плавного fade-in/fade-out": "Add intermediate key for smooth fade-in/fade-out",
    "Позиция промежуточного ключа по времени жизни (0..1)": "Intermediate key position over lifetime (0..1)",
    "Размер частицы в начале жизни": "Particle size at start of life",
    "Размер частицы в конце жизни": "Particle size at end of life",
    "Длительность жизни частицы в секундах": "Particle lifetime in seconds",
    "Количество частиц в секунду": "Particles per second",
    "Начальная скорость частицы": "Particle initial speed",
    "Направление эмиссии": "Emission direction",
    "Анимировать 2DFX частицы в viewport": "Animate 2DFX particles in viewport",
    "Имя нового эффекта (должно быть уникальным)": "New effect name (must be unique)",
    "Создастся пустая система с одним эмиттером": "An empty system with one emitter will be created",
    "Текстура: sphere. Жизнь 1с, rate 10/с, цвет белый": "Texture: sphere. Life 1s, rate 10/s, color white",
    "Действие необратимо (хотя есть .bak)": "Action is irreversible (though .bak is available)",
    "Имя системы в effects.fxp (можно новое — тогда клонируется из текущей)": "System name in effects.fxp (new name clones from current)",
    "Перезаписать существующую систему с таким именем": "Overwrite existing system with this name",
    "При первой записи создастся effects.fxp.bak": "On first write effects.fxp.bak will be created",
    "Эффект": "Effect",
    "Симуляция": "Simulation",
    "Переключение сбросит правки — сохраняйте первыми": "Switching will reset edits — save first",
    "Спрайт и смешивание": "Sprite & blending",
    "Текстура": "Texture",
    "Цвет (start → end)": "Color (start → end)",
    "Начало": "Start",
    "Средний": "Middle",
    "Конец": "End",
    "Эмиссия": "Emission",
    "Жизнь": "Life",
    "Скорость": "Speed",
    "Направление": "Direction",
    "Физика": "Physics",
    "Система": "System",
    "Кривые (keyframes)": "Curves (keyframes)",
    "Выбрать кривую...": "Select curve...",
    "Нет ключей": "No keys",
    "Записать кривую в effects.fxp": "Write curve to effects.fxp",
    "Сохранить в effects.fxp": "Save to effects.fxp",
    "effects.fxp не найден:": "effects.fxp not found:",
    "Ошибка парсинга effects.fxp:": "effects.fxp parse error:",
    "Reload effects.fxp": "Reload effects.fxp",

    # v1.6.3 — Object Properties IDE/IPL panel
    "GTA SA: IDE / IPL": "GTA SA: IDE / IPL",

    # v1.6.3 — Bone Management
    "Выделите кость в Armature": "Select a bone in Armature",
    "Выделите Armature": "Select an Armature",
    "Не найдены пары костей L/R": "No L/R bone pairs found",
    "Armature не найден": "Armature not found",
    "Костей:": "Bones:",
    "Переименовать": "Rename",
    "Выделить": "Select",
    "Выделите кость для редактирования": "Select a bone to edit",
    "Инструменты весов:": "Weight Tools:",
    "Нормализовать (4 кости)": "Normalize (4 bones)",
    "Зеркалировать X (L↔R)": "Mirror X (L↔R)",
    "Список костей:": "Bone List:",

    # v1.6.3 — Vertex Paint panel
    "Пост-обработка:": "Post-processing:",
    "Объект": "Object",

    # v1.6.3 — Shared TXD
    "Общий TXD": "Shared TXD",
    "Имя общего TXD файла для нескольких DFF моделей": "Shared TXD filename for multiple DFF models",

    # v1.6.3 — Copy color attributes
    "Day → Night": "Day → Night",
    "Night → Day": "Night → Day",
    "объектов": "objects",

    # v1.6.4 — Experimental features
    # Operator docstrings
    "Проверить все материалы и показать текстуры, файлы которых не найдены":
        "Scan all materials and report textures whose files cannot be found",
    "Рекурсивно искать в выбранной папке и подставлять image.filepath для найденных по имени недостающих текстур":
        "Search a folder recursively and patch image.filepath for any missing texture found by name",
    "Скопировать все используемые материалами текстуры сцены в выбранную папку":
        "Copy every texture used by scene materials into the chosen folder",
    "Хэшировать все файлы текстур и показать группы одинаковых файлов":
        "Hash every texture file and report groups of identical files",
    "Пропорционально масштабировать всю иерархию машины (Empty-корень + меши + дамми), сохраняя структуру. Применяет масштаб к данным меша чтобы DFF-экспорт остался чистым":
        "Rescale the active vehicle hierarchy (Empty root + meshes + dummies) preserving structure. Applies scale to mesh data so DFF export stays clean",
    "Экспортировать выделение как готовый район GTA SA (DFF + COL + TXD + IDE + IPL в одну папку)":
        "Export the current selection as a ready-to-ship GTA SA map (DFF + COL + TXD + IDE + IPL in one folder)",
    "Импортировать все *.ifp из папки и уложить анимации на NLA-трек активного armature":
        "Import every *.ifp in a folder and stack animations on an NLA track of the active armature",
    "Пересоздать видимые Empty-маркеры для каждой станции на активном ж/д пути":
        "Recreate visible Empty markers for every station on the active train track",
    "Переключить roadblock или задать тип светофора на выделенных точках кривой пути":
        "Toggle roadblock or set traffic-light kind on selected spline points of the active path curve",
    "Импорт текстового файла Steve's COL Editor (.cst)":
        "Import a Steve's COL Editor text file (.cst)",
    "Экспорт выделения в текстовый файл Steve's COL Editor (.cst)":
        "Export selection as Steve's COL Editor text file (.cst)",
    "Записать выбранный GTA Material пресет в свойства mat.inu.*":
        "Write the selected GTA Material preset into mat.inu.* properties",

    # Property descriptions
    "Создать подпапку на каждый txd_name (читается с mesh-объектов)":
        "Create a subfolder per txd_name (read from mesh objects)",
    "Множитель равномерного масштаба — применяется к позициям и вершинам":
        "Uniform scale factor applied to positions and vertices",
    "Двигать только дамми-Empty, меши не трогать":
        "Move only the dummy empties, leave meshes untouched",
    "Первый ID для DFF у которых inu.model_id == 0":
        "First ID assigned to DFFs that have inu.model_id == 0",
    "Применять только анимации, имя которых начинается с этого префикса (регистронезависимо)":
        "Only apply animations whose name starts with this prefix (case-insensitive)",
    "Уложить клипы на один NLA-трек с зазором":
        "Stack clips on one NLA track with a gap",
    "Создать Actions, без NLA":
        "Create Actions, no NLA arrangement",
    "Переключить бит 12 (барьер копов) на каждой выделенной точке":
        "Flip bit 12 (cops barrier) on every selected point",
    "Поставить traffic_light=0 на каждой выделенной точке":
        "Write traffic_light=0 on every selected point",
    "Поставить traffic_light=1 на каждой выделенной точке":
        "Write traffic_light=1 on every selected point",
    "Поставить traffic_light=2 на каждой выделенной точке":
        "Write traffic_light=2 on every selected point",
    "Поставить traffic_light=3 на каждой выделенной точке":
        "Write traffic_light=3 on every selected point",

    # UI buttons / labels
    "Импорт CST": "Import CST",
    "Экспорт CST": "Export CST",
    "Масштаб машины…": "Vehicle Scale…",
    "Batch папка…": "Batch Folder…",
    "Обновить маркеры станций": "Refresh Station Markers",
    "Флаги выделенных точек:": "Flags on selected points:",
    "Переключить Roadblock": "Toggle Roadblock",
    "Светофор —": "Light —",
    "Обычн.": "Normal",
    "Ж/д": "Rail",
    "Авт.": "Bus",
    "Разрушаемый (Breakable)": "Breakable",
    "Писать UV Anim в DFF": "Write UV Anim to DFF",
    "UV Анимация": "UV Animation",
    "Имя анимации": "Animation name",
    "Длительность": "Duration",
    "Break Force": "Break Force",

    # Binary IPL selector
    "Сканировать IMG архивы и собрать список бинарных IPL для выбранного района. После скана можно галочками включать/выключать конкретные файлы":
        "Scan IMG archives and collect the list of binary IPLs for the selected region. After the scan you can enable/disable individual files via checkboxes",
    "Включить этот бинарный IPL в сборку карты":
        "Include this binary IPL when building the map",
    "Включить или выключить все бинарные IPL в списке одной кнопкой":
        "Enable or disable every binary IPL in the list at once",
    "Развернуть список бинарных IPL для галочек":
        "Expand the list of binary IPLs to see individual checkboxes",
    "Бинарные IPL": "Binary IPLs",
    "Район изменился — пересканируйте": "Region changed — rescan",
    "Список пуст — нажмите Scan": "List is empty — click Scan",
    "Все": "All",
    "Никакие": "None",
    "Без 2DFX": "No 2DFX",
    "Не импортировать 2DFX-эффекты (лампы, частицы, ped attractors, sun glare) при импорте карты и DFF":
        "Skip 2DFX effects (lights, particles, ped attractors, sun glare) when importing the map or a DFF",

    # Pipeline enum tooltips
    "Без указания pipeline — использовать стандартный рендер RenderWare. Подходит для простых объектов, которым не нужны специальные эффекты движка":
        "No pipeline — use the plain RenderWare renderer. Suitable for simple objects that need no engine-specific effects",
    "Pipeline кузова машины (RSPIPE_PC_CustomCarEnvMap). Добавляет env-map отражения неба/облаков/улицы. Используется совместно с текстурами vehicleenv128 + vehiclespecdot64 на материале":
        "Car body pipeline (RSPIPE_PC_CustomCarEnvMap). Adds env-map reflections of sky/clouds/street. Pair with vehicleenv128 + vehiclespecdot64 textures on the material",
    "Pipeline здания с day/night vertex colors (RSPIPE_PC_CustomBuildingDN). Движок плавно смешивает дневной и ночной слои vertex colors по игровому времени. Требует ДВА Color Attribute слоя (Day + Night) на меше":
        "Building pipeline with day/night vertex colors (RSPIPE_PC_CustomBuildingDN). The engine blends day and night color layers based on in-game time. Requires TWO Color Attribute layers (Day + Night) on the mesh",
    "Простой pipeline здания (RSPIPE_PC_CustomBuilding). Статическое освещение через один слой vertex colors. Работает быстрее чем Day/Night, но нет смены по времени суток":
        "Plain building pipeline (RSPIPE_PC_CustomBuilding). Static lighting via one vertex color layer. Faster than Day/Night but no time-of-day transition",
    "Указать произвольное значение pipeline ID через поле Custom Pipeline":
        "Enter an arbitrary pipeline ID via the Custom Pipeline field",

    # UV Animation property descriptions
    "Вписать простую UV-прокрутку в экспортируемый DFF":
        "Embed a simple UV-scroll animation into the exported DFF",
    "Скорость прокрутки UV по U в секунду":
        "UV scroll speed along U per second",
    "Скорость прокрутки UV по V в секунду":
        "UV scroll speed along V per second",
    "Длительность цикла UV-анимации":
        "Duration of the UV animation cycle",

    # ── Operator/Panel docstrings (auto-translated via register loop) ───
    "IDE/IPL свойства в Object Properties": "IDE / IPL properties in Object Properties",
    "X Radar Maker — генерация тайлов мини-карты GTA SA":
        "X Radar Maker — generate GTA SA radar tiles",
    "Включить/выключить отображение LightMap UV2":
        "Toggle LightMap UV2 display",
    "Выбрать активный ключ для удаления":
        "Select the active keyframe for removal",
    "Выбрать имя эффекта из effects.fxp":
        "Pick an effect name from effects.fxp",
    "Выбрать кривую для редактирования":
        "Pick a curve to edit",
    "Выбрать позицию привязки UV в ячейке":
        "Pick the UV snap anchor inside the cell",
    "Выставить Vehicle pipeline (0x53F2009A) на выделенных MESH-объектах.\n    Нужен чтобы кузов получил env-map отражения в игре.":
        "Set the Vehicle pipeline (0x53F2009A) on selected MESH objects.\nRequired so the body gets env-map reflections in game.",
    "Генерировать тайлы радара GTA SA":
        "Generate GTA SA radar tiles",
    "Добавить / обновить запись в существующем IDE файле (авто-LOD)":
        "Insert / update an entry in an existing IDE file (auto-LOD)",
    "Добавить / обновить запись в существующем IPL файле (авто-LOD привязка)":
        "Insert / update an entry in an existing IPL file (auto-LOD linkage)",
    "Добавить ID (Fastman Limit Adjuster)":
        "Add IDs (Fastman Limit Adjuster)",
    "Добавить ID из объектов сцены в менеджер":
        "Add IDs from scene objects into the manager",
    "Добавить ключевой кадр в конец кривой":
        "Append a keyframe to the end of the curve",
    "Единый экспорт INU — DFF, COL, TXD, IDE, IPL в одну папку":
        "Unified INU export — DFF, COL, TXD, IDE, IPL into one folder",
    "Загрузить выбранный пресет":
        "Load the selected preset",
    "Загрузить занятые ID из IDE файлов GTA SA":
        "Load occupied IDs from GTA SA IDE files",
    "Задать параметры воды для выделенных объектов":
        "Set water parameters on selected objects",
    "Заменить IPL Empty-плейсхолдеры на модели из сцены":
        "Replace IPL empty placeholders with scene models",
    "Заменить выделенные fake-объекты на DFF модели из IMG":
        "Replace selected fake objects with real DFF models from IMG",
    "Записать буфер ключей обратно в effects.fxp для выбранной кривой":
        "Write the keyframe buffer back to effects.fxp for the selected curve",
    "Извлечь все DFF, COL и текстуры из IMG в .inu_cache/":
        "Extract all DFF, COL and textures from IMG into .inu_cache/",
    "Импорт GTA SA файлов (.dff/.col/.txd/.ide/.ipl) с авто-определением формата":
        "Import GTA SA files (.dff/.col/.txd/.ide/.ipl) with auto format detection",
    "Импорт IFP — анимации GTA SA":
        "Import IFP — GTA SA animations",
    "Импорт TXD при перетаскивании во viewport":
        "Import TXD on drag-and-drop into the viewport",
    "Импорт flight.dat — маршруты полётов":
        "Import flight.dat — flight paths",
    "Импорт nodes.dat — пешеходные/авто пути (мультивыбор)":
        "Import nodes.dat — pedestrian / vehicle paths (multi-select)",
    "Импорт paths.ipl — пути для gta.dat":
        "Import paths.ipl — paths listed in gta.dat",
    "Импорт tracks.dat — железнодорожные пути":
        "Import tracks.dat — railway paths",
    "Импорт water.dat": "Import water.dat",
    "Импорт карты GTA SA: автопоиск IDE/IPL/IMG по папке игры":
        "Import GTA SA map: auto-discover IDE/IPL/IMG from the game folder",
    "Импорт секций IPL (cull, grge, enex, pick, cars, auzo, jump, occl)":
        "Import IPL sections (cull, grge, enex, pick, cars, auzo, jump, occl)",
    "Импортировать .glb карты с сортировкой по коллекциям":
        "Import map .glb with per-collection sorting",
    "Импортировать модели из IMG архива (по списку из IDE/IPL)":
        "Import models from an IMG archive (driven by IDE/IPL)",
    "Интеграция с Itera Tools 3 — материалы освещения":
        "Itera Tools 3 integration — lighting materials",
    "Конвертировать кривую или рёбра меша в путь paths.ipl":
        "Convert a curve or mesh edges into a paths.ipl path",
    "Копировать vertex colors из одного атрибута в другой (Day ↔ Night)":
        "Copy vertex colors between attributes (Day ↔ Night)",
    "Массовое переключение типа объектов (OBJ/COL/SHA/2DFX/NON)":
        "Batch switch object type (OBJ/COL/SHA/2DFX/NON)",
    "Назначить ID всем выделенным объектам с Model ID = 0":
        "Assign IDs to every selected object with Model ID = 0",
    "Назначить последовательные ID выделенным объектам начиная с указанного":
        "Assign sequential IDs to selected objects starting from a given value",
    "Найти все IDE/IPL/IMG по gta.dat из корневой папки игры":
        "Find every IDE/IPL/IMG referenced by gta.dat from the game root",
    "Обновить список файлов IMG архива":
        "Refresh the IMG archive file list",
    "Объединить дубликаты материалов и текстур (.001, .002, и т.д.) с оригиналами":
        "Merge duplicate materials and textures (.001, .002, etc.) with their originals",
    "Освободить ID": "Release ID",
    "Отвязать все 2DFX/частицы от выделенного меша":
        "Detach every 2DFX / particle from the selected mesh",
    "Отметить/снять выбранные точки кривой как станции (flag=1)":
        "Toggle the station flag (flag=1) on the selected curve points",
    "Очистить Model ID у выделенных объектов":
        "Clear Model ID on selected objects",
    "Очистить все занятые ID": "Clear all occupied IDs",
    "Очистить сохранённые raw DFF данные для экспорта отредактированной геометрии":
        "Clear the cached raw DFF data so edited geometry is exported",
    "Панель IDE / IPL / IMG для работы с существующими файлами GTA SA":
        "IDE / IPL / IMG panel for working with existing GTA SA files",
    "Панель Path IO": "Path IO panel",
    "Панель Water IO": "Water IO panel",
    "Панель анимаций IFP": "IFP animations panel",
    "Панель проверки геометрии и материалов":
        "Geometry and materials check panel",
    "Панель экспорта/импорта GTA моделей":
        "GTA model export / import panel",
    "Переключить все Map_ объекты между Bounding Box и Textured":
        "Toggle every Map_ object between Bounding Box and Textured",
    "Переключить редактируемый эмиттер в системе с несколькими":
        "Switch the editable emitter in a multi-emitter system",
    "Перечитать effects.fxp с диска (сбросить кэш)":
        "Reload effects.fxp from disk (flush cache)",
    "Подтянуть LOD и COL к позиции DFF модели":
        "Snap LOD and COL to the DFF model's position",
    "Показать/скрыть линии связей DFF↔LOD↔COL":
        "Show / hide DFF ↔ LOD ↔ COL link lines",
    "Превью COL Night Light — зелёная визуализация и числа на полигонах":
        "Preview COL Night Light — green overlay and per-face numbers",
    "Привязать вершины воды к кратным 4 координатам (требование GTA SA)":
        "Snap water vertices to multiples of 4 (GTA SA requirement)",
    "Применить IFP анимацию к выделенному скелету":
        "Apply an IFP animation to the selected armature",
    "Применить Itera материал из библиотеки к выделенным объектам":
        "Apply an Itera material from the library to selected objects",
    "Применить Quickstart Vertex Lightable Surface — модификатор + коллекция со светом":
        "Apply Quickstart Vertex Lightable Surface — modifier + light collection",
    "Применить стандартные SA-настройки для материала кузова машины:\n    env map = xvehicleenv128, specular = vehiclespecdot64, blend = 0.05, + Vehicle pipeline.\n    Эквивалент кнопки \"SA Vehicle default\" из Kam's GTA_Material.ms.":
        "Apply standard SA vehicle body settings:\nenv map = xvehicleenv128, specular = vehiclespecdot64, blend = 0.05, + Vehicle pipeline.\nEquivalent to Kam's GTA_Material.ms 'SA Vehicle default' button.",
    "Применить текстуру LightMap на UV2 (Multiply) для выделенных объектов":
        "Apply a LightMap texture on UV2 (Multiply) for selected objects",
    "Сброс Location и Rotation в (0,0,0) для выделенных мешей":
        "Reset Location and Rotation to (0, 0, 0) on selected meshes",
    "Сгладить vertex colors на стыках между выделенными объектами":
        "Smooth vertex colors across seams between selected objects",
    "Скрыть/показать DFF, LOD или COL объекты во всей сцене":
        "Hide / show DFF, LOD or COL objects across the whole scene",
    "Собрать один .glb файл карты (все модели с позициями из IPL)":
        "Build a single map .glb (all models with IPL positions)",
    "Создать водный полигон с параметрами GTA SA":
        "Create a water polygon with GTA SA parameters",
    "Создать новый автомобильный путь (меш с вершинами)":
        "Create a new vehicle path (vertex mesh)",
    "Создать новый ж/д путь (кривая)":
        "Create a new railway path (curve)",
    "Создать новый пешеходный путь (меш с вершинами)":
        "Create a new pedestrian path (vertex mesh)",
    "Создать новый пустой эффект в effects.fxp":
        "Create a new empty effect in effects.fxp",
    "Создать новый путь для paths.ipl":
        "Create a new path for paths.ipl",
    "Сохранить правки эффекта обратно в effects.fxp (с автобэкапом)":
        "Save effect edits back to effects.fxp (with auto-backup)",
    "Сохранить текущие настройки как пресет":
        "Save current settings as a preset",
    "Сшить края двух водных плоскостей (выровнять ближайшие вершины)":
        "Stitch the edges of two water planes (align nearest vertices)",
    "Убрать Itera материал и восстановить оригинальные":
        "Remove the Itera material and restore the originals",
    "Убрать LightMap UV2 из материалов выделенных объектов":
        "Remove LightMap UV2 from selected objects' materials",
    "Удалить DFF/TXD/COL выделенных моделей из IMG архива":
        "Remove selected models' DFF / TXD / COL from the IMG archive",
    "Удалить color attribute по имени на всех выделенных объектах":
        "Delete a color attribute by name across all selected objects",
    "Удалить активный ключевой кадр": "Delete the active keyframe",
    "Удалить выбранный пресет": "Delete the selected preset",
    "Удалить текущий эффект из effects.fxp (с автобэкапом)":
        "Delete the current effect from effects.fxp (with auto-backup)",
    "Упаковать тайлы радара в TXD архивы (1 тайл = 1 TXD)":
        "Pack radar tiles into TXD archives (1 tile = 1 TXD)",
    "Экспорт IFP — анимации GTA SA": "Export IFP — GTA SA animations",
    "Экспорт flight.dat — маршруты полётов": "Export flight.dat — flight paths",
    "Экспорт nodes.dat — группировка по имени файла или авто-разбиение по зонам":
        "Export nodes.dat — group by filename or auto-split by zones",
    "Экспорт paths.ipl — пути для gta.dat":
        "Export paths.ipl — paths listed in gta.dat",
    "Экспорт tracks.dat — железнодорожные пути":
        "Export tracks.dat — railway paths",
    "Экспорт water.dat": "Export water.dat",
    "Экспорт секций IPL из коллекций IPL_* в файл":
        "Export IPL sections from IPL_* collections into a file",
    "Экспортировать один общий TXD для нескольких DFF моделей":
        "Export a single shared TXD for multiple DFF models",

    # ── Particle property descriptions (effects.fxp) ────────────────────
    "CULLDIST — расстояние отсечения эффекта в игре":
        "CULLDIST — effect cull distance in game",
    "EMANGLE MAX — максимальный угол конуса эмиссии":
        "EMANGLE MAX — maximum emission cone angle",
    "EMANGLE MIN — минимальный угол конуса эмиссии":
        "EMANGLE MIN — minimum emission cone angle",
    "EMLIFE BIAS — случайный разброс длительности жизни":
        "EMLIFE BIAS — random lifetime scatter",
    "EMPOS X/Y/Z — смещение точки спавна":
        "EMPOS X/Y/Z — spawn point offset",
    "EMROTATION ANGLEMAX — макс начальный поворот спрайта":
        "EMROTATION ANGLEMAX — max initial sprite rotation",
    "EMROTATION ANGLEMIN — мин начальный поворот спрайта":
        "EMROTATION ANGLEMIN — min initial sprite rotation",
    "EMSIZE половина размера бокса эмиссии (centered)":
        "EMSIZE — half-extent of the emission box (centered)",
    "EMSPEED BIAS — случайный разброс начальной скорости":
        "EMSPEED BIAS — random initial-speed scatter",
    "FORCE X/Y/Z — постоянное ускорение (например -9.8 по Z = гравитация)":
        "FORCE X/Y/Z — constant acceleration (e.g. -9.8 on Z = gravity)",
    "FRICTION — сопротивление воздуха": "FRICTION — air resistance",
    "GROUNDCOLLIDE BOUNCE — сила отскока при ударе о землю":
        "GROUNDCOLLIDE BOUNCE — bounce factor on ground hit",
    "GROUNDCOLLIDE SPEEDMULT — потеря скорости при ударе":
        "GROUNDCOLLIDE SPEEDMULT — speed loss on impact",
    "JITTER JITTERFACTOR — резкий случайный дёрг":
        "JITTER JITTERFACTOR — sharp random jitter",
    "LENGTH — длительность цикла системы в секундах":
        "LENGTH — system cycle duration in seconds",
    "NOISE — сглаженное случайное движение":
        "NOISE — smoothed random motion",
    "PLAYMODE — режим проигрывания (0-3)": "PLAYMODE — play mode (0-3)",
    "ROTSPEED MAXCW — макс скорость вращения спрайта":
        "ROTSPEED MAXCW — max sprite rotation speed",
    "ROTSPEED MINCW — мин скорость вращения спрайта":
        "ROTSPEED MINCW — min sprite rotation speed",
    "WIND WINDFACTOR — восприимчивость к ветру игры":
        "WIND WINDFACTOR — game wind responsiveness",

    # ── Status / report / label strings ─────────────────────────────────
    "Автоматически ставить material alpha = 254 при наличии vertex alpha < 255.\nНужно для стандартных прозрачных мешей (стёкла, дым). Выключи если материал должен остаться opaque":
        "Automatically set material alpha = 254 when any vertex alpha < 255.\nNeeded for standard transparent meshes (glass, smoke). Disable if the material must stay opaque",
    "Восстановлено:": "Restored:",
    "Выберите папку для экспорта": "Pick an output folder",
    "Выделите объекты с нодами": "Select objects that carry nodes",
    "Извлечение ресурсов...": "Extracting resources...",
    "Импорт .glb...": "Importing .glb...",
    "Импорт .glb:": "Import .glb:",
    "Импорт карты...": "Importing map...",
    "Импорт карты:": "Import map:",
    "Источник:": "Source:",
    "Материалов:": "Materials:",
    "Не найден 3D Viewport": "No 3D Viewport found",
    "Не найдено моделей для экспорта": "No models to export",
    "Нет меш объектов для экспорта": "No mesh objects to export",
    "Нет файлов для импорта": "No files to import",
    "Нечего экспортировать": "Nothing to export",
    "Node group не найден:": "Node group not found:",
    "Открыть/Закрыть UV Editor": "Open / Close UV Editor",
    "Отменено": "Cancelled",
    "Ошибка загрузки node group:": "Failed to load node group:",
    "Писать IPL в бинарном формате (только inst+cars)":
        "Write IPL in binary format (inst + cars only)",
    "Писать nodes*.dat в расширенном FLA4 формате (spawn/speed/lanes per-node)":
        "Write nodes*.dat in extended FLA4 format (per-node spawn / speed / lanes)",
    "Пометить геометрию как разрушаемую (пишет чанк 0x253F2FD в DFF)":
        "Mark geometry as breakable (writes chunk 0x253F2FD into the DFF)",
    "Помечает меш как объёмный луч света для плагина SA_Light.asi.\nУстанавливает material color = (254,254,254,254) — этот маркер плагин ищет во время рендера.\n\nТРЕБУЕТ SA_Light.asi в корне GTA SA. Без плагина меш будет рендериться как обычный полупрозрачный объект с жёстким срезом alpha.\n\nДля использования:\n1. Собери меш-конус/куб формой луча\n2. Покрась vertex colors как хочешь (любые значения alpha)\n3. Включи этот флаг + Set Material Alpha выключи\n4. Экспорт → плагин автоматически включит плавный alpha blend на этом меше":
        "Mark the mesh as a volumetric light beam for the SA_Light.asi plugin.\nSets material color = (254, 254, 254, 254) — the plugin looks for this marker at render time.\n\nREQUIRES SA_Light.asi in the GTA SA root. Without the plugin the mesh renders as an ordinary semi-transparent object with hard alpha cutoff.\n\nHow to use:\n1. Build a cone / box mesh shaped like the beam\n2. Paint vertex colors however you want (any alpha values)\n3. Enable this flag + disable Set Material Alpha\n4. Export — the plugin switches this mesh to smooth alpha blending automatically",
    "Превью COL Light включено": "COL Light preview enabled",
    "Превью COL Light выключено": "COL Light preview disabled",
    "Привязано вершин:": "Snapped vertices:",
    "Применить SA Vehicle defaults": "Apply SA Vehicle defaults",
    "Пропущено (разные пути):": "Skipped (different paths):",
    "Сборка карты...": "Building map...",
    "Сборка карты:": "Building map:",
    "Сила, нужная чтобы сломать объект (умолчание 1.0)":
        "Force required to break the object (default 1.0)",
    "Слот цвета машины:": "Vehicle color slot:",
    "Слот цвета машины: движок SA подставит цвет из carcols.dat. Меняет базовый RGB материала на магическую метку.":
        "Vehicle color slot: the SA engine substitutes the color from carcols.dat. Replaces the material's base RGB with the magic marker.",
    "Сшито вершин:": "Stitched vertices:",
    "Текстур:": "Textures:",
    "Формат:": "Format:",
    "пропущено": "skipped",

    # ── IDE flag descriptions (wrapped with T() after fix) ──────────────
    "Дорога (1)": "Road (1)",
    "Прозрачный, рисовать последним (4)": "Transparent, draw last (4)",
    "Аддитивный блендинг (8)": "Additive blending (8)",
    "Не писать в Z-буфер (64)": "Don't write Z-buffer (64)",
    "Не получать тени (128)": "Don't receive shadows (128)",
    "Стекло разбиваемое (512)": "Breakable glass (512)",
    "Стекло с трещинами (1024)": "Cracked glass (1024)",
    "Дверь гаража (2048)": "Garage door (2048)",
    "Разрушаемый (4096)": "Breakable (4096)",
    "Дерево, качается на ветру (8192)": "Tree, sways in wind (8192)",
    "Пальма, качается на ветру (16384)": "Palm, sways in wind (16384)",
    "Нет коллизии с летающим (32768)": "No collision with flying (32768)",
    "Граффити тег (1048576)": "Graffiti tag (1048576)",
    "Рисовать обе стороны (2097152)": "Draw both sides (2097152)",
    "Разрушаемая статуя (4194304)": "Breakable statue (4194304)",

    # ── Vehicle color slot labels / enums ───────────────────────────────
    "Обычный материал, не связан с carcols": "Plain material, unrelated to carcols",
    "Основной цвет (первый в carcols.dat)": "Primary color (first in carcols.dat)",
    "Второй цвет": "Secondary color",
    "Третий цвет (некоторые машины)": "Third color (some vehicles)",
    "Четвёртый цвет": "Fourth color",
    "Левая фара": "Left headlight",
    "Правая фара": "Right headlight",
    "Левый задний фонарь": "Left tail light",
    "Правый задний фонарь": "Right tail light",

    # ── Misc property descriptions & confirmations ──────────────────────
    "Я понимаю что это перезапишет effects.fxp":
        "I understand this will overwrite effects.fxp",
    "<Game Root не задан>": "<Game Root not set>",
    "<effects.fxp не найден>": "<effects.fxp not found>",
    "<нет эффектов>": "<no effects>",
    "nvcompress.exe не найден в указанной папке":
        "nvcompress.exe not found in the given folder",

    # ── Report messages (FXP editor, misc) ──────────────────────────────
    "Имя пустое": "Name is empty",
    "Подтверждение не получено": "Confirmation not given",
    "Имя эффекта пустое": "Effect name is empty",
    "Эффект не выбран": "No effect selected",
    "У эффекта один эмиттер": "Effect has a single emitter",
    "Нет изменений — файл не тронут": "No changes — file left untouched",

    # ── IFP batch / Bitmaps / Map Export / Vehicle Scale tooltips ───────
    "Применять только анимации, имя которых начинается с этого префикса (регистронезависимо)":
        "Only apply animations whose name starts with this prefix (case-insensitive)",
    "Уложить клипы на один NLA-трек с зазором":
        "Lay clips onto one NLA track with a gap between them",
    "Создать Actions, без NLA": "Create Actions only, no NLA",
    "Создать подпапку на каждый txd_name (читается с mesh-объектов)":
        "Create a subfolder per txd_name (read from mesh objects)",
    "Первый ID для DFF у которых inu.model_id == 0":
        "Starting ID for DFFs whose inu.model_id == 0",
    "Множитель равномерного масштаба — применяется к позициям и вершинам":
        "Uniform scale factor — applied to positions and vertices",
    "Двигать только дамми-Empty, меши не трогать":
        "Move dummy Empties only, leave meshes untouched",

    # ── Imported-class docstrings (tools/* and ops/*) ───────────────────
    "Конвертировать vertex colors в COL Day/Night Light (разбиение материалов по яркости)":
        "Convert vertex colors to COL Day / Night Light (split materials by brightness)",
    "Удалить COL light материалы, созданные Bake COL Light":
        "Delete COL light materials created by Bake COL Light",
    "Проверить все материалы и показать текстуры, файлы которых не найдены":
        "Scan every material and list textures whose files are missing",
    "Рекурсивно искать в выбранной папке и подставлять image.filepath для найденных по имени недостающих текстур":
        "Recursively scan the chosen folder and reassign image.filepath for missing textures found by name",
    "Скопировать все используемые материалами текстуры сцены в выбранную папку":
        "Copy every texture used by scene materials into the chosen folder",
    "Хэшировать все файлы текстур и показать группы одинаковых файлов":
        "Hash every texture file and group identical files together",
    "Импорт текстового файла Steve's COL Editor (.cst)":
        "Import a Steve's COL Editor text file (.cst)",
    "Экспорт выделения в текстовый файл Steve's COL Editor (.cst)":
        "Export the selection to a Steve's COL Editor text file (.cst)",
    "Пропорционально масштабировать всю иерархию машины (Empty-корень + меши + дамми), сохраняя структуру. Применяет масштаб к данным меша чтобы DFF-экспорт остался чистым":
        "Uniformly scale the whole vehicle hierarchy (Empty root + meshes + dummies) while preserving structure. Applies the scale to mesh data so DFF export stays clean",

    # ── COL library mode ────────────────────────────────────────────────
    "Library (несколько коллизий)": "Library (multiple collisions)",
    "Сгруппировать выделение по базовому имени (house1_COL + house1_SHA → одна запись 'house1') и записать все группы в один .col файл подряд. Так vanilla SA хранит <district>.col и vehicles.col":
        "Group the selection by base name (house1_COL + house1_SHA → one record 'house1') and write every group into a single .col file back-to-back. This is how vanilla SA stores <district>.col and vehicles.col",
    "COL Library": "COL Library",
    "Писать все коллизии в один .col файл (multi-entry library). Каждая запись в файле — отдельная коллизия со своим model_id, сопоставляется с DFF по ID":
        "Write every collision into a single .col file (multi-entry library). Each record has its own model_id and links to a DFF by matching ID",
    "Имя library .col": "Library .col name",
    "Имя общего .col файла без расширения (например 'district' → district.col)":
        "Name of the combined .col file without extension (e.g. 'district' → district.col)",
    "Писать все коллизии в один <district>.col файл (multi-entry library). Каждая запись в файле — отдельная коллизия со своим model_id, сопоставляется с DFF по ID":
        "Write every collision into a single <district>.col file (multi-entry library). Each record has its own model_id and links to a DFF by matching ID",

    # ── Batch set distance ──────────────────────────────────────────────
    "Задать Draw Distance и/или LOD Distance всем выделенным MESH-объектам.\n\n    По умолчанию поля заполняются значениями активного объекта — можно\n    изменить и применить к выделению одним действием. Галочки слева\n    выбирают какие именно поля переписывать (удобно менять только одно)":
        "Set Draw Distance and/or LOD Distance on every selected MESH object.\n\nFields are prefilled from the active object — tweak and apply to the entire selection in one action. The left-hand checkboxes pick which fields to overwrite (handy for changing only one)",
    "Применить Draw Dist": "Apply Draw Dist",
    "Применить LOD Dist": "Apply LOD Dist",
    "объектов будет изменено": "objects will be modified",
    "Включите хотя бы одну галочку": "Enable at least one checkbox",
    "Изменено:": "Modified:",
    "Применить к выделенным": "Apply to selected",

    # ── Export-to-IMG TXD plan dialog ───────────────────────────────────
    "Экспортировать DFF + TXD + COL прямо в .img архив.\n\n    Перед записью открывается диалог со списком моделей и их TXD именами —\n    можно переключить режим на один общий TXD, отключить отдельные модели,\n    или отредактировать имя архива для каждой (модели с одинаковым TXD\n    именем попадут в один .txd с объединёнными текстурами)":
        "Export DFF + TXD + COL directly into an .img archive.\n\nBefore writing a dialog opens with the list of models and their TXD names — switch to a single shared TXD, disable individual models, or edit the archive name per model (models with the same TXD name merge into one .txd)",
    "Общий TXD": "Shared TXD",
    "Пакует все текстуры в один .txd. Выключено — один .txd на каждую уникальную строку txd_name из списка ниже":
        "Pack every texture into a single .txd. When off, each unique txd_name from the list below gets its own .txd",
    "Имя общего TXD": "Shared TXD name",
    "Имя .txd файла без расширения": "Name of the .txd file without extension",
    "Имя TXD архива для этой модели. Модели с одинаковым именем попадут в один .txd (textures merged)":
        "TXD archive name for this model. Models sharing a name merge into one .txd (textures combined)",
    "Включить модель в экспорт": "Include this model in the export",
    "IMG:": "IMG:",
    "Моделей:": "Models:",
    "TXD имя на модель:": "TXD name per model:",
    "Общий TXD включён — список игнорируется":
        "Shared TXD enabled — the list is ignored",

    # Bitmaps Manager panel
    "Менеджер текстур": "Bitmaps Manager",
    "Сканировать": "Scan",
    "Пропущено": "Missing",
    "Найти в папке…": "Resolve From Folder…",
    "Скопировать в папку…": "Copy Used To Folder…",
    "Найти дубликаты": "Find Duplicates",

    # Unified Export (Stage 3)
    "Экспорт:": "Export:",
    "В папку": "To Folder",
    "В IMG": "To IMG",

    # ID Manager buttons (Stage 4 / 2-column layout)
    "Назначить": "Assign",
    "Создать": "Create",
    "Sync": "Sync",
    "С ID...": "From ID...",
    "Очистить выд.": "Clear Selected",
    "Расширить FLA": "Extend FLA",
    "Из игры": "From Game",
    "Открыть файл": "Open File",

    # Import Map (Build/Load .glb pair)
    "Собрать .glb": "Build .glb",
    "Импорт .glb": "Import .glb",
    "Auto-discover": "Auto-discover",

    # Object INU Tools panel (Stage 6)
    "По имени:": "By name:",
    "Экспортировать как": "Export as",
}
