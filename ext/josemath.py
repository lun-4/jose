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

class JoseMath(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_wolframalpha(self, message, args):
        '''`!wolframalpha terms` - make a request to Wolfram|Alpha'''
        if len(args) < 2:
            await self.say(self.c_wolframalpha.__doc__)

        term_to_wolfram = ' '.join(args[1:])

        res = wac.query(term_to_wolfram)

        await self.say("length of pods in response: %d" % len(res.pods))

        response_wolfram = ''
        for pod in res.pods:
            print(pod)
            response_wolfram += repr(pod) + '\n'

        await self.say(self.codeblock("", response_wolfram))
