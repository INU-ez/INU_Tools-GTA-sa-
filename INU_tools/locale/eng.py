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
    "Без LOD": "Skip LOD",
    "Без TXD": "Skip TXD",
    "Без коллизии": "Skip COL",
    "Заменить на DFF": "Replace with DFF",
    "Заменено:": "Replaced:",
    "Выделите fake объекты карты": "Select fake map objects",
    "Импорт плоскостей вместо моделей (быстрый превью карты)": "Import planes instead of models (fast map preview)",
    "Район карты для импорта": "Map region to import",
    "Не найден gta3.img": "gta3.img not found",
    "Не найден IMG архив": "IMG archive not found",
    "Кеш пуст — сначала запустите «Извлечь ресурсы»": "Cache is empty — run «Extract Resources» first",
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
    "Геометрия путей": "Path geometry",
    "Создать или скрыть геометрию визуализации путей":
        "Create or hide path visualisation geometry",
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
    "Очистить ID": "Clear ID",
    "Очистить ID выделенных": "Clear selected IDs",
    "освобождено в пресете:": "freed in preset:",
    "Загружать коллизии из кеша при импорте карты. Нужно для round-trip (импорт части карты → редактирование → экспорт в IMG другой сборки). При выключенном — только DFF геометрия, сцена легче": "Load collisions from cache during map import. Needed for round-trip (import part of map → edit → export to IMG in another build). When off — geometry only, scene stays lighter",
    "Освободить фантомы": "Free phantoms",
    "Освобождено фантомных ID:": "Phantom IDs freed:",
    "Освободить записи пресета, у которых нет соответствующего объекта в сцене": "Free preset entries with no matching scene object",
    "Shared TXD": "Shared TXD",
    "Добавить в IFP": "Merge Into IFP",
    "Неизвестные кости в Action:": "Unknown bones in Action:",
    "неизвестные кости:": "unknown bones:",
    "Проверить round-trip": "Validate round-trip",
    "Начальный индекс": "Start index",
    "0-based индекс первой анимации в отфильтрованном списке. Удобно бить ped.ifp на порции: 0..49 проверил → 50..99 следующим проходом, не забивая сцену сразу всеми 294 клипами": "0-based index of the first animation in the filtered list. Handy for slicing ped.ifp: run 0..49, then 50..99, instead of dumping all 294 clips into the scene at once",
    "Сколько применить": "Count",
    "Максимум анимаций для обработки в этом запуске. 0 = все оставшиеся после start_index": "Maximum animations to process in this run. 0 = all remaining after start_index",
    "диапазон": "range",
    "из": "of",
    "Выберите анимацию в списке": "Pick an animation from the list",
    "Preview ●": "Preview ●",
    "Прорежать ключи": "Decimate keyframes",
    "Формат": "Format",
    "Кодировка IFP-файла на диске. ANP3 — компактный формат GTA SA (int16). ANPK / ANP2 — chunked float32 (GTA III, VC, плюс совместим с SA)": "On-disk IFP encoding. ANP3 — compact GTA SA format (int16). ANPK / ANP2 — chunked float32 (GTA III, VC, also loadable in SA)",
    "Chunked float32 — III, VC, читается и в SA": "Chunked float32 — III, VC, also loaded by SA",
    "Flat int16-compressed — родной формат GTA SA, минимальный размер файла": "Flat int16-compressed — native GTA SA format, smallest file size",
    "Удалять keyframe'ы которые лежат на линейной интерполяции между соседями. Уменьшает размер .ifp без потери качества — первый и последний ключ каждой кости сохраняются всегда": "Drop keyframes that lie on a linear interpolation between neighbours. Reduces .ifp size without quality loss — first and last keyframe of every bone are always preserved",
    "Допуск поворота": "Rotation tolerance",
    "Max-norm tolerance по XYZW quaternion. 1e-3 безопасно — ANP3 квантует rotation c точностью 1/4096 ≈ 2.4e-4, поэтому ниже не имеет смысла": "Max-norm tolerance on XYZW quaternion. 1e-3 is safe — ANP3 quantises rotation at 1/4096 ≈ 2.4e-4, going below that brings no benefit",
    "Допуск позиции": "Translation tolerance",
    "Max-norm tolerance по XYZ translation в DFF-единицах (обычно метры). 1e-3 = около 1 мм — незаметно при обычных масштабах сцены": "Max-norm tolerance on XYZ translation in DFF units (usually metres). 1e-3 ≈ 1 mm — invisible at typical scene scales",
    "с прореживанием": "decimated",
    "прорежено": "decimated",
    "ключей": "keys",
    "Нет анимаций для экспорта": "No animations to export",
    "Нет анимаций для merge": "No animations to merge",
    "Укажите .ifp файл": "Pick an .ifp file",
    "Анимации:": "Animations:",
    "Кости:": "Bones:",
    "Ключи:": "Keyframes:",
    "Макс. отклонение поворота:": "Max rotation delta:",
    "Макс. отклонение позиции:": "Max translation delta:",
    "Макс. отклонение времени:": "Max time delta:",
    "Потеряны анимации:": "Missing animations:",
    "Анимаций с потерянными костями:": "Animations with missing bones:",
    "Несовпадений по числу ключей:": "Keyframe-count mismatches:",
    "Round-trip: OK ✓": "Round-trip: OK ✓",
    "Round-trip: расхождения ⚠": "Round-trip: mismatches ⚠",
    "Только текущая анимация": "Current action only",
    "Имя пакета (оставьте пустым чтобы сохранить имя существующего файла)": "Package name (leave empty to keep the existing file's name)",
    "Экспортировать только активную Action арматуры (Action Editor). Иначе — все Actions с меткой ifp_source плюс активная": "Export only the armature's active Action (Action Editor). Otherwise — all Actions tagged with ifp_source plus the active one",
    "У арматуры нет активной Action — включите опцию «Только текущая» выкл. или присвойте Action": "Armature has no active Action — either disable «Current action only» or assign an Action",
    "заменено": "replaced",
    "Добавить или заменить анимации в существующем IFP-паке.\n\n    Открывает ped.ifp / anim.ifp (или любой другой .ifp), подменяет\n    анимации по имени (case-insensitive) или дописывает в конец, и\n    сохраняет файл обратно. Остальные анимации пака сохраняются.\n    Позволяет обойтись без внешних IFP-редакторов при правке одной\n    анимации в ванильном паке": "Add or replace animations in an existing IFP pack.\n\n    Opens ped.ifp / anim.ifp (or any other .ifp), overwrites animations\n    by name (case-insensitive) or appends them, then saves the file back.\n    Other animations in the pack stay intact. Lets you skip external\n    IFP editors when editing a single animation in a vanilla pack",
    "Писать все текстуры в один общий .txd файл вместо отдельного .txd на каждую модель. Полезно для районов и сборок где множество моделей делят одни и те же текстуры": "Pack all textures into one shared .txd file instead of a separate .txd per model. Handy for districts and builds where many models share the same textures",
    "Имя общего .txd": "Shared .txd name",
    "Имя общего .txd файла без расширения (например 'district' → district.txd)": "Name of the shared .txd file without extension (e.g. 'district' → district.txd)",
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
    # VC Layer System
    "Слои Vertex Color": "Vertex Color Layers",
    "Слои Vertex Color (BETA)": "Vertex Color Layers (BETA)",
    "База (прилайт):": "Base (prelight):",
    "Нет атрибутов прилайта": "No prelight attributes",
    "Слои Day": "Day Layers",
    "Слои Night": "Night Layers",
    "Стек пуст — жми +": "Stack empty — click +",
    "Имя слоя": "Layer name",
    "Видимое имя слоя. Изменение переименует атрибут на меше": "Visible layer name. Editing renames the underlying mesh attribute",
    "Куда композится": "Compose target",
    "Day / Night — в какой стек этот слой вкладывается при flatten": "Day / Night — which stack this layer composes into on flatten",
    "Прозрачность": "Opacity",
    "Какая часть слоя смешивается с тем что под ним": "How much of the layer blends over what's beneath",
    "Режим": "Mode",
    "Как этот слой смешивается со стеком ниже": "How this layer blends with the stack below",
    "Виден": "Visible",
    "Выключенный слой исключается из flatten (alpha → 0)": "Hidden layer is excluded from flatten (alpha → 0)",
    "Заблокирован": "Locked",
    "Запрещает рисование на слое. Слайдеры остаются доступны": "Disables painting on the layer. Sliders remain editable",
    "Выделен": "Selected",
    "Включить в групповое редактирование (multi-edit slider'ы)": "Include in multi-edit slider operations",
    "Яркость до": "Brightness pre",
    "Яркость после": "Brightness post",
    "Контраст до": "Contrast pre",
    "Контраст после": "Contrast post",
    "Сдвиг яркости пикселей этого слоя ДО блендинга": "Brightness offset applied to this layer's pixels BEFORE blending",
    "Контраст пикселей этого слоя ДО блендинга": "Contrast applied to this layer's pixels BEFORE blending",
    "Лимит {n} слоёв для стека {scope} достигнут": "Limit of {n} layers for {scope} stack reached",
    "Слой с именем {} уже есть": "A layer named {} already exists",
    "Атрибут не найден": "Attribute not found",
    "Не VCL-атрибут": "Not a VCL attribute",
    "Это уже VCL-слой": "Already a VCL layer",
    "Атрибут «{}» уже есть — переименуйте слой перед promote": "Attribute «{}» already exists — rename the layer before promoting",
    "Атрибут «{}» уже есть": "Attribute «{}» already exists",
    "Стек": "Stack",
    "Редактируем Day-стек": "Editing Day stack",
    "Редактируем Night-стек": "Editing Night stack",
    "Multi-edit": "Multi-edit",
    "Как групповые слайдеры применяются к выделенным слоям": "How group sliders are applied to selected layers",
    "Absolute": "Absolute",
    "Relative": "Relative",
    "Все выделенные получают одинаковое значение": "All selected get the same value",
    "Все выделенные сдвигаются на одну дельту от текущего": "All selected shift by the same delta from current",
    "Выделенные слои ({}):": "Selected layers ({}):",
    "(групповые слайдеры — Фаза 2)": "(group sliders — Phase 2)",
    "Рисовать": "Paint",
    "→ База": "→ Base",
    "Live preview": "Live preview",
    "Дополнительные атрибуты:": "Additional attributes:",
    "Авто-композиция стека при изменении любого слайдера или мазке кистью": "Auto-recompose stack on any slider change or brush stroke",
    "Композит пуст — добавь хотя бы один слой": "Composite is empty — add at least one layer",
    "Атрибут «{}» не существует": "Attribute «{}» does not exist",
    "Live Preview выключен — нечего обновлять": "Live Preview is off — nothing to refresh",
    "Day/Night показывают композит — рисуй на слое": "Day/Night show the composite — paint on a layer",
    "BETA": "BETA",
    "IMG: нет результатов экспорта": "IMG: no export results",
    "Будут перекрашены": "Will be recoloured",
    "Перекрасить выделенные…": "Recolor Selected…",
    "Цвет": "Color",
    "Нет выделенных слоёв": "No selected layers",

    "Менеджер текстур": "Bitmaps Manager",
    "Сканировать": "Scan",
    "Пропущено": "Missing",
    "Найти в папке…": "Resolve From Folder…",
    "Скопировать в папку…": "Copy Used To Folder…",
    "Найти дубликаты": "Find Duplicates",
    "Найти неиспользуемые": "Find Unused",
    "Удалить неиспользуемые…": "Remove Unused…",
    "Неисп.": "Unused",
    "Будет удалено:": "Will be removed:",
    "Текстуры": "Textures",
    "Материалы": "Materials",
    "пропущены": "skipped",
    "Также удалить неиспользуемые материалы": "Also remove unused materials",
    "Удалить также материалы, не назначенные ни на один меш-слот": "Also remove materials not assigned to any mesh slot",
    "use_fake_user-помеченные пропускаются": "use_fake_user-flagged are skipped",

    # Unified Export (Stage 3)
    "Экспорт:": "Export:",
    "Экспорт...": "Exporting...",
    "INU Export...": "INU Export...",
    "INU Export:": "INU Export:",
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

    # IMG export progress
    "Экспорт в IMG:": "Export to IMG:",
    "Экспорт в IMG...": "Exporting to IMG...",

    # Build Map .glb — no auto-import
    "Собрано:": "Built:",
    "инстансов": "instances",

    # Direct map import
    "Import Map (прямой)": "Import Map (direct)",

    # Profiler
    "Профайлер": "Profiler",
    "Замерять время операций и записывать отчёт в .inu_cache/_profile.log. Включай только для отладки — добавляет небольшой overhead на каждый шаг":
        "Time each stage and write a report to .inu_cache/_profile.log. Enable only for debugging — adds a small overhead per step",
    "Профайлер (debug timings)": "Profiler (debug timings)",

    # ── 1.6.6 — Map Export split modes ──────────────────────────────────
    "Разбиение": "Split",
    "Как разбить выделение на отдельные district'ы при экспорте":
        "How to split the selection into separate districts during export",
    "Без разбиения": "No split",
    "Один общий district, все DFF в корне target_dir. base_name используется для имён IDE/IPL/COL/TXD":
        "One shared district, all DFFs in the target directory root. base_name is used for IDE/IPL/COL/TXD filenames",
    "XY-сетка": "XY grid",
    "Биннить DFF по XY-координате origin'а на ячейки cell_size метров. Каждая непустая ячейка получает подпапку <base>_x<cx>_y<cy> со своими IDE/IPL/COL/TXD":
        "Bin DFFs by their XY origin into cell_size-meter cells. Each non-empty cell gets a <base>_x<cx>_y<cy> subdirectory with its own IDE/IPL/COL/TXD",
    "По коллекциям": "By collection",
    "Биннить DFF по имени верхней (top-level) коллекции, в которой объект лежит. Имя коллекции становится именем district'а — идеально для round-trip с Group-by-IPL импортом (vegasn_stream0 в Blender → vegasn_stream0.ipl на выходе)":
        "Bin DFFs by the name of the top-level collection they live in. The collection name becomes the district name — ideal for round-trip with Group-by-IPL import (vegasn_stream0 in Blender → vegasn_stream0.ipl on output)",
    "Размер ячейки (м)": "Cell size (m)",
    "Сторона квадратной ячейки в метрах для разбиения по XY-сетке. 256 м соответствует ванильному радиусу стриминга. Уменьшай для более мелких чанков, увеличивай если районов получается слишком много":
        "Side of the square cell in meters for XY-grid splitting. 256 m matches the vanilla streaming radius. Decrease for finer chunks, increase if you end up with too many districts",

    # ── 1.6.6 — Vehicle damage variants ─────────────────────────────────
    "Damage variants": "Damage variants",
    "Добавить _dam вариант": "Add _dam variant",
    "Состояние повреждений": "Damage state",
    "Состояние": "State",
    "Damaged": "Damaged",
    "Оба": "Both",
    "Показать целые меши, скрыть _dam": "Show OK meshes, hide _dam",
    "Показать повреждённые _dam меши, скрыть _ok": "Show damaged _dam meshes, hide _ok",
    "Показать оба варианта одновременно": "Show both variants simultaneously",
    "Проверить _ok/_dam пары": "Check _ok/_dam pairs",
    "Создать _dam": "Create _dam",
    "Dam": "Dam",
    "Проверить пары": "Check pairs",
    "Показать:": "Show:",
    "Создан": "Created",
    "Пар": "Pairs",
    "одиночные _ok": "lonely _ok",
    "одиночные _dam": "lonely _dam",
    "детали в системной консоли": "details in system console",

    # ── 1.6.6 — Map import: group by IPL ────────────────────────────────
    "Группировать по IPL": "Group by IPL",
    "Создавать отдельную коллекцию на каждый IPL-файл (Map_LAn, Map_LAs, Map_SF…) вместо одиночных Map_DFF_Far/Mid/Near. Удобно для скрытия районов целиком и для совместного редактирования карты. LOD-меши идут в коллекцию своего IPL вместе с обычными мешами":
        "Create a separate collection per IPL file (Map_LAn, Map_LAs, Map_SF…) instead of the unified Map_DFF_Far/Mid/Near buckets. Handy for hiding whole districts and for co-op map editing. LOD meshes go into their IPL's collection alongside regular meshes",

    # ── 1.6.6 — Map Export modal progress ───────────────────────────────
    "Map Export: подготовка...": "Map Export: preparing...",
    "Ошибка экспорта": "Export error",

    # ── 1.6.6 — Vehicle panel ───────────────────────────────────────────
    "Машины": "Vehicles",
    "Целевые коллекции": "Target collections",
    "Целевые коллекции:": "Target collections:",
    "Какие top-level коллекции экспортировать. Авто-инициализация по выделению в outliner; если не угадало — отметь галочками вручную. Имеет смысл вместе с режимом «По коллекциям»":
        "Which top-level collections to export. Auto-initialised from the outliner selection; if it didn't catch them, tick the boxes manually. Most useful with «By collection» split mode",
    "(пусто = выделение из outliner на момент нажатия)":
        "(empty = outliner selection captured when button was pressed)",
    "Export Map": "Export Map",

    # ── 1.6.6 — LOD round-trip + COL library property ──────────────────
    "COL Library": "COL Library",
    "Имя .col-библиотеки в которой хранится коллизия модели. Заполняется автоматически при Map Import (= имя исходного .col файла). При Map Export DFF группируются в одну .col-библиотеку по совпадающему col_name. Пусто → fallback на txd_name, затем на имя модели":
        "Name of the .col library this model's collision belongs to. Auto-populated on Map Import (= source .col filename). On Map Export, DFFs sharing a col_name are merged into one .col library. Empty → falls back to txd_name, then to the model's own name",
    "LOD partner": "LOD partner",
    "LOD-модель этой DFF — заполняется автоматически при Map Import из IPL lod_index. При Map Export пересчитывается в lod_index = позицию LOD-инстанса в выходном IPL. Пусто = модель не имеет LOD":
        "LOD model paired with this DFF — auto-populated on Map Import from the source IPL's lod_index. On Map Export it is converted back into a lod_index = position of the LOD instance in the output IPL. Empty = no LOD partner",

    # ── 1.7.0 — IK Rig, Animated Map Object, Frame Hierarchy, Paintjob,
    #          Profile system, 2DFX UX, Texture Manager dropdowns ──
    # IK Rig
    "Add IK Rig": "Add IK Rig",
    "Bake & Clear IK": "Bake & Clear IK",
    "IK Rig": "IK Rig",
    "Ground plane создан": "Ground plane created",
    "Цвет IK-контроллов": "IK control colour",
    "Форма IK-эмпти": "IK empty shape",
    "Какой примитив рисовать на IK-target и pole": "Which primitive to draw at IK target and pole",
    "Множитель размера всех IK-контролов ": "Size multiplier for all IK controls ",
    "Смещение куба руки/ноги": "Hand/foot cube offset",
    "Пол": "Floor",
    "Коллизия": "Collision",
    "Показывать кубы запястий и ступней ": "Show wrist and ankle cubes ",
    "Показывать кубы-маркеры на локтях и ": "Show elbow/knee marker cubes on ",
    "Показывать кубы головы, верхнего торса ": "Show head and upper-torso cubes ",
    "Показывать корневой куб (мастер-контроль ": "Show root cube (master control ",
    "Руки/ноги": "Hands/feet",
    "Локти/колени": "Elbows/knees",
    "Голова/торс": "Head/torso",
    "Голова/торс/плечи": "Head/torso/shoulders",
    "Корень": "Root",
    "Настройки пола, коллизии, цвета IK, плюс ": "Floor, collision and IK colour settings, plus ",
    "Дополнительно": "Advanced",
    "Дополнить": "Append",

    # Animated Map Object
    "Animated Map Object": "Animated Map Object",
    "Animated Map Object — мельницы, краны, флюгеры": "Animated Map Object — windmills, cranes, weather vanes",
    "Animated object готов к экспорту": "Animated object ready for export",
    "Animated rig готов": "Animated rig ready",
    "Setup rig": "Setup rig",
    "Validate": "Validate",
    "DFF+IFP+IDE": "DFF+IFP+IDE",
    "Дописать IDE entry": "Append IDE entry",
    "Добавить anim-запись в IDE-файл, заданный в Scene → INU Tools → IDE Path": "Add an anim entry to the IDE file set in Scene → INU Tools → IDE Path",
    "IDE path не задан — anim-запись пропущена": "IDE path is empty — anim entry skipped",
    "Имя файлов без расширения (например 'mill')": "File name without extension (e.g. 'mill')",
    "Куда положить .dff и .ifp": "Where to put .dff and .ifp",
    "Имя action": "Action name",
    "Имя IFP": "IFP name",
    "IFP файл": "IFP file",
    "Формат IFP": "IFP format",
    "Режим IFP": "IFP mode",
    "Перезаписать файл — старые анимации удаляются": "Overwrite file — existing animations are wiped",
    "Подгрузить существующий, добавить новые анимации, ": "Append new animations to the existing file, ",
    "Подгрузить существующий, заменить ТОЛЬКО анимации ": "Load existing, replace ONLY the animations ",
    "Новый": "New",
    "перезаписываю": "overwriting",
    "пропущено (уже есть)": "skipped (already present)",
    "анимаций": "animations",
    "Имя кости": "Bone name",
    "Все вершины меша получат weight=1.0 на эту кость": "All mesh vertices get weight=1.0 on this bone",
    "Ось": "Axis",
    "Ось вращения": "Rotation axis",
    "Оборотов за цикл": "Turns per cycle",
    "Длительность (кадров)": "Duration (frames)",
    "В обратную сторону": "Reverse direction",
    "Auto": "Auto",
    "Вручную": "Manual",
    "Manual режим — keyframes управляются вручную": "Manual mode — keyframes are managed by hand",
    "Переключение в Auto перезапишет твои ключи": "Switching to Auto will overwrite your keyframes",
    "Цикл точно зацикливается (целое число оборотов)": "Loop is exactly cyclic (integer turns count)",
    "об/сек при FPS": "rev/s at FPS",
    "оборотов/сек при FPS": "turns/s at FPS",
    "Что экспортировать:": "What to export:",
    "Объекты": "Objects",
    "Персонажи": "Characters",
    "Раздел панели Анимации": "Animations panel tab",
    "Выдели MESH и нажми Setup rig": "Select a MESH and press Setup rig",
    "Выделите MESH": "Select a MESH",
    "Выделите MESH или ARMATURE": "Select a MESH or ARMATURE",
    "Активный объект — не MESH и не ARMATURE": "Active object is not MESH or ARMATURE",
    "На MESH нет Armature modifier": "MESH has no Armature modifier",
    "Armature modifier указывает на другой скелет": "Armature modifier points to a different skeleton",
    "В скелете 0 костей": "Skeleton has 0 bones",
    "Не нашли пару MESH+ARMATURE — запустите Validate": "MESH+ARMATURE pair not found — run Validate",
    "Кости без vertex group:": "Bones without vertex group:",
    "Не найдена кость": "Bone not found",
    "Не найдены кости: ": "Bones not found: ",
    "К armature не привязан Action": "No Action linked to armature",
    "Нет Action на armature — IFP будет пустой": "No Action on armature — IFP will be empty",
    "Нет Armature — animated object без скелета не работает": "No Armature — animated object can't work without a skeleton",
    "Нет MESH": "No MESH",
    "В Action меньше 2 keyframe — анимации нет": "Action has fewer than 2 keyframes — no animation",
    "В action нет ключей — IFP не записан": "Action has no keyframes — IFP wasn't written",

    # Frame Hierarchy editor
    "Иерархия фреймов": "Frame hierarchy",
    "Rename": "Rename",
    "Set Parent": "Set Parent",
    "Unparent": "Unparent",
    "Validate Vehicle": "Validate Vehicle",
    "Validate Ped": "Validate Ped",
    "Зеркало L↔R": "Mirror L↔R",
    "Новое имя фрейма (точное соответствие требуется для машин и педов)": "New frame name (exact match required for vehicles and peds)",
    "сняли parent с": "unparented",
    "зеркально создано": "mirrored",
    "иерархия OK": "hierarchy OK",
    "parent": "parent",

    # Paintjob
    "Paintjob (Pay'n'Spray):": "Paintjob (Pay'n'Spray):",
    "Раскраска 1": "Paint 1",
    "Раскраска 2": "Paint 2",
    "Все paintjob материалы OK": "All paintjob materials OK",
    "Paintjob проблем": "Paintjob issues",
    "Paintjob'ов в сцене нет": "No paintjobs in the scene",
    "заполнен только Paintjob 1 — нужны оба": "only Paintjob 1 is set — both are required",
    "заполнен только Paintjob 2 — нужны оба": "only Paintjob 2 is set — both are required",
    "Нужны обе альтернативы (1 и 2)": "Both alternatives (1 and 2) are required",

    # Profile system
    "Профиль": "Profile",
    "Настройки": "Settings",
    "Раскройте нужный инструмент:": "Expand the tool you need:",

    # Prelight panel polish
    "Скопировать:": "Copy:",

    # Adaptive map auto-split (1.7.0)
    "Адаптивная сетка": "Adaptive grid",
    "Quadtree-разбиение по плотности: ячейка делится 2×2 пока в ней больше max_per_cell DFF. Плотные районы получают мелкие ячейки, разреженные остаются одной большой. Гарантирует число DFF на ячейку вместо равномерного пространственного разбиения. Имена подпапок: <base>_q<path>, где path — путь по квадрантам (0=SW, 1=SE, 2=NW, 3=NE)":
        "Density-driven quadtree subdivision: a cell splits 2×2 whenever it holds more than max_per_cell DFFs. Dense regions get small cells, sparse regions stay as one big cell. Guarantees per-cell DFF count instead of uniform spatial sub-division. Subdirectory naming: <base>_q<path>, where path is the quadrant path (0=SW, 1=SE, 2=NW, 3=NE)",
    "Макс. DFF на ячейку": "Max DFFs per cell",
    "Целевой потолок DFF в одной адаптивной ячейке. Когда число превышено — ячейка делится на 4. Меньше = больше мелких ячеек (тоньше streaming, но больше IPL-файлов). Больше = крупные ячейки. Vanilla SA streaming-радиус хорошо работает с ~150-300 DFF на IPL":
        "Target ceiling for DFFs in one adaptive cell. When exceeded the cell is split into 4. Lower = more small cells (finer streaming but more IPL files). Higher = bigger cells. Vanilla SA streaming radius works well with ~150-300 DFFs per IPL",
    "Мин. размер ячейки (м)": "Min cell size (m)",
    "Минимальная сторона ячейки для адаптивной сетки — нижняя граница рекурсии. Защищает от бесконечного деления когда много DFF разделяют одну XY-точку (вертикально стопкой, как небоскрёбы). При достижении этого предела ячейка остаётся, даже если в ней больше max_per_cell":
        "Minimum cell side length for the adaptive grid — recursion floor. Protects against infinite splitting when many DFFs share one XY point (stacked vertical like skyscrapers). On reaching this floor the cell is kept even if it still holds more than max_per_cell",

    # 2DFX panel — collapsible sections, semantic flag groups
    "Свойства света": "Light properties",
    "Поведение": "Behaviour",
    "Тень": "Shadow",
    "Флаги": "Flags",
    "Создать эффект": "Create effect",
    "Light — уличные фонари, неон, corona\nParticle — дым, огонь, частицы\nPed Attractor — точки притяжения NPC (банкомат, скамейка)\nSun Glare — блик солнца на поверхности":
        "Light — street lights, neon, corona\nParticle — smoke, fire, particles\nPed Attractor — NPC attractor points (ATM, bench)\nSun Glare — sun glare on surfaces",
    "Видимость:": "Visibility:",
    "Эффекты короны:": "Corona effects:",
    "Мерцание:": "Blinking:",
    "Доп.:": "Misc.:",
    "Множитель": "Multiplier",
    "Дистанция": "Distance",

    # Particle effect properties
    "Angle min": "Angle min",
    "Angle max": "Angle max",
    "Bounce": "Bounce",
    "Box": "Box",
    "Cull dist": "Cull dist",
    "Force": "Force",
    "Friction": "Friction",
    "Jitter": "Jitter",
    "Length": "Length",
    "Life bias": "Life bias",
    "Mid time": "Mid time",
    "Middle": "Middle",
    "Noise": "Noise",
    "Offset": "Offset",
    "Play mode": "Play mode",
    "Preview": "Preview",
    "Rate": "Rate",
    "Rot min": "Rot min",
    "Rot max": "Rot max",
    "RotSpd min": "RotSpd min",
    "RotSpd max": "RotSpd max",
    "Speed bias": "Speed bias",
    "SpeedMult": "SpeedMult",
    "Wind": "Wind",
    "Draw distance": "Draw distance",

    # DFF Flags / pipeline tooltips
    "Day": "Day",
    "Night": "Night",
    "Pipeline здания с day/night vertex colors (RSPIPE_PC_CustomBuildingDN). Движок плавно смешивает дневной и ночной слои vertex colors по игровому времени. Требует ДВА Color Attribute слоя (Day + Night) на меше. Mesh-флаги Day/Night здесь не нужны — переход делает pipeline через VC":
        "Building day/night vertex-colour pipeline (RSPIPE_PC_CustomBuildingDN). The engine smoothly blends a day and a night vertex-colour layer by in-game time. Requires TWO Color Attribute layers (Day + Night) on the mesh. Mesh Day/Night flags are NOT needed here — the pipeline does the transition via VC",

    # Auto-TXD picker help text
    "Как ищется TXD:": "How TXD is matched:",
    "1. <имя_dff>.txd в той же папке": "1. <dff_name>.txd in the same folder",
    "2. .txd с покрытием ≥50% текстур DFF": "2. .txd that covers ≥50% of DFF textures",
    "3. Единственный .txd в папке": "3. The only .txd in the folder",
    "   (выбирается с макс. покрытием,": "   (the one with the highest coverage,",
    "    меньший по размеру при равенстве)": "    smaller in size on a tie)",
    "Иначе — warning, ничего не грузится": "Otherwise a warning is shown and nothing is loaded",
    "TXD не найден": "TXD not found",
    "не найден ни по имени": "not found by name",
    "и нет .txd с подходящими текстурами": "and no .txd with matching textures",
    "ни по покрытию ≥50% текстур в": "nor by ≥50% texture coverage in",
    "доп. папка": "extra folder",
    "Укажите существующую папку": "Enter an existing folder",

    # IDE / Map workflow
    "Model ID": "Model ID",
    "Model ID = 0 — IDE entry пропущена": "Model ID = 0 — IDE entry skipped",
    "Model ID = 0 — задай в Object Properties → ": "Model ID = 0 — set it in Object Properties → ",
    "Имя TXD для IDE entry (обычно совпадает с base_name)": "TXD name for the IDE entry (usually matches base_name)",
    "Базовое имя": "Base name",
    "Базовое имя для общего TXD (без .txd)": "Base name for the shared TXD (without .txd)",
    "Базовое имя не может быть пустым": "Base name can't be empty",
    "Имя не может быть пустым": "Name can't be empty",
    "Имя": "Name",
    "Сначала сохраните .blend": "Save the .blend first",
    "Кеш пуст — будут расставлены только Empty по ": "Cache is empty — only Empty placeholders will be spawned at ",
    "Кеш пуст — карта без моделей": "Cache is empty — map without models",
    "Не найден файл: ": "File not found: ",
    "Не удалось записать отчёт:": "Failed to write report:",
    "Ничего не найдено": "Nothing found",
    "Только выделенное": "Selected only",
    "Используются:": "In use:",
    "Свободные ID:": "Free IDs:",

    # Texture Manager dropdowns
    "Светофор": "Traffic light",

    # Misc tooltips/help
    "TXD": "TXD",
    "TXD не будет загружаться автоматически": "TXD won't be loaded automatically",
    "(см. System Console)": "(see System Console)",
    "см. System Console": "see System Console",
    "...": "...",
    "Action Editor / Pose Mode": "Action Editor / Pose Mode",
    "Обновить совпадения": "Refresh matches",
    "Создать ID": "Create ID",
    "Связи: ON": "Links: ON",
    "Связи: OFF": "Links: OFF",
    "All → Папка": "All → Folder",
    "All → IMG": "All → IMG",
    "RW-эффекты материала: env map, bump, specular, reflection, dual texture, UV anim":
        "RW material effects: env map, bump, specular, reflection, dual texture, UV anim",
    "Пресеты материала и сводка активных эффектов": "Material presets and active-effect summary",
    "IFP импорт/экспорт, применение анимации к скелету, IK Rig": "IFP import/export, applying animation to a skeleton, IK Rig",
    "Показать сервисные кнопки": "Show service buttons",
    "Ошибок": "Errors",
    "Предупреждений": "Warnings",
    "предупреждений": "warnings",
    "моделей": "models",
    "текстур": "textures",
    "OFF (по умолчанию): каждая DFF получает свой отдельный <model>.col файл — соответствует ванильному SA где у большинства моделей коллизии в собственных файлах.\nON: все коллизии группируются в .col-библиотеки по inu.col_name (vegasN.col, LAs.col, …). Полезно когда есть осознанная shared collision на много моделей":
        "OFF (default): each DFF gets its own <model>.col file — matches vanilla SA where most models keep collision in standalone files.\nON: collisions are grouped into .col libraries by inu.col_name (vegasN.col, LAs.col, …). Useful when shared collision across many models is intentional",
    "Помечает меш как объёмный луч света для плагина SA_Light.asi.\nУстанавливает material color = (254,254,254,254) — этот маркер плагин ищет во время рендера.\n\nТРЕБУЕТ SA_Light.asi в корне GTA SA. Без плагина меш будет рендериться как обычный полупрозрачный объект с жёстким срезом alpha.\n\nДля использования:\n1. Собери меш-конус/куб формой луча\n2. Покрась vertex colors как хочешь (любые значения alpha)\n3. Включи этот флаг + Set Material Alpha выключи\n4. Экспорт → плагин автоматически включит плавный alpha blend на этом меше":
        "Marks the mesh as a volumetric light beam for the SA_Light.asi plugin.\nSets material color = (254,254,254,254) — the marker the plugin scans for at render time.\n\nREQUIRES SA_Light.asi in the GTA SA root. Without the plugin the mesh renders as a regular semi-transparent object with hard alpha cutoff.\n\nUsage:\n1. Build a cone/cube mesh shaped like the beam\n2. Paint vertex colors as you wish (any alpha values)\n3. Enable this flag + disable Set Material Alpha\n4. Export → the plugin automatically applies smooth alpha blend on this mesh",
    "Автоматически ставить material alpha = 254 при наличии vertex alpha < 255.\nНужно для стандартных прозрачных мешей (стёкла, дым). Выключи если материал должен остаться opaque":
        "Automatically sets material alpha = 254 when any vertex alpha < 255.\nUseful for standard transparent meshes (glass, smoke). Disable if the material must stay opaque",
    "Day — дневные вертексные цвета\nNight — ночные вертексные цвета\nDay/Night — создать оба атрибута\n+/- — добавить или удалить атрибут\nSave Materials — сохранить материалы (для Itera Tools)\nRestore — восстановить сохранённые материалы":
        "Day — daytime vertex colours\nNight — nighttime vertex colours\nDay/Night — create both attributes\n+/- — add or remove an attribute\nSave Materials — save materials (for Itera Tools)\nRestore — restore saved materials",
    "Гамма-коррекция vertex colors\n1.0 — без изменений\n< 1.0 — светлее (тени)\n> 1.0 — темнее (тени)":
        "Gamma correction for vertex colors\n1.0 — unchanged\n< 1.0 — brighter (shadows)\n> 1.0 — darker (shadows)",
    "Контраст vertex colors\n1.0 — без изменений\n< 1.0 — меньше контраст\n> 1.0 — больше контраст":
        "Contrast of vertex colors\n1.0 — unchanged\n< 1.0 — less contrast\n> 1.0 — more contrast",
    "Сглаживание vertex colors между соседними вершинами\nIterations — количество проходов\nFactor — сила сглаживания (0-1)":
        "Vertex-color smoothing between adjacent vertices\nIterations — number of passes\nFactor — smoothing strength (0-1)",
    "Яркость vertex colors\n0.0 — без изменений\n> 0 — светлее\n< 0 — темнее":
        "Vertex-color brightness\n0.0 — unchanged\n> 0 — brighter\n< 0 — darker",
    "V — смещение яркости vertex colors\nПоложительное значение — светлее\nОтрицательное — темнее":
        "V — vertex-color brightness offset\nPositive — brighter\nNegative — darker",
    "Тени — включить расчёт теней при запекании\nЗапечь — быстрое запекание без теней\nС тенями — запекание с raycast тенями (медленнее, но точнее)":
        "Shadows — enable shadow calculation during baking\nBake — fast baking without shadows\nWith Shadows — raycast-shadow baking (slower but more accurate)",
    "Диапазон дневного освещения для COL материалов\nMin/Max — значения от 0 до 15\nЯркость vertex colors конвертируется в этот диапазон":
        "Daytime light range for COL materials\nMin/Max — values from 0 to 15\nVertex-color brightness is mapped into this range",
    "Диапазон ночного освещения для COL материалов\nMin/Max — значения от 0 до 15\nИспользует Night color attribute если есть":
        "Nighttime light range for COL materials\nMin/Max — values from 0 to 15\nUses the Night color attribute if present",
    "COL Surface Type — тип физической поверхности и Day/Night Light":
        "COL Surface Type — physical surface type and Day/Night Light",

    # Validate Scene + COL Import + Onboarding strings (added 2026-05-02)
    "Action не найден": "Action not found",
    "COL Import отменён": "COL Import cancelled",
    "COL Import: подготовка...": "COL Import: preparing...",
    "Fastman92 Limit Adjuster: 12-я колонка `realInterior` в IPL inst. Обычная SA читает только 11 колонок — это поле игнорируется без FLA. Пусто (0) = не использовать. Включить запись 12-й колонки можно в Map Export → FLA Extended IPL":
        "Fastman92 Limit Adjuster: 12th `realInterior` column in IPL inst. Vanilla SA reads only 11 columns — this field is ignored without FLA. Empty (0) = not used. Enable 12th column writing in Map Export → FLA Extended IPL",
    "Modulate Color снят": "Modulate Color disabled",
    "Rebuild Archive в IMG-туле — иначе игра подтянет старую запись":
        "Rebuild Archive in IMG tool — otherwise game keeps the old entry",
    "Имя Action содержит спецсимволы — IDE entry может не сработать":
        "Action name contains special characters — IDE entry may not work",
    "Материал без носителя": "Material without owner",
    "Материал не найден": "Material not found",
    "Не выбран ни один .col файл": "No .col file selected",
    "Не удалось удалить": "Failed to delete",
    "Нормализовано ключей": "Keyframes normalised",
    "Нормализовать": "Normalise",
    "Объект вне View Layer": "Object outside View Layer",
    "Объект не найден": "Object not found",
    "Открыть полный changelog на GitHub": "Open full changelog on GitHub",
    "Ошибка импорта COL": "COL import error",
    "Перейти": "Go to",
    "Проверить сцену": "Validate scene",
    "Проверка перед экспортом": "Pre-export check",
    "Русский": "Russian",
    "Снять": "Disable",
    "Сцена готова к экспорту — проблем не найдено":
        "Scene ready to export — no problems found",
    "Удалена Action": "Action deleted",
    "Что делать если такой .ifp уже существует на диске":
        "What to do if such .ifp already exists on disk",
    "Экспорт пройдёт OK, замечаний": "Export will proceed OK, notes",
    "включи коллекцию в outliner": "enable collection in outliner",
    "выбери armature и повтори": "pick armature and retry",
    "нет основной текстуры — paintjob не к чему привязать":
        "no base texture — paintjob has nothing to bind to",
    "объект(ов)": "object(s)",
    "с ошибкой": "with error",
    "файлов": "files",
    "из": "of",
    "Docs": "Docs",
    "Issues": "Issues",
    "Только SAMP": "SAMP only",
    "Блокировать Map Export при SAMP-предупреждениях":
        "Block Map Export on SAMP warnings",
    "FLA: real_interior": "FLA: real_interior",
    "Записать 12-ю колонку realInterior в каждой inst-строке IPL. Fastman92 Limit Adjuster читает её, vanilla SA молча игнорирует. Значение берётся из obj.inu.real_interior":
        "Write the 12th realInterior column in each IPL inst row. Fastman92 Limit Adjuster reads it, vanilla SA silently ignores. Value is taken from obj.inu.real_interior",

    # Profile editor popup hints
    "Взято:": "Picked:",
    "клик на другую = переместить сюда": "click another = move here",
    "Клик на название = взять, потом клик на другую = поставить":
        "Click the name = pick up, then click another = drop here",

    # Validate Scene category labels
    "Кватернионы": "Quaternions",
    "Modulate Color": "Modulate Color",
    "Пары _ok / _dam": "_ok / _dam pairs",
    "Сирые LOD / COL": "Orphan LOD / COL",
    "Непривязанный 2DFX": "Unattached 2DFX",
    "Дубликаты model_id": "Duplicate model_id",
    "Пустые меши": "Empty meshes",
    "Большие меши": "Large meshes",
    "Материал без текстуры": "Material without texture",
    "Суффиксы / префиксы": "Suffixes / prefixes",
    "Scale объектов": "Object scale",

    # Validate Scene — static issue messages
    "заполнен только Paintjob 2 — нужны оба":
        "only Paintjob 2 filled — both required",
    "заполнен только Paintjob 1 — нужны оба":
        "only Paintjob 1 filled — both required",
    "Modulate Color на меше с vertex colors — может flicker":
        "Modulate Color on mesh with vertex colors — may flicker",
    "LOD без main DFF — engine не сможет переключиться между ближним и дальним LOD":
        "LOD without a main DFF — the engine can't switch between near/far LODs",
    "COL без main DFF — коллизия не привязана к модели":
        "COL without a main DFF — collision is not linked to a model",
    "меш с 0 вершин — экспортируется как пустой атомик":
        "mesh with 0 vertices — exports as an empty atomic",
    "материал без image texture — pipeline скорее всего ожидает базовую":
        "material without image texture — pipeline likely expects a base one",
    "флаг Light Beam ASI включён, но SA_Light.asi не найден в game root — плагин не активируется":
        "Light Beam ASI flag is set but SA_Light.asi not found in game root — plugin won't activate",
    "нет парного _dam": "no paired _dam",
    "нет парного _ok": "no paired _ok",

    # Validate Scene — interpolated message templates
    "{count} ненормированных ключей (экспорт чинит сам, но preview прыгает)":
        "{count} non-unit keyframes (export auto-normalises, but preview stutters)",
    "2DFX не привязан к MESH (parent: {parent}) — не попадёт в DFF":
        "2DFX not parented to a MESH (parent: {parent}) — won't go into the DFF",
    "model_id={mid} занят {count} разными моделями: {names}":
        "model_id={mid} is used by {count} different models: {names}",
    "{count} вершин — лимит атомика 65535, возможно стоит разрезать":
        "{count} vertices — atomic limit is 65535, consider splitting",
    "имя содержит '{combo}' — лишний суффикс рядом с {kind}":
        "name contains '{combo}' — extra suffix next to {kind}",
    "имя оканчивается на '{alt}', но настройка ожидает '{sfx}'":
        "name ends with '{alt}' but settings expect '{sfx}'",
    "отрицательный scale ({sx:.2f}, {sy:.2f}, {sz:.2f}) — нормали вывернутся, faces могут стать невидимы":
        "negative scale ({sx:.2f}, {sy:.2f}, {sz:.2f}) — normals flip, faces may become invisible",
    "non-uniform scale ({sx:.2f}, {sy:.2f}, {sz:.2f}) — перед экспортом сделай Ctrl+A → All Transforms":
        "non-uniform scale ({sx:.2f}, {sy:.2f}, {sz:.2f}) — Ctrl+A → All Transforms before export",

    # Validate Scene — fix button label + new fix operator strings
    "Исправить": "Fix",
    "Не нашёл несоответствия суффикса для этого объекта":
        "No suffix mismatch found for this object",

    # ── v1.9.0 ──────────────────────────────────────────────────────
    # File Scanner / Binary linter
    "Скан файлов": "File Scanner",
    "Сканировать": "Scan",
    "Что это значит:": "What it means:",
    "Открыть в Проводнике": "Reveal in Explorer",
    "Сохранить отчёт:": "Save report:",
    "Сохранить .txt": "Save .txt",
    "Список пуст — запустите скан": "List empty — run a scan",
    "Скан завершён": "Scan complete",
    "Скан завершён: проблем не найдено":
        "Scan complete: no issues found",
    "Включите хотя бы один тип файла (DFF/COL/TXD)":
        "Enable at least one file type (DFF/COL/TXD)",
    "Укажите существующую папку": "Pick an existing folder",
    "Нет результатов для сохранения — сначала запустите скан":
        "No results to save — run a scan first",
    "Сцена не сохранена — сохраните .blend или выберите другую папку для отчёта":
        "Scene not saved — save the .blend or choose another report folder",
    "Папка скана не задана — выберите .blend или свою папку":
        "Scan folder not set — choose .blend or a custom folder",
    "Своя папка для отчёта не задана или не существует":
        "Custom report folder not set or doesn't exist",
    "Неизвестный target для отчёта": "Unknown report target",
    "Нет выбранной строки": "No row selected",
    "Файл не найден:": "File not found:",
    "Отчёт сохранён:": "Report saved:",
    "Сцена не сохранена!": "Scene not saved!",
    "Сцена не сохранена": "Scene not saved",

    # Asset Library / Build Library
    "Собрать Asset Library": "Build Asset Library",
    "Извлечь ресурсы": "Extract resources",
    "Корневая папка GTA SA": "GTA SA root folder",
    "Регион": "Region",
    "Параметры": "Parameters",
    "Размер превью (px)": "Preview size (px)",
    "Перегенерировать превью": "Regenerate previews",
    "Без превьюшек (быстрее, но без миниатюр)":
        "Skip previews (faster, but no thumbnails)",
    "Пропускать готовые .blend": "Skip existing .blend files",
    "Сборка библиотеки...": "Building library...",
    "Сканирование кеша...": "Scanning cache...",
    "Чтение IDE файлов...": "Reading IDE files...",
    "Перегенерация превью...": "Regenerating previews...",
    "Финализация...": "Finalising...",
    "Инициализация...": "Initialising...",
    "Превью: готово": "Previews: done",
    "Готовность": "Readiness",
    "Готово": "Ready",
    "Старт": "Start",
    "Кеш найден": "Cache found",
    "Кеш пуст — Extract Resources": "Cache empty — run Extract Resources",
    "Game Root указан": "Game Root set",
    "Game Root не указан": "Game Root not set",
    "Output задан": "Output set",
    "Output не задан": "Output not set",
    ".blend сохранён": ".blend saved",
    "Имя уже занято": "Name already taken",
    "Укажите корневую папку GTA SA": "Pick the GTA SA root folder",
    "Как пользоваться": "How to use",
    "1. Сохрани .blend": "1. Save the .blend",
    "1. Извлечь ресурсы": "1. Extract resources",
    "2. Папка библиотеки": "2. Library folder",
    "2. Укажи Game Root и регион": "2. Set Game Root and region",
    "3. Извлеки ресурсы": "3. Extract resources",
    "4. Укажи папку Output": "4. Set the Output folder",
    "5. Жми «Собрать»": "5. Hit «Build»",
    "6. Edit > Preferences > File Paths >": "6. Edit > Preferences > File Paths >",
    "   Asset Libraries > Add → твой Output":
        "   Asset Libraries > Add → your Output",

    # Prelight: V-offset inline + scatter color sub-panel
    "Дальность": "Distance",
    "Цвет (из кисти)": "Color (from brush)",
    "Запечь с тенями": "Bake with shadows",
    "Сначала выберите пресет в списке": "Pick a preset from the list first",
    "без изменений": "no changes",

    # Misc UI / IK
    "OK": "OK",
    "Отменено": "Cancelled",
    "Root motion (walk/run)": "Root motion (walk/run)",
    "Настройка анимации": "Animation setup",
    "Исправить кватернионы (sign-flip)": "Fix quaternions (sign-flip)",
    "Сгладить между выделенными ключами":
        "Smooth between selected anchor keys",
    "Сгладить ключей":
        "Smoothed keys",
    "Выдели минимум 2 ключа в Dope Sheet как опорные":
        "Select at least 2 keyframes in the Dope Sheet to use as anchors",
    "Размер тени / интенсивность света":
        "Shadow size / light intensity",
    "VC Layers System": "VC Layers System",
    "Выдели объект чтобы увидеть иерархию":
        "Select an object to see the hierarchy",
    # === Added 2026-05-18 (parity sync with spa.py + new NEW-only strings) ===

    # --- 44 keys imported from SA eng.py ---
    'Auto: ползунки сами пересчитывают keyframes цикла.\nManual: ползунки заморожены, ты сам ставишь keyframes в Action Editor / Pose Mode. Переключение Manual→Auto перезапишет твои ключи значениями ниже':
        'Auto: sliders auto-recompute cycle keyframes.\nManual: sliders are frozen — you set keyframes yourself in Action Editor / Pose Mode. Switching Manual→Auto will overwrite your keys with the values below',
    'ID модели для IDE — должен быть свободен в карте.\n0 = не задан (исправь в Object Properties → INU Tools → Model ID)':
        'Model ID for IDE — must be free on the map.\n0 = not set (fix in Object Properties → INU Tools → Model ID)',
    'Library Output не указан или не существует':
        'Library Output is not set or does not exist',
    'Model ID = 0 — задай в Object Properties → INU Tools → Model ID':
        'Model ID = 0 — set it in Object Properties → INU Tools → Model ID',
    'Scene → INU Tools → IDE Path не задан — anim-запись не будет дописана':
        'Scene → INU Tools → IDE Path is not set — anim entry will not be appended',
    'Автоматически ставить material.alpha = 254 при наличии\nvertex alpha < 255 хоть на одной вершине меша.\n\nВКЛЮЧАТЬ: для прозрачных мешей (стёкла, дым, листва)\nесли хочешь чтобы движок воспринял геометрию как\nalpha-blended объект и сортировал её правильно.\n\nВЫКЛЮЧАТЬ (по умолчанию): материал остаётся opaque,\nvertex alpha не задаёт прозрачность всего объекта.\nПолезно когда vertex alpha используется для других\nцелей (vcol fade, light beam masking)':
        'Automatically set material.alpha = 254 when at least one\nvertex of the mesh has vertex alpha < 255.\n\nENABLE: for transparent meshes (glass, smoke, foliage)\nif you want the engine to treat the geometry as an\nalpha-blended object and sort it correctly.\n\nDISABLE (default): material stays opaque,\nvertex alpha does not drive whole-object transparency.\nUseful when vertex alpha is used for other purposes\n(vcol fade, light beam masking)',
    "Альтернативная текстура для Pay'n'Spray paintjob 1.\nБудет упакована в TXD как <base>_paintjob1, где <base> — имя основной текстуры этого материала.":
        "Alternate texture for Pay'n'Spray paintjob 1.\nPacked into TXD as <base>_paintjob1, where <base> is the name of this material's main texture.",
    "Альтернативная текстура для Pay'n'Spray paintjob 2.\nБудет упакована в TXD как <base>_paintjob2.":
        "Alternate texture for Pay'n'Spray paintjob 2.\nPacked into TXD as <base>_paintjob2.",
    "Базовое имя для .ifp (без расширения). Пусто = взять из «Базовое имя». Можно ввести общее имя типа 'myhood_anims' чтобы складывать анимации мельницы, крана и флюгера в один файл":
        "Base name for .ifp (without extension). Empty = take from «Base name». You can enter a common name like 'myhood_anims' to pack windmill, crane and weathervane animations into a single file",
    'Библиотека собрана за':
        'Library built in',
    'Библиотека:':
        'Library:',
    'В кеше нет DFF файлов — запустите «Извлечь ресурсы»':
        'No DFF files in cache — run «Extract resources»',
    'Длина цикла в кадрах. Скорость = обороты_за_цикл × fps_сцены / длительность':
        'Cycle length in frames. Speed = rotations_per_cycle × scene_fps / duration',
    'Длина цикла в кадрах. Скорость вращения = оборотов_за_цикл / длительность × fps_сцены':
        'Cycle length in frames. Rotation speed = rotations_per_cycle / duration × scene_fps',
    'Имя Blender Action — попадёт в IFP как имя анимации. Игра ищет анимацию по этому имени из IDE anim entry':
        'Blender Action name — written into IFP as animation name. Game looks up the animation by this name from the IDE anim entry',
    'Имя кости которую крутит rig. Меняется только если ты переименовал кость вручную в Edit Mode скелета':
        'Name of the bone driven by the rig. Change only if you renamed the bone manually in skeleton Edit Mode',
    'Имя кости — попадёт в DFF Frame name и в IFP bone-track. Принято использовать что-то описательное: blades, propeller, gear...':
        'Bone name — written into DFF Frame name and IFP bone-track. Convention is something descriptive: blades, propeller, gear...',
    'Кеш пуст — будут расставлены только Empty по IPL без геометрии. Для полной карты сначала запустите «Извлечь ресурсы»':
        'Cache is empty — only Empties will be placed per IPL without geometry. For a full map, run «Extract resources» first',
    'Крутить против часовой стрелки (с точки зрения +оси). Удобно если меш вышел зеркальным или физика подразумевает вращение в другую сторону':
        'Rotate counter-clockwise (looking down the +axis). Useful if the mesh ended up mirrored or the physics implies the opposite rotation direction',
    "Не найден исполняемый файл Blender'а":
        'Blender executable not found',
    'Перевёрнуто ключей':
        'Keys flipped',
    'Перезаписан:':
        'Overwritten:',
    'Подгрузить существующий, добавить новые анимации, заменить с тем же именем':
        'Load existing, add new animations, replace those with the same name',
    'Подгрузить существующий, заменить ТОЛЬКО анимации с совпадающим именем, новые НЕ добавлять':
        'Load existing, replace ONLY animations with a matching name, do NOT add new ones',
    'Превью обновлены за':
        'Previews refreshed in',
    'Сборка библиотеки (headless)…':
        'Building library (headless)…',
    'Сборка завершена':
        'Build finished',
    'Сначала сохраните сцену (.blend) — кеш создаётся рядом с ней':
        'Save the scene (.blend) first — cache is created next to it',
    'Сначала сохраните сцену (.blend) — кеш создаётся рядом с ней. Без сохранения извлечение уйдёт во временную папку и пропадёт':
        'Save the scene (.blend) first — cache is created next to it. Without saving, extraction will go to a temp folder and be lost',
    'Собрать все текстуры из выделенных DFF в один общий TXD.\nАвто-включает «Только выделенное» и подставляет имя ниже.':
        'Collect all textures from selected DFFs into one shared TXD.\nAuto-enables «Selected only» and fills in the name below.',
    'Сохрани текущую сцену — оператор открывает .blend файлы библиотеки в этом окне Blender и потеряет несохранённые изменения':
        'Save the current scene — the operator opens library .blend files in this Blender window and will lose unsaved changes',
    'Удалить кеш после сборки':
        'Delete cache after build',
    'Укажите папку для библиотеки в INU настройках (Library Output Path)':
        'Set the library folder in INU settings (Library Output Path)',
    'Флаг rpGEOMETRYLIGHT — геометрия принимает\nдинамическое освещение от движка (sun + ambient).\n\nБез флага: меш рендерится как unlit, виден только\nvertex prelight × matCol. Используется для\nself-illuminated объектов (вывески, окна с\nзапечённым свечением)':
        'rpGEOMETRYLIGHT flag — geometry receives\ndynamic lighting from the engine (sun + ambient).\n\nWithout the flag: mesh is rendered as unlit, visible\nonly via vertex prelight × matCol. Used for\nself-illuminated objects (signs, windows with\nbaked glow)',
    'Флаг rpGEOMETRYMODULATEMATERIALCOLOR — vertex prelight\nумножается на material color и ambient_obj в runtime.\n\nВЫКЛЮЧИ если хочешь чтобы prelight использовался «как\nесть» без модуляции (нужно для запечённого ночного\nосвещения, эффектов flicker от prelight). Стандарт\nу ванильных зданий — включён':
        'rpGEOMETRYMODULATEMATERIALCOLOR flag — vertex prelight\nis multiplied by material color and ambient_obj at runtime.\n\nDISABLE if you want prelight used «as-is» without\nmodulation (needed for baked night lighting, flicker\neffects from prelight). Standard for vanilla buildings —\nenabled',
    'Целое число полных оборотов за анимацию. Игра проигрывает цикл повторно — модель возвращается в стартовую позицию точно (без визуального рывка на стыке)':
        'Integer number of full rotations per animation. Game replays the cycle — model returns to start position exactly (no visual jerk at the seam)',
    'Целое число полных оборотов за анимацию. Цикл проигрывается повторно — модель возвращается в стартовую позицию точно (без визуального рывка)':
        'Integer number of full rotations per animation. Cycle is replayed — model returns to start position exactly (no visual jerk)',
    "Экспорт chunk'а Bin Mesh PLG в DFF.\n\nСодержит индексы триангуляции в том виде в котором\nдвижок ожидает их у себя в RpAtomic. Без него:\n• MEd / DFF Viewer не показывает геометрию\n• некоторые версии движка не рендерят меш\n\nВыключать имеет смысл только при микро-оптимизации\nразмера DFF когда модель не идёт в игру":
        "Export the Bin Mesh PLG chunk into DFF.\n\nContains triangulation indices in the form the\nengine expects on RpAtomic. Without it:\n• MEd / DFF Viewer doesn't show the geometry\n• some engine versions won't render the mesh\n\nOnly worth disabling to micro-optimize DFF size when\nthe model isn't shipped in the game",
    "Экспорт второй UV-карты — используется для lightmap'ов\nи dual-pass материалов. Если меш без второй UV-карты,\nфлаг безопасно оставить включённым (DFF не получит\nлишний chunk)":
        "Export the second UV map — used for lightmaps\nand dual-pass materials. If the mesh has no second UV map,\nit's safe to keep this flag on (DFF won't get an\nextra chunk)",
    'Экспорт дневных vertex colors (атрибут «Day»).\nЭто ванильный prelight который игра умножает на\nambient_obj в runtime. Выключи только если хочешь\nDFF без vertex colors (редкий случай)':
        'Export day vertex colors (attribute «Day»).\nThis is the vanilla prelight that the game multiplies\nby ambient_obj at runtime. Disable only if you want\na DFF without vertex colors (rare case)',
    "Экспорт нормалей вершин в DFF.\n\nВКЛЮЧАТЬ: для скиннингованных объектов (peds, vehicles)\nи любых моделей у которых динамическое освещение должно\nкорректно реагировать на смену освещения сцены.\n\nВЫКЛЮЧАТЬ (по умолчанию для map-объектов): нормали\nудваивают размер vertex stream'а; статичные здания\nобычно полностью освещены через vertex prelight, и\nдвижок нормали не использует. Файл получается меньше":
        'Export vertex normals into DFF.\n\nENABLE: for skinned objects (peds, vehicles)\nand any model whose dynamic lighting must respond\ncorrectly to changes in scene lighting.\n\nDISABLE (default for map objects): normals double\nthe vertex stream size; static buildings are usually\nfully lit via vertex prelight and the engine ignores\nnormals. File ends up smaller',
    'Экспорт ночных vertex colors (атрибут «Night»,\nRpExtraVertColors chunk). Игра берёт их в ночное\nвремя через timecyc-blend. Если у меша нет «Night»\nслоя — chunk не пишется автоматически':
        'Export night vertex colors (attribute «Night»,\nRpExtraVertColors chunk). Game uses them at night\nvia timecyc-blend. If the mesh has no «Night» layer,\nthe chunk is not written automatically',
    'Экспорт первой UV-карты — основной набор текстурных\nкоординат. Должен быть включён почти всегда —\nвыключи только если меш специально без UV':
        'Export the first UV map — the main set of texture\ncoordinates. Should be on almost always —\ndisable only if the mesh is intentionally without UV',
    'изменено':
        'changed',

    # --- 84 keys new to NEW codebase (multi-game III/VC/SA, weight-merge, presets) ---
    "'Default' read-only — сохрани под другим именем (Save)":
        "'Default' is read-only — save under a different name (Save)",
    "'Default' зарезервирован — выбери другое имя":
        "'Default' is reserved — pick another name",
    "'Default' нельзя переименовать — это встроенный пресет":
        "Cannot rename 'Default' — it's a built-in preset",
    "'Default' нельзя удалить — это встроенный пресет":
        "Cannot delete 'Default' — it's a built-in preset",
    "Backup идентичен текущему mesh'у (Undo схлопнул). Тэг очищен.":
        'Backup is identical to current mesh (Undo collapsed it). Tag cleared.',
    "Backup идентичен текущему mesh'у. Тэг очищен.":
        'Backup is identical to current mesh. Tag cleared.',
    'Cross-ref с IDE (used by)':
        'Cross-ref with IDE (used by)',
    'IDE cross-ref активен':
        'IDE cross-ref active',
    'IDE файлы:':
        'IDE files:',
    'IPL файлы:':
        'IPL files:',
    'Merge откатан, веса восстановлены':
        'Merge rolled back, weights restored',
    'Merged для weight paint:':
        'Merged for weight paint:',
    'Weight Paint: швы':
        'Weight Paint: seams',
    "cluster'ов,":
        'clusters,',
    'Авто-определение':
        'Auto-detect',
    'Аддитивный блендинг (8) · III/VC/SA':
        'Additive blending (8) · III/VC/SA',
    'Анализ завершён: проблем не найдено':
        'Analysis complete: no issues found',
    'Анализ карты завершён':
        'Map analysis complete',
    'Анализ карты/файлов':
        'Map/file analysis',
    'Архив':
        'Archive',
    'Без затухания на дистанции (2) · III/VC':
        'No distance fade (2) · III/VC',
    'Веса применены к':
        'Weights applied to',
    'Выдели минимум 2 ключа .location в Dope Sheet как опорные':
        'Select at least 2 .location keys in the Dope Sheet as anchors',
    'Граффити тег (1048576) · SA only':
        'Graffiti tag (1048576) · SA only',
    'Дверь гаража (2048) · SA only':
        'Garage door (2048) · SA only',
    'Дерево, качается на ветру (8192) · SA only':
        'Tree, sways in wind (8192) · SA only',
    'Динамическое освещение вместо статического (32) · III/VC':
        'Dynamic lighting instead of static (32) · III/VC',
    'Дорога, wet reflections (1) · VC/SA':
        'Road, wet reflections (1) · VC/SA',
    'Игнорировать draw distance (256) · VC only — typical для LOD-моделей':
        'Ignore draw distance (256) · VC only — typical for LOD models',
    'Игра':
        'Game',
    'Игра-источник IDE flags (III/VC/SA). Используется при экспорте для перевода битов между играми':
        'Source game for IDE flags (III/VC/SA). Used at export to translate bits between games',
    'Игра-источник Surface ID (III/VC/SA). Использует core.surface_translate при экспорте в другую игру':
        'Source game for Surface ID (III/VC/SA). Uses core.surface_translate when exporting to another game',
    'Из какой игры импортируем COL. Auto — по magic header':
        'Which game to import COL from. Auto — by magic header',
    'Из какой игры импортируем IPL. Auto — по числу колонок в inst-секции':
        'Which game to import IPL from. Auto — by column count in inst section',
    'Из какой игры импортируем. Auto — определить по RW-версии файла':
        'Which game to import from. Auto — detect by file RW version',
    'Использует gta.dat':
        'Uses gta.dat',
    'Лампы удалены':
        'Lights removed',
    'Между объектами:':
        'Between objects:',
    'Найдено':
        'Found',
    'Не жми Ctrl+Z — Undo ломает backup-mesh!':
        "Don't press Ctrl+Z — Undo breaks the backup-mesh!",
    'Не найдено translation-каналов для смещения в мировом пространстве':
        'No translation channels found for world-space offset',
    'Не писать в Z-буфер (64) · III/VC/SA':
        'No write to Z-buffer (64) · III/VC/SA',
    'Не получать тени (128) · VC/SA':
        'Do not receive shadows (128) · VC/SA',
    'Неизвестный режим input':
        'Unknown input mode',
    'Неизвестный режим источника':
        'Unknown source mode',
    'Нет mesh-объектов для сброса':
        'No mesh objects to reset',
    'Нет коллизии с летающим (32768) · SA only':
        'No collision with flying (32768) · SA only',
    'Нет результатов для сохранения — сначала запустите анализ':
        'No results to save — run the analysis first',
    'Объединить для покраски':
        'Merge for painting',
    'Откатить':
        'Roll back',
    'Пальма, качается на ветру (16384) · SA only':
        'Palm, sways in wind (16384) · SA only',
    'Поддержка':
        'Support',
    'Подтянуть тени':
        'Pull up shadows',
    'Применить и вернуть швы':
        'Apply and restore seams',
    'Принудительно III':
        'Force III',
    'Принудительно SA':
        'Force SA',
    'Принудительно VC':
        'Force VC',
    'Проанализировать':
        'Analyze',
    'Проверять модели в IMG':
        'Check models in IMG',
    'Прозрачный, рисовать последним (4) · III/VC/SA':
        'Transparent, draw last (4) · III/VC/SA',
    'Прочитать RW версию и угадать игру':
        'Read RW version and guess game',
    'РЕЖИМ MERGE: не меняй геометрию!':
        "MERGE MODE: don't modify geometry!",
    'Разрушаемая статуя (4194304) · SA only':
        'Breakable statue (4194304) · SA only',
    'Разрушаемый ok/dam (4096) · SA only':
        'Breakable ok/dam (4096) · SA only',
    'Рассеять цвет:':
        'Scatter color:',
    'Рисовать обе стороны (2097152) · SA only':
        'Draw both sides (2097152) · SA only',
    'Свет (8 ламп)':
        'Light (8 lamps)',
    'Сглажено ключей':
        'Keys smoothed',
    'Слить co-located вершины для покраски:':
        'Merge co-located vertices for painting:',
    "Список IDE/IPL пуст — добавь файлы кнопкой '+'":
        "IDE/IPL list is empty — add files with the '+' button",
    "Список файлов пуст — добавь .img / .txd кнопкой '+'":
        "File list is empty — add .img / .txd with the '+' button",
    'Стекло разбиваемое (512) · VC/SA':
        'Breakable glass (512) · VC/SA',
    'Стекло с трещинами (1024) · VC/SA':
        'Cracked glass (1024) · VC/SA',
    'Сцена не сохранена — сохраните .blend, отчёт пишется рядом':
        'Scene not saved — save the .blend, report is written next to it',
    'Текстур найдено':
        'Textures found',
    'Текстуры (TXD)':
        'Textures (TXD)',
    'Туннель, видим только в cull-зоне (16) · III only':
        'Tunnel, visible only in cull zone (16) · III only',
    'Укажите gta.dat файл в Map Analyzer':
        'Specify gta.dat file in Map Analyzer',
    'Укажите существующий .dat файл':
        'Specify an existing .dat file',
    'Файлы (.img / .txd):':
        'Files (.img / .txd):',
    'вершин. Не меняй геометрию!':
        "vertices. Don't change the geometry!",
    'вершинам, split-геометрия восстановлена':
        'vertices, split geometry restored',
    'ламп':
        'lights',
    'сглажено ключей':
        'keys smoothed',

    # Operator bl_label / bl_description (raw — no T()) — found 2026-05-18
    "INU: Импорт": "INU: Import",
    "INU: Экспорт": "INU: Export",
    "INU: Материалы": "INU: Materials",
    "INU: Текстуры": "INU: Textures",
    "INU: Создать 2DFX": "INU: Create 2DFX",
    "INU: Сохранить пресет": "INU: Save Preset",
    "INU: Удалить пресет": "INU: Delete Preset",
    "INU: Генерировать радар": "INU: Generate Radar",
    "INU: Светофор": "INU: Traffic Light",
    "Инструменты": "Tools",
    "Проредить ключи": "Thin keyframes",
    # === Wrapped at 2026-05-18 (display strings via T()) ===
    ' ключей':
        'keys',
    ' ключей записано':
        'keys written',
    ' материал(ов)':
        'material(s)',
    ' моделей)':
        'models)',
    ' уже _dam — выбери _ok вариант':
        'already _dam — pick the _ok variant',
    ' уже есть в сцене — связана пара':
        'already in scene — pair linked',
    ' файлов (':
        'files (',
    "' не найден в effects.fxp":
        "' not found in effects.fxp",
    "' не найдена":
        "' not found",
    "' не найдена — нечего клонировать":
        "' not found — nothing to clone",
    "' нет эмиттеров":
        "' has no emitters",
    "' уже существует":
        "' already exists",
    "' уже существует (снимите галку 'Overwrite' нельзя, включите её)":
        "' already exists (you cannot uncheck 'Overwrite' — turn it on)",
    ', интерполяция применена к ':
        ', interpolation applied to ',
    'ALL удалить нельзя':
        'Cannot delete ALL',
    'Auto-decimate выполнен, интерполяция применена к ':
        'Auto-decimate done, interpolation applied to ',
    'Game Root не задан':
        'Game Root is not set',
    'Lightmap не найден в материалах':
        'Lightmap not found in materials',
    'Lightmap удалён из ':
        'Lightmap removed from ',
    'effects.fxp не найден: ':
        'effects.fxp not found: ',
    'Автобусный':
        'Bus',
    'Без светофора':
        'No traffic light',
    'Блик солнца':
        'Sun Glare',
    'Выделено: ...':
        'Selected: ...',
    'Генерировать радар':
        'Generate Radar',
    'Железнодорожный':
        'Railroad',
    "Имя 'ALL' зарезервировано":
        "The name 'ALL' is reserved",
    'Имя содержит недопустимые символы или слишком длинное':
        'Name contains invalid characters or is too long',
    'Интерполяция оставшихся ключей:':
        'Interpolation for remaining keys:',
    "Исходная система '":
        "Source system '",
    'Меню радар (3x3)':
        'Radar menu (3x3)',
    "Не нашёл F-curve'ы — выбери анимированный объект.":
        'No F-curves found — select an animated object.',
    'Не удалось загрузить ':
        'Failed to load ',
    'Не удалось создать бэкап: ':
        'Failed to create backup: ',
    'Неверный ключ кривой: ':
        'Invalid curve key: ',
    'Нет выделенных ключей. Выдели нужные ключи в Graph Editor.':
        'No selected keys. Select the keys you need in Graph Editor.',
    'Обычный':
        'Normal',
    'Ошибка записи профиля':
        'Profile write error',
    'Ошибка записи: ':
        'Write error: ',
    'Ошибка парсинга effects.fxp: ':
        'effects.fxp parse error: ',
    'Ошибка парсинга: ':
        'Parse error: ',
    'Ошибка применения правок: ':
        'Edit application error: ',
    'Ошибка сохранения':
        'Save error',
    'Ошибка удаления':
        'Delete error',
    'Полный меню':
        'Full Menu',
    'Полный радар':
        'Full Radar',
    'Применить':
        'Apply',
    'Проредить выделенные ключи':
        'Thin selected keys',
    'Свет':
        'Light',
    "Система '":
        "System '",
    'Создан эффект: ':
        'Effect created: ',
    'Создан: ':
        'Created: ',
    'Сохранить как…':
        'Save as…',
    "У системы '":
        "System '",
    'Удалено ключей: ':
        'Keys removed: ',
    'Удалено: ':
        'Removed: ',
    'Удалить':
        'Delete',
    'Удалён: ':
        'Deleted: ',
    'Указанные тайлы':
        'Specified tiles',
    'Частица':
        'Particle',
    "Эффект '":
        "Effect '",
    'имя обязательно':
        'name is required',
    'не удалось удалить':
        'failed to delete',
    'нет выбранного пресета':
        'no preset selected',
    'ошибка сохранения':
        'save error',
    'сохранён: ':
        'saved: ',
    'удалён: ':
        'deleted: ',

    # === Docstring / prop translations added 2026-05-18 ===
    'Создать рiг для animated map object (мельница, кран, флюгер):\n    Armature с одной костью + Action с цикличной Z-вращением.\n\n    Все вершины активного меша автоматически привязываются к\n    единственной кости (vertex group weight=1.0). Готово к экспорту в\n    DFF + IFP без ручной настройки скелета.':
        'Create a rig for animated map object (windmill, crane, weathervane):\n    Armature with one bone + Action with a cyclic Z rotation.\n\n    All vertices of the active mesh are auto-bound to the single bone (vertex group weight=1.0). Ready to export to DFF + IFP without manual skeleton setup.',
    'Проверить настройку animated map object перед экспортом:\n    есть ли armature, привязан ли меш, заданы ли веса, есть ли action,\n    цикличный ли он. Лог проблем в System Console.':
        'Validate animated map object setup before export: armature presence, mesh binding, weights, action presence and cyclicity. Issues are logged to the System Console.',
    'Экспортировать animated map object одним кликом: пишет\n    <base>.dff + <base>.ifp в выбранную папку. Опционально дописывает\n    или обновляет anim-запись в указанном IDE-файле.':
        'Export the animated map object in one click: writes <base>.dff + <base>.ifp into the chosen folder. Optionally appends or updates the anim entry in the specified IDE file.',
    "Собрать Blender Asset Library из извлечённых ресурсов.\n\n    Walks every IDE in gta.dat / default.dat, classifies every cached DFF\n    by category (Cars / Peds / Weapons / Map Objects per region / LOD /\n    Interiors), imports each into a Collection, marks as an asset, embeds\n    INU metadata (model_id, txd_name, draw_distance, ide_flags), and\n    optionally renders a thumbnail. Output is a folder with one .blend\n    per category plus blender_assets.cats.txt — point Blender's Asset\n    Library preferences at it and you're done.":
        "Build a Blender Asset Library from extracted resources.\n\n    Walks every IDE in gta.dat / default.dat, classifies every cached DFF\n    by category (Cars / Peds / Weapons / Map Objects per region / LOD /\n    Interiors), imports each into a Collection, marks as an asset, embeds\n    INU metadata (model_id, txd_name, draw_distance, ide_flags), and\n    optionally renders a thumbnail. Output is a folder with one .blend\n    per category plus blender_assets.cats.txt — point Blender's Asset\n    Library preferences at it and you're done.",
    "Перегенерировать превьюшки в существующей Asset Library.\n\n    Iterates every ``<output>/*.blend``, opens it in this Blender\n    instance, re-renders thumbnails for every asset-marked collection,\n    then saves the .blend back. The asset list / metadata / textures\n    are untouched — only the preview pixels are refreshed. Useful for\n    bumping ``preview_size`` from 128 to 256 (or vice-versa) without\n    waiting through a full DFF re-import.\n\n    Stays in-process (modal generator) — opens .blend files in the\n    current session, headless subprocess would lose that scene-state\n    integration with the asset browser. Speed-up isn't critical for\n    preview-only refresh anyway.":
        "Regenerate previews in an existing Asset Library.\n\n    Iterates every ``<output>/*.blend``, opens it in this Blender\n    instance, re-renders thumbnails for every asset-marked collection,\n    then saves the .blend back. The asset list / metadata / textures\n    are untouched — only the preview pixels are refreshed. Useful for\n    bumping ``preview_size`` from 128 to 256 (or vice-versa) without\n    waiting through a full DFF re-import.\n\n    Stays in-process (modal generator) — opens .blend files in the\n    current session, headless subprocess would lose that scene-state\n    integration with the asset browser. Speed-up isn't critical for\n    preview-only refresh anyway.",
    'Импорт COL коллизии GTA SA с прогресс-баром.\n    ESC прерывает импорт, уже созданные объекты остаются в сцене.':
        'Import a GTA SA collision COL with progress bar.\n    ESC interrupts the import — already-created objects stay in the scene.',
    'Импорт COL при перетаскивании во viewport (батч, прогресс + ESC).\n\n    Принимает несколько файлов сразу. Селекция игнорируется — COL\n    создаёт собственные mesh-объекты, не цепляется к существующим.':
        "Import COL on drag-and-drop into the viewport (batch, progress + ESC).\n\n    Accepts multiple files at once. Selection is ignored — COL\n    creates its own mesh objects, it doesn't attach to existing ones.",
    'Импорт DFF при перетаскивании во viewport.\n\n    Принимает несколько файлов сразу (батч), каждый импортируется\n    как отдельная модель. Та же логика автоматического подцепления\n    одноимённого .txd, что и в обычном импорте.':
        'Import DFF on drag-and-drop into the viewport.\n\n    Accepts multiple files at once (batch); each is imported as a separate model. Same auto-attach logic for the matching .txd as the regular import.',
    'Переключить один бит в 2dfx_flags1 / 2dfx_flags2 на активном объекте.':
        'Toggle one bit in 2dfx_flags1 / 2dfx_flags2 on the active object.',
    'Сканировать выбранную папку на crash-prone паттерны в DFF/COL/TXD':
        'Scan selected folder for crash-prone patterns in DFF/COL/TXD',
    'Сохранить результат скана в .txt':
        'Save scan result to .txt',
    'Открыть папку файла в Проводнике':
        "Open file's folder in Explorer",
    'Очистить список результатов':
        'Clear results list',
    'Сделать активным указанный фрейм (используется панелью при клике\n    на строку дерева).':
        'Make the specified frame active (used by the panel when clicking\n    on a tree row).',
    'Переименовать активный фрейм.':
        'Rename the active frame.',
    'Назначить parent: активный объект становится родителем для остальных\n    выделенных. Мировая позиция каждого ребёнка сохраняется, а\n    matrix_parent_inverse сбрасывается в identity (DFF requirement).':
        'Set parent: active object becomes the parent of the other selected ones. World position of every child is preserved, and matrix_parent_inverse is reset to identity (DFF requirement).',
    'Снять parent с выделенных объектов (parent → None). Мировая\n    позиция сохраняется.':
        'Clear parent on selected objects (parent → None). World position is preserved.',
    'Проверить иерархию активного объекта против vanilla SA шаблона.\n    Тип шаблона выбирается атрибутом ``template`` оператора.':
        "Validate the active object's hierarchy against the vanilla SA template.\n    Template type is selected by the operator's ``template`` attribute.",
    'Создать зеркальную копию выделенных фреймов: ``_lf`` → ``_rf``,\n    ``_lb`` → ``_rb`` (X отражается, остальные оси без изменений). Если\n    зеркальный близнец уже существует — оператор его не трогает.':
        'Create a mirrored copy of selected frames: ``_lf`` → ``_rf``,\n    ``_lb`` → ``_rb`` (X is mirrored, other axes unchanged). If the\n    mirrored twin already exists — operator leaves it alone.',
    'Прореживание выделенных ключей. Stride — оставить каждый N-ный\n    ключ. Auto — удалить ключи которые лежат на прямой между соседями\n    (избыточные).':
        'Thin out selected keyframes. Stride — keep every Nth key. Auto — remove keys lying on the straight line between neighbours (redundant).',
    'N-panel в Graph Editor с прореживанием ключей.':
        'N-panel in the Graph Editor for thinning keyframes.',
    'Диагностика round-trip для IFP — проверяет что read → write → read\n    не теряет анимации, не путает кости и не ломает квартернионы.\n\n    Выбранный файл не меняется: экспорт идёт во временный файл рядом,\n    результат сравнивается с оригиналом и удаляется. Отчёт показывает\n    счётчики и максимальные численные отклонения (dRot, dTrans, dTime)':
        "Round-trip diagnostics for IFP — checks that read → write → read doesn't lose animations, mix up bones or break quaternions.\n\n    The selected file is not modified: export goes to a temp file next to it, the result is compared with the original and deleted. Report shows counters and maximum numerical deltas (dRot, dTrans, dTime)",
    "Переключить живой preview IFP-анимации без коммита в Action.\n\n    Позволяет быстро пробежаться по 294 ванильным анимациям `ped.ifp`\n    простым переключением Action-dropdown'а без захламления Action\n    Editor'а. Handler frame_change_post напрямую пишет в pose bones\n    при скрабе Timeline. Повторный клик — выключает preview и\n    восстанавливает предыдущий Action арматуры":
        "Toggle live IFP animation preview without committing to Action.\n\n    Lets you quickly browse through 294 vanilla `ped.ifp` animations\n    by simply switching the Action dropdown, without cluttering the\n    Action Editor. The frame_change_post handler writes directly to\n    pose bones when scrubbing the Timeline. A repeated click — turns\n    off preview and restores the armature's previous Action",
    'Исправить sign-discontinuities кватернионов на диапазоне кадров.\n    Между двумя соседними ключами с dot < 0 кость крутится длинной\n    дорогой через 360°. Скрипт находит такие пары и инвертирует знак\n    кватерниона на втором ключе — q и -q описывают одинаковую ротацию,\n    но интерполяция между ними после флипа идёт коротким путём.\n\n    Идемпотентный — повторный прогон не ухудшит, иногда нужен 2-й\n    проход чтобы вылезли ранее скрытые разрывы.':
        "Fix quaternion sign-discontinuities over a frame range.\n    Between two adjacent keys with dot < 0 the bone takes the long path through 360°. The script finds such pairs and flips the sign of the second key — q and -q describe the same rotation, but interpolation after the flip takes the short path.\n\n    Idempotent — a repeat run won't make things worse; sometimes a 2nd pass is needed for earlier-hidden discontinuities to surface.",
    'Сгладить ключи между выделенными опорными.\n\n    Use-case: запечённая анимация с ключом на каждом кадре (например 700\n    ключей). Хочешь опустить кость на кадре 70 — двигаешь её там, потом\n    в Dope Sheet/Graph Editor выделяешь 3 ключа (50, 70, 90: первый,\n    редактированный, последний) и нажимаешь эту кнопку. Промежуточные\n    ключи (51-69 и 71-89) перезаписываются smooth-step интерполяцией\n    между соседними опорными — будто там никаких ключей и не было.\n\n    Режимы оси:\n    - ALL — обрабатывает ВСЕ F-curve (включая rotation, scale) в bone-\n      local координатах. Быстро.\n    - WORLD_X/Y/Z — обрабатывает только .location и считает в МИРОВЫХ\n      координатах. Учитывает поворот родительских костей и armature.\n      Медленнее (per-frame depsgraph eval), но даёт правильный «по Z\n      вниз» эффект независимо от ориентации кости.\n\n    Анкоры берутся из выделенных ключей, минимум 2.\n    Структура «ключ на каждом кадре» сохраняется (важно для round-trip\n    в IFP).':
        'Smooth keys between selected anchors.\n\n    Use-case: a baked animation with a key on every frame (e.g. 700\n    keys). You want to lower the bone at frame 70 — you move it there, then\n    in Dope Sheet/Graph Editor you select 3 keys (50, 70, 90: first,\n    edited, last) and press this button. Intermediate\n    keys (51-69 and 71-89) are overwritten with smooth-step interpolation\n    between the adjacent anchors — as if no keys had been there at all.\n\n    Axis modes:\n    - ALL — processes ALL F-curves (including rotation, scale) in bone-\n      local coordinates. Fast.\n    - WORLD_X/Y/Z — processes only .location and computes in WORLD\n      coordinates. Takes parent bone rotation and armature into account.\n      Slower (per-frame depsgraph eval), but gives the correct «down\n      along Z» effect regardless of bone orientation.\n\n    Anchors are taken from the selected keys, minimum 2.\n    The «key on every frame» structure is preserved (important for IFP\n    round-trip).',
    'Удалить активную Action арматуры из файла полностью.\n    В отличие от кнопки X в Action Editor (которая только отвязывает),\n    этот оператор стирает Action из bpy.data.actions — полезно чтобы\n    в IFP-экспорт не попадали забытые анимации.':
        "Delete the armature's active Action from the file entirely.\n    Unlike the X button in Action Editor (which only unlinks),\n    this operator wipes the Action from bpy.data.actions — useful so\n    forgotten animations don't end up in the IFP export.",
    'Накинуть bone-based IK на стандартные цепочки SA-педа.\n    Создаёт non-deform контрольные кости внутри армча: запястья,\n    ступни, голову и корень. На deform-кости — IK-constraint и\n    Copy Rotation/Location, target — соответствующая control-кость.\n    Контроллы окрашены зелёным (THEME09). Перед Export IFP — Bake\n    & Clear IK, которая всё снимет и удалит control-кости.':
        'Apply bone-based IK to the standard SA-ped chains.\n    Creates non-deform control bones inside the armature: wrists,\n    feet, head and root. Deform bones get IK-constraints and\n    Copy Rotation/Location targeting the matching control bone.\n    Controls are coloured green (THEME09). Before Export IFP — Bake\n    & Clear IK, which removes everything and deletes the control bones.',
    'Запечь визуальную позу с IK на deform-кости, удалить\n    IK-constraints и control-кости. Делать ПЕРЕД Export IFP —\n    иначе ифп получит сырые ротации без учёта IK.':
        'Bake the visual IK pose onto the deform bones and remove\n    IK-constraints and control bones. Do this BEFORE Export IFP —\n    otherwise IFP would get raw rotations without IK applied.',
    'Создать "пол" — плоскость 10×10м с dev_anim текстурой,\n    которая работает как ограничитель для ног IK-рига. После\n    Add IK Rig стопы автоматически получают Floor constraint\n    с этой плоскостью как target — двигаешь плоскость по Z,\n    стопы клемпятся выше неё. Зазор (offset над плоскостью)\n    настраивается слайдером "Зазор"':
        'Create a "floor" — a 10×10m plane with dev_anim texture\n    that acts as a limiter for the IK rig\'s feet. After\n    Add IK Rig the feet automatically get a Floor constraint\n    targeting this plane — you move the plane along Z,\n    feet clamp above it. The gap (offset above the plane)\n    is tuned with the "Зазор" slider',
    'Извлечь все DFF, COL и текстуры из IMG-архивов GTA SA.\n\n    Кеш создаётся в папке .inu_cache/ рядом с твоим .blend файлом,\n    поэтому сцену нужно сначала сохранить — без сохранённого .blend\n    кешу некуда лечь, и оператор откажется работать.\n\n    Региональный фильтр (если выбран) сужает извлечение до TXD/моделей,\n    реально используемых в этом регионе по IDE/IPL — экономит минуты\n    на больших картах. ALL = извлечь всё':
        "Extract all DFF, COL and textures from GTA SA IMG archives.\n\n    The cache is created in the .inu_cache/ folder next to your .blend file,\n    so the scene must be saved first — without a saved .blend there's\n    nowhere to put the cache, and the operator will refuse to run.\n\n    The region filter (when chosen) narrows extraction to TXD/models\n    actually used in that region per IDE/IPL — saves minutes\n    on big maps. ALL = extract everything",
    'Toggle 8-light setup: создать если ламп нет, удалить если есть':
        'Toggle 8-light setup: create if no lamps exist, remove if they do',
    'Подтянуть тёмные участки к ярким, сохраняя шаг между гранями':
        'Lift dark areas towards the bright ones while preserving the step between faces',
    'Рассеять выбранный цвет вокруг выделенных полигонов с убыванием по расстоянию':
        'Scatter the chosen colour around the selected polygons with distance falloff',
    'Добавить IDE файл в список Custom':
        'Add IDE file to the Custom list',
    'Добавить IPL файл в список Custom':
        'Add IPL file to the Custom list',
    'Удалить запись IDE из Custom списка':
        'Remove an IDE entry from the Custom list',
    'Удалить запись IPL из Custom списка':
        'Remove an IPL entry from the Custom list',
    'Очистить список результатов':
        'Clear results list',
    'Сохранить результаты анализа в .txt':
        'Save analysis results to .txt',
    'Открыть документацию аддона на GitHub. Язык подбирается\n    под текущую локаль Blender.':
        "Open the addon's documentation on GitHub. Language is picked\n    to match the current Blender locale.",
    'Открыть issues аддона на GitHub — для багрепортов и пожеланий.':
        "Open the addon's issues on GitHub — for bug reports and feature requests.",
    'Открыть страницу последнего релиза на GitHub — там полный\n    changelog текущей версии, рендерится из RELEASE_NOTES.':
        'Open the latest release page on GitHub — full changelog of\n    the current version, rendered from RELEASE_NOTES.',
    'Показать краткий обзор новых фич текущей версии.':
        'Show a brief overview of the new features in this version.',
    "Проверить все материалы со слотами Paintjob:\n    оба слота должны быть заполнены, и у материала должна быть основная\n    текстура — иначе игра не подхватит paintjob в Pay'n'Spray.":
        "Validate all materials with Paintjob slots:\n    both slots must be filled, and the material must have a main\n    texture — otherwise the game won't pick up the paintjob in Pay'n'Spray.",
    'Перезаписать выбранный пресет текущими настройками (без диалога имени)':
        'Overwrite the selected preset with the current settings (no name dialog)',
    'Переименовать выбранный пресет':
        'Rename the selected preset',
    'Просканировать TXD по выбранному источнику и заполнить\n    Texture Browser метаданными (без декодинга пикселей)':
        'Scan TXD from the chosen source and populate\n    Texture Browser with metadata (without decoding pixels)',
    'Очистить результаты Texture Browser':
        'Clear Texture Browser results',
    'Добавить .img / .txd в список Custom':
        'Add .img / .txd to the Custom list',
    'Удалить запись из Custom-списка':
        'Remove an entry from the Custom list',
    "Запустить полную проверку сцены: paintjob слоты, нормировку\n    кватернионов в Action'ах, Modulate Color на прилайтах и парность\n    _ok/_dam. Результаты пишутся в панель — кликом можно перейти к\n    проблемному объекту или починить автоматически.":
        'Run a full scene check: paintjob slots, Action quaternion\n    normalisation, Modulate Color on prelight meshes and\n    _ok/_dam pairing. Results are written to the panel — a click\n    can jump to the problem object or fix it automatically.',
    'Очистить список результатов.':
        'Clear results list.',
    'Сделать активным объект/материал из строки результата.':
        'Make the object/material from the result row active.',
    'Нормализовать все кватернионные ключи в указанном Action.\n    Идентично тому что делает IFP-экспортёр на лету, но пишет правку\n    обратно в Action — на след. экспорт уже нечего нормировать.':
        'Normalise every quaternion key in the specified Action.\n    Identical to what the IFP exporter does on the fly, but writes the\n    fix back into the Action — next export has nothing left to normalise.',
    "Переименовать объект, заменив неправильный разделитель в\n    суффиксе на тот, что задан в настройках суффиксов сцены.\n\n    Применимо только к мисматчу типа «.DFF при настройке _DFF» —\n    т.е. имя оканчивается на конфигурированный bare-token, но через\n    другой разделитель. Двойной суффикс (body_LOD_DFF) не трогаем —\n    там нет однозначного автоматического fix'а.":
        "Rename the object, replacing the wrong separator in the\n    suffix with the one set in scene suffix preferences.\n\n    Applies only to mismatches like «.DFF when configured as _DFF» —\n    i.e. the name ends with the configured bare-token but via\n    a different separator. A double suffix (body_LOD_DFF) is left\n    alone — there's no unambiguous automatic fix.",
    'Снять флаг Modulate Color у указанного объекта — устраняет\n    flicker на прилайтных мешах.':
        'Clear the Modulate Color flag on the specified object —\n    fixes flicker on prelit meshes.',
    "Временно слить co-located вершины для редактирования весов.\n\n    Backup'ит mesh datablock, усредняет веса между cluster-mate'ами,\n    делает bmesh remove_doubles. В Outliner'е остаётся один объект.":
        'Temporarily merge co-located vertices for weight editing.\n\n    Backs up the mesh datablock, averages weights between cluster-mates,\n    runs bmesh remove_doubles. A single object remains in the Outliner.',
    "Применить покрашенные веса обратно на оригинальную split-геометрию.\n\n    Считывает веса с merged-меша, swap'ает mesh datablock обратно на\n    backup (со split-вершинами), распределяет веса по cluster-mate'ам\n    через position-match.":
        'Apply painted weights back to the original split geometry.\n\n    Reads weights from the merged mesh, swaps the mesh datablock back to\n    the backup (with split vertices), distributes the weights across the\n    cluster-mates via position-match.',
    "Откатить merge без сохранения покрашенных весов.\n\n    Swap'ает mesh datablock обратно на backup, удаляет merged-копию.\n    Веса покрашенные в merged-режиме теряются.":
        'Roll back the merge without saving painted weights.\n\n    Swaps the mesh datablock back to the backup, removes the merged copy.\n    Weights painted in merged mode are lost.',
    "Фоновый модал — диспатчит события на все видимые floater'ы":
        'Background modal — dispatches events to all visible floaters',
    'Показать / скрыть плавающее окно INU Floater':
        'Show / hide an INU Floater window',
    'Найти неиспользуемые текстуры и материалы — те, на которые не ссылается ни один меш-слот в сцене':
        'Find unused textures and materials — those not referenced by any mesh slot in the scene',
    'Удалить неиспользуемые текстуры и (опционально) материалы из сцены.\n\n    use_fake_user-помеченные datablocks пропускаются — это явный знак\n    «оставить даже без ссылок». Действие необратимо без Ctrl+Z, поэтому\n    показывает подтверждение со счётчиками перед удалением':
        "Remove unused textures and (optionally) materials from the scene.\n\n    use_fake_user-flagged datablocks are skipped — that's an explicit signal\n    «keep even with no references». The action is irreversible without Ctrl+Z, so it\n    shows a confirmation with counters before deleting",
    'Сохранить текущие настройки материала как новый пресет':
        'Save current material settings as a new preset',
    'Удалить пользовательский пресет (встроенные удалить нельзя)':
        "Delete a user preset (built-ins can't be deleted)",
    'Создать новый профиль. Маленький popup только с именем и\n    описанием — все панели включаются по умолчанию, видимость и\n    порядок настраиваются после через кнопку ⚙ (Edit Profile).':
        'Create a new profile. A small popup with just the name and\n    description — all panels are on by default; visibility and\n    order are tuned afterwards via the ⚙ button (Edit Profile).',
    'Удалить активный пользовательский профиль (ALL удалить нельзя).':
        'Delete the active user profile (ALL cannot be deleted).',
    "Click-to-pick / click-to-place reorder: первый клик «берёт»\n    панель (она подсвечивается), второй клик по другой панели\n    «кладёт» её на это место. Эмулирует drag-and-drop через два\n    клика — Blender Python не отдаёт настоящий drag для custom\n    items в popup'е.":
        "Click-to-pick / click-to-place reorder: first click «picks» a\n    panel (it highlights), second click on another panel\n    «places» it at that spot. Emulates drag-and-drop via two\n    clicks — Blender Python doesn't expose a real drag for custom\n    items in a popup.",
    'Eye-toggle: переключает видимость одной панели в активном\n    профиле. Позиция панели в `order` не меняется — только\n    membership в `hidden` set.':
        "Eye-toggle: flips visibility of a single panel in the active\n    profile. The panel's position in `order` isn't changed —\n    only membership in the `hidden` set.",
    'Открыть редактор активного профиля в отдельном popup-окне.\n    Та же UI что и inline-список, но скрытая за одной кнопкой —\n    main panel остаётся чистой пока юзер не настраивает layout.':
        'Open the editor for the active profile in a separate popup\n    window. Same UI as the inline list, but hidden behind one\n    button — the main panel stays clean until the user tunes layout.',
    'Добавить новый слой в текущий стек (Day или Night).\n\n    Создаёт ``BYTE_COLOR``/``CORNER`` атрибут с префиксом ``VCL_D_`` или\n    ``VCL_N_`` и инициализирует его прозрачным (alpha=0). Стек ограничен\n    10 слоями — операция отказывает с предупреждением при переполнении':
        'Add a new layer to the current stack (Day or Night).\n\n    Creates a ``BYTE_COLOR``/``CORNER`` attribute prefixed with ``VCL_D_`` or\n    ``VCL_N_`` and initialises it as transparent (alpha=0). Stack is capped\n    at 10 layers — operation refuses with a warning on overflow',
    'Удалить активный слой и его color attribute. Действие undo-able':
        'Remove the active layer and its color attribute. Action is undo-able',
    'Переместить активный слой вверх/вниз в стеке (меняет порядок блендинга)':
        'Move the active layer up/down in the stack (changes blend order)',
    'Сделать слой полноценным прилайт-атрибутом (убрать VCL_<scope>_ префикс).\n\n    Атрибут останется на меше под коротким именем — но из стека VCL\n    исчезнет. Полезно когда заведомо «временный» слой пора зафиксировать\n    как новый базовый прилайт':
        'Promote a layer to a full-fledged prelight attribute (strip the VCL_<scope>_ prefix).\n\n    The attribute stays on the mesh under the short name — but disappears\n    from the VCL stack. Useful when a deliberately «temporary» layer is ready\n    to be locked in as a new base prelight',
    'Превратить произвольный color attribute в VCL-слой (добавить префикс).\n\n    Scope (Day или Night) определяется параметром оператора — на UI\n    кнопки «→ Day» / «→ Night» рядом с не-VCL атрибутами в секции «База»':
        'Demote an arbitrary color attribute into a VCL layer (add the prefix).\n\n    Scope (Day or Night) is set by the operator parameter — in the UI\n    «→ Day» / «→ Night» buttons appear next to non-VCL attributes in the «База» section',
    'Сделать атрибут Day или Night активным в Color Attributes.\n\n    В hijack-режиме (Live Preview ON) Day и Night содержат итоговую\n    композицию своего стека — клик на эту кнопку просто переключает\n    активный color attribute на нужный, чтобы viewport показал нужный\n    стек. Если Live Preview OFF — Day/Night содержат оригиналы, кнопки\n    работают как обычный «выбрать атрибут»':
        'Make the Day or Night attribute active in Color Attributes.\n\n    In hijack mode (Live Preview ON) Day and Night contain the final\n    composition of their stack — clicking this button just switches the\n    active color attribute to the one you need so the viewport shows the\n    right stack. If Live Preview is OFF — Day/Night contain the originals,\n    the buttons behave like a regular «pick attribute»',
    'Пересобрать composite в Day/Night вручную.\n\n    Используется когда нужно форсировать пересчёт без триггера через\n    слайдер — например после ручного редактирования атрибутов через\n    Mesh Data Properties':
        'Rebuild the Day/Night composite manually.\n\n    Used when you need to force a recompute without triggering via a\n    slider — e.g. after manually editing the attributes via\n    Mesh Data Properties',
    "Применить значение слайдера к выделенным слоям.\n\n    Режим 'ABSOLUTE' — всем выделенным присваивается одно и то же\n    значение. 'RELATIVE' — каждое значение сдвигается на дельту\n    относительно своего текущего":
        "Apply the slider value to the selected layers.\n\n    Mode 'ABSOLUTE' — all selected get the same value. 'RELATIVE' —\n    each value is shifted by the delta relative to its current one",
    'Перекрасить выделенные слои — заменить RGB всех окрашенных\n    пикселей на выбранный цвет (alpha сохраняется).\n\n    Полезно когда хочешь поменять оттенок группы слоёв, не трогая то\n    что под ними и не перерисовывая руками':
        "Recolor selected layers — replace the RGB of every coloured\n    pixel with the chosen colour (alpha is preserved).\n\n    Useful when you want to change the tint of a group of layers without\n    touching what's underneath or repainting by hand",
    "Сделать color attribute этого слоя активным на меше + (опционально) переключиться в Vertex Paint.\n\n    Используется UIList'ом — клик по строке слоя сразу даёт пользователю\n    рисовать в нужный атрибут без ручного переключения в Mesh Data\n    Properties → Color Attributes":
        "Make this layer's color attribute active on the mesh + (optionally) switch to Vertex Paint.\n\n    Used by the UIList — clicking on a layer row lets the user paint into\n    the correct attribute without manually switching in Mesh Data\n    Properties → Color Attributes",
    'Создать поврежденный (_dam) дубликат активного меша. Если у источника нет суффикса, ему присваивается _ok. Поврежденный вариант ставится в ту же иерархию и скрывается во viewport (но остаётся видим для DFF-экспорта)':
        'Create a damaged (_dam) duplicate of the active mesh. If the source has no suffix, _ok is assigned to it. The damaged variant is placed in the same hierarchy and hidden in the viewport (but stays visible for DFF export)',
    'Переключить отображение OK / Damaged частей машины во viewport. Сканирует иерархию активной машины (или всю сцену, если активного объекта нет) и скрывает _ok или _dam меши в зависимости от выбранного состояния. Не влияет на DFF-экспорт':
        "Toggle OK / Damaged vehicle parts display in the viewport. Scans the active vehicle's hierarchy (or the whole scene if no active object) and hides _ok or _dam meshes depending on the chosen state. Does not affect DFF export",
    'Найти и отчитаться о парах _ok / _dam в активной иерархии. Предупреждает если у меша есть _ok без _dam (или наоборот) — такой меш пропускается движком при повреждениях':
        'Find and report _ok / _dam pairs in the active hierarchy. Warns when a mesh has _ok without _dam (or vice versa) — such a mesh is skipped by the engine on damage',
    'Главная панель GTA Tools — root of the N-sidebar tab. Not in\n    PANELS registry: roots have no bl_order (they own the tab) and\n    Phase 5 will need one root per tab, handled separately.':
        'Main GTA Tools panel — root of the N-sidebar tab. Not in\n    PANELS registry: roots have no bl_order (they own the tab) and\n    Phase 5 will need one root per tab, handled separately.',
    'Pre-export sweep: paintjob slots, quaternion normalisation,\n    Modulate Color на прилайтах, парность _ok/_dam.\n\n    Sub-panel живёт внутри Export panel — pre-flight check рядом с\n    кнопкой экспорта, без отдельного слота в registry.':
        'Pre-export sweep: paintjob slots, quaternion normalisation,\n    Modulate Color on prelight meshes, _ok/_dam pairing.\n\n    Sub-panel lives inside the Export panel — pre-flight check next\n    to the export button, no separate slot in the registry.',
    'Scrollable list of binary file lint issues. Filters by severity\n    («Только ERROR» toggle) and free-text search via the standard\n    UIList search field.':
        'Scrollable list of binary file lint issues. Filters by severity\n    («ERRORS only» toggle) and free-text search via the standard\n    UIList search field.',
    'Combined sub-panel внутри «Проверка»: переключатель сверху между\n    двумя режимами анализа — DFF/COL/TXD файлы или IDE/IPL карта.\n\n    Историческое имя ``GTATOOLS_PT_file_scanner`` оставлено, чтобы\n    layouts с ``bl_parent_id`` не сломались — содержание расширено\n    на два подрежима.':
        "Combined sub-panel inside «Validation»: top toggle between\n    two analysis modes — DFF/COL/TXD files or IDE/IPL map.\n\n    The historical name ``GTATOOLS_PT_file_scanner`` is kept so\n    layouts with ``bl_parent_id`` don't break — the content is\n    extended to two sub-modes.",
    'Result list for the Map Analyzer panel. Same shape as the file\n    scanner list but reads its own «Только ERROR» toggle from\n    ``gtatools_map_analyzer_only_errors`` so the two panels filter\n    independently.':
        'Result list for the Map Analyzer panel. Same shape as the file\n    scanner list but reads its own «ERRORS only» toggle from\n    ``gtatools_map_analyzer_only_errors`` so the two panels filter\n    independently.',
    'Frame Hierarchy Editor — компактное дерево фреймов активного\n    объекта + операторы для безопасного rename / set-parent / validate\n    против vanilla SA шаблонов (vehicle, ped). DFF-frame-list пишется\n    точно по этим именам, так что любая опечатка ломает поведение в\n    игре — лучше отловить здесь, чем после копирования в IMG.':
        'Frame Hierarchy Editor — compact tree of frames of the active\n    object + operators for safe rename / set-parent / validate against\n    vanilla SA templates (vehicle, ped). The DFF frame list is written\n    using exactly these names, so any typo breaks behavior in the\n    game — better caught here than after copying to IMG.',
    'Менеджер ID моделей GTA SA':
        'GTA SA Model ID Manager',
    'Lighting — общий контейнер для всех инструментов по работе со светом\n    и vertex colors. Объединяет 5 подпанелей (Prelight, Prelight COL,\n    Vertex Paint, LightMap, Itera Tools 3) под одним заголовком, чтобы не\n    раздувать N-sidebar пятью отдельными top-level панелями. Все дети\n    свёрнуты по умолчанию — юзер раскрывает только нужный.':
        "Lighting — common container for all light / vertex-color tools.\n    Bundles 5 sub-panels (Prelight, Prelight COL, Vertex Paint,\n    LightMap, Itera Tools 3) under one heading so the N-sidebar isn't\n    bloated with five separate top-level panels. All children are\n    collapsed by default — the user expands only what they need.",
    'Sub-panel: инструменты для работы со светом / vertex colors.':
        'Sub-panel: tools for working with light / vertex colors.',
    "Документация, баг-репорты и What's New — внизу панели":
        "Documentation, bug reports and What's New — at the bottom of the panel",
    'V-offset для Day vcol — применяется автоматически при изменении':
        'V-offset for Day vcol — applied automatically when changed',
    'V-offset для Night vcol — применяется автоматически при изменении':
        'V-offset for Night vcol — applied automatically when changed',
    'Из какой игры импортируем TXD. Auto — по RW-версии в chunk header':
        'Which game to import TXD from. Auto — by RW version in chunk header',
    'Имя пресета (буквы, цифры, дефис, подчёркивание, пробел)':
        'Preset name (letters, digits, hyphen, underscore, space)',
    'Описание':
        'Description',
    'Короткое описание (необязательно)':
        'Short description (optional)',
    'Имя нового профиля. Заменит существующий с тем же именем':
        'Name of the new profile. Replaces any existing one with the same name',
    'Короткая подсказка для tooltip в dropdown':
        'Short hint shown as tooltip in the dropdown',

    # ── Mobile TXD warning (txd_export.py) ──
    'TXD сохранён в PC формате. Для mobile конвертируй через TxdGen (PVRTC/ETC1).':
        'TXD saved in PC format. For mobile use TxdGen (PVRTC/ETC1) to convert.',

    # ── Empty-rig (Kams-style) animated map object (animobj_ops.py) ──
    "Префикс для имени Empty'ев: <base>_root + <base>_pivot. Совпадает с именем модели DFF/IFP":
        "Prefix for Empty names: <base>_root + <base>_pivot. Matches the DFF/IFP model name",
    'Имя Blender Action на pivot Empty — попадёт в IFP. Игра ищет анимацию по этому имени из IDE anim entry':
        "Blender Action name on the pivot Empty — written to IFP. The game looks up animations by this name in the IDE anim entry",
    'После Setup припарентите статичный меш к <base>_root,':
        'After Setup, parent the static mesh to <base>_root,',
    'а анимируемый — к <base>_pivot':
        'and the animated mesh to <base>_pivot',
    'Empty rig: ни один pivot не дал ключей — IFP не записан':
        'Empty rig: no pivot produced any keys — IFP was not written',
    'Не нашли root Empty — запустите Setup (Empty rig)':
        'No root Empty found — run Setup (Empty rig)',
    'Rig содержит только root — нужен хотя бы один pivot Empty':
        'Rig only contains a root — at least one pivot Empty is required',
    'Ни один pivot не имеет Action с keyframes':
        'No pivot has an Action with keyframes',
    'В rig нет меша — припарентите DFF меш к root или pivot':
        'Rig has no mesh — parent the DFF mesh to root or pivot',
    "Выделите объект rig'а":
        'Select an object in the rig',
    'Auto: ползунки сами пересчитывают keyframes цикла.\nManual: ползунки заморожены, ты сам ставишь keyframes':
        'Auto: sliders rebuild the cycle keyframes themselves.\nManual: sliders frozen, you place keyframes yourself',

    # ── UI buttons for both rig flavours (ui/panels.py) ──
    'Setup (skin)':
        'Setup (skin)',
    'Setup (Empty)':
        'Setup (Empty)',
    'Validate (skin)':
        'Validate (skin)',
    'Validate (Empty)':
        'Validate (Empty)',
    'Выдели MESH/Empty и нажми Setup (skin) или Setup (Empty)':
        'Select MESH/Empty and press Setup (skin) or Setup (Empty)',

    # ── Curve-based path workflow (path_curves.py + panels.py) ──
    'Меш не содержит рёбер — путь не построен':
        'Mesh has no edges — path was not built',
    'Не нашли цепочек путей в меше':
        'No path chains found in the mesh',
    'кривых построено':
        'curves built',
    'Куда сохранить nodes*.dat':
        'Where to save nodes*.dat',
    'Записать в расширенном FLA4 формате (для Fastman92 limit adjuster)':
        'Write in the extended FLA4 format (for Fastman92 limit adjuster)',
    'Выделите хотя бы одну Curve':
        'Select at least one Curve',
    'нод записано в':
        'nodes written to',
    'Curve workflow (Kams / ZZPuma):':
        'Curve workflow (Kams / ZZPuma):',
    'Меш → Curves':
        'Mesh → Curves',
    'Curves → .dat':
        'Curves → .dat',
    'Атрибуты:':
        'Attributes:',

    # ── ZZPuma-style extras: pathset, selection, bulk, accessories ──
    'Path set':
        'Path set',
    'Размер регионной сетки. 64 = vanilla SA. Большие значения требуют Fastman92 limit adjuster (FLA4)':
        'Region grid size. 64 = vanilla SA. Larger values require the Fastman92 limit adjuster (FLA4)',
    'Записать всю карту':
        'Write entire map',
    'Создать пустые nodes*.dat для всех регионов pathSet\'а, не только для тех где есть Curve\'ы. Vanilla SA требует наличия всех 64 файлов':
        "Emit empty nodes*.dat for every region in the pathSet, not only those that have Curves. Vanilla SA requires all 64 files to exist",
    'пустых':
        'empty',
    'ped Curve выделено':
        'ped Curves selected',
    'vehicle Curve выделено':
        'vehicle Curves selected',
    'Curve выделено':
        'Curves selected',
    'Curve перекрашено':
        'Curves recoloured',
    'Скопировано props:':
        'Props copied:',
    'Буфер пуст — сначала Pick на исходной Curve':
        'Clipboard is empty — Pick from a source Curve first',
    'Props применены к':
        'Props applied to',
    'Не менять':
        'Keep',
    'Включён':
        'Enabled',
    'Выключён':
        'Disabled',
    'Выключен':
        'Disabled',
    'Нет':
        'No',
    'Да':
        'Yes',
    'Spawn rate':
        'Spawn rate',
    'Spawn probability 0.0-1.0. Введи -1 чтобы не менять':
        'Spawn probability 0.0-1.0. Enter -1 to skip',
    'Width':
        'Width',
    'Path width. Введи -1 чтобы не менять':
        'Path width. Enter -1 to skip',
    'Highway':
        'Highway',
    'Boats':
        'Boats',
    'Parking':
        'Parking',
    'Traffic':
        'Traffic',
    'Bulk-set применён к':
        'Bulk-set applied to',

    # Accessories
    'TrafficLight':
        'TrafficLight',
    'RoadBlock':
        'RoadBlock',
    'Connector':
        'Connector',
    'SpecialNode':
        'SpecialNode',
    'Светофор: spawn\'ится на сегменте между knot и knot+1':
        'TrafficLight: spawned on the segment between knot and knot+1',
    'Дорожный блок копов на самом knot':
        'Police road block exactly at the knot',
    'Connector нода (для inter-region путей FLA4)':
        'Connector node (for inter-region paths in FLA4)',
    'Универсальный маркер для special-логики':
        'Universal marker for special-purpose logic',
    'Knot index':
        'Knot index',
    'Индекс knot\'а на родительской Curve (0-based)':
        'Knot index on the parent Curve (0-based)',
    'Создан':
        'Created',
    'Удалено accessory:':
        'Removed accessories:',

    # Auto-sync + debug
    'Auto-sync включён':
        'Auto-sync enabled',
    'Что показать':
        'What to show',
    'Node IDs':
        'Node IDs',
    'Navi IDs':
        'Navi IDs',
    'Выключить всё':
        'Turn everything off',

    # UI labels for new buttons
    'Peds':
        'Peds',
    'Vehs':
        'Vehs',
    'Все':
        'All',
    'Pick':
        'Pick',
    'Apply':
        'Apply',
    'Bulk':
        'Bulk',
    'Colors':
        'Colors',
    '+TL/RB/CO':
        '+TL/RB/CO',
    'Удалить':
        'Remove',
    'Sync':
        'Sync',
    'Off':
        'Off',
    'Тип':
        'Type',

    # ── Operator tooltips (bl_description from docstrings) ──
    'Выделить все Curve-пути типа Ped (sapath_type=1)':
        'Select all Curve paths of type Ped (sapath_type=1)',
    'Выделить все Curve-пути типа Vehicle (sapath_type=2)':
        'Select all Curve paths of type Vehicle (sapath_type=2)',
    'Выделить все Curve-пути с sapath_* свойствами':
        'Select every Curve path that carries sapath_* properties',
    'Перекрасить wireframe выделенных Curve-путей по их типу/флагам':
        'Recolour wireframe of the selected Curve paths according to their type/flags',
    'Скопировать sapath_* свойства активной Curve во внутренний буфер':
        "Copy sapath_* properties of the active Curve into the addon's clipboard",
    'Применить ранее скопированные sapath_* к выделенным Curve':
        'Apply the previously picked sapath_* properties to every selected Curve',
    'Bulk-set sapath_* свойств для всех выделенных Curve.\n\n    Опции с -1 / 0 значением «не менять». Полезно для разом установить\n    type=Vehicle + traffic=enabled + spawn=1.0 на массу путей после\n    импорта или ручной правки.':
        "Bulk-set sapath_* properties on all selected Curves.\n\n    Options with a -1 / 0 value mean «keep as is». Handy for setting\n    type=Vehicle + traffic=enabled + spawn=1.0 on lots of paths after\n    import or manual edits in one go.",
    'Добавить TrafficLight / RoadBlock / Connector / SpecialNode на\n    активный knot выделенной Curve.':
        'Add a TrafficLight / RoadBlock / Connector / SpecialNode on the\n    active knot of the selected Curve.',
    'Удалить выделенные path accessory объекты':
        'Remove the selected path accessory objects',
    "Включить фоновую синхронизацию позиций path accessory'ев\n    с их родительскими Curve'ами":
        'Enable background sync of path accessory positions\n    with their parent Curves',
    'Включить/выключить debug overlay для путей (NodeID/AreaID на нодах)':
        'Toggle the path debug overlay (NodeID/AreaID labels on nodes)',
    'Создать Empty-rig для animated map object в стиле Kams скриптов:\n    два Empty (root + pivot) с user-prop BoneID и циклической Action на\n    pivot. Меши парентится вручную — статичные к root, анимируемые к pivot.\n    Не требует armature/skin — обходит rest_quat баг bone-flow.':
        "Build an Empty-based rig for an animated map object, Kams-style:\n    two Empty objects (root + pivot) with a BoneID user-prop and a cyclic\n    Action on the pivot. Meshes are parented manually — static to root,\n    animated to pivot. Skips the armature/skin path and side-steps the\n    rest_quat bug of the bone flow.",
    'Проверить Empty-rig: есть ли root + pivot, корректные BoneID,\n    Action на pivot, припарентенные меши. Сообщает первую ошибку.':
        'Validate an Empty-rig: presence of root + pivot, correct BoneIDs,\n    Action on the pivot, parented meshes. Reports the first issue found.',

    # Pre-existing armature-rig animobj docstrings (English fill-ins)
    'Создать рiг для animated map object (мельница, кран, флюгер):\n    Armature с одной костью + Action с цикличной Z-вращением.\n\n    Все вершины активного меша автоматически привязываются к\n    единственной кости (vertex group weight=1.0). Готово к экспорту в\n    DFF + IFP без ручной настройки скелета.':
        'Build a rig for an animated map object (windmill, crane, vane):\n    a single-bone Armature + an Action with a cyclic Z rotation.\n\n    Every vertex of the active mesh is automatically weighted to the\n    sole bone (vertex group weight=1.0). Ready for DFF + IFP export\n    without any manual skeleton setup.',
    'Проверить настройку animated map object перед экспортом:\n    есть ли armature, привязка ли все, единая ли кость, есть ли action,\n    нормальные ли ID. Все находки в System Console.':
        'Validate the animated map object setup before export:\n    armature present, all vertices weighted, single bone, Action present,\n    sensible IDs. Findings are printed to the System Console.',
    'Экспортировать animated map object одним кликом: пишет\n    <base>.dff + <base>.ifp в выбранную папку. Опционально дописывает\n    или обновляет anim-запись в указанном IDE-файле.':
        'Export an animated map object in one click: writes\n    <base>.dff + <base>.ifp to the chosen folder. Optionally appends\n    or updates the anim entry in the specified IDE file.',

    # ── Empty-rig setup: auto-parent option + sanity warnings ──
    'Активный меш':
        'Active mesh',
    'Что сделать с активным меш-объектом после Setup:\n  Pivot — припарентить к pivot (будет крутиться вместе с rig\'ом)\n  Root  — припарентить к root (останется статичным как \'основание\')\n  Нет   — не трогать':
        "What to do with the active mesh after Setup:\n  Pivot — parent to pivot (mesh follows the rotating rig)\n  Root  — parent to root (mesh stays static as a base)\n  Нет   — leave the mesh alone",
    'Парентить к pivot':
        'Parent to pivot',
    'Парентить к root':
        'Parent to root',
    'Не парентить':
        'Do not parent',
    'Меш будет крутиться вместе с pivot':
        'The mesh will rotate with the pivot',
    'Меш остаётся статичным как основание':
        'The mesh stays static as the base',
    'Не трогать активный меш':
        'Leave the active mesh alone',
    'Этот меш скиннирован (Armature). Empty-rig для map-объектов, не персонажей':
        'This mesh is skinned (Armature). Empty-rig is for map objects, not characters',
    'Для персонажей используй Setup (skin) + Character Animation':
        'For characters use Setup (skin) + Character Animation',

    # ── Post-setup parenting helpers ──
    "Припарентить выделенные меши к pivot Empty-rig'а — меш будет\n    крутиться вместе с rig'ом. Если rig'ов несколько, используется\n    тот в иерархии которого уже находится активный объект.":
        'Parent selected meshes to the rig pivot — they will rotate with\n    the rig. If several rigs exist, the one containing the active\n    object is preferred.',
    "Припарентить выделенные меши к root Empty-rig'а — они останутся\n    статичными как 'основание' (как корпус мельницы без лопастей).":
        "Parent selected meshes to the rig root — they stay static as the\n    base (e.g. the windmill body without its blades).",
    "В сцене нет Empty-rig'а — сначала Setup (Empty)":
        'No Empty-rig in the scene — run Setup (Empty) first',
    "У rig'а нет pivot Empty":
        'The rig has no pivot Empty',
    'меш(а) припарентено к':
        'mesh(es) parented to',

    # ── Panel labels for child counts + parenting buttons ──
    'Меш под pivot:':
        'Meshes under pivot:',
    'под root:':
        'under root:',
    'Pivot пустой — анимация не будет видна. Выдели меш и нажми «К pivot»':
        'Pivot has no mesh — animation will not be visible. Select a mesh and press «To pivot»',
    'К pivot':
        'To pivot',
    'К root':
        'To root',

    # ── Add Pivot operator (multi-part rigs) ──
    "Добавить ещё один pivot Empty в существующий Empty-rig — для\n    моделей с несколькими анимированными частями (например мельница +\n    противовес). Каждому pivot'у выдаётся свой BoneID и Action.\n\n    Если выделен меш — он сразу парентится к новому pivot'у.\n    Если выделена кость старого pivot'а или root — новый pivot\n    создаётся как ребёнок root'а того же rig'а.":
        'Add another pivot Empty to an existing Empty-rig — for models\n    with several animated parts (e.g. windmill + counterweight). Each\n    pivot gets its own BoneID and Action.\n\n    If a mesh is active — it is parented to the new pivot immediately.\n    If a previous pivot or root is active — the new pivot is created\n    as a child of the same rig root.',
    "Имя pivot'а":
        'Pivot name',
    "Суффикс для нового Empty: <rig>_<name>. Имя action автоматически берётся таким же":
        'Suffix for the new Empty: <rig>_<name>. The Action name is taken from this too',
    'Припарентить активный меш':
        'Parent active mesh',
    'Сразу подвесить активный меш под новый pivot':
        'Immediately hang the active mesh under the new pivot',
    '+Pivot':
        '+Pivot',
    "Структура rig'а:":
        'Rig structure:',

    # ── Orphan-mesh panel (when a non-rig mesh is active and a rig exists) ──
    "Меш вне rig'а:":
        'Mesh outside rig:',
    "Этот меш не входит в иерархию rig'а. Прикрепи его:":
        'This mesh is not part of any rig hierarchy. Attach it:',
    'К pivot (анимирован)':
        'To pivot (animated)',
    'К root (статика)':
        'To root (static)',
    'Target rig:':
        'Target rig:',

    # ── Multi-select Setup hint ──
    'Других мешей в выделении (→ root):':
        'Other meshes in selection (→ root):',

    # ── Cleaned-up Setup/Validate labels (armature flow removed) ──
    'Setup':
        'Setup',
    'Validate':
        'Validate',
    'Выдели меш и нажми Setup':
        'Select a mesh and press Setup',
    'Выбери меш пипеткой выше — rig создастся автоматически':
        'Pick a mesh with the eyedropper above — the rig will be created automatically',

    'Статика:':
        'Static:',
    'Пипеткой выбери анимированную часть ↓':
        'Pick the animated part with the eyedropper ↓',
    'Выдели меш-основание (станет статикой)':
        'Select a base mesh (will become the static part)',

    # ── Eyedropper picker for adding meshes to rig ──
    'Куда добавить':
        'Where to add',
    'Куда привесить выбранный меш:\n  К pivot — на первый pivot (анимация общая со всем pivot\'ом)\n  Новый pivot — создать отдельный pivot с собственной анимацией\n  К root — статичная часть без анимации':
        "Where to attach the picked mesh:\n  To pivot — to the first pivot (shares animation with that pivot)\n  New pivot — create a fresh pivot with its own animation\n  To root — static part with no animation",
    'Новый pivot':
        'New pivot',
    'Создать новый pivot и привесить меш к нему':
        'Create a new pivot and parent the mesh to it',
    'К существующему pivot':
        'To existing pivot',
    "Парентить к первому pivot'у (одна анимация на всех)":
        'Parent to the first pivot (one shared animation)',
    'К root (статика)':
        'To root (static)',
    'Статичная часть, не будет крутиться':
        'Static part — will not rotate',
    'Меш':
        'Mesh',
    'Кликни на пипетку и выбери меш в сцене или 3D-окне. Он автоматически добавится в rig согласно выбору «Куда добавить»':
        'Click the eyedropper and pick a mesh in the scene or 3D viewport. It will be attached to the rig according to «Where to add»',
    'Добавить меш в rig:':
        'Add mesh to rig:',
    'Или возьми пипеткой:':
        'Or use the eyedropper:',
    # === TXD per-mesh export strings (2026-05-18) ===
    'Не удалось экспортировать ни одного TXD':
        'Failed to export any TXD',
    'TXD записано в':
        'TXDs written to',
    'с ошибками':
        'with errors',

    # === v2.0.0 misc gaps ===
    'Action Editor':
        'Action Editor',
    'Damage variants:':
        'Damage variants:',
    'FLA4':
        'FLA4',
    'Ped':
        'Ped',
    'Used by':
        'Used by',
    'Vehicle':
        'Vehicle',
    "В сцене нет Empty-rig'а — сначала Setup":
        "No Empty-rig in scene — run Setup first",
    "Нет анимированных pivot'ов — IFP будет пустой":
        "No animated pivots — IFP would be empty",

    # === weight_paint_ops.py (Py 3.11 f-string fix) ===
    "Backup '{n}' исчез (вероятно Undo). ":
        "Backup '{n}' disappeared (Undo'd?). ",
    'Тэг очищен, текущая геометрия принята как есть. ':
        'Tag cleared, current geometry kept as-is. ',
    'Тэг очищен, текущая геометрия принята как есть.':
        'Tag cleared, current geometry kept as-is.',
    'Изменения весов сделанные после Undo сохранены.':
        'Weight changes made after Undo are preserved.',

    # === animobj_export — explicit existing-IFP picker ===
    'Дополнить файл':
        'Append to file',
    'Существующий IFP (опционально)':
        'Existing IFP (optional)',
    "Указать конкретный .ifp файл куда дополнить анимацию. Когда задан — игнорируется «Папка» и «Имя IFP», анимация пишется СЮДА. Удобно для merge'а в <game>/anim/myhood.ifp или подобных общих файлов вне папки экспорта DFF":
        "Pick a specific .ifp file to append the animation into. When set, «Folder» and «IFP name» are ignored — the animation goes HERE. Useful for merging into <game>/anim/myhood.ifp or other shared files outside the DFF export folder",

}
