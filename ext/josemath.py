#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import joseconfig as jconfig

import wolframalpha
wac = wolframalpha.Client(jconfig.WOLFRAMALPHA_APP_ID)

import pyowm
owm = pyowm.OWM(jconfig.OWM_APIKEY)

class JoseMath(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.wac = wac
        self.owm = owm

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_wolframalpha(self, message, args):
        '''`!wolframalpha terms` - make a request to Wolfram|Alpha
        **ratelimit GLOBAL: 2 chamadas por hora**'''
        if len(args) < 2:
            await self.say(self.c_wolframalpha.__doc__)
            return

        term_to_wolfram = ' '.join(args[1:])

        res = self.wac.query(term_to_wolfram)
        if getattr(res, 'results', False):
            try:
                response_wolfram = next(res.results).text
            except StopIteration:
                await self.say(":warning: Erro tentando pegar o texto da resposta :warning:")
                return
            await self.say("%s:\n%s" % (term_to_wolfram, self.codeblock("", response_wolfram)))
        else:
            await self.say(":cyclone: Sem resposta :cyclone:")
            return

    async def c_wa(self, message, args):
        '''`!wa terms` - alias para `!wolframalpha`'''
        await self.c_wolframalpha(message, args)

    async def c_temperature(self, message, args):
        '''`!temperature location` - Temperatura de um local, usando OpenWeatherMap
        mostra tanto em Celsius quanto em Fahrenheit
        **ratelimit GLOBAL: 60 chamadas / minuto**'''
        if len(args) < 2:
            await self.say(self.c_temperature.__doc__)
            return

        location = ' '.join(args[1:])

        try:
            observation = owm.weather_at_place(location)
        except:
            await self.say("Erro tentando conseguir a temperatura para esse local")
            return
        w = observation.get_weather()

        tempcelsius = w.get_temperature("celsius")
        tempfahren = w.get_temperature("fahrenheit")

        celsiusnow = tempcelsius['temp']
        fahnow = tempfahren['temp']

        await self.say("%s °C, %s °F" % (celsiusnow, fahnow))

    async def c_temp(self, message, args):
        '''`!temp location` - alias para `!temperature`'''
        await self.c_temperature(message, args)

    async def c_therm(self, message, args):
        '''`!therm location` - alias para `!temperature`'''
        await self.c_temperature(message, args)
