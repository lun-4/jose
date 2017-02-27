#!/usr/bin/env python3

import sys
sys.path.append("..")
import jauxiliar as jaux
import joseconfig as jconfig

from random import SystemRandom
random = SystemRandom()

import aiohttp
import wolframalpha
import pyowm
import traceback

class JoseMath(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.wac = wolframalpha.Client(jconfig.WOLFRAMALPHA_APP_ID)
        self.owm = pyowm.OWM(jconfig.OWM_APIKEY)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_wolframalpha(self, message, args, cxt):
        '''`j!wolframalpha terms` - make a request to Wolfram|Alpha
        **ratelimit GLOBAL: 2 chamadas por hora**'''
        if len(args) < 2:
            await cxt.say(self.c_wolframalpha.__doc__)
            return

        term_to_wolfram = ' '.join(args[1:])
        if len(term_to_wolfram.strip()) < 1:
            await cxt.say("haha no")
            return

        self.logger.info("Wolfram|Alpha: %s", term_to_wolfram)

        future = self.loop.run_in_executor(None, \
            self.wac.query, term_to_wolfram)
        res = await future

        if getattr(res, 'results', False):
            try:
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
                    pass

                if text is not None:
                    await cxt.say("%s:\n%s", (term_to_wolfram, text))
                else:
                    await cxt.say(":poop: `%r`", (pod,))
                return
            except Exception as e:
                await cxt.say(self.codeblock("", traceback.format_exc()))
        else:
            await cxt.say(":cyclone: Sem resposta :cyclone:")
            return

    async def c_wa(self, message, args, cxt):
        '''`j!wa terms` - alias para `!wolframalpha`'''
        await self.c_wolframalpha(message, args, cxt)

    async def c_temperature(self, message, args, cxt):
        '''`j!temperature location` - OpenWeatherMap'''
        # ratelimit 60/minute
        if len(args) < 2:
            await cxt.say(self.c_temperature.__doc__)
            return

        location = ' '.join(args[1:])

        try:
            future = self.loop.run_in_executor(None, \
                self.owm.weather_at_place, location)
            observation = await future
        except:
            await cxt.say("Erro tentando conseguir a temperatura para esse local")
            return
        w = observation.get_weather()

        tempkelvin = w.get_temperature()
        tempcelsius = w.get_temperature("celsius")
        tempfahren = w.get_temperature("fahrenheit")

        celsiusnow = tempcelsius['temp']
        fahnow = tempfahren['temp']
        kelnow = tempkelvin['temp']

        await cxt.say("`%s` is at `%s °C, %s °F, %s °K`", \
            (location, celsiusnow, fahnow, kelnow))

    async def c_temp(self, message, args, cxt):
        '''`j!temp location` - alias para `!temperature`'''
        await self.c_temperature(message, args, cxt)

    async def c_therm(self, message, args, cxt):
        '''`j!therm location` - alias para `!temperature`'''
        await self.c_temperature(message, args, cxt)

    def lewd(self, n):
        num = 3
        t = 0
        while t != n:
            lewd = num ** 2 - 2
            for a in range(2, lewd):
                if lewd % a == 0:
                    break
            else:
                yield num
                t += 1
            num += 6

    async def c_lewd(self, message, args, cxt):
        '''`j!lewd n` - shows the `n` lewd numbers'''
        if len(args) < 2:
            await cxt.say(self.c_lewd.__doc__)

        try:
            n = int(args[1])
        except Exception as e:
            await cxt.say("Error parsing arguments: %r", (e,))
            return

        if n > 30:
            await cxt.say("nope")
            return

        await cxt.say(self.codeblock("", list(self.lewd(n))))

    async def c_money(self, message, args, cxt):
        '''`j!money amount base to` - Converts money, with `base` and `to` being currencies.
`!money list` - list all available currencies'''

        if len(args) > 1:
            if args[1] == 'list':
                r = await aiohttp.request('GET', "http://api.fixer.io/latest")
                content = await r.text()
                data = await self.json_load(content)
                await cxt.say(self.codeblock("", " ".join(data["rates"])))
                return

        if len(args) < 3:
            await cxt.say(self.c_money.__doc__)
            return

        try:
            amount = float(args[1])
        except Exception as e:
            await cxt.say("Error parsing `amount`")
            return

        currency_from = args[2]
        currency_to = args[3]

        url = "http://api.fixer.io/latest?base={}".format(currency_from.upper())
        r = await aiohttp.request('GET', url)
        content = await r.text()
        data = await self.json_load(content)


        if 'error' in data:
            await cxt.say("money API error: %s", (data['error'],))
            return

        if currency_to not in data['rates']:
            await cxt.say("Invalid currency to convert to: %s", (currency_to,))
            return

        rate = data['rates'][currency_to]
        res = amount * rate

        await cxt.say('{} {} = {} {}'.format(
            amount, currency_from, res, currency_to
        ))

    async def c_roll(self, message, args, cxt):
        '''`j!roll <amount>d<sides>` - roll fucking dice'''
        if len(args) < 2:
            await cxt.say(self.c_roll.__doc__)
            return

        dicestr = args[1]
        dice = dicestr.split('d')
        dice_amount = 1
        dice_sides = 6

        try:
            if dice[0] != '':
                dice_amount = int(dice[0])
        except ValueError:
            await cxt.say("try to do your things better(dice_amount).")
            return

        try:
            dice_sides = int(dice[1])
        except ValueError:
            await cxt.say("try to do your things better(dice_sides).")
            return

        dices = []
        for i in range(dice_amount):
            dice_result = random.randint(1, dice_sides)
            dices.append(dice_result)

        await cxt.say("%s: `%s` => %d", (dicestr, \
            ', '.join(str(r) for r in dices), sum(dices)))
