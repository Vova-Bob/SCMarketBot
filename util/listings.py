import datetime
from typing import List

import discord
import humanize
from discord.ext.paginators.button_paginator import ButtonPaginator

from util.iter import chunks

categories = ["Armor", "Clothing", "Weapon", "Paint", "Bundle", "Flair", "Addon", "Consumable", "Other"]
sorting_methods = {
    'title': "Title",
    'price-low': "Price (Low to High)",
    'price-high': "Price (High to Low)",
    'quantity-low': "Quantity Available (Low to High)",
    'quantity-high': "Quantity Available (High to Low)",
    'date-new': "Date Listed (Old to New)",
    'date-old': "Date Listed (New to Old)",
    'activity': "Recent Activity",
    'rating': "Rating (High to Low)",
}

sale_types = ["Aggregate", "Auction", "Sale"]


def create_market_embed(listing: dict):
    embed = discord.Embed(url=f"https://sc-market.space/market/{listing['listing_id']}", title=listing['title'])
    embed.add_field(name="Item Type", value=listing['item_type'].capitalize())
    if listing["listing_type"] != "unique":
        embed.add_field(name="Minimum Price", value=f"{int(listing['minimum_price']):,} aUEC")
        embed.add_field(name="Maximum Price", value=f"{int(listing['maximum_price']):,} aUEC")
    else:
        embed.add_field(name="Price", value=f"{int(listing['price']):,} aUEC")
        embed.add_field(
            name="Seller",
            value=f"[{listing['contractor_seller'] or listing['user_seller']}]({'https://sc-market.space/contractor/' + listing['contractor_seller'] if listing['contractor_seller'] else 'https://sc-market.space/user/' + listing['user_seller']}) {'⭐' * int(round(listing['avg_rating']))}"
        )

    if listing['auction_end_time'] is not None:
        date = datetime.datetime.strptime(listing['auction_end_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        embed.add_field(name="Auction End", value="Ending " + humanize.naturaltime(date))

    embed.add_field(name="Quantity Available", value=f"{int(listing['quantity_available']):,}")

    embed.set_image(url=listing['photo'])
    embed.timestamp = datetime.datetime.strptime(listing['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

    return embed


def create_market_embed_individual(listing: dict):
    embed = discord.Embed(url=f"https://sc-market.space/market/{listing['listing']['listing_id']}",
                          title=listing['details']['title'])
    embed.add_field(name="Item Type", value=listing['details']['item_type'].capitalize())
    embed.add_field(name="Price", value=f"{int(listing['listing']['price']):,} aUEC")
    seller = listing['listing'].get('contractor_seller') or listing['listing'].get('user_seller')
    embed.add_field(
        name="Seller",
        value=f"[{seller.get('name') or seller.get('display_name')}]({'https://sc-market.space/contractor/' + seller['spectrum_id'] if listing['listing'].get('contractor_seller') else 'https://sc-market.space/user/' + seller['username']}) {'⭐' * int(round(seller['rating']['avg_rating'] / 10))}"
    )

    if listing.get('auction_details') and listing['auction_details']['auction_end_time'] is not None:
        date = datetime.datetime.strptime(listing['auction_details']['auction_end_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        embed.add_field(name="Auction End", value="Ending " + humanize.naturaltime(date))

    embed.add_field(name="Quantity Available", value=f"{int(listing['listing']['quantity_available']):,}")

    embed.set_image(url=listing['photos'][0] if listing[
        'photos'] else "https://cdn.robertsspaceindustries.com/static/images/Temp/default-image.png")
    embed.timestamp = datetime.datetime.strptime(listing['listing']['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

    return embed


def create_stock_embed(entries: List[str]):
    embed = discord.Embed(url=f"https://sc-market.space/market/manage?quantityAvailable=0",
                          title="My Stock")
    body = '\n'.join(entries)
    embed.description = f"""```ansi\n{body}\n```"""
    embed.timestamp = datetime.datetime.now()

    return embed


async def display_listings_compact(interaction: discord.Interaction, alllistings: list):
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

        header = f"\u001b[4;40;37m {'Qt.':<{mq}} | {'Item':<{tq}} | {'Price':>{pq + 5}} "
        entries.insert(0, header)
        pages.append(entries)

    embeds = [create_stock_embed(page) for page in pages]
    paginator = ButtonPaginator(embeds, author_id=interaction.user.id)
    await paginator.send(interaction)
