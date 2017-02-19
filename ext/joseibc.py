#!/usr/bin/env python3

import sys
sys.path.append("..")
import jauxiliar as jaux

import json

ibc_global_dict = {}
IBC_MAX_DICTSIZE = 10

async def syscall_pong(ibc, args, cxt):
    await cxt.say("pong")

async def syscall_say(ibc, args, cxt):
    await cxt.say(' '.join(args))

async def syscall_dict_set(ibc, args, cxt):
    key = args[0]
    val = args[1]
    if len(ibc_global_dict) > IBC_MAX_DICTSIZE:
        await cxt.say("E_MAX_MEM")
        return -1
    ibc_global_dict[key] = val
    await cxt.say("OK")

async def syscall_dict_get(ibc, args, cxt):
    key = args[0]
    if key in ibc_global_dict:
        await cxt.say(ibc_global_dict[key])
    else:
        await cxt.say("E_NO_KEY")

syscall_functions = {
    0: syscall_pong,
    1: syscall_say,
    2: syscall_dict_set,
    3: syscall_dict_get,
}

class JoseIBC(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_callpage(self, message, args, cxt):
        '''!callpage <num> - mostra a página da lista de syscalls'''
        return

    async def c_syscall(self, message, args, cxt):
        '''`!syscall <JSON>` - https://github.com/lkmnds/jose/blob/master/doc/ibc.md'''
        json_to_parse = ' '.join(args[1:])
        try:
            json_data = json.loads(json_to_parse)
        except Exception as e:
            await cxt.say("syscall->json.loads: `%r`", (e,))
            return

        try:
            syscall_number = json_data['callnumber']
        except Exception as e:
            await cxt.say("syscall->json_data.callnumber: `%r`", (e,))
            return

        await syscall_functions[syscall_number](self, json_data['arguments'], cxt)
        return
