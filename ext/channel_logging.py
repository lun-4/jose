import logging
import aiohttp
import asyncio
import time

import discord
from discord.ext import commands

from .common import Cog
from joseconfig import PACKET_CHANNEL, LEVELS

log = logging.getLogger(__name__)


LOG_LEVEL = logging.DEBUG
LOGGER_SILENCE = ['discord', 'websockets']

CUSTOM_LEVELS = {
    60: '\N{MONEY BAG}'  # 60 is used for transactions
}


def clean_content(content):
    content = content.replace('`', '\'')
    content = content.replace('@', '@\u200b')
    content = content.replace('&', '&\u200b')
    content = content.replace('<#', '<#\u200b')
    return content


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
    closed : bool
        Whether this handler is closed or not
    """

    def __init__(self, webhook, *, level=None, loop=None):
        if level is not None:
            super().__init__(level)
        else:
            super().__init__()

        self.webhook = webhook
        self.loop = loop = loop or asyncio.get_event_loop()

        self.closed = False

        self._buffer = []

        self._last_emit = 0
        self._can_emit = asyncio.Event()

        self._emit_task = loop.create_task(self.emitter())

    def emit(self, record: logging.LogRecord):
        if record.levelno != self.level:
            return  # only log the handlers level to the handlers channel, not above

        msg = self.format(record)

        start = msg.find('```py\n')
        if start != -1:
            msg, trace = msg[:start], msg[start:]
        else:
            trace = None

        # the actual log message
        for line in msg.split('\n'):
            # if this is a small codeblock and goes over multiple messages it will break out
            # so we check that each chunk (besides the first) starts and stops with a backtick
            for idx, chunk in enumerate(line[x:x + 1994] for x in range(0, len(line), 1994)):
                # ugh
                if not chunk.endswith('`'):
                    chunk = f'{chunk}`'
                if not chunk.startswith('`'):
                    chunk = f'`{chunk}'

                self._buffer.append(chunk)

        # the traceback, sent separately to be in a big codeblock for syntax highlighting
        if trace is not None:
            # cut off the original codeblock
            trace = trace[6:-3]

            paginator = commands.Paginator(prefix='```py\n', suffix='```')

            for line in trace.split('\n'):
                for chunk in (line[x:x + 1987] for x in range(0, len(line), 1987)):
                    paginator.add_line(chunk)

            for page in paginator.pages:
                self._buffer.append(page)

        self._can_emit.set()

    async def emitter(self):
        while not self.closed:
            now = time.monotonic()

            send_delta = now - self._last_emit
            if send_delta < 5:
                await asyncio.sleep(5 - send_delta)

            self._last_emit = time.monotonic()

            paginator = commands.Paginator(prefix='', suffix='')

            for chunk in self._buffer:
                paginator.add_line(chunk.strip())

            self._buffer.clear()
            self._can_emit.clear()

            try:
                for page in paginator.pages:
                    await self.webhook.execute(page)
            except (discord.HTTPException, aiohttp.ClientError):
                log.exception('Failed to emit logs')

            await self._can_emit.wait()

    def close(self):
        try:
            self.closed = True
            self._emit_task.cancel()
        finally:
            super().close()


class DiscordFormatter(logging.Formatter):
    """
    Custom logging formatter meant to use in combination with the DiscordHandler.

    The formatter puts exceptions into a big codeblock to properly highlight them in Discord
    as well as allowing to pass emoji which will replace the level (name) to allow seeing what's going on easier.

    Parameters
    ----------
    emoji : Dict[int, str]
        Dictionary of logging levels and characters which will replace the level name or 'Level <int>' in the log.
        By default the DEBUG, INFO, WARNING and ERROR levels have emoji set, but these can be overwritten.
    """

    def __init__(self, fmt=None, datefmt=None, style='%', *, emoji=None):
        super().__init__(fmt, datefmt, style)

        self.emoji = {
            logging.DEBUG: '\N{CONSTRUCTION SIGN}',
            logging.INFO: '\N{ENVELOPE}',
            logging.WARNING: '\N{WARNING SIGN}',
            logging.ERROR:'\N{HEAVY EXCLAMATION MARK SYMBOL}',
        }

        if emoji is not None:
            self.emoji.update(emoji)

    def formatMessage(self, record: logging.LogRecord):
        msg = super().formatMessage(record)

        emoji = self.emoji.get(record.levelno)
        if emoji is None:
            return msg

        msg = msg.replace(record.levelname, emoji)
        msg = msg.replace(f'Level {record.levelno}', emoji)

        return msg

    def format(self, record: logging.LogRecord):
        """
        Format the specified record as text.
        This implementation is directly copied from the superclass, only adding the codeblock to the traceback.
        """

        record.message = clean_content(record.getMessage())

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        s = self.formatMessage(record)

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"

            # add a codeblock so the DiscordHandler can properly split the error into multiple messages if needed
            s = f'{s}```py\n{record.exc_text}```'

        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)

        return s


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
                                                    f'```py\n{payload}\n```')

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
    root.setLevel(LOG_LEVEL)

    # stdout logging
    default_formatter = logging.Formatter(
        '[%(levelname)s] [%(name)s] %(message)s')

    sh = logging.StreamHandler()
    sh.setFormatter(default_formatter)
    root.addHandler(sh)

    # so it gets detach on reload
    bot.channel_handlers.append(sh)

    formatter = DiscordFormatter(
        '`[%(asctime)s]` %(levelname)s `[%(name)s]` `%(message)s`',
        datefmt='%H:%M:%S',
        emoji=CUSTOM_LEVELS
    )

    # silence loggers
    # force them to info
    for logger_name in LOGGER_SILENCE:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

    # add all channel loggers from the config
    for level, url in LEVELS.items():
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

    bot.channel_handlers = []
