import logging
import urllib.parse
import decimal

from xml.etree import ElementTree

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)
TAX_PER_CHAR = decimal.Decimal('0.022')


class Translation(Cog):
    """Microsoft's Translation API."""
    def __init__(self, bot):
        super().__init__(bot)
        self.APIROUTE = 'https://api.microsofttranslator.com/V2/Http.svc'
        self.apicfg = self.bot.config.MSFT_TRANSLATION

        # This one is given by azure
        self.subkey = self.apicfg['key']

        self.subkey_headers = {
            'Ocp-Apim-Subscription-Key': self.subkey,
        }

    async def req(self, method, route, qs_dict: dict) -> 'any':
        """Make a request to the translation API."""
        qs = urllib.parse.urlencode(qs_dict)
        url = f'{self.APIROUTE}{route}?{qs}'
        async with self.bot.session.request(method, url,
                                            headers=self.subkey_headers) as r:
            return r

    async def get(self, route: str, qs: dict) -> 'any':
        return await self.req('GET', route, qs)

    async def post(self, route: str, qs: dict) -> 'any':
        return await self.req('POST', route, qs)

    @commands.command()
    async def translist(self, ctx):
        """List all available languages."""
        resp = await self.get('/GetLanguagesForTranslate', {})
        text = await resp.text()
        if resp.status != 200:
            raise self.SayException(f'\N{WARNING SIGN} API '
                                    f'replied {resp.status}')

        root = ElementTree.fromstring(text)
        await ctx.send(f"`{', '.join(list(root.itertext()))}`")

    @commands.command()
    async def translate(self, ctx, to_lang: str, *, sentence: str):
        """Translate from one language to another."""
        to_lang = self.bot.clean_content(to_lang).lower()
        to_lang = to_lang.replace("jp", "ja").replace("zh-CHS", "cn")
        sentence = self.bot.clean_content(sentence)

        tax = len(sentence) * TAX_PER_CHAR
        await self.coins.pricing(ctx, tax)

        # detect language
        resp_detect = await self.get('/Detect', {
            'text': sentence,
        })
        text_detect = await resp_detect.text()
        if resp_detect.status != 200:
            raise self.SayException(f'\N{WARNING SIGN} Detect failed'
                                    f' with {resp_detect.status}')

        root_detect = ElementTree.fromstring(text_detect)
        detected = root_detect.text

        # translate
        resp = await self.get('/Translate', {
            'to': to_lang,
            'text': sentence,
        })

        text = await resp.text()
        if resp.status != 200:
            log.warning('[trans] got a non-200, %r', text)
            raise self.SayException(f'\N{WARNING SIGN} Translation failed'
                                    f' with {resp.status}')

        root = ElementTree.fromstring(text)
        translated = list(root.itertext())[0]
        translated = self.bot.clean_content(translated)

        log.debug('[translate] %r [%s] => %r [%s]',
                  sentence, detected, translated, to_lang)

        res = [
            f'detected language: {detected}',
            f'`{translated}` ({to_lang})',
        ]
        await ctx.send('\n'.join(res))


def setup(bot):
    bot.add_cog(Translation(bot))
