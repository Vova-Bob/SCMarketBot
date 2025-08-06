import logging
import os
import traceback

from dotenv import load_dotenv

load_dotenv()

import aiohttp
import discord
from aiohttp import web
from discord import ChannelType
from discord.ext.commands import Bot

from cogs.admin import Admin
from cogs.lookup import Lookup
from cogs.order import order
from cogs.registration import Registration, DISCORD_BACKEND_URL
from cogs.stock import stock
from util.api_server import create_api
from util.result import Result
from util.i18n import t, tr

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

logger = logging.getLogger('SCMarketBot')
logger.setLevel(logging.DEBUG)


class SCMarket(Bot):
    session = None

    async def setup_hook(self):
        await self.add_cog(Registration(self))
        await self.add_cog(Admin(self))
        await self.add_cog(Lookup(self))
        await self.add_cog(order(self))
        await self.add_cog(stock(self))

        await self.tree.sync()

        runner = web.AppRunner(api)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        self.loop.create_task(site.start())

        self.session = aiohttp.ClientSession()
        logger.info("Ready!")

    async def on_command_error(self, interaction, error):
        print(error)

    def on_error(self, *args, **kwargs):
        print(*args, kwargs)

    async def on_message(self, message):
        if isinstance(message.channel, discord.Thread):
            if not message.author.bot and message.content:
                async with self.session.post(
                        f'{DISCORD_BACKEND_URL}/threads/message',
                        json=dict(
                            author_id=str(message.author.id),
                            name=message.author.name,
                            thread_id=str(message.channel.id),
                            content=message.content,
                        )
                ) as resp:
                    await resp.read()

    async def order_placed(self, body):
        try:
            result = await self.create_thread(
                body.get('server_id'),
                body.get('channel_id'),
                body.get('members'),
                body.get('order'),
            )

            thread = result.value

            if body.get('server_id') and body.get('channel_id'):
                invite = await self.verify_invite(
                    body.get('customer_discord_id'),
                    body.get('server_id'),
                    body.get('channel_id'),
                    body.get("discord_invite")
                )
            else:
                invite = None

            if not thread:
                thread = dict(thread_id=None,
                              invite_code=str(invite) if invite else None)

                print("Received error:", result.error)
            return dict(thread=thread, failed=bool(result.error), message=result.error, invite_code=invite)
        except:
            traceback.print_exc()
            return dict(
                thread=None,
                failed=True,
                message=t('errors.unknown', 'en'),
                invite_code=None,
            )

    async def verify_invite(self, customer_id, server_id, channel_id, invite_code):
        guild: discord.Guild = await self.fetch_guild(int(server_id))
        if not guild:
            return None

        channel: discord.TextChannel = guild.get_channel(int(channel_id))
        if not channel:
            return None

        try:
            is_member = customer_id and await guild.fetch_member(int(customer_id))
            if is_member:
                return None
        except:
            pass

        try:
            if invite_code:
                invite = await self.fetch_invite(invite_code)
            else:
                invite = None

            if invite:
                return invite_code
            else:
                new_invite = await channel.create_invite(reason="Invite customer to the guild", unique=False)
                return new_invite.code
        except:
            traceback.print_exc()
            return None

    async def on_member_join(self, member):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f'{DISCORD_BACKEND_URL}/threads/user/{member.id}',
                ) as resp:
                    if not resp.ok:
                        logger.error("Failed to fetch threads: %s", resp.reason)
                        return

                    try:
                        result = await resp.json()
                    except Exception as e:
                        logger.error("Failed to decode response: %s", e)
                        return

                    logger.info("Threads payload: %s", result)

                    guild: discord.Guild = member.guild
                    for thread_id in result['thread_ids']:
                        try:
                            thread = guild.get_thread(int(thread_id))
                            if thread:
                                await thread.add_user(member)
                        except Exception as e:
                            logger.error("Failed to add to thread: %s", e)
                            pass
        except Exception as e:
            traceback.print_exc()

    async def order_status_update(self, order: dict):
        try:
            seller_id = order.get('seller_discord_id')
            if not seller_id:
                return False
            user = await self.fetch_user(int(seller_id))
            now = discord.utils.utcnow()
            buyer_name = order.get('buyer_name', '')
            embed = discord.Embed(
                title=tr(user, 'order.embed.items_sold_to', buyer=buyer_name),
                description=tr(user, 'order.embed.complete_delivery', buyer=buyer_name),
            )
            embed.add_field(
                name=tr(user, 'order.embed.discord_user_details'),
                value=order.get('buyer_tag', ''),
                inline=False,
            )
            for item in order.get('items', []):
                embed.add_field(
                    name=tr(user, 'order.embed.item_field', item=item.get('name')),
                    value=tr(user, 'order.embed.item_quantity', quantity=str(item.get('quantity', ''))),
                    inline=False,
                )
            if order.get('total') is not None:
                embed.add_field(name=tr(user, 'order.embed.total'), value=str(order.get('total')), inline=True)
            if order.get('user_offer') is not None:
                embed.add_field(name=tr(user, 'order.embed.user_offer'), value=str(order.get('user_offer')), inline=True)
            if order.get('note_from_buyer'):
                embed.add_field(name=tr(user, 'order.embed.note_from_buyer'), value=order.get('note_from_buyer'), inline=False)
            if order.get('offer') is not None:
                embed.add_field(name=tr(user, 'order.embed.offer'), value=str(order.get('offer')), inline=True)
            if order.get('kind'):
                embed.add_field(name=tr(user, 'order.embed.kind'), value=str(order.get('kind')), inline=True)
            if order.get('collateral'):
                embed.add_field(name=tr(user, 'order.embed.collateral'), value=str(order.get('collateral')), inline=True)
            embed.timestamp = now
            embed.set_footer(text=tr(user, 'order.embed.today', time=now.strftime('%H:%M')))
            await user.send(embed=embed)
            return True
        except Exception:
            traceback.print_exc()
            return False

    async def create_thread(self, server_id: int, channel_id: int, members: list[int], offer: dict):
        if not server_id or not channel_id or not members:
            return Result(error=t('errors.server_channel_members', 'en'))

        guild: discord.Guild = await self.fetch_guild(int(server_id))
        if not guild:
            return Result(error=t('errors.bot_not_in_guild', 'en'))

        try:
            channel = guild.get_channel(int(channel_id))
            if not channel:
                try:
                    channel: discord.TextChannel = await guild.fetch_channel(int(channel_id))
                except discord.NotFound:
                    pass
            if not channel:
                return Result(error=t('errors.thread_channel_missing', 'en'))
        except discord.Forbidden:
            return Result(error=t('errors.no_view_perm', 'en'))
        except discord.InvalidData:
            return Result(error=t('errors.invalid_thread_data', 'en'))

        is_order = offer.get("order_id")

        try:
            thread = await channel.create_thread(
                name=f"{'order' if is_order else 'offer'}-{offer.get('id', offer.get('order_id'))[:8]}",
                type=ChannelType.private_thread
            )
        except:
            return Result(error=t('errors.no_create_thread_perm', 'en'))

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
            try:
                invite = await channel.create_invite(max_uses=len(failed))
                for member in failed:
                    user = await self.fetch_user(int(member))
                    try:
                        await user.send(
                            tr(
                                user,
                                'dm.offer_invite',
                                invite=invite,
                            )
                        )
                    except Exception as e:
                        print(e, offer)
            except Exception as e:
                print(e)

        return Result(value=dict(thread_id=str(thread.id), failed=failed, invite_code=str(invite) if invite else None))


bot = SCMarket(intents=intents, command_prefix="/")
api = create_api(bot)

bot.run(os.environ.get("DISCORD_API_KEY"))
