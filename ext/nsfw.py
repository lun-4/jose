import logging
import random
import urllib.parse

import aiohttp
import discord
from discord.ext import commands
from .common import Cog

log = logging.getLogger(__name__)


class BooruError(Exception):
    pass


class BooruProvider:
    url = ''

    @classmethod
    def transform_file_url(cls, url):
        return url

    @classmethod
    def get_author(cls, post):
        return post['author']

    @classmethod
    async def get_posts(cls, bot, tags, *, limit=5):
        tags = urllib.parse.quote(' '.join(tags), safe='')
        async with bot.session.get(f'{cls.url}&limit={limit}&tags={tags}') \
                as resp:
            results = await resp.json()
            if not results:
                return []

            try:
                # e621 sets this to false
                # when the request fails
                if not results.get('success', True):
                    raise BooruError(results.get('reason'))
            except AttributeError:
                # when the thing actually worked and
                # its a list of posts and not a fucking
                # dictionary

                # where am I gonna see good porn APIs?
                pass

            # transform file url
            for post in results:
                post['file_url'] = cls.transform_file_url(post['file_url'])

            return results


class E621Booru(BooruProvider):
    url = 'https://e621.net/post/index.json?'
    url_post = 'https://e621.net/post/show/{0}'


class HypnohubBooru(BooruProvider):
    url = 'http://hypnohub.net/post/index.json?'
    url_post = 'https://hypnohub.net/post/show/{0}'

    @classmethod
    def transform_file_url(cls, url):
        return 'https:' + url.replace('.net//', '.net/')


class GelBooru(BooruProvider):
    url = 'https://gelbooru.com/index.php?page=dapi&s=post&json=1&q=index'
    url_post = 'https://gelbooru.com/index.php?page=post&s=view&id={0}'

    @classmethod
    def get_author(cls, post):
        return post['owner']


class NSFW(Cog):
    async def booru(self, ctx, booru, tags):
        # taxxx
        await self.jcoin.pricing(ctx, self.prices['API'])

        try:
            # grab posts
            posts = await booru.get_posts(ctx.bot, tags)

            if not posts:
                return await ctx.send('Found nothing.')

            # grab random post
            post = random.choice(posts)
            post_id = post.get('id')
            post_author = booru.get_author(post)

            log.info('%d posts from %s, chose %d', len(posts),
                     booru.__name__, post_id)

            tags = (post['tags'].replace('_', '\\_'))[:500]

            # add stuffs
            embed = discord.Embed(title=f'Posted by {post_author}')
            embed.set_image(url=post['file_url'])
            embed.add_field(name='Tags', value=tags)
            embed.add_field(name='URL', value=booru.url_post.format(post_id))

            # hypnohub doesn't have this
            if 'fav_count' in post and 'score' in post:
                embed.add_field(name='Votes/Favorites',
                                value=f"{post['score']} votes, {post['fav_count']} favorites")

            # send
            await ctx.send(embed=embed)
        except BooruError as err:
            await ctx.send(f'Error while fetching posts: `{err!r}`')
        except aiohttp.ClientError as err:
            raise self.SayException(f'Something went wrong. Sorry! `{err!r}`')

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

    @commands.command()
    @commands.is_nsfw()
    async def gelbooru(self, ctx, *tags):
        """Randomly searches Gelbooru for posts."""
        await self.booru(ctx, GelBooru, tags)

    @commands.command()
    @commands.is_nsfw()
    async def penis(self, ctx):
        """get penis from e621 bb"""
        await ctx.invoke(self.bot.get_command('e621'), 'penis')


def setup(bot):
    bot.add_cog(NSFW(bot))
