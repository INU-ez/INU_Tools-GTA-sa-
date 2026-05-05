# INU_tools.tools.compat — Blender API compatibility shims
#
# Минимальная поддерживаемая версия: Blender 2.83 LTS.
# 2.80–2.82 не поддерживаются (отсутствует UILayout.ui_units_x,
# CHECKMARK icon, ряд RNA-различий — критичные панели не рисуются).
# Этот модуль — единственное место где код знает о различиях между
# API-версиями. Все остальные модули обращаются сюда вместо if'ов
# по `bpy.app.version` или try/except'ов на отсутствующие attrs.
#
# Принцип: фичи, которые нельзя бэкпортировать (например VC Layers
# System на color_attributes 3.2+), показывают warning и отключают
# себя через `require_version` / `warn_unsupported`. Фичи, которые
# можно реализовать через старый API — обёрнуты в универсальные
# helper'ы (get_vcols, make_mix_rgba и т.п.).

import bpy


# ── Version constants ────────────────────────────────────────────────

BL = bpy.app.version  # tuple (major, minor, patch)

MIN_SUPPORTED = (2, 83, 0)

# Color Attributes API (mesh.color_attributes) — 3.2+. До этого был
# mesh.vertex_colors (только BYTE_COLOR per-corner).
HAS_COLOR_ATTRIBUTES = BL >= (3, 2, 0)

# ShaderNodeMix (универсальный, RGBA/Vector/Float) — 3.4+. До этого
# для RGBA был ShaderNodeMixRGB с другими input-именами.
HAS_SHADER_NODE_MIX = BL >= (3, 4, 0)

# Bone Collections (armature.collections, bone.collections) — 4.0+.
# До этого bone groups + 32 layer'ов.
HAS_BONE_COLLECTIONS = BL >= (4, 0, 0)

# Principled BSDF v2 — 4.0+. Inputs переименованы: 'Emission' →
# 'Emission Color', subsurface group reshuffled, etc.
HAS_PRINCIPLED_V2 = BL >= (4, 0, 0)

# Layered Actions API (action.layers, slots, channelbag) — 4.4+. До
# этого action.fcurves напрямую.
HAS_LAYERED_ACTIONS = BL >= (4, 4, 0)

# `mesh.calc_normals_split()` убран в 4.1+ (нормали авто-доступны).
HAS_CALC_NORMALS_SPLIT = BL < (4, 1, 0)

# Extension manifest (blender_manifest.toml) — 4.2+. До этого только
# bl_info dict в __init__.py.
HAS_EXTENSION_MANIFEST = BL >= (4, 2, 0)


# ── Icon name shims ──────────────────────────────────────────────────
# Иконка 'CHECKMARK' появилась в 2.81. На 2.80 её нет — UILayout кидает
# исключение каждый кадр в draw_header(), что роняет UI до 2 fps. Любая
# незнакомая иконка вызывает тот же эффект — TypeError на enum, и весь
# оставшийся draw() в panel'е обрывается, кнопки/чекбоксы пропадают.
#
# Решение: на module-load интроспектируем реальный enum из bpy.types.
# safe_icon() возвращает запрошенную иконку если есть, иначе из таблицы
# ручных fallback'ов, иначе 'BLANK1' (везде валидный пустой 16×16).

def _collect_valid_icons():
    """Прочитать enum_items у UILayout.label.icon — возвращает set
    реальных иконок текущего Blender'а, или None при ошибке."""
    try:
        items = (bpy.types.UILayout.bl_rna
                 .functions['label']
                 .parameters['icon']
                 .enum_items)
        return set(items.keys())
    except Exception:
        return None


_VALID_ICONS = _collect_valid_icons()

# Ручные substitution'ы для важных «модернизированных» иконок —
# подобраны по смыслу/визуалу. Если новой иконки нет на старом
# Blender'е, подставляем ближайший аналог. Расширяется по мере
# обнаружения новых случаев.
_ICON_FALLBACKS = {
    'CHECKMARK':           'FILE_TICK',
    'OUTLINER_COLLECTION': 'GROUP',
    'IMAGE_RGB_ALPHA':     'IMAGE_RGB',
    'COLLECTION':          'GROUP',
    'COLLECTION_NEW':      'NEW',
    'GP_SELECT_POINTS':    'PARTICLE_POINT',
    'CURRENT_FILE':        'FILE_BLEND',
    'TOPBAR':              'WINDOW',
    'STATUSBAR':           'WINDOW',
    'WORKSPACE':           'WORKSPACE',  # есть на 2.80
    'CON_OBJECTSOLVER':    'CONSTRAINT',
    'BLENDER_LOGO_LARGE':  'BLENDER',
}


def safe_icon(name):
    """Вернуть `name` если иконка валидна в текущем Blender'е, иначе
    fallback из таблицы либо 'BLANK1' (универсально пустой слот).

    На современном Blender'е (≥ 2.81) — pass-through для всего, что
    использует аддон. Активная подмена включается только если иконки
    физически нет в enum'е — т.е. на старых версиях."""
    if _VALID_ICONS is None:
        return name  # introspection failed — trust caller
    if name in _VALID_ICONS:
        return name
    fb = _ICON_FALLBACKS.get(name)
    if fb is not None and fb in _VALID_ICONS:
        return fb
    return 'BLANK1' if 'BLANK1' in _VALID_ICONS else 'NONE'


# Backward-compat constant — раньше было `ICON_CHECK`, оставляем для
# уже подставленных мест.
ICON_CHECK = safe_icon('CHECKMARK')


# ── Vertex color attribute helpers ───────────────────────────────────
# Унифицированный API поверх mesh.color_attributes (3.2+) и старого
# mesh.vertex_colors (≤ 3.1). Все вызывающие модули должны
# использовать только эти функции, не лезть в mesh.* напрямую.

def vcol_collection(mesh):
    """Возвращает collection-объект (color_attributes или vertex_colors)."""
    if HAS_COLOR_ATTRIBUTES:
        return mesh.color_attributes
    return mesh.vertex_colors


def vcol_list(mesh):
    """Возвращает list всех vcol-слоёв."""
    return list(vcol_collection(mesh))


def vcol_get(mesh, name):
    """Возвращает vcol-слой по имени, либо None."""
    coll = vcol_collection(mesh)
    return coll.get(name)


def vcol_new(mesh, name, *, domain='CORNER', dtype='BYTE_COLOR'):
    """Создаёт новый vcol-слой.

    На 2.80-3.1 domain/dtype игнорируются (всегда CORNER + BYTE_COLOR).
    На 3.2+ domain может быть 'POINT' или 'CORNER'; dtype —
    'BYTE_COLOR' или 'FLOAT_COLOR'.

    Если на старом Blender'е запрошен FLOAT_COLOR — silently fallback
    на BYTE_COLOR (точность урежется до 8 бит/канал).
    """
    if HAS_COLOR_ATTRIBUTES:
        return mesh.color_attributes.new(name=name, type=dtype, domain=domain)
    return mesh.vertex_colors.new(name=name)


def vcol_remove(mesh, layer):
    """Удалить vcol-слой."""
    if HAS_COLOR_ATTRIBUTES:
        mesh.color_attributes.remove(layer)
    else:
        mesh.vertex_colors.remove(layer)


def vcol_active(mesh, layer=None):
    """Get/set активного vcol-слоя.

    layer=None → возвращает активный слой.
    layer=<layer> → ставит активным.
    """
    if HAS_COLOR_ATTRIBUTES:
        if layer is None:
            return mesh.color_attributes.active_color
        mesh.color_attributes.active_color = layer
        return layer
    if layer is None:
        return mesh.vertex_colors.active
    mesh.vertex_colors.active = layer
    return layer


def vcol_layer_name(layer):
    """Имя vcol-слоя (одинаково для обоих API, но wrapper для будущего)."""
    return layer.name


def vcol_data_type(layer):
    """'BYTE_COLOR' / 'FLOAT_COLOR'. На 2.80-3.1 всегда 'BYTE_COLOR'."""
    if HAS_COLOR_ATTRIBUTES:
        return getattr(layer, 'data_type', 'BYTE_COLOR')
    return 'BYTE_COLOR'


def vcol_domain(layer):
    """'POINT' / 'CORNER'. На 2.80-3.1 всегда 'CORNER'."""
    if HAS_COLOR_ATTRIBUTES:
        return getattr(layer, 'domain', 'CORNER')
    return 'CORNER'


# ── Shader node helpers ──────────────────────────────────────────────

# Mix node identifier + socket name constants — версионно-зависимые.
# Старый ShaderNodeMixRGB и новый ShaderNodeMix имеют разные имена
# input'ов и output'ов; чтобы каждый call-site не делал if-version,
# держим имена тут как константы.
if HAS_SHADER_NODE_MIX:
    MIX_NODE_TYPE = 'ShaderNodeMix'
    MIX_INPUT_FACTOR = 'Factor'
    MIX_INPUT_A = 'A'
    MIX_INPUT_B = 'B'
    MIX_OUTPUT_RESULT = 'Result'
else:
    MIX_NODE_TYPE = 'ShaderNodeMixRGB'
    MIX_INPUT_FACTOR = 'Fac'
    MIX_INPUT_A = 'Color1'
    MIX_INPUT_B = 'Color2'
    MIX_OUTPUT_RESULT = 'Color'


def setup_mix_rgba_node(node, *, blend='MIX'):
    """Сконфигурировать только что созданный mix-узел как RGBA-blend.

    На 3.4+ ставит data_type='RGBA' (на старых нет такого свойства).
    Всегда ставит blend_type. Используется парой с
    nodes.new(compat.MIX_NODE_TYPE).
    """
    if HAS_SHADER_NODE_MIX:
        node.data_type = 'RGBA'
    node.blend_type = blend


class _MixWrap:
    """Унифицированный handle поверх ShaderNodeMix или ShaderNodeMixRGB.

    Интерфейс одинаковый: .node, .factor, .a, .b, .result — везде
    socket'ы. Каллер может писать `wrap.factor.default_value = ...`
    и `links.new(wrap.result, ...)` без знаний о версии Blender.
    """
    __slots__ = ('node', 'factor', 'a', 'b', 'result')

    def __init__(self, node, factor, a, b, result):
        self.node = node
        self.factor = factor
        self.a = a
        self.b = b
        self.result = result


def make_mix_rgba(nodes, *, blend='MIX', name=None, label=None):
    """Создать RGBA-mix узел совместимо для всех версий.

    На 3.4+ → ShaderNodeMix с data_type='RGBA'.
    На 2.80-3.3 → ShaderNodeMixRGB.

    Возвращает _MixWrap с унифицированными socket'ами.
    """
    if HAS_SHADER_NODE_MIX:
        n = nodes.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        n.blend_type = blend
        wrap = _MixWrap(n,
                        factor=n.inputs['Factor'],
                        a=n.inputs['A'],
                        b=n.inputs['B'],
                        result=n.outputs['Result'])
    else:
        n = nodes.new('ShaderNodeMixRGB')
        n.blend_type = blend
        wrap = _MixWrap(n,
                        factor=n.inputs['Fac'],
                        a=n.inputs['Color1'],
                        b=n.inputs['Color2'],
                        result=n.outputs['Color'])
    if name is not None:
        n.name = name
    if label is not None:
        n.label = label
    return wrap


def find_mix_rgba(nodes, name):
    """Найти ранее созданный mix-узел и вернуть _MixWrap (или None)."""
    n = nodes.get(name)
    if n is None:
        return None
    if n.bl_idname == 'ShaderNodeMix':
        return _MixWrap(n,
                        factor=n.inputs['Factor'],
                        a=n.inputs['A'],
                        b=n.inputs['B'],
                        result=n.outputs['Result'])
    if n.bl_idname == 'ShaderNodeMixRGB':
        return _MixWrap(n,
                        factor=n.inputs['Fac'],
                        a=n.inputs['Color1'],
                        b=n.inputs['Color2'],
                        result=n.outputs['Color'])
    return None


def principled_emission_input(principled_node):
    """Возвращает input-socket эмиссии у Principled BSDF.

    На 4.0+ это 'Emission Color', до 4.0 — 'Emission'.
    """
    return (principled_node.inputs.get('Emission Color')
            or principled_node.inputs.get('Emission'))


# ── Operator gating helpers ──────────────────────────────────────────

def supports(min_ver) -> bool:
    """True если текущий Blender ≥ min_ver."""
    return BL >= tuple(min_ver)


def version_str(ver) -> str:
    """(4, 0, 0) → '4.0'. (3, 2, 0) → '3.2'."""
    return f"{ver[0]}.{ver[1]}" + (f".{ver[2]}" if len(ver) > 2 and ver[2] else "")


def require_version_message(feature_name, min_ver) -> str:
    """Стандартный текст сообщения для unsupported фичи."""
    return f"{feature_name}: требуется Blender {version_str(min_ver)}+ (у вас {version_str(BL)})"


def warn_unsupported(operator, feature_name, min_ver):
    """Отчёт о неподдерживаемой фиче в self.report() оператора.

    Использование:
        if not supports((3, 2, 0)):
            return warn_unsupported(self, "VC Layers", (3, 2, 0))

    Возвращает {'CANCELLED'} — можно сразу `return`.
    """
    operator.report({'ERROR'}, require_version_message(feature_name, min_ver))
    return {'CANCELLED'}


# ── Module load sanity check ─────────────────────────────────────────

if BL < MIN_SUPPORTED:
    # Если кто-то всё-таки запустил аддон на ещё более древнем Blender'е —
    # не падать молча, а явно сказать.
    print(f"[INU Tools] WARNING: Blender {version_str(BL)} ниже "
          f"минимально поддерживаемого {version_str(MIN_SUPPORTED)}. "
          f"Часть функций может не работать.")
