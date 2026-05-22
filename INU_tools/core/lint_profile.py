# INU_tools.core.lint_profile
# Lint profile = preset of threshold overrides + post-scan filters
# shared between file_lint and map_lint. One profile is active at a
# time; UI exposes it as a single EnumProperty (gtatools_lint_profile)
# on the scene.
#
# Two mechanisms cooperate:
#   1) **Threshold overrides** — scanner reads cfg.dff_*/txd_*/draw* and
#      uses them instead of module defaults when not None. Lets STRICT
#      tighten the WARN thresholds without duplicating issue codes.
#   2) **Post-scan filter** — apply_filter() drops issues by code or
#      severity. Lets FLA mode silence FLA-required warnings, LENIENT
#      mode drop INFO-level diagnostics, both without scanner changes.

from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Dict, List

# ── Profile names (used as EnumProperty IDs and string keys) ───────

STANDARD = 'STANDARD'   # default, calibrated against vanilla SA
FLA = 'FLA'             # assume Fastman92 Limit Adjuster installed
STRICT = 'STRICT'       # tighter thresholds for QA passes
LENIENT = 'LENIENT'     # drop INFO-level for legacy projects

ALL_PROFILES = (STANDARD, FLA, STRICT, LENIENT)


@dataclass(frozen=True)
class ProfileConfig:
    """Resolved settings for a single lint profile.

    Threshold fields override the corresponding constant inside
    file_lint / map_lint when not None. Filter fields apply post-scan:
    silenced_codes drops issues by code, silenced_severities by level.
    """
    # ── Threshold overrides (None = use module default) ───────────
    # file_lint scope:
    dff_vert_soft: Optional[int] = None         # default 32000
    dff_tri_soft: Optional[int] = None          # default 30000
    dff_mat_vanilla: Optional[int] = None       # default 100
    dff_2dfx_soft: Optional[int] = None         # default 200
    txd_size_vanilla: Optional[int] = None      # default 1024
    # map_lint scope:
    drawdist_high: Optional[float] = None       # default 2000.0

    # ── Post-scan filters ─────────────────────────────────────────
    silenced_codes: FrozenSet[str] = frozenset()
    silenced_severities: FrozenSet[str] = frozenset()


# Codes silenced when the user has Fastman92 installed — they're WARNs
# that say "this value needs FLA". With FLA confirmed present, those
# are no longer warnings, just facts.
_FLA_SILENCED_CODES = frozenset({
    'IDE_ID_NEEDS_FLA',
    'IPL_INTERIOR_NON_STANDARD',
    'COL_SURFACE_ID_FLA_ONLY',
})


def get_profile(name: str) -> ProfileConfig:
    """Return the ProfileConfig for the given profile name. Unknown
    names fall back to STANDARD (no overrides, no filters)."""
    if name == FLA:
        return ProfileConfig(silenced_codes=_FLA_SILENCED_CODES)
    if name == STRICT:
        # Tighter thresholds. Values chosen so WARN fires for ~30% of
        # vanilla SA models that pass STANDARD silently — meant for
        # modders who care about asset quality, not vanilla baseline.
        return ProfileConfig(
            dff_vert_soft=16000,
            dff_tri_soft=16000,
            dff_mat_vanilla=50,
            dff_2dfx_soft=100,
            txd_size_vanilla=512,
            drawdist_high=800.0,
        )
    if name == LENIENT:
        # Drop everything informational. Useful when scanning a
        # legacy mod where you already know about the cruft.
        return ProfileConfig(silenced_severities=frozenset({'INFO'}))
    return ProfileConfig()


def apply_filter(issues: List, profile_name: str) -> List:
    """Drop issues silenced by the profile. Returns a new list — the
    original is not modified. Scanners call this once at the end."""
    cfg = get_profile(profile_name)
    if not cfg.silenced_codes and not cfg.silenced_severities:
        return list(issues)
    return [
        it for it in issues
        if it.code not in cfg.silenced_codes
        and it.severity not in cfg.silenced_severities
    ]
