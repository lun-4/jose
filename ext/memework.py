from discord.ext import commands

from .common import Cog

MEMEWORK = [
    295341979800436736,
    387091446676586496,
]

MOD_ROLES = (
    303296657787715585,  # root
)


def is_memework_mod():
    def predicate(ctx):
        return ctx.guild is not None and any(x.id in MOD_ROLES
                                             for x in ctx.author.roles)

    return commands.check(predicate)


class Memework(Cog):
    """Memework-only commands.

    Made by me and 90% from FrostLuma
    """

    def __local_check(self, ctx):
        if not ctx.guild:
            return False

        return ctx.guild.id in MEMEWORK

    @commands.command()
    async def email(self, ctx):
        """fuck gerd"""
        await ctx.send('You can now get a @memework.org address, '
                       'pm heatingdevice#1212 for more info!')


def setup(bot):
    bot.add_cog(Memework(bot))
