import logging
import random
import urllib.parse

import aiohttp
import discord
from discord.ext import commands
from .common import Cog

log = logging.getLogger(__name__)


class BooruProvider:
    url = ''

    @classmethod
    def transform_file_url(cls, url):
        return url

    @classmethod
    async def get_posts(cls, bot, tags, *, limit=5):
        tags = urllib.parse.quote(' '.join(tags), safe='')
        async with bot.session.get(f'{cls.url}?limit={limit}&tags={tags}') as resp:
            results = await resp.json()

            # transform file url
            for post in results:
                post['file_url'] = cls.transform_file_url(post['file_url'])

            return results


class E621Booru(BooruProvider):
    url = 'https://e621.net/post/index.json'


class HypnohubBooru(BooruProvider):
    url = 'http://hypnohub.net/post/index.json'

    @classmethod
    def transform_file_url(cls, url):
        return 'https:' + url.replace('.net//', '.net/')


class NSFW(Cog):
    async def booru(self, ctx, booru, tags):
        # taxxx
        await self.jcoin.pricing(ctx, self.prices['API'])

        try:
            # grab posts
            posts = await booru.get_posts(ctx.bot, tags)
            log.info('Grabbed %d posts from %s.', len(posts), booru.__name__)

            if not posts:
                return await ctx.send('Found nothing.')

            # grab random post
            post = random.choice(posts)
            tags = (post['tags'].replace('_', '\\_'))[:500]

            # add stuffs
            embed = discord.Embed(title=f'Posted by {post["author"]}')
            embed.set_image(url=post['file_url'])
            embed.add_field(name='Tags', value=tags)

            # hypnohub doesn't have this
            if 'fav_count' in post and 'score' in post:
                embed.add_field(name='Votes/Favorites', value=f"{post['score']} votes, {post['fav_count']} favorites")

            # send
            await ctx.send(embed=embed)
        except aiohttp.ClientError:
            await ctx.send('Something went wrong. Sorry!')

    @commands.command()
    @commands.is_nsfw()
    async def e621(self, ctx, *tags):
        """Randomly searches e621 for posts."""
        async with ctx.typing():
            await self.booru(ctx, E621Booru, tags)

    @commands.command(aliases=['hh'])
    @commands.is_nsfw()
    async def hypnohub(self, ctx, *tags):
        """Randomly searches Hypnohub for posts."""
        async with ctx.typing():
            await self.booru(ctx, HypnohubBooru, tags)


def setup(bot):
    bot.add_cog(NSFW(bot))
