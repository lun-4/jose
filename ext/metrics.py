import logging
import asyncio
import collections

import discord

from discord.ext import commands
from .common import Cog

log = logging.getLogger(__name__)

# if average sample and current sample differ the unit
# defined here, a warning is thrown.

# keep in mind samples happen each minute
EVENT_THRESHOLD = {
    'message': 70,
    'command': 60,
    'command_compl': 50,
    'command_error': 2,  # errors should be delivered asap
}


class Metrics(Cog):
    """Metrics subsystem."""
    def __init__(self, bot):
        super().__init__(bot)

        # get webhooks
        wbh = discord.Webhook.from_url
        adp = discord.AsyncWebhookAdapter(self.bot.session)
        self.webhook = wbh(self.bot.config.METRICS_WEBHOOK, adapter=adp)

        # metrics state
        self.sum_state = collections.defaultdict(int)
        self.samples = 0

        self.last_state = None
        self.empty_state()

        self.sampletask = self.bot.loop.create_task(self.sample_task())
        self.owner = None

    def __unload(self):
        self.sampletask.cancel()

    def get_rates(self):
        """Get the rates, given current state."""
        return {k: round(v / 60, 4) for k, v in self.current_state.items()}

    def empty_state(self):
        """Set current state to 0"""
        self.current_state = {
            'message': 0,
            'command': 0,
            'command_error': 0,
            'command_compl': 0,
        }

    def submit_state(self):
        """Submit current state to the sum of states."""
        self.samples += 1
        log.debug(f'Sampling: {self.current_state!r}')
        for k, val in self.current_state.items():
            self.sum_state[k] += val

    def get_average_state(self):
        """Get the average state"""
        return {k: (v / self.samples) for k, v in self.sum_state.items()}

    async def sample(self):
        """Sample current data."""

        # compare current_state with last_state
        average = self.get_average_state()

        warn = []
        for k, average in average.items():
            delta = self.current_state[k] - average
            threshold = EVENT_THRESHOLD[k]
            if threshold <= 0:
                # ignore if threshold is 0 etc
                continue

            if delta > EVENT_THRESHOLD[k]:
                # this event is above the threshold, we warn!
                warn.append((k, self.current_state[k],
                             average, delta, threshold))

        # this only really works if we already made 3 samples
        if warn and self.samples > 3:
            if not self.owner:
                self.owner = (await self.bot.application_info()).owner

            res = [f'{self.owner.mention}!!\n']
            for (event, cur_state, average, delta, threshold) in warn:
                res.append(f'\tEvent `{event}`, current: {cur_state}, '
                           f'average: {average}, delta: {delta}, '
                           f'threshold: {threshold}\n')

            await self.webhook.execute('\n'.join(res))

        # set last_state to a copy of current_state
        self.last_state = dict(self.current_state)

        # set current_state to 0
        self.submit_state()
        self.empty_state()

    async def sample_task(self):
        try:
            while True:
                log.debug('metrics sampling')
                await self.sample()
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            log.warning('sample task cancel')
        except Exception:
            log.exception('sample task rip')

    async def on_message(self, message):
        if message.author.bot:
            return

        self.current_state['message'] += 1

    async def on_command(self, ctx):
        self.current_state['command'] += 1

    async def on_command_error(self, ctx, error):
        self.current_state['command_error'] += 1

    async def on_command_completion(self, ctx):
        self.current_state['command_compl'] += 1

    @commands.command()
    async def mstate(self, ctx):
        """Get current state of metrics."""
        state = self.current_state
        await ctx.send(f'Messages received: {state["message"]}\n'
                       f'Commands received: {state["command"]}\n'
                       f'Commands completed: {state["command_compl"]}\n'

                       'Commands which raised errors: '
                       f'{state["command_error"]}\n')

    @commands.command()
    async def mrates(self, ctx):
        """Get per-second rates of current state."""
        rates = self.get_rates()
        await ctx.send(f'Messages/second: {rates["message"]}\n'
                       f'Commands/second: {rates["command"]}\n'
                       f'Complete/second: {rates["command_compl"]}\n'
                       f'Errors/second: {rates["command_error"]}')

    @commands.command()
    async def msample(self, ctx):
        """Force a sample"""
        await self.sample()
        await ctx.ok()


def setup(bot):
    bot.add_cog(Metrics(bot))
