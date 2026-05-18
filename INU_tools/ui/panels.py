# INU_tools.ui.panels — every Blender Panel and UIList class.
#
# Phase 4 (2026-04-26): all panels moved out of __init__.py into a
# single module. Material panel and its 3 draw helpers also recovered
# from ops/col_surface_ops.py where Phase 3 batch script wrongly
# moved them.
#
# Helpers used by draw() methods (e.g. _draw_label_with_info, surface
# name lookup, particle enum items) live in __init__.py — pulled in
# lazily inside each method. T() is top-level since panel class bodies
# use T(...) at class-definition time.

import ast
import bpy

from .. import T
from ..tools import compat
from ..tools.compat import safe_icon
from ..ui.registry import apply_order


def _draw_material_surface(layout, mat):
    """SURFACE tab — COL physical surface type + Day/Night light."""
    from .. import get_surface_name
    inu = mat.inu
    current_id = inu.col_mat_index
    current_name = get_surface_name(current_id)

    row = layout.row(align=True)
    row.prop(inu, "col_mat_index", text="ID")
    op = row.operator("gtatools.col_surface_menu", text="", icon=safe_icon('VIEWZOOM'))
    op.material_name = mat.name

    layout.label(text=f"{current_name}", icon=safe_icon('PHYSICS'))

    layout.separator()

    row = layout.row(align=True)
    row.prop(inu, "col_day_light", text=T("Дневной свет"))
    row.prop(inu, "col_night_light", text=T("Ночной свет"))

    layout.prop(inu, "col_brightness", text=T("Яркость"))



def _draw_material_effects(layout, mat):
    """EFFECTS tab — RW material effects (env map, bump, specular,
    reflection, dual texture, UV anim) + ambient + vehicle color slot."""
    inu = mat.inu

    layout.prop(inu, "ambient", text=T("Фоновое затенение"))

    box = layout.box()
    row = box.row()
    row.label(text=T("Слот цвета машины:"), icon=safe_icon('AUTO'))
    box.prop(inu, "vehicle_color_slot", text="")
    if inu.vehicle_color_slot != 'NONE':
        box.operator("gtatools.sa_vehicle_preset", text=T("Применить SA Vehicle defaults"), icon=safe_icon('SHADING_RENDERED'))

    # ── Vehicle Paintjob (Pay'n'Spray alt textures) ──
    # These two images are packed into the vehicle's TXD as
    # <base>_paintjob1 / <base>_paintjob2 — the game swaps them with the
    # main body texture at runtime when the player buys a paintjob.
    pj_box = layout.box()
    pj_row = pj_box.row()
    pj_row.label(text=T("Paintjob (Pay'n'Spray):"), icon=safe_icon('BRUSH_DATA'))
    has_pj = bool(inu.paintjob_alt_1 or inu.paintjob_alt_2)
    if has_pj:
        pj_row.operator("gtatools.validate_paintjobs",
                        text="", icon=compat.ICON_CHECK)
    pj_box.template_ID(inu, "paintjob_alt_1", open="image.open",
                       text=T("Раскраска 1"))
    pj_box.template_ID(inu, "paintjob_alt_2", open="image.open",
                       text=T("Раскраска 2"))
    if has_pj and not (inu.paintjob_alt_1 and inu.paintjob_alt_2):
        pj_box.label(
            text=T("Нужны обе альтернативы (1 и 2)"),
            icon=safe_icon('ERROR'))

    layout.separator()

    box = layout.box()
    row = box.row()
    row.prop(inu, "export_env_map", text=T("Карта окружения"))
    if inu.export_env_map:
        box.prop(inu, "env_map_tex", text=T("Текстура"))
        box.prop(inu, "env_map_coef", text=T("Коэффициент"))
        box.prop(inu, "env_map_fb_alpha", text=T("Использовать FB Alpha"))

    box = layout.box()
    row = box.row()
    row.prop(inu, "export_bump_map", text=T("Карта высот"))
    if inu.export_bump_map:
        box.prop(inu, "bump_map_tex", text=T("Текстура карты высот"))

    box = layout.box()
    row = box.row()
    row.prop(inu, "export_reflection", text=T("Отражение материала"))
    if inu.export_reflection:
        row = box.row(align=True)
        row.prop(inu, "reflection_scale_x", text=T("Масштаб X"))
        row.prop(inu, "reflection_scale_y", text="Y")
        row = box.row(align=True)
        row.prop(inu, "reflection_offset_x", text=T("Смещение X"))
        row.prop(inu, "reflection_offset_y", text="Y")
        box.prop(inu, "reflection_intensity", text=T("Интенсивность"))

    box = layout.box()
    row = box.row()
    row.prop(inu, "export_specular", text=T("Зеркальный материал"))
    if inu.export_specular:
        box.prop(inu, "specular_level", text=T("Уровень зеркальности"))
        box.prop(inu, "specular_texture", text=T("Текстура"))

    box = layout.box()
    row = box.row()
    row.prop(inu, "export_dual_tex", text="Blend Mode (Src/Dst)")
    if inu.export_dual_tex:
        box.prop(inu, "dual_tex_src_blend", text="Src")
        box.prop(inu, "dual_tex_dst_blend", text="Dst")
        box.prop(inu, "dual_tex_texture", text=T("Текстура"))

    box = layout.box()
    row = box.row()
    row.prop(inu, "export_animation", text=T("UV Анимация"))
    if inu.export_animation:
        box.prop(inu, "animation_name", text=T("Имя анимации"))

    box = layout.box()
    row = box.row(align=True)
    row.prop(inu, "uv_anim_write", text=T("Писать UV Anim в DFF"))
    if inu.uv_anim_write:
        row = box.row(align=True)
        row.prop(inu, "uv_anim_speed_u", text="Speed U")
        row.prop(inu, "uv_anim_speed_v", text="Speed V")
        box.prop(inu, "uv_anim_duration", text=T("Длительность"))



def _draw_sort_materials_menu(self, context):
    """Append sort button to material context menu"""
    self.layout.separator()
    self.layout.operator("gtatools.sort_materials", text=T("Сортировка материалов"), icon=safe_icon('SORTALPHA'))


# ── 2DFX Light flags1/flags2 — bit-by-bit named toggles ───────────
# Per-bit tooltips live on the operator (`description` classmethod in
# effects_ops._2DFX_BIT_TOOLTIPS) so hovering a flag button shows
# what the bit actually does.
#
# Bits are grouped *semantically* in the UI (visibility / corona-fx /
# blinking / advanced) instead of by raw byte (flags1/flags2). Users
# don't think in terms of "byte 1 vs byte 2" — they think "I want
# this thing to blink at night". Each tuple is (prop_name, bit, label).
_2DFX_GROUP_VISIBILITY = (
    ("2dfx_flags1", 6, "AT_DAY"),
    ("2dfx_flags1", 7, "AT_NIGHT"),
    ("2dfx_flags1", 3, "Without Corona"),
    ("2dfx_flags1", 0, "Check Obstacles"),
)
_2DFX_GROUP_CORONA = (
    ("2dfx_flags1", 4, "Corona Reflects"),
    ("2dfx_flags1", 5, "Corona Flare"),
)
_2DFX_GROUP_BLINK = (
    ("2dfx_flags2", 0, "Blink 1"),
    ("2dfx_flags2", 1, "Blink 2"),
    ("2dfx_flags2", 2, "Blink 3"),
    ("2dfx_flags2", 7, "Police Light"),
    ("2dfx_flags2", 3, "Traffic Light"),
    ("2dfx_flags2", 4, "Train Crossing"),
)
_2DFX_GROUP_ADVANCED = (
    ("2dfx_flags1", 1, "Fog Type 1"),
    ("2dfx_flags1", 2, "Fog Type 2"),
    ("2dfx_flags2", 5, "Update Height"),
    ("2dfx_flags2", 6, "Check Direction"),
)


def _draw_2dfx_flag_group(parent, obj, group, header):
    """Draw a labeled group of bit-toggle buttons in 2-column grid.
    Each button XOR-toggles its bit via gtatools.toggle_2dfx_flag_bit;
    the operator's `description` classmethod supplies per-bit tooltip."""
    parent.label(text=header, icon=safe_icon('LIGHT_DATA'))
    grid = parent.column(align=True)
    pairs = [group[i:i + 2] for i in range(0, len(group), 2)]
    for pair in pairs:
        row = grid.row(align=True)
        for prop_name, bit, label in pair:
            cur = int(obj.get(prop_name, 0))
            depressed = bool(cur & (1 << bit))
            op = row.operator(
                "gtatools.toggle_2dfx_flag_bit",
                text=label, depress=depressed,
            )
            op.prop_name = prop_name
            op.bit = bit
        # Pad with empty cell if odd count, so single button doesn't
        # stretch full-width.
        if len(pair) == 1:
            row.label(text="")


def _draw_2dfx_flag_box(parent, obj):
    """Render 4 semantic flag groups inside the parent box. Caller is
    responsible for the collapsible header — this just draws content.
    Groups stacked into one aligned column so Blender collapses the
    inter-row gap; the bold group label alone separates them visually."""
    col = parent.column(align=True)
    _draw_2dfx_flag_group(col, obj, _2DFX_GROUP_VISIBILITY,
                          T("Видимость:"))
    _draw_2dfx_flag_group(col, obj, _2DFX_GROUP_CORONA,
                          T("Эффекты короны:"))
    _draw_2dfx_flag_group(col, obj, _2DFX_GROUP_BLINK,
                          T("Мерцание:"))
    _draw_2dfx_flag_group(col, obj, _2DFX_GROUP_ADVANCED,
                          T("Доп.:"))



class GTATOOLS_PT_material_panel(bpy.types.Panel):
    """Unified GTA SA Material panel — SURFACE / EFFECTS / PIPELINE tabs."""
    bl_label = "GTA Material"
    bl_idname = "GTATOOLS_PT_material_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    @classmethod
    def poll(cls, context):
        return context.material is not None

    def draw(self, context):
        layout = self.layout
        mat = context.material

        # Tab row at the top — expand=True renders enum as a button row.
        layout.prop(mat.inu, "material_tab", expand=True)
        layout.separator()

        tab = mat.inu.material_tab
        if tab == 'SURFACE':
            _draw_material_surface(layout, mat)
        elif tab == 'EFFECTS':
            _draw_material_effects(layout, mat)
        else:  # PIPELINE
            from ..tools.gta_material_panel import draw_pipeline_tab
            draw_pipeline_tab(layout, context)





class GTATOOLS_UL_txd_export_plan(bpy.types.UIList):
    """Per-model TXD name editor shown in the Export-to-IMG dialog."""
    bl_idname = "GTATOOLS_UL_txd_export_plan"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        row = layout.row(align=True)
        row.prop(item, "include", text="")
        sub = row.row(align=True)
        sub.active = item.include
        sub.label(text=item.model_name, icon=safe_icon('MESH_DATA'))
        sub.prop(item, "txd_name", text="", icon=safe_icon('TEXTURE'))



class GTATOOLS_UL_img_files(bpy.types.UIList):
    """Scrollable list of files in IMG archive."""
    bl_idname = "GTATOOLS_UL_img_files"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        ext = item.name.rsplit('.', 1)[-1].lower() if '.' in item.name else ''
        icons = {'dff': 'MESH_DATA', 'col': 'MESH_CUBE', 'txd': 'TEXTURE', 'ipl': 'EMPTY_AXIS'}
        layout.label(text=item.name, icon=icons.get(ext, 'FILE'))

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt_flags = [self.bitflag_filter_item] * len(items)
        # Keep original order — no sorting
        flt_neworder = []

        if self.filter_name:
            search = self.filter_name.lower()
            for i, item in enumerate(items):
                if search not in item.name.lower():
                    flt_flags[i] = 0

        return flt_flags, flt_neworder




class GTATOOLS_PT_main_panel(bpy.types.Panel):
    """Главная панель GTA Tools — root of the N-sidebar tab. Not in
    PANELS registry: roots have no bl_order (they own the tab) and
    Phase 5 will need one root per tab, handled separately."""
    bl_label = "GTA Tools"
    bl_idname = "GTATOOLS_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GTA Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # ── Onboarding row ──
        # Three icon buttons that lead a fresh user to docs / issues /
        # release notes. Without this, a new install dumps 14 panels in
        # the sidebar with no pointer to the manual; from the N-tab
        # there's no other way to reach docs/. URLs are GitHub-hosted
        # so they survive the addons-folder install path that strips
        # everything but the INU_tools/ module.
        row = layout.row(align=True)
        row.operator("gtatools.open_docs",
                     text=T("Docs"), icon=safe_icon('HELP'))
        row.operator("gtatools.open_issues",
                     text=T("Issues"), icon=safe_icon('URL'))
        row.operator("gtatools.whats_new",
                     text="", icon=safe_icon('SOLO_ON'))

        # ── Profile switcher ──
        # ALL = no filter, default order. User profiles are saved in
        # INU_Preset/profiles/ and govern both visibility and order.
        # +/- manage profiles; the gear button opens the layout editor
        # popup (where pick-and-place + eye-toggle live) so the main
        # panel stays compact. Label is dropped — the dropdown itself
        # shows the active profile name, and «Профиль» got truncated
        # to «Проф…» on narrow sidebars while empty space sat next
        # to the dropdown.
        row = layout.row(align=True)
        row.prop(scene.inu_settings, "gtatools_profile", text="", icon=safe_icon('PRESET'))
        row.operator("gtatools.profile_save", text="", icon=safe_icon('ADD'))
        del_btn = row.row(align=True)
        del_btn.enabled = (scene.inu_settings.gtatools_profile != 'ALL')
        del_btn.operator("gtatools.profile_delete", text="", icon=safe_icon('REMOVE'))
        edit_btn = row.row(align=True)
        edit_btn.enabled = (scene.inu_settings.gtatools_profile != 'ALL')
        edit_btn.operator("gtatools.profile_edit", text="", icon=safe_icon('PREFERENCES'))





@apply_order
class GTATOOLS_PT_ide_ipl_panel(bpy.types.Panel):
    """Панель IDE / IPL / IMG для работы с существующими файлами GTA SA"""
    bl_label = "IDE / IPL / IMG"
    bl_idname = "GTATOOLS_PT_ide_ipl_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('PACKAGE'))

    def draw(self, context):
        import os
        layout = self.layout
        scn = context.scene

        # IDE + IPL side-by-side — narrow N-panel still fits since
        # both columns hold short button labels. Counts tooltip stays
        # in the header row of each box so the user can spot empty
        # files at a glance.
        cols_row = layout.row(align=True)
        col_ide = cols_row.column(align=True)
        col_ipl = cols_row.column(align=True)

        # IDE section
        box = col_ide.box()
        row = box.row(align=True)
        row.label(text="IDE", icon=safe_icon('TEXT'))
        ide_path = bpy.path.abspath(scn.inu_settings.gtatools_ide_path)
        if ide_path and os.path.isfile(ide_path):
            try:
                from ..core.ide import read_ide
                _ide = read_ide(ide_path)
                counts = []
                if _ide.objects: counts.append(f"objs: {len(_ide.objects)}")
                if _ide.anims: counts.append(f"anim: {len(_ide.anims)}")
                if _ide.cars: counts.append(f"cars: {len(_ide.cars)}")
                if _ide.peds: counts.append(f"peds: {len(_ide.peds)}")
                if _ide.txdps: counts.append(f"txdp: {len(_ide.txdps)}")
                if counts:
                    info_text = ", ".join(counts)
                    op = row.operator("gtatools.info_tooltip", text=info_text, icon=safe_icon('INFO'), emboss=False)
                    op.tooltip = T("Количество записей в IDE файле")
            except Exception:
                pass
        # Short un-translated labels — icons already carry the
        # meaning, and "Add/Del/Import/Export" are universally
        # readable across both Russian and English UIs. translate=
        # False is critical here: without it Blender's built-in
        # i18n catches "Add"/"Export"/etc. and swaps them for the
        # localised forms ("Добавить", "Экспортировать") which then
        # truncate in the narrow column.
        row = box.row(align=True)
        row.operator("gtatools.upsert_ide", text="Add",
                     icon=safe_icon('ADD'), translate=False)
        row.operator("gtatools.remove_ide", text="Del",
                     icon=safe_icon('REMOVE'), translate=False)
        row = box.row(align=True)
        row.operator("gtatools.import_ide", text="Import",
                     icon=safe_icon('IMPORT'), translate=False)
        row.operator("gtatools.export_ide", text="Export",
                     icon=safe_icon('EXPORT'), translate=False)

        # IPL section
        box = col_ipl.box()
        row = box.row(align=True)
        row.label(text="IPL", icon=safe_icon('EMPTY_AXIS'))
        ipl_path = bpy.path.abspath(scn.inu_settings.gtatools_ipl_path)
        if ipl_path and os.path.isfile(ipl_path):
            try:
                from ..core.ipl import read_ipl
                _ipl = read_ipl(ipl_path)
                counts = []
                if _ipl.instances: counts.append(f"inst: {len(_ipl.instances)}")
                if _ipl.culls: counts.append(f"cull: {len(_ipl.culls)}")
                if _ipl.garages: counts.append(f"grge: {len(_ipl.garages)}")
                if _ipl.enexs: counts.append(f"enex: {len(_ipl.enexs)}")
                if _ipl.pickups: counts.append(f"pick: {len(_ipl.pickups)}")
                if _ipl.cars: counts.append(f"cars: {len(_ipl.cars)}")
                if _ipl.jumps: counts.append(f"jump: {len(_ipl.jumps)}")
                if _ipl.auzos: counts.append(f"auzo: {len(_ipl.auzos)}")
                if _ipl.occls: counts.append(f"occl: {len(_ipl.occls)}")
                if _ipl.zones: counts.append(f"zone: {len(_ipl.zones)}")
                if counts:
                    info_text = ", ".join(counts)
                    op = row.operator("gtatools.info_tooltip", text=info_text, icon=safe_icon('INFO'), emboss=False)
                    op.tooltip = T("Количество записей в IPL файле")
            except Exception:
                pass
        row = box.row(align=True)
        row.operator("gtatools.upsert_ipl", text="Add",
                     icon=safe_icon('ADD'), translate=False)
        row.operator("gtatools.remove_ipl", text="Del",
                     icon=safe_icon('REMOVE'), translate=False)
        row = box.row(align=True)
        row.operator("gtatools.import_ipl", text="Import",
                     icon=safe_icon('IMPORT'), translate=False)
        row.operator("gtatools.export_ipl", text="Export",
                     icon=safe_icon('EXPORT'), translate=False)

        # Below the two columns — niche IPL utilities that don't
        # need to live inside the per-format box. Full panel width
        # gives the labels room to breathe.
        row = layout.row(align=True)
        row.operator("gtatools.import_ipl_sections", text=T("Секции IPL"), icon=safe_icon('IMPORT'))
        row.operator("gtatools.export_ipl_sections", text=T("Секции IPL"), icon=safe_icon('EXPORT'))
        layout.operator("gtatools.replace_ipl_placeholders", text=T("Заменить Empty"), icon=safe_icon('MESH_DATA'))

        # IMG section — kept just import-side toggles + the three
        # IMG ops. DFF/COL/LOD/TXD format pickers + COL library +
        # shared TXD all live in the «Экспорт в IMG» dialog now,
        # and the standalone «Общий TXD» button duplicates the
        # shared-TXD toggle inside that same dialog.
        box = layout.box()
        row = box.row(align=True)
        row.label(text="IMG", icon=safe_icon('PACKAGE'))
        row = box.row(align=True)
        row.prop(scn.inu_settings, "gtatools_img_skip_lod", text="Skip LOD", toggle=True)
        row.prop(scn.inu_settings, "gtatools_img_load_txd", text="TXD", toggle=True)
        row.prop(scn.inu_settings, "gtatools_map_load_col", text="COL", toggle=True)
        box.operator("gtatools.import_from_img", text=T("Импорт из IMG"), icon=safe_icon('IMPORT'))
        box.operator("gtatools.export_to_img",
                     text=T("Экспорт в IMG"),
                     icon=safe_icon('EXPORT'))
        box.operator("gtatools.remove_from_img", text=T("Удалить из IMG"), icon=safe_icon('REMOVE'))





# ── Popover-меню для точечного импорта/экспорта одного формата.
# Заменяют 8 отдельных кнопок (4 import + 4 export) на 2 menu-dropdown'а.
class GTATOOLS_MT_import_menu(bpy.types.Menu):
    bl_label = "INU: Импорт"
    bl_idname = "GTATOOLS_MT_import_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("gtatools.import_dff", text="DFF", icon=safe_icon('MESH_DATA'))
        layout.operator("gtatools.import_col", text="COL", icon=safe_icon('MESH_ICOSPHERE'))
        layout.operator("gtatools.import_cst", text="CST (Steve's)", icon=safe_icon('TEXT'))
        layout.operator("gtatools.import_txd", text="TXD", icon=safe_icon('IMAGE_DATA'))
        layout.separator()
        layout.operator("gtatools.inu_import", text="All", icon=safe_icon('FILE'), translate=False)


class GTATOOLS_MT_export_menu(bpy.types.Menu):
    bl_label = "INU: Экспорт"
    bl_idname = "GTATOOLS_MT_export_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("gtatools.export_dff", text="DFF", icon=safe_icon('MESH_DATA'))
        layout.operator("gtatools.export_col", text="COL", icon=safe_icon('MESH_ICOSPHERE'))
        layout.operator("gtatools.export_cst", text="CST (Steve's)", icon=safe_icon('TEXT'))
        layout.operator("gtatools.export_txd", text="TXD", icon=safe_icon('IMAGE_DATA'))
        layout.separator()
        layout.operator("gtatools.export_all",
                        text=T("All → Папка"), icon=safe_icon('FILE_FOLDER'))
        layout.operator("gtatools.export_to_img",
                        text=T("All → IMG"), icon=safe_icon('PACKAGE'))


# ── Menu: Create 2DFX effect ────────────────────────────────────
# Replaces 4 buttons (Light/Particle/Ped Attractor/Sun Glare) with one
# dropdown — each item just calls the same operator with a different
# effect_type. Clusters effect choice in one well-known UI pattern.
class GTATOOLS_MT_create_2dfx(bpy.types.Menu):
    bl_label = "INU: Создать 2DFX"
    bl_idname = "GTATOOLS_MT_create_2dfx"

    def draw(self, context):
        layout = self.layout
        op = layout.operator("gtatools.create_2dfx", text=T("Свет"),
                             icon=safe_icon('LIGHT_POINT'))
        op.effect_type = 'LIGHT'
        op = layout.operator("gtatools.create_2dfx", text=T("Частица"),
                             icon=safe_icon('PARTICLES'))
        op.effect_type = 'PARTICLE'
        op = layout.operator("gtatools.create_2dfx", text="Ped Attractor",
                             icon=safe_icon('COMMUNITY'))
        op.effect_type = 'PED_ATTRACTOR'
        op = layout.operator("gtatools.create_2dfx", text=T("Блик солнца"),
                             icon=safe_icon('LIGHT_SUN'))
        op.effect_type = 'SUN_GLARE'


# ── Menu: Radar generation modes ────────────────────────────────
# 5 separate mode buttons (ALL / MENU / FULL / FULL_MENU / SPECIFIC) →
# one dropdown. The "Specific" item still requires the user to fill
# the «Индексы» field on the panel — the menu just triggers, doesn't
# replace the parameter row.
class GTATOOLS_MT_radar_generate(bpy.types.Menu):
    bl_label = "INU: Генерировать радар"
    bl_idname = "GTATOOLS_MT_radar_generate"

    def draw(self, context):
        layout = self.layout
        op = layout.operator("gtatools.radar_generate",
                             text=T("Генерировать радар"),
                             icon=safe_icon('RENDER_RESULT'))
        op.mode = 'ALL'
        op = layout.operator("gtatools.radar_generate",
                             text=T("Меню радар (3x3)"),
                             icon=safe_icon('RENDER_RESULT'))
        op.mode = 'MENU'
        layout.separator()
        op = layout.operator("gtatools.radar_generate",
                             text=T("Полный радар"), icon=safe_icon('IMAGE'))
        op.mode = 'FULL'
        op = layout.operator("gtatools.radar_generate",
                             text=T("Полный меню"), icon=safe_icon('IMAGE'))
        op.mode = 'FULL_MENU'
        layout.separator()
        op = layout.operator("gtatools.radar_generate",
                             text=T("Указанные тайлы"),
                             icon=safe_icon('RENDER_RESULT'))
        op.mode = 'SPECIFIC'


# ── Menu: Path node traffic flags ───────────────────────────────
# 4 traffic-light buttons (None / Normal / Rail / Bus) → one dropdown.
# Roadblock toggle stays as a separate button (different operator
# semantics — it's a toggle, not an enum pick).
class GTATOOLS_MT_path_traffic(bpy.types.Menu):
    bl_label = "INU: Светофор"
    bl_idname = "GTATOOLS_MT_path_traffic"

    def draw(self, context):
        layout = self.layout
        op = layout.operator("gtatools.path_node_flag", text=T("Без светофора"))
        op.action = 'TRAFFIC_NONE'
        op = layout.operator("gtatools.path_node_flag", text=T("Обычный"))
        op.action = 'TRAFFIC_NORMAL'
        op = layout.operator("gtatools.path_node_flag", text=T("Железнодорожный"))
        op.action = 'TRAFFIC_RAIL'
        op = layout.operator("gtatools.path_node_flag", text=T("Автобусный"))
        op.action = 'TRAFFIC_BUS'


@apply_order
class GTATOOLS_PT_export_panel(bpy.types.Panel):
    """Панель экспорта/импорта GTA моделей"""
    bl_label = "Экспорт / Импорт"
    bl_idname = "GTATOOLS_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('EXPORT'))

    def draw(self, context):
        from ..tools.model_utils import (
            find_selected_models, find_all_selected_model_groups,
        )
        from .. import _draw_suffix_prefix
        layout = self.layout

        # ── Selection diagnostic (top of panel, always visible) ──
        models = find_selected_models()
        groups = find_all_selected_model_groups()
        selected_count = len([o for o in context.selected_objects if o.type == 'MESH'])

        # Per-type counts across ALL selected groups — single mesh shows
        # only the first DFF/LOD/COL, but a multi-select like 5 cars
        # should reveal the batch size instead of hiding it behind one
        # name. Format: "name +N" when >1.
        counts = {'DFF': 0, 'LOD': 0, 'COL': 0}
        for g in groups.values():
            for k in counts:
                if g[k] is not None:
                    counts[k] += 1

        def _line(kind):
            obj = models[kind]
            if obj is None:
                return f"{kind}: -"
            n = counts[kind]
            return f"{kind}: {obj.name}" if n <= 1 else f"{kind}: {obj.name} +{n - 1}"

        box = layout.box()
        box.label(text=f"{T('Выделено')}: {selected_count} {T('меш(ей)')}", icon=safe_icon('OBJECT_DATA'))
        col = box.column()
        for kind in ('DFF', 'LOD', 'COL'):
            col.label(text=_line(kind),
                      icon=compat.ICON_CHECK if models[kind] else 'X')

        # ── Quick single-format I/O via menus ──
        row = layout.row(align=True)
        row.menu("GTATOOLS_MT_import_menu", text=T("Импорт"), icon=safe_icon('IMPORT'))
        row.menu("GTATOOLS_MT_export_menu", text=T("Экспорт"), icon=safe_icon('EXPORT'))

        # ── Auto TXD + DXT backend selector ──
        row = layout.row(align=True)
        row.prop(context.scene.inu_settings, "gtatools_txd_auto_import", text=T("Авто TXD"))
        row.prop(context.scene.inu_settings, "gtatools_dxt_backend", text="")

        layout.separator()

        # ── Pipeline (one row, no info-label clutter — tooltip on each btn) ──
        row = layout.row(align=True)
        row.prop_enum(context.scene.inu_settings, "gtatools_export_pipeline", 'NONE')
        row.prop_enum(context.scene.inu_settings, "gtatools_export_pipeline", '0x53F2009A')
        row.prop_enum(context.scene.inu_settings, "gtatools_export_pipeline", '0x53F20098')
        row.prop_enum(context.scene.inu_settings, "gtatools_export_pipeline", '0x53F2009C')
        # Suffix/Prefix (collapsible, hidden by default)
        row = layout.row(align=True)
        row.prop(context.scene.inu_settings, "gtatools_show_suffix_settings",
                 icon=safe_icon('TRIA_DOWN') if context.scene.inu_settings.gtatools_show_suffix_settings else 'TRIA_RIGHT',
                 text=T("Суффиксы / Префиксы"), emboss=False)
        if context.scene.inu_settings.gtatools_show_suffix_settings:
            sbox = layout.box()
            _draw_suffix_prefix(sbox, context.scene)

        obj = context.active_object
        if obj and obj.type == 'MESH' and hasattr(obj, 'inu'):
            inu = obj.inu
            row = layout.row(align=True)
            row.prop(context.scene.inu_settings, "gtatools_show_dff_flags",
                     icon=safe_icon('TRIA_DOWN') if context.scene.inu_settings.gtatools_show_dff_flags else 'TRIA_RIGHT',
                     text="DFF Flags", emboss=False)
            if context.scene.inu_settings.gtatools_show_dff_flags:
                fbox = layout.box()
                fc = fbox.column(align=True)
                fc.prop(inu, "export_normals", text="Normals")
                fc.prop(inu, "light", text="Light")
                fc.prop(inu, "modulate_color", text="Modulate Color")
                fc.prop(inu, "set_material_alpha", text="Set Material Alpha")
                # Pipeline-specific gating: Vehicle (env-map) doesn't
                # use Light Beam — that's an ASI-plugin street-lamp
                # mechanic. DN Building handles day/night via two VC
                # layers, so the mesh-visibility Day/Night flags are
                # redundant there. Vehicle uses damage variants instead
                # of day/night meshes, so flags are noise.
                pipeline = context.scene.inu_settings.gtatools_export_pipeline
                if pipeline != '0x53F2009A':  # not Vehicle
                    fc.prop(inu, "light_beam_asi", text="Light Beam (SA_Light.asi)")
                fc.prop(inu, "export_binsplit", text="Bin Mesh PLG")
                fc.prop(inu, "uv_map1", text="UV1")
                fc.prop(inu, "uv_map2", text="UV2")
                if pipeline not in ('0x53F2009A', '0x53F20098'):  # not Vehicle, not DN Building
                    fc.prop(inu, "day_cols", text="Day")
                    fc.prop(inu, "night_cols", text="Night")




class GTATOOLS_PT_validate_scene(bpy.types.Panel):
    """Pre-export sweep: paintjob slots, quaternion normalisation,
    Modulate Color на прилайтах, парность _ok/_dam.

    Sub-panel живёт внутри Export panel — pre-flight check рядом с
    кнопкой экспорта, без отдельного слота в registry."""
    bl_label = "Проверка перед экспортом"
    bl_idname = "GTATOOLS_PT_validate_scene"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_export_panel"
    bl_options = {'DEFAULT_CLOSED'}

    _SEVERITY_ICON = {
        'ERROR':   'ERROR',
        'WARNING': 'ERROR',  # Blender has no separate WARN icon; ERROR is closest
        'INFO':    'INFO',
    }

    # Human-readable category labels — mirror the (raw) category tag
    # written by core/validate.py. Keep in sync if a new check is added.
    _CATEGORY_LABEL = {
        'Paintjob':       "Paintjob",
        'Quaternions':    "Кватернионы",
        'ModulateColor':  "Modulate Color",
        'DamagePair':     "Пары _ok / _dam",
        'OrphanModel':    "Сирые LOD / COL",
        'Orphan2DFX':     "Непривязанный 2DFX",
        'DuplicateID':    "Дубликаты model_id",
        'EmptyMesh':      "Пустые меши",
        'LargeMesh':      "Большие меши",
        'NoTexture':      "Материал без текстуры",
        'SuffixMismatch': "Суффиксы / префиксы",
        'BadScale':       "Scale объектов",
        'LightBeamASI':   "Light Beam ASI",
    }

    def draw_header(self, context):
        self.layout.label(text="", icon=compat.ICON_CHECK)

    def draw(self, context):
        layout = self.layout
        issues = context.scene.inu_settings.inu_validate_issues

        row = layout.row(align=True)
        row.operator("gtatools.validate_run",
                     text=T("Проверить сцену"), icon=safe_icon('VIEWZOOM'))
        if len(issues):
            row.operator("gtatools.validate_clear",
                         text="", icon='X')

        if not len(issues):
            return

        # Summary banner
        errors = sum(1 for i in issues if i.severity == 'ERROR')
        warns = sum(1 for i in issues if i.severity == 'WARNING')
        infos = sum(1 for i in issues if i.severity == 'INFO')
        box = layout.box()
        srow = box.row(align=True)
        if errors:
            srow.label(text=f"{errors} ✗", icon=safe_icon('CANCEL'))
        if warns:
            srow.label(text=f"{warns} ⚠", icon=safe_icon('ERROR'))
        if infos:
            srow.label(text=f"{infos} i", icon=safe_icon('INFO'))
        if not (errors or warns or infos):
            srow.label(text=T("OK"), icon=compat.ICON_CHECK)

        # ── Group issues by category, preserving first-seen order ──
        # Each category becomes a collapsible-feeling section: a small
        # header with severity colour + count, followed by per-issue
        # rows. A flat list with 6 categories was hard to scan when
        # one category had many entries.
        grouped: "dict[str, list]" = {}
        for issue in issues:
            grouped.setdefault(issue.category, []).append(issue)

        import json as _json
        for cat, group in grouped.items():
            # Worst severity in the group drives the header icon.
            worst = 'INFO'
            for it in group:
                if it.severity == 'ERROR':
                    worst = 'ERROR'
                    break
                if it.severity == 'WARNING' and worst != 'ERROR':
                    worst = 'WARNING'
            cat_box = layout.box()
            header = cat_box.row(align=True)
            # Category label is stored as raw Russian in _CATEGORY_LABEL
            # — wrap with T() so the active locale picks up its
            # eng.py translation at draw time.
            header.label(
                text=f"{T(self._CATEGORY_LABEL.get(cat, cat))}  ({len(group)})",
                icon=self._SEVERITY_ICON.get(worst, 'INFO'))

            for issue in group:
                ibox = cat_box.box()
                if issue.target_name:
                    ibox.label(text=issue.target_name,
                               icon=safe_icon('OBJECT_DATA') if issue.target_kind == 'OBJECT'
                                    else 'MATERIAL' if issue.target_kind == 'MATERIAL'
                                    else 'ACTION' if issue.target_kind == 'ACTION'
                                    else 'BLANK1')
                # Render the message:
                #   • If the check function emitted a translation
                #     template + JSON args, look up the template's
                #     localised form and format the args into it. That
                #     way interpolated messages (e.g. «.DFF vs _DFF»)
                #     follow the active locale.
                #   • Otherwise the message is static — pass it
                #     through T() directly.
                shown = ""
                if issue.message_template:
                    template = T(issue.message_template)
                    args = {}
                    if issue.message_args:
                        try:
                            args = _json.loads(issue.message_args)
                        except Exception:
                            args = {}
                    try:
                        shown = template.format(**args)
                    except (KeyError, IndexError, ValueError):
                        shown = T(issue.message)
                else:
                    shown = T(issue.message)
                ibox.label(text=shown)

                actions = ibox.row(align=True)
                if issue.target_name:
                    op = actions.operator("gtatools.validate_goto",
                                          text=T("Перейти"),
                                          icon=safe_icon('RESTRICT_SELECT_OFF'))
                    op.target_kind = issue.target_kind
                    op.target_name = issue.target_name
                if issue.fix_op_id:
                    # Three fixers; each takes a single StringProperty
                    # arg. Dispatch by idname so we pass the correct
                    # arg name (action_name / object_name).
                    if issue.fix_op_id == 'gtatools.validate_fix_quaternions':
                        fix = actions.operator(issue.fix_op_id,
                                               text=T("Нормализовать"),
                                               icon=safe_icon('FILE_REFRESH'))
                        fix.action_name = issue.fix_arg
                    elif issue.fix_op_id == 'gtatools.validate_fix_modulate_color':
                        fix = actions.operator(issue.fix_op_id,
                                               text=T("Снять"),
                                               icon='X')
                        fix.object_name = issue.fix_arg
                    elif issue.fix_op_id == 'gtatools.validate_fix_suffix':
                        fix = actions.operator(issue.fix_op_id,
                                               text=T("Исправить"),
                                               icon=safe_icon('OUTLINER_DATA_FONT'))
                        fix.object_name = issue.fix_arg




@apply_order
class GTATOOLS_PT_check_panel(bpy.types.Panel):
    """Панель проверки геометрии и материалов"""
    bl_label = "Проверка"
    bl_idname = "GTATOOLS_PT_check_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=compat.ICON_CHECK)

    def draw(self, context):
        from ..ops.object_utils_ops import _hide_dff, _hide_lod, _hide_col, _hide_sha
        from ..ops.map_ops import _links_active
        layout = self.layout

        # Геометрия
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("gtatools.check_geometry", text=T("Проверка вершин"), icon=safe_icon('VIEWZOOM'))
        row.operator("gtatools.check_ngons", text=T("Проверка N-gon"), icon=safe_icon('MESH_DATA'))
        col.operator("gtatools.reset_transform", text=T("Сброс трансформ"), icon=safe_icon('EMPTY_AXIS'))
        col.operator("gtatools.snap_to_dff", text=T("LOD/COL → DFF"), icon=safe_icon('SNAP_ON'))

        # «Материалы» (Проверка/Очистка/Сортировка) переехали в
        # «Менеджер текстур» — там же где Find/Remove Unused и Find
        # Duplicates, чтобы все операции по чистке ассетов жили в
        # одном месте.

        # Видимость
        row = layout.row(align=True)
        op = row.operator("gtatools.toggle_visibility", text="DFF",
                          icon=safe_icon('HIDE_ON') if _hide_dff else 'HIDE_OFF', depress=_hide_dff)
        op.model_type = 'DFF'
        op = row.operator("gtatools.toggle_visibility", text="LOD",
                          icon=safe_icon('HIDE_ON') if _hide_lod else 'HIDE_OFF', depress=_hide_lod)
        op.model_type = 'LOD'
        op = row.operator("gtatools.toggle_visibility", text="COL",
                          icon=safe_icon('HIDE_ON') if _hide_col else 'HIDE_OFF', depress=_hide_col)
        op.model_type = 'COL'
        op = row.operator("gtatools.toggle_visibility", text="SHA",
                          icon=safe_icon('HIDE_ON') if _hide_sha else 'HIDE_OFF', depress=_hide_sha)
        op.model_type = 'SHA'

        # Visual links between matching DFF/LOD/COL groups — colored
        # dashed lines drawn in the viewport so the user can spot
        # orphaned LODs / unpaired COLs without opening the outliner.
        # Lives here (not in Map/IMG) because it's a check-style
        # overlay, not part of map import workflow.
        layout.operator("gtatools.toggle_links",
                        text=T("Связи: ON") if _links_active
                             else T("Связи: OFF"),
                        icon=safe_icon('LINKED'),
                        depress=_links_active)

        # Batch set type
        row = layout.row(align=True)
        row.label(text=T("Тип:"))
        for _t in ('OBJ', 'COL', 'SHA', 'NON'):
            op = row.operator("gtatools.batch_set_type", text=_t)
            op.obj_type = _t



class GTATOOLS_UL_lint_issues(bpy.types.UIList):
    """Scrollable list of binary file lint issues. Filters by severity
    («Только ERROR» toggle) and free-text search via the standard
    UIList search field."""
    bl_idname = "GTATOOLS_UL_lint_issues"

    _SEV_ICON = {'ERROR': 'ERROR', 'WARN': 'ERROR', 'INFO': 'INFO'}

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        ic = self._SEV_ICON.get(item.severity, 'BLANK1')
        row = layout.row(align=True)
        row.label(text="", icon=safe_icon(ic))
        # Show filename (basename) + the message — full path is in the
        # tooltip via the UIList's automatic property reflection.
        import os as _os
        fn = _os.path.basename(item.file) if item.file else "?"
        row.label(text=f"{fn}: {item.message}")

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        n = len(items)
        flt_flags = [self.bitflag_filter_item] * n
        flt_neworder = []

        s = context.scene.inu_settings
        only_err = s.gtatools_scan_only_errors
        search = (self.filter_name or "").lower()

        for i, it in enumerate(items):
            if only_err and it.severity != 'ERROR':
                flt_flags[i] = 0
                continue
            if search:
                hay = f"{it.code} {it.file} {it.where} {it.message}".lower()
                if search not in hay:
                    flt_flags[i] = 0

        return flt_flags, flt_neworder


class GTATOOLS_PT_file_scanner(bpy.types.Panel):
    """Sub-panel внутри «Проверка»: сканер DFF/COL/TXD на диске.

    Отдельно от GTATOOLS_PT_validate_scene (pre-export sweep, который
    работает со сценой) — здесь линтер уже-готовых файлов на диске.
    """
    bl_label = "Скан файлов"
    bl_idname = "GTATOOLS_PT_file_scanner"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_check_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('VIEWZOOM'))

    def draw(self, context):
        layout = self.layout
        s = context.scene.inu_settings
        wm = context.window_manager

        # Папка
        row = layout.row(align=True)
        row.prop(s, "gtatools_scan_dir", text="")
        layout.prop(s, "gtatools_scan_recursive")

        # Type checkboxes
        row = layout.row(align=True)
        row.prop(s, "gtatools_scan_dff", toggle=True)
        row.prop(s, "gtatools_scan_col", toggle=True)
        row.prop(s, "gtatools_scan_txd", toggle=True)

        layout.prop(s, "gtatools_scan_only_errors")

        # Action row
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator("gtatools.scan_files", text=T("Сканировать"), icon=safe_icon('VIEWZOOM'))

        # Results
        n_total = len(wm.gtatools_scan_results)
        if n_total:
            n_err = sum(1 for x in wm.gtatools_scan_results if x.severity == 'ERROR')
            n_warn = sum(1 for x in wm.gtatools_scan_results if x.severity == 'WARN')
            box = layout.box()
            head = box.row(align=True)
            head.label(text=f"ERROR: {n_err}", icon=safe_icon('ERROR'))
            head.label(text=f"WARN: {n_warn}")
            head.label(text=f"всего: {n_total}")
            head.operator("gtatools.scan_clear", text="", icon=safe_icon('X'))

            box.template_list("GTATOOLS_UL_lint_issues", "",
                              wm, "gtatools_scan_results",
                              wm, "gtatools_scan_results_index",
                              rows=8)

            # Selected row details + long-form explanation
            idx = wm.gtatools_scan_results_index
            if 0 <= idx < n_total:
                cur = wm.gtatools_scan_results[idx]
                detail = box.box()
                head = detail.row(align=True)
                head.label(text=f"[{cur.severity}] {cur.code}",
                           icon=safe_icon('INFO'))
                head.operator("gtatools.scan_reveal_file",
                              text="", icon=safe_icon('FILE_FOLDER'))

                # File path + where
                import os as _os
                detail.label(text=_os.path.basename(cur.file) if cur.file else "?",
                             icon=safe_icon('FILE'))
                if cur.where:
                    detail.label(text=cur.where, icon=safe_icon('VIEWZOOM'))
                detail.label(text=cur.message)

                # Long-form explanation: pulled from EXPLANATIONS
                # registry. Auto-wraps via splitting on whitespace —
                # Blender's label() doesn't wrap text by itself.
                from ..core.file_lint import explain
                explanation = explain(cur.code)
                detail.separator()
                detail.label(text=T("Что это значит:"), icon=safe_icon('QUESTION'))
                # Naive word-wrap at ~50 chars (panel width-dependent —
                # this is a rough fit for default 250px N-panel width).
                words = explanation.split()
                line, lines = [], []
                for w in words:
                    if sum(len(x) for x in line) + len(line) + len(w) > 50:
                        lines.append(' '.join(line))
                        line = [w]
                    else:
                        line.append(w)
                if line:
                    lines.append(' '.join(line))
                for ln in lines:
                    detail.label(text=ln)

            # Save report block
            box2 = layout.box()
            box2.label(text=T("Сохранить отчёт:"))
            box2.prop(s, "gtatools_scan_report_target", text="")
            if s.gtatools_scan_report_target == 'CUSTOM':
                box2.prop(s, "gtatools_scan_report_custom_path", text="")
            elif s.gtatools_scan_report_target == 'BLEND' and not bpy.data.filepath:
                box2.label(text=T("Сцена не сохранена!"), icon=safe_icon('ERROR'))
            box2.operator("gtatools.scan_save_report",
                          text=T("Сохранить .txt"), icon=safe_icon('FILE_TEXT'))
        else:
            layout.label(text=T("Список пуст — запустите скан"), icon=safe_icon('INFO'))


@apply_order
class GTATOOLS_PT_vehicle_panel(bpy.types.Panel):
    """Dedicated panel for vehicle-specific operators — body scale,
    damage variants (_ok / _dam pairs). Moved out of Check so the
    vehicle workflow has a stable home, and so non-vehicle modders
    don't see it during regular map work."""
    bl_label = "Машины"
    bl_idname = "GTATOOLS_PT_vehicle_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    # poll() removed — panel is always visible. Visibility filtering
    # is now handled by the profile system; users who don't want
    # vehicle tools can hide this panel via their profile.

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('AUTO'))
    def draw(self, context):
        layout = self.layout

        # Hierarchy scale
        layout.operator("gtatools.vehicle_scale",
                        text=T("Масштаб машины…"),
                        icon=safe_icon('FULLSCREEN_ENTER'))

        # Damage variants — _ok / _dam pair management
        layout.separator()
        box = layout.box()
        box.label(text=T("Damage variants"), icon=safe_icon('AUTO'))
        box.operator("gtatools.vehicle_add_damage_variant",
                     text=T("Создать _dam"), icon=safe_icon('DUPLICATE'))
        row = box.row(align=True)
        row.label(text=T("Показать:"))
        op = row.operator("gtatools.vehicle_show_damage", text=T("OK"))
        op.state = 'OK'
        op = row.operator("gtatools.vehicle_show_damage", text=T("Dam"))
        op.state = 'DAM'
        op = row.operator("gtatools.vehicle_show_damage", text=T("Оба"))
        op.state = 'BOTH'
        box.operator("gtatools.vehicle_pair_report",
                     text=T("Проверить пары"), icon=compat.ICON_CHECK)


@apply_order
class GTATOOLS_PT_frame_hierarchy(bpy.types.Panel):
    """Frame Hierarchy Editor — компактное дерево фреймов активного
    объекта + операторы для безопасного rename / set-parent / validate
    против vanilla SA шаблонов (vehicle, ped). DFF-frame-list пишется
    точно по этим именам, так что любая опечатка ломает поведение в
    игре — лучше отловить здесь, чем после копирования в IMG."""
    bl_label = "Иерархия фреймов"
    bl_idname = "GTATOOLS_PT_frame_hierarchy"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('OUTLINER'))

    def draw(self, context):
        layout = self.layout
        active = context.active_object

        # Operator row — visible regardless of tree size
        row = layout.row(align=True)
        row.operator("gtatools.frame_rename",
                     text=T("Rename"), icon=safe_icon('GREASEPENCIL'))
        row.operator("gtatools.frame_set_parent",
                     text=T("Set Parent"), icon=safe_icon('LINKED'))
        row.operator("gtatools.frame_unparent",
                     text=T("Unparent"), icon=safe_icon('UNLINKED'))

        row = layout.row(align=True)
        op = row.operator("gtatools.frame_validate",
                          text=T("Validate Vehicle"), icon=safe_icon('AUTO'))
        op.template = 'VEHICLE'
        op = row.operator("gtatools.frame_validate",
                          text=T("Validate Ped"), icon=safe_icon('ARMATURE_DATA'))
        op.template = 'PED'

        layout.operator("gtatools.frame_mirror_lr",
                        text=T("Зеркало L↔R"), icon=safe_icon('MOD_MIRROR'))

        layout.separator()

        # Tree section needs a selected root. Show a hint when there's
        # no active object instead of hiding the whole panel — the
        # operator buttons above stay accessible (e.g. you can pick a
        # template in the Validate dialog without selecting first).
        if active is None:
            layout.label(text=T("Выдели объект чтобы увидеть иерархию"),
                         icon=safe_icon('INFO'))
            return

        # Tree view of active object's hierarchy
        layout.label(text=f"{T('Корень')}: {active.name}", icon=safe_icon('OBJECT_DATA'))

        from ..ops.frame_hierarchy import _all_descendants
        items = _all_descendants(active)

        # Compute depth per object for indentation
        depth_of = {active: 0}
        for it in items[1:]:  # skip root
            d = depth_of.get(it.parent, 0) + 1
            depth_of[it] = d

        box = layout.box()
        col = box.column(align=True)
        max_visible = 60
        shown = 0
        for it in items:
            if shown >= max_visible:
                col.label(text=f"… +{len(items) - max_visible} more")
                break
            row = col.row(align=True)
            depth = depth_of.get(it, 0)
            # Indent via spacer columns — each level = ~10px
            for _ in range(depth):
                spc = row.column()
                spc.scale_x = 0.5
                spc.label(text="")
            # Icon by type
            icon = ('MESH_DATA' if it.type == 'MESH'
                    else 'ARMATURE_DATA' if it.type == 'ARMATURE'
                    else 'EMPTY_AXIS')
            is_active = (it == active)
            sel_op = row.operator("gtatools.frame_select",
                                  text=it.name, icon=icon,
                                  emboss=is_active,
                                  depress=is_active)
            sel_op.target_name = it.name
            sel_op.extend = False
            shown += 1


@apply_order
class GTATOOLS_PT_2dfx_panel(bpy.types.Panel):
    """2DFX Effects Properties"""
    bl_label = "2DFX Effects"
    bl_idname = "GTATOOLS_PT_2dfx_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def _is_2dfx(self, context):
        obj = context.active_object
        return (obj and obj.type == 'EMPTY'
                and getattr(obj, 'inu', None)
                and obj.inu.type == '2DFX')

    def draw_header(self, context):
        # Always show the panel icon; append a checkmark when the
        # active object is actually a 2DFX empty, so the header hints
        # whether the panel's content applies to the current selection.
        self.layout.label(text="", icon=safe_icon('LIGHT'))
        if self._is_2dfx(context):
            self.layout.label(text="", icon=compat.ICON_CHECK)

    def draw(self, context):
        from .. import _get_effect_emitter_count
        from .. import _draw_label_with_info
        layout = self.layout
        obj = context.active_object
        is_active = self._is_2dfx(context)

        # ── Кнопки создания (видны всегда) ──
        box = layout.box()
        _draw_label_with_info(box, "Create Effect:",
            T("Light — уличные фонари, неон, corona\nParticle — дым, огонь, частицы\nPed Attractor — точки притяжения NPC (банкомат, скамейка)\nSun Glare — блик солнца на поверхности"),
            icon=safe_icon('ADD'))
        box.menu("GTATOOLS_MT_create_2dfx",
                 text=T("Создать эффект"), icon=safe_icon('ADD'))

        # ── Если выделен меш — показываем привязанные 2DFX ──
        if not is_active and obj and obj.type == 'MESH':
            attached = [c for c in bpy.data.objects
                        if c.parent == obj and c.type == 'EMPTY'
                        and getattr(c, 'inu', None) and c.inu.type == '2DFX']
            if attached:
                box = layout.box()
                box.label(text=f"{T('Привязанные 2DFX:')} {len(attached)}", icon=safe_icon('LINKED'))
                for fx in attached:
                    row = box.row(align=True)
                    row.label(text=fx.name, icon=safe_icon('LIGHT') if fx.inu.effect_2dfx == 'LIGHT' else 'PARTICLES')
                    op = row.operator("gtatools.detach_2dfx", text="", icon='X')
                    op.fx_name = fx.name
                layout.operator("gtatools.detach_all_2dfx", text=T("Отвязать все"), icon=safe_icon('UNLINKED'))
                layout.separator()
            layout.label(text=T("Выберите 2DFX Empty для редактирования"), icon=safe_icon('RESTRICT_SELECT_ON'))
            return

        # ── Если не выбран 2DFX — показываем подсказку ──
        if not is_active:
            layout.label(text=T("Выберите 2DFX Empty для редактирования"), icon=safe_icon('RESTRICT_SELECT_ON'))
            return

        # ── Активный 2DFX — зелёная галка в заголовке, свойства ниже ──
        layout.separator()

        # Обводка-box для активного эффекта
        main_box = layout.box()
        settings = obj.inu
        # Header icon reflects effect type — type is fixed at creation
        # (Light vs Particle initialise different custom props), so we
        # show it instead of an editable selector.
        _type_icon = {
            'LIGHT': 'LIGHT_POINT',
            'PARTICLE': 'PARTICLES',
            'PED_ATTRACTOR': 'COMMUNITY',
            'SUN_GLARE': 'LIGHT_SUN',
        }.get(settings.effect_2dfx, compat.ICON_CHECK)
        header_row = main_box.row()
        header_row.label(text=f"Active: {obj.name}", icon=_type_icon)

        # Attach/Detach buttons
        attach_box = main_box.box()
        if obj.parent and obj.parent.type == 'MESH':
            row_a = attach_box.row(align=True)
            row_a.label(text=f"Model: {obj.parent.name}", icon=safe_icon('LINKED'))
            row_a.operator("gtatools.detach_2dfx", text="", icon='X')
        else:
            attach_box.operator("gtatools.attach_2dfx", text=T("Привязать к модели"), icon=safe_icon('LINK_BLEND'))
            attach_box.label(text=T("Выделите меш + 2DFX, затем нажмите"), icon=safe_icon('INFO'))

        effect = settings.effect_2dfx

        # Preview buttons
        if effect in ('LIGHT', 'PARTICLE'):
            row = main_box.row(align=True)
            row.operator("gtatools.refresh_2dfx_preview", text=T("Обновить превью"), icon=safe_icon('FILE_REFRESH'))
            row.operator("gtatools.remove_2dfx_preview", text=T("Удалить превью"), icon='X')

        if effect == 'LIGHT':
            # Presets
            box_p = main_box.box()
            box_p.label(text=T("Пресеты:"), icon=safe_icon('PRESET'))
            row_p = box_p.row(align=True)
            row_p.prop(settings, "preset_2dfx", text="")
            row_p.operator("gtatools.apply_2dfx_preset", text=T("Применить"), icon=compat.ICON_CHECK)

            # Each Light section is a collapsible box. Default-open
            # state lives on the scene so it persists across selection
            # changes and undo. «Свойства» starts open (most-used
            # fields), the rest start closed to keep the panel compact.
            scn = context.scene

            def _section(parent, prop, label, icon='NONE'):
                """Header row + content box. Returns the content box if
                expanded, else None so caller can skip drawing fields."""
                row = parent.row(align=True)
                row.prop(scn.inu_settings, prop,
                         icon=safe_icon('TRIA_DOWN') if getattr(scn.inu_settings, prop) else 'TRIA_RIGHT',
                         text=label, emboss=False, toggle=True)
                if getattr(scn.inu_settings, prop):
                    return parent.box()
                return None

            # ── Свойства света (color, corona, range, texture) ──
            sec = _section(main_box, "gtatools_2dfx_show_props",
                           T("Свойства света"), icon=safe_icon('LIGHT_POINT'))
            if sec is not None:
                sec.prop(settings, "color_2dfx", text=T("Цвет"))
                col = sec.column(align=True)
                col.prop(settings, "corona_size_2dfx", text=T("Размер короны"))
                col.prop(obj, '["2dfx_corona_far_clip"]', text=T("Дальность отрисовки"))
                col.prop(obj, '["2dfx_pointlight_range"]', text=T("Радиус света"))
                sec.label(text=T("Имя короны:"))
                sec.prop(settings, "corona_tex_2dfx", text="")

            # ── Поведение (показ + блики + отражение) ──
            sec = _section(main_box, "gtatools_2dfx_show_behavior",
                           T("Поведение"))
            if sec is not None:
                col = sec.column(align=True)
                col.label(text=T("Режим показа:"))
                col.prop(settings, "show_mode_2dfx", text="")
                col.label(text=T("Тип бликов:"))
                col.prop(settings, "flare_type_2dfx", text="")
                sec.prop(obj, '["2dfx_corona_enable_reflection"]',
                         text=T("Отражение короны"))

            # ── Тень ──
            sec = _section(main_box, "gtatools_2dfx_show_shadow",
                           T("Тень"))
            if sec is not None:
                col = sec.column(align=True)
                col.prop(settings, "shadow_size_2dfx", text=T("Размер"))
                col.prop(obj, '["2dfx_shadow_z_distance"]', text=T("Дистанция"))
                col.prop(obj, '["2dfx_shadow_color_multiplier"]', text=T("Множитель"))
                sec.label(text=T("Имя тени:"))
                sec.prop(settings, "shadow_tex_2dfx", text="")

            # ── Флаги (semantic groups, per-bit tooltip on hover) ──
            sec = _section(main_box, "gtatools_2dfx_show_flags",
                           T("Флаги"))
            if sec is not None:
                _draw_2dfx_flag_box(sec, obj)

            # View Vector — always-visible, only present on imported
            # lights with explicit direction (rare, so OK as plain box).
            if '2dfx_look_direction' in obj:
                box5 = main_box.box()
                box5.label(text=T("Вектор направления:"), icon=safe_icon('EMPTY_ARROWS'))
                box5.prop(obj, '["2dfx_look_direction"]', text="")


        elif effect == 'PARTICLE':
            box = main_box.box()
            box.label(text=T("Свойства частицы:"), icon=safe_icon('PARTICLES'))
            row = box.row(align=True)
            row.prop(obj.inu, 'particle_effect_2dfx', text=T("Эффект"))
            row.operator("gtatools.particle_effect_new", text="", icon=safe_icon('ADD'))
            row.operator("gtatools.particle_effect_delete", text="", icon=safe_icon('REMOVE'))
            row.operator("gtatools.reload_effects_fxp", text="", icon=safe_icon('FILE_REFRESH'))

            # Emitter switcher (only if system has > 1 emitter)
            eff_name = obj.get('2dfx_effect_name', '') or ''
            if eff_name:
                em_total = _get_effect_emitter_count(eff_name)
                if em_total > 1:
                    em_row = box.row(align=True)
                    op = em_row.operator("gtatools.particle_emitter_switch", text="", icon=safe_icon('TRIA_LEFT'))
                    op.direction = -1
                    em_row.label(text=f"Emitter {obj.inu.particle_emitter_index + 1} / {em_total}")
                    op = em_row.operator("gtatools.particle_emitter_switch", text="", icon=safe_icon('TRIA_RIGHT'))
                    op.direction = 1
                    box.label(text=T("Переключение сбросит правки — сохраняйте первыми"), icon=safe_icon('INFO'))

            # Live simulation toggle (scene-global)
            sim_row = box.row(align=True)
            sim_row.prop(
                context.scene.inu_settings, 'gtatools_particle_sim',
                text=T("Симуляция"),
                icon=safe_icon('PLAY') if context.scene.inu_settings.gtatools_particle_sim else 'PAUSE',
                toggle=True,
            )

            inu = obj.inu
            scene = context.scene

            def _section(parent, prop_name: str, label: str, icon: str):
                """Collapsible section helper. Returns the content box or None."""
                expanded = getattr(scene.inu_settings, prop_name)
                header = parent.row(align=True)
                header.prop(
                    scene.inu_settings, prop_name,
                    icon=safe_icon('TRIA_DOWN') if expanded else 'TRIA_RIGHT',
                    text="", emboss=False,
                )
                header.label(text=label, icon=icon)
                if expanded:
                    return parent.box()
                return None

            # ── Texture / blend ── #
            tex_box = _section(box, 'gtatools_pfx_exp_texture', T("Спрайт и смешивание"), 'TEXTURE')
            if tex_box:
                tex_box.prop(inu, 'particle_texture', text=T("Текстура"))
                row = tex_box.row(align=True)
                row.prop(inu, 'particle_src_blend', text="SRC")
                row.prop(inu, 'particle_dst_blend', text="DST")

            # ── Colour ── #
            col_box = _section(box, 'gtatools_pfx_exp_color', T("Цвет (start → end)"), 'COLOR')
            if col_box:
                col_box.prop(inu, 'particle_color_start', text=T("Начало"))
                col_box.prop(inu, 'particle_color_mid_enabled', text=T("Средний"), toggle=True)
                if inu.particle_color_mid_enabled:
                    col_box.prop(inu, 'particle_color_mid', text=T("Middle"))
                    col_box.prop(inu, 'particle_color_mid_time', text=T("Mid time"), slider=True)
                col_box.prop(inu, 'particle_color_end', text=T("Конец"))

            # ── Size ── #
            size_box = _section(box, 'gtatools_pfx_exp_size', T("Размер"), 'FULLSCREEN_ENTER')
            if size_box:
                row = size_box.row(align=True)
                row.prop(inu, 'particle_size_start', text=T("Начало"))
                row.prop(inu, 'particle_size_end', text=T("Конец"))

            # ── Emission ── #
            em_box = _section(box, 'gtatools_pfx_exp_emission', T("Эмиссия"), 'OUTLINER_OB_FORCE_FIELD')
            if em_box:
                em_box.prop(inu, 'particle_life', text=T("Жизнь"))
                em_box.prop(inu, 'particle_life_bias', text=T("Life bias"))
                em_box.prop(inu, 'particle_rate', text=T("Rate"))
                em_box.prop(inu, 'particle_speed', text=T("Скорость"))
                em_box.prop(inu, 'particle_speed_bias', text=T("Speed bias"))
                em_box.prop(inu, 'particle_direction', text=T("Направление"))
                row = em_box.row(align=True)
                row.prop(inu, 'particle_angle_min', text=T("Angle min"))
                row.prop(inu, 'particle_angle_max', text=T("Angle max"))
                em_box.prop(inu, 'particle_volume', text=T("Box"))
                em_box.prop(inu, 'particle_offset', text=T("Offset"))
                row = em_box.row(align=True)
                row.prop(inu, 'particle_rotation_min', text=T("Rot min"))
                row.prop(inu, 'particle_rotation_max', text=T("Rot max"))

            # ── Physics ── #
            ph_box = _section(box, 'gtatools_pfx_exp_physics', T("Физика"), 'PHYSICS')
            if ph_box:
                ph_box.prop(inu, 'particle_force', text=T("Force"))
                row = ph_box.row(align=True)
                row.prop(inu, 'particle_friction', text=T("Friction"))
                row.prop(inu, 'particle_wind', text=T("Wind"))
                row = ph_box.row(align=True)
                row.prop(inu, 'particle_noise', text=T("Noise"))
                row.prop(inu, 'particle_jitter', text=T("Jitter"))
                row = ph_box.row(align=True)
                row.prop(inu, 'particle_rotspeed_min', text=T("RotSpd min"))
                row.prop(inu, 'particle_rotspeed_max', text=T("RotSpd max"))
                row = ph_box.row(align=True)
                row.prop(inu, 'particle_ground_bounce', text=T("Bounce"))
                row.prop(inu, 'particle_ground_speedmult', text=T("SpeedMult"))

            # ── System-level (FX_SYSTEM_DATA header) ── #
            sys_box = _section(box, 'gtatools_pfx_exp_system', T("Система"), 'WORLD')
            if sys_box:
                sys_box.prop(inu, 'particle_sys_length', text=T("Length"))
                sys_box.prop(inu, 'particle_sys_playmode', text=T("Play mode"))
                sys_box.prop(inu, 'particle_sys_culldist', text=T("Cull dist"))

            # ── Curve editor (B1) ── #
            cv_box = _section(box, 'gtatools_pfx_exp_curves', T("Кривые (keyframes)"), 'FCURVE')
            if cv_box:
                # Curve picker row
                pick_row = cv_box.row(align=True)
                pick_row.operator(
                    "gtatools.particle_curve_select",
                    text=inu.particle_curve_name or T("Выбрать кривую..."),
                    icon=safe_icon('VIEWZOOM'),
                )

                if inu.particle_curve_name:
                    keys = inu.particle_curve_keys
                    # Header
                    hdr = cv_box.row(align=True)
                    hdr.label(text=T(f"Ключи ({len(keys)}):"))
                    hdr.operator("gtatools.particle_curve_key_add", text="", icon=safe_icon('ADD'))
                    hdr.operator("gtatools.particle_curve_key_remove", text="", icon=safe_icon('REMOVE'))

                    # Keyframe rows (time, val)
                    if len(keys) == 0:
                        cv_box.label(text=T("Нет ключей"), icon=safe_icon('INFO'))
                    else:
                        for i, kf in enumerate(keys):
                            r = cv_box.row(align=True)
                            # Active-row indicator (click selects for deletion)
                            is_active = (i == inu.particle_curve_key_index)
                            op = r.operator(
                                "gtatools.particle_curve_key_select_row",
                                text="", depress=is_active,
                                icon=safe_icon('RADIOBUT_ON') if is_active else 'RADIOBUT_OFF',
                            )
                            op.index = i
                            r.prop(kf, 'time', text="t")
                            r.prop(kf, 'val', text="v")

                    # Write to FXP button
                    write_row = cv_box.row(align=True)
                    write_row.scale_y = 1.2
                    write_row.operator(
                        "gtatools.particle_curve_write",
                        text=T("Записать кривую в effects.fxp"),
                        icon=safe_icon('FILE_TICK'),
                    )

            # Save to effects.fxp
            save_row = box.row(align=True)
            save_row.scale_y = 1.3
            save_row.operator(
                "gtatools.save_particle_effect",
                text=T("Сохранить в effects.fxp"),
                icon=safe_icon('FILE_TICK'),
            )

        elif effect == 'PED_ATTRACTOR':
            box = main_box.box()
            box.label(text=T("Точка притяжения:"), icon=safe_icon('COMMUNITY'))
            if '2dfx_attractor_type' in obj:
                box.prop(obj, '["2dfx_attractor_type"]', text=T("Тип аттрактора"))
            if '2dfx_rotation_matrix' in obj:
                box.prop(obj, '["2dfx_rotation_matrix"]', text=T("Матрица поворота"))
            if '2dfx_external_script' in obj:
                box.prop(obj, '["2dfx_external_script"]', text=T("Внешний скрипт"))
            if '2dfx_ped_probability' in obj:
                box.prop(obj, '["2dfx_ped_probability"]', text=T("Вероятность NPC"))

        elif effect == 'SUN_GLARE':
            box = main_box.box()
            box.label(text=T("Солнечный блик"), icon=safe_icon('LIGHT_SUN'))
            box.label(text=T("Только позиция (без доп. данных)"))



@apply_order
class GTATOOLS_PT_object_ide_ipl_panel(bpy.types.Panel):
    """Per-object IDE/IPL properties (N-sidebar, DATA zone)"""
    bl_label = "Object IDE / IPL"
    bl_idname = "GTATOOLS_PT_object_ide_ipl_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('COPY_ID'))

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        obj = context.active_object
        inu = obj.inu

        col = layout.column(align=True)
        col.prop(inu, "model_id", text="Model ID")
        col.prop(inu, "draw_distance", text="Draw Dist")
        col.prop(inu, "lod_draw_distance", text="LOD Dist")

        # Batch: apply distances to all selected MESH objects
        n_sel = sum(1 for o in context.selected_objects if o.type == 'MESH')
        if n_sel > 1:
            layout.operator(
                "gtatools.batch_set_distance",
                text=f"{T('Применить к выделенным')} ({n_sel})",
                icon=safe_icon('STICKY_UVS_LOC'),
            )

        # Flags with expandable checkboxes
        row = layout.row(align=True)
        row.prop(inu, "ide_flags", text="Flags")
        row.prop(scn.inu_settings, "gtatools_show_ide_flags",
                 icon=safe_icon('TRIA_DOWN') if scn.inu_settings.gtatools_show_ide_flags else 'TRIA_RIGHT',
                 text="", emboss=False)
        if scn.inu_settings.gtatools_show_ide_flags:
            fbox = layout.box()
            fc = fbox.column(align=True)
            fc.prop(inu, "flag_is_road")
            fc.prop(inu, "flag_draw_last")
            fc.prop(inu, "flag_additive")
            fc.prop(inu, "flag_no_zbuffer")
            fc.prop(inu, "flag_no_shadows")
            fc.prop(inu, "flag_glass_1")
            fc.prop(inu, "flag_glass_2")
            fc.prop(inu, "flag_garage_door")
            fc.prop(inu, "flag_damagable")
            fc.prop(inu, "flag_is_tree")
            fc.prop(inu, "flag_is_palm")
            fc.prop(inu, "flag_no_flyer_col")
            fc.prop(inu, "flag_is_tag")
            fc.prop(inu, "flag_no_backface")
            fc.prop(inu, "flag_breakable")

        row = layout.row(align=True)
        row.prop(inu, "interior_id", text="Interior")
        row.prop(inu, "lod_index", text="LOD")

        # Breakable object (DFF chunk 0x253F2FD)
        box = layout.box()
        row = box.row(align=True)
        row.prop(inu, "breakable", text=T("Разрушаемый (Breakable)"))
        if inu.breakable:
            box.prop(inu, "breakable_force", text=T("Break Force"))

        # Check for ID conflicts — ignore Blender duplicate suffixes (.001,
        # .002, ...). Multiple placements of the same model legitimately
        # share a model_id; only a different base name counts as a real
        # conflict (two distinct meshes claiming the same IDE entry).
        if inu.model_id > 0:
            def _dup_base(n: str) -> str:
                if '.' in n:
                    head, tail = n.rsplit('.', 1)
                    if tail.isdigit():
                        return head
                return n

            self_base = _dup_base(obj.name)
            conflicts = [o.name for o in bpy.data.objects
                         if o.type == 'MESH' and o != obj
                         and hasattr(o, 'inu') and o.inu.model_id == inu.model_id
                         and _dup_base(o.name) != self_base]
            if conflicts:
                layout.label(text=f"ID {inu.model_id}: {T('конфликт с')} {', '.join(conflicts[:3])}", icon=safe_icon('ERROR'))



class GTATOOLS_PT_object_inu_tools(bpy.types.Panel):
    """INU Tools — full per-object model settings in Object Properties"""
    bl_label = "INU Tools: Model"
    bl_idname = "GTATOOLS_PT_object_inu_tools"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('COPY_ID'))

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type in ('MESH', 'EMPTY')

    def draw(self, context):
        from ..tools.model_utils import get_model_type
        layout = self.layout
        scn = context.scene
        obj = context.active_object
        inu = obj.inu

        # ── Тип (по имени + manual) ──
        box = layout.box()
        box.label(text=T("Тип:"), icon=safe_icon('OBJECT_DATA'))
        detected, _ = get_model_type(obj)
        name_row = box.row(align=True)
        name_row.enabled = False
        name_row.label(text=f"{T('По имени:')} {detected or '—'}")
        box.prop(inu, "type", text=T("Экспортировать как"))

        # ── IDE / Placement ──
        box = layout.box()
        box.label(text="IDE / Placement", icon=safe_icon('COPY_ID'))
        col = box.column(align=True)
        col.prop(inu, "model_id", text="Model ID")
        col.prop(inu, "txd_name", text="TXD")
        col.prop(inu, "draw_distance", text="Draw Dist")
        col.prop(inu, "lod_draw_distance", text="LOD Dist")
        col.prop(inu, "interior_id", text="Interior")
        # LOD partner — clickable object picker. Auto-filled on Map
        # Import (preserves the IPL lod_index relationship even when
        # vanilla LOD names don't follow the lod* convention), but
        # the user can re-target it if naming heuristics get it wrong.
        # Map Export converts the pointer back into IPL lod_index.
        col.prop(inu, "lod_object", text="LOD partner")

        # Batch distance button
        n_sel = sum(1 for o in context.selected_objects if o.type == 'MESH')
        if n_sel > 1:
            box.operator(
                "gtatools.batch_set_distance",
                text=f"{T('Применить к выделенным')} ({n_sel})",
                icon=safe_icon('STICKY_UVS_LOC'),
            )

        # Clear Model ID on selection — quick path to re-run Auto Assign
        # on objects that already have IDs (duplicated with Shift+D,
        # imported from map, etc. — their inu.model_id carries over).
        clear_row = box.row(align=True)
        clear_row.operator(
            "gtatools.id_manager_clear_selected",
            text=f"{T('Очистить ID выделенных')} ({n_sel})" if n_sel > 1
                 else T("Очистить ID"),
            icon='X',
        )

        # IDE Flags (collapsible)
        row = box.row(align=True)
        row.prop(inu, "ide_flags", text="IDE Flags")
        row.prop(scn.inu_settings, "gtatools_show_ide_flags",
                 icon=safe_icon('TRIA_DOWN') if scn.inu_settings.gtatools_show_ide_flags else 'TRIA_RIGHT',
                 text="", emboss=False)
        if scn.inu_settings.gtatools_show_ide_flags:
            fbox = box.box()
            fc = fbox.column(align=True)
            fc.prop(inu, "flag_is_road")
            fc.prop(inu, "flag_draw_last")
            fc.prop(inu, "flag_additive")
            fc.prop(inu, "flag_no_zbuffer")
            fc.prop(inu, "flag_no_shadows")
            fc.prop(inu, "flag_glass_1")
            fc.prop(inu, "flag_glass_2")
            fc.prop(inu, "flag_garage_door")
            fc.prop(inu, "flag_damagable")
            fc.prop(inu, "flag_is_tree")
            fc.prop(inu, "flag_is_palm")
            fc.prop(inu, "flag_no_flyer_col")
            fc.prop(inu, "flag_is_tag")
            fc.prop(inu, "flag_no_backface")
            fc.prop(inu, "flag_breakable")

        # ── DFF Flags (collapsible, only for mesh) ──
        if obj.type == 'MESH':
            box = layout.box()
            row = box.row(align=True)
            row.prop(scn.inu_settings, "gtatools_show_dff_flags",
                     icon=safe_icon('TRIA_DOWN') if scn.inu_settings.gtatools_show_dff_flags else 'TRIA_RIGHT',
                     text="DFF Flags", emboss=False)
            if scn.inu_settings.gtatools_show_dff_flags:
                fc = box.column(align=True)
                fc.prop(inu, "export_normals", text="Normals")
                fc.prop(inu, "light", text="Light")
                fc.prop(inu, "modulate_color", text="Modulate Color")
                fc.prop(inu, "set_material_alpha", text="Set Material Alpha")
                fc.prop(inu, "light_beam_asi", text="Light Beam (SA_Light.asi)")
                fc.prop(inu, "export_binsplit", text="Bin Mesh PLG")
                fc.prop(inu, "uv_map1", text="UV1")
                fc.prop(inu, "uv_map2", text="UV2")
                fc.prop(inu, "day_cols", text="Day")
                fc.prop(inu, "night_cols", text="Night")

        # ── Pipeline ──
        if obj.type == 'MESH':
            box = layout.box()
            box.label(text="Pipeline", icon=safe_icon('NODETREE'))
            box.prop(inu, "pipeline", text="")
            if inu.pipeline == 'CUSTOM':
                box.prop(inu, "custom_pipeline", text="")

        # ── Breakable ──
        if obj.type == 'MESH':
            box = layout.box()
            box.prop(inu, "breakable", text=T("Разрушаемый (Breakable)"))
            if inu.breakable:
                box.prop(inu, "breakable_force", text=T("Break Force"))

        # ── 2DFX (only for EMPTY with type='2DFX') ──
        if obj.type == 'EMPTY' and inu.type == '2DFX':
            box = layout.box()
            box.label(text="2DFX", icon=safe_icon('LIGHT'))
            box.prop(inu, "effect_2dfx", text=T("Тип эффекта"))
            if inu.effect_2dfx == 'LIGHT':
                box.prop(inu, "color_2dfx", text=T("Цвет"))
                row = box.row(align=True)
                row.prop(inu, "preset_2dfx", text=T("Пресет"))
                row.operator("gtatools.apply_2dfx_preset", text="", icon=compat.ICON_CHECK)



class GTATOOLS_PT_inu_tools_panel(bpy.types.Panel):
    """Панель INU Tools в Properties > Scene"""
    bl_label = "INU Tools"
    bl_idname = "GTATOOLS_PT_inu_tools_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    def draw(self, context):
        from ..ops.map_ops import _bbox_mode_active
        layout = self.layout
        scene = context.scene

        # IDE / IPL / IMG paths (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene.inu_settings, "gtatools_show_paths_settings",
                 icon=safe_icon('TRIA_DOWN') if scene.inu_settings.gtatools_show_paths_settings else 'TRIA_RIGHT',
                 text=T("Import Map"), emboss=False)
        if scene.inu_settings.gtatools_show_paths_settings:
            box.label(text="Game Root", icon=safe_icon('FILE_FOLDER'))
            box.prop(scene.inu_settings, "gtatools_game_root", text="")
            box.operator("gtatools.discover_game", text=T("Auto-discover"))
            # Все «Без …» тогглы импорта в одном блоке — пара рядов
            # сразу под Auto-discover, чтобы пользователь видел все
            # фильтры импорта в одном месте без скролла.
            row = box.row(align=True)
            row.prop(scene.inu_settings, "gtatools_img_skip_lod",
                     text=T("Без LOD"), toggle=True)
            row.prop(scene.inu_settings, "gtatools_map_skip_2dfx",
                     text=T("Без 2DFX"), toggle=True)
            row = box.row(align=True)
            row.prop(scene.inu_settings, "gtatools_img_load_txd",
                     text=T("Без TXD"), toggle=True, invert_checkbox=True)
            row.prop(scene.inu_settings, "gtatools_map_load_col",
                     text=T("Без коллизии"), toggle=True, invert_checkbox=True)
            box.prop(scene.inu_settings, "gtatools_map_region", text="")

            # Binary IPL selector (collapsible)
            bi_box = box.box()
            bi_row = bi_box.row(align=True)
            bi_row.prop(
                scene.inu_settings, "gtatools_show_binary_ipls",
                icon=safe_icon('TRIA_DOWN') if scene.inu_settings.gtatools_show_binary_ipls else 'TRIA_RIGHT',
                emboss=False,
                text=T("Бинарные IPL") + f": {len(scene.inu_settings.gtatools_binary_ipls)}",
            )
            bi_row.operator(
                "gtatools.scan_binary_ipls", text="", icon=safe_icon('FILE_REFRESH'),
            )
            if scene.inu_settings.gtatools_show_binary_ipls:
                cached_region = scene.get('gtatools_binary_ipls_region', '')
                if cached_region and cached_region != scene.inu_settings.gtatools_map_region:
                    bi_box.label(
                        text=T("Район изменился — пересканируйте"),
                        icon=safe_icon('ERROR'),
                    )
                if not scene.inu_settings.gtatools_binary_ipls:
                    bi_box.label(
                        text=T("Список пуст — нажмите Scan"),
                        icon=safe_icon('INFO'),
                    )
                else:
                    bi_row2 = bi_box.row(align=True)
                    op_all = bi_row2.operator(
                        "gtatools.binary_ipl_toggle_all",
                        text=T("Все"), icon=safe_icon('CHECKBOX_HLT'),
                    )
                    op_all.enable = True
                    op_none = bi_row2.operator(
                        "gtatools.binary_ipl_toggle_all",
                        text=T("Никакие"), icon=safe_icon('CHECKBOX_DEHLT'),
                    )
                    op_none.enable = False
                    bi_col = bi_box.column(align=True)
                    for item in scene.inu_settings.gtatools_binary_ipls:
                        bi_col.prop(item, "enabled", text=item.name)

            # Cache dir lives next to the .blend. When the scene is
            # unsaved, wrap the (disabled) button + warning label in
            # a single red alert-box so the user sees the
            # requirement and the affected control as one unit.
            # Once saved, the wrapper vanishes and only the regular
            # button remains.
            saved = bool(bpy.data.filepath)
            if saved:
                box.operator("gtatools.extract_textures",
                             text=T("Извлечь ресурсы"),
                             icon=safe_icon('PACKAGE'))
            else:
                warn = box.box()
                warn.alert = True
                warn_row = warn.row()
                warn_row.alignment = 'CENTER'
                warn_row.label(
                    text=T("Сначала сохраните .blend"),
                    icon=safe_icon('ERROR'))
                btn_row = warn.row(align=True)
                btn_row.enabled = False
                btn_row.operator("gtatools.extract_textures",
                                 text=T("Извлечь ресурсы"),
                                 icon=safe_icon('PACKAGE'))
            # «Без LOD/2DFX/TXD/коллизии» — все 4 фильтра импорта
            # вынесены наверх под Auto-discover, здесь не дублируем.
            box.prop(scene.inu_settings, "gtatools_map_group_by_ipl",
                     text=T("Группировать по IPL"), toggle=True,
                     icon=safe_icon('OUTLINER_COLLECTION'))
            # Same red alert pattern as Extract Resources: when the
            # scene is unsaved, wrap the warning + disabled buttons
            # in a single alert-box. Once saved, fall back to the
            # soft cache-empty INFO hint and normal active buttons.
            import os as _os_panel
            blend_path = bpy.data.filepath
            saved = bool(blend_path)
            cache_exists = saved and _os_panel.path.isdir(
                _os_panel.path.join(_os_panel.path.dirname(blend_path),
                                    '.inu_cache'))
            # Import/Export Map — primary actions of the panel, делаем
            # row.scale_y > 1 чтобы кнопки были крупнее остальных.
            _MAP_BTN_SCALE = 1.7
            if saved:
                if cache_exists:
                    row = box.row(align=True)
                    row.scale_y = _MAP_BTN_SCALE
                    row.operator("gtatools.import_map",
                                 text=T("Import Map"),
                                 icon=safe_icon('IMPORT'))
                    row.operator("gtatools.map_export",
                                 text=T("Export Map"),
                                 icon=safe_icon('EXPORT'))
                else:
                    # Saved but no cache: wrap warning + disabled
                    # Import Map together; Export Map stays active
                    # OUTSIDE the alert box since exporting doesn't
                    # need extracted resources.
                    warn = box.box()
                    warn.alert = True
                    warn_row = warn.row()
                    warn_row.alignment = 'CENTER'
                    warn_row.label(
                        text=T("Кеш пуст — карта без моделей"),
                        icon=safe_icon('INFO'))
                    btn_row = warn.row(align=True)
                    btn_row.enabled = False
                    btn_row.scale_y = _MAP_BTN_SCALE
                    btn_row.operator("gtatools.import_map",
                                     text=T("Import Map"),
                                     icon=safe_icon('IMPORT'))
                    exp_row = box.row(align=True)
                    exp_row.scale_y = _MAP_BTN_SCALE
                    exp_row.operator("gtatools.map_export",
                                     text=T("Export Map"),
                                     icon=safe_icon('EXPORT'))
            else:
                warn = box.box()
                warn.alert = True
                warn_row = warn.row()
                warn_row.alignment = 'CENTER'
                warn_row.label(
                    text=T("Сначала сохраните .blend"),
                    icon=safe_icon('ERROR'))
                btn_row = warn.row(align=True)
                btn_row.enabled = False
                btn_row.scale_y = _MAP_BTN_SCALE
                btn_row.operator("gtatools.import_map",
                                 text=T("Import Map"),
                                 icon=safe_icon('IMPORT'))
                btn_row.operator("gtatools.map_export",
                                 text=T("Export Map"),
                                 icon=safe_icon('EXPORT'))
            box.prop(scene.inu_settings, "gtatools_profile_enabled",
                     text=T("Профайлер (debug timings)"), toggle=False)
            # Links toggle moved to the Check panel ("Проверка") —
            # it's a validation overlay, not a map-import setting.
            box.operator("gtatools.toggle_bbox",
                         text=T("BBox: ON") if _bbox_mode_active else T("BBox: OFF"),
                         icon=safe_icon('MESH_CUBE'),
                         depress=_bbox_mode_active)
            box.separator()
            box.label(text="IDE", icon=safe_icon('TEXT'))
            box.prop(scene.inu_settings, "gtatools_ide_path", text="")
            box.label(text="IPL", icon=safe_icon('EMPTY_AXIS'))
            box.prop(scene.inu_settings, "gtatools_ipl_path", text="")
            box.label(text="IMG", icon=safe_icon('PACKAGE'))
            box.prop(scene.inu_settings, "gtatools_img_path", text="")

        # Textures (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene.inu_settings, "gtatools_show_texture_settings",
                 icon=safe_icon('TRIA_DOWN') if scene.inu_settings.gtatools_show_texture_settings else 'TRIA_RIGHT',
                 text=T("Текстуры"), emboss=False)
        if scene.inu_settings.gtatools_show_texture_settings:
            box.label(text=T("Системные текстуры:"), icon=safe_icon('TEXTURE'))
            box.prop(scene.inu_settings, "gtatools_texture_path1", text="")
            row = box.row()
            row.label(text=T("Папка .blend:"), icon=safe_icon('FILE_FOLDER'))
            row.operator("gtatools.set_blend_folder", text="", icon=safe_icon('FILE_REFRESH'))
            box.prop(scene.inu_settings, "gtatools_texture_path2", text="")
            box.operator("gtatools.load_textures", text=T("Загрузить текстуры"), icon=safe_icon('IMPORT'))

        # IMG file list (collapsible)
        box = layout.box()
        row = box.row()
        row.prop(scene.inu_settings, "gtatools_show_img_list",
                 icon=safe_icon('TRIA_DOWN') if scene.inu_settings.gtatools_show_img_list else 'TRIA_RIGHT',
                 text=T("Файлы IMG"), emboss=False)
        if scene.inu_settings.gtatools_show_img_list:
            if len(scene.inu_settings.gtatools_img_entries) > 0:
                box.template_list("GTATOOLS_UL_img_files", "",
                                  scene.inu_settings, "gtatools_img_entries",
                                  scene.inu_settings, "gtatools_img_entries_index", rows=8)
                entries = scene.inu_settings.gtatools_img_entries
                dff_c = sum(1 for e in entries if e.name.lower().endswith('.dff'))
                col_c = sum(1 for e in entries if e.name.lower().endswith('.col'))
                txd_c = sum(1 for e in entries if e.name.lower().endswith('.txd'))
                box.label(text=f"DFF: {dff_c}  COL: {col_c}  TXD: {txd_c}  Total: {len(entries)}", icon=safe_icon('INFO'))
            box.operator("gtatools.refresh_img_list", text=T("Обновить список"), icon=safe_icon('FILE_REFRESH'))



@apply_order
class GTATOOLS_PT_id_manager_panel(bpy.types.Panel):
    """Менеджер ID моделей GTA SA"""
    bl_label = "ID Manager"
    bl_idname = "GTATOOLS_PT_id_manager_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('COPY_ID'))

    def draw(self, context):
        from .. import _draw_id_manager
        layout = self.layout
        scene = context.scene
        _draw_id_manager(layout, scene, context)



@apply_order
class GTATOOLS_PT_light_master(bpy.types.Panel):
    """Lighting — общий контейнер для всех инструментов по работе со светом
    и vertex colors. Объединяет 5 подпанелей (Prelight, Prelight COL,
    Vertex Paint, LightMap, Itera Tools 3) под одним заголовком, чтобы не
    раздувать N-sidebar пятью отдельными top-level панелями. Все дети
    свёрнуты по умолчанию — юзер раскрывает только нужный."""
    bl_label = "Lighting"
    bl_idname = "GTATOOLS_PT_light_master"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('LIGHT'))

    def draw(self, context):
        # Container only — actual content lives in subpanels below.
        # A short hint helps when all children are collapsed.
        col = self.layout.column()
        col.scale_y = 0.7
        col.label(text=T("Раскройте нужный инструмент:"), icon=safe_icon('INFO'))



class GTATOOLS_PT_prelight_panel(bpy.types.Panel):
    """Панель Prelight"""
    bl_label = "Prelight"
    bl_idname = "GTATOOLS_PT_prelight_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_light_master"
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('COLOR'))

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene

        # Setup Lights
        row = layout.row(align=True)
        row.operator("gtatools.create_prelight_lights", text=T("Создать 8 ламп"), icon=safe_icon('LIGHT'))
        row.operator("gtatools.remove_prelight_lights", text=T("Удалить"), icon='X')

        # Пресеты охватывают всю панель Prelight и её подпанели.
        # «Применить» (load) — primary action, в конце ряда с текстом.
        # Поскольку у load text=«Применить», scale_x на load_cell реально
        # тянет ВИДИМУЮ ширину кнопки (текст ужимается/растягивается),
        # в отличие от icon-only кнопок где cell разбухает пустым местом.
        # ВАЖНО: оператор `prelight_preset_LOAD` импортирует значения из
        # выбранного пресета в сцену. `prelight_preset_APPLY` несмотря
        # на имя — overwrite выбранного пресета текущими настройками,
        # для него мелкая ✓ слева.
        preset_row = layout.row(align=True)
        # Слева — load (✓ Применить): загрузить выбранный пресет в сцену.
        # Primary action, шире остальных через scale_x.
        load_cell = preset_row.row(align=True)
        load_cell.scale_x = 1
        load_cell.operator("gtatools.prelight_preset_load",
                           text=T("Применить"),
                           icon=compat.ICON_CHECK)
        preset_row.prop(scene.inu_settings, "gtatools_prelight_preset", text="")
        preset_row.operator("gtatools.prelight_preset_rename", text="", icon=safe_icon('GREASEPENCIL'))
        preset_row.operator("gtatools.prelight_preset_save", text="", icon=safe_icon('ADD'))
        preset_row.operator("gtatools.prelight_preset_delete", text="", icon=safe_icon('REMOVE'))
        # Справа — overwrite (export-up arrow): сохранить текущие настройки
        # в выбранный пресет (визуально «отправить вверх в пресет»).
        preset_row.operator("gtatools.prelight_preset_apply", text="", icon=safe_icon('EXPORT'))

        if obj and obj.type == 'MESH':
            mesh = obj.data
            active_attr = compat.vcol_active(mesh)

            # Preview state computed up-front — кнопка теперь внутри box'а
            # слева от Day/Night рядов как высокий вертикальный rect.
            _preview_on = False
            for _ms in obj.material_slots:
                _m = _ms.material
                if _m and _m.use_nodes and _m.node_tree.nodes.get("Prelight_Mix"):
                    _preview_on = True
                    break
            _pv_icon = safe_icon('HIDE_OFF') if _preview_on else 'HIDE_ON'

            box = layout.box()
            # Two-column body: tall preview eye on the left, Day/Night
            # rows on the right.
            # preview_col имеет ФИКСИРОВАННУЮ ширину (ui_units_x ≈ 1 icon-
            # ширина) — иначе body.row делит 50/50 и Day/Night колонка
            # ужимается, а внутри неё страдают [+]/[—] кнопки.
            body = box.row(align=True)
            preview_col = body.column(align=True)
            preview_col.ui_units_x = 1.4
            preview_col.scale_y = 2.0
            op_pv = preview_col.operator("gtatools.prelight_preview",
                                         text="", icon=_pv_icon,
                                         depress=_preview_on)
            op_pv.enable = not _preview_on
            box_col = body.column(align=True)

            # Day / Night rows: [select btn][V offset prop][— remove].
            # Кнопка-селектор слева, V-offset справа от неё, кнопка
            # удаления в самом конце. Значение V применяется
            # автоматически при изменении (callback на per-object
            # FloatProperty).
            for _attr_name, _v_prop in (("Day", "gtatools_v_offset_day"),
                                        ("Night", "gtatools_v_offset_night")):
                # 3-cell layout: [name 60%][V slot ~34%][action btn ~6%].
                # Same column geometry whether the attribute exists or
                # not, so the «+» (create) lands in exactly the slot
                # the «—» (remove) would, instead of stretching across
                # the whole right side.
                row = box_col.split(factor=0.6, align=True)
                left = row.row(align=True)
                right_part = row.split(factor=0.85, align=True)
                v_cell = right_part.row(align=True)
                btn_cell = right_part.row(align=True)
                if compat.vcol_get(mesh, _attr_name) is not None:
                    is_active = bool(active_attr and active_attr.name == _attr_name)
                    icon = safe_icon('RADIOBUT_ON') if is_active else 'RADIOBUT_OFF'
                    op = left.operator("gtatools.select_color_attribute",
                                       text=_attr_name, icon=icon, depress=is_active)
                    op.attribute_name = _attr_name
                    v_cell.prop(obj, _v_prop, text="V")
                    op = btn_cell.operator("gtatools.remove_color_attr", text="", icon=safe_icon('REMOVE'))
                    op.attr_name = _attr_name
                else:
                    left.label(text=_attr_name, icon=safe_icon('RADIOBUT_OFF'))
                    # Disabled-prop как «фантом» V — занимает ту же ширину,
                    # что и активный prop в [—]-state. Иначе label("") был
                    # 0-ширины, split-proportions уезжали, и btn ([+])
                    # становился визуально уже чем [—] после создания attr.
                    v_sub = v_cell.row(align=True)
                    v_sub.enabled = False
                    v_sub.prop(obj, _v_prop, text="V")
                    op = btn_cell.operator("gtatools.create_color_attr", text="", icon=safe_icon('ADD'))
                    op.attr_name = _attr_name

            # Other attributes are NOT shown here — they live in the
            # «Слои Vertex Color» collapsible section below LightMap.
            #
            # REMOVED: combined Preview / Day-Night-create / Add / Remove row.
            # • Preview-глаз перенесён внутрь box'а как высокая левая ячейка.
            # • «Day/Night» (создавал сразу оба) и bulk +/- убраны —
            #   каждая строка уже имеет свой персональный + / — для своего
            #   attr-name, чтобы юзеру было понятнее что именно создаётся.

            # Bake row сразу под Day/Night атрибутами — это primary action
            # после настройки V-offset'ов, держим близко к атрибутам чтобы
            # workflow читался сверху-вниз: pick attr → tune V → bake.
            row = layout.row(align=True)
            row.operator("gtatools.bake_vertex_colors_simple", text=T("Запечь"), icon=safe_icon('RENDER_STILL'))
            op_bs = row.operator("gtatools.bake_vertex_colors", text=T("Запечь с тенями"), icon=safe_icon('RENDER_RESULT'))
            op_bs.use_shadows = True

            # Copy Day ↔ Night — text-only buttons. Earlier the
            # FORWARD/BACK icons looked like media-player play/back
            # buttons and competed visually with the `→` glyph in the
            # label. Removing the icons leaves one unambiguous arrow
            # per button, which is what the user reads anyway.
            row = layout.row(align=True)
            op = row.operator("gtatools.copy_color_attr", text="Day → Night")
            op.source = "Day"
            op.target = "Night"
            op = row.operator("gtatools.copy_color_attr", text="Night → Day")
            op.source = "Night"
            op.target = "Day"

            # LightMap UV2 row
            row = layout.row(align=True)
            _lm_on = False
            _lm_exists = False
            for _ms in obj.material_slots:
                _m = _ms.material
                if _m and _m.use_nodes:
                    _lm_mix = _m.node_tree.nodes.get("LM_Mix")
                    if _lm_mix:
                        _lm_exists = True
                        if not _lm_mix.mute:
                            _lm_on = True
                        break
            _lm_icon=safe_icon('HIDE_OFF') if _lm_on else 'HIDE_ON'
            if _lm_exists:
                op_lm = row.operator("gtatools.toggle_lightmap_uv2", text="", icon=_lm_icon, depress=_lm_on)
                op_lm.enable = not _lm_on
            else:
                row.label(text="", icon=safe_icon('HIDE_ON'))
            row.operator("gtatools.apply_lightmap_uv2", text=T("Добавить LightMap"))
            row.operator("gtatools.remove_lightmap_uv2", text="", icon=safe_icon('REMOVE'))

            # ─── Слои Vertex Color (collapsible, inline) ──────────────
            # Sits below LightMap so the user sees it in the natural
            # flow of vertex-color editing — pick base → tweak with
            # layers. Bake row уже выведен выше (рядом с Day/Night).
            # Collapsed by default until the user adds their first VCL.
            from ..tools.vc_layers import draw_vc_layers_section
            draw_vc_layers_section(layout, context, mesh)

        # Bake row перенесён внутрь `if obj and obj.type == 'MESH'`
        # сразу под Day/Night атрибутами — без активного меша запекать
        # всё равно нечего, операторы сами выдают error в том случае.

        # V-offset переехал инлайн в Day/Night-строки выше — каждый
        # атрибут хранит свой V и применяется автоматически.

        # Modulate Color — preview-only пресет: OFF / Day / Night.
        # Хардкод значений из ванильного timecyc.dat (EXTRASUNNY_LA).
        # Vcols и DFF-флаги не трогаются. Заголовок секции убран —
        # кнопки Выкл/Day/Night сами по себе понятны.
        layout.prop(scene.inu_settings, "gtatools_modulate_mode", expand=True)




class GTATOOLS_PT_bake_settings_subpanel(bpy.types.Panel):
    """Расширенные настройки запекания"""
    bl_label = "Advanced Settings"
    bl_idname = "GTATOOLS_PT_bake_settings_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_prelight_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene.inu_settings, "gtatools_bake_ambient", text=T("Окружающий"), slider=True)
        layout.prop(scene.inu_settings, "gtatools_bake_intensity", text=T("Интенсивность"), slider=True)
        layout.prop(scene.inu_settings, "gtatools_bake_gamma", text=T("Гамма"), slider=True)

        layout.separator()
        layout.operator("gtatools.reset_bake_settings", icon=safe_icon('LOOP_BACK'))

        # Presets перенесены в шапку Prelight (рядом с «Цветовые атрибуты:»)
        # — теперь они охватывают всю панель и её подпанели.



class GTATOOLS_PT_scatter_color_subpanel(bpy.types.Panel):
    """Sub-panel: инструменты для работы со светом / vertex colors."""
    bl_label = "Инструменты"
    bl_idname = "GTATOOLS_PT_scatter_color_subpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_prelight_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Defensive: любой exception в draw() ломает рендер панели.
        # Сначала рисуем кнопку «Применить» сверху, потом параметры,
        # чтобы кнопка точно была видна даже если color picker упадёт.
        layout.operator("gtatools.scatter_color",
                        text=T("Применить"),
                        icon=safe_icon('CHECKMARK'))

        layout.prop(scene.inu_settings, "gtatools_scatter_color_strength",
                    text=T("Сила"), slider=True)
        layout.prop(scene.inu_settings, "gtatools_scatter_color_distance",
                    text=T("Дальность"), slider=True)

        # Цвет: пробуем взять из активной Vertex Paint brush; иначе
        # используем scene prop. Любая ошибка → fallback на scene prop.
        try:
            ts = context.tool_settings
            vp = getattr(ts, 'vertex_paint', None)
            brush = getattr(vp, 'brush', None) if vp else None
            if brush is not None and hasattr(brush, 'color'):
                layout.prop(brush, "color", text=T("Цвет (из кисти)"))
            else:
                layout.prop(scene.inu_settings, "gtatools_scatter_color_color",
                            text=T("Цвет"))
        except Exception:
            layout.prop(scene.inu_settings, "gtatools_scatter_color_color",
                        text=T("Цвет"))


class GTATOOLS_PT_vc_postprocess_panel(bpy.types.Panel):
    """Панель пост-обработки vertex colors"""
    bl_label = "Post-Processing"
    bl_idname = "GTATOOLS_PT_vc_postprocess_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_prelight_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        from .. import _draw_label_with_info
        layout = self.layout
        scene = context.scene

        # Smooth
        box = layout.box()
        _draw_label_with_info(box, T("Сглаживание:"),
            T("Сглаживание vertex colors между соседними вершинами\nIterations — количество проходов\nFactor — сила сглаживания (0-1)"),
            icon=safe_icon('MOD_SMOOTH'))
        row = box.row(align=True)
        row.prop(scene.inu_settings, "gtatools_vc_smooth_iterations", text=T("Проходы"))
        row.prop(scene.inu_settings, "gtatools_vc_smooth_factor", text=T("Сила"))
        box.operator("gtatools.vc_smooth", text=T("Сгладить"), icon=safe_icon('SMOOTHCURVE'))

        # Contrast
        box = layout.box()
        _draw_label_with_info(box, T("Контраст:"),
            T("Контраст vertex colors\n1.0 — без изменений\n< 1.0 — меньше контраст\n> 1.0 — больше контраст"),
            icon=safe_icon('CAMERA_DATA'))
        row = box.row(align=True)
        row.prop(scene.inu_settings, "gtatools_vc_contrast", text=T("Контраст"))
        row.operator("gtatools.vc_contrast", text=T("Применить"), icon=compat.ICON_CHECK)

        # Brightness
        box = layout.box()
        _draw_label_with_info(box, T("Яркость:"),
            T("Яркость vertex colors\n0.0 — без изменений\n> 0 — светлее\n< 0 — темнее"),
            icon=safe_icon('LIGHT_SUN'))
        row = box.row(align=True)
        row.prop(scene.inu_settings, "gtatools_vc_brightness", text=T("Яркость"))
        row.operator("gtatools.vc_brightness", text=T("Применить"), icon=compat.ICON_CHECK)

        # Gamma
        box = layout.box()
        _draw_label_with_info(box, T("Гамма:"),
            T("Гамма-коррекция vertex colors\n1.0 — без изменений\n< 1.0 — светлее (тени)\n> 1.0 — темнее (тени)"),
            icon=safe_icon('FCURVE'))
        row = box.row(align=True)
        row.prop(scene.inu_settings, "gtatools_vc_gamma", text=T("Гамма"))
        row.operator("gtatools.vc_gamma", text=T("Применить"), icon=compat.ICON_CHECK)

        # Smooth between objects
        layout.separator()
        layout.operator("gtatools.vc_smooth_between", text=T("Сгладить между объектами"), icon=safe_icon('MOD_SMOOTH'))



class GTATOOLS_PT_itera_panel(bpy.types.Panel):
    """Интеграция с Itera Tools 3 — материалы освещения"""
    bl_label = "Itera Tools 3"
    bl_idname = "GTATOOLS_PT_itera_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_light_master"
    bl_order = 4
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('LIGHT_SUN'))

    def draw(self, context):
        from ..ops.light_ops import _find_itera_blend_path
        layout = self.layout

        itera_path = _find_itera_blend_path()
        if not itera_path:
            layout.label(text=T("Itera не найден в библиотеках ассетов"), icon=safe_icon('ERROR'))
            return

        # Apply presets
        row = layout.row(align=True)
        row.operator("gtatools.apply_itera_material", text="Vertex Lit Linear", icon=safe_icon('MATERIAL'))
        row.operator("gtatools.apply_itera_quickstart", text="Quickstart", icon=safe_icon('NODE_MATERIAL'))

        layout.operator("gtatools.remove_itera_material", text=T("Убрать Itera"), icon=safe_icon('LOOP_BACK'))

        layout.separator()

        # Fix Itera Collection
        itera_cols = [c for c in bpy.data.collections if c.name.startswith("Template Scene - Vertex Lights")]
        if itera_cols:
            needs_fix = any(c.library or c.name not in context.scene.collection.children for c in itera_cols)
            if needs_fix:
                layout.operator("gtatools.fix_itera_collection", text=T("Исправить коллекцию Itera"), icon=safe_icon('LIGHT'))
            else:
                row = layout.row()
                row.enabled = False
                row.operator("gtatools.fix_itera_collection", text=T("Коллекция Itera исправлена"), icon=compat.ICON_CHECK)



class GTATOOLS_PT_prelight_col_panel(bpy.types.Panel):
    """Конвертировать vertex colors в COL Day/Night Light"""
    bl_label = "Prelight COL"
    bl_idname = "GTATOOLS_PT_prelight_col_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_light_master"
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('COLOR'))

    def draw(self, context):
        from .. import _col_light_mod
        from .. import _draw_label_with_info
        layout = self.layout
        obj = context.active_object
        scene = context.scene

        # Show source layers
        if obj and obj.type == 'MESH' and compat.vcol_list(obj.data):
            mesh = obj.data
            _act = compat.vcol_active(mesh)
            day_src = "Day" if compat.vcol_get(mesh, "Day") else (_act.name if _act else "—")
            night_src = "Night" if compat.vcol_get(mesh, "Night") else day_src
            layout.label(text=f"Day: {day_src} | Night: {night_src}", icon=safe_icon('COLOR'))
        else:
            layout.label(text=T("Нет vertex colors"), icon=safe_icon('INFO'))

        layout.separator()

        # Day range
        box = layout.box()
        _draw_label_with_info(box, T("Дневной свет:"),
            T("Диапазон дневного освещения для COL материалов\nMin/Max — значения от 0 до 15\nЯркость vertex colors конвертируется в этот диапазон"),
            icon=safe_icon('LIGHT_SUN'))
        row = box.row(align=True)
        row.prop(scene.inu_settings, "gtatools_col_day_min", text=T("Мин."))
        row.prop(scene.inu_settings, "gtatools_col_day_max", text=T("Макс."))

        # Night range
        box = layout.box()
        _draw_label_with_info(box, T("Ночной свет:"),
            T("Диапазон ночного освещения для COL материалов\nMin/Max — значения от 0 до 15\nИспользует Night color attribute если есть"),
            icon=safe_icon('SHADING_RENDERED'))
        row = box.row(align=True)
        row.prop(scene.inu_settings, "gtatools_col_night_min", text=T("Мин."))
        row.prop(scene.inu_settings, "gtatools_col_night_max", text=T("Макс."))

        layout.separator()

        # Preview button
        preview_icon=safe_icon('HIDE_OFF') if _col_light_mod._col_light_preview_active else 'HIDE_ON'
        preview_text = T("Скрыть превью") if _col_light_mod._col_light_preview_active else T("Превью COL Light")
        layout.operator("gtatools.preview_col_light", text=preview_text,
                         icon=preview_icon, depress=_col_light_mod._col_light_preview_active)

        if _col_light_mod._col_light_preview_active:
            box = layout.box()
            box.prop(scene.inu_settings, "gtatools_col_light_edge", text=T("Край"), slider=True)
            box.prop(scene.inu_settings, "gtatools_col_light_threshold", text=T("Порог"), slider=True)
            box.prop(scene.inu_settings, "gtatools_col_light_contrast", text=T("Контраст"), slider=True)
            row = box.row(align=True)
            row.prop(scene.inu_settings, "gtatools_col_light_show_numbers", text=T("Цифры"), toggle=True)
            row.prop(scene.inu_settings, "gtatools_col_light_font_size", text=T("Размер"))

        row = layout.row(align=True)
        row.operator("gtatools.bake_col_light", text=T("Запечь COL Light"), icon=safe_icon('RENDER_STILL'))
        row.operator("gtatools.clear_col_light_mats", text="", icon='X')

        # Show info about created COL materials
        if obj and obj.type == 'MESH':
            import json
            stored = json.loads(obj.get("gtatools_col_light_mats", "[]"))
            if stored:
                layout.label(text=f"{T('COL light материалов:')} {len(stored)}", icon=compat.ICON_CHECK)



class GTATOOLS_PT_vertex_paint_panel(bpy.types.Panel):
    """Панель инструментов Vertex Paint"""
    bl_label = "Vertex Paint"
    bl_idname = "GTATOOLS_PT_vertex_paint_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_light_master"
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return False  # Hidden — code kept for future use

    def draw(self, context):
        from ..tools.prelight import get_scatter_levels
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        # Mode switching
        layout.label(text=T("Режим:"))
        row = layout.row(align=True)
        row.operator("gtatools.switch_to_edit", text=T("Редактор"), icon=safe_icon('EDITMODE_HLT'))
        row.operator("gtatools.switch_to_vpaint", text=T("Рисование"), icon=safe_icon('VPAINT_HLT'))

        # Face selection toggle (only in Vertex Paint mode)
        if obj and obj.mode == 'VERTEX_PAINT':
            row = layout.row()
            icon=safe_icon('RESTRICT_SELECT_OFF') if obj.data.use_paint_mask else 'RESTRICT_SELECT_ON'
            row.operator("gtatools.toggle_face_select", text=T("Выделение граней"), icon=icon, depress=obj.data.use_paint_mask)

        layout.separator()

        # Fill selected faces
        layout.label(text=T("Заливка граней:"))
        row = layout.row(align=True)
        row.prop(scene.inu_settings, "gtatools_fill_color", text="")
        row.operator("gtatools.eyedropper_color", text="", icon=safe_icon('EYEDROPPER'))
        row = layout.row(align=True)
        row.operator("gtatools.fill_faces", text=T("Залить"), icon=safe_icon('BRUSH_DATA'))
        row.operator("gtatools.restore_fill", text=T("Восстановить"), icon=safe_icon('LOOP_BACK'))

        # Список использованных цветов с уровнями
        if obj and hasattr(obj, 'gtatools_fill_colors') and len(obj.gtatools_fill_colors) > 0:
            for i, item in enumerate(obj.gtatools_fill_colors):
                color_box = layout.box()

                # Заголовок цвета
                row = color_box.row(align=True)
                row.prop(item, "color", text="")
                # Кнопка выделения полигонов с этим цветом
                op = row.operator("gtatools.select_fill_color", text="", icon=safe_icon('RESTRICT_SELECT_OFF'))
                op.index = i
                # Кнопка удаления цвета (и всех его уровней)
                op = row.operator("gtatools.remove_fill_color", text="", icon='X')
                op.index = i

                # Scatter уровни для этого цвета
                color = item.color
                levels = get_scatter_levels(obj, color)
                if levels:
                    row = color_box.row()
                    row.label(text=f"Levels ({len(levels)}):")
                    op = row.operator("gtatools.clear_fill_color_levels", text=T("Очистить всё"), icon='X')
                    op.color_index = i

                    levels_box = color_box.box()
                    last_level = max(levels)

                    # Показываем только последний уровень
                    max_visible = 1
                    if len(levels) > max_visible:
                        hidden_count = len(levels) - max_visible
                        row = levels_box.row()
                        row.label(text=f"... +{hidden_count} hidden", icon=safe_icon('THREE_DOTS'))
                        visible_levels = levels[-max_visible:]
                    else:
                        visible_levels = levels

                    for lvl in visible_levels:
                        row = levels_box.row(align=True)
                        row.label(text=f"Level {lvl}")
                        # Кнопка отмены только для последнего уровня
                        if lvl == last_level:
                            op = row.operator("gtatools.delete_fill_color_level", text=T("Отменить"), icon=safe_icon('LOOP_BACK'))
                            op.color_index = i
                            op.level = lvl

        layout.separator()

        # Scatter light
        row = layout.row()
        row.label(text=T("Рассеянный свет:"))
        row.operator("gtatools.reset_scatter_settings", text="", icon=safe_icon('LOOP_BACK'))
        layout.prop(scene.inu_settings, "gtatools_scatter_intensity", text=T("Интенсивность"), slider=True)
        layout.prop(scene.inu_settings, "gtatools_scatter_falloff", text=T("Затухание"), slider=True)
        layout.prop(scene.inu_settings, "gtatools_scatter_iterations", text=T("Итерации"))
        layout.prop(scene.inu_settings, "gtatools_scatter_radius", text=T("Радиус (0=авто)"), slider=True)
        layout.operator("gtatools.scatter_light", text=T("Рассеять от выделенных"), icon=safe_icon('LIGHT_POINT'))



class GTATOOLS_PT_lightmap_panel(bpy.types.Panel):
    """Панель генератора Lightmap"""
    bl_label = "LightMap (beta_MTA)"
    bl_idname = "GTATOOLS_PT_lightmap_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_light_master"
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return False  # Hidden — code kept for future use

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Load Lightmap texture
        layout.label(text=T("Текстура Lightmap:"))
        row = layout.row(align=True)
        row.operator("gtatools.load_lightmap", text=T("Загрузить (LP_)"), icon=safe_icon('IMAGE_DATA'))
        row.operator("gtatools.remove_lightmap", text=T("Удалить"), icon='X')

        layout.separator()

        # Generate code
        layout.label(text=T("Генерация кода:"))
        layout.operator("gtatools.lightmap_generate", text=T("Генерировать"), icon=safe_icon('FILE_TEXT'))
        layout.prop(scene.inu_settings, "gtatools_lightmap_path", text=T("Путь"))
        layout.prop(scene.inu_settings, "gtatools_model_id", text=T("ID модели"))

        layout.separator()
        layout.label(text=T("Результат:"))

        box = layout.box()
        if scene.inu_settings.gtatools_lightmap_result:
            lines = scene.inu_settings.gtatools_lightmap_result.split('\n')
            for line in lines:
                box.label(text=line)
            row = layout.row(align=True)
            row.operator("gtatools.lightmap_copy", text=T("Копировать"), icon=safe_icon('COPYDOWN'))
            row.operator("gtatools.lightmap_clear", text=T("Очистить"), icon='X')
        else:
            box.label(text=T("Нажмите кнопку для генерации"))



@apply_order
class GTATOOLS_PT_water_panel(bpy.types.Panel):
    """Панель Water IO"""
    bl_label = "Water"
    bl_idname = "GTATOOLS_PT_water_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('MOD_FLUIDSIM'))

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Import / Export
        row = layout.row(align=True)
        row.operator("gtatools.import_water", text=T("Импорт"), icon=safe_icon('IMPORT'))
        row.operator("gtatools.export_water", text=T("Экспорт"), icon=safe_icon('EXPORT'))

        layout.separator()

        # Add water
        layout.operator("gtatools.add_water", text=T("Добавить воду"), icon=safe_icon('SHADING_RENDERED'))

        layout.separator()

        # Water parameters
        box = layout.box()
        box.label(text=T("Параметры воды:"), icon=safe_icon('PREFERENCES'))
        flag_labels = {
            '0': T("Обычная / Невидимая"),
            '1': T("Обычная / Видимая"),
            '2': T("Мелкая / Невидимая"),
            '3': T("Мелкая / Видимая"),
        }
        box.prop_menu_enum(scene.inu_settings, "gtatools_water_flag", text=flag_labels.get(scene.inu_settings.gtatools_water_flag, "?"))
        box.label(text=T("Скорость течения:"))
        row = box.row(align=True)
        row.prop(scene.inu_settings, "gtatools_water_speed_x", text="X")
        row.prop(scene.inu_settings, "gtatools_water_speed_y", text="Y")
        row.prop(scene.inu_settings, "gtatools_water_speed_z", text="Z")
        box.prop(scene.inu_settings, "gtatools_water_wave_height", text=T("Волны"))
        box.operator("gtatools.water_set_params", text=T("Применить"), icon=compat.ICON_CHECK)

        layout.separator()

        # Tools
        box = layout.box()
        box.label(text=T("Инструменты:"), icon=safe_icon('TOOL_SETTINGS'))
        box.operator("gtatools.water_snap_grid", text=T("Привязка к сетке (x4)"), icon=safe_icon('SNAP_GRID'))
        box.operator("gtatools.water_stitch", text=T("Сшить края"), icon=safe_icon('AUTOMERGE_ON'))

        # Show active object water info
        obj = context.active_object
        if obj and obj.type == 'MESH' and 'water_flag' in obj:
            layout.separator()
            box = layout.box()
            flag = obj.get('water_flag', -1)
            flag_names = {
                0: "Default / Invisible",
                1: "Default / Visible",
                2: "Shallow / Invisible",
                3: "Shallow / Visible",
            }
            box.label(text=f"{obj.name}: {flag_names.get(flag, '?')} (flag={flag})", icon=safe_icon('INFO'))



@apply_order
class GTATOOLS_PT_anim_panel(bpy.types.Panel):
    """Панель анимаций IFP"""
    bl_label = "Анимации"
    bl_idname = "GTATOOLS_PT_anim_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('ARMATURE_DATA'))

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # ── Internal tab switcher ──
        # Two distinct workflows ended up in this panel: ped/character
        # animation (IFP, IK Rig) and animated map props (windmills,
        # cranes). They have nothing in common UX-wise, so a tab row
        # at the top hides the irrelevant half.
        layout.prop(scene.inu_settings, "gtatools_anim_tab", expand=True)
        layout.separator()

        if scene.inu_settings.gtatools_anim_tab == 'OBJ':
            self._draw_object_tab(context, layout)
        else:
            self._draw_character_tab(context, layout)

    def _draw_object_tab(self, context, layout):
        """Animated Map Object — single-bone rotating prop workflow."""
        scene = context.scene
        obj = context.active_object

        # ── Top action row ──
        # In the Object tab the «Импорт» slot from the Character tab is
        # replaced by the combo «DFF+IFP+IDE»: importing an IFP rarely
        # makes sense when you're authoring a new animated prop from
        # scratch, but writing all three artefacts at once is the main
        # action for this workflow.
        row = layout.row(align=True)
        row.operator("gtatools.animobj_export",
                     text=T("DFF+IFP+IDE"), icon=safe_icon('EXPORT'))
        row.operator("gtatools.export_ifp",
                     text=T("Экспорт"), icon=safe_icon('EXPORT'))
        row.operator("gtatools.merge_ifp",
                     text=T("Добавить"), icon=safe_icon('FILE_REFRESH'))

        ifp_actions = [a for a in bpy.data.actions if a.get('ifp_source')]
        if ifp_actions:
            layout.label(
                text=f"{len(ifp_actions)} {T('анимаций загружено')}")

        layout.separator()

        amo_box = layout.box()
        amo_box.label(text=T("Animated Map Object"), icon=safe_icon('MOD_SCREW'))
        ar = amo_box.row(align=True)
        ar.operator("gtatools.animobj_setup",
                    text=T("Setup rig"), icon=safe_icon('ARMATURE_DATA'))
        ar.operator("gtatools.animobj_validate",
                    text=T("Validate"), icon=compat.ICON_CHECK)

        # Live-edit sliders for the active rig — same logic as before.
        rig = None
        if obj is not None:
            if obj.type == 'ARMATURE' and obj.get('inu_animobj'):
                rig = obj
            elif (obj.type == 'MESH' and obj.parent
                  and obj.parent.type == 'ARMATURE'
                  and obj.parent.get('inu_animobj')):
                rig = obj.parent
        if rig is not None:
            ed_box = amo_box.box()
            ed_box.label(text=f"{T('Настройки')}: {rig.name}",
                         icon=safe_icon('MOD_SCREW'))
            props = rig.inu_animobj_props

            # Mode toggle — always visible. Auto = sliders rebuild
            # keyframes; Manual = sliders frozen, user owns keyframes.
            # IPO_LINEAR icon = the "computed animation curve" mental
            # model; the default 'AUTO' icon is a literal car silhouette
            # in Blender and reads as "vehicle tools" instead of "auto".
            mode_row = ed_box.row(align=True)
            mode_row.prop(
                props, "auto_mode",
                text=T("Авто"),
                icon=safe_icon('IPO_LINEAR'),
                toggle=True)
            mr = mode_row.row(align=True)
            mr.enabled = False  # Pseudo-button — purely visual contrast
            mr.prop(
                props, "auto_mode",
                text=T("Вручную"),
                icon=safe_icon('HAND'),
                toggle=True, invert_checkbox=True)

            if props.auto_mode:
                ed_box.prop(props, "axis", expand=True)
                ed_box.prop(props, "reverse")
                ed_box.prop(props, "turns_per_cycle", slider=True)
                ed_box.prop(props, "duration_frames", slider=True)
                fps = max(1, scene.render.fps)
                sign = -1 if props.reverse else 1
                rpm = (sign * props.turns_per_cycle * fps
                       / max(1, props.duration_frames))
                ed_box.label(
                    text=f"≈ {rpm:+.2f} {T('об/сек при FPS')} {fps}",
                    icon=safe_icon('INFO'))
            else:
                # Manual mode: hide sliders to make the contract clear
                # and tell the user where to go.
                col = ed_box.column(align=True)
                col.scale_y = 0.85
                col.label(
                    text=T("Manual режим — keyframes управляются вручную"),
                    icon=safe_icon('HAND'))
                col.label(
                    text=T("Action Editor / Pose Mode"))
                col.label(
                    text=T("Переключение в Auto перезапишет твои ключи"),
                    icon=safe_icon('ERROR'))
        else:
            amo_box.label(
                text=T("Выдели MESH и нажми Setup rig"),
                icon=safe_icon('INFO'))

    def _draw_character_tab(self, context, layout):
        """Character animations — IFP I/O, action apply, IK Rig."""
        scene = context.scene
        obj = context.active_object

        # ── IFP main row ─────────────────────────────────────────
        row = layout.row(align=True)
        row.operator("gtatools.import_ifp",
                     text=T("Импорт"), icon=safe_icon('IMPORT'))
        row.operator("gtatools.export_ifp",
                     text=T("Экспорт"), icon=safe_icon('EXPORT'))
        row.operator("gtatools.merge_ifp",
                     text=T("Добавить"), icon=safe_icon('FILE_REFRESH'))

        # ── Loaded actions + apply / preview ─────────────────────
        ifp_actions = [a for a in bpy.data.actions if a.get('ifp_source')]
        if ifp_actions:
            layout.label(
                text=f"{len(ifp_actions)} {T('анимаций загружено')}")
            if obj and obj.type == 'ARMATURE':
                layout.prop_search(scene.inu_settings, "gtatools_ifp_action",
                                   bpy.data, "actions",
                                   text=T("Анимация"), icon=safe_icon('ACTION'))
                ar = layout.row(align=True)
                ar.operator("gtatools.apply_ifp",
                            text=T("Применить"), icon=safe_icon('PLAY'))
                try:
                    from ..ops.ifp_import import preview_is_active as _pv
                    _pv_on = _pv()
                except Exception:
                    _pv_on = False
                ar.operator(
                    "gtatools.ifp_preview_toggle",
                    text=T("Preview") if not _pv_on else T("Preview ●"),
                    icon=('HIDE_OFF' if not _pv_on
                          else 'RESTRICT_VIEW_OFF'),
                    depress=_pv_on)
                if obj.animation_data and obj.animation_data.action:
                    cur_row = layout.row(align=True)
                    cur_row.label(
                        text=f"{T('Текущая')}: "
                             f"{obj.animation_data.action.name}",
                        icon=safe_icon('ARMATURE_DATA'))
                    cur_row.operator(
                        "gtatools.delete_active_action",
                        text="", icon=safe_icon('TRASH'))
            else:
                layout.label(text=T("Выделите скелет для применения"),
                             icon=safe_icon('INFO'))

        # ── IK Rig label (no separator — the label itself
        # gives enough visual break, factor=1.5 leaves a too-big
        # gap on Blender 5.x default UI scale)
        layout.label(text=T("IK Rig"), icon=safe_icon('CON_KINEMATIC'))

        if obj and obj.type == 'ARMATURE':
            if obj.get('inu_ik_rigged'):
                layout.operator("gtatools.bake_ik_rig",
                                text=T("Bake & Clear IK"), icon=safe_icon('REC'))
            else:
                # Root motion toggle — must be set BEFORE Add IK Rig,
                # determines whether INU_IK_root targets Pelvis (off,
                # default) or the topmost bone (on, for walk/run).
                layout.prop(scene.inu_settings, "gtatools_ik_root_motion",
                            text=T("Root motion (walk/run)"))
                layout.operator("gtatools.add_ik_rig",
                                text=T("Add IK Rig"),
                                icon=safe_icon('CON_KINEMATIC'))

        # ── Single "Дополнительно" — IK extras + IFP utilities ──
        # Combined collapsible holds all the niche tweakables: ground
        # plane spawning, floor collision tuning, IK control color,
        # plus the rare round-trip and batch-import utilities. One
        # toggle keeps the panel calm during normal animation work.
        extras_row = layout.row(align=True)
        extras_row.alignment = 'LEFT'
        extras_row.prop(
            scene.inu_settings, "gtatools_ik_extras_show",
            text=T("Дополнительно"),
            icon=('TRIA_DOWN' if scene.inu_settings.gtatools_ik_extras_show
                  else 'TRIA_RIGHT'),
            emboss=False,
        )
        if scene.inu_settings.gtatools_ik_extras_show:
            ebox = layout.box()
            # Single align'd column collapses the inter-row gaps
            # Blender adds between standalone ``box.prop`` calls —
            # the section now reads as one grouped block.
            col = ebox.column(align=True)
            col.operator("gtatools.add_ground_plane",
                         text=T("Пол"), icon=safe_icon('MESH_PLANE'))
            col.prop(scene.inu_settings, "gtatools_floor_offset",
                     text=T("Коллизия"))
            # Color swatch shrinks to half-width when paired with
            # the size slider on the same row — saves a row and
            # matches the user's "цвет помельче" request.
            row = col.row(align=True)
            row.prop(scene.inu_settings, "gtatools_ik_color", text="")
            row.prop(scene.inu_settings, "gtatools_ik_size", text=T("Размер"))

            # 2×2 eye-icon grid for control-type visibility. Each
            # toggle keeps its short label and flips between
            # HIDE_OFF / HIDE_ON so the icon mirrors the state.
            col.separator()
            grid = col.grid_flow(
                row_major=True, columns=2, align=True)
            grid.prop(
                scene.inu_settings, "gtatools_ik_show_chain",
                text=T("Руки/ноги"),
                icon=('HIDE_OFF' if scene.inu_settings.gtatools_ik_show_chain
                      else 'HIDE_ON'),
                toggle=True)
            grid.prop(
                scene.inu_settings, "gtatools_ik_show_pole",
                text=T("Локти/колени"),
                icon=('HIDE_OFF' if scene.inu_settings.gtatools_ik_show_pole
                      else 'HIDE_ON'),
                toggle=True)
            grid.prop(
                scene.inu_settings, "gtatools_ik_show_rot",
                text=T("Голова/торс"),
                icon=('HIDE_OFF' if scene.inu_settings.gtatools_ik_show_rot
                      else 'HIDE_ON'),
                toggle=True)
            grid.prop(
                scene.inu_settings, "gtatools_ik_show_root",
                text=T("Корень"),
                icon=('HIDE_OFF' if scene.inu_settings.gtatools_ik_show_root
                      else 'HIDE_ON'),
                toggle=True)

            col.separator()
            col.operator("gtatools.ifp_roundtrip",
                         text=T("Проверить round-trip"),
                         icon=compat.ICON_CHECK)
            col.operator("gtatools.ifp_batch_import",
                         text=T("Batch папка…"),
                         icon=safe_icon('FILE_FOLDER'))

        # ── Настройка анимации — sign-fix утилиты с диапазоном кадров
        anim_row = layout.row(align=True)
        anim_row.alignment = 'LEFT'
        anim_row.prop(
            scene.inu_settings, "gtatools_anim_tools_show",
            text=T("Настройка анимации"),
            icon=('TRIA_DOWN' if scene.inu_settings.gtatools_anim_tools_show
                  else 'TRIA_RIGHT'),
            emboss=False,
        )
        if scene.inu_settings.gtatools_anim_tools_show:
            abox = layout.box()
            acol = abox.column(align=True)
            range_row = acol.row(align=True)
            range_row.prop(scene.inu_settings, "gtatools_anim_fix_start", text=T("Старт"))
            range_row.prop(scene.inu_settings, "gtatools_anim_fix_end", text=T("Конец"))
            acol.operator(
                "gtatools.fix_quat_signs",
                text=T("Исправить кватернионы (sign-flip)"),
                icon=safe_icon('ORIENTATION_GIMBAL'))



@apply_order
class GTATOOLS_PT_radar_panel(bpy.types.Panel):
    """X Radar Maker — генерация тайлов мини-карты GTA SA"""
    bl_label = "X Radar Maker"
    bl_idname = "GTATOOLS_PT_radar_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('TRACKER'))

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        layout.prop(scn.inu_settings, "gtatools_radar_output", text=T("Папка"))
        col = layout.column(align=True)
        col.prop(scn.inu_settings, "gtatools_radar_grid", text=T("Сетка"))
        col.prop(scn.inu_settings, "gtatools_radar_size", text=T("Размер"))
        col.prop(scn.inu_settings, "gtatools_radar_height", text=T("Высота"))

        layout.separator()

        # All 5 generation modes live in a single dropdown — the
        # «Индексы» field above stays visible because Specific mode
        # reads it as input.
        layout.prop(scn.inu_settings, "gtatools_radar_specific", text=T("Индексы"))
        layout.menu("GTATOOLS_MT_radar_generate",
                    text=T("Генерировать"), icon=safe_icon('RENDER_RESULT'))

        layout.separator()
        layout.operator("gtatools.radar_pack_txd", text=T("Упаковать в TXD"), icon=safe_icon('PACKAGE'))



@apply_order
class GTATOOLS_PT_paths_panel(bpy.types.Panel):
    """Панель Path IO"""
    bl_label = "Пути"
    bl_idname = "GTATOOLS_PT_paths_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "GTATOOLS_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="", icon=safe_icon('TRACKING'))

    def draw(self, context):
        layout = self.layout

        # Convert to path button (top)
        obj = context.active_object
        if obj and (obj.type == 'CURVE' or (obj.type == 'MESH' and len(obj.data.polygons) == 0)):
            if obj.get('path_type') != 'path_ipl':
                layout.operator("gtatools.convert_to_path", text=T("Конвертировать в путь"), icon=safe_icon('CURVE_PATH'))

        # Paths IPL (main — for gta.dat)
        box = layout.box()
        box.label(text=T("Пути (paths.ipl):"), icon=safe_icon('TRACKING'))
        row = box.row(align=True)
        row.operator("gtatools.import_paths_ipl", text=T("Импорт"), icon=safe_icon('IMPORT'))
        row.operator("gtatools.export_paths_ipl", text=T("Экспорт"), icon=safe_icon('EXPORT'))
        box.operator("gtatools.add_path_ipl", text=T("Создать путь"), icon=safe_icon('ADD'))
        # Roadblocks / Traffic Lights — visible only in Edit Curve on path_ipl
        if (obj and obj.type == 'CURVE' and obj.get('path_type') == 'path_ipl'
                and context.mode == 'EDIT_CURVE'):
            sub = box.column(align=True)
            sub.label(text=T("Флаги выделенных точек:"), icon=safe_icon('CONSTRAINT'))
            op = sub.operator("gtatools.path_node_flag",
                              text=T("Переключить Roadblock"))
            op.action = 'TOGGLE_ROADBLOCK'
            sub.menu("GTATOOLS_MT_path_traffic",
                     text=T("Светофор"), icon=safe_icon('LIGHT'))

        layout.separator()

        # Train tracks
        box = layout.box()
        box.label(text=T("Ж/д пути:"), icon=safe_icon('CON_FOLLOWPATH'))
        row = box.row(align=True)
        row.operator("gtatools.import_track", text=T("Импорт"), icon=safe_icon('IMPORT'))
        row.operator("gtatools.export_track", text=T("Экспорт"), icon=safe_icon('EXPORT'))
        box.operator("gtatools.add_track", text=T("Создать ж/д путь"), icon=safe_icon('ADD'))
        obj = context.active_object
        if (obj and obj.type == 'CURVE' and obj.get('path_type') == 'track'
                and context.mode == 'EDIT_CURVE'):
            box.operator("gtatools.mark_station", text=T("Станция (вкл/выкл)"), icon=safe_icon('DECORATE_KEYFRAME'))
        # Station markers refresh — works in object mode too
        if obj and obj.type == 'CURVE' and obj.get('path_type') == 'track':
            box.operator("gtatools.refresh_station_markers",
                         text=T("Обновить маркеры станций"),
                         icon=safe_icon('EMPTY_SINGLE_ARROW'))

        layout.separator()

        # Compiled nodes (NODES*.DAT)
        box = layout.box()
        box.label(text=T("Скомпилированные (NODES):"), icon=safe_icon('FILE_CACHE'))
        row = box.row(align=True)
        row.operator("gtatools.import_nodes", text=T("Импорт"), icon=safe_icon('IMPORT'))
        row.operator("gtatools.export_nodes", text=T("Экспорт"), icon=safe_icon('EXPORT'))
        # Visualization toggle — turns Skin modifier off on all path
        # meshes so heavy maps don't lag the viewport. Mesh data (verts
        # + link arrays) survives; only the generated tube geometry
        # is hidden.
        box.operator("gtatools.toggle_nodes_viz",
                     text=T("Геометрия путей"),
                     icon=safe_icon('MODIFIER'))

        # Info about selected path object
        obj = context.active_object
        if obj and 'path_type' in obj:
            layout.separator()
            box = layout.box()
            pt = obj.get('path_type', '')
            type_names = {
                'track': T("Ж/д путь"),
                'path_ipl': T("Путь IPL"),
                'nodes_vehicle': T("Авто пути"),
                'nodes_ped': T("Пешеходные пути"),
                'nodes_navi': T("Навигационные точки"),
            }
            label = type_names.get(pt, pt)
            if pt == 'path_ipl':
                gt = obj.get('group_type', 1)
                gt_label = T("Авто") if gt == 1 else T("Пешеходный")
                count = sum(len(s.points) for s in obj.data.splines)
                box.label(text=f"{obj.name}: {gt_label} ({count}/12 pts)", icon=safe_icon('INFO'))
            elif obj.type == 'CURVE':
                count = sum(len(s.points) for s in obj.data.splines)
                stations = obj.get('station_indices', '[]')
                try:
                    num_st = len(ast.literal_eval(stations))
                except Exception:
                    num_st = 0
                box.label(text=f"{obj.name}: {label} ({count} pts, {num_st} stations)", icon=safe_icon('INFO'))
            elif obj.type == 'MESH':
                box.label(text=f"{obj.name}: {label} ({len(obj.data.vertices)} nodes)", icon=safe_icon('INFO'))


# ── Vertex Paint mode panel gating ─────────────────────────────────
# При входе в Vertex Paint mode от пользователя ожидается только
# работа с цветом — все панели кроме «Освещение» (и его sub-panel'ов)
# скрываются. Sub-panel'ы наследуют видимость от родителя автоматически
# (если parent.poll → False, sub-panel не показывается), поэтому гейтить
# нужно только top-level не-light панели.

def _gate_vertex_paint_panel(cls):
    """Wrap class's poll() to return False when context.mode == 'PAINT_VERTEX'."""
    existing_poll = cls.__dict__.get('poll')

    @classmethod
    def poll(klass, context):
        try:
            if context.mode == 'PAINT_VERTEX':
                return False
        except AttributeError:
            pass
        if existing_poll is not None:
            return existing_poll.__func__(klass, context)
        return True

    cls.poll = poll
    return cls


# NOTE: GTATOOLS_PT_main_panel — top-level container N-sidebar, у него
# bl_parent_id отсутствует. Все остальные панели (включая light_master)
# — его дети. Гейтить main_panel НЕЛЬЗЯ — спрячется вся вкладка
# аддона. Гейтим только конкретные top-level-в-логике дочерние панели,
# оставляя light_master невредимым.
_VPAINT_HIDDEN_PANELS = [
    GTATOOLS_PT_material_panel,
    GTATOOLS_PT_ide_ipl_panel,
    GTATOOLS_PT_export_panel,
    GTATOOLS_PT_validate_scene,
    GTATOOLS_PT_check_panel,
    GTATOOLS_PT_vehicle_panel,
    GTATOOLS_PT_frame_hierarchy,
    GTATOOLS_PT_2dfx_panel,
    GTATOOLS_PT_object_ide_ipl_panel,
    GTATOOLS_PT_id_manager_panel,
    GTATOOLS_PT_water_panel,
    GTATOOLS_PT_anim_panel,
    GTATOOLS_PT_radar_panel,
    GTATOOLS_PT_paths_panel,
]

# Панели в других модулях добавляем lazy чтобы не плодить
# циркулярные импорты на module-load.
try:
    from ..tools.bitmaps_manager import GTATOOLS_PT_bitmaps_panel as _bp
    _VPAINT_HIDDEN_PANELS.append(_bp)
except Exception:
    pass

for _cls in _VPAINT_HIDDEN_PANELS:
    _gate_vertex_paint_panel(_cls)


classes = (
    GTATOOLS_PT_material_panel,
    GTATOOLS_UL_txd_export_plan,
    GTATOOLS_UL_img_files,
    GTATOOLS_MT_create_2dfx,
    GTATOOLS_MT_radar_generate,
    GTATOOLS_MT_path_traffic,
    GTATOOLS_PT_main_panel,
    GTATOOLS_PT_ide_ipl_panel,
    GTATOOLS_PT_export_panel,
    GTATOOLS_PT_check_panel,
    GTATOOLS_PT_vehicle_panel,
    GTATOOLS_PT_frame_hierarchy,
    GTATOOLS_PT_2dfx_panel,
    GTATOOLS_PT_object_ide_ipl_panel,
    GTATOOLS_PT_object_inu_tools,
    GTATOOLS_PT_inu_tools_panel,
    GTATOOLS_PT_id_manager_panel,
    GTATOOLS_PT_light_master,
    GTATOOLS_PT_prelight_panel,
    GTATOOLS_PT_bake_settings_subpanel,
    GTATOOLS_PT_scatter_color_subpanel,
    GTATOOLS_PT_vc_postprocess_panel,
    GTATOOLS_PT_itera_panel,
    GTATOOLS_PT_prelight_col_panel,
    GTATOOLS_PT_vertex_paint_panel,
    GTATOOLS_PT_lightmap_panel,
    GTATOOLS_PT_water_panel,
    GTATOOLS_PT_anim_panel,
    GTATOOLS_PT_radar_panel,
    GTATOOLS_PT_paths_panel,
)
