import json
from pathlib import Path
from functools import lru_cache

LOCALE_DIR = Path(__file__).resolve().parent.parent / 'locale'

def get_locale(ctx) -> str:
    """Return the locale for the given interaction/ctx."""
    locale = None
    if getattr(ctx, 'interaction', None) and getattr(ctx.interaction, 'locale', None):
        locale = ctx.interaction.locale
    elif getattr(ctx, 'author', None) and getattr(ctx.author, 'locale', None):
        locale = ctx.author.locale
    elif getattr(ctx, 'locale', None):
        locale = ctx.locale
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
