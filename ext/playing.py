import logging
import json
import asyncio
import random

import discord
from discord.ext import commands

from .common import Cog

MINUTE = 60
PL_MIN = 3 * MINUTE
PL_MAX = 10 * MINUTE

log = logging.getLogger(__name__)


class PlayingStatus(Cog):
    """Playing status shit"""
    def __init__(self, bot):
        super().__init__(bot)
        self.rotate_task = None
        self.phrases = json.load(open('./playing_status.json', 'r'))

    async def on_ready(self):
        # don't fuck up
        if self.rotate_task is not None:
            return

        self.rotate_task = self.bot.loop.create_task(self.rotate_loop())

    async def rotate(self):
        """Get a random playing status and use it"""
        msg = random.choice(self.phrases)
        fmt = f'{msg} | v{self.JOSE_VERSION} | {self.bot.command_prefix}help'
        log.info('Setting playing to %r', fmt)
        await self.bot.change_presence(game=discord.Game(name=fmt))

    async def rotate_loop(self):
        try:
            while True:
                await self.rotate()
                await asyncio.sleep(random.randint(PL_MIN, PL_MAX))
        except asyncio.CancelledError:
            pass

    @commands.command(name='rotate')
    @commands.is_owner()
    async def _rotate(self, ctx):
        """Rotate playing status"""
        await self.rotate()
        await ctx.send('done!')


def setup(bot):
    bot.add_cog(PlayingStatus(bot))
