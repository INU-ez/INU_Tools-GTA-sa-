# INU_tools.ops.floater package marker.
#
# Hosts the floater subsystem split out of viewport_floater.py:
#   * theme      — palette/sizes + _apply_theme() (this file's only consumer for now)
#   * (planned)  gpu_shaders, text_atlas, widgets, base, info/ie/validation/lighting/iii
#
# viewport_floater.py re-imports from these submodules to keep its
# public symbols stable for __init__.py registration.
