import sys
import asyncio
sys.path.append("..")

import discord
import youtube_dl

import josecommon as jcommon
import joseerror as je
MUSIC_ROLE = 'music'

# sanity test
if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

@asyncio.coroutine
def check_roles(correct, rolelist):
    for role in rolelist:
        if role.name == correct:
            return True
    return False


class Entry:
    def __init__(self, m, pl):
        self.requester = m.author
        self.channel = m.channel
        self.player = pl

    def __str__(self):
        fmt = '*%s* por %s, pedido por %s'
        return (fmt % (self.player.title, self.player.uploader, self.requester))


class VoiceState:
    def __init__(self, jm):
        self.current = None
        self.voice = None
        self.jm = jm
        self.songlist = []
        self.taskflag = True

        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set() # a set of user_ids that voted
        self.player_task()

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
            try:
                self.current.player.stop()
                #self.songlist.pop()
            except Exception as e:
                await self.say('pyerr: %s' % e)
        else:
            await self.say("c_skip: não estou tocando nada")

    def toggle_next(self):
        self.play_next_song.set()

    async def player_task(self):
        while self.taskflag:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            try:
                self.songlist.pop()
            except Exception as e:
                await self.jm.say('pyerr: %s' % e)

            await self.jm.say('ZELAO® tocando: %s' % str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()

class JoseMusic(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.voice_channel = discord.Object(id='208768258818441219') # funk

        # stuff
        self.c_message = ''
        self.player = None
        self.state = None

        # flags
        self.init_flag = False
        self.loop_started = False

    def get_voice_state(self):
        if self.state is None:
            self.state = VoiceState(self)

        return self.state

    async def c_mstat(self, msg, args):
        res = ''
        res += 'JMusic iniciado: %s\n' % self.init_flag
        if self.init_flag and self.state:
            ispl = self.state.is_playing()
            res += 'tocando música? %s\n' % ispl
            if ispl:
                res += 'Música sendo tocada: %s\n' % self.state.current
        await self.say("%s" % res)

    async def c_minit(self, msg, args):
        auth = await self.rolecheck(MUSIC_ROLE)

        if self.init_flag:
            await self.say("JMusic já conectado")
            return

        voice = await self.client.join_voice_channel(self.voice_channel)
        state = self.get_voice_state()
        state.voice = voice
        self.init_flag = True

    async def c_play(self, message, args):
        auth = await self.rolecheck(MUSIC_ROLE)

        if not self.init_flag:
            await self.say("JMusic não foi iniciado")
            return

        state = self.state
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        args = message.content.split(' ')
        song = ' '.join(args[1:])
        player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)


        player.volume = 0.6
        entry = Entry(message, player)
        await self.say('Colocado na fila: %s' % entry)
        state.songlist.append(entry)
        await state.songs.put(entry)

    async def c_pause(self, message, args):
        auth = await self.rolecheck(MUSIC_ROLE)

        if self.state.is_playing():
            player = self.state.current.player
            player.pause()

    async def c_resume(self, message, args):
        auth = await check_roles(MUSIC_ROLE, message.author.roles)
        if not auth:
            await self.say("jm_PermissionError: usuário não autorizado")
            return

        if self.state.is_playing():
            player = self.state.current.player
            player.resume()

    async def c_queue(self, message, args):
        auth = await self.rolecheck(MUSIC_ROLE)
        res = 'Lista de sons: \n'
        for song in self.state.songlist:
            res += ' * %s\n' % song
        await self.say(res)

    async def c_playing(self, message, args):
        if self.loop_started:
            if self.state.is_playing():
                await self.say('Música sendo tocada: %s\n' % self.state.current)
            else:
                await self.say("Nenhuma música sendo tocada")
        else:
            await self.say("Loop não iniciado")

    async def c_stop(self, message, args):
        auth = await self.rolecheck(MUSIC_ROLE)
        state = self.state

        if state.is_playing():
            player = state.current.player
            player.stop()

        try:
            state.taskflag = False
            await self.state.voice.disconnect()
            del self.state
        except Exception as e:
            await self.say("c_stop: pyerr: %s" % e)

    async def c_zelao(self, message, args):
        auth = await self.rolecheck(MUSIC_ROLE)
        if not self.loop_started:
            self.loop_started = True
            await self.state.player_task()
            await self.say("o player terminou... isso não deveria acontecer... né?")
        else:
            await self.say("Player já iniciado")

    async def c_skip(self, message, args):
        if not self.state.is_playing():
            await self.say('Nenhuma música sendo tocada para pular')
            return

        voter = message.author
        state = self.state
        if voter == state.current.requester:
            await self.say('Solicitante pediu para pular a música...')
            await state.skip()
            return

        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 3:
                await self.say('3 votos, pulando...')
                await state.skip()
                return
            else:
                await self.say('Voto adicionado, já existem [{}/3]'.format(total_votes))
        else:
            await self.say('Você já votou.')

'''cmds_start = {
    '!mstat': jm.c_status,
    '!minit': jm.c_init,

    '!play': jm.c_play,
    '!queue': jm.c_queue,
    '!zelao': jm.c_zelao,

    '!pause': jm.c_pause,
    '!resume': jm.c_resume,
    '!stop': jm.c_stop,

    '!skip': jm.c_skip,
    '!playing': jm.c_playing,
}
'''
