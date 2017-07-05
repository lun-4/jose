import logging

from discord.ext import commands

from .common import Cog

BOT_RATIO_MAX = 1.1

WHITELIST = (295341979800436736, 319540379495956490)

log = logging.getLogger(__name__)

class BotCollection(Cog):
    """Bot collection commands."""
    def bot_human_ratio(self, guild):
        bots = [member for member in guild.members if member.bot]
        humans = [member for member in guild.members if not member.bot]

        return bots, humans, (len(bots) / len(humans))

    def bhratio_global(self):
        all_members = self.bot.get_all_members

        bots = [member for member in all_members() if member.bot]
        humans = [member for member in all_members() if not member.bot]

        return bots, humans, (len(bots) / len(humans))

    async def on_guild_join(self, guild):
        bots, humans, ratio = self.bot_human_ratio(guild)

        log.info(f'[bh] {guild!s} -> ratio {bots} / {humans} = {ratio:.2}')

        if guild.id in WHITELIST:
            return

        if ratio > BOT_RATIO_MAX:
            log.info(f'[bh] leaving {guild!s}')
            await guild.leave()

    async def on_member_join(self, member):
        guild = member.guild

        bots, humans, ratio = self.bot_human_ratio(guild)

        if guild.id in WHITELIST:
            return

        if ratio > BOT_RATIO_MAX:
            log.info('[bh:member_join] leaving')
            await guild.leave()

    @commands.command()
    @commands.guild_only()
    async def bhratio(self, ctx):
        """Get your guild's bot-to-human ratio"""

        bots, humans, ratio = self.bot_human_ratio(ctx.guild)
        _, _, global_ratio = self.bhratio_global()

        await ctx.send(f'{len(bots)} bots / {len(humans)} humans => `{ratio:.2}b/h`, global is `{global_ratio:.2}`')

def setup(bot):
    bot.add_cog(BotCollection(bot))
