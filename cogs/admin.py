from random import randint

import discord
from discord import app_commands
from discord.ext import commands

from util.i18n import tr, cmd


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(**cmd('info'))
    async def info(self, interaction: discord.Interaction):
        me = self.bot.user if not interaction.guild else interaction.guild.me
        appinfo = await self.bot.application_info()
        embed = discord.Embed(color=randint(0, 0xFFFFFF))
        embed.set_author(name=me.display_name, icon_url=appinfo.owner.display_avatar.url,
                         url="https://sc-market.space")
        embed.add_field(name=tr(interaction, 'info.author'), value='henry232323')
        embed.add_field(name=tr(interaction, 'info.servers'), value=tr(interaction, 'info.server_count', count=len(self.bot.guilds)))
        embed.set_footer(text=tr(interaction, 'info.footer'), icon_url='http://i.imgur.com/5BFecvA.png')
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
