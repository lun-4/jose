import asyncio
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
import randemoji as emoji

import discord

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

JOSE_VERSION = '1.4.6'
JOSE_PREFIX = "j!"
LEN_PREFIX = len(JOSE_PREFIX)

MARKOV_LENGTH_PATH = 'db/wordlength.json'
MARKOV_MESSAGES_PATH = 'db/messages.json'
STAT_DATABASE_PATH = 'db/stats.json'
CONFIGDB_PATH = 'db/languages.json'

JOSE_DEV_SERVER_ID = '273863625590964224'
JOSE_ID = '202587271679967232'
JOSE_APP_ID = '202586824013643777'
OAUTH_URL = 'https://discordapp.com/oauth2/authorize?client_id=%s&scope=bot&permissions=67259457' % JOSE_APP_ID

#configuration things
ADMIN_TOPICS = {
    # Luna, Corno, Dan and Nat
    '162819866682851329': ('Development',),
    '144377237997748224': ('General Support',),
    '191334773744992256': ('General Support',),
    '142781100152848384': ('Development',),
}

ADMIN_IDS = list(ADMIN_TOPICS.keys())

COOLDOWN_SECONDS = 4
PIRU_ACTIVITY = .0000069

# 1 percent
JC_PROBABILITY = .015
JC_REWARDS = [0, 0, 0, 0.6, 0.7, 1, 1.2, 1.5, 1.7]

LEARN_PRICE = 10
IMG_PRICE = 1.3
OP_TAX_PRICE = 0.80
API_TAX_PRICE = 0.60

PL_MIN_MINUTES = 2
PL_MAX_MINUTES = 7

ascii_to_wide = dict((i, chr(i + 0xfee0)) for i in range(0x21, 0x7f))
ascii_to_wide.update({0x20: u'\u3000', 0x2D: u'\u2212'})  # space and minus

WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
WIDE_MAP[0x20] = 0x3000

client = None

def set_client(_client):
    global client
    client = _client

# Language database
configdb = None

# Phrases that will be shown randomly when jose starts
JOSE_PLAYING_PHRASES = playing_phrases.JOSE_PLAYING_PHRASES

WELCOME_MESSAGE = '''
Thanks for implementing José v{} into your server!
Jose is a bot that learns to speak based on conversations that happen in your server.
**See `j!docs josespeak` to learn more about this.**
To start off, you need to generate at least 100+ messages, just talk and watch the magic happens!
When he's ready, you can use `j!speaktrigger` or `j!spt` to hear what he has to say.

Use `j!botblock` if you want to block/unblock bot messages coming into José.
Use `j!language en` to set your language to English or `j!language pt` to set your language to Portuguese.
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

async def jose_debug(message, dbg_msg):
    message_banner = '%s[%s]: %r' % (message.author, message.channel, message.content)
    dbg_msg = '%s -> %s' % (message_banner, str(dbg_msg))
    logger.info(dbg_msg)

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

async def show_top(message):
    await client.send_message(message.channel, "BALADINHA TOPPER %s %s" % (
        (":joy:" * random.randint(1, 5)),
        (":ok_hand:" * random.randint(1, 6))))

async def check_roles(correct, rolelist):
    roles = [role.name == correct for role in rolelist]
    return True in roles

async def random_emoji(maxn):
    return ''.join((str(emoji.random_emoji()) for i in range(maxn)))

ATIVIDADE = [
    'http://i.imgur.com/lkZVh3K.jpg',
    'http://imgur.com/a/KKwId',
    'http://imgur.com/a/ekrmK'
]

async def gorila_routine(channel):
    if random.random() < PIRU_ACTIVITY:
        await client.send_message(channel, random.choice(ATIVIDADE))

async def str_xor(string, other):
    return "".join(chr(ord(a) ^ ord(b)) for a, b in zip(string, other))

JCRYPT_KEY = 'vcefodaparabensfrozen2meuovomeuovinhoayylmaogordoquaseexploderindo'

async def parse_id(data, message=None):
    if data[0:2] == '<@':
        if data[2] == '!':
            return data[3:-1]
        else:
            return data[2:-1]
    else:
        logger.error("parse_id: %s", data)
        return None

def speak_filter(message):
    # remove URLs
    message = re.sub(r'https?:\/\/([\/\?\w\.\&\;\=\-])+', '', message)

    # remove numbers
    message = re.sub(r'\d+', '', message)

    # remove discord mentions
    message = re.sub(r'<@(\!)?\d+>', '', message)

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
    def __init__(self, cid, func, sec):
        self.func = func
        self.sec = sec
        self.run = False
        self.cid = cid
        self.last_run = None

    async def do(self):
        logger.info("%s: Running Callback", self.cid)
        while self.run:
            logger.debug("%s: called", self.cid)

            try:
                self.last_run = time.time()
                await self.func()
            except:
                logger.error('Error at cbk %s.do', self.cid, exc_info=True)

            await asyncio.sleep(self.sec)
        logger.debug("%s: ended", self.cid)

    def stop(self):
        self.run = False

    def start(self):
        self.run = True

async def run_callback(callback_id, callback):
    if callback_id in callbacks:
        return None

    callbacks[callback_id] = callback
    callback.start()
    await callback.do()
    return True

async def cbk_call(callback_id):
    if callback_id not in callbacks:
        return None

    callback = callbacks[callback_id]
    res = await callback.func()
    return res

async def cbk_remove(callback_id):
    if callback_id not in callbacks:
        return None

    callback = callbacks[callback_id]
    callback.stop()
    del callbacks[callback_id]
    return True

# === DATABASE API ===

conn = None
JOSE_DATABASE_PATH = "jose.db"

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
    global conn
    cur = conn.cursor()
    cur.execute(stmt, params)
    conn.commit()
    return cur

class DatabaseAPI:
    def __init__(self, _client):
        self.client = _client

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

class Extension:
    def __init__(self, _client):
        '''
        Extension - A general extension used by josé

        The Extension class defines the API for josé's modules,
        all modules inherit from this class.
        '''
        self.client = _client
        self.loop = client.loop
        self.logger = logger.getChild('Extension')

        self._callbacks = {}
        self._databases = {}
        self.dbapi = DatabaseAPI(self.client)

        self.cbk_new('jsondb:save_all', self.jsondb_save_all, 1200)

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

    def codeblock(self, lang, string):
        return "```%s\n%s```" % (lang, string)

    def noasync(self, func, args):
        return asyncio.ensure_future(func(*args), loop=self.loop)

    def cbk_new(self, callback_id, func, timer_sec):
        logger.info("New callback %s every %d seconds", callback_id, timer_sec)

        self._callbacks[callback_id] = Callback(callback_id, func, timer_sec)

        status = self.noasync(run_callback, [callback_id, \
            self._callbacks[callback_id]])

        if status is None:
            logger.error("Error happened in callback %s", callback_id)

        logger.info("Callback %s finished", callback_id)

    async def cbk_call(self, callback_id):
        status = await cbk_call(callback_id)
        if status is None:
            logger.error("Error calling callback %s", callback_id)
            return
        logger.info("called callback %s", callback_id)

    def cbk_remove(self, callback_id):
        status = self.noasync(cbk_remove, [callback_id])
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
        if database_id in self._databases:
            return None

        database_path = kwargs.get('path')
        attribute = kwargs.get('watch', database_id)
        default_file = kwargs.get('default', '{}')

        self._databases[database_id] = {
            'attr': attribute,
            'path': database_path,
            'default': default_file,
        }

        setattr(self, attribute, {})

        if not os.path.isfile(database_path):
            with open(database_path, 'w') as dbfile:
                dbfile.write(default_file)

        setattr(self, attribute, json.load(open(database_path, 'r')))

    def jsondb_save(self, database_id):
        if database_id not in self._databases:
            return None

        database = self._databases[database_id]
        attribute = database['attr']
        database_path = database['path']

        try:
            json.dump(getattr(self, attribute), open(database_path, 'w'))
        except:
            return False

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
        'language': 'en',

        # TODO: use them????
        'imgchannel': 'None',
        'prefix': JOSE_PREFIX,
        'speak_prob': 0,
    }

redis = None

def make_rkey(server_id):
    return 'config:{0}'.format(server_id)

async def r_configdb_raw_load():
    global redis
    loop = asyncio.get_event_loop()
    redis = await aioredis.create_redis(('localhost', 6379), loop=loop)
    status = await redis.ping()
    status = status.decode('utf-8')
    if status == 'PONG':
        return True
    return False

async def r_configdb_ensure(server_id):
    rediskey = make_rkey(server_id)
    exists = await redis.exists(rediskey)

    if not exists:
        default_cdb = get_defaultcdb()

        res = await redis.hmset_dict(rediskey, default_cdb)
        if not res:
            logger.error("Error creating configdb for server %s", rediskey)

async def r_configdb_ensure_key(server_id, key, default):
    await r_configdb_ensure(server_id)

    exists = await redis.hexists(rediskey)
    if not exists:
        res = await redis.hmset(rediskey, key, default)
        if not res:
            logger.error("Error creating configdb for server %s", rediskey)


async def r_configdb_set(server_id, key, value):
    await r_configdb_ensure(server_id)
    rediskey = make_rkey(server_id)

    try:
        await redis.hmset(rediskey, key, value)
        after = await redis.hmget(rediskey, key)
        if after != value:
            logger.warning("[r_cdb] configdb_set(%s, %s) = %s != %s", sid, key, value, after)
    except Exception as err:
        logger.error('configdb_set(%s, %s)', sid, key, exc_info=True)
        return False

async def r_configdb_get(server_id, key):
    await r_configdb_ensure(server_id)
    rediskey = 'config:{0}'.format(server_id)
    res = await redis.hmget(rediskey, key)
    return res

async def r_save_configdb():
    logger.info("savedb:r_config")
    try:
        # don't use aioredis, use subprocess
        out = subprocess.check_output('redis-cli save', shell=True)
        if not out.startswith('OK'):
            logger.warning("[r_save_configdb] error saving")

        return True, ''
    except Exception as err:
        return False, repr(err)

async def r_load_configdb():
    logger.info("load_db:r_config")
    try:
        res = await r_configdb_raw_load()
        if not res:
            return False, 'raw_load sent false'

        # ensure new configdb features
        keys = await redis.keys('*')
        for rediskey in keys:
            if rediskey.startswith('config:'):
                server_id = rediskey.split(':')[1]
                r_configdb_ensure_key(server_id, 'speak_prob', 0)

        await r_save_configdb()

        return True, ''
    except Exception as err:
        return False, repr(err)

async def configdb_set(sid, key, value):
    global configdb
    if sid not in configdb:
        configdb[sid] = get_defaultcdb()

    try:
        configdb[sid][key] = value
        res = configdb[sid][key]
        if res != value:
            logger.warning("configdb_set(%s, %s) = %s didn't went through", sid, key, value)
            return False

        return True
    except Exception as err:
        logger.error('configdb_set(%s, %s)', sid, key, exc_info=True)
        return False

async def configdb_get(sid, key, defaultval=None):
    global configdb
    if sid not in configdb:
        configdb[sid] = get_defaultcdb()
    return configdb[sid].get(key)

# langdb stuff
async def langdb_set(sid, lang):
    await configdb_set(sid, 'language', lang)

async def langdb_get(sid):
    res = await configdb_get(sid, 'language', 'default')
    return res

async def save_configdb():
    global configdb
    logger.info("savedb:config")

    try:
        res = await r_save_configdb()
        if not res[0]:
            return False, res[1]

        json.dump(configdb, open(CONFIGDB_PATH, 'w'))
        return True, ''
    except Exception as err:
        return False, repr(err)

def cdb_ensure(serverid, entry, default):
    cdb = configdb[serverid]

    if entry not in cdb:
        cdb[entry] = default

async def load_configdb():
    global configdb
    if not os.path.isfile(CONFIGDB_PATH):
        # recreate
        logger.info("Recreating config database")
        with open(CONFIGDB_PATH, 'w') as rawconfig_db:
            rawconfig_db.write('{}')

    sanity_save = False
    logger.info("load:config")
    try:
        res = await r_load_configdb()
        if not res[0]:
            return False, res[1]

        configdb = json.load(open(CONFIGDB_PATH, 'r'))

        # ensure new configdb features
        for serverid in configdb:
            cdb_ensure(serverid, 'speak_prob', 0)

        if sanity_save:
            await save_configdb()

        return True, ''
    except Exception as err:
        return False, repr(err)


async def get_translated(langid, string):
    lang = LANGUAGE_OBJECTS.get(langid, None)
    if lang is None:
        # fallback, just return the same string
        return string
    else:
        return lang.gettext(string)

class Context:
    def __init__(self, _client, message, t_creation=None, jose=None):
        if t_creation is None:
            t_creation = time.time()

        self.message = message
        self.client = _client
        self.t_creation = t_creation
        self.jose = jose
        self.env = {}

    async def send_typing(self):
        try:
            await self.client.send_typing(self.message.channel)
        except discord.Forbidden:
            server = self.message.server
            channel = self.message.channel
            logger.info("Context.send_typing: got err Forbidden from\
serverid %s servername %s chname #%s", server.id, server.name, channel.name)
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
            if configdb is None:
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
                    ret = await self.client.send_message(channel, translated)
                    return ret
            except discord.Forbidden:
                logger.info("discord.Forbidden: %r %r %r", channel, \
                    channel.server.id, channel.server.name)

class EmptyContext:
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

    async def getall(self):
        return '\n'.join(self.messages)
