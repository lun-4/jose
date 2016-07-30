import discord
import asyncio

class JoseBot:
    def __init__(self, cl):
        self.client = cl
        self.current = None

    @asyncio.coroutine
    def say(self, msg):
        yield from self.client.send_message(self.current.channel, msg)

    @asyncio.coroutine
    def c_jbot(self, args, message):
        yield from self.say("Olá do módulo jose.py")

    @asyncio.coroutine
    def recv(self, message):
        self.current = message
