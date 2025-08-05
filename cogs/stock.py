import json
import traceback
from typing import List

import discord
import ujson
from discord import app_commands
from discord.ext import commands

from util.fetch import internal_post, get_user_listings, get_user_orgs, get_org_listings
from util.i18n import t, get_locale, TRANSLATIONS
from util.listings import display_listings_compact


class stock(
    commands.GroupCog,
    name=lambda locale: t("commands.stock.group.name", locale),
    description=lambda locale: t("commands.stock.group.description", locale),
):
    def __init__(self, bot):
        self.bot = bot
        self.__cog_app_commands_group__.name_localizations = {
            loc: t("commands.stock.group.name", loc) for loc in TRANSLATIONS
        }
        self.__cog_app_commands_group__.description_localizations = {
            loc: t("commands.stock.group.description", loc) for loc in TRANSLATIONS
        }

    @app_commands.command(
        name=lambda locale: t("commands.stock.set.name", locale),
        description=lambda locale: t("commands.stock.set.description", locale),
    )
    @app_commands.describe(
        owner=app_commands.locale_str(
            t("commands.stock.set.owner", "en"),
            **{loc: t("commands.stock.set.owner", loc) for loc in TRANSLATIONS},
        ),
        listing=app_commands.locale_str(
            t("commands.stock.set.listing", "en"),
            **{loc: t("commands.stock.set.listing", loc) for loc in TRANSLATIONS},
        ),
        quantity=app_commands.locale_str(
            t("commands.stock.set.quantity", "en"),
            **{loc: t("commands.stock.set.quantity", loc) for loc in TRANSLATIONS},
        ),
    )
    async def set_stock(
            self,
            interaction: discord.Interaction,
            owner: str,
            listing: str,
            quantity: int,
    ):
        """Set the stock quantity for a given market listing"""
        await self.handle_stock_change(interaction, 'set', owner, listing, quantity)

    set_stock.name_localizations = {
        loc: t("commands.stock.set.name", loc) for loc in TRANSLATIONS
    }
    set_stock.description_localizations = {
        loc: t("commands.stock.set.description", loc) for loc in TRANSLATIONS
    }

    @app_commands.command(
        name=lambda locale: t("commands.stock.add.name", locale),
        description=lambda locale: t("commands.stock.add.description", locale),
    )
    @app_commands.describe(
        owner=app_commands.locale_str(
            t("commands.stock.add.owner", "en"),
            **{loc: t("commands.stock.add.owner", loc) for loc in TRANSLATIONS},
        ),
        listing=app_commands.locale_str(
            t("commands.stock.add.listing", "en"),
            **{loc: t("commands.stock.add.listing", loc) for loc in TRANSLATIONS},
        ),
        quantity=app_commands.locale_str(
            t("commands.stock.add.quantity", "en"),
            **{loc: t("commands.stock.add.quantity", loc) for loc in TRANSLATIONS},
        ),
    )
    async def add_stock(
            self,
            interaction: discord.Interaction,
            owner: str,
            listing: str,
            quantity: int,
    ):
        """Add to the stock quantity for a given market listing"""
        await self.handle_stock_change(interaction, 'add', owner, listing, quantity)

    add_stock.name_localizations = {
        loc: t("commands.stock.add.name", loc) for loc in TRANSLATIONS
    }
    add_stock.description_localizations = {
        loc: t("commands.stock.add.description", loc) for loc in TRANSLATIONS
    }

    @app_commands.command(
        name=lambda locale: t("commands.stock.sub.name", locale),
        description=lambda locale: t("commands.stock.sub.description", locale),
    )
    @app_commands.describe(
        owner=app_commands.locale_str(
            t("commands.stock.sub.owner", "en"),
            **{loc: t("commands.stock.sub.owner", loc) for loc in TRANSLATIONS},
        ),
        listing=app_commands.locale_str(
            t("commands.stock.sub.listing", "en"),
            **{loc: t("commands.stock.sub.listing", loc) for loc in TRANSLATIONS},
        ),
        quantity=app_commands.locale_str(
            t("commands.stock.sub.quantity", "en"),
            **{loc: t("commands.stock.sub.quantity", loc) for loc in TRANSLATIONS},
        ),
    )
    async def sub_stock(
            self,
            interaction: discord.Interaction,
            owner: str,
            listing: str,
            quantity: int,
    ):
        """Subtract from the stock quantity for a given market listing"""
        await self.handle_stock_change(interaction, 'sub', owner, listing, quantity)

    sub_stock.name_localizations = {
        loc: t("commands.stock.sub.name", loc) for loc in TRANSLATIONS
    }
    sub_stock.description_localizations = {
        loc: t("commands.stock.sub.description", loc) for loc in TRANSLATIONS
    }

    async def handle_stock_change(self, interaction: discord.Interaction, action: str, owner: str, listing: str,
                                  quantity: int):
        locale = get_locale(interaction.user.id, interaction)
        listing_payload = json.loads(listing)
        payload = {
            "quantity": quantity,
            "listing_id": listing_payload["l"],
            "discord_id": str(interaction.user.id),
        }

        response = await internal_post(
            f"/threads/market/quantity/{action.lower()}",
            json=payload,
            session=self.bot.session
        )

        if response.get("error"):
            await interaction.response.send_message(response['error'])
        else:
            newquantity = listing_payload['q']
            if action == "add":
                newquantity += quantity
            elif action == "sub":
                newquantity -= quantity
            else:
                newquantity = quantity

            await interaction.response.send_message(
                t("stock.updated", locale).format(
                    title=listing_payload['t'],
                    listing_id=listing_payload['l'],
                    old=listing_payload['q'],
                    new=newquantity,
                )
            )

    @app_commands.command(
        name=lambda locale: t("commands.stock.view.name", locale),
        description=lambda locale: t("commands.stock.view.description", locale),
    )
    @app_commands.describe(
        owner=app_commands.locale_str(
            t("commands.stock.view.owner", "en"),
            **{loc: t("commands.stock.view.owner", loc) for loc in TRANSLATIONS},
        ),
    )
    async def view_stock(
            self,
            interaction: discord.Interaction,
            owner: str = None,
    ):
        """View the stock quantity for a given market listing"""
        if owner and interaction.namespace.owner != "_ME":
            owner = json.loads(interaction.namespace.owner)
            listings = await get_org_listings(owner['s'], interaction.user.id,
                                              session=self.bot.session)
        else:
            listings = await get_user_listings(interaction.user.id, session=self.bot.session)

        locale = get_locale(interaction.user.id, interaction)
        if not listings:
            await interaction.response.send_message(t("stock.no_listings", locale), ephemeral=True)
            return

        await display_listings_compact(interaction, listings)

    view_stock.name_localizations = {
        loc: t("commands.stock.view.name", loc) for loc in TRANSLATIONS
    }
    view_stock.description_localizations = {
        loc: t("commands.stock.view.description", loc) for loc in TRANSLATIONS
    }

    @set_stock.autocomplete('listing')
    @add_stock.autocomplete('listing')
    @sub_stock.autocomplete('listing')
    async def update_stock_listing(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        locale = get_locale(interaction.user.id, interaction)
        try:
            if interaction.namespace.owner != "_ME":
                owner = json.loads(interaction.namespace.owner)
                listings = await get_org_listings(owner['s'], interaction.user.id,
                                                  session=self.bot.session)
            else:
                listings = await get_user_listings(interaction.user.id, session=self.bot.session)

            choices = [
                          app_commands.Choice(
                              name=f"{listing['title'][:100]} ({int(listing['quantity_available']):,} {t('stock.available', locale)})",
                              value=ujson.dumps(dict(l=listing['listing_id'], t=listing['title'],
                                                     q=int(listing['quantity_available'])))
                          )
                          for listing in listings if
                          current.lower() in listing['title'].lower()
                      ][:25]
            return choices
        except Exception as e:
            traceback.print_exc()
            raise e

    @set_stock.autocomplete('owner')
    @add_stock.autocomplete('owner')
    @sub_stock.autocomplete('owner')
    @view_stock.autocomplete('owner')
    async def update_stock_owner(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        locale = get_locale(interaction.user.id, interaction)
        orgs = await get_user_orgs(interaction.user.id, session=self.bot.session)

        choices = [
            app_commands.Choice(
                name=f"{org['name']} ({org['spectrum_id']})",
                value=json.dumps(dict(s=org['spectrum_id'], n=org['name']))
            )
            for org in orgs
            if current.lower() in org['name'].lower() or current.lower() in org['spectrum_id'].lower()
        ][:24]

        me_choice = app_commands.Choice(name=t('stock.me', locale), value='_ME')
        me_choice.name_localizations = {loc: t('stock.me', loc) for loc in TRANSLATIONS}
        return choices + [me_choice]
