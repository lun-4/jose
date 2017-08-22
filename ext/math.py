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

W_API_ICONS = {
    'tornado': ':cloud_tornado:',
    'tropical-storm': ':cyclone:',
    'thunderstorm': ':thunder_cloud_rain:',
    'rain-snow': ':cloud_rain: :snowflake:',
    'rain-hail': ':cloud_rain: *(hail)*',
    'freezing-drizzle': ':cloud_rain: *(freezing)*',
    'scattered-showers': ':white_sun_rain_cloud:',
    'rain': ':cloud_rain:',
    'flurries': ':cloud_snow:',
    'snow': ':cloud_snow:',
    'blowing-snow': ':cloud_snow: :dash:',
    'hail': '*(hail)*',
    'fog': ':fog: *(fog)*',
    'wind': ':dash:',
    'cloudy': ':cloud:',
    'mostly-cloudy-night': ':partly_sunny:',
    'mostly-cloudy': ':partly_sunny:',
    'partly-cloudy-night': ':white_sun_small_cloud:',
    'partly-cloudy': ':white_sun_small_cloud:',
    'clear-night': ':full_moon:',
    'sunny': ':sunny:',
    'mostly-clear-night': ':full_moon: :cloud: *(partly cloudy)*',
    'mostly-sunny': ':white_sun_small_cloud:',
    'isolated-thunderstorms': ':thunder_cloud_rain:',
    'scattered-thunderstorms': ':thunder_cloud_rain:',
    'heavy-rain': ':cloud_rain: *(heavy)*',
    'scattered-snow': ':cloud_snow: *(scattered)*',
    'heavy-snow': ':cloud_snow: *(heavy)*',
    'na': ':no_entry_sign: *(na)*',
    'scattered-showers-night': ':white_sun_rain_cloud:',
    'scattered-snow-night': ':cloud_snow: *(scattered)*',
    'scattered-thunderstorms-night': ':thunder_cloud_rain:'
}

class Math(Cog):
    """Math related commands."""
    def __init__(self, bot):
        super().__init__(bot)

        self.wac = wolframalpha.Client(self.bot.config.WOLFRAMALPHA_APP_ID)
        self.owm = pyowm.OWM(self.bot.config.OWM_APIKEY)
        self.w_config = getattr(self.bot.config, 'WEATHER_API', None)
        
        if self.w_config is not None:
            self.w_api_base_url = self.w_config['base_url']
            self.w_api_base_payload = {
                'key': self.w_config['key'],
                'secret': self.w_config['secret'],
            }


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
                text = subpod['img']['@src']
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

    @commands.command(aliases=['vgay'])
    async def owm(self, ctx, location: str):
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

    async def w_api_post(self, route, payload):
        payload_send = {**self.w_api_base_payload, **payload}
        base_url = self.w_api_base_url

        async with self.bot.session.post(f'{base_url}{route}', json=payload_send) as resp:
            try:
                data = await resp.json()
            except Exception:
                data = {}
            
            status = data.get('status')

            if resp.status != 200:
                if resp.status == 500:
                    log.error(f'```<@116693403147698181>```api shitted itself {status!r}')
                    raise self.SayException(f'x_x 500. `{status["decrypted"]}`')
                else:
                    raise self.SayException(f'Failed to retrieve weather data, code {resp.status}')


            return data

    @commands.command(aliases=['temperature', 'therm'])
    async def weather(self, ctx, *, querylocation: str):
        """Query temperature data.
        
        Uses data from The Weather Channel
        """
        if self.w_config is None:
            raise self.SayException('No weather API data found in config file')

        await self.jcoin.pricing(ctx, self.prices['API'])
        async with ctx.typing():
            _locations = await self.w_api_post('location', {'query': querylocation})
            locations = _locations['locations']
            if len(locations) < 1:
                raise self.SayException('No locations found')

            location_found = locations[0]

            _weather_data = await self.w_api_post('weather', {'location': location_found['id']})

        current = _weather_data['current']
        location = _weather_data['location']

        for field in current:
            try:
                current[field] = round(current[field], 2)
            except: pass

        location_time = datetime.datetime.fromtimestamp(int(current['time']))

        em = discord.Embed(title=f"Weather for '{querylocation}'")
        em.description = f"Time of observation (GMT+0): {location_time}"

        em.add_field(name='Location', value=f'{location["city"]}, {location["stateName"]}, {location["country"]}')
        em.add_field(name='Situation', value=f'{current["text"]} {W_API_ICONS[current["condition"]]}')
        em.add_field(name='Temperature', value=f'`{current["tempC"]} °C, {current["temp"]} °F, {current["tempK"]} °K`')

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Math(bot))
