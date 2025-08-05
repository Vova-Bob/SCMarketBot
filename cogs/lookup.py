from typing import List

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.paginators.button_paginator import ButtonPaginator

from util.fetch import public_fetch, search_users, search_orgs
from util.i18n import t, get_locale
from util.listings import (
    create_market_embed,
    categories,
    sorting_methods,
    sale_types,
    create_market_embed_individual,
    display_listings_compact,
)


class Lookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name=t("commands.lookup.search.name"),
        description=t("commands.lookup.search.description"),
    )
    @app_commands.describe(
        query=app_commands.locale_str("The search query", uk="Пошуковий запит"),
        category=app_commands.locale_str(
            "What category the item belongs to",
            uk="Категорія, до якої належить предмет",
        ),
        sorting=app_commands.locale_str(
            "What order to sort the listings by",
            uk="Порядок сортування оголошень",
        ),
        sale_type=app_commands.locale_str(
            "The method of sale",
            uk="Метод продажу",
        ),
        quantity_available=app_commands.locale_str(
            "The minimum quantity available an item must have",
            uk="Мінімальна доступна кількість предмета",
        ),
        min_cost=app_commands.locale_str(
            "The minimum cost of items to search",
            uk="Мінімальна ціна для пошуку",
        ),
        max_cost=app_commands.locale_str(
            "The maximum cost of items to search",
            uk="Максимальна ціна для пошуку",
        ),
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name=t(name_key), value=value)
            for value, name_key in categories.items()
        ],
        sorting=[
            app_commands.Choice(name=t(name_key), value=key)
            for key, name_key in sorting_methods.items()
        ],
        sale_type=[
            app_commands.Choice(name=t(name_key), value=value)
            for value, name_key in sale_types.items()
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
        locale = get_locale(interaction.user.id, interaction)
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

        embeds = [
            create_market_embed(item, locale)
            for item in result['listings']
            if item['listing']['quantity_available']
        ]
        if not embeds:
            await interaction.response.send_message(t("lookup.no_results", locale))

        paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
        await paginator.send(interaction)

    search.name_localizations = {"uk": t("commands.lookup.search.name", "uk")}
    search.description_localizations = {"uk": t("commands.lookup.search.description", "uk")}

    lookup = app_commands.Group(
        name=t("commands.lookup.group.name"),
        description=t("commands.lookup.group.description"),
    )
    lookup.name_localizations = {"uk": t("commands.lookup.group.name", "uk")}
    lookup.description_localizations = {"uk": t("commands.lookup.group.description", "uk")}

    @lookup.command(
        name=t("commands.lookup.user.name"),
        description=t("commands.lookup.user.description"),
    )
    @app_commands.describe(
        handle=app_commands.locale_str("The handle of the user", uk="Ім'я користувача"),
    )
    async def user_search(
            self,
            interaction: discord.Interaction,
            handle: str,
            compact: bool = False,
    ):
        """Lookup the market listings for a user"""
        locale = get_locale(interaction.user.id, interaction)
        try:
            listings = await public_fetch(
                f"/market/user/{handle}",
                session=self.bot.session,
            )
        except:
            await interaction.response.send_message(t("lookup.invalid_user", locale))
            return

        if compact:
            await display_listings_compact(interaction, [{**l['details'], **l['listing']} for l in listings])
        else:
            embeds = [
                create_market_embed_individual(item, locale)
                for item in listings
                if item['listing']['quantity_available']
            ]

            if not embeds:
                await interaction.response.send_message(t("lookup.no_listings_org", locale))
                return

            paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
            await paginator.send(interaction)

    user_search.name_localizations = {"uk": t("commands.lookup.user.name", "uk")}
    user_search.description_localizations = {"uk": t("commands.lookup.user.description", "uk")}

    @lookup.command(
        name=t("commands.lookup.org.name"),
        description=t("commands.lookup.org.description"),
    )
    @app_commands.describe(
        spectrum_id=app_commands.locale_str(
            "The spectrum ID of the org",
            uk="Spectrum ID організації",
        ),
    )
    async def org_search(
            self,
            interaction: discord.Interaction,
            spectrum_id: str,
            compact: bool = False,
    ):
        """Lookup the market listings for an org"""
        locale = get_locale(interaction.user.id, interaction)
        try:
            listings = await public_fetch(
                f"/market/contractor/{spectrum_id}",
                session=self.bot.session,
            )
        except:
            await interaction.response.send_message(t("lookup.invalid_org", locale))
            return

        if compact:
            await display_listings_compact(interaction, [{**l['details'], **l['listing']} for l in listings])
        else:
            embeds = [
                create_market_embed_individual(item, locale)
                for item in listings
                if item['listing']['quantity_available']
            ]

            if not embeds:
                await interaction.response.send_message(t("lookup.no_listings_org", locale))
                return

            paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
            await paginator.send(interaction)

    org_search.name_localizations = {"uk": t("commands.lookup.org.name", "uk")}
    org_search.description_localizations = {"uk": t("commands.lookup.org.description", "uk")}

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
