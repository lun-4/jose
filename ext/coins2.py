import logging
import asyncio
import decimal
import sys
import pprint

import discord
from discord.ext import commands

from .common import Cog, CoinConverter
from .utils import Timer

sys.path.append('..')
from jcoin.errors import GenericError, AccountNotFoundError, \
        InputError, ConditionError, err_list

log = logging.getLogger(__name__)


class TransferError(Exception):
    """Represents a generic transfer error."""
    pass


class PostError(Exception):
    """Represents a generic POST error to the API."""
    pass


class AccountType:
    """Account types."""
    USER = 0
    TAXBANK = 1


class Coins2(Cog):
    """Version 3 of JoséCoin.

    NOTE: this is incomplete
    """
    def __init__(self, bot):
        super().__init__(bot)
        self.base_url = bot.config.JOSECOIN_API
        self.bot.simple_exc.extend(err_list)

    def route(self, route):
        return f'{self.base_url}{route}'

    async def generic_call(self, method: str, route: str,
                           payload: dict = None) -> 'any':
        """Generic call to any JoséCoin API route."""
        route = self.route(route)
        async with self.bot.session.request(method, route, json=payload) as r:
            log.info('calling %s, status code %d', route, r.status)

            if r.status == 500:
                raise Exception('Internal Server Error')

            p = await r.json()
            if p.get('error'):
                for exc in err_list:
                    if exc.status_code == r.status:
                        raise exc(p['message'])
            return p

    async def jc_get(self, route: str, payload: dict = None) -> 'any':
        """Make a GET request to JoséCoin API."""
        return await self.generic_call('GET', route, payload)

    async def jc_post(self, route: str, payload: dict = None) -> 'any':
        """Calls a route with POST."""
        return await self.generic_call('POST', route, payload)

    async def jc_delete(self, route: str, payload: dict=None) -> 'any':
        """Calls a route with DELETE."""
        return await self.generic_call('DELETE', route, payload)

    def get_name(self, user_id: int, account=None):
        """Get a string representation of a user or guild.

        Parameters
        ----------
        user_id: int
            User ID to get a string representation of.
        account: dict, optional
            Account object to determine if this is
            A user or a guild to search.

        Returns
        -------
        str
        """
        if isinstance(user_id, discord.Guild):
            return f'taxbank:{user_id.name}'
        elif isinstance(user_id, discord.User):
            return str(user_id)

        obj = self.bot.get_user(int(user_id))

        if not obj:
            # try to find guild
            obj = self.bot.get_guild(user_id)
            if obj:
                obj = f'taxbank:{obj}'

        if not obj:
            # we tried stuff, show a special text
            if account:
                res = ''
                if account['type'] == AccountType.USER:
                    res = f'Unfindable User {user_id}'
                elif account['type'] == AccountType.TAXBANK:
                    res = f'Unfindable Guild {user_id}'
                else:
                    res = f'Unfindable Unknown {user_id}'
                return res
            else:
                return f'Unfindable ID {user_id}'

        return str(obj)

    async def get_account(self, wallet_id: int) -> dict:
        """Get an account"""
        r = await self.jc_get(f'/wallets/{wallet_id}')
        r['amount'] = decimal.Decimal(r['amount'])
        try:
            r['taxpaid'] = decimal.Decimal(r['taxpaid'])
        except:
            pass
        return r

    async def create_wallet(self, thing):
        """Send a request to create a JoséCoin account."""

        log.info('Creating account for %r', thing)
        acc_type = AccountType.USER if isinstance(thing, discord.abc.User) else \
            AccountType.TAXBANK

        rows = await self.jc_post(f'/wallets/{thing.id}', {
            'type': acc_type,
        })

        if rows:
            log.info('Created account for %r[%d]', thing, thing.id)

        return rows

    async def ensure_ctx(self, ctx):
        try:
            await self.create_wallet(ctx.bot.user, 'NaN')
        except:
            pass

    async def get_ranks(self, account_id: int, guild_id=None) -> dict:
        rank_data = await self.jc_get(f'/wallets/{account_id}/rank', {
            'guild_id': guild_id
        })
        return rank_data

    async def transfer(self, from_id: int, to_id: int,
                       amount: decimal.Decimal) -> dict:
        """Make the transfer call"""
        return await self.jc_post(f'/wallets/{from_id}/transfer', {
            'receiver': to_id,
            'amount': str(amount)
        })

    async def ensure_taxbank(self, ctx):
        """Ensure a taxbank exists for the guild."""
        if ctx.guild is None:
            raise self.SayException('You cannot do this in a DM.')

        try:
            await self.get_account(ctx.guild.id)
            return
        except AccountNotFoundError:
            await self.create_wallet(ctx.guild)

    @commands.group(hidden=True)
    async def jc3(self, ctx):
        """Main command group for JoséCoin v3 commands.

        NOTE: this should be REMOVED once JoséCoin v3 becomes stable.
        """
        pass

    @jc3.command()
    async def account(self, ctx):
        """Create a JoséCoin wallet."""
        try:
            await self.ensure_taxbank(ctx)
            await self.get_account(ctx.author.id)
            return await ctx.send('You already have an account.')
        except AccountNotFoundError:
            await self.create_wallet(ctx.author)
            await ctx.ok()
        except Exception as err:
            await ctx.not_ok()
            await ctx.send(f':x: `{err!r}`')

    @jc3.command()
    async def wallet(self, ctx, person: discord.User = None):
        """Check your wallet details."""
        if not person:
            person = ctx.author

        account = await self.get_account(person.id)

        await ctx.send(f'`{self.get_name(person.id)}` > '
                       f'`{account["amount"]}`, paid '
                       f'`{account["taxpaid"]}JC` as tax.')

    @jc3.command(name='transfer')
    async def _transfer(self, ctx,
                        receiver: discord.User, amount: CoinConverter):
        """Transfer coins between you and someone else."""
        if receiver.bot:
            raise self.SayException('Receiver can not be a bot')

        await self.transfer(ctx.author.id, receiver.id, amount)
        await ctx.send(f'\N{MONEY WITH WINGS} {ctx.author!s} > '
                       f'`{amount}JC` > {receiver!s} \N{MONEY BAG}')

    @jc3.command()
    async def donate(self, ctx, amount: CoinConverter):
        """Donate to the guild's taxbank."""
        await self.transfer(ctx.author.id, ctx.guild.id, amount)
        await ctx.ok()

    @jc3.command()
    @commands.guild_only()
    async def ranks(self, ctx):
        """Get rank data."""
        res = await self.get_ranks(ctx.author.id, ctx.guild.id)
        await ctx.send(res)

    @jc3.command()
    async def ping(self, ctx):
        """Check if the JoséCoin API is up."""
        with Timer() as timer:
            try:
                res = await self.jc_get('/health')
                up = res['status']
                if not up:
                    return await ctx.send('JoséCoin API is not ok.')
            except:
                return await ctx.send('Failed to contact the JoséCoin API')

        await ctx.send(f'`{timer}`')

    @jc3.command()
    @commands.is_owner()
    async def migrate(self, ctx):
        """Migrate JoséCoin data from Mongo -> Postgres"""
        await ctx.send('migrating shit')
        cur = self.jcoin.jcoin_coll.find()
        db = self.bot.get_cog("Config").db

        async with db.acquire() as conn:
            acc_stmt = await conn.prepare("""
            INSERT INTO accounts (account_id, account_type, amount)
            VALUES ($1, $2, $3)
            """)

            user_stmt = await conn.prepare("""
            INSERT INTO wallets (user_id, taxpaid, steal_uses, steal_success)
            VALUES ($1, $2, $3, $4)
            """)

            ucount, acount = 0, 0
            async for account in cur:
                atype = account['type']
                acc_da = decimal.Decimal(account['amount'])
                as_int = AccountType.USER if atype == 'user' \
                    else AccountType.TAXBANK

                if acc_da.is_infinite():
                    acc_da = decimal.Decimal('NaN')

                await acc_stmt.fetchval(account['id'], as_int, acc_da)
                if as_int == AccountType.USER:
                    acc_dt = decimal.Decimal(account['taxpaid'])
                    await user_stmt.fetchval(account['id'], acc_dt,
                                             account['times_stolen'],
                                             account['success_steal'])
                    ucount += 1
                acount += 1

        await ctx.send(f'Inserted {acount} accounts, {ucount} users')

    @jc3.command()
    async def coinprob(self, ctx, person: discord.User=None):
        if not person:
            person = ctx.author

        data = await self.jc_get(f'/wallets/{person.id}/probability')
        p = data['probability']
        await ctx.send(f'You have a {p * 100}%/message chance')

    @jc3.command()
    async def jcgetraw(self, ctx):
        """Get raw info on your wallet"""
        wallet = await self.get_account(ctx.author.id)
        res = pprint.pformat(wallet)
        await ctx.send(f'```python\n{res}\n```')

    @jc3.command()
    @commands.is_owner()
    async def write(self, ctx, person: discord.User, amount: str):
        """Overwrite someone's wallet"""
        with Timer() as timer:
            await self.pool.execute("""
            UPDATE accounts
            SET amount=$1
            WHERE account_id=$2
            """, amount, person.id)

        await ctx.send(f'write took {timer}')

    @jc3.command()
    @commands.is_owner()
    async def spam(self, ctx, taskcount: int=200, timeout: int=30):
        """webscale memes
        
        This will spawn an initial amount of [taskcount] tasks,
        with each one doing a transfer call.

        If all tasks complete the operation, we double the amount of tasks.

        If we hit a timeout, this stops.
        """
        while True:
            tasks = []
            with Timer() as timer:
                for i in range(taskcount):
                    coro = self.transfer(ctx.bot.user.id,
                                         ctx.author.id, 0.1)
                    t = self.loop.create_task(coro)
                    tasks.append(t)

            done, pending = await asyncio.wait(tasks, timeout=timeout)
            await ctx.send(f'{taskcount} tasks in {timer}')

            lp = len(pending)
            if lp:
                return await ctx.send(f'stopping from {lp} > 0 pending')

            taskcount *= 2

    @jc3.command()
    async def deleteaccount(self, ctx, confirm: bool=False):
        """Delete your JoséCoin account.
        
        There is no going back from this operation.

        Use "y", "yes", and variants, to confirm it.
        """
        if not confirm:
            return await ctx.send('You did not confirm the operation.')

        log.warning(f'deleting account {ctx.author!r}')

        res = await self.jc_delete(f'/wallets/{ctx.author.id}')
        await ctx.status(res['success'])

    @jc3.command()
    async def hidecoins(self, ctx):
        """Toggle the coin reaction in your account"""
        result = await self.jc_post(f'/wallets/{ctx.author.id}/hidecoins')
        result = result['new_hidecoins']
        resultstr = 'on' if result else 'off'
        await ctx.send(f'no reactions are set to `{resultstr}` for you.')


def setup(bot):
    bot.add_cog(Coins2(bot))
