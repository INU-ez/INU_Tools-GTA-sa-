"""Static checks against extensions.blender.org rules and addon
manifest hygiene. These run on plain Python (no Blender required) so
they ride the existing CI lane.

Why these matter: a violation surfaces during the store review queue
and bumps the addon back to the end of it — sometimes weeks of delay
per round. Catching it here means the violation never makes it past
local pre-commit.

Source of rules:
- https://docs.blender.org/manual/en/latest/extensions/index.html
- The blender_manifest.toml field reference
- Past review feedback captured in
  memory/reference_blender_extensions_review.md
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


# ── Paths ────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]
ADDON_DIR = REPO_ROOT / "INU_tools"
MANIFEST_PATH = ADDON_DIR / "blender_manifest.toml"


def _addon_py_files():
    """All .py files inside the addon, excluding __pycache__."""
    return [
        p for p in ADDON_DIR.rglob("*.py")
        if "__pycache__" not in p.parts
    ]


# ── 1. Banned dynamic-execution builtins ─────────────────────────

# extensions.blender.org disallows arbitrary code execution: `eval`,
# `exec`, `compile`, `__import__` with a non-literal argument. The
# AST check below catches direct calls. `re.compile(...)` is a method
# on the `re` module, not the builtin `compile`, so it doesn't match.

BANNED_BUILTINS = {"eval", "exec", "compile"}


def _find_banned_calls(source: str, path: Path):
    """Yield (line, name) for every direct call to a banned builtin."""
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        # A syntax error is itself a critical problem — fail loudly.
        raise AssertionError(f"{path}: cannot parse ({e})") from e

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BANNED_BUILTINS:
                yield node.lineno, node.func.id


def test_no_eval_exec_compile_calls():
    """Walk every .py in the addon and assert none of them call
    `eval()`, `exec()`, or bare `compile()`. `re.compile(...)` is a
    method call (Attribute), not a builtin call, and is fine."""
    offenders: list[str] = []
    for path in _addon_py_files():
        source = path.read_text(encoding="utf-8")
        for line, name in _find_banned_calls(source, path):
            offenders.append(f"{path.relative_to(REPO_ROOT)}:{line} — {name}()")
    assert not offenders, (
        "Banned builtin calls found (extensions.blender.org rejects these):\n  "
        + "\n  ".join(offenders)
    )


def test_no_dunder_import_with_runtime_arg():
    """`__import__(name)` is fine when `name` is a string literal —
    that's just a static import in disguise. `__import__(some_var)`
    on the other hand is dynamic and gets rejected."""
    offenders: list[str] = []
    for path in _addon_py_files():
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "__import__"
                    and node.args
                    and not isinstance(node.args[0], ast.Constant)):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    assert not offenders, (
        "__import__() called with a non-literal argument:\n  "
        + "\n  ".join(offenders)
    )


# ── 2. subprocess audit ──────────────────────────────────────────
#
# subprocess isn't banned outright, but every call must be defensible:
# user-initiated, non-network, and not arbitrary code. The addon
# currently has exactly one subprocess.Popen (xdg-open the user's ID
# file on Linux). New ones should be reviewed before they land.

ALLOWED_SUBPROCESS_USES = {
    # Path -> reason. Update when adding a legitimate new caller.
    "INU_tools/ops/id_manager_ops.py": "xdg-open user-initiated file open",
    "INU_tools/tools/nvtt_compress.py": (
        "spawns the NVTT binary for hardware DXT compression; "
        "FULL build only — store build excludes this file entirely "
        "(verified by test_packaging.test_store_build_excludes_nvtt)"
    ),
}


def test_subprocess_uses_are_allowlisted():
    """Force a code-review checkpoint when a new file starts using
    subprocess. If the use is legitimate, add it to the allowlist
    above with a one-line reason."""
    used: dict[str, list[int]] = {}
    for path in _addon_py_files():
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            # Catches both `subprocess.Popen(...)` and `subprocess.run(...)`
            if (isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "subprocess"):
                rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
                used.setdefault(rel, []).append(node.lineno)
    unauthorised = {p: lines for p, lines in used.items()
                    if p not in ALLOWED_SUBPROCESS_USES}
    assert not unauthorised, (
        "subprocess used in non-allowlisted files:\n  "
        + "\n  ".join(f"{p}: lines {lines}" for p, lines in unauthorised.items())
        + "\n  If the use is legitimate, add it to ALLOWED_SUBPROCESS_USES "
          "with a one-line reason."
    )


# ── 3. Manifest validation ───────────────────────────────────────

REQUIRED_MANIFEST_FIELDS = {
    "schema_version", "id", "version", "name", "tagline",
    "maintainer", "type", "blender_version_min", "license", "tags",
}


def _load_manifest() -> dict:
    if sys.version_info >= (3, 11):
        import tomllib
        with MANIFEST_PATH.open("rb") as fh:
            return tomllib.load(fh)
    else:
        import tomli
        with MANIFEST_PATH.open("rb") as fh:
            return tomli.load(fh)


def test_manifest_parses_and_has_required_fields():
    data = _load_manifest()
    missing = REQUIRED_MANIFEST_FIELDS - set(data)
    assert not missing, f"manifest missing required fields: {sorted(missing)}"

    assert data["type"] == "add-on", "type must be 'add-on'"
    assert data["schema_version"] == "1.0.0", "schema_version must be 1.0.0"


def test_manifest_id_is_snake_case():
    """The extension id is the URL slug on extensions.blender.org and
    can't change between versions. Catch typos before the first
    submission, when changing it is still painless."""
    data = _load_manifest()
    assert re.fullmatch(r"[a-z][a-z0-9_]+", data["id"]), (
        f"id {data['id']!r} must be lowercase snake_case (no dashes/dots)")


def test_manifest_version_is_semver():
    data = _load_manifest()
    v = data["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", v), (
        f"version {v!r} must be MAJOR.MINOR.PATCH")


def test_manifest_blender_version_min_is_supported():
    """Pin the floor at 4.2.0 — that's when the extension API stabilised.
    Anything lower means we're shipping legacy add-on metadata that
    extensions.blender.org won't accept."""
    data = _load_manifest()
    bvm = data["blender_version_min"]
    parts = tuple(int(x) for x in bvm.split("."))
    assert parts >= (4, 2, 0), (
        f"blender_version_min {bvm} is below 4.2.0; the extensions API "
        "isn't available on older Blender")


def test_manifest_tags_are_official():
    """Only tags from Blender's official taxonomy are accepted; any
    custom string lands the addon back in the review queue."""
    # https://docs.blender.org/manual/en/latest/extensions/tags.html
    OFFICIAL = {
        "3D View", "Add Curve", "Add Mesh", "Animation", "Bake",
        "Camera", "Compositing", "Development", "Game Engine",
        "Geometry Nodes", "Grease Pencil", "Import-Export",
        "Lighting", "Material", "Mesh", "Modeling", "Node",
        "Object", "Paint", "Pipeline", "Physics", "Render", "Rigging",
        "Scene", "Sculpt", "Sequencer", "System", "Text Editor",
        "Tracking", "User Interface", "UV",
    }
    data = _load_manifest()
    bad = [t for t in data.get("tags", []) if t not in OFFICIAL]
    assert not bad, (
        f"tags not in official taxonomy: {bad}\n"
        f"Allowed: {sorted(OFFICIAL)}")


def test_manifest_permission_reasons_no_trailing_punctuation():
    """Past review feedback (memory/reference_blender_extension_manifest.md):
    extensions.blender.org rejects permission reasons ending in `.`,
    `!`, or `?`. The reason is shown as inline text — trailing
    punctuation makes the UI look broken."""
    data = _load_manifest()
    perms = data.get("permissions", {})
    bad: list[str] = []
    for key, reason in perms.items():
        if not isinstance(reason, str):
            continue
        if reason.rstrip().endswith((".", "!", "?", "…")):
            bad.append(f"{key}: {reason!r}")
    assert not bad, (
        "permission reason(s) end with punctuation (rejected by review):\n  "
        + "\n  ".join(bad))


def test_manifest_permission_reasons_one_line():
    """Reasons are inline UI text — no newlines, no leading/trailing
    whitespace. Flag any that wrap."""
    data = _load_manifest()
    bad: list[str] = []
    for key, reason in (data.get("permissions") or {}).items():
        if not isinstance(reason, str):
            continue
        if "\n" in reason or reason != reason.strip():
            bad.append(f"{key}: {reason!r}")
    assert not bad, (
        "permission reason(s) have newlines or padding:\n  "
        + "\n  ".join(bad))


def test_manifest_excludes_pycache():
    """Without `__pycache__/` in `paths_exclude_pattern`, the published
    zip ships compiled bytecode for whoever built it last — different
    Python version, different paths in tracebacks, larger zip."""
    data = _load_manifest()
    excludes = (data.get("build") or {}).get("paths_exclude_pattern", [])
    assert any("__pycache__" in p for p in excludes), (
        "build.paths_exclude_pattern must drop __pycache__/")
