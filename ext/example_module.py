#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

class JoseExtension(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)

    async def ext_load(self):
        pass

    async def c_command(self, message, args):
        pass
