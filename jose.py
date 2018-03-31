import logging
import random
import time
import asyncio
import pathlib
import importlib
import collections

import discord
import aiohttp

import uvloop

from discord.ext import commands

import joseconfig as config
from ext.common import SayException

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

log = logging.getLogger(__name__)

extensions = [
    'channel_logging',  # loading at start to get the logger to run
    'config',
    'admin',
    'exec',
    'state',
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
    "u can't give me this and think i can do something",
    'succ',
    "i'm not a god, fix your args",
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

    async def status(self, flag):
        await self.success(flag)

    async def err(self, msg):
        await self.send(f'\N{POLICE CARS REVOLVING LIGHT} {msg}')

    def send(self, content='', **kwargs):
        # FUCK EACH AND @EVERYONE OF YOU
        # specially mary and gerd

        # i hope this saves my life, forever.
        nc = self.bot.clean_content(content, normal_send=True)
        return super().send(nc, **kwargs)


class JoseBot(commands.Bot):
    """Main bot subclass."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init_time = time.time()
        self.config = config
        self.session = aiohttp.ClientSession()

        #: Exceptions that will be simplified
        #   to WARN logging instead of ERROR logging
        self.simple_exc = [SayException]

        #: used by ext.channel_logging
        self.channel_handlers = []

        #: blocking stuff
        self.block_coll = None
        self.block_cache = {}

    async def on_ready(self):
        """Bot ready handler"""
        log.info(f'Logged in! {self.user!s}')

    async def is_blocked(self, user_id: int, key: str = 'user_id') -> bool:
        """Returns if something blocked to use José. Uses cache"""
        if user_id in self.block_cache:
            return self.block_cache[user_id]

        blocked = await self.block_coll.find_one({key: user_id})
        is_blocked = bool(blocked)
        self.block_cache[user_id] = is_blocked

        return is_blocked

    async def is_blocked_guild(self, guild_id: int) -> bool:
        """Returns if a guild is blocked to use José. Uses cache"""
        return await self.is_blocked(guild_id, 'guild_id')

    def clean_content(self, content: str, **kwargs) -> str:
        """Make a string clean of mentions and not breaking codeblocks"""
        content = str(content)

        # only escape codeblocks when we are not normal_send
        # only escape single person pings when we are not normal_send
        if not kwargs.get('normal_send', False):
            content = content.replace('`', r'\`')
            content = content.replace('<@', '<@\u200b')
            content = content.replace('<#', '<#\u200b')

        # always escape role pings (@everyone) and @here
        content = content.replace('<@&', '<@&\u200b')
        content = content.replace('@here', '@\u200bhere')
        content = content.replace('@everyone', '@\u200beveryone')

        return content

    async def on_command(self, ctx):
        """Log command usage"""
        # thanks dogbot ur a good
        content = ctx.message.content
        content = self.clean_content(content)

        author = ctx.message.author
        guild = ctx.guild
        checks = [c.__qualname__.split('.')[0] for c in ctx.command.checks]
        location = '[DM]' if isinstance(ctx.channel, discord.DMChannel) else \
                   f'[Guild {guild.name} {guild.id}]'

        log.info('%s [cmd] %s(%d) "%s" checks=%s', location, author, author.id,
                 content, ','.join(checks) or '(none)')

    async def on_error(self, event_method, *args, **kwargs):
        # TODO: analyze current exception
        # and simplify the logging to WARN
        # if it is on self.simple_exc
        log.exception('Got an error while running the %s event', event_method)

    async def on_message(self, message):
        if message.author.bot:
            return

        author_id = message.author.id
        if await self.is_blocked(author_id):
            return

        if message.guild is not None:
            guild_id = message.guild.id

            if await self.is_blocked_guild(guild_id):
                return

        ctx = await self.get_context(message, cls=JoseContext)
        await self.invoke(ctx)

    def load_extension(self, name: str):
        """wrapper for the Bot.load_extension"""
        log.debug(f'[load:loading] {name}')
        t_start = time.monotonic()
        super().load_extension(name)
        t_end = time.monotonic()

        delta = round((t_end - t_start) * 1000, 2)
        log.info(f'[load] {name} took {delta}ms')

    def add_jose_cog(self, cls: 'class'):
        """Add a cog but load its requirements first."""
        requires = cls._cog_metadata.get('requires', [])

        log.debug('requirements for %s: %r', cls, requires)
        if not requires:
            log.debug(f'no requirements for {cls}')
        for _req in requires:
            req = f'ext.{_req}'
            if req in self.extensions:
                log.debug('loading %r from requirements', req)
                self.load_extension(req)
            else:
                log.debug('%s is already loaded', req)

        # We instantiate here because
        # instantiating on the old add_cog
        # is exactly the cause of the problem
        cog = cls(self)
        super().add_cog(cog)

    def load_all(self):
        """Load all extensions in the extensions folder.
        
        Thanks FrostLuma for code!
        """

        for extension in extensions:
            self.load_extension(f'ext.{extension}')

        path = pathlib.Path('ext/')
        files = path.glob('**/*.py')

        for fileobj in files:
            if fileobj.stem == '__init__':
                name = str(fileobj)[:-12]
            else:
                name = str(fileobj)[:-3]

            name = name.replace('/', '.')
            module = importlib.import_module(name)

            if not hasattr(module, 'setup'):
                # ignore extensions that do not have a setup() function
                continue

            if name in extensions:
                log.debug(f'ignoring {name}')

            self.load_extension(name)


async def get_prefix(bot, message) -> list:
    """Get the preferred list of prefixes for a determined guild/dm."""
    if not message.guild:
        return bot.config.prefix

    config_cog = bot.get_cog('Config')
    if not config_cog:
        log.warning('config cog not found')
        return [config.prefix]

    custom = await config_cog.cfg_get(message.guild, "prefix")
    if custom == bot.config.prefix:
        return custom

    # sort backwards due to the command parser taking the first match
    return sorted([bot.config.prefix, custom], reverse=True)


def main():
    """Main entry point"""
    jose = JoseBot(
        command_prefix=get_prefix,
        description='henlo dis is jose',
        pm_help=None,
        owner_id=getattr(config, 'owner_id', None),
    )

    jose.load_all()
    jose.run(config.token)


if __name__ == '__main__':
    main()
