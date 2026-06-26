# INU_tools.tools.bake.bake_maps — Слой 2 подсистемы запекания.
#
# Реестр карт (BAKE_MAPS) — единственный источник правды о том, какие
# карты бывают и как каждая печётся. Добавить карту = одна запись (+
# опционально один builder). Также владеет светозависимостью карт
# (риги, M3) и построением Bevel-материала в Python (light-free).
#
# Зависит ТОЛЬКО от bake_core (нижний слой) и compat. Не знает про
# операторы/UI/scene-настройки — параметры приходят словарём `params`.
#
# ВАЖНО: НЕ добавлять `from __future__ import annotations`.

import math
from collections import OrderedDict
from dataclasses import dataclass

import bpy
import mathutils

from . import bake_core


# Namespaced datablock-имена (get-or-reuse без `.001`, чистятся sweep'ом).
BEVEL_MAT_NAME = 'INU_Bevel_Mat'
BAKE_LIGHTS_COLL = 'INU_Bake_Lights'
BAKE_WORLD_NAME = 'INU_Bake_World'

# Hi→Low пары определяются по ФИКСИРОВАННЫМ суффиксам (не настраиваются).
HI_SUFFIX = '_hi'
LOW_SUFFIX = '_low'

# Дефолтные параметры запекания (перекрываются из scene-настроек на M5).
DEFAULT_PARAMS = {
    'bevel_size': 0.05,
    'bevel_samples': 8,
    'light_energy_scale': 1.0,
}


# ── Map definition ───────────────────────────────────────────────────

@dataclass(frozen=True)
class BakeMapDef:
    """Описание одной карты. Pure-data, не bpy-тип."""
    id: str                    # 'AO' | 'DIFFUSE' | 'BEVEL' | ...
    label_key: str             # сырой ключ для T() (перевод — в UI/proxy)
    bake_type: str             # тип для bpy.ops.object.bake: 'AO'|'DIFFUSE'|'EMIT'
    needs_light: bool          # True → нужен внутренний риг + изоляция (M3)
    rig_kind: str              # 'NONE' | 'SUN' | 'PRELIGHT_8'
    node_group_builder: object # callable(obj, params)->teardown | None
    samples: int               # cycles.samples для прохода
    default_blend: str         # режим смешивания свежего слоя в стеке
    default_opacity: float
    default_contrast: float    # FUTURE (1.0 = identity)
    default_gamma: float       # FUTURE (1.0 = identity)
    pass_direct: bool = False  # для DIFFUSE-семейства
    pass_indirect: bool = False
    pass_color: bool = True


# ── Bevel material (Python, light-free) ──────────────────────────────

def build_bevel_material(params):
    """Собрать/переиспользовать материал-маску кромок (Bevel).

    Идея: нормаль с Bevel-ноды совпадает с геометрической на плоскости
    и расходится у рёбер → их dot-product ≈1 на плоскости, <1 на кромке.
    Маска кромок = clamp(1 − dot): рёбра светлые, плоскости тёмные.
    Выход — Emission, поэтому печётся как EMIT и не зависит от света.

    Инверсию делаем ShaderNodeMath(SUBTRACT), а НЕ MapRange: у MapRange
    дублированные сокеты From/To Min/Max (FLOAT + VECTOR режимы), и
    inputs['From Min'] неоднозначен — попадает не в тот сокет, выход
    схлопывается в константу (тот же баг, что compat.py описывает для
    ShaderNodeMix). У ShaderNodeMath сокеты простые float — без ловушки.

    Сокеты материала строятся напрямую (без node-группы), поэтому
    interface-API 4.0 здесь не нужен; compat.node_group_* зарезервирован
    для будущих grouped-карт.
    """
    mat = bpy.data.materials.get(BEVEL_MAT_NAME)
    if mat is None:
        mat = bpy.data.materials.new(BEVEL_MAT_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    bevel = nt.nodes.new('ShaderNodeBevel')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.use_clamp = True

    bevel.samples = int(params.get('bevel_samples', 8))
    rad = bevel.inputs.get('Radius')
    if rad is not None:
        rad.default_value = float(params.get('bevel_size', 0.05))

    # bevel.Normal · geo.Normal → скаляр (output 'Value')
    nt.links.new(bevel.outputs['Normal'], dot.inputs[0])
    nt.links.new(geo.outputs['Normal'], dot.inputs[1])

    # mask = clamp(1 − dot): ребро (dot<1) → светлое, плоскость → тёмное
    inv.inputs[0].default_value = 1.0
    nt.links.new(dot.outputs['Value'], inv.inputs[1])
    nt.links.new(inv.outputs['Value'], emit.inputs['Color'])
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])

    mat.use_fake_user = False
    return mat


def _prepare_bevel(obj, params):
    """Временно подменить материалы объекта на Bevel-материал. Возвращает
    teardown-замыкание, восстанавливающее исходные материалы."""
    mat = build_bevel_material(params)
    slots = obj.material_slots
    if len(slots) > 0:
        original = [s.material for s in slots]
        for s in slots:
            s.material = mat

        def teardown():
            for s, m in zip(obj.material_slots, original):
                s.material = m
            if mat.users == 0:
                try:
                    bpy.data.materials.remove(mat)
                except Exception:
                    pass
        return teardown

    obj.data.materials.append(mat)

    def teardown_appended():
        try:
            obj.data.materials.pop()
        except Exception:
            pass
        if mat.users == 0:
            try:
                bpy.data.materials.remove(mat)
            except Exception:
                pass
    return teardown_appended


# ── Self-contained light rig (Shadow / Diffuse-Lit) ──────────────────
# Свет генерирует сама подсистема — внешние источники сцены не нужны и НЕ
# должны влиять на результат. SUN-лампы (без inverse-square falloff →
# экспозиция инвариантна к размеру объекта, C5) в собственной коллекции
# INU_Bake_Lights (НЕ 'Prelight_Lights' — C3). На время прохода прячем
# (hide_render) все прочие объекты и ставим нейтральный мир (изоляция
# чужого света и эмиссии, C2); всё восстанавливаем в teardown.

# kind → список (euler_градусы_xyz, множитель_энергии).
# Энергии откалиброваны так, чтобы полностью освещённая поверхность давала
# ≈1.0 (учёт ламбертовского 1/π): иначе SHADOW как MULTIPLY-слой давит всю
# текстуру, а не только тени, а Diffuse-Lit выходит тёмным (C5). Точная
# подстройка — через gtatools_bake_light_energy_scale.
_RIG_SPECS = {
    'SUN':  [((50.0, 0.0, 40.0), 4.0)],                 # Shadow: один key-SUN (lit≈1)
    'DOME': [((0.0, 0.0, 0.0), 3.0),                    # Diffuse-Lit: верх + 4 бока
             ((60.0, 0.0, 0.0), 1.2),
             ((60.0, 0.0, 90.0), 1.2),
             ((60.0, 0.0, 180.0), 1.2),
             ((60.0, 0.0, 270.0), 1.2)],
}
# kind → (strength, color) нейтрального мира (ambient-fill, чтобы тени
# не были абсолютно чёрными).
_RIG_WORLD = {
    'SUN':  (0.05, (1.0, 1.0, 1.0)),
    'DOME': (0.15, (1.0, 1.0, 1.0)),
}


def _world_bbox(obj):
    """world-space центр + радиус (полудиагональ) bbox объекта."""
    mw = obj.matrix_world
    cs = [mw @ mathutils.Vector((c[0], c[1], c[2])) for c in obj.bound_box]
    xs = [c.x for c in cs]
    ys = [c.y for c in cs]
    zs = [c.z for c in cs]
    mn = mathutils.Vector((min(xs), min(ys), min(zs)))
    mx = mathutils.Vector((max(xs), max(ys), max(zs)))
    return (mn + mx) * 0.5, max((mx - mn).length * 0.5, 0.001)


def _make_bake_world(strength, color):
    w = bpy.data.worlds.get(BAKE_WORLD_NAME) or bpy.data.worlds.new(BAKE_WORLD_NAME)
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    if bg is not None:
        bg.inputs['Color'].default_value = (color[0], color[1], color[2], 1.0)
        bg.inputs['Strength'].default_value = strength
    return w


def _find_layer_collection(layer_coll, name):
    if layer_coll.collection.name == name:
        return layer_coll
    for ch in layer_coll.children:
        r = _find_layer_collection(ch, name)
        if r is not None:
            return r
    return None


def _build_light_rig(context, obj, kind, params, keep_visible=()):
    """Построить самодостаточный свет-риг под светозависимую карту и
    изолировать сцену от чужого света. keep_visible — объекты, которые НЕ
    прятать (для hi→low: хайполи-источник). Возвращает teardown (finally)."""
    scene = context.scene
    center, _radius = _world_bbox(obj)
    scale = float(params.get('light_energy_scale', 1.0))

    # 1. Снапшот + изоляция: прячем из рендера всё кроме целевого объекта
    #    (и keep_visible) — убирает чужие лампы И эмиссивные материалы (C2).
    keep = {obj}
    keep.update(keep_visible or ())
    hidden = []
    for o in scene.objects:
        hidden.append((o, o.hide_render))
        o.hide_render = (o not in keep)

    # 2. Снапшот + нейтральный мир.
    orig_world = scene.world
    strength, color = _RIG_WORLD.get(kind, (0.1, (1.0, 1.0, 1.0)))
    scene.world = _make_bake_world(strength, color)

    # 3. Собственная коллекция рига (очищаем от прошлых прогонов).
    coll = bpy.data.collections.get(BAKE_LIGHTS_COLL)
    if coll is None:
        coll = bpy.data.collections.new(BAKE_LIGHTS_COLL)
    if coll.name not in scene.collection.children:
        scene.collection.children.link(coll)
    for o in list(coll.objects):
        ld = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if ld and getattr(ld, 'users', 1) == 0:
            bpy.data.lights.remove(ld)

    # 4. SUN-лампы (без falloff → инвариантны к размеру объекта).
    lamps = []
    for euler_deg, energy_f in _RIG_SPECS.get(kind, _RIG_SPECS['DOME']):
        ld = bpy.data.lights.new(name='INU_Bake_Sun', type='SUN')
        ld.energy = energy_f * scale
        lo = bpy.data.objects.new('INU_Bake_Sun', ld)
        lo.location = center
        lo.rotation_euler = (math.radians(euler_deg[0]),
                             math.radians(euler_deg[1]),
                             math.radians(euler_deg[2]))
        coll.objects.link(lo)
        lamps.append(lo)

    # 5. Коллекция рига не должна быть excluded из активного view layer (C10).
    lc = _find_layer_collection(context.view_layer.layer_collection, BAKE_LIGHTS_COLL)
    if lc is not None:
        lc.exclude = False
        lc.hide_viewport = False

    def teardown():
        for o, val in hidden:
            try:
                o.hide_render = val
            except Exception:
                pass
        try:
            scene.world = orig_world
        except Exception:
            pass
        for lo in lamps:
            ld = lo.data
            try:
                bpy.data.objects.remove(lo, do_unlink=True)
            except Exception:
                pass
            try:
                if ld and getattr(ld, 'users', 1) == 0:
                    bpy.data.lights.remove(ld)
            except Exception:
                pass
        c = bpy.data.collections.get(BAKE_LIGHTS_COLL)
        if c is not None:
            try:
                if scene.collection.children.get(BAKE_LIGHTS_COLL) is not None:
                    scene.collection.children.unlink(c)
            except Exception:
                pass
            try:
                if len(c.objects) == 0:
                    bpy.data.collections.remove(c)
            except Exception:
                pass
        w = bpy.data.worlds.get(BAKE_WORLD_NAME)
        if w is not None and w.users == 0:
            try:
                bpy.data.worlds.remove(w)
            except Exception:
                pass

    return teardown


# ── Per-map orchestration ────────────────────────────────────────────

def prepare_map(map_def, obj, context, params, keep_visible=()):
    """Подготовить окружение под карту. Возвращает teardown-замыкание
    (всегда вызывать в finally).

    - Bevel → подмена материалов (node_group_builder).
    - Светозависимые (Shadow / Diffuse-Lit) → самодостаточный свет-риг
      (keep_visible не прячется — для hi→low хайполи остаётся виден).
    - Остальные light-free (AO / Diffuse-albedo) → no-op.
    """
    if map_def.node_group_builder is not None:
        return map_def.node_group_builder(obj, params)
    if map_def.needs_light:
        return _build_light_rig(context, obj, map_def.rig_kind, params,
                                keep_visible)
    return lambda: None


def bake_one_map(context, map_def, obj, image, *, margin=8, params=None,
                 samples=None, target_uv=None, selected_to_active=False,
                 cage_extrusion=0.0, max_ray=0.0, keep_visible=()):
    """Запечь одну карту `map_def` объекта `obj` в `image`.

    Предполагается, что вызывающий уже внутри bake_core.BakeStateGuard,
    объект активен+выделен и в OBJECT mode.

    samples=None → берём map_def.samples; иначе override (оператор даёт
    его шумным картам — AO / свет).

    target_uv (имя UV-карты) → печь в неё, а не в активную (UV→UV; нужно
    для trim-развёрток: рабочая UV с наложениями даёт кашу, печём в
    отдельную чистую). None → активная UV.

    Мульти-материал: один вызов bpy.ops.object.bake печёт все слоты в
    одну картинку (у всех активная image-нода указывает на неё) —
    отдельный per-slot цикл не нужен.
    """
    if params is None:
        params = DEFAULT_PARAMS
    teardown = prepare_map(map_def, obj, context, params, keep_visible=keep_visible)

    # UV→UV: если печём в ДРУГУЮ UV, исходные текстуры надо приколоть к
    # исходной (текущей активной) UV — иначе они засэмплятся по целевой и
    # выйдет каша. Источник = активная UV на момент старта (твоя trim).
    pin_token = None
    uv_token = None
    if target_uv:
        uvs = getattr(obj.data, 'uv_layers', None)
        # Источник = UV, по которой материал РЕНДЕРИТ текстуры (active_render),
        # с fallback на active. Её пиним, чтобы текстуры не «съехали» на
        # целевую UV при переключении.
        src_name = None
        if uvs:
            src_name = next((u.name for u in uvs if u.active_render), None)
            if src_name is None and uvs.active:
                src_name = uvs.active.name
        if src_name and src_name != target_uv:
            pin_token = bake_core.pin_image_nodes_to_uv(obj, src_name)
        uv_token = bake_core.set_active_uv(obj, target_uv)
    try:
        rec = bake_core.prepare_bake_targets(obj, image)
        try:
            bake_core.run_cycles_bake(
                map_def.bake_type,
                margin=margin,
                use_clear=True,
                pass_direct=map_def.pass_direct,
                pass_indirect=map_def.pass_indirect,
                pass_color=map_def.pass_color,
                samples=(samples if samples is not None else map_def.samples),
                selected_to_active=selected_to_active,
                cage_extrusion=cage_extrusion,
                max_ray_distance=max_ray,
            )
        finally:
            bake_core.restore_bake_targets(rec)
    finally:
        bake_core.restore_active_uv(uv_token)
        bake_core.unpin_image_nodes(pin_token)
        teardown()


# ── Registry ─────────────────────────────────────────────────────────
# Светозависимые карты (SHADOW, DIFFUSE_LIT) добавляются на M3 — реестр
# data-driven, появление записи автоматически прокидывает их в enum/UI.

BAKE_MAPS = OrderedDict([
    ('AO', BakeMapDef(
        id='AO', label_key='AO', bake_type='AO',
        needs_light=False, rig_kind='NONE', node_group_builder=None,
        samples=16, default_blend='MULTIPLY', default_opacity=1.0,
        default_contrast=1.0, default_gamma=1.0)),
    ('DIFFUSE', BakeMapDef(
        id='DIFFUSE', label_key='Diffuse', bake_type='DIFFUSE',
        needs_light=False, rig_kind='NONE', node_group_builder=None,
        samples=1, default_blend='NORMAL', default_opacity=1.0,
        default_contrast=1.0, default_gamma=1.0,
        pass_direct=False, pass_indirect=False, pass_color=True)),
    ('DIFFUSE_LIT', BakeMapDef(
        id='DIFFUSE_LIT', label_key='Diffuse Lit', bake_type='DIFFUSE',
        needs_light=True, rig_kind='DOME', node_group_builder=None,
        samples=8, default_blend='NORMAL', default_opacity=1.0,
        default_contrast=1.0, default_gamma=1.0,
        pass_direct=True, pass_indirect=False, pass_color=True)),
    ('SHADOW', BakeMapDef(
        id='SHADOW', label_key='Shadow', bake_type='DIFFUSE',
        needs_light=True, rig_kind='SUN', node_group_builder=None,
        samples=32, default_blend='MULTIPLY', default_opacity=1.0,
        default_contrast=1.0, default_gamma=1.0,
        pass_direct=True, pass_indirect=False, pass_color=False)),
    ('BEVEL', BakeMapDef(
        id='BEVEL', label_key='Bevel', bake_type='EMIT',
        needs_light=False, rig_kind='NONE',
        node_group_builder=_prepare_bevel,
        samples=4, default_blend='OVERLAY', default_opacity=1.0,
        default_contrast=1.0, default_gamma=1.0)),

    # ── PBR-карты (нативные пассы Cycles) ─────────────────────────────
    # Полноценные карты стека, как AO/Diffuse/Bevel. Печёт сам материал
    # объекта (свой normal/roughness/emission); для переноса детали — hi→low.
    ('NORMAL', BakeMapDef(
        id='NORMAL', label_key='Normal Map', bake_type='NORMAL',
        needs_light=False, rig_kind='NONE', node_group_builder=None,
        samples=1, default_blend='NORMAL', default_opacity=1.0,
        default_contrast=1.0, default_gamma=1.0)),
    # ROUGHNESS убрана из списка карт по запросу — для GTA-текстур она не
    # нужна. Старые слои/пресеты со map_id='ROUGHNESS' безопасно
    # игнорируются (get_map вернёт None, bake_ops такие слои пропускает).
    ('EMISSION', BakeMapDef(
        id='EMISSION', label_key='Emission', bake_type='EMIT',
        needs_light=False, rig_kind='NONE', node_group_builder=None,
        samples=1, default_blend='NORMAL', default_opacity=1.0,
        default_contrast=1.0, default_gamma=1.0)),
    # Свет ОТ излучающих граней на соседние поверхности (GI). В отличие от
    # карты Emission (она снимает только само свечение грани), здесь
    # светящийся материал работает как лампа: запекаем НЕпрямой diffuse-свет
    # (pass_indirect, без albedo) — зелёная грань «подсвечивает» кирпич
    # вокруг. Складываем поверх (ADD). GI шумный → сэмплы из настроек.
    ('EMIT_GI', BakeMapDef(
        id='EMIT_GI', label_key='Emission Light (GI)', bake_type='DIFFUSE',
        needs_light=False, rig_kind='NONE', node_group_builder=None,
        samples=64, default_blend='ADD', default_opacity=1.0,
        default_contrast=1.0, default_gamma=1.0,
        pass_direct=False, pass_indirect=True, pass_color=False)),
])


def get_map(map_id):
    """BakeMapDef по id (или None)."""
    return BAKE_MAPS.get(map_id)


def bake_map_enum_items():
    """Список (id, raw_label, description) для EnumProperty. Перевод
    (T()) применяется на стороне UI/proxy — bake_maps не зависит от T."""
    return [(m.id, m.label_key, '') for m in BAKE_MAPS.values()]


def _find_dff_lod_pair(obj):
    """GTA DFF↔LOD pair for `obj`: the main DFF acts as high-detail, the LOD
    as low-detail. Resolved through the addon's model-type detection, so any
    naming convention (suffix `_LOD`, prefix `LOD…`, or the user's configured
    suffixes) matches `base_dff` ↔ `base_lod` / `LODbase`. Returns
    (dff_obj, lod_obj); either may be None when no partner exists."""
    try:
        from ..model_utils import get_model_type
    except Exception:
        return (None, None)
    mt, base = get_model_type(obj)
    if mt not in ('DFF', 'LOD') or not base:
        return (None, None)
    base_u = base.upper()
    want = 'LOD' if mt == 'DFF' else 'DFF'
    dff = obj if mt == 'DFF' else None
    lod = obj if mt == 'LOD' else None
    for o in bpy.data.objects:
        if o.type != 'MESH' or o is obj:
            continue
        omt, obase = get_model_type(o)
        if omt == want and (obase or '').upper() == base_u:
            if want == 'DFF':
                dff = o
            else:
                lod = o
            break
    return (dff, lod)


def find_hilow_pair(obj, hi_suffix, low_suffix, dff_lod_fallback=False):
    """По объекту `obj` (хай- или лоуполи) найти пару.

    Сначала по явным суффиксам 'wheel_hi' ↔ 'wheel_low'. Если их нет и
    включён `dff_lod_fallback` — пробуем GTA-пару DFF↔LOD (DFF = high,
    LOD = low), например `base_dff` ↔ `base_lod`. Фолбэк опционален: в
    режиме «Камера» low — это плоский billboard, а LOD-меш им не является,
    поэтому там его не используем (только в режиме Hi→Low). Принимает любой
    из пары. Возвращает (high_obj, low_obj); любой может быть None.
    """
    if obj is None:
        return (None, None)
    name = obj.name
    if low_suffix and name.endswith(low_suffix):
        base = name[:-len(low_suffix)]
        return (bpy.data.objects.get(base + hi_suffix), obj)
    if hi_suffix and name.endswith(hi_suffix):
        base = name[:-len(hi_suffix)]
        return (obj, bpy.data.objects.get(base + low_suffix))
    # Fallback: GTA DFF/LOD pair (DFF acts as hi, LOD as low). Only when a
    # real pair exists — a lone object returns nothing usable.
    if dff_lod_fallback:
        dff, lod = _find_dff_lod_pair(obj)
        if dff is not None and lod is not None:
            return (dff, lod)
    return (None, None)
