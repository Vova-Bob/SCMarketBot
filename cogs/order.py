import json
import traceback
from typing import List

import discord
import ujson
from discord import app_commands
from discord.ext import commands

from util.fetch import internal_post, get_user_orders
from util.i18n import t, get_locale


class order(
    commands.GroupCog,
    name=t("commands.order.group.name"),
    description=t("commands.order.group.description"),
):
    def __init__(self, bot):
        self.bot = bot
        self.__cog_app_commands_group__.name_localizations = {
            "uk": t("commands.order.group.name", "uk")
        }
        self.__cog_app_commands_group__.description_localizations = {
            "uk": t("commands.order.group.description", "uk")
        }

    @app_commands.command(
        name=t("commands.order.status.name"),
        description=t("commands.order.status.description"),
    )
    @app_commands.describe(
        order=app_commands.locale_str("The order to update", uk="Замовлення для оновлення"),
        newstatus=app_commands.locale_str(
            "The new status to set the order to",
            uk="Новий статус замовлення",
        ),
    )
    @app_commands.choices(
        newstatus=[
            app_commands.Choice(name=t("order.status.fulfilled"), value="fulfilled"),
            app_commands.Choice(name=t("order.status.in_progress"), value="in-progress"),
            app_commands.Choice(name=t("order.status.cancelled"), value="cancelled"),
        ],
    )
    async def update_status(
            self,
            interaction: discord.Interaction,
            newstatus: str,
            order: str = None,
    ):
        """Set the new status for the order in the current thread"""
        locale = get_locale(interaction.user.id, interaction)
        if order is None:
            if isinstance(interaction.channel, discord.Thread):
                response = await internal_post(
                    "/threads/order/status",
                    json={
                        "status": newstatus,
                        "thread_id": str(interaction.channel.id),
                        "discord_id": str(interaction.user.id)
                    },
                    session=self.bot.session
                )
            else:
                await interaction.response.send_message(t("order.no_order", locale))
                return
        else:
            try:
                order_payload = json.loads(order)
            except json.JSONDecodeError:
                await interaction.response.send_message(t("order.invalid", locale))
                return
            response = await internal_post(
                "/threads/order/status",
                json={
                    "status": newstatus,
                    "order_id": order_payload['o'],
                    "discord_id": str(interaction.user.id)
                },
                session=self.bot.session
            )

        if response.get("error"):
            await interaction.response.send_message(response['error'])
        else:
            if order:
                await interaction.response.send_message(
                    t("order.update_success_with_title", locale).format(
                        status=t(f"order.status.{newstatus.replace('-', '_')}", locale),
                        title=order_payload['t'],
                        order_id=order_payload['o'],
                    )
                )
            else:
                await interaction.response.send_message(t("order.update_success", locale))

    update_status.name_localizations = {
        "uk": t("commands.order.status.name", "uk")
    }
    update_status.description_localizations = {
        "uk": t("commands.order.status.description", "uk")
    }

    @update_status.autocomplete('order')
    async def update_status_order_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> List[app_commands.Choice[str]]:
        try:
            orders = await get_user_orders(interaction.user.id, session=self.bot.session)
            choices = [
                app_commands.Choice(name=order['title'],
                                    value=ujson.dumps(dict(t=order['title'], o=order['order_id'])))
                for order in orders if
                (current.lower() in order['title'].lower() or current.lower() in order['description'].lower()) and
                order['status'] != interaction.namespace.newstatus
            ]
            return choices

        except Exception as e:
            traceback.print_exc()
            raise e
