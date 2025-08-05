"""Simple internationalization utilities."""

import json
from pathlib import Path
from typing import Dict

# This dictionary will hold all loaded translations.
TRANSLATIONS: Dict[str, Dict[str, str]] = {}

# Path and dictionary for user locale preferences.
PREFERENCES_PATH = Path(__file__).resolve().parent.parent / "locale_prefs.json"
LOCALES: Dict[str, str] = {}


def load_translations() -> None:
    """Load all JSON translation files from the locales directory."""
    global TRANSLATIONS
    locales_path = Path(__file__).resolve().parent.parent / "locales"
    for file in locales_path.glob("*.json"):
        with file.open("r", encoding="utf-8") as f:
            TRANSLATIONS[file.stem] = json.load(f)


def load_preferences() -> None:
    """Load saved user locale preferences from disk."""
    global LOCALES
    if PREFERENCES_PATH.exists():
        with PREFERENCES_PATH.open("r", encoding="utf-8") as f:
            LOCALES = json.load(f)


def save_preferences() -> None:
    """Persist user locale preferences to disk."""
    with PREFERENCES_PATH.open("w", encoding="utf-8") as f:
        json.dump(LOCALES, f)


def set_locale(user_id: int, code: str) -> None:
    """Set the locale preference for ``user_id``."""
    LOCALES[str(user_id)] = code
    save_preferences()


def get_locale(user_id: int, interaction) -> str:
    """Return the preferred locale for ``user_id``.

    Checks saved preferences first, then falls back to the locale
    provided by the interaction or defaults to English.
    """
    if str(user_id) in LOCALES:
        return LOCALES[str(user_id)]
    if interaction and getattr(interaction, "locale", None):
        return str(interaction.locale).split("-")[0]
    return "en"


# Load preferences on import so ``get_locale`` can be used immediately.
load_preferences()


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
