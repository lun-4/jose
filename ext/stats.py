import collections

from discord.ext import commands

from .common import Cog

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

    async def on_command_completion(self, ctx):
        command = ctx.command
        c_name = command.name

        stats = await self.cstats_coll.find_one({'name': c_name})
        if stats is None:
            await self.cstats_coll.insert_one(empty_stats(c_name))

        await self.cstats_coll.update_one({'name': c_name}, {'$inc': {'uses': 1}})

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

def setup(bot):
    bot.add_cog(Statistics(bot))
