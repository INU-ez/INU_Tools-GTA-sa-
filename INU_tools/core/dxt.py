# INU_tools.core.dxt — vectorized numpy BC1 (DXT1) & BC3 (DXT5) encoder.
#
# Pure-numpy, MIT-licensed, no external dependencies. Designed for
# extensions.blender.org compliance: no subprocess, no external
# binaries, no closed-source libraries. Replaces the per-block Python
# loop in tools/txd_export.py with a single self-contained module —
# the addon's old external-binary subprocess path was dropped entirely.
#
# Algorithm: range-fit endpoints on the principal axis of each block
# (covariance largest eigenvector via 6-step power iteration),
# 4-color BC1 mode, 8-value BC3 alpha. Quality is in the same band
# as stb_dxt's "fast" range-fit; cluster-fit is not implemented
# because range-fit is enough for ~99% of real GTA-SA textures and
# 5–10× faster.
#
# Public API:
#     encode_bc1(rgba_u8) -> bytes      # H*W//2 bytes
#     encode_bc2(rgba_u8) -> bytes      # H*W bytes (DXT3, 4-bit explicit alpha)
#     encode_bc3(rgba_u8) -> bytes      # H*W bytes (DXT5, interpolated alpha)
#
# Input must be H×W×4 uint8 with H, W multiples of 4. Block order is
# row-major (block_y, block_x); pixels within a block are row-major
# (py, px) — matches the D3D9/DDS layout GTA SA's RW reader expects.

import numpy as np


# ---------------------------------------------------------------------------
# Block reshape: image (H, W, C) -> blocks (N, 16, C) in DDS-canonical order
# ---------------------------------------------------------------------------

def _to_blocks(rgba):
    h, w = rgba.shape[:2]
    bh, bw = h // 4, w // 4
    return rgba.reshape(bh, 4, bw, 4, -1).swapaxes(1, 2).reshape(bh * bw, 16, -1)


# ---------------------------------------------------------------------------
# 565 quantize / dequantize with bit-replication (matches GPU decoders)
# ---------------------------------------------------------------------------

def _to_565(rgb_u8):
    r5 = (rgb_u8[..., 0].astype(np.uint32) * 31 + 127) // 255
    g6 = (rgb_u8[..., 1].astype(np.uint32) * 63 + 127) // 255
    b5 = (rgb_u8[..., 2].astype(np.uint32) * 31 + 127) // 255
    return ((r5 << 11) | (g6 << 5) | b5).astype(np.uint16)


def _from_565(c565):
    r5 = (c565.astype(np.uint32) >> 11) & 0x1F
    g6 = (c565.astype(np.uint32) >> 5) & 0x3F
    b5 = c565.astype(np.uint32) & 0x1F
    r8 = (r5 << 3) | (r5 >> 2)
    g8 = (g6 << 2) | (g6 >> 4)
    b8 = (b5 << 3) | (b5 >> 2)
    return np.stack([r8, g8, b8], axis=-1).astype(np.uint8)


# ---------------------------------------------------------------------------
# Shared BC1 block packer
# ---------------------------------------------------------------------------
#
# Direct byte assembly for the 4-byte index field: avoids the (N, 16) uint32
# `idx << shifts; bitwise_or.reduce` materialization the old path used. Indices
# are packed pairwise into bytes via shifts+OR over 4 (N,) views.

def _pack_bc1_block(c0, c1, idx_u8):
    """Pack two RGB565 endpoints + (N, 16) 2-bit indices into 8 BC1 bytes.

    ``idx_u8`` must be uint8 with values in 0..3; ``c0``, ``c1`` are
    (N,) uint16. Output shape is (N, 8) uint8.
    """
    n = c0.shape[0]
    out = np.empty((n, 8), dtype=np.uint8)
    out[:, 0] = c0 & 0xFF
    out[:, 1] = (c0 >> 8) & 0xFF
    out[:, 2] = c1 & 0xFF
    out[:, 3] = (c1 >> 8) & 0xFF
    out[:, 4:8] = (idx_u8[:, 0::4]
                   | (idx_u8[:, 1::4] << 2)
                   | (idx_u8[:, 2::4] << 4)
                   | (idx_u8[:, 3::4] << 6))
    return out


# ---------------------------------------------------------------------------
# Per-block principal axis via covariance + 6-step power iteration
# ---------------------------------------------------------------------------

def _principal_axis(rgb):
    n = rgb.shape[0]
    mean = rgb.mean(axis=1)                                       # (N, 3)
    centered = rgb - mean[:, None, :]                             # (N, 16, 3)
    cov = np.einsum('nij,nik->njk', centered, centered)           # (N, 3, 3)

    # Init along channel with largest variance — converges in fewer iters
    # than a uniform [1,1,1] start, and avoids NaN on grayscale blocks.
    diag = np.stack([cov[:, 0, 0], cov[:, 1, 1], cov[:, 2, 2]], axis=-1)
    best = np.argmax(diag, axis=-1)
    axis = np.zeros((n, 3), dtype=np.float32)
    axis[np.arange(n), best] = 1.0

    fallback = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    for _ in range(6):
        axis = np.einsum('nij,nj->ni', cov, axis)
        norm = np.linalg.norm(axis, axis=1, keepdims=True)
        bad = norm.squeeze(-1) < 1e-9
        axis = np.where(bad[:, None], fallback, axis / np.maximum(norm, 1e-9))

    return axis.astype(np.float32), mean.astype(np.float32)


# ---------------------------------------------------------------------------
# BC1 color block (8 bytes): two RGB565 endpoints + 16×2-bit indices
# ---------------------------------------------------------------------------

def _bc1_color_blocks(rgb_f32):
    n = rgb_f32.shape[0]

    axis, mean = _principal_axis(rgb_f32)
    centered = rgb_f32 - mean[:, None, :]
    proj = np.einsum('nik,nk->ni', centered, axis)                # (N, 16)
    t_min = proj.min(axis=1)
    t_max = proj.max(axis=1)

    p_max = np.clip(mean + axis * t_max[:, None], 0, 255)
    p_min = np.clip(mean + axis * t_min[:, None], 0, 255)
    c0 = _to_565(np.rint(p_max).astype(np.uint8))
    c1 = _to_565(np.rint(p_min).astype(np.uint8))

    # 4-color mode requires color0 > color1; swap if quantization inverted them
    swap = c0 < c1
    c0_o = np.where(swap, c1, c0)
    c1_o = np.where(swap, c0, c1)
    c0, c1 = c0_o, c1_o

    p0 = _from_565(c0).astype(np.float32)                         # (N, 3)
    p1 = _from_565(c1).astype(np.float32)
    palette = np.stack([
        p0, p1,
        (2.0 * p0 + p1) / 3.0,
        (p0 + 2.0 * p1) / 3.0,
    ], axis=1)                                                    # (N, 4, 3)

    diff = rgb_f32[:, :, None, :] - palette[:, None, :, :]
    dist = (diff * diff).sum(axis=-1)                             # (N, 16, 4)
    idx = np.argmin(dist, axis=-1).astype(np.uint8)               # (N, 16)

    # Constant-color blocks: c0 == c1 means we're technically in 3-color mode
    # (where index 3 = transparent black). Force all indices to 0 to avoid
    # the rare argmin tie-break landing on idx=3 → black-pixel artifact.
    constant = (c0 == c1)
    idx = np.where(constant[:, None], np.uint8(0), idx)

    return _pack_bc1_block(c0, c1, idx)


# ---------------------------------------------------------------------------
# BC3 alpha block (8 bytes): two alpha endpoints + 16×3-bit indices
# ---------------------------------------------------------------------------

# Weights on a0 for the 8-value (a0 > a1) palette:
#   palette[0] = a0
#   palette[1] = a1
#   palette[i] = ((8-i)*a0 + (i-1)*a1) / 7   for i in 2..7
_BC3_W_A0 = np.array(
    [1.0, 0.0, 6.0 / 7, 5.0 / 7, 4.0 / 7, 3.0 / 7, 2.0 / 7, 1.0 / 7],
    dtype=np.float32,
)


def _bc3_alpha_blocks(alpha_u8):
    n = alpha_u8.shape[0]
    a_max = alpha_u8.max(axis=1).astype(np.uint8)
    a_min = alpha_u8.min(axis=1).astype(np.uint8)

    a0 = a_max.astype(np.float32)
    a1 = a_min.astype(np.float32)
    w_a0 = _BC3_W_A0
    w_a1 = 1.0 - w_a0
    palette = a0[:, None] * w_a0[None, :] + a1[:, None] * w_a1[None, :]   # (N, 8)

    diff = alpha_u8[:, :, None].astype(np.float32) - palette[:, None, :]
    dist = diff * diff
    idx = np.argmin(dist, axis=-1).astype(np.uint64)                       # (N, 16)

    shifts = (np.arange(16, dtype=np.uint64) * 3)
    packed = np.bitwise_or.reduce(idx << shifts[None, :], axis=1).astype(np.uint64)

    out = np.zeros((n, 8), dtype=np.uint8)
    out[:, 0] = a_max
    out[:, 1] = a_min
    for i in range(6):
        out[:, 2 + i] = (packed >> np.uint64(i * 8)) & np.uint64(0xFF)
    return out


# ---------------------------------------------------------------------------
# Public encoders
# ---------------------------------------------------------------------------

def _validate(rgba):
    if rgba.dtype != np.uint8:
        raise TypeError(f"expected uint8 RGBA, got {rgba.dtype}")
    if rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ValueError(f"expected (H, W, 4) array, got shape {rgba.shape}")
    h, w = rgba.shape[:2]
    if h % 4 or w % 4:
        raise ValueError(f"dimensions must be multiples of 4, got {w}x{h}")


def encode_bc1(rgba, fast=False):
    """Encode H×W×4 uint8 RGBA to BC1/DXT1. Returns H*W//2 bytes.

    ``fast=False`` (default): range-fit on the principal axis via
    covariance + 6-step power iteration. Best quality.
    ``fast=True``: bbox-fit (per-channel min/max), integer-only path —
    ~2–3× faster, ~0.5 dB lower PSNR on most textures.
    """
    _validate(rgba)
    blocks = _to_blocks(rgba)
    if fast:
        # Stay uint8 — avoids the 12 MB float32 materialization that
        # dominated bandwidth in the previous bbox path.
        return _bc1_color_blocks_bbox(blocks[..., :3]).tobytes()
    rgb = blocks[..., :3].astype(np.float32)
    return _bc1_color_blocks(rgb).tobytes()


# ---------------------------------------------------------------------------
# BC1 FAST variant — bbox endpoints + 1D projection index assignment.
#
# Two simplifications vs range-fit:
#   1. Endpoints from per-channel min/max (skip covariance + power iter).
#   2. Index per pixel via projection onto the (p_max - p_min) axis,
#      thresholded into 4 buckets (skip the per-pixel 4-palette
#      euclidean distance).
#
# This implementation is integer-only. The previous float32 version
# materialized (N, 16, 3) float32 + a same-shape `centered` + a same-shape
# product — ≈40 MB of L2-blowing temps for a 1024² mip. Working in
# uint8/int32 with einsum's fused multiply-accumulate cuts the working
# set ~4× and roughly halves wall-clock encode for the bbox path.
#
# Bucket math, integer form:
#   u = proj / norm_sq ∈ [0, 1]
#   bucket = clip(round(3·u), 0, 3)
#          = clip((6·proj + norm_sq) // (2·norm_sq), 0, 3)   for proj ≥ 0
# Equivalent to floor(3·u + 0.5) which the float path used.
# ---------------------------------------------------------------------------

def _bc1_color_blocks_bbox(rgb_u8):
    n = rgb_u8.shape[0]

    # Per-channel min/max → endpoints in original RGB space.
    p_min = rgb_u8.min(axis=1)                          # (N, 3) uint8
    p_max = rgb_u8.max(axis=1)

    # Quantize endpoints to 565 directly on uint8.
    c0 = _to_565(p_max)
    c1 = _to_565(p_min)

    # Force 4-color BC1 mode: c0 must be > c1.
    swap = c0 < c1
    c0_o = np.where(swap, c1, c0)
    c1_o = np.where(swap, c0, c1)
    c0, c1 = c0_o, c1_o

    # Projection axis = bbox diagonal, kept in int32. axis components
    # are each in [0, 255], so axis·axis ≤ 3·255² = 195075, well under int32.
    axis = p_max.astype(np.int32) - p_min.astype(np.int32)         # (N, 3)
    norm_sq = (axis * axis).sum(axis=-1)                            # (N,)

    # centered = rgb - p_min, all components ≥ 0 ⇒ uint8 modular subtraction
    # is mathematically correct here (no underflow because p_min is the
    # block-wise minimum).
    centered = rgb_u8 - p_min[:, None, :]                           # (N, 16, 3) uint8

    # einsum fuses the per-pixel dot with axis into a single int32 (N, 16),
    # so we never materialize the full (N, 16, 3) int32 product — that was
    # the dominant float-path cost.
    proj = np.einsum('nij,nj->ni', centered, axis,
                     dtype=np.int32, casting='unsafe')              # (N, 16) int32

    safe = np.where(norm_sq > 0, norm_sq, 1).astype(np.int32)       # (N,)
    qu = (6 * proj + safe[:, None]) // (2 * safe[:, None])
    qu = np.clip(qu, 0, 3).astype(np.int32)                         # (N, 16)

    # Index remap depends on whether endpoints got swapped.
    # Without swap: c0 = quantize(p_max), so palette[0]=p_max-side.
    #   bucket 0 (u→0) → idx 1, bucket 1 → idx 3, bucket 2 → idx 2, bucket 3 → idx 0
    # With swap: c0 = quantize(p_min), so palette[0]=p_min-side.
    #   bucket 0 → idx 0, bucket 1 → idx 2, bucket 2 → idx 3, bucket 3 → idx 1
    remap_no_swap = np.array([1, 3, 2, 0], dtype=np.uint8)
    remap_swap    = np.array([0, 2, 3, 1], dtype=np.uint8)
    idx = np.where(
        swap[:, None],
        remap_swap[qu],
        remap_no_swap[qu],
    ).astype(np.uint8)

    constant = (c0 == c1)
    idx = np.where(constant[:, None], np.uint8(0), idx)

    return _pack_bc1_block(c0, c1, idx)


# ---------------------------------------------------------------------------
# BC2 alpha block (8 bytes): 16×4-bit explicit alpha, no endpoints
# ---------------------------------------------------------------------------

def _bc2_alpha_blocks(alpha_u8):
    # Two 4-bit alpha values pack into one byte: pixel 2k → low nibble,
    # pixel 2k+1 → high nibble. Direct shift+OR over (N, 8) views avoids
    # the (N, 16) uint64 reduce the old path used.
    a4 = ((alpha_u8.astype(np.uint16) * 15 + 127) // 255).astype(np.uint8)
    return a4[:, 0::2] | (a4[:, 1::2] << 4)              # (N, 8) uint8


def encode_bc2(rgba, fast=False):
    """Encode H×W×4 uint8 RGBA to BC2/DXT3 (4-bit explicit alpha + BC1 color).
    See ``encode_bc1`` for the meaning of ``fast``."""
    _validate(rgba)
    blocks = _to_blocks(rgba)
    alpha = blocks[..., 3]

    if fast:
        color = _bc1_color_blocks_bbox(blocks[..., :3])
    else:
        color = _bc1_color_blocks(blocks[..., :3].astype(np.float32))

    alpha_b = _bc2_alpha_blocks(alpha)

    out = np.empty((color.shape[0], 16), dtype=np.uint8)
    out[:, :8] = alpha_b
    out[:, 8:] = color
    return out.tobytes()


def encode_bc3(rgba, fast=False):
    """Encode H×W×4 uint8 RGBA to BC3/DXT5 (interpolated alpha + BC1 color).
    See ``encode_bc1`` for the meaning of ``fast``."""
    _validate(rgba)
    blocks = _to_blocks(rgba)
    alpha = blocks[..., 3]

    if fast:
        color = _bc1_color_blocks_bbox(blocks[..., :3])
    else:
        color = _bc1_color_blocks(blocks[..., :3].astype(np.float32))

    alpha_b = _bc3_alpha_blocks(alpha)

    out = np.empty((color.shape[0], 16), dtype=np.uint8)
    out[:, :8] = alpha_b
    out[:, 8:] = color
    return out.tobytes()
