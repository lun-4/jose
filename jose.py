import logging
import random
import time
import sys
import traceback
import asyncio

import discord
import aiohttp

import uvloop

from discord.ext import commands

import joseconfig as config
from ext.common import SayException

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)7s] [%(name)s] %(message)s')

log = logging.getLogger(__name__)

extensions = [
    'config', 'admin', 'exec', 'pipupdates',
    'coins', 'coins+',
    'basic',
    'gambling',
    'speak',
    'math',
    'datamosh',
    'memes',
    'extra',
    'stars',
    'stats',
    'mod', 'botcollection',
    'channel_logging',
    'playing', 'sub',
    'nsfw', 'heist', 'midi',
    'lottery',
]

CHECK_FAILURE_PHRASES = [
    'br?',
    'u died [real] [Not ClickBait]',
    'rEEEEEEEEEEEEE',
    'not enough permissions lul',
    'you sure you can run this?',
]

BAD_ARG_MESSAGES = [
    'dude give me the right thing',
    'u can\'t give me this and think i can do something',
    'succ',
    'i\'m not a god, fix your args',
    'why. just why',
]


class JoseContext(commands.Context):
    @property
    def member(self):
        if self.guild is None:
            return None
        return self.guild.get_member(self.author.id)

    async def ok(self):
        try:
            await self.message.add_reaction('👌')
        except discord.Forbidden:
            await self.message.channel.send('ok')

    async def not_ok(self):
        try:
            await self.message.add_reaction('❌')
        except discord.Forbidden:
            await self.message.channel.send('not ok')

    async def success(self, flag):
        if flag:
            await self.ok()
        else:
            await self.not_ok()


class JoseBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_time = time.time()
        self.config = config
        self.session = aiohttp.ClientSession()
        self.simple_exc = [SayException]
        self.channel_handler = None

        # reeeeee dont query mongo every message god damn it
        self.block_cache = {}

    async def hell(self):
        """That happened. Yeah."""
        await asyncio.sleep(3)

        if self.channel_handler is not None:
            self.channel_handler.do_ready()

    async def on_ready(self):
        log.info(f'Logged in! {self.user!s}')
        self.loop.create_task(self.hell())

    async def is_blocked(self, user_id: int):
        """Returns If a user is blocked to use José. Uses cache"""
        if user_id in self.block_cache:
            return self.block_cache[user_id]

        blocked = await self.block_coll.find_one({'user_id': user_id})
        is_blocked = bool(blocked)
        self.block_cache[user_id] = is_blocked

        return is_blocked

    async def is_blocked_guild(self, guild_id: int):
        """Returns if a guild is blocked to use José. Uses cache"""
        if guild_id in self.block_cache:
            return self.block_cache[guild_id]

        blocked = await self.block_coll.find_one({'guild_id': guild_id})
        is_blocked = bool(blocked)
        self.block_cache[guild_id] = is_blocked

        return is_blocked

    def clean_content(self, content):
        content = content.replace('`', '\'')
        content = content.replace('@', '@\u200b')
        content = content.replace('&', '&\u200b')
        content = content.replace('<#', '<#\u200b')
        return content

    async def on_command(self, ctx):
        # thanks dogbot ur a good
        content = ctx.message.content
        content = self.clean_content(content)

        author = ctx.message.author
        guild = ctx.guild
        checks = [c.__qualname__.split('.')[0] for c in ctx.command.checks]
        location = '[DM]' if isinstance(ctx.channel, discord.DMChannel) else \
                   f'[Guild {guild.name} {guild.id}]'

        log.info('%s [cmd] %s(%d) "%s" checks=%s', location, author,
                 author.id, content, ','.join(checks) or '(none)')

    async def on_command_error(self, ctx, error):
        message = ctx.message
        content = self.clean_content(message.content)

        if isinstance(error, commands.errors.CommandInvokeError):
            orig = error.original
            if isinstance(orig, SayException):
                arg0 = orig.args[0]
                log.warning('SayException: %s[%d] %s %r => %r', ctx.guild,
                            ctx.guild.id, ctx.author, content, arg0)

                await ctx.send(arg0)
                return

            tb = ''.join(traceback.format_exception(
                type(error.original), error.original,
                error.original.__traceback__
            ))

            if isinstance(orig, tuple(self.simple_exc)):
                log.error(f'Errored at {content!r}'
                          f' from {ctx.author!s}\n{orig!r}')
            else:
                log.error(f'Errored at {content!r} from {ctx.author!s}\n{tb}')

            if isinstance(orig, self.cogs['Coins'].TransferError):
                await ctx.send(f'JoséCoin error: `{error.original!r}`')
                return

            b = '\N{NEGATIVE SQUARED LATIN CAPITAL LETTER B}'
            await ctx.send(f'{b}ot machine {b}roke\n '
                           f'```py\n{error.original!r}\n```')
        elif isinstance(error, commands.errors.BadArgument):
            await ctx.send('bad argument — '
                           f'{random.choice(BAD_ARG_MESSAGES)} - {error!s}')
        elif isinstance(error, commands.errors.CheckFailure):
            await ctx.send('check failed — '
                           f'{random.choice(CHECK_FAILURE_PHRASES)}')
        elif isinstance(error, commands.errors.CommandOnCooldown):
            # retry = round(error.retry_after, 2)
            # await ctx.send(f'Command on cooldown, wait `{retry}` seconds')
            pass

    async def on_message(self, message):
        author_id = message.author.id

        # fucking spam, i hate it >:c
        if message.author.bot:
            return

        if await self.is_blocked(author_id):
            return

        try:
            guild_id = message.guild.id

            if await self.is_blocked_guild(guild_id):
                return
        except AttributeError:
            # in a DM
            pass

        ctx = await self.get_context(message, cls=JoseContext)
        await self.invoke(ctx)

async def get_prefix(bot, message):
    if message.guild is None:
        return bot.config.prefix

    if message.guild.id == 216292020371718146:
        return ['j%']

    config = bot.get_cog('Config')
    if config is None:
        log.warning('config cog not found')
        return ['j!']

    custom = await config.cfg_get(message.guild, "prefix")
    if custom == bot.config.prefix:
        return custom

    # sort backwards due to the command parser taking the first match
    return sorted([bot.config.prefix, custom], reverse=True)

jose = JoseBot(
    command_prefix=get_prefix,
    description='henlo dis is jose',
    pm_help=None
)

if __name__ == '__main__':
    for extension in extensions:
        try:
            t_start = time.monotonic()
            jose.load_extension(f'ext.{extension}')
            t_end = time.monotonic()
            delta = round((t_end - t_start) * 1000, 2)
            log.info(f"[load] {extension} took {delta}ms")
        except Exception as err:
            log.error(f'Failed to load {extension}', exc_info=True)
            sys.exit(1)

    jose.run(config.token)
