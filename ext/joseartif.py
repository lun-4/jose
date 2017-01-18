#!/usr/bin/env python3

import discord
import asyncio
import sys
import json

from chatterbot import ChatBot
chatbot = ChatBot(
    "José",
    storage_adapter='chatterbot.storage.JsonFileStorageAdapter',
    logic_adapters=[
        'chatterbot.logic.BestMatch'
    ],
    trainer='chatterbot.trainers.ChatterBotCorpusTrainer'
)

chatbot.train("chatterbot.corpus.portuguese.conversations")

sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import joseerror as je

from random import SystemRandom
random = SystemRandom()

# 3 percent of all messages
ARTIF_CHATINESS = .03

class JoseArtif(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.jose_mention = "<@%s>" % jcommon.JOSE_ID
        self.answers = 0

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def e_on_message(self, message):
        '''# give up on anything related, use chatterbot
        if random.random() < ARTIF_CHATINESS or self.jose_mention in message.content:
            self.current = message
            await self.client.send_typing(message.channel)
            msg = message.content.replace(self.jose_mention, "")
            answer = chatbot.get_response(msg)
            self.answers += 1
            await self.say(answer)'''
        pass

    async def c_chatstatus(self, message, args):
        with open('database.db', 'r') as f:
            dbjson = json.load(f)
        len_entries = len(dbjson)
        report_str = """Status Report: ```
I made %d answers in this session
I have %d entries in my database
```""" % (self.answers, len_entries)
        await self.say(report_str)
