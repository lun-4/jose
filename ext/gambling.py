import asyncio
import decimal
import random
import collections

import discord

from discord.ext import commands
from .common import Cog, CoinConverter


EMOJI_POOL = ':thinking: :snail: :shrug: :chestnut: :ok_hand: :eggplant:'.split() + \
        ':fire: :green_book: :radioactive: :rage: :new_moon_with_face: :sun_with_face: :bread:'.split()
BET_MULTIPLIER_EMOJI = ':thinking:'
X4_EMOJI = [':snail:', ':ok_hand', ':chestnut:']
X6_EMOJI = [':eggplant:']


class Gambling(Cog, requires=['coins']):
    """Gambling commands."""
    def __init__(self, bot):
        super().__init__(bot)
        self.duels = {}
        self.locked = collections.defaultdict(bool)

    @commands.command()
    @commands.guild_only()
    async def duel(self, ctx, challenged_user: discord.User,
                   amount: CoinConverter):
        """Duel a user for coins.

        The winner of the duel is the person that sends a message first as soon
        as josé says "GO".
        """
        if challenged_user == ctx.author:
            raise self.SayException("You can't do this alone.")

        if challenged_user.bot:
            raise self.SayException('You cannot duel bots.')

        if amount > 5:
            raise self.SayException("Can't duel more than 5JC.")

        challenger_user = ctx.author
        challenger = ctx.author.id
        challenged = challenged_user.id

        if await self.bot.is_blocked(challenged):
            raise self.SayException('Challenged person is blocked from José'
                                    '(use `j!blockreason <their user id>`)')

        if self.locked[challenged]:
            raise self.SayException('Challenged person is locked to new duels')

        if challenger in self.duels:
            raise self.SayException('You are already in a duel')

        challenger_acc = await self.jcoin.get_account(challenger)
        if not challenger_acc:
            raise self.SayException("You don't have a wallet.")

        challenged_acc = await self.jcoin.get_account(challenged)
        if not challenged_acc:
            raise self.SayException("Challenged person doesn't have a wallet.")

        if amount > challenger_acc['amount'] or \
           amount > challenged_acc['amount']:
            raise self.SayException("One of you don't have enough"
                                    " funds to make the duel.")

        try:
            await self.coins.lock(challenger, challenged)

            self.locked[challenged] = True
            await ctx.send(f'{challenged_user}, you got challenged '
                           f'for a duel :gun: by {challenger_user} '
                           f'with a total of {amount}JC, accept it? (y/n)')

            def yn_check(msg):
                cnt = msg.content
                return msg.author.id == challenged and \
                    msg.channel == ctx.channel and \
                    any(x in cnt for x in ['y', 'n', 'Y', 'N'])

            try:
                msg = await self.bot.wait_for('message',
                                              timeout=10, check=yn_check)
            except asyncio.TimeoutError:
                raise self.SayException('timeout reached')

            if msg.content != 'y':
                raise self.SayException("Challenged person didn't"
                                        " say a lowercase `y`.")

            countdown = 3
            countdown_msg = await ctx.send('First to send a '
                                           f'message wins! {countdown}')
            await asyncio.sleep(1)

            for i in reversed(range(1, 4)):
                await countdown_msg.edit(content=f'{i}...')
                await asyncio.sleep(1)

            await asyncio.sleep(random.randint(2, 7))
            await countdown_msg.edit(content='**GO!**')

            self.duels[challenger] = {
                'challenged': challenged,
                'amount': amount,
            }

            duelists = [challenged, challenger]

            def duel_check(msg):
                return msg.channel == ctx.channel and msg.author.id in duelists

            try:
                msg = await self.bot.wait_for('message',
                                              timeout=5, check=duel_check)
            except asyncio.TimeoutError:
                raise self.SayException('u guys suck.')

            self.locked[challenged] = False
            await self.coins.unlock(challenger, challenged)

            winner = msg.author.id
            duelists.remove(winner)
            loser = duelists[0]

            try:
                await self.jcoin.transfer(loser, winner, amount)
            except self.jcoin.TransferError as err:
                raise self.SayException(f'Failed to transfer: {err!r}')

            await ctx.send(f'<@{winner}> won {amount}JC.')
        finally:
            self.locked[challenged] = False
            if challenger in self.duels:
                del self.duels[challenger]

            await self.coins.unlock(challenger, challenged)

    @commands.command()
    async def slots(self, ctx, amount: CoinConverter):
        """little slot machine"""
        if amount > 8:
            raise self.SayException('You cannot gamble too much.')

        await self.jcoin.transfer(ctx.author.id, ctx.guild.id, amount)

        res = []
        slots = [random.choice(EMOJI_POOL) for i in range(3)]

        res.append(' '.join(slots))
        bet_multiplier = slots.count(BET_MULTIPLIER_EMOJI) * 2

        for emoji in slots:
            if slots.count(emoji) == 3:
                if emoji in X4_EMOJI:
                    bet_multiplier = 4
                elif emoji in X6_EMOJI:
                    bet_multiplier = 6

        applied_amount = amount * bet_multiplier

        res.append(f'**Multiplier**: {bet_multiplier}x')
        res.append(f'bet: {amount}, won: {applied_amount}')

        if applied_amount > 0:
            try:
                await self.jcoin.transfer(ctx.guild.id,
                                          ctx.author.id,
                                          applied_amount)
            except self.jcoin.TransferError as err:
                raise self.SayException(f'err(g->a, a): {err!r}')
        else:
            res.append(':peach:')

        await ctx.send('\n'.join(res))

    @commands.command()
    async def flip(self, ctx):
        """Flip a coin. (49%, 49%, 2%)"""
        p = random.random()
        if p < .49:
            await ctx.send('https://i.imgur.com/oEEkybO.png')
        elif .49 < p < .98:
            await ctx.send('https://i.imgur.com/c9smEW6.png')
        else:
            await ctx.send('https://i.imgur.com/yDPUp3P.png')


def setup(bot):
    bot.add_jose_cog(Gambling)
