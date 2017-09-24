import logging
import re
import random
import hashlib
import urllib.parse
import datetime
import collections
import time
import json

import discord

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)

RXKCD_ENDPOINT = 'http://0.0.0.0:8080/search'

class Extra(Cog):
    """Extra commands that don't fit in any other cogs."""
    def __init__(self, bot):
        super().__init__(bot)

        self.description_coll = self.config.jose_db['descriptions']

        self.socket_stats = collections.Counter()
        self.sock_start = time.monotonic()

    async def on_socket_response(self, data):
        self.socket_stats[data.get('t')] += 1

    @commands.command()
    async def avatar(self, ctx, person: discord.User = None):
        """Get someone's avatar."""
        if person is None:
            person = ctx.author

        await ctx.send(person.avatar_url.replace('webp', 'png'))

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
            except:
                as_int = -1

            if number == 'rand':
                random_num = random.randint(0, info['num'])
                info = await self.get_json(f'https://xkcd.com/{random_num}/info.0.json')
            elif as_int > 0:
                info = await self.get_json(f'https://xkcd.com/{number}/info.0.json')

        await ctx.send(f'xkcd {info["num"]} => {info["img"]}')

    async def _do_rxkcd(self, ctx, terms):
        async with self.bot.session.post(RXKCD_ENDPOINT, json={'search': terms}) as r:
            if r.status != 200:
                raise self.SayException(f'Got a not good error code: {r.code}')

            data = await r.text()
            data = json.loads(data)
            if not data['success']:
                raise self.SayException(f'XKCD retrieval failed: {data["message"]!r}')

            if len(data['results']) < 1:
                raise self.SayException('No comics found.')

            comic = data['results'][0]
            
            em = discord.Embed(title=f'Relevant XKCD for {terms!r}')
            em.description = f'XKCD {comic["number"]}, {comic["title"]}'
            em.set_image(url=comic['image'])

            await ctx.send(embed=em)

    async def _do_rxkcd_debug(self, ctx):
        async with self.bot.session.post(RXKCD_ENDPOINT, json={'search': 'standards'}) as r:
            await ctx.send(repr(r))
            await ctx.send(await r.text())

    #@commands.command()
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

        query_string = urllib.parse.urlencode({"search_query" : search_term})

        await self.jcoin.pricing(ctx, self.prices['OPR'])

        url = f'http://www.youtube.com/results?{query_string}'

        with ctx.typing():
            html_content = await self.http_get(url)

            future_re = self.loop.run_in_executor(None, re.findall, \
                r'href=\"\/watch\?v=(.{11})', html_content)

            search_results = await future_re

        if len(search_results) < 2:
            await ctx.send("!yt: No results found.")
            return

        await ctx.send(f'http://www.youtube.com/watch?v={search_results[0]}')

    async def set_description(self, user_id, description):
        desc_obj = {
            'id': user_id,
            'description': description,
        }

        if await self.get_description(user_id) is not None:
            await self.description_coll.update_one({'id': user_id}, {'$set': desc_obj})
        else:
            await self.description_coll.insert_one(desc_obj)

    async def get_description(self, user_id):
        dobj = await self.description_coll.find_one({'id': user_id})
        if dobj is None:
            return None
        return dobj['description']

    def mkcolor(self, name):
        colorval = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:6], 16)
        return discord.Colour(colorval)

    def delta_str(self, delta):
        seconds = delta.total_seconds()
        years = seconds / 60 / 60 / 24 / 365.25
        days = seconds / 60 / 60 / 24
        if years >= 1:
            return f'{years:.2f} years'
        else:
            return f'{days:.2f} days'

    @commands.command()
    async def profile(self, ctx, user: discord.Member = None):
        """Get profile cards."""
        if user is None:
            user = ctx.author

        await ctx.trigger_typing()

        em = discord.Embed(title='Profile card', colour=self.mkcolor(user.name))

        if len(user.avatar_url) > 0:
            em.set_thumbnail(url=user.avatar_url)

        em.set_footer(text=f'User ID: {user.id}')

        if user.nick is not None:
            em.add_field(name='Name', value=f'{user.nick} ({user.name})')
        else:
            em.add_field(name='Name', value=user.name)

        description = await self.get_description(user.id)
        if description is not None:
            em.add_field(name='Description', value=description)

        delta = datetime.datetime.now() - user.created_at
        em.add_field(name='Account age', value=f'{self.delta_str(delta)}')

        account = await self.jcoin.get_account(user.id)
        if account is not None:
            guild_rank, global_rank, guild_accounts, all_accounts = await self.jcoin.ranks(user.id, ctx.guild)

            em.add_field(name='JC Rank', value=f'{guild_rank}/{guild_accounts}, '
                                               f'{global_rank}/{all_accounts} globally')

            em.add_field(name='JoséCoin Wallet', value=f'{account["amount"]}JC')
            em.add_field(name='Tax paid', value=f'{account["taxpaid"]}JC')

            try:
                ratio = account['success_steal'] / account['times_stolen']
                ratio = round((ratio * 100), 3)

                em.add_field(name='Stealing', value='{} tries, {} success, ratio of success: {}/steal'.format( \
                    account['times_stolen'], account['success_steal'], ratio))
            except ZeroDivisionError:
                pass

        await ctx.send(embed=em)

    @commands.command()
    async def setdesc(self, ctx, *, description: str = ''):
        """Set your profile card description."""
        description = description.strip()
        if len(description) < 1:
            raise self.SayException('pls put something')

        if len(description) > 300:
            raise self.SayException('3 long 5 me pls bring it down dud')

        await self.set_description(ctx.author.id, description)
        await ctx.ok()

    @commands.command()
    async def sockstats(self, ctx):
        """Event count through the websocket."""
        delta = time.monotonic() - self.sock_start
        minutes = delta / 60
        total = sum(self.socket_stats.values())
        events_minute = round(total / minutes, 2)

        await ctx.send(f'{total} events, {events_minute}/minute:\n{self.socket_stats}')

    @commands.command(hidden=True)
    async def awoo(self, ctx):
        """A weeb made me do this."""
        await ctx.send("https://cdn.discordapp.com/attachments/202055538773721099/257717450135568394/awooo.gif")

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
    async def elixir(self, ctx, *, terms: str):
        """Search through the Elixir documentation.
        
        Powered by https://github.com/lnmds/elixir-docsearch.
        """
        await ctx.trigger_typing()
        try:
            base = self.bot.config.elixir_docsearch
        except AttributeError:
            raise self.SayException('No URL for elixir-docsearch found in configuration.')

        async with self.bot.session.get(f'http://{base}/search', json={'query': terms}) as r:
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
                em.description += f'[{name}](https://hexdocs.pm{entry}) ({score * 100}%)\n'

            await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Extra(bot))
