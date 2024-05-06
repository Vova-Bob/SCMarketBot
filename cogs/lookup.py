from typing import List

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.paginators.button_paginator import ButtonPaginator

from util.fetch import public_fetch, search_users, search_orgs
from util.listings import create_market_embed, categories, sorting_methods, sale_types, create_market_embed_individual, \
    display_listings_compact


class Lookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        result = await public_fetch(
            "/market/public/search",
            params=params,
            session=self.bot.session,
        )

        embeds = [create_market_embed(item) for item in result['listings'] if item['listing']['quantity_available']]

        paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
        await paginator.send(interaction)

    lookup = app_commands.Group(name="lookup", description="Look up an org or user's market listings")

    @lookup.command(name="user")
    @app_commands.describe(
        handle='The handle of the user',
    )
    async def user_search(
            self,
            interaction: discord.Interaction,
            handle: str,
            compact: bool = False,
    ):
        """Lookup the market listings for a user"""
        try:
            listings = await public_fetch(
                f"/market/user/{handle}",
                session=self.bot.session,
            )
        except:
            await interaction.response.send_message("Invalid user")
            return

        if compact:
            await display_listings_compact(interaction, [{**l['details'], **l['listing']} for l in listings])
        else:
            embeds = [create_market_embed_individual(item) for item in listings if
                      item['listing']['quantity_available']]

            if not embeds:
                await interaction.response.send_message("No listings to display for org")
                return

            paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
            await paginator.send(interaction)

    @lookup.command(name="org")
    @app_commands.describe(
        spectrum_id='The spectrum ID of the org',
    )
    async def org_search(
            self,
            interaction: discord.Interaction,
            spectrum_id: str,
            compact: bool = False,
    ):
        """Lookup the market listings for an org"""
        try:
            listings = await public_fetch(
                f"/market/contractor/{spectrum_id}",
                session=self.bot.session,
            )
        except:
            await interaction.response.send_message("Invalid org")
            return

        if compact:
            await display_listings_compact(interaction, [{**l['details'], **l['listing']} for l in listings])
        else:
            embeds = [create_market_embed_individual(item) for item in listings if
                      item['listing']['quantity_available']]

            if not embeds:
                await interaction.response.send_message("No listings to display for org")
                return

            paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
            await paginator.send(interaction)

    @user_search.autocomplete('handle')
    async def autocomplete_get_users(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        users = await search_users(current, self.bot.session)
        choices = [
                      app_commands.Choice(
                          name=f"{user['display_name'][:100]} ({user['username']})",
                          value=user['username']
                      )
                      for user in users
                  ][:25]
        return choices

    @org_search.autocomplete('spectrum_id')
    async def autocomplete_get_orgs(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        orgs = await search_orgs(current, self.bot.session)

        choices = [
                      app_commands.Choice(
                          name=f"{org['name'][:30]} ({org['spectrum_id']})",
                          value=org['spectrum_id']
                      )
                      for org in orgs
                  ][:25]
        return choices
