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
        jcommon.langdb = {}
        self.db_languages_path = jcommon.LANGUAGES_PATH

    async def savedb(self):
        self.logger.info("Saving language database")
        await jcommon.save_langdb()

    async def ext_load(self):
        try:
            await jcommon.load_langdb()

            return True, ''
        except Exception as e:
            return False, str(e)

    async def ext_unload(self):
        try:
            await self.savedb()
            return True, ''
        except Exception as e:
            return False, str(e)

    async def c_language(self, message, args, cxt):
        '''`!language lang` - sets language for a server'''
        if message.server is None:
            await cxt.say("Language support is not available for DMs")
            #await cxt.sayt("jlang_no_lang")

        if len(args) < 2:
            await cxt.say(self.c_language.__doc__)
            return

        language = args[1]

        if language not in self.LANGLIST:
            await cxt.say("%s: Language not found")
            #await cxt.sayt("jlang_lang_404", language=language)
            return

        await jcommon.langdb_set(message.server.id, language)
        await cxt.say("Set language to %s" % language)
        #await cxt.sayt("jlang_set_lang", language=language)
        await self.savedb()


    async def c_listlang(self, message, args, cxt):
        '''`!listlang` - lists all available languages'''
        await cxt.say(self.codeblock("", " ".join(self.LANGLIST)))
