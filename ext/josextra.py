#!/usr/bin/env python3

import aiohttp
import json
import subprocess
import re
import psutil
import os

import sys
sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon

from random import SystemRandom
random = SystemRandom()

JOSE_URL = 'https://github.com/lkmnds/jose/blob/master'

docsdict = {
    "modules": "{}/doc/modules.md".format(JOSE_URL),
    "events": "{}/doc/events.md".format(JOSE_URL),
    "queries": "{}/doc/queries.md".format(JOSE_URL),
    "queries-pt": "{}/doc/queries.md".format(JOSE_URL),
    "manual": "{}/doc/manual.md".format(JOSE_URL),
    "eapi": "{}/doc/extension_api.md".format(JOSE_URL),
}

class joseXtra(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.docs = docsdict

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_xkcd(self, message, args, cxt):
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
            await cxt.say('xkcd %s : %s' % (n, info['img']))

        except Exception as e:
            await cxt.say("err: %r" % e)

    async def c_tm(self, message, args, cxt):
        await cxt.say('%s™' % ' '.join(args[1:]))

    async def c_loteria(self, message, args, cxt):
        await cxt.say("nao")

    async def c_report(self, message, args, cxt):
        res = []

        # get memory usage
        process = psutil.Process(os.getpid())
        mem_bytes = process.memory_info().rss
        mem_mb = mem_bytes / 1024 / 1024
        res.append("Memory Usage: %.2f MB" % mem_mb)

        # get num of servers
        res.append("Guilds: %d" % (len(self.client.servers)))

        await cxt.say(self.codeblock("", '\n'.join(res)))

    async def c_status(self, message, args, cxt):
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

        await self.client.edit_message(edit1, edit1.content + """
%s : min %sms avg %sms max %sms
""" % ("google.com", g_rtt[0], g_rtt[1], g_rtt[2]))

    async def c_info(self, message, args, cxt):
        await cxt.say("""
José v%s\n
José Testing Enviroment, JTE: https://discord.gg/5ASwg4C\n
José is open-source! see it in https://github.com/lkmnds/jose\n

Made with :heart: by Luna Mendes""" % (jcommon.JOSE_VERSION))

    async def c_docs(self, message, args, cxt):
        '''`!docs <topic>` - Documentação do josé
        `!docs list` lista todos os tópicos disponíveis'''
        if len(args) < 2:
            await cxt.say(self.c_docs.__doc__)
            return

        topic = ' '.join(args[1:])

        if topic == 'list':
            topics = ' '.join(self.docs)
            await cxt.say(topics)
        else:
            if topic in self.docs:
                await cxt.say(self.docs[topic])
            else:
                await cxt.say("%s: tópico não encontrado" % topic)

    async def mkresponse(message, fmt, phrases, cxt):
        d = message.content.split(' ')
        user_use = d[1]
        response = random.choice(phrases)
        await cxt.say(fmt.format(user_use, response))

    async def c_xingar(self, message, args, cxt):
        await self.mkresponse(message, '{}, {}', jcommon.xingamentos, cxt)

    async def c_elogio(self, message, args, cxt):
        await self.mkresponse(message, '{}, {}', jcommon.elogios, cxt)

    async def c_cantada(self, message, args, cxt):
        await self.mkresponse(message, 'Ei {}, {}', jcommon.cantadas, cxt)
