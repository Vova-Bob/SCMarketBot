from aiohttp import web


def create_api(bot):
    routes = web.RouteTableDef()

    @routes.post('/order_placed')
    async def order_placed(request: web.Request):
        body = await request.json()

        return web.json_response(
            data=dict(
                result=await bot.create_thread(
                    body.get('server_id'),
                    body.get('channel_id'),
                    body.get('members'),
                    body.get('order'),
                )
            )
        )

    @routes.post('/order_assigned')
    async def order_assigned(request: web.Request):
        body = await request.json()

        return web.json_response(
            data=dict(
                result=await bot.add_to_thread(
                    body.get('server_id'),
                    body.get('thread_id'),
                    body.get('members'),
                    body.get('order'),
                )
            )
        )

    @routes.post('/order_status_updated')
    async def order_placed(request: web.Request):
        body = await request.json()

        return web.json_response(
            data=dict(
                result=await bot.order_status_update(
                    body.get('order'),
                )
            )
        )

    app = web.Application()
    app.add_routes(routes)

    return app
