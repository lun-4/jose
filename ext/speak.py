import logging
import asyncio
import time
import random
import collections

import discord
import markovify
from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)


def make_textmodel(texter, data):
    texter.model = markovify.NewlineText(data, texter.chain_length)


async def make_texter(chain_length, data, texter_id):
    texter = Texter(texter_id, chain_length)
    await texter.fill(data)
    return texter


class TexterFail(Exception):
    pass


class Texter:
    """Texter - Main texter class.

    This class holds information about a markov chain generator.
    """
    __slots__ = ('loop', 'id', 'refcount', 'chain_length', \
        'model', 'wordcount', 'linecount', 'time_taken')

    def __init__(self, texter_id, chain_length=1, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self.id = texter_id
        self.refcount = 1
        self.wordcount = 0
        self.linecount = 0

        self.chain_length = chain_length
        self.loop = loop
        self.model = None

        #: Time taken to make this texter
        self.time_taken = 0

    def __repr__(self):
        return f'<Texter refcount={self.refcount} wordcount={self.wordcount}>'

    async def fill(self, data):
        """Fill a texter with its text model."""
        t_start = time.monotonic()

        future_textmodel = self.loop.run_in_executor(None, make_textmodel, self, data)
        await future_textmodel

        self.wordcount = data.count(' ') + 1
        self.linecount = data.count('\n')

        delta = round((time.monotonic() - t_start) * 1000, 2)
        self.time_taken = delta

        log.info(f"Texter.fill: {self.linecount} lines, {self.wordcount} words, {delta}ms")

    def _sentence(self, char_limit):
        """Get a sentence from a initialized texter."""
        text = 'None'
        if char_limit is not None:
            text = self.model.make_short_sentence(char_limit)
        else:
            text = self.model.make_sentence()

        return text

    async def sentence(self, char_limit=None):
        """Get a sentence from a initialized texter."""
        if self.refcount <= 4:
            # max value refcount can be is 5
            self.refcount += 1

        res = None
        count = 0
        while res is None:
            if count > 3: break
            future_sentence = self.loop.run_in_executor(None, self._sentence, char_limit)
            res = await future_sentence
            count += 1

        return str(res)

    def clear(self):
        del self.model, self.refcount, self.chain_length, self.loop

class Speak(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.text_generators = {}
        self.generating = {}

        self.coll_task = self.bot.loop.create_task(self.coll_task_func())

        self.st_gen_totalms = 1
        self.st_gen_count = 1

        self.st_txc_totalms = 1
        self.st_txc_runs = 1

    def __unload(self):
        """Remove all texters from memory"""
        to_del = []
        for tx in self.text_generators.values():
            tx.clear()
            to_del.append(tx.id)

        for tx_id in to_del:
            del self.text_generators[tx_id]

    async def coll_task_func(self):
        try:
            while True:
                await self.texter_collection()
                await asyncio.sleep(120)
        except asyncio.CancelledError:
            pass

    async def texter_collection(self):
        """Free memory by collecting unused Texters."""
        amount = len(self.text_generators)
        if amount < 1:
            return

        t_start = time.monotonic()
        cleaned = 0

        for texter in list(self.text_generators.values()):
            if texter.refcount < 1:
                texter.clear()
                cleaned += 1
                del self.text_generators[texter.id]
            else:
                texter.refcount -= 1

        t_end = time.monotonic()

        if cleaned > 0:
            delta = round((t_end - t_start) * 1000, 2)

            self.st_txc_runs += 1
            self.st_txc_totalms += delta

            log.info(f'[tx:coll] {amount} -> {amount - cleaned}, {delta}ms')

    async def get_messages(self, guild, amount=2000) -> list:
        channel_id = await self.config.cfg_get(guild, 'speak_channel')
        channel = guild.get_channel(channel_id)
        if channel is None:
            raise TexterFail('Channel to read messages not found, use "j!help speakchan"?')

        self.generating[guild.id] = True
        try:
            messages = []
            async for message in channel.history(limit=amount):
                author = message.author
                if author == self.bot.user:
                    continue

                if author.bot:
                    continue

                content = message.clean_content
                if content.startswith('j!'):
                    continue

                messages.append(message.clean_content)

            self.generating[guild.id] = False
            return messages
        except discord.Forbidden:
            log.info(f'[get_messages] Forbidden from {guild.name}[{guild.id}]')
            self.generating[guild.id] = False
            raise TexterFail("Can't read from the channel, setup your permissions!")

    async def get_messages_str(self, guild, amount=2000):
        m = await self.get_messages(guild, amount)
        return '\n'.join(m)

    async def new_texter(self, guild):
        guild_messages = await self.get_messages_str(guild)
        new_texter = await make_texter(1, guild_messages, guild.id)

        self.st_txc_totalms += new_texter.time_taken
        self.st_txc_runs += 1

        self.text_generators[guild.id] = new_texter

    async def get_texter(self, guild):
        if guild.id not in self.text_generators:
            await self.new_texter(guild)

        return self.text_generators[guild.id]

    async def make_sentence(self, ctx, char_limit=None):
        with ctx.typing():
            try:
                texter = await self.get_texter(ctx.guild)
            except TexterFail as err:
                raise self.SayException(f'Failed to generate a texter: `{err.args[0]!r}`')

        sentence = await texter.sentence(char_limit)
        return sentence

    async def on_message(self, message):
        ctx = await self.bot.get_context(message)
        if message.author.bot:
            return

        if not isinstance(ctx.channel, discord.TextChannel):
            return

        if await self.bot.is_blocked(message.author.id):
            return

        if await self.bot.is_blocked_guild(message.guild.id):
            return

        prob = await self.config.cfg_get(ctx.guild, 'autoreply_prob')
        if prob is None:
            log.warning('[autoreply] how can autoreply_prob be none??')
            return

        force = False
        for prefix in self.bot.config.SPEAK_PREFIXES:
            if message.content.startswith(prefix):
                log.info('[autoreply:speak_prefix] %s(%d), %s(%d) - %r', \
                    message.guild, message.guild.id, message.author, message.author.id, message.content)
                force = True

        if not force:
            if random.random() > prob:
                return

        if self.generating.get(ctx.guild.id):
            return

        sentence = await self.make_sentence(ctx)
        await ctx.send(sentence)

    @commands.command()
    @commands.is_owner()
    async def texclean(self, ctx, amount: int = 1):
        """Clean texters."""
        before = len(self.text_generators)
        t_start = time.monotonic()

        for i in range(amount):
            await self.texter_collection()

        after = len(self.text_generators)
        t_end = time.monotonic()

        delta = round((t_end - t_start) * 1000, 2)
        await ctx.send(f"`{before} => {after}, cleaned {before-after}, took {delta}ms`")

    @commands.command()
    @commands.is_owner()
    async def ntexter(self, ctx, guild_id: int = None):
        """Create a new texter for a guild, overwrites existing one"""
        if guild_id is None:
            guild_id = ctx.guild.id

        guild = self.bot.get_guild(guild_id)
        t1 = time.monotonic()
        await self.new_texter(guild)
        t2 = time.monotonic()

        delta = round((t2 - t1), 2)
        await ctx.send(f'Took {delta} seconds loading texter.')

    @commands.command(aliases=['spt'])
    @commands.guild_only()
    async def speaktrigger(self, ctx):
        """Force your Texter to say a sentence.
        
        If the texter is still being generated, this command
        does nothing while it isn't completly generated.
        """
        if self.generating.get(ctx.guild.id):
            return

        sentence = await self.make_sentence(ctx)
        await ctx.send(sentence)

    @commands.command(hidden=True)
    async def covfefe(self, ctx):
        """covfefe."""
        await ctx.send("Despite the constant negative press covfefe.")

    @commands.command(aliases=['jw'])
    @commands.guild_only()
    async def jwormhole(self, ctx):
        """lul wormhole"""
        res = await self.make_sentence(ctx)
        await ctx.send(f'<@127296623779774464> wormhole send {res}')

    @commands.command()
    @commands.guild_only()
    async def madlibs(self, ctx, *, inputstr: str):
        """Changes any "---" in the input to a 12-letter generated sentence"""

        inputstr = inputstr.replace('@everyone', '@\u200beveryone')
        inputstr = inputstr.replace('@here', '@\u200bhere')

        splitted = inputstr.split()
        if splitted.count('---') < 1:
            await ctx.send(":no_entry_sign: you can't just make josé say whatever you want! :no_entry_sign:")
            return

        if splitted.count('---') > 5:
            await ctx.send("thats a .......... lot")
            return

        res = []

        for word in splitted:
            if word == '---':
                res.append(await self.make_sentence(ctx, 12))
            else:
                res.append(word)

        await ctx.send(' '.join(res))

    @commands.command()
    @commands.is_owner()
    async def txstress(self, ctx):
        """Stress test texters LUL"""
        t1 = time.monotonic()
        async def create_tx(guild):
            try:
                return await self.new_texter(guild)
            except TexterFail:
                await ctx.send(f'Failed for `{guild!s}[{guild.id}]`')
        for guild in self.bot.guilds:
            await create_tx(guild)
        t2 = time.monotonic()

        delta = round((t2 - t1), 2)
        await ctx.send(f'Generated {len(txs)} texters in {delta} seconds')

    @commands.command()
    async def txstat(self, ctx):
        """Show statistics about all texters"""
        tg = self.text_generators

        refcounts = collections.Counter()
        for gid, tx in tg.items():
            refcounts[tx.refcount] += 1

        res = ['refcount | texters']
        res += [f'{r}        | {txc}' for (r, txc) in refcounts.most_common()]
        res = '\n'.join(res)
        await ctx.send(f'```{res}```')

    @commands.command()
    @commands.is_owner()
    async def alltx(self, ctx):
        """Get info about all loaded texters."""
        em = discord.Embed(colour=discord.Colour.blurple())
        em.description = ''
        for guild_id, tx in self.text_generators.items():
            guild = self.bot.get_guild(guild_id)
            em.description += f'**{guild!s}**, gid={guild_id} - `refcount={tx.refcount}, words={tx.wordcount} lines={tx.linecount}`\n'

        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Speak(bot))
