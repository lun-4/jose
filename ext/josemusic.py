import asyncio
import discord
from discord.ext import commands

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

    @asyncio.coroutine
    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            try:
                self.current.player.stop()
                self.songlist.pop()
            except Exception as e:
                yield from self.jm.say('pyerr: %s' % e)
        else:
            yield from self.jm.say("c_skip: não estou tocando nada")

    def toggle_next(self):
        self.play_next_song.set()

    @asyncio.coroutine
    def player_task(self):
        while self.taskflag:
            self.play_next_song.clear()
            self.current = yield from self.songs.get()
            try:
                self.songlist.pop()
            except Exception as e:
                yield from self.jm.say('pyerr: %s' % e)

            yield from self.jm.say('ZELAO® tocando: %s' % str(self.current))
            self.current.player.start()
            yield from self.play_next_song.wait()

class JoseMusic:
    def __init__(self, cl):

        self.voice_channel = discord.Object(id='208768258818441219') # funk

        # stuff
        self.client = cl
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

    @asyncio.coroutine
    def say(self, msg):
        yield from self.client.send_message(self.c_message.channel, msg)

    @asyncio.coroutine
    def c_status(self, msg):
        res = ''
        res += 'JMusic iniciado: %s\n' % self.init_flag
        if self.init_flag and self.state:
            ispl = self.state.is_playing()
            res += 'tocando música? %s\n' % ispl
            if ispl:
                res += 'Música sendo tocada: %s\n' % self.state.current
        yield from self.say("%s" % res)

    @asyncio.coroutine
    def c_init(self, msg):
        auth = yield from check_roles(MUSIC_ROLE, msg.author.roles)
        if not auth:
            yield from self.say("jm_PermissionError: usuário não autorizado")
            return

        if self.init_flag:
            yield from self.say("JMusic já conectado")
            return

        voice = yield from self.client.join_voice_channel(self.voice_channel)
        state = self.get_voice_state()
        state.voice = voice
        self.init_flag = True

    @asyncio.coroutine
    def c_play(self, message):
        auth = yield from check_roles(MUSIC_ROLE, message.author.roles)
        if not auth:
            yield from self.say("jm_PermissionError: usuário não autorizado")
            return

        if not self.init_flag:
            yield from self.say("JMusic não foi iniciado")
            return

        state = self.state
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        try:
            args = message.content.split(' ')
            song = ' '.join(args[1:])
            player = yield from state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            yield from self.say("jm_err: pyerr: `%s`" % e)
        else:
            player.volume = 0.6
            entry = Entry(message, player)
            yield from self.say('Colocado na fila: %s' % entry)
            state.songlist.append(entry)
            yield from state.songs.put(entry)

    @asyncio.coroutine
    def c_pause(self, message):
        auth = yield from check_roles(MUSIC_ROLE, message.author.roles)
        if not auth:
            yield from self.say("jm_PermissionError: usuário não autorizado")
            return

        if self.state.is_playing():
            player = self.state.current.player
            player.pause()

    @asyncio.coroutine
    def c_resume(self, message):
        auth = yield from check_roles(MUSIC_ROLE, message.author.roles)
        if not auth:
            yield from self.say("jm_PermissionError: usuário não autorizado")
            return

        if self.state.is_playing():
            player = self.state.current.player
            player.resume()

    @asyncio.coroutine
    def c_queue(self, message):
        auth = yield from check_roles(MUSIC_ROLE, message.author.roles)
        if not auth:
            yield from self.say("jm_PermissionError: usuário não autorizado")
            return
        res = 'Lista de sons: \n'
        for song in self.state.songlist:
            res += ' * %s\n' % song
        yield from self.say(res)

    @asyncio.coroutine
    def c_playing(self, message):
        if self.loop_started:
            if self.state.is_playing():
                yield from self.say('Música sendo tocada: %s\n' % self.state.current)
            else:
                yield from self.say("Nenhuma música sendo tocada")
        else:
            yield from self.say("Loop não iniciado")

    @asyncio.coroutine
    def c_stop(self, message):
        auth = yield from check_roles(MUSIC_ROLE, message.author.roles)
        if not auth:
            yield from self.say("jm_PermissionError: usuário não autorizado")
            return
        state = self.state

        if state.is_playing():
            player = state.current.player
            player.stop()

        try:
            state.taskflag = False
            yield from self.state.voice.disconnect()
            del self.state
        except Exception as e:
            yield from self.say("c_stop: pyerr: %s" % e)

    @asyncio.coroutine
    def c_zelao(self, message):
        auth = yield from check_roles(MUSIC_ROLE, message.author.roles)
        if not auth:
            yield from self.say("jm_PermissionError: usuário não autorizado")
            return
        if not self.loop_started:
            self.loop_started = True
            yield from self.state.player_task()
            yield from self.say("o player terminou... isso não deveria acontecer... né?")
        else:
            yield from self.say("Player já iniciado")

    @asyncio.coroutine
    def c_skip(self, message):
        if not self.state.is_playing():
            yield from self.say('Nenhuma música sendo tocada para pular')
            return

        voter = message.author
        state = self.state
        if voter == state.current.requester:
            yield from self.say('Solicitante pediu para pular a música...')
            yield from state.skip()
            return

        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 3:
                yield from self.say('3 votos, pulando...')
                yield from state.skip()
                return
            else:
                yield from self.say('Voto adicionado, já existem [{}/3]'.format(total_votes))
        else:
            yield from self.say('Você já votou.')

    @asyncio.coroutine
    def recv(self, msg):
        self.c_message = msg

jm = JoseMusic(None)

cmds_start = {
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
