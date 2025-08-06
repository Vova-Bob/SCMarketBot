import json
from pathlib import Path
from functools import lru_cache

from discord import app_commands

LOCALE_DIR = Path(__file__).resolve().parent.parent / 'locale'

def get_locale(ctx) -> str:
    """Return the locale for the given interaction/ctx."""
    locale = None
    if getattr(ctx, 'interaction', None) and getattr(ctx.interaction, 'locale', None):
        locale = str(ctx.interaction.locale)
    elif getattr(ctx, 'author', None) and getattr(ctx.author, 'locale', None):
        locale = str(ctx.author.locale)
    elif getattr(ctx, 'locale', None):
        locale = str(ctx.locale)
    if locale:
        locale = locale.split('-')[0]
    if not locale or not (LOCALE_DIR / f"{locale}.json").exists():
        return 'en'
    return locale

@lru_cache(maxsize=None)
def _load(locale: str) -> dict:
    path = LOCALE_DIR / f"{locale}.json"
    if not path.exists() and locale != 'en':
        return _load('en')
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

def t(key: str, locale: str, **kwargs) -> str:
    data = _load(locale)
    for part in key.split('.'):
        data = data.get(part, {})
    if isinstance(data, str):
        try:
            return data.format(**kwargs)
        except Exception:
            return data
    # fallback
    if locale != 'en':
        return t(key, 'en', **kwargs)
    return key


def _lookup(locale: str, key: str):
    """Return raw translation value for the given locale and key."""
    data = _load(locale)
    for part in key.split('.'):
        if isinstance(data, dict):
            data = data.get(part)
        else:
            return None
    return data if isinstance(data, str) else None


def get_localizations(key: str) -> dict:
    """Return mapping of locale->translation for the given key.

    Falls back to English if a specific locale does not provide the key.
    """
    localizations = {}
    for path in LOCALE_DIR.glob('*.json'):
        locale = path.stem
        value = _lookup(locale, key)
        if value:
            localizations[locale] = value
    if 'en' not in localizations:
        value = _lookup('en', key)
        if value:
            localizations['en'] = value
    return localizations


def cmd(key: str) -> dict:
    """Return parameters for a localized command/group."""
    name_loc = get_localizations(f'commands.{key}.name')
    desc_loc = get_localizations(f'commands.{key}.description')
    return dict(
        name=name_loc.get('en', key.split('.')[-1]),
        description=desc_loc.get('en', ''),
        name_localizations=name_loc,
        description_localizations=desc_loc,
    )


def option(command_key: str, option_name: str, default=None):
    """Return app_commands.Param configured with localizations."""
    name_loc = get_localizations(f'commands.{command_key}.options.{option_name}.name')
    desc_loc = get_localizations(f'commands.{command_key}.options.{option_name}.description')
    return app_commands.Param(
        default,
        name=name_loc.get('en', option_name),
        description=desc_loc.get('en', ''),
        name_localizations=name_loc,
        description_localizations=desc_loc,
    )
