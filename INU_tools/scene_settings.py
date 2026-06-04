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
    PointerProperty,
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


# Texture-bake map enum: ДИНАМИЧЕСКИЙ (ведётся tools.bake.BAKE_MAPS,
# который растёт по этапам). Кэшируем построенный список в module-global,
# чтобы строки пережили GC enum-items Blender'а (иначе метки кракозябрятся)
# — тот же приём, что у _profile_enum_items_proxy.
_bake_map_enum_cache = []


def _bake_map_enum_items_proxy(self, context):
    from .tools.bake import bake_map_enum_items
    global _bake_map_enum_cache
    # Английские имена карт как есть (без T) — карты не переводим.
    _bake_map_enum_cache = [(mid, label, desc)
                            for (mid, label, desc) in bake_map_enum_items()]
    return _bake_map_enum_cache


# Режимы смешивания композита — статичны (зеркало tools.bake.BLEND_MODES).
# Статичные items GC-безопасны, proxy/кэш не нужны.
_BAKE_BLEND_ITEMS = [
    ('NORMAL',   "Normal",   "Заменяет нижний слой"),
    ('MULTIPLY', "Multiply", "Умножение (затемнение) — AO / Shadow"),
    ('ADD',      "Add",      "Сложение (осветление)"),
    ('SCREEN',   "Screen",   "Экран (осветление)"),
    ('OVERLAY',  "Overlay",  "Перекрытие — контраст / износ кромок"),
]

# Разрешения — степени двойки. X/Y привязаны к этому списку (enum), а
# «Размер» — квадратный пресет, синхронящий оба через _bake_res_update.
_BAKE_POT_VALUES = (32, 64, 128, 256, 512, 1024, 2048, 4096, 8192)
_BAKE_POT_ITEMS = [(str(v), str(v), "") for v in _BAKE_POT_VALUES]


def _nearest_pot(v):
    return min(_BAKE_POT_VALUES, key=lambda p: abs(p - int(v)))


def _bake_res_update(self, context):
    # «Размер» — квадратный пресет: синхронит X и Y (числовые поля).
    v = int(self.gtatools_bake_resolution)
    self.gtatools_bake_res_x = v
    self.gtatools_bake_res_y = v


def _bake_res_x_update(self, context):
    snapped = _nearest_pot(self.gtatools_bake_res_x)
    if snapped != self.gtatools_bake_res_x:        # привязка к степени двойки
        self.gtatools_bake_res_x = snapped


def _bake_res_y_update(self, context):
    snapped = _nearest_pot(self.gtatools_bake_res_y)
    if snapped != self.gtatools_bake_res_y:
        self.gtatools_bake_res_y = snapped


def _bake_live_update(self, context):
    # Правка слоя (opacity/blend/enabled/карта) → пересобрать живой нодовый
    # композит на активном объекте (если он показан) → мгновенное превью.
    obj = getattr(context, 'active_object', None)
    if obj is None:
        return
    try:
        from .ops.bake_ops import rebuild_live_composite
        rebuild_live_composite(obj)
    except Exception:
        pass


def _bake_layer_index_update(self, context):
    # Клик по слою → показать его запечённую карту в Image-редакторе.
    obj = getattr(context, 'active_object', None)
    if obj is None:
        return
    base = obj.get("inu_bake_base", "")
    i = self.gtatools_bake_layers_index
    layers = self.gtatools_bake_layers
    if not base or not (0 <= i < len(layers)):
        return
    img = bpy.data.images.get(f"{base}_{layers[i].map_id}")
    if img is None:
        return
    try:
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.spaces.active.image = img
    except Exception:
        pass


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


def _inu_pipeline_changed_proxy(self, context):
    try:
        from . import _inu_pipeline_changed
        _inu_pipeline_changed(self, context)
    except Exception as e:
        # update-коллбэк не должен ронять остальной UI. Если что-то
        # пошло не так с per-pipeline snapshot logic — печатаем в
        # консоль и идём дальше, не мешая пайплайну сохраниться.
        print(f"[INU] pipeline-change snapshot failed: {e!r}")


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


class GTATOOLS_TextIplEntry(bpy.types.PropertyGroup):
    """One text IPL file (loose on disk via gta.dat, or inside an IMG)
    — parallel to GTATOOLS_BinaryIplEntry but for human-readable IPLs.

    ``name`` is the display label.  ``path`` holds either an absolute
    loose-file path (when ``img_source`` is empty) or the entry name
    within ``img_source`` IMG.
    """
    name: StringProperty()
    enabled: BoolProperty(name="", default=True)
    path: StringProperty()
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


class GTATOOLS_PathItem(bpy.types.PropertyGroup):
    """Single file-path entry — used by map analyzer's custom IDE/IPL
    lists. CollectionProperty of these gives the user an add/remove UI."""
    path: StringProperty(name="Path", subtype='FILE_PATH', default='')


class GTATOOLS_TextureBrowserItem(bpy.types.PropertyGroup):
    """One row in the Texture Browser UIList. Mirrors
    core/texture_index.TextureEntry. Lives on WindowManager
    (transient — index isn't saved with the .blend, user re-scans
    each session)."""
    archive_path: StringProperty(default='')
    txd_name: StringProperty(default='')
    texture_name: StringProperty(default='')
    width: IntProperty(default=0)
    height: IntProperty(default=0)
    depth: IntProperty(default=0)
    fourcc: IntProperty(default=0)
    num_levels: IntProperty(default=1)
    platform_id: IntProperty(default=8)
    format_label: StringProperty(default='')
    usage_count: IntProperty(default=0)    # IDE models referencing this TXD


class INUBakeLayer(bpy.types.PropertyGroup):
    """Один слой в стеке запекания текстур (tools/bake/). Поля
    contrast/gamma/influence_* объявлены сейчас с identity-дефолтами —
    композитор их УЖЕ читает, включение = только UI, без смены схемы.
    См. docs/BAKE_FEATURE_PLAN.md."""
    map_id: EnumProperty(
        name="Карта", description="Какую карту печь в этом слое",
        items=_bake_map_enum_items_proxy, update=_bake_live_update)
    enabled: BoolProperty(name="", default=True, update=_bake_live_update)
    blend_mode: EnumProperty(
        name="Режим", description="Как смешивать с нижними слоями",
        items=_BAKE_BLEND_ITEMS, default='MULTIPLY', update=_bake_live_update)
    opacity: FloatProperty(
        name="Прозрачность", default=1.0, min=0.0, max=1.0, subtype='FACTOR',
        update=_bake_live_update)
    # ── FUTURE (identity сейчас; композитор уже читает) ──
    contrast: FloatProperty(name="Контраст", default=1.0, min=0.0, max=4.0)
    gamma: FloatProperty(name="Гамма", default=1.0, min=0.05, max=4.0)
    influence_target: StringProperty(name="Влияние на", default='')
    influence_amount: FloatProperty(
        name="Сила влияния", default=1.0, min=0.0, max=1.0, subtype='FACTOR')


def _on_scene_animobj_pick(self, context):
    """Fires when the user picks a mesh via the scene-level animobj
    pipette. Delegates to ``attach_mesh_to_rig`` which auto-creates a
    rig on the first pick, then routes subsequent picks per the
    sibling ``gtatools_animobj_picker_target`` enum. Imports the
    helper lazily — scene_settings is imported very early and the
    operators module isn't ready yet at top-level."""
    mesh = self.gtatools_animobj_picker
    if mesh is None or mesh.type != 'MESH':
        return
    target = self.gtatools_animobj_picker_target
    try:
        from .ops.animobj_ops import attach_mesh_to_rig
        attach_mesh_to_rig(context, mesh, target=target)
    except Exception as ex:
        print(f"[INU] animobj pipette failed: {ex}")

    # Clear the picker via a deferred timer — update callbacks can't
    # safely mutate their own property in the same event cycle.
    settings = self
    def _clear():
        try:
            settings.gtatools_animobj_picker = None
        except Exception:
            pass
        return None
    try:
        bpy.app.timers.register(_clear, first_interval=0.01)
    except Exception:
        pass


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
    gtatools_show_text_ipls: BoolProperty(
        name="Show text IPLs",
        description="Развернуть список текстовых IPL для галочек",
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
    # Active game — drives version dispatch in DFF/COL/TXD/IDE/IPL/IMG
    # writers and lint thresholds. Default SA (the addon's historical
    # focus). III/VC are work-in-progress — readers/writers gradually
    # gaining version-aware code paths.
    gtatools_game: EnumProperty(
        name="Игра",
        description="Целевая игра для экспорта / валидации. Импорт авто-детектит игру по RW-версии",
        items=[
            ('SA',  "SA",  "GTA: San Andreas (RW 3.6, COL3, IMG VER2)"),
            ('VC',  "VC",  "GTA: Vice City (RW 3.5, COL2, IMG VER1)"),
            ('III', "III", "GTA III (RW 3.3, COL1, IMG VER1)"),
        ],
        default='SA')
    # Target platform — PC (vanilla RW geometry, D3D textures) vs
    # Mobile (Native Data PLG / OpenGL geometry, PVRTC/ETC1 textures).
    # Affects DFF reader/writer dispatch and export options. Импорт
    # авто-детектит платформу по наличию Native Data PLG чанков.
    gtatools_platform: EnumProperty(
        name="Платформа",
        description="Целевая платформа: PC (vanilla) или Mobile (iOS/Android, Native Data PLG)",
        items=[
            ('PC',     "PC",     "PC / Xbox / PS2 (vanilla RW geometry)"),
            ('MOBILE', "Mobile", "iOS / Android (Native Data PLG, War Drum OpenGL)"),
        ],
        default='PC')
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

    # ── «Проверка» panel toggle state ─────────────────────────────────
    # Persisted with the .blend so the panel reflects actual hidden /
    # links-active state after Blender restart. Previously lived as
    # module-level globals which reset on every addon (re)load.
    gtatools_hide_dff: BoolProperty(
        name="Hide DFF",
        description="Currently hiding DFF meshes via the «Проверка» toggle",
        default=False)
    gtatools_hide_lod: BoolProperty(
        name="Hide LOD",
        description="Currently hiding LOD meshes via the «Проверка» toggle",
        default=False)
    gtatools_hide_col: BoolProperty(
        name="Hide COL",
        description="Currently hiding COL meshes via the «Проверка» toggle",
        default=False)
    gtatools_hide_sha: BoolProperty(
        name="Hide SHA",
        description="Currently hiding shadow meshes via the «Проверка» toggle",
        default=False)
    gtatools_links_active: BoolProperty(
        name="Model links overlay",
        description="DFF↔LOD↔COL dashed-link viewport overlay enabled",
        default=False)

    gtatools_dxt_backend: EnumProperty(
        name="",
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

    # ── Animated Map Object — scene-level eyedropper ─────────────
    # Replaces the «Setup» button: user picks meshes one by one with
    # the pipette, and the rig is auto-created on the first pick.
    # update= lives in ops/animobj_ops.py (lazy-imported to dodge
    # the circular import that would happen at module load time).
    gtatools_animobj_picker_target: EnumProperty(
        name="Куда добавить",
        description=(
            "Куда привесить выбранный пипеткой меш:\n"
            "  Новый pivot — анимированная часть (своя ось/скорость)\n"
            "  К существующему pivot — на тот же pivot что и предыдущая\n"
            "  К root — статичная часть без анимации"),
        items=[
            ('NEW_PIVOT', "Новый pivot",
             "Создать новый pivot и привесить меш к нему — он будет крутиться отдельно"),
            ('PIVOT', "К существующему pivot",
             "На первый pivot — общая анимация с другими мешами под ним"),
            ('ROOT', "К root (статика)",
             "Статичная часть, не крутится"),
        ],
        default='NEW_PIVOT')
    gtatools_animobj_picker: PointerProperty(
        type=bpy.types.Object,
        name="Меш",
        description=(
            "Кликни на пипетку и выбери меш в сцене или 3D-окне. "
            "Если rig'а ещё нет — он создастся автоматически. "
            "После пика поле очищается — можно сразу подбирать следующий"),
        poll=lambda self, obj: obj is not None and obj.type == 'MESH',
        update=lambda self, context: _on_scene_animobj_pick(self, context))

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
    gtatools_show_preset_dir: BoolProperty(
        name="Show Preset Folder", default=False)
    gtatools_col_auto_light: BoolProperty(
        name="Auto COL Light",
        description=("Заполнять байт освещения коллизии у фейсов, где он "
                     "равен 0 (нет COL-материала / day+night не заданы). "
                     "Повторяет поведение Kam's CST-экспорта (light=78), "
                     "иначе коллизия в игре остаётся неосвещённой. "
                     "Заданные вручную и импортированные значения не "
                     "трогаются"),
        default=True)
    gtatools_col_auto_light_value: IntProperty(
        name="COL Light",
        description=("Значение байта освещения для незаполненных фейсов. "
                     "78 = день≈15 / ночь 4 (дефолт Kam). Упаковка: "
                     "день = младший ниббл, ночь = старший ниббл"),
        default=78, min=0, max=255)
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
    gtatools_smooth_axis_mode: EnumProperty(
        name="Smooth axis",
        description=("Ось вдоль которой сглаживать ключи между опорными. "
                     "ALL — все каналы в локальных координатах кости; "
                     "WORLD_X/Y/Z — только translation, в мировых "
                     "координатах (медленнее, but учитывает поворот родителей)"),
        items=[
            ('ALL', "All", "All channels (local)"),
            ('WORLD_X', "X", "World X (translation only)"),
            ('WORLD_Y', "Y", "World Y (translation only)"),
            ('WORLD_Z', "Z", "World Z (translation only)"),
        ],
        default='ALL')
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

    # ── Texture Bake (карты → текстура; tools/bake/) ────────────
    # Отдельная подсистема от vertex-prelight выше: печёт AO/Diffuse/
    # Shadow/Bevel через Cycles и опц. складывает в одну diffuse-текстуру.
    # Композит строится ВСЕГДА (живой нодовый стек) — тумблера нет.
    gtatools_bake_resolution: EnumProperty(
        name="Размер", description="Квадратный пресет размера (синхронит X/Y)",
        items=_BAKE_POT_ITEMS, default='1024', update=_bake_res_update)
    gtatools_bake_res_x: IntProperty(
        name="X", description="Ширина текстуры (привязка к степеням двойки)",
        default=1024, min=32, max=8192, update=_bake_res_x_update)
    gtatools_bake_res_y: IntProperty(
        name="Y", description="Высота текстуры (привязка к степеням двойки)",
        default=1024, min=32, max=8192, update=_bake_res_y_update)
    gtatools_bake_samples: IntProperty(
        name="Samples",
        description="Сэмплы Cycles для шумных карт (AO / свет)",
        default=16, min=1, max=512)
    gtatools_bake_margin: IntProperty(
        name="Margin", description="Залив за края UV-островов, px",
        default=8, min=0, max=64)
    # Имя выходной текстуры НЕ задаётся вручную — берётся из имени модели
    # (без префиксов/суффиксов _DFF/_LOD/_COL/hi/low) в ops/bake_ops.py.
    # Цель запекания = ВЫДЕЛЕННАЯ UV (mesh.uv_layers.active), источник =
    # рендер-UV (active_render, иконка 📷). Читаются прямо с меша — поэтому
    # отдельного поля для целевой UV нет (TexTools-подход).
    gtatools_bake_mode: EnumProperty(
        name="Режим",
        description="Что запекаем",
        items=[
            ('UV', "UV → UV",
             "Запечь сам объект: текстуры берутся с рендер-UV (источник), "
             "результат пишется в выделенную UV (цель). Для trim-развёрток"),
            ('HILOW', "Hi → Low",
             "Перенести деталь с хайполи на выделенный лоуполи (в разработке)"),
        ],
        default='UV')
    gtatools_bake_bevel_size: FloatProperty(
        name="Bevel радиус",
        description="Радиус скругления для Bevel-карты (в единицах сцены)",
        default=0.05, min=0.0, soft_max=1.0, precision=3)
    gtatools_bake_bevel_samples: IntProperty(
        name="Bevel samples", default=8, min=2, max=64)
    gtatools_bake_light_energy_scale: FloatProperty(
        name="Свет (экспозиция)",
        description="Множитель энергии внутреннего свет-рига для карт "
                    "Shadow / Diffuse-Lit. Больше — ярче",
        default=1.0, min=0.0, soft_max=4.0)
    # Hi→Low: суффиксы пар ФИКСИРОВАНЫ (_hi / _low, см. tools.bake.HI_SUFFIX)
    # — поля выбора убраны намеренно. Настраивается только cage.
    gtatools_bake_cage_extrusion: FloatProperty(
        name="Cage",
        description="Выдавливание cage (на сколько отодвинуть лучи от "
                    "лоуполи к хайполи)",
        default=0.1, min=0.0, soft_max=1.0, precision=3)
    gtatools_bake_max_ray: FloatProperty(
        name="Max Ray",
        description="Макс. дистанция луча (0 = авто)",
        default=0.0, min=0.0, soft_max=1.0, precision=3)
    gtatools_bake_show_advanced: BoolProperty(
        name="Дополнительно", default=False)
    gtatools_bake_layers_index: IntProperty(
        default=0, update=_bake_layer_index_update)

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
        description=(
            "Сглаживание vertex colors между соседними вершинами.\n"
            "Iterations — количество проходов.\n"
            "Больше проходов = плавнее переходы"),
        default=1, min=1, max=50)
    gtatools_vc_smooth_factor: FloatProperty(
        name="Factor",
        description=(
            "Сила сглаживания за один проход (0-1).\n"
            "0 — без эффекта, 1 — vertex берёт полное среднее соседей"),
        default=0.5, min=0.0, max=1.0)
    gtatools_vc_contrast: FloatProperty(
        name="Contrast",
        description=(
            "Контраст vertex colors.\n"
            "1.0 — без изменений\n"
            "< 1.0 — меньше контраст\n"
            "> 1.0 — больше контраст"),
        default=1.0, min=0.0, max=3.0)
    gtatools_vc_brightness: FloatProperty(
        name="Brightness",
        description=(
            "Яркость vertex colors (additive offset).\n"
            "0.0 — без изменений\n"
            "> 0 — светлее\n"
            "< 0 — темнее"),
        default=0.0, min=-1.0, max=1.0)
    gtatools_lift_shadows_strength: FloatProperty(
        name="Подтянуть тени",
        description=(
            "Подтягивает тёмные участки к самой яркой точке, "
            "сохраняя шаг между гранями.\n"
            "0 — без изменений\n"
            "0.3-0.5 — рекомендуемый диапазон\n"
            "1 — все цвета доходят до max (теряется визуальный шаг)"),
        default=0.5, min=0.0, max=1.0, subtype='FACTOR')
    gtatools_vc_gamma: FloatProperty(
        name="Gamma",
        description=(
            "Гамма-коррекция vertex colors.\n"
            "1.0 — без изменений\n"
            "< 1.0 — светлее (lift тени)\n"
            "> 1.0 — темнее (deepen тени)"),
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
            ('PED', 'Ped',
             "Preset для персонажа: pipeline ID = 0, SkinPLG обязателен, "
             "MatFX/day-night vcols отключены. Используется для экспорта "
             "скиннутых ped-моделей. На самом экспорте автоматически "
             "выставляет ped-friendly defaults: has_skin=True, "
             "day_cols=False, night_cols=False, matfx=False"),
        ],
        name="Pipeline",
        description="Рендер-пайплайн для экспорта DFF",
        default='NONE',
        update=_inu_pipeline_changed_proxy)
    # Last seen pipeline value — без этого update-коллбэк не знает
    # из какого слота сохранять. Hidden, не показывается юзеру.
    inu_prev_pipeline_internal: StringProperty(default='NONE', options={'HIDDEN'})

    # ── Graph editor: keyframe thinning ──
    gtatools_thin_keys_mode: EnumProperty(
        name="Режим прореживания",
        items=[
            ('NTH',  "Каждый N-ный", "Оставить каждый N-ный ключ"),
            ('AUTO', "Авто",          "Удалить избыточные (колинеарные) ключи"),
        ],
        default='NTH')
    gtatools_thin_keys_stride: IntProperty(
        name="N",
        description="Оставить каждый N-ный из выделенных (2 = удалить каждый второй)",
        default=2, min=2, max=20)
    gtatools_thin_keys_error: FloatProperty(
        name="Порог ошибки",
        description="Чем выше — тем агрессивнее срез избыточных ключей",
        default=0.01, min=0.0001, max=1.0, precision=4)
    gtatools_thin_keys_interp: EnumProperty(
        name="Интерполяция",
        items=[
            ('BEZIER',   "Безье",     "Плавная кривая между ключами"),
            ('LINEAR',   "Линейная",  "Прямые линии между ключами"),
            ('CONSTANT', "Постоянная", "Ступенька — без интерполяции"),
        ],
        default='BEZIER')
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

    # ── Analysis combined panel (file scanner + map analyzer) ──
    # Внутренний toggle между двумя режимами в одной sub-panel
    # «Анализ карты/файлов» внутри Check.
    gtatools_analysis_mode: EnumProperty(
        name="Режим",
        items=[
            ('FILES', "Файлы",  "Скан DFF/COL/TXD на диске"),
            ('MAP',   "Карта",  "Cross-reference IDE/IPL"),
        ],
        default='FILES')

    # ── Map Analyzer (cross-reference IDE/IPL) ──────────────────
    gtatools_map_analyzer_mode: EnumProperty(
        name="Источник",
        items=[
            ('DAT',    "DAT файл",   "gta.dat / default.dat / кастомный — следует за IDE/IPL/IMG строками"),
            ('FOLDER', "Папка",      "Сканировать все *.ide / *.ipl в указанной папке"),
            ('CUSTOM', "Свои пути",  "Ручной список IDE и IPL файлов"),
        ],
        default='FOLDER')
    gtatools_map_analyzer_dat_path: StringProperty(
        name=".dat файл",
        subtype='FILE_PATH', default="")
    gtatools_map_analyzer_folder: StringProperty(
        name="Папка с IDE/IPL",
        subtype='DIR_PATH', default="")
    gtatools_map_analyzer_recursive: BoolProperty(
        name="Включая подпапки",
        description="Рекурсивный обход подпапок при FOLDER-режиме",
        default=True)
    gtatools_map_analyzer_check_img: BoolProperty(
        name="Проверять модели в IMG",
        description="Авто-поиск всех *.img в области скана (DAT-строки / FOLDER walk / CUSTOM parent dirs) и cross-check IDE entries — flag missing DFF/TXD",
        default=False)
    gtatools_map_analyzer_custom_ides: CollectionProperty(type=GTATOOLS_PathItem)
    gtatools_map_analyzer_custom_ipls: CollectionProperty(type=GTATOOLS_PathItem)
    gtatools_map_analyzer_only_errors: BoolProperty(
        name="Только ERROR",
        description="Скрыть WARN/INFO в списке (фильтр draw)",
        default=True)
    # Shared profile for File Scanner + Map Analyzer. Single EnumProperty
    # rather than per-tool — modders typically have one stance on
    # what counts as a problem; splitting would force them to keep
    # both panels in sync manually.
    # Texture Browser inputs. Reuses the same source-mode pattern as
    # Map Analyzer (DAT / FOLDER / CUSTOM) but with its own paths so
    # the user can index a different scope.
    gtatools_texture_browser_source: EnumProperty(
        name="Источник",
        description="Откуда брать TXD-файлы для индекса",
        items=[
            ('DAT',    "DAT",    "Из gta.dat по путям сцены — все *.img и *.txd"),
            ('FOLDER', "Папка", "Просканировать одну папку рекурсивно"),
            ('CUSTOM', "Файлы", "Вручную выбранные .img / .txd"),
        ],
        default='DAT')
    gtatools_texture_browser_folder: StringProperty(
        name="Папка",
        description="Папка со стандалон-TXD для сканирования",
        subtype='DIR_PATH', default='')
    gtatools_texture_browser_custom: CollectionProperty(type=GTATOOLS_PathItem)
    gtatools_texture_browser_check_ide: BoolProperty(
        name="Cross-ref c IDE",
        description="Подсчитать сколько IDE-моделей используют каждый TXD (используется тот же набор IDE что и у Map Analyzer)",
        default=True)
    gtatools_texture_browser_search: StringProperty(
        name="Поиск",
        description="Фильтр по имени текстуры или TXD",
        default='')

    gtatools_lint_profile: EnumProperty(
        name="Профиль",
        description="Стандарт (vanilla SA) / FLA / Строгий / Мягкий",
        items=[
            ('STANDARD', "Стандарт", "Калибровано под vanilla SA — поведение из коробки"),
            ('FLA',      "FLA",      "Считаем что Fastman92 Limit Adjuster установлен: глушим warnings про ID > 19999, interior > 18, COL surface > 178"),
            ('STRICT',   "Строгий", "Жёстче пороги: draw_distance > 800m, mat > 50, vert > 16k, 2DFX > 100, texture > 512px. Для QA сборки"),
            ('LENIENT',  "Мягкий",  "Прячем все INFO-уровни. Для легаси-проектов где informational шум перевешивает сигнал"),
        ],
        default='STANDARD')

    # ── Viewport Floater ──────────────────────────────────────
    # Plавающее окно с инфо по активному объекту. State for the
    # gpu+blf-drawn panel in ops/viewport_floater.py. Default OFF so
    # opening Blender never shows the floater until user toggles it.
    inu_floater_visible: BoolProperty(default=False)
    inu_floater_collapsed: BoolProperty(default=False)
    inu_floater_locked: BoolProperty(default=False)
    inu_floater_workspace: StringProperty(default="")
    inu_floater_x: IntProperty(default=40, min=-9999, max=9999)
    inu_floater_y: IntProperty(default=200, min=-9999, max=9999)

    # Import/Export floater (second instance, framework-driven)
    inu_floater_ie_visible: BoolProperty(default=False)
    inu_floater_ie_collapsed: BoolProperty(default=False)
    inu_floater_ie_locked: BoolProperty(default=False)
    inu_floater_ie_workspace: StringProperty(default="")
    inu_floater_ie_x: IntProperty(default=340, min=-9999, max=9999)
    inu_floater_ie_y: IntProperty(default=200, min=-9999, max=9999)

    # Validation floater (Проверка перед экспортом)
    inu_floater_val_visible: BoolProperty(default=False)
    inu_floater_val_collapsed: BoolProperty(default=False)
    inu_floater_val_locked: BoolProperty(default=False)
    inu_floater_val_workspace: StringProperty(default="")
    inu_floater_val_x: IntProperty(default=640, min=-9999, max=9999)
    inu_floater_val_y: IntProperty(default=200, min=-9999, max=9999)

    # Lighting floater
    inu_floater_light_visible: BoolProperty(default=False)
    inu_floater_light_collapsed: BoolProperty(default=False)
    inu_floater_light_locked: BoolProperty(default=False)
    inu_floater_light_workspace: StringProperty(default="")
    inu_floater_light_x: IntProperty(default=340, min=-9999, max=9999)
    inu_floater_light_y: IntProperty(default=400, min=-9999, max=9999)

    # IDE / IPL / IMG floater
    inu_floater_iii_visible: BoolProperty(default=False)
    inu_floater_iii_collapsed: BoolProperty(default=False)
    inu_floater_iii_locked: BoolProperty(default=False)
    inu_floater_iii_workspace: StringProperty(default="")
    inu_floater_iii_x: IntProperty(default=640, min=-9999, max=9999)
    inu_floater_iii_y: IntProperty(default=400, min=-9999, max=9999)

    # ── CollectionProperty fields with custom item types ──────
    inu_validate_issues: CollectionProperty(type=INUValidateIssue)
    gtatools_binary_ipls: CollectionProperty(type=GTATOOLS_BinaryIplEntry)
    gtatools_text_ipls: CollectionProperty(type=GTATOOLS_TextIplEntry)
    gtatools_img_entries: CollectionProperty(type=GTATOOLS_ImgFileEntry)
    gtatools_bake_layers: CollectionProperty(type=INUBakeLayer)
