#!/usr/bin/env python3

import discord
import asyncio

import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

import time
import datetime
import traceback

STARBOARD_HELPTEXT = '''
O Starboard do josé permite aos usuários darem like nas mensagens, sem precisar de Pin ou algo do tipo.
`!like <message ID>` - manda aquele laik :top:
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
                await self.debug("load_stars: erro carregando estrelinha.db(%s)" % e)
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

    def make_emoji(self, likes):
        if likes > 0:
            return ':ok_hand:'
        elif likes > 2:
            return ':star:'
        elif likes > 4:
            return ':star2:'

    async def make_message(self, msg, likes):
        emoji = self.make_emoji(likes)
        content = msg.clean_content

        if msg.attachments:
            attachments = '(attachment: {[url]})'.format(msg.attachments[0])
            if content:
                content = content + ' ' + attachments
            else:
                content = attachments

        # <emoji> <star> <content> - <time> by <user> in <channel>
        if likes > 1:
            base = '{0} **{1}**'
        else:
            base = '{0}'

        fmt = base + ' {2} - {3.timestamp:%Y-%m-%d %H:%M UTC} by {3.author} in {3.channel.mention} (ID: {3.id})'
        return fmt.format(emoji, likes, content, msg)

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

        msg = await self.client.get_message(message.channel, msg_id)
        if msg is None:
            await self.bot.say(':question: Mensagem não encontrada')
            return

        stars = db.get(message, [None, []])
        starrers = stars[1]
        if starrer.id in starrers:
            await self.say("Você já deu like nesta mensagem")
            return

        if starrer.id == msg.author.id:
            await self.say("Não pode dar like na sua própria mensagem")
            return

        if msg.channel.id == star_channel.id:
            await self.say(':busstop: Você não pode dar like nas mensagens da #estrelinha')
            return

        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        if msg.timestamp < seven_days_ago:
            await self.say(':busstop: Esta mensagem tem mais de 7 dias.')
            return

        to_send = await self.make_message(msg, len(starrers) + 1)
        if len(to_send) > 2000:
            await self.say(':busstop: Mensagem muito grande.')
            return

        try:
            await self.client.delete_message(message)
        except:
            pass

        starrers.append(starrer.id)
        db[message] = stars

        # freshly starred
        if stars[0] is None:
            sent = await self.client.send_message(star_channel, to_send)
            stars[0] = sent.id

            db[message] = stars
            self.stars[message.server.id] = db
            await self.save_stars()
            return

        bot_msg = await self.client.get_message(starboard, stars[0])

        await self.bot.edit_message(bot_msg, to_send)
        self.stars[message.server.id] = db

        await self.save_stars()

        return
