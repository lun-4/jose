#!/usr/bin/env python3

import discord
import asyncio
import sys

sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import josecommon as jcommon

class JoseLanguage(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.LANGLIST = [
            'pt', 'en'
        ]

    async def savedb(self):
        await jcommon.save_langdb()

    async def ext_load(self):
        status = await jcommon.load_langdb()
        return status

    async def ext_unload(self):
        status = await jcommon.save_langdb()
        return status

    async def c_reloadlangdb(self, message, args, cxt):
        await self.savedb()
        await jcommon.load_langdb()
        await cxt.say(":speech_left: langdb reloaded")

    async def c_language(self, message, args, cxt):
        '''`!language lang` - sets language for a server'''
        if message.server is None:
            await cxt.say("Language support is not available for DMs")

        if len(args) < 2:
            await cxt.say(self.c_language.__doc__)
            return

        language = args[1]

        if language not in self.LANGLIST:
            await cxt.say("%s: Language not found" % language)
            return

        await jcommon.langdb_set(message.server.id, language)
        await cxt.say(":speech_left: Set language to %s" % language)
        await self.savedb()


    async def c_listlang(self, message, args, cxt):
        '''`!listlang` - lists all available languages'''
        await cxt.say(self.codeblock("", " ".join(self.LANGLIST)))
