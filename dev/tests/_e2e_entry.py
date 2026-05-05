"""Entry point launched by Blender (--background --python).

Blender's bundled Python ships without pytest. We install it on first
run, but we have to be careful WHERE it goes:

  * `pip install --user pytest` puts it in the user-site
    (~/AppData/Roaming/Python/PythonXY/site-packages on Windows), but
    Blender disables user-site by default, so the install "succeeds"
    and `import pytest` still fails. That's the trap to avoid.

  * Installing into Blender's bundled site-packages works as long as
    the install dir is writable by the current user (it usually is
    when Blender lives outside Program Files).

We add the user-site path to sys.path manually as well, so a pytest
installed previously via --user is also picked up.
"""
from __future__ import annotations

import os
import site
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
E2E_DIR = HERE / "e2e"


def _add_user_site_to_path():
    """Blender disables user-site (`site.ENABLE_USER_SITE = False`) so
    that addons don't accidentally pull in random user installs. We
    re-enable it here so a pre-existing `pip install --user pytest`
    is found without re-installing into Blender's bundle."""
    try:
        user_site = site.getusersitepackages()
    except Exception:
        return
    if user_site and Path(user_site).is_dir() and user_site not in sys.path:
        sys.path.insert(0, user_site)
        print(f"[e2e] added user-site to sys.path: {user_site}", flush=True)


def _ensure_pytest():
    _add_user_site_to_path()
    try:
        import pytest  # noqa: F401
        print(f"[e2e] pytest {pytest.__version__} found at {pytest.__file__}", flush=True)
        return
    except ImportError:
        pass

    print("[e2e] pytest not found — installing into Blender's bundled site-packages…", flush=True)
    # No --user: send it into Blender's own site-packages so it loads
    # next time without any sys.path tricks.
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])

    # The freshly-installed package needs site-packages re-scanned for
    # this process; importlib invalidate_caches handles that.
    import importlib
    importlib.invalidate_caches()


def main() -> int:
    _ensure_pytest()
    import pytest

    # -p no:cacheprovider: Blender's startup folder is sometimes read-only
    # for the test run user, and pytest's .pytest_cache write fails noisily.
    args = ["-v", "-p", "no:cacheprovider", str(E2E_DIR)]
    print(f"[e2e] running: pytest {' '.join(args)}", flush=True)
    return pytest.main(args)


if __name__ == "__main__":
    code = main()
    print(f"[e2e] pytest exit code: {code}", flush=True)
    # Blender ignores sys.exit() exit codes from --python scripts; the
    # only way to surface failure to the shell is bpy.ops.wm.quit_blender()
    # plus a sentinel file the runner reads. Simplest: write a status file.
    status_file = HERE / ".e2e_last_exit"
    status_file.write_text(str(code), encoding="utf-8")
    sys.exit(code)
