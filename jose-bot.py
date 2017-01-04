# -*- coding: utf-8 -*-
import asyncio
import sys
import os
import ast
import time
import subprocess
import re
import traceback
import logging
from random import SystemRandom
import cProfile
random = SystemRandom()

import discord

import ext.jose as jose_bot
import ext.joseassembly as jasm
from josecommon import *
import jcoin.josecoin as jcoin
import joseconfig as jconfig
import joseerror as je

logging.basicConfig(level=logging.INFO)

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

start_time = time.time()

#default stuff
client = discord.Client()
set_client(client) # to jcommon

# initialize jose instance
jose = jose_bot.JoseBot(client)

started = False
GAMBLING_LAST_BID = 0.0

#enviroment things
josescript_env = {}
jose_env = jose.env
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
    async def func(message):
        d = message.content.split(' ')
        user_use = d[1]

        new_message = random.choice(dict_messages)
        await jose.say(fmt.format(user_use, new_message))

    return func

show_xingar = make_something('{}, {}', xingamentos)
show_elogio = make_something('{}, {}', elogios)
show_cantada = make_something('Ei {}, {}', cantadas)

async def show_aerotrem(message):
    ch = discord.Object(id='206590341317394434')
    aviao = random.choice(aviaos)
    await client.send_message(ch, aviao)

async def new_debug(message):
    args = message.content.split(' ')
    dbg = ' '.join(args[1:])

    await jose_debug(message, dbg)

causos = [
    '{} foi no matinho com {}',
    '{} inventou de fumar com {} e deu merda',
]

async def make_causo(message):
    args = message.content.split(' ')
    x = args[1]
    y = args[2]

    causo = random.choice(causos)

    await jose.say(causo.format(x, y))

help_josecoin = make_func(jcoin.JOSECOIN_HELP_TEXT)

@asyncio.coroutine
def jcoin_control(id_user, amnt):
    '''
    returns True if user can access
    '''
    return jcoin.transfer(id_user, jcoin.jose_id, amnt, jcoin.LEDGER_PATH)

def sanitize_data(data):
    data = re.sub('<@!?([0-9]+)>', '', data)
    data = re.sub('<#!?([0-9]+)>', '', data)
    data = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', data)
    data = data.replace("@jose-bot", '')
    return data

async def add_sentence(content, author):
    data = content
    sd = sanitize_data(data)
    debug_log("write %r from %s" % (sd, author))
    if len(sd.strip()) > 1:
        with open('jose-data.txt', 'a') as f:
            f.write(sd+'\n')
    else:
        print("ignoring(len(sd.strip) < 1)")

async def learn_data(message):
    res = await jcoin_control(message.author.id, LEARN_PRICE)
    if not res[0]:
        await client.send_message(message.channel,
            "PermError: %s" % res[1])
        raise je.PermissionError()

    auth = await check_roles(LEARN_ROLE, message.author.roles)
    if not auth:
        await client.send_message(message.channel,
            "JCError: usuário não autorizado a usar o !learn")
        raise je.PermissionError()

    args = message.content.split(' ')
    data_to_learn = ' '.join(args[1:])
    await add_sentence(data_to_learn, message.author)
    feedback = 'texto inserido no jose-data.txt!\n'

    # quick'n'easy solution
    line_count = data_to_learn.count('\n')
    word_count = data_to_learn.count(' ')
    byte_count = len(data_to_learn)
    feedback += "%d linhas, %d palavras e %d bytes foram inseridos\n" % (line_count, word_count, byte_count)
    await jose.say(feedback)
    return

async def demon(message):
    if DEMON_MODE:
        await jose.say(random.choice(demon_videos))
    else:
        await jose.say("espere até que o modo demônio seja sumonado em momentos específicos.")

async def main_status(message):
    global MAINTENANCE_MODE
    auth = await check_roles(MASTER_ROLE, message.author.roles)
    if auth:
        MAINTENANCE_MODE = not MAINTENANCE_MODE
        await jose_debug(message, "Modo de construção: %s" % (MAINTENANCE_MODE))
    else:
        await jose_debug(message, "PermError: Não permitido alterar o status do jose")

async def show_maintenance(message):
    await jose.say("**JOSÉ EM CONSTRUÇÃO, AGUARDE**\nhttps://umasofe.files.wordpress.com/2012/11/placa.jpg")

async def show_price(message):
    res = ''

    for k in PRICE_TABLE:
        d = PRICE_TABLE[k]
        res += "categoria %r: %s > %.2f\n" % (k, d[0], d[1])

    await jose.say(res)
    return

'''
    RMV : removed(or marked to remove)
    DEAC : deactivated until better solution
    MOV : moved to new protocol/anything else
'''

exact_commands = {
    'jose': show_help,
    'melhor bot': show_shit,
}

jcoin.load(jconfig.jcoin_path)
jc = jcoin.JoseCoin(client)

josecoin_save = jc.josecoin_save
josecoin_load = jc.josecoin_load

commands_start = {
    '!xingar': show_xingar,
    '!elogiar': show_elogio,
    '!cantar': show_cantada,

    # '!dbgmsg': new_debug,

    '!causar': make_causo,

    '!learn': learn_data,

    '!josecoin': help_josecoin,
    '!save': josecoin_save,
    '!load': josecoin_load,

    '!ping': pong,
    '!xuxa': demon,
    'axux!': demon,

    '!jasm': make_func(jasm.JASM_HELP_TEXT),
    '!construção': main_status,

    '!ahelp': show_gambling_full,
    '!adummy': show_gambling,
    '!airport': show_aerotrem,

    '!awoo': make_func("https://cdn.discordapp.com/attachments/202055538773721099/257717450135568394/awooo.gif"),

    '!price': show_price,
}

commands_match = {
    'baladinha top': show_top,

    'que tampa': show_tampa,

    "me abraça, josé": show_noabraco,
    'tijolo': show_tijolo,
    "mc gorila": show_mc,
    'frozen 2': show_frozen_2,
    'emule': show_emule,
    'vinheta': show_vinheta,

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

def from_dict(f):
    async def a(m, args):
        await f(m)
    return a

for cmd in commands_start:
    setattr(jose, 'c_%s' % cmd[1:], from_dict(commands_start[cmd]))

jose.load_gext(jc, 'josecoin')

def load_module(n, n_cl):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(jose.load_ext(n, n_cl))

load_module('josensfw', 'JoseNSFW')
load_module('josememes', 'JoseMemes')
load_module('josemusic', 'JoseMusic')
load_module('josespeak', 'JoseSpeak')
load_module('josegambling', 'JoseGambling')
# load_module('josegames', 'JoseGames')
# load_module('josestrelinha', "JoseStrelinha")
load_module('josedatamosh', 'JoseDatamosh')
load_module('joseibc', 'JoseIBC')
load_module('josextra', 'joseXtra')

help_helptext = """
`!help` - achar ajuda para outros comandos
`!help comando` - procura algum texto de ajuda para o comando dado
Exemplos: `!help help`, `!help pstatus`, `!help ap`
"""

cmd_queue = WaitingQueue()

@client.event
async def on_message(message):
    global cmd_queue
    await cmd_queue.push(message)

@asyncio.coroutine
def one_message(message):
    global jose
    global started
    global counter
    global help_helptext

    if message.content == '!construção': #override maintenance mode
        yield from main_status(message)
        return

    for user_id in list(jose_env['spamcl']):
        if time.time() > jose_env['spamcl'][user_id]:
            del jose_env['spamcl'][user_id]
            del jose_env['spam'][user_id]
            yield from jose.say("<@%s> : cooldown destruído" % user_id)

    if jose.command_lock:
        return

    if message.author.id in jcoin.data:
        if hasattr(message.author, 'nick'):
            if message.author.nick is not None:
                jcoin.data[message.author.id]['name'] = message.author.nick
            else:
                jcoin.data[message.author.id]['name'] = str(message.author)
        else:
            try:
                jcoin.data[message.author.id]['name'] = message.author.name
            except Exception as e:
                yield from jose_debug(message, "aid.jc: pyerr: ```%s```" % traceback.format_exc())

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # log stuff
    bnr = '%s(%r) : %s : %r' % (message.channel, message.channel.is_private, message.author, message.content)
    print(bnr)

    if not started:
        started = True
        initmsg = "josé %s iniciou em %s" % (JOSE_VERSION, message.channel)
        if DEMON_MODE:
            initmsg = initmsg[::-1]
        elif PARABENS_MODE:
            initmsg = "Parabéns %s" % initmsg

        yield from jose_debug(message, initmsg)
        yield from josecoin_load(message, False)
        return

    counter += 1
    if counter > 11:
        yield from josecoin_save(message, False)
        counter = 0

    st = time.time()

    yield from jose.recv(message) # at least

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
        method = "c_%s" % command

        if command == 'help':
            # load helptext
            yield from jose.recv(message) # default

            cmd_ht = 'help'
            try:
                if args[1] == 'help':
                    yield from jose.say(help_helptext)
                    return
                else:
                    cmd_ht = args[1]
            except:
                pass

            try:
                if cmd_ht == 'help':
                    yield from jose.say(help_helptext)
                    return
                jose_method = getattr(jose, 'c_%s' % cmd_ht)
            except Exception as e:
                yield from jose.say("%s: %r" % (command, e))
                return

            try:
                yield from jose.say(jose_method.__doc__)
            except Exception as e:
                yield from jose.say(repr(e))
            return

        try:
            if MAINTENANCE_MODE:
                yield from show_maintenance(message)
                return

            # call c_ bullshit
            try:
                jose_method = getattr(jose, method)
            except AttributeError:
                return

            # but first, repeat the recv steps
            yield from jose.mod_recv(message)
            try:
                yield from jose_method(message, args)

            except je.PermissionError:
                yield from jose.say("permissão ¯\_(ツ)_/¯ 💠 ¯\_(ツ)_/¯ negada")
            except RuntimeError:
                yield from jose.say('jose: py_rt_err: %s' % repr(e))
            except je.LimitError:
                pass

            end = time.time()
            delta = end-st
            if delta > 10:
                yield from jose.say("Alguma coisa está demorando demais para responder(delta=%.4fs)..." % delta)

            # yield from jose.unlock()

            # yield from jose.say("time: real %.4fs user %.4fs" % (delta, delta+(delta/4)))
            return
        except Exception as e:
            yield from jose.say("jose: py_err: ```%s```" % traceback.format_exc())
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

    if message.content.startswith('$jasm'):
        if MAINTENANCE_MODE:
            yield from show_maintenance(message)
            return
        yield from jose.say('Bem vindo ao REPL do JoseAssembly!\nPara sair, digite "exit"')

        if not (message.author.id in jasm_env):
            jasm_env[message.author.id] = jasm.empty_env()

        pointer = jasm_env[message.author.id]

        while True:
            data = yield from client.wait_for_message(author=message.author)
            if data.content == 'exit':
                yield from jose.say('saindo do REPL')
                break
            else:
                insts = yield from jasm.parse(data.content)
                res = yield from jasm.execute(insts, pointer)
                if res[0] == True:
                    if len(res[2]) < 1:
                        yield from jose.say("**debug: nenhum resultado**")
                    else:
                        yield from jose.say(res[2])
                else:
                    yield from jose_debug(message, "jasm error: %s" % res[2])
                pointer = res[1]
        return

    # a normal message, spy it
    if not message.author.bot:
        with open("zelao.txt", 'a') as f:
            f.write('%s\n' % speak_filter(message.content))

    if random.random() < jc_probabiblity:
        if not message.channel.is_private:
            if not message.author.id in jose_env['spam']:
                jose_env['spam'][message.author.id] = 0

            if str(message.author.id) in jcoin.data:
                jose_env['spam'][message.author.id] += 1
                if jose_env['spam'][message.author.id] >= JOSE_SPAM_TRIGGER:

                    # set timeout of user
                    if not message.author.id in jose_env['spamcl']:
                        jose_env['spamcl'][message.author.id] = time.time() + 300
                        yield from jose.say('@%s recebe cooldown de 5 minutos!' % message.author)
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
                    emoji_res = yield from random_emoji(3)
                    if PARABENS_MODE:
                        yield from jose.say("Parabéns")
                    else:
                        yield from jose.say('%s %.2fJC > %s' % (emoji_res, amount, acc_to['name']))
                else:
                    yield from jose_debug(message, 'jc_error: %s' % res[1])
        else:
            return

    yield from gorila_routine(message.channel)

async def command_loop():
    while True:
        if cmd_queue.length > 0:
            msg = await cmd_queue.pop()
            if len(msg.content) > 0:
                await one_message(msg)
        else:
            await asyncio.sleep(0.001)

@client.event
async def on_ready():
    print("="*25)
    print('josé ready:')
    print('name', client.user.name)
    print('id', client.user.id)
    print('='*25)


async def main_task():
    global client

    print("start")
    await client.start(jconfig.discord_token)

loop = asyncio.get_event_loop()
try:
    print("iniciando loop de processamento")
    asyncio.ensure_future(command_loop())

    print("main_task")
    loop.run_until_complete(main_task())
except:
    loop.run_until_complete(client.logout())
finally:
    loop.close()

print("jose: exit")
