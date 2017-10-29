import logging

import discord
from discord.ext import commands

from .common import Cog, CoinConverter

log = logging.getLogger(__name__)


class TransferError(Exception):
    pass


class PostError(Exception):
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

    def get_name(self, user_id, account=None):
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
                if account['type'] == AccountType.USER:
                    return f'Unfindable User {user_id}'
                elif account['type'] == AccountType.TAXBANK:
                    return f'Unfindable Guild {user_id}'
                else:
                    return f'Unfindable Unknown {user_id}'
            else:
                return f'Unfindable ID {user_id}'

        return str(obj)

    async def create_wallet(self, thing):
        """Send a request to create a JoséCoin account."""
        acc_type = AccountType.USER if isinstance(thing, discord.User) else \
            AccountType.TAXBANK

        await self.jc_post('/create', {
            'id': thing.id,
            'type': acc_type,
        })

        log.info('Created account for %r[%d]', thing, thing.id)

    async def ensure_taxbank(self, ctx):
        """Ensure a taxbank exists for the guild."""
        if ctx.guild is None:
            raise self.SayException('You cannot do this in a DM.')

        acc = await self.get_account(ctx.guild.id)
        if acc:
            return

        await self.create_wallet(ctx.guild)

    @commands.command()
    async def account(self, ctx):
        """Create a JoséCoin wallet."""
        try:
            await self.ensure_taxbank(ctx)
            await self.create_wallet(ctx.author)
            await ctx.ok()
        except PostError as err:
            await ctx.not_ok()
            await ctx.send(f':x: `{err.message}`')

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
