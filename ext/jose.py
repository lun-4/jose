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
    def c_exit(self, message, args):
        try:
            auth = yield from jcommon.check_roles(jcommon.MASTER_ROLE, message.author.roles)
            if auth:
                yield from self.debug("AuthModule: autorização concluída")
                yield from jcommon.josecoin_save(message, True)
                yield from self.client.logout()
                sys.exit(0)
            else:
                yield from self.debug("PermError: sem permissão para desligar jose-bot")
        except Exception as e:
            yield from self.debug("c_exit: pyerr: %s" % e)
        return

    @asyncio.coroutine
    def c_jbot(self, message, args):
        yield from self.say("Olá do módulo jose.py")

    @asyncio.coroutine
    def recv(self, message):
        self.current = message
