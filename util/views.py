import dataclasses
from typing import Tuple, List

import discord.ui


class SelectItem(discord.ui.Select):
    def __init__(self, choices: List[Tuple[str, str, str]], min_values=1, max_values=1, placeholder='Select status...'):
        super().__init__(
            min_values=min_values, max_values=max_values, placeholder=placeholder,
            options=[
                discord.SelectOption(label=label,
                                     description=description[:97] + "..."[
                                                                    :100 - len(description)] if description else None,
                                     value=value)
                for label, description, value in choices
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)


@dataclasses.dataclass
class EntrySpec:
    choices: List[Tuple[str, str, str]]
    min_values: int = 1
    max_values: int = 1
    placeholder: str = 'Select status...'


class UpdateView(discord.ui.View):
    def __init__(self, interaction, callback: callable, specs: List[EntrySpec]):
        super().__init__()
        self.interaction = interaction
        self.selects = []
        for spec in specs:
            item = SelectItem(spec.choices, spec.min_values, spec.max_values, spec.placeholder)
            self.selects.append(item)
            self.add_item(item)
        self.callback = callback

    async def send(self):
        await self.interaction.response.send_message(view=self, ephemeral=True)

    @discord.ui.button(label='Update')
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.callback(interaction, *[item.values for item in self.selects])
