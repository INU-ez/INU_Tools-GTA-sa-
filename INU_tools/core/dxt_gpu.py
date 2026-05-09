# INU_tools.core.dxt_gpu — bpy.gpu compute-shader DXT encoder.
#
# WORK IN PROGRESS. Currently slower than core.dxt (numpy) on typical
# TXDs because of per-mip dispatch overhead and Python list bridge,
# but kept for future improvement: a batched-dispatch + storage-buffer
# rewrite could realistically beat numpy on large maps.
#
# ── Architecture ────────────────────────────────────────────────────
# - Input: source RGBA8 image uploaded as RGBA32F GPUTexture.
# - Output: RGBA32F image, 4 × 16-bit values per block (c0, c1,
#   indices_lo16, indices_hi16). Blender 5.1 doesn't expose
#   GPUStorageBuf in Python (added in newer/Vulkan builds), so
#   storage-buffer output is unavailable. Splitting the 32-bit
#   indices into two 16-bit halves keeps every component ≤ 16 bits,
#   which fits in float32 mantissa exactly — round-trip through
#   GPUTexture.read() is bit-precise.
# - Algorithm in GLSL: identical to core.dxt — per-block mean + 3×3
#   covariance + 6-step power iteration → principal axis → projection
#   → quantize 565 → 4-color palette → nearest-index per pixel.

import numpy as np


# ───────────────────── GLSL kernel ─────────────────────
#
# Reads a 4×4 RGBA texel block via texelFetch, fits BC1 endpoints,
# packs (c0, c1, indices) into 2 × uint32 written to the storage
# buffer at index (block_y * blocks_x + block_x).

_BC1_GLSL = """
// Helper: fetch pixel i (0..15) of current block as vec3 RGB in [0,1].
vec3 fetch_pixel(ivec2 block, int i) {
    ivec2 coord = block * 4 + ivec2(i % 4, i / 4);
    return texelFetch(src_tex, coord, 0).rgb;
}

void main() {
    ivec2 block = ivec2(gl_GlobalInvocationID.xy);
    if (block.x >= blocks_x || block.y >= blocks_y) return;

    // Pass 1: mean of the 4×4 block.
    vec3 mean = vec3(0.0);
    for (int i = 0; i < 16; i++) mean += fetch_pixel(block, i);
    mean /= 16.0;

    // Pass 2: 3×3 covariance.
    mat3 cov = mat3(0.0);
    for (int i = 0; i < 16; i++) {
        vec3 c = fetch_pixel(block, i) - mean;
        cov[0][0] += c.x * c.x; cov[1][0] += c.x * c.y; cov[2][0] += c.x * c.z;
        cov[0][1] += c.y * c.x; cov[1][1] += c.y * c.y; cov[2][1] += c.y * c.z;
        cov[0][2] += c.z * c.x; cov[1][2] += c.z * c.y; cov[2][2] += c.z * c.z;
    }

    // Init axis from largest channel-variance, then 6-step power iteration.
    vec3 axis;
    if (cov[0][0] >= cov[1][1] && cov[0][0] >= cov[2][2]) axis = vec3(1.0, 0.0, 0.0);
    else if (cov[1][1] >= cov[2][2])                      axis = vec3(0.0, 1.0, 0.0);
    else                                                  axis = vec3(0.0, 0.0, 1.0);

    for (int it = 0; it < 6; it++) {
        axis = cov * axis;
        float n = length(axis);
        if (n < 1e-9) { axis = vec3(1.0, 0.0, 0.0); break; }
        axis /= n;
    }

    // Pass 3: project pixels onto axis, find range.
    float t0 = dot(fetch_pixel(block, 0) - mean, axis);
    float t_min = t0;
    float t_max = t0;
    for (int i = 1; i < 16; i++) {
        float t = dot(fetch_pixel(block, i) - mean, axis);
        t_min = min(t_min, t);
        t_max = max(t_max, t);
    }

    vec3 p_max = clamp(mean + axis * t_max, 0.0, 1.0);
    vec3 p_min = clamp(mean + axis * t_min, 0.0, 1.0);

    uvec3 q_max = uvec3(round(p_max * vec3(31.0, 63.0, 31.0)));
    uvec3 q_min = uvec3(round(p_min * vec3(31.0, 63.0, 31.0)));
    q_max = clamp(q_max, uvec3(0u), uvec3(31u, 63u, 31u));
    q_min = clamp(q_min, uvec3(0u), uvec3(31u, 63u, 31u));
    uint c0 = (q_max.r << 11) | (q_max.g << 5) | q_max.b;
    uint c1 = (q_min.r << 11) | (q_min.g << 5) | q_min.b;
    if (c0 < c1) { uint t = c0; c0 = c1; c1 = t; }

    uint r5 = (c0 >> 11) & 0x1Fu, g6 = (c0 >> 5) & 0x3Fu, b5 = c0 & 0x1Fu;
    vec3 p0 = vec3(float((r5 << 3) | (r5 >> 2)),
                   float((g6 << 2) | (g6 >> 4)),
                   float((b5 << 3) | (b5 >> 2))) / 255.0;
    r5 = (c1 >> 11) & 0x1Fu; g6 = (c1 >> 5) & 0x3Fu; b5 = c1 & 0x1Fu;
    vec3 p1 = vec3(float((r5 << 3) | (r5 >> 2)),
                   float((g6 << 2) | (g6 >> 4)),
                   float((b5 << 3) | (b5 >> 2))) / 255.0;
    vec3 palette[4];
    palette[0] = p0;
    palette[1] = p1;
    palette[2] = (2.0 * p0 + p1) / 3.0;
    palette[3] = (p0 + 2.0 * p1) / 3.0;

    // Pass 4: find nearest palette entry per pixel.
    bool single_color = (c0 == c1);
    uint indices = 0u;
    for (int i = 0; i < 16; i++) {
        uint best = 0u;
        if (!single_color) {
            vec3 px = fetch_pixel(block, i);
            float best_d = 1e30;
            for (uint k = 0u; k < 4u; k++) {
                vec3 d = px - palette[k];
                float dd = dot(d, d);
                if (dd < best_d) { best_d = dd; best = k; }
            }
        }
        indices |= best << uint(i * 2);
    }

    imageStore(out_blocks, block, vec4(
        float(c0),
        float(c1),
        float(indices & 0xFFFFu),
        float(indices >> 16)
    ));
}
"""


# ───────────────────── Module-level cache ─────────────────────

_gpu = None
_bc1_shader = None
_compute_available_cache = None


def _get_gpu():
    global _gpu
    if _gpu is None:
        import gpu  # raises ImportError outside Blender — caller handles
        _gpu = gpu
    return _gpu


def gpu_compute_available():
    """Return True iff bpy.gpu compute dispatch can be used here.

    Cached after first call. Probes by compiling a minimal compute
    shader — covers driver/format support and Blender API version
    (compute shaders need Blender 3.5+; we target 4.2+ via manifest)."""
    global _compute_available_cache
    if _compute_available_cache is not None:
        return _compute_available_cache
    try:
        gpu = _get_gpu()
        info = gpu.types.GPUShaderCreateInfo()
        info.compute_source("void main() {}")
        info.local_group_size(1, 1, 1)
        gpu.shader.create_from_info(info)
        _compute_available_cache = True
    except Exception as e:
        print(f"[dxt_gpu] compute unavailable: {e}")
        _compute_available_cache = False
    return _compute_available_cache


def _compile_bc1_shader():
    """Build the BC1 compute shader. Cached after first build."""
    global _bc1_shader
    if _bc1_shader is not None:
        return _bc1_shader
    gpu = _get_gpu()
    info = gpu.types.GPUShaderCreateInfo()
    info.sampler(0, 'FLOAT_2D', 'src_tex')
    # RGBA32F image output — 4 × 16-bit halves per block. See module
    # header comment for why storage buffers aren't usable here.
    info.image(0, 'RGBA32F', 'FLOAT_2D', 'out_blocks', qualifiers={'WRITE'})
    info.push_constant('INT', 'blocks_x')
    info.push_constant('INT', 'blocks_y')
    info.local_group_size(8, 8, 1)
    info.compute_source(_BC1_GLSL)
    _bc1_shader = gpu.shader.create_from_info(info)
    return _bc1_shader


# ───────────────────── Buffer upload ─────────────────────
#
# Creating a gpu.types.Buffer('FLOAT', size, data) with the data
# parameter is bottlenecked by Python iteration when data is a list.
# For 1024² RGBA = 4M floats, .tolist() + Buffer(list) takes ~50-100ms.
# Try cheaper paths first:
#   1. Pass numpy array directly       — Buffer may accept it via
#                                         buffer protocol (fast)
#   2. Pass numpy array via memoryview  — explicit conversion
#   3. Fall back to .tolist()           — slow but always works

_upload_strategy_cached = None  # 'numpy' | 'memview' | 'tolist'


def _make_float_buffer(gpu, flat_arr):
    """Create gpu.types.Buffer('FLOAT', n, data) from a 1D float32 numpy
    array via the fastest path that the running Blender accepts."""
    global _upload_strategy_cached
    n = flat_arr.size

    if _upload_strategy_cached in (None, 'numpy'):
        try:
            buf = gpu.types.Buffer('FLOAT', n, flat_arr)
            if _upload_strategy_cached is None:
                print("[dxt_gpu] upload: numpy-array path (fastest)")
            _upload_strategy_cached = 'numpy'
            return buf
        except Exception:
            pass

    if _upload_strategy_cached in (None, 'memview'):
        try:
            mv = memoryview(flat_arr)
            buf = gpu.types.Buffer('FLOAT', n, mv)
            if _upload_strategy_cached is None:
                print("[dxt_gpu] upload: memoryview path (fast)")
            _upload_strategy_cached = 'memview'
            return buf
        except Exception:
            pass

    if _upload_strategy_cached is None:
        print("[dxt_gpu] upload: tolist() fallback (slow)")
    _upload_strategy_cached = 'tolist'
    return gpu.types.Buffer('FLOAT', n, flat_arr.tolist())


# ───────────────────── Buffer readback ─────────────────────
#
# Reading a Blender RGBA32F Buffer back to numpy is surprisingly tricky
# in 5.1: recursive iteration mangles per-pixel components, plain
# np.array() may or may not work depending on Buffer protocol support,
# and bytes(buf) may raise BufferError on multi-dim non-C-contiguous
# storage. We try strategies in order of speed and fall through.
#
# Strategy timings (1024×1024 = 65536-block texture, rough estimates):
#   np.array(buf)          ~ 1 ms   (zero-copy if works)
#   np.frombuffer(bytes)   ~ 5 ms   (bytes() copies, frombuffer is free)
#   indexed Python loop    ~ 200 ms (slow but bulletproof — 262K Python ops)

_readback_strategy_cached = None
# Order: memview → bytes → asarray → rowwise → sliced → indexed (fallback)


def _verify_readback(arr, raw, h, w):
    """Sanity-check fast-path against indexed access on probe pixels."""
    try:
        for c in range(4):
            if abs(float(raw[0][0][c]) - float(arr[0, 0, c])) > 1e-3:
                return False
        if h > 1 or w > 1:
            yy, xx = h - 1, w - 1
            for c in range(4):
                if abs(float(raw[yy][xx][c]) - float(arr[yy, xx, c])) > 1e-3:
                    return False
        return True
    except Exception:
        return False


def _readback_rgba32f(raw, h, w):
    """Read an RGBA32F Buffer into a (h, w, 4) float32 numpy array.
    Caches the fastest working strategy after first call."""
    global _readback_strategy_cached
    target_shape = (h, w, 4)

    # Strategy 1: memoryview + np.frombuffer — if Buffer exposes the
    # buffer protocol with a flat layout, this is essentially zero-copy.
    if _readback_strategy_cached in (None, 'memview'):
        try:
            mv = memoryview(raw)
            arr = np.frombuffer(mv, dtype=np.float32)
            if arr.size == h * w * 4:
                arr = arr.reshape(target_shape).copy()
                if _readback_strategy_cached == 'memview' or _verify_readback(arr, raw, h, w):
                    if _readback_strategy_cached is None:
                        print("[dxt_gpu] readback: memoryview (fastest)")
                    _readback_strategy_cached = 'memview'
                    return arr
        except Exception:
            pass

    # Strategy 2: bytes() + np.frombuffer — bytes() may force a flat
    # contig copy where memoryview wouldn't expose one.
    if _readback_strategy_cached in (None, 'frombytes'):
        try:
            arr = np.frombuffer(bytes(raw), dtype=np.float32)
            if arr.size == h * w * 4:
                arr = arr.reshape(target_shape).copy()
                if _readback_strategy_cached == 'frombytes' or _verify_readback(arr, raw, h, w):
                    if _readback_strategy_cached is None:
                        print("[dxt_gpu] readback: bytes()+frombuffer (fast)")
                    _readback_strategy_cached = 'frombytes'
                    return arr
        except Exception:
            pass

    # Strategy 3: full-buffer np.array.
    if _readback_strategy_cached in (None, 'asarray'):
        try:
            arr = np.array(raw, dtype=np.float32)
            if arr.size == h * w * 4:
                arr = arr.reshape(target_shape)
                if _readback_strategy_cached == 'asarray' or _verify_readback(arr, raw, h, w):
                    if _readback_strategy_cached is None:
                        print("[dxt_gpu] readback: np.array (fast)")
                    _readback_strategy_cached = 'asarray'
                    return arr
        except Exception:
            pass

    # Strategy 4: row-by-row np.asarray.
    if _readback_strategy_cached in (None, 'rowwise'):
        try:
            arr = np.empty(target_shape, dtype=np.float32)
            for _y in range(h):
                arr[_y] = np.asarray(raw[_y], dtype=np.float32).reshape(w, 4)
            if _readback_strategy_cached == 'rowwise' or _verify_readback(arr, raw, h, w):
                if _readback_strategy_cached is None:
                    print("[dxt_gpu] readback: row-wise np.asarray (medium)")
                _readback_strategy_cached = 'rowwise'
                return arr
        except Exception:
            pass

    # Strategy 5: indexed loop with per-pixel slice.
    if _readback_strategy_cached in (None, 'sliced'):
        try:
            arr = np.empty(target_shape, dtype=np.float32)
            for _y in range(h):
                row = raw[_y]
                for _x in range(w):
                    arr[_y, _x] = row[_x][:]
            if _readback_strategy_cached == 'sliced' or _verify_readback(arr, raw, h, w):
                if _readback_strategy_cached is None:
                    print("[dxt_gpu] readback: per-pixel slice (slow)")
                _readback_strategy_cached = 'sliced'
                return arr
        except Exception:
            pass

    # Strategy 6 (bulletproof): per-component indexed loop.
    if _readback_strategy_cached is None:
        print("[dxt_gpu] readback: per-component indexed (slowest)")
    _readback_strategy_cached = 'indexed'
    arr = np.empty(target_shape, dtype=np.float32)
    for _y in range(h):
        row = raw[_y]
        for _x in range(w):
            pix = row[_x]
            arr[_y, _x, 0] = float(pix[0])
            arr[_y, _x, 1] = float(pix[1])
            arr[_y, _x, 2] = float(pix[2])
            arr[_y, _x, 3] = float(pix[3])
    return arr


# ───────────────────── Public encoders ─────────────────────

# Per-phase timing accumulators. ``read_wait`` is the GPU-bound part
# of readback (Blender's out_tex.read() waits for queued GPU work to
# finish). ``read_iter`` is the pure-Python cost of slicing the
# returned Buffer into a numpy array — that's where parallelization
# would actually help.
_timing = {'upload': 0.0, 'dispatch': 0.0, 'read_wait': 0.0,
           'read_iter': 0.0, 'pack': 0.0, 'count': 0}


def reset_timing():
    global _timing
    _timing = {'upload': 0.0, 'dispatch': 0.0, 'read_wait': 0.0,
               'read_iter': 0.0, 'pack': 0.0, 'count': 0}


def print_timing():
    n = _timing['count']
    if n == 0:
        return
    total = (_timing['upload'] + _timing['dispatch'] + _timing['read_wait']
             + _timing['read_iter'] + _timing['pack'])
    print(f"[dxt_gpu timing] {n} dispatches, total={total:.3f}s")
    for phase in ('upload', 'dispatch', 'read_wait', 'read_iter', 'pack'):
        t = _timing[phase]
        print(f"  {phase:10s} {t*1000:8.1f}ms ({100*t/total:5.1f}%)  avg/call {t*1000/n:6.2f}ms")


def encode_bc1_gpu_dispatch(rgba):
    """PHASE A (main thread only): upload, dispatch, and call read().
    Returns a handle (raw_buffer, blocks_x, blocks_y) that the
    finalize step turns into BC1 bytes — can run on a worker thread,
    making the slow Python iteration parallelizable."""
    return _encode_bc1_internal(rgba, finalize=False)


def encode_bc1_gpu_finalize(handle):
    """PHASE B (any thread): turn the readback Buffer into BC1 bytes.
    Pure Python + numpy, no GPU calls, safe to run in worker thread."""
    import time as _t
    raw, blocks_x, blocks_y = handle

    _t0 = _t.perf_counter()
    floats = _readback_rgba32f(raw, blocks_y, blocks_x)
    _timing['read_iter'] += _t.perf_counter() - _t0

    _t0 = _t.perf_counter()
    u16 = np.rint(floats).astype(np.uint32)
    c0 = u16[..., 0].flatten()
    c1 = u16[..., 1].flatten()
    idx_lo = u16[..., 2].flatten()
    idx_hi = u16[..., 3].flatten()
    indices = (idx_hi << 16) | idx_lo

    n_blocks = blocks_x * blocks_y
    out = np.empty((n_blocks, 8), dtype=np.uint8)
    out[:, 0] = c0 & 0xFF
    out[:, 1] = (c0 >> 8) & 0xFF
    out[:, 2] = c1 & 0xFF
    out[:, 3] = (c1 >> 8) & 0xFF
    out[:, 4] = indices & 0xFF
    out[:, 5] = (indices >> 8) & 0xFF
    out[:, 6] = (indices >> 16) & 0xFF
    out[:, 7] = (indices >> 24) & 0xFF
    result = out.tobytes()
    _timing['pack'] += _t.perf_counter() - _t0
    return result


def encode_bc1_gpu(rgba):
    """Single-call BC1 encoder (dispatch + finalize sequentially)."""
    return encode_bc1_gpu_finalize(encode_bc1_gpu_dispatch(rgba))


def _encode_bc1_internal(rgba, finalize):
    """Shared body — runs the GPU portion. If finalize=True, also runs
    the Python readback inline (legacy single-call path). If False,
    returns a handle for deferred finalize on a worker thread."""
    import time as _t
    if rgba.dtype != np.uint8 or rgba.ndim != 3 or rgba.shape[2] != 4:
        raise TypeError("encode_bc1_gpu: expected (H, W, 4) uint8 array")
    h, w = rgba.shape[:2]
    if h % 4 or w % 4:
        raise ValueError(f"encode_bc1_gpu: dimensions must be multiples of 4, got {w}x{h}")

    gpu = _get_gpu()
    blocks_x, blocks_y = w // 4, h // 4

    # ── PHASE 1: upload ────────────────────────────────────────────
    _t0 = _t.perf_counter()
    rgba_f = np.ascontiguousarray(rgba.astype(np.float32) / 255.0)
    flat = rgba_f.reshape(-1)  # 1D view, no copy if already contiguous
    src_buf = _make_float_buffer(gpu, flat)
    src_tex = gpu.types.GPUTexture((w, h), format='RGBA32F', data=src_buf)
    out_tex = gpu.types.GPUTexture((blocks_x, blocks_y), format='RGBA32F')
    _timing['upload'] += _t.perf_counter() - _t0

    # ── PHASE 2: dispatch ──────────────────────────────────────────
    _t0 = _t.perf_counter()
    shader = _compile_bc1_shader()
    shader.bind()
    shader.uniform_sampler('src_tex', src_tex)
    shader.image('out_blocks', out_tex)
    shader.uniform_int('blocks_x', blocks_x)
    shader.uniform_int('blocks_y', blocks_y)
    work_x = (blocks_x + 7) // 8
    work_y = (blocks_y + 7) // 8
    gpu.compute.dispatch(shader, work_x, work_y, 1)
    _timing['dispatch'] += _t.perf_counter() - _t0

    # ── PHASE 3a: GPU wait (out_tex.read() blocks for queued work) ──
    _t0 = _t.perf_counter()
    raw = out_tex.read()
    _timing['read_wait'] += _t.perf_counter() - _t0
    _timing['count'] += 1

    if not finalize:
        # Caller will run finalize on a worker thread.
        return (raw, blocks_x, blocks_y)

    # Single-call legacy path: finalize inline on calling thread.
    _t0 = _t.perf_counter()
    floats = _readback_rgba32f(raw, blocks_y, blocks_x)
    _timing['read_iter'] += _t.perf_counter() - _t0
    # ── PHASE 4: pack to BC1 byte stream ───────────────────────────
    _t0 = _t.perf_counter()
    u16 = np.rint(floats).astype(np.uint32)
    c0 = u16[..., 0].flatten()
    c1 = u16[..., 1].flatten()
    idx_lo = u16[..., 2].flatten()
    idx_hi = u16[..., 3].flatten()
    indices = (idx_hi << 16) | idx_lo

    n_blocks = blocks_x * blocks_y
    out = np.empty((n_blocks, 8), dtype=np.uint8)
    out[:, 0] = c0 & 0xFF
    out[:, 1] = (c0 >> 8) & 0xFF
    out[:, 2] = c1 & 0xFF
    out[:, 3] = (c1 >> 8) & 0xFF
    out[:, 4] = indices & 0xFF
    out[:, 5] = (indices >> 8) & 0xFF
    out[:, 6] = (indices >> 16) & 0xFF
    out[:, 7] = (indices >> 24) & 0xFF
    result = out.tobytes()
    _timing['pack'] += _t.perf_counter() - _t0
    return result


# ───────────────────── Diagnostic passthrough ─────────────────────
#
# Tools for narrowing down WHERE the GPU encoder diverges from the
# numpy reference. Two probes:
#
#   1. ``passthrough_test(rgba)`` — runs a compute shader that simply
#      copies texelFetch'd pixels to an RGBA32F output texture, with NO
#      encoding logic. Round-trips bytes through the entire upload +
#      sampling + imageStore + readback pipeline. If output != input,
#      the bug is OUTSIDE the BC1 algorithm (Y-flip, channel swap,
#      precision loss). If output == input, the BC1 algorithm itself
#      is the suspect.
#
#   2. ``compare_with_numpy(rgba)`` — encodes via both numpy and GPU,
#      diffs the BC1 byte streams, and prints the first divergent block
#      with both decoders' decoded RGB. Quickly tells you what KIND of
#      divergence we're seeing (whole-block-wrong vs subtle endpoint
#      drift).

_PASSTHROUGH_GLSL = """
void main() {
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    if (coord.x >= img_w || coord.y >= img_h) return;
    vec4 c = texelFetch(src_tex, coord, 0);
    imageStore(out_tex, coord, c);
}
"""

_passthrough_shader = None


def _compile_passthrough_shader():
    global _passthrough_shader
    if _passthrough_shader is not None:
        return _passthrough_shader
    gpu = _get_gpu()
    info = gpu.types.GPUShaderCreateInfo()
    info.sampler(0, 'FLOAT_2D', 'src_tex')
    info.image(0, 'RGBA32F', 'FLOAT_2D', 'out_tex', qualifiers={'WRITE'})
    info.push_constant('INT', 'img_w')
    info.push_constant('INT', 'img_h')
    info.local_group_size(8, 8, 1)
    info.compute_source(_PASSTHROUGH_GLSL)
    _passthrough_shader = gpu.shader.create_from_info(info)
    return _passthrough_shader


def passthrough_test(rgba):
    """Round-trip an image through GPU upload → texelFetch → imageStore
    → readback, with NO encoding. Returns the round-tripped (H, W, 4)
    uint8 array that came back from the GPU. Compare to ``rgba`` to
    diagnose upload/coord issues independently of the BC1 encoder."""
    if rgba.dtype != np.uint8 or rgba.ndim != 3 or rgba.shape[2] != 4:
        raise TypeError("passthrough_test: expected (H, W, 4) uint8")
    h, w = rgba.shape[:2]
    gpu = _get_gpu()

    rgba_f = (rgba.astype(np.float32) / 255.0)
    src_data = rgba_f.flatten().tolist()
    src_buf = gpu.types.Buffer('FLOAT', len(src_data), src_data)
    src_tex = gpu.types.GPUTexture((w, h), format='RGBA32F', data=src_buf)
    out_tex = gpu.types.GPUTexture((w, h), format='RGBA32F')

    shader = _compile_passthrough_shader()
    shader.bind()
    shader.uniform_sampler('src_tex', src_tex)
    shader.image('out_tex', out_tex)
    shader.uniform_int('img_w', w)
    shader.uniform_int('img_h', h)

    gpu.compute.dispatch(shader, (w + 7) // 8, (h + 7) // 8, 1)

    raw = out_tex.read()
    flat = []
    def _walk(item):
        if hasattr(item, '__iter__'):
            for sub in item:
                _walk(sub)
        else:
            flat.append(item)
    _walk(raw)
    arr = np.array(flat, dtype=np.float32).reshape(h, w, 4)
    return np.clip(np.rint(arr * 255), 0, 255).astype(np.uint8)


def compare_with_numpy(rgba, max_blocks_to_show=3):
    """Encode *rgba* via both numpy and GPU, byte-diff the streams,
    and print the first ``max_blocks_to_show`` divergent blocks with
    decoded RGB endpoints. Returns (n_blocks_total, n_blocks_differ)."""
    from .dxt import encode_bc1
    cpu = encode_bc1(rgba)
    gpu_bytes = encode_bc1_gpu(rgba)

    cpu_arr = np.frombuffer(cpu, dtype=np.uint8).reshape(-1, 8)
    gpu_arr = np.frombuffer(gpu_bytes, dtype=np.uint8).reshape(-1, 8)
    n_blocks = cpu_arr.shape[0]
    diff_mask = np.any(cpu_arr != gpu_arr, axis=1)
    n_differ = int(diff_mask.sum())

    print(f"[GPU diagnostic] {n_blocks} blocks total, {n_differ} differ "
          f"({100.0 * n_differ / n_blocks:.1f}%)")

    diff_idx = np.where(diff_mask)[0][:max_blocks_to_show]
    h, w = rgba.shape[:2]
    blocks_x = w // 4
    for k in diff_idx:
        by, bx = int(k) // blocks_x, int(k) % blocks_x
        print(f"  block ({bx},{by})  "
              f"CPU={cpu_arr[k].tobytes().hex()}  "
              f"GPU={gpu_arr[k].tobytes().hex()}")
        cc0 = cpu_arr[k, 0] | (cpu_arr[k, 1] << 8)
        cc1 = cpu_arr[k, 2] | (cpu_arr[k, 3] << 8)
        gc0 = gpu_arr[k, 0] | (gpu_arr[k, 1] << 8)
        gc1 = gpu_arr[k, 2] | (gpu_arr[k, 3] << 8)
        print(f"    CPU 565: c0=0x{cc0:04X} c1=0x{cc1:04X}  "
              f"GPU 565: c0=0x{gc0:04X} c1=0x{gc1:04X}")
    return n_blocks, n_differ


def encode_bc2_gpu_dispatch(rgba):
    """PHASE A (main thread): dispatch BC1 color + eagerly compute BC2
    alpha block (cheap numpy). Returns ``(bc1_handle, alpha_blocks)``."""
    from .dxt import _to_blocks, _bc2_alpha_blocks
    if rgba.dtype != np.uint8 or rgba.ndim != 3 or rgba.shape[2] != 4:
        raise TypeError("encode_bc2_gpu_dispatch: expected (H, W, 4) uint8 array")
    handle = encode_bc1_gpu_dispatch(rgba)
    blocks = _to_blocks(rgba)
    alpha_blocks = _bc2_alpha_blocks(blocks[..., 3])
    return (handle, alpha_blocks)


def encode_bc2_gpu_finalize(deferred):
    """PHASE B (any thread): finalize BC1 color, splice with alpha block."""
    handle, alpha_blocks = deferred
    color_bytes = encode_bc1_gpu_finalize(handle)
    color_arr = np.frombuffer(color_bytes, dtype=np.uint8).reshape(-1, 8)
    out = np.empty((color_arr.shape[0], 16), dtype=np.uint8)
    out[:, :8] = alpha_blocks
    out[:, 8:] = color_arr
    return out.tobytes()


def encode_bc2_gpu(rgba):
    """Single-call BC2 encoder (dispatch + finalize sequentially)."""
    return encode_bc2_gpu_finalize(encode_bc2_gpu_dispatch(rgba))
