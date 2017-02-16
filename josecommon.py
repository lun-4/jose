import asyncio
import time
import re
import json
import os
import sqlite3

import randemoji as emoji

from random import SystemRandom
random = SystemRandom()

import joseerror as je
import jplaying_phrases as playing_phrases

import logging

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


JOSE_PREFIX = "j!"
JOSE_VERSION = '1.3.6'

MARKOV_LENGTH_PATH = 'db/wordlength.json'
MARKOV_MESSAGES_PATH = 'db/messages.json'
STAT_DATABASE_PATH = 'db/stats.json'
LANGUAGES_PATH = 'db/languages.json'

JOSE_ID = '202587271679967232'
JOSE_APP_ID = '202586824013643777'
OAUTH_URL = 'https://discordapp.com/oauth2/authorize?client_id=%s&scope=bot&permissions=67259457' % JOSE_APP_ID

#configuration things
chattiness = .25
LEARN_ROLE = 'cult'
ADMIN_IDS = ['162819866682851329', '144377237997748224', '191334773744992256']

#just for 0.6.6.6 and 6.6.6 or any demon version
DEMON_MODE = False

#mode changes
MAINTENANCE_MODE = False
GAMBLING_MODE = False

JOSE_SPAM_TRIGGER = 4
PIRU_ACTIVITY = .000069
jc_probabiblity = .01
JC_REWARDS = [0, 0, 0.2, 0.6, 1, 1.2, 1.5]

PORN_LIMIT = 14
GAMBLING_FEE = 5 # 5 percent
TOTAL = 10.0
PORN_MEMBERS = 0.3
LEARN_MEMBERS = 1.0

# prices
'''
P = len_recompensas * (recompensa * prob) / TOTAL
'''
BASE_PRICE = 3 * ((len(JC_REWARDS) * (JC_REWARDS[len(JC_REWARDS)-1] * jc_probabiblity)) / TOTAL)

PORN_PRICE = (BASE_PRICE) * ((TOTAL-1.0) / PORN_MEMBERS)
LEARN_PRICE = (BASE_PRICE) * ((TOTAL-1.0) / LEARN_MEMBERS)
OP_TAX_PRICE = (BASE_PRICE) * ((TOTAL-1.0) / TOTAL)

PRICE_TABLE = {
    'porn': ("Comandos relacionados a pornografia", PORN_PRICE),
    'learn': ("Comandos relacionados ao josé aprender textos", LEARN_PRICE),
    'operational': ("Taxa operacional de alguns comandos(normalmente relacionados a muito processamento)", OP_TAX_PRICE)
}

PL_MIN_MINUTES = 2
PL_MAX_MINUTES = 7

ascii_to_wide = dict((i, chr(i + 0xfee0)) for i in range(0x21, 0x7f))
ascii_to_wide.update({0x20: u'\u3000', 0x2D: u'\u2212'})  # space and minus

client = None

def set_client(cl):
    global client
    client = cl

# Language database
langdb = None

# Phrases that will be shown randomly when jose starts
JOSE_PLAYING_PHRASES = playing_phrases.JOSE_PLAYING_PHRASES

WELCOME_MESSAGE = '''
Thanks for implementing José v{} into your server!
Jose is a bot that learns to speak based on conversations that happen in your server.
**See `j!docs josespeak` to learn more about this.**
To start off, you need to generate at least 100 messages, just talk and watch the magic happen!
When he's ready, you can use `j!speaktrigger` or `j!spt` to hear what he has to say.

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

GAMBLING_HELP_TEXT = '''O que é: Função que permite dois (ou mais) usuários apostarem josecoins por esporte.

Como funciona:
 * Primeiro, ativar o "modo aposta" do jose-bot com o comando: !aposta (qualquer um pode começar uma aposta)
 * jose-bot printa a mensagem "Modo aposta ativado. Joguem suas granas!" ou algo do tipo
 * Enquanto o "modo aposta" estiver ativado, qualquer um que !ap josecoins para o jose-bot entra na aposta, o jose-bot grava o nome da pessoa
temporariamente como se fosse um "acesso a memória RAM"
 * As apostas são cumulativas, ou seja, se uma mesma pessoa !enviar 20 e depois !enviar 40, é como se ela apostasse 60 josecoins de uma vez
 * Quando todos tiverem feito suas apostas, inserir o comando !rolar (ou outro nome sla), o que fará com que o jose-bot sorteie aleatoriamente uma pessoa com base na fórmula: n = 1/x (x sendo o número de pessoas que entraram na aposta)
 * A pessoa sorteada ganha a aposta, recebendo 76.54% do montante, e os outros apostadores ficam com o que sobrou, que será dividido igualmente.
 * Após o pagamento, o modo aposta se desativa automaticamente(editado)

Exemplo:
Número de apostadores = 3 (pessoas A, B e C, respectivamente)
Inserindo o comando ---> j!aposta
jose-bot printa: "Modo aposta ativado. Joguem suas granas!"
A pessoa A aposta 50 josecoins ---> j!ap 50
A pessoa B aposta 30 josecoins ---> j!ap 30
A pessoa C aposta 20 josecoins ---> j!ap 20
"Rolando o dado" ---> j!rolar

Cálculo do prêmio:
M = montante acumulado de todas as apostas
P = total de josecoins que o vencedor da aposta ganha
p = total de josecoins que cada um dos perdedores da aposta ganha
x = número de pessoas que entraram na aposta

P = M * 0.7654
p = M * 0.2346 / x
Pegando os valores anteriores, o montante é 50+30+20=100
A pessoa B ganhou a aposta, sendo assim ela ganha 76.54 josecoins, sobrando 23.46 josecoins.
Desses 23.46 josecoins, as pessoas A e C vão receber, cada uma, 11.73 josecoins.
'''

GAMBLING_HELP_TEXT_SMALL = '''Aposta for Dummies:
j!aposta - inicia modo de aposta do jose
j!ap <quantidade> - aposta propiamente dita
j!rolar - quando você já está pronto pra ver quem é o ganhador
'''

debug_logs = []

async def debug_log(string):
    logger.debug(string)
    today_str = time.strftime("%d-%m-%Y")
    with open("logs/jose_debug-%s.log" % today_str, 'a') as f:
        f.write(string+'\n')

async def jose_debug(message, dbg_msg, flag=True):
    message_banner = '%s[%s]: %r' % (message.author, message.channel, message.content)
    dbg_msg = '%s -> %s' % (message_banner, str(dbg_msg))
    debug_logs.append(dbg_msg)
    await debug_log('%s : %s' % (time.strftime("%d-%m-%Y %H:%M:%S"), dbg_msg))
    if flag:
        await client.send_message(message.channel, "jdebug: {}".format(dbg_msg))

cantadas = [
    'ô lá em casa',
    'vc é o feijão do meu acarajé',
    'gate, teu cu tem air bag?? pq meu pau tá sem freio',
    'se merda fosse beleza você estaria toda cagada',
    'me chama de bombeiro e deixa eu apagar seu fogo com a minha mangueira',
    'tô no hospital esperando uma doaçao de coração, pq vc roubou o meu',
    'me chama de piraque e vamos pra minha casa',
    'me chama de gorila e deixa eu te sarrar no ritmo do seu coração',
    'meu nome é arlindo, mas pode me chamar de lindo pq perdi o ar quando te vi',
    'me chama de lula e deixa eu roubar seu coração',
    'espero que o seu dia seja tão bom quanto sua bunda',
    'chama meu pau de Jean Willys e deixa ele cuspir na sua cara',
    'deixe eu ser a bala do seu Hamilton e acertar seu coração',
    'me chama de terrorista e deixa eu explodir dentro de você',
    'me chama de lava jato e me deixa te taxar de tão linde',
]

elogios = [
    "você é linde! <3",
    "sabia que você pode ser alguém na vida?",
    "eu acredito em você",
    'vc é FODA',
    'Parabéns',
]

xingamentos = [
    "Tu fica na merda",
    "Vai se fuder!",
    "pq colocou man",
    "MANO PQ",
    "vsf",
    "seu FILHO DA PUTA",
    "se fosse eu não deixava",
    "vai tomar no cu",
    'CABALO IMUNDO',
    'HIJO DE PUTA',
]

aviaos = [
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

async def show_gambling_full(message):
    await client.send_message(message.author, GAMBLING_HELP_TEXT)

async def show_gambling(message):
    await client.send_message(message.author, GAMBLING_HELP_TEXT_SMALL)

async def show_top(message):
    await client.send_message(message.channel, "BALADINHA TOPPER %s %s" % (
        (":joy:" * random.randint(1,5)),
        (":ok_hand:" * random.randint(1,6))))

async def check_roles(correct, rolelist):
    c = [role.name == correct for role in rolelist]
    return True in c

async def random_emoji(maxn):
    return ''.join((str(emoji.random_emoji()) for i in range(maxn)))

atividade = [
    'http://i.imgur.com/lkZVh3K.jpg',
    'http://imgur.com/a/KKwId',
    'http://imgur.com/a/ekrmK'
]

async def gorila_routine(ch):
    if random.random() < PIRU_ACTIVITY:
        await client.send_message(ch, random.choice(atividade))

def make_func(res):
    async def response(message):
        await client.send_message(message.channel, res)

    return response

rodei_teu_cu = make_func("RODEI MEU PAU NO TEU CU")
show_tampa = make_func("A DO TEU CU\nHÁ, TROLEI")
show_vtnc = make_func("OQ VC DISSE?\nhttp://i.imgur.com/Otky963.jpg")
show_shit = make_func("tbm amo vc humano <3")
show_emule = make_func("http://i.imgur.com/GO90sEv.png")
show_frozen_2 = make_func('http://i.imgur.com/HIcjyoW.jpg')

show_tijolo = make_func("http://www.ceramicabelem.com.br/produtos/TIJOLO%20DE%2006%20FUROS.%209X14X19.gif")
show_mc = make_func("https://cdn.discordapp.com/attachments/202055538773721099/203989039504687104/unknown.png")
show_vinheta = make_func('http://prntscr.com/bvcbju')
show_agira = make_func("http://docs.unity3d.com/uploads/Main/SL-DebugNormals.png")
show_casa = make_func("https://thumbs.dreamstime.com/z/locais-de-trabalho-em-um-escrit%C3%B3rio-panor%C3%A2mico-moderno-opini%C3%A3o-de-new-york-city-das-janelas-tabelas-pretas-e-cadeiras-de-couro-59272285.jpg")

meme_ratelimit = make_func("http://i.imgur.com/P6bDtR9.gif")
meme_dank_memes = make_func("http://i.imgur.com/Fzk4jfl.png")

async def str_xor(s,t):
    return "".join(chr(ord(a)^ord(b)) for a,b in zip(s,t))

JCRYPT_KEY = 'vcefodaparabensfrozen2meuovomeuovinhoayylmaogordoquaseexploderindo'

async def parse_id(data, message):
    '''
    <@196461455569059840>
    <@!162819866682851329>
    '''
    if data[0:2] == '<@':
        if data[2] == '!':
            return data[3:-1]
        else:
            return data[2:-1]
    else:
        await jose_debug(message, "error parsing id %s" % data)
        return

def speak_filter(message):
    filtered_message = ""

    # remove URLs
    message = re.sub(r'https?:\/\/([\/\?\w\.\&\;\=\-])+', '', message, flags=re.MULTILINE)

    # remove numbers
    message = re.sub(r'\d+', '', message)

    # remove discord mentions
    message = re.sub(r'<@(\!)?\d+>', '', message)

    i = 0
    while i < len(message):
        char = message[i]
        if char == '<':
            if i+1 > len(message):
                if message[i+1] == '@':
                    ending_tag = message.find('>', i+1)
                    if ending_tag == -1:
                        raise Exception("ending_tag == -1, wtf?")
                    i += ending_tag + 1
        elif char == ';':
            if i+1 < len(message):
                if message[i+1] == ';':
                    i += len(message)
        elif char == '!' and i == 0:
            #jose command, skip it
            i += len(message)
        else:
            filtered_message += char
        i += 1

    return filtered_message

# Callbacks

# one table to have the relationship ID => Function
callbacks = {}

class Callback:
    def __init__(self, cid, func, sec):
        self.func = func
        self.sec = sec
        self.run = False
        self.cid = cid

    async def do(self):
        logger.debug("%s: running", self.cid)
        while self.run:
            logger.debug("%s: called", self.cid)
            await self.func()
            await asyncio.sleep(self.sec)
        logger.debug("%s: ended", self.cid)

    def stop(self):
        self.run = False

    def start(self):
        self.run = True

async def run_callback(callback_id, c):
    if callback_id in callbacks:
        return None

    callbacks[callback_id] = c
    c.start()
    await c.do()
    return True

async def cbk_call(callback_id):
    if callback_id not in callbacks:
        return None

    c = callbacks[callback_id]
    res = await c.func()
    return res

async def cbk_remove(callback_id):
    if callback_id not in callbacks:
        return None

    c = callbacks[callback_id]
    c.stop()
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
    def __init__(self, cl):
        self.client = cl

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
    def __init__(self, cl):
        '''
        Extension - A general extension used by josé

        The Extension class defines the API for josé's modules, all modules inherit
        from this class.
        '''
        self.client = cl
        self.current = None
        self.loop = cl.loop
        self.logger = logger
        self._callbacks = {}
        self.dbapi = DatabaseAPI(self.client)

    async def say(self, msg, channel=None):
        if channel is None:
            channel = self.current.channel

        if len(msg) > 2000:
            await self.client.send_message(channel, ":elephant: Mensagem muito grande :elephant:")
        else:
            await self.client.send_message(channel, ":warning: This message is using a deprecated API!! :warning:")

    async def debug(self, msg, flag=True):
        await jose_debug(self.current, msg, flag)

    async def recv(self, msg):
        self.current = msg

    async def rolecheck(self, correct_role):
        c = [role.name == correct_role for role in self.current.author.roles]
        if not (True in c):
            raise je.PermissionError()
        else:
            return True

    async def is_admin(self, id):
        if id in ADMIN_IDS:
            return True
        else:
            raise je.PermissionError()

    async def brolecheck(self, correct_role):
        try:
            return (await self.rolecheck(correct_role))
        except je.PermissionError:
            return False

    async def b_isowner(self, cxt):
        return cxt.message.author.id in ADMIN_IDS

    def codeblock(self, lang, string):
        return "```%s\n%s```" % (lang, string)

    def noasync(self, func, args):
        return asyncio.ensure_future(func(*args), loop=self.loop)

    def is_owner(self):
        return self.current.id in ADMIN_IDS

    def cbk_new(self, callback_id, func, timer_sec):
        logger.info("New callback %s every %d seconds", callback_id, timer_sec)

        self._callbacks[callback_id] = Callback(callback_id, func, timer_sec)
        ok = self.noasync(run_callback, [callback_id, self._callbacks[callback_id]])
        if ok is None:
            logger.error("Error happened in callback %s", callback_id)

        logger.info("Callback %s finished", callback_id)

    async def cbk_call(self, callback_id):
        ok = await cbk_call(callback_id)
        if ok is None:
            logger.error("Error calling callback %s", callback_id)
            return
        logger.info("called callback %s", callback_id)

    def cbk_remove(self, callback_id):
        ok = self.noasync(cbk_remove, [callback_id])
        if ok is None:
            logger.error("Error removing callback %s", callback_id)
            return

        del self._callbacks[callback_id]
        logger.info("Callback %s removed", callback_id)

def parse_command(message):
    if not isinstance(message, str):
        message = message.content

    if message.startswith(JOSE_PREFIX):
        k = message.find(" ")
        command = message[len(JOSE_PREFIX):k]
        if k == -1:
            command = message[len(JOSE_PREFIX):]
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
        self.db = json.load(open(fpath, 'r'))

    def gettext(self, msgid):
        res = self.db.get(msgid, "")
        if len(res) == 0:
            return msgid
        else:
            return res

# initialize language object for each language
langobjects = {
    'en': LangObject(EN_LANGUAGE_PATH),
    'pt': LangObject(PT_LANGUAGE_PATH),
}

# langdb stuff
async def langdb_set(sid, lang):
    global langdb
    langdb[sid] = lang

async def langdb_get(sid):
    global langdb
    return langdb.get(sid, 'default')

async def save_langdb():
    global langdb
    logger.info("Saving language database")
    try:
        json.dump(langdb, open(LANGUAGES_PATH, 'w'))
    except Exception as e:
        return False, repr(e)

    return True, ''

async def load_langdb():
    global langdb
    if not os.path.isfile(LANGUAGES_PATH):
        # recreate
        logger.info("Recreating language database")
        with open(LANGUAGES_PATH, 'w') as f:
            f.write('{}')

    logger.info("Loading language database")
    try:
        langdb = json.load(open(LANGUAGES_PATH, 'r'))
    except Exception as e:
        return False, repr(e)

    return True, ''


async def get_translated(langid, string):
    lang = langobjects.get(langid, None)
    if lang is None:
        # fallback, just return the same string
        return string
    else:
        return lang.gettext(string)

class Context:
    def __init__(self, client, message, t_creation=None, jose=None):
        if t_creation is None:
            t_creation = time.time()

        self.message = message
        self.client = client
        self.t_creation = t_creation
        self.jose = jose

    async def say(self, string, _channel=None, tup=None):
        global langdb

        channel = None
        if isinstance(_channel, tuple):
            tup = _channel
            channel = self.message.channel
        else:
            channel = _channel

        if channel is None:
            channel = self.message.channel

        if len(string) > 2000:
            await self.client.send_message(channel, ":elephant: Mensagem muito grande :elephant:")
        else:
            if langdb is None:
                await logger.info("Loading language database @ cxt.say")
                await load_langdb()

            if self.message.server is not None:
                if self.message.server.id not in langdb:
                    await self.client.send_message(channel, \
                        ":warning: No Language has been defined for this server, use `!language` to set up :warning:")
            else:
                # in a DM
                ret = await self.client.send_message(channel, string)
                return ret

            # since 'default' doesn't exist in the language table
            # it will go back to fallback and just send the message already
            lang = await langdb_get(self.message.server.id)
            translated = await get_translated(lang, string)

            if tup is not None:
                translated = translated % tup

            try:
                ret = await self.client.send_message(channel, translated)
                return ret
            except discord.Forbidden:
                logger.info("discord.Forbidden: %r %r %r" % (channel, channel.server.id, channel.server.name))

class EmptyContext:
    def __init__(self, client, message):
        self.client = client
        self.message = message
        self.messages = []

    async def say(self, string, channel=None):
        self.messages.append(string)

    async def getall(self):
        return '\n'.join(self.messages)
