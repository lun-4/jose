import asyncio
import decimal
import random

import discord

from discord.ext import commands
from .common import Cog


EMOJI_POOL = ':thinking: :snail: :shrug: :chestnut: :ok_hand: :eggplant:'.split()
BET_MULTIPLIER_EMOJI = ':thinking:'
X4_EMOJI = [':snail:', ':chestnut:', ':shrug:']
X6_EMOJI = [':eggplant:', ':ok_hand:']

class Gambling(Cog):
    """Gambling commands."""
    def __init__(self, bot):
        super().__init__(bot)
        self.duels = {}

    @commands.command()
    async def duel(self, ctx, challenged_user: discord.User, amount: decimal.Decimal):
        """Duel a user for coins.
        
        The winner of the duel is the person that sends a message first as soon
        as josé says "GO".
        """

        amount = round(amount, 2)
        if amount > 3:
            await ctx.send('Can\'t duel with more than 3JC.')
            return

        if amount <= 0:
            await ctx.send('lul')
            return

        challenger_user = ctx.author
        challenger = ctx.author.id
        challenged = challenged_user.id

        if challenger in self.duels:
            await ctx.send('You are already in a duel.')
            return

        challenger_acc = await self.jcoin.get_account(challenger)

        if challenger_acc is None:
            await ctx.send('You don\'t have a wallet.')
            return

        challenged_acc = await self.jcoin.get_account(challenged)

        if challenged_acc is None:
            await ctx.send('Challenged person doesn\'t have a wallet.')
            return

        if amount > challenger_acc['amount'] or amount > challenged_acc['amount']:
            await ctx.send('One of you don\'t have tnough funds to make the duel.')
            return

        await ctx.send(f'{challenged_user}, you got challenged for a duel :gun: by {challenger_user} with a total of {amount}JC, accept it? (y/n)')

        def yn_check(msg):
            return msg.author.id == challenged and msg.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', timeout=10, check=yn_check)
        except asyncio.TimeoutError:
            await ctx.send('timeout reached')
            return

        if msg.content != 'y':
            await ctx.send('Challenged person didn\'t say a lowercase y.')
            return

        self.duels[challenger] = {
            'challenged': challenged,
            'amount': amount,
        }

        countdown = 3
        countdown_msg = await ctx.send(f'First to send a message wins! {countdown}')

        for i in reversed(range(1, 4)):
            await countdown_msg.edit(content=f'{i}...')
            await asyncio.sleep(1)

        await asyncio.sleep(random.randint(2, 7))
        await ctx.send('**GO!**')

        duelists = [challenged, challenger]

        def duel_check(msg):
            return msg.channel == ctx.channel and msg.author.id in duelists

        try:
            msg = await self.bot.wait_for('message', timeout=5, check=duel_check)
        except asyncio.TimeoutError:
            await ctx.send('u guys suck')
            return

        winner = msg.author.id
        duelists.remove(winner)
        loser = duelists[0]

        try:
            await self.jcoin.transfer(loser, winner, amount)
        except self.jcoin.TransferError as err:
            await ctx.send(f'Failed to tranfer: {err!r}')
            return

        await ctx.send(f'<@{winner}> won {amount}JC.')
        del self.duels[challenger]
    
    @commands.command()
    async def slots(self, ctx, amount: decimal.Decimal):
        """little slot machine"""
        await self.jcoin.ensure_taxbank(ctx)
        await self.jcoin.pricing(ctx, amount)

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
                await self.jcoin.transfer(ctx.guild.id, ctx.author.id, applied_amount)
            except self.jcoin.TransferError as err:
                await ctx.send(f'err: {err!r}')
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
    bot.add_cog(Gambling(bot))
