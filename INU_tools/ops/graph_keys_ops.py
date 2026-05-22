"""Graph-editor N-panel: keyframe thinning utilities.

Adds a sidebar panel with one button that decimates selected keyframes:
either keeps every Nth selected key (stride mode), or removes redundant
keys whose value is interpolated by neighbours within an error margin
(auto mode, delegates to ``bpy.ops.graph.decimate(mode='ERROR')``).
"""

import bpy
from bpy.props import EnumProperty, IntProperty, FloatProperty
from .. import T


def _iter_fcurves(obj):
    """Yield ``FCurve`` objects from active action, handling both the
    pre-4.4 flat ``action.fcurves`` and the 4.4+ slotted layered model
    (``action.layers[].strips[].channelbag(slot).fcurves``)."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    action = ad.action
    # Pre-4.4: flat fcurves list
    fc_attr = getattr(action, 'fcurves', None)
    if fc_attr is not None:
        for fcu in fc_attr:
            yield fcu
        return
    # 4.4+: slotted action. Pull fcurves from the slot bound to this
    # animation_data (every channelbag belongs to one slot — using the
    # object's own slot avoids touching other datablocks that share
    # this action).
    slot = getattr(ad, 'action_slot', None)
    for layer in getattr(action, 'layers', ()):
        for strip in getattr(layer, 'strips', ()):
            cb = None
            try:
                if slot is not None and hasattr(strip, 'channelbag'):
                    cb = strip.channelbag(slot)
            except Exception:
                cb = None
            if cb is None:
                # Fallback — iterate every channelbag attached to this strip
                for c in getattr(strip, 'channelbags', ()):
                    for fcu in getattr(c, 'fcurves', ()):
                        yield fcu
                continue
            for fcu in getattr(cb, 'fcurves', ()):
                yield fcu


def _stride_delete(stride: int) -> int:
    """Cleaner stride deletion via direct keyframe_points.remove."""
    if stride < 2:
        return 0
    obj = bpy.context.active_object
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return 0
    deleted = 0
    for fcu in _iter_fcurves(obj):
        if fcu.hide or fcu.lock:
            continue
        kps = fcu.keyframe_points
        selected_idx = [i for i, kp in enumerate(kps) if kp.select_control_point]
        if len(selected_idx) < 3:
            continue
        keep = set(selected_idx[::stride])
        to_remove = [i for i in selected_idx if i not in keep]
        # Iterate from the end so indices don't shift
        for i in reversed(to_remove):
            kps.remove(kps[i], fast=True)
            deleted += 1
        fcu.update()
    return deleted


class GTATOOLS_OT_thin_keyframes(bpy.types.Operator):
    """Прореживание выделенных ключей. Stride — оставить каждый N-ный
    ключ. Auto — удалить ключи которые лежат на прямой между соседями
    (избыточные)."""
    bl_idname = "gtatools.thin_keyframes"
    bl_label = "Проредить ключи"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(
        name="Режим",
        items=[
            ('NTH',  "Каждый N-ный",
             "Оставить каждый N-ный из выделенных ключей, остальные удалить"),
            ('AUTO', "Авто (по ошибке)",
             "Удалить избыточные ключи, лежащие близко к интерполяции "
             "между соседями (Blender'овский decimate ERROR-mode)"),
        ],
        default='NTH',
    )

    stride: IntProperty(
        name="N",
        description="Оставить каждый N-ный ключ (2 = удалить каждый второй)",
        default=2, min=2, max=20,
    )

    error: FloatProperty(
        name="Порог ошибки",
        description="Чем выше — тем агрессивнее срез избыточных ключей",
        default=0.01, min=0.0001, max=1.0, precision=4,
    )

    interp: EnumProperty(
        name="Интерполяция",
        items=[
            ('BEZIER',   "Безье",      "Плавная кривая между ключами"),
            ('LINEAR',   "Линейная",   "Прямые линии между ключами"),
            ('CONSTANT', "Постоянная", "Ступенька"),
        ],
        default='BEZIER',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bool(obj and obj.animation_data and obj.animation_data.action)

    def _apply_interp_to_selected(self):
        """Set interpolation type on every remaining selected key."""
        obj = bpy.context.active_object
        if not obj or not obj.animation_data or not obj.animation_data.action:
            return 0
        n = 0
        for fcu in _iter_fcurves(obj):
            if fcu.hide or fcu.lock:
                continue
            for kp in fcu.keyframe_points:
                if kp.select_control_point:
                    kp.interpolation = self.interp
                    n += 1
            fcu.update()
        return n

    def execute(self, context):
        obj = context.active_object
        # Diagnostic: dump what we actually see — counts of fcurves
        # and selected keys per curve. Helps when 5.1 slotted-action
        # API returns nothing we can iterate.
        fcs = list(_iter_fcurves(obj)) if obj else []
        sel_total = sum(
            sum(1 for kp in f.keyframe_points if kp.select_control_point)
            for f in fcs
        )
        print(f"[INU thin] obj={obj.name if obj else None} "
              f"fcurves={len(fcs)} selected_keys={sel_total} "
              f"mode={self.mode} stride={self.stride} interp={self.interp}")
        if fcs and sel_total == 0:
            self.report({'WARNING'},
                T("Нет выделенных ключей. Выдели нужные ключи в Graph Editor."))
            return {'CANCELLED'}
        if not fcs:
            ad = obj.animation_data if obj else None
            print(f"[INU thin] animation_data={ad} "
                  f"action={getattr(ad, 'action', None) if ad else None} "
                  f"slot={getattr(ad, 'action_slot', None) if ad else None}")
            self.report({'WARNING'},
                T("Не нашёл F-curve'ы — выбери анимированный объект."))
            return {'CANCELLED'}

        if self.mode == 'NTH':
            n = _stride_delete(self.stride)
            m = self._apply_interp_to_selected()
            self.report({'INFO'},
                f"{T('Удалено ключей: ')}{n}{T(', интерполяция применена к ')}{m}")
        else:
            try:
                bpy.ops.graph.decimate(mode='ERROR',
                                       remove_error_margin=self.error)
            except RuntimeError as e:
                self.report({'ERROR'}, f"Не получилось вызвать decimate: {e}. "
                                       f"Активируй окно Graph Editor.")
                return {'CANCELLED'}
            m = self._apply_interp_to_selected()
            self.report({'INFO'},
                f"{T('Auto-decimate выполнен, интерполяция применена к ')}{m}")
        return {'FINISHED'}


class GTATOOLS_PT_graph_thin_keys(bpy.types.Panel):
    """N-panel в Graph Editor с прореживанием ключей."""
    bl_label = "INU Tools"
    bl_idname = "GTATOOLS_PT_graph_thin_keys"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = "INU Tools"

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        s = scn.inu_settings

        box = layout.box()
        box.label(text=T("Проредить выделенные ключи"))
        box.prop(s, "gtatools_thin_keys_mode", expand=True)

        if s.gtatools_thin_keys_mode == 'NTH':
            row = box.row(align=True)
            row.prop(s, "gtatools_thin_keys_stride")
        else:
            row = box.row(align=True)
            row.prop(s, "gtatools_thin_keys_error")

        box.label(text=T("Интерполяция оставшихся ключей:"))
        row = box.row(align=True)
        row.prop(s, "gtatools_thin_keys_interp", expand=True)

        op = box.operator("gtatools.thin_keyframes",
                          text=T("Применить"),
                          icon='IPO_BEZIER')
        op.mode   = s.gtatools_thin_keys_mode
        op.stride = s.gtatools_thin_keys_stride
        op.error  = s.gtatools_thin_keys_error
        op.interp = s.gtatools_thin_keys_interp


classes = (
    GTATOOLS_OT_thin_keyframes,
    GTATOOLS_PT_graph_thin_keys,
)
