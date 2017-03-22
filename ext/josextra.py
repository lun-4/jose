#!/usr/bin/env python3

import discord
import aiohttp
import urllib.parse
import urllib.request
import subprocess
import re
import psutil
import os
import hashlib
import collections
import time
import datetime

import sys
sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import joseconfig as jconfig

from random import SystemRandom
random = SystemRandom()

DESCRIPTION_DATABASE = 'db/descriptions.json'
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

COLOR_API = 'http://thecolorapi.com'

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}
LOWERCASE, UPPERCASE = 'x', 'X'

def hex_to_rgb(triplet):
    triplet = triplet.lstrip('#')
    try:
        return _HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]]
    except:
        return None

def rgb_to_hex(triplet):
    return '%02x%02x%02x' % triplet

class joseXtra(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.docs = docsdict
        self.sock_start = time.time()
        self.socket_stats = collections.Counter()

        self.msgcount_min = 0
        self.msgcount_hour = 0
        self.total_msg = 0

        self.best_msg_minute = 0
        self.best_msg_hour = 0

        # every minute, show josé's usage
        self.cbk_new("jxtra.msgcount", self.msg_count_minute, 60)
        self.cbk_new("jxtra.msgcount_hour", self.msg_count_hour, 3600)

    async def ext_load(self):
        try:
            self.jsondb('descdb', path=DESCRIPTION_DATABASE)
            return True, ''
        except Exception as err:
            return False, ''

    async def ext_unload(self):
        try:
            self.cbk_remove('jxtra.msgcount')
            self.cbk_remove('jxtra.msgcount_hour')
            return True, ''
        except Exception as err:
            return False, ''

    async def msg_count_minute(self):
        if self.msgcount_min > 0:
            if self.msgcount_min > self.best_msg_minute:
                self.best_msg_minute = self.msgcount_min
            self.logger.info("Received %d messages/minute", self.msgcount_min)

        self.msgcount_min = 0

    async def msg_count_hour(self):
        if self.msgcount_hour > 0:
            if self.msgcount_hour > self.best_msg_hour:
                self.best_msg_hour = self.msgcount_hour
            self.logger.info("Received %d messages/hour", self.msgcount_hour)

        self.msgcount_hour = 0

    async def e_any_message(self, message, cxt):
        self.msgcount_min += 1
        self.msgcount_hour += 1
        self.total_msg += 1

    async def e_socket_response(self, msg):
        self.socket_stats[msg.get('t')] += 1

    def bot_human_ratio(self, server):
        bots = [member for member in server.members if member.bot]
        humans = [member for member in server.members if not member.bot]

        return bots, humans, (len(bots) / len(humans))

    def bhratio_global(self):
        all_members = self.client.get_all_members

        bots = [member for member in all_members() if member.bot]
        humans = [member for member in all_members() if not member.bot]

        return bots, humans, (len(bots) / len(humans))

    async def e_server_join(self, server, channel):
        # bots-to-members ratio
        bots, humans, ratio = self.bot_human_ratio(server)
        self.logger.info("ratio %dbots / %dhumans = %.2f", len(bots), len(humans), ratio)

        if ratio > 2:
            self.logger.warning("BOT RATIO > 2, BLOCKING %s[%s]", \
                server.name, server.id)
            self.client.jose.blocks['guilds'].append(server.id)

    async def c_bhratio(self, message, args, cxt):
        bots, humans, ratio = self.bot_human_ratio(message.server)
        await cxt.say("%d bots / %d humans = `%.2fb/h`, global is `%.2fb/h`", \
            ( len(bots), len(humans), ratio, self.bhratio_global()[2] ))

    async def c_sockstats(self, message, args, cxt):
        '''`j!sockstats` - Socket Stats'''
        delta = time.time() - self.sock_start
        minutes = delta / 60
        total = sum(self.socket_stats.values())
        events_minute = total / minutes

        await cxt.say("%d socket events, %.2f/minute:\n%s", \
            (total, events_minute, self.socket_stats))

    async def c_msgstats(self, message, args, cxt):
        '''`j!msgstats` - Show message rate statistics'''
        res = []

        res.append("In this current session:")
        res.append("Current messages/minute rate: %d msg/min" % (self.msgcount_min))
        res.append("Current messages/hour rate: %d msg/hour" % (self.msgcount_hour))
        res.append("Best messages/minute rate: %d msg/min" % (self.best_msg_minute))
        res.append("Best messages/hour rate: %d msg/hour" % (self.best_msg_hour))
        res.append("Total messages received: %d" % (self.total_msg))

        await cxt.say(self.codeblock("", '\n'.join(res)))

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

    async def c_commands(self, message, args, cxt):
        await cxt.say(self.docs['commands'])

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

    def mkcolor(self, name):
        colorval = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:6], 16)
        return discord.Colour(colorval)

    def delta_str(self, delta):
        seconds = delta.total_seconds()
        years = seconds / 60 / 60 / 24 / 365.25
        days = seconds / 60 / 60 / 24
        if years >= 1:
            return f'{years:.2f} years'
        else:
            return f'{days:.2f} days'

    async def c_profile(self, message, args, cxt):
        '''`j!profile [@mention]` - profile card stuff'''
        await cxt.send_typing()

        user = message.author
        acc_id = message.author.id

        try:
            _acc_id = await jcommon.parse_id(args[1])
            if _acc_id is not None:
                acc_id = _acc_id
        except IndexError:
            pass
        except Exception as err:
            await cxt.say("`%r`", (err,))
            return

        if acc_id != message.author.id:
            user = await self.client.get_user_info(acc_id)

        em = discord.Embed(title='Profile card', colour=self.mkcolor(user.name))

        if len(user.avatar_url) > 0:
            em.set_thumbnail(url=user.avatar_url)

        em.set_footer(text="User ID: {}".format(user.id))

        if hasattr(user, 'nick'):
            if user.nick is not None:
                em.add_field(name='Name', value='{} ({})'.format( \
                    user.nick, user.name))
            else:
                em.add_field(name='Name', value='{}'.format(user.name))
        else:
            em.add_field(name='Name', value='{}'.format(user.name))

        description = self.descdb.get(user.id)
        if description is not None:
            em.add_field(name='Description', value=description)

        # check if admin
        if user.id in jcommon.ADMIN_TOPICS:
            topic = jcommon.ADMIN_TOPICS[user.id]
            em.add_field(name='José Admin! Works on', value=topic[0])

        delta = datetime.datetime.now() - user.created_at
        em.add_field(name='Discord account age', value='{}'.format(self.delta_str(delta)))

        if acc_id in self.jcoin.data:
            account = self.jcoin.data.get(acc_id)

            _gaccounts = [userid for userid in self.jcoin.data \
                if message.server.get_member(userid) is not None]

            gacc_sorted = sorted(_gaccounts, key=lambda userid: \
                self.jcoin.data[userid]['amount'], reverse=True)

            sorted_data = sorted(self.jcoin.data, key=lambda userid: \
                self.jcoin.data[userid]['amount'], reverse=True)

            # index start from 0
            guildrank = gacc_sorted.index(acc_id) + 1
            globalrank = sorted_data.index(acc_id) + 1

            em.add_field(name='JoséCoin Rank', value='{}/{} ({}/{} globally)'.format( \
                guildrank, len(gacc_sorted), \
                globalrank, len(sorted_data))
            )

            em.add_field(name='JoséCoin Wallet', value='{}JC'.format(account['amount']))
            em.add_field(name='Tax paid', value='{}JC'.format(account['taxpaid']))

            em.add_field(name='Stealing', value='{} tries, {} success'.format( \
                account['times_stolen'], account['success_steal']))

        await cxt.say_embed(em)

    async def c_setdesc(self, message, args, cxt):
        '''`j!setdesc stuff` - set your description(max 140 chars)'''

        if len(args) < 2:
            await cxt.say(self.c_setdesc.__doc__)
            return

        new_description = ' '.join(args[1:])

        if len(new_description) > 140:
            await cxt.say("Your description has more than 140 characters.")
            return

        self.descdb[message.author.id] = new_description
        self.jsondb_save('descdb')
        await cxt.say("description set to `%r`!", (new_description,))

    async def c_color(self, message, args, cxt):
        '''`j!color "rand"|#aabbcc|red,green,blue` - show colors'''

        if len(args) < 2:
            await cxt.say(self.c_color.__doc__)
            return

        color = (0, 0, 0)
        mk_rand = False

        if args[1] == 'rand':
            mk_rand = True

        elif args[1].startswith('#'):
            # parse hex #aabbcc
            if len(args[1]) > 7:
                await cxt.say("`#aabbcc` format not recognized")
                return
            color = hex_to_rgb(args[1])
            if color is None:
                await cxt.say("Error recognizing hex data")
                return

        elif args[1].find(','):
            # parse rgb int,int,int
            sp = args[1].split(',')

            if len(sp) != 3:
                await cxt.say("Error parsing rgb(RED, GRN, BLU)")
                return

            for (i, el) in enumerate(sp):
                try:
                    sp[i] = int(el)
                    if sp[i] < 0 or sp[i] >= 255:
                        await cxt.say("`%r` out or range 0-255")
                        return
                except:
                    await cxt.say("Error converting `%r` to Integer base 10", \
                        (el,))
                    return

            red, green, blue = sp
            color = (red, green, blue)

        if mk_rand:
            red = random.randint(0x0, 0xff)
            green = random.randint(0x0, 0xff)
            blue = random.randint(0x0, 0xff)
            color = (red, green, blue)

        imageurl = 'http://placehold.it/100x100.png/{}'.format\
            (rgb_to_hex(color).upper())

        await cxt.say('Color `%s`: %s', (color, imageurl))

    async def c_avatar(self, message, args, cxt):
        '''`j!avatar [@someone]` - get avatar for person!!!1'''

        user = message.author
        acc_id = message.author.id

        try:
            _acc_id = await jcommon.parse_id(args[1])
            if _acc_id is not None:
                acc_id = _acc_id
        except IndexError:
            pass
        except Exception as err:
            await cxt.say("`%r`", (err,))
            return

        if acc_id != message.author.id:
            user = await self.client.get_user_info(acc_id)

        await cxt.say("This is what discord gave me: %s", \
            (user.avatar_url.replace('webp', 'png'),))

    async def c_snoop(self, message, args, cxt):
        '''`j!snoop amount guildid` - snoop on messages'''
        await self.is_admin(message.author.id)

        if len(args) < 3:
            await cxt.say(self.c_snoop.__doc__)
            return

        try:
            amount = int(args[1])
        except:
            await cxt.say("Error parsing `amount`")
            return

        try:
            channel_id = args[2]
        except:
            await cxt.say("Error parsing `channelid`")
            return

        if channel_id == 'global':
            base_messages = sorted([m for m in self.client.messages if \
                m.author.id != jcommon.JOSE_ID], key=lambda m: m.timestamp, reverse=True)

            _messages = [(str(m.author), '#%s: %s' % (str(m.channel), m.content)) for m in \
                base_messages][:amount]
        else:
            base_messages = sorted([m for m in self.client.messages], \
                key=lambda m: m.timestamp, reverse=True)

            _messages = [(str(m.author), '%s' % (m.content)) for m in base_messages if \
                m.channel.id == channel_id][:amount]

        if len(_messages) < 1:
            await cxt.say("No messages found")
            return

        messages = '\n'.join(('%s: %s' % tup for tup in reversed(_messages)))

        await cxt.say(self.codeblock("", messages))

    async def c_testembed(self, message, args, cxt):
        emojoj = '<:cody1:266337951586189312>'
        em = discord.Embed(colour=discord.Colour.purple(), title='test')
        em.add_field(name=emojoj, value="fuck")
        await cxt.say_embed(em)

    async def c_pinch(self, message, args, cxt):
        try:
            p1 = args[1]
        except:
            await cxt.say("Error parsing p1")
            return

        await cxt.say("{} got pinched by {} for not wearing green!\n{}".format\
            (p1, message.author, 'http://theotakuspot.animeblogger.net/wp-content/uploads/2007/10/shana2-3.png'))

    async def c_betterping(self, message, args, cxt):
        res = []
        delta_cmd_process = (time.time() - cxt.t_creation) * 1000
        res.append("`cmd_process`: **%.2fms**" % delta_cmd_process)

        ping_st = time.monotonic()
        await cxt.send_typing()
        ping_st_end = time.monotonic()
        delta_st = (ping_st_end - ping_st) * 1000
        res.append("`send_typing`: **%.2fms**" % delta_st)

        ping_sm = time.monotonic()
        pong = await cxt.send("pong")
        ping_sm_end = time.monotonic()
        delta_sm = (ping_sm_end - ping_sm) * 1000
        res.append("`send_message`: **%.2fms**" % delta_sm)

        await asyncio.sleep(0.3)

        ping_em = time.monotonic()
        await self.client.edit_message(pong, "pong 2")
        ping_em_end = time.monotonic()
        delta_em = (ping_em_end - ping_em) * 1000
        res.append("`edit_message`: **%.2fms**" % delta_em)

        await asyncio.sleep(0.3)

        ping_dm = time.monotonic()
        await self.client.delete_message(pong)
        ping_dm_end = time.monotonic()
        delta_dm = (ping_dm_end - ping_dm) * 1000
        res.append("`delete_message`: **%.2fms**" % delta_dm)

        await cxt.say('\n'.join(res))
