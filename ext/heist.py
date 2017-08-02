from random import SystemRandom

from discord.ext import commands
from .common import Cog

random = SystemRandom()

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

