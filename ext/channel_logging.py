import logging
import asyncio
import time

import discord
from discord.ext import commands

from .common import Cog
from joseconfig import PACKET_CHANNEL, LEVELS

log = logging.getLogger(__name__)
LOGLEVEL = logging.DEBUG
LOGGER_SILENCE = ['discord', 'websockets']


# copied from https://github.com/FrostLuma/Mousey
class DiscordHandler(logging.Handler):
    """
    A custom logging handler which sends records to a Discord webhook.

    Messages are queued internally and only sent every 5 seconds to avoid waiting due to ratelimits.

    Parameters
    ----------
    webhook : discord.Webhook
        The webhook the logs will be sent to
    level : Optional[int]
        The level this logger logs at
    loop : Optional[asyncio.AbstractEventLoop]
        The loop which the handler will run on

    Attributes
    ----------
    loop : asyncio.AbstractEventLoop
        The loop the handler runs on
    closed : bool
        Whether this handler is closed or not
    """

    def __init__(self, webhook: discord.Webhook, *, level=None, loop=None):
        super().__init__(level)

        self.webhook = webhook
        self.loop = loop = loop or asyncio.get_event_loop()

        self.closed = False

        self._buffer = []

        self._last_emit = 0
        self._can_emit = asyncio.Event()

        self._emit_task = loop.create_task(self.emitter())

    def emit(self, record):
        if record.levelno != self.level:
            return  # only log the handlers level to the handlers channel, not above

        msg = self.format(record).replace('\N{GRAVE ACCENT}', '\N{MODIFIER LETTER GRAVE ACCENT}')

        if self.level in (logging.WARNING, logging.ERROR):
            chunks = (msg[x:x + 1989] for x in range(0, len(msg), 1989))

            paginator = commands.Paginator(prefix='```py\n', suffix='```')
            for chunk in chunks:
                paginator.add_line(chunk)

            for page in paginator.pages:
                self._buffer.append(page)
        else:
            for chunk in (msg[x:x+1996] for x in range(0, len(msg), 1996)):
                # not using the paginators prefix/suffix due to this resulting in weird indentation on newlines
                self._buffer.append(f'`{chunk}`')

        self._can_emit.set()

    async def emitter(self):
        while not self.closed:
            now = time.monotonic()

            send_delta = now - self._last_emit
            if send_delta < 5:
                await asyncio.sleep(5 - send_delta)

            self._last_emit = now

            paginator = commands.Paginator(prefix='', suffix='')

            for message in self._buffer:
                paginator.add_line(message)

            self._buffer.clear()
            self._can_emit.clear()

            for page in paginator.pages:
                await self.webhook.execute(page)

            await self._can_emit.wait()

    def close(self):
        try:
            self.closed = True
            self._emit_task.cancel()
        finally:
            super().close()


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
    root = logging.getLogger()
    root.setLevel(LOGLEVEL)

    default_formatter = logging.Formatter(
        '[%(levelname)s] [%(name)s] %(message)s')
    root.setFormatter(default_formatter)

    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    # silence loggers
    # force them to info
    for logger in LOGGER_SILENCE:
        logger.setLevel(logging.INFO)

    for name, url in LEVELS.items():
        level = getattr(logging, name.upper(), None)
        if level is None:
            continue

        webhook = discord.Webhook.from_url(url, adapter=discord.AsyncWebhookAdapter(bot.session))

        handler = DiscordHandler(webhook, level=level)
        handler.setFormatter(formatter)

        root.addHandler(handler)
        bot.channel_handlers.append(handler)

    bot.add_cog(Logging(bot))


def teardown(bot):
    root = logging.getLogger()

    for handler in bot.channel_handlers:
        root.removeHandler(handler)
