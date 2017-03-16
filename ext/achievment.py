#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

class JoseAchievment(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)

    async def ext_load(self):
        try:
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def ext_unload(self):
        try:
            return True, ''
        except Exception as err:
            return False, repr(err)

    async def c_command(self, message, args, cxt):
        pass
