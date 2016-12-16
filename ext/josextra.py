#!/usr/bin/env python3

import discord
import aiohttp

import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

class joseXtra(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_xkcd(self, message, args):
        '''`!xkcd` - procura tirinhas do XKCD
        `!xkcd` - mostra a tirinha mais recente
        `!xkcd [num]` - mostra a tirinha de número `num`
        `!xkcd rand` - tirinha aleatória
        '''
        n = False
        if len(args) > 1:
            n = args[1]

        loop = asyncio.get_event_loop()

        url = "http://xkcd.com/info.0.json"
        r = await aiohttp.request('GET', url)
        content = await r.text()

        info_latest = info = json.loads(content)
        info = None
        try:
            if not n:
                info = info_latest
                n = info['num']
            elif n == 'random' or n == 'r' or n == 'rand':
                rn_xkcd = random.randint(0, info_latest['num'])

                url = "http://xkcd.com/{0}/info.0.json".format(rn_xkcd)
                r = await aiohttp.request('GET', url)
                content = await r.text()

                info = json.loads(content)
            else:
                url = "http://xkcd.com/{0}/info.0.json".format(n)
                r = await aiohttp.request('GET', url)
                content = await r.text()
                info = json.loads(content)
            await self.say('xkcd número %s : %s' % (n, info['img']))

        except Exception as e:
            await self.debug("xkcd: pyerr: %s" % str(e))

    async def c_tm(self, message, args):
        await self.say('%s™' % ' '.join(args[1:]))
