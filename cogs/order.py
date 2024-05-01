from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from util.fetch import internal_post, get_user_orders


class order(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status")
    @app_commands.describe(
        order='The order to update',
        newstatus='The new status to set the order to',
    )
    @app_commands.choices(
        newstatus=[
            app_commands.Choice(name=name, value=value) for name, value in
            [("Fulfilled", "fulfilled"), ("In Progress", "in-progress"), ("Cancelled", "cancelled")]
        ],
    )
    async def update_status(
            self,
            interaction: discord.Interaction,
            newstatus: str,
            order: str = None,
    ):
        """Set the new status for the order in the current thread"""
        if order is None:
            if isinstance(interaction.channel, discord.Thread):
                response = await internal_post("/threads/order/status",
                                               json={
                                                   "status": newstatus,
                                                   "thread_id": str(interaction.channel.id),
                                                   "discord_id": str(interaction.user.id)
                                               },
                                               session=self.bot.session)
            else:
                await interaction.response.send_message("No order in this channel. Please select an order to update.")
                return
        else:
            response = await internal_post(
                "/threads/order/status",
                json={
                    "status": newstatus,
                    "order_id": order,
                    "discord_id": str(interaction.user.id)
                },
                session=self.bot.session
            )

        if response.get("error"):
            await interaction.response.send_message(response['error'])
        else:
            if order:
                await interaction.response.send_message(
                    f"Successfully updated status for the [order](<https://sc-market.space/contract/{order}>)"
                )
            else:
                await interaction.response.send_message(f"Successfully updated status for the order")

    @update_status.autocomplete('order')
    async def update_status_order_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        orders = await get_user_orders(interaction.user.id, session=self.bot.session)

        return [
            app_commands.Choice(name=f"{order['title']} ({order['order_id'].split('-')[0]})", value=order['order_id'])
            for order in orders if
            (current.lower() in order['title'].lower() or current.lower() in order['description'].lower()) and order[
                'status'] != interaction.namespace.newstatus
        ]
