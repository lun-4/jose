"""
jcoin/josecoin.py - main module for josécoin backend

a neat webserver which handles josécoin transfers,
wallets, database connections, authentication, etc
"""
import logging
import asyncio
import decimal
import time

import asyncpg

from sanic import Sanic
from sanic import response

import config as jconfig
from errors import GenericError, AccountNotFoundError, \
        InputError, ConditionError


app = Sanic()
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# constants
AUTOCOIN_BASE_PROB = decimal.Decimal('0.012')
PROB_CONSTANT = decimal.Decimal('1.003384590736')

# !!!!! VERY IMPORTANT
ENCODED_INFINITY = -69


def is_inf(decimal):
    return decimal == ENCODED_INFINITY


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
async def index(_):
    """Give simple index page."""
    return response.text('josecoin v3 haha ye')


@app.middleware('request')
async def request_check(request):
    """Check the client token and deny if possible."""
    try:
        token = request.headers['Authorization']
    except KeyError:
        return response.json({
            'error': 'no token provided'
        }, status=403)

    row = await request.app.db.fetchrow("""
    SELECT client_id, client_name, auth_level FROM clients
    WHERE token=$1
    """, token)

    if row is None:
        log.info('token not found')
        return response.json({
            'error': 'unauthorized'
        }, status=403)

    client_id = row['client_id']
    client_name = row['client_name']
    auth_level = row['auth_level']
    log.info(f'id={client_id} name={client_name} level={auth_level}')


@app.get('/api/health')
async def get_status(request) -> response:
    """Simple response."""
    t1 = time.monotonic()
    await request.app.db.fetchrow('SELECT 1')
    t2 = time.monotonic()
    delta = round((t2 - t1), 8)
    return response.json({
        'status': True,
        'db_latency_sec': delta,
    })


@app.get('/api/wallets/<account_id:int>')
async def get_wallet(request, account_id):
    """Get a single wallet.

    Can be user or taxbank.
    """
    account = await request.app.db.fetchrow("""
    SELECT account_id, account_type, amount
    FROM account_amount
    WHERE account_id = $1
    """, account_id)

    if not account:
        raise AccountNotFoundError('Account not found')

    daccount = dict(account)
    if account['account_type'] == AccountType.USER:
        wallet = await request.app.db.fetchrow("""
        SELECT taxpaid, steal_uses, steal_success
        FROM wallets_taxpaid
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

    try:
        res = await request.app.db.execute("""
        INSERT INTO accounts (account_id, account_type)
        VALUES ($1, $2)
        """, account_id, account_type)
    except asyncpg.exceptions.UniqueViolationError:
        raise ConditionError('Account exists')

    if account_type == 0:
        await request.app.db.execute("""
        INSERT INTO wallets (user_id)
        VALUES ($1)
        """, account_id)

    _, _, rows = res.split()
    return response.json({'inserted': rows})


@app.delete('/api/wallets/<account_id:int>')
async def delete_account(request, account_id: int):
    try:
        await request.app.db.execute("""
        DELETE FROM accounts
        WHERE account_id = $1
        """, account_id)

        return response.json({
            'success': True
        })
    except Exception as err:
        log.exception('error while deleting')
        return response.json({
            'success': False,
            'err': repr(err)
        })


@app.post('/api/wallets/<sender_id:int>/transfer')
async def transfer(request, sender_id):
    """Transfer money between users."""
    try:
        receiver_id = int(request.json['receiver'])
        amount = decimal.Decimal(request.json['amount'])
    except:
        raise InputError('Invalid input')

    if receiver_id == sender_id:
        raise InputError('Account can not transfer to itself')

    try:
        amount = round(amount, 3)
    except:
        raise InputError('Error rounding.')

    if amount < 0.01:
        raise InputError('Negative amounts are not allowed')

    # NOTE: this uses the view
    accs = await request.app.db.fetch("""
    SELECT * FROM account_amount
    WHERE account_id=$1 or account_id=$2
    """, sender_id, receiver_id)

    accounts = {a['account_id']: a for a in accs}
    sender = accounts.get(sender_id)
    receiver = accounts.get(receiver_id)

    if not sender:
        raise AccountNotFoundError('Sender is missing account')

    if not receiver:
        raise AccountNotFoundError('Receiver is missing account')

    snd_amount = sender['amount']
    if not is_inf(snd_amount) and amount > snd_amount:
        raise ConditionError(f'Not enough funds: {amount} > {snd_amount}')

    amount = str(amount)
    async with request.app.db.acquire() as conn, conn.transaction():
        # send it back to db
        if not is_inf(snd_amount):
            await conn.execute("""
            UPDATE accounts
            SET amount=accounts.amount - $1
            WHERE account_id = $2
            """, amount, sender_id)

        if receiver['account_type'] == AccountType.TAXBANK and \
                sender['account_type'] == AccountType.USER:
            await conn.execute("""
            UPDATE wallets
            SET taxpaid=wallets.taxpaid + $1
            WHERE user_id=$2
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

    einf = str(ENCODED_INFINITY)
    # yes, we go back and forth.
    amount = float(amount)
    return response.json({
        'sender_amount': einf if is_inf(snd_amount) else snd_amount - amount,
        'receiver_amount': einf if is_inf(receiver['amount']) else receiver['amount'] + amount
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

    if not global_rank:
        raise AccountNotFoundError('Account not found')

    global_rank = global_rank['rank']

    taxes_total = await request.app.db.fetchrow("""
    SELECT COUNT(*) FROM wallets
    """)
    taxes_total = taxes_total['count']

    taxes_rank = await request.app.db.fetchrow("""
    SELECT s.rank FROM (
        SELECT wallets.user_id, rank() over (
            ORDER BY wallets.taxpaid DESC
        ) FROM wallets
    ) AS s WHERE s.user_id = $1
    """, wallet_id)
    taxes_rank = taxes_rank['rank']

    res = {
        'global': {
            'rank': global_rank,
            'total': global_total,
        },
        'taxes': {
            'rank': taxes_rank,
            'total': taxes_total,
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
    SELECT SUM(amount)::numeric FROM accounts WHERE account_type=$1
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
    SELECT SUM(amount)::numeric FROM accounts;
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


@app.get('/api/wallets/<wallet_id:int>/probability')
async def get_wallet_probability(request, wallet_id: int):
    wallet = await request.app.db.fetchrow("""
    SELECT taxpaid FROM wallets_taxpaid
    WHERE user_id=$1
    """, wallet_id)
    if not wallet:
        raise AccountNotFoundError('Wallet not found')
    taxpaid = wallet['taxpaid']

    prob = AUTOCOIN_BASE_PROB

    # Based on the tax paid.
    taxpaid = decimal.Decimal(taxpaid)
    if taxpaid >= 50:
        raised = pow(PROB_CONSTANT, taxpaid)
        prob += round(raised / 100, 5)

    if prob > 0.042:
        prob = 0.042

    return response.json({
        'probability': str(prob),
    })


@app.get('/api/wallets')
async def get_wallets(request):
    """Get wallets by specific criteria"""
    key = request.json['key']
    try:
        reverse = bool(request.json['reverse'])
    except:
        reverse = False

    sorting = 'DESC' if reverse else 'ASC'

    try:
        guild_id = int(request.json['guild_id'])
    except:
        guild_id = None

    try:
        limit = int(request.json['limit'])
    except:
        limit = 20

    try:
        acc_type = int(request.json['type'])
    except:
        acc_type = -1

    if limit <= 0 or limit > 30:
        raise InputError('invalid limit range')

    query = ''

    # very ugly hack
    acc_type_str = {
        AccountType.USER: f'account_amount.account_type={AccountType.USER}',
        AccountType.TAXBANK: 'account_amount.account_type'
                             f'={AccountType.TAXBANK}',
    }.get(acc_type, '')

    acc_type_str_w = ''
    if acc_type_str:
        acc_type_str_w = f'WHERE {acc_type_str}'

    args = [guild_id]

    if key == 'local':
        query = f"""
        SELECT * FROM account_amount

        JOIN members ON account_amount.account_id = members.user_id
        WHERE members.guild_id = $1

        ORDER BY amount {sorting}
        LIMIT {limit}
        """
    elif key == 'global':
        query = f"""
        SELECT * FROM account_amount
        {acc_type_str_w}

        ORDER BY amount {sorting}
        LIMIT {limit}
        """
        args = []
    elif key == 'taxpaid':
        query = f"""
        SELECT * FROM wallets_taxpaid
        JOIN accounts ON account_amount.account_id = wallets_taxpaid.user_id

        ORDER BY taxpaid {sorting}
        LIMIT {limit}
        """
        args = []
    elif key == 'taxbanks':
        query = f"""
        SELECT * FROM account_amount
        WHERE account_type={AccountType.TAXBANK}

        ORDER BY amount {sorting}
        LIMIT {limit}
        """
        args = []
    else:
        return response.json({
            'success': False,
            'status': 'invalid key',
        })

    log.info(query)
    rows = await request.app.db.fetch(query, *args)
    return response.json(map(dict, rows))


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
    SELECT SUM(steal_uses) FROM wallets
    """)
    steal_uses = steal_uses['sum']

    steal_success = await request.app.db.fetchrow("""
    SELECT SUM(steal_success) FROM wallets;
    """)
    steal_success = steal_success['sum']

    res['steals'] = steal_uses
    res['success'] = steal_success

    return response.json(res)


@app.post('/api/wallets/<user_id:int>/hidecoins')
async def toggle_hidecoins(request, user_id: int):
    async with request.app.db.acquire() as conn, conn.transaction():
        await conn.execute("""
        UPDATE wallets
        SET hidecoins = not hidecoins
        WHERE user_id = $1
        """, user_id)

        new_hidecoins = await conn.fetchrow("""
        SELECT hidecoins FROM wallets
        WHERE user_id = $1
        """, user_id)
        if not new_hidecoins:
            raise AccountNotFoundError('Account not found')

        return response.json({
            'new_hidecoins': new_hidecoins['hidecoins']
        })


@app.get('/api/wallets/<user_id:int>/hidecoin_status')
async def hidecoin_status(request, user_id: int):
    hidecoins = await request.app.db.fetchrow("""
    SELECT hidecoins FROM wallets
    WHERE user_id = $1
    """, user_id)
    if not hidecoins:
        raise AccountNotFoundError('Account not found')

    return response.json({
        'hidden': hidecoins['hidecoins']
    })


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
