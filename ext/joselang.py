#!/usr/bin/env python3

import discord
import asyncio
import sys
import json
import os

sys.path.append("..")
import jauxiliar as jaux
import joseerror as je
import josecommon as jcommon

class JoseLanguage(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.langdb = {}
        self.LANGLIST = [
            'pt', 'en'
        ]
        self.db_languages_path = jcommon.LANGUAGES_PATH
        jcommon.dblang_ref = self.langdb

    async def savedb(self):
        self.logger.info("Saving language database")
        json.dump(self.landgb, open(self.db_languages_path, 'w'))

    async def ext_load(self):
        try:
            self.langdb = {}
            if not os.path.isfile(self.db_languages_path):
                # recreate
                with open(self.db_languages_path, 'w') as f:
                    f.write('{}')

            self.langdb = json.load(open(self.db_languages_path, 'r'))

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

        self.landgb[message.server.id] = language
        await cxt.say("Set language to %s" % language)
        #await cxt.sayt("jlang_set_lang", language=language)
        await self.savedb()


    async def c_listlang(self, message, args, cxt):
        '''`!listlang` - lists all available languages'''
        await cxt.say(self.codeblock("", " ".join(self.LANGLIST)))
