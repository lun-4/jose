import asyncio
import decimal
import logging

import discord
from discord.ext import commands

JOSE_VERSION = '2.4'

ZERO = decimal.Decimal(0)
INF = decimal.Decimal('inf')

WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
WIDE_MAP[0x20] = 0x3000

log = logging.getLogger(__name__)


class SayException(Exception):
    """Say something using an exception."""
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
        ba = commands.BadArgument
        coins = ctx.bot.get_cog('Coins')
        if not coins:
            raise ba('Coins extension not loaded.')

        if argument.lower() == 'all':
            if ctx.invoked_with in ('steal', 'heist'):
                # this is the member/guild
                target = ctx.args[-1]
            else:
                target = ctx.author

            try:
                account = await coins.get_account(target.id)
            except coins.AccountNotFoundError:
                raise ba(f'Your target `{target}` does not have a'
                         ' JoséCoin account.')

            return account['amount']

        value = decimal.Decimal(argument)
        if value <= ZERO:
            raise ba("You can't input values lower or equal to 0.")
        elif value >= INF:
            raise ba("You can't input values equal or higher to infinity.")

        try:
            value = round(value, 2)
        except:
            raise ba('Rounding failed.')

        # Ensure a taxbank account tied to the guild exists
        await coins.ensure_taxbank(ctx)
        try:
            account = await coins.get_account(ctx.author.id)
        except coins.AccountNotFoundError:
            raise ba("You don't have a JoséCoin account, "
                     f"make one with `j!account`")

        return value


class FuzzyMember(commands.Converter):
    """Fuzzy matching for member objects"""

    async def convert(self, ctx, arg):
        arg = arg.lower()
        ms = ctx.guild.members
        scores = {}
        for m in ms:
            score = 0
            mn = m.name

            # compare against username
            # We give a better score to exact matches
            # than to just "contain"-type matches
            if arg == mn:
                score += 10
            if arg in mn:
                score += 3

            # compare with nickname in a non-throw-exception way
            nick = getattr(m.nick, "lower", "".lower)()
            if arg == nick:
                score += 2
            if arg in nick:
                score += 1

            # we don't want a really big dict thank you
            if score > 0:
                scores[m.id] = score

        try:
            sortedkeys = sorted(
                scores.keys(), key=lambda k: scores[k], reverse=True)
            return sortedkeys[0]
        except IndexError:
            raise commands.BadArgument('No user was found')


class Cog:
    """Main cog base class.

    Provides common functions to cogs.
    """

    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.JOSE_VERSION = JOSE_VERSION

        # so it becomes available for all cogs without needing to import shit
        self.SayException = SayException
        self.prices = {
            'OPR': 0.9,
            'API': 0.65,
            'TRN': '0.022/char',
        }

    def __init_subclass__(cls, **kwargs):
        """Fill in cog metadata about a cog's requirements."""
        requires = kwargs.get('requires', [])

        cls._cog_metadata = {
            'requires': requires,
        }

    async def get_json(self, url: str) -> 'any':
        """Get JSON from a url."""
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

    @property
    def pool(self):
        return self.bot.cogs.get('Config').db


async def shell(command: str) -> str:
    """Execute shell commands."""
    process = await asyncio.create_subprocess_shell(
        command,
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    out, err = map(lambda s: s.decode('utf-8'), await process.communicate())
    return f'{out}{err}'.strip()
