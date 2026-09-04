# INU_tools.ops.texture_ops — Texture loading + drop + material check/cleanup/sort + lightmap UV2 + reset_transform.
#
# Phase 3 (2026-04-26): operators moved from __init__.py.

import os
import re as _re
import bpy
import numpy as np
from bpy.props import (
    StringProperty, BoolProperty, CollectionProperty,
)

from .. import T
from ..tools import compat


# Alpha-detection thresholds. A texture is considered an "alpha texture"
# iff at least ALPHA_MIN_TRANSPARENT_PIXELS pixels have alpha below
# ALPHA_OPAQUE_THRESHOLD/255.
#
# Why two values:
#   - DXT decoder occasionally produces stray sub-255 alpha pixels from
#     block-quantization noise on fully opaque textures. A single-pixel
#     check would false-positive every DXT1 texture as alpha.
#   - Channel count alone (`img.channels == 4`) is useless: every
#     DXT-decoded image is RGBA8 by construction.
#
# Defaults: anything below ~98% opaque counts as transparent, and we
# need at least 10 such pixels (well above decoder noise, well below
# any real alpha texture which has hundreds-to-thousands).
#
# 1.8.x history: legacy threshold was 5000 pixels @ <0.95 — far too
# strict for typical 256×256 GTA fence/foliage textures, which have
# 1500-3000 transparent pixels and were silently failing the check.
ALPHA_OPAQUE_THRESHOLD = 250          # alpha < 250/255 → "transparent"
ALPHA_MIN_TRANSPARENT_PIXELS = 10     # min count to count as alpha texture

# Подробные [ALPHA]/[ALPHA-LINK] логи — диагностические, по строке на КАЖДЫЙ
# материал/изображение. На карте это сотни строк И тормозит из-за самих
# print(). По умолчанию выключено; True — для отладки «почему забор не
# прозрачный».
_ALPHA_VERBOSE = False

# Кэш вердикта «есть значимая альфа» по ИЗОБРАЖЕНИЮ. Десятки материалов-
# дубликатов (mat.001 … mat.014) ссылаются на одну текстуру — без кэша
# полный буфер image.pixels[:] (для 512×512 это ~1 млн float) читался бы и
# сканировался по разу на каждый материал. Ключ — имя+размер+каналы
# (метаданные, без чтения пикселей); значение — bool. Сбрасывается через
# clear_alpha_cache() при переимпорте, чтобы не залипал старый вердикт.
_ALPHA_SIG_CACHE = {}


def clear_alpha_cache():
    """Сбросить кэш альфа-вердиктов (вызывать при (пере)импорте текстур)."""
    _ALPHA_SIG_CACHE.clear()


def _alpha_cache_key(image):
    try:
        return (image.name, int(image.size[0]), int(image.size[1]), int(image.channels))
    except Exception:
        return (getattr(image, 'name', '?'),)


def image_has_significant_alpha(image) -> bool:
    """True iff ``image`` has at least ``ALPHA_MIN_TRANSPARENT_PIXELS``
    pixels with alpha below ``ALPHA_OPAQUE_THRESHOLD``/255. Used by the
    auto-link path to decide whether to wire the texture's Alpha output
    into the BSDF Alpha input.

    Результат кэшируется по изображению (см. ``_ALPHA_SIG_CACHE``), так что
    дорогое чтение пикселей выполняется ОДИН раз на текстуру, а не на каждый
    материал, который её использует."""
    if image is None:
        return False
    key = _alpha_cache_key(image)
    cached = _ALPHA_SIG_CACHE.get(key)
    if cached is not None:
        return cached
    if image.channels < 4:
        if _ALPHA_VERBOSE:
            print(f"[ALPHA] {image.name}: channels={image.channels}, no alpha")
        _ALPHA_SIG_CACHE[key] = False
        return False
    try:
        # Don't trust ``image.has_data`` — it returns False on
        # packed-only images right after ``pack()``, even when the
        # pixels are already accessible. Read pixels directly and let
        # any real failure raise.
        pixels_seq = image.pixels[:]
        if len(pixels_seq) == 0:
            # Пиксели ещё не загружены — НЕ кэшируем, чтобы пересчитать позже.
            if _ALPHA_VERBOSE:
                print(f"[ALPHA] {image.name}: pixels not loaded yet")
            return False
        pixels = np.asarray(pixels_seq, dtype=np.float32)
        alpha = pixels[3::4]
        threshold_f = ALPHA_OPAQUE_THRESHOLD / 255.0
        transparent_count = int(np.count_nonzero(alpha < threshold_f))
        is_alpha = transparent_count >= ALPHA_MIN_TRANSPARENT_PIXELS
        if _ALPHA_VERBOSE:
            print(f"[ALPHA] {image.name}: "
                  f"{transparent_count}/{alpha.size} pixels < {ALPHA_OPAQUE_THRESHOLD}/255 "
                  f"(min_a={alpha.min():.3f}), threshold={ALPHA_MIN_TRANSPARENT_PIXELS}, "
                  f"is_alpha={is_alpha}")
        _ALPHA_SIG_CACHE[key] = is_alpha
        return is_alpha
    except Exception as e:
        if _ALPHA_VERBOSE:
            print(f"[ALPHA] {getattr(image, 'name', '?')}: error {type(e).__name__}: {e}")
        return False


def _alog(msg):
    """Печать диагностики alpha-link только при включённом _ALPHA_VERBOSE."""
    if _ALPHA_VERBOSE:
        print(msg)


def link_material_alpha_if_textured(material) -> bool:
    """If ``material`` has a Principled BSDF and an Image Texture node,
    re-evaluate the Alpha link based on the image's actual pixel content:

      * image has transparent pixels → wire texture.Alpha → BSDF.Alpha
        (and switch the material to HASHED alpha-test for Eevee/Cycles)
      * image is opaque → remove any existing texture→Alpha link

    Idempotent across runs and re-imports — safe to call repeatedly,
    catches both new alpha textures and textures that lost their alpha
    after being re-imported as opaque.

    Verbose: prints a one-line diagnostic per material so it's obvious
    why a fence/foliage material did or didn't get its alpha wired.

    Returns True iff the link state was changed (added or removed)."""
    if not material:
        return False
    name = material.name
    if not material.use_nodes or not material.node_tree:
        _alog(f"[ALPHA-LINK] mat={name!r}: no node tree, skip")
        return False
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        _alog(f"[ALPHA-LINK] mat={name!r}: no Principled BSDF, skip")
        return False
    alpha_input = bsdf.inputs.get('Alpha')
    if alpha_input is None:
        _alog(f"[ALPHA-LINK] mat={name!r}: BSDF has no Alpha input, skip")
        return False

    tex_node = next(
        (n for n in nodes
         if n.type == 'TEX_IMAGE' and n.image is not None),
        None,
    )
    if tex_node is None:
        _alog(f"[ALPHA-LINK] mat={name!r}: no TEX_IMAGE with image, skip")
        return False

    img = tex_node.image
    has_alpha = image_has_significant_alpha(img)
    already_linked = (
        alpha_input.is_linked
        and alpha_input.links[0].from_node is tex_node
    )

    changed = False

    if has_alpha:
        # Ensure the link itself
        if not already_linked:
            for link in list(alpha_input.links):
                links.remove(link)
            links.new(tex_node.outputs['Alpha'], alpha_input)
            changed = True

        # CRITICAL: always enforce the blend mode, even when the link was
        # already correct. Reason — earlier passes (Phase 1 from
        # _assign_textures_to_materials, manual user wiring) may have
        # created the link without touching it, leaving the material in
        # an inconsistent state where Alpha is wired in the node graph
        # but the viewport renders it opaque. This is the exact bug that
        # produces «alpha pin connected, fence still black». Re-running
        # this every TXD import keeps blend mode in sync with the actual
        # link state. Standard: Смешанный + Перекрытие прозрачности ВЫКЛ
        # (compat.make_material_alpha writes both EEVEE generations —
        # blend_method alone is a no-op on 4.2+).
        if compat.make_material_alpha(material):
            changed = True
        if hasattr(material, 'shadow_method') and material.shadow_method == 'OPAQUE':
            material.shadow_method = 'HASHED'
            changed = True

        if changed:
            _alog(f"[ALPHA-LINK] mat={name!r} img={img.name!r}: "
                  f"Alpha {'WIRED' if not already_linked else 'kept'} + blend=BLEND")
        else:
            _alog(f"[ALPHA-LINK] mat={name!r} img={img.name!r}: already correct (link + blend)")
        return changed

    # Image is opaque — drop any tex_node→Alpha link, restore OPAQUE blend.
    for link in list(alpha_input.links):
        if link.from_node is tex_node:
            links.remove(link)
            changed = True
    if changed:
        # Only flip blend back to OPAQUE if WE removed a link — leave it
        # alone if the user has set BLEND/HASHED for some other reason.
        # Via compat so the 4.2+ render method goes back to Dithered too
        # (otherwise the material stays «Смешанный» forever).
        compat.set_blend_method(material, 'OPAQUE')
        if hasattr(material, 'shadow_method'):
            material.shadow_method = 'OPAQUE'

    if changed:
        _alog(f"[ALPHA-LINK] mat={name!r} img={img.name!r}: opaque → REMOVED Alpha link + blend=OPAQUE")
    else:
        _alog(f"[ALPHA-LINK] mat={name!r} img={img.name!r}: opaque, no change")
    return changed


def _force_material_opaque(material) -> bool:
    """Hard-disable alpha on *material*: drop any tex→BSDF Alpha link, reset
    Alpha to 1.0, force OPAQUE blend/shadow. Counterpart to
    :func:`link_material_alpha_if_textured` for the scene-wide OFF toggle."""
    if not material or not material.use_nodes or not material.node_tree:
        return False
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    changed = False
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is not None:
        ai = bsdf.inputs.get('Alpha')
        if ai is not None:
            for lk in list(ai.links):
                links.remove(lk)
                changed = True
            if ai.default_value != 1.0:
                ai.default_value = 1.0
                changed = True
    if compat.blend_method_of(material) != 'OPAQUE':
        compat.set_blend_method(material, 'OPAQUE')
        changed = True
    if hasattr(material, 'shadow_method') and material.shadow_method != 'OPAQUE':
        material.shadow_method = 'OPAQUE'
        changed = True
    return changed


def _scene_materials(context):
    """Unique materials used by MESH objects in the current scene."""
    seen = {}
    for obj in context.scene.objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            m = slot.material
            if m is not None and m.name not in seen:
                seen[m.name] = m
    return list(seen.values())


class GTATOOLS_OT_toggle_scene_alpha(bpy.types.Operator):
    """Включить / выключить альфу (прозрачность) на всех материалах сцены.

    ВКЛ — подключает альфу текстуры к шейдеру там, где у текстуры есть
    прозрачные пиксели (листва, заборы, окна), и ставит HASHED.
    ВЫКЛ — снимает связь и делает материалы OPAQUE."""
    bl_idname = "gtatools.toggle_scene_alpha"
    bl_label = "INU: Toggle Scene Alpha"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.inu_settings
        enable = not bool(getattr(s, 'gtatools_scene_alpha_on', True))
        n = 0
        for m in _scene_materials(context):
            try:
                if enable:
                    if link_material_alpha_if_textured(m):
                        n += 1
                else:
                    if _force_material_opaque(m):
                        n += 1
            except Exception as ex:
                print(f"[ALPHA-TOGGLE] {m.name!r} failed: {ex}")
        s.gtatools_scene_alpha_on = enable
        state = T("включена") if enable else T("выключена")
        self.report({'INFO'}, f"{T('Альфа')} {state}: {n} {T('материалов')}")
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}


class GTATOOLS_OT_load_textures(bpy.types.Operator):
    """Загрузить текстуры по именам материалов из указанных папок"""
    bl_idname = "gtatools.load_textures"
    bl_label = "INU: Load Textures"
    bl_options = {'REGISTER', 'UNDO'}

    def find_texture_file(self, material_name, search_paths):
        """Search for texture file with given material name in specified paths"""
        extensions = ['.png', '.jpg', '.jpeg', '.tga', '.bmp', '.dds']

        for search_path in search_paths:
            if not search_path or not os.path.isdir(search_path):
                continue

            for ext in extensions:
                # Try exact name
                texture_path = os.path.join(search_path, material_name + ext)
                if os.path.isfile(texture_path):
                    return texture_path

                # Try lowercase
                texture_path = os.path.join(search_path, material_name.lower() + ext)
                if os.path.isfile(texture_path):
                    return texture_path

                # Try uppercase
                texture_path = os.path.join(search_path, material_name.upper() + ext)
                if os.path.isfile(texture_path):
                    return texture_path

        return None

    def setup_material_texture(self, material, image):
        """Setup material nodes to use the loaded texture"""
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Find or create Principled BSDF
        principled = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break

        if not principled:
            principled = nodes.new('ShaderNodeBsdfPrincipled')
            principled.location = (0, 0)

        # Set Specular to 0 (works for Blender 3.x and 4.x)
        for inp in principled.inputs:
            if 'specular' in inp.name.lower() or 'ior level' in inp.name.lower():
                if inp.type == 'VALUE':
                    inp.default_value = 0.0

        # Check if texture already connected
        for node in nodes:
            if node.type == 'TEX_IMAGE' and node.image == image:
                return False  # Already setup, use "Fix Materials" button instead

        # Find existing empty image texture node or create new
        tex_node = None
        for node in nodes:
            if node.type == 'TEX_IMAGE' and node.image is None:
                tex_node = node
                break

        if not tex_node:
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.location = (-300, 0)

        tex_node.image = image

        # Connect to Principled BSDF Base Color
        base_color_input = principled.inputs.get('Base Color')
        if base_color_input and not base_color_input.is_linked:
            links.new(tex_node.outputs['Color'], base_color_input)

        # Connect Alpha only if image has significant transparent pixels (>100)
        has_significant_alpha = False
        try:
            # Принудительно загрузить пиксели в память
            if not image.has_data:
                image.reload()

            if image.channels >= 4 and len(image.pixels) > 0:
                pixels = np.array(image.pixels[:])
                alpha = pixels[3::4]
                transparent_count = int(np.sum(alpha < 0.95))
                print(f"[Texture] {image.name}: прозрачных = {transparent_count}")
                if transparent_count > 5000:
                    has_significant_alpha = True
        except Exception as e:
            print(f"[Texture] {image.name}: ошибка - {e}")

        if has_significant_alpha:
            alpha_input = principled.inputs.get('Alpha')
            if alpha_input and not alpha_input.is_linked:
                links.new(tex_node.outputs['Alpha'], alpha_input)
                compat.make_material_alpha(material)
                if hasattr(material, 'shadow_method'):
                    material.shadow_method = 'HASHED'

        return True

    def execute(self, context):
        scene = context.scene

        # Get search paths
        path1 = scene.inu_settings.gtatools_texture_path1
        path2 = scene.inu_settings.gtatools_texture_path2

        # If path2 is empty, try to get blend file directory
        if not path2 and bpy.data.filepath:
            path2 = os.path.dirname(bpy.data.filepath)

        search_paths = [p for p in [path1, path2] if p]

        if not search_paths:
            self.report({'ERROR'}, T("Укажите хотя бы один путь к папке с текстурами!"))
            return {'CANCELLED'}

        # Get active material from active object
        obj = context.active_object
        if not obj or not obj.active_material:
            self.report({'ERROR'}, T("Выберите материал в списке!"))
            return {'CANCELLED'}

        material = obj.active_material
        material_name = material.name

        # Skip default/system material names
        if material_name.lower() in ('none', 'material', 'dots stroke'):
            self.report({'ERROR'}, T("Выберите корректный материал!"))
            return {'CANCELLED'}

        # Find texture file
        texture_path = self.find_texture_file(material_name, search_paths)

        if texture_path:
            # Check if image already loaded
            existing_image = None
            for img in bpy.data.images:
                if img.filepath and os.path.normpath(img.filepath) == os.path.normpath(texture_path):
                    existing_image = img
                    break

            if existing_image:
                image = existing_image
            else:
                # Load new image
                try:
                    image = bpy.data.images.load(texture_path)
                except Exception as e:
                    self.report({'ERROR'}, f"{T('Не удалось загрузить')} {texture_path}: {e}")
                    return {'CANCELLED'}

            # Setup material
            if self.setup_material_texture(material, image):
                self.report({'INFO'}, f"{T('Загружена текстура:')} {material_name}")
            else:
                self.report({'INFO'}, f"{T('Текстура уже подключена:')} {material_name}")
        else:
            self.report({'WARNING'}, f"{T('Текстура не найдена:')} {material_name}")

        return {'FINISHED'}


class GTATOOLS_OT_set_blend_folder(bpy.types.Operator):
    """Установить путь к папке .blend файла"""
    bl_idname = "gtatools.set_blend_folder"
    bl_label = "INU: Set Blend Folder"
    bl_options = {'REGISTER'}

    def execute(self, context):
        if bpy.data.filepath:
            context.scene.inu_settings.gtatools_texture_path2 = os.path.dirname(bpy.data.filepath)
            self.report({'INFO'}, T("Путь установлен"))
        else:
            self.report({'WARNING'}, T("Сначала сохраните .blend файл!"))
        return {'FINISHED'}


class GTATOOLS_OT_drop_texture_as_material(bpy.types.Operator):
    """Создать материал из перетаскиваемой текстуры"""
    bl_idname = "gtatools.drop_texture_as_material"
    bl_label = "INU: Drop Texture as Material"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        subtype='FILE_PATH',
    )

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, T("Файл не указан!"))
            return {'CANCELLED'}

        # Check extension
        ext = os.path.splitext(self.filepath)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.tga', '.bmp', '.dds'):
            self.report({'ERROR'}, f"{T('Неподдерживаемый формат:')} {ext}")
            return {'CANCELLED'}

        # Get active object
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        # Имя материала из имени файла
        mat_name = os.path.splitext(os.path.basename(self.filepath))[0]

        # Load image
        try:
            image = bpy.data.images.load(self.filepath)
        except Exception as e:
            self.report({'ERROR'}, f"{T('Ошибка загрузки:')} {e}")
            return {'CANCELLED'}

        # Создаём материал
        material = bpy.data.materials.new(name=mat_name)
        material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Получаем Principled BSDF (ищем по типу, не по имени)
        principled = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break

        # Specular = 0 (GTA стиль)
        for inp in principled.inputs:
            if 'specular' in inp.name.lower() or 'ior level' in inp.name.lower():
                if inp.type == 'VALUE':
                    inp.default_value = 0.0

        # Создаём Image Texture ноду
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = image
        tex_node.location = (-300, 300)

        # Подключаем Color к Base Color
        links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])

        # Проверяем альфа канал
        if image.channels >= 4:
            try:
                pixels = np.array(image.pixels[:])
                alpha = pixels[3::4]
                transparent_count = int(np.sum(alpha < 0.95))
                if transparent_count > 5000:
                    links.new(tex_node.outputs['Alpha'], principled.inputs['Alpha'])
                    compat.make_material_alpha(material)
                    if hasattr(material, 'shadow_method'):
                        material.shadow_method = 'HASHED'
            except (RuntimeError, ValueError, KeyError, MemoryError):
                # Пиксели могут быть не загружены (RuntimeError), а сокета
                # 'Alpha' может не быть на нестандартной ноде (KeyError).
                pass

        # Применяем материал к объекту
        if obj.data.materials:
            obj.data.materials.append(material)
        else:
            obj.data.materials.append(material)

        # Делаем новый материал активным
        obj.active_material_index = len(obj.data.materials) - 1

        self.report({'INFO'}, f"{T('Создан материал:')} {mat_name}")
        return {'FINISHED'}


if hasattr(bpy.types, 'FileHandler'):
    class GTATOOLS_FH_texture_drop(bpy.types.FileHandler):
        """File Handler для перетаскивания текстур"""
        bl_idname = "GTATOOLS_FH_texture_drop"
        bl_label = "GTA Texture Drop"
        bl_import_operator = "gtatools.drop_texture_as_material"
        bl_file_extensions = ".png;.jpg;.jpeg;.tga;.bmp;.dds"

        @classmethod
        def poll_drop(cls, context):
            return context.area and context.area.type == 'VIEW_3D'


class GTATOOLS_OT_drop_txd(bpy.types.Operator):
    """Импорт TXD при перетаскивании во viewport"""
    bl_idname = "gtatools.drop_txd"
    bl_label = "INU: Import TXD (Drop)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        from .txd_import import import_txd as inu_import_txd
        # If meshes are selected when the user drops the TXD,
        # append every newly-created material to each of them. The
        # user is then free to assign per-face. Without selection
        # we keep the legacy behaviour — materials sit in
        # bpy.data.materials and the user wires them up manually.
        targets = [o for o in context.selected_objects
                   if o.type == 'MESH']
        new_materials = []
        count = 0
        for f in self.files:
            path = os.path.join(self.directory, f.name)
            if os.path.isfile(path) and path.lower().endswith('.txd'):
                try:
                    images = inu_import_txd(filepath=path)
                    for img in images:
                        mat_name = os.path.splitext(img.name)[0]
                        mat = bpy.data.materials.get(mat_name)
                        was_new = mat is None
                        if was_new:
                            mat = bpy.data.materials.new(name=mat_name)
                            mat.use_nodes = True
                            nodes = mat.node_tree.nodes
                            bsdf = None
                            for n in nodes:
                                if n.type == 'BSDF_PRINCIPLED':
                                    bsdf = n
                                    break
                            if bsdf:
                                tex_node = nodes.new('ShaderNodeTexImage')
                                tex_node.image = img
                                tex_node.location = (bsdf.location.x - 300, bsdf.location.y)
                                mat.node_tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
                                if 'Specular IOR Level' in bsdf.inputs:
                                    bsdf.inputs['Specular IOR Level'].default_value = 0.0
                                elif 'Specular' in bsdf.inputs:
                                    bsdf.inputs['Specular'].default_value = 0.0
                        new_materials.append(mat)
                    count += len(images)
                except Exception as e:
                    self.report({'WARNING'}, f"TXD: {e}")

        if targets and new_materials:
            attached = 0
            for obj in targets:
                existing = {ms.material for ms in obj.material_slots
                            if ms.material is not None}
                for mat in new_materials:
                    if mat in existing:
                        continue
                    obj.data.materials.append(mat)
                    existing.add(mat)
                    attached += 1
            self.report({'INFO'},
                        f"TXD: {count} {T('текстур')} → "
                        f"{len(targets)} {T('моделей')} ({attached} mat slots)")
        else:
            self.report({'INFO'},
                        f"TXD: {count} {T('текстур импортировано')}")
        return {'FINISHED'}


if hasattr(bpy.types, 'FileHandler'):
    class GTATOOLS_FH_txd_drop(bpy.types.FileHandler):
        """File Handler для перетаскивания TXD"""
        bl_idname = "GTATOOLS_FH_txd_drop"
        bl_label = "GTA TXD Drop"
        bl_import_operator = "gtatools.drop_txd"
        bl_file_extensions = ".txd"

        @classmethod
        def poll_drop(cls, context):
            return context.area and context.area.type == 'VIEW_3D'


class GTATOOLS_OT_check_materials(bpy.types.Operator):
    """Проверить количество материалов на выделенных объектах"""
    bl_idname = "gtatools.check_materials"
    bl_label = "INU: Check Materials"

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected:
            self.report({'ERROR'}, T("Выделите меш объекты!"))
            return {'CANCELLED'}

        total_materials = 0
        report_lines = []

        for obj in selected:
            mat_count = len([slot for slot in obj.material_slots if slot.material])
            total_materials += mat_count

            # GTA SA limit is 50 materials per object
            status = "⚠️" if mat_count > 50 else "✓"
            report_lines.append(f"{status} {obj.name}: {mat_count} mat.")

        # Show detailed report
        if len(selected) == 1:
            obj = selected[0]
            mat_count = len([slot for slot in obj.material_slots if slot.material])
            if mat_count > 50:
                self.report({'WARNING'}, f"{obj.name}: {mat_count} materials (GTA limit: 50)")
            else:
                self.report({'INFO'}, f"{obj.name}: {mat_count} materials")
        else:
            over_limit = sum(1 for obj in selected if len([s for s in obj.material_slots if s.material]) > 50)
            if over_limit > 0:
                self.report({'WARNING'}, f"{T('Объектов:')} {len(selected)}, {T('всего материалов:')} {total_materials}, {T('превышен лимит:')} {over_limit}")
            else:
                self.report({'INFO'}, f"{T('Объектов:')} {len(selected)}, {T('всего материалов:')} {total_materials}")

        return {'FINISHED'}


class GTATOOLS_OT_cleanup_materials(bpy.types.Operator):
    """Объединить дубликаты материалов и текстур (.001, .002, и т.д.) с оригиналами"""
    bl_idname = "gtatools.cleanup_materials"
    bl_label = "INU: Cleanup Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import re
        import os

        # Pattern to match .001, .002, etc. suffix
        pattern = re.compile(r'^(.+)\.(\d{3})$')

        merged_count = 0
        removed_materials = []

        # Find all duplicate materials
        duplicates = {}  # {base_name: [list of duplicate materials]}

        for mat in bpy.data.materials:
            match = pattern.match(mat.name)
            if match:
                base_name = match.group(1)
                if base_name not in duplicates:
                    duplicates[base_name] = []
                duplicates[base_name].append(mat)

        # Process each group of duplicates
        for base_name, dup_list in duplicates.items():
            # Find original material
            original = bpy.data.materials.get(base_name)

            if not original:
                # No original found, rename first duplicate to base name
                first_dup = dup_list[0]
                first_dup.name = base_name
                original = first_dup
                dup_list = dup_list[1:]

            # Replace duplicates with original in all objects
            for dup_mat in dup_list:
                for obj in bpy.data.objects:
                    if obj.type != 'MESH':
                        continue
                    for slot in obj.material_slots:
                        if slot.material == dup_mat:
                            try:
                                slot.material = original
                                merged_count += 1
                            except AttributeError:
                                # Слот только для чтения (линк-библиотека /
                                # override / нередактируемые данные) — не роняем
                                # всю чистку из-за одного объекта, пропускаем.
                                pass

                removed_materials.append(dup_mat.name)

        # Remove unused duplicate materials
        for mat_name in removed_materials:
            mat = bpy.data.materials.get(mat_name)
            if mat and mat.users == 0:
                bpy.data.materials.remove(mat)

        # --- Textures (images) cleanup: safe mode (filepath must match) ---
        img_merged_count = 0
        removed_images = []
        skipped_images = 0

        def _img_key(img):
            # Compare by absolute filepath when possible; fall back to basename
            try:
                fp = bpy.path.abspath(img.filepath, library=img.library) if img.filepath else ""
            except Exception:
                fp = img.filepath or ""
            if fp:
                return os.path.normcase(os.path.normpath(fp))
            # No filepath (packed/generated) — use source+size as a weak key
            return f"<nofile>:{img.source}:{tuple(img.size)}"

        img_duplicates = {}  # {base_name: [list of duplicate images]}
        for img in bpy.data.images:
            match = pattern.match(img.name)
            if match:
                base_name = match.group(1)
                img_duplicates.setdefault(base_name, []).append(img)

        for base_name, dup_list in img_duplicates.items():
            original = bpy.data.images.get(base_name)

            if not original:
                # No original — promote first duplicate whose key matches the rest
                first_dup = dup_list[0]
                first_dup.name = base_name
                original = first_dup
                dup_list = dup_list[1:]

            orig_key = _img_key(original)

            for dup_img in dup_list:
                # Safe check: only merge if filepath matches the original
                if _img_key(dup_img) != orig_key:
                    skipped_images += 1
                    continue

                # Replace in all material node trees
                for mat in bpy.data.materials:
                    if not mat.use_nodes or not mat.node_tree:
                        continue
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image == dup_img:
                            node.image = original
                            img_merged_count += 1

                # Replace in node groups (shader/geometry/compositor)
                for ng in bpy.data.node_groups:
                    for node in ng.nodes:
                        if node.type == 'TEX_IMAGE' and getattr(node, 'image', None) == dup_img:
                            node.image = original
                            img_merged_count += 1

                removed_images.append(dup_img.name)

        for img_name in removed_images:
            img = bpy.data.images.get(img_name)
            if img and img.users == 0:
                bpy.data.images.remove(img)

        # --- Report ---
        parts = []
        if merged_count or removed_materials:
            parts.append(f"{T('Материалов:')} {merged_count}/{len(removed_materials)}")
        if img_merged_count or removed_images:
            parts.append(f"{T('Текстур:')} {img_merged_count}/{len(removed_images)}")
        if skipped_images:
            parts.append(f"{T('Пропущено (разные пути):')} {skipped_images}")

        if parts:
            self.report({'INFO'}, " | ".join(parts))
        else:
            self.report({'INFO'}, T("Дубликаты материалов не найдены"))

        return {'FINISHED'}


class GTATOOLS_OT_sort_materials(bpy.types.Operator):
    """Сортировка материалов"""
    bl_idname = "gtatools.sort_materials"
    bl_label = "INU: Sort Materials"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and len(obj.material_slots) > 1

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # Собираем текущие материалы и индексы полигонов
        mat_names = []
        for slot in obj.material_slots:
            mat_names.append(slot.material.name if slot.material else "")

        # Натуральная сортировка: 1, 2, 3, 10 вместо 1, 10, 2, 3
        def natural_key(i):
            return [int(p) if p.isdigit() else p for p in _re.split(r'(\d+)', mat_names[i].lower())]

        sorted_indices = sorted(range(len(mat_names)), key=natural_key)

        # Если уже отсортировано — ничего не делаем
        if sorted_indices == list(range(len(mat_names))):
            self.report({'INFO'}, T("Материалы уже отсортированы"))
            return {'FINISHED'}

        # Маппинг старый индекс -> новый индекс
        index_map = {old: new for new, old in enumerate(sorted_indices)}

        # Сохраняем новые индексы полигонов
        new_indices = [index_map[poly.material_index] for poly in mesh.polygons]

        # Сохраняем отсортированные материалы
        sorted_mats = [obj.material_slots[i].material for i in sorted_indices]

        # Очищаем все слоты и добавляем в отсортированном порядке
        mesh.materials.clear()
        for mat in sorted_mats:
            mesh.materials.append(mat)

        # Восстанавливаем индексы полигонов
        for poly, idx in zip(mesh.polygons, new_indices):
            poly.material_index = idx

        sorted_count = len(sorted_mats)
        self.report({'INFO'}, f"{T('Отсортировано материалов:')} {sorted_count}")
        return {'FINISHED'}


class GTATOOLS_OT_reset_transform(bpy.types.Operator):
    """Сброс Location и Rotation в (0,0,0) для выделенных мешей"""
    bl_idname = "gtatools.reset_transform"
    bl_label = "INU: Reset Transform"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sel_meshes = [o for o in context.selected_objects if o.type == 'MESH']
        targets = sel_meshes if sel_meshes else [
            o for o in context.scene.objects if o.type == 'MESH'
        ]
        if not targets:
            self.report({'WARNING'},
                        T("Нет mesh-объектов для сброса"))
            return {'CANCELLED'}

        # Direct property writes (no sub-ops). Avoids the multi-undo
        # explosion that `bpy.ops.object.location_clear` + co. produce
        # when called from inside another operator's execute(): each
        # sub-op may push its own step, leaving the user to mash
        # Ctrl+Z five times to roll back what should be one action.
        for obj in targets:
            # Quaternion / axis-angle don't react to rotation_euler
            # writes visually; switch to XYZ so the reset is visible.
            if obj.rotation_mode != 'XYZ':
                obj.rotation_mode = 'XYZ'
            obj.location = (0.0, 0.0, 0.0)
            obj.rotation_euler = (0.0, 0.0, 0.0)

        # Force depsgraph re-eval inside the operator scope. Without
        # this the viewport doesn't refresh until the next user
        # interaction (matrix_world is a lazy-evaluated cache).
        try:
            context.view_layer.update()
        except Exception:
            pass

        self.report({'INFO'}, f"{T('Сброшено объектов:')} {len(targets)}")
        return {'FINISHED'}


class GTATOOLS_OT_apply_lightmap_uv2(bpy.types.Operator):
    """Применить текстуру LightMap на UV2 (Multiply) для выделенных объектов"""
    bl_idname = "gtatools.apply_lightmap_uv2"
    bl_label = "INU: Apply LightMap UV2"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.png;*.jpg;*.jpeg;*.tga;*.bmp;*.tif;*.tiff", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath or not os.path.isfile(self.filepath):
            self.report({'ERROR'}, T("Файл не найден"))
            return {'CANCELLED'}

        lm_image = bpy.data.images.load(self.filepath, check_existing=True)

        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                objects = [obj]
        if not objects:
            self.report({'ERROR'}, T("Выберите меш объект!"))
            return {'CANCELLED'}

        applied = 0
        for obj in objects:
            mesh = obj.data
            # Ensure UV2 exists
            if len(mesh.uv_layers) < 2:
                mesh.uv_layers.new(name="UVMap.001")
            uv2_name = mesh.uv_layers[1].name

            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not mat or not mat.use_nodes:
                    continue

                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                # Find Principled BSDF
                principled = None
                for n in nodes:
                    if n.type == 'BSDF_PRINCIPLED':
                        principled = n
                        break
                if not principled:
                    continue

                # Skip if already has lightmap
                if nodes.get("LM_Texture"):
                    nodes.get("LM_Texture").image = lm_image
                    applied += 1
                    continue

                # Find what's connected to Base Color
                base_input = principled.inputs['Base Color']
                orig_socket = None
                if base_input.links:
                    orig_socket = base_input.links[0].from_socket

                # UV Map node for UV2
                uv_node = nodes.new('ShaderNodeUVMap')
                uv_node.name = "LM_UV"
                uv_node.uv_map = uv2_name

                # Lightmap texture node
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.name = "LM_Texture"
                tex_node.label = "LightMap"
                tex_node.image = lm_image

                # Mix node (Multiply) — через compat (ShaderNodeMix на
                # 3.4+ или ShaderNodeMixRGB на 2.80-3.3).
                mix = nodes.new(compat.MIX_NODE_TYPE)
                compat.setup_mix_rgba_node(mix, blend='MULTIPLY')
                compat.mix_input_factor(mix).default_value = 1.0
                in_a, in_b, out_r = (
                    compat.MIX_INPUT_A, compat.MIX_INPUT_B, compat.MIX_OUTPUT_RESULT)
                mix.name = "LM_Mix"
                mix.label = "LightMap Mix"

                # Position nodes
                px = principled.location.x
                py = principled.location.y
                uv_node.location = (px - 700, py - 300)
                tex_node.location = (px - 500, py - 300)
                mix.location = (px - 200, py)

                # Connect
                links.new(uv_node.outputs['UV'], tex_node.inputs['Vector'])
                if orig_socket:
                    links.new(orig_socket, mix.inputs[in_a])
                else:
                    mix.inputs[in_a].default_value = (1, 1, 1, 1)
                links.new(tex_node.outputs['Color'], mix.inputs[in_b])
                links.new(mix.outputs[out_r], base_input)

                applied += 1

        self.report({'INFO'}, f"LightMap UV2: {applied} {T('материалов')}")
        return {'FINISHED'}


class GTATOOLS_OT_remove_lightmap_uv2(bpy.types.Operator):
    """Убрать LightMap UV2 из материалов выделенных объектов"""
    bl_idname = "gtatools.remove_lightmap_uv2"
    bl_label = "INU: Remove LightMap UV2"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                objects = [obj]

        removed = 0
        for obj in objects:
            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not mat or not mat.use_nodes:
                    continue

                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                lm_mix = nodes.get("LM_Mix")
                lm_tex = nodes.get("LM_Texture")
                lm_uv = nodes.get("LM_UV")

                if not lm_mix:
                    continue

                # Restore original connection: A input -> Base Color target
                orig_socket = None
                a_input = lm_mix.inputs.get('A') or lm_mix.inputs.get('Color1')
                if a_input and a_input.links:
                    orig_socket = a_input.links[0].from_socket

                # Find where mix output goes
                for link in lm_mix.outputs[0].links:
                    target_socket = link.to_socket
                    if orig_socket:
                        links.new(orig_socket, target_socket)

                if lm_mix:
                    nodes.remove(lm_mix)
                if lm_tex:
                    nodes.remove(lm_tex)
                if lm_uv:
                    nodes.remove(lm_uv)
                removed += 1

        self.report({'INFO'}, f"LightMap UV2: {removed} {T('удалено')}")
        return {'FINISHED'}


class GTATOOLS_OT_toggle_lightmap_uv2(bpy.types.Operator):
    """Включить/выключить отображение LightMap UV2"""
    bl_idname = "gtatools.toggle_lightmap_uv2"
    bl_label = "INU: Toggle LightMap UV2"
    bl_options = {'REGISTER', 'UNDO'}

    enable: BoolProperty(name="Enable", default=True)

    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            obj = context.active_object
            if obj and obj.type == 'MESH':
                objects = [obj]

        count = 0
        for obj in objects:
            for mat_slot in obj.material_slots:
                mat = mat_slot.material
                if not mat or not mat.use_nodes:
                    continue

                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                lm_mix = nodes.get("LM_Mix")
                if not lm_mix:
                    continue

                principled = None
                for n in nodes:
                    if n.type == 'BSDF_PRINCIPLED':
                        principled = n
                        break
                if not principled:
                    continue

                base_input = principled.inputs['Base Color']
                # Get A input of mix (original texture)
                a_input = lm_mix.inputs.get('A') or lm_mix.inputs.get('Color1')
                out_socket = lm_mix.outputs.get('Result') or lm_mix.outputs.get('Color') or lm_mix.outputs[0]
                orig_socket = a_input.links[0].from_socket if a_input and a_input.links else None

                if self.enable:
                    # ON: connect LM_Mix output → Base Color
                    lm_mix.mute = False
                    links.new(out_socket, base_input)
                else:
                    # OFF: bypass LM_Mix, connect original texture → Base Color directly
                    lm_mix.mute = True
                    if orig_socket:
                        links.new(orig_socket, base_input)
                count += 1

        state = "ON" if self.enable else "OFF"
        self.report({'INFO'}, f"LightMap UV2: {state} ({count})")
        return {'FINISHED'}


