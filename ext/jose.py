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
        jcommon.Extension.__init__(self, cl)

    @asyncio.coroutine
    def sec_auth(self, f):
        auth = yield from jcommon.check_roles(jcommon.MASTER_ROLE, self.current.author.roles)
        if auth:
            yield from self.debug("auth: autorizado")
            yield from f()
        else:
            yield from self.debug("PermError: sem permissão")

    @asyncio.coroutine
    def turnoff(self):
        yield from jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        yield from self.client.logout()
        sys.exit(0)

    @asyncio.coroutine
    def reboot(self):
        yield from jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        yield from self.client.logout()
        os.system("./reload_jose.sh &")
        sys.exit(0)

    @asyncio.coroutine
    def update(self):
        banner = "atualizando josé para nova versão(era v%s b%d)" % (jcommon.JOSE_VERSION, jcommon.JOSE_BUILD)
        yield from self.debug(banner)
        yield from jcoin.JoseCoin(self.client).josecoin_save(self.current, True)
        yield from self.client.logout()
        os.system("./reload_jose.sh &")
        sys.exit(0)

    @asyncio.coroutine
    def c_exit(self, message, args):
        yield from self.sec_auth(self.turnoff)

    @asyncio.coroutine
    def c_reboot(self, message, args):
        yield from self.sec_auth(self.reboot)

    @asyncio.coroutine
    def c_update(self, message, args):
        yield from self.sec_auth(self.update)

    @asyncio.coroutine
    def c_xkcd(self, message, args):
        n = False
        if len(args) > 1:
            n = args[1]

        loop = asyncio.get_event_loop()

        url = "http://xkcd.com/info.0.json"
        r = yield from aiohttp.request('GET', url)
        content = yield from r.text()

        info_latest = info = json.loads(content)
        info = None
        try:
            if not n:
                info = info_latest
                n = info['num']
            elif n == 'random' or n == 'r' or n == 'rand':
                rn_xkcd = random.randint(0, info_latest['num'])

                url = "http://xkcd.com/{0}/info.0.json".format(rn_xkcd)
                r = yield from aiohttp.request('GET', url)
                content = yield from r.text()

                info = json.loads(content)
            else:
                url = "http://xkcd.com/{0}/info.0.json".format(n)
                r = yield from aiohttp.request('GET', url)
                content = yield from r.text()
                info = json.loads(content)
            yield from self.say('xkcd número %s : %s' % (n, info['img']))

        except Exception as e:
            yield from self.debug("xkcd: pyerr: %s" % str(e))

    @asyncio.coroutine
    def c_rand(self, message, args):
        n_min, n_max = 0,0
        try:
            n_min = int(args[1])
            n_max = int(args[2])
        except:
            yield from self.debug("erro parseando os números para a função.")
            return

        if n_min > n_max:
            yield from self.debug("minimo > máximo, intervalo não permitido")
            return

        n_rand = random.randint(n_min, n_max)
        yield from self.say("Número aleatório de %d a %d: %d" % (n_min, n_max, n_rand))
        return

    @asyncio.coroutine
    def c_enc(self, message, args):
        to_encrypt = ' '.join(args[1:])
        encdata = yield from jcommon.str_xor(to_encrypt, jcommon.JCRYPT_KEY)
        a85data = base64.a85encode(bytes(encdata, 'UTF-8'))
        yield from self.say('resultado(enc): %s' % a85data.decode('UTF-8'))
        return

    @asyncio.coroutine
    def c_dec(self, message, args):
        to_decrypt = ' '.join(args[1:])
        to_decrypt = to_decrypt.encode('UTF-8')
        to_decrypt = base64.a85decode(to_decrypt).decode('UTF-8')
        plaintext = yield from jcommon.str_xor(to_decrypt, jcommon.JCRYPT_KEY)
        yield from self.say("resultado(dec): %s" % plaintext)
        return

    @asyncio.coroutine
    def c_money(self, message, args):
        amount = float(args[1])
        currency_from = args[2]
        currency_to = args[3]

        loop = asyncio.get_event_loop()

        baseurl = "http://api.fixer.io/latest?base={}".format(currency_from.upper())
        r = yield from aiohttp.request('GET', url)
        content = yield from r.text()
        data = json.loads(content)

        if 'error' in data:
            yield from self.debug("!money: %s" % data['error'])
            return

        rate = data['rates'][currency_to]
        res = amount * rate

        yield from self.say('{} {} = {} {}'.format(
            amount, currency_from, res, currency_to
        ))

    @asyncio.coroutine
    def c_yt(self, message, args):
        search_term = ' '.join(args[1:])

        loop = asyncio.get_event_loop()

        print("!yt @ %s : %s" % (message.author.id, search_term))

        query_string = urllib.parse.urlencode({"search_query" : search_term})

        url = "http://www.youtube.com/results?" + query_string
        future_search = loop.run_in_executor(None, urllib.request.urlopen, url)
        html_content = yield from future_search

        future_re = loop.run_in_executor(None, re.findall, r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
        search_results = yield from future_re

        if len(search_results) < 2:
            yield from client.send_message(message.channel, "!yt: Nenhum resultado encontrado.")
            return

        yield from self.say("http://www.youtube.com/watch?v=" + search_results[0])

    @asyncio.coroutine
    def c_sndc(self, message, args):
        query = ' '.join(args[1:])
        print("soundcloud -> %s" % query)

        if len(query) < 3:
            yield from self.say("preciso de mais coisas para pesquisar(length < 3)")
            return

        search_url = 'https://api.soundcloud.com/search?q=%s&facet=model&limit=10&offset=0&linked_partitioning=1&client_id='+jconfig.soundcloud_id
        url = search_url % urllib.parse.quote(query)

        while url:
            response = yield from aiohttp.request('GET', url)

            if response.status != 200:
                yield from self.debug("!sndc: error: status code != 200(st = %d)" % response.status)
                return

            try:
                doc = yield from response.json()
            except Exception as e:
                yield from jose_debug(message, "!sndc: py_err %s" % str(e))
                return

            for entity in doc['collection']:
                if entity['kind'] == 'track':
                    yield from self.say(entity['permalink_url'])
                    return

            yield from self.say("verifique sua pesquisa, porque nenhuma track foi encontrada.")
            return

    @asyncio.coroutine
    def c_playing(self, message, args):
        playing_name = ' '.join(args[1:])
        g = discord.Game(name=playing_name, url=playing_name, type='game')
        yield from self.client.change_status(g)

    @asyncio.coroutine
    def c_fullwidth(self, message, args):
        ascii_text = ' '.join(args[1:])
        res = ascii_text.translate(jcommon.ascii_to_wide)
        yield from self.say(res)

    @asyncio.coroutine
    def c_escolha(self, message, args):
        escolhas = (' '.join(args[1:])).split(';')
        choice = random.choice(escolhas)
        yield from self.say("Eu escolho %s" % choice)

    @asyncio.coroutine
    def c_nick(self, message, args):
        auth = yield from jcommon.check_roles(jcommon.MASTER_ROLE, message.author.roles)
        if not auth:
            yield from self.debug("PermissionError: Não pode mudar o nick do josé.")
            return

        if len(args) < 2:
            self.nick = 'jose-bot'
        else:
            self.nick = ' '.join(args[1:])

        for server in self.client.servers:
            m = server.get_member(jcommon.JOSE_ID)
            yield from self.client.change_nickname(m, self.nick)

        return

    @asyncio.coroutine
    def c_distatus(self, m, a):
        auth = yield from self.rolecheck(jcommon.MASTER_ROLE)
        if not auth:
            yield from self.say("PermissionError: permissão negada")
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

        yield from self.say(fmt % (host, rtt[0], rtt[1], rtt[2], rtt[3], looks_like))

    @asyncio.coroutine
    def c_jbot(self, message, args):
        yield from self.say("Olá do módulo jose.py")

    @asyncio.coroutine
    def recv(self, message):
        self.current = message

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

    @asyncio.coroutine
    def load_ext(self, n, n_cl):
        loaded_success = False

        module = None
        if n in self.modules: #already loaded
            module = importlib.reload(self.modules[n]['module'])
        else:
            module = importlib.import_module('ext.%s' % n)

        inst = getattr(module, n_cl)(self.client)
        try:
            yield from inst.ext_load()
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
                yield from self.say(":ok_hand:")
            else:
                yield from self.say(":poop:")
        else:
            print("load_ext: carregado %s" % n)

    @asyncio.coroutine
    def c_reload(self, message, args):
        auth = yield from self.rolecheck(jcommon.MASTER_ROLE)
        if not auth:
            yield from self.say("PermError: permissão negada")
            return

        n = args[1]
        if n in self.modules:
            yield from self.load_ext(n, self.modules[n]['class'])
        else:
            yield from self.say("%s: módulo não encontrado/carregado" % n)

    @asyncio.coroutine
    def c_modules(self, message, args):
        mod_gen = (key for key in self.modules)
        mod_generator = []
        for key in mod_gen:
            if 'module' in self.modules[key]:
                mod_generator.append('ext:%s' % key)
            else:
                mod_generator.append('gext:%s' % key)
        yield from self.say("módulos carregados: %s" % (" ".join(mod_generator)))

    # !eval `yield from self.say("hello")`
    # !eval `self.loop.run_until_complete(self.say("Hello"))`
    # !eval `self.loop.run_until_complete(self.reboot())`
    # !eval `self.says(str(self.modules))`
    # !eval `self.loop.run_until_complete(self.say(discord.__version__))`
    @asyncio.coroutine
    def c_eval(self, message, args):
        # eval expr
        yield from self.rolecheck(jcommon.MASTER_ROLE)

        eval_cmd = ' '.join(args[1:])
        if eval_cmd[0] == '`' and eval_cmd[-1] == '`':
            eval_cmd = eval_cmd[1:-1]
        res = eval(eval_cmd)
        yield from self.say("```%s``` -> `%s`" % (eval_cmd, res))

    def says(self, msg):
        # calls self.say but in an non-async way
        asyncio.async(self.say(msg), loop=self.loop)
