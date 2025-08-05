import json
import traceback
from typing import List

import discord
import ujson
from discord import app_commands
from discord.ext import commands

from util.fetch import internal_post, get_user_orders
from util.i18n import TRANSLATIONS, get_locale, t


class order(
    commands.GroupCog,
    name=lambda locale: t("commands.order.group.name", locale),
    description=lambda locale: t("commands.order.group.description", locale),
):
    def __init__(self, bot):
        self.bot = bot
        self.__cog_app_commands_group__.name_localizations = {
            loc: t("commands.order.group.name", loc) for loc in TRANSLATIONS
        }
        self.__cog_app_commands_group__.description_localizations = {
            loc: t("commands.order.group.description", loc) for loc in TRANSLATIONS
        }

    status_choices = []
    for value, key in [
        ("fulfilled", "order.status.fulfilled"),
        ("in-progress", "order.status.in_progress"),
        ("cancelled", "order.status.cancelled"),
    ]:
        choice = app_commands.Choice(name=t(key), value=value)
        choice.name_localizations = {loc: t(key, loc) for loc in TRANSLATIONS}
        status_choices.append(choice)

    @app_commands.command(
        name=lambda locale: t("commands.order.status.name", locale),
        description=lambda locale: t("commands.order.status.description", locale),
    )
    @app_commands.describe(
        order=app_commands.locale_str(
            t("commands.order.status.order", "en"),
            **{loc: t("commands.order.status.order", loc) for loc in TRANSLATIONS},
        ),
        newstatus=app_commands.locale_str(
            t("commands.order.status.newstatus", "en"),
            **{loc: t("commands.order.status.newstatus", loc) for loc in TRANSLATIONS},
        ),
    )
    @app_commands.choices(newstatus=status_choices)
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
        loc: t("commands.order.status.name", loc) for loc in TRANSLATIONS
    }
    update_status.description_localizations = {
        loc: t("commands.order.status.description", loc) for loc in TRANSLATIONS
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
