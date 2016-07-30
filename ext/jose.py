import discord
import asyncio

import sys
import time
import os

from .. import josecommon as jcommon
from .. import jcoin.josecoin as jcoin

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
    def c_exit(self, args, message):
        try:
            auth = yield from jcommon.check_roles(jcommon.MASTER_ROLE, message.author.roles)
            if auth:
                yield from jcoin.josecoin_save(message)
                yield from self.debug("saindo")
                yield from self.client.logout()
                sys.exit(0)
            else:
                yield from self.debug(message, "PermError: sem permissão para desligar jose-bot")
        except Exception as e:
            yield from self.debug(message, "c_exit: pyerr: %s" % e)
        return

    @asyncio.coroutine
    def c_jbot(self, args, message):
        yield from self.say("Olá do módulo jose.py")

    @asyncio.coroutine
    def recv(self, message):
        self.current = message
