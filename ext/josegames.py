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

class JoseExtension(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.db = {}

    async def ext_load(self):
        self.db = pickle.load(open('d-go.db', 'rb'))

    async def ext_unload(self):
        pickle.dump(self.db, open('d-go.db', 'wb'))

    async def c_dgoinit(self, message, args):
        '''`!dgoinit` - inicia uma conta no Deusesmon GO'''
        self.db[message.author.id] = {
            'coin': 0,
            'xp': 0,
            'level': 1,
            'inv': {},
            'dinv': {},
        }
        await self.say("<@%s> conta criada!" % message.author.id)

    async def c_dgostat(self, message, args):
        '''`!dgostat` - mostra os status do seu personagem'''
        pass
