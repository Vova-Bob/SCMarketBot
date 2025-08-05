from random import randint

import discord
from discord import app_commands
from discord.ext import commands

from util.i18n import t, get_locale


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def info(self, interaction: discord.Interaction):
        """Some simple details about the bot."""
        locale = get_locale(interaction.user.id, interaction)
        me = self.bot.user if not interaction.guild else interaction.guild.me
        appinfo = await self.bot.application_info()
        embed = discord.Embed(
            color=randint(0, 0xFFFFFF),
            title=t("admin.info.title", locale),
        )
        embed.set_author(
            name=me.display_name,
            icon_url=appinfo.owner.display_avatar.url,
            url="https://sc-market.space",
        )
        embed.add_field(
            name=t("admin.info.author", locale),
            value="henry232323",
        )
        embed.add_field(
            name=t("admin.info.servers", locale),
            value=t("admin.info.servers_value", locale).format(count=len(self.bot.guilds)),
        )
        embed.set_footer(
            text=t("admin.info.footer", locale),
            icon_url="http://i.imgur.com/5BFecvA.png",
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
