# INU_tools.ops.animobj_ops
# "Animated Map Object" workflow — windmills, cranes, wheels of fortune,
# any static map prop with a single rotating part.
#
# In GTA SA an animated map object needs three coordinated artefacts:
#   1. DFF with a 1-bone armature, all verts weighted to that bone
#   2. IFP with one Action (e.g. cyclic Z-rotation 0°→360° over 60 frames)
#   3. IDE 'anim' entry: ID, modelname, txdname, animname, drawdist, flags
#
# The trio has to land on disk with matching names and the IDE entry has
# to be wired up — easy to misconfigure step-by-step in Blender. This
# module collapses the whole chain into three operators:
#   - animobj_setup: builds the rig from scratch on the active mesh
#   - animobj_export: writes DFF + IFP + upserts IDE anim row
#   - animobj_validate: pre-flight checks (rig, weights, action, names)

import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty
import math
import os

from .. import T
from ..tools.compat import safe_icon


# ── Live-edit PropertyGroup ──────────────────────────────────────
# After Setup-rig the user gets sliders in the Anim panel that
# regenerate the action's keyframes on the fly. Each property has an
# update callback that calls _rebuild_animobj_action — no Action
# Editor / Graph Editor needed for routine speed/length tweaks.

def _rebuild_animobj_action(arm_obj):
    """Idempotently rewrite the rig's action so it matches the props.
    Clears the bone's existing rotation_euler keyframes first to avoid
    leftover keyframes when ``duration_frames`` shrinks."""
    if arm_obj is None or arm_obj.type != 'ARMATURE':
        return
    props = arm_obj.inu_animobj_props
    if not props.bone_name:
        return

    ad = arm_obj.animation_data
    if ad is None or ad.action is None:
        return
    action = ad.action

    pb = arm_obj.pose.bones.get(props.bone_name)
    if pb is None:
        return

    # Drop every fcurve that targets this bone's rotation_euler. We can't
    # rely on keyframe_insert overwriting because the user may have
    # shrunk duration — old end-frame would linger as a stale keyframe.
    target_path = f'pose.bones["{props.bone_name}"].rotation_euler'
    _strip_fcurves_at_path(action, target_path)

    # Re-insert the two boundary keyframes.
    sign = -1.0 if props.reverse else 1.0
    total_radians = sign * props.turns_per_cycle * 2.0 * math.pi
    axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[props.axis]

    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0.0, 0.0, 0.0)
    pb.keyframe_insert(data_path="rotation_euler",
                       frame=1, group=props.bone_name)

    end_rot = [0.0, 0.0, 0.0]
    end_rot[axis_idx] = total_radians
    pb.rotation_euler = tuple(end_rot)
    pb.keyframe_insert(data_path="rotation_euler",
                       frame=max(2, props.duration_frames),
                       group=props.bone_name)

    pb.rotation_euler = (0.0, 0.0, 0.0)


def _strip_fcurves_at_path(action, data_path):
    """Remove every fcurve in *action* whose data_path == *data_path*.
    Walks both legacy ``Action.fcurves`` (4.x) and the layered
    ``slots × layers → strips → channelbag → fcurves`` tree (4.4+/5.x)."""
    legacy = getattr(action, 'fcurves', None)
    if legacy is not None:
        for fc in list(legacy):
            if fc.data_path == data_path:
                try:
                    legacy.remove(fc)
                except Exception:
                    pass
        return

    slots = getattr(action, 'slots', None)
    layers = getattr(action, 'layers', None)
    if not slots or not layers:
        return
    for layer in layers:
        for strip in getattr(layer, 'strips', []):
            cbag_fn = getattr(strip, 'channelbag', None)
            if cbag_fn is None:
                continue
            for slot in slots:
                cb = cbag_fn(slot)
                if cb is None:
                    continue
                fcurves = getattr(cb, 'fcurves', None)
                if fcurves is None:
                    continue
                for fc in list(fcurves):
                    if fc.data_path == data_path:
                        try:
                            fcurves.remove(fc)
                        except Exception:
                            pass


def _on_animobj_prop_update(self, context):
    """Property update callback — fires when any slider in
    INUAnimObjProps changes, rebuilds the action's keyframes and
    syncs the scene's frame_end so the timeline shows the full loop.

    No-op when the rig is in MANUAL mode — that mode hands keyframe
    management entirely to the user, so a slider edit must NOT clobber
    whatever they're hand-editing in Action Editor."""
    obj = self.id_data  # The Object owning this PropertyGroup
    if obj is None or not obj.get('inu_animobj'):
        return
    props = obj.inu_animobj_props
    if not props.auto_mode:
        return
    _rebuild_animobj_action(obj)

    # Stretch the scene timeline to fit the cycle. Without this the
    # timeline ruler still ends at frame 250 even though the action
    # now needs 207 frames — the user has to scrub past the end and
    # gets confused why the animation "stops".
    scene = context.scene
    scene.frame_start = 1
    scene.frame_end = max(2, props.duration_frames)


def _on_auto_mode_toggle(self, context):
    """Switching MANUAL → AUTO regenerates keyframes from the slider
    values (effectively reverts hand-edits). MANUAL → AUTO never
    happens silently — the user explicitly clicked the toggle, so we
    treat their click as consent to overwrite. Switching AUTO → MANUAL
    is harmless: keyframes stay where they are, sliders just stop
    rebuilding on change."""
    obj = self.id_data
    if obj is None or not obj.get('inu_animobj'):
        return
    props = obj.inu_animobj_props
    if props.auto_mode:
        _rebuild_animobj_action(obj)
        scene = context.scene
        scene.frame_start = 1
        scene.frame_end = max(2, props.duration_frames)


class INUAnimObjProps(bpy.types.PropertyGroup):
    """Per-rig settings persisted on the armature Object. Drives the
    live keyframe regeneration on slider edits in the Anim panel."""
    auto_mode: bpy.props.BoolProperty(
        name=T("Auto"),
        description=T(
            "Auto: ползунки сами пересчитывают keyframes цикла.\n"
            "Manual: ползунки заморожены, ты сам ставишь keyframes "
            "в Action Editor / Pose Mode. Переключение Manual→Auto "
            "перезапишет твои ключи значениями ниже"),
        default=True,
        update=_on_auto_mode_toggle,
    )
    bone_name: StringProperty(
        name=T("Имя кости"),
        description=T(
            "Имя кости которую крутит rig. Меняется только если ты "
            "переименовал кость вручную в Edit Mode скелета"),
        default="blades_bone",
        update=_on_animobj_prop_update,
    )
    axis: EnumProperty(
        name=T("Ось"),
        items=[('X', "X", ""), ('Y', "Y", ""), ('Z', "Z", "")],
        default='Z',
        update=_on_animobj_prop_update,
    )
    reverse: bpy.props.BoolProperty(
        name=T("В обратную сторону"),
        description=T(
            "Крутить против часовой стрелки (с точки зрения +оси). "
            "Удобно если меш вышел зеркальным или физика подразумевает "
            "вращение в другую сторону"),
        default=False,
        update=_on_animobj_prop_update,
    )
    turns_per_cycle: IntProperty(
        name=T("Оборотов за цикл"),
        description=T(
            "Целое число полных оборотов за анимацию. Цикл "
            "проигрывается повторно — модель возвращается в "
            "стартовую позицию точно (без визуального рывка)"),
        default=1, min=1, soft_max=20,
        update=_on_animobj_prop_update,
    )
    duration_frames: IntProperty(
        name=T("Длительность (кадров)"),
        description=T(
            "Длина цикла в кадрах. Скорость = "
            "обороты_за_цикл × fps_сцены / длительность"),
        default=60, min=2, soft_max=600,
        update=_on_animobj_prop_update,
    )


def _iter_action_fcurves(action):
    """Yield every fcurve in an Action across both Blender APIs.

    Pre-4.4 keeps fcurves on the Action root (``action.fcurves``).
    4.4+ moved them into the layered system: Action → slots × layers
    → strips → channelbag(slot) → fcurves. We unify both so callers
    don't have to branch on bpy.app.version every time they want to
    count keyframes.
    """
    legacy = getattr(action, 'fcurves', None)
    if legacy is not None:
        for fc in legacy:
            yield fc
        return
    slots = getattr(action, 'slots', None)
    layers = getattr(action, 'layers', None)
    if not slots or not layers:
        return
    for layer in layers:
        for strip in getattr(layer, 'strips', []):
            cbag_fn = getattr(strip, 'channelbag', None)
            if cbag_fn is None:
                continue
            for slot in slots:
                cb = cbag_fn(slot)
                if cb is None:
                    continue
                for fc in getattr(cb, 'fcurves', []):
                    yield fc


# ── Setup wizard ──────────────────────────────────────────────────

class GTATOOLS_OT_animobj_setup(bpy.types.Operator):
    """Создать рiг для animated map object (мельница, кран, флюгер):
    Armature с одной костью + Action с цикличной Z-вращением.

    Все вершины активного меша автоматически привязываются к
    единственной кости (vertex group weight=1.0). Готово к экспорту в
    DFF + IFP без ручной настройки скелета."""
    bl_idname = "gtatools.animobj_setup"
    bl_label = "INU: Animated Object Setup"
    bl_options = {'REGISTER', 'UNDO'}

    bone_name: StringProperty(
        name=T("Имя кости"),
        description=T(
            "Имя кости — попадёт в DFF Frame name и в IFP bone-track. "
            "Принято использовать что-то описательное: blades, propeller, gear..."),
        default="blades_bone",
    )
    action_name: StringProperty(
        name=T("Имя action"),
        description=T(
            "Имя Blender Action — попадёт в IFP как имя анимации. Игра "
            "ищет анимацию по этому имени из IDE anim entry"),
        default="windmill",
    )
    axis: EnumProperty(
        name=T("Ось вращения"),
        items=[('X', "X", ""), ('Y', "Y", ""), ('Z', "Z", "")],
        default='Z',
    )
    turns_per_cycle: IntProperty(
        name=T("Оборотов за цикл"),
        description=T(
            "Целое число полных оборотов за анимацию. Игра проигрывает "
            "цикл повторно — модель возвращается в стартовую позицию "
            "точно (без визуального рывка на стыке)"),
        default=1, min=1, soft_max=20,
    )
    duration_frames: IntProperty(
        name=T("Длительность (кадров)"),
        description=T(
            "Длина цикла в кадрах. Скорость вращения = "
            "оборотов_за_цикл / длительность × fps_сцены"),
        default=60, min=2, soft_max=600,
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None
                and context.active_object.type == 'MESH')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=380)

    def draw(self, context):
        col = self.layout.column()
        col.prop(self, "bone_name")
        col.prop(self, "action_name")
        col.prop(self, "axis")
        col.prop(self, "turns_per_cycle")
        col.prop(self, "duration_frames")

        # Show derived RPM as a hint so the user can sanity-check the
        # speed without doing the math themselves.
        fps = max(1, context.scene.render.fps)
        rpm = self.turns_per_cycle * fps / max(1, self.duration_frames)
        col.label(
            text=f"≈ {rpm:.2f} {T('оборотов/сек при FPS')} {fps}",
            icon=safe_icon('INFO'))

        col.label(
            text=T("Все вершины меша получат weight=1.0 на эту кость"),
            icon=safe_icon('INFO'))
        col.label(
            text=T("Цикл точно зацикливается (целое число оборотов)"),
            icon=safe_icon('LOOP_BACK'))

    def execute(self, context):
        mesh_obj = context.active_object
        if mesh_obj is None or mesh_obj.type != 'MESH':
            self.report({'ERROR'}, T("Выделите MESH"))
            return {'CANCELLED'}

        # ── 1) Armature with one bone at mesh origin ──
        arm_data = bpy.data.armatures.new(f"{mesh_obj.name}_armature")
        arm_obj = bpy.data.objects.new(f"{mesh_obj.name}_armature", arm_data)
        arm_obj.location = mesh_obj.location.copy()

        # Same collection as the mesh
        for col in mesh_obj.users_collection:
            col.objects.link(arm_obj)

        # Edit-mode bone creation
        prev_active = context.view_layer.objects.active
        context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')
        bone = arm_data.edit_bones.new(self.bone_name)
        bone.head = (0.0, 0.0, 0.0)
        # Pointing along Z so Z-rotation is the visual axis the user
        # picked (most windmill rigs spin around Z).
        bone.tail = (0.0, 0.0, 1.0)
        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = prev_active

        # ── 2) Vertex group on mesh, all verts → weight 1.0 ──
        vg = mesh_obj.vertex_groups.get(self.bone_name)
        if vg is None:
            vg = mesh_obj.vertex_groups.new(name=self.bone_name)
        vg.add(list(range(len(mesh_obj.data.vertices))), 1.0, 'REPLACE')

        # Armature modifier (or update existing)
        mod = next(
            (m for m in mesh_obj.modifiers if m.type == 'ARMATURE'), None)
        if mod is None:
            mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
        mod.object = arm_obj

        # Parent mesh to armature (keep transform — armature is at mesh origin)
        mesh_obj.parent = arm_obj
        mesh_obj.matrix_parent_inverse.identity()

        # ── 3) Cyclic rotation Action ──
        # Blender 4.4+ moved fcurves out of Action root into the new
        # layered animation system. action.fcurves.new() is gone in 5.x.
        # Workaround: assign an empty action to the armature first, then
        # use pose_bone.keyframe_insert() — that high-level path
        # auto-creates whatever slot/layer/channelbag plumbing the
        # current Blender version needs, in 4.x it just writes fcurves.
        action = bpy.data.actions.new(self.action_name)
        action.use_fake_user = True

        if arm_obj.animation_data is None:
            arm_obj.animation_data_create()
        arm_obj.animation_data.action = action

        # End-rotation = exactly N full turns. Integer turns → mesh
        # ends at the same orientation it started → seamless loop.
        total_radians = self.turns_per_cycle * 2.0 * math.pi

        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[self.axis]

        pb = arm_obj.pose.bones.get(self.bone_name)
        if pb is None:
            self.report({'ERROR'},
                        f"{T('Не найдена кость')} {self.bone_name}")
            return {'CANCELLED'}

        # Frame 1: zero rotation
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert(data_path="rotation_euler",
                           frame=1, group=self.bone_name)

        # Last frame: total_radians on chosen axis
        end_rot = [0.0, 0.0, 0.0]
        end_rot[axis_idx] = total_radians
        pb.rotation_euler = tuple(end_rot)
        pb.keyframe_insert(data_path="rotation_euler",
                           frame=self.duration_frames,
                           group=self.bone_name)

        # Reset back to zero so the bone visually starts at origin
        pb.rotation_euler = (0.0, 0.0, 0.0)

        # Tag for our IFP exporter so the action survives 'Save Materials'
        # and similar bulk operations that strip metadata.
        action['ifp_source'] = self.action_name

        # Tag the rig so animobj_export can find it without UI guessing.
        arm_obj['inu_animobj'] = True

        # Mirror operator inputs onto the rig's PropertyGroup so the
        # live-edit sliders in the Anim panel show the right starting
        # values (and keep working even after the user closes / reopens
        # Blender — the props persist on the Object).
        # The .duration_frames assignment fires the update callback,
        # which both rebuilds keyframes (already there from the manual
        # keyframe_insert above — gets cleanly replaced) and syncs
        # scene.frame_end. Order matters: bone_name first so the
        # callback can find the pose bone.
        props = arm_obj.inu_animobj_props
        props.bone_name = self.bone_name
        props.axis = self.axis
        props.turns_per_cycle = self.turns_per_cycle
        props.duration_frames = self.duration_frames

        self.report({'INFO'},
                    f"{T('Animated rig готов')}: armature={arm_obj.name}, "
                    f"bone={self.bone_name}, action={self.action_name}")
        return {'FINISHED'}


# ── Validator ─────────────────────────────────────────────────────

class GTATOOLS_OT_animobj_validate(bpy.types.Operator):
    """Проверить настройку animated map object перед экспортом:
    есть ли armature, привязан ли меш, заданы ли веса, есть ли action,
    цикличный ли он. Лог проблем в System Console."""
    bl_idname = "gtatools.animobj_validate"
    bl_label = "INU: Validate Animated Object"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        problems = []
        warns = []

        obj = context.active_object
        # Find the armature: either active object IS one, or its parent is.
        if obj.type == 'ARMATURE':
            arm = obj
            mesh = next(
                (c for c in arm.children if c.type == 'MESH'), None)
        elif obj.type == 'MESH':
            mesh = obj
            arm = (obj.parent if obj.parent and obj.parent.type == 'ARMATURE'
                   else None)
            if arm is None:
                # Maybe the mesh has an Armature modifier instead
                for m in mesh.modifiers:
                    if m.type == 'ARMATURE' and m.object:
                        arm = m.object
                        break
        else:
            problems.append(T("Активный объект — не MESH и не ARMATURE"))
            arm, mesh = None, None

        if arm is None:
            problems.append(T("Нет Armature — animated object без скелета не работает"))
        if mesh is None:
            problems.append(T("Нет MESH"))

        if arm and mesh:
            # Bones present?
            bones = list(arm.data.bones)
            if not bones:
                problems.append(T("В скелете 0 костей"))

            # Vertex groups cover the bones?
            vg_names = {vg.name for vg in mesh.vertex_groups}
            missing_vgs = [b.name for b in bones if b.name not in vg_names]
            if missing_vgs:
                warns.append(
                    f"{T('Кости без vertex group:')} {', '.join(missing_vgs)}")

            # Armature modifier present and pointing to arm?
            mods = [m for m in mesh.modifiers if m.type == 'ARMATURE']
            if not mods:
                problems.append(T("На MESH нет Armature modifier"))
            elif not any(m.object is arm for m in mods):
                warns.append(T("Armature modifier указывает на другой скелет"))

            # Action assigned?
            ad = arm.animation_data
            action = ad.action if ad else None
            if action is None:
                problems.append(T("К armature не привязан Action"))
            else:
                # Cyclic? (length > 1, more than one keyframe per fcurve)
                non_trivial = any(
                    len(fc.keyframe_points) >= 2
                    for fc in _iter_action_fcurves(action))
                if not non_trivial:
                    problems.append(
                        T("В Action меньше 2 keyframe — анимации нет"))

                # Action name should match what IDE anim entry references
                if not action.name.replace('_', '').isalnum():
                    warns.append(T(
                        "Имя Action содержит спецсимволы — IDE entry может не сработать"))

        # Always log to console
        print(f"[animobj_validate] obj={obj.name if obj else '<none>'}")
        for p in problems:
            print(f"  ! {p}")
        for w in warns:
            print(f"  ? {w}")
        if not problems and not warns:
            print("  OK — всё готово к экспорту")

        if problems:
            self.report({'ERROR'},
                        f"{T('Ошибок')}: {len(problems)}, "
                        f"{T('предупреждений')}: {len(warns)} "
                        f"({T('см. System Console')})")
        elif warns:
            self.report({'WARNING'},
                        f"{T('Предупреждений')}: {len(warns)} "
                        f"({T('см. System Console')})")
        else:
            self.report({'INFO'}, T("Animated object готов к экспорту"))
        return {'FINISHED'}


# ── Combo export ──────────────────────────────────────────────────

class GTATOOLS_OT_animobj_export(bpy.types.Operator):
    """Экспортировать animated map object одним кликом: пишет
    <base>.dff + <base>.ifp в выбранную папку. Опционально дописывает
    или обновляет anim-запись в указанном IDE-файле."""
    bl_idname = "gtatools.animobj_export"
    bl_label = "INU: Export Animated Object"
    bl_options = {'REGISTER'}

    directory: StringProperty(
        name=T("Папка"), subtype='DIR_PATH',
        description=T("Куда положить .dff и .ifp"),
    )
    base_name: StringProperty(
        name=T("Базовое имя"),
        description=T("Имя файлов без расширения (например 'mill')"),
        default="mill",
    )
    txd_name: StringProperty(
        name=T("TXD"),
        description=T("Имя TXD для IDE entry (обычно совпадает с base_name)"),
        default="mill",
    )
    model_id: IntProperty(
        name=T("Model ID"),
        description=T(
            "ID модели для IDE — должен быть свободен в карте.\n"
            "0 = не задан (исправь в Object Properties → INU Tools → Model ID)"),
        default=18000, min=0, max=65535,
    )
    draw_distance: FloatProperty(
        name=T("Draw distance"),
        default=300.0, min=10.0, soft_max=2000.0,
    )
    write_ide: bpy.props.BoolProperty(
        name=T("Дописать IDE entry"),
        description=T("Добавить anim-запись в IDE-файл, заданный в Scene → INU Tools → IDE Path"),
        default=True,
    )
    ifp_name: StringProperty(
        name=T("Имя IFP"),
        description=T(
            "Базовое имя для .ifp (без расширения). Пусто = взять "
            "из «Базовое имя». Можно ввести общее имя типа "
            "'myhood_anims' чтобы складывать анимации мельницы, "
            "крана и флюгера в один файл"),
        default="",
    )
    ifp_mode: EnumProperty(
        name=T("Режим IFP"),
        description=T(
            "Что делать если такой .ifp уже существует на диске"),
        items=[
            ('NEW',    T("Новый"),
             T("Перезаписать файл — старые анимации удаляются")),
            ('APPEND', T("Дополнить"),
             T("Подгрузить существующий, добавить новые анимации, "
               "заменить с тем же именем")),
            ('UPDATE', T("Обновить совпадения"),
             T("Подгрузить существующий, заменить ТОЛЬКО анимации "
               "с совпадающим именем, новые НЕ добавлять")),
        ],
        default='APPEND',
    )
    ifp_format: EnumProperty(
        name=T("Формат IFP"),
        items=[
            ('ANPK', "ANPK / ANP2 (III, VC, SA)", ""),
            ('ANP3', "ANP3 (SA compressed)", ""),
        ],
        default='ANPK',
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        # Resolve the rig + its first mesh child the same way execute()
        # does — keeps invoke pre-fill consistent with what gets used
        # at write time.
        active = context.active_object
        arm = mesh = None
        if active is not None:
            if active.type == 'ARMATURE':
                arm = active
                mesh = next(
                    (c for c in arm.children if c.type == 'MESH'), None)
            elif active.type == 'MESH':
                mesh = active
                if (active.parent and active.parent.type == 'ARMATURE'):
                    arm = active.parent
                else:
                    for m in mesh.modifiers:
                        if m.type == 'ARMATURE' and m.object:
                            arm = m.object
                            break

        # Pre-fill names from the rig's action (Setup wizard puts the
        # action name in arm.animation_data.action — that's the IFP
        # anim name and a sensible default file basename too).
        if arm is not None:
            ad = arm.animation_data
            if ad and ad.action:
                self.base_name = ad.action.name
                self.txd_name = ad.action.name

        # Pre-fill model-side fields from mesh.inu so the user's earlier
        # choices in Object Properties (Model ID, Draw Distance, TXD
        # Name) propagate without retyping. We copy unconditionally —
        # even mesh defaults (model_id=0, draw_distance=299) are the
        # user's truth; surfacing 18000 when the mesh says 0 was
        # actively misleading.
        if mesh is not None:
            inu = getattr(mesh, 'inu', None)
            if inu is not None:
                self.model_id = inu.model_id
                self.draw_distance = inu.draw_distance
                if inu.txd_name:
                    self.txd_name = inu.txd_name

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        col = self.layout.column()

        # Show which Action will be exported as the IFP animation —
        # the user otherwise has no visual confirmation that the right
        # animation is selected (active armature could have a stale
        # action assigned from a previous import).
        active = context.active_object
        anim_name = None
        for candidate in (active,
                          active.parent if active else None):
            if (candidate and candidate.type == 'ARMATURE'
                    and candidate.animation_data
                    and candidate.animation_data.action):
                anim_name = candidate.animation_data.action.name
                break
        if anim_name:
            col.label(
                text=f"{T('Анимация')}: {anim_name}",
                icon=safe_icon('ACTION'))
        else:
            col.label(
                text=T("Нет Action на armature — IFP будет пустой"),
                icon=safe_icon('ERROR'))

        col.separator()
        col.prop(self, "directory")
        col.prop(self, "base_name")
        col.prop(self, "txd_name")
        col.prop(self, "model_id")
        if self.model_id == 0:
            col.label(
                text=T("Model ID = 0 — задай в Object Properties → "
                       "INU Tools → Model ID"),
                icon=safe_icon('ERROR'))
        col.prop(self, "draw_distance")

        # ── IFP file naming + write strategy ──
        # Most common pattern: artist exports several rigs (mill +
        # crane + flag) over time but wants them in a single shared
        # myhood_anims.ifp. Default mode APPEND lets every
        # subsequent export grow the file safely.
        ifp_box = col.box()
        ifp_box.label(text=T("IFP файл"), icon=safe_icon('ACTION'))
        # Show resolved filename next to the input — user can sanity-
        # check that it'll go where they expect.
        resolved = (self.ifp_name.strip() or self.base_name.strip()
                    or "<пусто>")
        ifp_box.prop(self, "ifp_name", text=T("Имя"))
        ifp_box.label(
            text=f"→ {resolved}.ifp", icon=safe_icon('FILE_BLANK'))
        ifp_box.prop(self, "ifp_mode", text=T("Режим"))
        ifp_box.prop(self, "ifp_format")

        col.prop(self, "write_ide")
        if self.write_ide:
            ide_path = getattr(context.scene, 'gtatools_ide_path', '')
            if ide_path:
                col.label(text=f"IDE: {ide_path}", icon=safe_icon('TEXT'))
            else:
                col.label(text=T(
                    "Scene → INU Tools → IDE Path не задан — "
                    "anim-запись не будет дописана"),
                    icon=safe_icon('ERROR'))

    def execute(self, context):
        if not self.directory or not os.path.isdir(self.directory):
            self.report({'ERROR'}, T("Укажите существующую папку"))
            return {'CANCELLED'}
        base = self.base_name.strip()
        if not base:
            self.report({'ERROR'}, T("Базовое имя не может быть пустым"))
            return {'CANCELLED'}

        # Resolve mesh and armature like the validator does.
        active = context.active_object
        if active.type == 'ARMATURE':
            arm = active
            mesh = next(
                (c for c in arm.children if c.type == 'MESH'), None)
        elif active.type == 'MESH':
            mesh = active
            arm = (active.parent
                   if active.parent and active.parent.type == 'ARMATURE'
                   else None)
            if arm is None:
                for m in mesh.modifiers:
                    if m.type == 'ARMATURE' and m.object:
                        arm = m.object
                        break
        else:
            self.report({'ERROR'}, T("Выделите MESH или ARMATURE"))
            return {'CANCELLED'}

        if mesh is None or arm is None:
            self.report({'ERROR'},
                        T("Не нашли пару MESH+ARMATURE — запустите Validate"))
            return {'CANCELLED'}

        # IFP filename: user override wins, else fall back to base_name.
        # Useful for shared "myhood_anims.ifp" across many rigs.
        ifp_basename = self.ifp_name.strip() or base
        dff_path = os.path.join(self.directory, f"{base}.dff")
        ifp_path = os.path.join(self.directory, f"{ifp_basename}.ifp")

        # ── DFF: select arm + mesh, run gtatools.export_dff with filepath ──
        # We reuse the existing operator instead of duplicating its logic
        # (skinning, MatFX, breakable, …) — it expects a non-empty
        # selection and an active object, so we set both deterministically.
        for o in bpy.data.objects:
            o.select_set(False)
        arm.select_set(True)
        mesh.select_set(True)
        context.view_layer.objects.active = arm
        try:
            bpy.ops.gtatools.export_dff(
                'EXEC_DEFAULT', filepath=dff_path)
        except Exception as ex:
            self.report({'ERROR'}, f"DFF: {ex}")
            return {'CANCELLED'}

        # ── IFP: build directly from arm's action via core.ifp ──
        # Bypass the file-dialog operator and call the helper module so
        # we can pass a fixed path and skip user-prompts.
        ifp_msg = ""
        try:
            from .ifp_export import build_ifp_from_actions
            from ..core.ifp import write_ifp, read_ifp, IFPFile
            new_ifp = build_ifp_from_actions(
                armature=arm, package_name=ifp_basename)
            if not new_ifp.animations:
                self.report({'WARNING'},
                            T("В action нет ключей — IFP не записан"))
            else:
                # Merge strategy depends on ifp_mode + whether the
                # target file already exists. APPEND/UPDATE need to
                # load the old IFP first; NEW just overwrites.
                target_ifp = new_ifp
                file_exists = os.path.isfile(ifp_path)
                if file_exists and self.ifp_mode in ('APPEND', 'UPDATE'):
                    try:
                        existing = read_ifp(ifp_path)
                    except Exception as ex:
                        self.report({'WARNING'},
                                    f"IFP read failed, "
                                    f"{T('перезаписываю')}: {ex}")
                        existing = IFPFile(name=ifp_basename)

                    by_name = {a.name: a for a in existing.animations}
                    new_names = {a.name for a in new_ifp.animations}

                    if self.ifp_mode == 'APPEND':
                        # Replace anims with same name + add new ones
                        for a in new_ifp.animations:
                            by_name[a.name] = a
                    else:  # UPDATE
                        # Replace ONLY existing names — drop brand-new
                        for a in new_ifp.animations:
                            if a.name in by_name:
                                by_name[a.name] = a
                            # else silently skip — that's the contract

                    target_ifp = IFPFile(
                        name=existing.name or ifp_basename,
                        animations=list(by_name.values()),
                        source_format=existing.source_format,
                    )

                # write_ifp param is `format`, not `fmt` — passing
                # `fmt=` would TypeError. Be explicit.
                write_ifp(ifp_path, target_ifp,
                          format=self.ifp_format)

                action_count = len(new_ifp.animations)
                if file_exists and self.ifp_mode != 'NEW':
                    ifp_msg = f" ({self.ifp_mode.lower()}, +{action_count})"
                else:
                    ifp_msg = f" ({action_count})"
        except Exception as ex:
            self.report({'ERROR'}, f"IFP: {ex}")
            return {'CANCELLED'}

        # ── IDE anim entry (optional) ──
        ide_msg = ""
        if self.write_ide and self.model_id == 0:
            self.report({'WARNING'},
                        T("Model ID = 0 — IDE entry пропущена"))
        elif self.write_ide:
            ide_path = getattr(context.scene, 'gtatools_ide_path', '')
            ide_path = bpy.path.abspath(ide_path) if ide_path else ""
            if ide_path and os.path.isfile(ide_path):
                try:
                    from ..core.ide import (
                        read_ide, write_ide, IdeAnim,
                    )
                    ide = read_ide(ide_path)
                    # Action-name as anim_file (game looks up by anim name)
                    anim_action_name = base
                    new_entry = IdeAnim(
                        model_id=self.model_id,
                        model_name=base,
                        txd_name=self.txd_name or base,
                        anim_file=anim_action_name,
                        draw_distance=self.draw_distance,
                        flags=0,
                    )
                    # Replace existing entry with same model_id, else append
                    for i, a in enumerate(ide.anims):
                        if a.model_id == self.model_id:
                            ide.anims[i] = new_entry
                            break
                    else:
                        ide.anims.append(new_entry)
                    write_ide(ide_path, ide)
                    ide_msg = f", IDE+1"
                except Exception as ex:
                    self.report({'WARNING'}, f"IDE: {ex}")
            else:
                self.report({'WARNING'},
                            T("IDE path не задан — anim-запись пропущена"))

        self.report({'INFO'},
                    f"{base}.dff + {ifp_basename}.ifp{ifp_msg}{ide_msg}")
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_animobj_setup,
    GTATOOLS_OT_animobj_validate,
    GTATOOLS_OT_animobj_export,
)
