#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

class JoseExtension(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        pass

    async def ext_unload(self):
        pass

    async def c_command(self, message, args):
        pass
