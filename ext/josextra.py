#!/usr/bin/env python3

import discord
import aiohttp
import urllib.parse
import urllib.request
import subprocess
import re
import psutil
import os

import sys
sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import joseconfig as jconfig

from random import SystemRandom
random = SystemRandom()

JOSE_URL = 'https://github.com/lkmnds/jose/blob/master'

docsdict = {
    "modules": "{}/doc/modules.md".format(JOSE_URL),
    "events": "{}/doc/events.md".format(JOSE_URL),
    "queries": "{}/doc/cmd/queries.md".format(JOSE_URL),
    "queries-pt": "{}/doc/cmd/queries-pt.md".format(JOSE_URL),
    "manual": "{}/doc/manual.md".format(JOSE_URL),
    "eapi": "{}/doc/extension_api.md".format(JOSE_URL),

    "magicwords": "{}/doc/cmd/magicwords.md".format(JOSE_URL),
    "magicwords-pt": "{}/doc/cmd/magicwords-pt.md".format(JOSE_URL),

    "commands": "{}/doc/cmd/listcmd.md".format(JOSE_URL),
    "josespeak": "{}/doc/josespeak.md".format(JOSE_URL),

    "contributing": "{}/CONTRIBUTING.md".format(JOSE_URL),
    "jcoin": "{}/doc/jcoin.md".format(JOSE_URL),
}

class joseXtra(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.docs = docsdict
        self.msgcount = 0

        # every minute, show josé's usage
        self.cbk_new("jxtra.msgcount", self.message_count, 60)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        self.cbk_remove('jxtra.msgcount')
        return True, ''

    async def message_count(self):
        if self.msgcount > 0:
            self.logger.info("Processed %d messages/minute", self.msgcount)
        self.msgcount = 0

    async def e_any_message(self, message, cxt):
        self.msgcount += 1

    async def c_xkcd(self, message, args, cxt):
        '''`j!xkcd` - latest xkcd
        `j!xkcd [num]` - xkcd number `num`
        `j!xkcd rand` - random xkcd
        '''
        n = False
        if len(args) > 1:
            n = args[1]

        await self.jcoin_pricing(cxt, jcommon.API_TAX_PRICE)

        url = "http://xkcd.com/info.0.json"
        r = await aiohttp.request('GET', url)
        content = await r.text()

        info_latest = info = await self.json_load(content)
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

                info = await self.json_load(content)
            else:
                url = "http://xkcd.com/{0}/info.0.json".format(n)
                r = await aiohttp.request('GET', url)
                content = await r.text()
                info = await self.json_load(content)
            await cxt.say('xkcd %s : %s', (n, info['img']))

        except Exception as e:
            await cxt.say("err: %r", (e,))

    async def c_tm(self, message, args, cxt):
        await cxt.say('%s™', (' '.join(args[1:]),))

    async def c_loteria(self, message, args, cxt):
        await cxt.say("nao")

    async def c_awoo(self, message, args, cxt):
        await cxt.say("https://cdn.discordapp.com/attachments/\
202055538773721099/257717450135568394/awooo.gif")

    async def c_report(self, message, args, cxt):
        '''`j!report` - show important stuff'''
        res = []

        # get memory usage
        process = psutil.Process(os.getpid())
        mem_bytes = process.memory_info().rss
        mem_mb = mem_bytes / 1024 / 1024
        res.append("Memory Usage: %.2f MB" % mem_mb)

        # get num of servers
        res.append("Guilds: %d" % len(self.client.servers))

        # num of channels
        res.append("Channels: %s" % len(list(self.client.get_all_channels())))

        # num of users
        res.append("Members: %s" % len(list(self.client.get_all_members())))

        members = [m for m in self.client.get_all_members() if not m.bot]

        # num of actual numbers that aren't bots
        res.append("Users: %s" % len(members))

        # unique users
        res.append("Unique Users: %s" % len(set(members)))

        await cxt.say(self.codeblock("", '\n'.join(res)))

    async def c_status(self, message, args, cxt):
        '''`j!status` get josé's status to some servers'''
        await self.is_admin(message.author.id)

        msg = await self.client.send_message(message.channel, "Status:")

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
José v%s
JTE, José Testing Enviroment: https://discord.gg/5ASwg4C
José is Licensed through the Don't Be a Dick Public License.
See the source at https://github.com/lkmnds/jose

Made with :heart: by Luna Mendes""" % (jcommon.JOSE_VERSION))

    async def c_docs(self, message, args, cxt):
        '''`j!docs <topic>` - José's Documentation, use `j!docs list`'''
        if len(args) < 2:
            await cxt.say(self.c_docs.__doc__)
            return

        topic = ' '.join(args[1:])

        if topic == 'list':
            topics = ' '.join(sorted(self.docs))
            await cxt.say(topics)
        else:
            if topic in self.docs:
                await cxt.say(self.docs[topic])
            else:
                await cxt.say("%s: tópico não encontrado", (topic,))

    async def c_yt(self, message, args, cxt):
        '''`j!yt tunak tunak tun` - youtube searches'''
        if len(args) < 2:
            await cxt.say(self.c_yt.__doc__)
            return

        search_term = ' '.join(args[1:])

        self.logger.info("Youtube request @ %s : %s", \
            message.author, search_term)

        query_string = urllib.parse.urlencode({"search_query" : search_term})

        await self.jcoin_pricing(cxt, jcommon.OP_TAX_PRICE)

        url = "http://www.youtube.com/results?{}".format(query_string)
        html_content = await self.http_get(url)

        # run in a thread
        future_re = self.loop.run_in_executor(None, re.findall, \
            r'href=\"\/watch\?v=(.{11})', html_content)
        search_results = await future_re

        if len(search_results) < 2:
            await cxt.say("!yt: No results found.")
            return

        await cxt.say("http://www.youtube.com/watch?v={}".format(search_results[0]))

    async def c_sndc(self, message, args, cxt):
        '''`j!sndc [stuff]` - Soundcloud search'''
        if len(args) < 2:
            await cxt.say(self.c_sndc.__doc__)
            return

        query = ' '.join(args[1:])

        self.logger.info("Soundcloud request: %s", query)

        if len(query) < 3:
            await cxt.say("preciso de mais coisas para pesquisar(length < 3)")
            return

        await self.jcoin_pricing(cxt, jcommon.API_TAX_PRICE)

        search_url = 'https://api.soundcloud.com/search?q=%s&facet=model&limit=10&offset=0&linked_partitioning=1&client_id='+jconfig.soundcloud_id
        url = search_url % urllib.parse.quote(query)

        while url:
            response = await aiohttp.request('GET', url)

            if response.status != 200:
                await cxt.say("sndc: error: status code != 200(st = %d)", \
                    (response.status))
                return

            try:
                doc = await response.json()
            except Exception as e:
                await cxt.say("sndc: py_err %s" % str(e))
                return

            for entity in doc['collection']:
                if entity['kind'] == 'track':
                    await cxt.say(entity['permalink_url'])
                    return

            await cxt.say("No results found")
            return

    async def c_profile(self, message, args, cxt):
        '''`j!profile` - experimental shit'''
        await cxt.send_typing()

        em = discord.Embed(colour=discord.Colour.purple())
        if message.author.nick is not None:
            em.add_field(name='Name', value='{} ({})'.format( \
                message.author.nick, message.author.name))
        else:
            em.add_field(name='Name', value='{}'.format(message.author.name))

        if message.author.id in self.jcoin.data:
            account = self.jcoin.data.get(message.author.id)

            _gaccounts = [userid for userid in self.jcoin.data \
                if message.server.get_member(userid) is not None]

            guildaccounts = sorted(_gaccounts, key=lambda userid: \
                self.jcoin.data[userid]['amount'])

            sorted_data = sorted(self.jcoin.data, key=lambda userid: \
                self.jcoin.data[userid]['amount'])

            # josé is always gonna be 1st, count from 2nd
            guildrank = 2
            for userid in guildaccounts:
                if userid == message.author.id: break
                guildrank += 1

            globalrank = 2
            for userid in sorted_data:
                if userid == message.author.id: break
                globalrank += 1

            em.add_field(name='JoséCoin Rank', value='{}/{} ({}/{} globally)'.format( \
                guildrank, len(guildaccounts)+1, globalrank, len(self.jcoin.data)+1))
            em.add_field(name='JoséCoin Wallet', value='{}'.format(account['amount']))
            em.add_field(name='Tax paid', value=str(account['taxpaid']))

            em.add_field(name='Stealing', value='{} tries, {} success'.format( \
                account['times_stolen'], account['success_steal']))

        await cxt.say_embed(em)
