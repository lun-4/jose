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

import itertools
import collections
import re
import io
import aiohttp

MEMES_TECH_HELP = '''
Então você teve problemas usando `!m stat` ou `!m get` ou alguma merda assim?
Siga esses passos:
    1) Rode um `!m check` no josé
        O `!m check` irá checar meme por meme e ver se ele faz sentido, tipo ter um
        número de usos, se não, ele irá corrigir automaticamente

        Outra coisa que o `!m check` faz é procurar por duplicatas, ou seja, 2 memes que
        vão pro mesmo resultado, ele te mostra quem tem duplicata e você remove manualmente
    2) Se o problema persiste, fale com lunão.
'''

class JoseMemes(jcommon.Extension):
    def __init__(self, cl):
        self.memes = {}
        self.WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
        self.WIDE_MAP[0x20] = 0x3000
        self.patterns = ['fbcdn.net', 'akamaihd.net']
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

    async def c_htmpr(self, message, args):
        await self.say(MEMES_TECH_HELP)

    async def c_meme(self, message, args):
        '''
        !meme: Adicione e mostre memes com o josé!
        **RECOMENDADO**: use `!htmpr` para descobrir problemas técnicos.
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
        `!meme page <página>` - mostra a página tal de todos os memes disponíveis(inicia de 1, não do 0)
        `!meme see @user` - mostra todos os memes que a @pessoa fez
        `!meme check` - checa o banco de dados de memes

        Tenha cuidado ao adicionar coisas NSFW.
        '''

        if len(args) < 2:
            await self.say(self.c_meme.__doc__)
            return

        command = args[1]
        if command == 'add':
            args_s = ' '.join(args[2:])
            args_sp = args_s.split(';')
            meme = args_sp[0]
            url = args_sp[1]

            if len(meme) > 96:
                await self.say("*não tem meme grátis*")
                return

            if meme in self.memes:
                await self.say("%s: meme já existe" % meme)
                return

            for pat in self.patterns:
                if re.search(pat, url):
                    await self.say("Detectado um link do facebook, tratando...")

                    with aiohttp.ClientSession() as session:
                        data = io.BytesIO()

                        async with session.get(url) as resp:
                            data_read = await resp.read()
                            data.write(data_read)

                        clone = io.BytesIO(data.getvalue())
                        msg = await self.client.send_file(message.channel, clone, filename='%s.jpg' % meme, content='*tratado*')
                        data.close()
                        clone.close()

                        url = msg.attachments[0]['url']
                        break

            self.memes[meme] = {
                'owner': message.author.id,
                'data': url,
                'uses': 0,
            }
            await self.save_memes()
            await self.say("%s: meme adicionado!" % meme)
            return
        elif command == 'rm':
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
        elif command == 'save':
            done = await self.save_memes()
            if done:
                await self.say("jmemes: banco de dados salvo")
            else:
                raise IOError("banco de dados não salvo corretamente")

            return
        elif command == 'load':
            done = await self.load_memes()
            if done:
                await self.say("jmemes: banco de dados carregado")
            else:
                raise IOError("banco de dados não carregado corretamente")

            return

        elif command == 'saveload':
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
        #elif command == 'list':
        #    await self.say("memes: %s" % ', '.join(self.memes.keys()))
        elif command == 'get':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                self.memes[meme]['uses'] += 1
                await self.say(self.memes[meme]['data'])
                await self.save_memes()
            else:
                await self.say("%s: meme não encontrado" % meme)
            return
        elif command == 'cnv': # debug purposes
            for key in self.memes:
                meme = self.memes[key]
                url = meme['data']
                for pat in self.patterns:
                    if re.search(pat, url[:40]):
                        await self.say("Detectado um link do facebook, tratando...")

                        with aiohttp.ClientSession() as session:
                            data = io.BytesIO()

                            async with session.get(url) as resp:
                                data_read = await resp.read()
                                data.write(data_read)

                            clone = io.BytesIO(data.getvalue())
                            msg = await self.client.send_file(message.channel, clone, filename='%s.jpg' % key, content='*tratado*')
                            data.close()
                            clone.close()

                            url = msg.attachments[0]['url']
                            await asyncio.sleep(0.3)
                        meme['data'] = url
            await self.save_memes()
            await self.say("done.")
        elif command == 'search':
            term = ' '.join(args[2:])
            term = term.lower()
            if term.strip() == '':
                await self.say("Pesquisas vazias não são permitidas")
                return

            probables = [key for key in self.memes if term in key.lower()]
            if len(probables) > 0:
                await self.say("Resultados: %s" % ', '.join(probables))
            else:
                await self.say("%r: Nenhum resultado encontrado" % term)
        elif command == 'rename':
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
            await self.say("`%s` foi renomeado para `%s`!" % (oldname, newname))
            await self.save_memes()
            return

        elif command == 'owner':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                u = discord.utils.get(message.server.members, id=self.memes[meme]['owner'])
                await self.say("%s foi criado por %s" % (meme, u))
            else:
                await self.say("%s: meme não encontrado" % meme)
            return

        elif command == 'count':
            await self.say("quantidade de memes: %s" % len(self.memes))

        elif command == 'stat':
            stat = ''

            copy = dict(self.memes)

            inconsistency = False
            i = 1
            for k in copy:
                if 'uses' not in copy[k]:
                    await self.say('INCONSISTENCY: %s' % k)
                    inconsistency = True

            if inconsistency:
                await self.say("INCONSISTENCY entries detected.")
                return

            for key in sorted(copy, key=lambda key: -copy[key]['uses']):
                if i > 10: break
                stat += '%d lugar: %s com %d usos\n' % (i, \
                    key, copy[key]['uses'])
                i += 1
            await self.say(self.codeblock('', stat))

        elif command == 'istat':
            meme = ' '.join(args[2:])
            if meme in self.memes:
                await self.say(self.codeblock('', 'usos: %d' % self.memes[meme]['uses']))
            else:
                await self.say("%s: meme não encontrado" % meme)
            return

        elif command == 'page':
            if len(args) < 3:
                await self.say("SyntaxError: `!m page <page>`")
                return
            page = args[2]

            try:
                page = int(page)
            except Exception as e:
                await self.say("jmemes: %r" % e)

            if page < 0:
                await self.say("EI EI EI EI CALMAI CUZAO")
                return

            PER_PAGE = 50
            min_it = PER_PAGE * (page - 1)
            max_it = PER_PAGE * page

            x = sorted(self.memes.keys())
            x_slice = x[min_it:max_it]

            if len(x_slice) < 1:
                await self.say("*nao tem meme gratis*")
                return

            report = ', '.join(x_slice)
            await self.say(report)

        elif command == 'check':
            await self.say("checking INCONSISTENCY data")
            for key in self.memes:
                meme = self.memes[key]
                if 'uses' not in meme:
                    await self.say("INCONSISTENCY(uses): %s" % key)
                    self.memes[key].update({"uses": 0})

            await self.say("checking duplicates(by value)")
            new_memes = {}
            for k in self.memes:
                v = self.memes[k]
                if v['data'] not in new_memes:
                    new_memes[v['data']] = []
                new_memes[v['data']].append(k)

            for v in new_memes:
                if len(new_memes[v]) > 1:
                    await self.say("DUPLICATE(s): ```%s```\n" % (new_memes[v]))

            await self.say("done.")
            return

        elif command == 'see':
            owner = args[2]

            owner_id = await jcommon.parse_id(owner, message)

            from_owner = [x for x in self.memes if self.memes[x]['owner'] == owner_id]
            if len(from_owner) < 1:
                await self.say("*nao tem owner gratis*")
                return

            report = '''Quantidade: %d,\nMemes: %s''' % (len(from_owner), ', '.join(from_owner))
            await self.say(report)

        else:
            await self.say("comando inválido: %s" % command)

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
        '''`!emoji [qt]` - gera de 1 a 5(ou `qt`(máx. 512)) emojis aleatórios'''
        res = ''
        if len(args) < 2:
            res = await jcommon.random_emoji(random.randint(1,5))
        else:
            a = int(args[1])
            if a < 1:
                await self.say("*Emojis inexistentes*")
                return
            if a >= 512:
                await self.say("*Não tem emoji grátis*")
                return
            res = await jcommon.random_emoji(int(args[1]))
        await self.say(res)
