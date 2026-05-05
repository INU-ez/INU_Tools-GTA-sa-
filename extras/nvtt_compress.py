# NVTT (NVIDIA Texture Tools) GPU compression path for INU Tools.
#
# This module is INTENTIONALLY OUTSIDE the addon source tree (`INU_tools/`).
# It is copied into `INU_tools/tools/nvtt_compress.py` at build time by the
# `dev/build_extension.ps1` script — but only for the full GitHub release.
# The store build (extensions.blender.org) skips the copy, producing an
# extension zip that does NOT contain any subprocess calls or external-tool
# references — fully ToS-compliant ("self-contained, no external software").
#
# `INU_tools/tools/txd_export.py` contains a try-import wrapper that falls
# back to stubs when this module isn't present; the addon keeps working
# entirely on the bundled CPU encoder in that case.

import subprocess
import os
import struct
import tempfile

from .. import T


def check_nvtt_available(nvtt_path):
    """Проверить доступность NVIDIA Texture Tools."""
    if not nvtt_path or not os.path.isdir(nvtt_path):
        return False, T("Папка NVTT не найдена")
    nvcompress = os.path.join(nvtt_path, "nvcompress.exe")
    if not os.path.isfile(nvcompress):
        return False, T("nvcompress.exe не найден в указанной папке")
    return True, nvcompress


def _nvtt_prepare_png(name, image):
    """Save *image* as a PNG to the system temp dir for NVTT to read.

    Must run on the main thread — uses ``image.save()`` which is a
    Blender API call. Returns ``(name, input_png, output_dds, w, h)``
    so the parallel-safe second half can pick up without touching bpy.
    """
    temp_dir = tempfile.gettempdir()
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    input_file = os.path.join(temp_dir, f"_nvtt_{safe_name}.png")
    output_file = os.path.join(temp_dir, f"_nvtt_{safe_name}.dds")

    old_path = image.filepath_raw
    old_format = image.file_format
    try:
        image.filepath_raw = input_file
        image.file_format = 'PNG'
        image.save()
    finally:
        image.filepath_raw = old_path
        image.file_format = old_format

    width, height = image.size[0], image.size[1]
    return name, input_file, output_file, width, height


def _nvtt_compress_and_parse(prepared, use_alpha, nvcompress_path):
    """Run ``nvcompress.exe`` on the pre-saved PNG and assemble a
    Native Texture chunk from the resulting DDS. Pure-Python — no
    bpy access — so it's safe to run in a ``ThreadPoolExecutor``
    worker. Returns the texture-native bytes or ``None`` on failure.
    """
    name, input_file, output_file, width, height = prepared

    # ``-bc1`` = DXT1, ``-bc2`` = DXT3. Alpha-flag tells nvcompress
    # that the source PNG has a meaningful alpha channel.
    fmt = "-bc2" if use_alpha else "-bc1"
    alpha_flag = ["-alpha"] if use_alpha else []
    cmd_nocuda = [nvcompress_path, "-nocuda", fmt, "-mipmap"] + alpha_flag + [input_file, output_file]
    cmd_cuda = [nvcompress_path, fmt, "-mipmap"] + alpha_flag + [input_file, output_file]

    result = subprocess.run(cmd_cuda, capture_output=True, timeout=60)
    if result.returncode != 0:
        result = subprocess.run(cmd_nocuda, capture_output=True, timeout=60)

    if not os.path.exists(output_file):
        return None
    return _build_tex_native_from_dds(name, output_file, use_alpha)


def compress_with_nvtt(name, image, use_alpha, nvcompress_path):
    """Сжать текстуру через NVIDIA Texture Tools (GPU).

    Backward-compatible serial entry point — saves the PNG and runs
    the compressor + DDS parse in one call. Newer code paths (Map
    Export, batch IMG export) split these stages so the subprocess
    spawn can fan out across worker threads.
    """
    try:
        prepared = _nvtt_prepare_png(name, image)
        return _nvtt_compress_and_parse(prepared, use_alpha, nvcompress_path)
    except Exception as e:
        print(f"NVTT ERROR: {name}: {e}")
        return None


def _build_tex_native_from_dds(name, output_file, use_alpha):
    """Read a DDS file and turn it into the RW Texture-Native chunk
    bytes (PLATFORM_D3D9, single TextureNative record). Pure I/O +
    binary fiddling — no bpy access. Cleans up the temp files
    (both the DDS output and the matching ``_nvtt_<name>.png``)
    before returning."""
    # Lazy import — avoids circular when txd_export.py try-imports us.
    from .txd_export import (
        PLATFORM_D3D9, RASTER_565, RASTER_8888, RASTER_MIPMAP,
        RW_STRUCT, RW_EXTENSION,
        make_filter_flags, write_rw_section_header,
    )

    input_file = output_file.replace('.dds', '.png')
    try:
        with open(output_file, 'rb') as f:
            dds_data = f.read()
        if dds_data[:4] != b'DDS ':
            return None

        dds_height = struct.unpack('<I', dds_data[12:16])[0]
        dds_width = struct.unpack('<I', dds_data[16:20])[0]
        mip_count = struct.unpack('<I', dds_data[28:32])[0]
        if mip_count == 0:
            mip_count = 1

        # DX10 extended header pushes the pixel block 20 bytes further.
        pf_fourcc = dds_data[84:88]
        header_size = 148 if pf_fourcc == b'DX10' else 128
        pixel_data = dds_data[header_size:]

        if use_alpha:
            dxt_type = 3
            raster_format = RASTER_8888 | RASTER_MIPMAP
            depth = 32
            block_size = 16
        else:
            dxt_type = 1
            raster_format = RASTER_565 | RASTER_MIPMAP
            depth = 16
            block_size = 8

        tex_name = name[:31].encode('ascii', errors='replace').ljust(32, b'\x00')
        fourcc = b'DXT1' if dxt_type == 1 else b'DXT3'

        struct_data = bytearray()
        struct_data.extend(struct.pack('<II', PLATFORM_D3D9, make_filter_flags()))
        struct_data.extend(tex_name)
        struct_data.extend(b'\x00' * 32)
        struct_data.extend(struct.pack('<I', raster_format))
        struct_data.extend(fourcc)
        struct_data.extend(struct.pack('<HH', dds_width, dds_height))
        struct_data.extend(struct.pack('<B', depth))
        struct_data.extend(struct.pack('<B', mip_count))
        struct_data.extend(struct.pack('<B', 4))   # raster type
        struct_data.extend(struct.pack('<B', 0x08))  # D3D format flag

        offset = 0
        mip_w, mip_h = dds_width, dds_height
        for _ in range(mip_count):
            blocks_x = max(1, (mip_w + 3) // 4)
            blocks_y = max(1, (mip_h + 3) // 4)
            mip_size = blocks_x * blocks_y * block_size

            if offset + mip_size <= len(pixel_data):
                mip_data = pixel_data[offset:offset + mip_size]
                struct_data.extend(struct.pack('<I', len(mip_data)))
                struct_data.extend(mip_data)
                offset += mip_size

            mip_w = max(1, mip_w // 2)
            mip_h = max(1, mip_h // 2)

        tex_native = bytearray()
        write_rw_section_header(tex_native, RW_STRUCT, len(struct_data))
        tex_native.extend(struct_data)
        write_rw_section_header(tex_native, RW_EXTENSION, 0)

        return bytes(tex_native)

    except Exception as e:
        print(f"NVTT ERROR: {name}: {e}")
        return None

    finally:
        for tmp in (input_file, output_file):
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
