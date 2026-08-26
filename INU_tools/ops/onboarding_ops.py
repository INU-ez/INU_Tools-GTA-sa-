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


def _active_doc_lang():
    """Return 'ru' when Blender shows the Russian UI, else 'en' (the English
    docs also serve Spanish / other locales).

    ``get_locale()`` returns a FULL code like 'ru_RU', so we must match by
    PREFIX — the old exact ``== 'ru'`` check silently fell through to English
    for every real Russian user (their locale is 'ru_RU', never bare 'ru')."""
    return 'ru' if (get_locale() or '').startswith('ru') else 'en'


def _doc_url_for_active_locale():
    """Pick Russian or English documentation based on Blender's UI
    language. The addon's other strings flip via get_locale() too —
    keeping the docs link consistent matches user expectations."""
    return _DOC_URL_RU if _active_doc_lang() == 'ru' else _DOC_URL_EN


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


# Stable panel-section key → GitHub heading anchor, per doc language.
# A single hardcoded anchor can't serve both docs: the headings differ
# between languages (## Материалы → #материалы  vs  ## Materials → #materials),
# so each panel passes a KEY and we resolve the right anchor for the active
# UI language. GitHub keeps Cyrillic letters in anchors (lowercased), strips
# punctuation, and turns spaces into hyphens (a removed «/» leaves a double
# hyphen: «IDE / IPL / IMG» → «ide--ipl--img»).
_DOC_SECTIONS = {
    'ide_ipl':         {'ru': 'ide--ipl--img',        'en': 'ide--ipl--img'},
    'export':          {'ru': 'экспорт--импорт',       'en': 'export--import'},
    'check':           {'ru': 'проверка',              'en': 'check'},
    'texture_browser': {'ru': 'texture-browser',       'en': 'texture-browser'},
    '2dfx':            {'ru': '2dfx-эффекты',           'en': '2dfx-effects'},
    'id_manager':      {'ru': 'менеджер-id',            'en': 'model-id-manager'},
    'lighting':        {'ru': 'прелайт-vertex-colors',  'en': 'prelight-vertex-colors'},
    'water':           {'ru': 'вода',                   'en': 'water-io'},
    # Панель «Анимации» = две вкладки; «?» ведёт в раздел по активной вкладке.
    'anim_character':  {'ru': 'персонажи-skinned-dff',  'en': 'characters-skinned-dff'},
    'anim_object':     {'ru': 'анимация-объектов-animated-map-objects', 'en': 'animated-map-objects'},
    'paths':           {'ru': 'пути',                   'en': 'path-io'},
    'zon':             {'ru': 'зоны-карты-mapzon',       'en': 'map-zones-mapzon'},
    'baking':          {'ru': 'запекание-текстур-210',  'en': 'texture-baking-210'},
    'materials':       {'ru': 'материалы',              'en': 'materials'},
    'vehicles':        {'ru': 'машины',                 'en': 'vehicles'},
    'grass':           {'ru': 'трава',                  'en': 'grass'},
    'radar':           {'ru': 'x-radar-maker',          'en': 'x-radar-maker'},
    'bitmaps':         {'ru': 'менеджер-текстур-bitmaps-manager', 'en': 'bitmaps-manager'},
}


def _resolve_doc_anchor(section):
    """Map a section KEY to the doc anchor for the active UI language.
    An unknown key is treated as a literal anchor (back-compat)."""
    if not section:
        return ""
    entry = _DOC_SECTIONS.get(section)
    if entry is None:
        return section
    return entry.get(_active_doc_lang(), "")


# ── Operators ───────────────────────────────────────────────────────


class GTATOOLS_OT_open_docs(bpy.types.Operator):
    """Открыть документацию аддона на GitHub. Язык подбирается
    под текущую локаль Blender."""
    bl_idname = "gtatools.open_docs"
    bl_label = "INU: Open Docs"
    bl_options = {'REGISTER'}

    # Section KEY (see _DOC_SECTIONS) — so «?» on a panel opens ITS doc
    # section (resolved to the right anchor for the active UI language),
    # not the top of the docs. Empty = open the docs at the top.
    section: bpy.props.StringProperty(default="", options={'HIDDEN'})

    def execute(self, context):
        url = _doc_url_for_active_locale()
        anchor = _resolve_doc_anchor(self.section)
        if anchor:
            url += "#" + anchor
        bpy.ops.wm.url_open(url=url)
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


