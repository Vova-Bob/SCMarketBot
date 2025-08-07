from __future__ import annotations

from typing import Sequence

import discord
from discord.ext.paginators.button_paginator import ButtonPaginator, PaginatorButton

from util.i18n import t


class LocalizedPaginator(ButtonPaginator):
    """Button paginator with localized labels and messages."""

    def __init__(self, pages: Sequence, locale: str, *, author_id: int | None = None, **kwargs) -> None:
        self.locale = locale
        buttons = {
            "FIRST": PaginatorButton(label=t('paginator.first', locale), position=0),
            "LEFT": PaginatorButton(label=t('paginator.left', locale), position=1),
            "PAGE_INDICATOR": PaginatorButton(label="", position=2, disabled=False),
            "RIGHT": PaginatorButton(label=t('paginator.right', locale), position=3),
            "LAST": PaginatorButton(label=t('paginator.last', locale), position=4),
            "STOP": PaginatorButton(label=t('paginator.stop', locale), style=discord.ButtonStyle.danger, position=5),
        }
        super().__init__(pages, buttons=buttons, author_id=author_id, **kwargs)

    @property
    def page_string(self) -> str:  # type: ignore[override]
        return t('paginator.page', self.locale, page=self.current_page + 1, total=self.max_pages)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:  # type: ignore[override]
        valid = await super().interaction_check(interaction)
        if not valid and not interaction.response.is_done():
            await interaction.response.send_message(t('paginator.action_failed', self.locale), ephemeral=True)
        return valid
