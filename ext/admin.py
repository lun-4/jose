import traceback
import asyncio
import logging

from discord.ext import commands

from .common import Cog


log = logging.getLogger(__name__)


class Admin(Cog):
    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("dude rip")
        #await self.bot.session.close()        
        await self.bot.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, extension_name : str):
        """Loads an extension."""
        try:
            self.bot.load_extension("ext." + extension_name)
        except Exception as e: 
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
            return
        log.info(f'Loaded {extension_name}')
        await ctx.send(f':ok_hand: `{extension_name}` loaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, extension_name : str):
        """Unloads an extension."""
        self.bot.unload_extension('ext.' + extension_name)
        log.info(f'Unloaded {extension_name}')
        await ctx.send(f':ok_hand: `{extension_name}` unloaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, extension_name : str):
        """Reloads an extension"""
        try:
            self.bot.unload_extension('ext.' + extension_name)
            self.bot.load_extension('ext.' + extension_name)
        except Exception as err:
            await ctx.send(f'```{traceback.format_exc()}```')
            return
        log.info(f'Reloaded {extension_name}')
        await ctx.send(f':ok_hand: Reloaded `{extension_name}`')

    @commands.command()
    @commands.is_owner()
    async def shell(self, ctx, *, command: str):
        """Execute shell commands."""

        p = await asyncio.create_subprocess_shell(command,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        with ctx.typing():
            await p.wait()

        result = (await p.stdout.read()).decode("utf-8")
        await ctx.send(f"`{command}`: ```{res}```\n")

def setup(bot):
    bot.add_cog(Admin(bot))
