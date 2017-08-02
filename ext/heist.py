import collections
import asyncio
import logging
from random import SystemRandom

from discord.ext import commands

from .common import Cog, SayException

random = SystemRandom()
log = logging.getLogger(__name__)


class HeistSessionError(Exception):
    pass


class GuildConverter(commands.Converter):
    async def guild_name_lookup(self, ctx, arg):
        def f(guild):
            return arg == guild.name.lower()
        return discord.utils.find(f, ctx.bot.guilds)

    async def convert(self, ctx, arg):
        try:
            guild_id = int(argument)
        except (TypeError, ValueError):
            guild = await self.guild_name_lookup(ctx, arg)
            if guild is None:
                raise commands.BadArgument('Guild not found')

        guild = ctx.bot.get_guild(guild_id)
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
        self.target = target
        self.users = []
        self.started = False
        self.finish = asyncio.Event()
        self.task = None

    def add_member(self, user_id: int):
        self.started = True

        try:
            self.users.index(user_id)
            raise SayException('User already in the session')
        except IndexError:
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

        res = {
            'success': False,
            'amount_stolen': 0,
            'jailed': [],
        }

        bot = ctx.bot
        jcoin = bot.jcoin
        account = jcoin.get_account(self.target.id)
        if account is None:
            await ctx.send('Guild not found')
            return

        if account['type'] != 'taxbank':
            await ctx.send('Account is not a taxbank')
            return

        # TODO: add the random chance of who went to jail and
        # who didn't

        return res

    def finish(self):
        self.finish.set()

class Heist(Cog):
    """Heist system
    
    Heisting works by stealing taxbanks(see "j!help taxes" for a quick
    explanation on them) of other guilds/servers.
    """
    def __init__(self, bot):
        super().__init__(bot)
        self.join_sessions = {}

    @property
    def coinsext(self):
        return self.bot.get_cog('Coins+')

    def get_session(self, ctx, target=None, clean=False):
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
        session = self.join_sessions.get(ctx.guild.id)
        if session is None and target is None:
            raise self.SayException('Cannot create a session without a target')

        if session is None:
            session = JoinSession(ctx, target)
            self.join_sessions[ctx.guild.id] = session

        if session.started and clean:
            raise self.SayException('An already started join session exists')
        elif (not session.started) and (not clean):
            raise self.SayException("Join session isn't started")

        return session

    @commands.group()
    async def heist(self, ctx, target: GuildConverter):
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
        session.add_member(ctx.author.id)
        self.loop.create_task(session.do_heist(ctx))
        await ctx.send('Join session started!')

        # timeout of 5 minutes accepting members
        # OR "j!heist finish"
        await asyncio.sleep(300)
        if not session.finish.is_set():
            session.finish()

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
        session.add_member(ctx.author.id)
        await ctx.ok()

    @heist.command(name='finish')
    async def heist_force(self, ctx):
        """Force a current heist join session to be finish already."""
        session = self.get_sess(ctx)
        session.finish()

