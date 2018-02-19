import time
import random
import sys
import os
import datetime
import logging
import asyncio

import psutil
import discord
from discord.ext import commands

from .common import Cog, shell


FEEDBACK_CHANNEL_ID = 290244095820038144

OAUTH_URL = 'https://discordapp.com/oauth2/authorize?permissions=379968&scope=bot&client_id=202586824013643777'
SUPPORT_SERVER = 'https://discord.gg/5ASwg4C'
log = logging.getLogger(__name__)


class Basic(Cog):
    """Basic commands."""
    def __init__(self, bot):
        super().__init__(bot)
        self.support_inv = SUPPORT_SERVER
        self.process = psutil.Process(os.getpid())

    @commands.command(aliases=['p'])
    async def ping(self, ctx):
        """Ping.

        Meaning of the data:
         - rtt: time taken to send a message in discord.

         - gateway: time taken to send a HEARTBEAT
            packet and receive an HEARTBEAT ACK in return.

        None values may be shown if josé did not update the data.
        """

        t1 = time.monotonic()
        m = await ctx.send('pinging...')
        t2 = time.monotonic()

        rtt = (t2 - t1) * 1000
        gw = self.bot.latency * 1000
        await m.edit(content=f'rtt: `{rtt:.1f}ms`, gateway: `{gw:.1f}ms`')

    @commands.command(aliases=['rand'])
    async def random(self, ctx, n_min: int, n_max: int):
        """Get a random number."""
        if n_min < -1e100 or n_max > 1e100:
            return await ctx.send('Your values are outside the range `[-1e100, 1e100]`')

        if n_min > n_max:
            await ctx.send("`min > max` u wot")
            return

        n_rand = random.randint(n_min, n_max)
        await ctx.send(f"from {n_min} to {n_max} I go {n_rand}")

    @commands.command(aliases=['choose', 'choice'])
    async def pick(self, ctx, *choices: commands.clean_content):
        """Pick a random element."""
        choices = set(choices)
        if len(choices) <= 1:
            return await ctx.send("dude what")
        choices = list(choices)

        await ctx.send(random.choice(choices))

    @commands.command()
    async def version(self, ctx):
        """Show current josé version"""
        pyver = '%d.%d.%d' % (sys.version_info[:3])
        head_id = await shell('git rev-parse --short HEAD')
        branch = await shell('git rev-parse --abbrev-ref HEAD')

        await ctx.send(f'`José v{self.JOSE_VERSION} git:{branch}-{head_id} '
                       f'py:{pyver} d.py:{discord.__version__}`')

    @commands.command()
    async def uptime(self, ctx):
        """Show uptime"""
        sec = round(time.time() - self.bot.init_time)

        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        await ctx.send(f'Uptime: **`{d} days, {h} hours, '
                       f'{m} minutes, {s} seconds`**')

    @commands.command()
    async def stats(self, ctx):
        """Statistics."""
        em = discord.Embed(title='Statistics')

        # get memory usage
        mem_bytes = self.process.memory_full_info().rss
        mem_mb = round(mem_bytes / 1024 / 1024, 2)

        cpu_usage = round(self.process.cpu_percent() / psutil.cpu_count(), 2)

        em.add_field(name='Memory / CPU usage',
                     value=f'`{mem_mb}MB / {cpu_usage}% CPU`')

        channels = sum((1 for c in self.bot.get_all_channels()))

        em.add_field(name='Guilds', value=f'{len(self.bot.guilds)}')
        em.add_field(name='Channels', value=f'{channels}')

        gay_chans = sum(1 for c in self.bot.get_all_channels()
                        if 'gay' in c.name.lower())
        em.add_field(name='Gaynnels', value=gay_chans)

        em.add_field(name='Texters',
                     value=f'{len(self.bot.cogs["Speak"].text_generators)}/'
                     f'{len(self.bot.guilds)}')

        member_count = sum((g.member_count for g in self.bot.guilds))
        em.add_field(name='Members', value=member_count)

        humans = sum(1 for m in self.bot.get_all_members() if not m.bot)
        unique_humans = sum(1 for c in self.bot.users)
        em.add_field(name='human/unique humans',
                     value=f'`{humans}, {unique_humans}`')

        await ctx.send(embed=em)

    @commands.command()
    async def about(self, ctx):
        """Show stuff."""

        em = discord.Embed(title='José')
        em.add_field(name='About', value='José is a generic-purpose '
                     'bot (with some complicated features)')

        appinfo = await self.bot.application_info()
        owner = appinfo.owner
        em.add_field(name='Owner',
                     value=f'{owner.mention}, {owner}, (`{owner.id}`)')

        em.add_field(name='Guilds',
                     value=f'{len(self.bot.guilds)}')

        await ctx.send(embed=em)

    @commands.command()
    async def feedback(self, ctx, *, feedback: str):
        """Sends feedback to a special channel.

        Feedback replies will be sent to the
        same channel you used the command on.

        Replies can take any time.
        """

        author = ctx.author
        channel = ctx.channel
        guild = ctx.guild

        em = discord.Embed(title='', colour=discord.Colour.magenta())
        em.timestamp = datetime.datetime.utcnow()
        em.set_footer(text='Feedback Report')
        em.set_author(name=str(author), icon_url=author.avatar_url or
                      author.default_avatar_url)

        em.add_field(name="Feedback", value=feedback)
        em.add_field(name="Guild", value=f'{guild.name} [{guild.id}]')
        em.add_field(name="Channel", value=f'{channel.name} [{channel.id}]')

        feedback_channel = self.bot.get_channel(FEEDBACK_CHANNEL_ID)
        if feedback_channel is None:
            await ctx.send('feedback channel not found we are fuckd')
            return

        await feedback_channel.send(embed=em)
        await ctx.ok()

    @commands.command(name='feedback-reply', aliases=['freply'])
    @commands.is_owner()
    async def feedback_reply(self, ctx, channel_id: int, *, message: str):
        """Sends a feedback reply to a specified channel."""
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return await ctx.send("Can't find specified "
                                  "channel! Please try again.")

        embed = discord.Embed(colour=discord.Color.magenta(),
                              description=message)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)

        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text='Feedback Reply')

        await channel.send(embed=embed)
        await ctx.ok()

    @commands.command()
    async def clist(self, ctx, cog_name: str):
        """Search for all commands that were declared by a cog.

        This is case sensitive.
        """
        matched = [cmd.name for cmd in self.bot.commands
                   if cmd.cog_name == cog_name]

        if len(matched) < 1:
            await ctx.send('No commands found')
            return

        _res = ' '.join(matched)
        await ctx.send(f'```\n{_res}\n```')

    @commands.command()
    async def invite(self, ctx):
        """Get invite URL"""
        em = discord.Embed(title='Invite stuff')
        em.add_field(name='OAuth URL', value=OAUTH_URL)
        em.add_field(name='Support Server', value=SUPPORT_SERVER)
        await ctx.send(embed=em)

    @commands.command()
    async def source(self, ctx):
        """Source code:tm:"""
        await ctx.send('https://github.com/lnmds/jose')


def setup(bot):
    bot.add_cog(Basic(bot))
