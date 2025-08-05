import datetime
from typing import List

import discord
import humanize
from discord.ext.paginators.button_paginator import ButtonPaginator

from util.i18n import t, get_locale
from util.iter import chunks

# Mapping of category identifiers to translation keys
categories = {
    "armor": "listings.category.armor",
    "clothing": "listings.category.clothing",
    "weapon": "listings.category.weapon",
    "paint": "listings.category.paint",
    "bundle": "listings.category.bundle",
    "flair": "listings.category.flair",
    "addon": "listings.category.addon",
    "consumable": "listings.category.consumable",
    "other": "listings.category.other",
}

# Mapping of sorting identifiers to translation keys
sorting_methods = {
    "title": "listings.sort.title",
    "price-low": "listings.sort.price_low",
    "price-high": "listings.sort.price_high",
    "quantity-low": "listings.sort.quantity_low",
    "quantity-high": "listings.sort.quantity_high",
    "date-new": "listings.sort.date_new",
    "date-old": "listings.sort.date_old",
    "activity": "listings.sort.activity",
    "rating": "listings.sort.rating",
}

# Mapping of sale type identifiers to translation keys
sale_types = {
    "aggregate": "listings.sale_type.aggregate",
    "auction": "listings.sale_type.auction",
    "sale": "listings.sale_type.sale",
}


def create_market_embed(listing: dict, locale: str):
    embed = discord.Embed(
        url=f"https://sc-market.space/market/{listing['listing_id']}",
        title=listing['title'],
    )
    embed.add_field(
        name=t("listings.field.item_type", locale),
        value=listing['item_type'].capitalize(),
    )
    if listing["listing_type"] != "unique":
        embed.add_field(
            name=t("listings.field.min_price", locale),
            value=f"{int(listing['minimum_price']):,} aUEC",
        )
        embed.add_field(
            name=t("listings.field.max_price", locale),
            value=f"{int(listing['maximum_price']):,} aUEC",
        )
    else:
        embed.add_field(
            name=t("listings.field.price", locale),
            value=f"{int(listing['price']):,} aUEC",
        )
        embed.add_field(
            name=t("listings.field.seller", locale),
            value=(
                f"[{listing['contractor_seller'] or listing['user_seller']}]"
                f"({'https://sc-market.space/contractor/' + listing['contractor_seller'] if listing['contractor_seller'] else 'https://sc-market.space/user/' + listing['user_seller']})"
                f" {'⭐' * int(round(listing['avg_rating']))}"
            ),
        )

    if listing['auction_end_time'] is not None:
        date = datetime.datetime.strptime(
            listing['auction_end_time'], '%Y-%m-%dT%H:%M:%S.%fZ'
        )
        embed.add_field(
            name=t("listings.field.auction_end", locale),
            value=t("listings.field.ending", locale) + humanize.naturaltime(date),
        )

    embed.add_field(
        name=t("listings.field.quantity_available", locale),
        value=f"{int(listing['quantity_available']):,}",
    )

    embed.set_image(url=listing['photo'])
    embed.timestamp = datetime.datetime.strptime(
        listing['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ'
    )

    return embed


def create_market_embed_individual(listing: dict, locale: str):
    embed = discord.Embed(
        url=f"https://sc-market.space/market/{listing['listing']['listing_id']}",
        title=listing['details']['title'],
    )
    embed.add_field(
        name=t("listings.field.item_type", locale),
        value=listing['details']['item_type'].capitalize(),
    )
    embed.add_field(
        name=t("listings.field.price", locale),
        value=f"{int(listing['listing']['price']):,} aUEC",
    )
    seller = listing['listing'].get('contractor_seller') or listing['listing'].get('user_seller')
    embed.add_field(
        name=t("listings.field.seller", locale),
        value=f"[{seller.get('name') or seller.get('display_name')}]({'https://sc-market.space/contractor/' + seller['spectrum_id'] if listing['listing'].get('contractor_seller') else 'https://sc-market.space/user/' + seller['username']}) {'⭐' * int(round(seller['rating']['avg_rating'] / 10))}"
    )

    if listing.get('auction_details') and listing['auction_details']['auction_end_time'] is not None:
        date = datetime.datetime.strptime(listing['auction_details']['auction_end_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        embed.add_field(
            name=t("listings.field.auction_end", locale),
            value=t("listings.field.ending", locale) + humanize.naturaltime(date),
        )

    embed.add_field(
        name=t("listings.field.quantity_available", locale),
        value=f"{int(listing['listing']['quantity_available']):,}",
    )

    embed.set_image(url=listing['photos'][0] if listing[
        'photos'] else "https://cdn.robertsspaceindustries.com/static/images/Temp/default-image.png")
    embed.timestamp = datetime.datetime.strptime(listing['listing']['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

    return embed


def create_stock_embed(entries: List[str], locale: str):
    embed = discord.Embed(
        url="https://sc-market.space/market/manage?quantityAvailable=0",
        title=t("listings.stock.title", locale),
    )
    body = '\n'.join(entries)
    embed.description = f"""```ansi\n{body}\n```"""
    embed.timestamp = datetime.datetime.now()

    return embed


async def display_listings_compact(interaction: discord.Interaction, alllistings: list):
    locale = get_locale(interaction.user.id, interaction)
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

        header = (
            f"\u001b[4;40;37m {t('listings.stock.header.qt', locale):<{mq}} | "
            f"{t('listings.stock.header.item', locale):<{tq}} | "
            f"{t('listings.stock.header.price', locale):>{pq + 5}} "
        )
        entries.insert(0, header)
        pages.append(entries)

    embeds = [create_stock_embed(page, locale) for page in pages]
    paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
    await paginator.send(interaction)
