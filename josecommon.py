import asyncio
import datetime
import time
import re
import json
import os
import sqlite3
import aioredis
import logging
import subprocess
from random import SystemRandom
random = SystemRandom()

import joseerror as je
import jplaying_phrases as playing_phrases

import discord

discord_logger = logging.getLogger('discord')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# José.log = all logs
handler = logging.FileHandler('José.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

JOSE_VERSION = '1.5.4'
JOSE_PREFIX = 'j!'
LEN_PREFIX = len(JOSE_PREFIX)

MARKOV_LENGTH_PATH = 'db/wordlength.json'
MARKOV_MESSAGES_PATH = 'db/messages.json'
STAT_DATABASE_PATH = 'db/stats.json'
CONFIGDB_PATH = 'db/languages.json'
CONFIGDB_PREFIX = 'config'

JOSE_DEV_SERVER_ID = '273863625590964224'
JOSE_ID = '202587271679967232'
JOSE_APP_ID = '202586824013643777'
JOSE_LOG_CHANNEL_ID = '290698227483934721'
OAUTH_URL = 'https://discordapp.com/oauth2/authorize?client_id=%s&scope=bot&permissions=67259457' % JOSE_APP_ID

_now = datetime.datetime.utcnow()
APRIL_FOOLS = _now.month == 4 and _now.day == 1

#configuration things
ADMIN_TOPICS = {
    # Luna, Corno, Dan
    '162819866682851329': ('Development',),
    '144377237997748224': ('General Support',),
    '191334773744992256': ('General Support',),
}

ADMIN_IDS = list(ADMIN_TOPICS.keys())

COOLDOWN_SECONDS = 4

# 1.5 percent
JC_PROBABILITY = .015
JC_REWARDS = [0, 0, 0, 0.6, 0.7, 1, 1.2, 1.5, 1.7]

# pricing for things
LEARN_PRICE = 10
IMG_PRICE = 1.3
OP_TAX_PRICE = 0.80
API_TAX_PRICE = 0.60

# playing status
PL_MIN_MINUTES = 3.2
PL_MAX_MINUTES = 12

ascii_to_wide = dict((i, chr(i + 0xfee0)) for i in range(0x21, 0x7f))
ascii_to_wide.update({0x20: u'\u3000', 0x2D: u'\u2212'})  # space and minus

WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
WIDE_MAP[0x20] = 0x3000

client = None

def set_client(_client):
    global client
    client = _client

# Phrases that will be shown randomly when jose starts
JOSE_PLAYING_PHRASES = playing_phrases.JOSE_PLAYING_PHRASES

WELCOME_MESSAGE = '''
Thanks for implementing José v{} into your server!
Jose is a bot that learns to speak based on conversations that happen in your server.
**See `j!docs josespeak` to learn more about this.**
You can use `j!speaktrigger` or `j!spt` to hear what he has to say.
Turn on autospeak by using `j!jsprob 3` to make him have a 3% chance to reply per message.

Use `j!botblock` if you want to block/unblock bot messages coming into José.
Use `j!language en` to set your language to English or `j!language pt` to set your language to Portuguese.
Use the `j!confighelp` to find any other specific configuration

Use José\'s Discord server for support/help/feedback/etc https://discord.gg/5ASwg4C
'''.format(JOSE_VERSION)

JOSE_GENERAL_HTEXT = '''
Recommended *top notch* Reading, the command list:
Also `j!info` has the José Testing Enviroment invite if you have any problems.
---
Recomenado a leitura da lista de comandos, em inglês:
`j!info` tem o invite para o José Testing Enviroment se você tiver algum problema.
---

https://github.com/lkmnds/jose/blob/master/doc/cmd/listcmd.md
'''

LETTER_TO_PITCH = {
    "a": 34,
    "A": 35,
    "b": 36,
    "B": 37,
    "c": 38,
    "C": 39,
    "d": 40,
    "D": 41,
    "e": 42,
    "E": 43,
    "f": 44,
    "F": 45,
    "g": 46,
    "G": 47,
    "h": 48,
    "H": 49,
    "i": 50,
    "I": 51,
    "j": 52,
    "J": 53,
    "k": 54,
    "K": 55,
    "l": 56,
    "L": 57,
    "m": 58,
    "M": 59,
    "n": 60,
    "N": 61,
    "o": 62,
    "O": 63,
    "p": 64,
    "P": 65,
    "q": 66,
    "Q": 67,
    "r": 68,
    "R": 69,
    "s": 70,
    "S": 71,
    "t": 72,
    "T": 73,
    "u": 74,
    "U": 75,
    "v": 76,
    "V": 77,
    "w": 78,
    "W": 79,
    "x": 80,
    "X": 81,
    "y": 82,
    "Y": 83,
    "z": 84,
    "Z": 85,

    # numbahs
    "0": 86,
    "1": 87,
    "2": 88,
    "3": 89,
    "4": 90,
    "5": 91,
    "6": 92,
    "7": 93,
    "8": 94,
    "9": 95,
}

AVIAOS = [
    'https://www.aboutcar.com/car-advice/wp-content/uploads/2011/02/Spoiler.jpg',
    'http://i.imgur.com/eL2hUyd.jpg',
    'http://i.imgur.com/8kS03gI.jpg',
    'http://i.imgur.com/Zfb05Qh.jpg',
    'http://i.imgur.com/w8Tp5z2.jpg',
    'http://i.imgur.com/ptpQdQx.jpg',
    'http://i.imgur.com/szx1S9n.jpg',
    'http://i.imgur.com/GG3zk49.jpg',
    'http://i.imgur.com/9Jq6oo6.jpg',
    'http://i.imgur.com/AIbjvX7.jpg',
]

ATIVIDADE = [
    'http://i.imgur.com/lkZVh3K.jpg',
    'http://imgur.com/a/KKwId',
    'http://imgur.com/a/ekrmK'
]

async def parse_id(data, message=None):
    if data[0:2] == '<@':
        if data[2] == '!':
            return data[3:-1]
        else:
            return data[2:-1]
    elif data[0] == 'u':
        return data[1:]
    else:
        return None

def parse_command(message):
    if not isinstance(message, str):
        message = message.content

    if message.startswith(JOSE_PREFIX):
        k = message.find(" ")

        command = message[LEN_PREFIX:k]
        if k == -1:
            command = message[LEN_PREFIX:]

        args = message.split(' ')
        method = "c_%s" % command
        return command, args, method
    else:
        return False, None, None

def speak_filter(message):
    # remove URLs
    message = re.sub(r'https?:\/\/([\/\?\w\.\&\;\=\-])+', '', message)

    # remove numbers
    message = re.sub(r'\d+', '', message)

    # remove discord mentions
    message = re.sub(r'<@(\!)?\d+>', '', message)

    # remove @everyone and @here, of course
    message = re.sub(r'@everyone', '', message)
    message = re.sub(r'@here', '', message)

    # remove discord channels
    message = re.sub(r'<#(\!)?\d+>', '', message)

    # remove josé commands
    # REMEMBER TO CHANGE THIS IF COMMAND PREFIX CHANGE HAPPENS
    message = re.sub(r'j!\w+', '', message)

    return message

# Callbacks

# one table relationing callback ID to its function
callbacks = {}

class Callback:
    '''
    A callback is just an asyncio.Task on steroids.
    It does the "while True" and the "asyncio.sleep" for you
    Also Callbacks handle asyncio.CancelledError automatically
    '''
    def __init__(self, cid, func, sec):
        self.func = func
        self.sec = sec
        self.run = False
        self.cid = cid
        self.last_run = None
        self.task = None

    async def do(self):
        try:
            logger.info("[callback:%s] running", self.cid)
            while self.run:
                logger.debug("%s: called", self.cid)

                try:
                    self.last_run = time.time()
                    await self.func()
                except:
                    logger.error('Error at cbk %s.do', self.cid, exc_info=True)

                await asyncio.sleep(self.sec)
            logger.debug("[callback:%s] finished", self.cid)
        except asyncio.CancelledError as err:
            logger.info("[callback:%s] Cancelled", self.cid)

    def stop(self):
        self.run = False

    def start(self):
        self.run = True

async def run_callback(callback_id, callback):
    if callback_id in callbacks:
        return None

    callbacks[callback_id] = callback
    callback.start()
    callback.task = client.loop.create_task(callback.do())

    return True

async def callback_call(callback_id):
    if callback_id not in callbacks:
        return None

    callback = callbacks[callback_id]
    res = await callback.func()
    return res

def callback_remove(callback_id):
    if callback_id not in callbacks:
        return None

    callback = callbacks[callback_id]
    callback.task.cancel()
    callback.stop()
    del callbacks[callback_id]

    return True

# === DATABASE API ===

conn = None
JOSE_DATABASE_PATH = "jose.db"
statements = 0

async def init_db(client):
    global conn
    logger.info("Initialize jose SQL database")
    conn = sqlite3.connect(JOSE_DATABASE_PATH)

async def register_table(tableid, table_stmt):
    global conn
    logger.info("Register table %s", tableid)
    cur = conn.cursor()
    cur.execute(table_stmt)
    conn.commit()

async def do_stmt(stmt, params=None):
    global conn, statements
    cur = conn.cursor()
    cur.execute(stmt, params)
    statements += 1
    return cur

def commit_changes():
    conn.commit()

class DatabaseAPI:
    '''
    DatabaseAPI - A general SQL API for Extensions
    All operations are handled using Python's SQLite, meaning its blocking.

    There is a Callback at the joselang module that runs
    every 5 minutes to commit data to the database
    '''
    def __init__(self, _client):
        global conn, statements
        self.client = _client
        self.conn = conn
        self.statements = statements

    async def initializedb(self):
        await init_db(self.client)

    async def register(self, tablename, tablestmt):
        await register_table(tablename, tablestmt)

    def _register(self, tablename, tablestmt):
        return asyncio.ensure_future(self.register(tablename, tablestmt), \
            loop=self.client.loop)

    async def do(self, stmt, params=None):
        cur = await do_stmt(stmt, params)
        return cur

    def commit(self):
        commit_changes()

class Extension:
    '''
    Extension - A general extension used by josé

    The Extension class defines the API for josé's modules,
    all modules inherit from this class.
    '''
    def __init__(self, _client):
        self.client = _client
        self.loop = _client.loop
        self.logger = logger.getChild('Extension')

        self._callbacks = {}
        self._databases = {}
        self.dbapi = DatabaseAPI(self.client)

    async def rolecheck(self, cxt, correct_role):
        roles = [role.name == correct_role for role in cxt.message.author.roles]
        if not True in roles:
            raise je.PermissionError()
        else:
            return True

    async def is_admin(self, uid):
        if uid in ADMIN_IDS:
            return True
        else:
            raise je.PermissionError()

    async def brolecheck(self, cxt, correct_role):
        try:
            res = await self.rolecheck(cxt, correct_role)
            return res
        except je.PermissionError:
            return False

    async def b_isowner(self, cxt):
        return cxt.message.author.id in ADMIN_IDS

    def _mkdown(self, string):
        return string.replace('`', '\\`')

    def codeblock(self, lang, string):
        return "```%s\n%s```" % (lang, self._mkdown(string))

    def noasync(self, func, args):
        return asyncio.ensure_future(func(*args), loop=self.loop)

    def cbk_new(self, callback_id, func, timer_sec):
        '''Create a new callback'''
        logger.info("New callback %s every %d seconds", callback_id, timer_sec)

        self._callbacks[callback_id] = Callback(callback_id, func, timer_sec)

        status = self.noasync(run_callback, [callback_id, \
            self._callbacks[callback_id]])

        if status is None:
            logger.error("Error happened in callback %s", callback_id)

    async def cbk_call(self, callback_id):
        '''Call an already running callback'''
        status = await callback_call(callback_id)
        if status is None:
            logger.error("Error calling callback %s", callback_id)
            return

        logger.info("called callback %s", callback_id)

    def cbk_remove(self, callback_id):
        '''Remove an existing callback'''
        status = callback_remove(callback_id)
        if status is None:
            logger.error("Error removing callback %s", callback_id)
            return

        del self._callbacks[callback_id]
        logger.info("Callback %s removed", callback_id)

    async def jsondb_save_all(self):
        if len(self._databases) <= 0:
            return

        for database_id in self._databases:
            self.jsondb_save(database_id)

    def jsondb(self, database_id, **kwargs):
        '''Use JSON storage'''
        if database_id in self._databases:
            return None

        database_path = kwargs.get('path')
        attribute = kwargs.get('attribute', database_id)
        default_file = kwargs.get('default', '{}')

        # only create callback when actually needed
        if len(self._databases) < 1:
            self.cbk_new('jsondb:save_all', self.jsondb_save_all, 1200)

        self._databases[database_id] = {
            'attr': attribute,
            'path': database_path,
        }

        setattr(self, attribute, {})

        if not os.path.isfile(database_path):
            with open(database_path, 'w') as dbfile:
                dbfile.write(default_file)

        setattr(self, attribute, json.load(open(database_path, 'r')))

    def jsondb_save(self, database_id):
        '''Save an already existing jsondb'''
        if database_id not in self._databases:
            return None

        database = self._databases[database_id]
        attribute = database['attr']
        database_path = database['path']

        try:
            json.dump(getattr(self, attribute), open(database_path, 'w'))
        except:
            return False

# === LANGUAGE STUFF ===

EN_LANGUAGE_PATH = './locale/jose.en.json'
PT_LANGUAGE_PATH = './locale/jose.pt.json'

class LangObject:
    def __init__(self, fpath):
        self.path = fpath
        self.database = json.load(open(fpath, 'r'))

    def reload_db(self):
        self.database = json.load(open(self.path, 'r'))

    def gettext(self, msgid):
        res = self.database.get(msgid, "")
        if len(res) == 0:
            return msgid
        else:
            return res

# initialize language object for each language
LANGUAGE_OBJECTS = {
    'en': LangObject(EN_LANGUAGE_PATH),
    'pt': LangObject(PT_LANGUAGE_PATH),
}

def get_defaultcdb():
    return {
        'botblock': 1,
        'language': 'default',
        'imgchannel': 'None',
        'speak_channel': '',
        'prefix': JOSE_PREFIX,
        'speak_prob': 0,
        'fw_prob': 0.1,
    }

redis = None
cdb_cache = {}

def make_rkey(server_id):
    return '{0}:{1}'.format(CONFIGDB_PREFIX, server_id)

def from_redis(element, flag=False):
    if element == 'None':
        element = None

    try:
        if element[0] == 's':
            if flag:
                return element
            else:
                return element[1:]
    except:
        pass

    try:
        element = int(element)
        return element
    except:
        pass

    try:
        element = float(element)
        return element
    except:
        pass

    return element

def redis_value(value):
    if value is None:
        value = 'None'
    elif value is True:
        value = 1
    elif value is False:
        value = 0
    elif isinstance(value, str):
        return 's%s' % value

    return value

async def configdb_raw_load():
    global redis
    loop = asyncio.get_event_loop()
    redis = await aioredis.create_redis(('localhost', 6379), loop=loop)
    status = await redis.ping()
    status = status.decode('utf-8')
    if status == 'PONG':
        return True
    return False

async def configdb_ensure(server_id):
    rediskey = make_rkey(server_id)
    exists = await redis.exists(rediskey)

    if not exists:
        default_cdb = get_defaultcdb()

        res = await redis.hmset_dict(rediskey, default_cdb)
        if not res:
            logger.error("Error creating configdb for server %s", rediskey)

    # set empty cache
    cdb_cache[server_id] = {}

async def configdb_ensure_key(server_id, key, default):
    await configdb_ensure(server_id)

    rediskey = make_rkey(server_id)
    exists = await redis.hexists(rediskey, key)
    if not exists:
        default = redis_value(default)
        res = await redis.hmset(rediskey, key, default)
        if not res:
            logger.error("Error ensuring key %s = %s for key %s", key, default, rediskey)


async def configdb_set(server_id, key, value):
    global cdb_cache
    await configdb_ensure(server_id)
    rediskey = make_rkey(server_id)

    value = redis_value(value)

    try:
        await redis.hmset(rediskey, key, value)
        res = await redis.hmget(rediskey, key)
        after = next(iter(res)).decode('utf-8')
        after = from_redis(after, True)

        if after != value:
            logger.warning("[cdb] configdb_set(%s, %s) = %r != %r", server_id, key, value, after)
            return False

        # overwrite cache
        cdb_cache[server_id][key] = value
        return True

    except Exception as err:
        logger.error('configdb_set(%s, %s)', server_id, key, exc_info=True)
        return False

async def configdb_get(server_id, key, default=None):
    global cdb_cache

    # ensure first, get cache LATER
    await configdb_ensure(server_id)

    if key in cdb_cache[server_id]:
        element = from_redis(cdb_cache[server_id][key])
        return element

    rediskey = make_rkey(server_id)
    res = await redis.hmget(rediskey, key)

    # aioredis returns a set... I'm pretty WTF rn but ok.
    try:
        element = from_redis(next(iter(res)).decode('utf-8'))
    except AttributeError:
        return 'vNothing'

    # insert in cache
    cdb_cache[server_id][key] = element

    return element

async def save_configdb():
    logger.info("savedb:r_config")
    try:
        # don't use aioredis, use subprocess
        _out = subprocess.check_output('redis-cli save', shell=True)
        out = _out.decode('utf-8')
        if not out.startswith('OK'):
            logger.warning("[save_configdb] error saving: %s", out)
            return False, out

        return True, ''
    except Exception as err:
        return False, repr(err)

async def load_configdb():
    logger.info("load_db:r_config")
    try:
        res = await configdb_raw_load()
        if not res:
            return False, 'raw_load sent false'

        # ensure new configdb features are already there
        default = get_defaultcdb()

        # get all keys (yes its inneficient)
        # TODO: use SCAN?
        keys = await redis.keys('*')
        for rediskey in keys:
            rediskey = rediskey.decode('utf-8')
            if rediskey.startswith('{}:'.format(CONFIGDB_PREFIX)):
                server_id = rediskey.split(':')[1]

                # create serverid entry in cache
                cdb_cache[server_id] = {}

                for key in default:
                    await configdb_ensure_key(server_id, key, default[key])

        await save_configdb()

        return True, ''
    except Exception as err:
        return False, repr(err)

# langdb stuff
async def langdb_set(sid, lang):
    await configdb_set(sid, 'language', lang)

async def langdb_get(sid):
    res = await configdb_get(sid, 'language', 'default')
    return res

async def get_translated(langid, string):
    lang = LANGUAGE_OBJECTS.get(langid)
    if lang is None:
        # fallback, just return the same string
        return string
    else:
        return lang.gettext(string)

class Context:
    '''
    Context - context class
    The context is passed to commands when they are called

    Context abstracts Client.send_message into Context.say,
    which handles translation, if possible
    '''
    def __init__(self, _client, message, t_creation=None, jose=None):
        if t_creation is None:
            t_creation = time.time()

        self.message = message
        self.server = message.server
        self.channel = message.channel
        self.author = message.author
        self.me = message.server.me

        self.client = _client
        self.t_creation = t_creation
        self.jose = jose
        self.env = {}

    async def send_typing(self):
        try:
            await self.client.send_typing(self.message.channel)
        except discord.Forbidden:
            # I really don't care anymore
            pass
        except Exception as err:
            logger.error('send_typing', exc_info=True)

    async def say_embed(self, em, channel=None):
        if channel is None:
            channel = self.message.channel

        await self.client.send_message(channel, embed=em)

    async def say(self, string, _channel=None, tup=None):
        channel = None
        if isinstance(_channel, tuple):
            tup = _channel
            channel = self.message.channel
        else:
            channel = _channel

        if channel is None:
            channel = self.message.channel

        if len(string) > 2000:
            await self.client.send_message(channel, \
                ":elephant: Mensagem muito grande :elephant:")
        else:
            if redis is None:
                logger.info("Loading configuration database @ cxt.say")
                await load_configdb()

            lang = 'default'
            if self.message.server is not None:
                lang = await langdb_get(self.message.server.id)

            translated = await get_translated(lang, string)

            if tup is not None:
                translated = translated % tup

            try:
                if len(translated) < 1:
                    ret = await self.say("Can't send empty message", _channel, tup)
                    return ret
                else:
                    if APRIL_FOOLS:
                        translated = translated[::-1]
                    ret = await self.client.send_message(channel, translated)
                    return ret
            except discord.Forbidden:
                # I don't care anymore
                return False

class EmptyContext:
    '''
    EmptyContext - Capture output from commands

    This Context clone just implements the send_typing and say methods.
    It also provides a getall method when your command ends.
    '''
    def __init__(self, _client, message):
        self.client = _client
        self.message = message
        self.messages = []
        self.env = {}

    async def send_typing(self):
        return None

    async def say(self, string, _channel=None, tup=None):
        if isinstance(_channel, tuple):
            tup = _channel

        lang = 'default'

        translated = await get_translated(lang, string)
        if tup is not None:
            translated = translated % tup

        self.messages.append(translated)
        return False

    async def getall(self):
        return '\n'.join(self.messages)

# logging

class ChannelHandler(logging.Handler):
    '''
    ChannelHandler - Logging handler to send log messages to a Discord channel

    The handler already asummes that the client can see the
    channel when it receives a READY event.

    To prevent ratelimiting, instead of sending a message on every log entry,
    the handler queues log events and sends them every 10 seconds(ChannelHandler.watcher),
    emptying the queue afterwards.
    '''
    def __init__(self, channel_id):
        logging.Handler.__init__(self)
        self.channel_id = channel_id
        self.channel = None
        self._queue = []

        # You don't want to disable this.
        self.use_queue = True

    async def setup(self):
        '''Wait until the client is ready to get a Channel object'''
        await client.wait_until_ready()
        self.channel = client.get_channel(self.channel_id)

    def dump_queue(self):
        # only dump the queue if actually needed
        if len(self._queue) > 0:
            res = '\n'.join(self._queue)
            asyncio.ensure_future(client.send_message(self.channel, res), \
                loop=client.loop)

            # empty it afterwards
            self._queue = []

    async def watcher(self):
        await client.wait_until_ready()
        while True:
            self.dump_queue()
            await asyncio.sleep(10)

    def queue_message(self, string):
        self._queue.append(string)

    def emit(self, record):
        # only start receiving log entries when José is actually ready
        # and has a log channel in place
        if self.channel is not None:
            _msg = self.format(record)
            msg = '\n**`[{}] [{}]`** `{}`'.format(record.levelname, \
                record.name, _msg)

            if self.use_queue:
                self.queue_message(msg)
            else:
                asyncio.ensure_future(client.send_message(self.channel, msg), \
                    loop=client.loop)

    def in_shutdown(self):
        self.dump_queue()
        self.channel = None

log_channel_handler = ChannelHandler(JOSE_LOG_CHANNEL_ID)

async def setup_logging():
    await client.wait_until_ready()
    await log_channel_handler.setup()
    logger.addHandler(log_channel_handler)
    discord_logger.addHandler(log_channel_handler)
