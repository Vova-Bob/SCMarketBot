import discord
from discord import app_commands
from discord.ext import commands

from util.fetch import internal_post, get_users_orders
from util.views import UpdateView, EntrySpec


class order(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status")
    @app_commands.describe(
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
            newstatus: str
    ):
        """Set the new status for the order in the current thread"""
        if isinstance(interaction.channel, discord.Thread):
            response = await internal_post("/threads/order/status",
                                           json={
                                               "status": newstatus,
                                               "thread_id": str(interaction.channel.id),
                                               "discord_id": str(interaction.user.id)
                                           },
                                           session=self.bot.session)

            if response.get("error"):
                await interaction.response.send_message(response['error'])
            else:
                await interaction.response.send_message("Successfully updated status")
        else:
            orders = await get_users_orders(interaction.user.id, session=self.bot.session)

            async def callback(interaction, order_ids):
                response = await internal_post("/threads/order/status",
                                               json={
                                                   "status": newstatus,
                                                   "order_id": order_ids[0],
                                                   "discord_id": str(interaction.user.id)
                                               },
                                               session=self.bot.session)

                if response.get("error"):
                    await interaction.response.send_message(response['error'])
                else:
                    await interaction.response.send_message("Successfully updated status")

            spec = EntrySpec(
                [(order['title'], order['description'], order['order_id']) for order in orders[:25]],
                placeholder='Select order to update'
            )

            view = UpdateView(interaction, callback, [spec])
            await interaction.response.send_message("No order in this channel. Please select an order to update.",
                                                    view=view)
