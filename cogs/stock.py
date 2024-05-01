from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from util.fetch import internal_post, get_user_listings, get_user_orgs, get_org_listings


class Market(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stock")
    @app_commands.describe(
        owner='The owner of the listing you want to update. Either you or one of your contractors',
        listing='The listing to modify',
        quantity='The new quantity to set for the listing',
        action='Choose whether to set, add, or subtract the stock',
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name=name, value=value) for name, value in
            [("Add", "add"), ("Set", "set"), ("Subtract", "sub")]
        ],
    )
    async def set_stock(
            self,
            interaction: discord.Interaction,
            action: str,
            owner: str,
            listing: str,
            quantity: int,
    ):
        """Set the stock quantity for a given market listing"""
        payload = {
            "quantity": quantity,
            "listing_id": listing,
            "discord_id": str(interaction.user.id),
        }

        if owner != "_ME":
            payload["contractor_id"] = owner

        response = await internal_post(
            "/threads/market/quantity/set",
            json=payload,
            session=self.bot.session
        )

        if response.get("error"):
            await interaction.response.send_message(response['error'])
        else:
            await interaction.response.send_message(
                f"Successfully updated stock for the [listing](<https://sc-market.space/market/{listing}>)"
            )

    @set_stock.autocomplete('listing')
    async def update_stock_listing(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        if interaction.namespace.owner != "_ME":
            listings = await get_org_listings(interaction.namespace.owner, interaction.user.id,
                                              session=self.bot.session)
        else:
            listings = await get_user_listings(interaction.user.id, session=self.bot.session)

        return [
            app_commands.Choice(name=f"{listing['title']} ({listing['listing_id'].split('-')[0]})",
                                value=listing['listing_id'])
            for listing in listings if
            current.lower() in listing['title'].lower() or current.lower() in listing['description'].lower()
        ][:25]

    @set_stock.autocomplete('owner')
    async def update_stock_owner(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        orgs = await get_user_orgs(interaction.user.id, session=self.bot.session)

        return [
            app_commands.Choice(name=f"{org['name']} ({org['spectrum_id']})", value=org['spectrum_id'])
            for org in orgs if
            current.lower() in org['name'].lower() or current.lower() in org['spectrum_id'].lower()
        ] + [app_commands.Choice(name=f"Me", value='_ME')]
