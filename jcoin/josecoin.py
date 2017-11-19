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
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def index(request):
    return request.Response('oof')


async def get_wallet(request):
    wallet_id = int(request.match_dict['wallet_id'])

    wallet = await request.app.db.fetchrow("""
    SELECT * FROM wallets
    WHERE wallet_id = $1

    JOIN accounts
      ON accounts.id = wallets.id AND accounts.account_type = 0
    """, wallet_id)

    return request.Response(json=dict(wallet))


async def create_wallet(request):
    wallet_id = int(request.match_dict['wallet_id'])
    wallet_type = int(request.json['type'])

    res = await request.app.db.execute("""
    INSERT INTO accounts (account_id, account_type)
    VALUES ($1, $2)
    """, wallet_id, wallet_type)

    _, _, rows = res.split()
    return request.Response(text=f'Inserted {rows} rows')


async def db_init(app):
    app.db = await asyncpg.create_pool(**jconfig.db)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    r = app.router
    r.add_route('/', index)
    r.add_route('/api/wallets/{wallet_id}', get_wallet, 'GET')
    r.add_route('/api/wallets/{wallet_id}', create_wallet, 'POST')

    app.loop.create_task(db_init(app))
    app.run(debug=True)
