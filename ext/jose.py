import discord
import asyncio

import sys
import time
import os
from random import SystemRandom
random = SystemRandom()
import base64
import subprocess

import aiohttp
import urllib.parse
import urllib.request
import re
import json
import importlib

sys.path.append("..")
import josecommon as jcommon
import joseerror as je
import joseconfig as jconfig
import jcoin.josecoin as jcoin

jose_debug = jcommon.jose_debug

class JoseBot(jcommon.Extension):
    def __init__(self, cl):
        self.nick = 'jose-bot'
        self.modules = {}
        self.env = {
            'survey': {},
            'spam': {},
            'spamcl': {},
            'apostas': {},
        }
        self.start_time = time.time()
        jcommon.Extension.__init__(self, cl)

    def load_gext(self, inst, n):
        print("carregando módulo: %s" % n)
        methods = (method for method in dir(inst) if callable(getattr(inst, method)))

        self.modules[n] = {'inst': inst, 'methods': [], 'class': ''}

        for method in methods:
            if method.startswith('c_'):
                print("add %s" % method)
                setattr(self, method, getattr(inst, method))
                self.modules[n]['methods'].append(method)

        print("módulo carregado: %s" % n)
        return True

    async def load_ext(self, n, n_cl):
        loaded_success = False

        module = None
        if n in self.modules: #already loaded
            module = importlib.reload(self.modules[n]['module'])
        else:
            module = importlib.import_module('ext.%s' % n)

        inst = getattr(module, n_cl)(self.client)
        try:
            await inst.ext_load()
        except:
            print("%s doesn't have any ext_load method" % module)
        methods = (method for method in dir(inst) if callable(getattr(inst, method)))

        self.modules[n] = {'inst': inst, 'methods': [], 'class': n_cl, 'module': module}

        for method in methods:
            if method.startswith('c_'):
                print("add %s" % method)
                setattr(self, method, getattr(inst, method))
                self.modules[n]['methods'].append(method)
                loaded_success = True

        if self.current is not None:
            if loaded_success:
                await self.say(":ok_hand:")
            else:
                await self.say(":poop:")
        else:
            print("load_ext: carregado %s" % n)

    async def c_reload(self, message, args):
        auth = await self.rolecheck(jcommon.MASTER_ROLE)
        if not auth:
            await self.say("PermError: permissão negada")
            return

        n = args[1]
        if n in self.modules:
            await self.load_ext(n, self.modules[n]['class'])
        else:
            await self.say("%s: módulo não encontrado/carregado" % n)

    async def c_modules(self, message, args):
        mod_gen = (key for key in self.modules)
        mod_generator = []
        for key in mod_gen:
            if 'module' in self.modules[key]:
                # normally loaded ext, can use !reload on it
                mod_generator.append('ext:%s' % key)
            else:
                # externally loaded ext, can reload
                mod_generator.append('gext:%s' % key)
        await self.say("módulos carregados: %s" % (" ".join(mod_generator)))

    def says(self, msg):
        # calls self.say but in an non-async way
        asyncio.async(self.say(msg), loop=self.loop)

    async def c_help(self, message, args):
        await self.say(jcommon.JOSE_HELP_TEXT, channel=message.author)

    async def c_htgeral(self, message, args):
        await self.say(jcommon.JOSE_GENERAL_HTEXT, channel=message.author)

    async def c_httech(self, message, args):
        await self.say(jcommon.JOSE_TECH_HTEXT, channel=message.author)

    async def sec_auth(self, f):
        auth = await jcommon.check_roles(jcommon.MASTER_ROLE, self.current.author.roles)
        if auth:
            await self.debug("auth: autorizado")
            await f()
        else:
            await self.debug("PermError: sem permissão")

    async def turnoff(self):
        await jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        await self.client.logout()
        sys.exit(0)

    async def reboot(self):
        await jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        await self.client.logout()
        os.system("./reload_jose.sh &")
        sys.exit(0)

    async def update(self):
        banner = "atualizando josé para nova versão(era v%s b%d)" % (jcommon.JOSE_VERSION, jcommon.JOSE_BUILD)
        await self.debug(banner)
        await jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        await self.client.logout()
        os.system("./reload_jose.sh &")
        sys.exit(0)

    async def c_exit(self, message, args):
        await self.sec_auth(self.turnoff)

    async def c_reboot(self, message, args):
        await self.sec_auth(self.reboot)

    async def c_update(self, message, args):
        await self.sec_auth(self.update)

    async def c_xkcd(self, message, args):
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

    async def c_rand(self, message, args):
        n_min, n_max = 0,0
        try:
            n_min = int(args[1])
            n_max = int(args[2])
        except:
            await self.debug("erro parseando os números para a função.")
            return

        if n_min > n_max:
            await self.debug("minimo > máximo, intervalo não permitido")
            return

        n_rand = random.randint(n_min, n_max)
        await self.say("Número aleatório de %d a %d: %d" % (n_min, n_max, n_rand))
        return

    async def c_enc(self, message, args):
        to_encrypt = ' '.join(args[1:])
        encdata = await jcommon.str_xor(to_encrypt, jcommon.JCRYPT_KEY)
        a85data = base64.a85encode(bytes(encdata, 'UTF-8'))
        await self.say('resultado(enc): %s' % a85data.decode('UTF-8'))
        return

    async def c_dec(self, message, args):
        to_decrypt = ' '.join(args[1:])
        to_decrypt = to_decrypt.encode('UTF-8')
        to_decrypt = base64.a85decode(to_decrypt).decode('UTF-8')
        plaintext = await jcommon.str_xor(to_decrypt, jcommon.JCRYPT_KEY)
        await self.say("resultado(dec): %s" % plaintext)
        return

    async def c_money(self, message, args):
        amount = float(args[1])
        currency_from = args[2]
        currency_to = args[3]

        loop = asyncio.get_event_loop()

        url = "http://api.fixer.io/latest?base={}".format(currency_from.upper())
        r = await aiohttp.request('GET', url)
        content = await r.text()
        data = json.loads(content)

        if 'error' in data:
            await self.debug("!money: %s" % data['error'])
            return

        rate = data['rates'][currency_to]
        res = amount * rate

        await self.say('{} {} = {} {}'.format(
            amount, currency_from, res, currency_to
        ))

    async def c_yt(self, message, args):
        search_term = ' '.join(args[1:])

        loop = asyncio.get_event_loop()

        print("!yt @ %s : %s" % (message.author.id, search_term))

        query_string = urllib.parse.urlencode({"search_query" : search_term})

        url = "http://www.youtube.com/results?" + query_string
        future_search = loop.run_in_executor(None, urllib.request.urlopen, url)
        html_content = await future_search

        future_re = loop.run_in_executor(None, re.findall, r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
        search_results = await future_re

        if len(search_results) < 2:
            await client.send_message(message.channel, "!yt: Nenhum resultado encontrado.")
            return

        await self.say("http://www.youtube.com/watch?v=" + search_results[0])

    async def c_sndc(self, message, args):
        query = ' '.join(args[1:])
        print("soundcloud -> %s" % query)

        if len(query) < 3:
            await self.say("preciso de mais coisas para pesquisar(length < 3)")
            return

        search_url = 'https://api.soundcloud.com/search?q=%s&facet=model&limit=10&offset=0&linked_partitioning=1&client_id='+jconfig.soundcloud_id
        url = search_url % urllib.parse.quote(query)

        while url:
            response = await aiohttp.request('GET', url)

            if response.status != 200:
                await self.debug("!sndc: error: status code != 200(st = %d)" % response.status)
                return

            try:
                doc = await response.json()
            except Exception as e:
                await jose_debug(message, "!sndc: py_err %s" % str(e))
                return

            for entity in doc['collection']:
                if entity['kind'] == 'track':
                    await self.say(entity['permalink_url'])
                    return

            await self.say("verifique sua pesquisa, porque nenhuma track foi encontrada.")
            return

    async def c_playing(self, message, args):
        playing_name = ' '.join(args[1:])
        g = discord.Game(name=playing_name, url=playing_name, type='game')
        await self.client.change_status(g)

    async def c_fullwidth(self, message, args):
        ascii_text = ' '.join(args[1:])
        res = ascii_text.translate(jcommon.ascii_to_wide)
        await self.say(res)

    async def c_escolha(self, message, args):
        escolhas = (' '.join(args[1:])).split(';')
        choice = random.choice(escolhas)
        await self.say("Eu escolho %s" % choice)

    async def c_nick(self, message, args):
        auth = await jcommon.check_roles(jcommon.MASTER_ROLE, message.author.roles)
        if not auth:
            await self.debug("PermissionError: Não pode mudar o nick do josé.")
            return

        if len(args) < 2:
            self.nick = 'jose-bot'
        else:
            self.nick = ' '.join(args[1:])

        for server in self.client.servers:
            m = server.get_member(jcommon.JOSE_ID)
            await self.client.change_nickname(m, self.nick)

        return

    async def c_distatus(self, m, a):
        auth = await self.rolecheck(jcommon.MASTER_ROLE)
        if not auth:
            await self.say("PermissionError: permissão negada")
            return

        host = "discordapp.com"

        ping = subprocess.Popen(
            ["ping", "-c", "6", host],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        out, error = ping.communicate()
        matcher = re.compile("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")
        rtt = matcher.search(out.decode('utf-8')).groups()

        fmt = 'ping to `%s` min %sms avg %sms max %sms mdev %sms\n%s'
        looks_like = ''
        if float(rtt[1]) > 100:
            looks_like = 'Parece que algo tá rodando ruim nos servidores, cheque http://status.discordapp.com'
        elif float(rtt[2]) > 150:
            looks_like = 'Alguma coisa deve ter ocorrido no meio dos pings, tente denovo'
        else:
            looks_like = 'Tudo bem... eu acho'

        await self.say(fmt % (host, rtt[0], rtt[1], rtt[2], rtt[3], looks_like))

    async def c_version(self, message, args):
        pyver = '%d.%d.%d' % (sys.version_info[:3])
        await self.say("José v%s b%d py:%s discord.py:%s" % (jcommon.JOSE_VERSION,
            jcommon.JOSE_BUILD, pyver, discord.__version__))

    async def c_jose_add(self, message, args):
        await self.say("José pode ser adicionado para outro servidor usando este link:\n```%s```" % jcommon.OAUTH_URL)

    async def c_fale(self, message, args):
        await speak_routine(message, True)

    async def c_uptime(self, message, args):
        sec = (time.time() - self.start_time)
        MINUTE  = 60
        HOUR    = MINUTE * 60
        DAY     = HOUR * 24

        days    = int(sec / DAY)
        hours   = int((sec % DAY) / HOUR)
        minutes = int((sec % HOUR) / MINUTE)
        seconds = int(sec % MINUTE)

        fmt = "uptime: %d dias, %d horas, %d minutos, %d segundos"
        await self.debug(fmt % (days, hours, minutes, seconds))

    async def c_jbot(self, message, args):
        await self.say("Olá do módulo jose.py")

    # !eval `await self.say("hello")`
    # !eval `self.loop.run_until_complete(self.say("Hello"))`
    # !eval `self.loop.run_until_complete(self.reboot())`
    # !eval `self.says(str(self.modules))`
    # !eval `self.loop.run_until_complete(self.say(discord.__version__))`
    async def c_eval(self, message, args):
        # eval expr
        await self.rolecheck(jcommon.MASTER_ROLE)

        eval_cmd = ' '.join(args[1:])
        if eval_cmd[0] == '`' and eval_cmd[-1] == '`':
            eval_cmd = eval_cmd[1:-1]
        res = eval(eval_cmd)
        await self.say("```%s``` -> `%s`" % (eval_cmd, res))
