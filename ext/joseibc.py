#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

import json

class JoseIBC(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        pass

    async def ext_unload(self):
        pass

    async def c_syscall(self, message, args):
        '''`!syscall <JSON>` - https://github.com/lkmnds/jose/blob/master/doc/ibc.md'''
        try:
            json_data = json.loads(args[1])
        except Exception as e:
            await self.say("syscall->pyerr: `%r`" % e)
            return
        return
