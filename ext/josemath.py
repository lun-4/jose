#!/usr/bin/env python3

import sys
sys.path.append("..")
import jauxiliar as jaux
import joseconfig as jconfig

import aiohttp
import json
import wolframalpha
import pyowm
import traceback

class JoseMath(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
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
        res = self.wac.query(term_to_wolfram)

        if getattr(res, 'results', False):
            try:
                pods = (pod for pod in res.pods)
                pod = next(pods)
                while pod.title == 'Input interpretation':
                    pod = next(pods)
                text = None

                self.logger.info(repr(pod))
                if getattr(pod, 'text', False):
                    self.logger.info("get text")
                    text = pod.text
                elif pod.get('subpod', False):
                    subpod = pod['subpod']
                    text = subpod['img']['@src']
                else:
                    self.logger.info("fucking nothing")
                    text = None
                    pass

                if text is not None:
                    await cxt.say("%s:\n%s", (term_to_wolfram, text)
                else:
                    await cxt.say(":poop:")
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
            observation = self.owm.weather_at_place(location)
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

    async def c_plot(self, message, args, cxt):
        '''`j!plot func` - plot f(x) functions'''
        pass

    async def c_money(self, message, args, cxt):
        '''`j!money quantity base to` - converte dinheiro usando cotações etc
        `!money list` - lista todas as moedas disponíveis'''

        if len(args) > 1:
            if args[1] == 'list':
                r = await aiohttp.request('GET', "http://api.fixer.io/latest")
                content = await r.text()
                data = json.loads(content)
                await cxt.say(self.codeblock("", " ".join(data["rates"])))
                return

        if len(args) < 3:
            await cxt.say(self.c_money.__doc__)
            return

        try:
            amount = float(args[1])
        except Exception as e:
            await cxt.say("Error parsing `quantity`")
            return

        currency_from = args[2]
        currency_to = args[3]

        url = "http://api.fixer.io/latest?base={}".format(currency_from.upper())
        r = await aiohttp.request('GET', url)
        content = await r.text()
        data = json.loads(content)

        if 'error' in data:
            await cxt.say("!money: %s", (data['error'],))
            return

        if currency_to not in data['rates']:
            await cxt.say("Invalid currency to convert to")
            return

        rate = data['rates'][currency_to]
        res = amount * rate

        await cxt.say('{} {} = {} {}'.format(
            amount, currency_from, res, currency_to
        ))
