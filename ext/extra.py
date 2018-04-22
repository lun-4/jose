import logging
import re
import random
import urllib.parse
import collections
import time
import json

import discord

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)

RXKCD_ENDPOINT = 'http://0.0.0.0:8080/search'
MEME_DISCRIMS = [
    '0420', '2600', '1337', '0666', '0000', '1234', '5678', '4321'
]


def is_palindrome(string):
    return string == string[::-1]


def is_repeating(string):
    for i in range(1, int(len(string) / 2) + 1):
        main_substring = string[:i]

        # get all other substrings
        chunks = [
            string[n:n + i] for n in range(0, len(string), 1 if not i else i)
        ]

        # check if selected main substring matches
        # all other substrings
        repeating = all(main_substring in chunk for chunk in chunks)
        if repeating:
            return True

    return False


# Borrowed from https://rosettacode.org/wiki/Miller%E2%80%93Rabin_primality_test#Python:_Proved_correct_up_to_large_N
# Thanks Rosetta Code!


def _try_composite(a, d, n, s):
    if pow(a, d, n) == 1:
        return False
    for i in range(s):
        if pow(a, 2**i * d, n) == n - 1:
            return False
    return True  # n  is definitely composite


def is_prime(n, _precision_for_huge_n=16):
    if n in _known_primes or n in (0, 1):
        return True
    if any((n % p) == 0 for p in _known_primes):
        return False
    d, s = n - 1, 0
    while not d % 2:
        d, s = d >> 1, s + 1
    # Returns exact according to http://primes.utm.edu/prove/prove2_3.html
    if n < 1373653:
        return not any(_try_composite(a, d, n, s) for a in (2, 3))
    if n < 25326001:
        return not any(_try_composite(a, d, n, s) for a in (2, 3, 5))
    if n < 118670087467:
        if n == 3215031751:
            return False
        return not any(_try_composite(a, d, n, s) for a in (2, 3, 5, 7))
    if n < 2152302898747:
        return not any(_try_composite(a, d, n, s) for a in (2, 3, 5, 7, 11))
    if n < 3474749660383:
        return not any(
            _try_composite(a, d, n, s) for a in (2, 3, 5, 7, 11, 13))
    if n < 341550071728321:
        return not any(
            _try_composite(a, d, n, s) for a in (2, 3, 5, 7, 11, 13, 17))
    # otherwise
    return not any(
        _try_composite(a, d, n, s)
        for a in _known_primes[:_precision_for_huge_n])


_known_primes = [2, 3]
_known_primes += [x for x in range(5, 1000, 2) if is_prime(x)]


async def is_nice_discrim(member):
    discrim_s = member.discriminator
    discrim = int(discrim_s)
    if discrim_s in MEME_DISCRIMS:
        return True

    if discrim < 20:
        return True

    if is_palindrome(discrim_s):
        return True

    if is_repeating(discrim_s):
        return True

    if is_prime(discrim):
        return True

    return False


class Extra(Cog, requires=['config']):
    """Extra commands that don't fit in any other cogs."""

    def __init__(self, bot):
        super().__init__(bot)

        self.socket_stats = collections.Counter()
        self.sock_start = time.monotonic()

    async def on_socket_response(self, data):
        self.socket_stats[data.get('t')] += 1

    @commands.command()
    async def avatar(self, ctx, *, person: discord.User = None):
        """Get someone's avatar."""
        if person is None:
            person = ctx.author

        url = person.avatar_url_as(static_format='png')

        await ctx.send(url)

    @commands.command()
    async def xkcd(self, ctx, number: str = ''):
        """Get XKCD shit."""

        await self.jcoin.pricing(ctx, self.prices['API'])
        info = None

        with ctx.typing():
            url = 'https://xkcd.com/info.0.json'
            info = await self.get_json(url)

            try:
                as_int = int(number)
            except (TypeError, ValueError):
                as_int = -1

            if number == 'rand':
                random_num = random.randint(0, info['num'])
                info = await self.get_json(f'https://xkcd.com/{random_num}/'
                                           'info.0.json')
            elif as_int > 0:
                info = await self.get_json(f'https://xkcd.com/{number}/'
                                           'info.0.json')

        await ctx.send(f'xkcd {info["num"]} => {info["img"]}')

    async def _do_rxkcd(self, ctx, terms):
        async with self.bot.session.post(RXKCD_ENDPOINT,
                                         json={'search': terms}) as r:
            if r.status != 200:
                raise self.SayException(f'Got a not good error code: {r.code}')

            data = await r.text()
            data = json.loads(data)
            if not data['success']:
                raise self.SayException('XKCD retrieval failed:'
                                        f' {data["message"]!r}')

            if len(data['results']) < 1:
                raise self.SayException('No comics found.')

            comic = data['results'][0]

            em = discord.Embed(title=f'Relevant XKCD for {terms!r}')
            em.description = f'XKCD {comic["number"]}, {comic["title"]}'
            em.set_image(url=comic['image'])

            await ctx.send(embed=em)

    async def _do_rxkcd_debug(self, ctx):
        async with self.bot.session.post(
                RXKCD_ENDPOINT, json={'search': 'standards'}) as r:
            await ctx.send(repr(r))
            await ctx.send(await r.text())

    # @commands.command()
    async def rxkcd(self, ctx, *, terms: str):
        """Get a Relevant XKCD.

        Made with https://github.com/adtac/relevant-xkcd
        """
        try:
            if '-debug' in terms:
                return await self._do_rxkcd_debug(ctx)

            async with ctx.typing():
                await self._do_rxkcd(ctx, terms)
        except Exception as err:
            raise self.SayException(f'Error while requesting data: `{err!r}`')

    @commands.command(aliases=['yt'])
    async def youtube(self, ctx, *, search_term: str):
        """Search youtube."""
        log.info(f'[yt] {ctx.author} {search_term!r}')

        query_string = urllib.parse.urlencode({"search_query": search_term})

        await self.jcoin.pricing(ctx, self.prices['OPR'])

        url = f'http://www.youtube.com/results?{query_string}'

        with ctx.typing():
            html_content = await self.http_get(url)

            future_re = self.loop.run_in_executor(
                None, re.findall, r'href=\"\/watch\?v=(.{11})', html_content)

            search_results = await future_re

        if len(search_results) < 2:
            await ctx.send("!yt: No results found.")
            return

        await ctx.send(f'http://www.youtube.com/watch?v={search_results[0]}')

    @commands.command()
    async def sockstats(self, ctx):
        """Event count through the websocket."""
        delta = time.monotonic() - self.sock_start
        minutes = delta / 60
        total = sum(self.socket_stats.values())
        events_minute = round(total / minutes, 2)

        await ctx.send(f'{total} events, {events_minute}/minute:'
                       f'\n{self.socket_stats}')

    @commands.command(hidden=True)
    async def awoo(self, ctx):
        """A weeb made me do this."""
        await ctx.send("https://cdn.discordapp.com/attachments/"
                       "202055538773721099/257717450135568394/awooo.gif")

    @commands.command()
    @commands.guild_only()
    async def presence(self, ctx, member: discord.Member = None):
        """Shows your status/presence info in José's view."""
        if member is None:
            member = ctx.member

        status = member.status
        try:
            game_name = member.game.name
        except AttributeError:
            game_name = '<no game>'

        game_name = game_name.replace('@', '@\u200b')

        game_name = await commands.clean_content().convert(ctx, game_name)
        await ctx.send(f'status: `{status}`, game: `{game_name}`')

    @commands.command()
    @commands.is_owner()
    async def elixir(self, ctx, *, terms: str):
        """Search through the Elixir documentation.

        Powered by https://github.com/lnmds/elixir-docsearch.
        """
        await ctx.trigger_typing()
        try:
            base = self.bot.config.elixir_docsearch
        except AttributeError:
            raise self.SayException('No URL for elixir-docsearch'
                                    ' found in configuration.')

        async with self.bot.session.get(f'http://{base}/search',
                                        json={'query': terms}) as r:
            if r.status != 200:
                raise self.SayException(f'{r.status} is not 200, rip.')

            res = await r.json()
            if len(res) == 0:
                raise self.SayException('No results found.')

            res = res[:5]
            em = discord.Embed(colour=discord.Colour.blurple())
            em.description = ''
            for (entry, score) in res:
                name = entry.split('/')[-1].replace('.html', '')
                em.description += (f'[{name}](https://hexdocs.pm{entry}) '
                                   f'({score * 100}%)\n')

            await ctx.send(embed=em)

    @commands.command()
    async def excuse(self, ctx):
        """Give an excuse.

        http://pages.cs.wisc.edu/~ballard/bofh/
        """
        async with self.bot.session.get('http://pages.cs.wisc.edu'
                                        '/~ballard/bofh/excuses') as resp:
            data = await resp.text()
            lines = data.split('\n')
            line = random.choice(lines)
            await ctx.send(f'`{line}`')

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def nicediscrim(self, ctx):
        """ONLY GET NICE DISCRIM.

        This is a very expensive operation
        to do, so it has a 1/10s ratelimit per-guild

        Factors of a nice discrim:
         - some meme discrims like '0420' OR
         - below 20 OR
         - is a palindrome OR
         - has a pattern with itself OR
         - is a prime
        """
        e = discord.Embed(title='nice discrims')
        lines = []

        for m in ctx.guild.members:
            if await is_nice_discrim(m):
                lines.append(m.mention)

        e.description = ' '.join(lines)
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Extra(bot))
