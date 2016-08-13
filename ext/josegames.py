#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

class Deusmon:
    def __init__(self, did):
        self.id = did
        self.name = dgo_names[did]

class JoseGames(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.db = {}

    async def ext_load(self):
        try:
            self.db = pickle.load(open('d-go.db', 'rb'))
            return True
        except Exception as e:
            return False, repr(e)

    async def ext_unload(self):
        try:
            pickle.dump(self.db, open('d-go.db', 'wb'))
            return True
        except Exception as e:
            return False, repr(e)

    async def c_dgoinit(self, message, args):
        '''`!dgoinit` - inicia uma conta no Deusesmon GO'''
        self.db[message.author.id] = {
            'coin': 0,
            'xp': 0,
            'level': 1,
            'inv': {},
            'dinv': {},
        }
        await self.say("conta criada para <@%s>!" % message.author.id)

    async def c_dgosave(self, message, args):
        done = await self.ext_unload()
        if done:
            await self.say("salvo.")
        elif not done[0]:
            await self.say("py_err: %s" % done[1])
        return

    async def c_dgoload(self, message, args):
        done = await self.ext_load()
        if done:
            await self.say("carregado.")
        elif not done[0]:
            await self.say("py_err: %s" % done[1])
        return

    async def c_dgostat(self, message, args):
        '''`!dgostat` - mostra os status do seu personagem'''
        pass
