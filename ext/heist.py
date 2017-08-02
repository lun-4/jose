from random import SystemRandom

from discord.ext import commands
from .common import Cog

random = SystemRandom()

class GuildConverter(commands.Converter):
    async def guild_name_lookup(self, ctx, arg):
        def f(guild):
            return arg == guild.name.lower()
        return discord.utils.get(f, ctx.bot.guilds)

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
    """"""

    @property
    def coinsext(self):
        return self.bot.get_cog('Coins+')

    @commands.group()
    async def heist(self, ctx, guild: GuildConverter):
        pass

    @heist.command(name='join')
    async def heist_join()

