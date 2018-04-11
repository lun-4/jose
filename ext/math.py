import logging
import asyncio
import random
import decimal

import discord
import wolframalpha
import pyowm

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)

W_CLEAR_SKY = ':sunny:'
W_FEW_CLOUDS = ':white_sun_small_cloud:'
W_SCATTERED_CLOUDS = ':partly_sunny:'
W_BROKEN_CLOUDS = ':cloud:'
W_SHOWER_RAIN = ':cloud_rain:'
W_RAIN = ':cloud_rain:'
W_THUNDERSTORM = ':thunder_cloud_rain:'
W_SNOW = ':snowflake:'
W_MIST = ':foggy:'

OWM_ICONS = {
    '01d': W_CLEAR_SKY,
    '02d': W_FEW_CLOUDS,
    '03d': W_SCATTERED_CLOUDS,
    '04d': W_BROKEN_CLOUDS,
    '09d': W_SHOWER_RAIN,
    '10d': W_RAIN,
    '11d': W_THUNDERSTORM,
    '13d': W_SNOW,
    '50d': W_MIST,
}

RESULT_PODS = {'Result', 'Plot', 'Plots', 'Solution', 'Derivative'}

UNECESSARY_PODS = {'Input', 'Input interpretation'}


def pod_finder(pod_list):
    """Finds a probable pod."""
    log.debug('pod_finder: going to score %d pods', len(pod_list))
    log.debug(f'pod_finder {pod_list!r}')
    pod_scores = {}

    for pod in pod_list:
        # convert pod to dict
        pod = dict(pod)

        if pod.get('@title') in RESULT_PODS:
            # log.info('pod_finder: found result pod! %s', pod)
            return pod

        score = 0

        # meh pods
        if pod.get('@title') in UNECESSARY_PODS:
            score -= 100

        if 'subpod' not in pod:
            # ignore pods without subpod
            continue

        if isinstance(pod['subpod'], list):
            # subpod has an image
            score += 10 + (len(pod['subpod']) * 10)
        else:
            # subpod is singular

            # plain text
            if pod['subpod'].get('plaintext'):
                score += 50

            # image
            if pod['subpod'].get('img'):
                score += 30

        pod_scores[pod['@id']] = score

    log.debug('pod_finder: got %d pods', len(pod_scores))
    log.debug('pod_finder scores: %s', pod_scores)

    # return pod with highest score
    best_id = max(pod_scores, key=pod_scores.get)
    return discord.utils.find(lambda pod: pod['@id'] == best_id, pod_list)


class Math(Cog):
    """Math related commands."""

    def __init__(self, bot):
        super().__init__(bot)

        self.wac = wolframalpha.Client(self.bot.config.WOLFRAMALPHA_APP_ID)
        self.owm = pyowm.OWM(self.bot.config.OWM_APIKEY)

    @commands.command(aliases=['wa'])
    @commands.cooldown(rate=1, per=6, type=commands.BucketType.user)
    async def wolframalpha(self, ctx, *, term: str):
        """Query Wolfram|Alpha"""
        if len(term) < 1:
            await ctx.send('Haha, no.')
            return

        await self.jcoin.pricing(ctx, self.prices['API'])

        log.debug('Wolfram|Alpha: %s', term)

        future = self.loop.run_in_executor(None, self.wac.query, term)
        res = None

        # run the thingy
        async with ctx.typing():
            try:
                res = await asyncio.wait_for(future, 13)
            except asyncio.TimeoutError:
                await ctx.send(
                    '\N{HOURGLASS WITH FLOWING SAND} Timeout reached.')
                return
            except Exception as err:
                await ctx.send(f'\N{CRYING FACE} Error: `{err!r}`')
                return

        if res is None:
            await ctx.send("\N{THINKING FACE} Wolfram|Alpha didn't reply.")
            return

        if not res.success:
            await ctx.send("\N{CRYING FACE} Wolfram|Alpha failed.")
            return

        if not getattr(res, 'pods', False):
            # no pods were returned by wa
            await ctx.send("\N{CYCLONE} No answer. \N{CYCLONE}")
            return

        pods = list(res.pods)

        # run algo on pod list
        pod = pod_finder(pods)

        def subpod_simplify(subpod):
            """Simplifies a subpod into its image or plaintext equivalent."""
            if subpod.get('img'):
                # use image over text
                return subpod['img']['@src']
            return subpod['plaintext']

        if isinstance(pod['subpod'], dict):
            # just a single pod!
            await ctx.send(subpod_simplify(pod['subpod']))
        else:
            # multiple pods...choose the first one.
            await ctx.send(subpod_simplify(pod['subpod'][0]))

    @commands.command(aliases=['owm'])
    async def weather(self, ctx, *, location: str):
        """Get weather data for a location."""

        await self.jcoin.pricing(ctx, self.prices['API'])

        try:
            future = self.loop.run_in_executor(None, self.owm.weather_at_place,
                                               location)
            observation = await future
        except Exception as err:
            raise self.SayException(
                f'Error retrieving weather data: `{err!r}`')

        w = observation.get_weather()

        def _wg(t):
            return w.get_temperature(t)['temp']

        _icon = w.get_weather_icon_name()
        icon = OWM_ICONS.get(_icon, '*<no icon>*')
        status = w.get_detailed_status()

        em = discord.Embed(title=f"Weather for '{location}'")

        o_location = observation.get_location()

        em.add_field(name='Location', value=f'{o_location.get_name()}')
        em.add_field(name='Situation', value=f'{status} {icon}')
        em.add_field(
            name='Temperature',
            value=
            f'`{_wg("celsius")} °C, {_wg("fahrenheit")} °F, {_wg("kelvin")} K`'
        )

        await ctx.send(embed=em)

    @commands.command()
    async def money(self,
                    ctx,
                    amount: str,
                    currency_from: str = '',
                    currency_to: str = ''):
        """Convert currencies."""

        currency_from = currency_from.upper()
        currency_to = currency_to.upper()

        if amount == 'list':
            data = await self.get_json('http://api.fixer.io/latest')
            res = ' '.join(data["rates"].keys())
            await ctx.send(f'```\n{res}\n```')
            return

        try:
            amount = decimal.Decimal(amount)
        except:
            raise self.SayException('Error parsing `amount`')

        await self.jcoin.pricing(ctx, self.prices['API'])

        data = await self.get_json('https://api.fixer.io/'
                                   f'latest?base={currency_from}')

        if 'error' in data:
            raise self.SayException(f'API error: {data["error"]}')

        if currency_to not in data['rates']:
            raise self.SayException('Invalid currency to convert to: '
                                    f'{currency_to}')

        rate = data['rates'][currency_to]
        rate = decimal.Decimal(rate)
        res = amount * rate
        res = round(res, 7)

        await ctx.send(f'{amount} {currency_from} = {res} {currency_to}')

    @commands.command()
    async def roll(self, ctx, dicestr: str):
        """Roll fucking dice.
        format is <amount>d<sides>
        """

        dice = dicestr.split('d')
        dice_amount = 1
        dice_sides = 6

        try:
            if dice[0] != '':
                dice_amount = int(dice[0])
        except (ValueError, IndexError):
            await ctx.send('invalid amount')
            return

        try:
            dice_sides = int(dice[1])
        except (IndexError, ValueError):
            await ctx.send('invalid dice side')
            return

        if dice_amount <= 0 or dice_sides <= 0:
            await ctx.send('nonono')
            return

        if dice_amount > 100:
            await ctx.send('100+ dice? nonono')
            return

        if dice_sides > 10000:
            await ctx.send('10000+ sides? nonono')
            return

        dices = []
        for i in range(dice_amount):
            dice_result = random.randint(1, dice_sides)
            dices.append(dice_result)

        joined = ', '.join(str(r) for r in dices)
        await ctx.send(f'{dicestr} : `{joined}` => {sum(dices)}')


def setup(bot):
    bot.add_cog(Math(bot))
