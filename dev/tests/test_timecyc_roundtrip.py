"""Round-trip tests for core/timecyc.py — GTA SA timecyc.dat.

Проверяем то, ради чего парсер и писался:
  * схема выбирается по самой широкой строке файла (ваниль SA — 51
    значение с Dir RGB, сборки с DirectionalMult — 52, старые — 49);
  * нетронутый файл переписывается байт-в-байт, включая CRLF;
  * правка одного среза меняет ровно одну строку;
  * укороченная строка (в ванилле такая есть в UNDERWATER) не теряет и
    не приобретает колонок;
  * интерполяция по часу совпадает с игровой: линейно между соседними
    срезами, 22 → 0 через полночь.

Pure Python."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core import timecyc as tc  # noqa: E402


# ── Синтетический файл в формате ванильного SA ───────────────────────

HEADER = "//Amb\tAmb_Obj\tDir\tSky top\tSky bot\tSunCore\tSunCorona\tSunSz"


def _row(sky_top, sky_bot, far_clip, extra_tail=False):
    """Строка данных: 51 значение (ваниль) или 52 (с DirectionalMult)."""
    vals = [
        "22 22 22",                       # amb
        "220 212 130",                    # amb_obj
        "255 255 255",                    # dir
        "%d %d %d" % sky_top,             # sky top
        "%d %d %d" % sky_bot,             # sky bot
        "255 128 0",                      # sun core
        "5 0 0",                          # sun corona
        "1.00 1.00 0.30",                 # sunsz sprsz sprbght
        "200 100 0",                      # shdw lightshd poleshd
        "%.2f 100.00 1.00" % far_clip,    # farclp fogst lightonground
        "30 20 0",                        # low clouds
        "3 3 3",                          # bottom clouds
        "85 85 65 240",                   # water rgba
        "255 87 87 87",                   # postfx1 argb
        "255 60 121 122",                 # postfx2 argb
        "0 90 0" + (" 1.00" if extra_tail else ""),
    ]
    return "\t".join(vals)


def _make_file(tmp_path, name="timecyc.dat", extra_tail=False,
               short_block=False, newline="\r\n"):
    lines = []
    for w, weather in enumerate(("EXTRASUNNY_LA", "RAINY_SF", "UNDERWATER")):
        lines.append("//////////// " + weather)
        lines.append(HEADER)
        for s, label in enumerate(tc.SLOT_LABELS):
            lines.append("//" + label)
            row = _row((10 + w, 20 + s, 30), (40, 50, 60), 400.0 + 10 * s,
                       extra_tail=extra_tail)
            if short_block and weather == "UNDERWATER":
                # Как в ванилле: у блока обрезан хвост.
                row = row.rsplit("\t", 1)[0]
            lines.append(row)
        lines.append("//")

    path = tmp_path / name
    path.write_bytes(newline.join(lines).encode("utf-8"))
    return path


# ── Разбор ───────────────────────────────────────────────────────────

def test_parse_vanilla_shape(tmp_path):
    cyc = tc.parse(str(_make_file(tmp_path)))
    assert [w.name for w in cyc.weathers] == [
        "EXTRASUNNY_LA", "RAINY_SF", "UNDERWATER"]
    assert all(len(w.slots) == 8 for w in cyc.weathers)
    assert cyc.width == 51
    assert cyc.has_field('dir')
    assert cyc.newline == "\r\n"


def test_parse_extended_width_keeps_dir_mult(tmp_path):
    cyc = tc.parse(str(_make_file(tmp_path, extra_tail=True)))
    assert cyc.width == 52
    assert cyc.slot(0, 0).get('dir_mult') == 1.0


def test_missing_tail_falls_back_to_neutral_dir_mult(tmp_path):
    """В ванильной ширине 51 колонки DirectionalMult нет вовсе —
    подставляется 1.0, а не 0, иначе превью гасит солнце."""
    cyc = tc.parse(str(_make_file(tmp_path)))
    assert cyc.slot(0, 0).get('dir_mult') == 1.0


def test_field_offsets(tmp_path):
    cyc = tc.parse(str(_make_file(tmp_path)))
    slot = cyc.slot(0, 3)
    assert slot.get('amb') == [22.0, 22.0, 22.0]
    assert slot.get('dir') == [255.0, 255.0, 255.0]
    assert slot.get('sky_top') == [10.0, 23.0, 30.0]
    assert slot.get('sky_bot') == [40.0, 50.0, 60.0]
    assert slot.get('far_clip') == 430.0
    assert slot.get('water') == [85.0, 85.0, 65.0, 240.0]
    assert slot.get('postfx1') == [255.0, 87.0, 87.0, 87.0]
    assert slot.get('cloud_alpha') == 0.0
    assert slot.get('highlight_min') == 90.0


# ── Запись ───────────────────────────────────────────────────────────

def test_untouched_write_is_byte_identical(tmp_path):
    path = _make_file(tmp_path)
    before = path.read_bytes()
    cyc = tc.parse(str(path))
    tc.write(cyc, backup=False)
    assert path.read_bytes() == before


def test_lf_file_stays_lf(tmp_path):
    path = _make_file(tmp_path, newline="\n")
    before = path.read_bytes()
    cyc = tc.parse(str(path))
    assert cyc.newline == "\n"
    tc.write(cyc, backup=False)
    assert path.read_bytes() == before


def test_edit_touches_only_its_own_line(tmp_path):
    path = _make_file(tmp_path)
    before = path.read_bytes().split(b"\r\n")

    cyc = tc.parse(str(path))
    cyc.slot(1, 4).set('sky_top', [1, 2, 3])
    assert cyc.dirty_count() == 1
    tc.write(cyc, backup=False)

    after = path.read_bytes().split(b"\r\n")
    assert len(before) == len(after)
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert len(changed) == 1

    reread = tc.parse(str(path))
    assert reread.slot(1, 4).get('sky_top') == [1.0, 2.0, 3.0]
    assert reread.slot(1, 3).get('sky_top') == cyc.slot(1, 3).get('sky_top')
    assert reread.dirty_count() == 0


def test_short_row_keeps_its_width(tmp_path):
    path = _make_file(tmp_path, short_block=True)
    cyc = tc.parse(str(path))
    short = cyc.slot(2, 0)
    assert short.width < tc.schema_width(cyc.fields)

    short.set('sky_top', [7, 8, 9])
    tc.write(cyc, backup=False)

    reread = tc.parse(str(path))
    assert reread.slot(2, 0).width == short.width
    assert reread.slot(2, 0).get('sky_top') == [7.0, 8.0, 9.0]


def test_write_makes_backup(tmp_path):
    path = _make_file(tmp_path)
    original = path.read_bytes()
    cyc = tc.parse(str(path))
    cyc.slot(0, 0).set('far_clip', 999.0)
    tc.write(cyc, backup=True)
    assert (tmp_path / "timecyc.dat.bak").read_bytes() == original


def test_revert_slot(tmp_path):
    cyc = tc.parse(str(_make_file(tmp_path)))
    slot = cyc.slot(0, 2)
    before = list(slot.get('sky_top'))
    slot.set('sky_top', [99, 99, 99])
    assert slot.dirty
    tc.revert_slot(cyc, slot)
    assert not slot.dirty
    assert slot.get('sky_top') == before


def test_copy_from(tmp_path):
    cyc = tc.parse(str(_make_file(tmp_path)))
    src, dst = cyc.slot(0, 0), cyc.slot(0, 5)
    src.set('sky_top', [11, 22, 33])
    dst.copy_from(src)
    assert dst.get('sky_top') == [11.0, 22.0, 33.0]
    assert dst.dirty


# ── Интерполяция ─────────────────────────────────────────────────────

def test_interpolate_hits_slots_exactly(tmp_path):
    cyc = tc.parse(str(_make_file(tmp_path)))
    for i, hour in enumerate(tc.SLOT_HOURS):
        got = cyc.interpolate(0, hour)['sky_top']
        assert got == cyc.slot(0, i).get('sky_top')


def test_interpolate_midpoint(tmp_path):
    """12:00 → 19:00, середина = 15:30."""
    cyc = tc.parse(str(_make_file(tmp_path)))
    a = cyc.slot(0, 4).get('sky_top')
    b = cyc.slot(0, 5).get('sky_top')
    mid = cyc.interpolate(0, 15.5)['sky_top']
    for x, y, m in zip(a, b, mid):
        assert abs(m - (x + y) / 2.0) < 1e-6


def test_interpolate_wraps_past_midnight(tmp_path):
    """22:00 → 00:00 идёт через полночь, а не назад через сутки."""
    cyc = tc.parse(str(_make_file(tmp_path)))
    late = cyc.slot(0, 7).get('sky_top')     # 22:00
    midnight = cyc.slot(0, 0).get('sky_top')  # 00:00
    got = cyc.interpolate(0, 23.0)['sky_top']
    for x, y, m in zip(late, midnight, got):
        assert abs(m - (x + y) / 2.0) < 1e-6


# ── Цвет ─────────────────────────────────────────────────────────────

def test_byte_linear_round_trip():
    for b in (0, 1, 17, 128, 200, 254, 255):
        assert tc.linear_to_byte(tc.byte_to_linear(b)) == b


# ── Согласованность панели и файла ───────────────────────────────────

def test_int_props_list_matches_scene_settings():
    """`_INT_PROPS` в ops/timecyc_ops.py должен перечислять РОВНО те
    поля среза, что объявлены IntProperty. Blender 5.x не приводит float
    к int-свойству и падает прямо в операторе импорта, а bpy сюда не
    затащить — поэтому сверяем исходники текстом."""
    import re

    settings = (ROOT / "INU_tools" / "scene_settings.py").read_text(encoding="utf-8")
    declared = set(re.findall(r"^    (f_[a-z_]+): IntProperty", settings, re.M))

    ops = (ROOT / "INU_tools" / "ops" / "timecyc_ops.py").read_text(encoding="utf-8")
    block = re.search(r"_INT_PROPS = frozenset\(\((.*?)\)\)", ops, re.S)
    assert block, "_INT_PROPS не найден"
    listed = set(re.findall(r"'(f_[a-z_]+)'", block.group(1)))
    assert declared, "IntProperty-поля среза не нашлись — сравнение вхолостую"

    assert declared == listed, (
        "IntProperty-поля разъехались: только в scene_settings %s, "
        "только в _INT_PROPS %s" % (declared - listed, listed - declared))


# ── Баланс Day/Night прилайта ────────────────────────────────────────

def test_night_balance_day_and_night_plateaus():
    for h in (7, 9, 12, 15, 19, 19.99):
        assert tc.night_balance(h) == 0.0, h
    for h in (21, 22, 23, 0, 2, 4.99):
        assert tc.night_balance(h) == 1.0, h


def test_night_balance_dusk_ramp():
    """20:00 → 21:00, как в игре: там же зажигаются фонари."""
    assert tc.night_balance(20.0) == 0.0
    assert abs(tc.night_balance(20.5) - 0.5) < 1e-6
    assert tc.night_balance(21.0) == 1.0


def test_night_balance_dawn_ramp():
    assert tc.night_balance(5.0) == 1.0
    assert abs(tc.night_balance(5.5) - 0.5) < 1e-6
    assert tc.night_balance(6.0) == 0.0


def test_night_balance_is_continuous():
    prev = tc.night_balance(0.0)
    h = 0.0
    while h < 24.0:
        h += 0.05
        cur = tc.night_balance(h)
        assert abs(cur - prev) < 0.1, "разрыв на %.2f" % h
        prev = cur


def test_night_balance_custom_hours():
    """Мод перекроил сутки — границы задаются вызывающим."""
    b = tc.night_balance(18.5, dusk_start=18.0, dusk_end=19.0,
                         dawn_start=4.0, dawn_end=5.0)
    assert abs(b - 0.5) < 1e-6
    assert tc.night_balance(19.5, dusk_start=18.0, dusk_end=19.0,
                            dawn_start=4.0, dawn_end=5.0) == 1.0


def test_night_balance_zero_length_ramp():
    """Мгновенный переход не должен делить на ноль."""
    assert tc.night_balance(20.0, dusk_start=20.0, dusk_end=20.0) == 1.0
    assert tc.night_balance(19.9, dusk_start=20.0, dusk_end=20.0) == 0.0


# ── PostFX (цветофильтр кадра) ───────────────────────────────────────

def test_postfx_gain_pc_formula():
    """out = in*(1 + rgb1*a1 + rgb2*a2) — PC/Xbox путь цветофильтра."""
    values = {'postfx1': [255, 66, 66, 48], 'postfx2': [255, 166, 129, 60]}
    kr, kg, kb = tc.postfx_gain(values)
    assert abs(kr - (1 + 66 / 255 + 166 / 255)) < 1e-6
    assert abs(kg - (1 + 66 / 255 + 129 / 255)) < 1e-6
    assert abs(kb - (1 + 48 / 255 + 60 / 255)) < 1e-6


def test_postfx_gain_respects_alpha():
    """Альфа слоя — его вес; нулевая альфа = слой не участвует."""
    values = {'postfx1': [0, 255, 255, 255], 'postfx2': [128, 255, 0, 0]}
    kr, kg, kb = tc.postfx_gain(values)
    assert abs(kr - (1 + 128 / 255)) < 1e-3
    assert kg == 1.0 and kb == 1.0


def test_postfx_gain_missing_layers_is_neutral():
    assert tc.postfx_gain({}) == (1.0, 1.0, 1.0)


def test_apply_gain_srgb_works_in_gamma_space():
    """Множитель кадра применяется к значениям кадра, а не к linear:
    128 sRGB × 1.5 даёт 192 sRGB, а не результат умножения в linear."""
    lin = [tc.byte_to_linear(128)] * 3
    out = tc.apply_gain_srgb(lin, (1.5, 1.5, 1.5))
    assert [tc.linear_to_byte(c) for c in out] == [192, 192, 192]


def test_apply_gain_srgb_clamps():
    lin = [tc.byte_to_linear(200)] * 3
    out = tc.apply_gain_srgb(lin, (3.0, 3.0, 3.0))
    assert [tc.linear_to_byte(c) for c in out] == [255, 255, 255]
