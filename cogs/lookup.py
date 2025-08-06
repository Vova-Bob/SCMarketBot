from typing import List

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.paginators.button_paginator import ButtonPaginator

from util.fetch import public_fetch, search_users, search_orgs
from util.listings import create_market_embed, categories, sorting_methods, sale_types, create_market_embed_individual, \
    display_listings_compact
from util.i18n import get_locale, tr, cmd, option


class Lookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(**cmd('search'))
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
            query: str = option('search', 'query'),
            category: app_commands.Choice[str] = option('search', 'category', ''),
            sorting: app_commands.Choice[str] = option('search', 'sorting', 'activity'),
            sale_type: app_commands.Choice[str] = option('search', 'sale_type', ''),
            quantity_available: int = option('search', 'quantity_available', 1),
            min_cost: int = option('search', 'min_cost', 0),
            max_cost: int = option('search', 'max_cost', 0),
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

        locale = get_locale(interaction)
        embeds = [create_market_embed(item, locale) for item in result['listings'] if item['listing']['quantity_available']]
        if not embeds:
            await interaction.response.send_message(tr(interaction, 'search.no_results'))

        paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
        await paginator.send(interaction)

    lookup = app_commands.Group(**cmd('lookup'))

    @lookup.command(**cmd('lookup.user'))
    async def user_search(
            self,
            interaction: discord.Interaction,
            handle: str = option('lookup.user', 'handle'),
            compact: bool = option('lookup.user', 'compact', False),
    ):
        """Lookup the market listings for a user"""
        try:
            listings = await public_fetch(
                f"/market/user/{handle}",
                session=self.bot.session,
            )
        except:
            await interaction.response.send_message(tr(interaction, 'lookup.invalid_user'))
            return

        if compact:
            await display_listings_compact(interaction, [{**l['details'], **l['listing']} for l in listings])
        else:
            locale = get_locale(interaction)
            embeds = [create_market_embed_individual(item, locale) for item in listings if
                      item['listing']['quantity_available']]

            if not embeds:
                await interaction.response.send_message(tr(interaction, 'lookup.no_listings'))
                return

            paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
            await paginator.send(interaction)

    @lookup.command(**cmd('lookup.org'))
    async def org_search(
            self,
            interaction: discord.Interaction,
            spectrum_id: str = option('lookup.org', 'spectrum_id'),
            compact: bool = option('lookup.org', 'compact', False),
    ):
        """Lookup the market listings for an org"""
        try:
            listings = await public_fetch(
                f"/market/contractor/{spectrum_id}",
                session=self.bot.session,
            )
        except:
            await interaction.response.send_message(tr(interaction, 'lookup.invalid_org'))
            return

        if compact:
            await display_listings_compact(interaction, [{**l['details'], **l['listing']} for l in listings])
        else:
            locale = get_locale(interaction)
            embeds = [create_market_embed_individual(item, locale) for item in listings if
                      item['listing']['quantity_available']]

            if not embeds:
                await interaction.response.send_message(tr(interaction, 'lookup.no_org_listings'))
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
