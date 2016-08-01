# -*- coding: utf-8 -*-
import discord
import cProfile

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

# import ext.josemusic as jmusic
import ext.jose as jose_bot
import ext.joseassembly as jasm

from random import SystemRandom
random = SystemRandom()

import asyncio
import sys
import os
import ast
import time
import subprocess

import re

from josecommon import *
import josespeak as jspeak
import jcoin.josecoin as jcoin
import joseconfig as jconfig

start_time = time.time()

#default stuff
client = discord.Client()
set_client(client)

JOSE_NICK = 'jose-bot'
lil_message = ''
msmsg = ''
started = False
bank = None
GAMBLING_LAST_BID = 0.0

#enviroment things
josescript_env = {}
jose_env = {
    'survey': {},
    'spam': {},
    'spamcl': {},
    'apostas': {},
}
survey_id = 0
jasm_env = {}

if PARABENS_MODE:
    old_send = client.send_message

    @asyncio.coroutine
    def newsend(ch, d):
        return old_send(ch, 'Parabéns %s' % d)

    client.send_message = newsend

# !pesquisa 1 Qual o melhor mensageiro:discord,skype,teamspeak,raidcall

def make_something(fmt, dict_messages):
    @asyncio.coroutine
    def func(message):
        d = message.content.split(' ')
        user_use = d[1]

        new_message = random.choice(dict_messages)
        yield from client.send_message(message.channel, fmt.format(user_use, new_message))

    return func

show_xingar = make_something('{}, {}', xingamentos)
show_elogio = make_something('{}, {}', elogios)
show_cantada = make_something('Ei {}, {}', cantadas)

@asyncio.coroutine
def show_aerotrem(message):
    ch = discord.Object(id='206590341317394434')
    aviao = random.choice(aviaos)
    yield from client.send_message(ch, aviao)

@asyncio.coroutine
def show_debug(message):
    res = ''
    for (index, debug_msg) in enumerate(debug_logs):
        res += "log[{}]: {}\n".format(index, debug_msg)
    yield from client.send_message(message.channel, res)

@asyncio.coroutine
def new_debug(message):
    args = message.content.split(' ')
    dbg = ' '.join(args[1:])

    yield from jose_debug(message, dbg)

@asyncio.coroutine
def josescript_eval(message):
    if not message.author in josescript_env:
        josescript_env[message.author] = {
            'vars': {
                'jose_version': JOSE_VERSION,
            }
        }

    env = josescript_env[message.author]
    # yield from jose_debug(message, "env %s : %s" % (message.author, repr(env)))
    for line in message.content.split('\n'):
        for command in line.split(';'):
            if command == ']help':
                yield from jose_debug(message, JOSESCRIPT_HELP_TEXT)
            elif command.find('=') != -1:
                d = command.split('=')
                name = d[0]
                value = d[1]
                yield from jose_debug(message, "jsr: set %s to %s" % (name, value))
                env['vars'][name] = value
            elif command[:2] == ('g '):
                var_name = command[2:]
                var_val = None
                try:
                    var_val = env['vars'][var_name]
                    yield from jose_debug(message, "jsr: %s" % var_val)
                except KeyError:
                    yield from jose_debug(message, "jsr: variável %s não encontrada" % var_name)
                except Exception as e:
                    yield from jose_debug(message, "error: %s" % str(e))
            elif command == 'pv':
                res = ''
                for key in env['vars']:
                    res += '%s -> %s\n' % (key, env['vars'][key])
                yield from jose_debug(message, res)
            else:
                yield from jose_debug(message, "jsr: erro identificando comando")

animation_counter = 0

@asyncio.coroutine
def make_pisca(message):
    global animation_counter
    if animation_counter > JOSE_ANIMATION_LIMIT:
        yield from jose_debug(message, "FilaError: espere até alguma animação terminar")
        return

    animation_counter += 1

    args = message.content.split(' ')
    animate = ' '.join(args[1:])

    animate_banner = animate
    animate_msg = yield from client.send_message(message.channel, animate_banner)

    for i in range(20):
        if i%2 == 0:
            animate_banner = '**%s**' % animate
        else:
            animate_banner = '%s' % animate

        yield from client.edit_message(animate_msg, animate_banner)
        time.sleep(.5)

    animation_counter -= 1

@asyncio.coroutine
def make_animation(message):
    global animation_counter
    if animation_counter > JOSE_ANIMATION_LIMIT:
        yield from jose_debug(message, "FilaError: espere até alguma animação terminar")
        return

    animation_counter += 1

    args = message.content.split(' ')
    animate = ' '.join(args[1:])

    animate_banner = ' '*(20) + animate + ' '*(10)
    animate_msg = yield from client.send_message(message.channel, animate_banner)

    for i in range(20):
        animate_banner = ' '*(10-i) + animate + ' '*(10+i)
        yield from client.edit_message(animate_msg, animate_banner)
        time.sleep(.1)

    animation_counter -= 1

causos = [
    '{} foi no matinho com {}',
    '{} inventou de fumar com {} e deu merda',
]

@asyncio.coroutine
def make_causo(message):
    args = message.content.split(' ')
    x = args[1]
    y = args[2]

    causo = random.choice(causos)

    yield from client.send_message(message.channel, causo.format(x, y))

help_josecoin = make_func(jcoin.JOSECOIN_HELP_TEXT)
josecoin_save = lambda x,y: None
josecoin_load = lambda x,y: None

@asyncio.coroutine
def jcoin_control(id_user, amnt):
    '''
    returns True if user can access
    '''
    return jcoin.transfer(id_user, jcoin.jose_id, amnt, jcoin.LEDGER_PATH)

@asyncio.coroutine
def show_uptime(message):
    global start_time
    sec = (time.time() - start_time)
    MINUTE  = 60
    HOUR    = MINUTE * 60
    DAY     = HOUR * 24

    days    = int( sec / DAY )
    hours   = int( ( sec % DAY ) / HOUR )
    minutes = int( ( sec % HOUR ) / MINUTE )
    seconds = int( sec % MINUTE )

    fmt = "jose: uptime: %d dias, %d horas, %d minutos, %d segundos"
    yield from jose_debug(message, fmt % (days, hours, minutes, seconds))

@asyncio.coroutine
def make_pesquisa(message):
    global survey_id
    # nome:op1,op2,op3...
    c = len("!pesquisa ")
    survey_type = 1
    try:
        survey_type = int(message.content[c:c+1])
    except:
        yield from jose_debug(message,
            "erro parseando tipo de pesquisa")
    survey_data = message.content[c+2:]

    sp = survey_data.split(':')
    if len(sp) != 2:
        yield from jose_debug(message, "Erro parseando comando: len(%r) != 2" % sp)
        return
    survey_name = sp[0]
    survey_options = sp[1].split(',')

    survey_id += 1
    jose_env['survey'][survey_id] = {
        'name': survey_name,
        'opt': survey_options,
        'votes': {},
        'author': message.author,
    }

    for opt in survey_options:
        jose_env['survey'][survey_id]['votes'][opt] = 0

    yield from jose_debug(message,
        "Nova pesquisa de %s feita por %s" % (survey_name, message.author))

    yield from jose_debug(message,
        "opções: %r" % (survey_options))

@asyncio.coroutine
def make_voto(message):
    args = message.content.split(' ')
    cmd = args[1]

    survey_id = -1
    try:
        survey_id = int(args[2])
    except:
        pass

    vote = None
    try:
        vote = args[3]
    except:
        pass

    all_surveys = jose_env['survey']

    if cmd == 'list':
        if survey_id in all_surveys:
            #list one survey
            survey = all_surveys[survey_id]
            res = ''

            res += ' * %s\n' % survey['name']
            for iop, op in enumerate(survey['opt']):
                res += '\t * opção %d. %s\n' % (iop, op)

            yield from client.send_message(message.author, res)
            return
        else:
            #list all
            res = ''

            for k in all_surveys:
                res += ' * %d -> %s' % (k, all_surveys[k]['name'])
                res += '\n'

            yield from client.send_message(message.author, res)
            return

    elif cmd == 'vote':
        if survey_id in jose_env['survey']:
            yield from jose_debug(message, "%r" % all_surveys[survey_id]['votes'])
            try:
                survey = all_surveys[survey_id]
                opt = survey['opt'][int(vote)]
                survey['votes'][opt] += 1
            except Exception as e:
                yield from jose_debug(message, "erro processando voto: %s" % str(e))
                return

            yield from jose_debug(message, "%r" % all_surveys[survey_id]['votes'])
            yield from jose_debug(message, 'voto contado com sucesso!')
            return
        else:
            yield from jose_debug(message, "Pesquisa não encontrada.")
            return

    elif cmd == 'close':
        if survey_id in jose_env['survey']:
            survey = jose_env['survey'][survey_id]
            if message.author == survey['author']:
                yield from jose_debug(message, "Pesquisa \"%s\" apagada com sucesso." % survey['name'])

                res = ''
                res += ' Resultados para %s\n' % survey['name']
                for iop, op in enumerate(survey['opt']):
                    res += '\t * votos para %d - %s = %d\n' % (iop, op, survey['votes'][op])

                yield from jose_debug(message, res)

                survey = None
                return
            else:
                yield from jose_debug(message, "PermError: sem permissão para fechar a pesquisa")
                return
        else:
            yield from jose_debug(message, "Pesquisa não encontrada.")
            return

def sanitize_data(data):
    data = re.sub('<@!?([0-9]+)>', '', data)
    data = re.sub('<#!?([0-9]+)>', '', data)
    data = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', data)
    data = data.replace("@jose-bot", '')
    return data

@asyncio.coroutine
def add_sentence(content, author):
    data = content
    sd = sanitize_data(data)
    debug_log("write %r from %s" % (sd, author))
    if len(sd.strip()) > 1:
        with open('jose-data.txt', 'a') as f:
            f.write(sd+'\n')
    else:
        print("ignoring(len(sd.strip) < 1)")

@asyncio.coroutine
def speak_routine(channel, run=False):
    if (random.random() < chattiness) or run:
        res = jspeak.genSentence(1, 100)
        if DEMON_MODE:
            res = res[::-1]
        elif PARABENS_MODE:
            res = 'Parabéns %s' % res
        yield from client.send_message(channel, res)

@asyncio.coroutine
def show_josetxt(message):
    output = subprocess.Popen(['wc', '-l', 'jose-data.txt'], stdout=subprocess.PIPE).communicate()[0]
    yield from client.send_message(message.channel, output)

@asyncio.coroutine
def learn_data(message):
    res = yield from jcoin_control(message.author.id, LEARN_PRICE)
    if not res[0]:
        yield from client.send_message(message.channel,
            "PermError: %s" % res[1])
        return

    auth = yield from check_roles(LEARN_ROLE, message.author.roles)
    if not auth:
        yield from client.send_message(message.channel,
            "JCError: usuário não autorizado a usar o !learn")
        return

    args = message.content.split(' ')
    data_to_learn = ' '.join(args[1:])
    yield from add_sentence(data_to_learn, message.author)
    feedback = 'texto inserido no jose-data.txt!\n'

    # quick'n'easy solution
    line_count = data_to_learn.count('\n')
    word_count = data_to_learn.count(' ')
    byte_count = len(data_to_learn)
    feedback += "%d linhas, %d palavras e %d bytes foram inseridos\n" % (line_count, word_count, byte_count)
    yield from client.send_message(message.channel, feedback)
    return

@asyncio.coroutine
def josecoin_send(message):
    global GAMBLING_LAST_BID
    args = message.content.split(' ')

    try:
        id_to = args[1]
        amount = float(args[2])

        id_from = message.author.id
        id_to = yield from parse_id(id_to, message)

        fee_amount = amount * (GAMBLING_FEE/100.)
        atleast = (amount + fee_amount)

        if GAMBLING_MODE:
            a = jcoin.get(id_from)[1]
            if a['amount'] <= atleast:
                yield from client.send_message(message.channel, "sua conta não possui fundos suficientes para apostar(%.2fJC são necessários, você tem %.2fJC, faltam %.2fJC)" % (atleast, a['amount'], atleast - a['amount']))
                return

            if amount < GAMBLING_LAST_BID:
                yield from client.send_message(message.channel, "sua aposta tem que ser maior do que a última, que foi %.2fJC" % GAMBLING_LAST_BID)
                return

        res = ''
        if GAMBLING_MODE:
            res = jcoin.transfer(id_from, id_to, atleast, jcoin.LEDGER_PATH)
        else:
            res = jcoin.transfer(id_from, id_to, amount, jcoin.LEDGER_PATH)
        yield from josecoin_save(message, False)
        if res[0]:
            yield from client.send_message(message.channel, res[1])
            if GAMBLING_MODE:
                if id_to == jcoin.jose_id:
                    # use jenv
                    if not id_from in jose_env['apostas']:
                        jose_env['apostas'][id_from] = 0

                    jose_env['apostas'][id_from] += amount
                    val = jose_env['apostas'][id_from]
                    GAMBLING_LAST_BID = amount
                    yield from client.send_message(message.channel, "jc_aposta: aposta total de %.2f de <@%s>" % (val, id_from))
            return
        else:
            yield from client.send_message(message.channel, 'erro em jc: %s' % res[1])
    except Exception as e:
        yield from jose_debug(message, "py_error: %s" % str(e))


@asyncio.coroutine
def josecoin_dbg(message):
    yield from client.send_message(message.channel, jcoin.data)

@asyncio.coroutine
def show_jenv(message):
    yield from client.send_message(message.channel, "`%r`" % jose_env)

@asyncio.coroutine
def demon(message):
    if DEMON_MODE:
        yield from client.send_message(message.channel, random.choice(demon_videos))
    else:
        yield from client.send_message(message.channel, "espere até que o modo demônio seja sumonado em momentos específicos.")

@asyncio.coroutine
def rand_emoji(message):
    res = yield from random_emoji(random.randint(1,5))
    yield from client.send_message(message.channel, "%s" % res)

@asyncio.coroutine
def main_status(message):
    global MAINTENANCE_MODE
    auth = yield from check_roles(MASTER_ROLE, message.author.roles)
    if auth:
        MAINTENANCE_MODE = not MAINTENANCE_MODE
        yield from jose_debug(message, "Modo de construção: %s" % (MAINTENANCE_MODE))
    else:
        yield from jose_debug(message, "PermError: Não permitido alterar o status do jose")

@asyncio.coroutine
def show_maintenance(message):
    yield from client.send_message(message.channel, "==JOSÉ EM CONSTRUÇÃO, AGUARDE==\nhttps://umasofe.files.wordpress.com/2012/11/placa.jpg")

@asyncio.coroutine
def init_aposta(message):
    global GAMBLING_MODE
    if message.channel.is_private:
        yield from client.send_message(message.channel, "Nenhum canal privado é autorizado a iniciar apostas")
        return

    if not GAMBLING_MODE:
        GAMBLING_MODE = True
        yield from client.send_message(message.channel, "Modo aposta ativado, mandem seus JC$!")
        return
    else:
        yield from client.send_message(message.channel, "Modo aposta já foi ativado.")
        return

@asyncio.coroutine
def aposta_start(message):
    global GAMBLING_MODE
    global GAMBLING_LAST_BID
    PORCENTAGEM_GANHADOR = 76.54
    PORCENTAGEM_OUTROS = 100 - PORCENTAGEM_GANHADOR

    PORCENTAGEM_GANHADOR /= 100
    PORCENTAGEM_OUTROS /= 100

    K = list(jose_env['apostas'].keys())
    if len(K) < 2:
        yield from client.send_message(message.channel, "Nenhuma aposta com mais de 1 jogador foi feita, modo aposta desativado.")
        GAMBLING_MODE = False
        return
    winner = random.choice(K)

    M = sum(jose_env['apostas'].values()) # total
    apostadores = len(jose_env['apostas'])-1 # remove one because of the winner
    P = (M * PORCENTAGEM_GANHADOR)
    p = (M * PORCENTAGEM_OUTROS) / apostadores

    report = ''

    res = jcoin.transfer(jcoin.jose_id, winner, P, jcoin.LEDGER_PATH)
    if res[0]:
        report += "<@%s> ganhou %.2fJC nessa aposta por ser o ganhador!\n" % (winner, P)
    else:
        yield from jose_debug(message, "erro no jc_aposta->jcoin: %s" % res[1])
        yield from jose_debug(message, "aposta abortada.")
        return

    del jose_env['apostas'][winner]

    # going well...
    for apostador in jose_env['apostas']:
        res = jcoin.transfer(jcoin.jose_id, apostador, p, jcoin.LEDGER_PATH)
        if res[0]:
            report += "<@%s> ganhou %.2fJC nessa aposta!\n" % (apostador, p)
        else:
            yield from jose_debug(message, "erro no jc_aposta->jcoin: %s" % res[1])
            yield from jose_debug(message, "aposta abortada.")
            return

    yield from client.send_message(message.channel, "%s\nModo aposta desativado!\nhttp://i.imgur.com/huUlJhR.jpg" % (report))

    # clear everything
    jose_env['apostas'] = {}
    GAMBLING_MODE = False
    GAMBLING_LAST_BID = 0.0
    return

@asyncio.coroutine
def aposta_report(message):
    res = ''
    total = 0.0
    for apostador in jose_env['apostas']:
        res += '<@%s> apostou %.2fJC\n' % (apostador, jose_env['apostas'][apostador])
        total += jose_env['apostas'][apostador]
    res += 'Total apostado: %.2fJC' % (total)
    yield from client.send_message(message.channel, res)
    return

@asyncio.coroutine
def show_price(message):
    res = ''

    for k in PRICE_TABLE:
        d = PRICE_TABLE[k]
        res += "categoria %r: %s > %.2f\n" % (k, d[0], d[1])

    yield from client.send_message(message.channel, res)
    return

exact_commands = {
    'jose': show_help,
    '!help': show_help,
    'melhor bot': show_shit,
}

'''
    RMV : removed
    DEAC : deactivated until better solution
'''

commands_start = {
    '!xingar': show_xingar,
    '!elogiar': show_elogio,
    '!cantar': show_cantada,
    '!version': show_version,

    '!log': show_debug,
    '!dbgmsg': new_debug,

    # DEAC '!animate': make_animation,
    '!pisca': make_pisca,

    '!causar': make_causo,
    '!uptime': show_uptime,

    # DEAC '!pesquisa': make_pesquisa,
    # DEAC '!voto': make_voto,

    # DEAC '!hypno': nsfw_hypnohub,
    # DEAC '!e621': nsfw_e621,
    # DEAC '!yandere': nsfw_yandere,
    # DEAC '!porn': nsfw_porn,

    '!josetxt': show_josetxt,
    '!learn': learn_data,

    '!josecoin': help_josecoin,
    '!save': josecoin_save,
    '!load': josecoin_load,
    # '!jcdebug': josecoin_dbg,
    '!jcdata': josecoin_dbg,
    '!enviar': josecoin_send,
    # RMV '!saldo': josecoin_saldo,
    '!jenv': show_jenv,

    '!ping': pong,
    '!xuxa': demon,
    'axux!': demon,
    '!emoji': rand_emoji,

    '!jasm': make_func(jasm.JASM_HELP_TEXT),
    '!construção': main_status,

    '!aposta': init_aposta,
    '!rolar': aposta_start,
    '!ahelp': show_gambling_full,
    '!adummy': show_gambling,
    '!areport': aposta_report,
    '!airport': show_aerotrem,

    '!awoo': make_func("https://images-2.discordapp.net/.eJwVyEEOwiAQAMC_8ABgEdi2nzGEIsW0LmHXeDD-vfUyh_mq99jVojaRzosxa-NMY9UsNFItuhLVvaTeWGc6TBJJeTvKS9g4e3M--BmiB8QJcLoqRnAWg50RA4TgTPoQ3f-0Ryusn72q3wkG3CWg.CTrgww5nr8mw_Fkm0BcEsEGV8t0.jpg"),
    '!Parabéns': make_func("http://puu.sh/qcSLD/f82b7f48c3.png"),
    '!vtnc': make_func("vai toma no cu 2"),
    '!sigabem': make_func("SIGA BEM CAMINHONEIRO"),

    '!price': show_price,
    '!htgeral': make_func(JOSE_GENERAL_HTEXT),
    '!htech': make_func(JOSE_TECH_HTEXT),
}

commands_match = {
    'baladinha top': show_top,
    'BALADINHA TOP': show_top,

    'que tampa': show_tampa,

    "me abraça, josé": show_noabraco,
    'tijolo': show_tijolo,
    "mc gorila": show_mc,
    'frozen 2': show_frozen_2,
    'emule': show_emule,
    'vinheta': show_vinheta,

    "se fude jose": show_vtnc,
    "jose se fude": show_vtnc,
    "vtnc jose": show_vtnc,
    'que rodeio': rodei_teu_cu,
    'anal giratorio': show_agira,

    'lenny face': make_func("( ͡° ͜ʖ ͡°)"),
    'janela': show_casa,
    'frozen3': make_func("https://thumbs.dreamstime.com/t/construo-refletiu-nas-janelas-do-prdio-de-escritrios-moderno-contra-47148949.jpg"),
    'q fita': make_func("http://i.imgur.com/DQ3YnI0.jpg"),
    'compiuter': make_func("https://i.ytimg.com/vi/cU3330gwoh8/hqdefault.jpg\nhttp://puu.sh/qcVi0/04d58f422d.JPG"),
}

counter = 0

jose = jose_bot.JoseBot(client)
#commands_start.update(jmusic.cmds_start)
#jmusic.jm.client = client

def from_dict(f):
    def a(m, args):
        yield from f(m)
    return a

for cmd in commands_start:
    setattr(jose, 'c_%s' % cmd[1:], from_dict(commands_start[cmd]))

jcoin.load(jconfig.jcoin_path)
jc = jcoin.JoseCoin(client)

josecoin_save = jc.josecoin_save
josecoin_load = jc.josecoin_load

# jn = jnsfw.JoseNSFW(client)
jose.load_gext(jc, 'josecoin')

def load_module(n, n_cl):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(jose.load_ext(n, n_cl))

load_module('josensfw', 'JoseNSFW')
load_module('josememes', 'JoseMemes')
load_module('josemusic', 'JoseMusic')

print("carregando jspeak")
jspeak.buildMapping(jspeak.wordlist('jose-data.txt'), 1)
print("jspeak carregado")

@client.event
@asyncio.coroutine
def on_message(message):
    global jose
    global started
    global counter
    global debug_channel

    if message.content == '!construção': #override maintenance mode
        yield from main_status(message)
        return

    for user_id in list(jose_env['spamcl']):
        if time.time() > jose_env['spamcl'][user_id]:
            del jose_env['spamcl'][user_id]
            del jose_env['spam'][user_id]
            yield from client.send_message(message.channel, "<@%s> : cooldown destruído" % user_id)

    if message.author.id in jcoin.data:
        if message.author.nick != None:
            jcoin.data[message.author.id]['name'] = message.author.nick
        else:
            try:
                jcoin.data[message.author.id]['name'] = message.author.name
            except Exception as e:
                yield from jose_debug(message, "nc: pyerr: %s" % e)

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # log stuff
    bnr = '%s(%r) : %s : %r' % (message.channel, message.channel.is_private, message.author, message.content)
    print(bnr)
    yield from client.send_message(debug_channel, bnr)

    if not started:
        started = True
        initmsg = "josé v%s b%d iniciou em %s" % (JOSE_VERSION, JOSE_BUILD, message.channel)
        if DEMON_MODE:
            yield from jose_debug(message, initmsg[::-1])
        elif PARABENS_MODE:
            yield from jose_debug(message, "Parabéns %s" % initmsg)
        else:
            yield from jose_debug(message, initmsg)
        yield from josecoin_load(message)
        return

    counter += 1
    if counter > 11:
        yield from josecoin_save(message, False)
        counter = 0

    st = time.time()
    # get command and push it to jose
    if message.content[0] == '!':
        #parse command
        #rules:
        # !{command} {args...}
        k = message.content.find(" ")
        command = message.content[1:k]
        if k == -1:
            command = message.content[1:]
        args = message.content.split(' ')
        try:
            method = "c_%s" % command
            # yield from jose.say("comando: %s" % method)
            # yield from jose.say(str(getattr(jose, method)))
            yield from jose.recv(message) # default
            for mod in jose.modules:
                mod_obj = jose.modules[mod]
                yield from mod_obj['inst'].recv(message)

            if MAINTENANCE_MODE:
                yield from show_maintenance(message)
                return

            # call c_ bullshit
            try:
                jose_method = getattr(jose, method)
            except AttributeError:
                return
            yield from jose_method(message, args)
            end = time.time()
            yield from jose.say("time: real %.4fs user %.4fs" % (end-st, 0.78131+end-st))
            return
        except Exception as e:
            yield from jose.say("jose: pyerr: %s" % e)
            # return

    if message.content in exact_commands:
        if MAINTENANCE_MODE:
            yield from show_maintenance(message)
            return
        func = exact_commands[message.content]
        yield from func(message)
        return

    for command in commands_match:
        if command in message.content:
            if MAINTENANCE_MODE:
                yield from show_maintenance(message)
                return
            func = commands_match[command]
            yield from func(message)
            return

    if message.content.startswith('$guess'):
        yield from client.send_message(message.channel, 'Me fale um número de 0 a 10, imundo.')

        def guess_check(m):
            return m.content.isdigit()

        guess = yield from client.wait_for_message(timeout=5.0, author=message.author, check=guess_check)
        answer = random.randint(1, 10)
        if guess is None:
            fmt = 'Demorou demais, era {}.'
            yield from client.send_message(message.channel, fmt.format(answer))
            return
        if int(guess.content) == answer:
            yield from client.send_message(message.channel, 'Acertô miseravi!')
        else:
            yield from client.send_message(message.channel, 'Errou filho da puta, era {}.'.format(answer))
        return

    elif message.content.startswith('$repl'):
        yield from client.send_message(message.channel, 'Fale um comando python(15 segundos de timeout)')

        data = yield from client.wait_for_message(timeout=15.0, author=message.author)

        if data is None:
            yield from client.send_message(message.channel, 'demorou demais')
            return

        try:
            res = ast.literal_eval(str(data.content))
            yield from client.send_message(message.channel, 'eval: %r' % res)
        except:
            yield from jose_debug(message, "erro dando eval na expressão dada")
        return

    elif message.content.startswith('$josescript'):
        if MAINTENANCE_MODE:
            yield from show_maintenance(message)
            return
        yield from client.send_message(message.channel, 'Bem vindo ao REPL do JoseScript!\nPara sair, digite "exit"')

        while True:
            data = yield from client.wait_for_message(author=message.author)
            if data.content == 'exit':
                yield from client.send_message(message.channel, 'saindo do REPL')
                break
            else:
                yield from josescript_eval(data)
                # yield from client.send_message(message.channel, 'eval: %s' % )
        return

    elif message.content.startswith('$jasm'):
        if MAINTENANCE_MODE:
            yield from show_maintenance(message)
            return
        yield from client.send_message(message.channel, 'Bem vindo ao REPL do JoseAssembly!\nPara sair, digite "exit"')

        if not (message.author.id in jasm_env):
            jasm_env[message.author.id] = jasm.empty_env()

        pointer = jasm_env[message.author.id]

        while True:
            data = yield from client.wait_for_message(author=message.author)
            if data.content == 'exit':
                yield from client.send_message(message.channel, 'saindo do REPL')
                break
            else:
                insts = yield from jasm.parse(data.content)
                res = yield from jasm.execute(insts, pointer)
                if res[0] == True:
                    if len(res[2]) < 1:
                        yield from client.send_message(message.channel, "**debug: nenhum resultado**")
                    else:
                        yield from client.send_message(message.channel, res[2])
                else:
                    yield from jose_debug(message, "jasm error: %s" % res[2])
                pointer = res[1]
                # yield from client.send_message(message.channel, 'eval: %s' % )
        return

    elif "<@202587271679967232>" in message.content: #mention
        yield from speak_routine(message.channel, True)

    elif random.random() < jc_probabiblity:
        if not message.channel.is_private:
            if not message.author.id in jose_env['spam']:
                jose_env['spam'][message.author.id] = 0

            if str(message.author.id) in jcoin.data:
                jose_env['spam'][message.author.id] += 1
                if jose_env['spam'][message.author.id] >= JOSE_SPAM_TRIGGER:

                    # set timeout of user
                    if not message.author.id in jose_env['spamcl']:
                        jose_env['spamcl'][message.author.id] = time.time() + 300
                        yield from client.send_message(message.channel, 'spam de @%s! cooldown de 5 minutos foi aplicado!' % message.author)
                        return
                    else:
                        return

                if MAINTENANCE_MODE:
                    return

                author_id = str(message.author.id)
                amount = random.choice(JC_REWARDS)

                res = jcoin.transfer(jcoin.jose_id, author_id, amount, jcoin.LEDGER_PATH)
                yield from josecoin_save(message, False)
                if res[0]:
                    acc_to = jcoin.get(author_id)[1]
                    # yield from client.send_message(message.channel, res[1])
                    emoji_res = yield from random_emoji(3)
                    if PARABENS_MODE:
                        yield from client.send_message(message.channel, "Parabéns")
                    else:
                        yield from client.send_message(message.channel, '%s %.2fJC > %s' % (emoji_res, amount, acc_to['name']))
                else:
                    yield from jose_debug(message, 'jc_error: %s' % res[1])
        else:
            yield from jose_debug(message, 'erro conseguindo JC$ para %s(canal %r) porquê você está em um canal privado.' % (message.author.id, message.channel))

        yield from speak_routine(message.channel)
        yield from gorila_routine(message.channel)

@client.event
@asyncio.coroutine
def on_ready():
    print("="*25)
    print('josé pronto:')
    print('name', client.user.name)
    print('id', client.user.id)
    print('='*25)

print("rodando cliente")
client.run(jconfig.discord_token)
print("jose: finish line")
