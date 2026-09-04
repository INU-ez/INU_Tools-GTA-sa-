# INU_tools.core.timecyc — чтение/запись GTA SA timecyc.dat (и timecycp.dat).
#
# Формат: текстовый файл из блоков погоды. Каждый блок —
#
#     //////////// EXTRASUNNY_LA
#     //Amb  Amb_Obj  Dir  Sky top  Sky bot  ...           <- шапка колонок
#     //Midnight
#     22 22 22   220 212 130   ...                         <- строка данных
#     //5AM
#     ...
#     //
#
# Ровно 8 строк данных на блок — временны́е срезы 0/5/6/7/12/19/20/22 ч.
# Игра линейно интерполирует между соседними срезами (22 → 0 через
# полночь), поэтому «час» — непрерывная величина, а правится всегда
# конкретный срез.
#
# Ширина строки (проверено на реальных файлах, не по вики):
#   51 — ванильный SA: Dir RGB есть, хвост из трёх (CloudAlpha,
#        HighLightMinIntensity, WaterFogAlpha);
#   52 — сборки с четвёртым хвостовым DirectionalMult (Project Eagle TC);
#   49 — без Dir RGB;
#   короче — попадается и в ванилле (одна строка), и в модах (в Project
#        Eagle весь блок UNDERWATER на значение короче).
# Поэтому схема выбирается по САМОЙ ШИРОКОЙ строке файла, недостающий
# хвост отдельной строки добивается дефолтами, а исходная ширина
# запоминается — при экспорте лишняя колонка не дописывается.
#
# Экспорт байт-в-байт для нетронутых строк: writer отдаёт оригинальную
# строку, если срез не помечен dirty. Дифф файла = только правки.

import os
import re


# ── Временны́е срезы ─────────────────────────────────────────────────

SLOT_HOURS = (0, 5, 6, 7, 12, 19, 20, 22)
SLOT_LABELS = ("Midnight", "5AM", "6AM", "7AM", "Midday", "7PM", "8PM", "10PM")
SLOTS = len(SLOT_HOURS)


# ── Схема полей ─────────────────────────────────────────────────────
#
# (key, size, kind, fmt)
#   size — сколько чисел подряд;
#   kind — 'rgb' / 'rgba' / 'argb' (альфа ПЕРВОЙ — так лежат PostFX) / 'num';
#   fmt  — 'i' целое, 'f' с двумя знаками после точки.

_FIELDS_CORE = [
    ('amb',             3, 'rgb',  'i'),
    ('amb_obj',         3, 'rgb',  'i'),
    ('sky_top',         3, 'rgb',  'i'),
    ('sky_bot',         3, 'rgb',  'i'),
    ('sun_core',        3, 'rgb',  'i'),
    ('sun_corona',      3, 'rgb',  'i'),
    ('sun_size',        1, 'num',  'f'),
    ('spr_size',        1, 'num',  'f'),
    ('spr_bright',      1, 'num',  'f'),
    ('shadow',          1, 'num',  'i'),
    ('light_shad',      1, 'num',  'i'),
    ('pole_shad',       1, 'num',  'i'),
    ('far_clip',        1, 'num',  'f'),
    ('fog_start',       1, 'num',  'f'),
    ('light_on_ground', 1, 'num',  'f'),
    ('low_clouds',      3, 'rgb',  'i'),
    ('bottom_clouds',   3, 'rgb',  'i'),
    ('water',           4, 'rgba', 'i'),
    ('postfx1',         4, 'argb', 'i'),
    ('postfx2',         4, 'argb', 'i'),
    ('cloud_alpha',     1, 'num',  'i'),
    ('highlight_min',   1, 'num',  'i'),
    ('water_fog',       1, 'num',  'i'),
    ('dir_mult',        1, 'num',  'f'),
]

_DIR_FIELD = ('dir', 3, 'rgb', 'i')

# Чем добивается хвост, которого в строке не оказалось. Ноль подходит
# почти всем, но белый Dir и dir_mult=1 — нейтральные значения, при
# которых отсутствующая колонка не гасит освещение.
_DEFAULTS = {
    'dir':      [255.0, 255.0, 255.0],
    'dir_mult': [1.0],
}

# Человекочитаемые подписи — их же показывает панель.
FIELD_LABELS = {
    'amb':             "Ambient (мир)",
    'amb_obj':         "Ambient (объекты)",
    'dir':             "Directional",
    'sky_top':         "Небо: зенит",
    'sky_bot':         "Небо: горизонт",
    'sun_core':        "Солнце: ядро",
    'sun_corona':      "Солнце: корона",
    'sun_size':        "Размер солнца",
    'spr_size':        "Размер блика",
    'spr_bright':      "Яркость блика",
    'shadow':          "Тени",
    'light_shad':      "Тени от света",
    'pole_shad':       "Тени столбов",
    'far_clip':        "Дальность прорисовки",
    'fog_start':       "Начало тумана",
    'light_on_ground': "Свет на земле",
    'low_clouds':      "Нижние облака",
    'bottom_clouds':   "Облака у горизонта",
    'water':           "Вода (RGBA)",
    'postfx1':         "PostFX 1 (ARGB)",
    'postfx2':         "PostFX 2 (ARGB)",
    'cloud_alpha':     "Прозрачность облаков",
    'highlight_min':   "Мин. яркость бликов",
    'water_fog':       "Туман под водой",
    'dir_mult':        "Множитель directional",
}


def schema_for(width):
    """Список полей под файл, самая широкая строка которого — `width`
    чисел. 50+ → есть Dir RGB (ваниль SA и всё, что от неё пошло),
    иначе ванильная схема без Dir."""
    fields = list(_FIELDS_CORE)
    if width >= 50:
        fields.insert(2, _DIR_FIELD)
    return fields


def schema_width(fields):
    return sum(f[1] for f in fields)


# ── Цвет ────────────────────────────────────────────────────────────

def srgb_to_linear(c):
    """0..1 sRGB → scene-linear. Blender рисует color-свотчи и считает
    шейдеры в линейном пространстве, а в timecyc лежат sRGB-байты —
    без конверсии цвет в панели светлее игрового."""
    c = min(max(float(c), 0.0), 1.0)
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(c):
    c = min(max(float(c), 0.0), 1.0)
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def byte_to_linear(b):
    return srgb_to_linear(float(b) / 255.0)


def linear_to_byte(c):
    return int(round(min(max(linear_to_srgb(c), 0.0), 1.0) * 255.0))


# ── Модель данных ───────────────────────────────────────────────────

class TimecycSlot:
    """Один временно́й срез одной погоды."""

    __slots__ = ('values', 'raw', 'width', 'dirty')

    def __init__(self, values, raw, width):
        self.values = values      # {key: [float, ...]}
        self.raw = raw            # исходная строка без перевода строки
        self.width = width        # сколько чисел было в файле
        self.dirty = False

    def get(self, key, default=0.0):
        v = self.values.get(key)
        if not v:
            return default
        return v[0] if len(v) == 1 else list(v)

    def set(self, key, value):
        if key not in self.values:
            return
        seq = value if isinstance(value, (list, tuple)) else (value,)
        cur = self.values[key]
        new = [float(x) for x in seq][:len(cur)]
        while len(new) < len(cur):
            new.append(cur[len(new)])
        if new != cur:
            self.values[key] = new
            self.dirty = True

    def copy_from(self, other):
        for key, val in other.values.items():
            if key in self.values:
                self.set(key, list(val))


class TimecycWeather:
    __slots__ = ('name', 'slots')

    def __init__(self, name):
        self.name = name
        self.slots = []


class TimecycFile:
    """Разобранный timecyc.dat, помнящий исходные строки файла."""

    def __init__(self, path=''):
        self.path = path
        self.lines = []        # исходные строки, без перевода строки
        self.newline = '\r\n'  # как файл был свёрстан — так и запишем
        self.weathers = []
        self.fields = list(_FIELDS_CORE)
        self.width = 49
        # line_index → (weather_idx, slot_idx)
        self.line_map = {}

    # -- запросы -----------------------------------------------------

    @property
    def weather_names(self):
        return [w.name for w in self.weathers]

    def has_field(self, key):
        return any(f[0] == key for f in self.fields)

    def slot(self, weather_idx, slot_idx):
        try:
            return self.weathers[weather_idx].slots[slot_idx]
        except IndexError:
            return None

    def is_dirty(self):
        return any(s.dirty for w in self.weathers for s in w.slots)

    def dirty_count(self):
        return sum(1 for w in self.weathers for s in w.slots if s.dirty)

    def interpolate(self, weather_idx, hour):
        """Значения погоды на произвольный час — как в игре: линейно
        между соседними срезами, 22 ч → 0 ч через полночь."""
        try:
            slots = self.weathers[weather_idx].slots
        except IndexError:
            return {}
        if not slots:
            return {}
        if len(slots) < 2:
            return {k: list(v) for k, v in slots[0].values.items()}

        n = min(len(slots), SLOTS)
        hour = float(hour) % 24.0
        lo = n - 1
        for i in range(n):
            if hour < SLOT_HOURS[i]:
                lo = i - 1
                break
        if lo < 0:
            lo = n - 1
        hi = (lo + 1) % n

        span = (SLOT_HOURS[hi] - SLOT_HOURS[lo]) % 24
        if span == 0:
            t = 0.0
        else:
            t = min(max(((hour - SLOT_HOURS[lo]) % 24) / span, 0.0), 1.0)

        a, b = slots[lo].values, slots[hi].values
        out = {}
        for key, va in a.items():
            vb = b.get(key, va)
            out[key] = [x + (y - x) * t for x, y in zip(va, vb)]
        return out


# ── Парсинг ─────────────────────────────────────────────────────────

_WEATHER_RE = re.compile(r'^\s*/{4,}\s*([^/\s].*?)\s*$')
_NUM_RE = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')


def _parse_values(tokens, fields):
    """Числа строки → {key: [...]}; хвост, которого нет, — из _DEFAULTS."""
    values = {}
    pos = 0
    for key, size, _kind, _fmt in fields:
        chunk = list(tokens[pos:pos + size])
        if len(chunk) < size:
            fallback = _DEFAULTS.get(key, [0.0] * size)
            while len(chunk) < size:
                chunk.append(fallback[len(chunk)] if len(chunk) < len(fallback) else 0.0)
        values[key] = chunk
        pos += size
    return values


def parse(path):
    """Читает timecyc.dat. Бросает ValueError, если блоков не нашлось."""
    # newline='' — переводы строк не трогаем, чтобы вернуть файл в
    # игровую папку ровно в том виде (CRLF в ванилле), в каком взяли.
    with open(path, 'r', encoding='utf-8', errors='replace', newline='') as fh:
        text = fh.read()

    cyc = TimecycFile(path)
    cyc.newline = '\r\n' if '\r\n' in text else '\n'
    cyc.lines = text.replace('\r\n', '\n').split('\n')

    # Ширину схемы берём по самой широкой строке данных: узкие блоки
    # (UNDERWATER, битая строка в ванилле) не должны переключить весь
    # файл на схему без Dir и сдвинуть все поля.
    width = 0
    for line in cyc.lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('//'):
            continue
        width = max(width, len(_NUM_RE.findall(line)))
    if width == 0:
        raise ValueError("timecyc: строк с данными не найдено")

    cyc.width = width
    cyc.fields = schema_for(width)

    current = None
    for idx, line in enumerate(cyc.lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('//'):
            m = _WEATHER_RE.match(line)
            if m:
                current = TimecycWeather(m.group(1))
                cyc.weathers.append(current)
            continue

        tokens = [float(t) for t in _NUM_RE.findall(line)]
        if not tokens:
            continue
        if current is None:
            # Данные до первого заголовка — заводим безымянный блок.
            current = TimecycWeather("WEATHER_%d" % len(cyc.weathers))
            cyc.weathers.append(current)
        slot = TimecycSlot(_parse_values(tokens, cyc.fields), line, len(tokens))
        current.slots.append(slot)
        cyc.line_map[idx] = (len(cyc.weathers) - 1, len(current.slots) - 1)

    if not cyc.weathers:
        raise ValueError("timecyc: блоков погоды не найдено")
    return cyc


# ── PostFX (цветофильтр кадра) ──────────────────────────────────────
#
# Два ARGB-слоя из timecyc — это полноэкранный фильтр, который игра
# накладывает на ГОТОВЫЙ кадр:
#
#     PC/Xbox: out = in + in*rgb1*alpha1 + in*rgb2*alpha2
#     PS2:     out = in*rgb1*2 + in*rgb2*2*alpha2*2
#
# То есть кадр умножается покомпонентно на (1 + rgb1*a1 + rgb2*a2). Для
# ванильного полдня это ≈ (1.58, 1.82, 1.82): картинка заметно светлеет
# и уходит в голубизну. Без него превью выглядит темнее и синее игры —
# особенно небо, где эффект виден чище всего.
#
# Умножение идёт по значениям кадра, то есть в gamma-пространстве, а не
# в linear — вызывающий обязан это учесть.


def postfx_gain(values, ps2=False):
    """Множитель кадра (kr, kg, kb) из PostFX1/PostFX2 среза."""
    def _layer(key):
        v = values.get(key)
        if not v or len(v) < 4:
            return 0.0, (0.0, 0.0, 0.0)
        # ARGB: альфа первой.
        alpha = min(max(v[0] / 255.0, 0.0), 1.0)
        rgb = tuple(min(max(c / 255.0, 0.0), 1.0) for c in v[1:4])
        return alpha, rgb

    a1, rgb1 = _layer('postfx1')
    a2, rgb2 = _layer('postfx2')

    if ps2:
        # PS2 blend: обе стадии удваиваются, вклад второй ещё и по альфе.
        return tuple(rgb1[i] * 2.0 + rgb2[i] * 2.0 * a2 * 2.0
                     for i in range(3))
    return tuple(1.0 + rgb1[i] * a1 + rgb2[i] * a2 for i in range(3))


def apply_gain_srgb(linear_rgb, gain):
    """Применить множитель кадра к linear-цвету.

    Фильтр работает по значениям кадра (gamma-пространство), поэтому
    цвет разворачивается в sRGB, множится и сворачивается обратно —
    иначе осветление выходит заметно грубее игрового."""
    out = []
    for c, k in zip(linear_rgb, gain):
        v = linear_to_srgb(c) * float(k)
        out.append(srgb_to_linear(min(max(v, 0.0), 1.0)))
    return tuple(out)


# ── Баланс дневного / ночного прилайта ──────────────────────────────
#
# В SA ночные вершинные цвета лежат отдельной секцией (Extra Vert
# Colour), а движок держит в геометрии параметр dnParam и пишет в
# preLitLum смесь:
#
#     preLit = day * (1 - dnParam) + night * dnParam
#
# (CCustomBuildingDNPipeline::SetPrelitColors). Сам dnParam качается по
# игровым суткам; смена дневного набора на ночной приходится на 20:00 →
# 21:00 — те же часы, когда зажигаются фонари и фары. Утренний порог
# берём по срезам timecyc (05:00 → 06:00, ночь → рассвет); границы
# вынесены в параметры, потому что в модах сутки перекраивают.

DUSK_START, DUSK_END = 20.0, 21.0
DAWN_START, DAWN_END = 5.0, 6.0


def night_balance(hour, dusk_start=DUSK_START, dusk_end=DUSK_END,
                  dawn_start=DAWN_START, dawn_end=DAWN_END):
    """dnParam для часа: 0.0 — чистый Day, 1.0 — чистый Night."""
    hour = float(hour) % 24.0

    def _ramp(h, start, end):
        span = end - start
        if span <= 0.0:
            return None if h < start else 1.0
        if h < start:
            return None
        if h >= end:
            return 1.0
        return (h - start) / span

    # Рассвет: ночь → день.
    if dawn_start <= hour < dawn_end:
        t = _ramp(hour, dawn_start, dawn_end)
        return 1.0 - (t if t is not None else 1.0)
    # Закат: день → ночь.
    if dusk_start <= hour < dusk_end:
        t = _ramp(hour, dusk_start, dusk_end)
        return t if t is not None else 1.0
    # День — между концом рассвета и началом заката.
    if dawn_end <= hour < dusk_start:
        return 0.0
    return 1.0


def revert_slot(cyc, slot):
    """Вернуть срез к содержимому его исходной строки файла."""
    tokens = [float(t) for t in _NUM_RE.findall(slot.raw)]
    slot.values = _parse_values(tokens, cyc.fields)
    slot.width = len(tokens) or slot.width
    slot.dirty = False
    return slot


# ── Запись ──────────────────────────────────────────────────────────

def _fmt_num(value, fmt):
    if fmt == 'i':
        return str(int(round(value)))
    return "%.2f" % value


def format_slot(slot, fields):
    """Строка данных из значений среза: группы через таб, числа внутри
    группы через пробел. Ширина обрезается до исходной, чтобы в
    укороченном блоке не появилась лишняя колонка."""
    groups = []
    written = 0
    for key, size, _kind, fmt in fields:
        if written >= slot.width:
            break
        vals = slot.values.get(key, [0.0] * size)
        take = min(size, slot.width - written)
        groups.append(' '.join(_fmt_num(v, fmt) for v in vals[:take]))
        written += take
    return '\t'.join(groups)


def write(cyc, path=None, backup=True):
    """Пишет файл. Нетронутые строки уходят байт-в-байт.

    Рядом кладётся `.bak` прошлой версии — правки timecyc делаются в
    живой игровой папке, и откатиться должно быть чем."""
    target = path or cyc.path
    if not target:
        raise ValueError("timecyc: не задан путь для записи")

    out = []
    for idx, line in enumerate(cyc.lines):
        ref = cyc.line_map.get(idx)
        if ref is None:
            out.append(line)
            continue
        weather_idx, slot_idx = ref
        slot = cyc.weathers[weather_idx].slots[slot_idx]
        out.append(format_slot(slot, cyc.fields) if slot.dirty else slot.raw)

    tmp = target + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(cyc.newline.join(out))

    if backup and os.path.exists(target):
        bak = target + '.bak'
        try:
            if os.path.exists(bak):
                os.remove(bak)
            os.replace(target, bak)
        except OSError:
            pass
    os.replace(tmp, target)

    # Файл на диске теперь совпадает с моделью — сбрасываем dirty и
    # переносим отформатированный текст в raw, чтобы следующая запись
    # снова была байт-в-байт для нетронутых строк.
    for weather in cyc.weathers:
        for slot in weather.slots:
            if slot.dirty:
                slot.raw = format_slot(slot, cyc.fields)
                slot.dirty = False
    cyc.path = target
    cyc.lines = out
    return target
