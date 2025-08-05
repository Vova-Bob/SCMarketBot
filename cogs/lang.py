import discord
from discord import app_commands
from discord.ext import commands


class Language(commands.GroupCog, name="language"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set")
    @app_commands.describe(locale="Locale code to use, e.g. 'en'")
    async def set_language(self, interaction: discord.Interaction, locale: str):
        """Set your preferred language"""
        self.bot.i18n.set_user_lang(interaction.user.id, locale)
        await interaction.response.send_message(
            self.bot.i18n.t(locale, "language_set", locale=locale),
            ephemeral=True,
        )

    @app_commands.command(name="show")
    async def show_language(self, interaction: discord.Interaction):
        """Show your current language"""
        locale = self.bot.i18n.user_lang.get(str(interaction.user.id), self.bot.i18n.default)
        await interaction.response.send_message(
            self.bot.i18n.t(locale, "language_current", locale=locale),
            ephemeral=True,
        )
