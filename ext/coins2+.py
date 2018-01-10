from discord.ext import commands

from .common import Cog
from .utils import Table

from .coins2 import AccountType


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
        raise NotImplementedError('not implemented')

    @commands.command(name='jc3deadtxb')
    async def deadtxb(self, ctx):
        raise NotImplementedError('not implemented')


def setup(bot):
    bot.add_jose_cog(CoinsExt2)
