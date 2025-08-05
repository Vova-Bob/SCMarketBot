import json
import os
import traceback

import aiohttp
import discord
from discord import app_commands
from discord.app_commands import checks
from discord.ext import commands

from util.i18n import t, get_locale

DISCORD_BACKEND_URL = os.environ.get("DISCORD_BACKEND_URL", "http://web:8081")


class Registration(
    commands.GroupCog,
    name=t("commands.register.group.name"),
    description=t("commands.register.group.description"),
):
    def __init__(self, bot):
        self.bot = bot
        self.__cog_app_commands_group__.name_localizations = {
            "uk": t("commands.register.group.name", "uk")
        }
        self.__cog_app_commands_group__.description_localizations = {
            "uk": t("commands.register.group.description", "uk")
        }
    channel = app_commands.Group(
        name=t("commands.register.channel.group.name"),
        description=t("commands.register.channel.group.description"),
    )
    channel.name_localizations = {
        "uk": t("commands.register.channel.group.name", "uk")
    }
    channel.description_localizations = {
        "uk": t("commands.register.channel.group.description", "uk")
    }
    server = app_commands.Group(
        name=t("commands.register.server.group.name"),
        description=t("commands.register.server.group.description"),
    )
    server.name_localizations = {
        "uk": t("commands.register.server.group.name", "uk")
    }
    server.description_localizations = {
        "uk": t("commands.register.server.group.description", "uk")
    }

    async def cog_app_command_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message(str(error))

    @channel.command(
        name=t("commands.register.channel.contractor.name"),
        description=t("commands.register.channel.contractor.description"),
    )
    @checks.has_permissions(administrator=True)
    @app_commands.describe(
        name=app_commands.locale_str(
            "The name of the contractor",
            uk="Ім'я підрядника",
        )
    )
    async def contractor_channel(
            self, interaction: discord.Interaction,
            name: str
    ):
        """Register a channel as the channel that will house threads for order fulfillment for your contractor. Make sure the bot has permission to see the channel and make private threads there."""
        await self.register(interaction, "channel", "contractor", name)

    contractor_channel.name_localizations = {
        "uk": t("commands.register.channel.contractor.name", "uk")
    }
    contractor_channel.description_localizations = {
        "uk": t("commands.register.channel.contractor.description", "uk")
    }

    @channel.command(
        name=t("commands.register.channel.user.name"),
        description=t("commands.register.channel.user.description"),
    )
    @checks.has_permissions(administrator=True)
    async def user_channel(
            self, interaction: discord.Interaction,
    ):
        """Register a channel as the channel that will house threads for order fulfillment for your user. Make sure the bot has permission to see the channel and make private threads there."""
        await self.register(interaction, "channel", "user")

    user_channel.name_localizations = {
        "uk": t("commands.register.channel.user.name", "uk")
    }
    user_channel.description_localizations = {
        "uk": t("commands.register.channel.user.description", "uk")
    }

    @server.command(
        name=t("commands.register.server.contractor.name"),
        description=t("commands.register.server.contractor.description"),
    )
    @checks.has_permissions(administrator=True)
    @app_commands.describe(
        name=app_commands.locale_str(
            "The name of the contractor",
            uk="Ім'я підрядника",
        )
    )
    async def contractor_server(
            self, interaction: discord.Interaction,
            name: str
    ):
        """Register a server as the official server for order fulfillment for your contractor."""
        await self.register(interaction, "server", "contractor", name)

    contractor_server.name_localizations = {
        "uk": t("commands.register.server.contractor.name", "uk")
    }
    contractor_server.description_localizations = {
        "uk": t("commands.register.server.contractor.description", "uk")
    }

    @server.command(
        name=t("commands.register.server.user.name"),
        description=t("commands.register.server.user.description"),
    )
    @checks.has_permissions(administrator=True)
    async def user_server(
            self, interaction: discord.Interaction,
    ):
        """Register a server as the official server for order fulfillment for your user."""
        await self.register(interaction, "server", "user")

    user_server.name_localizations = {
        "uk": t("commands.register.server.user.name", "uk")
    }
    user_server.description_localizations = {
        "uk": t("commands.register.server.user.description", "uk")
    }

    @staticmethod
    async def register(interaction, type, entity, name=""):
        locale = get_locale(interaction.user.id, interaction)
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
                    return await interaction.response.send_message(
                        t("registration.error.unexpected", locale),
                        ephemeral=True,
                    )

        if resp.ok:
            await interaction.response.send_message(
                t("registration.success", locale).format(
                    type=t(f"registration.type.{type}", locale),
                    entity=t(f"registration.entity.{entity}", locale),
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                t("registration.fail", locale).format(
                    type=t(f"registration.type.{type}", locale),
                    error=result.get('error'),
                ),
                ephemeral=True,
            )
