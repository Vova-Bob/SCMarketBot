import json
import traceback
from typing import List

import discord
import ujson
from discord import app_commands
from discord.ext import commands

from util.fetch import internal_post, get_user_listings, get_user_orgs, get_org_listings
from util.listings import display_listings_compact
from util.i18n import tr, cmd, option


class stock(commands.GroupCog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(**cmd('stock.set'))
    @app_commands.describe(
        owner=option('stock.set', 'owner'),
        listing=option('stock.set', 'listing'),
        quantity=option('stock.set', 'quantity'),
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

    @app_commands.command(**cmd('stock.add'))
    @app_commands.describe(
        owner=option('stock.add', 'owner'),
        listing=option('stock.add', 'listing'),
        quantity=option('stock.add', 'quantity'),
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

    @app_commands.command(**cmd('stock.sub'))
    @app_commands.describe(
        owner=option('stock.sub', 'owner'),
        listing=option('stock.sub', 'listing'),
        quantity=option('stock.sub', 'quantity'),
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

    async def handle_stock_change(self, interaction: discord.Interaction, action: str, owner: str, listing: str,
                                  quantity: int):
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
            await interaction.response.send_message(
                tr(interaction, 'stock.backend_error', error=response['error'])
            )
        else:
            newquantity = listing_payload['q']
            if action == "add":
                newquantity += quantity
            elif action == "sub":
                newquantity -= quantity
            else:
                newquantity = quantity

            await interaction.response.send_message(
                tr(interaction, 'stock.stock_set', title=listing_payload['t'], old=listing_payload['q'], new=newquantity)
            )

    @app_commands.command(**cmd('stock.view'))
    @app_commands.describe(owner=option('stock.view', 'owner'))
    async def view_stock(
            self,
            interaction: discord.Interaction,
            owner: str = None,
    ):
        """Set the stock quantity for a given market listing"""
        if owner and interaction.namespace.owner != "_ME":
            owner = json.loads(interaction.namespace.owner)
            listings = await get_org_listings(owner['s'], interaction.user.id,
                                              session=self.bot.session)
        else:
            listings = await get_user_listings(interaction.user.id, session=self.bot.session)

        if not listings:
            await interaction.response.send_message(tr(interaction, 'stock.no_listings'), ephemeral=True)
            return

        await display_listings_compact(interaction, listings, empty_key='stock.no_listings')

    @set_stock.autocomplete('listing')
    @add_stock.autocomplete('listing')
    @sub_stock.autocomplete('listing')
    async def update_stock_listing(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        try:
            if interaction.namespace.owner != "_ME":
                owner = json.loads(interaction.namespace.owner)
                listings = await get_org_listings(owner['s'], interaction.user.id,
                                                  session=self.bot.session)
            else:
                listings = await get_user_listings(interaction.user.id, session=self.bot.session)

            choices = [
                          app_commands.Choice(
                              name=f"{listing['title'][:100]} ({int(listing['quantity_available']):,} "
                                   f"{tr(interaction, 'stock.available')})",
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
        orgs = await get_user_orgs(interaction.user.id, session=self.bot.session)

        return [
            app_commands.Choice(name=f"{org['name']} ({org['spectrum_id']})",
                                value=json.dumps(dict(s=org['spectrum_id'], n=org['name'])))
            for org in orgs if
            current.lower() in org['name'].lower() or current.lower() in org['spectrum_id'].lower()
        ][:24] + [app_commands.Choice(name=tr(interaction, 'stock.me'), value='_ME')]
