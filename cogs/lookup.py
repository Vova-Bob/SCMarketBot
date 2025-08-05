from typing import List

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.paginators.button_paginator import ButtonPaginator

from util.fetch import public_fetch, search_users, search_orgs
from util.i18n import TRANSLATIONS, get_locale, t
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

    # Pre-build localized choices for categories, sorting methods, and sale types
    category_choices = []
    for value, name_key in categories.items():
        choice = app_commands.Choice(name=t(name_key), value=value)  # name_key
        choice.name_localizations = {
            loc: t(name_key, loc) for loc in TRANSLATIONS
        }
        category_choices.append(choice)

    sorting_choices = []
    for key, name_key in sorting_methods.items():
        choice = app_commands.Choice(name=t(name_key), value=key)  # name_key
        choice.name_localizations = {
            loc: t(name_key, loc) for loc in TRANSLATIONS
        }
        sorting_choices.append(choice)

    sale_type_choices = []
    for value, name_key in sale_types.items():
        choice = app_commands.Choice(name=t(name_key), value=value)  # name_key
        choice.name_localizations = {
            loc: t(name_key, loc) for loc in TRANSLATIONS
        }
        sale_type_choices.append(choice)

    @app_commands.command(
        name=lambda locale: t("commands.lookup.search.name", locale),  # commands.lookup.search.name
        description=lambda locale: t(
            "commands.lookup.search.description", locale
        ),  # commands.lookup.search.description
    )
    @app_commands.describe(
        query=app_commands.locale_str(
            t("commands.lookup.search.query"),  # commands.lookup.search.query
            **{
                loc: t("commands.lookup.search.query", loc)
                for loc in TRANSLATIONS
            },
        ),
        category=app_commands.locale_str(
            t("commands.lookup.search.category"),  # commands.lookup.search.category
            **{
                loc: t("commands.lookup.search.category", loc)
                for loc in TRANSLATIONS
            },
        ),
        sorting=app_commands.locale_str(
            t("commands.lookup.search.sorting"),  # commands.lookup.search.sorting
            **{
                loc: t("commands.lookup.search.sorting", loc)
                for loc in TRANSLATIONS
            },
        ),
        sale_type=app_commands.locale_str(
            t("commands.lookup.search.sale_type"),  # commands.lookup.search.sale_type
            **{
                loc: t("commands.lookup.search.sale_type", loc)
                for loc in TRANSLATIONS
            },
        ),
        quantity_available=app_commands.locale_str(
            t("commands.lookup.search.quantity_available"),  # commands.lookup.search.quantity_available
            **{
                loc: t("commands.lookup.search.quantity_available", loc)
                for loc in TRANSLATIONS
            },
        ),
        min_cost=app_commands.locale_str(
            t("commands.lookup.search.min_cost"),  # commands.lookup.search.min_cost
            **{
                loc: t("commands.lookup.search.min_cost", loc)
                for loc in TRANSLATIONS
            },
        ),
        max_cost=app_commands.locale_str(
            t("commands.lookup.search.max_cost"),  # commands.lookup.search.max_cost
            **{
                loc: t("commands.lookup.search.max_cost", loc)
                for loc in TRANSLATIONS
            },
        ),
    )
    @app_commands.choices(
        category=category_choices,
        sorting=sorting_choices,
        sale_type=sale_type_choices,
    )
    async def search(
            self,
            interaction: discord.Interaction,
            query: str,
            category: str | None = None,
            sorting: str | None = 'activity',
            sale_type: str | None = None,
            quantity_available: int = 1,
            min_cost: int = 0,
            max_cost: int = 0,
    ):
        """Search the site market listings"""
        locale = get_locale(interaction.user.id, interaction)
        params = {
            'query': query,
            'sort': sorting.value if isinstance(sorting, app_commands.Choice) else sorting,
            'quantityAvailable': quantity_available,
            'minCost': min_cost,
            'page_size': 48,
            'index': 0
        }

        if category:
            params['item_type'] = category.value if isinstance(category, app_commands.Choice) else category
        if sale_type:
            params['sale_type'] = sale_type.value if isinstance(sale_type, app_commands.Choice) else sale_type
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
            return

        paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
        await paginator.send(interaction)

    lookup = app_commands.Group(
        name=lambda locale: t(
            "commands.lookup.group.name", locale
        ),  # commands.lookup.group.name
        description=lambda locale: t(
            "commands.lookup.group.description", locale
        ),  # commands.lookup.group.description
    )

    @lookup.command(
        name=lambda locale: t(
            "commands.lookup.user.name", locale
        ),  # commands.lookup.user.name
        description=lambda locale: t(
            "commands.lookup.user.description", locale
        ),  # commands.lookup.user.description
    )
    @app_commands.describe(
        handle=app_commands.locale_str(
            t("commands.lookup.user.handle"),  # commands.lookup.user.handle
            **{
                loc: t("commands.lookup.user.handle", loc)
                for loc in TRANSLATIONS
            },
        ),
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

    @lookup.command(
        name=lambda locale: t(
            "commands.lookup.org.name", locale
        ),  # commands.lookup.org.name
        description=lambda locale: t(
            "commands.lookup.org.description", locale
        ),  # commands.lookup.org.description
    )
    @app_commands.describe(
        spectrum_id=app_commands.locale_str(
            t("commands.lookup.org.spectrum_id"),  # commands.lookup.org.spectrum_id
            **{
                loc: t("commands.lookup.org.spectrum_id", loc)
                for loc in TRANSLATIONS
            },
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
