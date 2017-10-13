import decimal
import logging

import discord
from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)

PERCENTAGE_PER_TAXBANK = (0.2 / 100)
TICKET_PRICE = 20


class Lottery(Cog):
    """Weekly lottery.

    The lottery works with you buying a 20JC lottery ticket.
    Every Saturday, a winner is chosen from the people
    who bought a ticket.

    The winner gets 0.2% of money from all taxbanks.
    """
    def __init__(self, bot):
        super().__init__(bot)
        self.ticket_coll = self.config.jose_db['lottery']

    @commands.group(aliases=['l'], invoke_without_command=True)
    async def lottery(self, ctx):
        """Show current lottery state.

        A read 'j!help Lottery' is highly recommended.
        """
        amount = decimal.Decimal(0)
        async for account in self.jcoin.all_accounts('taxbank'):
            amount += PERCENTAGE_PER_TAXBANK * account['amount']

        await ctx.send('Next saturday you have a chance to win: '
                       f'`{amount:.2}JC`')

    @lottery.command()
    async def users(self, ctx):
        """Show the users that are in the current lottery."""
        em = discord.Embed()

        users = []
        async for ticket in self.ticket_coll.find():
            users.append(f'<@{ticket["user_id"]}>')

        em.add_field(name='Users', value='\n'.join(users))
        await ctx.send(embed=em)

    @lottery.command()
    async def enter(self, ctx, amount: decimal.Decimal):
        """Enter the weekly lottery."""
        await ctx.send('not implemented yet')
        # Check if the user is in jose guild
        # Pay 20jc to jose
        # put user in ticket collection
        # send message to #lottery-log


def setup(bot):
    bot.add_cog(Lottery(bot))
