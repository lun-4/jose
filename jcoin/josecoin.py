"""
jcoin/josecoin.py - josecoin meme module

a webserver that makes transactions between users and stuff
"""
import logging
import asyncio

import asyncpg
from japronto import Application

import config as jconfig

app = Application()
log = logging.getLogger(__name__)


async def index(request):
    return request.Response('oof')


async def db_init(app):
    app.db = await asyncpg.create_pool(**jconfig.db)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    r = app.router
    r.add_route('/', index)

    app.loop.create_task(db_init(app))
    app.run(debug=True)
