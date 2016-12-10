#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

import json

async def syscall_pong(ibc, args):
    await ibc.say("pong")

async def syscall_say(ibc, args):
    await ibc.say(' '.join(args))

syscall_functions = {
    0: syscall_pong,
    1: syscall_say,
}

class JoseIBC(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_callpage(self, message, args):
        '''!callpage <num> - mostra a página da lista de syscalls'''
        return

    async def c_syscall(self, message, args):
        '''`!syscall <JSON>` - https://github.com/lkmnds/jose/blob/master/doc/ibc.md'''
        json_to_parse = ' '.join(args[1:])
        try:
            json_data = json.loads(json_to_parse)
        except Exception as e:
            await self.say("syscall->json.loads: `%r`" % e)
            return

        try:
            syscall_number = json_data['callnumber']
        except Exception as e:
            await self.say("syscall->json_data.callnumber: `%r`" % e)
            return

        await syscall_functions[syscall_number](self, json_data['arguments'])
        return
