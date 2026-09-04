# INU_tools.ops.prelight_preset_ops — Prelight bake preset load/save/delete.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import bpy
from bpy.props import (
    StringProperty,
)

from .. import T


def _pub(op, type_set, msg):
    """``op.report(type_set, msg)`` (banner / Info log as usual) AND mirror
    the same text into the active floater's bottom strip — so a button
    pressed in a floater shows the SAME notification the N-panel shows.
    Floaters dispatch ops via ``bpy.ops`` where Blender hides the banner,
    hence this explicit mirror. ``set_floater_status`` is a no-op when no
    floater is the active target."""
    op.report(type_set, msg)
    try:
        from .floater.base import set_floater_status
        lvl = ('ERROR' if 'ERROR' in type_set
               else 'WARNING' if 'WARNING' in type_set else 'INFO')
        set_floater_status(str(msg), lvl)
    except Exception:
        pass


# ── Lights snapshot ────────────────────────────────────────────
# 8-light prelight rig is part of the preset payload. Position is
# stored RELATIVE to the lights' bounding-box center (so loading the
# preset on a scene with a different active object re-derives the
# absolute positions from the active obj's bbox center). Color +
# energy + radius captured verbatim.

_PRELIGHT_COLLECTION = "Prelight_Lights"


def _collect_lights_snapshot():
    """Return list of dicts describing each lamp in Prelight_Lights
    collection, or [] if collection is missing/empty.

    Positions are stored RELATIVE to the bbox center of all lamps —
    this lets the snapshot load on objects of any size; Apply will
    re-anchor the lamp ring around the active object's bbox.
    """
    coll = bpy.data.collections.get(_PRELIGHT_COLLECTION)
    if not coll or not coll.objects:
        return []
    lamp_objs = [o for o in coll.objects if o.type == 'LIGHT']
    if not lamp_objs:
        return []

    # Bbox center of the lamp ring → relative offsets.
    cx = sum(o.location.x for o in lamp_objs) / len(lamp_objs)
    cy = sum(o.location.y for o in lamp_objs) / len(lamp_objs)
    cz = sum(o.location.z for o in lamp_objs) / len(lamp_objs)

    out = []
    for o in lamp_objs:
        ldata = o.data
        out.append({
            "name": o.name,
            "rel_offset": [
                float(o.location.x - cx),
                float(o.location.y - cy),
                float(o.location.z - cz),
            ],
            "color": [float(c) for c in ldata.color],
            "energy": float(getattr(ldata, "energy", 0.0)),
            "radius": float(getattr(ldata, "shadow_soft_size", 0.0)),
        })
    return out


def _apply_lights_snapshot(context, snapshot):
    """Replace contents of Prelight_Lights collection with the lamps
    described by ``snapshot``. Lamp positions are anchored around the
    active mesh object's bbox center; if no active mesh, anchored at
    world origin."""
    if not snapshot:
        return 0
    from mathutils import Vector
    obj = context.active_object
    if obj is not None and obj.type == 'MESH':
        bbox_center = sum((Vector(b) for b in obj.bound_box), Vector()) / 8
        center = obj.matrix_world @ bbox_center
    else:
        center = Vector((0.0, 0.0, 0.0))

    coll = bpy.data.collections.get(_PRELIGHT_COLLECTION)
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        coll = bpy.data.collections.new(_PRELIGHT_COLLECTION)
        context.scene.collection.children.link(coll)

    created = 0
    for entry in snapshot:
        name = entry.get("name", "Prelight_Lamp")
        rel = entry.get("rel_offset", [0.0, 0.0, 0.0])
        ldata = bpy.data.lights.new(name=name, type='POINT')
        ldata.color = tuple(entry.get("color", [1.0, 1.0, 1.0]))[:3]
        ldata.energy = float(entry.get("energy", 10.0))
        if hasattr(ldata, "shadow_soft_size"):
            ldata.shadow_soft_size = float(entry.get("radius", 0.0))
        lamp_obj = bpy.data.objects.new(name=name, object_data=ldata)
        lamp_obj.location = (
            center.x + rel[0],
            center.y + rel[1],
            center.z + rel[2],
        )
        coll.objects.link(lamp_obj)
        created += 1
    return created


# ── Default preset (read-only) ─────────────────────────────────
# Lives next to the addon code as `data/default_prelight_preset.json`.
# Always shows up first in the preset enum and cannot be deleted /
# overwritten / renamed. «Load» works as usual.

_DEFAULT_PRESET_NAME = "Default"


def _is_default_preset(name):
    return (name or "").strip() == _DEFAULT_PRESET_NAME


def _collect_object_preset_state(context):
    """Read per-object Day/Night state from the active mesh.

    Returns a dict with v_offset_day/_night and has_day_attr/_night_attr.
    Falls back to zeros / False when no active mesh — the preset still
    saves cleanly and Load becomes a no-op for the per-object part.
    """
    from ..tools import compat
    obj = context.active_object
    if not obj or obj.type != 'MESH':
        return {
            "v_offset_day": 0.0,
            "v_offset_night": 0.0,
            "has_day_attr": False,
            "has_night_attr": False,
        }
    mesh = obj.data
    return {
        "v_offset_day": float(getattr(obj, "gtatools_v_offset_day", 0.0)),
        "v_offset_night": float(getattr(obj, "gtatools_v_offset_night", 0.0)),
        "has_day_attr": compat.vcol_get(mesh, "Day") is not None,
        "has_night_attr": compat.vcol_get(mesh, "Night") is not None,
    }


def _apply_object_preset_state(context, preset):
    """Materialise saved Day/Night attrs + V values on selected meshes.

    For each selected mesh (or the active one): create missing Day/Night
    attributes when the preset flagged them, then apply V offset via
    apply_brightness_offset and sync the per-object FloatProperty.
    Returns (objects_touched, attrs_created).
    """
    has_day = bool(preset.get('has_day_attr', False))
    has_night = bool(preset.get('has_night_attr', False))
    if not has_day and not has_night:
        return 0, 0

    from ..tools import compat
    from ..tools.prelight import apply_brightness_offset

    targets = [o for o in context.selected_objects if o.type == 'MESH']
    if not targets:
        ao = context.active_object
        if ao and ao.type == 'MESH':
            targets = [ao]
    if not targets:
        return 0, 0

    day_v = float(preset.get('v_offset_day', 0.0))
    night_v = float(preset.get('v_offset_night', 0.0))
    attrs_created = 0

    for obj in targets:
        mesh = obj.data
        saved_active = compat.vcol_active(mesh)
        saved_active_name = saved_active.name if saved_active else None

        for attr_name, want, v_value, prop_name in (
            ("Day", has_day, day_v, "gtatools_v_offset_day"),
            ("Night", has_night, night_v, "gtatools_v_offset_night"),
        ):
            if not want:
                continue
            layer = compat.vcol_get(mesh, attr_name)
            if layer is None:
                layer = compat.vcol_new(mesh, attr_name)
                for i in range(len(layer.data)):
                    layer.data[i].color = (1.0, 1.0, 1.0, 1.0)
                # Reset the tracked offset so apply_brightness_offset
                # multiplies fresh white (mult=1.0) rather than re-using
                # whatever this object had under the same attr-name before.
                obj["v_offset_" + attr_name] = 0.0
                attrs_created += 1
            compat.vcol_active(mesh, layer)
            apply_brightness_offset(obj, v_value)
            # Sync displayed prop. May be a no-op if value unchanged —
            # apply_brightness_offset above already wrote the colors.
            setattr(obj, prop_name, v_value)

        if saved_active_name:
            sl = compat.vcol_get(mesh, saved_active_name)
            if sl is not None:
                compat.vcol_active(mesh, sl)

    return len(targets), attrs_created


class GTATOOLS_OT_prelight_preset_load(bpy.types.Operator):
    """Загрузить выбранный пресет"""
    bl_idname = "gtatools.prelight_preset_load"
    bl_label = "INU: Load Preset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        s = scene.inu_settings
        name = s.gtatools_prelight_preset
        from .. import _load_prelight_presets
        presets = _load_prelight_presets()
        for p in presets:
            if p['name'] == name:
                # Bake (Запекание)
                s.gtatools_bake_ambient = p.get('ambient', 0.10)
                s.gtatools_bake_intensity = p.get('intensity', 0.05)
                s.gtatools_bake_gamma = p.get('gamma', 0.50)
                s.gtatools_bake_shadows = p.get('shadows', True)
                # Modulate Color
                s.gtatools_modulate_mode = p.get('modulate_mode', s.gtatools_modulate_mode)
                s.gtatools_modulate_mix = p.get('modulate_mix', s.gtatools_modulate_mix)
                s.gtatools_modulate_contrast = p.get('modulate_contrast', s.gtatools_modulate_contrast)
                s.gtatools_modulate_gamma = p.get('modulate_gamma', s.gtatools_modulate_gamma)
                # Adjust Color
                s.gtatools_v_offset = p.get('v_offset', s.gtatools_v_offset)
                # Sub-panel: Инструменты (scatter color)
                s.gtatools_scatter_color_strength = p.get('scatter_strength', s.gtatools_scatter_color_strength)
                s.gtatools_scatter_color_distance = p.get('scatter_distance', s.gtatools_scatter_color_distance)
                # Sub-panel: Post-Processing
                s.gtatools_vc_smooth_iterations = p.get('vc_smooth_iter', s.gtatools_vc_smooth_iterations)
                s.gtatools_vc_smooth_factor = p.get('vc_smooth_factor', s.gtatools_vc_smooth_factor)
                s.gtatools_vc_contrast = p.get('vc_contrast', s.gtatools_vc_contrast)
                s.gtatools_vc_brightness = p.get('vc_brightness', s.gtatools_vc_brightness)
                s.gtatools_vc_gamma = p.get('vc_gamma', s.gtatools_vc_gamma)
                s.gtatools_lift_shadows_strength = p.get('lift_shadows', s.gtatools_lift_shadows_strength)
                # Per-object: create Day/Night attrs (if preset flagged
                # them) on selected meshes and apply saved V offsets.
                touched, created = _apply_object_preset_state(context, p)
                # Lights: if preset has a snapshot, materialise it
                # (replaces existing Prelight_Lights collection).
                lights_count = _apply_lights_snapshot(context, p.get('lights', []))
                msg = f"{T('Пресет загружен:')} {name}"
                if touched:
                    msg += f" | {touched} {T('объектов')}, +{created} attr"
                if lights_count:
                    msg += f" | {lights_count} {T('ламп')}"
                _pub(self,{'INFO'}, msg)
                return {'FINISHED'}
        _pub(self,{'ERROR'}, T("Пресет не найден"))
        return {'CANCELLED'}


class GTATOOLS_OT_prelight_preset_save(bpy.types.Operator):
    """Сохранить текущие настройки как пресет"""
    bl_idname = "gtatools.prelight_preset_save"
    bl_label = "INU: Save Preset"
    bl_options = {'REGISTER'}

    preset_name: StringProperty(name="Name", default="My Preset")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        s = context.scene.inu_settings

        if _is_default_preset(self.preset_name):
            _pub(self,{'ERROR'}, T("'Default' зарезервирован — выбери другое имя"))
            return {'CANCELLED'}

        new_preset = {
            "name": self.preset_name,
            # Bake (Запекание)
            "ambient": s.gtatools_bake_ambient,
            "intensity": s.gtatools_bake_intensity,
            "gamma": s.gtatools_bake_gamma,
            "shadows": s.gtatools_bake_shadows,
            # Modulate Color
            "modulate_mode": s.gtatools_modulate_mode,
            "modulate_mix": s.gtatools_modulate_mix,
            "modulate_contrast": s.gtatools_modulate_contrast,
            "modulate_gamma": s.gtatools_modulate_gamma,
            # Adjust Color
            "v_offset": s.gtatools_v_offset,
            # Sub-panel: Инструменты (scatter color)
            "scatter_strength": s.gtatools_scatter_color_strength,
            "scatter_distance": s.gtatools_scatter_color_distance,
            # Sub-panel: Post-Processing
            "vc_smooth_iter": s.gtatools_vc_smooth_iterations,
            "vc_smooth_factor": s.gtatools_vc_smooth_factor,
            "vc_contrast": s.gtatools_vc_contrast,
            "vc_brightness": s.gtatools_vc_brightness,
            "vc_gamma": s.gtatools_vc_gamma,
            "lift_shadows": s.gtatools_lift_shadows_strength,
            # Per-object Day/Night state (read from active mesh).
            **_collect_object_preset_state(context),
            # Lights snapshot (8-light rig if present in scene).
            "lights": _collect_lights_snapshot(),
        }

        from .. import _save_preset_file
        _save_preset_file(new_preset)
        _pub(self,{'INFO'}, f"{T('Пресет сохранён:')} {self.preset_name}")
        return {'FINISHED'}


class GTATOOLS_OT_prelight_preset_delete(bpy.types.Operator):
    """Удалить выбранный пресет"""
    bl_idname = "gtatools.prelight_preset_delete"
    bl_label = "INU: Delete Preset"
    bl_options = {'REGISTER'}

    def execute(self, context):
        name = context.scene.inu_settings.gtatools_prelight_preset
        if _is_default_preset(name):
            _pub(self,{'ERROR'}, T("'Default' нельзя удалить — это встроенный пресет"))
            return {'CANCELLED'}
        from .. import _delete_preset_file
        _delete_preset_file(name)
        _pub(self,{'INFO'}, f"{T('Пресет удалён:')} {name}")
        return {'FINISHED'}


class GTATOOLS_OT_prelight_preset_apply(bpy.types.Operator):
    """Перезаписать выбранный пресет текущими настройками (без диалога имени)"""
    bl_idname = "gtatools.prelight_preset_apply"
    bl_label = "INU: Save to Selected Preset"
    bl_options = {'REGISTER'}

    def execute(self, context):
        s = context.scene.inu_settings
        name = s.gtatools_prelight_preset
        if not name or name == 'NONE':
            _pub(self,{'ERROR'}, T("Сначала выберите пресет в списке"))
            return {'CANCELLED'}
        if _is_default_preset(name):
            _pub(self,{'ERROR'},
                T("'Default' read-only — сохрани под другим именем (Save)"))
            return {'CANCELLED'}

        new_preset = {
            "name": name,
            # Bake (Запекание)
            "ambient": s.gtatools_bake_ambient,
            "intensity": s.gtatools_bake_intensity,
            "gamma": s.gtatools_bake_gamma,
            "shadows": s.gtatools_bake_shadows,
            # Modulate Color
            "modulate_mode": s.gtatools_modulate_mode,
            "modulate_mix": s.gtatools_modulate_mix,
            "modulate_contrast": s.gtatools_modulate_contrast,
            "modulate_gamma": s.gtatools_modulate_gamma,
            # Adjust Color (legacy single V)
            "v_offset": s.gtatools_v_offset,
            # Sub-panel: Инструменты (scatter color)
            "scatter_strength": s.gtatools_scatter_color_strength,
            "scatter_distance": s.gtatools_scatter_color_distance,
            # Sub-panel: Post-Processing
            "vc_smooth_iter": s.gtatools_vc_smooth_iterations,
            "vc_smooth_factor": s.gtatools_vc_smooth_factor,
            "vc_contrast": s.gtatools_vc_contrast,
            "vc_brightness": s.gtatools_vc_brightness,
            "vc_gamma": s.gtatools_vc_gamma,
            "lift_shadows": s.gtatools_lift_shadows_strength,
            # Per-object Day/Night state (read from active mesh).
            **_collect_object_preset_state(context),
            # Lights snapshot (8-light rig if present in scene).
            "lights": _collect_lights_snapshot(),
        }

        # Diff против старого файла, чтобы отчитаться что изменилось.
        from .. import _load_prelight_presets, _save_preset_file
        existing = None
        for p in _load_prelight_presets():
            if p.get('name') == name:
                existing = p
                break

        def _fmt(v):
            if isinstance(v, float):
                return f"{v:.3g}"
            return str(v)

        changed, added = [], []
        if existing:
            for k, new_v in new_preset.items():
                if k == 'name':
                    continue
                if k not in existing:
                    added.append(k)
                elif existing[k] != new_v:
                    changed.append(f"{k}: {_fmt(existing[k])}→{_fmt(new_v)}")
        else:
            added = [k for k in new_preset if k != 'name']

        _save_preset_file(new_preset)

        parts = [f"{T('Перезаписан:')} {name}"]
        if changed:
            parts.append(f"{T('изменено')}: {', '.join(changed)}")
        if added:
            parts.append(f"{T('добавлено')}: {', '.join(added)}")
        if not changed and not added:
            parts.append(T("без изменений"))
        _pub(self,{'INFO'}, " | ".join(parts))
        return {'FINISHED'}


class GTATOOLS_OT_prelight_preset_rename(bpy.types.Operator):
    """Переименовать выбранный пресет"""
    bl_idname = "gtatools.prelight_preset_rename"
    bl_label = "INU: Rename Preset"
    bl_options = {'REGISTER'}

    new_name: StringProperty(
        name="Новое название",
        default="",
    )

    def invoke(self, context, event):
        s = context.scene.inu_settings
        current = s.gtatools_prelight_preset
        if not current or current == 'NONE':
            _pub(self,{'ERROR'}, T("Сначала выберите пресет в списке"))
            return {'CANCELLED'}
        if _is_default_preset(current):
            _pub(self,{'ERROR'},
                T("'Default' нельзя переименовать — это встроенный пресет"))
            return {'CANCELLED'}
        self.new_name = current
        return context.window_manager.invoke_props_dialog(self, width=320)

    def draw(self, context):
        self.layout.prop(self, 'new_name')

    def execute(self, context):
        s = context.scene.inu_settings
        current = s.gtatools_prelight_preset
        new = (self.new_name or '').strip()
        if not new:
            _pub(self,{'ERROR'}, T("Введите новое название"))
            return {'CANCELLED'}
        if new == current:
            return {'CANCELLED'}
        if _is_default_preset(new):
            _pub(self,{'ERROR'}, T("'Default' зарезервирован — выбери другое имя"))
            return {'CANCELLED'}

        from .. import _load_prelight_presets, _save_preset_file, _delete_preset_file
        presets = _load_prelight_presets()

        # Refuse if the target name already exists — avoid silently
        # overwriting another preset.
        if any(p.get('name') == new for p in presets):
            _pub(self,{'ERROR'}, T("Имя уже занято"))
            return {'CANCELLED'}

        src = next((p for p in presets if p.get('name') == current), None)
        if src is None:
            _pub(self,{'ERROR'}, T("Пресет не найден"))
            return {'CANCELLED'}

        renamed = dict(src)
        renamed['name'] = new
        _save_preset_file(renamed)
        # Delete the old file only after the new one is written, so a
        # crash mid-rename leaves a copy rather than nothing.
        _delete_preset_file(current)

        try:
            s.gtatools_prelight_preset = new
        except Exception:
            pass
        _pub(self,{'INFO'}, f"{T('Переименован:')} {current} → {new}")
        return {'FINISHED'}


class GTATOOLS_OT_prelight_view_reset(bpy.types.Operator):
    """Сбросить коррекцию превью в нейтраль — превью покажет прилайт ровно таким, каким он уйдёт в игру"""
    bl_idname = "gtatools.prelight_view_reset"
    bl_label = "Нейтрально"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..tools.prelight import (PRELIGHT_VIEW_NEUTRAL,
                                      apply_prelight_view_correction)
        ins = context.scene.inu_settings
        bright, contrast, gamma, saturation = PRELIGHT_VIEW_NEUTRAL
        ins.prelight_view_bright = bright
        ins.prelight_view_contrast = contrast
        ins.prelight_view_gamma = gamma
        ins.prelight_view_saturation = saturation
        apply_prelight_view_correction(context.scene)
        return {'FINISHED'}
