import traceback
import logging
import re

import asyncpg
from discord.ext import commands

from .utils import Table, Timer
from .common import Cog, shell

log = logging.getLogger(__name__)


def no_codeblock(text: str) -> str:
    """
    Removes codeblocks (grave accents), python and sql syntax highlight
    indicators from a text if present.
    .. note:: only the start of a string is checked, the text is allowed
     to have grave accents in the middle
    """
    if text.startswith('```'):
        text = text[3:-3]

        if text.startswith(('py', 'sql')):
            # cut off the first line as this removes the
            # highlight indicator regardless of length
            text = '\n'.join(text.split('\n')[1:])

    if text.startswith('`'):
        text = text[1:-1]

    return text


class Admin(Cog, requires=['config']):
    @property
    def db(self) -> asyncpg.pool.Pool:
        cfg = self.bot.get_cog('Config')
        if cfg is not None:
            return cfg.db
        raise RuntimeError('Required config Cog is not loaded.')

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
            m = ctx.send(f':ok_hand: `{ext}` loaded.')
            self.bot.loop.create_task(m)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, *exts: str):
        """Unloads an extension."""
        for ext in exts:
            self.bot.unload_extension('ext.' + ext)
            log.info(f'Unloaded {ext}')
            m = ctx.send(f':ok_hand: `{ext}` unloaded.')
            self.bot.loop.create_task(m)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *extensions: str):
        """Reloads an extension"""
        for ext in extensions:
            try:
                self.bot.unload_extension('ext.' + ext)
                self.bot.load_extension('ext.' + ext)
                log.info(f'Reloaded {ext}')
            except Exception as err:
                await ctx.send('OOPSIE WOOPSIE!!\nUwu We made a fucky wucky!\n'
                               'A wittle fucko boingo!```py\n'
                               f'{traceback.format_exc()}\n```')

                return

            # don't block the coro waiting for a message send
            # since we might cause state inconsistencies
            msg = ctx.send(f':ok_hand: Reloaded `{ext}`')
            self.bot.loop.create_task(msg)

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

    @commands.command()
    @commands.is_owner()
    async def urel(self, ctx):
        """Update and reload automatically.

        Thanks aveao (github). <3
        """
        with ctx.typing():
            out = await shell('git pull')

        await ctx.send(f"```\n{out}\n```\n")

        # regex magic from ave <3
        to_reload = re.findall(r'ext/([a-z]*).py[ ]*\|', out)

        if not to_reload:
            return await ctx.send('No cogs found to reload')

        if 'coins' in to_reload:
            to_reload.pop('coins')

            # enforce coins is loaded BEFORE anything else
            to_reload.insert(0, 'coins')

        # offload actual reloading to reload command
        await ctx.invoke(self.bot.get_command('reload'), *to_reload)

    @commands.command(typing=True)
    @commands.is_owner()
    async def sql(self, ctx, *, statement: no_codeblock):
        """Execute SQL."""
        # this is probably not the ideal solution
        if 'select' in statement.lower():
            coro = self.db.fetch
        else:
            coro = self.db.execute

        try:
            with Timer() as t:
                result = await coro(statement)
        except asyncpg.PostgresError as e:
            return await ctx.send(f':x: Failed to execute!'
                                  f' {type(e).__name__}: {e}')

        # execute returns the status as a string
        if isinstance(result, str):
            return await ctx.send(f'```py\n{result}```took {t.duration:.3f}ms')

        if not result:
            return await ctx.send(f'no results, took {t.duration:.3f}ms')

        # render output of statement
        columns = list(result[0].keys())
        table = Table(*columns)

        for row in result:
            values = [str(x) for x in row]
            table.add_row(*values)

        rendered = await table.render(self.loop)

        # properly emulate the psql console
        rows = len(result)
        rows = f'({rows} row{"s" if rows > 1 else ""})'

        await ctx.send(f'```py\n{rendered}\n{rows}```took {t.duration:.3f}ms')


def setup(bot):
    bot.add_cog(Admin(bot))
