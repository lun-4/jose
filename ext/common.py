import discord

JOSE_VERSION = '2.3'

WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
WIDE_MAP[0x20] = 0x3000

class SayException(Exception):
    pass

class Cog:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.JOSE_VERSION = JOSE_VERSION

        # so it becomes available for all cogs without needing to import shit
        self.SayException = SayException
        self.prices = {
            'OPR': 0.8,
            'API': 0.6,
        }

    def get_name(self, user_id):
        return str(self.bot.get_user(user_id))

    async def get_json(self, url):
        async with self.bot.session.get(url) as resp:
            try:
                return await resp.json()
            except Exception as err:
                raise SayException(f'Error parsing JSON: {err!r}')

    async def http_get(self, url):
        async with self.bot.session.get(url) as resp:
            return await resp.text()

    @property
    def config(self):
        return self.bot.cogs.get('Config')

    @property
    def jcoin(self):
        return self.bot.cogs.get('Coins')
