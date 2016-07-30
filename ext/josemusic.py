import asyncio
import discord
from discord.ext import commands

# sanity test
if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

class JoseMusic:
    def __init__(self, cl):
        self.client = cl
        self.c_message = ''

    @asyncio.coroutine
    def say(self, msg):
        yield from self.client.send_message(self.c_message.channel, msg)

    @asyncio.coroutine
    def c_status(self, msg):
        yield from self.say("ESTOU FUNCIONANDO SEU HIJO DA PUTA")

    @asyncio.coroutine
    def recv(self, msg):
        self.c_message = msg

jm = JoseMusic(None)

cmds_start = {
    '!mstat': jm.c_status,
}
