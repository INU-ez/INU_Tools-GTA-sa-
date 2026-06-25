# INU_tools.tools.uv_anim_preview — live viewport preview of GTA UV-animation.
#
# Когда на материале включается «UV Анимация» (inu.uv_anim_write), мы строим в
# шейдере связку  UVMap → Mapping → (Vector входы текстур)  и вешаем на
# Mapping.Location драйверы от текущего кадра:
#       location.x = speed_u * frame / fps
#       location.y = speed_v * frame / fps
# Так при проигрывании таймлайна текстура едет в вьюпорте ровно с той скоростью
# (UV-единиц в секунду), что уйдёт в DFF. Выключение тумблера убирает ноды.
#
# Это ТОЛЬКО предпросмотр — на экспорт в DFF не влияет (его делает dff_export).

import bpy

PREFIX = "INU_UVAnim_"
_MAPPING = PREFIX + "Mapping"
_UVNODE = PREFIX + "UV"


def _target_image_nodes(nt):
    """Текстуры, которым стоит крутить UV: те, что идут в Base Color
    Principled, иначе — все Image Texture. Только со СВОБОДНЫМ входом Vector,
    чтобы не ломать пользовательские маппинги (и чтобы откат был чистым)."""
    targets = []
    for node in nt.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            inp = node.inputs.get('Base Color')
            if inp and inp.is_linked:
                for link in inp.links:
                    if link.from_node.type == 'TEX_IMAGE':
                        targets.append(link.from_node)
    if not targets:
        targets = [n for n in nt.nodes if n.type == 'TEX_IMAGE']
    # только с несвязанным Vector
    out = []
    for t in targets:
        vin = t.inputs.get('Vector')
        if vin is not None and not vin.is_linked:
            out.append(t)
    return out


def _set_location_drivers(mat, mapping):
    """Драйверы Location X/Y от кадра: spd * frame / fps."""
    loc = mapping.inputs['Location']
    scene = bpy.context.scene if bpy.context else None
    for idx, prop in ((0, 'uv_anim_speed_u'), (1, 'uv_anim_speed_v')):
        try:
            loc.driver_remove('default_value', idx)
        except Exception:
            pass
        fcurve = loc.driver_add('default_value', idx)
        drv = fcurve.driver
        drv.type = 'SCRIPTED'
        for v in list(drv.variables):
            drv.variables.remove(v)
        sv = drv.variables.new()
        sv.name = 'spd'
        sv.type = 'SINGLE_PROP'
        st = sv.targets[0]
        st.id_type = 'MATERIAL'
        st.id = mat
        st.data_path = f'inu.{prop}'
        fv = drv.variables.new()
        fv.name = 'fps'
        fv.type = 'SINGLE_PROP'
        ft = fv.targets[0]
        ft.id_type = 'SCENE'
        ft.id = scene
        ft.data_path = 'render.fps'
        # spd * frame / fps — простое арифметическое выражение, не требует
        # «Auto Run Python Scripts». frame — встроенная переменная драйвера.
        drv.expression = 'spd * frame / fps'


def _clear_location_drivers(mapping):
    loc = mapping.inputs['Location']
    for idx in (0, 1):
        try:
            loc.driver_remove('default_value', idx)
        except Exception:
            pass


def setup(mat, mode='SCROLL'):
    """Построить/обновить предпросмотр UV-анимации на материале.

    mode='SCROLL'   — на Location вешаются драйверы от кадра (Speed U/V).
    mode='KEYFRAME' — драйверы НЕ ставятся: Location/Scale остаются свободными,
                      чтобы пользователь сам расставил ключи (I-key) на ноде
                      Mapping; экспорт прочитает эти ключи (read_keyframes)."""
    if mat is None or not mat.use_nodes or mat.node_tree is None:
        return False
    nt = mat.node_tree
    nodes = nt.nodes

    mapping = nodes.get(_MAPPING)
    if mapping is None:
        targets = _target_image_nodes(nt)
        if not targets:
            return False
        uvnode = nodes.new('ShaderNodeUVMap')
        uvnode.name = _UVNODE
        uvnode.label = "INU UV Anim"
        mapping = nodes.new('ShaderNodeMapping')
        mapping.name = _MAPPING
        mapping.label = "INU UV Anim"
        tx, ty = targets[0].location
        mapping.location = (tx - 220, ty)
        uvnode.location = (tx - 440, ty)
        nt.links.new(uvnode.outputs['UV'], mapping.inputs['Vector'])
        for t in targets:
            nt.links.new(mapping.outputs['Vector'], t.inputs['Vector'])

    if mode == 'KEYFRAME':
        _clear_location_drivers(mapping)   # ключи ставит пользователь вручную
    else:
        _set_location_drivers(mat, mapping)
    return True


# Индексы входов ноды Mapping: 0=Vector, 1=Location, 2=Rotation, 3=Scale.
_LOC_INPUT = 1
_SCALE_INPUT = 3


def _action_fcurves(act):
    """Все F-Curves действия — и для старых действий (act.fcurves), и для
    новых «slotted actions» Blender 4.4+/5.x (layers → strips → channelbags),
    где плоский act.fcurves пустой."""
    fcs = list(getattr(act, 'fcurves', []) or [])
    if fcs:
        return fcs
    out = []
    for layer in getattr(act, 'layers', []) or []:
        for strip in getattr(layer, 'strips', []) or []:
            for cb in getattr(strip, 'channelbags', []) or []:
                out.extend(list(getattr(cb, 'fcurves', []) or []))
    return out


def read_keyframes(mat, fps):
    """Прочитать ключи ноды Mapping → список кадров UV-анимации.

    Возвращает (keyframes, duration), где keyframes — список кортежей
    (time, scale_u, scale_v, trans_u, trans_v). t=0 привязан к первому ключу.
    None — если ключей нет (тогда вызывающий откатится к режиму прокрутки)."""
    if mat is None or mat.node_tree is None:
        return None
    nt = mat.node_tree
    mapping = nt.nodes.get(_MAPPING)
    if mapping is None:
        # имя могло получить авто-суффикс (.001) — берём любой наш Mapping
        for n in nt.nodes:
            if n.type == 'MAPPING' and n.name.startswith(PREFIX):
                mapping = n
                break
    if mapping is None:
        return None
    ad = nt.animation_data
    act = ad.action if ad else None
    if act is None:
        return None

    # Индексы входов Location/Scale берём С САМОЙ ноды (а не хардкодим) —
    # и реальное имя ноды. Иначе data_path ключей не совпадёт.
    def _input_index(name, fallback):
        for i, s in enumerate(mapping.inputs):
            if s.name == name:
                return i
        return fallback
    li = _input_index('Location', _LOC_INPUT)
    si = _input_index('Scale', _SCALE_INPUT)
    base = f'nodes["{mapping.name}"].inputs'
    loc_path = f'{base}[{li}].default_value'
    scale_path = f'{base}[{si}].default_value'
    fcurves = {}
    frames = set()
    for fc in _action_fcurves(act):
        if fc.data_path in (loc_path, scale_path):
            fcurves[(fc.data_path, fc.array_index)] = fc
            for kp in fc.keyframe_points:
                frames.add(round(float(kp.co[0])))
    if not frames:
        return None
    frames = sorted(frames)
    f0 = frames[0]
    fps = max(1.0, float(fps))

    def ev(path, idx, frame, default):
        fc = fcurves.get((path, idx))
        return float(fc.evaluate(frame)) if fc else default

    keyframes = []
    for f in frames:
        keyframes.append((
            (f - f0) / fps,                       # time
            ev(scale_path, 0, f, 1.0),            # scale_u
            ev(scale_path, 1, f, 1.0),            # scale_v
            ev(loc_path, 0, f, 0.0),              # trans_u
            ev(loc_path, 1, f, 0.0),              # trans_v
        ))
    duration = (frames[-1] - f0) / fps
    return keyframes, duration


def clear_keyframes(mat):
    """Удалить ключи Location/Scale ноды UV-анимации (legacy и slotted)."""
    if mat is None or mat.node_tree is None:
        return 0
    nt = mat.node_tree
    mapping = nt.nodes.get(_MAPPING)
    if mapping is None:
        for n in nt.nodes:
            if n.type == 'MAPPING' and n.name.startswith(PREFIX):
                mapping = n
                break
    ad = nt.animation_data
    act = ad.action if ad else None
    if mapping is None or act is None:
        return 0
    base = f'nodes["{mapping.name}"].inputs'
    paths = (f'{base}[{_LOC_INPUT}].default_value',
             f'{base}[{_SCALE_INPUT}].default_value')

    removed = 0
    # legacy
    legacy = getattr(act, 'fcurves', None)
    if legacy and len(legacy):
        for fc in list(legacy):
            if fc.data_path in paths:
                legacy.remove(fc)
                removed += 1
    # slotted (Blender 4.4+)
    for layer in getattr(act, 'layers', []) or []:
        for strip in getattr(layer, 'strips', []) or []:
            for cb in getattr(strip, 'channelbags', []) or []:
                for fc in list(getattr(cb, 'fcurves', []) or []):
                    if fc.data_path in paths:
                        cb.fcurves.remove(fc)
                        removed += 1
    return removed


def remove(mat):
    """Убрать ноды предпросмотра. Vector-входы текстур станут свободными —
    Blender вернётся к статичным UV (как было)."""
    if mat is None or mat.node_tree is None:
        return
    nt = mat.node_tree
    mapping = nt.nodes.get(_MAPPING)
    if mapping is not None:
        loc = mapping.inputs['Location']
        for idx in (0, 1):
            try:
                loc.driver_remove('default_value', idx)
            except Exception:
                pass
        nt.nodes.remove(mapping)
    uvnode = nt.nodes.get(_UVNODE)
    if uvnode is not None:
        nt.nodes.remove(uvnode)
