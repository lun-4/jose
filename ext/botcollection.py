import logging

import discord
from discord.ext import commands

from .common import Cog

BOT_RATIO_MIN = 1.7
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
    248143597097058305,  # cyn private server
    291990349776420865,  # em's meme heaven
    366513799404060672,  # dan's another gay guild
    322885030806421509,  # heating's gay guild
    350752456554184704,  # eric's gay guild
    422495103941345282,  # muh testing
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

    async def guild_ratio(self, guild: discord.Guild) -> float:
        """Get the bot-to-human ratio for a guild"""
        if len(guild.members) < 50:
            return BOT_RATIO_MIN
        else:
            return BOT_RATIO_MAX

    def fallback(self, guild: discord.Guild, message: str):
        """Send a message to the first channel we can send.

        Serves as a fallback instad of DMing owner.
        """
        chan = next(c for c in guild.text_channels
                    if guild.me.permissions_in(c).send_messages)
        return chan.send(message)

    async def on_guild_join(self, guild):
        bots, humans, ratio = self.bot_human_ratio(guild)
        owner = guild.owner

        log.info(f'[bh:join] {guild!s} -> ratio {len(bots)}b / {len(humans)}h '
                 f'= {ratio:.2}')

        if guild.id in WHITELIST:
            return

        bot_ratio = await self.guild_ratio(guild)
        if ratio > bot_ratio:
            log.info(f'[bh:leave:guild_join] {ratio} > {bot_ratio},'
                     f' leaving {guild!s}')

            explode_bh = ('This guild was classified as a bot collection, '
                          f'josé automatically left. {ratio} > {bot_ratio}')
            try:
                await owner.send(explode_bh)
            except discord.Forbidden:
                await self.fallback(guild, explode_bh)

            return await guild.leave()

        if await self.bot.is_blocked_guild(guild.id):
            blocked_msg = ('Sorry. The guild you added José on is blocked. '
                           'Appeal to the block at the support server'
                           '(Use the invite provided in `j!invite`).')

            try:
                await owner.send(blocked_msg)
            except discord.Forbidden:
                await self.fallback(guild, blocked_msg)

            return await guild.leave()

        welcome = ('Hello, welcome to José!\n'

                   "Discord's API Terms of Service requires me to"
                   " tell you I log\n"

                   'Command usage and errors to a special channel.\n'

                   '**Only commands and errors are logged, no '
                   'messages are logged, ever.**\n'

                   '**Disclaimer:** José is free software maintained by'
                   'the hard work of many volunteers keeping it up. **SPAM '
                   'IS NOT TOLERATED.**')

        try:
            await owner.send(welcome)
        except discord.Forbidden:
            await self.fallback(guild, welcome)

    async def on_member_join(self, member):
        guild = member.guild

        if guild.id in WHITELIST:
            return

        bots, humans, ratio = self.bot_human_ratio(guild)
        bot_ratio = await self.guild_ratio(guild)

        if ratio > bot_ratio:
            log.info(f'[bh:leave:member_join] leaving {guild!r} {guild.id},'
                     f' {ratio} ({len(bots)} / {len(humans)}) > {bot_ratio}')

            bc_msg = ('Your guild became classified as a bot'
                      'collection, josé automatically left.'
                      f'{len(bots)} bots, '
                      f'{len(humans)} humans, '
                      f'{ratio}b/h > {bot_ratio}')

            try:
                await guild.owner.send(bc_msg)
            except discord.Forbidden:
                await self.fallback(guild, bc_msg)

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
