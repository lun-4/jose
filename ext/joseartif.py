#!/usr/bin/env python3

import discord
import asyncio
import sys

sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

class JoseArtif(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def e_on_message(self, message):
        print("joseartif: recv on_message")

    async def c_command(self, message, args):
        pass
