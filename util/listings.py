import datetime

import discord
import humanize

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
    embed = discord.Embed(url=f"https://sc-market.space/market/{listing['listing']['listing_id']}", title=listing['details']['title'])
    embed.add_field(name="Item Type", value=listing['details']['item_type'].capitalize())
    embed.add_field(name="Price", value=f"{int(listing['listing']['price']):,} aUEC")
    seller = listing['listing'].get('contractor_seller', listing['listing'].get('user_seller', None))
    embed.add_field(
        name="Seller",
        value=f"[{seller['name']}]({'https://sc-market.space/contractor/' + seller['spectrum_id'] if listing['listing']['contractor_seller'] else 'https://sc-market.space/user/' + seller['username']}) {'⭐' * int(round(seller['rating']['avg_rating'] / 10))}"
    )

    if listing.get('auction_details') and listing['auction_details']['auction_end_time'] is not None:
        date = datetime.datetime.strptime(listing['auction_details']['auction_end_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        embed.add_field(name="Auction End", value="Ending " + humanize.naturaltime(date))

    embed.add_field(name="Quantity Available", value=f"{int(listing['listing']['quantity_available']):,}")

    embed.set_image(url=listing['photos'][0] if listing['photos'] else "https://cdn.robertsspaceindustries.com/static/images/Temp/default-image.png")
    embed.timestamp = datetime.datetime.strptime(listing['listing']['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

    return embed