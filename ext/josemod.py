#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

class JoseMod(jaux.Auxiliar):
    def __init__(self, cl):
        '''josemod - Moderator Extension'''
        jaux.Auxiliar.__init__(self, cl)
        # TODO: Implement database
        self.moddb = {}

        # TODO: commands for josemod

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_initmod(self, message, args, cxt):
        '''`j!initmod modchannel logchannel` - Initialize Moderator extension in this server'''
        await self.is_admin(message.author.id)

        if len(args) < 3:
            await cxt.say(self.c_initmod.__doc__)
            return

        if server_id in self.moddb:
            await cxt.say("Moderator is already on in this server")
            return

        server_id = message.server.id

        try:
            mod_channel_id = args[1]
            log_channel_id = args[2]
        except:
            await cxt.say("???")
            return

        self.moddb[server_id] = {
            'mod_channel': mod_channel_id,
            'log_channel': log_channel_id,
            'bans': {},
            'kicks': {},
        }

        return

    async def c_kick(self, message, args, cxt):
        '''`j!kick userid|@mention` - kicks a user'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_kick.__doc__)

        # make its ID for reason, etc

        return

    async def c_reason(self, message, args, cxt):
        '''`j!reason id reason` - Sets a reason for a kick/ban/etc'''
        await self.is_admin(message.author.id)

        if len(args) < 2:
            await cxt.say(self.c_reason.__doc__)

        return
