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


def option(command_key: str, option_name: str, default=None):
    """Return app_commands.Param using English strings from locale files."""
    name = t(f'commands.{command_key}.options.{option_name}.name', 'en')
    desc = t(f'commands.{command_key}.options.{option_name}.description', 'en')
    if name == f'commands.{command_key}.options.{option_name}.name':
        name = option_name
    if desc == f'commands.{command_key}.options.{option_name}.description':
        desc = ''
    return app_commands.Param(default, name=name, description=desc)

