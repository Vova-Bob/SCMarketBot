import aiohttp

from cogs.registration import DISCORD_BACKEND_URL


async def public_fetch(url, params=None, session=None, return_type=dict):
    tempsession = None
    try:
        if session is None:
            tempsession = aiohttp.ClientSession()
        else:
            tempsession = session

        async with tempsession.get(
                f"https://api.sc-market.space/api{url}",
                params=params
        ) as resp:
            if resp.status // 100 != 2:
                return return_type()
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

        async with tempsession.get(
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

        async with tempsession.post(
                f"{DISCORD_BACKEND_URL}{url}",
                params=params,
                json=json,
        ) as resp:
            return await resp.json()
    finally:
        if session is None and tempsession is not None:
            await tempsession.close()


async def get_user_orders(discord_id, session=None):
    response = await internal_fetch(f"/threads/user/{discord_id}/assigned", session=session)
    return response['orders'] if 'orders' in response else response


async def get_user_listings(discord_id, session=None):
    response = await internal_fetch(f"/threads/user/{discord_id}/listings", session=session)
    return response['listings'] if 'listings' in response else response


async def get_org_listings(contractor_id, discord_id, session=None):
    response = await internal_fetch(f"/threads/user/{discord_id}/listings/{contractor_id}", session=session)
    return response['listings'] if 'listings' in response else response


async def get_user_orgs(discord_id, session=None):
    response = await internal_fetch(f"/threads/user/{discord_id}/contractors", session=session)
    return response['contractors'] if 'contractors' in response else response


async def search_users(query, session=None):
    response = await public_fetch(f"/profile/search/{query}", session=session, return_type=list)
    return response if isinstance(response, list) else []


async def search_orgs(query, session=None):
    response = await public_fetch(f"/contractors", params=dict(query=query, sorting='name'), session=session)
    return response.get('items', []) if isinstance(response, dict) else []
