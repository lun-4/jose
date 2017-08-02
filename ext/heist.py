from random import SystemRandom

from discord.ext import commands
from .common import Cog

random = SystemRandom()

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

class Heist(Cog):
    """Heist system
    
    Heisting works by stealing taxbanks(see "j!help taxes" for a quick
    explanation on them) of other guilds/servers.
    """
    def __init__(self, bot):
        super().__init__(bot)
        # TODO: more attrs

    @property
    def coinsext(self):
        return self.bot.get_cog('Coins+')

    @commands.group()
    async def heist(self, ctx, guild: GuildConverter):
        """Heist a server.
        
        Heisting works better if you have more people joining in your heist

         - As soon as you use this command, a heist join session will start.
           - This session requires that all other people that want to join the
            heist to use the "j!heist join" command
           - There is a timeout of 5 minutes on the heist join session.
         - If your heist fails, all participants of the heist will be sentenced
            to jail or not, its random.
        """
        pass

    @heist.command(name='join')
    async def heist_join(self, ctx):
        """Enter the current heist join session."""

    @heist.command(name='force')
    async def heist_force(self, ctx):
        """Force a current heist join session to be done."""

