# INU_tools.tools.timecyc_screen — туман и PostFX как экранные эффекты.
#
# И то и другое в игре — операции по ГОТОВОМУ кадру:
#
#     туман:  out = lerp(color, fogColor, f(depth))   fixed-function fog
#     PostFX: out = in * (1 + rgb1*a1 + rgb2*a2)      полноэкранный квад
#
# Поэтому и здесь они живут в композиторе, а не в материалах: ложатся на
# весь кадр разом — включая объекты, куда превью прилайта не заглядывало,
# — и ни один материал не приходится трогать.
#
# Работает в вьюпорте: Blender 4.2+ умеет считать композитор прямо в
# View3D (Shading → Compositor), а пассы рендера там доступны на EEVEE —
# что нам и нужно. В Solid-режиме композитора нет, это цена подхода.
#
# Чужие композиторные ноды не ломаем: своя цепочка помечена именами
# INU_TC_*, прежний источник Composite запоминается на сцене и
# возвращается, когда режим выключают.

import bpy

from ..core.timecyc import linear_to_srgb, srgb_to_linear

_N_RL = "INU_TC_RenderLayers"
_N_RANGE = "INU_TC_FogRange"
_N_DIV = "INU_TC_FogDiv"
_N_CURVE = "INU_TC_FogCurve"
_N_SKY = "INU_TC_FogSkyGate"
_N_FACMUL = "INU_TC_FogFac"
_N_FOGCOL = "INU_TC_FogColor"
_N_FOGMIX = "INU_TC_FogMix"
_N_ENC = "INU_TC_PostEnc"
_N_GAIN = "INU_TC_PostGain"
_N_MUL = "INU_TC_PostMul"
_N_DEC = "INU_TC_PostDec"
_N_COMP = "INU_TC_Composite"

_OUR_NODES = (_N_RL, _N_RANGE, _N_DIV, _N_CURVE, _N_SKY, _N_FACMUL, _N_FOGCOL, _N_FOGMIX,
              _N_ENC, _N_GAIN, _N_MUL, _N_DEC)

# Бампать при правке структуры цепочки — старые сцены пересоберутся сами.
_TREE_VERSION = 4

# Типы нод: сначала композиторный, потом общий — в 5.x часть
# CompositorNode* исчезла, а общие ноды остались.
_MATH = ('CompositorNodeMath', 'ShaderNodeMath')
_RGB = ('CompositorNodeRGB', 'ShaderNodeRGB')
_GAMMA = ('CompositorNodeGamma', 'ShaderNodeGamma')
_MIX = ('CompositorNodeMixRGB', 'CompositorNodeMix', 'ShaderNodeMix')

_PREV_LINK = 'inu_tc_comp_prev'
_PREV_USE_NODES = 'inu_tc_comp_use_nodes'
_PREV_COMP_GROUP = 'inu_tc_comp_group_created'


def comp_tree(scene, create=False):
    """Дерево композитора сцены — кросс-версионно.

    В Blender 5.0 `scene.node_tree` удалён: композитор стал отдельным
    датаблоком `scene.compositing_node_group`, а `use_nodes` объявлен
    устаревшим. На 4.x всё по-старому.
    """
    if hasattr(scene, 'compositing_node_group'):
        tree = scene.compositing_node_group
        if tree is None and create:
            tree = bpy.data.node_groups.new("INU Timecyc Comp",
                                            'CompositorNodeTree')
            scene.compositing_node_group = tree
            scene[_PREV_COMP_GROUP] = True
        return tree

    if create and not scene.use_nodes:
        scene[_PREV_USE_NODES] = False
        scene.use_nodes = True
    return getattr(scene, 'node_tree', None)


def _output_node(tree):
    """Куда отдавать кадр: нода Composite, а если её в этой версии уже
    нет — выход группы композитора."""
    for node in tree.nodes:
        if node.bl_idname in ('CompositorNodeComposite', 'NodeGroupOutput'):
            return node
    if hasattr(bpy.types, 'CompositorNodeComposite'):
        return _node(tree, _N_COMP, 'CompositorNodeComposite', (860, 40))
    iface = getattr(tree, 'interface', None)
    if iface is not None and not any(
            getattr(i, 'in_out', None) == 'OUTPUT'
            for i in getattr(iface, 'items_tree', ())):
        iface.new_socket(name="Image", in_out='OUTPUT',
                         socket_type='NodeSocketColor')
    node = _node(tree, _N_COMP, 'NodeGroupOutput', (860, 40))
    return node


def _node(tree, name, idnames, location):
    """Нода по имени; тип берётся первый доступный из `idnames`.

    Композитор в Blender 5.0 переписан, и часть типов оттуда исчезла
    (CompositorNodeMapRange, например). Поэтому — перебор кандидатов и
    None вместо исключения: лучше собрать цепочку попроще, чем уронить
    применение среза."""
    if isinstance(idnames, str):
        idnames = (idnames,)

    node = tree.nodes.get(name)
    if node is not None and node.bl_idname not in idnames:
        tree.nodes.remove(node)
        node = None
    if node is not None:
        return node

    for idname in idnames:
        try:
            node = tree.nodes.new(idname)
        except (RuntimeError, TypeError):
            continue
        node.name = name
        node.label = name
        node.location = location
        return node
    print("[INU timecyc] нет ни одной из нод %s — стадия пропущена"
          % (idnames,))
    return None


# У старой MixRGB сокеты зовутся Fac/Image/Image, у новой Mix —
# Factor/A/B/Result, и у неё их по три пары (Float/Vector/Color).
# Поэтому ищем по имени с запасными вариантами И по типу сокета — тем
# же приёмом, что tools/compat.py применяет к шейдерному Mix.

def _socket(sockets, names, sock_type=None, skip=()):
    for name in names:
        for sock in sockets:
            if sock.name != name or sock in skip:
                continue
            if sock_type is None or sock.type == sock_type:
                return sock
    return None


def _in(node, names, sock_type='RGBA'):
    """Вход ноды по кандидатам имён, иначе — первый подходящий по типу.

    Имена сокетов гуляют между версиями (у композиторной Gamma это то
    'Image', то 'Color'), и падать из-за этого посреди сборки нельзя."""
    if node is None:
        return None
    sock = _socket(node.inputs, names, sock_type)
    if sock is not None:
        return sock
    for cand in node.inputs:
        if sock_type is None or cand.type == sock_type:
            return cand
    return None


def _out(node, names, sock_type='RGBA'):
    if node is None:
        return None
    sock = _socket(node.outputs, names, sock_type)
    if sock is not None:
        return sock
    for cand in node.outputs:
        if sock_type is None or cand.type == sock_type:
            return cand
    return None


_IMG = ('Image', 'Color', 'Result')


def _const(node, skip=0):
    """Числовой вход ноды под КОНСТАНТУ — первый свободный.

    Обращаться по индексу нельзя: у композиторных Math в разных версиях
    Blender разное число сокетов и разный их порядок, и константа
    уезжала мимо — туман считался с дефолтами и заливал весь кадр."""
    if node is None:
        return None
    free = [sock for sock in node.inputs
            if sock.type == 'VALUE' and not sock.is_linked]
    if len(free) > skip:
        return free[skip]
    return None


def _set_const(node, value):
    """Записать константу в свободный числовой вход ноды."""
    sock = _const(node)
    if sock is None:
        return False
    if abs(float(sock.default_value) - float(value)) > 1e-6:
        sock.default_value = float(value)
    return True


def _mix_fac(node):
    return _socket(node.inputs, ('Fac', 'Factor'), 'VALUE')


def _mix_ab(node):
    """(A, B) — цветовые входы микса."""
    a = _socket(node.inputs, ('Image', 'A'), 'RGBA')
    b = _socket(node.inputs, ('Image', 'B'), 'RGBA', skip=(a,))
    return a, b


def _mix_result(node):
    return _socket(node.outputs, ('Image', 'Result'), 'RGBA')


def _setup_mix(node, blend):
    """Настроить микс: новой ноде Mix нужен ещё и data_type."""
    if hasattr(node, 'data_type'):
        try:
            node.data_type = 'RGBA'
        except TypeError:
            pass
    node.blend_type = blend


def _existing_render_layers(tree):
    """Чужая нода Render Layers, если она уже есть — переиспользуем её,
    чтобы не плодить второй источник кадра."""
    for node in tree.nodes:
        if node.bl_idname == 'CompositorNodeRLayers':
            return node
    return None


def ensure_tree(scene):
    """Собрать цепочку «кадр → туман → PostFX → Composite».

    Идемпотентно: пересобирается только при смене _TREE_VERSION или
    если кто-то поломал ноды руками."""
    tree = comp_tree(scene, create=True)
    if tree is None:
        return None

    if (scene.get('inu_tc_comp_version') == _TREE_VERSION
            and tree.nodes.get(_N_MUL) is not None):
        return tree

    # Пасс глубины включаем ПЕРВЫМ делом: сокет Depth появляется у ноды
    # Render Layers только вместе с ним. Раньше пасс включался в конце
    # функции — на первом проходе сокета ещё не было, связь тумана не
    # создавалась, а на втором функция выходила раньше по версии. Туман
    # молча не работал.
    for view_layer in scene.view_layers:
        try:
            if not view_layer.use_pass_z:
                view_layer.use_pass_z = True
        except AttributeError:
            pass

    rl = _existing_render_layers(tree) or _node(
        tree, _N_RL, 'CompositorNodeRLayers', (-900, 0))

    # Линейный ремап делаем парой Math: (depth - start) / (end - start).
    # Отдельной Map Range в композиторе 5.x уже нет.
    sub = _node(tree, _N_RANGE, _MATH, (-700, -220))
    div = _node(tree, _N_DIV, _MATH, (-540, -220))
    curve = _node(tree, _N_CURVE, _MATH, (-380, -220))
    fog_col = _node(tree, _N_FOGCOL, _RGB, (-440, 160))
    fog_mix = _node(tree, _N_FOGMIX, _MIX, (-220, 0))
    if None in (sub, div, curve, fog_col, fog_mix):
        return tree
    sub.operation = 'SUBTRACT'
    div.operation = 'DIVIDE'
    div.use_clamp = True
    curve.operation = 'POWER'
    curve.use_clamp = True
    _setup_mix(fog_mix, 'MIX')

    # Небо туманом НЕ красим. У фона глубина «бесконечная» (порядка
    # 1e10), фактор выходил равным единице, и весь фон замещался цветом
    # тумана — градиент зенит↔горизонт при этом просто не был виден.
    # В игре fixed-function fog на небо тоже не действует.
    sky_gate = _node(tree, _N_SKY, _MATH, (-540, -380))
    fac_mul = _node(tree, _N_FACMUL, _MATH, (-380, -380))
    if None in (sky_gate, fac_mul):
        return tree
    sky_gate.operation = 'LESS_THAN'
    fac_mul.operation = 'MULTIPLY'
    fac_mul.use_clamp = True

    enc = _node(tree, _N_ENC, _GAMMA, (0, 0))
    gain = _node(tree, _N_GAIN, _RGB, (0, -220))
    mul = _node(tree, _N_MUL, _MIX, (200, 0))
    dec = _node(tree, _N_DEC, _GAMMA, (400, 0))
    if None in (gain, mul):
        return tree
    _setup_mix(mul, 'MULTIPLY')

    comp = _output_node(tree)

    # Чем Composite питался до нас — вернём это при выключении.
    comp_in = _in(comp, _IMG)
    if comp_in is not None and comp_in.is_linked and _PREV_LINK not in scene:
        src = comp_in.links[0].from_node
        if src.name not in _OUR_NODES:
            scene[_PREV_LINK] = [src.name, comp_in.links[0].from_socket.name]

    links = tree.links
    img = _out(rl, ('Image', 'Combined', 'Color'))
    depth = (rl.outputs.get('Depth') or rl.outputs.get('Z')
             or _socket(rl.outputs, ('Depth', 'Z', 'Mist'), 'VALUE'))
    if img is None or comp_in is None:
        return tree

    def _relink(src, dst):
        if dst.is_linked and dst.links[0].from_socket == src:
            return
        for lnk in list(dst.links):
            links.remove(lnk)
        links.new(src, dst)

    fog_fac = _mix_fac(fog_mix)
    fog_a, fog_b = _mix_ab(fog_mix)
    mul_a, mul_b = _mix_ab(mul)
    if None in (fog_a, fog_b, mul_a, mul_b):
        # Сокеты микса не опознались — оставляем дерево как есть, чем
        # рвать чужой композитор полусобранной цепочкой.
        return tree

    wired_fog = depth is not None and fog_fac is not None
    if wired_fog:
        _relink(depth, sub.inputs[0])
        _relink(_out(sub, ('Value',), 'VALUE'), div.inputs[0])
        _relink(_out(div, ('Value',), 'VALUE'), curve.inputs[0])
        _relink(depth, sky_gate.inputs[0])
        fac_a = _socket(fac_mul.inputs, ('Value',), 'VALUE')
        fac_b = _socket(fac_mul.inputs, ('Value',), 'VALUE', skip=(fac_a,))
        _relink(_out(curve, ('Value',), 'VALUE'), fac_a)
        _relink(_out(sky_gate, ('Value',), 'VALUE'), fac_b)
        _relink(_out(fac_mul, ('Value',), 'VALUE'), fog_fac)
    _relink(img, fog_a)
    _relink(_out(fog_col, ('RGBA', 'Color')), fog_b)

    # Gamma-обвязка необязательна: нет такой ноды — множим напрямую.
    post_src = _mix_result(fog_mix)
    enc_in, enc_out = _in(enc, _IMG), _out(enc, _IMG)
    if enc_in is not None and enc_out is not None:
        _relink(post_src, enc_in)
        post_src = enc_out
    _relink(post_src, mul_a)
    _relink(_out(gain, ('RGBA', 'Color')), mul_b)
    mul_fac = _mix_fac(mul)
    if mul_fac is not None:
        mul_fac.default_value = 1.0

    out_src = _mix_result(mul)
    dec_in, dec_out = _in(dec, _IMG), _out(dec, _IMG)
    if dec_in is not None and dec_out is not None:
        _relink(out_src, dec_in)
        out_src = dec_out
    _relink(out_src, comp_in)

    enc_gamma = _in(enc, ('Gamma',), 'VALUE')
    if enc_gamma is not None:
        enc_gamma.default_value = 1.0 / 2.2
    dec_gamma = _in(dec, ('Gamma',), 'VALUE')
    if dec_gamma is not None:
        dec_gamma.default_value = 2.2

    # ВАЖНО: свежая цепочка обязана быть нейтральной. Нода RGB родится
    # ЧЁРНОЙ, а на неё умножается весь кадр — если значения не успели
    # приехать (или применение упало раньше), вьюпорт становится
    # чёрным. Поэтому нейтраль ставим прямо здесь, при сборке.
    neutral = _out(gain, ('RGBA', 'Color'))
    if neutral is not None:
        neutral.default_value = (1.0, 1.0, 1.0, 1.0)
    fog_neutral = _out(fog_col, ('RGBA', 'Color'))
    if fog_neutral is not None:
        fog_neutral.default_value = (0.0, 0.0, 0.0, 1.0)
    _set_const(sub, 1.0e7)      # начало тумана за горизонтом
    _set_const(div, 1.0e6)      # длина спада
    _set_const(curve, 1.0)      # показатель кривой
    _set_const(sky_gate, 1.0e7)  # порог «дальше — небо»

    # Версию помечаем, когда туман подключён — тогда следующий вызов выйдет
    # рано и дерево не пересобирается. Сокет Depth появляется у Render Layers
    # только на следующий тик после включения пасса Z, поэтому первый проход
    # обычно без тумана — даём ему пере-собраться ещё раз и подключиться.
    if wired_fog:
        scene['inu_tc_comp_version'] = _TREE_VERSION
        scene['inu_tc_fog_attempts'] = 0
    else:
        # Но если глубины так и нет (движок/конфиг без Z), нельзя пересобирать
        # ВСЁ дерево на каждый тик слайдера — это тот самый лаг-шторм. После
        # пары попыток штампуем версию и прекращаем: туман без depth не
        # подключится, но пересборки не будет.
        attempts = int(scene.get('inu_tc_fog_attempts', 0)) + 1
        scene['inu_tc_fog_attempts'] = attempts
        print("[INU timecyc] экранный туман: у Render Layers нет выхода "
              "глубины — включите пасс Z в свойствах слоя (попытка %d)"
              % attempts)
        if attempts >= 2:
            scene['inu_tc_comp_version'] = _TREE_VERSION
    return tree


def apply_values(scene, fog=None, postfx_gain=None, sky_threshold=None):
    """Значения экранных стадий. `fog` — (color, start, end, curve) или
    None, если туман выключен; `postfx_gain` — множитель кадра.

    `sky_threshold` — глубина, дальше которой туман не накладывается:
    там уже небо, а на небо fixed-function fog в игре не действует.
    Константы тут мало: глубина фона зависит от clip end вьюпорта, и
    жёсткий порог в 1e6 её просто не ловил — небо заливалось целиком.
    По умолчанию берём чуть дальше конца тумана."""
    tree = comp_tree(scene)
    if tree is None:
        return False
    nodes = tree.nodes

    sub = nodes.get(_N_RANGE)
    div = nodes.get(_N_DIV)
    curve_node = nodes.get(_N_CURVE)
    fog_col = nodes.get(_N_FOGCOL)
    if sub is not None and div is not None and fog_col is not None:
        if fog:
            color, start, end, curve = fog
            end = max(float(end), float(start) + 1.0)
        else:
            # Выключенный туман — порог за горизонтом: цепочка остаётся
            # собранной, но ничего не красит.
            color, start, end, curve = (0.0, 0.0, 0.0), 1.0e7, 1.1e7, 1.0
        _set_const(sub, float(start))
        _set_const(div, max(float(end) - float(start), 1e-3))

        threshold = (float(sky_threshold) if sky_threshold
                     else float(end) * 1.25)
        _set_const(nodes.get(_N_SKY), max(threshold, 1.0))
        col_out = _out(fog_col, ('RGBA', 'Color'))
        if col_out is not None:
            col_out.default_value = (color[0], color[1], color[2], 1.0)
        _set_const(curve_node, max(float(curve), 0.1))

    gain_out = _out(nodes.get(_N_GAIN), ('RGBA', 'Color'))
    if gain_out is not None:
        gain = postfx_gain or (1.0, 1.0, 1.0)
        gain_out.default_value = (
            float(gain[0]), float(gain[1]), float(gain[2]), 1.0)
    return True


def enable_viewport_compositor(context, enable=True):
    """Включить композитор в 3D-вьюпорте — без него экранные стадии
    считаются только на F12."""
    mode = 'ALWAYS' if enable else 'DISABLED'
    touched = 0
    for area in getattr(context.screen, 'areas', ()) or ():
        if area.type != 'VIEW_3D':
            continue
        for space in area.spaces:
            if space.type != 'VIEW_3D':
                continue
            shading = getattr(space, 'shading', None)
            if shading is None or not hasattr(shading, 'use_compositor'):
                continue
            try:
                shading.use_compositor = mode
                touched += 1
            except TypeError:
                pass
    return touched


def viewport_compositor_state(context):
    """(включён_хоть_где, всего_вьюпортов). Нужен панели: экранные
    стадии считаются только при включённом композиторе, и молчаливое
    «тумана нет» обычно означает именно это."""
    on = total = 0
    for area in getattr(context.screen, 'areas', ()) or ():
        if area.type != 'VIEW_3D':
            continue
        for space in area.spaces:
            if space.type != 'VIEW_3D':
                continue
            shading = getattr(space, 'shading', None)
            if shading is None or not hasattr(shading, 'use_compositor'):
                continue
            total += 1
            if str(getattr(shading, 'use_compositor', 'DISABLED')) not in (
                    'DISABLED', 'False'):
                on += 1
    return on, total


def teardown(scene, context=None):
    """Убрать наши ноды и вернуть Composite прежний источник."""
    tree = comp_tree(scene)
    if tree is not None:
        comp = next((n for n in tree.nodes
                     if n.bl_idname in ('CompositorNodeComposite',
                                        'NodeGroupOutput')), None)
        prev = scene.get(_PREV_LINK)
        if comp is not None and prev:
            src = tree.nodes.get(prev[0])
            comp_in = comp.inputs.get('Image')
            if src is not None and comp_in is not None:
                out = src.outputs.get(prev[1])
                if out is not None:
                    for lnk in list(comp_in.links):
                        tree.links.remove(lnk)
                    tree.links.new(out, comp_in)
        for name in _OUR_NODES:
            node = tree.nodes.get(name)
            if node is not None:
                tree.nodes.remove(node)
        node = tree.nodes.get(_N_COMP)
        if node is not None and not any(
                n for n in tree.nodes if n.name in _OUR_NODES):
            tree.nodes.remove(node)

    if scene.get(_PREV_USE_NODES) is False and hasattr(scene, 'use_nodes'):
        try:
            scene.use_nodes = False
        except (AttributeError, TypeError):
            pass
    if scene.get(_PREV_COMP_GROUP) and hasattr(scene, 'compositing_node_group'):
        # Группу заводили мы — её же и отцепляем.
        group = scene.compositing_node_group
        scene.compositing_node_group = None
        if group is not None and getattr(group, 'users', 1) == 0:
            try:
                bpy.data.node_groups.remove(group)
            except (TypeError, ReferenceError):
                pass
    for key in (_PREV_LINK, _PREV_USE_NODES, _PREV_COMP_GROUP,
                'inu_tc_comp_version'):
        if key in scene:
            del scene[key]
    if context is not None:
        enable_viewport_compositor(context, False)
    return True


def gain_to_srgb_scale(gain):
    """Хелпер для мест, где множитель нужно применить к константному
    цвету (например к небу, если экранная стадия выключена)."""
    return tuple(float(g) for g in gain)


def apply_gain_to_color(linear_rgb, gain):
    out = []
    for c, k in zip(linear_rgb, gain):
        out.append(srgb_to_linear(min(max(linear_to_srgb(c) * float(k), 0.0), 1.0)))
    return tuple(out)


def describe(scene, context=None):
    """Полный дамп экранной цепочки — что реально собрано в этой сцене.

    Нужен, когда «туман не работает»: по нему сразу видно, дошли ли
    константы до нужных сокетов, подключена ли глубина и не заливает ли
    порог всё подряд."""
    lines = ["Blender %s" % (getattr(bpy.app, 'version_string',
                                     bpy.app.version),)]

    tree = comp_tree(scene)
    if tree is None:
        lines.append("композитор: дерева нет")
        return chr(10).join(lines)
    lines.append("композитор: %s (версия цепочки %s)"
                 % (tree.name, scene.get('inu_tc_comp_version')))

    for name in _OUR_NODES + (_N_COMP,):
        node = tree.nodes.get(name)
        if node is None:
            lines.append("  %-22s НЕТ" % name)
            continue
        bits = ["%-22s %s" % (name, node.bl_idname)]
        if hasattr(node, 'operation'):
            bits.append("op=%s" % node.operation)
        for sock in node.inputs:
            if sock.is_linked:
                bits.append("%s<-%s.%s" % (sock.name,
                                           sock.links[0].from_node.name,
                                           sock.links[0].from_socket.name))
            elif sock.type == 'VALUE':
                bits.append("%s=%.4g" % (sock.name, sock.default_value))
            elif sock.type == 'RGBA':
                bits.append("%s=%s" % (sock.name,
                                       tuple(round(c, 3) for c in
                                             sock.default_value)))
        for sock in node.outputs:
            if sock.type == 'RGBA' and not sock.is_linked:
                bits.append("out %s=%s" % (sock.name,
                                           tuple(round(c, 3)
                                                 for c in sock.default_value)))
            elif sock.type == 'RGBA':
                bits.append("out %s->%s" % (sock.name,
                                            sock.links[0].to_node.name))
        lines.append("  " + "  ".join(bits))

    try:
        lines.append("pass Z: %s" % [vl.use_pass_z for vl in scene.view_layers])
    except AttributeError:
        lines.append("pass Z: недоступен")

    if context is not None:
        on, total = viewport_compositor_state(context)
        # clip end считаем прямо здесь: диагностика обязана работать,
        # даже если соседний модуль по какой-то причине не грузится.
        clip = 0.0
        for area in getattr(context.screen, 'areas', ()) or ():
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    clip = max(clip, float(space.clip_end))
        lines.append("композитор во вьюпортах: %d из %d, clip end %.1f"
                     % (on, total, clip))
    return chr(10).join(lines)
