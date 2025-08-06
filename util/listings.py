import datetime
from typing import List

import discord
import humanize
from discord.ext.paginators.button_paginator import ButtonPaginator

from util.iter import chunks
from util.i18n import t, get_locale

# These lists provide the internal keys for display options. The human readable
# strings are stored in the locale JSON files and accessed via ``t``/``tr``.
categories = [
    "armor",
    "clothing",
    "weapon",
    "paint",
    "bundle",
    "flair",
    "addon",
    "consumable",
    "other",
]

sorting_methods = {
    "title": "sorting.title",
    "price-low": "sorting.price_low",
    "price-high": "sorting.price_high",
    "quantity-low": "sorting.quantity_low",
    "quantity-high": "sorting.quantity_high",
    "date-new": "sorting.date_new",
    "date-old": "sorting.date_old",
    "activity": "sorting.activity",
    "rating": "sorting.rating",
}

sale_types = ["aggregate", "auction", "sale"]


def create_market_embed(listing: dict, locale: str):
    embed = discord.Embed(url=f"https://sc-market.space/market/{listing['listing_id']}", title=listing['title'])
    embed.add_field(
        name=t('fields.item_type', locale),
        value=t(f"categories.{listing['item_type'].lower()}", locale),
    )
    if listing["listing_type"] != "unique":
        embed.add_field(name=t('fields.minimum_price', locale), value=f"{int(listing['minimum_price']):,} aUEC")
        embed.add_field(name=t('fields.maximum_price', locale), value=f"{int(listing['maximum_price']):,} aUEC")
    else:
        embed.add_field(name=t('fields.price', locale), value=f"{int(listing['price']):,} aUEC")
        embed.add_field(
            name=t('fields.seller', locale),
            value=f"[{listing['contractor_seller'] or listing['user_seller']}]({'https://sc-market.space/contractor/' + listing['contractor_seller'] if listing['contractor_seller'] else 'https://sc-market.space/user/' + listing['user_seller']}) {'⭐' * int(round(listing['avg_rating']))}"
        )

    if listing['auction_end_time'] is not None:
        date = datetime.datetime.strptime(listing['auction_end_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        embed.add_field(
            name=t('fields.auction_end', locale),
            value=t('fields.ending', locale, time=humanize.naturaltime(date)),
        )

    embed.add_field(name=t('fields.quantity_available', locale), value=f"{int(listing['quantity_available']):,}")

    embed.set_image(url=listing['photo'])
    embed.timestamp = datetime.datetime.strptime(listing['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

    return embed


def create_market_embed_individual(listing: dict, locale: str):
    embed = discord.Embed(url=f"https://sc-market.space/market/{listing['listing']['listing_id']}",
                          title=listing['details']['title'])
    embed.add_field(
        name=t('fields.item_type', locale),
        value=t(f"categories.{listing['details']['item_type'].lower()}", locale),
    )
    embed.add_field(name=t('fields.price', locale), value=f"{int(listing['listing']['price']):,} aUEC")
    seller = listing['listing'].get('contractor_seller') or listing['listing'].get('user_seller')
    embed.add_field(
        name=t('fields.seller', locale),
        value=f"[{seller.get('name') or seller.get('display_name')}]({'https://sc-market.space/contractor/' + seller['spectrum_id'] if listing['listing'].get('contractor_seller') else 'https://sc-market.space/user/' + seller['username']}) {'⭐' * int(round(seller['rating']['avg_rating'] / 10))}"
    )

    if listing.get('auction_details') and listing['auction_details']['auction_end_time'] is not None:
        date = datetime.datetime.strptime(listing['auction_details']['auction_end_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        embed.add_field(
            name=t('fields.auction_end', locale),
            value=t('fields.ending', locale, time=humanize.naturaltime(date)),
        )

    embed.add_field(name=t('fields.quantity_available', locale), value=f"{int(listing['listing']['quantity_available']):,}")

    embed.set_image(url=listing['photos'][0] if listing[
        'photos'] else "https://cdn.robertsspaceindustries.com/static/images/Temp/default-image.png")
    embed.timestamp = datetime.datetime.strptime(listing['listing']['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

    return embed


def create_stock_embed(entries: List[str], locale: str):
    embed = discord.Embed(url=f"https://sc-market.space/market/manage?quantityAvailable=0",
                          title=t('fields.my_stock', locale))
    body = '\n'.join(entries)
    embed.description = f"""```ansi\n{body}\n```"""
    embed.timestamp = datetime.datetime.now()

    return embed


async def display_listings_compact(interaction: discord.Interaction, alllistings: list):
    locale = get_locale(interaction)
    pages = []
    for listings in chunks(alllistings, 10):
        mq = max(3, *(len(f"{int(l['quantity_available']):,}") for l in listings))
        tq = max(3, *(len(l['title']) for l in listings))
        pq = max(3, *(len(f"{int(l['price']):,}") for l in listings))

        entries = []
        for listing in listings:
            entries.append(
                f"\u001b[0;40;33m {int(listing['quantity_available']):>{mq},} \u001b[0;40;37m| \u001b[0;40;36m{listing['title']:<{tq}} \u001b[0;40;37m| \u001b[0;40;33m{int(listing['price']):>{pq},} \u001b[0;40;36maUEC "
            )

        header = f"\u001b[4;40;37m {t('fields.qt', locale):<{mq}} | {t('fields.item', locale):<{tq}} | {t('fields.price_label', locale):>{pq + 5}} "
        entries.insert(0, header)
        pages.append(entries)

    embeds = [create_stock_embed(page, locale) for page in pages]
    paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
    await paginator.send(interaction)
