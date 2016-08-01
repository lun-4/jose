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

Existem 2 modos de usar o !meme, mostrar um meme e adicionar um meme:
`!meme add <trigger> <meme>` - toda vez que alguém mandar um `!meme <trigger>`, josé falará `<meme>`
`!meme <trigger>` - josé falará o que estiver programado para falar de acordo com `<trigger>`

Memes não podem ser removidos(*ainda*), então tenha cuidado ao adicionar qualquer coisa NSFW.
'''

class JoseMemes(jcommon.Extension):
    def __init__(self, cl):
        self.memes = {}
        jcommon.Extension.__init__(self, cl)

    @asyncio.coroutine
    def ext_load(self):
        yield from self.load_memes()

    @asyncio.coroutine
    def load_memes(self):
        try:
            self.memes = pickle.load(open('ext/josememes.db', 'rb'))
        except Exception as e:
            if self.current is not None:
                yield from self.debug("load_memes: erro carregando josememes.db(%s)" % e)
            else:
                print('load_memes: erro: %s' % e)
            self.memes = {}

    @asyncio.coroutine
    def save_memes(self):
        try:
            pickle.dump(self.memes, open("ext/josememes.db", 'wb'))
        except Exception as e:
            yield from self.debug("save_memes: pyerr: %s" % e)

    @asyncio.coroutine
    def c_aprovado(self, message, args):
        yield from self.say('http://gaveta.com.br/images/Aprovacao-Sean-Anthony.png')

    @asyncio.coroutine
    def c_meme(self, message, args):
        if len(args) < 2:
            yield from self.say(MEME_HELP_TEXT)
            return
        elif args[1] == 'add':
            meme = args[2]
            url = args[3]

            if meme in self.memes:
                yield from self.say("%s: meme já existe" % meme)
                return
            else:
                self.memes[meme] = url
                yield from self.save_memes()
                yield from self.say("%s: meme adicionado!" % meme)
            return
        elif args[1] == 'save':
            yield from self.save_memes()
            return
        elif args[1] == 'load':
            yield from self.load_memes()
            return
        else:
            meme = args[1]
            if meme in self.memes:
                yield from self.say(self.memes[meme])
            else:
                yield from self.say("%s: meme não encontrado" % meme)
            return

    @asyncio.coroutine
    def c_m(self, message, args):
        yield from self.c_meme(message, args)
