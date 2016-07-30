import discord
import asyncio

import sys
import time
import os

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
            f()
        else:
            yield from self.debug("PermError: sem permissão")

    @asyncio.coroutine
    def turnoff(self):
        yield from jcommon.josecoin_save(message, True)
        yield from self.client.logout()
        sys.exit(0)

    @asyncio.coroutine
    def reboot(self):
        yield from jcommon.josecoin_save(message, True)
        yield from self.client.logout()
        os.system("./reload_jose.sh &")
        sys.exit(0)

    @asyncio.coroutine
    def update(self):
        banner = "atualizando josé para nova versão(era v%s b%d)" % (jcommon.JOSE_VERSION, jcommon.JOSE_BUILD)
        yield from self.debug(banner)
        yield from jcommon.josecoin_save(message, True)
        yield from client.logout()
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
    def c_jbot(self, message, args):
        yield from self.say("Olá do módulo jose.py")

    @asyncio.coroutine
    def recv(self, message):
        self.current = message
