#!/usr/bin/env python3
"""
INU GTA SA Asset Library Builder — standalone CLI wrapper.

Thin shim around ``INU_tools.tools.build_library``. The real logic lives
in the addon module so the in-Blender operator (build_library_ops.py)
runs the exact same pipeline. This script is kept for power users who
prefer headless / scripted runs:

    blender --background --python dev/build_library.py -- ^
        --cache "C:\\path\\to\\.inu_cache" ^
        --game-root "C:\\Games\\GTA San Andreas" ^
        --output "F:\\INU_GTA_SA_Library"

Optional flags: see ``--help``.
"""

from __future__ import annotations

import argparse
import os
import sys


def parse_args():
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []

    p = argparse.ArgumentParser(
        prog='build_library.py',
        description='Build a Blender asset library from extracted GTA SA assets.')
    p.add_argument('--cache', required=True,
                   help='Path to .inu_cache folder produced by Extract Resources.')
    p.add_argument('--game-root', required=True,
                   help='GTA SA install root (used to read IDE files).')
    p.add_argument('--output', required=True,
                   help='Where to write the library (.blend files + textures/).')
    p.add_argument('--no-preview', action='store_true',
                   help='Skip preview rendering.')
    p.add_argument('--preview-size', type=int, default=128,
                   help='Preview thumbnail size in pixels (default: 128).')
    p.add_argument('--limit', type=int, default=0,
                   help='Stop after N DFFs per category (debug).')
    p.add_argument('--dry-run', action='store_true',
                   help='Classify only, do not write .blend files.')
    p.add_argument('--categories', default='',
                   help='Comma-separated categories to build (default: all).')
    p.add_argument('--skip-existing', action='store_true',
                   help='Skip categories whose .blend already exists in --output.')
    p.add_argument('--quiet-alpha', action='store_true', default=True,
                   help='Suppress per-material alpha-link logging (default: on).')
    p.add_argument('--delete-cache', action='store_true',
                   help='After successful build, delete <cache>/ to free disk space. '
                        'Forces texture copy (no symlink) so the library stays self-contained.')
    return p.parse_args(argv)


ARGS = parse_args()

import bpy  # noqa: E402

# Add INU_tools parent (this script's grandparent dir) to sys.path so
# ``import INU_tools.<sub>`` works whether or not the addon is installed.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Enable the addon: registers PropertyGroups (obj.inu, mat.inu) that the
# DFF importer writes into. addon_enable is idempotent.
try:
    bpy.ops.preferences.addon_enable(module='INU_tools')
except Exception as e:
    print(f"[Build Library] addon_enable failed ({e}); falling back to manual register")
    import INU_tools  # noqa: F401
    INU_tools.register()

from INU_tools.tools.build_library import build_library_iter  # noqa: E402


def main():
    args = ARGS
    cache = os.path.abspath(args.cache)
    game_root = os.path.abspath(args.game_root)
    output = os.path.abspath(args.output)

    print(f"[Build Library] cache     = {cache}")
    print(f"[Build Library] game_root = {game_root}")
    print(f"[Build Library] output    = {output}")
    print(f"[Build Library] preview   = "
          f"{'no' if args.no_preview else f'yes ({args.preview_size}px)'}")

    categories = None
    if args.categories.strip():
        categories = {c.strip() for c in args.categories.split(',') if c.strip()}
        print(f"      filter: only {sorted(categories)}")

    status: dict = {}
    gen = build_library_iter(
        cache_dir=cache,
        game_root=game_root,
        output_dir=output,
        status=status,
        no_preview=args.no_preview,
        preview_size=args.preview_size,
        limit=args.limit,
        categories=categories,
        skip_existing=args.skip_existing,
        quiet_alpha=args.quiet_alpha,
        dry_run=args.dry_run,
        delete_cache_after=args.delete_cache,
    )

    # Drain the generator. Standalone runs are fully synchronous — no
    # modal/timer dance needed; we just want progress prints which the
    # generator already emits via plain ``print`` calls.
    for _ in gen:
        pass

    if not args.dry_run:
        print()
        print("Next steps:")
        print("  1. Open Blender → Edit > Preferences > File Paths > Asset Libraries")
        print(f"  2. Add: {output}")
        print("  3. Open Asset Browser, pick the new library, browse by catalog.")


if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
