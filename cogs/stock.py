import json
import traceback
from typing import List

import discord
import ujson
from discord import app_commands
from discord.ext import commands

from util.fetch import internal_post, get_user_listings, get_user_orgs, get_org_listings
from util.i18n import t, get_locale
from util.listings import display_listings_compact


class stock(
    commands.GroupCog,
    name=t("commands.stock.group.name"),
    description=t("commands.stock.group.description"),
):
    def __init__(self, bot):
        self.bot = bot
        self.__cog_app_commands_group__.name_localizations = {
            "uk": t("commands.stock.group.name", "uk")
        }
        self.__cog_app_commands_group__.description_localizations = {
            "uk": t("commands.stock.group.description", "uk")
        }

    @app_commands.command(
        name=t("commands.stock.set.name"),
        description=t("commands.stock.set.description"),
    )
    @app_commands.describe(
        owner=app_commands.locale_str(
            "The owner of the listing you want to update. Either you or one of your contractors",
            uk="Власник оголошення, яке потрібно оновити. Ви або ваш підрядник",
        ),
        listing=app_commands.locale_str("The listing to modify", uk="Оголошення для змін"),
        quantity=app_commands.locale_str(
            "The new quantity to set for the listing",
            uk="Нова кількість для оголошення",
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

    set_stock.name_localizations = {"uk": t("commands.stock.set.name", "uk")}
    set_stock.description_localizations = {
        "uk": t("commands.stock.set.description", "uk")
    }

    @app_commands.command(
        name=t("commands.stock.add.name"),
        description=t("commands.stock.add.description"),
    )
    @app_commands.describe(
        owner=app_commands.locale_str(
            "The owner of the listing you want to update. Either you or one of your contractors",
            uk="Власник оголошення, яке потрібно оновити. Ви або ваш підрядник",
        ),
        listing=app_commands.locale_str("The listing to modify", uk="Оголошення для змін"),
        quantity=app_commands.locale_str(
            "The quantity to add to the listings stock",
            uk="Кількість, яку додати до запасу",
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

    add_stock.name_localizations = {"uk": t("commands.stock.add.name", "uk")}
    add_stock.description_localizations = {
        "uk": t("commands.stock.add.description", "uk")
    }

    @app_commands.command(
        name=t("commands.stock.sub.name"),
        description=t("commands.stock.sub.description"),
    )
    @app_commands.describe(
        owner=app_commands.locale_str(
            "The owner of the listing you want to update. Either you or one of your contractors",
            uk="Власник оголошення, яке потрібно оновити. Ви або ваш підрядник",
        ),
        listing=app_commands.locale_str("The listing to modify", uk="Оголошення для змін"),
        quantity=app_commands.locale_str(
            "The quantity to subtract from the listings stock",
            uk="Кількість, яку відняти із запасу",
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

    sub_stock.name_localizations = {"uk": t("commands.stock.sub.name", "uk")}
    sub_stock.description_localizations = {
        "uk": t("commands.stock.sub.description", "uk")
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
        name=t("commands.stock.view.name"),
        description=t("commands.stock.view.description"),
    )
    @app_commands.describe(
        owner=app_commands.locale_str(
            "The owner of the listing you want to update. Either you or one of your contractors",
            uk="Власник оголошення, яке потрібно оновити. Ви або ваш підрядник",
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

    view_stock.name_localizations = {"uk": t("commands.stock.view.name", "uk")}
    view_stock.description_localizations = {
        "uk": t("commands.stock.view.description", "uk")
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

        return [
            app_commands.Choice(
                name=f"{org['name']} ({org['spectrum_id']})",
                value=json.dumps(dict(s=org['spectrum_id'], n=org['name']))
            )
            for org in orgs
            if current.lower() in org['name'].lower() or current.lower() in org['spectrum_id'].lower()
        ][:24] + [app_commands.Choice(name=t('stock.me', locale), value='_ME')]
