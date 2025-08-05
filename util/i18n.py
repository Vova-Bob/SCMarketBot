import json
import os
from typing import Any, Dict


class I18n:
    def __init__(self, default: str = "en", locales_dir: str = "locales"):
        self.default = default
        self.locales_dir = locales_dir
        self.translations: Dict[str, Dict[str, str]] = {}
        self.user_lang: Dict[str, str] = {}
        self._load_locales()
        self._load_user_lang()

    @property
    def available_languages(self) -> list[str]:
        """Return a list of loaded language codes."""
        return list(self.translations.keys())

    def _load_locales(self) -> None:
        if not os.path.isdir(self.locales_dir):
            return
        for filename in os.listdir(self.locales_dir):
            if not filename.endswith('.json') or filename == 'users.json':
                continue
            path = os.path.join(self.locales_dir, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.translations[os.path.splitext(filename)[0]] = json.load(f)
            except Exception:
                self.translations[os.path.splitext(filename)[0]] = {}

    def _load_user_lang(self) -> None:
        users_path = os.path.join(self.locales_dir, 'users.json')
        if os.path.exists(users_path):
            try:
                with open(users_path, 'r', encoding='utf-8') as f:
                    self.user_lang = json.load(f)
            except Exception:
                self.user_lang = {}
        else:
            self.user_lang = {}

    def _save_user_lang(self) -> None:
        os.makedirs(self.locales_dir, exist_ok=True)
        users_path = os.path.join(self.locales_dir, 'users.json')
        with open(users_path, 'w', encoding='utf-8') as f:
            json.dump(self.user_lang, f, ensure_ascii=False, indent=2)

    def set_user_lang(self, user_id: int | str, lang: str) -> None:
        self.user_lang[str(user_id)] = lang
        self._save_user_lang()

    def set_user(self, user_id: int | str, lang: str) -> None:
        """Alias for backwards compatibility."""
        self.set_user_lang(user_id, lang)

    def get_lang(self, interaction: Any) -> str:
        user_id = getattr(getattr(interaction, 'user', None), 'id', None)
        if user_id is not None:
            lang = self.user_lang.get(str(user_id))
            if lang:
                return lang
        locale = getattr(interaction, 'locale', None)
        if locale:
            return str(locale)
        guild_locale = getattr(interaction, 'guild_locale', None)
        if guild_locale:
            return str(guild_locale)
        return self.default

    def t(self, lang: str, key: str, **kwargs: Any) -> str:
        data = self.translations.get(lang) or self.translations.get(self.default, {})
        text = data.get(key) or self.translations.get(self.default, {}).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        return text
