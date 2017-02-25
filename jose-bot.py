# -*- coding: utf-8 -*-
import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# profiling
from pympler import tracker

import sys
import time
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

async def do_event(event_name, args):
    for handler in jose.event_tbl[event_name]:
        if isinstance(args[0], discord.Message):
            cxt = jcommon.Context(client, args[0], time.time(), jose)
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

    if jose.dev_mode:
        # Ignore messages from other servers
        if message.server != jcommon.JOSE_DEV_SERVER_ID:
            return False

        # Ignore non-admins
        if cxt.message.author.id not in ADMIN_IDS:
            return False

    if jose.command_lock:
        return False

    if len(message.content) <= 0:
        return False

    # configdb is langdb but with more bits
    cdb = await jcommon.configdb_get(message.server.id)
    if cdb['botblock']:
        return False

    return True

async def do_command_table(message):
    for command in commands_match:
        if command in message.content:
            func = commands_match[command]
            await func(message)
            return True

    return False

async def do_command(method, message, args, cxt, t_start, st):
    # try/except is WAY FASTER than checking if/else
    try:
        jose_method = getattr(jose, method)
    except AttributeError:
        return

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

    delta = time.time() - st
    if delta > 10:
        jcommon.logger.warning("HIGH DELTA OF COMMAND PROCESSING: %.4fs", delta)

    # signal python to clean this shit
    del delta, st, jose_method

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
    await do_event('any_message', [message])

    # get command and push it to jose
    if message.content.startswith(jcommon.JOSE_PREFIX):
        # use jcommon.parse_command
        command, args, method = jcommon.parse_command(message)

        cxt = jcommon.Context(client, message, t_start, jose)

        if command == '':
            return

        try:
            getattr(jose, method)
            stop = await do_cooldown(message, cxt)
            if stop:
                return
        except AttributeError:
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
    await do_event('on_message', [message])

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

    await do_event('client_ready', [client])

    if not jose.dev_mode:
        await timer_playing()
    else:
        jcommon.logger.info("Developer Mode Enabled")
        g = discord.Game(name = 'JOSÉ IN MAINTENANCE', url = 'fuck you')
        await client.change_presence(game = g)

    t_allowed = False

@client.event
async def on_server_join(server):
    for channel in server.channels:
        if channel.is_default:
            await do_event('server_join', [server, channel])

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

def main(args):
    try:
        mode = args[1]
    except:
        mode = 'normal'

    tr = tracker.SummaryTracker()

    if mode == 'dev':
        print("===ENTERING DEVELOPER MODE===")
        jose.dev_mode = True

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
    main(sys.argv)
