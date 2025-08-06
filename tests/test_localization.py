import types
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from util.i18n import get_locale, t, LOCALE_DIR

class Dummy:
    def __init__(self, locale=None):
        self.locale = locale

class Ctx:
    def __init__(self, interaction=None, author=None, locale=None):
        self.interaction = interaction
        self.author = author
        self.locale = locale


def flatten(d, prefix=""):
    keys = set()
    for k, v in d.items():
        if isinstance(v, dict):
            keys |= flatten(v, f"{prefix}{k}.")
        else:
            keys.add(f"{prefix}{k}")
    return keys


def test_get_locale_preference_interaction():
    ctx = Ctx(interaction=Dummy("uk"))
    assert get_locale(ctx) == "uk"


def test_get_locale_fallback_author():
    ctx = Ctx(interaction=Dummy(None), author=Dummy("uk"))
    assert get_locale(ctx) == "uk"


def test_get_locale_default():
    ctx = Ctx()
    assert get_locale(ctx) == "en"


def test_translation():
    assert t("info.author", "uk") == "Автор"


def test_locale_files_have_same_keys():
    en = json.load(open(LOCALE_DIR / "en.json", "r", encoding="utf-8"))
    uk = json.load(open(LOCALE_DIR / "uk.json", "r", encoding="utf-8"))
    assert flatten(en) == flatten(uk)
