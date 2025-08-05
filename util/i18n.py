"""Simple internationalization utilities."""

import json
from pathlib import Path
from typing import Dict

# This dictionary will hold all loaded translations.
TRANSLATIONS: Dict[str, Dict[str, str]] = {}


def load_translations() -> None:
    """Load all JSON translation files from the locales directory."""
    global TRANSLATIONS
    locales_path = Path(__file__).resolve().parent.parent / "locales"
    for file in locales_path.glob("*.json"):
        with file.open("r", encoding="utf-8") as f:
            TRANSLATIONS[file.stem] = json.load(f)


def t(key: str, locale: str = "en") -> str:
    """Return the translated string for ``key`` in ``locale``.

    Falls back to English if the key is missing in the requested locale and
    returns the key itself if it is missing in English as well.
    """
    return (
        TRANSLATIONS.get(locale, {}).get(
            key, TRANSLATIONS.get("en", {}).get(key, key)
        )
    )
