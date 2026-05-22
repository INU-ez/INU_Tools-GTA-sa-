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
# don't ship 4000+ lines of release notes to the modal.
_WHATS_NEW_RU = [
    ("v1.7.0 — IK Rig, Animated Map Object, Profile System", 'PRESET'),
    ("",  None),
    ("• IK Rig для педов — Add IK Rig + Floor", 'ARMATURE_DATA'),
    ("• Animated Map Object (мельницы, краны)", 'CON_FOLLOWPATH'),
    ("• Frame Hierarchy Editor + Validate Vehicle/Ped", 'OUTLINER'),
    ("• Paintjob (Pay'n'Spray) на материалах", 'BRUSH_DATA'),
    ("• Adaptive grid auto-split (quadtree)", 'GRID'),
    ("• Profile system: наборы N-панелей", 'PRESET'),
    ("• Drag-drop DFF/COL во viewport", 'IMPORT'),
    ("• Smart auto-TXD picker", 'TEXTURE'),
]
_WHATS_NEW_EN = [
    ("v1.7.0 — IK Rig, Animated Map Object, Profile System", 'PRESET'),
    ("",  None),
    ("• IK Rig for peds — Add IK Rig + Floor", 'ARMATURE_DATA'),
    ("• Animated Map Object (windmills, cranes)", 'CON_FOLLOWPATH'),
    ("• Frame Hierarchy Editor + Validate Vehicle/Ped", 'OUTLINER'),
    ("• Paintjob (Pay'n'Spray) on materials", 'BRUSH_DATA'),
    ("• Adaptive grid auto-split (quadtree)", 'GRID'),
    ("• Profile system: N-sidebar panel sets", 'PRESET'),
    ("• Drag-drop DFF/COL into viewport", 'IMPORT'),
    ("• Smart auto-TXD picker", 'TEXTURE'),
]


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
        body = _WHATS_NEW_RU if get_locale() == 'ru' else _WHATS_NEW_EN
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


classes = (
    GTATOOLS_OT_open_docs,
    GTATOOLS_OT_open_issues,
    GTATOOLS_OT_open_release,
    GTATOOLS_OT_whats_new,
)
