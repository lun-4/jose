import subprocess
import time
import random
import sys
import os
import datetime

import psutil
import discord

from discord.ext import commands

from .common import Cog

FEEDBACK_CHANNEL_ID = 290244095820038144

OAUTH_URL = 'https://discordapp.com/oauth2/authorize?permissions=379968&scope=bot&client_id=202586824013643777'
SUPPORT_SERVER = 'https://discord.gg/5ASwg4C'

class Basic(Cog):
    """Basic commands."""
    def __init__(self, bot):
        super().__init__(bot)
        self.process = psutil.Process(os.getpid())

    @commands.command(aliases=['p'])
    async def ping(self, ctx):
        """Ping."""
        t1 = time.monotonic()
        m = await ctx.send('pinging...')
        t2 = time.monotonic()
        delta = round((t2 - t1) * 1000, 2)
        await m.edit(content=f'`{delta}ms`')

    @commands.command(aliases=['rand'])
    async def random(self, ctx, n_min: int, n_max: int):
        """Get a random number."""
        if n_min > n_max:
            await ctx.send("`min > max` u wot")
            return

        n_rand = random.randint(n_min, n_max)
        await ctx.send(f"from {n_min} to {n_max} I go {n_rand}")

    @commands.command(aliases=['choose', 'choice'])
    async def pick(self, ctx, *choices: commands.clean_content):
        """Pick a random element."""
        if len(choices) < 1:
            await ctx.send("dude what")
            return

        await ctx.send(random.choice(choices))

    @commands.command()
    async def version(self, ctx):
        """Show current josé version"""
        pyver = '%d.%d.%d' % (sys.version_info[:3])
        do = lambda cmd: subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        head_id = do('git rev-parse --short HEAD')
        branch = do('git rev-parse --abbrev-ref HEAD')

        await ctx.send(f'`José v{self.JOSE_VERSION} git:{branch}-{head_id} py:{pyver} d.py:{discord.__version__}`')

    @commands.command()
    async def uptime(self, ctx):
        """Show uptime"""
        sec = round(time.time() - self.bot.init_time)

        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        await ctx.send(f'Uptime: **`{d} days, {h} hours, {m} minutes, {s} seconds`**')

    @commands.command()
    async def stats(self, ctx):
        """Statistics."""
        em = discord.Embed(title='Statistics')

        # get memory usage
        mem_bytes = self.process.memory_full_info().rss
        mem_mb = round(mem_bytes / 1024 / 1024, 2)

        cpu_usage = round(self.process.cpu_percent() / psutil.cpu_count(), 2)

        em.add_field(name='Memory / CPU usage', value=f'`{mem_mb}MB / {cpu_usage}% CPU`')

        channels = sum([len(g.channels) for g in self.bot.guilds])

        em.add_field(name='Guilds', value=f'{len(self.bot.guilds)}')
        em.add_field(name='Channels', value=f'{channels}')
        em.add_field(name='Texters', value=f'{len(self.bot.cogs["Speak"].text_generators)}/{len(self.bot.guilds)}')
        em.add_field(name='Members', value=len(list(self.bot.get_all_members())))

        humans = [m for m in self.bot.get_all_members() if not m.bot]
        em.add_field(name='human/unique humans', value=f'`{len(humans)}, {len(set(humans))}`')

        await ctx.send(embed=em)

    @commands.command()
    async def feedback(self, ctx, *, feedback: str):
        """Sends feedback to a special channel."""

        author = ctx.author
        channel = ctx.channel
        guild = ctx.guild

        em = discord.Embed(title='', colour=discord.Colour.magenta())
        em.timestamp = datetime.datetime.now()
        em.set_footer(text='Feedback Report')
        em.set_author(name=str(author), icon_url=author.avatar_url or \
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

    @commands.command()
    async def clist(self, ctx, cog_name: str):
        """Search for all commands that were declared by a cog.
        
        This is case sensitive.
        """ 
        matched = [cmd.name for cmd in self.bot.commands if cmd.cog_name == cog_name]

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

def setup(bot):
    bot.add_cog(Basic(bot))
