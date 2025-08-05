import discord
from discord import app_commands
from discord.ext import commands

from util.i18n import TRANSLATIONS, set_locale, t, get_locale


class LocaleView(discord.ui.View):
    """View offering buttons for available translations."""

    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        for code in TRANSLATIONS:
            self.add_item(LocaleButton(code))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This view isn't for you", ephemeral=True)
            return False
        return True


class LocaleButton(discord.ui.Button):
    def __init__(self, code: str):
        super().__init__(label=code.upper(), style=discord.ButtonStyle.primary)
        self.code = code

    async def callback(self, interaction: discord.Interaction):
        set_locale(interaction.user.id, self.code)
        await interaction.response.edit_message(
            content=t("locale.set.success", self.code).format(locale=self.code),
            view=None,
        )


class Locale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _set_language(self, interaction: discord.Interaction, code: str | None):
        if code:
            code = code.lower()
            if code not in TRANSLATIONS:
                locale = get_locale(interaction.user.id, interaction)
                await interaction.response.send_message(
                    t("locale.set.invalid", locale).format(locale=code),
                    ephemeral=True,
                )
                return
            set_locale(interaction.user.id, code)
            await interaction.response.send_message(
                t("locale.set.success", code).format(locale=code),
                ephemeral=True,
            )
            return

        view = LocaleView(interaction.user.id)
        locale = get_locale(interaction.user.id, interaction)
        await interaction.response.send_message(
            t("locale.select_language", locale), view=view, ephemeral=True
        )

    @app_commands.command(
        name=t("commands.locale.setlanguage.name"),
        description=t("commands.locale.setlanguage.description"),
    )
    @app_commands.describe(
        code=app_commands.locale_str(
            "Locale code, e.g. 'en' or 'uk'",
            uk="Код мови, напр. 'en' або 'uk'",
        )
    )
    async def setlanguage(self, interaction: discord.Interaction, code: str | None = None):
        """Set the preferred language for this user."""
        await self._set_language(interaction, code)

    setlanguage.name_localizations = {
        "uk": t("commands.locale.setlanguage.name", "uk")
    }
    setlanguage.description_localizations = {
        "uk": t("commands.locale.setlanguage.description", "uk")
    }

    @app_commands.command(
        name=t("commands.locale.language.name"),
        description=t("commands.locale.language.description"),
    )
    @app_commands.describe(
        code=app_commands.locale_str(
            "Locale code, e.g. 'en' or 'uk'",
            uk="Код мови, напр. 'en' або 'uk'",
        )
    )
    async def language(self, interaction: discord.Interaction, code: str | None = None):
        """Alias for setlanguage."""
        await self._set_language(interaction, code)

    language.name_localizations = {
        "uk": t("commands.locale.language.name", "uk")
    }
    language.description_localizations = {
        "uk": t("commands.locale.language.description", "uk")
    }


async def setup(bot):
    await bot.add_cog(Locale(bot))
