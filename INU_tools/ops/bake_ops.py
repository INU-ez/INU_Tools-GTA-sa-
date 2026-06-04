# INU_tools.ops.bake_ops — Слой 4 подсистемы запекания: операторы.
#
# Оркестрируют bake_core + bake_maps + bake_composite по scene-настройкам
# (INUSceneSettings.gtatools_bake_*) и стеку слоёв (gtatools_bake_layers).
# Сами карты/композит живут в tools/bake/ — здесь только склейка, guard'ы
# валидации (Cycles, UV), report() и undo.
#
# ВАЖНО: НЕ добавлять `from __future__ import annotations` — модуль
# объявляет Operator-проперти (EnumProperty), их ломает PEP 563.

import json
import re

import bpy
from bpy.props import EnumProperty, StringProperty

from .. import T


def _derive_texture_name(obj, s):
    """Имя выходной текстуры из имени модели: срезаем .001-хвост, известные
    префиксы и суффиксы (_DFF/_LOD/_COL + фиксированные _hi/_low).
    Регистронезависимо."""
    from ..tools.bake import HI_SUFFIX, LOW_SUFFIX
    name = re.sub(r'\.\d+$', '', obj.name)
    low = name.lower()
    for pfx in (s.gtatools_prefix_dff, s.gtatools_prefix_lod,
                s.gtatools_prefix_col):
        if pfx and low.startswith(pfx.lower()):
            name = name[len(pfx):]
            low = name.lower()
    for sfx in (HI_SUFFIX, LOW_SUFFIX,
                s.gtatools_suffix_dff, s.gtatools_suffix_lod,
                s.gtatools_suffix_col):
        if sfx and low.endswith(sfx.lower()):
            name = name[:-len(sfx)]
            break
    name = name.strip(' _.')
    return name or "inu_bake"


def _snapshot_materials(obj):
    """Сохранить исходные материалы + рендер-UV в custom-props (только если
    ещё не сохранены — не перезаписываем при повторном применении)."""
    if obj.get("inu_bake_preview_on", 0):
        return
    me = obj.data
    obj["inu_bake_prev_mats"] = json.dumps(
        [s.material.name if s.material else "" for s in obj.material_slots])
    obj["inu_bake_prev_render_uv"] = next(
        (u.name for u in me.uv_layers if u.active_render), "")


def _assign_material(obj, mat, uv_name):
    """Поставить единственный материал `mat`; переключить рендер-UV на uv_name."""
    me = obj.data
    if uv_name and uv_name in me.uv_layers:
        for u in me.uv_layers:
            u.active_render = (u.name == uv_name)
    me.materials.clear()
    me.materials.append(mat)
    obj["inu_bake_preview_on"] = 1


def _restore_materials(obj):
    """Вернуть исходные материалы + рендер-UV; снять флаг превью."""
    me = obj.data
    try:
        mats = json.loads(obj.get("inu_bake_prev_mats", "[]"))
    except Exception:
        mats = []
    me.materials.clear()
    for nm in mats:
        me.materials.append(bpy.data.materials.get(nm) if nm else None)
    ruv = obj.get("inu_bake_prev_render_uv", "")
    if ruv and ruv in me.uv_layers:
        for u in me.uv_layers:
            u.active_render = (u.name == ruv)
    obj["inu_bake_preview_on"] = 0
    for nm in ("INU_BakePreview", "INU_BakeComposite"):
        m = bpy.data.materials.get(nm)
        if m is not None and m.users == 0:
            try:
                bpy.data.materials.remove(m)
            except Exception:
                pass


def _build_single_image_mat(img, uv_name):
    """Материал INU_BakePreview — flat-эмиссия одной картинки (per-map)."""
    pm = (bpy.data.materials.get("INU_BakePreview")
          or bpy.data.materials.new("INU_BakePreview"))
    pm.use_nodes = True
    pm.use_fake_user = False
    nt = pm.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    if uv_name:
        uvm = nt.nodes.new('ShaderNodeUVMap')
        uvm.uv_map = uv_name
        nt.links.new(uvm.outputs['UV'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], emit.inputs['Color'])
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return pm


def _layer_specs(s):
    return [{'map_id': L.map_id, 'blend_mode': L.blend_mode,
             'opacity': L.opacity, 'enabled': L.enabled}
            for L in s.gtatools_bake_layers]


def _apply_result_material(obj):
    """Показать результат на модели: композит → живой нодовый стек, per-map →
    одиночная картинка. Возвращает материал (или None, если нечего показать)."""
    s = bpy.context.scene.inu_settings
    base = obj.get("inu_bake_base", "")
    uv = obj.get("inu_bake_uv", "")
    _snapshot_materials(obj)
    if obj.get("inu_bake_mode_live", 0):
        from ..tools.bake import bake_nodes
        mat = bake_nodes.build_composite_material(_layer_specs(s), base, uv)
    else:
        img = bpy.data.images.get(obj.get("inu_bake_image", ""))
        if img is None:
            return None
        mat = _build_single_image_mat(img, uv)
    _assign_material(obj, mat, uv)
    return mat


def rebuild_live_composite(obj):
    """Пересобрать живой нодовый материал при правке слоёв (мгновенное
    обновление). Только если композит-превью сейчас на модели."""
    if not (obj and obj.get("inu_bake_preview_on", 0)
            and obj.get("inu_bake_mode_live", 0)):
        return
    from ..tools.bake import bake_nodes
    s = bpy.context.scene.inu_settings
    bake_nodes.build_composite_material(
        _layer_specs(s), obj.get("inu_bake_base", ""), obj.get("inu_bake_uv", ""))


class GTATOOLS_OT_bake_run(bpy.types.Operator):
    """Запечь карты активного объекта. В режиме «Композит» складывает
    включённые слои в одну текстуру, иначе пишет каждую карту в свою
    картинку. Свет для карт генерируется самой подсистемой — внешние
    источники сцены не нужны."""
    bl_idname = "gtatools.bake_run"
    bl_label = "Запечь"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def execute(self, context):
        from ..tools import bake as B

        scene = context.scene
        s = scene.inu_settings
        obj = context.active_object

        # ── Валидация ──
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выделите меш-объект"))
            return {'CANCELLED'}
        if not B.cycles_available(scene):
            self.report({'ERROR'}, T("Cycles недоступен — включите аддон Cycles"))
            return {'CANCELLED'}
        layers = [L for L in s.gtatools_bake_layers if L.enabled]
        if not layers:
            self.report({'ERROR'}, T("Добавьте хотя бы один слой карты"))
            return {'CANCELLED'}

        res_x = int(s.gtatools_bake_res_x)
        res_y = int(s.gtatools_bake_res_y)
        margin = int(s.gtatools_bake_margin)
        composite = bool(s.gtatools_bake_composite_mode)
        scene_samples = int(s.gtatools_bake_samples)
        params = {
            'bevel_size': float(s.gtatools_bake_bevel_size),
            'bevel_samples': int(s.gtatools_bake_bevel_samples),
            'light_energy_scale': float(s.gtatools_bake_light_energy_scale),
        }

        if obj.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

        # ── Режим: что и куда печём ──
        # bpy.ops.object.bake обрабатывает ВЫДЕЛЕННЫЕ объекты и падает, если
        # среди них скрытый из рендера — поэтому ниже аккуратно выставляем
        # выделение под каждый режим.
        s2a = False
        cage = 0.0
        mray = 0.0
        keep = ()
        if s.gtatools_bake_mode == 'HILOW':
            high, low = B.find_hilow_pair(obj, B.HI_SUFFIX, B.LOW_SUFFIX)
            if high is None or low is None:
                self.report(
                    {'ERROR'},
                    T("У выделенной модели нет пары по суффиксам ")
                    + f"{B.HI_SUFFIX} / {B.LOW_SUFFIX} "
                    + T("(назовите модели вида name_hi и name_low)"))
                return {'CANCELLED'}
            if not low.data.uv_layers or not low.data.uv_layers.active:
                self.report({'ERROR'}, T("У лоуполи нет UV-развёртки"))
                return {'CANCELLED'}
            bake_obj = low
            target_uv = None              # печём в активную UV лоуполи
            s2a = True
            cage = float(s.gtatools_bake_cage_extrusion)
            mray = float(s.gtatools_bake_max_ray)
            keep = (high,)
            for o in context.view_layer.objects:
                try:
                    o.select_set(o is high or o is low)
                except Exception:
                    pass
            context.view_layer.objects.active = low
        else:  # UV → UV
            if not obj.data.uv_layers or len(obj.data.uv_layers) == 0:
                self.report({'ERROR'}, T("У объекта нет UV-развёртки для запекания"))
                return {'CANCELLED'}
            bake_obj = obj
            # Цель = ВЫДЕЛЕННАЯ UV (uv_layers.active); источник = рендер-UV
            # (active_render) — определяется автоматически в bake_one_map.
            target_uv = (obj.data.uv_layers.active.name
                         if obj.data.uv_layers.active else None)
            for o in context.view_layer.objects:
                try:
                    o.select_set(o is obj)
                except Exception:
                    pass
            context.view_layer.objects.active = obj

        # Имя выходной текстуры — из имени модели (без префиксов/суффиксов).
        result_name = _derive_texture_name(bake_obj, s)

        # Уникальные карты (одна карта может встречаться в стеке несколько
        # раз с разными blend — печём её ОДИН раз, композит переиспользует).
        unique = []
        for L in layers:
            if L.map_id not in unique and B.get_map(L.map_id) is not None:
                unique.append(L.map_id)
        if not unique:
            self.report({'ERROR'}, T("Нет валидных карт в стеке"))
            return {'CANCELLED'}

        def _samples_for(md):
            return scene_samples if (md.bake_type == 'AO' or md.needs_light) else None

        # Если превью включено — печём по ИСХОДНЫМ материалам (иначе
        # запеклась бы превью-эмиссия), потом вернём превью с новой
        # текстурой → она обновится сразу.
        was_preview = bool(bake_obj.get("inu_bake_preview_on", 0))
        if was_preview:
            _restore_materials(bake_obj)

        baked = 0
        result_img = None
        try:
            with B.BakeStateGuard(context):
                # Каждую карту печём в свою картинку <base>_<map> — это
                # источники и для живого нодового стека, и для «Свести».
                for mid in unique:
                    md = B.get_map(mid)
                    img = B.setup_target_image(
                        f"{result_name}_{mid}", res_x, res_y, transient=False)
                    B.bake_one_map(context, md, bake_obj, img, margin=margin,
                                   params=params, samples=_samples_for(md),
                                   target_uv=target_uv, selected_to_active=s2a,
                                   cage_extrusion=cage, max_ray=mray,
                                   keep_visible=keep)
                    try:
                        img.pack()
                    except Exception:
                        pass
                    img.update()
                    if result_img is None or mid == 'DIFFUSE':
                        result_img = img
                    baked += 1
        except RuntimeError as e:
            self.report({'ERROR'}, T("Ошибка запекания: ") + str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, T("Ошибка: ") + str(e))
            return {'CANCELLED'}

        # Метаданные для нод / превью / сведения.
        baked_uv = target_uv or (bake_obj.data.uv_layers.active.name
                                 if bake_obj.data.uv_layers.active else "")
        bake_obj["inu_bake_base"] = result_name
        bake_obj["inu_bake_uv"] = baked_uv
        bake_obj["inu_bake_mode_live"] = 1 if composite else 0
        bake_obj["inu_bake_image"] = (
            "" if composite else (result_img.name if result_img else ""))

        if composite:
            # Живой нодовый материал на модель — крутишь opacity/blend сразу.
            _apply_result_material(bake_obj)
            msg = T("Live-композит собран: ") + str(baked) + T(" карт")
        else:
            # Показать diffuse-карту в Image-редакторе.
            if result_img is not None:
                try:
                    sp = getattr(context, 'space_data', None)
                    if sp is not None and getattr(sp, 'type', '') == 'IMAGE_EDITOR':
                        sp.image = result_img
                    else:
                        for area in context.screen.areas:
                            if area.type == 'IMAGE_EDITOR':
                                area.spaces.active.image = result_img
                                break
                except Exception:
                    pass
            if was_preview:           # вернуть превью с обновлённой картинкой
                _apply_result_material(bake_obj)
            msg = T("Запечено карт: ") + str(baked)

        self.report({'INFO'}, msg)
        return {'FINISHED'}


class GTATOOLS_OT_bake_layer_add(bpy.types.Operator):
    """Добавить слой карты в стек запекания"""
    bl_idname = "gtatools.bake_layer_add"
    bl_label = "Добавить слой"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..tools.bake import BAKE_MAPS
        s = context.scene.inu_settings
        layer = s.gtatools_bake_layers.add()
        first = next(iter(BAKE_MAPS.values()), None)
        if first is not None:
            layer.map_id = first.id
            layer.blend_mode = first.default_blend
            layer.opacity = first.default_opacity
        s.gtatools_bake_layers_index = len(s.gtatools_bake_layers) - 1
        rebuild_live_composite(context.active_object)
        return {'FINISHED'}


class GTATOOLS_OT_bake_layer_remove(bpy.types.Operator):
    """Удалить выбранный слой из стека запекания"""
    bl_idname = "gtatools.bake_layer_remove"
    bl_label = "Удалить слой"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.inu_settings
        i = s.gtatools_bake_layers_index
        n = len(s.gtatools_bake_layers)
        if 0 <= i < n:
            s.gtatools_bake_layers.remove(i)
            s.gtatools_bake_layers_index = min(i, len(s.gtatools_bake_layers) - 1)
        rebuild_live_composite(context.active_object)
        return {'FINISHED'}


class GTATOOLS_OT_bake_layer_move(bpy.types.Operator):
    """Переместить слой вверх/вниз в стеке (порядок = порядок смешивания)"""
    bl_idname = "gtatools.bake_layer_move"
    bl_label = "Переместить слой"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=[('UP', "Up", ""), ('DOWN', "Down", "")], default='UP')

    def execute(self, context):
        s = context.scene.inu_settings
        i = s.gtatools_bake_layers_index
        n = len(s.gtatools_bake_layers)
        j = i - 1 if self.direction == 'UP' else i + 1
        if 0 <= i < n and 0 <= j < n:
            s.gtatools_bake_layers.move(i, j)
            s.gtatools_bake_layers_index = j
        rebuild_live_composite(context.active_object)
        return {'FINISHED'}


class GTATOOLS_OT_bake_add_uv(bpy.types.Operator):
    """Создать отдельную чистую UV-карту для запекания (Smart UV Project) и
    выбрать её целевой. Рабочую trim-развёртку НЕ трогает — для trim-
    воркфлоу: текстуры остаются на trim-UV, а свет/AO печём в эту чистую."""
    bl_idname = "gtatools.bake_add_uv"
    bl_label = "Создать UV для запекания"
    bl_options = {'REGISTER', 'UNDO'}

    uv_name: StringProperty(name="Имя UV", default="bake_uv")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        me = obj.data
        name = (self.uv_name or "bake_uv").strip() or "bake_uv"
        created = name not in me.uv_layers
        # Снапшот рендер-UV (источник, 📷): новая bake-UV НЕ должна его
        # перехватить — иначе перенос засэмплит её же, а не trim-источник.
        prev_render = next((u.name for u in me.uv_layers if u.active_render), None)

        if created:
            me.uv_layers.new(name=name)
        me.uv_layers.active = me.uv_layers[name]

        prev_mode = obj.mode
        try:
            if obj.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(island_margin=0.02)
        except Exception as e:
            self.report({'WARNING'},
                        T("UV создана, авто-развёртка не удалась: ") + str(e))
        finally:
            try:
                if obj.mode != prev_mode:
                    bpy.ops.object.mode_set(mode=prev_mode)
            except Exception:
                pass

        # Источник (рендер-UV, 📷) оставляем на рабочей развёртке; новую
        # bake-UV оставляем ВЫДЕЛЕННОЙ — она и есть цель запекания.
        if prev_render and prev_render in me.uv_layers:
            for u in me.uv_layers:
                u.active_render = (u.name == prev_render)
        me.uv_layers.active = me.uv_layers[name]
        self.report({'INFO'},
                    (T("Создана UV: ") if created else T("UV обновлена: ")) + name)
        return {'FINISHED'}


class GTATOOLS_OT_bake_preview(bpy.types.Operator):
    """Показать/скрыть запечённую текстуру прямо на модели (flat-эмиссия,
    видно при любом освещении). Для UV→UV переключает отображение на UV, в
    которую запекали; для hi→low просто показывает на лоуполи. Повторный
    клик возвращает исходные материалы и рендер-UV.

    Исходные материалы/UV хранятся в custom-props объекта (переживают
    перезагрузку аддона и сохранение .blend)."""
    bl_idname = "gtatools.bake_preview"
    bl_label = "Показать текстуру"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'MESH'
                and bool(obj.get("inu_bake_base")))

    def execute(self, context):
        obj = context.active_object
        if bool(obj.get("inu_bake_preview_on", 0)):
            _restore_materials(obj)
            self.report({'INFO'}, T("Превью выключено"))
            return {'FINISHED'}
        if _apply_result_material(obj) is None:
            self.report({'ERROR'},
                        T("Нет запечённого результата — сначала запеките"))
            return {'CANCELLED'}
        self.report({'INFO'}, T("Превью включено"))
        return {'FINISHED'}


class GTATOOLS_OT_bake_flatten(bpy.types.Operator):
    """Свести стек слоёв (per-map картинки <base>_<map>) в ОДНУ текстуру
    <base> numpy-композитом — финальная плоская текстура для экспорта."""
    bl_idname = "gtatools.bake_flatten"
    bl_label = "Свести в текстуру"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'MESH'
                and bool(obj.get("inu_bake_base")))

    def execute(self, context):
        from ..tools import bake as B
        obj = context.active_object
        s = context.scene.inu_settings
        base = obj.get("inu_bake_base", "")

        pixels = {}
        for L in s.gtatools_bake_layers:
            if not L.enabled or L.map_id in pixels:
                continue
            img = bpy.data.images.get(f"{base}_{L.map_id}")
            if img is not None:
                pixels[L.map_id] = B.read_image_to_numpy(img)
        if not pixels:
            self.report({'ERROR'}, T("Нет запечённых карт для сведения"))
            return {'CANCELLED'}

        first = bpy.data.images.get(f"{base}_{next(iter(pixels))}")
        w, h = first.size
        specs = [B.LayerSpec(
            map_id=L.map_id, enabled=L.enabled, blend_mode=L.blend_mode,
            opacity=L.opacity, contrast=L.contrast, gamma=L.gamma,
            influence_target=L.influence_target,
            influence_amount=L.influence_amount) for L in s.gtatools_bake_layers]
        arr = B.composite_layers(pixels, specs, w, h, srgb=False)
        final = B.setup_target_image(base, w, h, transient=False)
        B.write_numpy_to_image(final, arr, pack=True)

        try:
            sp = getattr(context, 'space_data', None)
            if sp is not None and getattr(sp, 'type', '') == 'IMAGE_EDITOR':
                sp.image = final
            else:
                for area in context.screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        area.spaces.active.image = final
                        break
        except Exception:
            pass

        self.report({'INFO'}, T("Сведено в текстуру: ") + final.name)
        return {'FINISHED'}
