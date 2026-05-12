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
    # Полное имя модуля аддона в текущем install-mode:
    #   • Legacy:  'INU_tools'
    #   • Extension (4.2+): 'bl_ext.<repo>.<addon_basename>'
    # Operator passes own __package__ root так что worker не гадает.
    p.add_argument('--addon-module', default='',
                   help='Full python module name of the addon (passed from '
                        'the parent operator). Auto-detected from __file__ '
                        'if empty.')
    return p.parse_args(argv)


def _detect_addon_module() -> str:
    """Derive the addon's python module name from this worker's path.

    Two install modes covered:
      • Legacy `scripts/addons/INU_tools/scripts/build_library_worker.py`
        → 'INU_tools'
      • Extension `extensions/<repo>/<addon>/scripts/build_library_worker.py`
        → 'bl_ext.<repo>.<addon>'

    Used as a fallback when `--addon-module` isn't passed by the parent
    operator (e.g., during direct CLI invocation from `dev/`).
    """
    worker_file = os.path.abspath(__file__)
    scripts_dir = os.path.dirname(worker_file)
    addon_dir = os.path.dirname(scripts_dir)
    addon_basename = os.path.basename(addon_dir)
    parent_dir = os.path.dirname(addon_dir)
    parent_basename = os.path.basename(parent_dir)
    # Extension install lives under `…/extensions/<repo>/<addon>/`. The
    # signature: parent's parent is named `extensions`. Anything else we
    # treat as legacy (parent is `addons` или ad-hoc dev path).
    grand = os.path.basename(os.path.dirname(parent_dir))
    if grand == 'extensions':
        return f'bl_ext.{parent_basename}.{addon_basename}'
    return addon_basename


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
    import importlib

    # Resolve addon module name. Operator passes it via --addon-module
    # (knows its own __package__); if missing — auto-detect from path.
    addon_module = args.addon_module or _detect_addon_module()
    print(f"[Worker] addon module = {addon_module}", flush=True)

    # Make the addon importable. When the worker is launched from a
    # running Blender (operator-mode), the addon is already installed
    # and `addon_enable` finds it by name. For dev-mode (direct CLI)
    # we put the repo parent on sys.path so `import INU_tools` resolves.
    _this = os.path.dirname(os.path.abspath(__file__))
    _pkg_root = os.path.dirname(os.path.dirname(_this))
    if _pkg_root not in sys.path:
        sys.path.insert(0, _pkg_root)

    try:
        bpy.ops.preferences.addon_enable(module=addon_module)
    except Exception as e:
        print(f"[Worker] addon_enable({addon_module}) failed ({e}); "
              f"falling back to manual register", flush=True)
        try:
            mod = importlib.import_module(addon_module)
            if hasattr(mod, 'register'):
                mod.register()
        except Exception as e2:
            print(f"[Worker] manual register failed: {e2}", flush=True)
            raise

    build_library_module = importlib.import_module(
        f'{addon_module}.tools.build_library')
    build_library_iter = build_library_module.build_library_iter

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
