import dataclasses
from typing import Tuple, List

import discord.ui

from .i18n import t


class SelectItem(discord.ui.Select):
    def __init__(
        self,
        choices: List[Tuple[str, str, str]],
        min_values: int = 1,
        max_values: int = 1,
        placeholder: str | None = None,
    ):
        super().__init__(
            min_values=min_values,
            max_values=max_values,
            placeholder=placeholder,
            options=[
                discord.SelectOption(
                    label=label,
                    description=description[:97]
                    + "..."[: 100 - len(description)]
                    if description
                    else None,
                    value=value,
                )
                for label, description, value in choices
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)


@dataclasses.dataclass
class EntrySpec:
    choices: List[Tuple[str, str, str]]
    min_values: int = 1
    max_values: int = 1
    placeholder: str | None = None


class UpdateView(discord.ui.View):
    def __init__(self, interaction, callback: callable, specs: List[EntrySpec], locale: str):
        super().__init__()
        self.interaction = interaction
        self.selects: List[SelectItem] = []
        for spec in specs:
            item = SelectItem(
                spec.choices,
                spec.min_values,
                spec.max_values,
                spec.placeholder or t("views.select_status", locale),
            )
            self.selects.append(item)
            self.add_item(item)
        self.submit.label = t("views.update", locale)
        self.callback = callback

    async def send(self):
        await self.interaction.response.send_message(view=self, ephemeral=True)

    @discord.ui.button()
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.callback(interaction, *[item.values for item in self.selects])
