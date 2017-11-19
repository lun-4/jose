"""
jcoin/josecoin.py - josecoin meme module

a webserver that makes transactions between users and stuff
"""
import logging
import asyncio

import asyncpg

from sanic import Sanic
from sanic import response

import config as jconfig

app = Sanic()
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


@app.get('/')
async def index(request):
    return response.text('oof')


@app.get('/api/wallets/<wallet_id:int>')
async def get_wallet(request, wallet_id):
    wallet = await request.app.db.fetchrow("""
    SELECT * FROM wallets
    WHERE wallet_id = $1

    JOIN accounts
      ON accounts.id = wallets.id AND accounts.account_type = 0
    """, wallet_id)

    return response.json(dict(wallet))


@app.post('/api/wallets/<wallet_id:int>')
async def create_wallet(request, wallet_id):
    wallet_type = int(request.json['type'])

    res = await request.app.db.execute("""
    INSERT INTO accounts (account_id, account_type)
    VALUES ($1, $2)
    """, wallet_id, wallet_type)

    _, _, rows = res.split()
    return response.text(f'Inserted {rows} rows')


async def db_init(app):
    app.db = await asyncpg.create_pool(**jconfig.db)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    server = app.create_server(host='0.0.0.0', port=8080)
    loop.create_task(server)
    loop.create_task(db_init(app))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
    except:
        log.exception('stopping')
        loop.close()
