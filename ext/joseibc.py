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

    async def c_callpage(self, message, args):
        '''!callpage <num> - mostra a página da lista de syscalls'''
        return

    async def c_syscall(self, message, args):
        '''`!syscall <JSON>` - https://github.com/lkmnds/jose/blob/master/doc/ibc.md'''
        json_to_parse = ' '.join(args[1:])
        try:
            json_data = json.loads(json_to_parse)
        except Exception as e:
            await self.say("syscall->pyerr: `%r`" % e)
            return

        try:
            syscall_number = json_data['callnumber']
        except Exception as e:
            await self.say("syscall->pyerr: `%r`" % e)
            return

        if syscall_number == 0:
            await self.say("pong")

        return
