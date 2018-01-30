from discord.ext import commands

from .common import Cog

MEMEWORK = [
    295341979800436736,
    387091446676586496,
]


class Memework(Cog):
    """memes my dude"""
    def __local_check(self, ctx):
        if not ctx.guild:
            return False

        return ctx.guild.id in MEMEWORK

    @commands.command()
    async def email(self, ctx):
        """fuck gerd"""
        await ctx.send('You can now get a @memework.org address, pm heatingdevice#1212 for more info!')


def setup(bot):
    bot.add_cog(Memework(bot))
