import asyncio
import discord
from discord.ext import commands

# sanity test
if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

class Entry:
    def __init__(self, m, pl):
        self.requester = m.author
        self.channel = m.channel
        self.player = pl

    def __str__(self):
        fmt = '*%s* pedido por %s'
        return (fmt % (self.player.title, self.requester))


class VoiceState:
    def __init__(self, jm):
        self.current = None
        self.voice = None
        self.jm = jm

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

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.play_next_song.set()

    @asyncio.coroutine
    def player_task(self):
        yield from self.jm.say("ZELAO INCORPORATED MUSIC START LOOP")
        while True:
            self.play_next_song.clear()
            yield from self.jm.say("ZELAO INCORPORATED CLEAR MUSIC LIST")
            self.current = yield from self.songs.get()
            yield from self.jm.say('ZELAO INC. ESTA TOCANDO %s' % str(self.current))
            self.current.player.start()
            yield from self.play_next_song.wait()
            yield from self.jm.say("ZELAO INCORPORATED WAIT FOR PROXIMO SOM")

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
        res += 'JMusic iniciado: %s' % self.init_flag
        if self.init_flag and self.state:
            ispl = self.state.is_playing()
            res += 'tocando música? %s\n' % ispl
            if ispl:
                res += 'Música sendo tocada: %s' % self.state.current
        yield from self.say("%s" % res)

    @asyncio.coroutine
    def c_init(self, msg):
        if self.init_flag:
            yield from self.jm.say("JMusic já conectado")
            return

        voice = yield from self.client.join_voice_channel(self.voice_channel)
        state = self.get_voice_state()
        state.voice = voice
        self.init_flag = True

    @asyncio.coroutine
    def c_play(self, message):
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
            yield from state.songs.put(entry)

    @asyncio.coroutine
    def c_pause(self, message):
        if self.state.is_playing():
            player = self.state.player
            player.pause()

    @asyncio.coroutine
    def resume(self, message):
        if self.state.is_playing():
            player = self.state.player
            player.resume()

    @asyncio.coroutine
    def c_queue(self, message):
        yield from self.say("queue: %s" % self.state.songs)

    @asyncio.coroutine
    def c_playing(self, message):
        pass

    @asyncio.coroutine
    def c_zelao(self, message):
        if not self.loop_started:
            self.loop_started = True
            yield from self.state.player_task()
        else:
            yield from self.say("Player já iniciado")

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
}
