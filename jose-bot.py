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
import inspect
from random import SystemRandom
random = SystemRandom()

import discord

import josecommon as jcommon
import ext.jose as jose_bot
import jcoin.josecoin as josecoin
import joseconfig as jconfig
import joseerror as je

logging.basicConfig(level=logging.INFO)

start_time = time.time()

#default stuff
client = discord.Client()
jcommon.set_client(client) # to jcommon

# initialize jose instance
jose = jose_bot.JoseBot(client)
env = jose.env

async def jcoin_control(id_user, amnt):
    '''
    returns True if user can access
    '''
    return josecoin.transfer(id_user, josecoin.jose_id, \
        amnt, josecoin.LEDGER_PATH)

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

async def show_price(message):
    res = ''

    for k in jcommon.PRICE_TABLE:
        d = jcommon.PRICE_TABLE[k]
        res += "%r: %s > %.2f\n" % (k, d[0], d[1])

    await jose.say(res)
    return

show_pior_bot = jcommon.make_func("me tree :christmas_tree: me spam :christmas_tree: no oxygen :christmas_tree:  if ban\n" * 4)

exact_commands = {
    'melhor bot': jcommon.show_shit,
    'pior bot': show_pior_bot,
}

commands_start = {
    'learn': learn_data,
    'ahelp': jcommon.show_gambling_full,
    'adummy': jcommon.show_gambling,
    'awoo': jcommon.make_func("https://cdn.discordapp.com/attachments/202055538773721099/257717450135568394/awooo.gif"),
    'price': show_price,
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
    'compiuter':        jcommon.make_func("https://i.ytimg.com/vi/cU3330gwoh8/hqdefault.jpg"),
    'Parabéns':         jcommon.make_func("http://i.imgur.com/L0VlX0m.jpg")
}

counter = 0

def from_dict(f):
    async def a(m, args):
        await f(m)
    return a

for cmd in commands_start:
    setattr(jose, 'c_%s' % cmd, from_dict(commands_start[cmd]))

def load_module(n, n_cl):
    t_start = time.time()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(jose.load_ext(n, n_cl, None))

    time_taken_ms = (time.time() - t_start) * 1000
    jcommon.logger.info("%s took %.3fms to load", n, time_taken_ms)

def load_all_modules():
    # essential stuff
    load_module('joselang', 'JoseLanguage')
    load_module('josehelp', 'JoseHelp')
    load_module('josespeak', 'JoseSpeak')
    load_module('josestats', 'JoseStats')
    load_module('josemagicword', 'JoseMagicWord')
    load_module('jcoin', 'JoseCoin')

    # fun stuff
    load_module('josememes', 'JoseMemes')
    load_module('joseimages', 'JoseImages')
    load_module('josedatamosh', 'JoseDatamosh')
    load_module('josextra', 'joseXtra')
    load_module('josegambling', 'JoseGambling')

    # etc
    load_module('joseassembly', 'JoseAssembly')
    load_module('joseibc', 'JoseIBC')
    load_module('josemath', 'JoseMath')


    # load events
    jose.ev_empty()
    jose.ev_load(True)

async def do_event(event_name, **args):
    for handler in jose.event_tbl[event_name]:
        if isinstance(args[1], discord.Message):
            cxt = jcommon.Context(client, args[1], time.time(), jose)
            await handler(cxt.message, cxt)
        else:
            await handler(**args)

help_helptext = """
`j!docstring` - docsrings for commands
`j!docstring command` - get docstring for a command
Exemplos: `j!docstring docstring`, `j!docstring pstatus`, `j!docstring ap`, `j!docstring wa`, etc.
"""

async def check_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
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

async def do_docstring(message, args, cxt, command):
    # load helptext
    cmd_ht = 'docstring'
    try:
        if args[1] == 'docstring':
            await cxt.say(help_helptext)
            return True
        else:
            cmd_ht = args[1]
    except:
        pass

    if cmd_ht == 'docstring':
        await cxt.say(help_helptext)
        return True

    cmd_method = getattr(jose, 'c_%s' % cmd_ht, None)
    if cmd_method is None:
        await cxt.say("%s: Command not found" % cmd_ht)
        return True

    try:
        docstring = cmd_method.__doc__
        if docstring is None:
            await cxt.say("Docstring not found")
        else:
            await cxt.say(docstring)
    except Exception as e:
        await cxt.say("error getting docstring for %s: %r" % (command, repr(e)))

    return True

async def do_command(method, message, args, cxt, t_start, st):
    # try/except is WAY FASTER than checking if/else
    try:
        jose_method = getattr(jose, method)
    except AttributeError:
        return

    # but first, repeat the recv steps
    await jose.mod_recv(message)
    try:
        sig = inspect.signature(jose_method)
        # if function can receive the Context, do it
        # else just do it normally
        if len(sig.parameters) == 3:
            await jose_method(message, args, cxt)
        else:
            jcommon.logger.warning("%r is not using Context protocol", \
                jose_method)
            await jose_method(message, args)

    except je.PermissionError:
        jcommon.logger.warning("thrown PermissionError at author %s", \
            str(message.author))

        await cxt.say("Permission ¯\_(ツ)_/¯ 💠 ¯\_(ツ)_/¯ Error")
    except RuntimeError as e:
        jcommon.logger.error("RuntimeError happened with %s", \
            str(message.author), exc_info=True)
        await cxt.say(':interrobang: RuntimeError: %s' % repr(e))
    except je.LimitError:
        pass

    del t_start

    end = time.time()
    delta = end - st
    if delta > 13:
        jcommon.logger.warning("Something is takind longer than expected, delta=%.4fs", delta)

    # signal python to clean this shit
    del delta, st, end, jose_method

    # kthxbye
    return

async def do_cooldown(message, cxt):
    # cooldown system top notch :ok_hand:
    # Check for cooldowns from the author of the command
    authorid = message.author.id
    now = time.time()

    # timestamp to terminate the cooldown
    if authorid in env['cooldowns']:
        cdown_term_time = env['cooldowns'][authorid]
        if now < cdown_term_time:
            secleft = cdown_term_time - now

            if secleft > 0.5:
                # say to the user they're being a shit person
                m = await cxt.say("Please cool down!(**%.1f** seconds left)", \
                    (secleft,))
                # wait secleft before deleting and removing cooldown from user
                await asyncio.sleep(secleft)
                await client.delete_message(m)

                # that code repetiton was needed, sorry
                try:
                    del env['cooldowns'][authorid]
                    return True
                except Exception as e:
                    jcommon.logger.error("do_cooldown: error removing cooldown for %d: %r", \
                        authorid, e)
            else:
                try:
                    del env['cooldowns'][authorid]
                except Exception as e:
                    jcommon.logger.error("do_cooldown: error removing cooldown for %d: %r", \
                        authorid, e)

    # always update user's cooldown
    env['cooldowns'][authorid] = now + jcommon.COOLDOWN_SECONDS
    return False

@client.event
async def on_message(message):
    global jose
    global counter

    t_start = time.time()

    is_good = await check_message(message)
    if not is_good:
        return

    if message.author.id in josecoin.data:
        josecoin.data[message.author.id]['name'] = str(message.author)

    st = time.time()

    await jose.recv(message) # at least

    # any_message event
    await do_event('any_message', message)

    # get command and push it to jose
    if message.content.startswith(jcommon.JOSE_PREFIX):
        # use jcommon.parse_command
        command, args, method = jcommon.parse_command(message)

        cxt = jcommon.Context(client, message, t_start, jose)

        if command == '':
            return

        stop = await do_cooldown(message, cxt)
        if stop:
            return

        if command == 'docstring':
            needs_stop = await do_docstring(message, args, cxt, command)
            if needs_stop:
                return

        try:
            # do a barrel roll
            await do_command(method, message, args, cxt, t_start, st)
            return
        except Exception as e:
            await cxt.say("jose.py_err: ```%s```" % traceback.format_exc())

        return

    should_stop = await do_command_table(message)
    if should_stop:
        return

    # a normal message, put it in the global text
    if not message.author.bot:
        with open("zelao.txt", 'a') as f:
            f.write('%s\n' % jcommon.speak_filter(message.content))

    # handle e_on_message
    await do_event('on_message', message)

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
    global t_allowed
    if t_allowed:
        while True:
            await _timer_playing()
            t_allowed = False
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

    await do_event('client_ready', client)
    await timer_playing()
    t_allowed = False

@client.event
async def on_server_join(server):
    for channel in server.channels:
        if channel.is_default:
            await do_event('server_join', server, channel)

            jcommon.logger.info("New server: %s" % server.id)
            await client.send_message(channel, jcommon.WELCOME_MESSAGE)

@client.event
async def on_error(event, *args, **kwargs):
    err = traceback.format_exc()
    jcommon.logger.error("Error at %s(%s, %s), %s" % \
        (str(event), args, kwargs, err))

    if str(event) == 'on_message':
        message = args[0]
        jcommon.logger.error("Message error happened at ServerID %s name %r" % \
            (message.server.id, message.server.name))

async def main_task():
    global client
    startupdelta = time.time() - jose.start_time
    jcommon.logger.info("--- STARTUP TOOK %.2f SECONDS ---", startupdelta)
    jcommon.logger.info("Starting Client")
    await client.start(jconfig.discord_token)

def main():
    tr = tracker.SummaryTracker()

    # load all josé's modules
    load_all_modules()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main_task())
    except KeyboardInterrupt:
        jcommon.logger.info("received KeyboardInterrupt, exiting")

        # unload normally
        loop.run_until_complete(jose.unload_all())
        loop.run_until_complete(client.logout())
    except Exception as e:
        jcommon.logger.error("Received Exception from main function, exiting")
        jcommon.logger.error("This is the error: %s", traceback.format_exc())

        # unload as always
        loop.run_until_complete(jose.unload_all())
        loop.run_until_complete(client.logout())
    finally:
        loop.close()

    tr.print_diff()

    jcommon.logger.info("Exiting main function")
    logging.shutdown()

if __name__ == '__main__':
    main()
