import json
import os
import traceback

import aiohttp
import discord
from discord import app_commands
from discord.app_commands import checks
from discord.ext import commands
from util.i18n import tr, cmd, option

DISCORD_BACKEND_URL = os.environ.get("DISCORD_BACKEND_URL", "http://web:8081")


class Registration(commands.GroupCog):
    channel = app_commands.Group(**cmd('register.channel'))
    server = app_commands.Group(**cmd('register.server'))

    def __init__(self, bot):
        super().__init__(**cmd('register'))
        self.bot = bot

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(str(error))

    @channel.command(**cmd('register.channel.contractor'))
    @checks.has_permissions(administrator=True)
    async def contractor_channel(
            self, interaction: discord.Interaction,
            name: str = option('register.channel.contractor', 'name')
    ):
        """Register a channel as the channel that will house threads for order fulfillment for your contractor. Make sure the bot has permission to see the channel and make private threads there."""
        await self.register(interaction, "channel", "contractor", name)

    @channel.command(**cmd('register.channel.user'))
    @checks.has_permissions(administrator=True)
    async def user_channel(
            self, interaction: discord.Interaction,
    ):
        """Register a channel as the channel that will house threads for order fulfillment for your user. Make sure the bot has permission to see the channel and make private threads there."""
        await self.register(interaction, "channel", "user")

    @server.command(**cmd('register.server.contractor'))
    @checks.has_permissions(administrator=True)
    async def contractor_server(
            self, interaction: discord.Interaction,
            name: str = option('register.server.contractor', 'name')
    ):
        """Register a server as the official server for order fulfillment for your contractor."""
        await self.register(interaction, "server", "contractor", name)

    @server.command(**cmd('register.server.user'))
    @checks.has_permissions(administrator=True)
    async def user_server(
            self, interaction: discord.Interaction,
    ):
        """Register a server as the official server for order fulfillment for your user."""
        await self.register(interaction, "server", "user")

    @staticmethod
    async def register(interaction, type, entity, name=""):
        async with aiohttp.ClientSession() as session:
            payload = dict(
                discord_id=str(interaction.user.id),
                channel_id=str(interaction.channel.id) if type == "channel" else None,
                server_id=str(interaction.guild.id) if type == "server" else None,
            )
            print(payload)
            async with session.post(
                    f'{DISCORD_BACKEND_URL}/register/{entity}/{name}',
                    json=payload
            ) as resp:
                try:
                    text = await resp.text()
                    result = json.loads(text)  # await resp.json()
                except Exception as e:
                    traceback.print_exc()
                    print(text)
                    return await interaction.response.send_message(tr(interaction, 'registration.unexpected'), ephemeral=True)

        if resp.ok:
            await interaction.response.send_message(tr(interaction, 'registration.success', type=type, entity=entity), ephemeral=True)
        else:
            await interaction.response.send_message(tr(interaction, 'registration.fail', error=result.get('error')), ephemeral=True)
