import logging
import urllib.parse

import discord
from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)


async def custom_getjson(ctx, url: str) -> dict:
    """Get JSON from a website with custom useragent."""
    log.debug('Requesting %s', url)
    resp = await ctx.bot.session.get(url, headers={
        'User-Agent': ctx.cog.USER_AGENT,
    })
    return await resp.json()


class WikiHow(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.API_BASE = 'https://www.wikihow.com/api.php?action=query'
        self.USER_AGENT = 'JoseBot-WikiHowCog/0.1 ' + \
                          '(https://example.com;wikihowcog@ave.zone)'

    async def wh_query(self, ctx, term: str) -> dict:
        log.debug(f'Querying {term}')

        url = f'{self.API_BASE}&generator=search&gsrsearch={term}&prop=' + \
              f'info|images&format=json'

        data = await custom_getjson(ctx, url)
        return data

    @commands.command(aliases=['wh'])
    async def wikihow(self, ctx, *, query: str):
        """Search WikiHow"""
        query = urllib.parse.quote(query)
        await self.jcoin.pricing(ctx, self.prices['API'])

        wh_json = await self.wh_query(ctx, query)
        wh_query = wh_json['query']

        page_count = wh_query["searchinfo"]["totalhits"]
        display_count = page_count if page_count < 5 else 5

        log.debug(f'total results: {page_count}, ' +
                  f'displaying {display_count}')

        if not display_count:
            raise self.SayException('No pages found')

        query_continue = wh_json['query-continue']
        image_name = query_continue['images']['imcontinue']
        image_name = image_name.split("|")[-1]

        image_query_link = f'{self.API_BASE}&titles=File:{image_name}' + \
                           '&prop=imageinfo&iiprop=url&format=json'

        image_json = await custom_getjson(ctx, image_query_link)
        image_data = next(iter(image_json["query"]["pages"].values()))
        image_link = image_data["imageinfo"][0]["url"]

        log.info(f'Image: {image_link}')

        pages = wh_query["pages"].values()
        pages = sorted(pages, key=lambda page: page['counter'], reverse=True)
        pages = pages[:display_count]

        embed_text = []

        for page in pages:
            url = f'https://wikihow.com/{page["title"].replace(" ", "-")}'
            embed_text.append(f'**[{page["title"]}]({url}) '
                              f'({page["counter"]} views)**')

        e = discord.Embed(title='WikiHow results for '
                                f'`"{urllib.parse.unquote(query)}"`',
                          url='https://www.wikihow.com/wikiHowTo?'
                              f'search={query}',
                          description='\n'.join(embed_text))
        e.set_image(url=image_link)
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(WikiHow(bot))

