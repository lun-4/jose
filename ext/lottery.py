import logging
import decimal
import asyncio
from random import SystemRandom

import discord
from discord.ext import commands

from .common import Cog

random = SystemRandom()
log = logging.getLogger(__name__)

PERCENTAGE_PER_TAXBANK = decimal.Decimal(0.275 / 100)
TICKET_PRICE = 11
TICKET_INCREASE = decimal.Decimal(65 / 100)
LOTTERY_COOLDOWN = 5


class Lottery(Cog, requires=['coins']):
    """Weekly lottery.

    The lottery works with you buying a 15JC lottery ticket.
    From time to time(maximum a week) a winner is chosen from the people
    who bought a ticket.

    The winner gets 0.275% of money from the top 40 taxbanks.
    This amount also increases with more people buying tickets.
    """

    def __init__(self, bot):
        super().__init__(bot)
        self.ticket_coll = self.config.jose_db['lottery']
        self.cdown_coll = self.config.jose_db['lottery_cooldown']

    async def get_taxbanks(self):
        """Fetch taxbanks for lottery."""
        return await self.coins.jc_get(
            '/wallets', {
                'key': 'global',
                'reverse': True,
                'type': self.coins.AccountType.TAXBANK,
                'limit': 40,
            })

    @commands.group(aliases=['l'], invoke_without_command=True)
    async def lottery(self, ctx):
        """Show current lottery state.

        A read on 'j!help Lottery' is highly recommended.
        """
        amount = decimal.Decimal(0)
        taxbanks = await self.get_taxbanks()
        for account in taxbanks:
            amount += PERCENTAGE_PER_TAXBANK * \
                      decimal.Decimal(account['amount'])

        amount_people = await self.ticket_coll.count()
        amount += TICKET_INCREASE * amount_people * TICKET_PRICE

        amount = round(amount, 2)
        await ctx.send('Calculation of the big money for lottery: '
                       f'`{amount}JC`')

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

    async def lottery_send(self, message: str):
        lottery_log = self.bot.get_channel(self.bot.config.LOTTERY_LOG)
        if not lottery_log:
            raise self.SayException('`config error`: log channel not found.')

        return await lottery_log.send(message)

    def get_jose_guild(self):
        joseguild = self.bot.get_guild(self.bot.config.JOSE_GUILD)
        if not joseguild:
            raise self.SayException('`config error`: José guild not found.')

        return joseguild

    @lottery.command()
    @commands.is_owner()
    async def roll(self, ctx):
        """Roll a winner from the pool"""
        joseguild = self.get_jose_guild()
        cur = self.ticket_coll.find()

        # !!! bad code !!!
        # this is not WEBSCALE
        all_users = await cur.to_list(length=None)
        winner_id = random.choice(all_users)['user_id']

        if not any(m.id == ctx.author.id for m in joseguild.members):
            raise self.SayException(f'selected winner, <@{winner_id}> '
                                    'is not in jose guild. ignoring!')

        u_winner = self.bot.get_user(winner_id)
        if u_winner is None:
            return await ctx.send('Winner is unfindable user.')

        await self.lottery_send(f'**Winner!** `{u_winner!s}, {u_winner.id}`')
        await ctx.send(f'Winner: <@{winner_id}>, transferring will take time')

        # insert user into cooldown
        await self.cdown_coll.delete_many({'user_id': winner_id})
        await self.cdown_coll.insert_one({
            'user_id': winner_id,
            'rolls_wait': LOTTERY_COOLDOWN,
        })

        # business logic is here
        total = decimal.Decimal(0)
        taxbanks = await self.get_taxbanks()
        for account in taxbanks:
            amount = PERCENTAGE_PER_TAXBANK * \
                    decimal.Decimal(account['amount'])

            try:
                await self.jcoin.transfer(account['account_id'], winner_id,
                                          amount)
                total += amount
            except Exception as err:
                await ctx.send(f'err txb tx: {err!r}')

            await asyncio.sleep(0.1)

        amount_people = await self.ticket_coll.count()
        amount_from_ticket = TICKET_INCREASE * amount_people * TICKET_PRICE
        await self.jcoin.transfer(self.bot.user.id, winner_id,
                                  amount_from_ticket)

        total += amount_from_ticket
        total = round(total, 3)
        await ctx.send(f'Sent a total of `{total}` to the winner')

        # check out all current winners
        upd = await self.cdown_coll.update_many({}, {'$inc': {'rolls_wait': -1}})
        await ctx.send(f'Updated {upd.modified_count} winner wait documents')

        delt = await self.ticket_coll.delete_many({})
        await ctx.send(f'Deleted {delt.deleted_count} tickets')

    @lottery.command()
    async def enter(self, ctx):
        """Enter the weekly lottery.
        You will pay 11JC for a ticket.
        """
        # Check if the user is in jose guild
        joseguild = self.get_jose_guild()

        if ctx.author not in joseguild.members:
            raise self.SayException("You are not in José's server. "
                                    'For means of transparency, it is '
                                    'recommended to join it, use '
                                    f'`{ctx.prefix}invite`')

        win = await self.cdown_coll.find_one({'user_id': ctx.author.id})
        if win and win['rolls_wait'] > 0:
            raise self.SayException(f'You have to wait {win["rolls_wait"]} rolls.')

        ticket = await self.ticket_coll.find_one({'user_id': ctx.author.id})
        if ticket:
            raise self.SayException('You already bought a ticket.')

        # Pay 20jc to jose
        await self.coins.transfer(ctx.author.id, self.bot.user.id,
                                  TICKET_PRICE)

        await self.ticket_coll.insert_one({'user_id': ctx.author.id})
        await self.lottery_send(f'In lottery: `{ctx.author!s}, {ctx.author.id}`')
        await ctx.ok()


def setup(bot):
    bot.add_jose_cog(Lottery)
