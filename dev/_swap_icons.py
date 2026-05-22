"""One-shot transform: rewrite every `icon=<expr>` kwarg call in the
addon so it routes through `inu_icon(...)`, falling back to native
icons when no Lucide PNG exists.

We don't try to parse Python — we walk the source character by
character, find `icon=` only where it sits as a fresh kwarg (not as
attribute access), then scan the RHS as a balanced expression that
terminates at a top-level `,` or `)`. The captured expression is
re-emitted as `**inu_icon(<expr>)`. `inu_icon` itself accepts any
input that yields an icon-name string, so wrapping `safe_icon(...)`,
constants like `compat.ICON_CHECK`, dict lookups, and `if/else`
expressions all keep working without unwrapping.

Run from repo root:
    python dev/_swap_icons.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "INU_tools"

FILES = [
    "ui/panels.py",
    "ui/library_panel.py",
    "tools/bitmaps_manager.py",
    "tools/vc_layers.py",
    "tools/map_export.py",
    "tools/gta_material_panel.py",
    "tools/profiles.py",
    "tools/uv_tools.py",
    "ops/effects_ops.py",
    "ops/col_surface_ops.py",
    "ops/img_ops.py",
    "ops/dff_import.py",
    "ops/onboarding_ops.py",
    "ops/inu_export.py",
    "ops/animobj_ops.py",
    "__init__.py",
]


def _is_kwarg_position(text: str, start: int) -> bool:
    """Return True only when `icon=` at `start` sits as a function-call
    kwarg (preceded by `,` or `(` after skipping whitespace+newlines)
    AND its line does not declare a `def` (parameter default position)."""
    i = start - 1
    while i >= 0 and text[i] in " \t\n\r\\":
        i -= 1
    if i < 0:
        return False
    if text[i] not in (",", "("):
        return False
    line_start = text.rfind("\n", 0, start) + 1
    line_to_pos = text[line_start:start]
    if re.search(r"\bdef\s+\w+\s*\(", line_to_pos):
        return False
    return True


def transform(text: str) -> tuple[str, int]:
    out = []
    i = 0
    n = len(text)
    count = 0
    while i < n:
        m = re.search(r"(?<![\w.])icon=", text[i:])
        if not m:
            out.append(text[i:])
            break
        start = i + m.start()
        eq_end = i + m.end()
        if not _is_kwarg_position(text, start):
            out.append(text[i:eq_end])
            i = eq_end
            continue
        out.append(text[i:start])
        # parse balanced expression after `=` until top-level , or )
        j = eq_end
        dp = db = dc = 0
        in_str = None
        while j < n:
            ch = text[j]
            if in_str:
                if ch == "\\" and j + 1 < n:
                    j += 2
                    continue
                if text.startswith(in_str, j):
                    j += len(in_str)
                    in_str = None
                    continue
                j += 1
                continue
            if text[j:j + 3] in ('"""', "'''"):
                in_str = text[j:j + 3]
                j += 3
                continue
            if ch in ('"', "'"):
                in_str = ch
                j += 1
                continue
            if ch == "(":
                dp += 1
            elif ch == ")":
                if dp == 0 and db == 0 and dc == 0:
                    break
                dp -= 1
            elif ch == "[":
                db += 1
            elif ch == "]":
                db -= 1
            elif ch == "{":
                dc += 1
            elif ch == "}":
                dc -= 1
            elif ch == "," and dp == 0 and db == 0 and dc == 0:
                break
            j += 1
        expr = text[eq_end:j]
        out.append("**inu_icon(" + expr + ")")
        i = j
        count += 1
    return "".join(out), count


def patch_import(text: str) -> str:
    """Make sure `inu_icon` is imported alongside `safe_icon` in the
    one file-level import line that already brings in `safe_icon`."""
    pat = re.compile(
        r"^(from\s+\.+tools\.compat\s+import\s+safe_icon)\s*$",
        re.MULTILINE,
    )
    if pat.search(text):
        return pat.sub(r"\1, inu_icon", text)
    pat2 = re.compile(
        r"^(from\s+\.compat\s+import\s+safe_icon)\s*$",
        re.MULTILINE,
    )
    if pat2.search(text):
        return pat2.sub(r"\1, inu_icon", text)
    return text


total_swaps = 0
for rel in FILES:
    p = ROOT / rel
    src = p.read_text(encoding="utf-8")
    new, c = transform(src)
    new = patch_import(new)
    if new != src:
        p.write_text(new, encoding="utf-8")
        print(f"{rel}: {c} icon= swaps")
        total_swaps += c
    else:
        print(f"{rel}: nothing changed")

print(f"\nTotal: {total_swaps} icon= -> **inu_icon(...) swaps")
