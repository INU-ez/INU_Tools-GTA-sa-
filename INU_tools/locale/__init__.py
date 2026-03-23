# INU_tools localization package
# Each language file exports a LANG dict: {"Русский ключ": "Translation"}
# Default language (Russian) is built into the addon code.
# To add a new language: create <lang_code>.py with LANG = { ... }

import os
import importlib

_LANGUAGES = {}

def _load_languages():
    """Auto-discover and load all language modules in this package."""
    pkg_dir = os.path.dirname(__file__)
    for fname in os.listdir(pkg_dir):
        if fname.endswith('.py') and fname != '__init__.py':
            lang_code = fname[:-3]  # e.g. "eng" from "eng.py"
            try:
                mod = importlib.import_module(f'.{lang_code}', package=__package__)
                if hasattr(mod, 'LANG'):
                    _LANGUAGES[lang_code] = mod.LANG
            except Exception:
                pass

_load_languages()


def get_translation(lang_code):
    """Get translation dict for a language code, or None."""
    return _LANGUAGES.get(lang_code)


def available_languages():
    """Return list of available language codes."""
    return list(_LANGUAGES.keys())
