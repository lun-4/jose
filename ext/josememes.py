#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon

class JoseMemes(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)

    @asyncio.coroutine
    def c_aprovado(self, message, args):
        yield from self.say('http://gaveta.com.br/images/Aprovacao-Sean-Anthony.png')
