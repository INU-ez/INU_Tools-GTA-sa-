# INU_tools.tools.bake.bake_nodes — живой нодовый композит.
#
# Собирает материал-стек Mix-нод из per-map картинок (<base>_<map_id>):
# каждый слой = одна Mix-нода, blend_type = режим слоя, Fac = прозрачность.
# Результат показывается на модели в реальном времени (Material Preview) —
# blend/opacity крутятся без перезапекания. Финальное «сведение» в одну
# текстуру делает numpy-композит (bake_composite) отдельной кнопкой.

import bpy

from .. import compat
from .bake_composite import BLEND_NODE_TYPE


COMPOSITE_MAT = 'INU_BakeComposite'


def build_composite_material(specs, base_name, uv_name):
    """Собрать/пересобрать материал INU_BakeComposite по списку слоёв.

    specs: list[dict(map_id, blend_mode, opacity, enabled)] СНИЗУ ВВЕРХ
           (index 0 = база). Картинки берутся как <base_name>_<map_id>.
    Возвращает материал. Если материал уже на объекте — пересборка его нод
    обновляет живое превью мгновенно.
    """
    mat = (bpy.data.materials.get(COMPOSITE_MAT)
           or bpy.data.materials.new(COMPOSITE_MAT))
    mat.use_nodes = True
    mat.use_fake_user = False
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (500, 0)
    emit = nt.nodes.new('ShaderNodeEmission')
    emit.location = (300, 0)
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])

    enabled = [L for L in specs
               if L.get('enabled')
               and bpy.data.images.get(f"{base_name}_{L['map_id']}") is not None]
    # Список идёт СВЕРХУ ВНИЗ (как в фотошопе): верхний слой накладывается
    # последним. База = НИЖНИЙ слой списка → разворачиваем.
    enabled.reverse()
    if not enabled:
        emit.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
        return mat

    def _img_node(map_id, y):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.get(f"{base_name}_{map_id}")
        n.location = (-900, y)
        n.label = map_id
        if uv_name:
            uvm = nt.nodes.new('ShaderNodeUVMap')
            uvm.uv_map = uv_name
            uvm.location = (-1100, y)
            nt.links.new(uvm.outputs['UV'], n.inputs['Vector'])
        return n

    def _cg(color_out, contrast, gamma, y):
        """Контраст/гамма слоя нодами (если не identity). Формулы 1:1 с
        bake_composite.apply_contrast_gamma → живой превью = numpy-сведение:
          contrast (c−0.5)·k+0.5  → BrightContrast, Contrast = k−1;
          gamma c**(1/g)          → Gamma, Gamma = 1/g.
        Возвращает итоговый Color-сокет."""
        out = color_out
        if contrast != 1.0:
            bc = nt.nodes.new('ShaderNodeBrightContrast')
            bc.location = (-680, y)
            bc.inputs['Bright'].default_value = 0.0
            bc.inputs['Contrast'].default_value = float(contrast) - 1.0
            nt.links.new(out, bc.inputs['Color'])
            out = bc.outputs['Color']
        if gamma != 1.0 and gamma > 0.0:
            g = nt.nodes.new('ShaderNodeGamma')
            g.location = (-680, y - 160)
            g.inputs['Gamma'].default_value = 1.0 / float(gamma)
            nt.links.new(out, g.inputs['Color'])
            out = g.outputs['Color']
        return out

    y = 0
    base = enabled[0]
    acc = _cg(_img_node(base['map_id'], y).outputs['Color'],
              base.get('contrast', 1.0), base.get('gamma', 1.0), y)
    x = -460
    for L in enabled[1:]:
        y -= 320
        top_col = _cg(_img_node(L['map_id'], y).outputs['Color'],
                      L.get('contrast', 1.0), L.get('gamma', 1.0), y)
        wrap = compat.make_mix_rgba(
            nt.nodes,
            blend=BLEND_NODE_TYPE.get(L['blend_mode'], 'MIX'),
            label=L['map_id'])
        wrap.node.location = (x, y // 2)
        wrap.factor.default_value = float(L['opacity'])
        nt.links.new(acc, wrap.a)
        nt.links.new(top_col, wrap.b)
        acc = wrap.result
        x += 220
    nt.links.new(acc, emit.inputs['Color'])
    return mat
