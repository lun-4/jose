import logging

import discord
from discord.ext import commands

from .common import Cog, CoinConverter

log = logging.getLogger(__name__)


class TransferError(Exception):
    pass


class AccountType:
    USER = 0
    TAXBANK = 1


class Coins3(Cog):
    """Version 3 of JoséCoin.

    NOTE: this is incomplete
    """
    def __init__(self, bot):
        super().__init__(bot)

    async def jc_get(self, route, payload):
        pass

    async def jc_post(self, route, payload):
        """Calls a route with POST.

        Can raise errors.
        """
        pass

    async def create_wallet(self, thing):
        """Send a request to create a JoséCoin account."""
        acc_type = AccountType.USER if isinstance(thing, discord.User) else \
            AccountType.TAXBANK

        await self.jc_post('/create', {
            'id': thing.id,
            'type': acc_type,
        })

    @commands.command()
    async def account(self, ctx):
        """Create a JoséCoin wallet."""
        await self.create_wallet(ctx.author)

    @commands.command()
    async def wallet(self, ctx, person: discord.User=None):
        if not person:
            person = ctx.author

        account = await self.jc_get('/wallet', {
            'id': person.id
        })

        await ctx.send(f'`{self.get_name(person.id)}` > '
                       f'`{account["amount"]}`, paid '
                       f'`{account["taxpaid"]}JC` as tax.')

    @commands.command(name='transfer')
    async def _transfer(self, ctx, person: discord.User,
                        amount: CoinConverter):

        await self.jc_post('/transfer', {
            'from': ctx.author.id,
            'to': person.id,
            'amount': amount,
        })
