"""Headless Asset Library builder — worker process.

Runs inside `blender --background --python ...` spawned by
`ops/build_library_ops.py`. Wraps the same `build_library_iter`
generator that the in-process operator uses, but drains it end-to-end
without UI yields — that is the whole speed-up over the modal pump.

Two stdout protocols share the pipe:
  - Plain text lines  → existing print() calls in build_library.py
  - JSON-progress     → ``__INU_JSON__{json}\\n`` after every yield
                         (the parent operator parses these to drive its
                          progress bar; everything else is logged for
                          debugging on subprocess failure).

Argv layout (after `--`):
    --cache PATH        : .inu_cache directory produced by Extract Resources
    --game-root PATH    : GTA SA install root (IDE files)
    --output PATH       : where to write the library .blend files
    --no-preview        : skip thumbnail rendering
    --preview-size N    : thumbnail size (default 128)
    --skip-existing     : skip categories whose .blend already exists
    --delete-cache      : delete cache after successful build
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def _parse_args():
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []

    p = argparse.ArgumentParser(prog='build_library_worker.py')
    p.add_argument('--cache', required=True)
    p.add_argument('--game-root', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--no-preview', action='store_true')
    p.add_argument('--preview-size', type=int, default=128)
    p.add_argument('--skip-existing', action='store_true')
    p.add_argument('--delete-cache', action='store_true')
    p.add_argument('--categories', default='',
                   help='Comma-separated subset of categories to build '
                        '(default: all). Empty string = no filter.')
    return p.parse_args(argv)


def _emit_progress(status: dict):
    """Write one JSON-line so the parent operator can parse progress.

    Use a magic prefix so plain stdout (informational prints from
    build_library.py) doesn't get mistaken for progress data.
    """
    try:
        line = '__INU_JSON__' + json.dumps(status, ensure_ascii=False)
    except (TypeError, ValueError):
        return
    print(line, flush=True)


def main():
    args = _parse_args()

    import bpy  # noqa: E402

    # Make the addon importable. When the worker is launched from a
    # running Blender (operator-mode), the addon is already installed in
    # `<config>/scripts/addons/INU_tools/` and `addon_enable` finds it
    # by name. When the worker is run directly from the repo (dev mode),
    # we put the repo root on sys.path so `import INU_tools` resolves.
    _this = os.path.dirname(os.path.abspath(__file__))
    _pkg_root = os.path.dirname(os.path.dirname(_this))  # parent of INU_tools
    if _pkg_root not in sys.path:
        sys.path.insert(0, _pkg_root)

    try:
        bpy.ops.preferences.addon_enable(module='INU_tools')
    except Exception as e:
        print(f"[Worker] addon_enable failed ({e}); falling back to manual register",
              flush=True)
        import INU_tools  # noqa: F401
        INU_tools.register()

    from INU_tools.tools.build_library import build_library_iter

    cache = os.path.abspath(args.cache)
    game_root = os.path.abspath(args.game_root)
    output = os.path.abspath(args.output)

    print(f"[Worker] cache     = {cache}", flush=True)
    print(f"[Worker] game_root = {game_root}", flush=True)
    print(f"[Worker] output    = {output}", flush=True)
    print(f"[Worker] preview   = "
          f"{'no' if args.no_preview else f'yes ({args.preview_size}px)'}",
          flush=True)

    categories = None
    if args.categories.strip():
        categories = {c.strip() for c in args.categories.split(',') if c.strip()}
        print(f"[Worker] categories filter: {sorted(categories)}", flush=True)

    status: dict = {}
    gen = build_library_iter(
        cache_dir=cache,
        game_root=game_root,
        output_dir=output,
        status=status,
        no_preview=args.no_preview,
        preview_size=args.preview_size,
        categories=categories,
        skip_existing=args.skip_existing,
        delete_cache_after=args.delete_cache,
    )

    # Drain the generator. Headless mode is fully synchronous — no modal/
    # timer slicing. After each yield the worker emits a JSON-progress
    # line so the parent operator can repaint its progress bar without
    # re-running any of the heavy work itself.
    last_emit_keys: tuple = ()
    for _ in gen:
        # Cheap dedup: skip emit if the keys we care about haven't changed
        # (cuts stdout volume on long categories where status flips many
        # times per asset).
        cur_keys = (
            status.get('phase'),
            status.get('category'),
            status.get('cat_done'),
            status.get('current_asset'),
        )
        if cur_keys != last_emit_keys:
            _emit_progress(dict(status))
            last_emit_keys = cur_keys

    # Final summary so the parent reports «done» with stats.
    _emit_progress({
        'phase': 'done',
        'classified': status.get('classified', 0),
        'cat_done': status.get('cat_done', 0),
    })


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
