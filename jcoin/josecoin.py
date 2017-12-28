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
from errors import GenericError, AccountNotFoundError, \
        InputError, ConditionError

app = Sanic()
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class AccountType:
    """Account types."""
    USER = 0
    TAXBANK = 1


# Exception handling
@app.exception(GenericError)
def handle_generic_error(request, exception):
    """Handle generic errors from JoséCoin API"""
    return response.json({
        'error': True,
        'message': exception.args[0]
    }, status=exception.status_code)


@app.get('/')
async def index(request):
    """Give simple index page."""
    return response.text('oof')


@app.get('/api/wallets/<account_id:int>')
async def get_wallet(request, account_id):
    """Get a single wallet.

    Can be user or taxbank.
    """
    account = await request.app.db.fetchrow("""
    SELECT account_id, account_type, amount
    FROM accounts
    WHERE account_id = $1
    """, account_id)

    if not account:
        raise AccountNotFoundError('Account not found')

    daccount = dict(account)
    if account['account_type'] == AccountType.USER:
        wallet = await request.app.db.fetchrow("""
        SELECT taxpaid, steal_uses, steal_success
        FROM wallets
        WHERE user_id=$1
        """, account_id)

        daccount.update(dict(wallet))
        return response.json(daccount)

    return response.json(daccount)


@app.post('/api/wallets/<account_id:int>')
async def create_account(request, account_id):
    """Create a single account.

    Can be user or taxbank.
    """
    log.info('create %d', account_id)
    account_type = int(request.json['type'])

    res = await request.app.db.execute("""
    INSERT INTO accounts (account_id, account_type)
    VALUES ($1, $2)
    """, account_id, account_type)

    if account_type == 0:
        await request.app.db.execute("""
        INSERT INTO wallets (user_id)
        VALUES ($1)
        """, account_id)

    _, _, rows = res.split()
    return response.json({'inserted': rows})


@app.post('/api/wallets/<sender_id:int>/transfer')
async def transfer(request, sender_id):
    """Transfer money between users."""
    receiver_id = int(request.json['receiver'])
    amount = decimal.Decimal(request.json['amount'])

    if receiver_id == sender_id:
        raise InputError('Account can not transfer to itself')

    if amount < 0.0009:
        raise InputError('Negative amounts are not allowed')

    accs = await request.app.db.fetch("""
    SELECT * FROM accounts
    WHERE account_id=$1 or account_id=$2
    """, sender_id, receiver_id)

    accounts = {a['account_id']: a for a in accs}
    log.debug(accounts)

    sender = accounts.get(sender_id)
    receiver = accounts.get(receiver_id)

    if not sender:
        raise AccountNotFoundError('Sender is missing account')

    if not receiver:
        raise AccountNotFoundError('Receiver is missing account')

    sender_amount = decimal.Decimal(sender['amount'])
    if amount > sender_amount:
        raise ConditionError(f'Not enough funds: {amount} > {sender_amount}')

    async with request.app.db.acquire() as conn, conn.transaction():
        # send it back to db
        await conn.execute("""
            UPDATE accounts
            SET amount=accounts.amount - $1
            WHERE account_id = $2
        """, amount, sender_id)

        await conn.execute("""
            UPDATE accounts
            SET amount=accounts.amount + $1
            WHERE account_id = $2
        """, amount, receiver_id)

        # log transaction
        await conn.execute("""
            INSERT INTO transactions (sender, receiver, amount)
            VALUES ($1, $2, $3)
        """, sender_id, receiver_id, amount)

    return response.json({
        'sender_amount': sender_amount - amount,
        'receiver_amount': receiver['amount'] + amount
    })


@app.post('/api/wallets/<wallet_id:int>/steal_use')
async def inc_steal_use(request, wallet_id: int):
    """Increment a wallet's `steal_uses` field by one."""
    async with request.app.db.acquire() as conn, conn.transaction():
        res = await conn.execute("""
        UPDATE wallets
        SET steal_uses = steal_uses + 1
        WHERE user_id=$1
        """, wallet_id)

        _, items = res.split()
        items = int(items)
        return response.json({
            'success': bool(items),
        })


@app.post('/api/wallets/<wallet_id:int>/steal_success')
async def inc_steal_success(request, wallet_id: int):
    """Increment a wallet's `steal_success` field by one."""
    async with request.app.db.acquire() as conn, conn.transaction():
        res = await conn.execute("""
        UPDATE wallets
        SET steal_success = steal_success + 1
        WHERE user_id=$1
        """, wallet_id)

        _, items = res.split()
        items = int(items)
        return response.json({
            'success': bool(items),
        })


@app.get('/api/wallets/<wallet_id:int>/rank')
async def wallet_rank(request, wallet_id: int):
    """Caulculate the ranks of a wallet.

    Returns more data if a guild id is provided
    in the `guild_id` field, as json.
    """
    try:
        guild_id = request.json.get('guild_id')
    except AttributeError:
        guild_id = None

    global_total = await request.app.db.fetchrow("""
    SELECT COUNT(*) FROM accounts
    """)

    global_total = global_total['count']

    global_rank = await request.app.db.fetchrow("""
    SELECT s.rank FROM (
        SELECT accounts.account_id, rank() over (
            ORDER BY accounts.amount DESC
        ) FROM accounts
    ) AS s WHERE s.account_id = $1
    """, wallet_id)

    global_rank = global_rank['rank']

    res = {
        'global': {
            'rank': global_rank,
            'total': global_total,
        }
    }

    if guild_id:
        local_total = await request.app.db.fetchrow("""
        SELECT COUNT(*) FROM accounts
        JOIN members ON accounts.account_id = members.user_id
        WHERE members.guild_id = $1
        """, guild_id)

        local_total = local_total['count']

        local_rank = await request.app.db.fetchrow("""
        SELECT s.rank FROM (
            SELECT accounts.account_id, rank() over (
                ORDER BY accounts.amount DESC
            ) FROM accounts
            JOIN members ON accounts.account_id = members.user_id
            WHERE members.guild_id = $1
        ) AS s WHERE s.account_id = $2
        """, guild_id, wallet_id)
        local_rank = local_rank['rank']

        res['local'] = {
            'rank': local_rank,
            'total': local_total,
        }

    return response.json(res)


async def getsum(request, acc_type: int) -> decimal.Decimal:
    """Get the sum of all the amounts of a
    specific account type."""

    resp = await request.app.db.fetchrow("""
    SELECT SUM(amount) FROM accounts WHERE account_type=$1
    """, acc_type)
    return resp['sum']

async def get_count(request, acc_type: int) -> int:
    """Get the total account count for a specific
    account type."""
    resp = await request.app.db.fetchrow("""
    SELECT COUNT(*) FROM accounts WHERE account_type=$1
    """, acc_type)
    return resp['count']


async def get_gdp(request):
    """Get the GDP (sum of all account amounts) in the economy"""
    resp = await request.app.db.fetchrow("""
    SELECT SUM(amount) FROM accounts;
    """)
    return resp['sum']


async def get_counts(request) -> dict:
    """Get account counts"""

    # TODO: add idx and use MAX(idx) instead of COUNT(*)

    count = await request.app.db.fetchrow("""
    SELECT COUNT(*) FROM accounts
    """)
    count = count['count']

    usercount = await get_count(request, AccountType.USER)
    txbcount = await get_count(request, AccountType.TAXBANK)

    return {
        'accounts': count,
        'user_accounts': usercount,
        'txb_accounts': txbcount,
    }


async def get_sums(request) -> dict:
    """Get sum information about accounts."""
    total_amount = await get_gdp(request)
    user_amount = await getsum(request, AccountType.USER)
    txb_amount = await getsum(request, AccountType.TAXBANK)

    return {
        'gdp': total_amount,
        'user': user_amount,
        'taxbank': txb_amount
    }


@app.get('/api/gdp')
async def get_gdp_handler(request):
    """Get the total amount of coins in the economy."""
    return response.json(await get_sums(request))


@app.get('/api/stats')
async def get_stats_handler(request):
    """Get stats about it all."""

    gdp_data = await get_sums(request)
    res = {
        'gdp': gdp_data['gdp'],
    }

    res.update(await get_counts(request))

    res['user_money'] = gdp_data['user']
    res['txb_money'] = gdp_data['taxbank']

    steal_uses = await request.app.db.fetchrow("""
    SELECT SUM(steal_uses) FROM wallets;
    """)
    steal_uses = steal_uses['sum']

    steal_success = await request.app.db.fetchrow("""
    SELECT SUM(steal_success) FROM wallets;
    """)
    steal_success = steal_success['sum']

    res['steals'] = steal_uses
    res['success'] = steal_success

    return response.json(res)


async def db_init(app):
    """Initialize database"""
    app.db = await asyncpg.create_pool(**jconfig.db)


def main():
    """Main entrypoint."""
    loop = asyncio.get_event_loop()

    server = app.create_server(host='0.0.0.0', port=8080)
    loop.create_task(server)
    loop.create_task(db_init(app))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
    except Exception:
        log.exception('stopping')
        loop.close()


if __name__ == '__main__':
    main()
