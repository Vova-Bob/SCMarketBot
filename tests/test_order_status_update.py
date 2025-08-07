import asyncio
import discord
from main import SCMarket
from util.i18n import t


class DummyUser:
    def __init__(self):
        self.embed = None

    async def send(self, embed=None):
        self.embed = embed


def test_order_status_update_uses_seller_locale(monkeypatch):
    async def run():
        bot = SCMarket(intents=discord.Intents.none(), command_prefix='/')
        dummy_user = DummyUser()

        async def fetch_user(user_id):
            return dummy_user

        monkeypatch.setattr(bot, 'fetch_user', fetch_user)

        order = {
            'seller_discord_id': '1',
            'seller_locale': 'uk',
            'buyer_name': 'Bob',
            'buyer_tag': 'Bob#1234',
            'items': [{'name': 'Item', 'quantity': 1}],
        }
        result = await bot.order_status_update(order)
        assert result is True
        assert dummy_user.embed.title == t('order.embed.items_sold_to', 'uk', buyer='Bob')
        assert dummy_user.embed.fields[0].name == t('order.embed.discord_user_details', 'uk')
        await bot.close()

    asyncio.run(run())
