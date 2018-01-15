import logging
import datetime

import discord
from discord.ext import commands

from .common import Cog, CoinConverter
from .utils import Table
from .coins2 import AccountType

log = logging.getLogger(__name__)

# 6 hours in jail by default
# 9 hours for point regen
DEFAULT_ARREST = 6
DEFAULT_REGEN = 9


class CooldownTypes:
    prison = 0
    points = 1


class CooldownError(Exception):
    pass


class CoinsExt2(Cog, requires=['coins2']):
    @property
    def coins2(self):
        return self.bot.get_cog('Coins2')

    async def show(self, ctx, accounts, *, field='amount', limit=10):
        """Show a list of accounts"""
        filtered = []

        for idx, account in enumerate(accounts):
            name = self.jcoin.get_name(account['account_id'], account=account)

            if 'Unfindable' in name:
                continue
            else:
                account['_name'] = name
                filtered.append(account)

            if len(filtered) == limit:
                break

        table = Table('pos', 'name', 'account id', field)
        for idx, account in enumerate(filtered):
            table.add_row(str(idx + 1), account['_name'],
                          str(account['account_id']), str(account[field]))

        rendered = await table.render(loop=self.loop)

        if len(rendered) > 1993:
            await ctx.send(f'very big cant show: {len(rendered)}')
        else:
            await ctx.send(f'```\n{rendered}```')

    @commands.command()
    async def jc3top(self, ctx, mode: str='g', limit: int=10):
        """Show accounts by specific criteria.

        'global' means all accounts in josé.
        'local' means the accounts in the server/guild.

        modes:
        - g: global accounts ordered by amount.
        - l: local accounts ordered by amount.
        - t: tax, global accounts ordered by tax paid.
        - b: taxbanks, all taxbanks ordered by amount

        - p: global poorest.
        - lp: local poorest.
        """
        if limit > 30 or limit < 1:
            raise self.SayException('invalid limit')

        if mode == 'g':
            accounts = await self.coins2.jc_get('/wallets', {
                'key': 'global',
                'reverse': True,
                'type': AccountType.USER,
                'limit': limit,
            })
        elif mode == 'l':
            accounts = await self.coins2.jc_get('/wallets', {
                'key': 'local',
                'guild_id': ctx.guild.id,
                'reverse': True,
                'limit': 'limit'
            })
        elif mode == 't':
            accounts = await self.coins2.jc_get('/wallets', {
                'key': 'taxpaid',
                'reverse': True,
                'limit': limit,
            })
        elif mode == 'b':
            accounts = await self.coins2.jc_get('/wallets', {
                'key': 'taxbanks',
                'reverse': True,
                'limit': limit,
            })
        elif mode == 'p':
            accounts = await self.coins2.jc_get('/wallets', {
                'key': 'global',
                'type': AccountType.USER,
                'limit': limit,
            })
        elif mode == 'lp':
            accounts = await self.coins2.jc_get('/wallets', {
                'key': 'local',
                'guild_id': ctx.guild.id,
                'limit': limit,
            })
        else:
            raise self.SayException('mode not found')

        await self.show(ctx, accounts)

    @commands.command(name='jc3prices')
    async def _prices(self, ctx):
        raise NotImplementedError('not implemented')

    @commands.command(name='jc3taxes')
    @commands.guild_only()
    async def taxes(self, ctx):
        await self.coins2.ensure_taxbank(ctx)
        acc = await self.coins2.get_account(ctx.guild.id)
        await ctx.send(f'`{self.coins2.get_name(ctx.guild)}: {acc["amount"]}`')

    async def add_cooldown(self, user, c_type=0,
                           hours: int=DEFAULT_ARREST) -> int:
        """Add a steal cooldown to a user.
        """

        c_type = 'prison' if c_type == 0 else 'points'
        await self.pool.execute(f"""
        INSERT INTO steal_cooldown (user_id, ctype, finish)
        VALUES ($1, $2, now() + interval '{hours} hours')
        """, user.id, c_type)

    async def remove_cooldown(self, user, c_type: CooldownTypes):
        """Remove a cooldown from a user.
        
        This resets the user's steal points if we are
        removing a type 1 cooldown.
        """
        user_id = user.id
        _ctype = 'points' if c_type == CooldownTypes.points else 'prison'
        res = await self.pool.execute("""
        DELETE FROM steal_cooldown
        WHERE user_id=$1 AND ctype=$2
        """, user_id, _ctype)

        _, deleted = res.split()
        deleted = int(deleted)
        if deleted and c_type == CooldownTypes.points:
            await self.pool.execute("""
            UPDATE steal_points
            SET points=3
            WHERE user_id=$1
            """, user_id)

    async def check_cooldowns(self, thief):
        """Check if the current thief is with its cooldowns
        checked up.
        """
        now = datetime.datetime.utcnow()
        cooldowns = await self.pool.fetch("""
        SELECT * FROM steal_cooldown
        WHERE user_id=$1
        """, thief.id)

        for cooldown in cooldowns:
            c_type, c_finish = cooldown['ctype'], cooldown['finish']
            if now >= c_finish:
                await self.remove_cooldown(thief.id, c_type)
                continue

            # in the case the cooldown isnt finished
            remaining = c_finish - now
            if c_type == 'prison':
                raise self.SayException('\N{POLICE CAR} You are still in '
                                        f'prison, wait {remaining} hours')

            elif c_type == 'points':
                raise self.SayException('\N{DIAMOND SHAPE WITH A DOT INSIDE}'
                                        ' You are waiting for steal points.'
                                        f'Wait {remaining} hours')

    async def check_grace(self, target: discord.User):
        """Check if the target is in grace period."""
        pass

    async def check_points(self, ctx):
        """Check if current thief has enough steal points,
        decrement 1 from them if thief has enough,
        puts cooldown if it reaches 0."""
        pass

    async def add_grace(self, target, hours):
        """Add a grace period to the target."""
        pass

    async def arrest(self, ctx, amount):
        """Arrest the thief."""
        pass

    @commands.command(name='jc3steal')
    @commands.guild_only()
    async def steal(self, ctx, target: discord.User, *, amount: CoinConverter):
        pass

    @commands.command(name='jc3stealstate', aliases=['jc3stealstatus'])
    async def stealstate(self, ctx):
        pass

    @commands.command(name='jc3stealreset')
    @commands.is_owner()
    async def stealreset(self, ctx, *people: discord.User):
        pass

def setup(bot):
    bot.add_jose_cog(CoinsExt2)
