import traceback
import logging

from discord.ext import commands

from .common import Cog, shell


log = logging.getLogger(__name__)


class Admin(Cog):
    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        log.info('Logging out! %s', ctx.author)
        await ctx.send("dude rip")
        # await self.bot.session.close()
        await self.bot.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, *exts: str):
        """Loads an extension."""
        for ext in exts:
            try:
                self.bot.load_extension("ext." + ext)
            except Exception as e:
                await ctx.send(f'Oops. ```py\n{traceback.format_exc()}\n```')
                return
            log.info(f'Loaded {ext}')
            await ctx.send(f':ok_hand: `{ext}` loaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, *exts: str):
        """Unloads an extension."""
        for ext in exts:
            self.bot.unload_extension('ext.' + ext)
            log.info(f'Unloaded {ext}')
            await ctx.send(f':ok_hand: `{ext}` unloaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *extensions: str):
        """Reloads an extension"""
        for ext in extensions:
            try:
                self.bot.unload_extension('ext.' + ext)
                self.bot.load_extension('ext.' + ext)
            except Exception as err:
                await ctx.send(f'```{traceback.format_exc()}```')
                return
            log.info(f'Reloaded {ext}')
            await ctx.send(f':ok_hand: Reloaded `{ext}`')

    @commands.command()
    @commands.is_owner()
    async def shell(self, ctx, *, command: str):
        """Execute shell commands."""
        with ctx.typing():
            result = await shell(command)
        await ctx.send(f"`{command}`: ```{result}```\n")

    @commands.command()
    @commands.is_owner()
    async def update(self, ctx):
        """im lazy"""
        await ctx.invoke(self.bot.get_command('shell'), command='git pull')


def setup(bot):
    bot.add_cog(Admin(bot))
