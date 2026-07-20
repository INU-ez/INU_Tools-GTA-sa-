# INU_tools.ops.onboarding_ops
# Onboarding helpers — three header buttons in the main panel that
# point new users at docs, the issue tracker, and a What's-New popup
# for the current version. None of this is functional addon work —
# it's pure discoverability so a fresh install doesn't strand the
# user wondering where the manual lives.

import bpy

from .. import T, get_locale
from ..tools.compat import safe_icon, inu_icon
# Docs and issues live on GitHub; the addon installer only ships the
# INU_tools/ module to Blender's addons folder, NOT the docs/ folder
# from the repo, so we can't rely on a local file path. Web URLs are
# the only reliably-available targets.
_REPO = "https://github.com/INU-ez/INU_Tools-GTA-sa-"
_DOC_URL_RU = f"{_REPO}/blob/main/docs/DOCS_rus.md"
_DOC_URL_EN = f"{_REPO}/blob/main/docs/DOCS.md"
_ISSUES_URL = f"{_REPO}/issues"
# /releases/latest auto-resolves to the newest published release —
# evergreen across version bumps, no need to edit this constant when
# we ship v1.8.
_RELEASE_URL = f"{_REPO}/releases/latest"


def _doc_url_for_active_locale():
    """Pick Russian or English documentation based on Blender's UI
    language. The addon's other strings flip via get_locale() too —
    keeping the docs link consistent matches user expectations."""
    return _DOC_URL_RU if get_locale() == 'ru' else _DOC_URL_EN


# What's-new popup body. Two locales — kept hardcoded rather than
# parsing the bl_info changelog so the layout stays curated and we
# don't ship 4000+ lines of release notes to the modal. The version number
# in the header is filled in at draw time from bl_info so it never goes
# stale on a bump (it used to be hardcoded «v1.7.0»).
_WHATS_NEW_HEADER_RU = "Анимации IFP, Альфа-материалы, IK Rig"
_WHATS_NEW_HEADER_EN = "IFP animations, Alpha materials, IK Rig"

_WHATS_NEW_RU = [
    ("• Анимации IFP: импорт/экспорт + зеркало L/R", 'ACTION'),
    ("• IK Rig для педов — Add IK Rig + Floor", 'ARMATURE_DATA'),
    ("• Animated Map Object (мельницы, краны)", 'CON_FOLLOWPATH'),
    ("• Массовая замена альфа-режимов материалов", 'MATERIAL'),
    ("• Frame Hierarchy Editor + Validate Vehicle/Ped", 'OUTLINER'),
    ("• Paintjob (Pay'n'Spray) на материалах", 'BRUSH_DATA'),
    ("• Profile: наборы N-панелей", 'PRESET'),
    ("• Drag-drop DFF/COL + Smart auto-TXD", 'IMPORT'),
]
_WHATS_NEW_EN = [
    ("• IFP animations: import/export + L/R mirror", 'ACTION'),
    ("• IK Rig for peds — Add IK Rig + Floor", 'ARMATURE_DATA'),
    ("• Animated Map Object (windmills, cranes)", 'CON_FOLLOWPATH'),
    ("• Bulk alpha blend-mode replace on materials", 'MATERIAL'),
    ("• Frame Hierarchy Editor + Validate Vehicle/Ped", 'OUTLINER'),
    ("• Paintjob (Pay'n'Spray) on materials", 'BRUSH_DATA'),
    ("• Profile: N-sidebar panel sets", 'PRESET'),
    ("• Drag-drop DFF/COL + Smart auto-TXD", 'IMPORT'),
]


def _addon_version_str():
    """Current addon version as 'vX.Y.Z', read from bl_info so the what's-new
    header tracks the real version instead of a stale hardcoded one."""
    try:
        from .. import bl_info
        v = bl_info.get("version")
        if v:
            return "v" + ".".join(str(n) for n in v)
    except Exception:
        pass
    return ""


# ── Operators ───────────────────────────────────────────────────────


class GTATOOLS_OT_open_docs(bpy.types.Operator):
    """Открыть документацию аддона на GitHub. Язык подбирается
    под текущую локаль Blender."""
    bl_idname = "gtatools.open_docs"
    bl_label = "INU: Open Docs"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.url_open(url=_doc_url_for_active_locale())
        return {'FINISHED'}


class GTATOOLS_OT_open_issues(bpy.types.Operator):
    """Открыть issues аддона на GitHub — для багрепортов и пожеланий."""
    bl_idname = "gtatools.open_issues"
    bl_label = "INU: Open Issues"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.url_open(url=_ISSUES_URL)
        return {'FINISHED'}


class GTATOOLS_OT_open_release(bpy.types.Operator):
    """Открыть страницу последнего релиза на GitHub — там полный
    changelog текущей версии, рендерится из RELEASE_NOTES."""
    bl_idname = "gtatools.open_release"
    bl_label = "INU: Open Release Notes"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.url_open(url=_RELEASE_URL)
        return {'FINISHED'}


class GTATOOLS_OT_whats_new(bpy.types.Operator):
    """Показать краткий обзор новых фич текущей версии."""
    bl_idname = "gtatools.whats_new"
    bl_label = "INU: What's New"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=360)

    def draw(self, context):
        layout = self.layout
        is_ru = get_locale() == 'ru'
        header = _WHATS_NEW_HEADER_RU if is_ru else _WHATS_NEW_HEADER_EN
        body = _WHATS_NEW_RU if is_ru else _WHATS_NEW_EN

        # Version header, filled from bl_info at draw time (never stale).
        ver = _addon_version_str()
        title = f"{ver} — {header}" if ver else header
        layout.row().label(text=title, **inu_icon(safe_icon('PRESET')))
        layout.row().label(text="")   # divider

        for text, icon in body:
            row = layout.row()
            if not text:
                # Blank divider line.
                row.label(text="")
            elif icon:
                row.label(text=text, **inu_icon(icon))
            else:
                row.label(text=text)

        layout.separator()
        layout.operator("gtatools.open_release",
                        text=T("Открыть полный changelog на GitHub"),
                        **inu_icon(safe_icon('URL')))

    def execute(self, context):
        return {'FINISHED'}


