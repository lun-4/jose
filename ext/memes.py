import random
import string
import urllib.parse
import asyncio

import discord
import pymongo

from discord.ext import commands
from .common import Cog, WIDE_MAP

MAX_MEME_NAME = 30

RI_TABLE = {
    '0': ':zero:',
    '1': ':one:',
    '2': ':two:',
    '3': ':three:',
    '4': ':four:',
    '5': ':five:',
    '6': ':six:',
    '7': ':seven:',
    '8': ':eight:',
    '9': ':nine:',

    '.': ':record_button:',
    '!': ':exclamation:',
    '?': ':question:',
    '+': ':heavy_plus_sign:',
    '-': ':heavy_minus_sign:',
}

# implement letters
RI_STR = '🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿'

RI_TABLE.update({letter:RI_STR[string.ascii_lowercase.find(letter)] for \
    letter in string.ascii_lowercase})


class Memes(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.memes_coll = self.config.jose_db['memes']
        self.urban_cache = {}

    async def add_meme(self, name, value, author_id, uses=0, nsfw=None):
        """Add a meme to the database."""

        meme = {
            'name': name,
            'value': value,
            'uses': uses,
            'author_id': author_id,
            'nsfw': nsfw,
        }

        await self.memes_coll.insert_one(meme)

    async def get_meme(self, name):
        """Get a meme from the database."""
        return await self.memes_coll.find_one({'name': name})

    async def delete_meme(self, name):
        """Remove a meme from the database."""
        return await self.memes_coll.delete_many({'name': name})

    async def update_meme(self, new_meme):
        """Update a new meme into the database."""

        await self.memes_coll.update_one({'name': new_meme['name']}, {'$set': new_meme})

    async def search_memes(self, name):
        """Get a list of memes that have names that are close to the name given."""

        cur = self.memes_coll.find({
            'name': {
                '$regex': name,
            }
        })

        return [m['name'] for m in await cur.to_list(length=None)]

    @commands.group(aliases=['m'], invoke_without_command=True)
    async def meme(self, ctx):
        """The meme database."""
        await ctx.send("`j!help m`")

    @meme.command(name='add')
    async def add(self, ctx, name: str, *, value: str):
        """Add a meme."""
        name, value = name.strip(), value.strip()

        if len(name) > MAX_MEME_NAME:
            await ctx.send('2 long 5 me')
            return

        meme = await self.get_meme(name)
        if meme is not None:
            await ctx.send('meme already exists')
            return

        await self.add_meme(name, value, ctx.author.id, 0, ctx.channel.is_nsfw())
        await ctx.ok()

    @meme.command(name='get')
    async def get(self, ctx, *, name: str):
        """Retrieve a meme.

        Doesn't allow NSFW memes(memes created in NSFW channels) to be shown
        in non-NSFW channels
        """
        name = name.strip()

        meme = await self.get_meme(name)
        if meme is None:
            probables = await self.search_memes(name)
            if len(probables) > 0:
                await ctx.send(f'Didn\'t you mean `{",".join(probables)}`')
                return
            await ctx.send('Meme not found.')
            return

        nsfw_meme = meme.get('nsfw', False)
        if nsfw_meme and not ctx.channel.is_nsfw():
            await ctx.send('Can\'t show NSFW memes in a non-NSFW channel')
            return

        meme['uses'] += 1
        await self.update_meme(meme)
        await ctx.send(meme['value'])

    @meme.command()
    async def rm(self, ctx, name: str):
        """Remove a meme."""
        name = name.strip()

        meme = await self.get_meme(name)
        if meme is None:
            await ctx.send('Meme not found')
            return

        owner = (await self.bot.application_info()).owner
        authorized = (meme.get('author_id') == ctx.author.id) or (ctx.author == owner)
        if not authorized:
            await ctx.send('Unauthorized')
            return

        await self.delete_meme(name)
        await ctx.ok()

    @meme.command()
    async def rename(self, ctx, name: str, new_name: str):
        """Rename a meme's name."""
        name, new_name = name.strip(), new_name.strip()

        meme = await self.get_meme(name)
        if meme is None:
            await ctx.send('Meme not found')
            return

        new_name_meme = await self.get_meme(new_name)
        if new_name_meme is not None:
            await ctx.send('New name already used.')
            return

        await self.delete_meme(meme['name'])
        await self.add_meme(new_name, meme['value'], meme.get('author_id'), meme['uses'], meme['nsfw'])
        await ctx.send(f'Renamed {meme["name"]!r} to {new_name!r}')

    @meme.command()
    async def owner(self, ctx, name: str):
        """Get a meme's owner (who created it)."""
        name = name.strip()

        meme = await self.get_meme(name)
        if meme is None:
            await ctx.send('Meme not found')
            return

        await ctx.send(f'`{name}` was made by {self.get_name(meme.get("author_id"))}')

    @meme.command()
    async def count(self, ctx):
        """Amount of memes in the database."""
        amnt = await self.memes_coll.count()
        await ctx.send(f'amount: {amnt}')

    @meme.command()
    async def top(self, ctx):
        """Shows the top 15 most used memes."""
        res = []
        cur = self.memes_coll.find({}).sort('uses', pymongo.DESCENDING)

        for (idx, meme) in enumerate(await cur.to_list(length=15)):
            res.append(f'[{idx}] {meme["name"]} used {meme["uses"]} times')

        _joined = "\n".join(res)
        await ctx.send(f'```\n{_joined}\n```')

    @meme.command()
    async def used(self, ctx, name: str):
        """Shows the amount of times this meme was used."""
        name = name.strip()

        meme = await self.get_meme(name)
        if meme is None:
            await ctx.send('Meme not found')
            return

        await ctx.send(f'`{meme["name"]}` => {meme["uses"]} times')

    @meme.command()
    async def see(self, ctx, owner: discord.User, page: int = 0):
        """See memes made by someone."""
        cur = self.memes_coll.find({'author_id': owner.id})

        from_owner = [m['name'] for m in await cur.to_list(length=None)]

        if len(from_owner) < 1:
            await ctx.send("No memes found.")
            return

        page_slice = from_owner[page * 50:(page + 1) * 50]

        res = len(from_owner), len(page_slice), ', '.join(page_slice)
        report = f'Showing {res[0]}[{res[1]} in page],\nMemes: {res[2]}'
        await ctx.send(report)

    @meme.command()
    async def rand(self, ctx):
        """Get a random meme."""
        total = await self.memes_coll.count()
        rand_idx = random.randint(0, total - 1)

        cur = self.memes_coll.find()
        async for meme in cur.limit(-1).skip(rand_idx):
            await ctx.send(f'{meme["name"]}: {meme["value"]}')

    @meme.command()
    async def search(self, ctx, term: str):
        """Search for memes"""
        term = term.strip()
        if len(term) < 1:
            await ctx.send('lul')
            return

        memes = await self.search_memes(term)
        if len(memes) < 1:
            await ctx.send('No memes found')
            return

        await ctx.send(f'```\n{",".join(memes)}\n```')

    @commands.command(aliases=['fw'])
    async def fullwidth(self, ctx, *, text: str):
        """Convert text to full width."""
        if len(text.strip()) <= 0:
            return

        await ctx.send(text.translate(WIDE_MAP))

    @commands.command()
    async def ri(self, ctx, *, inputstr: str):
        """Convert text to Regional Indicators."""
        inputstr = inputstr.strip().lower()
        l_inputstr = len(inputstr)
        if l_inputstr < 1 or l_inputstr > 1995:
            await ctx.send('lul')
            return

        inputstr = list(inputstr)

        for (index, char) in enumerate(inputstr):
            if char in RI_TABLE:
                inputstr[index] = f'{RI_TABLE[char]}\u200b'

        res = ''.join(inputstr)
        await ctx.send(res)

    @commands.command(hidden=True)
    async def pupper(self, ctx):
        await ctx.send('http://i.imgur.com/9Le8rW7.jpg :sob:')

    @commands.command(name='8ball')
    async def _8ball(self, ctx):
        """8ball lul"""
        answer = random.choice([
            'Yes',
            'No',
            'Maybe',
            'Potentially',
            'Answer hazy',
            'Only in your dreams',
            'Ask later',
        ])

        await ctx.send(f'**{ctx.author.name}**, :8ball: said {answer}.')

    @commands.command(hidden=True)
    async def br(self, ctx):
        """br?"""
        await ctx.send('br?')

    @commands.command()
    async def urban(self, ctx, *, term: str):
        """Search for a word in the Urban Dictionary."""

        # cache :DDDDDDDDD
        if term in self.urban_cache:
            definition = self.urban_cache[term]
            return await ctx.send(f'```\n{term!r}:\n{definition}\n```')

        await self.jcoin.pricing(ctx, self.prices['API'])

        urban_url = f'https://api.urbandictionary.com/v0/define?term={urllib.parse.quote(term)}'

        content = await self.get_json(urban_url)
        c_list = content['list']

        if len(c_list) < 1:
            raise self.SayException('No results found')

        definition = c_list[0]['definition']
        self.urban_cache[term] = definition

        await ctx.send(f'```\n{term!r}:\n{definition}\n```')

    @commands.command(hidden=True)
    async def ejaculate(self, ctx):
        """PUMPE THE MOOSCLES YIIIS"""
        await ctx.send('https://www.youtube.com/watch?v=S6UqgjaBt4w')

    @commands.command()
    @commands.is_owner()
    async def blink(self, ctx, *, text: str):
        m = await ctx.send(text)
        for i in range(10):
            if i % 2 == 0:
                await m.edit(content=f'**{text}**')
            else:
                await m.edit(content=f'{text}')
            await asyncio.sleep(2)

    @commands.command()
    async def neko(self, ctx):
        """Posts a random neko picture."""
        api_url = 'http://nekos.life/api/neko'

        response = await self.get_json(api_url)
        image_url = response['neko']

        embed = discord.Embed(color=discord.Color(0xf84a6e))
        embed.set_image(url=image_url)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Memes(bot))
