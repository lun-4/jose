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
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.langlist = (
            'pt', 'en'
        )

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
        if message.server is None:
            await cxt.say("Why are you here?")
            return

        sid = message.server.id

        botblock = await jcommon.configdb_get(sid, 'botblock')
        if botblock is None:
            self.logger.warning("Botblock is None")

        done = await jcommon.configdb_set(sid, 'botblock', not botblock)
        if not done:
            await cxt.say("Error when changing `botblock` for this server.")
            return

        # sanity check
        n_botblock = await jcommon.configdb_get(sid, 'botblock')
        if n_botblock is None:
            self.logger.warning("Botblock is None... again")

        if n_botblock == (not botblock):
            await cxt.say("Botblock from %s to %s", (botblock, not botblock))
        else:
            await cxt.say("No changes to botblock")

    async def c_jsprob(self, message, args, cxt):
        '''`j!jsprob prob` - Set JoseSpeak probability of responding to random messages, default 0, maximum 3'''

        if len(args) < 2:
            await cxt.say(self.c_setprob.__doc__)
            return

        try:
            prob = decimal.Decimal(args[1])
        except:
            await cxt.say("Error parsing `prob`")
            return

        if prob < 0:
            await cxt.say("`prob` can't be less than 0%")

        if prob > 3:
            await cxt.say("`prob` can't be higher than 3%")

        done = await jcommon.configdb_set(sid, 'speak_prob', prob / 100)
        if not done:
            await cxt.say("Error changing `prob`.")
        else:
            await cxt.say("`josespeak` probability is now %.2f%%", (prob,))

    async def c_language(self, message, args, cxt):
        '''`j!language lang` - sets language for a server(use `!listlang` for available languages)'''
        if message.server is None:
            await cxt.say("Language support is not available for DMs")
            return

        if len(args) < 2:
            await cxt.say(self.c_language.__doc__)
            return

        language = args[1]

        if language not in self.langlist:
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

        llist = self.codeblock("", " ".join(self.langlist))
        serverlang = await jcommon.langdb_get(message.server.id)
        await cxt.say("This server's language: `%s`\nAvailable languages: %s", \
            (serverlang, llist))
