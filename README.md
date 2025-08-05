# SCMarketBot
This is the repository that hosts the official Discord bot for [SC Market](https://sc-market.space).

## Local Development
This project requires Python 3.12. You can install requirements with
```shell
python -m pip install -r requirements.txt
```

The bot can be launched from the Docker configuration in [the backend](https://github.com/SC-Market/sc-market-backend).

## Adding a New Language

- Create a new `locales/<lang>.json` file.
- Populate it with the same translation keys as the other locale files; keeping keys consistent across languages prevents missing strings.
- Reload or restart the bot so it loads the new locale file.

Example:

```python
from util.i18n import t

locale = "en"  # e.g., "en", "uk"
message = t("admin.info.title", locale)
```

