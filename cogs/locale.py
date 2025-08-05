import discord
from discord import app_commands
from discord.ext import commands

from util.i18n import set_locale


class Locale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="language")
    @app_commands.describe(code="Locale code, e.g. 'en' or 'uk'")
    async def language(self, interaction: discord.Interaction, code: str):
        """Set the preferred language for this user."""
        set_locale(interaction.user.id, code)
        await interaction.response.send_message(f"Language set to {code}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Locale(bot))
