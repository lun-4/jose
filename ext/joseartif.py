#!/usr/bin/env python3

import discord
import asyncio
import sys
import json

sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon
import joseerror as je

from random import SystemRandom
random = SystemRandom()

class JoseArtif(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.jose_mention = "<@%s>" % jcommon.JOSE_ID
        self.answers = 0

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def make_output(self, input):
        return False, "Nothing available"

    async def e_on_message(self, message, cxt):
        if True:
            # for now, disable this
            return

        if self.jose_mention in message.content:
            await self.client.send_typing(message.channel)
            msg = message.content.replace(self.jose_mention, "")
            answer = await make_output(msg)
            if not answer[0]:
                await self.say(":warning: %s :warning:" % answer[1])
            else:
                self.answers += 1
                await self.say(":speech_left: %s" % answer[1])

    async def c_chatstatus(self, message, args, cxt):
        report_str = """Chat Report: ```
I made %d answers in this session
```""" % (self.answers, len_entries)
        await cxt.say(report_str)
