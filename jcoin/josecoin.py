"""
jcoin/josecoin.py - josecoin meme module

a webserver that makes transactions between users and stuff
"""
import logging
import asyncio

from japronto import Application

app = Application()
log = logging.getLogger(__name__)


class AccountType:
    USER = 0
    TAXBANK = 1


async def index(request):
    return request.Response('oof')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    r = app.router
    r.add_route('/', index)

    app.run(debug=True)
