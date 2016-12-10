#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import jauxiliar as jaux
import joseerror as je

MUSIC_ROLE = 'music'

# sanity test
if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

class JoseExtension(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

        self.state = None
        self.player = None

        self.init_flag = False
        self.started_flag = False

    async def ext_load(self):
        pass

    async def ext_unload(self):
        pass

    def get_voice_state(self):
        if self.state is None:
            self.state = VoiceState(self)

        return self.state

    async def c_minit(self, message, args):
        '''`!minit` - inicia o JMusic'''
        await self.rolecheck(MUSIC_ROLE)

        if self.init_flag:
            return self.say("JMusic já foi iniciado")

        # get server channel
        self.voice_channel = discord.utils.get(msg.server.channels, name='funk')
        if self.voice_channel is None:
            return self.say("Canal de voz #funk não existe")

        try:
            voice = await self.client.join_voice_channel(self.voice_channel)
        except discord.InvalidArgument:
            return self.say("Isso não é um canal de voz...")

        # initialize voice state
        state = self.get_voice_state()
        state.voice = voice
        self.message_channel = msg.channel
        self.init_flag = True
        await self.say("`[jmusic] init`")

    async def c_mstat(self, message, args):
        '''`!mstat` - checa o status do JMusic'''
        res = ''
        res += 'JMusic iniciado[init_flag]: %s\n' % self.init_flag

        if self.init_flag:
            is_playing = self.state.is_playing()
            res += 'state.isplaying = %r\n' % is_playing
            if is_playing:
                res + 'state.current: %r' % self.state.current

        await self.say(self.codeblock('', res))

    async def c_play(self, message, args):
        pass

    async def c_mpause(self, message, args):
        pass

    async def c_mresume(self, message, args):
        pass

    async def c_mstop(self, message, args):
        pass

    async def c_mqueue(self, message, args):
        pass

    async def c_skip(self, message, args):
        pass
