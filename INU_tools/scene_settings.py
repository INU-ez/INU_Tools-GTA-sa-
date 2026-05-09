# INU_tools.scene_settings
#
# Consolidated PropertyGroup for all Scene-level settings — registered
# in __init__.py as ``bpy.types.Scene.inu_settings``.
#
# Per Blender extensions ToS, the addon's ``register()`` should declare
# Scene properties via a single PropertyGroup, not 131 separate
# ``bpy.types.Scene.X = ...`` calls. All legacy field names keep the
# ``gtatools_`` prefix verbatim so the load_post migration handler in
# __init__.py can copy values from old scenes byte-for-byte.

import bpy
from bpy.props import (
    StringProperty, BoolProperty, IntProperty, FloatProperty,
    EnumProperty, FloatVectorProperty, CollectionProperty,
)


# ── Update callbacks ────────────────────────────────────────────────
# All callbacks live at module level so they're picklable and can be
# referenced both from `update=` and `items=` parameters below. Most
# delegate to helpers defined in __init__.py via lazy imports — this
# breaks the circular dependency that would arise from importing the
# scene_settings module BEFORE __init__.py finishes loading.


def _save_paths_proxy(self, context):
    from . import _save_paths
    _save_paths(self, context)


def _col_light_invalidate_preview_proxy(self, context):
    from . import _col_light_invalidate_preview
    _col_light_invalidate_preview(self, context)


def _get_map_region_items_proxy(self, context):
    from . import _get_map_region_items
    return _get_map_region_items(self, context)


def _get_id_preset_items_proxy(self, context):
    from . import _get_id_preset_items
    return _get_id_preset_items(self, context)


def _id_preset_update_proxy(self, context):
    from . import _id_preset_update
    _id_preset_update(self, context)


def _upd_suffix_dff_proxy(self, context):
    from . import _upd_suffix_dff
    _upd_suffix_dff(self, context)


def _upd_suffix_lod_proxy(self, context):
    from . import _upd_suffix_lod
    _upd_suffix_lod(self, context)


def _upd_suffix_col_proxy(self, context):
    from . import _upd_suffix_col
    _upd_suffix_col(self, context)


def _upd_prefix_dff_proxy(self, context):
    from . import _upd_prefix_dff
    _upd_prefix_dff(self, context)


def _upd_prefix_lod_proxy(self, context):
    from . import _upd_prefix_lod
    _upd_prefix_lod(self, context)


def _upd_prefix_col_proxy(self, context):
    from . import _upd_prefix_col
    _upd_prefix_col(self, context)


def _get_preset_items_proxy(self, context):
    from . import _get_preset_items
    return _get_preset_items(self, context)


def _on_profile_changed_proxy(self, context):
    from .tools.profiles import _on_profile_changed
    _on_profile_changed(self, context)


def _profile_enum_items_proxy(self, context):
    from .tools.profiles import profile_enum_items
    return profile_enum_items(self, context)


def _mat_preset_items_proxy(self, context):
    from .tools.gta_material_panel import preset_items
    return preset_items(self, context)


def _ik_empty_types_proxy(self, context):
    from .ops.ik_rig import EMPTY_TYPES
    return EMPTY_TYPES


def _update_particle_sim(self, context):
    from .ops import particle_sim
    if self.gtatools_particle_sim:
        particle_sim.start_simulation()
    else:
        particle_sim.stop_simulation()


def _update_uv_grid(self, context):
    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            area.tag_redraw()


def _on_modulate_preview_update(self, context):
    from .tools.prelight import apply_modulate_preview
    apply_modulate_preview(context.scene)


def _ifp_action_changed(self, context):
    try:
        from .ops.ifp_import import preview_is_active, preview_start
    except Exception:
        return
    if not preview_is_active():
        return
    arm = context.active_object
    if not arm or arm.type != 'ARMATURE':
        return
    name = self.gtatools_ifp_action
    if not name:
        return
    preview_start(arm, name)


def _on_ik_color_change(self, context):
    rgb = tuple(self.gtatools_ik_color)[:3]
    for arm in bpy.data.objects:
        if arm.type != 'ARMATURE' or not arm.get('inu_ik_rigged'):
            continue
        for pb in arm.pose.bones:
            db = arm.data.bones.get(pb.name)
            if db is None or not db.get('inu_ik_control'):
                continue
            try:
                pb.color.palette = 'CUSTOM'
                pb.color.custom.normal = rgb
                pb.color.custom.select = rgb
                pb.color.custom.active = rgb
            except Exception:
                pass


def _on_floor_offset_change(self, context):
    for arm in bpy.data.objects:
        if arm.type != 'ARMATURE' or not arm.get('inu_ik_rigged'):
            continue
        for pb in arm.pose.bones:
            for c in pb.constraints:
                if (c.type == 'FLOOR'
                        and c.name.startswith('INU_IK_')):
                    c.offset = float(self.gtatools_floor_offset)


def _on_chain_offset_change(self, context):
    offset = tuple(self.gtatools_ik_chain_offset)
    for arm in bpy.data.objects:
        if arm.type != 'ARMATURE' or not arm.get('inu_ik_rigged'):
            continue
        for pb in arm.pose.bones:
            db = arm.data.bones.get(pb.name)
            if db is None or not db.get('inu_ik_control'):
                continue
            ct = db.get('inu_ik_ctrl_type')
            if ct != 'chain':
                continue
            try:
                pb.custom_shape_translation = offset
            except Exception:
                pass


_IK_BASE_SIZES = {
    'chain': 0.08, 'head': 0.08, 'rot': 0.08,
    'pole':  0.04, 'root': 0.16,
}


def _derive_ik_type(name):
    if not name.startswith('INU_IK_'):
        return None
    if name.endswith('_pole'):
        return 'pole'
    suffix = name[len('INU_IK_'):]
    if suffix in {'R_arm', 'L_arm', 'R_leg', 'L_leg'}:
        return 'chain'
    if suffix == 'root':
        return 'root'
    return 'rot'


def _ctrl_type_of(db):
    return db.get('inu_ik_ctrl_type') or _derive_ik_type(db.name)


def _on_ik_size_change(self, context):
    mult = float(self.gtatools_ik_size)
    for arm in bpy.data.objects:
        if arm.type != 'ARMATURE' or not arm.get('inu_ik_rigged'):
            continue
        for pb in arm.pose.bones:
            db = arm.data.bones.get(pb.name)
            if db is None or not db.get('inu_ik_control'):
                continue
            ct = _ctrl_type_of(db) or 'chain'
            base = _IK_BASE_SIZES.get(ct, 0.08)
            size = base * mult
            try:
                pb.custom_shape_scale_xyz = (size, size, size)
            except Exception:
                pass


_IK_TYPE_TO_COLL = {
    'chain': 'INU_IK_Chain',
    'pole':  'INU_IK_Pole',
    'rot':   'INU_IK_Rot',
    'head':  'INU_IK_Rot',
    'root':  'INU_IK_Root',
}


def _make_ik_visibility_setter(ctrl_types):
    def _setter(self, context):
        attr = ctrl_types[1]
        visible = bool(getattr(self, attr))
        type_set = ctrl_types[0]
        coll_names = {_IK_TYPE_TO_COLL[t] for t in type_set
                      if t in _IK_TYPE_TO_COLL}

        for arm in bpy.data.objects:
            if (arm.type != 'ARMATURE'
                    or not arm.get('inu_ik_rigged')):
                continue

            bone_colls = getattr(arm.data, 'collections', None)
            touched_via_collection = set()
            if bone_colls is not None:
                for cname in coll_names:
                    coll = bone_colls.get(cname)
                    if coll is None:
                        continue
                    coll.is_visible = visible
                    try:
                        for bone in coll.bones:
                            touched_via_collection.add(bone.name)
                    except Exception:
                        pass

            for db in arm.data.bones:
                if db.name in touched_via_collection:
                    continue
                if not db.get('inu_ik_control'):
                    continue
                if _ctrl_type_of(db) in type_set:
                    db.hide = not visible

            arm.data.update_tag()

        if context.area is not None:
            context.area.tag_redraw()
    return _setter


# ── CollectionProperty item types ─────────────────────────────────
#
# Defined here (not in their feature modules) so they can be referenced
# by ``CollectionProperty(type=...)`` fields inside INUSceneSettings
# without circular imports. Each remains a standalone PropertyGroup
# registered through the addon's classes-to-register list.


class INUValidateIssue(bpy.types.PropertyGroup):
    """One line in the Validate Scene panel. Backed by a Scene
    CollectionProperty so it survives between draws and across the
    Run → Goto/Fix interaction."""
    severity: StringProperty(default='WARNING')
    category: StringProperty(default='')
    message: StringProperty(default='')
    # Translation template + JSON-encoded args for interpolated
    # messages. When non-empty the panel does
    # ``T(template).format(**json.loads(args))`` so the user-facing
    # text follows the active locale. Empty when the message is
    # static and ``message`` itself is the displayed string.
    message_template: StringProperty(default='')
    message_args: StringProperty(default='')
    target_kind: StringProperty(default='')
    target_name: StringProperty(default='')
    fix_op_id: StringProperty(default='')
    fix_arg: StringProperty(default='')


class GTATOOLS_ImgFileEntry(bpy.types.PropertyGroup):
    """One file entry in IMG archive list."""
    name: StringProperty()


class GTATOOLS_BinaryIplEntry(bpy.types.PropertyGroup):
    """One binary IPL file found inside an IMG archive — user-selectable
    for inclusion in Build Map / Import Map."""
    name: StringProperty()
    enabled: BoolProperty(name="", default=True)
    img_source: StringProperty()


class GTATOOLS_LintIssueItem(bpy.types.PropertyGroup):
    """One row in the binary file scanner UIList. Mirrors core/file_lint.LintIssue.

    Lives on WindowManager (transient — results don't pollute .blend).
    """
    severity: StringProperty(default='ERROR')   # ERROR / WARN / INFO
    code: StringProperty(default='')            # stable key
    file: StringProperty(default='')            # absolute path
    where: StringProperty(default='')           # 'model[1].sphere[7]'
    message: StringProperty(default='')


# ── PropertyGroup ─────────────────────────────────────────────────


class INUSceneSettings(bpy.types.PropertyGroup):
    """All Scene-level INU Tools settings.

    Registered as ``bpy.types.Scene.inu_settings``. Field names keep
    their legacy ``gtatools_`` prefix to make the load_post migration
    a 1:1 attribute copy.
    """

    # ── Lightmap & validation ───────────────────────────────────
    gtatools_lightmap_result: StringProperty(name="Result", default="")
    gtatools_lightmap_path: StringProperty(name="Lightmap Path", default="lightmaps/lightmap.png")

    # inu_validate_issues uses a separate registered class — registered
    # in __init__.py at the bpy.types.Scene level since it predates this
    # consolidation and CollectionProperty(type=...) needs the class
    # registered first. Kept on Scene directly for now.

    # ── Particle 2DFX panel collapsibles ────────────────────────
    gtatools_pfx_exp_texture: BoolProperty(default=False)
    gtatools_pfx_exp_color: BoolProperty(default=False)
    gtatools_pfx_exp_size: BoolProperty(default=False)
    gtatools_pfx_exp_emission: BoolProperty(default=False)
    gtatools_pfx_exp_physics: BoolProperty(default=False)
    gtatools_pfx_exp_system: BoolProperty(default=False)
    gtatools_pfx_exp_curves: BoolProperty(default=False)

    gtatools_particle_sim: BoolProperty(
        name="Particle Simulation",
        description="Анимировать 2DFX частицы в viewport",
        default=False,
        update=_update_particle_sim,
    )
    gtatools_model_id: StringProperty(name="Model ID", default="0")
    gtatools_vc_analysis: StringProperty(name="VC Analysis", default="")

    # ── UV Grid Randomizer ──────────────────────────────────────
    gtatools_uv_grid_cols: IntProperty(
        name="Columns",
        description="Количество колонок в сетке текстуры",
        default=3, min=1, max=16,
        update=_update_uv_grid,
    )
    gtatools_uv_grid_rows: IntProperty(
        name="Rows",
        description="Количество рядов в сетке текстуры",
        default=2, min=1, max=16,
        update=_update_uv_grid,
    )
    gtatools_uv_grid_align: EnumProperty(
        name="Alignment",
        description="Позиция UV в ячейке",
        items=[
            ('CENTER', "Center", "Center of cell"),
            ('TOP_LEFT', "Top Left", "Top left corner"),
            ('TOP_CENTER', "Top", "Top center"),
            ('TOP_RIGHT', "Top Right", "Top right corner"),
            ('LEFT_CENTER', "Left", "Left center"),
            ('RIGHT_CENTER', "Right", "Right center"),
            ('BOTTOM_LEFT', "Bottom Left", "Bottom left corner"),
            ('BOTTOM_CENTER', "Bottom", "Bottom center"),
            ('BOTTOM_RIGHT', "Bottom Right", "Bottom right corner"),
        ],
        default='CENTER',
    )
    gtatools_uv_link_islands: BoolProperty(
        name="Link Polygons",
        description="Полигоны с пересекающимися UV перемещаются вместе",
        default=False,
    )

    # ── COL Light ───────────────────────────────────────────────
    gtatools_col_day_min: IntProperty(
        name="Day Min", description="Минимальное значение дневного света (тень)",
        default=10, min=0, max=15)
    gtatools_col_day_max: IntProperty(
        name="Day Max", description="Максимальное значение дневного света (свет)",
        default=15, min=0, max=15)
    gtatools_col_night_min: IntProperty(
        name="Night Min", description="Минимальное значение ночного света (тень)",
        default=0, min=0, max=15,
        update=_col_light_invalidate_preview_proxy)
    gtatools_col_night_max: IntProperty(
        name="Night Max", description="Максимальное значение ночного света (свет)",
        default=5, min=0, max=15,
        update=_col_light_invalidate_preview_proxy)
    gtatools_col_light_edge: FloatProperty(
        name="Edge",
        description="Сдвиг границы COL освещения",
        default=0.0, min=-5.0, max=5.0, soft_min=-1.0, soft_max=1.0, step=1,
        update=_col_light_invalidate_preview_proxy)
    gtatools_col_light_threshold: IntProperty(
        name="Threshold",
        description="Порог яркости",
        default=0, min=0, max=100,
        update=_col_light_invalidate_preview_proxy)
    gtatools_col_light_contrast: FloatProperty(
        name="Contrast",
        description="Контраст",
        default=0.0, min=0.0, max=5.0, soft_min=0.0, soft_max=1.0, step=1,
        update=_col_light_invalidate_preview_proxy)
    gtatools_col_light_font_size: IntProperty(
        name="Font Size",
        description="Размер цифр на полигонах",
        default=13, min=6, max=36,
        update=_col_light_invalidate_preview_proxy)
    gtatools_col_light_show_numbers: BoolProperty(
        name="Show Numbers",
        description="Показать цифры на полигонах",
        default=True)

    # ── Map / IMG / Paths ───────────────────────────────────────
    gtatools_img_path: StringProperty(
        name="IMG Archive",
        description="Путь к .img архиву GTA SA для экспорта моделей",
        default="", subtype='FILE_PATH',
        update=_save_paths_proxy)
    gtatools_map_region: EnumProperty(
        name="Region",
        description="Район карты для импорта",
        items=_get_map_region_items_proxy)
    gtatools_profile_enabled: BoolProperty(
        name="Профайлер",
        description="Замерять время операций",
        default=False)
    gtatools_show_binary_ipls: BoolProperty(
        name="Show binary IPLs",
        description="Развернуть список бинарных IPL для галочек",
        default=False)
    gtatools_map_skip_2dfx: BoolProperty(
        name="Skip 2DFX",
        description="Не импортировать 2DFX-эффекты при импорте",
        default=True)
    gtatools_img_use_gta_dat: BoolProperty(
        name="Use gta.dat",
        description="Искать все IDE/IPL через gta.dat",
        default=False)
    gtatools_img_skip_lod: BoolProperty(
        name="Skip LOD",
        description="Пропустить LOD модели при импорте",
        default=True)
    gtatools_img_load_txd: BoolProperty(
        name="Load TXD",
        description="Загружать TXD текстуры вместе с DFF",
        default=False)
    gtatools_map_load_col: BoolProperty(
        name="Load COL",
        description="Загружать коллизии из кеша при импорте карты",
        default=False)
    gtatools_map_group_by_ipl: BoolProperty(
        name="Group by IPL",
        description="Создавать отдельную коллекцию на каждый IPL-файл",
        default=True)
    gtatools_game_root: StringProperty(
        name="Game Root",
        description="Корневая папка GTA SA",
        default="", subtype='DIR_PATH',
        update=_save_paths_proxy)
    gtatools_ide_path: StringProperty(
        name="IDE File",
        description="Путь к IDE файлу GTA SA",
        default="", subtype='FILE_PATH',
        update=_save_paths_proxy)
    gtatools_ipl_path: StringProperty(
        name="IPL File",
        description="Путь к IPL файлу GTA SA",
        default="", subtype='FILE_PATH',
        update=_save_paths_proxy)

    # ── TXD settings ────────────────────────────────────────────
    gtatools_txd_auto_import: BoolProperty(
        name="Import TXD",
        description="Автоимпорт TXD текстур при импорте DFF",
        default=True)
    gtatools_shared_txd_name: StringProperty(
        name="Shared TXD Name",
        description="Имя общего TXD файла",
        default="")
    gtatools_txd_import_path: StringProperty(
        name="TXD Import Folder",
        description="Папка для поиска TXD при импорте DFF",
        default="", subtype='DIR_PATH')

    # ── Asset Library Builder ───────────────────────────────────
    # Settings for the operator that turns the .inu_cache contents into
    # a portable Blender Asset Library (one .blend per category, with
    # thumbnails + IDE metadata embedded on every asset).
    gtatools_library_output_path: StringProperty(
        name="Library Output",
        description="Папка куда писать собранную Asset Library "
                    "(13 .blend файлов + blender_assets.cats.txt + textures/)",
        default="", subtype='DIR_PATH')
    gtatools_library_no_preview: BoolProperty(
        name="Без превью",
        description="Не рендерить превьюшки. В ~3× быстрее, но Asset Browser "
                    "показывает заглушки вместо миниатюр",
        default=False)
    gtatools_library_preview_size: IntProperty(
        name="Размер превью",
        description="Размер превьюшек в пикселях. 128 — стандарт Blender, "
                    "256 крупнее но в 4× медленнее на рендере",
        default=128, min=64, max=512)
    gtatools_library_skip_existing: BoolProperty(
        name="Пропускать готовые",
        description="Пропускать категории чьи .blend уже существуют в Output. "
                    "Удобно при инкрементальном добавлении новых моделей "
                    "после установки модов",
        default=True)
    gtatools_library_delete_cache: BoolProperty(
        name="Удалить кеш после сборки",
        description="После успешной сборки библиотеки удалить папку "
                    ".inu_cache/ (DFF, COL, исходные PNG). Освобождает "
                    "много места на диске. Текстуры в самой библиотеке "
                    "остаются — при включённой галочке они принудительно "
                    "копируются в библиотеку (не симлинком). Будь готов "
                    "что Import Map после этого потребует повторно "
                    "«Извлечь ресурсы»",
        default=False)
    # Дополнительные категории при региональной сборке. Когда Map Region
    # ≠ ALL, по умолчанию строится только regional + GENERIC + LOD.
    # Чекбоксы ниже позволяют опционально докинуть универсальные группы.
    # При region == ALL — игнорируются (всё равно строится всё).
    gtatools_library_include_vehicles: BoolProperty(
        name="Vehicles",
        description="Включить в сборку машины/мотоциклы/лодки/самолёты. "
                    "Имеет смысл только при выбранном регионе — при ALL "
                    "категория всё равно строится",
        default=False)
    gtatools_library_include_peds: BoolProperty(
        name="Peds",
        description="Включить в сборку модели NPC / игрока. "
                    "Имеет смысл только при выбранном регионе",
        default=False)
    gtatools_library_include_weapons: BoolProperty(
        name="Weapons",
        description="Включить в сборку модели оружия. "
                    "Имеет смысл только при выбранном регионе",
        default=False)
    gtatools_library_include_interiors: BoolProperty(
        name="Interiors",
        description="Включить в сборку Interior-объекты (data/maps/interior). "
                    "Имеет смысл только при выбранном регионе",
        default=False)
    gtatools_dxt_backend: EnumProperty(
        name="DXT",
        description=(
            "Бэкенд сжатия DXT-текстур.\n"
            "Pure numpy, без NVTT и внешних бинарей — соответствует требованиям\n"
            "extensions.blender.org. Поверх любого бэкенда работает кэш по\n"
            "session_uid: повторный экспорт без правок текстур почти мгновенный."
        ),
        items=[
            ('numpy', "Numpy",
             "Рекомендуемый режим для финального экспорта в IMG.\n"
             "Range-fit на mip 0 (главный уровень детализации) + bbox-int\n"
             "на меньших мипах. Лучшее качество — на уровне NVTT2 «fast».\n"
             "Скорость: ~0.5с на 54 текстурах (1024²). В ~7× быстрее старого\n"
             "NVTT-пути. Бери его, если не уверен какой выбрать"),
            ('numpy_fast', "Numpy fast",
             "Для массовых тестовых прогонов и итеративной работы над\n"
             "геометрией, когда пиксельное качество не критично.\n"
             "Bbox-int на всех мипах, ~1.7× быстрее режима Numpy\n"
             "(~0.27с на тех же 54 текстурах).\n"
             "Качество: на типовых текстурах (бетон, кирпич, дороги) на глаз\n"
             "не отличается. На текстурах с резкими альфа-границами — заборы\n"
             "(a_fence_*), листва, проволока — могут быть видимые артефакты\n"
             "до −5 dB PSNR. Перед релизом переключи обратно на Numpy"),
            ('gpu', "GPU",
             "Work-in-progress. bpy.gpu compute shader через RGBA32F image-\n"
             "слот (в Blender 5.1 ещё нет публичного SSBO API). На практике\n"
             "не даёт выигрыша: readback Buffer'а упирается в Python GIL и\n"
             "выходит медленнее обоих CPU-режимов. Оставлено как задел —\n"
             "оживёт когда в Blender добавят GPUStorageBuf. Сейчас используй\n"
             "Numpy или Numpy fast"),
        ],
        default='numpy')

    # ── UI section toggles ──────────────────────────────────────
    gtatools_show_texture_settings: BoolProperty(
        name="Show Texture Settings", default=False)
    gtatools_show_paths_settings: BoolProperty(
        name="Show Paths Settings", default=False)
    gtatools_show_suffix_settings: BoolProperty(
        name="Show Suffix Settings", default=False)
    gtatools_show_dff_flags: BoolProperty(
        name="Show DFF Flags", default=False)
    gtatools_2dfx_show_props: BoolProperty(
        name="Show 2DFX Light Props", default=False)
    gtatools_2dfx_show_behavior: BoolProperty(
        name="Show 2DFX Behavior", default=False)
    gtatools_2dfx_show_shadow: BoolProperty(
        name="Show 2DFX Shadow", default=False)
    gtatools_2dfx_show_flags: BoolProperty(
        name="Show 2DFX Flags", default=False)

    gtatools_anim_tab: EnumProperty(
        name="Animation Tab",
        description="Раздел панели Анимации",
        items=[
            ('CHAR', "Персонажи", "IFP импорт/экспорт, IK Rig"),
            ('OBJ',  "Объекты",   "Animated Map Object"),
        ],
        default='CHAR')

    # ── Profile ─────────────────────────────────────────────────
    gtatools_profile: EnumProperty(
        name="Профиль",
        description="Какие панели показывать в N-sidebar",
        items=_profile_enum_items_proxy,
        update=_on_profile_changed_proxy)
    gtatools_profile_picked: StringProperty(
        name="Profile Picked Panel",
        default="")

    # ── IDE flags / suffixes / prefixes ─────────────────────────
    gtatools_show_ide_flags: BoolProperty(
        name="Show IDE Flags",
        description="Показать флаги IDE",
        default=False)
    gtatools_suffix_dff: StringProperty(
        name="DFF Suffix", default="_DFF",
        description="Суффикс для DFF моделей",
        update=_upd_suffix_dff_proxy)
    gtatools_suffix_lod: StringProperty(
        name="LOD Suffix", default="_LOD",
        description="Суффикс для LOD моделей",
        update=_upd_suffix_lod_proxy)
    gtatools_suffix_col: StringProperty(
        name="COL Suffix", default="_COL",
        description="Суффикс для COL моделей",
        update=_upd_suffix_col_proxy)
    gtatools_prefix_dff: StringProperty(
        name="DFF Prefix", default="",
        description="Префикс для DFF моделей",
        update=_upd_prefix_dff_proxy)
    gtatools_prefix_lod: StringProperty(
        name="LOD Prefix", default="",
        description="Префикс для LOD моделей",
        update=_upd_prefix_lod_proxy)
    gtatools_prefix_col: StringProperty(
        name="COL Prefix", default="",
        description="Префикс для COL моделей",
        update=_upd_prefix_col_proxy)

    # ── X Radar Maker ───────────────────────────────────────────
    gtatools_radar_output: StringProperty(
        name="Radar Output", subtype='DIR_PATH', default="",
        description="Папка для сохранения тайлов радара")
    gtatools_radar_grid: IntProperty(
        name="Radar Grid", default=8, min=1, max=16,
        description="Размер сетки (8 = 64 тайла)")
    gtatools_radar_size: IntProperty(
        name="Radar Tile Size", default=256, min=64, max=4096,
        description="Размер тайла в пикселях")
    gtatools_radar_height: FloatProperty(
        name="Radar Height", default=3000.0, min=100.0,
        description="Высота камеры")
    gtatools_radar_gamma: FloatProperty(
        name="Radar Gamma", default=1.0, min=0.1, max=5.0)
    gtatools_radar_specific: StringProperty(
        name="Radar Specific", default="",
        description="Индексы тайлов через запятую (0,1,5,63)")

    # ── IMG / ID Manager ───────────────────────────────────────
    gtatools_show_img_list: BoolProperty(
        name="Show IMG List", default=False)
    gtatools_img_entries_index: IntProperty(default=0)
    gtatools_show_id_manager: BoolProperty(
        name="Show ID Manager",
        description="Показать менеджер ID",
        default=False)
    gtatools_id_search: StringProperty(
        name="ID Search",
        description="Поиск по ID или имени модели",
        default="")
    gtatools_id_page: IntProperty(
        name="ID Page", default=0, min=0, soft_max=1000)
    gtatools_id_preset: EnumProperty(
        name="Пресет ID",
        description="Активный файл со списком ID",
        items=_get_id_preset_items_proxy,
        update=_id_preset_update_proxy)
    gtatools_id_show_service: BoolProperty(
        name="Показать сервисные кнопки",
        description="Развернуть редкие операции",
        default=False)

    # ── Texture loader ──────────────────────────────────────────
    gtatools_texture_path1: StringProperty(
        name="System Textures Path",
        description="Путь к папке с системными текстурами GTA",
        default="", subtype='DIR_PATH',
        update=_save_paths_proxy)
    gtatools_texture_path2: StringProperty(
        name="Blend Folder Path",
        description="Путь к папке где находится .blend файл",
        default="", subtype='DIR_PATH',
        update=_save_paths_proxy)

    # ── IK Rig ──────────────────────────────────────────────────
    gtatools_ik_display: EnumProperty(
        name="Форма IK-эмпти",
        description="Какой примитив рисовать на IK-target и pole",
        items=_ik_empty_types_proxy,
        default=0)
    gtatools_ik_color: FloatVectorProperty(
        name="Цвет IK-контроллов",
        description="Цвет всех IK-контрольных костей",
        subtype='COLOR', size=4, min=0.0, max=1.0,
        default=(0.2, 1.0, 0.2, 1.0),
        update=_on_ik_color_change)
    gtatools_floor_offset: FloatProperty(
        name="Коллизия",
        description="Высота виртуальной коллизии над плоскостью-полом",
        default=0.05, min=0.0, max=1.0, step=1, precision=3,
        subtype='DISTANCE',
        update=_on_floor_offset_change)
    gtatools_ik_extras_show: BoolProperty(
        name="Дополнительно",
        description="Настройки пола, коллизии, цвета IK",
        default=False)
    gtatools_ik_root_motion: BoolProperty(
        name="Root motion",
        description="Включить для анимаций которые двигают персонажа",
        default=False)
    gtatools_anim_tools_show: BoolProperty(
        name="Настройка анимации",
        description="Утилиты для исправления sign-discontinuities",
        default=False)
    gtatools_anim_fix_start: IntProperty(
        name="Старт",
        description="Первый кадр диапазона",
        default=0, min=0)
    gtatools_anim_fix_end: IntProperty(
        name="Конец",
        description="Последний кадр диапазона",
        default=10000, min=0)
    gtatools_ik_chain_offset: FloatVectorProperty(
        name="Смещение куба руки/ноги",
        description="Визуальный сдвиг кубов IK для рук и ног",
        size=3, subtype='TRANSLATION',
        default=(0.0, 0.0, 0.0), precision=3,
        update=_on_chain_offset_change)
    gtatools_ik_size: FloatProperty(
        name="Размер",
        description="Множитель размера всех IK-контролов",
        default=1.0, min=0.1, max=5.0, step=10, precision=2,
        update=_on_ik_size_change)
    gtatools_ik_show_chain: BoolProperty(
        name="Руки/ноги",
        description="Показывать кубы запястий и ступней",
        default=True,
        update=_make_ik_visibility_setter(
            (frozenset({'chain'}), 'gtatools_ik_show_chain')))
    gtatools_ik_show_pole: BoolProperty(
        name="Локти/колени",
        description="Показывать кубы-маркеры на локтях и коленях",
        default=True,
        update=_make_ik_visibility_setter(
            (frozenset({'pole'}), 'gtatools_ik_show_pole')))
    gtatools_ik_show_rot: BoolProperty(
        name="Голова/торс/плечи",
        description="Показывать кубы головы, верхнего торса и ключиц",
        default=True,
        update=_make_ik_visibility_setter(
            (frozenset({'rot', 'head'}), 'gtatools_ik_show_rot')))
    gtatools_ik_show_root: BoolProperty(
        name="Корень",
        description="Показывать корневой куб",
        default=True,
        update=_make_ik_visibility_setter(
            (frozenset({'root'}), 'gtatools_ik_show_root')))

    gtatools_ifp_action: StringProperty(
        name="IFP Action",
        description="Select IFP animation to apply",
        update=_ifp_action_changed)

    # ── Water ───────────────────────────────────────────────────
    gtatools_water_flag: EnumProperty(
        name="Water Type",
        description="Water polygon visibility and depth type",
        items=[
            ('0', "Обычная / Невидимая", "Глубокая вода, не отображается"),
            ('1', "Обычная / Видимая",   "Глубокая вода с волнами"),
            ('2', "Мелкая / Невидимая",  "Мелкая вода, не отображается"),
            ('3', "Мелкая / Видимая",    "Мелкая вода, отображается"),
        ],
        default='1')
    gtatools_water_speed_x: FloatProperty(
        name="Speed X", default=0.0, min=-5.0, max=5.0)
    gtatools_water_speed_y: FloatProperty(
        name="Speed Y", default=0.0, min=-5.0, max=5.0)
    gtatools_water_speed_z: FloatProperty(
        name="Speed Z", default=0.05, min=-5.0, max=5.0)
    gtatools_water_wave_height: FloatProperty(
        name="Wave Height", default=0.1, min=0.0, max=10.0)

    # ── Bake ────────────────────────────────────────────────────
    gtatools_bake_ambient: FloatProperty(
        name="Ambient",
        description="Базовый рассеянный свет",
        default=0.10, min=0.0, max=0.5)
    gtatools_bake_intensity: FloatProperty(
        name="Intensity",
        description="Множитель интенсивности света",
        default=0.05, min=0.0001, max=0.5)
    gtatools_bake_gamma: FloatProperty(
        name="Gamma",
        description="Гамма-коррекция",
        default=0.50, min=0.1, max=3.0)
    gtatools_bake_shadows: BoolProperty(
        name="Shadows",
        description="Включить тени при запекании",
        default=True)

    # ── Modulate Color preview ──────────────────────────────────
    gtatools_modulate_mode: EnumProperty(
        name="Modulate Color",
        description="Preview-режим",
        items=[
            ('OFF',   "Off",   "Без ambient — только prelight"),
            ('DAY',   "Day",   "EXTRASUNNY_LA Midday"),
            ('NIGHT', "Night", "EXTRASUNNY_LA Midnight"),
        ],
        default='OFF',
        update=_on_modulate_preview_update)
    gtatools_modulate_mix: FloatProperty(
        name="Прозрачность",
        description="Сколько ambient добавлять к prelight",
        default=0.002, min=0.0, max=1.0, precision=3,
        subtype='FACTOR',
        update=_on_modulate_preview_update)
    gtatools_modulate_contrast: FloatProperty(
        name="Контраст",
        description="Контраст финального изображения",
        default=0.0, min=-1.0, max=1.0,
        subtype='FACTOR',
        update=_on_modulate_preview_update)
    gtatools_modulate_gamma: FloatProperty(
        name="Гамма",
        description="Гамма финального изображения",
        default=0.8, min=0.1, max=4.0,
        update=_on_modulate_preview_update)

    # ── Prelight / VC processing ────────────────────────────────
    gtatools_prelight_preset: EnumProperty(
        name="Prelight Preset",
        items=_get_preset_items_proxy,
        description="Выбрать пресет настроек прелайта")
    gtatools_v_offset: FloatProperty(
        name="V Offset",
        description="Смещение яркости",
        default=0.0, min=-100.0, max=100.0)
    gtatools_vc_smooth_iterations: IntProperty(
        name="Iterations",
        description="Количество итераций сглаживания",
        default=1, min=1, max=50)
    gtatools_vc_smooth_factor: FloatProperty(
        name="Factor",
        description="Сила сглаживания",
        default=0.5, min=0.0, max=1.0)
    gtatools_vc_contrast: FloatProperty(
        name="Contrast",
        description="Контраст",
        default=1.0, min=0.0, max=3.0)
    gtatools_vc_brightness: FloatProperty(
        name="Brightness",
        description="Яркость смещение",
        default=0.0, min=-1.0, max=1.0)
    gtatools_vc_gamma: FloatProperty(
        name="Gamma",
        description="Гамма-коррекция",
        default=1.0, min=0.1, max=3.0)
    gtatools_fill_color: FloatVectorProperty(
        name="Fill Color",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0.0, max=1.0)
    gtatools_scatter_intensity: FloatProperty(
        name="Intensity",
        description="Интенсивность рассеивания света",
        default=1.0, min=0.1, max=5.0)
    gtatools_scatter_falloff: FloatProperty(
        name="Falloff",
        description="Скорость затухания света",
        default=1.5, min=0.5, max=5.0)
    gtatools_scatter_iterations: IntProperty(
        name="Iterations",
        description="Количество слоёв соседних граней",
        default=3, min=1, max=10)
    gtatools_scatter_radius: FloatProperty(
        name="Radius",
        description="Радиус поиска соседних граней",
        default=0.0)

    # Scatter Color — paints chosen color around selected polys with
    # linear distance falloff. Independent from Scatter Light (which
    # spreads existing prelight).
    gtatools_scatter_color_color: FloatVectorProperty(
        name="Цвет",
        description="Цвет, которым заливаются вершины вокруг выделенных полигонов",
        subtype='COLOR_GAMMA', size=3,
        default=(1.0, 1.0, 1.0), min=0.0, max=1.0)
    gtatools_scatter_color_strength: FloatProperty(
        name="Сила",
        description="Сила вклада цвета в центре. 0 — ничего не делать, 1 — полностью заменить vcols в центре на выбранный цвет",
        default=1.0, min=0.0, max=1.0, subtype='FACTOR')
    gtatools_scatter_color_distance: FloatProperty(
        name="Дальность",
        description="Радиус как доля половины bbox-диагонали меша. 0 — только выделенные вершины, 1 — расходится на половину диагонали",
        default=0.3, min=0.0, max=1.0, subtype='FACTOR')

    # ── Pipeline / Material preset ──────────────────────────────
    gtatools_export_pipeline: EnumProperty(
        items=[
            ('NONE', 'None', "Без pipeline"),
            ('0x53F2009A', 'Vehicle', "Pipeline кузова машины"),
            ('0x53F20098', 'Day/Night', "Pipeline здания с day/night vertex colors"),
            ('0x53F2009C', 'Building', "Простой pipeline здания"),
        ],
        name="Pipeline",
        description="Рендер-пайплайн для экспорта DFF",
        default='NONE')
    gtatools_material_preset: EnumProperty(
        items=_mat_preset_items_proxy,
        name="GTA Material Preset")

    # ── Export All ──────────────────────────────────────────────
    gtatools_export_all_dff: BoolProperty(
        name="Export DFF",
        description="Экспортировать DFF при Export All",
        default=True)
    gtatools_export_all_col: BoolProperty(
        name="Export COL",
        description="Экспортировать COL при Export All",
        default=True)
    gtatools_export_all_lod: BoolProperty(
        name="Export LOD",
        description="Экспортировать LOD при Export All",
        default=True)
    gtatools_export_all_txd: BoolProperty(
        name="Export TXD",
        description="Экспортировать TXD при Export All",
        default=True)
    gtatools_export_all_col_library: BoolProperty(
        name="COL Library",
        description="Писать все коллизии в один .col файл",
        default=False)
    gtatools_export_all_col_library_name: StringProperty(
        name="Имя library .col",
        description="Имя общего .col файла без расширения",
        default="collision")
    gtatools_export_all_txd_shared: BoolProperty(
        name="Shared TXD",
        description="Писать все текстуры в один общий .txd файл",
        default=False)
    gtatools_export_all_txd_shared_name: StringProperty(
        name="Имя общего .txd",
        description="Имя общего .txd файла без расширения",
        default="textures")

    # ── Misc ────────────────────────────────────────────────────
    gtatools_vc_layers_expanded: BoolProperty(
        name="VC Layers Section Expanded",
        default=False)

    # ── Binary file scanner (DFF / COL / TXD lint) ─────────────
    gtatools_scan_dir: StringProperty(
        name="Папка",
        description="Папка с DFF/COL/TXD для сканирования",
        subtype='DIR_PATH', default="")
    gtatools_scan_recursive: BoolProperty(
        name="Включая подпапки",
        description="Рекурсивный обход подпапок. По умолчанию выключено, чтобы случайно не просканировать всю систему",
        default=False)
    gtatools_scan_dff: BoolProperty(name="DFF", default=True)
    gtatools_scan_col: BoolProperty(name="COL", default=True)
    gtatools_scan_txd: BoolProperty(name="TXD", default=True)
    gtatools_scan_only_errors: BoolProperty(
        name="Только ERROR",
        description="Скрыть WARN/INFO в списке (фильтр draw, коллекция не пересоздаётся)",
        default=True)
    gtatools_scan_report_target: EnumProperty(
        name="Куда сохранять отчёт",
        items=[
            ('BLEND', "Рядом с .blend", "В папке текущей сцены (.blend должен быть сохранён)"),
            ('SCAN',  "В папке скана",   "Туда же, откуда брались файлы"),
            ('CUSTOM',"Своя папка",      "Указать вручную"),
        ],
        default='BLEND')
    gtatools_scan_report_custom_path: StringProperty(
        name="Папка для отчёта",
        subtype='DIR_PATH', default="")

    # ── CollectionProperty fields with custom item types ──────
    inu_validate_issues: CollectionProperty(type=INUValidateIssue)
    gtatools_binary_ipls: CollectionProperty(type=GTATOOLS_BinaryIplEntry)
    gtatools_img_entries: CollectionProperty(type=GTATOOLS_ImgFileEntry)
