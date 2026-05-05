"""User-writable data directory for INU Tools.

Per Blender ToS, addons must not write files in their own directory
(extensions repository may be on read-only filesystem). This module
provides ``get_user_data_dir(subfolder)`` which resolves to a
user-isolated directory via ``bpy.utils.extension_path_user``
(Blender 4.2+) or ``bpy.utils.user_resource('CONFIG')`` fallback.

Subfolders used by INU Tools:
    profiles/           — N-sidebar layout profiles (tools/profiles.py)
    material_presets/   — GTA Material panel JSON presets
    id_presets/         — Model ID Manager presets
    paths.json          — saved game paths (top-level file, no subfolder)

Migration from the legacy ``<addons>/INU_Preset/...`` location is
performed by ``migrate_legacy_inu_preset()`` and called once at
addon register time.
"""

from __future__ import annotations

import os
import shutil

import bpy


# Top-level addon package name. From inside this submodule
# ``__package__`` is ``INU_tools.tools`` (legacy) or
# ``bl_ext.<repo>.inu_tools_gta_sa.tools`` (extension format).
# Strip the trailing ``.tools`` segment to get the addon root.
_ADDON_PACKAGE = __package__.rsplit('.', 1)[0]


def get_user_data_dir(subfolder: str = "") -> str:
    """Return the user data directory for INU Tools.

    Args:
        subfolder: optional sub-directory under the data root.
            Created if missing.

    Returns:
        Absolute path. Always created (with parents) before return.
    """
    base = None
    if hasattr(bpy.utils, 'extension_path_user'):
        try:
            base = bpy.utils.extension_path_user(
                _ADDON_PACKAGE, path='', create=True)
        except (ValueError, TypeError):
            base = None
    if base is None:
        # Pre-4.2 fallback or extension API rejected the package name.
        base = bpy.utils.user_resource('CONFIG', path='inu_tools')
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        pass
    if subfolder:
        path = os.path.join(base, subfolder)
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass
        return path
    return base


def _legacy_inu_preset_dir() -> str:
    """Old location: ``<blender addons dir>/INU_Preset/``.

    Pre-Step 8 (extensions.blender.org review) the addon wrote user
    data in a sibling folder next to ``INU_tools/``. This is no longer
    allowed by the platform — files now live in the user config
    directory. The path is still computed so the one-time migration
    can pull data forward.
    """
    addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    addons_dir = os.path.dirname(addon_dir)
    return os.path.join(addons_dir, 'INU_Preset')


# Marker file written into the new dir after a successful migration so
# we don't repeat the copy on every register.
_MIGRATION_MARKER = '.migrated_from_inu_preset'


def migrate_legacy_inu_preset() -> int:
    """Copy user data from ``<addons>/INU_Preset/`` to the new user
    data directory. Idempotent — drops a marker file after the first
    successful run so subsequent registers are no-ops.

    Returns:
        Number of files copied. 0 means nothing to migrate (either
        already migrated or the legacy directory never existed).
    """
    new_root = get_user_data_dir()
    marker = os.path.join(new_root, _MIGRATION_MARKER)
    if os.path.isfile(marker):
        return 0  # already migrated

    legacy = _legacy_inu_preset_dir()
    if not os.path.isdir(legacy):
        # No legacy data on this install — drop the marker so we don't
        # keep checking on every register.
        try:
            with open(marker, 'w', encoding='utf-8') as f:
                f.write('no-legacy-data\n')
        except Exception:
            pass
        return 0

    copied = 0
    for entry in os.listdir(legacy):
        src = os.path.join(legacy, entry)
        dst = os.path.join(new_root, entry)
        try:
            if os.path.isdir(src):
                if not os.path.exists(dst):
                    shutil.copytree(src, dst)
                    copied += sum(len(files) for _, _, files in os.walk(dst))
                else:
                    # Merge — copy only files that don't exist in destination.
                    for root, _, files in os.walk(src):
                        rel = os.path.relpath(root, src)
                        target_dir = os.path.join(dst, rel) if rel != '.' else dst
                        os.makedirs(target_dir, exist_ok=True)
                        for fn in files:
                            s = os.path.join(root, fn)
                            d = os.path.join(target_dir, fn)
                            if not os.path.exists(d):
                                shutil.copy2(s, d)
                                copied += 1
            elif os.path.isfile(src):
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    copied += 1
        except Exception as e:
            print(f"[INU user_data] migration error for {entry}: {e}")

    try:
        with open(marker, 'w', encoding='utf-8') as f:
            f.write(f'migrated {copied} files from {legacy}\n')
    except Exception:
        pass

    if copied > 0:
        print(f"[INU user_data] migrated {copied} files from {legacy} → {new_root}")
    return copied
