#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon

import pickle
import io

MEME_HELP_TEXT = '''!meme: Adicione e mostre memes com o josé!
*alias*: !m

Subcomandos:
`!meme add <trigger>;<meme>` - toda vez que alguém mandar um `!meme get <trigger>`, josé falará `<meme>`
`!meme get <trigger>` - josé falará o que estiver programado para falar de acordo com `<trigger>`
`!meme list` - mostra todos os memes que estão escritos no josé
`!meme rm <meme>` - remove um meme

Tenha cuidado ao adicionar coisas NSFW.
'''

class JoseMemes(jcommon.Extension):
    def __init__(self, cl):
        self.memes = {}
        self.WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
        self.WIDE_MAP[0x20] = 0x3000
        jcommon.Extension.__init__(self, cl)

    async def ext_load(self):
        await self.load_memes()

    async def load_memes(self):
        try:
            self.memes = pickle.load(open('ext/josememes.db', 'rb'))
        except Exception as e:
            if self.current is not None:
                await self.debug("load_memes: erro carregando josememes.db(%s)" % e)
            else:
                print('load_memes: erro: %s' % e)
            self.memes = {}

    async def save_memes(self):
        try:
            pickle.dump(self.memes, open("ext/josememes.db", 'wb'))
        except Exception as e:
            await self.debug("save_memes: pyerr: %s" % e)

    async def c_aprovado(self, message, args):
        await self.say('http://gaveta.com.br/images/Aprovacao-Sean-Anthony.png')

    async def c_meme(self, message, args):
        if len(args) < 2:
            await self.say(MEME_HELP_TEXT)
            return
        elif args[1] == 'add':
            args_s = ' '.join(args[2:])
            args_sp = args_s.split(';')
            meme = args_sp[0]
            url = args_sp[1]

            if meme in self.memes:
                await self.say("%s: meme já existe" % meme)
                return
            else:
                self.memes[meme] = url
                await self.save_memes()
                await self.say("%s: meme adicionado!" % meme)
            return
        elif args[1] == 'rm':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                del self.memes[meme]
                await self.say("%s: meme removido" % meme)
                return
            else:
                await self.say("%s: meme não encontrado" % meme)
                return
        elif args[1] == 'save':
            await self.save_memes()
            return
        elif args[1] == 'load':
            await self.load_memes()
            return
        elif args[1] == 'list':
            await self.say("memes: %s" % ', '.join(self.memes.keys()))
        elif args[1] == 'get':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                await self.say(self.memes[meme])
            else:
                await self.say("%s: meme não encontrado" % meme)
            return
        else:
            await self.say("comando inválido: %s" % args[1])
            return

    async def c_m(self, message, args):
        await self.c_meme(message, args)

    async def c_fullwidth(self, message, args):
        # discord by some stuff removed fullwidth char support
        # dayum.
        text = ' '.join(args[1:])
        await self.say(text.translate(self.WIDE_MAP))

    async def c_fw(self, message, args):
        await self.c_fullwidth(message, args)
