"""Геометрия процедурного перекрёстка — тесты БЕЗ Blender.

`tools/junction_build.py` берёт из Blender только `Vector`, поэтому
подставляем свой двумерный и грузим модуль по пути, минуя пакет (он
тянет за собой весь аддон).

Проверяем то, на чём такой алгоритм обычно и ломается: порядок лучей,
углы между соседними, глубину подрезки, замкнутость и обход контура
против часовой стрелки, вырожденный случай сквозной дороги.
"""

import importlib.util
import math
import pathlib
import sys
import types

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[2] / "INU_tools"


class V:
    """Мини-вектор: ровно то, чем пользуется junction_build.

    Размерность держим честно и на сложении 2D с 3D падаем так же, как
    настоящий mathutils. Без этого заглушка молча проглатывала смесь
    плоских и объёмных векторов, и тесты зеленели там, где Blender
    выбрасывал «vectors must have the same dimensions».
    """

    __slots__ = ("x", "y", "z", "dim")

    def __init__(self, xy=(0.0, 0.0)):
        self.dim = len(xy)
        self.x = float(xy[0])
        self.y = float(xy[1])
        self.z = float(xy[2]) if self.dim > 2 else 0.0

    def _same(self, other):
        if self.dim != other.dim:
            raise ValueError("Vector addition: vectors must have the same "
                             "dimensions for this operation")

    def __add__(self, other):
        self._same(other)
        return V((self.x + other.x, self.y + other.y))

    def __sub__(self, other):
        self._same(other)
        return V((self.x - other.x, self.y - other.y))

    def __mul__(self, k):
        return V((self.x * k, self.y * k))

    __rmul__ = __mul__

    def __neg__(self):
        return V((-self.x, -self.y))

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    @property
    def length(self):
        return math.hypot(self.x, self.y)

    def normalized(self):
        n = self.length
        return V((0.0, 0.0)) if n < 1e-12 else V((self.x / n, self.y / n))

    def __repr__(self):                                   # для отчётов pytest
        return "V(%.3f, %.3f)" % (self.x, self.y)


def _load():
    stub = types.ModuleType("mathutils")
    stub.Vector = V
    added = "mathutils" not in sys.modules
    if added:
        sys.modules["mathutils"] = stub
    try:
        spec = importlib.util.spec_from_file_location(
            "inu_junction_build", ROOT / "tools" / "junction_build.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if added:
            del sys.modules["mathutils"]
    return mod


jb = _load()


def _arm(dx, dy, half=4.0):
    return {'dir': V((dx, dy)).normalized(), 'half': half}


def _area(points):
    """Площадь по формуле шнурков: знак говорит о направлении обхода."""
    total = 0.0
    for i, p in enumerate(points):
        q = points[(i + 1) % len(points)]
        total += p.x * q.y - q.x * p.y
    return total * 0.5


CROSS = [_arm(1, 0), _arm(0, 1), _arm(-1, 0), _arm(0, -1)]
TEE = [_arm(1, 0), _arm(-1, 0), _arm(0, 1)]


def test_arms_sorted_counterclockwise():
    angles = [math.atan2(a['dir'].y, a['dir'].x) for a in jb.sort_arms(CROSS)]
    assert angles == sorted(angles)


def test_corner_of_two_perpendicular_arms():
    # Юг и восток: их границы дают угол ровно на (полуширина, полуширина).
    got = jb.corner(V((0, 0)), _arm(0, -1), _arm(1, 0), margin=1.0)
    assert got.x == pytest.approx(4.0)
    assert got.y == pytest.approx(-4.0)


def test_straight_road_does_not_collapse():
    # Встречные лучи: границы параллельны, пересечения нет — угол всё
    # равно обязан отойти вбок, иначе контур схлопнется в точку.
    got = jb.corner(V((0, 0)), _arm(1, 0), _arm(-1, 0), margin=2.0)
    assert got.length > 1.0


def test_cross_reach_is_half_width_plus_margin():
    _, reach = jb.outline(V((0, 0)), CROSS, margin=1.0, round_steps=0)
    assert reach == pytest.approx([5.0] * 4)


def test_cross_outline_is_closed_ring_ccw():
    points, _ = jb.outline(V((0, 0)), CROSS, margin=1.0, round_steps=0)
    # По два устья и по углу на луч.
    assert len(points) == 4 * 3
    assert _area(points) > 0.0                      # обход против часовой
    assert max(abs(p.x) for p in points) == pytest.approx(5.0)
    assert max(abs(p.y) for p in points) == pytest.approx(5.0)


def test_tee_has_three_arms():
    points, reach = jb.outline(V((0, 0)), TEE, margin=1.0, round_steps=0)
    assert len(reach) == 3
    assert len(points) == 3 * 3
    assert _area(points) > 0.0


def test_rounded_corner_fills_inner_angle():
    sharp, _ = jb.outline(V((0, 0)), CROSS, margin=1.0, round_steps=0)
    round3, _ = jb.outline(V((0, 0)), CROSS, margin=1.0, round_steps=3)
    assert len(round3) == 4 * 5
    # Углы между лучами ВОГНУТЫЕ: контур крестовины входит внутрь между
    # соседними устьями. Скругление их заполняет — ровно как настоящий
    # закруглённый бордюр, — поэтому площадь узла растёт, а не падает.
    assert _area(round3) > _area(sharp)
    # Но не больше, чем габарит всей крестовины.
    assert _area(round3) < 10.0 * 10.0


def test_wide_road_pushes_junction_out():
    wide = [_arm(1, 0, 8.0), _arm(0, 1, 4.0), _arm(-1, 0, 8.0),
            _arm(0, -1, 4.0)]
    _, reach = jb.outline(V((0, 0)), wide, margin=0.0, round_steps=0)
    # Лучи узкой дороги отходят на полуширину широкой, и наоборот.
    for arm, depth in zip(jb.sort_arms(wide), reach):
        other = 4.0 if arm['half'] == 8.0 else 8.0
        assert depth == pytest.approx(other)


def test_fan_covers_every_edge():
    points, _ = jb.outline(V((0, 0)), CROSS, margin=1.0, round_steps=2)
    hub, tris = jb.fan(points, V((0, 0)))
    assert hub == len(points)
    assert len(tris) == len(points)
    assert all(hub in tri for tri in tris)


def test_two_arms_give_nothing():
    points, reach = jb.outline(V((0, 0)), [_arm(1, 0)], margin=1.0)
    assert points == [] and reach == []


def test_bisector_splits_the_angle():
    got = jb.bisector(_arm(1, 0), _arm(0, 1))
    assert got.x == pytest.approx(got.y)          # ровно 45°
    assert got.length == pytest.approx(1.0)


def test_bisector_of_opposite_arms_is_crosswise():
    # Сквозная дорога: биссектриса вырождается, режем поперёк.
    got = jb.bisector(_arm(1, 0), _arm(-1, 0))
    assert abs(got.x) == pytest.approx(0.0)
    assert abs(got.y) == pytest.approx(1.0)


def _profile(half=4.0):
    return [(-half, 0.0), (0.0, 0.06), (half, 0.0)]


def test_wedge_reaches_from_mouth_to_bisector():
    arms = jb.sort_arms(CROSS)
    east = next(a for a in arms if a['dir'].x > 0.5)
    back = jb.bisector(_arm(0, -1), east)         # юг ↔ восток
    fwd = jb.bisector(east, _arm(0, 1))           # восток ↔ север
    rows = jb.wedge(V((0, 0)), east, back, fwd, reach=5.0,
                    profile=_profile())
    assert len(rows) == 3
    # Устье стоит на своём месте, поперёк — по профилю.
    (mouth_r, _), (cut_r, _) = rows[0]
    assert mouth_r.x == pytest.approx(5.0)
    assert mouth_r.y == pytest.approx(-4.0)
    # Правая кромка упирается в биссектрису юг-восток: там x = -y.
    assert cut_r.x == pytest.approx(-cut_r.y)
    # Осевая линия доходит до самого центра.
    (_, _), (cut_mid, _) = rows[1]
    assert cut_mid.x == pytest.approx(0.0, abs=1e-6)
    assert cut_mid.y == pytest.approx(0.0, abs=1e-6)


def test_wedge_keeps_profile_height():
    arms = jb.sort_arms(CROSS)
    east = next(a for a in arms if a['dir'].x > 0.5)
    rows = jb.wedge(V((0, 0)), east,
                    jb.bisector(_arm(0, -1), east),
                    jb.bisector(east, _arm(0, 1)),
                    reach=5.0, profile=_profile())
    # Подъём центра дороги обязан доехать до узла как есть.
    assert [row[0][1] for row in rows] == [0.0, 0.06, 0.0]
    assert [row[1][1] for row in rows] == [0.0, 0.06, 0.0]


def test_wedges_do_not_overlap_in_the_middle():
    # Смысл всей затеи: четыре куска сходятся, но не лезут друг на
    # друга. Проверяем через углы: точка реза каждого куска не должна
    # заходить в сектор соседа.
    arms = jb.sort_arms(CROSS)
    n = len(arms)
    for i, arm in enumerate(arms):
        back = jb.bisector(arms[(i - 1) % n], arm)
        fwd = jb.bisector(arm, arms[(i + 1) % n])
        rows = jb.wedge(V((0, 0)), arm, back, fwd, reach=5.0,
                        profile=_profile())
        for (_, _), (cut, _) in rows:
            if cut.length < 1e-6:
                continue                  # центр принадлежит всем
            # Угол между резом и своим лучом не больше 45° — то есть
            # кусок остался в своей четверти.
            cosine = cut.normalized().dot(arm['dir'])
            assert cosine > 0.70          # cos 45° ≈ 0.707, с допуском


def test_center_may_be_three_dimensional():
    # Центр узла приходит объёмным — с высотой, снятой с дорог. Смесь
    # 2D и 3D в Blender не складывается, поэтому приведение обязано
    # быть внутри, а не на совести вызывающего.
    flat, _ = jb.outline(V((0, 0)), CROSS, margin=1.0, round_steps=0)
    tall, _ = jb.outline(V((0, 0, 12.5)), CROSS, margin=1.0, round_steps=0)
    assert [(p.x, p.y) for p in tall] == [(p.x, p.y) for p in flat]


def test_stub_catches_mixed_dimensions():
    # Страховка на саму заглушку: если она перестанет ловить смесь
    # размерностей, тест выше снова начнёт врать.
    with pytest.raises(ValueError):
        V((1, 2)) + V((1, 2, 3))
