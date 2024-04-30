import json
import os
import traceback

import aiohttp
import discord
from discord import app_commands
from discord.app_commands import checks
from discord.ext import commands

DISCORD_BACKEND_URL = os.environ.get("DISCORD_BACKEND_URL", "http://web:8081")


class Registration(commands.GroupCog, name="register"):
    channel = app_commands.Group(name="channel",
                                 description="Register a channel as the channel that will house threads for order fulfillment")
    server = app_commands.Group(name="server",
                                description="Register a server as the official server for order fulfillment")

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(str(error))

    @channel.command(name="contractor")
    @checks.has_permissions(administrator=True)
    @app_commands.describe(name='The name of the contractor')
    async def contractor_channel(
            self, interaction: discord.Interaction,
            name: str
    ):
        """Register a channel as the channel that will house threads for order fulfillment for your contractor. Make sure the bot has permission to see the channel and make private threads there."""
        await self.register(interaction, "channel", "contractor", name)

    @channel.command(name="user")
    @checks.has_permissions(administrator=True)
    async def user_channel(
            self, interaction: discord.Interaction,
    ):
        """Register a channel as the channel that will house threads for order fulfillment for your user. Make sure the bot has permission to see the channel and make private threads there."""
        await self.register(interaction, "channel", "user")

    @server.command(name="contractor")
    @checks.has_permissions(administrator=True)
    @app_commands.describe(name='The name of the contractor')
    async def contractor_server(
            self, interaction: discord.Interaction,
            name: str
    ):
        """Register a server as the official server for order fulfillment for your contractor."""
        await self.register(interaction, "server", "contractor", name)

    @server.command(name="user")
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
                    return await interaction.response.send_message("An unexpected error occurred", ephemeral=True)

        if resp.ok:
            await interaction.response.send_message(f"Registered {type} for {entity}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Failed to register channel: {result.get('error')}",
                                                    ephemeral=True)
