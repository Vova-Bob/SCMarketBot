import datetime

import aiohttp
import discord
import humanize
from discord import app_commands
from discord.ext import commands
from discord.ext.paginators.button_paginator import ButtonPaginator, PaginatorButton

class Stock(commands.Cog):
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

        embeds = [create_embed(item) for item in result['listings']]

        paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
        await paginator.send(interaction)
