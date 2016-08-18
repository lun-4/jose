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
        '''`!aprovado` - O Melhor Sean Anthony®'''
        await self.say('http://gaveta.com.br/images/Aprovacao-Sean-Anthony.png')

    async def c_meme(self, message, args):
        '''!meme: Adicione e mostre memes com o josé!
        *alias*: !m

        Subcomandos:
        `!meme add <trigger>;<meme>` - toda vez que alguém mandar um `!meme get <trigger>`, josé falará `<meme>`
        `!meme get <trigger>` - josé falará o que estiver programado para falar de acordo com `<trigger>`
        `!meme search <termo>` - procura o banco de dados de memes por um meme específico
        `!meme rm <meme>` - remove um meme
        `!meme rename <nome antigo>;<nome novo>` - altera o `<trigger>` de um meme
        `!meme owner <meme>` - mostra quem "criou" o `<meme>`
        `!meme count` - mostra a quantidade de memes
        `!meme stat` - estatísticas sobre o uso dos memes
        `!meme istat <meme>` - estatísticas sobre o uso de um meme específico

        Tenha cuidado ao adicionar coisas NSFW.
        '''
        if len(args) < 2:
            await self.say(self.c_meme.__doc__)
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
                    'uses': 0,
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
                    await self.save_memes()
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
            print('saveload')
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
        #elif args[1] == 'list':
        #    await self.say("memes: %s" % ', '.join(self.memes.keys()))
        elif args[1] == 'get':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                self.memes[meme]['uses'] += 1
                await self.say(self.memes[meme]['data'])
                await self.save_memes()
            else:
                await self.say("%s: meme não encontrado" % meme)
            return
        elif args[1] == 'all':
            await self.say(self.codeblock('python', self.memes))
        elif args[1] == 'cnv': # debug purposes
            for key in self.memes:
                meme = self.memes[key]
                if 'uses' not in meme:
                    print("uses not in meme")
                    meme['uses'] = 0
            await self.say("done.")
        elif args[1] == 'search':
            term = ' '.join(args[2:])
            probables = [key for key in self.memes if term in key]
            if len(probables) > 0:
                await self.say("Resultados: %s" % ', '.join(probables))
            else:
                await self.say("%r: Nenhum resultado encontrado" % term)
        elif args[1] == 'rename':
            args_s = ' '.join(args[2:])
            args_sp = args_s.split(';')
            oldname = args_sp[0]
            newname = args_sp[1]

            if not oldname in self.memes:
                await self.say("%s: meme não encontrado" % oldname)
                return

            # swapping
            old_meme = self.memes[oldname]

            if old_meme['owner'] != message.author.id:
                raise je.PermissionError()

            self.memes[newname] = {
                'owner': message.author.id,
                'data': old_meme['data'],
            }

            del self.memes[oldname]
            await self.say("%s foi renomeado para %s!" % (oldname, newname))
            await self.save_memes()
            return

        elif args[1] == 'owner':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                u = discord.utils.get(message.server.members, id=self.memes[meme]['owner'])
                await self.say("%s foi criado por %s" % (meme, u))
            else:
                await self.say("%s: meme não encontrado" % meme)
            return

        elif args[1] == 'count':
            await self.say("quantidade de memes: %s" % len(self.memes))

        elif args[1] == 'stat':
            stat = ''

            copy = dict(self.memes)
            i = 1
            for key in sorted(self.memes, key=lambda key: -self.memes[key]['uses']):
                if i > 3: break
                stat += '%d lugar: %s com %d usos\n' % (i, \
                    key, self.memes[key]['uses'])
                i += 1
            await self.say(self.codeblock('', stat))

        elif args[1] == 'istat':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                await self.say(self.codeblock('', 'usos: %d' % self.memes[meme]['uses']))
            else:
                await self.say("%s: meme não encontrado" % meme)
            return

        else:
            await self.say("comando inválido: %s" % args[1])
            return

    async def c_m(self, message, args):
        '''`!m` - alias para `!meme`'''
        await self.c_meme(message, args)

    async def c_fullwidth(self, message, args):
        '''`!fullwidth texto` - converte texto para fullwidth'''
        # looks like discord made fullwidth suppoert available again :D
        text = ' '.join(args[1:])
        await self.say(text.translate(self.WIDE_MAP))

    async def c_fw(self, message, args):
        '''`!fw` - alias para `!fullwidth`'''
        await self.c_fullwidth(message, args)

    async def c_emoji(self, message, args):
        '''`!emoji` - gera de 1 a 5 emojis aleatórios'''
        res = await jcommon.random_emoji(random.randint(1,5))
        await self.say(res)
