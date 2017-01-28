# -*- coding: utf-8 -*-
import asyncio
import sys
import os
import ast
import time
import re
import traceback
import logging
from random import SystemRandom
random = SystemRandom()

import discord

import ext.jose as jose_bot
import ext.joseassembly as jasm
from josecommon import *
import jcoin.josecoin as jcoin
import joseconfig as jconfig
import joseerror as je
from inspect import signature

logging.basicConfig(level=logging.INFO)

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

start_time = time.time()

#default stuff
client = discord.Client()
set_client(client) # to jcommon

# initialize jose instance
jose = jose_bot.JoseBot(client)

GAMBLING_LAST_BID = 0.0

#enviroment thingies
jose_env = jose.env
jasm_env = {}

if PARABENS_MODE:
    old_send = client.send_message

    async def newsend(ch, d):
        return old_send(ch, 'Parabéns %s' % d)

    client.send_message = newsend

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

async def jcoin_control(id_user, amnt):
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
        logger.debug("add_sentence: ignoring len(sd.strip) < 1")

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
        raise je.PermissionError()

async def show_maintenance(message):
    await jose.say("**JOSÉ EM CONSTRUÇÃO, AGUARDE**\nhttps://umasofe.files.wordpress.com/2012/11/placa.jpg")

async def show_price(message):
    res = ''

    for k in PRICE_TABLE:
        d = PRICE_TABLE[k]
        res += "categoria %r: %s > %.2f\n" % (k, d[0], d[1])

    await jose.say(res)
    return

show_pior_bot = make_func("me tree :christmas_tree: me spam :christmas_tree: no oxygen :christmas_tree:  if ban\n" * 4)

'''
    RMV : removed(or marked to remove)
    DEAC : deactivated until better solution
    MOV : moved to new protocol/anything else
'''

exact_commands = {
    'jose': show_help,
    'melhor bot': show_shit,
    'pior bot': show_pior_bot,
}

jcoin.load(jconfig.jcoin_path)
jc = jcoin.JoseCoin(client)

josecoin_save = jc.josecoin_save
josecoin_load = jc.josecoin_load

commands_start = {
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
# load_module('josemusic', 'JoseMusic')
load_module('josespeak', 'JoseSpeak')
load_module('josegambling', 'JoseGambling')
# load_module('josegames', 'JoseGames')
# load_module('josestrelinha', "JoseStrelinha")
load_module('josedatamosh', 'JoseDatamosh')
load_module('joseibc', 'JoseIBC')
load_module('josextra', 'joseXtra')
load_module('joseartif', 'JoseArtif')
load_module('josestats', 'JoseStats')
load_module('josemath', 'JoseMath')
load_module('josemagicword', 'JoseMagicWord')

help_helptext = """
`!help` - achar ajuda para outros comandos
`!help <comando>` - procura algum texto de ajuda para o comando dado
Exemplos: `!help help`, `!help pstatus`, `!help ap`, `!help wa`, etc.
"""

event_table = {
    # any message that is not a command
    "on_message": [],

    # any message, including commands
    "any_message": [],

    # TODO: called on discord.client.logout
    "logout": [],
}

for modname in jose.modules:
    module = jose.modules[modname]
    modinst = jose.modules[modname]['inst']

    for method in module['handlers']:
        if method.startswith("e_"):
            evname = method[method.find("_")+1:]
            logger.info("Register Event %s@%s:%s", method, modname, evname)
            if evname in event_table:
                handler = getattr(modinst, method)
                event_table[evname].append(handler)

# cmd_queue = WaitingQueue()

'''
@client.event
async def on_message(message):
    global cmd_queue
    await cmd_queue.push(message)
'''

@client.event
async def on_message(message):
    global jose
    global counter
    global help_helptext

    if message.content == '!construção': #override maintenance mode
        await main_status(message)
        return

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
                await jose_debug(message, "aid.jc: pyerr: ```%s```" % traceback.format_exc())

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    counter += 1
    if counter > 11:
        await josecoin_save(message, False)
        counter = 0

    st = time.time()

    await jose.recv(message) # at least

    # any_message event
    for handler in event_table['any_message']:
        await handler(message)

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
            await jose.recv(message) # default

            cmd_ht = 'help'
            try:
                if args[1] == 'help':
                    await jose.say(help_helptext)
                    return
                else:
                    cmd_ht = args[1]
            except:
                pass

            try:
                if cmd_ht == 'help':
                    await jose.say(help_helptext)
                    return

                jose_method = getattr(jose, 'c_%s' % cmd_ht)

                if jose_method is None:
                    await jose.say("%s: Command not found" % cmd_ht)
                    return

            except Exception as e:
                await jose.say("help.%s: %r" % (cmd_ht, e))
                return

            try:
                await jose.say(jose_method.__doc__)
            except Exception as e:
                await jose.say("error getting helptext for %s: %r" % (command, repr(e)))
            return

        try:
            if MAINTENANCE_MODE:
                await show_maintenance(message)
                return

            # call c_ bullshit
            try:
                jose_method = getattr(jose, method)
            except AttributeError:
                return

            # but first, repeat the recv steps
            await jose.mod_recv(message)
            try:
                sig = signature(jose_method)
                if len(sig.parameters) == 3:
                    await jose_method(message, args, jcommon.Context(message))
                else:
                    await jose_method(message, args)

            except je.PermissionError:
                await jose.say("permissão ¯\_(ツ)_/¯ 💠 ¯\_(ツ)_/¯ negada")
            except RuntimeError as e:
                await jose.say('jose: py_rt_err: %s' % repr(e))
            except je.LimitError:
                pass

            end = time.time()
            delta = end - st
            if delta > 13:
                await jose.say("Alguma coisa está demorando demais para responder(delta=%.4fs)..." % delta)

            return
        except Exception as e:
            await jose.say("jose: py_err: ```%s```" % traceback.format_exc())
            # return

    if message.content in exact_commands:
        if MAINTENANCE_MODE:
            await show_maintenance(message)
            return
        func = exact_commands[message.content]
        await func(message)
        return

    for command in commands_match:
        if command in message.content:
            if MAINTENANCE_MODE:
                await show_maintenance(message)
                return
            func = commands_match[command]
            await func(message)
            return

    if message.content.startswith('$jasm'):
        if MAINTENANCE_MODE:
            await show_maintenance(message)
            return
        await jose.say('Bem vindo ao REPL do JoseAssembly!\nPara sair, digite "exit"')

        if not (message.author.id in jasm_env):
            jasm_env[message.author.id] = jasm.empty_env()

        pointer = jasm_env[message.author.id]

        while True:
            data = await client.wait_for_message(author=message.author)
            if data.content == 'exit':
                await jose.say('saindo do REPL')
                break
            else:
                insts = await jasm.parse(data.content)
                res = await jasm.execute(insts, pointer)
                if res[0] == True:
                    if len(res[2]) < 1:
                        await jose.say("**debug: nenhum resultado**")
                    else:
                        await jose.say(res[2])
                else:
                    await jose_debug(message, "jasm error: %s" % res[2])
                pointer = res[1]
        return

    # a normal message, spy it
    if not message.author.bot:
        with open("zelao.txt", 'a') as f:
            f.write('%s\n' % speak_filter(message.content))

    # handle e_on_message
    for handler in event_table['on_message']:
        await handler(message)

    if random.random() < jc_probabiblity:
        if not message.channel.is_private:

            # only if author has account
            if str(message.author.id) in jcoin.data:
                # if it is on the wrong server, return
                logger.debug("%s %s", message.server.id, message.server.id != "271378126234320897")
                if message.server.id != "271378126234320897":
                    return

                if MAINTENANCE_MODE:
                    return

                author_id = str(message.author.id)
                amount = random.choice(JC_REWARDS)
                acc_to = jcoin.get(author_id)[1]

                if amount == 0:
                    await jose.say("0JC > %s" % (acc_to['name']))
                else:
                    res = jcoin.transfer(jcoin.jose_id, author_id, amount, jcoin.LEDGER_PATH)
                    await josecoin_save(message, False)
                    if res[0]:
                        emoji_res = await random_emoji(3)
                        await jose.say('%s %.2fJC > %s' % (emoji_res, amount, acc_to['name']))
                    else:
                        await jose_debug(message, 'jc_error: %s' % res[1])
        else:
            return

    await gorila_routine(message.channel)

'''
async def command_loop():
    while True:
        if cmd_queue.length > 0:
            msg = await cmd_queue.pop()
            if len(msg.content) > 0:
                await one_message(msg)
        else:
            await asyncio.sleep(0.001)
'''

@client.event
async def on_ready():
    print("="*25)
    logger.info("josé ready, name = %s, id = %s", client.user.name, client.user.id)
    print('='*25)


async def main_task():
    global client
    startupdelta = time.time() - jose.start_time
    logger.info("took %.2f seconds on startup", startupdelta)
    logger.info("José Starting")
    await client.start(jconfig.discord_token)

loop = asyncio.get_event_loop()
try:
    #asyncio.ensure_future(command_loop())

    print("main_task")
    loop.run_until_complete(main_task())
except:
    loop.run_until_complete(jose.unload_all())
    loop.run_until_complete(client.logout())
finally:
    loop.close()

logger.info("Exit")
