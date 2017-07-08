
from discord.ext import commands

from .common import Cog

# prod
JOSE_SERVER = 273863625590964224
ROLE_ID = 332410139762098178

# test
#JOSE_SERVER = 319540379495956490
#ROLE_ID = 332410900600324097

class Subscribe(Cog):
    """Subscribe to a role and participate in José's development!"""
    def __init__(self, bot):
        super().__init__(bot)
    
    def __local_check(self, ctx):
        return ctx.guild.id == JOSE_SERVER

    def get_role(self, ctx, roleid):
        return next(r for r in ctx.guild.roles if r.id == roleid)

    @commands.command()
    async def sub(self, ctx):
        """Subscribe to the little group of memers who i can ping with
        to ask about josé
        """
        sub_role = self.get_role(ctx, ROLE_ID)
        await ctx.member.add_roles(sub_role)
        await ctx.ok()

    @commands.command()
    async def unsub(self, ctx):
        """Unsubscribe from the paradise"""
        sub_role = self.get_role(ctx, ROLE_ID)
        await ctx.member.remove_roles(sub_role)
        await ctx.send(':c')

    @commands.command()
    @commands.is_owner()
    async def callout(self, ctx, *, msg: str):
        """Call out the subscribers"""
        role = self.get_role(ctx, ROLE_ID)
        await role.edit(mentionable=True)
        await ctx.send(f'{role.mention} {msg}')
        await role.edit(mentionable=False)

def setup(bot):
    bot.add_cog(Subscribe(bot))

