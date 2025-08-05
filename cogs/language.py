import discord
from discord import app_commands
from discord.ext import commands

from util.i18n import I18n

# Build choices from available languages
_language_choices = [
    app_commands.Choice(name=lang, value=lang)
    for lang in I18n().available_languages
]


class Language(commands.GroupCog, name="language"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set")
    @app_commands.describe(lang="Language to use")
    @app_commands.choices(lang=_language_choices)
    async def set_language(
        self, interaction: discord.Interaction, lang: app_commands.Choice[str]
    ):
        """Set your preferred language"""
        self.bot.i18n.set_user(interaction.user.id, lang.value)
        await interaction.response.send_message(
            self.bot.i18n.t(lang.value, "language_set", locale=lang.value),
            ephemeral=True,
        )
