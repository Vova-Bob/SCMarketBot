import json
from pathlib import Path
from functools import lru_cache

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
    if locale != 'en':
        return t(key, 'en', **kwargs)
    return key


def tr(ctx, key: str, **kwargs) -> str:
    """Translate *key* using the locale derived from *ctx*."""
    return t(key, get_locale(ctx), **kwargs)


def cmd(key: str) -> dict:
    """Return English name/description for a command or group."""
    name = t(f'commands.{key}.name', 'en')
    desc = t(f'commands.{key}.description', 'en')
    if name == f'commands.{key}.name':
        name = key.split('.')[-1]
    if desc == f'commands.{key}.description':
        desc = ''
    return dict(name=name, description=desc)


def option(command_key: str, option_name: str) -> str:
    """Return the English description for an option.

    This pulls the description from the locale JSON files so descriptions
    remain centralized alongside other translations. Only the English strings
    are used for command registration in accordance with discord.py 2.5.2.
    """

    desc = t(f'commands.{command_key}.options.{option_name}.description', 'en')
    if desc == f'commands.{command_key}.options.{option_name}.description':
        desc = ''
    return desc

