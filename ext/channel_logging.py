import logging
import asyncio
import collections

from discord.ext import commands

from .common import Cog
from joseconfig import PACKET_CHANNEL, LEVELS

log = logging.getLogger(__name__)

# pls no ratelimit
LOGGING_PERIOD = 1

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
                    n = 1900
                    chunks = [msg[i:i+n] for i in range(0, len(msg), n)]
                    for chunk in chunks:
                        p.add_line(chunk)

            channel = self.channels[level]
            if not channel:
                print(f'[chdump] getting channel = {channel!r}')
            else:
                for page in p.pages:
                    self.loop.create_task(channel.send(page))

            # empty queue
            self.queue[level] = []

    def load(self):
        """Fill handler with channel information
        and attach itself to common loggers.
        """
        for level, channel_id in LEVELS.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                self.channels[level] = channel
                print(f'[ch:load] {level} -> {channel_id} -> {channel!s}')
            else:
                print(f'[ch:load] {level} -> {channel_id} -> NOT FOUND')

        self.dumper_task = self.loop.create_task(self.dumper())
        self.attach()

    def unload(self):
        """Detach from attached loggers.
        Cancels the dumper task.
        """
        self.detach()

        if self.dumper_task is not None:
            self.dumper_task.cancel()

    def all_loggers(self, func):
        """Invoke a function to all attachable loggers."""
        func(log, self)
        for logger_name in LOGGERS_TO_ATTACH:
            logger = logging.getLogger(logger_name)
            func(logger, self)

    def attach(self):
        """Attach to loggers."""
        self.all_loggers(logging.Logger.addHandler)

    def detach(self):
        """Detach from loggers."""
        self.all_loggers(logging.Logger.removeHandler)

    async def dumper(self):
        """Does a log dump every `LOGGING_PERIOD` seconds."""
        try:
            while True:
                self.dump()
                await asyncio.sleep(LOGGING_PERIOD)
        except asyncio.CancelledError:
            log.info('[channel_logging] dumper got cancelled')
        except:
            log.exception('dumper failed')

    def emit(self, record):
        """Queues the log record to be sent on the next available window."""
        if self.channels is None:
            log.warning('No channels are setup')
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
                                                    f'```py\n{payload!r}\n```')

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

    # unload if already loaded
    if getattr(bot, 'channel_handler', None) is not None:
        bot.channel_handler.unload()

    bot.channel_handler = ChannelHandler(bot)
    if bot.is_ready():
        bot.channel_handler.load()
