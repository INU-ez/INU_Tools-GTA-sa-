# INU_tools.tools.bake — подсистема запекания карт + композит в текстуру.
#
# Слоистая архитектура (нижний слой не импортирует верхний):
#   bake_composite (чистый numpy, M4)
#       ▲ bake_core   (движок + BakeStateGuard, M1 — этот этап)
#       ▲ bake_maps   (реестр BAKE_MAPS + риги + bevel-нода, M2/M3)
#       ▲ ops/bake_ops.py (операторы, M5)
#       ▲ ui/panels.py + scene_settings.py (M6)
#
# Полное описание: docs/BAKE_FEATURE_PLAN.md.
#
# Пакет import-only: не регистрирует bpy-классы, поэтому до подключения
# операторов (M5) на работающий аддон никак не влияет.

from .bake_core import (
    cycles_available,
    BakeStateGuard,
    setup_target_image,
    prepare_bake_targets,
    restore_bake_targets,
    run_cycles_bake,
    read_image_to_numpy,
    write_numpy_to_image,
)
from .bake_maps import (
    BakeMapDef,
    BAKE_MAPS,
    get_map,
    bake_map_enum_items,
    bake_one_map,
    find_hilow_pair,
    HI_SUFFIX,
    LOW_SUFFIX,
)
from .bake_composite import (
    LayerSpec,
    BLEND_MODES,
    composite_layers,
    linear_to_srgb,
    apply_contrast_gamma,
)

__all__ = [
    # bake_core
    'cycles_available',
    'BakeStateGuard',
    'setup_target_image',
    'prepare_bake_targets',
    'restore_bake_targets',
    'run_cycles_bake',
    'read_image_to_numpy',
    'write_numpy_to_image',
    # bake_maps
    'BakeMapDef',
    'BAKE_MAPS',
    'get_map',
    'bake_map_enum_items',
    'bake_one_map',
    'find_hilow_pair',
    'HI_SUFFIX',
    'LOW_SUFFIX',
    # bake_composite
    'LayerSpec',
    'BLEND_MODES',
    'composite_layers',
    'linear_to_srgb',
    'apply_contrast_gamma',
]
