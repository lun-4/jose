#!/usr/bin/env python3

import sys
import time
sys.path.append("..")
import jauxiliar as jaux
import josecommon as jcommon

CONFIG_HELP = """
José Configuration:
 * `botblock`, if True, blocks all bot messages, use `j!botblock`
 * `language`, string representing the server's language, use `j!language`
 * `j!jsprob`, sets probability for JoséSpeak
 * `j!fwprob`, sets JoséSpeak's probability of sending fullwidth text
 * `j!schannel`, setup JoséSpeak's speak channel, the channel where josé will get all his messages from
"""

class JoseLanguage(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.langlist = (
            'pt', 'en'
        )

        self.cbk_new('jlang.dbapi_commit', self.dbapi_commit, 300)

    async def dbapi_commit(self):
        t_start = time.time()
        if self.dbapi.statements > 0:
            self.dbapi.commit()
            t_end = time.time()

            delta = (t_end - t_start) * 1000
            self.logger.info("[dbapi:commit] Took %.2fms", delta)

    async def savedb(self):
        await jcommon.save_configdb()

    async def ext_load(self):
        await self.dbapi.initializedb()
        status = await jcommon.load_configdb()
        return status

    async def ext_unload(self):
        # save all databases
        self.dbapi.commit()
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
            self.logger.warning("`botblock` is None... again")

        if n_botblock == (not botblock):
            await cxt.say("`botblock` set from %s to %s", (botblock, not botblock))
        else:
            await cxt.say("No changes to `botblock`")

    async def c_jsprob(self, message, args, cxt):
        '''`j!jsprob prob` - Set JoseSpeak probability of responding to random messages, default 0, maximum 3'''

        if len(args) < 2:
            await cxt.say(self.c_jsprob.__doc__)
            return

        try:
            prob = float(args[1])
        except:
            await cxt.say("Error parsing `prob`")
            return

        if prob < 0 or prob > 5:
            await cxt.say("`prob` is out of the range `[0-5]`")
            return

        done = await jcommon.configdb_set(message.server.id, 'speak_prob', prob / 100)
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

    async def c_fwprob(self, message, args, cxt):
        '''`j!fwprob fw_prob` - Set JoseSpeak probability of saying fullwidth text, default 1%, maximum 10%'''

        if len(args) < 2:
            await cxt.say(self.c_fwprob.__doc__)
            return

        try:
            fw_prob = float(args[1])
        except:
            await cxt.say("Error parsing `fw_prob`")
            return

        if fw_prob < 0 or fw_prob > 10:
            await cxt.say("`fw_prob` is out of the range `[0%-10%]`")
            return

        done = await jcommon.configdb_set(message.server.id, 'fw_prob', fw_prob / 100)
        if not done:
            await cxt.say("Error changing `fw_prob`.")
        else:
            await cxt.say("`josespeak.fw` probability is now %.2f%%", (fw_prob,))

    async def c_schannel(self, message, args, cxt):
        '''`j!schannel #channel` - sets the channel for `josespeak` to gather source text'''

        try:
            channel_id = self.parse_channel(args[1])
        except:
            await cxt.say("Error parsing `channel`")
            return

        channel = message.server.get_channel(channel_id)
        if channel is None:
            await cxt.say("Channel not found")
            return

        self.logger.info("Set speak_channel to %r", channel_id)
        done = await jcommon.configdb_set(message.server.id, 'speak_channel', channel_id)
        if done:
            await cxt.say("channel to gather messages is now <#%s>", (channel_id,))
        else:
            await cxt.say("Error changing `speak_channel`.")

    async def c_imgchannel(self, message, args, cxt):
        '''`j!imgchannel #channel` - sets the channel for `joseimages` to work on'''

        try:
            channel_id = self.parse_channel(args[1])
        except:
            await cxt.say("Error parsing `channel`")
            return

        channel = message.server.get_channel(channel_id)
        if channel is None:
            await cxt.say("Channel not found")
            return

        self.logger.info("Set imgchannel in %r to %r", message.server.name, channel_id)
        done = await jcommon.configdb_set(message.server.id, 'imgchannel', channel_id)
        if done:
            await cxt.say("image channel is now <#%s>", (channel_id,))
        else:
            await cxt.say("Error changing `imgchannel`.")
