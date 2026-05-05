# INU_tools.tools.txd_export — TXD texture archive export

import bpy
import struct
import os
import numpy as np

from .. import T

# =============================================================================
# TXD EXPORTER
# =============================================================================

RW_TEXDICTIONARY = 0x16
RW_TEXTURENATIVE = 0x15
RW_STRUCT = 0x01
RW_EXTENSION = 0x03
RW_VERSION = 0x1803FFFF
PLATFORM_D3D9 = 9
RASTER_565 = 0x0200
RASTER_8888 = 0x0500
RASTER_MIPMAP = 0x8000
FILTER_LINEAR = 0x02
ADDRESS_WRAP = 0x01


def make_filter_flags():
    return FILTER_LINEAR | (ADDRESS_WRAP << 8) | (ADDRESS_WRAP << 12)


# Optional NVTT path lives in a sibling `nvtt_compress` module that ships
# only with the full GitHub release (copied in by `dev/build_extension.ps1`).
# When absent — e.g. the extensions.blender.org build — these stubs keep the
# call sites simple and the addon falls back to the bundled CPU encoder.
try:
    from .nvtt_compress import (
        check_nvtt_available, _nvtt_prepare_png,
        _nvtt_compress_and_parse, compress_with_nvtt,
    )
    HAS_NVTT_MODULE = True
except ImportError:
    HAS_NVTT_MODULE = False

    def check_nvtt_available(nvtt_path):
        return False, T("NVTT недоступен в этой сборке (CPU кодер)")

    def _nvtt_prepare_png(name, image):
        return None

    def _nvtt_compress_and_parse(prepared, use_alpha, nvcompress_path):
        return None

    def compress_with_nvtt(name, image, use_alpha, nvcompress_path):
        return None


def write_rw_section_header(data, section_type, size):
    data.extend(struct.pack('<III', section_type, size, RW_VERSION))


def is_texture_connected_to_alpha(tex_node):
    # Alpha выход - индекс 1 у TEX_IMAGE
    if len(tex_node.outputs) < 2:
        return False
    alpha_output = tex_node.outputs[1]
    if not alpha_output.is_linked:
        return False
    # Проверяем что подключено к Principled BSDF (любой вход с alpha в имени)
    for link in alpha_output.links:
        to_node = link.to_socket.node
        if to_node.type == 'BSDF_PRINCIPLED':
            # Проверяем по индексу или имени (Alpha вход ~индекс 21, но лучше по имени)
            socket_name = link.to_socket.name.lower()
            socket_id = link.to_socket.identifier.lower() if hasattr(link.to_socket, 'identifier') else ''
            if 'alpha' in socket_name or 'alpha' in socket_id or 'альфа' in socket_name:
                return True
    return False


def check_image_has_transparent_pixels(image):
    try:
        pixels = np.array(image.pixels[:])
        if len(pixels) < 4:
            return False
        alpha = pixels[3::4]
        return np.any(alpha < 0.99)
    except:
        return False


def is_node_connected(node):
    """Проверить, подключена ли нода к чему-либо (любой выход)"""
    for output in node.outputs:
        if output.is_linked:
            return True
    return False


def collect_textures(selected_only=False):
    textures = {}
    transparent_textures = set()

    if selected_only:
        materials = set()
        for obj in bpy.context.selected_objects:
            if hasattr(obj, 'material_slots'):
                for slot in obj.material_slots:
                    if slot.material:
                        materials.add(slot.material)
        materials = list(materials)
    else:
        materials = bpy.data.materials

    # First pass: gather every texture used by a connected image node, and
    # remember the "main" image of each material (its first connected
    # texture). The main image's basename is what paintjob alts attach
    # to in pass 2.
    material_main_image = {}

    for mat in materials:
        if not mat.use_nodes or not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                # Пропускаем лайтмап превью ноды (не экспортировать в TXD)
                if node.name in ("LM_Texture", "Lightmap_Texture"):
                    continue
                # Игнорировать ноды которые ни к чему не подключены
                if not is_node_connected(node):
                    continue

                img = node.image
                name = os.path.splitext(img.name)[0]
                alpha_connected = is_texture_connected_to_alpha(node)
                has_transparent = check_image_has_transparent_pixels(img)
                if has_transparent:
                    transparent_textures.add(img.name)
                # DXT3 только если альфа подключена И есть прозрачные пиксели
                uses_alpha = alpha_connected and has_transparent
                if name in textures:
                    existing_alpha = textures[name][1]
                    textures[name] = (img, existing_alpha or uses_alpha)
                else:
                    textures[name] = (img, uses_alpha)

                # Record this material's main image (first one we see).
                if mat not in material_main_image:
                    material_main_image[mat] = name

    # Second pass: vehicle paintjob alts — pack them with derived names so
    # the game's runtime swap works: <base>_paintjob1 / <base>_paintjob2.
    # Materials without a main image are skipped (no <base> to attach to).
    for mat in materials:
        inu = getattr(mat, 'inu', None)
        if inu is None:
            continue
        alt1 = getattr(inu, 'paintjob_alt_1', None)
        alt2 = getattr(inu, 'paintjob_alt_2', None)
        if not (alt1 or alt2):
            continue
        base = material_main_image.get(mat)
        if not base:
            # Material has paintjob alts but no main texture — silently
            # skip; the validator operator surfaces this to the user.
            continue
        for alt_img, suffix in ((alt1, '_paintjob1'), (alt2, '_paintjob2')):
            if not alt_img:
                continue
            tex_name = f"{base}{suffix}"
            has_transparent = check_image_has_transparent_pixels(alt_img)
            if has_transparent:
                transparent_textures.add(alt_img.name)
            # Paintjobs swap into the body slot — use same alpha mode
            # as the base texture so DXT format matches.
            base_uses_alpha = textures.get(base, (None, False))[1]
            uses_alpha = base_uses_alpha or has_transparent
            textures[tex_name] = (alt_img, uses_alpha)

    return textures, list(transparent_textures)


def downsample_image(pixels, width, height):
    new_w = max(1, width // 2)
    new_h = max(1, height // 2)
    if width == 1 and height == 1:
        return None, 0, 0
    if width > 1 and height > 1:
        reshaped = pixels[:new_h*2, :new_w*2].reshape(new_h, 2, new_w, 2, 4)
        downsampled = reshaped.mean(axis=(1, 3)).astype(np.uint8)
    elif width > 1:
        downsampled = pixels[:1, :new_w*2].reshape(1, new_w, 2, 4).mean(axis=2).astype(np.uint8)
    elif height > 1:
        downsampled = pixels[:new_h*2, :1].reshape(new_h, 2, 1, 4).mean(axis=1).astype(np.uint8)
    else:
        return None, 0, 0
    return downsampled, new_w, new_h


def pad_to_4x4(pixels, width, height):
    if width >= 4 and height >= 4:
        return pixels, width, height
    pad_w = max(4, width)
    pad_h = max(4, height)
    padded = np.zeros((pad_h, pad_w, 4), dtype=np.uint8)
    padded[:height, :width] = pixels
    if width < pad_w:
        padded[:height, width:] = pixels[:, -1:, :]
    if height < pad_h:
        padded[height:, :width] = pixels[-1:, :, :]
    if width < pad_w and height < pad_h:
        padded[height:, width:] = pixels[-1, -1, :]
    return padded, pad_w, pad_h


def compress_dxt1_block(rgb):
    rgb = rgb.astype(np.float32)
    lum = rgb[:, 0] * 0.299 + rgb[:, 1] * 0.587 + rgb[:, 2] * 0.114
    min_idx, max_idx = np.argmin(lum), np.argmax(lum)
    c0, c1 = rgb[max_idx], rgb[min_idx]

    def to_565(c):
        r = int(np.clip(c[0] / 255.0 * 31 + 0.5, 0, 31))
        g = int(np.clip(c[1] / 255.0 * 63 + 0.5, 0, 63))
        b = int(np.clip(c[2] / 255.0 * 31 + 0.5, 0, 31))
        return (r << 11) | (g << 5) | b

    def from_565(c):
        return np.array([
            ((c >> 11) & 0x1F) * 255.0 / 31.0,
            ((c >> 5) & 0x3F) * 255.0 / 63.0,
            (c & 0x1F) * 255.0 / 31.0
        ])

    color0, color1 = to_565(c0), to_565(c1)

    # Для DXT3 нужен режим 4 цветов (color0 > color1)
    if color0 < color1:
        color0, color1 = color1, color0

    # Палитру строим из 565 значений (как будет при декомпрессии)
    c0_565 = from_565(color0)
    c1_565 = from_565(color1)
    palette = np.array([c0_565, c1_565, (2.0*c0_565 + c1_565)/3.0, (c0_565 + 2.0*c1_565)/3.0])
    indices = 0
    for i in range(16):
        dists = np.sum((rgb[i] - palette) ** 2, axis=1)
        indices |= (np.argmin(dists) << (i * 2))
    return struct.pack('<HHI', color0, color1, indices)


def compress_dxt3_block(rgba):
    alpha_data = 0
    for i in range(16):
        a4 = int(np.clip(rgba[i, 3] / 255.0 * 15 + 0.5, 0, 15))
        alpha_data |= (a4 << (i * 4))
    alpha_bytes = struct.pack('<Q', alpha_data)
    color_bytes = compress_dxt1_block(rgba[:, :3])
    return alpha_bytes + color_bytes


def compress_miplevel_dxt1(pixels):
    h, w = pixels.shape[:2]
    compressed = bytearray()
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            block = pixels[y:y+4, x:x+4, :3].reshape(16, 3)
            compressed.extend(compress_dxt1_block(block))
    return bytes(compressed)


def compress_miplevel_dxt3(pixels):
    h, w = pixels.shape[:2]
    compressed = bytearray()
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            block = pixels[y:y+4, x:x+4].reshape(16, 4)
            compressed.extend(compress_dxt3_block(block))
    return bytes(compressed)


def create_texture_native(name, image, use_alpha):
    width, height = image.size[0], image.size[1]
    new_w = (width + 3) // 4 * 4
    new_h = (height + 3) // 4 * 4

    pixels = np.array(image.pixels[:]).reshape(height, width, 4)
    pixels = (pixels * 255).astype(np.uint8)
    pixels = np.flipud(pixels)

    if new_w != width or new_h != height:
        padded = np.zeros((new_h, new_w, 4), dtype=np.uint8)
        padded[:height, :width] = pixels
        if width < new_w:
            padded[:height, width:] = pixels[:, -1:, :]
        if height < new_h:
            padded[height:, :] = padded[height-1:height, :]
        pixels = padded
        width, height = new_w, new_h

    mip_levels = []
    current_pixels = pixels
    current_w, current_h = width, height

    while current_w >= 1 and current_h >= 1:
        compress_pixels, _, _ = pad_to_4x4(current_pixels, current_w, current_h)
        if use_alpha:
            compressed = compress_miplevel_dxt3(compress_pixels)
        else:
            compressed = compress_miplevel_dxt1(compress_pixels)
        mip_levels.append(compressed)
        current_pixels, current_w, current_h = downsample_image(current_pixels, current_w, current_h)
        if current_pixels is None:
            break

    if use_alpha:
        dxt_type = 3
        raster_format = RASTER_8888 | RASTER_MIPMAP
        depth = 32
    else:
        dxt_type = 1
        raster_format = RASTER_565 | RASTER_MIPMAP
        depth = 16

    tex_name = name[:31].encode('ascii', errors='replace').ljust(32, b'\x00')
    mip_count = len(mip_levels)
    fourcc = b'DXT1' if dxt_type == 1 else b'DXT3'

    struct_data = bytearray()
    struct_data.extend(struct.pack('<II', PLATFORM_D3D9, make_filter_flags()))
    struct_data.extend(tex_name)
    struct_data.extend(b'\x00' * 32)
    struct_data.extend(struct.pack('<I', raster_format))
    struct_data.extend(fourcc)
    struct_data.extend(struct.pack('<HH', width, height))
    struct_data.extend(struct.pack('<B', depth))
    struct_data.extend(struct.pack('<B', mip_count))
    struct_data.extend(struct.pack('<B', 4))  # raster type
    # D3D format flag: 0x08 для DXT1, 0x09 для DXT3 (с альфой)
    struct_data.extend(struct.pack('<B', 0x09 if use_alpha else 0x08))

    for mip_data in mip_levels:
        struct_data.extend(struct.pack('<I', len(mip_data)))
        struct_data.extend(mip_data)

    tex_native = bytearray()
    write_rw_section_header(tex_native, RW_STRUCT, len(struct_data))
    tex_native.extend(struct_data)
    write_rw_section_header(tex_native, RW_EXTENSION, 0)

    return bytes(tex_native)


def prepare_texture_data(name, image, use_alpha):
    """Prepare texture data in main thread (Blender data access)"""
    width, height = image.size[0], image.size[1]
    pixels = np.array(image.pixels[:]).reshape(height, width, 4)
    pixels = (pixels * 255).astype(np.uint8)
    pixels = np.flipud(pixels)
    return (name, pixels, width, height, use_alpha)


def process_texture_parallel(texture_data):
    """Process prepared texture data (can run in parallel)"""
    name, pixels, width, height, use_alpha = texture_data

    new_w = (width + 3) // 4 * 4
    new_h = (height + 3) // 4 * 4

    if new_w != width or new_h != height:
        padded = np.zeros((new_h, new_w, 4), dtype=np.uint8)
        padded[:height, :width] = pixels
        if width < new_w:
            padded[:height, width:] = pixels[:, -1:, :]
        if height < new_h:
            padded[height:, :] = padded[height-1:height, :]
        pixels = padded
        width, height = new_w, new_h

    mip_levels = []
    current_pixels = pixels
    current_w, current_h = width, height

    while current_w >= 1 and current_h >= 1:
        compress_pixels, _, _ = pad_to_4x4(current_pixels, current_w, current_h)
        if use_alpha:
            compressed = compress_miplevel_dxt3(compress_pixels)
        else:
            compressed = compress_miplevel_dxt1(compress_pixels)
        mip_levels.append(compressed)
        current_pixels, current_w, current_h = downsample_image(current_pixels, current_w, current_h)
        if current_pixels is None:
            break

    if use_alpha:
        dxt_type = 3
        raster_format = RASTER_8888 | RASTER_MIPMAP
        depth = 32
    else:
        dxt_type = 1
        raster_format = RASTER_565 | RASTER_MIPMAP
        depth = 16

    tex_name = name[:31].encode('ascii', errors='replace').ljust(32, b'\x00')
    mip_count = len(mip_levels)
    fourcc = b'DXT1' if dxt_type == 1 else b'DXT3'

    struct_data = bytearray()
    struct_data.extend(struct.pack('<II', PLATFORM_D3D9, make_filter_flags()))
    struct_data.extend(tex_name)
    struct_data.extend(b'\x00' * 32)
    struct_data.extend(struct.pack('<I', raster_format))
    struct_data.extend(fourcc)
    struct_data.extend(struct.pack('<HH', width, height))
    struct_data.extend(struct.pack('<B', depth))
    struct_data.extend(struct.pack('<B', mip_count))
    struct_data.extend(struct.pack('<B', 4))  # raster type
    # D3D format flag: 0x08 для DXT1, 0x09 для DXT3 (с альфой)
    struct_data.extend(struct.pack('<B', 0x09 if use_alpha else 0x08))

    for mip_data in mip_levels:
        struct_data.extend(struct.pack('<I', len(mip_data)))
        struct_data.extend(mip_data)

    tex_native = bytearray()
    write_rw_section_header(tex_native, RW_STRUCT, len(struct_data))
    tex_native.extend(struct_data)
    write_rw_section_header(tex_native, RW_EXTENSION, 0)

    return bytes(tex_native)


def export_txd(filepath, context, selected_only=False, use_gpu=False):
    textures, transparent_list = collect_textures(selected_only)
    if not textures:
        msg = "No textures found on selected objects" if selected_only else "No textures found in scene"
        return {'CANCELLED'}, msg, []

    scene = context.scene
    nvcompress_path = None
    mode_name = "CPU"

    # Проверка GPU режима
    if use_gpu:
        nvtt_path = getattr(scene.inu_settings, 'gtatools_nvtt_path', '')
        available, result = check_nvtt_available(nvtt_path)
        if not available:
            return {'CANCELLED'}, f"GPU режим недоступен: {result}\nУкажите путь к NVIDIA Texture Tools в настройках", []
        nvcompress_path = result
        mode_name = "GPU (NVTT)"

    wm = context.window_manager
    total = len(textures)
    wm.progress_begin(0, total * 2)

    # Разделяем на DXT1 и DXT3 для правильного порядка (DXT3 в конце)
    dxt1_images = []  # (name, image, use_alpha) для GPU
    dxt3_images = []
    dxt1_data = []    # prepared data для CPU
    dxt3_data = []

    skipped_textures = []
    for i, (name, (image, uses_alpha)) in enumerate(textures.items()):
        wm.progress_update(i)

        # Проверка размера - должен быть кратен 4 для DXT
        w, h = image.size[0], image.size[1]
        if w % 4 != 0 or h % 4 != 0:
            print(f"[TXD] ПРОПУСК {name}: размер {w}x{h} не кратен 4 (DXT требует кратность 4)")
            skipped_textures.append(f"{name} ({w}x{h})")
            continue

        print(f"[TXD] {name}: {w}x{h}, uses_alpha={uses_alpha}")
        try:
            if uses_alpha:
                dxt3_images.append((name, image, True))
                if not use_gpu:
                    dxt3_data.append(prepare_texture_data(name, image, True))
            else:
                dxt1_images.append((name, image, False))
                if not use_gpu:
                    dxt1_data.append(prepare_texture_data(name, image, False))
        except Exception as e:
            print(f"TXD PREPARE ERROR: {name}: {e}")

    dxt1_count = len(dxt1_images)
    dxt3_count = len(dxt3_images)

    # Phase 2: Compression
    tex_natives = []

    if use_gpu and nvcompress_path:
        # GPU режим — NVTT для DXT1, CPU для DXT3 (NVTT DXT3 неточный).
        #
        # Two-stage pipeline:
        #   Stage 1 (serial, main thread): image.save() PNG to temp dir.
        #     Must stay on main thread because Blender's image API is
        #     not thread-safe.
        #   Stage 2 (parallel, worker pool): spawn nvcompress.exe per
        #     PNG and parse the resulting DDS. Pure subprocess + I/O,
        #     so 4 workers happily overlap GPU encode + disk + parse.
        # CPU fallback (process_texture_parallel) also gets bucketed
        # into the same DXT1 future list when image.save fails.
        prepared_dxt1 = []
        cpu_fallback_dxt1 = []
        for i, (name, image, _) in enumerate(dxt1_images):
            wm.progress_update(total + i)
            try:
                prepared_dxt1.append(_nvtt_prepare_png(name, image))
            except Exception as e:
                print(f"NVTT PNG save error {name}: {e} — fallback to CPU DXT")
                try:
                    cpu_fallback_dxt1.append(prepare_texture_data(name, image, False))
                except Exception as e2:
                    print(f"NVTT CPU fallback prepare error {name}: {e2}")

        for prep in prepared_dxt1:
            try:
                result = _nvtt_compress_and_parse(prep, False, nvcompress_path)
                if result:
                    tex_natives.append(result)
                else:
                    # NVTT silently failed (no DDS produced) — re-prepare
                    # the texture from bpy on main thread for CPU fallback.
                    # Rare; happens with non-power-of-two oddities.
                    name_failed = prep[0]
                    img = next((img for n, img, _ in dxt1_images if n == name_failed), None)
                    if img is not None:
                        try:
                            cpu_fallback_dxt1.append(
                                prepare_texture_data(name_failed, img, False))
                        except Exception:
                            pass
            except Exception as e:
                print(f"TXD GPU ERROR: {e}")

        # CPU fallback for any DXT1 textures NVTT couldn't handle
        for d in cpu_fallback_dxt1:
            try:
                result = process_texture_parallel(d)
                if result:
                    tex_natives.append(result)
            except Exception as e:
                print(f"TXD CPU fallback ERROR: {e}")

        # DXT3 (alpha) — keep on CPU because nvcompress's BC2 output
        # doesn't round-trip cleanly through SA's TXD reader.
        if dxt3_images:
            dxt3_data_local = []
            for i, (name, image, _) in enumerate(dxt3_images):
                wm.progress_update(total + dxt1_count + i)
                try:
                    dxt3_data_local.append(prepare_texture_data(name, image, True))
                except Exception as e:
                    print(f"TXD CPU (DXT3) prepare ERROR: {name}: {e}")
            for d in dxt3_data_local:
                try:
                    result = process_texture_parallel(d)
                    if result:
                        tex_natives.append(result)
                except Exception as e:
                    print(f"TXD CPU (DXT3) ERROR: {e}")
    else:
        # CPU режим - обрабатываем в правильном порядке (DXT1 первыми)
        # Sequential — Blender extensions ToS prefers no threading; DXT
        # encoding is fast enough on a single core for typical TXDs.

        # Сначала DXT1
        for i, data in enumerate(dxt1_data):
            wm.progress_update(total + i)
            try:
                result = process_texture_parallel(data)
                tex_natives.append(result)
            except Exception as e:
                print(f"TXD CPU ERROR: {e}")

        # Потом DXT3
        for i, data in enumerate(dxt3_data):
            wm.progress_update(total + dxt1_count + i)
            try:
                result = process_texture_parallel(data)
                tex_natives.append(result)
            except Exception as e:
                print(f"TXD CPU ERROR: {e}")

    wm.progress_end()

    if not tex_natives:
        return {'CANCELLED'}, "No textures could be processed", []

    tex_natives_data = bytearray()
    for tex_native in tex_natives:
        write_rw_section_header(tex_natives_data, RW_TEXTURENATIVE, len(tex_native))
        tex_natives_data.extend(tex_native)

    struct_section = bytearray()
    dict_struct = struct.pack('<HH', len(tex_natives), 0)
    write_rw_section_header(struct_section, RW_STRUCT, len(dict_struct))
    struct_section.extend(dict_struct)

    extension_data = bytearray()
    write_rw_section_header(extension_data, RW_EXTENSION, 0)

    with open(filepath, 'wb') as f:
        content_size = len(struct_section) + len(tex_natives_data) + len(extension_data)
        f.write(struct.pack('<III', RW_TEXDICTIONARY, content_size, RW_VERSION))
        f.write(struct_section)
        f.write(tex_natives_data)
        f.write(extension_data)

    msg = f"Exported {dxt1_count} DXT1 + {dxt3_count} DXT3 ({mode_name})"
    if skipped_textures:
        msg += f"\nПРОПУЩЕНО (размер не кратен 4): {', '.join(skipped_textures)}"
    return {'FINISHED'}, msg, transparent_list
