"""
jcoin/josecoin.py - main module for josécoin backend

a neat webserver which handles josécoin transfers,
wallets, database connections, authentication, etc
"""
import logging
import asyncio
import decimal

import asyncpg

from sanic import Sanic
from sanic import response

import config as jconfig
from .manager import TransferManager

app = Sanic()
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TransferError(Exception):
    pass


@app.get('/')
async def index(request):
    return response.text('oof')


@app.get('/api/wallets/<wallet_id:int>')
async def get_wallet(request, wallet_id):
    wallet = await request.app.db.fetchrow("""
    SELECT account_id, account_type, amount,
     taxpaid, steal_uses, steal_success FROM wallets

    JOIN accounts
      ON accounts.account_id = wallets.user_id

    WHERE user_id = $1
    """, wallet_id)

    if not wallet:
        return response.json(None)

    dwallet = dict(wallet)
    if wallet['account_type'] == 0:
        return response.json(dwallet)
    else:
        log.info('Stripping down info from taxbank')
        dwallet.pop('taxpaid')
        dwallet.pop('steal_uses')
        dwallet.pop('steal_success')
        return response.json(dwallet)


@app.post('/api/wallets/<wallet_id:int>')
async def create_wallet(request, wallet_id):
    wallet_type = int(request.json['type'])

    res = await request.app.db.execute("""
    INSERT INTO accounts (account_id, account_type)
    VALUES ($1, $2)
    """, wallet_id, wallet_type)

    if wallet_type == 0:
        await request.app.db.execute("""
        INSERT INTO wallets (user_id)
        VALUES ($1)
        """, wallet_id)

    _, _, rows = res.split()
    return response.text(f'Inserted {rows} rows')


@app.post('/api/wallets/<wallet_id:int>/transfer')
async def transfer(request, sender_id):
    """Transfer money between users."""
    receiver_id = int(request.json['receiver'])
    amount = decimal.Decimal(request.json['amount'])

    if receiver_id == sender_id:
        raise TransferError('Account can not transfer to itself')

    if amount < 0.0009:
        raise TransferError('Negative amounts are not allowed')

    accs = await request.app.db.fetchrows("""
    SELECT * FROM accounts
    WHERE account_id=$1 or account_id=$2
    """, sender_id)

    accounts = {a['account_id']: a for a in accs}
    sender = accounts.get('sender_id')
    receiver = accounts.get('receiver_id')

    if not sender:
        raise TransferError('Sender is missing account')

    if not receiver:
        raise TransferError('Receiver is missing account')

    sender_amount = decimal.Decimal(sender['amount'])
    if amount > sender_amount:
        raise TransferError('Not enough funds: {amount} > {sender_amount}')

    # the idea here is that we queue and have a commit task
    # that brings up the queued transactions to postgres
    await app.tx.queue((sender_id, receiver_id, amount))
    return request.json({
        'status': True,
        'message': 'transaction queued',
    })


async def db_init(app):
    app.db = await asyncpg.create_pool(**jconfig.db)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    server = app.create_server(host='0.0.0.0', port=8080)
    loop.create_task(server)
    loop.create_task(db_init(app))
    app.tx = TransferManager(app)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
    except:
        log.exception('stopping')
        loop.close()
