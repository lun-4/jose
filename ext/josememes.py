#!/usr/bin/env python3

import asyncio
import sys
from random import SystemRandom
random = SystemRandom()
import pickle

import discord

sys.path.append("..")
import josecommon as jcommon
import joseerror as je

MEME_HELP_TEXT = '''!meme: Adicione e mostre memes com o josé!
*alias*: !m

Subcomandos:
`!meme add <trigger>;<meme>` - toda vez que alguém mandar um `!meme get <trigger>`, josé falará `<meme>`
`!meme get <trigger>` - josé falará o que estiver programado para falar de acordo com `<trigger>`
`!meme list` - mostra todos os memes que estão escritos no josé
`!meme search <termo>` - procura o banco de dados de memes por um meme específico
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

    async def ext_unload(self):
        # supress every kind of debug to self.say
        old_cur = self.current
        self.current = None
        await self.save_memes()
        self.currrent = old_cur

    async def load_memes(self):
        try:
            self.memes = pickle.load(open('ext/josememes.db', 'rb'))
            return True
        except Exception as e:
            if self.current is not None:
                await self.debug("load_memes: erro carregando josememes.db(%s)" % e)
                return False
            else:
                print('load_memes: erro: %s' % e)
                return False
            self.memes = {}

    async def save_memes(self):
        try:
            pickle.dump(self.memes, open("ext/josememes.db", 'wb'))
            return True
        except Exception as e:
            if self.current is not None:
                await self.debug("save_memes: pyerr: %s" % e)
            else:
                print(traceback.print_exc())
            return False

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
                self.memes[meme] = {
                    'owner': message.author.id,
                    'data': url,
                }
                await self.save_memes()
                await self.say("%s: meme adicionado!" % meme)
            return
        elif args[1] == 'rm':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                meme_data = self.memes[meme]
                is_admin = await self.brolecheck(jcommon.MASTER_ROLE)

                if (message.author.id == meme_data['owner']) or is_admin:
                    del self.memes[meme]
                    await self.say("%s: meme removido" % meme)
                    return
                else:
                    raise je.PermissionError()

                return
            else:
                await self.say("%s: meme não encontrado" % meme)
                return
        elif args[1] == 'save':
            done = await self.save_memes()
            if done:
                await self.say("jmemes: banco de dados salvo")
            else:
                raise IOError("banco de dados não salvo corretamente")

            return
        elif args[1] == 'load':
            done = await self.load_memes()
            if done:
                await self.say("jmemes: banco de dados carregado")
            else:
                raise IOError("banco de dados não carregado corretamente")

            return

        elif args[1] == 'saveload':
            done = await self.save_memes()
            if done:
                await self.say("jmemes: banco de dados salvo")
            else:
                raise IOError("banco de dados não salvo corretamente")

            done = await self.load_memes()
            if done:
                await self.say("jmemes: banco de dados carregado")
            else:
                raise IOError("banco de dados não carregado corretamente")

            return
        elif args[1] == 'list':
            await self.say("memes: %s" % ', '.join(self.memes.keys()))
        elif args[1] == 'get':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                await self.say(self.memes[meme]['data'])
            else:
                await self.say("%s: meme não encontrado" % meme)
            return
        elif args[1] == 'all':
            await self.say(self.codeblock('python', self.memes))
        elif args[1] == 'search':
            term = ' '.join(args[2:])
            probables = [key for key in self.memes if term in key]
            if len(probables) > 0:
                await self.say("Resultados: %s" % ', '.join(probables))
            else:
                await self.say("%r: Nenhum resultado encontrado" % term)
        else:
            await self.say("comando inválido: %s" % args[1])
            return

    async def c_m(self, message, args):
        await self.c_meme(message, args)

    async def c_fullwidth(self, message, args):
        # looks like discord made fullwidth suppoert available again :D
        text = ' '.join(args[1:])
        await self.say(text.translate(self.WIDE_MAP))

    async def c_fw(self, message, args):
        await self.c_fullwidth(message, args)

    async def c_emoji(self, message, args):
        res = await jcommon.random_emoji(random.randint(1,5))
        await jose.say(res)
