import os

import aiohttp
import discord
import traceback
from discord import app_commands
from discord.app_commands import checks
from discord.ext import commands

DISCORD_BACKEND_URL = os.environ.get("DISCORD_BACKEND_URL", "http://web:8081")


class Registration(commands.Cog):
    @app_commands.command(name="register")
    @checks.has_permissions(administrator=True)
    @app_commands.describe(
        type='Whether to register the server as official or the current channel as the one used for order threads')
    @app_commands.choices(type=[
        app_commands.Choice(name="Channel", value="channel"),
        app_commands.Choice(name="Server", value="server"),
    ])
    @app_commands.describe(
        entity='Whether to register the channel or server for an org/contractor or for an individual user')
    @app_commands.choices(entity=[
        app_commands.Choice(name="Contractor", value="contractor"),
        app_commands.Choice(name="User", value="user"),
    ])
    @app_commands.describe(entity='If registering a contractor, the name of the contractor')
    async def register(
            self, interaction: discord.Interaction,
            type: app_commands.Choice[str],
            entity: app_commands.Choice[str],
            name: str = ""
    ):
        """Register a server as the official server for order fulfillment for your contractor or user, or register a channel as the channel that will house threads for order fulfillment."""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f'{DISCORD_BACKEND_URL}/register/{entity.value}/{name}',
                    json=dict(
                        discord_id=str(interaction.user.id),
                        channel_id=str(interaction.channel.id) if type.value == "channel" else None,
                        server_id=str(interaction.guild.id) if type.value == "server" else None,
                    )
            ) as resp:
                try:
                    result = await resp.json()
                except Exception as e:
                    traceback.print_exc()
                    return await interaction.response.send_message("An unexpected error occured", ephemeral=True)

        if resp.ok:
            await interaction.response.send_message("Registered channel", ephemeral=True)
        else:
            await interaction.response.send_message(f"Failed to register channel: {result.get('error')}",
                                                    ephemeral=True)
