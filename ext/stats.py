import asyncio
import logging
import decimal

import pymongo

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

        self.stats_task = None
        if self.bot.config.datadog:
            self.stats_task = bot.loop.create_task(self.querystats())
        else:
            log.warning('Datadog is disabled!')

    def __unload(self):
        if self.stats_task:
            self.stats_task.cancel()

    async def datadog(self, method_str, *args):
        method = getattr(statsd, method_str)
        saviour = self.loop.run_in_executor(None, method, *args)
        return await saviour

    async def gauge(self, key, value):
        return await self.datadog('gauge', key, value)

    async def increment(self, key):
        return await self.datadog('increment', key)

    async def decrement(self, key):
        return await self.datadog('decrement', key)

    async def basic_measures(self):
        await self.gauge('jose.guilds', len(self.bot.guilds))
        await self.gauge('jose.users', len(self.bot.users))
        await self.gauge('jose.channels', sum(1 for c
                                              in self.bot.get_all_channels()))

    async def starboard_stats(self):
        """Pushes starboard statistics to datadog."""
        stars = self.bot.get_cog('Starboard')
        if stars is None:
            log.warning('[stats] Starboard cog not found, ignoring')
            return

        total_sconfig = await stars.starconfig_coll.count()
        await self.gauge('jose.starboard.total_configs', total_sconfig)

        total_stars = await stars.starboard_coll.count()
        await self.gauge('jose.starboard.total_stars', total_stars)

    async def jcoin_stats(self):
        """Push JoséCoin stats to datadog."""

        coins = self.bot.get_cog('Coins')
        if coins is None:
            log.warning('[stats] Coins cog not found')
            return

        total_accounts = await coins.jcoin_coll.count()
        total_users = await coins.jcoin_coll.count({'type': 'user'})
        total_tbanks = await coins.jcoin_coll.count({'type': 'taxbank'})
        await self.gauge('jose.coin.accounts', total_accounts)
        await self.gauge('jose.coin.users', total_users)
        await self.gauge('jose.coin.taxbanks', total_tbanks)

        total_coins = [decimal.Decimal(0), decimal.Decimal(0)]
        inf = decimal.Decimal('inf')
        async for account in coins.jcoin_coll.find():
            account['amount'] = decimal.Decimal(account['amount'])
            if account['amount'] == inf:
                continue

            acctype = account['type']
            if acctype == 'user':
                total_coins[0] += account['amount']
            elif acctype == 'taxbank':
                total_coins[1] += account['amount']

        uc, tc = int(total_coins[0]), int(total_coins[1])
        await self.gauge('jose.coin.usercoins', uc)
        await self.gauge('jose.coin.taxcoins', tc)

        await self.gauge('jose.coin.totalcoins', uc + tc)

    async def texter_stats(self):
        """Report Texter statistics to datadog."""
        speak = self.bot.get_cog('Speak')
        if not speak:
            log.warning('[stats] Speak not found')
            return

        await self.gauge('jose.tx.count', len(speak.text_generators))
        await self.gauge('jose.tx.avg_gen',
                         speak.st_gen_totalms / speak.st_gen_count)
        await self.gauge('jose.tx.txc_avg_run',
                         speak.st_txc_totalms / speak.st_txc_runs)

    async def querystats(self):
        try:
            while True:
                await self.basic_measures()
                await self.starboard_stats()
                await self.jcoin_stats()
                await self.texter_stats()

                await asyncio.sleep(120)
        except asyncio.CancelledError:
            log.info('[statsd] stats machine broke')
        except Exception:
            log.error('[statsd] we had shit', exc_info=True)

    async def on_command(self, ctx):
        command = ctx.command
        c_name = command.name

        stats = await self.cstats_coll.find_one({'name': c_name})
        if stats is None:
            await self.cstats_coll.insert_one(empty_stats(c_name))

        if self.bot.config.datadog:
            statsd.increment('jose.complete_commands')
        await self.cstats_coll.update_one({'name': c_name},
                                          {'$inc': {'uses': 1}})

    async def on_message(self, message):
        if self.bot.config.datadog:
            statsd.increment('jose.recv_messages')

    async def on_guild_remove(self, guild):
        log.info(f'Left guild {guild.name} {guild.id},'
                 f' {guild.member_count} members')

    @commands.command(aliases=['cstats'])
    async def command_stats(self, ctx, limit: int=10):
        """Show most used commands."""
        if limit > 20 or limit < 1:
            await ctx.send('no')
            return

        cur = self.cstats_coll.find().sort('uses',
                                           direction=pymongo.DESCENDING)\
                                     .limit(limit)
        res = []
        async for single in cur:
            name, uses = single['name'], single['uses']
            res.append(f'{name}: used {uses} times')

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
