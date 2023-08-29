import asyncio
import os

import aiohttp
import discord
from aiohttp import web
from discord import ChannelType
from discord.ext.commands import Bot

from cogs.registration import Registration, DISCORD_BACKEND_URL
from util.api_server import create_api

intents = discord.Intents.default()
intents.members = True


class SCMarket(Bot):
    async def setup_hook(self):
        await self.add_cog(Registration(self))
        await self.tree.sync()

        runner = web.AppRunner(api)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        asyncio.create_task(site.start())

        print("Ready!")

    async def on_command_error(self, interaction, error):
        pass

    async def on_member_join(self, member):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'{DISCORD_BACKEND_URL}/register/user',
                    json=dict(
                        discord_id=str(member.id),
                        server_id=str(member.guild.id),
                    )
            ) as resp:
                if not resp.ok:
                    return

                try:
                    result = await resp.json()
                except Exception as e:
                    return

                guild: discord.Guild = member.guild
                for thread_id in result['thread_ids']:
                    try:
                        thread = await guild.fetch_channel(int(thread_id))
                        if thread:
                            await thread.add_user(member)
                    except:
                        pass

    async def create_thread(self, server_id: int, channel_id: int, members: list[int], order: dict):
        if not server_id or not channel_id or not members:
            return

        guild: discord.Guild = await self.fetch_guild(server_id)
        if not guild:
            return

        channel: discord.TextChannel = await guild.fetch_channel(channel_id)
        if not channel:
            return

        thread = await channel.create_thread(
            name=f"order-{order['order_id'][:8]}",
            type=ChannelType.private_thread
        )

        await thread.add_user(self.user)

        failed = []
        for member in members:
            if not member:
                continue

            try:
                await thread.add_user(discord.Object(int(member)))
            except Exception as e:
                failed.append(member)

        invite = None
        if failed:
            invite = await channel.create_invite(max_uses=len(failed))
            for member in failed:
                user = await self.fetch_user(int(member))
                try:
                    await user.send(
                        f"You placed an order:\n\n```{order['description']}```\n\nPlease join this server to work with the seller to complete your order: {invite}"
                    )
                except:
                    pass

        return dict(thread_id=str(thread.id), failed=failed, invite_code=str(invite) if invite else None)


bot = SCMarket(intents=intents, command_prefix="/")
api = create_api(bot)

bot.run(os.environ.get("DISCORD_API_KEY"))
