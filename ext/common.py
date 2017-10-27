import asyncio
import decimal

import discord
from discord.ext import commands

JOSE_VERSION = '2.3'

ZERO = decimal.Decimal(0)
INF = decimal.Decimal('inf')

WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
WIDE_MAP[0x20] = 0x3000


class SayException(Exception):
    pass


class GuildConverter(commands.Converter):
    """Convert the name of a guild to
    a Guild object."""
    async def convert(self, ctx, arg):
        bot = ctx.bot

        try:
            guild_id = int(arg)
        except ValueError:
            def is_guild(g):
                return arg.lower() == g.name.lower()
            guild = discord.utils.find(is_guild, bot.guilds)

            if guild is None:
                raise commands.BadArgument('Guild not found')
            return guild

        guild = bot.get_guild(guild_id)
        if guild is None:
            raise commands.BadArgument('Guild not found')
        return guild


class CoinConverter(commands.Converter):
    """Does simple checks to the value being given.

    Also checks if the user has an account
    """
    async def convert(self, ctx, argument):
        cf = commands.CheckFailure

        value = decimal.Decimal(argument)
        if value <= ZERO:
            raise cf("You can't input values lower or equal to 0.")
        elif value >= INF:
            raise cf("You can't input values lower of equal to infinity.")

        try:
            value = round(value, 3)
        except:
            raise cf('Rounding failed.')

        coins = ctx.bot.get_cog('Coins')
        if not coins:
            return value

        # Ensure a taxbank account tied to the guild exists
        await coins.ensure_taxbank(ctx)

        account = await coins.get_account(ctx.author.id)
        if not account:
            raise cf("You don't have a JoséCoin account, "
                     "make one with `{ctx.bot.prefix}account`")

        return value


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

    @property
    def coins(self):
        return self.bot.cogs.get('Coins')


async def shell(command: str):
    process = await asyncio.create_subprocess_shell(
        command,
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    out, err = map(lambda s: s.decode('utf-8'), await process.communicate())
    return f'{out}{err}'.strip()
