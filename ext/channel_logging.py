import logging
import asyncio
import collections
import json
import zlib

from discord.ext import commands

from .common import Cog
from joseconfig import PACKET_CHANNEL, LEVELS

log = logging.getLogger(__name__)


LOGGING_PERIOD = 5

LOGGERS_TO_ATTACH = [
    'discord',
    'ext',
    '__main__',
]


class ChannelHandler(logging.Handler):
    """Log handler for discord channels.

    This logging handler will setup logging so that your bot's logs go
    to a discord channel.

    Edit LEVELS to match your preferred channel IDs.

    This handler will only send logs from its internal queue every 5 seconds,
    to prevent ratelimiting.

    Attributes
    ----------
    bot: bot
        The bot instance.
    loop: `asyncio event loop`
        The bot's event loop the handler will do things upon.
    channels: dict or None
        Relates logging levels to channel IDs.
    dumper_task: `asyncio.Task` or None
        Task that cleans the queues every 5 seconds.
    queue: `collections.defaultdict(list)`
        Queue of logs.
    """
    def __init__(self, bot):
        super().__init__()
        log.info('[channel_handler] Starting...')
        self.bot = bot
        self.loop = bot.loop
        self.channels = {}
        self.dumper_task = None
        self.queue = collections.defaultdict(list)

        self.root_logger = logging.getLogger(None)

        self._special_packet_channel = None

    def dump(self):
        """Dump all queued log messages into their respective channels."""
        if len(self.queue) < 1:
            return

        for level, messages in self.queue.items():
            if len(messages) < 1:
                continue

            # TODO: maybe remove ChannelHandler.queue
            #  and offload it all to the paginator
            p = commands.Paginator(prefix='', suffix='')
            for msg in messages:
                try:
                    p.add_line(msg)
                except RuntimeError:
                    log.info('Log message made 2k+, paginator failed')

            channel = self.channels[level]
            if not channel:
                print(f'[chdump] getting channel = {channel!r}')
            else:
                for page in p.pages:
                    self.loop.create_task(channel.send(page))

            # empty queue
            self.queue[level] = []

    def do_ready(self):
        for level, channel_id in LEVELS.items():
            channel = self.bot.get_channel(channel_id)
            self.channels[level] = channel
            print(f'[ch:ready] {level} -> {channel_id} -> {channel!s}')

        self.dumper_task = self.loop.create_task(self.dumper())
        self.attach()

    def attach(self):
        """Attach to the loggers in ``LOGGERS_TO_ATTACH``"""
        log.addHandler(self)
        for logger_name in LOGGERS_TO_ATTACH:
            logger = logging.getLogger(logger_name)
            logger.addHandler(self)

    def detach(self):
        """Detach from the loggers, disables the dumper task too"""
        if self.dumper_task is not None:
            self.dumper_task.cancel()

        log.removeHandler(self)
        for logger_name in LOGGERS_TO_ATTACH:
            logger = logging.getLogger(logger_name)
            logger.removeHandler(self)

    async def dumper(self):
        """Does a log dump every `LOGGING_PERIOD` seconds."""
        try:
            while True:
                self.dump()
                await asyncio.sleep(LOGGING_PERIOD)
        except asyncio.CancelledError:
            log.info('[channel_logging] dumper got cancelled')

    def emit(self, record):
        """Queues the log record to be sent on the next available window."""
        if self.channels is None:
            # No channels setup, this is logging BEFORE client is ready.
            return

        log_level = record.levelno
        formatted = self.format(record)

        # because commands like eval can fuck the
        # codeblock up
        formatted = self.bot.clean_content(formatted)

        log_message = f'\n**`[{record.levelname}] [{record.name}]`** `{formatted}`'
        if log_level in (logging.WARNING, logging.ERROR):
            log_message = f'\n**`[{record.levelname}] [{record.name}]`**\n```py\n{formatted}\n```'

        self.queue[log_level].append(log_message)


class Logging(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self._special_packet_channel = None

    async def on_ready(self):
        self._special_packet_channel = self.bot.get_channel(PACKET_CHANNEL)

    async def on_socket_response(self, payload):
        """Convert msg to JSON and check for specific
        OP codes"""
        if self._special_packet_channel is None:
            return

        op, t = payload['op'], payload['t']
        if op != 0:
            return

        if t in ('WEBHOOKS_UPDATE', 'PRESENCES_REPLACE'):
            log.info('GOT A WANTED PACKET!!')
            await self._special_packet_channel.send('HELLO I GOT A GOOD'
                                                    ' PACKET PLS SEE '
                                                    f'```py\n{j}\n```')

    @commands.command()
    @commands.is_owner()
    async def dumplogs(self, ctx):
        log.info('dumping!')
        await ctx.send('mk')
        self.bot.channel_handler.dump()

    @commands.command()
    @commands.is_owner()
    async def logerr(self, ctx):
        log.error('EXAMPLE ERROR')
        await ctx.send('logged')

    @commands.command()
    @commands.is_owner()
    async def err(self, ctx):
        raise Exception('THIS IS A TEST ERROR!!!!!')

    @commands.command()
    @commands.is_owner()
    async def test_2k(self, ctx):
        log.info('a' * 2000)


def setup(bot):
    bot.add_cog(Logging(bot))

    # Remove the handler if it already exists
    if getattr(bot, 'channel_handler', None) is not None:
        bot.channel_handler.detach()

    bot.channel_handler = ChannelHandler(bot)
    if bot.is_ready():
        bot.loop.create_task(bot.channel_handler.do_ready())
