import discord
import asyncio

import sys
import time
import os
from random import SystemRandom
random = SystemRandom()

import requests

sys.path.append("..")
import josecommon as jcommon

jose_debug = jcommon.jose_debug

class JoseBot:
    def __init__(self, cl):
        self.client = cl
        self.current = None

    @asyncio.coroutine
    def say(self, msg):
        yield from self.client.send_message(self.current.channel, msg)

    @asyncio.coroutine
    def debug(self, msg):
        yield from jose_debug(self.current, msg)

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
        yield from jcommon.josecoin_save(self.current, True)
        yield from self.client.logout()
        sys.exit(0)

    @asyncio.coroutine
    def reboot(self):
        yield from jcommon.josecoin_save(self.current, True)
        yield from self.client.logout()
        os.system("./reload_jose.sh &")
        sys.exit(0)

    @asyncio.coroutine
    def update(self):
        banner = "atualizando josé para nova versão(era v%s b%d)" % (jcommon.JOSE_VERSION, jcommon.JOSE_BUILD)
        yield from self.debug(banner)
        yield from jcommon.josecoin_save(self.current, True)
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
        future_stmt = loop.run_in_executor(None, requests.get, url)
        r = yield from future_stmt

        info_latest = info = r.json()
        info = None
        try:
            if not n:
                info = info_latest
                n = info['num']
            elif n == 'random' or n == 'r' or n == 'rand':
                rn_xkcd = random.randint(0, info_latest['num'])

                url = "http://xkcd.com/{0}/info.0.json".format(rn_xkcd)
                future_stmt = loop.run_in_executor(None, requests.get, url)
                r = yield from future_stmt
                info = r.json()
            else:
                url = "http://xkcd.com/{0}/info.0.json".format(n)
                future_stmt = loop.run_in_executor(None, requests.get, url)
                r = yield from future_stmt
                info = r.json()
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

    @asyncio.coroutine
    def c_dec(self, message, args):
        to_decrypt = ' '.join(args[1:])
        to_decrypt = to_decrypt.encode('UTF-8')
        to_decrypt = base64.a85decode(to_decrypt).decode('UTF-8')
        plaintext = yield from jcommon.str_xor(to_decrypt, jcommon.JCRYPT_KEY)
        yield from self.say("resultado(dec): %s" % plaintext)

    @asyncio.coroutine
    def c_money(self, message, args):
        pass

    @asyncio.coroutine
    def c_jbot(self, message, args):
        yield from self.say("Olá do módulo jose.py")

    @asyncio.coroutine
    def recv(self, message):
        self.current = message
