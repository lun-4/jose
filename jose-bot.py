# -*- coding: utf-8 -*-
import sys
import time
import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
import traceback
import logging
import discord
from discord.ext import commands

import josecommon as jcommon
import ext.jose as jose_bot
import jcoin.josecoin as josecoin
import joseconfig as jconfig
import joseerror as je

# profiling
from pympler import tracker
from random import SystemRandom
random = SystemRandom()

logging.basicConfig(level=logging.INFO, \
    format='[%(levelname)7s] [%(name)s] %(message)s')

start_time = time.time()
bot = commands.Bot(command_prefix=jcommon.JOSE_PREFIX)
jcommon.set_client(bot) # to jcommon

# initialize jose instance
jose = jose_bot.JoseBot(bot)
env = jose.env
loop = asyncio.get_event_loop()

counter = 0

def load_module(n, n_cl):
    t_start = time.time()
    loop.run_until_complete(jose.load_ext(n, n_cl, None))
    time_taken_ms = (time.time() - t_start) * 1000
    jcommon.logger.info("%s took %.3fms to load", n, time_taken_ms)

def load_all_modules():
    # essential stuff
    load_module('joselang', 'JoseLanguage')
    load_module('josehelp', 'JoseHelp')
    load_module('jcoin', 'JoseCoin')
    load_module('josestats', 'JoseStats')
    load_module('josemagicword', 'JoseMagicWord')
    load_module('josewatch', 'JoseWatch')
    load_module('josemod', 'JoseMod')
    load_module('josespeak', 'JoseSpeak')

    # the other stuff
    load_module('josememes', 'JoseMemes')
    load_module('joseimages', 'JoseImages')
    load_module('josedatamosh', 'JoseDatamosh')
    load_module('josextra', 'joseXtra')
    load_module('josegambling', 'JoseGambling')
    load_module('josemath', 'JoseMath')

    # achievment is last
    load_module('achievement', 'JoseAchievement')
    load_module('tools', 'JoseTools')

    # load events
    jose.ev_empty()
    jose.ev_load(True)

async def do_event(event_name, args):
    if event_name not in jose.event_tbl:
        jose.event_tbl[event_name] = []

    for handler in jose.event_tbl[event_name]:
        if isinstance(args[0], discord.Message):
            cxt = jcommon.Context(bot, args[0], time.time(), jose)
            await handler(cxt.message, cxt)
        else:
            await handler(*args)

async def check_message(message):
    # we do not want the bot to reply to itself
    if message.author == bot.user:
        return False

    if len(message.content) <= 0:
        return False

    if jose.command_lock:
        return False

    # Block DMs altogether
    if message.server is None:
        return False

    if message.author.id in jose.blocks['users']:
        return False

    if message.server.id in jose.blocks['guilds']:
        return False

    if jose.sw_mode:
        if message.author.id not in jcommon.ADMIN_IDS:
            return False

    if jose.dev_mode:
        # Ignore messages from other servers
        if message.server.id != jcommon.JOSE_DEV_SERVER_ID:
            return False

        # Ignore non-admins
        if message.author.id not in jcommon.ADMIN_IDS:
            return False

    # configdb is langdb but with more bits
    botblock = await jcommon.configdb_get(message.server.id, 'botblock')
    if botblock and message.author.bot:
        return False

    return True

async def do_command(method, message, args, cxt, t_start, st):
    # try/except is WAY FASTER than checking if/else
    try:
        jose_method = getattr(jose, method)
    except AttributeError:
        return

    try:
        # await bot.process_commands(message)

        is_admin = message.author.id in jcommon.ADMIN_IDS
        if jose.sw_mode:
            if not is_admin:
                await cxt.say("I'm on suicide watch mode, Discord is having issues\n\
https://status.discordapp.com")
                return


        await jose_method(message, args, cxt)

    except je.PermissionError:
        jcommon.logger.warning("thrown PermissionError at %r from %s(%r)", \
            str(message.author), method, args)

        await cxt.say("Permission ¯\_(ツ)_/¯ 💠 ¯\_(ツ)_/¯ Error")

    except RuntimeError as err:
        jcommon.logger.error("RuntimeError happened with %s[%s] from %s(%r)", \
            str(message.author), message.author.id, method, args, exc_info=True)
        await cxt.say(':interrobang: RuntimeError: %r' % err)

    except je.CommonError as err:
        jcommon.logger.error("CommonError to %r from %s(%r): %r", \
            str(message.author), method, args, repr(err))

        await cxt.say('```\nCommonError: %r```', (err,))

    except je.JoseCoinError as err:
        await cxt.say('err: `%r`', (err,))

    except asyncio.TimeoutError as err:
        jcommon.logger.error("TimeoutError to %r from %s(%r): %r", \
            str(message.author), method, args, repr(err))
        await cxt.say("`[timeout] Timeout Reached`")

    except je.LimitError:
        pass

    del t_start

    delta = time.time() - st
    if delta > 10:
        jcommon.logger.warning("HIGH DELTA %r from %s[%s]: %.4fs", \
            message.content, message.author, message.author.id, delta)

    # signal python to clean this shit
    del delta, st, jose_method

    # kthxbye
    return

def cooldown_apply(author_id, now):
    env['cooldowns'][author_id] = now + jcommon.COOLDOWN_SECONDS

def cooldown_remove(author_id):
    env['cooldowns'].pop(author_id, None)

async def do_cooldown(message, cxt):
    author_id = message.author.id
    now = time.time()

    # create cooldown
    if author_id not in env['cooldowns']:
        cooldown_apply(author_id, now)
        return False

    # check if cooldown is alredy gone
    cooldown_end = env['cooldowns'][author_id]
    if now >= cooldown_end:
        cooldown_remove(author_id)
        return False

    time_left = cooldown_end - now
    if time_left < 0.5:
        cooldown_remove(author_id)
        return False

    cooldown_msg = await cxt.say("Wait **%.2f** seconds", (time_left,))

    await asyncio.sleep(time_left)
    await bot.delete_message(cooldown_msg)
    cooldown_remove(author_id)

    return True

@bot.event
async def on_message(message):
    global jose
    global counter

    t_start = time.time()

    is_good = await check_message(message)
    if not is_good:
        return

    if message.author.id in josecoin.data:
        account = josecoin.data[message.author.id]
        if str(message.author) != account['name']:
            account['name'] = str(message.author)

    st = time.time()

    # any_message event
    await do_event('any_message', [message])

    # get command and push it to jose
    if message.content.startswith(jcommon.JOSE_PREFIX):
        # use jcommon.parse_command
        command, args, method = jcommon.parse_command(message)
        if len(command.strip()) == '':
            return

        cxt = jcommon.Context(bot, message, t_start, jose)

        try:
            getattr(jose, method)
            stop = await do_cooldown(message, cxt)
            if stop:
                return
        except AttributeError:
            return

        try:
            await do_command(method, message, args, cxt, t_start, st)
        except Exception as e:
            jcommon.logger.error("Exception at %s, made by %s", method, \
                str(message.author), exc_info=True)
            # signal user
            await cxt.say("jose.py_err: ```%s```", (traceback.format_exc(),))

        return

    # handle e_on_message
    await do_event('on_message', [message])

t_allowed = True

async def _timer_playing():
    playing_phrase = random.choice(jcommon.JOSE_PLAYING_PHRASES)
    playing_name = '%s | v%s | %d guilds | %shjose' % (playing_phrase, jcommon.JOSE_VERSION, \
        len(bot.servers), jcommon.JOSE_PREFIX)

    return playing_name

async def timer_playing():
    global t_allowed
    await bot.wait_until_ready()

    if t_allowed:
        while True:
            if not jose.dev_mode:
                game_str = await _timer_playing()
                g = discord.Game(name=game_str, url=game_str)
                await bot.change_presence(game=g)

                t_allowed = False
                sec = random.randint(jcommon.PL_MIN_MINUTES * 60, \
                    jcommon.PL_MAX_MINUTES * 60)

                minutes = int((sec % (60 * 60)) / 60)
                seconds = int(sec % 60)

                jcommon.logger.info("Playing %r for %dmin:%dsec", \
                    game_str, minutes, seconds)

                await asyncio.sleep(sec)
            else:
                await asyncio.sleep(10)

@bot.event
async def on_ready():
    global t_allowed
    print("="*25)
    jcommon.logger.info("josé ready, name = %s, id = %s", bot.user.name, bot.user.id)
    print('='*25)
    jose.command_lock = False

    await do_event('client_ready', [bot])

    t_allowed = False

@bot.event
async def on_server_join(server):
    for channel in server.channels:
        if channel.is_default:
            await do_event('server_join', [server, channel])

            jcommon.logger.info("New server: %s[%s]", server, server.id)
            await bot.send_message(channel, jcommon.WELCOME_MESSAGE)

@bot.event
async def on_error(event, *args, **kwargs):
    err = traceback.format_exc()
    jcommon.logger.error("Error at %s(%s, %s), %s" % \
        (str(event), args, kwargs, err))

    if str(event) == 'on_message':
        message = args[0]
        jcommon.logger.error("Message error happened at ServerID %s name %r" % \
            (message.server.id, message.server.name))

@bot.event
async def on_member_join(member):
    await do_event('member_join', [member])

@bot.event
async def on_member_remove(member):
    await do_event('member_remove', [member])

@bot.event
async def on_member_ban(member):
    await do_event('member_ban', [member])

@bot.event
async def on_member_unban(server, user):
    await do_event('member_unban', [server, user])

@bot.event
async def on_server_remove(server):
    await do_event('server_remove', [server])

@bot.event
async def on_socket_response(data):
    await do_event('socket_response', [data])

@bot.event
async def on_message_edit(before, after):
    await do_event('message_edit', [before, after])

    is_good = await check_message(before)
    if not is_good:
        return

    if not before.content.startswith(jcommon.JOSE_PREFIX):
        return

    delta = after.edited_timestamp - before.timestamp

    if delta.total_seconds() > 10:
        return

    # redo on_message event
    # this is bulky but yeah, fast solutions require ugliness
    await on_message(after)

async def main_task():
    startupdelta = time.time() - jose.start_time
    jcommon.logger.info("--- STARTUP TOOK %.2f SECONDS ---", startupdelta)

    try:
        jcommon.logger.info("[start] logging")

        jose.playing_task = bot.loop.create_task(timer_playing())
        if not jose.dev_mode:
            jose.playing_task = bot.loop.create_task(timer_playing())
        else:
            jose.playing_task = bot.loop.create_task(jose.do_dev_mode())

        bot.loop.create_task(jcommon.setup_logging())
        bot.loop.create_task(jcommon.log_channel_handler.watcher())

        jcommon.logger.info("[start] discord bot")
        await bot.start(jconfig.discord_token)
        jcommon.logger.info("[exit] discord bot")
    except discord.GatewayNotFound:
        jcommon.logger.error("Received GatewayNotFound from discord.")
    except Exception as err:
        jcommon.logger.error("Received %r from bot.start", err, exc_info=True)
        try:
            await bot.logout()
        except Exception as err:
            jcommon.logger.error("Received %r from bot.logout", err, exc_info=True)

def main(args):
    try:
        mode = args[1]
    except:
        mode = 'normal'

    tr = tracker.SummaryTracker()

    if mode == 'dev':
        print("===ENTERING DEVELOPER MODE===")
        jose.dev_mode = True
        logging.basicConfig(level=logging.DEBUG)
    elif mode == 'sw':
        print("===SUICIDE WATCH MODE===")
        jose.sw_mode = True
        logging.basicConfig(level=logging.DEBUG)

    # load all josé's modules
    load_all_modules()

    loop = asyncio.get_event_loop()
    try:
        jcommon.logger.info("[start] main_task")
        loop.run_until_complete(main_task())
        jcommon.logger.info("[exit] main_task")
    except KeyboardInterrupt:
        jcommon.logger.info("received KeyboardInterrupt, exiting")
    except Exception as err:
        jcommon.logger.error("Received %r from main function, exiting", err)
        jcommon.logger.error("This is the error: %s", traceback.format_exc())
    finally:
        if not jose.made_gshutdown:
            jcommon.logger.info("[general_shutdown]")
            loop.run_until_complete(jose.general_shutdown(None))
        else:
            jcommon.logger.info("[general_shutdown] already done")

    try:
        pending = asyncio.Task.all_tasks(loop=loop)
        gathered = asyncio.gather(*pending, loop=loop)
        gathered.cancel()
        loop.run_until_complete(gathered)
        gathered.exception()
    except Exception as err:
        print(traceback.format_exc())

    jcommon.logger.info("[asyncio] Closing event loop")
    loop.close()

    tr.print_diff()

    jcommon.logger.info("[exit] main")
    logging.shutdown()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
