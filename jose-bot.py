# -*- coding: utf-8 -*-
import discord

from random import SystemRandom
random = SystemRandom()

import asyncio
import requests
import sys
import os
import ast
import time
import subprocess
import pickle
from lxml import html
import json

import urllib.request
import urllib.parse
import re
from xml.etree import ElementTree

from josecommon import *
import josespeak as jspeak
import jcoin.josecoin as jcoin
import joseconfig as jconfig
import joseassembly as jasm

start_time = time.time()

#config
chattiness = .25
MASTER_ROLE = 'mestra'
LEARN_ROLE = 'cult'
jc_probabiblity = .12
JOSE_ANIMATION_LIMIT = 1 # 2 animações simultaneamente

#just for 0.6.6.6 and 6.6.6
DEMON_MODE = False

#default stuff
client = discord.Client()
set_client(client)

JOSE_NICK = 'jose-bot'
lil_message = ''
msmsg = ''
started = False
bank = None
MAINTENANCE_MODE = False
GAMBLING_MODE = False

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
def set_lilmsg(message):
    global lil_message
    d = message.content.split(' ')
    lil_message = ' '.join(d[1:])

    yield from client.send_message(message.channel, "lilmessage foi alterada para {}".format(lil_message))

@asyncio.coroutine
def show_lilmsg(message):
    yield from client.send_message(message.channel, "lilmessage: {}".format(lil_message))

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

@asyncio.coroutine
def set_msmsg(message):
    global msmsg

    args = message.content.split(' ')
    msmsg = ' '.join(args[1:])

    yield from client.send_message(message.channel, 'msmsg: %s' % msmsg)

@asyncio.coroutine
def show_msmsg(message):
    global msmsg
    yield from client.send_message(message.channel, msmsg)

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

@asyncio.coroutine
def convert_money(message):
    args = message.content.split(' ')
    amount = float(args[1])
    currency_from = args[2]
    currency_to = args[3]

    baseurl = "http://api.fixer.io/latest?base={}".format(currency_from.upper())
    data = requests.get(baseurl).json()
    if 'error' in data:
        yield from jose_debug(message, "!money error: %s" % data['error'])
        return

    rate = data['rates'][currency_to]
    res = amount * rate

    yield from client.send_message(message.channel, '{} {} = {} {}'.format(
        amount, currency_from, res, currency_to
    ))

# globals
ascii_to_wide = dict((i, chr(i + 0xfee0)) for i in range(0x21, 0x7f))
ascii_to_wide.update({0x20: u'\u3000', 0x2D: u'\u2212'})  # space and minus
wide_to_ascii = dict((i, chr(i - 0xfee0)) for i in range(0xff01, 0xff5f))
wide_to_ascii.update({0x3000: u' ', 0x2212: u'-'})        # space and minus

@asyncio.coroutine
def convert_fullwidth(message):
    args = message.content.split(' ')
    ascii_text = ' '.join(args[1:])

    res = ascii_text.translate(ascii_to_wide)
    yield from client.send_message(message.channel, res)

@asyncio.coroutine
def change_playing(message):
    args = message.content.split(' ')
    gameid = ' '.join(args[1:])

    g = discord.Game(name=gameid, url=gameid, type='game')
    yield from client.change_status(g)

@asyncio.coroutine
def show_uptime(message):
    global start_time
    sec = (time.time() - start_time)
    yield from jose_debug(message, "uptime: %.2fmin" % (sec/60.0))

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
        res = jspeak.genSentence(1, 50)
        if DEMON_MODE:
            res = res[::-1]
        yield from client.send_message(channel, res)

nsfw_hypnohub = make_xmlporn('http://hypnohub.net/post/index.xml')
nsfw_yandere = make_xmlporn('https://yande.re/post.xml')

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
    yield from client.send_message(message.channel, "texto inserido no data.txt!")
    return

@asyncio.coroutine
def nsfw_e621(message):
    res = yield from jcoin_control(message.author.id, PORN_PRICE)
    if not res[0]:
        yield from client.send_message(message.channel,
            "PermError: %s" % res[1])
        return

    args = message.content.split(' ')
    search_term = ' '.join(args[1:])

    if search_term == ':latest' or search_term == '' or search_term == ' ':
        yield from client.send_message(message.channel, 'getting latest post in e621')
        r = requests.get('https://e621.net/post/index.json?limit=%s' % PORN_LIMIT).json()
        try:
            post = random.choice(r)
            yield from client.send_message(message.channel, '%s' % post['sample_url'])
            return
        except Exception as e:
            yield from jose_debug(message, "erro em !e621: %s" % str(e))
            return

    else:
        yield from client.send_message(message.channel, 'searching for %r in e621' % search_term)
        r = requests.get('https://e621.net/post/index.json?limit=%s&tags=%s' % (PORN_LIMIT, search_term)).json()
        try:
            post = random.choice(r)
            yield from client.send_message(message.channel, '%s' % post['sample_url'])
            return
        except Exception as e:
            yield from jose_debug(message, "erro no !e621: provavelmente nada foi encontrado, seu merda. (%s)" % str(e))
            return

@asyncio.coroutine
def nsfw_porn(message):
    res = yield from jcoin_control(message.author.id, PORN_PRICE)
    if not res[0]:
        yield from client.send_message(message.channel,
            "PermError: %s" % res[1])
        return

    args = message.content.split(' ')
    search_term = ' '.join(args[1:])

    if search_term == ':latest' or search_term == '' or search_term == ' ':
        yield from client.send_message(message.channel, 'procurando posts')
        r = requests.get('http://api.porn.com/videos/find.json?limit=%s' % PORN_LIMIT).json()
        try:
            post = random.choice(r['result'])
            yield from client.send_message(message.channel, '%s' % post['url'])
            return
        except Exception as e:
            yield from jose_debug(message, "erro em !e621: %s" % str(e))
            return

    else:
        yield from client.send_message(message.channel, 'procurando por %r' % search_term)
        r = requests.get('http://api.porn.com/videos/find.json?limit=%s&tags=%s' % (PORN_LIMIT, search_term)).json()
        try:
            post = random.choice(r['result'])
            yield from client.send_message(message.channel, '%s' % post['url'])
            return
        except Exception as e:
            yield from jose_debug(message, "erro: provavelmente nada foi encontrado, seu merda. (%s)" % str(e))
            return

@asyncio.coroutine
def make_escolha(message):
    args = message.content.split(' ')
    escolhas = ' '.join(args[1:])
    escolhas = escolhas.split(';')
    choice = random.choice(escolhas)
    yield from client.send_message(message.channel, "Eu escolho %s" % choice)

def parse_id(data, message):
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
        yield from jose_debug(message, "error parsing id %s" % data)
        return

@asyncio.coroutine
def josecoin_new(message):
    print("new jcoin account %s" % message.author.id)

    res = jcoin.new_acc(message.author.id, str(message.author))
    if res[0]:
        yield from client.send_message(message.channel, res[1])
    else:
        yield from client.send_message(message.channel, 'erro: %s' % res[1])

@asyncio.coroutine
def josecoin_saldo(message):
    args = message.content.split(' ')

    id_check = None
    if len(args) < 2:
        id_check = message.author.id
    else:
        id_check = yield from parse_id(args[1], message)

    res = jcoin.get(id_check)
    if res[0]:
        accdata = res[1]
        yield from client.send_message(message.channel, '%s -> %.2f' % (accdata['name'], accdata['amount']))
    else:
        yield from client.send_message(message.channel, 'erro encontrando conta(id: %s)' % (id_check))

@asyncio.coroutine
def josecoin_write(message):
    if not check_roles(MASTER_ROLE, message.author.roles):
        yield from jose_debug(message, "PermissionError: sem permissão para alterar dados da JC")

    args = message.content.split(' ')

    id_from = yield from parse_id(args[1], message)
    new_amount = float(args[2])

    jcoin.data[id_from]['amount'] = new_amount
    yield from client.send_message(message.channel, jcoin.data[id_from]['amount'])

@asyncio.coroutine
def josecoin_send(message):
    args = message.content.split(' ')

    try:
        id_to = args[1]
        amount = float(args[2])

        id_from = message.author.id
        id_to = yield from parse_id(id_to, message)

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
                    yield from client.send_message(message.channel, "jc_aposta: aposta total de %.2f de <@%s>" % (val, id_from))
            return
        else:
            yield from client.send_message(message.channel, 'erro em jc: %s' % res[1])
    except Exception as e:
        yield from jose_debug(message, "jc_error: %s" % str(e))


@asyncio.coroutine
def josecoin_dbg(message):
    yield from client.send_message(message.channel, jcoin.data)

@asyncio.coroutine
def josecoin_save(message, dbg_flag=True):
    yield from jose_debug(message, "saving josecoin data", dbg_flag)
    res = jcoin.save('jcoin/josecoin.db')
    if not res[0]:
        yield from jose_debug(message, 'error: %r' % res, dbg_flag)

@asyncio.coroutine
def josecoin_load(message, dbg_flag=True):
    yield from jose_debug(message, "loading josecoin data", dbg_flag)
    res = jcoin.load('jcoin/josecoin.db')
    if not res[0]:
        yield from jose_debug(message, 'error: %r' % res, dbg_flag)

@asyncio.coroutine
def josecoin_top10(message):
    args = message.content.split(' ')
    jcdata = dict(jcoin.data)

    range_max = 11
    if len(args) > 1:
        range_max = int(args[1]) + 1

    res = 'Top %d pessoas que tem mais JC$\n' % (range_max - 1)
    maior = {
        'id': 0,
        'name': '',
        'amount': 0.0,
    }

    for i in range(1,range_max):
        if len(jcdata) < 1:
            break

        for accid in jcdata:
            acc = jcdata[accid]
            name, amount = acc['name'], acc['amount']
            if amount > maior['amount']:
                maior['id'] = accid
                maior['name'] = name
                maior['amount'] = amount

        del jcdata[maior['id']]
        res += '%d. %s -> %.2f\n' % (i, maior['name'], maior['amount'])

        # reset to next
        maior = {
            'id': 0,
            'name': '',
            'amount': 0.0,
        }

    yield from client.send_message(message.channel, res)

@asyncio.coroutine
def show_jenv(message):
    yield from client.send_message(message.channel, "`%r`" % jose_env)

@asyncio.coroutine
def change_nickname(message):
    global JOSE_NICK

    auth = yield from check_roles(MASTER_ROLE, message.author.roles)
    if not auth:
        yield from jose_debug(message, "PermissionError: Não pode mudar o nick do josé.")
        return

    args = message.content.split(' ')
    if len(args) < 2:
        JOSE_NICK = None
    JOSE_NICK = ' '.join(args[1:])

    for server in client.servers:
        m = server.get_member(jcoin.jose_id)
        yield from client.change_nickname(m, JOSE_NICK)

    return

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
def search_soundcloud(message):
    args = message.content.split(' ')
    query = ' '.join(args[1:])
    print("soundcloud -> %s" % query)

    if len(query) < 3:
        yield from client.send_message(message.channel, "preciso de mais coisas para pesquisar")
        return

    search_url = 'https://api.soundcloud.com/search?q=%s&facet=model&limit=10&offset=0&linked_partitioning=1&client_id='+jconfig.soundcloud_id

    url = search_url % query

    while url:
        response = requests.get(url)
        if response.status_code != 200:
            yield from jose_debug(message, "erro no !sndc: status code != 200")
            return
        try:
            doc = json.loads(response.text)
        except Exception as e:
            yield from jose_debug(message, "erro no !sndc: %s" % str(e))
            return

        for entity in doc['collection']:
            if entity['kind'] == 'track':
                yield from client.send_message(message.channel, entity['permalink_url'])
                return

        yield from client.send_message(message.channel, "verifique sua pesquisa, porque nenhuma track foi encontrada.")
        return

        url = doc.get('next_href')

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
        report += "<@%s> ganhou %.2fJC nessa aposta por ser o ganhador!" % (winner, P))
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

    yield from client.send_message(message.channel, "%s\nModo aposta desativado!" % (report))

    # clear everything
    jose_env['apostas'] = {}
    GAMBLING_MODE = False
    return

exact_commands = {
    'jose': show_help,
    'josé': show_help,
    'Jose': show_help,
    'José': show_help,
    '!help': show_help,
    'melhor bot': show_shit,
}

commands_start = {
    "!setmsmsg": set_msmsg,
    "!msmsg": show_msmsg,

    '!xingar': show_xingar,
    '!elogiar': show_elogio,
    '!cantar': show_cantada,

    '!yt': search_youtube,
    '!setlmsg': set_lilmsg,
    '!version': show_version,

    '!lilmsg': show_lilmsg,
    '!lmsg': show_lilmsg,

    '!log': show_debug,
    '!dbgmsg': new_debug,

    '!animate': make_animation,
    '!pisca': make_pisca,

    '!causar': make_causo,
    '!money': convert_money,
    '!fullwidth': convert_fullwidth,
    '!playing': change_playing,
    '!uptime': show_uptime,

    '!pesquisa': make_pesquisa,
    '!voto': make_voto,

    '!hypno': nsfw_hypnohub,
    '!e621': nsfw_e621,
    '!yandere': nsfw_yandere,
    '!porn': nsfw_porn,

    '!josetxt': show_josetxt,
    '!learn': learn_data,
    '!escolha': make_escolha,

    '!josecoin': help_josecoin,
    '!save': josecoin_save,
    '!load': josecoin_load,
    # '!jcdebug': josecoin_dbg,
    '!jcdata': josecoin_dbg,
    '!conta': josecoin_new,
    '!enviar': josecoin_send,
    '!saldo': josecoin_saldo,
    '!top10': josecoin_top10,
    '!write': josecoin_write,
    '!jenv': show_jenv,

    '!nick': change_nickname,
    '!ping': pong,
    '!xuxa': demon,
    'axux!': demon,
    '!emoji': rand_emoji,

    '!sndc': search_soundcloud,
    '!jasm': make_func(jasm.JASM_HELP_TEXT),
    '!construção': main_status,
    '!aposta': init_aposta,
    '!rolar': aposta_start,
    '!ahelp': show_gambling_full,
    '!adummy': show_gambling,
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
    'top': show_top,

    "se fude jose": show_vtnc,
    "jose se fude": show_vtnc,
    "vtnc jose": show_vtnc,
    'que rodeio': rodei_teu_cu,
    'anal giratorio': show_agira,

    'lenny face': make_func("( ͡° ͜ʖ ͡°)"),
    'janela': show_casa,
    'frozen3': make_func("https://thumbs.dreamstime.com/t/construo-refletiu-nas-janelas-do-prdio-de-escritrios-moderno-contra-47148949.jpg"),
    'q fita': make_func("http://i.imgur.com/DQ3YnI0.jpg"),
}

counter = 0

@client.event
@asyncio.coroutine
def on_message(message):
    global started
    global counter

    for user_id in list(jose_env['spamcl']):
        if time.time() > jose_env['spamcl'][user_id]:
            del jose_env['spamcl'][user_id]
            del jose_env['spam'][user_id]
            # yield from client.send_message(message.channel, "`%r`" % jose_env)
            yield from client.send_message(message.channel, "<@%s> : cooldown destruído" % user_id)

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    bnr = '%s(%r) : %s : %r' % (message.channel, message.channel.is_private, message.author, message.content)
    print(bnr)

    # TODO: log message

    if not started:
        started = True
        initmsg = "Bem vindo ao josé v%s b%d iniciou em %s" % (JOSE_VERSION, JOSE_BUILD, message.channel)
        if DEMON_MODE:
            yield from jose_debug(message, initmsg[::-1])
        else:
            yield from jose_debug(message, initmsg)
        yield from josecoin_load(message)
        return

    counter += 1
    if counter > 10:
        yield from josecoin_save(message, False)
        counter = 0

    if message.content == '!exit':
        try:
            auth = yield from check_roles(MASTER_ROLE, message.author.roles)
            if auth:
                yield from josecoin_save(message)
                yield from jose_debug(message, "saindo")
                yield from client.logout()
                sys.exit(0)
            else:
                yield from jose_debug(message, "PermError: sem permissão para desligar jose-bot")
        except Exception as e:
            yield from jose_debug(message, "ErroGeral: %s" % str(e))
        return

    elif message.content == '!reboot':
        try:
            auth = yield from check_roles(MASTER_ROLE, message.author.roles)
            if auth:
                yield from josecoin_save(message)
                yield from jose_debug(message, "reiniciando")
                yield from client.logout()
                os.system("./reload_jose.sh &")
                sys.exit(0)
            else:
                yield from jose_debug(message, "PermError: sem permissão para reiniciar jose-bot")
        except Exception as e:
            yield from jose_debug(message, "ErroGeral: %s" % str(e))
        return

    elif message.content == '!update':
        try:
            auth = yield from check_roles(MASTER_ROLE, message.author.roles)
            if auth:
                yield from josecoin_save(message)
                yield from jose_debug(message, "atualizando josé para nova versão(era v%s b%d)" % (JOSE_VERSION, JOSE_BUILD))
                yield from client.logout()
                os.system("./reload_jose.sh &")
                sys.exit(0)
            else:
                yield from jose_debug(message, "PermError: sem permissão para atualizar jose-bot")
        except Exception as e:
            yield from jose_debug(message, "ErroGeral: %s" % str(e))
        return

    elif message.content in exact_commands:
        if MAINTENANCE_MODE:
            yield from show_maintenance(message)
            return
        func = exact_commands[message.content]
        yield from func(message)
        return

    for command in commands_start:
        if message.content.startswith(command):
            if MAINTENANCE_MODE:
                yield from show_maintenance(message)
                return
            func = commands_start[command]
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

    if message.content.startswith("!xkcd"):
        k = message.content.split(' ')
        n = False
        if len(k) > 1:
            n = k[1]

        info_latest = info = requests.get("http://xkcd.com/info.0.json").json()
        info = None
        try:
            if not n:
                info = info_latest
            elif n == 'random' or n == 'r' or n == 'rand':
                rn_xkcd = random.randint(0, info_latest['num'])
                info = requests.get("http://xkcd.com/{0}/info.0.json".format(rn_xkcd)).json()
            else:
                info = requests.get("http://xkcd.com/{0}/info.0.json".format(n)).json()

            yield from client.send_message(message.channel, 'xkcd {} : {}'.format(n, info['img']))
        except ValueError as e:
            yield from client.send_message(message.channel, "ValueError: provavelmente deu merda baixando o info.0.json da sua comic, seu fdp.")
        except Exception as e:
            yield from client.send_message(message.channel, "ERRO: %s" % str(e))

        return

    elif message.content.startswith("!rand"):
        args = message.content.split()
        n_min, n_max = 0,0
        try:
            n_min = int(args[1])
            n_max = int(args[2])
        except:
            yield from jose_debug(message, "erro parseando os números para a função.")
            return

        if n_min > n_max:
            yield from jose_debug(message, "minimo > máximo, intervalo não permitido")
            return

        n_rand = random.randint(n_min, n_max)
        yield from client.send_message(message.channel, "Número aleatório de %d a %d: %d" % (n_min, n_max, n_rand))
        return

    elif message.content.startswith('$guess'):
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
                        yield from client.send_message(message.channel, 'spam detectado a @%s! cooldown de 5 minutos foi aplicado!' % message.author)
                        return
                    else:
                        return

                if MAINTENANCE_MODE:
                    return

                author_id = str(message.author.id)
                amount = random.choice([1, 1.2, 2, 2.5, 5, 5.1, 7.4])

                res = jcoin.transfer(jcoin.jose_id, author_id, amount, jcoin.LEDGER_PATH)
                yield from josecoin_save(message, False)
                if res[0]:
                    acc_to = jcoin.get(author_id)[1]
                    # yield from client.send_message(message.channel, res[1])
                    emoji_res = yield from random_emoji(3)
                    yield from client.send_message(message.channel, '%s %.2fJC > %s' % (emoji_res, amount, acc_to['name']))
                else:
                    yield from jose_debug(message, 'jc_error: %s' % res[1])
        else:
            yield from jose_debug(message, 'erro conseguindo JC$ para %s(canal %r) porquê você está em um canal privado.' % (message.author.id, message.channel))

    #else:
    #    yield from add_sentence(message)
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

jcoin.load(jconfig.jcoin_path)
jspeak.buildMapping(jspeak.wordlist('jose-data.txt'), 1)
client.run(jconfig.discord_token)
