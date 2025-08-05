import discord
from discord import app_commands
from discord.ext import commands

from util.i18n import TRANSLATIONS, set_locale, t


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
                locale = str(interaction.locale).split("-")[0] if interaction.locale else "en"
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
        await interaction.response.send_message("Select a language:", view=view, ephemeral=True)

    @app_commands.command(name="setlanguage")
    @app_commands.describe(code="Locale code, e.g. 'en' or 'uk'")
    async def setlanguage(self, interaction: discord.Interaction, code: str | None = None):
        """Set the preferred language for this user."""
        await self._set_language(interaction, code)

    @app_commands.command(name="language")
    @app_commands.describe(code="Locale code, e.g. 'en' or 'uk'")
    async def language(self, interaction: discord.Interaction, code: str | None = None):
        """Alias for setlanguage."""
        await self._set_language(interaction, code)


async def setup(bot):
    await bot.add_cog(Locale(bot))
