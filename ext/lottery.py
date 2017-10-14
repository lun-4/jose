import logging
import decimal
import asyncio
from random import SystemRandom

import discord
from discord.ext import commands

from .common import Cog

random = SystemRandom()
log = logging.getLogger(__name__)

PERCENTAGE_PER_TAXBANK = decimal.Decimal(0.26 / 100)
TICKET_PRICE = 15


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

        A read on 'j!help Lottery' is highly recommended.
        """
        amount = decimal.Decimal(0)
        async for account in self.jcoin.jcoin_coll.find({'type': 'taxbank'}):
            amount += PERCENTAGE_PER_TAXBANK * \
                      decimal.Decimal(account['amount'])

        await ctx.send('Next saturday you have a chance to win: '
                       f'`{amount:.2}JC`')

    @lottery.command()
    async def users(self, ctx):
        """Show the users that are in the current lottery."""
        em = discord.Embed()

        users = []
        async for ticket in self.ticket_coll.find():
            users.append(f'<@{ticket["user_id"]}>')

        if users:
            em.add_field(name='Users', value=' '.join(users))
        else:
            em.description = 'No users in the current lottery'

        await ctx.send(embed=em)

    @lottery.command()
    @commands.is_owner()
    async def roll(self, ctx):
        """Roll a winner from the pool"""

        joseguild = self.bot.get_guild(self.bot.config.JOSE_GUILD)
        if not joseguild:
            raise self.SayException('`config error`: José guild not found.')

        lottery_log = self.bot.get_channel(self.bot.config.LOTTERY_LOG)
        if not lottery_log:
            raise self.SayException('`config error`: log channel not found.')

        cur = self.ticket_coll.find()

        # !!! bad code !!!
        # this is not WEBSCALE
        all_users = await cur.to_list(length=None)

        winner = random.choice(all_users)
        winner_id = winner['user_id']

        if not any(m.id == ctx.author.id for m in joseguild.members):
            raise self.SayException(f'selected winner, <@{winner_id}> '
                                    'is not in jose guild. ignoring!')

        u_winner = self.bot.get_user(winner_id)
        await lottery_log.send(f'**Winner!** `{u_winner!s}, {u_winner.id}`')

        await ctx.send(f'Winner: <@{winner_id}>, transferring will take time')

        # business logic is here
        total = decimal.Decimal(0)
        async for account in self.jcoin.jcoin_coll.find({'type': 'taxbank'}):
            amount = PERCENTAGE_PER_TAXBANK * \
                     decimal.Decimal(account['amount'])

            if amount < 0.1:
                continue

            try:
                await self.jcoin.transfer(account['id'], winner_id, amount)
                total += amount
            except Exception as err:
                await ctx.send(f'err: {err}')

            await asyncio.sleep(0.2)

        await ctx.send(f'Sent a total of `{total:.2}` to the winner')

        r = await self.ticket_coll.delete_many({})
        await ctx.send(f'Deleted {r.deleted_count} tickets')

    @lottery.command()
    async def enter(self, ctx):
        """Enter the weekly lottery.
        You will pay 20JC for a ticket.
        """
        # Check if the user is in jose guild
        joseguild = self.bot.get_guild(self.bot.config.JOSE_GUILD)
        if not joseguild:
            raise self.SayException('`config error`: José guild not found.')

        lottery_log = self.bot.get_channel(self.bot.config.LOTTERY_LOG)
        if not lottery_log:
            raise self.SayException('`config error`: log channel not found.')

        if ctx.author not in joseguild.members:
            raise self.SayException("You are not in José's server."
                                    'For means of transparency, it is'
                                    'recommended to join it, use '
                                    f'`{ctx.prefix}invite`')

        ticket = await self.ticket_coll.find_one({'user_id':
                                                  ctx.author.id})
        if ticket:
            raise self.SayException('You already bought a ticket.')

        # Pay 20jc to jose
        await self.coins.transfer(ctx.author.id,
                                  self.bot.user.id, TICKET_PRICE)

        await self.ticket_coll.insert_one({'user_id': ctx.author.id})
        await lottery_log.send(f'In lottery: `{ctx.author!s}, {ctx.author.id}`')
        await ctx.ok()


def setup(bot):
    bot.add_cog(Lottery(bot))
