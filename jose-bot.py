# -*- coding: utf-8 -*-
import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# profiling
from pympler import tracker

import time
import re
import traceback
import logging
from random import SystemRandom
random = SystemRandom()

import discord

import josecommon as jcommon
import ext.jose as jose_bot
import ext.joseassembly as jasm
import jcoin.josecoin as jcoin
import joseconfig as jconfig
import joseerror as je
from inspect import signature

logging.basicConfig(level=logging.INFO)

start_time = time.time()

#default stuff
client = discord.Client()
jcommon.set_client(client) # to jcommon

# initialize jose instance
jose = jose_bot.JoseBot(client)

GAMBLING_LAST_BID = 0.0

# JASM enviroment
jasm_env = {}

help_josecoin = jcommon.make_func(jcoin.JOSECOIN_HELP_TEXT)

async def jcoin_control(id_user, amnt):
    '''
    returns True if user can access
    '''
    return jcoin.transfer(id_user, jcoin.jose_id, amnt, jcoin.LEDGER_PATH)

def sanitize_data(data):
    data = re.sub(r'<@!?([0-9]+)>', '', data)
    data = re.sub(r'<#!?([0-9]+)>', '', data)
    data = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', data)
    data = data.replace("@jose-bot", '')
    return data

async def add_sentence(content, author):
    data = content
    sd = sanitize_data(data)
    jcommon.logger.debug("write %r from %s" % (sd, author))
    if len(sd.strip()) > 1:
        with open('jose-data.txt', 'a') as f:
            f.write(sd+'\n')
    else:
        jcommon.logger.debug("add_sentence: ignoring len(sd.strip) < 1")

async def learn_data(message):
    res = await jcoin_control(message.author.id, jcommon.LEARN_PRICE)
    if not res[0]:
        await client.send_message(message.channel,
            "PermError: %s" % res[1])
        raise je.PermissionError()

    auth = await jcommon.check_roles(jcommon.LEARN_ROLE, message.author.roles)
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

async def main_status(message):
    auth = await jcommon.check_roles(jcommon.MASTER_ROLE, message.author.roles)
    if auth:
        jcommon.MAINTENANCE_MODE = not jcommon.MAINTENANCE_MODE
        await jcommon.jose_debug(message, "Modo de construção: %s" % (jcommon.MAINTENANCE_MODE))
    else:
        raise je.PermissionError()

async def show_maintenance(message):
    await jose.say("**JOSÉ EM CONSTRUÇÃO, AGUARDE**\nhttps://umasofe.files.wordpress.com/2012/11/placa.jpg")

async def show_price(message):
    res = ''

    for k in jcommon.PRICE_TABLE:
        d = jcommon.PRICE_TABLE[k]
        res += "categoria %r: %s > %.2f\n" % (k, d[0], d[1])

    await jose.say(res)
    return

show_pior_bot = jcommon.make_func("me tree :christmas_tree: me spam :christmas_tree: no oxygen :christmas_tree:  if ban\n" * 4)

'''
    RMV : removed(or marked to remove)
    DEAC : deactivated until better solution
    MOV : moved to new protocol/anything else
'''

exact_commands = {
    'melhor bot': jcommon.show_shit,
    'pior bot': show_pior_bot,
}

jcoin.load(jconfig.jcoin_path)
jc = jcoin.JoseCoin(client)

josecoin_save = jc.josecoin_save
josecoin_load = jc.josecoin_load

commands_start = {
    '!learn': learn_data,
    '!ahelp': jcommon.show_gambling_full,
    '!adummy': jcommon.show_gambling,
    '!awoo': jcommon.make_func("https://cdn.discordapp.com/attachments/202055538773721099/257717450135568394/awooo.gif"),
    '!price': show_price,
}

commands_match = {
    'baladinha top':    jcommon.show_top,
    'que tampa':        jcommon.show_tampa,
    'tijolo':           jcommon.show_tijolo,
    "mc gorila":        jcommon.show_mc,
    'frozen 2':         jcommon.show_frozen_2,
    'emule':            jcommon.show_emule,
    'vinheta':          jcommon.show_vinheta,
    "vtnc jose":        jcommon.show_vtnc,
    'que rodeio':       jcommon.rodei_teu_cu,
    'anal giratorio':   jcommon.show_agira,
    'lenny face':       jcommon.make_func("( ͡° ͜ʖ ͡°)"),
    'janela':           jcommon.show_casa,
    'frozen3':          jcommon.make_func("https://thumbs.dreamstime.com/t/construo-refletiu-nas-janelas-do-prdio-de-escritrios-moderno-contra-47148949.jpg"),
    'q fita':           jcommon.make_func("http://i.imgur.com/DQ3YnI0.jpg"),
    'compiuter':        jcommon.make_func("https://i.ytimg.com/vi/cU3330gwoh8/hqdefault.jpg\nhttp://puu.sh/qcVi0/04d58f422d.JPG"),
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
    t_start = time.time()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(jose.load_ext(n, n_cl, None))

    time_taken_ms = (time.time() - t_start) * 1000
    jcommon.logger.info("%s took %.3fms", n, time_taken_ms)

# essential stuff
load_module('joselang', 'JoseLanguage')
load_module('josespeak', 'JoseSpeak')
load_module('josestats', 'JoseStats')
load_module('josemagicword', 'JoseMagicWord')

# fun stuff
load_module('josememes', 'JoseMemes')
load_module('josensfw', 'JoseNSFW')
load_module('josedatamosh', 'JoseDatamosh')
load_module('josextra', 'joseXtra')
load_module('josegambling', 'JoseGambling')

# etc
load_module('joseibc', 'JoseIBC')
load_module('joseartif', 'JoseArtif')
load_module('josemath', 'JoseMath')

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

# register events
for modname in jose.modules:
    module = jose.modules[modname]
    modinst = jose.modules[modname]['inst']

    for method in module['handlers']:
        if method.startswith("e_"):
            evname = method[method.find("_")+1:]
            jcommon.logger.info("Register Event %s@%s:%s", \
                method, modname, evname)

            # check if event exists
            if evname in event_table:
                handler = getattr(modinst, method, None)
                if handler is None:
                    # ????
                    jcommon.logger.error("Event handler %s@%s:%s doesn't... exist????", \
                        method, modname, evname)
                    sys.exit(0)

                event_table[evname].append(handler)
            else:
                jcommon.logger.warning("Event %s@%s:%s doesn't exist in Event Table", \
                    method, modname, evname)

async def do_event(event_name, message):
    for handler in event_table[event_name]:
        cxt = jcommon.Context(client, message, time.time(), jose)
        await handler(message, cxt)

async def check_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return False

    # override maintenance mode
    if message.content == '!construção':
        await main_status(message)
        return False

    if jose.command_lock:
        return False

    if len(message.content) <= 0:
        return False

    return True

async def do_command_table(message):
    if message.content in exact_commands:
        func = exact_commands[message.content]
        await func(message)
        return True

    for command in commands_match:
        if command in message.content:
            func = commands_match[command]
            await func(message)
            return True

    return False

async def do_jasm(message, cxt):
    await cxt.say('Bem vindo ao REPL do JoseAssembly!\nPara sair, digite "exit"')

    if not (message.author.id in jasm_env):
        jasm_env[message.author.id] = jasm.empty_env()

    pointer = jasm_env[message.author.id]

    while True:
        data = await client.wait_for_message(author=message.author)
        if data.content == 'exit':
            await cxt.say('saindo do REPL')
            break
        else:
            insts = await jasm.parse(data.content)
            res = await jasm.execute(insts, pointer)
            if res[0] == True:
                if len(res[2]) < 1:
                    await cxt.say("**debug: nenhum resultado**")
                else:
                    await cxt.say(res[2])
            else:
                await cxt.say("jasm error: %s" % res[2])
            pointer = res[1]
    return

@client.event
async def on_message(message):
    global jose
    global counter

    t_start = time.time()

    is_good = await check_message(message)
    if not is_good:
        return

    if message.author.id in jcoin.data:
        jcoin.data[message.author.id]['name'] = str(message.author)

    counter += 1
    if counter > 11:
        await josecoin_save(message, False)
        counter = 0

    st = time.time()

    await jose.recv(message) # at least

    # any_message event
    await do_event('any_message', message)

    # get command and push it to jose
    if message.content.startswith(jcommon.JOSE_PREFIX):
        # use jcommon.parse_command
        command, args, method = jcommon.parse_command(message)

        cxt = jcommon.Context(client, message, t_start, jose)

        if command == 'help':
            # load helptext
            await jose.recv(message) # default

            cmd_ht = 'help'
            try:
                if args[1] == 'help':
                    await cxt.say(help_helptext)
                    return
                else:
                    cmd_ht = args[1]
            except:
                pass

            if cmd_ht == 'help':
                await cxt.say(help_helptext)
                return

            cmd_method = getattr(jose, 'c_%s' % cmd_ht, None)
            if cmd_method is None:
                await cxt.say("%s: Command not found" % cmd_ht)
                return

            try:
                docstring = cmd_method.__doc__
                if docstring is None:
                    await cxt.say("Docstring not found")
                else:
                    await cxt.say(docstring)
            except Exception as e:
                await cxt.say("error getting helptext for %s: %r" % (command, repr(e)))

            return

        try:
            # call c_ bullshit
            # use try/except, looks like it is faster than if/else
            try:
                jose_method = getattr(jose, method)
            except AttributeError:
                return

            # but first, repeat the recv steps
            await jose.mod_recv(message)
            try:
                sig = signature(jose_method)
                # if function can receive the Context, do it
                # else just do it normally
                if len(sig.parameters) == 3:
                    await jose_method(message, args, cxt)
                else:
                    await jose_method(message, args)

            except je.PermissionError:
                await cxt.say("Permission ¯\_(ツ)_/¯ 💠 ¯\_(ツ)_/¯ Error")
            except RuntimeError as e:
                await cxt.say('jose: py_rt_err: %s' % repr(e))
            except je.LimitError:
                pass

            del t_start

            end = time.time()
            delta = end - st
            if delta > 13:
                await cxt.say("Alguma coisa está demorando demais para responder(delta=%.4fs)..." % delta)

            # signal python to clean this shit
            del delta, st, end, jose_method

            # kthxbye
            return
        except Exception as e:
            await cxt.say("jose: py_err: ```%s```" % traceback.format_exc())
            # return

    should_stop = await do_command_table(message)
    if should_stop:
        return

    if message.content.startswith('!jasm'):
        await do_jasm(message)

    # a normal message, put it in the global text
    if not message.author.bot:
        with open("zelao.txt", 'a') as f:
            f.write('%s\n' % jcommon.speak_filter(message.content))

    # handle e_on_message
    await do_event('on_message', message)

    if random.random() < jcommon.jc_probabiblity:
        if not message.channel.is_private:

            # only if author has account
            if str(message.author.id) in jcoin.data:
                # if it is on the wrong server, return
                if message.server.id != "271378126234320897":
                    return

                if jcommon.MAINTENANCE_MODE:
                    return

                cxt = jcommon.Context(client, message, t_start, jose)

                author_id = str(message.author.id)
                amount = random.choice(jcommon.JC_REWARDS)
                acc_to = jcoin.get(author_id)[1]

                if amount == 0:
                    await cxt.say("0JC > %s" % (acc_to['name']))
                else:
                    res = jcoin.transfer(jcoin.jose_id, author_id, amount, jcoin.LEDGER_PATH)
                    await josecoin_save(message, False)
                    if res[0]:
                        emoji_res = await jcommon.random_emoji(3)
                        await cxt.say('%s %.2fJC > %s' % (emoji_res, amount, acc_to['name']))
                    else:
                        await jcommon.jose_debug(message, 'jc_error: %s' % res[1])
        else:
            return

    await jcommon.gorila_routine(message.channel)

t_allowed = True

async def _timer_playing():
    playing_phrase = random.choice(jcommon.JOSE_PLAYING_PHRASES)
    playing_name = '%s | v%s | %d guilds | %shjose' % (playing_phrase, jcommon.JOSE_VERSION, \
        len(client.servers), jcommon.JOSE_PREFIX)

    jcommon.logger.info("Playing %r", playing_name)
    g = discord.Game(name = playing_name, url = playing_name)
    await client.change_presence(game = g)

async def timer_playing():
    if t_allowed:
        while True:
            await _timer_playing()
            sec = random.randint(jcommon.PL_MIN_MINUTES * 60, \
                jcommon.PL_MAX_MINUTES * 60)

            minutes = int((sec % (60 * 60)) / 60)
            seconds = int(sec % 60)

            jcommon.logger.info("Playing for %dmin:%dsec", minutes, seconds)
            await asyncio.sleep(sec)

@client.event
async def on_ready():
    global t_allowed
    print("="*25)
    jcommon.logger.info("josé ready, name = %s, id = %s", client.user.name, client.user.id)
    print('='*25)

    await timer_playing()
    t_allowed = False


async def main_task():
    global client
    startupdelta = time.time() - jose.start_time
    jcommon.logger.info("took %.2f seconds on startup", startupdelta)
    jcommon.logger.info("José Starting")
    await client.start(jconfig.discord_token)

tr = tracker.SummaryTracker()

loop = asyncio.get_event_loop()
try:
    print("main_task")
    loop.run_until_complete(main_task())
except:
    # unload everything and logout
    loop.run_until_complete(jose.unload_all())
    loop.run_until_complete(client.logout())
finally:
    loop.close()

tr.print_diff()

jcommon.logger.info("Exit")
