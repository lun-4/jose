import collections
import asyncio
import logging
import discord
import decimal
from random import SystemRandom

from discord.ext import commands

from .common import Cog, SayException

random = SystemRandom()
log = logging.getLogger(__name__)

BASE_HEIST_CHANCE = decimal.Decimal('1')
HEIST_CONSTANT = decimal.Decimal('0.32')

class HeistSessionError(Exception):
    pass


class GuildConverter(commands.Converter):
    async def guild_name_lookup(self, ctx, arg):
        def f(guild):
            return arg == guild.name.lower()
        return discord.utils.find(f, ctx.bot.guilds)

    async def convert(self, ctx, arg):
        bot = ctx.bot

        try:
            guild_id = int(arg)
        except ValueError:
            f = lambda g: arg == g.name.lower()
            guild = discord.utils.find(f, bot.guilds)

            if guild is None:
                raise commands.BadArgument('Guild not found')
            return guild

        guild = bot.get_guild(guild_id)
        if guild is None:
            raise commands.BadArgument('Guild not found')
        return guild


class JoinSession:
    """Heist join session class
    
    This managers all the users in the session and
    does the actual "heisting", the "j!heist" subcommands
    are just a frontend for this :^)

    Attributes
    ----------
    ctx: `context`
        Context of the session, how it was started
    target: `discord.Guild`
        Guild that is the target of this session
    users: list[int]
        Users that are in this session
    started: bool
        If the session is started and accepts new users
    task: `asyncio.Task` or :py:meth:`None`
        Task for :meth:`JoinSession.do_heist`
    """
    def __init__(self, ctx, target):
        self.ctx = ctx
        self.bot = ctx.bot
        self.target = target
        self.amount = 0

        self.users = []
        self.started = False
        self.finish = asyncio.Event()
        self.task = None

    @property
    def fine(self) -> 'decimal.Decimal':
        """Get the fine to be paid by all people in the session
        if the heist failed.
        """
        return self.amount / len(self.users)

    def add_member(self, user_id: int):
        self.started = True
        try:
            self.users.index(user_id)
            raise SayException('User already in the session')
        except ValueError:
            self.users.append(user_id)

    async def do_heist(self, ctx) -> dict:
        """Actually does the heist.

        Returns
        -------
        dict
            With data about if the heist was successful and the amount stolen,
            or which members went to jail if it was unsuccessful.
        """

        await self.finish.wait()
        log.info('Doing the heist')

        res = {
            'success': False,
            'jailed': [],
            'saved': [],
        }

        bot = ctx.bot
        jcoin = bot.get_cog('Coins')
        if not jcoin:
            raise self.SayException('rip')

        target_account = await jcoin.get_account(self.target.id)
        if target_account is None:
            raise self.SayException('Guild not found')

        if target_account['type'] != 'taxbank':
            raise self.SayException('Account is not a taxbank')

        chance = BASE_HEIST_CHANCE + (amnt / self.amount) * HEIST_CONSTANT

        # trim it to 50% success
        if chance > 5:
            chance = 5

        res = random.uniform(0, 10)

        res['chance'] = chance
        res['result'] = res

        if res < chance:
            res['success'] = True
        else:
            res['success'] = False

            # 50% chance of every person
            # in the heist to go to jail
            for user_id in self.users:
                if random.random() < 0.5:
                    res['jailed'].append(user_id)
                else:
                    res['saved'].append(user_id)

        return res

    async def jail(self, res: dict):
        """Put people in jail."""
        cext = bot.get_cog('Coins+')
        coins = bot.get_cog('Coins')

        ctx = self.ctx

        for user_id in res['users']:
            await coins.transfer(user_id, self.target.id, self.fine)

        for jailed_id in res['jailed']:
            jailed = self.bot.get_user(jailed_id)
            if jailed is None:
                log.warning('uid=%d not found', jailed_id)
                continue

            # put them in normal jail
            await cext.add_cooldown(jailed)

        res = ' '.join([f'<@{jailed}>' for jailed in res['jailed']])
        await ctx.send('In jail: {res}')

        res2 = ' '.join([f'<@{saved}>' for saved in res['saved']])
        await ctx.send('Not in Jail: {res2}')

    async def process_heist(self, res: dict):
        """Process the result given by :meth:`JoinSession.do_heist`"""
        await self.ctx.send(f'gay: `{res!r}`')

        if not res['success']:
            return await self.jail(res)

        # TODO: the actual success logic
        pass

    async def force_finish(self) -> 'any':
        """Force the join session to finish
        and the heist to start.
        
        Returns
        any
            Anything

        Raises
        ------
        Exception
            Whatever :class:`JoinSession.do_heist` raises.
        RuntimeError
            If no task is provided to the session.
        """
        guild = self.ctx.guild
        log.info('Forcing a finish at {guild!s}[{guild.id}]')
        self.finish.set()

        if self.task is None:
            raise RuntimeError('wat')

        # since Task.exception() returns None
        # I had to setup err as a string by default
        err = 'nothing'
        while err == 'nothing':
            try:
                log.info(f'waiting for exception {self.finish.is_set()}')
                err = self.task.exception()
            except asyncio.InvalidStateError:
                await asyncio.sleep(1)

        if err is not None:
            raise err
        
        log.info('returning result')
        return self.task.result()


class Heist(Cog):
    """Heist system
    
    Heisting works by stealing taxbanks(see "j!help taxes" for a quick
    explanation on them) of other guilds/servers.
    """
    def __init__(self, bot):
        super().__init__(bot)
        self.sessions = {}

    @property
    def coinsext(self):
        return self.bot.get_cog('Coins+')

    def get_sess(self, ctx, target=None, clean=False):
        """Get a join session.
        
        Parameters
        ----------
        ctx: `context`
            Command context.
        clean: bool, optional
            If this requires a clean session(not started).

        Raises
        ------
        SayException
            - If no target is provided when creating the session

            - If the session already started and we required
            a clean session to exist

            - If the session isn't started and we required a started session
        """
        session = self.sessions.get(ctx.guild.id)
        if session is None and target is None:
            raise self.SayException('Cannot create a session without a target')

        if session is None:
            session = JoinSession(ctx, target)
            self.sessions[ctx.guild.id] = session

        if session.started and clean:
            raise self.SayException('An already started join session exists')
        elif (not session.started) and (not clean):
            raise self.SayException("Join session isn't started")

        return session

    async def check_user(self, ctx, session):
        cext = bot.get_cog('CoinsExt')
        coins = bot.get_cog('Coins')

        await cext.check_cooldowns(ctx)
        acc = await coins.get_account(ctx.author.id)
        if acc['amount'] < 10:
            raise self.SayException("You don't have more than `10JC` to join the session.")

    @commands.group(invoke_without_command=True)
    async def heist(self, ctx, amount: decimal.Decimal, *, target: GuildConverter):
        """Heist a server.
        
        This works better if you have more people joining in your heist.

         - As soon as you use this command, a heist join session will start.
           - This session requires that all other people that want to join the
            heist to use the "j!heist join" command

           - There is a timeout of 5 minutes on the heist join session.
         - If your heist fails, all participants of the heist will be sentenced
            to jail or not, its random.
        """
        for session in self.sessions.values():
            if session.target.id == target.id:
                raise self.SayException('An already existing session exists with the same target')

        session = self.get_sess(ctx, target, True)

        try:
            await self.check_user(ctx, session)
        except self.SayException as err:
            self.sessions.pop(ctx.guild.id)
            raise err

        session.amount = amount
        session.add_member(ctx.author.id)
        session.task = self.loop.create_task(session.do_heist(ctx))

        await ctx.send('Join session started!')

        # timeout of 5 minutes accepting members
        # OR "j!heist finish"
        await asyncio.sleep(300)
        if not session.finish.is_set():
            await session.process_heist(await session.force_finish())

    @heist.command(name='join')
    async def heist_join(self, ctx):
        """Enter the current heist join session.

        You can't leave a join session.
        """
        # we need to check all current sessions
        # and make users enter only one join session
        # per time. so we don't have race conditions
        # or whatever

        for session in self.sessions.values():
            if ctx.author.id in session.users:
                raise self.SayException(f'You are already in a join session at `{session.ctx.guild!s}`')
        
        session = self.get_sess(ctx)
        await self.check_user(ctx, session)

        session.add_member(ctx.author.id)
        await ctx.ok()

    @heist.command(name='current')
    async def current(self, ctx):
        """Get your current heist join session."""
        session = self.get_sess(ctx)

        res = [f'Guild being attacked: `{session.guild!s}`', 
            f'Amount: `{session.amount!s}i`',
            'Current users in the session:'
        ]

        for user_id in session.users:
            res.append(f'\t<@{user_id}>')

        res = '\n'.join(res)
        await ctx.send(f'{res}')

    @heist.command(name='finish')
    async def heist_force(self, ctx):
        """Force a current heist join session to be finish already."""
        session = self.get_sess(ctx)
        await session.process_heist(await session.force_finish())

def setup(bot):
    bot.add_cog(Heist(bot))

