import logging
import asyncio
import time
import random
import collections
import re

import discord
import markovify
from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)
SENTENCE_PRICE = '0.08'

URL_REGEX = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\)'
                       ',]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', re.I)


def make_textmodel(texter, data):
    """Make a text model and insert it into a texter object."""
    texter.model = markovify.NewlineText(data, texter.chain_length,
                                         **texter.model_kwargs)


async def make_texter(texter_id, data, **kwargs):
    """Generate a texter, given its ID and data to work with."""
    texter = Texter(texter_id, **kwargs)
    await texter.fill(data)
    return texter


class TexterFail(Exception):
    """Error representing a failure while generating a Texter."""
    pass


class Texter:
    """Texter - Main texter class.

    This class holds information about a markov chain generator.
    """
    __slots__ = ('loop', 'id', 'refcount', 'chain_length', 'model',
                 'wordcount', 'linecount', 'time_taken', 'model_kwargs')

    def __init__(self, texter_id, **kwargs):
        self.loop = kwargs.pop('loop', None)
        if not self.loop:
            self.loop = asyncio.get_event_loop()

        self.chain_length = kwargs.pop('chain_length', 1)
        self.id = texter_id

        #: internal things
        self.refcount = 1
        self.wordcount = 0
        self.linecount = 0
        self.time_taken = 0

        self.model = None
        self.model_kwargs = kwargs

    def __repr__(self):
        return (f'<Texter id={self.id} '
                f'refcount={self.refcount} wordcount={self.wordcount}>')

    async def fill(self, data):
        """Fill a texter with its text model."""
        t_start = time.monotonic()

        future_textmodel = self.loop.run_in_executor(None, make_textmodel,
                                                     self, data)
        await future_textmodel

        self.wordcount = data.count(' ') + 1
        self.linecount = data.count('\n')

        delta = round((time.monotonic() - t_start) * 1000, 2)
        self.time_taken = delta

        log.info(f"Texter.fill: {self.linecount} lines, "
                 f"{self.wordcount} words, {delta}ms")

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
            if count > 3:
                break
            future_sentence = self.loop.run_in_executor(
                None, self._sentence, char_limit)
            res = await future_sentence
            count += 1

        return str(res)

    def clear(self):
        """
        delete stuff out of the texter
        """
        del self.model, self.refcount, self.chain_length, self.loop


class Speak(Cog):
    """José's markov cog."""

    def __init__(self, bot):
        super().__init__(bot)
        self.text_generators = {}
        self.generating = {}

        self.coll_task = self.bot.loop.create_task(self.coll_task_func())

        self.st_gen_totalms = 1
        self.st_gen_count = 1

        self.st_txc_totalms = 1
        self.st_txc_runs = 1

        self.txstress_semaphore = asyncio.Semaphore(5)

    def __unload(self):
        """Remove all texters from memory"""
        to_del = []
        for texter in self.text_generators.values():
            texter.clear()
            to_del.append(texter.id)

        for tx_id in to_del:
            del self.text_generators[tx_id]

    async def coll_task_func(self):
        """Collect texters every minute."""
        try:
            while True:
                await self.texter_collection()
                await asyncio.sleep(60)
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

            self.st_txc_totalms += delta

            log.info(f'[tx:coll] {amount} -> {amount - cleaned}, {delta}ms')

        self.st_txc_runs += 1

    async def get_messages(self, guild, amount=2000) -> list:
        """fetch messages from a guild. defaults to 2000 messages"""
        channel_id = await self.config.cfg_get(guild, 'speak_channel')
        channel = guild.get_channel(channel_id)
        if channel is None:
            raise TexterFail('Channel to read messages not found, check '
                             'the j!speakchan command(j!help speakchan)')

        self.generating[guild.id] = True
        try:
            messages = []
            async for message in channel.history(limit=amount):

                author = message.author
                if author == self.bot.user or author.bot:
                    continue

                # remove commands
                content = message.clean_content
                if content.startswith('j!'):
                    continue

                # remove messages with speak prefix
                starts_prefix = False

                for prefix in self.bot.config.SPEAK_PREFIXES:
                    if content.startswith(prefix):
                        starts_prefix = True

                if starts_prefix:
                    continue

                messages.append(message.clean_content.strip())

            new_msgs = []
            for clean_content in messages:
                # filter urls out of a message
                content = re.sub(URL_REGEX, '', clean_content)
                content = content.strip()

                if content:
                    new_msgs.append(content)

            self.generating[guild.id] = False
            return new_msgs
        except discord.Forbidden:
            log.info(f'[get_messages] Forbidden from {guild.name}[{guild.id}]')
            self.generating[guild.id] = False
            raise TexterFail("Can't read from the channel, "
                             "setup your permissions!")

    async def get_messages_str(self, guild, amount=2000) -> str:
        """Call get_messages, return a string afterwards"""
        m = await self.get_messages(guild, amount)
        return '\n'.join(m)

    async def new_texter(self, guild, **kwargs):
        guild_messages = await self.get_messages_str(guild)
        if len(guild_messages) < 100:
            raise self.SayException('Selected channel has less than '
                                    '100 characters. (`j!help speakchan`)')

        new_texter = await make_texter(guild.id, guild_messages, **kwargs)

        self.st_gen_totalms += new_texter.time_taken
        self.st_gen_count += 1

        self.text_generators[guild.id] = new_texter
        return new_texter

    async def get_texter(self, guild):
        if guild.id not in self.text_generators:
            await self.new_texter(guild)

        return self.text_generators[guild.id]

    async def sentence_tax(self, ctx, mode='user', recursive=False):
        """Tax someone when they request a sentence.

        Catches transfer errors, logs them, but
        it doesn't raise to the upper scope(calling function).

        Parameters
        ----------
        ctx: context
            Command context
        mode: str
            can be ``"user"`` or ``"txb"``

        Returns
        -------
        None
        """
        account = None
        # quickpatches
        if mode == 'user':
            try:
                account = await self.coins.get_account(ctx.author.id)
            except self.coins.AccountNotFoundError:
                account = None
        elif mode == 'txb':
            try:
                account = await self.coins.get_account(ctx.guild.id)
            except self.coins.AccountNotFoundError:
                account = None
        else:
            raise RuntimeError(f'Sentence tax type not found: {mode}')

        if not account:
            return

        try:
            await self.coins.sink(account['account_id'], SENTENCE_PRICE)
        except self.coins.TransferError as err:
            # we retry, doing the taxbank instead of user
            # or user instead of taxbank

            # this should be called when user or taxbank
            # do not have enough funds to pay.

            # We set the recursive flag
            # so that this function is not called more than once.
            # (or else we would have a very bad day when both user
            # and taxbank have 0 JC)
            if not recursive:
                await self.sentence_tax(ctx, 'txb'
                                        if mode == 'user' else 'user', True)

    async def make_sentence(self, ctx,
                            char_limit=None, priority='user') -> str:
        with ctx.typing():
            try:
                texter = await self.get_texter(ctx.guild)
            except TexterFail as err:
                raise self.SayException('Failed to generate a '
                                        f'texter: `{err.args[0]!r}`')

        await self.sentence_tax(ctx, priority)
        sentence = await texter.sentence(char_limit)

        self.bot.dispatch('markov', ctx)

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
            return

        nick = ctx.me.nick
        if nick is not None:
            nick = f'{nick} '
            prefixes = self.bot.config.SPEAK_PREFIXES + [nick.lower()]
        else:
            prefixes = self.bot.config.SPEAK_PREFIXES

        # ensure we are not working on references
        prefixes = list(prefixes)

        for prefix in list(prefixes):
            modified = prefix.replace(' ', ', ')
            try:
                prefixes.index(modified)
            except ValueError:
                prefixes.append(modified)

        autoreply = False
        cnt = message.content.lower()
        if not any(cnt.startswith(prefix.lower()) for prefix in prefixes):
            # autoreply
            if random.random() > prob:
                return

            disabled = await self.config.cfg_get(ctx.guild,
                                                 'autoreply_disable', [])

            if ctx.channel.id in disabled:
                return
        else:
            log.info('[autoreply:speak_prefix] %s(%d), %s(%d) - %r',
                     message.guild, message.guild.id, message.author,
                     message.author.id, message.content)
            autoreply = True

        if self.generating.get(ctx.guild.id):
            return

        try:
            sentence = await self.make_sentence(ctx, None, 'txb'
                                                if autoreply else 'user')

            self.bot.dispatch('markov_prefixed', ctx)
        except self.SayException as err:
            sentence = f'Failed to generate a sentence: `{err.args[0]!r}`'

        try:
            await ctx.send(sentence)
        except discord.HTTPException:
            # no need to log not permission errors,
            # as this occurs pretty often
            pass

    @commands.command()
    @commands.is_owner()
    async def texclean(self, ctx, amount: int = 1):
        """Clean texters."""
        before = len(self.text_generators)
        t_start = time.monotonic()

        for _ in range(amount):
            await self.texter_collection()

        after = len(self.text_generators)
        t_end = time.monotonic()

        delta = round((t_end - t_start) * 1000, 2)
        await ctx.send(f"`{before} => {after}, cleaned "
                       f"{before-after}, took {delta}ms`")

    @commands.command()
    @commands.is_owner()
    async def ntexter(self, ctx, guild_id: int = None):
        """Create a new texter for a guild, overwrites existing one"""
        if guild_id is None:
            guild_id = ctx.guild.id

        guild = self.bot.get_guild(guild_id)

        # TODO: maybe see if delta is too long and warn?
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
        self.bot.dispatch('markov_command', ctx)
        await ctx.send(sentence)

    @commands.command(hidden=True)
    async def covfefe(self, ctx):
        """covfefe."""
        await ctx.send("Despite the constant negative press covfefe.")

    @commands.command()
    @commands.guild_only()
    async def madlibs(self, ctx, *, inputstr: str):
        """Changes any "---" in the input to a 12-letter generated sentence

        If you see "None" in the resulting text, it means josé
        failed to generate a 12-letter sentence,
        and that can happen by any reason tbh.
        """

        inputstr = inputstr.replace('@e', '@\u200be')
        inputstr = inputstr.replace('@h', '@\u200bh')
        inputstr = self.bot.clean_content(inputstr)

        splitted = inputstr.split()
        if splitted.count('---') < 1:
            await ctx.send(":no_entry_sign: you can't just make "
                           "josé say whatever you want! :no_entry_sign:")
            return

        if splitted.count('---') > 5:
            await ctx.send('too much --- pls')
            return

        res = []

        for word in splitted:
            if word == '---':
                res.append(await self.make_sentence(ctx, 12))
            else:
                res.append(word)

        await ctx.send(' '.join(res))

    async def stress_one(self, ctx, guild):
        """Force a recreation of a texter with big refcount for a guild."""
        await self.txstress_semaphore.acquire()

        try:
            texter = await self.new_texter(guild)

            # go above 5, really.
            # since new_texter can take a lot of time
            texter.refcount = 10
            await ctx.send(f'Success for `{guild!r}[{guild.id}]`')
        except TexterFail:
            await ctx.send(f'Failed for `{guild!r}[{guild.id}]`')
        finally:
            self.txstress_semaphore.release()

    @commands.command()
    @commands.is_owner()
    async def txstress(self, ctx):
        """Stress test texters LUL"""
        t1 = time.monotonic()

        for guild in self.bot.guilds:
            # we can be safe stress_one will acquire its semaphore
            # and not overload everything at the same time.
            self.loop.create_task(self.stress_one(ctx, guild))

        t2 = time.monotonic()
        delta = round((t2 - t1), 2)

        await ctx.send(f'Spawned {len(self.bot.guilds)} tasks'
                       f' in {delta} seconds')

    @commands.command()
    async def txstat(self, ctx):
        """Show statistics about all texters.

         - 'tx gen time' is the time taken to generate one texter.

         - 'txc cycle time' is the time from one cycle of the texter
        garbage collector.
        """
        txg = self.text_generators

        refcounts = collections.Counter()
        for _, texter in txg.items():
            refcounts[texter.refcount] += 1

        res = ['refcount | texters']
        res += [f'{r}        | {txc}' for (r, txc) in refcounts.most_common()]

        res += [
            f'avg tx gen time: {self.st_gen_totalms / self.st_gen_count}'
            f' ms, {self.st_gen_count} generated'
        ]
        res += [
            f'avg txc cycle time: {self.st_txc_totalms / self.st_txc_runs}'
            f' ms, {self.st_txc_runs} runs'
        ]

        res = '\n'.join(res)
        await ctx.send(f'```{res}```')

    @commands.command()
    @commands.is_owner()
    async def alltx(self, ctx):
        """Get info about all loaded texters."""
        em = discord.Embed(colour=discord.Colour.blurple())
        em.description = ''
        for guild_id, texter in self.text_generators.items():
            guild = self.bot.get_guild(guild_id)

            if not guild:
                em.description += '{texter!r} not found\n'
                continue

            em.description += (f'**{guild!s}**, `gid={guild_id} - '
                               f'refcount={texter.refcount}, '
                               f'words={texter.wordcount} '
                               f'lines={texter.linecount}` \n')

        await ctx.send(embed=em)

    @commands.command()
    @commands.guild_only()
    async def curtx(self, ctx):
        """Get information about the current Texter(if any)
        loaded at your guild.
        """
        tx = self.text_generators.get(ctx.guild.id)
        if not tx:
            return await ctx.send('No texter loaded for this guild')

        lines = (f'Refcount: {tx.refcount}\n', f'Words: {tx.wordcount}\n',
                 f'Lines: {tx.linecount}\n')
        await ctx.send(''.join(lines))

    @commands.command()
    @commands.guild_only()
    async def wordcount(self, ctx):
        """Get top 10 of most used words, given the text sample."""
        with ctx.typing():
            messages = await self.get_messages(ctx.guild)
            processed = ' '.join(messages).replace('\n', ' ')
            count = collections.Counter(
                (w for w in processed.split(' ') if len(w) > 4))

        common = count.most_common(10)
        res = '\n'.join(
            [f'`{word!r}: {count} times`' for (word, count) in common])
        await ctx.send(res)


def setup(bot):
    bot.add_cog(Speak(bot))
