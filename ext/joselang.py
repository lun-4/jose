#!/usr/bin/env python3

import sys

sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon

CONFIG_HELP = """
José Configuration:
 * `botblock`, if True, blocks all bot messages, use `j!botblock`
 * `language`, string representing the server's language, use `j!language`
"""

class JoseLanguage(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)
        self.LANGLIST = [
            'pt', 'en'
        ]

    async def savedb(self):
        await jcommon.save_configdb()

    async def ext_load(self):
        await self.dbapi.initializedb()
        status = await jcommon.load_configdb()
        return status

    async def ext_unload(self):
        status = await jcommon.save_configdb()
        return status

    async def c_reloadcdb(self, message, args, cxt):
        await self.savedb()
        await jcommon.load_configdb()
        await cxt.say(":speech_left: configdb reloaded")

    async def c_confighelp(self, message, args, cxt):
        await cxt.say(CONFIG_HELP)

    async def c_botblock(self, message, args, cxt):
        '''`j!botblock` - toggles bot block'''
        cur = jcommon.configdb_get(message.server.id, 'botblock', False)
        await jcommon.configdb_set(message.server.id, 'botblock', not cur)
        await cxt.say("Botblock defined to %s", (not cur,))

    async def c_language(self, message, args, cxt):
        '''`j!language lang` - sets language for a server(use `!listlang` for available languages)'''
        if message.server is None:
            await cxt.say("Language support is not available for DMs")
            return

        if len(args) < 2:
            await cxt.say(self.c_language.__doc__)
            return

        language = args[1]

        if language not in self.LANGLIST:
            await cxt.say("%s: Language not found", (language,))
            return

        await jcommon.langdb_set(message.server.id, language)
        await cxt.say(":speech_left: Set language to %s", (language,))
        await self.savedb()


    async def c_listlang(self, message, args, cxt):
        '''`j!listlang` - lists all available languages'''
        if message.server is None:
            await cxt.say("Language support is not available for DMs")
            return

        llist = self.codeblock("", " ".join(self.LANGLIST))
        serverlang = await jcommon.langdb_get(message.server.id)
        await cxt.say("This server's language: `%s`\nAvailable languages: %s", \
            (serverlang, llist))
