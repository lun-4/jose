import logging

import discord
from discord.ext import commands

from .common import Cog

BOT_RATIO_MAX = 1.1

WHITELIST = (
    273863625590964224,  # José's server
    295341979800436736,  # Memework
    319540379495956490,  # v2 testing serv
    380295555039100932,  # Comet Obversavotory / luma's home
    319252487280525322,  # robert is gay
    340609473439596546,  # slice is a furry that plays agario
    191611344137617408,  # dan's 'haha gay pussy party'
    277919178340565002,  # lold - lolbot testing server
    248143597097058305,  # cyn bae's private server we gotta get 69
    291990349776420865,  # em's meme heaven
    366513799404060672,  # dan's another gay guild
    322885030806421509,  # heating's gay guild
    350752456554184704,  # eric's gay guild
)

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
        owner = guild.owner

        log.info(f'[bh:join] {guild!s} -> ratio {len(bots)}b / {len(humans)}h '
                 f'= {ratio:.2}')

        if guild.id in WHITELIST:
            return

        if ratio > BOT_RATIO_MAX:
            log.info(f'[bh:leave:guild_join] leaving {guild!s}')
            await guild.leave()
            return

        if await self.bot.is_blocked_guild(guild.id):
            await owner.send('Sorry. The guild you added José on is blocked. '
                             'Appeal to the block at the support server'
                             '(Use the invite provided in `j!invite`).')
            await guild.leave()
            return

        await owner.send('Hello, welcome to José!\n'
                         "Discord's API Terms of Service requires me to tell you I log\n"
                         'Command usage and errors to a special channel.\n'
                         '**Only commands and errors are logged, no messages are logged, ever.**')

    async def on_member_join(self, member):
        guild = member.guild
        bots, humans, ratio = self.bot_human_ratio(guild)

        if guild.id in WHITELIST:
            return

        if ratio > BOT_RATIO_MAX:
            log.info(f'[bh:leave:member_join] leaving {guild!r} {guild.id},'
                     f' {len(bots)}/{len(humans)} = {ratio}')
            try:
                await guild.owner.send('Your guild was classified as a bot'
                                       'collection, josé automatically left.'
                                       f'{len(bots)} bots, {len(humans)} humans, '
                                       f'{ratio}b/h, ratio is over {BOT_RATIO_MAX}')
            except discord.HTTPException:
                pass
            await guild.leave()

    @commands.command()
    @commands.guild_only()
    async def bhratio(self, ctx):
        """Get your guild's bot-to-human ratio"""

        bots, humans, ratio = self.bot_human_ratio(ctx.guild)
        _, _, global_ratio = self.bhratio_global()

        await ctx.send(f'{len(bots)} bots / {len(humans)} humans => '
                       f'`{ratio:.2}b/h`, global is `{global_ratio:.2}`')


def setup(bot):
    bot.add_cog(BotCollection(bot))
