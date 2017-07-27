import collections
import asyncio
import logging

from datadog import statsd
from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)

def empty_stats(c_name):
    return {
        'name': c_name,
        'uses': 0,
    }

class Statistics(Cog):
    """Bot stats stuff."""
    def __init__(self, bot):
        super().__init__(bot)

        self.cstats_coll = self.config.jose_db['command_stats']

        if self.bot.config.datadog:
            self.stats_task = bot.loop.create_task(self.querystats())
        else:
            log.warning('Datadog is disabled!')

    def __unload(self):
        self.stats_task.cancel()

    async def querystats(self):
        try:
            while True:
                statsd.gauge('jose.guilds', len(self.bot.guilds))
                statsd.gauge('jose.channels', len(list(self.bot.get_all_channels())))
                statsd.gauge('jose.users', len(self.bot.users))
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            log.info('[statsd] stats machine broke')

    async def on_command(self, ctx):
        command = ctx.command
        c_name = command.name

        stats = await self.cstats_coll.find_one({'name': c_name})
        if stats is None:
            await self.cstats_coll.insert_one(empty_stats(c_name))
        
        if self.bot.config.datadog:
            statsd.increment('jose.complete_commands')
        await self.cstats_coll.update_one({'name': c_name}, {'$inc': {'uses': 1}})

    async def on_message(self, message):
        if self.bot.config.datadog:
            statsd.increment('jose.recv_messages')

    async def on_guild_leave(self, guild):
        log.info(f'Left guild {guild.name} {guild.id}, {guild.member_count} members')

    @commands.command(aliases=['cstats'])
    async def command_stats(self, ctx, limit: int = 10):
        """Shows the most used commands"""
        if limit > 20 or limit < 1:
            await ctx.send('no')
            return

        cur = self.cstats_coll.find()
        cnt = collections.Counter()

        for stat in await cur.to_list(length=limit):
            cnt[stat['name']] = stat['uses']

        most_used = cnt.most_common(limit)
        res = [f'{name}: used {uses} times' for (name, uses) in most_used]
        _res = '\n'.join(res)
        await ctx.send(f'```\n{_res}\n```')

    @commands.command(aliases=['cstat'])
    async def command_stat(self, ctx, command: str):
        """Get usage for a single command"""
        stat = await self.cstats_coll.find_one({'name': command})
        if stat is None:
            raise self.SayException('Command not found')

        await ctx.send(f'`{command}: {stat["uses"]} uses`')

def setup(bot):
    bot.add_cog(Statistics(bot))
