"""Dump Blender's current default-theme wcol values + view3d colours
to stdout so we can copy them as constants into the floater code.

Run via:
    blender --background --factory-startup --python dev/dump_theme.py
"""
import bpy


def rgb_str(c):
    return "({:.4f}, {:.4f}, {:.4f}, {:.4f})".format(*tuple(c) + (1.0,)[:max(0, 4 - len(c))])


def dump_wcol(name, w):
    print(f"  {name}:")
    print(f"    inner       = {rgb_str(w.inner)}")
    print(f"    inner_sel   = {rgb_str(w.inner_sel)}")
    print(f"    outline     = {rgb_str(w.outline)}")
    print(f"    item        = {rgb_str(w.item)}")
    print(f"    text        = {rgb_str(w.text)}")
    print(f"    text_sel    = {rgb_str(w.text_sel)}")
    print(f"    show_shaded = {w.show_shaded}")
    print(f"    shadetop    = {w.shadetop}")
    print(f"    shadedown   = {w.shadedown}")
    print(f"    roundness   = {w.roundness}")


def main():
    ui = bpy.context.preferences.themes[0].user_interface
    print("=== user_interface wcol_* ===")
    for slot in ('wcol_regular', 'wcol_tool', 'wcol_toolbar_item',
                 'wcol_radio', 'wcol_text', 'wcol_option', 'wcol_toggle',
                 'wcol_num', 'wcol_numslider', 'wcol_box', 'wcol_menu',
                 'wcol_pulldown', 'wcol_menu_back', 'wcol_menu_item',
                 'wcol_tooltip', 'wcol_scroll', 'wcol_progress',
                 'wcol_list_item', 'wcol_tab'):
        try:
            dump_wcol(slot, getattr(ui, slot))
        except AttributeError:
            print(f"  {slot}: (missing)")

    print()
    print("=== view_3d space colours (full property scan) ===")
    v3d = bpy.context.preferences.themes[0].view_3d
    space = v3d.space
    print(f"  type(space) = {type(space).__name__}")

    # Walk every property exposed by RNA on the space object — catches
    # ThemeSpaceGradient-specific attrs like gradients/panelcolors that
    # were missed by the original hardcoded list.
    def dump_obj(obj, indent="  "):
        try:
            props = list(obj.bl_rna.properties)
        except AttributeError:
            print(f"{indent}(no bl_rna)")
            return
        for prop in props:
            name = prop.identifier
            if name == 'rna_type':
                continue
            try:
                v = getattr(obj, name)
            except Exception as e:
                print(f"{indent}{name} = ERR {e}")
                continue
            t = type(v).__name__
            if t in ('Color', 'bpy_prop_array'):
                try:
                    print(f"{indent}{name} = {rgb_str(v)}")
                except Exception:
                    print(f"{indent}{name} = {tuple(v)!r}")
            elif hasattr(v, 'bl_rna'):
                print(f"{indent}{name}:  ({type(v).__name__})")
                dump_obj(v, indent + "  ")
            else:
                print(f"{indent}{name} = {v!r}")

    dump_obj(space)


if __name__ == "__main__":
    main()
