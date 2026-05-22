# INU_tools.core.txd_mobile
# Detection helpers for the 4-file mobile TXD container used by GTA SA
# iOS / Android (and VC mobile).
#
# Mobile builds replace RW TextureNative with a custom container split
# across four parallel files sharing a basename + format-extension:
#
#   <name>.<fmt>.txt   — property table (texture names, w/h, alpha flags)
#   <name>.<fmt>.toc   — offset table for fast seek into .dat
#   <name>.<fmt>.dat   — packed pixel data (PVRTC / ETC1 / DXT depending
#                        on <fmt>)
#   <name>.<fmt>.tmb   — thumbnails for in-game previews
#
# <fmt> ∈ {pvr (iOS), etc (Android, ETC1), dxt (Android, S3TC)}.
#
# This module ONLY detects the container and exposes the list of files.
# Pixel-level decoding (PVRTC / ETC1) requires a C-extension codec
# (e.g. texture2ddecoder) and is intentionally not implemented in pure
# Python — when the addon hits a mobile TXD it points the user at
# TxdGen for the PC↔mobile conversion instead of half-working in-house.

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


MOBILE_TXD_EXTS = ('.pvr', '.etc', '.dxt')
MOBILE_TXD_SUFFIXES = ('.txt', '.toc', '.dat', '.tmb')


@dataclass
class MobileTxdContainer:
    """Describes a detected 4-file mobile TXD container."""
    base_path: str = ''      # path WITHOUT the .{txt|toc|dat|tmb} suffix
    fmt: str = ''            # 'pvr' / 'etc' / 'dxt'
    txt_path: str = ''
    toc_path: str = ''
    dat_path: str = ''
    tmb_path: str = ''
    file_sizes: dict = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return all((self.txt_path, self.toc_path, self.dat_path))


def detect_mobile_txd(path: str) -> Optional[MobileTxdContainer]:
    """Try to recognise *path* as part of a mobile TXD container.

    *path* can point to any of the four files (.txt / .toc / .dat / .tmb)
    or to the bare base (no suffix). Returns a populated
    MobileTxdContainer if at least .txt + .toc + .dat exist alongside,
    None otherwise.
    """
    if not path:
        return None

    p = path
    suffix = ''
    fmt = ''
    # Strip the trailing piece (.txt/.toc/.dat/.tmb) so 'base' is e.g.
    # '/data/gta3.pvr'. Then strip the format extension to learn 'fmt'.
    for s in MOBILE_TXD_SUFFIXES:
        if p.lower().endswith(s):
            p = p[: -len(s)]
            suffix = s
            break

    lower = p.lower()
    for ext in MOBILE_TXD_EXTS:
        if lower.endswith(ext):
            fmt = ext[1:]      # 'pvr' / 'etc' / 'dxt'
            break

    if not fmt:
        return None

    base = p   # e.g. '/data/gta3.pvr'
    cont = MobileTxdContainer(base_path=base, fmt=fmt)
    cont.txt_path = base + '.txt'
    cont.toc_path = base + '.toc'
    cont.dat_path = base + '.dat'
    cont.tmb_path = base + '.tmb'

    found_any = False
    for attr in ('txt_path', 'toc_path', 'dat_path', 'tmb_path'):
        fp = getattr(cont, attr)
        if os.path.isfile(fp):
            cont.file_sizes[attr] = os.path.getsize(fp)
            found_any = True
        else:
            setattr(cont, attr, '')

    if not found_any:
        return None
    return cont


def container_summary(cont: MobileTxdContainer) -> str:
    """Human-readable description for logs / Operator.report() output."""
    pieces = [f"Mobile TXD container ({cont.fmt.upper()})"]
    for attr, label in (('txt_path', 'meta'), ('toc_path', 'toc'),
                        ('dat_path', 'data'), ('tmb_path', 'thumb')):
        fp = getattr(cont, attr)
        if fp:
            size = cont.file_sizes.get(attr, 0)
            pieces.append(f"{label}={os.path.basename(fp)} ({size} B)")
        else:
            pieces.append(f"{label}=<missing>")
    return ' | '.join(pieces)


class MobileTxdPixelDecodeUnsupported(NotImplementedError):
    """Raised when caller asks for actual pixel data from a mobile TXD.

    Decoding PVRTC / ETC1 in pure Python isn't shipped — point the user
    at TxdGen (external CLI) for PC↔mobile texture conversion.
    """

    def __init__(self, cont: MobileTxdContainer):
        super().__init__(
            f"Mobile TXD pixel decode is not implemented "
            f"({cont.fmt.upper()} in {os.path.basename(cont.dat_path)}). "
            f"Convert to PC TXD with TxdGen first."
        )
