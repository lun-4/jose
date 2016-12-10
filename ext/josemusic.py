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

class MusicEntry:
    def __init__(self, msg, player):
        self.requester = msg.author
        self.player = player

    def __str__(self):
        fmt = '*%s* (%s) pedido por %s'
        return fmt % (self.player.title, self.player.uploader, self.requester)

class VoiceState:
    def __init__(self, jm):
        self.jm = jm
        self.current = None
        self.voice = None
        self.task_flag = True
        self.songs = asyncio.Queue()

        self.play_next_song = asyncio.Event()
        # self.songs = asyncio.Queue()
        self.skip_votes = set()

        self.player = jm.client.loop.create_task(self.player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    def player(self):
        return self.current.player

    async def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.current.player.stop()
        else:
            await self.say("[VS.skip]: não estou tocando nada")

    def toggle_next(self):
        self.play_next_song.set()

    async def player_task(self):
        while self.task_flag:
            # clear event
            self.play_next_song.clear()

            # get next song
            self.current = await self.songs.get()
            print("GOT CURRENT: %s" % self.current)

            # show current song
            await self.jm.say('ZELAO® tocando: %s' % str(self.current), channel=self.jm.message_channel)

            # play and wait for next trigger
            self.current.player.start()
            await self.play_next_song.wait()

class JoseMusic(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

        self.state = None
        self.player = None

        self.init_flag = False
        self.started_flag = False

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    def get_voice_state(self):
        if self.state is None:
            self.state = VoiceState(self)

        return self.state

    async def c_minit(self, message, args):
        '''`!minit` - inicia o JMusic'''
        await self.rolecheck(MUSIC_ROLE)

        if self.init_flag:
            await self.say("JMusic já foi iniciado")
            return

        # get server channel
        self.voice_channel = discord.utils.get(message.server.channels, name='funk')
        if self.voice_channel is None:
            await self.say("Canal de voz #funk não existe")
            return

        try:
            voice = await self.client.join_voice_channel(self.voice_channel)
        except discord.InvalidArgument:
            await self.say("Isso não é um canal de voz...")
            return

        # initialize voice state
        state = self.get_voice_state()
        state.voice = voice
        self.message_channel = message.channel
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
        await self.rolecheck(MUSIC_ROLE)

        if not self.init_flag:
            await self.say("JMusic não foi iniciado")
            return

        state = self.state
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        song = ' '.join(args[1:])
        player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)


        player.volume = 0.6
        entry = MusicEntry(message, player)
        await self.say('Colocado na fila: %s' % entry)
        await state.songs.put(entry)

    '''async def c_mstart(self, message, args):
        await self.rolecheck(MUSIC_ROLE)
        if not self.started_flag:
            self.started_flag = True
            await self.state.player_task()
            await self.say("o player terminou... isso não deveria acontecer... né?")
        else:
            await self.say("Player já iniciado")'''

    async def c_mpause(self, message, args):
        '''`!mpause` - pausa uma música'''
        await self.rolecheck(MUSIC_ROLE)

        if self.state.is_playing():
            self.state.current.player.pause()

    async def c_mresume(self, message, args):
        '''`!mresume` - resume uma música'''
        await self.rolecheck(MUSIC_ROLE)

        if self.state.is_playing():
            self.state.current.player.resume()

    async def c_mstop(self, message, args):
        '''`!mstop` - PARA TUDO'''
        await self.rolecheck(MUSIC_ROLE)
        state = self.state

        if state.is_playing():
            player = state.current.player
            player.stop()

        state.taskflag = False
        await self.state.voice.disconnect()
        del self.state

    async def c_mqueue(self, message, args):
        '''`!mqueue` - mostra a fila de músicas'''
        res = 'Lista de músicas: \n'
        for song in list(self.state.songs._queue):
            res += '\t * %s\n' % song
        await self.say(res)

    async def c_skip(self, message, args):
        pass
