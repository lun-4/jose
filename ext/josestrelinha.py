#!/usr/bin/env python3

import discord
import asyncio

import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

import time
import traceback

STARBOARD_HELPTEXT = '''
O Starboard do josé permite aos usuários darem like nas mensagens, sem precisar de Pin ou algo do tipo.
`!like <message ID>` - laik :top:
'''

class JoseStrelinha(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.stars = {}

    async def ext_load(self):
        await self.load_stars()

    async def ext_unload(self):
        # supress every kind of debug to self.say
        old_cur = self.current
        self.current = None
        await self.save_stars()
        self.currrent = old_cur

    async def load_stars(self):
        try:
            self.stars = pickle.load(open('ext/estrelinha.db', 'rb'))
            return True
        except Exception as e:
            if self.current is not None:
                await self.debug("load_stars: erro carregando josememes.db(%s)" % e)
                return False
            else:
                print('load_stars: erro: %s' % e)
                return False
            self.stars = {}

    async def save_stars(self):
        try:
            pickle.dump(self.stars, open("ext/estrelinha.db", 'wb'))
            return True
        except Exception as e:
            if self.current is not None:
                await self.debug("save_stars: pyerr: %s" % e)
            else:
                print(traceback.print_exc())
            return False

    async def c_starinit(self, message, args):
        star_channel = discord.utils.get(message.server.channels, name='estrelinha')
        if star_channel is None:
            await self.say("Criando canal #estrelinha...")
            self.client.create_channel(message.server, "estrelinha")
            await self.say("Administre as permissões.")
        else:
            await self.say("#estrelinha já existe")

    async def c_htstb(self, message, args):
        await self.say(STARBOARD_HELPTEXT)

    async def c_like(self, message, args):
        '''`!like` - O Starboard do josé

        É recomendado que você use `!htstb` para entender o conceito do Starboard

        `!like <id da mensagem>` - manda um like numa mensagem
        `!like quem <id da mensagem>` - fala quem fez tal mensagem
        '''
        star_channel = discord.utils.get(message.server.channels, name='estrelinha')
        if star_channel is None:
            await self.say("#estrelinha não existe")
            return

        command = args[1]
        msg_id = ''
        if command.isdigit():
            msg_id = command
            command = 'like'
        else:
            try:
                msg_id = args[2]
            except:
                await self.say("Erro parseando comando")
                return

        db = self.stars.get(message.server.id, {})
        starrer = message.author

        msg = await self.get_message(ctx.message.channel, msg_id)
        if msg is None:
            await self.bot.say(':question: Mensagem não encontrada')
            return

        starrers = db.get(message, [])
        if starrer.id in starrers:
            await self.say("Você já deu like nesta mensagem")
            return

        if starrer.id == msg.author.id:
            await self.say("Não pode dar like na sua própria mensagem")
            return

        if msg.channel.id == star_channel.id:
            await self.say(':busstop: Você não pode dar like nas mensagens da #estrelinha')
            return

        # self.stars[message.server.id] = db
        await self.save_stars()
        return
