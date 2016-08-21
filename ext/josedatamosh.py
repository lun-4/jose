#!/usr/bin/env python3

import discord
import asyncio
import sys

sys.path.append("..")
import josecommon as jcommon
import joseerror as je

class JoseDatamosh(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)

    async def ext_load(self):
        return

    async def ext_unload(self):
        return

    async def c_datamosh(self, message, args):
        '''
        `!datamosh <url>` - *Datamoshing.* (somente JPG por um momento)
        '''
        return
