import logging
import asyncio
import random
import datetime

import discord
import wolframalpha
import pyowm

from discord.ext import commands

from .common import Cog

log = logging.getLogger(__name__)

W_CLEAR_SKY =           ':sunny:'
W_FEW_CLOUDS =          ':white_sun_small_cloud:'
W_SCATTERED_CLOUDS =    ':partly_sunny:'
W_BROKEN_CLOUDS =       ':cloud:'
W_SHOWER_RAIN =         ':cloud_rain:'
W_RAIN =                ':cloud_rain:'
W_THUNDERSTORM =        ':thunder_cloud_rain:'
W_SNOW =                ':snowflake:'
W_MIST =                ':foggy:'

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


class Math(Cog):
    """Math related commands."""
    def __init__(self, bot):
        super().__init__(bot)

        self.wac = wolframalpha.Client(self.bot.config.WOLFRAMALPHA_APP_ID)
        self.owm = pyowm.OWM(self.bot.config.OWM_APIKEY)
        
    @commands.command(aliases=['wa'])
    async def wolframalpha(self, ctx, *, term: str):
        """Query Wolfram|Alpha"""
        if len(term) < 1:
            await ctx.send("haha no")
            return

        await self.jcoin.pricing(ctx, self.prices['API'])

        log.info('Wolfram|Alpha: %s', term)

        future = self.loop.run_in_executor(None, self.wac.query, term)
        res = None

        async with ctx.typing():
            try:
                res = await asyncio.wait_for(future, 13)
            except asyncio.TimeoutError:
                await ctx.send('⏳ Timeout reached')
                return
            except Exception as err:
                await ctx.send(f':cry: {err!r}')
                return

        if res is None:
            return

        if getattr(res, 'results', False):
            pods = (pod for pod in res.pods)
            pod = next(pods)
            while pod.title == 'Input interpretation':
                pod = next(pods)
            text = None

            if getattr(pod, 'text', False):
                text = pod.text
            elif pod.get('subpod', False):
                subpod = pod['subpod']
                if isinstance(subpod, dict):
                    text = subpod['img']['@src']
                else:
                    text = subpod 
            else:
                text = None

            if text is not None:
                await ctx.send(f'{term}:\n{text}')
            else:
                await ctx.send(f':poop: `{pod!r}`')
            return
        else:
            await ctx.send(f'{ctx.author.mention}, :cyclone: No answer :cyclone:')
            return

    @commands.command(aliases=['owm'])
    async def weather(self, ctx, location: str):
        """Get weather data for a location."""

        await self.jcoin.pricing(ctx, self.prices['API'])

        try:
            future = self.loop.run_in_executor(None, \
                self.owm.weather_at_place, location)
            observation = await future
        except:
            await ctx.send('Error retrieving weather data')
            return

        w = observation.get_weather()
        _wg = lambda t: w.get_temperature(t)['temp']

        _icon = w.get_weather_icon_name()
        icon = OWM_ICONS.get(_icon, '*<no icon>*')
        status = w.get_detailed_status()

        em = discord.Embed(title=f"Weather for '{location}'")

        o_location = observation.get_location()

        em.add_field(name='Location', value=f'{o_location.get_name()}')
        em.add_field(name='Situation', value=f'{status} {icon}')
        em.add_field(name='Temperature', value=f'`{_wg("celsius")} °C, {_wg("fahrenheit")} °F, {_wg("kelvin")} °K`')

        await ctx.send(embed=em)

    @commands.command()
    async def money(self, ctx, amount: str, currency_from: str = '', currency_to: str = ''):
        """Convert currencies."""

        currency_from = currency_from.upper()
        currency_to = currency_to.upper()

        if amount == 'list':
            data = await self.get_json('http://api.fixer.io/latest')
            res = ' '.join(data["rates"].keys())
            await ctx.send(f'```\n{res}\n```')
            return

        try:
            amount = float(amount)
        except:
            await ctx.send("Error parsing `amount`")
            return

        await self.jcoin.pricing(ctx, self.prices['API'])

        data = await self.get_json(f'https://api.fixer.io/latest?base={currency_from}')

        if 'error' in data:
            await ctx.send(f'API error: {data["error"]}')
            return

        if currency_to not in data['rates']:
            await ctx.send(f'Invalid currency to convert to: {currency_to}')
            return

        rate = data['rates'][currency_to]
        res = amount * rate

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
        except ValueError:
            await ctx.send('invalid amount')
            return

        try:
            dice_sides = int(dice[1])
        except ValueError:
            await ctx.send('invalid dice side')
            return

        if dice_amount <= 0 or dice_sides <= 0:
            await ctx.send('nonono')
            return

        if dice_amount > 100:
            await ctx.send('100+ dice? nonono')
            return

        if dice_sides > 50:
            await ctx.send('50+ sides? nonono')
            return

        dices = []
        for i in range(dice_amount):
            dice_result = random.randint(1, dice_sides)
            dices.append(dice_result)

        joined = ', '.join(str(r) for r in dices)
        await ctx.send(f'{dicestr} : `{joined}` => {sum(dices)}')


def setup(bot):
    bot.add_cog(Math(bot))
