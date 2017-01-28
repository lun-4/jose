#!/usr/bin/env python3

import discord
import aiohttp
import json
import subprocess
import re

import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import josecommon as jcommon

from random import SystemRandom
random = SystemRandom()

docsdict = {
    "modules": "https://github.com/lkmnds/jose/blob/master/doc/modules.md",
    "events": "https://github.com/lkmnds/jose/blob/master/doc/events.md",
    "queries": "https://github.com/lkmnds/jose/blob/master/doc/queries.md",
    "queries-pt": "https://github.com/lkmnds/jose/blob/master/doc/queries.md",
}

class joseXtra(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.docs = docsdict

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
            await self.say("err: %r" % e)

    async def c_tm(self, message, args):
        await self.say('%s™' % ' '.join(args[1:]))

    async def c_loteria(self, message, args):
        await self.say("nao")

    async def c_status(self, message, args):
        # ping discordapp one time

        msg = await self.client.send_message(message.channel, "Pong!")

        discordapp_ping = subprocess.Popen(
            ["ping", "-c", "3", "discordapp.com"],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        d_out, d_error = discordapp_ping.communicate()
        matcher = re.compile("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")
        d_rtt = matcher.search(d_out.decode('utf-8')).groups()

        edit1 = await self.client.edit_message(msg, msg.content + """
%s : min %sms avg %sms max %sms
""" % ("discordapp.com", d_rtt[0], d_rtt[1], d_rtt[2]))

        google_ping = subprocess.Popen(
            ["ping", "-c", "3", "google.com"],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        g_out, g_error = google_ping.communicate()
        matcher = re.compile("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")
        g_rtt = matcher.search(g_out.decode('utf-8')).groups()

        edit2 = await self.client.edit_message(edit1, edit1.content + """
%s : min %sms avg %sms max %sms
""" % ("google.com", g_rtt[0], g_rtt[1], g_rtt[2]))

    async def c_info(self, message, args):
        await self.say("""José v%s, feito por Luna Mendes\nhttps://github.com/lkmnds/jose""" % (jcommon.JOSE_VERSION))

    async def c_docs(self, message, args):
        '''`!docs <topic>` - Documentação do josé
        `!docs list` lista todos os tópicos disponíveis'''
        if len(args) < 2:
            await self.say(self.c_docs.__doc__)
            return

        topic = ' '.join(args[1:])

        if topic == 'list':
            topics = ' '.join(self.docs)
            await self.say(topics)
        else:
            if topic in self.docs:
                await self.say(self.docs[topic])
            else:
                await self.say("%s: tópico não encontrado" % topic)

    async def mkresponse(message, fmt, phrases):
        d = message.content.split(' ')
        user_use = d[1]
        response = random.choice(phrases)
        await self.say(fmt.format(user_use, response))

    async def c_xingar(self, message, args, cxt):
        await self.mkresponse(message, '{}, {}', xingamentos)

    async def c_elogio(self, message, args, cxt):
        await self.mkresponse(message, '{}, {}', xingamentos)

    async def c_cantada(self, message, args, cxt):
        await self.mkresponse(message, 'Ei {}, {}', xingamentos)
