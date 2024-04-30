import aiohttp

from cogs.registration import DISCORD_BACKEND_URL


async def public_fetch(url, params=None, session=None):
    tempsession = None
    try:
        if session is None:
            tempsession = aiohttp.ClientSession()
        else:
            tempsession = session

        async with session.get(
                f"https://api.sc-market.space/api{url}",
                params=params
        ) as resp:
            return await resp.json()
    finally:
        if session is None and tempsession is not None:
            await tempsession.close()


async def internal_fetch(url, params=None, session=None):
    tempsession = None
    try:
        if session is None:
            tempsession = aiohttp.ClientSession()
        else:
            tempsession = session

        async with session.get(
                f"{DISCORD_BACKEND_URL}{url}",
                params=params
        ) as resp:
            return await resp.json()
    finally:
        if session is None and tempsession is not None:
            await tempsession.close()


async def internal_post(url, params=None, json=None, session=None):
    tempsession = None
    try:
        if session is None:
            tempsession = aiohttp.ClientSession()
        else:
            tempsession = session

        async with session.post(
                f"{DISCORD_BACKEND_URL}{url}",
                params=params,
                json=json,
        ) as resp:
            return await resp.json()
    finally:
        if session is None and tempsession is not None:
            await tempsession.close()


async def get_users_orders(discord_id, session=None):
    response = await internal_fetch(f"/threads/user/{discord_id}/assigned", session=session)
    return response['orders'] if 'orders' in response else response
