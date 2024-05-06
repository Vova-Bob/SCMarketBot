import json
import traceback
from datetime import datetime
from typing import List

import discord
import ujson
from discord import app_commands
from discord.ext import commands
from discord.ext.paginators.button_paginator import ButtonPaginator

from util.fetch import internal_post, get_user_listings, get_user_orgs, get_org_listings
from util.iter import chunks


def create_stock_embed(entries: List[str]):
    embed = discord.Embed(url=f"https://sc-market.space/market/manage?quantityAvailable=0",
                          title="My Stock")
    body = '\n'.join(entries)
    embed.description = f"""```ansi\n{body}\n```"""
    embed.timestamp = datetime.now()

    return embed


class stock(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set")
    @app_commands.describe(
        owner='The owner of the listing you want to update. Either you or one of your contractors',
        listing='The listing to modify',
        quantity='The new quantity to set for the listing',
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

    @app_commands.command(name="add")
    @app_commands.describe(
        owner='The owner of the listing you want to update. Either you or one of your contractors',
        listing='The listing to modify',
        quantity='The quantity to add to the listings stock',
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

    @app_commands.command(name="sub")
    @app_commands.describe(
        owner='The owner of the listing you want to update. Either you or one of your contractors',
        listing='The listing to modify',
        quantity='The quantity to subtract from the listings stock',
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
                f"Stock for [{listing_payload['t']}](<https://sc-market.space/market/{listing_payload['l']}>) has been set from `{listing_payload['q']}` to `{newquantity}`."
            )

    @app_commands.command(name="view")
    @app_commands.describe(
        owner='The owner of the listing you want to update. Either you or one of your contractors',
    )
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
            await interaction.response.send_message("No listings to display", ephemeral=True)

        mq = max(3, *(len(f"{int(l['quantity_available']):,}") for l in listings))
        tq = max(3, *(len(l['title']) for l in listings))
        pq = max(3, *(len(f"{int(l['price']):,}") for l in listings))

        entries = []
        for listing in listings:
            entries.append(
                f"\u001b[0;40;33m {int(listing['quantity_available']):>{mq},} \u001b[0;40;37m| \u001b[0;40;36m{listing['title']:<{tq}} \u001b[0;40;37m| \u001b[0;40;33m{int(listing['price']):>{pq},} \u001b[0;40;36maUEC "
            )

        pages = list(chunks(entries, 10))
        header = f"\u001b[4;40;37m {'Qt.':<{mq}} | {'Item':<{tq}} | {'Price':>{pq + 5}} "
        for page in pages:
            page.insert(0, header)
        embeds = [create_stock_embed(page) for page in pages]
        paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
        await paginator.send(interaction)

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
                              name=f"{listing['title'][:100]} ({int(listing['quantity_available']):,} available)",
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
        ] + [app_commands.Choice(name=f"Me", value='_ME')]
