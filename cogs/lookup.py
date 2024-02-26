import datetime

import aiohttp
import discord
import humanize
from discord import app_commands
from discord.ext import commands
from discord.ext.paginators.button_paginator import ButtonPaginator

categories = ["Armor", "Clothing", "Weapon", "Paint", "Bundle", "Flair", "Addon", "Consumable", "Other"]
sorting_methods = {
    'title': "Title",
    'price-low': "Price (Low to High)",
    'price-high': "Price (High to Low)",
    'quantity-low': "Quantity Available (Low to High)",
    'quantity-high': "Quantity Available (High to Low)",
    'date-new': "Date Listed (Old to New)",
    'date-old': "Date Listed (New to Old)",
    'activity': "Recent Activity",
    'rating': "Rating (High to Low)",
}

sale_types = ["Aggregate", "Auction", "Sale"]


def create_embed(listing: dict):
    embed = discord.Embed(url=f"https://sc-market.space/market/{listing['listing_id']}", title=listing['title'])
    embed.add_field(name="Item Type", value=listing['item_type'].capitalize())
    if listing["listing_type"] != "unique":
        embed.add_field(name="Minimum Price", value=f"{int(listing['minimum_price']):,} aUEC")
        embed.add_field(name="Maximum Price", value=f"{int(listing['maximum_price']):,} aUEC")
    else:
        embed.add_field(name="Price", value=f"{int(listing['price']):,} aUEC")
        embed.add_field(
            name="Seller",
            value=f"[{listing['contractor_seller'] or listing['user_seller']}]({'https://sc-market.space/contractor/' + listing['contractor_seller'] if listing['contractor_seller'] else 'https://sc-market.space/user/' + listing['user_seller']}) {'⭐' * int(round(listing['avg_rating']))}"
        )

    if listing['auction_end_time'] is not None:
        date = datetime.datetime.strptime(listing['auction_end_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        embed.add_field(name="Auction End", value="Ending " + humanize.naturaltime(date))

    embed.add_field(name="Quantity Available", value=f"{int(listing['quantity_available']):,}")

    embed.set_image(url=listing['photo'])
    embed.timestamp = datetime.datetime.strptime(listing['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

    return embed


class Lookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    @app_commands.command(name="search")
    @app_commands.describe(
        query='The search query',
        category='What category the item belongs to',
        sorting='What order to sort the listings by',
        sale_type='The method of sale',
        quantity_available='The minimum quantity available an item must have',
        min_cost='The minimum cost of items to search',
        max_cost='The maximum cost of items to search',
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name=item, value=item.lower()) for item in categories
        ],
        sorting=[
            app_commands.Choice(name=value, value=key) for key, value in sorting_methods.items()
        ],
        sale_type=[
            app_commands.Choice(name=item, value=item.lower()) for item in sale_types
        ],
    )
    async def search(
            self,
            interaction: discord.Interaction,
            query: str,
            category: app_commands.Choice[str] = '',
            sorting: app_commands.Choice[str] = 'activity',
            sale_type: app_commands.Choice[str] = '',
            quantity_available: int = 1,
            min_cost: int = 0,
            max_cost: int = 0,
    ):
        """Search the site market listings"""
        params = {
            'query': query,
            'sort': sorting,
            'quantityAvailable': quantity_available,
            'minCost': min_cost,
            'page_size': 48,
            'index': 0
        }

        if category:
            params['item_type'] = category
        if sale_type:
            params['sale_type'] = sale_type
        if max_cost:
            params['maxCost'] = max_cost

        async with self.session.get(
                "https://api.sc-market.space/api/market/public/search",
                params=params
        ) as resp:
            result = await resp.json()
            print(result)

        embeds = [create_embed(item) for item in result['listings']]

        paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
        await paginator.send(interaction)
