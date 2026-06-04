# INU_tools.tools.bake.bake_nodes — живой нодовый композит.
#
# Собирает материал-стек Mix-нод из per-map картинок (<base>_<map_id>):
# каждый слой = одна Mix-нода, blend_type = режим слоя, Fac = прозрачность.
# Результат показывается на модели в реальном времени (Material Preview) —
# blend/opacity крутятся без перезапекания. Финальное «сведение» в одну
# текстуру делает numpy-композит (bake_composite) отдельной кнопкой.

import bpy

from .. import compat


COMPOSITE_MAT = 'INU_BakeComposite'

# Наши режимы → blend_type ноды ShaderNodeMix (один-в-один).
_BLEND_TO_NODE = {
    'NORMAL': 'MIX', 'MULTIPLY': 'MULTIPLY', 'ADD': 'ADD',
    'SCREEN': 'SCREEN', 'OVERLAY': 'OVERLAY',
}


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
    if not enabled:
        emit.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
        return mat

    def _img_node(map_id, y):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.get(f"{base_name}_{map_id}")
        n.location = (-800, y)
        n.label = map_id
        if uv_name:
            uvm = nt.nodes.new('ShaderNodeUVMap')
            uvm.uv_map = uv_name
            uvm.location = (-1000, y)
            nt.links.new(uvm.outputs['UV'], n.inputs['Vector'])
        return n

    y = 0
    acc = _img_node(enabled[0]['map_id'], y).outputs['Color']
    x = -500
    for L in enabled[1:]:
        y -= 320
        top = _img_node(L['map_id'], y)
        wrap = compat.make_mix_rgba(
            nt.nodes,
            blend=_BLEND_TO_NODE.get(L['blend_mode'], 'MIX'),
            label=L['map_id'])
        wrap.node.location = (x, y // 2)
        wrap.factor.default_value = float(L['opacity'])
        nt.links.new(acc, wrap.a)
        nt.links.new(top.outputs['Color'], wrap.b)
        acc = wrap.result
        x += 220
    nt.links.new(acc, emit.inputs['Color'])
    return mat
